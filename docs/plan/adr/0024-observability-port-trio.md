# ADR 0024 — Observability-Port-Trio: LogPort + MetricsPort + TracePort (M3 Welle 5)

**Status:** Accepted — M3-Welle-7-Closure 2026-05-25 (C1.3).
Validierung lieferten Welle 5 (Foundation, `7427daf..a690c02`:
1023 Unit-Tests + 19 Integration-Tests gruen, Port-Trio +
SpanContext + Null-Adapter + additive TickLoop-Hooks; `make
fullbuild` cache-frei gruen ohne Override, §4.1 erfuellt) und
Welle 6 (OTLP-Adapter, `c98ce1a..46dbd6e` inkl. Trigger-029-
Closure als Fehlbefund: 1023 Unit-Tests + 21 Integration-Tests,
OtlpLog/Metrics/TraceAdapter + build_otlp_adapters-Factory +
deploy/compose.yml-otel-collector-Sibling + Compose-Smoke mit
Tripel-Assert Span+Metric+Log, §4.5.7 Sink-Determinismus-
Pflichten 1-4 erfuellt, `AC-OTLP-ADAPTER-NO-TIME` als
12. arch_check-Contract aktiv).
**Datum:** 2026-05-23
**Status geaendert am:** 2026-05-25 — `Provisional → Accepted`
(M3-Welle-7-Closure-Lauf C1.3; ADR-Header-Schliff ohne
Architektur-Aenderung).
**Vorherige Aenderung (2026-05-23)** — `Proposed → Provisional`.
**Letzte inhaltliche Aenderung:** 2026-05-25 — `Provisional →
Accepted`-Closure-Schliff (Status-Update + Welle-5/6-Beleg
ergaenzt; keine Architektur-Aenderung). **Vorherige Aenderung
(2026-05-24)** — Slice 027 Paket C:
`LogPort.log`-Surface auf `log(entry: LogEntry)` umgestellt (vorher
6-Parameter `level/message/run_id/module/event_id/attributes`).
Pflicht-Felder bleiben inhaltlich identisch (`GG-OTEL-002`),
werden jetzt am `LogEntry`-frozen-dataclass-Envelope getragen.
Adapter (NullLogAdapter, OtlpLogAdapter) + TickLoop-`_obs_log`-
Helper + alle Tests entsprechend nachgezogen. Schaerfung-ohne-
Supersede per ADR 0011. **Vorherige Aenderung (2026-05-24)** —
Welle-6-C1.2-Schaerfungen: neue §4.5 loest die §4.4-Forward-Pointer
L-2/N-1/N-2/Sentinel-Pattern/Trace-ID-Determinismus normativ auf;
nimmt zusaetzlich die in `M3-welle-6.md` festgelegten C0-Decisions
(D-4 = kein `time.*` im Adapter-Code; gRPC-Transport-Pinning;
Compose-Smoke-Determinismus-Pattern mit Sink-Isolation + Flush +
Poll) als verbindliche Welle-6-Vertraege in diese ADR auf.
**Vorherige Aenderung (2026-05-23)** — Welle-5-Review-Folge-Schaerfungen: §1 N-3
(`ADR 0022 §2.5 → §2.4` Pre-Tick-Hook-Korrektur); §2.6 M-1
(Log-/`tick_duration_ms`-Hooks als Welle-6-Material qualifiziert);
§4.3 M-2 (Welle-6-Forward-Pointer fuer Sentinel-Pattern, Trace-ID-
Determinismus, Vertragsschnitt); §7 (L-2/N-1/N-2 Out-of-Scope-
Erweiterungen); `Bezug:`-Liste L-3 (`ADR 0011` ergaenzt). Vor-
`Accepted`-Schliff per ADR 0006 §4; ADR-Index `Letzte inhaltliche
Aenderung`-Datum gepflegt.
**Bezug:**
[Lastenheft](../../../spec/lastenheft.md) §19 Telemetrie
(`GG-OTEL-001..004`),
[Architektur](../../../spec/architecture.md) §4.2 Driven-Ports-Tabelle
(`GG-AR-PORT-DRN-008`), §5 Komponentensicht (`GG-AR-COMP-OBS`), §15
Beobachtbarkeit,
[`ADR 0007`](0007-random-port.md) (Driven-Port-Pattern-Praezedenz,
PRNG-Wahl + Seeding-Kette),
[`ADR 0022`](0022-fault-injection-protocol.md) (FaultPort als
Driven-Port-Schwester),
[`ADR 0023`](0023-agent-bus-protocol.md) §2.6 (Observability-
Vorgriff-Verbot fuer Welle 3 — diese ADR loest das auf),
[`ADR 0026`](0026-agent-drain-registry-pattern.md) (Agent-
Schritt-A0v/A0a + TickLoop-Schritt-Reihenfolge, die Welle-5-Hooks
nicht antasten duerfen),
[`ADR 0028`](0028-link-maintenance-accepted-adr-bezug.md) (Bezug-Pfad-
Pflege als Maintenance-Edit),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Schaerfung-ohne-
Supersedes-Pattern als Fallback bei Welle-6-OTLP-Compose-Smoke-Bruch,
siehe §4.2),
M3-Slice-Plan
[`in-progress/M3-faults-agents-observability.md §3 Welle 5/6`](../planning/done/M3-faults-agents-observability.md),
Welle-5-Slice-Doc
[`done/M3-welle-5.md §3`](../planning/done/M3-welle-5.md)
(Welle-5-Triage-Vorgabe — diese ADR formalisiert die dort gesetzten
Contracts),
Welle-6-Slice-Doc
[`done/M3-welle-6.md §3`](../planning/done/M3-welle-6.md)
(Welle-6-C0-Decisions: gRPC-Transport, D-4 Span-Dauer-Quelle, Compose-
Smoke-Determinismus — §4.5 unten nimmt sie normativ in diese ADR auf).

---

## 1. Kontext

