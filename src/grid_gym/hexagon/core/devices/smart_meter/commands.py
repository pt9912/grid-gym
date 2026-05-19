"""`SmartMeterAlarm` (ADR 0018 §2.6).

SmartMeter hat in Welle-4b-Minimum **keinen produktiven
Command-Surface** — beliebige `Command.type` → `IGNORED`
(ADR 0013 §2.3). Der Drain-Pfad (`drain_alarms()`, Welle-2-
Review M-3-Spiegel) ist trotzdem vorhanden, weil
Forward-Looking-Erweiterungen (z. B.
`set_aggregate_scope`-Command in Post-MVP) Alarme erzeugen
koennten.
"""

from __future__ import annotations

from dataclasses import dataclass

from grid_gym.hexagon.core.domain.command_result import CommandResult


@dataclass(frozen=True, slots=True)
class SmartMeterAlarm:
    """SmartMeter-Alarm-Eintrag (analog `PvAlarm`/`GridConnectionAlarm`).

    Felder:
    - `target_device_id` — Zielgeraet.
    - `reason` — Frei-Text-Begruendung (z. B. fuer Forward-
      Looking-Erweiterungen). Welle 4b nutzt diesen Pfad nicht
      aktiv.
    - `result` — `CommandResult` des ausloesenden Befehls.
    - `command_id` — Bezug zum ausloesenden `Command`.
    """

    target_device_id: str
    reason: str
    result: CommandResult
    command_id: str


__all__ = [
    "SmartMeterAlarm",
]
