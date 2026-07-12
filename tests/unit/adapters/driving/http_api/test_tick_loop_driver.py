"""M5-Welle-4b-Review-Fixes #1, #2, #9, #12, #13 fuer
`DemoTickLoopDriver`.

Pinnt:

- `#1` Late-Wiring via Provider-Callable: ein nachtraegliches
  `configure_alarm_stream(...)` wird beim naechsten Publish
  beachtet.
- `#2` Task-Exception-Handling: eine Tick-Exception killt den
  Task nicht silently — der Repository-Status wird auf
  `stopped` mirror'd.
- `#9` stop() mirror'd den TickLoop-State auf `stopped`, sodass
  der persistierte Run-Status mit der Driver-Lebenszeit
  konsistent bleibt.
- `#12` `_publish_emitted_alarms` schreibt zuerst in den Buffer,
  dann auf den Stream — bei Stream-Exception bleibt die History
  konsistent.
- `#13` Orphan-Driver-Guard in `configure_demo_run`.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import cast

import pytest

from grid_gym.adapters.driven.alarm_stream_inmemory import (
    AlarmHistoryBuffer,
    InMemoryAlarmStream,
)
from grid_gym.adapters.driving._field_current_value import CurrentValueProjection
from grid_gym.adapters.driving.http_api._tick_loop_driver import DemoTickLoopDriver
from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.domain.alarm import Alarm
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint as DomainTelemetryPoint
from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driven.field_publish import (
    FieldPublishPortStartError,
    FieldPublishPortStopError,
)
from grid_gym.hexagon.ports.driving.alarm_stream import AlarmStreamPort
from grid_gym.hexagon.ports.driving.device_server import (
    DeviceServerPortStartError,
    DeviceServerPortStopError,
)
from tests.unit.hexagon.ports.driven._fakes import (
    FakeClock,
    FixedSeedRandom,
    InMemoryRunRepository,
)


def _make_battery_with_low_charge_limit() -> BatteryDevice:
    battery = BatteryDevice()
    battery.initialize(
        ScenarioDevice(
            id="battery-1",
            type="battery",
            params={
                "capacity_kwh": Decimal("100"),
                "initial_soc_pct": Decimal("50"),
                "min_soc_pct": Decimal("0"),
                "max_soc_pct": Decimal("100"),
                "max_charge_kw": Decimal("50"),
                "max_discharge_kw": Decimal("50"),
                "charge_efficiency": Decimal("1"),
                "discharge_efficiency": Decimal("1"),
                "ramp_kw_per_s": Decimal("100"),
            },
        ),
        FixedSeedRandom(seed=0),
    )
    return battery


def _set_power_command(value_kw: Decimal) -> Command:
    return Command(
        command_id="cmd-1",
        simulation_time=0,
        target_device_id="battery-1",
        type="set_power_kw",
        payload={"value": value_kw},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _make_tick_loop_with_battery_alarm(
    run_id: str = "driver-test-1",
    repository: InMemoryRunRepository | None = None,
) -> TickLoop:
    battery = _make_battery_with_low_charge_limit()
    battery.apply_command(_set_power_command(Decimal("500")))
    return TickLoop(
        run_id=run_id,
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=(battery,),
        run_repository=repository,
    )


def test_publish_buffer_before_stream_keeps_history_when_stream_raises() -> None:
    """Welle-4b-Review-Fix #12: bei Stream-Exception bleibt die
    History konsistent — Buffer wird VOR dem Stream beschrieben.
    """

    class _RaisingStream:
        def publish(self, alarm: Alarm) -> None:
            raise RuntimeError("publish boom")

        def subscriber_count(self) -> int:
            return 0

    history_buffer = AlarmHistoryBuffer()
    raising_stream = cast(AlarmStreamPort, _RaisingStream())
    loop = _make_tick_loop_with_battery_alarm()
    driver = DemoTickLoopDriver(
        loop,
        alarm_stream_provider=lambda: raising_stream,
        alarm_history_buffer_provider=lambda: history_buffer,
    )
    result = loop.tick()
    assert len(result.emitted_alarms) == 1
    with pytest.raises(RuntimeError):
        driver._publish_emitted_alarms(result)
    # Trotz Stream-Exception ist der Alarm in der History.
    history = history_buffer.get_recent(run_id=loop.run_id, limit=10)
    assert len(history) == 1


def test_late_wiring_provider_reads_app_state_at_each_tick() -> None:
    """Welle-4b-Review-Fix #1: der Provider-Callable wird bei
    jedem Tick neu evaluiert — wenn die Slot-Referenz spaeter
    bereitgestellt wird, sieht der Driver sie."""
    holder: dict[str, AlarmHistoryBuffer | None] = {"buffer": None}
    loop = _make_tick_loop_with_battery_alarm()
    driver = DemoTickLoopDriver(
        loop,
        alarm_history_buffer_provider=lambda: holder["buffer"],
    )
    result_1 = loop.tick()
    assert len(result_1.emitted_alarms) == 1
    # Erster Publish — Buffer ist noch None, kein Append.
    driver._publish_emitted_alarms(result_1)
    # Buffer nachtraeglich verdrahten (simuliert
    # `configure_alarm_stream` nach `configure_demo_run`).
    holder["buffer"] = AlarmHistoryBuffer()
    # Naechster Tick erzeugt einen neuen Alarm; Publish sollte
    # jetzt im Buffer landen.
    battery = _make_battery_with_low_charge_limit()
    battery.apply_command(_set_power_command(Decimal("500")))
    fake_result = TickResult(
        tick=1,
        simulation_time=1000,
        popped_events=(),
        emitted_telemetry=(),
        emitted_alarms=(
            Alarm(
                alarm_id="a-late",
                run_id=loop.run_id,
                simulation_time_ms=1000,
                target="battery-1",
                code="power_clamp_limited",
                severity="warning",
                message="",
                status="active",
                fault_id=None,
            ),
        ),
    )
    driver._publish_emitted_alarms(fake_result)
    history = holder["buffer"].get_recent(run_id=loop.run_id, limit=10)
    assert len(history) == 1
    assert history[0].alarm_id == "a-late"


def test_stop_mirrors_terminal_state_to_repository() -> None:
    """Welle-4b-Review-Fix #9: `stop()` setzt den TickLoop-State
    auf `stopped` und mirrort an das injizierte Repository,
    sodass der persistierte Run-Status nach Driver-Shutdown
    nicht mehr `running` ist."""
    repository = InMemoryRunRepository()
    from grid_gym.hexagon.core.domain.run import RunMetadata

    repository.save(
        RunMetadata(
            run_id="driver-test-1",
            scenario_hash="0" * 64,
            schema_version="grid-gym.scenario.v1",
            seed=42,
            tick_ms=1000,
            started_at="",
            ended_at="",
            tool_version="0.1.0",
        )
    )
    loop = _make_tick_loop_with_battery_alarm(repository=repository)
    # Loop einmal anticken, damit der State auf `running` flippt.
    loop.tick()
    assert repository.get_status("driver-test-1") == "running"
    driver = DemoTickLoopDriver(loop)

    async def _run() -> None:
        # Driver wurde nicht gestartet — stop() ist No-op fuer
        # den Task, soll aber den State-Mirror trotzdem ausloesen,
        # wenn der Loop noch nicht terminal ist.
        driver._task = asyncio.create_task(asyncio.sleep(0))
        await driver.stop()

    asyncio.run(_run())
    assert loop.control_state == "stopped"
    assert repository.get_status("driver-test-1") == "stopped"


def test_run_loop_catches_tick_exception_and_marks_run_stopped() -> None:
    """Welle-4b-Review-Fix #2: eine Exception in `tick()` killt
    den Driver-Task nicht silently — sie wird gefangen, geloggt
    und der State auf `stopped` mirror'd."""

    class _ExplodingTickLoop:
        def __init__(self, run_id: str) -> None:
            self._run_id = run_id
            self._control_state = "running"
            self.marked_failed = False
            self.finalized = False

        @property
        def run_id(self) -> str:
            return self._run_id

        @property
        def control_state(self) -> str:
            return self._control_state

        def tick(self) -> TickResult:
            raise ValueError("device blew up mid-tick")

        def request(self, action: str) -> None:
            self._control_state = "stopped"

        def mark_run_failed(self) -> None:
            self.marked_failed = True

        def finalize(self) -> tuple[object, ...]:
            self.finalized = True
            return ()

    fake_loop = _ExplodingTickLoop("driver-explode-1")
    driver = DemoTickLoopDriver(cast(TickLoop, fake_loop), tick_interval_s=0.01)

    async def _run() -> None:
        driver.start()
        # Driver-Task sollte selbst beenden (Exception → catch →
        # Force-Stop). Warten mit Timeout, sonst haengt der Test.
        assert driver._task is not None
        try:
            await asyncio.wait_for(driver._task, timeout=2.0)
        except asyncio.TimeoutError:
            driver._task.cancel()
            raise

    asyncio.run(_run())
    # State wurde via `request("stop")` auf `stopped` gesetzt.
    assert fake_loop._control_state == "stopped"
    assert driver.is_running is False
    # ADR 0067 §2.4: der Failure-Pfad markiert den Lauf als Partial und
    # finalisiert ihn (im `finally`) — nicht nur stop().
    assert fake_loop.marked_failed is True
    assert fake_loop.finalized is True


