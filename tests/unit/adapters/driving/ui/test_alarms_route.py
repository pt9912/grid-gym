"""Tests fuer die Alarms-UI-Page (M5 Welle 4b, ADR 0040 Decision 17).

Prueft die Welle-4b-`GET /runs/{run_id}/alarms`-Route:

- Full-Page-Rendering mit Run-ID + HTMX-Hydration-Target +
  WS-Bridge.
- HTMX-Partial-Rendering bei `HX-Request: true`.
- 404 fuer nicht-existenten Run.
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
from grid_gym.hexagon.core.domain.run import RunMetadata
from tests.unit.hexagon.ports.driven._fakes import InMemoryRunRepository


@pytest.fixture
def configured_app() -> Iterator[tuple[TestClient, InMemoryRunRepository]]:
    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    configure_telemetry_stream(InMemoryTelemetryStream())
    configure_tick_loop_registry(TickLoopRegistry())
    configure_alarm_stream(InMemoryAlarmStream(), AlarmHistoryBuffer())
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


def test_get_run_alarms_renders_full_page_with_table_and_ws_bridge(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Welle-4b (ADR 0040 Decision 17): Full-Page-Rendering enthaelt
    die 6-Spalten-Tabelle + HTMX-Hydration-Target + WS-Bridge."""
    client, repository = configured_app
    metadata = _seed_run(repository)
    response = client.get(f"/runs/{metadata.run_id}/alarms")
    assert response.status_code == 200
    html = response.text
    assert metadata.run_id in html
    # 6 Pflicht-Spalten per GG-UI-005.
    for column in ["Zeit", "Ziel", "Schweregrad", "Code", "Nachricht", "Status"]:
        assert column in html
    # HTMX-Hydration-Target via hx-get.
    assert 'hx-get="/runs/' in html
    # WS-Bridge fuer Live-Updates.
    assert 'ws-connect="/runs/' in html
    assert "<!DOCTYPE html>" in html


def test_get_run_alarms_renders_partial_for_htmx_request(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Welle-4b: `HX-Request: true` liefert nur den Content-Block."""
    client, repository = configured_app
    metadata = _seed_run(repository)
    response = client.get(
        f"/runs/{metadata.run_id}/alarms",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    html = response.text
    assert metadata.run_id in html
    assert "<!DOCTYPE html>" not in html
    assert 'class="alarms"' in html


def test_get_run_alarms_returns_404_for_unknown_run(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    client, _ = configured_app
    run_id = str(uuid.uuid4())
    response = client.get(f"/runs/{run_id}/alarms")
    assert response.status_code == 404
