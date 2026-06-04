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
from collections.abc import Callable, Mapping
from typing import Annotated, Protocol, cast

from fastapi import APIRouter, Depends, HTTPException, Request

from grid_gym.adapters.driving.http_api._dependencies import (
    get_alarm_history_buffer,
    get_run_repository,
)
from grid_gym.adapters.driving.http_api._schemas import (
    AlarmDto,
    AlarmsResponse,
    DeviceStateEntry,
    DevicesResponse,
    ErrorResponse,
    RunDetailResponse,
    RunStatusResponse,
    SnapshotResponse,
)
from grid_gym.adapters.driving.http_api._tick_loop_registry import (
    TickLoopRegistry,
    get_tick_loop_registry,
)
from grid_gym.hexagon.core.domain.quality import QUALITY_SEVERITY, Quality
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort


runs_router = APIRouter(tags=["runs"])


# M5-Welle-6b-Review F5/F15: worst-case-Severity-Ranking lebt jetzt in
# `core/domain/quality.py` neben der Quality-Enum (Knowledge-Locality
# beim Hinzufuegen neuer Enum-Varianten). `_aggregate_quality` nutzt
# `.get(...)` mit `INVALID`-Default fuer Forward-Compat-Defense:
# unbekannte Quality-Werte zaehlen als „schlecht genug um aufzufallen"
# statt mit KeyError zu eskalieren (vgl. Welle-6a R3 silent-drop).
_UNKNOWN_QUALITY_RANK = QUALITY_SEVERITY[Quality.INVALID]


class _DeviceView(Protocol):
    """Minimal-Protocol des Adapter-internen Views auf ein Geraet.

    AC-ADAPTER-PURE verbietet den Import von
    `grid_gym.hexagon.core.devices` aus der Adapter-Schicht; dieser
    Schicht-lokale Protocol-Stub spiegelt nur die drei Member, die
    der Welle-6b-Endpunkt liest (`device_id`, `snapshot()`,
    `telemetry()`). Concretisierungen (BatteryDevice, PvDevice, ...)
    erfuellen das Protocol strukturell durch die existierende
    `DeviceModel`-Surface im Core.

    Welle-6b-Review F12: `@runtime_checkable` entfaellt — kein
    `isinstance(..., _DeviceView)`-Call existiert, der Decorator war
    purer Overhead + Mis-Signal an Reviewer.
    """

    @property
    def device_id(self) -> str: ...

    def snapshot(self) -> Mapping[str, object]: ...

    def telemetry(self) -> tuple[TelemetryPoint, ...]: ...


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
    "/runs/{run_id}/devices/state",
    response_model=DevicesResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run_devices_state(
    run_id: str,
    repository: Annotated[
        RunRepositoryPort,
        Depends(get_run_repository),
    ],
    tick_loop_registry: Annotated[
        TickLoopRegistry,
        Depends(get_tick_loop_registry),
    ],
) -> DevicesResponse:
    """Per-Device-State + Quality-Marker fuer alle Run-Devices
    (M5 Welle 6b, Decision 21; `GG-UI-006`).

    Welle-6b-Realization (Slice-Doc §3.1 → C3-Realization-Note):
    Decision 21 sah `GET /runs/{run_id}/devices` als JSON-URL vor;
    Decision 22 nutzt denselben Pfad fuer die UI-Page. FastAPI
    routet aber path+method first-match — die naheliegende
    Aufloesung ist das Welle-4b-Alarms-Pattern (UI behaelt die
    natuerliche URL, JSON haengt einen Sub-Pfad an). JSON-Surface
    wandert daher auf `/runs/{run_id}/devices/state`; Response-
    Shape + Decision-21-Felder bleiben unveraendert.

    Welle-6b-produktiv: liest die Devices aus dem im
    `TickLoopRegistry` registrierten TickLoop, joint sie ueber
    `tick_loop.device_types` (Welle-6a-Property) mit dem
    Device-Typ-Segment und extrahiert pro Typ das Welle-6b-Pflicht-
    State-Subset (Decision 21 §3.1). Die `quality` jedes Devices ist
    die worst-case `Quality` der letzten `device.telemetry()`-
    Sequenz; bei leerer Telemetrie (Pre-First-Tick) faellt der Wert
    auf `VALID`.

    Welle-7+/M3-Geraete ohne `_DEVICE_TYPE_BY_CLASS_NAME`-Eintrag
    werden durch `device_types` gedroppt (Welle-6a R3-Symmetrie);
    der Endpoint silent-droppt sie analog statt 500 zu werfen.

    Ohne aktiven TickLoop (Welle-1-Stub-Pfad fuer rein persistierte
    Runs) bleibt die `devices`-Liste leer; der Status-Endpoint
    spiegelt das mit `tick_count=0`.

    Wird vom UI (`GET /runs/{id}/devices`-Page) per HTMX-Polling
    alle ~1s aufgerufen; 404 bei nicht-existentem Run
    (`GG-API-004`).
    """
    _resolve_repository(run_id, repository)
    tick_loop = tick_loop_registry.tick_loop_for(run_id)
    if tick_loop is None:
        return DevicesResponse(run_id=run_id, devices=[])
    device_types = tick_loop.device_types
    entries: list[DeviceStateEntry] = []
    # Welle-6b-Review F9: TickLoop.devices ist jetzt eine oeffentliche
    # Property (analog `device_types`); der Welle-6b-C2-Pfad ueber
    # `cast(..., tick_loop._devices)` ist abgeloest. Iteration-Source
    # bleibt die deterministische Konstruktor-Reihenfolge; `device_
    # types` joinst pro Device das Typ-Segment und filtert Welle-7+/M3-
    # Klassen, die im Mapping fehlen (silent-drop-Symmetrie zur Welle-
    # 6a-Fault-Validation). Schicht-lokales `_DeviceView`-Protocol
    # haelt den AC-ADAPTER-PURE-Contract ein; der Core-`DeviceModel`
    # erfuellt es strukturell, das `cast(...)` greift nur, um die
    # Tuple-Invarianz auf das Protocol zu uebertragen.
    devices = cast(tuple[_DeviceView, ...], tick_loop.devices)
    for device in devices:
        device_type = device_types.get(device.device_id)
        if device_type is None:
            continue
        state = _extract_state_subset(device, device_type)
        if state is None:
            # Welle-6b-Review F2: pre-init devices liefern aus
            # `snapshot()` nur `{"version": N}` (Pflicht-Felder
            # fehlen). Statt 500 zu werfen, silent-droppen wir das
            # Device — konsistent zur Welle-6a-R3-Drift-Defense.
            continue
        entries.append(
            DeviceStateEntry(
                device_id=device.device_id,
                device_type=device_type,
                state=state,
                quality=_aggregate_quality(device),
            )
        )
    return DevicesResponse(run_id=run_id, devices=entries)


