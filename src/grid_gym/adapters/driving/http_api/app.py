"""FastAPI-`app` fuer das HTTP-Driving-Interface (M1 Welle 6a/6b).

Endpoints:
- `GET  /health`  — Liveness-Probe (`HEALTHCHECK` im Dockerfile).
- `POST /runs`    — `GG-API-001`: persistiert einen neuen Lauf via
  `RunRepositoryPort` (Welle 6b). Welle 6c haengt
  `PostgresRunRepository` als Production-Implementation an;
  Welle-6a/6b nutzt die `InMemoryRunRepository` aus
  `tests/unit/hexagon/ports/driven/_fakes.py` als Default.
- `GET  /openapi.json` — automatisch von FastAPI generiert
  (`GG-QG-006`/`GG-API-003`).

Port-Injektion: `app.state.run_repository` haelt die
`RunRepositoryPort`-Instanz. Aufrufer (uvicorn-Entry, Tests)
setzen das vor der ersten Anfrage; `get_run_repository`-Dependency
liest aus dem State. Standard-Fallback (`set_default_run_
repository_for_local_use`) bleibt fuer M1-Welle-6a/b in-process
in Kraft, bis Welle 6c einen Postgres-Adapter konfiguriert.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Final

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel, Field
from typing import cast

from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort

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


def configure_run_repository(repository: RunRepositoryPort) -> None:
    """Setzt das Run-Repository fuer die laufende App.

    Aufrufer (uvicorn-Entry in Welle 6c, Tests) injizieren die
    Implementation vor dem ersten Request. Die Funktion ist
    bewusst global — `app.state` ist die einzige FastAPI-eigene
    Persistenz-Schicht ueber Request-Grenzen hinweg.
    """
    app.state.run_repository = repository


def get_run_repository(request: Request) -> RunRepositoryPort:
    """Dependency-Provider fuer `RunRepositoryPort`.

    Wirft `RuntimeError`, wenn die App nicht konfiguriert ist —
    Endpoints muessen vor dem ersten Aufruf
    `configure_run_repository` durchlaufen haben. Verhindert,
    dass ein nicht konfigurierter Welle-6-Stand stillschweigend
    nichts persistiert.
    """
    repository = getattr(request.app.state, "run_repository", None)
    if repository is None:
        raise RuntimeError(  # noqa: TRY003 — Konfigurations-Fehler, kein Domain-Fehler
            "RunRepositoryPort is not configured. Call "
            "grid_gym.adapters.driving.http_api.app.configure_run_repository "
            "before serving requests."
        )
    return cast(RunRepositoryPort, repository)


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def get_health() -> HealthResponse:
    """Liveness-Probe.

    Antwortet immer mit `{"status": "ok"}`, solange der Prozess
    laeuft. Persistente Backend-Checks (Postgres-Erreichbarkeit
    etc.) kommen mit Welle 6c als `/ready`-Endpoint dazu.
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
    repository: Annotated[RunRepositoryPort, Depends(get_run_repository)],
) -> RunCreateResponse:
    """Legt einen neuen Lauf an (`GG-API-001`).

    Welle 6b: persistiert die `RunMetadata` ueber den
    `RunRepositoryPort`. Welle 6c bringt
    `PostgresRunRepository` + alembic-Migration; bis dahin
    laeuft der Endpoint gegen die In-Memory-Test-Variante.
    """
    run_id = str(uuid.uuid4())
    metadata = RunMetadata(
        run_id=run_id,
        scenario_hash=request.scenario_hash,
        schema_version="grid-gym.scenario.v1",
        seed=request.seed,
        tick_ms=request.tick_ms,
        started_at="",
        ended_at="",
        tool_version=_APP_VERSION,
    )
    repository.save(metadata)
    return RunCreateResponse(
        run_id=run_id,
        scenario_hash=request.scenario_hash,
        seed=request.seed,
        tick_ms=request.tick_ms,
    )
