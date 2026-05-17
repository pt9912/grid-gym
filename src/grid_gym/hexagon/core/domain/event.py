"""Ereignis-Datenmodell (`GG-ARCH-005`).

Ereignisse werden ueber einen internen Event-Typ mit Simulationszeit,
Quelle, Ziel, Typ, Payload und Sequenznummer verarbeitet
(`GG-ARCH-005`). Welle 3 fuegt den deterministischen Scheduler mit
Tie-Breaking `(time, priority, source, sequence, event_id)`
(`GG-ARCH-006`) — die Felder hier sind die Eingangsmenge dieses
Sortier-Tupels.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Event:
    """Ein internes Simulations-Ereignis.

    Felder gemaess `GG-ARCH-005`:
    - `event_id`: stabile Ereignis-Identitaet (UUID-String); letztes
      Tie-Breaking-Glied im Scheduler.
    - `simulation_time`: Faellig-Zeit in ms.
    - `source`/`target`: emittierende/empfangende Modul-Identitaeten;
      `target` darf bei Broadcast-Ereignissen leer sein (`""`).
    - `type`: fachlicher Ereignistyp (Welle 1 trifft keine Aussage
      zum Wertebereich; Geraetemodelle/Scheduler in M2+/Welle 3
      schaerfen das).
    - `payload`: Ereignis-Parameter; gleicher canonical-Vertrag wie
      `Command.payload`.
    - `priority`: Sortierfeld (kleiner = frueher), `0` als
      Default-Mid-Range. Wertebereich bleibt offen bis Welle 3.
    - `sequence`: Einfuege-Reihenfolge im Scheduler (`GG-ARCH-006`).
    """

    event_id: str
    simulation_time: int
    source: str
    target: str
    type: str
    payload: Mapping[str, object]
    priority: int
    sequence: int
