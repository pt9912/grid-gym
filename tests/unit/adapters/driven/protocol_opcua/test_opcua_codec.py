"""Codec-Roundtrip-Tests fuer den OPC-UA-Adapter
(M4 Welle 4, ADR 0033 §2.3).

Deckt:

- Encode `Python-Native -> ua.Variant` pro Welle-4-Datatype.
- Decode `ua.Variant -> Python-Native`.
- Out-of-Range-Errors (Integer-Datatypes).
- NaN/Infinity-Errors (Float/Double).
- Payload-Type-Errors (z. B. `bool` zu `Int32`).
- Hypothesis-Property-Tests fuer Integer-Roundtrip.
"""

from __future__ import annotations

import math
from decimal import Decimal

import pytest
from asyncua import ua
from hypothesis import given, strategies as st

from grid_gym.adapters.driven.protocol_opcua import (
    OpcuaCodecDecodeError,
    OpcuaCodecNonFiniteError,
    OpcuaCodecOutOfRangeError,
    OpcuaCodecPayloadTypeError,
    OpcuaDatatype,
    decode_variant_to_value,
    encode_value_to_variant,
)


# ---------------------------------------------------------------------------
# Encode
# ---------------------------------------------------------------------------


def test_encode_boolean() -> None:
    variant = encode_value_to_variant(True, OpcuaDatatype.BOOLEAN)
    assert variant.Value is True
    assert variant.VariantType is ua.VariantType.Boolean


def test_encode_int16() -> None:
    variant = encode_value_to_variant(-1000, OpcuaDatatype.INT16)
    assert variant.Value == -1000
    assert variant.VariantType is ua.VariantType.Int16


def test_encode_uint32() -> None:
    variant = encode_value_to_variant(123456, OpcuaDatatype.UINT32)
    assert variant.Value == 123456
    assert variant.VariantType is ua.VariantType.UInt32


def test_encode_float() -> None:
    variant = encode_value_to_variant(Decimal("3.14"), OpcuaDatatype.FLOAT)
    assert variant.VariantType is ua.VariantType.Float
    assert variant.Value == pytest.approx(3.14)


def test_encode_double() -> None:
    variant = encode_value_to_variant(2.71828, OpcuaDatatype.DOUBLE)
    assert variant.VariantType is ua.VariantType.Double
    assert variant.Value == pytest.approx(2.71828)


def test_encode_string() -> None:
    variant = encode_value_to_variant("hello", OpcuaDatatype.STRING)
    assert variant.Value == "hello"
    assert variant.VariantType is ua.VariantType.String


def test_encode_int_out_of_range() -> None:
    with pytest.raises(OpcuaCodecOutOfRangeError) as exc_info:
        encode_value_to_variant(2**20, OpcuaDatatype.INT16)
    assert exc_info.value.datatype is OpcuaDatatype.INT16


def test_encode_float_nan_rejected() -> None:
    with pytest.raises(OpcuaCodecNonFiniteError):
        encode_value_to_variant(float("nan"), OpcuaDatatype.FLOAT)


def test_encode_float_infinity_rejected() -> None:
    with pytest.raises(OpcuaCodecNonFiniteError):
        encode_value_to_variant(float("inf"), OpcuaDatatype.DOUBLE)


def test_encode_bool_to_int_rejected() -> None:
    with pytest.raises(OpcuaCodecPayloadTypeError):
        encode_value_to_variant(True, OpcuaDatatype.INT32)


def test_encode_string_to_int_rejected() -> None:
    with pytest.raises(OpcuaCodecPayloadTypeError):
        encode_value_to_variant("oops", OpcuaDatatype.INT32)


# ---------------------------------------------------------------------------
# Decode
# ---------------------------------------------------------------------------


def test_decode_boolean() -> None:
    variant = ua.Variant(True, ua.VariantType.Boolean)
    assert decode_variant_to_value(variant, OpcuaDatatype.BOOLEAN) is True


def test_decode_int32() -> None:
    variant = ua.Variant(-42, ua.VariantType.Int32)
    assert decode_variant_to_value(variant, OpcuaDatatype.INT32) == -42


def test_decode_float_returns_decimal_via_repr() -> None:
    variant = ua.Variant(3.14, ua.VariantType.Float)
    result = decode_variant_to_value(variant, OpcuaDatatype.FLOAT)
    assert isinstance(result, Decimal)
    # Decimal via repr bewahrt Float-Praezisions-Konvention (ADR 0032 §2.2).
    assert float(result) == pytest.approx(3.14)


def test_decode_double_returns_decimal_via_repr() -> None:
    variant = ua.Variant(2.71828, ua.VariantType.Double)
    result = decode_variant_to_value(variant, OpcuaDatatype.DOUBLE)
    assert isinstance(result, Decimal)
    assert float(result) == pytest.approx(2.71828)


def test_decode_string() -> None:
    variant = ua.Variant("hello", ua.VariantType.String)
    assert decode_variant_to_value(variant, OpcuaDatatype.STRING) == "hello"


def test_decode_none_value_rejected() -> None:
    variant = ua.Variant(None)
    with pytest.raises(OpcuaCodecDecodeError):
        decode_variant_to_value(variant, OpcuaDatatype.INT32)


def test_decode_type_mismatch_rejected() -> None:
    # String-Variant gegen Int32-Datatype.
    variant = ua.Variant("oops", ua.VariantType.String)
    with pytest.raises(OpcuaCodecDecodeError):
        decode_variant_to_value(variant, OpcuaDatatype.INT32)


