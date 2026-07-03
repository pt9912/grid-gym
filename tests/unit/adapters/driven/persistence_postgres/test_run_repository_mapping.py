"""Slice 038 (ADR 0073 §2.3/§2.7) — `enabled_adapters`-Persistenz-
Mapping des `PostgresRunRepository`.

Pinnt den Tupel ↔ komma-separierter-String-Round-Trip inklusive der
Fehlend-Repraesentation (``()`` ↔ ``""``). Die SQL-Pfade selbst
laufen in `tests/integration/` gegen echtes Postgres.
"""

from __future__ import annotations

import pytest

from grid_gym.adapters.driven.persistence_postgres.run_repository import (
    _decode_enabled_adapters,
    _encode_enabled_adapters,
)
from grid_gym.hexagon.core.errors import (
    InvalidAdapterNameError,
    NonCanonicalEnabledAdaptersError,
)


@pytest.mark.parametrize(
    ("names", "encoded"),
    [
        ((), ""),
        (("http_api",), "http_api"),
        (("http_api", "persistence_inmemory"), "http_api,persistence_inmemory"),
    ],
)
def test_encode_enabled_adapters(names: tuple[str, ...], encoded: str) -> None:
    """Kanonisches Tupel → Persistenz-String; leer = fehlend."""
    assert _encode_enabled_adapters(names) == encoded


@pytest.mark.parametrize(
    ("encoded", "names"),
    [
        ("", ()),
        ("http_api", ("http_api",)),
        ("http_api,persistence_inmemory", ("http_api", "persistence_inmemory")),
    ],
)
def test_decode_enabled_adapters(encoded: str, names: tuple[str, ...]) -> None:
    """Persistenz-String → Tupel; ``""`` → ``()`` (fehlend)."""
    assert _decode_enabled_adapters(encoded) == names


def test_enabled_adapters_roundtrip_is_symmetric() -> None:
    """encode(decode(x)) == x fuer kanonische Werte (Symmetrie-Pin)."""
    for names in ((), ("http_api",), ("a", "b_c", "d0")):
        assert _decode_enabled_adapters(_encode_enabled_adapters(names)) == names


@pytest.mark.parametrize(
    "names",
    [
        ("persistence_inmemory", "http_api"),
        ("http_api", "http_api"),
        ("a,b",),
    ],
)
def test_encode_rejects_non_canonical_tuples(names: tuple[str, ...]) -> None:
    """Slice-038-Review-Folge: die Persistenz-Grenze erzwingt die
    Kanonik — ein unkanonisches Tupel (unsortiert, dupliziert oder
    mit Komma im Namen) wuerde sonst still eine Round-Trip-
    Asymmetrie persistieren."""
    with pytest.raises((NonCanonicalEnabledAdaptersError, InvalidAdapterNameError)):
        _encode_enabled_adapters(names)


@pytest.mark.parametrize(
    "raw",
    [
        "persistence_inmemory,http_api",
        "http_api,http_api",
        "a,,b",
        "Http_Api",
    ],
)
def test_decode_rejects_corrupt_column_content(raw: str) -> None:
    """Unkanonischer DB-Bestand (Fremd-Schreiber/manuelles SQL) wird
    typisiert rejected statt still in die Core-Domain gehoben."""
    with pytest.raises((NonCanonicalEnabledAdaptersError, InvalidAdapterNameError)):
        _decode_enabled_adapters(raw)
