"""ReplaySnapshotPort — Rekonstruktion von `ReplaySample`-Sequenzen
aus persistierten Telemetrie-Zeitreihen (`GG-MVP-002`/`GG-REPLAY-*`,
M7 Welle 1b-a, ADR 0048).

Driven-Port-Vertrag fuer die **Lese-/Rekonstruktions-Seite** des
deterministischen Replay: aus den in Welle 1a (`TelemetrySinkPort`,
ADR 0047) persistierten `telemetry_points` wird die
`ReplaySample`-Sequenz eines Laufs rekonstruiert — genau die Form,
die `diff_replay()` (`hexagon/core/replay/diff.py`, `GG-REPLAY-007`)
als `expected`/`actual` konsumiert. Welle 1b-a liefert das Protocol
+ einen `PostgresReplaySnapshotAdapter`; die Verdrahtung in einen
Lauf-Lifecycle-Hook ist **Welle 1b-b** (ADR 0049) — dieser Port
traegt **keinen** Core-Kwarg.

Vertrag (ADR 0048 §2):

- `read_samples(run_id)` liefert die `ReplaySample`-Sequenz eines
  Laufs in **deterministischer Insertion-Reihenfolge** (dieselbe
  `ORDER BY id`-Basis wie `TelemetrySinkPort.read_ordered`).
- **Timestamp-Derivation (D-1.1):** `ReplaySample.timestamp` wird
  deterministisch aus `simulation_time` abgeleitet
  (`str(simulation_time)`), **nicht** aus Wall-Clock-Werten — sonst
  waere der Self-Replay byte-instabil (`GG-REPLAY-002`; ADR 0048
  §2.2).
- **`import_sequence`** ist die 0-basierte Enumeration ueber die
  Insertion-Reihenfolge (`GG-REPLAY-003`-Tie-Break); diff-volatil.

`ReplaySample` ist der Core-Domain-Typ (`core.domain.replay`) —
AC-PORTS-NO-OUT-konform (Praezedenz `TelemetrySinkPort` →
`core.domain.telemetry`).
"""

from __future__ import annotations

from typing import Protocol

from grid_gym.hexagon.core.domain.replay import ReplaySample


class ReplaySnapshotPort(Protocol):
    """Driven-Port fuer die Rekonstruktion von `ReplaySample`-
    Sequenzen aus persistierten Telemetrie-Zeitreihen (ADR 0048).

    Implementationen MUESSEN deterministisch sein: zwei Laeufe
    desselben Szenarios (gleicher Seed/`tick_ms`/Szenario) liefern
    strukturell identische `ReplaySample`-Sequenzen → leerer
    `diff_replay()`. `value` kommt byte-stabil zurueck (1a-`TEXT`-
    `str(Decimal)`-Round-Trip), `timestamp` deterministisch aus
    `simulation_time` abgeleitet.
    """

    def read_samples(self, run_id: str) -> tuple[ReplaySample, ...]:
        """Rekonstruiert die `ReplaySample`-Sequenz eines Laufs in
        Insertion-Reihenfolge.

        Leeres Tupel, wenn der Lauf keine Telemetrie persistiert
        hat. `import_sequence` ist die 0-basierte Position in der
        Insertion-Reihenfolge; `timestamp` ist `str(simulation_time)`.
        """
        ...
