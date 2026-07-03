"""Welle-4a-Demo-Setup: erzeugt einen Demo-Run + Demo-TickLoop +
DemoTickLoopDriver auf der bereits konfigurierten App (M5 Welle 4a,
ADR 0039 Decision 13).

Auslagerung aus `app.py`, damit der `AC-NO-GOD-UTILS`-Contract
(max 5 public top-level functions pro Modul) in `app.py` nicht
gerissen wird. `app.py` exportiert nur die Konfiguration-Injection-
Punkte (`configure_run_repository`/`_telemetry_stream`/
`_tick_loop_registry`); dieses Modul kombiniert die drei zu einem
Demo-Run-Bundle.

Komposition-Root-Hinweis: importiert `TickLoop` + `Scheduler` aus
`hexagon.core.simulation` (per ADR-0039-Erlaubnis im
`AC-ADAPTER-PURE`-Block in `pyproject.toml`).
"""

from __future__ import annotations

from typing import Final, cast

from grid_gym.adapters.driven.alarm_stream_inmemory import AlarmHistoryBuffer
from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.adapters.driving.http_api._dependencies import (
    _RunRepositoryNotConfiguredError,
)
from grid_gym.adapters.driving.http_api._tick_loop_driver import (
    DemoTickLoopDriver,
)
from grid_gym.adapters.driving.http_api._tick_loop_registry import (
    TickLoopRegistry,
    _TickLoopRegistryNotConfiguredError,
)
from grid_gym.adapters.driving.http_api.app import _APP_VERSION, app
from grid_gym.composition._execution_profile import default_run_execution_profile
from grid_gym.hexagon.core.domain.run import SIM_START_TIME_ORIGIN, RunMetadata
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driven.clock import SimulationTime
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort
from grid_gym.hexagon.ports.driving.alarm_stream import AlarmStreamPort


class _DemoTickLoopDriverAlreadyConfiguredError(RuntimeError):
    """Welle-4b-Review-Fix #13: zweiter `configure_demo_run`-Aufruf
    mit anderem `run_id` orphant den bisherigen Driver. Statt
    stiller Drop wird hier hart abgewiesen — Welle-5-Multi-Run
    bekommt einen `MultiRunDriverRegistry`, Welle-4a/4b bleibt
    Single-Run."""

    def __init__(self, existing_run_id: str, new_run_id: str) -> None:
        super().__init__(
            f"DemoTickLoopDriver is already configured for run_id="
            f"{existing_run_id!r}; refusing to overwrite with run_id="
            f"{new_run_id!r}. Restart the app or extend "
            "configure_demo_run for multi-run scenarios (Welle 5)."
        )


_DEMO_RUN_ID: Final[str] = "demo-run-0001"
"""Welle-4a-Demo-Run-ID fuer den Lifespan-TickLoop. Stabil ueber
alle App-Starts, damit `templates/navigation.html` einen festen
Link auf `/runs/demo-run-0001/control` setzen kann."""


class _DemoSimulationClockInvalidDeltaError(ValueError):
    """`_DemoSimulationClock.advance` mit nicht-positivem `delta_ms`."""

    def __init__(self, value: int) -> None:
        super().__init__(f"delta_ms must be positive, got {value}")


class _DemoSimulationClock:
    """In-Memory-Counter-`ClockPort` fuer den Welle-4a-Demo-TickLoop.

    Welle-4a inline-Adapter: hat keine Devices/grid_model und
    braucht nur einen monotonen Tick-Zaehler in Millisekunden.
    Welle 5 ersetzt das durch eine vollwertige
    ``SimulationClock``-Adapter-Klasse unter
    ``adapters/driven/clock_simulated/``.
    """

    def __init__(self) -> None:
        self._now_ms: SimulationTime = 0

    def now(self) -> SimulationTime:
        return self._now_ms

    def advance(self, delta_ms: int) -> None:
        if delta_ms <= 0:
            raise _DemoSimulationClockInvalidDeltaError(delta_ms)
        self._now_ms += delta_ms


def _cast_run_repository_or_raise() -> RunRepositoryPort:
    """Liest die konfigurierte `RunRepositoryPort` von `app.state`
    oder wirft `_RunRepositoryNotConfiguredError`."""
    repository = getattr(app.state, "run_repository", None)
    if repository is None:
        raise _RunRepositoryNotConfiguredError
    return cast(RunRepositoryPort, repository)


