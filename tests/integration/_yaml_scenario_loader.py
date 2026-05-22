"""Test-seitiger YAML-Loader fuer M2-Welle-6c-Integrationstests.

Konvertiert eine YAML-Datei in das vom Core erwartete
`Mapping[str, object]` mit `Decimal`-coerced numerischen Feldern
und ruft anschliessend `load_scenario(...)`.

Welle-6c-Anti-Scope: dies ist KEIN produktiver Adapter unter
`src/`. ADR 0021 §2.1 haelt YAML-File-Parsing als
Adapter-Verantwortung ausserhalb von `core/scenario/`. Bis ein
produktiver Adapter geplant wird (eigenes Slice + ADR), bleibt
die Konvertierung auf die Integrationstest-Infrastruktur
beschraenkt.

Konvertierungsregel: ausschliesslich `str` → `Decimal`. Floats
in den Quelldaten werden vom Scenario-Validator typisiert
abgelehnt (`ScenarioWrongTypeError`); Praezisionsverluste sind
damit konstruktiv ausgeschlossen (`GG-DATA-005`).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from grid_gym.hexagon.core.scenario.loader import LoadedScenario, load_scenario

_DEVICE_DECIMAL_PARAMS: frozenset[str] = frozenset(
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
    }
)

_GRID_MODEL_DECIMAL_FIELDS: frozenset[str] = frozenset(
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

_LOAD_EVENT_DECIMAL_FIELDS: frozenset[str] = frozenset({"start_s", "duration_s", "power_kw"})


def load_yaml_scenario(path: Path) -> LoadedScenario:
    """Laedt eine YAML-Szenariodatei und konvertiert sie nach Decimal."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"YAML root must be a mapping; got {type(raw).__name__} from {path}")
    return load_scenario(_coerce_decimals(raw))


def _coerce_decimals(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Schema-bewusste Decimal-Konvertierung.

    Welle-6c-Review M-4: Nicht-Mapping/Nicht-List-Strukturen werden
    **unveraendert** durchgereicht (`raw["devices"] = "not-a-list"`
    fliesst durch und triggert anschliessend
    `ScenarioWrongTypeError` im Validator), statt einen opaken
    `ValueError` aus `dict(non-mapping)` zu erzeugen.
    """
    result: dict[str, Any] = dict(raw)

    devices = result.get("devices")
    if isinstance(devices, list):
        result["devices"] = [_coerce_device(entry) for entry in devices]

    grid_model = result.get("grid_model")
    if isinstance(grid_model, Mapping):
        result["grid_model"] = _coerce_decimal_fields(grid_model, _GRID_MODEL_DECIMAL_FIELDS)

    load_events = result.get("load_events")
    if isinstance(load_events, list):
        result["load_events"] = [_coerce_load_event(entry) for entry in load_events]

    load_profiles = result.get("load_profiles")
    if isinstance(load_profiles, list):
        result["load_profiles"] = [_coerce_load_profile(entry) for entry in load_profiles]

    # M3-Welle-4b (ADR 0027): agents-Block payload-Decimal-Coercion.
    agents = result.get("agents")
    if isinstance(agents, Mapping):
        result["agents"] = {
            agent_id: _coerce_agent(agent_def) for agent_id, agent_def in agents.items()
        }

    return result


def _coerce_device(entry: Any) -> Any:
    """Welle-6c-Review M-4: Non-Mapping wird durchgereicht — der
    Scenario-Validator wirft anschliessend `ScenarioWrongTypeError`
    mit Pfad `devices[i]`."""
    if not isinstance(entry, Mapping):
        return entry
    result = dict(entry)
    params = result.get("params")
    if isinstance(params, Mapping):
        result["params"] = _coerce_decimal_fields(params, _DEVICE_DECIMAL_PARAMS)
    return result


def _coerce_decimal_fields(
    entry: Mapping[str, Any], decimal_fields: frozenset[str]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in entry.items():
        if key in decimal_fields and isinstance(value, str):
            result[key] = Decimal(value)
        else:
            result[key] = value
    return result


def _coerce_load_event(entry: Any) -> Any:
    """Welle-6c-Review M-4: Non-Mapping wird durchgereicht."""
    if not isinstance(entry, Mapping):
        return entry
    return _coerce_decimal_fields(entry, _LOAD_EVENT_DECIMAL_FIELDS)


def _coerce_load_profile(entry: Any) -> Any:
    """Welle-6c-Review M-4: Non-Mapping wird durchgereicht."""
    if not isinstance(entry, Mapping):
        return entry
    result = dict(entry)
    tick_values = result.get("tick_values")
    if isinstance(tick_values, list):
        result["tick_values"] = [
            Decimal(value) if isinstance(value, str) else value for value in tick_values
        ]
    return result


# Welle-4b-Helper fuer agents-Block. Decimal-Coercion ist
# pflicht-pragmatisch: Rule-`action.payload` enthaelt typisch
# physikalische Werte (`value: "20"` fuer `set_power_kw`), die
# der TickLoop an `Device.apply_command` weiterreicht (erwartet
# Decimal). Welle-4b-Schema-Coercion ist nur fuer den
# `action.payload`-Strang aktiv; Conditions sind int-typed.
_RULE_PAYLOAD_DECIMAL_KEYS: frozenset[str] = frozenset(
    {
        "value",
        "power_kw",
    }
)


def _coerce_agent(entry: Any) -> Any:
    """Welle-4b: konvertiert Decimal-Strings im `params.rules[*]
    .action.payload`-Strang nach `Decimal`."""
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
                    Decimal(value)
                    if key in _RULE_PAYLOAD_DECIMAL_KEYS and isinstance(value, str)
                    else value
                )
                for key, value in payload.items()
            }
        result["action"] = action_dict
    return result
