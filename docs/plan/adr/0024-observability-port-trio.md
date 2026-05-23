# ADR 0024 — Observability-Port-Trio: LogPort + MetricsPort + TracePort (M3 Welle 5)

**Status:** Proposed
**Datum:** 2026-05-23
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
M3-Slice-Plan
[`in-progress/M3-faults-agents-observability.md §3 Welle 5`](../planning/in-progress/M3-faults-agents-observability.md),
Welle-5-Slice-Doc
[`in-progress/M3-welle-5.md §3`](../planning/in-progress/M3-welle-5.md)
(Welle-5-Triage-Vorgabe — diese ADR formalisiert die dort gesetzten
Contracts).

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

`ADR 0022 §2.5` (FaultPort) hat den Pre-Tick-Hook eingefuehrt und
`ADR 0026 §2.1` die Schritte A0v / A0a fixiert. Beide setzen
Reihenfolge-Vertraege, die Welle-5-Hooks **nicht antasten** duerfen
(nur additive Anhaengung).

`Open-Trigger 006` (`--strict-bytes`-Aktivierung,
[`open/006-mypy-strict-bytes.md`](../planning/open/006-mypy-strict-bytes.md))
ist potentieller Konsument: OTLP-Adapter (Welle 6) arbeitet auf
Protobuf-Bytes-Pfaden. Welle 5 fuehrt **noch keinen** Bytes-Vertrag
ein — Trigger 006 bleibt mit Welle-6-Aktivierungs-Notiz offen.

Welle-5-Slice-Doc
[`M3-welle-5.md §3`](../planning/in-progress/M3-welle-5.md) hat die
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
class LogPort(Protocol):
    def log(
        self,
        level: str,
        message: str,
        *,
        run_id: str | None = None,
        module: str | None = None,
        event_id: str | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> None: ...
```

- Surface deckt die in Architektur §15 / `GG-OTEL-002` geforderten
  Pflicht-Felder ab.
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
[`ADR 0022 §2.5`](0022-fault-injection-protocol.md),
[`ADR 0023 §2.4`](0023-agent-bus-protocol.md), und
[`ADR 0026 §2.1`](0026-agent-drain-registry-pattern.md) fixierten
TickLoop-Schritte an. **Keine Reihenfolge-/Schritt-Aenderung** und
keine Modifikation existierender Atomizitaets-/Drain-Vertraege.

- TickLoop:
  - `MetricsPort.observe("tick_duration_ms", ...)` am Tick-Schluss.
  - `MetricsPort.gauge("event_queue_len", ...)` nach Scheduler-Drain.
  - `LogPort.log("info", "tick begin", ...)` / `"tick end"` als
    optionaler Per-Tick-Trail; Default-Adapter (Null) frisst die
    Aufrufe ohne Sichtbarkeit, der produktive Welle-6-OTLP-Adapter
    kann sie filtern.
- Agent (siehe ADR 0023 §2.6 — Vorgriff-Verbot wird hier
  aufgeloest):
  - `LogPort.log("info", "agent decision", attributes={...})` im
    `Agent.decide()`-Pfad.
  - `TracePort.start_span("agent.decide", parent=<tick-span>)`
    /`end_span` als optionaler Wrap.
- Fault (siehe ADR 0022 §2.5):
  - `TracePort.start_span("fault.inject", ...)` /`end_span` um
    `FaultPort.apply_active_faults(...)`.
  - `LogPort.log("warn", "fault active", attributes={...})` als
    Audit-Trail-Ereignis.

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
  [`M3-welle-5.md §7 R-2`](../planning/in-progress/M3-welle-5.md)
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
[`M3-welle-5.md §6 Verifikationspfad`](../planning/in-progress/M3-welle-5.md)
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

- Wahl des konkreten OTLP-Transports (gRPC vs. HTTP) — Welle 6
  per Folge-ADR oder Closure-Notiz.
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
