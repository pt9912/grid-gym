"""Tests fuer den reinen Inbound-Write-Decoder (`_write_map`, ADR 0076 §2.1).

pymodbus-frei: `decode_float32` (Decode-Oracle, Umkehr von `encode_float32`) +
`InboundWriteDecoder` (Write-Fenster → `DecodedInboundWrite`). Die Funktions-Code-
Filterung + Enqueue sitzt im Adapter (Write-E2E), nicht hier.
"""

from __future__ import annotations

import struct
from decimal import Decimal

import pytest

from grid_gym.adapters.driving.device_server_modbus._config import (
    ModbusServerConfig,
    RegisterMapping,
    WritableRegisterMapping,
)
from grid_gym.adapters.driving.device_server_modbus._register_map import encode_float32
from grid_gym.adapters.driving.device_server_modbus._write_map import (
    DecodedInboundWrite,
    InboundWriteDecoder,
    decode_float32,
)


def _config(*write_map: WritableRegisterMapping) -> ModbusServerConfig:
    return ModbusServerConfig(
        bind_host="127.0.0.1",
        bind_port=5020,
        register_map=(RegisterMapping("meter-1", "voltage_v", 100),),
        write_map=write_map,
    )


def _words(value: str) -> list[int]:
    """`float32`-Registerpaar `[high, low]` fuer einen Decimal-String."""
    return list(encode_float32(Decimal(value)))


# --- decode_float32 (Decode-Oracle) ----------------------------------------


# "0.1"/"-0.333" sind in float32 **nicht** exakt darstellbar → decode liefert den
# vollpraezisen float32-Wert (nicht-rund); der Test pinnt, dass auch dieser Edge
# deterministisch + byte-stabil ist (Review-Fund Slice 075 LOW-3).
@pytest.mark.parametrize("raw", ["42.5", "-12.5", "0", "230.5", "1000000.0", "0.1", "-0.333"])
def test_decode_reencode_roundtrip_is_stable(raw: str) -> None:
    # decode(encode(x)) muss byte-stabil zurueck-encodieren (float32 ist idempotent
    # quantisiert): encode(decode(encode(x))) == encode(x).
    words = encode_float32(Decimal(raw))
    decoded = decode_float32(*words)
    assert decoded is not None
    assert encode_float32(decoded) == words
    # ...und wertgleich zur float32-Quantisierung des Eingangs (Decimal-Vergleich,
    # kein Float-Equality).
    quantized = struct.unpack(">f", struct.pack(">f", float(raw)))[0]
    assert decoded == Decimal(str(quantized))


def test_decode_nan_bitpattern_is_none() -> None:
    # 0x7FC0_0000 == quiet NaN → nicht-endlich → verworfen (None), damit kein
    # Decimal('NaN') in einen Command wandert (ADR 0076-Haerte).
    assert decode_float32(0x7FC0, 0x0000) is None


def test_decode_inf_bitpattern_is_none() -> None:
    # 0x7F80_0000 == +inf → verworfen.
    assert decode_float32(0x7F80, 0x0000) is None


# --- InboundWriteDecoder ----------------------------------------------------


def test_no_write_map_has_no_writable() -> None:
    decoder = InboundWriteDecoder(_config())
    assert decoder.has_writable is False
    assert decoder.decode(0, _words("42.5")) == ()


def test_full_window_write_decodes_to_command_seed() -> None:
    decoder = InboundWriteDecoder(_config(WritableRegisterMapping(10, "battery-1", "set_power_kw")))
    decoded = decoder.decode(10, _words("42.5"))
    assert decoded == (DecodedInboundWrite("battery-1", "set_power_kw", Decimal("42.5")),)


def test_partial_window_write_is_skipped() -> None:
    # Nur das High-Word geschrieben (FC06-Einzelregister) → kein vollstaendiger
    # float32 → uebersprungen.
    decoder = InboundWriteDecoder(_config(WritableRegisterMapping(10, "battery-1", "set_power_kw")))
    assert decoder.decode(10, [_words("42.5")[0]]) == ()


def test_write_to_unmapped_address_is_empty() -> None:
    decoder = InboundWriteDecoder(_config(WritableRegisterMapping(10, "battery-1", "set_power_kw")))
    assert decoder.decode(20, _words("42.5")) == ()


def test_write_spanning_multiple_windows_is_ordered_by_address() -> None:
    # Ein Block-Write [10..13] ueberdeckt zwei Sollwert-Fenster → deterministische
    # Reihenfolge nach Adresse (Same-Request-Multiplizitaet).
    decoder = InboundWriteDecoder(
        _config(
            WritableRegisterMapping(12, "battery-2", "set_power_kw"),
            WritableRegisterMapping(10, "battery-1", "set_power_kw"),
        )
    )
    decoded = decoder.decode(10, _words("42.5") + _words("-7.0"))
    assert decoded == (
        DecodedInboundWrite("battery-1", "set_power_kw", Decimal("42.5")),
        DecodedInboundWrite("battery-2", "set_power_kw", Decimal("-7.0")),
    )


def test_nan_write_is_skipped() -> None:
    decoder = InboundWriteDecoder(_config(WritableRegisterMapping(10, "battery-1", "set_power_kw")))
    assert decoder.decode(10, [0x7FC0, 0x0000]) == ()
