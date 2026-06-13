"""RunExecutionPort — Driving-Port fuer Run-Ausfuehrung (ADR 0050 §2.3).

Kleine strukturelle Surface, gegen die die HTTP-Adapter (Registry,
Driver, Healthcheck, Router) typisieren, statt gegen den konkreten
`TickLoop` aus `hexagon.core.simulation`. `TickLoop` implementiert die
Surface strukturell (Protocol, kein expliziter Vererbungs-Zwang); der
Adapter sieht nur noch den Port und importiert `core.simulation` nicht
mehr (`AC-ADAPTER-PURE`, 041-C2).

`devices` ist bewusst `tuple[object, ...]`, damit Adapter keine
`core.devices.DeviceModel` importieren muessen — Konsumenten casten auf
ihr eigenes schicht-lokales View-Protocol.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from grid_gym.hexagon.core.domain.replay import ReplayDelta
from grid_gym.hexagon.core.domain.run import ControlAction, RunStatus
from grid_gym.hexagon.core.domain.tick_result import TickResult


class RunExecutionPort(Protocol):
    """Strukturelle Run-Ausfuehrungs-Surface (ADR 0050 §2.3).

    Read-only-Properties + drei Verben (`request`/`tick`/`finalize`).
    Die Member-Auswahl deckt exakt die reale Adapter-Nutzung
    (Registry-Lookup, Driver-Lifecycle, Healthcheck-Mess, Run-Status-
    und Geraete-Lookup der Router).
    """

    @property
    def run_id(self) -> str: ...

    @property
    def tick_ms(self) -> int: ...

    @property
    def tick_count(self) -> int: ...

    @property
    def control_state(self) -> RunStatus: ...

    @property
    def device_types(self) -> Mapping[str, str]: ...

    @property
    def devices(self) -> tuple[object, ...]: ...

    def request(self, action: ControlAction) -> None: ...

    def tick(self) -> TickResult: ...

    def finalize(self) -> tuple[ReplayDelta, ...]: ...
