"""In-Memory-`TelemetrySinkPort`-Implementation (M7 Welle 1a,
ADR 0047).

Produktiver Demo-Pfad-Adapter fuer den Lifespan-env-var-Pfad
(`GRID_GYM_DEMO_SCENARIO_PATH`) — parallel zu
`InMemoryRunRepository`: der in-process-Demo-Lauf nutzt einen
in-memory Store (kein Postgres im Lifespan). Haelt die
persistierten `TelemetryPoint`s in Insertion-Reihenfolge in einer
Liste; der Store ueberlebt den Prozess nicht.

`PostgresTelemetrySinkAdapter` (`persistence_postgres/`) ist die
Postgres-Variante fuer den Integration-Smoke und ein kuenftiges
Postgres-backed Deployment; beide erfuellen denselben
`TelemetrySinkPort`-Vertrag (append-only + Insertion-geordnetes
`read_ordered`).
"""

from __future__ import annotations

from collections.abc import Sequence

from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint


class InMemoryTelemetrySink:
    """`TelemetrySinkPort`-Implementation mit list-basiertem Store.

    Append-only: `persist` haengt die Batch in Insertion-Reihenfolge
    an; `read_ordered` liefert die Punkte eines Laufs in genau
    dieser Reihenfolge (reproduziert die deterministische
    `emitted_telemetry`-Reihenfolge). Kein `UPDATE`/`DELETE`.
    """

    def __init__(self) -> None:
        self._points: list[TelemetryPoint] = []

    def persist(self, points: Sequence[TelemetryPoint]) -> None:
        self._points.extend(points)

    def read_ordered(self, run_id: str) -> tuple[TelemetryPoint, ...]:
        return tuple(point for point in self._points if point.run_id == run_id)
