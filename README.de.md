# grid-gym

**Deutsch** | [English](README.md)

`grid-gym` ist eine Open-Source-Plattform zur deterministischen
Simulation, Validierung und Analyse elektrischer Energiesysteme. Sie
modelliert Netzanschlusspunkte, PV-Anlagen, Batteriespeicher, Smart Meter
und Lastprofile mit reproduzierbarer Tick-Loop-Ausfuehrung, Snapshot/
Replay, Fault Injection und Protokolladaptern fuer Feldbus-Telemetrie.

> **Nur Simulation — nicht fuer produktive Anlagensteuerung freigegeben.**
> `grid-gym` ist eine Simulations-, Replay- und Validierungs-Umgebung.
> Die Protokolladapter (MQTT, Modbus, OPC-UA, DNP3, IEC-61850) sind dazu
> gedacht, simulierte Geraete oder Testaufbauten anzusteuern — nicht
> reale Anlagen ([`GG-SAFE-007`](spec/lastenheft.md#gg-safe-007), [`GG-NONGOAL-001`](spec/lastenheft.md#gg-nongoal-001)).

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
- fuenf Protokolladapter (MQTT, Modbus, OPC-UA, DNP3, IEC-61850) mit
  container-basierten Integration-Tests
- eine HTTP-API (FastAPI, REST + WebSocket) mit server-gerenderter
  Web-UI (HTMX + Chart.js): Live-Telemetrie, Replay-Controls, Alarme
- Zeitreihen-Persistenz (Postgres) und deterministisches
  Zwei-Lauf-Replay mit `replay_diff_status`-Verdict
- eine Telemetrie-Quality-Pipeline (`STALE`-max-age-Markierung,
  Comm-Failure-`MISSING` + Alarm) fuer [`GG-SAFE-001`](spec/lastenheft.md#gg-safe-001)..004
- einen maschinenlesbaren Abnahme-Lauf via `make accept`
  (`AbnahmeReport`-JSON)

Die aktuellen Gates und Szenarien laufen mit:

```bash
make help
make gates              # 10 Pflicht-Gates (lint, format, typecheck,
                        # arch-check, tests, coverage, critical-coverage,
                        # dep-audit, noqa-gate, spdx-check)
make test-unit          # Unit-Test-Suite (1796 Tests, Stand 2026-06-12,
                        # M7-Closure / v0.1.0)
make test-integration   # Compose-/testcontainers-Integration-Suite
                        # (139 passed + 4 skipped, Stand 2026-06-12; inkl.
                        # Protokolladapter (MQTT/Modbus/OPC-UA/DNP3/IEC-61850),
                        # OTLP, HTTP-API/UI, Persistenz + Replay-Determinismus-
                        # E2E und GG-SAFE-001..004-Quality-Pipeline-Smokes;
                        # die 4 Skips sind nur IEC-61850-auf-Python-3.13 —
                        # abgedeckt via `make test-iec61850`)
```

Beispiel-YAML-Szenarien liegen unter
[`tests/integration/scenarios/`](tests/integration/scenarios/).

Das Repository ist **Docker-only**: Host braucht nur `docker` und `make`.
Keine lokale Python-/uv-Installation.

`make fullbuild` faehrt die volle Closure-Pipeline inkl.
`image-audit` (Trivy) und Compose-Smoke. Das Pflicht-
Entwicklungsgate ist `make gates`.

> Vulnerability-Audit-Ignores werden aus
> `deploy/security/vulnignore.yaml` (Audit-Source-of-Truth mit
> Pflicht-Feldern `id`/`reason`/`expires`/`scope`) gerendert
> per `make render-trivyignore` zu
> `deploy/security/.trivyignore` (siehe [`ADR 0044`](docs/plan/adr/0044-generated-trivyignore-permit.md)). Abgelaufene
> Eintraege brechen den Build und erzwingen Maintenance ohne
> externe Erinnerung. Aktuell gibt es keine aktiven Ignore-
> Eintraege. (Der vorige Eintrag CVE-2026-42504 — Go-stdlib-MIME-
> Header-DoS im OTel-Collector-Sibling — wurde am 2026-06-18 durch
> den Bump von `otel/opentelemetry-collector-contrib` auf 0.154.0
> (gebaut gegen go1.26.4+) aufgeloest; Trivy-Re-Scan meldet
> 0 HIGH/CRITICAL.)

Aktuelles Release: **v0.2.0** (2026-07-01) — siehe
[Releases](https://github.com/pt9912/grid-gym/releases).
Ein Release wird durch einen `v*.*.*`-Git-Tag-Push ausgeloest
(alternativ Manual `workflow_dispatch` in der GitHub-UI). Der
Release-Workflow publiziert ein Container-Image nach GHCR
(`ghcr.io/<owner>/grid-gym:<tag>`) plus fuenf Release-Asset-Files:
SBOM (CycloneDX-JSON via Syft gegen das Runtime-Image), Test-Reports
(JUnit-XML), Coverage-HTML-Tarball, OpenAPI-Spezifikation (JSON)
und das Demo-Abnahmedokument. Lokale SBOM-Erzeugung: `make sbom`
(schreibt `artifacts/sbom-<version>.cdx.json`; Version-Default aus
`pyproject.toml`).

CI laeuft ueber sechs GitHub-Actions-Workflows: `ci.yml` (lint /
format-check / typecheck / arch-check; die vier Slice-025-Pflicht-
Gates), `tests.yml` (test-unit auf einer Python-3.13/3.14-Matrix +
test-integration), `coverage.yml` (coverage-gate 90/85 Line/Branch +
coverage-gate-critical 90 % Critical-Domain), `dep-audit.yml`
(pip-audit), `fullbuild.yml` (`make fullbuild` bei relevanten Paths +
workflow_dispatch-Fallback; deckt image-audit und Compose-Smoke ab)
und `release.yml` (Tag-Push oder workflow_dispatch).

## Was macht es vertrauenswuerdig?

- **Deterministische Ausfuehrung.** Ein zentraler Tick-Loop treibt ein
  diskretes Zeitmodell; Snapshot-Envelopes und Replay-Samples sind
  byte-reproduzierbar via Canonical-JSON-Serialisierung.
- **Erzwungene Architektur.** 20 Architektur-Contracts laufen bei
  jedem `make arch-check`: 7 Forbidden-Import-Contracts via
  `lint-imports` plus 13 Custom-AST-/Graph-Checks in
  [`tools/arch_check.py`](tools/arch_check.py) (u. a.
  [`AC-ADAPTER-LIGHTWEIGHT`](docs/plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-OTLP-ADAPTER-NO-TIME`](docs/plan/adr/0024-observability-port-trio.md),
  [`AC-TICK-LOOP-PRIVATE-RESUME-ERRORS`](docs/plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) und [`AC-IEC61850-GPL-BOUNDARY`](docs/plan/adr/0035-iec61850-adapter-profile.md)).
- **Zehnstufiges Pflicht-Gate.** `make gates` laeuft Lint, Format-Check,
  `mypy --strict`, Arch-Check, Unit-Tests, Coverage (90 % Line pro
  Modul / 85 % kritisch), Critical-Coverage, Dependency-Audit, ein
  `# noqa`-Verbot und `spdx-check` (GPL-3.0-only-Header-Lint fuer die
  IEC-61850-Boundary) — alles cache-frei gruen ohne lokalen Override.
- **ADR-getriebene Entscheidungen.** Jede tragende Entscheidung wird
  als [Architecture Decision Record](docs/plan/adr/) dokumentiert;
  alle Meilenstein-Closure-ADRs bis M8 sind `Accepted` (69 von 71),
  Wellen-ADRs landen als `Provisional` und werden mit Meilenstein-
  Closure `Accepted` (M8-ADRs 0050/0051/0054/0055..0071 alle `Accepted`).
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

Stand **2026-07-01**:

- **M1..M8 · `Done`** — **der MVP ist geliefert (M7); SOLLTE-Geraete
  & Netz sind geliefert (M8)**. 69 von 71 ADRs `Accepted` (1
  `Provisional`, 1 `Superseded`). Closure-Artefakte:
  [`docs/plan/planning/done/M8-results.md`](docs/plan/planning/done/M8-results.md)
  +
  [`docs/plan/planning/done/M7-results.md`](docs/plan/planning/done/M7-results.md).
- **M8 — SOLLTE-Geraete & Netz** · `Done` (2026-07-01; Welle 1..5)
  → **Release v0.2.0**. Alle vier SOLLTE-Geraete
  ([`GG-DEV-015`](spec/lastenheft.md#gg-dev-015)..018: EV-Charger,
  Transformer, Wind-Turbine, Diesel-Generator), das SOLLTE-Netzmodell
  ([`GG-GRID-005`](spec/lastenheft.md#gg-grid-005)..007: Inselnetz,
  Trafo-Grenzen, Blindleistung) und die BESS-Telemetrie
  ([`GG-BESS-006`](spec/lastenheft.md#gg-bess-006)/007: Temperatur,
  Zellspannung) sind produktiv; M8-ADRs 0050/0051/0054/0055..0071
  `Accepted`. Parallel eingefaltet: Replay-Paar 039/040,
  Multi-Run-Execution, Scenario-Scheduled-Commands (046),
  Harness-Durchsetzungsschicht (051).
- **v0.2.0 released** (2026-07-01): zweiter Release-Workflow-Lauf —
  GHCR-Image `ghcr.io/pt9912/grid-gym:v0.2.0` (+ digest-gleiches
  `:latest`), GitHub-Release mit SBOM (CycloneDX, digest-gebunden),
  JUnit-XML, Coverage-HTML, OpenAPI-JSON und Abnahme-Doku. (v0.1.0
  bleibt die MVP-Basislinie; der Doku-only-Cut v0.1.1 wurde bewusst
  verworfen.)
- **Post-M8-Modus: Trigger-Watch** — kein Folge-Meilenstein wird
  automatisch eroeffnet. Offene Trigger 037 (Multi-Node-Deployment),
  038 (volle [`GG-TERM-002`](spec/lastenheft.md#gg-term-002)/003-Equality-Matrix),
  047 (SNMP/LwM2M-Adapter) plus der Tooling-/Spike-Bestand tragen
  dokumentierte Aktivierungs-Bedingungen. Ein neuer Meilenstein
  entsteht bei Trigger-Aktivierung oder Stakeholder-Mandat.

**Testbilanz:** 139 Integration passed + 4 skipped (verbleibende
Skips nur IEC-61850-auf-Python-3.13, abgedeckt durch die dedizierte
`make test-iec61850`-Stage per [`ADR 0046`](docs/plan/adr/0046-multi-python-test-stage-pattern.md)) zum M7-Closure
(2026-06-12). `make gates` 10-stufig cache-frei gruen ohne Override;
`make fullbuild` inkl. `accept-pin-check` gruen.

**Pointer:** Anwenderhandbuch →
[`docs/user/anwenderhandbuch.md`](docs/user/anwenderhandbuch.md);
Abnahmereihenfolge [`GG-DEMO-008`](spec/lastenheft.md#gg-demo-008) →
[`docs/user/gg-demo-008-abnahme.md`](docs/user/gg-demo-008-abnahme.md);
Quality-Pipeline-Audit [`GG-SAFE-001`](spec/lastenheft.md#gg-safe-001)..004 →
[`docs/user/safe-001-004-quality-pipeline.md`](docs/user/safe-001-004-quality-pipeline.md);
ADRs → [`docs/plan/adr/README.md`](docs/plan/adr/README.md);
AI-Agent-Briefing → [`AGENTS.md`](AGENTS.md).

## Build, Test, Lint

Einzel-Gates fuer schnelle Feedback-Schleifen:

```bash
make lint                # ruff check
make format-check        # ruff format --check
make typecheck           # mypy --strict (ADR 0005)
make arch-check          # import-linter + tools/arch_check.py (ADR 0002 §A-1)
make arch-check-imports  # nur import-linter (7 Tabu-Contracts)
make arch-check-custom   # nur tools/arch_check.py (13 Custom-Checks)
make docs-check          # Markdown-Link-/Anker-Validator (gepinnter d-check-Container)
make fullbuild           # gates + integration + runtime-Image + image-audit + Compose-Smoke
make perf                # GG-RT-004 + GG-RT-005 SOLLTE: pytest-benchmark gegen tests/perf/baseline.json (20% Median-Drift; ADR 0041; opt-in `--extra perf`; tick-loop 100 Devices x 10k Ticks + telemetry-port 10k Publish/s mit Payloads ≤256 Byte)
# GG-RT-001 MUSS Backpressure-Healthcheck: GET /runs/{id}/healthcheck → JSON mit tick_duration_ms_p50/p95, missed_ticks_count, backpressure_status (Welle-4b-c).
make perf-baseline-update # nur Maintainer: regeneriert tests/perf/baseline.json
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

## Optionale Erweiterungen / Roadmap

Der oben beschriebene MVP-Scope ist umgesetzt und mit **v0.1.0**
(2026-06-12) ausgeliefert; die folgenden
Erweiterungen sind bewusst ausserhalb des MVP gehalten und in
den normativen Anforderungen ([`spec/lastenheft.md`](spec/lastenheft.md)) als optionale
Ergaenzungen gefuehrt:

- weitere Zeitreihen-Speicheradapter
  (TimescaleDB [`GG-PERSIST-006`](spec/lastenheft.md#gg-persist-006), InfluxDB [`GG-PERSIST-007`](spec/lastenheft.md#gg-persist-007))
- Hardware-in-the-Loop-Integration (HIL) [`GG-TEST-004`](spec/lastenheft.md#gg-test-004)
- modellpraediktive Regelung (MPC-Agenten) [`GG-FUTURE-001`](spec/lastenheft.md#gg-future-001)
- Reinforcement-Learning-Agenten (RL) [`GG-FUTURE-002`](spec/lastenheft.md#gg-future-002)

## Projektstruktur

```text
.
├── .github/workflows/           ← 6 CI-Workflows (ci, tests, coverage,
│                                   dep-audit, fullbuild, release)
├── AGENTS.md, CHANGELOG.md, CONTRIBUTING.md, README.de.md, README.md
│                                ← Projekt-Doku + Dual-License-Policy + AI-Agenten-Briefing
├── Dockerfile, Makefile, alembic.ini, pyproject.toml, uv.lock, .python-version
│                                ← Build- / Gate- / Dependency-Schicht (ADR 0002 §6.1)
├── LICENSE + LICENSES/          ← MIT-Default + GPL-3.0-only fuer die IEC-61850-Boundary
├── deploy/
│   ├── compose.yml              ← Produktiver Compose-Stack + OTLP-Collector-Sibling
│   └── otel-collector-config.yaml ← Collector-Konfig (gRPC :4317)
├── docs/
│   ├── archive/                 ← verworfene / historische Skizzen
│   ├── plan/
│   │   ├── adr/                 ← Architecture Decision Records (0001..0053)
│   │   └── planning/
│   │       ├── done/            ← abgeschlossene Slices + Closure-Notizen
│   │       ├── in-progress/     ← aktive Roadmap + Slice-Plaene
│   │       ├── next/            ← geplant, aber noch nicht aktiv
│   │       └── open/            ← Trigger-Watch, offene Folgearbeiten
│   └── user/                    ← anwender- / betreibernahe Doku (Code-Review etc.)
├── harness/                     ← Agent-Harness (roles, review, verification, replay)
├── spec/
│   ├── architecture.md          ← Architektur (GG-AR-*)
│   ├── lastenheft.md            ← normative Anforderungen (GG-*)
│   └── protocol_profiles.md     ← Adapter-Profil-Index pro Protokoll
├── src/grid_gym/
│   ├── adapters/
│   │   ├── driven/
│   │   │   ├── _protocol_otel_wrap.py     ← OTel-Span-Wrapper (+ Comm-Failure-
│   │   │   │                                  Wrapper `_protocol_comm_failure_wrap.py`)
│   │   │   ├── alarm_stream_inmemory/     ← InMemoryAlarmStream + AlarmHistoryBuffer
│   │   │   ├── observability_null/        ← Null-Log / Metrics / Trace-Fallback
│   │   │   ├── persistence_postgres/      ← Postgres-RunRepository + alembic-Migrationen
│   │   │   ├── protocol_dnp3/             ← nfm-dnp3 produktiv + dnp3-outstation dev-only
│   │   │   ├── protocol_iec61850/         ← pyiec61850-ng GPLv3-isoliertes Optional-Extra
│   │   │   ├── protocol_modbus/           ← pymodbus
│   │   │   ├── protocol_mqtt/             ← paho-mqtt
│   │   │   ├── protocol_opcua/            ← asyncua + OpcuaLoopThread-Async-Bridge
│   │   │   ├── random_mt/                 ← MersenneTwisterRandomPort
│   │   │   ├── telemetry_otlp/            ← OTLP-gRPC-Adapter (Log / Metric / Trace-Exporter)
│   │   │   └── telemetry_stream_inmemory/ ← InMemoryTelemetryStream + DemoTelemetryGenerator
│   │   └── driving/
│   │       ├── http_api/        ← FastAPI-App + REST + WebSocket + Komposition-Roots
│   │       └── ui/              ← Jinja2-Templates + vendored HTMX + Chart.js + StaticFiles
│   └── hexagon/
│       ├── core/
│       │   ├── agents/          ← Agent-Protocol + AgentMessageBus + RuleBasedAgent
│       │   ├── devices/         ← battery/, grid_connection/, load/, pv/, smart_meter/
│       │   ├── domain/          ← Frozen-Dataclasses (Command, Event, Alarm, ScenarioFault, ...)
│       │   ├── faults/          ← Battery- + GridFaultAdapter
│       │   ├── grid_model/      ← Bilanz-Modell + LoadEvent / LoadProfile
│       │   ├── replay/          ← Replay-Sample-Codec
│       │   ├── scenario/        ← YAML-Loader + Validator
│       │   ├── serialization/   ← canonical_json
│       │   └── simulation/      ← TickLoop + Scheduler + alarm_mappers
│       └── ports/
│           ├── driven/         ← Clock, DeviceProtocol, Fault, Observability, Random, RunRepository
│           └── driving/        ← AlarmStream, TelemetryStream
├── tests/
│   ├── integration/             ← Compose-basierte Integration-Tests (139 passed + 4 skipped)
│   ├── unit/                    ← pytest-Unit-Tests (1796 Stand 2026-06-12)
│   └── unit/_arch_check_*       ← Architektur-Tests (7 lint + 13 custom = 20 Contracts)
└── tools/
    ├── accept.py                    ← `make accept`-Abnahme-CLI (GG-MVP-003)
    ├── arch_check.py                ← AST- / Graph-Architektur-Checks (ADR 0002 §A-1)
    ├── check_core_determinism.py    ← Core-Determinismus-Sweep
    ├── check_demo_scenario_pin.py   ← Demo-Scenario-Hash-Pin-Lint (`accept-pin-check`)
    ├── check_noqa.py                ← `# noqa`-Verbots-Gate
    ├── check_spdx.py                ← SPDX-Header-Lint fuer die GPL-3.0-only-Boundary
    ├── _demo_replay.py              ← Headless-Demo-Replay-Helper
    ├── diagnose_otlp_span_export.py ← OTLP-Debug-Matrix-Skript
    ├── render_trivyignore.py        ← vulnignore → .trivyignore-Renderer (ADR 0044)
    └── wait_otel_collector.py       ← Bounded-Liveness-Poll fuer distroless OTLP-Collector

(`make docs-check` laeuft ueber das gepinnte `d-check`-Container-Image — kein In-Repo-Skript.)
```

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
