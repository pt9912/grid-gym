"""M5-Welle-4b-Tests fuer den TickLoop-Alarm-Aggregations-Hook
(ADR 0040 Decision 16).

Pinnt:

- Ohne Devices ist `TickResult.emitted_alarms` ein leeres Tupel.
- Ein Battery mit ueberschrittenem `max_charge_kw` emittiert
  einen LIMITED-Alarm; TickLoop drainst + mapped + sammelt ihn
  in `TickResult.emitted_alarms` mit Unified-`Alarm`-Schema.
- `alarm_id_source`-Kwarg ist testbar (monotoner Zaehler-Stub
  fuer deterministische Snapshot-Asserts).
- Aggregations-Reihenfolge ist deterministisch nach Device-
  Konstruktor-Reihenfolge.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator
from decimal import Decimal

from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


def _make_battery(
    device_id: str = "battery-1",
    *,
    max_charge_kw: Decimal = Decimal("50"),
) -> BatteryDevice:
    battery = BatteryDevice()
    battery.initialize(
        ScenarioDevice(
            id=device_id,
            type="battery",
            params={
                "capacity_kwh": Decimal("100"),
                "initial_soc_pct": Decimal("50"),
                "min_soc_pct": Decimal("0"),
                "max_soc_pct": Decimal("100"),
                "max_charge_kw": max_charge_kw,
                "max_discharge_kw": Decimal("50"),
                "charge_efficiency": Decimal("1"),
                "discharge_efficiency": Decimal("1"),
                "ramp_kw_per_s": Decimal("100"),
            },
        ),
        FixedSeedRandom(seed=0),
    )
    return battery


def _set_power_command(value_kw: Decimal, target: str = "battery-1") -> Command:
    return Command(
        command_id="cmd-1",
        simulation_time=0,
        target_device_id=target,
        type="set_power_kw",
        payload={"value": value_kw},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _counting_alarm_id_source() -> Iterator[str]:
    counter = itertools.count()
    while True:
        yield f"alarm-{next(counter)}"


def _make_loop_with_devices(
    *,
    devices: tuple = (),
    alarm_id_source=None,
) -> TickLoop:
    return TickLoop(
        run_id="run-welle-4b-aggregation",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=devices,
        alarm_id_source=alarm_id_source,
    )


# ---------------------------------------------------------------------------
# Leere Aggregation
# ---------------------------------------------------------------------------


def test_tick_without_devices_yields_empty_emitted_alarms() -> None:
    """ADR 0040 §2.2: TickLoop ohne Devices liefert `()` als
    `emitted_alarms` — Backward-Compat fuer M1-Welle-4-Tests."""
    loop = _make_loop_with_devices()
    result = loop.tick()
    assert result.emitted_alarms == ()


def _make_grid(device_id: str = "grid-1") -> GridConnectionDevice:
    grid = GridConnectionDevice()
    grid.initialize(
        ScenarioDevice(
            id=device_id,
            type="grid_connection",
            params={
                "nominal_voltage_v": Decimal("400"),
                "max_import_kw": Decimal("1000"),
                "max_export_kw": Decimal("1000"),
            },
        ),
        FixedSeedRandom(seed=0),
    )
    return grid


def test_frequency_drop_fault_emits_grid_fault_alarm_in_tick_result() -> None:
    """GG-FAULT-004 Akzeptanz „erzeugt ... einen Alarm": ein aktiver
    `frequency_drop` (via GridFaultEngine als fault_port) hebt einen
    `GridConnectionFaultAlarm`, den der TickLoop drainst + auf den
    Unified-`Alarm` (`grid_fault_frequency_drop`) mapped."""
    from grid_gym.hexagon.core.domain.scenario import ScenarioFault
    from grid_gym.hexagon.core.faults import GridFaultEngine

    grid = _make_grid()
    fault = ScenarioFault(
        start_simulation_time=0,
        duration_ms=5000,
        target="grid-1",
        type="frequency_drop",
        payload={"delta_hz": Decimal("2")},
        recovery="auto-recover-after-N-ticks",
    )
    alarm_id_iterator = _counting_alarm_id_source()
    loop = TickLoop(
        run_id="run-freq-drop",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=(grid,),
        fault_port=GridFaultEngine(faults=(fault,)),
        alarm_id_source=lambda: next(alarm_id_iterator),
    )
    # Erster Tick: now=1000 liegt im Fault-Window [0, 5000).
    result = loop.tick()
    fault_alarms = [a for a in result.emitted_alarms if a.code == "grid_fault_frequency_drop"]
    assert len(fault_alarms) == 1
    alarm = fault_alarms[0]
    assert alarm.target == "grid-1"
    assert alarm.severity == "warning"
    assert alarm.status == "active"
    assert alarm.run_id == "run-freq-drop"
    assert "48" in alarm.message  # 50 - 2 Hz
    # Grid-Telemetrie traegt den gedroppten frequency_hz-Punkt.
    freq_points = [p for p in result.emitted_telemetry if p.metric == "frequency_hz"]
    assert len(freq_points) == 1
    assert freq_points[0].value == Decimal("48.000000")
    # Idempotenz: der zweite Tick (weiterhin im Window) hebt keinen
    # zweiten Alarm (inject_fault laeuft nur beim inactive→active-Uebergang).
    result2 = loop.tick()
    assert [a for a in result2.emitted_alarms if a.code == "grid_fault_frequency_drop"] == []


# ---------------------------------------------------------------------------
# Drain + Map + Aggregate
# ---------------------------------------------------------------------------


def test_battery_limited_command_emits_unified_alarm_in_tick_result() -> None:
    """ADR 0040 §2.2: Battery mit ueberschrittenem `max_charge_kw`
    emittiert einen LIMITED-Alarm; TickLoop drainst + mapped auf
    Unified-`Alarm` mit korrektem Schema."""
    battery = _make_battery(max_charge_kw=Decimal("50"))
    # Set 500 kW: ueber dem Charge-Limit → LIMITED + Alarm.
    battery.apply_command(_set_power_command(Decimal("500")))
    alarm_id_iterator = _counting_alarm_id_source()
    loop = _make_loop_with_devices(
        devices=(battery,),
        alarm_id_source=lambda: next(alarm_id_iterator),
    )
    result = loop.tick()
    assert len(result.emitted_alarms) == 1
    alarm = result.emitted_alarms[0]
    assert alarm.target == "battery-1"
    assert alarm.code == "power_clamp_limited"
    assert alarm.severity == "warning"
    assert alarm.run_id == "run-welle-4b-aggregation"
    assert alarm.status == "active"
    assert alarm.fault_id is None
    # Deterministic alarm_id from monotoner Stub.
    assert alarm.alarm_id == "alarm-0"


def test_tick_loop_aggregation_assigns_simulation_time_from_clock() -> None:
    """ADR 0040 §2.2: `simulation_time_ms` kommt aus dem Clock-
    Stand nach `advance(tick_ms)`. Bei tick_ms=1000 nach erstem
    Tick = 1000."""
    battery = _make_battery(max_charge_kw=Decimal("50"))
    battery.apply_command(_set_power_command(Decimal("500")))
    alarm_id_iterator = _counting_alarm_id_source()
    loop = _make_loop_with_devices(
        devices=(battery,),
        alarm_id_source=lambda: next(alarm_id_iterator),
    )
    result = loop.tick()
    assert result.emitted_alarms[0].simulation_time_ms == 1000


def test_default_alarm_id_source_yields_uuids() -> None:
    """ADR 0040 §2.2: Production-Default ist UUIDv4 (kollisionsfrei)."""
    battery = _make_battery(max_charge_kw=Decimal("50"))
    battery.apply_command(_set_power_command(Decimal("500")))
    loop = _make_loop_with_devices(devices=(battery,))
    result = loop.tick()
    assert len(result.emitted_alarms) == 1
    # UUIDv4 hat 36 Zeichen mit Dashes.
    assert len(result.emitted_alarms[0].alarm_id) == 36
    assert result.emitted_alarms[0].alarm_id.count("-") == 4


def test_dispatch_alarm_mapper_routes_all_5_device_alarm_families() -> None:
    """ADR 0040 §2.2: `_dispatch_alarm_mapper` isinstance-Chain
    erkennt alle 5 device-spezifischen Raw-Alarm-Typen."""
    from grid_gym.hexagon.core.devices.battery.commands import BatteryAlarm
    from grid_gym.hexagon.core.devices.grid_connection.commands import (
        GridConnectionAlarm,
    )
    from grid_gym.hexagon.core.devices.load.commands import LoadAlarm
    from grid_gym.hexagon.core.devices.pv.commands import PvAlarm
    from grid_gym.hexagon.core.devices.smart_meter.commands import SmartMeterAlarm
    from grid_gym.hexagon.core.simulation.alarm_mappers import dispatch_alarm_mapper

    common = dict(
        target_device_id="dev-1",
        limit=Decimal("1"),
        limit_unit="kW",
        result=CommandResult.LIMITED,
        command_id="c1",
    )
    raw_alarms = [
        BatteryAlarm(**common),
        PvAlarm(**common),
        LoadAlarm(**common),
        GridConnectionAlarm(**common),
        SmartMeterAlarm(
            target_device_id="dev-1",
            reason="x",
            result=CommandResult.REJECTED,
            command_id="c1",
        ),
    ]
    for raw in raw_alarms:
        mapped = dispatch_alarm_mapper(raw, run_id="r", simulation_time_ms=0, alarm_id="a")
        assert mapped.target == "dev-1"


def test_dispatch_alarm_mapper_unknown_type_raises_typeerror() -> None:
    """ADR 0040 §2.2: Forward-Compat-Defensive — unbekannter
    Typ wirft `TypeError` mit klarer Welle-7+/M3-Hinweis."""
    import pytest

    from grid_gym.hexagon.core.simulation.alarm_mappers import dispatch_alarm_mapper

    with pytest.raises(TypeError, match="unknown raw-alarm type"):
        dispatch_alarm_mapper(object(), run_id="r", simulation_time_ms=0, alarm_id="a")


def test_drain_alarms_consumes_buffer_no_re_emit_on_next_tick() -> None:
    """ADR 0040 §2.2 + ADR 0014 §2.5: `drain_alarms` ist
    destruktiv — der zweite Tick liefert keine Alarms mehr,
    sofern kein neuer Command appliziert wurde."""
    battery = _make_battery(max_charge_kw=Decimal("50"))
    battery.apply_command(_set_power_command(Decimal("500")))
    loop = _make_loop_with_devices(devices=(battery,))
    first = loop.tick()
    second = loop.tick()
    assert len(first.emitted_alarms) == 1
    assert second.emitted_alarms == ()


class _UnknownDeviceStub:
    """Welle-4b-Review-Fix #4: Minimal-Stub mit `drain_alarms()`-
    Surface, der eine fremde Raw-Alarm-Klasse liefert — simuliert
    ein Welle-7+/M3-Geraet, dessen Raw-Typ der Mapper nicht kennt."""

    def __init__(self, raw_alarm: object) -> None:
        self._raw = raw_alarm
        self._drained = False

    @property
    def device_id(self) -> str:
        return "unknown-1"

    def set_run_id(self, run_id: str) -> None:
        return

    def tick(self, context: object) -> object:
        from grid_gym.hexagon.core.domain.device import DeviceTickOutcome

        return DeviceTickOutcome(telemetry=())

    def drain_alarms(self) -> tuple[object, ...]:
        if self._drained:
            return ()
        self._drained = True
        return (self._raw,)


def test_tick_continues_when_mapper_does_not_know_raw_alarm_type() -> None:
    """Welle-4b-Review-Fix #4: ein Welle-7+/M3-Geraet mit einer
    nicht-registrierten Raw-Alarm-Klasse darf den Tick NICHT
    abreissen — sonst staende `tick_count` nie wieder auf
    `running` und der Clock waere bereits weiter."""
    stub = _UnknownDeviceStub(raw_alarm=object())
    loop = _make_loop_with_devices(devices=(stub,))
    result = loop.tick()
    assert result.tick == 0
    # Counter wird inkrementiert, aber Tick laeuft durch.
    assert loop.unknown_alarm_type_count == 1
    assert loop.tick_count == 1
    assert result.emitted_alarms == ()


def test_tick_drains_all_devices_before_mapping_atomicity() -> None:
    """Welle-4b-Review-Fix #4: erst ALLE Devices drainen, dann
    mappen. Sonst koennte ein Mapper-Fehler in der Mitte des
    Drain-Loops Raw-Alarms spaeterer Devices verschlucken."""
    # Stub vor Battery: liefert unbekannten Raw, dahinter ein
    # echtes Battery-LIMITED. Erwartung: Battery-Alarm wird trotzdem
    # gemappt (kein Drop), nur der Unknown wird gezaehlt.
    stub = _UnknownDeviceStub(raw_alarm=object())
    battery = _make_battery(max_charge_kw=Decimal("50"))
    battery.apply_command(_set_power_command(Decimal("500")))
    loop = _make_loop_with_devices(devices=(stub, battery))
    result = loop.tick()
    assert loop.unknown_alarm_type_count == 1
    assert len(result.emitted_alarms) == 1
    assert result.emitted_alarms[0].target == "battery-1"
