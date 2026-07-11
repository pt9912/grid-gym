"""Validator-Tests fuer die `nan_injection`-Payload-Schaerfung
(ADR 0074 §2.1; Slice 071 / GG-FAULT-003).

`_assert_fault_list` verlangt fuer `type == "nan_injection"` ein
`payload["metric"]: str` (die metrik-adressierte Zielgroesse). Fehlend
→ `ScenarioMissingKeysError`; fehltypisiert → `ScenarioWrongTypeError`.
Die Metrik reist bewusst im `payload` (kein `ScenarioFault.metric`-
Schema-Feld, das den `scenario_hash` aller Szenarien flippen wuerde).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.errors import ScenarioMissingKeysError, ScenarioWrongTypeError
from grid_gym.hexagon.core.scenario.loader import load_scenario


def _scenario_with_nan_fault(payload: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "slice-071", "name": "nan-injection-validator"},
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
                "target": "load-1",
                "type": "nan_injection",
                "payload": payload,
                "recovery": "auto",
            },
        ],
    }


def test_accepts_nan_injection_with_str_metric() -> None:
    """Happy-Path: `payload["metric"]: str` wird akzeptiert."""
    loaded = load_scenario(_scenario_with_nan_fault({"metric": "voltage_v"}))
    assert loaded.scenario.faults[0].type == "nan_injection"
    assert loaded.scenario.faults[0].payload["metric"] == "voltage_v"


def test_rejects_nan_injection_missing_metric() -> None:
    """ADR 0074 §2.1: fehlender `metric`-Key → typisierter
    `ScenarioMissingKeysError`."""
    with pytest.raises(ScenarioMissingKeysError) as exc_info:
        load_scenario(_scenario_with_nan_fault({}))
    assert "metric" in str(exc_info.value)


def test_rejects_nan_injection_non_str_metric() -> None:
    """ADR 0074 §2.1: fehltypisierter `metric`-Wert → typisierter
    `ScenarioWrongTypeError`."""
    with pytest.raises(ScenarioWrongTypeError):
        load_scenario(_scenario_with_nan_fault({"metric": Decimal("1")}))
