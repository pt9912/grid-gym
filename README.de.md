# grid-gym

**Deutsch** | [English](README.md)

`grid-gym` ist eine geplante modulare Open-Source-Plattform zur Simulation,
Validierung und Analyse elektrischer Energiesysteme.

Der Fokus liegt auf deterministischer Ausfuehrung, reproduzierbaren Ergebnissen,
Replaybarkeit, Fault Injection, simulierter Echtzeitfaehigkeit und
Integrationsfaehigkeit fuer Test- und Forschungsumgebungen.

Das Projekt richtet sich an Entwickler, Forschungseinrichtungen und
Systemintegratoren, die Energy-Management-Strategien, Smart-Grid-Regelungen,
Batteriespeicherstrategien, Replay-Systeme und HIL-nahe Tests in einer
lokalen, nachvollziehbaren Umgebung modellieren wollen.

## Status

**Stand 2026-05-25:** M1 (Tick-Loop-Spine), M2 (Geraetemodelle) und
M3 (Faults + Multi-Agent + Observability) sind alle `Done`. M3
wurde mit Welle 7 geschlossen (sechs M3-ADRs `Accepted`, Trigger 006
verschoben, S-1..S-6-End-to-End-Sweep, vollstaendige Closure-Notiz
[`done/M3-results.md`](docs/plan/planning/done/M3-results.md)).
**Naechster aktiver Slice: M4** (Protokolladapter — MQTT, Modbus,
OPC-UA, DNP3, IEC 61850). Trigger 029 (vermuteter OTLP-Span-
Export-Bug) wurde als Fehlbefund geschlossen — der eigentliche Bug
lag am Span-Regex im Smoke-Test.

**Slice 027 (Noqa-Abbau) `Done`** zwischengeschoben: alle 36
bestehenden `# noqa`-Marker entfernt; `tools/check_noqa.py --fail-on-
noqa` ist 9. Pflicht-Gate in `make gates`. Neue Envelope-Types
(`LogEntry`, `OtlpAdapterConfigOverrides`, `TickLoopWiring`,
`RuleBasedAgentConfig`) + 15 typisierte Sub-Exception-Klassen.

