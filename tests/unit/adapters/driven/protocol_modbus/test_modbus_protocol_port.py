"""Lifecycle + Read/Write fuer `ModbusDeviceProtocolPort` mit
gemocktem pymodbus-Client (M4 Welle 3, ADR 0030 + ADR 0032 §2.3).
"""

from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType
from typing import Any
from unittest.mock import MagicMock

import pytest

from grid_gym.adapters.driven.protocol_modbus import (
    ModbusDatatype,
    ModbusDeviceProtocolPort,
    ModbusPortAccessMismatchError,
    ModbusPortConnectError,
    ModbusPortMissingCommandPayloadError,
    ModbusPortNotStartedError,
    ModbusPortReadFailedError,
    ModbusPortWriteFailedError,
    ModbusProtocolPortConfig,
    ModbusRegisterConfig,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPort,
    DeviceProtocolPortUnknownTargetError,
)


def _build_config() -> ModbusProtocolPortConfig:
    return ModbusProtocolPortConfig(
        host="localhost",
        port=502,
        unit_id=1,
        registers={
            "soc": ModbusRegisterConfig(
                address=40001, datatype=ModbusDatatype.UINT16, access="read"
            ),
            "power": ModbusRegisterConfig(
                address=40003, datatype=ModbusDatatype.INT32, access="read"
            ),
            "setpoint": ModbusRegisterConfig(
                address=40010, datatype=ModbusDatatype.INT16, access="write"
            ),
            "multi_setpoint": ModbusRegisterConfig(
                address=40020, datatype=ModbusDatatype.INT32, access="write"
            ),
        },
    )


def _make_factory(client: MagicMock) -> Any:
    return lambda _config: client


def _make_read_response(registers: list[int]) -> MagicMock:
    response = MagicMock()
    response.registers = registers
    response.isError.return_value = False
    return response


def _make_write_response() -> MagicMock:
    response = MagicMock()
    response.isError.return_value = False
    return response


def _sample_command(value: int) -> Command:
    return Command(
        command_id="cmd-1",
        simulation_time=0,
        target_device_id="setpoint",
        type="set_setpoint",
        payload=MappingProxyType({"value": value}),
        validation_status="validated",
        result=CommandResult.ACCEPTED,
    )


def test_port_satisfies_device_protocol_port_protocol() -> None:
    client = MagicMock()
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    assert isinstance(port, DeviceProtocolPort)


def test_start_connects_via_factory() -> None:
    client = MagicMock()
    client.connect.return_value = True
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    client.connect.assert_called_once_with()


def test_start_is_idempotent() -> None:
    client = MagicMock()
    client.connect.return_value = True
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    port.start()
    assert client.connect.call_count == 1


def test_start_raises_connect_error_when_connect_returns_false() -> None:
    client = MagicMock()
    client.connect.return_value = False
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    with pytest.raises(ModbusPortConnectError):
        port.start()


def test_start_raises_connect_error_when_connect_raises_oserror() -> None:
    client = MagicMock()
    client.connect.side_effect = OSError("Connection refused")
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    with pytest.raises(ModbusPortConnectError) as exc_info:
        port.start()
    assert "Connection refused" in str(exc_info.value)


def test_stop_closes_client() -> None:
    client = MagicMock()
    client.connect.return_value = True
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    port.stop()
    client.close.assert_called_once_with()


def test_stop_is_idempotent_without_start() -> None:
    client = MagicMock()
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.stop()  # No-op
    client.close.assert_not_called()


def test_read_uint16_returns_telemetry_point() -> None:
    client = MagicMock()
    client.connect.return_value = True
    client.read_holding_registers.return_value = _make_read_response([85])
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    point = port.read("soc")
    assert point is not None
    assert point.value == Decimal(85)
    client.read_holding_registers.assert_called_once_with(address=40001, count=1, device_id=1)


