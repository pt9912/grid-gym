"""Konstruktor-Validation fuer `ModbusProtocolPortConfig` /
`ModbusRegisterConfig` (M4 Welle 3, ADR 0032 §2.1).
"""

from __future__ import annotations

import pytest

from grid_gym.adapters.driven.protocol_modbus import (
    ModbusConfigEmptyFieldError,
    ModbusConfigEmptyRegistersError,
    ModbusConfigFunctionCodeAccessMismatchError,
    ModbusConfigInvalidAccessError,
    ModbusConfigInvalidAddressError,
    ModbusConfigInvalidByteOrderError,
    ModbusConfigInvalidFunctionCodeError,
    ModbusConfigInvalidPortError,
    ModbusConfigInvalidTimeoutError,
    ModbusConfigInvalidUnitIdError,
    ModbusDatatype,
    ModbusProtocolPortConfig,
    ModbusRegisterConfig,
    datatype_register_count,
    resolve_function_code,
    resolve_unit_id,
)


def _basic_register() -> dict[str, ModbusRegisterConfig]:
    return {
        "battery1_soc": ModbusRegisterConfig(
            address=40001, datatype=ModbusDatatype.UINT16, access="read"
        ),
    }


def test_minimal_config_construction_succeeds() -> None:
    config = ModbusProtocolPortConfig(host="localhost", registers=_basic_register())
    assert config.host == "localhost"
    assert config.port == 502
    assert config.unit_id == 1
    assert config.timeout_s == pytest.approx(5.0)
    assert "battery1_soc" in config.registers


def test_config_rejects_empty_host() -> None:
    with pytest.raises(ModbusConfigEmptyFieldError) as exc_info:
        ModbusProtocolPortConfig(host="", registers=_basic_register())
    assert exc_info.value.field_name == "host"


@pytest.mark.parametrize("port", [0, -1, 65536, 99999])
def test_config_rejects_invalid_port(port: int) -> None:
    with pytest.raises(ModbusConfigInvalidPortError) as exc_info:
        ModbusProtocolPortConfig(host="localhost", port=port, registers=_basic_register())
    assert exc_info.value.value == port


@pytest.mark.parametrize("unit_id", [0, 248, 255])
def test_config_rejects_invalid_parent_unit_id(unit_id: int) -> None:
    with pytest.raises(ModbusConfigInvalidUnitIdError) as exc_info:
        ModbusProtocolPortConfig(host="localhost", unit_id=unit_id, registers=_basic_register())
    assert exc_info.value.value == unit_id
    assert exc_info.value.context == "<parent>"


@pytest.mark.parametrize("timeout_s", [0.0, -1.0])
def test_config_rejects_non_positive_timeout(timeout_s: float) -> None:
    with pytest.raises(ModbusConfigInvalidTimeoutError):
        ModbusProtocolPortConfig(host="localhost", timeout_s=timeout_s, registers=_basic_register())


def test_config_rejects_empty_registers() -> None:
    with pytest.raises(ModbusConfigEmptyRegistersError):
        ModbusProtocolPortConfig(host="localhost", registers={})


@pytest.mark.parametrize("address", [-1, 65536, 100000])
def test_register_rejects_invalid_address(address: int) -> None:
    with pytest.raises(ModbusConfigInvalidAddressError) as exc_info:
        ModbusProtocolPortConfig(
            host="localhost",
            registers={
                "x": ModbusRegisterConfig(
                    address=address,
                    datatype=ModbusDatatype.UINT16,
                    access="read",
                )
            },
        )
    assert exc_info.value.value == address
    assert exc_info.value.device_id == "x"


def test_register_rejects_invalid_byte_order() -> None:
    with pytest.raises(ModbusConfigInvalidByteOrderError):
        ModbusProtocolPortConfig(
            host="localhost",
            registers={
                "x": ModbusRegisterConfig(
                    address=0,
                    datatype=ModbusDatatype.INT16,
                    access="read",
                    byte_order="middle_endian",
                )
            },
        )


