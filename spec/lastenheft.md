# Lastenheft - grid-gym

**Projektname:** grid-gym
**Dokumenttyp:** Lastenheft
**Format:** Markdown
**Version:** 0.8
**Status:** Draft

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
- perspektivisch MPC- und RL-Regelungen
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

- MUSS: verpflichtend fuer den jeweils zugeordneten Abnahmestand
- DARF NICHT: verboten fuer den jeweils zugeordneten Abnahmestand
- SOLLTE: geplant, aber nicht blockierend fuer den jeweiligen Abnahmestand
- KANN: optionale Erweiterung ohne Abnahmeverpflichtung

MVP-blockierend sind nur Anforderungen, die in Kapitel 3 explizit dem
MVP-Abnahmescope zugeordnet sind, in ihrer Formulierung den MVP nennen oder in
der Requirements-Matrix als `mvp` klassifiziert werden.

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
die in Kapitel 3 definierten Anforderungen, explizit als MVP gekennzeichnete
Anforderungen sowie die Demo-, Test- und Abnahmeartefakte, die zur Abnahme
dieser Anforderungen notwendig sind. Weitere MUSS-Anforderungen beschreiben
verpflichtende Anforderungen fuer spaetere Abnahmestaende, sofern sie nicht in
der Requirements-Matrix dem MVP zugeordnet sind. SOLLTE- und
KANN-Anforderungen duerfen implementiert sein, sind aber nicht
abnahmeblockierend.

Akzeptanz: Das Repository enthaelt eine Requirements-Matrix, die jedes
Requirement einer Abnahmestufe, einem Status und mindestens einem Test, einer
Demo-Funktion oder einem Architekturentscheid zuordnet.

## GG-TERM-006

Fachliche Ausgaben sind kanonisch serialisierte Simulationsergebnisse ohne
volatile Laufzeitfelder wie Wall-Clock-Zeit, Prozess-ID, zufaellige UUIDs oder
Hostnamen. Float-Werte werden fuer Vergleichsartefakte auf eine dokumentierte
Dezimalpraezision gerundet; NaN-, Inf- und fehlende Werte werden als
dokumentierte Qualitaetszustaende serialisiert.

Akzeptanz: Der Replay-Diff ignoriert ausschliesslich dokumentierte volatile
Felder und meldet jede fachliche Abweichung.

---

# 3. MVP-Abnahmescope

## GG-MVP-001 Lokaler Single-Node-Betrieb
<a id="gg-mvp-001"></a>

Der MVP MUSS einen lokalen Single-Node-Betrieb bereitstellen.

Akzeptanz: API, UI, Simulationskern, Persistenz und Demo-Szenario laufen auf
einem Entwicklerrechner ueber Docker Compose.

## GG-MVP-002 End-to-End-Referenzszenario
<a id="gg-mvp-002"></a>

Der MVP MUSS mindestens ein End-to-End-Szenario mit Netzanschlusspunkt, PV,
Lastprofil, Smart Meter und Batteriespeicher enthalten.

Akzeptanz: Das Szenario startet ueber API, erzeugt Live-Telemetrie, persistiert
Zeitreihen und laesst sich deterministisch replayen.

## GG-MVP-003 Abnahme-CLI/-Script
<a id="gg-mvp-003"></a>

Der MVP MUSS eine CLI oder ein Script fuer Abnahmepruefungen bereitstellen.

Akzeptanz: Ein einzelner Befehl fuehrt deterministische Replay-Pruefung,
Szenario-Validierung und Demo-Healthcheck aus und liefert einen maschinenlesbaren
Status.

## GG-MVP-004 Keine externe Abhaengigkeit (MVP)
<a id="gg-mvp-004"></a>

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

## GG-ARCH-001 Modularer Aufbau
<a id="gg-arch-001"></a>

Die Plattform MUSS modular aufgebaut sein.

Akzeptanz: Simulationskern, Geraetemodelle, Szenario-/Replay-System,
Kommunikationsadapter, Persistenz und UI sind als getrennte Module oder Pakete
mit expliziten Schnittstellen dokumentiert.

## GG-ARCH-002 Hexagonale Kern-Architektur
<a id="gg-arch-002"></a>

Die Plattform MUSS Hexagonal Architecture fuer den Simulationskern verwenden.

Akzeptanz: Der Simulationskern definiert Ports fuer Zeitquelle, Eingaben,
Ausgaben, Persistenz und Telemetrie. Adapter implementieren diese Ports und
werden nicht aus der Domain-Logik heraus direkt instanziiert.

## GG-ARCH-003 Adapter-entkoppelte Simulationslogik
<a id="gg-arch-003"></a>

Die Simulationslogik DARF NICHT direkt an Kommunikationsadapter gekoppelt sein.

Akzeptanz: Der Simulationskern importiert keine REST-, WebSocket-, MQTT-,
Modbus-, OPC-UA-, DNP3- oder IEC61850-Adapterpakete.

## GG-ARCH-004 Austauschbare Geraetemodelle
<a id="gg-arch-004"></a>

Geraetemodelle MUESSEN austauschbar sein.

Akzeptanz: Ein Szenario kann fuer mindestens einen Geraetetyp zwischen zwei
Implementierungen wechseln, ohne den Simulationskern zu aendern. Fuer den MVP
darf eine der Implementierungen eine dokumentierte Test- oder Minimalvariante
sein; es ist nicht erforderlich, jeden MVP-Geraetetyp doppelt zu implementieren.

## GG-ARCH-005 Event-basierte Kommunikation
<a id="gg-arch-005"></a>

Die Plattform MUSS Event-basierte Kommunikation innerhalb der Simulation
unterstuetzen.

Akzeptanz: Ereignisse werden ueber einen internen Event-Typ mit Simulationszeit,
Quelle, Ziel, Typ, Payload und Sequenznummer verarbeitet.

## GG-ARCH-006 Deterministischer Event-Scheduler
<a id="gg-arch-006"></a>

Die Plattform MUSS einen deterministischen Event Scheduler bereitstellen.

Akzeptanz: Ereignisse mit gleichem Zeitstempel werden stabil nach Prioritaet,
Quelle, Sequenznummer und Event-ID sortiert. Diese Tie-Breaking-Regeln sind
dokumentiert und getestet.

## GG-ARCH-007 Zentralisierte Zeitmodellierung
<a id="gg-arch-007"></a>

Zeitmodellierung MUSS zentralisiert erfolgen.

Akzeptanz: Fachlogik liest Simulationszeit nur ueber den zentralen Clock-Port und
verwendet keine Systemzeit fuer fachliche Entscheidungen.

## GG-ARCH-008 Geteilte Replay/Live-Pipeline
<a id="gg-arch-008"></a>

Replay und Live-Simulation MUESSEN dieselbe Simulationspipeline verwenden.

Akzeptanz: Replay- und Live-Laeufe benutzen denselben Tick-Prozessor und dieselbe
Geraetemodell-API. Unterschiede liegen nur in den Eingabe-Adaptern.

---

# 6. Simulationskern

## GG-SIM-001 Deterministische Simulation
<a id="gg-sim-001"></a>

Der Simulationskern MUSS deterministische Simulationen unterstuetzen.

Akzeptanz: Das Referenzszenario `demo/basic-grid` erzeugt in zwei Laeufen mit
gleichem Seed identische kanonische Ergebnisdateien.

## GG-SIM-002 Diskrete Zeitschritte
<a id="gg-sim-002"></a>

Der Simulationskern MUSS diskrete Zeitschritte unterstuetzen.

Akzeptanz: Szenarien koennen Tick-Groessen von 10 ms, 100 ms und 1 s konfigurieren.

## GG-SIM-003 Reproduzierbare Ergebnisse
<a id="gg-sim-003"></a>

Der Simulationskern MUSS reproduzierbare Ergebnisse liefern.

Akzeptanz: Jeder Lauf exportiert Metadaten gemaess GG-TERM-003.

## GG-SIM-004 Parallele Geraete-Simulation
<a id="gg-sim-004"></a>

Der Simulationskern MUSS parallele Geraete simulieren koennen, ohne fachlichen
Nichtdeterminismus einzufuehren.

Akzeptanz: Parallele Berechnung darf nur innerhalb eines Ticks erfolgen; das
Commit der Ergebnisse erfolgt in deterministischer Reihenfolge.

## GG-SIM-005 Snapshot-Zustaende
<a id="gg-sim-005"></a>

Der Simulationskern MUSS Snapshot-basierte Zustaende unterstuetzen.

Akzeptanz: Ein Lauf kann nach einem Snapshot fortgesetzt werden und liefert ab
dem Snapshot dieselben Ergebniswerte wie ein ununterbrochener Lauf.

## GG-SIM-006 Replay-Simulation
<a id="gg-sim-006"></a>

Der Simulationskern MUSS Replay-Simulation unterstuetzen.

Akzeptanz: Historische Zeitreihen koennen als Eingabequelle fuer denselben
Tick-Prozessor verwendet werden.

## GG-SIM-007 Beschleunigte Simulation
<a id="gg-sim-007"></a>

Der Simulationskern MUSS beschleunigte Simulation unterstuetzen.

Akzeptanz: Ein Szenario kann ohne Wall-Clock-Warten so schnell wie moeglich
ausgefuehrt werden.

## GG-SIM-008 Pause/Resume
<a id="gg-sim-008"></a>

Der Simulationskern MUSS Pause/Resume unterstuetzen.

Akzeptanz: Ein pausierter Lauf verarbeitet keine weiteren Ticks, bis Resume
ausgeloest wird.

