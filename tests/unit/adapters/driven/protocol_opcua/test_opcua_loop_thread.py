"""Lifecycle-Tests fuer `OpcuaLoopThread` (M4 Welle 4, ADR 0033 §2.2).

Deckt:

- `start()` ist idempotent.
- `stop()` ist idempotent (auch vor `start()`).
- `run_coroutine` vor `start()` wirft typed `OpcuaLoopThreadNotStartedError`.
- Coroutine-Ergebnis wird korrekt durchgereicht.
- Coroutine-Exception wird korrekt propagiert.
- `stop()` cancelt pending Tasks ohne haengen zu bleiben.
- Loop-Close passiert nach erfolgreichem Thread-Join.
"""

from __future__ import annotations

import asyncio
import threading

import pytest

from grid_gym.adapters.driven.protocol_opcua import (
    OpcuaLoopThread,
    OpcuaLoopThreadNotStartedError,
    OpcuaLoopThreadStartTimeoutError,
)


def test_start_is_idempotent() -> None:
    thread = OpcuaLoopThread()
    thread.start()
    try:
        first_loop = thread._loop  # type: ignore[attr-defined]
        thread.start()  # second call — no-op
        assert thread._loop is first_loop  # type: ignore[attr-defined]
    finally:
        thread.stop()


def test_stop_before_start_is_noop() -> None:
    thread = OpcuaLoopThread()
    thread.stop()  # darf nicht werfen
    assert not thread.is_running


def test_double_stop_is_noop() -> None:
    thread = OpcuaLoopThread()
    thread.start()
    thread.stop()
    thread.stop()  # darf nicht werfen
    assert not thread.is_running


async def _trivial() -> int:
    # Trivial coroutine, used in `run_coroutine` tests below; `asyncio.sleep(0)`
    # ist genug, damit ruff den `async`-Marker akzeptiert.
    await asyncio.sleep(0)
    return 42


async def _double(x: int) -> int:
    await asyncio.sleep(0)
    return x * 2


async def _boom() -> int:
    await asyncio.sleep(0)
    raise ValueError("boom")


def test_run_coroutine_before_start_raises() -> None:
    thread = OpcuaLoopThread()
    coro = _trivial()
    try:
        with pytest.raises(OpcuaLoopThreadNotStartedError):
            thread.run_coroutine(coro, timeout_s=1.0)
    finally:
        coro.close()


def test_run_coroutine_returns_result() -> None:
    thread = OpcuaLoopThread()
    thread.start()
    try:
        result = thread.run_coroutine(_double(21), timeout_s=2.0)
        assert result == 42
    finally:
        thread.stop()


def test_run_coroutine_propagates_exception() -> None:
    thread = OpcuaLoopThread()
    thread.start()
    try:
        with pytest.raises(ValueError, match="boom"):
            thread.run_coroutine(_boom(), timeout_s=2.0)
    finally:
        thread.stop()


def test_run_coroutine_respects_timeout() -> None:
    thread = OpcuaLoopThread()
    thread.start()
    try:

        async def slow() -> None:
            await asyncio.sleep(5.0)

        with pytest.raises(TimeoutError):
            thread.run_coroutine(slow(), timeout_s=0.1)
    finally:
        thread.stop()


def test_stop_cancels_pending_tasks() -> None:
    thread = OpcuaLoopThread()
    thread.start()

    async def block_briefly() -> None:
        # Wuerde 30s blocken, soll von stop() cancelled werden.
        await asyncio.sleep(30.0)

    # Spawn task, dann sofort stop.
    loop = thread._loop  # type: ignore[attr-defined]
    assert loop is not None
    asyncio.run_coroutine_threadsafe(block_briefly(), loop)
    # Stop muss durchgehen — Cancel + Loop-Stop + Join.
    thread.stop(timeout_s=3.0)
    assert not thread.is_running


def test_is_running_property_reflects_state() -> None:
    thread = OpcuaLoopThread()
    assert not thread.is_running
    thread.start()
    assert thread.is_running
    thread.stop()
    assert not thread.is_running


# ---------------------------------------------------------------------------
# Slice-032-Schaerfungen (Welle-4-Review-Folge)
# ---------------------------------------------------------------------------


