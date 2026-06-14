"""`ScenarioFaultEngine` — generische Recovery-Engine fuer
Szenario-Faults (M8 Welle 2, ADR 0059; generalisiert ADR 0025).

Haelt die **einzige** Kopie der Fault-Scheduling-Logik, die zuvor
in `BatteryFaultEngine` und `GridFaultEngine` byte-identisch
dupliziert war. Parametrisiert ueber `supported_types` (die
Fault-Typen, fuer die diese Engine zustaendig ist) statt einer
Klasse pro Typ.

Schluessel-Erkenntnis (ADR 0059 §1): die Engine muss den
Fault-Typ nicht *kennen*. `device.inject_fault(fault.type,
payload)` reicht den Typ an das per `fault.target` aufgeloeste
Geraet durch, das ihn intern validiert
(`FaultUnsupportedTypeError` bei Mismatch). Die typ-spezifische
Verantwortung liegt im Geraet; die Engine ist reines Scheduling.

Pro Tick ruft `TickLoop.tick()` im Vor-Tick-Block-Schritt-A2
(ADR 0022 §2.4) genau einmal `apply_active_faults(devices,
context)`; die Engine:

1. Iteriert durch die (auf `supported_types` gefilterte)
   `scenario.faults`-Liste.
2. Aktivitaets-Check pro Fault: half-open `[start, end)`
   (ADR 0025 §2.3).
3. Target-Resolution + `isinstance(d, FaultInjectableDevice)`-
   Filter (ADR 0022 §2.2 + ADR 0025 §2.2).
4. Idempotenter `device.inject_fault(...)` nur beim Uebergang
   inactive → active (ADR 0025 §2.4).
5. Recovery (`device.clear_fault(fault.type)`) beim Uebergang
   active → inactive; manual-via-command per
   `_pending_manual_recoveries`-Set.

State-Lokalisation (ADR 0025 §2.2): Engine haelt
`_active_faults: dict[(fault_id, target_device_id), bool]`
(True = aktiv injiziert); Device haelt nur das Physik-Flag.
"""

from __future__ import annotations

from collections.abc import Sequence

from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioFault
from grid_gym.hexagon.core.errors import FaultUnknownReferenceError
from grid_gym.hexagon.core.faults._protocol import FaultInjectableDevice


class ScenarioFaultEngine:
    """Generischer Driven-Adapter (`FaultPort`) fuer Szenario-Faults.

    Konstruktor-Injection von `scenario.faults` + der Menge
    `supported_types`, fuer die diese Engine zustaendig ist; alle
    uebrigen Fault-Typen aus der Liste werden ignoriert (No-Op).
    `subsystem` ist nur ein diagnostisches Label.
    """

    def __init__(
        self,
        faults: Sequence[ScenarioFault],
        supported_types: frozenset[str],
        subsystem: str = "scenario",
    ) -> None:
        self._subsystem = subsystem
        # Auf `supported_types` filtern + mit deterministischer ID
        # belegen. ID-Konvention (ADR 0025 §2.1 + Welle-2-Review-
        # Folge M-2): `fault-{i}` mit Original-Scenario-Index `i`
        # (nicht gefilterter Index) -- stabil ueber Fault-Typ-
        # Hinzufuegungen.
        self._faults: list[tuple[str, ScenarioFault]] = [
            (f"fault-{i}", fault) for i, fault in enumerate(faults) if fault.type in supported_types
        ]
        # ADR 0025 §2.2: Scheduling-State.
        # Key: (fault_id, target_device_id); Value: bool active
        self._active_faults: dict[tuple[str, str], bool] = {}
        # ADR 0025 §2.1: manual-via-command-Set fuer manuelle
        # Recovery-Trigger. Die Command-Verarbeitung selbst ist
        # Welle-3+ (AgentBus ruft `register_manual_recovery`).
        self._pending_manual_recoveries: set[tuple[str, str]] = set()

    def apply_active_faults(
        self,
        devices: Sequence[object],
        context: DeviceTickContext,
    ) -> None:
        """`FaultPort.apply_active_faults`-Implementation.

        Welle-1-Port-Surface ist `Sequence[object]` (AC-PORTS-NO-OUT,
        ADR 0022 §2.2 Welle-1-Review-Schaerfung). Engine filtert
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
                    target.clear_fault(fault.type)
                self._active_faults[key] = False
                self._pending_manual_recoveries.discard(key)
                continue

            if in_window and not currently_active:
                if target is not None:
                    target.inject_fault(fault.type, fault.payload)
                self._active_faults[key] = True
            elif not in_window and currently_active:
                if target is not None:
                    target.clear_fault(fault.type)
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
        `(fault_id, target_device_id)`-Kombination nicht in der
        Engine bekannt ist (Validierung gegen die Konstruktor-
        Fault-Liste).
        """
        known = any(
            fid == fault_id and fault.target == target_device_id for fid, fault in self._faults
        )
        if not known:
            raise FaultUnknownReferenceError(fault_id, target_device_id)
        self._pending_manual_recoveries.add((fault_id, target_device_id))