## GG-SIM-009 Exportierbare Simulationslaeufe
<a id="gg-sim-009"></a>

Simulationslaeufe MUESSEN exportierbar sein.

Akzeptanz: Export umfasst mindestens Metadaten, Szenario-Hash, Telemetrie und
Alarme in einem dokumentierten Format. Fuer MVP-Referenzlaeufe muss der Export
alle Daten enthalten, die fuer deterministisches Replay und Golden-File-Vergleich
notwendig sind.

---

# 7. Echtzeit und Zeitmodell

Referenzumgebung fuer Performance-Akzeptanz:

- Linux x86_64
- 4 CPU-Kerne
- 8 GB RAM
- lokale Container-Umgebung
- Demo-Szenario ohne externe Netzwerkdienste ausser den im Compose-Stack
  enthaltenen Diensten

## GG-RT-001 Konfigurierbare Simulationszyklen
<a id="gg-rt-001"></a>

Die Plattform MUSS Simulationszyklen von 10 ms bis 1 s konfigurieren koennen.

Akzeptanz: Die Demo-Konfiguration startet erfolgreich mit 10 ms, 100 ms und 1 s
Tick-Groesse. Fuer 100 ms und 1 s Tick-Groesse verarbeitet die Demo 1.000 Ticks
ohne Backpressure. Fuer 10 ms Tick-Groesse dokumentiert der Healthcheck
Tick-Dauer, p95-Jitter, verpasste Ticks und Backpressure-Status; 10 ms ist fuer
den MVP ein Mess- und Diagnosemodus, kein garantierter Echtzeitbetrieb.

## GG-RT-002 Deterministische Tick-Verarbeitung
<a id="gg-rt-002"></a>

Tick-Verarbeitung MUSS deterministisch erfolgen.

Akzeptanz: Die Tick-Reihenfolge wird in der Ergebnisdatei protokolliert und ist
zwischen zwei identischen Laeufen gleich.

## GG-RT-003 Stale-Markierung veralteter Daten
<a id="gg-rt-003"></a>

Veraltete Daten MUESSEN markiert werden.

Akzeptanz: Ein Eingangswert gilt als stale, wenn sein Simulationszeitstempel
aelter ist als die konfigurierte `max_age` des Datenpunkts.

## GG-RT-004 Skalierung auf 100 Geraete
<a id="gg-rt-004"></a>

Die Plattform SOLLTE mindestens 100 simulierte Geraete in der Referenzumgebung
unterstuetzen.

Akzeptanz: Ein Benchmark-Szenario mit 100 Geraeten verarbeitet 10.000 Ticks ohne
verlorene Events und ohne nichtdeterministischen Replay-Diff.

## GG-RT-005 Durchsatz 10.000 Zeitreihenpunkte/s
<a id="gg-rt-005"></a>

Die Plattform SOLLTE mindestens 10.000 Zeitreihenpunkte/s in der
Referenzumgebung verarbeiten koennen.

Akzeptanz: Gemessen wird am Telemetrie-Port mit Payloads bis 256 Byte je Punkt;
Persistenz darf gepuffert erfolgen.

## GG-RT-006 Replay-Zeitmultiplikatoren
<a id="gg-rt-006"></a>

Replay-Modi MUESSEN Zeitmultiplikatoren unterstuetzen.

Akzeptanz: Replay-Faktoren `0.5x`, `1x`, `10x` und `unbounded` sind
konfigurierbar.

---

# 8. Datenmodell, Einheiten und Qualitaet

## GG-DATA-001 Einheitliches Telemetrie-Datenmodell
<a id="gg-data-001"></a>

Die Plattform MUSS ein einheitliches Telemetrie-Datenmodell verwenden.

Akzeptanz: Jeder Telemetriepunkt enthaelt `run_id`, `tick`, `simulation_time`,
`device_id`, `metric`, `value`, `unit`, `quality`, `source` und `sequence`.

## GG-DATA-002 Explizite SI-Einheiten
<a id="gg-data-002"></a>

Die Plattform MUSS SI-nahe Einheiten und explizite Einheitenfelder verwenden.

Akzeptanz: Leistung wird in `kW`, Energie in `kWh`, Frequenz in `Hz`, Spannung in
`V`, Strom in `A`, Temperatur in `degC`, Zeit in `ms` oder `s` und SOC in `pct`
ausgegeben.

## GG-DATA-003 Standardisierte Datenqualitaet
<a id="gg-data-003"></a>

Die Plattform MUSS Datenqualitaet standardisiert markieren.

Akzeptanz: Der Qualitaetsstatus unterstuetzt mindestens `valid`, `stale`,
`estimated`, `limited`, `invalid`, `nan`, `missing` und `fault_injected`.

## GG-DATA-004 Standardisierte Kommandoergebnisse
<a id="gg-data-004"></a>

Die Plattform MUSS Kommandoergebnisse standardisiert markieren.

Akzeptanz: Jeder Steuerbefehl endet in genau einem Status aus `accepted`,
`rejected`, `limited`, `expired`, `failed` oder `ignored`.

## GG-DATA-005 Kanonische Serialisierung
<a id="gg-data-005"></a>

Die Plattform MUSS kanonische Serialisierung fuer Vergleich und Replay
bereitstellen.

Akzeptanz: JSON-Ausgaben verwenden stabile Feldreihenfolge, stabile Sortierung,
explizite Dezimalpraezision und keine nichtdeterministischen IDs. Fuer den MVP
werden Zeitstempel als ISO-8601-UTC oder als ganzzahlige Simulationszeit in ms,
Sequenzen als Integer und Messwerte mit maximal sechs Nachkommastellen
kanonisiert.

---

# 9. Geraetemodelle

## GG-DEV-001 Abstrahierte Geraeteschnittstellen
<a id="gg-dev-001"></a>

Geraete MUESSEN ueber gemeinsame Schnittstellen abstrahiert werden.

Akzeptanz: Jedes Geraetemodell implementiert mindestens `initialize`, `tick`,
`apply_command`, `snapshot` und `telemetry`.

## GG-DEV-002 Geraete-Telemetrie-Export
<a id="gg-dev-002"></a>

Geraete MUESSEN Telemetrie exportieren koennen.

Akzeptanz: Jeder Telemetriepunkt enthaelt Simulationszeit, Geraete-ID, Metrikname,
Wert, Einheit und Qualitaetsstatus.

## GG-DEV-003 Geraete-Steuerbefehle
<a id="gg-dev-003"></a>

Geraete SOLLTEN Steuerbefehle akzeptieren koennen.

Akzeptanz: Steuerbefehle enthalten Command-ID, Simulationszeit, Zielgeraet,
Befehlstyp, Payload und Validierungsstatus.

## 9.1 Unterstuetzte Geraete

### GG-DEV-010 Batteriespeicher-Simulation
<a id="gg-dev-010"></a>

Die Plattform MUSS Batteriespeicher simulieren koennen.

Akzeptanz: Der Geraetetyp `battery` hat ein Minimalmodell, ein Beispiel im
Szenarioformat und einen deterministischen Smoke-Test.

### GG-DEV-011 PV-Anlagen-Simulation
<a id="gg-dev-011"></a>

Die Plattform MUSS PV-Anlagen simulieren koennen.

Akzeptanz: Der Geraetetyp `pv` hat ein Minimalmodell, ein Beispiel im
Szenarioformat und einen deterministischen Smoke-Test.

### GG-DEV-012 Netzanschlusspunkt-Simulation
<a id="gg-dev-012"></a>

Die Plattform MUSS Netzanschlusspunkte simulieren koennen.

Akzeptanz: Der Geraetetyp `grid_connection` hat ein Minimalmodell, ein Beispiel
im Szenarioformat und einen deterministischen Smoke-Test.

### GG-DEV-013 Lastprofil-Simulation
<a id="gg-dev-013"></a>

Die Plattform MUSS Lastprofile simulieren koennen.

Akzeptanz: Der Geraetetyp `load` hat ein Minimalmodell, ein Beispiel im
Szenarioformat und einen deterministischen Smoke-Test.

### GG-DEV-014 Smart-Meter-Simulation
<a id="gg-dev-014"></a>

Die Plattform MUSS Smart Meter simulieren koennen.

Akzeptanz: Der Geraetetyp `smart_meter` hat ein Minimalmodell, ein Beispiel im
Szenarioformat und einen deterministischen Smoke-Test.

### GG-DEV-015 EV-Ladepunkt-Simulation
<a id="gg-dev-015"></a>

Die Plattform SOLLTE EV-Ladepunkte simulieren koennen.

Akzeptanz: Wenn der Geraetetyp `ev_charger` implementiert wird, hat er ein
Minimalmodell, ein Beispiel im Szenarioformat und einen deterministischen
Smoke-Test.

### GG-DEV-016 Transformator-Simulation
<a id="gg-dev-016"></a>

Die Plattform SOLLTE Transformatoren simulieren koennen.

Akzeptanz: Wenn der Geraetetyp `transformer` implementiert wird, hat er ein
Minimalmodell, ein Beispiel im Szenarioformat und einen deterministischen
Smoke-Test.

### GG-DEV-017 Windkraft-Simulation
<a id="gg-dev-017"></a>

Die Plattform SOLLTE Windkraftanlagen simulieren koennen.

Akzeptanz: Wenn der Geraetetyp `wind_turbine` implementiert wird, hat er ein
Minimalmodell, ein Beispiel im Szenarioformat und einen deterministischen
Smoke-Test.

