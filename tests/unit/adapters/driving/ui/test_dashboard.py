"""Tests fuer die Dashboard-UI-Page (M5 Welle 3, ADR 0038).

Prueft die Welle-3-`GET /runs/{run_id}/dashboard`-Route:

- Full-Page-Rendering mit Run-ID + Asset-Tags + WS-Bridge.
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
from grid_gym.adapters.driving.http_api.app import (
    configure_run_repository,
    configure_telemetry_stream,
)
from grid_gym.hexagon.core.domain.run import RunMetadata
from tests.unit.hexagon.ports.driven._fakes import InMemoryRunRepository


@pytest.fixture
def configured_app() -> Iterator[tuple[TestClient, InMemoryRunRepository]]:
    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    configure_telemetry_stream(InMemoryTelemetryStream())
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


def test_dashboard_full_page_rendered_with_run_id(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Full-Page-Request liefert Base-Layout + Run-ID + WS-Bridge."""
    client, repository = configured_app
    metadata = _seed_run(repository)
    response = client.get(f"/runs/{metadata.run_id}/dashboard")
    assert response.status_code == 200
    body = response.text
    assert "<!DOCTYPE html>" in body
    assert metadata.run_id in body
    assert f'ws-connect="/runs/{metadata.run_id}/telemetry"' in body
    assert 'hx-ext="ws"' in body
    assert "telemetry-chart" in body
    assert "/static/chart.umd.min.js" in body


def test_dashboard_htmx_partial_rendered_without_base_layout(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """HTMX-Sub-Request liefert nur den Content-Partial."""
    client, repository = configured_app
    metadata = _seed_run(repository)
    response = client.get(
        f"/runs/{metadata.run_id}/dashboard",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    body = response.text
    assert "<!DOCTYPE html>" not in body
    assert metadata.run_id in body
    assert 'hx-ext="ws"' in body


def test_dashboard_returns_404_for_unknown_run(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Nicht-existenter Run → 404."""
    client, _ = configured_app
    response = client.get(f"/runs/{uuid.uuid4()}/dashboard")
    assert response.status_code == 404
