"""Write-Pfad-E2E (Slice 075 S1b, ADR 0076 §2.1/§2.3).

Ein **echter pymodbus-Master** schreibt (FC16) einen `float32`-Sollwert in ein
`write_map`-Fenster des `ModbusDeviceServerAdapter` (realer pymodbus-3.13-Server
im Loop-Thread); der Server dekodiert ihn und puffert ihn im geteilten
`InboundCommandBuffer`. In-Process (echter Socket + echter Master), kein
testcontainers noetig — der „externe Master" ist die pymodbus-Client-Library.

Belegt die drei S1b-Kern-Nahtstellen:
- **Write→`Command`**: Master-Write → dekodierter `Command` (target/type/payload).
- **Capture**: der aufgeloeste Sim-Tick landet in der Aufzeichnung (ADR 0076 §2.1).
- **Diskriminator**: der interne Refresh-Push (FC03) + Reads loesen **keinen**
  Inbound-`Command` aus (nur FC06/FC16, `set_values is not None`).
- **Volle Kette**: Master-Write → Puffer → `TickLoop` (Schritt A0i) → Zielgeraet
  erhaelt den `Command` mit dem dekodierten `Decimal`-Wert.
"""

from __future__ import annotations

import socket
import time
from collections.abc import Iterator, Mapping
from decimal import Decimal
from typing import Self

import pytest
from pymodbus.client import ModbusTcpClient

from grid_gym.adapters.driving._field_current_value import CurrentValueProjection
from grid_gym.adapters.driving._inbound_command_buffer import InboundCommandBuffer
from grid_gym.adapters.driving.device_server_modbus._adapter import (
    ModbusDeviceServerAdapter,
)
from grid_gym.adapters.driving.device_server_modbus._config import (
    ModbusServerConfig,
    RegisterMapping,
    WritableRegisterMapping,
)
from grid_gym.adapters.driving.device_server_modbus._register_map import encode_float32
from grid_gym.hexagon.core.devices._protocol import DeviceModel
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import (
    DeviceTickContext,
    DeviceTickOutcome,
)
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driven.random import RandomPort
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom

_UNIT_ID = 1
_TIMEOUT_S = 3.0
_SETPOINT_ADDRESS = 10  # Sollwert-Fenster (Read-Meter liegt auf 0..1, disjunkt).


def _free_port() -> int:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port: int = probe.getsockname()[1]
    probe.close()
    return port


def _ctx(simulation_time: int) -> DeviceTickContext:
    return DeviceTickContext(tick=0, simulation_time=simulation_time, tick_ms=1000)


def _config() -> ModbusServerConfig:
    return ModbusServerConfig(
        bind_host="127.0.0.1",
        bind_port=_free_port(),
        register_map=(RegisterMapping("meter-1", "voltage_v", 0),),
        write_map=(WritableRegisterMapping(_SETPOINT_ADDRESS, "battery-1", "set_power_kw"),),
        unit_id=_UNIT_ID,
    )


def _seeded_projection() -> CurrentValueProjection:
    projection = CurrentValueProjection()
    projection.update_from_tick(
        TickResult(
            tick=0,
            simulation_time=0,
            popped_events=(),
            emitted_telemetry=(
                TelemetryPoint(
                    run_id="run-1",
                    tick=0,
                    simulation_time=0,
                    device_id="meter-1",
                    metric="voltage_v",
                    value=Decimal("230.5"),
                    unit="V",
                    quality=Quality.VALID,
                    source="smart_meter.meter-1",
                    sequence=0,
                ),
            ),
            emitted_alarms=(),
        )
    )
    return projection


def _connect(config: ModbusServerConfig) -> ModbusTcpClient:
    client = ModbusTcpClient(config.bind_host, port=config.bind_port)
    deadline = time.monotonic() + _TIMEOUT_S
    while time.monotonic() < deadline:
        if client.connect():
            return client
        time.sleep(0.05)
    pytest.fail("Master konnte nicht zum Modbus-Server verbinden")


def _drain_until(buffer: InboundCommandBuffer, context: DeviceTickContext) -> tuple[Command, ...]:
    """Draint den Puffer; wartet kurz, falls der Write-Callback noch nicht
    durchlief (der Enqueue passiert zwar vor der Write-Response, aber ein leerer
    Drain ist harmlos — er entleert nichts und wird erneut versucht)."""
    deadline = time.monotonic() + _TIMEOUT_S
    while time.monotonic() < deadline:
        commands = buffer.drain_due(context)
        if commands:
            return commands
        time.sleep(0.02)
    return ()


