"""Bench-Fixtures + ADR-0041-§2.2-Konfig-Marker fuer M6 Welle 4b-a/b.

`BenchStubDevice` ist eine minimale `DeviceModel`-Implementation, die
das Protocol erfuellt, aber pro Tick nichts berechnet. Das misst den
TickLoop-Overhead pro Geraet (`GG-RT-004`-Akzeptanz: 100 Geraete x
10 000 Ticks) ohne Geraete-spezifische Last.

`pytest_configure`-Hook erzwingt die ADR-0041 §2.2-Pflicht-Bench-
Parameter (`--benchmark-min-rounds=10`, `--benchmark-disable-gc`,
`--benchmark-warmup=on`) ohne CLI-Argumente — die Welle-4b-b-C2-
Review-Folge-F1-HIGH-Finding (ADR-0041-§2.2-Vertragsbruch) ist
dadurch geschlossen.

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

# ADR-0041 §2.2 Pflicht-Parameter; werden in `pytest_configure`
# applied. pytest-benchmark-Defaults sind anders (min_rounds=5,
# disable_gc=False, warmup=False), was die Welle-4b-a/b-Baselines
# zu nicht-ADR-konformen Mess-Substanzen gemacht hatte (siehe
# Welle-4b-b-C2-Review-Folge F1 HIGH).
_ADR_0041_MIN_ROUNDS = 10
_PYTEST_BENCHMARK_DEFAULT_MIN_ROUNDS = 5


def pytest_configure(config: pytest.Config) -> None:
    """ADR-0041 §2.2-Pflicht-Bench-Parameter erzwingen.

    Wirkt nur, wenn pytest-benchmark geladen ist (`--extra perf`);
    sonst No-Op. CLI-Override (z. B.
    `--benchmark-min-rounds=20`) bleibt moeglich — der Hook
    schreibt nur ueber den pytest-benchmark-Default, nicht ueber
    explizite User-Werte.
    """

    if not hasattr(config.option, "benchmark_min_rounds"):
        return

    if config.option.benchmark_min_rounds == _PYTEST_BENCHMARK_DEFAULT_MIN_ROUNDS:
        config.option.benchmark_min_rounds = _ADR_0041_MIN_ROUNDS
    config.option.benchmark_disable_gc = True
    config.option.benchmark_warmup = "on"


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
