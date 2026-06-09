"""In-Memory-Driven-Adapter fuer `RunRepositoryPort` (M5 Welle 5).

Welle-5-Aufloesung des `PostgresRunRepository.update_status`/
`get_status`-`NotImplementedError`-Stubs (Welle-4a-Entscheidung
M3-Welle-6c-Verschiebung): der Welle-5-Demo-Pfad
(`make demo` + `python -m grid_gym demo` + Lifespan-env-var-Pfad)
braucht eine produktive `RunRepositoryPort`-Implementation, die
den Lifecycle-Status haelt — Postgres bleibt ohne Status-Spalte
bis M3-Welle-6c. Pattern parallel zu `alarm_stream_inmemory`
(Welle 4b) — beide leben unter `adapters/driven/` und sind die
heute einzige nicht-Stub-Implementation ihres Ports.

Modul-Re-Export: `InMemoryRunRepository` ist die einzige
oeffentliche API dieses Pakets. Tests koennen entweder den
Test-Fake unter ``tests/unit/hexagon/ports/driven/_fakes.py``
nutzen (substanzgleich, eigene Test-Doku) oder direkt diesen
produktiven Adapter — beide Varianten erfuellen den
`RunRepositoryPort`-Vertrag (siehe
``hexagon/ports/driven/run_repository.py``).
"""

from __future__ import annotations

from grid_gym.adapters.driven.persistence_inmemory.replay_snapshot import (
    InMemoryReplaySnapshot,
)
from grid_gym.adapters.driven.persistence_inmemory.run_repository import (
    InMemoryRunRepository,
)
from grid_gym.adapters.driven.persistence_inmemory.telemetry_sink import (
    InMemoryTelemetrySink,
)


__all__ = ["InMemoryReplaySnapshot", "InMemoryRunRepository", "InMemoryTelemetrySink"]