@pytest.fixture
def write_ctx() -> Iterator[tuple[ModbusServerConfig, InboundCommandBuffer]]:
    config = _config()
    buffer = InboundCommandBuffer()
    adapter = ModbusDeviceServerAdapter(config, _seeded_projection(), inbound_buffer=buffer)
    adapter.start()
    try:
        yield config, buffer
    finally:
        adapter.stop()


def test_master_write_lands_as_inbound_command(
    write_ctx: tuple[ModbusServerConfig, InboundCommandBuffer],
) -> None:
    config, buffer = write_ctx
    client = _connect(config)
    try:
        rr = client.write_registers(
            _SETPOINT_ADDRESS, list(encode_float32(Decimal("42.5"))), device_id=_UNIT_ID
        )
        assert not rr.isError()
        commands = _drain_until(buffer, _ctx(1000))
    finally:
        client.close()

    assert len(commands) == 1
    command = commands[0]
    assert command.target_device_id == "battery-1"
    assert command.type == "set_power_kw"
    assert command.simulation_time == 1000  # auf den aktuellen Tick aufgeloest
    assert command.validation_status == "inbound"
    assert command.payload == {"value": Decimal("42.5")}
    # Capture zeichnet den aufgeloesten Tick auf (Source-of-Truth, ADR 0076 §2.1).
    assert buffer.capture()[0].resolved_sim_tick == 1000


def test_reads_and_refresh_do_not_enqueue(
    write_ctx: tuple[ModbusServerConfig, InboundCommandBuffer],
) -> None:
    # Diskriminator: nur echte Master-Writes (FC06/FC16) enqueuen. Reads (FC03)
    # UND der interne Refresh-Push (der ebenfalls FC03 nutzt) duerfen nicht.
    config, buffer = write_ctx
    client = _connect(config)
    try:
        for _ in range(3):
            rr = client.read_holding_registers(0, count=2, device_id=_UNIT_ID)
            assert not rr.isError()
            time.sleep(0.06)  # > Refresh-Intervall (50ms) → mind. ein Refresh-Push
    finally:
        client.close()
    assert buffer.drain_due(_ctx(1000)) == ()
    assert buffer.capture() == ()


def test_master_write_reaches_target_device_via_tick_loop(
    write_ctx: tuple[ModbusServerConfig, InboundCommandBuffer],
) -> None:
    # Volle Kette (DoD): Master-Write → Puffer → TickLoop-Schritt A0i → Zielgeraet.
    config, buffer = write_ctx
    battery = _CommandRecordingDevice("battery-1")
    loop = TickLoop(
        run_id="slice-075-write-e2e",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=(battery,),
        inbound_source=buffer,
    )
    client = _connect(config)
    try:
        rr = client.write_registers(
            _SETPOINT_ADDRESS, list(encode_float32(Decimal("-7.5"))), device_id=_UNIT_ID
        )
        assert not rr.isError()
        # Warten bis der Write-Callback gepuffert hat, dann ticken (A0i draint).
        deadline = time.monotonic() + _TIMEOUT_S
        while time.monotonic() < deadline and not battery.received:
            loop.tick()
            time.sleep(0.02)
    finally:
        client.close()

    assert len(battery.received) == 1
    delivered = battery.received[0]
    assert delivered.target_device_id == "battery-1"
    assert delivered.type == "set_power_kw"
    assert delivered.payload == {"value": Decimal("-7.5")}


class _CommandRecordingDevice:
    """Test-Double (`DeviceModel`): zeichnet jeden `apply_command` auf."""

    def __init__(self, device_id: str) -> None:
        self._device_id = device_id
        self.received: list[Command] = []

    @property
    def device_id(self) -> str:
        return self._device_id

    def initialize(self, scenario_device: ScenarioDevice, random: RandomPort) -> None:
        _ = (scenario_device, random)

    def apply_command(self, command: Command) -> CommandResult:
        self.received.append(command)
        return CommandResult.ACCEPTED

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        _ = context
        return DeviceTickOutcome(telemetry=())

    def snapshot(self) -> Mapping[str, object]:
        return {"version": 1}

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return ()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        _ = state
        return cls("battery-1")

    def set_run_id(self, run_id: str) -> None:
        _ = run_id


_ = DeviceModel  # Protokoll-Referenz (der Recorder erfuellt `DeviceModel`).
