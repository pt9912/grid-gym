"""M5-Welle-3-Pre-C0c Probe-Run: Asyncio-Pub/Sub fuer Live-WS-Telemetry.

Ziel: server-side validieren, dass das geplante
Welle-3-Pattern (asyncio.Queue-basiertes Pub/Sub + FastAPI-
WebSocket-Pump) produktions-reif ist, BEVOR die Slice-Doc-
Anlage in C0 die Architektur fixiert.

**Kein Touch am `src/`-Baum** — die Probe-App ist inline
hier definiert (analog Welle-1-Pre-C0c-Probe `9c20dad`).
Bei C2 wird die produktive Implementation diese Datei
ersetzen.

Probe-Aussage (4 Tests):
- Ein einzelner Subscriber empfaengt alle Publisher-
  Messages in Reihenfolge.
- Zwei Subscriber bekommen dieselben Messages (Fan-out).
- Wenn der Publisher schneller produziert als der
  Subscriber konsumiert, dropped der Stream silently aelteste
  Messages (Drop-Oldest-Backpressure-Pattern via bounded
  `asyncio.Queue`).
- Subscriber-Disconnect schluesselt den Topic ohne
  Server-side Resource-Leak.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient


class _ProbeStream:
    """Welle-3-Probe Pub/Sub-Skeleton.

    Spiegelt die Welle-3-C2-Produktiv-Surface
    (`TelemetryStreamPort`) ab: `subscribe()`-AsyncIterator
    + `publish()`-Methode. Bounded Queue mit
    `drop-oldest`-Backpressure per `Queue.full() -> get_nowait`-
    Drain.
    """

    def __init__(self, *, queue_maxsize: int = 16) -> None:
        self._subscribers: list[asyncio.Queue[dict[str, Any]]] = []
        self._queue_maxsize = queue_maxsize

    def publish(self, message: dict[str, Any]) -> None:
        """Pusht eine Message an alle Subscribers.

        Bei voller Queue wird der aelteste Eintrag verworfen
        (drop-oldest); damit kann der WS-Pump bei
        Browser-Tab-Sleep nicht den ganzen Server blockieren.
        """
        for subscriber in self._subscribers:
            if subscriber.full():
                try:
                    subscriber.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            subscriber.put_nowait(message)

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        """Liefert einen AsyncIterator ueber alle publishten Messages."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(
            maxsize=self._queue_maxsize
        )
        self._subscribers.append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.remove(queue)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


@pytest.fixture
def probe_client() -> Iterator[tuple[TestClient, _ProbeStream]]:
    """FastAPI-Probe-App mit einem WS-Endpoint und Stream-Instanz."""
    app = FastAPI()
    stream = _ProbeStream(queue_maxsize=4)

    @app.websocket("/ws")
    async def ws_telemetry(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            async for message in stream.subscribe():
                await websocket.send_json(message)
        except WebSocketDisconnect:
            return

    with TestClient(app) as client:
        yield client, stream


def test_single_subscriber_receives_messages_in_order(
    probe_client: tuple[TestClient, _ProbeStream],
) -> None:
    """Ein Subscriber empfaengt die publishten Messages in Reihenfolge."""
    client, stream = probe_client
    with client.websocket_connect("/ws") as ws:
        # Lass den Subscribe-Loop einmal scheduled werden.
        for tick in range(3):
            stream.publish({"tick": tick, "value": tick * 10})
        received = [ws.receive_json() for _ in range(3)]
    assert received == [
        {"tick": 0, "value": 0},
        {"tick": 1, "value": 10},
        {"tick": 2, "value": 20},
    ]


def test_two_subscribers_get_same_messages_fanout(
    probe_client: tuple[TestClient, _ProbeStream],
) -> None:
    """Zwei parallele Subscribers bekommen identischen Inhalt (Fan-out)."""
    client, stream = probe_client
    with (
        client.websocket_connect("/ws") as ws_a,
        client.websocket_connect("/ws") as ws_b,
    ):
        stream.publish({"tick": 0, "value": 100})
        stream.publish({"tick": 1, "value": 200})
        msgs_a = [ws_a.receive_json() for _ in range(2)]
        msgs_b = [ws_b.receive_json() for _ in range(2)]
    assert msgs_a == msgs_b == [
        {"tick": 0, "value": 100},
        {"tick": 1, "value": 200},
    ]


def test_drop_oldest_backpressure_on_full_queue() -> None:
    """Bei vollem Queue-Buffer droppt der Stream aelteste Messages.

    Direkt am Stream getestet (kein WebSocket-Wrapping), damit
    der sync-TestClient nicht in `receive_json()`-Race laeuft.
    Probe-Aussage: das produktive Welle-3-Wiring darf bei
    Browser-Tab-Sleep nicht den ganzen Server blockieren — das
    bounded `asyncio.Queue` haelt den Speicher-Footprint konstant
    und Drop-Oldest gibt die jungsten Daten Vorrang.
    """
    stream = _ProbeStream(queue_maxsize=4)
    # Subscriber manuell registrieren ohne Async-Loop (Test-Hook
    # auf private `_subscribers`; die Probe-App nutzt das gleiche
    # Pattern produktiv via `subscribe()`-AsyncIterator).
    subscriber_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=4)
    stream._subscribers.append(subscriber_queue)

    for tick in range(10):
        stream.publish({"tick": tick, "value": tick * 10})

    # Queue ist voll, alte gedroppt; nur die letzten 4 Messages
    # ueberleben.
    assert subscriber_queue.qsize() == 4
    contents: list[dict[str, Any]] = []
    while not subscriber_queue.empty():
        contents.append(subscriber_queue.get_nowait())
    # Juengste Message ueberlebt (tick=9 ist der letzte publish).
    assert contents[-1]["tick"] == 9
    # Alle gespeicherten Ticks gehoeren zur juengeren Haelfte des
    # 10-Publish-Bursts (tick >= 6 wegen 4-Slot-Queue + Drop-
    # Oldest).
    assert all(msg["tick"] >= 6 for msg in contents)


def test_subscribe_unsubscribe_cycle_releases_resources() -> None:
    """`subscribe()`-AsyncIterator gibt den Subscriber-Slot bei
    Iterator-Exit frei (finally-Block).

    Direkt mit `asyncio.run()` getestet, damit der TestClient-
    WebSocket-Shutdown-Race umgangen wird; die produktive
    `subscribe()`-Methode wird hier 1:1 abgegangen.
    """

    async def _cycle() -> tuple[int, int, int]:
        stream = _ProbeStream(queue_maxsize=4)
        before = stream.subscriber_count
        iterator = stream.subscribe()
        # `anext` als Task starten: der Async-Generator-Body
        # laeuft erst bis zum ersten `yield`, dann blockiert
        # er in `queue.get()`. Mehrere `asyncio.sleep(0)`-Yields
        # geben dem Scheduler Gelegenheit, den Generator bis
        # zum park-Punkt zu durchlaufen → Subscriber ist
        # registriert.
        task = asyncio.create_task(anext(iterator))
        for _ in range(5):
            await asyncio.sleep(0)
        during = stream.subscriber_count
        stream.publish({"tick": 0})
        async with asyncio.timeout(1.0):
            first = await task
        assert first["tick"] == 0
        # AsyncIterator schliessen → finally-Block entfernt
        # Subscriber.
        await iterator.aclose()
        return before, during, stream.subscriber_count

    before, during, after = asyncio.run(_cycle())
    assert before == 0
    assert during == 1
    assert after == 0
