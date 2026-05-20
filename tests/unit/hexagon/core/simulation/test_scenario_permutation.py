"""M2-Welle-6c Unit-Property-Test (ScenarioDevice-Permutation).

Spiegelt das Welle-3-Scheduler-Permutation-Pattern
(`test_scheduler.py::test_permutation_of_inputs_yields_identical_pop_order`):
zwei `TickLoop`-Instanzen mit derselben Geraetemenge in
unterschiedlicher Eingabe-Reihenfolge muessen byte-identische
**per-Device**-`TelemetryPoint`-Sequenzen emittieren.

Per-Device statt globaler Tuple-Vergleich: `emitted_telemetry`
ist explizit nach Device-Iterations-Reihenfolge x Per-Device-
Sequence sortiert (`tick_loop.py:16`), also AENDERT sich die
Tuple-Position eines Records mit der Eingabe-Permutation. Die
Invariante ist „pro Geraet identische Telemetry" — diese
verifiziert die Determinismus-Pflicht aus ADR 0021 §2.2 / §2.9.

Hypothesis @given mit `st.permutations(_devices())` + 25
Beispielen + 20 Ticks ist konservativ; das exerziert den
TickLoop-Komplettzyklus inkl. Vor-Tick-Block + GridConnection-
Auto-Schluss.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

import hypothesis.strategies as st
from hypothesis import HealthCheck, given, settings

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.scenario import (
    Scenario,
    ScenarioDevice,
    ScenarioMetadata,
    ScenarioSimulation,
)
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.grid_model import GridModelConfig
from grid_gym.hexagon.core.scenario.loader import build_tick_loop
from tests.unit.hexagon.ports.driven._fakes import FakeClock


_TICKS: int = 20


def _devices() -> tuple[ScenarioDevice, ...]:
    return (
        ScenarioDevice(
            id="pv-1",
            type="pv",
            params={"rated_power_kw": Decimal("500")},
        ),
        ScenarioDevice(
            id="load-1",
            type="load",
            params={"rated_power_kw": Decimal("300")},
        ),
        ScenarioDevice(
            id="battery-1",
            type="battery",
            params={
                "capacity_kwh": Decimal("100"),
                "initial_soc_pct": Decimal("50"),
                "min_soc_pct": Decimal("0"),
                "max_soc_pct": Decimal("100"),
                "max_charge_kw": Decimal("50"),
                "max_discharge_kw": Decimal("50"),
                "charge_efficiency": Decimal("1"),
                "discharge_efficiency": Decimal("1"),
                "ramp_kw_per_s": Decimal("100"),
            },
        ),
        ScenarioDevice(
            id="grid-1",
            type="grid_connection",
            params={
                "nominal_voltage_v": Decimal("400"),
                "max_import_kw": Decimal("1000"),
                "max_export_kw": Decimal("1000"),
            },
        ),
    )


def _grid_model_config() -> GridModelConfig:
    return GridModelConfig(
        nominal_frequency_hz=Decimal("50"),
        frequency_sensitivity_hz_per_kw=Decimal("0.001"),
        frequency_clamp_min_hz=Decimal("45"),
        frequency_clamp_max_hz=Decimal("55"),
        nominal_voltage_v=Decimal("400"),
        voltage_sensitivity_v_per_kw=Decimal("0.1"),
        voltage_clamp_min_v=Decimal("280"),
        voltage_clamp_max_v=Decimal("520"),
    )


def _scenario(devices: tuple[ScenarioDevice, ...], seed: int) -> Scenario:
    return Scenario(
        schema_version="grid-gym.scenario.v1",
        metadata=ScenarioMetadata(id="welle-6c-perm", name="Welle 6c Permutation"),
        simulation=ScenarioSimulation(tick_ms=1000, duration_s=_TICKS, seed=seed),
        devices=devices,
        events=(),
        replay=None,
        faults=(),
        grid_model_config=_grid_model_config(),
        load_events=(),
        load_profiles=(),
    )


def _drive(devices: tuple[ScenarioDevice, ...], seed: int) -> tuple[TelemetryPoint, ...]:
    loop = build_tick_loop(
        _scenario(devices, seed),
        run_id="perm",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=seed),
    )
    out: list[TelemetryPoint] = []
    for _ in range(_TICKS):
        out.extend(loop.tick().emitted_telemetry)
    return tuple(out)


def _group_by_device(
    telemetry: tuple[TelemetryPoint, ...],
) -> dict[str, tuple[TelemetryPoint, ...]]:
    groups: dict[str, list[TelemetryPoint]] = {}
    for point in telemetry:
        groups.setdefault(point.device_id, []).append(point)
    return {device_id: tuple(points) for device_id, points in groups.items()}


@given(
    permutation=st.permutations(list(_devices())),
    seed=st.integers(min_value=0, max_value=2**32 - 1),
)
@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_scenario_device_permutation_yields_identical_per_device_telemetry(
    permutation: Sequence[ScenarioDevice], seed: int
) -> None:
    """ADR 0021 §2.2 / §2.9 — Determinismus-Pflicht: gleicher Seed
    + gleiche Geraetemenge in beliebiger Reihenfolge ⇒ pro Geraet
    byte-identische Telemetry-Sequenz."""
    canonical = _devices()
    permuted = tuple(permutation)
    telemetry_canonical = _drive(canonical, seed)
    telemetry_permuted = _drive(permuted, seed)
    assert _group_by_device(telemetry_canonical) == _group_by_device(telemetry_permuted)
