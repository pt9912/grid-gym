"""Tests fuer `routes.py` (M5 Welle 2, ADR 0036).

Drei Sub-Bereiche:

- ``GET /`` — Demo-Hello-Page, Full-Page-Pfad + HTMX-Partial-Pfad.
- ``GET /ui/health`` — Healthcheck-Page, Full-Page-Pfad + HTMX-
  Partial-Pfad.
- Static-Mount unter ``/static/*`` — vendored Assets sind
  abrufbar.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driving.http_api import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Frischer ``TestClient`` gegen die Welle-2-App."""
    with TestClient(app) as test_client:
        yield test_client


def test_get_demo_index_returns_full_page_with_base_layout(
    client: TestClient,
) -> None:
    """Browser-Default-Request rendert die volle Demo-Page inkl. Base-Layout."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "<!DOCTYPE html>" in body
    assert "grid-gym" in body
    assert "HTMX-Sanity-Probe" in body
    assert "/static/htmx.min.js" in body


def test_get_demo_index_with_htmx_request_returns_partial(
    client: TestClient,
) -> None:
    """HTMX-Sub-Request rendert nur den Demo-Content-Partial ohne Base-Layout."""
    response = client.get("/", headers={"HX-Request": "true"})
    assert response.status_code == 200
    body = response.text
    assert "<!DOCTYPE html>" not in body
    assert "HTMX-Sanity-Probe" in body


def test_get_ui_health_returns_full_page_with_status_ok(
    client: TestClient,
) -> None:
    """Healthcheck-Page rendert Status `ok` als Welle-2-Stub."""
    response = client.get("/ui/health")
    assert response.status_code == 200
    body = response.text
    assert "<!DOCTYPE html>" in body
    assert 'class="status-ok"' in body
    assert ">ok<" in body


def test_get_ui_health_with_htmx_request_returns_partial(
    client: TestClient,
) -> None:
    """HTMX-Sub-Request auf Healthcheck rendert nur den Content-Partial."""
    response = client.get("/ui/health", headers={"HX-Request": "true"})
    assert response.status_code == 200
    body = response.text
    assert "<!DOCTYPE html>" not in body
    assert 'class="status-ok"' in body


def test_static_mount_serves_vendored_htmx(client: TestClient) -> None:
    """Vendored HTMX 2.0.9 ist via `/static/htmx.min.js` abrufbar."""
    response = client.get("/static/htmx.min.js")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        ("application/javascript", "text/javascript")
    )
    assert len(response.content) > 40_000


def test_static_mount_serves_vendored_chartjs(client: TestClient) -> None:
    """Vendored Chart.js 4.5.1 ist via `/static/chart.umd.min.js` abrufbar."""
    response = client.get("/static/chart.umd.min.js")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        ("application/javascript", "text/javascript")
    )
    assert len(response.content) > 150_000


def test_static_mount_serves_stylesheet(client: TestClient) -> None:
    """CSS-Skeleton ist via `/static/style.css` abrufbar."""
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
