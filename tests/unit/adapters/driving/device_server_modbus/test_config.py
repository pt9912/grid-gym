"""Tests fuer `ModbusServerConfig` (Field-Server Pull-Seite, ADR 0075 §2.1).

Fail-fast-Validierung im Konstruktor (typed `ModbusServerConfigError`-Familie).
"""

from __future__ import annotations

import pytest

from grid_gym.adapters.driving.device_server_modbus._config import (
    ModbusServerConfig,
    ModbusServerConfigEmptyFieldError,
    ModbusServerConfigEmptyRegisterMapError,
    ModbusServerConfigInvalidAddressError,
    ModbusServerConfigInvalidPortError,
    ModbusServerConfigInvalidUnitIdError,
    ModbusServerConfigRegisterOverlapError,
    RegisterMapping,
)


def _mapping(address: int = 0) -> RegisterMapping:
    return RegisterMapping(device_id="meter-1", metric="voltage_v", address=address)


def test_valid_config_holds_fields() -> None:
    config = ModbusServerConfig(
        bind_host="0.0.0.0",
        bind_port=5020,
        register_map=(_mapping(0), RegisterMapping("meter-2", "power_w", 2)),
        unit_id=1,
    )
    assert config.bind_port == 5020
    assert len(config.register_map) == 2


def test_empty_bind_host_rejected() -> None:
    with pytest.raises(ModbusServerConfigEmptyFieldError):
        ModbusServerConfig(bind_host="", bind_port=5020, register_map=(_mapping(),))


@pytest.mark.parametrize("port", [0, 65536, -1])
def test_port_out_of_range_rejected(port: int) -> None:
    with pytest.raises(ModbusServerConfigInvalidPortError):
        ModbusServerConfig(bind_host="0.0.0.0", bind_port=port, register_map=(_mapping(),))


@pytest.mark.parametrize("unit_id", [-1, 0, 248])
def test_unit_id_out_of_range_rejected(unit_id: int) -> None:
    # 0 = Broadcast (SimDevice-Catch-all) → als konkrete Slave-Adresse verboten.
    with pytest.raises(ModbusServerConfigInvalidUnitIdError):
        ModbusServerConfig(
            bind_host="0.0.0.0",
            bind_port=5020,
            register_map=(_mapping(),),
            unit_id=unit_id,
        )


@pytest.mark.parametrize("address", [-1, 65535, 70000])
def test_register_address_out_of_range_rejected(address: int) -> None:
    # address+1 (zweites float32-Register) muss noch in [0, 65535] passen → max 65534.
    with pytest.raises(ModbusServerConfigInvalidAddressError):
        ModbusServerConfig(
            bind_host="0.0.0.0",
            bind_port=5020,
            register_map=(RegisterMapping("meter-1", "voltage_v", address),),
        )


def test_highest_valid_register_address_accepted() -> None:
    config = ModbusServerConfig(
        bind_host="0.0.0.0",
        bind_port=5020,
        register_map=(RegisterMapping("meter-1", "voltage_v", 65534),),
    )
    assert config.register_map[0].address == 65534


def test_empty_register_map_rejected() -> None:
    with pytest.raises(ModbusServerConfigEmptyRegisterMapError):
        ModbusServerConfig(bind_host="0.0.0.0", bind_port=5020, register_map=())


def test_overlapping_registers_rejected() -> None:
    # float32 belegt 2 Register: address=0 → {0,1}, address=1 → {1,2} → Ueberlapp bei 1.
    with pytest.raises(ModbusServerConfigRegisterOverlapError):
        ModbusServerConfig(
            bind_host="0.0.0.0",
            bind_port=5020,
            register_map=(_mapping(0), RegisterMapping("meter-2", "power_w", 1)),
        )


def test_adjacent_registers_do_not_overlap() -> None:
    # address=0 → {0,1}, address=2 → {2,3}: lueckenlos benachbart, kein Ueberlapp.
    config = ModbusServerConfig(
        bind_host="0.0.0.0",
        bind_port=5020,
        register_map=(_mapping(0), RegisterMapping("meter-2", "power_w", 2)),
    )
    assert len(config.register_map) == 2
