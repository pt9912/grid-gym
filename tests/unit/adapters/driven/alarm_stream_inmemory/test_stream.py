"""Tests fuer `InMemoryAlarmStream` + `AlarmHistoryBuffer`
(M5 Welle 4b, ADR 0040 Decision 17).

Pattern parallel zu `test_stream.py` aus
`adapters/driven/telemetry_stream_inmemory/`. Async-Tests
benutzen ``asyncio.run`` direkt.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator

from grid_gym.adapters.driven.alarm_stream_inmemory import (
    AlarmHistoryBuffer,
    InMemoryAlarmStream,
)
from grid_gym.hexagon.core.domain.alarm import Alarm


def _make_alarm(*, run_id: str = "r0", alarm_id: str = "a0") -> Alarm:
    return Alarm(
        alarm_id=alarm_id,
        run_id=run_id,
        simulation_time_ms=100,
        target="battery-1",
        code="power_clamp_limited",
        severity="warning",
        message="msg",
        status="active",
        fault_id=None,
    )


# ---------------------------------------------------------------------------
# InMemoryAlarmStream
# ---------------------------------------------------------------------------


def test_single_subscriber_receives_alarms_in_publish_order() -> None:
    """ADR 0040 §2.3: Pub/Sub-Ordnung pro Subscriber."""

    async def scenario() -> list[Alarm]:
        stream = InMemoryAlarmStream(queue_maxsize=4)
        received: list[Alarm] = []

        async def consume(iterator: AsyncIterator[Alarm]) -> None:
            async for alarm in iterator:
                received.append(alarm)
                if len(received) >= 3:
                    return

        consumer = asyncio.create_task(consume(stream.subscribe()))
        await asyncio.sleep(0)  # yield to let subscriber register
        for i in range(3):
            stream.publish(_make_alarm(alarm_id=f"a-{i}"))
        await consumer
        return received

    received = asyncio.run(scenario())
    assert [a.alarm_id for a in received] == ["a-0", "a-1", "a-2"]


def test_subscribe_filter_by_run_id() -> None:
    async def scenario() -> list[Alarm]:
        stream = InMemoryAlarmStream(queue_maxsize=8)
        received: list[Alarm] = []

        async def consume(iterator: AsyncIterator[Alarm]) -> None:
            async for alarm in iterator:
                received.append(alarm)
                if len(received) >= 2:
                    return

        consumer = asyncio.create_task(consume(stream.subscribe(run_id="r1")))
        await asyncio.sleep(0)
        stream.publish(_make_alarm(run_id="r0", alarm_id="a-0"))
        stream.publish(_make_alarm(run_id="r1", alarm_id="a-1"))
        stream.publish(_make_alarm(run_id="r0", alarm_id="a-2"))
        stream.publish(_make_alarm(run_id="r1", alarm_id="a-3"))
        await consumer
        return received

    received = asyncio.run(scenario())
    assert [a.alarm_id for a in received] == ["a-1", "a-3"]
    assert all(a.run_id == "r1" for a in received)


def test_drop_oldest_backpressure_on_full_queue() -> None:
    """ADR 0040 §2.3 + ADR 0038 §2.2 Pattern: Drop-Oldest bei
    voller Queue — juengste Alarms ueberleben.

    Strategie: ein Konsument-Task wird gestartet, parkt am ersten
    `await queue.get()` (registriert dabei den Subscriber); der
    Producer publisht dann 10 Alarms hintereinander **ohne**
    Zwischen-Yields. Sobald die Queue voll ist (maxsize=4),
    drainst `publish` die aelteste Message; die juengsten 4
    ueberleben.
    """

    async def scenario() -> list[Alarm]:
        stream = InMemoryAlarmStream(queue_maxsize=4)
        received: list[Alarm] = []
        ready = asyncio.Event()

        async def consume() -> None:
            async for alarm in stream.subscribe():
                ready.set()
                received.append(alarm)
                if len(received) >= 4:
                    return

        task = asyncio.create_task(consume())
        # Yield bis der Subscriber registriert ist (Generator-
        # Body laeuft bis zum ersten `await queue.get()`).
        while stream.subscriber_count == 0:
            await asyncio.sleep(0)
        # Jetzt publish 10 Alarms ohne Yield zwischendurch.
        for i in range(10):
            stream.publish(_make_alarm(alarm_id=f"a-{i}"))
        await task
        return received

    received = asyncio.run(scenario())
    # Juengste Alarms (a-6..a-9) sollten ueberleben.
    assert [a.alarm_id for a in received] == ["a-6", "a-7", "a-8", "a-9"]


def test_subscribe_unsubscribe_cycle_releases_resources() -> None:
    """ADR 0040 §2.3 + ADR 0038 §2.3 Pattern: try/finally-Cleanup
    nach aclose. Subscriber wird beim ersten `__anext__`
    registriert; nach Cancel + `aclose` ist der Slot frei."""

    async def scenario() -> tuple[int, int]:
        stream = InMemoryAlarmStream(queue_maxsize=4)
        ready = asyncio.Event()

        async def consume() -> None:
            async for _ in stream.subscribe():
                ready.set()

        task = asyncio.create_task(consume())
        while stream.subscriber_count == 0:
            await asyncio.sleep(0)
        active_count = stream.subscriber_count
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        return active_count, stream.subscriber_count

    active, after_close = asyncio.run(scenario())
    assert active == 1
    assert after_close == 0


# ---------------------------------------------------------------------------
# AlarmHistoryBuffer
# ---------------------------------------------------------------------------


def test_history_buffer_appends_and_returns_recent_in_reverse_order() -> None:
    """ADR 0040 §2.3: neueste zuerst."""
    buffer = AlarmHistoryBuffer(max_size=10)
    for i in range(5):
        buffer.append(_make_alarm(alarm_id=f"a-{i}"))
    recent = buffer.get_recent(limit=3)
    assert [a.alarm_id for a in recent] == ["a-4", "a-3", "a-2"]


def test_history_buffer_filters_by_run_id() -> None:
    buffer = AlarmHistoryBuffer(max_size=10)
    buffer.append(_make_alarm(run_id="r0", alarm_id="a-0"))
    buffer.append(_make_alarm(run_id="r1", alarm_id="a-1"))
    buffer.append(_make_alarm(run_id="r0", alarm_id="a-2"))
    recent = buffer.get_recent(run_id="r0")
    assert [a.alarm_id for a in recent] == ["a-2", "a-0"]


def test_history_buffer_ring_evicts_oldest_when_full() -> None:
    """ADR 0040 §2.3: FIFO-Drop bei Capacity-Ueberschreitung
    (deque.maxlen-Verhalten)."""
    buffer = AlarmHistoryBuffer(max_size=3)
    for i in range(5):
        buffer.append(_make_alarm(alarm_id=f"a-{i}"))
    # Nur die letzten 3 ueberleben.
    recent = buffer.get_recent(limit=10)
    assert [a.alarm_id for a in recent] == ["a-4", "a-3", "a-2"]
    assert len(buffer) == 3
