"""Tests fuer `GridConnectionDevice.inject_fault`
(M3 Welle 2, ADR 0022 + ADR 0025).

Pinnt:
- `FaultInjectableDevice`-Protocol-Adherence.
- `voltage_drop`-Fault setzt Device-Flag + reduziert
  `_pending_voltage_v` auf 50 % von `nominal_voltage_v`.
- `clear_fault` reset auf `nominal_voltage_v`.
- `tick()` emittiert `voltage_v`-Telemetry; bei aktivem Fault
  ist der Wert reduziert.
- Snapshot-Roundtrip mit Voltage-State + Fault-Flag.
- GridConnection-Constraint (ADR 0022 §2.4): `_pending_power_kw`
  wird vom Fault NICHT mutiert.
- Unbekannter `fault_type` wirft `FaultUnsupportedTypeError`.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.errors import FaultUnsupportedTypeError
from grid_gym.hexagon.core.faults import FaultInjectableDevice


def _grid_device() -> GridConnectionDevice:
    device = GridConnectionDevice()
    device.initialize(
        ScenarioDevice(
            id="grid-1",
            type="grid_connection",
            params={
                "nominal_voltage_v": Decimal("400"),
                "max_import_kw": Decimal("1000"),
                "max_export_kw": Decimal("1000"),
            },
        ),
        MersenneTwisterRandomPort(seed=42),
    )
    device.set_run_id("test")
    return device


def test_grid_device_satisfies_fault_injectable_protocol() -> None:
    """ADR 0022 §2.1: GridConnectionDevice ist FaultInjectableDevice."""
    device = _grid_device()
    assert isinstance(device, FaultInjectableDevice)


def test_inject_voltage_drop_sets_active_flag() -> None:
    device = _grid_device()
    assert device._voltage_drop_active is False
    device.inject_fault("voltage_drop", {})
    assert device._voltage_drop_active is True


def test_inject_voltage_drop_halves_pending_voltage() -> None:
    """ADR 0025 §2.1: 50 % von nominal_voltage_v (Welle-2-Default)."""
    device = _grid_device()
    # Pre: nominal = 400.
    assert device._pending_voltage_v == Decimal("400")
    device.inject_fault("voltage_drop", {})
    # 50 % → 200.
    assert device._pending_voltage_v == Decimal("200")


def test_clear_fault_resets_voltage_to_nominal() -> None:
    device = _grid_device()
    device.inject_fault("voltage_drop", {})
    assert device._pending_voltage_v == Decimal("200")
    device.clear_fault("voltage_drop")
    assert device._voltage_drop_active is False
    assert device._pending_voltage_v == Decimal("400")


def test_clear_fault_is_idempotent() -> None:
    """ADR 0025 §2.4: wiederholte `clear_fault`-Aufrufe sind No-Op."""
    device = _grid_device()
    device.clear_fault("voltage_drop")  # pre-fault clear
    device.inject_fault("voltage_drop", {})
    device.clear_fault("voltage_drop")
    device.clear_fault("voltage_drop")  # zweiter clear — No-Op
    assert device._voltage_drop_active is False
    assert device._pending_voltage_v == Decimal("400")


def test_inject_unknown_fault_type_raises_typed() -> None:
    """ADR 0025 §2.1 Closed-Set: unbekannter fault_type wirft
    `FaultUnsupportedTypeError`."""
    device = _grid_device()
    with pytest.raises(FaultUnsupportedTypeError):
        device.inject_fault("cell_failure", {})


def test_clear_fault_unknown_type_raises_typed() -> None:
    """ADR 0025 §2.4 + H-2: `clear_fault` symmetrisch."""
    device = _grid_device()
    with pytest.raises(FaultUnsupportedTypeError):
        device.clear_fault("cell_failure")


def test_tick_emits_voltage_v_telemetry() -> None:
    """ADR 0025 §2.1: GridConnection emittiert `voltage_v` als
    vierte Telemetry-Metric (alphabetisch sortiert nach
    `export_kwh`, `import_kwh`, `power_kw`, `voltage_v`)."""
    device = _grid_device()
    outcome = device.tick(DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000))
    metrics = [p.metric for p in outcome.telemetry]
    assert metrics == ["export_kwh", "import_kwh", "power_kw", "voltage_v"]
    voltage_v = next(p for p in outcome.telemetry if p.metric == "voltage_v")
    assert voltage_v.value == Decimal("400.000000")
    assert voltage_v.unit == "V"


def test_tick_with_active_voltage_drop_emits_reduced_voltage() -> None:
    """ADR 0025 §2.1: bei aktivem voltage_drop emittiert tick()
    den reduzierten Voltage-Wert."""
    device = _grid_device()
    device.inject_fault("voltage_drop", {})
    outcome = device.tick(DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000))
    voltage_v = next(p for p in outcome.telemetry if p.metric == "voltage_v")
    assert voltage_v.value == Decimal("200.000000")


def test_inject_voltage_drop_does_not_mutate_pending_power_kw() -> None:
    """ADR 0022 §2.4 GridConnection-Constraint: voltage_drop darf
    `_pending_power_kw` NICHT veraendern (Welle-6b-Auto-Schluss
    wuerde das in derselben Tick ueberschreiben)."""
    device = _grid_device()
    pending_before = device._pending_power_kw
    current_before = device._current_power_kw
    device.inject_fault("voltage_drop", {})
    assert device._pending_power_kw == pending_before
    assert device._current_power_kw == current_before


def test_snapshot_roundtrip_preserves_voltage_state_and_flag() -> None:
    """ADR 0017 §2.3 + ADR 0025 §2.2: Snapshot-Roundtrip ist
    byte-stabil inkl. Voltage-State und fault_state."""
    device = _grid_device()
    device.inject_fault("voltage_drop", {})
    state = device.snapshot()
    restored = GridConnectionDevice.from_snapshot(state)
    assert restored._voltage_drop_active is True
    assert restored._pending_voltage_v == Decimal("200")
    assert restored._current_voltage_v == Decimal("400")  # tick not yet
    assert restored == device


def test_snapshot_roundtrip_without_fault_state_defaults_to_nominal() -> None:
    """ADR 0025 §2.2 Backward-Compat: Welle-1-Snapshots ohne
    Voltage-Felder + fault_state defaulten auf nominal_voltage_v
    bzw. False."""
    device = _grid_device()
    state = dict(device.snapshot())
    state.pop("fault_state", None)
    state.pop("current_voltage_v", None)
    state.pop("pending_voltage_v", None)
    restored = GridConnectionDevice.from_snapshot(state)
    assert restored._voltage_drop_active is False
    assert restored._pending_voltage_v == Decimal("400")
    assert restored._current_voltage_v == Decimal("400")


def test_snapshot_with_unknown_fault_keys_ignored() -> None:
    """Welle-2-Review M-1 Forward-Compat: unbekannte fault_state-
    Keys werden ignoriert (Welle-3-Forward-Compat)."""
    device = _grid_device()
    state = dict(device.snapshot())
    state["fault_state"] = {
        "voltage_drop_active": True,
        "frequency_drop_active": True,  # Welle-3-Forward-Compat
    }
    restored = GridConnectionDevice.from_snapshot(state)
    assert restored._voltage_drop_active is True
    # Unbekannter Welle-3-Key wird ignoriert.
