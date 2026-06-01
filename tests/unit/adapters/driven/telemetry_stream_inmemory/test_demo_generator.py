"""Tests fuer `DemoTelemetryGenerator` (M5 Welle 3, ADR 0038 §3.1).

Pruefen die Lifecycle-Semantik (idempotent start, sauberes
stop) und die Tick-Shape (4 Points/Tick mit `demo-run-0001`).
"""

from __future__ import annotations

import asyncio

from grid_gym.adapters.driven.telemetry_stream_inmemory.demo_generator import (
    DemoTelemetryGenerator,
    _make_demo_points,
)


def test_make_demo_points_produces_four_devices_per_tick() -> None:
    """Welle-3-Demo-Stub erzeugt 4 Points pro Tick (2 Devices x 2 Metriken)."""
    points = _make_demo_points(tick=0)
    assert len(points) == 4
    devices_metrics = {(p.device_id, p.metric) for p in points}
    assert devices_metrics == {
        ("battery-1", "power"),
        ("battery-1", "soc"),
        ("grid-1", "power"),
        ("grid-1", "voltage"),
    }
    assert all(p.run_id == "demo-run-0001" for p in points)
    assert all(p.sequence == 0 for p in points)


def test_make_demo_points_quality_marker_appears_periodically() -> None:
    """Quality `stale` taucht 2 von 50 Ticks auf (UI-Visualisierungs-Beleg)."""
    qualities = [_make_demo_points(tick=t)[0].quality for t in range(50)]
    assert qualities.count("stale") == 2
    assert qualities.count("ok") == 48


def test_demo_generator_lifecycle_start_idempotent_and_stop_releases() -> None:
    """`start()` ist idempotent; `stop()` bringt den Task in done state."""

    async def _run() -> tuple[bool, bool, bool]:
        generator = DemoTelemetryGenerator(tick_interval_s=0.01)
        # Vorm Start ist nichts aktiv.
        before = generator.is_running
        # Dummy-Stream-Ersatz: produktiv ist es ein InMemory-Stream;
        # fuer den Lifecycle-Test reicht ein leerer Singleton, dem wir
        # publish-Calls zumuten. Wir nutzen InMemoryTelemetryStream,
        # damit publish keine AttributeError wirft.
        from grid_gym.adapters.driven.telemetry_stream_inmemory.stream import (
            InMemoryTelemetryStream,
        )

        stream = InMemoryTelemetryStream(queue_maxsize=4)
        generator.start(stream)
        generator.start(stream)  # idempotent — kein zweiter Task.
        during = generator.is_running
        await asyncio.sleep(0.05)
        await generator.stop()
        after = generator.is_running
        return before, during, after

    before, during, after = asyncio.run(_run())
    assert before is False
    assert during is True
    assert after is False


def test_demo_generator_stop_without_start_is_no_op() -> None:
    """`stop()` ohne vorigen `start` wirft nichts."""

    async def _run() -> None:
        generator = DemoTelemetryGenerator()
        await generator.stop()

    asyncio.run(_run())
