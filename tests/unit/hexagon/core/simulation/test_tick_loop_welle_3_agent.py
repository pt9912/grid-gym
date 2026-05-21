"""M3-Welle-3-Tests fuer den TickLoop-AgentBus-Hook
(ADR 0023 §2.4 + §2.5).

Pinnt:

- TickLoop akzeptiert `agent_bus: AgentMessageBus | None`-Kwarg
  ohne Default-Bruch (existing tests bleiben gruen).
- `agent_bus=None` (Default) skippt den Hook sauber.
- Mit `agent_bus + _agents`: Hook ruft `agent.tick(context, bus)`
  pro Agent pro Tick.
- Hook-Order: Agent-Tick laeuft NACH Device-Tick (Schritt D2
  zwischen Schritt D und E, Architektur §6 Schritt 7).
- TickResult-Struktur bleibt unveraendert (Agents emittieren
  keine TelemetryPoints in Welle 3).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Self

from grid_gym.hexagon.core.agents import AgentMessageBus
from grid_gym.hexagon.core.devices._protocol import DeviceModel
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.core.devices._fakes import NullDevice
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


class _OrderRecordingAgent:
    """Inline-Stub: zeichnet Aufruf-Reihenfolge auf.

    Welle-3-Test-Pattern: minimaler `Agent`-Implementer mit
    Order-Recorder. Produktive Agents kommen in Welle 4.
    """

    SNAPSHOT_VERSION: int = 1

    def __init__(self, agent_id: str, recorder: list[str]) -> None:
        self._agent_id = agent_id
        self._recorder = recorder
        self._emitted_commands: tuple[Command, ...] = ()

    @property
    def agent_id(self) -> str:
        return self._agent_id

    def set_run_id(self, run_id: str) -> None:
        # Welle-3-Hook ruft set_run_id nicht auf (Welle-4-Decision);
        # No-Op reicht fuer die Protocol-Surface.
        pass

    def queue_emission(self, commands: tuple[Command, ...]) -> None:
        """Test-Helper: legt Commands ab, die der naechste
        `tick(...)` als Return-Wert liefern wird (Welle-3-Review-
        Folge-2 F-1-Buffer-Test)."""
        self._emitted_commands = commands

    def tick(
        self,
        context: DeviceTickContext,
        bus: AgentMessageBus,
    ) -> Sequence[Command]:
        self._recorder.append(f"agent.tick:{self._agent_id}")
        return self._emitted_commands

    def snapshot(self) -> Mapping[str, object]:
        return {"version": self.SNAPSHOT_VERSION, "agent_id": self._agent_id}

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        # Test-Stub: rekonstruktion ohne Recorder (Recorder ist
        # ephemer pro Test). Welle 4 wird das nicht brauchen.
        agent_id = state.get("agent_id")
        if not isinstance(agent_id, str):
            raise TypeError(
                f"_OrderRecordingAgent.from_snapshot: agent_id "
                f"must be str, got {type(agent_id).__name__}"
            )
        return cls(agent_id=agent_id, recorder=[])


class _OrderRecordingNullDevice(NullDevice):
    """NullDevice + Tick-Order-Recorder."""

    def __init__(self, recorder: list[str]) -> None:
        super().__init__()
        self._recorder = recorder

    def tick(self, context):  # type: ignore[override, no-untyped-def]
        outcome = super().tick(context)
        self._recorder.append(f"device.tick:{self.device_id}")
        return outcome


def _make_loop(
    *,
    devices: tuple[DeviceModel, ...] = (),
    agent_bus: AgentMessageBus | None = None,
) -> TickLoop:
    return TickLoop(
        run_id="welle-3-agent-test",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=devices,
        agent_bus=agent_bus,
    )


def test_tick_loop_accepts_none_default_for_agent_bus() -> None:
    """ADR 0023 §2.5: `agent_bus=None` (Default) skippt den Hook
    — bestehende Tests bleiben gruen."""
    loop = _make_loop(agent_bus=None)
    result = loop.tick()
    assert result.simulation_time == 1000  # tick_ms=1000 → time advanced
    # Schritt D2 wird intern uebersprungen; keine Exception, kein
    # Agent-Aufruf (Welle-3-`_agents` ist sowieso `()`).


def test_tick_loop_accepts_agent_bus_without_agents() -> None:
    """Mit `agent_bus=AgentMessageBus()` ohne registrierte Agents
    bleibt der Tick ein No-Op auf dem Hook (Loop-Body ueber leere
    Sequenz)."""
    bus = AgentMessageBus()
    loop = _make_loop(agent_bus=bus)
    result = loop.tick()
    assert result.simulation_time == 1000
    # Bus bleibt leer, kein Agent hat publiziert.
    assert bus.snapshot()["next_sequence"] == 0


def test_tick_loop_calls_each_agent_when_registered() -> None:
    """ADR 0023 §2.4: pro registriertem Agent ruft TickLoop
    `agent.tick(context, bus)` einmal pro Tick.

    Welle-3-Stand: `_agents` ist Konstruktor-leer; Test-Code
    befuellt es via `_set_agents_for_testing(...)` (L-1-Helper).
    Welle 4 wird die produktive Registry-API formalisieren
    (Kwarg vs. Builder-Pfad).
    """
    recorder: list[str] = []
    agent_a = _OrderRecordingAgent("agent-a", recorder)
    agent_b = _OrderRecordingAgent("agent-b", recorder)
    bus = AgentMessageBus()
    loop = _make_loop(agent_bus=bus)
    loop._set_agents_for_testing((agent_a, agent_b))
    loop.tick()
    assert recorder == ["agent.tick:agent-a", "agent.tick:agent-b"]


def test_agent_tick_runs_after_device_tick() -> None:
    """ADR 0023 §2.4 Order-Pflicht: Agent-Hook (Schritt D2) laeuft
    NACH der Geraete-Iteration. Architektur §6 Schritt 7."""
    recorder: list[str] = []
    device = _OrderRecordingNullDevice(recorder)
    device.initialize(
        ScenarioDevice(id="null-1", type="null", params={}),
        FixedSeedRandom(seed=1),
    )
    agent = _OrderRecordingAgent("agent-x", recorder)
    bus = AgentMessageBus()
    loop = _make_loop(devices=(device,), agent_bus=bus)
    loop._set_agents_for_testing((agent,))
    loop.tick()
    assert "device.tick:null-1" in recorder
    assert "agent.tick:agent-x" in recorder
    # Order: Device-Tick zuerst, dann Agent.
    assert recorder.index("device.tick:null-1") < recorder.index("agent.tick:agent-x")


def test_agent_hook_skipped_when_bus_is_none_even_with_agents() -> None:
    """ADR 0023 §2.5: `agent_bus=None` skippt den Hook **auch**
    wenn `_agents` gefuellt waere. Verhindert NullPointer-Sequence
    durch versehentliche Agent-Registrierung ohne Bus."""
    recorder: list[str] = []
    agent = _OrderRecordingAgent("agent-x", recorder)
    loop = _make_loop(agent_bus=None)
    loop._set_agents_for_testing((agent,))  # technisch moeglich, semantisch falsch
    loop.tick()
    # Agent wurde nicht aufgerufen — Bus-Check kommt vor Loop.
    assert recorder == []


def test_set_agents_for_testing_rejects_duplicate_agent_id() -> None:
    """Welle-3-Review-Folge L-1 (2026-05-21): der Test-Helper
    prueft `agent_id`-Eindeutigkeit defensiv, damit Tests nicht
    versehentlich Duplicate-IDs durchreichen, die Welle 4 spaeter
    abfangen wuerde."""
    recorder: list[str] = []
    agent_a = _OrderRecordingAgent("agent-x", recorder)
    agent_b = _OrderRecordingAgent("agent-x", recorder)
    loop = _make_loop(agent_bus=AgentMessageBus())
    try:
        loop._set_agents_for_testing((agent_a, agent_b))
    except ValueError as exc:
        assert "agent-x" in str(exc)
    else:  # pragma: no cover — Test schlaegt fehl, wenn kein Raise
        msg = "_set_agents_for_testing accepted duplicate agent_id"
        raise AssertionError(msg)


def test_tick_result_unchanged_when_only_agent_bus_present() -> None:
    """Welle-3-Foundation emittiert KEINE TelemetryPoints aus
    Agents. `TickResult.emitted_telemetry` bleibt leer wenn
    kein Device telemetriert."""
    bus = AgentMessageBus()
    loop = _make_loop(agent_bus=bus)
    result = loop.tick()
    assert result.emitted_telemetry == ()


def _command(command_id: str, target: str = "device-1") -> Command:
    """Helfer fuer Command-Konstruktion in F-1-Tests."""
    return Command(
        command_id=command_id,
        simulation_time=1000,
        target_device_id=target,
        type="set_power_kw",
        payload={"power_kw": 5},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def test_pending_agent_commands_empty_by_default() -> None:
    """Welle-3-Review-Folge-2 F-1 (2026-05-21): ohne registrierte
    Agents bleibt der Pending-Buffer nach `tick()` leer."""
    loop = _make_loop(agent_bus=AgentMessageBus())
    assert loop.pending_agent_commands == ()
    loop.tick()
    assert loop.pending_agent_commands == ()


def test_pending_agent_commands_collects_agent_returns() -> None:
    """Welle-3-Review-Folge-2 F-1: emittierte Commands der Agents
    landen im `_pending_agent_commands`-Buffer (nicht verworfen).
    Welle 4 wird den Drain-Pfad verdrahten."""
    recorder: list[str] = []
    agent_a = _OrderRecordingAgent("agent-a", recorder)
    agent_b = _OrderRecordingAgent("agent-b", recorder)
    cmd_1 = _command("cmd-1")
    cmd_2 = _command("cmd-2")
    cmd_3 = _command("cmd-3")
    agent_a.queue_emission((cmd_1,))
    agent_b.queue_emission((cmd_2, cmd_3))
    loop = _make_loop(agent_bus=AgentMessageBus())
    loop._set_agents_for_testing((agent_a, agent_b))
    loop.tick()
    # Reihenfolge: Agents werden in `_agents`-Reihenfolge iteriert.
    assert loop.pending_agent_commands == (cmd_1, cmd_2, cmd_3)


def test_pending_agent_commands_accumulates_across_ticks() -> None:
    """Welle-3-Review-Folge-2 F-1: Buffer waechst tick-by-tick
    (Welle-3-Foundation: keine Eviction; Welle-4-Drain-Pfad raeumt
    ihn). Spiegelt AgentMessageBus-Buffer-Semantik."""
    recorder: list[str] = []
    agent = _OrderRecordingAgent("agent-x", recorder)
    cmd_a = _command("cmd-a")
    cmd_b = _command("cmd-b")
    loop = _make_loop(agent_bus=AgentMessageBus())
    loop._set_agents_for_testing((agent,))
    agent.queue_emission((cmd_a,))
    loop.tick()
    agent.queue_emission((cmd_b,))
    loop.tick()
    assert loop.pending_agent_commands == (cmd_a, cmd_b)


def test_pending_agent_commands_property_is_immutable_view() -> None:
    """Welle-3-Review-Folge-2 F-1: Property liefert `tuple`-
    Snapshot, damit Aufrufer den internen Buffer nicht mutieren."""
    loop = _make_loop(agent_bus=AgentMessageBus())
    pending = loop.pending_agent_commands
    assert isinstance(pending, tuple)


def test_pending_agent_commands_empty_when_bus_is_none() -> None:
    """Welle-3-Review-Folge-2 F-1 + L-3 Konsistenz: bei
    `agent_bus=None` skippt Schritt D2 komplett; Buffer bleibt
    unangetastet selbst bei gefuelltem `_agents`-Tuple."""
    recorder: list[str] = []
    agent = _OrderRecordingAgent("agent-x", recorder)
    agent.queue_emission((_command("cmd-x"),))
    loop = _make_loop(agent_bus=None)
    loop._set_agents_for_testing((agent,))
    loop.tick()
    assert loop.pending_agent_commands == ()
