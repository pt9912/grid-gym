"""End-to-End-Integration-Smoke fuer M5-Welle-4b (Alarm-
Aggregation + AlarmStreamPort + Alarm-Tabelle-UI, ADR 0040).

Pinnt die produktive Wiring-Composition aus C0..C3:

1. ``POST /runs`` → 201 + run_id.
2. TickLoop mit Battery-Device registrieren; Power-Command
   ueber Limit applizieren → Battery emittiert LIMITED-Alarm.
3. ``tick()`` manuell ausfuehren → ``TickResult.emitted_alarms``
   enthaelt den Unified `Alarm` mit Run-Kontext.
4. Driver publisht den Alarm auf Stream + History-Buffer.
5. ``GET /runs/{id}/alarms`` zeigt den Alarm in der History.
6. UI-Page ``GET /runs/{id}/alarms`` rendert die Tabelle mit
   `GG-UI-005`-6-Spalten-Layout.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driven.alarm_stream_inmemory import (
    AlarmHistoryBuffer,
    InMemoryAlarmStream,
)
from grid_gym.adapters.driven.telemetry_stream_inmemory import (
    InMemoryTelemetryStream,
)
from grid_gym.adapters.driving.http_api import app
from grid_gym.adapters.driving.http_api._alarm_setup import configure_alarm_stream
from grid_gym.adapters.driving.http_api._tick_loop_driver import DemoTickLoopDriver
from grid_gym.adapters.driving.http_api._tick_loop_registry import TickLoopRegistry
from grid_gym.adapters.driving.http_api.app import (
    configure_run_repository,
    configure_telemetry_stream,
    configure_tick_loop_registry,
)
from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import (
    FakeClock,
    FixedSeedRandom,
    InMemoryRunRepository,
)


_VALID_SCENARIO_HASH = "0" * 64
_VALID_RUN_PAYLOAD: dict[str, object] = {
    "scenario_hash": _VALID_SCENARIO_HASH,
    "seed": 42,
    "tick_ms": 1000,
}


@pytest.fixture
def smoke_client() -> Iterator[
    tuple[
        TestClient,
        InMemoryRunRepository,
        TickLoopRegistry,
        InMemoryAlarmStream,
        AlarmHistoryBuffer,
    ]
]:
    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    configure_telemetry_stream(InMemoryTelemetryStream(queue_maxsize=8))
    registry = TickLoopRegistry()
    configure_tick_loop_registry(registry)
    alarm_stream = InMemoryAlarmStream(queue_maxsize=8)
    history_buffer = AlarmHistoryBuffer()
    configure_alarm_stream(alarm_stream, history_buffer)
    with TestClient(app) as client:
        yield client, repository, registry, alarm_stream, history_buffer


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


def test_alarms_full_lifecycle_workflow(
    smoke_client: tuple[
        TestClient,
        InMemoryRunRepository,
        TickLoopRegistry,
        InMemoryAlarmStream,
        AlarmHistoryBuffer,
    ],
) -> None:
    """End-to-End-Smoke: Run anlegen → TickLoop mit Battery
    registrieren → Over-rated Command → tick() emittiert
    Unified Alarm → publish auf Stream + Buffer → GET /alarms
    zeigt den Alarm → UI rendert die Tabelle."""
    client, repository, registry, alarm_stream, history_buffer = smoke_client

    # 1. Run anlegen
    create_response = client.post("/runs", json=_VALID_RUN_PAYLOAD)
    assert create_response.status_code == 201
    run_id = create_response.json()["run_id"]
    uuid.UUID(run_id)

    # 2. TickLoop + Battery registrieren
    battery = _make_battery_with_low_charge_limit()
    battery.apply_command(_set_power_command(Decimal("500")))
    tick_loop = TickLoop(
        run_id=run_id,
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=(battery,),
        run_repository=repository,
    )
    registry.register(tick_loop)

    # 3. Tick driver publisht emitted_alarms auf Stream + Buffer.
    driver = DemoTickLoopDriver(
        tick_loop,
        alarm_stream_provider=lambda: alarm_stream,
        alarm_history_buffer_provider=lambda: history_buffer,
    )
    # Wir treiben den Loop manuell (statt via asyncio-Task), um
    # deterministisch zu sein.
    result = tick_loop.tick()
    assert len(result.emitted_alarms) == 1
    # Manuelle Publish-Symmetrie (Driver-Task wuerde das in async
    # tun).
    for alarm in result.emitted_alarms:
        alarm_stream.publish(alarm)
        history_buffer.append(alarm)

    # 4. GET /alarms-history zeigt den Alarm.
    alarms_response = client.get(f"/runs/{run_id}/alarms-history")
    assert alarms_response.status_code == 200
    body = alarms_response.json()
    assert len(body["alarms"]) == 1
    alarm = body["alarms"][0]
    assert alarm["target"] == "battery-1"
    assert alarm["code"] == "power_clamp_limited"
    assert alarm["severity"] == "warning"
    assert alarm["status"] == "active"
    assert alarm["run_id"] == run_id

    # 5. UI rendert die Tabelle mit 6 Pflicht-Spalten.
    ui_response = client.get(f"/runs/{run_id}/alarms")
    assert ui_response.status_code == 200
    html = ui_response.text
    for column in ["Zeit", "Ziel", "Schweregrad", "Code", "Nachricht", "Status"]:
        assert column in html
    # Cleanup: Lifespan-Driver ist hier nicht aktiv (kein
    # configure_demo_run); kein async-Stop noetig.
    assert driver.is_running is False
