"""Validator-Negativ-Tests fuer Fault-Target-Existenz
(M3 Welle 1, ADR 0022 §2.3).

`_assert_fault_list` prueft seit Welle 1 zusaetzlich, ob
`fault.target` in `devices` existiert. Pattern parallel zu
`ScenarioUnknownEventTargetError`.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.errors import ScenarioUnknownFaultTargetError
from grid_gym.hexagon.core.scenario.loader import load_scenario


def _scenario_with_fault(target: str) -> dict[str, object]:
    return {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "welle-1-fault", "name": "Fault Target Test"},
        "simulation": {"tick_ms": 1000, "duration_s": 60, "seed": 42},
        "devices": [
            {
                "id": "load-1",
                "type": "load",
                "params": {"rated_power_kw": Decimal("100")},
            },
        ],
        "faults": [
            {
                "start_simulation_time": 0,
                "duration_ms": 5000,
                "target": target,
                "type": "voltage_drop",
                "payload": {},
                "recovery": "auto-recover-after-5-ticks",
            },
        ],
    }


def test_load_scenario_accepts_fault_with_known_target() -> None:
    """Happy-Path: Fault zeigt auf existierendes Device."""
    raw = _scenario_with_fault("load-1")
    loaded = load_scenario(raw)
    assert len(loaded.scenario.faults) == 1
    assert loaded.scenario.faults[0].target == "load-1"


def test_load_scenario_rejects_fault_with_unknown_target() -> None:
    """ADR 0022 §2.3: unbekannter Target → typisierter
    `ScenarioUnknownFaultTargetError`."""
    raw = _scenario_with_fault("ghost-battery-99")
    with pytest.raises(ScenarioUnknownFaultTargetError) as exc_info:
        load_scenario(raw)
    assert "ghost-battery-99" in str(exc_info.value)
