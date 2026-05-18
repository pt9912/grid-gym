"""Tests fuer `LoadDevice` (M2 Welle 3b, ADR 0016, GG-DEV-013).

Spiegelt `test_pv_device.py`-Struktur; einzige semantische
Unterschiede sind die Sign-Konvention-Begruendung (Load
verbraucht statt erzeugt) und der `source="load"`-Tag.
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
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.devices.load.commands import (
    COMMAND_TYPE_SET_POWER_KW,
    LoadAlarm,
    validate_set_power_command,
)
from grid_gym.hexagon.core.devices.load.config import (
    LoadConfig,
    LoadConfigInvalidValueError,
)
from grid_gym.hexagon.core.devices.load.snapshot import (
    SNAPSHOT_VERSION,
    LoadSnapshot,
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


def _scenario_device(rated_power_kw: Decimal = Decimal("800")) -> ScenarioDevice:
    return ScenarioDevice(
        id="load-1",
        type="load",
        params={"rated_power_kw": rated_power_kw},
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
        target_device_id="load-1",
        type=cmd_type,
        payload=payload,
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _context(tick: int = 0) -> DeviceTickContext:
    return DeviceTickContext(tick=tick, simulation_time=tick * 1000, tick_ms=1000)


def _initialize(device: LoadDevice, rated_power_kw: Decimal = Decimal("800")) -> LoadDevice:
    device.initialize(_scenario_device(rated_power_kw), FixedSeedRandom(seed=0))
    return device


# ---------------------------------------------------------------------------
# LoadConfig
# ---------------------------------------------------------------------------


def test_valid_config_constructs() -> None:
    config = LoadConfig(rated_power_kw=Decimal("800"))
    assert config.rated_power_kw == Decimal("800")


def test_config_is_frozen() -> None:
    config = LoadConfig(rated_power_kw=Decimal("800"))
    with pytest.raises(FrozenInstanceError):
        config.rated_power_kw = Decimal("100")  # type: ignore[misc]


def test_zero_rated_power_rejected() -> None:
    with pytest.raises(LoadConfigInvalidValueError) as exc_info:
        LoadConfig(rated_power_kw=Decimal("0"))
    assert "rated_power_kw" in str(exc_info.value)


def test_negative_rated_power_rejected() -> None:
    with pytest.raises(LoadConfigInvalidValueError):
        LoadConfig(rated_power_kw=Decimal("-100"))


# ---------------------------------------------------------------------------
# Protocol-Adherence + Lifecycle
# ---------------------------------------------------------------------------


def test_load_device_satisfies_device_model_protocol() -> None:
    assert isinstance(LoadDevice(), DeviceModel)


def test_device_id_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        _ = LoadDevice().device_id


def test_tick_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        LoadDevice().tick(_context())


def test_apply_command_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        LoadDevice().apply_command(_command())


def test_double_initialize_raises() -> None:
    device = _initialize(LoadDevice())
    with pytest.raises(DeviceAlreadyInitializedError):
        device.initialize(_scenario_device(), FixedSeedRandom(seed=1))


def test_device_id_after_init() -> None:
    device = _initialize(LoadDevice())
    assert device.device_id == "load-1"


def test_initial_power_is_rated_power() -> None:
    """ADR 0016 §2.6: Default-Output ist Nennleistung."""
    device = _initialize(LoadDevice(), rated_power_kw=Decimal("600"))
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry[0].value == Decimal("600.000000")


# ---------------------------------------------------------------------------
# Param-Parsing
# ---------------------------------------------------------------------------


def test_missing_param_raises_missing_keys_error() -> None:
    sd = ScenarioDevice(id="load-1", type="load", params={})
    with pytest.raises(MissingKeysError) as exc_info:
        LoadDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc_info.value.subsystem == "load"


def test_non_decimal_param_raises_wrong_type_error() -> None:
    sd = ScenarioDevice(id="load-1", type="load", params={"rated_power_kw": 800})
    with pytest.raises(WrongTypeError) as exc_info:
        LoadDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc_info.value.subsystem == "load"


# ---------------------------------------------------------------------------
# Command-Surface (ADR 0016 §2.4)
# ---------------------------------------------------------------------------


def test_unknown_command_type_returns_ignored() -> None:
    config = LoadConfig(rated_power_kw=Decimal("800"))
    outcome = validate_set_power_command(
        config=config, command=_command(cmd_type="set_mode"), device_id="load-1"
    )
    assert outcome.result is CommandResult.IGNORED


def test_missing_value_payload_returns_ignored() -> None:
    config = LoadConfig(rated_power_kw=Decimal("800"))
    cmd = Command(
        command_id="cmd-x",
        simulation_time=0,
        target_device_id="load-1",
        type=COMMAND_TYPE_SET_POWER_KW,
        payload={},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )
    outcome = validate_set_power_command(config=config, command=cmd, device_id="load-1")
    assert outcome.result is CommandResult.IGNORED


def test_negative_value_rejected_with_sign_alarm() -> None:
    """ADR 0016 §2.2: Load verbraucht nicht-negativ."""
    config = LoadConfig(rated_power_kw=Decimal("800"))
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("-100")), device_id="load-1"
    )
    assert outcome.result is CommandResult.REJECTED
    assert isinstance(outcome.alarm, LoadAlarm)
    assert outcome.alarm.limit == Decimal("0")
    assert outcome.alarm.limit_unit == "kW"


def test_value_above_rated_clamped_and_alarmed() -> None:
    config = LoadConfig(rated_power_kw=Decimal("800"))
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("1500")), device_id="load-1"
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("800")
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("800")


def test_within_limits_accepted() -> None:
    config = LoadConfig(rated_power_kw=Decimal("800"))
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("500")), device_id="load-1"
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw == Decimal("500")


def test_zero_power_accepted() -> None:
    """Sign-Vertrag erlaubt 0 (Load offline)."""
    config = LoadConfig(rated_power_kw=Decimal("800"))
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("0")), device_id="load-1"
    )
    assert outcome.result is CommandResult.ACCEPTED


# ---------------------------------------------------------------------------
# Tick + Telemetry (ADR 0016 §2.5)
# ---------------------------------------------------------------------------


def test_telemetry_emits_single_power_metric() -> None:
    device = _initialize(LoadDevice())
    outcome = device.tick(_context(tick=0))
    assert [p.metric for p in outcome.telemetry] == ["power_kw"]


def test_telemetry_quality_is_valid() -> None:
    device = _initialize(LoadDevice())
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry[0].quality is Quality.VALID


def test_telemetry_source_is_load() -> None:
    """Load-spezifisches `source="load"`-Tag im Unterschied zu
    PV (`source="pv"`) und Battery (`source="battery"`)."""
    device = _initialize(LoadDevice())
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry[0].source == "load"


def test_apply_command_then_tick_uses_pending() -> None:
    device = _initialize(LoadDevice())
    device.apply_command(_command(value=Decimal("300")))
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry[0].value == Decimal("300.000000")


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip
# ---------------------------------------------------------------------------


def test_snapshot_first_field_is_version() -> None:
    device = _initialize(LoadDevice())
    state = device.snapshot()
    assert next(iter(state)) == "version"


def test_snapshot_pre_init_returns_minimal() -> None:
    state = LoadDevice().snapshot()
    assert state == {"version": SNAPSHOT_VERSION}


def test_from_snapshot_byte_stable_roundtrip() -> None:
    device = _initialize(LoadDevice())
    device.apply_command(_command(value=Decimal("400")))
    device.tick(_context(tick=0))
    state = device.snapshot()
    restored = LoadDevice.from_snapshot(state)
    assert restored == device


def test_from_snapshot_device_is_immediately_usable() -> None:
    original = _initialize(LoadDevice())
    state = original.snapshot()
    restored = LoadDevice.from_snapshot(state)
    assert restored.device_id == "load-1"
    result = restored.apply_command(_command(value=Decimal("100")))
    assert result is CommandResult.ACCEPTED


def test_from_dict_missing_top_level_key() -> None:
    device = _initialize(LoadDevice())
    state = dict(device.snapshot())
    del state["pending_power_kw"]
    with pytest.raises(MissingKeysError) as exc_info:
        LoadSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "load"


def test_from_dict_unsupported_version_raises_version_error() -> None:
    device = _initialize(LoadDevice())
    state = dict(device.snapshot())
    state["version"] = 99
    with pytest.raises(VersionError):
        LoadSnapshot.from_dict(state)


def test_from_dict_invalid_config_reraises_as_wrong_type() -> None:
    device = _initialize(LoadDevice())
    state = dict(device.snapshot())
    bad_config = dict(cast(Mapping[str, object], state["config"]))
    bad_config["rated_power_kw"] = Decimal("-1")
    state["config"] = bad_config
    with pytest.raises(WrongTypeError) as exc_info:
        LoadSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "load"


# ---------------------------------------------------------------------------
# Alarms + Drain
# ---------------------------------------------------------------------------


def test_alarm_emitted_on_clamped_command() -> None:
    device = _initialize(LoadDevice())
    device.apply_command(_command(value=Decimal("9999")))
    assert len(device.alarms) == 1
    assert device.alarms[0].result is CommandResult.LIMITED


def test_drain_alarms_returns_and_clears() -> None:
    device = _initialize(LoadDevice())
    device.apply_command(_command(value=Decimal("9999")))
    drained = device.drain_alarms()
    assert len(drained) == 1
    assert device.alarms == ()


def test_set_run_id_propagates_to_telemetry() -> None:
    device = _initialize(LoadDevice())
    device.set_run_id("run-load-1")
    device.tick(_context(tick=0))
    assert device.telemetry()[0].run_id == "run-load-1"


# ---------------------------------------------------------------------------
# Multi-Command + last-wins
# ---------------------------------------------------------------------------


def test_multiple_commands_in_same_tick_last_wins() -> None:
    device = _initialize(LoadDevice())
    device.apply_command(_command(value=Decimal("100"), command_id="a"))
    device.apply_command(_command(value=Decimal("300"), command_id="b"))
    device.apply_command(_command(value=Decimal("200"), command_id="c"))
    state = device.snapshot()
    assert state["pending_power_kw"] == Decimal("200")


# ---------------------------------------------------------------------------
# Determinismus-Property (ADR 0016 §2.7)
# ---------------------------------------------------------------------------


_TICKS = 100


def _run_load(seed: int, command_powers: tuple[Decimal, ...]) -> tuple[TelemetryPoint, ...]:
    device = LoadDevice()
    device.initialize(_scenario_device(), FixedSeedRandom(seed=seed))
    for index, power in enumerate(command_powers):
        device.apply_command(_command(value=power, command_id=f"cmd-{index}"))
    out: list[TelemetryPoint] = []
    for tick in range(_TICKS):
        outcome = device.tick(_context(tick=tick))
        out.extend(outcome.telemetry)
    return tuple(out)


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
@settings(deadline=None, max_examples=20)
def test_same_seed_produces_byte_identical_trace(seed: int) -> None:
    commands = (Decimal("400"),)
    trace_a = _run_load(seed, commands)
    trace_b = _run_load(seed, commands)
    assert trace_a == trace_b


@given(
    power_values=st.lists(
        st.decimals(
            min_value=0,
            max_value=800,
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
    trace_a = _run_load(seed=0, command_powers=normalized)
    trace_b = _run_load(seed=0, command_powers=normalized)
    assert trace_a == trace_b


def test_full_100_tick_trace_has_100_telemetry_points() -> None:
    trace = _run_load(seed=42, command_powers=(Decimal("400"),))
    assert len(trace) == 100
