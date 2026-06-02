"""In-Memory Pub/Sub-Implementation des AlarmStreamPort (ADR 0040
Decision 17).

Pattern 1:1 parallel zu `InMemoryTelemetryStream` (ADR 0038 §2.2):

- ``publish(alarm)``: iteriert ueber alle Subscribers,
  drained bei voller Queue eine alte Message (drop-oldest),
  pusht den neuen Alarm via ``put_nowait``.
- ``subscribe(run_id)``: AsyncIterator; eigene bounded
  ``asyncio.Queue`` pro Subscriber, `try/finally`-Cleanup
  garantiert deterministische Slot-Freigabe.
- Filter nach ``run_id`` direkt im AsyncGenerator-Body.

Welle-4b-Default `queue_maxsize=64` ist kleiner als Telemetry's
128, weil Alarms typischerweise niederfrequent sind (Power-Clamp
pro Tick = Ausnahme). ~6.4s Buffer bei 100ms-Tick-Rate reicht
fuer Browser-Tab-Sleep-Resilience.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Final

from grid_gym.hexagon.core.domain.alarm import Alarm


_DEFAULT_QUEUE_MAXSIZE: Final[int] = 64
"""Default-Buffer pro Subscriber (ADR 0040 §2.3).

64 Slots bei 100ms-Tick-Rate (`GG-SIM-002` standard) ueberbrueckt
rund 6.4s Browser-Tab-Sleep ohne sichtbare Drops; kleiner als
Telemetry's 128 weil Alarms niederfrequenter sind.
"""


class InMemoryAlarmStream:
    """Asyncio-basierter Pub/Sub-Stream (AlarmStreamPort-Impl)."""

    def __init__(self, *, queue_maxsize: int = _DEFAULT_QUEUE_MAXSIZE) -> None:
        self._subscribers: list[asyncio.Queue[Alarm]] = []
        self._queue_maxsize = queue_maxsize

    def publish(self, alarm: Alarm) -> None:
        for subscriber in self._subscribers:
            if subscriber.full():
                with contextlib.suppress(asyncio.QueueEmpty):
                    subscriber.get_nowait()
            subscriber.put_nowait(alarm)

    async def subscribe(self, run_id: str | None = None) -> AsyncIterator[Alarm]:
        queue: asyncio.Queue[Alarm] = asyncio.Queue(maxsize=self._queue_maxsize)
        self._subscribers.append(queue)
        try:
            while True:
                alarm = await queue.get()
                if run_id is None or alarm.run_id == run_id:
                    yield alarm
        finally:
            self._subscribers.remove(queue)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
