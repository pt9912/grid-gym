"""FastAPI-Router fuer Run-GET-Endpunkte (M5 Welle 1, ADR 0037).

Drei REST-Endpunkte:

- `GET /runs/{run_id}`         — Run-Detail (`GG-API-001`).
- `GET /runs/{run_id}/status`  — Kompakter Run-Status.
- `GET /runs/{run_id}/snapshot`— Snapshot-Export-Stub.

Welle-1-Anti-Scope: alle drei Endpunkte sind **Stubs**
hinsichtlich der dynamischen Werte (`state`/`simulation_
time`/`tick_count`/Snapshot-Body); echte Werte kommen mit
Welle 4 (`TickLoop`-Wiring) bzw. Welle 5 (Snapshot-Envelope-
Serialisierung).

Standard-Fehler-Format `GG-API-004`: bei nicht-existentem
Run gibt der Endpoint 404 mit `ErrorResponse`-Body
(`code="run_not_found"`).

Trennung von POST/WS-Endpunkten unter `_runs_action_router.py`
ist `AC-NO-GOD-UTILS`-getrieben (max 5 public functions pro
Modul); semantisch waeren alle `/runs/{id}/*`-Endpunkte ein
einzelner logischer Block.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from grid_gym.adapters.driving.http_api._dependencies import get_run_repository
from grid_gym.adapters.driving.http_api._schemas import (
    ErrorResponse,
    RunDetailResponse,
    RunStatusResponse,
    SnapshotResponse,
)
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort


runs_router = APIRouter(tags=["runs"])


def _require_run(run_id: str, repository: RunRepositoryPort) -> RunMetadata:
    """Liefert die `RunMetadata` zu `run_id` oder wirft 404
    mit `GG-API-004`-Fehler-Format.

    Welle-1-Helper: alle `/runs/{run_id}/*`-Endpunkte
    (REST + WS via `_runs_action_router`) nutzen das, um
    Run-Existenz vor der Stub-Logik zu pruefen.
    """
    if not repository.exists(run_id):
        error = ErrorResponse(
            code="run_not_found",
            message=f"Run '{run_id}' not found.",
            run_id=run_id,
        )
        raise HTTPException(status_code=404, detail=error.model_dump())
    return repository.get_by_id(run_id)


def _resolve_repository(run_id: str, repository: RunRepositoryPort) -> RunMetadata:
    """Wrapper um `_require_run` mit gleicher Signatur — laesst
    Test-Mocks den Helper isoliert auswechseln (Welle 4+).

    Aktuell delegiert nur. Bewusst belassen, um die Welle-1-
    Helper-Surface stabil zu halten waehrend Welle 4 die echte
    TickLoop-Integration einzieht.
    """
    return _require_run(run_id, repository)


@runs_router.get(
    "/runs/{run_id}",
    response_model=RunDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run(
    run_id: str,
    repository: Annotated[
        RunRepositoryPort,
        Depends(get_run_repository),
    ],
) -> RunDetailResponse:
    """Liefert die vollstaendige `RunMetadata` zu `run_id`
    (`GG-API-001`)."""
    metadata = _resolve_repository(run_id, repository)
    return RunDetailResponse(
        run_id=metadata.run_id,
        scenario_hash=metadata.scenario_hash,
        schema_version=metadata.schema_version,
        seed=metadata.seed,
        tick_ms=metadata.tick_ms,
        started_at=metadata.started_at,
        ended_at=metadata.ended_at,
        tool_version=metadata.tool_version,
    )


@runs_router.get(
    "/runs/{run_id}/status",
    response_model=RunStatusResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run_status(
    run_id: str,
    repository: Annotated[
        RunRepositoryPort,
        Depends(get_run_repository),
    ],
) -> RunStatusResponse:
    """Kompakter Run-Status (`GG-API-001`).

    Welle-1-Stub: `state` ist immer `pending`,
    `simulation_time` und `tick_count` immer `0`. Welle 4
    bringt das echte TickLoop-Wiring.
    """
    _resolve_repository(run_id, repository)
    return RunStatusResponse(
        run_id=run_id,
        state="pending",
        simulation_time=0,
        tick_count=0,
    )


@runs_router.get(
    "/runs/{run_id}/snapshot",
    response_model=SnapshotResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run_snapshot(
    run_id: str,
    repository: Annotated[
        RunRepositoryPort,
        Depends(get_run_repository),
    ],
) -> SnapshotResponse:
    """Snapshot-Export (`GG-API-001`).

    Welle-1-Stub: gibt nur einen `schema_ref`-Pointer
    zurueck. Echte Snapshot-Serialisierung kommt in Welle 4/5
    mit `SnapshotEnvelope`-v2-Body.
    """
    _resolve_repository(run_id, repository)
    return SnapshotResponse(
        run_id=run_id,
        schema_ref="grid-gym.snapshot.envelope.v2",
    )
