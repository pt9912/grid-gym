"""Unified `Alarm`-Domain-Type + Severity-/Status-Literals (M5
Welle 4b, ADR 0040 Decision 15).

Welle-4b-Domain-Slot fuer den Alarm-Schluesseltyp. Die 5 device-
spezifischen Raw-Alarm-Familien
(`BatteryAlarm`/`PvAlarm`/`LoadAlarm`/`GridConnectionAlarm`/
`SmartMeterAlarm` in `hexagon/core/devices/*/commands.py`)
bleiben unveraendert; die Mapper-Funktionen, die sie auf diesen
Unified-Type abbilden, leben in
`hexagon/core/simulation/alarm_mappers.py` (Welle-4b-C2-
Realization-Note: dort, weil sie `core.devices` importieren und
damit nicht in `hexagon/core/domain/` bleiben koennen, ohne dass
`AC-PORTS-NO-OUT` durch Transitiv-Importe von
`hexagon/ports/driving/alarm_stream.py` reisst).

**Hexagonal-Rationale:** dieses Modul ist pure Domain — keine
Imports aus `core/devices/` oder `core/simulation/`; ausschliesslich
Domain-Primitives. Der Schluessel-Type `Alarm` plus die zwei
`Literal`-Aliases sind die Surface, die `hexagon/ports/driving/
alarm_stream.py` + Adapter-Schemas (`AlarmDto`) konsumieren.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AlarmSeverity = Literal["info", "warning", "critical"]
"""Welle-4b-Hierarchie (3 Werte; OTel-/syslog-aehnlich):

- `info` — reserviert, Welle-4b hat keine produktive Quelle.
- `warning` — Power-Clamp (`LIMITED`) oder SmartMeter-Reject.
- `critical` — Command-Reject (`REJECTED`) bei Battery/PV/Load/
  GridConnection.

Literal-Erweiterung ist additiv und braucht keinen Schema-Bruch.
"""

AlarmStatus = Literal["active"]
"""Welle-4b: nur `active`. Lifecycle-Erweiterung
(`acknowledged`/`resolved`) ist Welle 6+/M6-Material (ADR 0040
§4 Out-of-Scope). Literal-Erweiterung waere additiv."""


@dataclass(frozen=True, slots=True)
class Alarm:
    """Unified Alarm-Domain-Type (kanonisches 9-Feld-Schema per
    [`spec/architecture.md §Alarm`](../../../../../spec/architecture.md),
    M5 Welle 4b, ADR 0040 Decision 15).

    Felder:

    - `alarm_id` — UUIDv4-String; eindeutig pro Alarm.
    - `run_id` — Lauf-Identitaet (`GG-DATA-001`).
    - `simulation_time_ms` — Tick-Zeitpunkt in ms (ab Lauf-Start).
    - `target` — Zielgeraet-ID (= `target_device_id` des raw-
      Alarms).
    - `code` — Stabile Fehler-ID (z. B. `power_clamp_limited`,
      `command_rejected`, `smart_meter_rejected`).
    - `severity` — 3-Werte-Hierarchie aus `AlarmSeverity`.
    - `message` — Mensch-lesbare Beschreibung.
    - `status` — Welle-4b: immer `"active"` (Lifecycle-Erweiterung
      Welle 6+/M6).
    - `fault_id` — Optional; Welle-4b immer `None` (Fault-
      Injection-Mapping ist Welle 6+/M6-Material).
    """

    alarm_id: str
    run_id: str
    simulation_time_ms: int
    target: str
    code: str
    severity: AlarmSeverity
    message: str
    status: AlarmStatus
    fault_id: str | None


__all__ = [
    "Alarm",
    "AlarmSeverity",
    "AlarmStatus",
]
