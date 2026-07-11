"""M5-Welle-4b-Tests fuer den NEU `Alarm`-Domain-Type + Mapper-
Familie (ADR 0040 Decision 15).

Pinnt:

- `Alarm` ist frozen + slots (`AC-DOMAIN-FROZEN`-Compliance).
- `AlarmSeverity` + `AlarmStatus` Literal-Werte.
- 5 Mapper-Funktionen sind rein (deterministisch + side-effect-
  free); gleiche Inputs → gleicher Output.
- Mapping-Heuristik `(result, limit, limit_unit) → (code,
  severity, message)` per ADR-0040-§2.1-Tabelle.
"""

from __future__ import annotations

import typing
from decimal import Decimal

from grid_gym.hexagon.core.devices.battery.commands import BatteryAlarm
from grid_gym.hexagon.core.devices.grid_connection.commands import GridConnectionAlarm
from grid_gym.hexagon.core.devices.load.commands import LoadAlarm
from grid_gym.hexagon.core.devices.pv.commands import PvAlarm
from grid_gym.hexagon.core.devices.smart_meter.commands import SmartMeterAlarm
from grid_gym.hexagon.core.domain.alarm import Alarm, AlarmSeverity, AlarmStatus
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.simulation.alarm_mappers import (
    alarm_from_power_device_alarm,
    alarm_from_quality_fault_nan_injection_alarm,
    alarm_from_smart_meter_alarm,
    dispatch_alarm_mapper,
)
from grid_gym.hexagon.core.simulation.quality_fault import QualityFaultNanInjectionAlarm


# ---------------------------------------------------------------------------
# Schema-Smokes
# ---------------------------------------------------------------------------


def test_alarm_severity_literal_has_three_welle_4b_values() -> None:
    """ADR 0040 §2.1: AlarmSeverity = `info`/`warning`/`critical`."""
    assert set(typing.get_args(AlarmSeverity)) == {"info", "warning", "critical"}


def test_alarm_status_literal_welle_4b_has_only_active() -> None:
    """ADR 0040 §2.1: AlarmStatus in Welle 4b nur `active`.
    Lifecycle-Erweiterung (`acknowledged`/`resolved`) ist Welle
    6+/M6-Material."""
    assert typing.get_args(AlarmStatus) == ("active",)


def test_alarm_dataclass_is_frozen_with_slots() -> None:
    """ADR 0040 §2.1 + AC-DOMAIN-FROZEN: Alarm ist frozen +
    slots fuer Snapshot-Equality-Konsistenz."""
    alarm = Alarm(
        alarm_id="a-1",
        run_id="r-1",
        simulation_time_ms=100,
        target="battery-1",
        code="power_clamp_limited",
        severity="warning",
        message="msg",
        status="active",
        fault_id=None,
    )
    assert alarm.alarm_id == "a-1"
    # Frozen: mutation wirft FrozenInstanceError.
    try:
        alarm.alarm_id = "a-2"  # type: ignore[misc]
    except Exception as exc:
        assert "frozen" in str(exc).lower() or "cannot assign" in str(exc).lower()
    else:
        raise AssertionError("Alarm should be frozen")


# ---------------------------------------------------------------------------
# Mapper-Heuristik (LIMITED → warning, REJECTED → critical)
# ---------------------------------------------------------------------------


def test_battery_alarm_limited_maps_to_warning_power_clamp() -> None:
    raw = BatteryAlarm(
        target_device_id="battery-1",
        limit=Decimal("30.0"),
        limit_unit="kW",
        result=CommandResult.LIMITED,
        command_id="cmd-1",
    )
    mapped = alarm_from_power_device_alarm(
        raw,
        run_id="run-1",
        simulation_time_ms=200,
        alarm_id="alarm-1",
    )
    assert mapped.code == "power_clamp_limited"
    assert mapped.severity == "warning"
    assert "30.0" in mapped.message
    assert "kW" in mapped.message
    assert mapped.target == "battery-1"
    assert mapped.run_id == "run-1"
    assert mapped.simulation_time_ms == 200
    assert mapped.alarm_id == "alarm-1"
    assert mapped.status == "active"
    assert mapped.fault_id is None


def test_battery_alarm_rejected_maps_to_critical_command_rejected() -> None:
    raw = BatteryAlarm(
        target_device_id="battery-1",
        limit=Decimal("100"),
        limit_unit="pct",
        result=CommandResult.REJECTED,
        command_id="cmd-2",
    )
    mapped = alarm_from_power_device_alarm(
        raw,
        run_id="run-1",
        simulation_time_ms=300,
        alarm_id="alarm-2",
    )
    assert mapped.code == "command_rejected"
    assert mapped.severity == "critical"
    assert "100" in mapped.message


