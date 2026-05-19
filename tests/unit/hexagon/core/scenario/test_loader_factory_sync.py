"""Sync-Test fuer `_DEVICE_FACTORIES` (loader.py) vs.
`_DEVICE_TYPE_BY_CLASS_NAME` (tick_loop.py).

Welle-6b-Review L-1: beide Maps muessen mit jedem neuen DeviceModel
parallel gepflegt werden. Eine Drift faellt sonst erst zur
Snapshot-Laufzeit auf (`TickLoopUnknownDeviceTypeError`).
"""

from __future__ import annotations

from grid_gym.hexagon.core.scenario.loader import _DEVICE_FACTORIES
from grid_gym.hexagon.core.simulation.tick_loop import _DEVICE_TYPE_BY_CLASS_NAME


def test_factory_and_snapshot_maps_cover_same_device_types() -> None:
    """Beide Maps muessen das gleiche Set von `device_type`-Strings
    kennen — die eine via `ScenarioDevice.type` → Factory, die
    andere via Class-Name → `device_type` fuer den Sub-Snapshot-
    Schluessel `devices.<device_type>.<device_id>`."""
    factory_types = set(_DEVICE_FACTORIES)
    snapshot_types = set(_DEVICE_TYPE_BY_CLASS_NAME.values())
    assert factory_types == snapshot_types


def test_factory_class_names_match_snapshot_class_keys() -> None:
    """Die Klassen, die `_DEVICE_FACTORIES` liefert, muessen unter
    ihrem Class-Name in `_DEVICE_TYPE_BY_CLASS_NAME` registriert
    sein und zum gleichen `device_type`-String mappen."""
    for type_str, factory in _DEVICE_FACTORIES.items():
        class_name = factory.__name__
        assert class_name in _DEVICE_TYPE_BY_CLASS_NAME, (
            f"Factory-Klasse {class_name!r} fehlt in "
            f"_DEVICE_TYPE_BY_CLASS_NAME (Drift-Risiko Welle-6b-Review L-1)."
        )
        assert _DEVICE_TYPE_BY_CLASS_NAME[class_name] == type_str
