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
make gates              # 9 Pflicht-Gates (lint, format, typecheck,
                        # arch-check, tests, coverage, critical-coverage,
                        # dep-audit, noqa-gate)
make test-unit          # Unit-Test-Suite (1401 Tests, Stand 2026-05-31)
make test-integration   # Compose-/testcontainers-Integration-Suite
                        # (31 Tests inkl. OTLP-, MQTT-, Modbus- und OPC-UA-Smokes)
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
- **Erzwungene Architektur.** 19 Architektur-Contracts laufen bei
  jedem `make arch-check`: 7 Forbidden-Import-Contracts via
  `lint-imports` plus 12 Custom-AST-/Graph-Checks in
  [`tools/arch_check.py`](tools/arch_check.py) (u. a.
  `AC-ADAPTER-LIGHTWEIGHT`, `AC-OTLP-ADAPTER-NO-TIME`,
  `AC-TICK-LOOP-PRIVATE-RESUME-ERRORS`).
- **Neunstufiges Pflicht-Gate.** `make gates` laeuft Lint, Format-Check,
  `mypy --strict`, Arch-Check, Unit-Tests, Coverage (90 % Line pro
  Modul / 85 % kritisch / 96 % gesamt), Critical-Coverage,
  Dependency-Audit und ein `# noqa`-Verbot — alles cache-frei gruen
  ohne lokalen Override.
- **ADR-getriebene Entscheidungen.** Jede tragende Entscheidung wird
  als [Architecture Decision Record](docs/plan/adr/) dokumentiert;
  M1..M3-Closure-ADRs sind `Accepted`, M4-Wellen-ADRs landen als
  `Provisional` und werden mit Meilenstein-Closure `Accepted`.
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

Stand **2026-05-30**:

- **M1 — Tick-Loop-Spine** · `Done`
- **M2 — Geraetemodelle** · `Done`
- **M3 — Faults + Multi-Agent + Observability** · `Done`
  (sechs ADRs `Accepted`)
- **M4 — Protokolladapter** · `In Progress`
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
  - Wellen 5–7 — DNP3 / IEC 61850 / Closure · `Pending`
- **M5 — UI + Demo** · `Pending`
- **M6 — Performance + Security + CI/CD** · `Pending`

**Testbilanz:** 1401 Unit-Tests + 31 Integration-Tests gruen
(Stand nach M4-Welle-4-Closure + Slice-032-Review-Folge —
+81 Unit-Tests ggue. Welle-3-Closure fuer den OPC-UA-Adapter
plus +6 Review-Folge-Tests fuer Lifecycle-Lock, Start-Timeout,
Marshal-Pfad, Quality.INVALID-String-Read, Float32-
Quantisierung und Overflow-Handling).

**`make gates`** ist 9-stufig und cache-frei gruen ohne Override:
Lint, Format-Check, `mypy --strict`, Arch-Check
(19 Contracts: 7 `lint-imports` + 12 `tools/arch_check.py`),
Test-Unit, Coverage (90 % Line pro Modul / 85 % kritisch / 96 %
gesamt), Critical-Coverage, Dep-Audit, `# noqa`-Verbot.

Per-Wellen-Commits, ADR-Pointer und Detail-Aufschluesselung in den
Slice-Plaenen unter [`docs/plan/planning/`](docs/plan/planning/) und
in der Detail-Tabelle unten.

### Status-Detail

