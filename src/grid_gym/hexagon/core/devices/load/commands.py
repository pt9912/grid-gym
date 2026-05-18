"""Command-Validator + `LoadAlarm` (ADR 0016 §2.4).

Load akzeptiert `Command.type == "set_power_kw"` mit Payload
`{"value": Decimal}`. Validierung spiegelt PV:

- `value < 0`: REJECTED + Alarm (`limit=0`, `limit_unit="kW"`)
  — Sign-Vertrag verletzt (Load verbraucht nicht-negativ).
- `value > rated_power_kw`: LIMITED + Alarm
  (`limit=rated_power_kw`, `limit_unit="kW"`).
- Sonst: ACCEPTED.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.devices.load.config import LoadConfig
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult

_ZERO = Decimal(0)
COMMAND_TYPE_SET_POWER_KW = "set_power_kw"
_PAYLOAD_VALUE_KEY = "value"


@dataclass(frozen=True, slots=True)
class LoadAlarm:
    """Load-Alarm-Eintrag (analog `BatteryAlarm`/`PvAlarm`)."""

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
    alarm: LoadAlarm | None


def validate_set_power_command(
    *,
    config: LoadConfig,
    command: Command,
    device_id: str,
) -> CommandValidationOutcome:
    """Validiert einen `set_power_kw`-Command gegen `LoadConfig`
    (ADR 0016 §2.4)."""
    if command.type != COMMAND_TYPE_SET_POWER_KW:
        return _ignored_outcome()

    payload: Mapping[str, object] | None = command.payload
    if payload is None:
        return _ignored_outcome()

    raw_value = payload.get(_PAYLOAD_VALUE_KEY)
    if not isinstance(raw_value, Decimal):
        return _ignored_outcome()

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
    alarm = LoadAlarm(
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
    alarm = LoadAlarm(
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
    "LoadAlarm",
    "validate_set_power_command",
]