def _aggregate_quality(device: _DeviceView) -> Quality:
    """Worst-case `Quality` ueber alle TelemetryPoints der letzten
    `device.telemetry()`-Sequenz (M5 Welle 6b, Decision 21).

    Pre-First-Tick (`telemetry()` ist `()` per `DeviceModel`-Protocol
    §2.6) faellt auf `Quality.VALID` zurueck. Severity-Ranking siehe
    `QUALITY_SEVERITY` (hoeher = schlechter).

    Welle-6b-Review F5: unbekannte Quality-Werte (z. B. Welle-N-
    Erweiterung ohne Mapping-Update) bekommen `_UNKNOWN_QUALITY_RANK`
    (= INVALID-Severity) statt KeyError — Forward-Compat-Defense
    analog zur Welle-6a-R3-Symmetrie.
    """
    worst = Quality.VALID
    worst_rank = QUALITY_SEVERITY[worst]
    for point in device.telemetry():
        rank = QUALITY_SEVERITY.get(point.quality, _UNKNOWN_QUALITY_RANK)
        if rank > worst_rank:
            worst = point.quality
            worst_rank = rank
    return worst


def _extract_state_subset(
    device: _DeviceView,
    device_type: str,
) -> dict[str, str | bool] | None:
    """Welle-6b-Pflicht-State-Subset pro Device-Typ (Decision 21 §3.1).

    Liest aus `device.snapshot()` nur die UI-Pflicht-Felder und
    serialisiert `Decimal`-Werte via `str(...)` (canonical_json-
    Konsistenz; ADR 0021 §2.9 + Welle-3-`TelemetryPoint.value`-
    Pattern). Bool-Flags (`cell_failure_active`, `voltage_drop_active`)
    leben im `fault_state`-Sub-Block des Snapshots (ADR 0025 §2.2)
    und werden hier nach oben gehoben.

    Welle-6b-Review F2: gibt `None` zurueck, wenn der Snapshot pre-
    init ist (Pflicht-Feld fehlt) — Aufrufer silent-droppt das Device
    statt 500 zu werfen. SmartMeter und unbekannte Typen liefern
    `{}` (kein Power-State).
    """
    snap = device.snapshot()
    extractor = _STATE_EXTRACTORS.get(device_type)
    if extractor is None:
        # SmartMeter (kein eigener Power-State) + unbekannte Typen.
        return {}
    return extractor(snap)


def _extract_battery_state(
    snap: Mapping[str, object],
) -> dict[str, str | bool] | None:
    """Decision-21-Battery-Subset; gibt None bei pre-init (Pflicht-
    Feld fehlt)."""
    if "soc_kwh" not in snap or "current_power_kw" not in snap:
        return None
    return {
        "soc_kwh": _snap_decimal_str(snap, "soc_kwh"),
        "current_power_kw": _snap_decimal_str(snap, "current_power_kw"),
        "cell_failure_active": _snap_fault_flag(snap, "cell_failure_active"),
    }


