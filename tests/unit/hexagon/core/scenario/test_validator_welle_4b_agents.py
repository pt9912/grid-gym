"""Tests fuer den `_assert_agent_list`-Validator (M3 Welle 4b, ADR 0027 §2.2).

Pinnt:
- Optionaler nested `agents`-Block (Default: keine agents).
- Pflicht-Keys pro Eintrag (`type`, `params`).
- `target_device_id`-Existenz-Check gegen `devices`.
- Mutual Exclusivity Rules ODER Plugin (ADR 0027 §2.3 / F-5).
- Rules-Block Schema (Comparator-Whitelist + Metric-Whitelist).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.errors import (
    ScenarioInvalidAgentParamsError,
    ScenarioInvalidRuleComparatorError,
    ScenarioInvalidRuleMetricError,
    ScenarioMissingKeysError,
    ScenarioUnknownAgentTargetError,
    ScenarioWrongTypeError,
)
from grid_gym.hexagon.core.scenario.validator import validate_scenario_mapping


def _minimal_raw() -> dict[str, object]:
    return {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "welle-4b-test", "name": "Welle 4b Validator Tests"},
        "simulation": {"tick_ms": 1000, "duration_s": 60, "seed": 42},
        "devices": [
            {
                "id": "battery-1",
                "type": "battery",
                "params": {
                    "capacity_kwh": Decimal("100"),
                    "initial_soc_pct": Decimal("50"),
                    "min_soc_pct": Decimal("0"),
                    "max_soc_pct": Decimal("100"),
                    "max_charge_kw": Decimal("50"),
                    "max_discharge_kw": Decimal("50"),
                    "charge_efficiency": Decimal("1"),
                    "discharge_efficiency": Decimal("1"),
                    "ramp_kw_per_s": Decimal("100"),
                },
            },
        ],
    }


def _valid_rule(threshold: int = 5) -> dict[str, object]:
    return {
        "condition": {"metric": "tick", "comparator": ">=", "threshold": threshold},
        "action": {"type": "charge", "payload": {"power_kw": "50"}},
    }


def test_validator_accepts_missing_agents_block() -> None:
    """Optionaler Block — fehlt der Top-Level-Key, ist's gueltig."""
    raw = _minimal_raw()
    validate_scenario_mapping(raw)  # darf nicht raisen


def test_validator_accepts_valid_agents_block_rules_path() -> None:
    """Rules-Pfad mit gueltigem target + min. einer Regel."""
    raw = _minimal_raw()
    raw["agents"] = {
        "bess-controller": {
            "type": "rule_based",
            "params": {
                "target_device_id": "battery-1",
                "rules": [_valid_rule()],
            },
        },
    }
    validate_scenario_mapping(raw)


def test_validator_accepts_valid_agents_block_plugin_path() -> None:
    """Plugin-Pfad mit plugin-Name + plugin_params."""
    raw = _minimal_raw()
    raw["agents"] = {
        "bess-controller": {
            "type": "rule_based",
            "params": {
                "plugin": "stub_v1",
                "plugin_params": {"k": "v"},
            },
        },
    }
    validate_scenario_mapping(raw)


def test_validator_rejects_agents_not_mapping() -> None:
    """`agents` muss Mapping sein."""
    raw = _minimal_raw()
    raw["agents"] = []  # type: ignore[assignment]
    with pytest.raises(ScenarioWrongTypeError):
        validate_scenario_mapping(raw)


def test_validator_rejects_missing_type_key() -> None:
    """Pflicht-Keys: `type` fehlt."""
    raw = _minimal_raw()
    raw["agents"] = {
        "bess": {"params": {"target_device_id": "battery-1", "rules": [_valid_rule()]}}
    }
    with pytest.raises(ScenarioMissingKeysError):
        validate_scenario_mapping(raw)


