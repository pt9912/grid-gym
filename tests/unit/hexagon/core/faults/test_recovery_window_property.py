"""Hypothesis-Property-Tests fuer Recovery-Window-Boundary
und Per-Fault-Determinismus (M3 Welle 2 Item 9, ADR 0025 §2.3
+ §2.4).

Pinnt:
- **Half-open `[start, end)`**: BatteryFaultAdapter aktiviert den
  Fault genau in `[start, start+duration)`-Ticks, nicht davor
  oder danach. Property-Test mit `@given(start_ms, duration_ms,
  probe_offset)`.
- **Per-Fault-Determinismus**: gleicher Seed + identische
  Fault-Sequenz erzeugen byte-identische Telemetry. Spiegelt
  M2-Welle-6c-Permutations-Pattern fuer den Fault-Pfad.
"""

from __future__ import annotations

from decimal import Decimal

import hypothesis.strategies as st
from hypothesis import HealthCheck, given, settings

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice, ScenarioFault
from grid_gym.hexagon.core.faults import BatteryFaultAdapter, GridFaultAdapter


def _battery() -> BatteryDevice:
    device = BatteryDevice()
    device.initialize(
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
        MersenneTwisterRandomPort(seed=42),
    )
    device.set_run_id("property-test")
    return device


def _grid_device() -> GridConnectionDevice:
    device = GridConnectionDevice()
    device.initialize(
        ScenarioDevice(
            id="grid-1",
            type="grid_connection",
            params={
                "nominal_voltage_v": Decimal("400"),
                "max_import_kw": Decimal("1000"),
                "max_export_kw": Decimal("1000"),
            },
        ),
        MersenneTwisterRandomPort(seed=42),
    )
    device.set_run_id("property-test")
    return device


@given(
    start_ms=st.integers(min_value=0, max_value=100_000).map(lambda x: x * 1000),
    duration_ms=st.integers(min_value=1, max_value=50).map(lambda x: x * 1000),
    probe_offset=st.integers(min_value=-3, max_value=3),
)
@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_battery_fault_window_half_open_property(
    start_ms: int, duration_ms: int, probe_offset: int
) -> None:
    """ADR 0025 §2.3 half-open `[start, end)`-Property:
    - Tick bei `start_ms` ist aktiv.
    - Tick bei `start_ms + duration_ms - 1000` ist aktiv (letzte
      aktive Tick).
    - Tick bei `start_ms + duration_ms` ist inaktiv (erste
      Recovery-Tick).
    """
    end_ms = start_ms + duration_ms
    fault = ScenarioFault(
        start_simulation_time=start_ms,
        duration_ms=duration_ms,
        target="battery-1",
        type="cell_failure",
        payload={},
        recovery="auto-recover-after-N-ticks",
    )
    # Drei Probe-Punkte: start, end-1000, end (alle in ms).
    probe_times = (start_ms, max(0, end_ms - 1000), end_ms)
    expected_active = (True, True, False)
    for probe_time, expected in zip(probe_times, expected_active, strict=True):
        # `probe_offset` haben wir, um die Permutation zu testen,
        # aber der Window-Vertrag selbst ist deterministisch —
        # nutzen wir nur fuer Hypothesis-Variantenabdeckung.
        device = _battery()
        adapter = BatteryFaultAdapter(faults=(fault,))
        adapter.apply_active_faults(
            (device,),
            DeviceTickContext(tick=0, simulation_time=probe_time, tick_ms=1000),
        )
        assert device._cell_failure_active is expected, (
            f"start={start_ms} duration={duration_ms} probe={probe_time} "
            f"offset={probe_offset}: expected active={expected}"
        )


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_battery_fault_telemetry_deterministic_per_seed(seed: int) -> None:
    """ADR 0025 §2.4 Determinismus: gleicher Seed + gleiche
    Fault-Sequenz → byte-identische Telemetry."""
    fault = ScenarioFault(
        start_simulation_time=2000,
        duration_ms=5000,
        target="battery-1",
        type="cell_failure",
        payload={},
        recovery="auto-recover-after-N-ticks",
    )

    def _run(seed_value: int) -> tuple[Decimal, ...]:
        device = BatteryDevice()
        device.initialize(
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
            MersenneTwisterRandomPort(seed=seed_value),
        )
        device.set_run_id("property-test")
        adapter = BatteryFaultAdapter(faults=(fault,))
        emissions: list[Decimal] = []
        for tick_num in range(10):
            sim_time = tick_num * 1000
            adapter.apply_active_faults(
                (device,),
                DeviceTickContext(tick=tick_num, simulation_time=sim_time, tick_ms=1000),
            )
            outcome = device.tick(
                DeviceTickContext(tick=tick_num, simulation_time=sim_time, tick_ms=1000)
            )
            emissions.extend(p.value for p in outcome.telemetry)
        return tuple(emissions)

    trace_a = _run(seed)
    trace_b = _run(seed)
    assert trace_a == trace_b


@given(
    start_ms=st.integers(min_value=0, max_value=50_000).map(lambda x: x * 1000),
    duration_ms=st.integers(min_value=1, max_value=20).map(lambda x: x * 1000),
)
@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_grid_fault_window_half_open_property(start_ms: int, duration_ms: int) -> None:
    """ADR 0025 §2.3 fuer GridFaultAdapter: half-open `[start,
    end)`. Welle-2-Test spiegelt `test_battery_fault_window_*`."""
    end_ms = start_ms + duration_ms
    fault = ScenarioFault(
        start_simulation_time=start_ms,
        duration_ms=duration_ms,
        target="grid-1",
        type="voltage_drop",
        payload={},
        recovery="auto-recover-after-N-ticks",
    )
    probe_times = (start_ms, max(0, end_ms - 1000), end_ms)
    expected_active = (True, True, False)
    for probe_time, expected in zip(probe_times, expected_active, strict=True):
        device = _grid_device()
        adapter = GridFaultAdapter(faults=(fault,))
        adapter.apply_active_faults(
            (device,),
            DeviceTickContext(tick=0, simulation_time=probe_time, tick_ms=1000),
        )
        assert device._voltage_drop_active is expected, (
            f"start={start_ms} duration={duration_ms} probe={probe_time}: "
            f"expected active={expected}"
        )
