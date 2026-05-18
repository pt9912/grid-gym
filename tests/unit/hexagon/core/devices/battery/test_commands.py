"""Tests fuer `validate_set_power_command` (`GG-BESS-002`).

Pinnt:
- Unknown-Type → IGNORED.
- Missing/wrong-type Payload-`value` → IGNORED (Adapter-Pflicht).
- Wert ueber max_charge → LIMITED + Alarm.
- Wert unter -max_discharge → LIMITED + Alarm.
- SOC am Boden + Entladen → REJECTED + Alarm.
- SOC an der Decke + Laden → REJECTED + Alarm.
- Sonst → ACCEPTED + neuer Soll.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import cast

import pytest

from grid_gym.hexagon.core.devices.battery.commands import (
    COMMAND_TYPE_SET_POWER_KW,
    BatteryAlarm,
    validate_set_power_command,
)
from grid_gym.hexagon.core.devices.battery.config import BatteryConfig
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult


def _config(
    capacity_kwh: Decimal = Decimal("1000"),
    min_soc_pct: Decimal = Decimal("10"),
    max_soc_pct: Decimal = Decimal("90"),
    max_charge_kw: Decimal = Decimal("500"),
    max_discharge_kw: Decimal = Decimal("500"),
) -> BatteryConfig:
    return BatteryConfig(
        capacity_kwh=capacity_kwh,
        initial_soc_pct=Decimal("50"),
        min_soc_pct=min_soc_pct,
        max_soc_pct=max_soc_pct,
        max_charge_kw=max_charge_kw,
        max_discharge_kw=max_discharge_kw,
        charge_efficiency=Decimal("0.95"),
        discharge_efficiency=Decimal("0.95"),
        ramp_kw_per_s=Decimal("50"),
    )


def _command(
    cmd_type: str = COMMAND_TYPE_SET_POWER_KW,
    value: object = Decimal("100"),
    command_id: str = "cmd-1",
) -> Command:
    payload: dict[str, object] = {"value": value}
    return Command(
        command_id=command_id,
        simulation_time=0,
        target_device_id="battery-1",
        type=cmd_type,
        payload=payload,
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


# ---------------------------------------------------------------------------
# Unknown-Type / Payload-Pfade → IGNORED
# ---------------------------------------------------------------------------


def test_unknown_type_returns_ignored() -> None:
    outcome = validate_set_power_command(
        config=_config(),
        soc_kwh=Decimal("500"),
        command=_command(cmd_type="set_mode"),
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.IGNORED
    assert outcome.pending_power_kw is None
    assert outcome.alarm is None


def test_missing_value_payload_returns_ignored() -> None:
    cmd = Command(
        command_id="cmd-x",
        simulation_time=0,
        target_device_id="battery-1",
        type=COMMAND_TYPE_SET_POWER_KW,
        payload={},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )
    outcome = validate_set_power_command(
        config=_config(),
        soc_kwh=Decimal("500"),
        command=cmd,
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.IGNORED


def test_non_decimal_value_returns_ignored() -> None:
    outcome = validate_set_power_command(
        config=_config(),
        soc_kwh=Decimal("500"),
        command=_command(value=100),  # int statt Decimal
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.IGNORED


# ---------------------------------------------------------------------------
# Power-Grenz-Pfade → LIMITED + Alarm
# ---------------------------------------------------------------------------


def test_value_above_max_charge_clamped_and_alarmed() -> None:
    outcome = validate_set_power_command(
        config=_config(max_charge_kw=Decimal("500")),
        soc_kwh=Decimal("500"),  # in der Mitte, SOC-Grenze irrelevant
        command=_command(value=Decimal("700")),
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("500")
    assert isinstance(outcome.alarm, BatteryAlarm)
    assert outcome.alarm.limit == Decimal("500")
    assert outcome.alarm.result is CommandResult.LIMITED


def test_value_below_neg_max_discharge_clamped_and_alarmed() -> None:
    outcome = validate_set_power_command(
        config=_config(max_discharge_kw=Decimal("500")),
        soc_kwh=Decimal("500"),
        command=_command(value=Decimal("-700")),
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("-500")
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("-500")


# ---------------------------------------------------------------------------
# SOC-Grenz-Pfade → REJECTED + Alarm
# ---------------------------------------------------------------------------


def test_discharge_at_soc_floor_rejected() -> None:
    config = _config(min_soc_pct=Decimal("10"))
    # min_soc_kwh = 100; SOC bei 100 (genau am Boden)
    outcome = validate_set_power_command(
        config=config,
        soc_kwh=Decimal("100"),
        command=_command(value=Decimal("-100")),  # Entladen
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.REJECTED
    assert outcome.pending_power_kw is None
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("10")  # min_soc_pct


def test_charge_at_soc_ceiling_rejected() -> None:
    config = _config(max_soc_pct=Decimal("90"))
    # max_soc_kwh = 900; SOC bei 900 (genau an der Decke)
    outcome = validate_set_power_command(
        config=config,
        soc_kwh=Decimal("900"),
        command=_command(value=Decimal("100")),  # Laden
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.REJECTED
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("90")  # max_soc_pct


def test_discharge_at_soc_floor_zero_command_is_accepted() -> None:
    """Stillstand-Command (`0 kW`) am Boden ist NICHT REJECTED —
    es entlaedt nicht."""
    outcome = validate_set_power_command(
        config=_config(min_soc_pct=Decimal("10")),
        soc_kwh=Decimal("100"),
        command=_command(value=Decimal("0")),
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.ACCEPTED


def test_charge_at_soc_floor_is_accepted() -> None:
    """Lade-Command (`+100 kW`) am Boden ist ACCEPTED — SOC steigt."""
    outcome = validate_set_power_command(
        config=_config(min_soc_pct=Decimal("10")),
        soc_kwh=Decimal("100"),
        command=_command(value=Decimal("100")),
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.ACCEPTED


# ---------------------------------------------------------------------------
# Happy-Path → ACCEPTED + Soll-Wert gesetzt
# ---------------------------------------------------------------------------


def test_within_limits_accepts_and_sets_pending() -> None:
    outcome = validate_set_power_command(
        config=_config(),
        soc_kwh=Decimal("500"),
        command=_command(value=Decimal("250")),
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw == Decimal("250")
    assert outcome.alarm is None


def test_alarm_carries_command_id() -> None:
    outcome = validate_set_power_command(
        config=_config(),
        soc_kwh=Decimal("500"),
        command=_command(value=Decimal("9999"), command_id="cmd-42"),
        device_id="battery-1",
    )
    assert outcome.alarm is not None
    assert outcome.alarm.command_id == "cmd-42"


def test_battery_alarm_is_frozen() -> None:
    from dataclasses import FrozenInstanceError

    alarm = BatteryAlarm(
        target_device_id="battery-1",
        limit=Decimal("500"),
        result=CommandResult.LIMITED,
        command_id="cmd-1",
    )
    with pytest.raises(FrozenInstanceError):
        alarm.limit = Decimal("0")  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Welle-2-Review M-8: SOC-Reject vor Power-Clamp
# ---------------------------------------------------------------------------


def test_clamped_command_at_soc_floor_rejects_not_limits() -> None:
    """Doppelt-verletzender Command (-700 kW bei SOC-Boden, max
    discharge 500) geht direkt auf REJECTED — nicht
    LIMITED→-500→Clamp-Drop. ADR 0014 §2.3 + Welle-2-Review M-8."""
    config = _config(min_soc_pct=Decimal("10"), max_discharge_kw=Decimal("500"))
    outcome = validate_set_power_command(
        config=config,
        soc_kwh=Decimal("100"),  # an min_soc_kwh (10% * 1000)
        command=_command(value=Decimal("-700")),  # ueber discharge-Grenze
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.REJECTED
    assert outcome.pending_power_kw is None
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("10")  # min_soc_pct


def test_clamped_command_at_soc_ceiling_rejects_not_limits() -> None:
    """Spiegel: +700 kW (max charge 500) bei SOC-Decke geht
    REJECTED, nicht LIMITED."""
    config = _config(max_soc_pct=Decimal("90"), max_charge_kw=Decimal("500"))
    outcome = validate_set_power_command(
        config=config,
        soc_kwh=Decimal("900"),  # an max_soc_kwh
        command=_command(value=Decimal("700")),
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.REJECTED
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("90")  # max_soc_pct


# ---------------------------------------------------------------------------
# Welle-2-Review M-7: payload=None Defensive
# ---------------------------------------------------------------------------


def test_command_with_none_payload_returns_ignored() -> None:
    """Defekter Adapter koennte ein Command mit payload=None
    bauen. Welle-2-Review M-7: defensiv abfangen statt
    AttributeError zu werfen."""
    cmd = Command(
        command_id="cmd-x",
        simulation_time=0,
        target_device_id="battery-1",
        type=COMMAND_TYPE_SET_POWER_KW,
        payload=cast("Mapping[str, object]", None),
        validation_status="validated",
        result=CommandResult.IGNORED,
    )
    outcome = validate_set_power_command(
        config=_config(),
        soc_kwh=Decimal("500"),
        command=cmd,
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.IGNORED
