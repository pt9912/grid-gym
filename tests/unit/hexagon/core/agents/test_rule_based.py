"""Tests fuer `RuleBasedAgent` (M3 Welle 4b, ADR 0027).

Pinnt:
- Rules-Pfad: first-match-wins, leerer Return bei keinem Match.
- Comparator-Vertrag (`<`, `<=`, `==`, `!=`, `>=`, `>`).
- Metric-Whitelist `tick` / `simulation_time`.
- Plugin-Pfad: delegiert an `AgentPlugin.decide`.
- Snapshot-Roundtrip-Vertrag (byte-stabil ueber canonical_json).
- set_run_id-Lifecycle.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pytest

from grid_gym.hexagon.core.agents import (
    Agent,
    AgentMessageBus,
    AgentPlugin,
    RuleBasedAgent,
)
from grid_gym.hexagon.core.agents.rule_based import (
    COMPARATOR_WHITELIST,
    WELLE_4B_METRIC_WHITELIST,
    Rule,
    RuleAction,
    RuleCondition,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext


def _ctx(tick: int, simulation_time: int = 0, tick_ms: int = 1000) -> DeviceTickContext:
    return DeviceTickContext(tick=tick, simulation_time=simulation_time, tick_ms=tick_ms)


def _rule(metric: str, comparator: str, threshold: int, command_type: str = "charge") -> Rule:
    return Rule(
        condition=RuleCondition(metric=metric, comparator=comparator, threshold=threshold),
        action=RuleAction(type=command_type, payload={"power_kw": "50"}),
    )


def test_rule_based_agent_implements_agent_protocol() -> None:
    """RuleBasedAgent erfuellt das Welle-3-Agent-Protocol."""
    agent = RuleBasedAgent(
        agent_id="bess", target_device_id="battery-1", rules=(_rule("tick", ">=", 5),)
    )
    assert isinstance(agent, Agent)


def test_rules_pfad_first_match_wins() -> None:
    """ADR 0027 §2.3: first-match-wins ueber die geordnete Rules-Tuple."""
    agent = RuleBasedAgent(
        agent_id="bess",
        target_device_id="battery-1",
        rules=(
            _rule("tick", ">=", 0, "first-rule"),
            _rule("tick", ">=", 0, "second-rule"),  # wuerde auch matchen
        ),
    )
    commands = agent.tick(_ctx(tick=5), AgentMessageBus())
    assert len(commands) == 1
    assert commands[0].type == "first-rule"


def test_rules_no_match_yields_empty_sequence() -> None:
    """Kein Match → leere Sequenz, kein Command."""
    agent = RuleBasedAgent(
        agent_id="bess",
        target_device_id="battery-1",
        rules=(_rule("tick", ">=", 100),),
    )
    assert agent.tick(_ctx(tick=5), AgentMessageBus()) == ()


@pytest.mark.parametrize(
    ("comparator", "tick_value", "threshold", "expected_match"),
    [
        ("<", 5, 10, True),
        ("<", 10, 10, False),
        ("<=", 10, 10, True),
        ("==", 10, 10, True),
        ("==", 11, 10, False),
        ("!=", 11, 10, True),
        ("!=", 10, 10, False),
        (">=", 10, 10, True),
        (">", 10, 10, False),
        (">", 11, 10, True),
    ],
)
def test_comparator_set_value_based(
    comparator: str, tick_value: int, threshold: int, expected_match: bool
) -> None:
    """ADR 0027 §2.3: Comparator-Whitelist wertbasiert."""
    agent = RuleBasedAgent(
        agent_id="bess",
        target_device_id="battery-1",
        rules=(_rule("tick", comparator, threshold),),
    )
    commands = agent.tick(_ctx(tick=tick_value), AgentMessageBus())
    assert (len(commands) == 1) is expected_match


def test_command_uses_context_simulation_time() -> None:
    """ADR 0027 §2.3: emittierte Commands tragen
    `context.simulation_time`, nicht den Threshold."""
    agent = RuleBasedAgent(
        agent_id="bess",
        target_device_id="battery-1",
        rules=(_rule("tick", ">=", 0),),
    )
    commands = agent.tick(_ctx(tick=5, simulation_time=12345), AgentMessageBus())
    assert commands[0].simulation_time == 12345
    assert commands[0].target_device_id == "battery-1"


def test_command_id_is_deterministic_per_tick_and_rule() -> None:
    """Command-ID nutzt agent_id + tick + rule_index → deterministisch."""
    agent = RuleBasedAgent(
        agent_id="bess",
        target_device_id="battery-1",
        rules=(_rule("tick", "<", 100, "first"), _rule("tick", ">=", 5, "second")),
    )
    commands = agent.tick(_ctx(tick=10), AgentMessageBus())
    assert commands[0].command_id == "rule_based_bess_tick_10_rule_0"


def test_metric_simulation_time_is_supported() -> None:
    """ADR 0027 §2.3 Welle-4b-Whitelist: `simulation_time` zulaessig."""
    agent = RuleBasedAgent(
        agent_id="bess",
        target_device_id="battery-1",
        rules=(_rule("simulation_time", ">=", 10000),),
    )
    no_match = agent.tick(_ctx(tick=0, simulation_time=5000), AgentMessageBus())
    match = agent.tick(_ctx(tick=0, simulation_time=10000), AgentMessageBus())
    assert no_match == ()
    assert len(match) == 1


def test_unknown_metric_does_not_match() -> None:
    """Defensive: bei `metric` ausserhalb der Welle-4b-Whitelist
    matched die Regel nicht (Validator haette das vorgelagert
    abgewiesen)."""
    agent = RuleBasedAgent(
        agent_id="bess",
        target_device_id="battery-1",
        rules=(_rule("voltage_v", ">=", 230),),
    )
    commands = agent.tick(_ctx(tick=10), AgentMessageBus())
    assert commands == ()


def test_set_run_id_sets_internal_state() -> None:
    """Welle-4a-Lifecycle-Hook (ADR 0026 §2.3): set_run_id wird
    vom TickLoop-Konstruktor via `_attach_agents()` aufgerufen."""
    agent = RuleBasedAgent(
        agent_id="bess", target_device_id="battery-1", rules=(_rule("tick", ">=", 0),)
    )
    agent.set_run_id("run-42")
    # No-op-Vertrag; nur sichergestellt, dass der Aufruf nicht raised.


def test_rule_based_agent_is_not_random_attachable_by_default() -> None:
    """RuleBasedAgent ist deterministisch → kein
    `_RandomAttachableAgent`-Sub-Protocol."""
    from grid_gym.hexagon.core.agents import _RandomAttachableAgent

    agent = RuleBasedAgent(
        agent_id="bess", target_device_id="battery-1", rules=(_rule("tick", ">=", 0),)
    )
    assert not isinstance(agent, _RandomAttachableAgent)


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip
# ---------------------------------------------------------------------------


def test_snapshot_contains_pflicht_keys() -> None:
    """ADR 0027 §2.4: Snapshot hat version + agent_id + target +
    rules + plugin + plugin_state."""
    agent = RuleBasedAgent(
        agent_id="bess", target_device_id="battery-1", rules=(_rule("tick", ">=", 5),)
    )
    snap = agent.snapshot()
    assert snap["version"] == 1
    assert snap["agent_id"] == "bess"
    assert snap["target_device_id"] == "battery-1"
    assert snap["plugin"] is None
    assert snap["plugin_state"] is None
    rules = snap["rules"]
    assert isinstance(rules, tuple)
    assert len(rules) == 1
    rule_dict = rules[0]
    assert rule_dict["condition"]["metric"] == "tick"
    assert rule_dict["condition"]["comparator"] == ">="
    assert rule_dict["condition"]["threshold"] == 5
    assert rule_dict["action"]["type"] == "charge"


def test_from_snapshot_roundtrip_is_byte_stable() -> None:
    """Snapshot → from_snapshot → snapshot ist byte-stabil
    (ADR 0013 §2.4-Pattern)."""
    agent = RuleBasedAgent(
        agent_id="bess",
        target_device_id="battery-1",
        rules=(
            _rule("tick", ">=", 5, "charge"),
            _rule("simulation_time", "<", 1000, "idle"),
        ),
    )
    snap1 = agent.snapshot()
    restored = RuleBasedAgent.from_snapshot(snap1)
    snap2 = restored.snapshot()
    assert snap1 == snap2
    assert restored.agent_id == "bess"
    assert restored.target_device_id == "battery-1"
    assert len(restored.rules) == 2


def test_from_snapshot_rejects_wrong_version() -> None:
    """Snapshot-Version-Drift wirft typisiert."""
    from grid_gym.hexagon.core.errors import VersionError

    bad = {
        "version": 999,
        "agent_id": "bess",
        "target_device_id": "battery-1",
        "rules": (),
        "plugin": None,
        "plugin_state": None,
    }
    with pytest.raises(VersionError):
        RuleBasedAgent.from_snapshot(bad)


def test_from_snapshot_rejects_wrong_type_threshold() -> None:
    """ADR 0027 §2.3: `threshold` muss int sein."""
    from grid_gym.hexagon.core.errors import WrongTypeError

    bad = {
        "version": 1,
        "agent_id": "bess",
        "target_device_id": "battery-1",
        "rules": (
            {
                "condition": {"metric": "tick", "comparator": ">=", "threshold": "5"},  # str
                "action": {"type": "charge", "payload": {"power_kw": "50"}},
            },
        ),
        "plugin": None,
        "plugin_state": None,
    }
    with pytest.raises(WrongTypeError):
        RuleBasedAgent.from_snapshot(bad)


def _base_snapshot() -> dict[str, object]:
    return {
        "version": 1,
        "agent_id": "bess",
        "target_device_id": "battery-1",
        "rules": (),
        "plugin": None,
        "plugin_state": None,
    }


@pytest.mark.parametrize(
    ("key", "bad_value"),
    [
        ("agent_id", 123),  # non-str
        ("target_device_id", 123),  # non-str-non-None
        ("rules", "not-a-list"),  # str instead of Sequence
        ("plugin", 123),  # non-str-non-None
    ],
)
def test_from_snapshot_rejects_wrong_type_per_field(key: str, bad_value: object) -> None:
    """ADR 0027 §2.4: pro Pflichtfeld Type-Check."""
    from grid_gym.hexagon.core.errors import WrongTypeError

    snap = _base_snapshot()
    snap[key] = bad_value
    with pytest.raises(WrongTypeError):
        RuleBasedAgent.from_snapshot(snap)


def test_apply_comparator_unknown_returns_false() -> None:
    """ADR 0027 §2.3 Defensive: unknown comparator → False (Validator
    haette das vorher abgewiesen)."""
    from grid_gym.hexagon.core.agents.rule_based import _apply_comparator

    assert _apply_comparator(5, "approximately", 10) is False


@pytest.mark.parametrize(
    ("missing_path", "rule_override"),
    [
        # condition fehlt
        (
            "condition",
            {"action": {"type": "charge", "payload": {}}},
        ),
        # action fehlt
        (
            "action",
            {"condition": {"metric": "tick", "comparator": ">=", "threshold": 0}},
        ),
    ],
)
def test_rule_from_mapping_rejects_non_mapping_per_field(
    missing_path: str, rule_override: dict[str, object]
) -> None:
    """ADR 0027 §2.3: condition/action Pflicht-Keys; fehlt einer →
    typisierter Reject."""
    from grid_gym.hexagon.core.errors import WrongTypeError

    snap = _base_snapshot()
    snap["rules"] = (rule_override,)
    with pytest.raises(WrongTypeError):
        RuleBasedAgent.from_snapshot(snap)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("metric", 123),
        ("comparator", 123),
        ("threshold", "5"),  # str instead of int
    ],
)
def test_rule_from_mapping_rejects_wrong_type_in_condition(field: str, bad_value: object) -> None:
    """ADR 0027 §2.3: pro Condition-Feld Type-Check (defensive
    Welle-0a-Codec-Pattern)."""
    from grid_gym.hexagon.core.errors import WrongTypeError

    snap = _base_snapshot()
    condition: dict[str, object] = {"metric": "tick", "comparator": ">=", "threshold": 0}
    condition[field] = bad_value
    snap["rules"] = (
        {"condition": condition, "action": {"type": "charge", "payload": {}}},
    )
    with pytest.raises(WrongTypeError):
        RuleBasedAgent.from_snapshot(snap)


def test_rule_from_mapping_rejects_non_mapping_payload() -> None:
    """ADR 0027 §2.3: action.payload muss Mapping sein."""
    from grid_gym.hexagon.core.errors import WrongTypeError

    snap = _base_snapshot()
    snap["rules"] = (
        {
            "condition": {"metric": "tick", "comparator": ">=", "threshold": 0},
            "action": {"type": "charge", "payload": "not-a-mapping"},
        },
    )
    with pytest.raises(WrongTypeError):
        RuleBasedAgent.from_snapshot(snap)


def test_rule_from_mapping_rejects_non_mapping_entry() -> None:
    """ADR 0027 §2.3: rules-Eintrag muss Mapping sein."""
    from grid_gym.hexagon.core.errors import WrongTypeError

    snap = _base_snapshot()
    snap["rules"] = ("not-a-mapping",)
    with pytest.raises(WrongTypeError):
        RuleBasedAgent.from_snapshot(snap)


# ---------------------------------------------------------------------------
# Plugin-Pfad
# ---------------------------------------------------------------------------


class _StubPlugin:
    """Test-Stub fuer AgentPlugin-Surface (ADR 0027 §2.3)."""

    SNAPSHOT_VERSION = 1

    def __init__(self, recorded_calls: list[int]) -> None:
        self.recorded_calls = recorded_calls

    def decide(
        self,
        context: DeviceTickContext,
        bus: AgentMessageBus,
        params: Mapping[str, object],
    ) -> Sequence[Command]:
        del bus, params
        self.recorded_calls.append(context.tick)
        return (
            Command(
                command_id=f"plugin_tick_{context.tick}",
                simulation_time=context.simulation_time,
                target_device_id="battery-1",
                type="plugin_action",
                payload={},
                validation_status="validated",
                result=CommandResult.IGNORED,
            ),
        )

    def snapshot(self) -> Mapping[str, object]:
        return {"version": self.SNAPSHOT_VERSION, "calls": tuple(self.recorded_calls)}

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> "_StubPlugin":
        calls_raw = state.get("calls", ())
        assert isinstance(calls_raw, (list, tuple))
        return cls(recorded_calls=list(calls_raw))


def test_plugin_is_protocol_compliant() -> None:
    """`_StubPlugin` erfuellt `AgentPlugin` strukturell."""
    plugin = _StubPlugin(recorded_calls=[])
    assert isinstance(plugin, AgentPlugin)


def test_plugin_path_delegates_decide() -> None:
    """ADR 0027 §2.3: Plugin-Pfad ruft `plugin.decide(...)`."""
    recorded: list[int] = []
    plugin = _StubPlugin(recorded_calls=recorded)
    agent = RuleBasedAgent(
        agent_id="bess",
        plugin=plugin,
        plugin_name="stub_v1",
        plugin_params={"param-a": "value"},
    )
    commands = agent.tick(_ctx(tick=7), AgentMessageBus())
    assert recorded == [7]
    assert len(commands) == 1
    assert commands[0].type == "plugin_action"


def test_plugin_snapshot_serializes_plugin_state() -> None:
    """ADR 0027 §2.4: Plugin-Pfad serialisiert plugin_name + plugin_state."""
    plugin = _StubPlugin(recorded_calls=[1, 2, 3])
    agent = RuleBasedAgent(
        agent_id="bess",
        plugin=plugin,
        plugin_name="stub_v1",
        plugin_params={"param-a": "value"},
    )
    snap = agent.snapshot()
    assert snap["plugin"] == "stub_v1"
    assert snap["plugin_state"] == {"version": 1, "calls": (1, 2, 3)}
    assert snap["target_device_id"] is None
    assert snap["rules"] == ()
