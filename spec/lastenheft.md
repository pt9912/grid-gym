# Lastenheft - grid-gym

Version: 0.4  
Status: Draft  
Projekt: `grid-gym`

---

# 1. Zielsetzung

`grid-gym` ist eine modulare Open-Source-Plattform zur Simulation,
Validierung und Analyse elektrischer Energiesysteme.

Die Plattform dient der Entwicklung, Evaluierung und Validierung von:

- Energy-Management-Strategien, ohne selbst ein produktives EMS zu sein
- Multi-Agent-Energiesystemen
- Netzregelalgorithmen
- Batteriespeicherstrategien
- Smart-Grid-Regelungen
- Replay- und HIL-Testsystemen
- MPC- und RL-Regelungen
- Demand-Response-Systemen

Der Fokus liegt auf:

- deterministischer Ausfuehrung
- reproduzierbaren Ergebnissen
- Replaybarkeit
- Fault Injection
- simulierter Echtzeitfaehigkeit
- Integrationsfaehigkeit fuer Test- und Forschungsumgebungen
- agentenbasierter Steuerung

---

# 2. Normative Begriffe und Abnahme

## GG-TERM-001

Die Begriffe MUSS, DARF NICHT, SOLLTE und KANN sind normativ zu verstehen:

- MUSS: verpflichtend fuer den MVP-Abnahmestand
- DARF NICHT: verboten fuer den MVP-Abnahmestand
- SOLLTE: geplant, aber nicht blockierend fuer MVP-Abnahme
- KANN: optionale Erweiterung ohne Abnahmeverpflichtung

Akzeptanz: Ein Requirement gilt nur dann als erfuellt, wenn ein automatisierter
Test, ein reproduzierbarer manueller Test oder ein dokumentierter
Architekturentscheid die Erfuellung nachweist.

## GG-TERM-002

Determinismus bedeutet: Bei gleicher Version, gleicher Plattformarchitektur,
gleichen Eingabedaten, gleicher Szenario-Datei, gleicher Konfiguration und
gleichem Seed erzeugt ein Simulationslauf dieselben fachlichen Ausgaben in
derselben Tick-Reihenfolge.

Akzeptanz: Zwei Laeufe desselben Referenzszenarios erzeugen byte-identische
kanonische Ergebnisdateien oder einen leeren Replay-Diff.

## GG-TERM-003

Reproduzierbarkeit bedeutet: Ein Simulationslauf speichert alle zur
Wiederholung notwendigen Metadaten, mindestens Version, Szenario-Hash,
Konfiguration, Startzeit im Simulationszeitmodell, Seed, Tick-Groesse und
aktivierte Adapter.

Akzeptanz: Ein exportierter Lauf kann ohne externe Live-Daten erneut ausgefuehrt
werden und liefert dieselben fachlichen Ausgaben.

## GG-TERM-004

Echtzeitfaehigkeit bedeutet in diesem Lastenheft simulierte Echtzeit fuer lokale
Test- und Demo-Umgebungen. Sie ist keine Garantie fuer harte industrielle
Real-Time-Anforderungen.

Akzeptanz: Die Plattform dokumentiert Tick-Dauer, Jitter-Messung und
Backpressure-Verhalten fuer die Demo-Konfiguration.

## GG-TERM-005

MVP bezeichnet den ersten abnahmefaehigen Stand der Plattform. Der MVP umfasst
nur Anforderungen mit MUSS-Status sowie die Demo- und Testartefakte, die zur
Abnahme dieser MUSS-Anforderungen notwendig sind.

Akzeptanz: Das Repository enthaelt eine Requirements-Matrix, die jedes
MUSS-Requirement einem Test, einer Demo-Funktion oder einem Architekturentscheid
zuordnet.

## GG-TERM-006

Fachliche Ausgaben sind kanonisch serialisierte Simulationsergebnisse ohne
volatile Laufzeitfelder wie Wall-Clock-Zeit, Prozess-ID, zufaellige UUIDs oder
Hostnamen.

Akzeptanz: Der Replay-Diff ignoriert ausschliesslich dokumentierte volatile
Felder und meldet jede fachliche Abweichung.

---

# 3. MVP-Abnahmescope

## GG-MVP-001

Der MVP MUSS einen lokalen Single-Node-Betrieb bereitstellen.

Akzeptanz: API, UI, Simulationskern, Persistenz und Demo-Szenario laufen auf
einem Entwicklerrechner ueber Docker Compose.

## GG-MVP-002

Der MVP MUSS mindestens ein End-to-End-Szenario mit Netzanschlusspunkt, PV,
Lastprofil, Smart Meter und Batteriespeicher enthalten.

Akzeptanz: Das Szenario startet ueber API, erzeugt Live-Telemetrie, persistiert
Zeitreihen und laesst sich deterministisch replayen.

## GG-MVP-003

Der MVP MUSS eine CLI oder ein Script fuer Abnahmepruefungen bereitstellen.

Akzeptanz: Ein einzelner Befehl fuehrt deterministische Replay-Pruefung,
Szenario-Validierung und Demo-Healthcheck aus und liefert einen maschinenlesbaren
Status.

## GG-MVP-004