| Subsystem | Stand | Belege |
| --- | --- | --- |
| Tick-Loop-Spine (M1) | `Done` | [`done/M1-tick-loop-results.md`](docs/plan/planning/done/M1-tick-loop-results.md) |
| Geraetemodelle (M2) | `Done` | [`done/M2-devices-results.md`](docs/plan/planning/done/M2-devices-results.md); Battery, PV, Load, GridConnection, SmartMeter + GridModelBilanz produktiv |
| Faults + Multi-Agent + Observability (M3) | `Done` | [`done/M3-results.md`](docs/plan/planning/done/M3-results.md); Welle 0..7 geschlossen. Sechs M3-ADRs `Accepted` (siehe Detail-Zeilen unten). |
| Fault-Subsystem (M3 Welle 1+2) | `Done` | ADR [0022](docs/plan/adr/0022-fault-injection-protocol.md) `Accepted` + ADR [0025](docs/plan/adr/0025-fault-recovery-pattern.md) `Accepted`; `BatteryFaultAdapter` + `GridFaultAdapter` mit `cell_failure`/`voltage_drop` und Recovery-Logik |
| Multi-Agent-Foundation (M3 Welle 3+4a) | `Done` | ADR [0023](docs/plan/adr/0023-agent-bus-protocol.md) `Accepted` + ADR [0026](docs/plan/adr/0026-agent-drain-registry-pattern.md) `Accepted`; `Agent`-Protocol + `AgentMessageBus` + TickLoop-`agents`-Registry + Schritt-A0v/A0a-Drain + Agent-Foundation-State-Snapshot |
| Multi-Agent konkret (M3 Welle 4b) | `Done` | ADR [0027](docs/plan/adr/0027-rule-based-agent-scenario-pattern.md) `Accepted`; `RuleBasedAgent` mit Hybrid Rules + Plugin-Hook + Scenario-`agents`-Top-Level-Block + bidirektionaler `agents.<type>.<id>`-Sub-Snapshot-Resume-Match + End-to-End-Demo (`tests/integration/scenarios/agents_demo.yaml`) |
| Observability-Foundation (M3 Welle 5) | `Done` | ADR [0024](docs/plan/adr/0024-observability-port-trio.md) `Accepted`; `LogPort`/`MetricsPort`/`TracePort` + `SpanContext` + Null-Adapter-Trio + additive TickLoop/Agent/Fault-Hooks. Plus ADR [0029](docs/plan/adr/0029-no-coverage-pragma-contract.md) `Accepted` (`AC-NO-COVERAGE-PRAGMA`). |
| OTLP-Adapter (M3 Welle 6) | `Done` (2026-05-25) | `adapters/driven/telemetry_otlp/` mit `OtlpLogAdapter`/`OtlpMetricsAdapter`/`OtlpTraceAdapter` (gRPC) + `build_otlp_adapters`-Factory + `flush_and_shutdown`-Helper. ADR 0024 §4.5 mit 8 normativen Decisions. arch_check-Contract `AC-OTLP-ADAPTER-NO-TIME` (12. Custom-Contract). `deploy/compose.yml`-`otel-collector`-Sibling + `tools/wait_otel_collector.py`-Liveness-Poll + `make image-audit`-Trivy-Erweiterung (C2). Integration-Smoke `tests/integration/test_otlp_compose_smoke.py` (volles Tripel Span+Metric+Log) + Runbook [`docs/user/observability.md`](docs/user/observability.md) (C3). |
| Noqa-Hygiene (Slice 027) | `Done` | [`done/027-noqa-abbau.md`](docs/plan/planning/done/027-noqa-abbau.md); 36 → 0 `# noqa`-Marker, `make gates` um `noqa-gate` erweitert (9-stufig). |
| Tick-Loop-Private-Import-Contract (Slice 028) | `Done` | [`done/028-tick-loop-private-error-import-contract.md`](docs/plan/planning/done/028-tick-loop-private-error-import-contract.md); 13. arch_check-Contract `AC-TICK-LOOP-PRIVATE-RESUME-ERRORS` (19 A-1-Contracts insgesamt). |
| Protokolladapter (M4) | `Pending` (naechster aktiver Meilenstein) | MQTT, Modbus, OPC-UA, DNP3, IEC 61850 |
| UI + Demo (M5) | `Pending` | Web-UI, Scenario-Editor, Live-Telemetry-Stream |
| Performance + Security + CI/CD (M6) | `Pending` | 10000-Points/s-Benchmark, SBOM, Multi-Version-Matrix |

**Testbilanz:** 1138 Unit-Tests + 21 Integration-Tests gruen
(Stand `0b3164a` nach M3-Closure). `make gates` ist 9-stufig
(lint, format-check, mypy `--strict`, arch-check **19/19
contracts kept** [6 import-linter + 13 arch_check inkl.
`AC-OTLP-ADAPTER-NO-TIME` und `AC-TICK-LOOP-PRIVATE-RESUME-ERRORS`],
test-unit, coverage-gate 90/85 line + 96 % total, critical-coverage
90 inkl. `telemetry_otlp`, dep-audit, **noqa-gate**
[`tools/check_noqa.py --fail-on-noqa`, Slice 027]) — ohne Override
cache-frei gruen seit Welle-6-C2 (`c61ab0d`).

**CI:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) mit vier
Pflicht-Gates fuer `pull_request` und `push` auf `main`:
`lint-imports`, `ruff check`, `python tools/arch_check.py`,
`mypy --strict`. Siehe Closure-Doc
[`done/025-github-actions-four-gates.md`](docs/plan/planning/done/025-github-actions-four-gates.md).

**Briefing fuer AI-Coding-Agenten:** [`AGENTS.md`](AGENTS.md) — harte
Regeln (Docker-only, `# noqa`-Verbot, `git mv`-Zwei-Commit-Pattern,
Wave-Self-Close-Konvention, Architektur-Spec sprach-/meilensteinfrei)
und Pointer auf die kanonischen Quellen.

## Build, Test, Lint

Das Repository ist **Docker-only**: Host braucht nur `docker` und
`make`. Keine lokale Python-/uv-Installation. Alle Builds, Tests
und Gates laufen ueber Dockerfile-Stages.

```bash
make help                # alle Targets auflisten
make gates               # alle A-1-Pflicht-Gates (lint, format-check,
                         # typecheck, arch-check, test-unit, coverage,
                         # critical-coverage, dep-audit, noqa-gate)
make test-unit           # nur Unit-Tests
make test-integration    # Integration-Tests via Compose (Postgres-Container)
make fullbuild           # gates + integration + runtime-Image-Bau
```

