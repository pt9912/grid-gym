"""Drift-Detection fuer `DEVICE_DECIMAL_PARAMS`-Allowlist
(M2-Welle-6c-Review M-3).

Wenn eine Folge-Welle ein neues `Decimal`-Feld in einem Device-
Config ergaenzt (z. B. `BatteryConfig.thermal_capacity_kwh_per_k`)
und der Eintrag in der Shared-Loader-Allowlist
(`grid_gym.scenario_yaml.DEVICE_DECIMAL_PARAMS`) vergessen wird,
akzeptiert die YAML-Coercion den `str`-Wert nicht — das Demo-
Szenario knallt erst beim `device.initialize(...)` mit einem
generischen `WrongTypeError("Decimal", "str")`, dessen Quelle
nicht offensichtlich auf die fehlende Loader-Coercion zeigt.

Dieser Test scannt alle 5 MVP-Device-Configs ueber
`dataclasses.fields(...)` und stellt sicher, dass **jedes**
Decimal-Feld in `DEVICE_DECIMAL_PARAMS` enthalten ist. Faellt
fail-fast in CI, wenn eine spaetere Welle Device-Configs
erweitert.
"""

from __future__ import annotations

from dataclasses import fields
from decimal import Decimal
from typing import get_type_hints

from grid_gym.hexagon.core.devices.battery.config import BatteryConfig
from grid_gym.hexagon.core.devices.ev_charger.config import EvChargerConfig
from grid_gym.hexagon.core.devices.grid_connection.config import GridConnectionConfig
from grid_gym.hexagon.core.devices.load.config import LoadConfig
from grid_gym.hexagon.core.devices.pv.config import PvConfig
from grid_gym.hexagon.core.devices.smart_meter.config import SmartMeterConfig

from grid_gym.scenario_yaml import DEVICE_DECIMAL_PARAMS


_DEVICE_CONFIG_CLASSES = (
    BatteryConfig,
    EvChargerConfig,
    GridConnectionConfig,
    LoadConfig,
    PvConfig,
    SmartMeterConfig,
)


def _decimal_field_names(config_cls: type) -> set[str]:
    """Liefert die Namen aller `Decimal`-typed Felder eines Configs."""
    hints = get_type_hints(config_cls)
    return {field.name for field in fields(config_cls) if hints.get(field.name) is Decimal}


def test_yaml_loader_allowlist_covers_all_device_decimal_fields() -> None:
    """Welle-6c-Review M-3: `DEVICE_DECIMAL_PARAMS` muss alle
    Decimal-Felder der 5 MVP-Device-Configs enthalten."""
    expected: set[str] = set()
    for config_cls in _DEVICE_CONFIG_CLASSES:
        expected |= _decimal_field_names(config_cls)
    missing = expected - DEVICE_DECIMAL_PARAMS
    assert not missing, (
        "src/grid_gym/scenario_yaml.py::DEVICE_DECIMAL_PARAMS "
        f"fehlen folgende Decimal-Felder: {sorted(missing)}. "
        "Eintrag ergaenzen, sonst akzeptiert die YAML-Coercion str-Werte "
        "nicht und der MVP-Demo-Test knallt mit irrefuehrendem "
        "WrongTypeError."
    )


def test_yaml_loader_allowlist_has_no_orphan_entries() -> None:
    """Welle-6c-Review M-3: jeder Eintrag in `DEVICE_DECIMAL_PARAMS`
    muss in mindestens einem Device-Config existieren — sonst ist
    er ein Relikt aus einer entfernten Welle und kann weg."""
    actual: set[str] = set()
    for config_cls in _DEVICE_CONFIG_CLASSES:
        actual |= _decimal_field_names(config_cls)
    orphans = DEVICE_DECIMAL_PARAMS - actual
    assert not orphans, (
        "src/grid_gym/scenario_yaml.py::DEVICE_DECIMAL_PARAMS "
        f"enthaelt Orphan-Eintraege (in keinem Device-Config): {sorted(orphans)}. "
        "Eintraege entfernen."
    )
