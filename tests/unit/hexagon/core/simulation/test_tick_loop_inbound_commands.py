"""Pins fuer die TickLoop-Inbound-Command-Naht (Schritt A0i, ADR 0076 §2.3,
Slice 075 S1a).

- TickLoop zieht pro Tick die faelligen Inbound-Writes aus dem
  `InboundCommandPort` und stellt sie an ihr Target zu (Schritt A0i), auf
  `context.simulation_time` aufgeloest.
- Ordnung: A0i laeuft **nach** A0a (scenario→agent→inbound); mehrere Writes in
  `arrival_sequence`-Reihenfolge.
- Unbekanntes Target wird defensiv uebersprungen (kein `KeyError`).
- `inbound_source=None` (Default) ist ein No-op (Bestands-Laeufe byte-identisch).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Self

from grid_gym.adapters.driving._inbound_command_buffer import InboundCommandBuffer
from grid_gym.hexagon.core.devices._protocol import DeviceModel
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext, DeviceTickOutcome
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
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
    inbound_source: InboundCommandBuffer | None = None,
) -> TickLoop:
    return TickLoop(
        run_id="slice-075-inbound-test",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=devices,
        inbound_source=inbound_source,
    )


def test_inbound_command_applied_at_current_tick() -> None:
    recorder = _CommandRecordingDevice("rec-1")
    buffer = InboundCommandBuffer()
    loop = _make_loop(devices=(recorder,), inbound_source=buffer)

    buffer.enqueue("rec-1", "set_power_kw", {})
    loop.tick()  # now=1000 → A0i loest auf 1000 auf

    assert len(recorder.received) == 1
    delivered = recorder.received[0]
    assert delivered.simulation_time == 1000
    assert delivered.target_device_id == "rec-1"
    assert delivered.type == "set_power_kw"
    assert delivered.validation_status == "inbound"
    # Capture zeichnet den aufgeloesten Tick auf (Source-of-Truth, ADR 0076 §2.1).
    assert buffer.capture()[0].resolved_sim_tick == 1000
    # Puffer geleert → kein erneutes Zustellen.
    loop.tick()
    assert len(recorder.received) == 1


def test_no_inbound_source_is_a_noop() -> None:
    recorder = _CommandRecordingDevice("rec-1")
    loop = _make_loop(devices=(recorder,))
    loop.tick()
    loop.tick()
    assert recorder.received == []


def test_unknown_target_is_skipped_without_error() -> None:
    recorder = _CommandRecordingDevice("rec-1")
    buffer = InboundCommandBuffer()
    loop = _make_loop(devices=(recorder,), inbound_source=buffer)

    buffer.enqueue("does-not-exist", "set_x", {})
    loop.tick()  # darf nicht werfen

    assert recorder.received == []


def test_multiple_inbound_applied_in_arrival_order() -> None:
    recorder = _CommandRecordingDevice("rec-1")
    buffer = InboundCommandBuffer()
    loop = _make_loop(devices=(recorder,), inbound_source=buffer)

    buffer.enqueue("rec-1", "first", {})
    buffer.enqueue("rec-1", "second", {})
    loop.tick()

    assert [command.type for command in recorder.received] == ["first", "second"]
