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
from decimal import Decimal


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


@dataclass(frozen=True, slots=True)
class GridConstraintViolationEvent:
    """Pro-Tick-Laufzeit-Event einer Netz-Constraint-Verletzung
    (M8 Welle 3b, ADR 0061 §2.3).

    **Kein** Scheduler-`Event` (nicht eingeplant, sondern pro Tick aus
    `GridModelBilanz.update(...)` emittiert) und **kein** Config-
    Construction-Error (die Grenzwert-Config-Validierung ist davon
    getrennt). Frozen + immutable (AC-DOMAIN-FROZEN). Transientes
    Tick-Output (kein Snapshot-State; re-derived je Tick).

    Felder:
    - `constraint`: Kennung der verletzten Grenze
      (`"transformer_hot_spot"` in Welle 3b).
    - `simulation_time`: Sim-Zeit (ms) des ausloesenden Ticks.
    - `apparent_power_kva`: Scheinleistung am Modell-Trafo
      (`S ≈ |grid_connection_kw|` bis 3c; ADR 0061 §2.2).
    - `limit_kva`: Nennscheinleistung `max_apparent_power_kva` (Basis
      fuer `load_pu`).
    - `top_oil_temp_c` / `hot_spot_temp_c`: Thermo-Zustand zum Tick.
    - `hot_spot_limit_c`: ueberschrittene Ausloese-Schwelle.
    """

    constraint: str
    simulation_time: int
    apparent_power_kva: Decimal
    limit_kva: Decimal
    top_oil_temp_c: Decimal
    hot_spot_temp_c: Decimal
    hot_spot_limit_c: Decimal


CONSTRAINT_TRANSFORMER_HOT_SPOT = "transformer_hot_spot"
"""ADR 0061 §2.3: `GridConstraintViolationEvent.constraint`-Wert fuer die
Transformer-Hot-Spot-Ausloesung (einzige Verletzung in Welle 3b)."""
