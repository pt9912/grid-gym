"""Tests fuer `SnapshotEnvelope` (M1 Welle 1, Vorbereitung Welle 4)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict

import pytest

from grid_gym.hexagon.core.domain.snapshot import SnapshotEnvelope
from grid_gym.hexagon.core.errors import (
    MissingSubSnapshotVersionError,
    NonIntegerSubSnapshotVersionError,
)
from grid_gym.hexagon.core.serialization.canonical import canonical_json


def _make_envelope() -> SnapshotEnvelope:
    return SnapshotEnvelope(
        version=1,
        run_id="r",
        simulation_time=0,
        sub_snapshots={
            "scheduler": {"version": 1, "queue": []},
            "random": {"version": 1, "seed": 42},
        },
    )


def test_envelope_constructs_with_valid_sub_snapshots() -> None:
    envelope = _make_envelope()
    assert envelope.version == 1
    assert "scheduler" in envelope.sub_snapshots


def test_envelope_is_frozen() -> None:
    envelope = _make_envelope()
    with pytest.raises(FrozenInstanceError):
        envelope.version = 2  # type: ignore[misc]


def test_envelope_rejects_sub_snapshot_without_version() -> None:
    with pytest.raises(MissingSubSnapshotVersionError):
        SnapshotEnvelope(
            version=1,
            run_id="r",
            simulation_time=0,
            sub_snapshots={"scheduler": {"queue": []}},
        )


def test_envelope_rejects_sub_snapshot_with_non_int_version() -> None:
    with pytest.raises(NonIntegerSubSnapshotVersionError):
        SnapshotEnvelope(
            version=1,
            run_id="r",
            simulation_time=0,
            sub_snapshots={"scheduler": {"version": "1"}},
        )


def test_envelope_rejects_sub_snapshot_with_bool_version() -> None:
    """`bool` ist `int`-Subklasse — Schema-Versionen sind aber
    Ganzzahlen, keine Wahrheitswerte."""
    with pytest.raises(NonIntegerSubSnapshotVersionError):
        SnapshotEnvelope(
            version=1,
            run_id="r",
            simulation_time=0,
            sub_snapshots={"scheduler": {"version": True}},
        )


def test_envelope_canonical_roundtrip_is_stable() -> None:
    a = _make_envelope()
    b = _make_envelope()
    assert canonical_json(asdict(a)) == canonical_json(asdict(b))
