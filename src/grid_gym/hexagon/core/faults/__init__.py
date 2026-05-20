"""Fault-Injection-Core (M3 Welle 1, ADR 0022).

Re-exportiert die Sub-Protocol-Surface
(`FaultInjectableDevice`) als oeffentliches Paket-Interface.
Konkrete Fault-Engine-Logik (Aktivitaets-Checks, Target-
Resolution, Type-Dispatch) lebt in den `FaultPort`-Adaptern
unter `adapters/driven/fault_*/` (Welle 2).
"""

from grid_gym.hexagon.core.faults._protocol import FaultInjectableDevice
from grid_gym.hexagon.core.faults.battery_fault_adapter import BatteryFaultAdapter

__all__ = ["BatteryFaultAdapter", "FaultInjectableDevice"]