def test_run_loop_finalizes_on_natural_termination_without_marking_failed() -> None:
    """ADR 0067 §2.4: verlaesst `_tick_forever()` den Loop bei terminalem
    `control_state` (natuerliche Terminierung), feuert `finalize()` im
    `finally` — nicht nur ueber stop(). Der saubere Lauf wird NICHT als
    failed markiert (kein Partial-Run)."""

    class _SelfTerminatingTickLoop:
        def __init__(self, run_id: str) -> None:
            self._run_id = run_id
            self._control_state = "running"
            self._ticks = 0
            self.marked_failed = False
            self.finalized = False

        @property
        def run_id(self) -> str:
            return self._run_id

        @property
        def control_state(self) -> str:
            return self._control_state

        def tick(self) -> TickResult:
            self._ticks += 1
            if self._ticks >= 2:
                self._control_state = "stopped"
            return TickResult(
                tick=self._ticks,
                simulation_time=self._ticks * 1000,
                popped_events=(),
                emitted_telemetry=(),
                emitted_alarms=(),
            )

        def request(self, action: str) -> None:
            self._control_state = "stopped"

        def mark_run_failed(self) -> None:
            self.marked_failed = True

        def finalize(self) -> tuple[object, ...]:
            self.finalized = True
            return ()

    fake_loop = _SelfTerminatingTickLoop("driver-natural-1")
    driver = DemoTickLoopDriver(cast(TickLoop, fake_loop), tick_interval_s=0.001)

    async def _run() -> None:
        driver.start()
        assert driver._task is not None
        await asyncio.wait_for(driver._task, timeout=2.0)

    asyncio.run(_run())
    assert fake_loop.finalized is True  # finalize() im finally
    assert fake_loop.marked_failed is False  # sauberer Lauf, kein Partial
    assert driver.is_running is False


