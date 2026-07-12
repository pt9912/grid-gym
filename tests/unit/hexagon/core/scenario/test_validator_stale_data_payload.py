"""Validator-Tests fuer die `stale_data`-Payload-Schaerfung
(ADR 0074 §2.1; Slice 072 / GG-FAULT-002).

`_assert_fault_list` verlangt fuer `type == "stale_data"` ein
`payload["metric"]: str` **und** ein `payload["max_age_ms"]: int > 0`
(die metrik-adressierte Zielgroesse + das Alter-Fenster). Fehlend →
`ScenarioMissingKeysError`; fehltypisiert → `ScenarioWrongTypeError`;
nicht-positiv → `ScenarioInvalidStaleDataMaxAgeError`. Beide Parameter
reisen bewusst im `payload` (kein `ScenarioFault.metric`-Schema-Feld,
das den `scenario_hash` aller Szenarien flippen wuerde).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.errors import (
    ScenarioInvalidStaleDataMaxAgeError,
    ScenarioMissingKeysError,
    ScenarioWrongTypeError,
)
from grid_gym.hexagon.core.scenario.loader import load_scenario

# Slice 054/072: fault-Sensor-Traeger fuer `make test-fault`.
pytestmark = pytest.mark.fault


def _scenario_with_stale_fault(payload: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "slice-072", "name": "stale-data-validator"},
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
                "type": "stale_data",
                "payload": payload,
                "recovery": "auto",
            },
        ],
    }


def test_accepts_stale_data_with_metric_and_max_age() -> None:
    """Happy-Path: `metric: str` + `max_age_ms: int > 0` akzeptiert."""
    loaded = load_scenario(_scenario_with_stale_fault({"metric": "voltage_v", "max_age_ms": 2000}))
    fault = loaded.scenario.faults[0]
    assert fault.type == "stale_data"
    assert fault.payload["metric"] == "voltage_v"
    assert fault.payload["max_age_ms"] == 2000


def test_rejects_stale_data_missing_metric() -> None:
    """ADR 0074 §2.1: fehlender `metric`-Key → `ScenarioMissingKeysError`."""
    with pytest.raises(ScenarioMissingKeysError) as exc_info:
        load_scenario(_scenario_with_stale_fault({"max_age_ms": 2000}))
    assert "metric" in str(exc_info.value)


def test_rejects_stale_data_missing_max_age() -> None:
    """ADR 0074 §2.1: fehlender `max_age_ms`-Key → `ScenarioMissingKeysError`."""
    with pytest.raises(ScenarioMissingKeysError) as exc_info:
        load_scenario(_scenario_with_stale_fault({"metric": "voltage_v"}))
    assert "max_age_ms" in str(exc_info.value)


def test_rejects_stale_data_non_str_metric() -> None:
    """ADR 0074 §2.1: fehltypisierter `metric` → `ScenarioWrongTypeError`."""
    with pytest.raises(ScenarioWrongTypeError):
        load_scenario(_scenario_with_stale_fault({"metric": Decimal("1"), "max_age_ms": 2000}))


def test_rejects_stale_data_non_int_max_age() -> None:
    """ADR 0074 §2.1: fehltypisierter `max_age_ms` → `ScenarioWrongTypeError`.
    `bool` wird als `int`-Subklasse ausdruecklich abgelehnt."""
    with pytest.raises(ScenarioWrongTypeError):
        load_scenario(
            _scenario_with_stale_fault({"metric": "voltage_v", "max_age_ms": Decimal("2000")})
        )
    with pytest.raises(ScenarioWrongTypeError):
        load_scenario(_scenario_with_stale_fault({"metric": "voltage_v", "max_age_ms": True}))


def test_rejects_stale_data_non_positive_max_age() -> None:
    """ADR 0074 §2.1: `max_age_ms <= 0` ist eine Policy-Verletzung →
    `ScenarioInvalidStaleDataMaxAgeError` (ein Alter-Fenster ≤ 0 ist
    fachlich sinnlos)."""
    for invalid in (0, -1):
        with pytest.raises(ScenarioInvalidStaleDataMaxAgeError):
            load_scenario(
                _scenario_with_stale_fault({"metric": "voltage_v", "max_age_ms": invalid})
            )
