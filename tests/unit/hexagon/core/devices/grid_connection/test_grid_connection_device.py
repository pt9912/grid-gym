"""Tests fuer `GridConnectionDevice` (M2 Welle 4a, ADR 0017, GG-DEV-012).

Konsolidiert Config-/Commands-/Snapshot-/Model-/Determinismus-
Tests in einem Modul (Spiegel zu PV/Load).

Pinnt:
- GridConnectionConfig-Validierung (positive
  nominal_voltage_v / max_import_kw / max_export_kw,
  ADR 0017 §2.3).
- Command-Surface (set_power_kw ACCEPTED/LIMITED/IGNORED;
  **kein** REJECTED-Pfad fuer Vorzeichen — ADR 0017 §2.4).
- Sign-Konvention bidirektional (positiv = Import, negativ =
  Export; ADR 0017 §2.2).
- Snapshot-Roundtrip byte-stabil inkl. kumulativer
  `import_kwh`/`export_kwh`-Felder + Codec-Errors.
- Protocol-Adherence (`isinstance(GridConnectionDevice(),
  DeviceModel)`).
- Lifecycle-Pre-init-Raises.
- Energie-Akkumulation (delta_kwh aus tick_ms) und Monotonie.
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
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.devices.grid_connection.commands import (
    COMMAND_TYPE_SET_POWER_KW,
    GridConnectionAlarm,
    validate_set_power_command,
)
from grid_gym.hexagon.core.devices.grid_connection.config import (
    GridConnectionConfig,
    GridConnectionConfigInvalidValueError,
)
from grid_gym.hexagon.core.devices.grid_connection.snapshot import (
    SNAPSHOT_VERSION,
    GridConnectionSnapshot,
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


def _scenario_device(
    nominal_voltage_v: Decimal = Decimal("400"),
    max_import_kw: Decimal = Decimal("100"),
    max_export_kw: Decimal = Decimal("50"),
) -> ScenarioDevice:
    return ScenarioDevice(
        id="grid-1",
        type="grid_connection",
        params={
            "nominal_voltage_v": nominal_voltage_v,
            "max_import_kw": max_import_kw,
            "max_export_kw": max_export_kw,
        },
    )


def _command(
    cmd_type: str = COMMAND_TYPE_SET_POWER_KW,
    value: object = Decimal("10"),
    command_id: str = "cmd-1",
) -> Command:
    payload: dict[str, object] = {"value": value}
    return Command(
        command_id=command_id,
        simulation_time=0,
        target_device_id="grid-1",
        type=cmd_type,
        payload=payload,
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _context(tick: int = 0, tick_ms: int = 1000) -> DeviceTickContext:
    return DeviceTickContext(tick=tick, simulation_time=tick * tick_ms, tick_ms=tick_ms)


def _initialize(
    device: GridConnectionDevice,
    *,
    nominal_voltage_v: Decimal = Decimal("400"),
    max_import_kw: Decimal = Decimal("100"),
    max_export_kw: Decimal = Decimal("50"),
) -> GridConnectionDevice:
    sd = _scenario_device(
        nominal_voltage_v=nominal_voltage_v,
        max_import_kw=max_import_kw,
        max_export_kw=max_export_kw,
    )
    device.initialize(sd, FixedSeedRandom(seed=0))
    return device


# ---------------------------------------------------------------------------
# GridConnectionConfig
# ---------------------------------------------------------------------------


def test_valid_config_constructs() -> None:
    config = GridConnectionConfig(
        nominal_voltage_v=Decimal("400"),
        max_import_kw=Decimal("100"),
        max_export_kw=Decimal("50"),
    )
    assert config.nominal_voltage_v == Decimal("400")
    assert config.max_import_kw == Decimal("100")
    assert config.max_export_kw == Decimal("50")


def test_config_is_frozen() -> None:
    config = GridConnectionConfig(
        nominal_voltage_v=Decimal("400"),
        max_import_kw=Decimal("100"),
        max_export_kw=Decimal("50"),
    )
    with pytest.raises(FrozenInstanceError):
        config.nominal_voltage_v = Decimal("230")  # type: ignore[misc]


def test_zero_nominal_voltage_rejected() -> None:
    with pytest.raises(GridConnectionConfigInvalidValueError) as exc_info:
        GridConnectionConfig(
            nominal_voltage_v=Decimal("0"),
            max_import_kw=Decimal("100"),
            max_export_kw=Decimal("50"),
        )
    assert "nominal_voltage_v" in str(exc_info.value)


def test_negative_nominal_voltage_rejected() -> None:
    with pytest.raises(GridConnectionConfigInvalidValueError):
        GridConnectionConfig(
            nominal_voltage_v=Decimal("-1"),
            max_import_kw=Decimal("100"),
            max_export_kw=Decimal("50"),
        )


def test_zero_max_import_rejected() -> None:
    with pytest.raises(GridConnectionConfigInvalidValueError) as exc_info:
        GridConnectionConfig(
            nominal_voltage_v=Decimal("400"),
            max_import_kw=Decimal("0"),
            max_export_kw=Decimal("50"),
        )
    assert "max_import_kw" in str(exc_info.value)


def test_zero_max_export_rejected() -> None:
    with pytest.raises(GridConnectionConfigInvalidValueError) as exc_info:
        GridConnectionConfig(
            nominal_voltage_v=Decimal("400"),
            max_import_kw=Decimal("100"),
            max_export_kw=Decimal("0"),
        )
    assert "max_export_kw" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Protocol-Adherence + Lifecycle
# ---------------------------------------------------------------------------


def test_grid_connection_device_satisfies_device_model_protocol() -> None:
    """ADR 0013 §5 Konvention: jede konkrete Geraete-Implementation
    durchlaeuft `isinstance(..., DeviceModel)`."""
    assert isinstance(GridConnectionDevice(), DeviceModel)


def test_device_id_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        _ = GridConnectionDevice().device_id


def test_tick_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        GridConnectionDevice().tick(_context())


def test_apply_command_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        GridConnectionDevice().apply_command(_command())


def test_double_initialize_raises() -> None:
    device = _initialize(GridConnectionDevice())
    with pytest.raises(DeviceAlreadyInitializedError):
        device.initialize(_scenario_device(), FixedSeedRandom(seed=1))


def test_device_id_after_init() -> None:
    device = _initialize(GridConnectionDevice())
    assert device.device_id == "grid-1"


def test_initial_power_is_zero() -> None:
    """ADR 0017 §2.6: Default-Output ist 0 (Balanced),
    NICHT rated_power_kw wie PV/Load."""
    device = _initialize(GridConnectionDevice())
    outcome = device.tick(_context(tick=0))
    points_by_metric = {p.metric: p for p in outcome.telemetry}
    assert points_by_metric["power_kw"].value == Decimal("0.000000")
    assert points_by_metric["import_kwh"].value == Decimal("0.000000")
    assert points_by_metric["export_kwh"].value == Decimal("0.000000")


# ---------------------------------------------------------------------------
# Param-Parsing
# ---------------------------------------------------------------------------


def test_missing_param_raises_missing_keys_error() -> None:
    sd = ScenarioDevice(id="grid-1", type="grid_connection", params={})
    with pytest.raises(MissingKeysError) as exc_info:
        GridConnectionDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc_info.value.subsystem == "grid_connection"


def test_non_decimal_param_raises_wrong_type_error() -> None:
    sd = ScenarioDevice(
        id="grid-1",
        type="grid_connection",
        params={
            "nominal_voltage_v": 400,  # int statt Decimal
            "max_import_kw": Decimal("100"),
            "max_export_kw": Decimal("50"),
        },
    )
    with pytest.raises(WrongTypeError) as exc_info:
        GridConnectionDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc_info.value.subsystem == "grid_connection"


# ---------------------------------------------------------------------------
# Command-Surface (ADR 0017 §2.4) — kein REJECTED fuer Vorzeichen
# ---------------------------------------------------------------------------


def test_unknown_command_type_returns_ignored() -> None:
    config = _config()
    outcome = validate_set_power_command(
        config=config, command=_command(cmd_type="set_mode"), device_id="grid-1"
    )
    assert outcome.result is CommandResult.IGNORED


def test_missing_value_payload_returns_ignored() -> None:
    config = _config()
    cmd = Command(
        command_id="cmd-x",
        simulation_time=0,
        target_device_id="grid-1",
        type=COMMAND_TYPE_SET_POWER_KW,
        payload={},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )
    outcome = validate_set_power_command(config=config, command=cmd, device_id="grid-1")
    assert outcome.result is CommandResult.IGNORED


def test_non_decimal_value_returns_ignored() -> None:
    config = _config()
    outcome = validate_set_power_command(
        config=config, command=_command(value="not-a-decimal"), device_id="grid-1"
    )
    assert outcome.result is CommandResult.IGNORED


def test_positive_within_import_cap_accepted() -> None:
    config = _config()
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("80")), device_id="grid-1"
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw == Decimal("80")
    assert outcome.alarm is None


def test_negative_within_export_cap_accepted_no_reject() -> None:
    """ADR 0017 §2.4: kein REJECTED-Pfad fuer Vorzeichen.
    Negative Werte innerhalb -max_export_kw werden akzeptiert."""
    config = _config()
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("-30")), device_id="grid-1"
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw == Decimal("-30")
    assert outcome.alarm is None


def test_zero_power_accepted() -> None:
    config = _config()
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("0")), device_id="grid-1"
    )
    assert outcome.result is CommandResult.ACCEPTED
    assert outcome.pending_power_kw == Decimal("0")


def test_value_above_max_import_clamped() -> None:
    config = _config()
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("150")), device_id="grid-1"
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("100")
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("100")
    assert outcome.alarm.limit_unit == "kW"


def test_value_below_minus_max_export_clamped() -> None:
    config = _config()
    outcome = validate_set_power_command(
        config=config, command=_command(value=Decimal("-200")), device_id="grid-1"
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("-50")
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("-50")
    assert outcome.alarm.limit_unit == "kW"


def test_alarm_limit_sign_disambiguates_clamp_direction() -> None:
    """ADR 0017 §2.4: das Limit-Vorzeichen disambiguiert
    Import-Clamp (positiv) vs. Export-Clamp (negativ)."""
    config = _config()
    import_alarm = validate_set_power_command(
        config=config, command=_command(value=Decimal("9999")), device_id="grid-1"
    ).alarm
    export_alarm = validate_set_power_command(
        config=config, command=_command(value=Decimal("-9999")), device_id="grid-1"
    ).alarm
    assert import_alarm is not None and export_alarm is not None
    assert import_alarm.limit > Decimal("0")
    assert export_alarm.limit < Decimal("0")


def test_alarm_carries_command_id() -> None:
    config = _config()
    outcome = validate_set_power_command(
        config=config,
        command=_command(value=Decimal("9999"), command_id="cmd-42"),
        device_id="grid-1",
    )
    assert outcome.alarm is not None
    assert outcome.alarm.command_id == "cmd-42"


# ---------------------------------------------------------------------------
# Tick + Telemetry
# ---------------------------------------------------------------------------


def test_telemetry_emits_four_metrics_sorted() -> None:
    """ADR 0017 §2.5 + M3-Welle-2 (ADR 0025 §2.1): vier
    TelemetryPoints sortiert nach Metrikname (`export_kwh`,
    `import_kwh`, `power_kw`, `voltage_v` — Welle-2 ergaenzt
    `voltage_v`).

    Welle-4a-Review M-5 + M3-Welle-2: die Sortier-Invariante wird
    mechanisch gepinnt, damit ein zukuenftiger Metrik-Eintrag
    nicht stille Drift einfuehrt.
    """
    device = _initialize(GridConnectionDevice())
    outcome = device.tick(_context(tick=0))
    metrics = [p.metric for p in outcome.telemetry]
    assert metrics == ["export_kwh", "import_kwh", "power_kw", "voltage_v"]
    assert metrics == sorted(metrics), "Telemetrie-Metriken muessen alphabetisch sortiert sein"


def test_telemetry_units() -> None:
    device = _initialize(GridConnectionDevice())
    outcome = device.tick(_context(tick=0))
    points = {p.metric: p for p in outcome.telemetry}
    assert points["export_kwh"].unit == "kWh"
    assert points["import_kwh"].unit == "kWh"
    assert points["power_kw"].unit == "kW"


def test_telemetry_quality_is_valid() -> None:
    device = _initialize(GridConnectionDevice())
    outcome = device.tick(_context(tick=0))
    for point in outcome.telemetry:
        assert point.quality is Quality.VALID


def test_telemetry_value_is_decimal_quantized() -> None:
    """Welle-4a-Review L-4: robuste Pruefung ueber `Decimal.as_tuple().
    exponent`, statt fragiles `str.split(".", 1)[1]` (das bei
    ganzzahligen Decimals ohne `.` einen IndexError werfen wuerde).
    `quantize(Decimal("0.000001"))` setzt den Exponenten immer auf
    -6, auch fuer den Wert `Decimal("0.000000")`."""
    device = _initialize(GridConnectionDevice())
    device.apply_command(_command(value=Decimal("50")))
    outcome = device.tick(_context(tick=0))
    for point in outcome.telemetry:
        assert point.value.as_tuple().exponent == -6


def test_apply_command_then_tick_uses_pending() -> None:
    device = _initialize(GridConnectionDevice())
    device.apply_command(_command(value=Decimal("75")))
    outcome = device.tick(_context(tick=0))
    points = {p.metric: p for p in outcome.telemetry}
    assert points["power_kw"].value == Decimal("75.000000")


def test_telemetry_equals_last_tick_outcome() -> None:
    device = _initialize(GridConnectionDevice())
    outcome = device.tick(_context(tick=0))
    assert device.telemetry() == outcome.telemetry


def test_telemetry_pre_init_returns_empty() -> None:
    assert GridConnectionDevice().telemetry() == ()


# ---------------------------------------------------------------------------
# Energie-Akkumulation (ADR 0017 §2.5)
# ---------------------------------------------------------------------------


def test_positive_power_increments_import_kwh() -> None:
    """delta_kwh = 60 kW * 1000 ms / 3_600_000 = 0.016666… kWh"""
    device = _initialize(GridConnectionDevice())
    device.apply_command(_command(value=Decimal("60")))
    device.tick(_context(tick=0, tick_ms=1000))
    state = device.snapshot()
    assert state["import_kwh"] > Decimal("0")
    assert state["export_kwh"] == Decimal("0")


def test_negative_power_increments_export_kwh() -> None:
    device = _initialize(GridConnectionDevice())
    device.apply_command(_command(value=Decimal("-30")))
    device.tick(_context(tick=0, tick_ms=1000))
    state = device.snapshot()
    assert state["export_kwh"] > Decimal("0")
    assert state["import_kwh"] == Decimal("0")


def test_zero_power_increments_nothing() -> None:
    device = _initialize(GridConnectionDevice())
    device.tick(_context(tick=0, tick_ms=1000))
    state = device.snapshot()
    assert state["import_kwh"] == Decimal("0")
    assert state["export_kwh"] == Decimal("0")


def test_import_kwh_monotone_over_multiple_ticks() -> None:
    """ADR 0017 §2.5-Invariante: Summen sind monoton nicht-fallend."""
    device = _initialize(GridConnectionDevice())
    device.apply_command(_command(value=Decimal("50")))
    last = Decimal("0")
    for tick in range(10):
        device.tick(_context(tick=tick, tick_ms=1000))
        state = device.snapshot()
        current = cast(Decimal, state["import_kwh"])
        assert current >= last
        last = current


def test_tick_ms_scales_delta_kwh() -> None:
    """Trigger-013-Spiegel (Welle 2): kleinerer tick_ms = feinere
    Aufloesung der Energie-Aufschreibung. Vergleich auf der
    Telemetrie-quantisierten Form (6 NK; ADR 0017 §2.5), nicht
    auf der vollen 28-Decimal-Praezision — Rounding-Drift in der
    27. Stelle ist erwartet und harmlos."""
    quantum = Decimal("0.000001")
    # Saubere Arithmetik: 60 kW * 60_000 ms / 3_600_000 = 1.0 kWh exakt.
    device_coarse = _initialize(GridConnectionDevice())
    device_fine = _initialize(GridConnectionDevice())
    device_coarse.apply_command(_command(value=Decimal("60"), command_id="a"))
    device_fine.apply_command(_command(value=Decimal("60"), command_id="b"))
    device_coarse.tick(_context(tick=0, tick_ms=60_000))
    # 10 Ticks mit tick_ms=6000 = 1 Tick mit tick_ms=60_000.
    for tick in range(10):
        device_fine.tick(_context(tick=tick, tick_ms=6_000))
    coarse_kwh = cast(Decimal, device_coarse.snapshot()["import_kwh"]).quantize(quantum)
    fine_kwh = cast(Decimal, device_fine.snapshot()["import_kwh"]).quantize(quantum)
    assert coarse_kwh == fine_kwh == Decimal("1.000000")


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip (ADR 0017 §2.3)
# ---------------------------------------------------------------------------


def test_snapshot_first_field_is_version() -> None:
    device = _initialize(GridConnectionDevice())
    state = device.snapshot()
    assert next(iter(state)) == "version"
    assert state["version"] == SNAPSHOT_VERSION


def test_snapshot_pre_init_returns_minimal() -> None:
    state = GridConnectionDevice().snapshot()
    assert state == {"version": SNAPSHOT_VERSION}


def test_snapshot_carries_required_fields() -> None:
    device = _initialize(GridConnectionDevice())
    state = device.snapshot()
    for key in (
        "device_id",
        "run_id",
        "sequence",
        "config",
        "current_power_kw",
        "pending_power_kw",
        "import_kwh",
        "export_kwh",
    ):
        assert key in state


def test_from_snapshot_byte_stable_roundtrip_after_command() -> None:
    device = _initialize(GridConnectionDevice())
    device.apply_command(_command(value=Decimal("40")))
    device.tick(_context(tick=0))
    state = device.snapshot()
    restored = GridConnectionDevice.from_snapshot(state)
    assert restored == device


def test_from_snapshot_preserves_cumulative_energy() -> None:
    """ADR 0017 §2.3: import_kwh/export_kwh ueberleben Roundtrip
    byte-stabil (kein impliziter Reset auf 0)."""
    device = _initialize(GridConnectionDevice())
    device.apply_command(_command(value=Decimal("50")))
    for tick in range(5):
        device.tick(_context(tick=tick, tick_ms=1000))
    state = device.snapshot()
    pre_import = state["import_kwh"]
    restored = GridConnectionDevice.from_snapshot(state)
    assert restored.snapshot()["import_kwh"] == pre_import


def test_from_snapshot_device_is_immediately_usable() -> None:
    """Welle-2-Review-C-1-Spiegel: from_snapshot liefert
    sofort-nutzbares Device ohne initialize()-Re-Run."""
    original = _initialize(GridConnectionDevice())
    state = original.snapshot()
    restored = GridConnectionDevice.from_snapshot(state)
    assert restored.device_id == "grid-1"
    result = restored.apply_command(_command(value=Decimal("20")))
    assert result is CommandResult.ACCEPTED
    outcome = restored.tick(_context(tick=1))
    assert outcome.telemetry


def test_from_dict_missing_top_level_key() -> None:
    device = _initialize(GridConnectionDevice())
    state = dict(device.snapshot())
    del state["import_kwh"]
    with pytest.raises(MissingKeysError) as exc_info:
        GridConnectionSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "grid_connection"


def test_from_dict_unsupported_version_raises_version_error() -> None:
    device = _initialize(GridConnectionDevice())
    state = dict(device.snapshot())
    state["version"] = 99
    with pytest.raises(VersionError):
        GridConnectionSnapshot.from_dict(state)


def test_from_dict_wrong_version_type_rejected() -> None:
    device = _initialize(GridConnectionDevice())
    state = dict(device.snapshot())
    state["version"] = "1"
    with pytest.raises(WrongTypeError):
        GridConnectionSnapshot.from_dict(state)


def test_from_dict_invalid_config_reraises_as_wrong_type() -> None:
    """ADR 0014 §2.2 M-5-Spiegel: ConfigError → WrongTypeError."""
    device = _initialize(GridConnectionDevice())
    state = dict(device.snapshot())
    bad_config = dict(cast(Mapping[str, object], state["config"]))
    bad_config["max_import_kw"] = Decimal("-1")
    state["config"] = bad_config
    with pytest.raises(WrongTypeError) as exc_info:
        GridConnectionSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "grid_connection"


# ---------------------------------------------------------------------------
# Alarms + Drain
# ---------------------------------------------------------------------------


def test_alarm_emitted_on_import_clamp() -> None:
    device = _initialize(GridConnectionDevice())
    device.apply_command(_command(value=Decimal("9999")))
    assert len(device.alarms) == 1
    alarm = device.alarms[0]
    assert isinstance(alarm, GridConnectionAlarm)
    assert alarm.result is CommandResult.LIMITED
    assert alarm.limit > Decimal("0")


def test_alarm_emitted_on_export_clamp() -> None:
    device = _initialize(GridConnectionDevice())
    device.apply_command(_command(value=Decimal("-9999")))
    assert len(device.alarms) == 1
    alarm = device.alarms[0]
    assert alarm.result is CommandResult.LIMITED
    assert alarm.limit < Decimal("0")


def test_no_alarm_on_accepted_command() -> None:
    device = _initialize(GridConnectionDevice())
    device.apply_command(_command(value=Decimal("50")))
    assert device.alarms == ()


def test_drain_alarms_returns_and_clears() -> None:
    device = _initialize(GridConnectionDevice())
    device.apply_command(_command(value=Decimal("9999")))
    drained = device.drain_alarms()
    assert len(drained) == 1
    assert device.alarms == ()


# ---------------------------------------------------------------------------
# Lifecycle-Hooks (Welle-3-Review M-4/M-6-Spiegel)
# ---------------------------------------------------------------------------


def test_set_run_id_propagates_to_telemetry() -> None:
    device = _initialize(GridConnectionDevice())
    device.set_run_id("run-grid-1")
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == "run-grid-1"


def test_run_id_default_is_empty_string_pre_set() -> None:
    device = _initialize(GridConnectionDevice())
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == ""


def test_attach_random_after_from_snapshot() -> None:
    """Welle-3-Review M-6-Spiegel: attach_random reattacht
    RandomPort fuer Welle-5+/M3-stochastische Anteile."""
    original = _initialize(GridConnectionDevice())
    state = original.snapshot()
    restored = GridConnectionDevice.from_snapshot(state)
    new_random = FixedSeedRandom(seed=42)
    restored.attach_random(new_random)
    outcome = restored.tick(_context(tick=1))
    assert outcome.telemetry


def test_set_run_id_pre_init_is_allowed() -> None:
    """Welle-4a-Review M-4: set_run_id darf vor initialize()
    aufgerufen werden (TickLoop-Lifecycle in Welle 6 kann
    run_id setzen, bevor der Scenario-Loader das Geraet
    initialisiert). Spiegelt PV/Load (kein Pre-Init-Raise auf
    set_run_id)."""
    device = GridConnectionDevice()
    device.set_run_id("run-pre-init")
    # Kein Raise — und der gespeicherte run_id taucht beim
    # ersten Tick nach Init in der Telemetrie auf.
    _initialize(device)
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == "run-pre-init"


def test_attach_random_pre_init_is_allowed() -> None:
    """Welle-4a-Review M-4: analog set_run_id. Hook bleibt
    defensiv aufrufbar — kein DeviceNotInitializedError. Der
    nachfolgende initialize()-Aufruf ueberschreibt die
    Random-Port-Referenz (ADR 0013 §2.6 Lifecycle: initialize
    setzt random)."""
    device = GridConnectionDevice()
    device.attach_random(FixedSeedRandom(seed=99))
    # Kein Raise.
    _initialize(device)
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry


# ---------------------------------------------------------------------------
# Multi-Command + last-wins (ADR 0014 §2.3-Spiegel)
# ---------------------------------------------------------------------------


def test_multiple_commands_in_same_tick_last_wins() -> None:
    device = _initialize(GridConnectionDevice())
    device.apply_command(_command(value=Decimal("10"), command_id="a"))
    device.apply_command(_command(value=Decimal("-20"), command_id="b"))
    device.apply_command(_command(value=Decimal("30"), command_id="c"))
    state = device.snapshot()
    assert state["pending_power_kw"] == Decimal("30")
    device.tick(_context(tick=0))
    points = {p.metric: p for p in device.telemetry()}
    assert points["power_kw"].value == Decimal("30.000000")


# ---------------------------------------------------------------------------
# Determinismus-Property (ADR 0017 §2.7, ≥ 100 Ticks)
# ---------------------------------------------------------------------------


_TICKS = 100


def _run_grid(seed: int, command_powers: tuple[Decimal, ...]) -> tuple[TelemetryPoint, ...]:
    device = GridConnectionDevice()
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
    """ADR 0017 §2.7 + Slice-Plan §3 Welle 4a: ≥ 100 Ticks
    byte-stabil."""
    commands = (Decimal("40"),)
    trace_a = _run_grid(seed, commands)
    trace_b = _run_grid(seed, commands)
    assert trace_a == trace_b


@given(
    power_values=st.lists(
        st.decimals(
            min_value=-50,
            max_value=100,
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
    """Zweimal dieselbe Command-Sequenz → byte-identische Telemetrie."""
    normalized = tuple(Decimal(0) if v == 0 else v for v in power_values)
    trace_a = _run_grid(seed=0, command_powers=normalized)
    trace_b = _run_grid(seed=0, command_powers=normalized)
    assert trace_a == trace_b


def test_full_100_tick_trace_has_400_telemetry_points() -> None:
    """M3-Welle-2 (ADR 0025 §2.1): GridConnection emittiert 4
    Metriken/Tick (`export_kwh`, `import_kwh`, `power_kw`,
    `voltage_v`) → 100 Ticks * 4 = 400 Points."""
    trace = _run_grid(seed=42, command_powers=(Decimal("60"),))
    assert len(trace) == 400


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
@settings(deadline=None, max_examples=10)
def test_import_kwh_monotone_property(seed: int) -> None:
    """ADR 0017 §2.5-Invariante (Hypothesis): import_kwh und
    export_kwh sind monoton nicht-fallend ueber den Lauf."""
    device = GridConnectionDevice()
    device.initialize(_scenario_device(), FixedSeedRandom(seed=seed))
    device.apply_command(_command(value=Decimal("50")))
    last_import = Decimal("0")
    last_export = Decimal("0")
    for tick in range(50):
        device.tick(_context(tick=tick))
        state = device.snapshot()
        current_import = cast(Decimal, state["import_kwh"])
        current_export = cast(Decimal, state["export_kwh"])
        assert current_import >= last_import
        assert current_export >= last_export
        last_import = current_import
        last_export = current_export


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _config() -> GridConnectionConfig:
    return GridConnectionConfig(
        nominal_voltage_v=Decimal("400"),
        max_import_kw=Decimal("100"),
        max_export_kw=Decimal("50"),
    )
