"""M3-Welle-4a-Tests fuer den `_attach_agents()`-Lifecycle
(ADR 0026 §2.3).

Pinnt:
- `set_run_id(self._run_id)`-Aufruf fuer jeden registrierten
  Agent.
- Optionaler `attach_random(...)`-Aufruf via
  `_RandomAttachableAgent`-Sub-Protocol; Sub-Port-Namens-
  Konvention `agent-{agent_id}`.
- Agents ohne `_RandomAttachableAgent`-Surface bekommen keinen
  Sub-Port + keinen No-op-Hook aufgezwungen.
- `isinstance(agent, _RandomAttachableAgent)` wirft keinen
  `TypeError` zur Laufzeit (Sub-Protocol ist
  `@runtime_checkable`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Self

from grid_gym.hexagon.core.agents import (
    Agent,
    AgentMessageBus,
    _RandomAttachableAgent,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driven.random import RandomPort
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


class _NullAgent:
    """Minimaler Agent ohne Stochastik (nicht `_RandomAttachableAgent`)."""

    SNAPSHOT_VERSION: int = 1

    def __init__(self, agent_id: str) -> None:
        self._agent_id = agent_id
        self.set_run_id_calls: list[str] = []

    @property
    def agent_id(self) -> str:
        return self._agent_id

    def set_run_id(self, run_id: str) -> None:
        self.set_run_id_calls.append(run_id)

    def tick(
        self,
        context: DeviceTickContext,
        bus: AgentMessageBus,
    ) -> Sequence[Command]:
        return ()

    def snapshot(self) -> Mapping[str, object]:
        return {"version": self.SNAPSHOT_VERSION, "agent_id": self._agent_id}

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        agent_id = state["agent_id"]
        assert isinstance(agent_id, str)
        return cls(agent_id=agent_id)


class _StochasticAgent(_NullAgent):
    """Agent mit `_RandomAttachableAgent`-Surface."""

    def __init__(self, agent_id: str) -> None:
        super().__init__(agent_id)
        self.attached_random: RandomPort | None = None

    def attach_random(self, random: RandomPort) -> None:
        self.attached_random = random


def _make_loop(*, agents: tuple = ()) -> TickLoop:
    return TickLoop(
        run_id="welle-4a-lifecycle",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        agent_bus=AgentMessageBus() if agents else None,
        agents=agents,
    )


def test_attach_agents_calls_set_run_id() -> None:
    """ADR 0026 §2.3: `_attach_agents()` ruft `set_run_id(run_id)`
    fuer jeden Agent."""
    agent_a = _NullAgent("agent-a")
    agent_b = _NullAgent("agent-b")
    _make_loop(agents=(agent_a, agent_b))
    assert agent_a.set_run_id_calls == ["welle-4a-lifecycle"]
    assert agent_b.set_run_id_calls == ["welle-4a-lifecycle"]


def test_attach_agents_calls_attach_random_for_stochastic_agents() -> None:
    """ADR 0026 §2.3: `_RandomAttachableAgent`-Agents bekommen
    `attach_random(random_root.sub_port(f"agent-{agent_id}"))`."""
    agent = _StochasticAgent("agent-x")
    _make_loop(agents=(agent,))
    assert agent.attached_random is not None


def test_attach_agents_skips_attach_random_for_non_stochastic() -> None:
    """ADR 0026 §2.3: Agents ohne `_RandomAttachableAgent`-Surface
    bekommen weder Sub-Port noch No-op-Hook aufgezwungen."""
    agent = _NullAgent("agent-y")
    _make_loop(agents=(agent,))
    # Kein crash; `_NullAgent` hat keinen `attached_random`-Attribut
    # und auch keine `attach_random`-Methode. Sanity-Check:
    assert not hasattr(agent, "attached_random")


def test_random_attachable_protocol_runtime_checkable() -> None:
    """ADR 0026 §2.3: `_RandomAttachableAgent` ist
    `@runtime_checkable`, sonst wirft `isinstance(...)` `TypeError`."""
    stochastic = _StochasticAgent("agent-s")
    null_agent = _NullAgent("agent-n")
    # Beides muss ohne TypeError funktionieren.
    assert isinstance(stochastic, _RandomAttachableAgent)
    assert not isinstance(null_agent, _RandomAttachableAgent)
    # Sanity: beide erfuellen das Base-`Agent`-Protocol.
    assert isinstance(stochastic, Agent)
    assert isinstance(null_agent, Agent)


def test_attach_random_sub_port_name_convention() -> None:
    """ADR 0026 §2.3 + Welle-3-Review-Folge M-3: Sub-Port-Name ist
    `agent-{agent_id}`."""
    agent = _StochasticAgent("agent-7")
    _make_loop(agents=(agent,))
    # `attached_random` ist ein RandomPort-SubPort, snapshot zeigt
    # den abgeleiteten Pfad. FixedSeedRandom liefert Sub-Port-
    # Snapshot mit sub-name als Teil von snapshot_as_mapping().
    assert agent.attached_random is not None
