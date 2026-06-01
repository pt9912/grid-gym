"""TelemetryStreamPort — Live-Telemetry-Stream Driving-Port (M5 Welle 3, ADR 0038).

Surface fuer einen In-Process Pub/Sub-Stream: Producer
(Welle-3-Demo-Generator, ab Welle 4 der TickLoop) ruft
``publish``, Konsumer (`WS /runs/{run_id}/telemetry`-Endpoint)
abonniert via ``subscribe`` und liest als ``async for``-Loop.

Welle-3-Scope deckt `GG-API-002` (WebSocket-Telemetrie:
Lauf-ID, Simulationszeit, Sequenznummer, Telemetrie-Payload)
und `GG-UI-002/003/009` (Live-Telemetry, Zeitreihen,
Quality-Marker) ab.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol

TelemetryQuality = Literal[
    "ok",
    "stale",
    "invalid",
    "nan",
    "missing",
    "fault_injected",
]
"""Sechs Quality-Zustaende (`GG-UI-009`)."""


@dataclass(frozen=True, slots=True)
class TelemetryPoint:
    """Ein einzelner Telemetry-Sample, der ueber den Stream geht.

    Felder decken `GG-API-002`-Akzeptanz (Lauf-ID + Simulationszeit
    + Sequenznummer + Payload) sowie `GG-UI-002` (Geraet + Metrik
    + Wert + Einheit + Quality) ab.
    """

    run_id: str
    device_id: str
    metric: str
    value: float
    unit: str
    simulation_time_ms: int
    quality: TelemetryQuality
    sequence: int


class TelemetryStreamPort(Protocol):
    """Pub/Sub-Vertrag fuer Live-Telemetry (ADR 0038)."""

    def publish(self, point: TelemetryPoint) -> None:
        """Pusht einen Telemetry-Point an alle aktiven Subscribers.

        Synchrone Methode; der Producer (Demo-Generator in
        Welle 3, TickLoop ab Welle 4) braucht keinen
        Event-Loop-Kontext. Bei vollem Subscriber-Buffer
        wendet die Implementation Drop-Oldest-Backpressure an
        (ADR 0038 §2.2).
        """
        ...

    def subscribe(self, run_id: str | None = None) -> AsyncIterator[TelemetryPoint]:
        """Liefert einen AsyncIterator ueber publishte Points.

        Filterung optional nach ``run_id``; ``None`` liefert
        alle Points. Bei Iterator-Exit (`aclose()` oder
        WebSocketDisconnect) wird der Subscriber-Slot
        automatisch freigegeben (ADR 0038 §2.3).
        """
        ...

    @property
    def subscriber_count(self) -> int:
        """Anzahl aktiver Subscribers (Test- + Observability-
        Sichtbarkeit)."""
        ...
