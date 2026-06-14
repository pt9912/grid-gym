"""M8-Welle-2a End-to-End-Smoke fuer das EV-Charger-Demo-Szenario
(GG-DEV-015, ADR 0055).

Pinnt die End-to-End-Verdrahtung des neuen SOLLTE-Geraets:

1. **Pipeline**: YAML → `str→Decimal`-Coercion (inkl. der neuen
   `battery_capacity_kwh`/`cv_phase_start_soc`/`initial_soc`-Felder)
   → `load_scenario` → `build_tick_loop` mit
   `_DEVICE_FACTORIES["ev_charger"]`.
2. **Determinismus** (ADR 0055 §2.8): zwei Laeufe mit gleichem Seed
   liefern byte-identische `TickResult.emitted_telemetry`.
3. **Telemetrie-Surface**: der EV emittiert seine 7 Metriken/Tick.
4. **Idle-Verhalten**: ohne Command idlet der EV bei `power_kw = 0`,
   der SoC bleibt auf `initial_soc` konstant (kein spontanes Laden).

Lade-/V2G-/CC-CV-/Fault-Dynamik ist im Unit-Test gepinnt
(`tests/unit/.../ev_charger/`); ein produktiver scenario-getriebener
EV-Fault-Engine ist M-Folge-Material (ADR 0055 §6 / §4).
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.scenario.loader import LoadedScenario, build_tick_loop

from tests.integration._constants import (
    EV_CHARGER_DEMO_SCENARIO_PATH,
    EV_CHARGER_DEMO_TICKS,
)
from tests.integration._yaml_scenario_loader import load_yaml_scenario
from tests.unit.hexagon.ports.driven._fakes import FakeClock

_EV_METRICS = [
    "charged_kwh",
    "connection_loss",
    "discharged_kwh",
    "plug_state",
    "power_kw",
    "soc",
    "voltage_v",
]


def _drive(loaded: LoadedScenario, *, ticks: int) -> tuple[TelemetryPoint, ...]:
    loop = build_tick_loop(
        loaded.scenario,
        run_id="welle-2a-ev-demo",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed),
    )
    collected: list[TelemetryPoint] = []
    for _ in range(ticks):
        collected.extend(loop.tick().emitted_telemetry)
    return tuple(collected)


def test_ev_charger_demo_loads_and_runs() -> None:
    """Pipeline-Smoke: das EV-Charger-Szenario laedt (inkl. der neuen
    Decimal-Param-Coercion) und faehrt durch den TickLoop."""
    loaded = load_yaml_scenario(EV_CHARGER_DEMO_SCENARIO_PATH)
    ev_device = next(d for d in loaded.scenario.devices if d.id == "ev-1")
    assert ev_device.type == "ev_charger"
    assert ev_device.params["battery_capacity_kwh"] == Decimal("60")
    assert ev_device.params["initial_plug_state"] == "plugged"
    telemetry = _drive(loaded, ticks=EV_CHARGER_DEMO_TICKS)
    assert len(telemetry) > 0


def test_ev_charger_demo_telemetry_byte_identical_across_runs() -> None:
    """ADR 0055 §2.8 Determinismus: gleicher Seed → byte-identisch."""
    loaded = load_yaml_scenario(EV_CHARGER_DEMO_SCENARIO_PATH)
    assert _drive(loaded, ticks=EV_CHARGER_DEMO_TICKS) == _drive(
        loaded, ticks=EV_CHARGER_DEMO_TICKS
    )


def test_ev_charger_demo_emits_seven_metrics_per_tick() -> None:
    """ADR 0055 §2.8: der EV emittiert genau seine 7 Metriken/Tick."""
    loaded = load_yaml_scenario(EV_CHARGER_DEMO_SCENARIO_PATH)
    telemetry = _drive(loaded, ticks=EV_CHARGER_DEMO_TICKS)
    ev_points = [p for p in telemetry if p.device_id == "ev-1"]
    assert sorted({p.metric for p in ev_points}) == _EV_METRICS
    assert len(ev_points) == EV_CHARGER_DEMO_TICKS * len(_EV_METRICS)


def test_ev_charger_demo_idle_keeps_soc_and_plug_constant() -> None:
    """Ohne Command idlet der EV: `power_kw = 0`, SoC konstant auf
    `initial_soc = 0.2`, `plug_state = plugged`."""
    loaded = load_yaml_scenario(EV_CHARGER_DEMO_SCENARIO_PATH)
    telemetry = [p for p in _drive(loaded, ticks=EV_CHARGER_DEMO_TICKS) if p.device_id == "ev-1"]
    soc = [p.value for p in telemetry if p.metric == "soc"]
    power = [p.value for p in telemetry if p.metric == "power_kw"]
    plug = [p.value for p in telemetry if p.metric == "plug_state"]
    assert all(v == Decimal("0.200000") for v in soc)
    assert all(v == Decimal("0.000000") for v in power)
    assert all(v == Decimal("1.000000") for v in plug)
