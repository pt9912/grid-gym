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
`TelemetrySinkPort` (Welle 3) und `FaultPort` (Welle 6)
ist Folge-Welle-Material — die Schemas hier vermeiden
implementierungs-spezifische Felder, die spaeter brechen
koennten.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


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


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/status
# ---------------------------------------------------------------------------


RunState = Literal["pending", "running", "paused", "stopped", "completed"]


class RunStatusResponse(BaseModel):
    """Kompakter Run-Status (`GG-API-001`).

    Welle-1-Stub-Felder: `simulation_time` und `tick_count`
    sind in Welle 1 immer `0` (kein TickLoop-Wiring); Welle 4
    bringt die echte Werte.
    """

    run_id: str = Field(description="UUIDv4-Identitaet des Laufs.")
    state: RunState = Field(
        description="Lauf-Zustand (`pending`/`running`/`paused`/`stopped`/`completed`)."
    )
    simulation_time: int = Field(
        description="Aktuelle Simulationszeit in ms (Welle-1-Stub: 0).",
        ge=0,
    )
    tick_count: int = Field(
        description="Anzahl abgearbeiteter Ticks (Welle-1-Stub: 0).",
        ge=0,
    )


# ---------------------------------------------------------------------------
# POST /runs/{run_id}/control
# (ADR 0037 Decision API-1: Action-Body statt Action-Pfad)
# ---------------------------------------------------------------------------


ControlAction = Literal["pause", "resume", "stop"]


class ControlRequest(BaseModel):
    """Steuerungs-Action fuer einen Lauf (ADR 0037 Decision API-1).

    Action-Set: `pause` / `resume` / `stop`. Erweiterungen
    (z. B. `restart`, `replay-step`) erfolgen per Literal-
    Erweiterung; keine neuen Endpunkte noetig.
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


class FaultInjectionRequest(BaseModel):
    """Fault-Injection-Anfrage (Welle-1-Stub-Schema; echte
    `FaultPort`-Wiring in Welle 6)."""

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
