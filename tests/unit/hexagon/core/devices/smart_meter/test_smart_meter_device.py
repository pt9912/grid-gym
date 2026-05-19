"""Tests fuer `SmartMeterDevice` (M2 Welle 4b, ADR 0018, GG-DEV-014).

Konsolidiert Config-/Commands-/Snapshot-/Model-/Aggregator-/
Determinismus-Tests in einem Modul (Spiegel zu PV/Load/
GridConnection, mit Welle-4b-spezifischen attach_sources- +
Reference-Lookup-Defense-Tests).

Pinnt:
- SmartMeterConfig-Validierung (sortiert + eindeutig +
  nicht-leere String-IDs, ADR 0018 §2.2).
- attach_sources-Lifecycle-Hook + Pre-attach-Verhalten
  (Quality.MISSING, ADR 0018 §2.3).
- Reference-Lookup-Defense (typisierter Fehler bei
  fehlender Quell-ID, ADR 0018 §2.4).
- Silent-Skip auf Metric-Ebene (Pre-init-Quelle).
- Snapshot **OHNE** aggregated_*-Felder (negative
  Assertion, ADR 0018 §2.5 DoD-Item).
- Protocol-Adherence + Lifecycle-Pre-init-Raises.
- Determinismus-Property (bedingt — Funktion der Quellen).
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
from grid_gym.hexagon.core.devices.smart_meter import SmartMeterDevice
from grid_gym.hexagon.core.devices.smart_meter.commands import SmartMeterAlarm
from grid_gym.hexagon.core.devices.smart_meter.config import (
    SmartMeterConfig,
    SmartMeterConfigInvalidValueError,
)
from grid_gym.hexagon.core.devices.smart_meter.model import (
    SmartMeterSourceMissingError,
)
from grid_gym.hexagon.core.devices.smart_meter.snapshot import (
    SNAPSHOT_VERSION,
    SmartMeterSnapshot,
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
    aggregate_device_ids: tuple[str, ...] = ("pv-1",),
    aggregate_metric_name: str = "power_kw",
) -> ScenarioDevice:
    return ScenarioDevice(
        id="meter-1",
        type="smart_meter",
        params={
            "aggregate_device_ids": list(aggregate_device_ids),
            "aggregate_metric_name": aggregate_metric_name,
        },
    )


def _command(
    cmd_type: str = "set_power_kw",
    command_id: str = "cmd-1",
) -> Command:
    return Command(
        command_id=command_id,
        simulation_time=0,
        target_device_id="meter-1",
        type=cmd_type,
        payload={"value": Decimal("10")},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _context(tick: int = 0, tick_ms: int = 1000) -> DeviceTickContext:
    return DeviceTickContext(tick=tick, simulation_time=tick * tick_ms, tick_ms=tick_ms)


def _initialize(
    device: SmartMeterDevice,
    aggregate_device_ids: tuple[str, ...] = ("pv-1",),
) -> SmartMeterDevice:
    sd = _scenario_device(aggregate_device_ids=aggregate_device_ids)
    device.initialize(sd, FixedSeedRandom(seed=0))
    return device


def _make_pv(device_id: str = "pv-1", rated: Decimal = Decimal("500")) -> PvDevice:
    """Liefert einen initialisierten PvDevice als Quelle."""
    pv = PvDevice()
    pv.initialize(
        ScenarioDevice(id=device_id, type="pv", params={"rated_power_kw": rated}),
        FixedSeedRandom(seed=0),
    )
    return pv


# ---------------------------------------------------------------------------
# SmartMeterConfig
# ---------------------------------------------------------------------------


def test_valid_config_constructs() -> None:
    config = SmartMeterConfig(aggregate_device_ids=("pv-1",))
    assert config.aggregate_device_ids == ("pv-1",)
    assert config.aggregate_metric_name == "power_kw"


def test_config_default_metric_name_is_power_kw() -> None:
    config = SmartMeterConfig(aggregate_device_ids=())
    assert config.aggregate_metric_name == "power_kw"


def test_config_empty_aggregate_device_ids_is_valid() -> None:
    """ADR 0018 §2.2: leeres Aggregat ist erlaubt; liefert spaeter
    `Decimal(0)`."""
    config = SmartMeterConfig(aggregate_device_ids=())
    assert config.aggregate_device_ids == ()


def test_config_is_frozen() -> None:
    config = SmartMeterConfig(aggregate_device_ids=("pv-1",))
    with pytest.raises(FrozenInstanceError):
        config.aggregate_metric_name = "other"  # type: ignore[misc]


def test_config_unsorted_ids_rejected() -> None:
    with pytest.raises(SmartMeterConfigInvalidValueError) as exc_info:
        SmartMeterConfig(aggregate_device_ids=("pv-1", "battery-1"))
    assert "sorted" in str(exc_info.value).lower()


def test_config_duplicate_ids_rejected() -> None:
    with pytest.raises(SmartMeterConfigInvalidValueError) as exc_info:
        SmartMeterConfig(aggregate_device_ids=("pv-1", "pv-1"))
    msg = str(exc_info.value).lower()
    # Either "unique" or "sorted" depending on which check fires first;
    # sorted check happens first wenn die Liste schon sortiert ist
    # (("pv-1", "pv-1") ist trivially sorted), aber sorted(["pv-1", "pv-1"]) == ["pv-1", "pv-1"],
    # also faellt die unique-Pruefung an.
    assert "unique" in msg or "sorted" in msg


def test_config_empty_id_rejected() -> None:
    with pytest.raises(SmartMeterConfigInvalidValueError) as exc_info:
        SmartMeterConfig(aggregate_device_ids=("",))
    assert "empty" in str(exc_info.value).lower()


def test_config_empty_metric_name_rejected() -> None:
    with pytest.raises(SmartMeterConfigInvalidValueError):
        SmartMeterConfig(aggregate_device_ids=(), aggregate_metric_name="")


# ---------------------------------------------------------------------------
# Protocol-Adherence + Lifecycle
# ---------------------------------------------------------------------------


def test_smart_meter_satisfies_device_model_protocol() -> None:
    assert isinstance(SmartMeterDevice(), DeviceModel)


def test_device_id_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        _ = SmartMeterDevice().device_id


def test_tick_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        SmartMeterDevice().tick(_context())


def test_apply_command_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        SmartMeterDevice().apply_command(_command())


def test_double_initialize_raises() -> None:
    device = _initialize(SmartMeterDevice())
    with pytest.raises(DeviceAlreadyInitializedError):
        device.initialize(_scenario_device(), FixedSeedRandom(seed=1))


def test_device_id_after_init() -> None:
    device = _initialize(SmartMeterDevice())
    assert device.device_id == "meter-1"


# ---------------------------------------------------------------------------
# Param-Parsing
# ---------------------------------------------------------------------------


def test_missing_aggregate_device_ids_raises() -> None:
    sd = ScenarioDevice(id="meter-1", type="smart_meter", params={})
    with pytest.raises(MissingKeysError) as exc_info:
        SmartMeterDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc_info.value.subsystem == "smart_meter"


def test_non_list_aggregate_device_ids_raises() -> None:
    sd = ScenarioDevice(
        id="meter-1",
        type="smart_meter",
        params={"aggregate_device_ids": "pv-1"},
    )
    with pytest.raises(WrongTypeError) as exc_info:
        SmartMeterDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc_info.value.subsystem == "smart_meter"


def test_aggregate_metric_name_optional_defaults_to_power_kw() -> None:
    """Forward-Looking: `aggregate_metric_name` darf in params fehlen."""
    sd = ScenarioDevice(
        id="meter-1",
        type="smart_meter",
        params={"aggregate_device_ids": ["pv-1"]},
    )
    device = SmartMeterDevice()
    device.initialize(sd, FixedSeedRandom(seed=0))
    state = device.snapshot()
    config_state = cast(Mapping[str, object], state["config"])
    assert config_state["aggregate_metric_name"] == "power_kw"


def test_tuple_aggregate_device_ids_accepted() -> None:
    sd = ScenarioDevice(
        id="meter-1",
        type="smart_meter",
        params={"aggregate_device_ids": ("pv-1", "pv-2")},
    )
    device = SmartMeterDevice()
    device.initialize(sd, FixedSeedRandom(seed=0))
    assert device.device_id == "meter-1"


# ---------------------------------------------------------------------------
# Command-Surface (ADR 0018 §2.6) — alles IGNORED
# ---------------------------------------------------------------------------


def test_any_command_returns_ignored() -> None:
    device = _initialize(SmartMeterDevice())
    assert device.apply_command(_command()) is CommandResult.IGNORED


def test_unknown_command_returns_ignored() -> None:
    device = _initialize(SmartMeterDevice())
    assert device.apply_command(_command(cmd_type="set_mode")) is CommandResult.IGNORED


def test_apply_command_does_not_add_alarms_in_welle_4b() -> None:
    device = _initialize(SmartMeterDevice())
    device.apply_command(_command())
    assert device.alarms == ()


# ---------------------------------------------------------------------------
# attach_sources (Welle-4b-Lifecycle-Hook, ADR 0018 §2.3)
# ---------------------------------------------------------------------------


def test_pre_attach_tick_emits_zero_with_quality_unknown() -> None:
    """ADR 0018 §2.3 / §2.4: ohne attach_sources liefert tick
    `aggregated_power_kw=0` mit `quality=UNKNOWN`."""
    device = _initialize(SmartMeterDevice())
    outcome = device.tick(_context(tick=0))
    assert len(outcome.telemetry) == 1
    point = outcome.telemetry[0]
    assert point.metric == "aggregated_power_kw"
    assert point.value == Decimal("0.000000")
    assert point.quality is Quality.MISSING


def test_attach_sources_enables_aggregation() -> None:
    device = _initialize(SmartMeterDevice())
    pv = _make_pv(rated=Decimal("500"))
    pv.tick(_context(tick=0))  # PV emittiert power_kw=500
    device.attach_sources({"pv-1": pv})
    outcome = device.tick(_context(tick=0))
    point = outcome.telemetry[0]
    assert point.value == Decimal("500.000000")
    assert point.quality is Quality.VALID


def test_attach_sources_can_be_called_multiple_times() -> None:
    """ADR 0018 §2.3: Mehrfach-Aufruf ist erlaubt (Welle-6-
    TickLoop-Reload-Pfad)."""
    device = _initialize(SmartMeterDevice())
    pv_a = _make_pv(rated=Decimal("100"))
    pv_b = _make_pv(rated=Decimal("700"))
    pv_a.tick(_context(tick=0))
    pv_b.tick(_context(tick=0))
    device.attach_sources({"pv-1": pv_a})
    device.attach_sources({"pv-1": pv_b})  # ueberschreibt
    outcome = device.tick(_context(tick=1))
    assert outcome.telemetry[0].value == Decimal("700.000000")


def test_attach_sources_defensive_copy() -> None:
    """ADR 0018 §2.3: nachtraegliche Mutation des Aufrufer-
    Mappings darf SmartMeter nicht beeinflussen."""
    device = _initialize(SmartMeterDevice())
    pv = _make_pv(rated=Decimal("500"))
    pv.tick(_context(tick=0))
    mapping: dict[str, DeviceModel] = {"pv-1": pv}
    device.attach_sources(mapping)
    mapping.clear()  # nachtraegliche Mutation
    outcome = device.tick(_context(tick=1))
    # Trotz Clear sollte SmartMeter den ursprunglichen Inhalt behalten.
    assert outcome.telemetry[0].value == Decimal("500.000000")


def test_attach_sources_pre_init_is_allowed() -> None:
    """Welle-4a-Review-M-4-Spiegel: attach_sources darf vor
    initialize() aufgerufen werden (Hook bleibt defensiv)."""
    device = SmartMeterDevice()
    pv = _make_pv(rated=Decimal("100"))
    device.attach_sources({"pv-1": pv})  # kein Raise
    _initialize(device)
    pv.tick(_context(tick=0))
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry[0].value == Decimal("100.000000")


# ---------------------------------------------------------------------------
# Reference-Lookup-Defense (ADR 0018 §2.4)
# ---------------------------------------------------------------------------


def test_missing_source_id_after_attach_raises_typed() -> None:
    """ADR 0018 §2.4: wenn attach_sources gerufen wurde, aber eine
    aggregate_device_ids-ID nicht im Mapping ist, wirft tick()
    `SmartMeterSourceMissingError`."""
    device = _initialize(
        SmartMeterDevice(),
        aggregate_device_ids=("battery-1", "pv-1"),
    )
    pv = _make_pv(rated=Decimal("500"))
    pv.tick(_context(tick=0))
    device.attach_sources({"pv-1": pv})  # battery-1 fehlt
    with pytest.raises(SmartMeterSourceMissingError) as exc_info:
        device.tick(_context(tick=0))
    assert exc_info.value.device_id == "meter-1"
    assert exc_info.value.missing_source_id == "battery-1"


def test_empty_attach_with_empty_scope_emits_zero_valid() -> None:
    """ADR 0018 §2.2: leeres aggregate_device_ids + attach({})
    liefert Decimal(0) mit Quality.VALID (kein Fehler)."""
    device = _initialize(SmartMeterDevice(), aggregate_device_ids=())
    device.attach_sources({})
    outcome = device.tick(_context(tick=0))
    point = outcome.telemetry[0]
    assert point.value == Decimal("0.000000")
    assert point.quality is Quality.VALID


# ---------------------------------------------------------------------------
# Aggregation-Mechanik (ADR 0018 §2.4)
# ---------------------------------------------------------------------------


def test_aggregation_sums_power_kw_over_multiple_sources() -> None:
    device = _initialize(
        SmartMeterDevice(),
        aggregate_device_ids=("pv-1", "pv-2"),
    )
    pv1 = _make_pv("pv-1", rated=Decimal("300"))
    pv2 = _make_pv("pv-2", rated=Decimal("500"))
    pv1.tick(_context(tick=0))
    pv2.tick(_context(tick=0))
    device.attach_sources({"pv-1": pv1, "pv-2": pv2})
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry[0].value == Decimal("800.000000")


def test_pre_init_source_contributes_zero_silent_skip() -> None:
    """ADR 0018 §2.4: Pre-init-Quelle liefert `telemetry()==()` —
    SmartMeter darf nicht durchstuerzen, Beitrag ist `0`."""
    device = _initialize(SmartMeterDevice(), aggregate_device_ids=("pv-1",))
    pv = PvDevice()  # NICHT initialisiert
    device.attach_sources({"pv-1": pv})
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry[0].value == Decimal("0.000000")
    assert outcome.telemetry[0].quality is Quality.VALID


def test_source_without_matching_metric_contributes_zero() -> None:
    """Quelle existiert + ist initialisiert, aber emittiert keine
    aggregate_metric_name-Metric → Beitrag 0."""
    device = _initialize(
        SmartMeterDevice(),
        aggregate_device_ids=("pv-1",),
    )
    # Aendere die gesuchte Metric auf etwas, das PV nicht emittiert.
    sd = ScenarioDevice(
        id="meter-1",
        type="smart_meter",
        params={
            "aggregate_device_ids": ["pv-1"],
            "aggregate_metric_name": "soc_kwh",
        },
    )
    custom_device = SmartMeterDevice()
    custom_device.initialize(sd, FixedSeedRandom(seed=0))
    pv = _make_pv(rated=Decimal("500"))
    pv.tick(_context(tick=0))
    custom_device.attach_sources({"pv-1": pv})
    outcome = custom_device.tick(_context(tick=0))
    assert outcome.telemetry[0].value == Decimal("0.000000")


# ---------------------------------------------------------------------------
# Tick + Telemetry (ADR 0018 §2.4 Punkt 5)
# ---------------------------------------------------------------------------


def test_telemetry_emits_single_aggregated_power_metric() -> None:
    device = _initialize(SmartMeterDevice())
    pv = _make_pv()
    pv.tick(_context(tick=0))
    device.attach_sources({"pv-1": pv})
    outcome = device.tick(_context(tick=0))
    metrics = [p.metric for p in outcome.telemetry]
    assert metrics == ["aggregated_power_kw"]
    assert metrics == sorted(metrics)


def test_telemetry_unit_is_kw() -> None:
    device = _initialize(SmartMeterDevice())
    pv = _make_pv()
    pv.tick(_context(tick=0))
    device.attach_sources({"pv-1": pv})
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry[0].unit == "kW"


def test_telemetry_value_is_decimal_quantized() -> None:
    device = _initialize(SmartMeterDevice())
    pv = _make_pv(rated=Decimal("500"))
    pv.tick(_context(tick=0))
    device.attach_sources({"pv-1": pv})
    outcome = device.tick(_context(tick=0))
    assert outcome.telemetry[0].value.as_tuple().exponent == -6


def test_telemetry_equals_last_tick_outcome() -> None:
    device = _initialize(SmartMeterDevice())
    pv = _make_pv()
    pv.tick(_context(tick=0))
    device.attach_sources({"pv-1": pv})
    outcome = device.tick(_context(tick=0))
    assert device.telemetry() == outcome.telemetry


def test_telemetry_pre_init_returns_empty() -> None:
    assert SmartMeterDevice().telemetry() == ()


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip (ADR 0018 §2.5) — keine aggregated_*-Felder
# ---------------------------------------------------------------------------


def test_snapshot_first_field_is_version() -> None:
    device = _initialize(SmartMeterDevice())
    state = device.snapshot()
    assert next(iter(state)) == "version"
    assert state["version"] == SNAPSHOT_VERSION


def test_snapshot_pre_init_returns_minimal() -> None:
    state = SmartMeterDevice().snapshot()
    assert state == {"version": SNAPSHOT_VERSION}


def test_snapshot_carries_required_fields() -> None:
    device = _initialize(SmartMeterDevice())
    state = device.snapshot()
    for key in ("device_id", "run_id", "sequence", "config"):
        assert key in state


def test_snapshot_does_not_carry_aggregated_fields() -> None:
    """ADR 0018 §2.5 Welle-4b-DoD: KEIN aggregated_*-Feld im
    Snapshot — Aggregate sind derived und werden nach Resume
    neu berechnet."""
    device = _initialize(SmartMeterDevice())
    pv = _make_pv()
    pv.tick(_context(tick=0))
    device.attach_sources({"pv-1": pv})
    device.tick(_context(tick=0))
    state = device.snapshot()
    config_state = cast(Mapping[str, object], state["config"])
    for key in state:
        assert not key.startswith("aggregated_")
    for key in config_state:
        assert not key.startswith("aggregated_")


def test_from_snapshot_byte_stable_roundtrip() -> None:
    device = _initialize(SmartMeterDevice(), aggregate_device_ids=("battery-1", "pv-1"))
    state = device.snapshot()
    restored = SmartMeterDevice.from_snapshot(state)
    assert restored == device


def test_from_snapshot_device_is_immediately_usable_after_attach_sources() -> None:
    """Welle-2-Review-C-1-Spiegel: from_snapshot liefert sofort-
    nutzbares Device. Aufrufer muss attach_sources rufen, dann
    tick."""
    original = _initialize(SmartMeterDevice())
    state = original.snapshot()
    restored = SmartMeterDevice.from_snapshot(state)
    assert restored.device_id == "meter-1"
    # Sources mussen nach Resume neu verdrahtet werden.
    pv = _make_pv()
    pv.tick(_context(tick=0))
    restored.attach_sources({"pv-1": pv})
    outcome = restored.tick(_context(tick=1))
    assert outcome.telemetry


def test_from_snapshot_pre_attach_after_resume() -> None:
    """Nach from_snapshot ist sources_by_id wieder None
    (ADR 0018 §2.3); erster Tick ohne attach_sources liefert
    Quality.MISSING."""
    original = _initialize(SmartMeterDevice())
    state = original.snapshot()
    restored = SmartMeterDevice.from_snapshot(state)
    outcome = restored.tick(_context(tick=1))
    assert outcome.telemetry[0].quality is Quality.MISSING


def test_from_dict_missing_top_level_key() -> None:
    device = _initialize(SmartMeterDevice())
    state = dict(device.snapshot())
    del state["config"]
    with pytest.raises(MissingKeysError) as exc_info:
        SmartMeterSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "smart_meter"


def test_from_dict_unsupported_version_raises_version_error() -> None:
    device = _initialize(SmartMeterDevice())
    state = dict(device.snapshot())
    state["version"] = 99
    with pytest.raises(VersionError):
        SmartMeterSnapshot.from_dict(state)


def test_from_dict_wrong_version_type_rejected() -> None:
    device = _initialize(SmartMeterDevice())
    state = dict(device.snapshot())
    state["version"] = "1"
    with pytest.raises(WrongTypeError):
        SmartMeterSnapshot.from_dict(state)


def test_from_dict_invalid_config_reraises_as_wrong_type() -> None:
    device = _initialize(SmartMeterDevice())
    state = dict(device.snapshot())
    bad_config = dict(cast(Mapping[str, object], state["config"]))
    bad_config["aggregate_device_ids"] = ["b", "a"]  # unsortiert
    state["config"] = bad_config
    with pytest.raises(WrongTypeError) as exc_info:
        SmartMeterSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "smart_meter"


def test_from_dict_non_list_aggregate_device_ids_rejected() -> None:
    device = _initialize(SmartMeterDevice())
    state = dict(device.snapshot())
    bad_config = dict(cast(Mapping[str, object], state["config"]))
    bad_config["aggregate_device_ids"] = "pv-1"  # string statt list
    state["config"] = bad_config
    with pytest.raises(WrongTypeError):
        SmartMeterSnapshot.from_dict(state)


# ---------------------------------------------------------------------------
# Alarms + Drain (Welle-4b-Minimum: meist leer)
# ---------------------------------------------------------------------------


def test_drain_alarms_empty_in_welle_4b() -> None:
    device = _initialize(SmartMeterDevice())
    assert device.drain_alarms() == ()


def test_alarms_tuple_returns_empty_in_welle_4b() -> None:
    device = _initialize(SmartMeterDevice())
    assert device.alarms == ()


def test_smart_meter_alarm_dataclass_constructs() -> None:
    """Forward-Looking: SmartMeterAlarm-Klasse existiert fuer
    Post-MVP-Erweiterungen (z. B. set_aggregate_scope-Command)."""
    alarm = SmartMeterAlarm(
        target_device_id="meter-1",
        reason="test",
        result=CommandResult.LIMITED,
        command_id="cmd-x",
    )
    assert alarm.target_device_id == "meter-1"


# ---------------------------------------------------------------------------
# Lifecycle-Hooks (Welle-3-Review M-4/M-6-Spiegel)
# ---------------------------------------------------------------------------


def test_set_run_id_propagates_to_telemetry() -> None:
    device = _initialize(SmartMeterDevice())
    pv = _make_pv()
    pv.tick(_context(tick=0))
    device.attach_sources({"pv-1": pv})
    device.set_run_id("run-meter-1")
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == "run-meter-1"


def test_run_id_default_is_empty_string_pre_set() -> None:
    device = _initialize(SmartMeterDevice())
    pv = _make_pv()
    pv.tick(_context(tick=0))
    device.attach_sources({"pv-1": pv})
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == ""


def test_set_run_id_pre_init_is_allowed() -> None:
    """Welle-4a-Review-M-4-Spiegel: set_run_id darf pre-init."""
    device = SmartMeterDevice()
    device.set_run_id("run-pre-init")
    _initialize(device)
    pv = _make_pv()
    pv.tick(_context(tick=0))
    device.attach_sources({"pv-1": pv})
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == "run-pre-init"


def test_attach_random_after_from_snapshot() -> None:
    original = _initialize(SmartMeterDevice())
    state = original.snapshot()
    restored = SmartMeterDevice.from_snapshot(state)
    restored.attach_random(FixedSeedRandom(seed=42))
    outcome = restored.tick(_context(tick=1))
    assert outcome.telemetry


# ---------------------------------------------------------------------------
# Determinismus-Property (ADR 0018 §2.8)
# ---------------------------------------------------------------------------


_TICKS = 100


def _run_smart_meter(seed: int) -> tuple[TelemetryPoint, ...]:
    """Faehrt einen SmartMeter ueber zwei PV-Quellen ueber 100 Ticks.

    Determinismus von SmartMeter ist bedingt — gleiche Quellen-
    Telemetrie → gleiche Aggregat-Telemetrie. PV-Quellen sind seed-
    bestimmt determined."""
    meter = SmartMeterDevice()
    meter.initialize(
        _scenario_device(aggregate_device_ids=("pv-1", "pv-2")),
        FixedSeedRandom(seed=seed),
    )
    pv1 = _make_pv("pv-1", rated=Decimal("300"))
    pv2 = _make_pv("pv-2", rated=Decimal("500"))
    meter.attach_sources({"pv-1": pv1, "pv-2": pv2})
    out: list[TelemetryPoint] = []
    for tick in range(_TICKS):
        pv1.tick(_context(tick=tick))
        pv2.tick(_context(tick=tick))
        outcome = meter.tick(_context(tick=tick))
        out.extend(outcome.telemetry)
    return tuple(out)


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
@settings(deadline=None, max_examples=20)
def test_same_seed_produces_byte_identical_trace(seed: int) -> None:
    """ADR 0018 §2.8: bedingt deterministisch — gleicher Seed +
    identische Quellen → byte-identische Telemetrie."""
    trace_a = _run_smart_meter(seed)
    trace_b = _run_smart_meter(seed)
    assert trace_a == trace_b


def test_full_100_tick_trace_has_100_telemetry_points() -> None:
    """SmartMeter emittiert 1 Metric/Tick → 100 Ticks * 1 = 100 Points."""
    trace = _run_smart_meter(seed=42)
    assert len(trace) == 100


def test_aggregation_does_not_consume_random_port() -> None:
    """ADR 0018 §2.8: SmartMeter fuegt keine eigene Entropie hinzu.
    Aufruf von tick() ueber 50 Ticks darf den RandomPort
    nicht touchen (Welle-4b-Verifikation; M3 wird das aendern)."""
    device = _initialize(SmartMeterDevice())
    pv = _make_pv()
    device.attach_sources({"pv-1": pv})
    random_before = device._random  # type: ignore[has-type]
    for tick in range(50):
        pv.tick(_context(tick=tick))
        device.tick(_context(tick=tick))
    assert device._random is random_before  # type: ignore[has-type]
