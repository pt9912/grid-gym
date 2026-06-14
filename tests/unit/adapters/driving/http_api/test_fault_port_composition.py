"""Unit-Tests fuer `_compose_fault_port` aus
`_demo_scenario_setup.py` (ADR 0059 — generische Single-Engine).

Pinnt:
- None-on-empty-faults Vertrag (Default-Welle-5-Verhalten).
- Eine bekannte Fault-Liste → eine `ScenarioFaultEngine`
  (vorher `_FaultPortComposition`; Welle-6a Decision 19 abgeloest).
- Unbekannte YAML-fault-Typen werden fail-fast rejected
  (Welle-6a-Review F13, `_DemoScenarioUnknownFaultTypeError`).
- **D-8**: die drei neuen Welle-2-Fault-Typen
  (`connection_loss`/`winding_fault`/`genset_fault`) werden NICHT
  mehr rejected, sondern in die Engine aufgenommen.
"""

from __future__ import annotations

import pytest

from grid_gym.composition._demo_scenario_setup import (
    _DemoScenarioUnknownFaultTypeError,
    _compose_fault_port,
)
from grid_gym.hexagon.core.domain.scenario import ScenarioFault
from grid_gym.hexagon.core.faults import ScenarioFaultEngine
from grid_gym.hexagon.core.faults.types import (
    FAULT_TYPE_CONNECTION_LOSS,
    FAULT_TYPE_GENSET_FAULT,
    FAULT_TYPE_WINDING_FAULT,
)


def _fault(target: str, fault_type: str) -> ScenarioFault:
    return ScenarioFault(
        start_simulation_time=10000,
        duration_ms=5000,
        target=target,
        type=fault_type,
        payload={},
        recovery="auto-recover-after-N-ticks",
    )


def test_compose_fault_port_returns_none_for_empty_faults() -> None:
    """Leere Fault-Liste ist kein FaultPort-Wiring
    (TickLoopWiring.fault_port-Default greift)."""
    assert _compose_fault_port(()) is None


def test_compose_fault_port_returns_single_engine() -> None:
    """ADR 0059: eine bekannte Fault-Liste wird zu EINER
    generischen `ScenarioFaultEngine` (kein `_FaultPortComposition`
    mehr)."""
    engine = _compose_fault_port((_fault("battery-1", "cell_failure"),))
    assert isinstance(engine, ScenarioFaultEngine)


def test_compose_fault_port_rejects_unknown_fault_type() -> None:
    """Welle-6a-Review F13: unbekannte fault.type-Werte werden
    fail-fast rejected mit `_DemoScenarioUnknownFaultTypeError`."""
    unknown = _fault("battery-1", "thermal_runaway")  # not in _KNOWN_FAULT_TYPES
    with pytest.raises(_DemoScenarioUnknownFaultTypeError) as exc_info:
        _compose_fault_port((unknown,))
    assert "thermal_runaway" in str(exc_info.value)
    assert "cell_failure" in str(exc_info.value)
    assert "voltage_drop" in str(exc_info.value)


@pytest.mark.parametrize(
    ("target", "fault_type"),
    [
        ("ev-1", FAULT_TYPE_CONNECTION_LOSS),
        ("tr-1", FAULT_TYPE_WINDING_FAULT),
        ("dg-1", FAULT_TYPE_GENSET_FAULT),
    ],
)
def test_compose_fault_port_accepts_new_welle2_fault_types(target: str, fault_type: str) -> None:
    """D-8: die drei neuen Welle-2-Fault-Typen werden seit ADR 0059
    von `_compose_fault_port` akzeptiert (frueher
    `_DemoScenarioUnknownFaultTypeError` beim `make demo`-Startup)."""
    engine = _compose_fault_port((_fault(target, fault_type),))
    assert isinstance(engine, ScenarioFaultEngine)
