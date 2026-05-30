"""Function-Code-Override-Tests (Decision M-d) fuer
`ModbusDeviceProtocolPort` (M4 Welle 3, ADR 0032 §2.4).
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any
from unittest.mock import MagicMock

from grid_gym.adapters.driven.protocol_modbus import (
    ModbusDatatype,
    ModbusDeviceProtocolPort,
    ModbusProtocolPortConfig,
    ModbusRegisterConfig,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult


def _make_factory(client: MagicMock) -> Any:
    return lambda _config: client


def _make_read_response(registers: list[int]) -> MagicMock:
    r = MagicMock()
    r.registers = registers
    r.isError.return_value = False
    return r


def _make_write_response() -> MagicMock:
    r = MagicMock()
    r.isError.return_value = False
    return r


def test_fc04_read_input_registers_used_when_overridden() -> None:
    config = ModbusProtocolPortConfig(
        host="localhost",
        registers={
            "input_sensor": ModbusRegisterConfig(
                address=30001,
                datatype=ModbusDatatype.UINT16,
                access="read",
                function_code=4,
            ),
        },
    )
    client = MagicMock()
    client.connect.return_value = True
    client.read_input_registers.return_value = _make_read_response([1234])
    port = ModbusDeviceProtocolPort(config, client_factory=_make_factory(client))
    port.start()
    point = port.read("input_sensor")
    assert point is not None
    client.read_input_registers.assert_called_once_with(address=30001, count=1, device_id=1)
    client.read_holding_registers.assert_not_called()


def test_fc03_read_holding_registers_used_as_default_for_read() -> None:
    config = ModbusProtocolPortConfig(
        host="localhost",
        registers={
            "soc": ModbusRegisterConfig(
                address=40001, datatype=ModbusDatatype.UINT16, access="read"
            )
        },
    )
    client = MagicMock()
    client.connect.return_value = True
    client.read_holding_registers.return_value = _make_read_response([85])
    port = ModbusDeviceProtocolPort(config, client_factory=_make_factory(client))
    port.start()
    port.read("soc")
    client.read_holding_registers.assert_called_once()
    client.read_input_registers.assert_not_called()


def test_fc06_write_single_register_used_as_default_for_single_register_write() -> None:
    config = ModbusProtocolPortConfig(
        host="localhost",
        registers={
            "setpoint": ModbusRegisterConfig(
                address=40010,
                datatype=ModbusDatatype.INT16,
                access="write",
            )
        },
    )
    client = MagicMock()
    client.connect.return_value = True
    client.write_register.return_value = _make_write_response()
    port = ModbusDeviceProtocolPort(config, client_factory=_make_factory(client))
    port.start()
    port.write(
        "setpoint",
        Command(
            command_id="c",
            simulation_time=0,
            target_device_id="setpoint",
            type="x",
            payload=MappingProxyType({"value": 42}),
            validation_status="v",
            result=CommandResult.ACCEPTED,
        ),
    )
    client.write_register.assert_called_once()
    client.write_registers.assert_not_called()


def test_fc10_write_multiple_registers_used_as_default_for_multi_register_write() -> None:
    config = ModbusProtocolPortConfig(
        host="localhost",
        registers={
            "long_setpoint": ModbusRegisterConfig(
                address=40020, datatype=ModbusDatatype.UINT32, access="write"
            )
        },
    )
    client = MagicMock()
    client.connect.return_value = True
    client.write_registers.return_value = _make_write_response()
    port = ModbusDeviceProtocolPort(config, client_factory=_make_factory(client))
    port.start()
    port.write(
        "long_setpoint",
        Command(
            command_id="c",
            simulation_time=0,
            target_device_id="long_setpoint",
            type="x",
            payload=MappingProxyType({"value": 0xDEADBEEF}),
            validation_status="v",
            result=CommandResult.ACCEPTED,
        ),
    )
    client.write_registers.assert_called_once()
    client.write_register.assert_not_called()


def test_fc16_override_forces_multi_register_write_for_single_register_datatype() -> None:
    """`function_code=16`-Override forciert FC10 auch fuer single-
    register-Datatypes (z. B. wenn ein Slave nur FC10 unterstuetzt)."""
    config = ModbusProtocolPortConfig(
        host="localhost",
        registers={
            "setpoint": ModbusRegisterConfig(
                address=40010,
                datatype=ModbusDatatype.INT16,
                access="write",
                function_code=16,
            )
        },
    )
    client = MagicMock()
    client.connect.return_value = True
    client.write_registers.return_value = _make_write_response()
    port = ModbusDeviceProtocolPort(config, client_factory=_make_factory(client))
    port.start()
    port.write(
        "setpoint",
        Command(
            command_id="c",
            simulation_time=0,
            target_device_id="setpoint",
            type="x",
            payload=MappingProxyType({"value": 42}),
            validation_status="v",
            result=CommandResult.ACCEPTED,
        ),
    )
    client.write_registers.assert_called_once()
    client.write_register.assert_not_called()


def test_per_target_unit_id_override_passed_to_pymodbus_call() -> None:
    config = ModbusProtocolPortConfig(
        host="localhost",
        unit_id=1,
        registers={
            "slave_42_sensor": ModbusRegisterConfig(
                address=40001,
                datatype=ModbusDatatype.UINT16,
                access="read",
                unit_id=42,
            )
        },
    )
    client = MagicMock()
    client.connect.return_value = True
    client.read_holding_registers.return_value = _make_read_response([7])
    port = ModbusDeviceProtocolPort(config, client_factory=_make_factory(client))
    port.start()
    port.read("slave_42_sensor")
    # Parent unit_id ist 1, Override ist 42 — pymodbus muss 42 sehen.
    _args, kwargs = client.read_holding_registers.call_args
    assert kwargs["device_id"] == 42
