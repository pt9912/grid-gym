"""Tests fuer den HTTP-API-Adapter (M1 Welle 6a/6b).

Nutzt `fastapi.testclient.TestClient` (`httpx`-basiert) — kein
echter ASGI-Loop noetig. Welle 6b haengt `POST /runs` an den
`RunRepositoryPort` ueber `configure_run_repository`; die Tests
nutzen `InMemoryRunRepository` aus `_fakes.py`.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driving.http_api import app
from grid_gym.adapters.driving.http_api.app import configure_run_repository
from tests.unit.hexagon.ports.driven._fakes import InMemoryRunRepository

_VALID_SCENARIO_HASH = "0" * 64
_VALID_PAYLOAD: dict[str, object] = {
    "scenario_hash": _VALID_SCENARIO_HASH,
    "seed": 42,
    "tick_ms": 100,
}


@pytest.fixture
def configured_app() -> Iterator[tuple[TestClient, InMemoryRunRepository]]:
    """App mit frischem InMemoryRunRepository pro Test.

    `app.state.run_repository` ist Modul-global; um Test-
    Interferenz auszuschliessen, wird vor jedem Test eine neue
    `InMemoryRunRepository` injiziert.
    """
    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    with TestClient(app) as client:
        yield client, repository


def test_health_returns_ok(configured_app: tuple[TestClient, InMemoryRunRepository]) -> None:
    client, _ = configured_app
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_runs_returns_uuid_and_echoes_inputs(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    client, _ = configured_app
    response = client.post("/runs", json=_VALID_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["scenario_hash"] == _VALID_SCENARIO_HASH
    assert body["seed"] == 42
    assert body["tick_ms"] == 100
    # `run_id` muss ein valides UUID sein.
    parsed = uuid.UUID(body["run_id"])
    assert parsed.version == 4


def test_post_runs_persists_metadata_via_repository(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Welle 6b: POST /runs persistiert ueber den
    `RunRepositoryPort` — die Metadata muss im Store
    auffindbar sein."""
    client, repository = configured_app
    body = client.post("/runs", json=_VALID_PAYLOAD).json()
    run_id = body["run_id"]
    persisted = repository.get_by_id(run_id)
    assert persisted.scenario_hash == _VALID_SCENARIO_HASH
    assert persisted.seed == 42
    assert persisted.tick_ms == 100
    assert persisted.schema_version == "grid-gym.scenario.v1"


def test_post_runs_returns_distinct_run_ids_for_repeated_calls(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    client, repository = configured_app
    first = client.post("/runs", json=_VALID_PAYLOAD).json()
    second = client.post("/runs", json=_VALID_PAYLOAD).json()
    assert first["run_id"] != second["run_id"]
    # Beide Eintraege landen im Repository.
    assert repository.exists(first["run_id"])
    assert repository.exists(second["run_id"])


# ---------------------------------------------------------------------------
# ADR 0068 (Slice 039 Phase A): API-Replay-Bindung `replay_of`.
# ---------------------------------------------------------------------------


def test_post_runs_without_replay_of_defaults_none(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    # Ohne `replay_of` ist der Lauf regulaer → null in Response + Store.
    client, repository = configured_app
    body = client.post("/runs", json=_VALID_PAYLOAD).json()
    assert body["replay_of"] is None
    assert repository.get_by_id(body["run_id"]).replay_of is None


def test_post_runs_with_valid_replay_of_persists_and_echoes(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    # ADR 0068 §2.2: ein Lauf laesst sich als Replay eines existierenden
    # Referenzlaufs anlegen; die Bindung wird persistiert + geechot.
    client, repository = configured_app
    reference_id = client.post("/runs", json=_VALID_PAYLOAD).json()["run_id"]
    response = client.post("/runs", json={**_VALID_PAYLOAD, "replay_of": reference_id})
    assert response.status_code == 201
    payload = response.json()
    assert payload["replay_of"] == reference_id
    assert repository.get_by_id(payload["run_id"]).replay_of == reference_id


def test_post_runs_with_unknown_replay_of_rejected_422(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    # ADR 0068 §2.2: `replay_of` auf einen nicht-existenten Lauf → 422
    # `reference_run_not_found`; es wird kein Lauf angelegt (Reject vor Save).
    client, repository = configured_app
    unknown = str(uuid.uuid4())
    response = client.post("/runs", json={**_VALID_PAYLOAD, "replay_of": unknown})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "reference_run_not_found"
    assert not repository.exists(unknown)


def test_get_run_exposes_replay_of(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    # ADR 0068: GET /runs/{id} gibt die persistierte `replay_of`-Bindung aus.
    client, _ = configured_app
    reference_id = client.post("/runs", json=_VALID_PAYLOAD).json()["run_id"]
    replay_id = client.post("/runs", json={**_VALID_PAYLOAD, "replay_of": reference_id}).json()[
        "run_id"
    ]
    detail = client.get(f"/runs/{replay_id}").json()
    assert detail["replay_of"] == reference_id


def test_post_runs_rejects_short_scenario_hash(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """`scenario_hash` ist Pflicht-64-Zeichen (Pydantic-Validierung)."""
    client, _ = configured_app
    bad = {**_VALID_PAYLOAD, "scenario_hash": "deadbeef"}
    response = client.post("/runs", json=bad)
    assert response.status_code == 422


def test_post_runs_rejects_negative_seed(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    client, _ = configured_app
    bad = {**_VALID_PAYLOAD, "seed": -1}
    response = client.post("/runs", json=bad)
    assert response.status_code == 422


def test_post_runs_rejects_zero_tick_ms(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """tick_ms muss > 0 sein (Welle-4-Review S2-Pattern)."""
    client, _ = configured_app
    bad = {**_VALID_PAYLOAD, "tick_ms": 0}
    response = client.post("/runs", json=bad)
    assert response.status_code == 422


def test_post_runs_rejects_missing_fields(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    client, _ = configured_app
    response = client.post("/runs", json={"scenario_hash": _VALID_SCENARIO_HASH})
    assert response.status_code == 422


def test_openapi_spec_is_generated_and_contains_routes(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """`make openapi-validate` (Dockerfile-Stage) erwartet eine
    gueltige OpenAPI-Definition mit den dokumentierten Pfaden."""
    client, _ = configured_app
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["title"] == "grid-gym HTTP API"
    paths = spec["paths"]
    assert "/health" in paths
    assert "/runs" in paths
    assert "post" in paths["/runs"]
    assert "get" in paths["/health"]


def test_post_runs_raises_if_repository_not_configured() -> None:
    """Schutz vor stillem Welle-6a-Fallback: ohne
    `configure_run_repository` muss der Endpoint scharf
    failen.

    Mit `raise_server_exceptions=False` reicht TestClient den
    Server-`RuntimeError` als 500-Status durch (statt ihn beim
    Aufrufer zu re-raisen). Pruefen wir nur, dass der
    Endpoint nicht stillschweigend 201 zurueckgibt.
    """
    # Wir setzen `app.state.run_repository` explizit auf None,
    # falls vorhergehender Test es konfiguriert hat.
    app.state.run_repository = None
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/runs", json=_VALID_PAYLOAD)
    assert response.status_code == 500
