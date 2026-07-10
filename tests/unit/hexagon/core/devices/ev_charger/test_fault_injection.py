"""Tests fuer `EvChargerDevice.inject_fault`/`clear_fault`
(M8 Welle 2a, ADR 0055 §2.7, ADR 0022 + ADR 0025).

Pinnt:
- `FaultInjectableDevice`-Protocol-Adherence.
- `connection_loss`-Fault setzt das Flag + friert SoC ein
  (`power_kw` hart `0`, analog `unplugged`).
- `clear_fault` symmetrisch + idempotent + pre-init-sicher.
- Unbekannter `fault_type` wirft `FaultUnsupportedTypeError`.
- Snapshot-Roundtrip mit `fault_state`-Block (Backward-Compat:
  fehlender/leerer Block → `False`; falsch-typisiert → WrongTypeError).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.devices.ev_charger import EvChargerDevice
from grid_gym.hexagon.core.devices.ev_charger.commands import (
    COMMAND_TYPE_SET_CHARGE_POWER,
)
from grid_gym.hexagon.core.devices.ev_charger.config import PLUG_STATE_PLUGGED
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.errors import FaultUnsupportedTypeError, WrongTypeError
from grid_gym.hexagon.core.faults import FaultInjectableDevice
from grid_gym.hexagon.core.faults.types import FAULT_TYPE_CONNECTION_LOSS
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom

# Slice 054: fault-Sensor-Traeger fuer `make test-fault`.
pytestmark = pytest.mark.fault

_CTX = DeviceTickContext(tick=0, simulation_time=0, tick_ms=3_600_000)


def _ev_device() -> EvChargerDevice:
    device = EvChargerDevice()
    device.initialize(
        ScenarioDevice(
            id="ev-1",
            type="ev_charger",
            params={
                "max_charge_kw": Decimal("11"),
                "max_discharge_kw": Decimal("11"),
                "nominal_voltage_v": Decimal("400"),
                "battery_capacity_kwh": Decimal("60"),
                "cv_phase_start_soc": Decimal("0.8"),
                "initial_soc": Decimal("0.5"),
                "initial_plug_state": PLUG_STATE_PLUGGED,
            },
        ),
        FixedSeedRandom(seed=42),
    )
    device.set_run_id("test")
    return device


def _charge_command(value: Decimal) -> Command:
    return Command(
        command_id="cmd-1",
        simulation_time=0,
        target_device_id="ev-1",
        type=COMMAND_TYPE_SET_CHARGE_POWER,
        payload={"value": value},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def test_device_satisfies_fault_injectable_protocol() -> None:
    assert isinstance(_ev_device(), FaultInjectableDevice)


def test_inject_connection_loss_sets_flag() -> None:
    device = _ev_device()
    assert device._connection_loss_active is False
    device.inject_fault(FAULT_TYPE_CONNECTION_LOSS, {})
    assert device._connection_loss_active is True


def test_connection_loss_forces_zero_power_and_freezes_soc() -> None:
    device = _ev_device()
    device.apply_command(_charge_command(Decimal("11")))
    stored_before = device.snapshot()["stored_kwh"]
    device.inject_fault(FAULT_TYPE_CONNECTION_LOSS, {})
    outcome = device.tick(_CTX)
    power = next(p for p in outcome.telemetry if p.metric == "power_kw")
    loss = next(p for p in outcome.telemetry if p.metric == "connection_loss")
    assert power.value == Decimal("0.000000")
    assert loss.value == Decimal("1.000000")
    assert device.snapshot()["stored_kwh"] == stored_before  # SoC eingefroren


def test_clear_fault_re_enables_charging() -> None:
    device = _ev_device()
    device.apply_command(_charge_command(Decimal("11")))
    device.inject_fault(FAULT_TYPE_CONNECTION_LOSS, {})
    device.tick(_CTX)
    device.clear_fault(FAULT_TYPE_CONNECTION_LOSS)
    assert device._connection_loss_active is False
    outcome = device.tick(DeviceTickContext(tick=1, simulation_time=3_600_000, tick_ms=3_600_000))
    power = next(p for p in outcome.telemetry if p.metric == "power_kw")
    assert power.value == Decimal("11.000000")


def test_clear_fault_is_idempotent() -> None:
    device = _ev_device()
    device.clear_fault(FAULT_TYPE_CONNECTION_LOSS)  # pre-fault clear
    device.inject_fault(FAULT_TYPE_CONNECTION_LOSS, {})
    device.clear_fault(FAULT_TYPE_CONNECTION_LOSS)
    device.clear_fault(FAULT_TYPE_CONNECTION_LOSS)  # No-Op
    assert device._connection_loss_active is False


def test_clear_fault_pre_init_is_safe_noop() -> None:
    device = EvChargerDevice()
    device.clear_fault(FAULT_TYPE_CONNECTION_LOSS)
    assert device._connection_loss_active is False


def test_inject_unknown_fault_type_raises_typed() -> None:
    device = _ev_device()
    with pytest.raises(FaultUnsupportedTypeError):
        device.inject_fault("cell_failure", {})


def test_clear_unknown_fault_type_raises_typed() -> None:
    device = _ev_device()
    with pytest.raises(FaultUnsupportedTypeError):
        device.clear_fault("voltage_drop")


def test_snapshot_roundtrip_preserves_fault_flag() -> None:
    device = _ev_device()
    device.inject_fault(FAULT_TYPE_CONNECTION_LOSS, {})
    restored = EvChargerDevice.from_snapshot(device.snapshot())
    assert restored._connection_loss_active is True
    assert restored == device


def test_snapshot_without_fault_state_defaults_false() -> None:
    device = _ev_device()
    state = dict(device.snapshot())
    state.pop("fault_state", None)
    restored = EvChargerDevice.from_snapshot(state)
    assert restored._connection_loss_active is False


def test_snapshot_with_empty_fault_state_defaults_false() -> None:
    device = _ev_device()
    state = dict(device.snapshot())
    state["fault_state"] = {}
    restored = EvChargerDevice.from_snapshot(state)
    assert restored._connection_loss_active is False


def test_snapshot_with_wrong_typed_fault_flag_raises() -> None:
    device = _ev_device()
    state = dict(device.snapshot())
    state["fault_state"] = {"connection_loss_active": "true"}
    with pytest.raises(WrongTypeError):
        EvChargerDevice.from_snapshot(state)