def test_decode_bool_against_int_rejected() -> None:
    # Bool ist `int`-Subclass — wir wollen ihn aber NICHT als Int akzeptieren.
    variant = ua.Variant(True, ua.VariantType.Boolean)
    with pytest.raises(OpcuaCodecDecodeError):
        decode_variant_to_value(variant, OpcuaDatatype.INT32)


def test_decode_int_against_boolean_rejected() -> None:
    # Int-Variant gegen Boolean-Datatype.
    variant = ua.Variant(42, ua.VariantType.Int32)
    with pytest.raises(OpcuaCodecDecodeError):
        decode_variant_to_value(variant, OpcuaDatatype.BOOLEAN)


def test_decode_int_against_string_rejected() -> None:
    variant = ua.Variant(42, ua.VariantType.Int32)
    with pytest.raises(OpcuaCodecDecodeError):
        decode_variant_to_value(variant, OpcuaDatatype.STRING)


def test_decode_string_against_float_rejected() -> None:
    variant = ua.Variant("oops", ua.VariantType.String)
    with pytest.raises(OpcuaCodecDecodeError):
        decode_variant_to_value(variant, OpcuaDatatype.FLOAT)


def test_decode_bool_against_float_rejected() -> None:
    variant = ua.Variant(True, ua.VariantType.Boolean)
    with pytest.raises(OpcuaCodecDecodeError):
        decode_variant_to_value(variant, OpcuaDatatype.FLOAT)


# ---------------------------------------------------------------------------
# Encode coerce-helper branches
# ---------------------------------------------------------------------------


def test_encode_boolean_rejects_int() -> None:
    with pytest.raises(OpcuaCodecPayloadTypeError):
        encode_value_to_variant(1, OpcuaDatatype.BOOLEAN)


def test_encode_string_rejects_int() -> None:
    with pytest.raises(OpcuaCodecPayloadTypeError):
        encode_value_to_variant(42, OpcuaDatatype.STRING)


def test_encode_int_accepts_decimal() -> None:
    variant = encode_value_to_variant(Decimal(100), OpcuaDatatype.INT32)
    assert variant.Value == 100
    assert variant.VariantType is ua.VariantType.Int32


def test_encode_int_rejects_unsupported_type() -> None:
    with pytest.raises(OpcuaCodecPayloadTypeError):
        encode_value_to_variant([1, 2, 3], OpcuaDatatype.INT32)  # type: ignore[arg-type]


def test_encode_float_rejects_unsupported_type() -> None:
    with pytest.raises(OpcuaCodecPayloadTypeError):
        encode_value_to_variant({"x": 1}, OpcuaDatatype.FLOAT)  # type: ignore[arg-type]


def test_encode_float_accepts_int() -> None:
    variant = encode_value_to_variant(42, OpcuaDatatype.FLOAT)
    assert variant.Value == pytest.approx(42.0)


# ---------------------------------------------------------------------------
# Roundtrip (Hypothesis-Property-Tests)
# ---------------------------------------------------------------------------


@given(value=st.integers(min_value=-(2**15), max_value=2**15 - 1))
def test_int16_roundtrip(value: int) -> None:
    variant = encode_value_to_variant(value, OpcuaDatatype.INT16)
    assert decode_variant_to_value(variant, OpcuaDatatype.INT16) == value


@given(value=st.integers(min_value=0, max_value=2**16 - 1))
def test_uint16_roundtrip(value: int) -> None:
    variant = encode_value_to_variant(value, OpcuaDatatype.UINT16)
    assert decode_variant_to_value(variant, OpcuaDatatype.UINT16) == value


@given(value=st.integers(min_value=-(2**31), max_value=2**31 - 1))
def test_int32_roundtrip(value: int) -> None:
    variant = encode_value_to_variant(value, OpcuaDatatype.INT32)
    assert decode_variant_to_value(variant, OpcuaDatatype.INT32) == value


@given(value=st.integers(min_value=0, max_value=2**32 - 1))
def test_uint32_roundtrip(value: int) -> None:
    variant = encode_value_to_variant(value, OpcuaDatatype.UINT32)
    assert decode_variant_to_value(variant, OpcuaDatatype.UINT32) == value


@given(
    value=st.floats(
        min_value=-1e30,
        max_value=1e30,
        allow_nan=False,
        allow_infinity=False,
        width=64,
    )
)
def test_double_roundtrip_within_precision(value: float) -> None:
    variant = encode_value_to_variant(value, OpcuaDatatype.DOUBLE)
    result = decode_variant_to_value(variant, OpcuaDatatype.DOUBLE)
    assert isinstance(result, Decimal)
    # Double-Roundtrip muss innerhalb von 1e-9-relativem Fehler liegen.
    if value == 0:
        assert math.isclose(float(result), 0.0, abs_tol=1e-30)
    else:
        assert math.isclose(float(result), value, rel_tol=1e-9)


@given(value=st.text(max_size=64))
def test_string_roundtrip(value: str) -> None:
    variant = encode_value_to_variant(value, OpcuaDatatype.STRING)
    assert decode_variant_to_value(variant, OpcuaDatatype.STRING) == value


@given(value=st.booleans())
def test_bool_roundtrip(value: bool) -> None:
    variant = encode_value_to_variant(value, OpcuaDatatype.BOOLEAN)
    assert decode_variant_to_value(variant, OpcuaDatatype.BOOLEAN) is value
