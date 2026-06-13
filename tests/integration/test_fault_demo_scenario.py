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

import uuid
from decimal import Decimal

from grid_gym.adapters.driven.persistence_postgres import PostgresRunRepository
from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.faults import BatteryFaultEngine, GridFaultEngine
from grid_gym.hexagon.core.scenario.loader import (
    LoadedScenario,
    TickLoopWiring,
    build_tick_loop,
)

from tests.integration._constants import (
    DEMO_TOOL_VERSION,
    FAULT_DEMO_SCENARIO_PATH,
    FAULT_DEMO_TICKS,
)
from tests.integration._fault_composite import CompositeFaultPort
from tests.integration._yaml_scenario_loader import load_yaml_scenario
from tests.unit.hexagon.ports.driven._fakes import FakeClock


def _drive_fault_demo(
    loaded: LoadedScenario,
    *,
    ticks: int,
    battery_first: bool = True,
) -> tuple[TelemetryPoint, ...]:
    """Faehrt den Fault-Demo durch `ticks` Ticks und liefert das
    konkatenierte Telemetry-Tupel zurueck. `battery_first` schaltet
    die Sub-Port-Reihenfolge im CompositeFaultPort um (Welle-2-
    Review M-2)."""
    composite = CompositeFaultPort(
        battery_adapter=BatteryFaultEngine(faults=loaded.scenario.faults),
        grid_adapter=GridFaultEngine(faults=loaded.scenario.faults),
        battery_first=battery_first,
    )
    loop = build_tick_loop(
        loaded.scenario,
        run_id="welle-2-fault-demo",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed),
        wiring=TickLoopWiring(fault_port=composite),
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


def test_fault_demo_battery_emits_power_kw_smoke() -> None:
    """Welle-2-Items-7-10-Review-Folge H-1: Smoke-Pflicht — der
    Integrationstest beobachtet, dass Battery 30 `power_kw`-
    Telemetry-Punkte emittiert (1 pro Tick) und ohne expliziten
    `set_power_kw`-Command nicht aus eigener Initiative
    entlaedt.

    **NICHT** gepinnt durch diesen Test: das `max_discharge_kw`-
    Halbierungs-Verhalten unter aktivem `cell_failure`. Welle-6b
    `_assert_overlay_targets` (ADR 0021 §2.5) erlaubt
    `LoadEvent`/`LoadProfile` nur auf `LoadDevice`/
    `GridConnectionDevice`, nicht auf Battery — ein YAML-
    angetriebener Battery-Discharge ist in Welle-2-Scope nicht
    moeglich, ohne den Scenario-Loader-Vertrag zu erweitern
    (Welle-3-Material).

    Der Halbierungs-Vertrag selbst ist gepinnt durch:
    - `test_tick_with_active_cell_failure_halves_discharge_clamp`
      (`tests/unit/.../battery/test_fault_injection.py`).
    - `test_battery_fault_telemetry_deterministic_per_seed`
      (`tests/unit/.../faults/test_recovery_window_property.py`).
    """
    loaded = load_yaml_scenario(FAULT_DEMO_SCENARIO_PATH)
    telemetry = _drive_fault_demo(loaded, ticks=FAULT_DEMO_TICKS)
    battery_power = [
        p.value for p in telemetry if p.device_id == "battery-1" and p.metric == "power_kw"
    ]
    assert len(battery_power) == FAULT_DEMO_TICKS
    # Kein externer Command → Default-Discharge = 0.
    assert all(value == Decimal("0.000000") for value in battery_power)


