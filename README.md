# grid-gym

`grid-gym` ist eine geplante modulare Plattform zur deterministischen Simulation,
Validierung und Analyse elektrischer Energiesysteme.

Der Fokus liegt auf reproduzierbaren Replay-Simulationen, Fault Injection,
Echtzeit-Telemetrie und Integrationstests fuer EMS- und Smart-Grid-Anwendungen.
Das Projekt richtet sich an Entwickler, Forschungseinrichtungen und
Systemintegratoren, die testbare Energiesystem-Szenarien ohne proprietaere
Werkzeuge modellieren wollen.

## Status

Dieses Repository befindet sich in einer fruehen Spezifikationsphase. Aktuell
enthaelt es das Lastenheft und diese Projektuebersicht; eine lauffaehige
Implementierung ist noch nicht enthalten.

## Geplante Funktionen

- Deterministischer Simulationskern mit diskreten Zeitschritten
- Replay- und beschleunigte Simulationsmodi
- Austauschbare Modelle fuer Batteriespeicher, PV-Anlagen, Lastprofile,
  Netzanschlusspunkte und Smart Meter
- Fault Injection fuer Kommunikations-, Sensor- und Geraetefehler
- Agentenbasierte Steuerung fuer EMS-, MPC-, RL- und Demand-Response-Szenarien
- Telemetrie-Export fuer Analyse, Monitoring und Integrationstests
- Adapter fuer Integrationen wie MQTT, Modbus TCP und containerbasierte
  Testumgebungen

## Projektstruktur

```text
.
├── README.md
└── spec/
    └── lastenheft.md
```

## Spezifikation

Die fachlichen und technischen Anforderungen sind im Lastenheft dokumentiert:

- [`spec/lastenheft.md`](spec/lastenheft.md)

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Details stehen in [`LICENSE`](LICENSE).
