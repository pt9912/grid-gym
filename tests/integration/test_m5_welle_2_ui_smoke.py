"""M5-Welle-2-UI-Smoke-Integration-Test (ADR 0036).

End-to-End-Smoke der Welle-2-UI-Foundation gegen den
echten `app`-Mount inkl. StaticFiles-Mount + ui_router.
Im Gegensatz zu den Unit-Tests in
`tests/unit/adapters/driving/ui/test_routes.py` (die
einzelne Routes pruefen) deckt dieser Smoke einen
sichtbaren Workflow ab:

1. Browser laedt `/` (Demo-Hello-Page).
2. Statisches HTMX-JS-Asset ist erreichbar.
3. Statisches Chart.js-Asset ist erreichbar.
4. HTMX-Probe-Klick triggert `/ui/health` (HX-Request)
   und liefert nur den Partial-Body.

Welle-2-Anti-Scope: kein Live-Telemetry, kein Replay-
Control, kein Chart.js-Use — die UI ist Foundation-
Skeleton, das Welle 3/4 verlaengern.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driving.http_api import app


@pytest.fixture
def smoke_client() -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client


def test_full_ui_foundation_workflow(smoke_client: TestClient) -> None:
    """End-to-End-Smoke: Demo-Page + 2 Static-Assets + HTMX-Probe."""
    # 1. Demo-Page liefert volle HTML-Response mit Asset-Tags.
    index_response = smoke_client.get("/")
    assert index_response.status_code == 200
    index_body = index_response.text
    assert "<!DOCTYPE html>" in index_body
    assert "/static/htmx.min.js" in index_body
    assert "/static/chart.umd.min.js" in index_body
    assert "/static/style.css" in index_body

    # 2. HTMX-JS-Asset ist abrufbar mit reasonably-grossem Body.
    htmx_response = smoke_client.get("/static/htmx.min.js")
    assert htmx_response.status_code == 200
    assert len(htmx_response.content) > 40_000

    # 3. Chart.js-Asset ist abrufbar (Welle 2 vendored, Welle 3 nutzt es).
    chartjs_response = smoke_client.get("/static/chart.umd.min.js")
    assert chartjs_response.status_code == 200
    assert len(chartjs_response.content) > 150_000

    # 4. HTMX-Probe gegen `/ui/health` → Partial ohne Base-Layout.
    probe_response = smoke_client.get(
        "/ui/health",
        headers={"HX-Request": "true"},
    )
    assert probe_response.status_code == 200
    probe_body = probe_response.text
    assert "<!DOCTYPE html>" not in probe_body
    assert 'class="status-ok"' in probe_body


def test_ui_routes_appear_in_openapi_schema_under_ui_tag(
    smoke_client: TestClient,
) -> None:
    """UI-Routes (`GET /`, `GET /ui/health`) sind im OpenAPI-Schema
    mit `tags=["ui"]` markiert.

    Welle-2-Begruendung: das Schema deckt alle HTTP-Endpunkte ab
    (`GG-API-003`), und der `ui`-Tag erlaubt UI-Routes optisch
    von Run-Routes zu trennen.
    """
    response = smoke_client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    paths = spec["paths"]

    # UI-Routes sichtbar.
    assert "/" in paths
    assert "/ui/health" in paths

    # Beide Routes tragen den `ui`-Tag.
    assert paths["/"]["get"]["tags"] == ["ui"]
    assert paths["/ui/health"]["get"]["tags"] == ["ui"]

    # Welle-1-Endpunkte bleiben sichtbar (Regressionscheck).
    assert "/health" in paths
    assert "/runs" in paths
    assert "/runs/{run_id}" in paths
