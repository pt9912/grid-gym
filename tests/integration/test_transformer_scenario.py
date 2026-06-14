"""M8-Welle-2b End-to-End-Smoke fuer das Transformer-Demo-Szenario
(GG-DEV-016, ADR 0056).

Pinnt die End-to-End-Verdrahtung des neuen SOLLTE-Geraets:

1. **Pipeline**: YAML → `str→Decimal`-Coercion (inkl. der neuen
   `primary_voltage_v`/`turns_ratio`/`no_load_loss_kw`/`load_loss_kw`-
   Felder) → `load_scenario` → `build_tick_loop` mit
   `_DEVICE_FACTORIES["transformer"]`.
2. **Determinismus** (ADR 0056 §2.7): zwei Laeufe mit gleichem Seed
   liefern byte-identische `TickResult.emitted_telemetry`.
3. **Telemetrie-Surface**: der Transformer emittiert seine 7 Metriken/Tick.
4. **Idle-Verhalten**: ohne Command idlet der Transformer bei
   `primary_power_kw = 0` (nur Eisen-/Leerlaufverlust), `throughput_kwh`
   bleibt 0.

Verlust-/Saettigungs-/Fault-Dynamik ist im Unit-Test gepinnt
(`tests/unit/.../transformer/`).
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.scenario.loader import LoadedScenario, build_tick_loop

from tests.integration._constants import (
    TRANSFORMER_DEMO_SCENARIO_PATH,
    TRANSFORMER_DEMO_TICKS,
)
from tests.integration._yaml_scenario_loader import load_yaml_scenario
from tests.unit.hexagon.ports.driven._fakes import FakeClock

_TR_METRICS = [
    "efficiency",
    "loss_kw",
    "primary_power_kw",
    "secondary_power_kw",
    "secondary_voltage_v",
    "throughput_kwh",
    "winding_fault",
]


def _drive(loaded: LoadedScenario, *, ticks: int) -> tuple[TelemetryPoint, ...]:
    loop = build_tick_loop(
        loaded.scenario,
        run_id="welle-2b-transformer-demo",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed),
    )
    collected: list[TelemetryPoint] = []
    for _ in range(ticks):
        collected.extend(loop.tick().emitted_telemetry)
    return tuple(collected)


def test_transformer_demo_loads_and_runs() -> None:
    """Pipeline-Smoke: das Transformer-Szenario laedt (inkl. der neuen
    Decimal-Param-Coercion) und faehrt durch den TickLoop."""
    loaded = load_yaml_scenario(TRANSFORMER_DEMO_SCENARIO_PATH)
    tr_device = next(d for d in loaded.scenario.devices if d.id == "tr-1")
    assert tr_device.type == "transformer"
    assert tr_device.params["turns_ratio"] == Decimal("50")
    assert tr_device.params["no_load_loss_kw"] == Decimal("5")
    assert len(_drive(loaded, ticks=TRANSFORMER_DEMO_TICKS)) > 0


def test_transformer_demo_telemetry_byte_identical_across_runs() -> None:
    """ADR 0056 §2.7 Determinismus: gleicher Seed → byte-identisch."""
    loaded = load_yaml_scenario(TRANSFORMER_DEMO_SCENARIO_PATH)
    assert _drive(loaded, ticks=TRANSFORMER_DEMO_TICKS) == _drive(
        loaded, ticks=TRANSFORMER_DEMO_TICKS
    )


def test_transformer_demo_emits_seven_metrics_per_tick() -> None:
    """ADR 0056 §2.7: der Transformer emittiert genau seine 7 Metriken/Tick."""
    loaded = load_yaml_scenario(TRANSFORMER_DEMO_SCENARIO_PATH)
    telemetry = _drive(loaded, ticks=TRANSFORMER_DEMO_TICKS)
    tr_points = [p for p in telemetry if p.device_id == "tr-1"]
    assert sorted({p.metric for p in tr_points}) == _TR_METRICS
    assert len(tr_points) == TRANSFORMER_DEMO_TICKS * len(_TR_METRICS)


def test_transformer_demo_idle_keeps_primary_zero() -> None:
    """Ohne Command idlet der Transformer: `primary_power_kw = 0`,
    `throughput_kwh = 0`, nur Eisenverlust (`loss_kw = no_load_loss_kw`)."""
    loaded = load_yaml_scenario(TRANSFORMER_DEMO_SCENARIO_PATH)
    telemetry = [p for p in _drive(loaded, ticks=TRANSFORMER_DEMO_TICKS) if p.device_id == "tr-1"]
    primary = [p.value for p in telemetry if p.metric == "primary_power_kw"]
    throughput = [p.value for p in telemetry if p.metric == "throughput_kwh"]
    loss = [p.value for p in telemetry if p.metric == "loss_kw"]
    assert all(v == Decimal("0.000000") for v in primary)
    assert all(v == Decimal("0.000000") for v in throughput)
    assert all(v == Decimal("5.000000") for v in loss)
