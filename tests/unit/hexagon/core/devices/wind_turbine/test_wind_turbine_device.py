"""Tests fuer `WindTurbineDevice` (M8 Welle 2c, ADR 0057, GG-DEV-017).

Pinnt:
- `WindTurbineConfig`-Validierung (positive rated_power, nicht-negative
  Speeds, Reihenfolge cut_in < rated < cut_out, max >= min; ADR 0057 §2.3).
- Kubische Leistungskennlinie `_power_from_curve` direkt (Zonen +
  Endpunkte) und via konstantem Wind (`min == max`) end-to-end.
- Stochastischer Windeingang: Determinismus pro Seed, Bounds.
- Snapshot-Roundtrip byte-stabil + `attach_random`-Resume-Lifecycle.
- `apply_command` → IGNORED (command-los).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import FrozenInstanceError
from decimal import Decimal
from typing import cast

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from grid_gym.hexagon.core.devices import DeviceModel
from grid_gym.hexagon.core.devices.wind_turbine import WindTurbineDevice
from grid_gym.hexagon.core.devices.wind_turbine.config import (
    WindTurbineConfig,
    WindTurbineConfigInconsistentRangeError,
    WindTurbineConfigInvalidValueError,
)
from grid_gym.hexagon.core.devices.wind_turbine.snapshot import (
    SNAPSHOT_VERSION,
    WindTurbineSnapshot,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import (
    DeviceAlreadyInitializedError,
    DeviceNotInitializedError,
    MissingKeysError,
    VersionError,
    WrongTypeError,
)
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom

_DEFAULT: dict[str, Decimal] = {
    "rated_power_kw": Decimal("2000"),
    "cut_in_speed_ms": Decimal("2"),
    "rated_speed_ms": Decimal("15"),
    "cut_out_speed_ms": Decimal("25"),
    "min_wind_speed_ms": Decimal("2"),
    "max_wind_speed_ms": Decimal("20"),
}
_ONE_HOUR_MS = 3_600_000


def _scenario_device(**overrides: Decimal) -> ScenarioDevice:
    params: dict[str, object] = {**_DEFAULT, **overrides}
    return ScenarioDevice(id="wt-1", type="wind_turbine", params=params)


def _config(**overrides: Decimal) -> WindTurbineConfig:
    return WindTurbineConfig(**{**_DEFAULT, **overrides})


def _context(tick: int = 0, tick_ms: int = 1000) -> DeviceTickContext:
    return DeviceTickContext(tick=tick, simulation_time=tick * tick_ms, tick_ms=tick_ms)


def _initialize(
    device: WindTurbineDevice, seed: int = 0, **overrides: Decimal
) -> WindTurbineDevice:
    device.initialize(_scenario_device(**overrides), FixedSeedRandom(seed=seed))
    return device


def _metrics(device: WindTurbineDevice) -> dict[str, TelemetryPoint]:
    return {p.metric: p for p in device.telemetry()}


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def test_valid_config_constructs() -> None:
    assert _config().rated_power_kw == Decimal("2000")


def test_config_is_frozen() -> None:
    with pytest.raises(FrozenInstanceError):
        _config().rated_power_kw = Decimal("1")  # type: ignore[misc]


def test_non_positive_rated_power_rejected() -> None:
    with pytest.raises(WindTurbineConfigInvalidValueError) as exc:
        _config(rated_power_kw=Decimal("0"))
    assert "rated_power_kw" in str(exc.value)


@pytest.mark.parametrize("field", ["cut_in_speed_ms", "min_wind_speed_ms"])
def test_negative_speed_rejected(field: str) -> None:
    with pytest.raises(WindTurbineConfigInvalidValueError) as exc:
        _config(**{field: Decimal("-1")})
    assert field in str(exc.value)


def test_rated_not_above_cut_in_rejected() -> None:
    with pytest.raises(WindTurbineConfigInconsistentRangeError) as exc:
        _config(cut_in_speed_ms=Decimal("15"), rated_speed_ms=Decimal("15"))
    assert "rated_speed_ms" in str(exc.value)


def test_cut_out_not_above_rated_rejected() -> None:
    with pytest.raises(WindTurbineConfigInconsistentRangeError) as exc:
        _config(rated_speed_ms=Decimal("25"), cut_out_speed_ms=Decimal("25"))
    assert "cut_out_speed_ms" in str(exc.value)


def test_max_below_min_rejected() -> None:
    with pytest.raises(WindTurbineConfigInconsistentRangeError) as exc:
        _config(min_wind_speed_ms=Decimal("10"), max_wind_speed_ms=Decimal("5"))
    assert "max_wind_speed_ms" in str(exc.value)


def test_max_equals_min_allowed() -> None:
    """ADR 0057 §2.3: `max == min` = konstanter Wind, valide."""
    config = _config(min_wind_speed_ms=Decimal("7"), max_wind_speed_ms=Decimal("7"))
    assert config.max_wind_speed_ms == config.min_wind_speed_ms


# ---------------------------------------------------------------------------
# Leistungskennlinie (_power_from_curve, ADR 0057 §2.5)
# ---------------------------------------------------------------------------


def _curve_config() -> WindTurbineConfig:
    return _config(
        rated_power_kw=Decimal("1000"),
        cut_in_speed_ms=Decimal("3"),
        rated_speed_ms=Decimal("12"),
        cut_out_speed_ms=Decimal("25"),
    )


def test_curve_below_cut_in_is_zero() -> None:
    assert WindTurbineDevice._power_from_curve(Decimal("2"), _curve_config()) == Decimal("0")


def test_curve_at_cut_in_is_zero() -> None:
    assert WindTurbineDevice._power_from_curve(Decimal("3"), _curve_config()) == Decimal("0")


def test_curve_at_rated_is_rated_power() -> None:
    assert WindTurbineDevice._power_from_curve(Decimal("12"), _curve_config()) == Decimal("1000")


def test_curve_between_rated_and_cut_out_is_rated_power() -> None:
    assert WindTurbineDevice._power_from_curve(Decimal("20"), _curve_config()) == Decimal("1000")


def test_curve_at_cut_out_is_zero() -> None:
    assert WindTurbineDevice._power_from_curve(Decimal("25"), _curve_config()) == Decimal("0")


def test_curve_above_cut_out_is_zero() -> None:
    assert WindTurbineDevice._power_from_curve(Decimal("30"), _curve_config()) == Decimal("0")


def test_curve_cubic_exact_value() -> None:
    """cut_in=0, rated=10 → P = rated * v^3 / rated^3. v=5 →
    1000 * 125 / 1000 = 125 (exakt)."""
    config = _config(
        rated_power_kw=Decimal("1000"),
        cut_in_speed_ms=Decimal("0"),
        rated_speed_ms=Decimal("10"),
        cut_out_speed_ms=Decimal("25"),
    )
    assert WindTurbineDevice._power_from_curve(Decimal("5"), config) == Decimal("125")


def test_curve_cubic_exact_value_with_nonzero_cut_in() -> None:
    """Innenwert mit aktivem `cut_in**3`-Term (cut_in != 0) — faengt
    einen Numerator-/Denominator-only-Bug, den der cut_in=0-Fall (Term
    verschwindet) verdeckt. rp=1701 cancelt den Nenner:
    P = 1701 * (7^3 - 3^3) / (12^3 - 3^3) = 1701 * 316 / 1701 = 316."""
    config = _config(
        rated_power_kw=Decimal("1701"),
        cut_in_speed_ms=Decimal("3"),
        rated_speed_ms=Decimal("12"),
        cut_out_speed_ms=Decimal("25"),
    )
    assert WindTurbineDevice._power_from_curve(Decimal("7"), config) == Decimal("316")


def test_curve_is_monotone_nondecreasing_in_ramp() -> None:
    config = _curve_config()
    speeds = [Decimal(str(v)) for v in ("3", "5", "7", "9", "11", "12")]
    powers = [WindTurbineDevice._power_from_curve(v, config) for v in speeds]
    assert powers == sorted(powers)


# ---------------------------------------------------------------------------
# Konstanter Wind (min == max) — Kennlinie end-to-end ohne RNG-Kopplung
# ---------------------------------------------------------------------------


def _constant_wind_device(speed: str, **curve: Decimal) -> WindTurbineDevice:
    return _initialize(
        WindTurbineDevice(),
        min_wind_speed_ms=Decimal(speed),
        max_wind_speed_ms=Decimal(speed),
        **curve,
    )


def test_constant_wind_emits_curve_power() -> None:
    # cut_in=0, rated=10, rated_power=1000, wind=5 → power 125.
    device = _constant_wind_device(
        "5",
        rated_power_kw=Decimal("1000"),
        cut_in_speed_ms=Decimal("0"),
        rated_speed_ms=Decimal("10"),
        cut_out_speed_ms=Decimal("25"),
    )
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    m = _metrics(device)
    assert m["wind_speed_ms"].value == Decimal("5.000000")
    assert m["power_kw"].value == Decimal("125.000000")
    # Energie-Konsistenz: 125 kW * 1 h = 125 kWh.
    assert m["generated_kwh"].value == Decimal("125.000000")


def test_constant_wind_below_cut_in_generates_zero() -> None:
    device = _constant_wind_device("1")  # default cut_in=2 → below
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    m = _metrics(device)
    assert m["power_kw"].value == Decimal("0.000000")
    assert m["generated_kwh"].value == Decimal("0.000000")


def test_constant_wind_above_cut_out_generates_zero() -> None:
    device = _constant_wind_device("30")  # default cut_out=25 → above
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    assert _metrics(device)["power_kw"].value == Decimal("0.000000")


def test_throughput_uses_dt_conversion_at_default_tick_ms() -> None:
    """generated_kwh = power * (tick_ms / 3_600_000). Pinnt dt am
    Default tick_ms=1000 (nicht nur am degenerierten 1-h-Tick)."""
    device = _constant_wind_device(
        "10",
        rated_power_kw=Decimal("1000"),
        cut_in_speed_ms=Decimal("0"),
        rated_speed_ms=Decimal("10"),
        cut_out_speed_ms=Decimal("25"),
    )  # wind 10 == rated → power 1000
    device.tick(_context(tick=0, tick_ms=1000))
    expected = (Decimal("1000") * Decimal(1000) / Decimal(3_600_000)).quantize(Decimal("0.000001"))
    assert expected == Decimal("0.277778")
    assert _metrics(device)["generated_kwh"].value == expected


def test_generated_kwh_monotone_over_ticks() -> None:
    device = _constant_wind_device(
        "8",
        rated_power_kw=Decimal("1000"),
        cut_in_speed_ms=Decimal("0"),
        rated_speed_ms=Decimal("10"),
        cut_out_speed_ms=Decimal("25"),
    )
    last = Decimal("0")
    for tick in range(10):
        device.tick(_context(tick=tick, tick_ms=1000))
        current = cast(Decimal, device.snapshot()["generated_kwh"])
        assert current >= last
        last = current


# ---------------------------------------------------------------------------
# Protocol-Adherence + Lifecycle + Command
# ---------------------------------------------------------------------------


def test_device_satisfies_device_model_protocol() -> None:
    assert isinstance(WindTurbineDevice(), DeviceModel)


def test_device_id_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        _ = WindTurbineDevice().device_id


def test_tick_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        WindTurbineDevice().tick(_context())


def test_apply_command_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        WindTurbineDevice().apply_command(_set_power_cmd())


def test_apply_command_returns_ignored() -> None:
    """ADR 0057 §2.1: Wind nimmt keine Steuerbefehle."""
    device = _initialize(WindTurbineDevice())
    assert device.apply_command(_set_power_cmd()) is CommandResult.IGNORED


def test_double_initialize_raises() -> None:
    device = _initialize(WindTurbineDevice())
    with pytest.raises(DeviceAlreadyInitializedError):
        device.initialize(_scenario_device(), FixedSeedRandom(seed=1))


def test_missing_param_raises_missing_keys() -> None:
    sd = ScenarioDevice(id="wt-1", type="wind_turbine", params={})
    with pytest.raises(MissingKeysError) as exc:
        WindTurbineDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc.value.subsystem == "wind_turbine"


def test_non_decimal_param_raises_wrong_type() -> None:
    sd = ScenarioDevice(id="wt-1", type="wind_turbine", params={**_DEFAULT, "rated_power_kw": 2000})
    with pytest.raises(WrongTypeError) as exc:
        WindTurbineDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc.value.subsystem == "wind_turbine"


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------


def test_telemetry_emits_three_metrics_sorted() -> None:
    device = _initialize(WindTurbineDevice())
    metrics = [p.metric for p in device.tick(_context(tick=0)).telemetry]
    assert metrics == ["generated_kwh", "power_kw", "wind_speed_ms"]
    assert metrics == sorted(metrics)


def test_telemetry_quality_and_quantization() -> None:
    device = _initialize(WindTurbineDevice())
    for point in device.tick(_context(tick=0)).telemetry:
        assert point.quality is Quality.VALID
        assert point.value.as_tuple().exponent == -6


def test_telemetry_pre_init_returns_empty() -> None:
    assert WindTurbineDevice().telemetry() == ()


# ---------------------------------------------------------------------------
# Stochastik: Determinismus + Bounds
# ---------------------------------------------------------------------------


def test_stochastic_power_within_bounds() -> None:
    device = _initialize(WindTurbineDevice(), seed=7)
    for tick in range(50):
        m = _metrics_after_tick(device, tick)
        power = m["power_kw"].value
        wind = m["wind_speed_ms"].value
        assert Decimal("0") <= power <= Decimal("2000")
        assert Decimal("2") <= wind < Decimal("20")  # [min, max)


def _metrics_after_tick(device: WindTurbineDevice, tick: int) -> dict[str, TelemetryPoint]:
    device.tick(_context(tick=tick))
    return _metrics(device)


def _run(seed: int) -> tuple[TelemetryPoint, ...]:
    device = WindTurbineDevice()
    device.initialize(_scenario_device(), FixedSeedRandom(seed=seed))
    out: list[TelemetryPoint] = []
    for tick in range(100):
        out.extend(device.tick(_context(tick=tick)).telemetry)
    return tuple(out)


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
@settings(deadline=None, max_examples=15)
def test_same_seed_produces_byte_identical_trace(seed: int) -> None:
    assert _run(seed) == _run(seed)


def test_different_seeds_diverge() -> None:
    """Sanity: der stochastische Eingang wirkt tatsaechlich
    (unterschiedliche Seeds → unterschiedliche Wind-Folge)."""
    assert _run(1) != _run(2)


def test_full_100_tick_trace_has_300_points() -> None:
    """ADR 0057 §2.6: 3 Metriken/Tick → 300."""
    assert len(_run(42)) == 300


class _CountingRandom:
    """Minimaler `RandomPort`-Fake, der `next_float()`-Aufrufe zaehlt
    (pinnt die §2.4-„eine Ziehung pro Tick"-Stream-Konsistenz)."""

    def __init__(self) -> None:
        self.next_float_calls = 0

    def next_float(self) -> Decimal:
        self.next_float_calls += 1
        return Decimal("0.5")

    def next_int(self, low: int, high: int) -> int:
        return low

    def sub_port(self, name: str) -> _CountingRandom:
        return self

    def snapshot(self) -> bytes:
        return b"{}"

    def snapshot_as_mapping(self) -> dict[str, object]:
        return {}


def test_exactly_one_draw_per_tick() -> None:
    rng = _CountingRandom()
    device = WindTurbineDevice()
    device.initialize(_scenario_device(), rng)
    for tick in range(5):
        device.tick(_context(tick=tick))
    assert rng.next_float_calls == 5


def test_exactly_one_draw_per_tick_even_for_constant_wind() -> None:
    """ADR 0057 §2.4: auch bei `min == max` (span 0) wird gezogen —
    sonst desynchronisiert ein Stream-sharing-Szenario."""
    rng = _CountingRandom()
    device = WindTurbineDevice()
    device.initialize(
        _scenario_device(min_wind_speed_ms=Decimal("7"), max_wind_speed_ms=Decimal("7")), rng
    )
    device.tick(_context(tick=0))
    assert rng.next_float_calls == 1


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip + attach_random-Resume (ADR 0057 §2.6)
# ---------------------------------------------------------------------------


def test_snapshot_first_field_is_version() -> None:
    state = _initialize(WindTurbineDevice()).snapshot()
    assert next(iter(state)) == "version"
    assert state["version"] == SNAPSHOT_VERSION


def test_snapshot_pre_init_returns_minimal() -> None:
    assert WindTurbineDevice().snapshot() == {"version": SNAPSHOT_VERSION}


def test_from_snapshot_byte_stable_roundtrip() -> None:
    device = _initialize(WindTurbineDevice(), seed=3)
    device.set_run_id("run-x")  # nicht-trivialer run_id muss den Roundtrip ueberleben
    device.tick(_context(tick=0))
    restored = WindTurbineDevice.from_snapshot(device.snapshot())
    assert restored == device
    assert restored.snapshot()["run_id"] == "run-x"


def test_from_snapshot_preserves_generated_kwh() -> None:
    device = _initialize(WindTurbineDevice(), seed=3)
    for tick in range(5):
        device.tick(_context(tick=tick))
    state = device.snapshot()
    restored = WindTurbineDevice.from_snapshot(state)
    assert restored.snapshot()["generated_kwh"] == state["generated_kwh"]


def test_tick_after_from_snapshot_without_attach_random_raises() -> None:
    """ADR 0057 §2.6 Resume-Vertrag: `from_snapshot` setzt `_random`
    nicht; ohne `attach_random` wirft der Tick typisiert."""
    restored = WindTurbineDevice.from_snapshot(_initialize(WindTurbineDevice()).snapshot())
    with pytest.raises(DeviceNotInitializedError):
        restored.tick(_context(tick=1))


def test_attach_random_after_from_snapshot_enables_tick() -> None:
    restored = WindTurbineDevice.from_snapshot(_initialize(WindTurbineDevice()).snapshot())
    restored.attach_random(FixedSeedRandom(seed=0))
    assert restored.tick(_context(tick=1)).telemetry


def test_eq_with_non_wind_turbine_is_not_implemented() -> None:
    assert WindTurbineDevice().__eq__(object()) is NotImplemented


def test_from_dict_missing_top_level_key() -> None:
    state = dict(_initialize(WindTurbineDevice()).snapshot())
    del state["generated_kwh"]
    with pytest.raises(MissingKeysError) as exc:
        WindTurbineSnapshot.from_dict(state)
    assert exc.value.subsystem == "wind_turbine"


def test_from_dict_unsupported_version_raises() -> None:
    state = dict(_initialize(WindTurbineDevice()).snapshot())
    state["version"] = 99
    with pytest.raises(VersionError):
        WindTurbineSnapshot.from_dict(state)


def test_from_dict_invalid_config_reraises_as_wrong_type() -> None:
    state = dict(_initialize(WindTurbineDevice()).snapshot())
    bad_config = dict(cast(Mapping[str, object], state["config"]))
    bad_config["rated_power_kw"] = Decimal("-1")
    state["config"] = bad_config
    with pytest.raises(WrongTypeError) as exc:
        WindTurbineSnapshot.from_dict(state)
    assert exc.value.subsystem == "wind_turbine"


def test_set_run_id_propagates_to_telemetry() -> None:
    device = _initialize(WindTurbineDevice())
    device.set_run_id("run-wt-1")
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == "run-wt-1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _set_power_cmd() -> Command:
    return Command(
        command_id="cmd-1",
        simulation_time=0,
        target_device_id="wt-1",
        type="set_power_kw",
        payload={"value": Decimal("100")},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )
