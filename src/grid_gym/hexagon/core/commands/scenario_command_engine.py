"""ScenarioCommandEngine — die pro Tick faelligen scenario-geplanten Commands
(ADR 0070, Trigger 046; S2).

Stateless + tick-genau: ein `ScenarioCommand` ist in dem Tick faellig, dessen
half-open Span `[now, now + tick_ms)` seine geplante `simulation_time` enthaelt
(analog der Fault-Fenster-Logik, ADR 0022 §2.4). Kein Mutations-State ->
deterministisch + resume-kontinuierlich ohne Snapshot (die Faelligkeit wird pro
Tick allein aus `context.simulation_time` re-derived).
"""

from __future__ import annotations

from collections.abc import Sequence

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioCommand

_SCENARIO_VALIDATION_STATUS = "scenario"


class ScenarioCommandEngine:
    """Haelt die scenario-geplanten Commands + liefert die pro Tick faelligen.

    Die `Command`-Objekte werden einmal im Konstruktor aus `scenario.commands`
    vorgebaut (stabiler `command_id`-Index = Source-Reihenfolge, Determinismus
    ADR 0070 §2.3). Targets sind beim Scenario-Load gegen `devices` validiert
    (`_assert_command_list`); die Engine trifft keine Existenz-Aussage.
    """

    def __init__(self, commands: Sequence[ScenarioCommand]) -> None:
        self._commands: tuple[Command, ...] = tuple(
            _to_command(command, index) for index, command in enumerate(commands)
        )

    def due_commands(self, context: DeviceTickContext) -> tuple[Command, ...]:
        """Commands, deren `simulation_time` in den half-open Span
        `[now, now + tick_ms)` des aktuellen Ticks faellt (Source-Reihenfolge).

        Stateless -> deterministisch + resume-sicher (kein Delivered-Set; jeder
        Tick re-derived die Faelligkeit aus `context.simulation_time`)."""
        now = context.simulation_time
        upper = now + context.tick_ms
        return tuple(
            command for command in self._commands if now <= command.simulation_time < upper
        )


def _to_command(command: ScenarioCommand, index: int) -> Command:
    """Baut das Runtime-`Command` aus einem `ScenarioCommand`. `result` ist ein
    Pre-Apply-Platzhalter (`IGNORED`, wie der Agent-Pfad in `rule_based`); den
    echten Status liefert `device.apply_command(...)` zurueck."""
    return Command(
        command_id=f"scenario-cmd-{index}",
        simulation_time=command.simulation_time,
        target_device_id=command.target,
        type=command.type,
        payload=command.payload,
        validation_status=_SCENARIO_VALIDATION_STATUS,
        result=CommandResult.IGNORED,
    )
