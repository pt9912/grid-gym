"""Tests fuer `_build_agents` + `build_tick_loop(agents=)`-Defaultierung
aus `scenario.agents` (M3 Welle 4b, ADR 0027 §2.2).

Pinnt:
- `_build_agents` dispatcht ueber `_AGENT_FACTORIES`.
- Unknown-Type → `ScenarioUnknownAgentTypeError`.
- Plugin-Pfad ohne registrierte Factory → `ScenarioUnknownAgentPluginError`.
- `build_tick_loop` defaultet `agents` aus `scenario.agents`, wenn
  kein Override geliefert ist; expliziter Override gewinnt.
- `load_scenario` befuellt `Scenario.agents` aus dem nested
  YAML-Block in lexikographischer Reihenfolge.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.agents import RuleBasedAgent
from grid_gym.hexagon.core.domain.scenario import (
    Scenario,
    ScenarioAgent,
    ScenarioDevice,
    ScenarioMetadata,
    ScenarioSimulation,
)
from grid_gym.hexagon.core.errors import (
    ScenarioUnknownAgentPluginError,
    ScenarioUnknownAgentTypeError,
)
from grid_gym.hexagon.core.scenario.loader import (
    _build_agents,
    build_tick_loop,
    load_scenario,
)
from tests.unit.hexagon.ports.driven._fakes import FakeClock


def _battery_device(device_id: str = "battery-1") -> ScenarioDevice:
    return ScenarioDevice(
        id=device_id,
        type="battery",
        params={
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
    )


def _rule_based_agent(agent_id: str = "bess") -> ScenarioAgent:
    return ScenarioAgent(
        id=agent_id,
        type="rule_based",
        params={
            "target_device_id": "battery-1",
            "rules": [
                {
                    "condition": {"metric": "tick", "comparator": ">=", "threshold": 0},
                    "action": {"type": "charge", "payload": {"power_kw": "50"}},
                },
            ],
        },
    )


def _scenario_with_agents(agents: tuple[ScenarioAgent, ...]) -> Scenario:
    return Scenario(
        schema_version="grid-gym.scenario.v1",
        metadata=ScenarioMetadata(id="w4b", name="Welle 4b Loader Test"),
        simulation=ScenarioSimulation(tick_ms=1000, duration_s=60, seed=42),
        devices=(_battery_device(),),
        events=(),
        replay=None,
        faults=(),
        agents=agents,
    )


def test_build_agents_dispatches_rule_based_factory() -> None:
    """ADR 0027 §2.2: `_AGENT_FACTORIES["rule_based"]` liefert `RuleBasedAgent`."""
    agents = _build_agents((_rule_based_agent(),))
    assert len(agents) == 1
    assert isinstance(agents[0], RuleBasedAgent)
    assert agents[0].agent_id == "bess"


def test_build_agents_rejects_unknown_type() -> None:
    """Unknown `type` → `ScenarioUnknownAgentTypeError`."""
    unknown = ScenarioAgent(id="x", type="ml_policy", params={"target_device_id": "battery-1"})
    with pytest.raises(ScenarioUnknownAgentTypeError):
        _build_agents((unknown,))


def test_build_agents_rejects_unknown_plugin() -> None:
    """ADR 0027 §2.3: `plugin: "<name>"` ohne registrierte Factory
    → `ScenarioUnknownAgentPluginError` (Welle 4b ist leer)."""
    plugin_agent = ScenarioAgent(id="bess", type="rule_based", params={"plugin": "ghost_plugin"})
    with pytest.raises(ScenarioUnknownAgentPluginError):
        _build_agents((plugin_agent,))


def test_build_tick_loop_defaults_agents_from_scenario() -> None:
    """ADR 0027 §2.2: ohne expliziten `agents=`-Kwarg leitet der
    Builder das Tuple aus `scenario.agents` ab."""
    scenario = _scenario_with_agents((_rule_based_agent(),))
    loop = build_tick_loop(
        scenario,
        run_id="run-w4b",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
    )
    assert len(loop._agents) == 1  # type: ignore[attr-defined]
    assert isinstance(loop._agents[0], RuleBasedAgent)  # type: ignore[attr-defined]
    # Auto-Bus-Regel von Welle 4a aktiv:
    assert loop._agent_bus is not None  # type: ignore[attr-defined]


def test_build_tick_loop_explicit_agents_override_scenario() -> None:
    """Expliziter `agents=`-Override gewinnt gegen `scenario.agents`."""
    scenario = _scenario_with_agents((_rule_based_agent("scenario-agent"),))
    custom_agent = RuleBasedAgent(
        agent_id="custom-agent",
        target_device_id="battery-1",
        rules=(),
    )
    # Da `rules=()`-Konstruktor das normalerweise zu „kein
    # Decision-Pfad" macht, faengt der Validator das ab — der
    # TickLoop-Konstruktor akzeptiert das aber (keine Welle-4a-
    # Pflicht, dass Rules nicht leer sein duerfen).
    # Wir nutzen das nur zur Override-Demo.
    loop = build_tick_loop(
        scenario,
        run_id="run-w4b",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
        agents=(custom_agent,),
    )
    assert len(loop._agents) == 1  # type: ignore[attr-defined]
    assert loop._agents[0].agent_id == "custom-agent"  # type: ignore[attr-defined]


def test_build_tick_loop_explicit_empty_tuple_yields_agentless_run() -> None:
    """ADR 0027 §2.2 + Welle-4b-Review-Folge F-1 (2026-05-22):
    expliziter `agents=()` (leeres Tupel) wird vom Builder als
    „agentenloser Run" respektiert, auch wenn `scenario.agents`
    nicht-leer ist. Vorher hatte `not agents`-Check das
    silent zu `_build_agents(scenario.agents)` umgeleitet."""
    scenario = _scenario_with_agents((_rule_based_agent(),))
    loop = build_tick_loop(
        scenario,
        run_id="run-w4b-empty",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
        agents=(),  # explizit leer
    )
    assert loop._agents == ()  # type: ignore[attr-defined]
    # Auto-Bus-Regel ist Welle-4a-Verantwortung: bei agents=()
    # wird kein Bus angelegt.
    assert loop._agent_bus is None  # type: ignore[attr-defined]


def test_build_tick_loop_none_agents_derives_from_scenario() -> None:
    """ADR 0027 §2.2 + Welle-4b-Review-Folge F-1: `agents=None`-
    Sentinel triggert Scenario-Defaultierung (kanonischer Pfad)."""
    scenario = _scenario_with_agents((_rule_based_agent(),))
    loop = build_tick_loop(
        scenario,
        run_id="run-w4b-derived",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
        # agents nicht angegeben → None-Default → derive
    )
    assert len(loop._agents) == 1  # type: ignore[attr-defined]
    assert loop._agents[0].agent_id == "bess"  # type: ignore[attr-defined]


def test_load_scenario_populates_agents_in_lex_order() -> None:
    """ADR 0027 §2.1: `agents`-Dict-Keys werden lexikographisch
    sortiert in den Tuple gemappt."""
    raw: dict[str, object] = {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "w4b", "name": "Lex order"},
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
        # YAML-Insertion-Order: zebra zuerst, alpha danach
        "agents": {
            "zebra-agent": {
                "type": "rule_based",
                "params": {
                    "target_device_id": "battery-1",
                    "rules": [
                        {
                            "condition": {"metric": "tick", "comparator": ">=", "threshold": 0},
                            "action": {"type": "charge", "payload": {}},
                        },
                    ],
                },
            },
            "alpha-agent": {
                "type": "rule_based",
                "params": {
                    "target_device_id": "battery-1",
                    "rules": [
                        {
                            "condition": {"metric": "tick", "comparator": ">=", "threshold": 0},
                            "action": {"type": "discharge", "payload": {}},
                        },
                    ],
                },
            },
        },
    }
    loaded = load_scenario(raw)
    assert [a.id for a in loaded.scenario.agents] == ["alpha-agent", "zebra-agent"]
