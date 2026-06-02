# grid-gym

**Deutsch** | [English](README.md)

`grid-gym` ist eine Open-Source-Plattform zur deterministischen
Simulation, Validierung und Analyse elektrischer Energiesysteme. Sie
modelliert Netzanschlusspunkte, PV-Anlagen, Batteriespeicher, Smart Meter
und Lastprofile mit reproduzierbarer Tick-Loop-Ausfuehrung, Snapshot/
Replay, Fault Injection und Protokolladaptern fuer Feldbus-Telemetrie.

## Fuer wen?

`grid-gym` richtet sich an Entwickler, Forschungseinrichtungen und
Systemintegratoren, die eine lokale, nachvollziehbare Umgebung fuer
Energy-Management-Strategien, Smart-Grid-Regelungen, Batteriespeicher-
strategien, Replay-Systeme und HIL-nahe Tests brauchen — ohne reale
Feldgeraete, Cloud-Dienste oder Internetzugriff zur Laufzeit.

## Was kann ich heute ausfuehren?

`grid-gym` ist bereits als lokale, Docker-basierte Validierungs-Umgebung
ausfuehrbar. Die aktuelle Implementierung umfasst:

- einen deterministischen Tick-Loop mit Snapshot- und Replay-Unterstuetzung
- produktive Geraetemodelle fuer Batterie, PV, Last, Netzanschluss und
  Smart Meter
- Fault-Injection- und Recovery-Flows
- Multi-Agent-Szenarien mit einem regelbasierten Agenten
- strukturierte Logs, Metriken und Traces via Observability-Port-Trio
- einen OTLP-Adapter mit lokalem OpenTelemetry-Collector-Smoke-Test
- einen MQTT-Protokolladapter mit Mosquitto-basiertem Integration-Test

Die aktuellen Gates und Szenarien laufen mit:

```bash
make help
make gates              # 10 Pflicht-Gates (lint, format, typecheck,
                        # arch-check, tests, coverage, critical-coverage,
                        # dep-audit, noqa-gate, spdx-check)
make test-unit          # Unit-Test-Suite (~1696 Tests, Stand 2026-06-02,
                        # M5-Welle-4b-Closure + Review-Folge)
make test-integration   # Compose-/testcontainers-Integration-Suite
                        # (51 passed + 4 skipped Tests inkl. OTLP-, MQTT-,
                        # Modbus-, OPC-UA-, DNP3-, IEC-61850-, M5-HTTP-API-,
                        # M5-UI-Foundation-, M5-Live-Telemetry-,
                        # M5-Replay-Controls- und M5-Alarms-Smokes +
                        # Async-Pub/Sub-Probe)
```

Beispiel-YAML-Szenarien liegen unter
[`tests/integration/scenarios/`](tests/integration/scenarios/).

Das Repository ist **Docker-only**: Host braucht nur `docker` und `make`.
Keine lokale Python-/uv-Installation.

> `make fullbuild` enthaelt einen `image-audit`-Schritt, der aktuell
> fehlschlaegt, solange ein ausstehender Debian-13-Base-Image-CVE-Bump
> (`CVE-2026-40356` in der `krb5`-Familie) in einem separaten
> Base-Image-Bump-Stack adressiert wird. Das Pflicht-Entwicklungsgate
> ist `make gates`.

## Was macht es vertrauenswuerdig?

- **Deterministische Ausfuehrung.** Ein zentraler Tick-Loop treibt ein
  diskretes Zeitmodell; Snapshot-Envelopes und Replay-Samples sind
  byte-reproduzierbar via Canonical-JSON-Serialisierung.
- **Erzwungene Architektur.** 20 Architektur-Contracts laufen bei
  jedem `make arch-check`: 6 Forbidden-Import-Contracts via
  `lint-imports` plus 14 Custom-AST-/Graph-Checks in
  [`tools/arch_check.py`](tools/arch_check.py) (u. a.
  `AC-ADAPTER-LIGHTWEIGHT`, `AC-OTLP-ADAPTER-NO-TIME`,
  `AC-TICK-LOOP-PRIVATE-RESUME-ERRORS` und `AC-IEC61850-GPL-BOUNDARY`).
