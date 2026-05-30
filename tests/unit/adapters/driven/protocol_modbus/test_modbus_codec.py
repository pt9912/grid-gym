"""Encode/Decode-Roundtrip + Fehlerfaelle fuer den Modbus-Codec
(M4 Welle 3, ADR 0032 §2.2).

Inkl. `hypothesis`-Property-Tests fuer die 5 Datatypes mit
beiden Byte-Order-Varianten + Word-Swap-Matrix.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from grid_gym.adapters.driven.protocol_modbus import (
    ModbusCodecNonFiniteError,
    ModbusCodecOutOfRangeError,
    ModbusCodecRegisterCountMismatchError,
    ModbusDatatype,
    decode_registers_to_value,
    encode_value_to_registers,
)


# ---------------------------------------------------------------------------
# Hand-curated unit tests
# ---------------------------------------------------------------------------


def test_uint16_roundtrip_big_endian() -> None:
    encoded = encode_value_to_registers(42, ModbusDatatype.UINT16, "big_endian", word_swap=False)
    assert encoded == (42,)
    decoded = decode_registers_to_value(
        encoded, ModbusDatatype.UINT16, "big_endian", word_swap=False
    )
    assert decoded == Decimal(42)


def test_int16_roundtrip_negative_value() -> None:
    encoded = encode_value_to_registers(-1, ModbusDatatype.INT16, "big_endian", word_swap=False)
    # -1 als int16 in big-endian -> 0xFFFF
    assert encoded == (0xFFFF,)
    decoded = decode_registers_to_value(
        encoded, ModbusDatatype.INT16, "big_endian", word_swap=False
    )
    assert decoded == Decimal(-1)


def test_int32_roundtrip_big_endian_no_word_swap() -> None:
    encoded = encode_value_to_registers(
        0x12345678, ModbusDatatype.INT32, "big_endian", word_swap=False
    )
    assert encoded == (0x1234, 0x5678)
    decoded = decode_registers_to_value(
        encoded, ModbusDatatype.INT32, "big_endian", word_swap=False
    )
    assert decoded == Decimal(0x12345678)


def test_int32_word_swap_rotates_register_pair() -> None:
    encoded_no_swap = encode_value_to_registers(
        0x12345678, ModbusDatatype.INT32, "big_endian", word_swap=False
    )
    encoded_swapped = encode_value_to_registers(
        0x12345678, ModbusDatatype.INT32, "big_endian", word_swap=True
    )
    assert encoded_swapped == (encoded_no_swap[1], encoded_no_swap[0])


def test_float32_roundtrip_preserves_value() -> None:
    encoded = encode_value_to_registers(3.14, ModbusDatatype.FLOAT32, "big_endian", word_swap=False)
    assert len(encoded) == 2
    decoded = decode_registers_to_value(
        encoded, ModbusDatatype.FLOAT32, "big_endian", word_swap=False
    )
    # float32 ist 7-stellig praezise — 3.14 roundtripped exakt im
    # repr().
    assert abs(decoded - Decimal("3.14")) < Decimal("0.0001")


def test_uint16_rejects_negative_value() -> None:
    with pytest.raises(ModbusCodecOutOfRangeError):
        encode_value_to_registers(-1, ModbusDatatype.UINT16, "big_endian", word_swap=False)


def test_int16_rejects_out_of_range() -> None:
    with pytest.raises(ModbusCodecOutOfRangeError) as exc_info:
        encode_value_to_registers(70000, ModbusDatatype.INT16, "big_endian", word_swap=False)
    assert exc_info.value.datatype is ModbusDatatype.INT16


def test_float32_rejects_nan() -> None:
    with pytest.raises(ModbusCodecNonFiniteError):
        encode_value_to_registers(
            float("nan"), ModbusDatatype.FLOAT32, "big_endian", word_swap=False
        )


def test_float32_rejects_infinity() -> None:
    with pytest.raises(ModbusCodecNonFiniteError):
        encode_value_to_registers(
            float("inf"), ModbusDatatype.FLOAT32, "big_endian", word_swap=False
        )


def test_decode_rejects_register_count_mismatch_int16() -> None:
    with pytest.raises(ModbusCodecRegisterCountMismatchError) as exc_info:
        decode_registers_to_value((1, 2), ModbusDatatype.INT16, "big_endian", word_swap=False)
    assert exc_info.value.datatype is ModbusDatatype.INT16
    assert exc_info.value.expected == 1
    assert exc_info.value.actual == 2


def test_decode_rejects_register_count_mismatch_int32() -> None:
    with pytest.raises(ModbusCodecRegisterCountMismatchError):
        decode_registers_to_value((1,), ModbusDatatype.INT32, "big_endian", word_swap=False)


def test_uint32_roundtrip_big_endian() -> None:
    encoded = encode_value_to_registers(
        0xAABBCCDD, ModbusDatatype.UINT32, "big_endian", word_swap=False
    )
    assert encoded == (0xAABB, 0xCCDD)
    decoded = decode_registers_to_value(
        encoded, ModbusDatatype.UINT32, "big_endian", word_swap=False
    )
    assert decoded == Decimal(0xAABBCCDD)


# ---------------------------------------------------------------------------
# hypothesis-Property-Tests (5 Datatypes x 2 Byte-Orders x 2 Word-Swap)
# ---------------------------------------------------------------------------


@given(value=st.integers(min_value=-32768, max_value=32767))
@pytest.mark.parametrize("byte_order", ["big_endian", "little_endian"])
def test_property_int16_roundtrip_preserves_value(value: int, byte_order: str) -> None:
    encoded = encode_value_to_registers(value, ModbusDatatype.INT16, byte_order, word_swap=False)
    decoded = decode_registers_to_value(encoded, ModbusDatatype.INT16, byte_order, word_swap=False)
    assert decoded == Decimal(value)


@given(value=st.integers(min_value=0, max_value=65535))
@pytest.mark.parametrize("byte_order", ["big_endian", "little_endian"])
def test_property_uint16_roundtrip_preserves_value(value: int, byte_order: str) -> None:
    encoded = encode_value_to_registers(value, ModbusDatatype.UINT16, byte_order, word_swap=False)
    decoded = decode_registers_to_value(encoded, ModbusDatatype.UINT16, byte_order, word_swap=False)
    assert decoded == Decimal(value)


@given(value=st.integers(min_value=-(2**31), max_value=2**31 - 1))
@pytest.mark.parametrize("byte_order", ["big_endian", "little_endian"])
@pytest.mark.parametrize("word_swap", [False, True])
def test_property_int32_roundtrip_with_word_swap_matrix(
    value: int, byte_order: str, word_swap: bool
) -> None:
    encoded = encode_value_to_registers(
        value, ModbusDatatype.INT32, byte_order, word_swap=word_swap
    )
    decoded = decode_registers_to_value(
        encoded, ModbusDatatype.INT32, byte_order, word_swap=word_swap
    )
    assert decoded == Decimal(value)


@given(value=st.integers(min_value=0, max_value=2**32 - 1))
@pytest.mark.parametrize("byte_order", ["big_endian", "little_endian"])
@pytest.mark.parametrize("word_swap", [False, True])
def test_property_uint32_roundtrip_with_word_swap_matrix(
    value: int, byte_order: str, word_swap: bool
) -> None:
    encoded = encode_value_to_registers(
        value, ModbusDatatype.UINT32, byte_order, word_swap=word_swap
    )
    decoded = decode_registers_to_value(
        encoded, ModbusDatatype.UINT32, byte_order, word_swap=word_swap
    )
    assert decoded == Decimal(value)


@given(
    value=st.floats(
        min_value=-1e6,
        max_value=1e6,
        allow_nan=False,
        allow_infinity=False,
        width=32,
    )
)
@pytest.mark.parametrize("byte_order", ["big_endian", "little_endian"])
@pytest.mark.parametrize("word_swap", [False, True])
def test_property_float32_roundtrip_with_word_swap_matrix(
    value: float, byte_order: str, word_swap: bool
) -> None:
    encoded = encode_value_to_registers(
        value, ModbusDatatype.FLOAT32, byte_order, word_swap=word_swap
    )
    decoded = decode_registers_to_value(
        encoded, ModbusDatatype.FLOAT32, byte_order, word_swap=word_swap
    )
    # float32 hat ~7 Stellen Praezision; Roundtrip-Toleranz analog.
    assert abs(float(decoded) - value) < max(abs(value), 1.0) * 1e-5
