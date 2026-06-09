"""Postgres-Driven-Adapter (`GG-PERSIST-001`/`003`/`009`, M1 Welle 6c).

Liefert die produktive `RunRepositoryPort`-Implementation auf
`psycopg`-Basis. Welle 6b hatte den Port + InMemory-Fake; Welle 6c
bringt die Postgres-Persistenz und das alembic-Schema.

Modul-Re-Export: `PostgresRunRepository` (Laufmetadaten/Status,
Welle 6c) + `PostgresTelemetrySinkAdapter` (Telemetrie-Zeitreihen,
M7 Welle 1a / ADR 0047) + `PostgresReplaySnapshotAdapter`
(`ReplaySample`-Rekonstruktion aus `telemetry_points`, M7 Welle
1b-a / ADR 0048).
"""

from __future__ import annotations

from grid_gym.adapters.driven.persistence_postgres.replay_snapshot_repository import (
    PostgresReplaySnapshotAdapter,
)
from grid_gym.adapters.driven.persistence_postgres.run_repository import (
    PostgresRunRepository,
)
from grid_gym.adapters.driven.persistence_postgres.telemetry_sink_repository import (
    PostgresTelemetrySinkAdapter,
)

__all__ = [
    "PostgresReplaySnapshotAdapter",
    "PostgresRunRepository",
    "PostgresTelemetrySinkAdapter",
]
