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
make test-unit          # Unit-Test-Suite (1462 Tests, Stand 2026-05-31)
make test-integration   # Compose-/testcontainers-Integration-Suite
                        # (35 Tests inkl. OTLP-, MQTT-, Modbus-, OPC-UA- und DNP3-Smokes)
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
  - Welle 5a — DNP3-Adapter (Spike)
    (ADR [0034](docs/plan/adr/0034-dnp3-adapter-profile.md)
    `Provisional`) · `Done`
  - Welle 5b — IEC-61850-Adapter (Spike, GPL-isoliert)
    (ADR [0035](docs/plan/adr/0035-iec61850-adapter-profile.md)
    `Provisional`) · `Done`
  - Welle 6a — Cross-Adapter-Hardening (OTel-Span-Wrap +
    AC-ADAPTER-LIGHTWEIGHT-Planted-Violator-Test +
    `strict_bytes`) · `Done`
  - Welle 6b — IEC-61850-Lizenz-und-Smoke-Hardening · `Pending`
  - Welle 7 — Closure · `Pending`
- **M5 — UI + Demo** · `Pending`
- **M6 — Performance + Security + CI/CD** · `Pending`

**Testbilanz:** 1564 Unit-Tests + 35 Integration-Tests passed + 4 skipped
(Stand nach M4-Welle-6a-Closure — +27 Unit-Tests ggue. Welle 5b
fuer Cross-Adapter-Hardening: 13 OTel-Span-Wrap-Tests +
7 AC-ADAPTER-LIGHTWEIGHT-Planted-Violator-Property-Tests +
7 Slice-033-Review-Folge-Updates. Welle 5b hatte +75 Unit-Tests ggue.
Welle-5a-Closure fuer den IEC-61850-Adapter: 21 Config-
Validation + 30 Codec-Roundtrip inkl. hypothesis-Property-
Tests + Container-Repr-Rejection + Overflow-Pfade + 18
Protocol-Port-Lifecycle gegen Mock-Client + 6 Read-Pfad-
Edge-Cases; 4 Integration-Smokes fuer den in-process
`IedServer` per `pytest.mark.skip` deaktiviert unter dem
**2c-Mock-only-Fallback** aktiv in Welle 5b — Probe-Run
auf Python 3.12 hat den vollen MMSClient↔IedServer-
Roundtrip verifiziert, aber der grid-gym-Docker-Stack
mit Python 3.14 segfaultet im `_pyiec61850.so`-SWIG-Layer;
Welle-6-Schaerfungspfade in ADR 0035 §2.5 dokumentiert).

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
| OPC-UA-Adapter (M4 Welle 4) | `Done` | [`done/M4-welle-4.md`](docs/plan/planning/done/M4-welle-4.md); ADR [0033](docs/plan/adr/0033-opcua-adapter-profile.md) `Provisional` — `protocol_opcua/`-6-Modul-Paket (asyncua 1.2b2; **erster rein-async-Stack** im Repo mit eigenem `OpcuaLoopThread` — asyncio-Event-Loop in Daemon-Thread + `run_coroutine_threadsafe`-Marshal, Decision O-b; 8 Datatypes (Boolean/Int16/UInt16/Int32/UInt32/Float/Double/String), Polling-Read + Direct-Write, Subscription-Pfad Welle-6-Schaerfung) + in-process `asyncua.Server`-Integration-Smoke parametrisiert ueber alle 8 Datatypes (Decision O-e; LGPL-3.0 Library-Linking, umgeht `open62541/open62541` MPL-2.0-Container-Komplexitaet). asyncua-Pin `>=1.2b2,<2.0` mit dem Python-3.14-Forward-Reference-Fix, der in 1.1.8 fehlt. Folge-Slice [`032`](docs/plan/planning/done/032-opcua-adapter-review-folge.md) hat 6 HIGH + 11 MEDIUM Code-Review-Findings adressiert (Lifecycle-Lock im `OpcuaLoopThread`, Port-Exception-Filter, Quality.INVALID-String-Read, Float32-Quantisierung). |
| DNP3-Adapter (M4 Welle 5a) | `Done` | [`done/M4-welle-5a.md`](docs/plan/planning/done/M4-welle-5a.md); ADR [0034](docs/plan/adr/0034-dnp3-adapter-profile.md) `Provisional` — `protocol_dnp3/`-5-Modul-Paket (nfm-dnp3 1.0.x sync-Master + dnp3-outstation 0.2.x Test-Sibling, **kein** Thread-Marshal noetig — Decision D-c direkt-sync; 2 Datatypes (BinaryInput g1v1/v2, AnalogInput g30v1/v5), Class-0-Polling + filter-by-index, Write-Pfad Welle-5b-Anti-Scope) + in-process `dnp3-outstation.AsyncOutstation`-Integration-Smoke parametrisiert ueber alle 4 Group/Variation-Kombinationen (Decision D-e; beide Libraries MIT, Pure-Python — keine Container-Sibling-Komplexitaet). Library-Bug-Find waehrend C2: `AnalogInput.index` (nicht `.idx` wie nfm-dnp3-Doku-Repr suggeriert). |
| IEC-61850-Adapter (M4 Welle 5b, Spike, GPL-isoliert) | `Done` | [`in-progress/M4-welle-5b.md`](docs/plan/planning/in-progress/M4-welle-5b.md); ADR [0035](docs/plan/adr/0035-iec61850-adapter-profile.md) `Provisional` — `protocol_iec61850/`-5-Modul-Paket (pyiec61850-ng 1.6.x als **eine** Library fuer Client (`MMSClient`) **und** in-process-Server (`IedServer`), sync API — Decision I-b direkt-sync analog Modbus M-c + DNP3 D-b; 4 Datatypes (bool/int32/float/string) × FC-Allow-List `{MX,ST,SP,CF,DC}` mit Adapter-Default `MX`; Per-Target `MMSClient.read_value(reference, fc)` — Decision I-d, RCB-Subscription + GOOSE Welle-6+; Write-Pfad Welle-5b-Anti-Scope, wirft `Iec61850PortWriteNotImplementedError`) + in-process `IedServer(model_path=fixture)`-Integration-Smoke unter **2c-Mock-only-Fallback** aktiv (Decision I-e + I-f; **erstes GPL-isoliertes Sub-Modul** im Repo via `SPDX-License-Identifier: GPL-3.0-only` pro Datei + `LICENSES/GPL-3.0.txt` + LICENSE-Hinweis + `pyiec61850-ng` als opt-in `pip install grid-gym[iec61850]`-Extra, **nicht** in `[project] dependencies`; Probe-Run auf Python 3.12 hat MMSClient↔IedServer-Roundtrip mit libiec61850-nativem CFG-Fixture verifiziert, aber grid-gym-Docker auf Python 3.14 segfaultet im `_pyiec61850.so`-SWIG-Layer — DoD via 18 Mock-Client-Unit-Tests erfuellt, Welle-6-Schaerfungspfade: Python-3.12-Runtime / Library-Upgrade / Wheel-Rebuild). Probe-Run-Library-Findings 2026-06-01: Reference-Konvention konkateniert MODEL+LD-Namen ohne Trennzeichen (`simpleIO`+`GenericIO`→`simpleIOGenericIO`), MMSClient-FC akzeptiert Two-Letter-String, IedServer braucht `model_path` sonst wirft `start()` `ModelError`. |
| Cross-Adapter-Hardening (M4 Welle 6a) | `Done` | [`done/M4-welle-6a.md`](docs/plan/planning/done/M4-welle-6a.md) (Self-Close-Move `d1cb65d`; Slice 034 Review-Folge `bde8fdb` adressiert 15 Findings) — OTel-Span-Wrap via `OtelSpanWrappedDeviceProtocolPort`-Composition-Wrapper fuer alle 5 Adapter (ADR 0024 §4.5; Standard-Attribute `adapter_type`/`target`/`operation`/`latency_ms`; Adapter-Code-Diff: NULL), Adapter-Profil-Index unter [`spec/protocol_profiles.md`](spec/protocol_profiles.md) mit 5 Eintraegen + ADR-Links + Lastenheft-IDs, Lastenheft-§16-Implementierungs-Matrix auf `✅ M4` x 5 synchronisiert, Architektur-§8.2 mit OTel-Wrap-Pattern geschaerft. AC-ADAPTER-LIGHTWEIGHT-Planted-Violator-Property-Test (Welle-1-§7-Folge-Pflicht-Closure) verifiziert Arch-Check-Filter-Korrektheit. Trigger-006-Closure: `[tool.mypy] strict_bytes = true` aktiviert. `compose.yml`-Header konsolidiert in 2 Sibling-Tabellen (Container + In-Process) mit Lizenz-Spalten. Trigger 004 auf M5/M6 verschoben. |
| IEC-61850-Lizenz-und-Smoke-Hardening (M4 Welle 6b) | `Done` | [`in-progress/M4-welle-6b.md`](docs/plan/planning/in-progress/M4-welle-6b.md) — SPDX-License-Identifier-Lint via NEU `tools/check_spdx.py` (10. A-1-Gate `make spdx-check`; 11 GPL-Boundary-Files Lint-clean), NEU arch_check-Contract `AC-IEC61850-GPL-BOUNDARY` (14. arch_check-Contract; 19 → 20 Contracts KEPT; AST-Import-Scan ueber MIT-Code), NEU `CONTRIBUTING.md` mit Dual-License-Policy (Default MIT, GPL-3.0-only opt-in fuer `protocol_iec61850/*`-Boundary), IedServer-Smoke-Reaktivierungs-Probe-Pfad-A-Befund (PyPI `pyiec61850-ng 1.6.1.2` identisch zu Welle 5b, kein cp314-Manylinux-Wheel) → Pfad C aktiv mit konkretem Trigger 009 (passiv: Library publishet cp314-Wheel; aktiv: eigener Slice fuer Dockerfile-Multi-Python-Test-Stage), plus Slice-034-F13-Folge (`_is_adapter_lightweight_path` erweitert um flat-file `_protocol_*.py`-Cross-Adapter-Helper unter `adapters/driven/`). |
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
│   ├── unit/                    ← pytest-Unit-Tests (1462 Stand 2026-05-31, M4-Welle-5a-Closure)
│   ├── integration/             ← Compose-basierte Integration-Tests (35 Tests; OTLP- + MQTT- + Modbus- + OPC-UA- + DNP3-Smoke inkl.)
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
