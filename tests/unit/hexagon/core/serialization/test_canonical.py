"""Property- und Smoke-Tests fuer `canonical_json` (ADR 0002 §A-2).

Erwartete Invarianten:
- Decimal-Werte werden in Fixed-Point-Notation emittiert; Tail-Nullen
  bleiben erhalten.
- Dict-Schluessel werden lexikographisch sortiert — Einfuegereihenfolge
  ist irrelevant.
- NaN/Infinity, float-Eingaben, Nicht-`str`-Dict-Keys und unbekannte
  Typen loesen typisierte Subklassen von `CanonicalSerializationError`
  aus.
- Roundtrip via `json.loads` (zur Strukturpruefung) bleibt
  byte-stabil fuer Domain-Skizzen.
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from grid_gym.hexagon.core.errors import GridGymError
from grid_gym.hexagon.core.serialization.canonical import (
    CanonicalSerializationError,
    FloatNotAllowedError,
    NonFiniteDecimalError,
    NonStringDictKeyError,
    UnsupportedTypeError,
    canonical_json,
)

# ---------------------------------------------------------------------------
# Strategien
# ---------------------------------------------------------------------------

_decimals = st.decimals(
    min_value=Decimal("-1000000000"),
    max_value=Decimal("1000000000"),
    allow_nan=False,
    allow_infinity=False,
    places=6,
)


# ---------------------------------------------------------------------------
# Basis-Typen
# ---------------------------------------------------------------------------


def test_none_emits_null() -> None:
    assert canonical_json(None) == b"null"


def test_bool_true_emits_true() -> None:
    assert canonical_json(True) == b"true"


def test_bool_false_emits_false() -> None:
    assert canonical_json(False) == b"false"


def test_int_zero() -> None:
    assert canonical_json(0) == b"0"


def test_int_positive() -> None:
    assert canonical_json(42) == b"42"


def test_int_negative() -> None:
    assert canonical_json(-7) == b"-7"


def test_string_empty() -> None:
    assert canonical_json("") == b'""'


def test_string_simple() -> None:
    assert canonical_json("hello") == b'"hello"'


def test_string_with_quote() -> None:
    assert canonical_json('say "hi"') == b'"say \\"hi\\""'


def test_string_with_backslash() -> None:
    assert canonical_json("a\\b") == b'"a\\\\b"'


def test_string_with_control_char() -> None:
    assert canonical_json("\x01") == b'"\\u0001"'


def test_string_with_newline_uses_named_escape() -> None:
    assert canonical_json("\n") == b'"\\n"'


def test_list_empty() -> None:
    assert canonical_json([]) == b"[]"


def test_list_preserves_order_concrete() -> None:
    assert canonical_json([3, 1, 2]) == b"[3,1,2]"


def test_tuple_emits_like_list() -> None:
    assert canonical_json((1, 2, 3)) == b"[1,2,3]"


def test_dict_empty() -> None:
    assert canonical_json({}) == b"{}"


def test_dict_single_entry() -> None:
    assert canonical_json({"a": 1}) == b'{"a":1}'


def test_dict_sorts_keys_lexicographically() -> None:
    assert canonical_json({"b": 1, "a": 2}) == b'{"a":2,"b":1}'


def test_nested_structure() -> None:
    payload: dict[str, object] = {
        "outer": [{"k": "v"}, [1, 2]],
        "n": None,
    }
    encoded = canonical_json(payload)
    assert encoded == b'{"n":null,"outer":[{"k":"v"},[1,2]]}'


# ---------------------------------------------------------------------------
# Decimal
# ---------------------------------------------------------------------------


def test_decimal_integer() -> None:
    assert canonical_json(Decimal("42")) == b"42"


def test_decimal_fractional() -> None:
    assert canonical_json(Decimal("1.5")) == b"1.5"


def test_decimal_preserves_trailing_zeros() -> None:
    """Quantisierung auf 6 Stellen passiert an der Domain-Eingangsgrenze;
    `canonical_json` selbst gibt `Decimal` unveraendert in Fixed-Point
    aus (Tail-Nullen bleiben sichtbar)."""
    assert canonical_json(Decimal("1.500000")) == b"1.500000"


def test_decimal_negative() -> None:
    assert canonical_json(Decimal("-0.123456")) == b"-0.123456"


def test_decimal_zero_variants_emit_as_is() -> None:
    assert canonical_json(Decimal("0")) == b"0"
    assert canonical_json(Decimal("0.0")) == b"0.0"
    assert canonical_json(Decimal("-0")) == b"-0"


# ---------------------------------------------------------------------------
# Fehler
# ---------------------------------------------------------------------------


def test_float_raises_float_not_allowed() -> None:
    with pytest.raises(FloatNotAllowedError):
        canonical_json(1.5)


def test_float_error_is_canonical_error_subclass() -> None:
    assert issubclass(FloatNotAllowedError, CanonicalSerializationError)
    assert issubclass(CanonicalSerializationError, GridGymError)


def test_nan_raises_non_finite_decimal() -> None:
    with pytest.raises(NonFiniteDecimalError):
        canonical_json(Decimal("NaN"))


def test_positive_infinity_raises_non_finite_decimal() -> None:
    with pytest.raises(NonFiniteDecimalError):
        canonical_json(Decimal("Infinity"))


def test_negative_infinity_raises_non_finite_decimal() -> None:
    with pytest.raises(NonFiniteDecimalError):
        canonical_json(Decimal("-Infinity"))


def test_bytes_raises_unsupported_type() -> None:
    with pytest.raises(UnsupportedTypeError):
        canonical_json(b"raw")


def test_dict_non_str_key_raises() -> None:
    with pytest.raises(NonStringDictKeyError):
        canonical_json({1: "value"})


def test_unsupported_custom_type_raises() -> None:
    class Custom:
        pass

    with pytest.raises(UnsupportedTypeError):
        canonical_json(Custom())


# ---------------------------------------------------------------------------
# Property-Tests
# ---------------------------------------------------------------------------


@given(_decimals)
def test_decimal_output_equals_fixed_point_format(d: Decimal) -> None:
    """`canonical_json(d)` muss `format(d, "f")`-UTF-8-Bytes sein."""
    encoded = canonical_json(d)
    assert encoded.decode("utf-8") == format(d, "f")


@given(st.dictionaries(st.text(min_size=1, max_size=10), _decimals, min_size=2, max_size=8))
def test_dict_insertion_order_irrelevant(d: dict[str, Decimal]) -> None:
    """Gleicher Inhalt, andere Einfuegereihenfolge → identische Bytes."""
    items = list(d.items())
    d_forward = dict(items)
    d_reversed = dict(reversed(items))
    assert canonical_json(d_forward) == canonical_json(d_reversed)


@given(st.text())
def test_string_roundtrip_through_json_loads(s: str) -> None:
    """`canonical_json`-Output ist gueltiges JSON; `json.loads` ergibt
    den Original-String zurueck."""
    encoded = canonical_json(s)
    assert json.loads(encoded) == s


@given(st.lists(_decimals, max_size=10))
def test_list_length_preserved(items: list[Decimal]) -> None:
    encoded = canonical_json(items)
    parsed = json.loads(encoded)
    assert len(parsed) == len(items)


@given(st.integers())
def test_int_roundtrip(value: int) -> None:
    encoded = canonical_json(value)
    assert json.loads(encoded) == value


@given(_decimals)
def test_decimal_in_dict_value(d: Decimal) -> None:
    encoded = canonical_json({"v": d})
    assert encoded == b'{"v":' + format(d, "f").encode("utf-8") + b"}"


# ---------------------------------------------------------------------------
# Domain-Skizzen (Telemetry/Command/Event)
# ---------------------------------------------------------------------------


def test_telemetry_skizze_is_order_independent() -> None:
    point: dict[str, object] = {
        "run_id": "run-001",
        "tick": 42,
        "simulation_time": 4200,
        "device_id": "battery-1",
        "metric": "power_kw",
        "value": Decimal("123.456789"),
        "unit": "kW",
        "quality": "valid",
        "source": "sim",
        "sequence": 100,
    }
    point_reordered: dict[str, object] = {k: point[k] for k in reversed(list(point))}
    assert canonical_json(point) == canonical_json(point_reordered)


def test_command_skizze_with_nested_payload() -> None:
    cmd: dict[str, object] = {
        "command_id": "cmd-001",
        "simulation_time": 5000,
        "target_device_id": "battery-1",
        "type": "set_power_kw",
        "payload": {"value": Decimal("250.000")},
        "validation_status": "accepted",
        "result": "accepted",
    }
    encoded = canonical_json(cmd)
    parsed = json.loads(encoded)
    assert parsed["command_id"] == "cmd-001"
    # `json.loads` gibt float fuer JSON-Zahlen zurueck; nur
    # Strukturpruefung, deshalb pytest.approx fuer den Wert.
    assert parsed["payload"]["value"] == pytest.approx(250.0)


def test_event_skizze_with_mixed_payload_array() -> None:
    event: dict[str, object] = {
        "event_id": "evt-001",
        "simulation_time": 1000,
        "source": "scheduler",
        "target": "battery-1",
        "type": "tick",
        "payload": [1, Decimal("2.5"), "three", None],
        "priority": 10,
        "sequence": 1,
    }
    encoded = canonical_json(event)
    parsed = json.loads(encoded)
    payload = parsed["payload"]
    assert payload[0] == 1
    assert payload[1] == pytest.approx(2.5)
    assert payload[2] == "three"
    assert payload[3] is None


def test_skizze_byte_stable_across_runs() -> None:
    """Zwei separat aufgebaute Dicts mit identischem Inhalt erzeugen
    identische Bytes — Determinismus-Invariante (`GG-DATA-005`)."""
    skizze_a: dict[str, object] = {
        "a": 1,
        "b": Decimal("2.0"),
        "c": ["x", "y"],
    }
    skizze_b: dict[str, object] = {
        "c": ["x", "y"],
        "b": Decimal("2.0"),
        "a": 1,
    }
    assert canonical_json(skizze_a) == canonical_json(skizze_b)
