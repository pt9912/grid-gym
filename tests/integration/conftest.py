"""Shared Fixtures fuer Integration-Tests (M2 Welle 6c).

`postgres_dsn` spawnt einen ephemeren Postgres-Container fuer
das gesamte Test-Modul und rollt das `runs`-Schema via Alembic
auf. Mehrere Test-Module (Welle-1-Repository + Welle-6c-MVP-
Demo) teilen sich diese Instanz pro Modul.

Welle-6c-Refactor (`M2-devices.md §3 Welle 6c`): die Fixture lag
zuvor lokal in `test_postgres_run_repository.py` und wurde nach
hier hochgezogen, damit `test_mvp_demo_scenario.py` sie ohne
Duplikation nutzen kann. `test-runner`-Container mountet weiterhin
`/var/run/docker.sock` (Sibling-Container-Mode, kein
docker-in-docker).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def postgres_dsn() -> Iterator[tuple[str, str]]:
    """Spawnt einen Postgres-Container fuer das ganze Test-Modul.

    Liefert ein Tupel `(psycopg_dsn, sqlalchemy_url)`:
    - `psycopg_dsn` (`postgresql://...`) fuer `psycopg.connect`.
    - `sqlalchemy_url` (`postgresql+psycopg://...`) fuer
      alembic/SQLAlchemy 2.x mit psycopg3-Dialect.
    """
    with PostgresContainer("postgres:16-alpine") as postgres:
        # testcontainers liefert per Default `postgresql+psycopg2://`
        # (alter Dialect-Name). psycopg3 nutzt
        # `postgresql+psycopg://`; psycopg.connect kommt mit
        # `postgresql://` aus (kein Dialect-Praefix).
        raw_url = postgres.get_connection_url()
        sqlalchemy_url = raw_url.replace("postgresql+psycopg2://", "postgresql+psycopg://")
        psycopg_dsn = raw_url.replace("postgresql+psycopg2://", "postgresql://")
        _run_alembic_upgrade(sqlalchemy_url)
        yield (psycopg_dsn, sqlalchemy_url)


def _run_alembic_upgrade(sqlalchemy_url: str) -> None:
    """Wendet alle Alembic-Migrationen auf das ephemere Schema an."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", sqlalchemy_url)
    command.upgrade(config, "head")