- **Zehnstufiges Pflicht-Gate.** `make gates` laeuft Lint, Format-Check,
  `mypy --strict`, Arch-Check, Unit-Tests, Coverage (90 % Line pro
  Modul / 85 % kritisch), Critical-Coverage, Dependency-Audit, ein
  `# noqa`-Verbot und `spdx-check` (GPL-3.0-only-Header-Lint fuer die
  IEC-61850-Boundary) — alles cache-frei gruen ohne lokalen Override.
- **ADR-getriebene Entscheidungen.** Jede tragende Entscheidung wird
  als [Architecture Decision Record](docs/plan/adr/) dokumentiert;
  M1..M4-Closure-ADRs sind `Accepted`, zukuenftige Meilenstein-Wellen-
  ADRs landen als `Provisional` und werden mit Meilenstein-Closure
  `Accepted`.
- **CI spiegelt lokal.** GitHub Actions faehrt die gleichen
  `lint-imports`-, `ruff check`-, `tools/arch_check.py`- und
  `mypy --strict`-Gates auf jedem Pull Request und `main`-Push
  ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Verhaeltnis zu bess-ems

`grid-gym` und [`bess-ems`](https://github.com/pt9912/bess-ems) sind
Schwesterprojekte im selben Energy-Systems-Toolkit.

`grid-gym` ist die deterministische Simulations-, Replay- und
Validierungs-Umgebung. Sie modelliert elektrische Energiesysteme,
injiziert Faults, zeichnet Traces auf und liefert reproduzierbare
Test-Szenarien.

`bess-ems` ist ein Batterie-Energy-Management-System zum Betrieb von
Battery Energy Storage Systems (BESS) mit Safety-First-Regelschleife,
Markt-/Schedule-Handling und Protokolladaptern.

In der Praxis kann `grid-gym` als lokale Test- und Validierungs-Umgebung
fuer ein produktives EMS wie `bess-ems` dienen: das EMS ist das System
under Test, waehrend `grid-gym` simulierte Geraete, Netzverhalten,
Telemetrie, Replay und Fault-Szenarien bereitstellt.

Die Projekte teilen Architektur-Ideen wie hexagonale Grenzen, explizite
Ports/Adapter und Architektur-Checks — `grid-gym` ist aber **kein**
EMS-Implementierung und dupliziert keine `bess-ems`-Control-Logik.

---

## Status

Stand **2026-06-02**:

- **M1 — Tick-Loop-Spine** · `Done`
- **M2 — Geraetemodelle** · `Done`
- **M3 — Faults + Multi-Agent + Observability** · `Done`
  (sechs ADRs `Accepted`)
- **M4 — Protokolladapter** · `Done`
  (sechs ADRs 0030..0035 `Accepted` 2026-06-01)
  - Welle 0 — Slice-Plan + Trigger-Triage · `Done`
  - Welle 1 — `DeviceProtocolPort`-Foundation
    (ADR [0030](docs/plan/adr/0030-device-protocol-port-surface.md)
    `Provisional`) · `Done`
  - Welle 2 — MQTT-Adapter
    (ADR [0031](docs/plan/adr/0031-mqtt-adapter-profile.md)
    `Provisional`) · `Done`
  - Welle 3 — Modbus-TCP-Adapter
    (ADR [0032](docs/plan/adr/0032-modbus-adapter-profile.md)
    `Provisional`) · `Done`
  - Welle 4 — OPC-UA-Adapter
    (ADR [0033](docs/plan/adr/0033-opcua-adapter-profile.md)
    `Provisional`) · `Done`
  - Welle 5a — DNP3-Adapter (Spike)
    (ADR [0034](docs/plan/adr/0034-dnp3-adapter-profile.md)
    `Provisional`) · `Done`
  - Welle 5b — IEC-61850-Adapter (Spike, GPL-isoliert)
    (ADR [0035](docs/plan/adr/0035-iec61850-adapter-profile.md)
    `Provisional`) · `Done`
  - Welle 6a — Cross-Adapter-Hardening (OTel-Span-Wrap +
    AC-ADAPTER-LIGHTWEIGHT-Planted-Violator-Test +
    `strict_bytes`) · `Done`
  - Welle 6b — IEC-61850-Lizenz-und-Smoke-Hardening · `Done`
  - Welle 7 — Closure · `Done`
- **M5 — UI + Demo** · `In Progress` 2026-06-01
  - Welle 0 — Slice-Plan + Trigger-Triage · `Done`
  - Welle 1 — HTTP-API-Surface + ADR-0036/0037-Schaerfung · `Done`
  - Welle 2 — UI-Foundation (Jinja2 + vendored HTMX + Chart.js
    + StaticFiles-Mount + 2 Page-Routes) · `Done`
  - Welle 3 — Live-Telemetry-Dashboard (NEU
    `TelemetryStreamPort` + `InMemoryTelemetryStream` +
    WS-Subscribe + Chart.js-Time-Series + 6-Zustands-
    Quality-Marker + ADR 0038) · `Done`
  - Welle 4a — Replay-Controls + TickLoop-Wiring (NEU
    `RunStatus` + RunRepository-Extension + TickLoop-
    Control-Surface + `request(action)` + 2 Endpoint-
    Wirings + `TickLoopRegistry` + `DemoTickLoopDriver` +
    Control-UI + ADR 0039) · `Done`
  - Welle 4b — Alarme (NEU Unified `Alarm`-Domain-Type +
    Mapper-Familie in `core/simulation/alarm_mappers.py` +
    `TickResult.emitted_alarms` + TickLoop-Drain-Hook +
    NEU `AlarmStreamPort` + `InMemoryAlarmStream` +
    `AlarmHistoryBuffer` + REST + WS Endpoints + Alarms-
    UI-Page + ADR 0040; loest ADR-0014-§6-Forward-Pointer
    „AlarmSinkPort kommt mit M3" Driving-Side-Anteil) ·
    `Done`
  - Welle 5 — Demo-Pipeline (kanonisches Demo-YAML +
    `make demo` + `python -m grid_gym demo` +
    Lifespan-Demo-Pfad via `GRID_GYM_DEMO_SCENARIO_PATH`
    + `docs/user/demo.md` + Integration-Smoke) ·
    `In Progress` 2026-06-02 (Slice-Doc `155c421` —
    `GG-DEMO-001..005+008` + `GG-DEMO-007` eng
    inkludiert; `GG-DEMO-006` deferiert auf Welle 6)
- **M6 — Performance + Security + CI/CD** · `Pending`

**Testbilanz (Stand 2026-06-02 nach M5-Welle-4b-Closure + Review-Folge):**
~1696 Unit-Tests + 51 Integration-Tests passed + 4 skipped
(1681 post-C3 + 15 aus der Review-Folge).
Die 4 skipped Tests sind der **2c-Mock-only-Fallback** fuer
den IEC-61850-In-Process-`IedServer`-Smoke (ADR 0035 §2.5;
Trigger 009). Pro-Welle-Test-Inkremente + Begruendungen
leben kanonisch in den Slice-Docs unter
[`docs/plan/planning/`](docs/plan/planning/).

**`make gates`** ist 10-stufig und cache-frei gruen ohne Override:
Lint, Format-Check, `mypy --strict`, Arch-Check
(20 Contracts: 6 `lint-imports` + 14 `tools/arch_check.py`),
Test-Unit, Coverage (90 % Line pro Modul / 85 % kritisch),
Critical-Coverage, Dep-Audit, `# noqa`-Verbot, `spdx-check`.

Per-Wellen-Commits, ADR-Pointer und Detail-Aufschluesselung in den
Slice-Plaenen unter [`docs/plan/planning/`](docs/plan/planning/) und
im ADR-Index unter
[`docs/plan/adr/README.md`](docs/plan/adr/README.md).

**Briefing fuer AI-Coding-Agenten:** [`AGENTS.md`](AGENTS.md) — harte
Regeln (Docker-only, `# noqa`-Verbot, `git mv`-Zwei-Commit-Pattern,
Wave-Self-Close-Konvention, sprach-/meilensteinfreie Architektur-Spec).

## Build, Test, Lint

Einzel-Gates fuer schnelle Feedback-Schleifen:

```bash
make lint                # ruff check
make format-check        # ruff format --check
make typecheck           # mypy --strict (ADR 0005)
make arch-check          # import-linter + tools/arch_check.py (ADR 0002 §A-1)
make arch-check-imports  # nur import-linter (7 Tabu-Contracts)
make arch-check-custom   # nur tools/arch_check.py (12 Custom-Checks)
make fullbuild           # gates + integration + runtime-Image-Bau
                         # (siehe Hinweis oben zu image-audit / krb5-CVE)
```

## MVP-Scope

Der erste abnahmefaehige Stand soll lokal auf einem Entwicklerrechner laufen und
keine externen Cloud-Dienste, realen Feldgeraete oder Internetzugriff zur
Laufzeit benoetigen. Nach Bereitstellung der Container-Images soll die Demo
offline ausfuehrbar sein.

Der MVP umfasst laut Lastenheft mindestens:

- lokalen Single-Node-Betrieb ueber Docker Compose
- ein End-to-End-Szenario mit Netzanschlusspunkt, PV, Lastprofil, Smart Meter
  und Batteriespeicher
- Live-Telemetrie, Zeitreihenpersistenz und deterministisches Replay
- eine CLI oder ein Script fuer Abnahmepruefungen
- maschinenlesbare Abnahmeergebnisse fuer Replay-Pruefung,
  Szenario-Validierung und Demo-Healthcheck

## Geplante Funktionsbereiche

- Simulationskern mit diskreten Zeitschritten, zentralem Zeitmodell und
  deterministischem Event Scheduler
- Szenario-, Snapshot-, Export- und Replay-System
- Kanonische Serialisierung fuer Replay-Diff und Golden-File-Vergleiche
- Geraetemodelle fuer Batteriespeicher, PV-Anlagen, Lastprofile,
  Netzanschlusspunkte und Smart Meter
- Vereinfachte Netzmodelle fuer Frequenz-, Spannungs- und Lastverhalten
- Fault Injection fuer Kommunikationsausfaelle, stale Daten, NaN-Werte,
  Frequenzabfaelle, Spannungseinbrueche und Geraeteausfaelle
- REST-API, WebSocket-Telemetrie und lokales Web-UI fuer Demo- und Testbetrieb
- PostgreSQL-basierte Persistenz im MVP; weitere Speicheradapter optional
- Architektur-, Integrations-, Replay- und Demo-Abnahmetests
- Optionale Adapter und Erweiterungen wie MQTT, Modbus TCP, OPC-UA, DNP3,
  IEC61850, TimescaleDB, InfluxDB, Agenten, HIL, MPC und RL

## Projektstruktur

```text
.
├── .github/workflows/ci.yml     ← CI: 4 Pflicht-Gates (Trigger 025)
├── Dockerfile, Makefile, pyproject.toml, uv.lock, alembic.ini, .python-version
│                                ← Build-/Gate-/Dependency-Schicht (ADR 0002 §6.1; alembic fuer M1-Welle-6c-Postgres-Migrationen)
├── LICENSE + LICENSES/GPL-3.0.txt
│                                ← MIT-Default + GPL-3.0-only fuer die IEC-61850-Boundary (ADR 0035 Decision I-f, M4 Welle 5b/6b)
├── README.md + README.de.md + CHANGELOG.md + CONTRIBUTING.md + AGENTS.md
│                                ← Projekt-Doku + Dual-License-Policy + AI-Coding-Agenten-Briefing
├── deploy/
│   ├── compose.yml              ← Produktiver Compose-Stack + OTLP-Collector-Sibling (M3 Welle 6)
│   └── otel-collector-config.yaml ← Collector-Konfig (gRPC :4317, Debug- + File-Exporter)
├── harness/                     ← Agent-Harness-Contracts: README + roles + review + verification + replay
├── spec/
│   ├── lastenheft.md            ← normative Anforderungen (GG-*)
│   ├── architecture.md          ← Architektur (GG-AR-*)
│   └── protocol_profiles.md     ← Adapter-Profil-Index pro Protokoll (M4 Welle 6a)
├── src/grid_gym/
│   ├── hexagon/
│   │   ├── core/
│   │   │   ├── agents/          ← Agent-Protocol + AgentMessageBus + RuleBasedAgent (M3 Welle 3+4a+4b)
│   │   │   ├── devices/         ← battery/, pv/, load/, grid_connection/, smart_meter/ (M2)
│   │   │   ├── domain/          ← Frozen-Dataclasses (Command, Event, Alarm, ScenarioFault, ...)
│   │   │   ├── faults/          ← Battery- + GridFaultAdapter (M3 Welle 2)
│   │   │   ├── grid_model/      ← Bilanz-Modell + LoadEvent/LoadProfile (M2 Welle 5)
│   │   │   ├── replay/          ← Replay-Sample-Codec (M1 Welle 5)
│   │   │   ├── scenario/        ← YAML-Loader + Validator (M1 Welle 5)
│   │   │   ├── serialization/   ← canonical_json (M1 Welle 0a, Trigger 014)
│   │   │   └── simulation/      ← TickLoop + Scheduler + alarm_mappers (M5 Welle 4b)
│   │   └── ports/
│   │       ├── driven/          ← Clock, Random, Fault, RunRepository, Observability (Log/Metrics/Trace), DeviceProtocol (M4 Welle 1)
│   │       └── driving/         ← TelemetryStream (M5 Welle 3), AlarmStream (M5 Welle 4b)
│   └── adapters/
│       ├── driving/
│       │   ├── http_api/        ← FastAPI-App + REST + WebSocket + Komposition-Roots (M5 Welle 1/4a/4b)
│       │   └── ui/              ← Jinja2-Templates + vendored HTMX + Chart.js + StaticFiles (M5 Welle 2)
│       └── driven/
│           ├── persistence_postgres/    ← Postgres-RunRepository + alembic-Migrationen (M1 Welle 6c)
│           ├── random_mt/               ← MersenneTwisterRandomPort (M1 Welle 2)
│           ├── observability_null/      ← Null-Log/Metrics/Trace-Fallback (M3 Welle 5)
│           ├── telemetry_otlp/          ← OTLP-gRPC-Adapter (M3 Welle 6, ADR 0024)
│           ├── telemetry_stream_inmemory/ ← InMemoryTelemetryStream + DemoTelemetryGenerator (M5 Welle 3)
│           ├── alarm_stream_inmemory/   ← InMemoryAlarmStream + AlarmHistoryBuffer (M5 Welle 4b)
│           ├── protocol_mqtt/           ← paho-mqtt (M4 Welle 2, ADR 0031)
│           ├── protocol_modbus/         ← pymodbus (M4 Welle 3, ADR 0032)
│           ├── protocol_opcua/          ← asyncua + OpcuaLoopThread Async-Bridge (M4 Welle 4, ADR 0033)
│           ├── protocol_dnp3/           ← nfm-dnp3 produktiv + dnp3-outstation dev-only (M4 Welle 5a, ADR 0034)
│           ├── protocol_iec61850/       ← pyiec61850-ng GPLv3-isoliertes Optional-Extra (M4 Welle 5b, ADR 0035 Decision I-f)
│           └── _protocol_otel_wrap.py   ← OtelSpanWrappedDeviceProtocolPort Cross-Adapter-Wrapper (M4 Welle 6a)
├── tests/
│   ├── unit/                    ← pytest-Unit-Tests (1696 Stand 2026-06-02, M5-Welle-4b-Closure + Review-Folge)
│   ├── integration/             ← Compose-basierte Integration-Tests (51 passed + 4 skipped; OTLP- + MQTT- + Modbus- + OPC-UA- + DNP3- + IEC-61850- (Mock-only-Fallback) + M5-HTTP-API- + UI-Foundation- + Live-Telemetry- + Replay-Controls- + Alarms-Smokes inkl.)
│   └── unit/_arch_check_*       ← Architektur-Tests (6 lint-imports + 14 custom AC-Checks = 20 A-1; AC-NO-IO-MOD in beiden Tools enforced, einmal gezaehlt)
├── tools/
│   ├── arch_check.py            ← AST-/Graph-Architektur-Checks (ADR 0002 §A-1)
│   ├── check_noqa.py            ← `# noqa`-Verbots-Gate (Slice 027)
│   ├── check_spdx.py            ← SPDX-Header-Lint fuer die GPL-3.0-only-Boundary (M4 Welle 6b)
│   ├── check_refs.py            ← Markdown-Link-Validator (`make docs-check`)
│   ├── check_core_determinism.py ← Core-Determinismus-Sweep
│   ├── wait_otel_collector.py   ← Bounded-Liveness-Poll fuer distroless OTLP-Collector
│   └── diagnose_otlp_span_export.py ← OTLP-Debug-Matrix-Skript (Trigger-029-Pattern)
└── docs/
    ├── plan/
    │   ├── adr/                 ← Architecture Decision Records (0001..0040)
    │   └── planning/
    │       ├── open/            ← Trigger-Watch, offene Folgearbeiten
    │       ├── next/            ← geplant, aber noch nicht aktiv
    │       ├── in-progress/     ← aktive Roadmap + Slice-Plaene
    │       └── done/            ← abgeschlossene Slices + Closure-Notizen
    ├── user/                    ← anwender-/betreibernah (Code-Review etc.)
    └── archive/                 ← verworfene/historische Skizzen
```

Quelltext, Tests und Tooling-Skripte (`src/grid_gym/`, `tests/`,
`tools/`) wurden mit Spike-0 (Closure: [`docs/plan/planning/done/spike-0.md`](docs/plan/planning/done/spike-0.md),
2026-05-15) angelegt; `Dockerfile`, `Makefile` und `pyproject.toml`
sind die verbindliche Build-/Gate-Schicht gemaess
[`ADR 0002`](docs/plan/adr/0002-language-and-build-stack.md)
(`Accepted` 2026-05-15) und
[`ADR 0005`](docs/plan/adr/0005-type-check-gate.md)
(`Accepted` 2026-05-15).

Die Dokumentations- und Planungsstruktur ist in
[`docs/plan/adr/0001-documentation-and-planning-structure.md`](docs/plan/adr/0001-documentation-and-planning-structure.md)
festgelegt.

## Lizenz

Dieses Projekt steht standardmaessig unter der **MIT-Lizenz** —
Details in [`LICENSE`](LICENSE).

**Ausnahme: GPLv3-isolierter IEC-61850-Adapter** (M4 Welle 5b,
ADR [0035](docs/plan/adr/0035-iec61850-adapter-profile.md)
Decision I-f): die Sub-Pfade
`src/grid_gym/adapters/driven/protocol_iec61850/`,
`tests/unit/adapters/driven/protocol_iec61850/`,
`tests/integration/test_iec61850_*.py` und
`tests/integration/fixtures/iec61850/` linken gegen die
GPLv3-lizenzierte Library [`pyiec61850-ng`](https://pypi.org/project/pyiec61850-ng/)
/ libiec61850 und stehen daher unter **GPL-3.0-only**. Der
GPLv3-Volltext steht in [`LICENSES/GPL-3.0.txt`](LICENSES/GPL-3.0.txt).

Die `pyiec61850-ng`-Library selbst ist als **optionales Extra**
ausgeliefert. Der Default-Install bringt nur MIT-Code; wer den
IEC-61850-Adapter — und die zugehoerigen GPL-Distribution-
Bedingungen — aktivieren will, installiert das Extra bewusst:

```bash
pip install grid-gym                  # nur MIT
pip install 'grid-gym[iec61850]'      # MIT + GPLv3-IEC-61850-Adapter
```
