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

**SmartMeter-Constraint** (Welle-6c-Review M-1, ADR 0018 §2.3):
SmartMeter liest die Telemetry seiner Quell-Devices innerhalb
**desselben Ticks** und ist deswegen lese-Reihenfolge-abhaengig.
Wenn SmartMeter VOR seinen Quellen in der Iteration steht, liest
er Stale-Tick-(t-1)-Werte; die Aggregation ist dann nicht mehr
identisch zur Konstellation „SmartMeter LAST". Welle 6c klammert
das aus, indem die Permutation **nur** die Nicht-Aggregator-
Devices permutiert (pv/load/battery/grid_connection) und der
SmartMeter konsistent am Ende der Sequenz haengt — das spiegelt
die MVP-Demo-Konvention `mvp_demo.yaml` und pinnt die
Permutation-Invariante fuer die produktive Topologie.

Hypothesis @given mit `st.permutations(non-aggregator devices)`
+ 50 Beispielen + 20 Ticks; das deckt alle 4!=24 Permutationen
der 4 Nicht-Aggregator-Geraete statistisch ueberzeugend ab
(Welle-6c-Review L-5).
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

import pytest
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

# Slice 054: determinism-Sensor-Traeger fuer `make test-determinism`.
pytestmark = pytest.mark.determinism


_TICKS: int = 20


def _non_aggregator_devices() -> tuple[ScenarioDevice, ...]:
    """Devices ohne Inter-Tick-Read-Abhaengigkeit (siehe Modul-
    Docstring M-1: SmartMeter ist ausgeklammert)."""
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


def _smart_meter_device() -> ScenarioDevice:
    """Aggregator-Device, das **immer** am Ende der Iteration
    stehen muss (siehe Modul-Docstring M-1). `aggregate_device_ids`
    in alphabetischer Reihenfolge (canonical, ADR 0018 §2.2)."""
    return ScenarioDevice(
        id="meter-1",
        type="smart_meter",
        params={
            "aggregate_device_ids": ["battery-1", "load-1", "pv-1"],
            "aggregate_metric_name": "power_kw",
        },
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
    permutation=st.permutations(list(_non_aggregator_devices())),
    seed=st.integers(min_value=0, max_value=2**32 - 1),
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_scenario_device_permutation_yields_identical_per_device_telemetry(
    permutation: Sequence[ScenarioDevice], seed: int
) -> None:
    """ADR 0021 §2.2 / §2.9 — Determinismus-Pflicht: gleicher Seed
    + gleiche Nicht-Aggregator-Geraetemenge in beliebiger Reihenfolge
    (mit SmartMeter konstant am Ende) ⇒ pro Geraet byte-identische
    Telemetry-Sequenz inkl. SmartMeter-Aggregat (`aggregated_power_kw`)."""
    smart_meter = _smart_meter_device()
    canonical = (*_non_aggregator_devices(), smart_meter)
    permuted = (*permutation, smart_meter)
    telemetry_canonical = _drive(canonical, seed)
    telemetry_permuted = _drive(permuted, seed)
    assert _group_by_device(telemetry_canonical) == _group_by_device(telemetry_permuted)
