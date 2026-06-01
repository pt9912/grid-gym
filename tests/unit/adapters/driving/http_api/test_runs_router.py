"""Tests fuer `_runs_router.py` (M5 Welle 1, ADR 0037).

Drei GET-Endpunkte:

- `GET /runs/{run_id}` — Run-Detail.
- `GET /runs/{run_id}/status` — Kompakter Run-Status.
- `GET /runs/{run_id}/snapshot` — Snapshot-Export-Stub.

Plus 404-Pfade mit `GG-API-004`-Fehler-Format.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driving.http_api import app
from grid_gym.adapters.driving.http_api.app import configure_run_repository
from grid_gym.hexagon.core.domain.run import RunMetadata
from tests.unit.hexagon.ports.driven._fakes import InMemoryRunRepository


@pytest.fixture
def configured_app() -> Iterator[tuple[TestClient, InMemoryRunRepository]]:
    """App mit frischem `InMemoryRunRepository` pro Test."""
    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    with TestClient(app) as client:
        yield client, repository


def _seed_run(repository: InMemoryRunRepository) -> RunMetadata:
    """Speichert einen Test-Run und gibt die Metadaten zurueck."""
    metadata = RunMetadata(
        run_id=str(uuid.uuid4()),
        scenario_hash="0" * 64,
        schema_version="grid-gym.scenario.v1",
        seed=42,
        tick_ms=100,
        started_at="",
        ended_at="",
        tool_version="0.1.0",
    )
    repository.save(metadata)
    return metadata


# ---------------------------------------------------------------------------
# GET /runs/{run_id}
# ---------------------------------------------------------------------------


def test_get_run_returns_full_metadata(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    client, repository = configured_app
    metadata = _seed_run(repository)
    response = client.get(f"/runs/{metadata.run_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == metadata.run_id
    assert body["scenario_hash"] == metadata.scenario_hash
    assert body["schema_version"] == metadata.schema_version
    assert body["seed"] == metadata.seed
    assert body["tick_ms"] == metadata.tick_ms
    assert body["started_at"] == metadata.started_at
    assert body["ended_at"] == metadata.ended_at
    assert body["tool_version"] == metadata.tool_version


def test_get_run_returns_404_for_unknown_run(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    client, _ = configured_app
    run_id = str(uuid.uuid4())
    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "run_not_found"
    assert detail["run_id"] == run_id
    assert run_id in detail["message"]


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/status
# ---------------------------------------------------------------------------


def test_get_run_status_returns_pending_stub(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Welle-1-Stub: Status ist immer `pending`, Counter `0`."""
    client, repository = configured_app
    metadata = _seed_run(repository)
    response = client.get(f"/runs/{metadata.run_id}/status")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == metadata.run_id
    assert body["state"] == "pending"
    assert body["simulation_time"] == 0
    assert body["tick_count"] == 0


def test_get_run_status_returns_404_for_unknown_run(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    client, _ = configured_app
    run_id = str(uuid.uuid4())
    response = client.get(f"/runs/{run_id}/status")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "run_not_found"


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/snapshot
# ---------------------------------------------------------------------------


def test_get_run_snapshot_returns_schema_ref(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Welle-1-Stub: nur `schema_ref`-Pointer, kein Snapshot-Body."""
    client, repository = configured_app
    metadata = _seed_run(repository)
    response = client.get(f"/runs/{metadata.run_id}/snapshot")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == metadata.run_id
    assert body["schema_ref"] == "grid-gym.snapshot.envelope.v2"


def test_get_run_snapshot_returns_404_for_unknown_run(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    client, _ = configured_app
    run_id = str(uuid.uuid4())
    response = client.get(f"/runs/{run_id}/snapshot")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "run_not_found"
