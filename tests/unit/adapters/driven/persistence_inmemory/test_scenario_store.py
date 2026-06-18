"""Pins fuer `InMemoryScenarioStore` (Multi-Run-Execution S1, ADR 0069 §2.1).

Happy: put → get roundtrip + exists. Boundary: idempotenter Overwrite.
Negative: unbekannter Hash → None.
"""

from __future__ import annotations

from grid_gym.adapters.driven.persistence_inmemory import InMemoryScenarioStore
from grid_gym.hexagon.core.scenario.loader import load_scenario

_HASH_A = "a" * 64
_HASH_B = "b" * 64


def _minimal_scenario() -> object:
    return load_scenario(
        {
            "schema_version": "grid-gym.scenario.v1",
            "metadata": {"id": "demo", "name": "Demo Scenario"},
            "simulation": {"tick_ms": 100, "duration_s": 60, "seed": 42},
            "devices": [{"id": "grid-1", "type": "grid_connection", "params": {}}],
        }
    ).scenario


def test_put_then_get_roundtrips_scenario() -> None:
    store = InMemoryScenarioStore()
    scenario = _minimal_scenario()
    store.put(_HASH_A, scenario)
    assert store.get(_HASH_A) == scenario


def test_get_unknown_hash_returns_none() -> None:
    store = InMemoryScenarioStore()
    assert store.get(_HASH_B) is None


def test_exists_reflects_put() -> None:
    store = InMemoryScenarioStore()
    assert store.exists(_HASH_A) is False
    store.put(_HASH_A, _minimal_scenario())
    assert store.exists(_HASH_A) is True


def test_put_is_idempotent_overwrite() -> None:
    store = InMemoryScenarioStore()
    scenario = _minimal_scenario()
    store.put(_HASH_A, scenario)
    store.put(_HASH_A, scenario)  # idempotent: kein Duplikat-Fehler
    assert store.get(_HASH_A) == scenario
