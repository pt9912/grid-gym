"""Tests fuer die `FaultSurfaceDevice`-Sub-Protocol-Naht (Slice 077 S2, ADR 0077 §2.5).

Pinnt:
- `isinstance`-Diskriminierung: `BatteryDevice` traegt die Surface, ein
  Nicht-Surface-Geraet (`LoadDevice`) nicht — der `TickLoop` selektiert darueber.
- `DeviceStatus` ist eine frozen Daten-Projektion (kein `TelemetryPoint`).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from grid_gym.hexagon.core.devices._status_surface import FaultSurfaceDevice
from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.domain.device import DeviceStatus
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom


def _battery() -> BatteryDevice:
    battery = BatteryDevice()
    battery.initialize(
        ScenarioDevice(
            id="battery-1",
            type="battery",
            params={
                "capacity_kwh": Decimal("100"),
                "initial_soc_pct": Decimal("50"),
                "min_soc_pct": Decimal("0"),
                "max_soc_pct": Decimal("100"),
                "max_charge_kw": Decimal("50"),
                "max_discharge_kw": Decimal("50"),
                "charge_efficiency": Decimal("1"),
                "discharge_efficiency": Decimal("1"),
                "ramp_kw_per_s": Decimal("100"),
            },
        ),
        FixedSeedRandom(seed=0),
    )
    return battery


def _load() -> LoadDevice:
    load = LoadDevice()
    load.initialize(
        ScenarioDevice(id="load-1", type="load", params={"rated_power_kw": Decimal("30")}),
        FixedSeedRandom(seed=0),
    )
    return load


def test_battery_is_fault_surface_device() -> None:
    assert isinstance(_battery(), FaultSurfaceDevice)


def test_load_is_not_fault_surface_device() -> None:
    # LoadDevice hat kein `available`/`fault_status` → der Loop sammelt es nicht.
    assert not isinstance(_load(), FaultSurfaceDevice)


def test_battery_surface_reflects_fault() -> None:
    battery = _battery()
    assert (battery.available, battery.fault_status) == (True, "ok")
    battery.inject_fault("cell_failure", {})
    assert (battery.available, battery.fault_status) == (False, "cell_failure")


def test_device_status_is_frozen() -> None:
    status = DeviceStatus(device_id="battery-1", available=True, fault_status="ok")
    with pytest.raises(FrozenInstanceError):
        status.available = False  # type: ignore[misc]
