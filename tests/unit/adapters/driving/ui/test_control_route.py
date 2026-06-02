"""Tests fuer die Replay-Controls-UI-Page (M5 Welle 4a, ADR 0039
Decision 14).

Prueft die Welle-4a-`GET /runs/{run_id}/control`-Route:

- Full-Page-Rendering mit Run-ID + HTMX-Buttons + Status-Polling-
  Block.
- HTMX-Partial-Rendering bei `HX-Request: true`.
- 404 fuer nicht-existenten Run.
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
from grid_gym.hexagon.core.domain.run import RunMetadata
from tests.unit.hexagon.ports.driven._fakes import InMemoryRunRepository


@pytest.fixture
def configured_app() -> Iterator[tuple[TestClient, InMemoryRunRepository]]:
    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    configure_telemetry_stream(InMemoryTelemetryStream())
    configure_tick_loop_registry(TickLoopRegistry())
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


def test_get_run_control_renders_full_page_with_buttons(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Welle-4a (ADR 0039 Decision 14): Full-Page-Rendering enthaelt
    die 3 HTMX-POST-Buttons + Status-Polling-Block."""
    client, repository = configured_app
    metadata = _seed_run(repository)
    response = client.get(f"/runs/{metadata.run_id}/control")
    assert response.status_code == 200
    html = response.text
    assert metadata.run_id in html
    assert 'hx-post="/runs/' in html
    assert '"action": "pause"' in html
    assert '"action": "resume"' in html
    assert '"action": "stop"' in html
    assert 'hx-trigger="every 1s"' in html
    assert "<!DOCTYPE html>" in html  # full layout, not partial


def test_get_run_control_renders_partial_for_htmx_request(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Welle-4a: `HX-Request: true` liefert nur den Content-Block,
    nicht das Base-Layout."""
    client, repository = configured_app
    metadata = _seed_run(repository)
    response = client.get(
        f"/runs/{metadata.run_id}/control",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    html = response.text
    assert metadata.run_id in html
    assert "<!DOCTYPE html>" not in html  # kein full layout
    assert 'class="control"' in html


def test_get_run_control_returns_404_for_unknown_run(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    client, _ = configured_app
    run_id = str(uuid.uuid4())
    response = client.get(f"/runs/{run_id}/control")
    assert response.status_code == 404
