"""Welle-6a-Review F12/F13/F14: Unit-Tests fuer
`_compose_fault_port` + `_FaultPortComposition` aus
`_demo_scenario_setup.py`.

Pinnt:
- None-on-empty-faults Vertrag (Default-Welle-5-Verhalten).
- Delegation-Reihenfolge Battery → Grid (deterministisch).
- Exception-Isolation: Battery-Adapter-Exception in Tick N
  ueberspringt den Grid-Adapter-Aufruf NICHT (F12, ADR-0021-
  §2.9-Determinismus).
- Unbekannte YAML-fault-Typen werden fail-fast rejected
  (F13, `_DemoScenarioUnknownFaultTypeError`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from grid_gym.adapters.driving.http_api._demo_scenario_setup import (
    _DemoScenarioUnknownFaultTypeError,
    _FaultPortComposition,
    _compose_fault_port,
)
from grid_gym.hexagon.core.domain.scenario import ScenarioFault

if TYPE_CHECKING:
    from grid_gym.hexagon.core.faults import BatteryFaultAdapter, GridFaultAdapter


def _make_cell_failure(start_ms: int = 10000, dur_ms: int = 5000) -> ScenarioFault:
    return ScenarioFault(
        start_simulation_time=start_ms,
        duration_ms=dur_ms,
        target="battery-1",
        type="cell_failure",
        payload={},
        recovery="auto-recover-after-N-ticks",
    )


def _make_voltage_drop(start_ms: int = 20000, dur_ms: int = 5000) -> ScenarioFault:
    return ScenarioFault(
        start_simulation_time=start_ms,
        duration_ms=dur_ms,
        target="grid-1",
        type="voltage_drop",
        payload={},
        recovery="auto-recover-after-N-ticks",
    )


def test_compose_fault_port_returns_none_for_empty_faults() -> None:
    """Welle-6a Decision 19: leere Fault-Liste ist kein
    FaultPort-Wiring (TickLoopWiring.fault_port-Default greift)."""
    assert _compose_fault_port(()) is None


def test_compose_fault_port_returns_composition_for_one_fault() -> None:
    """Single-fault YAML wird zu einer Composition mit beiden
    Adaptern (auch wenn ein Adapter intern leer filtert)."""
    composition = _compose_fault_port((_make_cell_failure(),))
    assert isinstance(composition, _FaultPortComposition)


def test_compose_fault_port_rejects_unknown_fault_type() -> None:
    """Welle-6a-Review F13: unbekannte fault.type-Werte werden
    fail-fast rejected mit `_DemoScenarioUnknownFaultTypeError`."""
    unknown_fault = ScenarioFault(
        start_simulation_time=10000,
        duration_ms=5000,
        target="battery-1",
        type="thermal_runaway",  # not in _KNOWN_FAULT_TYPES
        payload={},
        recovery="auto-recover-after-N-ticks",
    )
    with pytest.raises(_DemoScenarioUnknownFaultTypeError) as exc_info:
        _compose_fault_port((unknown_fault,))
    assert "thermal_runaway" in str(exc_info.value)
    assert "cell_failure" in str(exc_info.value)
    assert "voltage_drop" in str(exc_info.value)


def test_fault_port_composition_delegates_battery_then_grid() -> None:
    """Decision 19 + ADR 0025 §2.4: Reihenfolge Battery → Grid
    ist deterministisch. Pruefen, dass beide Adapter pro Tick
    aufgerufen werden und in der richtigen Reihenfolge."""
    composition = _compose_fault_port((_make_cell_failure(), _make_voltage_drop()))
    assert composition is not None
    call_order: list[str] = []
    with (
        patch.object(
            composition._battery_adapter,  # type: ignore[attr-defined]
            "apply_active_faults",
            side_effect=lambda *_: call_order.append("battery"),
        ),
        patch.object(
            composition._grid_adapter,  # type: ignore[attr-defined]
            "apply_active_faults",
            side_effect=lambda *_: call_order.append("grid"),
        ),
    ):
        composition.apply_active_faults((), context=None)  # type: ignore[arg-type]
    assert call_order == ["battery", "grid"]


def test_fault_port_composition_calls_grid_even_when_battery_raises() -> None:
    """Welle-6a-Review F12: eine Battery-Adapter-Exception in
    Tick N darf den Grid-Adapter im selben Tick **nicht**
    skippen — sonst verletzt das ADR-0021-§2.9-byte-identische-
    Telemetry-Determinismus. Battery-Exception wird re-raised
    NACH dem Grid-Call."""
    composition = _compose_fault_port((_make_cell_failure(), _make_voltage_drop()))
    assert composition is not None
    grid_calls: list[str] = []
    battery_err = RuntimeError("battery adapter glitched")
    with (
        patch.object(
            composition._battery_adapter,  # type: ignore[attr-defined]
            "apply_active_faults",
            side_effect=battery_err,
        ),
        patch.object(
            composition._grid_adapter,  # type: ignore[attr-defined]
            "apply_active_faults",
            side_effect=lambda *_: grid_calls.append("grid"),
        ),
        pytest.raises(RuntimeError, match="battery adapter glitched"),
    ):
        composition.apply_active_faults((), context=None)  # type: ignore[arg-type]
    assert grid_calls == ["grid"], (
        "Welle-6a-Review F12: Grid-Adapter muss trotz Battery-Exception "
        "im selben Tick laufen, sonst driften gleich-geseedete Runs auseinander."
    )
