"""`AlarmHistoryPort` Driven-Port fuer die Alarm-History (ADR 0079 §2.3 Decision A).

Interim-Driven-Vertrag fuer den Alarm-History-Lese-/Append-Slot. Bis M5-Welle-4b
lebte die History als adapter-interner `AlarmHistoryBuffer` ohne Port-Abstraktion
(ADR 0040 §2.3 Decision 17, bewusst „kein Port"). ADR 0079 Decision A schaerft das
(Muster ADR 0011, Schaerfung ohne Abloesung): der HTTP-Driving-Adapter
(`_dependencies`/`_alarm_setup`/`_tick_loop_driver`) typisiert die History nun gegen
diesen Port statt gegen den konkreten driven-Adapter-Typ — a-checks `lateral-adapter`-
Regel (ADR 0079 §2.1) wird damit erfuellt.

**Interim, nicht final:** die M3-Welle-6c-Postgres-Persistenz (`GG-PERSIST-004`)
ersetzt den In-Memory-Stub durch einen produktiven `AlarmRepositoryPort`
(`save`/`get_recent`/`exists`, ADR 0040 §3.3), der diesen Lese-/Append-Vertrag
subsumiert. `AlarmHistoryPort` ist der minimale Vertrag fuer die HEUTIGE
Buffer-Surface — kein Persistenz-Versprechen.

Der einzige Implementer ist heute `AlarmHistoryBuffer`
(`adapters/driven/alarm_stream_inmemory/history_buffer.py`), der ihn strukturell
erfuellt (keine Signatur-Aenderung).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from grid_gym.hexagon.core.domain.alarm import Alarm


@runtime_checkable
class AlarmHistoryPort(Protocol):
    """Interim-Driven-Port fuer die Alarm-History (ADR 0079 §2.3).

    Surface = die heutige `AlarmHistoryBuffer`-Oberflaeche:

    - `append(alarm)`: haengt einen Alarm an (FIFO-Drop bei Capacity ist
      Adapter-Implementations-Detail, kein Vertrag).
    - `get_recent(run_id, *, limit)`: liefert die neuesten `limit` Alarms,
      optional nach `run_id` gefiltert, neueste zuerst.
    """

    def append(self, alarm: Alarm) -> None:
        """Haengt `alarm` an die History an."""
        ...

    def get_recent(self, run_id: str | None = None, *, limit: int = 50) -> tuple[Alarm, ...]:
        """Liefert die neuesten `limit` Alarms (neueste zuerst), optional nach
        `run_id` gefiltert. `limit <= 0` liefert das leere Tupel."""
        ...
