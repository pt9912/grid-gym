"""Command-Validatoren + `EvChargerAlarm` (ADR 0055 §2.6).

EV-Charger akzeptiert zwei `Command.type`-Werte:

- `set_charge_power` (`payload={"value": Decimal}` in kW): steuert die
  Soll-Leistung am Anschlusspunkt. Sign-Konvention (ADR 0055 §2.2):
  `> 0` = Laden, `< 0` = V2G-Entladen.
- `set_plug_state` (`payload={"value": str}` in `{"plugged",
  "unplugged"}`): steuert den Stecker-Zustand.

`set_charge_power`-Vertrag (ADR 0055 §2.6):

- `unplugged` ODER aktiver `connection_loss`-Fault → `REJECTED`
  (Soll unveraendert; kein Alarm — ein nicht-ladebereiter Anschluss
  ist ein erwarteter Betriebszustand, kein Grenzwert-Verstoss).
- Sonst **grobe** Cap-Pruefung gegen `[-max_discharge_kw,
  +max_charge_kw]`: ausserhalb → `LIMITED` (Clamp auf den Cap +
  Alarm), sonst `ACCEPTED`.
- **Die SoC-/Kennlinien-abhaengige Begrenzung passiert NICHT hier,
  sondern pro Tick** (ADR 0055 §2.8) — sonst clampte ein gehaltenes
  Command gegen einen veralteten SoC.

`set_plug_state`-Vertrag (ADR 0055 §2.6):

- `→ unplugged` setzt `pending_power_kw = 0` (Re-Aktivierung nach
  `plugged` braucht ein neues `set_charge_power`).
- `→ plugged` aktiviert den Anschluss, ohne die Soll-Leistung zu
  setzen.
- Strukturell ungueltiger `value` (fehlend / kein String / nicht im
  Enum) → `IGNORED` (Validierung am Adapter-Rand; analog Battery).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.devices.ev_charger.config import (
    PLUG_STATE_PLUGGED,
    PLUG_STATE_UNPLUGGED,
    PLUG_STATES,
    EvChargerConfig,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult

_ZERO = Decimal(0)

COMMAND_TYPE_SET_CHARGE_POWER = "set_charge_power"
"""ADR 0055 §2.6: Lade-/V2G-Soll-Leistung am Anschlusspunkt."""

COMMAND_TYPE_SET_PLUG_STATE = "set_plug_state"
"""ADR 0055 §2.6: Stecker-Zustand `plugged`/`unplugged`."""

_PAYLOAD_VALUE_KEY = "value"


@dataclass(frozen=True, slots=True)
class EvChargerAlarm:
    """EV-Charger-Alarm-Eintrag (5-Feld-Schema, strukturgleich zu
    `BatteryAlarm`/`GridConnectionAlarm` — damit der TickLoop-
    Alarm-Mapper die Power-Device-Familie konsolidiert erfasst,
    ADR 0040 Decision 15).

    Welle-2a emittiert Alarme ausschliesslich beim `LIMITED`-Clamp
    eines `set_charge_power`-Commands gegen den groben Cap
    (`limit` = geklemmter Cap, `limit_unit="kW"`). Der `REJECTED`-
    Pfad (unplugged/connection_loss) emittiert **keinen** Alarm.
    """

    target_device_id: str
    limit: Decimal
    limit_unit: str
    result: CommandResult
    command_id: str


@dataclass(frozen=True, slots=True)
class EvChargerCommandOutcome:
    """Ergebnis eines Command-Validators.

    `pending_power_kw is None` → kein neuer Soll-Wert (Aufrufer
    behaelt den bisherigen). `plug_state is None` → kein neuer
    Stecker-Zustand. `alarm is None` → kein Alarm zu emittieren.
    """

    result: CommandResult
    pending_power_kw: Decimal | None
    plug_state: str | None
    alarm: EvChargerAlarm | None


def validate_set_charge_power(
    *,
    config: EvChargerConfig,
    plug_state: str,
    connection_loss_active: bool,
    command: Command,
    device_id: str,
) -> EvChargerCommandOutcome:
    """Validiert einen `set_charge_power`-Command gegen Config +
    Plug-/Fault-Zustand (ADR 0055 §2.6)."""
    if command.type != COMMAND_TYPE_SET_CHARGE_POWER:
        return _ignored_outcome()

    payload: Mapping[str, object] | None = command.payload
    if payload is None:
        return _ignored_outcome()

    raw_value = payload.get(_PAYLOAD_VALUE_KEY)
    if not isinstance(raw_value, Decimal):
        return _ignored_outcome()

    if plug_state == PLUG_STATE_UNPLUGGED or connection_loss_active:
        # Erwarteter Betriebszustand → REJECTED ohne Alarm.
        return EvChargerCommandOutcome(
            result=CommandResult.REJECTED,
            pending_power_kw=None,
            plug_state=None,
            alarm=None,
        )

    clamped = _clamp_to_caps(raw_value, config)
    if clamped is not None:
        return _limited_outcome(clamped, command, device_id)

    return EvChargerCommandOutcome(
        result=CommandResult.ACCEPTED,
        pending_power_kw=raw_value,
        plug_state=None,
        alarm=None,
    )


def validate_set_plug_state(*, command: Command) -> EvChargerCommandOutcome:
    """Validiert einen `set_plug_state`-Command (ADR 0055 §2.6).

    `→ unplugged` setzt `pending_power_kw = 0` (Auto-Stopp);
    `→ plugged` aktiviert den Anschluss ohne Soll-Aenderung.
    Strukturell ungueltiger `value` → `IGNORED`.
    """
    if command.type != COMMAND_TYPE_SET_PLUG_STATE:
        return _ignored_outcome()

    payload: Mapping[str, object] | None = command.payload
    if payload is None:
        return _ignored_outcome()

    raw_value = payload.get(_PAYLOAD_VALUE_KEY)
    if not isinstance(raw_value, str) or raw_value not in PLUG_STATES:
        return _ignored_outcome()

    if raw_value == PLUG_STATE_UNPLUGGED:
        return EvChargerCommandOutcome(
            result=CommandResult.ACCEPTED,
            pending_power_kw=_ZERO,
            plug_state=PLUG_STATE_UNPLUGGED,
            alarm=None,
        )
    return EvChargerCommandOutcome(
        result=CommandResult.ACCEPTED,
        pending_power_kw=None,
        plug_state=PLUG_STATE_PLUGGED,
        alarm=None,
    )


def _clamp_to_caps(value: Decimal, config: EvChargerConfig) -> Decimal | None:
    """Liefert den geklemmten Cap, wenn `value` ausserhalb von
    `[-max_discharge_kw, +max_charge_kw]` liegt; sonst `None`
    (kein Clamp). Das Vorzeichen disambiguiert Lade-Cap (positiv)
    vs. V2G-Entlade-Cap (negativ)."""
    if value > config.max_charge_kw:
        return config.max_charge_kw
    if value < -config.max_discharge_kw:
        return -config.max_discharge_kw
    return None


def _ignored_outcome() -> EvChargerCommandOutcome:
    return EvChargerCommandOutcome(
        result=CommandResult.IGNORED,
        pending_power_kw=None,
        plug_state=None,
        alarm=None,
    )


def _limited_outcome(clamped: Decimal, command: Command, device_id: str) -> EvChargerCommandOutcome:
    alarm = EvChargerAlarm(
        target_device_id=device_id,
        limit=clamped,
        limit_unit="kW",
        result=CommandResult.LIMITED,
        command_id=command.command_id,
    )
    return EvChargerCommandOutcome(
        result=CommandResult.LIMITED,
        pending_power_kw=clamped,
        plug_state=None,
        alarm=alarm,
    )


__all__ = [
    "COMMAND_TYPE_SET_CHARGE_POWER",
    "COMMAND_TYPE_SET_PLUG_STATE",
    "EvChargerAlarm",
    "EvChargerCommandOutcome",
    "validate_set_charge_power",
    "validate_set_plug_state",
]
