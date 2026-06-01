"""Tests fuer `_runs_action_router.py` (M5 Welle 1, ADR 0037).

Drei Endpunkte:

- `POST /runs/{run_id}/control` — Run-Steuerung mit Action-Body
  (`pause`/`resume`/`stop`; ADR 0037 Decision API-1).
- `POST /runs/{run_id}/faults` — Fault-Injection-Submit
  (Welle-1-Stub).
- `WS /runs/{run_id}/telemetry` — Live-Telemetry-Stream
  (Welle-1-Skeleton mit Counter-Push).

Plus 404-Pfade fuer REST und Close-Code 1008 fuer WebSocket
bei nicht-existenten Runs.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

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
# POST /runs/{run_id}/control
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("action", ["pause", "resume", "stop"])
def test_post_run_control_accepts_valid_action(
    configured_app: tuple[TestClient, InMemoryRunRepository],
    action: str,
) -> None:
    """Welle-1-Stub: jede der drei Actions wird mit
    `accepted=True` quittiert (ADR 0037 Decision API-1)."""
    client, repository = configured_app
    metadata = _seed_run(repository)
    response = client.post(
        f"/runs/{metadata.run_id}/control",
        json={"action": action},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == metadata.run_id
    assert body["action"] == action
    assert body["accepted"] is True


def test_post_run_control_rejects_invalid_action(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Pydantic-Literal-Validation fuer ungueltige Actions → 422."""
    client, repository = configured_app
    metadata = _seed_run(repository)
    response = client.post(
        f"/runs/{metadata.run_id}/control",
        json={"action": "restart"},
    )
    assert response.status_code == 422


def test_post_run_control_returns_404_for_unknown_run(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    client, _ = configured_app
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
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Welle-1-Stub: 201 + UUID-Fault-ID + accepted=True."""
    client, repository = configured_app
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
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Pydantic-Validation: Missing-Field → 422."""
    client, repository = configured_app
    metadata = _seed_run(repository)
    response = client.post(
        f"/runs/{metadata.run_id}/faults",
        json={"fault_type": "cell_failure"},  # missing other fields
    )
    assert response.status_code == 422


def test_post_run_faults_returns_404_for_unknown_run(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    client, _ = configured_app
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


def test_ws_telemetry_pushes_three_counter_messages(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Welle-1-Skeleton: Server pusht 3 Counter-Updates + close."""
    client, repository = configured_app
    metadata = _seed_run(repository)
    with client.websocket_connect(f"/runs/{metadata.run_id}/telemetry") as ws:
        msg0 = ws.receive_json()
        msg1 = ws.receive_json()
        msg2 = ws.receive_json()
    assert msg0 == {"run_id": metadata.run_id, "tick": 0, "value": 0}
    assert msg1 == {"run_id": metadata.run_id, "tick": 1, "value": 10}
    assert msg2 == {"run_id": metadata.run_id, "tick": 2, "value": 20}


def test_ws_telemetry_closes_with_1008_for_unknown_run(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Welle-1-Skeleton: nicht-existenter Run → Close-Code 1008
    (Policy-Violation, analog 404-REST)."""
    client, _ = configured_app
    run_id = str(uuid.uuid4())
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect(f"/runs/{run_id}/telemetry") as ws,
    ):
        ws.receive_json()
    assert exc_info.value.code == 1008
