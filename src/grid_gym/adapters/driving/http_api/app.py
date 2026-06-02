"""FastAPI-`app` fuer das HTTP-Driving-Interface (M1 Welle 6a/6b
+ M5 Welle 1/2/3/4a).

Endpoints (M1 Welle 6a/6b):

- `GET  /health`  — Liveness-Probe (`HEALTHCHECK` im Dockerfile).
- `POST /runs`    — `GG-API-001`: persistiert einen neuen Lauf via
  `RunRepositoryPort` (Welle 6b).
- `GET  /openapi.json` — automatisch von FastAPI generiert
  (`GG-QG-006`/`GG-API-003`).

Endpoints (M5 Welle 1/4a, ADR 0037 + 0039):

- `GET  /runs/{run_id}`         — Run-Detail (`GG-API-001`).
- `GET  /runs/{run_id}/status`  — Kompakter Run-Status (Welle-4a
  produktiv mit RunStatus + TickLoop-Counter).
- `POST /runs/{run_id}/control` — Steuerung mit Action-Body
  (`pause`/`resume`/`stop`; ADR 0037 Decision API-1; Welle-4a-
  Wiring auf TickLoop-Control-Surface per ADR 0039 Decision 13).
- `GET  /runs/{run_id}/snapshot`— Snapshot-Export (Stub).
- `POST /runs/{run_id}/faults`  — Fault-Injection (Stub).
- `WS   /runs/{run_id}/telemetry` — Live-Telemetry-Stream
  (`GG-API-002`; Welle-3 Subscribe-Pattern auf
  `TelemetryStreamPort`, ADR 0038).

Endpoints + Mounts (M5 Welle 2/3/4a, ADR 0036 + 0039):

- `GET  /`               — Demo-Hello-Page (UI-Adapter).
- `GET  /ui/health`      — Healthcheck-UI-Seite mit HTMX-Partial-
  Refresh-Pfad.
- `GET  /runs/{run_id}/dashboard` — Live-Telemetry-Dashboard
  (Welle 3, ADR 0038).
- `GET  /runs/{run_id}/control`   — Replay-Controls-Page (Welle
  4a, ADR 0039 Decision 14; HTMX-Polling auf `GET /status`).
- `MOUNT /static/*`      — StaticFiles-Mount fuer vendored HTMX +
  Chart.js + CSS unter `adapters/driving/ui/static/`.

Welle-1-Anti-Scope-Erbschaft (jetzt teilweise aufgeloest durch
Welle 4a): `POST /faults` bleibt Welle-6-Material.

Port-Injektion: `app.state` haelt die Adapter-Instanzen
(`run_repository`, `telemetry_stream`, `tick_loop_registry`).
Aufrufer (uvicorn-Entry, Tests) setzen sie vor der ersten
Anfrage; die Dependency-Provider in `_dependencies.py` +
`_tick_loop_registry.py` lesen aus dem State.

Welle-4a-Lifespan: wenn ein `demo_tick_loop_driver` auf
`app.state` gesetzt ist, startet er beim App-Startup als
asyncio-Task und wird beim Shutdown sauber gecanceled. Tests
ohne demo Driver bekommen einen no-op Lifespan (Welle-3-Pattern).

Standardisiertes Fehler-Format (`GG-API-004`): siehe
`_schemas.ErrorResponse` mit `code`/`message`/`details`/
`run_id`. 404-Antworten fuer nicht-existente Runs nutzen
das Format; Welle 4a ergaenzt 409 (Invalid-Transition) und 503
(TickLoop-not-active) auf `POST /control`.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Final

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from grid_gym.adapters.driven.telemetry_stream_inmemory import (
    DemoTelemetryGenerator,
    InMemoryTelemetryStream,
)
from grid_gym.adapters.driving.http_api._dependencies import (
    _RunRepositoryNotConfiguredError,
    _TelemetryStreamNotConfiguredError,
    get_run_repository,
    get_telemetry_stream,
)
from grid_gym.adapters.driving.http_api._tick_loop_driver import (
    DemoTickLoopDriver,
)
from grid_gym.adapters.driving.http_api._tick_loop_registry import (
    TickLoopRegistry,
    _TickLoopRegistryNotConfiguredError,
)
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort
from grid_gym.hexagon.ports.driving.telemetry_stream import TelemetryStreamPort

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


@asynccontextmanager
async def _lifespan(app_: FastAPI) -> AsyncIterator[None]:
    """FastAPI-Lifespan: startet/stoppt Welle-3-Demo-Generator und
    Welle-4a-Demo-TickLoop-Driver, sofern konfiguriert.

    Welle 3 (ADR 0038 §3.1): `DemoTelemetryGenerator`-Singleton +
    `InMemoryTelemetryStream` werden via
    `configure_telemetry_stream(stream, demo_generator=...)`
    gesetzt; der Generator startet hier seinen periodischen
    Producer-Task.

    Welle 4a (ADR 0039 Decision 13): wenn ein
    `DemoTickLoopDriver` ueber `configure_demo_run(...)` auf
    `app.state` gelegt wurde, startet er hier seinen asyncio-
    Driver-Task; bei Shutdown sauberes Cancel + RunStatus →
    `completed` Update durch den ``stop()``-Pfad des Drivers.

    Tests ohne die jeweiligen Demo-Komponenten bekommen einen
    no-op Lifespan.
    """
    generator = getattr(app_.state, "demo_telemetry_generator", None)
    stream = getattr(app_.state, "telemetry_stream", None)
    if isinstance(generator, DemoTelemetryGenerator) and isinstance(
        stream, InMemoryTelemetryStream
    ):
        generator.start(stream)
    driver = getattr(app_.state, "demo_tick_loop_driver", None)
    if isinstance(driver, DemoTickLoopDriver):
        driver.start()
    try:
        yield
    finally:
        if isinstance(driver, DemoTickLoopDriver):
            await driver.stop()
        if isinstance(generator, DemoTelemetryGenerator):
            await generator.stop()


app: Final[FastAPI] = FastAPI(
    title=_APP_TITLE,
    version=_APP_VERSION,
    description=_APP_DESCRIPTION,
    lifespan=_lifespan,
)


def configure_run_repository(repository: RunRepositoryPort) -> None:
    """Setzt das Run-Repository fuer die laufende App.

    Aufrufer (uvicorn-Entry in Welle 6c, Tests) injizieren die
    Implementation vor dem ersten Request. Die Funktion ist
    bewusst global — `app.state` ist die einzige FastAPI-eigene
    Persistenz-Schicht ueber Request-Grenzen hinweg.
    """
    app.state.run_repository = repository


def configure_telemetry_stream(
    stream: TelemetryStreamPort,
    *,
    demo_generator: DemoTelemetryGenerator | None = None,
) -> None:
    """Setzt den Telemetry-Stream + optional einen Demo-Generator
    fuer die laufende App (M5 Welle 3, ADR 0038).

    ``demo_generator`` ist optional: wenn gesetzt **und** der
    Stream eine ``InMemoryTelemetryStream``-Instanz ist, startet
    der FastAPI-Lifespan-Hook den Generator als Background-Task
    (Welle-3-Demo-Producer). Tests koennen den Generator
    weglassen oder den Stream direkt mit synthetischen Points
    fuettern.
    """
    app.state.telemetry_stream = stream
    if demo_generator is not None:
        app.state.demo_telemetry_generator = demo_generator


def configure_tick_loop_registry(registry: TickLoopRegistry) -> None:
    """Setzt die `TickLoopRegistry` fuer die laufende App (M5 Welle
    4a, ADR 0039 Decision 13).

    Aufrufer (uvicorn-Entry, Tests, ``_demo_setup.configure_demo_run``)
    injizieren die Registry vor dem ersten Request. Endpunkte
    `POST /control` + `GET /status` lesen aus der Registry, um
    den passenden `TickLoop` zu finden.
    """
    app.state.tick_loop_registry = registry


# Re-export fuer Backward-Compat (Welle-6b-Tests + uvicorn-Entry-
# Module nutzen `from .app import get_run_repository`).
__all__ = (
    "_APP_VERSION",
    "_RunRepositoryNotConfiguredError",
    "_TelemetryStreamNotConfiguredError",
    "_TickLoopRegistryNotConfiguredError",
    "app",
    "configure_run_repository",
    "configure_telemetry_stream",
    "configure_tick_loop_registry",
    "get_run_repository",
    "get_telemetry_stream",
)


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


# ---------------------------------------------------------------------------
# M5 Welle 1 — APIRouter-Mounts (ADR 0037)
# ---------------------------------------------------------------------------
#
# Welle-1-Endpunkte sind ueber zwei Router-Module verteilt
# (siehe `_runs_router.py` + `_runs_action_router.py`), damit
# der `AC-NO-GOD-UTILS`-Contract (max 5 public top-level
# functions pro Modul) eingehalten wird.

from grid_gym.adapters.driving.http_api._runs_action_router import (
    runs_action_router,
)
from grid_gym.adapters.driving.http_api._runs_router import runs_router

app.include_router(runs_router)
app.include_router(runs_action_router)

# ---------------------------------------------------------------------------
# M5 Welle 2 — UI-Adapter-Mount (ADR 0036)
# ---------------------------------------------------------------------------
#
# Vendored Static-Assets (HTMX 2.0.9 + Chart.js 4.5.1) unter
# `adapters/driving/ui/static/` werden via `StaticFiles` an
# `/static/*` gemountet. Welle-2-Anti-Scope: kein Live-Telemetry
# (Welle 3), keine Replay-Controls (Welle 4).
from pathlib import Path

from fastapi.staticfiles import StaticFiles

from grid_gym.adapters.driving.ui.routes import ui_router

_UI_STATIC_DIR: Final[Path] = Path(__file__).parent.parent / "ui" / "static"
app.mount("/static", StaticFiles(directory=str(_UI_STATIC_DIR)), name="static")
app.include_router(ui_router)
