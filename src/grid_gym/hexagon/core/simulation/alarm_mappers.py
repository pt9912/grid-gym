"""Mapper-Familie aus den 5 device-spezifischen Raw-Alarms auf den
Unified `Alarm`-Domain-Type (M5 Welle 4b, ADR 0040 Decision 15).

**Layering-Begruendung** (Welle-4b-C2-Realization-Note):
ursprunglich in `core/domain/alarm.py` integriert; per AC-PORTS-
NO-OUT-Contract darf `hexagon.ports` aber nicht transitiv auf
`hexagon.core.devices` zugreifen. Da `core/domain/alarm.py` via
`Alarm`-Import von `hexagon/ports/driving/alarm_stream.py`
konsumiert wird, mussten die device-importierenden Mapper-
Funktionen aus `core/domain/alarm.py` ausgegliedert werden. Sie
leben hier in `core/simulation/` analog zur TickLoop-Aggregations-
Sequenz (die diese Mapper produktiv aufruft).

**Hexagonal-Rationale:** Devices kennen keinen Run-Kontext
(`run_id`/`simulation_time_ms`) — der TickLoop weiss beides. Die
Mapper nehmen Run-Kontext als zusaetzliche Argumente und sind
side-effect-free (gleiche Inputs → gleiche Outputs; UUIDv4-
Source wird extern injiziert).

**Mapping-Heuristik** (ADR 0040 §2.1; Pattern aus
`PvAlarm`-Docstring `pv/commands.py:53`: „IMMER `(result, limit)`
als Tupel auswerten"):

| Device-Familie | `result` | `code` | `severity` | `message` |
| --- | --- | --- | --- | --- |
| Battery/PV/Load/GridConnection | `LIMITED` | `power_clamp_limited` | `warning` | clamp-template |
| Battery/PV/Load/GridConnection | `REJECTED` | `command_rejected` | `critical` | reject-template |
| SmartMeter | `REJECTED` | `smart_meter_rejected` | `warning` | reason-template |
"""

from __future__ import annotations

from grid_gym.hexagon.core.devices.battery.commands import BatteryAlarm
from grid_gym.hexagon.core.devices.ev_charger.commands import EvChargerAlarm
from grid_gym.hexagon.core.devices.grid_connection.commands import GridConnectionAlarm
from grid_gym.hexagon.core.devices.load.commands import LoadAlarm
from grid_gym.hexagon.core.devices.pv.commands import PvAlarm
from grid_gym.hexagon.core.devices.smart_meter.commands import SmartMeterAlarm
from grid_gym.hexagon.core.domain.alarm import Alarm, AlarmSeverity
from grid_gym.hexagon.core.domain.command_result import CommandResult


def _power_clamp_message(limit: object, limit_unit: str) -> str:
    """Welle-4b-Template fuer LIMITED-Mapping (Battery/PV/Load/
    GridConnection)."""
    return f"power command clamped to {limit} {limit_unit}"


def _power_reject_message(limit: object, limit_unit: str) -> str:
    """Welle-4b-Template fuer REJECTED-Mapping (Battery/PV/Load/
    GridConnection)."""
    return f"command rejected: limit {limit} {limit_unit}"


def _power_alarm_code_severity(
    result: CommandResult,
) -> tuple[str, AlarmSeverity]:
    """Welle-4b-Mapping `(result) → (code, severity)` fuer
    Battery/PV/Load/GridConnection."""
    if result is CommandResult.LIMITED:
        return ("power_clamp_limited", "warning")
    return ("command_rejected", "critical")


PowerDeviceAlarm = BatteryAlarm | PvAlarm | LoadAlarm | GridConnectionAlarm | EvChargerAlarm
"""Welle-4b-Union der strukturell identischen Power-Device-Alarms
(5-Feld-Schema mit `target_device_id`/`limit`/`limit_unit`/`result`/
`command_id`). M8-Welle-2a ergaenzt `EvChargerAlarm` (gleiches Schema).
SmartMeter hat ein abweichendes 4-Feld-Schema und bekommt einen
eigenen Mapper."""


