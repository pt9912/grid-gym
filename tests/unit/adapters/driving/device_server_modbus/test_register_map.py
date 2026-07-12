"""Tests fuer `encode_float32` + `RegisterMap` (Field-Server Pull-Seite,
ADR 0075 §2.2; Encode-Oracle `spec/protocol_profiles.md`).

Reiner Kern (pymodbus-frei): float32-Encode gegen das definierte Oracle +
on-demand-Register-Berechnung aus der Current-Value-Projektion.
"""

from __future__ import annotations

import struct
from decimal import Decimal

import pytest

from grid_gym.adapters.driving._field_current_value import CurrentValueProjection
from grid_gym.adapters.driving.device_server_modbus._config import (
    ModbusServerConfig,
    RegisterMapping,
)
from grid_gym.adapters.driving.device_server_modbus._register_map import (
    RegisterMap,
    encode_float32,
)
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.domain.tick_result import TickResult


def _point(
    *,
    device_id: str = "meter-1",
    metric: str = "voltage_v",
    value: str = "230.5",
    quality: Quality = Quality.VALID,
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


def _projection(*points: TelemetryPoint) -> CurrentValueProjection:
    proj = CurrentValueProjection()
    proj.update_from_tick(
        TickResult(
            tick=0,
            simulation_time=0,
            popped_events=(),
            emitted_telemetry=points,
            emitted_alarms=(),
        )
    )
    return proj


def _config(*mappings: RegisterMapping) -> ModbusServerConfig:
    return ModbusServerConfig(bind_host="127.0.0.1", bind_port=5020, register_map=mappings)


# --- encode_float32: exakt das dokumentierte Oracle -------------------------


@pytest.mark.parametrize("raw", ["230.5", "0", "-12.25", "1000000.0"])
def test_encode_matches_struct_oracle(raw: str) -> None:
    expected = struct.unpack(">HH", struct.pack(">f", float(Decimal(raw))))
    assert encode_float32(Decimal(raw)) == expected


def test_encode_round_trips_through_float32() -> None:
    high, low = encode_float32(Decimal("230.5"))
    decoded = struct.unpack(">f", struct.pack(">HH", high, low))[0]
    assert decoded == pytest.approx(230.5)


# --- RegisterMap: Holding-Register (FC03) -----------------------------------


def test_holding_register_high_and_low_word() -> None:
    reg_map = RegisterMap(
        _config(RegisterMapping("meter-1", "voltage_v", 0)), _projection(_point())
    )
    high, low = encode_float32(Decimal("230.5"))
    assert reg_map.holding_register(0) == high  # High-Word zuerst
    assert reg_map.holding_register(1) == low


def test_holding_registers_span_matches_words() -> None:
    reg_map = RegisterMap(
        _config(RegisterMapping("meter-1", "voltage_v", 0)), _projection(_point())
    )
    assert reg_map.holding_registers(0, 2) == list(encode_float32(Decimal("230.5")))


def test_holding_register_unmapped_address_is_zero() -> None:
    reg_map = RegisterMap(
        _config(RegisterMapping("meter-1", "voltage_v", 0)), _projection(_point())
    )
    assert reg_map.holding_register(99) == 0


def test_holding_register_missing_value_is_zero() -> None:
    # Mapping existiert, aber die Projektion hat fuer das Paar keinen Wert.
    reg_map = RegisterMap(
        _config(RegisterMapping("meter-X", "voltage_v", 0)), _projection(_point())
    )
    assert reg_map.holding_register(0) == 0
    assert reg_map.holding_register(1) == 0


def test_holding_registers_reflect_live_projection_update() -> None:
    proj = _projection(_point(value="1.0"))
    reg_map = RegisterMap(_config(RegisterMapping("meter-1", "voltage_v", 0)), proj)
    proj.update_from_tick(
        TickResult(
            tick=1,
            simulation_time=1,
            popped_events=(),
            emitted_telemetry=(_point(value="2.0"),),
            emitted_alarms=(),
        )
    )
    # On-demand: der Poll sieht den fortgeschriebenen Wert (keine Materialisierung).
    assert reg_map.holding_registers(0, 2) == list(encode_float32(Decimal("2.0")))


# --- RegisterMap: Discrete-Input (FC02, Quality-Flag) -----------------------


def test_discrete_input_valid_is_true() -> None:
    reg_map = RegisterMap(
        _config(RegisterMapping("meter-1", "voltage_v", 0)), _projection(_point())
    )
    assert reg_map.discrete_input(0) is True


@pytest.mark.parametrize("quality", [Quality.STALE, Quality.NAN, Quality.INVALID])
def test_discrete_input_non_valid_is_false(quality: Quality) -> None:
    reg_map = RegisterMap(
        _config(RegisterMapping("meter-1", "voltage_v", 0)),
        _projection(_point(quality=quality)),
    )
    assert reg_map.discrete_input(0) is False


def test_discrete_input_missing_value_is_false() -> None:
    reg_map = RegisterMap(
        _config(RegisterMapping("meter-X", "voltage_v", 0)), _projection(_point())
    )
    assert reg_map.discrete_input(0) is False


def test_discrete_inputs_ordinal_index_per_mapping() -> None:
    reg_map = RegisterMap(
        _config(
            RegisterMapping("meter-1", "voltage_v", 0),
            RegisterMapping("meter-2", "power_w", 2),
        ),
        _projection(
            _point(),  # meter-1 VALID → di[0] True
            _point(device_id="meter-2", metric="power_w", quality=Quality.STALE),  # di[1] False
        ),
    )
    assert reg_map.discrete_inputs(0, 2) == [True, False]
