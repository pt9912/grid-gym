"""`FaultSurfaceDevice`-Sub-Protocol (Slice 077 S2, ADR 0077 §2.5).

Sub-Protocol-Vertrag fuer Devices, die eine **operative Fault-Surface**
(`available`/`fault_status`) exponieren — die Read-Projektion der
`_<fault>_active`-Flags (ADR 0025). ADR 0013 §2.8 mandatiert das
Closed-Set-Pattern: **keine** Erweiterung der Base-`DeviceModel`-Surface;
die Surface kommt als separates Sub-Protocol (Geschwister von
`FaultInjectableDevice`, `hexagon/core/faults/_protocol.py`).

**Stand**: heute implementiert nur `BatteryDevice` die Surface (aus
`_cell_failure_active`, ADR 0077 §2.5). Der `TickLoop` sammelt je Tick
einen `DeviceStatus` (`hexagon/core/domain/device.py`) pro Implementer in
`TickResult.emitted_device_status`; der bess-ems-Publisher (ADR 0078)
liest daraus die Envelope-Felder `available`/`fault_status`.

**Warum kein Telemetrie-Punkt**: `available`/`fault_status` sind bewusst
**keine** `TelemetryPoint`s (ADR 0077 §2.5) — sie fliessen nicht durch die
Quality-Spine/Persistenz, sondern als separate Status-Projektion. Darum
diese Surface + der additive `TickResult`-Slot statt zweier Telemetrie-
Metriken.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from grid_gym.hexagon.core.devices._protocol import DeviceModel


@runtime_checkable
class FaultSurfaceDevice(DeviceModel, Protocol):
    """Sub-Protocol fuer Devices mit operativer Fault-Surface (ADR 0077 §2.5).

    Pflicht-Surface erweitert `DeviceModel` um zwei Read-Properties:

    - `available: bool` — `False` gdw. ein Fault aus dem `available`-Closed-
      Set aktiv ist (heute `cell_failure`), sonst `True`.
    - `fault_status: str` — aktiver Fault-Typ-String, sonst `"ok"`.

    `@runtime_checkable` erlaubt `isinstance(obj, FaultSurfaceDevice)` — die
    Pruefung erfasst das Vorhandensein der Member-Namen (nicht Signaturen);
    der `TickLoop` nutzt sie, um beim Status-Sammeln die fault-surface-
    faehigen Geraete zu selektieren (heute nur `BatteryDevice`). Post-init-
    Aufruf-Vertrag: der Loop sammelt Status **nach** `initialize()`, die
    Properties sind dann nebenwirkungsfrei lesbar.
    """

    @property
    def available(self) -> bool:
        """`False` gdw. ein Fault aus dem `available`-Closed-Set aktiv ist
        (ADR 0077 §2.5). Reine Projektion der `_<fault>_active`-Flags,
        nebenwirkungsfrei."""
        ...

    @property
    def fault_status(self) -> str:
        """Aktiver Fault-Typ-String (z. B. `"cell_failure"`), sonst `"ok"`
        (ADR 0077 §2.5). Reine Projektion der `_<fault>_active`-Flags."""
        ...