def alarm_from_power_device_alarm(
    raw: PowerDeviceAlarm,
    *,
    run_id: str,
    simulation_time_ms: int,
    alarm_id: str,
) -> Alarm:
    """Mapped einen raw Power-Device-Alarm (Battery/PV/Load/
    GridConnection) auf einen Unified `Alarm` (M5 Welle 4b, ADR
    0040 Decision 15).

    Konsolidierter Mapper fuer die vier strukturell identischen
    Power-Device-Familien — alle haben das gleiche 5-Feld-Schema
    `(target_device_id, limit, limit_unit, result, command_id)`
    und die gleiche Mapping-Heuristik
    `(result, limit) → (code, severity, message)`. C2-Realization-
    Anpassung statt 4 separate Mapper-Funktionen, weil
    AC-NO-GOD-UTILS max=5 public functions pro Modul gilt.
    """
    code, severity = _power_alarm_code_severity(raw.result)
    message = (
        _power_clamp_message(raw.limit, raw.limit_unit)
        if raw.result is CommandResult.LIMITED
        else _power_reject_message(raw.limit, raw.limit_unit)
    )
    return Alarm(
        alarm_id=alarm_id,
        run_id=run_id,
        simulation_time_ms=simulation_time_ms,
        target=raw.target_device_id,
        code=code,
        severity=severity,
        message=message,
        status="active",
        fault_id=None,
    )


def alarm_from_smart_meter_alarm(
    raw: SmartMeterAlarm,
    *,
    run_id: str,
    simulation_time_ms: int,
    alarm_id: str,
) -> Alarm:
    """Mapped einen raw `SmartMeterAlarm` auf einen Unified
    `Alarm` (M5 Welle 4b, ADR 0040 Decision 15).

    SmartMeter hat kein `limit`/`limit_unit` (4-Feld-Schema mit
    `reason: str` statt). Welle-4b-Default: jeder SmartMeter-
    Alarm wird als `warning` mit `smart_meter_rejected`-Code
    klassifiziert; `reason` flows in die `message`.
    """
    return Alarm(
        alarm_id=alarm_id,
        run_id=run_id,
        simulation_time_ms=simulation_time_ms,
        target=raw.target_device_id,
        code="smart_meter_rejected",
        severity="warning",
        message=f"smart-meter rejected: {raw.reason}",
        status="active",
        fault_id=None,
    )


def dispatch_alarm_mapper(
    raw: object,
    *,
    run_id: str,
    simulation_time_ms: int,
    alarm_id: str,
) -> Alarm:
    """Dispatcht raw device-Alarms auf die passende Mapper-Funktion
    (M5 Welle 4b, ADR 0040 Decision 15 + Decision 16).

    isinstance-Chain ueber die 5 device-spezifischen Alarm-Typen.
    Forward-Compat-Defensive: ein nicht-erkannter Typ wirft
    `TypeError` — Welle-7+/M3-Geraete muessen sich hier eintragen
    (Pattern analog `_DEVICE_TYPE_BY_CLASS_NAME` im Snapshot-
    Schema).
    """
    if isinstance(raw, BatteryAlarm | PvAlarm | LoadAlarm | GridConnectionAlarm | EvChargerAlarm):
        return alarm_from_power_device_alarm(
            raw,
            run_id=run_id,
            simulation_time_ms=simulation_time_ms,
            alarm_id=alarm_id,
        )
    if isinstance(raw, SmartMeterAlarm):
        return alarm_from_smart_meter_alarm(
            raw,
            run_id=run_id,
            simulation_time_ms=simulation_time_ms,
            alarm_id=alarm_id,
        )
    raise UnknownRawAlarmTypeError(type(raw).__name__)


class UnknownRawAlarmTypeError(TypeError):
    """Welle-7+/M3-Geraete-Forward-Compat-Defensive: ein raw-Alarm-
    Typ, der nicht in `dispatch_alarm_mapper` registriert ist."""

    def __init__(self, type_name: str) -> None:
        super().__init__(
            f"TickLoop alarm-aggregation: unknown raw-alarm type "
            f"{type_name!r}. Welle-7+/M3-Geraete muessen sich in "
            f"`dispatch_alarm_mapper` registrieren."
        )


__all__ = [
    "PowerDeviceAlarm",
    "UnknownRawAlarmTypeError",
    "alarm_from_power_device_alarm",
    "alarm_from_smart_meter_alarm",
    "dispatch_alarm_mapper",
]
