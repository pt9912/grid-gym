"""Unit-Tests fuer die metrik-adressierte Quality-Fault-Stage
(`stale_data`) im `TickLoop` (ADR 0074 §2.3; Slice 072 / GG-FAULT-002).

Pinnt (ADR 0074 §2.1/§2.2/§2.3/§2.5/§2.6/§2.7):

- Aktiver `stale_data`-Fault liefert den zuletzt gecachten gueltigen
  Wert weiter (ersetzt den frischen Wert); `source`/`sequence`/
  `simulation_time` bleiben.
- Solange `(now - cached_sim_time) ≤ max_age_ms` bleibt die Quality
  unveraendert; sobald strikt `>` → `Quality.STALE` (Grenzsemantik
  ADR 0052 §2.5: `==` ist nicht „ueberschritten").
- Kein gueltiger Vorwert (Fault ab Tick 0) → keine Wert-Weiterlieferung,
  nur STALE-Markierung, wenn der Punkt selbst zu alt ist (ehrliche
  Grenze).
- Aktives Fenster ist half-open `[start, start+duration)`.
- `stale_data` hebt **keinen** Alarm (Zwilling-Unterschied zu
  `nan_injection`; Alarm-bei-STALE ist GG-SAFE-003-Scope).
- Severity-Override: `STALE` (3) ersetzt nur niedrigere Severity;
  `MISSING` (7) dominiert.
- Der Last-Value-Cache ueberlebt den TickLoop-Snapshot **opt-in**
  (byte-identisch ohne Vorwert; Resume mitten im Fenster behaelt den
  Vorwert).
- Koexistenz mit der `max_age`-STALE-Stage (ADR 0052).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from decimal import Decimal
from typing import Self

import pytest

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext, DeviceTickOutcome
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice, ScenarioFault
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import VersionError, WrongTypeError
from grid_gym.hexagon.core.scenario.loader import TickLoopWiring, build_tick_loop, load_scenario
from grid_gym.hexagon.core.simulation.quality_fault import (
    QualityFaultRuntime,
    build_quality_fault_runtime,
)
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom

# Slice 054/072: fault-Sensor-Traeger fuer `make test-fault`.
pytestmark = pytest.mark.fault

_RUN_ID = "slice-072-stale-data-test"
_CACHE_KEY = "quality_fault_last_value_cache"


class _StaleTestEmitter:
    """Test-Double: emittiert pro Tick genau einen Punkt fuer eine feste
    `(device_id, metric)`. `value_fn(now)` liefert den frischen Wert
    (Default: Wert == Sim-Zeit, damit der Forwarding-Nachweis sichtbar
    wird — der gecachte Vorwert unterscheidet sich vom frischen Wert).
    `lag_ms` datiert den Zeitstempel zurueck (fuer max_age-/no-cache-
    Tests); `quality` steuert die Severity-Override-Tests."""

    def __init__(
        self,
        device_id: str,
        *,
        metric: str = "voltage_v",
        value_fn: Callable[[int], Decimal] | None = None,
        quality: Quality = Quality.VALID,
        lag_ms: int = 0,
    ) -> None:
        self._device_id = device_id
        self._metric = metric
        self._value_fn = value_fn or (lambda now: Decimal(now))
        self._quality = quality
        self._lag_ms = lag_ms
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
        now = context.simulation_time
        return DeviceTickOutcome(
            telemetry=(
                TelemetryPoint(
                    run_id=self._run_id,
                    tick=context.tick,
                    simulation_time=now - self._lag_ms,
                    device_id=self._device_id,
                    metric=self._metric,
                    value=self._value_fn(now),
                    unit="V",
                    quality=self._quality,
                    source=f"test.{self._device_id}",
                    sequence=0,
                ),
            ),
        )

    def snapshot(self) -> Mapping[str, object]:
        return {"version": 1}

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return ()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        _ = state
        return cls("restored")

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id


def _stale_fault(
    target: str,
    metric: str,
    *,
    start_simulation_time: int = 0,
    duration_ms: int = 10000,
    max_age_ms: int = 1000,
) -> ScenarioFault:
    return ScenarioFault(
        start_simulation_time=start_simulation_time,
        duration_ms=duration_ms,
        target=target,
        type="stale_data",
        payload={"metric": metric, "max_age_ms": max_age_ms},
        recovery="auto-recover-after-N-ticks",
    )


def _nan_fault(
    target: str,
    metric: str,
    *,
    start_simulation_time: int = 0,
    duration_ms: int = 10000,
) -> ScenarioFault:
    return ScenarioFault(
        start_simulation_time=start_simulation_time,
        duration_ms=duration_ms,
        target=target,
        type="nan_injection",
        payload={"metric": metric},
        recovery="auto-recover-after-N-ticks",
    )


def _make_loop(
    devices: tuple[_StaleTestEmitter, ...],
    faults: tuple[ScenarioFault, ...],
    *,
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
    )


def _point(
    device_id: str,
    metric: str,
    value: Decimal,
    *,
    simulation_time: int,
    quality: Quality = Quality.VALID,
) -> TelemetryPoint:
    return TelemetryPoint(
        run_id=_RUN_ID,
        tick=0,
        simulation_time=simulation_time,
        device_id=device_id,
        metric=metric,
        value=value,
        unit="V",
        quality=quality,
        source=f"test.{device_id}",
        sequence=0,
    )


# ---------------------------------------------------------------------------
# Verhalten: Forwarding, Fenster, Grenzsemantik
# ---------------------------------------------------------------------------


def test_active_fault_forwards_last_valid_value() -> None:
    """ADR 0074 §2.3: aktiver `stale_data`-Fault ersetzt den frischen
    Wert durch den zuletzt gecachten gueltigen Vorwert."""
    # Fenster [2000, 12000), max_age 1500. Vorwert wird bei now=1000
    # gecacht (Wert==Sim-Zeit==1000).
    loop = _make_loop(
        (_StaleTestEmitter("meter-1"),),
        (_stale_fault("meter-1", "voltage_v", start_simulation_time=2000, max_age_ms=1500),),
    )
    pre = loop.tick().emitted_telemetry[0]  # now=1000, vor Fenster
    assert pre.quality is Quality.VALID
    assert pre.value == Decimal("1000")

    active = loop.tick().emitted_telemetry[0]  # now=2000, aktiv, age=1000 ≤ 1500
    # Der frische Wert waere 2000 — weitergeliefert wird der Vorwert 1000.
    assert active.value == Decimal("1000")
    assert active.quality is Quality.VALID


def test_forward_preserves_source_sequence_simulation_time() -> None:
    """ADR 0074 §2.2: Rewrite via `dataclasses.replace` tauscht nur
    `value`/`quality`; `source`/`sequence`/`simulation_time` bleiben."""
    loop = _make_loop(
        (_StaleTestEmitter("meter-1"),),
        (_stale_fault("meter-1", "voltage_v", start_simulation_time=2000, max_age_ms=1500),),
    )
    loop.tick()  # now=1000: cache (1000, 1000)
    point = loop.tick().emitted_telemetry[0]  # now=2000: aktiv
    assert point.value == Decimal("1000")
    assert point.source == "test.meter-1"
    assert point.sequence == 0
    assert point.simulation_time == 2000  # frischer Zeitstempel, eingefrorener Wert
    assert point.device_id == "meter-1"


def test_max_age_boundary_strict_greater_is_stale() -> None:
    """ADR 0074 §2.3 + ADR 0052 §2.5: `(now - cached_sim_time) == max_age`
    ist NICHT stale, strikt `>` ist stale."""
    # Vorwert gecacht bei now=1000 → (1000, 1000). max_age=1000.
    loop = _make_loop(
        (_StaleTestEmitter("meter-1"),),
        (_stale_fault("meter-1", "voltage_v", start_simulation_time=2000, max_age_ms=1000),),
    )
    loop.tick()  # now=1000: cache (1000, 1000)
    at_boundary = loop.tick().emitted_telemetry[0]  # now=2000, age==1000 → nicht stale
    assert at_boundary.quality is Quality.VALID
    assert at_boundary.value == Decimal("1000")
    over_boundary = loop.tick().emitted_telemetry[0]  # now=3000, age==2000 > 1000 → stale
    assert over_boundary.quality is Quality.STALE
    assert over_boundary.value == Decimal("1000")  # Wert bleibt eingefroren


def test_fault_inactive_before_and_after_window() -> None:
    """ADR 0074 §2.2: half-open `[start, start+duration)` — vor Start und
    ab `start+duration` (exklusiv) kein Rewrite (frischer Wert flieszt)."""
    # Fenster [2000, 3000): aktiv nur bei now == 2000. max_age 100, damit
    # der Vorwert im aktiven Tick sofort stale waere — beweist zugleich,
    # dass ausserhalb des Fensters NICHT eingegriffen wird.
    loop = _make_loop(
        (_StaleTestEmitter("meter-1"),),
        (
            _stale_fault(
                "meter-1",
                "voltage_v",
                start_simulation_time=2000,
                duration_ms=1000,
                max_age_ms=100,
            ),
        ),
    )
    before = loop.tick().emitted_telemetry[0]  # now=1000, vor Start
    assert before.quality is Quality.VALID
    assert before.value == Decimal("1000")
    during = loop.tick().emitted_telemetry[0]  # now=2000, aktiv: Vorwert 1000, age 1000 > 100
    assert during.quality is Quality.STALE
    assert during.value == Decimal("1000")
    after = loop.tick().emitted_telemetry[0]  # now=3000, Fenster-Ende exklusiv → frisch
    assert after.quality is Quality.VALID
    assert after.value == Decimal("3000")


def test_no_prior_value_does_not_forward_and_marks_stale_only_when_aged() -> None:
    """ADR 0074 §2.3: Fault ab Tick 0, nie ein gueltiger Vorwert → keine
    Wert-Weiterlieferung. STALE nur, wenn der Punkt selbst zu alt ist
    (Referenz = eigene Sim-Zeit; ehrliche Grenze)."""
    # Kein Vorwert (Fault [0, ...) aktiv seit Tick 0). Zeitstempel laggt
    # 5000ms → (now - point.sim_time) = 5000 > max_age(1000) → STALE, aber
    # der Wert bleibt der eigene (nichts weiterzuliefern).
    loop = _make_loop(
        (_StaleTestEmitter("meter-1", lag_ms=5000),),
        (_stale_fault("meter-1", "voltage_v", start_simulation_time=0, max_age_ms=1000),),
    )
    point = loop.tick().emitted_telemetry[0]  # now=1000, point.sim_time=-4000
    assert point.quality is Quality.STALE
    assert point.value == Decimal("1000")  # eigener Wert, NICHT ersetzt


def test_no_prior_value_fresh_point_is_untouched() -> None:
    """ADR 0074 §2.3: Fault ab Tick 0 ohne Vorwert und ein frischer
    Punkt (Alter 0 ≤ max_age) bleibt unveraendert (kein Forwarding, kein
    STALE)."""
    loop = _make_loop(
        (_StaleTestEmitter("meter-1"),),
        (_stale_fault("meter-1", "voltage_v", start_simulation_time=0, max_age_ms=1000),),
    )
    point = loop.tick().emitted_telemetry[0]  # now=1000, frisch, kein Cache
    assert point.quality is Quality.VALID
    assert point.value == Decimal("1000")


def test_only_matching_metric_and_device_are_affected() -> None:
    """ADR 0074 §2.2: Match ist `(device_id, metric)` — andere Metrik /
    anderes Geraet bleibt unberuehrt. Alle drei Emitter rampen (Wert ==
    Sim-Zeit); nur der gefaultete Punkt traegt den eingefrorenen Vorwert
    (1000), die anderen den frischen Wert (2000)."""
    loop = _make_loop(
        (
            _StaleTestEmitter("meter-1", metric="voltage_v"),
            _StaleTestEmitter("meter-1", metric="current_a"),
            _StaleTestEmitter("meter-2", metric="voltage_v"),
        ),
        (_stale_fault("meter-1", "voltage_v", start_simulation_time=2000, max_age_ms=100),),
    )
    loop.tick()  # now=1000: cache meter-1/voltage_v = (1000, 1000)
    by_key = {(p.device_id, p.metric): p for p in loop.tick().emitted_telemetry}  # now=2000
    # meter-1/voltage_v: aktiv, Vorwert 1000 (eingefroren), age 1000 > 100 → STALE.
    assert by_key["meter-1", "voltage_v"].quality is Quality.STALE
    assert by_key["meter-1", "voltage_v"].value == Decimal("1000")
    # andere Metrik desselben Geraets: unberuehrt (frisch, 2000).
    assert by_key["meter-1", "current_a"].quality is Quality.VALID
    assert by_key["meter-1", "current_a"].value == Decimal("2000")
    # anderes Geraet, gleiche Metrik: unberuehrt (frisch, 2000).
    assert by_key["meter-2", "voltage_v"].quality is Quality.VALID
    assert by_key["meter-2", "voltage_v"].value == Decimal("2000")


def test_stale_data_raises_no_alarm() -> None:
    """ADR 0074 §2.5: `stale_data` hebt ueber alle Ticks **keinen** Alarm
    (Zwilling-Unterschied zu `nan_injection`)."""
    loop = _make_loop(
        (_StaleTestEmitter("meter-1", lag_ms=5000),),
        (_stale_fault("meter-1", "voltage_v", start_simulation_time=0, max_age_ms=1000),),
    )
    for _ in range(4):
        result = loop.tick()
        assert result.emitted_alarms == ()


# ---------------------------------------------------------------------------
# Severity-Override + Koexistenz mit der max_age-Stage
# ---------------------------------------------------------------------------


def test_severity_override_missing_dominates() -> None:
    """ADR 0074 §2.6: `STALE` (3) ersetzt nur niedrigere Severity —
    `MISSING` (7) wird weder wert- noch quality-ersetzt."""
    # MISSING-Punkt, laggt 5000ms, Fault aktiv seit Tick 0.
    loop = _make_loop(
        (_StaleTestEmitter("meter-1", quality=Quality.MISSING, lag_ms=5000),),
        (_stale_fault("meter-1", "voltage_v", start_simulation_time=0, max_age_ms=1000),),
    )
    point = loop.tick().emitted_telemetry[0]
    assert point.quality is Quality.MISSING
    assert point.value == Decimal("1000")  # eigener Wert unangetastet


def test_coexists_with_max_age_stage() -> None:
    """ADR 0074 §2.6 + ADR 0052: beide Stages setzen `STALE`,
    severity-idempotent. Die Quality-Fault-Stage laeuft VOR der
    `max_age`-Stage; ein `stale_data`-Fault liefert den eingefrorenen
    Wert (die `max_age`-Stage tastet den frischen Zeitstempel nicht an),
    ein nicht-gefaultetes lagging-Geraet wird von der `max_age`-Stage
    unabhaengig `STALE` markiert."""
    loop = _make_loop(
        (
            _StaleTestEmitter("meter-1"),  # frisch, gefaultet
            _StaleTestEmitter("meter-2", lag_ms=2000),  # laggt, NICHT gefaultet
        ),
        (_stale_fault("meter-1", "voltage_v", start_simulation_time=2000, max_age_ms=1000),),
        max_age_ms=1500,
    )
    loop.tick()  # now=1000: cache meter-1 (1000, 1000)
    by_device = {p.device_id: p for p in loop.tick().emitted_telemetry}  # now=2000
    # meter-1: Fault-Stage friert Wert (1000) ein, age 1000 == max_age(1000)
    # → NICHT stale; frischer Zeitstempel 2000 → max_age-Stage (1500) laesst
    # ihn ebenfalls in Ruhe.
    assert by_device["meter-1"].value == Decimal("1000")
    assert by_device["meter-1"].quality is Quality.VALID
    # meter-2: ungefaultet, laggt 2000ms > max_age(1500) → max_age-Stage STALE.
    assert by_device["meter-2"].quality is Quality.STALE


def test_fault_stale_survives_max_age_stage_idempotently() -> None:
    """ADR 0074 §2.6: markiert die Quality-Fault-Stage einen Punkt bereits
    `STALE` (Severity 3), laesst ihn die nachgelagerte `max_age`-Stage
    (`3 < 3` false) unangetastet — der eingefrorene Wert ueberlebt."""
    loop = _make_loop(
        (_StaleTestEmitter("meter-1"),),
        (_stale_fault("meter-1", "voltage_v", start_simulation_time=2000, max_age_ms=1000),),
        max_age_ms=500,
    )
    loop.tick()  # now=1000: cache (1000, 1000)
    loop.tick()  # now=2000: age 1000 == max_age → VALID (frozen 1000)
    point = loop.tick().emitted_telemetry[0]  # now=3000: age 2000 > 1000 → STALE
    assert point.quality is Quality.STALE
    assert point.value == Decimal("1000")  # eingefroren, von max_age-Stage nicht angetastet


# ---------------------------------------------------------------------------
# Builder-/Runtime-Konstruktion
# ---------------------------------------------------------------------------


def test_build_runtime_none_without_quality_faults() -> None:
    """ADR 0074 §2.7: ohne metrik-adressierten Quality-Fault → `None`."""
    physics_fault = ScenarioFault(
        start_simulation_time=0,
        duration_ms=1000,
        target="battery-1",
        type="cell_failure",
        payload={},
        recovery="auto",
    )
    assert build_quality_fault_runtime((physics_fault,)) is None
    runtime = build_quality_fault_runtime((_stale_fault("meter-1", "voltage_v"),))
    assert isinstance(runtime, QualityFaultRuntime)
    assert runtime.has_faults


def test_runtime_ignores_malformed_stale_fault() -> None:
    """ADR 0074 §2.1: der Runtime-Bau ueberspringt einen `stale_data`-
    Fault ohne gueltige `metric: str` bzw. `max_age_ms: int` (defensive
    Tiefe; der Validator faengt das produktiv vorher ab). `bool` wird als
    `int`-Subklasse abgelehnt."""
    no_metric = ScenarioFault(
        start_simulation_time=0,
        duration_ms=1000,
        target="meter-1",
        type="stale_data",
        payload={"max_age_ms": 1000},
        recovery="auto",
    )
    no_max_age = ScenarioFault(
        start_simulation_time=0,
        duration_ms=1000,
        target="meter-1",
        type="stale_data",
        payload={"metric": "voltage_v"},
        recovery="auto",
    )
    bool_max_age = ScenarioFault(
        start_simulation_time=0,
        duration_ms=1000,
        target="meter-1",
        type="stale_data",
        payload={"metric": "voltage_v", "max_age_ms": True},
        recovery="auto",
    )
    assert build_quality_fault_runtime((no_metric,)) is None
    assert build_quality_fault_runtime((no_max_age,)) is None
    assert build_quality_fault_runtime((bool_max_age,)) is None


def test_build_tick_loop_wires_stale_data_runtime() -> None:
    """ADR 0074 §2.2: `build_tick_loop` verdrahtet den
    `QualityFaultRuntime` aus einem `stale_data`-Szenario-Fault."""
    scenario = load_scenario(
        {
            "schema_version": "grid-gym.scenario.v1",
            "metadata": {"id": "slice-072", "name": "stale-wiring"},
            "simulation": {"tick_ms": 1000, "duration_s": 60, "seed": 42},
            "devices": [
                {"id": "load-1", "type": "load", "params": {"rated_power_kw": Decimal("100")}},
            ],
            "faults": [
                {
                    "start_simulation_time": 0,
                    "duration_ms": 5000,
                    "target": "load-1",
                    "type": "stale_data",
                    "payload": {"metric": "power_kw", "max_age_ms": 2000},
                    "recovery": "auto",
                },
            ],
        }
    ).scenario
    loop = build_tick_loop(
        scenario,
        run_id=_RUN_ID,
        clock=FakeClock(),
        random_root=FixedSeedRandom(seed=42),
        wiring=TickLoopWiring(),
    )
    assert loop._quality_fault_runtime is not None
    assert loop._quality_fault_runtime.has_faults


# ---------------------------------------------------------------------------
# Snapshot: opt-in Last-Value-Cache
# ---------------------------------------------------------------------------


def test_snapshot_omits_cache_key_when_empty() -> None:
    """ADR 0074 §2.7: ohne gecachten Vorwert (bzw. ohne Runtime) fehlt der
    Cache-Sub-Snapshot-Key → byte-identisch."""
    # None-Runtime.
    loop_none = TickLoop(
        run_id=_RUN_ID,
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        quality_fault_runtime=None,
    )
    assert _CACHE_KEY not in loop_none.snapshot()["sub_snapshots"]
    # Runtime mit stale_data-Fault, aber leerer Cache (kein Tick gelaufen).
    loop_empty = TickLoop(
        run_id=_RUN_ID,
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        quality_fault_runtime=build_quality_fault_runtime((_stale_fault("m", "v"),)),
    )
    assert _CACHE_KEY not in loop_empty.snapshot()["sub_snapshots"]


def test_snapshot_includes_cache_and_restores_into_reinjected_runtime() -> None:
    """ADR 0074 §2.3/§2.7: ein gecachter Vorwert erscheint opt-in im
    Snapshot und wird auf Resume in den re-injizierten Runtime
    zurueckgelesen (Cache ueberlebt den Roundtrip)."""
    faults = (_stale_fault("meter-1", "voltage_v", start_simulation_time=5000, max_age_ms=1000),)
    runtime = build_quality_fault_runtime(faults)
    assert runtime is not None
    # Vorwert cachen (kein aktiver Fault bei now=1000): direkt ueber die
    # Stage, wie der TickLoop sie ruft.
    runtime.apply_stage([_point("meter-1", "voltage_v", Decimal("41"), simulation_time=1000)], 1000)

    loop = TickLoop(
        run_id=_RUN_ID,
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        quality_fault_runtime=runtime,
    )
    snap = loop.snapshot()
    assert _CACHE_KEY in snap["sub_snapshots"]

    resumed_runtime = build_quality_fault_runtime(faults)
    resumed = TickLoop.from_snapshot(
        snap,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        quality_fault_runtime=resumed_runtime,
    )
    # Der re-injizierte Runtime traegt den Cache-Eintrag wieder.
    assert resumed._quality_fault_runtime is resumed_runtime
    assert resumed_runtime._last_valid == {("meter-1", "voltage_v"): (Decimal("41"), 1000)}


def test_resume_mid_window_keeps_forwarding_last_valid_value() -> None:
    """ADR 0074 §2.3 (DoD): Resume mitten im Stale-Fenster verliert den
    letzten gueltigen Wert nicht — nach `restore_cache` liefert die Stage
    ihn weiter (Kontrakt-Ebene, geraeteunabhaengig)."""
    faults = (_stale_fault("meter-1", "voltage_v", start_simulation_time=0, max_age_ms=1000),)
    original = build_quality_fault_runtime(faults)
    assert original is not None
    # Vorwert cachen (Fault noch inaktiv gedacht — hier direkt via Stage
    # mit einem nicht-aktiven Zeitpunkt: der Vorwert ist der Cache-Inhalt).
    original._last_valid["meter-1", "voltage_v"] = (Decimal("41"), 1000)
    snap = original.cache_snapshot()

    resumed = build_quality_fault_runtime(faults)
    assert resumed is not None
    resumed.restore_cache(snap)
    # Mitten im Fenster (now=1500), frischer Punkt (Wert 99) → Vorwert 41
    # wird weitergeliefert; age 500 ≤ 1000 → VALID.
    rewritten, alarms = resumed.apply_stage(
        [_point("meter-1", "voltage_v", Decimal("99"), simulation_time=1500)], 1500
    )
    assert alarms == []
    assert rewritten[0].value == Decimal("41")
    assert rewritten[0].quality is Quality.VALID


def test_cache_snapshot_none_when_empty() -> None:
    """ADR 0074 §2.7: `cache_snapshot()` ist `None` bei leerem Cache."""
    runtime = build_quality_fault_runtime((_stale_fault("m", "v"),))
    assert runtime is not None
    assert runtime.cache_snapshot() is None


def test_restore_cache_none_is_noop() -> None:
    """ADR 0074 §2.3: `restore_cache(None)` (kein Sub-Snapshot-Key) ist
    ein no-op."""
    runtime = build_quality_fault_runtime((_stale_fault("m", "v"),))
    assert runtime is not None
    runtime.restore_cache(None)
    assert runtime.cache_snapshot() is None


def test_restore_cache_rejects_version_mismatch() -> None:
    """ADR 0074 §2.7: ein fremder Cache-Snapshot-`version` → typisierter
    `VersionError`."""
    runtime = build_quality_fault_runtime((_stale_fault("m", "v"),))
    assert runtime is not None
    with pytest.raises(VersionError):
        runtime.restore_cache({"version": 999, "entries": ()})


def test_restore_cache_rejects_wrong_entries_type() -> None:
    """ADR 0074 §2.7: `entries` kein list/tuple → typisierter
    `WrongTypeError`."""
    runtime = build_quality_fault_runtime((_stale_fault("m", "v"),))
    assert runtime is not None
    with pytest.raises(WrongTypeError):
        runtime.restore_cache({"version": 1, "entries": "not-a-list"})


def test_cache_snapshot_roundtrips_multiple_entries_sorted() -> None:
    """ADR 0074 §2.3: `cache_snapshot()`/`restore_cache()` sind Roundtrip-
    stabil und deterministisch nach `(device_id, metric)` sortiert."""
    runtime = build_quality_fault_runtime((_stale_fault("m-b", "v"), _stale_fault("m-a", "v")))
    assert runtime is not None
    runtime._last_valid["m-b", "v"] = (Decimal("2"), 2000)
    runtime._last_valid["m-a", "v"] = (Decimal("1"), 1000)
    snap = runtime.cache_snapshot()
    assert snap is not None
    entries = snap["entries"]
    assert [e["device_id"] for e in entries] == ["m-a", "m-b"]  # sortiert

    restored = build_quality_fault_runtime((_stale_fault("m-a", "v"),))
    assert restored is not None
    restored.restore_cache(snap)
    assert restored._last_valid == {
        ("m-a", "v"): (Decimal("1"), 1000),
        ("m-b", "v"): (Decimal("2"), 2000),
    }


# ---------------------------------------------------------------------------
# Review-Folge (Slice 072): Cache-Scoping, NaN-Koexistenz, Severity-Gate
# ---------------------------------------------------------------------------


def test_cache_only_holds_stale_target_pairs() -> None:
    """ADR 0074 §2.7 (Review MEDIUM-1): der Last-Value-Cache wird NUR fuer
    die tatsaechlich adressierten `stale_data`-Ziel-`(device, metric)`-Paare
    gefuehrt — nicht fuer jeden VALID-Punkt eines Szenarios mit irgendeinem
    `stale_data`-Fault (kein Snapshot-Bloat)."""
    runtime = build_quality_fault_runtime(
        (_stale_fault("m1", "v", start_simulation_time=5000, max_age_ms=1000),)
    )
    assert runtime is not None
    # Fault inaktiv bei now=1000; nur `m1/v` ist ein stale_data-Ziel.
    runtime.apply_stage(
        [
            _point("m1", "v", Decimal("1"), simulation_time=1000),
            _point("m1", "other", Decimal("2"), simulation_time=1000),
            _point("m2", "v", Decimal("3"), simulation_time=1000),
        ],
        1000,
    )
    assert runtime._last_valid == {("m1", "v"): (Decimal("1"), 1000)}


def test_nan_and_stale_on_same_key_nan_wins() -> None:
    """ADR 0074 §2.6: laeuft auf demselben `(device, metric)` ein aktiver
    `nan_injection`- UND ein aktiver `stale_data`-Fault, dominiert `NAN`
    (6) ueber `STALE` (3) — Sentinel `0` + `quality=nan`, kein STALE."""
    faults = (
        _nan_fault("meter-1", "voltage_v", start_simulation_time=2000, duration_ms=8000),
        _stale_fault("meter-1", "voltage_v", start_simulation_time=2000, max_age_ms=1000),
    )
    loop = _make_loop((_StaleTestEmitter("meter-1"),), faults)
    loop.tick()  # now=1000: beide inaktiv → cache (1000, 1000)
    point = loop.tick().emitted_telemetry[0]  # now=2000: beide aktiv
    assert point.quality is Quality.NAN
    assert point.value == Decimal("0")  # NaN-Sentinel, NICHT der Stale-Vorwert 1000


def test_stale_does_not_forward_to_worse_quality_point_with_cache() -> None:
    """ADR 0074 §2.6 (Review LOW-3/4): ein Live-Punkt mit **schlechterer**
    Quality (INVALID, Severity 5 ≥ STALE 3) wird trotz gefuelltem Cache
    **nicht** wert-ersetzt — der schwerere Befund darf nicht durch einen
    eingefrorenen Vorwert maskiert werden."""
    runtime = build_quality_fault_runtime(
        (_stale_fault("m", "v", start_simulation_time=0, max_age_ms=1000),)
    )
    assert runtime is not None
    runtime._last_valid["m", "v"] = (Decimal("41"), 1000)
    rewritten, _ = runtime.apply_stage(
        [_point("m", "v", Decimal("99"), simulation_time=1500, quality=Quality.INVALID)], 1500
    )
    assert rewritten[0].value == Decimal("99")  # eigener Wert, NICHT der Vorwert 41
    assert rewritten[0].quality is Quality.INVALID


def test_nan_only_run_omits_cache_key() -> None:
    """ADR 0074 §2.7 (Review LOW-5): ein Lauf mit ausschliesslich
    `nan_injection` (kein `stale_data`) baut keinen Cache auf →
    `cache_snapshot()` ist `None` → kein Snapshot-Key (byte-identisch zur
    Slice-A-Foundation, direkt gepinnt)."""
    runtime = build_quality_fault_runtime((_nan_fault("m", "v", duration_ms=5000),))
    assert runtime is not None
    runtime.apply_stage([_point("m", "v", Decimal("5"), simulation_time=1000)], 1000)
    assert runtime.cache_snapshot() is None


# ---------------------------------------------------------------------------
# Determinismus
# ---------------------------------------------------------------------------


@pytest.mark.determinism
def test_two_identical_runs_produce_identical_streams() -> None:
    """ADR 0074 §2.6: nur Sim-Zeit (AC-NO-TIME) — zwei identisch
    konfigurierte Laeufe emittieren ueber mehrere Ticks identische
    Telemetrie-Streams."""

    def _run() -> tuple[TelemetryPoint, ...]:
        loop = _make_loop(
            (_StaleTestEmitter("meter-1"),),
            (_stale_fault("meter-1", "voltage_v", start_simulation_time=2000, max_age_ms=1000),),
        )
        telemetry: list[TelemetryPoint] = []
        for _ in range(5):
            telemetry.extend(loop.tick().emitted_telemetry)
        return tuple(telemetry)

    assert _run() == _run()
    stream = _run()
    assert any(p.quality is Quality.STALE for p in stream)
    assert any(p.value == Decimal("1000") for p in stream)  # Vorwert weitergeliefert