Der MVP DARF NICHT verlangen, dass externe Cloud-Dienste, reale Feldgeraete oder
Internet-Zugriff zur Laufzeit verfuegbar sind.

Akzeptanz: Nach Bereitstellung der Container-Images ist die Demo offline
ausfuehrbar.

---

# 4. Nicht-Ziele und Scope-Grenzen

## GG-NONGOAL-001

Die Plattform ist KEIN produktives EMS.

Abgrenzung: Steuerstrategien duerfen simuliert, getestet und verglichen werden.
Die Plattform DARF NICHT als verbindliche Steuerinstanz fuer reale Anlagen ohne
separate Produktfreigabe, Security-Hardening und Betreiberabnahme beschrieben
oder ausgeliefert werden.

## GG-NONGOAL-002

Die Plattform ist KEIN vollstaendiges SCADA-System.

Abgrenzung: UI, Alarme und Kommunikationsadapter dienen Simulation,
Testautomatisierung und Demo-Zwecken. Nicht im Scope sind Benutzerverwaltung mit
Rollenmodell, Audit-Trail fuer Betrieb, Leitsystem-Redundanz, Leitwartenbetrieb
und produktive Prozessfuehrung.

## GG-NONGOAL-003

Die Plattform ist KEIN Cloud-SaaS.

Abgrenzung: Lokaler Betrieb und Container-basierte Entwicklung sind im Scope.
Mandantenfaehiger Cloud-Betrieb, Billing, Account-Lifecycle und gehostete
Service-Level sind nicht im Scope.

## GG-NONGOAL-004

Die Plattform ist KEIN Home-Automation-System.

Abgrenzung: Smart-Home-Protokolle und Consumer-Automation-Workflows sind nur im
Scope, wenn sie fuer ein Energie-Simulationsszenario als Adapter benoetigt
werden.

## GG-NONGOAL-005

Die Plattform ist KEIN proprietaeres Digital-Twin-System.

Abgrenzung: Geraete- und Netzmodelle muessen offen austauschbar sein. Proprietare
Modellformate koennen importiert werden, duerfen aber kein Pflichtbestandteil
des Kernsystems sein.

---

# 5. Architektur

## GG-ARCH-001

Die Plattform MUSS modular aufgebaut sein.

Akzeptanz: Simulationskern, Geraetemodelle, Szenario-/Replay-System,
Kommunikationsadapter, Persistenz und UI sind als getrennte Module oder Pakete
mit expliziten Schnittstellen dokumentiert.

## GG-ARCH-002

Die Plattform MUSS Hexagonal Architecture fuer den Simulationskern verwenden.

Akzeptanz: Der Simulationskern definiert Ports fuer Zeitquelle, Eingaben,
Ausgaben, Persistenz und Telemetrie. Adapter implementieren diese Ports und
werden nicht aus der Domain-Logik heraus direkt instanziiert.

## GG-ARCH-003

Die Simulationslogik DARF NICHT direkt an Kommunikationsadapter gekoppelt sein.

Akzeptanz: Der Simulationskern importiert keine REST-, WebSocket-, MQTT-,
Modbus-, OPC-UA-, DNP3- oder IEC61850-Adapterpakete.

## GG-ARCH-004

Geraetemodelle MUESSEN austauschbar sein.

Akzeptanz: Ein Szenario kann zwischen mindestens zwei Implementierungen eines
Geraetetyps wechseln, ohne den Simulationskern zu aendern.

## GG-ARCH-005

Die Plattform MUSS Event-basierte Kommunikation innerhalb der Simulation
unterstuetzen.

Akzeptanz: Ereignisse werden ueber einen internen Event-Typ mit Simulationszeit,
Quelle, Ziel, Typ, Payload und Sequenznummer verarbeitet.

## GG-ARCH-006

Die Plattform MUSS einen deterministischen Event Scheduler bereitstellen.

Akzeptanz: Ereignisse mit gleichem Zeitstempel werden stabil nach Prioritaet,
Quelle, Sequenznummer und Event-ID sortiert. Diese Tie-Breaking-Regeln sind
dokumentiert und getestet.

## GG-ARCH-007

Zeitmodellierung MUSS zentralisiert erfolgen.

Akzeptanz: Fachlogik liest Simulationszeit nur ueber den zentralen Clock-Port und
verwendet keine Systemzeit fuer fachliche Entscheidungen.

## GG-ARCH-008

Replay und Live-Simulation MUESSEN dieselbe Simulationspipeline verwenden.

Akzeptanz: Replay- und Live-Laeufe benutzen denselben Tick-Prozessor und dieselbe
Geraetemodell-API. Unterschiede liegen nur in den Eingabe-Adaptern.

---

# 6. Simulationskern

## GG-SIM-001

Der Simulationskern MUSS deterministische Simulationen unterstuetzen.

Akzeptanz: Das Referenzszenario `demo/basic-grid` erzeugt in zwei Laeufen mit
gleichem Seed identische kanonische Ergebnisdateien.

## GG-SIM-002

Der Simulationskern MUSS diskrete Zeitschritte unterstuetzen.

Akzeptanz: Szenarien koennen Tick-Groessen von 10 ms, 100 ms und 1 s konfigurieren.

## GG-SIM-003

