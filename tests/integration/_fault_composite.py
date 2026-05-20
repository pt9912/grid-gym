"""Test-Side `_CompositeFaultPort` fuer M3-Welle-2-
Integrationstests (Items 7-10 Review M-4).

Komponiert zwei `FaultPort`-Adapter (Battery + Grid) inline, weil
`TickLoop._fault_port` nur einen `FaultPort` pro Lauf akzeptiert
(ADR 0022 §2.5).

**Test-Only**: dieses Modul liegt unter `tests/integration/`, nicht
unter `src/`. Ein produktiver Composite-Pattern unter
`hexagon/core/faults/composite.py` ist Welle-3-Material (siehe
ADR 0025 Welle-3-Forward-Pointer); diese Datei dient nur dazu, die
Komposition zwischen mehreren Integrationstests zu teilen und im
gleichen Schritt die Reihenfolge der Sub-Ports zu pinnen
(Determinismus-Vertrag: Battery-zuerst vs. Grid-zuerst muessen
identische Telemetry erzeugen — ADR 0025 §2.4).

TODO(M3-Welle-3, Welle-2-Review-M-4): bei produktiver Composite-
Implementierung diesen Test-Helper durch den produktiven Adapter
ersetzen und die Datei loeschen.
"""

from __future__ import annotations

from collections.abc import Sequence

from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.faults import BatteryFaultAdapter, GridFaultAdapter


class CompositeFaultPort:
    """Inline-Komposition zweier `FaultPort`-Adapter
    (Welle-2-Test-Side; ADR 0025 Welle-3-Forward-Pointer)."""

    def __init__(
        self,
        battery_adapter: BatteryFaultAdapter,
        grid_adapter: GridFaultAdapter,
        *,
        battery_first: bool = True,
    ) -> None:
        """`battery_first=True` ist die Default-Reihenfolge fuer
        produktive Integrationstests. Der Kwarg existiert nur, damit
        `test_fault_composite_order_invariant_in_welle_2` beide
        Reihenfolgen vergleichen kann (Welle-2-Review M-2).
        """
        self._battery = battery_adapter
        self._grid = grid_adapter
        self._battery_first = battery_first

    def apply_active_faults(
        self,
        devices: Sequence[object],
        context: DeviceTickContext,
    ) -> None:
        if self._battery_first:
            self._battery.apply_active_faults(devices, context)
            self._grid.apply_active_faults(devices, context)
        else:
            self._grid.apply_active_faults(devices, context)
            self._battery.apply_active_faults(devices, context)
