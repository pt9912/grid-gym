"""Unit-Tests fuer die metrik-adressierte Quality-Fault-Stage
(`nan_injection`) im `TickLoop` (ADR 0074; Slice 071 / GG-FAULT-003).

Pinnt (ADR 0074 §2.2/§2.4/§2.5/§2.6/§2.7):

- Aktiver `nan_injection`-Fault rewritet matchende Punkte auf den
  endlichen Sentinel `Decimal("0")` + `quality=Quality.NAN` (kein
  numerischer NaN); `source`/`sequence`/`simulation_time` bleiben.
- Match ist `(device_id, metric)`: andere Metrik / anderes Geraet
  bleibt unberuehrt.
- Aktives Fenster ist half-open `[start, start+duration)`.
- Genau **ein** Alarm je Fault beim inactive→active-Uebergang (nicht
  pro Tick); Feld-Vertrag (`quality_fault_nan_injection`, `warning`).
- Severity-Override: `NAN` (6) ersetzt nur niedrigere Severity;
  `MISSING` (7) dominiert.
- `None`-Runtime (kein Quality-Fault) ist byte-identischer no-op-Pfad.
- `build_tick_loop`/`from_snapshot`-Symmetrie + Determinismus.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator, Mapping
from decimal import Decimal
from typing import Self

import pytest

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext, DeviceTickOutcome
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice, ScenarioFault
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.scenario.loader import TickLoopWiring, build_tick_loop, load_scenario
from grid_gym.hexagon.core.simulation.quality_fault import (
    QualityFaultRuntime,
    build_quality_fault_runtime,
)
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom

# Slice 054/071: fault-Sensor-Traeger fuer `make test-fault`.
pytestmark = pytest.mark.fault

_RUN_ID = "slice-071-nan-injection-test"


class _MetricEmitterDevice:
    """Test-Double: emittiert pro Tick je `(metric, quality)`-Paar
    einen frischen Punkt (Alter 0) fuer eine feste `device_id`.
    Substanz fuer die metrik-adressierte Quality-Fault-Stage (die
    produktiven Devices emittieren unbedingt `Quality.VALID`)."""

    def __init__(
        self,
        device_id: str,
        *,
        points: tuple[tuple[str, Quality], ...],
    ) -> None:
        self._device_id = device_id
        self._points = points
        self._run_id = ""

    @property
    def device_id(self) -> str:
        return self._device_id

    def initialize(self, scenario_device: ScenarioDevice, random: FixedSeedRandom) -> None:
        _ = scenario_device
        _ = random

    def apply_command(self, command: Command) -> CommandResult:
        _ = command
        return CommandResult.IGNORED

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        return DeviceTickOutcome(
            telemetry=tuple(
                TelemetryPoint(
                    run_id=self._run_id,
                    tick=context.tick,
                    simulation_time=context.simulation_time,
                    device_id=self._device_id,
                    metric=metric,
                    value=Decimal("42"),
                    unit="V",
                    quality=quality,
                    source=f"test.{self._device_id}",
                    sequence=index,
                )
                for index, (metric, quality) in enumerate(self._points)
            ),
        )

    def snapshot(self) -> Mapping[str, object]:
        return {"version": 1}

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return ()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        _ = state
        return cls("restored", points=())

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id


def _nan_fault(
    target: str,
    metric: str,
    *,
    start_simulation_time: int = 0,
    duration_ms: int = 5000,
) -> ScenarioFault:
    return ScenarioFault(
        start_simulation_time=start_simulation_time,
        duration_ms=duration_ms,
        target=target,
        type="nan_injection",
        payload={"metric": metric},
        recovery="auto-recover-after-N-ticks",
    )


def _counting_alarm_id_source() -> Iterator[str]:
    counter = itertools.count()
    while True:
        yield f"alarm-{next(counter)}"


def _make_loop(
    devices: tuple[_MetricEmitterDevice, ...],
    faults: tuple[ScenarioFault, ...],
    *,
    alarm_source: Iterator[str] | None = None,
    max_age_ms: int | None = None,
) -> TickLoop:
    return TickLoop(
        run_id=_RUN_ID,
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=devices,
        quality_fault_runtime=build_quality_fault_runtime(faults),
        max_age_ms=max_age_ms,
        alarm_id_source=(alarm_source or _counting_alarm_id_source()).__next__,
    )


def test_active_fault_rewrites_matching_point_to_nan_sentinel() -> None:
    """ADR 0074 §2.4: aktiver `nan_injection`-Fault → matchender Punkt
    traegt Sentinel `Decimal("0")` + `quality=Quality.NAN`."""
    loop = _make_loop(
        (_MetricEmitterDevice("meter-1", points=(("voltage_v", Quality.VALID),)),),
        (_nan_fault("meter-1", "voltage_v"),),
    )
    point = loop.tick().emitted_telemetry[0]
    assert point.quality is Quality.NAN
    assert point.value == Decimal("0")
    # Kein numerischer NaN — der Wert ist endlich.
    assert point.value.is_finite()


def test_rewrite_preserves_source_sequence_simulation_time() -> None:
    """ADR 0074 §2.2: Rewrite via `dataclasses.replace` tauscht nur
    `value`/`quality`; `source`/`sequence`/`simulation_time` bleiben
    (Scheduler-Tie-Breaking unberuehrt)."""
    loop = _make_loop(
        (_MetricEmitterDevice("meter-1", points=(("voltage_v", Quality.VALID),)),),
        (_nan_fault("meter-1", "voltage_v"),),
    )
    point = loop.tick().emitted_telemetry[0]
    assert point.source == "test.meter-1"
    assert point.sequence == 0
    assert point.simulation_time == 1000
    assert point.device_id == "meter-1"


def test_only_matching_metric_is_rewritten() -> None:
    """ADR 0074 §2.2: Match ist `(device_id, metric)` — ein Punkt
    derselben Device-ID mit anderer Metrik bleibt unberuehrt."""
    loop = _make_loop(
        (
            _MetricEmitterDevice(
                "meter-1",
                points=(("voltage_v", Quality.VALID), ("current_a", Quality.VALID)),
            ),
        ),
        (_nan_fault("meter-1", "voltage_v"),),
    )
    by_metric = {p.metric: p for p in loop.tick().emitted_telemetry}
    assert by_metric["voltage_v"].quality is Quality.NAN
    assert by_metric["current_a"].quality is Quality.VALID
    assert by_metric["current_a"].value == Decimal("42")


def test_only_matching_device_is_rewritten() -> None:
    """ADR 0074 §2.2: ein Punkt eines ANDEREN Geraets mit derselben
    Metrik bleibt unberuehrt."""
    loop = _make_loop(
        (
            _MetricEmitterDevice("meter-1", points=(("voltage_v", Quality.VALID),)),
            _MetricEmitterDevice("meter-2", points=(("voltage_v", Quality.VALID),)),
        ),
        (_nan_fault("meter-1", "voltage_v"),),
    )
    by_device = {p.device_id: p for p in loop.tick().emitted_telemetry}
    assert by_device["meter-1"].quality is Quality.NAN
    assert by_device["meter-2"].quality is Quality.VALID


def test_fault_inactive_before_and_after_window() -> None:
    """ADR 0074 §2.2: half-open `[start, start+duration)` — vor Start
    und ab `start+duration` (exklusiv) kein Rewrite."""
    # Fenster [2000, 3000): aktiv nur bei now == 2000.
    loop = _make_loop(
        (_MetricEmitterDevice("meter-1", points=(("voltage_v", Quality.VALID),)),),
        (_nan_fault("meter-1", "voltage_v", start_simulation_time=2000, duration_ms=1000),),
    )
    assert loop.tick().emitted_telemetry[0].quality is Quality.VALID  # now=1000, vor Start
    assert loop.tick().emitted_telemetry[0].quality is Quality.NAN  # now=2000, im Fenster
    assert loop.tick().emitted_telemetry[0].quality is Quality.VALID  # now=3000, Fenster-Ende


def test_alarm_raised_once_on_inactive_to_active_transition() -> None:
    """ADR 0074 §2.5: genau EIN Alarm beim inactive→active-Uebergang,
    NICHT pro Tick — sonst Alarm-Flut."""
    loop = _make_loop(
        (_MetricEmitterDevice("meter-1", points=(("voltage_v", Quality.VALID),)),),
        (_nan_fault("meter-1", "voltage_v", start_simulation_time=0, duration_ms=5000),),
    )
    first = loop.tick()  # now=1000: Uebergang → 1 Alarm
    second = loop.tick()  # now=2000: weiter aktiv → 0 Alarme
    third = loop.tick()  # now=3000: weiter aktiv → 0 Alarme
    assert len(first.emitted_alarms) == 1
    assert second.emitted_alarms == ()
    assert third.emitted_alarms == ()
    # Punkte bleiben in allen drei Ticks NaN-markiert.
    assert all(r.emitted_telemetry[0].quality is Quality.NAN for r in (first, second, third))


def test_alarm_field_contract() -> None:
    """ADR 0074 §2.5: Alarm-Feld-Vertrag (Code/Severity/Target/
    Message/Status/fault_id/Run-Kontext)."""
    loop = _make_loop(
        (_MetricEmitterDevice("meter-1", points=(("voltage_v", Quality.VALID),)),),
        (_nan_fault("meter-1", "voltage_v"),),
    )
    alarm = loop.tick().emitted_alarms[0]
    assert alarm.code == "quality_fault_nan_injection"
    assert alarm.severity == "warning"
    assert alarm.target == "meter-1"
    assert alarm.message == "nan injection on metric voltage_v"
    assert alarm.status == "active"
    assert alarm.fault_id is None
    assert alarm.run_id == _RUN_ID
    assert alarm.simulation_time_ms == 1000
    assert alarm.alarm_id == "alarm-0"


def test_severity_override_missing_dominates_lower_are_rewritten() -> None:
    """ADR 0074 §2.6: `NAN` (6) ersetzt nur niedrigere Severity —
    `VALID`/`INVALID` (0/5) werden NaN, `MISSING` (7) dominiert."""
    loop = _make_loop(
        (
            _MetricEmitterDevice("d-valid", points=(("voltage_v", Quality.VALID),)),
            _MetricEmitterDevice("d-invalid", points=(("voltage_v", Quality.INVALID),)),
            _MetricEmitterDevice("d-missing", points=(("voltage_v", Quality.MISSING),)),
        ),
        (
            _nan_fault("d-valid", "voltage_v"),
            _nan_fault("d-invalid", "voltage_v"),
            _nan_fault("d-missing", "voltage_v"),
        ),
    )
    by_device = {p.device_id: p for p in loop.tick().emitted_telemetry}
    assert by_device["d-valid"].quality is Quality.NAN
    assert by_device["d-invalid"].quality is Quality.NAN
    # MISSING dominiert: weder Quality noch Wert werden angetastet.
    assert by_device["d-missing"].quality is Quality.MISSING
    assert by_device["d-missing"].value == Decimal("42")


def test_nan_wins_over_max_age_stale() -> None:
    """ADR 0074 §2.6: laeuft ein Punkt zusaetzlich in die `max_age`-
    STALE-Stage, dominiert `NAN` (6) ueber `STALE` (3) — der Punkt ist
    NaN mit Sentinel, nicht STALE."""

    class _LaggingNanEmitter(_MetricEmitterDevice):
        def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
            # Nachlaufender Zeitstempel → max_age-Stage wuerde STALE markieren.
            return DeviceTickOutcome(
                telemetry=(
                    TelemetryPoint(
                        run_id=self._run_id,
                        tick=context.tick,
                        simulation_time=context.simulation_time - 5000,
                        device_id=self._device_id,
                        metric="voltage_v",
                        value=Decimal("42"),
                        unit="V",
                        quality=Quality.VALID,
                        source=f"test.{self._device_id}",
                        sequence=0,
                    ),
                ),
            )

    loop = _make_loop(
        (_LaggingNanEmitter("meter-1", points=()),),
        (_nan_fault("meter-1", "voltage_v"),),
        max_age_ms=1000,
    )
    point = loop.tick().emitted_telemetry[0]
    assert point.quality is Quality.NAN
    assert point.value == Decimal("0")


def test_none_runtime_is_noop() -> None:
    """ADR 0074 §2.7: ohne Quality-Fault-Runtime bleibt die Telemetrie
    unveraendert und es entstehen keine Alarme (byte-identischer Pfad)."""
    loop = TickLoop(
        run_id=_RUN_ID,
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=(_MetricEmitterDevice("meter-1", points=(("voltage_v", Quality.VALID),)),),
        quality_fault_runtime=None,
    )
    result = loop.tick()
    assert result.emitted_telemetry[0].quality is Quality.VALID
    assert result.emitted_telemetry[0].value == Decimal("42")
    assert result.emitted_alarms == ()


def test_build_quality_fault_runtime_none_without_nan_faults() -> None:
    """ADR 0074 §2.7: `build_quality_fault_runtime` liefert `None`,
    wenn kein `nan_injection`-Fault deklariert ist (Stage voll aus)."""
    physics_fault = ScenarioFault(
        start_simulation_time=0,
        duration_ms=1000,
        target="battery-1",
        type="cell_failure",
        payload={},
        recovery="auto",
    )
    assert build_quality_fault_runtime(()) is None
    assert build_quality_fault_runtime((physics_fault,)) is None
    runtime = build_quality_fault_runtime((_nan_fault("meter-1", "voltage_v"),))
    assert isinstance(runtime, QualityFaultRuntime)
    assert runtime.has_faults


def test_runtime_ignores_nan_fault_without_str_metric() -> None:
    """ADR 0074 §2.1: der Runtime-Bau ueberspringt einen
    `nan_injection`-Fault ohne gueltige `payload["metric"]: str`
    (defensive Tiefe; der Validator faengt das produktiv vorher ab)."""
    malformed = ScenarioFault(
        start_simulation_time=0,
        duration_ms=1000,
        target="meter-1",
        type="nan_injection",
        payload={},  # kein "metric"
        recovery="auto",
    )
    assert build_quality_fault_runtime((malformed,)) is None


def test_build_tick_loop_wires_quality_fault_runtime() -> None:
    """ADR 0074 §2.2: `build_tick_loop` verdrahtet den
    `QualityFaultRuntime` aus `scenario.faults` — mit `nan_injection`
    non-None, ohne None (Builder-Symmetrie)."""
    base_devices = [
        {
            "id": "grid-1",
            "type": "grid_connection",
            "params": {
                "max_import_kw": Decimal("1000"),
                "max_export_kw": Decimal("1000"),
                "nominal_voltage_v": Decimal("400"),
            },
        },
    ]
    with_fault = load_scenario(
        {
            "schema_version": "grid-gym.scenario.v1",
            "metadata": {"id": "slice-071", "name": "nan-wiring"},
            "simulation": {"tick_ms": 1000, "duration_s": 60, "seed": 42},
            "devices": base_devices,
            "faults": [
                {
                    "start_simulation_time": 0,
                    "duration_ms": 5000,
                    "target": "grid-1",
                    "type": "nan_injection",
                    "payload": {"metric": "voltage_v"},
                    "recovery": "auto",
                },
            ],
        }
    ).scenario
    loop = build_tick_loop(
        with_fault,
        run_id=_RUN_ID,
        clock=FakeClock(),
        random_root=FixedSeedRandom(seed=42),
        wiring=TickLoopWiring(),
    )
    assert loop._quality_fault_runtime is not None
    assert loop._quality_fault_runtime.has_faults

    without_fault = load_scenario(
        {
            "schema_version": "grid-gym.scenario.v1",
            "metadata": {"id": "slice-071", "name": "no-fault"},
            "simulation": {"tick_ms": 1000, "duration_s": 60, "seed": 42},
            "devices": base_devices,
        }
    ).scenario
    loop_no_fault = build_tick_loop(
        without_fault,
        run_id=_RUN_ID,
        clock=FakeClock(),
        random_root=FixedSeedRandom(seed=42),
    )
    assert loop_no_fault._quality_fault_runtime is None


def test_from_snapshot_reinjects_quality_fault_runtime() -> None:
    """ADR 0074 §2.2: `from_snapshot` nimmt `quality_fault_runtime` als
    Resume-Kwarg (Symmetrie zum Konstruktor) — ein resumed Lauf mit
    re-injiziertem Runtime markiert weiter NaN. Der Transitions-State
    startet leer (Praezedenz `ScenarioFaultEngine._active_faults`), der
    Alarm feuert daher auf dem ersten Resume-Tick erneut."""
    faults = (_nan_fault("meter-1", "voltage_v", start_simulation_time=0, duration_ms=10000),)
    original = TickLoop(
        run_id=_RUN_ID,
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        quality_fault_runtime=build_quality_fault_runtime(faults),
        alarm_id_source=_counting_alarm_id_source().__next__,
    )
    original.tick()
    snap = original.snapshot()

    resumed_clock = FakeClock()
    resumed_clock.advance(1000)
    resumed = TickLoop.from_snapshot(
        snap,
        clock=resumed_clock,
        random=FixedSeedRandom(seed=42),
        devices=(_MetricEmitterDevice("meter-1", points=(("voltage_v", Quality.VALID),)),),
        quality_fault_runtime=build_quality_fault_runtime(faults),
        alarm_id_source=_counting_alarm_id_source().__next__,
    )
    result = resumed.tick()
    assert result.emitted_telemetry[0].quality is Quality.NAN
    assert len(result.emitted_alarms) == 1


@pytest.mark.determinism
def test_two_identical_runs_produce_identical_streams_and_alarms() -> None:
    """ADR 0074 §2.6: nur Sim-Zeit (AC-NO-TIME) — zwei identisch
    konfigurierte Laeufe emittieren ueber mehrere Ticks identische
    Telemetrie- UND Alarm-Streams."""

    def _run() -> tuple[tuple[TelemetryPoint, ...], tuple[str, ...]]:
        loop = _make_loop(
            (
                _MetricEmitterDevice(
                    "meter-1",
                    points=(("voltage_v", Quality.VALID), ("current_a", Quality.VALID)),
                ),
            ),
            (_nan_fault("meter-1", "voltage_v", start_simulation_time=0, duration_ms=3000),),
        )
        telemetry: list[TelemetryPoint] = []
        alarm_codes: list[str] = []
        for _ in range(4):
            result = loop.tick()
            telemetry.extend(result.emitted_telemetry)
            alarm_codes.extend(a.code for a in result.emitted_alarms)
        return tuple(telemetry), tuple(alarm_codes)

    assert _run() == _run()
    telemetry, alarm_codes = _run()
    assert alarm_codes == ("quality_fault_nan_injection",)  # exactly one transition alarm
    assert any(p.quality is Quality.NAN for p in telemetry)