def test_configure_demo_run_orphan_guard_rejects_second_run_id() -> None:
    """Welle-4b-Review-Fix #13: `configure_demo_run` mit einem
    zweiten `run_id` orphant den bisherigen Driver — der Guard
    weist hart ab statt stille Drop."""
    from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
    from grid_gym.composition._demo_setup import (
        _DemoTickLoopDriverAlreadyConfiguredError,
        configure_demo_run,
    )
    from grid_gym.adapters.driving.http_api._tick_loop_registry import (
        TickLoopRegistry,
    )
    from grid_gym.adapters.driving.http_api.app import (
        app,
        configure_run_repository,
        configure_tick_loop_registry,
    )

    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    configure_tick_loop_registry(TickLoopRegistry())
    # Reset des Driver-Slots, damit der Test isoliert ist (Fixtures
    # in anderen Tests koennen ihn gesetzt haben).
    app.state.demo_tick_loop_driver = None
    configure_demo_run(run_id="run-a")
    # Erster Aufruf erfolgreich; der Slot ist jetzt belegt.
    assert app.state.demo_tick_loop_driver is not None
    try:
        with pytest.raises(_DemoTickLoopDriverAlreadyConfiguredError):
            configure_demo_run(run_id="run-b")
    finally:
        # Slot-Reset fuer nachfolgende Tests.
        app.state.demo_tick_loop_driver = None
    # Sanity: MersenneTwister-Import war im Test gebraucht (vermeidet
    # ungenutzten Import-Lint).
    _ = MersenneTwisterRandomPort


