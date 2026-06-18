"""Pins fuer `POST /scenarios` (Multi-Run-Execution S1, ADR 0069 §2.1).

Happy: 201 + Hash-Echo + Store-Write (Intake-Bridge registriert, mirror der
`composition.asgi`-Verdrahtung). Boundary: zu kurzer Hash → 422 (Pydantic).
Negative: Hash-Mismatch → 422 `scenario_hash_mismatch`; invalides Scenario →
422 `invalid_scenario`; Store/Intake nicht konfiguriert → 500.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import grid_gym.adapters.driving.http_api._scenarios_router as scenarios_router_module
from grid_gym.adapters.driven.persistence_inmemory import InMemoryScenarioStore
from grid_gym.adapters.driving.http_api._scenario_setup import configure_scenario_store
from grid_gym.adapters.driving.http_api.app import app
from grid_gym.composition.scenario_intake import intake_scenario
from grid_gym.hexagon.core.scenario.loader import load_scenario
from grid_gym.scenario_yaml import coerce_scenario_mapping

_BOGUS_HASH = "f" * 64


def _raw_minimal() -> dict[str, object]:
    return {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "demo", "name": "Demo Scenario"},
        "simulation": {"tick_ms": 100, "duration_s": 60, "seed": 42},
        "devices": [{"id": "grid-1", "type": "grid_connection", "params": {}}],
    }


def _expected_hash(raw: dict[str, object]) -> str:
    return load_scenario(coerce_scenario_mapping(raw)).scenario_hash


@pytest.fixture
def client_with_intake() -> Iterator[tuple[TestClient, InMemoryScenarioStore]]:
    """App mit registrierter Intake-Bridge + frischem Store — spiegelt die
    `composition.asgi`-Verdrahtung. Restauriert die Hook-/State-Globals."""
    store = InMemoryScenarioStore()
    configure_scenario_store(store)
    saved = scenarios_router_module._scenario_intake
    scenarios_router_module._register_scenario_intake(intake_scenario)
    try:
        with TestClient(app) as client:
            yield client, store
    finally:
        scenarios_router_module._scenario_intake = saved
        app.state.scenario_store = None


def test_post_scenarios_accepts_and_echoes_hash(
    client_with_intake: tuple[TestClient, InMemoryScenarioStore],
) -> None:
    client, store = client_with_intake
    raw = _raw_minimal()
    expected = _expected_hash(raw)
    resp = client.post("/scenarios", json={"scenario_hash": expected, "scenario": raw})
    assert resp.status_code == 201
    assert resp.json()["scenario_hash"] == expected
    assert store.exists(expected)


def test_post_scenarios_hash_mismatch_422(
    client_with_intake: tuple[TestClient, InMemoryScenarioStore],
) -> None:
    client, store = client_with_intake
    raw = _raw_minimal()
    resp = client.post("/scenarios", json={"scenario_hash": _BOGUS_HASH, "scenario": raw})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "scenario_hash_mismatch"
    assert not store.exists(_expected_hash(raw))


def test_post_scenarios_invalid_scenario_422(
    client_with_intake: tuple[TestClient, InMemoryScenarioStore],
) -> None:
    client, _ = client_with_intake
    # fehlende Pflicht-Keys (simulation/devices) -> ScenarioMissingKeysError
    bad = {"schema_version": "grid-gym.scenario.v1", "metadata": {"id": "x", "name": "X"}}
    resp = client.post("/scenarios", json={"scenario_hash": "0" * 64, "scenario": bad})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "invalid_scenario"


def test_post_scenarios_float_param_422(
    client_with_intake: tuple[TestClient, InMemoryScenarioStore],
) -> None:
    client, _ = client_with_intake
    bad = {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "bat", "name": "Battery"},
        "simulation": {"tick_ms": 100, "duration_s": 60, "seed": 7},
        "devices": [{"id": "battery-1", "type": "battery", "params": {"capacity_kwh": 1000.5}}],
    }
    resp = client.post("/scenarios", json={"scenario_hash": "0" * 64, "scenario": bad})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "invalid_scenario"


def test_post_scenarios_rejects_short_hash(
    client_with_intake: tuple[TestClient, InMemoryScenarioStore],
) -> None:
    client, _ = client_with_intake
    resp = client.post("/scenarios", json={"scenario_hash": "abc", "scenario": _raw_minimal()})
    assert resp.status_code == 422  # Pydantic min_length=64


def test_post_scenarios_store_not_configured_500() -> None:
    app.state.scenario_store = None
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/scenarios", json={"scenario_hash": "0" * 64, "scenario": _raw_minimal()})
    assert resp.status_code == 500


def test_post_scenarios_intake_not_registered_500() -> None:
    configure_scenario_store(InMemoryScenarioStore())
    saved = scenarios_router_module._scenario_intake
    scenarios_router_module._scenario_intake = (
        scenarios_router_module._raise_scenario_intake_unregistered
    )
    try:
        client = TestClient(app, raise_server_exceptions=False)
        raw = _raw_minimal()
        resp = client.post(
            "/scenarios", json={"scenario_hash": _expected_hash(raw), "scenario": raw}
        )
        assert resp.status_code == 500
    finally:
        scenarios_router_module._scenario_intake = saved
        app.state.scenario_store = None
