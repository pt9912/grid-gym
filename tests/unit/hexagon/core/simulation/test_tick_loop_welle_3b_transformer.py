"""M8-Welle-3b Transformer-Constraint-Integration-Tests fuer TickLoop
(ADR 0061).

Pinnt:
- Der TickLoop reicht `tick_ms`/`simulation_time` an `grid_model.update(...)`
  durch und drainst `last_constraint_violations` in
  `TickResult.emitted_grid_events`.
- Eine Dauer-Ueberlast am Netzanschluss (Auto-Schluss-Import > Nennlast)
  loest nach Zeit-Akkumulation einen `GridConstraintViolationEvent` aus.
- Ohne `transformer_limit` bleibt `emitted_grid_events` leer (Regression).
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.domain.event import (
    CONSTRAINT_TRANSFORMER_HOT_SPOT,
    GridConstraintViolationEvent,
)
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.grid_model import (
    GridModelBilanz,
    GridModelConfig,
    TransformerLimitConfig,
)
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


def _grid_config(*, transformer_limit: TransformerLimitConfig | None) -> GridModelConfig:
    return GridModelConfig(
        nominal_frequency_hz=Decimal("50"),
        frequency_sensitivity_hz_per_kw=Decimal("0.001"),
        frequency_clamp_min_hz=Decimal("45"),
        frequency_clamp_max_hz=Decimal("55"),
        nominal_voltage_v=Decimal("400"),
        voltage_sensitivity_v_per_kw=Decimal("0.1"),
        voltage_clamp_min_v=Decimal("280"),
        voltage_clamp_max_v=Decimal("520"),
        transformer_limit=transformer_limit,
    )


def _transformer_limit() -> TransformerLimitConfig:
    return TransformerLimitConfig(
        max_apparent_power_kva=Decimal("100"),
        ambient_temp_c=Decimal("20"),
        top_oil_rise_rated_c=Decimal("40"),
        hot_spot_rise_rated_c=Decimal("30"),
        top_oil_time_constant_s=Decimal("10"),
        hot_spot_limit_c=Decimal("98"),
    )


def _make_load(rated: Decimal) -> LoadDevice:
    load = LoadDevice()
    load.initialize(
        ScenarioDevice(id="load-1", type="load", params={"rated_power_kw": rated}),
        FixedSeedRandom(seed=0),
    )
    return load


def _make_grid_connection() -> GridConnectionDevice:
    grid_dev = GridConnectionDevice()
    grid_dev.initialize(
        ScenarioDevice(
            id="grid-1",
            type="grid_connection",
            params={
                "nominal_voltage_v": Decimal("400"),
                "max_import_kw": Decimal("1000"),
                "max_export_kw": Decimal("1000"),
            },
        ),
        FixedSeedRandom(seed=0),
    )
    return grid_dev


def _make_loop(grid_model: GridModelBilanz) -> TickLoop:
    return TickLoop(
        run_id="run-3b",
        tick_ms=1000,
        clock=FakeClock(),
        random=MersenneTwisterRandomPort(seed=42),
        scheduler=Scheduler(),
        devices=(_make_load(Decimal("130")), _make_grid_connection()),
        grid_model=grid_model,
    )


def test_sustained_overload_emits_grid_event_in_tick_result() -> None:
    """ADR 0061 §2.4: Dauer-Ueberlast (Load 130 → Auto-Schluss-Import 130
    > 100 kVA Nennlast) loest nach Zeit-Akkumulation einen
    `GridConstraintViolationEvent` aus, der im `TickResult` ankommt."""
    bilanz = GridModelBilanz(config=_grid_config(transformer_limit=_transformer_limit()))
    loop = _make_loop(bilanz)
    saw_event = False
    last_event: GridConstraintViolationEvent | None = None
    for _ in range(60):
        result = loop.tick()
        if result.emitted_grid_events:
            saw_event = True
            last_event = result.emitted_grid_events[0]
    assert saw_event, "Dauer-Ueberlast haette einen Constraint-Event emittieren muessen"
    assert last_event is not None
    assert last_event.constraint == CONSTRAINT_TRANSFORMER_HOT_SPOT
    assert last_event.apparent_power_kva == Decimal("130")
    assert last_event.limit_kva == Decimal("100")


def test_first_tick_no_event_thermal_inertia() -> None:
    """ADR 0061 §2.2: der erste Tick erwaermt das Oel kaum → kein Event
    (thermische Traegheit = Zeit-Strom-Kennlinie)."""
    bilanz = GridModelBilanz(config=_grid_config(transformer_limit=_transformer_limit()))
    loop = _make_loop(bilanz)
    result = loop.tick()
    assert result.emitted_grid_events == ()


def test_event_simulation_time_matches_tick() -> None:
    """ADR 0061 §2.3: die Event-`simulation_time` ist die Sim-Zeit des
    ausloesenden Ticks."""
    bilanz = GridModelBilanz(config=_grid_config(transformer_limit=_transformer_limit()))
    loop = _make_loop(bilanz)
    for _ in range(60):
        result = loop.tick()
        if result.emitted_grid_events:
            assert result.emitted_grid_events[0].simulation_time == result.simulation_time
            break
    else:
        raise AssertionError("kein Constraint-Event in 60 Ticks")


def test_without_transformer_limit_no_grid_events() -> None:
    """ADR 0061 §2.6 Regression: ohne `transformer_limit` bleibt
    `emitted_grid_events` ueber alle Ticks leer."""
    bilanz = GridModelBilanz(config=_grid_config(transformer_limit=None))
    loop = _make_loop(bilanz)
    for _ in range(20):
        assert loop.tick().emitted_grid_events == ()
