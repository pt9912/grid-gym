"""Geteilte Test-Doubles fuer TickLoop-Tests (M7 Welle 3a,
C2-Review-Folge F3).

`LaggingEmitterDevice` lebt hier als Single-Source fuer Unit-
(`test_tick_loop_welle_3a_max_age.py`) und Integration-Tests
(`test_m6_welle_5a_safe_001_004_smoke.py`) — vorher waren zwei
nahezu identische Klassen dupliziert. Pattern analog
`tests/unit/hexagon/ports/driven/_fakes.py` (FakeClock/
FixedSeedRandom), die Integration-Tests bereits importieren.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Self

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext, DeviceTickOutcome
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.random import RandomPort


class LaggingEmitterDevice:
    """Test-Double: emittiert pro Tick einen Punkt mit nachlaufendem
    Sim-Zeitstempel (`simulation_time - lag_ms`) und gegebener
    Quality. Produktive Devices emittieren frische Punkte (Alter 0)
    — der Lag ist die Test-Substanz fuer die `max_age`-STALE-Stage
    (ADR 0052 §6 „bewusste Grenze"; M7-welle-3a R2)."""

    def __init__(
        self,
        device_id: str = "lagging-001",
        *,
        lag_ms: int,
        quality: Quality = Quality.VALID,
    ) -> None:
        self._device_id = device_id
        self._lag_ms = lag_ms
        self._quality = quality
        self._run_id = ""

    @property
    def device_id(self) -> str:
        return self._device_id

    def initialize(self, scenario_device: ScenarioDevice, random: RandomPort) -> None:
        _ = scenario_device
        _ = random

    def apply_command(self, command: Command) -> CommandResult:
        _ = command
        return CommandResult.IGNORED

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        return DeviceTickOutcome(
            telemetry=(
                TelemetryPoint(
                    run_id=self._run_id,
                    tick=context.tick,
                    simulation_time=context.simulation_time - self._lag_ms,
                    device_id=self._device_id,
                    metric="power_kw",
                    value=Decimal("1"),
                    unit="kW",
                    quality=self._quality,
                    source="test_lagging_emitter",
                    sequence=1,
                ),
            ),
        )

    def snapshot(self) -> Mapping[str, object]:
        return {"version": 1}

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return ()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        _ = state
        return cls(lag_ms=0)

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id
