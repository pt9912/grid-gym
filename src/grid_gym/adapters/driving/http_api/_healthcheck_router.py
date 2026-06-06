"""FastAPI-Router fuer Backpressure-Healthcheck-Endpoint
(M6 Welle 4b-c; `GG-RT-001` 10ms-Modus).

Ein REST-Endpoint:

- `GET /runs/{run_id}/healthcheck` — 6-Feld-JSON-Output mit
  Tick-Dauer (p50/p95), missed_ticks, backpressure_status,
  tick_ms, window_size.

Welle-4b-c-D-5 fixiert JSON-only Output. Welle-4b-c-D-6
schliesst ADR-Schaerfungs-Bedarf negativ aus; das Pattern folgt
`_runs_router.py::get_run_status` ohne neuen Vertrag.

Trennung von `_runs_router.py` ist `AC-NO-GOD-UTILS`-getrieben
(C0-Review-Folge F6): separates Modul vermeidet Router-Wuchs,
Pattern analog `_runs_action_router.py` (M5-Welle-1).

Fehler-Mapping (`GG-API-004`):

- 404 `run_not_found`: Run existiert nicht im Repository.
- 503 `healthcheck_not_available`: Run existiert, aber kein
  Healthcheck-Adapter registriert (z. B. reine Repository-only-
  Runs ohne aktiven Driver, oder Welle-4a-Pre-Migration-Setup
  ohne Adapter-Konstruktion).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from grid_gym.adapters.driving.http_api._dependencies import (
    get_run_repository,
)
from grid_gym.adapters.driving.http_api._schemas import ErrorResponse
from grid_gym.adapters.driving.http_api._tick_loop_registry import (
    TickLoopRegistry,
    get_tick_loop_registry,
)
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort

healthcheck_router = APIRouter(tags=["runs"])


def _require_run_or_404(run_id: str, repository: RunRepositoryPort) -> None:
    """Welle-4b-c §1.2: 404 vor 503. Wenn der Run nicht
    existiert, ist `run_not_found` die richtigere Antwort als
    `healthcheck_not_available`."""

    if not repository.exists(run_id):
        error = ErrorResponse(
            code="run_not_found",
            message=f"Run '{run_id}' not found.",
            run_id=run_id,
        )
        raise HTTPException(status_code=404, detail=error.model_dump())


@healthcheck_router.get(
    "/runs/{run_id}/healthcheck",
    responses={
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def get_run_healthcheck(
    run_id: str,
    repository: Annotated[
        RunRepositoryPort,
        Depends(get_run_repository),
    ],
    tick_loop_registry: Annotated[
        TickLoopRegistry,
        Depends(get_tick_loop_registry),
    ],
) -> dict[str, object]:
    """M6-Welle-4b-c (`GG-RT-001` Backpressure-Healthcheck).

    Lastenheft-Akzeptanz Z. 463-465: dokumentiert Tick-Dauer,
    p95-Jitter, verpasste Ticks und Backpressure-Status im
    10ms-Modus.

    Welle-4b-c-D-1 Adapter-Side-Pattern: Mess geschieht im
    Driving-Adapter (`TickLoopHealthcheckAdapter`); Core bleibt
    AC-NO-TIME-konform und unangetastet.
    """
    _require_run_or_404(run_id, repository)
    adapter = tick_loop_registry.healthcheck_adapter_for(run_id)
    if adapter is None:
        error = ErrorResponse(
            code="healthcheck_not_available",
            message=(
                f"Run '{run_id}' has no healthcheck adapter registered. "
                "The run exists but no active Tick-Driver is wired."
            ),
            run_id=run_id,
        )
        raise HTTPException(status_code=503, detail=error.model_dump())
    return adapter.healthcheck()
