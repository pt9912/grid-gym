"""Page-Routes fuer das UI-Driving-Adapter (M5 Welle 2/3, ADR 0036 + 0038).

Welle-2-Scope: zwei Page-Routes als UI-Foundation-Skeleton:

- ``GET /`` — Demo-Hello-Page mit HTMX-Sanity-Probe.
- ``GET /ui/health`` — Healthcheck-UI-Seite; rendert ``/health``-
  JSON via HTMX-Partial-Refresh (Welle-1-Endpoint).

Welle-3-Erweiterung:

- ``GET /runs/{run_id}/dashboard`` — Live-Telemetry-Dashboard
  mit HTMX-`hx-ext="ws"`-Subscribe + Chart.js-Time-Series
  + Quality-Marker-Visualisierung (`GG-UI-002/003/009`).

Alle Routes erkennen den ``HX-Request``-Header und rendern
bei HTMX-Sub-Requests nur den Content-Block (Partial) statt
des vollen Base-Layouts.

Welle 4 ergaenzt Replay-Controls; Welle 5 den Scenario-
Editor. Diese Routes folgen demselben APIRouter-Pattern.
"""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from grid_gym.adapters.driving.http_api._dependencies import get_run_repository
from grid_gym.adapters.driving.ui._templates import get_templates
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort

ui_router: APIRouter = APIRouter(tags=["ui"])


def _is_htmx_request(request: Request) -> bool:
    """``True`` wenn HTMX den Request als Sub-Request markiert hat."""
    return request.headers.get("hx-request", "").lower() == "true"


@ui_router.get("/", response_class=HTMLResponse)
def get_demo_index(request: Request) -> HTMLResponse:
    """Demo-Hello-Page mit HTMX-Sanity-Probe (Welle-2-Foundation)."""
    templates = get_templates()
    template_name = "demo.html" if not _is_htmx_request(request) else "_demo_content.html"
    return templates.TemplateResponse(request, template_name)


@ui_router.get("/ui/health", response_class=HTMLResponse)
def get_ui_health(request: Request) -> HTMLResponse:
    """Healthcheck-UI-Seite (rendert Welle-1-`/health`-Status).

    Welle-2-Stub: Status-Wert ist statisch ``"ok"`` (analog
    Welle-1-`HealthResponse`). Welle 3 ergaenzt einen echten
    Backend-Roundtrip falls noetig.
    """
    templates = get_templates()
    template_name = "health.html" if not _is_htmx_request(request) else "_health_content.html"
    return templates.TemplateResponse(request, template_name, {"status": "ok"})


@ui_router.get("/runs/{run_id}/dashboard", response_class=HTMLResponse)
def get_run_dashboard(
    run_id: str,
    request: Request,
    repository: Annotated[RunRepositoryPort, Depends(get_run_repository)],
) -> HTMLResponse:
    """Live-Telemetry-Dashboard-Page (M5 Welle 3, ADR 0038).

    Rendert eine Page mit HTMX-WS-Subscribe an
    ``/runs/{run_id}/telemetry`` + Chart.js-Time-Series-
    Visualisierung. Bei nicht-existentem Run liefert die
    Route 404 (analog `GG-API-004`-Pattern aus
    HTTP-API-Surface).
    """
    if not repository.exists(run_id):
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    templates = get_templates()
    template_name = "dashboard.html" if not _is_htmx_request(request) else "_dashboard_content.html"
    return cast(
        HTMLResponse,
        templates.TemplateResponse(request, template_name, {"run_id": run_id}),
    )
