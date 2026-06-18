"""Pins fuer die Scenario-Intake-Bridge (Composition Root; Multi-Run-
Execution S1, ADR 0069 §2.1).

Happy: kanonisiert + hasht + legt im Store ab (inkl. `str → Decimal`-Koercion
der Device-Params). Negative: Hash-Mismatch, `float` an Decimal-Stelle,
malformed Decimal-String — jeweils typisierter Fehler, kein Store-Write.
"""

from __future__ import annotations

import pytest

from grid_gym.adapters.driven.persistence_inmemory import InMemoryScenarioStore
from grid_gym.composition.scenario_intake import intake_scenario
from grid_gym.hexagon.core.errors import ScenarioHashMismatchError, WrongTypeError
from grid_gym.hexagon.core.scenario.loader import load_scenario
from grid_gym.scenario_yaml import (
    ScenarioYamlDecimalCoercionError,
    coerce_scenario_mapping,
)

_BOGUS_HASH = "f" * 64


def _raw_minimal() -> dict[str, object]:
    return {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "demo", "name": "Demo Scenario"},
        "simulation": {"tick_ms": 100, "duration_s": 60, "seed": 42},
        "devices": [{"id": "grid-1", "type": "grid_connection", "params": {}}],
    }


def _raw_battery(capacity_kwh: object = "1000") -> dict[str, object]:
    """Battery-Szenario mit Decimal-Params als Strings (Variante A).
    `capacity_kwh` parametrisierbar fuer die Negativ-Pfade."""
    return {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "bat", "name": "Battery Scenario"},
        "simulation": {"tick_ms": 100, "duration_s": 60, "seed": 7},
        "devices": [
            {
                "id": "battery-1",
                "type": "battery",
                "params": {
                    "capacity_kwh": capacity_kwh,
                    "initial_soc_pct": "50",
                    "max_charge_kw": "500",
                    "max_discharge_kw": "500",
                },
            }
        ],
    }


def _expected_hash(raw: dict[str, object]) -> str:
    return load_scenario(coerce_scenario_mapping(raw)).scenario_hash


def test_intake_stores_scenario_on_matching_hash() -> None:
    store = InMemoryScenarioStore()
    raw = _raw_minimal()
    claimed = _expected_hash(raw)
    returned = intake_scenario(store, raw, claimed)
    assert returned == claimed
    assert store.exists(claimed)
    assert store.get(claimed) is not None


def test_intake_coerces_decimal_string_params() -> None:
    store = InMemoryScenarioStore()
    raw = _raw_battery()
    claimed = _expected_hash(raw)
    returned = intake_scenario(store, raw, claimed)
    assert returned == claimed
    assert store.exists(claimed)


def test_intake_rejects_hash_mismatch_without_write() -> None:
    store = InMemoryScenarioStore()
    raw = _raw_minimal()
    with pytest.raises(ScenarioHashMismatchError) as excinfo:
        intake_scenario(store, raw, _BOGUS_HASH)
    assert excinfo.value.claimed == _BOGUS_HASH
    assert excinfo.value.computed == _expected_hash(raw)
    assert not store.exists(_expected_hash(raw))


def test_intake_rejects_float_at_decimal_position() -> None:
    store = InMemoryScenarioStore()
    raw = _raw_battery(capacity_kwh=1000.5)  # float -> Validator: nicht canonical-kompatibel
    with pytest.raises(WrongTypeError):
        intake_scenario(store, raw, _BOGUS_HASH)


def test_intake_rejects_malformed_decimal_string() -> None:
    store = InMemoryScenarioStore()
    raw = _raw_battery(capacity_kwh="not-a-number")
    with pytest.raises(ScenarioYamlDecimalCoercionError):
        intake_scenario(store, raw, _BOGUS_HASH)