Architektur §15 (Beobachtbarkeit) verlangt drei distinkte
Observability-Aspekte:

- **Strukturierte Logs** (`GG-OTEL-002`): JSON mit `ts`, `level`,
  `run_id`, `module`, `event_id`, `message`.
- **Metriken** (`GG-OTEL-003`): `tick_duration_ms`,
  `event_queue_len`, `telemetry_points_per_s`, `error_count`,
  `replay_diff_status`.
- **Traces** (`GG-OTEL-001`/`004`): optional OTLP, traversierender
  Span Tick → Scheduler → Device → Adapter → Persistenz.

Architektur §4.2 buendelt diese drei Aspekte unter einem
**Driven-Port-Trio** `GG-AR-PORT-DRN-008` (`LogPort`, `MetricsPort`,
`TracePort`). Komponentensicht §5 lokalisiert die produktiven
Adapter unter `adapters/driven/telemetry-*` (`GG-AR-COMP-OBS`).

`ADR 0023 §2.6` (Welle-3-Multi-Agent) hat das **Observability-
Vorgriff-Verbot** dokumentiert: AgentBus/Agent **injizieren keine**
LogPort/MetricsPort/TracePort in Welle 3 — der Wiring-Entscheid
liegt explizit bei dieser ADR. Welle 4 (Multi-Agent-Konkretisierung)
hat die Klausel respektiert; M3-Welle-5 loest das Vorgriff-Verbot
jetzt auf.

`ADR 0022 §2.4` (FaultPort) hat den Pre-Tick-Hook eingefuehrt und
`ADR 0026 §2.1` die Schritte A0v / A0a fixiert. Beide setzen
Reihenfolge-Vertraege, die Welle-5-Hooks **nicht antasten** duerfen
(nur additive Anhaengung).

`Open-Trigger 006` (`--strict-bytes`-Aktivierung,
[`open/006-mypy-strict-bytes.md`](../planning/done/006-mypy-strict-bytes.md))
ist potentieller Konsument: OTLP-Adapter (Welle 6) arbeitet auf
Protobuf-Bytes-Pfaden. Welle 5 fuehrt **noch keinen** Bytes-Vertrag
ein — Trigger 006 bleibt mit Welle-6-Aktivierungs-Notiz offen.

Welle-5-Slice-Doc
[`M3-welle-5.md §3`](../planning/done/M3-welle-5.md) hat die
Triage-Resultate vor C1 festgelegt; diese ADR schreibt sie normativ
auf, ohne sie ergebnis-offen neu zu verhandeln.

---

## 2. Entscheidung

### 2.1 Gemeinsame Port-Surface-Form (alle drei Ports)

- **`typing.Protocol`** mit `@runtime_checkable`.
- **Stateless** — Port-Protocols definieren nur Methoden-Signaturen.
  Adapter halten ihren eigenen State (Sink, Buffer, Span-Tabelle).
- **Keine Default-Methoden** im Protocol-Body. Jede Methode ist eine
  reine Signatur (Ellipsis-Body).
- **Keine Seiteneffekte** auf Port-Ebene. Beobachtbar wird Telemetrie
  ausschliesslich durch konkrete Adapter (Null oder OTLP).
- **Keine externen OTLP-/SDK-Typen** in `ports/`-Layer. Span-/
  Metric-Datenstrukturen, die zwischen Core und Port-Surface
  ausgetauscht werden, sind interne, projekt-eigene Typen (siehe
  §2.4 `SpanContext`). Damit bleibt der Core OTLP-frei und kann
  ohne den OTLP-Stack ausgefuehrt werden.

