"""AlarmStreamPort — Live-Alarm-Stream Driving-Port (M5 Welle 4b,
ADR 0040 Decision 17).

Surface fuer einen In-Process Pub/Sub-Stream fuer unified `Alarm`-
Events. Producer (FastAPI-Lifespan-Driver, der nach jedem
TickLoop-Tick `TickResult.emitted_alarms` veroeffentlicht) ruft
``publish``; Konsumer (`WS /runs/{run_id}/alarms-stream`-Endpoint)
abonniert via ``subscribe`` und liest als ``async for``-Loop.

Pattern 1:1 parallel zu `TelemetryStreamPort` (ADR 0038 §2.1) —
selbe AsyncIterator-Surface, selbe Drop-Oldest-Backpressure-
Strategie (mit kleinerem Default-Queue-Maxsize 64 statt 128,
weil Alarms typischerweise niederfrequent sind), selbes
``try/finally``-Cleanup-Pattern. Welle-4b-Scope deckt `GG-UI-005`
(Alarm-Visualisierung) ab; Welle 5 erweitert auf Multi-Run-
Multiplexing ohne Surface-Aenderung.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from grid_gym.hexagon.core.domain.alarm import Alarm


class AlarmStreamPort(Protocol):
    """Pub/Sub-Vertrag fuer Live-Alarms (ADR 0040 Decision 17)."""

    def publish(self, alarm: Alarm) -> None:
        """Pusht einen Alarm an alle aktiven Subscribers.

        Synchrone Methode; der Producer (FastAPI-Lifespan-Driver)
        braucht keinen Event-Loop-Kontext. Bei vollem Subscriber-
        Buffer wendet die Implementation Drop-Oldest-Backpressure
        an (ADR 0040 §2.3; Pattern aus ADR 0038 §2.2).
        """
        ...

    def subscribe(self, run_id: str | None = None) -> AsyncIterator[Alarm]:
        """Liefert einen AsyncIterator ueber publishte Alarms.

        Filterung optional nach ``run_id``; ``None`` liefert
        alle Alarms. Bei Iterator-Exit (`aclose()` oder
        WebSocketDisconnect) wird der Subscriber-Slot
        automatisch freigegeben (ADR 0040 §2.3; Pattern aus
        ADR 0038 §2.3).
        """
        ...

    @property
    def subscriber_count(self) -> int:
        """Anzahl aktiver Subscribers (Test- + Observability-
        Sichtbarkeit)."""
        ...
