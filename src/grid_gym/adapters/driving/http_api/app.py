"""FastAPI-`app` fuer das HTTP-Driving-Interface (M1 Welle 6a).

Endpoints (Welle-6a-Scope, Welle-6b liefert Persistenz):
- `GET  /health`  — Liveness-Probe (`HEALTHCHECK` im Dockerfile).
- `POST /runs`    — `GG-API-001`-Stub: nimmt minimalen Body
  (`scenario_hash`, `seed`, `tick_ms`) und liefert eine
  `run_id`. M1-Welle-6a hat noch keine Persistenz — die `run_id`
  ist `uuid4`-generiert, die Run-Metadaten werden NICHT
  persistiert. Welle 6b haengt den `RunRepositoryPort` an.
- `GET  /openapi.json` — automatisch von FastAPI generiert
  (`GG-QG-006`/`GG-API-003`).

Die Title-/Version-/Description-Felder fliessen in die generierte
OpenAPI-Definition, die der `openapi-validate`-Stage prueft.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Final

from fastapi import FastAPI
from pydantic import BaseModel, Field

_APP_TITLE: Final[str] = "grid-gym HTTP API"
_APP_VERSION: Final[str] = "0.1.0"
_APP_DESCRIPTION: Final[str] = (
    "Driving-Adapter fuer den `grid-gym`-Simulationskern (M1 Welle 6a). "
    "Liefert `/health` als Liveness-Probe und `/runs` als Stub-Endpoint "
    "fuer Lauf-Erzeugung. Persistenz folgt in Welle 6b."
)


class HealthResponse(BaseModel):
    """Antwort des `/health`-Endpoints (Liveness-Probe)."""

    status: str = Field(description="Immer 'ok' bei laufender App.")


class RunCreateRequest(BaseModel):
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


class RunCreateResponse(BaseModel):
    """Antwort von `POST /runs`."""

    run_id: str = Field(description="UUIDv4-Identitaet des angelegten Laufs.")
    scenario_hash: str = Field(description="Echo des `scenario_hash`-Eingangs.")
    seed: int = Field(description="Echo des `seed`-Eingangs.")
    tick_ms: int = Field(description="Echo des `tick_ms`-Eingangs.")


app: Final[FastAPI] = FastAPI(
    title=_APP_TITLE,
    version=_APP_VERSION,
    description=_APP_DESCRIPTION,
)


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def get_health() -> HealthResponse:
    """Liveness-Probe.

    Antwortet immer mit `{"status": "ok"}`, solange der Prozess
    laeuft. Persistente Backend-Checks (Postgres-Erreichbarkeit
    etc.) kommen mit Welle 6b als `/ready`-Endpoint dazu.
    """
    return HealthResponse(status="ok")


@app.post(
    "/runs",
    response_model=RunCreateResponse,
    status_code=201,
    tags=["runs"],
)
def post_runs(
    request: Annotated[RunCreateRequest, ...],
) -> RunCreateResponse:
    """Legt einen neuen Lauf an (`GG-API-001`-Stub).

    Welle 6a generiert nur eine `run_id` per `uuid4` und echot die
    Eingangs-Felder. Welle 6b haengt den `RunRepositoryPort` an und
    persistiert in Postgres.
    """
    run_id = str(uuid.uuid4())
    return RunCreateResponse(
        run_id=run_id,
        scenario_hash=request.scenario_hash,
        seed=request.seed,
        tick_ms=request.tick_ms,
    )
