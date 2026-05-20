"""Integration-Test fuer `PostgresRunRepository` (M1 Welle 6c).

Nutzt `testcontainers[postgres]`, um pro Test eine ephemere
Postgres-Instanz hochzufahren. `alembic upgrade head` rollt das
`runs`-Schema ein; danach laeuft der Welle-1-`RunMetadata`-
Roundtrip plus typisierte Negativ-Pfade.

Der `make test-integration`-Stack mounted den Docker-Socket vom
Host in den Test-Runner-Container — testcontainers spawnt
Postgres ueber diesen Socket als Sibling-Container (nicht
docker-in-docker).

Die `postgres_dsn`-Fixture ist seit M2 Welle 6c modul-uebergreifend
in `tests/integration/conftest.py` (gemeinsame Nutzung mit
`test_mvp_demo_scenario.py`).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator

import psycopg
import pytest

from grid_gym.adapters.driven.persistence_postgres import PostgresRunRepository
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.errors import (
    RunAlreadyExistsError,
    RunNotFoundError,
)


@pytest.fixture
def repository(
    postgres_dsn: tuple[str, str],
) -> Iterator[PostgresRunRepository]:
    """Frisches Repository pro Test — Tabelle wird zwischen Tests
    geleert, damit Reihenfolge unabhaengig bleibt."""
    psycopg_dsn, _ = postgres_dsn
    factory: Callable[[], psycopg.Connection] = lambda: psycopg.connect(psycopg_dsn)
    _truncate_runs(factory)
    yield PostgresRunRepository(connection_factory=factory)


def _truncate_runs(factory: Callable[[], psycopg.Connection]) -> None:
    with factory() as conn, conn.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE runs")
        conn.commit()


def _make_metadata(run_id: str | None = None) -> RunMetadata:
    return RunMetadata(
        run_id=run_id or str(uuid.uuid4()),
        scenario_hash="0" * 64,
        schema_version="grid-gym.scenario.v1",
        seed=42,
        tick_ms=100,
        started_at="2026-05-17T10:00:00Z",
        ended_at="2026-05-17T10:01:00Z",
        tool_version="0.1.0",
    )


# ---------------------------------------------------------------------------
# Happy-Path
# ---------------------------------------------------------------------------


def test_save_then_get_by_id_roundtrips_all_fields(repository: PostgresRunRepository) -> None:
    metadata = _make_metadata()
    repository.save(metadata)
    loaded = repository.get_by_id(metadata.run_id)
    assert loaded == metadata


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