def test_fault_demo_grid_voltage_dropped_during_voltage_drop_window() -> None:
    """ADR 0025 §2.1: `voltage_v`-Telemetry waehrend des
    voltage_drop-Windows ist auf `0.5 * nominal_voltage_v`
    reduziert; davor und danach nominal.

    Welle-2-Review L-3: nominal + reduced + Window werden aus dem
    geladenen Scenario abgeleitet, nicht hardcoded. Dadurch
    erkennt der Test, wenn `fault_demo.yaml` umkonfiguriert wird
    (z. B. nominal_voltage_v=415V), und meldet sich statt sich
    selbst zu widerlegen.

    Tick-Index-Konvention: `TickLoop.tick()` ruft `clock.advance`
    am Anfang — der erste tick() emittiert
    `TelemetryPoint(tick=0, simulation_time=tick_ms=1000)`.
    """
    loaded = load_yaml_scenario(FAULT_DEMO_SCENARIO_PATH)
    telemetry = _drive_fault_demo(loaded, ticks=FAULT_DEMO_TICKS)
    voltage_points = [
        (p.tick, p.simulation_time, p.value)
        for p in telemetry
        if p.device_id == "grid-1" and p.metric == "voltage_v"
    ]
    assert len(voltage_points) == FAULT_DEMO_TICKS

    grid_device_def = next(d for d in loaded.scenario.devices if d.id == "grid-1")
    nominal_param = grid_device_def.params["nominal_voltage_v"]
    assert isinstance(nominal_param, Decimal)
    nominal = Decimal(nominal_param).quantize(Decimal("0.000001"))
    # ADR 0025 §2.1: `_VOLTAGE_DROP_FRACTION = 0.5`.
    reduced = (nominal_param * Decimal("0.5")).quantize(Decimal("0.000001"))

    voltage_fault = next(f for f in loaded.scenario.faults if f.type == "voltage_drop")
    window_start = voltage_fault.start_simulation_time
    window_end = window_start + voltage_fault.duration_ms

    for tick, sim_time, value in voltage_points:
        if window_start <= sim_time < window_end:
            assert value == reduced, f"tick {tick} sim_time {sim_time}: voltage should be reduced"
        else:
            assert value == nominal, f"tick {tick} sim_time {sim_time}: voltage should be nominal"


def test_fault_demo_run_roundtrips_through_postgres(
    repository: PostgresRunRepository,
) -> None:
    """Welle-2-Review M-3: Postgres-Roundtrip symmetrisch zu
    `test_demo_scenario_run_roundtrips_through_postgres` aus
    `test_mvp_demo_scenario.py`. `RunMetadata` aus dem Fault-Demo-
    Lauf wird ueber `PostgresRunRepository.save(...)` persistiert
    und per `get_by_id(...)` byte-identisch zurueckgelesen.

    Stellt sicher, dass die `runs`-Persistenz (M2-Welle-6c) auch
    mit dem Fault-Pfad (M3-Welle-2) zusammenarbeitet — Welle-2
    fuehrt keinen neuen `runs`-Felder-Bedarf ein, aber der
    Smoke-Test fixiert das.
    """
    loaded = load_yaml_scenario(FAULT_DEMO_SCENARIO_PATH)
    metadata = RunMetadata(
        run_id=str(uuid.uuid4()),
        scenario_hash=loaded.scenario_hash,
        schema_version=loaded.scenario.schema_version,
        seed=loaded.scenario.simulation.seed,
        tick_ms=loaded.scenario.simulation.tick_ms,
        started_at="2026-05-20T09:00:00Z",
        ended_at="2026-05-20T09:00:30Z",
        tool_version=DEMO_TOOL_VERSION,
    )
    repository.save(metadata)
    assert repository.get_by_id(metadata.run_id) == metadata


def test_fault_demo_composite_order_invariant_for_non_overlapping_faults() -> None:
    """Welle-2-Review M-2: das `fault_demo.yaml` enthaelt zwei
    NICHT-ueberlappende Faults (Battery `[5000, 15000)` vs. Grid
    `[20000, 25000)`). Damit muessen Battery-zuerst- und Grid-
    zuerst-Composite-Reihenfolge byte-identische Telemetry
    erzeugen.

    Pinnt: das Determinismus-Versprechen aus ADR 0025 §2.4 ist
    nicht von der Sub-Port-Reihenfolge im Composite abhaengig,
    solange keine zwei Faults im selben Tick auf dasselbe Device
    zielen. Welle-3-Composite-Adapter darf das Pattern brechen,
    aber dann braucht es einen expliziten ADR-Eintrag.
    """
    loaded = load_yaml_scenario(FAULT_DEMO_SCENARIO_PATH)
    battery_first = _drive_fault_demo(loaded, ticks=FAULT_DEMO_TICKS, battery_first=True)
    grid_first = _drive_fault_demo(loaded, ticks=FAULT_DEMO_TICKS, battery_first=False)
    assert battery_first == grid_first