### GG-DEV-018 Dieselgenerator-Simulation
<a id="gg-dev-018"></a>

Die Plattform SOLLTE Dieselgeneratoren simulieren koennen.

Akzeptanz: Wenn der Geraetetyp `diesel_generator` implementiert wird, hat er ein
Minimalmodell, ein Beispiel im Szenarioformat und einen deterministischen
Smoke-Test.

---

# 10. Batteriemodell

## GG-BESS-001 SOC-Simulation
<a id="gg-bess-001"></a>

Das Batteriemodell MUSS SOC simulieren.

Akzeptanz: SOC wird in Prozent und als Energieinhalt in kWh gefuehrt. Die
Fortschreibung erfolgt tick-basiert aus Leistung, Tick-Dauer, Kapazitaet und
konfiguriertem Wirkungsgrad.

## GG-BESS-002 Lade-/Entladegrenzen
<a id="gg-bess-002"></a>

Das Batteriemodell MUSS Lade- und Entladegrenzen beruecksichtigen.

Akzeptanz: Befehle ausserhalb `max_charge_kw`, `max_discharge_kw`, `min_soc_pct`
und `max_soc_pct` werden deterministisch behandelt: Leistungsbefehle innerhalb
der SOC-Grenzen werden auf die zulaessige Leistung begrenzt und erhalten den
Status `limited`; Befehle, die eine SOC-Grenze verletzen wuerden, werden
abgelehnt und erhalten den Status `rejected`. In beiden Faellen wird ein Alarm
mit Zielgeraet, Grenzwert und resultierendem Status erzeugt.

## GG-BESS-003 Wirkungsgrade
<a id="gg-bess-003"></a>

Das Batteriemodell MUSS Wirkungsgrade beruecksichtigen.

Akzeptanz: Lade- und Entlade-Wirkungsgrad sind getrennt konfigurierbar und
wirken auf die SOC-Fortschreibung.

## GG-BESS-004 Ramp-Limits
<a id="gg-bess-004"></a>

Das Batteriemodell MUSS Ramp-Limits unterstuetzen.

Akzeptanz: Leistungswechsel werden pro Tick durch `ramp_kw_per_s` begrenzt.

## GG-BESS-005 Sicherheitsgrenzen-Validierung
<a id="gg-bess-005"></a>

Das Batteriemodell MUSS Sicherheitsgrenzen validieren.

Akzeptanz: Unzulaessige SOC-, Leistungs-, Temperatur- oder Spannungswerte werden
nicht ungeprueft in den naechsten Tick uebernommen.

## GG-BESS-006 Temperaturzustaende
<a id="gg-bess-006"></a>

Das Batteriemodell SOLLTE Temperaturzustaende simulieren koennen.

Akzeptanz: Temperatur kann als vereinfachtes thermisches Zustandsmodell oder als
eingespeiste Zeitreihe abgebildet werden.

## GG-BESS-007 Zellspannungsabweichungen
<a id="gg-bess-007"></a>

Das Batteriemodell SOLLTE Zellspannungsabweichungen simulieren koennen.

Akzeptanz: Zellspannungsabweichungen koennen als aggregierte Metrik
`cell_voltage_delta_v` exportiert werden.

## GG-BESS-008 Initialparameter-Validierung
<a id="gg-bess-008"></a>

Das Batteriemodell MUSS Initialparameter validieren.

Akzeptanz: Kapazitaet, SOC-Grenzen, Initial-SOC, Leistungsgrenzen,
Wirkungsgrade und Ramp-Limits werden vor Simulationsstart validiert; ungueltige
Konfigurationen verhindern den Start des Szenarios.

---

# 11. Netzmodell

## GG-GRID-001 Frequenzabweichungen
<a id="gg-grid-001"></a>

Die Plattform MUSS Frequenzabweichungen simulieren koennen.

Akzeptanz: Das MVP enthaelt mindestens ein vereinfachtes Leistungsbilanzmodell,
das Frequenzabweichungen aus Erzeugung, Last und Speicherleistung ableitet.
Das Modell dokumentiert Annahmen, Grenzen und Parametrisierung.

## GG-GRID-002 Spannungsabweichungen
<a id="gg-grid-002"></a>

Die Plattform MUSS Spannungsabweichungen simulieren koennen.

Akzeptanz: Das MVP enthaelt mindestens ein vereinfachtes Spannungsmodell je
Netzanschlusspunkt. Das Modell muss kenntlich machen, ob es ein vereinfachtes
Ersatzmodell oder einen Power-Flow-Adapter verwendet.

## GG-GRID-003 Netzlast-Simulation
<a id="gg-grid-003"></a>

Die Plattform MUSS Netzlasten simulieren koennen.

Akzeptanz: Lasten koennen als konstante Werte, Zeitreihen oder Szenario-Events
definiert werden.

## GG-GRID-004 Lastspitzen
<a id="gg-grid-004"></a>

Die Plattform MUSS Lastspitzen simulieren koennen.

Akzeptanz: Szenarien koennen Lastspruenge mit Startzeit, Dauer und Leistung
definieren.

## GG-GRID-005 Inselnetzmodi
<a id="gg-grid-005"></a>

Die Plattform SOLLTE Inselnetzmodi unterstuetzen.

Akzeptanz: Wenn Inselnetzmodi implementiert sind, sind sie ueber ein eigenes
Modell aktivierbar und erzeugen dokumentierte Telemetrie zu Netzstatus,
Frequenz und Versorgungsbilanz.

## GG-GRID-006 Transformatorgrenzen
<a id="gg-grid-006"></a>

Die Plattform SOLLTE Transformatorgrenzen simulieren koennen.

Akzeptanz: Wenn Transformatorgrenzen implementiert sind, erzeugt das Modell
Telemetrie zu Auslastung, Grenzwerten und Qualitaetsstatus.

## GG-GRID-007 Blindleistungsfluesse
<a id="gg-grid-007"></a>

Die Plattform SOLLTE Blindleistungsfluesse simulieren koennen.

Akzeptanz: Wenn Blindleistungsfluesse implementiert sind, exportiert das Modell
mindestens Wirk-, Blind- und Scheinleistung mit dokumentierten Einheiten und
Annahmen.

---

# 12. Szenariosystem

## GG-SCN-001 YAML-Szenarien (versioniert)
<a id="gg-scn-001"></a>

Die Plattform MUSS YAML-basierte Szenarien mit Schema-Version unterstuetzen.

Akzeptanz: Szenariodateien enthalten `schema_version`, `metadata`,
`simulation`, `devices` und optional `events`, `replay` und `faults`.

## GG-SCN-002 Deterministische Szenarien
<a id="gg-scn-002"></a>

Szenarien MUESSEN deterministisch ausfuehrbar sein.

Akzeptanz: Das Szenarioformat erlaubt keine nichtdeterministische Systemzeit und
keine impliziten Zufallsquellen ohne Seed.

## GG-SCN-003 Versionierbare Szenarien
<a id="gg-scn-003"></a>

Szenarien MUESSEN versionierbar sein.

Akzeptanz: Schema-Version und Szenario-Hash werden bei jedem Lauf exportiert.

## GG-SCN-004 Exportierbare Szenarien
<a id="gg-scn-004"></a>

Szenarien MUESSEN exportierbar sein.

Akzeptanz: Ein geladenes Szenario kann kanonisch serialisiert werden.

## GG-SCN-005 Zeitbasierte Ereignisse
<a id="gg-scn-005"></a>

Szenarien MUESSEN zeitbasierte Ereignisse unterstuetzen.

Akzeptanz: Ereignisse koennen mit Simulationszeit, Ziel, Typ, Payload und
optionalem Wiederherstellungsverhalten definiert werden und werden vor dem ersten
Tick validiert.

## GG-SCN-006 Szenario-Fault-Injection
<a id="gg-scn-006"></a>

Szenarien MUESSEN Fault Injection unterstuetzen.

Akzeptanz: Das Szenarioformat kann Faults mit Startzeit, Dauer, Ziel, Fault-Typ,
Payload und Recovery-Verhalten ausdruecken; ungueltige Fault-Definitionen werden
vor dem ersten Tick als Validierungsfehler gemeldet.

## GG-SCN-007 Szenario-Replay-Verweise
<a id="gg-scn-007"></a>

Szenarien SOLLTEN Replay-Verweise unterstuetzen.

Akzeptanz: Wenn Replay-Verweise implementiert sind, enthalten sie Quelle,
Format, Zeitabbildung und Validierungsstatus und koennen vor Simulationsstart
auf Existenz und Schema-Kompatibilitaet geprueft werden.

## GG-SCN-008 Szenario-Validierung
<a id="gg-scn-008"></a>

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
      nominal_voltage_v: 400
      max_import_kw: 100
      max_export_kw: 100
  - id: "pv-1"
    type: "pv"
    params:
      rated_power_kw: 1500
  - id: "load-1"
    type: "load"
    params:
      rated_power_kw: 800
  - id: "battery-1"
    type: "battery"
    params:
      capacity_kwh: 1000
      initial_soc_pct: 50
      max_charge_kw: 500
      max_discharge_kw: 500
  - id: "meter-1"
    type: "smart_meter"
    params:
      aggregate_device_ids:
        - "battery-1"
        - "grid-1"
        - "load-1"
        - "pv-1"
      aggregate_metric_name: "power_kw"
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

## GG-REPLAY-001 Zeitreihen-Import
<a id="gg-replay-001"></a>

Die Plattform MUSS historische Zeitreihen importieren koennen.