Die Ports leben unter `src/grid_gym/hexagon/ports/driven/
observability.py` (drei Protocols in einer Datei — gemeinsame Domain
„Observability", konsistent zur Bundelung in `GG-AR-PORT-DRN-008`).

### 2.2 `LogPort`

```python
@dataclass(frozen=True, slots=True)
class LogEntry:
    level: str
    message: str
    run_id: str | None = None
    module: str | None = None
    event_id: str | None = None
    attributes: Mapping[str, object] | None = None


class LogPort(Protocol):
    def log(self, entry: LogEntry) -> None: ...
```

- Surface deckt die in Architektur §15 / `GG-OTEL-002` geforderten
  Pflicht-Felder ab — die Felder leben jetzt am `LogEntry`-Envelope
  (Slice 027 Paket C, ADR 0011-Schaerfung). Inhaltlich identisch zur
  vorherigen 6-Parameter-Signatur; der Aufrufer hat jetzt eine
  Single-Object-Surface.
- `level` ist als String typisiert (nicht als Enum), um dem Core
  keine Level-Hierarchie aufzuzwingen — Adapter sind frei in der
  Mapping-Wahl (z. B. Python-`logging.DEBUG/INFO/...`).
- `attributes` ist die strukturierte Payload (zusaetzliche Felder
  ueber das `GG-OTEL-002`-Pflichtset hinaus).
- `ts` wird **nicht** als Parameter gefuehrt — Adapter zieht die
  Zeit (typischerweise per `ClockPort` injiziert; Wall-Clock fuer
  Live, Simulations-Clock fuer Replay).

### 2.3 `MetricsPort`

```python
class MetricsPort(Protocol):
    def increment(
        self,
        name: str,
        value: int = 1,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None: ...

    def gauge(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None: ...

    def observe(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None: ...
```

- Drei Methoden decken die drei in §15 / `GG-OTEL-003` genannten
  Metrik-Familien ab:
  - `increment` — monoton steigende Counter (z. B.
    `error_count`, `telemetry_points_per_s`-Aggregator).
  - `gauge` — momentane Werte (z. B. `event_queue_len`).
  - `observe` — Verteilungen / Histogramme (z. B.
    `tick_duration_ms`).
- `name` ist String — kein Enum, kein zentrales Registry. Metric-
  Naming-Konvention lebt im OTLP-Adapter und in den Aufrufern.
- `attributes` ist Mapping-basierte Dimensionierung (typische
  OTLP-Praxis: Labels/Tags).

### 2.4 `TracePort` und `SpanContext`

```python
@dataclass(frozen=True, slots=True)
class SpanContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None = None


class TracePort(Protocol):
    def start_span(
        self,
        name: str,
        *,
        parent: SpanContext | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> SpanContext: ...

    def end_span(self, context: SpanContext) -> None: ...

    def record_event(
        self,
        context: SpanContext,
        name: str,
        attributes: Mapping[str, object] | None = None,
    ) -> None: ...
```

- `SpanContext` ist ein **internes, projekt-eigenes** frozen
  dataclass — keine OTLP-/W3C-Trace-Spec-Bindung im Port-Layer
  (siehe §2.1). Der OTLP-Adapter mapt es bei Bedarf auf den
  W3C-Standard.
- `trace_id` / `span_id` sind String-basiert (Adapter waehlt die
  Erzeugung — UUID, OTLP-W3C-Format, Hex-Identifier; Core nimmt
  den String opaque).
- `start_span` **gibt** den `SpanContext` zurueck — Aufrufer muss
  ihn fuer `end_span` und `record_event` weiterreichen.
- `end_span` und `record_event` nehmen `SpanContext` als
  **Pflichtparameter** (kein `Optional`). Aufrufer ist
  verantwortlich, den Kontext zu fuehren.
- Falls ein Aufrufer dennoch `None` weiterleitet (defensiver
  Programmierstil, z. B. wenn ein vorgelagerter Span nicht
  geoeffnet wurde), gilt **No-Op** als erlaubtes Fallback-Verhalten
  im Adapter (keine Exception, keine Seiteneffekte). Das ist nur
  fuer Adapter-Robustheit relevant — das Type-System verlangt
  ihn nicht.

### 2.5 Null-Adapter-Trio

Welle 5 liefert drei produktive **Null-Adapter** unter
`src/grid_gym/adapters/driven/observability_null/`:

- `NullLogAdapter(LogPort)`
- `NullMetricsAdapter(MetricsPort)`
- `NullTraceAdapter(TracePort)`

Pflicht-Surface jedes Adapters (auch im `record_calls=False`-
Default):

- `call_count: int` — Anzahl der ausgefuehrten Method-Aufrufe
  (alle Methoden zusammengezaehlt).
- `last_call: <CallRecord> | None` — letzter Aufruf als
  strukturierter Record (Methoden-Name + Args).

Erweiterungs-Surface bei `record_calls=True` (Konstruktor-Kwarg):

- `call_records: Sequence[<CallRecord>]` — vollstaendige Aufruf-
  Historie, append-only.
- `clear_calls() -> None` — Reset (setzt `call_count` zurueck auf
  `0`, `last_call` auf `None`, `call_records` auf `[]`).

Default ist `record_calls=False` — die strukturierte `call_count`/
`last_call`-Oberflaeche ist immer verfuegbar, aber kein voller
History-Speicher-Overhead in produktiven Test-Default-Pfaden. Tests,
die mehr als „wurde aufgerufen?" + „mit welchen letzten Args?"
brauchen, opt-in via `record_calls=True`.

`NullTraceAdapter.start_span(...)` gibt einen deterministischen
`SpanContext` zurueck (z. B. mit `trace_id=f"null-{counter}"`),
damit nachgelagerte `end_span` / `record_event` einen gueltigen
Kontext fuehren koennen.

### 2.6 Hook-Verdrahtung (TickLoop / Agent / Fault)

Welle 5 haengt Telemetrie-Hooks **rein additiv** an die in
[`ADR 0022 §2.4`](0022-fault-injection-protocol.md),
[`ADR 0023 §2.4`](0023-agent-bus-protocol.md), und
[`ADR 0026 §2.1`](0026-agent-drain-registry-pattern.md) fixierten
TickLoop-Schritte an. **Keine Reihenfolge-/Schritt-Aenderung** und
keine Modifikation existierender Atomizitaets-/Drain-Vertraege.

- TickLoop:
  - `MetricsPort.observe("tick_duration_ms", ...)` — **Welle-6-OTLP-
    Adapter-Material**, **nicht** aus TickLoop selbst emittiert.
    `AC-NO-TIME` verbietet Wall-Clock-Zugriff im Core; der OTLP-
    Adapter instrumentiert die Tick-Dauer extern via eigene Clock-
    Quelle (z. B. OpenTelemetry-Runtime-Hook).
  - `MetricsPort.gauge("event_queue_len", ...)` nach Scheduler-Drain
    (Welle-5-C2 produktiv).
  - `MetricsPort.increment("tick_count", ...)` am Tick-Ende (Welle-5-
    C2 produktiv; Counter, kein Gauge — Welle-6-Naming-Konvention
    fuer `tick_index`-Gauge bleibt OTLP-Adapter-Verantwortung).
  - `LogPort.log("info", "tick_begin"/"tick_end", ...)` als Per-Tick-
    Trail (Welle-5-C2 produktiv); Default-Null-Adapter frisst die
    Aufrufe, der produktive OTLP-Adapter kann sie filtern.
- Agent (siehe ADR 0023 §2.6 — Vorgriff-Verbot wird hier
  aufgeloest):
  - `TracePort.start_span("agent.tick", parent=<tick-span>)` /
    `end_span` als Wrap pro Agent-Tick (Welle-5-C2 produktiv).
  - `LogPort.log("info", "agent decision", attributes={...})` —
    **Welle-6-Material**; Welle-5-Minimum ist der Span-Wrap. Welle 6
    entscheidet im OTLP-Adapter, ob Decision-Logs zusaetzlich zum
    Span emittiert werden (Span-Attribute koennen die gleiche
    Information tragen).
- Fault (siehe ADR 0022 §2.4):
  - `TracePort.start_span("fault.inject", parent=<tick-span>)` /
    `end_span` um `FaultPort.apply_active_faults(...)` (Welle-5-C2
    produktiv).
  - `LogPort.log("warn", "fault active", attributes={...})` —
    **Welle-6-Material**; Welle-5-Minimum ist der Span-Wrap. Der
    Audit-Trail-Log waere pro aktivem Fault, nicht pro Tick — Welle 6
    entscheidet, ob TickLoop oder der Fault-Adapter selbst die Logs
    emittiert (Adapter-Side-Logs sind feiner granuliert).

Konkrete Hook-Positionen + Span-Schachtelung sind C2-Material und
werden im Welle-5-C2-Commit verdrahtet.

Konstruktor-Symmetrie (analog ADR 0022 / ADR 0023 / ADR 0026):

```python
class TickLoop:
    def __init__(
        self,
        ...,
        log_port: LogPort | None = None,
        metrics_port: MetricsPort | None = None,
        trace_port: TracePort | None = None,
    ) -> None: ...
```

- Default `None`: Hook **skippt**, kein produktiver Adapter wird
  angelegt. Konsistent zum ADR-0022-`fault_port: FaultPort | None`-
  und ADR-0023-`agent_bus: AgentMessageBus | None`-Pattern.
- `build_tick_loop(...)` (ADR 0021 §2.4) wird symmetrisch um
  `log_port=`/`metrics_port=`/`trace_port=`-Kwargs erweitert.

### 2.7 Trigger-006 (`--strict-bytes`) deferred

Welle 5 entscheidet **nicht** ueber die `--strict-bytes`-Aktivierung
(`open/006-mypy-strict-bytes.md`). Begruendung: der Bytes-Vertrag
entsteht erst mit dem OTLP-Adapter in Welle 6 (Protobuf-Encoding-
Pfad). Welle 5 fuehrt keine `bytes`-typisierten Port-Methoden ein —
alle Strings sind `str`, alle Attributes sind `Mapping[str, object]`.

Trigger 006 bleibt `Open` mit Welle-6-Aktivierungs-Notiz; eine
Folge-ADR oder ein C1-Trigger-Closure-Doc adressiert die Aktivierung
mit der Welle-6-Lieferung.

---

## 3. Begruendung

- **Triade-Symmetrie:** Drei Aspekte aus `GG-OTEL-001..004` und
  Architektur §15 werden als **drei separate Ports** modelliert
  (statt eines monolithischen `ObservabilityPort`). Vorteil:
  Test-Doubles koennen einzeln injiziert werden, OTLP-Adapter kann
  pro Aspekt unterschiedliche Sinks/Transports waehlen, und der
  Core-Hook-Code kann gezielt einen Aspekt nutzen, ohne die anderen
  zwei mit-zuziehen.
- **Stateless Protocols statt Abstract Bases:** Konsistent zu
  `ADR 0007` (RandomPort), `ADR 0022` (FaultPort), `ADR 0023`
  (`Agent`-Sub-Protocol). Keine Vererbungsschicht im Port-Layer.
- **Keine OTLP-Typen im Port-Layer:** Schliesst das Risiko aus,
  dass der Core zur Compile-/Import-Zeit auf den OTLP-SDK angewiesen
  ist. Null-Adapter-Tests laufen ohne OTLP-Stack. `AC-PORTS-NO-OUT`
  bleibt damit trivial gewahrt.
- **`SpanContext` als internes frozen dataclass:** Drei String-
  Felder reichen fuer die in §15 geforderte Traversierungs-Kette
  (Tick → Scheduler → Device → Adapter → Persistenz). Erweiterung
  um Sampling/Baggage bleibt einer Folge-ADR (z. B. Welle-6-OTLP-
  Adapter) vorbehalten.
- **Null-Adapter mit Default-`call_count`/`last_call`:**
  Senkt das in
  [`M3-welle-5.md §7 R-2`](../planning/done/M3-welle-5.md)
  identifizierte Coverage-Risiko der Null-Default-Verdrahtung —
  Tests haben **immer** eine strukturierte Assertion-Surface, ohne
  explizit `record_calls=True` aktivieren zu muessen. Voll-History
  bleibt opt-in fuer Tests, die sie wirklich brauchen.
- **Additive Hook-Verdrahtung:** Schliesst Reihenfolge-/Atomizitaets-
  Drift gegenueber ADR 0022 / 0023 / 0026 aus. Welle-5-C2 darf nur
  Hook-Aufrufe einfuegen, nicht bestehende Schritt-Reihenfolge
  umstellen.
- **Trigger-006-Defer:** Welle 5 hat keine `bytes`-Pfade — die
  Aktivierung der `--strict-bytes`-mypy-Klausel braucht den
  konkreten OTLP-Protobuf-Konsumenten aus Welle 6, sonst ist die
  Pflege-Investition Spekulation.

---

## 4. Reichweite

### 4.1 Welle-5-Validation-Spike-Vertrag (`Proposed → Provisional`)

Diese ADR ist `Proposed` zum Zeitpunkt der M3-Welle-5-C1. Sie wird
mit dem Welle-5-Merge auf `Provisional` gehoben, sofern der
Lieferungs-Vertrag aus
[`M3-welle-5.md §6 Verifikationspfad`](../planning/done/M3-welle-5.md)
gruen ist:

- `make gates` A-1 ohne Override.
- `make test-unit` mit den 3 Port-Surface-Tests, 3 Null-Adapter-
  Roundtrip-Tests, Tick-/Agent-/Fault-Default-Null-Hook-Tests.
- `make test-integration` mit Multi-Agent-Demo
  (`agents_demo.yaml`) und Fault-Demo unter Null-Adapter-Default —
  Null-Adapter-Metriken/Logs nachweislich aufgerufen.
- `make fullbuild` cache-frei gruen ohne Override (Compose-Smoke
  ohne OTLP-Collector-Asserts; jene sind Welle-6-AC).
- `AC-PORTS-NO-OUT` KEPT.

### 4.2 `Provisional → Accepted` mit M3-Welle-7-Closure

Voll-Acceptance setzt zusaetzlich voraus, dass Welle 6 (OTLP-
Adapter) den `TracePort`-/`MetricsPort`-/`LogPort`-Vertrag in der
produktiven Compose-Smoke gegen einen realen OTLP-Collector
exerziert hat. Bricht der Welle-6-Span-Export, wird `ADR 0024`
zurueckgeklappt oder per Folge-ADR (Schaerfung ohne Supersede,
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md)-Pattern) angepasst.

