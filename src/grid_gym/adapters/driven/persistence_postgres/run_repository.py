"""Postgres-Implementation des `RunRepositoryPort` (M1 Welle 6c).

Nutzt `psycopg` (synchron) gegen das `runs`-Schema aus
`migrations/versions/0001_create_runs.py`. Jeder Call oeffnet
eine eigene Connection ueber den injizierten
`connection_factory` — Pool-/Long-Lived-Connections kommen in
einem spaeteren Slice, sobald die `/runs`-API HTTP-Traffic
sieht.

Vertrag:
- `save(metadata)` macht ein `INSERT`. Bei `UNIQUE`-Verstoss
  (Postgres `23505`) wird der Fehler in
  `RunAlreadyExistsError` uebersetzt — die Boundary-Translation
  haelt den `psycopg.errors.UniqueViolation` aus der Domain raus.
- `get_by_id(run_id)` macht ein `SELECT`; leere Antwort →
  `RunNotFoundError`.
- `exists(run_id)` ist ein `SELECT 1`-Existenz-Check (cheaper
  als full row fetch).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

import psycopg
from psycopg import sql

from grid_gym.hexagon.core.domain.run import (
    RunMetadata,
    RunStatus,
    canonical_enabled_adapters,
)
from grid_gym.hexagon.core.errors import (
    NonCanonicalEnabledAdaptersError,
    RunAlreadyExistsError,
    RunNotFoundError,
)

_UNIQUE_VIOLATION_SQLSTATE: Final[str] = "23505"
"""Postgres SQLSTATE fuer `UNIQUE`-Constraint-Verletzung."""

_TABLE: Final[sql.Identifier] = sql.Identifier("runs")


def _encode_enabled_adapters(names: tuple[str, ...]) -> str:
    """Kanonisches Tupel → komma-separierter Persistenz-String
    (Slice 038 / ADR 0073 §2.3). Leeres Tupel → ``""`` (fehlend).

    Slice-038-Review-Folge: validiert die Kanonik an der
    Persistenz-Grenze (typisierter Reject statt stiller
    Round-Trip-Asymmetrie), falls ein Schreiber die
    `canonical_enabled_adapters`-Konvention umgeht.
    """
    if canonical_enabled_adapters(names) != names:
        raise NonCanonicalEnabledAdaptersError(names)
    return ",".join(names)


def _decode_enabled_adapters(raw: str) -> tuple[str, ...]:
    """Komma-separierter Persistenz-String → Tupel. ``""`` → ``()``
    (fehlend; Round-Trip-Symmetrie zu `_encode_enabled_adapters`).

    Slice-038-Review-Folge: unkanonischer DB-Bestand (unsortiert,
    Duplikate, Leersegmente, ungueltige Namen — nur via Fremd-
    Schreiber/manuelles SQL erreichbar) wird typisiert rejected
    statt still in die Core-Domain gehoben.
    """
    if not raw:
        return ()
    names = tuple(raw.split(","))
    if canonical_enabled_adapters(names) != names:
        raise NonCanonicalEnabledAdaptersError(raw)
    return names


class PostgresRunRepository:
    """`RunRepositoryPort`-Implementation auf `psycopg`-Basis.

    Der `connection_factory` ist ein Callable, das pro Call eine
    neue `psycopg.Connection` liefert — typischerweise eine kleine
    Closure ueber den DSN-String. Welle 6c nutzt das so, weil eine
    Pool-Layer-Entscheidung (`psycopg_pool` vs. eigenes Setup) noch
    nicht fixiert ist; bei der ersten produktiven Last-Welle
    aktualisiert eine Folge-ADR den Connection-Lifecycle.
    """

    def __init__(self, connection_factory: Callable[[], psycopg.Connection]) -> None:
        self._connection_factory = connection_factory

    def save(self, metadata: RunMetadata) -> None:
        """Persistiert einen Lauf.

        Uebersetzt `psycopg.errors.UniqueViolation` (`SQLSTATE
        23505`) in `RunAlreadyExistsError` — Aufrufer pruefen
        typisiert, nicht ueber Postgres-Fehler-Klassen.
        """
        try:
            with self._connection_factory() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        sql.SQL(
                            "INSERT INTO {table} ("
                            "run_id, scenario_hash, schema_version, seed, "
                            "tick_ms, started_at, ended_at, tool_version, replay_of, "
                            "platform_arch, enabled_adapters, sim_start_time, config_hash"
                            ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        ).format(table=_TABLE),
                        (
                            metadata.run_id,
                            metadata.scenario_hash,
                            metadata.schema_version,
                            metadata.seed,
                            metadata.tick_ms,
                            metadata.started_at,
                            metadata.ended_at,
                            metadata.tool_version,
                            metadata.replay_of,
                            metadata.platform_arch,
                            _encode_enabled_adapters(metadata.enabled_adapters),
                            metadata.sim_start_time,
                            metadata.config_hash,
                        ),
                    )
                conn.commit()
        except psycopg.errors.UniqueViolation as exc:
            raise RunAlreadyExistsError(metadata.run_id) from exc

    def get_by_id(self, run_id: str) -> RunMetadata:
        """Liest die Laufmetadaten zu einem `run_id`.

        Wirft `RunNotFoundError` bei leerer Ergebnismenge.
        """
        with self._connection_factory() as conn, conn.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "SELECT run_id, scenario_hash, schema_version, seed, "
                    "tick_ms, started_at, ended_at, tool_version, replay_of, "
                    "platform_arch, enabled_adapters, sim_start_time, config_hash "
                    "FROM {table} WHERE run_id = %s"
                ).format(table=_TABLE),
                (run_id,),
            )
            row = cursor.fetchone()
        if row is None:
            raise RunNotFoundError(run_id)
        return RunMetadata(
            run_id=row[0],
            scenario_hash=row[1],
            schema_version=row[2],
            seed=row[3],
            tick_ms=row[4],
            started_at=row[5],
            ended_at=row[6],
            tool_version=row[7],
            replay_of=row[8],
            platform_arch=row[9],
            enabled_adapters=_decode_enabled_adapters(row[10]),
            sim_start_time=row[11],
            config_hash=row[12],
        )

    def exists(self, run_id: str) -> bool:
        """`SELECT 1`-Existenz-Check (kein Full-Row-Fetch)."""
        with self._connection_factory() as conn, conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT 1 FROM {table} WHERE run_id = %s LIMIT 1").format(table=_TABLE),
                (run_id,),
            )
            return cursor.fetchone() is not None

    def ping(self) -> bool:
        """Readiness-Probe via ``SELECT 1`` (M6 Welle 6, `GG-DEPLOY-006`).

        Oeffnet eine frische Connection ueber den `connection_factory`
        und fuehrt ``SELECT 1`` aus (tabellen-unabhaengig — prueft die
        reine Postgres-Erreichbarkeit, nicht das `runs`-Schema). Gibt
        ``True`` zurueck, wenn der Roundtrip erfolgreich ist.
        Connection-/Query-Fehler propagieren als `psycopg`-Exception
        an den `/ready`-Adapter, der sie auf ``unhealthy`` mappt.
        """
        with self._connection_factory() as conn, conn.cursor() as cursor:
            cursor.execute(sql.SQL("SELECT 1"))
            return cursor.fetchone() is not None

    def update_status(self, run_id: str, status: RunStatus) -> None:
        """M5 Welle 4a (ADR 0039 Decision 12) — Status-Persistenz-Stub.

        Welle 4a aktualisiert das `RunRepositoryPort`-Protocol um
        ``update_status``/``get_status``; die produktive Postgres-
        Status-Spalte folgt mit M3-Welle-6c (Schema-Migration +
        Alembic-Revision). Welle-4a-Stand: Methode wirft
        ``NotImplementedError``, damit Protocol-Konformitaet
        gewahrt bleibt; produktive Runs laufen ueber den
        `InMemoryRunRepository`-Lifespan-Setup, der den State
        in-memory haelt.
        """
        raise NotImplementedError(
            "PostgresRunRepository.update_status awaits M3-Welle-6c Postgres-"
            "status column migration. Use InMemoryRunRepository for M5-Welle-4a "
            "demo wiring."
        )

    def get_status(self, run_id: str) -> RunStatus:
        """M5 Welle 4a (ADR 0039 Decision 12) — Status-Lese-Stub.

        Siehe ``update_status`` fuer die Welle-6c-Verschiebungs-
        Begruendung; Methode wirft ``NotImplementedError``.
        """
        raise NotImplementedError(
            "PostgresRunRepository.get_status awaits M3-Welle-6c Postgres-"
            "status column migration. Use InMemoryRunRepository for M5-Welle-4a "
            "demo wiring."
        )
