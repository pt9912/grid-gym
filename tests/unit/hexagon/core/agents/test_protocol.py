"""Protocol-Adherence-Tests fuer `Agent` (M3 Welle 3, ADR 0023 §2.1).

Pinnt:

- Ein `NullAgent`-Implementer erfuellt das `Agent`-Protocol via
  `isinstance(...)` (`@runtime_checkable`).
- Agent ist **nicht** ein `DeviceModel` (ADR 0023 §2.1 Closed-Set:
  Agents stehen neben Geraeten, nicht auf ihnen).
- Pflicht-Surface: `agent_id`, `set_run_id`, `tick`, `snapshot`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Self

import pytest

from grid_gym.hexagon.core.agents import Agent, AgentMessageBus
from grid_gym.hexagon.core.devices import DeviceModel
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.errors import VersionError


class NullAgent:
    """Test-Fake: minimaler `Agent`-Implementer (ADR 0023 §2.1).

    Welle-3-Test-Pattern (analog `NullDevice` aus M2-Welle-1):
    erfuellt die Protocol-Surface ohne Decision-Logik. Hilft
    Welle 4 als Baseline fuer Property-Tests.
    """

    SNAPSHOT_VERSION: int = 1

    def __init__(self, agent_id: str = "null-agent") -> None:
        self._agent_id: str = agent_id
        self._run_id: str | None = None
        self.tick_calls: list[tuple[DeviceTickContext, AgentMessageBus]] = []

    @property
    def agent_id(self) -> str:
        return self._agent_id

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id

    def tick(
        self,
        context: DeviceTickContext,
        bus: AgentMessageBus,
    ) -> Sequence[Command]:
        self.tick_calls.append((context, bus))
        return ()

    def snapshot(self) -> Mapping[str, object]:
        return {"version": self.SNAPSHOT_VERSION, "agent_id": self._agent_id}

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        """Welle-3-Review-Folge-2 F-2 (2026-05-21): roundtrip-Pflicht
        per Agent-Protocol. NullAgent rekonstruiert aus
        `{"version": ..., "agent_id": ...}`."""
        version = state.get("version")
        if version != cls.SNAPSHOT_VERSION:
            raise VersionError("null_agent", expected=cls.SNAPSHOT_VERSION, found=version)
        agent_id = state.get("agent_id")
        if not isinstance(agent_id, str):
            raise TypeError(
                f"NullAgent.from_snapshot: agent_id must be str, got {type(agent_id).__name__}"
            )
        return cls(agent_id=agent_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NullAgent):
            return NotImplemented
        return self._agent_id == other._agent_id

    def __hash__(self) -> int:
        return hash(("NullAgent", self._agent_id))


def test_null_agent_satisfies_agent_protocol() -> None:
    """ADR 0023 §2.1: `@runtime_checkable` erlaubt isinstance-
    Check ohne explizite Subclass-Deklaration."""
    agent = NullAgent()
    assert isinstance(agent, Agent)


def test_null_agent_is_not_a_device_model() -> None:
    """ADR 0023 §2.1 Closed-Set: Agents sind keine Geraete.
    Verhindert implizite Vermischung der Tuples im TickLoop."""
    agent = NullAgent()
    assert not isinstance(agent, DeviceModel)


def test_agent_id_is_stable() -> None:
    """`agent_id` ist Pflicht-Pflicht (analog DeviceModel.device_id)."""
    agent = NullAgent(agent_id="agent-7")
    assert agent.agent_id == "agent-7"


def test_set_run_id_is_lifecycle_hook() -> None:
    """Welle-3-Lifecycle: `set_run_id` wird vom TickLoop einmal
    aufgerufen; idempotente Mehrfach-Calls sind Welle-4-Decision."""
    agent = NullAgent()
    agent.set_run_id("run-123")
    assert agent._run_id == "run-123"


def test_agent_tick_returns_command_sequence_and_records_bus_argument() -> None:
    """ADR 0023 §2.1: `tick(context, bus) -> Sequence[Command]`.
    Welle-3-Stand: `NullAgent` returnt leere Sequenz; bus + context
    werden mitgeschickt."""
    agent = NullAgent()
    bus = AgentMessageBus()
    context = DeviceTickContext(tick=0, simulation_time=1000, tick_ms=1000)
    commands = agent.tick(context, bus)
    assert commands == ()
    assert len(agent.tick_calls) == 1
    assert agent.tick_calls[0] == (context, bus)


def test_agent_snapshot_includes_version_key() -> None:
    """ADR 0015 §2.3 Sub-Snapshot-Konvention: `"version": int`-Key."""
    agent = NullAgent()
    snapshot = agent.snapshot()
    assert snapshot["version"] == NullAgent.SNAPSHOT_VERSION


def test_agent_from_snapshot_roundtrip_is_byte_stable() -> None:
    """Welle-3-Review-Folge-2 F-2 (2026-05-21): `from_snapshot(
    snapshot()) == agent`-Vertrag (analog ADR 0013 §2.4)."""
    agent = NullAgent(agent_id="agent-7")
    restored = NullAgent.from_snapshot(agent.snapshot())
    assert restored == agent
    assert restored.agent_id == "agent-7"


def test_agent_from_snapshot_rejects_unknown_version() -> None:
    """Typed-Error bei Schema-Drift (Welle-0a-Codec-Pattern)."""
    with pytest.raises(VersionError):
        NullAgent.from_snapshot({"version": 999, "agent_id": "agent-x"})


def test_agent_protocol_requires_from_snapshot_classmethod() -> None:
    """Welle-3-Review-Folge-2 F-2: `Agent`-Protocol-Surface
    enthaelt `from_snapshot`-Classmethod. `@runtime_checkable`-
    isinstance prueft Methoden-Existenz."""
    # Sanity: NullAgent erfuellt das Protocol weiterhin nach F-2.
    agent = NullAgent()
    assert isinstance(agent, Agent)
    # Class-level Surface-Pruefung: `from_snapshot` ist Pflicht.
    assert callable(NullAgent.from_snapshot)

    # Eine Klasse ohne `from_snapshot` darf das Protocol NICHT
    # erfuellen (negative Sanity).
    class _AgentWithoutFromSnapshot:
        SNAPSHOT_VERSION = 1
        agent_id = "no-snap"

        def set_run_id(self, run_id: str) -> None:
            pass

        def tick(self, context: DeviceTickContext, bus: AgentMessageBus) -> Sequence[Command]:
            return ()

        def snapshot(self) -> Mapping[str, object]:
            return {"version": 1}

    incomplete = _AgentWithoutFromSnapshot()
    assert not isinstance(incomplete, Agent)
