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
from grid_gym.adapters.driving.http_api._tick_loop_driver import DemoTickLoopDriver
from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.domain.alarm import Alarm
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driving.alarm_stream import AlarmStreamPort
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
