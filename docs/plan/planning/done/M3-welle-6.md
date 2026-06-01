# Welle 6 — OTLP-Adapter (telemetry-otlp, gRPC)

**Status:** Done — geschlossen 2026-05-25 nach C3-Hauptcommit
`47a46b0` + dieser DoD-Sync-/Closure-Folge. M3-Welle 5
(Observability-Foundation) ist abgeschlossen
(`7427daf..a690c02` + End-of-Wave-Folge `4d95df7`); Welle 6 liefert
den **produktiven Export-Pfad** des Observability-Sub-Bereichs und
verbindet das Port-Trio aus Welle 5 mit einem OTLP-Collector-Sibling
in `deploy/compose.yml`. Damit schliesst Welle 6 den Observability-
Sub-Bereich der M3-Triade (Faults `Done` 2026-05-20, Multi-Agent
`Done` 2026-05-22, Observability **Foundation `Done` 2026-05-23,
OTLP-Adapter `Done` 2026-05-25**) ab; Welle 7 ist Closure.

**Closure-Stand 2026-05-25:** C0 done, C1 done (alle drei Sub-
Commits `8eba9ff`/`c99680c`/`54657dc` plus drei Review-Folgen
`3f887b5`/`c19c69d`/`5493831` — siehe Sub-Commit-Tabelle unter
C1), C2 done (`c61ab0d`), C3 done (`47a46b0`): Integration-Smoke
`tests/integration/test_otlp_compose_smoke.py` (Tripel
Span+Metric+Log — Trigger 029 ist als Fehlbefund geschlossen
[Span-Regex-Bug im Smoke-Test selbst, nicht im OTLP-Pfad];
siehe [`../done/029-otlp-span-grpc-export-edge-case.md`](../done/029-otlp-span-grpc-export-edge-case.md)
§0 Closure-Befund), Runbook `docs/user/observability.md`, README/
README.de-Closure-Zeilen, DoD-Haken in diesem Dokument.

**DoD-Checkliste (Welle-6-Abnahme):**

Konvention analog Roadmap §3 M3 — `[ ]` offen, `[x]` erfuellt,
`[~]` partiell. Status beim C0-Stand `In Progress`: alle Items
offen; Haken wandern mit C1/C2/C3-Beleg.

- [x] **`make fullbuild` cache-frei gruen ohne Override, mit
      OTLP-Collector-Sibling** im Compose-Smoke (volle CI +
      Runtime-Image + Compose-Smoke + Trivy-Image-Audit). Welle-6-
      Abnahme-Kriterium aus M3-Slice-Plan §3 Welle 6 + §2
      Erfolgskriterium 5. **Erfuellt mit C2 `c61ab0d`** (`make
      runtime` + `make image-audit` gruen mit Collector-Sibling)
      und C3-Verifikation in `47a46b0`.
- [x] **`make test-unit` gruen** mit Welle-6-Adapter-Tests
      (`OtlpLogAdapter` / `OtlpMetricsAdapter` / `OtlpTraceAdapter`
      Surface + Export-Roundtrip gegen In-Process-`grpcio`-Mock).
      **Erfuellt mit C1.3b `c99680c`**.
- [x] **`make test-integration` gruen** — Welle-6-Smoke fuegt
      mindestens einen Test hinzu, der gegen den `otel-collector`-
      Sibling pruft, dass **≥ 1 Span (`tick.cycle`) + ≥ 1 Metric
      (`tick_count`) + ≥ 1 Log (`tick_begin`/`tick_end`)
      exportiert** wurden. Sink-Determinismus erfuellt: per-Lauf
      eindeutige `service.instance.id` (uuid4) filtert alle
      Assertions; Sink ist `container.logs()` des Debug-Exporters
      statt File-Sink (testcontainers' `get_archive` lieferte aus
      tmpfs keine Daten zurueck — drei Iterationen siehe Test-
      Docstring). SDK-Side `OtlpAdapterBundle.flush_and_shutdown()`,
      Collector-Side 5s-Bounded-Poll. **Erfuellt mit C3 `47a46b0`**
      (zunaechst Duo wegen Span-Regex-Bug, danach Tripel via
      Trigger-029-Closure
      [`../done/029-otlp-span-grpc-export-edge-case.md`](../done/029-otlp-span-grpc-export-edge-case.md)).
- [x] **`make gates` A-1 gruen ohne Override** — lint, format-check,
      mypy `--strict`, arch-check (19 contracts), coverage 90/85 line,
      critical-coverage, dep-audit (`grpcio` +
      `opentelemetry-exporter-otlp-proto-grpc` aufgenommen).
      **Erfuellt mit C3 `47a46b0`**; verified im
      Gates-Run pre-Commit.
- [x] **Default-`CRITICAL_COV_TARGETS` um
      `src/grid_gym/adapters/driven/telemetry_otlp` erweitert**
      (DoD-Item aus Roadmap §3 M3 + M3-Slice-Plan §3 Welle 6).
      **Erfuellt mit C1.3c `54657dc`**. Pfadkonvention:
      das `ARG CRITICAL_COV_TARGETS`-Default in `Dockerfile:245`
      listet ausschliesslich filesystem-Pfade mit vollem
      `src/grid_gym/`-Prefix und Python-Underscore-Form
      (z. B. `src/grid_gym/hexagon/core/grid_connection`,
      `src/grid_gym/hexagon/core/smart_meter`). Der Architektur-
      Slug `telemetry-otlp` (Dash, Spec §5 Z. 314 `telemetry-*`)
      ist prosaisches Pendant, **nicht** Coverage-Target-Form.
- [x] **ADR-0024-Schaerfung** der §4.4-Forward-Pointer per ADR 0011-
      Pattern (Counter-/Gauge-Naming, `_obs_observe`-Helper,
      Trace-ID-Determinismus, `SpanContext`-Felder, Sentinel-
      Pattern fuer `scenario.observability`) + `Letzte inhaltliche
      Aenderung`-Pflichtfeld (ADR 0006 §4). **Erfuellt mit C1.2
      `fa0b11b`** (ADR 0024 §4.5 mit 8 Decisions; `make docs-check`
      exit 0).
