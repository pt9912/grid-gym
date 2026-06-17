# Architektur: grid-gym

**Projektname:** grid-gym
**Dokumenttyp:** Architekturbeschreibung
**Format:** Markdown
**Version:** 0.3.0
**Bezug:** [`lastenheft.md`](lastenheft.md)

---

## 1. Zweck

Dieses Dokument beschreibt die technische Architektur der Plattform
`grid-gym`. Es uebersetzt die Anforderungen aus dem Lastenheft in Schichten,
Module, Ports und Datenfluesse. Es legt fest, wie der deterministische
Simulationskern gegenueber Adaptern, Persistenz, API und UI getrennt ist,
wie Replay und Live-Simulation dieselbe Pipeline teilen und wie Fault
Injection, Agenten und Telemetrie strukturell verankert werden.

Das Dokument ergaenzt das Lastenheft, ersetzt es nicht. Anforderungen
referenzieren ihre `GG-*`-Kennung; Architekturkomponenten erhalten
`GG-AR-*`-Kennungen fuer die Rueckverfolgbarkeit (Rueckverfolgbarkeits-
tabelle weiter unten in diesem Dokument; `GG-TRACE-001` im Lastenheft).
Querverweis-Konvention: Kennungen sind primaere Referenz.

Nicht Gegenstand dieses Dokuments:

