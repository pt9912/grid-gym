"""Tests fuer die `TickResult.emitted_device_status`-Sammlung (Slice 077 S2,
ADR 0077 §2.5).

Pinnt:
- Der `TickLoop` sammelt je Tick einen `DeviceStatus` pro fault-surface-faehigem
  Geraet (`BatteryDevice`), in Device-Reihenfolge; Nicht-Surface-Geraete
  (`LoadDevice`) tauchen **nicht** auf.
- Der Status reflektiert eine injizierte `cell_failure` (`available=False`).
- Pin-Neutralitaet: ohne fault-surface-faehiges Geraet ist der Slot leer, und die
  Default-`TickResult`-Konstruktion traegt `()`.
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.domain.device import DeviceStatus
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


def _battery(device_id: str = "battery-1") -> BatteryDevice:
    battery = BatteryDevice()
    battery.initialize(
        ScenarioDevice(
            id=device_id,
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


def _make_tick_loop(*devices: object) -> TickLoop:
    return TickLoop(
        run_id="device-status-test",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=tuple(devices),  # type: ignore[arg-type]
    )


def test_collects_only_fault_surface_devices_in_device_order() -> None:
    # load VOR battery gelistet → nur die Battery erscheint (Load hat keine Surface).
    tick_loop = _make_tick_loop(_load(), _battery())
    result = tick_loop.tick()
    assert result.emitted_device_status == (
        DeviceStatus(device_id="battery-1", available=True, fault_status="ok"),
    )


def test_status_reflects_injected_cell_failure() -> None:
    battery = _battery()
    tick_loop = _make_tick_loop(battery)
    battery.inject_fault("cell_failure", {})
    result = tick_loop.tick()
    assert result.emitted_device_status == (
        DeviceStatus(device_id="battery-1", available=False, fault_status="cell_failure"),
    )


def test_empty_without_fault_surface_device() -> None:
    tick_loop = _make_tick_loop(_load())
    result = tick_loop.tick()
    assert result.emitted_device_status == ()


def test_default_tick_result_slot_is_empty_tuple() -> None:
    # Pin-Neutralitaet: Bestands-Konstruktionen ohne den Slot bleiben kompatibel.
    tick_loop = _make_tick_loop()
    result = tick_loop.tick()
    assert result.emitted_device_status == ()
