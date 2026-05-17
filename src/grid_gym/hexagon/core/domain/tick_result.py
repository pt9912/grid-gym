"""`TickResult` — Ergebnis eines einzelnen `TickLoop.tick()`-Aufrufs
(M1 Welle 4).

Frozen-Dataclass mit den deterministisch sortierten Outputs eines
Ticks: gepoppte Events aus dem `Scheduler` und (in Welle 4 noch
leeres) emittiertes Telemetry-Tupel. Geraetemodelle in M2 fuellen
`emitted_telemetry` mit konkreten `TelemetryPoint`-Eintraegen.

Konvention:
- `tick` ist die **gerade abgeschlossene** Tick-Nummer (0-basiert,
  startet bei `0` fuer den ersten `tick()`-Aufruf eines frisch
  initialisierten `TickLoop`s).
- `simulation_time` ist die Sim-Zeit *nach* `ClockPort.advance`,
  also die Zeitgrenze, gegen die `Scheduler.pop_due` aufgerufen
  wurde — alle Events in `popped_events` haben
  `event.simulation_time <= simulation_time`.
- `tuple` statt `list` fuer beide Sequenzfelder, damit
  AC-DOMAIN-FROZEN strukturell erfuellt ist (Frozen-Dataclass
  + immutable Felder).
"""

from __future__ import annotations

from dataclasses import dataclass

from grid_gym.hexagon.core.domain.event import Event
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint


@dataclass(frozen=True, slots=True)
class TickResult:
    """Ergebnis eines `TickLoop.tick()`-Aufrufs (`GG-SIM-001`/`002`).

    Felder:
    - `tick`: gerade abgeschlossene Tick-Nummer (0-basiert).
    - `simulation_time`: Zeitgrenze nach `ClockPort.advance`,
      gegen die der Scheduler gepoppt wurde.
    - `popped_events`: deterministisch sortiertes Tupel der vom
      `Scheduler` gepoppten Events (`GG-ARCH-006`-Tie-Breaking).
    - `emitted_telemetry`: Telemetry-Punkte aus
      Geraete-Tick-Ausgaben. In Welle 4 ohne Geraete: leeres Tupel.
    """

    tick: int
    simulation_time: int
    popped_events: tuple[Event, ...]
    emitted_telemetry: tuple[TelemetryPoint, ...]
