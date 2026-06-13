# Observability — Logs, Metrics, Traces

**Status:** Lebend ab M3-Welle-6-C3 (2026-05-25).
**Bezug:** [ADR 0024 §2.6](../plan/adr/0024-observability-port-trio.md),
[ADR 0027 §2.6](../plan/adr/0027-rule-based-agent-scenario-pattern.md),
M3-Welle-5 (Foundation, `Done` 2026-05-23) + M3-Welle-6 (OTLP-
Adapter + Compose-Smoke, `In Progress` 2026-05-25).

Welle 5 hat das `LogPort`/`MetricsPort`/`TracePort`-Trio plus
Null-Adapter eingefuehrt — Default-Verkabelung ist Null, kein
externer Side-Effect. Welle 6 liefert den produktiven OTLP-
Adapter (gRPC) plus einen Compose-Collector-Sibling in
[`deploy/compose.yml`](../../deploy/compose.yml).

Dieses Dokument beschreibt, **was** der Tick-Loop emittiert, **wie**
man den lokalen OTLP-Stack startet und **wie** man Diagnose-Pfade
geht, wenn Telemetrie verloren geht.

---

## 1. Was emittiert wird

### 1.1 Spans (`TracePort.start_span` / `.end_span` / `.record_event`)

Pro Tick-Iteration:

| Span-Name      | Quelle                                          | Attribute                                      | Parent       |
| -------------- | ----------------------------------------------- | ---------------------------------------------- | ------------ |
| `tick.cycle`   | `TickLoop.tick()`                               | `tick` (int), `run_id` (str)                   | —            |
| `fault.inject` | `_apply_fault_injection` (M3-Welle-2 Schritt A2) | `tick` (int)                                  | `tick.cycle` |
| `agent.tick`   | `_run_agent_tick_phase` (M3-Welle-3 Schritt D2) | `tick` (int), `agent_id` (str)                | `tick.cycle` |

Span-IDs sind **kein** Teil des Snapshot-Schemas ([`ADR 0024`](../plan/adr/0024-observability-port-trio.md) §2.5);
Trace-IDs sind cross-cutting und stehen nicht im Determinismus-
Vertrag. `OtlpTraceAdapter` zieht `trace_id`/`span_id` von der
OTel-SDK (`secrets.token_bytes`-default).

### 1.2 Metrics (`MetricsPort.increment` / `.gauge` / `.observe`)

| Metric-Name        | Typ     | Quelle                                  | Attribute   |
| ------------------ | ------- | --------------------------------------- | ----------- |
| `tick_count`       | Counter | `TickLoop.tick()` (NACH `_tick_count += 1`) | `run_id`    |
| `event_queue_len`  | Gauge   | `TickLoop.tick()` nach `scheduler.pop_due` | `run_id`    |

Counter (Sum, monotonic, cumulative) und Gauge sind die zwei
Welle-5-Default-Patterns. Histograms / `observe(...)` sind
Surface-bereit, aber heute nicht emittiert.

### 1.3 Logs (`LogPort.emit`)

Pro Tick-Iteration:

| Body          | Severity | Quelle                            | Attribute                                                    |
| ------------- | -------- | --------------------------------- | ------------------------------------------------------------ |
| `tick_begin`  | INFO     | `TickLoop.tick()` Body-Start      | `tick` (int), `event_id` (`tick-<N>`)                        |
| `tick_end`    | INFO     | `TickLoop.tick()` Body-Ende       | `tick` (int), `event_id` (`tick-<N>`), `emitted_count` (int) |

Per-Tick-Trail; `event_id` und `emitted_count` sind die zwei
Hauptdiagnose-Felder fuer Replay/Audit.

### 1.4 Welle-2 / Welle-3 Ergaenzungen

- Fault-Adapter (`BatteryFaultEngine`/`GridFaultEngine`) emittieren
  Audit-Logs beim Inject (Welle-2-Pfad).
- Agents (`RuleBasedAgent`) emittieren Decision-Trail-Logs ueber den
  AgentBus (Welle-3-Pfad).
