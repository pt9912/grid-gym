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
├── LICENSE
├── README.md
└── spec/
    └── lastenheft.md
```

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Details stehen in [`LICENSE`](LICENSE).
