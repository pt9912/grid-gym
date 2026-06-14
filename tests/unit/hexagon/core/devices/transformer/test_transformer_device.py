"""Tests fuer `TransformerDevice` (M8 Welle 2b, ADR 0056, GG-DEV-016).

Konsolidiert Config-/Commands-/Snapshot-/Model-/Determinismus-Tests
(Spiegel zu GridConnection/EV-Charger).

Pinnt:
- `TransformerConfig`-Validierung (positive rated/voltage/ratio,
  nicht-negative Verluste; ADR 0056 §2.3).
- Command-Surface (`set_power_kw` ACCEPTED/LIMITED/IGNORED; kein
  REJECTED fuer Vorzeichen; Saettigungs-Cap ±rated; ADR 0056 §2.5).
- Verlust-/Saettigungs-Math + Sekundaerleistung + Wirkungsgrad +
  Sekundaerspannung (ADR 0056 §2.4) inkl. Energie-Konsistenz.
- Snapshot-Roundtrip byte-stabil inkl. kumulativer `throughput_kwh`.
- Determinismus-Property ueber ≥ 100 Ticks (hypothesis).
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
from grid_gym.hexagon.core.devices.transformer import TransformerDevice
from grid_gym.hexagon.core.devices.transformer.commands import (
    COMMAND_TYPE_SET_POWER_KW,
    TransformerAlarm,
    validate_set_power_command,
)
from grid_gym.hexagon.core.devices.transformer.config import (
    TransformerConfig,
    TransformerConfigInvalidValueError,
)
from grid_gym.hexagon.core.devices.transformer.snapshot import (
    SNAPSHOT_VERSION,
    TransformerSnapshot,
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
    "rated_power_kw": Decimal("1000"),
    "primary_voltage_v": Decimal("20000"),
    "turns_ratio": Decimal("50"),
    "no_load_loss_kw": Decimal("5"),
    "load_loss_kw": Decimal("20"),
}
_ONE_HOUR_MS = 3_600_000


def _scenario_device(**overrides: Decimal) -> ScenarioDevice:
    params: dict[str, object] = {**_DEFAULT, **overrides}
    return ScenarioDevice(id="tr-1", type="transformer", params=params)


def _config(**overrides: Decimal) -> TransformerConfig:
    return TransformerConfig(**{**_DEFAULT, **overrides})


def _command(
    cmd_type: str = COMMAND_TYPE_SET_POWER_KW,
    value: object = Decimal("500"),
    command_id: str = "cmd-1",
) -> Command:
    return Command(
        command_id=command_id,
        simulation_time=0,
        target_device_id="tr-1",
        type=cmd_type,
        payload={"value": value},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _context(tick: int = 0, tick_ms: int = 1000) -> DeviceTickContext:
    return DeviceTickContext(tick=tick, simulation_time=tick * tick_ms, tick_ms=tick_ms)


def _initialize(device: TransformerDevice, **overrides: Decimal) -> TransformerDevice:
    device.initialize(_scenario_device(**overrides), FixedSeedRandom(seed=0))
    return device


def _metrics(device: TransformerDevice) -> dict[str, TelemetryPoint]:
    return {p.metric: p for p in device.telemetry()}


# ---------------------------------------------------------------------------
# TransformerConfig
# ---------------------------------------------------------------------------


def test_valid_config_constructs() -> None:
    config = _config()
    assert config.secondary_voltage_v == Decimal("400")  # 20000 / 50


def test_config_is_frozen() -> None:
    with pytest.raises(FrozenInstanceError):
        _config().rated_power_kw = Decimal("1")  # type: ignore[misc]


@pytest.mark.parametrize("field", ["rated_power_kw", "primary_voltage_v", "turns_ratio"])
def test_non_positive_required_rejected(field: str) -> None:
    with pytest.raises(TransformerConfigInvalidValueError) as exc:
        _config(**{field: Decimal("0")})
    assert field in str(exc.value)


@pytest.mark.parametrize("field", ["no_load_loss_kw", "load_loss_kw"])
def test_negative_loss_rejected(field: str) -> None:
    with pytest.raises(TransformerConfigInvalidValueError) as exc:
        _config(**{field: Decimal("-1")})
    assert field in str(exc.value)


def test_zero_losses_allowed() -> None:
    config = _config(no_load_loss_kw=Decimal("0"), load_loss_kw=Decimal("0"))
    assert config.no_load_loss_kw == Decimal("0")


# ---------------------------------------------------------------------------
# Protocol-Adherence + Lifecycle
# ---------------------------------------------------------------------------


def test_device_satisfies_device_model_protocol() -> None:
    assert isinstance(TransformerDevice(), DeviceModel)


def test_device_id_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        _ = TransformerDevice().device_id


def test_tick_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        TransformerDevice().tick(_context())


def test_apply_command_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        TransformerDevice().apply_command(_command())


def test_double_initialize_raises() -> None:
    device = _initialize(TransformerDevice())
    with pytest.raises(DeviceAlreadyInitializedError):
        device.initialize(_scenario_device(), FixedSeedRandom(seed=1))


def test_device_id_after_init() -> None:
    assert _initialize(TransformerDevice()).device_id == "tr-1"


def test_missing_param_raises_missing_keys() -> None:
    sd = ScenarioDevice(id="tr-1", type="transformer", params={})
    with pytest.raises(MissingKeysError) as exc:
        TransformerDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc.value.subsystem == "transformer"


def test_non_decimal_param_raises_wrong_type() -> None:
    sd = ScenarioDevice(
        id="tr-1",
        type="transformer",
        params={**_DEFAULT, "rated_power_kw": 1000},  # int statt Decimal
    )
    with pytest.raises(WrongTypeError) as exc:
        TransformerDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc.value.subsystem == "transformer"


# ---------------------------------------------------------------------------
# Command-Surface (ADR 0056 §2.5) — kein REJECTED fuer Vorzeichen
# ---------------------------------------------------------------------------


def test_within_cap_accepted() -> None:
    outcome = validate_set_power_command(
        config=_config(), command=_command(value=Decimal("800")), device_id="tr-1"
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw == Decimal("800")
    assert outcome.alarm is None


def test_negative_within_cap_accepted_no_reject() -> None:
    outcome = validate_set_power_command(
        config=_config(), command=_command(value=Decimal("-800")), device_id="tr-1"
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw == Decimal("-800")


def test_above_rated_clamped_forward() -> None:
    outcome = validate_set_power_command(
        config=_config(), command=_command(value=Decimal("1500")), device_id="tr-1"
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("1000")
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("1000")
    assert outcome.alarm.limit_unit == "kW"


def test_below_minus_rated_clamped_reverse() -> None:
    outcome = validate_set_power_command(
        config=_config(), command=_command(value=Decimal("-1500")), device_id="tr-1"
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("-1000")
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("-1000")


def test_saturation_sign_disambiguates_direction() -> None:
    fwd = validate_set_power_command(
        config=_config(), command=_command(value=Decimal("9999")), device_id="tr-1"
    ).alarm
    rev = validate_set_power_command(
        config=_config(), command=_command(value=Decimal("-9999")), device_id="tr-1"
    ).alarm
    assert fwd is not None and rev is not None
    assert fwd.limit > Decimal("0") and rev.limit < Decimal("0")


def test_unknown_command_type_ignored() -> None:
    outcome = validate_set_power_command(
        config=_config(), command=_command(cmd_type="set_mode"), device_id="tr-1"
    )
    assert outcome.result is CommandResult.IGNORED


def test_non_decimal_value_ignored() -> None:
    outcome = validate_set_power_command(
        config=_config(), command=_command(value="nope"), device_id="tr-1"
    )
    assert outcome.result is CommandResult.IGNORED


def test_none_payload_ignored() -> None:
    cmd = Command(
        command_id="cmd-x",
        simulation_time=0,
        target_device_id="tr-1",
        type=COMMAND_TYPE_SET_POWER_KW,
        payload=cast("Mapping[str, object]", None),
        validation_status="validated",
        result=CommandResult.IGNORED,
    )
    assert (
        validate_set_power_command(config=_config(), command=cmd, device_id="tr-1").result
        is CommandResult.IGNORED
    )


def test_apply_limited_records_alarm() -> None:
    device = _initialize(TransformerDevice())
    assert device.apply_command(_command(value=Decimal("9999"))) is CommandResult.LIMITED
    assert len(device.alarms) == 1
    assert isinstance(device.alarms[0], TransformerAlarm)


def test_drain_alarms_returns_and_clears() -> None:
    device = _initialize(TransformerDevice())
    device.apply_command(_command(value=Decimal("9999")))
    assert len(device.drain_alarms()) == 1
    assert device.alarms == ()


# ---------------------------------------------------------------------------
# Verlust-/Saettigungs-Math (ADR 0056 §2.4)
# ---------------------------------------------------------------------------


def test_loss_and_secondary_forward() -> None:
    # primary 500, rated 1000 → load_factor 0.5; loss = 5 + 20*0.25 = 10;
    # secondary = 490; efficiency = 0.98.
    device = _initialize(TransformerDevice())
    device.apply_command(_command(value=Decimal("500")))
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    m = _metrics(device)
    assert m["primary_power_kw"].value == Decimal("500.000000")
    assert m["loss_kw"].value == Decimal("10.000000")
    assert m["secondary_power_kw"].value == Decimal("490.000000")
    assert m["efficiency"].value == Decimal("0.980000")
    assert m["secondary_voltage_v"].value == Decimal("400.000000")
    # Energie-Konsistenz: throughput == |secondary| * dt == 490 kWh.
    assert m["throughput_kwh"].value == Decimal("490.000000")


def test_throughput_uses_dt_conversion_at_default_tick_ms() -> None:
    """ADR 0056 §2.7: `throughput += |secondary| * (tick_ms / 3_600_000)`.
    Pinnt die dt-Konversion am Default `tick_ms=1000` (nicht nur am
    degenerierten 1-h-Tick, wo dt == 1 die Konversion verschleiert)."""
    device = _initialize(TransformerDevice())
    device.apply_command(_command(value=Decimal("500")))  # secondary 490
    device.tick(_context(tick=0, tick_ms=1000))
    expected = (Decimal("490") * Decimal(1000) / Decimal(3_600_000)).quantize(Decimal("0.000001"))
    assert expected == Decimal("0.136111")
    assert _metrics(device)["throughput_kwh"].value == expected


def test_secondary_keeps_sign_on_reverse_flow() -> None:
    device = _initialize(TransformerDevice())
    device.apply_command(_command(value=Decimal("-500")))
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    m = _metrics(device)
    assert m["secondary_power_kw"].value == Decimal("-490.000000")
    # Durchsatz akkumuliert den Betrag.
    assert m["throughput_kwh"].value == Decimal("490.000000")


def test_no_load_loss_present_at_zero_throughput() -> None:
    device = _initialize(TransformerDevice())
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    m = _metrics(device)
    assert m["primary_power_kw"].value == Decimal("0.000000")
    assert m["loss_kw"].value == Decimal("5.000000")  # Eisenverlust konstant
    assert m["secondary_power_kw"].value == Decimal("0.000000")
    assert m["efficiency"].value == Decimal("0.000000")


def test_secondary_floored_when_loss_exceeds_input() -> None:
    # primary 3 → loss = 5 + 20*(3/1000)^2 ≈ 5.00018 > 3 → secondary 0.
    device = _initialize(TransformerDevice())
    device.apply_command(_command(value=Decimal("3")))
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    m = _metrics(device)
    assert m["secondary_power_kw"].value == Decimal("0.000000")
    # Konsequenzen des Floors: kein Durchsatz, Wirkungsgrad 0 (ein Bug,
    # der |primary| statt |secondary| akkumuliert, faellt hier auf).
    assert m["throughput_kwh"].value == Decimal("0.000000")
    assert m["efficiency"].value == Decimal("0.000000")


def test_saturation_clamps_through_power() -> None:
    device = _initialize(TransformerDevice())
    device.apply_command(_command(value=Decimal("5000")))  # > rated 1000 → LIMITED 1000
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    m = _metrics(device)
    assert m["primary_power_kw"].value == Decimal("1000.000000")
    # load_factor 1 → loss 25; secondary 975.
    assert m["loss_kw"].value == Decimal("25.000000")
    assert m["secondary_power_kw"].value == Decimal("975.000000")


def test_throughput_monotone_over_ticks() -> None:
    device = _initialize(TransformerDevice())
    device.apply_command(_command(value=Decimal("500")))
    last = Decimal("0")
    for tick in range(10):
        device.tick(_context(tick=tick, tick_ms=1000))
        current = cast(Decimal, device.snapshot()["throughput_kwh"])
        assert current >= last
        last = current


# ---------------------------------------------------------------------------
# Telemetry (ADR 0056 §2.7)
# ---------------------------------------------------------------------------


def test_telemetry_emits_seven_metrics_sorted() -> None:
    device = _initialize(TransformerDevice())
    outcome = device.tick(_context(tick=0))
    metrics = [p.metric for p in outcome.telemetry]
    assert metrics == [
        "efficiency",
        "loss_kw",
        "primary_power_kw",
        "secondary_power_kw",
        "secondary_voltage_v",
        "throughput_kwh",
        "winding_fault",
    ]
    assert metrics == sorted(metrics)


def test_telemetry_quality_and_quantization() -> None:
    device = _initialize(TransformerDevice())
    device.apply_command(_command(value=Decimal("500")))
    for point in device.tick(_context(tick=0)).telemetry:
        assert point.quality is Quality.VALID
        assert point.value.as_tuple().exponent == -6


def test_telemetry_equals_last_tick_outcome() -> None:
    device = _initialize(TransformerDevice())
    outcome = device.tick(_context(tick=0))
    assert device.telemetry() == outcome.telemetry


def test_telemetry_pre_init_returns_empty() -> None:
    assert TransformerDevice().telemetry() == ()


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip (ADR 0056 §2.7)
# ---------------------------------------------------------------------------


def test_snapshot_first_field_is_version() -> None:
    state = _initialize(TransformerDevice()).snapshot()
    assert next(iter(state)) == "version"
    assert state["version"] == SNAPSHOT_VERSION


def test_snapshot_pre_init_returns_minimal() -> None:
    assert TransformerDevice().snapshot() == {"version": SNAPSHOT_VERSION}


def test_snapshot_carries_required_fields() -> None:
    state = _initialize(TransformerDevice()).snapshot()
    for key in (
        "device_id",
        "run_id",
        "sequence",
        "config",
        "current_primary_power_kw",
        "pending_power_kw",
        "throughput_kwh",
    ):
        assert key in state


def test_from_snapshot_byte_stable_roundtrip() -> None:
    device = _initialize(TransformerDevice())
    device.apply_command(_command(value=Decimal("400")))
    device.tick(_context(tick=0))
    restored = TransformerDevice.from_snapshot(device.snapshot())
    assert restored == device


def test_from_snapshot_preserves_throughput() -> None:
    device = _initialize(TransformerDevice())
    device.apply_command(_command(value=Decimal("500")))
    for tick in range(5):
        device.tick(_context(tick=tick, tick_ms=1000))
    state = device.snapshot()
    restored = TransformerDevice.from_snapshot(state)
    assert restored.snapshot()["throughput_kwh"] == state["throughput_kwh"]


def test_from_snapshot_device_is_immediately_usable() -> None:
    restored = TransformerDevice.from_snapshot(_initialize(TransformerDevice()).snapshot())
    assert restored.device_id == "tr-1"
    assert restored.apply_command(_command(value=Decimal("200"))) is CommandResult.ACCEPTED
    assert restored.tick(_context(tick=1)).telemetry


def test_attach_random_after_from_snapshot() -> None:
    restored = TransformerDevice.from_snapshot(_initialize(TransformerDevice()).snapshot())
    restored.attach_random(FixedSeedRandom(seed=42))
    assert restored.tick(_context(tick=1)).telemetry


def test_eq_with_non_transformer_is_not_implemented() -> None:
    assert TransformerDevice().__eq__(object()) is NotImplemented


def test_from_dict_missing_top_level_key() -> None:
    state = dict(_initialize(TransformerDevice()).snapshot())
    del state["throughput_kwh"]
    with pytest.raises(MissingKeysError) as exc:
        TransformerSnapshot.from_dict(state)
    assert exc.value.subsystem == "transformer"


def test_from_dict_unsupported_version_raises() -> None:
    state = dict(_initialize(TransformerDevice()).snapshot())
    state["version"] = 99
    with pytest.raises(VersionError):
        TransformerSnapshot.from_dict(state)


def test_from_dict_invalid_config_reraises_as_wrong_type() -> None:
    state = dict(_initialize(TransformerDevice()).snapshot())
    bad_config = dict(cast(Mapping[str, object], state["config"]))
    bad_config["turns_ratio"] = Decimal("0")
    state["config"] = bad_config
    with pytest.raises(WrongTypeError) as exc:
        TransformerSnapshot.from_dict(state)
    assert exc.value.subsystem == "transformer"


# ---------------------------------------------------------------------------
# Lifecycle-Hooks
# ---------------------------------------------------------------------------


def test_set_run_id_propagates_to_telemetry() -> None:
    device = _initialize(TransformerDevice())
    device.set_run_id("run-tr-1")
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == "run-tr-1"


def test_set_run_id_pre_init_is_allowed() -> None:
    device = TransformerDevice()
    device.set_run_id("run-pre-init")
    _initialize(device)
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == "run-pre-init"


def test_multiple_commands_last_wins() -> None:
    device = _initialize(TransformerDevice())
    device.apply_command(_command(value=Decimal("100"), command_id="a"))
    device.apply_command(_command(value=Decimal("-200"), command_id="b"))
    device.apply_command(_command(value=Decimal("300"), command_id="c"))
    assert device.snapshot()["pending_power_kw"] == Decimal("300")


# ---------------------------------------------------------------------------
# Determinismus-Property (ADR 0056 §2.7, ≥ 100 Ticks)
# ---------------------------------------------------------------------------

_TICKS = 100


def _run(seed: int, command_powers: tuple[Decimal, ...]) -> tuple[TelemetryPoint, ...]:
    device = TransformerDevice()
    device.initialize(_scenario_device(), FixedSeedRandom(seed=seed))
    for index, power in enumerate(command_powers):
        device.apply_command(_command(value=power, command_id=f"cmd-{index}"))
    out: list[TelemetryPoint] = []
    for tick in range(_TICKS):
        out.extend(device.tick(_context(tick=tick)).telemetry)
    return tuple(out)


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
@settings(deadline=None, max_examples=15)
def test_same_seed_produces_byte_identical_trace(seed: int) -> None:
    commands = (Decimal("500"),)
    assert _run(seed, commands) == _run(seed, commands)


@given(
    power_values=st.lists(
        st.decimals(
            min_value=-1000,
            max_value=1000,
            places=0,
            allow_nan=False,
            allow_infinity=False,
        ),
        min_size=1,
        max_size=5,
    )
)
@settings(deadline=None, max_examples=15)
def test_command_sequence_determinism(power_values: list[Decimal]) -> None:
    normalized = tuple(Decimal(0) if v == 0 else v for v in power_values)
    assert _run(seed=0, command_powers=normalized) == _run(seed=0, command_powers=normalized)


def test_full_100_tick_trace_has_700_points() -> None:
    """ADR 0056 §2.7: 7 Metriken/Tick → 700."""
    assert len(_run(seed=42, command_powers=(Decimal("500"),))) == _TICKS * 7