- konkrete Sprach- und Frameworkwahl (`GG-AR-OPEN-001`; die Festlegung
  traegt die [Historie](#historie))
- konkrete Modul-Versionen oder API-Pfade
- Roadmap-Meilensteine (das Lastenheft-Kapitel mit `GG-FUTURE-*`-
  Anforderungen listet ausschliesslich Zukunfts-/`KANN`-Punkte)

---

## 2. Architekturprinzipien

| Kennung     | Prinzip                                                                                       | Bezug                                          |
| ----------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| GG-AR-P-001 | Modulare Plattform: Simulationskern, Geraetemodelle, Adapter, Persistenz, UI sind getrennt    | [`GG-ARCH-001`](lastenheft.md#gg-arch-001)                                    |
| GG-AR-P-002 | Hexagonale Architektur fuer den Simulationskern (Ports & Adapters)                            | [`GG-ARCH-002`](lastenheft.md#gg-arch-002)                                    |
| GG-AR-P-003 | Simulationslogik kennt keine Kommunikationsadapter; Abhaengigkeiten zeigen nach innen         | [`GG-ARCH-003`](lastenheft.md#gg-arch-003), [`GG-PRINC-006`](lastenheft.md#gg-princ-006)                      |
| GG-AR-P-004 | Geraetemodelle sind ueber gemeinsame Schnittstelle austauschbar                               | [`GG-ARCH-004`](lastenheft.md#gg-arch-004), [`GG-DEV-001`](lastenheft.md#gg-dev-001)                        |
| GG-AR-P-005 | Interne Kommunikation ist eventbasiert mit deterministischem Scheduler                        | [`GG-ARCH-005`](lastenheft.md#gg-arch-005), [`GG-ARCH-006`](lastenheft.md#gg-arch-006)                       |
| GG-AR-P-006 | Zeitmodell ist zentralisiert; Fachlogik liest Zeit nur ueber den Clock-Port                   | [`GG-ARCH-007`](lastenheft.md#gg-arch-007)                                    |
| GG-AR-P-007 | Live- und Replay-Simulation teilen denselben Tick-Prozessor                                   | [`GG-ARCH-008`](lastenheft.md#gg-arch-008), [`GG-SIM-006`](lastenheft.md#gg-sim-006)                        |
| GG-AR-P-008 | Determinismus ist invariant: gleicher Seed, gleiche Eingaben, gleiche kanonische Ausgabe      | [`GG-SIM-001`](lastenheft.md#gg-sim-001)/002/003, [`GG-RT-002`](lastenheft.md#gg-rt-002)                  |
| GG-AR-P-009 | Einheitliche interne Modelle fuer Telemetrie, Command, Event und Snapshot                     | [`GG-DATA-001`](lastenheft.md#gg-data-001)..005, [`GG-ARCH-005`](lastenheft.md#gg-arch-005)                  |
| GG-AR-P-010 | Sicherer Default: ungueltige, NaN-, stale-, missing-Werte werden nicht ungeprueft uebernommen | [`GG-SAFE-001`](lastenheft.md#gg-safe-001)..004, [`GG-BESS-005`](lastenheft.md#gg-bess-005)                  |
| GG-AR-P-011 | Simulationsadapter sind als solche gekennzeichnet und versprechen keine produktive Steuerung  | [`GG-SAFE-007`](lastenheft.md#gg-safe-007), [`GG-NONGOAL-001`](lastenheft.md#gg-nongoal-001)                    |
| GG-AR-P-012 | Plattform laeuft offline lokal in Docker Compose; PostgreSQL ist Pflicht-Persistenz           | [`GG-DEPLOY-001`](lastenheft.md#gg-deploy-001)/002/011, [`GG-PERSIST-005`](lastenheft.md#gg-persist-005)          |
| GG-AR-P-013 | Konfiguration statt Code: Geraete, Szenarien, Faults, Replays sind YAML-deklariert            | [`GG-SCN-001`](lastenheft.md#gg-scn-001), [`GG-ARCH-004`](lastenheft.md#gg-arch-004)                        |
| GG-AR-P-014 | Architektur-Tabus werden per Build-/Architekturtest erzwungen                                 | [`GG-PRINC-006`](lastenheft.md#gg-princ-006), [`GG-CC-002`](lastenheft.md#gg-cc-002)/003/004, `GG-ARCHTEST-*` |

---

## 3. Systemkontext

```text
            ┌──────────────────────┐  ┌────────────────────────┐
            │ Szenariodateien      │  │ Replay-Quellen         │
            │ (YAML, schema_vN)    │  │ (CSV / JSON Lines)     │
            └──────────┬───────────┘  └──────────┬─────────────┘
                       │                         │
                       ▼                         ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │                          grid-gym                               │
   │                                                                 │
   │   API (REST / WebSocket / OpenAPI) ◄──── CLI / UI / Test-Client │
   │                                                                 │
   │   Simulationskern (Scheduler, Tick-Loop, Geraetemodelle,        │
   │   Fault Injection, Multi-Agent, Snapshot)                       │
   │                                                                 │
   │   Adapter-Schicht (Replay, Protokolladapter — optional)         │
   └────┬──────────────┬─────────────────┬─────────────────┬─────────┘
        │              │                 │                 │
   ┌────▼────┐   ┌─────▼─────┐    ┌──────▼───────┐  ┌──────▼──────────┐
   │ Modbus  │   │ MQTT      │    │ OPC-UA       │  │ DNP3 / IEC61850 │
   │ TCP     │   │ Broker    │    │              │  │                 │
   └─────────┘   └───────────┘    └──────────────┘  └─────────────────┘

   Persistenz : PostgreSQL (Pflicht), TimescaleDB / InfluxDB optional
   Telemetrie : strukturierte Logs, Metriken, optional OpenTelemetry
```

Alle Protokolladapter sind als Simulations- und Testadapter gekennzeichnet
(`GG-AR-P-011`, `GG-SAFE-007`). Externe Netzwerkdienste sind fuer Demo- und
Abnahmelaeufe nicht erforderlich (`GG-DEPLOY-011`).

Bezug: [`GG-ARCH-001`](lastenheft.md#gg-arch-001)/002/003, [`GG-PERSIST-005`](lastenheft.md#gg-persist-005), [`GG-DEPLOY-001`](lastenheft.md#gg-deploy-001)/002/011.

---

## 4. Architekturstruktur

Das System wird aus zwei komplementaeren Sichten beschrieben:

- **Schichtenmodell** — logische Schichten der Verantwortung (Unterabschnitt
  4.1 dieses Dokuments).
- **Hexagonale Sicht** — strukturelle Trennung in fachlichen Kern und
  auswechselbare Adapter mit Driving/Driven-Klassifikation, getragen
  durch das Prinzip `GG-AR-P-002` und die Tabus `GG-AR-TABU-001..008`.

Bei einer scheinbaren Kollision gilt die Dependency Rule aus der
Hexagonalen Sicht (Tabus `GG-AR-TABU-001` bis `GG-AR-TABU-004`).

### 4.1 Schichtenmodell

```text
┌──────────────────────────────────────────────────────────────┐
│ API Layer                                                    │  REST / WebSocket / OpenAPI
├──────────────────────────────────────────────────────────────┤
│ Application / Run Orchestration                              │  Run-Lifecycle, Lauf-Metadaten
├──────────────────────────────────────────────────────────────┤
│ Scenario / Replay / Fault Layer                              │  Schema-Validierung, Event-Erzeugung
├──────────────────────────────────────────────────────────────┤
│ Simulation Core                                              │  Scheduler, Tick-Loop, Snapshot
├──────────────────────────────────────────────────────────────┤
│ Device Models / Multi-Agent                                  │  Asset-Modelle, Strategien
├──────────────────────────────────────────────────────────────┤
│ Domain Layer                                                 │  Telemetry, Command, Event, Quality
├──────────────────────────────────────────────────────────────┤
│ Protocol Adapter Layer                                       │  MQTT, Modbus, OPC-UA, DNP3, IEC61850
├──────────────────────────────────────────────────────────────┤
│ Persistence Layer                                            │  PostgreSQL, optional Timescale/Influx
├──────────────────────────────────────────────────────────────┤
│ Observability Layer                                          │  Logs, Metriken, optional OTEL
└──────────────────────────────────────────────────────────────┘
```

**Interpretation:** Das Schichtenmodell ist eine logische Verantwortungs-
und Datenflusssicht. Es erlaubt nicht automatisch, dass eine hoeher
dargestellte Schicht konkrete Implementierungen tieferer Schichten
referenziert. Konkrete Code-Abhaengigkeiten werden ueber Ports, Adapter und
Composition Root in der Hexagonalen Sicht (`GG-AR-TABU-001..008`) geregelt.

Bezug: [`GG-ARCH-001`](lastenheft.md#gg-arch-001)/002.

### 4.2 Hexagonale Sicht (Driving / Driven Ports)

Der fachliche Kern (Hexagon) enthaelt Domain, Simulationskern,
Geraetemodelle, Szenario- und Fault-Logik sowie das optionale
Multi-Agent-Subsystem. Alles, was Aussenwelt beruehrt — Protokolle,
Persistenz, Telemetrie, HTTP, UI, Dateien, Systemzeit — lebt in Adaptern.

```text
                Driving Ports                    Driven Ports
       (vom Kern angeboten, von               (vom Kern aufgerufen,
        Adaptern aufgerufen)                   von Adaptern implementiert)
                  │                                       ▲
                  ▼                                       │
   ┌────────────────────────────────────────────────────────────────┐
   │                       Hexagon (Kern)                           │
   │   - Domain (Telemetry, Command, Event, Quality, RunMetadata)   │
   │   - Simulation Core (Scheduler, Tick-Loop, Snapshot Store)     │
   │   - Device Models, Multi-Agent, Fault Logic                    │
   │   - Scenario Validator, Replay Mapper                          │
   └────────────────────────────────────────────────────────────────┘
                  ▲                                       │
                  │                                       ▼
        Driving Adapters                          Driven Adapters
        (REST/WebSocket-API,                      (PostgreSQL, MQTT,
         CLI, Test-Driver)                         Modbus, OPC-UA,
                                                   Files, Logger,
                                                   Metrics, OTEL)
```

#### Verzeichnisstruktur

Die konkrete Sprach- und Build-Wahl ist Python 3.13+/3.14 ueber `uv`.
Die Modulgrenzen sind sprachunabhaengig festgelegt; konkrete
Python-Paketnamen unter `src/grid_gym/{hexagon/{core,ports},adapters}/`
sind verbindlich.

```text
grid-gym/
├── spec/                                  ← normative Spezifikationen
│   ├── lastenheft.md
│   └── architecture.md
├── hexagon/                               ← Hexagon (fachlicher Kern + Ports)
│   ├── core/                              ← fachlicher Kern
│   │   ├── domain/                        ← Telemetry, Command, Event, Quality
│   │   ├── simulation/                    ← Scheduler, Tick-Loop, Snapshot
│   │   ├── devices/                       ← Device-Model-Interface + MVP-Modelle
│   │   ├── scenario/                      ← Loader, Validator, Hash
│   │   ├── replay/                        ← Replay-Mapper, Diff-Engine
│   │   ├── faults/                        ← Fault-Modell, Recovery
│   │   └── agents/                        ← Multi-Agent-Subsystem (optional)
│   └── ports/                             ← Port-Interfaces
│       ├── driving/                       ← API-Use-Cases, CLI-Use-Cases
│       └── driven/                        ← Clock, Persistence, Telemetry, Protocols
├── adapters/
│   ├── driving/
│   │   ├── http-api/                      ← REST + WebSocket + OpenAPI
│   │   └── cli/                           ← optionale CLI fuer Demo / Tests
│   └── driven/
│       ├── persistence-postgres/
│       ├── persistence-timescale/         ← optional
│       ├── persistence-influx/            ← optional
│       ├── protocol-mqtt/                 ← optional / Simulation
│       ├── protocol-modbus/               ← optional / Simulation
│       ├── protocol-opcua/                ← optional / Simulation
│       ├── protocol-dnp3/                 ← optional / Simulation
│       ├── protocol-iec61850/             ← optional / Simulation
│       ├── telemetry-logs/
│       ├── telemetry-metrics/
│       └── telemetry-otel/                ← optional
├── ui/                                    ← Web-UI (eigenes Modul)
├── deploy/                                ← docker-compose, optionale k8s-Manifeste
└── tests/                                 ← Unit, Integration, Architektur, E2E
```

Das `hexagon/`-Verzeichnis gruppiert `core/` (fachlicher Kern) und
`ports/` (Port-Interfaces) zu einer fachlichen Einheit. Die Dependency
Rule (`GG-AR-TABU-001..008`) gilt unveraendert: Abhaengigkeiten zeigen
nach innen, `hexagon/core/*` darf weder `adapters/*` noch
`hexagon/ports/driving/*` importieren; `hexagon/ports/*` kennt nur
`hexagon/core/domain`.

#### Driving Ports (vom Kern angeboten)

| Port-ID            | Verantwortung                                               | Bezug                          |
| ------------------ | ----------------------------------------------------------- | ------------------------------ |
| GG-AR-PORT-DRV-001 | `RunControlPort` — Start, Pause, Resume, Stop, Status       | [`GG-API-001`](lastenheft.md#gg-api-001), [`GG-SIM-008`](lastenheft.md#gg-sim-008)         |
| GG-AR-PORT-DRV-002 | `ScenarioPort` — Laden, Validieren, Hashen                  | [`GG-SCN-001`](lastenheft.md#gg-scn-001)/003/004/008         |
| GG-AR-PORT-DRV-003 | `ReplayPort` — Quelle binden, Faktor setzen, Diff abrufen   | [`GG-SIM-006`](lastenheft.md#gg-sim-006), [`GG-REPLAY-001`](lastenheft.md#gg-replay-001)..007 |
| GG-AR-PORT-DRV-004 | `FaultInjectionPort` — Faults laden, ausloesen, beenden     | [`GG-FAULT-001`](lastenheft.md#gg-fault-001)..010              |
| GG-AR-PORT-DRV-005 | `SnapshotPort` — erzeugen, fortsetzen                       | [`GG-SIM-005`](lastenheft.md#gg-sim-005)                     |
| GG-AR-PORT-DRV-006 | `TelemetryQueryPort` — Live- und Lauf-Abfragen              | [`GG-API-002`](lastenheft.md#gg-api-002), [`GG-PERSIST-001`](lastenheft.md#gg-persist-001)     |
| GG-AR-PORT-DRV-007 | `HealthPort` — Healthcheck mit `healthy/degraded/unhealthy` | [`GG-DEPLOY-006`](lastenheft.md#gg-deploy-006)                  |

#### Driven Ports (vom Kern aufgerufen)

| Port-ID            | Verantwortung                                                                                                                                                                    | Bezug                                        |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| GG-AR-PORT-DRN-001 | `ClockPort` — Simulationszeit (nicht Wall-Clock); zentraler Zeitlieferant. Protocol-Vertrag und `SimulationTime`-Alias bilden den verbindlichen Zeitvertrag des Kerns. | [`GG-ARCH-007`](lastenheft.md#gg-arch-007), [`GG-RT-002`](lastenheft.md#gg-rt-002)                       |
| GG-AR-PORT-DRN-002 | `TelemetrySinkPort` — Persistenz und Live-Stream von Telemetriepunkten                                                                                                           | [`GG-DATA-001`](lastenheft.md#gg-data-001), [`GG-PERSIST-001`](lastenheft.md#gg-persist-001)                  |
| GG-AR-PORT-DRN-003 | `RunRepositoryPort` — Laufmetadaten, Szenario-Hash, Lauf-Loeschung                                                                                                               | [`GG-PERSIST-003`](lastenheft.md#gg-persist-003)/009                           |
| GG-AR-PORT-DRN-004 | `AlarmSinkPort` — Alarme erzeugen und persistieren                                                                                                                               | [`GG-PERSIST-004`](lastenheft.md#gg-persist-004), [`GG-BESS-002`](lastenheft.md#gg-bess-002)                  |
| GG-AR-PORT-DRN-005 | `ScenarioSourcePort` — Szenario-Datei lesen                                                                                                                                      | [`GG-SCN-001`](lastenheft.md#gg-scn-001)                                   |
| GG-AR-PORT-DRN-006 | `ReplaySourcePort` — Replay-Samples liefern                                                                                                                                      | [`GG-REPLAY-001`](lastenheft.md#gg-replay-001)/002                            |
| GG-AR-PORT-DRN-007 | `DeviceProtocolPort` — externe Protokolladapter. Gelieferte Implementer: MQTT, Modbus, OPC-UA, DNP3, IEC 61850. Geplante Device-Management-Erweiterungen: SNMP und LwM2M (noch ohne Adapter-Profil/Implementierung). Sync-`Protocol` mit Caller-Scope-Lifecycle (`TickLoop.start_protocol_ports()` / `stop_protocol_ports()`); FIFO start, LIFO stop, Partial-Cleanup. | [`GG-ARCH-003`](lastenheft.md#gg-arch-003), GG-MQTT/MODB/OPCUA/DNP3/IEC/SNMP/LWM2M-001 |
| GG-AR-PORT-DRN-008 | `LogPort`, `MetricsPort`, `TracePort` — strukturierte Observability                                                                                                              | [`GG-OTEL-001`](lastenheft.md#gg-otel-001)..004                             |
| GG-AR-PORT-DRN-009 | `ConfigPort` — Konfigurationsquelle (Datei, ENV)                                                                                                                                 | [`GG-PRINC-005`](lastenheft.md#gg-princ-005)                                 |
| GG-AR-PORT-DRN-010 | `RandomPort` — gebondener PRNG, seedbar pro Lauf.                           | [`GG-SIM-001`](lastenheft.md#gg-sim-001), [`GG-SCN-002`](lastenheft.md#gg-scn-002)                       |
| GG-AR-PORT-DRN-011 | `FaultPort` — Fault-Injection-Adapter-Boundary (`apply_active_faults(devices, context)`). | [`GG-FAULT-001`](lastenheft.md#gg-fault-001)..010                            |

**Hinweis — `AgentMessageBus` ist kein Driven-Port.** Das
Multi-Agent-Subsystem (siehe §14) nutzt einen Core-internen
`AgentMessageBus`, der
bewusst **nicht** als Driven-Port modelliert ist: er kapselt
weder einen Adapter, noch eine externe Library, noch ein
Protokoll, sondern ist reines Domain-Orchestrierungs-Modell
(deterministisch sortierter In-Memory-Bus). Test-Isolierung
laeuft ueber das `Agent`-Sub-Protocol, nicht ueber Port-
Mocking.

#### Dependency Rule (verbindlich)

```text
                       ┌────────────────────┐
                       │   Domain           │  (innerster Ring)
                       └────────▲───────────┘
                                │
                       ┌────────┴───────────┐
                       │ Simulation Core,   │
                       │ Device Models,     │
                       │ Scenario, Faults   │
                       └────────▲───────────┘
                                │
                       ┌────────┴───────────┐
                       │ Application /      │
                       │ Use Cases (Ports)  │
                       └────────▲───────────┘
                                │
                       ┌────────┴───────────┐
                       │ Adapters           │  (Driving + Driven)
                       └────────────────────┘
```

Abhaengigkeiten zeigen **nur nach innen**. Domain und Simulation Core
duerfen keine Adapter, Frameworks oder Transport-Bibliotheken importieren.

#### Architektur-Tabus (Build-/Architekturtest)

| Tabu-ID        | Regel                                                                                   | Bezug                     |
| -------------- | --------------------------------------------------------------------------------------- | ------------------------- |
| GG-AR-TABU-001 | `hexagon/core/*` darf keine `adapters/*`-Symbole importieren                            | [`GG-ARCH-003`](lastenheft.md#gg-arch-003), [`GG-PRINC-006`](lastenheft.md#gg-princ-006) |
| GG-AR-TABU-002 | `hexagon/core/*` darf keine HTTP-, DB-, Messaging-, Datei-, OS-, UI-Pakete importieren  | [`GG-CC-003`](lastenheft.md#gg-cc-003)                 |
| GG-AR-TABU-003 | `adapters/*` darf keine fachlichen Entscheidungen treffen (nur Mapping/Transport)       | [`GG-CC-002`](lastenheft.md#gg-cc-002)                 |
| GG-AR-TABU-004 | Keine zyklischen Modulabhaengigkeiten                                                   | [`GG-CC-004`](lastenheft.md#gg-cc-004)                 |
| GG-AR-TABU-005 | Fachlogik liest Systemzeit nicht direkt; Zeit kommt aus `ClockPort`                     | [`GG-ARCH-007`](lastenheft.md#gg-arch-007)               |
| GG-AR-TABU-006 | Domain-Objekte sind immutable, sofern nicht explizit und lokal begrenzt                 | [`GG-CC-007`](lastenheft.md#gg-cc-007)                 |
| GG-AR-TABU-007 | Keine statischen God-Utility-Classes                                                    | [`GG-CC-006`](lastenheft.md#gg-cc-006)                 |
| GG-AR-TABU-008 | Fehler werden typisiert oder als dokumentierte Exceptions signalisiert, nie verschluckt | [`GG-CC-008`](lastenheft.md#gg-cc-008)                 |

Diese Tabus werden durch Architekturtests erzwungen
(`GG-ARCHTEST-001..005`; siehe `GG-AR-TEST-001` — Testarchitektur).

---

## 5. Komponentensicht

| Komponente             | Modul                               | Verantwortung                                                                                                    | Bezug                                                           |
| ---------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `GG-AR-COMP-CORE`      | `hexagon/core/simulation`           | Deterministischer Tick-Loop, Scheduler, Snapshot, Pause/Resume                                                   | [`GG-SIM-001`](lastenheft.md#gg-sim-001)..009, [`GG-ARCH-006`](lastenheft.md#gg-arch-006)/007/008                            |
| `GG-AR-COMP-SCHED`     | `hexagon/core/simulation/scheduler` | Event-Scheduler mit dokumentiertem Tie-Breaking                                                                  | [`GG-ARCH-005`](lastenheft.md#gg-arch-005)/006                                                 |
| `GG-AR-COMP-DEVICES`   | `hexagon/core/devices`              | `DeviceModel`-Interface, MVP-Modelle (`battery`, `pv`, `load`, `grid_connection`, `smart_meter`), SOLLTE-Modelle | [`GG-DEV-001`](lastenheft.md#gg-dev-001)..018, [`GG-BESS-001`](lastenheft.md#gg-bess-001)..008, [`GG-GRID-001`](lastenheft.md#gg-grid-001)..007             |
| `GG-AR-COMP-SCENARIO`  | `hexagon/core/scenario`             | YAML-Schema-Validator, Szenario-Hash, kanonische Serialisierung                                                  | [`GG-SCN-001`](lastenheft.md#gg-scn-001)..008, [`GG-DATA-005`](lastenheft.md#gg-data-005)                                    |
| `GG-AR-COMP-REPLAY`    | `hexagon/core/replay`               | Replay-Sample-Import, Zeitabbildung, Diff-Engine                                                                 | [`GG-REPLAY-001`](lastenheft.md#gg-replay-001)..007                                              |
| `GG-AR-COMP-FAULTS`    | `hexagon/core/faults`               | Fault-Modell, Aktivierung/Recovery, Determinismus                                                                | [`GG-FAULT-001`](lastenheft.md#gg-fault-001)..010                                               |
| `GG-AR-COMP-AGENTS`    | `hexagon/core/agents`               | optionales Multi-Agent-Subsystem, deterministisches Messaging                                                    | [`GG-AGENT-001`](lastenheft.md#gg-agent-001)..008                                               |
| `GG-AR-COMP-DOMAIN`    | `hexagon/core/domain`               | Telemetry, Command, Event, Quality-Status, Run-Metadaten                                                         | [`GG-DATA-001`](lastenheft.md#gg-data-001)..005, [`GG-DEV-002`](lastenheft.md#gg-dev-002)/003                                |
| `GG-AR-COMP-API`       | `adapters/driving/http-api`         | REST + WebSocket + OpenAPI                                                                                       | [`GG-API-001`](lastenheft.md#gg-api-001)..004, [`GG-UI-001`](lastenheft.md#gg-ui-001)                                      |
| `GG-AR-COMP-UI`        | `ui/`                               | Web-UI fuer Demo, Live-Telemetrie, Alarme, Replay-Steuerung                                                      | [`GG-UI-001`](lastenheft.md#gg-ui-001)..009                                                  |
| `GG-AR-COMP-PERSIST`   | `adapters/driven/persistence-*`     | PostgreSQL (Pflicht), optional Timescale / Influx; Migrationen                                                   | [`GG-PERSIST-001`](lastenheft.md#gg-persist-001)..009                                             |
| `GG-AR-COMP-PROTOCOLS` | `adapters/driven/protocol-*`        | MQTT, Modbus, OPC-UA, DNP3, IEC61850 als gelieferte Simulationsadapter; SNMP/LwM2M als geplante Device-Management-Erweiterungen | [`GG-MQTT-001`](lastenheft.md#gg-mqtt-001), [`GG-MODB-001`](lastenheft.md#gg-modb-001), [`GG-OPCUA-001`](lastenheft.md#gg-opcua-001), [`GG-DNP3-001`](lastenheft.md#gg-dnp3-001), [`GG-IEC-001`](lastenheft.md#gg-iec-001), [`GG-SNMP-001`](lastenheft.md#gg-snmp-001), [`GG-LWM2M-001`](lastenheft.md#gg-lwm2m-001) |
| `GG-AR-COMP-OBS`       | `adapters/driven/telemetry-*`       | Strukturierte Logs, Metriken, optional OTEL                                                                      | [`GG-OTEL-001`](lastenheft.md#gg-otel-001)..004                                                |
| `GG-AR-COMP-DEPLOY`    | `deploy/`                           | docker-compose, Healthchecks, optional Kubernetes-Manifeste                                                      | [`GG-DEPLOY-001`](lastenheft.md#gg-deploy-001)..011                                              |

---

## 6. Datenfluss: Tick-Loop

Der Tick-Loop ist die invariante Spine der Plattform. Live- und
Replay-Laeufe nutzen denselben Prozessor (`GG-AR-P-007`). Innerhalb eines
Ticks werden Schritte sequenziell ausgefuehrt; parallele Berechnung ist
auf einen Tick beschraenkt und committet deterministisch (`GG-SIM-004`).

Die produktive Schrittfolge des `TickLoop.tick()` ist wie folgt fixiert:

```text
   ┌──────────────────────────────────────────────────────────────────┐
   │                       Tick (t)                                   │
   │                                                                  │
   │  A0v Pre-Clock Pending-Agent-Command-Target-Validierung          │
   │       (Atomizitaets-Vertrag: Exception                           │
   │        laesst Clock/Scheduler/Buffer unangetastet)               │
   │  1.   ClockPort.advance(tick_ms); now := clock.now()             │
   │  2.   Scheduler.pop_due(now)                                     │
   │         (stabile Sortierung: time, prio, source, seq, id)        │
   │                                                                  │
   │  ┌── _tick_loop_decimal_context() — prec=28, ROUND_HALF_EVEN ──┐ │
   │  │ A0a Apply validierter Pending-Agent-Commands                │ │
   │  │       (GridConnection-Targets ergaenzen                     │ │
   │  │        manual_override_grid_ids; Buffer wird erst nach      │ │
   │  │        erfolgreichem Apply-Durchlauf geleert)               │ │
   │  │ A   Vor-Tick-Block: LoadDevice-Baseline + LoadProfile-      │ │
   │  │       Overlay + LoadEvent-Overlay → apply_command(          │ │
   │  │       set_power_kw)                                         │ │
   │  │ A2  FaultPort.apply_active_faults(devices, context)         │ │
   │  │       falls fault_port gesetzt                              │ │
   │  │ B   Erste Geraete-Iteration (PV/Load/Battery/SmartMeter):   │ │
   │  │       für jedes Device: tick → telemetry-Sammlung +         │ │
   │  │       Bilanz-Aggregation in generation/load/storage-Buckets │ │
   │  │ C   GridConnection-Auto-Schluss: pro GridConnection ohne    │ │
   │  │       manuellen Override apply_command(set_power_kw,        │ │
   │  │       -pre_grid_residual)                                   │ │
   │  │ D   Zweite Iteration (GridConnection-Tick) → telemetry +    │ │
   │  │       grid_connection-Bucket                                │ │
   │  │ D2  Agent-Tick (optional): für jeden registrierten Agent    │ │
   │  │       agent.tick(context, bus); emittierte Commands         │ │
   │  │       landen im _pending_agent_commands-Buffer fuer A0v/    │ │
   │  │       A0a der NAECHSTEN Tick (GG-AGENT-008 Commit-          │ │
   │  │       Reihenfolge-Invariante)                               │ │
   │  │ E   grid_model.update(generation_kw, load_kw, storage_kw,   │ │
   │  │       grid_connection_kw)                                   │ │
   │  └─────────────────────────────────────────────────────────────┘ │
   │                                                                  │
   │   Persistenz-/Snapshot-Commit:                                   │
   │     - TelemetrySinkPort / AlarmSinkPort / RunRepositoryPort      │
   │       werden deterministisch sortiert bedient                    │
   │     - Snapshots laufen zyklisch oder on-demand ueber             │
   │       TickLoop.snapshot()                                        │
   └──────────────────────────────────────────────────────────────────┘
```

Der Agent-Lifecycle-Hook im TickLoop-Konstruktor
ruft in `_attach_agents()`
`agent.set_run_id(run_id)` und — fuer Agents mit
`_RandomAttachableAgent`-Sub-Protocol —
`agent.attach_random(random_root.sub_port(f"agent-{agent_id}"))`. Damit
gilt die Sub-Random-Stream-Konvention `agent-{agent_id}` produktiv;
Agents ohne Stochastik bekommen keinen Sub-Port aufgezwungen.

**Determinismusinvarianten:**

- Tie-Breaking-Reihenfolge fuer Scheduler-Events ist dokumentiert und
  getestet (`GG-ARCH-006`).
- AgentMessageBus-Sortierung `(simulation_time, sender, sequence)` ist
  deterministisch unabhaengig von Publish-Reihenfolge.
- A0v/A0a-Trennung garantiert, dass ein
  `AgentInvalidCommandTargetError` weder Clock noch Scheduler noch
  Devices noch Pending-Buffer mutiert — Retry/Resume bleibt sauber
  moeglich.
- Agent-Foundation-State (`_pending_agent_commands` +
  `AgentMessageBus`) ist Sub-Snapshot-persistiert, damit Snapshots
  zwischen Agent-Tick und Folgetick keine Commands verlieren.
- Eingangswerte ohne gueltige Quelle werden mit Qualitaetsstatus
  markiert, nie ungeprueft uebernommen (`GG-SAFE-001..004`,
  `GG-AR-P-010`).
- Persistenz darf gepuffert sein, solange Commit-Reihenfolge fachlich
  stabil bleibt (`GG-RT-005`).

---

## 7. Domain-Modell (Skizze)

Die folgenden Typen sind die internen Domaenenobjekte. Sie sind
sprachunabhaengig beschrieben — konkrete Python-Repraesentation
(Pydantic `FrozenModel` oder `@dataclass(frozen=True, slots=True)`)
ist verbindlich unveraenderlich (frozen) festgelegt.

```text
RunMetadata {
  run_id              : RunId
  scenario_hash       : Hash
  schema_version      : String
  seed                : Long
  tick_ms             : Int
  started_at          : SimulationTime
  ended_at            : SimulationTime?
  tool_version        : String
}

TelemetryPoint {
  run_id, tick, simulation_time,
  device_id, metric, value, unit,
  quality   : { valid, stale, estimated, limited, invalid,
                nan, missing, fault_injected },
  source, sequence
}

Command {
  command_id, simulation_time,
  target_device_id, type, payload,
  validation_status,
  result    : { accepted, rejected, limited, expired, failed, ignored }
}

Event {
  event_id, simulation_time,
  source, target, type, payload,
  priority, sequence
}

Alarm {
  alarm_id, run_id, simulation_time,
  target, code, severity, message,
  status, fault_id?
}

Snapshot {
  run_id, simulation_time, tick,
  device_states : Map[DeviceId -> Bytes],
  scheduler_state, agent_states?
}

FaultDefinition {
  fault_id, type, target, start, duration,
  payload, recovery, sequence
}
```

Alle Domain-Objekte sind unveraenderlich (`GG-CC-007`, `GG-AR-TABU-006`).
Kanonische Serialisierung folgt `GG-DATA-005` (stabile Feldreihenfolge,
maximal sechs Nachkommastellen, ISO-8601-UTC oder ganzzahlige
Simulationszeit in ms, Integer-Sequenzen).

---

## 8. Schnittstellen

### 8.1 Externe API

| Endpunkt / Schnittstelle    | Aufgabe                                        | Bezug                     |
| --------------------------- | ---------------------------------------------- | ------------------------- |
| `POST /runs`                | Lauf starten (mit Szenario-Ref + Seed)         | [`GG-API-001`](lastenheft.md#gg-api-001)                |
| `POST /runs/{id}/pause`     | Pause                                          | [`GG-API-001`](lastenheft.md#gg-api-001), [`GG-SIM-008`](lastenheft.md#gg-sim-008)    |
| `POST /runs/{id}/resume`    | Resume                                         | [`GG-API-001`](lastenheft.md#gg-api-001), [`GG-SIM-008`](lastenheft.md#gg-sim-008)    |
| `POST /runs/{id}/stop`      | Stop                                           | [`GG-API-001`](lastenheft.md#gg-api-001)                |
| `GET  /runs/{id}/status`    | Statusabfrage                                  | [`GG-API-001`](lastenheft.md#gg-api-001), [`GG-DEPLOY-006`](lastenheft.md#gg-deploy-006) |
| `POST /runs/{id}/faults`    | Fault injizieren                               | [`GG-API-001`](lastenheft.md#gg-api-001), `GG-FAULT-*`    |
| `POST /runs/{id}/snapshot`  | Snapshot erzeugen / fortsetzen                 | [`GG-SIM-005`](lastenheft.md#gg-sim-005)                |
| `WS   /runs/{id}/telemetry` | Live-Telemetrie-Stream (sortiert, sequenziert) | [`GG-API-002`](lastenheft.md#gg-api-002)                |
| `GET  /openapi.json`        | OpenAPI-Vertrag                                | [`GG-API-003`](lastenheft.md#gg-api-003)                |

Fehlerantworten folgen `GG-API-004`: `code`, `message`, `details`,
`run_id?`, stabiler HTTP-Status. Eingaben werden vor Eintritt in den
Simulationskern validiert (`GG-SAFE-008`).

### 8.2 Adapter-Interfaces (Driven)

- `DeviceProtocolPort` — Read- und Write-Operationen mit Mapping auf
  `TelemetryPoint` / `Command`; Adapter dokumentieren Topic-, Register-,
  Node-, Point- bzw. LN/CDC-Profile (`GG-MQTT/MODB/OPCUA/DNP3/IEC-001`).
  **Fuenf konkrete Implementer** unter
  `src/grid_gym/adapters/driven/protocol_*/` — siehe
  Adapter-Profil-Index in [`spec/protocol_profiles.md`](protocol_profiles.md):
  - `protocol_mqtt/` — MQTT via paho-mqtt 2.x.
  - `protocol_modbus/` — Modbus-TCP via pymodbus 3.x.
  - `protocol_opcua/` — OPC-UA via asyncua 1.2b2 mit eigenem
    `OpcuaLoopThread`; **erster async-Stack** im Repo.
  - `protocol_dnp3/` — DNP3 via zwei-Library-Setup (`nfm-dnp3` + `dnp3-outstation`,
    beide MIT, Pure-Python).
  - `protocol_iec61850/` — IEC-61850 via `pyiec61850-ng` SWIG-Bindings
    (GPLv3-isoliert per SPDX-Header; **erster GPL-isolierter Sub-Module-
    Praezedenzfall** im sonst MIT-Repo; opt-in Extra
    `pip install grid-gym[iec61850]`).
- **OTel-Span-Wrap:**
  jeder `read(target)`/`write(target, command)`-Call wird in einen
  TracePort-Span mit Standard-Span-Attributen (`adapter_type`,
  `target`, `operation`; optional `reference` falls Caller eines
  am Wrapper-Constructor uebergeben hat) umschlossen. Zusaetzlich
  wird ein `latency`-Event mit Attribut `latency_ms` emittiert
  (Event-encoded statt Span-Attribut, weil `TracePort` keine
  `set_attribute`-Surface kennt und Latency erst nach Span-Open
  bekannt ist). Implementation ueber
  alle 5 Adapter-Pakete via `OtelSpanWrappedDeviceProtocolPort`-
  Composition-Wrapper.
- `TelemetrySinkPort` — Append-only, deterministische Sortierung;
  Persistenzadapter sind austauschbar (Postgres → Timescale → Influx).
- `ReplaySourcePort` — liefert Samples mit Originalzeitstempel +
  abgebildeter Simulationszeit; stabile Sortierung bei Zeitstempel-Ties.
- `ScenarioSourcePort` — laed YAML, validiert Schema, gibt kanonisches
  Szenarioobjekt + Hash zurueck.

### 8.3 Konfigurationsquelle

`ConfigPort` liefert eine geschichtete Konfiguration in fester
Praezedenz: CLI-Flags > Umgebungsvariablen > Konfigurationsdatei >
eingebaute Defaults. Geheimnisse werden nie in Klartext geloggt
(`GG-OTEL-002`).

---

## 9. Determinismus, Replay und Zeitmodell

Determinismus ist ein **Cross-Cutting-Concern**, nicht ein einzelner
Modulvertrag.

| Mechanismus                    | Aussage                                                                                                                                                     | Bezug                       |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| Zentraler `ClockPort`          | Einzige Quelle fuer `simulation_time` im Kern; kein direkter Systemzeitzugriff                                                                              | [`GG-ARCH-007`](lastenheft.md#gg-arch-007), GG-AR-TABU-005 |
| Seedbarer `RandomPort`         | Jeder Zufallsstrom haengt am Lauf-Seed und ist pro Lauf reproduzierbar | [`GG-SIM-001`](lastenheft.md#gg-sim-001), [`GG-SCN-002`](lastenheft.md#gg-scn-002)      |
| Stabiles Tie-Breaking          | `(time, priority, source, sequence, event_id)`                                                                                                              | [`GG-ARCH-006`](lastenheft.md#gg-arch-006)                 |
| Kanonische Serialisierung      | Stabile Feldreihenfolge, festgelegte Numerik                                                                                                                | [`GG-DATA-005`](lastenheft.md#gg-data-005)                 |
| Replay-Diff                    | Fachliche vs. volatile Felder werden klassifiziert                                                                                                          | [`GG-REPLAY-007`](lastenheft.md#gg-replay-007), [`GG-SAFE-006`](lastenheft.md#gg-safe-006)  |
| Replay & Live teilen Tick-Loop | Unterschiede liegen nur in Eingabe-Adaptern                                                                                                                 | [`GG-ARCH-008`](lastenheft.md#gg-arch-008), GG-AR-P-007    |
| Parallelitaet pro Tick         | Innerhalb eines Ticks zulaessig, Commit ist deterministisch geordnet                                                                                        | [`GG-SIM-004`](lastenheft.md#gg-sim-004)                  |

Die Plattform unterscheidet **logische Tick-Dauer** (10 ms … 1 s) und
**Wall-Clock-Verhalten** (Beschleunigung `0.5x / 1x / 10x / unbounded`).
10 ms Tick ist im MVP ein Mess-/Diagnosemodus, kein garantierter
Echtzeitbetrieb (`GG-RT-001`).

---

## 10. Sicherheit und Fallback-Strategien

### 10.1 Eingabe-Sicherheit

- Externe Schnittstellen validieren Schema, Wertebereich, Zielressource
  (`GG-SAFE-008`).
- Stale-, NaN-, missing- und fault-injected-Werte werden vor
  Zustandsfortschreibung erkannt und markiert (`GG-SAFE-001..004`).
- Batteriemodell-spezifische Sicherheit (`GG-BESS-002/005`) ist in
  `hexagon/core/devices/battery` lokalisiert, nicht im Adapter.

### 10.2 Sicherer Fallback

Geraetemodelle SOLLTEN dokumentierte Fallback-Zustaende anbieten
(`GG-SAFE-005`). Auslosung, Zielzustand, Telemetrie und Recovery
gehoeren zur Modelldefinition, nicht zum Adapter.

### 10.3 Trennung Simulation vs. Produktion

UI, OpenAPI-Beschreibung und Adapterkonfiguration kennzeichnen
Simulationsadapter als nicht-produktiv (`GG-SAFE-007`,
`GG-NONGOAL-001`). Die Architektur verhindert ueber `GG-AR-TABU-003`,
dass Adapter fachliche Schreibwege an reale Anlagen oeffnen.

---

## 11. Persistenz

```text
PostgreSQL  ←  Pflicht-MVP-Speicher (GG-PERSIST-005)
   │
   ├── runs                  (RunMetadata, Schema-Version, Hash)
   ├── telemetry_points      (run_id, tick, device, metric, ...)
   ├── alarms                (run_id, target, code, severity, ...)
   ├── snapshots             (run_id, tick, payload)
   ├── replay_samples        (run_id, origin_ts, mapped_ts, ...)
   ├── scenarios             (run_id, canonical_yaml, hash)
   └── migrations            (versioniert, GG-PERSIST-008)
```

Optionale Adapter:

- **TimescaleDB** als drop-in fuer `telemetry_points` (Hypertables),
  ohne Domain-Eingriff (`GG-PERSIST-006`).
- **InfluxDB** als alternativer Telemetry-Sink mit dokumentierten
  Buckets/Tags (`GG-PERSIST-007`).

`RunRepositoryPort.delete(run_id)` entfernt alle laufbezogenen Datensaetze
atomar, ohne andere Laeufe zu beruehren (`GG-PERSIST-009`).
Erfassungszeit (`ingest_ts`) ist Betriebsmetadatum und im Replay-Diff
als volatil klassifiziert (`GG-PERSIST-007`, `GG-REPLAY-007`).

---

## 12. Konfiguration und Szenariosystem

### 12.1 Szenarioformat

Szenarien sind YAML-Dateien mit `schema_version`, `metadata`,
`simulation`, `devices`, optional `events`, `replay`, `faults`
(`GG-SCN-001`). Beispiel: das YAML-Snippet zu `GG-SCN-001..008` im Lastenheft.

### 12.2 Validierungs-Pipeline

```text
YAML
 │
 ▼  ScenarioSourcePort.read()
 │
 ▼  SchemaValidator      (GG-SCN-001/008)
 │
 ▼  ReferenceValidator   (Geraetetypen, Ziele, Einheiten)
 │
 ▼  EventValidator       (Events vor erstem Tick)         GG-SCN-005
 │
 ▼  FaultValidator       (Faults vor erstem Tick)         GG-SCN-006
 │
 ▼  ReplayLinkValidator  (Quelle/Format/Mapping pruefen)  GG-SCN-007
 │
 ▼  CanonicalSerializer  (Hash, Export)                   GG-SCN-003/004
```

Ein Szenario wird **erst nach erfolgreicher Validierung** dem Tick-Loop
uebergeben. Validierungsfehler verhindern den Lauf (`GG-SCN-008`,
`GG-BESS-008`).

### 12.3 Plattformkonfiguration

`ConfigPort` liefert technische Parameter (Ports, DSN, Healthcheck,
Telemetrie-Exporter). Geraete- und Marktparameter leben im Szenario,
nicht im Code (`GG-AR-P-013`).

---

## 13. Fault-Injection-Architektur

Faults sind erstklassige Domain-Events. Sie werden im Szenario deklariert
(`GG-SCN-006`), vor dem ersten Tick validiert, im Tick-Loop als Events
verarbeitet und in Laufmetadaten + Telemetrie persistiert
(`GG-FAULT-010`).

```text
ScenarioFaults  ──▶  FaultRegistry  ──▶  FaultRuntime  ──▶  Telemetry+Alarms
                       │                       │
                       │                       └──▶ markiert Telemetrie
                       │                            mit Qualitaetsstatus
                       │                            (stale/nan/missing/...)
                       └──▶ Replay liefert dieselben Auswirkungen
```

Fault-Typen (`comm_outage`, `stale_data`, `nan`, `freq_drop`,
`voltage_sag`, `modbus_timeout`, `device_failure`, `soc_jump`,
`network_partition`, …) sind Auspraegungen eines gemeinsamen
`Fault`-Vertrags; jedes Geraetemodell dokumentiert sein Verhalten unter
Fault.

**Produktive Surface:**

- `FaultInjectableDevice(DeviceModel)`-Sub-Protocol
  (`hexagon/core/devices/_protocol.py`) traegt die Pflicht-Surface
  `inject_fault(fault_type, payload) -> None`; Implementer setzen
  ihren eigenen State, Recovery-Tick-Counter o. ae.
- `FaultPort`-Driven-Port (`hexagon/ports/driven/fault.py`,
  `GG-AR-PORT-DRN-011`) mit `apply_active_faults(devices, context)`-
  Surface; Adapter-Boundary trennt Domain-Orchestrierung von der
  konkreten Fault-Auswahl-Logik.
- TickLoop-Pre-Tick-Hook (Schritt A2) ruft
  `fault_port.apply_active_faults(...)` nach `_consume_load_inputs_into`
  und vor der ersten `_run_device_iteration`. Exception-Propagation
  bricht den Tick atomic ab (kein Wall-Clock-Zugriff im Core).
- **Konkrete Fault-Adapter:** `BatteryFaultEngine`
  (`hexagon/core/faults/battery_fault.py`) mit `cell_failure` und
  `GridFaultEngine` (`hexagon/core/faults/grid_fault.py`) mit
  `voltage_drop`. Beide leben **nicht** unter `adapters/driven/`,
  sondern unter `hexagon/core/faults/`, weil sie Domain-
  Orchestrierung sind und kein externes Protokoll uebersetzen.
- **Recovery-Engine:** zwei Modi —
  `auto-recover-after-N-ticks` (Tick-Counter pro aktivem Fault,
  deterministisch via half-open `[start, end)`-Window) und
  `manual-via-command` (Recovery via `recover_fault(fault_id)`-
  Command analog Agent-Command-Pfad).
- Property-Tests (Hypothesis) pinnen Determinismus + Seed-
  Independence pro Fault-Sequenz; Demo-Szenario
  [`tests/integration/scenarios/fault_demo.yaml`](../tests/integration/scenarios/fault_demo.yaml)
  + Postgres-Roundtrip via `PostgresRunRepository`.

**Architektur-Erweiterungspunkte:** `permanent`-Recovery-Modus,
weitere Fault-Typen (`comm_outage`, `stale_data`, `nan`, ...) als
zusaetzliche Adapter-Implementer, Quality-Status-Markierung auf
`TelemetryPoint`-Ebene (heute Fault-Effekt ueber Device-State, nicht
ueber `Quality`-Enum). Diese Punkte bleiben Architektur-
Erweiterungen; Lieferzeitpunkt und Slice-Zuschnitt gehoeren in
Roadmap, ADR-Folgepflege oder Closure-Notizen (analog zur
§14-Klausel fuer Multi-Agent-Erweiterungen).

---

## 14. Multi-Agent-Subsystem (optional)

Agenten sind ein SOLLTE-Feature (`GG-AGENT-001`). Architektonisch sind sie
ein eigenes Kernmodul `hexagon/core/agents`, das die folgenden Verbindungen hat:

- liest ueber `ClockPort` und `TelemetryQueryPort`,
- schreibt ueber `RunControlPort`/`DeviceProtocolPort`-Mapping nur per
  `Command`-Pfad,
- nutzt einen eigenen, deterministisch sortierten `AgentMessageBus`
  (`GG-AGENT-004/008`),
- ist isoliert testbar (`GG-AGENT-002`),
- ist snapshot-/replay-faehig (`GG-AGENT-006`, `GG-AGENT-003`).

Konkurrierende Strategien (`GG-AGENT-005`) werden durch dokumentierte
Priorisierung im Agent-Modul aufgeloest, nicht im Simulationskern.

**Produktive Surface:**

- `Agent`-Sub-Protocol (`hexagon/core/agents/_protocol.py`) fixiert
  die Pflicht-Surface (`agent_id`, `set_run_id`, `tick`, `snapshot`,
  `from_snapshot`); `_RandomAttachableAgent`-Sub-Protocol traegt den
  optionalen `attach_random(...)`-Hook fuer stochastische Agenten;
  `AgentPlugin`-Sub-Protocol traegt den
  Decision-Hook fuer pluginbasierte Agenten.
- `AgentMessageBus`-Core-Klasse (`hexagon/core/agents/bus.py`)
  liefert `publish` / `drain_for` (nicht-destruktiv) /
  `consume_for` (destruktive Direct-Inbox-Drain-Variante)
  sowie Snapshot-Roundtrip.
- Registrierung erfolgt produktiv ueber den Konstruktor-Kwarg
  `TickLoop(agents=tuple[Agent, ...])` mit Auto-Bus-Regel und
  `AgentDuplicateIdError`-Fail-Fast. Der `build_
  tick_loop(...)`-Loader reicht den Kwarg symmetrisch durch
  und defaultet ihn (Sentinel-Pattern `agents=None`) auf
  `scenario.agents`.
- Command-Drain laeuft ueber Schritt A0v + A0a vor Schritt A der
  naechsten Tick (siehe §6). Agent-Commands sind also frueh im
  Folge-Tick wirksam, ohne den Scheduler oder die Device-
  Iteration zu beruehren.
- Foundation-State (`AgentMessageBus`-Buffer +
  `_pending_agent_commands`) wird als additive Sub-Snapshots
  `agent_bus` und `pending_agent_commands` in
  `TickLoop.snapshot()` / `from_snapshot(...)` persistiert (additiv,
  kein Schema-Bump).
- **Konkrete Agent-Implementer:**
  `RuleBasedAgent` (`hexagon/core/agents/rule_based.py`) mit
  Hybrid Decision-Surface — Default-Pfad ist deterministische
  Threshold-Rules-Liste (first-match-wins; Metric-Whitelist
  `tick` / `simulation_time` aus `DeviceTickContext`),
  Erweiterungs-Pfad ist optionaler `plugin`-Hook ueber
  `_AGENT_PLUGIN_FACTORIES`-Registry. Rules und Plugin
  schliessen sich gegenseitig aus.
- **`agents`-Top-Level-Block im Scenario-Schema:**
  nested Mapping `agents: {<agent_id>:
  {type, params}}` mit lexikographischer Sort-Iteration im
  Loader; `ScenarioAgent`-Domain (frozen dataclass);
  `_assert_agent_list(...)`-Validator mit Comparator-/Metric-
  Whitelist-Checks; `_build_agents(...)`-Factory-Dispatch
  analog `build_devices`.
- **Konkrete Agent-Instanz-Sub-Snapshots**
  `agents.<agent_type>.<agent_id>`
  additiv (kein Schema-Bump); bidirektionaler
  Resume-Match-Check — jeder injizierte Agent hat einen Slot
  und jeder Slot einen injizierten Agent
  (canonical_json-Equality).

**Erweiterungspunkte fuer Agenten:** Die Architektur erlaubt konkrete
`AgentPlugin`-Implementer wie `LearnedPolicy` oder `MPCController`,
Plugin-State-Restore in `RuleBasedAgent.from_snapshot`,
Priorisierung konkurrierender Agents (`GG-AGENT-005`), Deadlines
(`GG-AGENT-007`), asynchrone Agent-Ausfuehrung (`GG-AGENT-008`) und
Telemetry-Forwarding ueber eine TickLoop-Bridge oder
`TelemetryQueryPort`. Diese Punkte bleiben Architektur-Erweiterungen;
Lieferzeitpunkt und Slice-Zuschnitt gehoeren in Roadmap, ADR-Folgepflege
oder Closure-Notizen.

---

## 15. Beobachtbarkeit

| Aspekt             | Mechanismus                                                                                          | Bezug                      |
| ------------------ | ---------------------------------------------------------------------------------------------------- | -------------------------- |
| Strukturierte Logs | JSON-Logs mit `ts, level, run_id, module, event_id, message`                                         | [`GG-OTEL-002`](lastenheft.md#gg-otel-002)                |
| Metriken           | `tick_duration_ms`, `event_queue_len`, `telemetry_points_per_s`, `error_count`, `replay_diff_status` | [`GG-OTEL-003`](lastenheft.md#gg-otel-003)                |
| Traces             | OTLP-gRPC, ein Tick → Scheduler → Device → Adapter → Persistenz                                      | [`GG-OTEL-001`](lastenheft.md#gg-otel-001)/004            |
| Healthcheck        | `healthy/degraded/unhealthy` mit Ursache, Dienste separat                                            | [`GG-DEPLOY-006`](lastenheft.md#gg-deploy-006)              |
| Replay-Diff-Status | maschinenlesbarer Statuswert pro Lauf                                                                | [`GG-REPLAY-007`](lastenheft.md#gg-replay-007), [`GG-SAFE-006`](lastenheft.md#gg-safe-006) |

**Produktive Surface:**

- **Driven-Port-Trio** `LogPort` / `MetricsPort` / `TracePort`
  (`hexagon/ports/driven/observability.py`, `GG-AR-PORT-DRN-008`)
  als `@runtime_checkable` Protocols. Surface stateless, keine
  OTLP-/SDK-Typen im Port-Layer — Core bleibt OTLP-frei und
  laeuft ohne den OTLP-Stack.
- `LogEntry`-frozen-dataclass-Envelope (`level`, `message`,
  `run_id`, `module`, `event_id`, `attributes`) als Single-Object-
  Surface fuer `LogPort.log(entry)`.
- `SpanContext`-frozen-dataclass (`trace_id`, `span_id`,
  `parent_span_id`) mit `start_span` / `end_span` / `record_event`-
  Surface; `None`-No-Op-Fallback im `TracePort` fuer Adapter-
  Robustheit.
- **Null-Adapter-Trio** (`hexagon/core/observability_null/`) mit
  Default-`call_count` + `last_call`-Surface und opt-in
  `record_calls=True` fuer `call_records` + `clear_calls()`. Default-
  Verkabelung im TickLoop ist Null (kein externer Side-Effect ohne
  explizite Adapter-Injektion).
- **OTLP-Adapter-Trio** (`adapters/driven/telemetry_otlp/`):
  `OtlpLogAdapter` / `OtlpMetricsAdapter` / `OtlpTraceAdapter`
  ueber `opentelemetry-exporter-otlp-proto-grpc`-SDK (gRPC-Transport
  auf Allow-List `{"grpc"}` gepinnt; HTTP/
  protobuf ist explizit Out-of-Scope).
  `build_otlp_adapters(config)`-Factory liefert ein
  `OtlpAdapterBundle` mit den drei Adaptern + Provider-Handles +
  `flush_and_shutdown()`-Helper.
- **Additive TickLoop-Hooks** (`log_port`/`metrics_port`/`trace_port`-
  Kwargs, Default `None` skippt): `tick.cycle`-Span umfasst die
  Tick-Arbeit; `tick_begin` / `tick_end` Logs; `gauge('event_queue_
  len', ...)` nach `scheduler.pop_due`; `increment('tick_count')`
  am Tick-Ende; `fault.inject`-Span um Schritt A2 (§13);
  `agent.tick`-Span pro Agent-Tick in Schritt D2 (§14). Schritt-/
  Atomizitaets-Vertraege aus den Fault-/Agent-Sektionen bleiben
  unangetastet.
- **Keine Wall-Clock im OTLP-Adapter:** kein `time`-/`datetime`-Import
  unter `adapters/driven/telemetry_otlp/**` — Span-Dauern liefert die
  OTel-SDK ueber den Span-Lifecycle (`StartTime`/`EndTime`), keine
  Wall-Clock-Affordance im Adapter-Code.
- **Compose-Smoke-Determinismus-Pattern** mit
  vier Pflichten: per-Lauf isolierter Sink + Vorab-Truncation +
  per-Lauf eindeutige `service.instance.id` + zweischichtiges
  Flush-Protokoll (SDK-Side `force_flush()` + `shutdown()` plus
  Collector-Side kurze `batch.timeout`-Konfig + Bounded-Poll).
- **Operations-Affordance:** Collector-Internal-Telemetry auf
  `:8888/metrics` (Prometheus-Format) via `service.telemetry.
  metrics.readers.pull.exporter.prometheus` in
  `deploy/otel-collector-config.yaml`. Die Counter
  `otelcol_receiver_accepted_spans` / `_refused_spans` /
  `otelcol_exporter_sent_spans` sind die verlaessliche Diagnose-
  Quelle fuer Receiver-/Pipeline-/Exporter-Pfad-Bruchpunkte —
  `OTLPSpanExporter.force_flush()` returnt laut Python-API trivial
  `True` und ist allein kein Beweis fuer Wire-Erfolg.
- **Runbook:** [`docs/user/observability.md`](../docs/user/observability.md)
  beschreibt emittierte Spans/Metrics/Logs, lokalen Stack-Boot,
  Padding-Format-Hinweise (Debug-Exporter-Output je Signal-Typ),
  Failure-Mode-Diagnose und das Diagnose-Tooling
  [`tools/diagnose_otlp_span_export.py`](../tools/diagnose_otlp_span_export.py)
  (Matrix-Varianten + Internal-Counter-Scrape).

**Architektur-Erweiterungspunkte:** OTLP/HTTP-Transport (heute
auf gRPC gepinnt), zusaetzliche Sampler-Strategien, Trace-ID-
Determinismus per `RandomPort.sub_port("observability-trace")`,
`tick_duration_ms` als Metric (heute bewusst nicht aus dem TickLoop
emittiert, weil der Core keinen Wall-Clock-Zugriff haben darf).
Lieferzeitpunkt und Slice-Zuschnitt gehoeren in Roadmap, ADR-
Folgepflege oder Closure-Notizen (analog zur §14-Klausel).

---

## 16. Deployment-Sicht

```text
docker compose up
   │
   ├─ service: api                (REST + WS + OpenAPI)
   ├─ service: simulation         (Worker / Tick-Loop)
   ├─ service: ui                 (Web-UI)
   ├─ service: postgres           (Pflicht-Persistenz)
   ├─ service: timescaledb        (optional, GG-PERSIST-006)
   ├─ service: influxdb           (optional, GG-PERSIST-007)
   └─ service: otel-collector     (produktiv-Sibling, GG-OTEL-001)
```

Vertraege:

- Lauffaehig offline (`GG-DEPLOY-002/011`).
- Linux x86_64 ist Referenzumgebung (`GG-DEPLOY-003`).
- DevContainer ist SOLLTE (`GG-DEPLOY-004`).
- Kubernetes-Manifeste sind SOLLTE; Rolling Update, Zero-Downtime und
  Rollback sind explizit als Trigger-getriebene Folgearbeit dokumentiert
  (`GG-DEPLOY-007..010`).

API, Simulation und UI MUESSEN getrennte Healthchecks liefern; die
Topologie API/Simulation als ein Prozess oder zwei Prozesse ist offen
(siehe `GG-AR-OPEN-002`).

---

## 17. Testarchitektur

**Kennung:** `GG-AR-TEST-001` — Testarchitektur als Ganzes.

| Testart            | Verortung                                         | Bezug                                 |
| ------------------ | ------------------------------------------------- | ------------------------------------- |
| Unit Tests         | je Modul, `tests/unit/...`                        | [`GG-TESTTYPE-001`](lastenheft.md#gg-testtype-001), [`GG-TEST-006`](lastenheft.md#gg-test-006)          |
| Integration Tests  | `tests/integration/...`                           | [`GG-TESTTYPE-002`](lastenheft.md#gg-testtype-002), [`GG-TEST-007`](lastenheft.md#gg-test-007)          |
| Architekturtests   | `tests/arch/...` — erzwingt `GG-AR-TABU-001..008` | [`GG-TESTTYPE-003`](lastenheft.md#gg-testtype-003), [`GG-ARCHTEST-001`](lastenheft.md#gg-archtest-001)..005 |
| Contract Tests     | OpenAPI / WebSocket / Adapter                     | [`GG-TESTTYPE-004`](lastenheft.md#gg-testtype-004), [`GG-API-003`](lastenheft.md#gg-api-003)           |
| E2E / Demo-Abnahme | `tests/e2e/demo`                                  | [`GG-TESTTYPE-005`](lastenheft.md#gg-testtype-005), `GG-DEMO-*`            | <!-- d-check:ignore (geplant: E2E-Verzeichnis nicht angelegt; Demo-Abnahme via make accept, `GG-MVP-003`) -->
| Replay-Diff-Tests  | Golden-File-Vergleich (Referenzlauf)              | [`GG-SIM-001`](lastenheft.md#gg-sim-001), [`GG-REPLAY-007`](lastenheft.md#gg-replay-007)             |
| Fault-Tests        | scenario-driven                                   | [`GG-FAULT-001`](lastenheft.md#gg-fault-001)..010                     |
| Performance-Tests  | Referenzumgebung aus `GG-RT-001`-Akzeptanz        | [`GG-TESTTYPE-006`](lastenheft.md#gg-testtype-006), [`GG-RT-004`](lastenheft.md#gg-rt-004)/005        |
| Security-Tests     | Dependency-/Schwachstellen-Scan                   | [`GG-TESTTYPE-007`](lastenheft.md#gg-testtype-007), [`GG-CICD-005`](lastenheft.md#gg-cicd-005)/006      |

Architekturtests sind ein **Quality Gate**: Verletzungen brechen den
Build (`GG-AR-TABU-001..008`, `GG-ARCHTEST-001..005`).

---

## 18. Rueckverfolgbarkeit Architektur ↔ Lastenheft

Diese Tabelle ist die Quelle fuer die Design-Mapping-Tabelle in
`GG-TRACE-001` (Lastenheft §27.1).

| Architekturartefakt                                 | Lastenheft-Anforderung(en)                                                                                                                                                                                                                   |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GG-AR-P-001..014` Architekturprinzipien            | [`GG-ARCH-001`](lastenheft.md#gg-arch-001)..008, [`GG-PRINC-001`](lastenheft.md#gg-princ-001)..006, [`GG-CC-001`](lastenheft.md#gg-cc-001)..008 (Detail-Mapping pro `GG-PRINC-*` siehe `GG-TRACE-001` in `lastenheft.md` §27.1)                                                                                                          |
| Schichtenmodell                                     | [`GG-ARCH-001`](lastenheft.md#gg-arch-001)/002                                                                                                                                                                                                                              |
| Hexagonale Sicht (`GG-AR-P-002`)                    | [`GG-ARCH-002`](lastenheft.md#gg-arch-002)/003, [`GG-PRINC-003`](lastenheft.md#gg-princ-003)..006                                                                                                                                                                                                           |
| `GG-AR-TABU-001..008` Architektur-Tabus             | [`GG-PRINC-006`](lastenheft.md#gg-princ-006), [`GG-CC-002`](lastenheft.md#gg-cc-002)/003/004/006/007/008, [`GG-ARCHTEST-001`](lastenheft.md#gg-archtest-001)..005                                                                                                                                                                            |
| `GG-AR-PORT-DRV-001..007` Driving Ports             | [`GG-API-001`](lastenheft.md#gg-api-001)/002, [`GG-SIM-005`](lastenheft.md#gg-sim-005)/006/008, [`GG-REPLAY-001`](lastenheft.md#gg-replay-001)..007, [`GG-FAULT-001`](lastenheft.md#gg-fault-001)..010, [`GG-PERSIST-001`](lastenheft.md#gg-persist-001), [`GG-DEPLOY-006`](lastenheft.md#gg-deploy-006)                                                                                                                                     |
| `GG-AR-PORT-DRN-001..010` Driven Ports              | [`GG-ARCH-003`](lastenheft.md#gg-arch-003)/007, [`GG-DATA-001`](lastenheft.md#gg-data-001), [`GG-PERSIST-001`](lastenheft.md#gg-persist-001)/003/009, [`GG-OTEL-001`](lastenheft.md#gg-otel-001)..004, GG-MQTT/MODB/OPCUA/DNP3/IEC-001                                                                                                                                      |
| `GG-AR-COMP-*` Komponentensicht                     | [`GG-ARCH-001`](lastenheft.md#gg-arch-001)..008, [`GG-DEV-001`](lastenheft.md#gg-dev-001)..018, [`GG-BESS-001`](lastenheft.md#gg-bess-001)..008, [`GG-GRID-001`](lastenheft.md#gg-grid-001)..007, [`GG-SCN-001`](lastenheft.md#gg-scn-001)..008, [`GG-REPLAY-001`](lastenheft.md#gg-replay-001)..007, [`GG-FAULT-001`](lastenheft.md#gg-fault-001)..010, [`GG-AGENT-001`](lastenheft.md#gg-agent-001)..008, [`GG-API-001`](lastenheft.md#gg-api-001)..004, [`GG-UI-001`](lastenheft.md#gg-ui-001)..009, [`GG-PERSIST-001`](lastenheft.md#gg-persist-001)..009, [`GG-OTEL-001`](lastenheft.md#gg-otel-001)..004, [`GG-DEPLOY-001`](lastenheft.md#gg-deploy-001)..011 |
| `GG-AR-COMP-CORE` Tick-Loop / Datenfluss            | [`GG-SIM-001`](lastenheft.md#gg-sim-001)..009, [`GG-RT-001`](lastenheft.md#gg-rt-001)..006, [`GG-ARCH-005`](lastenheft.md#gg-arch-005)/006/007/008                                                                                                                                                                                     |
| `GG-AR-COMP-DOMAIN` Domain-Modell                   | [`GG-DATA-001`](lastenheft.md#gg-data-001)..005, [`GG-DEV-002`](lastenheft.md#gg-dev-002)/003, [`GG-CC-007`](lastenheft.md#gg-cc-007)                                                                                                                                                                                                  |
| `GG-AR-COMP-API` (REST + WebSocket)                 | [`GG-API-001`](lastenheft.md#gg-api-001)..004, [`GG-SAFE-008`](lastenheft.md#gg-safe-008)                                                                                                                                                                                                                 |
| Adapter-Interfaces (Driven, `GG-AR-PORT-DRN-007`)   | GG-MQTT/MODB/OPCUA/DNP3/IEC-001, [`GG-ARCH-003`](lastenheft.md#gg-arch-003)                                                                                                                                                                                                 |
| Konfiguration (`GG-AR-PORT-DRN-009`, `GG-AR-P-013`) | [`GG-PRINC-005`](lastenheft.md#gg-princ-005), GG-AR-P-013                                                                                                                                                                                                                    |
| `GG-AR-P-008` Determinismus / Zeitmodell            | [`GG-SIM-001`](lastenheft.md#gg-sim-001)..004, [`GG-ARCH-006`](lastenheft.md#gg-arch-006)/007, [`GG-REPLAY-007`](lastenheft.md#gg-replay-007), [`GG-SAFE-006`](lastenheft.md#gg-safe-006)                                                                                                                                                                                 |
| `GG-AR-P-010` Sicherer Default + Fallback           | [`GG-SAFE-001`](lastenheft.md#gg-safe-001)..008, [`GG-BESS-002`](lastenheft.md#gg-bess-002)/005                                                                                                                                                                                                            |
| `GG-AR-COMP-PERSIST` Persistenz                     | [`GG-PERSIST-001`](lastenheft.md#gg-persist-001)..009                                                                                                                                                                                                                          |
| `GG-AR-COMP-SCENARIO` Szenariosystem                | [`GG-SCN-001`](lastenheft.md#gg-scn-001)..008, [`GG-DATA-005`](lastenheft.md#gg-data-005)                                                                                                                                                                                                                 |
| `GG-AR-COMP-FAULTS` Fault-Injection                 | [`GG-FAULT-001`](lastenheft.md#gg-fault-001)..010, [`GG-SCN-006`](lastenheft.md#gg-scn-006)                                                                                                                                                                                                                |
| `GG-AR-COMP-AGENTS` Multi-Agent-Subsystem           | [`GG-AGENT-001`](lastenheft.md#gg-agent-001)..008                                                                                                                                                                                                                            |
| `GG-AR-COMP-OBS` Beobachtbarkeit                    | [`GG-OTEL-001`](lastenheft.md#gg-otel-001)..004, [`GG-DEPLOY-006`](lastenheft.md#gg-deploy-006), [`GG-REPLAY-007`](lastenheft.md#gg-replay-007)                                                                                                                                                                                               |
| `GG-AR-COMP-DEPLOY` Deployment-Sicht                | [`GG-DEPLOY-001`](lastenheft.md#gg-deploy-001)..011                                                                                                                                                                                                                           |
| `GG-AR-TEST-001` Testarchitektur                    | [`GG-TESTTYPE-001`](lastenheft.md#gg-testtype-001)..007, [`GG-ARCHTEST-001`](lastenheft.md#gg-archtest-001)..005, [`GG-TEST-001`](lastenheft.md#gg-test-001)..008                                                                                                                                                                                 |

---

## 19. Offene architektonische Punkte

| Kennung        | Frage                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Status                   |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| GG-AR-OPEN-001 | Welche Sprache und welcher Build-Stack? (Python, Go, Rust, Kotlin, .NET?) — legt Sprache und Runtime des Simulationskerns, der Adapter und der Build-Toolchain fest. Modulgrenzen aus `GG-AR-P-002` und den Tabus `GG-AR-TABU-001..008` bleiben sprachunabhaengig; betroffen sind Implementierungspakete, Querschnittsbibliotheken und Test-/Architekturtest-Tooling. **Geschlossen mit [`ADR 0002`](../docs/plan/adr/0002-language-and-build-stack.md) (`Accepted` 2026-05-15)** und der synchronen [`ADR 0005`](../docs/plan/adr/0005-type-check-gate.md) (Type-Check-Gate via `mypy --strict`). | Geschlossen (2026-05-15) |
| GG-AR-OPEN-002 | API-Service und Simulationsdienst als ein Prozess oder zwei? — Composition-Root-Entscheidung. **Geschlossen mit [`ADR 0012`](../docs/plan/adr/0012-api-simulation-two-processes.md) (`Accepted` 2026-05-17): zwei Prozesse, Postgres als Persistenz-Bus.**                                                                                                                                                                                                                                                                                                                                         | Geschlossen (2026-05-17) |
| GG-AR-OPEN-003 | Persistenzzugriff: Repository-Pattern + leichtgewichtiger Treiber, oder ORM? — **Geschlossen** mit dem produktiven `PostgresRunRepository` (`hexagon/adapters/driven/persistence_postgres/`): Repository-Pattern + `psycopg`-Treiber (kein ORM), Alembic-Migrationen, Postgres als Persistenz-Bus per [`ADR 0012`](../docs/plan/adr/0012-api-simulation-two-processes.md). Driven-Port `RunRepositoryPort` (`GG-AR-PORT-DRN-001`).                                                                                                                                                                                                                                                                                                                                                                                  | Geschlossen (2026-05-17) |
| GG-AR-OPEN-004 | Wird der `AgentMessageBus` als In-Process-Bus oder als Adapter (z. B. NATS) implementiert? — **Geschlossen** mit [`ADR 0023`](../docs/plan/adr/0023-agent-bus-protocol.md) (`Accepted`): In-Process-Bus als Core-Klasse `AgentMessageBus` (`hexagon/core/agents/bus.py`), kein Driven-Port. Architektur §14 schreibt eigenes Kernmodul vor; der Bus hat keine externe Adapter-Boundary.                                                                                                                                                                                                                                                                                                                                                                                                                          | Geschlossen (2026-05-21) |
| GG-AR-OPEN-005 | Replay-Diff-Klassifikation: Liste fachlich vs. volatil als Konfiguration oder hartcodiert?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Offen                    |
| GG-AR-OPEN-006 | Snapshot-Format: einheitlich JSON-kanonisch, binaer, oder hybrid?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Offen                    |
| GG-AR-OPEN-007 | UI-Architektur: SSR vs. SPA; eigene REST-Konsumentenschicht oder direkte WebSocket-Anbindung?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Offen                    |
| GG-AR-OPEN-008 | OpenTelemetry-Pflicht ab welcher Reifestufe? Heute SOLLTE (`GG-OTEL-001`) — **Geschlossen** mit [`ADR 0024`](../docs/plan/adr/0024-observability-port-trio.md) (`Accepted`): Port-Trio `LogPort`/`MetricsPort`/`TracePort` ist Pflicht-Surface (Default-Verkabelung Null-Adapter, keine externer Side-Effekt ohne explizite Injektion). OTLP-Adapter-Trio (`adapters/driven/telemetry_otlp/`) ist produktiv; `otel-collector`-Sibling in `deploy/compose.yml` und Compose-Smoke-Determinismus-Pattern fixiert. `GG-OTEL-001` bleibt formal SOLLTE — die Architektur stellt die Pflicht-Surface, die Adapter-Wahl ist Deployment-Entscheidung.                                                                                                                                                                                                                                                  | Geschlossen (2026-05-25) |
| GG-AR-OPEN-009 | Welche Protokolladapter sind ab MVP enthalten? Heute alle SOLLTE (`GG-MQTT/MODB/OPCUA/DNP3/IEC-001`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Offen                    |
| GG-AR-OPEN-010 | Authentifizierung der API — heute nicht im Lastenheft normiert; spaetere `GG-SAFE-…`-Erweiterung                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Offen                    |

Geschlossene Punkte erhalten einen Verweis auf ein ADR-Dokument unter
[`docs/plan/adr/`](../docs/plan/adr/). Die Dokumentations- und
Planungsstruktur ist in
[`ADR 0001`](../docs/plan/adr/0001-documentation-and-planning-structure.md)
festgelegt.

---

## 20. Zusammenfassung

`grid-gym` ist als geschichtetes, hexagonales System konzipiert. Der
deterministische Tick-Loop ist die invariante Spine; Geraetemodelle,
Szenarien, Replay, Faults und Agenten sind austauschbar daran angedockt.
Die wichtigste Architekturregel bleibt:

```text
Die Simulation entscheidet, was passiert.
Adapter uebersetzen nur Protokolle, Formate und technische Fehler.
```

Diese Trennung wird durch klare Schichten, einheitliche interne Modelle
(`Telemetry`, `Command`, `Event`, `Quality`, `Snapshot`), einen zentralen
`ClockPort` und durch per Architekturtest erzwungene Modulgrenzen
getragen.

---

## Historie

Entscheidungs-Provenance (SDP Regel 5: Body vs. Changelog). Der Body oben
traegt die zeitlose Architektur-Festlegung; diese Sektion bindet jede
Surface/Komponente an die ADR, die sie spezifiziert. Sie ist vom
Referenzrichtungs-Gate (`matrix`) ausgenommen.

| Surface / Komponente | ADR |
| --- | --- |
| Sprach-/Build-Wahl, Domain-/No-Wall-Clock-Contracts (`AC-DOMAIN-FROZEN`, `AC-NO-TIME`, `AC-OTLP-ADAPTER-NO-TIME`) | [`ADR 0002`](../docs/plan/adr/0002-language-and-build-stack.md) §6.1 / §A-1 |
| Kennungs-Querverweis-Konvention | [`ADR 0004`](../docs/plan/adr/0004-identifier-based-cross-references.md) |
| `RandomPort` — PRNG-Wahl + Seeding-Kette | [`ADR 0007`](../docs/plan/adr/0007-random-port.md) |
| `SnapshotEnvelope` — additive Sub-Snapshots | [`ADR 0015`](../docs/plan/adr/0015-snapshot-envelope-v2.md) §2.3 |
| `grid_model.update(...)` — Netz-Bilanz | [`ADR 0019`](../docs/plan/adr/0019-grid-model-bilanz-pattern.md) §2.2 |
| Scenario-Loader + Tick-Loop-Wiring (LoadEvent/Auto-Schluss) | [`ADR 0021`](../docs/plan/adr/0021-scenario-loader-and-tick-loop-event-wiring.md) §2.5/§2.7 |
| `FaultPort` / `FaultInjectableDevice` / Pre-Tick-Hook | [`ADR 0022`](../docs/plan/adr/0022-fault-injection-protocol.md) §2.1/§2.4–§2.5 |
| Fault-Recovery-Engine (`auto-recover` / `manual-via-command`) | [`ADR 0025`](../docs/plan/adr/0025-fault-recovery-pattern.md) |
| `AgentMessageBus` — deterministischer In-Memory-Bus | [`ADR 0023`](../docs/plan/adr/0023-agent-bus-protocol.md) §2.2/§3 |
| Agent-Drain-Registry + Lifecycle-Hook | [`ADR 0026`](../docs/plan/adr/0026-agent-drain-registry-pattern.md) |
| `RuleBasedAgent` + `agents`-Scenario-Block | [`ADR 0027`](../docs/plan/adr/0027-rule-based-agent-scenario-pattern.md) |
| `DeviceProtocolPort` — Sync-Surface + Lifecycle | [`ADR 0030`](../docs/plan/adr/0030-device-protocol-port-surface.md) §2.1–2.4 |
| Observability-Port-Trio (`LogPort`/`MetricsPort`/`TracePort`) + OTLP | [`ADR 0024`](../docs/plan/adr/0024-observability-port-trio.md) |

Der **Status** der Architektur (gelieferte Meilensteine, Wellen-Stand) und
die ADR-Lifecycle-Stati leben in
[`roadmap.md`](../docs/plan/planning/in-progress/roadmap.md) und den
`M*-results.md`-Closure-Notizen, nicht in diesem zeitlosen Dokument.