def _extract_pv_or_load_state(
    snap: Mapping[str, object],
) -> dict[str, str | bool] | None:
    """Decision-21-PV/Load-Subset; gibt None bei pre-init."""
    if "current_power_kw" not in snap:
        return None
    return {"current_power_kw": _snap_decimal_str(snap, "current_power_kw")}


def _extract_grid_connection_state(
    snap: Mapping[str, object],
) -> dict[str, str | bool] | None:
    """Decision-21-GridConnection-Subset; gibt None bei pre-init."""
    if "current_power_kw" not in snap or "current_voltage_v" not in snap:
        return None
    return {
        "current_power_kw": _snap_decimal_str(snap, "current_power_kw"),
        "current_voltage_v": _snap_decimal_str(snap, "current_voltage_v"),
        "voltage_drop_active": _snap_fault_flag(snap, "voltage_drop_active"),
    }


# Welle-6b-Review F2 + Slice-Doc-Vorschlag „dispatch dict": per-typ
# Extractor analog `alarm_mappers.dispatch_alarm_mapper`. Welle-7+/M3-
# Geraete tragen sich hier ein, ohne `_extract_state_subset` weiter
# wachsen zu lassen.
_StateExtractor = Callable[[Mapping[str, object]], "dict[str, str | bool] | None"]
_STATE_EXTRACTORS: Mapping[str, _StateExtractor] = {
    "battery": _extract_battery_state,
    "pv": _extract_pv_or_load_state,
    "load": _extract_pv_or_load_state,
    "grid_connection": _extract_grid_connection_state,
}


def _snap_decimal_str(snap: Mapping[str, object], key: str) -> str:
    """Welle-6b (Decision 21 §3.1): liest ein numerisches Feld aus
    `device.snapshot()` und serialisiert es als String (canonical_
    json-Konsistenz; ADR 0021 §2.9). Aufrufer haben Pflicht-Feld-
    Existenz schon ueberprueft (`_extract_state_subset`).

    Welle-6b-Review F11: vorher hatte die Funktion zwei identische
    `str(value)`-Branches (eine 'Forward-Compat-Defense'-Branch fuer
    Nicht-Decimal-Werte). Beide Pfade waren gleich; die Branch ist
    raus. Wenn ein Welle-7+/M3-Geraet das Feld als float emittiert,
    bleibt `str(...)` monoton anwendbar — und das ist genau das, was
    der Test pinned (`str(Decimal('50.000')) == '50.000'`).
    """
    return str(snap[key])


def _snap_fault_flag(snap: Mapping[str, object], flag: str) -> bool:
    """Welle-6b (Decision 21 §3.1): liest ein Fault-Flag aus dem
    `fault_state`-Sub-Block (ADR 0025 §2.2 additiver Block).

    Defaultet zu `False` fuer Welle-1-Snapshots ohne Block.

    Welle-6b-Review F3: truthy-coerce statt strict-isinstance.
    Vorher hat `isinstance(raw, bool)` int(1) ausgeschlossen — ein
    JSON-roundtripped Snapshot mit `cell_failure_active=1` ist
    silent-False gewesen und hat einen aktiven Fault in der UI
    versteckt. Jetzt: `bool(raw)` macht aus jeder truthy nicht-
    leeren Repraesentation `True` (1, True, "true"-Strings) und aus
    jeder falsy `False`. Sicherheits-kritisches Signal geht nicht
    mehr durch eine Typ-Spitzfindigkeit verloren.
    """
    fault_state = snap.get("fault_state")
    if not isinstance(fault_state, Mapping):
        return False
    return bool(fault_state.get(flag, False))


@runs_router.get(
    "/runs/{run_id}/alarms-history",
    response_model=AlarmsResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run_alarms_history(
    run_id: str,
    request: Request,
    repository: Annotated[
        RunRepositoryPort,
        Depends(get_run_repository),
    ],
    limit: int = 50,
) -> AlarmsResponse:
    """Liefert die letzten `limit` Alarms aus dem `AlarmHistoryBuffer`
    (M5 Welle 4b, ADR 0040 Decision 17).

    Wird vom UI per HTMX-`hx-get` beim Page-Load fuer die
    Initial-Hydration aufgerufen; Live-Updates kommen via
    WS-`/alarms-stream`. Welle-4b-Default `limit=50`; max
    `200` durch Buffer-Capacity.

    Welle-4b-Review-Fix #7: `get_alarm_history_buffer` wird hier
    NACH `_resolve_repository(...)` aufgerufen — sonst feuert
    `_AlarmHistoryBufferNotConfiguredError` (500) bevor der
    404-Check fuer einen unbekannten `run_id` laufen kann. FastAPI
    `Depends` resolved sonst eagerly vor der Handler-Body-Logik.
    """
    _resolve_repository(run_id, repository)
    history_buffer = get_alarm_history_buffer(request)
    clamped_limit = min(max(limit, 0), 200)
    alarms = history_buffer.get_recent(run_id=run_id, limit=clamped_limit)
    return AlarmsResponse(
        run_id=run_id,
        alarms=[AlarmDto(**dataclasses.asdict(alarm)) for alarm in alarms],
    )
