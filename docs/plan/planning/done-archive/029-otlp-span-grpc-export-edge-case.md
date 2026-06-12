# 029 — OTLP-Span-gRPC-Export-Edge-Case (Welle 6 C3 Caveat) — **Done: Fehlbefund**

**Status:** Done — geschlossen 2026-05-25, **Fehlbefund**: der
OTLP-Span-Export-Pfad war nie kaputt. Die ursprueng-beobachtete
„0 Spans im Collector"-Assertion-Failure lag am Span-Name-Regex
im Smoke-Test (`^Name\\s*:\\s*(\\S+)\\s*$`), das das vom Debug-
Exporter erzeugte Leading-Whitespace-Padding-Format
(`    Name           : tick.cycle`, 4 Leerzeichen) nicht
matchen konnte. Korrigiertes Regex: `^\\s*Name\\s*:\\s*(\\S+)\\s*$`
— Smoke-Test ist mit dem Fix wieder auf das volle Tripel
(Span+Metric+Log) hochgezogen und gruen.
**Quelle:** M3-Welle-6-C3-Smoke-Test
(`tests/integration/test_otlp_compose_smoke.py`); Befund waehrend
des Tripel-Assert-Bauversuchs (Span/Metric/Log).
**Ziel:** OTLP-gRPC-Span-Export Sibling-Container reproduzierbar
gruen bekommen — damit der Welle-6-Smoke auf das volle Tripel
(Span/Metric/Log) hochgezogen werden kann, das ADR 0024 §4.5.7
und M3-welle-6.md §C3 urspruenglich vorsehen. **Erreicht.**

---

## 0. Closure-Befund (2026-05-25, Fehlbefund)

Trigger 029 ist als Fehlbefund geschlossen. Der gesamte OTLP-
Span-Adapter-Pfad ist intakt; der einzige Bug lag im
Span-Name-Regex des Smoke-Tests selbst.

**Beweisfuehrung** (via `tools/diagnose_otlp_span_export.py`,
Matrix-Run 2026-05-25):

| Diagnose-Variante                  | collector_hits | Erkenntnis                                                |
| ---------------------------------- | -------------- | --------------------------------------------------------- |
| `http-batch-no-flag`               | 1              | spec-konform; identisch zum Smoke-Test-Setup, gruen        |
| `http-simple-no-flag`              | 1              | SimpleSpanProcessor mit `http://`-Endpoint, gruen          |
| `http-simple-insecure`             | 1              | explizit `insecure=True`, gruen                            |
| `hostport-simple-insecure`         | 1              | ohne `http://`-Schema, `insecure=True`, gruen              |
| `hostport-batch-insecure`          | 1              | BatchSpanProcessor + nackter `host:port`, gruen            |
| **`factory-bundle`** (Produktiv-Pfad) | 1            | voller `build_otlp_adapters` + `OtlpTraceAdapter` +    |
|                                    |                | `bundle.flush_and_shutdown`, **gruen**                    |

Collector-Internal-Counter im selben Lauf:

```
otelcol_receiver_accepted_spans{receiver="otlp",transport="grpc"} 6
otelcol_receiver_refused_spans{receiver="otlp",transport="grpc"} 0
otelcol_exporter_sent_spans{exporter="debug"} 6
```

**Konkretes Format-Detail**, das den Bug versteckt hat: der
Debug-Exporter im Collector schreibt Span-Bloecke mit indented
key-value-Padding:

```
Span #0
    Trace ID       : ...
    Parent ID      :
    ID             : ...
    Name           : tick.cycle
    Kind           : Internal
```

— 4 Leerzeichen Leading vor `Name`, danach Spaces zum
Doppelpunkt. Mein urspruengliches Regex `^Name\\s*:` (Anker direkt
am Zeilenanfang) hat das nie matchen koennen. Korrektur:
`^\\s*Name\\s*:`. Im selben Pattern hatten Metric und Log
funktioniert (`^\\s*->\\s*Name:` mit Leading-`\\s*` bzw. Log-`Body`
ohne Padding-Indent), weshalb die Asymmetrie zwischen den drei
Signal-Typen entstand.

**Diagnose-Mehrwert (Erbschaft):**

- `tools/diagnose_otlp_span_export.py` bleibt im Repo. Die
  Matrix-Diagnose plus Collector-Internal-Counter-Scrape ist ein
  brauchbares Pattern fuer kuenftige OTLP-Debugging-Faelle.
- `deploy/otel-collector-config.yaml` `service.telemetry.metrics.
  readers.pull.exporter.prometheus`-Block bleibt aktiv — die
  Internal-Counter sind eine echte Operations-Affordance, nicht
  nur ein Diagnose-Helfer.
