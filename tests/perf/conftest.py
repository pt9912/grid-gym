"""Bench-Fixtures fuer M6 Welle 4b-a (ADR 0041).

`BenchStubDevice` ist eine minimale `DeviceModel`-Implementation, die
das Protocol erfuellt, aber pro Tick nichts berechnet. Das misst den
TickLoop-Overhead pro Geraet (`GG-RT-004`-Akzeptanz: 100 Geraete x
10 000 Ticks) ohne Geraete-spezifische Last.

Cross-Test-Reuse: bleibt in `tests/perf/conftest.py`, nicht in
`tests/unit/`-Fixtures (Bench-Layer ist eigenstaendig per ADR-0041
§2.4).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Self

import pytest

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext, DeviceTickOutcome
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.random import RandomPort

_SNAPSHOT_VERSION = 1


class BenchStubDevice:
    """Minimal `DeviceModel`-Stub fuer Bench-Tests. Tut nichts.

    Implementiert das Welle-3-Review-M-4-`set_run_id`-Lifecycle-Hook
    (`TickLoop._attach_devices` ruft das pro Konstruktor-Lauf) plus
    den ADR-0013-Pflicht-Surface (initialize/apply_command/tick/
    snapshot/telemetry/from_snapshot/device_id).
    """

    __slots__ = ("_device_id", "_initialized", "_run_id")

    def __init__(self, device_id: str, *, pre_initialized: bool = False) -> None:
        self._device_id = device_id
        self._initialized = pre_initialized
        self._run_id = ""

    @property
    def device_id(self) -> str:
        return self._device_id

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id

    def initialize(
        self,
        scenario_device: ScenarioDevice,
        random: RandomPort,
    ) -> None:
        del scenario_device, random
        self._initialized = True

    def apply_command(self, command: Command) -> CommandResult:
        del command
        return CommandResult.ACCEPTED

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        del context
        return DeviceTickOutcome(telemetry=())

    def snapshot(self) -> Mapping[str, object]:
        return {"version": _SNAPSHOT_VERSION, "device_id": self._device_id}

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return ()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        device_id = str(state["device_id"])
        return cls(device_id, pre_initialized=True)


@pytest.fixture
def bench_devices() -> tuple[BenchStubDevice, ...]:
    """100 BenchStubDevices fuer `GG-RT-004`-Akzeptanz."""

    return tuple(BenchStubDevice(f"bench-{i:03d}", pre_initialized=True) for i in range(100))
