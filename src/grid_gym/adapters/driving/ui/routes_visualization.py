"""Welle-6b-UI-Visualization-Routes (M5 Welle 6b, Decisions 21/22).

Schwester-Modul zu `routes.py` (AC-NO-GOD-UTILS-Split, Pattern analog
Welle-6a `routes_faults.py`). `routes.py` ist mit 5 public Functions
am Limit; Welle-6b haengt zwei weitere Page-Routes hier ab.

Welle-6b-Routes:

- `GET /runs/{run_id}/devices` — Geraete-Grafik-Page mit HTMX-
  Polling auf `GET /runs/{run_id}/devices/state` (REST, 1s-
  Trigger). 4-Spalten-Tabelle `ID / Type / State / Quality`.
  Erfuellt `GG-UI-006`. C3-Realization-Note: JSON-Surface liegt
  auf dem `/state`-Sub-Pfad statt der natuerlichen URL, weil
  FastAPI sonst die UI-Page-Route ueberlagern wuerde
  (Welle-4b-Alarms-Pattern: UI-Page natuerlicher URL, JSON-
  Surface suffixed).
- `GET /runs/{run_id}/system` — Simulationszustands-Dashboard mit
  HTMX-Polling auf `GET /runs/{run_id}/status` (1s) + `GET /health`
  (5s). Run-Status-Block + Service-Health-Block. Erfuellt
  `GG-UI-008`.

Beide Routes erkennen den `HX-Request`-Header und rendern bei
HTMX-Sub-Requests nur den Content-Block (Partial-Switch, Pattern
analog Welle-6a-Faults).

Welle-6b-Review F13: Run-Existenz + 404-Envelope-Konstruktion sind
in `_require_run_or_404` zentralisiert (frueher 2x verbatim
dupliziert in `get_run_devices_page` + `get_run_system_page`).
Welle-6b-Review F14: HX-Request-Detection liegt in `_templates.
is_htmx_request` (Drei-Modul-Duplikat aufgeloest).
"""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from grid_gym.adapters.driving.http_api._dependencies import get_run_repository
from grid_gym.adapters.driving.http_api._schemas import ErrorResponse
from grid_gym.adapters.driving.ui._templates import get_templates, is_htmx_request
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort

visualization_router: APIRouter = APIRouter(tags=["ui"])


def _require_run_or_404(repository: RunRepositoryPort, run_id: str) -> None:
    """Welle-6b-Review F13: gemeinsamer 404-Pfad fuer die zwei
    Visualization-UI-Pages.

    Liefert silent `None`, wenn der Run existiert; wirft sonst
    `HTTPException(404, ErrorResponse(...))` mit GG-API-004-
    Envelope (analog `_runs_router._require_run` /
    `_runs_action_router._ensure_run_exists`, Welle-6a-Review F4-
    Pattern).
    """
    if repository.exists(run_id):
        return
    error = ErrorResponse(
        code="run_not_found",
        message=f"Run '{run_id}' not found.",
        run_id=run_id,
    )
    raise HTTPException(status_code=404, detail=error.model_dump())


@visualization_router.get(
    "/runs/{run_id}/devices",
    response_class=HTMLResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run_devices_page(
    run_id: str,
    request: Request,
    repository: Annotated[RunRepositoryPort, Depends(get_run_repository)],
) -> HTMLResponse:
    """Geraete-Grafik-Page (M5 Welle 6b, Decision 22; `GG-UI-006`).

    Rendert eine Page mit HTMX-Polling-Tabelle auf
    `GET /runs/{run_id}/devices/state` (1s-Trigger). 4-Spalten-
    Layout (`ID` / `Type` / `State` / `Quality`) deckt die
    `GG-UI-006`-Akzeptanz (5 MVP-Geraete mit ID, Typ, Zustand,
    Qualitaetsstatus). Welle-6b-Review F10: poll-target ist die
    JSON-State-Surface, nicht die UI-Page selbst.

    Welle-6b-Anti-Scope (Decision 23): keine Inline-SVG-Grafik,
    kein Chart.js — HTMX-Partial-Tabelle reicht fuer den
    Lastenheft-Pflichttext.

    Bei nicht-existentem Run liefert die Route 404 mit
    `GG-API-004`-Envelope (analog Welle-6a-Faults-Pattern)."""
    _require_run_or_404(repository, run_id)
    templates = get_templates()
    template_name = "devices.html" if not is_htmx_request(request) else "_devices_content.html"
    return cast(
        HTMLResponse,
        templates.TemplateResponse(request, template_name, {"run_id": run_id}),
    )


@visualization_router.get(
    "/runs/{run_id}/system",
    response_class=HTMLResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run_system_page(
    run_id: str,
    request: Request,
    repository: Annotated[RunRepositoryPort, Depends(get_run_repository)],
) -> HTMLResponse:
    """Simulationszustands-Dashboard-Page (M5 Welle 6b, Decision 22;
    `GG-UI-008`).

    Rendert eine Page mit zwei HTMX-Polling-Bloecken:

    - Run-Status-Block: HTMX-Polling auf
      `GET /runs/{run_id}/status` (1s-Trigger), rendert `state`,
      `simulation_time`, `tick_count`.
    - Service-Health-Block: HTMX-Polling auf `GET /health`
      (5s-Trigger), rendert `status="ok"` als „Service: OK".

    Erfuellt `GG-UI-008` (Simulationszustaende-Dashboard mit
    state + tick_count + sim_time + Service-Health).

    Bei nicht-existentem Run liefert die Route 404 mit
    `GG-API-004`-Envelope."""
    _require_run_or_404(repository, run_id)
    templates = get_templates()
    template_name = "system.html" if not is_htmx_request(request) else "_system_content.html"
    return cast(
        HTMLResponse,
        templates.TemplateResponse(request, template_name, {"run_id": run_id}),
    )
