"""Test-Doubles fuer das `DeviceModel`-Protocol (M2 Welle 1).

`NullDevice` ist eine minimale Implementation, die alle fuenf
Protocol-Methoden mit No-Op-Verhalten erfuellt. Wird in
`test_protocol_contract.py` zur Protocol-Adherence-Pruefung
genutzt; M2 Welle 2..5 koennen die Klasse als Baseline-Vergleich
und Plattform fuer Tick-Loop-Integration-Tests wiederverwenden.

Konvention (siehe ADR 0013 §5): Test-Doubles liegen unter
`tests/unit/hexagon/core/devices/_fakes.py`. Konkrete Geraete-
Tests (Battery in Welle 2 etc.) duerfen `NullDevice` importieren,
um z. B. einen Tick-Loop mit gemischten Geraeten zu fahren.
"""

from __future__ import annotations

from collections.abc import Mapping

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import (
    DeviceTickContext,
    DeviceTickOutcome,
)
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.random import RandomPort


class NullDevice:
    """No-Op-Implementation des `DeviceModel`-Protocols.

    Methoden-Verhalten:

    - `initialize(scenario_device, random)` — speichert beide
      Argumente als Instanz-Zustand, damit Tests sie auslesen
      koennen.
    - `apply_command(command)` — gibt immer
      `CommandResult.IGNORED` zurueck (No-Op-Verhalten;
      Geraet implementiert keinen Command-Pfad).
    - `tick(context)` — gibt `DeviceTickOutcome(telemetry=())`
      zurueck (keine Telemetrie). Speichert `last_context` als
      Instanz-Zustand fuer Test-Assertions.
    - `snapshot()` — gibt `{"version": 1}` zurueck (Erst-Feld-
      Konvention erfuellt; kein weiterer State).
    - `telemetry()` — gibt `()` zurueck.

    Keine `from_snapshot`-Classmethod — der Roundtrip-Vertrag
    (`from_snapshot(snapshot()) == device`) wird erst von konkreten
    Geraete-Implementationen (Welle 2..5) erfuellt; NullDevice
    deckt nur den Protocol-Surface-Check ab.
    """

    SNAPSHOT_VERSION = 1

    def __init__(self) -> None:
        self.scenario_device: ScenarioDevice | None = None
        self.random: RandomPort | None = None
        self.last_context: DeviceTickContext | None = None
        self.applied_commands: list[Command] = []

    def initialize(
        self,
        scenario_device: ScenarioDevice,
        random: RandomPort,
    ) -> None:
        self.scenario_device = scenario_device
        self.random = random

    def apply_command(self, command: Command) -> CommandResult:
        self.applied_commands.append(command)
        return CommandResult.IGNORED

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        self.last_context = context
        return DeviceTickOutcome(telemetry=())

    def snapshot(self) -> Mapping[str, object]:
        return {"version": self.SNAPSHOT_VERSION}

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return ()
