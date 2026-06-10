"""Test-seitiger YAML-Loader fuer Integrationstests.

Komponiert den FastAPI-freien Shared-Helper `grid_gym.scenario_yaml`
(YAML-Datei-I/O + `str → Decimal`-Koercion, Single-Source seit
M7-Welle-2 / D-10-Revision C) mit dem I/O-freien Core-Loader
`load_scenario` zu der gewohnten `load_yaml_scenario(path) ->
LoadedScenario`-Signatur. Keine eigene Koercion-Kopie mehr (frueher
drohte Drift gegen `_demo_scenario_setup`); Tests duerfen den Core
direkt importieren (keine `AC-ADAPTER-PURE`-Bindung).
"""

from __future__ import annotations

from pathlib import Path

from grid_gym.hexagon.core.scenario.loader import LoadedScenario, load_scenario
from grid_gym.scenario_yaml import (
    DEVICE_DECIMAL_PARAMS,
    GRID_MODEL_DECIMAL_FIELDS,
    LOAD_EVENT_DECIMAL_FIELDS,
    RULE_PAYLOAD_DECIMAL_KEYS,
    read_scenario_yaml,
)

__all__ = [
    "DEVICE_DECIMAL_PARAMS",
    "GRID_MODEL_DECIMAL_FIELDS",
    "LOAD_EVENT_DECIMAL_FIELDS",
    "RULE_PAYLOAD_DECIMAL_KEYS",
    "load_yaml_scenario",
]


def load_yaml_scenario(path: Path) -> LoadedScenario:
    """Laedt + coerced via Shared-Helper und ruft den Core-Loader."""
    return load_scenario(read_scenario_yaml(path))
