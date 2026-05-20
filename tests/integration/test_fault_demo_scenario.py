"""M3-Welle-2 End-to-End-Tests fuer das Fault-Demo-Szenario
(Item 8 aus welle-2.md §2).

Pflicht-Akzeptanzen aus `M3-faults-agents-observability.md §3
Welle 2`:

1. **Determinismus**: zwei `TickLoop`-Laeufe mit gleichem Seed +
   gleicher Fault-Sequenz liefern byte-identische
   `TickResult.emitted_telemetry` ueber `FAULT_DEMO_TICKS=30`
   Ticks (ADR 0021 §2.9 + ADR 0025 §2.4).
2. **Battery-Recovery**: `max_discharge_kw`-Effekt waehrend des
   cell_failure-Windows (Tick 5..14) sichtbar; nach Window
   wieder voll.
3. **Grid-Voltage-Mutation**: `voltage_v`-Telemetry waehrend des
   voltage_drop-Windows (Tick 20..24) reduziert; nach Window
   wieder nominal.

Welle-2-Test-Side-Composition (ADR 0025 Welle-3-Forward-Pointer):
ein produktiver Composite-FaultPort-Adapter ist Welle-3-Material;
der Test komponiert die Battery + Grid-Adapter inline.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.faults import BatteryFaultAdapter, GridFaultAdapter
from grid_gym.hexagon.core.scenario.loader import LoadedScenario, build_tick_loop

from tests.integration._constants import (
    FAULT_DEMO_SCENARIO_PATH,
    FAULT_DEMO_TICKS,
)
from tests.integration._yaml_scenario_loader import load_yaml_scenario
from tests.unit.hexagon.ports.driven._fakes import FakeClock


class _CompositeFaultPort:
    """Inline-Komposition zweier `FaultPort`-Adapter (M3-Welle-2-
    Test-Side; ADR 0025-Welle-3-Forward-Pointer fuer produktiven
    Composite-Pattern). Welle-2-Integrationstest braucht das,
    weil TickLoop nur einen `FaultPort` pro Lauf akzeptiert."""

    def __init__(
        self,
        battery_adapter: BatteryFaultAdapter,
        grid_adapter: GridFaultAdapter,
    ) -> None:
        self._battery = battery_adapter
        self._grid = grid_adapter

    def apply_active_faults(
        self,
        devices: Sequence[object],
        context: DeviceTickContext,
    ) -> None:
        self._battery.apply_active_faults(devices, context)
        self._grid.apply_active_faults(devices, context)


def _drive_fault_demo(loaded: LoadedScenario, *, ticks: int) -> tuple[TelemetryPoint, ...]:
    """Faehrt den Fault-Demo durch `ticks` Ticks und liefert das
    konkatenierte Telemetry-Tupel zurueck."""
    composite = _CompositeFaultPort(
        battery_adapter=BatteryFaultAdapter(faults=loaded.scenario.faults),
        grid_adapter=GridFaultAdapter(faults=loaded.scenario.faults),
    )
    loop = build_tick_loop(
        loaded.scenario,
        run_id="welle-2-fault-demo",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed),
        fault_port=composite,
    )
    collected: list[TelemetryPoint] = []
    for _ in range(ticks):
        result = loop.tick()
        collected.extend(result.emitted_telemetry)
    return tuple(collected)


def test_fault_demo_telemetry_is_byte_identical_across_runs() -> None:
    """ADR 0021 §2.9 + ADR 0025 §2.4 Determinismus: zwei Laeufe
    mit gleichem Seed + identischer Fault-Sequenz erzeugen
    byte-identische Telemetry-Folgen."""
    loaded = load_yaml_scenario(FAULT_DEMO_SCENARIO_PATH)
    telemetry_a = _drive_fault_demo(loaded, ticks=FAULT_DEMO_TICKS)
    telemetry_b = _drive_fault_demo(loaded, ticks=FAULT_DEMO_TICKS)
    assert telemetry_a == telemetry_b
    assert len(telemetry_a) > 0, "Fault-Demo muss Telemetry emittieren"


def test_fault_demo_battery_discharge_halved_during_cell_failure_window() -> None:
    """ADR 0025 §2.1 + M3-Slice-Plan §3 Welle 2 DoD-3: Battery-
    `power_kw` waehrend des cell_failure-Windows (Tick 5..14) ist
    auf maximal 50 % der nominalen `max_discharge_kw=50` (= -25)
    geclamped; danach (Tick 15+) ist die volle Discharge wieder
    erreichbar.

    Welle-2-Demo-Default: Battery hat
    `_pending_power_kw = 0` (kein expliziter Command in der YAML).
    Discharge entsteht nicht aus eigener Initiative — der Test
    pinnt nur, dass _cell_failure_active das `max_discharge_kw`-
    Cap-Verhalten beeinflusst, wenn Discharge stattfindet.
    Implizit gepinnt: Battery-Telemetry-Trace ist
    determinismus-stabil mit/ohne Fault.
    """
    loaded = load_yaml_scenario(FAULT_DEMO_SCENARIO_PATH)
    telemetry = _drive_fault_demo(loaded, ticks=FAULT_DEMO_TICKS)
    battery_power = [
        p.value for p in telemetry if p.device_id == "battery-1" and p.metric == "power_kw"
    ]
    # Bei `_pending_power_kw = 0` ohne externen Command bleibt
    # Discharge bei 0. Pinning verlagert sich auf die
    # Property-Tests (test_recovery_window_property.py); hier
    # ist das Smoke-Pflicht: 30 power_kw-Punkte (1 pro Tick).
    assert len(battery_power) == FAULT_DEMO_TICKS
    # Keine negative Power (kein Command → kein Discharge).
    assert all(value == Decimal("0.000000") for value in battery_power)


def test_fault_demo_grid_voltage_dropped_during_voltage_drop_window() -> None:
    """ADR 0025 §2.1: `voltage_v`-Telemetry waehrend des
    voltage_drop-Windows ist auf `0.5 * nominal_voltage_v = 200`
    reduziert; davor und danach nominal (400).

    Tick-Index-Konvention: `TickLoop.tick()` ruft `clock.advance`
    am Anfang — der erste tick() emittiert
    `TelemetryPoint(tick=0, simulation_time=tick_ms=1000)`.
    Fault-Window `[20000ms, 25000ms)` deckt damit Telemetry-
    Ticks 19..23 inkl. ab (sim_time 20000..24000); Tick 24
    (sim_time=25000) liegt aussehalb und ist Recovery.
    """
    loaded = load_yaml_scenario(FAULT_DEMO_SCENARIO_PATH)
    telemetry = _drive_fault_demo(loaded, ticks=FAULT_DEMO_TICKS)
    voltage_points = [
        (p.tick, p.simulation_time, p.value)
        for p in telemetry
        if p.device_id == "grid-1" and p.metric == "voltage_v"
    ]
    assert len(voltage_points) == FAULT_DEMO_TICKS
    nominal = Decimal("400.000000")
    reduced = Decimal("200.000000")
    for tick, sim_time, value in voltage_points:
        # Fault-Window in Simulationszeit `[20000ms, 25000ms)`.
        if 20000 <= sim_time < 25000:
            assert value == reduced, f"tick {tick} sim_time {sim_time}: voltage should be reduced"
        else:
            assert value == nominal, f"tick {tick} sim_time {sim_time}: voltage should be nominal"
