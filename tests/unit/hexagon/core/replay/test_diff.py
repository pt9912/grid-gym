"""Tests fuer `hexagon/core/replay/diff.py` (M1 Welle 5b,
`GG-REPLAY-007`).

Pinnt:
- Identische Sequenzen -> keine Deltas.
- Fachliche Feld-Aenderung -> `classification=fachlich`.
- Volatil-Default (`import_sequence`, `timestamp`) ->
  `classification=volatil`.
- Custom volatile_fields-Override.
- Laengen-Mismatches: zusaetzliches/fehlendes Sample.
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.hexagon.core.domain.replay import (
    ReplayDeltaClassification,
    ReplaySample,
)
from grid_gym.hexagon.core.replay.diff import diff_replay


def _sample(
    *,
    timestamp: str = "2024-01-01T00:00:00Z",
    simulation_time: int = 0,
    device_id: str = "grid-1",
    metric: str = "power_kw",
    value: Decimal = Decimal("1.0"),
    unit: str = "kW",
    import_sequence: int = 0,
) -> ReplaySample:
    return ReplaySample(
        timestamp=timestamp,
        simulation_time=simulation_time,
        device_id=device_id,
        metric=metric,
        value=value,
        unit=unit,
        import_sequence=import_sequence,
    )


def test_identical_sequences_yield_no_deltas() -> None:
    samples = (_sample(), _sample(simulation_time=1000, import_sequence=1))
    assert diff_replay(samples, samples) == ()


def test_value_mismatch_is_fachlich() -> None:
    expected = (_sample(value=Decimal("1.0")),)
    actual = (_sample(value=Decimal("2.0")),)
    deltas = diff_replay(expected, actual)
    assert len(deltas) == 1
    assert deltas[0].path == "sample[0].value"
    assert deltas[0].expected == "1.0"
    assert deltas[0].actual == "2.0"
    assert deltas[0].classification == ReplayDeltaClassification.FACHLICH


def test_import_sequence_mismatch_is_volatil_by_default() -> None:
    expected = (_sample(import_sequence=0),)
    actual = (_sample(import_sequence=99),)
    deltas = diff_replay(expected, actual)
    assert len(deltas) == 1
    assert deltas[0].path == "sample[0].import_sequence"
    assert deltas[0].classification == ReplayDeltaClassification.VOLATIL


def test_timestamp_mismatch_is_volatil_by_default() -> None:
    expected = (_sample(timestamp="2024-01-01T00:00:00Z"),)
    actual = (_sample(timestamp="2024-01-01T00:00:00+00:00"),)
    deltas = diff_replay(expected, actual)
    assert len(deltas) == 1
    assert deltas[0].classification == ReplayDeltaClassification.VOLATIL


def test_custom_volatile_fields_override_default() -> None:
    """Wenn `volatile_fields=frozenset()` uebergeben wird, sind auch
    `import_sequence`/`timestamp` fachliche Felder."""
    expected = (_sample(import_sequence=0),)
    actual = (_sample(import_sequence=99),)
    deltas = diff_replay(expected, actual, volatile_fields=frozenset())
    assert deltas[0].classification == ReplayDeltaClassification.FACHLICH


def test_extra_actual_sample_yields_missing_expected_delta() -> None:
    expected = (_sample(),)
    actual = (_sample(), _sample(simulation_time=1000, import_sequence=1))
    deltas = diff_replay(expected, actual)
    assert len(deltas) == 1
    assert deltas[0].path == "sample[1]"
    assert deltas[0].expected == "<missing>"
    assert deltas[0].actual == "<sample>"
    assert deltas[0].classification == ReplayDeltaClassification.FACHLICH


def test_extra_expected_sample_yields_missing_actual_delta() -> None:
    expected = (_sample(), _sample(simulation_time=1000, import_sequence=1))
    actual = (_sample(),)
    deltas = diff_replay(expected, actual)
    assert len(deltas) == 1
    assert deltas[0].path == "sample[1]"
    assert deltas[0].expected == "<sample>"
    assert deltas[0].actual == "<missing>"


def test_multiple_field_mismatches_in_one_sample() -> None:
    expected = (_sample(value=Decimal("1.0"), unit="kW"),)
    actual = (_sample(value=Decimal("2.0"), unit="MW"),)
    deltas = diff_replay(expected, actual)
    paths = sorted(delta.path for delta in deltas)
    assert paths == ["sample[0].unit", "sample[0].value"]
    assert all(d.classification == ReplayDeltaClassification.FACHLICH for d in deltas)


def test_tick_is_simulation_time_divided_by_thousand() -> None:
    """`GG-REPLAY-007`-Akzeptanz nennt `tick` als Diff-Feld;
    Welle-5-Default: `simulation_time // 1000`."""
    expected = (_sample(simulation_time=5000, value=Decimal("1.0")),)
    actual = (_sample(simulation_time=5000, value=Decimal("2.0")),)
    delta = diff_replay(expected, actual)[0]
    assert delta.tick == 5
