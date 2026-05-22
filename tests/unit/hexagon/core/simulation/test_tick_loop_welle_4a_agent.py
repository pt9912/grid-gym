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
        # Welle-4a (ADR 0026 §2.3): `_attach_agents()` ruft das hier
        # produktiv auf — dieser Stub recordet aber bewusst nicht;
        # Lifecycle-Recording lebt im `_NullAgent` von
        # `test_tick_loop_welle_4a_lifecycle.py`. Der Order-Recorder
        # hier soll nur Tick-Reihenfolge pinnen.
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
    agents: tuple = (),
) -> TickLoop:
    return TickLoop(
        run_id="welle-4a-agent-test",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=devices,
        agent_bus=agent_bus,
        agents=agents,
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
    """ADR 0023 §2.4 + ADR 0026 §2.2: pro registriertem Agent
    ruft TickLoop `agent.tick(context, bus)` einmal pro Tick.

    Welle-4a-Stand (ADR 0026): produktive Registry-API via
    Konstruktor-Kwarg `agents=(...)`. Welle-3-Test-Helper
    `_set_agents_for_testing(...)` ist entfernt.
    """
    recorder: list[str] = []
    agent_a = _OrderRecordingAgent("agent-a", recorder)
    agent_b = _OrderRecordingAgent("agent-b", recorder)
    bus = AgentMessageBus()
    loop = _make_loop(agent_bus=bus, agents=(agent_a, agent_b))
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
    loop = _make_loop(devices=(device,), agent_bus=bus, agents=(agent,))
    loop.tick()
    assert "device.tick:null-1" in recorder
    assert "agent.tick:agent-x" in recorder
    # Order: Device-Tick zuerst, dann Agent.
    assert recorder.index("device.tick:null-1") < recorder.index("agent.tick:agent-x")


def test_agent_hook_skipped_when_bus_is_none_and_no_agents() -> None:
    """ADR 0023 §2.5 + ADR 0026 §2.2: `agent_bus=None` mit
    `agents=()` skippt Schritt D2 sauber.

    Welle-4a-Auto-Bus-Regel: `agents != () and agent_bus is None`
    erzeugt automatisch einen Bus, damit registrierte Agents
    nicht still als No-op enden. Der reine Skip-Pfad existiert
    nur fuer agentenlose Runs.
    """
    loop = _make_loop(agent_bus=None, agents=())
    loop.tick()
    # Kein Crash; agentenloser Run laeuft normal durch.
    assert loop.pending_agent_commands == ()


def test_constructor_auto_bus_when_agents_without_explicit_bus() -> None:
    """ADR 0026 §2.2 Auto-Bus-Regel: nicht-leere `agents` ohne
    `agent_bus` bekommen automatisch einen frischen Bus, damit
    Schritt D2 die Agents tickt."""
    recorder: list[str] = []
    agent = _OrderRecordingAgent("agent-x", recorder)
    loop = _make_loop(agent_bus=None, agents=(agent,))
    # Auto-Bus aktiv: `_agent_bus` ist nach Konstruktor nicht None.
    assert loop._agent_bus is not None  # type: ignore[attr-defined]
    loop.tick()
    # Agent wurde getickt (statt still als No-op zu enden).
    assert recorder == ["agent.tick:agent-x"]


def test_constructor_rejects_duplicate_agent_id() -> None:
    """ADR 0026 §2.5: Konstruktor wirft `AgentDuplicateIdError`
    bei doppelten `agent_id`-Werten. Welle-4a-Registry-Fail-Fast."""
    from grid_gym.hexagon.core.errors import AgentDuplicateIdError

    recorder: list[str] = []
    agent_a = _OrderRecordingAgent("agent-x", recorder)
    agent_b = _OrderRecordingAgent("agent-x", recorder)
    try:
        _make_loop(agent_bus=AgentMessageBus(), agents=(agent_a, agent_b))
    except AgentDuplicateIdError as exc:
        assert "agent-x" in str(exc)
    else:  # pragma: no cover — Test schlaegt fehl, wenn kein Raise
        msg = "TickLoop constructor accepted duplicate agent_id"
        raise AssertionError(msg)


def test_tick_result_unchanged_when_only_agent_bus_present() -> None:
    """Welle-3-Foundation emittiert KEINE TelemetryPoints aus
    Agents. `TickResult.emitted_telemetry` bleibt leer wenn
    kein Device telemetriert."""
    bus = AgentMessageBus()
    loop = _make_loop(agent_bus=bus)
    result = loop.tick()
    assert result.emitted_telemetry == ()


def test_pending_agent_commands_empty_by_default() -> None:
    """Welle-3-Review-Folge-2 F-1 (2026-05-21): ohne registrierte
    Agents bleibt der Pending-Buffer nach `tick()` leer.
    Welle-4a-Skip-Pfad: `agents=()` und `agent_bus=None` lassen
    den Buffer ungetastet."""
    loop = _make_loop(agent_bus=AgentMessageBus())
    assert loop.pending_agent_commands == ()
    loop.tick()
    assert loop.pending_agent_commands == ()


def test_pending_agent_commands_property_is_immutable_view() -> None:
    """Welle-3-Review-Folge-2 F-1: Property liefert `tuple`-
    Snapshot, damit Aufrufer den internen Buffer nicht mutieren."""
    loop = _make_loop(agent_bus=AgentMessageBus())
    pending = loop.pending_agent_commands
    assert isinstance(pending, tuple)


# Welle-4a-Drain-spezifische Pending-Buffer-Tests (Schritt-A0v/A0a-
# Atomizitaet, Drain-Order, GridConnection-Override etc.) leben in
# `test_tick_loop_welle_4a_drain.py`. Welle-3-Tests, die
# Buffer-Accumulation pinnten, sind in Welle 4a obsolet (Schritt
# A0a drainet den Buffer in der naechsten Tick).
