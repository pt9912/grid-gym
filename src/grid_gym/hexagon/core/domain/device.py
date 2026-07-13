"""Geraete-Tick-Interaktions-Modelle (M2 Welle 1, `GG-DEV-001`).

`DeviceTickContext` und `DeviceTickOutcome` sind reine
Daten-Frozen-Dataclasses: Eingabe und Ausgabe je Tick einer
`DeviceModel`-Implementation (`hexagon/core/devices/_protocol.py`).

**Bewusste Auslassungen** (ADR 0013):

- Kein `random_sub_port: RandomPort`-Feld. `RandomPort` kommt
  einmalig ueber `DeviceModel.initialize(...)` an das Geraet und
  wird dort als Instanz-Zustand gehalten. Damit bleibt
  `hexagon/core/domain/**` frei von Port-Importen — die M1-
  Konvention "Domain ist pure Daten" wird nicht gebrochen.
- Kein `pending_commands`-Feld. Per Architecture §6 Datenfluss-
  Schritt 5 ruft der TickLoop **erst** `apply_command(cmd)` pro
  Pending-Command, **dann** `tick(context)`. Command-State ist
  zum Zeitpunkt von `tick()` bereits angewendet; das Context-
  Objekt traegt nur Sim-Zeit-Information.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint


@dataclass(frozen=True, slots=True)
class DeviceTickContext:
    """Eingabe fuer einen `DeviceModel.tick(...)`-Aufruf.

    Felder:
    - `tick` — laufende Tick-Nummer ab Lauf-Beginn (`0`-basiert).
    - `simulation_time` — Sim-Zeit in ms zum Zeitpunkt des Tick-
      Aufrufs. Identisch mit `tick * tick_ms`, aber explizit
      geliefert, damit Geraete nicht selbst multiplizieren muessen.
    - `tick_ms` — konfigurierte Tick-Dauer in ms (`GG-SIM-002`,
      Whitelist 10/100/1000); fuer Energie-/SOC-Updates noetig
      (Leistung mal Dauer ergibt Energie).
    - `grid_voltage_v` — aktuelle Netzspannung (V) aus dem
      `GridModelBilanz` (M8-Welle-3c-b-1, ADR 0063 §2.1). Der TickLoop
      reicht die Spannung des **vorigen** Ticks durch (`grid_model.update`
      laeuft erst nach der Iteration → lagged, deterministisch ohne
      Iteration). `None` = keine Spannungsinformation (kein `grid_model`
      bzw. Standalone); ein Q(U)-Geraet emittiert dann kein Q. Bestands-
      Geraete (ohne Q(U)) ignorieren das Feld → bit-genau.
    """

    tick: int
    simulation_time: int
    tick_ms: int
    grid_voltage_v: Decimal | None = None


@dataclass(frozen=True, slots=True)
class DeviceTickOutcome:
    """Ausgabe eines `DeviceModel.tick(...)`-Aufrufs.

    Felder:
    - `telemetry` — Tupel mit `TelemetryPoint`-Eintraegen, die im
      aktuellen Tick erzeugt wurden. Reihenfolge ist deterministisch
      sortiert (nach Metrikname; Sortierung ist Geraete-
      Verantwortung, der TickLoop konkateniert ueber Geraete).

    Welle-1-Minimum: nur `telemetry`. Welle 3 (Fault-Injection)
    erweitert dies via ADR-Folge-Form um `alarms`/`fault_signals`-
    Tupel; M2 Welle 1..5 nutzen ausschliesslich das Telemetrie-Feld.
    """

    telemetry: tuple[TelemetryPoint, ...]


@dataclass(frozen=True, slots=True)
class DeviceStatus:
    """Operativer Fault-Status eines Geraets fuer einen Tick (Slice 077 S2,
    ADR 0077 §2.5).

    Reine Daten-Projektion der `FaultSurfaceDevice`-Read-Properties
    (`available`/`fault_status`) — **kein** `TelemetryPoint` (die
    Fault-Surface ist bewusst kein Telemetrie-Punkt, ADR 0077 §2.5).
    Der `TickLoop` sammelt je Tick einen `DeviceStatus` pro
    fault-surface-faehigem Geraet in `TickResult.emitted_device_status`;
    der bess-ems-Feldvertrags-Encoder (ADR 0078 §2.2) liest daraus die
    Envelope-Felder `available`/`fault_status`.

    Felder:
    - `device_id` — Geraete-Identitaet (`DeviceModel.device_id`).
    - `available` — `True` gdw. kein Fault aus dem `available`-Closed-Set
      aktiv ist.
    - `fault_status` — aktiver Fault-Typ-String, sonst `"ok"`.
    """

    device_id: str
    available: bool
    fault_status: str