- [ ] **ADR 0024 bleibt `Provisional`** bis M3-Welle-7-Closure;
      Promotion auf `Accepted` ist M3-Welle-7-Material.
- [x] **ADR-Folge-Entscheidung** fuer Compose-Smoke-Verifikations-
      Pattern (Sibling-Container + Export-Sink-Assertion): eigener
      ADR `Provisional` **oder** Schaerfung-ohne-Supersede in
      ADR 0024 — Decision dokumentiert. **Erfuellt mit C1.2
      `fa0b11b`** — Wahl: Schaerfung-ohne-Supersede in ADR 0024
      §4.5.7 (Compose-Smoke-Determinismus-Pattern mit vier
      Determinismus-Pflichten); kein separater ADR-Eintrag.
- [ ] **Trigger 006 (`--strict-bytes`) Entscheidung** am konkreten
      OTLP-Bytes-Vertrag (aktivieren oder konkrete Begruendung
      fuer Verschiebung in M4/M6-Re-Triage). Wandert nach M3-
      Welle-7-Closure oder spaeter.
- [x] **`AC-PORTS-NO-OUT` bleibt KEPT** — 3 neue Driven-Adapter
      unter `src/grid_gym/adapters/driven/telemetry_otlp/`,
      keine Driving-Port-Verletzer. **Verified mit C1**.
- [x] **`AC-NO-TIME` bleibt KEPT** — `tick_duration_ms` weiterhin
      **nicht** aus TickLoop emittiert; Adapter-Code importiert
      kein `time` (D-4 in C0 festgezogen); einzige Wall-Clock-
      Quellen liegen eine Schicht tiefer in der externen
      OTel-SDK (Span-Lifecycle setzt `StartTime`/`EndTime`,
      Batch-Processoren exportieren). **Verified per Welle-6-
      C1-Review-Folge-H-2** mit dem 12. arch_check-Contract
      `AC-OTLP-ADAPTER-NO-TIME` (`3f887b5`).
- [x] **`AC-NO-COVERAGE-PRAGMA` (ADR 0029) bleibt KEPT** — keine
      `# pragma: no cover`/`no branch`/`exclude file` in den
      neuen Adapter-Modulen. **Verified mit C1**.
- [x] **Runbook `docs/user/observability.md`** vorhanden (welche
      Spans/Metrics/Logs emittiert werden, lokaler Stack-Boot,
      Failure-Modes + Diagnose-Pfad). **Erfuellt mit C3-
      Closure-Commit** (Folge dieses DoD-Sync).
- [x] **`README.md` + `README.de.md` Welle-6-Closure-Zeile**
      ergaenzt (beide Sprach-Varianten halten den gleichen
      Status-Block). **Erfuellt mit C3-Closure-Commit** (Folge
      dieses DoD-Sync).
- [ ] **M3-welle-6.md → `done/`** via Wave-Self-Close-Commit-
      Konvention; relative Link- und Bezug-Pfade-Pflege im
      Folge-Commit (ADR 0028). Naechster Commit nach diesem
      DoD-Sync.

