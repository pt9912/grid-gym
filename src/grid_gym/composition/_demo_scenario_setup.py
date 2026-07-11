"""M5-Welle-5 Scenario-getriebener Demo-Setup (Decision 6 +
Slice-Doc-§3 Decisions 5/6/18).

Welle-5-Schwester zu `_demo_setup.py`: laedt ein YAML-Scenario
(`GRID_GYM_DEMO_SCENARIO_PATH`-getrieben), kanonisiert es ueber
den I/O-freien `hexagon.core.scenario.loader.load_scenario` und
baut einen produktiven `TickLoop` ueber `build_tick_loop`. Der
Lifespan (`app.py`) ruft `configure_scenario_demo_run(app_,
scenario_path)` an Stelle von `configure_demo_run`, wenn die
env-var gesetzt ist.

YAML-Datei-Load + `str → Decimal`-Koercion liegen seit M7-Welle-2
(D-10-Revision C) Single-Source im FastAPI-freien Outer-Ring-Modul
`grid_gym.scenario_yaml` (`read_scenario_yaml`); dieser Demo-
Lifespan konsumiert es nur noch (frueher hielt er eine eigene
Coercer-Kopie neben Test-Helper + Abnahme-CLI — Drift-Quelle).

Cycle-Vermeidung (arch_check AC-NO-CYCLES): das Modul nimmt
`app_: FastAPI` als ersten Parameter — kein Modul-Top-Level-
Import aus `app.py`, kein Re-Use der `app`-bezogenen Helfer in
`_demo_setup`. `_DemoSimulationClock` und die Alarm-Provider-
Closures sind lokal dupliziert (klein); `_APP_VERSION` ist hier
gepinnt und mit `app._APP_VERSION` per Konvention synchron zu
halten. Welle-4a-Pfad (`_demo_setup`) bleibt fuer Welle-1..4b-
Tests unangetastet, weil ihn `app.py` nicht importiert.

Komposition-Root-Hinweis: importiert `load_scenario` +
`build_tick_loop` + `TickLoopWiring` aus
`hexagon.core.scenario.loader` (per Welle-5-Bridge im
`AC-ADAPTER-PURE`-Block in `pyproject.toml`).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Final, cast

from fastapi import FastAPI

from grid_gym._app_version import resolve_app_version
from grid_gym.adapters.driven.alarm_stream_inmemory import AlarmHistoryBuffer
from grid_gym.adapters.driven.persistence_inmemory import (
    InMemoryReplaySnapshot,
    InMemoryTelemetrySink,
)
from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.adapters.driving.http_api._dependencies import (
    _RunRepositoryNotConfiguredError,
)
from grid_gym.adapters.driving.http_api._tick_loop_driver import (
    DemoTickLoopDriver,
)
from grid_gym.adapters.driving.http_api._tick_loop_healthcheck import (
    TickLoopHealthcheckAdapter,
)
from grid_gym.adapters.driving.http_api._tick_loop_registry import (
    TickLoopRegistry,
    _TickLoopRegistryNotConfiguredError,
)
from grid_gym.composition._execution_profile import default_run_execution_profile
from grid_gym.hexagon.core.domain.run import SIM_START_TIME_ORIGIN, RunMetadata
from grid_gym.hexagon.core.domain.scenario import Scenario, ScenarioFault
from grid_gym.hexagon.core.faults import ScenarioFaultEngine
from grid_gym.hexagon.core.faults.types import (
    FAULT_TYPE_CELL_FAILURE,
    FAULT_TYPE_CONNECTION_LOSS,
    FAULT_TYPE_FREQUENCY_DROP,
    FAULT_TYPE_GENSET_FAULT,
    FAULT_TYPE_NAN_INJECTION,
    FAULT_TYPE_VOLTAGE_DROP,
    FAULT_TYPE_WINDING_FAULT,
)
from grid_gym.hexagon.core.scenario.loader import (
    TickLoopWiring,
    build_tick_loop,
    load_scenario,
)
from grid_gym.hexagon.ports.driven.clock import SimulationTime
from grid_gym.scenario_yaml import read_scenario_yaml
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort
from grid_gym.hexagon.ports.driven.telemetry_sink import TelemetrySinkPort
from grid_gym.hexagon.ports.driving.alarm_stream import AlarmStreamPort
from grid_gym.hexagon.ports.driving.telemetry_stream import TelemetryStreamPort


_DEMO_RUN_ID: Final[str] = "demo-run-0001"
"""Welle-4a-/-5 stabile Demo-Run-ID. Symmetrie zu
`_demo_setup._DEMO_RUN_ID`, damit `templates/navigation.html`
und produktive UI-Bookmarks ueber beide Pfade konsistent
sind."""


_APP_VERSION: Final[str] = resolve_app_version()
"""Single-Source der Tool-Version via `grid_gym._app_version` (Slice 059).

