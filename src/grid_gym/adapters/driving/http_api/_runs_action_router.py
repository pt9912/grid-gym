"""FastAPI-Router fuer Run-Action-Endpunkte (M5 Welle 1/3, ADR 0037 + 0038).

Drei Endpunkte (2 REST + 1 WebSocket):

- `POST /runs/{run_id}/control` — Run-Steuerung mit Action-
  Body (`pause`/`resume`/`stop`; ADR 0037 Decision API-1).
- `POST /runs/{run_id}/faults`  — Fault-Injection-Submit
  (Welle-1-Stub; echtes `FaultPort.activate` in Welle 6).
- `WS   /runs/{run_id}/telemetry` — Live-Telemetry-Stream
  (`GG-API-002`; Welle-3-Subscribe-Pattern auf
  `TelemetryStreamPort`, ADR 0038).

Trennung von den GET-Endpunkten in `_runs_router.py` ist
`AC-NO-GOD-UTILS`-getrieben (max 5 public functions pro
Modul); semantisch waeren alle `/runs/{id}/*`-Endpunkte ein
einzelner logischer Block.

Standard-Fehler-Format `GG-API-004`: REST-Endpunkte geben
404 mit `ErrorResponse`-Body bei nicht-existentem Run; der
WebSocket-Endpoint schliesst mit Close-Code `1008` (Policy-
Violation).
"""

from __future__ import annotations

import dataclasses
import uuid
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from grid_gym.adapters.driving.http_api._dependencies import get_run_repository
from grid_gym.adapters.driving.http_api._schemas import (
    ControlRequest,
    ControlResponse,
    ErrorResponse,
    FaultInjectionRequest,
    FaultInjectionResponse,
)
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort
from grid_gym.hexagon.ports.driving.telemetry_stream import TelemetryStreamPort


runs_action_router = APIRouter(tags=["runs"])


def _ensure_run_exists(run_id: str, repository: RunRepositoryPort) -> None:
    """Wirft 404 mit `GG-API-004`-Fehler-Format wenn der Run
    nicht persistiert ist. Welle-1-Helper analog
    `_runs_router._require_run`, aber **ohne** `RunMetadata`-
    Return (Action-Endpunkte brauchen die Metadaten nicht).
    """
    if not repository.exists(run_id):
        error = ErrorResponse(
            code="run_not_found",
            message=f"Run '{run_id}' not found.",
            run_id=run_id,
        )
        raise HTTPException(status_code=404, detail=error.model_dump())


@runs_action_router.post(
    "/runs/{run_id}/control",
    response_model=ControlResponse,
    responses={404: {"model": ErrorResponse}},
)
def post_run_control(
    run_id: str,
    request: Annotated[ControlRequest, ...],
    repository: Annotated[RunRepositoryPort, Depends(get_run_repository)],
) -> ControlResponse:
    """Run-Steuerung mit Action-Body (ADR 0037 Decision API-1).

    Welle-1-Stub: nimmt die Action entgegen und gibt
    `accepted=True` zurueck — kein echtes TickLoop-Pause/
    Resume/Stop-Wiring (Welle 4).
    """
    _ensure_run_exists(run_id, repository)
    return ControlResponse(run_id=run_id, action=request.action, accepted=True)


@runs_action_router.post(
    "/runs/{run_id}/faults",
    response_model=FaultInjectionResponse,
    status_code=201,
    responses={404: {"model": ErrorResponse}},
)
def post_run_faults(
    run_id: str,
    request: Annotated[FaultInjectionRequest, ...],
    repository: Annotated[RunRepositoryPort, Depends(get_run_repository)],
) -> FaultInjectionResponse:
    """Fault-Injection-Submit (`GG-API-001`).

    Welle-1-Stub: erzeugt eine `fault_id` (UUIDv4) und gibt
    `accepted=True` zurueck — kein `FaultPort.activate`-Call
    (Welle 6). Der `request`-Body wird gegen das Pydantic-
    Schema validiert; ungueltige Bodies geben 422 zurueck.
    """
    _ensure_run_exists(run_id, repository)
    # Body wird durch Pydantic validiert; in Welle 6 wird das
    # Request-Objekt an `FaultPort.activate(...)` weitergegeben.
    _ = request
    return FaultInjectionResponse(
        run_id=run_id,
        fault_id=str(uuid.uuid4()),
        accepted=True,
    )


@runs_action_router.websocket("/runs/{run_id}/telemetry")
async def ws_run_telemetry(websocket: WebSocket, run_id: str) -> None:
    """Live-Telemetry-WebSocket (`GG-API-002`, ADR 0038).

    Welle-3-Verhalten:

    - Accept Connection.
    - Pruefe Run-Existenz (falls nicht persistiert: close
      mit Code 1008 = Policy-Violation analog 404-REST).
    - Subscribt am `TelemetryStreamPort` mit `run_id`-Filter.
    - Pusht jeden `TelemetryPoint` als JSON
      (`asdict`-Serialisierung).
    - Bei `WebSocketDisconnect` (Browser-Tab schliesst) gibt
      der AsyncIterator-`finally`-Block den Subscriber-Slot
      frei (ADR 0038 §2.3).
    """
    await websocket.accept()
    repository = cast(
        RunRepositoryPort | None,
        getattr(websocket.app.state, "run_repository", None),
    )
    if repository is None or not repository.exists(run_id):
        await websocket.close(code=1008, reason=f"Run '{run_id}' not found.")
        return
    stream = cast(
        TelemetryStreamPort | None,
        getattr(websocket.app.state, "telemetry_stream", None),
    )
    if stream is None:
        await websocket.close(code=1011, reason="TelemetryStreamPort is not configured.")
        return
    try:
        async for point in stream.subscribe(run_id=run_id):
            await websocket.send_json(dataclasses.asdict(point))
    except WebSocketDisconnect:
        return
    finally:
        # Ensure socket is closed even if subscribe-loop exits
        # for non-Disconnect reasons (e.g., app shutdown).
        try:
            await websocket.close()
        except RuntimeError:
            # Already closed by client; swallow.
            return
