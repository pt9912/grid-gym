"""Command-Validator + `PvAlarm` (ADR 0016 §2.4).

PV akzeptiert `Command.type == "set_power_kw"` mit Payload
`{"value": Decimal}`. Validierung folgt Welle-2-Review-Pattern
(M-7 payload-None-Defensive, M-8 Wertebereich-Pruefung VOR
Power-Clamp):

- `value < 0`: REJECTED + Alarm (`limit=0`, `limit_unit="kW"`)
  — Sign-Vertrag verletzt (PV erzeugt nicht-negativ).
- `value > rated_power_kw`: LIMITED + Alarm
  (`limit=rated_power_kw`, `limit_unit="kW"`) — clamp.
- Sonst: ACCEPTED, `pending_power_kw = value`.

Mehrfach-Commands im selben Tick: last-wins (ADR 0014 §2.3
spiegelt).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.devices.pv.config import PvConfig
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult

_ZERO = Decimal(0)
COMMAND_TYPE_SET_POWER_KW = "set_power_kw"
"""Welle-3-PV-Vertrag: einziger akzeptierter `Command.type`."""

_PAYLOAD_VALUE_KEY = "value"


@dataclass(frozen=True, slots=True)
class PvAlarm:
    """PV-Alarm-Eintrag (analog `BatteryAlarm`, ADR 0014 §2.5).

    Felder:
    - `target_device_id` — Zielgeraet.
    - `limit` — verletzter Grenzwert (`0` fuer Sign-Verstoss,
      `rated_power_kw` fuer Power-Clamp).
    - `limit_unit` — Einheit des Grenzwerts (in Welle 3 immer
      `"kW"`).
    - `result` — `CommandResult` des ausloesenden Befehls
      (`LIMITED` oder `REJECTED`).
    - `command_id` — Bezug zum ausloesenden `Command`.

    **Disambiguation (Welle-3-Review M-2):** Der `limit=0`-Wert ist
    NICHT mehrdeutig — er erscheint ausschliesslich zusammen mit
    `result=REJECTED` (Sign-Vertrag-Verstoss). `limit=rated_power_kw`
    erscheint ausschliesslich mit `result=LIMITED` (Power-Clamp).
    Welle-6-TickLoop und M3-AlarmSinkPort sollen IMMER `(result,
    limit)` als Tupel auswerten, nicht `limit` alleine. Welle 4
    SmartMeter (eigene ADR 0017) kann das Pattern uebernehmen.
    """

    target_device_id: str
    limit: Decimal
    limit_unit: str
    result: CommandResult
    command_id: str


@dataclass(frozen=True, slots=True)
class CommandValidationOutcome:
    """Ergebnis von `validate_set_power_command`."""

    result: CommandResult
    pending_power_kw: Decimal | None
    alarm: PvAlarm | None


def validate_set_power_command(
    *,
    config: PvConfig,
    command: Command,
    device_id: str,
) -> CommandValidationOutcome:
    """Validiert einen `set_power_kw`-Command gegen `PvConfig`
    (ADR 0016 §2.4)."""
    if command.type != COMMAND_TYPE_SET_POWER_KW:
        return _ignored_outcome()

    payload: Mapping[str, object] | None = command.payload
    if payload is None:
        return _ignored_outcome()

    raw_value = payload.get(_PAYLOAD_VALUE_KEY)
    if not isinstance(raw_value, Decimal):
        return _ignored_outcome()

    # Sign-Vertrag-Pruefung VOR Power-Clamp (Welle-2-Review-M-8-
    # Spiegelung).
    if raw_value < _ZERO:
        return _rejected_outcome(_ZERO, command, device_id)

    if raw_value > config.rated_power_kw:
        return _limited_outcome(config.rated_power_kw, command, device_id)

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
    alarm = PvAlarm(
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


def _rejected_outcome(limit: Decimal, command: Command, device_id: str) -> CommandValidationOutcome:
    alarm = PvAlarm(
        target_device_id=device_id,
        limit=limit,
        limit_unit="kW",
        result=CommandResult.REJECTED,
        command_id=command.command_id,
    )
    return CommandValidationOutcome(
        result=CommandResult.REJECTED,
        pending_power_kw=None,
        alarm=alarm,
    )


__all__ = [
    "COMMAND_TYPE_SET_POWER_KW",
    "CommandValidationOutcome",
    "PvAlarm",
    "validate_set_power_command",
]
