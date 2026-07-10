"""Tests fuer `MersenneTwisterRandomPort` (`ADR 0007 §4a` AC1-AC6).

Pinnt den vollstaendigen Validierungs-Spike-Vertrag aus ADR 0007 §4a:
- AC1 Protocol-Konformitaet (`RandomPort`-Methoden vorhanden + typed).
- AC3 Determinismus: gleicher Seed → gleiche Sequenz.
- AC4 Sub-Seeding-Stabilitaet: Parent-Calls beeinflussen Sub-Stream nicht.
- AC5 Snapshot/Resume bit-identisch.
- AC6 10.000-Call-Determinismus auf canonical_json-Decimal-Strings.

Sowie die typisierten Negativ-Pfade fuer das Snapshot-Format.
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.errors import (
    RandomPortRangeError,
    RandomPortSnapshotInvalidBytesError,
    RandomPortSnapshotInvalidRngStateLengthError,
    RandomPortSnapshotListItemWrongTypeError,
    RandomPortSnapshotMissingKeysError,
    RandomPortSnapshotNotAnObjectError,
    RandomPortSnapshotWrongTypeError,
    RandomPortVersionError,
    UnexpectedGaussNextError,
)
from grid_gym.hexagon.core.serialization.canonical import canonical_json
from grid_gym.hexagon.ports.driven.random import RandomPort

# Slice 054: determinism-Sensor-Traeger fuer `make test-determinism`.
pytestmark = pytest.mark.determinism

# ---------------------------------------------------------------------------
# AC1 — Protocol-Konformitaet
# ---------------------------------------------------------------------------


def test_implements_random_port_protocol_structurally() -> None:
    """`MersenneTwisterRandomPort` erfuellt strukturell den `RandomPort`-
    Vertrag — alle vier Methoden mit erwarteter Signatur sind da.

    `RandomPort` ist kein `@runtime_checkable` (sonst muesste mypy
    `Protocol`-`isinstance` mit allen Methoden tragen); statt
    `isinstance` pruefen wir explizit per `hasattr`/`callable`.
    """
    port: RandomPort = MersenneTwisterRandomPort(seed=42)
    assert callable(port.next_int)
    assert callable(port.next_float)
    assert callable(port.sub_port)
    assert callable(port.snapshot)


# ---------------------------------------------------------------------------
# AC3 — Determinismus (gleicher Seed → gleiche Sequenz)
# ---------------------------------------------------------------------------


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_same_seed_same_next_int_sequence(seed: int) -> None:
    a = MersenneTwisterRandomPort(seed)
    b = MersenneTwisterRandomPort(seed)
    assert [a.next_int(0, 1000) for _ in range(50)] == [b.next_int(0, 1000) for _ in range(50)]


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_same_seed_same_next_float_sequence(seed: int) -> None:
    a = MersenneTwisterRandomPort(seed)
    b = MersenneTwisterRandomPort(seed)
    assert [a.next_float() for _ in range(50)] == [b.next_float() for _ in range(50)]


def test_next_int_rejects_inverted_range_typed() -> None:
    """`low > high` ist Programmierfehler — typisiert via
    `RandomPortRangeError`, nicht ueber `ValueError` aus
    `random.randint`."""
    port = MersenneTwisterRandomPort(seed=42)
    with pytest.raises(RandomPortRangeError):
        port.next_int(10, 0)


def test_next_int_accepts_equal_low_and_high() -> None:
    """`low == high` ist gueltig — einziges Ergebnis."""
    port = MersenneTwisterRandomPort(seed=42)
    assert port.next_int(7, 7) == 7


def test_next_float_is_decimal_with_6_decimal_places() -> None:
    port = MersenneTwisterRandomPort(seed=42)
    sample = port.next_float()
    assert isinstance(sample, Decimal)
    # `Decimal("0.123456").as_tuple().exponent == -6` ist die
    # 6-Nachkommastellen-Invariante (`GG-DATA-005`).
    assert sample.as_tuple().exponent == -6


# ---------------------------------------------------------------------------
# AC4 — Sub-Seeding-Stabilitaet
# ---------------------------------------------------------------------------


def test_sub_port_stream_independent_of_parent_calls() -> None:
    """Sub-Stream haengt nur von `parent_seed` + `name` ab, nicht vom
    aktuellen Parent-RNG-State (ADR 0007 §4a AC4)."""
    parent_a = MersenneTwisterRandomPort(seed=12345)
    parent_b = MersenneTwisterRandomPort(seed=12345)
    # Parent B macht 100 Calls bevor sub_port — Parent A nicht.
    for _ in range(100):
        parent_b.next_int(0, 1000)
    sub_a = parent_a.sub_port("scheduler")
    sub_b = parent_b.sub_port("scheduler")
    assert [sub_a.next_int(0, 1000) for _ in range(30)] == [
        sub_b.next_int(0, 1000) for _ in range(30)
    ]


def test_sub_port_different_names_different_streams() -> None:
    parent = MersenneTwisterRandomPort(seed=42)
    sub_x = parent.sub_port("x")
    sub_y = parent.sub_port("y")
    seq_x = [sub_x.next_int(0, 10**9) for _ in range(20)]
    seq_y = [sub_y.next_int(0, 10**9) for _ in range(20)]
    assert seq_x != seq_y


def test_sub_port_path_carries_parent_chain() -> None:
    """`sub_port` baut den Pfad rekursiv weiter."""
    root = MersenneTwisterRandomPort(seed=42)
    sub1 = root.sub_port("a")
    sub2 = sub1.sub_port("b")
    # Snapshot enthaelt sub_path — strukturell pruefen ueber JSON.
    payload = json.loads(sub2.snapshot().decode("utf-8"))
    assert payload["sub_path"] == ["a", "b"]


# ---------------------------------------------------------------------------
# AC5 — Snapshot/Resume bit-identisch
# ---------------------------------------------------------------------------


def test_snapshot_resume_continues_identical_sequence() -> None:
    a = MersenneTwisterRandomPort(seed=42)
    # Konsumiere ein paar Werte.
    for _ in range(13):
        a.next_int(0, 10**6)
    state = a.snapshot()
    b = MersenneTwisterRandomPort.from_snapshot(state)
    # Beide Ports liefern jetzt die identische Fortsetzung.
    assert [a.next_int(0, 10**6) for _ in range(50)] == [b.next_int(0, 10**6) for _ in range(50)]


def test_snapshot_resume_preserves_sub_path() -> None:
    parent = MersenneTwisterRandomPort(seed=42)
    sub = parent.sub_port("scheduler")
    sub.next_int(0, 100)
    state = sub.snapshot()
    restored = MersenneTwisterRandomPort.from_snapshot(state)
    assert restored._sub_path == ("scheduler",)


def test_snapshot_rejects_non_none_gauss_next() -> None:
    """Wenn jemand den internen `random.Random` extern manipuliert
    und `gauss()` aufruft, traegt `getstate()` ein `float` in
    `gauss_next`. `snapshot()` MUSS das defensiv ablehnen, damit
    der canonical-Pfad nicht mit `FloatNotAllowedError` bricht.
    """
    port = MersenneTwisterRandomPort(seed=42)
    # Direkter Aufruf von gauss() umgeht die RandomPort-API und
    # setzt gauss_next intern auf einen float-Wert.
    port._rng.gauss(0.0, 1.0)
    with pytest.raises(UnexpectedGaussNextError):
        port.snapshot()


def test_snapshot_is_canonical_json_bytes() -> None:
    port = MersenneTwisterRandomPort(seed=42)
    state = port.snapshot()
    # canonical_json-Bytes sind UTF-8 und enthalten den Pflicht-
    # `version: int`-Schluessel (M1-Welle-1-Konvention).
    parsed = json.loads(state.decode("utf-8"))
    assert parsed["version"] == 1
    assert isinstance(parsed["seed"], int)


# ---------------------------------------------------------------------------
# Composition-Methode `snapshot_as_mapping` (`ADR 0010`)
# ---------------------------------------------------------------------------


def test_snapshot_as_mapping_is_dict_with_pflicht_keys() -> None:
    """`snapshot_as_mapping` liefert ein dict mit dem Pflicht-
    Schluesselsatz aus `ADR 0009 §2`."""
    port = MersenneTwisterRandomPort(seed=42)
    payload = port.snapshot_as_mapping()
    assert isinstance(payload, dict)
    assert set(payload.keys()) == {
        "version",
        "seed",
        "sub_path",
        "rng_version",
        "rng_state",
    }


def test_snapshot_as_mapping_matches_canonical_json_snapshot() -> None:
    """`ADR 0010` Single-Source-of-Truth-Invariante:
    `canonical_json(snapshot_as_mapping()) == snapshot()`."""
    port = MersenneTwisterRandomPort(seed=42)
    # Konsumiere ein paar Werte, damit der State nicht trivial ist.
    for _ in range(7):
        port.next_int(0, 1000)
    assert canonical_json(port.snapshot_as_mapping()) == port.snapshot()


def test_snapshot_as_mapping_carries_sub_path_for_sub_ports() -> None:
    parent = MersenneTwisterRandomPort(seed=42)
    sub = parent.sub_port("scheduler").sub_port("agents")
    payload = sub.snapshot_as_mapping()
    assert payload["sub_path"] == ["scheduler", "agents"]


def test_snapshot_as_mapping_raises_on_unexpected_gauss_next() -> None:
    """`_build_payload` ist Shared-Code — `snapshot_as_mapping`
    erbt die gauss_next-Defensive von `snapshot`."""
    port = MersenneTwisterRandomPort(seed=42)
    port._rng.gauss(0.0, 1.0)
    with pytest.raises(UnexpectedGaussNextError):
        port.snapshot_as_mapping()


# ---------------------------------------------------------------------------
# AC6 — Hoch-Volumen-Determinismus (canonical-Strings byte-identisch)
# ---------------------------------------------------------------------------

_HIGH_VOLUME_CALLS = 10_000


def test_ten_thousand_next_float_canonical_bytes_are_stable() -> None:
    """ADR 0007 §4a AC6: zwei Generatoren mit gleichem Seed produzieren
    ueber 10.000 `next_float`-Calls byte-identische canonical_json-
    Decimal-Strings."""
    port_a = MersenneTwisterRandomPort(seed=42)
    port_b = MersenneTwisterRandomPort(seed=42)
    bytes_a = canonical_json([port_a.next_float() for _ in range(_HIGH_VOLUME_CALLS)])
    bytes_b = canonical_json([port_b.next_float() for _ in range(_HIGH_VOLUME_CALLS)])
    assert bytes_a == bytes_b


# ---------------------------------------------------------------------------
# Negativ-Pfade — typisierte Snapshot-Format-Errors
# ---------------------------------------------------------------------------


def test_from_snapshot_rejects_invalid_utf8() -> None:
    with pytest.raises(RandomPortSnapshotInvalidBytesError):
        MersenneTwisterRandomPort.from_snapshot(b"\xff\xfe not utf-8")


def test_from_snapshot_rejects_invalid_json() -> None:
    with pytest.raises(RandomPortSnapshotInvalidBytesError):
        MersenneTwisterRandomPort.from_snapshot(b"{not valid json")


def test_from_snapshot_rejects_non_object_top_level() -> None:
    with pytest.raises(RandomPortSnapshotNotAnObjectError):
        MersenneTwisterRandomPort.from_snapshot(b"[1, 2, 3]")


def test_from_snapshot_rejects_missing_keys() -> None:
    with pytest.raises(RandomPortSnapshotMissingKeysError):
        MersenneTwisterRandomPort.from_snapshot(b'{"version": 1}')


def test_from_snapshot_rejects_wrong_seed_type() -> None:
    payload = b'{"version": 1, "seed": "42", "sub_path": [], "rng_version": 3, "rng_state": [0]}'
    with pytest.raises(RandomPortSnapshotWrongTypeError):
        MersenneTwisterRandomPort.from_snapshot(payload)


def test_from_snapshot_rejects_bool_in_rng_state() -> None:
    """`bool` ist `int`-Subklasse — fuer rng_state explizit verboten."""
    payload = b'{"version": 1, "seed": 0, "sub_path": [], "rng_version": 3, "rng_state": [true]}'
    with pytest.raises(RandomPortSnapshotListItemWrongTypeError):
        MersenneTwisterRandomPort.from_snapshot(payload)


def test_from_snapshot_rejects_non_string_in_sub_path() -> None:
    payload = b'{"version": 1, "seed": 0, "sub_path": [1], "rng_version": 3, "rng_state": [0]}'
    with pytest.raises(RandomPortSnapshotListItemWrongTypeError):
        MersenneTwisterRandomPort.from_snapshot(payload)


def test_from_snapshot_rejects_non_list_sub_path() -> None:
    """`sub_path` muss eine Liste sein, kein Skalar."""
    payload = (
        b'{"version": 1, "seed": 0, "sub_path": "not-a-list", "rng_version": 3, "rng_state": [0]}'
    )
    with pytest.raises(RandomPortSnapshotWrongTypeError):
        MersenneTwisterRandomPort.from_snapshot(payload)


def test_from_snapshot_rejects_non_list_rng_state() -> None:
    payload = b'{"version": 1, "seed": 0, "sub_path": [], "rng_version": 3, "rng_state": 0}'
    with pytest.raises(RandomPortSnapshotWrongTypeError):
        MersenneTwisterRandomPort.from_snapshot(payload)


def test_from_snapshot_rejects_non_int_in_rng_state() -> None:
    """Ein Float-Element im rng_state-Array ist verboten."""
    payload = b'{"version": 1, "seed": 0, "sub_path": [], "rng_version": 3, "rng_state": [1.5]}'
    with pytest.raises(RandomPortSnapshotListItemWrongTypeError):
        MersenneTwisterRandomPort.from_snapshot(payload)


def test_from_snapshot_rejects_unknown_version() -> None:
    """Nur `version: 1` wird heute unterstuetzt."""
    payload = b'{"version": 99, "seed": 0, "sub_path": [], "rng_version": 3, "rng_state": [0]}'
    # Vorab: das ist ein 1-Element-rng_state — der eigentliche
    # setstate-Call wird nie erreicht, weil VersionError vorher feuert.
    with pytest.raises(RandomPortVersionError):
        MersenneTwisterRandomPort.from_snapshot(payload)


def test_from_snapshot_rejects_wrong_rng_state_length() -> None:
    """`rng_state` muss exakt 625 Elemente haben (Mersenne-Twister:
    624 MT-Werte + 1 Index). Ein 1-Element-Array mit gueltiger
    `version: 1` faengt der typisierte Laengen-Check vor
    `random.Random.setstate` ab.
    """
    payload = b'{"version": 1, "seed": 0, "sub_path": [], "rng_version": 3, "rng_state": [0]}'
    with pytest.raises(RandomPortSnapshotInvalidRngStateLengthError):
        MersenneTwisterRandomPort.from_snapshot(payload)
