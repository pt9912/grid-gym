"""In-Memory Pub/Sub-Implementation des TelemetryStreamPort (ADR 0038).

Pattern aus dem Pre-C0c-Probe-Run `5349923`:

- ``publish(point)``: iteriert ueber alle Subscribers,
  drained bei voller Queue eine alte Message (drop-oldest),
  pusht die neue Message via ``put_nowait``.
- ``subscribe(run_id)``: AsyncIterator; eigene bounded
  ``asyncio.Queue`` pro Subscriber, `try/finally`-Cleanup
  garantiert deterministische Slot-Freigabe.
- Filter nach ``run_id`` direkt im AsyncGenerator-Body.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Final

from grid_gym.hexagon.ports.driving.telemetry_stream import TelemetryPoint

_DEFAULT_QUEUE_MAXSIZE: Final[int] = 128
"""Default-Buffer pro Subscriber (ADR 0038 §2.2).

128 Slots bei 100ms-Tick-Rate (`GG-SIM-002` standard)
ueberbrueckt rund 1.3s Browser-Tab-Sleep ohne sichtbare
Drops.
"""


class InMemoryTelemetryStream:
    """Asyncio-basierter Pub/Sub-Stream (TelemetryStreamPort-Impl)."""

    def __init__(self, *, queue_maxsize: int = _DEFAULT_QUEUE_MAXSIZE) -> None:
        self._subscribers: list[asyncio.Queue[TelemetryPoint]] = []
        self._queue_maxsize = queue_maxsize

    def publish(self, point: TelemetryPoint) -> None:
        for subscriber in self._subscribers:
            if subscriber.full():
                with contextlib.suppress(asyncio.QueueEmpty):
                    subscriber.get_nowait()
            subscriber.put_nowait(point)

    async def subscribe(self, run_id: str | None = None) -> AsyncIterator[TelemetryPoint]:
        queue: asyncio.Queue[TelemetryPoint] = asyncio.Queue(maxsize=self._queue_maxsize)
        self._subscribers.append(queue)
        try:
            while True:
                point = await queue.get()
                if run_id is None or point.run_id == run_id:
                    yield point
        finally:
            self._subscribers.remove(queue)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
