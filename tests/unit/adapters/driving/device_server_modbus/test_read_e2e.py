"""Read-Pfad-E2E (Slice 074 C2, ADR 0075 §2.1/§2.2).

Ein **echter pymodbus-Master** pollt den `ModbusDeviceServerAdapter` (realer
pymodbus-3.13-Server im Loop-Thread) und verifiziert die servierten Register
gegen das **Encode-Oracle** (deterministische `float32`-Quantisierung) + die
Quality-Discrete-Inputs. In-Process (echter Socket + echter Master), kein
testcontainers noetig — der „externe Master" ist die pymodbus-Client-Library
selbst.
"""

from __future__ import annotations

import socket
import struct
import time
from collections.abc import Iterator
from decimal import Decimal

import pytest
from pymodbus.client import ModbusTcpClient

from grid_gym.adapters.driving._field_current_value import CurrentValueProjection
from grid_gym.adapters.driving.device_server_modbus._adapter import (
    ModbusDeviceServerAdapter,
)
from grid_gym.adapters.driving.device_server_modbus._config import (
    ModbusServerConfig,
    RegisterMapping,
)
from grid_gym.adapters.driving.device_server_modbus._register_map import encode_float32
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.domain.tick_result import TickResult

_UNIT_ID = 1
_POLL_TIMEOUT_S = 3.0


def _free_port() -> int:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port: int = probe.getsockname()[1]
    probe.close()
    return port


def _point(
    device_id: str, metric: str, value: str, quality: Quality = Quality.VALID
) -> TelemetryPoint:
    return TelemetryPoint(
        run_id="run-1",
        tick=0,
        simulation_time=0,
        device_id=device_id,
        metric=metric,
        value=Decimal(value),
        unit="V",
        quality=quality,
        source=f"smart_meter.{device_id}",
        sequence=0,
    )


def _tick(*points: TelemetryPoint) -> TickResult:
    return TickResult(
        tick=0,
        simulation_time=0,
        popped_events=(),
        emitted_telemetry=points,
        emitted_alarms=(),
    )


def _connect(config: ModbusServerConfig) -> ModbusTcpClient:
    client = ModbusTcpClient(config.bind_host, port=config.bind_port)
    deadline = time.monotonic() + _POLL_TIMEOUT_S
    while time.monotonic() < deadline:
        if client.connect():
            return client
        time.sleep(0.05)
    pytest.fail("Master konnte nicht zum Modbus-Server verbinden")


@pytest.fixture
def server_ctx() -> Iterator[tuple[ModbusServerConfig, CurrentValueProjection]]:
    projection = CurrentValueProjection()
    projection.update_from_tick(
        _tick(
            _point("meter-1", "voltage_v", "230.5", Quality.VALID),
            _point("meter-2", "power_w", "-12.5", Quality.STALE),
        )
    )
    config = ModbusServerConfig(
        bind_host="127.0.0.1",
        bind_port=_free_port(),
        register_map=(
            RegisterMapping("meter-1", "voltage_v", 0),
            RegisterMapping("meter-2", "power_w", 2),
        ),
        unit_id=_UNIT_ID,
    )
    adapter = ModbusDeviceServerAdapter(config, projection)
    adapter.start()
    try:
        yield config, projection
    finally:
        adapter.stop()


def test_master_reads_holding_registers_matches_oracle(
    server_ctx: tuple[ModbusServerConfig, CurrentValueProjection],
) -> None:
    config, _projection = server_ctx
    client = _connect(config)
    try:
        rr = client.read_holding_registers(0, count=4, device_id=_UNIT_ID)
        assert not rr.isError()
        assert tuple(rr.registers[0:2]) == encode_float32(Decimal("230.5"))
        assert tuple(rr.registers[2:4]) == encode_float32(Decimal("-12.5"))
        # Und dekodiert als float32 (beide Verlustschritte beruecksichtigt):
        decoded = struct.unpack(">f", struct.pack(">HH", *rr.registers[0:2]))[0]
        assert decoded == pytest.approx(230.5)
    finally:
        client.close()


def test_master_reads_quality_as_discrete_inputs(
    server_ctx: tuple[ModbusServerConfig, CurrentValueProjection],
) -> None:
    config, _projection = server_ctx
    client = _connect(config)
    try:
        rr = client.read_discrete_inputs(0, count=2, device_id=_UNIT_ID)
        assert not rr.isError()
        # meter-1 VALID → True, meter-2 STALE → False (ADR 0074-Quality-Marker).
        assert rr.bits[0:2] == [True, False]
    finally:
        client.close()


def test_master_sees_updated_value_after_new_tick(
    server_ctx: tuple[ModbusServerConfig, CurrentValueProjection],
) -> None:
    config, projection = server_ctx
    client = _connect(config)
    try:
        projection.update_from_tick(_tick(_point("meter-1", "voltage_v", "240.0")))
        expected = encode_float32(Decimal("240.0"))
        deadline = time.monotonic() + _POLL_TIMEOUT_S
        got: tuple[int, ...] | None = None
        while time.monotonic() < deadline:
            rr = client.read_holding_registers(0, count=2, device_id=_UNIT_ID)
            if not rr.isError() and tuple(rr.registers[0:2]) == expected:
                got = tuple(rr.registers[0:2])
                break
            time.sleep(0.05)
        assert got == expected  # Refresh-Task hat den neuen Tick nachgezogen
    finally:
        client.close()
