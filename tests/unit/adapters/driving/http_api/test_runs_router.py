"""Tests fuer `_runs_router.py` (M5 Welle 1 + Welle 4a, ADR 0037 +
0039).

Drei GET-Endpunkte:

- `GET /runs/{run_id}` — Run-Detail.
- `GET /runs/{run_id}/status` — Kompakter Run-Status (Welle-4a-
  Wiring auf RunRepository + TickLoopRegistry).
- `GET /runs/{run_id}/snapshot` — Snapshot-Export-Stub.

Plus 404-Pfade mit `GG-API-004`-Fehler-Format.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driven.alarm_stream_inmemory import (
    AlarmHistoryBuffer,
    InMemoryAlarmStream,
)
from grid_gym.adapters.driving.http_api import app
from grid_gym.adapters.driving.http_api._alarm_setup import configure_alarm_stream
from grid_gym.adapters.driving.http_api._tick_loop_registry import TickLoopRegistry
from grid_gym.adapters.driving.http_api.app import (
    configure_run_repository,
    configure_tick_loop_registry,
)
from grid_gym.hexagon.core.domain.alarm import Alarm
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import (
    FakeClock,
    FixedSeedRandom,
    InMemoryRunRepository,
)


@pytest.fixture
def configured_app() -> Iterator[tuple[TestClient, InMemoryRunRepository, TickLoopRegistry]]:
    """App mit frischem `InMemoryRunRepository` + `TickLoopRegistry`
    + `AlarmStream` + `AlarmHistoryBuffer` pro Test."""
    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    registry = TickLoopRegistry()
    configure_tick_loop_registry(registry)
    configure_alarm_stream(InMemoryAlarmStream(), AlarmHistoryBuffer())
    with TestClient(app) as client:
        yield client, repository, registry


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
    configured_app: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    client, repository, _ = configured_app
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
    configured_app: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    client, _, _ = configured_app
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


def test_get_run_status_returns_pending_without_tick_loop(
    configured_app: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    """Welle-4a: ohne registrierten TickLoop ist Status `pending` und
    Counter `0` (Welle-1-Stub-Erbschaft fuer rein persistierte
    Runs)."""
    client, repository, _ = configured_app
    metadata = _seed_run(repository)
    response = client.get(f"/runs/{metadata.run_id}/status")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == metadata.run_id
    assert body["state"] == "pending"
    assert body["simulation_time"] == 0
    assert body["tick_count"] == 0


def test_get_run_status_reflects_running_tick_loop_counters(
    configured_app: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    """Welle-4a (ADR 0039 Decision 14): registrierter TickLoop + drei
    Ticks → `state=running`, `tick_count=3`, `simulation_time=300`."""
    client, repository, registry = configured_app
    metadata = _seed_run(repository)
    tick_loop = TickLoop(
        run_id=metadata.run_id,
        tick_ms=metadata.tick_ms,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=metadata.seed),
        scheduler=Scheduler(),
        run_repository=repository,
    )
    registry.register(tick_loop)
    for _ in range(3):
        tick_loop.tick()
    response = client.get(f"/runs/{metadata.run_id}/status")
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "running"
    assert body["tick_count"] == 3
    assert body["simulation_time"] == 3 * metadata.tick_ms


def test_get_run_status_reflects_paused_state_after_request_pause(
    configured_app: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    """Welle-4a: nach `request_pause` zeigt `/status` den `paused`-
    State; `tick_count` wird durch nachfolgendes `tick()` nicht
    weitergetrieben (Pre-Tick-Guard)."""
    client, repository, registry = configured_app
    metadata = _seed_run(repository)
    tick_loop = TickLoop(
        run_id=metadata.run_id,
        tick_ms=metadata.tick_ms,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=metadata.seed),
        scheduler=Scheduler(),
        run_repository=repository,
    )
    registry.register(tick_loop)
    tick_loop.tick()
    tick_loop.request("pause")
    tick_loop.tick()  # No-op durch Pre-Tick-Guard
    response = client.get(f"/runs/{metadata.run_id}/status")
    body = response.json()
    assert body["state"] == "paused"
    assert body["tick_count"] == 1


def test_get_run_status_returns_404_for_unknown_run(
    configured_app: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    client, _, _ = configured_app
    run_id = str(uuid.uuid4())
    response = client.get(f"/runs/{run_id}/status")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "run_not_found"


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/snapshot
# ---------------------------------------------------------------------------


def test_get_run_snapshot_returns_schema_ref(
    configured_app: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    """Welle-1-Stub: nur `schema_ref`-Pointer, kein Snapshot-Body."""
    client, repository, _ = configured_app
    metadata = _seed_run(repository)
    response = client.get(f"/runs/{metadata.run_id}/snapshot")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == metadata.run_id
    assert body["schema_ref"] == "grid-gym.snapshot.envelope.v2"


def test_get_run_snapshot_returns_404_for_unknown_run(
    configured_app: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    client, _, _ = configured_app
    run_id = str(uuid.uuid4())
    response = client.get(f"/runs/{run_id}/snapshot")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "run_not_found"


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/alarms (M5 Welle 4b, ADR 0040 Decision 17)
# ---------------------------------------------------------------------------


def _make_alarm(run_id: str, alarm_id: str = "a0") -> Alarm:
    return Alarm(
        alarm_id=alarm_id,
        run_id=run_id,
        simulation_time_ms=100,
        target="battery-1",
        code="power_clamp_limited",
        severity="warning",
        message="msg",
        status="active",
        fault_id=None,
    )


def test_get_run_alarms_returns_history_buffer_contents(
    configured_app: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    """Welle-4b (ADR 0040 Decision 17): GET /alarms liefert die
    Alarms aus dem AlarmHistoryBuffer; neueste zuerst."""
    client, repository, _ = configured_app
    metadata = _seed_run(repository)
    # Inject alarms direkt in den buffer ueber app.state.
    buffer = app.state.alarm_history_buffer
    for i in range(3):
        buffer.append(_make_alarm(metadata.run_id, alarm_id=f"a-{i}"))
    response = client.get(f"/runs/{metadata.run_id}/alarms-history")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == metadata.run_id
    alarm_ids = [a["alarm_id"] for a in body["alarms"]]
    assert alarm_ids == ["a-2", "a-1", "a-0"]


def test_get_run_alarms_returns_404_for_unknown_run(
    configured_app: tuple[TestClient, InMemoryRunRepository, TickLoopRegistry],
) -> None:
    client, _, _ = configured_app
    run_id = str(uuid.uuid4())
    response = client.get(f"/runs/{run_id}/alarms-history")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "run_not_found"
