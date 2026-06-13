"""`GridFaultEngine` — Recovery-Engine fuer GridConnection-Faults
(M3 Welle 2, ADR 0022 + ADR 0025).

Spiegelt das `BatteryFaultEngine`-Pattern (`battery_fault_engine.py`),
spezialisiert auf den `voltage_drop`-Fault-Typ. Pro Tick ruft
`TickLoop.tick()` im Vor-Tick-Block-Schritt-A2 (ADR 0022 §2.4)
genau einmal `apply_active_faults(devices, context)`; der Adapter:

1. Iteriert durch die konstruierte `scenario.faults`-Liste
   (gefiltert nach `voltage_drop`).
2. Aktivitaets-Check pro Fault: half-open `[start, end)`
   (ADR 0025 §2.3).
3. Target-Resolution + `isinstance(d, FaultInjectableDevice)`-
   Filter.
4. Idempotenter `device.inject_fault(...)` nur beim Uebergang
   inactive → active (ADR 0025 §2.4).
5. Recovery (`device.clear_fault`) beim Uebergang active → inactive.

**GridConnection-Constraint** (ADR 0022 §2.4): der Adapter
mutiert ueber `inject_fault` ausschliesslich `_pending_voltage_v`
(NICHT `_pending_power_kw` — der Welle-6b-Auto-Schluss in
Schritt C ueberschreibt das in derselben Tick).

State-Lokalisation (ADR 0025 §2.2): Adapter haelt
`_active_faults: dict[(fault_id, target_device_id), bool]`
(True = aktiv injiziert); Device haelt nur das Physik-Flag
(`_voltage_drop_active`).
"""

from __future__ import annotations

from collections.abc import Sequence

from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioFault
from grid_gym.hexagon.core.errors import (
    FaultUnknownReferenceError,
    FaultUnsupportedTypeError,
)
from grid_gym.hexagon.core.faults._protocol import FaultInjectableDevice
from grid_gym.hexagon.core.faults.types import FAULT_TYPE_VOLTAGE_DROP


class GridFaultEngine:
    """Driven-Adapter fuer GridConnection-`voltage_drop`-Faults.

    Konstruktor-Injection von `scenario.faults` reicht; der
    Adapter filtert intern nach `type == "voltage_drop"`. Andere
    Fault-Typen aus der Liste werden ignoriert (Welle-2-Closed-
    Set; Battery-Faults gehoeren in den `BatteryFaultEngine`).
    """

    def __init__(self, faults: Sequence[ScenarioFault]) -> None:
        # Nur voltage_drop-Faults filtern. ID-Konvention
        # (ADR 0025 §2.1 + Welle-2-Review-Folge M-2): `fault-{i}`
        # mit Original-Scenario-Index `i` (nicht gefilterter
        # Index) — stabil ueber Fault-Typ-Hinzufuegungen in Welle 3+.
        self._faults: list[tuple[str, ScenarioFault]] = [
            (f"fault-{i}", fault)
            for i, fault in enumerate(faults)
            if fault.type == FAULT_TYPE_VOLTAGE_DROP
        ]
        # ADR 0025 §2.2: Scheduling-State.
        # Key: (fault_id, target_device_id); Value: bool active
        self._active_faults: dict[tuple[str, str], bool] = {}
        # ADR 0025 §2.1: manual-via-command-Set fuer manuelle
        # Recovery-Trigger.
        self._pending_manual_recoveries: set[tuple[str, str]] = set()

    def apply_active_faults(
        self,
        devices: Sequence[object],
        context: DeviceTickContext,
    ) -> None:
        """`FaultPort.apply_active_faults`-Implementation.

        Welle-1-Port-Surface ist `Sequence[object]` (AC-PORTS-NO-OUT,
        ADR 0022 §2.2 Welle-1-Review-Schaerfung). Adapter filtert
        intern nach `FaultInjectableDevice`.
        """
        # Device-Lookup (intern strenger getypt).
        device_by_id: dict[str, FaultInjectableDevice] = {}
        for device in devices:
            if isinstance(device, FaultInjectableDevice):
                device_by_id[device.device_id] = device

        for fault_id, fault in self._faults:
            key = (fault_id, fault.target)
            window_end = fault.start_simulation_time + fault.duration_ms
            # ADR 0025 §2.3: half-open [start, end).
            in_window = fault.start_simulation_time <= context.simulation_time < window_end
            manual_recover = key in self._pending_manual_recoveries
            currently_active = self._active_faults.get(key, False)

            target = device_by_id.get(fault.target)

            if manual_recover:
                # ADR 0025 §2.1 Prioritaet: Manual-Override schlaegt
                # Auto-Schedule.
                if target is not None and currently_active:
                    target.clear_fault(FAULT_TYPE_VOLTAGE_DROP)
                self._active_faults[key] = False
                self._pending_manual_recoveries.discard(key)
                continue

            if in_window and not currently_active:
                if target is not None:
                    target.inject_fault(fault.type, fault.payload)
                self._active_faults[key] = True
            elif not in_window and currently_active:
                if target is not None:
                    target.clear_fault(FAULT_TYPE_VOLTAGE_DROP)
                self._active_faults[key] = False

    def register_manual_recovery(
        self,
        fault_id: str,
        target_device_id: str,
    ) -> None:
        """ADR 0025 §2.1: registriert eine
        `manual-recover-fault`-Anforderung fuer den naechsten
        `apply_active_faults`-Aufruf.

        Wirft `FaultUnknownReferenceError`, wenn die
        `(fault_id, target_device_id)`-Kombination nicht im
        Adapter bekannt ist (Validierung gegen die Konstruktor-
        Fault-Liste).
        """
        known = any(
            fid == fault_id and fault.target == target_device_id for fid, fault in self._faults
        )
        if not known:
            raise FaultUnknownReferenceError(fault_id, target_device_id)
        self._pending_manual_recoveries.add((fault_id, target_device_id))

    @staticmethod
    def assert_supported_type(fault_type: str) -> None:
        """Helper fuer Aufrufer, die vor `inject_fault` typ-pruefen
        wollen. Wirft `FaultUnsupportedTypeError` bei nicht-
        voltage_drop-Typen.
        """
        if fault_type != FAULT_TYPE_VOLTAGE_DROP:
            raise FaultUnsupportedTypeError("grid_connection", fault_type)