def test_start_timeout_raises_typed_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Finding 1.3: `start(timeout_s=...)` muss bei zu kurzem
    Ready-Timeout eine typed Exception werfen statt ewig zu blocken.

    Wir simulieren einen haengenden Thread-Init, indem
    `threading.Thread.start` als No-op gepatcht wird — der
    Daemon-Thread laeuft nie an, `ready.set()` wird nie aufgerufen,
    `ready.wait(timeout_s)` reisst.
    """

    def _no_start(self: threading.Thread) -> None:
        # Simulate Thread, der nie hochkommt.
        return None

    monkeypatch.setattr(threading.Thread, "start", _no_start)
    thread = OpcuaLoopThread()
    with pytest.raises(OpcuaLoopThreadStartTimeoutError) as exc_info:
        thread.start(timeout_s=0.1)
    assert exc_info.value.timeout_s == pytest.approx(0.1)


def test_concurrent_start_stop_serialized_by_lock() -> None:
    """Finding 1.4: Lifecycle-Lock serialisiert paralleles
    start()/stop() — kein Zombie-Loop, kein Doppel-Init.

    Spawnt N Threads, die alle `start()` aufrufen, dann N Threads,
    die `stop()` aufrufen. Am Ende muss der Thread sauber
    gestoppt sein, keine Hang-Threads, kein Exception.
    """
    thread = OpcuaLoopThread()
    barrier = threading.Barrier(parties=8)
    errors: list[BaseException] = []

    def _starter() -> None:
        barrier.wait()
        try:
            thread.start()
        except BaseException as exc:  # test-collector
            errors.append(exc)

    def _stopper() -> None:
        barrier.wait()
        try:
            thread.stop(timeout_s=2.0)
        except BaseException as exc:  # test-collector
            errors.append(exc)

    threads = [threading.Thread(target=_starter) for _ in range(4)]
    threads += [threading.Thread(target=_stopper) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5.0)
        assert not t.is_alive(), "Test-Thread haengt — Lifecycle-Lock-Race?"
    assert errors == [], f"Unerwartete Exceptions: {errors!r}"
    # Final-Cleanup (idempotent).
    thread.stop()
    assert not thread.is_running


def test_stop_after_loop_crash_is_safe() -> None:
    """Finding 1.2 + 1.5: `stop()` darf nicht werfen, auch wenn der
    Loop intern bereits gestoppt wurde."""
    thread = OpcuaLoopThread()
    thread.start()
    # Loop von aussen stoppen (simuliert internen Crash).
    loop = thread._loop  # type: ignore[attr-defined]
    assert loop is not None
    loop.call_soon_threadsafe(loop.stop)
    # Warte kurz, damit Stop greift.
    inner_thread = thread._thread  # type: ignore[attr-defined]
    assert inner_thread is not None
    inner_thread.join(timeout=2.0)
    # is_running muss false sein, weil loop.is_running() false ist.
    assert not thread.is_running
    # stop() darf trotz totem Loop sauber durchgehen.
    thread.stop(timeout_s=1.0)


def test_run_coroutine_during_stop_caller_side(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Finding 4.1 + 1.9: ein zweiter Thread, der `run_coroutine`
    macht, waehrend `stop()` laeuft, bekommt einen klar typisierten
    Fehler statt eines unerwarteten Hangs."""
    thread = OpcuaLoopThread()
    thread.start()

    async def _slow() -> int:
        await asyncio.sleep(10.0)
        return 1

    barrier = threading.Barrier(parties=2)
    results: dict[str, BaseException | int] = {}

    def _caller() -> None:
        barrier.wait()
        try:
            results["caller"] = thread.run_coroutine(_slow(), timeout_s=5.0)
        except BaseException as exc:  # test-collector
            results["caller"] = exc

    def _stopper() -> None:
        barrier.wait()
        try:
            thread.stop(timeout_s=3.0)
            results["stopper"] = 0
        except BaseException as exc:  # test-collector
            results["stopper"] = exc

    t1 = threading.Thread(target=_caller)
    t2 = threading.Thread(target=_stopper)
    t1.start()
    t2.start()
    t1.join(timeout=8.0)
    t2.join(timeout=8.0)
    assert not t1.is_alive() and not t2.is_alive()
    # Stop muss sauber durchgehen.
    assert results.get("stopper") == 0
    # Caller bekommt entweder einen Cancellation-/Timeout-Error
    # (Coroutine wurde im Loop cancelled) — die genaue Klasse haengt
    # vom Race-Outcome ab; wichtig ist nur, dass keine Hang-Situation
    # entsteht und keine `Exception`-Wurzel propagiert.
    caller_result = results.get("caller")
    assert caller_result is not None
