"""M5-Welle-4b-Review-Fix #5: AlarmHistoryBuffer.get_recent
snapshottet den deque vor reversed(), damit eine konkurrente
`append()` aus dem asyncio-Driver-Task waehrend einer Sync-REST-
Iteration nicht `RuntimeError: deque mutated during iteration`
ausloest.

Der Fix ist in CPython auf GIL-Atomic-Copy via `tuple(deque)`
gestuetzt — der Test reproduziert das Race-Symptom mit einer
abgeschwaechten In-Iteration-Mutation (`get_recent` darf nicht
werfen, auch wenn ein konkurrentes `append` zwischen
`tuple(...)` und dem `reversed(...)`-Generator passiert).
"""

from __future__ import annotations

import threading

from grid_gym.adapters.driven.alarm_stream_inmemory.history_buffer import (
    AlarmHistoryBuffer,
)
from grid_gym.hexagon.core.domain.alarm import Alarm


def _make_alarm(run_id: str, alarm_id: str) -> Alarm:
    return Alarm(
        alarm_id=alarm_id,
        run_id=run_id,
        simulation_time_ms=0,
        target="battery-1",
        code="power_clamp_limited",
        severity="warning",
        message="",
        status="active",
        fault_id=None,
    )


def test_get_recent_does_not_raise_when_buffer_mutates_concurrently() -> None:
    """Welle-4b-Review-Fix #5: konkurrentes `append()` waehrend
    eines `get_recent()`-Aufrufs darf keinen RuntimeError ausloesen.

    Vor dem Fix iterierte `reversed(self._buffer)` direkt ueber
    die deque; ein gleichzeitiges `append` aus einem anderen
    Thread (sync REST-Handler im Threadpool vs. asyncio-Driver-
    Task) konnte den Iterator brechen.
    """
    buffer = AlarmHistoryBuffer(max_size=200)
    for i in range(50):
        buffer.append(_make_alarm(run_id="r1", alarm_id=f"seed-{i}"))

    stop = threading.Event()
    errors: list[BaseException] = []

    def reader() -> None:
        try:
            for _ in range(200):
                buffer.get_recent(run_id="r1", limit=50)
        except BaseException as exc:
            errors.append(exc)

    def writer() -> None:
        try:
            i = 0
            while not stop.is_set():
                buffer.append(_make_alarm(run_id="r1", alarm_id=f"w-{i}"))
                i += 1
                if i >= 500:
                    break
        except BaseException as exc:
            errors.append(exc)

    reader_thread = threading.Thread(target=reader)
    writer_thread = threading.Thread(target=writer)
    reader_thread.start()
    writer_thread.start()
    reader_thread.join(timeout=5.0)
    stop.set()
    writer_thread.join(timeout=5.0)
    assert errors == []
    # Buffer ist nach max_size=200 capped.
    assert len(buffer) <= 200


def test_get_recent_returns_snapshot_unaffected_by_later_appends() -> None:
    """Welle-4b-Review-Fix #5: das zurueckgegebene Tuple ist ein
    Snapshot — spaetere `append()` veraendern es nicht."""
    buffer = AlarmHistoryBuffer(max_size=10)
    buffer.append(_make_alarm(run_id="r1", alarm_id="a-0"))
    snapshot = buffer.get_recent(run_id="r1", limit=10)
    buffer.append(_make_alarm(run_id="r1", alarm_id="a-1"))
    assert len(snapshot) == 1
    assert snapshot[0].alarm_id == "a-0"


def test_get_recent_respects_run_id_filter_after_snapshot() -> None:
    """Welle-4b-Review-Fix #5: Run-Filter laeuft auf dem Snapshot
    — Cross-Run-Drift im laufenden Buffer kontaminiert nicht die
    Antwort."""
    buffer = AlarmHistoryBuffer(max_size=10)
    buffer.append(_make_alarm(run_id="r1", alarm_id="a-0"))
    buffer.append(_make_alarm(run_id="r2", alarm_id="b-0"))
    buffer.append(_make_alarm(run_id="r1", alarm_id="a-1"))
    snapshot = buffer.get_recent(run_id="r1", limit=10)
    alarm_ids = [a.alarm_id for a in snapshot]
    assert alarm_ids == ["a-1", "a-0"]