Der Simulationskern MUSS reproduzierbare Ergebnisse liefern.

Akzeptanz: Jeder Lauf exportiert Metadaten gemaess GG-TERM-003.

## GG-SIM-004

Der Simulationskern MUSS parallele Geraete simulieren koennen, ohne fachlichen
Nichtdeterminismus einzufuehren.

Akzeptanz: Parallele Berechnung darf nur innerhalb eines Ticks erfolgen; das
Commit der Ergebnisse erfolgt in deterministischer Reihenfolge.

## GG-SIM-005

Der Simulationskern MUSS Snapshot-basierte Zustaende unterstuetzen.

Akzeptanz: Ein Lauf kann nach einem Snapshot fortgesetzt werden und liefert ab
dem Snapshot dieselben Ergebniswerte wie ein ununterbrochener Lauf.

## GG-SIM-006

Der Simulationskern MUSS Replay-Simulation unterstuetzen.

Akzeptanz: Historische Zeitreihen koennen als Eingabequelle fuer denselben
Tick-Prozessor verwendet werden.

## GG-SIM-007

Der Simulationskern MUSS beschleunigte Simulation unterstuetzen.

Akzeptanz: Ein Szenario kann ohne Wall-Clock-Warten so schnell wie moeglich
ausgefuehrt werden.

## GG-SIM-008

Der Simulationskern MUSS Pause/Resume unterstuetzen.

Akzeptanz: Ein pausierter Lauf verarbeitet keine weiteren Ticks, bis Resume
ausgeloest wird.

## GG-SIM-009

Simulationslaeufe SOLLTEN exportierbar sein.

Akzeptanz: Export umfasst mindestens Metadaten, Szenario-Hash, Telemetrie und
Alarme in einem dokumentierten Format.

---

# 7. Echtzeit und Zeitmodell

Referenzumgebung fuer Performance-Akzeptanz:

- Linux x86_64
- 4 CPU-Kerne
- 8 GB RAM
- lokale Container-Umgebung
- Demo-Szenario ohne externe Netzwerkdienste ausser den im Compose-Stack
  enthaltenen Diensten

## GG-RT-001

Die Plattform MUSS Simulationszyklen von 10 ms bis 1 s konfigurieren koennen.

Akzeptanz: Die Demo-Konfiguration startet erfolgreich mit 10 ms, 100 ms und 1 s
Tick-Groesse.

## GG-RT-002

Tick-Verarbeitung MUSS deterministisch erfolgen.

Akzeptanz: Die Tick-Reihenfolge wird in der Ergebnisdatei protokolliert und ist
zwischen zwei identischen Laeufen gleich.

## GG-RT-003

Veraltete Daten MUESSEN markiert werden.

Akzeptanz: Ein Eingangswert gilt als stale, wenn sein Simulationszeitstempel
aelter ist als die konfigurierte `max_age` des Datenpunkts.

## GG-RT-004

Die Plattform SOLLTE mindestens 100 simulierte Geraete in der Referenzumgebung
unterstuetzen.

Akzeptanz: Ein Benchmark-Szenario mit 100 Geraeten verarbeitet 10.000 Ticks ohne
verlorene Events und ohne nichtdeterministischen Replay-Diff.

## GG-RT-005

Die Plattform SOLLTE mindestens 10.000 Zeitreihenpunkte/s in der
Referenzumgebung verarbeiten koennen.

Akzeptanz: Gemessen wird am Telemetrie-Port mit Payloads bis 256 Byte je Punkt;
Persistenz darf gepuffert erfolgen.

## GG-RT-006

Replay-Modi MUESSEN Zeitmultiplikatoren unterstuetzen.

Akzeptanz: Replay-Faktoren `0.5x`, `1x`, `10x` und `unbounded` sind
konfigurierbar.

---

# 8. Datenmodell, Einheiten und Qualitaet

## GG-DATA-001

Die Plattform MUSS ein einheitliches Telemetrie-Datenmodell verwenden.

Akzeptanz: Jeder Telemetriepunkt enthaelt `run_id`, `tick`, `simulation_time`,
`device_id`, `metric`, `value`, `unit`, `quality`, `source` und `sequence`.

## GG-DATA-002

Die Plattform MUSS SI-nahe Einheiten und explizite Einheitenfelder verwenden.

Akzeptanz: Leistung wird in `kW`, Energie in `kWh`, Frequenz in `Hz`, Spannung in
`V`, Strom in `A`, Temperatur in `degC`, Zeit in `ms` oder `s` und SOC in `pct`
ausgegeben.

## GG-DATA-003

Die Plattform MUSS Datenqualitaet standardisiert markieren.

Akzeptanz: Der Qualitaetsstatus unterstuetzt mindestens `valid`, `stale`,
`estimated`, `limited`, `invalid`, `nan`, `missing` und `fault_injected`.

## GG-DATA-004

Die Plattform MUSS Kommandoergebnisse standardisiert markieren.

Akzeptanz: Jeder Steuerbefehl endet in genau einem Status aus `accepted`,
`rejected`, `limited`, `expired`, `failed` oder `ignored`.

## GG-DATA-005

Die Plattform MUSS kanonische Serialisierung fuer Vergleich und Replay
bereitstellen.

