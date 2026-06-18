"""Pins fuer die TickLoop-ScenarioCommandEngine-Naht (S2, ADR 0070 §2.3,
Trigger 046).

- TickLoop stellt im Tick faellige scenario-geplante Commands an ihr Target zu
  (Schritt A0s), genau im Span [now, now + tick_ms).
- Jeder Command wird genau einmal zugestellt (stateless Faelligkeit).
- `command_engine=None` (Default) ist bit-genau ein No-op (Bestands-Szenarien).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Self

from grid_gym.hexagon.core.commands import ScenarioCommandEngine
from grid_gym.hexagon.core.devices._protocol import DeviceModel
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext, DeviceTickOutcome
from grid_gym.hexagon.core.domain.scenario import ScenarioCommand, ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driven.random import RandomPort
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


class _CommandRecordingDevice:
    """Test-Double (`DeviceModel`): zeichnet jeden `apply_command` auf."""

    def __init__(self, device_id: str) -> None:
        self._device_id = device_id
        self.received: list[Command] = []

    @property
    def device_id(self) -> str:
        return self._device_id

    def initialize(self, scenario_device: ScenarioDevice, random: RandomPort) -> None:
        _ = scenario_device
        _ = random

    def apply_command(self, command: Command) -> CommandResult:
        self.received.append(command)
        return CommandResult.ACCEPTED

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        _ = context
        return DeviceTickOutcome(telemetry=())

    def snapshot(self) -> Mapping[str, object]:
        return {"version": 1}

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return ()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        _ = state
        return cls("rec-1")

    def set_run_id(self, run_id: str) -> None:
        _ = run_id


def _make_loop(
    *,
    devices: tuple[DeviceModel, ...],
    command_engine: ScenarioCommandEngine | None = None,
) -> TickLoop:
    return TickLoop(
        run_id="welle-046-cmd-test",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=devices,
        command_engine=command_engine,
    )


def test_scenario_command_applied_in_its_tick_span() -> None:
    recorder = _CommandRecordingDevice("rec-1")
    engine = ScenarioCommandEngine(
        [ScenarioCommand(simulation_time=2000, target="rec-1", type="set_power_kw", payload={})]
    )
    loop = _make_loop(devices=(recorder,), command_engine=engine)

    loop.tick()  # Tick 1: now=1000, Span [1000, 2000) -> nicht faellig
    assert recorder.received == []

    loop.tick()  # Tick 2: now=2000, Span [2000, 3000) -> faellig
    assert len(recorder.received) == 1
    delivered = recorder.received[0]
    assert delivered.command_id == "scenario-cmd-0"
    assert delivered.target_device_id == "rec-1"
    assert delivered.type == "set_power_kw"

    loop.tick()  # Tick 3: bereits zugestellt -> nicht erneut
    assert len(recorder.received) == 1


def test_no_command_engine_is_a_noop() -> None:
    recorder = _CommandRecordingDevice("rec-1")
    loop = _make_loop(devices=(recorder,))
    loop.tick()
    loop.tick()
    assert recorder.received == []
