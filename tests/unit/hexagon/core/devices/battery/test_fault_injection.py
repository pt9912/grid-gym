"""Tests fuer `BatteryDevice.inject_fault` (M3 Welle 2, ADR 0022 + ADR 0025).

Pinnt:
- `FaultInjectableDevice`-Protocol-Adherence.
- `cell_failure`-Fault setzt Device-Flag.
- `_clear_cell_failure` reset.
- `tick()` halbiert effektive `max_discharge_kw` bei aktivem Fault.
- Snapshot-Roundtrip mit Fault-State.
- Unbekannter `fault_type` wirft `FaultUnsupportedTypeError`.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.errors import FaultUnsupportedTypeError
from grid_gym.hexagon.core.faults import FaultInjectableDevice


def _set_power_command(value: Decimal, target: str = "battery-1") -> Command:
    return Command(
        command_id="cmd-1",
        simulation_time=0,
        target_device_id=target,
        type="set_power_kw",
        payload={"value": value},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _battery() -> BatteryDevice:
    device = BatteryDevice()
    device.initialize(
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
        MersenneTwisterRandomPort(seed=42),
    )
    device.set_run_id("test")
    return device


def test_battery_device_satisfies_fault_injectable_protocol() -> None:
    """ADR 0022 §2.1: BatteryDevice ist FaultInjectableDevice."""
    device = _battery()
    assert isinstance(device, FaultInjectableDevice)


def test_inject_cell_failure_sets_active_flag() -> None:
    device = _battery()
    assert device._cell_failure_active is False
    device.inject_fault("cell_failure", {})
    assert device._cell_failure_active is True


def test_clear_cell_failure_resets_flag() -> None:
    device = _battery()
    device.inject_fault("cell_failure", {})
    device._clear_cell_failure()
    assert device._cell_failure_active is False


def test_inject_unknown_fault_type_raises_typed() -> None:
    """ADR 0025 §2.1 Closed-Set: unbekannter fault_type wirft
    `FaultUnsupportedTypeError`."""
    device = _battery()
    with pytest.raises(FaultUnsupportedTypeError):
        device.inject_fault("voltage_drop", {})


def test_tick_with_active_cell_failure_halves_discharge_clamp() -> None:
    """ADR 0025 §2.1: bei aktivem `cell_failure` wird die
    effektive `max_discharge_kw` halbiert (Welle-2-Default 50 %).
    """
    device = _battery()
    # Discharge auf -50 (volle Discharge) ohne Fault.
    device.apply_command(_set_power_command(Decimal("-50")))
    # Ramp ist 100 kW/s, dt = 1s → erreicht -50 in einer Tick.
    outcome_pre = device.tick(DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000))
    power_pre = next(p.value for p in outcome_pre.telemetry if p.metric == "power_kw")
    assert power_pre == Decimal("-50.000000")  # voll

    # Fault aktivieren + naechste Tick.
    device.inject_fault("cell_failure", {})
    outcome_fault = device.tick(DeviceTickContext(tick=1, simulation_time=1000, tick_ms=1000))
    power_fault = next(p.value for p in outcome_fault.telemetry if p.metric == "power_kw")
    # Halbiert: -25 (statt -50).
    assert power_fault == Decimal("-25.000000")


def test_tick_after_clear_returns_to_full_discharge() -> None:
    """Recovery: nach `_clear_cell_failure` ist die volle
    Discharge wieder verfuegbar."""
    device = _battery()
    device.apply_command(_set_power_command(Decimal("-50")))
    device.inject_fault("cell_failure", {})
    device.tick(DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000))  # -25
    device._clear_cell_failure()
    outcome = device.tick(DeviceTickContext(tick=1, simulation_time=1000, tick_ms=1000))
    power = next(p.value for p in outcome.telemetry if p.metric == "power_kw")
    # Voll: -50 (ramp ist 100 kW/s, kann von -25 in einer Tick auf -50).
    assert power == Decimal("-50.000000")


def test_snapshot_roundtrip_preserves_fault_state_active() -> None:
    """ADR 0014 §2.4 + ADR 0025 §2.2: Snapshot-Roundtrip ist
    byte-stabil inkl. fault_state."""
    device = _battery()
    device.inject_fault("cell_failure", {})
    state = device.snapshot()
    restored = BatteryDevice.from_snapshot(state)
    assert restored._cell_failure_active is True
    assert restored == device


def test_snapshot_roundtrip_without_fault_state_defaults_false() -> None:
    """ADR 0025 §2.2 Backward-Compat: Welle-1-Snapshots ohne
    `fault_state`-Block sind weiterhin lesbar."""
    device = _battery()
    state = dict(device.snapshot())
    # `fault_state` entfernen (Welle-1-Stand-Simulation).
    state.pop("fault_state", None)
    restored = BatteryDevice.from_snapshot(state)
    assert restored._cell_failure_active is False