| Subsystem | Stand | Belege |
| --- | --- | --- |
| Tick-Loop-Spine (M1) | `Done` | [`done/M1-tick-loop-results.md`](docs/plan/planning/done/M1-tick-loop-results.md) |
| Geraetemodelle (M2) | `Done` | [`done/M2-devices-results.md`](docs/plan/planning/done/M2-devices-results.md) — Battery, PV, Load, GridConnection, SmartMeter + GridModel-Bilanz |
| Faults + Multi-Agent + Observability (M3) | `Done` | [`done/M3-results.md`](docs/plan/planning/done/M3-results.md) — Welle 0..7 geschlossen, sechs M3-ADRs `Accepted` (Detail-Zeilen unten) |
| Fault-Subsystem (M3 Welle 1+2) | `Done` | ADR [0022](docs/plan/adr/0022-fault-injection-protocol.md) + ADR [0025](docs/plan/adr/0025-fault-recovery-pattern.md); `BatteryFaultAdapter` + `GridFaultAdapter` mit Recovery-Logik |
| Multi-Agent-Foundation (M3 Welle 3+4a) | `Done` | ADR [0023](docs/plan/adr/0023-agent-bus-protocol.md) + ADR [0026](docs/plan/adr/0026-agent-drain-registry-pattern.md); `Agent`-Protocol + `AgentMessageBus` + TickLoop-`agents`-Registry |
| Multi-Agent konkret (M3 Welle 4b) | `Done` | ADR [0027](docs/plan/adr/0027-rule-based-agent-scenario-pattern.md); `RuleBasedAgent` mit Hybrid-Rules + Scenario-`agents`-Block + End-to-End-Demo (`tests/integration/scenarios/agents_demo.yaml`) |
| Observability-Foundation (M3 Welle 5) | `Done` | ADR [0024](docs/plan/adr/0024-observability-port-trio.md) + ADR [0029](docs/plan/adr/0029-no-coverage-pragma-contract.md); `LogPort` / `MetricsPort` / `TracePort` + Null-Adapter-Trio |
| OTLP-Adapter (M3 Welle 6) | `Done` | `adapters/driven/telemetry_otlp/` — gRPC-Log-/Metric-/Trace-Adapter + Compose-`otel-collector`-Sibling + Integration-Smoke + Runbook [`docs/user/observability.md`](docs/user/observability.md) |
| Noqa-Hygiene (Slice 027) | `Done` | [`done/027-noqa-abbau.md`](docs/plan/planning/done/027-noqa-abbau.md) — 36 → 0 `# noqa`-Marker, `noqa-gate` in `make gates` aufgenommen |
| Tick-Loop-Private-Import-Contract (Slice 028) | `Done` | [`done/028-tick-loop-private-error-import-contract.md`](docs/plan/planning/done/028-tick-loop-private-error-import-contract.md) — 12. `tools/arch_check.py`-Contract |
| `DeviceProtocolPort`-Foundation (M4 Welle 1) | `Done` | [`done/M4-welle-1.md`](docs/plan/planning/done/M4-welle-1.md); ADR [0030](docs/plan/adr/0030-device-protocol-port-surface.md) `Provisional` — Port + `*Error`-Hierarchie + TickLoop-FIFO/LIFO-Lifecycle |
| MQTT-Adapter (M4 Welle 2) | `Done` | [`done/M4-welle-2.md`](docs/plan/planning/done/M4-welle-2.md); ADR [0031](docs/plan/adr/0031-mqtt-adapter-profile.md) `Provisional` — `protocol_mqtt/`-7-Modul-Paket (paho-mqtt 2.x, Per-Target-Queue-Marshal) + Mosquitto-Integration-Smoke |
| Modbus-TCP-Adapter (M4 Welle 3) | `Done` | [`done/M4-welle-3.md`](docs/plan/planning/done/M4-welle-3.md); ADR [0032](docs/plan/adr/0032-modbus-adapter-profile.md) `Provisional` — `protocol_modbus/`-5-Modul-Paket (pymodbus 3.x sync-Client, **kein** Thread-Marshal noetig — Decision M-c direkt-sync; 5 Datatypes, FC03/FC10 Defaults mit FC04/FC06-Overrides) + in-process-pymodbus-Server-Integration-Smoke fuer das Default-Profil. Folge-Slice [`031`](docs/plan/planning/done/031-modbus-adapter-review-folge.md) hat FC06-Multi-Register-Guard, Read-/Write-Fehler-Taxonomie und bewusste Smoke-Abgrenzung umgesetzt. Trigger-006-Re-Eval (`mypy --strict-bytes`) ist **positiv**; Aktivierung bleibt Folgearbeit. |
| OPC-UA-Adapter (M4 Welle 4) | `Done` | [`in-progress/M4-welle-4.md`](docs/plan/planning/in-progress/M4-welle-4.md); ADR [0033](docs/plan/adr/0033-opcua-adapter-profile.md) `Provisional` — `protocol_opcua/`-6-Modul-Paket (asyncua 1.2b2; **erster rein-async-Stack** im Repo mit eigenem `OpcuaLoopThread` — asyncio-Event-Loop in Daemon-Thread + `run_coroutine_threadsafe`-Marshal, Decision O-b; 8 Datatypes (Boolean/Int16/UInt16/Int32/UInt32/Float/Double/String), Polling-Read + Direct-Write, Subscription-Pfad Welle-6-Schaerfung) + in-process `asyncua.Server`-Integration-Smoke parametrisiert ueber alle 8 Datatypes (Decision O-e; LGPL-3.0 Library-Linking, umgeht `open62541/open62541` MPL-2.0-Container-Komplexitaet). asyncua-Pin `>=1.2b2,<2.0` mit dem Python-3.14-Forward-Reference-Fix, der in 1.1.8 fehlt. Folge-Slice [`032`](docs/plan/planning/done/032-opcua-adapter-review-folge.md) hat 6 HIGH + 11 MEDIUM Code-Review-Findings adressiert (Lifecycle-Lock im `OpcuaLoopThread`, Port-Exception-Filter, Quality.INVALID-String-Read, Float32-Quantisierung). |
| OPC-UA / DNP3 / IEC 61850 (M4 Welle 4–6) | `Pending` | Konkrete Adapter folgen in den naechsten M4-Wellen |
| UI + Demo (M5) | `Pending` | Web-UI, Scenario-Editor, Live-Telemetry-Stream |
| Performance + Security + CI/CD (M6) | `Pending` | 10000-Points/s-Benchmark, SBOM, Multi-Version-Matrix |

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
│       └── driven/              ← Postgres, RandomMT, OTLP, MQTT (M1 Welle 6b/6c + M3/M4)
├── tests/
│   ├── unit/                    ← pytest-Unit-Tests (1401 Stand 2026-05-31, M4-Welle-4 + Slice-032-Closure)
│   ├── integration/             ← Compose-basierte Integration-Tests (31 Tests; OTLP- + MQTT- + Modbus- + OPC-UA-Smoke inkl.)
│   └── unit/_arch_check_*       ← Architektur-Tests (7 lint-imports + 12 custom AC-Checks = 19 A-1)
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
    │   ├── adr/                 ← Architecture Decision Records (0001..0031)
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
