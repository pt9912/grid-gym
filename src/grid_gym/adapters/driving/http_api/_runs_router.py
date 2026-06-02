"""FastAPI-Router fuer Run-GET-Endpunkte (M5 Welle 1 + Welle 4a,
ADR 0037 + 0039).

Drei REST-Endpunkte:

- `GET /runs/{run_id}`         — Run-Detail (`GG-API-001`).
- `GET /runs/{run_id}/status`  — Kompakter Run-Status (Welle-4a
  produktiv, Welle-1 war Stub).
- `GET /runs/{run_id}/snapshot`— Snapshot-Export-Stub.

Welle-4a-Wiring (ADR 0039 Decision 14): `GET /status` liest jetzt
den `RunStatus`-Lifecycle-State aus dem RunRepository und holt
`tick_count`/`simulation_time` aus dem im `TickLoopRegistry`
hinterlegten `TickLoop` (sofern vorhanden); ohne aktiven
TickLoop bleiben die Counter `0`.

Welle-1-Stub-Erbschaft: `GET /runs/{run_id}/snapshot` bleibt
Stub-Pointer; Welle 5 ersetzt es durch die `SnapshotEnvelope`-
v2-Serialisierung.

Standard-Fehler-Format `GG-API-004`: bei nicht-existentem
Run gibt der Endpoint 404 mit `ErrorResponse`-Body
(`code="run_not_found"`).

Trennung von POST/WS-Endpunkten unter `_runs_action_router.py`
ist `AC-NO-GOD-UTILS`-getrieben (max 5 public functions pro
Modul); semantisch waeren alle `/runs/{id}/*`-Endpunkte ein
einzelner logischer Block.
"""

from __future__ import annotations

import dataclasses
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from grid_gym.adapters.driven.alarm_stream_inmemory import AlarmHistoryBuffer
from grid_gym.adapters.driving.http_api._dependencies import (
    get_alarm_history_buffer,
    get_run_repository,
)
from grid_gym.adapters.driving.http_api._schemas import (
    AlarmDto,
    AlarmsResponse,
    ErrorResponse,
    RunDetailResponse,
    RunStatusResponse,
    SnapshotResponse,
)
from grid_gym.adapters.driving.http_api._tick_loop_registry import (
    TickLoopRegistry,
    get_tick_loop_registry,
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
    tick_loop_registry: Annotated[
        TickLoopRegistry,
        Depends(get_tick_loop_registry),
    ],
) -> RunStatusResponse:
    """Kompakter Run-Status (`GG-API-001`, ADR 0039 Decision 14).

    Welle-4a-produktiv: `state` aus Repository, `tick_count` und
    `simulation_time` aus dem im `TickLoopRegistry` registrierten
    `TickLoop`. Ohne aktiven TickLoop (Welle-1-Pfad fuer rein-
    persistierte Runs ohne Driver) bleiben die Counter `0`.

    Wird vom UI per HTMX-Polling alle ~1s aufgerufen
    (`hx-trigger="every 1s"`); 404 bei nicht-existentem Run.
    """
    _resolve_repository(run_id, repository)
    status = repository.get_status(run_id)
    tick_loop = tick_loop_registry.tick_loop_for(run_id)
    if tick_loop is None:
        tick_count = 0
        simulation_time = 0
    else:
        tick_count = tick_loop.tick_count
        simulation_time = tick_loop.tick_count * tick_loop.tick_ms
    return RunStatusResponse(
        run_id=run_id,
        state=status,
        simulation_time=simulation_time,
        tick_count=tick_count,
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


@runs_router.get(
    "/runs/{run_id}/alarms-history",
    response_model=AlarmsResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run_alarms_history(
    run_id: str,
    repository: Annotated[
        RunRepositoryPort,
        Depends(get_run_repository),
    ],
    history_buffer: Annotated[
        AlarmHistoryBuffer,
        Depends(get_alarm_history_buffer),
    ],
    limit: int = 50,
) -> AlarmsResponse:
    """Liefert die letzten `limit` Alarms aus dem `AlarmHistoryBuffer`
    (M5 Welle 4b, ADR 0040 Decision 17).

    Wird vom UI per HTMX-`hx-get` beim Page-Load fuer die
    Initial-Hydration aufgerufen; Live-Updates kommen via
    WS-`/alarms-stream`. Welle-4b-Default `limit=50`; max
    `200` durch Buffer-Capacity.
    """
    _resolve_repository(run_id, repository)
    clamped_limit = min(max(limit, 0), 200)
    alarms = history_buffer.get_recent(run_id=run_id, limit=clamped_limit)
    return AlarmsResponse(
        run_id=run_id,
        alarms=[AlarmDto(**dataclasses.asdict(alarm)) for alarm in alarms],
    )
