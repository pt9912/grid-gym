"""asyncio-Loop-Thread fuer den OPC-UA-Adapter (M4 Welle 4, ADR 0033 §2.2).

Decision O-b: dedizierter `asyncio.AbstractEventLoop` in einem
`threading.Thread(daemon=True)`. Sync-Aufrufer marshalen Coroutinen
via `run_coroutine_threadsafe(coro, loop).result(timeout)` in den
Loop-Thread.

Diese Klasse ist Welle-4-spezifisch produktiv, aber bewusst von
`_port.py` getrennt, weil Welle-5 (DNP3/IEC, falls Spike) das
Pattern reusen koennte. Welle-6-Schaerfung kann die Klasse nach
`src/grid_gym/adapters/driven/_async_bridge/` extrahieren — siehe
ADR 0033 §2.2 Konsequenzen.

**Teardown-Vertrag** (ADR 0033 §2.2): `stop()` cancelt pending
Tasks, ruft `loop.stop()`, wartet auf `thread.join(timeout_s)` und
schliesst den Loop. Daemon-Thread schuetzt den Test-Prozess vor
Aufhaengen, falls `thread.join` einen Timeout reisst.
"""

from __future__ import annotations

import asyncio
import contextlib
import threading
from collections.abc import Coroutine
from concurrent.futures import Future
from typing import Any, Final, TypeVar


_DEFAULT_STOP_TIMEOUT_S: Final[float] = 5.0
_CANCEL_GATHER_TIMEOUT_S: Final[float] = 1.0


T = TypeVar("T")


class OpcuaLoopThreadError(RuntimeError):
    """Base-Klasse fuer Loop-Thread-Lifecycle-Fehler."""


class OpcuaLoopThreadNotStartedError(OpcuaLoopThreadError):
    """`run_coroutine()` wurde aufgerufen, bevor `start()` erfolgreich
    war."""

    def __init__(self) -> None:
        super().__init__("OpcuaLoopThread: run_coroutine() aufgerufen vor start().")


class OpcuaLoopThread:
    """asyncio-Event-Loop in einem dedizierten Daemon-Thread.

    Idempotenz: `start()` ist No-op nach erstem erfolgreichem Lauf,
    `stop()` ist No-op nach erfolglosem oder doppelt aufgerufenem
    Stop.
    """

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._started: bool = False

    @property
    def is_running(self) -> bool:
        """True, wenn `start()` erfolgreich war und `stop()` noch nicht
        gelaufen ist."""
        return self._started

    def start(self) -> None:
        """Spawnt einen Daemon-Thread mit eigenem
        `asyncio.AbstractEventLoop`. Idempotent."""
        if self._started:
            return
        loop = asyncio.new_event_loop()
        ready = threading.Event()

        def _run_loop() -> None:
            asyncio.set_event_loop(loop)
            ready.set()
            loop.run_forever()

        thread = threading.Thread(target=_run_loop, daemon=True, name="opcua-loop")
        thread.start()
        ready.wait()
        self._loop = loop
        self._thread = thread
        self._started = True

    def stop(self, *, timeout_s: float = _DEFAULT_STOP_TIMEOUT_S) -> None:
        """Cancelt pending Tasks, stoppt den Loop und joint den
        Thread. Idempotent — Doppel-Stop ist No-op.

        Falls `thread.join(timeout_s)` reisst, bleibt der Daemon-
        Thread weiter aktiv; der Test-Prozess kann trotzdem beendet
        werden (Daemon-Semantik aus ADR 0033 §2.2).
        """
        if not self._started or self._loop is None or self._thread is None:
            return
        loop = self._loop
        thread = self._thread
        self._loop = None
        self._thread = None
        self._started = False

        # Cancel pending tasks via thread-safe call.
        cancel_future = asyncio.run_coroutine_threadsafe(_cancel_pending(loop), loop)
        with contextlib.suppress(TimeoutError, asyncio.CancelledError):
            cancel_future.result(timeout=_CANCEL_GATHER_TIMEOUT_S)

        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=timeout_s)
        if not thread.is_alive():
            loop.close()

    def run_coroutine(self, coro: Coroutine[Any, Any, T], *, timeout_s: float) -> T:
        """Marshalt `coro` in den Loop-Thread und blockiert auf das
        Ergebnis.

        Wirft `OpcuaLoopThreadNotStartedError`, wenn der Loop noch
        nicht gestartet ist. Original-Exception der Coroutine wird
        propagiert (asyncio-Semantik). `TimeoutError` bei
        `timeout_s`-Ueberschreitung.
        """
        if not self._started or self._loop is None:
            raise OpcuaLoopThreadNotStartedError
        future: Future[T] = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout_s)


async def _cancel_pending(loop: asyncio.AbstractEventLoop) -> None:
    """Sammelt + cancelt alle pending Tasks ausserhalb der aktuellen
    Task; wartet kurz auf Cancel-Bestaetigung."""
    pending = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)