Akzeptanz: JSON-Ausgaben verwenden stabile Feldreihenfolge, stabile Sortierung,
explizite Dezimalpraezision und keine nichtdeterministischen IDs.

---

# 9. Geraetemodelle

## GG-DEV-001

Geraete MUESSEN ueber gemeinsame Schnittstellen abstrahiert werden.

Akzeptanz: Jedes Geraetemodell implementiert mindestens `initialize`, `tick`,
`apply_command`, `snapshot` und `telemetry`.

## GG-DEV-002

Geraete MUESSEN Telemetrie exportieren koennen.

Akzeptanz: Jeder Telemetriepunkt enthaelt Simulationszeit, Geraete-ID, Metrikname,
Wert, Einheit und Qualitaetsstatus.

## GG-DEV-003

Geraete SOLLTEN Steuerbefehle akzeptieren koennen.

Akzeptanz: Steuerbefehle enthalten Command-ID, Simulationszeit, Zielgeraet,
Befehlstyp, Payload und Validierungsstatus.

## 9.1 Unterstuetzte Geraete

### GG-DEV-010

Die Plattform MUSS Batteriespeicher simulieren koennen.

### GG-DEV-011

Die Plattform MUSS PV-Anlagen simulieren koennen.

### GG-DEV-012

Die Plattform MUSS Netzanschlusspunkte simulieren koennen.

### GG-DEV-013

Die Plattform MUSS Lastprofile simulieren koennen.

### GG-DEV-014

Die Plattform MUSS Smart Meter simulieren koennen.

### GG-DEV-015

Die Plattform SOLLTE EV-Ladepunkte simulieren koennen.

### GG-DEV-016

Die Plattform SOLLTE Transformatoren simulieren koennen.

### GG-DEV-017

Die Plattform SOLLTE Windkraftanlagen simulieren koennen.

### GG-DEV-018

Die Plattform SOLLTE Dieselgeneratoren simulieren koennen.

Akzeptanz fuer GG-DEV-010 bis GG-DEV-018: Jeder unterstuetzte Geraetetyp hat ein
Minimalmodell, ein Beispiel im Szenarioformat und einen deterministischen
Smoke-Test.

---

# 10. Batteriemodell

## GG-BESS-001

Das Batteriemodell MUSS SOC simulieren.

Akzeptanz: SOC wird in Prozent und als Energieinhalt in kWh gefuehrt. Die
Fortschreibung erfolgt tick-basiert aus Leistung, Tick-Dauer, Kapazitaet und
konfiguriertem Wirkungsgrad.

## GG-BESS-002

Das Batteriemodell MUSS Lade- und Entladegrenzen beruecksichtigen.

Akzeptanz: Befehle ausserhalb `max_charge_kw`, `max_discharge_kw`, `min_soc_pct`
und `max_soc_pct` werden begrenzt oder abgelehnt und als Alarm markiert.

## GG-BESS-003

Das Batteriemodell MUSS Wirkungsgrade beruecksichtigen.

Akzeptanz: Lade- und Entlade-Wirkungsgrad sind getrennt konfigurierbar und
wirken auf die SOC-Fortschreibung.

## GG-BESS-004

Das Batteriemodell MUSS Ramp-Limits unterstuetzen.

Akzeptanz: Leistungswechsel werden pro Tick durch `ramp_kw_per_s` begrenzt.

## GG-BESS-005

Das Batteriemodell MUSS Sicherheitsgrenzen validieren.

Akzeptanz: Unzulaessige SOC-, Leistungs-, Temperatur- oder Spannungswerte werden
nicht ungeprueft in den naechsten Tick uebernommen.

## GG-BESS-006

Das Batteriemodell SOLLTE Temperaturzustaende simulieren koennen.

Akzeptanz: Temperatur kann als vereinfachtes thermisches Zustandsmodell oder als
eingespeiste Zeitreihe abgebildet werden.

## GG-BESS-007

Das Batteriemodell SOLLTE Zellspannungsabweichungen simulieren koennen.

Akzeptanz: Zellspannungsabweichungen koennen als aggregierte Metrik
`cell_voltage_delta_v` exportiert werden.

## GG-BESS-008

Das Batteriemodell MUSS Initialparameter validieren.

Akzeptanz: Kapazitaet, SOC-Grenzen, Initial-SOC, Leistungsgrenzen,
Wirkungsgrade und Ramp-Limits werden vor Simulationsstart validiert; ungueltige
Konfigurationen verhindern den Start des Szenarios.

---

# 11. Netzmodell

## GG-GRID-001

Die Plattform MUSS Frequenzabweichungen simulieren koennen.

Akzeptanz: Das MVP enthaelt mindestens ein vereinfachtes Leistungsbilanzmodell,
das Frequenzabweichungen aus Erzeugung, Last und Speicherleistung ableitet.
Das Modell dokumentiert Annahmen, Grenzen und Parametrisierung.

## GG-GRID-002

Die Plattform MUSS Spannungsabweichungen simulieren koennen.

Akzeptanz: Das MVP enthaelt mindestens ein vereinfachtes Spannungsmodell je
Netzanschlusspunkt. Das Modell muss kenntlich machen, ob es ein vereinfachtes
Ersatzmodell oder einen Power-Flow-Adapter verwendet.

