"""Tests fuer `agents.<agent_type>.<agent_id>`-Sub-Snapshots in
`TickLoop` (M3 Welle 4b, ADR 0027 §2.4).

Pinnt:
- Snapshot enthaelt `agents.rule_based.<id>` pro registriertem
  RuleBasedAgent.
- `from_snapshot(..., agents=...)` Roundtrip ist byte-stabil.
- Bidirektionaler Resume-Match: jeder injizierte Agent hat einen
  Slot; jeder Slot hat einen injizierten Agent.
"""

from __future__ import annotations

import pytest

from grid_gym.hexagon.core.agents import AgentMessageBus, RuleBasedAgent, RuleBasedAgentConfig
from grid_gym.hexagon.core.agents.rule_based import (
    Rule,
    RuleAction,
    RuleCondition,
)
from grid_gym.hexagon.core.errors import (
    TickLoopAgentInstanceSnapshotMismatchError,
)
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


def _rba(agent_id: str, target: str = "battery-1") -> RuleBasedAgent:
    return RuleBasedAgent(
        RuleBasedAgentConfig(
            agent_id=agent_id,
            target_device_id=target,
            rules=(
                Rule(
                    condition=RuleCondition(metric="tick", comparator=">=", threshold=0),
                    action=RuleAction(type="charge", payload={"power_kw": "50"}),
                ),
            ),
        )
    )


def _make_loop(*, agents: tuple = ()) -> TickLoop:
    return TickLoop(
        run_id="welle-4b-snap",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        agents=agents,
    )


def test_snapshot_emits_agents_sub_snapshot_per_instance() -> None:
    """ADR 0027 §2.4: Schreib-Pfad emittiert `agents.<type>.<id>`-Slot."""
    agent_a = _rba("bess-a")
    agent_b = _rba("bess-b")
    loop = _make_loop(agents=(agent_a, agent_b))
    snap = loop.snapshot()
    sub = snap["sub_snapshots"]
    assert isinstance(sub, dict)
    assert "agents.rule_based.bess-a" in sub
    assert "agents.rule_based.bess-b" in sub


def test_from_snapshot_roundtrip_with_agents() -> None:
    """ADR 0027 §2.4: Roundtrip mit injizierten Agents im exakten
    Snapshot-State ist gueltig."""
    agent = _rba("bess")
    loop = _make_loop(agents=(agent,))
    snap = loop.snapshot()
    restored_agent = _rba("bess")
    restored = TickLoop.from_snapshot(
        snap,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        agents=(restored_agent,),
    )
    assert restored.run_id == "welle-4b-snap"


def test_from_snapshot_rejects_subset_of_injected_agents() -> None:
    """ADR 0027 §2.4 + Welle-4a-Review-Folge (bidirektional):
    Snapshot mit 2 Agents, nur 1 injiziert → Mismatch."""
    loop = _make_loop(agents=(_rba("bess-a"), _rba("bess-b")))
    snap = loop.snapshot()
    with pytest.raises(TickLoopAgentInstanceSnapshotMismatchError):
        TickLoop.from_snapshot(
            snap,
            clock=FakeClock(),
            random=FixedSeedRandom(seed=42),
            agents=(_rba("bess-a"),),  # bess-b fehlt
        )


def test_from_snapshot_rejects_missing_snapshot_slot() -> None:
    """ADR 0027 §2.4: injizierter Agent ohne passenden Snapshot-Slot."""
    loop = _make_loop(agents=(_rba("bess-a"),))
    snap = loop.snapshot()
    with pytest.raises(TickLoopAgentInstanceSnapshotMismatchError):
        TickLoop.from_snapshot(
            snap,
            clock=FakeClock(),
            random=FixedSeedRandom(seed=42),
            agents=(_rba("bess-a"), _rba("ghost-agent")),
        )


def test_from_snapshot_rejects_snapshot_state_mismatch() -> None:
    """ADR 0027 §2.4: injizierter Agent mit gleicher ID aber
    abweichendem State → Mismatch."""
    loop = _make_loop(agents=(_rba("bess-a"),))
    snap = loop.snapshot()
    # Restored mit ABWEICHENDER Rule (anderer threshold).
    drifted = RuleBasedAgent(
        RuleBasedAgentConfig(
            agent_id="bess-a",
            target_device_id="battery-1",
            rules=(
                Rule(
                    condition=RuleCondition(metric="tick", comparator=">=", threshold=999),
                    action=RuleAction(type="charge", payload={"power_kw": "50"}),
                ),
            ),
        )
    )
    with pytest.raises(TickLoopAgentInstanceSnapshotMismatchError):
        TickLoop.from_snapshot(
            snap,
            clock=FakeClock(),
            random=FixedSeedRandom(seed=42),
            agents=(drifted,),
        )


