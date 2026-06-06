"""Unit-Tests fuer `TickLoopHealthcheckAdapter` (M6 Welle 4b-c;
`GG-RT-001` 10ms-Modus).

Welle-4b-c-D-1 Adapter-Side-Mess; D-2 `time.perf_counter()` (per
Welle-4b-c-C0-Review-Folge F1 als injectable `clock_source`); D-3
Window-Size 100; D-4 Single-Miss-Schwelle.

Test-Pattern: Fake-Clock-Injection statt globalem monkeypatch von
`time.perf_counter()`; ohne Injection waeren Tests real-time-
abhaengig und flaky.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

import pytest

from grid_gym.adapters.driving.http_api._tick_loop_healthcheck import (
    TickLoopHealthcheckAdapter,
)
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop


@dataclass
class _FakeTickLoop:
    """Minimaler TickLoop-Stub: nur `tick_ms`-Property wird vom
    Healthcheck-Adapter gelesen.

    Welle-4b-c-C2-Review-Folge F2: `cast(TickLoop, _FakeTickLoop())`
    am Aufruf-Site ist sauberer als `# type: ignore[arg-type]`-
    Marker, weil cast die Intention explizit dokumentiert
    (Duck-Typing-Bekenntnis).
    """

    tick_ms: int


def _build_adapter(
    *,
    tick_ms: int = 10,
    window_size: int = 100,
    clock_source: Callable[[], float] | None = None,
) -> TickLoopHealthcheckAdapter:
    """Test-Builder: Fake-TickLoop + optionaler Clock-Source-
    Override (Welle-4b-c-C0-Review-Folge F1).

    Default Clock-Source bleibt `time.perf_counter`; Tests
    injizieren typischerweise eine controlled-sequence-Clock.
    """
    fake_tick_loop = cast(TickLoop, _FakeTickLoop(tick_ms=tick_ms))
    if clock_source is None:
        return TickLoopHealthcheckAdapter(
            fake_tick_loop,
            window_size=window_size,
        )
    return TickLoopHealthcheckAdapter(
        fake_tick_loop,
        window_size=window_size,
        clock_source=clock_source,
    )


def test_healthcheck_no_recorded_ticks_returns_zero_values() -> None:
    """Welle-4b-c §1.2: bei leerem Window alle numerischen Felder
    0.0/0 und status `ok`."""

    adapter = _build_adapter(tick_ms=10)
    result = adapter.healthcheck()

    assert result["tick_duration_ms_p50"] == pytest.approx(0.0)
    assert result["tick_duration_ms_p95"] == pytest.approx(0.0)
    assert result["missed_ticks_count"] == 0
    assert result["backpressure_status"] == "ok"
    assert result["tick_ms"] == 10
    assert result["window_size"] == 0


def test_healthcheck_records_tick_durations() -> None:
    """`record_tick_duration` fuegt Werte zum Ring-Buffer hinzu;
    window_size reflektiert die Anzahl."""

    adapter = _build_adapter(tick_ms=10)
    for duration in [1.0, 2.0, 3.0]:
        adapter.record_tick_duration(duration)

    result = adapter.healthcheck()
    assert result["window_size"] == 3


def test_healthcheck_p95_jitter_calculated_correctly() -> None:
    """p50 und p95 nutzen nearest-rank-Approximation:
    - p50_idx = int(n * 0.5)
    - p95_idx = int(n * 0.95)

    Bei 100 sortierten Werten (1.0, 2.0, ..., 100.0) ist:
    - p50_idx = 50 → sorted[50] = 51.0
    - p95_idx = 95 → sorted[95] = 96.0
    """

    adapter = _build_adapter(tick_ms=1000, window_size=100)
    # Werte 1..100 in random order, damit `sorted()` sichtbar wirkt.
    for value in [50.0, 1.0, 100.0, 25.0, 75.0]:
        adapter.record_tick_duration(value)
    # Plus 95 weitere Werte 2..96 (so dass insgesamt 100 distincte Werte sind).
    for value in (
        [float(i) for i in range(2, 25)]
        + [float(i) for i in range(26, 50)]
        + [float(i) for i in range(51, 75)]
        + [float(i) for i in range(76, 100)]
    ):
        adapter.record_tick_duration(value)

    result = adapter.healthcheck()
    # n=100; p50_idx = 50; sorted hat Werte 1..100 → sorted[50] = 51.0
    assert result["window_size"] == 100
    assert result["tick_duration_ms_p50"] == pytest.approx(51.0)
    # n=100; p95_idx = 95; sorted[95] = 96.0
    assert result["tick_duration_ms_p95"] == pytest.approx(96.0)


def test_healthcheck_missed_ticks_counted() -> None:
    """Welle-4b-c-D-4: Ticks mit Dauer > tick_ms zaehlen als missed."""

    adapter = _build_adapter(tick_ms=10)
    # 3 Ticks innerhalb Budget (<=10), 2 Ticks ueberschreitend (>10).
    for duration in [5.0, 10.0, 9.5, 11.0, 15.0]:
        adapter.record_tick_duration(duration)

    result = adapter.healthcheck()
    assert result["missed_ticks_count"] == 2


def test_healthcheck_backpressure_status_ok_when_no_misses() -> None:
    """Alle Durations <= tick_ms → status `ok`."""

    adapter = _build_adapter(tick_ms=100)
    for duration in [1.0, 2.0, 50.0, 99.5, 100.0]:
        adapter.record_tick_duration(duration)

    result = adapter.healthcheck()
    assert result["backpressure_status"] == "ok"
    assert result["missed_ticks_count"] == 0


def test_healthcheck_backpressure_status_delayed_after_miss() -> None:
    """Welle-4b-c-D-4: schon ein einziger missed Tick im Window
    setzt den Status auf `delayed` (binaere Schwelle)."""

    adapter = _build_adapter(tick_ms=10)
    for duration in [1.0, 2.0, 3.0, 4.0]:
        adapter.record_tick_duration(duration)
    adapter.record_tick_duration(11.0)  # Einziger missed Tick

    result = adapter.healthcheck()
    assert result["backpressure_status"] == "delayed"
    assert result["missed_ticks_count"] == 1


def test_healthcheck_window_size_caps_buffer() -> None:
    """Welle-4b-c-D-3: Ring-Buffer ist auf Window-Size begrenzt;
    aeltere Eintraege werden verworfen (deque.maxlen-Verhalten).
    """

    adapter = _build_adapter(tick_ms=10, window_size=3)
    for duration in [1.0, 2.0, 3.0, 4.0, 5.0]:
        adapter.record_tick_duration(duration)

    result = adapter.healthcheck()
    # Nur die letzten 3 Werte (3.0, 4.0, 5.0) sind im Buffer.
    assert result["window_size"] == 3
    # n=3; p50_idx=int(3*0.5)=1; sorted=[3.0, 4.0, 5.0]; sorted[1]=4.0
    assert result["tick_duration_ms_p50"] == pytest.approx(4.0)


def test_clock_source_injection_returns_default_when_unset() -> None:
    """Welle-4b-c-C0-Review-Folge F1: clock_source-Default-Argument
    ist `time.perf_counter`; explizite Injection per Test."""

    import time as _time

    adapter = _build_adapter()
    assert adapter.clock_source is _time.perf_counter


def test_clock_source_injection_uses_injected_callable() -> None:
    """Welle-4b-c-C0-Review-Folge F1: Test injiziert Fake-Clock
    fuer deterministische Duration-Sequences."""

    def fake_clock() -> float:
        return 42.0

    adapter = _build_adapter(clock_source=fake_clock)
    assert adapter.clock_source is fake_clock
    assert adapter.clock_source() == pytest.approx(42.0)


def test_tick_loop_property_exposed() -> None:
    """`tick_loop`-Property liefert die in __init__ uebergebene
    TickLoop-Instanz."""

    fake = cast(TickLoop, _FakeTickLoop(tick_ms=10))
    adapter = TickLoopHealthcheckAdapter(fake)
    assert adapter.tick_loop is fake
