"""Scenario-Store-Setup: setzt `ScenarioStorePort` auf `app.state` fuer die
laufende App (Multi-Run-Execution S1, ADR 0069 §2.1).

Ausgelagert aus `app.py`, damit der `AC-NO-GOD-UTILS`-Contract (max 5 public
top-level functions pro Modul) nicht reisst — Pattern analog `_alarm_setup.py`.
`app.py` importiert dieses Modul nicht (kein Cycle); Composition-Root und Tests
rufen `configure_scenario_store` vor dem ersten Request.
"""

from __future__ import annotations

from grid_gym.adapters.driving.http_api.app import app
from grid_gym.hexagon.ports.driven.scenario_store import ScenarioStorePort


def configure_scenario_store(store: ScenarioStorePort) -> None:
    """Setzt den `ScenarioStorePort` fuer die laufende App (Multi-Run-Execution
    S1, ADR 0069 §2.1).

    `POST /scenarios` legt kanonisierte Szenarien dort ab; ein spaeterer
    hash-referenzierter Lauf loest sie auf. Pattern analog
    `_alarm_setup.configure_alarm_stream`.
    """
    app.state.scenario_store = store
