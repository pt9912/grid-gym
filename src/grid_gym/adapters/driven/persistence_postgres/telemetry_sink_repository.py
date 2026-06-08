"""Postgres-Implementation des `TelemetrySinkPort` (M7 Welle 1a,
ADR 0047).

Append-only Zeitreihen-Persistenz fuer `TelemetryPoint`s in die
`telemetry_points`-Tabelle (Migration `0002_create_telemetry_points`).
Nutzt `psycopg` (synchron) ueber den injizierten
`connection_factory` — Pattern identisch zu `PostgresRunRepository`
(M1 Welle 6c); eine Pool-Layer-Entscheidung kommt mit der ersten
produktiven Last-Welle.

Vertrag (ADR 0047 §2):

- `persist(points)`: batch-`INSERT` (executemany), append-only.
  Leere Sequenz → No-op. `value` als `str(Decimal)` (TEXT, byte-
  stabil); `quality` als StrEnum-Wert.
- `read_ordered(run_id)`: `SELECT ... ORDER BY id` — Insertion-
  Reihenfolge reproduziert die deterministische
  `emitted_telemetry`-Reihenfolge; `value` per `Decimal(...)`
  verlustfrei zurueck.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from decimal import Decimal
from typing import Any, Final

import psycopg
from psycopg import sql

from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint

_TABLE: Final[sql.Identifier] = sql.Identifier("telemetry_points")

_COLUMNS: Final[tuple[str, ...]] = (
    "run_id",
    "tick",
    "simulation_time",
    "device_id",
    "metric",
    "value",
    "unit",
    "quality",
    "source",
    "sequence",
)


class PostgresTelemetrySinkAdapter:
    """`TelemetrySinkPort`-Implementation auf `psycopg`-Basis
    (ADR 0047).

    `connection_factory` liefert pro Aufruf eine frische
    `psycopg.Connection` (Closure ueber den DSN), analog
    `PostgresRunRepository`.
    """

    def __init__(self, connection_factory: Callable[[], psycopg.Connection]) -> None:
        self._connection_factory = connection_factory

    def persist(self, points: Sequence[TelemetryPoint]) -> None:
        """Append-only Batch-`INSERT` der Telemetriepunkte.

        Leere Sequenz ist ein No-op (kein DB-Roundtrip). Der
        Surrogat-`id` (Identity) wird vom Schema vergeben; die
        Insertion-Reihenfolge entspricht der `points`-Reihenfolge.
        """
        if not points:
            return
        placeholders = sql.SQL(", ").join(sql.Placeholder() * len(_COLUMNS))
        statement = sql.SQL("INSERT INTO {table} ({columns}) VALUES ({values})").format(
            table=_TABLE,
            columns=sql.SQL(", ").join(sql.Identifier(c) for c in _COLUMNS),
            values=placeholders,
        )
        rows = [
            (
                point.run_id,
                point.tick,
                point.simulation_time,
                point.device_id,
                point.metric,
                str(point.value),
                point.unit,
                point.quality.value,
                point.source,
                point.sequence,
            )
            for point in points
        ]
        with self._connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(statement, rows)
            conn.commit()

    def read_ordered(self, run_id: str) -> tuple[TelemetryPoint, ...]:
        """Liest alle Punkte eines Laufs in Insertion-Reihenfolge
        (`ORDER BY id`) — reproduziert die deterministische
        `emitted_telemetry`-Reihenfolge."""
        statement = sql.SQL("SELECT {columns} FROM {table} WHERE run_id = %s ORDER BY id").format(
            columns=sql.SQL(", ").join(sql.Identifier(c) for c in _COLUMNS),
            table=_TABLE,
        )
        with self._connection_factory() as conn, conn.cursor() as cursor:
            cursor.execute(statement, (run_id,))
            rows = cursor.fetchall()
        return tuple(_row_to_point(row) for row in rows)


def _row_to_point(row: tuple[Any, ...]) -> TelemetryPoint:
    """Rekonstruiert einen `TelemetryPoint` aus einer DB-Zeile
    (`psycopg`-Tuple-Row). `value` per `Decimal(str)` verlustfrei,
    `quality` per `Quality`-StrEnum-Lookup."""
    return TelemetryPoint(
        run_id=str(row[0]),
        tick=int(row[1]),
        simulation_time=int(row[2]),
        device_id=str(row[3]),
        metric=str(row[4]),
        value=Decimal(str(row[5])),
        unit=str(row[6]),
        quality=Quality(str(row[7])),
        source=str(row[8]),
        sequence=int(row[9]),
    )
