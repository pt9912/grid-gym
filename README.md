# grid-gym

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

Dieses Repository befindet sich in einer fruehen Spezifikationsphase. Aktuell
enthaelt es das Lastenheft, diese Projektuebersicht und Basis-Metadaten. Eine
lauffaehige Implementierung ist noch nicht enthalten.

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
├── CHANGELOG.md
├── Dockerfile                   ← Multi-Stage (Lint, Arch-Check, Test, Runtime)
├── LICENSE
├── Makefile                     ← Build-/Test-Gates pro Dockerfile-Stage
├── README.md
├── spec/
│   ├── lastenheft.md            ← normative Anforderungen (GG-*)
│   └── architecture.md          ← Architektur (GG-AR-*)
└── docs/
    ├── plan/
    │   ├── adr/                 ← Architecture Decision Records
    │   └── planning/
    │       ├── open/            ← Trigger-Watch, offene Folgearbeiten
    │       ├── next/            ← geplant, aber noch nicht aktiv
    │       ├── in-progress/     ← aktive Roadmap und Slice-Plaene
    │       └── done/            ← Closure-Notizen
    ├── user/                    ← anwender-/betreibernah (geplant)
    └── archive/                 ← verworfene/historische Skizzen
```

Quelltext, Tests und Tooling-Skripte (`src/grid_gym/`, `tests/`,
`tools/`) werden im Rahmen von Spike-0 zu ADR 0002 (`GG-AR-OPEN-001`)
angelegt; `Dockerfile` und `Makefile` sind das Geruest dafuer.

Die Dokumentations- und Planungsstruktur ist in
[`docs/plan/adr/0001-documentation-and-planning-structure.md`](docs/plan/adr/0001-documentation-and-planning-structure.md)
festgelegt.

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Details stehen in [`LICENSE`](LICENSE).