## GG-GRID-003

Die Plattform MUSS Netzlasten simulieren koennen.

Akzeptanz: Lasten koennen als konstante Werte, Zeitreihen oder Szenario-Events
definiert werden.

## GG-GRID-004

Die Plattform MUSS Lastspitzen simulieren koennen.

Akzeptanz: Szenarien koennen Lastspruenge mit Startzeit, Dauer und Leistung
definieren.

## GG-GRID-005

Die Plattform SOLLTE Inselnetzmodi unterstuetzen.

## GG-GRID-006

Die Plattform SOLLTE Transformatorgrenzen simulieren koennen.

## GG-GRID-007

Die Plattform SOLLTE Blindleistungsfluesse simulieren koennen.

Akzeptanz fuer GG-GRID-005 bis GG-GRID-007: Die jeweilige Funktion ist ueber ein
eigenes Modell aktivierbar und erzeugt dokumentierte Telemetrie.

---

# 12. Szenariosystem

## GG-SCN-001

Die Plattform MUSS YAML-basierte Szenarien mit Schema-Version unterstuetzen.

Akzeptanz: Szenariodateien enthalten `schema_version`, `metadata`,
`simulation`, `devices` und optional `events`, `replay` und `faults`.

## GG-SCN-002

Szenarien MUESSEN deterministisch ausfuehrbar sein.

Akzeptanz: Das Szenarioformat erlaubt keine nichtdeterministische Systemzeit und
keine impliziten Zufallsquellen ohne Seed.

## GG-SCN-003

Szenarien MUESSEN versionierbar sein.

Akzeptanz: Schema-Version und Szenario-Hash werden bei jedem Lauf exportiert.

## GG-SCN-004

Szenarien MUESSEN exportierbar sein.

Akzeptanz: Ein geladenes Szenario kann kanonisch serialisiert werden.

## GG-SCN-005

Szenarien SOLLTEN zeitbasierte Ereignisse unterstuetzen.

## GG-SCN-006

Szenarien SOLLTEN Fault Injection unterstuetzen.

## GG-SCN-007

Szenarien SOLLTEN Replay-Verweise unterstuetzen.

## GG-SCN-008

Die Plattform MUSS Szenarien vor Ausfuehrung validieren.

Akzeptanz: Schemafehler, unbekannte Geraetetypen, doppelte IDs, ungueltige
Einheiten, fehlende Pflichtfelder und Events auf unbekannte Ziele werden vor dem
ersten Tick als Validierungsfehler gemeldet.

## 12.1 Beispiel

```yaml
schema_version: "grid-gym.scenario.v1"
metadata:
  id: "demo-basic-grid"
  name: "Basic grid demo"
simulation:
  tick_ms: 100
  duration_s: 60
  seed: 42
devices:
  - id: "grid-1"
    type: "grid_connection"
    params:
      nominal_frequency_hz: 50.0
  - id: "pv-1"
    type: "pv"
    params:
      rated_power_kw: 1500
  - id: "load-1"
    type: "load"
    params:
      power_kw: 800
  - id: "battery-1"
    type: "battery"
    params:
      capacity_kwh: 1000
      initial_soc_pct: 50
      max_charge_kw: 500
      max_discharge_kw: 500
events:
  - at_s: 10
    target: "pv-1"
    command: "set_power_kw"
    value: 1200
  - at_s: 15
    target: "load-1"
    command: "set_power_kw"
    value: 1800
  - at_s: 20
    target: "battery-1"
    command: "set_mode"
    value: "discharge"
```

---

# 13. Replay-System

## GG-REPLAY-001

Die Plattform MUSS historische Zeitreihen importieren koennen.

Akzeptanz: CSV und JSON Lines werden fuer MVP unterstuetzt; jedes Sample enthaelt
Zeitstempel, Geraete-ID, Metrikname, Wert und Einheit.

## GG-REPLAY-002

Replay-Systeme MUESSEN Originalzeitstempel unterstuetzen.

Akzeptanz: Originalzeitstempel werden unveraendert gespeichert und auf
Simulationszeit abgebildet.

## GG-REPLAY-003

Replay-Systeme MUESSEN deterministisch ausfuehrbar sein.

Akzeptanz: Samples mit gleichem Zeitstempel werden stabil nach Quelle, Metrik und
Import-Reihenfolge sortiert.

## GG-REPLAY-004

Replay-Systeme SOLLTEN beschleunigte Wiedergabe unterstuetzen.

## GG-REPLAY-005

Replay-Systeme SOLLTEN Pause/Resume unterstuetzen.

## GG-REPLAY-006

Replay-Systeme SOLLTEN Delta-Analysen ermoeglichen.

Akzeptanz fuer GG-REPLAY-004 bis GG-REPLAY-006: Die Funktion ist ueber API und CLI
ausloesbar und erzeugt einen dokumentierten Status.

## GG-REPLAY-007

Replay-Diffs MUESSEN fachliche und volatile Felder unterscheiden.

Akzeptanz: Diff-Ausgaben enthalten Pfad, erwarteten Wert, tatsaechlichen Wert,
Tick, Geraete-ID und Klassifikation der Abweichung.

