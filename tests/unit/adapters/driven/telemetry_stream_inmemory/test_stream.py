"""Tests fuer `InMemoryTelemetryStream` (M5 Welle 3, ADR 0038).

Pattern entspricht dem Welle-3-Pre-C0c-Probe (`5349923`),
aber gegen die produktive Klasse statt eines Inline-Stubs.
Async-Tests benutzen ``asyncio.run`` direkt (pytest-asyncio
ist im Repo nicht installiert).
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from grid_gym.adapters.driven.telemetry_stream_inmemory.stream import (
    InMemoryTelemetryStream,
)
from grid_gym.hexagon.ports.driving.telemetry_stream import TelemetryPoint


def _make_point(*, run_id: str = "r0", sequence: int = 0) -> TelemetryPoint:
    return TelemetryPoint(
        run_id=run_id,
        device_id="battery-1",
        metric="power",
        value=float(sequence),
        unit="kW",
        simulation_time_ms=sequence * 100,
        quality="ok",
        sequence=sequence,
    )


async def _collect(iterator: AsyncIterator[TelemetryPoint], count: int) -> list[TelemetryPoint]:
    """Konsumiere `count` Points aus einem AsyncIterator."""
    collected: list[TelemetryPoint] = []
    async for point in iterator:
        collected.append(point)
        if len(collected) >= count:
            break
    return collected


def test_publish_without_subscribers_is_no_op() -> None:
    """`publish` ohne Subscribers wirft nichts und macht keinen Effekt."""
    stream = InMemoryTelemetryStream()
    stream.publish(_make_point())
    assert stream.subscriber_count == 0


def test_drop_oldest_when_queue_full() -> None:
    """Bei vollem Subscriber-Buffer droppt der Stream den aeltesten Eintrag.

    Pattern aus ADR 0038 §2.2 + Probe-Run `5349923` Test 3 —
    hier direkt am produktiven `InMemoryTelemetryStream`
    getestet (ohne WebSocket-Wrap, damit die sync-TestClient-
    Race vermieden wird).
    """
    stream = InMemoryTelemetryStream(queue_maxsize=4)
    subscriber_queue: asyncio.Queue[TelemetryPoint] = asyncio.Queue(maxsize=4)
    stream._subscribers.append(subscriber_queue)

    for sequence in range(10):
        stream.publish(_make_point(sequence=sequence))

    assert subscriber_queue.qsize() == 4
    surviving: list[TelemetryPoint] = []
    while not subscriber_queue.empty():
        surviving.append(subscriber_queue.get_nowait())
    assert surviving[-1].sequence == 9
    assert all(p.sequence >= 6 for p in surviving)


def test_subscribe_yields_points_in_order() -> None:
    """`async for`-Konsum liefert publishte Points in Reihenfolge."""

    async def _run() -> list[TelemetryPoint]:
        stream = InMemoryTelemetryStream(queue_maxsize=8)
        iterator = stream.subscribe()
        task = asyncio.create_task(_collect(iterator, count=3))
        for _ in range(5):
            await asyncio.sleep(0)
        for sequence in range(3):
            stream.publish(_make_point(sequence=sequence))
        async with asyncio.timeout(1.0):
            collected = await task
        await iterator.aclose()
        return collected

    result = asyncio.run(_run())
    assert [p.sequence for p in result] == [0, 1, 2]


def test_subscribe_filters_by_run_id() -> None:
    """`subscribe(run_id=...)` filtert Points anderer Runs heraus."""

    async def _run() -> list[TelemetryPoint]:
        stream = InMemoryTelemetryStream(queue_maxsize=8)
        iterator = stream.subscribe(run_id="wanted")
        task = asyncio.create_task(_collect(iterator, count=2))
        for _ in range(5):
            await asyncio.sleep(0)
        stream.publish(_make_point(run_id="other", sequence=0))
        stream.publish(_make_point(run_id="wanted", sequence=1))
        stream.publish(_make_point(run_id="other", sequence=2))
        stream.publish(_make_point(run_id="wanted", sequence=3))
        async with asyncio.timeout(1.0):
            collected = await task
        await iterator.aclose()
        return collected

    result = asyncio.run(_run())
    assert [p.sequence for p in result] == [1, 3]
    assert all(p.run_id == "wanted" for p in result)


def test_subscribe_releases_slot_on_aclose() -> None:
    """`aclose()` raeumt den Subscriber-Slot deterministisch ab (ADR 0038 §2.3)."""

    async def _run() -> tuple[int, int, int]:
        stream = InMemoryTelemetryStream(queue_maxsize=4)
        before = stream.subscriber_count
        iterator = stream.subscribe()
        task = asyncio.create_task(_collect(iterator, count=1))
        for _ in range(5):
            await asyncio.sleep(0)
        during = stream.subscriber_count
        stream.publish(_make_point(sequence=0))
        async with asyncio.timeout(1.0):
            await task
        await iterator.aclose()
        return before, during, stream.subscriber_count

    before, during, after = asyncio.run(_run())
    assert before == 0
    assert during == 1
    assert after == 0


def test_two_subscribers_get_fanout() -> None:
    """Fan-out: zwei Subscribers bekommen dieselben Messages (ADR 0038 §2.1)."""

    async def _run() -> tuple[list[TelemetryPoint], list[TelemetryPoint]]:
        stream = InMemoryTelemetryStream(queue_maxsize=8)
        iter_a = stream.subscribe()
        iter_b = stream.subscribe()
        task_a = asyncio.create_task(_collect(iter_a, count=2))
        task_b = asyncio.create_task(_collect(iter_b, count=2))
        for _ in range(5):
            await asyncio.sleep(0)
        stream.publish(_make_point(sequence=0))
        stream.publish(_make_point(sequence=1))
        async with asyncio.timeout(1.0):
            a_msgs, b_msgs = await asyncio.gather(task_a, task_b)
        await iter_a.aclose()
        await iter_b.aclose()
        return a_msgs, b_msgs

    a_msgs, b_msgs = asyncio.run(_run())
    assert [p.sequence for p in a_msgs] == [0, 1]
    assert [p.sequence for p in b_msgs] == [0, 1]
