"""Tests fuer `InboundCommandBuffer` (Field-Server-Write-Pfad, ADR 0076 §2.1/§2.3).

Thread-sicherer Puffer + Capture: enqueue vergibt `arrival_sequence`, `drain_due`
loest auf den aktuellen Tick auf (leert den Puffer), `capture()` haelt die
aufgeloesten Writes als Aufzeichnung.
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.adapters.driving._inbound_command_buffer import (
    InboundCommandBuffer,
    InboundWriteCapture,
    materialize_inbound_writes,
)
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioCommand


def _ctx(simulation_time: int) -> DeviceTickContext:
    return DeviceTickContext(tick=0, simulation_time=simulation_time, tick_ms=1000)


def test_enqueue_assigns_monotonic_sequence() -> None:
    buffer = InboundCommandBuffer()
    assert buffer.enqueue("d1", "set_x", {"value": Decimal("1")}) == 0
    assert buffer.enqueue("d2", "set_y", {"value": Decimal("2")}) == 1


def test_drain_resolves_to_context_tick_and_clears() -> None:
    buffer = InboundCommandBuffer()
    buffer.enqueue("d1", "set_x", {"value": Decimal("1")})
    commands = buffer.drain_due(_ctx(2000))
    assert len(commands) == 1
    command = commands[0]
    assert command.simulation_time == 2000  # auf den aktuellen Tick aufgeloest
    assert command.target_device_id == "d1"
    assert command.type == "set_x"
    assert command.validation_status == "inbound"
    assert command.result is CommandResult.IGNORED
    assert command.payload == {"value": Decimal("1")}
    # Puffer geleert.
    assert buffer.drain_due(_ctx(3000)) == ()


def test_drain_orders_by_arrival_sequence() -> None:
    buffer = InboundCommandBuffer()
    buffer.enqueue("d1", "a", {})
    buffer.enqueue("d1", "b", {})
    buffer.enqueue("d1", "c", {})
    commands = buffer.drain_due(_ctx(1000))
    assert [command.type for command in commands] == ["a", "b", "c"]
    assert [command.command_id for command in commands] == [
        "inbound-cmd-0",
        "inbound-cmd-1",
        "inbound-cmd-2",
    ]


def test_empty_drain_is_empty_tuple() -> None:
    assert InboundCommandBuffer().drain_due(_ctx(1000)) == ()


def test_capture_records_resolved_writes() -> None:
    buffer = InboundCommandBuffer()
    buffer.enqueue("d1", "set_x", {"value": Decimal("42")})
    buffer.drain_due(_ctx(5000))
    assert buffer.capture() == (
        InboundWriteCapture(
            resolved_sim_tick=5000,
            target_device_id="d1",
            command_type="set_x",
            payload={"value": Decimal("42")},
            arrival_sequence=0,
        ),
    )


def test_capture_accumulates_across_ticks() -> None:
    buffer = InboundCommandBuffer()
    buffer.enqueue("d1", "a", {})
    buffer.drain_due(_ctx(1000))
    buffer.enqueue("d1", "b", {})
    buffer.drain_due(_ctx(2000))
    capture = buffer.capture()
    assert [entry.resolved_sim_tick for entry in capture] == [1000, 2000]
    assert [entry.arrival_sequence for entry in capture] == [0, 1]


# --- Materialisierung (ADR 0076 §2.1/§2.2) ----------------------------------


def test_materialize_maps_captures_1to1_to_scenario_commands() -> None:
    buffer = InboundCommandBuffer()
    buffer.enqueue("battery-1", "set_power_kw", {"value": Decimal("42.5")})
    buffer.drain_due(_ctx(3000))
    assert materialize_inbound_writes(buffer.capture()) == (
        ScenarioCommand(
            simulation_time=3000,
            target="battery-1",
            type="set_power_kw",
            payload={"value": Decimal("42.5")},
        ),
    )


def test_materialize_orders_by_tick_then_arrival_sequence() -> None:
    # Materialisierung ist von der Capture-Reihenfolge unabhaengig deterministisch:
    # sortiert nach (resolved_sim_tick, arrival_sequence) → byte-identischer Replay.
    captures = (
        InboundWriteCapture(2000, "d1", "b", {}, arrival_sequence=1),
        InboundWriteCapture(1000, "d1", "a", {}, arrival_sequence=0),
        InboundWriteCapture(2000, "d2", "c", {}, arrival_sequence=2),
    )
    commands = materialize_inbound_writes(captures)
    assert [(c.simulation_time, c.type) for c in commands] == [
        (1000, "a"),
        (2000, "b"),
        (2000, "c"),
    ]


def test_materialize_empty_capture_is_empty() -> None:
    assert materialize_inbound_writes(()) == ()
