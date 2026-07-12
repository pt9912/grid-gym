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
from typing import Literal, cast

from grid_gym.adapters.driven.alarm_stream_inmemory import AlarmHistoryBuffer
from grid_gym.adapters.driving._field_current_value import CurrentValueProjection
from grid_gym.adapters.driving.http_api._tick_loop_healthcheck import (
    TickLoopHealthcheckAdapter,
)
from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.errors import TickLoopInvalidTransitionError
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint as DomainTelemetryPoint
from grid_gym.hexagon.ports.driven.field_publish import FieldPublishPort
from grid_gym.hexagon.ports.driving.alarm_stream import AlarmStreamPort
from grid_gym.hexagon.ports.driving.device_server import DeviceServerPort
from grid_gym.hexagon.ports.driving.run_execution import RunExecutionPort
from grid_gym.hexagon.ports.driving.telemetry_stream import (
    TelemetryPoint as PortTelemetryPoint,
)
from grid_gym.hexagon.ports.driving.telemetry_stream import (
    TelemetryQuality,
    TelemetryStreamPort,
)


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
TelemetryStreamProvider = Callable[[], TelemetryStreamPort | None]
FieldPublishProvider = Callable[[], FieldPublishPort | None]
DeviceServerProvider = Callable[[], DeviceServerPort | None]


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
        tick_loop: RunExecutionPort,
        *,
        tick_interval_s: float = _DEFAULT_TICK_INTERVAL_S,
        alarm_stream_provider: AlarmStreamProvider | None = None,
        alarm_history_buffer_provider: AlarmHistoryBufferProvider | None = None,
        telemetry_stream_provider: TelemetryStreamProvider | None = None,
        field_publish_provider: FieldPublishProvider | None = None,
        device_server_provider: DeviceServerProvider | None = None,
        current_value_projection: CurrentValueProjection | None = None,
        healthcheck_adapter: TickLoopHealthcheckAdapter | None = None,
    ) -> None:
        self._tick_loop = tick_loop
        self._tick_interval_s = tick_interval_s
        self._task: asyncio.Task[None] | None = None
        # M6-Welle-4b-c-D-1: optionaler Healthcheck-Adapter; wenn
        # gesetzt, misst der Driver per `adapter.clock_source()` die
        # Wall-Clock-Dauer von `tick_loop.tick()` und ruft
        # `adapter.record_tick_duration(duration_ms)`. Ohne Adapter
        # (Default None) faellt der Mess-Pfad still aus — kein
        # Behavior-Bruch fuer pre-Welle-4b-c-Aufrufer.
        self._healthcheck_adapter = healthcheck_adapter
        self._alarm_stream_provider: AlarmStreamProvider = (
            alarm_stream_provider if alarm_stream_provider is not None else _none_provider
        )
        self._alarm_history_buffer_provider: AlarmHistoryBufferProvider = (
            alarm_history_buffer_provider
            if alarm_history_buffer_provider is not None
            else _none_provider
        )
        # Welle-5-Review F1: TickLoop-emitted_telemetry → TelemetryStream
        # publishing. Pre-Welle-5 hatte DemoTelemetryGenerator den
        # Stream gefuellt; Welle-5-Lifespan-Pfad wirt aber keinen
        # Generator und die TickLoop selbst hat keinen Stream-Port
        # (siehe TickLoopWiring). Driver publisht pro Tick.
        self._telemetry_stream_provider: TelemetryStreamProvider = (
            telemetry_stream_provider if telemetry_stream_provider is not None else _none_provider
        )
        # ADR 0075 §2.1/§2.3/§2.4: Field-Server-Push-Seite. Der Driver
        # (Kompositions-Schicht) resolved den `FieldPublishPort` EINMAL am
        # Run-Start, ruft `start()` (Broker-Connect), publisht je
        # emittiertem Domaenen-Punkt und `stop()` am Run-Ende. `None`-
        # Provider → kein Field-Publish (byte-identisch). Broker-Connect
        # degradiert graceful (Sim ist primaer, Field-Exposure optional).
        self._field_publish_provider: FieldPublishProvider = (
            field_publish_provider if field_publish_provider is not None else _none_provider
        )
        self._active_field_publish: FieldPublishPort | None = None
        # Review-Fix #7: Publish-Fehler pro Run zaehlen statt pro Punkt loggen
        # (Log-Flut-Schutz bei Broker-Ausfall); Summe in `_stop_field_publish`.
        self._field_publish_failures: int = 0
        # Review-Fix #8: True, sobald der Provider am Run-Start einen Port
        # lieferte (konfiguriert) — trennt `off` (nicht konfiguriert) von
        # `degraded` (konfiguriert, aber Connect-/Publish-Fehler).
        self._field_publish_configured: bool = False
        # ADR 0075 §2.2/§2.4: Pull-Seite — DeviceServerPort (bind/listen/serve,
        # driver-getrieben) + geteilte Current-Value-Projektion (pro Tick aus
        # `emitted_telemetry` gefuettert; der Server serviert die Register daraus).
        self._device_server_provider: DeviceServerProvider = (
            device_server_provider if device_server_provider is not None else _none_provider
        )
        self._active_device_server: DeviceServerPort | None = None
        self._current_value_projection: CurrentValueProjection | None = current_value_projection

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
        # ADR 0067 §2.4: `finalize()` laeuft jetzt im `_run_loop`-`finally`
        # (auf JEDEM Exit-Pfad, inkl. dem Cancel durch dieses `stop()`) — der
        # frueher hier explizite `finalize()`-Aufruf ist durch das
        # `_finalized`-Idempotenz-Flag redundant und entfaellt. Der Stop-
        # Status-Mirror (Welle-4b-Review-Fix #9) bleibt: er haelt den
        # Repository-Status davon ab, auf ``running`` zu haengen, falls der
        # Lauf nicht selbst terminal wurde.
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
            # ADR 0075 §2.4 (Review-Fix #6): Field-Publish-Start IM try — eine
            # Provider-/Connect-Exception darf `_stop_field_publish` + `finalize()`
            # (finally) nicht ueberspringen (sonst haengt der Repository-Status
            # auf `running`).
            await self._start_field_publish()
            await self._start_device_server()
            await self._tick_forever()
        except asyncio.CancelledError:
            raise
        except Exception:
            _logger.exception(
                "DemoTickLoopDriver tick loop failed for run_id=%r — stopping run.",
                self._tick_loop.run_id,
            )
            # ADR 0067 §2.4: Partial-Run markieren, damit `finalize()` den
            # abgebrochenen Lauf nicht irrefuehrend als `diverged` difft.
            self._tick_loop.mark_run_failed()
            self._force_stop_after_failure()
        finally:
            # ADR 0075 §2.4: Field-Publish-Broker am Run-Ende schliessen
            # (auf JEDEM Exit-Pfad — natuerliche Terminierung, Failure,
            # externer Cancel), bevor die Run-End-Naht laeuft.
            await self._stop_device_server()
            await self._stop_field_publish()
            # ADR 0067 §2.4: Run-End-Naht auf JEDEM Exit-Pfad (natuerliche
            # Terminierung, Failure, externer Cancel via stop()) — nicht nur
            # stop(). Idempotent (`_finalized`-Flag); gegen harten finalize()-
            # Fehler abgeschirmt (ADR 0049 §2.3 F1).
            try:
                self._tick_loop.finalize()
            except Exception:
                _logger.exception(
                    "TickLoop.finalize() failed for run_id=%r — replay diff skipped.",
                    self._tick_loop.run_id,
                )

    async def _tick_forever(self) -> None:
        while True:
            state = self._tick_loop.control_state
            if state in ("stopped", "completed"):
                return
            if state == "paused":
                await asyncio.sleep(_PAUSE_POLL_INTERVAL_S)
                continue
            result = self._tick_with_healthcheck_measure()
            self._publish_emitted_alarms(result)
            self._publish_emitted_telemetry(result)
            self._publish_field(result)
            self._update_projection(result)
            await asyncio.sleep(self._tick_interval_s)

    def _tick_with_healthcheck_measure(self) -> TickResult:
        """M6-Welle-4b-c-D-1 + D-2: misst die Wall-Clock-Dauer von
        `tick_loop.tick()` per `time.perf_counter()` (via
        `healthcheck_adapter.clock_source`) und meldet sie an den
        Healthcheck-Adapter. Ohne Adapter (Default-Pfad) fallback
        auf direkten `tick()`-Aufruf ohne Mess.

        Welle-4b-c-§7-R1: `time.perf_counter()`-Overhead ist
        Sub-Microsekunden; vernachlaessigbar gegen den 10ms-Tick-
        Budget.

        Welle-4b-c-C2-Review-Folge F4: try/finally-Wrap garantiert
        dass auch bei `tick_loop.tick()`-Exception die partielle
        Wall-Clock-Dauer (bis zum Crash) im Healthcheck-Buffer
        landet. Das hilft Diagnose: ein dauerhafter Tick-Crash
        wuerde sonst keinen Mess-Eintrag erzeugen, und der
        Healthcheck-Status koennte trotz Crash auf `ok` zeigen.
        """
        adapter = self._healthcheck_adapter
        if adapter is None:
            return self._tick_loop.tick()
        clock = adapter.clock_source
        start = clock()
        try:
            return self._tick_loop.tick()
        finally:
            end = clock()
            duration_ms = (end - start) * 1000.0
            adapter.record_tick_duration(duration_ms)

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

    def _publish_emitted_telemetry(self, result: TickResult) -> None:
        """Welle-5-Review F1: publish jeden `emitted_telemetry`-
        Point auf den TelemetryStream. Pre-Welle-5 fuellte
        `DemoTelemetryGenerator` den Stream synthetisch; der
        Welle-5-env-var-Pfad hat aber keinen Generator wired —
        ohne diesen Publish-Hook bleibt das Dashboard-WS leer
        obwohl die TickLoop produktiv Telemetry-Points emittiert.

        Provider-Pattern analog `_publish_emitted_alarms`: re-
        evaluiert pro Tick, damit ein nachtraegliches
        `configure_telemetry_stream(...)` greift. Domain-
        `TelemetryPoint` (`Decimal`-value + `source`/`tick`-
        Felder) wird auf Port-`TelemetryPoint` (`float`-value,
        Subset-Schema) abgebildet.

        Welle-5-Review-Folge: pro-Point try/except — eine einzelne
        Conversion-Exception (z. B. Decimal-NaN-`float`-Cast oder
        unbekannte Quality) darf nicht den ganzen Driver killen.
        """
        stream = self._telemetry_stream_provider()
        if stream is None:
            return
        for point in result.emitted_telemetry:
            try:
                stream.publish(_to_port_telemetry_point(point))
            except Exception:
                _logger.exception(
                    "Failed to publish telemetry point for run_id=%r device_id=%r",
                    point.run_id,
                    point.device_id,
                )

    def _publish_field(self, result: TickResult) -> None:
        """ADR 0075 §2.1/§2.3: Fan-out jedes emittierten (Domaenen-)
        `TelemetryPoint` an die Field-Publish-Push-Seite (Broker).

        Domaenen-Point **direkt** — kein `Decimal`->`float`-Cast wie beim
        Port-Stream (`_to_port_telemetry_point`), also volle Fidelity
        (ADR 0075 §2.1). Pro-Point try/except (Muster
        `_publish_emitted_telemetry`): ein einzelner Publish-Fehler toetet
        nicht den Driver. Ohne aktiven Port (`None`-Provider oder
        Start-Failure) ist es ein No-op → byte-identisch.
        """
        port = self._active_field_publish
        if port is None:
            return
        for point in result.emitted_telemetry:
            try:
                port.publish(point)
            except Exception:
                # Rate-Limit (Review-Fix #7): bei anhaltendem Broker-Ausfall
                # wuerde sonst pro Punkt/Tick ein Stacktrace geloggt (Flut).
                # Ersten Fehler voll loggen, danach nur zaehlen; Summe in
                # `_stop_field_publish`.
                if self._field_publish_failures == 0:
                    _logger.exception(
                        "Field-publish failed for run_id=%r device_id=%r — weitere "
                        "Fehler werden gezaehlt (nicht einzeln geloggt).",
                        point.run_id,
                        point.device_id,
                    )
                self._field_publish_failures += 1

    async def _start_field_publish(self) -> None:
        """ADR 0075 §2.4: Field-Publish-Port EINMAL am Run-Start resolven +
        `start()` (Broker-Connect).

        Review-Fix #1: der blockierende `start()` (paho-`connect()`) laeuft in
        einem Worker-Thread (`asyncio.to_thread`) — er darf den FastAPI-Event-
        Loop nicht stallen (sonst wuerde ein unerreichbarer Broker alle
        HTTP-Requests/Health/Cancellation fuer die TCP-Timeout-Dauer blockieren).

        Graceful Degrade: schlaegt `start()` fehl (Broker unerreichbar), wird
        geloggt und Field-Publish fuer diesen Run deaktiviert — die Simulation
        ist primaer, die Field-Exposure ein optionaler Add-on. `None`-Provider →
        No-op (kein Broker-Connect).
        """
        port = self._field_publish_provider()
        if port is None:
            return
        self._field_publish_configured = True
        try:
            await asyncio.to_thread(port.start)
        except Exception:
            _logger.exception(
                "FieldPublishPort.start() failed for run_id=%r — "
                "field-publish disabled for this run.",
                self._tick_loop.run_id,
            )
            return
        self._active_field_publish = port

    async def _stop_field_publish(self) -> None:
        """ADR 0075 §2.4: Field-Publish-Broker am Run-Ende schliessen
        (idempotent; nur wenn `start()` erfolgreich war).

        Review-Fix #1: der blockierende `stop()` (loop_stop-Join + disconnect)
        laeuft im Worker-Thread. Review-Fix #7: eine Publish-Fehler-Summe des
        Runs wird hier einmal geloggt.
        """
        failures = self._field_publish_failures
        if failures > 0:
            _logger.warning(
                "Field-publish: %d Punkt(e) fuer run_id=%r konnten nicht "
                "publiziert werden (Broker-Ausfall; QoS-0 verworfen).",
                failures,
                self._tick_loop.run_id,
            )
        port = self._active_field_publish
        if port is None:
            return
        self._active_field_publish = None
        try:
            await asyncio.to_thread(port.stop)
        except Exception:
            _logger.exception(
                "FieldPublishPort.stop() failed for run_id=%r.",
                self._tick_loop.run_id,
            )

    @property
    def field_publish_status(self) -> Literal["off", "active", "degraded"]:
        """Review-Fix #8: beobachtbarer Field-Publish-Zustand (fuer HIL/Health).

        - ``off``: nicht konfiguriert (kein Port) → kein Feed erwartet.
        - ``active``: Port konfiguriert, verbunden, keine Publish-Fehler.
        - ``degraded``: Port konfiguriert, aber Broker-Connect fehlgeschlagen
          ODER Publish-Fehler aufgetreten — der HIL/SUT-Feed kann still leer
          sein, obwohl die Sim `running` ist (macht den Falsch-Negativ
          beobachtbar statt ihn zu verstecken).
        """
        if not self._field_publish_configured:
            return "off"
        if self._active_field_publish is None or self._field_publish_failures > 0:
            return "degraded"
        return "active"

    def _update_projection(self, result: TickResult) -> None:
        """ADR 0075 §2.2: Current-Value-Projektion pro Tick aus
        `emitted_telemetry` aktualisieren (der Pull-Server serviert die Register
        daraus). No-op ohne Projektion → byte-identisch."""
        if self._current_value_projection is not None:
            self._current_value_projection.update_from_tick(result)

    async def _start_device_server(self) -> None:
        """ADR 0075 §2.4: DeviceServerPort am Run-Start binden/listen (im
        Worker-Thread, `asyncio.to_thread` — kein Event-Loop-Stall).

        **Bind-Fehler propagiert** — harter Fehler vor dem ersten Tick (der Lauf
        startet nicht; anders als der graceful-Degrade der Push-Seite, weil ein
        pollendes SUT ohne Server-Bind sinnlos ist). `None`-Provider → No-op.
        """
        port = self._device_server_provider()
        if port is None:
            return
        await asyncio.to_thread(port.start)
        self._active_device_server = port

    async def _stop_device_server(self) -> None:
        """ADR 0075 §2.4: DeviceServerPort am Run-Ende graceful schliessen (im
        Worker-Thread; idempotent). Close-Fehler werden gefangen + geloggt —
        der Run-End-/`finalize()`-Pfad soll nicht daran kippen."""
        port = self._active_device_server
        if port is None:
            return
        self._active_device_server = None
        try:
            await asyncio.to_thread(port.stop)
        except Exception:
            _logger.exception(
                "DeviceServerPort.stop() failed for run_id=%r.",
                self._tick_loop.run_id,
            )


def _to_port_telemetry_point(point: DomainTelemetryPoint) -> PortTelemetryPoint:
    """Welle-5-Review F1: Domain → Port-TelemetryPoint-Adapter.
    Domain hat `value: Decimal` + `tick` + `source`; Port hat
    `value: float` + `simulation_time_ms` (Subset)."""
    return PortTelemetryPoint(
        run_id=point.run_id,
        device_id=point.device_id,
        metric=point.metric,
        value=float(point.value),
        unit=point.unit,
        simulation_time_ms=point.simulation_time,
        quality=cast(TelemetryQuality, point.quality.value),
        sequence=point.sequence,
    )


def _none_provider() -> None:
    """Default-Provider — liefert immer ``None`` (Welle-4a-Pfad ohne
    Alarm-Wiring)."""
    return
