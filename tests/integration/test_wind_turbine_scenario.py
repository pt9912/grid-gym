"""M8-Welle-2c End-to-End-Smoke fuer das Wind-Turbine-Demo-Szenario
(GG-DEV-017, ADR 0057).

Pinnt die End-to-End-Verdrahtung des neuen SOLLTE-Geraets:

1. **Pipeline**: YAML → `str→Decimal`-Coercion (inkl. der neuen
   `cut_in/rated/cut_out/min/max`-Felder) → `load_scenario` →
   `build_tick_loop` mit `_DEVICE_FACTORIES["wind_turbine"]` (Sub-Stream
   `random_root.sub_port("wt-1")`).
2. **Determinismus** (ADR 0057 §2.6): zwei Laeufe mit gleichem Seed
   liefern byte-identische `TickResult.emitted_telemetry` — obwohl Wind
   stochastisch zieht (seeded `RandomPort`).
3. **Telemetrie-Surface**: 3 Metriken/Tick.
4. **Erzeugung + Bounds**: anders als die EV-/Transformer-Smokes idlet
   Wind nicht — `power_kw ∈ [0, rated]`, `generated_kwh` monoton und am
   Ende > 0.
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.scenario.loader import LoadedScenario, build_tick_loop

from tests.integration._constants import (
    WIND_TURBINE_DEMO_SCENARIO_PATH,
    WIND_TURBINE_DEMO_TICKS,
)
from tests.integration._yaml_scenario_loader import load_yaml_scenario
from tests.unit.hexagon.ports.driven._fakes import FakeClock

_WT_METRICS = ["generated_kwh", "power_kw", "wind_speed_ms"]
_RATED_POWER_KW = Decimal("2000")


def _drive(loaded: LoadedScenario, *, ticks: int) -> tuple[TelemetryPoint, ...]:
    loop = build_tick_loop(
        loaded.scenario,
        run_id="welle-2c-wind-demo",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed),
    )
    collected: list[TelemetryPoint] = []
    for _ in range(ticks):
        collected.extend(loop.tick().emitted_telemetry)
    return tuple(collected)


def test_wind_turbine_demo_loads_and_runs() -> None:
    loaded = load_yaml_scenario(WIND_TURBINE_DEMO_SCENARIO_PATH)
    wt = next(d for d in loaded.scenario.devices if d.id == "wt-1")
    assert wt.type == "wind_turbine"
    assert wt.params["cut_in_speed_ms"] == Decimal("2")
    assert wt.params["max_wind_speed_ms"] == Decimal("20")
    assert len(_drive(loaded, ticks=WIND_TURBINE_DEMO_TICKS)) > 0


def test_wind_turbine_demo_telemetry_byte_identical_across_runs() -> None:
    """ADR 0057 §2.6 Determinismus: gleicher Seed → byte-identisch,
    trotz stochastischer Ziehung."""
    loaded = load_yaml_scenario(WIND_TURBINE_DEMO_SCENARIO_PATH)
    assert _drive(loaded, ticks=WIND_TURBINE_DEMO_TICKS) == _drive(
        loaded, ticks=WIND_TURBINE_DEMO_TICKS
    )


def test_wind_turbine_demo_emits_three_metrics_per_tick() -> None:
    loaded = load_yaml_scenario(WIND_TURBINE_DEMO_SCENARIO_PATH)
    telemetry = _drive(loaded, ticks=WIND_TURBINE_DEMO_TICKS)
    wt_points = [p for p in telemetry if p.device_id == "wt-1"]
    assert sorted({p.metric for p in wt_points}) == _WT_METRICS
    assert len(wt_points) == WIND_TURBINE_DEMO_TICKS * len(_WT_METRICS)


def test_wind_turbine_demo_generates_within_bounds() -> None:
    """Wind erzeugt variabel: power_kw ∈ [0, rated], generated_kwh
    monoton nicht-fallend und am Ende > 0."""
    loaded = load_yaml_scenario(WIND_TURBINE_DEMO_SCENARIO_PATH)
    telemetry = [p for p in _drive(loaded, ticks=WIND_TURBINE_DEMO_TICKS) if p.device_id == "wt-1"]
    powers = [p.value for p in telemetry if p.metric == "power_kw"]
    generated = [p.value for p in telemetry if p.metric == "generated_kwh"]
    assert all(Decimal("0") <= v <= _RATED_POWER_KW for v in powers)
    assert generated == sorted(generated)  # monoton
    assert generated[-1] > Decimal("0")
