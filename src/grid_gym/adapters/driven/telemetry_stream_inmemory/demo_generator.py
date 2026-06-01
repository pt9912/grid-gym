"""Demo-Telemetry-Generator (M5 Welle 3, ADR 0038 §3.1).

Welle-3-Stub-Producer: ein periodischer asyncio-Task, der
synthetische Telemetry-Points fuer einen deterministischen
Demo-Run publisht. Welle 4 (Replay-Controls) ersetzt diesen
Generator durch echtes TickLoop-Wiring; die
`TelemetryStreamPort`-Surface bleibt unveraendert.

Pattern:

- Pro Tick erzeugt der Generator vier Points fuer einen
  Demo-Run: ``battery-1.power`` (sin-Welle, kW),
  ``battery-1.soc`` (langsame cos-Welle, %),
  ``grid-1.power`` (anti-phase sin, kW), ``grid-1.voltage``
  (statisch + leichte Drift, V).
- Sequenznummer ist ein simpler Tick-Counter (auf 2^53
  begrenzt, damit JSON keine Float-Rundung macht).
- Quality ist ``ok`` ausser bei den letzten 2 Ticks eines
  Sinus-Periods (alle 50 Ticks ein ``stale``), damit das
  UI alle 5 Sekunden mindestens einen non-OK-Marker
  sieht.
"""

from __future__ import annotations

import asyncio
import math
from typing import Final

from grid_gym.adapters.driven.telemetry_stream_inmemory.stream import (
    InMemoryTelemetryStream,
)
from grid_gym.hexagon.ports.driving.telemetry_stream import (
    TelemetryPoint,
    TelemetryQuality,
)

_DEMO_RUN_ID: Final[str] = "demo-run-0001"
_TICK_INTERVAL_S: Final[float] = 0.2
_SEQUENCE_MAX: Final[int] = 1 << 53
_TICK_MS_PER_INCREMENT: Final[int] = 100


def _make_demo_points(tick: int) -> list[TelemetryPoint]:
    """Vier Demo-Telemetry-Points pro Tick (Welle-3-Stub-Shape)."""
    sim_time_ms = tick * _TICK_MS_PER_INCREMENT
    phase = (tick % 50) / 50.0
    quality: TelemetryQuality = "stale" if tick % 50 in {48, 49} else "ok"
    return [
        TelemetryPoint(
            run_id=_DEMO_RUN_ID,
            device_id="battery-1",
            metric="power",
            value=round(50.0 * math.sin(phase * 2 * math.pi), 3),
            unit="kW",
            simulation_time_ms=sim_time_ms,
            quality=quality,
            sequence=tick % _SEQUENCE_MAX,
        ),
        TelemetryPoint(
            run_id=_DEMO_RUN_ID,
            device_id="battery-1",
            metric="soc",
            value=round(50.0 + 30.0 * math.cos(phase * math.pi), 3),
            unit="%",
            simulation_time_ms=sim_time_ms,
            quality=quality,
            sequence=tick % _SEQUENCE_MAX,
        ),
        TelemetryPoint(
            run_id=_DEMO_RUN_ID,
            device_id="grid-1",
            metric="power",
            value=round(-50.0 * math.sin(phase * 2 * math.pi), 3),
            unit="kW",
            simulation_time_ms=sim_time_ms,
            quality=quality,
            sequence=tick % _SEQUENCE_MAX,
        ),
        TelemetryPoint(
            run_id=_DEMO_RUN_ID,
            device_id="grid-1",
            metric="voltage",
            value=round(230.0 + 0.5 * math.sin(phase * 4 * math.pi), 3),
            unit="V",
            simulation_time_ms=sim_time_ms,
            quality=quality,
            sequence=tick % _SEQUENCE_MAX,
        ),
    ]


class DemoTelemetryGenerator:
    """Asyncio-Task, der periodisch Demo-Telemetry publisht.

    Lifecycle: ``start(stream)`` startet eine Background-Task,
    ``stop()`` cancelt sie und wartet auf Cleanup. Pattern
    fuer FastAPI-Lifespan-Hook (siehe `app.py`).
    """

    def __init__(self, *, tick_interval_s: float = _TICK_INTERVAL_S) -> None:
        self._tick_interval_s = tick_interval_s
        self._task: asyncio.Task[None] | None = None
        self._stream: InMemoryTelemetryStream | None = None

    def start(self, stream: InMemoryTelemetryStream) -> None:
        """Startet den Producer-Task (idempotent)."""
        if self._task is not None and not self._task.done():
            return
        self._stream = stream
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Cancelt den Producer-Task und wartet auf Cleanup."""
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
            self._stream = None

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def _run_loop(self) -> None:
        if self._stream is None:
            return
        tick = 0
        while True:
            for point in _make_demo_points(tick):
                self._stream.publish(point)
            tick += 1
            await asyncio.sleep(self._tick_interval_s)