Einzel-Gates fuer schnelle Feedback-Schleifen:

```bash
make lint                # ruff check
make format-check        # ruff format --check
make typecheck           # mypy --strict (ADR 0005)
make arch-check          # import-linter + tools/arch_check.py (ADR 0002 §A-1)
make arch-check-imports  # nur import-linter (7 Tabu-Contracts)
make arch-check-custom   # nur tools/arch_check.py (9 Custom-Checks)
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
├── .github/workflows/ci.yml     ← GitHub-Actions: 4 Pflicht-Gates (Trigger 025)
├── CHANGELOG.md
├── Dockerfile                   ← Multi-Stage (Lint, Arch-Check, Test, Runtime)
├── LICENSE
├── Makefile                     ← Build-/Test-Gates pro Dockerfile-Stage
├── alembic.ini                  ← Postgres-Migrationen (M1 Welle 6c)
├── pyproject.toml               ← Build-/Tool-Konfiguration (ADR 0002 §6.1)
├── uv.lock                      ← gepinnte Dependencies (uv)
├── .python-version              ← 3.14 (uv-kompatibel)
├── AGENTS.md                    ← Briefing fuer AI-Coding-Agenten (harte Regeln + Pointer)
├── README.md                    ← englische Hauptversion
├── README.de.md                 ← deutsche Version (dieses Dokument)
├── deploy/compose.yml           ← Produktiver Compose-Stack + OTLP-Collector-Sibling (M3 Welle 6)
├── deploy/otel-collector-config.yaml ← Collector-Konfig (gRPC :4317, Debug- + File-Exporter)
├── src/grid_gym/
│   ├── hexagon/
│   │   ├── core/
│   │   │   ├── agents/          ← Agent-Protocol + AgentMessageBus + RuleBasedAgent (M3 Welle 3+4a+4b)
│   │   │   ├── devices/         ← Battery, PV, Load, GridConnection, SmartMeter (M2)
│   │   │   ├── domain/          ← Frozen-Dataclasses (Command, Event, ScenarioFault, ...)
│   │   │   ├── faults/          ← Battery- + GridFaultAdapter (M3 Welle 2)
│   │   │   ├── grid_model/      ← Bilanz-Modell + LoadEvent/LoadProfile (M2 Welle 5)
│   │   │   ├── replay/          ← Replay-Sample-Codec (M1 Welle 5)
│   │   │   ├── scenario/        ← YAML-Loader + Validator (M1 Welle 5)
│   │   │   ├── serialization/   ← canonical_json (M1 Welle 0a, Trigger 014)
│   │   │   └── simulation/      ← TickLoop + Scheduler
│   │   └── ports/driven/        ← ClockPort, RandomPort, FaultPort, RunRepositoryPort
│   └── adapters/
│       ├── driving/             ← HTTP-API (FastAPI, M1 Welle 6a)
│       └── driven/              ← Postgres, RandomMT (M1 Welle 6b/6c)
├── tests/
│   ├── unit/                    ← pytest-Unit-Tests (1138 Stand 2026-05-25)
│   ├── integration/             ← Compose-basierte Integration-Tests (21 Tests; OTLP-Smoke inkl.)
│   └── unit/_arch_check_*       ← Architektur-Tests (6 import-linter + 13 custom AC-Checks = 19 A-1)
├── tools/
│   ├── arch_check.py            ← AST-/Graph-Architektur-Checks (ADR 0002 §A-1)
│   ├── check_noqa.py            ← `# noqa`-Verbots-Gate (9. A-1-Gate, Slice 027)
│   ├── check_refs.py            ← Markdown-Link-Validator (`make docs-check`)
│   ├── wait_otel_collector.py   ← Bounded-Liveness-Poll fuer distroless OTLP-Collector
│   └── diagnose_otlp_span_export.py ← OTLP-Debug-Matrix-Skript (Trigger-029-Pattern)
├── spec/
│   ├── lastenheft.md            ← normative Anforderungen (GG-*)
│   └── architecture.md          ← Architektur (GG-AR-*)
└── docs/
    ├── plan/
    │   ├── adr/                 ← Architecture Decision Records (0001..0029)
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

Dieses Projekt steht unter der MIT-Lizenz. Details stehen in [`LICENSE`](LICENSE).
