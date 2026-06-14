"""Command-Validator + `TransformerAlarm` (ADR 0056 §2.5).

Transformer akzeptiert `Command.type == "set_power_kw"` mit Payload
`{"value": Decimal}` (Primaer-Durchsatzleistung in kW). Validierung
spiegelt das GridConnection-Muster ([`ADR 0017`] §2.4):

- `value > rated_power_kw`: `LIMITED` + Alarm (`limit=rated_power_kw`,
  Vorwaerts-Saettigung).
- `value < -rated_power_kw`: `LIMITED` + Alarm (`limit=-rated_power_kw`,
  Rueckwaerts-Saettigung).
- Sonst: `ACCEPTED`, `pending_power_kw = value`.

**Kein REJECTED-Pfad fuer das Vorzeichen** (ADR 0056 §2.2) — beide
Richtungen sind valide. REJECTED/IGNORED greift nur strukturell
(fehlender/nicht-numerischer `value`, falscher `Command.type`).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.devices.transformer.config import TransformerConfig
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult

COMMAND_TYPE_SET_POWER_KW = "set_power_kw"
"""Welle-2b-Transformer-Vertrag: einziger akzeptierter `Command.type`
(analog GridConnection/PV/Load)."""

_PAYLOAD_VALUE_KEY = "value"


@dataclass(frozen=True, slots=True)
class TransformerAlarm:
    """Transformer-Alarm-Eintrag (5-Feld-Schema, strukturgleich zu
    `BatteryAlarm`/`GridConnectionAlarm`/`EvChargerAlarm` — der
    TickLoop-Alarm-Mapper erfasst die Power-Device-Familie
    konsolidiert, ADR 0040 Decision 15).

    Welle-2b emittiert Alarme beim `LIMITED`-Clamp eines
    `set_power_kw`-Commands gegen den Saettigungs-Cap. Das Vorzeichen
    von `limit` disambiguiert Vorwaerts-Saettigung (positiv) vs.
    Rueckwaerts-Saettigung (negativ).
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
    alarm: TransformerAlarm | None


def validate_set_power_command(
    *,
    config: TransformerConfig,
    command: Command,
    device_id: str,
) -> CommandValidationOutcome:
    """Validiert einen `set_power_kw`-Command gegen den Saettigungs-Cap
    `±rated_power_kw` (ADR 0056 §2.5)."""
    if command.type != COMMAND_TYPE_SET_POWER_KW:
        return _ignored_outcome()

    payload: Mapping[str, object] | None = command.payload
    if payload is None:
        return _ignored_outcome()

    raw_value = payload.get(_PAYLOAD_VALUE_KEY)
    if not isinstance(raw_value, Decimal):
        return _ignored_outcome()

    if raw_value > config.rated_power_kw:
        return _limited_outcome(config.rated_power_kw, command, device_id)
    reverse_floor = -config.rated_power_kw
    if raw_value < reverse_floor:
        return _limited_outcome(reverse_floor, command, device_id)

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
    alarm = TransformerAlarm(
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
    "TransformerAlarm",
    "validate_set_power_command",
]
