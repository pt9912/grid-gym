"""Tests fuer `EvChargerDevice` (M8 Welle 2a, ADR 0055, GG-DEV-015).

Konsolidiert Config-/Commands-/Snapshot-/Model-/Determinismus-Tests
in einem Modul (Spiegel zu Battery/GridConnection).

Pinnt:
- `EvChargerConfig`-Validierung (positive Caps, `cv_phase_start_soc`
  in `(0, 0.99]`, `initial_soc` in `[0, 1]`, Plug-Enum; ADR 0055 §2.3).
- Command-Surface (`set_charge_power` ACCEPTED/LIMITED/REJECTED/
  IGNORED; `set_plug_state`; ADR 0055 §2.6).
- CC/CV-Ladekennlinie + V2G-Entladung + Energie-Limit (ADR 0055
  §2.4/§2.5/§2.8).
- Snapshot-Roundtrip byte-stabil inkl. `stored_kwh`/`plug_state`/
  kumulativer Energie.
- Protocol-Adherence + Lifecycle-Pre-init-Raises.
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
from grid_gym.hexagon.core.devices.ev_charger import EvChargerDevice
from grid_gym.hexagon.core.devices.ev_charger.commands import (
    COMMAND_TYPE_SET_CHARGE_POWER,
    COMMAND_TYPE_SET_PLUG_STATE,
    EvChargerAlarm,
    validate_set_charge_power,
    validate_set_plug_state,
)
from grid_gym.hexagon.core.devices.ev_charger.config import (
    PLUG_STATE_PLUGGED,
    PLUG_STATE_UNPLUGGED,
    EvChargerConfig,
    EvChargerConfigInvalidValueError,
)
from grid_gym.hexagon.core.devices.ev_charger.snapshot import (
    SNAPSHOT_VERSION,
    EvChargerSnapshot,
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

_DEFAULT_PARAMS: dict[str, object] = {
    "max_charge_kw": Decimal("11"),
    "max_discharge_kw": Decimal("11"),
    "nominal_voltage_v": Decimal("400"),
    "battery_capacity_kwh": Decimal("60"),
    "cv_phase_start_soc": Decimal("0.8"),
}


def _scenario_device(**overrides: object) -> ScenarioDevice:
    params = {**_DEFAULT_PARAMS, **overrides}
    return ScenarioDevice(id="ev-1", type="ev_charger", params=params)


def _config(**overrides: object) -> EvChargerConfig:
    base: dict[str, object] = {
        "max_charge_kw": Decimal("11"),
        "max_discharge_kw": Decimal("11"),
        "nominal_voltage_v": Decimal("400"),
        "battery_capacity_kwh": Decimal("60"),
        "cv_phase_start_soc": Decimal("0.8"),
    }
    base.update(overrides)
    return EvChargerConfig(**base)  # type: ignore[arg-type]


def _command(
    cmd_type: str = COMMAND_TYPE_SET_CHARGE_POWER,
    value: object = Decimal("5"),
    command_id: str = "cmd-1",
) -> Command:
    return Command(
        command_id=command_id,
        simulation_time=0,
        target_device_id="ev-1",
        type=cmd_type,
        payload={"value": value},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _context(tick: int = 0, tick_ms: int = 1000) -> DeviceTickContext:
    return DeviceTickContext(tick=tick, simulation_time=tick * tick_ms, tick_ms=tick_ms)


def _initialize(device: EvChargerDevice, **overrides: object) -> EvChargerDevice:
    device.initialize(_scenario_device(**overrides), FixedSeedRandom(seed=0))
    return device


def _plugged(initial_soc: str = "0.5", **overrides: object) -> EvChargerDevice:
    """Init + sofort einstecken (Lade-/V2G-Tests)."""
    return _initialize(
        EvChargerDevice(),
        initial_soc=Decimal(initial_soc),
        initial_plug_state=PLUG_STATE_PLUGGED,
        **overrides,
    )


def _metrics(device: EvChargerDevice) -> dict[str, TelemetryPoint]:
    return {p.metric: p for p in device.telemetry()}


# ---------------------------------------------------------------------------
# EvChargerConfig
# ---------------------------------------------------------------------------


def test_valid_config_constructs_with_defaults() -> None:
    config = _config()
    assert config.initial_soc == Decimal("0.5")
    assert config.initial_plug_state == PLUG_STATE_UNPLUGGED
    assert config.initial_stored_kwh == Decimal("30.0")


def test_config_is_frozen() -> None:
    config = _config()
    with pytest.raises(FrozenInstanceError):
        config.max_charge_kw = Decimal("1")  # type: ignore[misc]


@pytest.mark.parametrize(
    "field",
    ["max_charge_kw", "max_discharge_kw", "nominal_voltage_v", "battery_capacity_kwh"],
)
def test_non_positive_caps_rejected(field: str) -> None:
    with pytest.raises(EvChargerConfigInvalidValueError) as exc:
        _config(**{field: Decimal("0")})
    assert field in str(exc.value)


@pytest.mark.parametrize("bad", [Decimal("0"), Decimal("-0.1"), Decimal("1.0"), Decimal("1.5")])
def test_cv_phase_start_soc_out_of_range_rejected(bad: Decimal) -> None:
    with pytest.raises(EvChargerConfigInvalidValueError) as exc:
        _config(cv_phase_start_soc=bad)
    assert "cv_phase_start_soc" in str(exc.value)


def test_cv_phase_start_soc_upper_bound_inclusive() -> None:
    assert _config(cv_phase_start_soc=Decimal("0.99")).cv_phase_start_soc == Decimal("0.99")


@pytest.mark.parametrize("bad", [Decimal("-0.1"), Decimal("1.1")])
def test_initial_soc_out_of_range_rejected(bad: Decimal) -> None:
    with pytest.raises(EvChargerConfigInvalidValueError) as exc:
        _config(initial_soc=bad)
    assert "initial_soc" in str(exc.value)


def test_initial_soc_bounds_inclusive() -> None:
    assert _config(initial_soc=Decimal("0")).initial_stored_kwh == Decimal("0")
    assert _config(initial_soc=Decimal("1")).initial_stored_kwh == Decimal("60")


def test_invalid_plug_state_rejected() -> None:
    with pytest.raises(EvChargerConfigInvalidValueError) as exc:
        _config(initial_plug_state="charging")
    assert "initial_plug_state" in str(exc.value)


# ---------------------------------------------------------------------------
# Protocol-Adherence + Lifecycle
# ---------------------------------------------------------------------------


def test_device_satisfies_device_model_protocol() -> None:
    assert isinstance(EvChargerDevice(), DeviceModel)


def test_device_id_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        _ = EvChargerDevice().device_id


def test_tick_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        EvChargerDevice().tick(_context())


def test_apply_command_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        EvChargerDevice().apply_command(_command())


def test_double_initialize_raises() -> None:
    device = _initialize(EvChargerDevice())
    with pytest.raises(DeviceAlreadyInitializedError):
        device.initialize(_scenario_device(), FixedSeedRandom(seed=1))


def test_device_id_and_plug_after_init() -> None:
    device = _initialize(EvChargerDevice(), initial_plug_state=PLUG_STATE_PLUGGED)
    assert device.device_id == "ev-1"
    assert device.snapshot()["plug_state"] == PLUG_STATE_PLUGGED


def test_missing_required_param_raises_missing_keys() -> None:
    sd = ScenarioDevice(id="ev-1", type="ev_charger", params={})
    with pytest.raises(MissingKeysError) as exc:
        EvChargerDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc.value.subsystem == "ev_charger"


def test_non_decimal_param_raises_wrong_type() -> None:
    with pytest.raises(WrongTypeError) as exc:
        EvChargerDevice().initialize(_scenario_device(max_charge_kw=11), FixedSeedRandom(seed=0))
    assert exc.value.subsystem == "ev_charger"


def test_non_str_plug_param_raises_wrong_type() -> None:
    with pytest.raises(WrongTypeError):
        EvChargerDevice().initialize(
            _scenario_device(initial_plug_state=1), FixedSeedRandom(seed=0)
        )


def test_optional_initial_soc_param_consumed() -> None:
    device = _initialize(EvChargerDevice(), initial_soc=Decimal("0.25"))
    assert device.snapshot()["stored_kwh"] == Decimal("15.00")


# ---------------------------------------------------------------------------
# Command-Surface (ADR 0055 §2.6)
# ---------------------------------------------------------------------------


def test_set_charge_power_within_caps_accepted() -> None:
    outcome = validate_set_charge_power(
        config=_config(),
        plug_state=PLUG_STATE_PLUGGED,
        connection_loss_active=False,
        command=_command(value=Decimal("8")),
        device_id="ev-1",
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw == Decimal("8")
    assert outcome.alarm is None


def test_set_charge_power_above_cap_limited() -> None:
    outcome = validate_set_charge_power(
        config=_config(),
        plug_state=PLUG_STATE_PLUGGED,
        connection_loss_active=False,
        command=_command(value=Decimal("99")),
        device_id="ev-1",
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("11")
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("11")
    assert outcome.alarm.limit_unit == "kW"


def test_set_charge_power_below_discharge_cap_limited() -> None:
    outcome = validate_set_charge_power(
        config=_config(),
        plug_state=PLUG_STATE_PLUGGED,
        connection_loss_active=False,
        command=_command(value=Decimal("-99")),
        device_id="ev-1",
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("-11")
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("-11")


def test_set_charge_power_when_unplugged_rejected_no_alarm() -> None:
    outcome = validate_set_charge_power(
        config=_config(),
        plug_state=PLUG_STATE_UNPLUGGED,
        connection_loss_active=False,
        command=_command(value=Decimal("5")),
        device_id="ev-1",
    )
    assert outcome.result is CommandResult.REJECTED
    assert outcome.pending_power_kw is None
    assert outcome.alarm is None


def test_set_charge_power_when_connection_loss_rejected() -> None:
    outcome = validate_set_charge_power(
        config=_config(),
        plug_state=PLUG_STATE_PLUGGED,
        connection_loss_active=True,
        command=_command(value=Decimal("5")),
        device_id="ev-1",
    )
    assert outcome.result is CommandResult.REJECTED


def test_set_charge_power_wrong_type_ignored() -> None:
    outcome = validate_set_charge_power(
        config=_config(),
        plug_state=PLUG_STATE_PLUGGED,
        connection_loss_active=False,
        command=_command(cmd_type="set_mode"),
        device_id="ev-1",
    )
    assert outcome.result is CommandResult.IGNORED


def test_set_charge_power_non_decimal_value_ignored() -> None:
    outcome = validate_set_charge_power(
        config=_config(),
        plug_state=PLUG_STATE_PLUGGED,
        connection_loss_active=False,
        command=_command(value="not-a-decimal"),
        device_id="ev-1",
    )
    assert outcome.result is CommandResult.IGNORED


def test_set_charge_power_none_payload_ignored() -> None:
    cmd = Command(
        command_id="cmd-x",
        simulation_time=0,
        target_device_id="ev-1",
        type=COMMAND_TYPE_SET_CHARGE_POWER,
        payload=cast("Mapping[str, object]", None),
        validation_status="validated",
        result=CommandResult.IGNORED,
    )
    outcome = validate_set_charge_power(
        config=_config(),
        plug_state=PLUG_STATE_PLUGGED,
        connection_loss_active=False,
        command=cmd,
        device_id="ev-1",
    )
    assert outcome.result is CommandResult.IGNORED


def test_set_plug_state_unplugged_resets_pending() -> None:
    outcome = validate_set_plug_state(
        command=_command(cmd_type=COMMAND_TYPE_SET_PLUG_STATE, value=PLUG_STATE_UNPLUGGED)
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw == Decimal("0")
    assert outcome.plug_state == PLUG_STATE_UNPLUGGED


def test_set_plug_state_plugged_no_pending_change() -> None:
    outcome = validate_set_plug_state(
        command=_command(cmd_type=COMMAND_TYPE_SET_PLUG_STATE, value=PLUG_STATE_PLUGGED)
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw is None
    assert outcome.plug_state == PLUG_STATE_PLUGGED


def test_set_plug_state_invalid_value_ignored() -> None:
    outcome = validate_set_plug_state(
        command=_command(cmd_type=COMMAND_TYPE_SET_PLUG_STATE, value="charging")
    )
    assert outcome.result is CommandResult.IGNORED


def test_set_plug_state_non_str_value_ignored() -> None:
    outcome = validate_set_plug_state(
        command=_command(cmd_type=COMMAND_TYPE_SET_PLUG_STATE, value=Decimal("1"))
    )
    assert outcome.result is CommandResult.IGNORED


def test_set_plug_state_wrong_type_ignored() -> None:
    outcome = validate_set_plug_state(command=_command(cmd_type="set_mode"))
    assert outcome.result is CommandResult.IGNORED


def test_set_plug_state_none_payload_ignored() -> None:
    cmd = Command(
        command_id="cmd-x",
        simulation_time=0,
        target_device_id="ev-1",
        type=COMMAND_TYPE_SET_PLUG_STATE,
        payload=cast("Mapping[str, object]", None),
        validation_status="validated",
        result=CommandResult.IGNORED,
    )
    assert validate_set_plug_state(command=cmd).result is CommandResult.IGNORED


def test_apply_unknown_command_type_ignored() -> None:
    device = _plugged()
    assert device.apply_command(_command(cmd_type="set_mode")) is CommandResult.IGNORED


def test_apply_set_charge_power_limited_records_alarm() -> None:
    device = _plugged()
    result = device.apply_command(_command(value=Decimal("99")))
    assert result is CommandResult.LIMITED
    assert len(device.alarms) == 1
    assert isinstance(device.alarms[0], EvChargerAlarm)


def test_apply_set_plug_state_round_trip() -> None:
    device = _plugged()
    device.apply_command(_command(value=Decimal("8")))
    device.apply_command(_command(cmd_type=COMMAND_TYPE_SET_PLUG_STATE, value=PLUG_STATE_UNPLUGGED))
    assert device.snapshot()["plug_state"] == PLUG_STATE_UNPLUGGED
    assert device.snapshot()["pending_power_kw"] == Decimal("0")
    device.apply_command(_command(cmd_type=COMMAND_TYPE_SET_PLUG_STATE, value=PLUG_STATE_PLUGGED))
    assert device.snapshot()["plug_state"] == PLUG_STATE_PLUGGED


def test_drain_alarms_returns_and_clears() -> None:
    device = _plugged()
    device.apply_command(_command(value=Decimal("99")))
    assert len(device.drain_alarms()) == 1
    assert device.alarms == ()


# ---------------------------------------------------------------------------
# Tick: Plug-Gate + CC/CV + V2G + Energie-Limit (ADR 0055 §2.4/2.5/2.8)
# ---------------------------------------------------------------------------

_ONE_HOUR_MS = 3_600_000


def test_unplugged_forces_zero_power() -> None:
    device = _initialize(EvChargerDevice(), initial_plug_state=PLUG_STATE_UNPLUGGED)
    device.tick(_context(tick=0))
    assert _metrics(device)["power_kw"].value == Decimal("0.000000")


def test_cc_phase_charges_at_requested_power() -> None:
    device = _plugged(initial_soc="0.5")  # soc 0.5 < cv_start 0.8 → CC
    device.apply_command(_command(value=Decimal("11")))
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    metrics = _metrics(device)
    assert metrics["power_kw"].value == Decimal("11.000000")
    assert metrics["charged_kwh"].value == Decimal("11.000000")
    assert metrics["discharged_kwh"].value == Decimal("0.000000")
    # soc = (30 + 11) / 60.
    assert metrics["soc"].value == (Decimal("41") / Decimal("60")).quantize(Decimal("0.000001"))


def test_cv_phase_tapers_charge_power() -> None:
    device = _plugged(initial_soc="0.9")  # soc 0.9 >= cv_start 0.8 → CV
    device.apply_command(_command(value=Decimal("11")))
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    # effective_max = 11 * (1 - 0.9) / (1 - 0.8) = 5.5.
    assert _metrics(device)["power_kw"].value == Decimal("5.500000")


def test_cc_cv_boundary_at_threshold_charges_full() -> None:
    """ADR 0055 §2.4: bei `soc == cv_phase_start_soc` ist der CV-Taper
    `(1 - soc) / (1 - cv_start) = 1`, d. h. die Kennlinie ist am Uebergang
    stetig — Laden noch mit vollem CC-Cap. Pinnt die Boundary (die `<`/`<=`-
    Zweige sind hier per Konstruktion deckungsgleich)."""
    device = _plugged(initial_soc="0.8")  # soc == cv_phase_start_soc (0.8)
    device.apply_command(_command(value=Decimal("11")))
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    assert _metrics(device)["power_kw"].value == Decimal("11.000000")


def test_full_battery_charges_zero() -> None:
    device = _plugged(initial_soc="1")
    device.apply_command(_command(value=Decimal("11")))
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    metrics = _metrics(device)
    assert metrics["power_kw"].value == Decimal("0.000000")
    assert metrics["soc"].value == Decimal("1.000000")


def test_energy_limit_caps_charge_near_full() -> None:
    # capacity 10, soc 0.5 (stored 5, headroom 5), max_charge 100 → CC.
    device = _plugged(
        initial_soc="0.5",
        battery_capacity_kwh=Decimal("10"),
        max_charge_kw=Decimal("100"),
    )
    device.apply_command(_command(value=Decimal("100")))
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    metrics = _metrics(device)
    # desired 100 kWh > headroom 5 kWh → power reduziert auf 5 kW.
    assert metrics["power_kw"].value == Decimal("5.000000")
    assert metrics["soc"].value == Decimal("1.000000")
    # Energie-Konsistenz (ADR 0055 §2.8 Schritt 3): gespeicherte Energie
    # == power * dt == headroom; nicht die ungedeckelte Anforderung.
    assert metrics["charged_kwh"].value == Decimal("5.000000")


def test_v2g_discharge_decrements_stored() -> None:
    device = _plugged(initial_soc="0.5")  # stored 30
    device.apply_command(_command(value=Decimal("-11")))
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    metrics = _metrics(device)
    assert metrics["power_kw"].value == Decimal("-11.000000")
    assert metrics["discharged_kwh"].value == Decimal("11.000000")
    assert metrics["charged_kwh"].value == Decimal("0.000000")


def test_v2g_discharge_hard_stops_at_empty() -> None:
    device = _plugged(
        initial_soc="0",
        battery_capacity_kwh=Decimal("10"),
        max_discharge_kw=Decimal("100"),
    )
    device.apply_command(_command(value=Decimal("-100")))
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    metrics = _metrics(device)
    assert metrics["power_kw"].value == Decimal("0.000000")
    assert metrics["discharged_kwh"].value == Decimal("0.000000")
    assert metrics["soc"].value == Decimal("0.000000")


def test_zero_power_tick_changes_nothing() -> None:
    device = _plugged(initial_soc="0.5")
    device.tick(_context(tick=0, tick_ms=_ONE_HOUR_MS))
    metrics = _metrics(device)
    assert metrics["power_kw"].value == Decimal("0.000000")
    assert metrics["charged_kwh"].value == Decimal("0.000000")
    assert metrics["discharged_kwh"].value == Decimal("0.000000")


# ---------------------------------------------------------------------------
# Telemetry (ADR 0055 §2.8)
# ---------------------------------------------------------------------------


def test_telemetry_emits_seven_metrics_sorted() -> None:
    device = _plugged()
    outcome = device.tick(_context(tick=0))
    metrics = [p.metric for p in outcome.telemetry]
    assert metrics == [
        "charged_kwh",
        "connection_loss",
        "discharged_kwh",
        "plug_state",
        "power_kw",
        "soc",
        "voltage_v",
    ]
    assert metrics == sorted(metrics)


def test_telemetry_units_and_quality() -> None:
    device = _plugged()
    outcome = device.tick(_context(tick=0))
    points = {p.metric: p for p in outcome.telemetry}
    assert points["charged_kwh"].unit == "kWh"
    assert points["power_kw"].unit == "kW"
    assert points["soc"].unit == "ratio"
    assert points["voltage_v"].unit == "V"
    assert points["plug_state"].unit == "bool"
    for point in outcome.telemetry:
        assert point.quality is Quality.VALID
        assert point.value.as_tuple().exponent == -6


def test_plug_and_loss_flags_in_telemetry() -> None:
    device = _plugged()
    device.tick(_context(tick=0))
    metrics = _metrics(device)
    assert metrics["plug_state"].value == Decimal("1.000000")
    assert metrics["connection_loss"].value == Decimal("0.000000")
    assert metrics["voltage_v"].value == Decimal("400.000000")


def test_telemetry_equals_last_tick_outcome() -> None:
    device = _plugged()
    outcome = device.tick(_context(tick=0))
    assert device.telemetry() == outcome.telemetry


def test_telemetry_pre_init_returns_empty() -> None:
    assert EvChargerDevice().telemetry() == ()


def test_cumulative_energy_monotone_over_ticks() -> None:
    device = _plugged(initial_soc="0.1")
    device.apply_command(_command(value=Decimal("5")))
    last = Decimal("0")
    for tick in range(10):
        device.tick(_context(tick=tick, tick_ms=1000))
        current = cast(Decimal, device.snapshot()["charged_kwh"])
        assert current >= last
        last = current


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip (ADR 0055 §2.8)
# ---------------------------------------------------------------------------


def test_snapshot_first_field_is_version() -> None:
    device = _plugged()
    state = device.snapshot()
    assert next(iter(state)) == "version"
    assert state["version"] == SNAPSHOT_VERSION


def test_snapshot_pre_init_returns_minimal() -> None:
    assert EvChargerDevice().snapshot() == {"version": SNAPSHOT_VERSION}


def test_snapshot_carries_required_fields() -> None:
    device = _plugged()
    state = device.snapshot()
    for key in (
        "device_id",
        "run_id",
        "sequence",
        "config",
        "plug_state",
        "stored_kwh",
        "current_power_kw",
        "pending_power_kw",
        "charged_kwh",
        "discharged_kwh",
    ):
        assert key in state


def test_from_snapshot_byte_stable_roundtrip() -> None:
    device = _plugged(initial_soc="0.3")
    device.apply_command(_command(value=Decimal("9")))
    device.tick(_context(tick=0))
    restored = EvChargerDevice.from_snapshot(device.snapshot())
    assert restored == device


def test_from_snapshot_preserves_state() -> None:
    device = _plugged(initial_soc="0.5")
    device.apply_command(_command(value=Decimal("8")))
    for tick in range(5):
        device.tick(_context(tick=tick, tick_ms=1000))
    state = device.snapshot()
    restored = EvChargerDevice.from_snapshot(state)
    assert restored.snapshot()["stored_kwh"] == state["stored_kwh"]
    assert restored.snapshot()["charged_kwh"] == state["charged_kwh"]
    assert restored.snapshot()["plug_state"] == state["plug_state"]


def test_from_snapshot_device_is_immediately_usable() -> None:
    restored = EvChargerDevice.from_snapshot(_plugged().snapshot())
    assert restored.device_id == "ev-1"
    result = restored.apply_command(_command(value=Decimal("7")))
    assert result is CommandResult.ACCEPTED
    assert restored.tick(_context(tick=1)).telemetry


def test_attach_random_after_from_snapshot() -> None:
    restored = EvChargerDevice.from_snapshot(_plugged().snapshot())
    restored.attach_random(FixedSeedRandom(seed=42))
    assert restored.tick(_context(tick=1)).telemetry


def test_eq_with_non_ev_charger_is_not_implemented() -> None:
    assert EvChargerDevice().__eq__(object()) is NotImplemented


def test_hash_changes_with_state() -> None:
    a = _plugged()
    b = _plugged()
    assert hash(a) == hash(b)
    b.apply_command(_command(value=Decimal("5")))
    b.tick(_context(tick=0))
    assert hash(a) != hash(b)


# ---------------------------------------------------------------------------
# Snapshot-Codec-Fehler
# ---------------------------------------------------------------------------


def test_from_dict_missing_top_level_key() -> None:
    state = dict(_plugged().snapshot())
    del state["stored_kwh"]
    with pytest.raises(MissingKeysError) as exc:
        EvChargerSnapshot.from_dict(state)
    assert exc.value.subsystem == "ev_charger"


def test_from_dict_unsupported_version_raises() -> None:
    state = dict(_plugged().snapshot())
    state["version"] = 99
    with pytest.raises(VersionError):
        EvChargerSnapshot.from_dict(state)


def test_from_dict_wrong_version_type_rejected() -> None:
    state = dict(_plugged().snapshot())
    state["version"] = "1"
    with pytest.raises(WrongTypeError):
        EvChargerSnapshot.from_dict(state)


def test_from_dict_invalid_plug_state_rejected() -> None:
    state = dict(_plugged().snapshot())
    state["plug_state"] = "charging"
    with pytest.raises(WrongTypeError):
        EvChargerSnapshot.from_dict(state)


def test_from_dict_invalid_config_reraises_as_wrong_type() -> None:
    state = dict(_plugged().snapshot())
    bad_config = dict(cast(Mapping[str, object], state["config"]))
    bad_config["max_charge_kw"] = Decimal("-1")
    state["config"] = bad_config
    with pytest.raises(WrongTypeError) as exc:
        EvChargerSnapshot.from_dict(state)
    assert exc.value.subsystem == "ev_charger"


# ---------------------------------------------------------------------------
# Lifecycle-Hooks
# ---------------------------------------------------------------------------


def test_set_run_id_propagates_to_telemetry() -> None:
    device = _plugged()
    device.set_run_id("run-ev-1")
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == "run-ev-1"


def test_set_run_id_pre_init_is_allowed() -> None:
    device = EvChargerDevice()
    device.set_run_id("run-pre-init")
    _initialize(device, initial_plug_state=PLUG_STATE_PLUGGED)
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == "run-pre-init"


def test_attach_random_pre_init_is_allowed() -> None:
    device = EvChargerDevice()
    device.attach_random(FixedSeedRandom(seed=99))
    _initialize(device, initial_plug_state=PLUG_STATE_PLUGGED)
    assert device.tick(_context(tick=0)).telemetry


# ---------------------------------------------------------------------------
# Determinismus-Property (ADR 0055 §2.8, ≥ 100 Ticks)
# ---------------------------------------------------------------------------

_TICKS = 100


def _run(seed: int, command_powers: tuple[Decimal, ...]) -> tuple[TelemetryPoint, ...]:
    device = EvChargerDevice()
    device.initialize(
        _scenario_device(initial_soc=Decimal("0.5"), initial_plug_state=PLUG_STATE_PLUGGED),
        FixedSeedRandom(seed=seed),
    )
    for index, power in enumerate(command_powers):
        device.apply_command(_command(value=power, command_id=f"cmd-{index}"))
    out: list[TelemetryPoint] = []
    for tick in range(_TICKS):
        out.extend(device.tick(_context(tick=tick)).telemetry)
    return tuple(out)


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
@settings(deadline=None, max_examples=15)
def test_same_seed_produces_byte_identical_trace(seed: int) -> None:
    commands = (Decimal("8"),)
    assert _run(seed, commands) == _run(seed, commands)


@given(
    power_values=st.lists(
        st.decimals(min_value=-11, max_value=11, places=0, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=5,
    )
)
@settings(deadline=None, max_examples=15)
def test_command_sequence_determinism(power_values: list[Decimal]) -> None:
    normalized = tuple(Decimal(0) if v == 0 else v for v in power_values)
    assert _run(seed=0, command_powers=normalized) == _run(seed=0, command_powers=normalized)


def test_full_100_tick_trace_has_700_telemetry_points() -> None:
    """ADR 0055 §2.8: EV-Charger emittiert 7 Metriken/Tick → 700."""
    assert len(_run(seed=42, command_powers=(Decimal("8"),))) == _TICKS * 7
