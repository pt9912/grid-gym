"""Unit: `grid_gym.composition.asgi` verdrahtet den Composition-Root.

Sichert die 041-C3b-Inversion: der ASGI-Entrypoint exportiert dieselbe
FastAPI-`app` wie der Adapter und registriert beim Import den Scenario-
Demo-Konfigurator, sodass der Adapter (`app.py`) selbst keinen
`composition`-Import mehr traegt.

`app.py` wird ueber `importlib.import_module` geholt, nicht ueber
`import ...http_api.app as ...` — letzteres liefert wegen des
Paket-`__init__`-Re-Exports das FastAPI-Objekt statt des Moduls.
"""

from __future__ import annotations

import importlib

from grid_gym.composition import asgi
from grid_gym.composition._demo_scenario_setup import configure_scenario_demo_run

_app_module = importlib.import_module("grid_gym.adapters.driving.http_api.app")


def test_asgi_reexports_the_adapter_app() -> None:
    assert asgi.app is _app_module.app


def test_asgi_import_registers_scenario_configurator() -> None:
    # Import von `asgi` (oben) hat den Konfigurator global registriert —
    # der fail-closed Default ist damit abgeloest.
    assert _app_module._scenario_configurator is configure_scenario_demo_run
