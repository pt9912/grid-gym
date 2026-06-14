"""Tests fuer `DieselGeneratorDevice.inject_fault`/`clear_fault`
(M8 Welle 2d, ADR 0058 §2.7, ADR 0022 + ADR 0025).

Pinnt:
- `FaultInjectableDevice`-Protocol-Adherence.
- `genset_fault` stoppt den Genset: `power_kw` hart `0`, `running` False,
  kein Kraftstoffverbrauch (Tank eingefroren).
- `clear_fault` symmetrisch + idempotent + pre-init-sicher.
- Unbekannter `fault_type` wirft `FaultUnsupportedTypeError`.
- Snapshot-Roundtrip mit `fault_state`-Block.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.devices.diesel_generator import DieselGeneratorDevice
from grid_gym.hexagon.core.devices.diesel_generator.commands import COMMAND_TYPE_SET_POWER_KW
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.errors import FaultUnsupportedTypeError, WrongTypeError
from grid_gym.hexagon.core.faults import FaultInjectableDevice
from grid_gym.hexagon.core.faults.types import FAULT_TYPE_GENSET_FAULT
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom

_CTX0 = DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000)
_CTX1 = DeviceTickContext(tick=1, simulation_time=1000, tick_ms=1000)


def _diesel() -> DieselGeneratorDevice:
    device = DieselGeneratorDevice()
    device.initialize(
        ScenarioDevice(
            id="dg-1",
            type="diesel_generator",
            params={
                "max_power_kw": Decimal("100"),
                "min_start_power_kw": Decimal("20"),
                "min_stop_power_kw": Decimal("10"),
                "fuel_capacity_l": Decimal("1000"),
                "initial_fuel_l": Decimal("1000"),
                "fuel_per_kwh_l": Decimal("0.3"),
                "ramp_kw_per_s": Decimal("1000"),
            },
        ),
        FixedSeedRandom(seed=42),
    )
    device.set_run_id("test")
    return device


def _set_power(value: Decimal) -> Command:
    return Command(
        command_id="cmd-1",
        simulation_time=0,
        target_device_id="dg-1",
        type=COMMAND_TYPE_SET_POWER_KW,
        payload={"value": value},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _by_metric(device: DieselGeneratorDevice) -> dict[str, Decimal]:
    return {p.metric: p.value for p in device.telemetry()}


def test_device_satisfies_fault_injectable_protocol() -> None:
    assert isinstance(_diesel(), FaultInjectableDevice)


def test_inject_genset_fault_sets_flag() -> None:
    device = _diesel()
    assert device._genset_fault_active is False
    device.inject_fault(FAULT_TYPE_GENSET_FAULT, {})
    assert device._genset_fault_active is True


def test_genset_fault_stops_and_freezes_fuel() -> None:
    device = _diesel()
    device.apply_command(_set_power(Decimal("50")))
    device.tick(_CTX0)  # laeuft, verbraucht Sprit
    fuel_before = device.snapshot()["fuel_l"]
    device.inject_fault(FAULT_TYPE_GENSET_FAULT, {})
    device.tick(_CTX1)
    m = _by_metric(device)
    assert m["power_kw"] == Decimal("0.000000")
    assert m["running"] == Decimal("0.000000")
    assert m["genset_fault"] == Decimal("1.000000")
    assert device.snapshot()["fuel_l"] == fuel_before  # kein Verbrauch im Fault


def test_clear_fault_re_enables_start() -> None:
    device = _diesel()
    device.apply_command(_set_power(Decimal("50")))
    device.inject_fault(FAULT_TYPE_GENSET_FAULT, {})
    device.tick(_CTX0)  # gestoppt durch Fault
    device.clear_fault(FAULT_TYPE_GENSET_FAULT)
    device.tick(_CTX1)  # Command 50 >= min_start → faehrt wieder an
    m = _by_metric(device)
    assert m["running"] == Decimal("1.000000")
    assert m["power_kw"] == Decimal("50.000000")


def test_clear_fault_is_idempotent() -> None:
    device = _diesel()
    device.clear_fault(FAULT_TYPE_GENSET_FAULT)  # pre-fault clear
    device.inject_fault(FAULT_TYPE_GENSET_FAULT, {})
    device.clear_fault(FAULT_TYPE_GENSET_FAULT)
    device.clear_fault(FAULT_TYPE_GENSET_FAULT)  # No-Op
    assert device._genset_fault_active is False


def test_clear_fault_pre_init_is_safe_noop() -> None:
    device = DieselGeneratorDevice()
    device.clear_fault(FAULT_TYPE_GENSET_FAULT)
    assert device._genset_fault_active is False


def test_inject_unknown_fault_type_raises_typed() -> None:
    with pytest.raises(FaultUnsupportedTypeError):
        _diesel().inject_fault("cell_failure", {})


def test_clear_unknown_fault_type_raises_typed() -> None:
    with pytest.raises(FaultUnsupportedTypeError):
        _diesel().clear_fault("voltage_drop")


def test_snapshot_roundtrip_preserves_fault_flag() -> None:
    device = _diesel()
    device.inject_fault(FAULT_TYPE_GENSET_FAULT, {})
    restored = DieselGeneratorDevice.from_snapshot(device.snapshot())
    assert restored._genset_fault_active is True
    assert restored == device


def test_snapshot_without_fault_state_defaults_false() -> None:
    device = _diesel()
    state = dict(device.snapshot())
    state.pop("fault_state", None)
    restored = DieselGeneratorDevice.from_snapshot(state)
    assert restored._genset_fault_active is False


def test_snapshot_with_wrong_typed_fault_flag_raises() -> None:
    device = _diesel()
    state = dict(device.snapshot())
    state["fault_state"] = {"genset_fault_active": "true"}
    with pytest.raises(WrongTypeError):
        DieselGeneratorDevice.from_snapshot(state)
