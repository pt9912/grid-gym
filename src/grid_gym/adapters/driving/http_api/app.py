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

import os
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Final

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from grid_gym.adapters.driven.alarm_stream_inmemory import (
    AlarmHistoryBuffer,
    InMemoryAlarmStream,
)
from grid_gym.adapters.driven.persistence_inmemory import InMemoryRunRepository
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
from grid_gym.adapters.driving.http_api._run_driver_registry import (
    RunDriverRegistry,
)
from grid_gym.adapters.driving.http_api._schemas import (
    ErrorResponse,
    RunCreateRequest,
    RunCreateResponse,
)
from grid_gym.adapters.driving.http_api._tick_loop_driver import (
    DemoTickLoopDriver,
)
from grid_gym.adapters.driving.http_api._run_execution_profile import (
    get_run_execution_profile,
)
from grid_gym.adapters.driving.http_api._tick_loop_registry import (
    TickLoopRegistry,
    _TickLoopRegistryNotConfiguredError,
)
from grid_gym.hexagon.core.domain.run import SIM_START_TIME_ORIGIN, RunMetadata
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort
from grid_gym.hexagon.ports.driving.telemetry_stream import TelemetryStreamPort

_APP_TITLE: Final[str] = "grid-gym HTTP API"
_APP_VERSION: Final[str] = "0.1.0"
_APP_DESCRIPTION: Final[str] = (
    "HTTP-Driving-Adapter fuer den `grid-gym`-Simulationskern. "
    "**Simulation only — not approved for production grid control "
    "(`GG-SAFE-007`, `GG-NONGOAL-001`).** "
    "Liefert REST-Endpunkte (`/runs`, `/health`, ...) sowie "
    "WebSocket-Streams fuer Telemetry und Alarme. Eingabe-Validation "
    'an REST-Request-Bodies ist Pydantic-Strict-Mode + `extra="forbid"` '
    "(`GG-SAFE-008`, ADR 0045)."
)

_DEMO_SCENARIO_ENV_VAR: Final[str] = "GRID_GYM_DEMO_SCENARIO_PATH"


class _DemoScenarioPathNotFoundError(FileNotFoundError):
    """Welle-5-Review F5: env-var `GRID_GYM_DEMO_SCENARIO_PATH`
    zeigt auf eine nicht-existente Datei (Tippfehler oder fehlender
    Volume-Mount). Fail-fast mit klarer Diagnose statt bare
    `FileNotFoundError` aus `path.read_text()` mitten im YAML-
    Loader."""

    def __init__(self, path_str: str) -> None:
        super().__init__(
            f"Demo scenario YAML not found at GRID_GYM_DEMO_SCENARIO_PATH="
            f"{path_str!r}. Check the env-var (typo?), the deploy/scenarios/"
            "volume-mount in compose.yml, or pass --scenario explicitly via "
            "`python -m grid_gym demo`."
        )


ScenarioConfigurator = Callable[[FastAPI, Path], None]
"""Signatur des Scenario-Demo-Setups (`configure_scenario_demo_run`). Per
`_register_scenario_configurator` aus dem Composition-Root
(`grid_gym.composition.asgi`) injiziert — `app.py` importiert das
Scenario-Bootstrap (`composition._demo_scenario_setup`) nicht mehr direkt,
sonst entstuende die indirekte Kette Adapter → composition →
`core.scenario`/`core.faults` (`AC-ADAPTER-PURE`, 041-C3b)."""


class _ScenarioConfiguratorNotRegisteredError(RuntimeError):
    """`GRID_GYM_DEMO_SCENARIO_PATH` gesetzt, aber kein Scenario-
    Konfigurator registriert: die App lief ueber den reinen Adapter-
    Entrypoint statt `grid_gym.composition.asgi:app` (041-C3b)."""

    def __init__(self, path_str: str) -> None:
        super().__init__(
            f"GRID_GYM_DEMO_SCENARIO_PATH={path_str!r} is set but no scenario "
            "configurator is registered. Start the app via the composition "
            "entrypoint `grid_gym.composition.asgi:app`, not the bare adapter "
            "`grid_gym.adapters.driving.http_api:app`."
        )


def _raise_scenario_configurator_unregistered(_app: FastAPI, scenario_path: Path) -> None:
    """Fail-closed Default-Konfigurator — aktiv, solange der
    Composition-Root keinen registriert hat."""
    raise _ScenarioConfiguratorNotRegisteredError(str(scenario_path))


_scenario_configurator: ScenarioConfigurator = _raise_scenario_configurator_unregistered


def _register_scenario_configurator(configurator: ScenarioConfigurator) -> None:
    """Injiziert den Scenario-Demo-Konfigurator (Composition Root,
    `grid_gym.composition.asgi`). Der Lifespan-Env-Branch ruft ihn, wenn
    `GRID_GYM_DEMO_SCENARIO_PATH` gesetzt ist."""
    global _scenario_configurator
    _scenario_configurator = configurator


