"""Tests fuer den HTTP-API-Adapter (M1 Welle 6a).

Nutzt `fastapi.testclient.TestClient` (`httpx`-basiert) — kein
echter ASGI-Loop noetig. Welle-6a-Scope: `/health`, `POST /runs`
als Stub, `/openapi.json`-Generierung.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from grid_gym.adapters.driving.http_api import app

_VALID_SCENARIO_HASH = "0" * 64
_VALID_PAYLOAD: dict[str, object] = {
    "scenario_hash": _VALID_SCENARIO_HASH,
    "seed": 42,
    "tick_ms": 100,
}


def test_health_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_runs_returns_uuid_and_echoes_inputs() -> None:
    client = TestClient(app)
    response = client.post("/runs", json=_VALID_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["scenario_hash"] == _VALID_SCENARIO_HASH
    assert body["seed"] == 42
    assert body["tick_ms"] == 100
    # `run_id` muss ein valides UUID sein.
    parsed = uuid.UUID(body["run_id"])
    assert parsed.version == 4


def test_post_runs_returns_distinct_run_ids_for_repeated_calls() -> None:
    client = TestClient(app)
    first = client.post("/runs", json=_VALID_PAYLOAD).json()
    second = client.post("/runs", json=_VALID_PAYLOAD).json()
    assert first["run_id"] != second["run_id"]


def test_post_runs_rejects_short_scenario_hash() -> None:
    """`scenario_hash` ist Pflicht-64-Zeichen (Pydantic-Validierung)."""
    client = TestClient(app)
    bad = {**_VALID_PAYLOAD, "scenario_hash": "deadbeef"}
    response = client.post("/runs", json=bad)
    assert response.status_code == 422


def test_post_runs_rejects_negative_seed() -> None:
    client = TestClient(app)
    bad = {**_VALID_PAYLOAD, "seed": -1}
    response = client.post("/runs", json=bad)
    assert response.status_code == 422


def test_post_runs_rejects_zero_tick_ms() -> None:
    """tick_ms muss > 0 sein (Welle-4-Review S2-Pattern)."""
    client = TestClient(app)
    bad = {**_VALID_PAYLOAD, "tick_ms": 0}
    response = client.post("/runs", json=bad)
    assert response.status_code == 422


def test_post_runs_rejects_missing_fields() -> None:
    client = TestClient(app)
    response = client.post("/runs", json={"scenario_hash": _VALID_SCENARIO_HASH})
    assert response.status_code == 422


def test_openapi_spec_is_generated_and_contains_routes() -> None:
    """`make openapi-validate` (Dockerfile-Stage) erwartet eine
    gueltige OpenAPI-Definition mit den dokumentierten Pfaden."""
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["title"] == "grid-gym HTTP API"
    paths = spec["paths"]
    assert "/health" in paths
    assert "/runs" in paths
    assert "post" in paths["/runs"]
    assert "get" in paths["/health"]