### 4.3 Out-of-Scope

- OTLP-Adapter-Implementierung (Welle 6).
- OTLP-Collector-Service in `deploy/compose.yml` (Welle 6).
- Compose-Smoke-Span-/Metric-Export-Asserts (Welle 6).
- Dashboards, Alerts, Trace-Korrelation in Multi-Service-Szenarien
  (Post-M3).
- Sampling-/Baggage-Felder im `SpanContext` (Welle 6 oder spaeter).

### 4.4 Welle-6-Forward-Pointer (Review-Folge M-2)

Carry-Over-Lessons aus Welle 3/4a/4b, die fuer den Welle-6-OTLP-
Adapter Welle-5-Vertrags-Stellen schaerfen:

- **Sentinel-Pattern fuer `scenario.observability`-Block** (Welle-4b-
  F-1-Parallel): falls Welle 6 einen optionalen `scenario.observability:`-
  Block einfuehrt, muss `build_tick_loop(..., log_port=None, ...)` auf
  `None`-Sentinel = „aus Scenario ableiten" und `()` / expliziter
  Skip-Adapter = „kein Hook" umgestellt werden. Aktuelles Welle-5-
  `None` ist eindeutig „Skip", weil es keinen Scenario-Block gibt;
  ein Welle-6-Sentinel-Bruch ist sonst silent (analog dem ADR-0027-
  `agents=()`-Default-Bug, der per F-1 mit `agents=None`-Sentinel
  behoben wurde).
