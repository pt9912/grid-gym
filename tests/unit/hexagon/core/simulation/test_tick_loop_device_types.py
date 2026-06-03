"""Welle-6a-Review F3/F14: Unit-Tests fuer
`TickLoop.device_types`-Property.

Pinnt: (a) happy-path Mapping fuer alle 5 MVP-Geraetetypen,
(b) unbekannte DeviceModel-Klassen werden silent gedroppt
statt `TickLoopUnknownDeviceTypeError` zu propagieren
(`device_types` darf den POST-/faults-Handler nie mit 500
crashen lassen).
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.devices.pv import PvDevice
from grid_gym.hexagon.core.devices.smart_meter import SmartMeterDevice
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


def _battery() -> BatteryDevice:
    battery = BatteryDevice()
    battery.initialize(
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
        FixedSeedRandom(seed=0),
    )
    return battery


def _grid() -> GridConnectionDevice:
    grid = GridConnectionDevice()
    grid.initialize(
        ScenarioDevice(
            id="grid-1",
            type="grid_connection",
            params={
                "nominal_voltage_v": Decimal("400"),
                "max_import_kw": Decimal("100"),
                "max_export_kw": Decimal("100"),
            },
        ),
        FixedSeedRandom(seed=0),
    )
    return grid


def _pv() -> PvDevice:
    pv = PvDevice()
    pv.initialize(
        ScenarioDevice(id="pv-1", type="pv", params={"rated_power_kw": Decimal("50")}),
        FixedSeedRandom(seed=0),
    )
    return pv


def _load() -> LoadDevice:
    load = LoadDevice()
    load.initialize(
        ScenarioDevice(id="load-1", type="load", params={"rated_power_kw": Decimal("30")}),
        FixedSeedRandom(seed=0),
    )
    return load


def _smart_meter() -> SmartMeterDevice:
    sm = SmartMeterDevice()
    sm.initialize(
        ScenarioDevice(
            id="sm-1",
            type="smart_meter",
            params={
                "aggregate_device_ids": ("grid-1",),
                "aggregate_metric_name": "power_kw",
            },
        ),
        FixedSeedRandom(seed=0),
    )
    sm.attach_sources({"grid-1": _grid()})
    return sm


def _make_tick_loop(*devices: object) -> TickLoop:
    return TickLoop(
        run_id="welle-6a-device-types-test",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=tuple(devices),  # type: ignore[arg-type]
    )


def test_device_types_maps_all_five_mvp_device_classes() -> None:
    """Happy-path: alle 5 MVP-Geraetetypen kommen in der
    Mapping-Antwort vor mit dem richtigen `device_type`-String."""
    battery = _battery()
    pv = _pv()
    load = _load()
    grid = _grid()
    sm = _smart_meter()
    tick_loop = _make_tick_loop(battery, pv, load, grid, sm)
    assert tick_loop.device_types == {
        "battery-1": "battery",
        "pv-1": "pv",
        "load-1": "load",
        "grid-1": "grid_connection",
        "sm-1": "smart_meter",
    }


def test_device_types_returns_empty_for_no_devices() -> None:
    """Edge: leerer Devices-Tuple → leeres Mapping (keine
    Exception)."""
    tick_loop = _make_tick_loop()
    assert tick_loop.device_types == {}


def test_device_types_silently_drops_unknown_class() -> None:
    """Welle-6a-Review F3: ein nicht-gemapptes DeviceModel
    (z. B. Welle-7+/M3-Geraete-Klasse, die `_DEVICE_TYPE_BY_
    CLASS_NAME` noch nicht enthaelt) darf den POST-/faults-
    Handler nie mit 500 crashen. `device_types` skippt die
    unbekannte Klasse; der Handler bekommt das Mapping der
    bekannten Devices und antwortet sauber mit 422
    fault_unknown_target.

    Wir reuse hier eine bekannte Device-Klasse (Battery) und
    patchen die `_DEVICE_TYPE_BY_CLASS_NAME` so, dass diese
    Klasse darin nicht steht — das simuliert eine Welle-7+
    Device-Klasse, die noch keinen Mapping-Eintrag bekommen hat.
    """
    import grid_gym.hexagon.core.simulation.tick_loop as tick_loop_module

    battery = _battery()
    tick_loop = _make_tick_loop(battery)
    original_map = tick_loop_module._DEVICE_TYPE_BY_CLASS_NAME
    patched_map = {k: v for k, v in original_map.items() if k != "BatteryDevice"}
    try:
        tick_loop_module._DEVICE_TYPE_BY_CLASS_NAME = patched_map  # type: ignore[misc]
        # Battery-Klasse ist temporaer „unbekannt" → device_types
        # skippt sie sauber statt zu crashen.
        assert tick_loop.device_types == {}
    finally:
        tick_loop_module._DEVICE_TYPE_BY_CLASS_NAME = original_map  # type: ignore[misc]
