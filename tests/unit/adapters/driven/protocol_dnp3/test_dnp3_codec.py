"""Codec-Tests fuer den DNP3-Adapter (M4 Welle 5a, ADR 0034 §2.3).

Deckt:

- Decode pro Welle-5a-Group/Variation (Binary, Int32-Analog, Float32-
  Analog).
- Group-Mismatch (defensive: Config-Validation sollte das aber nie
  zulassen).
- Value-Type-Errors (None, falscher Python-Typ).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from grid_gym.adapters.driven.protocol_dnp3 import (
    Dnp3CodecGroupMismatchError,
    Dnp3CodecValueTypeError,
    decode_point_value,
)


@dataclass
class _MockPoint:
    """Mock fuer `nfm-dnp3.AnalogInput`/`BinaryInput` mit `.value`-
    und `.index`-Feldern."""

    value: object
    index: int = 0


# ---------------------------------------------------------------------------
# Binary (Group 1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("variation", [1, 2])
def test_decode_binary_true(variation: int) -> None:
    result = decode_point_value(_MockPoint(value=True), group=1, variation=variation)
    assert result == Decimal(1)


@pytest.mark.parametrize("variation", [1, 2])
def test_decode_binary_false(variation: int) -> None:
    result = decode_point_value(_MockPoint(value=False), group=1, variation=variation)
    assert result == Decimal(0)


def test_decode_binary_rejects_non_bool() -> None:
    with pytest.raises(Dnp3CodecValueTypeError):
        decode_point_value(_MockPoint(value=42), group=1, variation=1)


# ---------------------------------------------------------------------------
# Int32 Analog (Group 30 / Variation 1)
# ---------------------------------------------------------------------------


def test_decode_int32_analog() -> None:
    result = decode_point_value(_MockPoint(value=-12345), group=30, variation=1)
    assert result == Decimal(-12345)


def test_decode_int32_analog_rejects_float() -> None:
    with pytest.raises(Dnp3CodecValueTypeError):
        decode_point_value(_MockPoint(value=3.14), group=30, variation=1)


def test_decode_int32_analog_rejects_bool() -> None:
    # Bool ist `int`-Subclass — wir wollen ihn aber NICHT akzeptieren.
    with pytest.raises(Dnp3CodecValueTypeError):
        decode_point_value(_MockPoint(value=True), group=30, variation=1)


# ---------------------------------------------------------------------------
# Float32 Analog (Group 30 / Variation 5)
# ---------------------------------------------------------------------------


def test_decode_float32_analog_returns_decimal_via_repr() -> None:
    result = decode_point_value(_MockPoint(value=3.14), group=30, variation=5)
    assert isinstance(result, Decimal)
    assert float(result) == pytest.approx(3.14)


def test_decode_float32_analog_accepts_int() -> None:
    result = decode_point_value(_MockPoint(value=42), group=30, variation=5)
    assert float(result) == pytest.approx(42.0)


def test_decode_float32_analog_rejects_bool() -> None:
    with pytest.raises(Dnp3CodecValueTypeError):
        decode_point_value(_MockPoint(value=True), group=30, variation=5)


def test_decode_float32_analog_rejects_string() -> None:
    with pytest.raises(Dnp3CodecValueTypeError):
        decode_point_value(_MockPoint(value="oops"), group=30, variation=5)


# ---------------------------------------------------------------------------
# Edge-Cases
# ---------------------------------------------------------------------------


def test_decode_none_value_rejected() -> None:
    with pytest.raises(Dnp3CodecValueTypeError):
        decode_point_value(_MockPoint(value=None), group=30, variation=5)


def test_decode_unknown_group_rejected() -> None:
    """Defensive — Config-Validation sollte das nie zulassen,
    aber der Codec haelt die Boundary."""
    with pytest.raises(Dnp3CodecGroupMismatchError) as exc_info:
        decode_point_value(_MockPoint(value=42), group=20, variation=1)
    assert exc_info.value.expected == (20, 1)


def test_decode_unknown_variation_in_group_30_rejected() -> None:
    with pytest.raises(Dnp3CodecGroupMismatchError):
        decode_point_value(_MockPoint(value=42), group=30, variation=99)


# ---------------------------------------------------------------------------
# Roundtrip (Property-Tests)
# ---------------------------------------------------------------------------


@given(value=st.integers(min_value=-(2**31), max_value=2**31 - 1))
def test_int32_decode_roundtrip(value: int) -> None:
    result = decode_point_value(_MockPoint(value=value), group=30, variation=1)
    assert result == Decimal(value)


@given(
    value=st.floats(
        allow_nan=False,
        allow_infinity=False,
        width=32,
    )
)
def test_float32_decode_property(value: float) -> None:
    result = decode_point_value(_MockPoint(value=value), group=30, variation=5)
    assert isinstance(result, Decimal)
    # Float-Decode via repr — direct equality after round-trip.
    assert Decimal(repr(float(value))) == result


@given(value=st.booleans())
def test_binary_decode_property(value: bool) -> None:
    result = decode_point_value(_MockPoint(value=value), group=1, variation=1)
    assert result == Decimal(int(value))
