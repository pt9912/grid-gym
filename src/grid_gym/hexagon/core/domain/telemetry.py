"""Telemetrie-Datenmodell (`GG-DATA-001`, `GG-DATA-002`).

`TelemetryPoint` ist die kanonische Repraesentation eines einzelnen
Messwerts. Die Pflichtfelder kommen 1:1 aus `GG-DATA-001`; `unit`
folgt der SI-Konvention aus `GG-DATA-002` (z. B. `"kW"`, `"kWh"`,
`"Hz"`, `"V"`, `"A"`, `"degC"`, `"pct"`).

`value` ist `Decimal` — `float` ist im canonical-Pfad verboten
(`FloatNotAllowedError`). Quantisierung auf max. 6 Nachkommastellen
(`GG-DATA-005`) ist Eingangsgrenze des Adapters/Loaders, NICHT der
Domain-Klasse selbst — der Encoder bleibt der einzige Pruefpunkt.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.domain.quality import Quality


@dataclass(frozen=True, slots=True)
class TelemetryPoint:
    """Ein Telemetriepunkt im einheitlichen Datenmodell.

    Felder gemaess `GG-DATA-001`:
    - `run_id`, `tick`, `simulation_time`, `device_id`, `metric`,
      `value`, `unit`, `quality`, `source`, `sequence`.

    `tick` ist die fortlaufende Tick-Nummer (0-basiert).
    `simulation_time` ist die Simulationszeit in ms ab Lauf-Start
    (`GG-DATA-005`).
    `source` identifiziert das emittierende Modul (z. B.
    `"battery.bess01"`); zusammen mit `sequence` definiert es das
    stabile Tie-Breaking im Scheduler (`GG-ARCH-006`).
    """

    run_id: str
    tick: int
    simulation_time: int
    device_id: str
    metric: str
    value: Decimal
    unit: str
    quality: Quality
    source: str
    sequence: int
