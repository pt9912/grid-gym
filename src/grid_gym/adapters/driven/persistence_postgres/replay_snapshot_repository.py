"""Postgres-Implementation des `ReplaySnapshotPort` (M7 Welle 1b-a,
ADR 0048).

Rekonstruiert `ReplaySample`-Sequenzen aus der in Welle 1a
persistierten `telemetry_points`-Tabelle (ADR 0047). **Keine
eigene Tabelle/Migration** (ADR 0048 §2.3): der Adapter liest
dieselbe Tabelle wie `PostgresTelemetrySinkAdapter`, nur in die
`ReplaySample`-Domain-Form gemappt. Nutzt `psycopg` (synchron)
ueber den injizierten `connection_factory` — Pattern identisch zu
`PostgresTelemetrySinkAdapter`.

Vertrag (ADR 0048 §2.2):

- `read_samples(run_id)`: `SELECT ... ORDER BY id` (gleiche
  Insertion-Order-Basis wie `read_ordered`); pro Zeile ein
  `ReplaySample`.
- `value` per `Decimal(...)` verlustfrei aus dem `TEXT`-Feld.
- `import_sequence` = 0-basierte Enumeration ueber die `id`-Order.
- `timestamp` = `str(simulation_time)` (deterministisch, NICHT
  Wall-Clock; byte-stabiler Self-Replay-Vertrag).
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Any, Final

import psycopg
from psycopg import sql

from grid_gym.hexagon.core.domain.replay import ReplaySample

_TABLE: Final[sql.Identifier] = sql.Identifier("telemetry_points")

# Nur die fuer ReplaySample relevanten Spalten; `id` steuert die
# Sortierung (ORDER BY), `import_sequence` wird aus der Position
# abgeleitet (nicht aus einer Spalte).
_COLUMNS: Final[tuple[str, ...]] = (
    "simulation_time",
    "device_id",
    "metric",
    "value",
    "unit",
)


class PostgresReplaySnapshotAdapter:
    """`ReplaySnapshotPort`-Implementation auf `psycopg`-Basis
    (ADR 0048).

    `connection_factory` liefert pro Aufruf eine frische
    `psycopg.Connection` (Closure ueber den DSN), analog
    `PostgresTelemetrySinkAdapter`.
    """

    def __init__(self, connection_factory: Callable[[], psycopg.Connection]) -> None:
        self._connection_factory = connection_factory

    def read_samples(self, run_id: str) -> tuple[ReplaySample, ...]:
        """Rekonstruiert die `ReplaySample`-Sequenz eines Laufs in
        Insertion-Reihenfolge (`ORDER BY id`).

        `import_sequence` ist die 0-basierte Position; `timestamp`
        wird deterministisch aus `simulation_time` abgeleitet.
        """
        statement = sql.SQL("SELECT {columns} FROM {table} WHERE run_id = %s ORDER BY id").format(
            columns=sql.SQL(", ").join(sql.Identifier(c) for c in _COLUMNS),
            table=_TABLE,
        )
        with self._connection_factory() as conn, conn.cursor() as cursor:
            cursor.execute(statement, (run_id,))
            rows = cursor.fetchall()
        return tuple(
            _row_to_sample(row, import_sequence) for import_sequence, row in enumerate(rows)
        )


def _row_to_sample(row: tuple[Any, ...], import_sequence: int) -> ReplaySample:
    """Rekonstruiert ein `ReplaySample` aus einer DB-Zeile.

    `timestamp` deterministisch aus `simulation_time` (ADR 0048
    §2.2); `value` per `Decimal(str)` verlustfrei; `import_sequence`
    aus der Enumeration der `id`-geordneten Zeilen.
    """
    simulation_time = int(row[0])
    return ReplaySample(
        timestamp=str(simulation_time),
        simulation_time=simulation_time,
        device_id=str(row[1]),
        metric=str(row[2]),
        value=Decimal(str(row[3])),
        unit=str(row[4]),
        import_sequence=import_sequence,
    )
