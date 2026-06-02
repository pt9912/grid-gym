# ADR 0040 — Alarm-Aggregation + AlarmStreamPort (M5 Welle 4b)

**Status:** Proposed — angelegt 2026-06-02 mit M5-Welle-4b-
C1 (dieser Commit). Die ADR verankert die Alarm-Architektur
fuer die Welle-4b-Lieferung und schliesst drei NEUE
Decisions (15/16/17) aus dem Welle-4b-Slice-Doc. Sie
definiert eine **NEU Domain-Type-Familie** (Unified `Alarm`
+ `AlarmSeverity` + `AlarmStatus`-Literals + 5 typisierte
Mapper-Funktionen aus den device-spezifischen Alarm-
Familien) plus eine **TickLoop-interne Aggregations-
Sequenz** (`TickResult.emitted_alarms`-Feld + Drain-Hook
am Tick-Ende) plus eine **NEU Driving-Port-Surface**
(`AlarmStreamPort` analog `TelemetryStreamPort` aus
ADR 0038) plus einen **REST-History-Endpoint** + **WS-
Live-Endpoint** mit adapter-internem Ring-Buffer.

**Datum:** 2026-06-02 (M5-Welle-4b-C1 dieser Commit; C3
zieht auf `Provisional` nach C2-Code-Merge)

**Bezug:**

- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md)
  (Schaerfungs-ohne-Supersede-Pattern — ADR 0040
  konkretisiert `GG-UI-005` aus Lastenheft §17 sowie die
  `spec/architecture.md`-§Alarm-Vorbelegung fuer Welle-
  4b-Implementation).
- [`ADR 0014`](0014-battery-snapshot-schema.md) §6
  (Welle-2-Review M-3, 2026-05-18: „AlarmSinkPort kommt
  mit M3" — M3 wurde ohne AlarmSinkPort geschlossen,
  Welle 4b loest die Driving-Side-Variante
  (`AlarmStreamPort` + adapter-interner
  `AlarmHistoryBuffer`) produktiv aus; Postgres-
  Persistenz (`GG-PERSIST-004`) bleibt M3-Welle-6c-
  Material). Pattern-Praezedenz fuer die hier
  ergaenzte `drain_alarms()`-Drain-Semantik.
- [`ADR 0016`](0016-pv-load-device-pattern.md) §2.5 +
  [`ADR 0017`](0017-grid-connection-device-pattern.md)
  §2.5 + [`ADR 0018`](0018-smart-meter-device-pattern.md)
  §2.3 (`PvAlarm`/`LoadAlarm`/`GridConnectionAlarm`/
  `SmartMeterAlarm`-Schemas als raw-Form-Praezedenz;
  Welle 4b mapped sie auf Unified-`Alarm`, aendert
  aber die Device-Internal-Schemas nicht).
- [`ADR 0036`](0036-ui-stack-choice.md) §2.5
  (UI-Stack HTMX + Chart.js — Welle 4b fuegt einen
  vierten Page-Route hinzu mit dem etablierten HTMX-
  Hydration + WS-Live-Pattern aus Welle 3 + Welle 4a).
- [`ADR 0037`](0037-http-api-surface-pattern.md) §2
  (HTTP-API-Surface-Pattern; Welle 4b ergaenzt den
  REST-Endpoint `GET /runs/{run_id}/alarms` und den
  WS-Endpoint `WS /runs/{run_id}/alarms-stream` unter
  bestehendem Pattern: REST fuer Hydration, WS fuer
  Live-Stream, `GG-API-004`-`ErrorResponse`-Format
  fuer 404).
- [`ADR 0038`](0038-telemetry-stream-port.md)
  (Pattern-Vorbild fuer `AlarmStreamPort` — Welle 4b
  spiegelt Surface, Backpressure-Strategie und
  Lifecycle 1:1 mit kleinerem Default-Queue-Maxsize
  `64` statt `128` weil Alarms typischerweise
  niederfrequent sind).
- [`ADR 0039`](0039-run-control-and-status-tracking.md)
  §3.2 (Welle-4a-Forward-Pointer auf Welle 4b mit NEU
  ADR 0040; in Welle-4b-C0 von ursprueglich 2 auf 3
  Decisions erweitert — siehe Welle-4b-Slice-Doc §0).
