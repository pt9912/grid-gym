"""Tests fuer die opt-in Battery-Zellspannungs-Telemetrie (M8 Welle 4b,
`GG-BESS-007`, ADR 0066).

Pinnt:
- `CellConfig`-Validierung (Positiv-/Grenz-Felder).
- **Inaktiv-Regression**: ohne `cell`-Block kein `cell_voltage_delta_v`-Punkt
  (3 Metriken/Tick wie heute), kein Snapshot-State.
- **Aktiv `noise=0`**: alle Zellen identisch, `delta=0`, **kein** `RandomPort`
  noetig (laeuft auch nach `from_snapshot` ohne `attach_random`).
- **Aktiv `noise>0`**: per-Zelle seeded Rauschen, `cell_voltage_delta_v`-Punkt
  (`unit="V"`, alphabetisch zuerst), `delta>0`.
- ≥ 100-Tick-Determinismus + **tick-gekeyte Resume-Kontinuitaet** + Resume-
  Fail-Loud (aktives Rauschen ohne `attach_random` → fail-loud).
- Opt-in Snapshot-Roundtrip (byte-stabil) + Params-`n_cells:int`-Pruefung.
"""

from __future__ import annotations

from decimal import Decimal
from itertools import pairwise

import pytest

from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.battery.config import (
    BatteryConfig,
    BatteryConfigInvalidValueError,
    CellConfig,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import (
    DeviceNotInitializedError,
    MissingKeysError,
    WrongTypeError,
)
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom

_BASE_PARAMS: dict[str, object] = {
    "capacity_kwh": Decimal("1000"),
    "initial_soc_pct": Decimal("50"),
    "min_soc_pct": Decimal("10"),
    "max_soc_pct": Decimal("90"),
    "max_charge_kw": Decimal("500"),
    "max_discharge_kw": Decimal("500"),
    "charge_efficiency": Decimal("1"),
    "discharge_efficiency": Decimal("1"),
    "ramp_kw_per_s": Decimal("1000"),
}


def _params(cell: dict[str, object] | None) -> dict[str, object]:
    params = dict(_BASE_PARAMS)
    if cell is not None:
        params["cell"] = cell
    return params


def _device(cell: dict[str, object] | None, *, seed: int = 0) -> BatteryDevice:
    device = BatteryDevice()
    device.initialize(
        ScenarioDevice(id="battery-1", type="battery", params=_params(cell)),
        FixedSeedRandom(seed=seed),
    )
    return device


_CELL_NOISY: dict[str, object] = {
    "nominal_pack_voltage_v": Decimal("400"),
    "n_cells": 8,
    "noise_amplitude_v": Decimal("0.5"),
}
_CELL_QUIET: dict[str, object] = {
    "nominal_pack_voltage_v": Decimal("400"),
    "n_cells": 4,
    "noise_amplitude_v": Decimal("0"),
}


def _run(device: BatteryDevice, ticks: int, *, tick_ms: int = 1000) -> tuple[TelemetryPoint, ...]:
    device.apply_command(
        Command(
            command_id="cmd-0",
            simulation_time=0,
            target_device_id="battery-1",
            type="set_power_kw",
            payload={"value": Decimal("100")},
            validation_status="validated",
            result=CommandResult.IGNORED,
        )
    )
    out: list[TelemetryPoint] = []
    for tick in range(ticks):
        outcome = device.tick(
            DeviceTickContext(tick=tick, simulation_time=tick * tick_ms, tick_ms=tick_ms)
        )
        out.extend(outcome.telemetry)
    return tuple(out)


def _deltas(trace: tuple[TelemetryPoint, ...]) -> list[Decimal]:
    return [p.value for p in trace if p.metric == "cell_voltage_delta_v"]


# ---------------------------------------------------------------------------
# CellConfig-Validierung
# ---------------------------------------------------------------------------


def test_cell_config_accepts_valid_values() -> None:
    cell = CellConfig(
        nominal_pack_voltage_v=Decimal("400"), n_cells=8, noise_amplitude_v=Decimal("0.5")
    )
    assert cell.base_cell_voltage_v == Decimal("50")


def test_cell_config_defaults_zero_noise() -> None:
    cell = CellConfig(nominal_pack_voltage_v=Decimal("400"), n_cells=4)
    assert cell.noise_amplitude_v == Decimal("0")


@pytest.mark.parametrize(
    ("field", "value", "constraint"),
    [
        ("nominal_pack_voltage_v", Decimal("0"), "> 0"),
        ("nominal_pack_voltage_v", Decimal("-1"), "> 0"),
        ("n_cells", 0, ">= 1"),
        ("noise_amplitude_v", Decimal("-0.1"), ">= 0"),
    ],
)
def test_cell_config_rejects_invalid(field: str, value: object, constraint: str) -> None:
    fields: dict[str, object] = {
        "nominal_pack_voltage_v": Decimal("400"),
        "n_cells": 4,
        "noise_amplitude_v": Decimal("0"),
    }
    fields[field] = value
    with pytest.raises(BatteryConfigInvalidValueError) as exc_info:
        CellConfig(**fields)  # type: ignore[arg-type]
    assert field in str(exc_info.value)


def test_battery_config_cell_defaults_none() -> None:
    config = BatteryConfig(
        capacity_kwh=Decimal("1000"),
        initial_soc_pct=Decimal("50"),
        min_soc_pct=Decimal("10"),
        max_soc_pct=Decimal("90"),
        max_charge_kw=Decimal("500"),
        max_discharge_kw=Decimal("500"),
        charge_efficiency=Decimal("1"),
        discharge_efficiency=Decimal("1"),
        ramp_kw_per_s=Decimal("50"),
    )
    assert config.cell is None


# ---------------------------------------------------------------------------
# Inaktiv-Regression
# ---------------------------------------------------------------------------


def test_inactive_emits_no_cell_point() -> None:
    trace = _run(_device(None), ticks=5)
    assert {p.metric for p in trace} == {"power_kw", "soc_kwh", "soc_pct"}


def test_inactive_snapshot_has_no_cell_keys() -> None:
    device = _device(None)
    _run(device, ticks=3)
    snap = device.snapshot()
    assert "cell_voltages_v" not in snap
    assert "cell" not in snap["config"]  # type: ignore[operator]


# ---------------------------------------------------------------------------
# Aktiv — noise=0 (alle Zellen identisch, kein RandomPort)
# ---------------------------------------------------------------------------


def test_quiet_cells_are_identical_and_delta_zero() -> None:
    trace = _run(_device(_CELL_QUIET), ticks=1)
    deltas = _deltas(trace)
    assert deltas == [Decimal("0")]


def test_quiet_works_without_random_after_resume() -> None:
    """`noise=0` zieht keinen `RandomPort` → laeuft auch nach `from_snapshot`
    ohne `attach_random` (kein fail-loud)."""
    device = _device(_CELL_QUIET)
    _run(device, ticks=3)
    restored = BatteryDevice.from_snapshot(device.snapshot())
    # kein attach_random — darf NICHT werfen (noise=0)
    outcome = restored.tick(DeviceTickContext(tick=3, simulation_time=3000, tick_ms=1000))
    assert any(p.metric == "cell_voltage_delta_v" for p in outcome.telemetry)


# ---------------------------------------------------------------------------
# Aktiv — noise>0
# ---------------------------------------------------------------------------


def test_noisy_emits_delta_point_sorted_first() -> None:
    trace = _run(_device(_CELL_NOISY), ticks=1)
    metrics = tuple(p.metric for p in trace)
    assert metrics == ("cell_voltage_delta_v", "power_kw", "soc_kwh", "soc_pct")
    delta_point = trace[0]
    assert delta_point.unit == "V"
    assert delta_point.value > Decimal("0")


def test_noisy_delta_within_amplitude_bound() -> None:
    """delta = max-min liegt in `[0, 2*amp)` (Rauschen in `[-amp, +amp)`)."""
    deltas = _deltas(_run(_device(_CELL_NOISY), ticks=50))
    assert all(Decimal("0") <= d < Decimal("1.0") for d in deltas)  # 2*0.5
    assert any(d > Decimal("0") for d in deltas)


# ---------------------------------------------------------------------------
# Determinismus + Resume
# ---------------------------------------------------------------------------


def test_noisy_trace_is_deterministic() -> None:
    a = _deltas(_run(_device(_CELL_NOISY, seed=7), ticks=100))
    b = _deltas(_run(_device(_CELL_NOISY, seed=7), ticks=100))
    assert a == b
    assert len(a) == 100


def test_different_seed_differs() -> None:
    a = _deltas(_run(_device(_CELL_NOISY, seed=1), ticks=30))
    b = _deltas(_run(_device(_CELL_NOISY, seed=2), ticks=30))
    assert a != b


def test_resume_without_attach_random_is_fail_loud() -> None:
    """Aktives Rauschen + `from_snapshot` ohne `attach_random` → der erste
    Tick wirft fail-loud statt nicht-deterministisch weiterzulaufen."""
    device = _device(_CELL_NOISY)
    _run(device, ticks=5)
    restored = BatteryDevice.from_snapshot(device.snapshot())
    with pytest.raises(DeviceNotInitializedError):
        restored.tick(DeviceTickContext(tick=5, simulation_time=5000, tick_ms=1000))


def test_resume_is_tick_keyed_continuous() -> None:
    """Tick-gekeyte Sub-Ports → der resumte Trace ist byte-kontinuierlich mit
    einem ununterbrochenen Lauf (kein Fresh-Start-Bruch)."""
    straight = _deltas(_run(_device(_CELL_NOISY, seed=3), ticks=60))

    split = _device(_CELL_NOISY, seed=3)
    _run(split, ticks=30)
    resumed = BatteryDevice.from_snapshot(split.snapshot())
    resumed.set_run_id("")
    resumed.attach_random(FixedSeedRandom(seed=3))
    tail: list[Decimal] = []
    for tick in range(30, 60):
        outcome = resumed.tick(
            DeviceTickContext(tick=tick, simulation_time=tick * 1000, tick_ms=1000)
        )
        tail.extend(p.value for p in outcome.telemetry if p.metric == "cell_voltage_delta_v")

    assert tail == straight[30:]


def test_active_snapshot_roundtrip_byte_stable() -> None:
    device = _device(_CELL_NOISY)
    _run(device, ticks=10)
    state = device.snapshot()
    assert "cell_voltages_v" in state
    assert "cell" in state["config"]  # type: ignore[operator]
    restored = BatteryDevice.from_snapshot(state)
    assert restored == device
    assert restored.snapshot() == state


# ---------------------------------------------------------------------------
# Params-Typpruefung (n_cells ist int)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_n_cells", [True, 4.0, "4"])
def test_params_n_cells_must_be_int(bad_n_cells: object) -> None:
    cell = dict(_CELL_QUIET)
    cell["n_cells"] = bad_n_cells
    with pytest.raises(WrongTypeError) as exc_info:
        _device(cell)
    assert exc_info.value.subsystem == "battery"
    assert "n_cells" in str(exc_info.value)


def test_params_cell_non_decimal_rejected() -> None:
    cell = dict(_CELL_QUIET)
    cell["nominal_pack_voltage_v"] = 400.0  # float statt Decimal
    with pytest.raises(WrongTypeError) as exc_info:
        _device(cell)
    assert "nominal_pack_voltage_v" in str(exc_info.value)


def _init_cell(block: object) -> None:
    BatteryDevice().initialize(
        ScenarioDevice(id="battery-1", type="battery", params={**_BASE_PARAMS, "cell": block}),
        FixedSeedRandom(seed=0),
    )


def test_params_cell_non_mapping_rejected() -> None:
    with pytest.raises(WrongTypeError) as exc_info:
        _init_cell(["not", "a", "mapping"])
    assert exc_info.value.subsystem == "battery"
    assert "cell" in str(exc_info.value)


def test_params_cell_missing_key_rejected() -> None:
    with pytest.raises(MissingKeysError) as exc_info:
        _init_cell({"nominal_pack_voltage_v": Decimal("400"), "n_cells": 4})
    assert "noise_amplitude_v" in str(exc_info.value)


def test_battery_config_rejects_non_cell_config() -> None:
    with pytest.raises(BatteryConfigInvalidValueError) as exc_info:
        BatteryConfig(
            capacity_kwh=Decimal("1000"),
            initial_soc_pct=Decimal("50"),
            min_soc_pct=Decimal("10"),
            max_soc_pct=Decimal("90"),
            max_charge_kw=Decimal("500"),
            max_discharge_kw=Decimal("500"),
            charge_efficiency=Decimal("1"),
            discharge_efficiency=Decimal("1"),
            ramp_kw_per_s=Decimal("50"),
            cell="not-a-config",  # type: ignore[arg-type]
        )
    assert "cell" in str(exc_info.value)
