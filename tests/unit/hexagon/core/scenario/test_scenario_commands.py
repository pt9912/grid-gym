"""Pins fuer den scenario-scheduled `commands`-Block (S1, ADR 0070, Trigger 046).

Deckt Loader (Domain-Aufbau), Validator (Pflicht-Felder/Typen/Target-Existenz/
Float-Reject), `scenario_hash`-Pin-Neutralitaet (leerer Block = unveraendert,
non-empty = Hash verschiebt) und die typ-bewusste `scenario_yaml`-Decimal-
Coercion (numerischer Command-Value -> Decimal; `set_plug_state` bleibt String).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.errors import (
    ScenarioMissingKeysError,
    ScenarioUnknownCommandTargetError,
    ScenarioWrongTypeError,
    WrongTypeError,
)
from grid_gym.hexagon.core.scenario.loader import load_scenario
from grid_gym.scenario_yaml import coerce_scenario_mapping


def _scenario(commands: object | None = None) -> dict[str, object]:
    raw: dict[str, object] = {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "welle-cmd", "name": "Command Schedule Test"},
        "simulation": {"tick_ms": 1000, "duration_s": 60, "seed": 42},
        "devices": [
            {"id": "load-1", "type": "load", "params": {"rated_power_kw": Decimal("100")}},
        ],
    }
    if commands is not None:
        raw["commands"] = commands
    return raw


def _command(target: str = "load-1") -> dict[str, object]:
    return {
        "simulation_time": 5000,
        "target": target,
        "type": "set_power_kw",
        "payload": {"value": Decimal("20")},
    }


# --- Loader (Happy) --------------------------------------------------------


def test_load_scenario_populates_commands() -> None:
    loaded = load_scenario(_scenario(commands=[_command()]))
    assert len(loaded.scenario.commands) == 1
    command = loaded.scenario.commands[0]
    assert command.simulation_time == 5000
    assert command.target == "load-1"
    assert command.type == "set_power_kw"
    assert command.payload["value"] == Decimal("20")


def test_load_scenario_without_commands_defaults_to_empty() -> None:
    loaded = load_scenario(_scenario())
    assert loaded.scenario.commands == ()


# --- Validator (Negative) --------------------------------------------------


def test_load_scenario_rejects_command_with_unknown_target() -> None:
    raw = _scenario(commands=[_command(target="ghost-device-99")])
    with pytest.raises(ScenarioUnknownCommandTargetError) as exc_info:
        load_scenario(raw)
    assert "ghost-device-99" in str(exc_info.value)


def test_load_scenario_rejects_command_missing_required_key() -> None:
    command = _command()
    del command["simulation_time"]
    with pytest.raises(ScenarioMissingKeysError):
        load_scenario(_scenario(commands=[command]))


def test_load_scenario_rejects_commands_not_a_list() -> None:
    with pytest.raises(ScenarioWrongTypeError):
        load_scenario(_scenario(commands={"not": "a list"}))


def test_load_scenario_rejects_command_payload_float() -> None:
    """`float` an einer Payload-Stelle -> WrongTypeError (canonical-incompatible,
    GG-DATA-005); spiegelt die Fault-/Event-Payload-Pruefung."""
    command = _command()
    command["payload"] = {"value": 20.0}
    with pytest.raises(WrongTypeError):
        load_scenario(_scenario(commands=[command]))


# --- scenario_hash Pin-Neutralitaet ----------------------------------------


def test_empty_commands_is_pin_neutral_for_scenario_hash() -> None:
    """Kein `commands`-Block und ein leerer `commands: []`-Block ergeben denselben
    `scenario_hash` (opt-in pop in `_scenario_hash_payload`)."""
    baseline = load_scenario(_scenario()).scenario_hash
    with_empty = load_scenario(_scenario(commands=[])).scenario_hash
    assert with_empty == baseline


def test_non_empty_commands_shifts_scenario_hash() -> None:
    baseline = load_scenario(_scenario()).scenario_hash
    with_command = load_scenario(_scenario(commands=[_command()])).scenario_hash
    assert with_command != baseline


# --- scenario_yaml Decimal-Coercion (typ-bewusst) --------------------------


def test_coercion_sets_decimal_for_numeric_command_value() -> None:
    raw = _scenario(
        commands=[
            {
                "simulation_time": 5000,
                "target": "load-1",
                "type": "set_charge_power",
                "payload": {"value": "20"},
            }
        ]
    )
    coerced = coerce_scenario_mapping(raw)
    commands = coerced["commands"]
    assert isinstance(commands, list)
    assert commands[0]["payload"]["value"] == Decimal("20")


def test_coercion_leaves_plug_state_value_as_string() -> None:
    raw = _scenario(
        commands=[
            {
                "simulation_time": 5000,
                "target": "load-1",
                "type": "set_plug_state",
                "payload": {"value": "plugged"},
            }
        ]
    )
    coerced = coerce_scenario_mapping(raw)
    commands = coerced["commands"]
    assert isinstance(commands, list)
    assert commands[0]["payload"]["value"] == "plugged"


def test_coercion_passes_through_non_mapping_command_entry() -> None:
    """Defensiv: ein Nicht-Mapping-Eintrag bleibt unveraendert (der Validator
    wirft spaeter); spiegelt `_coerce_rule`/`_coerce_agent`."""
    coerced = coerce_scenario_mapping(_scenario(commands=["not-a-mapping"]))
    assert coerced["commands"] == ["not-a-mapping"]


def test_coercion_skips_command_with_non_mapping_payload() -> None:
    """Numerischer Command-Typ, aber `payload` kein Mapping -> unangetastet."""
    raw = _scenario(
        commands=[
            {"simulation_time": 1, "target": "load-1", "type": "set_power_kw", "payload": "oops"}
        ]
    )
    coerced = coerce_scenario_mapping(raw)
    commands = coerced["commands"]
    assert isinstance(commands, list)
    assert commands[0]["payload"] == "oops"
