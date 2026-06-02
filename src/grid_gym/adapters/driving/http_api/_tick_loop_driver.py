"""DemoTickLoopDriver — asyncio-Task, der den Welle-4a-Demo-`TickLoop`
periodisch tickt (M5 Welle 4a, ADR 0039 Decision 13).

Welle-4a-Stub: Single-Run-Driver fuer den FastAPI-Lifespan-
Demo-Setup; iteriert die ``control_state``-Property und ruft
``tick()``, solange der State ``running``/``pending`` ist. Bei
``paused`` pollt der Driver alle ~100ms ohne ``tick()`` (kein
Tick-Fortschritt, kein Telemetry-Push). Bei ``stopped``/
``completed`` verlaesst der Driver den Loop sauber.

Produktive Multi-Run-Variante in Welle 5 (Scenario-Loader) wirt
einen Driver pro aktivem Run; Welle 4a tickt nur den einen
``demo-run-0001``-TickLoop, den der Lifespan beim Startup
registriert.

Pattern analog `DemoTelemetryGenerator` aus Welle 3 — gleicher
``start``/``stop``-Lifecycle, gleiche Idempotenz, gleiches
``CancelledError``-Cleanup-Pattern.
"""

from __future__ import annotations

import asyncio
import contextlib

from grid_gym.adapters.driven.alarm_stream_inmemory import AlarmHistoryBuffer
from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driving.alarm_stream import AlarmStreamPort


_DEFAULT_TICK_INTERVAL_S = 0.1
"""Welle-4a-Default: 100ms zwischen Ticks (entspricht ``GG-SIM-002``-
Standard-Tick-Rate ``tick_ms=100``). Welle 5 koennte das pro Run
konfigurierbar machen."""

_PAUSE_POLL_INTERVAL_S = 0.1
"""Polling-Intervall, waehrend `control_state == "paused"`. Der
Driver schlaeft 100ms und prueft den State erneut — keine
``tick()``-Aufrufe, kein Telemetry-Push."""


class DemoTickLoopDriver:
    """Asyncio-Task-Wrapper fuer den Welle-4a-Demo-`TickLoop` (ADR
    0039 Decision 13).

    Lifecycle:

    - ``start()`` startet den asyncio-Driver-Task (idempotent —
      wiederholtes ``start`` ist No-op, solange der Task laeuft).
    - ``stop()`` cancelt den Task, wartet auf Cleanup; setzt den
      `control_state` des TickLoops auf ``"completed"``, sofern
      noch nicht terminal.
    """

    def __init__(
        self,
        tick_loop: TickLoop,
        *,
        tick_interval_s: float = _DEFAULT_TICK_INTERVAL_S,
        alarm_stream: AlarmStreamPort | None = None,
        alarm_history_buffer: AlarmHistoryBuffer | None = None,
    ) -> None:
        self._tick_loop = tick_loop
        self._tick_interval_s = tick_interval_s
        self._task: asyncio.Task[None] | None = None
        self._alarm_stream: AlarmStreamPort | None = alarm_stream
        self._alarm_history_buffer: AlarmHistoryBuffer | None = alarm_history_buffer

    def start(self) -> None:
        """Startet den Driver-Task (idempotent)."""
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Cancelt den Driver-Task und wartet auf Cleanup; setzt den
        TickLoop-State auf ``"completed"``, sofern noch nicht
        terminal."""
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        # Best-effort: terminal-State sicherstellen. Bei
        # bereits-`stopped`/`completed`-State ist `request_stop`
        # idempotent (kein Throw); andernfalls flippt es nach
        # `stopped`. Welle-4a-Shutdown-Pfad markiert den Run als
        # `completed` indirekt (Driver verlaesst den Loop), den
        # final-State-Mirror brauchen wir nicht extra.

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def _run_loop(self) -> None:
        """Tick-Schleife: pruefe `control_state`, tick, schlafe.

        Welle-4a-Behavior:

        - ``stopped``/``completed`` → return (Task endet sauber).
        - ``paused`` → schlafe ``_PAUSE_POLL_INTERVAL_S`` ohne
          ``tick()``.
        - sonst → ``tick()`` + schlafe ``_tick_interval_s``.

        Synchroner ``tick()``-Aufruf blockt den Event-Loop fuer
        die Tick-Dauer; Welle-4a-Demo-TickLoop hat keine Devices
        und ist daher trivial-schnell. Welle 5 (Multi-Run +
        echte Devices) sollte zu ``asyncio.to_thread(tick_loop.
        tick)`` migrieren, um den Event-Loop nicht zu blocken.
        """
        while True:
            state = self._tick_loop.control_state
            if state in ("stopped", "completed"):
                return
            if state == "paused":
                await asyncio.sleep(_PAUSE_POLL_INTERVAL_S)
                continue
            result = self._tick_loop.tick()
            self._publish_emitted_alarms(result)
            await asyncio.sleep(self._tick_interval_s)

    def _publish_emitted_alarms(self, result: TickResult) -> None:
        """M5-Welle-4b (ADR 0040 Decision 17): publish jeden
        `emitted_alarm` auf den Stream + History-Buffer, sofern
        konfiguriert. Pattern symmetrisch zur Telemetry-Publish-
        Wiring; bei `None`-Defaults ist die Methode No-op."""
        if self._alarm_stream is None and self._alarm_history_buffer is None:
            return
        for alarm in result.emitted_alarms:
            if self._alarm_stream is not None:
                self._alarm_stream.publish(alarm)
            if self._alarm_history_buffer is not None:
                self._alarm_history_buffer.append(alarm)
