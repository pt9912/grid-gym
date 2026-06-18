"""ASGI-Entrypoint (Composition Root, 041-C3b / ADR 0054).

Produktiver uvicorn-Einstieg: `grid_gym.composition.asgi:app`. Importiert
die FastAPI-`app` aus dem HTTP-Adapter und registriert beim Import den
Scenario-Demo-Konfigurator (`configure_scenario_demo_run`). Damit traegt
**nicht** der Adapter (`app.py`) den `composition`-Import, sondern der
Composition-Root — `AC-ADAPTER-PURE` bleibt ohne `ignore_imports`-Bridge
gewahrt.

Wird die App stattdessen ueber den reinen Adapter-Entrypoint
`grid_gym.adapters.driving.http_api:app` gestartet, bleibt der
Scenario-Konfigurator unregistriert und der Env-getriebene Demo-Branch
schlaegt fail-closed fehl.
"""

from __future__ import annotations

from grid_gym.adapters.driven.persistence_inmemory import InMemoryTelemetrySink
from grid_gym.adapters.driving.http_api._run_driver_registry import RunDriver
from grid_gym.adapters.driving.http_api._run_start_router import (
    _register_run_driver_builder,
)
from grid_gym.adapters.driving.http_api._scenarios_router import (
    _register_scenario_intake,
)
from grid_gym.adapters.driving.http_api.app import (
    app,
    _register_scenario_configurator,
)
from grid_gym.composition._demo_scenario_setup import (
    build_run_driver,
    configure_scenario_demo_run,
)
from grid_gym.composition.scenario_intake import intake_scenario
from grid_gym.hexagon.core.domain.scenario import Scenario
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort

_RUN_TELEMETRY_SINK = InMemoryTelemetrySink()
"""S4 (ADR 0069 §2.3): EIN prozess-weiter, geteilter In-Memory-Telemetrie-Sink
ueber alle API-Laeufe (keyed by `run_id`) — ein Replay-Lauf liest so die Samples
seines Referenzlaufs. Unbounded-by-design (Showcase); der Postgres-
`ReplaySnapshotAdapter` (ADR 0048) ist der Deployment-Pfad (deferred)."""


def _build_run_driver_with_shared_sink(
    scenario: Scenario,
    run_id: str,
    repository: RunRepositoryPort,
    replay_of: str | None,
) -> RunDriver:
    """Hook-Inversion-Wrapper: bindet den prozess-weiten geteilten Sink an
    `build_run_driver` (S4, ADR 0069 §2.3/§2.5)."""
    return build_run_driver(
        scenario,
        run_id,
        repository,
        replay_of=replay_of,
        telemetry_sink=_RUN_TELEMETRY_SINK,
    )


_register_scenario_configurator(configure_scenario_demo_run)
_register_scenario_intake(intake_scenario)
_register_run_driver_builder(_build_run_driver_with_shared_sink)

__all__ = ["app"]
