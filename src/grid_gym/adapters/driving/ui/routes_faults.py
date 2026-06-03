"""Welle-6a-Fault-Injection-Form-Page-Route (M5 Welle 6a,
Decisions 19/20).

Ausgelagert aus `routes.py` wegen `AC-NO-GOD-UTILS` (max 5
public top-level functions pro Modul). Pattern analog zur
Welle-1-Split `_runs_router.py` + `_runs_action_router.py`.

Welle-6a-Route:

- `GET /runs/{run_id}/faults` — rendert das Fault-Injection-
  Form (5 Felder + HTMX-POST gegen `POST /runs/{run_id}/
  faults`). Cross-Field-Validation laeuft server-side im
  POST-Handler (Decision 20); diese Route stellt nur die
  Form-Surface bereit (`GG-UI-007`).
"""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from grid_gym.adapters.driving.http_api._dependencies import get_run_repository
from grid_gym.adapters.driving.ui._templates import get_templates
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort

faults_router: APIRouter = APIRouter(tags=["ui"])


def _is_htmx_request(request: Request) -> bool:
    """Welle-6a-Duplikat zu `routes._is_htmx_request`. Beide
    Module sind reine Route-Definitions und teilen die kleine
    Helper-Funktion bewusst nicht ueber einen dritten Modul-
    Schnitt (AC-NO-GOD-UTILS bevorzugt kleine, autarke
    Route-Module)."""
    return request.headers.get("hx-request", "").lower() == "true"


@faults_router.get("/runs/{run_id}/faults", response_class=HTMLResponse)
def get_run_faults(
    run_id: str,
    request: Request,
    repository: Annotated[RunRepositoryPort, Depends(get_run_repository)],
) -> HTMLResponse:
    """Fault-Injection-Form-Page (M5 Welle 6a, Decisions 19/20).

    Rendert ein HTML-Form mit fault_type/target/start_at_tick/
    duration_ticks/recovery + HTMX-POST gegen
    `POST /runs/{run_id}/faults`. Erfuellt `GG-UI-007`
    (Form-Validation-only; keine dynamische Fault-Aktivierung).
    Welle-6a-Substanz: Cross-Field-Validation laeuft server-
    side im POST-Handler (Decision 20).
    """
    if not repository.exists(run_id):
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    templates = get_templates()
    template_name = "faults.html" if not _is_htmx_request(request) else "_faults_content.html"
    return cast(
        HTMLResponse,
        templates.TemplateResponse(request, template_name, {"run_id": run_id}),
    )