def test_register_rejects_invalid_access() -> None:
    with pytest.raises(ModbusConfigInvalidAccessError):
        ModbusProtocolPortConfig(
            host="localhost",
            registers={
                "x": ModbusRegisterConfig(
                    address=0,
                    datatype=ModbusDatatype.INT16,
                    access="readwrite",  # type: ignore[arg-type]
                )
            },
        )


@pytest.mark.parametrize("fc", [0, 1, 2, 5, 7, 15, 17, 99])
def test_register_rejects_function_codes_outside_allowlist(fc: int) -> None:
    with pytest.raises(ModbusConfigInvalidFunctionCodeError):
        ModbusProtocolPortConfig(
            host="localhost",
            registers={
                "x": ModbusRegisterConfig(
                    address=0,
                    datatype=ModbusDatatype.UINT16,
                    access="read" if fc in (1, 2) else "write",
                    function_code=fc,
                )
            },
        )


def test_register_rejects_fc03_with_write_access() -> None:
    with pytest.raises(ModbusConfigFunctionCodeAccessMismatchError):
        ModbusProtocolPortConfig(
            host="localhost",
            registers={
                "x": ModbusRegisterConfig(
                    address=0,
                    datatype=ModbusDatatype.UINT16,
                    access="write",
                    function_code=3,  # FC03 ist read
                )
            },
        )


def test_register_rejects_fc06_with_read_access() -> None:
    with pytest.raises(ModbusConfigFunctionCodeAccessMismatchError):
        ModbusProtocolPortConfig(
            host="localhost",
            registers={
                "x": ModbusRegisterConfig(
                    address=0,
                    datatype=ModbusDatatype.UINT16,
                    access="read",
                    function_code=6,  # FC06 ist write
                )
            },
        )


@pytest.mark.parametrize("unit_id", [0, 248, 1000])
def test_register_rejects_invalid_override_unit_id(unit_id: int) -> None:
    with pytest.raises(ModbusConfigInvalidUnitIdError):
        ModbusProtocolPortConfig(
            host="localhost",
            registers={
                "x": ModbusRegisterConfig(
                    address=0,
                    datatype=ModbusDatatype.UINT16,
                    access="read",
                    unit_id=unit_id,
                )
            },
        )


@pytest.mark.parametrize(
    ("datatype", "expected_count"),
    [
        (ModbusDatatype.INT16, 1),
        (ModbusDatatype.UINT16, 1),
        (ModbusDatatype.INT32, 2),
        (ModbusDatatype.UINT32, 2),
        (ModbusDatatype.FLOAT32, 2),
    ],
)
def test_datatype_register_count(datatype: ModbusDatatype, expected_count: int) -> None:
    assert datatype_register_count(datatype) == expected_count


def test_resolve_function_code_defaults_to_fc03_for_read() -> None:
    reg = ModbusRegisterConfig(address=0, datatype=ModbusDatatype.UINT16, access="read")
    assert resolve_function_code(reg) == 3


def test_resolve_function_code_defaults_to_fc06_for_single_register_write() -> None:
    reg = ModbusRegisterConfig(address=0, datatype=ModbusDatatype.UINT16, access="write")
    assert resolve_function_code(reg) == 6


def test_resolve_function_code_defaults_to_fc10_for_multi_register_write() -> None:
    reg = ModbusRegisterConfig(address=0, datatype=ModbusDatatype.INT32, access="write")
    assert resolve_function_code(reg) == 16


def test_resolve_function_code_respects_override() -> None:
    reg = ModbusRegisterConfig(
        address=0,
        datatype=ModbusDatatype.UINT16,
        access="read",
        function_code=4,
    )
    assert resolve_function_code(reg) == 4


def test_resolve_unit_id_uses_register_override_when_set() -> None:
    reg = ModbusRegisterConfig(address=0, datatype=ModbusDatatype.UINT16, access="read", unit_id=42)
    assert resolve_unit_id(reg, parent_unit_id=1) == 42


def test_resolve_unit_id_falls_back_to_parent_when_unset() -> None:
    reg = ModbusRegisterConfig(address=0, datatype=ModbusDatatype.UINT16, access="read")
    assert resolve_unit_id(reg, parent_unit_id=7) == 7
