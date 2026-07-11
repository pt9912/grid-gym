"""`GridFaultEngine` — GridConnection-`voltage_drop`/`frequency_drop`-Faults
(M3 Welle 2, ADR 0022 + ADR 0025).

Seit ADR 0059 eine duenne Compat-Subklasse von
`ScenarioFaultEngine` (`scenario_fault_engine.py`): die gesamte
Scheduling-Logik lebt einmal in der generischen Engine. Diese
Klasse fixiert nur `supported_types` auf die GridConnection-Netz-
Faults (`voltage_drop` = GG-FAULT-005, `frequency_drop` =
GG-FAULT-004) und das Subsystem-Label.

**GridConnection-Constraint** (ADR 0022 §2.4): der Adapter
mutiert ueber `inject_fault` ausschliesslich `_pending_voltage_v`
(NICHT `_pending_power_kw`) — diese Verantwortung liegt im
`GridConnectionDevice.inject_fault`, nicht in der Engine.

Erhalten als benannte Klasse, weil die M3-Welle-2-Unit-/
Integration-Tests sie direkt konstruieren (Regressionsnetz +
ADR-0025-Vokabular). Konstruktor-Signatur unveraendert:
`GridFaultEngine(faults)`.
"""

from __future__ import annotations

from collections.abc import Sequence

from grid_gym.hexagon.core.domain.scenario import ScenarioFault
from grid_gym.hexagon.core.faults.scenario_fault_engine import ScenarioFaultEngine
from grid_gym.hexagon.core.faults.types import (
    FAULT_TYPE_FREQUENCY_DROP,
    FAULT_TYPE_VOLTAGE_DROP,
)


class GridFaultEngine(ScenarioFaultEngine):
    """Driven-Adapter fuer GridConnection-`voltage_drop`/`frequency_drop`-Faults.

    Andere Fault-Typen aus der `faults`-Liste werden ignoriert
    (No-Op) — die generische Basis filtert auf `supported_types`.
    """

    def __init__(self, faults: Sequence[ScenarioFault]) -> None:
        super().__init__(
            faults,
            frozenset({FAULT_TYPE_VOLTAGE_DROP, FAULT_TYPE_FREQUENCY_DROP}),
            "grid_connection",
        )
