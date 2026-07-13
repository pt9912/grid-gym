"""Tests fuer die opt-in Battery-Field-Envelope-Emissionen (Slice 077 S1, ADR 0077):
`soh_percent`/`HealthConfig`, `dc_voltage`/`DcBusConfig`, `reactive_power_kvar`/
`ReactiveConfig` + die Fault-Status-Surface (`available`/`fault_status`).

Pinnt:
- Config-Validierung je Block + die `dc_bus`↔`cell`-Nennspannungs-Versoehnung.
- **Inaktiv-Regression** (Pin-Neutralitaet): ohne die Bloecke kein neuer Punkt,
  kein `efc`/Config-Block im Snapshot — bit-genau ADR 0014.
- **Aktiv**: konkrete Formel-Pins (soh-Degradation, IR-Drop-Vorzeichen, q_factor),
  alphabetische Emissions-Reihenfolge.
- Fault-Surface: `ok`/verfuegbar ↔ aktiver `cell_failure`.
- Opt-in Snapshot-Roundtrip (efc) + Resume + Determinismus.
"""

from __future__ import annotations

from decimal import Decimal
from itertools import pairwise

import pytest

from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.battery.config import (
    BatteryConfig,
    BatteryConfigInconsistentRangeError,
    BatteryConfigInvalidValueError,
    DcBusConfig,
    HealthConfig,
    ReactiveConfig,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import MissingKeysError, WrongTypeError
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom

_BASE_PARAMS: dict[str, object] = {
    "capacity_kwh": Decimal("1000000"),
    "initial_soc_pct": Decimal("50"),
    "min_soc_pct": Decimal("0"),
    "max_soc_pct": Decimal("100"),
    "max_charge_kw": Decimal("500"),
    "max_discharge_kw": Decimal("500"),
    "charge_efficiency": Decimal("1"),
    "discharge_efficiency": Decimal("1"),
    "ramp_kw_per_s": Decimal("1000"),
}
_HEALTH_PARAMS: dict[str, object] = {
    "initial_soh_pct": Decimal("99"),
    "degradation_pct_per_full_cycle": Decimal("0"),
}
_DC_BUS_PARAMS: dict[str, object] = {
    "nominal_voltage_v": Decimal("800"),
    "ocv_soc_slope_v": Decimal("0"),
    "internal_resistance_ohm": Decimal("0"),
}
_REACTIVE_PARAMS: dict[str, object] = {"power_factor": Decimal("1")}


def _params(**blocks: dict[str, object]) -> dict[str, object]:
    return {**_BASE_PARAMS, **blocks}


def _device(seed: int = 0, **blocks: dict[str, object]) -> BatteryDevice:
    device = BatteryDevice()
    device.initialize(
        ScenarioDevice(id="battery-1", type="battery", params=_params(**blocks)),
        FixedSeedRandom(seed=seed),
    )
    return device


def _command(value: Decimal) -> Command:
    return Command(
        command_id="cmd-0",
        simulation_time=0,
        target_device_id="battery-1",
        type="set_power_kw",
        payload={"value": value},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _run(
    device: BatteryDevice, power: Decimal, ticks: int, *, tick_ms: int = 1000
) -> tuple[TelemetryPoint, ...]:
    device.apply_command(_command(power))
    out: list[TelemetryPoint] = []
    for tick in range(ticks):
        out.extend(
            device.tick(
                DeviceTickContext(tick=tick, simulation_time=tick * tick_ms, tick_ms=tick_ms)
            ).telemetry
        )
    return tuple(out)


def _values(trace: tuple[TelemetryPoint, ...], metric: str) -> list[Decimal]:
    return [p.value for p in trace if p.metric == metric]


# ---------------------------------------------------------------------------
# Config-Validierung
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [Decimal("0"), Decimal("-1"), Decimal("100.001")])
def test_health_config_rejects_soh_out_of_range(bad: Decimal) -> None:
    with pytest.raises(BatteryConfigInvalidValueError):
        HealthConfig(initial_soh_pct=bad)


def test_health_config_rejects_negative_degradation() -> None:
    with pytest.raises(BatteryConfigInvalidValueError):
        HealthConfig(initial_soh_pct=Decimal("100"), degradation_pct_per_full_cycle=Decimal("-1"))


def test_dc_bus_config_rejects_non_positive_nominal() -> None:
    with pytest.raises(BatteryConfigInvalidValueError):
        DcBusConfig(nominal_voltage_v=Decimal("0"))


def test_dc_bus_config_rejects_negative_resistance() -> None:
    with pytest.raises(BatteryConfigInvalidValueError):
        DcBusConfig(nominal_voltage_v=Decimal("800"), internal_resistance_ohm=Decimal("-1"))


@pytest.mark.parametrize("bad", [Decimal("0"), Decimal("-0.5"), Decimal("1.0001")])
def test_reactive_config_rejects_pf_out_of_range(bad: Decimal) -> None:
    with pytest.raises(BatteryConfigInvalidValueError):
        ReactiveConfig(power_factor=bad)


def test_reactive_q_factor_pin() -> None:
    # q_factor = sqrt(1 - pf^2)/pf; pf=0.8 -> sqrt(0.36)/0.8 = 0.6/0.8 = 0.75.
    assert ReactiveConfig(power_factor=Decimal("0.8")).q_factor == Decimal("0.75")
    assert ReactiveConfig(power_factor=Decimal("1")).q_factor == Decimal("0")


def _full_config(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "capacity_kwh": Decimal("1000"),
        "initial_soc_pct": Decimal("50"),
        "min_soc_pct": Decimal("10"),
        "max_soc_pct": Decimal("90"),
        "max_charge_kw": Decimal("500"),
        "max_discharge_kw": Decimal("500"),
        "charge_efficiency": Decimal("1"),
        "discharge_efficiency": Decimal("1"),
        "ramp_kw_per_s": Decimal("50"),
    }
    return {**base, **over}


def test_battery_config_field_blocks_default_none() -> None:
    config = BatteryConfig(**_full_config())  # type: ignore[arg-type]
    assert config.health is None and config.dc_bus is None and config.reactive is None


def test_dc_bus_cell_nominal_voltage_must_agree() -> None:
    from grid_gym.hexagon.core.devices.battery.config import CellConfig

    with pytest.raises(BatteryConfigInconsistentRangeError):
        BatteryConfig(
            **_full_config(  # type: ignore[arg-type]
                dc_bus=DcBusConfig(nominal_voltage_v=Decimal("800")),
                cell=CellConfig(nominal_pack_voltage_v=Decimal("799"), n_cells=200),
            )
        )
    # Uebereinstimmend -> ok.
    BatteryConfig(
        **_full_config(  # type: ignore[arg-type]
            dc_bus=DcBusConfig(nominal_voltage_v=Decimal("800")),
            cell=CellConfig(nominal_pack_voltage_v=Decimal("800"), n_cells=200),
        )
    )


@pytest.mark.parametrize("block", ["health", "dc_bus", "reactive"])
def test_params_block_missing_key_rejected(block: str) -> None:
    params_map = {"health": _HEALTH_PARAMS, "dc_bus": _DC_BUS_PARAMS, "reactive": _REACTIVE_PARAMS}
    incomplete = dict(params_map[block])
    incomplete.pop(next(iter(incomplete)))
    with pytest.raises(MissingKeysError):
        BatteryDevice().initialize(
            ScenarioDevice(
                id="battery-1", type="battery", params={**_BASE_PARAMS, block: incomplete}
            ),
            FixedSeedRandom(seed=0),
        )


def test_params_block_non_decimal_rejected() -> None:
    bad = {
        "nominal_voltage_v": 800.0,
        "ocv_soc_slope_v": Decimal("0"),
        "internal_resistance_ohm": Decimal("0"),
    }
    with pytest.raises(WrongTypeError):
        BatteryDevice().initialize(
            ScenarioDevice(id="battery-1", type="battery", params={**_BASE_PARAMS, "dc_bus": bad}),
            FixedSeedRandom(seed=0),
        )


# ---------------------------------------------------------------------------
# Inaktiv-Regression (Pin-Neutralitaet)
# ---------------------------------------------------------------------------


def test_inactive_emits_only_base_metrics() -> None:
    trace = _run(_device(), Decimal("250"), ticks=5)
    assert {p.metric for p in trace} == {"power_kw", "soc_kwh", "soc_pct"}


def test_inactive_snapshot_has_no_field_envelope_keys() -> None:
    device = _device()
    _run(device, Decimal("250"), ticks=3)
    snap = device.snapshot()
    assert "efc" not in snap
    config = snap["config"]
    assert isinstance(config, dict)
    assert "health" not in config and "dc_bus" not in config and "reactive" not in config


# ---------------------------------------------------------------------------
# soh_percent (HealthConfig)
# ---------------------------------------------------------------------------


def test_soh_constant_without_degradation() -> None:
    trace = _run(_device(health=_HEALTH_PARAMS), Decimal("-250"), ticks=20)
    soh = _values(trace, "soh_percent")
    assert soh == [Decimal("99.000000")] * 20


def test_soh_degrades_monotonically() -> None:
    # Kleine Kapazitaet -> spuerbarer EFC-Durchsatz; Degradation > 0.
    health = {"initial_soh_pct": Decimal("100"), "degradation_pct_per_full_cycle": Decimal("5")}
    params = {**_BASE_PARAMS, "capacity_kwh": Decimal("10"), "health": health}
    device = BatteryDevice()
    device.initialize(
        ScenarioDevice(id="battery-1", type="battery", params=params), FixedSeedRandom(0)
    )
    soh = _values(_run(device, Decimal("-2"), ticks=30, tick_ms=1000), "soh_percent")
    assert all(b < a for a, b in pairwise(soh))  # streng fallend
    assert soh[0] < Decimal("100")


def test_soh_degradation_rate_exact_pin() -> None:
    # Review-Fund (Rate-Pin gegen den 2*capacity-Nenner): capacity=10, degradation=5,
    # P=-2, dt=1s -> ΔSOC=-2/3600, efc=(2/3600)/(2*10)=1/36000,
    # soh = 100 - 5/36000 = 99.999861 (6dp, ROUND_HALF_EVEN).
    health = {"initial_soh_pct": Decimal("100"), "degradation_pct_per_full_cycle": Decimal("5")}
    params = {**_BASE_PARAMS, "capacity_kwh": Decimal("10"), "health": health}
    device = BatteryDevice()
    device.initialize(
        ScenarioDevice(id="battery-1", type="battery", params=params), FixedSeedRandom(0)
    )
    assert _values(_run(device, Decimal("-2"), ticks=1), "soh_percent") == [Decimal("99.999861")]


def test_soh_efc_counts_actual_throughput_at_saturation() -> None:
    # Review-Fund (F1/MEDIUM1): bei SOC-Saturation zaehlt EFC nur den TATSAECHLICH
    # geflossenen Durchsatz, nicht die intendierte (pre-clamp) Energie.
    # capacity=1, initial_soc=0.5 kWh (min=0), discharge -500 kW: nach ~4 Ticks ist
    # die Batterie leer (0.5 kWh geflossen) -> efc = 0.5/(2*1) = 0.25 ->
    # soh = 100 - 10*0.25 = 97.5, danach EINGEFROREN (kein Ghost-Cycling).
    health = {"initial_soh_pct": Decimal("100"), "degradation_pct_per_full_cycle": Decimal("10")}
    params = {
        **_BASE_PARAMS,
        "capacity_kwh": Decimal("1"),
        "initial_soc_pct": Decimal("50"),
        "health": health,
    }
    device = BatteryDevice()
    device.initialize(
        ScenarioDevice(id="battery-1", type="battery", params=params), FixedSeedRandom(0)
    )
    soh = _values(_run(device, Decimal("-500"), ticks=20), "soh_percent")
    assert soh[-1] == Decimal("97.500000")  # tatsaechlicher Durchsatz, nicht pre-clamp
    assert soh[-1] == soh[-2]  # nach Saturation eingefroren


def test_soh_clamped_at_zero() -> None:
    health = {"initial_soh_pct": Decimal("1"), "degradation_pct_per_full_cycle": Decimal("1000000")}
    params = {**_BASE_PARAMS, "capacity_kwh": Decimal("1"), "health": health}
    device = BatteryDevice()
    device.initialize(
        ScenarioDevice(id="battery-1", type="battery", params=params), FixedSeedRandom(0)
    )
    soh = _values(_run(device, Decimal("-1"), ticks=10), "soh_percent")
    assert soh[-1] == Decimal("0.000000")
    assert all(v >= Decimal("0") for v in soh)


# ---------------------------------------------------------------------------
# dc_voltage (DcBusConfig)
# ---------------------------------------------------------------------------


def test_dc_voltage_constant_at_nominal_by_default() -> None:
    # slope=0, R=0 -> dc_voltage == nominal, unabhaengig von Power/SOC.
    trace = _run(_device(dc_bus=_DC_BUS_PARAMS), Decimal("250"), ticks=5)
    assert _values(trace, "dc_voltage") == [Decimal("800.000000")] * 5


def test_dc_voltage_ir_drop_raises_on_charge() -> None:
    # Laden (P=+250) hebt die Klemmenspannung UEBER OCV: nominal=800, R=0.1,
    # i_dc=250*1000/800=312.5 A -> dc_voltage = 800 + 312.5*0.1 = 831.25.
    dc_bus = {
        "nominal_voltage_v": Decimal("800"),
        "ocv_soc_slope_v": Decimal("0"),
        "internal_resistance_ohm": Decimal("0.1"),
    }
    trace = _run(_device(dc_bus=dc_bus), Decimal("250"), ticks=1)
    assert _values(trace, "dc_voltage") == [Decimal("831.250000")]


def test_dc_voltage_ir_drop_lowers_on_discharge() -> None:
    # Entladen (P=-250) senkt die Klemmenspannung UNTER OCV.
    dc_bus = {
        "nominal_voltage_v": Decimal("800"),
        "ocv_soc_slope_v": Decimal("0"),
        "internal_resistance_ohm": Decimal("0.1"),
    }
    trace = _run(_device(dc_bus=dc_bus), Decimal("-250"), ticks=1)
    assert _values(trace, "dc_voltage")[0] < Decimal("800")


@pytest.mark.parametrize(
    ("initial_soc", "expected"),
    [
        (Decimal("100"), Decimal("850.000000")),  # soc_frac=1.0 -> ocv=800+100*0.5
        (Decimal("50"), Decimal("800.000000")),  # soc_frac=0.5 -> Slope-Term=0
        (Decimal("0"), Decimal("750.000000")),  # soc_frac=0.0 -> ocv=800+100*(-0.5)
    ],
)
def test_dc_voltage_ocv_soc_slope_activates_term(initial_soc: Decimal, expected: Decimal) -> None:
    # Review-Fund (MEDIUM3): der `slope*(soc_frac - 0.5)`-Zweig war ungetestet.
    # slope=100, R=0, P=0 -> dc_voltage = ocv (i_dc=0), verschiebt mit SOC.
    dc_bus = {
        "nominal_voltage_v": Decimal("800"),
        "ocv_soc_slope_v": Decimal("100"),
        "internal_resistance_ohm": Decimal("0"),
    }
    params = {**_BASE_PARAMS, "initial_soc_pct": initial_soc, "dc_bus": dc_bus}
    device = BatteryDevice()
    device.initialize(
        ScenarioDevice(id="battery-1", type="battery", params=params), FixedSeedRandom(0)
    )
    assert _values(_run(device, Decimal("0"), ticks=1), "dc_voltage") == [expected]


@pytest.mark.parametrize("slope", [Decimal("1600"), Decimal("-1600"), Decimal("2000")])
def test_dc_bus_rejects_slope_that_could_make_ocv_nonpositive(slope: Decimal) -> None:
    # Review-Fund (F2): |slope| >= 2*nominal koennte ocv <= 0 treiben -> fail-fast.
    with pytest.raises(BatteryConfigInvalidValueError):
        DcBusConfig(nominal_voltage_v=Decimal("800"), ocv_soc_slope_v=slope)


def test_dc_bus_accepts_slope_within_bound() -> None:
    DcBusConfig(nominal_voltage_v=Decimal("800"), ocv_soc_slope_v=Decimal("1599"))


# ---------------------------------------------------------------------------
# reactive_power_kvar (ReactiveConfig)
# ---------------------------------------------------------------------------


def test_reactive_zero_at_unity_pf() -> None:
    trace = _run(_device(reactive=_REACTIVE_PARAMS), Decimal("250"), ticks=3)
    assert _values(trace, "reactive_power_kvar") == [Decimal("0.000000")] * 3


def test_reactive_pin_at_pf_0_8() -> None:
    # Q = |P| * q_factor; P=250, pf=0.8 -> q_factor=0.75 -> Q = 187.5.
    trace = _run(_device(reactive={"power_factor": Decimal("0.8")}), Decimal("250"), ticks=1)
    assert _values(trace, "reactive_power_kvar") == [Decimal("187.500000")]


# ---------------------------------------------------------------------------
# Alphabetische Emissions-Reihenfolge (alle Bloecke aktiv)
# ---------------------------------------------------------------------------


def test_all_blocks_emit_sorted_alphabetically() -> None:
    trace = _run(
        _device(health=_HEALTH_PARAMS, dc_bus=_DC_BUS_PARAMS, reactive=_REACTIVE_PARAMS),
        Decimal("250"),
        ticks=1,
    )
    assert tuple(p.metric for p in trace) == (
        "dc_voltage",
        "power_kw",
        "reactive_power_kvar",
        "soc_kwh",
        "soc_pct",
        "soh_percent",
    )
    units = {p.metric: p.unit for p in trace}
    assert units["dc_voltage"] == "V"
    assert units["reactive_power_kvar"] == "kvar"
    assert units["soh_percent"] == "pct"


# ---------------------------------------------------------------------------
# Fault-Status-Surface (ADR 0077 §2.5)
# ---------------------------------------------------------------------------


def test_fault_surface_ok_without_fault() -> None:
    device = _device()
    assert device.fault_status == "ok"
    assert device.available is True


def test_fault_surface_reflects_cell_failure() -> None:
    device = _device()
    device.inject_fault("cell_failure", {})
    assert device.fault_status == "cell_failure"
    assert device.available is False
    device.clear_fault("cell_failure")
    assert device.fault_status == "ok"
    assert device.available is True


def test_fault_surface_survives_snapshot_resume() -> None:
    # Die Surface ist eine Projektion des snapshot-erfassten `_cell_failure_active`-
    # Flags -> nach `from_snapshot` konsistent.
    device = _device()
    device.inject_fault("cell_failure", {})
    restored = BatteryDevice.from_snapshot(device.snapshot())
    assert restored.fault_status == "cell_failure"
    assert restored.available is False


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip + Resume + Determinismus
# ---------------------------------------------------------------------------


def test_health_snapshot_roundtrip_and_resume() -> None:
    health = {"initial_soh_pct": Decimal("100"), "degradation_pct_per_full_cycle": Decimal("5")}
    params = {**_BASE_PARAMS, "capacity_kwh": Decimal("10"), "health": health}

    def _build() -> BatteryDevice:
        d = BatteryDevice()
        d.initialize(
            ScenarioDevice(id="battery-1", type="battery", params=params), FixedSeedRandom(0)
        )
        return d

    straight = _values(_run(_build(), Decimal("-2"), ticks=40), "soh_percent")

    split = _build()
    _run(split, Decimal("-2"), ticks=20)
    restored = BatteryDevice.from_snapshot(split.snapshot())
    assert restored == split
    assert restored.snapshot() == split.snapshot()
    restored.set_run_id("")
    tail = _values(_run(restored, Decimal("-2"), ticks=20), "soh_percent")
    assert straight[20:] == tail


def test_field_envelope_snapshot_byte_stable_all_blocks() -> None:
    device = _device(health=_HEALTH_PARAMS, dc_bus=_DC_BUS_PARAMS, reactive=_REACTIVE_PARAMS)
    _run(device, Decimal("-300"), ticks=15)
    restored = BatteryDevice.from_snapshot(device.snapshot())
    assert restored == device
    assert restored.snapshot() == device.snapshot()
