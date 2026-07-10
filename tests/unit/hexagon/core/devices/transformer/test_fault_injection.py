"""Tests fuer `TransformerDevice.inject_fault`/`clear_fault`
(M8 Welle 2b, ADR 0056 §2.6, ADR 0022 + ADR 0025).

Pinnt:
- `FaultInjectableDevice`-Protocol-Adherence.
- `winding_fault` isoliert den Transformator: `primary`/`secondary`/
  `loss` hart `0`, `throughput_kwh` eingefroren, `secondary_voltage` 0.
- `clear_fault` symmetrisch + idempotent + pre-init-sicher.
- Unbekannter `fault_type` wirft `FaultUnsupportedTypeError`.
- Snapshot-Roundtrip mit `fault_state`-Block (Backward-Compat:
  fehlender/leerer Block → False; falsch-typisiert → WrongTypeError).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.devices.transformer import TransformerDevice
from grid_gym.hexagon.core.devices.transformer.commands import COMMAND_TYPE_SET_POWER_KW
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.errors import FaultUnsupportedTypeError, WrongTypeError
from grid_gym.hexagon.core.faults import FaultInjectableDevice
from grid_gym.hexagon.core.faults.types import FAULT_TYPE_WINDING_FAULT
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom

# Slice 054: fault-Sensor-Traeger fuer `make test-fault`.
pytestmark = pytest.mark.fault

_CTX = DeviceTickContext(tick=0, simulation_time=0, tick_ms=3_600_000)


def _transformer() -> TransformerDevice:
    device = TransformerDevice()
    device.initialize(
        ScenarioDevice(
            id="tr-1",
            type="transformer",
            params={
                "rated_power_kw": Decimal("1000"),
                "primary_voltage_v": Decimal("20000"),
                "turns_ratio": Decimal("50"),
                "no_load_loss_kw": Decimal("5"),
                "load_loss_kw": Decimal("20"),
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
        target_device_id="tr-1",
        type=COMMAND_TYPE_SET_POWER_KW,
        payload={"value": value},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _by_metric(device: TransformerDevice) -> dict[str, Decimal]:
    return {p.metric: p.value for p in device.telemetry()}


def test_device_satisfies_fault_injectable_protocol() -> None:
    assert isinstance(_transformer(), FaultInjectableDevice)


def test_inject_winding_fault_sets_flag() -> None:
    device = _transformer()
    assert device._winding_fault_active is False
    device.inject_fault(FAULT_TYPE_WINDING_FAULT, {})
    assert device._winding_fault_active is True


def test_winding_fault_isolates_transformer_and_freezes_throughput() -> None:
    device = _transformer()
    device.apply_command(_set_power(Decimal("500")))
    device.tick(_CTX)  # baut Durchsatz auf
    throughput_before = device.snapshot()["throughput_kwh"]
    device.inject_fault(FAULT_TYPE_WINDING_FAULT, {})
    device.tick(DeviceTickContext(tick=1, simulation_time=3_600_000, tick_ms=3_600_000))
    m = _by_metric(device)
    assert m["primary_power_kw"] == Decimal("0.000000")
    assert m["secondary_power_kw"] == Decimal("0.000000")
    assert m["loss_kw"] == Decimal("0.000000")
    assert m["secondary_voltage_v"] == Decimal("0.000000")
    assert m["winding_fault"] == Decimal("1.000000")
    assert device.snapshot()["throughput_kwh"] == throughput_before  # eingefroren
    # Freeze haelt ueber mehrere gefaultete Ticks (Safety-Invariante).
    device.tick(DeviceTickContext(tick=2, simulation_time=2 * 3_600_000, tick_ms=3_600_000))
    assert device.snapshot()["throughput_kwh"] == throughput_before


def test_clear_fault_re_energizes() -> None:
    device = _transformer()
    device.apply_command(_set_power(Decimal("500")))
    device.inject_fault(FAULT_TYPE_WINDING_FAULT, {})
    device.tick(_CTX)
    device.clear_fault(FAULT_TYPE_WINDING_FAULT)
    assert device._winding_fault_active is False
    device.tick(DeviceTickContext(tick=1, simulation_time=3_600_000, tick_ms=3_600_000))
    m = _by_metric(device)
    assert m["secondary_power_kw"] == Decimal("490.000000")
    assert m["winding_fault"] == Decimal("0.000000")


def test_clear_fault_is_idempotent() -> None:
    device = _transformer()
    device.clear_fault(FAULT_TYPE_WINDING_FAULT)  # pre-fault clear
    device.inject_fault(FAULT_TYPE_WINDING_FAULT, {})
    device.clear_fault(FAULT_TYPE_WINDING_FAULT)
    device.clear_fault(FAULT_TYPE_WINDING_FAULT)  # No-Op
    assert device._winding_fault_active is False


def test_clear_fault_pre_init_is_safe_noop() -> None:
    device = TransformerDevice()
    device.clear_fault(FAULT_TYPE_WINDING_FAULT)
    assert device._winding_fault_active is False


def test_inject_unknown_fault_type_raises_typed() -> None:
    with pytest.raises(FaultUnsupportedTypeError):
        _transformer().inject_fault("cell_failure", {})


def test_clear_unknown_fault_type_raises_typed() -> None:
    with pytest.raises(FaultUnsupportedTypeError):
        _transformer().clear_fault("voltage_drop")


def test_snapshot_roundtrip_preserves_fault_flag() -> None:
    device = _transformer()
    device.inject_fault(FAULT_TYPE_WINDING_FAULT, {})
    restored = TransformerDevice.from_snapshot(device.snapshot())
    assert restored._winding_fault_active is True
    assert restored == device


def test_snapshot_without_fault_state_defaults_false() -> None:
    device = _transformer()
    state = dict(device.snapshot())
    state.pop("fault_state", None)
    restored = TransformerDevice.from_snapshot(state)
    assert restored._winding_fault_active is False


def test_snapshot_with_empty_fault_state_defaults_false() -> None:
    device = _transformer()
    state = dict(device.snapshot())
    state["fault_state"] = {}
    restored = TransformerDevice.from_snapshot(state)
    assert restored._winding_fault_active is False


def test_snapshot_with_wrong_typed_fault_flag_raises() -> None:
    device = _transformer()
    state = dict(device.snapshot())
    state["fault_state"] = {"winding_fault_active": "true"}
    with pytest.raises(WrongTypeError):
        TransformerDevice.from_snapshot(state)
