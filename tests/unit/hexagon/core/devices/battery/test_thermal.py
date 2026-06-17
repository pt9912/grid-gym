"""Tests fuer die opt-in Battery-Temperatur-Telemetrie (M8 Welle 4a,
`GG-BESS-006`, ADR 0065).

Pinnt:
- `ThermalConfig`-Validierung (positiv-Felder, negatives `ambient_temp_c`
  erlaubt).
- **Inaktiv-Regression**: ohne `thermal`-Block kein `temperature_celsius`-
  Punkt (3 Metriken/Tick wie heute), kein Snapshot-State (`thermal`-Block +
  `temperature_celsius`-Key fehlen) — bit-genau ADR 0014.
- **Aktiv**: Kaltstart auf `ambient_temp_c`, stateful Euler-Schritt
  (konkreter Tick-1-Pin), Aufheiz-Monotonie + Steady-State gegen `theta_ss`,
  Abkuehl-Monotonie, vierter `temperature_celsius`-Punkt (`unit="degC"`,
  alphabetisch zuletzt).
- Opt-in Snapshot-Roundtrip (byte-stabil) + Resume-`from_snapshot` mit
  Thermo-State.
- ≥ 100-Tick-Determinismus der T-Spur (gleicher Input -> identische Trace).
"""

from __future__ import annotations

