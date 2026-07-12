"""Current-Value-Projektion fuer die Field-Server-Pull-Seite (ADR 0075 §2.2).

Der gemeinsame Hebel aller Pull-Server (Modbus jetzt; DNP3-Outstation/OPC-UA-
Server/IEC-Server spaeter): eine **last-write-wins**-Projektion des letzten
emittierten `TelemetryPoint` pro `(device_id, metric)`, gespeist aus
`TickResult.emitted_telemetry` — **nicht** aus dem drop-oldest-
`TelemetryStreamPort` (der kann „letzter Wert JETZT" fuer einen zu beliebiger
Zeit pollenden Master nicht liefern; Review-Fund).

**Tick-frame-atomar (Review-Fund):** `update_from_tick` baut einen neuen
Frame-Snapshot und tauscht die interne Referenz **atomar** (CPython-GIL) — ein
konkurrenter Poll aus dem Server-Loop-Thread (`latest`/`snapshot`) sieht immer
einen vollstaendigen Frame, nie einen halb-aktualisierten. Lock-frei.

**Determinismus (ADR 0075 §2.5):** reine Funktion der emittierten Telemetrie
(Domaenen-`TelemetryPoint`, volle `Decimal`-Fidelity); volatil (kein
`SnapshotEnvelope`-Slot).
"""

from __future__ import annotations

from collections.abc import Mapping

from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.domain.tick_result import TickResult


class CurrentValueProjection:
    """Last-value-per-`(device_id, metric)`-Projektion (ADR 0075 §2.2)."""

    def __init__(self) -> None:
        self._latest: Mapping[tuple[str, str], TelemetryPoint] = {}

    def update_from_tick(self, result: TickResult) -> None:
        """Aktualisiert die Projektion aus `result.emitted_telemetry`
        (last-write-wins). Tick-frame-atomar: der neue Frame wird komplett
        gebaut und die interne Referenz danach in einem Schritt getauscht —
        ein nebenlaeufiger Poller sieht nie einen Teil-Frame."""
        if not result.emitted_telemetry:
            return
        updated: dict[tuple[str, str], TelemetryPoint] = dict(self._latest)
        for point in result.emitted_telemetry:
            updated[point.device_id, point.metric] = point
        self._latest = updated

    def latest(self, device_id: str, metric: str) -> TelemetryPoint | None:
        """Letzter emittierter Punkt fuer `(device_id, metric)`; `None`, wenn
        fuer das Paar noch nichts emittiert wurde. Thread-sicher (atomarer
        Dict-Read auf der aktuellen Frame-Referenz)."""
        return self._latest.get((device_id, metric))

    def snapshot(self) -> Mapping[tuple[str, str], TelemetryPoint]:
        """Momentaufnahme der gesamten Projektion (fuer den Register-Map-Aufbau
        im Server-Adapter). Kopie — der Aufrufer haelt nicht auf die interne
        Referenz."""
        return dict(self._latest)
