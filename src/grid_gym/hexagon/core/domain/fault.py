"""Fault-Typen-Konstanten — Single Source of Truth (ADR 0050 §2.2).

Verschoben aus `hexagon.core.faults.types` (M8-Welle-1, 041-C1), damit
HTTP-Request-Validation die Konstanten ueber die adapter-erlaubte
`hexagon.core.domain.*`-Surface konsumieren kann, ohne `core.faults` zu
importieren (`AC-ADAPTER-PURE`). `core.faults.types` re-exportiert von
hier; Devices und Fault-Engines konsumieren weiterhin dieselben Strings,
sodass der Single-Source-of-Truth-Vertrag erhalten bleibt.

Welle-2-Closed-Set: ein Typ pro Geraet (`cell_failure` fuer Battery,
`voltage_drop` fuer GridConnection). Welle 3+ erweitert den Set um
weitere Typen aus `GG-FAULT-005..010`.
"""

from __future__ import annotations

from typing import Final

FAULT_TYPE_CELL_FAILURE: Final[str] = "cell_failure"
"""Battery-Fault: Zell-Defekt mit reduzierter Discharge-Faehigkeit
(ADR 0025 §2.1)."""

FAULT_TYPE_VOLTAGE_DROP: Final[str] = "voltage_drop"
"""GridConnection-Fault: Spannungs-Einbruch ohne Power-Flow-Mutation
(ADR 0025 §2.1 + ADR 0022 §2.4 GridConnection-Constraint)."""
