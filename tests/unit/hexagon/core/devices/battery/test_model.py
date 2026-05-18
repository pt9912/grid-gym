"""Tests fuer `BatteryDevice` (ADR 0014, `GG-BESS-001..005, 008`).

Pinnt:
- Protocol-Adherence via `isinstance(BatteryDevice(), DeviceModel)`.
- Lifecycle-Pre-init-Raises (analog Welle-1-NullDevice-Tests).
- SOC-Fortschreibung mit Wirkungsgrad-Effekt.
- Ramp-Limit zwischen Ticks (`GG-BESS-004`).
- SOC-Hard-Clamp am Boden/an der Decke (`GG-BESS-005`).
- Telemetrie-Surface: 3 Punkte (`power_kw`, `soc_kwh`, `soc_pct`),
  alphabetisch sortiert, Decimal-Praezision quantisiert.
- Snapshot-Roundtrip `from_snapshot(snapshot()) == device`.
- Param-Parsing aus `ScenarioDevice.params` mit Decimal-Vertrag.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.devices import DeviceModel
from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.battery.config import BatteryConfig
from grid_gym.hexagon.core.devices.battery.snapshot import (
    SNAPSHOT_VERSION,
    BatterySnapshot,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.errors import (
    DeviceAlreadyInitializedError,
    DeviceNotInitializedError,
    MissingKeysError,
    WrongTypeError,
)
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom


def _scenario_device(
    device_id: str = "battery-1",
    capacity_kwh: Decimal = Decimal("1000"),
    initial_soc_pct: Decimal = Decimal("50"),
    min_soc_pct: Decimal = Decimal("10"),
    max_soc_pct: Decimal = Decimal("90"),
    max_charge_kw: Decimal = Decimal("500"),
    max_discharge_kw: Decimal = Decimal("500"),
    charge_efficiency: Decimal = Decimal("0.95"),
    discharge_efficiency: Decimal = Decimal("0.95"),
    ramp_kw_per_s: Decimal = Decimal("50"),
) -> ScenarioDevice:
    return ScenarioDevice(
        id=device_id,
        type="battery",
        params={
            "capacity_kwh": capacity_kwh,
            "initial_soc_pct": initial_soc_pct,
            "min_soc_pct": min_soc_pct,
            "max_soc_pct": max_soc_pct,
            "max_charge_kw": max_charge_kw,
            "max_discharge_kw": max_discharge_kw,
            "charge_efficiency": charge_efficiency,
            "discharge_efficiency": discharge_efficiency,
            "ramp_kw_per_s": ramp_kw_per_s,
        },
    )


def _set_power_command(
    value: Decimal,
    *,
    command_id: str = "cmd-1",
    target: str = "battery-1",
) -> Command:
    return Command(
        command_id=command_id,
        simulation_time=0,
        target_device_id=target,
        type="set_power_kw",
        payload={"value": value},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _context(
    tick: int = 0, tick_ms: int = 1000, simulation_time: int | None = None
) -> DeviceTickContext:
    return DeviceTickContext(
        tick=tick,
        simulation_time=simulation_time if simulation_time is not None else tick * tick_ms,
        tick_ms=tick_ms,
    )


def _initialize(device: BatteryDevice, **overrides: Decimal | str) -> BatteryDevice:
    scenario_kwargs = {k: v for k, v in overrides.items() if k != "device_id"}
    sd = _scenario_device(**scenario_kwargs)  # type: ignore[arg-type]
    device.initialize(sd, FixedSeedRandom(seed=0))
    return device


# ---------------------------------------------------------------------------
# Protocol-Adherence + Lifecycle
# ---------------------------------------------------------------------------


def test_battery_device_satisfies_device_model_protocol() -> None:
    """ADR 0013 §5 Konvention: jede konkrete Geraete-Implementation
    durchlaeuft `isinstance(..., DeviceModel)`."""
    device = BatteryDevice()
    assert isinstance(device, DeviceModel)


def test_battery_device_id_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        _ = BatteryDevice().device_id


def test_battery_tick_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        BatteryDevice().tick(_context())


def test_battery_apply_command_pre_init_raises() -> None:
    with pytest.raises(DeviceNotInitializedError):
        BatteryDevice().apply_command(_set_power_command(Decimal("100")))


def test_battery_snapshot_pre_init_returns_minimal() -> None:
    state = BatteryDevice().snapshot()
    assert state == {"version": SNAPSHOT_VERSION}


def test_battery_telemetry_pre_init_returns_empty() -> None:
    assert BatteryDevice().telemetry() == ()


def test_battery_double_initialize_raises() -> None:
    device = _initialize(BatteryDevice())
    with pytest.raises(DeviceAlreadyInitializedError):
        device.initialize(_scenario_device(), FixedSeedRandom(seed=1))


def test_battery_device_id_after_init() -> None:
    device = _initialize(BatteryDevice())
    assert device.device_id == "battery-1"


# ---------------------------------------------------------------------------
# Param-Parsing (Welle-2-Battery-Erstwurf erwartet Decimal-Params)
# ---------------------------------------------------------------------------


def test_missing_param_raises_missing_keys_error() -> None:
    sd = ScenarioDevice(id="battery-1", type="battery", params={"capacity_kwh": Decimal("1000")})
    with pytest.raises(MissingKeysError) as exc_info:
        BatteryDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc_info.value.subsystem == "battery"


def test_non_decimal_param_raises_wrong_type_error() -> None:
    sd = ScenarioDevice(
        id="battery-1",
        type="battery",
        params={
            "capacity_kwh": 1000,  # int statt Decimal
            "initial_soc_pct": Decimal("50"),
            "min_soc_pct": Decimal("10"),
            "max_soc_pct": Decimal("90"),
            "max_charge_kw": Decimal("500"),
            "max_discharge_kw": Decimal("500"),
            "charge_efficiency": Decimal("0.95"),
            "discharge_efficiency": Decimal("0.95"),
            "ramp_kw_per_s": Decimal("50"),
        },
    )
    with pytest.raises(WrongTypeError) as exc_info:
        BatteryDevice().initialize(sd, FixedSeedRandom(seed=0))
    assert exc_info.value.subsystem == "battery"
    assert "capacity_kwh" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Tick-Mechanik: SOC-Fortschreibung + Ramp + Hard-Clamp
# ---------------------------------------------------------------------------


def test_zero_command_keeps_soc_constant() -> None:
    device = _initialize(BatteryDevice())
    outcome = device.tick(_context(tick=0))
    # Ohne Command bleibt power=0, SOC unveraendert.
    soc_pct = next(p for p in outcome.telemetry if p.metric == "soc_pct")
    assert soc_pct.value == Decimal("50.000000")


def test_charging_at_max_power_increases_soc() -> None:
    """500 kW * 1 s * 0.95 / 3600 s = 0.131944... kWh delta."""
    device = _initialize(BatteryDevice())
    device.apply_command(_set_power_command(Decimal("500")))
    # Ramp-Limit erlaubt 50 kW pro Sekunde; tick_ms=1000 → max-delta=50.
    # current_power_kw startet bei 0; nach erstem Tick = 50.
    device.tick(_context(tick=0, tick_ms=1000))
    # Power-Telemetrie zeigt 50, nicht 500 (ramp-limited).
    power_point = next(p for p in device.telemetry() if p.metric == "power_kw")
    assert power_point.value == Decimal("50.000000")


def test_ramp_limit_progresses_over_multiple_ticks() -> None:
    """Bei 500 kW Soll und ramp=50 kW/s + tick_ms=1000 dauert es
    10 Ticks bis current_power == 500 kW."""
    device = _initialize(BatteryDevice())
    device.apply_command(_set_power_command(Decimal("500")))
    for t in range(10):
        device.tick(_context(tick=t, tick_ms=1000))
    power_point = next(p for p in device.telemetry() if p.metric == "power_kw")
    assert power_point.value == Decimal("500.000000")


def test_soc_clamp_at_ceiling() -> None:
    """Bei initial_soc_pct=89.99% und max_soc_pct=90% klemmt das
    SOC auf 90% (`GG-BESS-005`)."""
    device = BatteryDevice()
    sd = _scenario_device(
        capacity_kwh=Decimal("100"),  # kleine Kapazitaet, schneller voll
        initial_soc_pct=Decimal("89.99"),
        max_soc_pct=Decimal("90"),
        ramp_kw_per_s=Decimal("1000"),  # sofort vollladen
    )
    device.initialize(sd, FixedSeedRandom(seed=0))
    device.apply_command(_set_power_command(Decimal("500")))
    # 500 kW * 1 s * 0.95 / 3600 = ~0.132 kWh delta — viel mehr als
    # 0.01 kWh bis 90%. Hard-Clamp greift.
    for t in range(5):
        device.tick(_context(tick=t, tick_ms=1000))
    soc_pct = next(p for p in device.telemetry() if p.metric == "soc_pct")
    assert soc_pct.value <= Decimal("90.000000")


def test_soc_clamp_at_floor() -> None:
    """Analog: SOC darf nicht unter min_soc_pct fallen."""
    device = BatteryDevice()
    sd = _scenario_device(
        capacity_kwh=Decimal("100"),
        initial_soc_pct=Decimal("10.01"),
        min_soc_pct=Decimal("10"),
        ramp_kw_per_s=Decimal("1000"),
    )
    device.initialize(sd, FixedSeedRandom(seed=0))
    device.apply_command(_set_power_command(Decimal("-500")))
    for t in range(5):
        device.tick(_context(tick=t, tick_ms=1000))
    soc_pct = next(p for p in device.telemetry() if p.metric == "soc_pct")
    assert soc_pct.value >= Decimal("10.000000")


# ---------------------------------------------------------------------------
# Telemetrie-Vertrag (`GG-DEV-002`, ADR 0014 §2.4)
# ---------------------------------------------------------------------------


def test_telemetry_emits_three_metrics_alphabetical() -> None:
    device = _initialize(BatteryDevice())
    outcome = device.tick(_context(tick=0))
    metrics = [p.metric for p in outcome.telemetry]
    assert metrics == ["power_kw", "soc_kwh", "soc_pct"]


def test_telemetry_units_match_gg_data_002() -> None:
    device = _initialize(BatteryDevice())
    outcome = device.tick(_context(tick=0))
    units = {p.metric: p.unit for p in outcome.telemetry}
    assert units == {"power_kw": "kW", "soc_kwh": "kWh", "soc_pct": "pct"}


def test_telemetry_values_are_decimal_quantized() -> None:
    """`GG-DATA-005`: max. 6 Nachkommastellen."""
    device = _initialize(BatteryDevice())
    outcome = device.tick(_context(tick=0))
    for point in outcome.telemetry:
        # Sechs Nachkommastellen — fuer 0.00 zeigt str(value) "0.000000".
        assert "." in str(point.value)
        decimals_part = str(point.value).split(".", 1)[1]
        assert len(decimals_part) <= 6


def test_telemetry_quality_is_valid() -> None:
    device = _initialize(BatteryDevice())
    outcome = device.tick(_context(tick=0))
    assert all(p.quality is Quality.VALID for p in outcome.telemetry)


def test_telemetry_equals_last_tick_outcome_after_tick() -> None:
    """ADR 0013 §2.5: `telemetry()` ist `==`-identisch zu
    `DeviceTickOutcome.telemetry`."""
    device = _initialize(BatteryDevice())
    outcome = device.tick(_context(tick=3, tick_ms=1000))
    assert device.telemetry() == outcome.telemetry


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip (ADR 0013 §2.4 + ADR 0014 §2.2)
# ---------------------------------------------------------------------------


def test_snapshot_from_snapshot_byte_stable() -> None:
    device = _initialize(BatteryDevice())
    device.apply_command(_set_power_command(Decimal("250")))
    device.tick(_context(tick=0))
    state = device.snapshot()
    restored = BatteryDevice.from_snapshot(state)
    assert restored == device


def test_snapshot_first_field_is_version() -> None:
    device = _initialize(BatteryDevice())
    state = device.snapshot()
    assert next(iter(state)) == "version"
    assert state["version"] == SNAPSHOT_VERSION


def test_snapshot_carries_full_config() -> None:
    device = _initialize(BatteryDevice())
    state = device.snapshot()
    assert "config" in state
    config_state = state["config"]
    assert isinstance(config_state, dict)
    assert config_state["capacity_kwh"] == Decimal("1000")


def test_from_snapshot_reconstructs_pending_power() -> None:
    """`pending_power_kw` ist Teil des Snapshots — Resume erhaelt
    den letzten apply_command-Soll, damit der naechste tick()
    konsistent fortsetzt."""
    device = _initialize(BatteryDevice())
    device.apply_command(_set_power_command(Decimal("300")))
    state = device.snapshot()
    restored = BatteryDevice.from_snapshot(state)
    # _pending_power_kw ist privat — Roundtrip-Vergleich genuegt.
    assert restored == device


def test_from_snapshot_matches_dataclass_form() -> None:
    """`BatteryDevice.from_snapshot(...)` muss aequivalent zu
    `BatterySnapshot.from_dict(...)`-Konstruktion sein."""
    device = _initialize(BatteryDevice())
    device.tick(_context(tick=0))
    state = device.snapshot()
    direct = BatterySnapshot.from_dict(state)
    restored = BatteryDevice.from_snapshot(state)
    assert restored._soc_kwh == direct.soc_kwh  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Alarme (ADR 0014 §2.5)
# ---------------------------------------------------------------------------


def test_alarm_emitted_on_clamped_command() -> None:
    device = _initialize(BatteryDevice())
    device.apply_command(_set_power_command(Decimal("9999")))
    assert len(device.alarms) == 1
    assert device.alarms[0].result is CommandResult.LIMITED


def test_alarm_emitted_on_rejected_command() -> None:
    device = BatteryDevice()
    sd = _scenario_device(
        capacity_kwh=Decimal("100"),
        initial_soc_pct=Decimal("10"),  # genau am Boden
        min_soc_pct=Decimal("10"),
        max_soc_pct=Decimal("90"),
    )
    device.initialize(sd, FixedSeedRandom(seed=0))
    device.apply_command(_set_power_command(Decimal("-100")))  # Entladen
    assert len(device.alarms) == 1
    assert device.alarms[0].result is CommandResult.REJECTED


def test_alarms_is_tuple_snapshot_not_mutable_view() -> None:
    """`device.alarms` liefert ein Tuple — externe Mutation der
    internen Liste schlaegt nicht durch."""
    device = _initialize(BatteryDevice())
    device.apply_command(_set_power_command(Decimal("9999")))
    snap1 = device.alarms
    device.apply_command(_set_power_command(Decimal("9999")))  # zweiter Alarm
    snap2 = device.alarms
    assert len(snap1) == 1
    assert len(snap2) == 2


# ---------------------------------------------------------------------------
# Welle-2-Review M-3: drain_alarms() destruktiv
# ---------------------------------------------------------------------------


def test_drain_alarms_returns_and_clears() -> None:
    """`drain_alarms()` liefert das bisherige Tupel und leert
    die interne Liste. Welle-2-Review M-3 verlangt diese
    Drain-Semantik, damit lange Laeufe nicht unbeschraenkt
    Speicher binden (AlarmSinkPort ist erst M3)."""
    device = _initialize(BatteryDevice())
    device.apply_command(_set_power_command(Decimal("9999")))
    device.apply_command(_set_power_command(Decimal("9999")))
    drained = device.drain_alarms()
    assert len(drained) == 2
    # Nach drain: leer
    assert device.alarms == ()
    # Erneutes drain → leeres Tupel
    assert device.drain_alarms() == ()


def test_drain_alarms_returns_tuple_not_list() -> None:
    """Drain-Output ist unveraenderlich (Tupel)."""
    device = _initialize(BatteryDevice())
    device.apply_command(_set_power_command(Decimal("9999")))
    drained = device.drain_alarms()
    assert isinstance(drained, tuple)


# ---------------------------------------------------------------------------
# Welle-2-Review C-2: Saturation-Power-Reset + Alarm
# ---------------------------------------------------------------------------


def test_soc_saturation_zeroes_power_and_emits_alarm() -> None:
    """Welle-2-Review C-2 (ADR 0014 §2.4): Bei SOC-Hard-Clamp
    werden current_power_kw und pending_power_kw auf 0 gesetzt
    und ein Saturation-Alarm emittiert."""
    device = BatteryDevice()
    sd = _scenario_device(
        capacity_kwh=Decimal("100"),
        initial_soc_pct=Decimal("89.99"),  # knapp unter max
        max_soc_pct=Decimal("90"),
        ramp_kw_per_s=Decimal("1000"),  # sofort vollladen
    )
    device.initialize(sd, FixedSeedRandom(seed=0))
    device.apply_command(_set_power_command(Decimal("500")))
    # Erster Tick saettigt: 500 kW * 1 s * 0.95 / 3600 = 0.132 kWh
    # >> 0.01 kWh (90% - 89.99% von 100 kWh).
    device.tick(_context(tick=0, tick_ms=1000))
    # Power muss auf 0 stehen, Alarm muss vorliegen.
    power_point = next(p for p in device.telemetry() if p.metric == "power_kw")
    assert power_point.value == Decimal("0.000000")
    sat_alarms = [a for a in device.alarms if a.command_id == "<saturation>"]
    assert len(sat_alarms) >= 1
    assert sat_alarms[0].result is CommandResult.LIMITED
    assert sat_alarms[0].limit == Decimal("90")  # max_soc_pct


def test_soc_saturation_at_floor_alarm_carries_min_soc_pct() -> None:
    device = BatteryDevice()
    sd = _scenario_device(
        capacity_kwh=Decimal("100"),
        initial_soc_pct=Decimal("10.01"),
        min_soc_pct=Decimal("10"),
        max_soc_pct=Decimal("90"),
        ramp_kw_per_s=Decimal("1000"),
    )
    device.initialize(sd, FixedSeedRandom(seed=0))
    device.apply_command(_set_power_command(Decimal("-500")))
    device.tick(_context(tick=0, tick_ms=1000))
    sat_alarms = [a for a in device.alarms if a.command_id == "<saturation>"]
    assert len(sat_alarms) >= 1
    assert sat_alarms[0].limit == Decimal("10")  # min_soc_pct


def test_soc_saturation_no_alarm_if_power_already_zero() -> None:
    """Wenn das SOC genau an einer Grenze startet und keine Power
    aktiv ist, gibt es keinen Saturation-Alarm."""
    device = BatteryDevice()
    sd = _scenario_device(
        capacity_kwh=Decimal("100"),
        initial_soc_pct=Decimal("90"),  # genau an der Decke
        max_soc_pct=Decimal("90"),
    )
    device.initialize(sd, FixedSeedRandom(seed=0))
    # KEINE apply_command → pending=0, current=0
    device.tick(_context(tick=0))
    sat_alarms = [a for a in device.alarms if a.command_id == "<saturation>"]
    assert len(sat_alarms) == 0


# ---------------------------------------------------------------------------
# Welle-2-Review C-1: from_snapshot ist self-sufficient
# ---------------------------------------------------------------------------


def test_from_snapshot_device_id_accessible() -> None:
    """Welle-2-Review C-1: `device.device_id` MUSS post-
    `from_snapshot` funktionieren (kein
    DeviceNotInitializedError)."""
    original = _initialize(BatteryDevice())
    state = original.snapshot()
    restored = BatteryDevice.from_snapshot(state)
    assert restored.device_id == original.device_id


def test_from_snapshot_apply_command_works() -> None:
    original = _initialize(BatteryDevice())
    state = original.snapshot()
    restored = BatteryDevice.from_snapshot(state)
    result = restored.apply_command(_set_power_command(Decimal("100")))
    assert result is CommandResult.ACCEPTED


def test_from_snapshot_tick_continues_seamlessly() -> None:
    """Resume-Pfad: nach `from_snapshot` muss `tick()` direkt
    laufen, ohne Re-init."""
    original = _initialize(BatteryDevice())
    original.apply_command(_set_power_command(Decimal("250")))
    for t in range(3):
        original.tick(_context(tick=t))
    state = original.snapshot()
    restored = BatteryDevice.from_snapshot(state)
    # Setze run_id wie original (vor Tick gesetzt? Pre-init = "")
    outcome = restored.tick(_context(tick=3))
    assert outcome.telemetry  # Telemetrie kommt zurueck, kein Raise


def test_set_run_id_propagates_to_telemetry() -> None:
    """Welle-2-Review H-2: `set_run_id` setzt das `run_id`-Feld
    auf nachfolgenden Telemetrie-Emissions."""
    device = _initialize(BatteryDevice())
    device.set_run_id("run-42")
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == "run-42"


def test_run_id_default_is_empty_string_pre_set() -> None:
    """Welle-3-Review M-4: ohne `set_run_id` laeuft das Geraet mit
    `run_id=""` — TickLoop (Welle 6) muss `set_run_id` vor dem
    ersten Tick rufen."""
    device = _initialize(BatteryDevice())
    device.tick(_context(tick=0))
    for point in device.telemetry():
        assert point.run_id == ""


def test_attach_random_after_from_snapshot() -> None:
    """Welle-3-Review M-6: `attach_random` reattacht den
    `RandomPort` nach `from_snapshot`. Welle 2 Battery konsumiert
    `_random` nicht; die Methode bleibt symmetrisch fuer Welle-6-
    TickLoop, der alle drei Geraete-Typen uniform behandelt."""
    original = _initialize(BatteryDevice())
    state = original.snapshot()
    restored = BatteryDevice.from_snapshot(state)
    restored.attach_random(FixedSeedRandom(seed=42))
    outcome = restored.tick(_context(tick=1))
    assert outcome.telemetry


def test_snapshot_preserves_run_id_and_sequence() -> None:
    """Welle-2-Review H-1/H-2: run_id und sequence ueberleben
    Snapshot-Roundtrip."""
    device = _initialize(BatteryDevice())
    device.set_run_id("run-x")
    for t in range(2):
        device.tick(_context(tick=t))
    state = device.snapshot()
    assert state["run_id"] == "run-x"
    assert state["sequence"] == 6  # 2 Ticks * 3 Metriken = 6 Sequenz-Counter
    restored = BatteryDevice.from_snapshot(state)
    # Nach Resume: weiteres Tick muss sequence=7 starten.
    restored.tick(_context(tick=2))
    last_seq = max(p.sequence for p in restored.telemetry())
    assert last_seq == 9  # 6 + 3 fuer den naechsten Tick


# ---------------------------------------------------------------------------
# Welle-2-Review H-4: Multi-Command-last-wins-Semantik
# ---------------------------------------------------------------------------


def test_multiple_commands_in_same_tick_last_wins() -> None:
    """ADR 0014 §2.3 last-wins: bei mehreren apply_command-Aufrufen
    vor `tick()` setzt der letzte Command den pending_power_kw."""
    device = _initialize(BatteryDevice())
    device.apply_command(_set_power_command(Decimal("100"), command_id="cmd-a"))
    device.apply_command(_set_power_command(Decimal("300"), command_id="cmd-b"))
    device.apply_command(_set_power_command(Decimal("200"), command_id="cmd-c"))
    # Ramp = 50 kW/s * 1 s = 50 kW max-delta; pending=200,
    # current=0 → next_power=50. Aber pending wurde mit "200"
    # gesetzt (letzter Command), nicht "100" oder "300".
    state = device.snapshot()
    assert state["pending_power_kw"] == Decimal("200")
