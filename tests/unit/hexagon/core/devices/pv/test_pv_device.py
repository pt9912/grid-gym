"""Tests fuer `PvDevice` (M2 Welle 3, ADR 0016, GG-DEV-011).

Konsolidiert Config-/Commands-/Snapshot-/Model-/Determinismus-
Tests in einem Modul — PV ist strukturell deutlich einfacher als
Battery (kein SOC/Ramp/Safety-Clamp), eine 5-fache Datei-
Aufteilung waere Overkill.

Pinnt:
- PvConfig-Validierung (positive rated_power_kw, ADR 0016 §2.3).
- Command-Surface (set_power_kw ACCEPTED/LIMITED/REJECTED/IGNORED).
- Sign-Vertrag (negative Werte werden REJECTED, ADR 0016 §2.2).
- Snapshot-Roundtrip byte-stabil + Codec-Errors.
- Protocol-Adherence (`isinstance(PvDevice(), DeviceModel)`).
- Lifecycle-Pre-init-Raises.
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
from grid_gym.hexagon.core.devices.pv import PvDevice
from grid_gym.hexagon.core.devices.pv.commands import (
    COMMAND_TYPE_SET_POWER_KW,
    PvAlarm,
    validate_set_power_command,
)
from grid_gym.hexagon.core.devices.pv.config import (
    PvConfig,
    PvConfigInvalidValueError,
    VoltVarConfig,
)
from grid_gym.hexagon.core.devices.pv.snapshot import (
    SNAPSHOT_VERSION,
    PvSnapshot,
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


def _scenario_device(rated_power_kw: Decimal = Decimal("1500")) -> ScenarioDevice:
    return ScenarioDevice(
        id="pv-1",
        type="pv",
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
        target_device_id="pv-1",
        type=cmd_type,
        payload=payload,
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _context(tick: int = 0) -> DeviceTickContext:
    return DeviceTickContext(tick=tick, simulation_time=tick * 1000, tick_ms=1000)


def _initialize(device: PvDevice, rated_power_kw: Decimal = Decimal("1500")) -> PvDevice:
    device.initialize(_scenario_device(rated_power_kw), FixedSeedRandom(seed=0))
    return device


# ---------------------------------------------------------------------------
# PvConfig
# ---------------------------------------------------------------------------


def test_valid_config_constructs() -> None:
    config = PvConfig(rated_power_kw=Decimal("1500"))
    assert config.rated_power_kw == Decimal("1500")


def test_config_is_frozen() -> None:
    config = PvConfig(rated_power_kw=Decimal("1500"))
    with pytest.raises(FrozenInstanceError):
        config.rated_power_kw = Decimal("100")  # type: ignore[misc]


def test_zero_rated_power_rejected() -> None:
    with pytest.raises(PvConfigInvalidValueError) as exc_info:
        PvConfig(rated_power_kw=Decimal("0"))
    assert "rated_power_kw" in str(exc_info.value)


def test_negative_rated_power_rejected() -> None:
    with pytest.raises(PvConfigInvalidValueError):
        PvConfig(rated_power_kw=Decimal("-100"))


# ---------------------------------------------------------------------------
# Protocol-Adherence + Lifecycle
# ---------------------------------------------------------------------------


def test_pv_device_satisfies_device_model_protocol() -> None:
    """ADR 0013 §5 Konvention: jede konkrete Geraete-Implementation
    durchlaeuft `isinstance(..., DeviceModel)`."""
    assert isinstance(PvDevice(), DeviceModel)


def test_device_id_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        _ = PvDevice().device_id


def test_tick_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        PvDevice().tick(_context())


def test_apply_command_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        PvDevice().apply_command(_command())


def test_double_initialize_raises() -> None:
    device = _initialize(PvDevice())
    with pytest.raises(DeviceAlreadyInitializedError):
        device.initialize(_scenario_device(), FixedSeedRandom(seed=1))


def test_device_id_after_init() -> None:
    device = _initialize(PvDevice())
    assert device.device_id == "pv-1"


def test_initial_power_is_rated_power(rated: Decimal = Decimal("1200")) -> None:
    """ADR 0016 §2.6: Default-Output ist Nennleistung —
    ohne Command liefert der erste Tick `rated_power_kw`."""
    device = _initialize(PvDevice(), rated_power_kw=rated)
    outcome = device.tick(_context(tick=0))
    power_point = outcome.telemetry[0]
    assert power_point.value == Decimal("1200.000000")


# ---------------------------------------------------------------------------
# Param-Parsing
# ---------------------------------------------------------------------------


def test_missing_param_raises_missing_keys_error() -> None:
    sd = ScenarioDevice(id="pv-1", type="pv", params={})
    with pytest.raises(MissingKeysError) as exc_info:
        PvDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc_info.value.subsystem == "pv"


def test_non_decimal_param_raises_wrong_type_error() -> None:
    sd = ScenarioDevice(id="pv-1", type="pv", params={"rated_power_kw": 1500})  # int statt Decimal
    with pytest.raises(WrongTypeError) as exc_info:
        PvDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc_info.value.subsystem == "pv"


# ---------------------------------------------------------------------------
# Command-Surface (ADR 0016 §2.4)
# ---------------------------------------------------------------------------


def test_unknown_command_type_returns_ignored() -> None:
    config = PvConfig(rated_power_kw=Decimal("1500"))
    outcome = validate_set_power_command(
        config=config, command=_command(cmd_type="set_mode"), device_id="pv-1"
    )
    assert outcome.result is CommandResult.IGNORED


def test_missing_value_payload_returns_ignored() -> None:
    config = PvConfig(rated_power_kw=Decimal("1500"))
    cmd = Command(
        command_id="cmd-x",
        simulation_time=0,
        target_device_id="pv-1",
        type=COMMAND_TYPE_SET_POWER_KW,
        payload={},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )
    outcome = validate_set_power_command(config=config, command=cmd, device_id="pv-1")
    assert outcome.result is CommandResult.IGNORED


def test_negative_value_rejected_with_sign_alarm() -> None:
    """ADR 0016 §2.2/§2.4: PV erzeugt nicht-negativ. Negative
    Power-Anforderung geht direkt auf REJECTED."""
    config = PvConfig(rated_power_kw=Decimal("1500"))
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("-100")), device_id="pv-1"
    )
    assert outcome.result is CommandResult.REJECTED
    assert outcome.pending_power_kw is None
    assert isinstance(outcome.alarm, PvAlarm)
    assert outcome.alarm.limit == Decimal("0")
    assert outcome.alarm.limit_unit == "kW"


def test_value_above_rated_clamped_and_alarmed() -> None:
    config = PvConfig(rated_power_kw=Decimal("1500"))
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("2000")), device_id="pv-1"
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("1500")
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("1500")


def test_within_limits_accepted() -> None:
    config = PvConfig(rated_power_kw=Decimal("1500"))
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("800")), device_id="pv-1"
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw == Decimal("800")
    assert outcome.alarm is None


def test_zero_power_accepted() -> None:
    """Sign-Vertrag erlaubt 0 (PV im Schatten)."""
    config = PvConfig(rated_power_kw=Decimal("1500"))
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("0")), device_id="pv-1"
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw == Decimal("0")


def test_alarm_carries_command_id() -> None:
    config = PvConfig(rated_power_kw=Decimal("1500"))
    outcome = validate_set_power_command(
        config=config,
        command=_command(value=Decimal("-100"), command_id="cmd-42"),
        device_id="pv-1",
    )
    assert outcome.alarm is not None
    assert outcome.alarm.command_id == "cmd-42"


# ---------------------------------------------------------------------------
# Tick + Telemetry
# ---------------------------------------------------------------------------


def test_telemetry_emits_single_power_metric() -> None:
    """ADR 0016 §2.5: ein TelemetryPoint mit Metric `power_kw`."""
    device = _initialize(PvDevice())
    outcome = device.tick(_context(tick=0))
    metrics = [p.metric for p in outcome.telemetry]
    assert metrics == ["power_kw"]


def test_telemetry_value_is_decimal_quantized() -> None:
    device = _initialize(PvDevice())
    outcome = device.tick(_context(tick=0))
    point = outcome.telemetry[0]
    assert "." in str(point.value)
    decimals_part = str(point.value).split(".", 1)[1]
    assert len(decimals_part) <= 6


def test_telemetry_quality_is_valid() -> None:
    device = _initialize(PvDevice())
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry[0].quality is Quality.VALID


def test_telemetry_unit_is_kw() -> None:
    device = _initialize(PvDevice())
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry[0].unit == "kW"


def test_apply_command_then_tick_uses_pending() -> None:
    """ACCEPTED-Command setzt pending_power; naechster Tick uebernimmt."""
    device = _initialize(PvDevice())
    device.apply_command(_command(value=Decimal("500")))
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry[0].value == Decimal("500.000000")


def test_telemetry_equals_last_tick_outcome() -> None:
    """ADR 0013 §2.5: `telemetry()` ==-identisch zum letzten
    `tick()`-Ergebnis."""
    device = _initialize(PvDevice())
    outcome = device.tick(_context(tick=0))
    assert device.telemetry() == outcome.telemetry


def test_telemetry_pre_init_returns_empty() -> None:
    assert PvDevice().telemetry() == ()


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip (ADR 0014 §2.2-Schaerfung gespiegelt)
# ---------------------------------------------------------------------------


def test_snapshot_first_field_is_version() -> None:
    device = _initialize(PvDevice())
    state = device.snapshot()
    assert next(iter(state)) == "version"
    assert state["version"] == SNAPSHOT_VERSION


def test_snapshot_pre_init_returns_minimal() -> None:
    state = PvDevice().snapshot()
    assert state == {"version": SNAPSHOT_VERSION}


def test_snapshot_carries_required_fields() -> None:
    device = _initialize(PvDevice())
    state = device.snapshot()
    assert "device_id" in state
    assert "run_id" in state
    assert "sequence" in state
    assert "config" in state


def test_from_snapshot_byte_stable_roundtrip() -> None:
    device = _initialize(PvDevice())
    device.apply_command(_command(value=Decimal("750")))
    device.tick(_context(tick=0))
    state = device.snapshot()
    restored = PvDevice.from_snapshot(state)
    assert restored == device


def test_from_snapshot_device_is_immediately_usable() -> None:
    """Welle-2-Review-C-1-Spiegel: from_snapshot liefert
    sofort-nutzbares Device."""
    original = _initialize(PvDevice())
    state = original.snapshot()
    restored = PvDevice.from_snapshot(state)
    assert restored.device_id == "pv-1"
    result = restored.apply_command(_command(value=Decimal("100")))
    assert result is CommandResult.ACCEPTED
    outcome = restored.tick(_context(tick=1))
    assert outcome.telemetry


def test_from_dict_missing_top_level_key() -> None:
    device = _initialize(PvDevice())
    state = dict(device.snapshot())
    del state["pending_power_kw"]
    with pytest.raises(MissingKeysError) as exc_info:
        PvSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "pv"


def test_from_dict_unsupported_version_raises_version_error() -> None:
    device = _initialize(PvDevice())
    state = dict(device.snapshot())
    state["version"] = 99
    with pytest.raises(VersionError):
        PvSnapshot.from_dict(state)


def test_from_dict_wrong_version_type_rejected() -> None:
    device = _initialize(PvDevice())
    state = dict(device.snapshot())
    state["version"] = "1"
    with pytest.raises(WrongTypeError):
        PvSnapshot.from_dict(state)


def test_from_dict_invalid_config_reraises_as_wrong_type() -> None:
    """ADR 0014 §2.2 M-5-Spiegel: PvConfigError → WrongTypeError."""
    device = _initialize(PvDevice())
    state = dict(device.snapshot())
    bad_config = dict(cast(Mapping[str, object], state["config"]))
    bad_config["rated_power_kw"] = Decimal("-1")  # PvConfig wirft
    state["config"] = bad_config
    with pytest.raises(WrongTypeError) as exc_info:
        PvSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "pv"


# ---------------------------------------------------------------------------
# Alarms + Drain (ADR 0014 §2.5-Spiegel)
# ---------------------------------------------------------------------------


def test_alarm_emitted_on_clamped_command() -> None:
    device = _initialize(PvDevice())
    device.apply_command(_command(value=Decimal("9999")))
    assert len(device.alarms) == 1
    assert device.alarms[0].result is CommandResult.LIMITED


def test_alarm_emitted_on_negative_command() -> None:
    device = _initialize(PvDevice())
    device.apply_command(_command(value=Decimal("-100")))
    assert len(device.alarms) == 1
    assert device.alarms[0].result is CommandResult.REJECTED


def test_drain_alarms_returns_and_clears() -> None:
    device = _initialize(PvDevice())
    device.apply_command(_command(value=Decimal("9999")))
    drained = device.drain_alarms()
    assert len(drained) == 1
    assert device.alarms == ()


def test_set_run_id_propagates_to_telemetry() -> None:
    device = _initialize(PvDevice())
    device.set_run_id("run-pv-1")
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == "run-pv-1"


def test_run_id_default_is_empty_string_pre_set() -> None:
    """Welle-3-Review M-4: ohne `set_run_id` laeuft das Geraet mit
    `run_id=""` — TickLoop (Welle 6) muss `set_run_id` vor dem
    ersten Tick rufen; Welle-3-Test-Setup ist als Welle-6-Anchor
    explizit dokumentiert."""
    device = _initialize(PvDevice())
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == ""


def test_attach_random_after_from_snapshot() -> None:
    """Welle-3-Review M-6: `from_snapshot` rekonstruiert State,
    `attach_random` reattacht den `RandomPort` fuer Welle-5+
    stochastische Anteile."""
    original = _initialize(PvDevice())
    state = original.snapshot()
    restored = PvDevice.from_snapshot(state)
    new_random = FixedSeedRandom(seed=42)
    restored.attach_random(new_random)
    # Re-Attach ist No-Op fuer den heutigen Tick (Welle 3 konsumiert
    # `_random` nicht); Vertragsspiegel ist die Aufrufbarkeit selbst.
    outcome = restored.tick(_context(tick=1))
    assert outcome.telemetry


# ---------------------------------------------------------------------------
# Multi-Command + last-wins (ADR 0014 §2.3-Spiegel)
# ---------------------------------------------------------------------------


def test_multiple_commands_in_same_tick_last_wins() -> None:
    device = _initialize(PvDevice())
    device.apply_command(_command(value=Decimal("100"), command_id="a"))
    device.apply_command(_command(value=Decimal("300"), command_id="b"))
    device.apply_command(_command(value=Decimal("200"), command_id="c"))
    state = device.snapshot()
    assert state["pending_power_kw"] == Decimal("200")
    device.tick(_context(tick=0))
    assert device.telemetry()[0].value == Decimal("200.000000")


# ---------------------------------------------------------------------------
# Determinismus-Property (ADR 0016 §2.7, ≥ 100 Ticks)
# ---------------------------------------------------------------------------


_TICKS = 100


def _run_pv(seed: int, command_powers: tuple[Decimal, ...]) -> tuple[TelemetryPoint, ...]:
    device = PvDevice()
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
    """ADR 0016 §2.7 + Slice-Plan §3 Welle 3: ≥ 100 Ticks
    byte-stabil."""
    commands = (Decimal("500"),)
    trace_a = _run_pv(seed, commands)
    trace_b = _run_pv(seed, commands)
    assert trace_a == trace_b


@given(
    power_values=st.lists(
        st.decimals(
            min_value=0,
            max_value=1500,
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
    """Welle-2-Review-H-5-Spiegel: zweimal dieselbe Command-Sequenz
    → byte-identische Telemetrie."""
    normalized = tuple(Decimal(0) if v == 0 else v for v in power_values)
    trace_a = _run_pv(seed=0, command_powers=normalized)
    trace_b = _run_pv(seed=0, command_powers=normalized)
    assert trace_a == trace_b


def test_full_100_tick_trace_has_100_telemetry_points() -> None:
    """PV emittiert 1 Metric/Tick → 100 Ticks * 1 = 100 Points."""
    trace = _run_pv(seed=42, command_powers=(Decimal("750"),))
    assert len(trace) == 100


# ---------------------------------------------------------------------------
# M8-Welle-3c-b-1: Volt-Var-Q(U)-Emission (ADR 0063)
# ---------------------------------------------------------------------------


def _volt_var(
    *,
    reference_voltage_v: Decimal = Decimal("400"),
    deadband_v: Decimal = Decimal("5"),
    droop_kvar_per_v: Decimal = Decimal("2"),
    max_kvar: Decimal = Decimal("50"),
) -> VoltVarConfig:
    return VoltVarConfig(
        reference_voltage_v=reference_voltage_v,
        deadband_v=deadband_v,
        droop_kvar_per_v=droop_kvar_per_v,
        max_kvar=max_kvar,
    )


def _volt_var_params() -> dict[str, object]:
    return {
        "reference_voltage_v": Decimal("400"),
        "deadband_v": Decimal("5"),
        "droop_kvar_per_v": Decimal("2"),
        "max_kvar": Decimal("50"),
    }


def _pv_with_volt_var() -> PvDevice:
    pv = PvDevice()
    pv.initialize(
        ScenarioDevice(
            id="pv-1",
            type="pv",
            params={"rated_power_kw": Decimal("100"), "volt_var": _volt_var_params()},
        ),
        FixedSeedRandom(seed=0),
    )
    pv.set_run_id("r")
    return pv


def _ctx(voltage: Decimal | None) -> DeviceTickContext:
    return DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000, grid_voltage_v=voltage)


# --- VoltVarConfig + Q(U)-Auswertung ---------------------------------------


def test_volt_var_default_none() -> None:
    assert PvConfig(rated_power_kw=Decimal("100")).volt_var is None


def test_volt_var_zero_droop_rejected() -> None:
    with pytest.raises(PvConfigInvalidValueError) as exc_info:
        _volt_var(droop_kvar_per_v=Decimal("0"))
    assert "droop_kvar_per_v" in str(exc_info.value)


def test_volt_var_negative_deadband_rejected() -> None:
    with pytest.raises(PvConfigInvalidValueError):
        _volt_var(deadband_v=Decimal("-1"))


def test_volt_var_float_rejected() -> None:
    with pytest.raises(PvConfigInvalidValueError) as exc_info:
        _volt_var(max_kvar=50.0)  # type: ignore[arg-type]
    assert "Decimal" in str(exc_info.value)


def test_q_u_deadband_returns_zero() -> None:
    vv = _volt_var()
    assert vv.reactive_power_kvar(Decimal("402")) == Decimal("0")  # within +/-5
    assert vv.reactive_power_kvar(Decimal("400")) == Decimal("0")


def test_q_u_high_voltage_absorbs() -> None:
    """ADR 0063 §2.2: hohe Spannung -> -Q (induktiv absorbieren)."""
    # U=410, dv=10, excess=5, Q=-2*5=-10
    assert _volt_var().reactive_power_kvar(Decimal("410")) == Decimal("-10")


def test_q_u_low_voltage_injects() -> None:
    """ADR 0063 §2.2: niedrige Spannung -> +Q (kapazitiv einspeisen)."""
    assert _volt_var().reactive_power_kvar(Decimal("390")) == Decimal("10")


def test_q_u_clamps_at_max_kvar() -> None:
    # U=500, dv=100, excess=95, droop*95=190 -> clamp 50
    assert _volt_var().reactive_power_kvar(Decimal("500")) == Decimal("-50")


# --- Telemetrie-Emission (opt-in) ------------------------------------------


def test_no_volt_var_emits_no_q_telemetry() -> None:
    """ADR 0063 §2.3: ohne Kurve KEIN reactive_power_kvar-Punkt (nicht 0)."""
    pv = PvDevice()
    pv.initialize(_scenario_device(rated_power_kw=Decimal("100")), FixedSeedRandom(seed=0))
    pv.set_run_id("r")
    out = pv.tick(_ctx(Decimal("410")))
    assert [p.metric for p in out.telemetry] == ["power_kw"]


def test_volt_var_without_voltage_emits_no_q() -> None:
    """ADR 0063 §2.3: Kurve, aber keine Netzspannung -> kein Q-Punkt."""
    out = _pv_with_volt_var().tick(_ctx(None))
    assert [p.metric for p in out.telemetry] == ["power_kw"]


def test_volt_var_emits_q_telemetry() -> None:
    out = _pv_with_volt_var().tick(_ctx(Decimal("410")))
    q = [p for p in out.telemetry if p.metric == "reactive_power_kvar"]
    assert len(q) == 1
    assert q[0].value == Decimal("-10.000000")
    assert q[0].unit == "kvar"
    assert q[0].source == "pv"


def test_volt_var_in_deadband_emits_zero_q_point() -> None:
    """ADR 0063 §2.3: mit Kurve wird auch in der Deadband ein 0-kvar-Punkt
    emittiert (Kurve konfiguriert) — anders als ganz ohne Kurve."""
    out = _pv_with_volt_var().tick(_ctx(Decimal("402")))
    q = [p for p in out.telemetry if p.metric == "reactive_power_kvar"]
    assert len(q) == 1
    assert q[0].value == Decimal("0.000000")


# --- Snapshot opt-in (ADR 0063 §2.5) ---------------------------------------


def test_no_volt_var_snapshot_omits_key() -> None:
    pv = PvDevice()
    pv.initialize(_scenario_device(rated_power_kw=Decimal("100")), FixedSeedRandom(seed=0))
    pv.set_run_id("r")
    config_state = cast(Mapping[str, object], pv.snapshot()["config"])
    assert "volt_var" not in config_state


def test_volt_var_snapshot_roundtrip() -> None:
    pv = _pv_with_volt_var()
    pv.tick(_ctx(Decimal("410")))
    state = pv.snapshot()
    config_state = cast(Mapping[str, object], state["config"])
    assert isinstance(config_state["volt_var"], dict)
    restored = PvDevice.from_snapshot(state)
    assert restored == pv
    restored_config = cast(PvConfig, restored._config)  # type: ignore[attr-defined]
    assert restored_config.volt_var == _volt_var()