- Beide sind ueber das gleiche `LogPort`/`TracePort` verdrahtet.

---

## 2. Lokaler OTLP-Stack starten

### 2.1 Quick-Boot via `make runtime`

```bash
make runtime
```

faehrt `deploy/compose.yml` hoch (postgres + api + simulation +
otel-collector), pollt API-`/health` und Collector-`:13133`, und
faehrt den Stack wieder runter. Default-Image ist
`otel/opentelemetry-collector-contrib:0.153.0` (pinning via
`OTEL_COLLECTOR_IMAGE`-Env oder Makefile-Default).

### 2.2 Stack laufen lassen + Output inspizieren

```bash
docker compose -f deploy/compose.yml up -d --wait
docker compose -f deploy/compose.yml logs -f otel-collector
```

Der `debug`-Exporter im Collector-Config
([`deploy/otel-collector-config.yaml`](../../deploy/otel-collector-config.yaml))
schreibt **alle** empfangenen Records strukturiert nach stderr —
pro Block: `ResourceSpans/Metrics/Logs` mit Resource-Attributes
(`service.name`, `service.instance.id`, ...) plus Inhalts-Felder
(Span-`Name`, Metric-`Name` + Value, Log-`Body`).

Der `file`-Exporter schreibt parallel nach
`/var/log/otel/otel-out.jsonl` (tmpfs im Produktiv-Profil).

### 2.3 Cleanup

```bash
docker compose -f deploy/compose.yml down -v --remove-orphans
```

`-v` ist Pflicht, damit das `postgres`-Volume + Collector-tmpfs
zwischen Lauefen nicht hangen bleibt.

### 2.4 Manueller Test gegen den lokalen Collector

```python
from grid_gym.adapters.driven.telemetry_otlp import (
    OtlpAdapterConfig, build_otlp_adapters,
)

config = OtlpAdapterConfig(
    endpoint="http://localhost:4317",  # Compose-Sibling-Port
    service_name="grid-gym-local",
    service_instance_id="manual-debug",
)
bundle = build_otlp_adapters(config)
# ... TickLoop bauen mit bundle.log_adapter/metrics_adapter/trace_adapter ...
bundle.flush_and_shutdown(timeout_millis=5000)
```

Endpoint **muss** mit `http://` (insecure gRPC) oder ohne Schema
plus `OTEL_EXPORTER_OTLP_INSECURE=true` Env-Var sein — Default-
TLS-Mode der OTel-SDK ist `https`/secure.

---

## 3. Konfigurations-Knobs (`OtlpAdapterConfig`)

Frozen Dataclass; alle Felder optional mit OTel-Standard-Env-Var-
Fallback:

| Feld                    | Default                          | Env-Var                            |
| ----------------------- | -------------------------------- | ---------------------------------- |
| `endpoint`              | `http://localhost:4317`          | `OTEL_EXPORTER_OTLP_ENDPOINT`      |
| `headers`               | `{}`                             | `OTEL_EXPORTER_OTLP_HEADERS`       |
| `timeout_s`             | `10.0`                           | `OTEL_EXPORTER_OTLP_TIMEOUT` (ms)  |
| `batch_max_export_size` | `512`                            | —                                  |
| `service_name`          | `grid-gym`                       | `OTEL_SERVICE_NAME`                |
| `service_instance_id`   | `None`                           | aus `OTEL_RESOURCE_ATTRIBUTES`     |
| `protocol`              | `grpc` (validiert: `{"grpc"}`)   | `OTEL_EXPORTER_OTLP_PROTOCOL`      |

Validierung in `__post_init__` (siehe
[`src/grid_gym/adapters/driven/telemetry_otlp/_config.py`](../../src/grid_gym/adapters/driven/telemetry_otlp/_config.py)).
HTTP/protobuf ist explizit Out-of-Scope (Welle-6-Pin, [`ADR 0024`](../plan/adr/0024-observability-port-trio.md)
§4.5.6); fuer eine spaetere HTTP-Aktivierung braucht es eine
ADR-Folge + Allow-List-Erweiterung.