# ---------------------------------------------------------------------------
# ADR 0075 §2.1/§2.3/§2.4: Field-Publish (Push-Seite) — Fan-out + Lifecycle
# ---------------------------------------------------------------------------


class _RecordingFieldPublish:
    """Inline-Stub: zeichnet start/publish/stop auf; optional werfen."""

    def __init__(
        self,
        *,
        start_raises: bool = False,
        publish_raises: bool = False,
        stop_raises: bool = False,
    ) -> None:
        self.start_calls = 0
        self.stop_calls = 0
        self.published: list[DomainTelemetryPoint] = []
        self._start_raises = start_raises
        self._publish_raises = publish_raises
        self._stop_raises = stop_raises

    def start(self) -> None:
        self.start_calls += 1
        if self._start_raises:
            raise FieldPublishPortStartError("connect boom")

    def publish(self, point: DomainTelemetryPoint) -> None:
        if self._publish_raises:
            raise RuntimeError("publish boom")
        self.published.append(point)

    def stop(self) -> None:
        self.stop_calls += 1
        if self._stop_raises:
            raise FieldPublishPortStopError("disconnect boom")


def _domain_point(seq: int = 0) -> DomainTelemetryPoint:
    return DomainTelemetryPoint(
        run_id="driver-test-1",
        tick=0,
        simulation_time=0,
        device_id="meter-1",
        metric="voltage_v",
        value=Decimal("230.5"),
        unit="V",
        quality=Quality.VALID,
        source="smart_meter.meter-1",
        sequence=seq,
    )


def _telemetry_result(*points: DomainTelemetryPoint) -> TickResult:
    return TickResult(
        tick=0,
        simulation_time=0,
        popped_events=(),
        emitted_telemetry=points,
        emitted_alarms=(),
    )


def test_field_publish_fans_out_each_emitted_domain_point() -> None:
    """ADR 0075 §2.1: der Driver publisht jeden emittierten Punkt als
    Domaenen-`TelemetryPoint` (volle `Decimal`-Fidelity, kein float-Cast)."""
    port = _RecordingFieldPublish()
    loop = _make_tick_loop_with_battery_alarm()
    driver = DemoTickLoopDriver(loop, field_publish_provider=lambda: port)
    asyncio.run(driver._start_field_publish())
    assert port.start_calls == 1
    driver._publish_field(_telemetry_result(_domain_point(0), _domain_point(1)))
    assert len(port.published) == 2
    # Decimal-Fidelity: kein Decimal->float-Cast (Gegensatz zum Port-Stream).
    assert port.published[0].value == Decimal("230.5")


def test_field_publish_noop_without_configured_port() -> None:
    """`None`-Provider → kein aktiver Port → Fan-out + Lifecycle sind No-op
    (byte-identisch)."""
    loop = _make_tick_loop_with_battery_alarm()
    driver = DemoTickLoopDriver(loop)  # kein field_publish_provider
    asyncio.run(driver._start_field_publish())
    assert driver._active_field_publish is None
    driver._publish_field(_telemetry_result(_domain_point()))  # kein Fehler
    asyncio.run(driver._stop_field_publish())  # idempotent, kein Fehler


def test_field_publish_degrades_on_start_failure() -> None:
    """ADR 0075 §2.4: schlaegt `start()` fehl, wird Field-Publish fuer den
    Run deaktiviert (graceful degrade) — kein Publish, kein Crash."""
    port = _RecordingFieldPublish(start_raises=True)
    loop = _make_tick_loop_with_battery_alarm()
    driver = DemoTickLoopDriver(loop, field_publish_provider=lambda: port)
    asyncio.run(driver._start_field_publish())  # start() wirft → gefangen, degrade
    assert port.start_calls == 1
    assert driver._active_field_publish is None
    driver._publish_field(_telemetry_result(_domain_point()))
    assert port.published == []


