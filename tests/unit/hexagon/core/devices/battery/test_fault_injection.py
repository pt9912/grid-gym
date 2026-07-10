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

# Slice 054: fault-Sensor-Traeger fuer `make test-fault`.
pytestmark = pytest.mark.fault


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


def test_clear_fault_resets_flag() -> None:
    device = _battery()
    device.inject_fault("cell_failure", {})
    device.clear_fault("cell_failure")
    assert device._cell_failure_active is False


def test_clear_fault_is_idempotent() -> None:
    """ADR 0025 §2.4: wiederholte `clear_fault`-Aufrufe sind
    No-Op."""
    device = _battery()
    device.clear_fault("cell_failure")  # Pre-init No-Op
    device.inject_fault("cell_failure", {})
    device.clear_fault("cell_failure")
    device.clear_fault("cell_failure")  # zweiter clear — No-Op
    assert device._cell_failure_active is False


def test_clear_fault_unknown_type_raises_typed() -> None:
    """ADR 0025 §2.4 + H-2: `clear_fault` schaerft das Closed-Set
    symmetrisch zu `inject_fault`."""
    device = _battery()
    with pytest.raises(FaultUnsupportedTypeError):
        device.clear_fault("voltage_drop")


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
    """Recovery: nach `clear_fault("cell_failure")` ist die volle
    Discharge wieder verfuegbar."""
    device = _battery()
    device.apply_command(_set_power_command(Decimal("-50")))
    device.inject_fault("cell_failure", {})
    device.tick(DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000))  # -25
    device.clear_fault("cell_failure")
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


def test_snapshot_with_empty_fault_state_defaults_false() -> None:
    """Welle-2-Review M-1: leeres `fault_state = {}` defaultet
    alle Flags auf False (kein Crash, kein Surprise-True)."""
    device = _battery()
    state = dict(device.snapshot())
    state["fault_state"] = {}
    restored = BatteryDevice.from_snapshot(state)
    assert restored._cell_failure_active is False


def test_snapshot_with_unknown_fault_keys_ignored_silently() -> None:
    """Welle-2-Review M-1 Forward-Compat: unbekannte
    `fault_state`-Keys (z. B. Welle-3-`voltage_drop_active`) werden
    von Welle-2-Code ignoriert. Welle-3 Snapshots bleiben lesbar."""
    device = _battery()
    state = dict(device.snapshot())
    state["fault_state"] = {
        "cell_failure_active": True,
        "voltage_drop_active": True,  # Welle-3-Forward-Compat
        "some_future_flag": True,
    }
    restored = BatteryDevice.from_snapshot(state)
    assert restored._cell_failure_active is True
    # Welle-2-Code kennt `voltage_drop_active` nicht; silent-ignored.


def test_snapshot_with_wrong_typed_fault_flag_raises_wrongtype() -> None:
    """Welle-2-Review M-1: `cell_failure_active = "true"` (String
    statt bool) wirft typisierten `WrongTypeError`."""
    from grid_gym.hexagon.core.errors import WrongTypeError

    device = _battery()
    state = dict(device.snapshot())
    state["fault_state"] = {"cell_failure_active": "true"}
    with pytest.raises(WrongTypeError):
        BatteryDevice.from_snapshot(state)


def test_tick_with_active_cell_failure_overrides_ramp_limit() -> None:
    """Welle-2-Review M-6: bei aktivem `cell_failure` schlaegt
    der Derate-Hard-Clamp das Ramp-Limit. ADR 0025 §2.1:
    Safety-Constraint hat Vorrang vor Comfort-Ramp.

    Setup: ramp_kw_per_s=10 (langsam); current_power_kw=-50;
    fault aktiv. Ohne Derate haette Ramp die Power in einer Tick
    nicht senken koennen (kann nur 10 kW pro Sekunde aendern).
    Mit Derate wird sie instant auf -25 geclamped.
    """
    device = BatteryDevice()
    device.initialize(
        ScenarioDevice(
            id="battery-slow",
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
                "ramp_kw_per_s": Decimal("10"),  # langsamer Ramp
            },
        ),
        MersenneTwisterRandomPort(seed=42),
    )
    device.set_run_id("test")
    # Erste Tick: voll auf -50 (ramp ist 10, dt=1s — also nur -10
    # in einer Tick erreichbar). Wir setzen direkt -50:
    device.apply_command(_set_power_command(Decimal("-50"), target="battery-slow"))
    device.tick(DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000))
    # Erste Tick erreicht durch ramp nur -10 (von 0).
    assert device._current_power_kw == Decimal("-10")

    # Fault aktivieren — sollte instant auf -25 wirken trotz Ramp.
    # Aber: aktuelles Power ist -10, neue effective_max ist -25.
    # -10 ist innerhalb [-25, 0] → kein Clamp. Power bleibt -10.
    device.inject_fault("cell_failure", {})
    device.tick(DeviceTickContext(tick=1, simulation_time=1000, tick_ms=1000))
    # Ramp moechte -20 erreichen (-10 + -10), aber innerhalb -25.
    assert device._current_power_kw == Decimal("-20")
    # Eine weitere Tick — ramp moechte -30, aber Derate-Clamp setzt -25.
    device.tick(DeviceTickContext(tick=2, simulation_time=2000, tick_ms=1000))
    assert device._current_power_kw == Decimal("-25")  # Hard-Clamp greift
