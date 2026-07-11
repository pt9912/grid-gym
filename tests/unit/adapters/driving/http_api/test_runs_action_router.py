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

from grid_gym.adapters.driven.alarm_stream_inmemory import (
    AlarmHistoryBuffer,
    InMemoryAlarmStream,
)
from grid_gym.adapters.driven.telemetry_stream_inmemory import (
    InMemoryTelemetryStream,
)
from grid_gym.adapters.driving.http_api import app
from grid_gym.adapters.driving.http_api._alarm_setup import configure_alarm_stream
from grid_gym.adapters.driving.http_api._tick_loop_registry import TickLoopRegistry
from grid_gym.adapters.driving.http_api.app import (
    configure_run_repository,
    configure_telemetry_stream,
    configure_tick_loop_registry,
)
from decimal import Decimal

from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.domain.alarm import Alarm
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
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
    configure_alarm_stream(InMemoryAlarmStream(queue_maxsize=16), AlarmHistoryBuffer())
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


def _seed_run_with_tick_loop_and_devices(
    repository: InMemoryRunRepository,
    registry: TickLoopRegistry,
) -> tuple[RunMetadata, TickLoop]:
    """Welle-6a-Helper: wie `_seed_run_with_tick_loop`, aber mit
    einer Battery + GridConnection im TickLoop. Welle-6a-Decision-20
    Cross-Field-Validation braucht `tick_loop.device_types`-
    Mapping (Battery → cell_failure / GridConnection →
    voltage_drop)."""
    metadata = _seed_run(repository)
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
    grid = GridConnectionDevice()
    grid.initialize(
        ScenarioDevice(
            id="grid-1",
            type="grid_connection",
            params={
                "nominal_voltage_v": Decimal("400"),
                "max_import_kw": Decimal("100"),
                "max_export_kw": Decimal("100"),
            },
        ),
        FixedSeedRandom(seed=0),
    )
    tick_loop = TickLoop(
        run_id=metadata.run_id,
        tick_ms=metadata.tick_ms,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=metadata.seed),
        scheduler=Scheduler(),
        devices=(battery, grid),
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
    """Welle-6a Decision 19 + 20: 201 + UUID-Fault-ID + accepted=True
    bei Battery+cell_failure (Welle-1-Stub-Antwort bleibt; Cross-
    Field-Validation hat den Target gegen den TickLoop geprueft)."""
    client, repository, _, registry = configured_app
    metadata, _ = _seed_run_with_tick_loop_and_devices(repository, registry)
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


def test_post_run_faults_accepts_metric_addressed_nan_injection_on_any_device(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """ADR 0074 §2.1/§2.7 (Slice 071): `nan_injection` ist
    metrik-adressiert — das Ziel darf jedes existierende Geraet sein
    (hier Battery). Der device-Physik-Typ-Match wird uebersprungen; die
    Target-Existenz reicht → 201 accepted (kein
    `fault_invalid_type_for_target`/`fault_type_unknown`-Reject)."""
    client, repository, _, registry = configured_app
    metadata, _ = _seed_run_with_tick_loop_and_devices(repository, registry)
    response = client.post(
        f"/runs/{metadata.run_id}/faults",
        json={
            "fault_type": "nan_injection",
            "target": "battery-1",
            "start_at_tick": 10,
            "duration_ticks": 20,
            "recovery": "auto-recover-after-N-ticks",
        },
    )
    assert response.status_code == 201
    assert response.json()["accepted"] is True


def test_post_run_faults_rejects_metric_addressed_fault_on_unknown_target(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """ADR 0074 §2.7: die Target-Existenz bleibt auch fuer den
    metrik-adressierten Fault der einzige harte Cross-Field-Check →
    unbekanntes Ziel weiterhin 422 `fault_unknown_target`."""
    client, repository, _, registry = configured_app
    metadata, _ = _seed_run_with_tick_loop_and_devices(repository, registry)
    response = client.post(
        f"/runs/{metadata.run_id}/faults",
        json={
            "fault_type": "nan_injection",
            "target": "ghost-99",
            "start_at_tick": 10,
            "duration_ticks": 20,
            "recovery": "auto-recover-after-N-ticks",
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "fault_unknown_target"


def test_post_run_faults_rejects_invalid_body(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """Pydantic-Validation: Missing-Field → 422."""
    client, repository, _, registry = configured_app
    metadata, _ = _seed_run_with_tick_loop_and_devices(repository, registry)
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


# ---------------------------------------------------------------------------
# WS /runs/{run_id}/alarms-stream (M5 Welle 4b, ADR 0040 Decision 17)
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


def test_ws_alarms_stream_pushes_subscribed_alarms(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """Welle-4b (ADR 0040 Decision 17): WS pusht JSON-Serialized
    Alarms aus dem AlarmStreamPort; filtert nach run_id."""
    client, repository, _, _ = configured_app
    metadata = _seed_run(repository)
    alarm_stream = app.state.alarm_stream
    with client.websocket_connect(f"/runs/{metadata.run_id}/alarms-stream") as ws:
        alarm_stream.publish(_make_alarm(metadata.run_id, alarm_id="a-0"))
        alarm_stream.publish(_make_alarm("other-run", alarm_id="a-99"))
        alarm_stream.publish(_make_alarm(metadata.run_id, alarm_id="a-1"))
        msgs = [ws.receive_json() for _ in range(2)]
    assert [m["alarm_id"] for m in msgs] == ["a-0", "a-1"]
    assert all(m["run_id"] == metadata.run_id for m in msgs)


def test_ws_alarms_stream_closes_with_1008_for_unknown_run(
    configured_app: tuple[
        TestClient, InMemoryRunRepository, InMemoryTelemetryStream, TickLoopRegistry
    ],
) -> None:
    """Welle-4b: nicht-existenter Run → Close-Code 1008
    (Policy-Violation; Pattern aus Welle 3)."""
    client, _, _, _ = configured_app
    run_id = str(uuid.uuid4())
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect(f"/runs/{run_id}/alarms-stream") as ws,
    ):
        ws.receive_json()
    assert exc_info.value.code == 1008
