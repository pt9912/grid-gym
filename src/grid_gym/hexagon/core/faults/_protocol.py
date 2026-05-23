"""`FaultInjectableDevice`-Sub-Protocol (M3 Welle 1, ADR 0022 §2.1).

Sub-Protocol-Vertrag fuer Devices, die Fault-Injection
unterstuetzen. ADR 0013 §2.8 mandatiert das Closed-Set-Pattern:
keine Erweiterung der Base-`DeviceModel`-Surface; M2-Geraete
bleiben `DeviceModel`-only und werden in M3 nicht implizit
fault-faehig.

**Welle-1-Stand**: dieses Modul liefert nur den Protocol-
Vertrag. Konkrete Implementer (`BatteryDevice` mit
`cell_failure`, `GridConnectionDevice` mit `voltage_drop`)
kommen in Welle 2 zusammen mit `BatteryFaultAdapter` /
`GridFaultAdapter` (siehe ADR 0022 §4 Reichweite).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from grid_gym.hexagon.core.devices._protocol import DeviceModel


@runtime_checkable
class FaultInjectableDevice(DeviceModel, Protocol):
    """Sub-Protocol fuer fault-faehige Devices (ADR 0022 §2.1).

    Pflicht-Surface erweitert `DeviceModel` um:

    - `inject_fault(fault_type, payload) -> None`: wendet einen
      Fault auf den internen Zustand des Geraets an.

    `@runtime_checkable` erlaubt `isinstance(obj,
    FaultInjectableDevice)` — die Pruefung erfasst das
    Vorhandensein der Methoden-Surface (nicht Signaturen). Pro-
    Geraete-Adapter (Welle 2) nutzen das fuer „kann dieses
    Device den vom Scenario verlangten Fault uebersetzen?"-
    Entscheidungen.
    """

    def inject_fault(
        self,
        fault_type: str,
        payload: Mapping[str, object],
    ) -> None:
        """Wendet einen Fault auf das Device an.

        `fault_type` ist die kanonische Type-Bezeichnung aus
        `ScenarioFault.type` (z. B. `"cell_failure"`,
        `"voltage_drop"`). `payload` traegt fault-typ-spezifische
        Parameter (z. B. `{"affected_cell_index": 3}`).

        Welle-2-Implementer entscheiden:
        - Welche `fault_type`-Werte sie verstehen (closed set
          pro Geraet).
        - Was unbekannte `fault_type`-Werte triggern (typisierter
          `FaultUnsupportedTypeError` o. ae. — Welle-2-Material).
        - Wie der State mutiert (z. B. Battery setzt
          `_cell_failure_active = True` mit Effekt auf
          `max_discharge_kw` in der naechsten `tick()`).

        Welle 1 hat keine konkrete Implementation; Aufrufe gehen
        ueber den `FaultPort`-Adapter (Welle 2).
        """
        ...

    def clear_fault(self, fault_type: str) -> None:
        """Recovery-Surface: setzt den `_<fault_type>_active`-Flag
        zurueck (M3 Welle 2 Review-Folge H-2, ADR 0025 §2.2).

        Symmetrisch zu `inject_fault`: der `FaultPort`-Adapter
        ruft `clear_fault(fault_type)` beim Window-Ende (auto-
        recover) oder beim `manual-recover-fault`-Command. Welle-
        2-Implementer dispatchen intern auf den Flag des
        jeweiligen Fault-Typs.

        Unbekannter `fault_type` wirft typisiert
        `FaultUnsupportedTypeError` (gleiche Closed-Set-Disziplin
        wie `inject_fault`). Idempotenz-Vertrag (ADR 0025 §2.4):
        wiederholte `clear_fault`-Aufrufe sind No-Op.
        """
        ...
