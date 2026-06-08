"""TelemetrySinkPort — append-only Zeitreihen-Persistenz fuer
Telemetriepunkte (`GG-PERSIST-001`, M7 Welle 1a, ADR 0047).

Driven-Port-Vertrag fuer das append-only Persistieren der pro Tick
emittierten `TelemetryPoint`-Zeitreihen + ein deterministisch
geordnetes Lese-API. Welle 1a liefert das Protocol + einen
`PostgresTelemetrySinkAdapter`; der Core-`TickLoop` haelt den Port
als keyword-only-Kwarg und persistiert `TickResult.emitted_telemetry`
pro Tick aus dem Spine (Driven-Port-Konvention analog
`RunRepositoryPort`, ADR 0039 / ADR 0047 §2.3).

Vertrag (ADR 0047 §2.1):

- `persist(points)` ist **append-only** (kein `UPDATE`/`DELETE`)
  und **batch** (eine `Sequence` pro Tick). Leere Sequenz ist ein
  No-op.
- `read_ordered(run_id)` liefert alle Punkte eines Laufs in
  **Insertion-Reihenfolge** — die exakt die deterministische
  `emitted_telemetry`-Reihenfolge (Device-Major x Per-Device-
  `sequence`) reproduziert (ADR 0047 §2.1/§2.4). `value` ist
  byte-stabil ueber `str(Decimal)` round-getrippt.

`TelemetryPoint` ist der Core-Domain-Typ (`core.domain.telemetry`,
`GG-DATA-001`) — **nicht** das gleichnamige Driving-Stream-DTO.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint


class TelemetrySinkPort(Protocol):
    """Driven-Port fuer append-only Telemetrie-Zeitreihen-Persistenz
    (`GG-PERSIST-001`, ADR 0047).

    Implementationen MUESSEN append-only + deterministisch sein:
    `persist`-te Punkte kommen ueber `read_ordered` in derselben
    Insertion-Reihenfolge und strukturell gleich zurueck (Frozen-
    Dataclass-Roundtrip; `value` byte-stabil per `str(Decimal)`).
    """

    def persist(self, points: Sequence[TelemetryPoint]) -> None:
        """Persistiert eine Batch von Telemetriepunkten append-only.

        Eine leere `Sequence` ist ein No-op. Reihenfolge der
        `points` wird als Insertion-Reihenfolge bewahrt (relevant
        fuer `read_ordered` + den Welle-1b-Replay-Diff). Kein
        `UPDATE`/`DELETE` — wiederholtes `persist` haengt an.
        """
        ...

    def read_ordered(self, run_id: str) -> tuple[TelemetryPoint, ...]:
        """Liest alle Telemetriepunkte eines Laufs in Insertion-
        Reihenfolge (reproduziert die deterministische
        `emitted_telemetry`-Reihenfolge des Laufs).

        Leeres Tupel, wenn der Lauf keine Punkte persistiert hat.
        """
        ...