---

## 4. Failure-Modes + Diagnose

### 4.1 Collector down / Endpoint unerreichbar

**Symptom:** Adapter wirft **keine** Exception in den Tick-Loop —
OTLP-Exporter buffern intern und verwerfen Batches nach Retry-
Timeout. Kein Re-Raise (Adapter-Vertrag: Side-Effect-Loss > Tick-
Crash).

**Diagnose:** Container-Logs via
`docker compose logs api` und
`docker compose logs otel-collector` parallel ansehen. Wenn der
Collector schweigt aber API gesund weiterlaeuft, ist die Connection
broken; der OTel-SDK loggt Export-Fehler **nicht** auf stderr
(silent failure). Workaround zur Diagnose:
`logging.getLogger("opentelemetry").setLevel(logging.DEBUG)` plus
`GRPC_VERBOSITY=DEBUG`/`GRPC_TRACE=...`-Env-Vars.

### 4.2 Export-Timeout / Backpressure

**Symptom:** `BatchSpanProcessor.force_flush(timeout_millis=...)`
returnt `False`, sobald die Queue voller wird als der Export
ausspuelt.

**Workaround:** `batch_max_export_size` in `OtlpAdapterConfig`
hochsetzen oder Collector mit groesseren Receiver-Queues betreiben.
Default `512` reicht fuer Welle-6-Demo-Lasten (5-100 Ticks/s).

### 4.3 Spans, Metrics, Logs im Collector verifizieren

**Primaer-Quelle:** Der `debug`-Exporter im Collector schreibt
alle empfangenen Records strukturiert nach stderr; das ist die
schnellste Sicht.

**Achtung — Output-Padding-Format unterscheidet sich pro Signal-
Typ.** Aus dem Trigger-029-Closure-Befund (2026-05-25): Span-
Bloecke kommen mit Leading-Whitespace-Padding, Metric/Log nicht:

```
Span #0
    Trace ID       : ...
    Name           : tick.cycle              # 4 Leerzeichen vor `Name`!
    Kind           : Internal
...
Metric #0
Descriptor:
     -> Name: tick_count                     # `-> Name:` mit Leading-Space
...
LogRecord #0
Body: Str(tick_begin)                        # ohne Leading-Whitespace
```

Wenn du gegen den Output greppst/regex-matchst, **immer
`\s*`-Prefix** im Pattern. Beispiel-Regex in
[`tests/integration/test_otlp_compose_smoke.py`](../../tests/integration/test_otlp_compose_smoke.py):

```python
_RE_SPAN_NAME = re.compile(r"^\s*Name\s*:\s*(\S+)\s*$", re.MULTILINE)
_RE_METRIC_NAME = re.compile(r"^\s*->\s*Name:\s*(\S+)\s*$", re.MULTILINE)
_RE_LOG_BODY = re.compile(r"^Body:\s*Str\((\S+)\)\s*$", re.MULTILINE)
```

**Achtung — was NICHT als Diagnose taugt:**

- `force_flush() == True` allein. Laut OTLPSpanExporter-Python-
  API puffert der Exporter selbst nichts; `force_flush` returnt
  trivial `True`. Erst der Receiver-Counter im Collector beweist
  einen Annahme-Erfolg.
- Debug-Exporter-Logs allein, wenn vorgelagerte Drop-Stellen
  (Receiver-Refused / Processor-Filter) eine Rolle spielen
  koennen.

**Sekundaer-Quelle (Operations/Diagnose): Collector-Internal-
Telemetry.** Der Collector exponiert Prometheus-Counter auf
`:8888/metrics`
(`service.telemetry.metrics.readers.pull.exporter.prometheus` in
[`deploy/otel-collector-config.yaml`](../../deploy/otel-collector-config.yaml)):