---

# 14. Fault Injection

## GG-FAULT-001

Die Plattform MUSS Kommunikationsausfaelle simulieren koennen.

## GG-FAULT-002

Die Plattform MUSS Stale Data simulieren koennen.

## GG-FAULT-003

Die Plattform MUSS NaN-Werte simulieren koennen.

## GG-FAULT-004

Die Plattform MUSS Frequenzabfaelle simulieren koennen.

## GG-FAULT-005

Die Plattform MUSS Spannungseinbrueche simulieren koennen.

## GG-FAULT-006

Die Plattform MUSS Modbus-Timeouts simulieren koennen.

## GG-FAULT-007

Die Plattform MUSS Geraeteausfaelle simulieren koennen.

## GG-FAULT-008

Die Plattform SOLLTE SOC-Spruenge simulieren koennen.

## GG-FAULT-009

Die Plattform SOLLTE Netzwerkpartitionen simulieren koennen.

Akzeptanz fuer GG-FAULT-001 bis GG-FAULT-009: Jeder Fault-Typ kann im Szenario mit
Startzeit, Dauer, Ziel, Intensitaet und Recovery-Verhalten definiert werden und
erzeugt Telemetrie sowie einen Alarm.

## GG-FAULT-010

Fault Injection MUSS deterministisch replaybar sein.

Akzeptanz: Faults werden als Events mit Simulationszeit und Sequenznummer in den
Laufmetadaten protokolliert und erzeugen bei Replay dieselben fachlichen
Auswirkungen.

---

# 15. Multi-Agent-System

## GG-AGENT-001

Die Plattform SOLLTE agentenbasierte Steuerungsmodelle unterstuetzen.

## GG-AGENT-002

Agenten SOLLTEN isoliert testbar sein.

## GG-AGENT-003

Agenten SOLLTEN deterministisch replaybar sein.

## GG-AGENT-004

Agenten SOLLTEN standardisierte Nachrichten verwenden.

## GG-AGENT-005

Die Plattform SOLLTE konkurrierende Regelstrategien unterstuetzen.

## GG-AGENT-006

Agenten SOLLTEN lokale Zustaende verwalten koennen.

## GG-AGENT-007

Agenten SOLLTEN Zeitrestriktionen unterstuetzen.

## GG-AGENT-008

Agenten SOLLTEN asynchron kommunizieren koennen.

Akzeptanz: Agentenkommunikation wird ueber deterministisch sortierte Nachrichten
mit Simulationszeit, Sender, Empfaenger, Nachrichtentyp, Payload und Sequenznummer
abgebildet. Asynchrone Verarbeitung darf die Commit-Reihenfolge eines Ticks nicht
veraendern.

---

# 16. Kommunikationsschnittstellen

## GG-API-001

Die Plattform MUSS REST-Schnittstellen fuer Test- und Demo-Steuerung
bereitstellen.

Akzeptanz: REST bietet Endpunkte fuer Szenario-Start, Pause, Resume, Stop,
Status, Snapshot und Fault Injection.

## GG-API-002

Die Plattform MUSS WebSocket-Telemetrie fuer Live-Ansichten unterstuetzen.

Akzeptanz: WebSocket-Nachrichten enthalten Lauf-ID, Simulationszeit,
Sequenznummer und Telemetrie-Payload.

## GG-API-003

Die Plattform MUSS einen maschinenlesbaren API-Vertrag bereitstellen.

Akzeptanz: REST-Endpunkte sind per OpenAPI dokumentiert; Request- und
Response-Schemas enthalten Fehlerformate und Statuscodes.

## GG-API-004

Die Plattform MUSS API-Fehler standardisiert ausgeben.

Akzeptanz: Fehlerantworten enthalten `code`, `message`, `details`, `run_id`
falls vorhanden und einen stabilen HTTP-Status.

## GG-MQTT-001

Die Plattform MUSS MQTT als Simulationsadapter unterstuetzen.

## GG-MODB-001

Die Plattform MUSS Modbus TCP als Simulationsadapter unterstuetzen.

## GG-OPCUA-001

Die Plattform SOLLTE OPC-UA als Simulationsadapter unterstuetzen.

## GG-DNP3-001

Die Plattform SOLLTE DNP3 als Simulationsadapter unterstuetzen.

## GG-IEC-001

Die Plattform SOLLTE IEC61850 als Simulationsadapter unterstuetzen.

Akzeptanz fuer Protokolladapter: Adapter muessen klar als Simulations- und
Testadapter dokumentiert sein und duerfen keine produktive Anlagensteuerung
versprechen.

---

# 17. Visualisierung

## GG-UI-001

Die Plattform MUSS ein Web-UI fuer lokale Demo- und Testumgebungen bereitstellen.

## GG-UI-002

Das UI MUSS Live-Telemetrie visualisieren koennen.

## GG-UI-003

Das UI MUSS Zeitreihen visualisieren koennen.

## GG-UI-004

Das UI MUSS Replay-Steuerung unterstuetzen.

## GG-UI-005

Das UI MUSS Alarme visualisieren koennen.

## GG-UI-006

Das UI SOLLTE Geraete grafisch darstellen koennen.

