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
import logging
from collections.abc import Callable

from grid_gym.adapters.driven.alarm_stream_inmemory import AlarmHistoryBuffer
from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.errors import TickLoopInvalidTransitionError
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

_logger = logging.getLogger(__name__)


AlarmStreamProvider = Callable[[], AlarmStreamPort | None]
AlarmHistoryBufferProvider = Callable[[], AlarmHistoryBuffer | None]


class DemoTickLoopDriver:
    """Asyncio-Task-Wrapper fuer den Welle-4a-Demo-`TickLoop` (ADR
    0039 Decision 13).

    Lifecycle:

    - ``start()`` startet den asyncio-Driver-Task (idempotent —
      wiederholtes ``start`` ist No-op, solange der Task laeuft).
    - ``stop()`` cancelt den Task, wartet auf Cleanup; mirror der
      ``TickLoop.request("stop")``-Transition auf den Repository-
      Status, sofern noch nicht terminal (Welle-4b-Review-Fix #9).

    Provider-Callables (Welle-4b-Review-Fix #1): `alarm_stream`-
    und `alarm_history_buffer`-Refs werden bei jedem Tick
    re-evaluiert, damit ein nachtraegliches
    `configure_alarm_stream(...)` (nach `configure_demo_run`)
    den Publish-Pfad nicht stillschweigend skippt.
    """

    def __init__(
        self,
        tick_loop: TickLoop,
        *,
        tick_interval_s: float = _DEFAULT_TICK_INTERVAL_S,
        alarm_stream_provider: AlarmStreamProvider | None = None,
        alarm_history_buffer_provider: AlarmHistoryBufferProvider | None = None,
    ) -> None:
        self._tick_loop = tick_loop
        self._tick_interval_s = tick_interval_s
        self._task: asyncio.Task[None] | None = None
        self._alarm_stream_provider: AlarmStreamProvider = (
            alarm_stream_provider if alarm_stream_provider is not None else _none_provider
        )
        self._alarm_history_buffer_provider: AlarmHistoryBufferProvider = (
            alarm_history_buffer_provider
            if alarm_history_buffer_provider is not None
            else _none_provider
        )

    def start(self) -> None:
        """Startet den Driver-Task (idempotent)."""
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Cancelt den Driver-Task, wartet auf Cleanup und mirror den
        TickLoop-State terminal (Welle-4b-Review-Fix #9).

        Wenn `control_state` noch ``pending``/``running``/``paused``
        ist, ruft `request("stop")` — damit der Repository-Status
        nicht ewig auf ``running`` haengen bleibt, nachdem der
        Driver-Task beendet ist. `TickLoopInvalidTransitionError`
        wird geschluckt, weil der State zwischen Check und Request
        terminal werden kann (Race mit der Tick-Schleife).
        """
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        current = self._tick_loop.control_state
        if current not in ("stopped", "completed"):
            try:
                self._tick_loop.request("stop")
            except TickLoopInvalidTransitionError:
                return

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def tick_loop_run_id(self) -> str:
        """Welle-4b-Review-Fix #13: erlaubt `configure_demo_run`,
        einen orphan-Driver-Konflikt zu erkennen, ohne auf das
        private `_tick_loop`-Feld zuzugreifen."""
        return self._tick_loop.run_id

    async def _run_loop(self) -> None:
        """Tick-Schleife: pruefe `control_state`, tick, schlafe.

        Welle-4a-Behavior:

        - ``stopped``/``completed`` → return (Task endet sauber).
        - ``paused`` → schlafe ``_PAUSE_POLL_INTERVAL_S`` ohne
          ``tick()``.
        - sonst → ``tick()`` + schlafe ``_tick_interval_s``.

        Welle-4b-Review-Fix #2: Body ist in try/except gewrappt —
        eine Tick-Exception (TickLoopStoppedError, mapper-Defekt,
        Devices-Bug) wuerde sonst den Task still toeten und der
        Repository-Status auf ``running`` einfrieren. Stattdessen:
        loggen + `request("stop")` (Repository-Mirror), dann
        Task sauber beenden.
        """
        try:
            await self._tick_forever()
        except asyncio.CancelledError:
            raise
        except Exception:
            _logger.exception(
                "DemoTickLoopDriver tick loop failed for run_id=%r — stopping run.",
                self._tick_loop.run_id,
            )
            self._force_stop_after_failure()

    async def _tick_forever(self) -> None:
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

    def _force_stop_after_failure(self) -> None:
        """Welle-4b-Review-Fix #2: nach Tick-Exception den Repository-
        Status auf ``stopped`` mirrorn, damit `/status` und UI nicht
        weiter ``running`` anzeigen. `request("stop")` mirror an
        die optionale Repository — wenn der State bereits terminal
        ist (TickLoopStoppedError-Pfad), schluckt der Guard die
        Transition."""
        current = self._tick_loop.control_state
        if current in ("stopped", "completed"):
            return
        try:
            self._tick_loop.request("stop")
        except TickLoopInvalidTransitionError:
            return

    def _publish_emitted_alarms(self, result: TickResult) -> None:
        """M5-Welle-4b (ADR 0040 Decision 17): publish jeden
        `emitted_alarm` auf den Stream + History-Buffer, sofern
        konfiguriert.

        Welle-4b-Review-Fix #1: Provider-Callables re-lesen bei
        jedem Tick `app.state` — handle ``configure_alarm_stream``
        nach ``configure_demo_run``.

        Welle-4b-Review-Fix #12: History-Buffer wird VOR dem Stream
        beschrieben. Falls `stream.publish(...)` raist (Queue-Full-
        Race), bleibt der Alarm wenigstens in der History.
        """
        stream = self._alarm_stream_provider()
        history_buffer = self._alarm_history_buffer_provider()
        if stream is None and history_buffer is None:
            return
        for alarm in result.emitted_alarms:
            if history_buffer is not None:
                history_buffer.append(alarm)
            if stream is not None:
                stream.publish(alarm)


def _none_provider() -> None:
    """Default-Provider — liefert immer ``None`` (Welle-4a-Pfad ohne
    Alarm-Wiring)."""
    return
