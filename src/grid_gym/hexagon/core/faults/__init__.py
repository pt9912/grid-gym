"""Fault-Injection-Core (M3 Welle 1, ADR 0022).

Re-exportiert die Sub-Protocol-Surface
(`FaultInjectableDevice`) als oeffentliches Paket-Interface.
Konkrete Fault-Engine-Logik (Aktivitaets-Checks, Target-
Resolution, Type-Dispatch) lebt als Core-Fault-Engines
(`BatteryFaultEngine`/`GridFaultEngine`) in diesem Paket
(ADR 0051 — `FaultPort`-Implementierung im Core, kein Outer-Ring-
Adapter trotz historischem `*FaultAdapter`-Namen).
"""

from grid_gym.hexagon.core.faults._protocol import FaultInjectableDevice
from grid_gym.hexagon.core.faults.battery_fault_engine import BatteryFaultEngine
from grid_gym.hexagon.core.faults.grid_fault_engine import GridFaultEngine

__all__ = ["BatteryFaultEngine", "FaultInjectableDevice", "GridFaultEngine"]