- [Lastenheft](../../../spec/lastenheft.md) §17
  `GG-UI-005` (UI-Akzeptanz: „Das UI MUSS Alarme
  visualisieren koennen. Akzeptanz: Das UI zeigt
  Alarmzeit, Ziel, Schweregrad, Code, Nachricht und
  aktuellen Status in einer aktualisierbaren Tabelle
  an.").
- [Lastenheft](../../../spec/lastenheft.md) §23
  `GG-PERSIST-004` (Postgres-Alarm-Persistenz —
  Welle-4b-Anti-Scope; M3-Welle-6c-Material).
- [Architektur](../../../spec/architecture.md) §Alarm
  (kanonisches 9-Feld-Schema `{alarm_id, run_id,
  simulation_time, target, code, severity, message,
  status, fault_id?}`; Welle 4b implementiert
  produktiv).
- [`../planning/in-progress/M5-welle-4b.md §3`](../planning/in-progress/M5-welle-4b.md)
  (Welle-4b-Slice-Doc mit Decisions 15/16/17 final +
  Mapping-Heuristik-Tabelle).
- **Vorbild-Probes** — kein eigener Welle-4b-Probe
  noetig, weil alle relevanten Pattern bereits
  validiert sind:
  - `drain_alarms()`-Pattern produktiv in den 5
    device-Familien seit M2-Welle-2 (~41 Test-Files
    mit Drain-Bezug; ADR 0014 §2.5).
  - `TickResult`-Field-Default-Pattern aus Welle-4a-
    `paused: bool = False`-Feld bestaetigt
    Backward-Compat-Strategie.
  - Asyncio-Pub/Sub-Stream-Surface aus Welle-3-Probe
    `5349923` server-side validiert (4 Tests:
    Single-Subscriber-Order, Fan-out, Drop-Oldest-
    Backpressure, Resource-Cleanup) — Welle-4b
    uebernimmt das Pattern 1:1.
  - HTMX-Polling + REST-Hydration aus Welle-4a
    `/runs/{id}/status`-Endpoint (`f1284c4`+`9c188e0`)
    produktiv etabliert.

---

## 1. Kontext

M5-Welle-1 hat die HTTP-API-Surface angelegt. M5-Welle-3
hat den `TelemetryStreamPort` mit asyncio-Pub/Sub-Pattern
etabliert. M5-Welle-4a hat das Replay-Controls + TickLoop-
Wiring + RunStatus + die UI-Page `/runs/{id}/control`
geliefert. Welle-4a-Anti-Scope-Item: **„Keine Alarm-
Aggregation / AlarmStreamPort / Alarm-Tabelle-UI (Welle
4b)"**. Welle 4b loest dieses Versprechen ein und
implementiert `GG-UI-005` (Alarm-Visualisierung)
produktiv.

Die Welle-4b-Implementation muss vier Architektur-Concerns
synchron loesen:

- **Device-Alarm-Heterogenitaet.** Die 5 device-
  spezifischen Alarm-Klassen haben **heterogene
  Schemas**: Battery/PV/Load/GridConnection sind 5-
  Feld (`target_device_id`/`limit`/`limit_unit`/
  `result: CommandResult`/`command_id`), SmartMeter
  ist 4-Feld (`target_device_id`/`reason: str`/`result`/
  `command_id` — ohne `limit`/`limit_unit`). Aggregator
  muss die Heterogenitaet normalisieren.
- **Lauf-Kontext-Defizit.** Devices kennen keinen
  `run_id`/`simulation_time_ms` — beide Felder sind aus
  Hexagonal-Sicht Run-Kontext, der erst beim TickLoop-
  Aufruf bekannt ist.
- **UI-Tab-Reload-Resilience.** WS-Subscribe allein
  reicht nicht: ein Tab-Reload verliert die History;
  Initial-Render ist leer bis erster neuer Alarm.
- **`spec/architecture.md`-Schema-Vorbelegung.** Das
  kanonische 9-Feld-Schema mit `alarm_id`/`severity`/
  `status`/`fault_id?` muss in der Domain ankommen und
  in den UI- und Persistenz-Schnittstellen
  durchgereicht werden.

Drei Concerns formen das Welle-4b-Pattern:

- **Domain-Modellierung:** Unified Schema + Mapper-
  Familie (Decision 15).
- **TickLoop-Vertrag:** Aggregations-Sequenz +
  Determinismus (Decision 16).
- **Adapter-Surface:** Stream-Port + History-Endpoint
  + UI-Hydration-Pattern (Decision 17).

## 2. Entscheidung

### 2.1 Decision 15 (NEU Unified `Alarm`-Domain-Schema + Mapper-Familie)

**Gewaehlt:** NEU Domain-Modul `hexagon/core/domain/
alarm.py` mit Frozen-Dataclass `Alarm` (9 Felder per
[`spec/architecture.md §Alarm`](../../../spec/architecture.md))
+ zwei `Literal`-Typen (`AlarmSeverity`, `AlarmStatus`)
+ 5 typisierte Mapper-Funktionen, die jeweils einen raw
device-Alarm + Run-Kontext annehmen und einen Unified-
`Alarm` zurueckgeben.

**Surface-Konstruktion:**

```python
# hexagon/core/domain/alarm.py
from typing import Literal


AlarmSeverity = Literal["info", "warning", "critical"]
"""Welle-4b: 3-Werte-Hierarchie (OTel-/syslog-aehnlich).
`info` bleibt fuer Welle-4b reserviert (keine produktive
Quelle); `warning` ist Power-Clamp; `critical` ist
Command-Reject."""

AlarmStatus = Literal["active"]
"""Welle-4b: nur `active`. Lifecycle-Erweiterung
(`acknowledged`/`resolved`) ist Welle 6+/M6-Material
(Anti-Scope §4). Literal-Erweiterung waere additiv und
braucht keinen Schema-Bruch."""


@dataclass(frozen=True, slots=True)
class Alarm:
    """Unified Alarm-Domain-Type (kanonisches 9-Feld-
    Schema per `spec/architecture.md §Alarm`)."""

    alarm_id: str            # UUIDv4-String
    run_id: str              # Lauf-Identitaet (GG-DATA-001)
    simulation_time_ms: int  # Tick-Zeitpunkt (ms ab Run-Start)
    target: str              # = target_device_id
    code: str                # Mapper-Output (z.B. "power_clamp_limited")
    severity: AlarmSeverity
    message: str             # Mensch-lesbar
    status: AlarmStatus
    fault_id: str | None     # Welle-4b: immer None


# Mapper-Signaturen (5 reine Funktionen):
def alarm_from_battery_alarm(
    raw: BatteryAlarm,
    *,
    run_id: str,
    simulation_time_ms: int,
    alarm_id: str,
) -> Alarm: ...

def alarm_from_pv_alarm(
    raw: PvAlarm,
    *,
    run_id: str,
    simulation_time_ms: int,
    alarm_id: str,
) -> Alarm: ...

# analog: from_load_alarm, from_grid_connection_alarm,
# from_smart_meter_alarm
```

**Mapping-Heuristik `(result, limit, limit_unit)` →
`(code, severity, message)`:**

Pattern aus `PvAlarm`-Docstring (`pv/commands.py:53`,
Welle-3-Review M-2): „IMMER `(result, limit)` als Tupel
auswerten".

| Device-Familie | `result` | Heuristik | `code` | `severity` | `message`-Template |
| --- | --- | --- | --- | --- | --- |
| Battery/PV/Load/GridConnection | `LIMITED` | Power-Clamp | `"power_clamp_limited"` | `"warning"` | `f"power command clamped to {limit} {limit_unit}"` |
| Battery/PV/Load/GridConnection | `REJECTED` | Sign- oder SOC-Reject | `"command_rejected"` | `"critical"` | `f"command rejected: limit {limit} {limit_unit}"` |
| SmartMeter | `REJECTED` | reason-codiert (Welle-3-Pattern) | `"smart_meter_rejected"` | `"warning"` | `f"smart-meter rejected: {reason}"` |

SmartMeter hat heute keinen `LIMITED`-Pfad — der Mapper
muss das Tupel `(result, ...)` defensiv behandeln. Eine
zukuenftige Welle-7-Device-Klasse mit zusaetzlicher
Semantik adde eine neue Mapper-Funktion (Pattern-Test
prueft Mapper-Vollstaendigkeit).

**Begruendung gegen Alternativen:**

- **Option A — Device-Alarm-Klassen erweitern.** Adde
  `run_id`/`simulation_time_ms`/`severity`/`code`/
  `message`/`status`/`fault_id` in jede der 5 Device-
  Alarm-Dataclasses. Verworfen:
  - **Bricht Hexagonal-Reinheit.** Devices kennen
    keinen Lauf-Kontext (`run_id` ist Run-Konzept,
    nicht Device-Konzept).
  - **Hoher Test-Migration-Aufwand.** ~41 Test-Files
    mit `drain_alarms()`-Bezug + 5 Device-
    Implementations muessten angepasst werden.
  - **Semantisch falsch.** Felder wie `severity` sind
    Cross-Device-/UI-Semantik (eine Power-Clamp ist
    immer `warning`, kein Battery-spezifisches
    Konzept). Adapter-/Aggregator-Logik gehoert zum
    Aggregator, nicht zum Device.
- **Option C — Alarm-Schema im Adapter.** Adapter
  (`AlarmStream`) macht die Anreicherung. Verworfen:
  - **Bricht Domain-vs-Adapter-Separation.** Adapter
    sollen Transport sein, nicht Schema-Logik tragen.
  - **Schwer testbar.** Mapper-Logik braucht Adapter-
    Setup (FastAPI-State, Lifespan-Wiring), statt
    reiner Funktionen.
  - **Kein wiederverwendbarer Aggregator** fuer
    andere Driving-Adapter (CLI, Tests).

**Konsequenz:**
- 5 Mapper-Funktionen, jede ~5-10 Zeilen, alle reine
  Funktionen (deterministisch, side-effect-free).
- `Alarm` ist `@dataclass(frozen=True, slots=True)` wie
  `RunMetadata` / `TelemetryPoint` — `AC-DOMAIN-FROZEN`
  automatisch erfuellt.
- `AlarmSeverity` + `AlarmStatus` als `Literal` (kein
  Enum) — konsistent mit `RunStatus`-Pattern aus Welle
  4a (ADR 0039 §2.1).
- Property-Tests pruefen Mapper-Determinismus: gleiche
  Inputs → gleiche Outputs.

### 2.2 Decision 16 (TickLoop-Alarm-Aggregation via `TickResult.emitted_alarms`)

**Gewaehlt:** TickLoop drainst, mapped und aggregiert
Alarms am Ende von `_run_tick_body`, vor dem `return`
des `TickResult`. Das `TickResult`-Schema wird um ein
neues Feld `emitted_alarms: tuple[Alarm, ...] = ()`
erweitert (Default `()` haelt Backward-Compat). Der
TickLoop-Konstruktor bekommt einen neuen optionalen
Kwarg `alarm_id_source: Callable[[], str] | None = None`
fuer testbare UUIDv4-Determinismus.

**Surface-Konstruktion:**

```python
# hexagon/core/domain/tick_result.py (EDIT)
@dataclass(frozen=True, slots=True)
class TickResult:
    tick: int
    simulation_time: int
    popped_events: tuple[Event, ...]
    emitted_telemetry: tuple[TelemetryPoint, ...]
    paused: bool = False
    emitted_alarms: tuple[Alarm, ...] = ()  # NEU


# hexagon/core/simulation/tick_loop.py (EDIT)
class TickLoop:
    def __init__(
        self,
        *,
        # ... existing kwargs
        alarm_id_source: Callable[[], str] | None = None,
    ) -> None:
        # ...
        self._alarm_id_source = alarm_id_source or (lambda: str(uuid.uuid4()))

    def _run_tick_body(self, ...) -> TickResult:
        # ... existing tick body (Schritte A0v..E) ...

        # NEU Schritt F (Welle-4b): Drain + Map + Aggregate
        alarms: list[Alarm] = []
        for device in self._devices:  # Konstruktor-Reihenfolge
            for raw in device.drain_alarms():
                alarms.append(
                    _dispatch_mapper(  # isinstance-dispatch
                        raw,
                        run_id=self._run_id,
                        simulation_time_ms=now,
                        alarm_id=self._alarm_id_source(),
                    )
                )

        return TickResult(
            tick=self._tick_count,
            simulation_time=now,
            popped_events=popped,
            emitted_telemetry=tuple(emitted),
            emitted_alarms=tuple(alarms),  # NEU
        )
```

**Determinismus-Garantien:**

- **Device-Iteration in Konstruktor-Reihenfolge.** M2-
  Welle-6a-Pattern; jeder `tick()` iteriert in derselben
  Tuple-Index-Reihenfolge.
- **`drain_alarms()`-Determinismus.** Jedes Device
  emittiert Alarms in `apply_command()`-Reihenfolge;
  der Drain liefert sie in FIFO-Reihenfolge zurueck.
  Gleicher Input → gleiche Output-Sequenz.
- **UUIDv4-Source-Injection.** Production-Default ist
  `uuid.uuid4` (kollisionsfrei in der Praxis); Tests
  injizieren einen monoton zaehlenden Stub
  (`itertools.count()` als String) fuer Snapshot-
  Equality-Tests. Pattern analog `random: RandomPort`
  aus M1.

**Begruendung gegen Alternativen:**

- **Option B — Separate `AlarmAggregator`-Klasse.**
  Composition over inheritance. Verworfen:
  - **YAGNI.** TickLoop hat bereits Devices-Iteration +
    `run_id` + `clock` zur Hand; ein zusaetzlicher
    Aggregator dupliziert die Iteration.
  - **Welle-7-Refactor moeglich** falls Multi-Run-
    Multiplexing kommt — bis dahin Single-Class.
- **Option C — Adapter-Side-Drain.** Adapter subscribt
  am Tick-Lifecycle und pollt. Verworfen:
  - **Kein Lifecycle-Event-Bus etabliert.**
  - **Polling-Latenz reisst Determinismus auf.** Jeder
    Tick muss synchron drainen, sonst kann ein Tick
    schon mehrere Alarms emittiert haben bevor der
    Poller sie liest.

**Snapshot-Format-Compat (ADR 0015):**

Das `emitted_alarms`-Feld geht **nicht** in den Snapshot.
Pattern identisch zu `emitted_telemetry`: beide sind
Tick-Output (verarbeitet vom Caller des Ticks), nicht
persistenter State der TickLoop-Maschine. ADR 0015
Snapshot-Format bleibt unangetastet.

### 2.3 Decision 17 (AlarmStreamPort-Surface + REST-History + WS-Live)

**Gewaehlt:** NEU `AlarmStreamPort`-Driving-Port unter
`hexagon/ports/driving/alarm_stream.py` mit Surface 1:1
parallel zu `TelemetryStreamPort` (ADR 0038 §2.1) +
asyncio-Pub/Sub-`InMemoryAlarmStream`-Adapter mit Drop-
Oldest-Backpressure + adapter-interner
`AlarmHistoryBuffer`-Ring-Buffer (N=200) + REST-Endpoint
`GET /runs/{run_id}/alarms` (History-Hydration) + WS-
Endpoint `WS /runs/{run_id}/alarms-stream` (Live-
Updates). UI nutzt **beide** Endpoints: GET fuer
Initial-Render, WS fuer Live-Stream — Best-of-both
gegen Tab-Reload-Resilience.

**Surface-Konstruktion:**

```python
# hexagon/ports/driving/alarm_stream.py (NEU)
class AlarmStreamPort(Protocol):
    """Live-Pull-Slot fuer Alarm-Konsumenten (M5 Welle 4b,
    GG-AR-PORT-DRV-*-Familie). Pattern 1:1 parallel zu
    `TelemetryStreamPort` (ADR 0038 §2.1)."""

    def publish(self, alarm: Alarm) -> None:
        """Sync-publish; pusht an alle aktiven Subscribers."""

    async def subscribe(
        self, run_id: str | None = None
    ) -> AsyncIterator[Alarm]:
        """Async-Generator; liefert publishte Alarms,
        optional nach run_id gefiltert. Subscriber-Slot
        wird im finally-Block freigegeben (`try/finally`-
        Pattern aus ADR 0038 Decision 11c)."""

    @property
    def subscriber_count(self) -> int: ...
```

**`InMemoryAlarmStream`-Adapter-Default:**

| Konfig | Welle-4b-Wert | Begruendung |
| --- | --- | --- |
| Queue-Maxsize | 64 | Kleiner als Telemetry's 128, weil Alarms typischerweise niederfrequent (Power-Clamp pro Tick = Ausnahme); ~6.4s Buffer bei 100ms-Tick reicht fuer Browser-Tab-Sleep-Resilience. |
| Backpressure | Drop-Oldest | Identisch zu ADR 0038 Decision 11b — juengste Alarms ueberleben, alte gehen verloren. UX-konsistent zur Telemetry-Strategie. |
| Lifecycle | `try/finally`-Cleanup | Identisch zu ADR 0038 Decision 11c — `aclose()` / WebSocketDisconnect entlaedt Subscriber-Slot deterministisch. |

**`AlarmHistoryBuffer`-Adapter-Helper (kein Port):**

```python
# adapters/driven/alarm_stream_inmemory/history_buffer.py
class AlarmHistoryBuffer:
    """In-Memory-Ring-Buffer der letzten N=200 Alarms
    (Welle-4b-Stub fuer Postgres-Persistenz; M3-Welle-
    6c ersetzt durch produktive `PostgresAlarmRepository`
    — siehe §3.3)."""

    def __init__(self, *, max_size: int = 200) -> None:
        self._buffer: collections.deque[Alarm] = collections.deque(maxlen=max_size)

    def append(self, alarm: Alarm) -> None: ...

    def get_recent(
        self, run_id: str | None = None, *, limit: int = 50
    ) -> tuple[Alarm, ...]: ...
```

Bewusst **kein** neuer Port (`AlarmHistoryPort`). Der
History-Buffer ist Adapter-Implementations-Detail —
Welle-6c ersetzt ihn durch eine Postgres-getriebene
Implementation, die einen NEU `AlarmRepositoryPort`-
Driven-Vertrag erfuellt. Bis dahin ist der Buffer
Adapter-internes Helper-Konzept.

**REST-Endpoint `GET /runs/{run_id}/alarms`:**

- **Path:** `/runs/{run_id}/alarms` (REST-GET).
- **Query-Param:** `?limit=50` (Default 50; Max 200 =
  Buffer-Groesse).
- **Response:** `AlarmsResponse{alarms: list[AlarmDto]}`
  als JSON-Array (neueste zuerst).
- **404** mit `GG-API-004`-Format
  (`code="run_not_found"`) bei nicht-existentem Run.
- **`tags=["runs"]`** fuer OpenAPI-Schema-Konsistenz.

**WS-Endpoint `WS /runs/{run_id}/alarms-stream`:**

- **Path:** `/runs/{run_id}/alarms-stream` — bewusst
  separat von `/alarms`, damit REST-GET nicht
  versehentlich als WS-Upgrade-Pfad interpretiert wird.
  Pattern analog Welle-3-Trennung `/dashboard` (REST)
  vs `/telemetry` (WS).
- **Subscribe-Logik** identisch zur Welle-3-Telemetry-
  WS: `await stream.subscribe(run_id=run_id)`-
  AsyncIterator + `websocket.send_json(asdict(alarm))`.
- **1008-Close** (Policy-Violation) bei nicht-
  existentem Run (Welle-1+3-Pattern).

**UI-Hydration-Pattern:**

```html
<div hx-get="/runs/{run_id}/alarms" hx-trigger="load"
     hx-target="#alarms-tbody" hx-swap="innerHTML">
  <!-- Initial-Hydration: REST-GET nach Page-Load -->
</div>

<div hx-ext="ws"
     ws-connect="/runs/{run_id}/alarms-stream">
  <!-- Live-Stream-Updates via WS -->
</div>
```

**Begruendung gegen Alternativen:**

- **Option A — Nur WS-Subscribe.** Pattern identisch
  zu `TelemetryStreamPort`. Verworfen:
  - **Tab-Reload verliert History.** UI-Tabelle ist
    leer bis erster neuer Alarm publisht wird.
  - **Niederfrequente Alarms = lange Wartezeit.** Im
    Demo-Mode kann zwischen Alarms ein Vielfaches der
    Telemetry-Interval-Zeit liegen.
- **Option B — Nur GET-Polling.** Pattern analog
  Welle-4a-Status-Endpoint. Verworfen:
  - **1s-Polling fuer potenziell niederfrequente
    Alarms ist verschwenderisch.**
  - **Update-Latenz.** Neue Alarms sind bis zu 1s
    sichtbar — fuer kritische Alarms unangemessen.
  - **Live-Feeling fehlt.**

**6-Spalten-UI-Tabelle (`GG-UI-005`-Akzeptanz):**

| Spalte | Quelle | Hinweis |
| --- | --- | --- |
| Zeit | `simulation_time_ms` | Formatiert als ms oder relativ |
| Ziel | `target` | = `target_device_id` |
| Schweregrad | `severity` | CSS-Klasse `severity-{severity}` |
| Code | `code` | Stabile ID fuer Toolings (z.B. `power_clamp_limited`) |
| Nachricht | `message` | Mensch-lesbar |
| Status | `status` | Welle-4b: immer `"active"` |

NEU 3 `AlarmSeverity`-CSS-Klassen analog Welle-3-
Quality-Marker-Pattern: `severity-info` (neutral),
`severity-warning` (gelb), `severity-critical` (rot).

## 3. Konsequenzen

### 3.1 Welle-4b-Folge

- **Code-Merge (C2):** NEU `Alarm`-Domain-Type +
  Literals + 5 Mapper in `hexagon/core/domain/alarm.py`;
  `TickResult.emitted_alarms`-Feld; TickLoop-Drain-Hook
  + `alarm_id_source`-Kwarg; NEU `AlarmStreamPort` unter
  `hexagon/ports/driving/`; NEU `InMemoryAlarmStream` +
  `AlarmHistoryBuffer` unter `adapters/driven/alarm_
  stream_inmemory/`; NEU REST-Endpoint
  `GET /runs/{run_id}/alarms` + NEU WS-Endpoint
  `WS /runs/{run_id}/alarms-stream` + NEU UI-Page +
  Templates + CSS + Tests (~25-28 Unit + 1 Integration).
- **HTTP-API-Erweiterung:** OpenAPI-Schema waechst um
  `/runs/{run_id}/alarms`-Path (REST) + `AlarmsResponse`-
  Schema. WS bewusst nicht im Schema (analog ADR 0037
  §3-Klarstellung + ADR 0038-Pattern).
- **UI-Page:** NEU `GET /runs/{run_id}/control`-
  Naviga­tion-Link auf Alarms-Page; 6-Spalten-Tabelle
  per `GG-UI-005`; 3 `severity-*`-CSS-Klassen.
- **Lifespan-Wiring:** `_demo_setup.py` bekommt eine
  optionale `BatteryDevice`-Instanz im Demo-TickLoop +
  `DemoTickLoopDriver` publisht `TickResult.emitted_
  alarms` auf den Stream + History-Buffer.
- **Tests:** ~25-28 neue Unit + 1 neue Integration
  (`test_m5_welle_4b_alarms_smoke.py`).

### 3.2 Welle-5-Folge

- **Scenario-getriebene Alarm-Quellen.** Welle 5
  (Demo-Pipeline + Scenario-Loader) liefert echte
  Scenario-Devices, die im normalen Tick-Verlauf
  Alarms emittieren — der Welle-4b-Aggregator wirt
  ohne Surface-Aenderung produktiv.
- **Multi-Run-Streams.** Welle 5 (oder spaeter)
  ergaenzt Multi-Run-Multiplexing — `subscribe(run_id)`-
  Filter ist bereits da; `AlarmStreamPort`-Vertrag
  unveraendert.

### 3.3 Welle-6c-Persistenz-Folge

- **`PostgresAlarmRepository`** (M3-Welle-6c-Material,
  parallel zur Welle-4a-`PostgresRunRepository.update_
  status`/`get_status`-`NotImplementedError`-Stub-
  Pattern). Schema-Migration via alembic-Revision
  unter `migrations/versions/`. NEU `AlarmRepositoryPort`-
  Driven-Slot mit Surface analog `RunRepositoryPort`
  (`save(alarm)`/`get_recent(run_id, limit)`/
  `exists(alarm_id)`).
- **`AlarmHistoryBuffer` → `PostgresAlarmRepository`-
  Swap.** Adapter-internes Helper wird ersetzt; UI +
  TickLoop-Aggregations-Sequenz aendern sich nicht
  (Stream-Wiring + REST-History-Endpoint bleiben
  identisch).
- **`GG-PERSIST-004`-Akzeptanz** erfuellt: „Alarme
  werden mit Lauf-ID, Simulationszeit, Ziel, Code,
  Schweregrad, Nachricht, Status und optionaler
  Fault-ID gespeichert und laufbezogen abgefragt." —
  alle 9 Felder sind im Welle-4b-`Alarm`-Schema bereits
  vorhanden.

### 3.4 Welle-6+/M6-Folge

- **Status-Lifecycle (`acknowledged`/`resolved`).**
  `AlarmStatus`-Literal-Erweiterung ist additiv (keine
  Schema-Bruchstelle); UI-Action-Buttons fuer
  Status-Mutationen via NEU
  `POST /runs/{run_id}/alarms/{alarm_id}/status`-
  Endpoint (oder REST-PATCH). Welle-6+/M6-Material.
- **Fault-Injection-`fault_id`-Mapping.** Welle-6+/M6:
  wenn ein Alarm durch eine Fault-Injection-Aktion
  ausgeloest wurde, kann der Mapper den `fault_id`-Slot
  produktiv setzen. Schema bleibt unveraendert (`fault_
  id` ist seit Welle 4b optional).
- **OTel-Span-Wrap fuer Alarm-Publish.** Analog
  `_protocol_otel_wrap.py` aus M4-Welle-6a + ADR 0038
  §3.3-Wishlist: `OtelSpanWrappedAlarmStream` mit
  Attributen `subscriber_count`/`publish_count`/
  `dropped_count`. M6 oder separate Hardening-Welle.
- **Cooperative-Pause-on-Critical-Alarm.** Die in
  ADR 0039 §3.2 angedeutete Symmetrie zum Cooperative-
  TickLoop-Pattern (kritischer Alarm → `request("pause")`
  am TickLoop) ist Welle-6+/M6-Material; benoetigt
  Policy-Entscheidung („welche Codes sind kritisch
  genug fuer Auto-Pause?") + Repository-Mirror.

### 3.5 Architektur-Konsistenz

- **Pattern-Praezedenz Stream-Port:** ADR 0038
  (`TelemetryStreamPort`) hat das Driving-Port-Stream-
  Pattern etabliert. Decision 17 spiegelt es 1:1 mit
  kleinerem Default-Queue-Maxsize fuer Alarm-typische
  Niederfrequenz.
- **Pattern-Praezedenz `TickResult`-Field-Erweiterung:**
  Welle-4a-`paused: bool = False`-Feld (ADR 0039
  Decision 13). `emitted_alarms: tuple[Alarm, ...] = ()`
  folgt demselben Default-Pattern.
- **Pattern-Praezedenz Domain-Type-Familie:** Welle-4a-
  `RunStatus` (`Literal` statt Enum) + Welle-3-
  `TelemetryPoint` (`@dataclass(frozen=True, slots=
  True)`). Welle-4b-`Alarm` + `AlarmSeverity` +
  `AlarmStatus` folgen demselben Stil-Vorbild.
- **Pattern-Praezedenz REST-History + WS-Live:** Welle-
  4a-`GET /status` (Polling) + Welle-3-`WS /telemetry`
  (Stream) zeigen beide Patterns separat. Decision 17
  kombiniert sie auf einer Surface, weil der UI-Use-Case
  beides braucht (Hydration + Live).
- **Hexagonal-Architektur:** Domain-Slot (Alarm +
  Mapper) ist rein in `hexagon/core/domain/`; Driving-
  Port in `hexagon/ports/driving/`; Adapter in
  `adapters/driven/`. Keine `AC-ADAPTER-PURE`-
  `ignore_imports`-Extension noetig (im Gegensatz zu
  Welle 4a).

## 4. Out-of-Scope

- **Alarm-Status-Lifecycle** (`acknowledged`/`resolved`).
  Welle-4b-`AlarmStatus` ist `Literal["active"]`.
  Lifecycle-Erweiterung ist Welle 6+/M6-Material.
  `GG-UI-005`-Akzeptanz fordert „aktualisierbare
  Tabelle", nicht „quittierbare Alarme" — Live-Update
  via WS + Initial-Hydration via GET erfuellen die
  Akzeptanz produktiv.
- **Postgres-Alarm-Persistenz** (`GG-PERSIST-004`).
  Welle-4b bleibt In-Memory (`AlarmHistoryBuffer`-Ring
  N=200). Schema-Migration + `PostgresAlarmRepository`-
  Implementation + NEU `AlarmRepositoryPort`-Driven-
  Slot sind M3-Welle-6c-Material (Forward-Pointer
  §3.3).
- **Device-Alarm-Klassen-Migration.** Die 5 device-
  spezifischen Alarm-Klassen bleiben **unveraendert**.
  Welle 4b adde ausschliesslich NEU Mapper-Funktionen.
  Die ~41 existierenden device-Alarm-Tests bleiben
  passing ohne Aenderung.
- **`AlarmSinkPort`-Driven-Slot** (im Sinne von ADR
  0014 §6). Welle 4b liefert einen **Driving**-Port
  (`AlarmStreamPort` — UI/API konsumiert) und einen
  adapter-internen `AlarmHistoryBuffer`, NICHT einen
  Driven-Persistenz-Port. Die ADR-0014-§6-Erwartung
  wird damit teilweise erfuellt (Stream + History-
  Snapshot) und teilweise auf Welle-6c verschoben
  (Postgres-Persistenz via NEU `AlarmRepositoryPort`).
- **Fault-Injection-`fault_id`-Mapping.**
  `Alarm.fault_id` bleibt in Welle 4b immer `None`.
  Welle 6+/M6 (siehe §3.4).
- **Scenario-Loader / Multi-Run-Stream-Multiplexing.**
  Welle 5.
- **OTel-Span-Wrap fuer Alarm-Publish.** M6 oder
  separate Hardening-Welle (siehe §3.4).
- **Cooperative-Pause-on-Critical-Alarm.** Welle 6+
  (siehe §3.4).
- **UI-Action-Buttons fuer Status-Mutationen.** Welle
  6+/M6.

## 5. Status-Pfad

- **Proposed** — 2026-06-02 mit M5-Welle-4b-C1 (dieser
  Commit). Decisions 15/16/17 alle final entschieden im
  ADR-Body; Vorlaeufer-Probes Welle-3 `5349923`
  (Asyncio-Pub/Sub) + Welle-4a `f1284c4`+`9c188e0`
  (HTMX-Polling + REST-Hydration) decken Surface-
  Mechanik bereits ab.
- **Provisional** — geplant mit M5-Welle-4b-C3 nach
  C2-Code-Merge. Pattern analog ADR 0030..0039
  (`Proposed → Provisional` mit C3 nach C2-
  Implementation-Merge; C2 belegt die Decisions
  produktiv im Code).
- **Accepted** — geplant mit M5-Welle-7-Closure (analog
  ADR 0030..0039).

## 6. Folge-Pflichten

- **M5-Welle-4b-C2-Code-Merge** belegt Decisions
  15/16/17 produktiv:
  - `src/grid_gym/hexagon/core/domain/alarm.py` — NEU
    `Alarm` + `AlarmSeverity` + `AlarmStatus` Literals
    + 5 Mapper-Funktionen.
  - `src/grid_gym/hexagon/core/domain/tick_result.py`
    — NEU `emitted_alarms: tuple[Alarm, ...] = ()`-
    Feld.
  - `src/grid_gym/hexagon/core/simulation/tick_loop.py`
    — NEU `alarm_id_source: Callable[[], str] | None
    = None`-Konstruktor-Kwarg +
    `_attach_alarm_id_source`-Helper + Drain+Map+
    Aggregate-Hook im `_run_tick_body` vor `return`.
  - `src/grid_gym/hexagon/ports/driving/alarm_stream.py`
    — NEU `AlarmStreamPort`-Protocol.
  - `src/grid_gym/adapters/driven/alarm_stream_inmemory/`
    — NEU Paket mit `__init__.py` + `stream.py` (Pub/
    Sub) + `history_buffer.py` (Ring-Buffer).
  - `src/grid_gym/adapters/driving/http_api/_dependencies.py`
    — NEU `get_alarm_stream` +
    `get_alarm_history_buffer`-FastAPI-Dependencies +
    Not-Configured-Errors.
  - `src/grid_gym/adapters/driving/http_api/_runs_router.py`
    — NEU `GET /runs/{run_id}/alarms`-Endpoint.
  - `src/grid_gym/adapters/driving/http_api/_runs_action_router.py`
    — NEU `WS /runs/{run_id}/alarms-stream`-Endpoint.
  - `src/grid_gym/adapters/driving/http_api/_schemas.py`
    — NEU `AlarmDto` + `AlarmsResponse`-Pydantic-
    Models.
  - `src/grid_gym/adapters/driving/http_api/_demo_setup.py`
    — Demo-TickLoop bekommt optionale Battery-Device-
    Instanz + Driver publisht
    `TickResult.emitted_alarms`.
  - `src/grid_gym/adapters/driving/http_api/app.py`
    — NEU `configure_alarm_stream` + Lifespan-Wiring.
  - `src/grid_gym/adapters/driving/ui/routes.py` +
    `templates/alarms.html` +
    `_alarms_content.html` +
    `static/style.css` (3 `severity-*`-CSS-Klassen) +
    `templates/navigation.html` — NEU UI-Page.
- **M5-Welle-4b-C3 (dieser Commit)** zieht diese ADR
  auf `Provisional` mit C2-Code-Merge-Beleg + Status/
  DoD-Sync + Top-Level-Doku-Sync.
- **M5-Welle-5** (Demo-Pipeline + Scenario-Loader)
  liefert echte Scenario-Devices, die produktive
  Alarms emittieren; ADR 0040 bleibt unveraendert
  (Surface-stabil).
- **M3-Welle-6c** liefert `PostgresAlarmRepository` +
  NEU `AlarmRepositoryPort`-Driven-Slot (siehe §3.3);
  ADR 0040 bleibt unveraendert (Buffer-Swap
  transparent).
- **M5-Welle-7-Closure** zieht diese ADR auf `Accepted`.
- **Optional Welle-6+/M6:** Status-Lifecycle +
  Fault-ID-Mapping + OTel-Span-Wrap + Cooperative-
  Pause-on-Critical (siehe §3.4).

## 7. References

- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md)
  (Schaerfungs-ohne-Supersede-Pattern).
- [`ADR 0014`](0014-battery-snapshot-schema.md) §6
  („AlarmSinkPort kommt mit M3" Forward-Pointer-
  Erbschaft; Welle 4b loest den Driving-Side-Anteil
  aus, Postgres-Persistenz bleibt M3-Welle-6c).
- [`ADR 0015`](0015-snapshot-envelope-v2.md)
  (TickLoop-Snapshot-Envelope-v2 — `emitted_alarms`
  gehoert nicht in den Snapshot, analog
  `emitted_telemetry`).
- [`ADR 0036`](0036-ui-stack-choice.md) §2.5
  (HTMX-UI-Stack).
- [`ADR 0037`](0037-http-api-surface-pattern.md) §2
  (HTTP-API-Surface-Pattern; Welle-4b ergaenzt REST +
  WS analog Welle-1/3-Etablierung).
- [`ADR 0038`](0038-telemetry-stream-port.md)
  (Pattern-Vorbild fuer `AlarmStreamPort`; Welle-4b
  spiegelt Surface, Backpressure, Lifecycle 1:1).
- [`ADR 0039`](0039-run-control-and-status-tracking.md)
  §3.2 (Welle-4a-Forward-Pointer auf Welle 4b mit
  NEU ADR 0040; Decision-Plan von 2 auf 3 erweitert).
- [Lastenheft](../../../spec/lastenheft.md) §17
  `GG-UI-005` (UI-Akzeptanz: 6 Pflicht-Spalten).
- [Lastenheft](../../../spec/lastenheft.md) §23
  `GG-PERSIST-004` (Postgres-Alarm-Persistenz —
  Welle-4b-Anti-Scope; M3-Welle-6c).
- [Architektur](../../../spec/architecture.md) §Alarm
  (kanonisches 9-Feld-Schema).
- [`../planning/in-progress/M5-welle-4b.md §3`](../planning/in-progress/M5-welle-4b.md)
  (Welle-4b-Slice-Doc mit Decisions 15/16/17 +
  Mapping-Heuristik-Tabelle).
- **Vorbild-Probes** — keine eigene Welle-4b-Probe:
  - Welle-3-Asyncio-Pub/Sub-Probe `5349923` — 4 Tests
    in
    [`../../../tests/integration/test_m5_welle_3_async_pubsub_probe.py`](../../../tests/integration/test_m5_welle_3_async_pubsub_probe.py).
  - Welle-4a-HTMX-Polling + REST-Hydration
    `f1284c4`+`9c188e0` (`GET /status`-Endpoint +
    Inline-JSON-Render in `_control_content.html`).
- Pattern-Praezedenz **Domain-Type-Familie**: Welle-4a-
  `RunStatus` (ADR 0039 §2.1) — `Literal` statt Enum,
  `@dataclass(frozen=True, slots=True)` fuer Frozen-
  Compliance.
- Pattern-Praezedenz **NEU-Driving-Port**: ADR 0037
  (HTTP-API-Surface-Pattern) — NEU Surface fuer Welle-
  1; ADR 0038 (TelemetryStreamPort) — NEU Surface fuer
  Welle-3; hier NEU Surface fuer Welle-4b.