def test_no_agents_path_skips_resume_match() -> None:
    """Ohne injizierte Agents bleibt der Resume-Pfad Welle-4a-
    konform — kein Match-Check, kein Crash."""
    loop = _make_loop()
    snap = loop.snapshot()
    TickLoop.from_snapshot(snap, clock=FakeClock(), random=FixedSeedRandom(seed=42))


def test_tick_with_rule_based_agent_emits_command_in_next_tick() -> None:
    """Welle-4a-Drain (A0v/A0a) wirkt produktiv mit RuleBasedAgent:
    Tick 1 emittiert Command (Buffer=1). Tick 2 wendet Vorgaenger
    an (Buffer-clear nach A0a) UND emittiert in D2 erneut
    (Rule matched permanent, Buffer=1).

    Welle-4b-Test-Pattern: nutzt `NullDevice` als Target (analog
    test_tick_loop_welle_4a_drain.py) — Welle-4b-Snapshot-Tests
    haben Device-Integration-Test-Scope ausgelagert
    (Demo-Szenario laeuft End-to-End via Integration-Test).
    """
    from grid_gym.hexagon.core.domain.scenario import ScenarioDevice

    from tests.unit.hexagon.core.devices._fakes import NullDevice

    device = NullDevice()
    device.initialize(
        ScenarioDevice(id="battery-1", type="null", params={}),
        FixedSeedRandom(seed=1),
    )
    agent = _rba("bess")
    loop = TickLoop(
        run_id="welle-4b-drain",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=(device,),
        agents=(agent,),
        agent_bus=AgentMessageBus(),
    )
    # Tick 1: Agent emittiert Command in Schritt D2 → Buffer hat 1 cmd.
    loop.tick()
    pending_after_tick1 = loop.pending_agent_commands
    assert len(pending_after_tick1) == 1
    cmd_id_tick0 = pending_after_tick1[0].command_id
    # Tick 2: A0a wendet vorigen Command an UND D2 emittiert
    # erneut → Buffer enthaelt JETZT Tick-1-Command (vom soeben
    # gelaufenen D2-Schritt), NICHT mehr Tick-0-Command.
    loop.tick()
    pending_after_tick2 = loop.pending_agent_commands
    assert len(pending_after_tick2) == 1
    assert pending_after_tick2[0].command_id != cmd_id_tick0
    assert pending_after_tick2[0].command_id == "rule_based_bess_tick_1_rule_0"


def test_determinism_two_loops_with_same_seed_produce_same_commands() -> None:
    """`GG-AGENT-003`: Gleicher Seed + gleicher Eingabeverlauf
    → identische Command-Sequenzen.

    Wir bauen zwei Loops mit identischem Device + Agent ohne
    Battery-Integration (Welle-4b-Smoke-Pattern), pruefen dass
    die emittierten Commands der naechsten Tick identisch sind.
    """
    from grid_gym.hexagon.core.domain.scenario import ScenarioDevice

    from tests.unit.hexagon.core.devices._fakes import NullDevice

    def _build_loop() -> TickLoop:
        device = NullDevice()
        device.initialize(
            ScenarioDevice(id="battery-1", type="null", params={}),
            FixedSeedRandom(seed=1),
        )
        agent = _rba("bess")
        return TickLoop(
            run_id="welle-4b-determinism",
            tick_ms=1000,
            clock=FakeClock(),
            random=FixedSeedRandom(seed=42),
            scheduler=Scheduler(),
            devices=(device,),
            agents=(agent,),
            agent_bus=AgentMessageBus(),
        )

    loop_a = _build_loop()
    loop_b = _build_loop()
    snaps_a: list[tuple[str, ...]] = []
    snaps_b: list[tuple[str, ...]] = []
    for _ in range(5):
        loop_a.tick()
        loop_b.tick()
        snaps_a.append(tuple(c.command_id for c in loop_a.pending_agent_commands))
        snaps_b.append(tuple(c.command_id for c in loop_b.pending_agent_commands))
    assert snaps_a == snaps_b