Akzeptanz: CSV und JSON Lines werden fuer MVP unterstuetzt; jedes Sample enthaelt
Zeitstempel, Geraete-ID, Metrikname, Wert und Einheit.

## GG-REPLAY-002 Originalzeitstempel
<a id="gg-replay-002"></a>

Replay-Systeme MUESSEN Originalzeitstempel unterstuetzen.

Akzeptanz: Originalzeitstempel werden unveraendert gespeichert und auf
Simulationszeit abgebildet.

## GG-REPLAY-003 Deterministischer Replay
<a id="gg-replay-003"></a>

Replay-Systeme MUESSEN deterministisch ausfuehrbar sein.

Akzeptanz: Samples mit gleichem Zeitstempel werden stabil nach Quelle, Metrik und
Import-Reihenfolge sortiert.

## GG-REPLAY-004 Beschleunigte Wiedergabe
<a id="gg-replay-004"></a>

Replay-Systeme SOLLTEN beschleunigte Wiedergabe unterstuetzen.

Akzeptanz: Wenn beschleunigte Wiedergabe implementiert ist, kann der Faktor ueber
API und CLI gesetzt werden und erzeugt einen dokumentierten Status.

## GG-REPLAY-005 Replay-Pause/Resume
<a id="gg-replay-005"></a>

Replay-Systeme SOLLTEN Pause/Resume unterstuetzen.

Akzeptanz: Wenn Pause/Resume fuer Replay implementiert ist, kann ein Replay ueber
API und CLI pausiert und fortgesetzt werden, ohne Tick-Reihenfolge oder
Replay-Diff zu veraendern.

## GG-REPLAY-006 Replay-Delta-Analyse
<a id="gg-replay-006"></a>

Replay-Systeme SOLLTEN Delta-Analysen ermoeglichen.

Akzeptanz: Wenn Delta-Analysen implementiert sind, liefern sie ueber API oder CLI
einen maschinenlesbaren Status und eine Liste fachlicher Abweichungen.

## GG-REPLAY-007 Fachlich/volatil-Trennung
<a id="gg-replay-007"></a>

Replay-Diffs MUESSEN fachliche und volatile Felder unterscheiden.

Akzeptanz: Diff-Ausgaben enthalten Pfad, erwarteten Wert, tatsaechlichen Wert,
Tick, Geraete-ID und Klassifikation der Abweichung.

---

# 14. Fault Injection

## GG-FAULT-001 Kommunikationsausfaelle
<a id="gg-fault-001"></a>

Die Plattform MUSS Kommunikationsausfaelle simulieren koennen.

Akzeptanz: Ein Kommunikationsausfall kann im Szenario mit Startzeit, Dauer,
Ziel, betroffenen Ein- oder Ausgangskanaelen und Recovery-Verhalten definiert
werden. Waehrend des Ausfalls werden betroffene Werte als `missing` oder
`stale` markiert und mindestens ein Alarm erzeugt.

## GG-FAULT-002 Stale-Data-Injection
<a id="gg-fault-002"></a>

Die Plattform MUSS Stale Data simulieren koennen.

Akzeptanz: Ein Stale-Data-Fault kann fuer ein Ziel und eine Metrik aktivieren,
dass der letzte gueltige Wert weitergeliefert wird, bis `max_age` ueberschritten
ist. Danach wird der Qualitaetsstatus `stale` gesetzt.

## GG-FAULT-003 NaN-Injection
<a id="gg-fault-003"></a>

Die Plattform MUSS NaN-Werte simulieren koennen.

Akzeptanz: Ein NaN-Fault kann fuer ein Ziel und eine Metrik einen nicht
numerischen Eingangswert erzeugen. Der Wert wird nicht ungeprueft in den
Geraetezustand uebernommen, sondern mit Qualitaetsstatus `nan` und Alarm
protokolliert.

## GG-FAULT-004 Frequenzabfaelle
<a id="gg-fault-004"></a>

Die Plattform MUSS Frequenzabfaelle simulieren koennen.

Akzeptanz: Ein Frequenzabfall kann mit Startzeit, Dauer, Zielnetz,
Frequenzwert oder Delta und Recovery-Verhalten definiert werden und erzeugt
Grid-Telemetrie sowie einen Alarm.

## GG-FAULT-005 Spannungseinbrueche
<a id="gg-fault-005"></a>

Die Plattform MUSS Spannungseinbrueche simulieren koennen.

Akzeptanz: Ein Spannungseinbruch kann mit Startzeit, Dauer, Zielnetz,
Spannungswert oder Delta und Recovery-Verhalten definiert werden und erzeugt
Grid-Telemetrie sowie einen Alarm.

## GG-FAULT-006 Modbus-Timeouts
<a id="gg-fault-006"></a>

Die Plattform SOLLTE Modbus-Timeouts simulieren koennen.

Akzeptanz: Wenn der Modbus-Adapter implementiert ist, kann ein Timeout mit
Startzeit, Dauer, Zielregister und Recovery-Verhalten definiert werden. Der
Adapter liefert einen dokumentierten Fehlerstatus und erzeugt einen Alarm.

## GG-FAULT-007 Geraeteausfaelle
<a id="gg-fault-007"></a>

Die Plattform MUSS Geraeteausfaelle simulieren koennen.

Akzeptanz: Ein Geraeteausfall kann mit Startzeit, Dauer, Zielgeraet,
Ausfallmodus und Recovery-Verhalten definiert werden. Das Zielgeraet liefert
waehrend des Ausfalls dokumentierte Qualitaetszustaende und erzeugt einen Alarm.

## GG-FAULT-008 SOC-Spruenge
<a id="gg-fault-008"></a>

Die Plattform SOLLTE SOC-Spruenge simulieren koennen.

Akzeptanz: Wenn SOC-Spruenge implementiert sind, koennen Sprunghoehe, Startzeit,
Zielbatterie und Recovery-Verhalten im Szenario definiert werden. Der Sprung
wird als Fault-Telemetrie und Alarm protokolliert.

## GG-FAULT-009 Netzwerkpartitionen
<a id="gg-fault-009"></a>

Die Plattform SOLLTE Netzwerkpartitionen simulieren koennen.

Akzeptanz: Wenn Netzwerkpartitionen implementiert sind, koennen betroffene
Adapter, Startzeit, Dauer und Recovery-Verhalten im Szenario definiert werden.
Betroffene Nachrichten werden deterministisch verworfen, verzoegert oder als
fehlgeschlagen markiert.

## GG-FAULT-010 Deterministische Fault-Replays
<a id="gg-fault-010"></a>

Fault Injection MUSS deterministisch replaybar sein.

Akzeptanz: Faults werden als Events mit Simulationszeit und Sequenznummer in den
Laufmetadaten protokolliert und erzeugen bei Replay dieselben fachlichen
Auswirkungen.

---

# 15. Multi-Agent-System

## GG-AGENT-001 Agentenbasierte Steuerung
<a id="gg-agent-001"></a>

Die Plattform SOLLTE agentenbasierte Steuerungsmodelle unterstuetzen.

Akzeptanz: Wenn agentenbasierte Steuerung implementiert ist, kann mindestens ein
Agent ueber eine dokumentierte Schnittstelle Steuerentscheidungen erzeugen.

## GG-AGENT-002 Isoliert testbare Agenten
<a id="gg-agent-002"></a>

Agenten SOLLTEN isoliert testbar sein.

Akzeptanz: Wenn Agenten implementiert sind, koennen sie ohne laufende
Gesamtsimulation mit deterministischen Eingaben getestet werden.

## GG-AGENT-003 Deterministische Agenten-Replays
<a id="gg-agent-003"></a>

Agenten SOLLTEN deterministisch replaybar sein.

Akzeptanz: Wenn Agenten Replay unterstuetzen, erzeugt derselbe Eingabeverlauf mit
gleichem Seed dieselben Nachrichten und Steuerbefehle.

## GG-AGENT-004 Standardisierte Agenten-Nachrichten
<a id="gg-agent-004"></a>

Agenten SOLLTEN standardisierte Nachrichten verwenden.

Akzeptanz: Wenn Agentennachrichten implementiert sind, enthalten sie
Simulationszeit, Sender, Empfaenger, Nachrichtentyp, Payload und Sequenznummer.

## GG-AGENT-005 Konkurrierende Regelstrategien
<a id="gg-agent-005"></a>

Die Plattform SOLLTE konkurrierende Regelstrategien unterstuetzen.

Akzeptanz: Wenn konkurrierende Regelstrategien implementiert sind, ist die
Priorisierung oder Konfliktaufloesung dokumentiert und deterministisch getestet.

## GG-AGENT-006 Lokale Agenten-Zustaende
<a id="gg-agent-006"></a>

Agenten SOLLTEN lokale Zustaende verwalten koennen.

Akzeptanz: Wenn Agentenzustaende implementiert sind, koennen sie exportiert,
snapshot-basiert wiederhergestellt und im Replay verglichen werden.

## GG-AGENT-007 Agenten-Zeitrestriktionen
<a id="gg-agent-007"></a>

Agenten SOLLTEN Zeitrestriktionen unterstuetzen.

Akzeptanz: Wenn Zeitrestriktionen implementiert sind, werden Deadlines,
abgelaufene Entscheidungen und resultierende Statuswerte deterministisch
behandelt.

## GG-AGENT-008 Asynchrone Agenten-Kommunikation
<a id="gg-agent-008"></a>

Agenten SOLLTEN asynchron kommunizieren koennen.