| Counter                              | Bedeutung                                    |
| ------------------------------------ | -------------------------------------------- |
| `otelcol_receiver_accepted_spans`    | Receiver hat den Span angenommen             |
| `otelcol_receiver_refused_spans`     | Receiver hat den Span aktiv abgelehnt        |
| `otelcol_processor_batch_batch_send_size` | Batches, die der Processor weiterreicht |
| `otelcol_exporter_sent_spans`        | Exporter hat den Span erfolgreich verschickt |
| `otelcol_exporter_send_failed_spans` | Exporter hat einen Send-Failure              |

Diff-Interpretation: `accepted_spans=0` → Bruch **vor** dem
Receiver (Netz, TLS, Service-Methode); `accepted_spans>0` und
`sent_spans=0` → Bruch in Pipeline/Processor/Exporter.

**SDK-side Diagnose:**

`span.get_span_context().trace_flags & 0x01` (SAMPLED-Bit). Ist
das Bit 0, hat der SDK-Sampler den Span verworfen — kein OTLP-
Export findet statt.

**Diagnose-Tooling:**
[`tools/diagnose_otlp_span_export.py`](../../tools/diagnose_otlp_span_export.py)
— Matrix-Script mit Endpoint/Insecure/Processor-Varianten plus
Produktiv-Pfad-Variante (`build_otlp_adapters` + `OtlpAdapterBundle`),
voll aufgedrehte gRPC- + OTel-Debug-Logger; druckt pro Variante
`trace_flags` + `sampled` + `recording` und scraped am Ende die
Internal-Counter von `:8888/metrics`. Aufruf (Docker-only):

```bash
docker compose -f tests/integration/compose.yml run --rm test-runner \
    uv run python tools/diagnose_otlp_span_export.py
```

Historischer Kontext zur Tooling-Erbschaft: Trigger 029
([`done/029-otlp-span-grpc-export-edge-case.md`](../plan/planning/done-archive/029-otlp-span-grpc-export-edge-case.md))
wurde als Fehlbefund geschlossen — der vermutete OTLP-gRPC-Span-
Export-Bug existierte nicht, der Smoke-Test hatte schlicht das
`Name           : tick.cycle`-Padding-Format nicht im Span-Regex
erlaubt.

### 4.4 `force_flush()` returnt `True` aber Records fehlen

**Vorsicht-Pattern**: bei OTel-SDK signalisiert `force_flush=True`
„Queue ist leer", nicht „Records sind im Collector angekommen".
Insbesondere bei `OTLPSpanExporter` (Python-API): der Exporter
puffert selbst nichts, `force_flush` returnt trivial `True` — auch
wenn der Background-Send via gRPC fehlschlaegt. Export-Failures
werden aus der Queue entfernt, ohne dass `force_flush` `False`
meldet.

**Verifikation immer ueber das Empfaenger-seitige Ziel**
(Collector-Internal-Counter `otelcol_receiver_accepted_spans` /
`otelcol_exporter_sent_spans`, File-Sink, Backend-API), nicht
nur ueber SDK-Side-Returncodes. Siehe §4.3 fuer den Internal-
Telemetry-Endpunkt und das Diagnose-Tooling.

---

## 5. Bezug

- [ADR 0024 — Observability-Port-Trio](../plan/adr/0024-observability-port-trio.md)
- [ADR 0027 — RuleBasedAgent + Scenario-Pattern](../plan/adr/0027-rule-based-agent-scenario-pattern.md)
- [M3-Welle-6 Slice-Plan](../plan/planning/done-archive/M3-welle-6.md)
- [Trigger 029 — OTLP-Span-gRPC-Export-Edge-Case (Done: Fehlbefund)](../plan/planning/done-archive/029-otlp-span-grpc-export-edge-case.md)
- [`deploy/compose.yml`](../../deploy/compose.yml)
- [`deploy/otel-collector-config.yaml`](../../deploy/otel-collector-config.yaml)
- [`tools/wait_otel_collector.py`](../../tools/wait_otel_collector.py)
- [`tools/diagnose_otlp_span_export.py`](../../tools/diagnose_otlp_span_export.py)
