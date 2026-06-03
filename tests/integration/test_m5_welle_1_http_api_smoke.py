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
7. `WS /runs/{id}/telemetry` empfaengt subscribte Telemetry-
   Points (Welle 3 hat den Counter-Stub durch
   `TelemetryStreamPort.subscribe`-Pattern ersetzt).

Welle-1-Anti-Scope: alle REST-Calls sind Stubs; keine echte
TickLoop/FaultPort-Wiring (Welle 4/6). Der WS-Pfad ist seit
Welle 3 Subscribe-getrieben (ADR 0038); dieser Smoke
verifiziert nur die HTTP-Surface, das OpenAPI-Schema und
die Stub-Response-Shapes.
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
from decimal import Decimal

from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driving.telemetry_stream import TelemetryPoint
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
_VALID_FAULT_PAYLOAD: dict[str, object] = {
    "fault_type": "cell_failure",
    "target": "battery-1",
    "start_at_tick": 10,
    "duration_ticks": 20,
    "recovery": "auto-recover-after-N-ticks",
}


@pytest.fixture
def smoke_client() -> Iterator[
    tuple[TestClient, InMemoryTelemetryStream, InMemoryRunRepository, "TickLoopRegistry"]
]:
    """Frische App + InMemoryRunRepository + InMemoryTelemetryStream +
    TickLoopRegistry pro Test.

    Welle-3: WS-Endpoint braucht einen `TelemetryStreamPort`.
    Welle-4a: Status- und Control-Endpoints brauchen einen
    `TickLoopRegistry`; einzelne Tests registrieren ihre eigenen
    TickLoops fuer das Action-Routing.
    """
    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    stream = InMemoryTelemetryStream(queue_maxsize=8)
    configure_telemetry_stream(stream)
    registry = TickLoopRegistry()
    configure_tick_loop_registry(registry)
    with TestClient(app) as client:
        yield client, stream, repository, registry


def test_full_run_lifecycle_workflow(
    smoke_client: tuple[
        TestClient, InMemoryTelemetryStream, InMemoryRunRepository, TickLoopRegistry
    ],
) -> None:
    """End-to-End-Smoke: POST + 5 GET/POST + 1 WS in Sequence.

    Welle-1-Surface-Skeleton + Welle-3-WS-Subscribe + Welle-4a-
    Control-Wiring. Welle 4a wirt `POST /control` produktiv aus
    (`pause`/`resume`/`stop` rufen die TickLoop-Control-Surface);
    der Test registriert einen TickLoop fuer den erstellten Run,
    damit das Action-Routing den 503-Pfad vermeidet.
    """
    client, stream, repository, registry = smoke_client
    # 1. POST /runs → 201 + run_id
    create_response = client.post("/runs", json=_VALID_RUN_PAYLOAD)
    assert create_response.status_code == 201
    run_id = create_response.json()["run_id"]
    uuid.UUID(run_id)  # validate UUID format

    # Welle-4a: TickLoop fuer den frischen Run registrieren, damit
    # die Control- und Status-Endpoints (Schritte 3+4) produktiv
    # routen koennen.
    # Welle-6a (Decision 20): Cross-Field-Validation im POST-/faults-
    # Handler braucht ein Device im TickLoop, dessen Typ zum
    # Fault-Typ (`cell_failure` ↔ Battery) passt. Welle-1-Stub-
    # Verhalten war devices-frei — Welle-6a verschaerft den Vertrag.
    battery = BatteryDevice()
    battery.initialize(
        ScenarioDevice(
            id="battery-1",
            type="battery",
            params={
                "capacity_kwh": Decimal("100"),
                "initial_soc_pct": Decimal("50"),
                "min_soc_pct": Decimal("0"),
                "max_soc_pct": Decimal("100"),
                "max_charge_kw": Decimal("50"),
                "max_discharge_kw": Decimal("50"),
                "charge_efficiency": Decimal("1"),
                "discharge_efficiency": Decimal("1"),
                "ramp_kw_per_s": Decimal("100"),
            },
        ),
        FixedSeedRandom(seed=0),
    )
    tick_loop = TickLoop(
        run_id=run_id,
        tick_ms=100,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=(battery,),
        run_repository=repository,
    )
    registry.register(tick_loop)

    # 2. GET /runs/{id} → Full Metadata
    detail_response = client.get(f"/runs/{run_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["run_id"] == run_id
    assert detail["scenario_hash"] == _VALID_SCENARIO_HASH
    assert detail["seed"] == 42
    assert detail["tick_ms"] == 100

    # 3. GET /runs/{id}/status → Welle-4a-Wiring zeigt `pending` +
    #    Counter aus dem frisch registrierten TickLoop (noch 0).
    status_response = client.get(f"/runs/{run_id}/status")
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["state"] == "pending"
    assert status["simulation_time"] == 0
    assert status["tick_count"] == 0

    # 4. POST /runs/{id}/control mit `pause` → Welle-4a-Wiring auf
    #    TickLoop.request_pause(); Repository persistiert `paused`.
    control_response = client.post(
        f"/runs/{run_id}/control",
        json={"action": "pause"},
    )
    assert control_response.status_code == 200
    assert control_response.json()["accepted"] is True
    assert repository.get_status(run_id) == "paused"

    # 5. POST /runs/{id}/faults → 201 + fault_id
    faults_response = client.post(
        f"/runs/{run_id}/faults",
        json=_VALID_FAULT_PAYLOAD,
    )
    assert faults_response.status_code == 201
    fault_body = faults_response.json()
    assert fault_body["accepted"] is True
    uuid.UUID(fault_body["fault_id"])

    # 6. GET /runs/{id}/snapshot → schema_ref
    snapshot_response = client.get(f"/runs/{run_id}/snapshot")
    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["schema_ref"] == "grid-gym.snapshot.envelope.v2"

    # 7. WS /runs/{id}/telemetry → 3 Subscribed Points (Welle 3, ADR 0038)
    with client.websocket_connect(f"/runs/{run_id}/telemetry") as ws:
        for sequence in range(3):
            stream.publish(
                TelemetryPoint(
                    run_id=run_id,
                    device_id="battery-1",
                    metric="power",
                    value=float(sequence),
                    unit="kW",
                    simulation_time_ms=sequence * 100,
                    quality="ok",
                    sequence=sequence,
                )
            )
        messages = [ws.receive_json() for _ in range(3)]
    assert [m["sequence"] for m in messages] == [0, 1, 2]
    assert all(m["run_id"] == run_id for m in messages)


def test_openapi_schema_contains_welle_1_endpoints(
    smoke_client: tuple[
        TestClient, InMemoryTelemetryStream, InMemoryRunRepository, TickLoopRegistry
    ],
) -> None:
    """Welle-1-Endpunkte muessen im OpenAPI-Schema auftauchen
    (`GG-API-003`); `make openapi-validate` prueft das Schema
    gegen den OpenAPI-Spec-Validator."""
    client, _, _, _ = smoke_client
    response = client.get("/openapi.json")
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
