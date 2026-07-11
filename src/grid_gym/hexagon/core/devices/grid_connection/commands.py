"""Command-Validator + `GridConnectionAlarm` (ADR 0017 §2.4).

GridConnection akzeptiert `Command.type == "set_power_kw"` mit
Payload `{"value": Decimal}`. Validierung folgt Welle-2/3-Review-
Pattern (M-7 payload-None-Defensive, M-2/L-3 Alarm-Tupel mit
`limit_unit`):

- `value > max_import_kw`: LIMITED + Alarm
  (`limit=max_import_kw`, `limit_unit="kW"`) — Import-Clamp.
- `value < -max_export_kw`: LIMITED + Alarm
  (`limit=-max_export_kw`, `limit_unit="kW"`) — Export-Clamp.
- Sonst: ACCEPTED, `pending_power_kw = value`.

**Kein REJECTED-Pfad fuer Vorzeichen** (ADR 0017 §2.4) — beide
Vorzeichen sind valide (Import / Export). REJECTED greift nur
strukturell (fehlender `value`-Key, nicht-numerisch).
Mehrfach-Commands im selben Tick: last-wins (ADR 0014 §2.3
spiegelt).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.devices.grid_connection.config import (
    GridConnectionConfig,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult

COMMAND_TYPE_SET_POWER_KW = "set_power_kw"
"""Welle-4a-GridConnection-Vertrag: einziger akzeptierter
`Command.type` (analog PV/Load)."""

_PAYLOAD_VALUE_KEY = "value"


@dataclass(frozen=True, slots=True)
class GridConnectionAlarm:
    """GridConnection-Alarm-Eintrag (analog `PvAlarm`/`BatteryAlarm`).

    Felder:
    - `target_device_id` — Zielgeraet.
    - `limit` — verletzter Grenzwert (positiver `max_import_kw`
      bei Import-Clamp, negativer `-max_export_kw` bei
      Export-Clamp).
    - `limit_unit` — Einheit des Grenzwerts (Welle 4a immer `"kW"`).
    - `result` — `CommandResult` des ausloesenden Befehls
      (in Welle 4a nur `LIMITED`; kein `REJECTED`-Pfad fuer
      Vorzeichen).
    - `command_id` — Bezug zum ausloesenden `Command`.

    Disambiguation (Welle-3-Review M-2-Pattern): das Vorzeichen
    von `limit` disambiguiert Import-Clamp (positiv) vs.
    Export-Clamp (negativ). `(result, limit)` als Tupel
    auswerten, nicht `limit` alleine.
    """

    target_device_id: str
    limit: Decimal
    limit_unit: str
    result: CommandResult
    command_id: str


@dataclass(frozen=True, slots=True)
class GridConnectionFaultAlarm:
    """GridConnection-Netz-Fault-Alarm (M8/GG-FAULT-004).

    Getrennt vom Power-Clamp-`GridConnectionAlarm` (5-Feld-Schema mit
    `limit`/`result`), weil ein Netz-Fault (`frequency_drop`,
    perspektivisch `voltage_drop`) keinen Command-Kontext hat. Der Alarm
    wird beim Fault-Beginn (`inject_fault`) in die Device-`_alarms`-Liste
    gehoben und ueber die bestehende `drain_alarms`-Pipeline vom TickLoop
    gemapped (`alarm_from_grid_connection_fault_alarm`).

    Felder:
    - `target_device_id` — Zielgeraet (= Zielnetz-Anschlusspunkt).
    - `fault_type` — kanonischer Fault-Typ (`frequency_drop`).
    - `detail` — mensch-lesbare Beschreibung (fliesst in `Alarm.message`).
    """

    target_device_id: str
    fault_type: str
    detail: str


@dataclass(frozen=True, slots=True)
class CommandValidationOutcome:
    """Ergebnis von `validate_set_power_command`."""

    result: CommandResult
    pending_power_kw: Decimal | None
    alarm: GridConnectionAlarm | None


def validate_set_power_command(
    *,
    config: GridConnectionConfig,
    command: Command,
    device_id: str,
) -> CommandValidationOutcome:
    """Validiert einen `set_power_kw`-Command gegen `GridConnection
    Config` (ADR 0017 §2.4)."""
    if command.type != COMMAND_TYPE_SET_POWER_KW:
        return _ignored_outcome()

    payload: Mapping[str, object] | None = command.payload
    if payload is None:
        return _ignored_outcome()

    raw_value = payload.get(_PAYLOAD_VALUE_KEY)
    if not isinstance(raw_value, Decimal):
        return _ignored_outcome()

    if raw_value > config.max_import_kw:
        return _limited_outcome(config.max_import_kw, command, device_id)

    export_floor = -config.max_export_kw
    if raw_value < export_floor:
        return _limited_outcome(export_floor, command, device_id)

    return CommandValidationOutcome(
        result=CommandResult.ACCEPTED,
        pending_power_kw=raw_value,
        alarm=None,
    )


def _ignored_outcome() -> CommandValidationOutcome:
    return CommandValidationOutcome(result=CommandResult.IGNORED, pending_power_kw=None, alarm=None)


def _limited_outcome(
    clamped: Decimal, command: Command, device_id: str
) -> CommandValidationOutcome:
    alarm = GridConnectionAlarm(
        target_device_id=device_id,
        limit=clamped,
        limit_unit="kW",
        result=CommandResult.LIMITED,
        command_id=command.command_id,
    )
    return CommandValidationOutcome(
        result=CommandResult.LIMITED,
        pending_power_kw=clamped,
        alarm=alarm,
    )


__all__ = [
    "COMMAND_TYPE_SET_POWER_KW",
    "CommandValidationOutcome",
    "GridConnectionAlarm",
    "GridConnectionFaultAlarm",
    "validate_set_power_command",
]