def test_pv_alarm_limited_maps_to_warning() -> None:
    raw = PvAlarm(
        target_device_id="pv-1",
        limit=Decimal("50.0"),
        limit_unit="kW",
        result=CommandResult.LIMITED,
        command_id="cmd-3",
    )
    mapped = alarm_from_power_device_alarm(raw, run_id="r", simulation_time_ms=0, alarm_id="a")
    assert mapped.severity == "warning"
    assert mapped.target == "pv-1"


def test_load_alarm_rejected_maps_to_critical() -> None:
    raw = LoadAlarm(
        target_device_id="load-1",
        limit=Decimal("0"),
        limit_unit="kW",
        result=CommandResult.REJECTED,
        command_id="cmd-4",
    )
    mapped = alarm_from_power_device_alarm(raw, run_id="r", simulation_time_ms=0, alarm_id="a")
    assert mapped.severity == "critical"
    assert mapped.target == "load-1"


def test_grid_connection_alarm_limited_maps_to_warning() -> None:
    raw = GridConnectionAlarm(
        target_device_id="grid-1",
        limit=Decimal("80.0"),
        limit_unit="kW",
        result=CommandResult.LIMITED,
        command_id="cmd-5",
    )
    mapped = alarm_from_power_device_alarm(raw, run_id="r", simulation_time_ms=0, alarm_id="a")
    assert mapped.severity == "warning"
    assert mapped.target == "grid-1"


def test_smart_meter_alarm_maps_to_warning_with_reason_in_message() -> None:
    raw = SmartMeterAlarm(
        target_device_id="meter-1",
        reason="invalid setpoint",
        result=CommandResult.REJECTED,
        command_id="cmd-6",
    )
    mapped = alarm_from_smart_meter_alarm(raw, run_id="r", simulation_time_ms=0, alarm_id="a")
    assert mapped.code == "smart_meter_rejected"
    assert mapped.severity == "warning"
    assert "invalid setpoint" in mapped.message
    assert mapped.target == "meter-1"


# ---------------------------------------------------------------------------
# Determinismus (gleiche Inputs → gleicher Output)
# ---------------------------------------------------------------------------


def test_mapper_is_deterministic_same_inputs_same_output() -> None:
    """ADR 0040 §2.1: Mapper sind reine Funktionen."""
    raw = BatteryAlarm(
        target_device_id="battery-1",
        limit=Decimal("30.0"),
        limit_unit="kW",
        result=CommandResult.LIMITED,
        command_id="cmd-1",
    )
    a = alarm_from_power_device_alarm(raw, run_id="r-1", simulation_time_ms=100, alarm_id="alarm-1")
    b = alarm_from_power_device_alarm(raw, run_id="r-1", simulation_time_ms=100, alarm_id="alarm-1")
    assert a == b


def test_quality_fault_nan_injection_alarm_maps_to_warning() -> None:
    """ADR 0074 §2.5: der spine-erzeugte `QualityFaultNanInjectionAlarm`
    mappt auf Code `quality_fault_nan_injection`, Severity `warning`, mit
    der Metrik in der Message."""
    raw = QualityFaultNanInjectionAlarm(target_device_id="meter-1", metric="voltage_v")
    alarm = alarm_from_quality_fault_nan_injection_alarm(
        raw, run_id="r-1", simulation_time_ms=1000, alarm_id="alarm-9"
    )
    assert alarm.code == "quality_fault_nan_injection"
    assert alarm.severity == "warning"
    assert alarm.target == "meter-1"
    assert alarm.message == "nan injection on metric voltage_v"
    assert alarm.status == "active"
    assert alarm.fault_id is None
    assert alarm.alarm_id == "alarm-9"


def test_dispatch_routes_quality_fault_nan_injection_alarm() -> None:
    """ADR 0074 §2.5: `dispatch_alarm_mapper` erkennt den neuen
    Raw-Alarm-Typ (fail-fast-Dispatch bleibt fuer unbekannte Typen)."""
    raw = QualityFaultNanInjectionAlarm(target_device_id="meter-1", metric="freq_hz")
    alarm = dispatch_alarm_mapper(raw, run_id="r-1", simulation_time_ms=1000, alarm_id="alarm-0")
    assert alarm.code == "quality_fault_nan_injection"
    assert alarm.message == "nan injection on metric freq_hz"
