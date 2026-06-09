"""Postgres-Implementation des `ReplaySnapshotPort` (M7 Welle 1b-a,
ADR 0048).

Rekonstruiert `ReplaySample`-Sequenzen aus der in Welle 1a
persistierten `telemetry_points`-Tabelle. **Keine eigene Tabelle/
Migration** (ADR 0048 §2.3): der Adapter liest die persistierten
`TelemetryPoint`s ueber denselben Sink-Lesepfad
(`PostgresTelemetrySinkAdapter.read_ordered`, `ORDER BY id` =
Insertion-Reihenfolge) und mappt sie via der geteilten
`replay_sample_from_point`-Factory.

**C2-Review-Folge F5:** sowohl die `TelemetryPoint→ReplaySample`-
Mapping-Konvention (Domain-Factory) als auch der Roh-Zeilen-Lesepfad
(Sink) sind jetzt Single-Source — Postgres- und In-Memory-Replay-
Snapshot koennen nicht mehr auseinanderdriften.
"""

from __future__ import annotations

from collections.abc import Callable

import psycopg

from grid_gym.adapters.driven.persistence_postgres.telemetry_sink_repository import (
    PostgresTelemetrySinkAdapter,
)
from grid_gym.hexagon.core.domain.replay import (
    ReplaySample,
    replay_sample_from_point,
)


class PostgresReplaySnapshotAdapter:
    """`ReplaySnapshotPort`-Implementation auf `psycopg`-Basis
    (ADR 0048).

    `connection_factory` liefert pro Aufruf eine frische
    `psycopg.Connection` (Closure ueber den DSN); intern liest der
    Adapter ueber einen `PostgresTelemetrySinkAdapter` aus derselben
    `telemetry_points`-Tabelle.
    """

    def __init__(self, connection_factory: Callable[[], psycopg.Connection]) -> None:
        self._sink = PostgresTelemetrySinkAdapter(connection_factory)

    def read_samples(self, run_id: str) -> tuple[ReplaySample, ...]:
        """Rekonstruiert die `ReplaySample`-Sequenz eines Laufs in
        Insertion-Reihenfolge (`read_ordered` = `ORDER BY id`).

        `import_sequence` ist die 0-basierte Position; `timestamp`
        wird in der Factory deterministisch aus `simulation_time`
        abgeleitet (ADR 0048 §2.2)."""
        points = self._sink.read_ordered(run_id)
        return tuple(
            replay_sample_from_point(point, import_sequence)
            for import_sequence, point in enumerate(points)
        )
