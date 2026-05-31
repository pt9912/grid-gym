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
schliesst den Loop **konditional**: wenn `thread.join` den Timeout
reisst, bleibt der Daemon-Thread weiter aktiv (und damit der Loop
offen, bis der Prozess endet); der Test-Prozess kann trotzdem
beendet werden (Daemon-Semantik). Slice-032-Schaerfung (Review-
Folge): Lifecycle-Operationen sind durch ein `threading.Lock`
serialisiert; State-Nulling erfolgt **nach** Cancel/Join, damit
ein paralleler `start()` keinen Zombie-Loop spawnt.
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
_DEFAULT_START_TIMEOUT_S: Final[float] = 5.0


T = TypeVar("T")


class OpcuaLoopThreadError(RuntimeError):
    """Base-Klasse fuer Loop-Thread-Lifecycle-Fehler."""


class OpcuaLoopThreadNotStartedError(OpcuaLoopThreadError):
    """`run_coroutine()` wurde aufgerufen, bevor `start()` erfolgreich
    war."""

    def __init__(self) -> None:
        super().__init__("OpcuaLoopThread: run_coroutine() aufgerufen vor start().")


class OpcuaLoopThreadStartTimeoutError(OpcuaLoopThreadError):
    """Loop-Thread hat innerhalb des Start-Timeouts kein Ready-Signal
    geliefert (Slice-032-Schaerfung, Welle-4-Review-Folge Finding 1.3)."""

    def __init__(self, timeout_s: float) -> None:
        super().__init__(
            f"OpcuaLoopThread: Loop-Thread hat innerhalb {timeout_s}s kein Ready-Signal geliefert."
        )
        self.timeout_s: float = timeout_s


class OpcuaLoopThread:
    """asyncio-Event-Loop in einem dedizierten Daemon-Thread.

    Idempotenz: `start()` ist No-op nach erstem erfolgreichem Lauf,
    `stop()` ist No-op nach erfolglosem oder doppelt aufgerufenem
    Stop. Slice-032-Schaerfung: Lifecycle-Operationen sind durch
    ein `threading.Lock` serialisiert (Welle-4-Review-Folge
    Finding 1.4).
    """

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._started: bool = False
        self._lifecycle_lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """True, wenn `start()` erfolgreich war, `stop()` noch nicht
        gelaufen ist **und** der Loop noch lebt.

        Slice-032-Schaerfung (Welle-4-Review-Folge Finding 1.5):
        prueft zusaetzlich `loop.is_running()`, damit ein intern
        gestorbener Loop nicht weiterhin als „running" gilt.
        """
        return self._started and self._loop is not None and self._loop.is_running()

    def start(self, *, timeout_s: float = _DEFAULT_START_TIMEOUT_S) -> None:
        """Spawnt einen Daemon-Thread mit eigenem
        `asyncio.AbstractEventLoop`. Idempotent.

        Wirft `OpcuaLoopThreadStartTimeoutError`, wenn der Loop-Thread
        nicht innerhalb `timeout_s` ein Ready-Signal liefert (Slice-
        032-Schaerfung Finding 1.3 — verhindert ewiges Blockieren
        bei seltenen Thread-Init-Fehlern).
        """
        with self._lifecycle_lock:
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
            if not ready.wait(timeout=timeout_s):
                # Best-effort cleanup; Loop wurde noch nicht gestartet,
                # also kein Loop-Stop noetig. Daemon-Thread stirbt mit
                # dem Prozess, falls er gar nicht erst hochkommt.
                with contextlib.suppress(Exception):
                    loop.close()
                raise OpcuaLoopThreadStartTimeoutError(timeout_s)
            self._loop = loop
            self._thread = thread
            self._started = True

    def stop(self, *, timeout_s: float = _DEFAULT_STOP_TIMEOUT_S) -> None:
        """Cancelt pending Tasks, stoppt den Loop und joint den
        Thread. Idempotent — Doppel-Stop ist No-op.

        Falls `thread.join(timeout_s)` reisst, bleibt der Daemon-
        Thread weiter aktiv (Loop nicht geschlossen); der Test-
        Prozess kann trotzdem beendet werden (Daemon-Semantik aus
        ADR 0033 §2.2). Slice-032-Schaerfung (Welle-4-Review-Folge
        Finding 1.1): State-Nulling erfolgt **nach** Cancel/Join,
        damit paralleler `start()` keinen Zombie-Loop spawnt.
        """
        with self._lifecycle_lock:
            if not self._started or self._loop is None or self._thread is None:
                return
            loop = self._loop
            thread = self._thread

            # Cancel pending tasks via thread-safe call. Slice-032-Schaerfung
            # Finding 1.2: `RuntimeError` ("Event loop is closed" / "loop is
            # not running") supprimieren — idempotenter Stop darf nicht
            # werfen, wenn der Loop intern bereits gestoppt hat.
            with contextlib.suppress(RuntimeError):
                cancel_future = asyncio.run_coroutine_threadsafe(_cancel_pending(loop), loop)
                with contextlib.suppress(TimeoutError, asyncio.CancelledError, RuntimeError):
                    cancel_future.result(timeout=_CANCEL_GATHER_TIMEOUT_S)

            with contextlib.suppress(RuntimeError):
                loop.call_soon_threadsafe(loop.stop)
            thread.join(timeout=timeout_s)
            if not thread.is_alive():
                with contextlib.suppress(RuntimeError):
                    loop.close()

            # Slice-032 Finding 1.1: State erst NACH erfolgreichem
            # Cancel/Join nullen — sonst koennte paralleler start()
            # zwischen Cancel und Join einen frischen Loop spawnen,
            # waehrend der alte noch lebt.
            self._loop = None
            self._thread = None
            self._started = False

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
    Task; wartet kurz auf Cancel-Bestaetigung.

    Laeuft IM Loop-Thread (via `run_coroutine_threadsafe`);
    `asyncio.current_task()` liefert hier die `_cancel_pending`-Task
    selbst und wird aus der Cancel-Liste herausgefiltert.
    """
    pending = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)
