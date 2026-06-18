"""Run-Driver-Registry-Setup: setzt die `RunDriverRegistry` auf `app.state`
(Multi-Run-Execution S2, ADR 0069 §2.2).

Ausgelagert aus `app.py` (`AC-NO-GOD-UTILS`, max 5 public top-level functions);
Pattern analog `_scenario_setup.py`/`_alarm_setup.py`. `app.py` importiert dieses
Modul nicht (kein Cycle); Composition-Root und Tests rufen
`configure_run_driver_registry` vor dem ersten Request.
"""

from __future__ import annotations

from grid_gym.adapters.driving.http_api._run_driver_registry import RunDriverRegistry
from grid_gym.adapters.driving.http_api.app import app


def configure_run_driver_registry(registry: RunDriverRegistry) -> None:
    """Setzt die `RunDriverRegistry` fuer die laufende App (Multi-Run-Execution
    S2, ADR 0069 §2.2).

    Der Lifespan-Shutdown ruft `registry.stop_all()` (alle aktiven Driver
    sauber beenden, `finalize()`-garantiert); S3 fuettert die Registry per
    `POST /runs/{id}/start`.
    """
    app.state.run_driver_registry = registry
