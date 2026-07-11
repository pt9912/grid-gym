"""Fault-Typen-Konstanten — Single Source of Truth (ADR 0050 §2.2).

Verschoben aus `hexagon.core.faults.types` (M8-Welle-1, 041-C1), damit
HTTP-Request-Validation die Konstanten ueber die adapter-erlaubte
`hexagon.core.domain.*`-Surface konsumieren kann, ohne `core.faults` zu
importieren (`AC-ADAPTER-PURE`). `core.faults.types` re-exportiert von
hier; Devices und Fault-Engines konsumieren weiterhin dieselben Strings,
sodass der Single-Source-of-Truth-Vertrag erhalten bleibt.

Welle-2-Closed-Set: ein Typ pro Geraet (`cell_failure` fuer Battery,
`voltage_drop` fuer GridConnection). Welle 3+ erweitert den Set um
weitere Typen aus `GG-FAULT-005..010`. M8-Welle-2a ergaenzt
`connection_loss` fuer den EV-Charger (`GG-DEV-015`, ADR 0055 §2.7).
"""

from __future__ import annotations

from typing import Final

FAULT_TYPE_CELL_FAILURE: Final[str] = "cell_failure"
"""Battery-Fault: Zell-Defekt mit reduzierter Discharge-Faehigkeit
(ADR 0025 §2.1)."""

FAULT_TYPE_VOLTAGE_DROP: Final[str] = "voltage_drop"
"""GridConnection-Fault: Spannungs-Einbruch ohne Power-Flow-Mutation
(ADR 0025 §2.1 + ADR 0022 §2.4 GridConnection-Constraint). Erfuellt
GG-FAULT-005 (Spannungseinbrueche)."""

FAULT_TYPE_FREQUENCY_DROP: Final[str] = "frequency_drop"
"""GridConnection-Fault: Netz-Frequenzabfall ohne Power-Flow-Mutation —
Frequenz-Zwilling zu `voltage_drop` (ADR 0025 §2.1 + ADR 0022 §2.4
GridConnection-Constraint). Payload traegt `frequency_hz` (Absolutwert)
oder `delta_hz` (Abzug vom Nennwert). Erfuellt GG-FAULT-004
(Frequenzabfaelle): Grid-Telemetrie `frequency_hz` + Alarm."""

FAULT_TYPE_CONNECTION_LOSS: Final[str] = "connection_loss"
"""EV-Charger-Fault: Verbindungsabriss waehrend der Session — solange
aktiv ist `power_kw` hart `0` (SoC eingefroren), analog `unplugged`
(M8-Welle-2a, ADR 0055 §2.7)."""

FAULT_TYPE_WINDING_FAULT: Final[str] = "winding_fault"
"""Transformer-Fault: Schutzausloesung (Ueberlast/Kurzschluss) — solange
aktiv ist der Transformator isoliert/de-energized, `primary_power`/
`secondary_power`/`loss` hart `0` (M8-Welle-2b, ADR 0056 §2.6)."""

FAULT_TYPE_GENSET_FAULT: Final[str] = "genset_fault"
"""Diesel-Generator-Fault: Schutzausloesung — solange aktiv ist der
Genset gestoppt, `power_kw` hart `0`, kein Kraftstoffverbrauch
(M8-Welle-2d, ADR 0058 §2.7)."""