Akzeptanz: Agentenkommunikation wird ueber deterministisch sortierte Nachrichten
mit Simulationszeit, Sender, Empfaenger, Nachrichtentyp, Payload und Sequenznummer
abgebildet. Asynchrone Verarbeitung darf die Commit-Reihenfolge eines Ticks nicht
veraendern.

---

# 16. Kommunikationsschnittstellen

## GG-API-001 REST-Steuerungs-API
<a id="gg-api-001"></a>

Die Plattform MUSS REST-Schnittstellen fuer Test- und Demo-Steuerung
bereitstellen.

Akzeptanz: REST bietet Endpunkte fuer Szenario-Start, Pause, Resume, Stop,
Status, Snapshot und Fault Injection.

## GG-API-002 WebSocket-Telemetrie
<a id="gg-api-002"></a>

Die Plattform MUSS WebSocket-Telemetrie fuer Live-Ansichten unterstuetzen.

Akzeptanz: WebSocket-Nachrichten enthalten Lauf-ID, Simulationszeit,
Sequenznummer und Telemetrie-Payload.

## GG-API-003 Maschinenlesbarer API-Vertrag
<a id="gg-api-003"></a>

Die Plattform MUSS einen maschinenlesbaren API-Vertrag bereitstellen.

Akzeptanz: REST-Endpunkte sind per OpenAPI dokumentiert; Request- und
Response-Schemas enthalten Fehlerformate und Statuscodes.

## GG-API-004 Standardisierte API-Fehler
<a id="gg-api-004"></a>

Die Plattform MUSS API-Fehler standardisiert ausgeben.

Akzeptanz: Fehlerantworten enthalten `code`, `message`, `details`, `run_id`
falls vorhanden und einen stabilen HTTP-Status.

## GG-MQTT-001 MQTT-Adapter
<a id="gg-mqtt-001"></a>

Die Plattform SOLLTE MQTT als Simulationsadapter unterstuetzen.

Akzeptanz: Wenn MQTT implementiert ist, dokumentiert der Adapter Topic-Schema,
Payload-Format, QoS-Annahmen, Publish-/Subscribe-Richtung, Fehlerverhalten und
Zuordnung zu Simulationszeit. Ein deterministischer Adapter-Smoke-Test weist
Nachrichtenannahme und Telemetrieausgabe nach.

## GG-MODB-001 Modbus-TCP-Adapter
<a id="gg-modb-001"></a>

Die Plattform SOLLTE Modbus TCP als Simulationsadapter unterstuetzen.

Akzeptanz: Wenn Modbus TCP implementiert ist, dokumentiert der Adapter
Register-Mapping, Datentypen, Byte-Reihenfolge, Lese-/Schreiboperationen,
Timeout-Verhalten und Zuordnung zu Simulationszeit. Ein deterministischer
Adapter-Smoke-Test weist mindestens einen Lese- und einen Schreibpfad nach.

## GG-OPCUA-001 OPC-UA-Adapter
<a id="gg-opcua-001"></a>

Die Plattform SOLLTE OPC-UA als Simulationsadapter unterstuetzen.

Akzeptanz: Wenn OPC-UA implementiert ist, dokumentiert der Adapter Node-IDs,
Datentypen, Lese-/Schreibpfade, Fehlerverhalten und Zuordnung zu
Simulationszeit.

## GG-DNP3-001 DNP3-Adapter
<a id="gg-dnp3-001"></a>

Die Plattform SOLLTE DNP3 als Simulationsadapter unterstuetzen.

Akzeptanz: Wenn DNP3 implementiert ist, dokumentiert der Adapter Points,
Variations, Qualitaetsflags, Fehlerverhalten und Zuordnung zu Simulationszeit.

## GG-IEC-001 IEC-61850-Adapter
<a id="gg-iec-001"></a>

Die Plattform SOLLTE IEC61850 als Simulationsadapter unterstuetzen.

Akzeptanz: Wenn IEC61850 implementiert ist, dokumentiert der Adapter Logical
Nodes, Datenattribute, Report-/Control-Verhalten, Fehlerverhalten und Zuordnung
zu Simulationszeit.

## GG-SNMP-001 SNMP-Adapter
<a id="gg-snmp-001"></a>

Die Plattform SOLLTE SNMP als Simulationsadapter fuer Device-Management-
und Telemetrie-Use-Cases unterstuetzen.

Akzeptanz: Wenn SNMP implementiert ist, dokumentiert der Adapter
OID-/MIB-Mapping, SNMP-Version, Security-Annahmen, Polling-/Set-/Trap-
Richtung, Fehlerverhalten und Zuordnung zu Simulationszeit. Ein
deterministischer Adapter-Smoke-Test weist mindestens einen Polling-
Telemetriepfad nach; Schreibpfade werden nur aktiviert, wenn das
Adapter-Profil sie ausdruecklich vorsieht.

## GG-LWM2M-001 LwM2M-Adapter
<a id="gg-lwm2m-001"></a>

Die Plattform SOLLTE LwM2M als Simulationsadapter fuer Device-Management-
und Telemetrie-Use-Cases unterstuetzen.

Akzeptanz: Wenn LwM2M implementiert ist, dokumentiert der Adapter
Object-/Resource-Mapping, Client-/Server-Rolle, CoAP-/Security-Annahmen,
Observe-/Read-/Write-/Execute-Richtung, Fehlerverhalten und Zuordnung zu
Simulationszeit. Ein deterministischer Adapter-Smoke-Test weist mindestens
einen Observe- oder Polling-Telemetriepfad nach; Write/Execute-Pfade werden
nur aktiviert, wenn das Adapter-Profil sie ausdruecklich vorsieht.

Akzeptanz fuer alle Protokolladapter: Adapter muessen klar als Simulations- und
Testadapter dokumentiert sein und duerfen keine produktive Anlagensteuerung
versprechen.

---

# 17. Visualisierung

## GG-UI-001 Web-UI
<a id="gg-ui-001"></a>

Die Plattform MUSS ein Web-UI fuer lokale Demo- und Testumgebungen bereitstellen.

Akzeptanz: Das UI ist nach `docker compose up` lokal erreichbar und zeigt den
Systemstatus der Demo-Umgebung an.

## GG-UI-002 Live-Telemetrie-Ansicht
<a id="gg-ui-002"></a>

Das UI MUSS Live-Telemetrie visualisieren koennen.

Akzeptanz: Das UI zeigt waehrend eines laufenden Demo-Szenarios aktuelle
Telemetriepunkte mit Geraet, Metrik, Wert, Einheit, Simulationszeit und
Qualitaetsstatus an.

## GG-UI-003 Zeitreihen-Ansicht
<a id="gg-ui-003"></a>

Das UI MUSS Zeitreihen visualisieren koennen.

Akzeptanz: Das UI zeigt fuer mindestens eine Leistungsmetrik und eine SOC-Metrik
einen zeitlich sortierten Verlauf aus persistierten oder live gepufferten
Telemetriedaten an.

## GG-UI-004 Replay-Steuerung (UI)
<a id="gg-ui-004"></a>

Das UI MUSS Replay-Steuerung unterstuetzen.

Akzeptanz: Das UI bietet fuer einen vorhandenen Lauf mindestens Start, Pause,
Resume, Stop und Anzeige des Replay-Status an.

## GG-UI-005 Alarm-Ansicht
<a id="gg-ui-005"></a>

Das UI MUSS Alarme visualisieren koennen.

Akzeptanz: Das UI zeigt Alarmzeit, Ziel, Schweregrad, Code, Nachricht und
aktuellen Status in einer aktualisierbaren Tabelle an.

## GG-UI-006 Grafische Geraete-Ansicht
<a id="gg-ui-006"></a>

Das UI SOLLTE Geraete grafisch darstellen koennen.

Akzeptanz: Wenn grafische Geraetedarstellung implementiert ist, zeigt das UI
mindestens die MVP-Geraetetypen mit ID, Typ, aktuellem Zustand und
Qualitaetsstatus an.

## GG-UI-007 Fault-Injection-Bedienung
<a id="gg-ui-007"></a>

Das UI SOLLTE Fault Injection ausloesen koennen.

Akzeptanz: Wenn Fault Injection im UI implementiert ist, koennen Fault-Typ, Ziel,
Startzeit, Dauer und Recovery-Verhalten eingegeben und vor Ausloesung validiert
werden.

## GG-UI-008 Simulationszustands-Ansicht
<a id="gg-ui-008"></a>

Das UI SOLLTE Simulationszustaende visualisieren koennen.

Akzeptanz: Wenn diese Funktion implementiert ist, zeigt das UI mindestens
Laufstatus, aktuelle Simulationszeit, Tick-Zaehler und Zustand des
Simulationsdienstes.

## GG-UI-009 Datenqualitaets-Anzeige
<a id="gg-ui-009"></a>

Das UI MUSS Datenqualitaet sichtbar machen.

Akzeptanz: Telemetriepunkte mit `stale`, `invalid`, `nan`, `missing` oder
`fault_injected` werden in Tabellen und Zeitreihen unterscheidbar dargestellt.

---

# 18. Persistenz

## GG-PERSIST-001 Zeitreihen-Persistenz
<a id="gg-persist-001"></a>

Die Plattform MUSS Zeitreihen speichern koennen.

Akzeptanz: Telemetriepunkte koennen mit Lauf-ID, Simulationszeit, Geraet, Metrik,
Wert, Einheit, Qualitaetsstatus, Quelle und Sequenz persistiert und fuer einen
Lauf wieder abgefragt werden.

## GG-PERSIST-002 Replay-Daten-Persistenz
<a id="gg-persist-002"></a>

