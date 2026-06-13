"""`FaultPort` Driven-Port (M3 Welle 1, ADR 0022 §2.2).

Driven-Port-Vertrag fuer die Fault-Injection-Orchestrierung.
TickLoop ruft pro Tick genau einen Adapter-Aufruf an, der die
gesamte Entscheidung — welcher Fault wann auf welches Device —
kapselt.

**Welle-1-Stand**: dieses Modul liefert nur den Protocol-
Vertrag. Konkrete Adapter (`BatteryFaultEngine`,
`GridFaultEngine`) leben in Welle 2 unter
`adapters/driven/fault_*/` (siehe ADR 0022 §4 Reichweite).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from grid_gym.hexagon.core.domain.device import DeviceTickContext

# AC-PORTS-NO-OUT: `hexagon/ports/` darf NICHT von
# `hexagon/core/devices/` importieren. Die Adapter-Welle-2-
# Implementer (`BatteryFaultEngine` u. ae.) typisieren die
# `devices`-Liste intern strenger (z. B. `Sequence[DeviceModel]`)
# und filtern per `isinstance(d, FaultInjectableDevice)`. Welle-1-
# Port-Surface bleibt deshalb structural (`Sequence[object]`).


@runtime_checkable
class FaultPort(Protocol):
    """Driven-Port fuer Fault-Injection-Orchestrierung
    (ADR 0022 §2.2).

    Pflicht-Surface:

    - `apply_active_faults(devices, context) -> None`: wendet
      alle bei dieser Tick aktiven Faults auf die passenden
      Geraete an.

    Adapter-Verantwortung (Welle 2):

    1. Iteration durch die `scenario.faults`-Liste (ueber
       Konstruktor-Injection).
    2. Aktivitaets-Check pro Fault: ist
       `context.simulation_time in [start_simulation_time,
       start_simulation_time + duration_ms)`?
    3. Target-Resolution: finde Device mit passender
       `device_id` in `devices`.
    4. `isinstance(device, FaultInjectableDevice)`-Check.
    5. Aufruf `device.inject_fault(fault.type, fault.payload)`.

    Welle 1 macht keinen dieser Schritte; nur der Protocol-
    Vertrag steht. TickLoop akzeptiert `fault_port: FaultPort |
    None = None` und skippt den Hook bei `None`.
    """

    def apply_active_faults(
        self,
        devices: Sequence[object],
        context: DeviceTickContext,
    ) -> None:
        """Wendet alle bei dieser Tick aktiven Faults an.

        Wird von `TickLoop.tick()` im Vor-Tick-Block nach
        `_consume_load_inputs_into` und vor erster
        `_run_device_iteration` aufgerufen (ADR 0022 §2.4).
        Order-Pflicht: Faults werden VOR `device.tick(...)`
        angewandt, damit Devices in derselben Tick auf den
        gemutateten State reagieren koennen.

        Determinismus-Vertrag (analog ADR 0021 §2.2/§2.9):
        gleicher Seed + gleiche Fault-Sequenz → byte-identische
        State-Mutationen.

        Empty-`devices`-Vertrag (Welle-1-Review L-7): leere
        Sequenz ist zulaessig und produziert einen No-Op.
        Adapter muessen das absorbieren, ohne zu werfen
        (typischerweise indem die Iteration ueber `scenario.faults`
        einfach kein Match findet).

        Exception-Propagation (ADR 0022 §2.4): Adapter-
        Exceptions propagieren ungewrappt aus `TickLoop.tick()`
        heraus. TickLoop fuegt kein try/except hinzu — Welle-2-
        Adapter entscheiden selbst, ob sie Fail-Fast werfen
        oder einen Alarm-Pfad ueber Welle-3-/Welle-5-
        Observability emittieren.

        GridConnection-Constraint (ADR 0022 §2.4): Faults auf
        `GridConnectionDevice` duerfen NICHT `_pending_power_kw`
        oder `_current_power_kw` mutieren — der Welle-6b-Auto-
        Schluss (ADR 0021 §2.7) ueberschreibt diese Felder in
        derselben Tick. Grid-Faults muessen Voltage-/Frequency-
        State mutieren.
        """
        ...
