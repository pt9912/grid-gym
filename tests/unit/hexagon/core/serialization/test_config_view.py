"""Slice 038 (ADR 0073 §2.4) — versionierte ConfigView fuer
`RunMetadata.config_hash`.

Pinnt das Hash-Verfahren byte-genau: eine Aenderung an
`canonical_json`, am ConfigView-Schema oder an der Version bricht
diese Pins sichtbar (Determinismus-Vertrag, `GG-TERM-002/003`).
"""

from __future__ import annotations

from grid_gym.hexagon.core.serialization.config_view import (
    CONFIG_VIEW_VERSION,
    config_hash_for,
)

_EXPECTED_HASH_MAX_AGE_NONE = "9dd30572f035c108c26fdc749915c349011df9da98031f844f8e69aba04eb399"
"""sha256 von ``{"config_view":1,"max_age_ms":null}``."""

_EXPECTED_HASH_MAX_AGE_1000 = "82ea91c054fa3412f129ab080d100a3acba08bf80da9aadd8a66193e3854ca89"
"""sha256 von ``{"config_view":1,"max_age_ms":1000}``."""


def test_config_view_version_is_one() -> None:
    """ConfigView v1 (ADR 0073 §2.4); Bump nur mit Knob-Aufnahme."""
    assert CONFIG_VIEW_VERSION == 1


def test_config_hash_none_pin() -> None:
    """Byte-genauer Pin des produktiven Zustands (`max_age_ms=None`
    in allen heutigen Composition-Pfaden, ADR 0052 §2.4)."""
    assert config_hash_for(max_age_ms=None) == _EXPECTED_HASH_MAX_AGE_NONE


def test_config_hash_value_pin() -> None:
    """Byte-genauer Pin eines gesetzten Knobs."""
    assert config_hash_for(max_age_ms=1000) == _EXPECTED_HASH_MAX_AGE_1000


def test_config_hash_is_deterministic() -> None:
    """Zwei Aufrufe mit gleichem Knob ergeben denselben Digest."""
    assert config_hash_for(max_age_ms=None) == config_hash_for(max_age_ms=None)


def test_config_hash_distinguishes_knob_values() -> None:
    """Unterschiedliche Knob-Werte ergeben unterschiedliche Digests
    (sonst waere der Preflight-Vergleich bedeutungslos)."""
    assert config_hash_for(max_age_ms=None) != config_hash_for(max_age_ms=1000)
