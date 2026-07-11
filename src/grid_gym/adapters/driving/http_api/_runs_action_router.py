"""FastAPI-Router fuer Run-Action-Endpunkte (M5 Welle 1/3/4a,
ADR 0037 + 0038 + 0039).

Drei Endpunkte (2 REST + 1 WebSocket):

- `POST /runs/{run_id}/control` — Run-Steuerung mit Action-
  Body (`pause`/`resume`/`stop`; ADR 0037 Decision API-1;
  Welle-4a-Wiring auf TickLoop-Control-Surface per ADR 0039
  Decision 13).
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
404 mit `ErrorResponse`-Body bei nicht-existentem Run, **409**
mit `code="invalid_transition"` bei unerlaubtem Control-State-
Uebergang (Welle 4a), **503** mit `code="tick_loop_not_active"`
bei persistiertem Run ohne aktiven TickLoop-Driver; der
WebSocket-Endpoint schliesst mit Close-Code `1008` (Policy-
Violation).
"""

from __future__ import annotations

import dataclasses
import uuid
from collections.abc import Mapping
from typing import Annotated, Final, cast

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from grid_gym.adapters.driving.http_api._dependencies import get_run_repository
from grid_gym.adapters.driving.http_api._schemas import (
    ControlRequest,
    ControlResponse,
    ErrorResponse,
    FaultInjectionRequest,
    FaultInjectionResponse,
)
from grid_gym.adapters.driving.http_api._tick_loop_registry import (
    TickLoopRegistry,
    get_tick_loop_registry,
)
from grid_gym.hexagon.core.domain.fault import (
    FAULT_TYPE_CELL_FAILURE,
    FAULT_TYPE_CONNECTION_LOSS,
    FAULT_TYPE_FREQUENCY_DROP,
    FAULT_TYPE_GENSET_FAULT,
    FAULT_TYPE_VOLTAGE_DROP,
    FAULT_TYPE_WINDING_FAULT,
)
from grid_gym.hexagon.core.errors import TickLoopInvalidTransitionError
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort
from grid_gym.hexagon.ports.driving.alarm_stream import AlarmStreamPort
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
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def post_run_control(
    run_id: str,
    request: Annotated[ControlRequest, ...],
    repository: Annotated[RunRepositoryPort, Depends(get_run_repository)],
    tick_loop_registry: Annotated[TickLoopRegistry, Depends(get_tick_loop_registry)],
) -> ControlResponse:
    """Run-Steuerung mit Action-Body (ADR 0037 Decision API-1 +
    ADR 0039 Decision 13).

    Welle-4a-Wiring: ruft die passende
    `TickLoop.request_*`-Methode (`request_pause`/
    `request_resume`/`request_stop`); Repository-Mirror laeuft
    transparent im TickLoop. Status-Codes:

    - 404 — Run nicht persistiert.
    - 409 — Invalid-Transition (z. B. `pause` auf bereits
      gestopptem Run); `ErrorResponse.code="invalid_transition"`.
    - 503 — Run persistiert, aber kein aktiver TickLoop-Driver
      registriert; `ErrorResponse.code="tick_loop_not_active"`.
      Welle-4a-Single-Demo-Run-Stand; produktive Multi-Run-
      Variante in Welle 5.
    - 200 — Action akzeptiert; `accepted=True`.
    """
    _ensure_run_exists(run_id, repository)
    tick_loop = tick_loop_registry.tick_loop_for(run_id)
    if tick_loop is None:
        error = ErrorResponse(
            code="tick_loop_not_active",
            message=(
                f"Run '{run_id}' is persisted but has no active TickLoop "
                "driver. Welle 4a only wires the demo run; "
                "production multi-run setup follows in Welle 5."
            ),
            run_id=run_id,
        )
        raise HTTPException(status_code=503, detail=error.model_dump())
    try:
        tick_loop.request(request.action)
    except TickLoopInvalidTransitionError as exc:
        error = ErrorResponse(
            code="invalid_transition",
            message=str(exc),
            details={
                "current_state": exc.current_state,
                "target_state": exc.target_state,
            },
            run_id=run_id,
        )
        raise HTTPException(status_code=409, detail=error.model_dump()) from exc
    return ControlResponse(run_id=run_id, action=request.action, accepted=True)


_FAULT_TYPE_TO_DEVICE_TYPE: Final[Mapping[str, str]] = {
    FAULT_TYPE_CELL_FAILURE: "battery",
    FAULT_TYPE_VOLTAGE_DROP: "grid_connection",
    FAULT_TYPE_FREQUENCY_DROP: "grid_connection",
    FAULT_TYPE_CONNECTION_LOSS: "ev_charger",
    FAULT_TYPE_WINDING_FAULT: "transformer",
    FAULT_TYPE_GENSET_FAULT: "diesel_generator",
}
"""M5-Welle-6a (Decision 20): Whitelist Fault-Typ ↔ Device-Typ.
Welle-7+/M3-Fault-Typen muessen sich hier eintragen oder eine
Plugin-Form an ADR 0022 §2.2 verankern. Welle-6a-Review F9:
Keys sind `FAULT_TYPE_*`-Konstanten aus
`hexagon/core/faults/types.py` (Single-Source-of-Truth)."""