"""M5-Welle-5 (Slice-Doc Decision 6): Pfad-zur-Demo-YAML-Datei.
Wenn gesetzt, verdrahtet `_lifespan` beim Startup den
produktiven Demo-Stack (Repository + Telemetry + Registry +
Alarm + TickLoop ueber `configure_scenario_demo_run`). Wenn
ungesetzt, ist der Lifespan ein no-op fuer Tests, die ihre
Komponenten ueber `configure_*` selbst injizieren (Welle-1..4b-
Pattern)."""


class HealthResponse(BaseModel):
    """Antwort des `/health`-Endpoints (Liveness-Probe)."""

    status: str = Field(description="Immer 'ok' bei laufender App.")


# RunCreateRequest + RunCreateResponse leben in _schemas.py
# (ADR 0045 §2.4), damit der Strict-Mode-Mixin uniform auf alle
# Request-Bodies (control/faults/runs) wirkt.


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

    Welle 5 (Slice-Doc Decision 6): wenn die env-var
    ``GRID_GYM_DEMO_SCENARIO_PATH`` gesetzt ist UND der App-State
    noch leer ist (Test-Pfade haben ihre Komponenten bereits
    injiziert), verdrahtet der Lifespan den produktiven Demo-
    Stack ueber `_demo_scenario_setup.configure_scenario_demo_run`.

    Tests ohne die jeweiligen Demo-Komponenten bekommen einen
    no-op Lifespan.
    """
    _configure_scenario_demo_from_env_if_requested(app_)
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
        # ADR 0069 §2.2 (Multi-Run-Execution S2): alle per-Run-Driver der
        # RunDriverRegistry sauber stoppen (jeder finalize()-garantiert,
        # ADR 0067). Registry ist leer, solange kein Lauf gestartet wurde
        # (S3) — dann no-op.
        run_driver_registry = getattr(app_.state, "run_driver_registry", None)
        if isinstance(run_driver_registry, RunDriverRegistry):
            await run_driver_registry.stop_all()
        if isinstance(generator, DemoTelemetryGenerator):
            await generator.stop()


def _configure_scenario_demo_from_env_if_requested(app_: FastAPI) -> None:
    """Welle-5-Lifespan-Branch (Slice-Doc Decision 6): scenario-
    getriebener Demo-Setup nur, wenn die env-var
    ``GRID_GYM_DEMO_SCENARIO_PATH`` gesetzt ist UND noch nichts
    konfiguriert wurde.

    Test-Pfade (Welle 1..4b Smoke + Unit) rufen die
    ``configure_*``-Funktionen vor ``TestClient(app)`` explizit;
    `app.state.run_repository` ist dann bereits gesetzt und der
    Lifespan macht hier no-op. Production-Container und
    `python -m grid_gym demo` setzen die env-var und treffen
    `app.state` leer an — der Lifespan verdrahtet den vollen
    Stack (Repository + Telemetry + Registry + Alarm + Scenario-
    TickLoop) idempotent.

    Import ist lokal (statt Modul-Top), damit der Import-Linter-
    Bridge fuer ``_demo_scenario_setup → hexagon.core.scenario.
    loader`` aus `pyproject.toml` ohne `app.py`-Wiederbruch
    greift.
    """
    # Welle-5-Review F11: leerer-String-Env-Var (`= ""`) gilt als
    # nicht gesetzt (sonst Path("") → IsADirectoryError beim
    # read_text).
    scenario_path_raw = os.environ.get(_DEMO_SCENARIO_ENV_VAR, "").strip()
    if not scenario_path_raw:
        return
    # Welle-5-Review F9: Skip-Guard auf Sentinel-Attr statt nur
    # run_repository. Verhindert silent-overwrite vorhergehender
    # Test-State, der run_repository geloescht hat aber andere attrs
    # (tick_loop_registry, alarm_stream, ...) liegen liess.
    if getattr(app_.state, "_lifespan_scenario_configured", False):
        return
    # Welle-5-Review F5: pfad-validieren VOR lifespan-Setup. Ein
    # Tippfehler im env-var (`/app/.../gg-demo.yml` ohne `a`) loest
    # sonst eine bare FileNotFoundError mitten im Lifespan aus, der
    # Container restartet im CrashLoop ohne klaren Hinweis.
    scenario_path = Path(scenario_path_raw)
    if not scenario_path.is_file():
        raise _DemoScenarioPathNotFoundError(scenario_path_raw)
    # 041-C3b: `app.py` importiert das Scenario-Bootstrap NICHT mehr
    # (sonst Adapter → composition → core.scenario/faults, indirekte
    # AC-ADAPTER-PURE-Verletzung). Der Composition-Root
    # `grid_gym.composition.asgi` registriert den Konfigurator via
    # `_register_scenario_configurator`; der Default ist fail-closed.
    configure_run_repository(InMemoryRunRepository())
    configure_telemetry_stream(InMemoryTelemetryStream())
    configure_tick_loop_registry(TickLoopRegistry())
    # `app.state.alarm_*` direkt gesetzt statt ueber
    # `_alarm_setup.configure_alarm_stream`, weil `_alarm_setup`
    # `app` importiert (Cycle).
    app_.state.alarm_stream = InMemoryAlarmStream()
    app_.state.alarm_history_buffer = AlarmHistoryBuffer()
    _scenario_configurator(app_, scenario_path)
    # Welle-5-Review F9: Sentinel-Attr erst NACH erfolgreichem
    # `configure_scenario_demo_run` setzen — sonst blockt der Skip-
    # Guard zukuenftige Retries nach einer Setup-Exception (F2
    # macht configure_scenario_demo_run rollback-sicher, F5
    # validiert den Pfad vor dem Setup).
    app_.state._lifespan_scenario_configured = True


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
    laeuft. Readiness mit persistenten Backend-Checks (Postgres-
    Erreichbarkeit, UI-Surface, Simulation) liefert der separate
    `GET /ready`-Endpoint (M6 Welle 6, `GG-DEPLOY-006`); `/health`
    bleibt Liveness-only (Dockerfile-`HEALTHCHECK`).
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
    # ADR 0068 §2.2 (Trigger 039): Replay-Referenz vor dem Anlegen pruefen —
    # ein `replay_of` auf einen nicht-existenten Lauf wird abgelehnt (422
    # `reference_run_not_found`), statt eine unaufloesbare Bindung zu
    # persistieren (Reject vor Lauf-Start, nicht erst im finalize()-Preflight).
    if request.replay_of is not None and not repository.exists(request.replay_of):
        error = ErrorResponse(
            code="reference_run_not_found",
            message=(
                f"Reference run '{request.replay_of}' not found; cannot create a replay of it."
            ),
            run_id=request.replay_of,
        )
        raise HTTPException(status_code=422, detail=error.model_dump())
    run_id = str(uuid.uuid4())
    # Slice 038 (ADR 0073 §2.3): die GG-TERM-Vollfelder erbt jede neue
    # RunMetadata aus dem statischen Composition-Root-Profil; ohne
    # registrierten Composition Root bleibt das Profil leer und der
    # Replay-Preflight rejected solche Laeufe fail-closed (§2.6).
    profile = get_run_execution_profile()
    metadata = RunMetadata(
        run_id=run_id,
        scenario_hash=request.scenario_hash,
        schema_version="grid-gym.scenario.v1",
        seed=request.seed,
        tick_ms=request.tick_ms,
        started_at="",
        ended_at="",
        tool_version=_APP_VERSION,
        replay_of=request.replay_of,
        platform_arch=profile.platform_arch,
        enabled_adapters=profile.enabled_adapters,
        sim_start_time=SIM_START_TIME_ORIGIN,
        config_hash=profile.config_hash,
    )
    repository.save(metadata)
    return RunCreateResponse(
        run_id=run_id,
        scenario_hash=request.scenario_hash,
        seed=request.seed,
        tick_ms=request.tick_ms,
        replay_of=request.replay_of,
    )


# ---------------------------------------------------------------------------
# M5 Welle 1 — APIRouter-Mounts (ADR 0037)
# ---------------------------------------------------------------------------
#
# Welle-1-Endpunkte sind ueber zwei Router-Module verteilt
# (siehe `_runs_router.py` + `_runs_action_router.py`), damit
# der `AC-NO-GOD-UTILS`-Contract (max 5 public top-level
# functions pro Modul) eingehalten wird.

from grid_gym.adapters.driving.http_api._healthcheck_router import (
    healthcheck_router,
)
from grid_gym.adapters.driving.http_api._ready_router import ready_router
from grid_gym.adapters.driving.http_api._runs_action_router import (
    runs_action_router,
)
from grid_gym.adapters.driving.http_api._run_start_router import (
    runs_start_router,
)
from grid_gym.adapters.driving.http_api._runs_router import runs_router
from grid_gym.adapters.driving.http_api._scenarios_router import (
    scenarios_router,
)

app.include_router(runs_router)
app.include_router(runs_action_router)
app.include_router(scenarios_router)
app.include_router(runs_start_router)
# M6-Welle-4b-c: NEU Backpressure-Healthcheck-Endpoint (GG-RT-001
# 10ms-Modus). Separates Sub-Modul gegen `_runs_router.py`-Wuchs
# (AC-NO-GOD-UTILS; C0-Review-Folge F6).
app.include_router(healthcheck_router)
# M6-Welle-6: NEU `GET /ready`-Readiness-Endpoint (GG-DEPLOY-006
# Three-State). Separates Sub-Modul gegen `app.py`-Wuchs
# (AC-NO-GOD-UTILS max 5 public top-level functions).
app.include_router(ready_router)

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
from grid_gym.adapters.driving.ui.routes_faults import faults_router
from grid_gym.adapters.driving.ui.routes_visualization import visualization_router

_UI_STATIC_DIR: Final[Path] = Path(__file__).parent.parent / "ui" / "static"
app.mount("/static", StaticFiles(directory=str(_UI_STATIC_DIR)), name="static")
app.include_router(ui_router)
app.include_router(faults_router)
app.include_router(visualization_router)
