"""Hypothesis-Property-Tests fuer Recovery-Window-Boundary
und Per-Fault-Determinismus (M3 Welle 2 Item 9, ADR 0025 §2.3
+ §2.4).

Pinnt:
- **Half-open `[start, end)`**: BatteryFaultAdapter aktiviert den
  Fault genau in `[start, start+duration)`-Ticks, nicht davor
  oder danach. Property-Test mit `@given(start_ms, duration_ms)`.
- **Per-Fault-Determinismus**: gleicher Seed + identische
  Fault-Sequenz erzeugen byte-identische Telemetry. Spiegelt
  M2-Welle-6c-Permutations-Pattern fuer den Fault-Pfad.

TODO(M3-Welle-3, Welle-2-Review-N-2): falls Welle 3 stochastische
Recovery einfuehrt (z. B. `probabilistic-permanent-at-rate-X`),
muss `test_battery_fault_telemetry_deterministic_per_seed` den
`RandomPort` identisch in beide Adapter-Instanzen injizieren.
Welle-2-Adapter ignorieren den Random-Pfad; die Property haelt
deshalb byte-stabil.
"""

from __future__ import annotations

from decimal import Decimal

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, assume, given, settings

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
    duration_ms=st.integers(min_value=2, max_value=50).map(lambda x: x * 1000),
)
@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_battery_fault_window_half_open_property(start_ms: int, duration_ms: int) -> None:
    """ADR 0025 §2.3 half-open `[start, end)`-Property:
    - Tick bei `start_ms` ist aktiv.
    - Tick bei `start_ms + duration_ms - 1000` ist aktiv (letzte
      aktive Tick; bei duration_ms=1000 identisch zu start_ms,
      daher schliessen wir `duration_ms=1000` via min_value=2 aus
      — Welle-2-Review-L-1).
    - Tick bei `start_ms + duration_ms` ist inaktiv (erste
      Recovery-Tick).
    """
    # Welle-2-Review-Folge L-1: duration_ms >= 2000 garantiert,
    # dass `end_ms - 1000 > start_ms` und die mittlere Probe
    # tatsaechlich eine andere Tick als die Start-Probe trifft.
    assume(duration_ms >= 2000)
    end_ms = start_ms + duration_ms
    fault = ScenarioFault(
        start_simulation_time=start_ms,
        duration_ms=duration_ms,
        target="battery-1",
        type="cell_failure",
        payload={},
        recovery="auto-recover-after-N-ticks",
    )
    # Drei Probe-Punkte: start, end-1000 (letzte aktive Tick), end.
    probe_times = (start_ms, end_ms - 1000, end_ms)
    expected_active = (True, True, False)
    for probe_time, expected in zip(probe_times, expected_active, strict=True):
        device = _battery()
        adapter = BatteryFaultAdapter(faults=(fault,))
        adapter.apply_active_faults(
            (device,),
            DeviceTickContext(tick=0, simulation_time=probe_time, tick_ms=1000),
        )
        assert device._cell_failure_active is expected, (
            f"start={start_ms} duration={duration_ms} probe={probe_time}: "
            f"expected active={expected}"
        )


@given(seed=st.integers(min_value=0, max_value=2**16 - 1))
@settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_battery_fault_telemetry_deterministic_per_seed(seed: int) -> None:
    """ADR 0025 §2.4 Determinismus: gleicher Seed + gleiche
    Fault-Sequenz → byte-identische Telemetry.

    Welle-2-Review L-2: Seed-Range auf 16 bit beschraenkt
    (`0..65535`). Die Determinismus-Property ist Hash-Equality,
    nicht Verteilungs-Property; ein paar Beispiele reichen, der
    4G-Seed-Sample-Pool aus Welle-2-Erstwurf war Hypothesis-
    Budget-Verschwendung.
    """
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


def test_battery_fault_telemetry_battery_seed_independent_in_welle_2() -> None:
    """Welle-2-Review L-4: in Welle 2 ignorieren BatteryDevice und
    BatteryFaultAdapter den `RandomPort` voellig (kein
    stochastischer Anteil). Telemetry ist seed-unabhaengig.

    Welle-3-Forward-Pointer: bei stochastischer Recovery
    (siehe Modul-Docstring TODO) wird das nicht mehr gelten.
    """
    fault = ScenarioFault(
        start_simulation_time=2000,
        duration_ms=5000,
        target="battery-1",
        type="cell_failure",
        payload={},
        recovery="auto-recover-after-N-ticks",
    )

    def _run(seed_value: int) -> tuple[Decimal, ...]:
        device = _battery_with_seed(seed_value)
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

    assert _run(seed_value=0) == _run(seed_value=99999), (
        "Welle-2-Battery ist seed-unabhaengig; Telemetry-Trace muss "
        "ueber unterschiedliche Seeds identisch bleiben."
    )


def _battery_with_seed(seed_value: int) -> BatteryDevice:
    """Helper: BatteryDevice mit konfigurierbarem Seed
    (Welle-2-Review L-4)."""
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
    return device


@given(
    start_ms=st.integers(min_value=0, max_value=50_000).map(lambda x: x * 1000),
    duration_ms=st.integers(min_value=2, max_value=20).map(lambda x: x * 1000),
)
@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_grid_fault_window_half_open_property(start_ms: int, duration_ms: int) -> None:
    """ADR 0025 §2.3 fuer GridFaultAdapter: half-open `[start,
    end)`. Welle-2-Test spiegelt `test_battery_fault_window_*`."""
    assume(duration_ms >= 2000)
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