def test_field_publish_survives_publish_exception() -> None:
    """Pro-Point try/except (Muster `_publish_emitted_telemetry`): ein
    Publish-Fehler toetet nicht den Driver."""
    port = _RecordingFieldPublish(publish_raises=True)
    loop = _make_tick_loop_with_battery_alarm()
    driver = DemoTickLoopDriver(loop, field_publish_provider=lambda: port)
    asyncio.run(driver._start_field_publish())
    driver._publish_field(_telemetry_result(_domain_point()))  # kein Raise
    assert port.published == []


def test_field_publish_lifecycle_start_publish_stop_via_run_loop() -> None:
    """ADR 0075 §2.4: der Driver-`_run_loop` ruft `start()` vor dem Ticken,
    publisht je Tick und `stop()` im `finally` (auf jedem Exit-Pfad)."""

    class _TelemetryEmittingTickLoop:
        def __init__(self, run_id: str) -> None:
            self._run_id = run_id
            self._control_state = "running"
            self._ticks = 0
            self.finalized = False

        @property
        def run_id(self) -> str:
            return self._run_id

        @property
        def control_state(self) -> str:
            return self._control_state

        def tick(self) -> TickResult:
            self._ticks += 1
            if self._ticks >= 2:
                self._control_state = "stopped"
            return _telemetry_result(_domain_point(self._ticks))

        def request(self, action: str) -> None:
            self._control_state = "stopped"

        def mark_run_failed(self) -> None:
            pass

        def finalize(self) -> tuple[object, ...]:
            self.finalized = True
            return ()

    port = _RecordingFieldPublish()
    fake_loop = _TelemetryEmittingTickLoop("driver-fp-1")
    driver = DemoTickLoopDriver(
        cast(TickLoop, fake_loop),
        tick_interval_s=0.001,
        field_publish_provider=lambda: port,
    )

    async def _run() -> None:
        driver.start()
        assert driver._task is not None
        await asyncio.wait_for(driver._task, timeout=2.0)

    asyncio.run(_run())
    assert port.start_calls == 1
    assert len(port.published) >= 1  # mind. ein Tick emittierte vor Stop
    assert port.stop_calls == 1  # im finally gestoppt
    assert fake_loop.finalized is True


def test_field_publish_stop_swallows_disconnect_error() -> None:
    """Review-Fix #9: ein harter Disconnect-Fehler in `stop()` wird gefangen +
    geloggt — kippt nicht den `_run_loop`-`finally`/`finalize()`-Pfad; der
    aktive Port wird trotzdem zurueckgesetzt (Best-Effort-Cleanup)."""
    port = _RecordingFieldPublish(stop_raises=True)
    loop = _make_tick_loop_with_battery_alarm()
    driver = DemoTickLoopDriver(loop, field_publish_provider=lambda: port)
    asyncio.run(driver._start_field_publish())
    assert driver._active_field_publish is port
    asyncio.run(driver._stop_field_publish())  # wirft NICHT (gefangen)
    assert port.stop_calls == 1
    assert driver._active_field_publish is None


def test_field_publish_status_off_when_unconfigured() -> None:
    """Review-Fix #8: ohne Port → `off` (kein Feed erwartet)."""
    driver = DemoTickLoopDriver(_make_tick_loop_with_battery_alarm())
    assert driver.field_publish_status == "off"


def test_field_publish_status_active_after_successful_start() -> None:
    port = _RecordingFieldPublish()
    driver = DemoTickLoopDriver(
        _make_tick_loop_with_battery_alarm(), field_publish_provider=lambda: port
    )
    asyncio.run(driver._start_field_publish())
    assert driver.field_publish_status == "active"


