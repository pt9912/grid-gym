"""Pydantic-Schemas fuer die M5-Welle-1-HTTP-API-Surface
(`GG-API-001..004`, ADR 0037).

Welle-1-Scope: Request-/Response-Bodies fuer die 5 REST-
Endpunkte aus
[`docs/plan/planning/in-progress/M5-welle-1.md §2`](../../../../../docs/plan/planning/in-progress/M5-welle-1.md):

- `GET /runs/{run_id}` → `RunDetailResponse`.
- `GET /runs/{run_id}/status` → `RunStatusResponse`.
- `POST /runs/{run_id}/control` → `ControlRequest` /
  `ControlResponse` (ADR 0037 Decision API-1).
- `GET /runs/{run_id}/snapshot` → `SnapshotResponse`.
- `POST /runs/{run_id}/faults` → `FaultInjectionRequest` /
  `FaultInjectionResponse`.

Plus `ErrorResponse` als standardisiertes Fehler-Format
(`GG-API-004`: `code`, `message`, `details`, `run_id`).

Welle-1-Anti-Scope: Stub-Schemas reflektieren die volle
Surface, aber Endpoint-Bodies (siehe `app.py`) sind Stubs.
Echte Wiring an `TickLoop`-Pause/Resume (Welle 4),
`TelemetrySinkPort` (M7-Welle-1a, ADR 0047) und `FaultPort`
(Welle 6) ist Folge-Welle-Material — die Schemas hier vermeiden
implementierungs-spezifische Felder, die spaeter brechen
koennten.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from grid_gym.hexagon.core.domain.alarm import AlarmSeverity, AlarmStatus
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.run import RunStatus


# ---------------------------------------------------------------------------
# Strict-Mode-Mixin fuer alle REST-Request-Bodies
# (ADR 0045 §2.1 / GG-SAFE-008).
# ---------------------------------------------------------------------------


class _BaseRequest(BaseModel):
    """Gemeinsame Strict-Mode-Basis fuer alle REST-Request-Bodies
    (ADR 0045 §2.1).

    - `strict=True` schaltet Pydantic-Type-Coercion ab: ein Body
      `{"seed": "42"}` wird mit `int_type`-Fehler abgelehnt statt
      silent zu `42` umgewandelt zu werden.
    - `extra="forbid"` macht unbekannte Felder zu 422-Fehlern statt
      sie silent zu verwerfen — Tippfehler im Client (`"actoin"`
      statt `"action"`) werden direkt diagnostiziert.

    Pflicht-Substanz fuer jeden FastAPI-Request-Body unter
    `src/grid_gym/adapters/driving/http_api/`. Per-Endpunkt-Bypass
    via `strict=False`/`extra="allow"` ist ADR-Bruch.
    """

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )


# ---------------------------------------------------------------------------
# POST /runs (konsolidiert nach _schemas.py per ADR 0045 §2.4)
# ---------------------------------------------------------------------------


class RunCreateRequest(_BaseRequest):
    """Eingehender Request fuer `POST /runs` (`GG-API-001`)."""

    scenario_hash: str = Field(
        description="SHA-256-Hash des kanonisierten Szenarios (siehe `GG-SCN-003/004`).",
        min_length=64,
        max_length=64,
    )
    seed: int = Field(
        description="`RandomPort`-Wurzelseed (`GG-SEED-001`).",
        ge=0,
        le=2**32 - 1,
    )
    tick_ms: int = Field(
        description="Schrittweite je Tick in ms (`GG-SIM-002`).",
        gt=0,
    )
    replay_of: str | None = Field(
        default=None,
        description=(
            "Optionale `run_id` eines Referenzlaufs: legt diesen Lauf als "
            "dessen Replay an (Trigger 039 / ADR 0068). `None` = regulaerer "
            "Lauf. Der Referenzlauf MUSS bereits existieren — sonst 422 "
            "`reference_run_not_found`."
        ),
    )


class RunCreateResponse(BaseModel):
    """Antwort von `POST /runs`.

    Erbt bewusst `BaseModel` (nicht `_BaseRequest`): per ADR 0045 §2.2
    sind `strict=True` und `extra="forbid"` nur Pflicht-Substanz fuer
    **Request-Bodies**. Response-Modelle bleiben in Default-Pydantic-
    Mode, damit spaetere Feld-Erweiterungen (z. B. neue Echo-Felder
    aus dem RunRepository) bestehende Snapshot-/Roundtrip-Tests nicht
    silent brechen. Dieselbe Begruendung gilt fuer alle uebrigen
    `*Response`-Klassen in dieser Datei.
    """

    run_id: str = Field(description="UUIDv4-Identitaet des angelegten Laufs.")
    scenario_hash: str = Field(description="Echo des `scenario_hash`-Eingangs.")
    seed: int = Field(description="Echo des `seed`-Eingangs.")
    tick_ms: int = Field(description="Echo des `tick_ms`-Eingangs.")
    replay_of: str | None = Field(
        default=None,
        description="Echo der `replay_of`-Referenz (`None` = kein Replay).",
    )


# ---------------------------------------------------------------------------
# POST /scenarios (Multi-Run-Execution S1, ADR 0069 §2.1)
# ---------------------------------------------------------------------------


class ScenarioCreateRequest(_BaseRequest):
    """Eingehender Request fuer `POST /scenarios` (Multi-Run-Execution S1,
    ADR 0069 §2.1)."""

    scenario_hash: str = Field(
        description="Erwarteter SHA-256-Hash des kanonisierten Szenarios (`GG-SCN-003`/`GG-SCN-004`).",
        min_length=64,
        max_length=64,
    )
    scenario: dict[str, object] = Field(
        description=(
            "Kanonischer Szenario-Body (`GG-SCN-001`). Numerische Decimal-Felder "
            "werden als Strings uebertragen (ADR 0069 §2.1 Variante A); `float` "
            "wird typisiert abgelehnt."
        ),
    )


class ScenarioCreateResponse(BaseModel):
    """Antwort von `POST /scenarios`."""

    scenario_hash: str = Field(
        description="Server-berechneter SHA-256-Hash (== Request-Hash) des abgelegten Szenarios.",
    )


# ---------------------------------------------------------------------------
# POST /runs/{run_id}/start (Multi-Run-Execution S3, ADR 0069 §2.4)
# ---------------------------------------------------------------------------


class RunStartResponse(BaseModel):
    """Antwort von `POST /runs/{run_id}/start`."""

    run_id: str = Field(description="UUIDv4-Identitaet des gestarteten Laufs.")
    status: str = Field(
        description=(
            "`accepted` — der Driver startet asynchron; der persistierte Lauf-"
            "Status (`GET /runs/{id}/status`) flippt `pending → running` beim "
            "ersten Tick."
        ),
    )


# ---------------------------------------------------------------------------
# GET /runs/{run_id}
# ---------------------------------------------------------------------------


class RunDetailResponse(BaseModel):
    """Vollstaendige Lauf-Metadaten-Antwort (`GG-API-001`)."""

    run_id: str = Field(description="UUIDv4-Identitaet des Laufs.")
    scenario_hash: str = Field(description="SHA-256-Hash des kanonisierten Szenarios.")
    schema_version: str = Field(description="`RunMetadata.schema_version`.")
    seed: int = Field(description="`RandomPort`-Wurzelseed.")
    tick_ms: int = Field(description="Schrittweite je Tick in ms.")
    started_at: str = Field(description="ISO-8601-Start-Timestamp (leer wenn nicht gestartet).")
    ended_at: str = Field(description="ISO-8601-End-Timestamp (leer wenn aktiv).")
    tool_version: str = Field(description="`pyproject.toml`-Tool-Version zum Lauf-Start.")
    replay_of: str | None = Field(
        default=None,
        description="Referenzlauf, dessen Replay dieser Lauf ist (`None` = kein Replay).",
    )


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/status
# ---------------------------------------------------------------------------


RunState = RunStatus
"""Welle-1-Alias auf den Domain-`RunStatus`-Literal (M5 Welle 4a,
ADR 0039 Decision 12). Werte: ``pending``/``running``/``paused``/
``stopped``/``completed``. Domain owns the type — der Schema-
Layer re-exportiert nur, damit Pydantic-Modelle ohne Cross-Layer-
Import konsumieren koennen.
"""


class RunStatusResponse(BaseModel):
    """Kompakter Run-Status (`GG-API-001`).

    Welle-4a (ADR 0039 Decision 14): `state` reflektiert den
    persistierten `RunStatus` aus dem RunRepository; `tick_count`
    und `simulation_time` kommen aus dem aktiven `TickLoop`
    (Welle-4a-Demo-Single-Run-Setup; produktive Multi-Run-
    Variante folgt mit Welle 5). Wenn kein `TickLoop` registriert
    ist (Welle-1-Stub-Pfad fuer reine Repository-only-Runs),
    bleiben beide Felder ``0``.
    """

    run_id: str = Field(description="UUIDv4-Identitaet des Laufs.")
    state: RunState = Field(
        description="Lauf-Zustand (`pending`/`running`/`paused`/`stopped`/`completed`)."
    )
    simulation_time: int = Field(
        description="Aktuelle Simulationszeit in ms (0 wenn kein aktiver TickLoop).",
        ge=0,
    )
    tick_count: int = Field(
        description="Anzahl abgearbeiteter Ticks (0 wenn kein aktiver TickLoop).",
        ge=0,
    )


# ---------------------------------------------------------------------------
# POST /runs/{run_id}/control
# (ADR 0037 Decision API-1: Action-Body statt Action-Pfad)
# ---------------------------------------------------------------------------


ControlAction = Literal["pause", "resume", "stop"]


class ControlRequest(_BaseRequest):
    """Steuerungs-Action fuer einen Lauf (ADR 0037 Decision API-1).

    Action-Set: `pause` / `resume` / `stop`. Erweiterungen
    (z. B. `restart`, `replay-step`) erfolgen per Literal-
    Erweiterung; keine neuen Endpunkte noetig.

    Strict-Mode + extra-forbid (ADR 0045 §2.1) per `_BaseRequest`.
    """

    action: ControlAction = Field(description="Steuerungs-Action.")


class ControlResponse(BaseModel):
    """Antwort auf `POST /runs/{run_id}/control` (Welle-1-Stub:
    immer `accepted=True`; echtes TickLoop-Wiring in Welle 4)."""

    run_id: str = Field(description="UUIDv4-Identitaet des Laufs.")
    action: ControlAction = Field(description="Echo der angefragten Action.")
    accepted: bool = Field(
        description="True wenn der TickLoop die Action akzeptiert hat (Welle-1-Stub: immer True).",
    )


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/snapshot
# ---------------------------------------------------------------------------


class SnapshotResponse(BaseModel):
    """Snapshot-Export-Antwort (Welle-1-Stub).

    Welle-1-Stub gibt nur einen `schema_ref`-Pointer zurueck
    (keine echten Snapshot-Daten). Welle 4/5 bringt die volle
    `SnapshotEnvelope`-Serialisierung.
    """

    run_id: str = Field(description="UUIDv4-Identitaet des Laufs.")
    schema_ref: str = Field(
        description="Verweis auf das aktuelle Snapshot-Envelope-Schema (`ADR 0015` v2).",
    )


# ---------------------------------------------------------------------------
# POST /runs/{run_id}/faults
# ---------------------------------------------------------------------------


class FaultInjectionRequest(_BaseRequest):
    """Fault-Injection-Anfrage (Welle-1-Stub-Schema; echte
    `FaultPort`-Wiring in Welle 6).

    Strict-Mode + extra-forbid (ADR 0045 §2.1) per `_BaseRequest`.
    """

    fault_type: str = Field(
        description="Fault-Typ-Identifier (z. B. `cell_failure`, `voltage_drop`).",
        min_length=1,
    )
    target: str = Field(
        description="Ziel-Device-ID, an dem der Fault wirkt.",
        min_length=1,
    )
    start_at_tick: int = Field(
        description="Tick-Index, ab dem der Fault aktiv wird.",
        ge=0,
    )
    duration_ticks: int = Field(
        description="Fault-Dauer in Ticks (0 = unendlich bis Recovery).",
        ge=0,
    )
    recovery: str = Field(
        description="Recovery-Verhalten (`auto-recover-after-N-ticks` oder `manual-via-command`).",
        min_length=1,
    )


class FaultInjectionResponse(BaseModel):
    """Antwort auf `POST /runs/{run_id}/faults` (Welle-1-Stub:
    Fault-ID + Echo; kein `FaultPort.activate`-Call)."""

    run_id: str = Field(description="UUIDv4-Identitaet des Laufs.")
    fault_id: str = Field(description="UUIDv4-Identitaet des erzeugten Fault-Eintrags.")
    accepted: bool = Field(
        description="True wenn der Fault registriert wurde (Welle-1-Stub: immer True).",
    )


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/alarms (M5 Welle 4b, ADR 0040 Decision 17)
# ---------------------------------------------------------------------------


class AlarmDto(BaseModel):
    """Pydantic-DTO fuer den Unified `Alarm`-Domain-Type
    (`GG-UI-005`-6-Spalten-UI-Akzeptanz: Zeit/Ziel/Schweregrad/
    Code/Nachricht/Status; plus `alarm_id`/`run_id`/`fault_id`-
    Felder fuer kanonisches 9-Feld-Schema)."""

    alarm_id: str = Field(description="UUIDv4-Identitaet des Alarms.")
    run_id: str = Field(description="UUIDv4-Identitaet des Laufs.")
    simulation_time_ms: int = Field(
        description="Tick-Zeitpunkt in ms (ab Lauf-Start).",
        ge=0,
    )
    target: str = Field(description="Ziel-Geraete-ID.")
    code: str = Field(description="Stabile Fehler-ID (z. B. `power_clamp_limited`).")
    severity: AlarmSeverity = Field(
        description="Schweregrad-Hierarchie (`info`/`warning`/`critical`)."
    )
    message: str = Field(description="Mensch-lesbare Beschreibung.")
    status: AlarmStatus = Field(description="Lifecycle-Status (Welle-4b: immer `active`).")
    fault_id: str | None = Field(
        default=None,
        description="Optional; Welle-4b immer `None` (Fault-Injection-Mapping Welle 6+/M6).",
    )


class AlarmsResponse(BaseModel):
    """Antwort auf `GET /runs/{run_id}/alarms`. Neueste zuerst
    (LIFO der internen Ring-Buffer-deque)."""

    run_id: str = Field(description="UUIDv4-Identitaet des Laufs.")
    alarms: list[AlarmDto] = Field(
        description="Liste der letzten Alarms; neueste zuerst.",
    )


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/devices (M5 Welle 6b, Decision 21)
# ---------------------------------------------------------------------------


class DeviceStateEntry(BaseModel):
    """Per-Device-Entry der `DevicesResponse` (M5 Welle 6b, Decision 21).

    `state` ist ein flaches Mapping mit dem Welle-6b-Pflicht-Subset
    pro Device-Typ (Decision 21 §3.1):

    - `battery`: `soc_kwh`, `current_power_kw`, `cell_failure_active`.
    - `pv` / `load`: `current_power_kw`.
    - `grid_connection`: `current_power_kw`, `current_voltage_v`,
      `voltage_drop_active`.
    - `smart_meter`: `{}` (kein eigener State).

    `Decimal`-Werte werden vom Endpoint VOR der Pydantic-Konstruktion
    via `str(...)` serialisiert (canonical_json-Konsistenz; ADR 0021
    §2.9 + Welle-3-`TelemetryPoint.value`-Pattern). Bool-Flags bleiben
    `bool`. `quality` ist die worst-case `Quality` aller Telemetrie-
    Punkte des letzten Tick (Decision 21; Pre-First-Tick → `VALID`).
    """

    device_id: str = Field(description="Device-ID aus dem Run-Scenario.")
    device_type: str = Field(
        description=("Device-Typ-Segment (`battery`/`pv`/`load`/`grid_connection`/`smart_meter`)."),
    )
    state: dict[str, str | bool] = Field(
        description="Welle-6b-Pflicht-Subset pro Device-Typ (Decision 21 §3.1).",
    )
    quality: Quality = Field(
        description=(
            "Worst-case `Quality` der letzten `device.telemetry()`-Sequenz; "
            "`VALID` bei leerer Telemetrie (Pre-First-Tick)."
        ),
    )


class DevicesResponse(BaseModel):
    """Antwort auf `GET /runs/{run_id}/devices` (M5 Welle 6b,
    Decision 21; `GG-UI-006`).

    Liste aller im aktiven TickLoop registrierten Devices mit
    State-Subset + Quality-Marker. Reihenfolge spiegelt die
    Konstruktor-/Tick-Iteration-Reihenfolge (deterministisch).
    Ohne aktiven TickLoop (Welle-1-Stub-Pfad fuer rein
    persistierte Runs) bleibt `devices` leer.
    """

    run_id: str = Field(description="UUIDv4-Identitaet des Laufs.")
    devices: list[DeviceStateEntry] = Field(
        description="Geraete-Eintraege in TickLoop-Iteration-Reihenfolge.",
    )


# ---------------------------------------------------------------------------
# GET /ready (M6 Welle 6, GG-DEPLOY-006 — Three-State-Readiness)
# ---------------------------------------------------------------------------


ComponentState = Literal["healthy", "degraded", "unhealthy"]
"""Three-State-Health-Domaene fuer den `/ready`-Endpoint (M6 Welle 6,
`GG-DEPLOY-006`, Lastenheft Z. 1876-1879).

