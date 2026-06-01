"""M5-Welle-1-HTTP-API-Smoke-Integration-Test (ADR 0037).

End-to-End-Smoke der Welle-1-HTTP-API-Surface gegen den
echten `app`-Mount + `InMemoryRunRepository`-Backend. Im
Gegensatz zu den Unit-Tests in `tests/unit/adapters/driving/
http_api/test_runs_*.py` (die einzelne Endpunkte pruefen)
deckt dieser Test einen kompletten Workflow ab:

1. `POST /runs` legt einen neuen Lauf an.
2. `GET /runs/{id}` liefert die Metadaten.
3. `GET /runs/{id}/status` liefert den (Stub-)Status.
4. `POST /runs/{id}/control` mit `{"action": "pause"}` wird
   akzeptiert.
5. `POST /runs/{id}/faults` legt einen (Stub-)Fault an.
6. `GET /runs/{id}/snapshot` liefert den Schema-Ref.
7. `WS /runs/{id}/telemetry` pusht 3 Counter-Updates.

Welle-1-Anti-Scope: alle Calls sind Stubs; keine echte
TickLoop/FaultPort/TelemetrySink-Wiring (Welle 3/4/6).
Dieser Smoke validiert nur die HTTP-Surface, das
OpenAPI-Schema und die Stub-Response-Shapes.
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
_VALID_RUN_PAYLOAD: dict[str, object] = {
    "scenario_hash": _VALID_SCENARIO_HASH,
    "seed": 42,
    "tick_ms": 100,
}
_VALID_FAULT_PAYLOAD: dict[str, object] = {
    "fault_type": "cell_failure",
    "target": "battery-1",
    "start_at_tick": 10,
    "duration_ticks": 20,
    "recovery": "auto-recover-after-N-ticks",
}


@pytest.fixture
def smoke_client() -> Iterator[TestClient]:
    """Frische App + InMemoryRunRepository pro Test."""
    configure_run_repository(InMemoryRunRepository())
    with TestClient(app) as client:
        yield client


def test_full_run_lifecycle_workflow(smoke_client: TestClient) -> None:
    """End-to-End-Smoke: POST + 5 GET/POST + 1 WS in Sequence.

    Welle-1-Stub: jeder Schritt validiert die Surface-Shape,
    nicht das tatsaechliche Verhalten. Welle 3/4/6 ersetzen
    die Stubs durch echte TickLoop/FaultPort/TelemetrySink-
    Wiring.
    """
    # 1. POST /runs → 201 + run_id
    create_response = smoke_client.post("/runs", json=_VALID_RUN_PAYLOAD)
    assert create_response.status_code == 201
    run_id = create_response.json()["run_id"]
    uuid.UUID(run_id)  # validate UUID format

    # 2. GET /runs/{id} → Full Metadata
    detail_response = smoke_client.get(f"/runs/{run_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["run_id"] == run_id
    assert detail["scenario_hash"] == _VALID_SCENARIO_HASH
    assert detail["seed"] == 42
    assert detail["tick_ms"] == 100

    # 3. GET /runs/{id}/status → Stub-Status
    status_response = smoke_client.get(f"/runs/{run_id}/status")
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["state"] == "pending"
    assert status["simulation_time"] == 0
    assert status["tick_count"] == 0

    # 4. POST /runs/{id}/control mit `pause` → accepted=True
    control_response = smoke_client.post(
        f"/runs/{run_id}/control",
        json={"action": "pause"},
    )
    assert control_response.status_code == 200
    assert control_response.json()["accepted"] is True

    # 5. POST /runs/{id}/faults → 201 + fault_id
    faults_response = smoke_client.post(
        f"/runs/{run_id}/faults",
        json=_VALID_FAULT_PAYLOAD,
    )
    assert faults_response.status_code == 201
    fault_body = faults_response.json()
    assert fault_body["accepted"] is True
    uuid.UUID(fault_body["fault_id"])

    # 6. GET /runs/{id}/snapshot → schema_ref
    snapshot_response = smoke_client.get(f"/runs/{run_id}/snapshot")
    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["schema_ref"] == "grid-gym.snapshot.envelope.v2"

    # 7. WS /runs/{id}/telemetry → 3 Counter-Pushes
    with smoke_client.websocket_connect(f"/runs/{run_id}/telemetry") as ws:
        messages = [ws.receive_json() for _ in range(3)]
    assert [m["tick"] for m in messages] == [0, 1, 2]
    assert all(m["run_id"] == run_id for m in messages)


def test_openapi_schema_contains_welle_1_endpoints(
    smoke_client: TestClient,
) -> None:
    """Welle-1-Endpunkte muessen im OpenAPI-Schema auftauchen
    (`GG-API-003`); `make openapi-validate` prueft das Schema
    gegen den OpenAPI-Spec-Validator."""
    response = smoke_client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    paths = spec["paths"]

    # M1-Welle-7 Endpunkte
    assert "/health" in paths
    assert "/runs" in paths

    # M5-Welle-1 REST Endpunkte
    assert "/runs/{run_id}" in paths
    assert "/runs/{run_id}/status" in paths
    assert "/runs/{run_id}/control" in paths
    assert "/runs/{run_id}/snapshot" in paths
    assert "/runs/{run_id}/faults" in paths

    # Action-Body-Schema (ADR 0037 Decision API-1)
    control_post = paths["/runs/{run_id}/control"]["post"]
    schemas = spec["components"]["schemas"]
    control_request_schema = schemas["ControlRequest"]
    # Pydantic v2 serialisiert Literal als enum
    assert "enum" in control_request_schema["properties"]["action"]
    assert set(control_request_schema["properties"]["action"]["enum"]) == {
        "pause",
        "resume",
        "stop",
    }

    # WebSocket-Endpunkte sind **nicht** im OpenAPI (OpenAPI-3.x-
    # Standard; siehe ADR 0037 §3-Klarstellung).
    assert "/runs/{run_id}/telemetry" not in paths
