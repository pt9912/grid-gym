"""Shared YAML→Scenario-Loader (Outer-Ring; M7-Welle-2, D-10-Revision C).

**FastAPI-frei.** Single-Source der Szenario-YAML-Datei-I/O +
`str → Decimal`-Koercion fuer **alle** Konsumenten:

- `adapters/driving/http_api/_demo_scenario_setup.py` (produktiver
  Demo-Lifespan),
- `tools/accept.py` + `tools/check_demo_scenario_pin.py` (Abnahme-CLI,
  GG-MVP-003),
- `tests/integration/_yaml_scenario_loader.py` (Integrationstests).

**ADR-0021-§2.1-Schaerfung (D-10-Revision):** der Hexagon-Core haelt
weiterhin **keinen** YAML-Adapter — `load_scenario(raw)` bleibt
Mapping-only und I/O-frei. YAML-Datei-Lesen + Decimal-Normalisierung
sind ein kleiner FastAPI-freier **Outer-Ring**-Helper (kein
`adapters/driven/scenario_yaml/`-Hexagon-Adapter, Welle-5-Decision-18
bleibt insoweit gewahrt; dies ist der bewusste, schmale Shared-Helper
fuer Demo + Abnahme statt drei divergierender Koercion-Kopien).

**Koercionsregel:** ausschliesslich `str → Decimal` auf einer
schema-bewussten Feld-Allowlist. Floats in den Quelldaten lehnt der
Scenario-Validator typisiert ab (`ScenarioWrongTypeError`);
Praezisionsverluste sind damit konstruktiv ausgeschlossen
(`GG-DATA-005`). Nicht-Mapping/Nicht-List-Strukturen werden
**unveraendert** durchgereicht — der Validator wirft anschliessend
`ScenarioWrongTypeError` mit korrektem Pfad.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Final

import yaml

DEVICE_DECIMAL_PARAMS: Final[frozenset[str]] = frozenset(
    {
        "rated_power_kw",
        "capacity_kwh",
        "initial_soc_pct",
        "min_soc_pct",
        "max_soc_pct",
        "max_charge_kw",
        "max_discharge_kw",
        "charge_efficiency",
        "discharge_efficiency",
        "ramp_kw_per_s",
        "nominal_voltage_v",
        "max_import_kw",
        "max_export_kw",
        # M8-Welle-2a EV-Charger (ADR 0055 §2.3). `initial_plug_state`
        # bleibt String und wird bewusst NICHT coerced.
        "battery_capacity_kwh",
        "cv_phase_start_soc",
        "initial_soc",
        # M8-Welle-2b Transformer (ADR 0056 §2.3); `rated_power_kw` ist
        # schon oben (PV/Load) gelistet.
        "primary_voltage_v",
        "turns_ratio",
        "no_load_loss_kw",
        "load_loss_kw",
        # M8-Welle-2c Wind-Turbine (ADR 0057 §2.3); `rated_power_kw` ist
        # schon oben gelistet.
        "cut_in_speed_ms",
        "rated_speed_ms",
        "cut_out_speed_ms",
        "min_wind_speed_ms",
        "max_wind_speed_ms",
        # M8-Welle-2d Diesel-Generator (ADR 0058 §2.3); `ramp_kw_per_s`
        # ist schon oben (Battery) gelistet.
        "max_power_kw",
        "min_start_power_kw",
        "min_stop_power_kw",
        "fuel_capacity_l",
        "initial_fuel_l",
        "fuel_per_kwh_l",
    }
)

GRID_MODEL_DECIMAL_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "nominal_frequency_hz",
        "frequency_sensitivity_hz_per_kw",
        "frequency_clamp_min_hz",
        "frequency_clamp_max_hz",
        "nominal_voltage_v",
        "voltage_sensitivity_v_per_kw",
        "voltage_clamp_min_v",
        "voltage_clamp_max_v",
    }
)

LOAD_EVENT_DECIMAL_FIELDS: Final[frozenset[str]] = frozenset({"start_s", "duration_s", "power_kw"})

# Welle-4b (ADR 0027): `params.rules[*].action.payload`-Strang traegt
# physikalische Werte (z. B. `value: "20"` fuer `set_power_kw`), die der
# TickLoop an `Device.apply_command` reicht (erwartet Decimal). Conditions
# bleiben int-typed.
RULE_PAYLOAD_DECIMAL_KEYS: Final[frozenset[str]] = frozenset({"value", "power_kw"})

# ADR 0070 (Trigger 046): scenario-`commands`-Block. `payload.value` ist nur fuer
# numerische Command-Typen ein Decimal-kW-Wert; `set_plug_state` traegt einen
# String-Enum-Wert (z. B. "plugged") und wird bewusst NICHT coerced (sonst
# `Decimal("plugged")` -> InvalidOperation). Typ-bewusste Allowlist.
COMMAND_DECIMAL_VALUE_TYPES: Final[frozenset[str]] = frozenset({"set_charge_power", "set_power_kw"})
_COMMAND_PAYLOAD_DECIMAL_KEYS: Final[frozenset[str]] = frozenset({"value", "power_kw"})


class ScenarioYamlError(ValueError):
    """Wurzel fuer YAML-Lade-/Koercions-Fehler dieses Helpers."""


class ScenarioYamlInvalidRootError(ScenarioYamlError):
    """Die YAML-Datei hat keinen Mapping-Root (Liste/Skalar). Fail-fast
    vor `load_scenario`."""

    def __init__(self, path: Path, root_type: str) -> None:
        super().__init__(f"scenario YAML root must be a mapping; got {root_type} from {path}")


class ScenarioYamlDecimalCoercionError(ScenarioYamlError):
    """Ein Allowlist-Feld traegt einen malformed Decimal-String.

    `Decimal(value)` wirft `InvalidOperation` (ArithmeticError, NICHT
    ValueError); wir propagieren mit Feldname-Kontext, damit der
    YAML-Editor den Fehler sofort lokalisieren kann."""

    def __init__(self, field: str, value: str, cause: Exception) -> None:
        super().__init__(f"field '{field}' is not a valid Decimal: {value!r} ({cause})")


def read_scenario_yaml(path: Path) -> dict[str, Any]:
    """Liest eine YAML-Szenariodatei + coerced die Decimal-
    Pflichtfelder; liefert das fertige Mapping fuer den I/O-freien
    Core-Loader `load_scenario(raw)`.

    **Bewusst core-frei** (Outer-Ring, kein `hexagon.core`-Import):
    den `load_scenario(...)`-Aufruf macht der jeweilige Kompositions-
    Root (Demo-Lifespan / Abnahme-CLI / Test-Helper), der dafuer
    ohnehin Zugriff auf den Core hat. So entsteht **keine** Adapter→
    Core-Importkette ueber diesen Helper und damit **keine neue
    arch-check-Ausnahme** (`AC-ADAPTER-PURE`)."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ScenarioYamlInvalidRootError(path, type(raw).__name__)
    return _coerce_decimals(raw)


