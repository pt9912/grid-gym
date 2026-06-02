"""End-to-End-Integration-Smoke fuer M5-Welle-4a (Replay-Controls
+ TickLoop-Wiring, ADR 0039).

Pinnt die produktive Wiring-Composition aus C0..C3:

1. ``POST /runs`` → 201 + run_id.
2. TickLoop registrieren, manuell zwei ``tick()`` ausfuehren
   (Demo-Driver-Aequivalent ohne asyncio-Task).
3. ``GET /runs/{id}/status`` zeigt ``running`` + Counter > 0.
4. ``POST /runs/{id}/control`` mit ``pause`` → 200 + Repository
   spiegelt ``paused``; weiterer ``tick()`` ist No-op (Pre-Tick-
   Guard).
5. ``POST /runs/{id}/control`` mit ``resume`` → 200 +
   `running`; Tick-Counter steigt wieder.
6. ``POST /runs/{id}/control`` mit ``stop`` → 200 + `stopped`;
   weiterer ``request_resume`` waere Invalid-Transition (409).
7. ``GET /runs/{id}/control`` (UI-Page) rendert die Replay-
   Controls mit HTMX-Buttons.
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
    "tick_ms": 100,
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


def _register_tick_loop(
    run_id: str,
    repository: InMemoryRunRepository,
    registry: TickLoopRegistry,
) -> TickLoop:
    tick_loop = TickLoop(
        run_id=run_id,
        tick_ms=100,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        run_repository=repository,
    )
    registry.register(tick_loop)
    return tick_loop


def test_replay_controls_full_lifecycle_workflow(
    smoke_client: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    """End-to-End-Smoke: Run anlegen → TickLoop registrieren →
    pause/resume/stop ueber den HTTP-Endpoint + Status-Polling."""
    client, repository, registry = smoke_client

    # 1. Run anlegen
    create_response = client.post("/runs", json=_VALID_RUN_PAYLOAD)
    assert create_response.status_code == 201
    run_id = create_response.json()["run_id"]
    uuid.UUID(run_id)
    assert repository.get_status(run_id) == "pending"

    # 2. TickLoop registrieren + 2 Ticks ausfuehren
    tick_loop = _register_tick_loop(run_id, repository, registry)
    tick_loop.tick()
    tick_loop.tick()
    assert tick_loop.tick_count == 2
    assert tick_loop.control_state == "running"
    assert repository.get_status(run_id) == "running"

    # 3. Status zeigt running + Counter
    status = client.get(f"/runs/{run_id}/status").json()
    assert status["state"] == "running"
    assert status["tick_count"] == 2
    assert status["simulation_time"] == 200

    # 4. Pause → repository spiegelt paused; weiterer tick() No-op
    pause = client.post(f"/runs/{run_id}/control", json={"action": "pause"})
    assert pause.status_code == 200
    assert repository.get_status(run_id) == "paused"
    result = tick_loop.tick()
    assert result.paused is True
    assert tick_loop.tick_count == 2  # kein Fortschritt

    # 5. Resume → running; weiterer tick() arbeitet
    resume = client.post(f"/runs/{run_id}/control", json={"action": "resume"})
    assert resume.status_code == 200
    assert repository.get_status(run_id) == "running"
    tick_loop.tick()
    assert tick_loop.tick_count == 3

    # 6. Stop → stopped; resume danach → 409 Invalid-Transition
    stop = client.post(f"/runs/{run_id}/control", json={"action": "stop"})
    assert stop.status_code == 200
    assert repository.get_status(run_id) == "stopped"
    resume_after_stop = client.post(
        f"/runs/{run_id}/control",
        json={"action": "resume"},
    )
    assert resume_after_stop.status_code == 409
    assert resume_after_stop.json()["detail"]["code"] == "invalid_transition"

    # 7. UI-Page rendert die Replay-Controls
    ui_response = client.get(f"/runs/{run_id}/control")
    assert ui_response.status_code == 200
    html = ui_response.text
    assert "Replay Controls" in html
    assert run_id in html
    assert 'hx-trigger="every 1s"' in html
