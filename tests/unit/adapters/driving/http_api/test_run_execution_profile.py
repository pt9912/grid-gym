"""Slice 038 (ADR 0073 §2.3) — Run-Execution-Profil-Registrierung
und `POST /runs`-Vererbung der GG-TERM-Vollfelder.

Das Profil ist Modul-global (Hook-Inversions-Muster wie
`_register_run_driver_builder`); die Fixtures stellen den
Default (leeres Profil) nach jedem Test wieder her, damit kein
Zustand in andere Tests leakt.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driving.http_api import app
from grid_gym.adapters.driving.http_api._run_execution_profile import (
    _register_run_execution_profile,
    get_run_execution_profile,
)
from grid_gym.adapters.driving.http_api.app import configure_run_repository
from grid_gym.hexagon.core.domain.run import RunExecutionProfile
from tests.unit.hexagon.ports.driven._fakes import InMemoryRunRepository

_VALID_PAYLOAD: dict[str, object] = {
    "scenario_hash": "0" * 64,
    "seed": 42,
    "tick_ms": 100,
}

_PROFILE = RunExecutionProfile(
    platform_arch="x86_64",
    enabled_adapters=("http_api", "persistence_inmemory"),
    config_hash="c" * 64,
)


@pytest.fixture
def reset_profile() -> Iterator[None]:
    """Etabliert die leere Profil-Baseline und stellt danach den
    vorherigen Zustand wieder her.

    Der Modul-Global ist import-zeitlich befuellbar (der Import von
    `grid_gym.composition.asgi` in anderen Tests registriert das
    produktive Profil) — die Baseline macht die Tests
    ordnungs-unabhaengig."""
    previous = get_run_execution_profile()
    _register_run_execution_profile(RunExecutionProfile())
    yield
    _register_run_execution_profile(previous)


@pytest.fixture
def configured_app(
    reset_profile: None,
) -> Iterator[tuple[TestClient, InMemoryRunRepository]]:
    """App mit frischem Repository + Profil-Reset pro Test."""
    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    with TestClient(app) as client:
        yield client, repository


def test_default_profile_is_empty(reset_profile: None) -> None:
    """Bare-Adapter-Zustand ohne Composition-Registrierung (von der
    Fixture-Baseline hergestellt): leeres Profil — fail-closed im
    Replay-Preflight (ADR 0073 §2.3/§2.6)."""
    assert get_run_execution_profile() == RunExecutionProfile()


def test_registered_profile_is_returned(reset_profile: None) -> None:
    """Hook-Inversion: der Composition Root registriert, der
    Adapter liest."""
    _register_run_execution_profile(_PROFILE)
    assert get_run_execution_profile() == _PROFILE


def test_post_runs_inherits_registered_profile(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """`POST /runs` erbt die Vollfelder aus dem registrierten
    Profil (ADR 0073 §2.3); `sim_start_time` ist die
    Zeitmodell-Konstante 0 (§2.2)."""
    client, repository = configured_app
    _register_run_execution_profile(_PROFILE)
    body = client.post("/runs", json=_VALID_PAYLOAD).json()
    persisted = repository.get_by_id(body["run_id"])
    assert persisted.platform_arch == "x86_64"
    assert persisted.enabled_adapters == ("http_api", "persistence_inmemory")
    assert persisted.sim_start_time == 0
    assert persisted.config_hash == "c" * 64


def test_post_runs_without_profile_persists_missing_markers(
    configured_app: tuple[TestClient, InMemoryRunRepository],
) -> None:
    """Ohne Composition Root bleiben die Vollfelder leer (fehlend)
    — der Replay-Preflight rejected solche Laeufe (ADR 0073 §2.6),
    die Lauf-Anlage selbst bleibt zulaessig."""
    client, repository = configured_app
    body = client.post("/runs", json=_VALID_PAYLOAD).json()
    persisted = repository.get_by_id(body["run_id"])
    assert persisted.platform_arch == ""
    assert persisted.enabled_adapters == ()
    assert persisted.config_hash == ""