- **Trace-ID-Determinismus** (Welle-3-M-3-Parallel): Der Welle-6-
  OTLP-Adapter erzeugt W3C-128-bit-`trace_id`/`span_id`. Determinismus
  ist eine Welle-6-Entscheidung — entweder ueber
  `RandomPort.sub_port("observability-trace")` (deterministisch pro
  Lauf, konsistent zu ADR 0007 §5/§6 + ADR 0026 §2.3 Sub-Random-
  Stream-Konvention `agent-{agent_id}`) oder ueber externe Entropie
  (Determinismus-Garantie aufgegeben, OTLP-Standard-Verhalten).
  Welle 6 dokumentiert die Wahl + Begruendung.
- **Welle-6-Vertragsschnitt** (Welle-4b-F-2-Parallel): Welle 6 darf
  `SpanContext.trace_id`/`span_id`-String-Werte intern in das W3C-
  Hex-Format mappen — die `start_span`/`end_span`/`record_event`-
  Port-Signaturen + die `SpanContext`-Felder
  (`trace_id`/`span_id`/`parent_span_id`) sind Welle-5-eingefroren.
  Ein Welle-6-Bruch (z. B. neues `SpanContext`-Feld, neue Methoden-
  Signatur) braucht Folge-ADR per `ADR 0011`-Schaerfungs-Pattern.
- **Type-Signatur-Asymmetrie `end_span`/`record_event`** (Review-
  Folge L-2): Null-Adapter akzeptiert `SpanContext | None` (No-Op-
  Robustheit per §2.4); das Protocol verlangt `SpanContext`
  (strikt). Welle 6 muss diese Asymmetrie aufloesen — entweder das
  Protocol auf `SpanContext | None` erweitern (Single-Source-of-Truth
  fuer die No-Op-Invariante) oder den OTLP-Adapter explizit mit
  `| None`-Signatur bauen + ADR-0024-Notiz dazu.
- **Counter-vs-Gauge-Naming** (Review-Folge N-1): Welle-5 emittiert
  `MetricsPort.increment("tick_count", ...)` (Counter). Architektur
  §15 nennt `tick_index` als Gauge. Welle 6 OTLP-Adapter klaert die
  Naming-Konvention (z. B. `ticks_total` als Counter +
  `tick_index_current` als Gauge), damit Dashboards die Semantik
  nicht verwechseln.
- **`_obs_observe`-Helper-Symmetrie** (Review-Folge N-2): TickLoop
  hat `_obs_gauge` + `_obs_increment` Helper, aber bewusst kein
  `_obs_observe` (Histogramme braeuchten Wall-Clock-Quelle, die
  `AC-NO-TIME` im Core verbietet). Welle 6 OTLP-Adapter kann externe
  Histogramme instrumentieren; falls TickLoop spaeter einen
  `observe`-Use-Case ohne Wall-Clock findet (z. B. Verteilung von
  `event_queue_len`-Werten), ergaenzt eine Folge-Welle den Helper
  symmetrisch.

### 4.5 Welle-6-C1.2-Schaerfungen

Diese Sektion loest die in §4.4 dokumentierten Welle-6-Forward-
Pointer mit normativen C1.2-Entscheidungen auf und nimmt zusaetzlich
die in
[`M3-welle-6.md`](../planning/done/M3-welle-6.md)
festgelegten C0-Decisions verbindlich in diese ADR auf. Schaerfung-
ohne-Supersede per [`ADR 0011`](0011-schaerfung-ohne-abloesung.md).
Folge-Vertraege gelten fuer den OTLP-Adapter in
`adapters/driven/telemetry_otlp/` (C1.3-Lieferung).

#### 4.5.1 L-2 — Type-Signatur-Asymmetrie `end_span`/`record_event`

**Entscheidung:** Adapter-spezifische `| None`-Signatur (keine
Protocol-Erweiterung).

- Das `TracePort`-Protocol bleibt **strikt** (`SpanContext` als
  Pflichtparameter, §2.4 unveraendert). Aufrufer-Vertrag bleibt:
  „immer einen gueltigen Kontext fuehren".
