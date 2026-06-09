"""In-Memory-`ReplaySnapshotPort`-Implementation (M7 Welle 1b-b,
ADR 0049 §2.2 / ADR 0048 §2.2).

Rekonstruiert `ReplaySample`-Sequenzen aus einem
`TelemetrySinkPort`-Store (Demo-/Test-Pfad: `InMemoryTelemetrySink`)
ueber **dieselbe** `TelemetryPoint → ReplaySample`-Mapping-
Konvention wie der `PostgresReplaySnapshotAdapter` (ADR 0048 §2.2):

- `value` direkt (bereits `Decimal`; in-memory keine TEXT-Stufe).
- `import_sequence` = 0-basierte Enumeration ueber die Insertion-
  Reihenfolge (`read_ordered`).
- `timestamp` = `str(simulation_time)` (deterministisch, NICHT
  Wall-Clock; byte-stabiler Self-/Zwei-Lauf-Replay).

`PostgresReplaySnapshotAdapter` (`persistence_postgres/`) ist die
Postgres-Variante; beide erfuellen denselben `ReplaySnapshotPort`-
Vertrag mit identischer Mapping-Konvention.
"""

from __future__ import annotations

from grid_gym.hexagon.core.domain.replay import (
    ReplaySample,
    replay_sample_from_point,
)
from grid_gym.hexagon.ports.driven.telemetry_sink import TelemetrySinkPort


class InMemoryReplaySnapshot:
    """`ReplaySnapshotPort`-Implementation ueber einen
    `TelemetrySinkPort`-Store (ADR 0049).

    Liest die persistierten `TelemetryPoint`s eines Laufs via
    `read_ordered` (Insertion-Reihenfolge) und mappt sie auf
    `ReplaySample`s.
    """

    def __init__(self, source: TelemetrySinkPort) -> None:
        self._source = source

    def read_samples(self, run_id: str) -> tuple[ReplaySample, ...]:
        """Rekonstruiert die `ReplaySample`-Sequenz eines Laufs in
        Insertion-Reihenfolge; `import_sequence` ist die 0-basierte
        Position, `timestamp` = `str(simulation_time)`."""
        points = self._source.read_ordered(run_id)
        return tuple(
            replay_sample_from_point(point, import_sequence)
            for import_sequence, point in enumerate(points)
        )
