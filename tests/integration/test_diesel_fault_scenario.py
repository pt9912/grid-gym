"""M8-Welle-2-D8 End-to-End-Smoke fuer den Fault-Pfad eines neuen
Welle-2-Geraets ueber die generische `ScenarioFaultEngine`
(ADR 0059, Carveout D-8).

Pinnt, dass ein NEUER Fault-Typ (`genset_fault`) end-to-end wirkt:

    YAML faults-Block -> Loader -> TickLoop-Vor-Tick-Block ->
    ScenarioFaultEngine.apply_active_faults -> Diesel.inject_fault
    -> genset_fault-Telemetrie (1 im Window, 0 ausserhalb).

Vor ADR 0059 war dieser Pfad nicht verdrahtet (Carveout D-8): die
drei neuen Welle-2-Fault-Typen hatten Geraete-Surface + HTTP-
Whitelist, aber keine Runtime-Engine. Dieser Test guardt zudem, dass
`genset_fault` in der produktiven `_KNOWN_FAULT_TYPES` steht (Import).
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.composition._demo_scenario_setup import _KNOWN_FAULT_TYPES, _compose_fault_port
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.scenario.loader import (
    LoadedScenario,
    TickLoopWiring,
    build_tick_loop,
)

from tests.integration._constants import (
    DIESEL_FAULT_DEMO_SCENARIO_PATH,
    DIESEL_FAULT_DEMO_TICKS,
)
from tests.integration._yaml_scenario_loader import load_yaml_scenario
from tests.unit.hexagon.ports.driven._fakes import FakeClock


def _drive(loaded: LoadedScenario, *, ticks: int) -> tuple[TelemetryPoint, ...]:
    """Faehrt den Diesel-Fault-Demo durch `ticks` Ticks ueber den
    PRODUKTIVEN `_compose_fault_port` (exerziert die echte Single-
    Engine-Verdrahtung + die fail-fast `_KNOWN_FAULT_TYPES`-
    Validierung, nicht eine handgebaute Engine)."""
    fault_port = _compose_fault_port(loaded.scenario.faults)
    assert fault_port is not None, "diesel_fault_demo.yaml deklariert genset_fault"
    loop = build_tick_loop(
        loaded.scenario,
        run_id="welle-2-d8-diesel-fault-demo",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed),
        wiring=TickLoopWiring(fault_port=fault_port),
    )
    collected: list[TelemetryPoint] = []
    for _ in range(ticks):
        collected.extend(loop.tick().emitted_telemetry)
    return tuple(collected)


def test_genset_fault_in_production_known_fault_types() -> None:
    """D-8-Guard: genset_fault ist in der produktiven Whitelist."""
    assert "genset_fault" in _KNOWN_FAULT_TYPES


def test_diesel_genset_fault_active_only_in_window() -> None:
    """ADR 0025 §2.3 half-open: genset_fault-Telemetrie ist `1`
    waehrend des Windows [5000, 15000) und `0` davor/danach.

    Window/Telemetrie werden aus dem geladenen Scenario abgeleitet
    (nicht hardcoded), damit eine YAML-Umkonfiguration den Test
    nicht still widerlegt (Welle-2-Review L-3-Pattern)."""
    loaded = load_yaml_scenario(DIESEL_FAULT_DEMO_SCENARIO_PATH)
    telemetry = _drive(loaded, ticks=DIESEL_FAULT_DEMO_TICKS)
    fault_points = [
        (p.simulation_time, p.value)
        for p in telemetry
        if p.device_id == "dg-1" and p.metric == "genset_fault"
    ]
    assert len(fault_points) == DIESEL_FAULT_DEMO_TICKS

    genset_fault = next(f for f in loaded.scenario.faults if f.type == "genset_fault")
    window_start = genset_fault.start_simulation_time
    window_end = window_start + genset_fault.duration_ms

    active_ticks = 0
    for sim_time, value in fault_points:
        if window_start <= sim_time < window_end:
            assert value == Decimal("1.000000"), (
                f"sim_time {sim_time}: genset_fault sollte aktiv sein"
            )
            active_ticks += 1
        else:
            assert value == Decimal("0.000000"), (
                f"sim_time {sim_time}: genset_fault sollte inaktiv sein"
            )
    assert active_ticks == 10, "Window [5000,15000) deckt 10 Ticks ab"


def test_diesel_fault_demo_telemetry_byte_identical_across_runs() -> None:
    """Telemetrie-Stabilitaet: zwei Laeufe ueber `_compose_fault_port`
    liefern byte-identische Telemetrie. Dieses Szenario hat keine
    RNG-Konsumenten (Genset command-los STOPPED) — der starke Seed-
    Determinismus-Beweis fuer Fault-Sequenzen liegt in
    `test_fault_demo_scenario.py` (Battery+Grid, mehrere Faults);
    hier ist es ein Stabilitaets-Smoke des Composer-Pfads."""
    loaded = load_yaml_scenario(DIESEL_FAULT_DEMO_SCENARIO_PATH)
    assert _drive(loaded, ticks=DIESEL_FAULT_DEMO_TICKS) == _drive(
        loaded, ticks=DIESEL_FAULT_DEMO_TICKS
    )
