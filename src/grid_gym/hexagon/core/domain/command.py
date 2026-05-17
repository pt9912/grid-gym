"""Steuerbefehl-Datenmodell (`GG-DATA-004`).

Jeder Steuerbefehl endet in genau einem `CommandResult`. Welle 1
modelliert den abgeschlossenen Befehl als Frozen-Dataclass; eine
„in-Flight"-Repraesentation (z. B. `result=None`) ist explizit
Out-of-Scope — der Tick-Loop legt einen `Command`-Eintrag erst beim
Commit an.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from grid_gym.hexagon.core.domain.command_result import CommandResult


@dataclass(frozen=True, slots=True)
class Command:
    """Ein Steuerbefehl an ein Geraet.

    Felder:
    - `command_id`: stabile Befehls-Identitaet (UUID-String).
    - `simulation_time`: Sim-Zeit des Befehlseinlangens in ms.
    - `target_device_id`: Zielgeraet.
    - `type`: fachlicher Kommando-Typ (z. B. `"set_power_setpoint"`);
      Welle 1 trifft keine Aussage zum erlaubten Wertebereich —
      Geraetemodelle in M2+ schaerfen das per eigenem Typ-Vertrag.
    - `payload`: Kommando-Parameter; `Mapping[str, object]` ist der
      Vertrag mit `canonical_json` (akzeptiert
      `None|bool|int|Decimal|str|dict|list|tuple`) — Werte ausserhalb
      des Wertebereichs feuern `UnsupportedTypeError` an der
      Serialisierungsgrenze, nicht hier.
    - `validation_status`: Vor-Validierung am Adapter-Rand
      (frei, z. B. `"validated"`/`"pending"`); Geraetemodelle in M2+
      schaerfen das ebenfalls.
    - `result`: Endstatus (`GG-DATA-004`).
    """

    command_id: str
    simulation_time: int
    target_device_id: str
    type: str
    payload: Mapping[str, object]
    validation_status: str
    result: CommandResult
