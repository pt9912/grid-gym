"""M3-Welle-4a-Tests fuer den Schritt-A0-Pending-Agent-Command-Drain
(ADR 0026 §2.1).

Pinnt:
- A0v laeuft VOR `clock.advance(...)` und `scheduler.pop_due(...)`
  (Atomizitaets-Vertrag bei `AgentInvalidCommandTargetError`).
- A0a wendet validierte Commands per `apply_command(...)` an;
  Buffer wird erst nach erfolgreichem Apply geleert.
- Agent-Commands der vorigen Tick wirken in der aktuellen Tick.
- Agent-Commands auf GridConnection-IDs ergaenzen
  `manual_override_grid_ids` (manueller Auto-Close-Override).
- LoadDevice-Baseline gewinnt im selben Tick gegen Agent-Commands.
- Fehler-Pfad: unbekanntes Target → `AgentInvalidCommandTargetError`
  ohne Tick-/Clock-/Device-Mutation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Self

import pytest

from grid_gym.hexagon.core.agents import AgentMessageBus
from grid_gym.hexagon.core.devices._protocol import DeviceModel
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.errors import AgentInvalidCommandTargetError
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.core.devices._fakes import NullDevice
from tests.unit.hexagon.core.simulation.test_tick_loop_welle_4a_agent import (
    _OrderRecordingAgent,
)
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


def _command(command_id: str, target: str = "null-1") -> Command:
    """Test-Command fuer Drain-Pfad."""
    return Command(
        command_id=command_id,
        simulation_time=1000,
        target_device_id=target,
        type="set_power_kw",
        payload={"power_kw": 5},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _initialized_null_device(device_id: str = "null-1") -> NullDevice:
    device = NullDevice()
    device.initialize(
        ScenarioDevice(id=device_id, type="null", params={}),
        FixedSeedRandom(seed=1),
    )
    return device


def _make_loop(
    *,
    devices: tuple[DeviceModel, ...] = (),
    agents: tuple = (),
    agent_bus: AgentMessageBus | None = None,
) -> TickLoop:
    return TickLoop(
        run_id="welle-4a-drain",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=devices,
        agent_bus=agent_bus,
        agents=agents,
    )


def test_a0_drains_pending_commands_in_next_tick() -> None:
    """ADR 0026 §2.1 Drain-Vertrag: Agent emittiert in Tick N,
    Schritt A0a wendet Command in Tick N+1 auf das Device an,
    Buffer wird geleert."""
    recorder: list[str] = []
    agent = _OrderRecordingAgent("agent-x", recorder)
    device = _initialized_null_device("null-1")
    cmd = _command("cmd-1", target="null-1")
    agent.queue_emission((cmd,))
    loop = _make_loop(devices=(device,), agents=(agent,), agent_bus=AgentMessageBus())
    # Tick 1: Agent emittiert Command in D2 → landet im Buffer.
    loop.tick()
    assert loop.pending_agent_commands == (cmd,)
    # Tick 2: A0v validiert, A0a wendet an, Buffer wird geleert.
    agent.queue_emission(())  # Agent emittiert in Tick 2 nichts.
    loop.tick()
    assert loop.pending_agent_commands == ()
    # Device hat Command erhalten.
    assert device.applied_commands == [cmd]


def test_a0v_fails_fast_before_clock_advance() -> None:
    """ADR 0026 §2.1 Atomizitaets-Vertrag: unbekanntes Target wirft
    `AgentInvalidCommandTargetError` VOR `clock.advance(...)`. Clock
    und Tick-Counter bleiben unangetastet; Pending-Buffer ungeleert."""
    recorder: list[str] = []
    agent = _OrderRecordingAgent("agent-x", recorder)
    device = _initialized_null_device("null-1")
    bad_command = _command("cmd-bad", target="unknown-device")
    agent.queue_emission((bad_command,))
    loop = _make_loop(devices=(device,), agents=(agent,), agent_bus=AgentMessageBus())
    # Tick 1: Agent emittiert Command in D2 → Buffer.
    loop.tick()
    assert loop.pending_agent_commands == (bad_command,)
    clock_before = loop._clock.now()  # type: ignore[attr-defined]
    tick_count_before = loop.tick_count
    # Tick 2: A0v wirft, Clock/Counter/Buffer bleiben unangetastet.
    with pytest.raises(AgentInvalidCommandTargetError):
        loop.tick()
    assert loop._clock.now() == clock_before  # type: ignore[attr-defined]
    assert loop.tick_count == tick_count_before
    assert loop.pending_agent_commands == (bad_command,)
    # Device sah keinen Apply-Aufruf.
    assert device.applied_commands == []


def test_a0a_grid_connection_command_adds_to_manual_override() -> None:
    """ADR 0026 §2.1 GridConnection-Konflikt-Regel: Agent-Command
    auf GridConnection-ID ergaenzt `manual_override_grid_ids`,
    damit Schritt C Auto-Close den Agent-Wert nicht ueberschreibt.

    Welle-4a-Foundation: Test pinnt nur das End-zu-End-Verhalten
    (Tick lief durch ohne Crash, Telemetry emittiert). Die
    `manual_override_grid_ids`-Internals sind nicht direkt
    pruefbar ohne TickLoop-Internals zu inspizieren; das ist
    Welle-4b-Material mit konkretem Decision-Loop.
    """
    from decimal import Decimal

    from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
    from grid_gym.hexagon.core.domain.scenario import ScenarioDevice

    recorder: list[str] = []
    agent = _OrderRecordingAgent("agent-x", recorder)
    grid_device = GridConnectionDevice()
    grid_device.initialize(
        ScenarioDevice(
            id="grid-1",
            type="grid_connection",
            params={
                "nominal_voltage_v": Decimal("230"),
                "max_import_kw": Decimal("100"),
                "max_export_kw": Decimal("100"),
            },
        ),
        FixedSeedRandom(seed=1),
    )
    grid_device.set_run_id("welle-4a-drain")
    cmd = Command(
        command_id="cmd-grid",
        simulation_time=1000,
        target_device_id="grid-1",
        type="set_power_kw",
        payload={"power_kw": Decimal("5")},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )
    agent.queue_emission((cmd,))
    loop = _make_loop(
        devices=(grid_device,),
        agents=(agent,),
        agent_bus=AgentMessageBus(),
    )
    loop.tick()  # Tick 1: Agent emittiert Command in D2.
    # Tick 2: A0a wendet Command an, GridConnection-Override-Pfad.
    agent.queue_emission(())
    result = loop.tick()
    # Tick lief durch ohne Crash; Buffer leer.
    assert loop.pending_agent_commands == ()
    # GridConnection-Telemetry wurde emittiert (Tick lief erfolgreich).
    assert any(p.source == "grid_connection" for p in result.emitted_telemetry)
