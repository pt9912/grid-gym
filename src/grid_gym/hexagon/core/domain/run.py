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

`RunStatus` (M5 Welle 4a, ADR 0039 Decision 12) ist der orthogonale
Run-Lifecycle-State, der ausserhalb der Frozen-`RunMetadata` lebt:
das Repository haelt ihn als zweiten Lookup neben den Metadaten,
damit die Reproduzierbarkeits-Hash-Stabilitaet aus `RunMetadata`
nicht durch mutable Status-Felder gebrochen wird.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


RunStatus = Literal["pending", "running", "paused", "stopped", "completed"]
"""Lifecycle-Status eines Simulationslaufs (M5 Welle 4a, ADR 0039
Decision 12).

- ``pending``  — Run persistiert, Tick-Driver noch nicht gestartet.
- ``running``  — Tick-Driver aktiv; ``tick()`` fortschreitet.
- ``paused``   — Tick-Driver aktiv, aber Pre-Tick-Guard blockt.
- ``stopped``  — Final-Terminierung durch Benutzer.
- ``completed``— Final-Terminierung durch Tick-Loop-Ende oder
  Lifespan-Shutdown.

Welle-1-`RunState`-Alias in `_schemas.py` zeigt auf denselben
Literal-Set (Re-Export). Die fuenf Werte sind die kanonische
Vokabel fuer alle Welle-4a-Schichten (Domain, Repository, HTTP-API,
UI-CSS-Klassen).
"""


ControlAction = Literal["pause", "resume", "stop"]
"""Control-Action-Vokabel (M5-Welle-4a, ADR 0037 Decision API-1 + ADR
0039 Decision 13), gespiegelt aus dem HTTP-`ControlRequest`-Body.
Verschoben aus `core.simulation.tick_loop` in 041-C2 (ADR 0050 §2.3),
damit der `RunExecutionPort` sie ohne `core.simulation`-Import
referenzieren kann (`AC-ADAPTER-PURE`). `RunExecutionPort.request(action)`
und `TickLoop.request(action)` dispatchen ueber diesen Literal."""


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
    - `replay_of`: optionale, persistente Referenz auf den
      Lauf, dessen Replay dieser Lauf ist (Trigger 039 / ADR 0068).
      `None` = regulaerer Lauf (kein Replay). Die Bindung haengt
      damit auditierbar am Lauf statt nur als Runtime-Kwarg
      (`replay_reference_run_id`, ADR 0049 §2.2). Default `None`
      haelt bestehende Konstruktionen byte-stabil.
    """

    run_id: str
    scenario_hash: str
    schema_version: str
    seed: int
    tick_ms: int
    started_at: str
    ended_at: str
    tool_version: str
    replay_of: str | None = None
