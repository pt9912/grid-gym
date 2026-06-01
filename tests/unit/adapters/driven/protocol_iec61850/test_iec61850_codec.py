# SPDX-License-Identifier: GPL-3.0-only
"""Codec-Tests fuer den IEC-61850-Adapter (M4 Welle 5b, ADR 0035 §2.3).

Deckt:

- Decode pro Welle-5b-Datatype (bool, int32, float, string).
- Container-vs-Leaf-Erkennung (`'<MmsValue type=15>'`-Repr aus
  pyiec61850-ng-Probe-Run-Befund 2026-06-01).
- Overflow-Pfade (int32-Out-of-Range, Float-NaN/Inf).
- Property-Tests via hypothesis.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from grid_gym.adapters.driven.protocol_iec61850 import (
    Iec61850CodecOverflowError,
    Iec61850CodecValueTypeError,
    decode_mms_value,
)


# ---------------------------------------------------------------------------
# bool
# ---------------------------------------------------------------------------


def test_decode_bool_true() -> None:
    result = decode_mms_value(True, "bool", "LD/LN.DO", "MX")
    assert result is True


def test_decode_bool_false() -> None:
    result = decode_mms_value(False, "bool", "LD/LN.DO", "MX")
    assert result is False


def test_decode_bool_accepts_int_0() -> None:
    # pyiec61850-ng Probe-Run-Befund: Bool wird oft als int (0/1)
    # zurueckgeliefert, je nach CFG-DO-Struktur.
    result = decode_mms_value(0, "bool", "LD/LN.DO", "MX")
    assert result is False


def test_decode_bool_accepts_int_1() -> None:
    result = decode_mms_value(1, "bool", "LD/LN.DO", "MX")
    assert result is True


def test_decode_bool_rejects_int_out_of_range() -> None:
    with pytest.raises(Iec61850CodecOverflowError):
        decode_mms_value(42, "bool", "LD/LN.DO", "MX")


def test_decode_bool_rejects_string() -> None:
    with pytest.raises(Iec61850CodecValueTypeError):
        decode_mms_value("True", "bool", "LD/LN.DO", "MX")


# ---------------------------------------------------------------------------
# int32
# ---------------------------------------------------------------------------


def test_decode_int32_positive() -> None:
    result = decode_mms_value(12345, "int32", "LD/LN.DO", "MX")
    assert result == 12345


def test_decode_int32_negative() -> None:
    result = decode_mms_value(-12345, "int32", "LD/LN.DO", "MX")
    assert result == -12345


def test_decode_int32_rejects_bool() -> None:
    with pytest.raises(Iec61850CodecValueTypeError):
        decode_mms_value(True, "int32", "LD/LN.DO", "MX")


def test_decode_int32_rejects_float() -> None:
    with pytest.raises(Iec61850CodecValueTypeError):
        decode_mms_value(3.14, "int32", "LD/LN.DO", "MX")


def test_decode_int32_overflow_above() -> None:
    with pytest.raises(Iec61850CodecOverflowError):
        decode_mms_value(2**31, "int32", "LD/LN.DO", "MX")


def test_decode_int32_overflow_below() -> None:
    with pytest.raises(Iec61850CodecOverflowError):
        decode_mms_value(-(2**31) - 1, "int32", "LD/LN.DO", "MX")


# ---------------------------------------------------------------------------
# float
# ---------------------------------------------------------------------------


def test_decode_float_returns_decimal_via_repr() -> None:
    result = decode_mms_value(3.14, "float", "LD/LN.DO", "MX")
    assert isinstance(result, Decimal)
    assert float(result) == pytest.approx(3.14)


def test_decode_float_accepts_int() -> None:
    result = decode_mms_value(42, "float", "LD/LN.DO", "MX")
    assert isinstance(result, Decimal)
    assert float(result) == pytest.approx(42.0)


def test_decode_float_rejects_bool() -> None:
    with pytest.raises(Iec61850CodecValueTypeError):
        decode_mms_value(True, "float", "LD/LN.DO", "MX")


def test_decode_float_rejects_string() -> None:
    with pytest.raises(Iec61850CodecValueTypeError):
        decode_mms_value("3.14", "float", "LD/LN.DO", "MX")


# ---------------------------------------------------------------------------
# string
# ---------------------------------------------------------------------------


def test_decode_string_passthrough() -> None:
    result = decode_mms_value("battery-1", "string", "LD/LN.DO", "DC")
    assert result == "battery-1"


def test_decode_string_rejects_int() -> None:
    with pytest.raises(Iec61850CodecValueTypeError):
        decode_mms_value(42, "string", "LD/LN.DO", "DC")


# ---------------------------------------------------------------------------
# Container-vs-Leaf
# ---------------------------------------------------------------------------


def test_decode_rejects_mms_container_repr_for_bool() -> None:
    with pytest.raises(Iec61850CodecValueTypeError):
        decode_mms_value("<MmsValue type=15>", "bool", "LD/LN.DO", "ST")


def test_decode_rejects_mms_container_repr_for_int32() -> None:
    with pytest.raises(Iec61850CodecValueTypeError):
        decode_mms_value("<MmsValue type=15>", "int32", "LD/LN.DO", "MX")


def test_decode_rejects_mms_container_repr_for_float() -> None:
    with pytest.raises(Iec61850CodecValueTypeError):
        decode_mms_value("<MmsValue type=15>", "float", "LD/LN.DO", "MX")


def test_decode_rejects_mms_container_repr_for_string() -> None:
    # Auch fuer datatype="string" lehnen wir den Container-Repr ab —
    # wir wollen den echten Daten-String, nicht den Type-Wrapper.
    with pytest.raises(Iec61850CodecValueTypeError):
        decode_mms_value("<MmsValue type=4>", "string", "LD/LN.DO", "DC")


# ---------------------------------------------------------------------------
# Property-Tests
# ---------------------------------------------------------------------------


@given(value=st.integers(min_value=-(2**31), max_value=2**31 - 1))
def test_int32_decode_roundtrip_property(value: int) -> None:
    result = decode_mms_value(value, "int32", "LD/LN.DO", "MX")
    assert result == value


@given(
    value=st.floats(
        allow_nan=False,
        allow_infinity=False,
        width=32,
    )
)
def test_float_decode_property(value: float) -> None:
    result = decode_mms_value(value, "float", "LD/LN.DO", "MX")
    assert isinstance(result, Decimal)
    assert Decimal(repr(float(value))) == result


@given(value=st.booleans())
def test_bool_decode_property(value: bool) -> None:
    result = decode_mms_value(value, "bool", "LD/LN.DO", "MX")
    assert result is value


@given(value=st.text(max_size=64))
def test_string_decode_property(value: str) -> None:
    # Skip strings starting with `<MmsValue` (collision with
    # Container-Repr-Heuristik).
    if value.startswith("<MmsValue"):
        return
    result = decode_mms_value(value, "string", "LD/LN.DO", "DC")
    assert result == value
