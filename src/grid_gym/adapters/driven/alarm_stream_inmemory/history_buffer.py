"""In-Memory Ring-Buffer fuer Alarm-History (ADR 0040 Decision 17).

Welle-4b-Stub fuer die Postgres-Persistenz, die in M3-Welle-6c
durch eine produktive `PostgresAlarmRepository`-Implementation
ersetzt wird (parallel zur Welle-4a-`PostgresRunRepository.
update_status`/`get_status`-`NotImplementedError`-Stub-Pattern).

Der Buffer ist **kein** Port — er ist adapter-internes Helper-
Konzept; UI-`GET /runs/{run_id}/alarms`-Endpoint liest hier
direkt. Bei Welle-6c-Postgres-Migration wird der Buffer ersetzt
durch einen NEU `AlarmRepositoryPort`-Driven-Slot mit Surface
`save(alarm)` + `get_recent(run_id, limit)` + `exists(alarm_id)`.
"""

from __future__ import annotations

from collections import deque
from typing import Final

from grid_gym.hexagon.core.domain.alarm import Alarm


_DEFAULT_MAX_SIZE: Final[int] = 200
"""Welle-4b-Default-Capacity. Bei FIFO-Drop ueberleben die
juengsten 200 Alarms; alte gehen verloren bei Tab-Reload nach
langer Inaktivitaet. Akzeptabel fuer Demo-UX; produktive
Persistenz folgt mit M3-Welle-6c."""


class AlarmHistoryBuffer:
    """Ring-Buffer der letzten N Alarms (Welle-4b-Stub).

    FIFO-Drop bei Capacity-Ueberschreitung; ``get_recent(run_id,
    limit)`` filtert nach Lauf und gibt die neuesten ``limit``
    Eintraege in umgekehrter Reihenfolge zurueck (juengste
    zuerst).
    """

    def __init__(self, *, max_size: int = _DEFAULT_MAX_SIZE) -> None:
        self._buffer: deque[Alarm] = deque(maxlen=max_size)

    def append(self, alarm: Alarm) -> None:
        """Fuegt einen Alarm hinzu. Bei voller Capacity wird der
        aelteste Eintrag automatisch verdraengt (`deque.maxlen`-
        Verhalten)."""
        self._buffer.append(alarm)

    def get_recent(self, run_id: str | None = None, *, limit: int = 50) -> tuple[Alarm, ...]:
        """Liefert die neuesten ``limit`` Alarms, optional nach
        ``run_id`` gefiltert. Neueste zuerst (LIFO der internen
        deque).

        Welle-4b-Review-Fix #5: Sync-REST-Handler laeuft im FastAPI-
        Threadpool, waehrend der asyncio-Driver-Task `append(...)`
        ruft — `reversed(self._buffer)` waehrend gleichzeitigem
        Append wirft `RuntimeError: deque mutated during iteration`.
        `tuple(self._buffer)` ist in CPython atomar (GIL-Schutz
        ueber den C-Level-Copy) und liefert einen stabilen Snapshot.
        """
        if limit <= 0:
            return ()
        snapshot = tuple(self._buffer)
        filtered: list[Alarm] = []
        for alarm in reversed(snapshot):
            if run_id is not None and alarm.run_id != run_id:
                continue
            filtered.append(alarm)
            if len(filtered) >= limit:
                break
        return tuple(filtered)

    def __len__(self) -> int:
        return len(self._buffer)