def coerce_scenario_mapping(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Public `str → Decimal`-Koercion fuer ein Scenario-Mapping aus einer
    Nicht-YAML-Quelle (z. B. ein `POST /scenarios`-JSON-Body, ADR 0069
    §2.1 Variante A).

    Gleiche allowlist-basierte Koercion wie `read_scenario_yaml`, aber ohne
    Datei-I/O — der Aufrufer (Composition-Root) reicht das Ergebnis an den
    I/O-freien Core-Loader `load_scenario(raw)`. `float`-Werte bleiben
    **unveraendert**; der Scenario-Validator lehnt sie anschliessend
    typisiert ab (`ScenarioWrongTypeError`, `GG-DATA-005`)."""
    return _coerce_decimals(raw)


def _safe_decimal(value: str, field: str) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise ScenarioYamlDecimalCoercionError(field, value, exc) from exc


def _coerce_decimals(raw: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = dict(raw)

    devices = result.get("devices")
    if isinstance(devices, list):
        result["devices"] = [_coerce_device(entry) for entry in devices]

    grid_model = result.get("grid_model")
    if isinstance(grid_model, Mapping):
        result["grid_model"] = _coerce_decimal_fields(grid_model, GRID_MODEL_DECIMAL_FIELDS)

    load_events = result.get("load_events")
    if isinstance(load_events, list):
        result["load_events"] = [_coerce_load_event(entry) for entry in load_events]

    load_profiles = result.get("load_profiles")
    if isinstance(load_profiles, list):
        result["load_profiles"] = [_coerce_load_profile(entry) for entry in load_profiles]

    agents = result.get("agents")
    if isinstance(agents, Mapping):
        result["agents"] = {
            agent_id: _coerce_agent(agent_def) for agent_id, agent_def in agents.items()
        }

    commands = result.get("commands")
    if isinstance(commands, list):
        result["commands"] = [_coerce_command(entry) for entry in commands]

    return result


def _coerce_device(entry: Any) -> Any:
    if not isinstance(entry, Mapping):
        return entry
    result = dict(entry)
    params = result.get("params")
    if isinstance(params, Mapping):
        result["params"] = _coerce_decimal_fields(params, DEVICE_DECIMAL_PARAMS)
    return result


def _coerce_decimal_fields(
    entry: Mapping[str, Any], decimal_fields: frozenset[str]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in entry.items():
        if key in decimal_fields and isinstance(value, str):
            result[key] = _safe_decimal(value, key)
        else:
            result[key] = value
    return result


def _coerce_load_event(entry: Any) -> Any:
    if not isinstance(entry, Mapping):
        return entry
    return _coerce_decimal_fields(entry, LOAD_EVENT_DECIMAL_FIELDS)


def _coerce_load_profile(entry: Any) -> Any:
    if not isinstance(entry, Mapping):
        return entry
    result = dict(entry)
    tick_values = result.get("tick_values")
    if isinstance(tick_values, list):
        result["tick_values"] = [
            _safe_decimal(value, "tick_values") if isinstance(value, str) else value
            for value in tick_values
        ]
    return result


def _coerce_agent(entry: Any) -> Any:
    if not isinstance(entry, Mapping):
        return entry
    result = dict(entry)
    params = result.get("params")
    if isinstance(params, Mapping):
        result["params"] = _coerce_agent_params(params)
    return result


def _coerce_agent_params(params: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = dict(params)
    rules = result.get("rules")
    if isinstance(rules, list):
        result["rules"] = [_coerce_rule(rule) for rule in rules]
    return result


def _coerce_command(entry: Any) -> Any:
    """ADR 0070 (Trigger 046): coerced `payload.value`/`power_kw` (str -> Decimal)
    nur fuer numerische Command-Typen (`COMMAND_DECIMAL_VALUE_TYPES`).
    `set_plug_state` o. Ae. bleibt unangetastet (String-Enum-Wert)."""
    if not isinstance(entry, Mapping):
        return entry
    result = dict(entry)
    if result.get("type") not in COMMAND_DECIMAL_VALUE_TYPES:
        return result
    payload = result.get("payload")
    if isinstance(payload, Mapping):
        result["payload"] = {
            key: (
                _safe_decimal(value, f"commands.payload.{key}")
                if key in _COMMAND_PAYLOAD_DECIMAL_KEYS and isinstance(value, str)
                else value
            )
            for key, value in payload.items()
        }
    return result


def _coerce_rule(rule: Any) -> Any:
    if not isinstance(rule, Mapping):
        return rule
    result = dict(rule)
    action = result.get("action")
    if isinstance(action, Mapping):
        action_dict = dict(action)
        payload = action_dict.get("payload")
        if isinstance(payload, Mapping):
            action_dict["payload"] = {
                key: (
                    _safe_decimal(value, f"action.payload.{key}")
                    if key in RULE_PAYLOAD_DECIMAL_KEYS and isinstance(value, str)
                    else value
                )
                for key, value in payload.items()
            }
        result["action"] = action_dict
    return result
