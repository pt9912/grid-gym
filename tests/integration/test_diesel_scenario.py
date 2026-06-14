"""M8-Welle-2d End-to-End-Smoke fuer das Diesel-Generator-Demo-Szenario
(GG-DEV-018, ADR 0058).

Pinnt die End-to-End-Verdrahtung des neuen SOLLTE-Geraets:

1. **Pipeline**: YAML → `str→Decimal`-Coercion (inkl. der neuen
   `max_power_kw`/`min_start_power_kw`/`min_stop_power_kw`/
   `fuel_capacity_l`/`initial_fuel_l`/`fuel_per_kwh_l`-Felder) →
   `load_scenario` → `build_tick_loop` mit
   `_DEVICE_FACTORIES["diesel_generator"]`.
2. **Determinismus** (ADR 0058 §2.8): zwei Laeufe mit gleichem Seed
   liefern byte-identische `TickResult.emitted_telemetry`.
3. **Telemetrie-Surface**: 5 Metriken/Tick.
4. **Idle-Verhalten**: ohne Command bleibt der Genset STOPPED
   (`running = 0`, `power_kw = 0`, Kraftstoff konstant auf `initial_fuel_l`).

Hysterese-/Ramp-/Kraftstoff-/Fault-Dynamik ist im Unit-Test gepinnt
(`tests/unit/.../diesel_generator/`).
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.scenario.loader import LoadedScenario, build_tick_loop

from tests.integration._constants import DIESEL_DEMO_SCENARIO_PATH, DIESEL_DEMO_TICKS
from tests.integration._yaml_scenario_loader import load_yaml_scenario
from tests.unit.hexagon.ports.driven._fakes import FakeClock

_DG_METRICS = ["fuel_l", "generated_kwh", "genset_fault", "power_kw", "running"]


def _drive(loaded: LoadedScenario, *, ticks: int) -> tuple[TelemetryPoint, ...]:
    loop = build_tick_loop(
        loaded.scenario,
        run_id="welle-2d-diesel-demo",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed),
    )
    collected: list[TelemetryPoint] = []
    for _ in range(ticks):
        collected.extend(loop.tick().emitted_telemetry)
    return tuple(collected)


def test_diesel_demo_loads_and_runs() -> None:
    loaded = load_yaml_scenario(DIESEL_DEMO_SCENARIO_PATH)
    dg = next(d for d in loaded.scenario.devices if d.id == "dg-1")
    assert dg.type == "diesel_generator"
    assert dg.params["fuel_capacity_l"] == Decimal("500")
    assert dg.params["min_start_power_kw"] == Decimal("20")
    assert len(_drive(loaded, ticks=DIESEL_DEMO_TICKS)) > 0


def test_diesel_demo_telemetry_byte_identical_across_runs() -> None:
    """ADR 0058 §2.8 Determinismus: gleicher Seed → byte-identisch."""
    loaded = load_yaml_scenario(DIESEL_DEMO_SCENARIO_PATH)
    assert _drive(loaded, ticks=DIESEL_DEMO_TICKS) == _drive(loaded, ticks=DIESEL_DEMO_TICKS)


def test_diesel_demo_emits_five_metrics_per_tick() -> None:
    loaded = load_yaml_scenario(DIESEL_DEMO_SCENARIO_PATH)
    telemetry = _drive(loaded, ticks=DIESEL_DEMO_TICKS)
    dg_points = [p for p in telemetry if p.device_id == "dg-1"]
    assert sorted({p.metric for p in dg_points}) == _DG_METRICS
    assert len(dg_points) == DIESEL_DEMO_TICKS * len(_DG_METRICS)


def test_diesel_demo_idle_stays_stopped() -> None:
    """Ohne Command bleibt der Genset STOPPED: power 0, running 0,
    Kraftstoff konstant auf initial_fuel_l = 500."""
    loaded = load_yaml_scenario(DIESEL_DEMO_SCENARIO_PATH)
    telemetry = [p for p in _drive(loaded, ticks=DIESEL_DEMO_TICKS) if p.device_id == "dg-1"]
    power = [p.value for p in telemetry if p.metric == "power_kw"]
    running = [p.value for p in telemetry if p.metric == "running"]
    fuel = [p.value for p in telemetry if p.metric == "fuel_l"]
    assert all(v == Decimal("0.000000") for v in power)
    assert all(v == Decimal("0.000000") for v in running)
    assert all(v == Decimal("500.000000") for v in fuel)