def test_field_publish_status_degraded_after_start_failure() -> None:
    """Review-Fix #8: konfiguriert, aber Connect fehlgeschlagen → `degraded`
    (nicht `off`) — der leere Feed ist beobachtbar."""
    port = _RecordingFieldPublish(start_raises=True)
    driver = DemoTickLoopDriver(
        _make_tick_loop_with_battery_alarm(), field_publish_provider=lambda: port
    )
    asyncio.run(driver._start_field_publish())
    assert driver.field_publish_status == "degraded"


def test_field_publish_status_degraded_after_publish_failure() -> None:
    port = _RecordingFieldPublish(publish_raises=True)
    driver = DemoTickLoopDriver(
        _make_tick_loop_with_battery_alarm(), field_publish_provider=lambda: port
    )
    asyncio.run(driver._start_field_publish())
    driver._publish_field(_telemetry_result(_domain_point()))
    assert driver.field_publish_status == "degraded"


# ---------------------------------------------------------------------------
# ADR 0075 §2.2/§2.4: Pull-Seite — DeviceServerPort-Lifecycle + Projektion
# ---------------------------------------------------------------------------


class _RecordingDeviceServer:
    """Inline-Stub fuer `DeviceServerPort` (bind/listen via start, close via
    stop); optional werfen fuer Bind-/Close-Fehler."""

    def __init__(self, *, start_raises: bool = False, stop_raises: bool = False) -> None:
        self.start_calls = 0
        self.stop_calls = 0
        self._start_raises = start_raises
        self._stop_raises = stop_raises

    def start(self) -> None:
        self.start_calls += 1
        if self._start_raises:
            raise DeviceServerPortStartError("bind in use")

    def stop(self) -> None:
        self.stop_calls += 1
        if self._stop_raises:
            raise DeviceServerPortStopError("close boom")


def test_update_projection_feeds_current_value_projection() -> None:
    """ADR 0075 §2.2: der Driver fuettert die Projektion pro Tick aus
    `emitted_telemetry`."""
    proj = CurrentValueProjection()
    driver = DemoTickLoopDriver(_make_tick_loop_with_battery_alarm(), current_value_projection=proj)
    driver._update_projection(_telemetry_result(_domain_point(0)))
    point = proj.latest("meter-1", "voltage_v")
    assert point is not None
    assert point.value == Decimal("230.5")


def test_device_server_lifecycle_start_stop() -> None:
    server = _RecordingDeviceServer()
    driver = DemoTickLoopDriver(
        _make_tick_loop_with_battery_alarm(), device_server_provider=lambda: server
    )
    asyncio.run(driver._start_device_server())
    assert server.start_calls == 1
    assert driver._active_device_server is server
    asyncio.run(driver._stop_device_server())
    assert server.stop_calls == 1
    assert driver._active_device_server is None


def test_device_server_bind_failure_propagates_hard() -> None:
    """ADR 0075 §2.4: Bind-in-use ist ein harter Fehler — `start` propagiert
    (der Lauf startet nicht; kein graceful-Degrade wie bei der Push-Seite)."""
    server = _RecordingDeviceServer(start_raises=True)
    driver = DemoTickLoopDriver(
        _make_tick_loop_with_battery_alarm(), device_server_provider=lambda: server
    )
    with pytest.raises(DeviceServerPortStartError):
        asyncio.run(driver._start_device_server())
    assert driver._active_device_server is None


def test_device_server_stop_swallows_close_error() -> None:
    server = _RecordingDeviceServer(stop_raises=True)
    driver = DemoTickLoopDriver(
        _make_tick_loop_with_battery_alarm(), device_server_provider=lambda: server
    )
    asyncio.run(driver._start_device_server())
    asyncio.run(driver._stop_device_server())  # gefangen + geloggt, kein Raise
    assert driver._active_device_server is None


def test_device_server_and_projection_noop_when_unconfigured() -> None:
    """`None`-Provider + keine Projektion → No-op (byte-identisch)."""
    driver = DemoTickLoopDriver(_make_tick_loop_with_battery_alarm())
    asyncio.run(driver._start_device_server())
    assert driver._active_device_server is None
    driver._update_projection(_telemetry_result(_domain_point()))  # keine Projektion
    asyncio.run(driver._stop_device_server())  # No-op
