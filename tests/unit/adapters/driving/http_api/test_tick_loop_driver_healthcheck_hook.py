"""Unit-Tests fuer `DemoTickLoopDriver._tick_with_healthcheck_measure`
(M6 Welle 4b-c; Welle-4b-c-C2-Review-Folge F7).

Pruft die Wall-Clock-Mess-Substanz im Driver direkt — ohne den
asyncio-Run-Loop. Welle-4b-c-D-1: Adapter-Side-Mess; F4 (Review-
Folge): try/finally-Wrap gewaehrt auch bei `tick_loop.tick()`-
Exception die Mess-Eintragung.

Test-Pattern: Fake-TickLoop + Fake-Clock-Source (controlled
sequence) per Welle-4b-c-C0-Review-Folge F1.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

import pytest

from grid_gym.adapters.driving.http_api._tick_loop_driver import (
    DemoTickLoopDriver,
)
from grid_gym.adapters.driving.http_api._tick_loop_healthcheck import (
    TickLoopHealthcheckAdapter,
)
from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop


_EMPTY_TICK_RESULT: TickResult = TickResult(
    tick=0,
    simulation_time=0,
    popped_events=(),
    emitted_telemetry=(),
)


@dataclass
class _StubTickLoop:
    """Tick-Stub: liefert konstante TickResult; `tick_ms` festgelegt.

    Test-Override per `tick_impl` erlaubt Exception-Pfad-Pruefung.
    """

    tick_ms: int = 10
    tick_impl: Callable[[], TickResult] | None = None

    def tick(self) -> TickResult:
        if self.tick_impl is not None:
            return self.tick_impl()
        return _EMPTY_TICK_RESULT


def _make_clock_sequence(values_seconds: list[float]) -> Callable[[], float]:
    """Welle-4b-c-C0-Review-Folge F1: Fake-Clock liefert paarweise
    pre/post-Werte fuer pro `tick()`-Aufruf eine konkrete Duration
    in Sekunden.

    Beispiel: `_make_clock_sequence([0.005, 0.015])` simuliert
    einen 10ms-Tick (15ms-5ms = 10ms = tick_ms; nicht missed).
    """

    iterator = iter(values_seconds)
    return lambda: next(iterator)


def _build_driver_with_healthcheck(
    *,
    tick_impl: Callable[[], TickResult] | None = None,
    clock_values: list[float] | None = None,
    tick_ms: int = 10,
) -> tuple[DemoTickLoopDriver, TickLoopHealthcheckAdapter]:
    """Test-Builder: Stub-TickLoop + Healthcheck-Adapter mit Fake-
    Clock + DemoTickLoopDriver mit dem Adapter."""

    stub = cast(TickLoop, _StubTickLoop(tick_ms=tick_ms, tick_impl=tick_impl))
    clock = _make_clock_sequence(clock_values) if clock_values is not None else None
    adapter = TickLoopHealthcheckAdapter(
        stub,
        window_size=10,
        clock_source=clock if clock is not None else (lambda: 0.0),
    )
    driver = DemoTickLoopDriver(stub, healthcheck_adapter=adapter)
    return driver, adapter


def test_tick_with_healthcheck_measure_records_duration() -> None:
    """F7: misst Wall-Clock-Dauer und gibt sie an den Adapter weiter."""

    # Clock-Sequence: 1. Pair = pre=0.001s, post=0.004s → 3ms duration
    driver, adapter = _build_driver_with_healthcheck(clock_values=[0.001, 0.004], tick_ms=10)

    result = driver._tick_with_healthcheck_measure()  # type: ignore[reportPrivateUsage]

    assert result.tick == 0  # TickResult.empty(0)
    healthcheck = adapter.healthcheck()
    assert healthcheck["window_size"] == 1
    assert healthcheck["tick_duration_ms_p50"] == pytest.approx(3.0)
    assert healthcheck["missed_ticks_count"] == 0
    assert healthcheck["backpressure_status"] == "ok"


def test_tick_with_healthcheck_measure_no_adapter_skips_measurement() -> None:
    """F7: ohne Healthcheck-Adapter (Default-Pfad) wird direkt
    `tick_loop.tick()` aufgerufen ohne Mess; kein Behavior-Bruch
    fuer pre-Welle-4b-c-Aufrufer."""

    stub = cast(TickLoop, _StubTickLoop(tick_ms=10))
    driver = DemoTickLoopDriver(stub)  # No healthcheck_adapter

    result = driver._tick_with_healthcheck_measure()  # type: ignore[reportPrivateUsage]

    assert result.tick == 0


def test_tick_with_healthcheck_measure_records_duration_on_exception() -> None:
    """F4 (Review-Folge): try/finally garantiert dass auch bei
    `tick_loop.tick()`-Exception die partielle Wall-Clock-Dauer
    im Healthcheck-Buffer landet (Diagnose-Wert).
    """

    class _TickFailureError(RuntimeError):
        pass

    def _crashing_tick() -> TickResult:
        raise _TickFailureError("simulated tick crash")

    # Clock: pre=0.001s, post=0.011s → 10ms (passt zum tick_ms; nicht
    # missed). Falls die Exception die finally umgehen wuerde, waere
    # window_size == 0; der Test schlaegt fehl.
    driver, adapter = _build_driver_with_healthcheck(
        tick_impl=_crashing_tick,
        clock_values=[0.001, 0.011],
        tick_ms=10,
    )

    with pytest.raises(_TickFailureError):
        driver._tick_with_healthcheck_measure()  # type: ignore[reportPrivateUsage]

    healthcheck = adapter.healthcheck()
    assert healthcheck["window_size"] == 1, (
        "F4 try/finally muss Mess-Eintrag auch bei Exception erzeugen"
    )
    assert healthcheck["tick_duration_ms_p50"] == pytest.approx(10.0)


def test_tick_with_healthcheck_measure_missed_tick_flagged() -> None:
    """Mess > tick_ms loest `delayed`-Status aus (Welle-4b-c-D-4)."""

    # Clock: pre=0, post=0.020s → 20ms > tick_ms=10ms → missed
    driver, adapter = _build_driver_with_healthcheck(clock_values=[0.0, 0.020], tick_ms=10)

    driver._tick_with_healthcheck_measure()  # type: ignore[reportPrivateUsage]

    healthcheck = adapter.healthcheck()
    assert healthcheck["missed_ticks_count"] == 1
    assert healthcheck["backpressure_status"] == "delayed"
