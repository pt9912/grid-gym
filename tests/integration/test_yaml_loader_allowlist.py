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

from grid_gym.hexagon.core.devices.battery.config import (
    BatteryConfig,
    DcBusConfig,
    HealthConfig,
    ReactiveConfig,
    ThermalConfig,
)
from grid_gym.hexagon.core.devices.diesel_generator.config import DieselGeneratorConfig
from grid_gym.hexagon.core.devices.ev_charger.config import EvChargerConfig
from grid_gym.hexagon.core.devices.grid_connection.config import GridConnectionConfig
from grid_gym.hexagon.core.devices.load.config import LoadConfig
from grid_gym.hexagon.core.devices.pv.config import PvConfig
from grid_gym.hexagon.core.devices.smart_meter.config import SmartMeterConfig
from grid_gym.hexagon.core.devices.transformer.config import TransformerConfig
from grid_gym.hexagon.core.devices.wind_turbine.config import WindTurbineConfig

from grid_gym.scenario_yaml import DEVICE_DECIMAL_BLOCKS, DEVICE_DECIMAL_PARAMS

# Slice 077 S3: die nested Field-Envelope-Bloecke, die der Loader **block-scoped**
# (jeder String-Wert) zu Decimal coerced — nur sicher, solange JEDES Feld dieser
# Configs Decimal ist. Mapping Block-Name → Config-Klasse fuer den Drift-Guard.
_BLOCK_CONFIG_BY_NAME: dict[str, type] = {
    "thermal": ThermalConfig,
    "health": HealthConfig,
    "dc_bus": DcBusConfig,
    "reactive": ReactiveConfig,
}


_DEVICE_CONFIG_CLASSES = (
    BatteryConfig,
    DieselGeneratorConfig,
    EvChargerConfig,
    GridConnectionConfig,
    LoadConfig,
    PvConfig,
    SmartMeterConfig,
    TransformerConfig,
    WindTurbineConfig,
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


def test_decimal_blocks_map_to_all_decimal_configs() -> None:
    """Slice-077-S3-Closure-Review (borderline MEDIUM): die block-scoped YAML-Coercion
    (`scenario_yaml.DEVICE_DECIMAL_BLOCKS`) coerced JEDEN String-Wert dieser Bloecke —
    sicher **nur**, solange jedes Feld der zugehoerigen Config Decimal ist. Faellt
    fail-fast, wenn eine Folge-Welle ein `int`/Enum-Feld ergaenzt (dann waere der Block
    feld-genau zu behandeln oder aus `DEVICE_DECIMAL_BLOCKS` zu entfernen — Muster
    `cell`, das wegen `n_cells: int` bewusst draussen ist)."""
    assert set(DEVICE_DECIMAL_BLOCKS) == set(_BLOCK_CONFIG_BY_NAME), (
        "scenario_yaml.DEVICE_DECIMAL_BLOCKS und der Test-Mapping sind auseinander — "
        f"blocks={sorted(DEVICE_DECIMAL_BLOCKS)} mapped={sorted(_BLOCK_CONFIG_BY_NAME)}"
    )
    for block_name, config_cls in _BLOCK_CONFIG_BY_NAME.items():
        non_decimal = _non_decimal_field_names(config_cls)
        assert not non_decimal, (
            f"{config_cls.__name__} (Block {block_name!r}) hat Nicht-Decimal-Felder "
            f"{sorted(non_decimal)} — block-scoped YAML-Coercion wuerde sie korrumpieren. "
            "Feld-genau behandeln oder den Block aus DEVICE_DECIMAL_BLOCKS entfernen."
        )


def _non_decimal_field_names(config_cls: type) -> set[str]:
    hints = get_type_hints(config_cls)
    return {field.name for field in fields(config_cls) if hints.get(field.name) is not Decimal}


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
