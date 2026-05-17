"""Lauf-Metadaten (`GG-DATA-001`, `GG-SIM-003`, `GG-TERM-003`).

`RunMetadata` haelt die Reproduzierbarkeits-Metadaten eines
Simulationslaufs. Die Akzeptanz aus `GG-TERM-003` verlangt mindestens
Version, Szenario-Hash, Konfiguration, Startzeit im Simulationszeit-
modell, Seed, Tick-Groesse und aktivierte Adapter — Welle 1 deckt
den Spine ab; aktive Adapter folgen, sobald die Adapter-Schicht in
Welle 6 entsteht.

`started_at`/`ended_at` sind Wall-Clock-Zeiten in ISO-8601-UTC
(`GG-DATA-005`), nicht Simulationszeit. Simulationszeit wird in
`TelemetryPoint.simulation_time` als ganzzahlige ms gefuehrt.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunMetadata:
    """Metadaten eines reproduzierbaren Simulationslaufs.

    Felder:
    - `run_id`: stabile Lauf-Identitaet (UUID-String, Eingang).
    - `scenario_hash`: kanonischer Szenario-Hash (`GG-SCN-004`).
    - `schema_version`: Szenario-Schema-Version (z. B.
      `"grid-gym.scenario.v1"`).
    - `seed`: PRNG-Wurzelseed fuer `RandomPort` (`ADR 0007`).
    - `tick_ms`: Tick-Groesse in ms (10/100/1000 per `GG-SIM-002`).
    - `started_at`/`ended_at`: ISO-8601-UTC-Wall-Clock-Zeitstempel
      (`GG-DATA-005`); `ended_at` ist beim Lauf-Start typischerweise
      noch leer und wird erst beim Closure gesetzt — Welle 1
      modelliert nur den abgeschlossenen Eintrag.
      TODO(M1-Welle-7): in-flight-Repraesentation entscheiden —
      `ended_at: str | None` (Frozen-Equality-Verhalten beachten)
      vs. separate `RunMetadataInFlight`-Dataclass. Slice-Plan-
      Closure-Notiz traegt die Entscheidung.
    - `tool_version`: `grid_gym`-Version (Spec `GG-TERM-003`
      „Version").
    """

    run_id: str
    scenario_hash: str
    schema_version: str
    seed: int
    tick_ms: int
    started_at: str
    ended_at: str
    tool_version: str
