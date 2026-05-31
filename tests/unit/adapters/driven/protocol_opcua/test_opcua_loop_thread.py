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

import pytest

from grid_gym.adapters.driven.protocol_opcua import (
    OpcuaLoopThread,
    OpcuaLoopThreadNotStartedError,
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
