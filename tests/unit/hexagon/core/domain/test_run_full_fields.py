"""Slice 038 (ADR 0073 §2.1-§2.5) — `RunMetadata`-Vollfelder,
Kanonik-Funktionen und `RunExecutionProfile`.

Pinnt die C0-Entscheidungen: Back-Compat-Defaults (leer = fehlend),
`sim_start_time`-Konstante, Adapter-Namens-Kanonik (validieren +
deduplizieren + sortieren) und die `platform_arch`-Normalform.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from grid_gym.hexagon.core.domain.run import (
    SIM_START_TIME_ORIGIN,
    RunExecutionProfile,
    RunMetadata,
    canonical_enabled_adapters,
    canonical_platform_arch,
)
from grid_gym.hexagon.core.errors import (
    InvalidAdapterNameError,
    NonCanonicalEnabledAdaptersError,
    NonCanonicalPlatformArchError,
)


def _metadata(**overrides: object) -> RunMetadata:
    """Minimal-Konstruktion mit den 8 Pflichtfeldern."""
    base: dict[str, object] = {
        "run_id": "r",
        "scenario_hash": "h",
        "schema_version": "grid-gym.scenario.v1",
        "seed": 42,
        "tick_ms": 100,
        "started_at": "",
        "ended_at": "",
        "tool_version": "0.1.0",
    }
    base.update(overrides)
    return RunMetadata(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# RunMetadata-Vollfelder (ADR 0073 §2.1)
# ---------------------------------------------------------------------------


def test_run_metadata_full_field_defaults_mean_missing() -> None:
    """Back-Compat-Defaults: leer = fehlend (ADR 0073 §2.1);
    `sim_start_time` default ist die Zeitmodell-Konstante."""
    meta = _metadata()
    assert meta.platform_arch == ""
    assert meta.enabled_adapters == ()
    assert meta.sim_start_time == SIM_START_TIME_ORIGIN
    assert meta.config_hash == ""


def test_run_metadata_carries_full_fields() -> None:
    """Vollstaendig konstruierte Vollfelder bleiben erhalten
    (frozen Value-Object-Roundtrip)."""
    meta = _metadata(
        platform_arch="x86_64",
        enabled_adapters=("http_api", "persistence_inmemory"),
        sim_start_time=0,
        config_hash="a" * 64,
    )
    assert meta.platform_arch == "x86_64"
    assert meta.enabled_adapters == ("http_api", "persistence_inmemory")
    assert meta.sim_start_time == 0
    assert meta.config_hash == "a" * 64


def test_sim_start_time_origin_is_zero() -> None:
    """ADR 0073 §2.2: das tick-indizierte Zeitmodell startet
    strukturell bei 0 ms."""
    assert SIM_START_TIME_ORIGIN == 0


# ---------------------------------------------------------------------------
# canonical_platform_arch (ADR 0073 §2.5)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("x86_64", "x86_64"),
        ("  X86_64  ", "x86_64"),
        ("AArch64", "aarch64"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_canonical_platform_arch_normalform(raw: str, expected: str) -> None:
    """Trim + Lowercase; leeres Ergebnis bedeutet fehlend."""
    assert canonical_platform_arch(raw) == expected


# ---------------------------------------------------------------------------
# canonical_enabled_adapters (ADR 0073 §2.3)
# ---------------------------------------------------------------------------


def test_canonical_enabled_adapters_sorts_and_dedupes() -> None:
    """Deduplizieren + lexikografisch sortieren."""
    result = canonical_enabled_adapters(
        ("persistence_inmemory", "http_api", "persistence_inmemory")
    )
    assert result == ("http_api", "persistence_inmemory")


def test_canonical_enabled_adapters_empty_is_allowed() -> None:
    """Das leere Profil ist zulaessig und bedeutet fehlend
    (Bare-Adapter-Entrypoint, ADR 0073 §2.3)."""
    assert canonical_enabled_adapters(()) == ()


@pytest.mark.parametrize(
    "invalid_name",
    [
        "Http_Api",
        "http-api",
        "http_api,persistence",
        "http api",
        "",
    ],
)
def test_canonical_enabled_adapters_rejects_invalid_names(invalid_name: str) -> None:
    """Namen ausserhalb ``[a-z0-9_]+`` werden typisiert abgelehnt —
    der Komma-Ausschluss haelt die Persistenz-Form eindeutig."""
    with pytest.raises(InvalidAdapterNameError):
        canonical_enabled_adapters((invalid_name,))


# ---------------------------------------------------------------------------
# RunExecutionProfile (ADR 0073 §2.3)
# ---------------------------------------------------------------------------


def test_run_execution_profile_default_is_empty() -> None:
    """Default = leeres Profil (Bare-Adapter-Entrypoint) —
    fail-closed im Replay-Preflight statt falsch-gruen."""
    profile = RunExecutionProfile()
    assert profile.platform_arch == ""
    assert profile.enabled_adapters == ()
    assert profile.config_hash == ""


def test_run_execution_profile_is_frozen() -> None:
    """Attribut-Set wirft `FrozenInstanceError` (AC-DOMAIN-FROZEN)."""
    profile = RunExecutionProfile(platform_arch="x86_64")
    with pytest.raises(FrozenInstanceError):
        profile.platform_arch = "aarch64"  # type: ignore[misc]


@pytest.mark.parametrize("raw", ["X86_64", " x86_64", "x86_64 "])
def test_run_execution_profile_rejects_non_canonical_platform_arch(raw: str) -> None:
    """Slice-038-Review-Folge: unkanonisches `platform_arch` faellt
    fail-fast bei der Konstruktion — sonst wuerde ein Composition
    Root mit Roh-`platform.machine()` False-Rejects im Preflight
    produzieren."""
    with pytest.raises(NonCanonicalPlatformArchError):
        RunExecutionProfile(platform_arch=raw)


@pytest.mark.parametrize(
    "names",
    [
        ("persistence_inmemory", "http_api"),
        ("http_api", "http_api"),
    ],
)
def test_run_execution_profile_rejects_non_canonical_adapters(
    names: tuple[str, ...],
) -> None:
    """Unsortierte oder duplizierte Adapter-Namen sind unkanonisch
    (ADR 0073 §2.3) und werden typisiert abgewiesen."""
    with pytest.raises(NonCanonicalEnabledAdaptersError):
        RunExecutionProfile(enabled_adapters=names)


def test_run_execution_profile_rejects_invalid_adapter_name() -> None:
    """Ungueltige Namen fallen bereits in der Namens-Validierung
    (`InvalidAdapterNameError` ist praeziser als die Form-Pruefung)."""
    with pytest.raises(InvalidAdapterNameError):
        RunExecutionProfile(enabled_adapters=("Http-Api",))


def test_run_execution_profile_accepts_canonical_values() -> None:
    """Kanonische Werte (und das leere Profil) bleiben gueltig."""
    profile = RunExecutionProfile(
        platform_arch="x86_64",
        enabled_adapters=("http_api", "persistence_inmemory"),
        config_hash="c" * 64,
    )
    assert profile.enabled_adapters == ("http_api", "persistence_inmemory")
