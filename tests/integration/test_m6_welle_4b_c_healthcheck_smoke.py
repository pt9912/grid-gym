"""End-to-End-Integration-Smoke fuer M6-Welle-4b-c
(`GG-RT-001` Backpressure-Healthcheck-Endpoint).

Pinnt die produktive Wiring-Composition aus C2:

1. ``POST /runs`` → 201 + run_id.
2. TickLoop registrieren + TickLoopHealthcheckAdapter konstruieren
   und in der Registry registrieren.
3. Mehrere `record_tick_duration`-Calls simulieren echten Driver-
   Mess-Pfad.
4. ``GET /runs/{id}/healthcheck`` → 200 + 6-Feld-JSON-Output mit
   erwarteten Werten.

Zusatz-Pflicht (Welle-4b-c §1.2):

- 404 bei nicht-existentem Run (vor 503-Pfad gepruft).
- 503 wenn Run existiert aber Healthcheck-Adapter nicht registriert.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driven.telemetry_stream_inmemory import (
    InMemoryTelemetryStream,
)
from grid_gym.adapters.driving.http_api import app
from grid_gym.adapters.driving.http_api._tick_loop_healthcheck import (
    TickLoopHealthcheckAdapter,
)
from grid_gym.adapters.driving.http_api._tick_loop_registry import TickLoopRegistry
from grid_gym.adapters.driving.http_api.app import (
    configure_run_repository,
    configure_telemetry_stream,
    configure_tick_loop_registry,
)
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import (
    FakeClock,
    FixedSeedRandom,
    InMemoryRunRepository,
)

_VALID_SCENARIO_HASH = "0" * 64
_VALID_RUN_PAYLOAD: dict[str, object] = {
    "scenario_hash": _VALID_SCENARIO_HASH,
    "seed": 42,
    "tick_ms": 10,
}


@pytest.fixture
def smoke_client() -> Iterator[tuple[TestClient, InMemoryRunRepository, TickLoopRegistry]]:
    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    configure_telemetry_stream(InMemoryTelemetryStream(queue_maxsize=8))
    registry = TickLoopRegistry()
    configure_tick_loop_registry(registry)
    with TestClient(app) as client:
        yield client, repository, registry


def _register_with_healthcheck(
    run_id: str,
    repository: InMemoryRunRepository,
    registry: TickLoopRegistry,
) -> TickLoopHealthcheckAdapter:
    """Welle-4b-c-D-1: Demo-Setup registriert sowohl den TickLoop
    als auch den Healthcheck-Adapter (Welle-4b-c-Wiring-Pattern)."""

    tick_loop = TickLoop(
        run_id=run_id,
        tick_ms=10,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        run_repository=repository,
    )
    registry.register(tick_loop)
    adapter = TickLoopHealthcheckAdapter(tick_loop, window_size=100)
    registry.register_healthcheck_adapter(run_id, adapter)
    return adapter


def test_healthcheck_full_lifecycle_workflow(
    smoke_client: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    """End-to-End-Smoke: Run + TickLoop + Adapter + Driver-Mess +
    GET /healthcheck."""

    client, repository, registry = smoke_client

    create_response = client.post("/runs", json=_VALID_RUN_PAYLOAD)
    assert create_response.status_code == 201
    run_id = create_response.json()["run_id"]
    uuid.UUID(run_id)

    adapter = _register_with_healthcheck(run_id, repository, registry)
    for duration in [3.0, 5.0, 8.0, 9.5, 11.0]:
        adapter.record_tick_duration(duration)

    healthcheck_response = client.get(f"/runs/{run_id}/healthcheck")
    assert healthcheck_response.status_code == 200
    body = healthcheck_response.json()

    assert body["tick_ms"] == 10
    assert body["window_size"] == 5
    assert body["missed_ticks_count"] == 1
    assert body["backpressure_status"] == "delayed"
    assert isinstance(body["tick_duration_ms_p50"], float)
    assert isinstance(body["tick_duration_ms_p95"], float)


def test_healthcheck_returns_404_for_unknown_run(
    smoke_client: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    """Welle-4b-c §1.2: 404 vor 503 (Run-Existenz wird zuerst
    geprueft)."""

    client, _, _ = smoke_client

    response = client.get("/runs/non-existent-run-id/healthcheck")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "run_not_found"


def test_healthcheck_returns_503_when_adapter_not_registered(
    smoke_client: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    """Welle-4b-c §1.2: Run existiert (Repository), aber kein
    Healthcheck-Adapter registriert → 503."""

    client, _, _ = smoke_client

    create_response = client.post("/runs", json=_VALID_RUN_PAYLOAD)
    assert create_response.status_code == 201
    run_id = create_response.json()["run_id"]

    response = client.get(f"/runs/{run_id}/healthcheck")
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["code"] == "healthcheck_not_available"
