"""Fault-Injection-Core (M3 Welle 1, ADR 0022).

Re-exportiert die Sub-Protocol-Surface
(`FaultInjectableDevice`) als oeffentliches Paket-Interface.
Konkrete Fault-Engine-Logik (Aktivitaets-Checks, Target-
Resolution, Type-Dispatch) lebt als generische Core-Fault-Engine
(`ScenarioFaultEngine`, ADR 0059) in diesem Paket; die historischen
typ-spezifischen Engines (`BatteryFaultEngine`/`GridFaultEngine`)
sind seither duenne Compat-Subklassen
(ADR 0051 — `FaultPort`-Implementierung im Core, kein Outer-Ring-
Adapter trotz historischem `*FaultAdapter`-Namen).
"""

from grid_gym.hexagon.core.faults._protocol import FaultInjectableDevice
from grid_gym.hexagon.core.faults.battery_fault_engine import BatteryFaultEngine
from grid_gym.hexagon.core.faults.grid_fault_engine import GridFaultEngine
from grid_gym.hexagon.core.faults.scenario_fault_engine import ScenarioFaultEngine

__all__ = [
    "BatteryFaultEngine",
    "FaultInjectableDevice",
    "GridFaultEngine",
    "ScenarioFaultEngine",
]
