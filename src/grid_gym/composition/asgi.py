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

from grid_gym.adapters.driving.http_api.app import (
    app,
    _register_scenario_configurator,
)
from grid_gym.composition._demo_scenario_setup import configure_scenario_demo_run

_register_scenario_configurator(configure_scenario_demo_run)

__all__ = ["app"]
