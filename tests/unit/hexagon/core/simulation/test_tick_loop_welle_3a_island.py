"""M8-Welle-3a Inselnetz-Integration-Tests fuer TickLoop (ADR 0060).

Pinnt die Welle-3a-Vertraege:
- Im Inselnetz haelt das Forming-Geraet den Slack statt des
  GridConnection (`_run_islanded_iterations` / `_apply_islanded_forming_close`).
- Vorzeichen pro Bilanz-Bucket: Generation-Geraet (Diesel) absorbiert
  `-residual`, Storage-Geraet (Battery) `+residual` — beide schliessen die
  Bilanz auf `imbalance_kw == 0`.
- Existenz-Validierung im Wiring: unbekannte `forming_device_id` ->
  `TickLoopUnknownFormingDeviceError` beim Bau.
- Forming-Ueberlast: das Geraet clampt selbst, der Residual leakt ehrlich
  in `imbalance_kw` (ADR 0060 §2.6; Constraint-Event deferred -> 3b).
- `is_islanded=False` waehlt den GridConnection-Slack (Regressions-Abgrenzung).
- Inselnetz-Determinismus ueber >= 100 Ticks.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.diesel_generator import DieselGeneratorDevice
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.errors import TickLoopUnknownFormingDeviceError
from grid_gym.hexagon.core.grid_model import GridModelBilanz, GridModelConfig
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


def _grid_config(
    *, is_islanded: bool = False, forming_device_id: str | None = None
) -> GridModelConfig:
    return GridModelConfig(
        nominal_frequency_hz=Decimal("50"),
        frequency_sensitivity_hz_per_kw=Decimal("0.001"),
        frequency_clamp_min_hz=Decimal("45"),
        frequency_clamp_max_hz=Decimal("55"),
        nominal_voltage_v=Decimal("400"),
        voltage_sensitivity_v_per_kw=Decimal("0.1"),
        voltage_clamp_min_v=Decimal("280"),
        voltage_clamp_max_v=Decimal("520"),
        is_islanded=is_islanded,
        forming_device_id=forming_device_id,
    )


def _make_load(device_id: str = "load-1", rated: Decimal = Decimal("30")) -> LoadDevice:
    load = LoadDevice()
    load.initialize(
        ScenarioDevice(id=device_id, type="load", params={"rated_power_kw": rated}),
        FixedSeedRandom(seed=0),
    )
    return load


def _make_diesel(device_id: str = "diesel-1") -> DieselGeneratorDevice:
    """Forming-faehiger Diesel: hoher Ramp + min_start unter der Testlast,
    damit der Genset in einem Tick auf den Sollwert hochlaeuft."""
    diesel = DieselGeneratorDevice()
    diesel.initialize(
        ScenarioDevice(
            id=device_id,
            type="diesel_generator",
            params={
                "max_power_kw": Decimal("100"),
                "min_start_power_kw": Decimal("5"),
                "min_stop_power_kw": Decimal("1"),
                "fuel_capacity_l": Decimal("1000"),
                "initial_fuel_l": Decimal("1000"),
                "fuel_per_kwh_l": Decimal("0.3"),
                "ramp_kw_per_s": Decimal("1000"),
            },
        ),
        FixedSeedRandom(seed=0),
    )
    return diesel


def _make_battery(device_id: str = "battery-1") -> BatteryDevice:
    """Forming-faehige Battery: hoher Ramp + 50 % SoC-Headroom, damit
    Lade-/Entlade-Sollwerte in einem Tick erreicht werden."""
    battery = BatteryDevice()
    battery.initialize(
        ScenarioDevice(
            id=device_id,
            type="battery",
            params={
                "capacity_kwh": Decimal("100"),
                "initial_soc_pct": Decimal("50"),
                "min_soc_pct": Decimal("0"),
                "max_soc_pct": Decimal("100"),
                "max_charge_kw": Decimal("100"),
                "max_discharge_kw": Decimal("100"),
                "charge_efficiency": Decimal("1"),
                "discharge_efficiency": Decimal("1"),
                "ramp_kw_per_s": Decimal("1000"),
            },
        ),
        FixedSeedRandom(seed=0),
    )
    return battery


def _make_grid_connection(device_id: str = "grid-1") -> GridConnectionDevice:
    grid_dev = GridConnectionDevice()
    grid_dev.initialize(
        ScenarioDevice(
            id=device_id,
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


def _make_loop(
    *,
    devices: tuple[object, ...],
    grid_model: GridModelBilanz,
    tick_ms: int = 1000,
) -> TickLoop:
    return TickLoop(
        run_id="run-3a",
        tick_ms=tick_ms,
        clock=FakeClock(),
        random=MersenneTwisterRandomPort(seed=42),
        scheduler=Scheduler(),
        devices=devices,  # type: ignore[arg-type]
        grid_model=grid_model,
    )


# ---------------------------------------------------------------------------
# Forming-als-Slack: Bilanz schliesst (ADR 0060 §2.2)
# ---------------------------------------------------------------------------


def test_diesel_forming_device_closes_balance() -> None:
    """ADR 0060 §2.2: Generation-Forming-Geraet absorbiert das Residual
    (Diesel deckt 30 kW Last) -> imbalance == 0, Frequenz auf Nennwert."""
    load = _make_load(rated=Decimal("30"))
    diesel = _make_diesel("diesel-1")
    bilanz = GridModelBilanz(config=_grid_config(is_islanded=True, forming_device_id="diesel-1"))
    loop = _make_loop(devices=(load, diesel), grid_model=bilanz)
    result = loop.tick()
    # Diesel laeuft in einem Tick auf 30 kW hoch (residual = -30 ->
    # Generation-Setpoint = +30).
    diesel_power = [
        p
        for p in result.emitted_telemetry
        if p.source == "diesel_generator" and p.metric == "power_kw"
    ]
    assert diesel_power[0].value == Decimal("30")
    assert bilanz.last_imbalance_kw == Decimal("0")
    assert bilanz.frequency_hz == Decimal("50")


def test_battery_forming_device_closes_balance() -> None:
    """ADR 0060 §2.2: Storage-Forming-Geraet absorbiert das Residual
    (Battery entlaedt 30 kW) -> imbalance == 0. Storage-Bucket =>
    invertiertes Vorzeichen (set_power_kw = +residual = -30)."""
    load = _make_load(rated=Decimal("30"))
    battery = _make_battery("battery-1")
    bilanz = GridModelBilanz(config=_grid_config(is_islanded=True, forming_device_id="battery-1"))
    loop = _make_loop(devices=(load, battery), grid_model=bilanz)
    result = loop.tick()
    battery_power = [
        p for p in result.emitted_telemetry if p.source == "battery" and p.metric == "power_kw"
    ]
    assert battery_power[0].value == Decimal("-30")  # Entladen
    assert bilanz.last_imbalance_kw == Decimal("0")
    assert bilanz.frequency_hz == Decimal("50")


def test_forming_device_order_independent() -> None:
    """ADR 0060 §2.2: das Forming-Geraet wird per ID aus der ersten
    Iteration ausgeschlossen und als Slack getickt — unabhaengig von der
    Konstruktor-Reihenfolge (Forming vor Last)."""
    diesel = _make_diesel("diesel-1")
    load = _make_load(rated=Decimal("30"))
    bilanz = GridModelBilanz(config=_grid_config(is_islanded=True, forming_device_id="diesel-1"))
    loop = _make_loop(devices=(diesel, load), grid_model=bilanz)
    loop.tick()
    assert bilanz.last_imbalance_kw == Decimal("0")


# ---------------------------------------------------------------------------
# Existenz-Validierung im Wiring (ADR 0060 §2.3)
# ---------------------------------------------------------------------------


def test_unknown_forming_device_id_rejected_at_construction() -> None:
    """ADR 0060 §2.3: forming_device_id ohne registriertes Geraet ist ein
    Wiring-Fehler — Fail-Fast beim Konstruktor."""
    load = _make_load(rated=Decimal("30"))
    bilanz = GridModelBilanz(config=_grid_config(is_islanded=True, forming_device_id="ghost-dg"))
    with pytest.raises(TickLoopUnknownFormingDeviceError) as exc_info:
        _make_loop(devices=(load,), grid_model=bilanz)
    assert exc_info.value.forming_device_id == "ghost-dg"


def test_connected_config_does_not_validate_forming() -> None:
    """ADR 0060 §2.3: ohne is_islanded gibt es keinen Forming-Check —
    ein netzgekoppelter Loop baut ohne Forming-Geraet."""
    load = _make_load(rated=Decimal("30"))
    grid_dev = _make_grid_connection("grid-1")
    bilanz = GridModelBilanz(config=_grid_config())
    loop = _make_loop(devices=(load, grid_dev), grid_model=bilanz)
    loop.tick()
    # Netzanschluss schliesst die Bilanz (Bestands-Verhalten).
    assert bilanz.last_imbalance_kw == Decimal("0")


# ---------------------------------------------------------------------------
# Forming-Ueberlast: Geraete-Clamp, Residual leakt (ADR 0060 §2.6)
# ---------------------------------------------------------------------------


def test_forming_overload_leaks_residual_into_imbalance() -> None:
    """ADR 0060 §2.6: kann das Forming-Geraet den Sollwert nicht liefern,
    clampt es selbst und der Residual leakt ehrlich in die Bilanz (kein
    Constraint-Event in 3a). Hier liegt der Sollwert +3 kW unter der
    Diesel-min_start-Schwelle 5 kW -> Genset bleibt aus (power 0) ->
    imbalance = 0 - 3 - 0 + 0 = -3."""
    load = _make_load(rated=Decimal("3"))
    diesel = _make_diesel("diesel-1")  # min_start_power_kw = 5
    bilanz = GridModelBilanz(config=_grid_config(is_islanded=True, forming_device_id="diesel-1"))
    loop = _make_loop(devices=(load, diesel), grid_model=bilanz)
    loop.tick()
    # Sollwert +3 < min_start 5 -> Diesel startet nicht -> power 0 ->
    # imbalance = 0 - 3 - 0 + 0 = -3 (Residual unabsorbiert).
    assert bilanz.last_imbalance_kw == Decimal("-3")
    assert bilanz.frequency_hz == Decimal("49.997")


# ---------------------------------------------------------------------------
# Determinismus (ADR 0060 §2.5)
# ---------------------------------------------------------------------------


def _run_island_trace(n_ticks: int) -> tuple[tuple[Decimal, Decimal, Decimal], ...]:
    load = _make_load(rated=Decimal("30"))
    diesel = _make_diesel("diesel-1")
    bilanz = GridModelBilanz(config=_grid_config(is_islanded=True, forming_device_id="diesel-1"))
    loop = _make_loop(devices=(load, diesel), grid_model=bilanz)
    trace: list[tuple[Decimal, Decimal, Decimal]] = []
    for _ in range(n_ticks):
        loop.tick()
        trace.append((bilanz.frequency_hz, bilanz.voltage_v, bilanz.last_imbalance_kw))
    return tuple(trace)


def test_island_determinism_over_100_ticks() -> None:
    """ADR 0060 §2.5: gleiche Insel-Config + Geraete -> byte-identische
    Bilanz-Spur ueber >= 100 Ticks."""
    trace_a = _run_island_trace(100)
    trace_b = _run_island_trace(100)
    assert trace_a == trace_b
    assert len(trace_a) == 100
    # Eingeschwungen schliesst die Insel die Bilanz.
    assert trace_a[-1][2] == Decimal("0")
