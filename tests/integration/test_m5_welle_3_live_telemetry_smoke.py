"""M5-Welle-3-Live-Telemetry-Smoke-Integration-Test (ADR 0038).

End-to-End-Smoke der Welle-3-UI-Foundation:

1. Dashboard-Page laden (`GET /runs/{run_id}/dashboard`).
2. WebSocket subscribt auf `/runs/{run_id}/telemetry`.
3. Demo-Generator publisht Points → WS empfaengt JSON-
   serialisierte Telemetry-Points mit `run_id`-Filter.

Welle-3-Akzeptanz: alle 4 Lastenheft-IDs (`GG-API-002`,
`GG-UI-002`, `GG-UI-003`, `GG-UI-009`) sind durch diesen
Test belegbar.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driven.telemetry_stream_inmemory import (
    InMemoryTelemetryStream,
)
from grid_gym.adapters.driving.http_api import app
from grid_gym.adapters.driving.http_api.app import (
    configure_run_repository,
    configure_telemetry_stream,
)
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.ports.driving.telemetry_stream import TelemetryPoint
from tests.unit.hexagon.ports.driven._fakes import InMemoryRunRepository


_RUN_ID = "smoke-run-0001"


@pytest.fixture
def smoke_client() -> Iterator[tuple[TestClient, InMemoryTelemetryStream]]:
    repository = InMemoryRunRepository()
    repository.save(
        RunMetadata(
            run_id=_RUN_ID,
            scenario_hash="0" * 64,
            schema_version="grid-gym.scenario.v1",
            seed=42,
            tick_ms=100,
            started_at="",
            ended_at="",
            tool_version="0.1.0",
        )
    )
    configure_run_repository(repository)
    stream = InMemoryTelemetryStream(queue_maxsize=16)
    configure_telemetry_stream(stream)
    with TestClient(app) as client:
        yield client, stream


def test_dashboard_page_plus_ws_subscribe_end_to_end(
    smoke_client: tuple[TestClient, InMemoryTelemetryStream],
) -> None:
    """End-to-End: Dashboard-HTML + WS-Telemetry-Receive."""
    client, stream = smoke_client

    # 1. Dashboard-Page liefert HTML mit WS-Bridge.
    page = client.get(f"/runs/{_RUN_ID}/dashboard")
    assert page.status_code == 200
    page_body = page.text
    assert "<!DOCTYPE html>" in page_body
    assert _RUN_ID in page_body
    assert f'ws-connect="/runs/{_RUN_ID}/telemetry"' in page_body
    assert "/static/chart.umd.min.js" in page_body

    # 2. WebSocket-Connect + Publish + Receive.
    with client.websocket_connect(f"/runs/{_RUN_ID}/telemetry") as ws:
        for sequence in range(3):
            stream.publish(
                TelemetryPoint(
                    run_id=_RUN_ID,
                    device_id="battery-1",
                    metric="power",
                    value=float(sequence * 10),
                    unit="kW",
                    simulation_time_ms=sequence * 100,
                    quality="ok" if sequence < 2 else "stale",
                    sequence=sequence,
                )
            )
        messages = [ws.receive_json() for _ in range(3)]
    assert [m["sequence"] for m in messages] == [0, 1, 2]
    assert messages[-1]["quality"] == "stale"
    # Felder decken GG-API-002 + GG-UI-002 + GG-UI-009 ab.
    expected = {
        "run_id",
        "device_id",
        "metric",
        "value",
        "unit",
        "simulation_time_ms",
        "quality",
        "sequence",
    }
    assert set(messages[0].keys()) == expected


def test_dashboard_route_appears_in_openapi_under_ui_tag(
    smoke_client: tuple[TestClient, InMemoryTelemetryStream],
) -> None:
    """Welle-3-Route ist im OpenAPI-Schema mit `tags=["ui"]`."""
    client, _ = smoke_client
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    paths = spec["paths"]
    assert "/runs/{run_id}/dashboard" in paths
    assert paths["/runs/{run_id}/dashboard"]["get"]["tags"] == ["ui"]