- ``healthy``: Komponente voll erreichbar.
- ``degraded``: Komponente eingeschraenkt, aber nicht ausgefallen
  (z. B. `simulation`-Service als `sleep infinity`-Compose-Stub oder
  TickLoop mit `backpressure_status == "delayed"`).
- ``unhealthy``: Komponente ausgefallen (z. B. Postgres nicht
  erreichbar). Aggregiert auf HTTP-503 (Kubernetes-Readiness-
  Konvention).
"""


class ComponentStatus(BaseModel):
    """Per-Komponente-Status-Eintrag der `ReadyResponse` (M6 Welle 6,
    Welle-6-D-2). Three-State plus optionaler Ursachen-String pro
    Dienst — der Lastenheft-Z.-1876-Wortlaut „mit kurzer Ursache".

    Erbt `BaseModel` (kein `_BaseRequest`): Response-Model, ADR 0045
    §2.2 (Strict-Mode ist Request-Body-Pflicht).
    """

    state: ComponentState = Field(
        description="Three-State-Health der Komponente (`healthy`/`degraded`/`unhealthy`).",
    )
    reason: str | None = Field(
        default=None,
        description="Kurze Ursache bei `degraded`/`unhealthy`; `None` bei `healthy`.",
    )


class ReadyResponse(BaseModel):
    """Antwort des `/ready`-Endpoints (M6 Welle 6, `GG-DEPLOY-006`).

    `status` ist die aggregierte Top-Level-Health ueber die vier
    Lastenheft-Pflicht-Komponenten (`api`/`ui`/`db`/`simulation`):
    jede `unhealthy` → `unhealthy`; sonst eine `degraded` →
    `degraded`; sonst `healthy` (Welle-6-D-2 Aggregations-Regel).
    HTTP-Status-Mapping (im Endpoint-Handler): `200` bei
    `healthy`/`degraded`, `503` bei `unhealthy`.
    """

    status: ComponentState = Field(
        description="Aggregierter Top-Level-Readiness-Status.",
    )
    components: dict[str, ComponentStatus] = Field(
        description="Per-Komponente-Breakdown (`api`/`ui`/`db`/`simulation`).",
    )


# ---------------------------------------------------------------------------
# Standardisiertes Fehler-Format (GG-API-004)
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Standardisiertes Fehler-Format (`GG-API-004`).

    Pflicht-Felder: `code` (stabile Fehler-ID), `message`
    (menschen-lesbar), `details` (strukturierte Extension),
    `run_id` (falls Endpoint run-bezogen ist).
    """

    code: str = Field(description="Stabile Fehler-ID (z. B. `run_not_found`, `invalid_action`).")
    message: str = Field(description="Menschen-lesbare Fehler-Nachricht.")
    details: dict[str, object] | None = Field(
        default=None,
        description="Strukturierte Detail-Daten zum Fehler (Validation-Errors, Field-Refs, ...).",
    )
    run_id: str | None = Field(
        default=None,
        description="UUIDv4-Identitaet des Laufs (falls Endpoint run-bezogen ist).",
    )