## GG-UI-007

Das UI SOLLTE Fault Injection ausloesen koennen.

## GG-UI-008

Das UI SOLLTE Simulationszustaende visualisieren koennen.

Akzeptanz: Das MVP-UI zeigt mindestens Laufstatus, aktuelle Simulationszeit,
Geraeteliste, Live-Telemetrie, Alarmtabelle und Replay-Steuerung.

## GG-UI-009

Das UI MUSS Datenqualitaet sichtbar machen.

Akzeptanz: Telemetriepunkte mit `stale`, `invalid`, `nan`, `missing` oder
`fault_injected` werden in Tabellen und Zeitreihen unterscheidbar dargestellt.

---

# 18. Persistenz

## GG-PERSIST-001

Die Plattform MUSS Zeitreihen speichern koennen.

## GG-PERSIST-002

Die Plattform MUSS Replay-Daten speichern koennen.

## GG-PERSIST-003

Die Plattform MUSS Szenariodaten speichern koennen.

## GG-PERSIST-004

Die Plattform MUSS Alarmhistorien speichern koennen.

## GG-PERSIST-005

Die Plattform MUSS PostgreSQL unterstuetzen.

## GG-PERSIST-006

Die Plattform SOLLTE TimescaleDB unterstuetzen.

## GG-PERSIST-007

Die Plattform SOLLTE InfluxDB unterstuetzen.

Akzeptanz: Persistierte Datensaetze enthalten Lauf-ID, Simulationszeit,
Erfassungszeit, Quelle, Payload und Schema-Version. PostgreSQL ist der
verpflichtende MVP-Speicher; TimescaleDB und InfluxDB sind optionale Adapter.

## GG-PERSIST-008

Die Plattform MUSS Datenbankmigrationen versionieren.

Akzeptanz: Schemaaenderungen sind migrationsbasiert nachvollziehbar und koennen
in einer leeren lokalen Datenbank reproduzierbar angewendet werden.

## GG-PERSIST-009

Die Plattform MUSS Laufdaten eindeutig loeschen koennen.

Akzeptanz: Ein Lauf kann inklusive Telemetrie, Alarme, Snapshots und Metadaten
ueber eine dokumentierte Operation entfernt werden, ohne andere Laeufe zu
veraendern.

---

# 19. Telemetrie

## GG-OTEL-001

Die Plattform MUSS OpenTelemetry fuer Traces und Metriken unterstuetzen.

Akzeptanz: Die Demo exportiert OTLP-kompatible Traces und Metriken oder stellt
einen konfigurierbaren OTLP-Exporter bereit.

## GG-OTEL-002

Die Plattform MUSS strukturierte Logs unterstuetzen.

Akzeptanz: Logs enthalten Zeitstempel, Level, Lauf-ID, Modul, Event-ID und
Nachricht.

## GG-OTEL-003

Die Plattform MUSS Metriken exportieren koennen.

Akzeptanz: Exportiert werden mindestens Tick-Dauer, Event-Queue-Laenge,
verarbeitete Telemetriepunkte/s, Fehleranzahl und Replay-Diff-Status.

## GG-OTEL-004

Die Plattform MUSS Traces exportieren koennen.

Akzeptanz: Ein Tick kann ueber Scheduler, Geraetemodell, Adapter und Persistenz
tracebar sein.

---

# 20. Sicherheitsanforderungen

## GG-SAFE-001

Ungueltige Daten MUESSEN erkannt werden.

## GG-SAFE-002

NaN-Werte DUERFEN NICHT ungeprueft verarbeitet werden.

## GG-SAFE-003

Kommunikationsausfaelle MUESSEN erkannt werden.

## GG-SAFE-004

Veraltete Daten MUESSEN markiert werden.

## GG-SAFE-005

Die Plattform SOLLTE sichere Fallback-Zustaende unterstuetzen.

## GG-SAFE-006

Nichtdeterministische Simulationslaeufe SOLLTEN erkannt werden.

Akzeptanz: Validierungsfehler, NaN-Werte, stale Daten und Kommunikationsausfaelle
erzeugen einen Qualitaetsstatus und mindestens einen Alarm. Fallback-Zustaende
werden pro Geraetetyp dokumentiert.

## GG-SAFE-007

Die Plattform MUSS Simulations- und Produktivkontexte klar trennen.

Akzeptanz: UI, API-Dokumentation und Adapterkonfiguration kennzeichnen
Simulationsadapter als nicht fuer produktive Anlagensteuerung freigegeben.

## GG-SAFE-008

Die Plattform MUSS Eingaben an externen Schnittstellen validieren.

Akzeptanz: REST-, WebSocket-, MQTT- und Modbus-Eingaben werden gegen Schema,
Wertebereiche und Zielressourcen validiert, bevor sie in den Simulationskern
gelangen.

---

# 21. Testbarkeit

## GG-TEST-001

Die Plattform MUSS Replay-basierte Tests unterstuetzen.

## GG-TEST-002

Die Plattform MUSS deterministische Tests unterstuetzen.

## GG-TEST-003

Die Plattform MUSS Integrationstests unterstuetzen.

## GG-TEST-004

Die Plattform SOLLTE HIL-Tests unterstuetzen.

