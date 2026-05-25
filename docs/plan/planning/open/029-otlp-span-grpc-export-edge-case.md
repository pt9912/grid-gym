# 029 — OTLP-Span-gRPC-Export-Edge-Case (Welle 6 C3 Caveat)

**Status:** Open — eroeffnet 2026-05-25 als Welle-6-C3-Caveat.
**Quelle:** M3-Welle-6-C3-Smoke-Test
(`tests/integration/test_otlp_compose_smoke.py`); Befund waehrend
des Tripel-Assert-Bauversuchs (Span/Metric/Log).
**Ziel:** OTLP-gRPC-Span-Export Sibling-Container reproduzierbar
gruen bekommen — damit der Welle-6-Smoke spaeter auf das volle
Tripel (Span/Metric/Log) hochgezogen werden kann, das ADR 0024
§4.5.7 und M3-welle-6.md §C3 urspruenglich vorsehen.

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
Matrix-Varianten (Endpoint-Format × Insecure-Flag × Processor-
Variante) + voll aufgedrehtem `GRPC_VERBOSITY=DEBUG`,
`GRPC_TRACE=api,client_channel,connectivity_state,call_error` +
`opentelemetry`/`grpc`-Loggern auf DEBUG. Faehrt einen frischen
Collector-Sibling hoch, sendet einen Span je Variante mit
parallelem `ConsoleSpanExporter`, dumpt am Ende den vollen
Collector-stderr und eine `variant → collector_hits`-Matrix.

Aufruf (Docker-only, kein lokaler Python-Pfad):

```bash
docker compose -f tests/integration/compose.yml run --rm test-runner \\
    uv run python tools/diagnose_otlp_span_export.py
```

## 4. Hypothesen-Liste (Triage-Reihenfolge)

1. **gRPC-Channel-State-Race** im Cross-Network-Sibling-Setup —
   die Span-Connection wird vor dem Send teardown, weil `force_
   flush` die Queue als leer erkennt obwohl der Export-Call noch
   in-flight ist. Test: `BatchSpanProcessor` mit langem
   `schedule_delay_millis` + Beobachten, ob Spans nach
   ~5 s ankommen.
2. **OTel-SDK-`OTLPSpanExporter`-Bug mit Python 3.14** — neueste
   Python-Version + neueste SDK koennten an einer 3.13/3.14-
   Inkompatibilitaet leiden. Test: Downgrade auf Python 3.13 via
   `make ... PYTHON_VERSION=3.13` (verfuegbar laut ADR 0002 §6.1).
3. **Collector-Receiver dropped Spans silent** wegen Schema-/
   Resource-Inkonsistenz, die Metrics/Logs nicht haben. Test:
   `service.telemetry.logs.level: debug` im Collector
   (im `diagnose`-Script schon gesetzt) — Receiver-Logs sollten
   dann zeigen, dass etwas reinkommt und gedroppet wird.
4. **`grpcio`-Floor zu niedrig** — `pyproject.toml` haerten auf
   ein neueres `grpcio`-Minimum, falls Bekannte Bugs in der
   gepinnten Version dokumentiert sind.
5. **Header-/Resource-Diff zwischen Trace- und Metric-/Log-
   Exporter im Factory-Pfad** — `_factory.py` baut alle drei
   gleich, aber moeglich uebersehene Asymmetrie. Test:
   `OTLPSpanExporter`-Konstruktor mit explizit denselben Args
   wie `OTLPMetricExporter` (modulo Klasse).

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

- M3 Welle 6 C3 (`docs/plan/planning/in-progress/M3-welle-6.md`
  §C3) — Caveat dokumentiert.
- ADR 0024 §4.5.7 — Compose-Smoke-Determinismus-Pattern, vier
  Pflichten; Span ist Teil des Tripels.
- `tools/diagnose_otlp_span_export.py` — Matrix-Diagnose-Script.
- `tests/integration/test_otlp_compose_smoke.py` — Smoke-Test
  mit Span-Caveat im Docstring.
