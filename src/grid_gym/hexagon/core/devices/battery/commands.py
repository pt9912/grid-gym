"""Command-Validator + `BatteryAlarm`-Domain (`GG-BESS-002`).

Battery akzeptiert in Welle 2 ausschliesslich
`Command.type == "set_power_kw"`. Andere Typen → `IGNORED`.

`validate_set_power_command(...)` ist eine pure Funktion ueber:
- aktueller `BatteryConfig`,
- aktuelles `soc_kwh`,
- eingehender `Command`.

Sie liefert ein `CommandValidationOutcome` mit:
- `result: CommandResult` (`ACCEPTED`/`LIMITED`/`REJECTED`/`IGNORED`).
- `pending_power_kw: Decimal | None` — neuer Soll-Wert (None bei
  `REJECTED`/`IGNORED`; `BatteryDevice` behaelt seinen alten Soll).
- `alarm: BatteryAlarm | None` — emittierter Alarm bei
  `LIMITED`/`REJECTED`.

`BatteryDevice` ruft diese Pure-Function aus `apply_command` heraus
auf und uebernimmt das Outcome in seinen internen State.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.devices.battery.config import BatteryConfig
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult

_ZERO = Decimal(0)
COMMAND_TYPE_SET_POWER_KW = "set_power_kw"
"""Welle-2-Battery-Vertrag: einziger akzeptierter `Command.type`."""

_PAYLOAD_VALUE_KEY = "value"


@dataclass(frozen=True, slots=True)
class BatteryAlarm:
    """Alarm-Eintrag (`GG-BESS-002`).

    Felder:
    - `target_device_id` — Zielgeraet (Battery, das den Alarm ausloest).
    - `limit` — verletzter Grenzwert (z. B. `max_charge_kw` oder
      `min_soc_pct`).
    - `result` — `CommandResult` des ausloesenden Befehls
      (`LIMITED` oder `REJECTED`).
    - `command_id` — Bezug zum ausloesenden `Command`.
    """

    target_device_id: str
    limit: Decimal
    result: CommandResult
    command_id: str


@dataclass(frozen=True, slots=True)
class CommandValidationOutcome:
    """Ergebnis von `validate_set_power_command(...)`.

    `pending_power_kw is None` signalisiert: kein neuer Soll-Wert
    (Aufrufer behaelt den bisherigen). `alarm is None` signalisiert:
    kein Alarm zu emittieren.
    """

    result: CommandResult
    pending_power_kw: Decimal | None
    alarm: BatteryAlarm | None


def validate_set_power_command(
    *,
    config: BatteryConfig,
    soc_kwh: Decimal,
    command: Command,
    device_id: str,
) -> CommandValidationOutcome:
    """Validiert einen `set_power_kw`-Command gegen die aktuelle
    Battery-State + Config (`GG-BESS-002`).

    Vertrag (ADR 0014 §2.3):

    - `command.type != "set_power_kw"`: `IGNORED`, kein Alarm,
      kein neuer Soll.
    - Payload `value` fehlt oder ist kein `Decimal`: `IGNORED`
      (strukturelle Vorab-Validierung am Adapter-Rand; in
      Welle 2 nicht streng abgesichert).
    - Wert ausserhalb `[-max_discharge_kw, max_charge_kw]`:
      → clampen + Alarm(limit=clamped_value, result=LIMITED).
      → `pending_power_kw = clamped_value`, Rueckgabe `LIMITED`.
    - SOC am Boden (`<= min_soc_kwh`) und Wert < 0:
      → Alarm(limit=min_soc_pct, result=REJECTED). Soll unveraendert.
    - SOC an der Decke (`>= max_soc_kwh`) und Wert > 0:
      → Alarm(limit=max_soc_pct, result=REJECTED). Soll unveraendert.
    - Sonst: `ACCEPTED`, kein Alarm, `pending_power_kw = value`.
    """
    if command.type != COMMAND_TYPE_SET_POWER_KW:
        return _ignored_outcome()

    # Welle-2-Review M-7: payload ist in Command typisiert als
    # `Mapping[str, object]`, also nie `None`-by-Type. Aufrufer
    # mit defektem Adapter koennen es trotzdem als `None`
    # uebergeben; defensiv abfangen mit lokaler Erweiterung des
    # Typs.
    payload: Mapping[str, object] | None = command.payload
    if payload is None:
        return _ignored_outcome()

    raw_value = payload.get(_PAYLOAD_VALUE_KEY)
    if not isinstance(raw_value, Decimal):
        # Welle-2-Pragmatik: strukturelle Payload-Validierung gehoert
        # an die Adapter-Grenze; bei fehlendem oder falsch-typisiertem
        # `value` schlucken wir den Command als IGNORED, statt eine
        # Exception zu werfen. Strikte Adapter koennen das schaerfen.
        return _ignored_outcome()

    # Welle-2-Review M-8: SOC-Grenz-Pruefung VOR Power-Clamp.
    # Doppelt-verletzender Command (z. B. -700 kW bei SOC-Boden)
    # geht direkt auf REJECTED, nicht auf LIMITED → Clamp-Drop.
    soc_limit = _violated_soc_limit(soc_kwh, raw_value, config)
    if soc_limit is not None:
        return _rejected_outcome(soc_limit, command, device_id)

    # Power-Limit-Pruefung — beide Pole in einer Verzweigung.
    clamped = _clamp_to_power_limits(raw_value, config)
    if clamped is not None:
        return _limited_outcome(clamped, command, device_id)

    return CommandValidationOutcome(
        result=CommandResult.ACCEPTED,
        pending_power_kw=raw_value,
        alarm=None,
    )


def _ignored_outcome() -> CommandValidationOutcome:
    return CommandValidationOutcome(result=CommandResult.IGNORED, pending_power_kw=None, alarm=None)


def _clamp_to_power_limits(value: Decimal, config: BatteryConfig) -> Decimal | None:
    """Liefert den geklemmten Wert, wenn `value` ausserhalb der
    `[-max_discharge_kw, max_charge_kw]`-Grenzen liegt; sonst
    `None` (kein Clamp noetig)."""
    if value > config.max_charge_kw:
        return config.max_charge_kw
    if value < -config.max_discharge_kw:
        return -config.max_discharge_kw
    return None


def _violated_soc_limit(soc_kwh: Decimal, value: Decimal, config: BatteryConfig) -> Decimal | None:
    """Liefert die verletzte SOC-Grenze (als prozentualen Wert),
    falls der Command die aktuelle SOC-Position weiter ueber-/
    unterschreiten wuerde; sonst `None`."""
    if soc_kwh <= config.min_soc_kwh and value < _ZERO:
        return config.min_soc_pct
    if soc_kwh >= config.max_soc_kwh and value > _ZERO:
        return config.max_soc_pct
    return None


def _limited_outcome(
    clamped: Decimal, command: Command, device_id: str
) -> CommandValidationOutcome:
    alarm = BatteryAlarm(
        target_device_id=device_id,
        limit=clamped,
        result=CommandResult.LIMITED,
        command_id=command.command_id,
    )
    return CommandValidationOutcome(
        result=CommandResult.LIMITED,
        pending_power_kw=clamped,
        alarm=alarm,
    )


def _rejected_outcome(
    soc_limit: Decimal, command: Command, device_id: str
) -> CommandValidationOutcome:
    alarm = BatteryAlarm(
        target_device_id=device_id,
        limit=soc_limit,
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
    "BatteryAlarm",
    "CommandValidationOutcome",
    "validate_set_power_command",
]