## GG-TEST-005

Die Plattform SOLLTE Property-basierte Tests unterstuetzen.

## GG-TEST-006

Replay-Diffs SOLLTEN automatisiert vergleichbar sein.

Akzeptanz: Der CI-Testumfang enthaelt mindestens Unit-Tests fuer
Geraetemodelle, deterministische Replay-Tests fuer das Referenzszenario und
Integrationstests fuer API, Persistenz und Telemetrie.

## GG-TEST-007

Die Plattform MUSS eine Requirements-Matrix fuer MUSS-Anforderungen pflegen.

Akzeptanz: Jede MUSS-Anforderung verweist auf mindestens einen Test,
Architekturentscheid oder eine Demo-Abnahmepruefung.

## GG-TEST-008

Die Plattform MUSS Golden-Files fuer deterministische Referenzszenarien
unterstuetzen.

Akzeptanz: Golden-Files werden kanonisch erzeugt und koennen in CI gegen neue
Simulationsergebnisse verglichen werden.

---

# 22. Deployment

## GG-DEPLOY-001

Die Plattform MUSS Docker Compose unterstuetzen.

## GG-DEPLOY-002

Die Plattform MUSS offline lokal lauffaehig sein, nachdem Images und
Abhaengigkeiten bereitgestellt wurden.

## GG-DEPLOY-003

Die Plattform MUSS Linux-basiert deploybar sein.

## GG-DEPLOY-004

Die Plattform SOLLTE DevContainer unterstuetzen.

## GG-DEPLOY-005

Eine vollstaendige Demo MUSS mit folgendem Kommando startbar sein:

```bash
docker compose up
```

Akzeptanz: Nach erfolgreichem Start sind API, UI, Persistenz und Demo-Simulation
lokal erreichbar und der Systemstatus meldet `healthy`.

## GG-DEPLOY-006

Die Plattform MUSS Healthchecks fuer lokale Dienste bereitstellen.

Akzeptanz: API, UI, Datenbank und Simulationsdienst melden `healthy`,
`degraded` oder `unhealthy` mit kurzer Ursache.

---

# 23. Demo-System

## GG-DEMO-001

Die Plattform MUSS eine Demo-Umgebung bereitstellen.

## GG-DEMO-002

Die Demo MUSS ein simuliertes Netz enthalten.

## GG-DEMO-003

Die Demo MUSS eine simulierte Batterie enthalten.

## GG-DEMO-004

Die Demo MUSS Live-Telemetrie enthalten.

## GG-DEMO-005

Die Demo MUSS mindestens ein Replay-Szenario enthalten.

## GG-DEMO-006

Die Demo SOLLTE Fault Injection enthalten.

## GG-DEMO-007

Die Demo SOLLTE mindestens einen Agenten enthalten.

Akzeptanz: Die Demo kann ohne externe Dienste gestartet werden und erzeugt nach
spaetestens 30 s sichtbare Telemetrie, mindestens einen exportierbaren Lauf und
einen reproduzierbaren Replay-Test.

## GG-DEMO-008

Die Demo MUSS eine klare Abnahmereihenfolge dokumentieren.

Akzeptanz: Die Dokumentation beschreibt Start, Healthcheck, Szenarioausfuehrung,
Fault Injection, Replay und Export in reproduzierbaren Schritten.

---

# 24. Abnahmeartefakte

## GG-ACCEPT-001

Die Plattform MUSS eine Abnahmedokumentation fuer den MVP bereitstellen.

Akzeptanz: Die Dokumentation listet Umgebung, Startkommandos, erwartete
Ergebnisse, bekannte Einschraenkungen und Verweise auf Tests.

## GG-ACCEPT-002

Die Plattform MUSS bekannte Modellgrenzen dokumentieren.

Akzeptanz: Batterie-, PV-, Last- und Netzmodelle nennen Annahmen,
Gueltigkeitsbereich und bewusst nicht modellierte Effekte.

## GG-ACCEPT-003

Die Plattform MUSS Beispielartefakte fuer einen erfolgreichen Demo-Lauf
bereitstellen.

Akzeptanz: Beispielartefakte umfassen Laufmetadaten, Telemetrieexport,
Alarmexport, Replay-Diff und Healthcheck-Ausgabe.

---

# 25. Roadmap, keine MVP-Anforderungen

Die folgenden Punkte sind Zukunftserweiterungen. Sie sind nicht normativ fuer die
MVP-Abnahme und duerfen nicht als `MUSS`- oder `SOLLTE`-Scope interpretiert
werden, solange sie nicht in einen vorherigen Abschnitt verschoben werden.

## GG-FUTURE-001

Die Plattform KANN MPC-Regelung unterstuetzen.

## GG-FUTURE-002

Die Plattform KANN RL-/ML-Agenten unterstuetzen.

## GG-FUTURE-003

Die Plattform KANN pandapower integrieren.

## GG-FUTURE-004

Die Plattform KANN verteilte Simulation unterstuetzen.

## GG-FUTURE-005

Die Plattform KANN GPU-basierte Simulation unterstuetzen.

## GG-FUTURE-006

Die Plattform KANN Co-Simulation unterstuetzen.

---
