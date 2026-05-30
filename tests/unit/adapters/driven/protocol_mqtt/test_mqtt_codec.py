"""Encode/decode-Roundtrip + Fehlerfaelle fuer den MQTT-Codec
(M4 Welle 2, ADR 0031 §2.2).
"""

from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType

import pytest

from grid_gym.adapters.driven.protocol_mqtt import (
    MqttCodecInvalidEnumError,
    MqttCodecJsonDecodeError,
    MqttCodecMissingFieldError,
    MqttCodecPayloadShapeError,
    decode_command,
    decode_telemetry,
    encode_command,
    encode_telemetry,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint


def _sample_telemetry_point() -> TelemetryPoint:
    return TelemetryPoint(
        run_id="run-001",
        tick=42,
        simulation_time=4200,
        device_id="battery.bess01",
        metric="power_kw",
        value=Decimal("12.345"),
        unit="kW",
        quality=Quality.VALID,
        source="battery.bess01",
        sequence=7,
    )


def _sample_command() -> Command:
    return Command(
        command_id="cmd-001",
        simulation_time=4200,
        target_device_id="battery.bess01",
        type="set_power_setpoint",
        payload=MappingProxyType({"setpoint_kw": Decimal("10.0")}),
        validation_status="validated",
        result=CommandResult.ACCEPTED,
    )


def test_encode_telemetry_emits_canonical_bytes() -> None:
    point = _sample_telemetry_point()
    encoded = encode_telemetry(point)
    assert isinstance(encoded, bytes)
    # Canonical JSON: sortierte Keys, kein Whitespace.
    assert b'"device_id":"battery.bess01"' in encoded
    assert b'"value":12.345' in encoded
    # Decimal-Fixed-Point statt Float-Hex.
    assert b"e" not in encoded.lower().split(b'"value":')[1].split(b",")[0]


def test_encode_telemetry_is_deterministic() -> None:
    point = _sample_telemetry_point()
    assert encode_telemetry(point) == encode_telemetry(point)


def test_decode_telemetry_roundtrip() -> None:
    point = _sample_telemetry_point()
    restored = decode_telemetry(encode_telemetry(point))
    assert restored == point
    assert isinstance(restored.value, Decimal)
    assert restored.value == Decimal("12.345")


def test_decode_telemetry_rejects_non_json_bytes() -> None:
    with pytest.raises(MqttCodecJsonDecodeError):
        decode_telemetry(b"not-json")


def test_decode_telemetry_rejects_array_top_level() -> None:
    with pytest.raises(MqttCodecPayloadShapeError) as exc_info:
        decode_telemetry(b'["arrays-are-not-objects"]')
    assert exc_info.value.observed_type == "list"


def test_decode_telemetry_missing_field_raises() -> None:
    with pytest.raises(MqttCodecMissingFieldError) as exc_info:
        decode_telemetry(b'{"run_id":"x"}')
    # First missing field that's checked
    assert exc_info.value.field_name in (
        "tick",
        "simulation_time",
        "device_id",
        "metric",
        "value",
        "unit",
        "quality",
        "source",
        "sequence",
    )


def test_decode_telemetry_invalid_quality_enum_raises() -> None:
    point = _sample_telemetry_point()
    encoded = encode_telemetry(point)
    tampered = encoded.replace(b'"quality":"valid"', b'"quality":"unknown_quality"')
    with pytest.raises(MqttCodecInvalidEnumError) as exc_info:
        decode_telemetry(tampered)
    assert exc_info.value.field_name == "quality"


def test_encode_command_emits_canonical_bytes() -> None:
    command = _sample_command()
    encoded = encode_command(command)
    assert isinstance(encoded, bytes)
    assert b'"command_id":"cmd-001"' in encoded
    assert b'"result":"accepted"' in encoded


def test_decode_command_roundtrip() -> None:
    command = _sample_command()
    restored = decode_command(encode_command(command))
    assert restored.command_id == command.command_id
    assert restored.target_device_id == command.target_device_id
    assert restored.type == command.type
    assert restored.validation_status == command.validation_status
    assert restored.result == command.result
    assert dict(restored.payload) == dict(command.payload)


def test_decode_command_invalid_result_enum_raises() -> None:
    command = _sample_command()
    encoded = encode_command(command)
    tampered = encoded.replace(b'"result":"accepted"', b'"result":"maybe"')
    with pytest.raises(MqttCodecInvalidEnumError) as exc_info:
        decode_command(tampered)
    assert exc_info.value.field_name == "result"


def test_decode_telemetry_value_preserves_decimal_precision() -> None:
    point = _sample_telemetry_point()
    # `1.230000` waere bei float-Decode "1.23"; mit parse_float=Decimal
    # bleibt die exakte Repraesentation erhalten.
    high_precision = TelemetryPoint(
        run_id=point.run_id,
        tick=point.tick,
        simulation_time=point.simulation_time,
        device_id=point.device_id,
        metric=point.metric,
        value=Decimal("12.345678"),
        unit=point.unit,
        quality=point.quality,
        source=point.source,
        sequence=point.sequence,
    )
    restored = decode_telemetry(encode_telemetry(high_precision))
    assert restored.value == Decimal("12.345678")