def test_read_int32_returns_telemetry_point() -> None:
    client = MagicMock()
    client.connect.return_value = True
    # int32-big-endian-no-word-swap fuer 0x00010002 = 65538.
    client.read_holding_registers.return_value = _make_read_response([0x0001, 0x0002])
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    point = port.read("power")
    assert point is not None
    assert point.value == Decimal(0x00010002)
    client.read_holding_registers.assert_called_once_with(address=40003, count=2, device_id=1)


def test_read_rejects_unknown_target() -> None:
    client = MagicMock()
    client.connect.return_value = True
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    with pytest.raises(DeviceProtocolPortUnknownTargetError):
        port.read("unknown_target")


def test_read_rejects_write_access_target() -> None:
    client = MagicMock()
    client.connect.return_value = True
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    with pytest.raises(ModbusPortAccessMismatchError):
        port.read("setpoint")  # setpoint is access="write"


def test_read_before_start_raises_not_started() -> None:
    client = MagicMock()
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    with pytest.raises(ModbusPortNotStartedError):
        port.read("soc")


def test_read_translates_modbus_response_error_into_read_failed() -> None:
    client = MagicMock()
    client.connect.return_value = True
    bad_response = MagicMock()
    bad_response.isError.return_value = True
    client.read_holding_registers.return_value = bad_response
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    with pytest.raises(ModbusPortReadFailedError):
        port.read("soc")


def test_write_single_register_uses_fc06() -> None:
    client = MagicMock()
    client.connect.return_value = True
    client.write_register.return_value = _make_write_response()
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    port.write("setpoint", _sample_command(value=42))
    client.write_register.assert_called_once_with(address=40010, value=42, device_id=1)


def test_write_multi_register_uses_fc10() -> None:
    client = MagicMock()
    client.connect.return_value = True
    client.write_registers.return_value = _make_write_response()
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    # int32-big-endian-no-word-swap fuer 0x00010002.
    port.write(
        "multi_setpoint",
        Command(
            command_id="c",
            simulation_time=0,
            target_device_id="multi_setpoint",
            type="x",
            payload=MappingProxyType({"value": 0x00010002}),
            validation_status="v",
            result=CommandResult.ACCEPTED,
        ),
    )
    client.write_registers.assert_called_once_with(
        address=40020, values=[0x0001, 0x0002], device_id=1
    )


def test_write_rejects_unknown_target() -> None:
    client = MagicMock()
    client.connect.return_value = True
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    with pytest.raises(DeviceProtocolPortUnknownTargetError):
        port.write("unknown", _sample_command(42))


def test_write_rejects_read_access_target() -> None:
    client = MagicMock()
    client.connect.return_value = True
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    with pytest.raises(ModbusPortAccessMismatchError):
        port.write("soc", _sample_command(42))


def test_write_rejects_command_payload_without_value_key() -> None:
    client = MagicMock()
    client.connect.return_value = True
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    command = Command(
        command_id="c",
        simulation_time=0,
        target_device_id="setpoint",
        type="x",
        payload=MappingProxyType({}),
        validation_status="v",
        result=CommandResult.ACCEPTED,
    )
    with pytest.raises(ModbusPortMissingCommandPayloadError):
        port.write("setpoint", command)


def test_write_translates_modbus_response_error_into_write_failed() -> None:
    client = MagicMock()
    client.connect.return_value = True
    bad_response = MagicMock()
    bad_response.isError.return_value = True
    client.write_register.return_value = bad_response
    port = ModbusDeviceProtocolPort(_build_config(), client_factory=_make_factory(client))
    port.start()
    with pytest.raises(ModbusPortWriteFailedError):
        port.write("setpoint", _sample_command(42))


def test_default_factory_constructs_pymodbus_client() -> None:
    """Smoke: Default-Factory baut tatsaechlich einen `ModbusTcpClient`."""
    from pymodbus.client import ModbusTcpClient

    from grid_gym.adapters.driven.protocol_modbus._port import _default_client_factory

    config = _build_config()
    client = _default_client_factory(config)
    assert isinstance(client, ModbusTcpClient)
