"""`BatteryFaultEngine` — Battery-`cell_failure`-Faults
(M3 Welle 2, ADR 0022 + ADR 0025).

Seit ADR 0059 eine duenne Compat-Subklasse von
`ScenarioFaultEngine` (`scenario_fault_engine.py`): die gesamte
Scheduling-Logik (Fenster-Check, Target-Resolution, idempotenter
inject/clear, manual-recovery) lebt einmal in der generischen
Engine. Diese Klasse fixiert nur `supported_types` auf
`cell_failure` und das Subsystem-Label.

Erhalten als benannte Klasse, weil die M3-Welle-2-Unit-/
Integration-Tests sie direkt konstruieren (Regressionsnetz +
ADR-0025-Vokabular). Konstruktor-Signatur unveraendert:
`BatteryFaultEngine(faults)`.
"""

from __future__ import annotations

from collections.abc import Sequence

from grid_gym.hexagon.core.domain.scenario import ScenarioFault
from grid_gym.hexagon.core.faults.scenario_fault_engine import ScenarioFaultEngine
from grid_gym.hexagon.core.faults.types import FAULT_TYPE_CELL_FAILURE


class BatteryFaultEngine(ScenarioFaultEngine):
    """Driven-Adapter fuer Battery-`cell_failure`-Faults.

    Andere Fault-Typen aus der `faults`-Liste werden ignoriert
    (No-Op) — die generische Basis filtert auf `supported_types`.
    """

    def __init__(self, faults: Sequence[ScenarioFault]) -> None:
        super().__init__(faults, frozenset({FAULT_TYPE_CELL_FAILURE}), "battery")
