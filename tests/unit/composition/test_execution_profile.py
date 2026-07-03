"""Slice 038 (ADR 0073 §2.3-§2.5) — Profil des In-Memory-
Composition-Root (`default_run_execution_profile`)."""

from __future__ import annotations

from grid_gym.composition._execution_profile import default_run_execution_profile
from grid_gym.hexagon.core.serialization.config_view import config_hash_for


def test_profile_declares_inmemory_adapter_family() -> None:
    """Der heutige Composition Root verdrahtet `http_api` +
    `persistence_inmemory` (kanonisch sortiert)."""
    profile = default_run_execution_profile()
    assert profile.enabled_adapters == ("http_api", "persistence_inmemory")


def test_profile_platform_arch_is_normalized_and_present() -> None:
    """`platform.machine()` normalisiert (trim+lowercase) und
    nicht-leer — sonst wuerde jeder Composition-Lauf im Preflight
    als fehlend rejected."""
    profile = default_run_execution_profile()
    assert profile.platform_arch != ""
    assert profile.platform_arch == profile.platform_arch.strip().lower()


def test_profile_config_hash_pins_configview_v1_default() -> None:
    """ConfigView v1 mit `max_age_ms=None` (ADR 0052 §2.4: alle
    produktiven Pfade ohne `STALE`-Stage)."""
    profile = default_run_execution_profile()
    assert profile.config_hash == config_hash_for(max_age_ms=None)
