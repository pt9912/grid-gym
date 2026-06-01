"""Page-Routes fuer das UI-Driving-Adapter (M5 Welle 2, ADR 0036).

Welle-2-Scope: zwei Page-Routes als UI-Foundation-Skeleton:

- ``GET /`` — Demo-Hello-Page mit HTMX-Sanity-Probe.
- ``GET /ui/health`` — Healthcheck-UI-Seite; rendert ``/health``-
  JSON via HTMX-Partial-Refresh (Welle-1-Endpoint).

Beide Routes erkennen den ``HX-Request``-Header und rendern
bei HTMX-Sub-Requests nur den Content-Block (Partial) statt
des vollen Base-Layouts.

Welle-3-Folge: ``/runs/{id}/dashboard``-Page mit Live-
Telemetry. Welle 4 ergaenzt Replay-Controls; Welle 5 den
Scenario-Editor. Diese Routes folgen demselben APIRouter-
Pattern wie hier.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from grid_gym.adapters.driving.ui._templates import get_templates

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