def test_validator_rejects_unknown_target() -> None:
    """ADR 0027 §2.2: target_device_id muss existieren."""
    raw = _minimal_raw()
    raw["agents"] = {
        "bess": {
            "type": "rule_based",
            "params": {"target_device_id": "ghost-device", "rules": [_valid_rule()]},
        },
    }
    with pytest.raises(ScenarioUnknownAgentTargetError):
        validate_scenario_mapping(raw)


def test_validator_rejects_both_rules_and_plugin() -> None:
    """ADR 0027 §2.3: Mutual Exclusivity — nicht beide."""
    raw = _minimal_raw()
    raw["agents"] = {
        "bess": {
            "type": "rule_based",
            "params": {
                "target_device_id": "battery-1",
                "rules": [_valid_rule()],
                "plugin": "stub_v1",
            },
        },
    }
    with pytest.raises(ScenarioInvalidAgentParamsError, match="sowohl"):
        validate_scenario_mapping(raw)


def test_validator_rejects_neither_rules_nor_plugin() -> None:
    """ADR 0027 §2.3 (F-5): weder Rules noch Plugin — kein Decision-Pfad."""
    raw = _minimal_raw()
    raw["agents"] = {
        "bess": {"type": "rule_based", "params": {"target_device_id": "battery-1"}},
    }
    with pytest.raises(ScenarioInvalidAgentParamsError, match="weder"):
        validate_scenario_mapping(raw)


def test_validator_rejects_empty_rules_list() -> None:
    """ADR 0027 §2.3: leere Rules-Liste ist kein gueltiger Decision-Pfad."""
    raw = _minimal_raw()
    raw["agents"] = {
        "bess": {
            "type": "rule_based",
            "params": {"target_device_id": "battery-1", "rules": []},
        },
    }
    with pytest.raises(ScenarioInvalidAgentParamsError, match="leer"):
        validate_scenario_mapping(raw)


def test_validator_rejects_unknown_comparator() -> None:
    """ADR 0027 §2.3: Comparator muss in Whitelist."""
    raw = _minimal_raw()
    bad_rule = _valid_rule()
    bad_rule["condition"] = {"metric": "tick", "comparator": "approximately", "threshold": 5}
    raw["agents"] = {
        "bess": {
            "type": "rule_based",
            "params": {"target_device_id": "battery-1", "rules": [bad_rule]},
        },
    }
    with pytest.raises(ScenarioInvalidRuleComparatorError):
        validate_scenario_mapping(raw)


def test_validator_rejects_unknown_metric() -> None:
    """ADR 0027 §2.3 Welle-4b-Metric-Whitelist."""
    raw = _minimal_raw()
    bad_rule = _valid_rule()
    bad_rule["condition"] = {"metric": "state_of_charge_pct", "comparator": "<", "threshold": 20}
    raw["agents"] = {
        "bess": {
            "type": "rule_based",
            "params": {"target_device_id": "battery-1", "rules": [bad_rule]},
        },
    }
    with pytest.raises(ScenarioInvalidRuleMetricError):
        validate_scenario_mapping(raw)


def test_validator_rejects_non_int_threshold() -> None:
    """ADR 0027 §2.3: `threshold` muss int sein (Welle 4b int-Vergleich)."""
    raw = _minimal_raw()
    bad_rule = _valid_rule()
    bad_rule["condition"] = {"metric": "tick", "comparator": ">=", "threshold": "5"}  # str
    raw["agents"] = {
        "bess": {
            "type": "rule_based",
            "params": {"target_device_id": "battery-1", "rules": [bad_rule]},
        },
    }
    with pytest.raises(ScenarioWrongTypeError):
        validate_scenario_mapping(raw)


def test_validator_accepts_two_agents_with_distinct_ids() -> None:
    """Mehrere Agents im Block sind zulaessig."""
    raw = _minimal_raw()
    raw["agents"] = {
        "bess-controller": {
            "type": "rule_based",
            "params": {"target_device_id": "battery-1", "rules": [_valid_rule()]},
        },
        "grid-watcher": {
            "type": "rule_based",
            "params": {"target_device_id": "battery-1", "rules": [_valid_rule(threshold=10)]},
        },
    }
    validate_scenario_mapping(raw)
