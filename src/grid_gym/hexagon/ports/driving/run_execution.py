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

Stub-Form: Docstring + `...` auf eigener Zeile (nicht inline) wie
`alarm_stream`/`telemetry_stream` — so greift der Coverage-Exclude
`^\\s*\\.\\.\\.\\s*$` und `ruff format` kollabiert den Body nicht zu
inline-`...` (das ungedeckte Branch-Kanten erzeugte).
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
    def run_id(self) -> str:
        """Stabile Lauf-Identitaet (`GG-DATA-001`)."""
        ...

    @property
    def tick_ms(self) -> int:
        """Schrittweite je `tick()` in ms (`GG-SIM-002`)."""
        ...

    @property
    def tick_count(self) -> int:
        """0-basierter Tick-Zaehler."""
        ...

    @property
    def control_state(self) -> RunStatus:
        """Run-Lifecycle-State (ADR 0039)."""
        ...

    @property
    def device_types(self) -> Mapping[str, str]:
        """`device_id` → `device_type`-Lookup fuer die Router."""
        ...

    @property
    def devices(self) -> tuple[object, ...]:
        """Geraete-Sequenz; Konsumenten casten auf ihr View-Protocol."""
        ...

    def request(self, action: ControlAction) -> None:
        """Dispatcht eine Control-Action (pause/resume/stop)."""
        ...

    def tick(self) -> TickResult:
        """Fuehrt einen Tick aus und liefert das Ergebnis."""
        ...

    def finalize(self) -> tuple[ReplayDelta, ...]:
        """Schliesst den Lauf ab und liefert die Replay-Deltas."""
        ...