Die Plattform MUSS Replay-Daten speichern koennen.

Akzeptanz: Importierte Replay-Samples werden mit Originalzeitstempel,
Simulationszeit, Quelle, Geraet, Metrik, Wert, Einheit und Import-Sequenz
persistiert.

## GG-PERSIST-003 Szenariodaten-Persistenz
<a id="gg-persist-003"></a>

Die Plattform MUSS Szenariodaten speichern koennen.

Akzeptanz: Ein gestartetes Szenario wird mit Schema-Version, kanonischem
Szenario-Hash und kanonischer Szenario-Repraesentation gespeichert.

## GG-PERSIST-004 Alarmhistorien-Persistenz
<a id="gg-persist-004"></a>

Die Plattform MUSS Alarmhistorien speichern koennen.

Akzeptanz: Alarme werden mit Lauf-ID, Simulationszeit, Ziel, Code, Schweregrad,
Nachricht, Status und optionaler Fault-ID gespeichert und laufbezogen abgefragt.

## GG-PERSIST-005 PostgreSQL-Unterstuetzung
<a id="gg-persist-005"></a>

Die Plattform MUSS PostgreSQL unterstuetzen.

Akzeptanz: Der Docker-Compose-Stack startet PostgreSQL als verpflichtenden
MVP-Speicher, wendet Migrationen an und besteht einen Healthcheck.

## GG-PERSIST-006 TimescaleDB-Unterstuetzung
<a id="gg-persist-006"></a>

Die Plattform SOLLTE TimescaleDB unterstuetzen.

Akzeptanz: Wenn TimescaleDB implementiert ist, dokumentiert der Adapter Schema,
Hypertables oder Indizes, Migrationspfad und Abfrageverhalten fuer Laufdaten.

## GG-PERSIST-007 InfluxDB-Unterstuetzung
<a id="gg-persist-007"></a>

Die Plattform SOLLTE InfluxDB unterstuetzen.

Akzeptanz: Wenn InfluxDB implementiert ist, dokumentiert der Adapter Buckets,
Measurements, Tags, Retention-Annahmen und Abfrageverhalten fuer Laufdaten.
Persistierte Datensaetze enthalten Lauf-ID, Simulationszeit, Erfassungszeit,
Quelle, Payload und Schema-Version. PostgreSQL ist der verpflichtende
MVP-Speicher; TimescaleDB und InfluxDB sind optionale Adapter. Erfassungszeit
ist ein persistiertes Betriebsmetadatum und wird in kanonischen Replay- und
Golden-File-Vergleichen als volatil behandelt.

## GG-PERSIST-008 Versionierte Datenbankmigrationen
<a id="gg-persist-008"></a>

Die Plattform MUSS Datenbankmigrationen versionieren.

Akzeptanz: Schemaaenderungen sind migrationsbasiert nachvollziehbar und koennen
in einer leeren lokalen Datenbank reproduzierbar angewendet werden.

## GG-PERSIST-009 Lauf-Loeschung
<a id="gg-persist-009"></a>

Die Plattform MUSS Laufdaten eindeutig loeschen koennen.

Akzeptanz: Ein Lauf kann inklusive Telemetrie, Alarme, Snapshots und Metadaten
ueber eine dokumentierte Operation entfernt werden, ohne andere Laeufe zu
veraendern.

---

# 19. Telemetrie

## GG-OTEL-001 OpenTelemetry-Support
<a id="gg-otel-001"></a>

Die Plattform SOLLTE OpenTelemetry fuer Traces und Metriken unterstuetzen.

Akzeptanz: Wenn OpenTelemetry implementiert ist, exportiert die Demo
OTLP-kompatible Traces und Metriken oder stellt einen konfigurierbaren
OTLP-Exporter bereit.

## GG-OTEL-002 Strukturierte Logs
<a id="gg-otel-002"></a>

Die Plattform MUSS strukturierte Logs unterstuetzen.

Akzeptanz: Logs enthalten Zeitstempel, Level, Lauf-ID, Modul, Event-ID und
Nachricht.

## GG-OTEL-003 Metrik-Export
<a id="gg-otel-003"></a>

Die Plattform MUSS Metriken exportieren koennen.

Akzeptanz: Exportiert werden mindestens Tick-Dauer, Event-Queue-Laenge,
verarbeitete Telemetriepunkte/s, Fehleranzahl und Replay-Diff-Status.

## GG-OTEL-004 Trace-Export
<a id="gg-otel-004"></a>

Die Plattform SOLLTE Traces exportieren koennen.

Akzeptanz: Wenn Tracing implementiert ist, kann ein Tick ueber Scheduler,
Geraetemodell, Adapter und Persistenz tracebar sein.

---

# 20. Sicherheitsanforderungen

## GG-SAFE-001 Erkennung ungueltiger Daten
<a id="gg-safe-001"></a>

Ungueltige Daten MUESSEN erkannt werden.

Akzeptanz: Schema-, Wertebereichs- und Einheitenfehler werden vor Uebernahme in
den Simulationskern als Validierungsfehler oder Qualitaetsstatus `invalid`
gemeldet und erzeugen einen nachvollziehbaren Fehler- oder Alarmdatensatz.

## GG-SAFE-002 NaN-Schutz
<a id="gg-safe-002"></a>

NaN-Werte DUERFEN NICHT ungeprueft verarbeitet werden.

Akzeptanz: NaN-Werte werden vor Zustandsfortschreibung erkannt, als
Qualitaetsstatus `nan` serialisiert und erzeugen mindestens einen Alarm oder
einen typisierten Fehler.

## GG-SAFE-003 Ausfallerkennung
<a id="gg-safe-003"></a>

Kommunikationsausfaelle MUESSEN erkannt werden.

Akzeptanz: Kommunikationsausfaelle erzeugen einen dokumentierten Fehlerstatus,
betroffene Telemetrie wird als `missing` oder `stale` markiert und ein Alarm mit
Ziel, Startzeit und Ursache wird erzeugt.

## GG-SAFE-004 Markierung veralteter Daten
<a id="gg-safe-004"></a>

Veraltete Daten MUESSEN markiert werden.

Akzeptanz: Werte, deren Simulationszeitstempel die konfigurierte `max_age`
ueberschreiten, erhalten deterministisch den Qualitaetsstatus `stale`.

## GG-SAFE-005 Sichere Fallback-Zustaende
<a id="gg-safe-005"></a>

Die Plattform SOLLTE sichere Fallback-Zustaende unterstuetzen.

Akzeptanz: Wenn Fallback-Zustaende implementiert sind, dokumentiert jeder
betroffene Geraetetyp Ausloeser, Zielzustand, Telemetrie und Recovery-Verhalten.

## GG-SAFE-006 Nichtdeterminismus-Erkennung
<a id="gg-safe-006"></a>

Nichtdeterministische Simulationslaeufe SOLLTEN erkannt werden.

Akzeptanz: Wenn Erkennung nichtdeterministischer Laeufe implementiert ist,
meldet die Plattform Replay-Diff, volatile Felder, betroffene Ticks und
Abweichungsklassifikation maschinenlesbar.

## GG-SAFE-007 Sim/Prod-Kontexttrennung
<a id="gg-safe-007"></a>

Die Plattform MUSS Simulations- und Produktivkontexte klar trennen.

Akzeptanz: UI, API-Dokumentation und Adapterkonfiguration kennzeichnen
Simulationsadapter als nicht fuer produktive Anlagensteuerung freigegeben.

## GG-SAFE-008 Eingabevalidierung
<a id="gg-safe-008"></a>

Die Plattform MUSS Eingaben an externen Schnittstellen validieren.

Akzeptanz: REST-, WebSocket- und alle implementierten Adapter-Eingaben werden
gegen Schema, Wertebereiche und Zielressourcen validiert, bevor sie in den
Simulationskern gelangen.

---

# 21. Testbarkeit

## GG-TEST-001 Replay-basierte Tests
<a id="gg-test-001"></a>

Die Plattform MUSS Replay-basierte Tests unterstuetzen.

Akzeptanz: Ein automatisierter Test kann einen gespeicherten oder importierten
Lauf erneut ausfuehren und einen Replay-Diff als maschinenlesbares Ergebnis
erzeugen.

## GG-TEST-002 Deterministische Tests
<a id="gg-test-002"></a>

Die Plattform MUSS deterministische Tests unterstuetzen.

Akzeptanz: Ein automatisierter Test fuehrt dasselbe Referenzszenario zweimal mit
gleichem Seed aus und vergleicht kanonische Ergebnisartefakte.

## GG-TEST-003 Integrationstests
<a id="gg-test-003"></a>

Die Plattform MUSS Integrationstests unterstuetzen.

Akzeptanz: Der CI- oder Abnahmebefehl enthaelt Integrationstests fuer API,
Persistenz und Telemetriepfad der Demo.

## GG-TEST-004 HIL-Tests
<a id="gg-test-004"></a>

Die Plattform SOLLTE HIL-Tests unterstuetzen.

Akzeptanz: Wenn HIL-Tests implementiert sind, sind Testgrenzen,
Simulationsadapter, erwartete Signale und deterministisches Replay-Verhalten
dokumentiert.

## GG-TEST-005 Property-basierte Tests
<a id="gg-test-005"></a>

Die Plattform SOLLTE Property-basierte Tests unterstuetzen.

Akzeptanz: Wenn Property-basierte Tests implementiert sind, pruefen sie
Invarianten fuer Scheduler, Szenario-Validierung, Replay-Diff oder
Geraetemodelle mit reproduzierbaren Seeds.

