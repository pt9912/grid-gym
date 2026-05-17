"""Tests fuer `hexagon/core/replay/mapper.py` (M1 Welle 5b,
`GG-REPLAY-001..003`).

Pinnt:
- CSV + JSONL parsen, alle Pflichtfelder pruefen.
- Original-Timestamp bleibt unveraendert in `ReplaySample.timestamp`.
- `time_mapping="monotonic"` mappt ISO-8601-Deltas auf ms.
- `time_mapping="index"` mappt n -> n * tick_ms.
- `GG-REPLAY-003`-Tie-Breaking: gleicher `simulation_time` ->
  stabile Reihenfolge (`device_id, metric, import_sequence`).
- Typisierte Negativ-Pfade.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.errors import (
    ReplayInvalidValueError,
    ReplayMissingFieldError,
)
from grid_gym.hexagon.core.replay.mapper import parse_csv, parse_jsonl

# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

_CSV_TEMPLATE = (
    "timestamp,device_id,metric,value,unit\n"
    "2024-01-01T00:00:00Z,grid-1,power_kw,1.5,kW\n"
    "2024-01-01T00:00:01Z,grid-1,power_kw,2.5,kW\n"
    "2024-01-01T00:00:02Z,grid-1,power_kw,3.5,kW\n"
)


def test_parse_csv_returns_quantized_decimals_and_preserves_timestamp() -> None:
    samples = parse_csv(_CSV_TEMPLATE, tick_ms=1000)
    assert len(samples) == 3
    assert samples[0].timestamp == "2024-01-01T00:00:00Z"
    assert samples[0].value == Decimal("1.500000")
    assert samples[0].unit == "kW"


def test_parse_csv_monotonic_assigns_ms_deltas() -> None:
    samples = parse_csv(_CSV_TEMPLATE, tick_ms=1000, time_mapping="monotonic")
    assert [s.simulation_time for s in samples] == [0, 1000, 2000]


def test_parse_csv_index_assigns_n_times_tick_ms() -> None:
    samples = parse_csv(_CSV_TEMPLATE, tick_ms=100, time_mapping="index")
    assert [s.simulation_time for s in samples] == [0, 100, 200]


def test_parse_csv_rejects_missing_field() -> None:
    bad = "timestamp,device_id,metric,value\n2024-01-01T00:00:00Z,g,m,1\n"
    with pytest.raises(ReplayMissingFieldError):
        parse_csv(bad, tick_ms=1000)


def test_parse_csv_rejects_empty_value_field() -> None:
    bad = "timestamp,device_id,metric,value,unit\n2024-01-01T00:00:00Z,g,m,,kW\n"
    with pytest.raises(ReplayMissingFieldError):
        parse_csv(bad, tick_ms=1000)


def test_parse_csv_rejects_non_decimal_value() -> None:
    bad = "timestamp,device_id,metric,value,unit\n2024-01-01T00:00:00Z,g,m,not-a-number,kW\n"
    with pytest.raises(ReplayInvalidValueError):
        parse_csv(bad, tick_ms=1000)


def test_parse_csv_rejects_invalid_timestamp_for_monotonic_mapping() -> None:
    bad = "timestamp,device_id,metric,value,unit\nnot-iso,g,m,1.0,kW\n"
    with pytest.raises(ReplayInvalidValueError):
        parse_csv(bad, tick_ms=1000)


def test_parse_csv_rejects_unknown_time_mapping() -> None:
    with pytest.raises(ReplayInvalidValueError):
        parse_csv(_CSV_TEMPLATE, tick_ms=1000, time_mapping="weird")


# ---------------------------------------------------------------------------
# JSON-Lines
# ---------------------------------------------------------------------------


def test_parse_jsonl_minimal() -> None:
    jsonl = (
        '{"timestamp": "2024-01-01T00:00:00Z", "device_id": "g",'
        ' "metric": "m", "value": "1.0", "unit": "kW"}\n'
    )
    samples = parse_jsonl(jsonl, tick_ms=1000)
    assert len(samples) == 1
    assert samples[0].value == Decimal("1.000000")


def test_parse_jsonl_skips_empty_lines() -> None:
    jsonl = (
        "\n"
        '{"timestamp": "2024-01-01T00:00:00Z", "device_id": "g",'
        ' "metric": "m", "value": "1.0", "unit": "kW"}\n'
        "\n"
    )
    assert len(parse_jsonl(jsonl, tick_ms=1000)) == 1


def test_parse_jsonl_rejects_invalid_json() -> None:
    with pytest.raises(ReplayInvalidValueError):
        parse_jsonl("{broken\n", tick_ms=1000)


def test_parse_jsonl_rejects_non_object_line() -> None:
    with pytest.raises(ReplayInvalidValueError):
        parse_jsonl("[1, 2, 3]\n", tick_ms=1000)


def test_parse_jsonl_accepts_int_value() -> None:
    """`int` wird automatisch zu `Decimal` quantisiert."""
    jsonl = (
        '{"timestamp": "2024-01-01T00:00:00Z", "device_id": "g",'
        ' "metric": "m", "value": 42, "unit": "kW"}\n'
    )
    samples = parse_jsonl(jsonl, tick_ms=1000)
    assert samples[0].value == Decimal("42.000000")


# ---------------------------------------------------------------------------
# Tie-Breaking (`GG-REPLAY-003`)
# ---------------------------------------------------------------------------


def test_samples_with_same_simulation_time_sort_by_device_metric_sequence() -> None:
    """`GG-REPLAY-003`: stabile Sortierung nach `(simulation_time,
    device_id, metric, import_sequence)`. Hier alle 4 Samples mit
    derselben Sim-Zeit (`time_mapping="index"` mit tick_ms=0 wuerde
    durch 0 dividieren — stattdessen monotonic mit gleichen
    Timestamps)."""
    csv_text = (
        "timestamp,device_id,metric,value,unit\n"
        "2024-01-01T00:00:00Z,bravo,power,1.0,kW\n"
        "2024-01-01T00:00:00Z,alpha,power,2.0,kW\n"
        "2024-01-01T00:00:00Z,alpha,energy,3.0,kWh\n"
        "2024-01-01T00:00:00Z,alpha,power,4.0,kW\n"
    )
    samples = parse_csv(csv_text, tick_ms=1000, time_mapping="monotonic")
    # alle haben simulation_time=0. Sortierung:
    # (alpha, energy, seq=2), (alpha, power, seq=1), (alpha, power, seq=3), (bravo, power, seq=0).
    assert [(s.device_id, s.metric, s.import_sequence) for s in samples] == [
        ("alpha", "energy", 2),
        ("alpha", "power", 1),
        ("alpha", "power", 3),
        ("bravo", "power", 0),
    ]


def test_empty_input_returns_empty_tuple() -> None:
    assert parse_csv("timestamp,device_id,metric,value,unit\n", tick_ms=1000) == ()
    assert parse_jsonl("", tick_ms=1000) == ()
