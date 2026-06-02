"""Tests fuer `_runs_action_router.py` (M5 Welle 1/3/4a, ADR 0037
+ 0038 + 0039).

Drei Endpunkte:

- `POST /runs/{run_id}/control` — Run-Steuerung mit Action-Body
  (`pause`/`resume`/`stop`; ADR 0037 Decision API-1; Welle-4a-
  Wiring auf TickLoop-Control-Surface per ADR 0039 Decision 13).
- `POST /runs/{run_id}/faults` — Fault-Injection-Submit
  (Welle-1-Stub).
- `WS /runs/{run_id}/telemetry` — Live-Telemetry-Stream
  (Welle-3 mit `TelemetryStreamPort.subscribe`-Pattern; ADR 0038).

Plus 404-Pfade fuer REST, 409 fuer Invalid-Transition (Welle-4a),
503 fuer TickLoop-not-active (Welle-4a) und Close-Code 1008 fuer
WebSocket bei nicht-existenten Runs.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

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
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driving.telemetry_stream import TelemetryPoint
from tests.unit.hexagon.ports.driven._fakes import (
    FakeClock,
    FixedSeedRandom,
    InMemoryRunRepository,
)


@pytest.fixture
def configured_app() -> Iterator[
    tuple[TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry]
]:
    """App mit frischem `InMemoryRunRepository` + `InMemoryTelemetryStream`
    + `TickLoopRegistry` (Welle-4a; ADR 0039 Decision 13)."""
    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    stream = InMemoryTelemetryStream(queue_maxsize=16)
    configure_telemetry_stream(stream)
    registry = TickLoopRegistry()
    configure_tick_loop_registry(registry)
    with TestClient(app) as client:
        yield client, repository, stream, registry


def _seed_run(repository: InMemoryRunRepository) -> RunMetadata:
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


def _seed_run_with_tick_loop(
    repository: InMemoryRunRepository,
    registry: TickLoopRegistry,
) -> tuple[RunMetadata, TickLoop]:
    """Welle-4a-Helper: erzeugt Run + registriert TickLoop, damit
    `POST /control` produktiv Wiring zum TickLoop hat."""
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
    return metadata, tick_loop


# ---------------------------------------------------------------------------
# POST /runs/{run_id}/control
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("action", ["pause", "resume", "stop"])
def test_post_run_control_accepts_valid_action(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
    action: str,
) -> None:
    """Welle-4a-Wiring: jede der drei Actions wird durch den
    TickLoop verarbeitet und mit `accepted=True` quittiert
    (ADR 0037 Decision API-1 + ADR 0039 Decision 13)."""
    client, repository, _, registry = configured_app
    metadata, _ = _seed_run_with_tick_loop(repository, registry)
    response = client.post(
        f"/runs/{metadata.run_id}/control",
        json={"action": action},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == metadata.run_id
    assert body["action"] == action
    assert body["accepted"] is True


def test_post_run_control_pause_mirrors_state_to_repository(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """Welle-4a (ADR 0039 Decision 12): `POST /control` mit
    `action=pause` persistiert `paused` im Repository."""
    client, repository, _, registry = configured_app
    metadata, _ = _seed_run_with_tick_loop(repository, registry)
    client.post(f"/runs/{metadata.run_id}/control", json={"action": "pause"})
    assert repository.get_status(metadata.run_id) == "paused"


def test_post_run_control_returns_503_when_no_tick_loop_registered(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """Welle-4a: Run persistiert, aber kein TickLoop in der
    Registry → 503 `tick_loop_not_active`."""
    client, repository, _, _ = configured_app
    metadata = _seed_run(repository)  # ohne `_seed_run_with_tick_loop`
    response = client.post(
        f"/runs/{metadata.run_id}/control",
        json={"action": "pause"},
    )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "tick_loop_not_active"


def test_post_run_control_returns_409_for_invalid_transition(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """Welle-4a (ADR 0039 Decision 13): `resume` auf einen bereits
    gestoppten Run → 409 `invalid_transition`."""
    client, repository, _, registry = configured_app
    metadata, _ = _seed_run_with_tick_loop(repository, registry)
    client.post(f"/runs/{metadata.run_id}/control", json={"action": "stop"})
    response = client.post(
        f"/runs/{metadata.run_id}/control",
        json={"action": "resume"},
    )
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "invalid_transition"
    assert detail["details"]["current_state"] == "stopped"
    assert detail["details"]["target_state"] == "running"


def test_post_run_control_rejects_invalid_action(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """Pydantic-Literal-Validation fuer ungueltige Actions → 422."""
    client, repository, _, registry = configured_app
    metadata, _ = _seed_run_with_tick_loop(repository, registry)
    response = client.post(
        f"/runs/{metadata.run_id}/control",
        json={"action": "restart"},
    )
    assert response.status_code == 422


def test_post_run_control_returns_404_for_unknown_run(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    client, _, _, _ = configured_app
    run_id = str(uuid.uuid4())
    response = client.post(
        f"/runs/{run_id}/control",
        json={"action": "pause"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "run_not_found"


# ---------------------------------------------------------------------------
# POST /runs/{run_id}/faults
# ---------------------------------------------------------------------------


def test_post_run_faults_returns_fault_id_with_201(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """Welle-1-Stub: 201 + UUID-Fault-ID + accepted=True."""
    client, repository, _, _ = configured_app
    metadata = _seed_run(repository)
    response = client.post(
        f"/runs/{metadata.run_id}/faults",
        json={
            "fault_type": "cell_failure",
            "target": "battery-1",
            "start_at_tick": 10,
            "duration_ticks": 20,
            "recovery": "auto-recover-after-N-ticks",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["run_id"] == metadata.run_id
    assert body["accepted"] is True
    # fault_id muss valide UUID sein
    uuid.UUID(body["fault_id"])


def test_post_run_faults_rejects_invalid_body(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """Pydantic-Validation: Missing-Field → 422."""
    client, repository, _, _ = configured_app
    metadata = _seed_run(repository)
    response = client.post(
        f"/runs/{metadata.run_id}/faults",
        json={"fault_type": "cell_failure"},  # missing other fields
    )
    assert response.status_code == 422


def test_post_run_faults_returns_404_for_unknown_run(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    client, _, _, _ = configured_app
    run_id = str(uuid.uuid4())
    response = client.post(
        f"/runs/{run_id}/faults",
        json={
            "fault_type": "cell_failure",
            "target": "battery-1",
            "start_at_tick": 10,
            "duration_ticks": 20,
            "recovery": "auto-recover-after-N-ticks",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "run_not_found"


# ---------------------------------------------------------------------------
# WS /runs/{run_id}/telemetry
# ---------------------------------------------------------------------------


def _make_point(run_id: str, sequence: int) -> TelemetryPoint:
    return TelemetryPoint(
        run_id=run_id,
        device_id="battery-1",
        metric="power",
        value=float(sequence),
        unit="kW",
        simulation_time_ms=sequence * 100,
        quality="ok",
        sequence=sequence,
    )


def test_ws_telemetry_pushes_subscribed_points(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """Welle-3 (ADR 0038): WS-Endpoint pusht JSON-Serialized
    Telemetry-Points aus dem `TelemetryStreamPort.subscribe()`-
    Stream; filtert nach `run_id`.
    """
    client, repository, stream, _ = configured_app
    metadata = _seed_run(repository)
    with client.websocket_connect(f"/runs/{metadata.run_id}/telemetry") as ws:
        # Publishe drei Points fuer den seeded Run + einen fuer einen
        # anderen Run (der vom Subscribe-Filter verworfen wird).
        stream.publish(_make_point(metadata.run_id, sequence=0))
        stream.publish(_make_point("other-run", sequence=99))
        stream.publish(_make_point(metadata.run_id, sequence=1))
        stream.publish(_make_point(metadata.run_id, sequence=2))
        msgs = [ws.receive_json() for _ in range(3)]
    assert [m["sequence"] for m in msgs] == [0, 1, 2]
    assert all(m["run_id"] == metadata.run_id for m in msgs)
    expected_fields = {
        "run_id",
        "device_id",
        "metric",
        "value",
        "unit",
        "simulation_time_ms",
        "quality",
        "sequence",
    }
    assert set(msgs[0].keys()) == expected_fields


def test_ws_telemetry_closes_with_1008_for_unknown_run(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """Welle-3 (ADR 0038): nicht-existenter Run → Close-Code 1008
    (Policy-Violation, analog 404-REST)."""
    client, _, _, _ = configured_app
    run_id = str(uuid.uuid4())
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect(f"/runs/{run_id}/telemetry") as ws,
    ):
        ws.receive_json()
    assert exc_info.value.code == 1008