- Adapter (Null + OTLP) implementieren `def end_span(self,
  context: SpanContext | None) -> None` und `def record_event(
  self, context: SpanContext | None, ...) -> None` mit
  `if context is None: return` als erste Anweisung. Die No-Op-
  Robustheit aus §2.4 bleibt damit **Adapter-Verantwortung**, nicht
  Protocol-Pflicht.
- Begruendung gegen Protocol-Erweiterung: wuerde den Aufrufer-
  Vertrag retroaktiv permissiv machen („None ist OK"). §2.4 haelt
  ihn explizit auf „Aufrufer ist verantwortlich" — die
  `| None`-Robustheit ist defensiver Fallback, kein API-Versprechen.
- C1.3-Konsequenz: `OtlpTraceAdapter.end_span` und `.record_event`
  in `telemetry_otlp/traces.py` muessen die `| None`-Robustheit
  mit der `if context is None: return`-Praefix-Pruefung absichern.

#### 4.5.2 N-1 — Counter-vs-Gauge-Naming

**Entscheidung:** `tick_count` bleibt **Counter** (Welle-5-
Verdrahtung unangetastet); kein `tick_index`-Gauge ergaenzt.

- Architektur §15 nennt `tick_index` als Gauge-Beispiel — ohne
  konkreten UI-/Dashboard-Konsumenten ist die Ergaenzung YAGNI.
- Welle-5-Counter `tick_count` deckt das Monotonie-Beduerfnis
  vollstaendig ab; OTLP-Adapter mappt ihn auf einen OTel-`Counter`-
  Instrument (monoton steigend) ohne Naming-Bruch.
- Re-Open: ein konkreter UI-/Dashboard-Use-Case (M5) kann
  `tick_index` als Gauge per Folge-Welle ergaenzen — **nicht**
  silent im OTLP-Adapter.

#### 4.5.3 N-2 — `_obs_observe`-Helper-Symmetrie

**Entscheidung:** kein Helper.

- §4.5.5 D-4 (unten) faengt das Wall-Clock-Argument: der OTLP-
  Adapter bekommt Span-Dauern von der OTel-SDK direkt; ein
  `_obs_observe`-Helper im Core wuerde eine Wall-Clock-Affordance
  simulieren wollen (Histogramm-Werte mit Zeit-basierten Buckets)
  und damit gegen `AC-NO-TIME` verstossen.
- Re-Open: falls TickLoop spaeter einen `observe`-Use-Case
  **ohne** Wall-Clock findet (z. B. Verteilung von
  `event_queue_len`-Werten ueber N Ticks), wird der Helper
  symmetrisch zu `_obs_increment` / `_obs_gauge` ergaenzt —
  aber **nicht** fuer Zeitmessung.

#### 4.5.4 Sentinel-Pattern fuer `scenario.observability`-Block

**Entscheidung:** deferred auf Folge-Slice (M3-Welle-7+ oder
M4-Slice).

- Welle 6 nutzt `build_otlp_adapters(config=...)`-Factory statt
  Scenario-Schema-Eintrag. Konfiguration kommt ueber OTel-Standard-
  Env-Vars (`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`,
  `OTEL_RESOURCE_ATTRIBUTES`) plus expliziten `OtlpAdapterConfig`-
  Kwargs.
- Sentinel-Pattern (`None` = aus Scenario ableiten vs. `()` =
  expliziter Skip-Adapter) ist nur dann notwendig, wenn der
  Aufrufer-Pfad mehrere Quellen fuer Telemetrie-Konfig hat — der
  ist in Welle 6 nicht vorhanden. Aktuelles Welle-5-`None`
  bleibt eindeutig „Skip" (Default-Verhalten).
- Re-Open: ein expliziter `scenario.observability:`-Block in
  Welle 7+ (oder M4) braucht eine Folge-ADR mit
  Sentinel-Semantik-Definition (analog ADR-0027-`agents=None`-
  Sentinel-Fix).

#### 4.5.5 D-4 — Span-Dauer-Quelle (kein `time.*` im Adapter)

**Entscheidung:** Adapter-Code importiert **kein** `time` (weder
Modul-Import noch via Sub-Aufrufe).

- Start- und End-Zeitpunkte werden vom OTel-Span/SDK selbst
  gesetzt: `tracer.start_span(...)` setzt `StartTime`,
  `span.end()` setzt `EndTime`. `BatchSpanProcessor` / `Periodic-
  ExportingMetricReader` sind reine Export-Vehikel und messen
  nicht.
- Konsequenz fuer C1.3: `telemetry_otlp/`-Modul darf
  `import time` (oder `datetime`, `monotonic`, `perf_counter`)
  vollstaendig ausschliessen. `AC-NO-TIME` bleibt damit auch im
  Adapter-Code KEPT — Wall-Clock-Affordance liegt eine Schicht
  tiefer in der externen OTel-SDK.
- Die `AC-NO-FW`/`AC-PORTS-NO-FW`-Erweiterung um `opentelemetry`
  und `grpc` (C1.1) schuetzt den Core doppelt: kein OTel-Import
  im Core + kein Wall-Clock-Pfad im Adapter, der den Geist von
  AC-NO-TIME unterlaufen wuerde.
- Re-Open dieser Entscheidung nur per ADR-Folge (Schaerfung
  oder neuer ADR), nicht im C1.3-Code-Pfad.

#### 4.5.6 gRPC-Transport-Pinning

**Entscheidung:** OTLP-Transport in Welle 6 ist **gRPC**;
Pinning auf zwei Ebenen.

- **Adapter-seitig:** `OtlpAdapterConfig.protocol` validiert auf
  Allow-List `{"grpc"}`. Andere Werte erzeugen `ValueError` /
  `OtlpAdapterConfigError` (C1.3-Detail). HTTP/protobuf ist
  explizit Out-of-Scope (M3-welle-6.md §2) — Oeffnung erfordert
  Konfig-Erweiterung **plus** Folge-Welle.
- **Compose-seitig:** API-/Sim-Container bekommen
  `OTEL_EXPORTER_OTLP_PROTOCOL=grpc` per `environment`-Block
  (M3-welle-6.md §3 C2). Damit kann ein zukuenftiger SDK-Default-
  Wechsel den Export-Pfad nicht still auf `http/protobuf`
  umlenken.
- Begruendung gegen HTTP/protobuf-Parallelbetrieb in Welle 6:
  doppelte Konfig-/Test-Flaeche ohne klaren Mehrwert; HTTP-
  Transport hat hoehere Per-Request-Overhead und bringt keine
  Welle-6-spezifische Eigenschaft mit, die `grpc` nicht traegt.
- Re-Open fuer HTTP/protobuf: eigene Folge-ADR-Notiz + Konfig-
  Erweiterung der Allow-List.

#### 4.5.7 Compose-Smoke-Determinismus-Pattern (Welle-6-AC)

**Entscheidung:** Smoke-Tests gegen den OTLP-Collector-Sibling
muessen **vier** Determinismus-Pflichten erfuellen (Quelle
M3-welle-6.md §3 C3 + §7 R-8/R-9). Dieses Pattern ist Welle-6-
spezifische Acceptance-Bedingung und ergaenzt §4.1.

1. **Per-Lauf isolierter Sink-Pfad** — z. B. `pytest`-`tmp_path`
   in `OTEL_COLLECTOR_FILE_SINK`-Env-Var; verhindert
   Cross-Run-Contamination bei konkurrierenden Lauefen.
2. **Vorab-Truncation der Sink-Datei** vor Compose-Boot
   (defensive — `tmp_path` sollte leer sein, aber Pflicht-
   Schritt, falls Compose-Volumes Reste tragen).
3. **Per-Lauf eindeutige `service.instance.id`** (`uuid4()`)
   via `OTEL_RESOURCE_ATTRIBUTES`; alle Sink-Eintrag-Asserts
   filtern auf diese ID. Damit kann selbst ein versehentlich
   geteilter Sink-Pfad die Assertion nicht faelschlich gruen
   faerben.
4. **Zweischichtiges Flush-Protokoll** vor Assertion:
   - **SDK-Seite (synchron):** `tracer_provider`/
     `logger_provider`/`meter_provider` jeweils
     `force_flush()` **und danach** `shutdown()`. Reihenfolge
     ist Pflicht — erst alle Provider flushen, dann shutdown
     (sonst flush-waehrend-shutdown unsicher).
   - **Collector-Seite (eventually):** kurze `batch.timeout`-
     Konfig im Smoke-Profil (z. B. 100ms) **plus** Bounded-
     Poll mit 5s-Timeout im 100-ms-Raster auf den Sink-File.
     Timeout-Fall produziert klaren Fehlertext, der den Flush-
     Pfad als verdaechtig markiert.

C1.3-Folge-Vertrag: `build_otlp_adapters(config)` muss die drei
Provider-Handles fuer Test-Use exponieren (entweder als Teil
des Factory-Return-Werts oder ueber eine `flush_and_shutdown()`-
Helper-Funktion). Konkrete Form ist C1.3-Detail; die
Existenz der Surface ist hier normativ festgeschrieben.

#### 4.5.8 Trace-ID-Determinismus

**Entscheidung:** OTel-Standard-Random (keine
`RandomPort.sub_port`-Bindung).

- OTel-SDK erzeugt `trace_id`/`span_id` standardmaessig per
  `secrets.token_bytes(16)` bzw. `secrets.token_bytes(8)` —
  kryptographisch zufaellig, nicht deterministisch pro Lauf.
- Determinismus-Eigenschaft von `RandomPort.sub_port` ist fuer
  Tick-/Scheduler-Determinismus relevant (gleicher Seed →
  gleiche Tick-Sequenz). Trace-IDs sind aber Cross-Cutting-
  Telemetrie, kein Tick-State — sie gehen **nicht** in
  Snapshots ein (§2.5 unangetastet); Welle-5-Snapshot-Schema
  enthaelt keine `spans/`-Sub-Snapshots.
- Konsequenz fuer Property-Tests: Snapshot-Determinismus-
  Asserts stuetzen sich **nicht** auf `SpanContext`-Werte.
  Trace-IDs sind in produktiven Lauefen zufaellig (OTLP-
  Standard); C3-Compose-Smoke filtert per `service.instance.id`
  (per-Lauf eindeutiger UUID, siehe §4.5.7 Punkt 3), nicht per
  `trace_id`.
- Re-Open: nur, wenn ein konkreter Use-Case deterministische
  Trace-IDs braucht (z. B. Cross-Process-Test-Replay), dann
  per Folge-ADR mit `RandomPort.sub_port("observability-
  trace")`-Bindung (analog ADR-0007 §5/§6 + ADR-0026 §2.3
  Sub-Random-Stream-Konvention).

---

## 5. Operative Artefakte

Welle-5-C2 liefert:

- `src/grid_gym/hexagon/ports/driven/observability.py` — drei
  Protocols + `SpanContext`-dataclass.
- `src/grid_gym/adapters/driven/observability_null/__init__.py`
  (oder Sub-Modul) — die drei Null-Adapter.
- TickLoop-Konstruktor + `build_tick_loop(...)` (siehe ADR 0021
  §2.4) um `log_port`/`metrics_port`/`trace_port` erweitert.
- Hook-Aufrufe in TickLoop (Tick-Telemetrie), AgentBus / Agent
  (Decision-Trail), Fault-Adapter (Span-Wrap + Audit-Log).
- Welle-5-Tests: Port-Surface (`typing.runtime_checkable`
  Verifikation), Null-Adapter-Roundtrip (`call_count`/`last_call`/
  `record_calls=True`-Pfade), Hook-Integration (Default-Null laeuft
  durch, Aufrufe sind sichtbar).

Optional (C1-Triage TBD, kann bei Bedarf in C2-Closure nachgezogen
werden):

- Neuer Architektur-Test-Contract `AC-OBS-NULL-DEFAULT` in
  `tools/arch_check.py`, falls eine maschinelle Invariante fuer
  Default-Null-Adapter-Verdrahtung sinnvoll erscheint. Eingangs-
  Hypothese: Tests verifizieren das ausreichend, kein neuer
  AC-Contract noetig.

Welle-6-C1.3 liefert (Spec aus §4.5 oben + M3-welle-6.md §3 C1):

- `src/grid_gym/adapters/driven/telemetry_otlp/__init__.py` —
  Re-Exports + `build_otlp_adapters(config)`-Factory mit
  Provider-Handles (Tracer/Logger/Meter) plus
  `flush_and_shutdown()`-Helper (§4.5.7 Punkt 4).
- `src/grid_gym/adapters/driven/telemetry_otlp/_config.py` —
  `OtlpAdapterConfig`-frozen-dataclass mit `endpoint`, `headers`,
  `timeout_s`, `batch_max_export_size`, `service_name`,
  `service_instance_id`, `protocol`-Feld (validiert auf
  Allow-List `{"grpc"}`, §4.5.6).
- `src/grid_gym/adapters/driven/telemetry_otlp/logs.py` —
  `OtlpLogAdapter` (`LogPort`-Implementer).
- `src/grid_gym/adapters/driven/telemetry_otlp/metrics.py` —
  `OtlpMetricsAdapter` (`MetricsPort`-Implementer).
- `src/grid_gym/adapters/driven/telemetry_otlp/traces.py` —
  `OtlpTraceAdapter` (`TracePort`-Implementer) mit
  `| None`-Robustheit (§4.5.1) und ohne `time.*`-Import (§4.5.5).
- `tests/unit/adapters/driven/telemetry_otlp/test_*.py` — Unit-
  Tests gegen In-Process-`grpcio`-Mock (Surface, Konfig-Defaults,
  Konfig-Validation, Failure-Modes).
- `Dockerfile` `ARG CRITICAL_COV_TARGETS` (Z. 245) um
  `src/grid_gym/adapters/driven/telemetry_otlp` erweitert
  (Default-Coverage-Target-Liste, filesystem-Pfad-Form analog
  bestehender Eintraege).
- OpenTelemetry-Dependencies in `pyproject.toml` + Lock-Sync —
  bereits C1.1-Lieferung (`opentelemetry-sdk>=1.42`,
  `opentelemetry-exporter-otlp-proto-grpc>=1.42`).
- Import-Linter-Contract-Erweiterung `AC-NO-FW` /
  `AC-PORTS-NO-FW` um `opentelemetry` + `grpc` — bereits
  C1.1-Lieferung.

C2-/C3-Lieferungen (Welle 6) liegen ausserhalb dieses ADR-
Updates: `deploy/compose.yml`-OTLP-Collector-Sibling,
`deploy/otel-collector-config.yaml`, Compose-/Integration-
Smoke-Test, Runbook `docs/user/observability.md`, README/
README.de-Closure-Zeile.

---

## 6. Konsequenzen

- **Positiv:** `GG-AR-PORT-DRN-008` ist nach `Provisional` eines
  vollwertigen Driven-Ports — die Architektur-Tabelle muss
  textlich nicht geaendert werden (nur Verweis auf diese ADR).
- **Positiv:** `ADR 0023 §2.6` (Observability-Vorgriff-Verbot) ist
  mit dem Welle-5-C2-Merge erfuellt — AgentBus/Agent koennen
  Telemetrie injizieren, ohne dass Welle-3-Surface umgestellt
  werden muss.
- **Positiv:** Null-Adapter-Default-Verdrahtung in allen
  bestehenden Welle-2-/-3-/-4-Tests bleibt kompatibel — Tests, die
  bisher ohne Observability-Hook gearbeitet haben, werden nicht
  geaendert (Default `None` skippt Hooks).
- **Positiv:** OTLP-Stack bleibt **Core-frei** — `make
  arch-check`-Imports verifiziert, dass kein `opentelemetry`-Import
  im Core liegt.
- **Neutral:** Welle 6 muss den `TracePort`-Vertrag implementieren
  und gegen reale OTLP-Collector-Spans verifizieren. Falls W3C-
  Trace-Spec einen anderen `parent_span_id`-Vertrag verlangt,
  passt der Adapter — der Core sieht weiter den projekt-eigenen
  String-Type.
- **Neutral:** `Open-Trigger 006` (`--strict-bytes`) wird nicht
  geschlossen. Bleibt mit Welle-6-Aktivierungs-Notiz im `open/`-
  Bestand.

---

## 7. Nicht Gegenstand dieser ADR

- ~~Wahl des konkreten OTLP-Transports (gRPC vs. HTTP)~~ —
  **geschlossen** mit Welle-6-C1.2-Schaerfung §4.5.6: gRPC ist
  gepinnt (Adapter-Config-Allow-List `{"grpc"}` + Compose-Env-
  Var `OTEL_EXPORTER_OTLP_PROTOCOL=grpc`). HTTP/protobuf bleibt
  Folge-Slice-Material.
- Strukturierte-Logs-JSON-Schema (Pflicht-Felder + erweiterte
  Attributes) jenseits der `GG-OTEL-002`-Grundfelder — Welle 6
  oder Folge-ADR.
- Metric-Naming-Konvention / Registry — lebt im OTLP-Adapter und
  in den Aufrufer-Modulen, nicht im Port-Vertrag.
- Sampling-Strategie / Baggage / Trace-Korrelation ueber Service-
  Grenzen — Post-M3.
- Trigger 006 (`--strict-bytes`)-Aktivierungs-Zeitpunkt — explizit
  deferred auf Welle 6 (§2.7).
- Healthcheck-Endpoint (`GG-DEPLOY-006`) — gehoert nicht zum
  Observability-Port-Trio, ist eigener Adapter-Surface in
  `adapters/driving/http_api/`.
