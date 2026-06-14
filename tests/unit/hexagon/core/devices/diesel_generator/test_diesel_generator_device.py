"""Tests fuer `DieselGeneratorDevice` (M8 Welle 2d, ADR 0058, GG-DEV-018).

Pinnt:
- `DieselGeneratorConfig`-Validierung (positive Felder, Hysterese-/Tank-
  Reihenfolge; ADR 0058 §2.3).
- Command-Surface (`set_power_kw` ACCEPTED/LIMITED auf `[0, max]`; ADR
  0058 §2.6).
- Anfahr-/Abstell-Hysterese (Zustandsmaschine; ADR 0058 §2.4).
- Ramp + Kraftstoff-Limit/run-dry (ADR 0058 §2.5).
- Snapshot-Roundtrip byte-stabil inkl. `running`-Bool + Determinismus.
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
from grid_gym.hexagon.core.devices.diesel_generator import DieselGeneratorDevice
from grid_gym.hexagon.core.devices.diesel_generator.commands import (
    COMMAND_TYPE_SET_POWER_KW,
    DieselGeneratorAlarm,
    validate_set_power_command,
)
from grid_gym.hexagon.core.devices.diesel_generator.config import (
    DieselGeneratorConfig,
    DieselGeneratorConfigInconsistentRangeError,
    DieselGeneratorConfigInvalidValueError,
)
from grid_gym.hexagon.core.devices.diesel_generator.snapshot import (
    SNAPSHOT_VERSION,
    DieselGeneratorSnapshot,
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

# Hoher Ramp (1000 kW/s) → der Ramp limitiert in den meisten Tests nicht
# (Leistung springt sofort auf den Sollwert); Ramp wird separat getestet.
_DEFAULT: dict[str, Decimal] = {
    "max_power_kw": Decimal("100"),
    "min_start_power_kw": Decimal("20"),
    "min_stop_power_kw": Decimal("10"),
    "fuel_capacity_l": Decimal("1000"),
    "initial_fuel_l": Decimal("1000"),
    "fuel_per_kwh_l": Decimal("0.3"),
    "ramp_kw_per_s": Decimal("1000"),
}


def _scenario_device(**overrides: Decimal) -> ScenarioDevice:
    params: dict[str, object] = {**_DEFAULT, **overrides}
    return ScenarioDevice(id="dg-1", type="diesel_generator", params=params)


def _config(**overrides: Decimal) -> DieselGeneratorConfig:
    return DieselGeneratorConfig(**{**_DEFAULT, **overrides})


def _cmd(value: object = Decimal("50"), command_id: str = "cmd-1") -> Command:
    return Command(
        command_id=command_id,
        simulation_time=0,
        target_device_id="dg-1",
        type=COMMAND_TYPE_SET_POWER_KW,
        payload={"value": value},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _context(tick: int = 0, tick_ms: int = 1000) -> DeviceTickContext:
    return DeviceTickContext(tick=tick, simulation_time=tick * tick_ms, tick_ms=tick_ms)


def _device(**overrides: Decimal) -> DieselGeneratorDevice:
    device = DieselGeneratorDevice()
    device.initialize(_scenario_device(**overrides), FixedSeedRandom(seed=0))
    return device


def _metrics(device: DieselGeneratorDevice) -> dict[str, TelemetryPoint]:
    return {p.metric: p for p in device.telemetry()}


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def test_valid_config_constructs() -> None:
    assert _config().max_power_kw == Decimal("100")


def test_config_is_frozen() -> None:
    with pytest.raises(FrozenInstanceError):
        _config().max_power_kw = Decimal("1")  # type: ignore[misc]


@pytest.mark.parametrize(
    "field",
    ["max_power_kw", "min_start_power_kw", "fuel_capacity_l", "fuel_per_kwh_l", "ramp_kw_per_s"],
)
def test_non_positive_required_rejected(field: str) -> None:
    with pytest.raises(DieselGeneratorConfigInvalidValueError) as exc:
        _config(**{field: Decimal("0")})
    assert field in str(exc.value)


@pytest.mark.parametrize("field", ["min_stop_power_kw", "initial_fuel_l"])
def test_negative_rejected(field: str) -> None:
    with pytest.raises(DieselGeneratorConfigInvalidValueError) as exc:
        _config(**{field: Decimal("-1")})
    assert field in str(exc.value)


def test_min_start_above_max_rejected() -> None:
    with pytest.raises(DieselGeneratorConfigInconsistentRangeError) as exc:
        _config(min_start_power_kw=Decimal("150"))
    assert "min_start_power_kw" in str(exc.value)


def test_min_stop_not_below_min_start_rejected() -> None:
    with pytest.raises(DieselGeneratorConfigInconsistentRangeError) as exc:
        _config(min_stop_power_kw=Decimal("20"), min_start_power_kw=Decimal("20"))
    assert "min_stop_power_kw" in str(exc.value)


def test_initial_fuel_above_capacity_rejected() -> None:
    with pytest.raises(DieselGeneratorConfigInconsistentRangeError) as exc:
        _config(initial_fuel_l=Decimal("2000"), fuel_capacity_l=Decimal("1000"))
    assert "initial_fuel_l" in str(exc.value)


# ---------------------------------------------------------------------------
# Protocol-Adherence + Lifecycle
# ---------------------------------------------------------------------------


def test_device_satisfies_device_model_protocol() -> None:
    assert isinstance(DieselGeneratorDevice(), DeviceModel)


def test_device_id_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        _ = DieselGeneratorDevice().device_id


def test_tick_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        DieselGeneratorDevice().tick(_context())


def test_apply_command_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        DieselGeneratorDevice().apply_command(_cmd())


def test_double_initialize_raises() -> None:
    device = _device()
    with pytest.raises(DeviceAlreadyInitializedError):
        device.initialize(_scenario_device(), FixedSeedRandom(seed=1))


def test_missing_param_raises_missing_keys() -> None:
    with pytest.raises(MissingKeysError) as exc:
        DieselGeneratorDevice().initialize(
            ScenarioDevice(id="dg-1", type="diesel_generator", params={}),
            FixedSeedRandom(seed=0),
        )
    assert exc.value.subsystem == "diesel_generator"


def test_non_decimal_param_raises_wrong_type() -> None:
    with pytest.raises(WrongTypeError) as exc:
        DieselGeneratorDevice().initialize(
            ScenarioDevice(
                id="dg-1", type="diesel_generator", params={**_DEFAULT, "max_power_kw": 100}
            ),
            FixedSeedRandom(seed=0),
        )
    assert exc.value.subsystem == "diesel_generator"


# ---------------------------------------------------------------------------
# Command-Surface (ADR 0058 §2.6)
# ---------------------------------------------------------------------------


def test_within_range_accepted() -> None:
    outcome = validate_set_power_command(
        config=_config(), command=_cmd(Decimal("50")), device_id="dg-1"
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw == Decimal("50")


def test_negative_clamped_to_zero() -> None:
    outcome = validate_set_power_command(
        config=_config(), command=_cmd(Decimal("-5")), device_id="dg-1"
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("0")
    assert outcome.alarm is not None


def test_above_max_clamped() -> None:
    outcome = validate_set_power_command(
        config=_config(), command=_cmd(Decimal("150")), device_id="dg-1"
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("100")


def test_unknown_command_type_ignored() -> None:
    cmd = Command(
        command_id="c",
        simulation_time=0,
        target_device_id="dg-1",
        type="set_mode",
        payload={"value": Decimal("5")},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )
    assert validate_set_power_command(config=_config(), command=cmd, device_id="dg-1").result is (
        CommandResult.IGNORED
    )


def test_non_decimal_value_ignored() -> None:
    assert (
        validate_set_power_command(config=_config(), command=_cmd("nope"), device_id="dg-1").result
        is CommandResult.IGNORED
    )


def test_none_payload_ignored() -> None:
    cmd = Command(
        command_id="c",
        simulation_time=0,
        target_device_id="dg-1",
        type=COMMAND_TYPE_SET_POWER_KW,
        payload=cast("Mapping[str, object]", None),
        validation_status="validated",
        result=CommandResult.IGNORED,
    )
    assert (
        validate_set_power_command(config=_config(), command=cmd, device_id="dg-1").result
        is CommandResult.IGNORED
    )


def test_apply_limited_records_alarm() -> None:
    device = _device()
    assert device.apply_command(_cmd(Decimal("150"))) is CommandResult.LIMITED
    assert len(device.alarms) == 1
    assert isinstance(device.alarms[0], DieselGeneratorAlarm)


def test_drain_alarms_returns_and_clears() -> None:
    device = _device()
    device.apply_command(_cmd(Decimal("150")))
    assert len(device.drain_alarms()) == 1
    assert device.alarms == ()


# ---------------------------------------------------------------------------
# Anfahr-/Abstell-Hysterese (ADR 0058 §2.4)
# ---------------------------------------------------------------------------


def test_starts_when_request_reaches_min_start() -> None:
    device = _device()  # min_start 20, hoher Ramp
    device.apply_command(_cmd(Decimal("25")))
    device.tick(_context(tick=0))
    m = _metrics(device)
    assert m["running"].value == Decimal("1.000000")
    assert m["power_kw"].value == Decimal("25.000000")


def test_does_not_start_below_min_start() -> None:
    device = _device()
    device.apply_command(_cmd(Decimal("15")))  # < min_start 20
    device.tick(_context(tick=0))
    m = _metrics(device)
    assert m["running"].value == Decimal("0.000000")
    assert m["power_kw"].value == Decimal("0.000000")


def test_stops_below_min_stop() -> None:
    device = _device()
    device.apply_command(_cmd(Decimal("25")))
    device.tick(_context(tick=0))  # running at 25
    device.apply_command(_cmd(Decimal("5")))  # < min_stop 10
    device.tick(_context(tick=1))
    m = _metrics(device)
    assert m["running"].value == Decimal("0.000000")
    assert m["power_kw"].value == Decimal("0.000000")


def test_hysteresis_band_keeps_running() -> None:
    """ADR 0058 §2.4: zwischen min_stop (10) und min_start (20) laeuft
    ein bereits laufender Genset weiter (kein Takten)."""
    device = _device()
    device.apply_command(_cmd(Decimal("25")))
    device.tick(_context(tick=0))  # running at 25
    device.apply_command(_cmd(Decimal("15")))  # 10 <= 15 < 20 → bleibt an
    device.tick(_context(tick=1))
    m = _metrics(device)
    assert m["running"].value == Decimal("1.000000")
    assert m["power_kw"].value == Decimal("15.000000")


def test_cannot_start_with_empty_tank() -> None:
    device = _device(initial_fuel_l=Decimal("0"))
    device.apply_command(_cmd(Decimal("50")))  # >= min_start, aber kein Sprit
    device.tick(_context(tick=0))
    assert _metrics(device)["running"].value == Decimal("0.000000")


# ---------------------------------------------------------------------------
# Ramp + Kraftstoff (ADR 0058 §2.5)
# ---------------------------------------------------------------------------


def test_ramp_limits_power_rise() -> None:
    device = _device(ramp_kw_per_s=Decimal("10"))  # max_delta = 10 kW/Tick (dt 1s)
    device.apply_command(_cmd(Decimal("100")))
    device.tick(_context(tick=0, tick_ms=1000))
    assert _metrics(device)["power_kw"].value == Decimal("10.000000")  # 0 → 10 (geramped)


def test_ramp_limits_power_descent() -> None:
    """ADR 0058 §2.5: Ramp begrenzt auch das Absenken (ramp-down-Zweig)."""
    device = _device(ramp_kw_per_s=Decimal("10"))
    device.apply_command(_cmd(Decimal("30")))
    for tick in range(3):  # 0→10→20→30
        device.tick(_context(tick=tick, tick_ms=1000))
    assert _metrics(device)["power_kw"].value == Decimal("30.000000")
    device.apply_command(_cmd(Decimal("10")))  # == min_stop → bleibt an, rampt runter
    device.tick(_context(tick=3, tick_ms=1000))
    assert _metrics(device)["power_kw"].value == Decimal("20.000000")  # 30 - 10 (ramp-down)


def test_generated_kwh_exact_value_at_default_tick() -> None:
    """Energie-Konsistenz: generated_kwh = power * (tick_ms / 3_600_000).
    50 kW * (1000/3_600_000) h = 50/3600 = 0.013889 (gepinnt, nicht nur
    monoton)."""
    device = _device()
    device.apply_command(_cmd(Decimal("50")))
    device.tick(_context(tick=0, tick_ms=1000))
    expected = (Decimal("50") * Decimal(1000) / Decimal(3_600_000)).quantize(Decimal("0.000001"))
    assert expected == Decimal("0.013889")
    assert _metrics(device)["generated_kwh"].value == expected


def test_fuel_run_dry_limits_power_then_stops_next_tick() -> None:
    # initial_fuel 0.01 l, fuel_per_kwh 1, command 100, dt 1s (1/3600 h):
    # needed = 100 * (1/3600) * 1 ≈ 0.02778 > 0.01 → limited_power =
    # 0.01 / (1/3600) = 36 kW. Der Leerfahr-Tick ERZEUGT noch (running
    # bleibt an, ADR 0058 §2.5); der Stopp folgt im naechsten Tick, damit
    # `running==False ⇒ power_kw==0` gilt.
    device = _device(initial_fuel_l=Decimal("0.01"), fuel_per_kwh_l=Decimal("1"))
    device.apply_command(_cmd(Decimal("100")))
    device.tick(_context(tick=0, tick_ms=1000))  # Leerfahr-Tick: erzeugt 36 kW
    m0 = _metrics(device)
    assert m0["power_kw"].value == Decimal("36.000000")
    assert m0["fuel_l"].value == Decimal("0.000000")
    assert m0["running"].value == Decimal("1.000000")
    # Energie-Konsistenz: 36 kW * (1000/3_600_000) h == 0.01 kWh (der
    # gesamte Kraftstoff, nicht die ungedeckelte 100-kW-Anforderung).
    assert m0["generated_kwh"].value == Decimal("0.010000")

    device.tick(_context(tick=1, tick_ms=1000))  # leerer Tank → Stopp bei 0
    m1 = _metrics(device)
    assert m1["power_kw"].value == Decimal("0.000000")
    assert m1["running"].value == Decimal("0.000000")
    assert m1["generated_kwh"].value == Decimal("0.010000")  # eingefroren


def test_cannot_restart_after_running_dry() -> None:
    device = _device(initial_fuel_l=Decimal("0.01"), fuel_per_kwh_l=Decimal("1"))
    device.apply_command(_cmd(Decimal("100")))
    device.tick(_context(tick=0, tick_ms=1000))  # Leerfahr-Tick
    device.tick(_context(tick=1, tick_ms=1000))  # leer → Stopp
    device.tick(_context(tick=2, tick_ms=1000))  # command 100, aber kein Sprit
    assert _metrics(device)["power_kw"].value == Decimal("0.000000")
    assert _metrics(device)["running"].value == Decimal("0.000000")


def test_fuel_decrements_while_running() -> None:
    device = _device()  # fuel 1000, fuel_per_kwh 0.3
    device.apply_command(_cmd(Decimal("100")))
    device.tick(_context(tick=0, tick_ms=3_600_000))  # 1 h at 100 kW
    # consumed = 100 kWh * 0.3 l/kWh = 30 l → 1000 - 30 = 970.
    assert _metrics(device)["fuel_l"].value == Decimal("970.000000")


def test_generated_kwh_monotone() -> None:
    device = _device()
    device.apply_command(_cmd(Decimal("50")))
    last = Decimal("0")
    for tick in range(10):
        device.tick(_context(tick=tick, tick_ms=1000))
        current = cast(Decimal, device.snapshot()["generated_kwh"])
        assert current >= last
        last = current


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------


def test_telemetry_emits_five_metrics_sorted() -> None:
    device = _device()
    metrics = [p.metric for p in device.tick(_context(tick=0)).telemetry]
    assert metrics == ["fuel_l", "generated_kwh", "genset_fault", "power_kw", "running"]
    assert metrics == sorted(metrics)


def test_telemetry_quality_and_quantization() -> None:
    device = _device()
    device.apply_command(_cmd(Decimal("50")))
    for point in device.tick(_context(tick=0)).telemetry:
        assert point.quality is Quality.VALID
        assert point.value.as_tuple().exponent == -6


def test_telemetry_pre_init_returns_empty() -> None:
    assert DieselGeneratorDevice().telemetry() == ()


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip (ADR 0058 §2.8)
# ---------------------------------------------------------------------------


def test_snapshot_first_field_is_version() -> None:
    state = _device().snapshot()
    assert next(iter(state)) == "version"
    assert state["version"] == SNAPSHOT_VERSION


def test_snapshot_pre_init_returns_minimal() -> None:
    assert DieselGeneratorDevice().snapshot() == {"version": SNAPSHOT_VERSION}


def test_snapshot_carries_required_fields() -> None:
    state = _device().snapshot()
    for key in (
        "device_id",
        "run_id",
        "sequence",
        "config",
        "fuel_l",
        "current_power_kw",
        "pending_power_kw",
        "running",
        "generated_kwh",
    ):
        assert key in state


def test_from_snapshot_byte_stable_roundtrip_running() -> None:
    device = _device()
    device.set_run_id("run-x")
    device.apply_command(_cmd(Decimal("40")))
    device.tick(_context(tick=0))  # running=True
    assert device.snapshot()["running"] is True
    restored = DieselGeneratorDevice.from_snapshot(device.snapshot())
    assert restored == device
    assert restored.snapshot()["run_id"] == "run-x"


def test_from_snapshot_preserves_fuel_and_running() -> None:
    device = _device()
    device.apply_command(_cmd(Decimal("50")))
    for tick in range(5):
        device.tick(_context(tick=tick, tick_ms=1000))
    state = device.snapshot()
    restored = DieselGeneratorDevice.from_snapshot(state)
    assert restored.snapshot()["fuel_l"] == state["fuel_l"]
    assert restored.snapshot()["running"] == state["running"]


def test_from_snapshot_device_is_immediately_usable() -> None:
    restored = DieselGeneratorDevice.from_snapshot(_device().snapshot())
    assert restored.device_id == "dg-1"
    assert restored.apply_command(_cmd(Decimal("30"))) is CommandResult.ACCEPTED
    assert restored.tick(_context(tick=1)).telemetry


def test_eq_with_non_diesel_is_not_implemented() -> None:
    assert DieselGeneratorDevice().__eq__(object()) is NotImplemented


def test_from_dict_missing_top_level_key() -> None:
    state = dict(_device().snapshot())
    del state["fuel_l"]
    with pytest.raises(MissingKeysError) as exc:
        DieselGeneratorSnapshot.from_dict(state)
    assert exc.value.subsystem == "diesel_generator"


def test_from_dict_unsupported_version_raises() -> None:
    state = dict(_device().snapshot())
    state["version"] = 99
    with pytest.raises(VersionError):
        DieselGeneratorSnapshot.from_dict(state)


def test_from_dict_running_wrong_type_rejected() -> None:
    """`running` ist Top-Level-Bool (assert_bool) — String wirft."""
    state = dict(_device().snapshot())
    state["running"] = "true"
    with pytest.raises(WrongTypeError):
        DieselGeneratorSnapshot.from_dict(state)


def test_from_dict_invalid_config_reraises_as_wrong_type() -> None:
    state = dict(_device().snapshot())
    bad_config = dict(cast(Mapping[str, object], state["config"]))
    bad_config["max_power_kw"] = Decimal("-1")
    state["config"] = bad_config
    with pytest.raises(WrongTypeError) as exc:
        DieselGeneratorSnapshot.from_dict(state)
    assert exc.value.subsystem == "diesel_generator"


def test_set_run_id_propagates_to_telemetry() -> None:
    device = _device()
    device.set_run_id("run-dg-1")
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == "run-dg-1"


# ---------------------------------------------------------------------------
# Determinismus-Property (ADR 0058 §2.8, ≥ 100 Ticks)
# ---------------------------------------------------------------------------

_TICKS = 100


def _run(command_powers: tuple[Decimal, ...]) -> tuple[TelemetryPoint, ...]:
    device = _device()
    for index, power in enumerate(command_powers):
        device.apply_command(_cmd(power, command_id=f"cmd-{index}"))
    out: list[TelemetryPoint] = []
    for tick in range(_TICKS):
        out.extend(device.tick(_context(tick=tick)).telemetry)
    return tuple(out)


@given(
    power_values=st.lists(
        st.decimals(min_value=0, max_value=100, places=0, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=5,
    )
)
@settings(deadline=None, max_examples=15)
def test_command_sequence_determinism(power_values: list[Decimal]) -> None:
    normalized = tuple(Decimal(0) if v == 0 else v for v in power_values)
    assert _run(normalized) == _run(normalized)


def test_full_100_tick_trace_has_500_points() -> None:
    """ADR 0058 §2.8: 5 Metriken/Tick → 500."""
    assert len(_run((Decimal("50"),))) == _TICKS * 5
