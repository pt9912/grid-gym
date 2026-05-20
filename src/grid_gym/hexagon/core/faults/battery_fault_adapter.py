"""`BatteryFaultAdapter` — Recovery-Engine fuer Battery-Faults
(M3 Welle 2, ADR 0022 + ADR 0025).

Implementiert das `FaultPort`-Protocol fuer den `cell_failure`-
Fault-Typ. Pro Tick ruft `TickLoop.tick()` im Vor-Tick-Block-
Schritt-A2 (ADR 0022 §2.4) genau einmal
`apply_active_faults(devices, context)`; der Adapter:

1. Iteriert durch die konstruierte `scenario.faults`-Liste.
2. Aktivitaets-Check pro Fault: half-open `[start, end)`
   (ADR 0025 §2.3).
3. Target-Resolution + `isinstance(d, FaultInjectableDevice)`-
   Filter (ADR 0022 §2.2 + ADR 0025 §2.2).
4. Idempotenter `device.inject_fault(...)` nur beim Uebergang
   inactive → active (ADR 0025 §2.4).
5. Recovery beim Uebergang active → inactive
   (auto-recover-after-N-ticks per Window-Ende; manual-via-
   command per `_pending_manual_recoveries`-Set).

State-Lokalisation (ADR 0025 §2.2): Adapter haelt
`_active_faults: dict[(fault_id, target_device_id), bool]`
(True = aktiv injiziert); Device haelt nur das Physik-Flag.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from grid_gym.hexagon.core.devices._protocol import DeviceModel
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioFault
from grid_gym.hexagon.core.errors import (
    FaultUnknownReferenceError,
    FaultUnsupportedTypeError,
)
from grid_gym.hexagon.core.faults._protocol import FaultInjectableDevice

_SUPPORTED_FAULT_TYPE = "cell_failure"
"""ADR 0025 §2.1 Closed-Set fuer Welle 2."""


class BatteryFaultAdapter:
    """Driven-Adapter fuer Battery-`cell_failure`-Faults.

    Konstruktor-Injection von `scenario.faults` reicht; der
    Adapter filtert intern nach `type == "cell_failure"`. Andere
    Fault-Typen aus der Liste werden ignoriert (Welle-2-Closed-
    Set; Grid-Faults gehoeren in den `GridFaultAdapter`).
    """

    def __init__(self, faults: Sequence[ScenarioFault]) -> None:
        # Nur cell_failure-Faults filtern + mit deterministischer
        # ID belegen (`f"fault-{i}"` aus Welle-2-ADR-0025-Konvention).
        self._faults: list[tuple[str, ScenarioFault]] = [
            (f"fault-{i}", fault)
            for i, fault in enumerate(faults)
            if fault.type == _SUPPORTED_FAULT_TYPE
        ]
        # ADR 0025 §2.2: Scheduling-State.
        # Key: (fault_id, target_device_id); Value: bool active
        self._active_faults: dict[tuple[str, str], bool] = {}
        # ADR 0025 §2.1: manual-via-command-Set fuer manuelle
        # Recovery-Trigger. Welle 2 implementiert die Command-
        # Verarbeitung nicht direkt im Adapter — Welle 3+ AgentBus
        # ruft `register_manual_recovery(fault_id, target)`.
        self._pending_manual_recoveries: set[tuple[str, str]] = set()

    def apply_active_faults(
        self,
        devices: Sequence[object],
        context: DeviceTickContext,
    ) -> None:
        """`FaultPort.apply_active_faults`-Implementation.

        Welle-1-Port-Surface ist `Sequence[object]` (AC-PORTS-NO-OUT,
        ADR 0022 §2.2 Welle-1-Review-Schaerfung). Adapter cast +
        filtert intern nach `FaultInjectableDevice`.
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
                    target._clear_cell_failure()  # type: ignore[attr-defined]
                self._active_faults[key] = False
                self._pending_manual_recoveries.discard(key)
                continue

            if in_window and not currently_active:
                if target is not None:
                    target.inject_fault(fault.type, fault.payload)
                self._active_faults[key] = True
            elif not in_window and currently_active:
                if target is not None:
                    target._clear_cell_failure()  # type: ignore[attr-defined]
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
        cell_failure-Typen.
        """
        if fault_type != _SUPPORTED_FAULT_TYPE:
            raise FaultUnsupportedTypeError("battery", fault_type)


# Suppress unused-warning fuer `cast` (welle-1-Pattern fuer
# Type-Guards, falls Welle-3-Refactor das nutzt).
_ = cast
