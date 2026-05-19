"""Welle-6a-Integration-Tests fuer TickLoop (ADR 0015 + ADR 0019).

Pinnt:
- Device-Iteration in stabiler Reihenfolge.
- Telemetry-Konkatenation in TickResult.emitted_telemetry.
- Bilanz-Aggregation (TelemetryPoint.source -> generation/load/
  storage/grid_connection).
- grid_model.update(...) wird nach allen Device-Ticks gerufen.
- Snapshot-Sub-Keys: `devices.<device_type>.<device_id>` x N
  + `grid_model`.
- TickLoop ohne Devices/grid_model bleibt M1-kompatibel.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.devices.pv import PvDevice
from grid_gym.hexagon.core.devices.smart_meter import SmartMeterDevice
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.grid_model import GridModelBilanz, GridModelConfig
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


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


def _make_pv(device_id: str = "pv-1", rated: Decimal = Decimal("500")) -> PvDevice:
    pv = PvDevice()
    pv.initialize(
        ScenarioDevice(id=device_id, type="pv", params={"rated_power_kw": rated}),
        FixedSeedRandom(seed=0),
    )
    return pv


def _make_load(device_id: str = "load-1", rated: Decimal = Decimal("300")) -> LoadDevice:
    load = LoadDevice()
    load.initialize(
        ScenarioDevice(id=device_id, type="load", params={"rated_power_kw": rated}),
        FixedSeedRandom(seed=0),
    )
    return load


def _make_battery(device_id: str = "battery-1") -> BatteryDevice:
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
                "max_charge_kw": Decimal("50"),
                "max_discharge_kw": Decimal("50"),
                "charge_efficiency": Decimal("1"),
                "discharge_efficiency": Decimal("1"),
                "ramp_kw_per_s": Decimal("100"),
            },
        ),
        FixedSeedRandom(seed=0),
    )
    return battery


def _make_grid_connection(
    device_id: str = "grid-1",
) -> GridConnectionDevice:
    grid_dev = GridConnectionDevice()
    grid_dev.initialize(
        ScenarioDevice(
            id=device_id,
            type="grid_connection",
            params={
                "nominal_voltage_v": Decimal("400"),
                "max_import_kw": Decimal("100"),
                "max_export_kw": Decimal("100"),
            },
        ),
        FixedSeedRandom(seed=0),
    )
    return grid_dev


def _make_smart_meter(
    device_id: str = "meter-1",
    aggregate_device_ids: tuple[str, ...] = ("pv-1",),
) -> SmartMeterDevice:
    meter = SmartMeterDevice()
    meter.initialize(
        ScenarioDevice(
            id=device_id,
            type="smart_meter",
            params={
                "aggregate_device_ids": list(aggregate_device_ids),
                "aggregate_metric_name": "power_kw",
            },
        ),
        FixedSeedRandom(seed=0),
    )
    return meter


def _make_loop(
    *,
    devices: tuple[object, ...] = (),
    grid_model: GridModelBilanz | None = None,
    tick_ms: int = 1000,
) -> TickLoop:
    return TickLoop(
        run_id="run-6a",
        tick_ms=tick_ms,
        clock=FakeClock(),
        random=MersenneTwisterRandomPort(seed=42),
        scheduler=Scheduler(),
        devices=devices,  # type: ignore[arg-type]
        grid_model=grid_model,
    )


# ---------------------------------------------------------------------------
# Device-Iteration + Telemetry-Konkatenation
# ---------------------------------------------------------------------------


def test_tick_iterates_devices_and_collects_telemetry() -> None:
    pv = _make_pv()
    load = _make_load()
    loop = _make_loop(devices=(pv, load))
    result = loop.tick()
    sources = {p.source for p in result.emitted_telemetry}
    assert "pv" in sources
    assert "load" in sources


def test_tick_emits_telemetry_in_device_order() -> None:
    """Welle-6a: Telemetrie ist in Device-Konstruktor-Reihenfolge
    konkateniert."""
    pv = _make_pv()
    load = _make_load()
    loop = _make_loop(devices=(pv, load))
    result = loop.tick()
    sources_in_order = [p.source for p in result.emitted_telemetry]
    pv_idx = sources_in_order.index("pv")
    load_idx = sources_in_order.index("load")
    assert pv_idx < load_idx


def test_tick_without_devices_emits_empty_telemetry() -> None:
    """M1-Welle-4-Kompatibilitaet: ohne Devices bleibt emitted_telemetry
    leer."""
    loop = _make_loop()
    result = loop.tick()
    assert result.emitted_telemetry == ()


# ---------------------------------------------------------------------------
# Bilanz-Aggregation (ADR 0019 §2.2)
# ---------------------------------------------------------------------------


def test_grid_model_update_called_with_aggregated_power_kw() -> None:
    """pv=500 (gen), load=300 (load), battery=0 (storage),
    grid=0 (auto-default) -> imbalance = 500 - 300 - 0 + 0 = 200 kW."""
    pv = _make_pv(rated=Decimal("500"))
    load = _make_load(rated=Decimal("300"))
    battery = _make_battery()
    grid_dev = _make_grid_connection()
    bilanz = GridModelBilanz(config=_grid_model_config())
    loop = _make_loop(
        devices=(pv, load, battery, grid_dev),
        grid_model=bilanz,
    )
    loop.tick()
    assert bilanz.last_imbalance_kw == Decimal("200")


def test_grid_model_only_active_when_injected() -> None:
    """Ohne grid_model in Konstruktor wird die Bilanz nicht
    aktualisiert; Welle-6a-Default ist None."""
    pv = _make_pv()
    loop = _make_loop(devices=(pv,))  # grid_model=None
    # tick() darf nicht durchstuerzen; keine Bilanz-Aktualisierung.
    result = loop.tick()
    assert result.emitted_telemetry  # pv hat Telemetrie emittiert


def test_smart_meter_aggregated_power_kw_is_not_double_counted() -> None:
    """ADR 0015 §2.3 + ADR 0018 §2.4: SmartMeter emittiert
    `aggregated_power_kw` (nicht `power_kw`) — die Bilanz-
    Aggregation filtert via Metric-Name, sodass SmartMeter den
    `imbalance_kw` nicht verdoppelt."""
    pv = _make_pv(rated=Decimal("500"))
    meter = _make_smart_meter(aggregate_device_ids=("pv-1",))
    meter.attach_sources({"pv-1": pv})
    bilanz = GridModelBilanz(config=_grid_model_config())
    loop = _make_loop(
        devices=(pv, meter),
        grid_model=bilanz,
    )
    loop.tick()
    # pv emittiert power_kw=500; meter emittiert aggregated_power_kw=500
    # → nur PV trifft den generation-Bucket. imbalance = 500.
    assert bilanz.last_imbalance_kw == Decimal("500")


# ---------------------------------------------------------------------------
# Snapshot-Layout v2 (ADR 0015 §2.3)
# ---------------------------------------------------------------------------


def test_snapshot_includes_devices_and_grid_model_sub_keys() -> None:
    pv = _make_pv()
    battery = _make_battery()
    bilanz = GridModelBilanz(config=_grid_model_config())
    loop = _make_loop(devices=(pv, battery), grid_model=bilanz)
    loop.tick()
    snap = loop.snapshot()
    sub = snap["sub_snapshots"]
    assert isinstance(sub, Mapping)
    keys = set(sub.keys())
    assert "scheduler" in keys
    assert "random_root" in keys
    assert "devices.pv.pv-1" in keys
    assert "devices.battery.battery-1" in keys
    assert "grid_model" in keys


def test_snapshot_uses_typed_device_type_segment() -> None:
    """ADR 0015 §2.3: `devices.<device_type>.<device_id>` mit
    Typ-Segment fuer Welle-6b-from_snapshot-Dispatch."""
    pv = _make_pv("pv-42")
    loop = _make_loop(devices=(pv,))
    snap = loop.snapshot()
    sub = snap["sub_snapshots"]
    assert isinstance(sub, Mapping)
    assert "devices.pv.pv-42" in sub


def test_snapshot_version_is_two() -> None:
    """ADR 0015 §2.2: Welle 6a setzt TickLoop.snapshot()["version"]
    auf 2."""
    loop = _make_loop()
    snap = loop.snapshot()
    assert snap["version"] == 2


def test_snapshot_grid_model_sub_snapshot_carries_v2() -> None:
    """grid_model traegt ADR-0020-Snapshot-Version v2 (eigene
    Versionierung, unabhaengig von TickLoop-Snapshot-Version)."""
    bilanz = GridModelBilanz(config=_grid_model_config())
    loop = _make_loop(grid_model=bilanz)
    snap = loop.snapshot()
    sub = snap["sub_snapshots"]
    assert isinstance(sub, Mapping)
    grid_payload = sub["grid_model"]
    assert isinstance(grid_payload, Mapping)
    assert grid_payload["version"] == 2  # ADR 0020 §2.5 (LoadEvent/Profile)