Frueher ein zweiter harter `"0.1.0"`-Pin, per Konvention synchron zu
`app._APP_VERSION` — die Konvention hielt seit v0.2.0 nicht. `app.py`
importiert dieses Modul, deshalb liest die Version aus dem zyklenfreien
Leaf `grid_gym._app_version` statt aus `app.py` (Cycle-Vermeidung)."""


_DEFAULT_TICK_INTERVAL_S: Final[float] = 0.1
"""Welle-5-Default: 100ms zwischen Wall-Clock-Ticks. Entkoppelt
vom Scenario-`simulation.tick_ms`, damit ein Stunden-Profil
(`tick_ms=3600000`) nicht eine Stunde Wall-Clock pro Tick
bedeutet. Aequivalent zum `DemoTickLoopDriver._DEFAULT_TICK_
INTERVAL_S` aus Welle 4a."""


def configure_scenario_demo_run(
    app_: FastAPI,
    scenario_path: Path,
    *,
    run_id: str = _DEMO_RUN_ID,
    tick_interval_s: float = _DEFAULT_TICK_INTERVAL_S,
) -> None:
    """Welle-5-Demo-Setup: laedt ein Scenario-YAML und baut den
    produktiven Lifespan-`TickLoop` (Slice-Doc Decision 6).

    Voraussetzung: ``configure_run_repository``,
    ``configure_tick_loop_registry`` und (optional)
    ``configure_alarm_stream`` wurden bereits aufgerufen — Lifespan
    macht das in der env-var-Branch unmittelbar davor (Welle-5
    Slice-Doc §4 C2 Schritt e).

    `app_` ist die laufende `FastAPI`-Instanz; der Helfer liest
    `app_.state` und schreibt den `DemoTickLoopDriver` zurueck.
    Cycle-Vermeidung (Slice-Doc §9 + arch_check AC-NO-CYCLES):
    bewusste Parameter-Injection statt Modul-Top-Level-Import von
    `app`.

    Idempotenz: wenn der Run bereits unter ``run_id`` persistiert
    ist, ist der Aufruf ein No-op (Welle-4a-Pattern aus
    `configure_demo_run`). Multi-Run-Driver-Registry ist
    Anti-Scope (Welle-5 Slice-Doc §1.3); ein zweiter Aufruf mit
    abweichendem `run_id` wird vom `DemoTickLoopDriver`-
    Already-Configured-Pfad in `_demo_setup` abgewiesen, falls
    der Default-Path zuerst lief.
    """
    repository = _cast_run_repository_or_raise(app_)
    registry = _cast_tick_loop_registry_or_raise(app_)
    if repository.exists(run_id):
        return
    # Welle-5-Review F6: Already-Configured-Guard analog
    # `_demo_setup.configure_demo_run`. Verhindert silent-overwrite
    # eines bestehenden DemoTickLoopDrivers (orphaned-Task-Risk).
    existing_driver = getattr(app_.state, "demo_tick_loop_driver", None)
    if existing_driver is not None and existing_driver.tick_loop_run_id != run_id:
        raise _ScenarioDemoTickLoopDriverAlreadyConfiguredError(
            existing_driver.tick_loop_run_id, run_id
        )
    # Welle-5-Review F2: Validation-First. Erst Scenario laden, dann
    # FaultPort komponieren, dann TickLoop bauen — alles BEVOR
    # `repository.save`. Eine spaete Exception (UnknownFaultType,
    # ScenarioWrongType, DecimalCoercion) hinterlaesst die Repository
    # sonst befuellt, und der Skip-Guard im Lifespan blockt jeden
    # Re-Try permanent.
    loaded = load_scenario(read_scenario_yaml(scenario_path))
    clock = _DemoSimulationClock()
    random_root = MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed)
    fault_port = _compose_fault_port(loaded.scenario.faults)
    # M7-Welle-1a (ADR 0047): in-memory Telemetrie-Sink fuer den
    # in-process-Demo-Lauf (parallel zu InMemoryRunRepository; kein
    # Postgres im Lifespan). Der TickLoop persistiert pro Tick
    # `emitted_telemetry` append-only; lesbar via
    # `app_.state.telemetry_sink.read_ordered(run_id)`.
    telemetry_sink = InMemoryTelemetrySink()
    # M7-Welle-1b-b (ADR 0049 §2.2): Replay-Snapshot-Lese-Surface
    # ueber denselben In-Memory-Telemetrie-Store. Der Demo-Lauf hat
    # keinen Referenzlauf (`replay_reference_run_id=None`) → der
    # Core-`finalize()`-Hook ist hier no-op; die Bindung dokumentiert
    # die Verdrahtung + exerziert den Driver-`finalize()`-Trigger-Pfad.
    wiring = TickLoopWiring(
        run_repository=repository,
        alarm_id_source=_alarm_id_source(),
        fault_port=fault_port,
        telemetry_sink=telemetry_sink,
        replay_snapshot=InMemoryReplaySnapshot(telemetry_sink),
    )
    tick_loop = build_tick_loop(
        loaded.scenario,
        run_id=run_id,
        clock=clock,
        random_root=random_root,
        wiring=wiring,
    )
    # Slice 038 (ADR 0073 §2.3): GG-TERM-Vollfelder aus dem statischen
    # Composition-Root-Profil.
    profile = default_run_execution_profile()
    metadata = RunMetadata(
        run_id=run_id,
        scenario_hash=loaded.scenario_hash,
        schema_version=loaded.scenario.schema_version,
        seed=loaded.scenario.simulation.seed,
        tick_ms=loaded.scenario.simulation.tick_ms,
        started_at="",
        ended_at="",
        tool_version=_APP_VERSION,
        platform_arch=profile.platform_arch,
        enabled_adapters=profile.enabled_adapters,
        sim_start_time=SIM_START_TIME_ORIGIN,
        config_hash=profile.config_hash,
    )
    repository.save(metadata)
    registry.register(tick_loop)
    # M6-Welle-6: Healthcheck-Adapter am produktiven TickLoop
    # registrieren. Ohne diese Registrierung meldet `/ready`
    # (GG-DEPLOY-006) die `simulation`-Komponente dauerhaft
    # `degraded` mit der falschen „sleep-infinity-Stub"-Ursache
    # (`any_healthcheck_adapter()` → None), obwohl ein echter
    # TickLoop laeuft — GG-DEPLOY-005 „Systemstatus healthy" waere
    # im Compose-Stack nie erreichbar. Der Driver meldet pro Tick
    # `record_tick_duration` an diesen Adapter; er speist zugleich
    # den `GET /runs/{id}/healthcheck`-Endpoint (Welle 4b-c) im
    # Demo-Stack.
    healthcheck_adapter = TickLoopHealthcheckAdapter(tick_loop)
    registry.register_healthcheck_adapter(run_id, healthcheck_adapter)

    def _alarm_stream_provider() -> AlarmStreamPort | None:
        return cast(AlarmStreamPort | None, getattr(app_.state, "alarm_stream", None))

    def _alarm_history_buffer_provider() -> AlarmHistoryBuffer | None:
        return cast(
            AlarmHistoryBuffer | None,
            getattr(app_.state, "alarm_history_buffer", None),
        )

    def _telemetry_stream_provider() -> TelemetryStreamPort | None:
        return cast(
            TelemetryStreamPort | None,
            getattr(app_.state, "telemetry_stream", None),
        )

    # Welle-5-Review F10: tick_interval_s an scenario.tick_ms koppeln,
    # mit Cap auf 0.1s damit Stunden-Profile (tick_ms=3600000) nicht
    # 1h-wall-clock pro Tick brauchen. Reine 100ms-Wall-Clock-Konstante
    # liess gg-demo.yaml (tick_ms=1000) 10x schneller laufen.
    resolved_tick_interval_s = min(tick_interval_s, loaded.scenario.simulation.tick_ms / 1000.0)
    driver = DemoTickLoopDriver(
        tick_loop,
        tick_interval_s=resolved_tick_interval_s,
        healthcheck_adapter=healthcheck_adapter,
        alarm_stream_provider=_alarm_stream_provider,
        alarm_history_buffer_provider=_alarm_history_buffer_provider,
        telemetry_stream_provider=_telemetry_stream_provider,
    )
    app_.state.demo_tick_loop_driver = driver
    # M7-Welle-1a (ADR 0047): persistierte Zeitreihen lesbar machen
    # (Welle-1b-ReplaySource-Quelle + Demo-Persistenz-Beleg).
    app_.state.telemetry_sink = telemetry_sink


def build_run_driver(
    scenario: Scenario,
    run_id: str,
    repository: RunRepositoryPort,
    *,
    telemetry_sink: TelemetrySinkPort,
) -> DemoTickLoopDriver:
    """Multi-Run-Execution S3/S4 (ADR 0069 §2.4/§2.5): baut einen per-Run-
    `TickLoop` + `DemoTickLoopDriver` aus einem bereits kanonisierten `Scenario`.

    Spiegelt die Konstruktion in `configure_scenario_demo_run`, aber **ohne**
    `app.state`-/Registry-Wiring — der Aufrufer (`POST /runs/{id}/start`)
    registriert den Driver in der `RunDriverRegistry` (S2). Der Lauf MUSS bereits
    persistiert sein (`POST /runs`); Seed + `replay_of` liest dieser Builder aus
    der `RunMetadata` (Single Source — Review-MEDIUM: so deckt sich der
    Execution-Seed mit dem Replay-Preflight-Vergleichsfeld `RunMetadata.seed`).

    Per-Run-Isolation (ADR 0069 §2.3): eigener Clock + Random-Root je Lauf; der
    `RandomPort`-Wurzelseed kommt aus `metadata.seed` (= Lauf-Identitaet
    `(scenario_hash, seed)`, `GG-SEED-001`). Der **Telemetrie-Sink ist GETEILT**
    (keyed by `run_id`, vom Aufrufer gereicht), damit ein Replay-Lauf die Samples
    seines Referenzlaufs lesen kann (§2.3-Verfeinerung).

    Replay-Konsumnaht (S4, §2.5): ist `metadata.replay_of` gesetzt, wird es als
    `replay_reference_run_id` verdrahtet — `finalize()` difft den Lauf dann gegen
    den Referenzlauf (Samples aus dem geteilten Sink). `replay_of=None` → kein
    Diff (no-op); der Lauf persistiert nur seine eigenen Samples.
    """
    metadata = repository.get_by_id(run_id)
    clock = _DemoSimulationClock()
    random_root = MersenneTwisterRandomPort(seed=metadata.seed)
    fault_port = _compose_fault_port(scenario.faults)
    wiring = TickLoopWiring(
        run_repository=repository,
        alarm_id_source=_alarm_id_source(),
        fault_port=fault_port,
        telemetry_sink=telemetry_sink,
        replay_snapshot=InMemoryReplaySnapshot(telemetry_sink),
        replay_reference_run_id=metadata.replay_of,
    )
    tick_loop = build_tick_loop(
        scenario,
        run_id=run_id,
        clock=clock,
        random_root=random_root,
        wiring=wiring,
    )
    resolved_tick_interval_s = min(_DEFAULT_TICK_INTERVAL_S, scenario.simulation.tick_ms / 1000.0)
    return DemoTickLoopDriver(tick_loop, tick_interval_s=resolved_tick_interval_s)


class _ScenarioDemoTickLoopDriverAlreadyConfiguredError(RuntimeError):
    """Welle-5-Review F6: schon ein DemoTickLoopDriver auf
    `app_.state.demo_tick_loop_driver` registriert mit anderem
    `run_id`. Pattern analog `_demo_setup.
    _DemoTickLoopDriverAlreadyConfiguredError` (Welle-4b-Review-Fix
    #13) — wir importieren NICHT, weil `_demo_setup` `app` direkt
    importiert (Cycle-Vermeidung pro Slice-Doc §9)."""

    def __init__(self, existing_run_id: str, new_run_id: str) -> None:
        super().__init__(
            f"DemoTickLoopDriver is already configured for run_id="
            f"{existing_run_id!r}; refusing to overwrite with run_id="
            f"{new_run_id!r}. Restart the app or use the same run_id "
            "for multi-call scenarios."
        )


def _cast_run_repository_or_raise(app_: FastAPI) -> RunRepositoryPort:
    """Welle-5-Variante von `_demo_setup._cast_run_repository_or_
    raise` — liest aus `app_.state` (Parameter) statt aus dem
    Modul-Global `app`. Cycle-Vermeidung (Slice-Doc §9)."""
    repository = getattr(app_.state, "run_repository", None)
    if repository is None:
        raise _RunRepositoryNotConfiguredError
    return cast(RunRepositoryPort, repository)


def _cast_tick_loop_registry_or_raise(app_: FastAPI) -> TickLoopRegistry:
    """Welle-5-Variante von `_demo_setup._cast_tick_loop_registry_
    or_raise`."""
    registry = getattr(app_.state, "tick_loop_registry", None)
    if registry is None:
        raise _TickLoopRegistryNotConfiguredError
    return cast(TickLoopRegistry, registry)


_KNOWN_FAULT_TYPES: Final[frozenset[str]] = frozenset(
    {
        FAULT_TYPE_CELL_FAILURE,
        FAULT_TYPE_VOLTAGE_DROP,
        FAULT_TYPE_FREQUENCY_DROP,
        FAULT_TYPE_CONNECTION_LOSS,
        FAULT_TYPE_WINDING_FAULT,
        FAULT_TYPE_GENSET_FAULT,
    }
)
"""ADR 0059: single source of truth der **device-adressierten Physik-
Fault-Typen** — zugleich die `supported_types` der produktiven
`ScenarioFaultEngine`. Neue fault-faehige Geraete tragen ihren
`FAULT_TYPE_*` hier ein (mehr braucht es nicht: die generische Engine
reicht den Typ an das Ziel-Geraet durch, das ihn validiert)."""

_QUALITY_FAULT_TYPES: Final[frozenset[str]] = frozenset({FAULT_TYPE_NAN_INJECTION})
"""ADR 0074 §2.1/§2.2 (Slice 071): metrik-adressierte Quality-Fault-
Typen (`nan_injection`; Slice B ergaenzt `stale_data`). Sie laufen den
parallelen, spine-internen `QualityFaultRuntime`-Pfad (verdrahtet in
`build_tick_loop`), **nicht** den device-adressierten
`ScenarioFaultEngine` — sie duerfen deshalb NICHT in dessen
`supported_types` (`_KNOWN_FAULT_TYPES`), sonst wuerde die Engine ein
`device.inject_fault("nan_injection", …)` versuchen (kein Geraete-
Handler → `FaultUnsupportedTypeError`). Bewusst getrennt gehalten,
aber im „bekannter Fault-Typ"-Check (`_compose_fault_port`)
mitgezaehlt, damit eine Demo-YAML mit `nan_injection` nicht als
unbekannter Typ rejected wird."""

_ALL_KNOWN_FAULT_TYPES: Final[frozenset[str]] = _KNOWN_FAULT_TYPES | _QUALITY_FAULT_TYPES
"""Vereinigung fuer den Demo-YAML-„bekannter Fault-Typ"-Check: Physik-
Faults (`_KNOWN_FAULT_TYPES`) + metrik-adressierte Quality-Faults
(`_QUALITY_FAULT_TYPES`). YAML-faults mit einem Typ ausserhalb dieser
Menge werden per `_DemoScenarioUnknownFaultTypeError` rejected statt
silent gedroppt (Welle-6a-Review F13)."""


class _DemoScenarioUnknownFaultTypeError(ValueError):
    """Welle-6a-Review F13: `gg-demo.yaml` enthaelt einen
    `faults[].type`, fuer den kein Geraet einen Handler hat
    (nicht in `_KNOWN_FAULT_TYPES`). Frueher silent gedroppt;
    jetzt explizit fail-fast beim Demo-Lifespan-Startup, damit der
    Engineer den YAML-Tippfehler oder den fehlenden Geraete-Fault-
    Typ beim ersten `make demo` sieht."""

    def __init__(self, unknown_type: str, known: tuple[str, ...]) -> None:
        super().__init__(
            f"Demo scenario YAML declares fault type {unknown_type!r}, "
            f"but no device handles it. Known fault types: "
            f"{known}. Either fix the YAML, or add the new "
            "`FAULT_TYPE_*` to `_KNOWN_FAULT_TYPES`."
        )


def _compose_fault_port(
    faults: tuple[ScenarioFault, ...],
) -> "ScenarioFaultEngine | None":
    """ADR 0059: liefert **eine** generische `ScenarioFaultEngine`
    ueber alle bekannten Fault-Typen (`_KNOWN_FAULT_TYPES`). Liefert
    `None` bei leerer Fault-Liste (Welle-5-Default-Verhalten
    unveraendert).

    Vorher (Welle-6a Decision 19) komponierte `_FaultPortComposition`
    `BatteryFaultEngine` + `GridFaultEngine` sequenziell mit
    try/finally-Cross-Adapter-Isolation. Mit der generischen Engine
    entfaellt das: eine Engine verarbeitet alle Typen in einer
    Schleife in Fault-Listen-Reihenfolge — inhaerent deterministisch
    (ADR 0021 §2.9), kein Adapter-Ordering noetig.

    Welle-6a-Review F13: unbekannte `fault.type`-Werte werden
    fail-fast mit `_DemoScenarioUnknownFaultTypeError` rejected
    statt silent gedroppt (die Engine wuerde sie sonst stumm auf
    `_KNOWN_FAULT_TYPES` filtern — eine Demo-YAML mit fault_type=
    `thermal_runaway` haette ohne diesen Check keine Wirkung).
    """
    if not faults:
        return None
    for fault in faults:
        if fault.type not in _ALL_KNOWN_FAULT_TYPES:
            raise _DemoScenarioUnknownFaultTypeError(
                fault.type, tuple(sorted(_ALL_KNOWN_FAULT_TYPES))
            )
    # ADR 0074 §2.2: metrik-adressierte Quality-Faults (`_QUALITY_FAULT_
    # TYPES`) sind bewusst NICHT in den `supported_types` — sie laufen den
    # spine-internen `QualityFaultRuntime`-Pfad (aus `build_tick_loop`),
    # nicht diese device-adressierte Engine. Ein Szenario mit AUSSCHLIESS-
    # lich Quality-Faults bekommt hier eine Engine ohne aktive Physik-Typen
    # (No-Op-Filter), was korrekt ist; der Quality-Pfad ist separat.
    return ScenarioFaultEngine(faults, supported_types=_KNOWN_FAULT_TYPES, subsystem="demo")


class _DemoSimulationClockInvalidDeltaError(ValueError):
    """Symmetrisch zu `_demo_setup._DemoSimulationClockInvalidDeltaError`.

    Welle-5-Cycle-Fix-Duplikat (Slice-Doc §9) — Verschmelzung
    mit `_demo_setup` ist Welle-6+ Cleanup."""

    def __init__(self, value: int) -> None:
        super().__init__(f"delta_ms must be positive, got {value}")


class _DemoSimulationClock:
    """In-Memory-`ClockPort`-Duplikat zu `_demo_setup.
    _DemoSimulationClock`.

    Welle-5-Cycle-Fix-Duplikat (Slice-Doc §9): das Original lebt
    in `_demo_setup`, das `app.py` als Top-Level-Cycle braucht.
    Welle 5 kann nicht von `_demo_setup` importieren, weil
    `app.py` `_demo_scenario_setup` importiert — wir wuerden
    sonst `_demo_scenario_setup → _demo_setup → app →
    _demo_scenario_setup` als Cycle bekommen. Verschmelzung zu
    einem gemeinsamen `_simulation_clock`-Modul ist Welle-6+
    Cleanup.
    """

    def __init__(self) -> None:
        self._now_ms: SimulationTime = 0

    def now(self) -> SimulationTime:
        return self._now_ms

    def advance(self, delta_ms: int) -> None:
        if delta_ms <= 0:
            raise _DemoSimulationClockInvalidDeltaError(delta_ms)
        self._now_ms += delta_ms


def _alarm_id_source() -> Callable[[], str]:
    """Welle-5: Production-Default per `TickLoopWiring.alarm_id_
    source`-Vertrag (`uuid.uuid4().hex`). Tests koennen den Stub
    durch einen monoton zaehlenden Generator ersetzen — Welle-5-
    Smoke laesst den Production-Default laufen, weil Hash-Pin nur
    den ersten Tick-Block pinnt (vor erstem Alarm-Emit)."""
    return lambda: uuid.uuid4().hex
