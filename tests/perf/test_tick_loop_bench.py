"""`GG-RT-004` Bench: 100 Geraete x 10 000 Ticks (M6 Welle 4b-a; ADR 0041).

Pflicht-Doppel-Akzeptanz per ADR-0041 §2.2 (Lastenheft Z.486):

1. **lost_events == 0**: Ueber den vollen Lauf werden alle 10 000 Ticks
   verarbeitet ohne Drop (Proxy: `tick_loop.tick_count == 10000` nach
   dem Lauf).
2. **Replay-Diff-Determinismus**: Zwei Laeufe mit identischem Seed
   liefern byte-identische Geraete-Snapshots am Lauf-Ende. Die TickLoop-
   Top-Level-`snapshot()`-Methode wird in Welle-4b-a NICHT genutzt,
   weil `BenchStubDevice` nicht im produktiven
   `_DEVICE_TYPE_BY_CLASS_NAME`-Mapping registriert ist (das ist
   bewusste Anti-Scope-Wahl: die Bench misst TickLoop-Overhead, nicht
   produktiven Snapshot-Pfad — Welle 4b-b/4b-c koennen das mit echten
   Geraete-Klassen schaerfen).

Bench-Framework: pytest-benchmark (`>=4.0,<6.0`) per ADR-0041 §2.1
(opt-in via `--extra perf`).

Run: `make perf` (Dockerfile-`perf`-Stage). Baseline-Update:
`make perf-baseline-update` (Bind-Mount-Pattern; loest GNU-Make-
Option-Konflikt mit `--benchmark-save`).
"""

from __future__ import annotations

from collections.abc import Mapping

from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.perf.conftest import BenchStubDevice
from tests.unit.hexagon.ports.driven._fakes import (
    FakeClock,
    FixedSeedRandom,
    InMemoryRunRepository,
)

_TICK_COUNT = 10_000
_DEVICE_COUNT = 100
_SEED = 42
_TICK_MS = 100


def _build_tick_loop(seed: int = _SEED) -> TickLoop:
    """Konstruiert einen TickLoop mit 100 BenchStubDevices (`GG-RT-004`)."""

    devices = tuple(
        BenchStubDevice(f"bench-{i:03d}", pre_initialized=True) for i in range(_DEVICE_COUNT)
    )
    run_id = "bench-rt-004"
    repository = InMemoryRunRepository()
    repository.save(
        RunMetadata(
            run_id=run_id,
            scenario_hash="0" * 64,
            schema_version="grid-gym.scenario.v1",
            seed=seed,
            tick_ms=_TICK_MS,
            started_at="2026-06-06T00:00:00Z",
            ended_at="",
            tool_version="bench",
        )
    )
    return TickLoop(
        run_id=run_id,
        tick_ms=_TICK_MS,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=seed),
        scheduler=Scheduler(),
        run_repository=repository,
        devices=devices,
    )


def _device_snapshots(tick_loop: TickLoop) -> tuple[Mapping[str, object], ...]:
    """Sammelt die Snapshots aller Devices in registrierter Reihenfolge.

    Welle-4b-a-Anti-Scope: `tick_loop.snapshot()` wuerde fuer
    `BenchStubDevice` einen `TickLoopUnknownDeviceTypeError` werfen,
    weil die Stub-Klasse nicht im produktiven
    `_DEVICE_TYPE_BY_CLASS_NAME`-Mapping registriert ist (Anti-Scope-
    Wahl per Modul-Docstring). Stattdessen sammeln wir die einzelnen
    Device-Snapshots direkt — das misst die Replay-Determinismus-
    Equivalent fuer den Bench-Scope.
    """

    return tuple(device.snapshot() for device in tick_loop._devices)


def _run_bench_loop(
    seed: int = _SEED,
) -> tuple[int, tuple[Mapping[str, object], ...]]:
    """Einzelner GG-RT-004-Lauf: 100 Devices x 10 000 Ticks.

    Returns (final_tick_count, per_device_snapshots).
    """

    tick_loop = _build_tick_loop(seed=seed)
    for _ in range(_TICK_COUNT):
        tick_loop.tick()
    return tick_loop.tick_count, _device_snapshots(tick_loop)


def test_gg_rt_004_100_devices_10000_ticks(benchmark) -> None:  # type: ignore[no-untyped-def]
    """`GG-RT-004` Doppel-Akzeptanz per ADR-0041 §2.2:

    - lost_events == 0 (proxy: tick_count == 10000 nach dem Lauf).
    - Replay-Diff-Determinismus ueber zwei Runs mit identischem Seed.
    """

    final_tick_count, snapshots_a = benchmark(_run_bench_loop)

    # Assert 1: lost_events == 0 (Proxy via tick_count)
    assert final_tick_count == _TICK_COUNT, (
        f"GG-RT-004 lost_events check failed: expected {_TICK_COUNT} ticks, got {final_tick_count}"
    )

    # Assert 2: Replay-Diff-Determinismus
    _, snapshots_b = _run_bench_loop()
    assert snapshots_a == snapshots_b, (
        "GG-RT-004 Replay-Diff-Determinismus verletzt: "
        "zwei Runs mit identischem Seed liefern unterschiedliche "
        "Device-Snapshots."
    )
