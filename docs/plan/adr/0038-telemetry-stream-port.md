# ADR 0038 — TelemetryStreamPort (M5 Welle 3)

**Status:** Accepted — gezogen 2026-06-04 mit M5-Welle-7-C1
(dieser Commit; M5-Closure-Welle). Provisional-Schritt
2026-06-01 mit M5-Welle-3-C3 `0e0473d` nach C2-Code-Merge
`82bdf39` (NEU `TelemetryStreamPort` + NEU
`InMemoryTelemetryStream` + `DemoTelemetryGenerator` +
WS-Subscribe-Wiring + Dashboard-UI-Page + 6-Zustands-
Quality-Marker; 16 neue Unit + 2 Integration-Tests +
Welle-1-Smoke-Anpassung; 10/10 A-1-Gates gruen ohne
Override). Initial-Entwurf (`Proposed`) 2026-06-01 mit
M5-Welle-3-C1 `9f3c00d`. Die ADR schaerft die Telemetry-
Source-Architektur fuer die Live-Telemetry-Dashboard-
Welle und schliesst Welle-0-Decision 11 (siehe
[`../planning/done/M5-welle-0.md §3`](../planning/done/M5-welle-0.md)).
Sie verankert eine NEUE Driving-Port-Surface
`TelemetryStreamPort` (mit `publish()`/`subscribe()`/
`TelemetryPoint`) plus den Stand-Adapter
`InMemoryTelemetryStream` als asyncio-Pub/Sub-Implementation
mit bounded Queues + Drop-Oldest-Backpressure. Welle 3..6c
haben die Surface produktiv-belegt (WS-Dashboard
GG-UI-002/003/009 + Welle-6b-Devices-Quality-Aggregation).

**Datum:** 2026-06-01 (M5-Welle-3-C1 `9f3c00d` → C3
`0e0473d`) / 2026-06-04 (M5-Welle-7-C1 Accepted, dieser
Commit)

**Bezug:**

- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md)
  (Schaerfungs-ohne-Supersede-Pattern — ADR 0038
  konkretisiert `GG-API-002` und `GG-UI-002/003/009` aus
  Lastenheft §16/§17 fuer Welle-3-Implementation).
- [`ADR 0030`](0030-device-protocol-port-surface.md) §2.1
  (Adapter-Hexagon-Pattern auf Driven-Side; ADR 0038
  spiegelt das Pattern auf eine neue Driving-Port-Surface).
- [`ADR 0036`](0036-ui-stack-choice.md) §2.5
  (Charting-Library Chart.js — Welle 3 nutzt produktiv die
  vendored Chart.js 4.5.1 fuer die Time-Series-
  Visualisierung).
- [`ADR 0037`](0037-http-api-surface-pattern.md)
  (HTTP-API-Surface-Pattern — der WS-Endpoint
  `/runs/{id}/telemetry` aus Welle 1 ist der
  Konsumer-Pfad, der in Welle 3 von Counter-Stub auf
  `TelemetryStreamPort.subscribe()` umgestellt wird).