- `deploy/compose.yml` `tmpfs '/var/log/otel:mode=1777'` bleibt
  — das war ein Bestands-Permission-Bug im distroless-Image, der
  nebenbei aufgefallen ist.
- `docs/user/observability.md` §4.4 Warnung zu `force_flush()`
  (laut Doku trivial wahr beim OTLPSpanExporter) bleibt — wir
  hatten das im Diagnose-Lauf direkt validiert.

---

<details>
<summary><strong>Historischer Kontext (vor Closure) — Doku-Befund 2026-05-25</strong></summary>

*Hat die Hypothesen-Liste umgeordnet, war aber selbst nicht der
Bruchpunkt. Closure-Befund §0 oben ist die endgueltige Erklaerung.
§1-§5 unten sind das urspruengliche Trigger-Dokument; Inhalte sind
durch §0 ueberholt (insbesondere §2 „Aktueller Workaround: Test
asserted nur Duo" — der Smoke pruft jetzt das volle Tripel).*

## 0b. Doku-Befund (2026-05-25, vor Closure)


Die ursprueng-formulierten Hypothesen (Endpoint-Format, Insecure-
Flag, Processor-Variante) haben wir gegen die offizielle Doku
gegengeprueft (siehe §7 Bezug). Ergebnis:

1. **Endpoint-Matrix ist Spec-konform.** OTLP/gRPC akzeptiert
   sowohl `http://host:4317` (impliziter Insecure-Default per
   URL-Schema) als auch `host:port` + `insecure=True`. Beides
   ist gueltig. Damit ist der Bruchpunkt **nicht** in der
   Endpoint-Konfiguration zu suchen.
2. **Collector-Config ist Standard.** `otlp.grpc` auf
   `0.0.0.0:4317` + separate `traces`/`metrics`/`logs`-Pipelines
   mit demselben Receiver ist genau das dokumentierte Modell.
3. **`force_flush() == True` ist KEIN Beweis fuer
   Netzwerk-Export.** Laut `opentelemetry-python`-Source puffert
   `OTLPSpanExporter` selbst nichts; `force_flush` returnt
   trivial `True`. Die echte Beweisfuehrung muss processor-side
   (SimpleSpanProcessor / BatchSpanProcessor exportiert) und
   receiver-side (`otelcol_receiver_accepted_spans`) laufen.
4. **Metrics+Logs ueber denselben Host/Port beweisen nur
   Transport-Erreichbarkeit**, nicht den Trace-Service-Pfad.
   OTLP/gRPC ist signal-spezifisch (`ExportTraceServiceRequest`
   vs. `ExportMetricsServiceRequest` vs.
   `ExportLogsServiceRequest`) — der Trace-Pfad kann eigenstaendig
   brechen.
5. **Naechste Diagnose-Schritte (Doku):** Collector-Internal-
   Metrics scrapen (`otelcol_receiver_accepted_spans`,
   `otelcol_receiver_refused_spans`,
   `otelcol_exporter_sent_spans`) plus SDK-side
   `span.context.trace_flags & 0x01` (SAMPLED-Bit) auswerten.
   Damit trennt man sauber: kommt am Receiver an /
   wird gedroppet / wird exportiert / wird vom Sampler verworfen.

**Konsequenz:** Hypothesen-Liste unten neu geordnet — Sampling/
Processor-Pfad nach oben, Endpoint-Varianten nach unten. Diagnose-
Tooling um Internal-Metrics + `trace_flags` erweitert
(`tools/diagnose_otlp_span_export.py`, 2026-05-25).

---

## 1. Befund

**Reproduzierbar** im Welle-6-C3-Setup
(Python 3.14 + `opentelemetry-sdk==1.42.1` +
`opentelemetry-exporter-otlp-proto-grpc==1.42.1` +
`otel/opentelemetry-collector-contrib:0.152.1`):

1. `OtlpTraceAdapter.start_span(...)` returnt einen `SpanContext`
   mit nicht-null `span_id` und `trace_id`. SDK-Side ist alles
   korrekt.
2. Ein parallel angehaengter `ConsoleSpanExporter` zeigt den Span
   strukturiert (`"name": "smoke.direct.v2"`, `"trace_id":
   "0x..."`, `"kind": "SpanKind.INTERNAL"`) — `is_recording()` ist
   `True`.
3. `tracer_provider.force_flush(timeout_millis=5000)` returnt
   `True` (Queue ist leer; SDK glaubt, dass exportiert wurde).
4. **Collector-Container empfaengt den Span nicht** — kein
   `ResourceSpans`-Block im stderr des `debug`-Exporters,
   weder mit `BatchSpanProcessor` noch mit `SimpleSpanProcessor`,
   weder mit `http://`-Endpoint noch mit `host:port` +
   `insecure=True`.
5. **Metrics und Logs ueber die identische gRPC-Verbindung an den
   gleichen Endpoint funktionieren** — `tick_count` (Sum) +
   `tick_begin`/`tick_end` (LogRecord) sind im Collector-Debug-
   Exporter sichtbar.
6. **Kein Error-Log** in stderr — die OTel-SDK schluckt Export-
   Fehler des Span-Exporters silent.

## 2. Aktueller Workaround (Welle 6 C3)

`tests/integration/test_otlp_compose_smoke.py` asserted **nur**
Metric + Log (Duo statt Tripel). Span-Pflicht aus ADR 0024 §4.5.7
ist im Test-Docstring + im Slice-Plan-DoD entsprechend
gekennzeichnet und auf dieses Open-Trigger verschoben.
`OtlpTraceAdapter` und `OtlpAdapterBundle` sind produktiv und
SDK-side verifiziert (Unit-Tests in
`tests/unit/adapters/driven/telemetry_otlp/`).

## 3. Diagnose-Tooling

`tools/diagnose_otlp_span_export.py` — Standalone-Script mit
Matrix-Varianten (Endpoint-Format x Insecure-Flag x Processor-
Variante) + voll aufgedrehtem `GRPC_VERBOSITY=DEBUG`,
`GRPC_TRACE=api,client_channel,connectivity_state,call_error` +
`opentelemetry`/`grpc`-Loggern auf DEBUG. Faehrt einen frischen
Collector-Sibling hoch (inkl. `service.telemetry.metrics.address:
0.0.0.0:8888`), sendet einen Span je Variante mit parallelem
`ConsoleSpanExporter`, dumpt am Ende drei Diagnose-Quellen:

1. **Collector-stderr** (debug-Exporter-Pretty-Output + interner
   `service.telemetry.logs.level: debug`).
2. **Per-Variante-Tracking** im SDK: pro Span werden
   `trace_flags`, `sampled` (SAMPLED-Bit), `recording`, `span_id`
   geloggt — damit faellt auf, wenn der SDK-Sampler den Span
   verwirft (kein OTLP-Export); siehe Doku-Befund Punkt 5.
3. **Collector-Internal-Counter** (Prometheus-Scrape von
   `:8888/metrics`): `otelcol_receiver_accepted_spans`,
   `otelcol_receiver_refused_spans`,
   `otelcol_processor_batch_batch_send_size`,
   `otelcol_exporter_sent_spans`,
   `otelcol_exporter_send_failed_spans` plus die analogen
   `accepted_metric_points`/`accepted_log_records` zum Vergleich.
   Erst diese Counter beweisen, ob ein Span am Receiver
   angenommen, gedroppet oder weiterexportiert wurde — Debug-
   Exporter-Logs allein zeigen das nicht (Doku-Befund Punkt 5).

Aufruf (Docker-only, kein lokaler Python-Pfad):

```bash
docker compose -f tests/integration/compose.yml run --rm test-runner \\
    uv run python tools/diagnose_otlp_span_export.py
```

Erwartete Diagnose-Interpretation:

- `accepted_spans=0`: Span erreicht den Collector **nicht** —
  Bruch liegt zwischen SDK-Exporter und Receiver-Endpoint
  (Netz/TLS/Service-Methode).
- `accepted_spans>0` und `sent_spans=0`: Span wird angenommen,
  aber nicht exportiert — Pipeline-/Processor-/Exporter-Bug
  collector-side.
- `accepted_spans>0` und `sent_spans>0` und Debug-Log zeigt
  nichts: Debug-Exporter-Filter / Verbosity-Problem (sollte
  bei `verbosity: detailed` nicht passieren).
- `sampled=False`: SDK-Sampler verwirft den Span vor Exporter-
  Aufruf — Sampler-Konfig pruefen.

## 4. Hypothesen-Liste (Triage-Reihenfolge, post-Doku-Befund)

1. **SDK-Sampler verwirft Span vor Export.** Default-Sampler ist
   `ParentBasedSampler(ALWAYS_ON)`, der bei Root-Spans
   `ALWAYS_ON` greift — aber Edge-Case-Konstellationen
   (z. B. nested Provider, vergessener `set_tracer_provider`-
   Call) koennten zu `NonRecordingSpan` fuehren. **Test:**
   `trace_flags & 0x01`-Print im Diagnose-Script auswerten
   (jetzt eingebaut).
2. **Processor exportiert Span nicht.** `BatchSpanProcessor` mit
   Background-Thread koennte beim ersten gRPC-Channel-Setup im
   Cross-Network-Sibling-Mode in einen unrecoverable State
   geraten; `SimpleSpanProcessor` ist synchron — wenn dort
   auch `accepted_spans=0`, ist es eindeutig **vor** dem
   Processor. **Test:** Internal-Counter pro Variante
   (Batch vs. Simple) vergleichen.
3. **gRPC-Trace-Service-Pfad bricht selektiv.** Logs+Metrics
   nutzen `ExportLogsServiceRequest`/`ExportMetricsServiceRequest`
   ueber die gleiche Connection, aber `ExportTraceServiceRequest`
   wird vom Receiver moeglicherweise schon vor Pipeline-Annahme
   abgelehnt (Schema-Inkonsistenz, Resource-Mismatch). **Test:**
   `otelcol_receiver_refused_spans` > 0 ist Beweis.
4. **OTel-Python-Trace-Exporter-Bug mit grpcio-Floor.** SDK 1.42
   + grpcio-Default-Floor koennten an einer Inkompatibilitaet
   leiden, die Metrics/Logs durch ihre Exporter umgehen.
   **Test:** Trace-Exporter-Source-Inspektion (`force_flush`-
   Implementierung; pruefen, ob er einen eigenen Channel-State
   teardown macht, den die anderen nicht tun).
5. **Endpoint-/Insecure-Varianten.** *Nach Doku-Befund Punkt 1
   unwahrscheinlich*; Spec-konform sind sowohl
   `http://host:4317` als auch `host:port` + `insecure=True`.
   Bleibt als Cross-Check im Diagnose-Script enthalten, ist
   aber nicht der Primaer-Verdacht.
6. **Python-3.14-SDK-Edge.** *Spekulativ*; ggf. Downgrade auf
   3.13 (`make ... PYTHON_VERSION=3.13`) als Vergleich, falls
   alle anderen Hypothesen widerlegt sind.

## 5. Akzeptanz

Trigger 029 wandert nach `done/`, sobald:

- `tools/diagnose_otlp_span_export.py` mindestens eine
  Variante gruen liefert (Collector-Hits >= 1).
- `tests/integration/test_otlp_compose_smoke.py` wieder die
  Span-Assertion (`tick.cycle`) addiert (Tripel statt Duo).
- Slice-Plan `M3-welle-6.md` §C3 / ADR 0024 §4.5.7 Caveat
  entfernt + DoD-Haken auf „Span-Sichtbarkeit verifiziert"
  gesetzt.

## 6. Aktivierungs-Kriterium

- **Spaetestens** vor M3-Welle-7-Closure (Span-Verifikation
  gehoert in den Observability-Abschluss).
- **Frueher**, wenn ein Production-OTLP-Span-Konsument
  (Jaeger-Adapter, Trace-UI etc.) das Span-Surface braucht.

## 7. Bezug

**Welle-6-interne Quellen:**

- M3 Welle 6 C3
  ([`docs/plan/planning/done/M3-welle-6.md`](M3-welle-6.md)
  §C3) — Caveat dokumentiert.
- ADR 0024 §4.5.7 — Compose-Smoke-Determinismus-Pattern, vier
  Pflichten; Span ist Teil des Tripels.
- [`tools/diagnose_otlp_span_export.py`](../../../../tools/diagnose_otlp_span_export.py)
  — Matrix-Diagnose-Script (Endpoint x Insecure x Processor,
  plus `trace_flags`-Print + Internal-Counter-Scrape).
- [`tests/integration/test_otlp_compose_smoke.py`](../../../../tests/integration/test_otlp_compose_smoke.py)
  — Smoke-Test mit Span-Caveat im Docstring.
- [`deploy/otel-collector-config.yaml`](../../../../deploy/otel-collector-config.yaml)
  — `service.telemetry.metrics.address: 0.0.0.0:8888` aktiv,
  damit Internal-Counter per Sibling-Container scrapbar sind.

**OTel-Doku-Quellen (Doku-Befund 2026-05-25):**

- [OTLP Exporter Configuration](https://opentelemetry.io/docs/specs/otel/protocol/exporter/)
  — Endpoint-/Insecure-Konvention (Doku-Befund Punkt 1).
- [Collector Configuration](https://opentelemetry.io/docs/collector/configuration/)
  — receiver/pipeline-Modell (Doku-Befund Punkt 2).
- [Python OTLPSpanExporter](https://opentelemetry-python.readthedocs.io/en/latest/_modules/opentelemetry/exporter/otlp/proto/grpc/trace_exporter.html)
  — `force_flush()` returnt trivial `True` (Doku-Befund Punkt 3).
- [OTLP Spec](https://opentelemetry.io/docs/specs/otlp/)
  — `ExportTraceServiceRequest` vs.
  `ExportMetricsServiceRequest` vs. `ExportLogsServiceRequest`
  als getrennte Service-Methoden (Doku-Befund Punkt 4).
- [Collector Internal Telemetry](https://opentelemetry.io/docs/collector/internal-telemetry/)
  — `otelcol_receiver_accepted_spans` etc. als verlaessliche
  Diagnose-Quelle (Doku-Befund Punkt 5).

</details>