from decimal import Decimal
from itertools import pairwise

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.battery.config import (
    BatteryConfig,
    BatteryConfigInvalidValueError,
    ThermalConfig,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import MissingKeysError, WrongTypeError
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom

# Grosse Kapazitaet, damit der SOC ueber lange Heiz-/Kuehl-Laeufe nie
# saettigt (Saturation wuerde die Power auf 0 resetten und die konstante-
# Last-Annahme der Thermo-Pins brechen).
_BASE_PARAMS: dict[str, object] = {
    "capacity_kwh": Decimal("1000000"),
    "initial_soc_pct": Decimal("50"),
    "min_soc_pct": Decimal("0"),
    "max_soc_pct": Decimal("100"),
    "max_charge_kw": Decimal("500"),
    "max_discharge_kw": Decimal("500"),
    "charge_efficiency": Decimal("1"),
    "discharge_efficiency": Decimal("1"),
    # Ramp gross genug, damit die Soll-Power im ersten Tick erreicht wird.
    "ramp_kw_per_s": Decimal("1000"),
}

_THERMAL_PARAMS: dict[str, object] = {
    "ambient_temp_c": Decimal("20"),
    "thermal_rise_c_at_full_load": Decimal("40"),
    "thermal_time_constant_s": Decimal("600"),
}


def _params(*, thermal: bool) -> dict[str, object]:
    params = dict(_BASE_PARAMS)
    if thermal:
        params["thermal"] = dict(_THERMAL_PARAMS)
    return params


def _device(*, thermal: bool, seed: int = 0) -> BatteryDevice:
    device = BatteryDevice()
    device.initialize(
        ScenarioDevice(id="battery-1", type="battery", params=_params(thermal=thermal)),
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
        outcome = device.tick(
            DeviceTickContext(tick=tick, simulation_time=tick * tick_ms, tick_ms=tick_ms)
        )
        out.extend(outcome.telemetry)
    return tuple(out)


def _temps(trace: tuple[TelemetryPoint, ...]) -> list[Decimal]:
    return [p.value for p in trace if p.metric == "temperature_celsius"]


# ---------------------------------------------------------------------------
# ThermalConfig-Validierung
# ---------------------------------------------------------------------------


def test_thermal_config_accepts_valid_values() -> None:
    thermal = ThermalConfig(
        ambient_temp_c=Decimal("20"),
        thermal_rise_c_at_full_load=Decimal("40"),
        thermal_time_constant_s=Decimal("600"),
    )
    assert thermal.ambient_temp_c == Decimal("20")


def test_thermal_config_allows_negative_ambient() -> None:
    """Tiefsttemperatur-Umgebung (z. B. -20 degC Aussenschrank) ist
    gueltig — `ambient_temp_c` hat keine Positiv-Invariante (ADR 0065 §2.1)."""
    thermal = ThermalConfig(
        ambient_temp_c=Decimal("-20"),
        thermal_rise_c_at_full_load=Decimal("40"),
        thermal_time_constant_s=Decimal("600"),
    )
    assert thermal.ambient_temp_c == Decimal("-20")


@pytest.mark.parametrize("field", ["thermal_rise_c_at_full_load", "thermal_time_constant_s"])
@pytest.mark.parametrize("bad", [Decimal("0"), Decimal("-1")])
def test_thermal_config_rejects_non_positive(field: str, bad: Decimal) -> None:
    fields = dict(_THERMAL_PARAMS)
    fields[field] = bad
    with pytest.raises(BatteryConfigInvalidValueError) as exc_info:
        ThermalConfig(**fields)  # type: ignore[arg-type]
    assert field in str(exc_info.value)


def test_battery_config_thermal_defaults_none() -> None:
    """Ohne `thermal`-Argument ist das Thermomodell inaktiv (Default)."""
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
    assert config.thermal is None


def _init_with_thermal_params(thermal_block: object) -> None:
    BatteryDevice().initialize(
        ScenarioDevice(
            id="battery-1",
            type="battery",
            params={**_BASE_PARAMS, "thermal": thermal_block},
        ),
        FixedSeedRandom(seed=0),
    )


def test_params_thermal_non_mapping_rejected() -> None:
    """`_thermal_from_params`: nicht-Mapping `thermal` → `WrongTypeError`."""
    with pytest.raises(WrongTypeError) as exc_info:
        _init_with_thermal_params(["not", "a", "mapping"])
    assert exc_info.value.subsystem == "battery"
    assert "thermal" in str(exc_info.value)


def test_params_thermal_missing_key_rejected() -> None:
    """`_thermal_from_params`: fehlender Pflicht-Key → `MissingKeysError`."""
    block = dict(_THERMAL_PARAMS)
    del block["thermal_time_constant_s"]
    with pytest.raises(MissingKeysError) as exc_info:
        _init_with_thermal_params(block)
    assert exc_info.value.subsystem == "battery"
    assert "thermal_time_constant_s" in str(exc_info.value)


def test_params_thermal_non_decimal_value_rejected() -> None:
    """`_thermal_from_params`: No-float-Pruefung (`GG-DATA-005`) — ein
    nicht-`Decimal`-Wert → `WrongTypeError`."""
    block = dict(_THERMAL_PARAMS)
    block["ambient_temp_c"] = 20.0  # float statt Decimal
    with pytest.raises(WrongTypeError) as exc_info:
        _init_with_thermal_params(block)
    assert exc_info.value.subsystem == "battery"
    assert "thermal" in str(exc_info.value)


def test_battery_config_rejects_non_thermal_config() -> None:
    """Defensiver Typ-Guard (ADR 0065 §2.1): `thermal` ist `None` oder
    `ThermalConfig`."""
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
            thermal="not-a-config",  # type: ignore[arg-type]
        )
    assert "thermal" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Inaktiv-Regression (kein thermal-Block)
# ---------------------------------------------------------------------------


def test_inactive_emits_no_temperature_point() -> None:
    """Ohne `thermal`-Block: 3 Metriken/Tick wie heute (ADR 0014 §2.4),
    kein `temperature_celsius`-Punkt (nicht `0`)."""
    trace = _run(_device(thermal=False), Decimal("250"), ticks=10)
    metrics = {p.metric for p in trace}
    assert metrics == {"power_kw", "soc_kwh", "soc_pct"}
    assert len(trace) == 30


def test_inactive_snapshot_has_no_thermal_keys() -> None:
    """Ohne `thermal`-Block: Snapshot traegt weder den Config-`thermal`-
    Block noch den Top-Level `temperature_celsius`-Key (Pin-Neutralitaet)."""
    device = _device(thermal=False)
    _run(device, Decimal("250"), ticks=5)
    snap = device.snapshot()
    assert "temperature_celsius" not in snap
    assert "thermal" not in snap["config"]  # type: ignore[operator]


# ---------------------------------------------------------------------------
# Aktiv — Modell-Verhalten
# ---------------------------------------------------------------------------


def test_active_cold_start_at_ambient() -> None:
    """Kaltstart auf `ambient_temp_c` (ADR 0065 §2.4): nach `initialize`,
    vor jedem Tick, traegt der Snapshot die Umgebungstemperatur."""
    device = _device(thermal=True)
    assert device.snapshot()["temperature_celsius"] == Decimal("20")


def test_active_first_tick_euler_pin() -> None:
    """Konkreter Euler-Pin: dt=1s, tau=600, ambient=20, rise=40, P=-250
    -> load_pu=0.5, theta_ss=30, theta=20+(30-20)*(1/600)=20.016667."""
    trace = _run(_device(thermal=True), Decimal("-250"), ticks=1)
    assert _temps(trace) == [Decimal("20.016667")]


def test_active_emits_fourth_point_sorted_last() -> None:
    """Vierter Punkt `temperature_celsius` (`unit="degC"`), alphabetisch
    hinter `soc_pct` (ADR 0065 §2.3)."""
    trace = _run(_device(thermal=True), Decimal("250"), ticks=1)
    assert tuple(p.metric for p in trace) == (
        "power_kw",
        "soc_kwh",
        "soc_pct",
        "temperature_celsius",
    )
    temp_point = trace[3]
    assert temp_point.unit == "degC"
    assert temp_point.quality.name == "VALID"


def test_active_heating_is_monotonic_and_bounded() -> None:
    """Konstante Teillast (P=-250 -> theta_ss=30): T steigt streng monoton
    von ambient und bleibt unter theta_ss."""
    temps = _temps(_run(_device(thermal=True), Decimal("-250"), ticks=50))
    assert all(b > a for a, b in pairwise(temps))
    assert temps[0] > Decimal("20")  # ueber ambient gestiegen
    assert temps[-1] < Decimal("30")  # noch unter Steady-State


def test_active_steady_state_approaches_theta_ss() -> None:
    """Volllast (P=-500 -> load_pu=1 -> theta_ss=60) ueber viele
    Zeitkonstanten: T naehert sich 60, ohne es zu ueberschreiten."""
    temps = _temps(_run(_device(thermal=True), Decimal("-500"), ticks=3000))
    assert Decimal("59") < temps[-1] < Decimal("60")


def test_active_cooling_decays_toward_ambient() -> None:
    """Nach Aufheizen faellt T bei Nulllast (theta_ss=ambient=20) streng
    monoton zurueck Richtung ambient, ohne darunter zu fallen."""
    device = _device(thermal=True)
    _run(device, Decimal("-500"), ticks=200)
    hot = device.snapshot()["temperature_celsius"]
    assert isinstance(hot, Decimal) and hot > Decimal("30")
    cool_temps = _temps(_run(device, Decimal("0"), ticks=200))
    assert all(b < a for a, b in pairwise(cool_temps))
    assert cool_temps[-1] > Decimal("20")
    assert cool_temps[-1] < hot


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip + Resume
# ---------------------------------------------------------------------------


def test_active_snapshot_roundtrip_byte_stable() -> None:
    """Opt-in Snapshot mit aktivem Thermomodell: `from_snapshot(snapshot())`
    rekonstruiert ein gleichwertiges Device (Thermo-State + Config-Block)."""
    device = _device(thermal=True)
    _run(device, Decimal("-300"), ticks=25)
    restored = BatteryDevice.from_snapshot(device.snapshot())
    assert restored == device
    assert restored.snapshot() == device.snapshot()


def test_active_resume_continues_temperature_trace() -> None:
    """Resume aus Snapshot fuehrt dieselbe T-Spur fort wie ein
    ununterbrochener Lauf (Thermo-State persistiert, ADR 0065 §2.5)."""
    straight = _temps(_run(_device(thermal=True), Decimal("-250"), ticks=60))

    split = _device(thermal=True)
    _run(split, Decimal("-250"), ticks=30)
    resumed = BatteryDevice.from_snapshot(split.snapshot())
    resumed.set_run_id("")
    tail = _temps(_run(resumed, Decimal("-250"), ticks=30))

    assert straight[30:] == tail


# ---------------------------------------------------------------------------
# Determinismus
# ---------------------------------------------------------------------------


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
@settings(deadline=None, max_examples=15)
def test_temperature_trace_is_deterministic(seed: int) -> None:
    """ADR 0065 §2.5: gleicher Input -> byte-identische T-Spur ueber
    100 Ticks (kein RandomPort-Konsum; Determinismus by-construction)."""
    trace_a = _temps(_run(_device(thermal=True, seed=seed), Decimal("-250"), ticks=100))
    trace_b = _temps(_run(_device(thermal=True, seed=seed), Decimal("-250"), ticks=100))
    assert trace_a == trace_b
    assert len(trace_a) == 100