## GG-TEST-006 Automatisierte Replay-Diffs
<a id="gg-test-006"></a>

Replay-Diffs SOLLTEN automatisiert vergleichbar sein.

Akzeptanz: Wenn automatisierte Replay-Diff-Vergleiche implementiert sind, liefern
sie Exit-Code, maschinenlesbaren Status und eine Liste fachlicher Abweichungen.

## GG-TEST-007 MUSS-Requirements-Matrix
<a id="gg-test-007"></a>

Die Plattform MUSS eine Requirements-Matrix fuer MUSS-Anforderungen pflegen.

Akzeptanz: Jede MUSS-Anforderung verweist auf mindestens einen Test,
Architekturentscheid oder eine Demo-Abnahmepruefung.

## GG-TEST-008 Golden-File-Referenzen
<a id="gg-test-008"></a>

Die Plattform MUSS Golden-Files fuer deterministische Referenzszenarien
unterstuetzen.

Akzeptanz: Golden-Files werden kanonisch erzeugt und koennen in CI gegen neue
Simulationsergebnisse verglichen werden.

## 21.1 Teststrategie

### GG-TEST-009 Verpflichtende Tests
<a id="gg-test-009"></a>

Automatisierte Tests MUESSEN verpflichtender Bestandteil der Entwicklung sein.

Akzeptanz: Der dokumentierte Abnahmebefehl fuehrt automatisierte Tests aus und
liefert einen maschinenlesbaren Status.

### GG-TEST-010 Unabhaengige Unit-Tests
<a id="gg-test-010"></a>

Unit-Tests MUESSEN unabhaengig ausfuehrbar sein.

Akzeptanz: Unit-Tests benoetigen keine Datenbank, keine Netzwerkdienste und
keine externen Live-Systeme.

### GG-TEST-011 Containerisierte Integrationstests
<a id="gg-test-011"></a>

Integrationstests MUESSEN containerisiert ausfuehrbar sein.

Akzeptanz: Integrationstests fuer API, Persistenz und Telemetriepfad laufen in
der lokalen Container-Umgebung oder einer dokumentierten aequivalenten
CI-Umgebung.

### GG-TEST-012 Modulgrenzen-Architekturtests
<a id="gg-test-012"></a>

Architekturtests MUESSEN Modulgrenzen pruefen.

Akzeptanz: Architekturtests pruefen mindestens Domain-zu-Adapter-Abhaengigkeiten,
Framework-Freiheit der Domain und zyklische Modulabhaengigkeiten.

### GG-TEST-013 Testbare Replay-Funktionen
<a id="gg-test-013"></a>

Replay-Funktionalitaeten MUESSEN testbar sein.

Akzeptanz: Replay-Start, Replay-Diff, Golden-File-Vergleich,
Zeitmultiplikatoren und volatile Feldklassifikation sind durch Tests oder
Abnahmepruefungen abgedeckt.

### GG-TEST-014 Tests sicherheitsrelevanter Funktionen
<a id="gg-test-014"></a>

Sicherheitsrelevante Funktionen MUESSEN getestet werden.

Akzeptanz: Validierung externer Eingaben, NaN-Behandlung, stale Daten,
Kommunikationsausfaelle und Trennung von Simulations- und Produktivkontexten
sind durch automatisierte Tests oder reproduzierbare Abnahmepruefungen belegt.

### GG-TEST-015 Event-Processing-Tests
<a id="gg-test-015"></a>

Event-Processing MUSS getestet werden.

Akzeptanz: Tests pruefen Event-Sortierung, Tie-Breaking, Sequenznummern,
Tick-Commit-Reihenfolge und deterministisches Replay.

### GG-TEST-016 Fehlerfall-Tests
<a id="gg-test-016"></a>

Fehlerfaelle MUESSEN getestet werden.

Akzeptanz: Tests decken ungueltige Szenarien, unbekannte Geraete, ungueltige
Einheiten, Adapterfehler, Persistenzfehler und abgelehnte Steuerbefehle ab.

### GG-TEST-017 Datenschutz-/Retention-Tests
<a id="gg-test-017"></a>

Datenschutz-, Maskierungs- und Aufbewahrungsregeln SOLLTEN getestet werden.

Akzeptanz: Wenn solche Regeln implementiert sind, pruefen Tests Maskierung,
Export, Loeschung, Aufbewahrungsfristen und Ausschluss volatiler oder sensibler
Felder aus kanonischen Vergleichsartefakten.

### GG-TEST-018 Replay-Guard-Tests
<a id="gg-test-018"></a>

Replay-Freigaben, Whitelists, Dry-Run und Rate-Limits SOLLTEN getestet werden.

Akzeptanz: Wenn diese Schutzfunktionen implementiert sind, pruefen Tests
Freigabelogik, erlaubte Ziele, Dry-Run ohne Zustandsaenderung und deterministisch
behandelte Rate-Limits.

---

# 22. CI/CD-Anforderungen

## GG-CICD-001 Automatisierte Build-Pipeline
<a id="gg-cicd-001"></a>

Die Plattform MUSS eine automatisierte Build-Pipeline bereitstellen.

Akzeptanz: Die Pipeline baut alle produktiven Artefakte reproduzierbar aus dem
Repository.

## GG-CICD-002 Automatische Tests (CI)
<a id="gg-cicd-002"></a>

Die Pipeline MUSS Tests automatisch ausfuehren.

Akzeptanz: Unit-, Integrations-, Architektur- und Demo-Abnahmetests laufen in
der Pipeline oder sind dort als getrennte, dokumentierte Jobs verfuegbar.

## GG-CICD-003 Automatische Quality Gates
<a id="gg-cicd-003"></a>

Die Pipeline MUSS Quality Gates automatisch auswerten.

Akzeptanz: Teststatus, Architekturtests, OpenAPI-Validierung und Security-Scan
werden als maschinenlesbare Gate-Ergebnisse ausgewiesen.

## GG-CICD-004 Containerisierte Builds
<a id="gg-cicd-004"></a>

Builds SOLLTEN containerisiert ausfuehrbar sein.

Akzeptanz: Die Pipeline kann Build- und Testschritte in dokumentierten
Container-Images ausfuehren.

## GG-CICD-005 Security-Scanning
<a id="gg-cicd-005"></a>

Security-Scanning MUSS in der Pipeline verfuegbar sein.

Akzeptanz: Die Pipeline kann Abhaengigkeiten und Container-Images auf bekannte
Schwachstellen pruefen.

## GG-CICD-006 Dependency-Scanning
<a id="gg-cicd-006"></a>

Dependency-Scanning MUSS in der Pipeline verfuegbar sein.

Akzeptanz: Die Pipeline erzeugt eine Liste direkter und transitiver
Abhaengigkeiten und meldet bekannte Schwachstellen oder Lizenzkonflikte.

## GG-CICD-007 Automatisierte Artefakte
<a id="gg-cicd-007"></a>

Die Pipeline SOLLTE Artefakte automatisiert erzeugen.

Akzeptanz: Wenn Artefakterzeugung aktiviert ist, veroeffentlicht die Pipeline
Container-Images, Testberichte, Coverage-Berichte, OpenAPI-Spezifikation und
Demo-Abnahmeartefakte.

---

# 23. Deployment

## GG-DEPLOY-001 Docker-Compose-Support
<a id="gg-deploy-001"></a>

Die Plattform MUSS Docker Compose unterstuetzen.

Akzeptanz: Das Repository enthaelt eine dokumentierte Compose-Konfiguration, die
API, UI, Simulationsdienst und verpflichtende Persistenz lokal startet.

## GG-DEPLOY-002 Offline-Betrieb
<a id="gg-deploy-002"></a>

Die Plattform MUSS offline lokal lauffaehig sein, nachdem Images und
Abhaengigkeiten bereitgestellt wurden.

Akzeptanz: Nach lokalem Bereitstellen der benoetigten Images und Abhaengigkeiten
kann die Demo ohne Internetzugriff gestartet und abgenommen werden.

## GG-DEPLOY-003 Linux-Deployment
<a id="gg-deploy-003"></a>

Die Plattform MUSS Linux-basiert deploybar sein.

Akzeptanz: Die dokumentierte Referenzumgebung basiert auf Linux x86_64 und ein
Healthcheck weist die lauffaehigen Dienste dort nach.

## GG-DEPLOY-004 DevContainer-Support
<a id="gg-deploy-004"></a>

Die Plattform SOLLTE DevContainer unterstuetzen.

Akzeptanz: Wenn DevContainer-Unterstuetzung bereitgestellt wird, enthaelt das
Repository eine dokumentierte DevContainer-Konfiguration mit Build-, Test- und
Abnahmebefehlen.

## GG-DEPLOY-005 Ein-Kommando-Demo-Start
<a id="gg-deploy-005"></a>

Eine vollstaendige Demo MUSS mit folgendem Kommando startbar sein:

```bash
docker compose up
```

Akzeptanz: Nach erfolgreichem Start sind API, UI, Persistenz und Demo-Simulation
lokal erreichbar und der Systemstatus meldet `healthy`.

## GG-DEPLOY-006 Healthchecks
<a id="gg-deploy-006"></a>

Die Plattform MUSS Healthchecks fuer lokale Dienste bereitstellen.

Akzeptanz: API, UI, Datenbank und Simulationsdienst melden `healthy`,
`degraded` oder `unhealthy` mit kurzer Ursache.

## GG-DEPLOY-007 Kubernetes-Deployment
<a id="gg-deploy-007"></a>