Kanonische Slice-Spezifikation:
[`M3-faults-agents-observability.md §3 Welle 6`](M3-faults-agents-observability.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht als Ersatz.

**Commit-Sequenz (geplant):**

### C0 — `docs(plan)`: welle-6 Slice-Doc (dieses Dokument)

Eroeffnet Welle 6 mit Scope (gRPC-Transport-Entscheidung),
Interfaces (Welle-5-Ports unveraendert konsumiert), Config
(OTLP-Endpoint, Headers, Batch-/Timeout-Parameter), Failure
Modes (Collector down, Export-Timeout, Backpressure) und
Akzeptanzkriterien (≥ 1 Span + ≥ 1 Metric exportiert im Compose-
Smoke). Plus `in-progress/README.md`-Sync (M3-welle-6.md-Eintrag
im Bestand) und Slice-Plan-Status-Text-Sync.

Per Wave-Self-Close-Commit-Konvention
([`planning/README.md`](../README.md)) **kein Pre-C0-Move** mehr —
welle-5.md hat sich mit `b9bd8c7` + `4d95df7` selbst geschlossen.

### C1 — telemetry-otlp-Adapter + ADR-0024-Schaerfung (5 Sub-Commits)

C1 ist die produktivste Welle-6-Phase und wurde nach C0-Schliff
in fuenf Sub-Commits aufgeteilt, damit jeder Schritt unabhaengig
verifizierbar bleibt und Code-Review-Last sich gleichmaessig
verteilt:

| Sub-Commit | Gegenstand | Status |
| ---------- | ---------- | ------ |
| **C1.1** | OpenTelemetry-Dependencies + Import-Linter-Erweiterung (`AC-NO-FW`/`AC-PORTS-NO-FW` um `opentelemetry`+`grpc`) | **Done** — `c98ce1a` (2026-05-24); `make arch-check` 7/7 KEPT |
| Floor-Refresh | Bestehende Library-Floors (`fastapi`/`uvicorn`/`pydantic`/`psycopg`/`alembic`) auf aktuellen PyPI-Stand | **Done** — `69dd3d1` (2026-05-24); resolved-Versionen unveraendert, nur `requires-dist`-Metadata |
| **C1.2** | ADR-0024-Schaerfung §4.5 mit 8 Decisions (L-2/N-1/N-2/Sentinel/Trace-ID + D-4-Uebernahme + gRPC-Pinning + Smoke-Determinismus-Pattern) | **Done** — `fa0b11b` (2026-05-24); `make docs-check` exit 0 |
| **C1.3a** | `OtlpAdapterConfig` (`_config.py` frozen-dataclass mit Allow-List-Validation `{"grpc"}`) + Unit-Tests fuer Konfig-Surface, Defaults, Env-Var-Fallback, Validation-Errors | **Done** — `8eba9ff` (2026-05-24) |
| **C1.3b** | Drei OTLP-Adapter (`logs.py`/`metrics.py`/`traces.py`) implementieren `LogPort`/`MetricsPort`/`TracePort` mit `| None`-Robustheit (§4.5.1) und ohne `time.*`-Import (§4.5.5); Unit-Tests gegen In-Process-`grpcio`-Mock fuer Surface + Roundtrip + Failure-Modes | **Done** — `c99680c` (2026-05-24) |
| **C1.3c** | `build_otlp_adapters(config)`-Factory + `flush_and_shutdown()`-Helper (§4.5.7 Punkt 4); `__init__.py` Re-Exports; `Dockerfile`-`CRITICAL_COV_TARGETS` um `src/grid_gym/adapters/driven/telemetry_otlp` erweitert; Final-`make gates`-Verifikation | **Done** — `54657dc` (2026-05-24) |
| **C1-Review-Folge H** | High-Findings H-1/H-2/H-3 inkl. `NullTraceAdapter` (`AC-OTLP-ADAPTER-NO-TIME` als neuer 12. arch_check-Contract via H-2; per Slice 028 inzwischen 13 arch_check-Contracts insgesamt) | **Done** — `3f887b5` (2026-05-24) |
| **C1-Review-Folge M** | Medium-Findings M-1..M-6 | **Done** — `c19c69d` (2026-05-24) |
| **C1-Review-Folge L** | Low-Findings L-1/L-2/L-4 | **Done** — `5493831` (2026-05-24) |

Produktive Lieferung (Spec-Detail; verteilt ueber C1.3a/b/c):

- 3 OTLP-Adapter (gRPC-Transport) in
  `src/grid_gym/adapters/driven/telemetry_otlp/` (Modulname
  `telemetry_otlp` — Python-`-`/`_`-Konvention; Compose-Service
  bleibt `otel-collector`):
  - `OtlpLogAdapter` — implementiert `LogPort`-Protocol, mappt
    `level/message/attributes` auf
    `opentelemetry-exporter-otlp-proto-grpc`-`LogRecord`.
  - `OtlpMetricsAdapter` — implementiert `MetricsPort`-Protocol,
    `increment`/`gauge`/`observe`-Surface auf
    `Counter`/`UpDownCounter`/`Histogram` der OTel-Metrics-SDK.
  - `OtlpTraceAdapter` — implementiert `TracePort`-Protocol;
    `start_span`/`end_span`/`record_event`-Surface auf OTel-
    Tracer + `BatchSpanProcessor` + `OTLPSpanExporter`. Die
    Start-/End-Zeitpunkte werden vom OTel-Span/SDK selbst
    gesetzt (Span-Lifecycle: `tracer.start_span(...)` setzt
    `StartTime`, `span.end()` setzt `EndTime`); der
    `BatchSpanProcessor` ist nur das Export-Vehikel und
    misst nicht. Der Adapter ruft **kein** `time.*` selbst
    auf (D-4 unten in C0 festgezogen). `AC-NO-TIME` bleibt
    damit auch im Adapter-Code KEPT — Wall-Clock-Affordance
    liegt erst eine Schicht tiefer in der externen SDK.
- Konfigurations-Helper (`OtlpAdapterConfig`-frozen-dataclass):
  `endpoint`, `headers`, `timeout_s`, `batch_max_export_size`,
  `service_name`, `service_instance_id`. Default-Quelle:
  `OTEL_*`-Env-Vars (Standard-Konvention OTel-SDK); explizite
  Kwargs ueberschreiben.
- `build_tick_loop(..., log_port=, metrics_port=, trace_port=)`-
  Symmetrie bleibt aus Welle 5; Welle 6 fuegt
  `build_otlp_adapters(config)`-Factory in
  `adapters/driven/telemetry_otlp/__init__.py` hinzu.
- Unit-Tests gegen In-Process-`grpcio`-Mock (kein Live-Collector
  noetig): Surface-Validierung, Roundtrip-Assertions auf
  Exporter-Calls, Konfig-Defaults, Failure-Mode-Handling
  (Collector-down → Adapter loggt + verwirft Batches; kein
  Re-Raise in Tick-Loop-Pfad).
- `tools/arch_check.py`: pruefen, ob neuer Contract
  `AC-OBS-ADAPTER-NO-CORE-IMPORT` sinnvoll ist (Adapter darf
  Ports importieren, kein Core-Modul). Decision in C1-Triage.
- ADR-0024-Schaerfung (per ADR 0011 + ADR 0006 §4 — `Letzte
  inhaltliche Aenderung`-Pflichtfeld) fuer die in Welle-5-§4.4
  dokumentierten Welle-6-Forward-Pointer:
  - L-2: `NullTraceAdapter.end_span/record_event`-Signatur-
    Asymmetrie → Protocol-Erweiterung **oder** Adapter-
    spezifische `| None`-Signatur (Decision in C1).
  - N-1: `tick_count`-Counter vs. `tick_index`-Gauge-Naming —
    Welle 6 fixiert die Konvention (Counter monoton steigend,
    Gauge fuer State-Snapshot).
  - N-2: `_obs_observe`-Helper symmetrisch ergaenzen — Welle 6
    entscheidet (Pro: Helper-Symmetrie zu `_obs_increment` /
    `_obs_gauge`; Contra: Wall-Clock-Affordance laeuft am
    `AC-NO-TIME`-Geist vorbei). Default-Vorschlag: **nein**,
    weil die OTel-SDK die Span-Dauer ueber
    `StartTime`/`EndTime` im `BatchSpanProcessor` ohnehin
    liefert (D-4 oben). Der Adapter ruft selbst kein `time.*`
    auf; „intern" bedeutet ausdruecklich **nicht** manuelle
    Zeitmessung im Adapter-Code, sondern Delegation an die
    SDK eine Schicht tiefer.
  - §4.4 Sentinel-Pattern fuer `scenario.observability`-Block:
    bewusst aufgeschoben auf M3-Welle-7 oder Folge-Slice;
    Welle 6 nutzt `build_otlp_adapters(config=...)`-Factory
    statt Scenario-Schema-Eintrag.
  - §4.4 Trace-ID-Determinismus: per Default OTel-Standard
    (random 16-byte). Welle 6 dokumentiert, dass Determinismus-
    Property-Tests sich auf `RandomPort.sub_port`-basierte
    `SpanContext`-Erzeugung **nicht** stuetzen (OTLP-IDs sind
    bewusst zufaellig). Snapshot-Determinismus bleibt
    unangetastet, da `SpanContext` nicht in Snapshots eingeht
    (ADR 0024 §2.5).
- Trigger 006 (`--strict-bytes`) Entscheidung am OTLP-Protobuf-
  Bytes-Pfad: in Welle 6 aktivieren, falls OTel-SDK-Typstubs
  einen sauberen Bytes-Vertrag tragen; sonst Trigger 006 mit
  konkreter Begruendung weiter offen (M4/M6-Trigger-Re-Triage).

### C2 — `feat(welle-6)`: deploy/compose.yml OTLP-Collector-Sibling

- Neuer Service `otel-collector` in `deploy/compose.yml` (sowie
  `tests/integration/compose.yml`, falls Integration-Smoke
  separat laeuft):
  - Image: `otel/opentelemetry-collector-contrib:<gepinnte-tag>`
    (Pin-Strategie gemaess ADR 0019 Image-Pinning-Pattern).
  - Konfig-Volume `deploy/otel-collector-config.yaml` mit
    `otlp`-Receiver (gRPC :4317) + `file`-Exporter (Pfad per
    Env-Var `OTEL_COLLECTOR_FILE_SINK` parametrisiert, Default
    `/tmp/otel-out.jsonl` fuer lokalen Boot) + `logging`-
    Exporter fuer Smoke-Inspection. Smoke-Fixture in C3
    setzt `OTEL_COLLECTOR_FILE_SINK` auf einen per-Lauf
    eindeutigen Pfad (z. B. `pytest`-`tmp_path` + Compose-
    Volume-Mount), damit konkurrierende Lauefe keinen
    gemeinsamen Sink teilen.
  - **`batch`-Processor mit kurzer Timeout-Konfiguration**
    (z. B. `timeout: 100ms`, `send_batch_size: 1`) im
    Smoke-Pfad, damit Collector-Side-Batching die Sink-
    Sichtbarkeit nicht verzoegert. Produktiv-Profile (M3-
    Welle-7-Folge oder M4-Slice) duerfen groessere Werte
    fahren; Welle-6-Smoke verwendet die kurze Config.
  - Healthcheck per `otelcol --check-config` oder
    `wget`-Probe auf Health-Extension-Port.
- API-/Sim-Container bekommen per Compose-`environment`-Block
  (Default-Werte gemaess `OtlpAdapterConfig`):
  - `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317`
    (Sibling-Hostname + gRPC-Port).
  - `OTEL_EXPORTER_OTLP_PROTOCOL=grpc` — explizit gepinnt,
    damit ein SDK-Default-Wechsel oder ein Env-Override im
    Deploy-Stack den Export-Pfad nicht still auf
    `http/protobuf` umlenkt (Welle-6-Annahme: Transport
    bleibt deterministisch gRPC). C1-`OtlpAdapterConfig`
    validiert den Wert auf `{"grpc"}`; HTTP/protobuf ist
    explizit Out-of-Scope (siehe §2) und wuerde eine
    Konfig-Erweiterung erfordern.
  - `OTEL_SERVICE_NAME` (Welle-6-Default: `grid-gym-sim` bzw.
    `grid-gym-api`).
  - `OTEL_RESOURCE_ATTRIBUTES` (C3-Smoke-Fixture setzt hier
    die per-Lauf eindeutige `service.instance.id`).
- `make runtime`/`make compose-smoke` werden um Collector-
  Liveness-Wait erweitert; Boot-Reihenfolge per
  `depends_on.condition: service_healthy`.
- Trivy-Image-Audit pruft den Collector-Tag mit (Whitelist via
  vorhandenes Image-Audit-Pattern).

### C3 — `feat(welle-6)`/`docs`: Compose-/Integration-Smoke + Runbook + Status/DoD-Sync

- Integration-Smoke-Test (`tests/integration/test_otlp_compose_smoke.py`):
  - Sink-Determinismus-Setup (zwingend vor Boot):
    - Generiere per-Lauf eindeutige `service.instance.id`
      (z. B. `uuid4()`); per `OTEL_RESOURCE_ATTRIBUTES`-Env-Var
      an API/Sim weitergereicht.
    - Generiere per-Lauf eindeutigen Sink-Pfad (`pytest`-
      `tmp_path / "otel-out.jsonl"`); per
      `OTEL_COLLECTOR_FILE_SINK`-Env-Var an Collector weitergereicht.
    - Truncation der Sink-Datei vor Boot (defensive — `tmp_path`
      sollte ohnehin leer sein, aber Pflicht-Schritt fuer den
      Fall, dass Compose-Volumes Reste tragen).
  - Boot API + Sim + Collector via Compose-Fixture (mit den
    obigen Env-Vars).
  - Trigger einen Tick mit `RuleBasedAgent` + Battery-Fault
    (Demo-Szenario aus Welle 4b/Welle 2 wiederverwendet).
  - **Erzwungener Flush + Provider-Shutdown vor Assertions**
    (SDK-Seite — sonst sitzen Spans/Metrics/Logs noch in
    `BatchSpanProcessor` / `BatchLogRecordProcessor` /
    `PeriodicExportingMetricReader`):
    - `tracer_provider.force_flush()` + `shutdown()`.
    - `logger_provider.force_flush()` + `shutdown()`.
    - `meter_provider.force_flush()` + `shutdown()`.
    Reihenfolge: erst `force_flush()` aller Provider, dann
    `shutdown()`, damit kein Provider in Mitte des Flushes
    geschlossen wird. C1-Adapter stellt diese Provider-
    Handles ueber `build_otlp_adapters(...)` bereit oder
    exponiert eine `flush_and_shutdown()`-Helper-Funktion
    fuer Test-Use.
  - **Bounded Poll-Loop auf den Sink** (Collector-Seite —
    selbst nach SDK-Flush kann der Collector-`batch`-
    Processor und der `file`-Exporter noch puffern; die
    kurze Batch-Timeout-Konfig in C2 minimiert das, aber
    der Smoke wartet zusaetzlich): bis zu **5 Sekunden**
    Polling im 100-ms-Intervall, bis im Sink die drei
    erwarteten Eintraege (Span + Metric + Log) mit der
    per-Lauf eindeutigen `service.instance.id` sichtbar
    sind. Timeout → Test-Failure mit klarem Fehlertext
    („Smoke-Sink hat nach 5s keine Eintraege fuer
    instance.id=<uuid> gesammelt — flush nicht durchgekommen
    oder Adapter nicht verkabelt").
  - Pruefe gegen den Collector-File-Sink, dass im Output
    **alle drei** Adapter-Pfade Spuren hinterlassen haben:
    - **≥ 1 Span** mit `name == "tick.cycle"` (Welle-5-
      TickLoop-Span aus ADR 0024 §2.6).
    - **≥ 1 Metric** mit `name == "tick_count"` (Welle-5-
      Counter).
    - **≥ 1 Log-Record** mit `body in {"tick_begin", "tick_end"}`
      (Welle-5-Per-Tick-Trail).
    Alle Assertions filtern auf die per-Lauf eindeutige
    `service.instance.id`, damit kein Alt-Eintrag aus einem
    anderen Run als positiver Beleg durchgeht.
  - Pruefe zusaetzlich Service-Resource-Attribute
    (`service.name`, `service.instance.id`).
- Runbook `docs/user/observability.md` (neu) mit:
  - Welche Spans/Metrics/Logs der Tick-Loop emittiert
    (Quervers auf ADR 0024 §2.6 und ADR 0027 §2.6).
  - Lokaler OTLP-Stack-Boot via `make runtime` +
    Inspizierung des Collector-Outputs.
  - Failure-Modes + Diagnose-Pfad (Collector down →
    Adapter-Log-Pattern, Export-Timeout → Backpressure-
    Verhalten).
- `README.md` + `README.de.md` Eintrag (eine Zeile in der
  Status-Tabelle bzw. Telemetry-Sektion, beide Sprach-
  Varianten symmetrisch) inkl. Welle-6-Closure-Datum.
- C3 traegt zusaetzlich Status `In Progress → Done`,
  Welle-6-Gate-Beleg (`make fullbuild` cache-frei gruen ohne
  Override **mit** Collector-Sibling), Test-/Coverage-Stand,
  und M3-Welle 7 (Closure) als naechster Schritt im
  [`in-progress/README.md`](README.md) + Slice-Plan-Status-
  Text-Sync.

### End-of-Wave — `chore`: git mv M3-welle-6.md → done/ (rename-only)

Per Wave-Self-Close-Commit-Konvention reiner
`git mv M3-welle-6.md ../done/M3-welle-6.md`. Inhalts-Folge-Edits
(relative Link-Anpassung dieses Dokuments, Bezug-Pfade-Pflege per
[`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md))
in einem unmittelbar nachfolgenden Commit.

---

## 1. Context

M3 liefert drei distinkte Sub-Bereiche entlang der Welle 0..7:

- **Faults** (Welle 1+2) — `Done` 2026-05-20.
- **Multi-Agent** (Welle 3 + 4a + 4b) — `Done` 2026-05-22.
- **Observability** (Welle 5 + 6) — Foundation `Done`
  2026-05-23, **OTLP-Adapter diese Welle**.

Welle 6 ist die Export-Welle des Observability-Bereichs: sie
verkabelt die in Welle 5 etablierten Driven-Ports
(`LogPort`/`MetricsPort`/`TracePort`) mit einem produktiven
OTLP-Collector ueber gRPC. Ohne Welle 6 traegt das System zwar
Telemetrie-Surface im Code, aber nichts verlaesst den Prozess.
Mit Welle 6 verlaesst Tick-/Agent-/Fault-Telemetrie den Prozess
ueber OTLP-gRPC und landet in einem Sibling-Collector im
Compose-Stack.

Welle 7 (Closure) hebt ADR 0022/0023/0024 (sowie
0025/0026/0027) auf `Accepted`, schliesst M3 in
`done/M3-…md` ab und macht den End-to-End-Sweep S-1..S-6.

Quellen:

- M3-Slice-Plan
  [`M3-faults-agents-observability.md §3 Welle 6`](M3-faults-agents-observability.md)
  (kanonische Spec).
- Welle-5-Closure-Doc
  [`done/M3-welle-5.md`](../done/M3-welle-5.md) — §4.4 Welle-6-
  Forward-Pointer (Counter-/Gauge-Naming, `_obs_observe`-Helper,
  Trace-ID-Determinismus, `SpanContext`-Felder, Sentinel-Pattern
  fuer `scenario.observability`).
- Lastenheft §19 Telemetrie (`GG-OTEL-001..004`).
- Architektur §4.2 Driven-Ports-Tabelle (`GG-AR-PORT-DRN-008`),
  §5 Komponentensicht (`adapters/driven/telemetry-*`-Pfad Z. 314),
  §15 Beobachtbarkeit.
- [`ADR 0024`](../../adr/0024-observability-port-trio.md)
  (`Provisional` — Port-Trio-Spec).
- [`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md)
  (Bezug-Pfade-Pflege bei `git mv`).
- [`ADR 0029`](../../adr/0029-no-coverage-pragma-contract.md)
  (Adapter-Pragmas verboten).
- Trigger 006
  [`open/006-mypy-strict-bytes.md`](../done/006-mypy-strict-bytes.md)
  (`--strict-bytes`-Entscheidung am OTLP-Bytes-Vertrag — Welle-6-
  Konsument).

## 2. Scope

**In-Scope (Welle 6):**

- `adapters/driven/telemetry_otlp/` mit 3 Adaptern
  (`OtlpLogAdapter` / `OtlpMetricsAdapter` / `OtlpTraceAdapter`)
  + `OtlpAdapterConfig`-frozen-dataclass + `build_otlp_adapters(
  config)`-Factory.
- Transport: **OTLP-gRPC** ueber
  `opentelemetry-exporter-otlp-proto-grpc` + `grpcio`.
  Begruendung: Default-Pfad der OTel-SDKs, protobuf/binaer
  effizienter, weniger Sonderlogik im Adapter. Die zusaetzliche
  `grpcio`-Runtime-Dependency ist akzeptabel, weil das Runtime-
  Image ohnehin Telemetrie-Surface traegt. HTTP/protobuf bleibt
  Folge-Option hinter derselben internen Export-Basis (nicht
  Welle 6).
- `deploy/compose.yml` + `tests/integration/compose.yml`
  OTLP-Collector-Sibling (`otel-collector`-Service) inkl.
  Konfig-File + File-Sink fuer Smoke-Inspection.
- Compose-/Integration-Smoke-Test, der ≥ 1 Span + ≥ 1 Metric
  am Collector-File-Sink verifiziert (M3-Slice-Plan §2
  Erfolgskriterium 5).
- ADR-0024-Schaerfung (Welle-5-§4.4-Forward-Pointer aufloesen).
- Runbook `docs/user/observability.md`.
- Default-`CRITICAL_COV_TARGETS` um
  `src/grid_gym/adapters/driven/telemetry_otlp` erweitert
  (filesystem-Pfad-Form analog Dockerfile:245-Liste; der
  Architektur-Slug `telemetry-otlp` bleibt der prosaische
  Komponenten-Name).
- Trigger 006 (`--strict-bytes`) Entscheidung am konkreten
  OTLP-Bytes-Vertrag (aktivieren oder konkrete Begruendung fuer
  Verschiebung).

**Out-of-Scope (Welle 7 / Folge-Slices):**

- OTLP-HTTP/protobuf-Transport — Folge-Option hinter gemeinsamer
  interner Export-Basis.
- ADR 0024 → `Accepted` (passiert mit M3-Welle 7).
- Dashboards, Alerts, Trace-Korrelation in Multi-Service-
  Szenarien (Grafana/Tempo/Loki/Mimir) — Post-M3.
- RL-Agent-Telemetrie-Erweiterungen (`GG-FUTURE-001/002`).
- M4-Protokolladapter-Telemetrie (MQTT/Modbus/OPC-UA) — M4
  liefert eigene Telemetry-Schichten ueber die gleichen Ports.
- Persistente Span/Log-Storage (Datenbank-Sinks) — M6.

## 3. Architektur-Entscheidungen (C1-Triage TBD)

Wird mit C1 (ADR-0024-Schaerfung) gefuellt. Erwartete Decision-
Items:

- **D-1 Adapter-Modul-Struktur**: ein Modul mit drei Klassen
  (`telemetry_otlp/__init__.py`) **oder** drei Sub-Module
  (`logs.py` / `metrics.py` / `traces.py`)? Default-Vorschlag:
  drei Sub-Module + `__init__.py`-Re-Export, weil Logs/Metrics/
  Traces unterschiedliche OTel-SDK-Surfaces haben.
- **D-2 `OtlpAdapterConfig`-Quelle**: nur explizite Kwargs
  vs. `OTEL_*`-Env-Var-Fallback. Default-Vorschlag: Env-Var-
  Fallback mit expliziter Kwarg-Override (OTel-SDK-Standard).
- **D-3 Failure-Mode bei Collector-Down**: Re-Raise vs.
  Silent-Log-and-Drop. Default-Vorschlag: Silent-Log-and-Drop
  (Tick-Loop-Robustheit > Telemetrie-Strenge); WARN-Log auf
  `LogPort` mit Throttling.
- **D-4 Span-Dauer-Messung — Entschieden (C0):** OTel-SDK-
  Default (Start-/End-Zeitpunkte werden vom OTel-Span/SDK
  selbst gesetzt — `tracer.start_span()` setzt `StartTime`,
  `span.end()` setzt `EndTime`; `BatchSpanProcessor` ist
  reines Export-Vehikel), **kein eigener `time.*`-Aufruf im
  Adapter-Code**. Begruendung:
  die Alternative (`time.monotonic()` adapterseitig) waere zwar
  technisch zulaessig (Adapter liegt ausserhalb der Core-AC-NO-
  TIME-Boundary), wuerde aber ohne Mehrwert eine zusaetzliche
  Wall-Clock-Affordance in unserem Code erzeugen und C1 zwei
  legitime Implementierungen offen lassen. Konsequenz fuer §5
  Critical Files: `traces.py` importiert kein `time`; einzige
  Zeit-Quelle ist die externe OTel-SDK. Folge fuer §7 R-3:
  `time.*`-mypy-Findings sind in C1 ein Bug-Signal, kein
  Style-Issue. **Aenderungs-Vertrag:** Re-Open dieser Decision
  nur per ADR-Folge (ADR 0011-Schaerfung ODER neuer ADR), nicht
  im C1-Code-Pfad.
- **D-5 `_obs_observe`-Helper-Symmetrie**: ergaenzen vs.
  weglassen (Welle-5-§4.4-N-2). Default-Vorschlag: nein.
- **D-6 Counter/Gauge-Naming-Konvention**: `tick_count`
  (Counter, monoton) und `tick_index` (Gauge, State) klar
  trennen (Welle-5-§4.4-N-1). Default-Vorschlag: Counter
  bleibt, `tick_index`-Gauge **nicht** ergaenzt (YAGNI bis
  M5/UI).
- **D-7 `NullTraceAdapter`-Signatur-Asymmetrie**
  (Welle-5-§4.4-L-2): Protocol-Erweiterung **oder** Adapter-
  spezifische `| None`-Signatur. Default-Vorschlag: Protocol-
  Erweiterung (OTel-`OptionalSpanContext`-Pattern).
- **D-8 Trigger-006-Aktivierung**: am konkreten OTLP-Bytes-
  Vertrag aktivieren vs. verschieben. Default-Vorschlag: am
  konkreten C1-Code entscheiden.
- **D-9 ADR-Folge fuer Compose-Smoke-Pattern**: separater
  ADR (Provisional) **oder** Schaerfung-ohne-Supersede in
  bestehender ADR. Default-Vorschlag: Schaerfung-ohne-
  Supersede in ADR 0024.

## 4. Liefer-Reihenfolge

Siehe Commit-Sequenz oben (C0 → C1 → C2 → C3 → End-of-Wave).
Reihenfolge ist zwingend, weil C2 (Compose-Service) gegen den
in C1 produzierten Adapter laeuft und C3 (Integration-Smoke)
beide voraussetzt.

## 5. Critical Files (anticipated)

- `src/grid_gym/adapters/driven/telemetry_otlp/__init__.py` —
  **neu** (`build_otlp_adapters(config)`-Factory, Re-Exports).
- `src/grid_gym/adapters/driven/telemetry_otlp/_config.py` —
  **neu** (`OtlpAdapterConfig`-frozen-dataclass).
- `src/grid_gym/adapters/driven/telemetry_otlp/logs.py` —
  **neu** (`OtlpLogAdapter`).
- `src/grid_gym/adapters/driven/telemetry_otlp/metrics.py` —
  **neu** (`OtlpMetricsAdapter`).
- `src/grid_gym/adapters/driven/telemetry_otlp/traces.py` —
  **neu** (`OtlpTraceAdapter`).
- `src/grid_gym/hexagon/ports/driven/observability.py` —
  evtl. Signatur-Schaerfung (`OptionalSpanContext`-Pattern,
  D-7).
- `deploy/compose.yml` — `otel-collector`-Service +
  `environment`-Block fuer API/Sim-Container.
- `deploy/otel-collector-config.yaml` — **neu** (Receiver +
  Exporter + Pipelines).
- `tests/integration/compose.yml` — falls separat: gleiche
  Collector-Verkabelung.
- `tests/integration/test_otlp_compose_smoke.py` — **neu**
  (Smoke-Assertion ≥ 1 Span + ≥ 1 Metric).
- `tests/unit/adapters/driven/telemetry_otlp/test_*.py` —
  **neu** (Surface + Roundtrip + Failure-Modes).
- `pyproject.toml` / `requirements*.txt` — neue Dependencies
  (`opentelemetry-exporter-otlp-proto-grpc`, `grpcio`,
  `opentelemetry-sdk` falls noch nicht enthalten).
- `Dockerfile` (`ARG CRITICAL_COV_TARGETS`-Default Z. 245) —
  Default-Coverage-Target-Liste um
  `src/grid_gym/adapters/driven/telemetry_otlp` erweitert
  (filesystem-Pfad-Form, Underscore; **nicht** der Architektur-
  Slug `telemetry-otlp`). DoD-Item aus Roadmap §3 M3 +
  M3-Slice-Plan §3 Welle 6. Der `Makefile`-Pfad selbst aendert
  sich nicht — `CRITICAL_COV_TARGETS` wird durchgereicht.
- `tools/arch_check.py` — pruefen, ob
  `AC-OBS-ADAPTER-NO-CORE-IMPORT` als 12. Contract
  sinnvoll ist (Adapter darf Ports importieren, kein Core).
- `docs/adr/0024-observability-port-trio.md` — Welle-6-
  Schaerfung per ADR 0011-Pattern + ADR 0006 §4 (`Letzte
  inhaltliche Aenderung`-Pflichtfeld).
- `docs/user/observability.md` — **neu** (Runbook).
- `README.md` + `README.de.md` — Welle-6-Closure-Zeile.

## 6. Verifikationspfad

- `make gates` A-1 gruen ohne Override (lint, format-check,
  mypy `--strict`, arch-check, test-unit, coverage-gate,
  critical-coverage mit erweitertem Target, dep-audit).
- `make test-unit`: bestehende 1023 Tests + Welle-6-Adapter-
  Tests gruen (~30-50 zusaetzliche Tests erwartet — Surface
  je Adapter, Konfig-Defaults, Failure-Modes).
- `make test-integration`: bestehende 19 Tests + mindestens 1
  Welle-6-Compose-Smoke-Test gruen (Collector-Sibling;
  Span + Metric + Log-Sink-Assertion gefiltert auf per-Lauf
  eindeutige `service.instance.id`; SDK-Side `force_flush()` +
  `shutdown()` aller drei Provider; Collector-Side
  Bounded-Poll auf den Sink-File).
- `make fullbuild` cache-frei gruen ohne Override **mit**
  Collector-Sibling (Welle-6-Abnahme-Kriterium).
- AC-PORTS-NO-OUT bleibt KEPT — 3 neue Driven-Adapter,
  keine Driving-Port-Verletzer.
- `AC-NO-TIME` bleibt KEPT — kein Wall-Clock-Zugriff im
  Core und (per D-4 in C0 festgezogen) auch kein `time.*`-
  Import im Adapter-Code. Einzige Wall-Clock-Quelle ist die
  externe OTel-SDK.
- `AC-NO-COVERAGE-PRAGMA` bleibt KEPT.
- `make image-audit` Trivy gegen Runtime-Image + Collector-
  Image gruen (Whitelist pflegen, falls neue Findings).

## 7. Risiken

- **R-1** — **`grpcio`-Runtime-Dependency erhoeht Image-
  Attack-Surface**. *Mitigation:* Trivy-Image-Audit pflegt
  ggf. neue Findings ueber das bestehende Whitelist-Pattern;
  falls kritische Vulns auftauchen, Fallback auf
  HTTP/protobuf-Transport (Welle-6-Folge oder Welle-7-
  Schaerfung).
- **R-2** — **Compose-Smoke wird durch Collector-Sibling
  langsamer / flaky** (Boot-Wait, Healthcheck). *Mitigation:*
  `depends_on.condition: service_healthy` + Healthcheck mit
  konservativem Timeout; falls Boot zu lang, Collector als
  optionaler Smoke-Schritt hinter Feature-Flag (M3-Slice-Plan
  §5 Risiko-Fallback).
- **R-3** — **OTLP-SDK-Typstubs sind unvollstaendig**, so
  dass `mypy --strict` rot wird. *Mitigation:* gezielte
  `# type: ignore[<code>]`-Annotation **nur in den Adapter-
  Modulen** (Pragma-Verbot betrifft Coverage, nicht mypy);
  Alternative: `types-opentelemetry-*`-Stubs falls verfuegbar.
  Falls flaechig: ADR-Folge zur Adapter-mypy-Schicht.
- **R-4** — **Trace-ID-Determinismus bricht Snapshot-Hash-
  Tests**, falls `SpanContext` versehentlich in Snapshots
  eingeht. *Mitigation:* ADR 0024 §2.5 ist explizit dazu —
  `SpanContext` ist **nicht** snapshot-bar; Welle-6-C1 prueft,
  dass keine `spans/`-Sub-Snapshot-Surface entsteht.
- **R-5** — **`--strict-bytes` (Trigger 006) bricht den
  OTLP-Bytes-Pfad**. *Mitigation:* Trigger-006-Aktivierung
  am konkreten C1-Code entscheiden; falls aktiviert und
  zu viele Adapter-Stellen brechen, Trigger 006 offen
  lassen mit konkreter Welle-6-Begruendung.
- **R-6** — **Welle 6 ueberschreitet die Sub-Slicing-
  Schwelle** (Adapter + Compose + Smoke + Runbook +
  ADR-Schaerfung in einer Welle). *Mitigation:* C0..C3 ist
  bereits feingranular; falls C2/C3 sichtbar gross werden,
  in 6a (Adapter + Unit-Tests + ADR-Schaerfung) und 6b
  (Collector + Compose-Smoke + Runbook) splitten — Decision
  vor C2.
- **R-7** — **Hook-Reihenfolge-Drift gegen Welle-5-
  Verdrahtung** (Welle 5 hat `tick.cycle`/`fault.inject`/
  `agent.tick`-Spans bewusst additiv platziert). *Mitigation:*
  Welle 6 aendert die Hook-Reihenfolge **nicht**; Adapter
  konsumiert die existierende Surface. Welle-5-Tests
  (Span-Parent-Asserts) bleiben gruen.
- **R-8** — **Compose-Smoke-False-Positive durch Alt-Eintraege
  im Collector-Sink** (statischer `/tmp/otel-out.jsonl`-Pfad
  wuerde Eintraege aus frueheren oder konkurrierenden Lauefen
  zaehlen). *Mitigation:* Dreifach-Verteidigung in C3 (siehe
  §3 C3 Sink-Determinismus-Setup): (a) per-Lauf eindeutiger
  Sink-Pfad ueber `pytest`-`tmp_path` + `OTEL_COLLECTOR_FILE_SINK`-
  Env-Var, (b) Vorab-Truncation der Sink-Datei vor Boot,
  (c) Assertion-Filter auf eine per-Lauf eindeutige
  `service.instance.id`. Damit kann selbst ein versehentlich
  geteilter Sink-Pfad die Assertion nicht faelschlich gruen
  faerben. Folge fuer DoD-Checkliste #3 (Smoke-Pflicht-Item).
- **R-9** — **Compose-Smoke-False-Negative durch Buffering
  (SDK + Collector)**. Defaults der OTel-SDK
  (`BatchSpanProcessor`, `BatchLogRecordProcessor`,
  `PeriodicExportingMetricReader`) puffern Sekunden bis
  Minuten; der Collector-`batch`-Processor und der `file`-
  Exporter puffern eine zweite Schicht. Ohne erzwungenen
  Flush koennen Span/Metric/Log am Tick-Ende noch nicht im
  Sink stehen, obwohl der Adapter korrekt verkabelt ist —
  Test wuerde flaky rot. *Mitigation:* zweischichtiges
  Flush-Protokoll in C3:
  1. **SDK-Seite (synchron):** `tracer_provider`/
     `logger_provider`/`meter_provider` jeweils
     `force_flush()` und danach `shutdown()` (Reihenfolge:
     erst alle flushen, dann shutdown — sonst flush waehrend
     shutdown unsicher). C1-Adapter stellt diese Provider-
     Handles bereit (z. B. ueber `build_otlp_adapters(...)`-
     Rueckgabe oder eine `flush_and_shutdown()`-Helper-
     Funktion fuer Test-Use).
  2. **Collector-Seite (eventually):** kurze `batch.timeout`-
     Konfig (z. B. 100ms) plus Bounded-Poll mit 5s-Timeout
     im 100-ms-Raster auf den Sink-File. Timeout-Fall
     produziert klaren Fehlertext, der den Flush-Pfad als
     verdaechtig markiert.
  Folge fuer DoD-Checkliste #3 (Buffer-Determinismus-Klausel).
- **R-10** — **OTLP-Log-Exporter-Pfad-Drift bei OTel-Upgrade**.
  `OTLPLogExporter` liegt in OTel-SDK 1.42 unter
  `opentelemetry.exporter.otlp.proto.grpc._log_exporter` (Underscore-
  Prefix). Andere Exporter (`metric_exporter`, `trace_exporter`)
  haben den Underscore nicht — die Asymmetrie ist OTel-historisch.
  Ein 1.43er-Upgrade kann den Pfad zu `log_exporter` (ohne
  Underscore) verschieben, was per Floor `>=1.42` silent passieren
  und C1.3c-Imports brechen wuerde. *Mitigation:* Floor narrow auf
  `>=1.42,<1.43` (`pyproject.toml`). Ein 1.43-Upgrade braucht
  bewussten Test + ggf. Try/Except-Import + ADR-Folge.

## 8. Wandert nach

Per Wave-Self-Close-Commit-Konvention
([`planning/README.md`](../README.md)) — am Ende der Welle-6-
Sequenz reiner `git mv M3-welle-6.md ../done/M3-welle-6.md`,
gefolgt von einem Inhalts-Folge-Commit fuer relative Link-
Anpassungen + Bezug-Pfade-Pflege (ADR 0028).