@runs_action_router.post(
    "/runs/{run_id}/faults",
    response_model=FaultInjectionResponse,
    status_code=201,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def post_run_faults(
    run_id: str,
    request: Annotated[FaultInjectionRequest, ...],
    repository: Annotated[RunRepositoryPort, Depends(get_run_repository)],
    tick_loop_registry: Annotated[
        TickLoopRegistry,
        Depends(get_tick_loop_registry),
    ],
) -> FaultInjectionResponse:
    """Fault-Injection-Submit (`GG-API-001`, M5 Welle 6a Decision
    19/20).

    Welle-1-Stub-Antwort bleibt: erzeugt `fault_id` (UUIDv4) +
    `accepted=True`. Welle-6a-Erweiterung (Decision 19): kein
    `FaultPort.activate`-Call (Dynamic-FaultPort-Mutation
    Anti-Scope; YAML-side faults erfuellen `GG-DEMO-006`).
    Welle-6a-Erweiterung (Decision 20): **Cross-Field-Validation**
    pruefte vor dem Echo zwei Bedingungen:

    1. `request.target` muss im aktiven Run-Scenario existieren
       (Lookup ueber `tick_loop.device_types`).
    2. `request.fault_type` muss zum Target-Device-Typ passen
       (Whitelist `_FAULT_TYPE_TO_DEVICE_TYPE`).

    Beide Fehler liefern 422 + `ErrorResponse`; wenn kein
    TickLoop registriert ist (Welle-1-Stub-Pfad oder Multi-Run-
    Anti-Scope), gibt der Endpunkt 503 mit
    `code="tick_loop_not_active"` (analog Control-Pattern).
    """
    _ensure_run_exists(run_id, repository)
    tick_loop = tick_loop_registry.tick_loop_for(run_id)
    if tick_loop is None:
        error = ErrorResponse(
            code="tick_loop_not_active",
            message=(
                f"Run '{run_id}' is persisted but has no active TickLoop "
                "driver. Welle-6a Cross-Field-Validation needs the "
                "device-type mapping of the running TickLoop."
            ),
            run_id=run_id,
        )
        raise HTTPException(status_code=503, detail=error.model_dump())
    device_types = tick_loop.device_types
    target_type = device_types.get(request.target)
    if target_type is None:
        error = ErrorResponse(
            code="fault_unknown_target",
            message=(
                f"Target device '{request.target}' is not part of run "
                f"'{run_id}'. Known device IDs: {sorted(device_types)}."
            ),
            details={"target": request.target, "known": sorted(device_types)},
            run_id=run_id,
        )
        raise HTTPException(status_code=422, detail=error.model_dump())
    expected_device_type = _FAULT_TYPE_TO_DEVICE_TYPE.get(request.fault_type)
    if expected_device_type is None:
        # Welle-6a-Review F5: separater Code fuer „unbekannter Typ"
        # (vs. „Typ passt nicht zu Target"). Clients koennen die
        # beiden Faelle programmatisch unterscheiden.
        error = ErrorResponse(
            code="fault_type_unknown",
            message=(
                f"Fault type '{request.fault_type}' is unknown. "
                f"Welle-6a whitelist: {sorted(_FAULT_TYPE_TO_DEVICE_TYPE)}."
            ),
            details={
                "fault_type": request.fault_type,
                "known": sorted(_FAULT_TYPE_TO_DEVICE_TYPE),
            },
            run_id=run_id,
        )
        raise HTTPException(status_code=422, detail=error.model_dump())
    if expected_device_type != target_type:
        error = ErrorResponse(
            code="fault_invalid_type_for_target",
            message=(
                f"Fault type '{request.fault_type}' is not allowed on "
                f"device '{request.target}' (type '{target_type}'). "
                f"Expected device type for this fault: '{expected_device_type}'."
            ),
            details={
                "fault_type": request.fault_type,
                "target": request.target,
                "target_type": target_type,
                "expected_target_type": expected_device_type,
            },
            run_id=run_id,
        )
        raise HTTPException(status_code=422, detail=error.model_dump())
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


@runs_action_router.websocket("/runs/{run_id}/alarms-stream")
async def ws_run_alarms_stream(websocket: WebSocket, run_id: str) -> None:
    """Live-Alarm-WebSocket (`GG-UI-005`, ADR 0040 Decision 17).

    Welle-4b-Verhalten (Pattern 1:1 parallel zu
    `ws_run_telemetry`):

    - Accept Connection.
    - Pruefe Run-Existenz (falls nicht persistiert: close
      mit Code 1008 = Policy-Violation analog 404-REST).
    - Subscribt am `AlarmStreamPort` mit `run_id`-Filter.
    - Pusht jeden `Alarm` als JSON (`asdict`-Serialisierung).
    - Bei `WebSocketDisconnect` (Browser-Tab schliesst) gibt
      der AsyncIterator-`finally`-Block den Subscriber-Slot
      frei (ADR 0040 §2.3; Pattern aus ADR 0038 §2.3).
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
        AlarmStreamPort | None,
        getattr(websocket.app.state, "alarm_stream", None),
    )
    if stream is None:
        await websocket.close(code=1011, reason="AlarmStreamPort is not configured.")
        return
    try:
        async for alarm in stream.subscribe(run_id=run_id):
            await websocket.send_json(dataclasses.asdict(alarm))
    except WebSocketDisconnect:
        return
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            return
