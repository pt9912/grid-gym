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
