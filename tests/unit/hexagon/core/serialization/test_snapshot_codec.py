"""Tests fuer den generischen Snapshot-/Format-Codec
(M2 Welle 0a, Trigger 014).

Pruefen:
- `assert_required_keys`/`assert_int`/`assert_mapping` werfen typisierte
  `MissingKeysError`/`WrongTypeError` mit korrektem `subsystem`-Tag.
- `assert_payload_canonical_compatible` walks Mapping/list/tuple und
  wirft `WrongTypeError` bei Float-/Bytes-/Non-str-Key-Eintraegen.
- Per-Subsystem-Roots (`RandomPortSnapshotFormatError`, ...) sind
  `isinstance` von `SnapshotFormatError` und tragen das richtige
  `subsystem`-Attribut.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.errors import (
    MissingKeysError,
    RandomPortSnapshotFormatError,
    RandomPortSnapshotMissingKeysError,
    ReplayMissingFieldError,
    ReplayParseError,
    ScenarioMissingKeysError,
    ScenarioSchemaError,
    SchedulerSnapshotFormatError,
    SchedulerSnapshotMissingKeysError,
    SnapshotFormatError,
    TickLoopSnapshotFormatError,
    TickLoopSnapshotMissingKeysError,
    WrongTypeError,
)
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_int,
    assert_mapping,
    assert_payload_canonical_compatible,
    assert_required_keys,
)


# ---------------------------------------------------------------------------
# assert_required_keys
# ---------------------------------------------------------------------------


def test_assert_required_keys_passes_when_all_present() -> None:
    assert_required_keys({"a": 1, "b": 2}, frozenset({"a", "b"}), "battery")


def test_assert_required_keys_raises_missing_keys_error() -> None:
    with pytest.raises(MissingKeysError) as exc_info:
        assert_required_keys({"a": 1}, frozenset({"a", "b", "c"}), "battery")
    assert exc_info.value.subsystem == "battery"
    assert "['b', 'c']" in str(exc_info.value)


def test_missing_keys_error_is_snapshot_format_error() -> None:
    err = MissingKeysError("battery", ["soc_pct"])
    assert isinstance(err, SnapshotFormatError)
    assert err.subsystem == "battery"


# ---------------------------------------------------------------------------
# assert_int
# ---------------------------------------------------------------------------


def test_assert_int_returns_value_on_int() -> None:
    assert assert_int(42, "version", "battery") == 42


def test_assert_int_rejects_bool() -> None:
    with pytest.raises(WrongTypeError) as exc_info:
        assert_int(True, "version", "battery")
    assert exc_info.value.subsystem == "battery"
    assert "must be int" in str(exc_info.value)
    assert "got bool" in str(exc_info.value)


def test_assert_int_rejects_str() -> None:
    with pytest.raises(WrongTypeError) as exc_info:
        assert_int("42", "version", "battery")
    assert exc_info.value.subsystem == "battery"
    assert "got str" in str(exc_info.value)


# ---------------------------------------------------------------------------
# assert_mapping
# ---------------------------------------------------------------------------


def test_assert_mapping_returns_value_on_mapping() -> None:
    raw: dict[str, object] = {"k": 1}
    result = assert_mapping(raw, "params", "battery")
    assert result is raw


def test_assert_mapping_rejects_list() -> None:
    with pytest.raises(WrongTypeError) as exc_info:
        assert_mapping([1, 2, 3], "params", "battery")
    assert exc_info.value.subsystem == "battery"
    assert "must be Mapping" in str(exc_info.value)


# ---------------------------------------------------------------------------
# assert_payload_canonical_compatible
# ---------------------------------------------------------------------------


def test_payload_canonical_accepts_canonical_types() -> None:
    payload: dict[str, object] = {
        "name": "battery-1",
        "count": 42,
        "ratio": Decimal("0.95"),
        "enabled": True,
        "nothing": None,
        "tags": ["a", "b", "c"],
        "tuple_field": (1, 2),
        "nested": {"depth_int": 1, "depth_str": "x"},
    }
    assert_payload_canonical_compatible(payload, "scenario")


def test_payload_canonical_rejects_float() -> None:
    with pytest.raises(WrongTypeError) as exc_info:
        assert_payload_canonical_compatible({"x": 1.5}, "scenario", "events[0].payload")
    assert exc_info.value.subsystem == "scenario"
    assert "events[0].payload.x" in str(exc_info.value)
    assert "got float" in str(exc_info.value)


def test_payload_canonical_rejects_bytes() -> None:
    with pytest.raises(WrongTypeError) as exc_info:
        assert_payload_canonical_compatible({"x": b"raw"}, "scenario")
    assert exc_info.value.subsystem == "scenario"
    assert "got bytes" in str(exc_info.value)


def test_payload_canonical_rejects_non_str_key() -> None:
    payload: dict[object, object] = {42: "x"}
    with pytest.raises(WrongTypeError) as exc_info:
        assert_payload_canonical_compatible(payload, "scenario")
    assert exc_info.value.subsystem == "scenario"
    assert "<key>" in str(exc_info.value)
    assert "got int" in str(exc_info.value)


def test_payload_canonical_rejects_nested_float_in_list() -> None:
    with pytest.raises(WrongTypeError) as exc_info:
        assert_payload_canonical_compatible(
            {"items": [1, 2, 3.14]}, "scenario", "faults[0].payload"
        )
    assert exc_info.value.subsystem == "scenario"
    assert "faults[0].payload.items[2]" in str(exc_info.value)


def test_payload_canonical_rejects_top_level_float() -> None:
    with pytest.raises(WrongTypeError) as exc_info:
        assert_payload_canonical_compatible(1.5, "battery", "soc_pct")
    assert exc_info.value.subsystem == "battery"
    assert "soc_pct" in str(exc_info.value)
    assert "got float" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Welle-0b-Review M-4: erweiterte Negativ-Pfade
# (complex, set/frozenset, MappingProxyType — alles, was die
# Encoder-`dict`-vs-`Mapping`-Diskrepanz schliessen muss).
# ---------------------------------------------------------------------------


def test_payload_canonical_rejects_complex() -> None:
    with pytest.raises(WrongTypeError) as exc_info:
        assert_payload_canonical_compatible({"impedance": complex(1, 2)}, "grid_model")
    assert exc_info.value.subsystem == "grid_model"
    assert "got complex" in str(exc_info.value)


def test_payload_canonical_rejects_set() -> None:
    with pytest.raises(WrongTypeError) as exc_info:
        assert_payload_canonical_compatible({"flags": {"a", "b"}}, "battery")
    assert exc_info.value.subsystem == "battery"
    assert "got set" in str(exc_info.value)


def test_payload_canonical_rejects_frozenset() -> None:
    with pytest.raises(WrongTypeError) as exc_info:
        assert_payload_canonical_compatible(frozenset({"a", "b"}), "battery", "tags")
    assert exc_info.value.subsystem == "battery"
    assert "got frozenset" in str(exc_info.value)


def test_payload_canonical_rejects_mapping_proxy_type() -> None:
    """`MappingProxyType` ist `Mapping`-Subklasse, aber kein `dict` —
    der Encoder (`canonical_json`) dispatcht strikt auf `dict`.
    Welle-0b-Review H-2: Codec wurde von `Mapping` auf `dict` verengt,
    damit Smuggler hier landen, nicht erst im Encoder."""
    import types

    proxy = types.MappingProxyType({"version": 1, "value": 42})
    with pytest.raises(WrongTypeError) as exc_info:
        assert_payload_canonical_compatible(proxy, "battery", "snapshot")
    assert exc_info.value.subsystem == "battery"
    assert "got mappingproxy" in str(exc_info.value)


def test_payload_canonical_rejects_bytearray() -> None:
    with pytest.raises(WrongTypeError) as exc_info:
        assert_payload_canonical_compatible({"raw": bytearray(b"abc")}, "battery")
    assert exc_info.value.subsystem == "battery"
    assert "got bytearray" in str(exc_info.value)


def test_payload_canonical_accepts_empty_mapping_and_lists() -> None:
    """Leere Container sind canonical-zulaessig (`{}` und `[]` werden
    deterministisch emittiert)."""
    assert_payload_canonical_compatible({}, "battery")
    assert_payload_canonical_compatible([], "battery")
    assert_payload_canonical_compatible((), "battery")
    assert_payload_canonical_compatible({"nested": {"empty": {}}}, "battery")


def test_payload_canonical_walks_deeply_nested() -> None:
    """≥5 Ebenen tiefe Struktur — sicherstellen, dass die Rekursion
    keine willkuerliche Tiefen-Begrenzung hat und Pfad-Konstruktion
    konsistent bleibt."""
    deep = {"a": {"b": {"c": {"d": {"e": [1, 2, 3.14]}}}}}
    with pytest.raises(WrongTypeError) as exc_info:
        assert_payload_canonical_compatible(deep, "battery")
    assert "a.b.c.d.e[2]" in str(exc_info.value)
    assert "got float" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Welle-0b-Review M-4: assert_required_keys "alles-fehlt"-Pfad
# ---------------------------------------------------------------------------


def test_assert_required_keys_with_empty_state_lists_all_required_sorted() -> None:
    """Determinismus-Vertrag: Reihenfolge der fehlenden Keys ist
    lexikographisch sortiert (byte-stabile Fehler-Message)."""
    with pytest.raises(MissingKeysError) as exc_info:
        assert_required_keys({}, frozenset({"c", "a", "b"}), "battery")
    assert exc_info.value.subsystem == "battery"
    assert "['a', 'b', 'c']" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Per-Subsystem-Root-Aliasse erben jetzt von SnapshotFormatError
# (Trigger-014-Generalisierung) — Aufrufer koennen generisch catchen.
# ---------------------------------------------------------------------------


def test_random_port_snapshot_format_error_is_snapshot_format_error() -> None:
    err = RandomPortSnapshotMissingKeysError(["state"])
    assert isinstance(err, RandomPortSnapshotFormatError)
    assert isinstance(err, SnapshotFormatError)
    assert err.subsystem == "random_port"


def test_scheduler_snapshot_format_error_is_snapshot_format_error() -> None:
    err = SchedulerSnapshotMissingKeysError(["pending_events"])
    assert isinstance(err, SchedulerSnapshotFormatError)
    assert isinstance(err, SnapshotFormatError)
    assert err.subsystem == "scheduler"


def test_tick_loop_snapshot_format_error_is_snapshot_format_error() -> None:
    err = TickLoopSnapshotMissingKeysError(["scheduler"])
    assert isinstance(err, TickLoopSnapshotFormatError)
    assert isinstance(err, SnapshotFormatError)
    assert err.subsystem == "tick_loop"


def test_scenario_schema_error_is_snapshot_format_error() -> None:
    err = ScenarioMissingKeysError("scenario", ["devices"])
    assert isinstance(err, ScenarioSchemaError)
    assert isinstance(err, SnapshotFormatError)
    assert err.subsystem == "scenario"


def test_replay_parse_error_is_snapshot_format_error() -> None:
    err = ReplayMissingFieldError(0, "simulation_time")
    assert isinstance(err, ReplayParseError)
    assert isinstance(err, SnapshotFormatError)
    assert err.subsystem == "replay"
