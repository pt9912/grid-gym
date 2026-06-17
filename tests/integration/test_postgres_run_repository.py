"""Integration-Test fuer `PostgresRunRepository` (M1 Welle 6c).

Nutzt `testcontainers[postgres]`, um pro Test eine ephemere
Postgres-Instanz hochzufahren. `alembic upgrade head` rollt das
`runs`-Schema ein; danach laeuft der Welle-1-`RunMetadata`-
Roundtrip plus typisierte Negativ-Pfade.

Der `make test-integration`-Stack mounted den Docker-Socket vom
Host in den Test-Runner-Container — testcontainers spawnt
Postgres ueber diesen Socket als Sibling-Container (nicht
docker-in-docker).

Seit M2 Welle 6c (`fix(welle-6c)`-Review-Folge L-6): die
`postgres_dsn`- UND `repository`-Fixtures leben modul-uebergreifend
in `tests/integration/conftest.py` (gemeinsame Nutzung mit
`test_mvp_demo_scenario.py`).
"""

from __future__ import annotations

import uuid

import pytest

from grid_gym.adapters.driven.persistence_postgres import PostgresRunRepository
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.errors import (
    RunAlreadyExistsError,
    RunNotFoundError,
)


def _make_metadata(run_id: str | None = None, *, replay_of: str | None = None) -> RunMetadata:
    return RunMetadata(
        run_id=run_id or str(uuid.uuid4()),
        scenario_hash="0" * 64,
        schema_version="grid-gym.scenario.v1",
        seed=42,
        tick_ms=100,
        started_at="2026-05-17T10:00:00Z",
        ended_at="2026-05-17T10:01:00Z",
        tool_version="0.1.0",
        replay_of=replay_of,
    )


# ---------------------------------------------------------------------------
# Happy-Path
# ---------------------------------------------------------------------------


def test_save_then_get_by_id_roundtrips_all_fields(repository: PostgresRunRepository) -> None:
    metadata = _make_metadata()
    repository.save(metadata)
    loaded = repository.get_by_id(metadata.run_id)
    assert loaded == metadata


def test_save_then_get_by_id_roundtrips_replay_of(repository: PostgresRunRepository) -> None:
    """ADR 0068 (Slice 039): die persistente Replay-Bindung roundtrippt ueber
    die 0003-Migration `replay_of`-Spalte (NULL fuer regulaere Laeufe)."""
    reference = _make_metadata()
    repository.save(reference)
    replay = _make_metadata(replay_of=reference.run_id)
    repository.save(replay)
    loaded = repository.get_by_id(replay.run_id)
    assert loaded.replay_of == reference.run_id
    assert loaded == replay


def test_exists_returns_true_after_save(repository: PostgresRunRepository) -> None:
    metadata = _make_metadata()
    repository.save(metadata)
    assert repository.exists(metadata.run_id)


def test_exists_returns_false_for_unknown_run_id(
    repository: PostgresRunRepository,
) -> None:
    assert not repository.exists("missing")


# ---------------------------------------------------------------------------
# Typisierte Fehler-Pfade
# ---------------------------------------------------------------------------


def test_get_by_id_raises_typed_for_unknown_run_id(
    repository: PostgresRunRepository,
) -> None:
    with pytest.raises(RunNotFoundError):
        repository.get_by_id("missing")


def test_save_raises_typed_on_duplicate_run_id(
    repository: PostgresRunRepository,
) -> None:
    metadata = _make_metadata()
    repository.save(metadata)
    with pytest.raises(RunAlreadyExistsError):
        repository.save(metadata)