def _cast_tick_loop_registry_or_raise() -> TickLoopRegistry:
    """Liest die konfigurierte `TickLoopRegistry` von `app.state`
    oder wirft `_TickLoopRegistryNotConfiguredError`."""
    registry = getattr(app.state, "tick_loop_registry", None)
    if registry is None:
        raise _TickLoopRegistryNotConfiguredError
    return cast(TickLoopRegistry, registry)


def configure_demo_run(
    *,
    run_id: str = _DEMO_RUN_ID,
    tick_ms: int = 100,
    seed: int = 42,
) -> None:
    """Welle-4a-Demo-Setup: erzeugt einen Demo-Run + Demo-TickLoop +
    DemoTickLoopDriver (ADR 0039 Decision 13).

    Voraussetzung: ``configure_run_repository`` und
    ``configure_tick_loop_registry`` (beide aus ``app.py``) wurden
    bereits aufgerufen. Die Funktion ist idempotent gegenueber
    wiederholten Aufrufen mit demselben ``run_id`` (zweiter Aufruf
    ist No-op, sobald der Run bereits persistiert ist).

    Aufrufer (Welle-4a-Integration-Tests oder ein zukuenftiger
    uvicorn-Entry): nach `configure_demo_run(...)` und vor dem
    `with TestClient(app) as client:` setzt der Lifespan den
    Driver-Task; bei Shutdown wird er sauber gecanceled.
    """
    repository = _cast_run_repository_or_raise()
    registry = _cast_tick_loop_registry_or_raise()
    existing_driver = getattr(app.state, "demo_tick_loop_driver", None)
    if existing_driver is not None and existing_driver.tick_loop_run_id != run_id:
        raise _DemoTickLoopDriverAlreadyConfiguredError(existing_driver.tick_loop_run_id, run_id)
    if repository.exists(run_id):
        return
    # Slice 038 (ADR 0073 §2.3): GG-TERM-Vollfelder aus dem statischen
    # Composition-Root-Profil.
    profile = default_run_execution_profile()
    metadata = RunMetadata(
        run_id=run_id,
        scenario_hash="0" * 64,
        schema_version="grid-gym.scenario.v1",
        seed=seed,
        tick_ms=tick_ms,
        started_at="",
        ended_at="",
        tool_version=_APP_VERSION,
        platform_arch=profile.platform_arch,
        enabled_adapters=profile.enabled_adapters,
        sim_start_time=SIM_START_TIME_ORIGIN,
        config_hash=profile.config_hash,
    )
    repository.save(metadata)
    clock = _DemoSimulationClock()
    random = MersenneTwisterRandomPort(seed=seed)
    scheduler = Scheduler()
    tick_loop = TickLoop(
        run_id=run_id,
        tick_ms=tick_ms,
        clock=clock,
        random=random,
        scheduler=scheduler,
        run_repository=repository,
    )
    registry.register(tick_loop)
    # M5-Welle-4b (ADR 0040 Decision 17): optional alarm-publish-
    # Wiring. Provider-Callables (Welle-4b-Review-Fix #1) lesen
    # `alarm_stream` + `alarm_history_buffer` bei jedem Tick aus
    # `app.state`, damit ein nachtraegliches
    # `configure_alarm_stream(...)` (nach `configure_demo_run`)
    # nicht still in einen No-op-Publish-Pfad faellt.
    driver = DemoTickLoopDriver(
        tick_loop,
        tick_interval_s=tick_ms / 1000.0,
        alarm_stream_provider=_alarm_stream_from_app_state,
        alarm_history_buffer_provider=_alarm_history_buffer_from_app_state,
    )
    app.state.demo_tick_loop_driver = driver


def _alarm_stream_from_app_state() -> AlarmStreamPort | None:
    """Welle-4b-Review-Fix #1: Late-Binding-Provider fuer den
    `AlarmStreamPort`. Wird vom Driver bei jedem Tick aufgerufen,
    damit ein spaeter Aufruf von `configure_alarm_stream(...)`
    den Publish-Pfad noch aktiviert."""
    return cast(AlarmStreamPort | None, getattr(app.state, "alarm_stream", None))


def _alarm_history_buffer_from_app_state() -> AlarmHistoryBuffer | None:
    """Welle-4b-Review-Fix #1: Late-Binding-Provider fuer den
    `AlarmHistoryBuffer`. Symmetrisch zu
    `_alarm_stream_from_app_state`."""
    return cast(AlarmHistoryBuffer | None, getattr(app.state, "alarm_history_buffer", None))
