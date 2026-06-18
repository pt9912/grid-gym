"""Pins fuer `ScenarioCommandEngine.due_commands` (S2, ADR 0070, Trigger 046).

Stateless tick-genaue Faelligkeit: ein Command ist in dem Tick faellig, dessen
half-open Span `[now, now + tick_ms)` seine `simulation_time` enthaelt. Plus
`_to_command`-Feld-Mapping + Source-Reihenfolge.
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.hexagon.core.commands import ScenarioCommandEngine
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioCommand


def _ctx(simulation_time: int, tick_ms: int = 1000) -> DeviceTickContext:
    return DeviceTickContext(
        tick=simulation_time // tick_ms, simulation_time=simulation_time, tick_ms=tick_ms
    )


def _sc(
    simulation_time: int,
    *,
    target: str = "dev-1",
    command_type: str = "set_power_kw",
    value: str = "20",
) -> ScenarioCommand:
    return ScenarioCommand(
        simulation_time=simulation_time,
        target=target,
        type=command_type,
        payload={"value": Decimal(value)},
    )


def test_command_due_only_in_its_tick_span() -> None:
    engine = ScenarioCommandEngine([_sc(5000)])
    assert engine.due_commands(_ctx(4000)) == ()
    assert len(engine.due_commands(_ctx(5000))) == 1
    assert engine.due_commands(_ctx(6000)) == ()


def test_non_aligned_command_falls_in_containing_span() -> None:
    """`simulation_time=5500`, `tick_ms=1000` -> faellig im Span [5000, 6000)."""
    engine = ScenarioCommandEngine([_sc(5500)])
    assert engine.due_commands(_ctx(5000)) != ()
    assert engine.due_commands(_ctx(4000)) == ()
    assert engine.due_commands(_ctx(6000)) == ()


def test_empty_engine_returns_no_commands() -> None:
    engine = ScenarioCommandEngine([])
    assert engine.due_commands(_ctx(1000)) == ()


def test_to_command_maps_fields_in_source_order() -> None:
    engine = ScenarioCommandEngine(
        [
            _sc(1000, target="a", command_type="set_power_kw", value="10"),
            _sc(1000, target="b", command_type="set_charge_power", value="20"),
        ]
    )
    due = engine.due_commands(_ctx(1000))
    assert [c.command_id for c in due] == ["scenario-cmd-0", "scenario-cmd-1"]
    first = due[0]
    assert first.target_device_id == "a"
    assert first.type == "set_power_kw"
    assert first.payload["value"] == Decimal("10")
    assert first.validation_status == "scenario"
    assert first.result is CommandResult.IGNORED
    assert due[1].target_device_id == "b"
    assert due[1].simulation_time == 1000
