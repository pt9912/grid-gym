"""Fault-Typen-Konstanten — Re-Export (Single Source: `core.domain.fault`).

Die Konstanten sind mit 041-C1 (M8-Welle-1, ADR 0050 §2.2) nach
`hexagon.core.domain.fault` verschoben, damit HTTP-Adapter sie ueber die
adapter-erlaubte Domain-Surface konsumieren koennen, ohne `core.faults`
zu importieren (`AC-ADAPTER-PURE`). Dieses Modul bleibt als Re-Export
erhalten, damit Devices (`inject_fault`/`clear_fault`-Dispatch) und
Fault-Engines (Filter-Liste im Konstruktor) unveraendert
`from ...core.faults.types import FAULT_TYPE_*` nutzen koennen.
"""

from __future__ import annotations

from grid_gym.hexagon.core.domain.fault import (
    FAULT_TYPE_CELL_FAILURE,
    FAULT_TYPE_CONNECTION_LOSS,
    FAULT_TYPE_GENSET_FAULT,
    FAULT_TYPE_VOLTAGE_DROP,
    FAULT_TYPE_WINDING_FAULT,
)

__all__ = [
    "FAULT_TYPE_CELL_FAILURE",
    "FAULT_TYPE_CONNECTION_LOSS",
    "FAULT_TYPE_GENSET_FAULT",
    "FAULT_TYPE_VOLTAGE_DROP",
    "FAULT_TYPE_WINDING_FAULT",
]
