"""Fault-Typen-Konstanten (M3 Welle 2 Review-Folge L-4).

Zentrale Definition der Fault-Type-Strings. Welle-2-Closed-Set:
ein einziger Typ pro Geraet (`cell_failure` fuer Battery,
`voltage_drop` fuer GridConnection). Welle 3+ erweitert den Set
um weitere Typen aus `GG-FAULT-005..010` (z. B.
`overcurrent`, `temperature_runaway`, `island_mode_failure`).

Diese Konstanten werden von Devices (`inject_fault`/
`clear_fault`-Dispatch) und Adaptern (Filter-Liste im
Konstruktor) gleichermassen konsumiert. Konstante-Drift
vermeidet die typische "Magic-String"-Falle.
"""

from __future__ import annotations

from typing import Final

FAULT_TYPE_CELL_FAILURE: Final[str] = "cell_failure"
"""Battery-Fault: Zell-Defekt mit reduzierter Discharge-Faehigkeit
(ADR 0025 §2.1)."""

FAULT_TYPE_VOLTAGE_DROP: Final[str] = "voltage_drop"
"""GridConnection-Fault: Spannungs-Einbruch ohne Power-Flow-Mutation
(ADR 0025 §2.1 + ADR 0022 §2.4 GridConnection-Constraint)."""
