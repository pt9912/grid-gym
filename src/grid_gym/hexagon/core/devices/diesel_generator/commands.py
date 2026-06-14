"""Command-Validator + `DieselGeneratorAlarm` (ADR 0058 §2.6).

Diesel akzeptiert `Command.type == "set_power_kw"` mit Payload
`{"value": Decimal}` (Soll-Leistung in kW). Generator-Vertrag (ADR 0058
§2.2): nur Erzeugung, `power_kw >= 0`.

- `value < 0`: `LIMITED` auf `0` + Alarm (Generator kann nicht absorbieren).
- `value > max_power_kw`: `LIMITED` auf `max_power_kw` + Alarm.
- Sonst: `ACCEPTED`, `pending_power_kw = value`.

Die Hysterese-/Ramp-/Kraftstoff-Begrenzung passiert pro Tick
(ADR 0058 §2.4/§2.5), nicht hier. Strukturell ungueltig (falscher
`Command.type`, fehlender/nicht-numerischer `value`) → `IGNORED`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.devices.diesel_generator.config import DieselGeneratorConfig
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult

_ZERO = Decimal(0)
COMMAND_TYPE_SET_POWER_KW = "set_power_kw"
"""Welle-2d-Diesel-Vertrag: einziger akzeptierter `Command.type`."""

_PAYLOAD_VALUE_KEY = "value"


@dataclass(frozen=True, slots=True)
class DieselGeneratorAlarm:
    """Diesel-Alarm-Eintrag (5-Feld-Schema, strukturgleich zu
    `BatteryAlarm` — konsolidierter Power-Device-Alarm-Mapper,
    ADR 0040 Decision 15). `limit`-Vorzeichen/-Wert disambiguiert
    Unter-0-Clamp (`0`) vs. Ueber-Max-Clamp (`max_power_kw`)."""

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
    alarm: DieselGeneratorAlarm | None


def validate_set_power_command(
    *,
    config: DieselGeneratorConfig,
    command: Command,
    device_id: str,
) -> CommandValidationOutcome:
    """Validiert einen `set_power_kw`-Command gegen `[0, max_power_kw]`
    (ADR 0058 §2.6)."""
    if command.type != COMMAND_TYPE_SET_POWER_KW:
        return _ignored_outcome()

    payload: Mapping[str, object] | None = command.payload
    if payload is None:
        return _ignored_outcome()

    raw_value = payload.get(_PAYLOAD_VALUE_KEY)
    if not isinstance(raw_value, Decimal):
        return _ignored_outcome()

    if raw_value < _ZERO:
        return _limited_outcome(_ZERO, command, device_id)
    if raw_value > config.max_power_kw:
        return _limited_outcome(config.max_power_kw, command, device_id)

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
    alarm = DieselGeneratorAlarm(
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
    "DieselGeneratorAlarm",
    "validate_set_power_command",
]