Die Plattform SOLLTE Kubernetes-faehig deploybar sein.

Akzeptanz: Wenn Kubernetes-Deployment unterstuetzt wird, sind Manifeste oder
Helm/Kustomize-Artefakte fuer API, UI, Simulationsdienst und Persistenzadapter
dokumentiert.

## GG-DEPLOY-008 Rolling Updates
<a id="gg-deploy-008"></a>

Rolling Updates SOLLTEN fuer spaetere verteilte Deployments unterstuetzt werden.

Akzeptanz: Wenn verteiltes Deployment implementiert ist, dokumentiert die
Plattform Update-Strategie, Healthcheck-Gating und Verhalten laufender
Simulationen.

## GG-DEPLOY-009 Zero-Downtime-Deployment
<a id="gg-deploy-009"></a>

Zero-Downtime-Deployment KANN fuer nicht laufkritische Dienste unterstuetzt
werden.

Akzeptanz: Wenn Zero-Downtime-Deployment implementiert ist, sind betroffene
Dienste, Einschraenkungen und Ausschluss laufender Simulationen dokumentiert.

## GG-DEPLOY-010 Deployment-Rollback
<a id="gg-deploy-010"></a>

Rollback-Unterstuetzung SOLLTE fuer verteilte Deployments bereitgestellt werden.

Akzeptanz: Wenn verteiltes Deployment implementiert ist, dokumentiert die
Plattform Rollback fuer API, UI, Simulationsdienst und Datenbankschema inklusive
Grenzen bei migrationsbedingten Datenmodell-Aenderungen.

## GG-DEPLOY-011 Netzwerkfreie Abnahmelaeufe
<a id="gg-deploy-011"></a>

Simulations- und Abnahmelaeufe MUESSEN ohne externe Netzwerkverbindungen
ausfuehrbar sein.

Akzeptanz: Ein vollstaendiger Demo- oder Abnahmelauf inklusive Replay, Fault
Injection und Persistenz kann ohne aktive Netzwerkverbindungen ausserhalb des
lokalen Host- oder Container-Netzwerks durchgefuehrt werden.

---

# 24. Demo-System

## GG-DEMO-001 Demo-Umgebung
<a id="gg-demo-001"></a>

Die Plattform MUSS eine Demo-Umgebung bereitstellen.

Akzeptanz: Die Demo-Umgebung ist lokal startbar, dokumentiert und Teil des
Abnahmebefehls oder einer reproduzierbaren Demo-Abnahmepruefung.

## GG-DEMO-002 Demo-Netz
<a id="gg-demo-002"></a>

Die Demo MUSS ein simuliertes Netz enthalten.

Akzeptanz: Die Demo enthaelt mindestens einen Netzanschlusspunkt mit Frequenz-
und Spannungstelemetrie.

## GG-DEMO-003 Demo-Batterie
<a id="gg-demo-003"></a>

Die Demo MUSS eine simulierte Batterie enthalten.

Akzeptanz: Die Demo enthaelt mindestens einen Batteriespeicher mit Leistungs- und
SOC-Telemetrie.

## GG-DEMO-004 Demo-Live-Telemetrie
<a id="gg-demo-004"></a>

Die Demo MUSS Live-Telemetrie enthalten.

Akzeptanz: Nach Start der Demo werden innerhalb von 30 s aktuelle
Telemetriepunkte ueber API oder WebSocket bereitgestellt.

## GG-DEMO-005 Demo-Replay-Szenario
<a id="gg-demo-005"></a>

Die Demo MUSS mindestens ein Replay-Szenario enthalten.

Akzeptanz: Das Demo-Replay kann ueber den Abnahmebefehl oder die API gestartet
werden und liefert einen maschinenlesbaren Replay-Status.

## GG-DEMO-006 Demo-Fault-Injection
<a id="gg-demo-006"></a>

Die Demo SOLLTE Fault Injection enthalten.

Akzeptanz: Wenn Fault Injection in der Demo enthalten ist, kann mindestens ein
Fault reproduzierbar ausgeloest werden und erzeugt Telemetrie mit
Qualitaetsstatus sowie einen Alarm.

## GG-DEMO-007 Demo-Agent
<a id="gg-demo-007"></a>

Die Demo SOLLTE mindestens einen Agenten enthalten.

Akzeptanz: Wenn ein Agent in der Demo enthalten ist, erzeugt er dokumentierte
Steuerbefehle oder Nachrichten, die deterministisch replaybar sind.

## GG-DEMO-008 Demo-Abnahmereihenfolge
<a id="gg-demo-008"></a>

Die Demo MUSS eine klare Abnahmereihenfolge dokumentieren.

Akzeptanz: Die Dokumentation beschreibt Start, Healthcheck, Szenarioausfuehrung,
Fault Injection, Replay und Export in reproduzierbaren Schritten.

---

# 25. Abnahmeartefakte

## GG-ACCEPT-001 MVP-Abnahmedokumentation
<a id="gg-accept-001"></a>

Die Plattform MUSS eine Abnahmedokumentation fuer den MVP bereitstellen.

Akzeptanz: Die Dokumentation listet Umgebung, Startkommandos, erwartete
Ergebnisse, bekannte Einschraenkungen und Verweise auf Tests.

## GG-ACCEPT-002 Dokumentierte Modellgrenzen
<a id="gg-accept-002"></a>

Die Plattform MUSS bekannte Modellgrenzen dokumentieren.

Akzeptanz: Batterie-, PV-, Last- und Netzmodelle nennen Annahmen,
Gueltigkeitsbereich und bewusst nicht modellierte Effekte.

## GG-ACCEPT-003 Demo-Beispielartefakte
<a id="gg-accept-003"></a>

Die Plattform MUSS Beispielartefakte fuer einen erfolgreichen Demo-Lauf
bereitstellen.

Akzeptanz: Beispielartefakte umfassen Laufmetadaten, Telemetrieexport,
Alarmexport, Replay-Diff und Healthcheck-Ausgabe.

## GG-TRACE-001 Rueckverfolgbarkeitsmatrix
<a id="gg-trace-001"></a>

Das Projekt MUSS eine V-Modell-aehnliche Rueckverfolgbarkeitsmatrix
Anforderung→Design→Implementierung→Test fuehren.

Akzeptanz: Die kuratierten Design- und Test-Zuordnungen werden in einem
eigenen, aus dem Lastenheft verlinkten Traceability-Dokument gefuehrt
(`docs/plan/traceability.md`; ausgelagert in Slice 063, damit der Vertrag
frei von Abwaerts-Verweisen bleibt) — Anforderung→Design und
Anforderung→Test (Testtyp-Klassifikation). Die Liefer-/
Implementierungs-Rueckverfolgung (Anforderung→Slice/Welle/ADR inkl.
Abdeckungs- und Waisen-Status) wird nicht mehr handgepflegt, sondern aus
den Slice-, Wellen- und ADR-Artefakten automatisch abgeleitet (`make
doc-trace`; Re-Cut in Slice 066). Jede normative `GG-…`-Anforderung
(`MUSS`/`SOLLTE`) ist damit entweder ueber eine Slice-/Wellen-/ADR-Referenz
oder eine Coverage-Zeile nachverfolgbar. `GG-TRACE-001` ist die ID, die diese
Rueckverfolgbarkeit benennt.

---

# 26. Roadmap, keine MVP-Anforderungen

Die folgenden Punkte sind Zukunftserweiterungen. Sie sind nicht normativ fuer die
MVP-Abnahme und duerfen nicht als `MUSS`- oder `SOLLTE`-Scope interpretiert
werden, solange sie nicht in einen vorherigen Abschnitt verschoben werden.

## GG-FUTURE-001

Die Plattform KANN MPC-Regelung unterstuetzen.

Akzeptanz: Wenn MPC-Regelung in einen Abnahmescope verschoben wird, sind Modell,
Optimierungsziel, Nebenbedingungen, Determinismusannahmen und Tests dokumentiert.

## GG-FUTURE-002

Die Plattform KANN RL-/ML-Agenten unterstuetzen.

Akzeptanz: Wenn RL-/ML-Agenten in einen Abnahmescope verschoben werden, sind
Trainingsartefakte, Seeds, Modellversionen, Inferenzschnittstelle und
Replay-Grenzen dokumentiert.

## GG-FUTURE-003

Die Plattform KANN pandapower integrieren.

Akzeptanz: Wenn pandapower in einen Abnahmescope verschoben wird, sind
Modellabbildung, Version, Eingabe-/Ausgabeformate und deterministische
Vergleichsartefakte dokumentiert.

## GG-FUTURE-004

Die Plattform KANN verteilte Simulation unterstuetzen.

Akzeptanz: Wenn verteilte Simulation in einen Abnahmescope verschoben wird, sind
Partitionierung, Zeitkoordination, Fehlermodell und Replay-Grenzen dokumentiert.

## GG-FUTURE-005

Die Plattform KANN GPU-basierte Simulation unterstuetzen.

Akzeptanz: Wenn GPU-basierte Simulation in einen Abnahmescope verschoben wird,
sind Hardwareannahmen, numerische Toleranzen, deterministische Grenzen und
Fallback-Verhalten dokumentiert.

## GG-FUTURE-006

Die Plattform KANN Co-Simulation unterstuetzen.

Akzeptanz: Wenn Co-Simulation in einen Abnahmescope verschoben wird, sind
gekoppelte Simulatoren, Zeitkoordination, Datenvertraege und Replay-Grenzen
dokumentiert.