- [Lastenheft](../../../spec/lastenheft.md) §16
  (`GG-API-002` WebSocket-Telemetrie: Akzeptanz „WebSocket-
  Nachrichten enthalten Lauf-ID, Simulationszeit,
  Sequenznummer und Telemetrie-Payload").
- [Lastenheft](../../../spec/lastenheft.md) §17
  (`GG-UI-002` Live-Telemetry / `GG-UI-003` Zeitreihen /
  `GG-UI-009` Quality-Marker — alle drei sind Welle-3-
  Akzeptanz-Ziele).
- [Architektur](../../../spec/architecture.md) §4.2
  (`GG-AR-PORT-DRV-*`-Driving-Port-Familie; `TelemetryStream
  Port` erweitert die Familie um einen Live-Pull-Slot).
- [`../planning/done/M5-welle-0.md §3`](../planning/done/M5-welle-0.md)
  Decision 11 (Telemetry-Source-Architektur war als offene
  Decision in Welle 0 hinterlegt; Welle 3 schliesst sie).
- [`../planning/done/M5-welle-3.md §3`](../planning/done/M5-welle-3.md)
  (Welle-3-Slice-Doc mit Decision-3/7/11 final).
- **Probe-Run-Beleg** `5349923` — 4 Tests gruen in
  [`../../../tests/integration/test_m5_welle_3_async_pubsub_probe.py`](../../../tests/integration/test_m5_welle_3_async_pubsub_probe.py)
  validieren das Pattern server-side (Single-Subscriber-
  Order, Fan-out, Drop-Oldest, Resource-Cleanup).

---

## 1. Kontext

M5-Welle-1 hat die HTTP-API-Surface mit einem WebSocket-
Endpunkt `WS /runs/{run_id}/telemetry` angelegt — der pusht
in Welle 1 noch einen Timer-getriebenen Counter-Stub
(`tick=0/1/2`, dann close). Welle 3 erfuellt `GG-UI-002`
(Live-Telemetry), `GG-UI-003` (Zeitreihen) und `GG-UI-009`
(Quality-Marker) und ersetzt den Counter-Stub durch einen
echten Live-Telemetry-Stream.

Die Telemetry-Daten haben drei Eigenschaften, die das
Pattern formen:

- **Fan-out**: ein einzelner Stream kann mehrere Browser-
  Tabs gleichzeitig speisen.
- **Backpressure**: Browser-Tab-Sleep darf nicht den
  Producer (TickLoop bzw. Demo-Generator) blockieren.
- **Hexagonal-Sauberkeit**: Pub/Sub-Surface lebt in der
  Port-Schicht, nicht in `app.state` (Hexagonal-Bruch).

Drei Architektur-Fragen, die diese ADR beantwortet:

- **Decision 11a** — Surface-Form: Wie genau sieht die
  Subscribe-Methode aus (AsyncIterator vs Callback-
  Register vs Queue-Pull)?
- **Decision 11b** — Backpressure-Strategie: Wie verhaelt
  sich der Stream bei einem schlafenden Browser-Tab?
- **Decision 11c** — Lifecycle: Wie raeumt eine
  abreissende WebSocket-Verbindung den Subscriber-Slot
  zuverlaessig auf?

## 2. Entscheidung

### 2.1 Decision 11a (Surface-Form) — AsyncIterator-Pattern

**Gewaehlt:** `subscribe(run_id: str | None = None) ->
AsyncIterator[TelemetryPoint]` als Async-Generator. Pattern
folgt PEP 525 (Asynchrone Generatoren) + Python-3.10+-
`async for`-Idiom.

**Surface-Konstruktion:**

```python
class TelemetryPoint:
    run_id: str
    device_id: str
    metric: str
    value: float
    unit: str
    simulation_time_ms: int
    quality: Literal[
        "ok", "stale", "invalid", "nan", "missing", "fault_injected"
    ]
    sequence: int

class TelemetryStreamPort(Protocol):
    def publish(self, point: TelemetryPoint) -> None:
        """Sync-publish; pusht an alle aktiven Subscribers."""

    async def subscribe(
        self, run_id: str | None = None
    ) -> AsyncIterator[TelemetryPoint]:
        """Async-Generator; liefert publishte Points,
        optional nach run_id gefiltert. Subscriber-Slot
        wird im finally-Block freigegeben."""

    @property
    def subscriber_count(self) -> int:
        """Anzahl aktiver Subscribers (Test- + Observability-
        Sichtbarkeit)."""
```

**Begruendung gegen Alternativen:**

- **Callback-Register** (`stream.add_listener(callback)`):
  Erfordert blockiernde Brueckenschicht zwischen sync-
  Callback und async-WebSocket. Bricht den `async/await`-
  Fluss in FastAPI-Endpoints und macht Backpressure-
  Handling auf Subscriber-Ebene unmoeglich.
- **Queue-Pull** (`stream.poll(timeout)`): Polling
  verbraucht CPU bei niedriger Update-Rate; AsyncIterator
  parkt in `queue.get()` ohne Last.
- **Subject/Observable** (RxPy-Stil): grosser Dependency-
  Footprint und ueberlappende Mental-Models mit
  Pythons-eigenem `asyncio`.

**`TelemetryPoint`-Feld-Abdeckung (`GG-API-002` +
`GG-UI-002`):**

| `GG-API-002`-Pflicht | `TelemetryPoint`-Feld     |
| -------------------- | ------------------------- |
| Lauf-ID              | `run_id`                  |
| Simulationszeit      | `simulation_time_ms`      |
| Sequenznummer        | `sequence`                |
| Telemetrie-Payload   | `value` + `unit` + `metric`|

`GG-UI-002`-Akzeptanz fordert zusaetzlich Geraet
(`device_id`) und Qualitaetsstatus (`quality`).
`GG-UI-009`-Akzeptanz fordert 6 Quality-Zustaende; die
`Literal`-Type-Annotation deckt sie ab.

### 2.2 Decision 11b (Backpressure-Strategie) — Drop-Oldest

**Gewaehlt:** **Drop-Oldest** mit bounded `asyncio.Queue`
pro Subscriber (Default `maxsize=128`).

**Mechanik:**

- Jeder Subscriber bekommt eine eigene `asyncio.Queue
  (maxsize=128)`.
- `publish()` iteriert ueber alle Subscribers, prueft
  `queue.full()`, drained bei voller Queue eine alte
  Message via `get_nowait()` (`contextlib.suppress(asyncio.
  QueueEmpty)` faengt Race-Condition mit dem
  Subscribe-Loop), dann `put_nowait(message)`.
- `subscribe()`-AsyncGenerator parkt in `await
  queue.get()` zwischen Messages — kein Polling, kein
  Busy-Wait.

**Drop-Oldest-Begruendung:**

| Strategie         | Effekt                              | Eignung |
| ----------------- | ----------------------------------- | ------- |
| Drop-Oldest       | juengste Daten ueberleben           | gewaehlt|
| Drop-Newest       | aelteste Daten ueberleben           | falsch fuer Live-Anzeige (Browser will den aktuellen Wert) |
| Unbounded         | Memory-Leak bei Browser-Tab-Sleep   | inakzeptabel |
| Disconnect-Sub    | aggressives Verwerfen von Clients   | UX-feindlich |

**Probe-Run-Beleg `5349923`:**
`test_drop_oldest_backpressure_on_full_queue` validiert:
nach 10 `publish()`-Calls in eine Queue mit `maxsize=4`
ueberleben genau 4 Messages, alle mit `tick >= 6` (juengere
Haelfte des Bursts), und der letzte Eintrag hat
`tick == 9` (juengste Message).

**Welle-3-Default `maxsize=128`**: ~1.3 Sekunden Buffer bei
100ms-Tick-Rate (`GG-SIM-002` standard); ueberbrueckt
Browser-Tab-Sleep-Phasen bis ca. 1s ohne sichtbare
Drops fuer typische Web-Interaktion. Welle-4-Tuning
moeglich bei Bedarf.

### 2.3 Decision 11c (Lifecycle) — try/finally-Cleanup

**Gewaehlt:** Subscriber-Slot wird via `try/finally`-Block
im AsyncIterator-Body bei `aclose()` (oder
WebSocketDisconnect-Propagation) freigegeben.

**Pattern:**

```python
async def subscribe(self, run_id=None):
    queue = asyncio.Queue(maxsize=self._queue_maxsize)
    self._subscribers.append((run_id, queue))
    try:
        while True:
            point = await queue.get()
            if run_id is None or point.run_id == run_id:
                yield point
    finally:
        self._subscribers.remove((run_id, queue))
```

**Cleanup-Pfad:**

1. WebSocket-Browser-Tab schliesst → `WebSocketDisconnect`-
   Exception steigt im FastAPI-Endpoint auf.
2. FastAPI-Handler verlaesst den `async for`-Loop.
3. Python's GC ruft `aclose()` auf dem AsyncGenerator auf.
4. `aclose()` ruft das `finally:` mit
   `_subscribers.remove(...)` auf.
5. Subscriber-Slot ist freigegeben; `publish()` iteriert
   ihn nicht mehr.

**Probe-Run-Beleg `5349923`:**
`test_subscribe_unsubscribe_cycle_releases_resources`
validiert dass `subscriber_count` von `0 → 1 → 0` ueber
einen Subscribe-`aclose()`-Zyklus laeuft. Cleanup ist
deterministisch (kein Wait-on-GC).

## 3. Konsequenzen

### 3.1 Welle-3-Folge

- WS-Endpoint `ws_run_telemetry` ruft `subscribe(run_id)`
  und pusht jede Message als JSON.
- Demo-Generator-Task (asyncio.Task in FastAPI-Lifespan)
  ruft alle ~200ms `publish(TelemetryPoint(...))` mit
  synthetischen Werten.
- Dashboard-UI-Page nutzt HTMX `hx-ext="ws"` zum WS-
  Connect; Chart.js-Glue verarbeitet `htmx:wsAfterMessage`-
  Events und updated die Time-Series.

### 3.2 Welle-4-Folge

- Welle 4 (Replay-Controls) ersetzt den `demo_generator.
  py` durch echtes TickLoop-Wiring:
  - Beim `POST /runs/{id}/control` mit `action: "resume"`
    startet die Welle-4-Logik den TickLoop und ruft
    `stream.publish(...)` aus dem Loop.
  - `pause`/`stop` koennen die Producer-Task pausieren.
- `TelemetryStreamPort`-Surface bleibt unveraendert —
  Welle 4 touched die Implementation, nicht den Vertrag.

### 3.3 Welle-6-Folge

- OTel-Span-Wrap (analog `_protocol_otel_wrap.py` aus
  M4-Welle-6a) waere natuerlich:
  `OtelSpanWrappedTelemetryStream` mit Attributen
  `subscriber_count`, `publish_count`, `dropped_count`.
- Welle 3 liefert es NICHT (Anti-Scope; M6-Wishlist).

### 3.4 M6-Folge

- SSE-Fallback bleibt offen: ein zweiter Adapter
  `SseTelemetryStream` (Server-Sent-Events) koennte
  denselben `TelemetryStreamPort`-Vertrag fuer
  WebSocket-feindliche Browser-Umgebungen erfuellen.

### 3.5 Architektur-Konsistenz

- Pattern-Praezedenz: `DeviceProtocolPort` (ADR 0030 fuer
  Driven-Side); `TelemetryStreamPort` ist die Driving-
  Side-Analogie fuer Live-Pull.
- Test-Pattern: das produktive
  `InMemoryTelemetryStream` ist gleichzeitig der Test-
  Fake (kein separater `_fakes.py`-Eintrag noetig).

## 4. Out-of-Scope

- **TickLoop-Wiring** — der Producer im Welle-3-Build ist
  der `demo_generator.py`-Stub. Echtes TickLoop-Wiring
  folgt in Welle 4.
- **Persistence-Sink** — kein DB-Persist der publishten
  Points. Snapshot/History gehoert zu `GG-API-001`-
  `/runs/{id}/snapshot` (Welle-4-Material).
- **OTel-Span-Wrap** — Welle 3 wraps nicht; M6 oder eine
  eigene Cross-Adapter-Hardening-Welle macht es analog
  zu M4-Welle-6a.
- **SSE-Fallback** — `TelemetryStreamPort`-Vertrag ist
  Transport-agnostisch (publish() kennt kein WS-Konzept);
  ein SSE-Adapter waere ein zukuenftiger zweiter Adapter
  ohne Vertrags-Aenderung.
- **Run-Aware-Producer** — der Demo-Generator publisht
  fuer **alle** Runs (run_id wird vom Subscriber-Filter
  zurueck-gefiltert). Welle 4 bringt run-spezifische
  Producer-Logik.
- **Backpressure-Tuning** — `maxsize=128` ist Welle-3-
  Default; weder dynamisches Tuning noch Per-Subscriber-
  Konfiguration in Welle 3.
- **Reconnect-Pattern** — HTMX `hx-ext="ws"` baut
  automatisch ein Reconnect-Behavior an; Welle 3 testet
  es nicht explizit (M6 koennte das vertiefen).

## 5. Status-Pfad

- **Proposed** — 2026-06-01 mit M5-Welle-3-C1 `9f3c00d`.
  Decision 11a/b/c alle final entschieden im ADR-Body;
  Probe-Run `5349923` belegt das Pattern server-side.
- **Provisional** — 2026-06-01 mit M5-Welle-3-C3 (dieser
  Commit) nach C2-Code-Merge `82bdf39`. Pattern analog
  ADR 0030..0037 in M4/M5 (`Proposed → Provisional` mit
  C3 nach C2-Implementation-Merge; C2 belegt die
  Decisions produktiv im Code). Belege: Decision 11a
  produktiv in `hexagon/ports/driving/telemetry_stream.
  py`-Protocol + `TelemetryPoint`-Dataclass; Decision 11b
  produktiv in `adapters/driven/telemetry_stream_inmemory/
  stream.py:publish` mit `contextlib.suppress(asyncio.
  QueueEmpty)`-Drain; Decision 11c produktiv im
  `subscribe`-AsyncGenerator-`try/finally`-Block.
- **Accepted** — 2026-06-04 mit M5-Welle-7-C1 (dieser
  Commit; M5-Closure-Welle). Welle 3..6c haben den
  TelemetryStreamPort produktiv-belegt; keine offenen
  Decisions. Pattern analog ADR 0030..0037.

## 6. Folge-Pflichten

- **M5-Welle-3-C2-Code-Merge** belegt Decisions 11a/b/c
  produktiv:
  - `src/grid_gym/hexagon/ports/driving/telemetry_stream.
    py` — Port-Surface + `TelemetryPoint`-Dataclass.
  - `src/grid_gym/adapters/driven/telemetry_stream_inmemory/`
    — Stand-Adapter mit Pub/Sub-Pattern + Demo-Generator.
  - `src/grid_gym/adapters/driving/http_api/_runs_action_
    router.py` — WS-Endpoint auf Subscribe-Pattern
    umgestellt.
- **M5-Welle-3-C3** zieht diese ADR auf `Provisional` mit
  C2-Code-Merge-Beleg.
- **M5-Welle-4** (Replay-Controls) ersetzt den
  `demo_generator.py` durch echtes TickLoop-Wiring (siehe
  §3.2).
- **M5-Welle-7-Closure** zieht diese ADR auf `Accepted`.
- **Optional Welle-6 oder M6** liefert
  `OtelSpanWrappedTelemetryStream` (siehe §3.3) und
  optional SSE-Adapter (siehe §3.4).

## 7. References

- [`ADR 0030`](0030-device-protocol-port-surface.md) §2.1
  (Adapter-Hexagon-Pattern auf Driven-Side).
- [`ADR 0036`](0036-ui-stack-choice.md) §2.5 (Charting-
  Library Chart.js, von Welle 3 produktiv genutzt).
- [`ADR 0037`](0037-http-api-surface-pattern.md)
  (HTTP-API-Surface-Pattern; WS-Endpoint, der hier den
  Konsumer-Pfad bildet).
- [Lastenheft](../../../spec/lastenheft.md) §16
  `GG-API-002` (WebSocket-Telemetrie-Akzeptanz).
- [Lastenheft](../../../spec/lastenheft.md) §17
  `GG-UI-002/003/009` (Live-Telemetry +
  Zeitreihen + Quality-Marker).
- [Architektur](../../../spec/architecture.md) §4.2
  (`GG-AR-PORT-DRV-*`-Driving-Port-Familie).
- [`../planning/done/M5-welle-0.md §3`](../planning/done/M5-welle-0.md)
  Decision 11 (offene Decision, hier final geschlossen).
- [`../planning/done/M5-welle-3.md §3`](../planning/done/M5-welle-3.md)
  (Welle-3-Slice-Doc mit Decisions 3/7/11).
- **Probe-Run-Beleg** `5349923` — 4 Tests gruen in
  [`../../../tests/integration/test_m5_welle_3_async_pubsub_probe.py`](../../../tests/integration/test_m5_welle_3_async_pubsub_probe.py)
  (`test_single_subscriber_receives_messages_in_order`,
  `test_two_subscribers_get_same_messages_fanout`,
  `test_drop_oldest_backpressure_on_full_queue`,
  `test_subscribe_unsubscribe_cycle_releases_resources`).
- Pattern-Praezedenz **NEU-Driving-Port**: ADR 0037 (HTTP-
  API-Surface-Pattern) — NEU Surface fuer Welle-1, hier
  NEU Surface fuer Welle-3.
