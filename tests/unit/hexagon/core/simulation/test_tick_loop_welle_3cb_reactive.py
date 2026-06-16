"""M8-Welle-3c-b-1 Reaktive-Leistungs-Integration-Tests fuer TickLoop
(ADR 0063).

Pinnt:
- Der TickLoop reicht die (lagged) `GridModelBilanz.voltage_v` als
  `DeviceTickContext.grid_voltage_v` an die Geraete.
- Eine PV mit Volt-Var-Kurve emittiert `reactive_power_kvar`, das der
  TickLoop in `imbalance_kvar` aggregiert (-> Q-Spannungskopplung 3c-a).
- Lagged-Feedback-Determinismus ueber >= 100 Ticks.
- Eine PV OHNE Kurve emittiert keine Q-Telemetrie -> `imbalance_kvar == 0`
  (pin-neutral).
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.devices.pv import PvDevice
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.grid_model import GridModelBilanz, GridModelConfig
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


def _grid_config() -> GridModelConfig:
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


def _make_pv(*, with_volt_var: bool) -> PvDevice:
    params: dict[str, object] = {"rated_power_kw": Decimal("100")}
    if with_volt_var:
        # Referenz 395 < Nennspannung 400 → bei Nennspannung schon Q != 0
        # (Deadband 0), damit der Q-Pfad ohne P-Imbalance aktiv ist.
        params["volt_var"] = {
            "reference_voltage_v": Decimal("395"),
            "deadband_v": Decimal("0"),
            "droop_kvar_per_v": Decimal("2"),
            "max_kvar": Decimal("50"),
        }
    pv = PvDevice()
    pv.initialize(ScenarioDevice(id="pv-1", type="pv", params=params), FixedSeedRandom(seed=0))
    return pv


def _make_load() -> LoadDevice:
    # Last == PV-Nennleistung → Wirkleistungs-Bilanz geschlossen
    # (imbalance_kw == 0), damit der Test die reine Q-Spannungskopplung pinnt.
    load = LoadDevice()
    load.initialize(
        ScenarioDevice(id="load-1", type="load", params={"rated_power_kw": Decimal("100")}),
        FixedSeedRandom(seed=0),
    )
    return load


def _make_loop(pv: PvDevice, grid_model: GridModelBilanz) -> TickLoop:
    return TickLoop(
        run_id="run-3cb",
        tick_ms=1000,
        clock=FakeClock(),
        random=MersenneTwisterRandomPort(seed=42),
        scheduler=Scheduler(),
        devices=(pv, _make_load()),
        grid_model=grid_model,
    )


def test_pv_volt_var_q_flows_into_imbalance_kvar() -> None:
    """ADR 0063 §2.1/§2.4: die lagged Netzspannung treibt die PV-Q(U),
    der TickLoop aggregiert Q in `imbalance_kvar`."""
    bilanz = GridModelBilanz(config=_grid_config())
    loop = _make_loop(_make_pv(with_volt_var=True), bilanz)
    result = loop.tick()
    # Tick 0: grid_voltage = Nennspannung 400 (init), ref 395 → dv=5 →
    # Q = -2*5 = -10. Telemetrie + Bilanz-Q.
    q_points = [p for p in result.emitted_telemetry if p.metric == "reactive_power_kvar"]
    assert len(q_points) == 1
    assert q_points[0].value == Decimal("-10.000000")
    assert bilanz.last_imbalance_kvar == Decimal("-10.000000")
    # Q koppelt an die Spannung: 400 + 0.2*(-10) = 398.
    assert bilanz.voltage_v == Decimal("398")


def test_lagged_feedback_uses_previous_tick_voltage() -> None:
    """ADR 0063 §2.1: Tick N nutzt die Spannung aus Tick N-1."""
    bilanz = GridModelBilanz(config=_grid_config())
    loop = _make_loop(_make_pv(with_volt_var=True), bilanz)
    loop.tick()  # tick 0: U=400 → Q=-10 → U wird 398
    result = loop.tick()  # tick 1: liest U=398 (von tick 0), ref 395 → dv=3 → Q=-6
    q_points = [p for p in result.emitted_telemetry if p.metric == "reactive_power_kvar"]
    assert q_points[0].value == Decimal("-6.000000")


def test_no_volt_var_no_q_telemetry_pin_neutral() -> None:
    """ADR 0063 §2.6: PV ohne Kurve emittiert keine Q-Telemetrie ->
    imbalance_kvar bleibt 0 (pin-neutral)."""
    bilanz = GridModelBilanz(config=_grid_config())
    loop = _make_loop(_make_pv(with_volt_var=False), bilanz)
    result = loop.tick()
    assert [p for p in result.emitted_telemetry if p.metric == "reactive_power_kvar"] == []
    assert bilanz.last_imbalance_kvar == Decimal("0")


def _q_trace(n_ticks: int) -> tuple[tuple[Decimal, Decimal], ...]:
    bilanz = GridModelBilanz(config=_grid_config())
    loop = _make_loop(_make_pv(with_volt_var=True), bilanz)
    trace: list[tuple[Decimal, Decimal]] = []
    for _ in range(n_ticks):
        loop.tick()
        trace.append((bilanz.voltage_v, bilanz.last_imbalance_kvar))
    return tuple(trace)


def test_lagged_feedback_determinism_over_100_ticks() -> None:
    """ADR 0063 §2.6: gleiche Konfiguration → byte-identische Q-/Spannungs-
    Spur ueber >= 100 Ticks (lagged, ohne Iteration)."""
    trace_a = _q_trace(100)
    trace_b = _q_trace(100)
    assert trace_a == trace_b
    assert len(trace_a) == 100
