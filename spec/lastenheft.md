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

## GG-SEED-001

Alle Zufallsquellen MUESSEN explizit seedbar sein.

Akzeptanz: Zufallsquellen ohne dokumentierten Seed verhindern die
Determinismus-Abnahme. Seeds werden in Laufmetadaten exportiert und bei Replay
wiederverwendet.

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

Akzeptanz: Ein Szenario kann fuer mindestens einen Geraetetyp zwischen zwei
Implementierungen wechseln, ohne den Simulationskern zu aendern. Fuer den MVP
darf eine der Implementierungen eine dokumentierte Test- oder Minimalvariante
sein; es ist nicht erforderlich, jeden MVP-Geraetetyp doppelt zu implementieren.

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

## 5.1 Architektur- und Entwicklungsprinzipien

### GG-PRINC-001

Das System MUSS nach SOLID-Prinzipien entwickelt werden.

Akzeptanz: Architekturentscheidungen und Code-Reviews pruefen
Einzelverantwortung, Erweiterbarkeit, Austauschbarkeit, kleine Schnittstellen
und Abhaengigkeiten gegen Abstraktionen fuer geaenderte Kernmodule.

### GG-PRINC-002

Klassen, Module und Services MUESSEN eine klare Einzelverantwortung besitzen.

Akzeptanz: Ein Modul hat einen fachlich benennbaren Grund fuer Aenderungen.
Vermischungen von Domain-Logik, Persistenz, Transport und UI-Logik werden durch
Architekturtests, Code-Review oder dokumentierte Ausnahme erkannt.

### GG-PRINC-003

Erweiterungen SOLLTEN ohne Aenderung bestehender Kernlogik moeglich sein.

Akzeptanz: Neue Geraetemodelle, Szenario-Adapter und Persistenzadapter koennen
ueber definierte Ports, Registries oder Konfiguration ergaenzt werden, ohne den
Simulationskern fachlich zu veraendern.

### GG-PRINC-004

Implementierungen MUESSEN ueber ihre definierten Schnittstellen austauschbar
sein.

Akzeptanz: Mindestens ein Port des Simulationskerns hat im Test eine alternative
Implementierung, die ohne Aenderung der Domain-Logik eingesetzt werden kann.

### GG-PRINC-005

Schnittstellen MUESSEN klein und fachlich getrennt sein.

Akzeptanz: Ports fuer Zeit, Eingaben, Ausgaben, Persistenz, Telemetrie und
Steuerbefehle sind getrennt dokumentiert. Adapter implementieren nur die Ports,
die sie fachlich benoetigen.

### GG-PRINC-006

Abhaengigkeiten MUESSEN gegen Abstraktionen gerichtet sein.

Akzeptanz: Domain-Module haengen nicht direkt von Infrastruktur-, Framework-,
Transport- oder Datenbankpaketen ab. Diese Regel wird durch Architekturtests
oder statische Importpruefungen validiert.

### GG-CC-001

Methoden und Funktionen SOLLTEN kurz und fokussiert sein.

Akzeptanz: Produktionscode ueberschreitet 30 logische Zeilen pro Methode oder
Funktion nur mit fachlicher Begruendung, z. B. fuer klar strukturierte Parser,
Tabellen oder generierten Code.

### GG-CC-002

Infrastruktur-Adapter DUERFEN KEINE Businesslogik enthalten.

Akzeptanz: Adapter uebersetzen Protokolle, Datenformate und technische Fehler in
Ports und Domain-Typen. Fachliche Entscheidungen liegen im Simulationskern oder
in Geraetemodellen.

### GG-CC-003

Domain-Module DUERFEN KEINE Framework-Abhaengigkeiten enthalten.

Akzeptanz: Domain-Code importiert keine Web-, Datenbank-, Messaging-,
Container- oder UI-Frameworks.

### GG-CC-004

Module DUERFEN KEINE zyklischen Abhaengigkeiten besitzen.

Akzeptanz: Eine automatisierte Modul- oder Importanalyse meldet Zyklen als
Architekturverletzung.

### GG-CC-005

Fachliche Namen MUESSEN eindeutig und sprechend sein.

Akzeptanz: Oeffentliche Typen, Ports, Events, Commands, Metriken und
Qualitaetszustaende verwenden Begriffe aus Szenarioformat, Datenmodell oder
Dokumentation konsistent.

### GG-CC-006

Statische Utility-God-Classes DUERFEN NICHT eingefuehrt werden.

Akzeptanz: Wiederverwendbare Logik wird fachlich verortet oder als kleine,
zweckgebundene Funktion bzw. Komponente implementiert.

### GG-CC-007

Immutable Domain-Objekte SOLLTEN bevorzugt werden.

Akzeptanz: Events, Commands, Telemetriepunkte, Snapshots und Szenario-Modelle
sind unveraenderlich oder behandeln Mutation explizit und lokal begrenzt.

### GG-CC-008

Fehlerbehandlung MUSS explizit erfolgen.

Akzeptanz: Fehlerpfade liefern typisierte Fehler, Statuswerte oder dokumentierte
Exceptions. Fehler werden nicht stillschweigend verschluckt und nicht nur ueber
unklassifizierte Strings signalisiert.

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

## GG-RT-001

Die Plattform MUSS Simulationszyklen von 10 ms bis 1 s konfigurieren koennen.

Akzeptanz: Die Demo-Konfiguration startet erfolgreich mit 10 ms, 100 ms und 1 s
Tick-Groesse. Fuer 100 ms und 1 s Tick-Groesse verarbeitet die Demo 1.000 Ticks
ohne Backpressure. Fuer 10 ms Tick-Groesse dokumentiert der Healthcheck
Tick-Dauer, p95-Jitter, verpasste Ticks und Backpressure-Status; 10 ms ist fuer
den MVP ein Mess- und Diagnosemodus, kein garantierter Echtzeitbetrieb.

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
explizite Dezimalpraezision und keine nichtdeterministischen IDs. Fuer den MVP
werden Zeitstempel als ISO-8601-UTC oder als ganzzahlige Simulationszeit in ms,
Sequenzen als Integer und Messwerte mit maximal sechs Nachkommastellen
kanonisiert.

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

Akzeptanz: Der Geraetetyp `battery` hat ein Minimalmodell, ein Beispiel im
Szenarioformat und einen deterministischen Smoke-Test.

### GG-DEV-011

Die Plattform MUSS PV-Anlagen simulieren koennen.

Akzeptanz: Der Geraetetyp `pv` hat ein Minimalmodell, ein Beispiel im
Szenarioformat und einen deterministischen Smoke-Test.

### GG-DEV-012

Die Plattform MUSS Netzanschlusspunkte simulieren koennen.

Akzeptanz: Der Geraetetyp `grid_connection` hat ein Minimalmodell, ein Beispiel
im Szenarioformat und einen deterministischen Smoke-Test.

### GG-DEV-013

Die Plattform MUSS Lastprofile simulieren koennen.

Akzeptanz: Der Geraetetyp `load` hat ein Minimalmodell, ein Beispiel im
Szenarioformat und einen deterministischen Smoke-Test.

### GG-DEV-014

Die Plattform MUSS Smart Meter simulieren koennen.

Akzeptanz: Der Geraetetyp `smart_meter` hat ein Minimalmodell, ein Beispiel im
Szenarioformat und einen deterministischen Smoke-Test.

### GG-DEV-015

Die Plattform SOLLTE EV-Ladepunkte simulieren koennen.

Akzeptanz: Wenn der Geraetetyp `ev_charger` implementiert wird, hat er ein
Minimalmodell, ein Beispiel im Szenarioformat und einen deterministischen
Smoke-Test.

### GG-DEV-016

Die Plattform SOLLTE Transformatoren simulieren koennen.

Akzeptanz: Wenn der Geraetetyp `transformer` implementiert wird, hat er ein
Minimalmodell, ein Beispiel im Szenarioformat und einen deterministischen
Smoke-Test.

### GG-DEV-017

Die Plattform SOLLTE Windkraftanlagen simulieren koennen.

Akzeptanz: Wenn der Geraetetyp `wind_turbine` implementiert wird, hat er ein
Minimalmodell, ein Beispiel im Szenarioformat und einen deterministischen
Smoke-Test.

### GG-DEV-018

Die Plattform SOLLTE Dieselgeneratoren simulieren koennen.

Akzeptanz: Wenn der Geraetetyp `diesel_generator` implementiert wird, hat er ein
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
und `max_soc_pct` werden deterministisch behandelt: Leistungsbefehle innerhalb
der SOC-Grenzen werden auf die zulaessige Leistung begrenzt und erhalten den
Status `limited`; Befehle, die eine SOC-Grenze verletzen wuerden, werden
abgelehnt und erhalten den Status `rejected`. In beiden Faellen wird ein Alarm
mit Zielgeraet, Grenzwert und resultierendem Status erzeugt.

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

Akzeptanz: Wenn Inselnetzmodi implementiert sind, sind sie ueber ein eigenes
Modell aktivierbar und erzeugen dokumentierte Telemetrie zu Netzstatus,
Frequenz und Versorgungsbilanz.

## GG-GRID-006

Die Plattform SOLLTE Transformatorgrenzen simulieren koennen.

Akzeptanz: Wenn Transformatorgrenzen implementiert sind, erzeugt das Modell
Telemetrie zu Auslastung, Grenzwerten und Qualitaetsstatus.

## GG-GRID-007

Die Plattform SOLLTE Blindleistungsfluesse simulieren koennen.

Akzeptanz: Wenn Blindleistungsfluesse implementiert sind, exportiert das Modell
mindestens Wirk-, Blind- und Scheinleistung mit dokumentierten Einheiten und
Annahmen.

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

Szenarien MUESSEN zeitbasierte Ereignisse unterstuetzen.

Akzeptanz: Ereignisse koennen mit Simulationszeit, Ziel, Typ, Payload und
optionalem Wiederherstellungsverhalten definiert werden und werden vor dem ersten
Tick validiert.

## GG-SCN-006

Szenarien MUESSEN Fault Injection unterstuetzen.

Akzeptanz: Das Szenarioformat kann Faults mit Startzeit, Dauer, Ziel, Fault-Typ,
Payload und Recovery-Verhalten ausdruecken; ungueltige Fault-Definitionen werden
vor dem ersten Tick als Validierungsfehler gemeldet.

## GG-SCN-007

Szenarien SOLLTEN Replay-Verweise unterstuetzen.

Akzeptanz: Wenn Replay-Verweise implementiert sind, enthalten sie Quelle,
Format, Zeitabbildung und Validierungsstatus und koennen vor Simulationsstart
auf Existenz und Schema-Kompatibilitaet geprueft werden.

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

Akzeptanz: Wenn beschleunigte Wiedergabe implementiert ist, kann der Faktor ueber
API und CLI gesetzt werden und erzeugt einen dokumentierten Status.

## GG-REPLAY-005

Replay-Systeme SOLLTEN Pause/Resume unterstuetzen.

Akzeptanz: Wenn Pause/Resume fuer Replay implementiert ist, kann ein Replay ueber
API und CLI pausiert und fortgesetzt werden, ohne Tick-Reihenfolge oder
Replay-Diff zu veraendern.

## GG-REPLAY-006

Replay-Systeme SOLLTEN Delta-Analysen ermoeglichen.

Akzeptanz: Wenn Delta-Analysen implementiert sind, liefern sie ueber API oder CLI
einen maschinenlesbaren Status und eine Liste fachlicher Abweichungen.

## GG-REPLAY-007

Replay-Diffs MUESSEN fachliche und volatile Felder unterscheiden.

Akzeptanz: Diff-Ausgaben enthalten Pfad, erwarteten Wert, tatsaechlichen Wert,
Tick, Geraete-ID und Klassifikation der Abweichung.

---

# 14. Fault Injection

## GG-FAULT-001

Die Plattform MUSS Kommunikationsausfaelle simulieren koennen.

Akzeptanz: Ein Kommunikationsausfall kann im Szenario mit Startzeit, Dauer,
Ziel, betroffenen Ein- oder Ausgangskanaelen und Recovery-Verhalten definiert
werden. Waehrend des Ausfalls werden betroffene Werte als `missing` oder
`stale` markiert und mindestens ein Alarm erzeugt.

## GG-FAULT-002

Die Plattform MUSS Stale Data simulieren koennen.

Akzeptanz: Ein Stale-Data-Fault kann fuer ein Ziel und eine Metrik aktivieren,
dass der letzte gueltige Wert weitergeliefert wird, bis `max_age` ueberschritten
ist. Danach wird der Qualitaetsstatus `stale` gesetzt.

## GG-FAULT-003

Die Plattform MUSS NaN-Werte simulieren koennen.

Akzeptanz: Ein NaN-Fault kann fuer ein Ziel und eine Metrik einen nicht
numerischen Eingangswert erzeugen. Der Wert wird nicht ungeprueft in den
Geraetezustand uebernommen, sondern mit Qualitaetsstatus `nan` und Alarm
protokolliert.

## GG-FAULT-004

Die Plattform MUSS Frequenzabfaelle simulieren koennen.

Akzeptanz: Ein Frequenzabfall kann mit Startzeit, Dauer, Zielnetz,
Frequenzwert oder Delta und Recovery-Verhalten definiert werden und erzeugt
Grid-Telemetrie sowie einen Alarm.

## GG-FAULT-005

Die Plattform MUSS Spannungseinbrueche simulieren koennen.

Akzeptanz: Ein Spannungseinbruch kann mit Startzeit, Dauer, Zielnetz,
Spannungswert oder Delta und Recovery-Verhalten definiert werden und erzeugt
Grid-Telemetrie sowie einen Alarm.

## GG-FAULT-006

Die Plattform SOLLTE Modbus-Timeouts simulieren koennen.

Akzeptanz: Wenn der Modbus-Adapter implementiert ist, kann ein Timeout mit
Startzeit, Dauer, Zielregister und Recovery-Verhalten definiert werden. Der
Adapter liefert einen dokumentierten Fehlerstatus und erzeugt einen Alarm.

## GG-FAULT-007

Die Plattform MUSS Geraeteausfaelle simulieren koennen.

Akzeptanz: Ein Geraeteausfall kann mit Startzeit, Dauer, Zielgeraet,
Ausfallmodus und Recovery-Verhalten definiert werden. Das Zielgeraet liefert
waehrend des Ausfalls dokumentierte Qualitaetszustaende und erzeugt einen Alarm.

## GG-FAULT-008

Die Plattform SOLLTE SOC-Spruenge simulieren koennen.

Akzeptanz: Wenn SOC-Spruenge implementiert sind, koennen Sprunghoehe, Startzeit,
Zielbatterie und Recovery-Verhalten im Szenario definiert werden. Der Sprung
wird als Fault-Telemetrie und Alarm protokolliert.

## GG-FAULT-009

Die Plattform SOLLTE Netzwerkpartitionen simulieren koennen.

Akzeptanz: Wenn Netzwerkpartitionen implementiert sind, koennen betroffene
Adapter, Startzeit, Dauer und Recovery-Verhalten im Szenario definiert werden.
Betroffene Nachrichten werden deterministisch verworfen, verzoegert oder als
fehlgeschlagen markiert.

## GG-FAULT-010

Fault Injection MUSS deterministisch replaybar sein.

Akzeptanz: Faults werden als Events mit Simulationszeit und Sequenznummer in den
Laufmetadaten protokolliert und erzeugen bei Replay dieselben fachlichen
Auswirkungen.

---

# 15. Multi-Agent-System

## GG-AGENT-001

Die Plattform SOLLTE agentenbasierte Steuerungsmodelle unterstuetzen.

Akzeptanz: Wenn agentenbasierte Steuerung implementiert ist, kann mindestens ein
Agent ueber eine dokumentierte Schnittstelle Steuerentscheidungen erzeugen.

## GG-AGENT-002

Agenten SOLLTEN isoliert testbar sein.

Akzeptanz: Wenn Agenten implementiert sind, koennen sie ohne laufende
Gesamtsimulation mit deterministischen Eingaben getestet werden.

## GG-AGENT-003

Agenten SOLLTEN deterministisch replaybar sein.

Akzeptanz: Wenn Agenten Replay unterstuetzen, erzeugt derselbe Eingabeverlauf mit
gleichem Seed dieselben Nachrichten und Steuerbefehle.

## GG-AGENT-004

Agenten SOLLTEN standardisierte Nachrichten verwenden.

Akzeptanz: Wenn Agentennachrichten implementiert sind, enthalten sie
Simulationszeit, Sender, Empfaenger, Nachrichtentyp, Payload und Sequenznummer.

## GG-AGENT-005

Die Plattform SOLLTE konkurrierende Regelstrategien unterstuetzen.

Akzeptanz: Wenn konkurrierende Regelstrategien implementiert sind, ist die
Priorisierung oder Konfliktaufloesung dokumentiert und deterministisch getestet.

## GG-AGENT-006

Agenten SOLLTEN lokale Zustaende verwalten koennen.

Akzeptanz: Wenn Agentenzustaende implementiert sind, koennen sie exportiert,
snapshot-basiert wiederhergestellt und im Replay verglichen werden.

## GG-AGENT-007

Agenten SOLLTEN Zeitrestriktionen unterstuetzen.

Akzeptanz: Wenn Zeitrestriktionen implementiert sind, werden Deadlines,
abgelaufene Entscheidungen und resultierende Statuswerte deterministisch
behandelt.

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

Die Plattform SOLLTE MQTT als Simulationsadapter unterstuetzen.

Akzeptanz: Wenn MQTT implementiert ist, dokumentiert der Adapter Topic-Schema,
Payload-Format, QoS-Annahmen, Publish-/Subscribe-Richtung, Fehlerverhalten und
Zuordnung zu Simulationszeit. Ein deterministischer Adapter-Smoke-Test weist
Nachrichtenannahme und Telemetrieausgabe nach.

## GG-MODB-001

Die Plattform SOLLTE Modbus TCP als Simulationsadapter unterstuetzen.

Akzeptanz: Wenn Modbus TCP implementiert ist, dokumentiert der Adapter
Register-Mapping, Datentypen, Byte-Reihenfolge, Lese-/Schreiboperationen,
Timeout-Verhalten und Zuordnung zu Simulationszeit. Ein deterministischer
Adapter-Smoke-Test weist mindestens einen Lese- und einen Schreibpfad nach.

## GG-OPCUA-001

Die Plattform SOLLTE OPC-UA als Simulationsadapter unterstuetzen.

Akzeptanz: Wenn OPC-UA implementiert ist, dokumentiert der Adapter Node-IDs,
Datentypen, Lese-/Schreibpfade, Fehlerverhalten und Zuordnung zu
Simulationszeit.

## GG-DNP3-001

Die Plattform SOLLTE DNP3 als Simulationsadapter unterstuetzen.

Akzeptanz: Wenn DNP3 implementiert ist, dokumentiert der Adapter Points,
Variations, Qualitaetsflags, Fehlerverhalten und Zuordnung zu Simulationszeit.

## GG-IEC-001

Die Plattform SOLLTE IEC61850 als Simulationsadapter unterstuetzen.

Akzeptanz: Wenn IEC61850 implementiert ist, dokumentiert der Adapter Logical
Nodes, Datenattribute, Report-/Control-Verhalten, Fehlerverhalten und Zuordnung
zu Simulationszeit.

## GG-SNMP-001

Die Plattform SOLLTE SNMP als Simulationsadapter fuer Device-Management-
und Telemetrie-Use-Cases unterstuetzen.

Akzeptanz: Wenn SNMP implementiert ist, dokumentiert der Adapter
OID-/MIB-Mapping, SNMP-Version, Security-Annahmen, Polling-/Set-/Trap-
Richtung, Fehlerverhalten und Zuordnung zu Simulationszeit. Ein
deterministischer Adapter-Smoke-Test weist mindestens einen Polling-
Telemetriepfad nach; Schreibpfade werden nur aktiviert, wenn das
Adapter-Profil sie ausdruecklich vorsieht.

## GG-LWM2M-001

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

## GG-UI-001

Die Plattform MUSS ein Web-UI fuer lokale Demo- und Testumgebungen bereitstellen.

Akzeptanz: Das UI ist nach `docker compose up` lokal erreichbar und zeigt den
Systemstatus der Demo-Umgebung an.

## GG-UI-002

Das UI MUSS Live-Telemetrie visualisieren koennen.

Akzeptanz: Das UI zeigt waehrend eines laufenden Demo-Szenarios aktuelle
Telemetriepunkte mit Geraet, Metrik, Wert, Einheit, Simulationszeit und
Qualitaetsstatus an.

## GG-UI-003

Das UI MUSS Zeitreihen visualisieren koennen.

Akzeptanz: Das UI zeigt fuer mindestens eine Leistungsmetrik und eine SOC-Metrik
einen zeitlich sortierten Verlauf aus persistierten oder live gepufferten
Telemetriedaten an.

## GG-UI-004

Das UI MUSS Replay-Steuerung unterstuetzen.

Akzeptanz: Das UI bietet fuer einen vorhandenen Lauf mindestens Start, Pause,
Resume, Stop und Anzeige des Replay-Status an.

## GG-UI-005

Das UI MUSS Alarme visualisieren koennen.

Akzeptanz: Das UI zeigt Alarmzeit, Ziel, Schweregrad, Code, Nachricht und
aktuellen Status in einer aktualisierbaren Tabelle an.

## GG-UI-006

Das UI SOLLTE Geraete grafisch darstellen koennen.

Akzeptanz: Wenn grafische Geraetedarstellung implementiert ist, zeigt das UI
mindestens die MVP-Geraetetypen mit ID, Typ, aktuellem Zustand und
Qualitaetsstatus an.

## GG-UI-007

Das UI SOLLTE Fault Injection ausloesen koennen.

Akzeptanz: Wenn Fault Injection im UI implementiert ist, koennen Fault-Typ, Ziel,
Startzeit, Dauer und Recovery-Verhalten eingegeben und vor Ausloesung validiert
werden.

## GG-UI-008

Das UI SOLLTE Simulationszustaende visualisieren koennen.

Akzeptanz: Wenn diese Funktion implementiert ist, zeigt das UI mindestens
Laufstatus, aktuelle Simulationszeit, Tick-Zaehler und Zustand des
Simulationsdienstes.

## GG-UI-009

Das UI MUSS Datenqualitaet sichtbar machen.

Akzeptanz: Telemetriepunkte mit `stale`, `invalid`, `nan`, `missing` oder
`fault_injected` werden in Tabellen und Zeitreihen unterscheidbar dargestellt.

---

# 18. Persistenz

## GG-PERSIST-001

Die Plattform MUSS Zeitreihen speichern koennen.

Akzeptanz: Telemetriepunkte koennen mit Lauf-ID, Simulationszeit, Geraet, Metrik,
Wert, Einheit, Qualitaetsstatus, Quelle und Sequenz persistiert und fuer einen
Lauf wieder abgefragt werden.

## GG-PERSIST-002

Die Plattform MUSS Replay-Daten speichern koennen.

Akzeptanz: Importierte Replay-Samples werden mit Originalzeitstempel,
Simulationszeit, Quelle, Geraet, Metrik, Wert, Einheit und Import-Sequenz
persistiert.

## GG-PERSIST-003

Die Plattform MUSS Szenariodaten speichern koennen.

Akzeptanz: Ein gestartetes Szenario wird mit Schema-Version, kanonischem
Szenario-Hash und kanonischer Szenario-Repraesentation gespeichert.

## GG-PERSIST-004

Die Plattform MUSS Alarmhistorien speichern koennen.

Akzeptanz: Alarme werden mit Lauf-ID, Simulationszeit, Ziel, Code, Schweregrad,
Nachricht, Status und optionaler Fault-ID gespeichert und laufbezogen abgefragt.

## GG-PERSIST-005

Die Plattform MUSS PostgreSQL unterstuetzen.

Akzeptanz: Der Docker-Compose-Stack startet PostgreSQL als verpflichtenden
MVP-Speicher, wendet Migrationen an und besteht einen Healthcheck.

## GG-PERSIST-006

Die Plattform SOLLTE TimescaleDB unterstuetzen.

Akzeptanz: Wenn TimescaleDB implementiert ist, dokumentiert der Adapter Schema,
Hypertables oder Indizes, Migrationspfad und Abfrageverhalten fuer Laufdaten.

## GG-PERSIST-007

Die Plattform SOLLTE InfluxDB unterstuetzen.

Akzeptanz: Wenn InfluxDB implementiert ist, dokumentiert der Adapter Buckets,
Measurements, Tags, Retention-Annahmen und Abfrageverhalten fuer Laufdaten.
Persistierte Datensaetze enthalten Lauf-ID, Simulationszeit, Erfassungszeit,
Quelle, Payload und Schema-Version. PostgreSQL ist der verpflichtende
MVP-Speicher; TimescaleDB und InfluxDB sind optionale Adapter. Erfassungszeit
ist ein persistiertes Betriebsmetadatum und wird in kanonischen Replay- und
Golden-File-Vergleichen als volatil behandelt.

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

Die Plattform SOLLTE OpenTelemetry fuer Traces und Metriken unterstuetzen.

Akzeptanz: Wenn OpenTelemetry implementiert ist, exportiert die Demo
OTLP-kompatible Traces und Metriken oder stellt einen konfigurierbaren
OTLP-Exporter bereit.

## GG-OTEL-002

Die Plattform MUSS strukturierte Logs unterstuetzen.

Akzeptanz: Logs enthalten Zeitstempel, Level, Lauf-ID, Modul, Event-ID und
Nachricht.

## GG-OTEL-003

Die Plattform MUSS Metriken exportieren koennen.

Akzeptanz: Exportiert werden mindestens Tick-Dauer, Event-Queue-Laenge,
verarbeitete Telemetriepunkte/s, Fehleranzahl und Replay-Diff-Status.

## GG-OTEL-004

Die Plattform SOLLTE Traces exportieren koennen.

Akzeptanz: Wenn Tracing implementiert ist, kann ein Tick ueber Scheduler,
Geraetemodell, Adapter und Persistenz tracebar sein.

---

# 20. Sicherheitsanforderungen

## GG-SAFE-001

Ungueltige Daten MUESSEN erkannt werden.

Akzeptanz: Schema-, Wertebereichs- und Einheitenfehler werden vor Uebernahme in
den Simulationskern als Validierungsfehler oder Qualitaetsstatus `invalid`
gemeldet und erzeugen einen nachvollziehbaren Fehler- oder Alarmdatensatz.

## GG-SAFE-002

NaN-Werte DUERFEN NICHT ungeprueft verarbeitet werden.

Akzeptanz: NaN-Werte werden vor Zustandsfortschreibung erkannt, als
Qualitaetsstatus `nan` serialisiert und erzeugen mindestens einen Alarm oder
einen typisierten Fehler.

## GG-SAFE-003

Kommunikationsausfaelle MUESSEN erkannt werden.

Akzeptanz: Kommunikationsausfaelle erzeugen einen dokumentierten Fehlerstatus,
betroffene Telemetrie wird als `missing` oder `stale` markiert und ein Alarm mit
Ziel, Startzeit und Ursache wird erzeugt.

## GG-SAFE-004

Veraltete Daten MUESSEN markiert werden.

Akzeptanz: Werte, deren Simulationszeitstempel die konfigurierte `max_age`
ueberschreiten, erhalten deterministisch den Qualitaetsstatus `stale`.

## GG-SAFE-005

Die Plattform SOLLTE sichere Fallback-Zustaende unterstuetzen.

Akzeptanz: Wenn Fallback-Zustaende implementiert sind, dokumentiert jeder
betroffene Geraetetyp Ausloeser, Zielzustand, Telemetrie und Recovery-Verhalten.

## GG-SAFE-006

Nichtdeterministische Simulationslaeufe SOLLTEN erkannt werden.

Akzeptanz: Wenn Erkennung nichtdeterministischer Laeufe implementiert ist,
meldet die Plattform Replay-Diff, volatile Felder, betroffene Ticks und
Abweichungsklassifikation maschinenlesbar.

## GG-SAFE-007

Die Plattform MUSS Simulations- und Produktivkontexte klar trennen.

Akzeptanz: UI, API-Dokumentation und Adapterkonfiguration kennzeichnen
Simulationsadapter als nicht fuer produktive Anlagensteuerung freigegeben.

## GG-SAFE-008

Die Plattform MUSS Eingaben an externen Schnittstellen validieren.

Akzeptanz: REST-, WebSocket- und alle implementierten Adapter-Eingaben werden
gegen Schema, Wertebereiche und Zielressourcen validiert, bevor sie in den
Simulationskern gelangen.

---

# 21. Testbarkeit

## GG-TEST-001

Die Plattform MUSS Replay-basierte Tests unterstuetzen.

Akzeptanz: Ein automatisierter Test kann einen gespeicherten oder importierten
Lauf erneut ausfuehren und einen Replay-Diff als maschinenlesbares Ergebnis
erzeugen.

## GG-TEST-002

Die Plattform MUSS deterministische Tests unterstuetzen.

Akzeptanz: Ein automatisierter Test fuehrt dasselbe Referenzszenario zweimal mit
gleichem Seed aus und vergleicht kanonische Ergebnisartefakte.

## GG-TEST-003

Die Plattform MUSS Integrationstests unterstuetzen.

Akzeptanz: Der CI- oder Abnahmebefehl enthaelt Integrationstests fuer API,
Persistenz und Telemetriepfad der Demo.

## GG-TEST-004

Die Plattform SOLLTE HIL-Tests unterstuetzen.

Akzeptanz: Wenn HIL-Tests implementiert sind, sind Testgrenzen,
Simulationsadapter, erwartete Signale und deterministisches Replay-Verhalten
dokumentiert.

## GG-TEST-005

Die Plattform SOLLTE Property-basierte Tests unterstuetzen.

Akzeptanz: Wenn Property-basierte Tests implementiert sind, pruefen sie
Invarianten fuer Scheduler, Szenario-Validierung, Replay-Diff oder
Geraetemodelle mit reproduzierbaren Seeds.

## GG-TEST-006

Replay-Diffs SOLLTEN automatisiert vergleichbar sein.

Akzeptanz: Wenn automatisierte Replay-Diff-Vergleiche implementiert sind, liefern
sie Exit-Code, maschinenlesbaren Status und eine Liste fachlicher Abweichungen.

## GG-TEST-007

Die Plattform MUSS eine Requirements-Matrix fuer MUSS-Anforderungen pflegen.

Akzeptanz: Jede MUSS-Anforderung verweist auf mindestens einen Test,
Architekturentscheid oder eine Demo-Abnahmepruefung.

## GG-TEST-008

Die Plattform MUSS Golden-Files fuer deterministische Referenzszenarien
unterstuetzen.

Akzeptanz: Golden-Files werden kanonisch erzeugt und koennen in CI gegen neue
Simulationsergebnisse verglichen werden.

## 21.1 Teststrategie

### GG-TEST-009

Automatisierte Tests MUESSEN verpflichtender Bestandteil der Entwicklung sein.

Akzeptanz: Der dokumentierte Abnahmebefehl fuehrt automatisierte Tests aus und
liefert einen maschinenlesbaren Status.

### GG-TEST-010

Unit-Tests MUESSEN unabhaengig ausfuehrbar sein.

Akzeptanz: Unit-Tests benoetigen keine Datenbank, keine Netzwerkdienste und
keine externen Live-Systeme.

### GG-TEST-011

Integrationstests MUESSEN containerisiert ausfuehrbar sein.

Akzeptanz: Integrationstests fuer API, Persistenz und Telemetriepfad laufen in
der lokalen Container-Umgebung oder einer dokumentierten aequivalenten
CI-Umgebung.

### GG-TEST-012

Architekturtests MUESSEN Modulgrenzen pruefen.

Akzeptanz: Architekturtests pruefen mindestens Domain-zu-Adapter-Abhaengigkeiten,
Framework-Freiheit der Domain und zyklische Modulabhaengigkeiten.

### GG-TEST-013

Replay-Funktionalitaeten MUESSEN testbar sein.

Akzeptanz: Replay-Start, Replay-Diff, Golden-File-Vergleich,
Zeitmultiplikatoren und volatile Feldklassifikation sind durch Tests oder
Abnahmepruefungen abgedeckt.

### GG-TEST-014

Sicherheitsrelevante Funktionen MUESSEN getestet werden.

Akzeptanz: Validierung externer Eingaben, NaN-Behandlung, stale Daten,
Kommunikationsausfaelle und Trennung von Simulations- und Produktivkontexten
sind durch automatisierte Tests oder reproduzierbare Abnahmepruefungen belegt.

### GG-TEST-015

Event-Processing MUSS getestet werden.

Akzeptanz: Tests pruefen Event-Sortierung, Tie-Breaking, Sequenznummern,
Tick-Commit-Reihenfolge und deterministisches Replay.

### GG-TEST-016

Fehlerfaelle MUESSEN getestet werden.

Akzeptanz: Tests decken ungueltige Szenarien, unbekannte Geraete, ungueltige
Einheiten, Adapterfehler, Persistenzfehler und abgelehnte Steuerbefehle ab.

### GG-TEST-017

Datenschutz-, Maskierungs- und Aufbewahrungsregeln SOLLTEN getestet werden.

Akzeptanz: Wenn solche Regeln implementiert sind, pruefen Tests Maskierung,
Export, Loeschung, Aufbewahrungsfristen und Ausschluss volatiler oder sensibler
Felder aus kanonischen Vergleichsartefakten.

### GG-TEST-018

Replay-Freigaben, Whitelists, Dry-Run und Rate-Limits SOLLTEN getestet werden.

Akzeptanz: Wenn diese Schutzfunktionen implementiert sind, pruefen Tests
Freigabelogik, erlaubte Ziele, Dry-Run ohne Zustandsaenderung und deterministisch
behandelte Rate-Limits.

## 21.2 Testarten

### GG-TESTTYPE-001

Die Plattform MUSS Unit-Tests unterstuetzen.

Akzeptanz: Unit-Tests koennen lokal ohne Container gestartet werden.

### GG-TESTTYPE-002

Die Plattform MUSS Integrationstests unterstuetzen.

Akzeptanz: Integrationstests pruefen mindestens API, Persistenz und Telemetrie
ueber reale Adapter- oder Containergrenzen.

### GG-TESTTYPE-003

Die Plattform MUSS Architekturtests unterstuetzen.

Akzeptanz: Architekturtests pruefen Modulgrenzen und Abhaengigkeitsrichtung.

### GG-TESTTYPE-004

Die Plattform SOLLTE Contract-Tests unterstuetzen.

Akzeptanz: Wenn Contract-Tests implementiert sind, pruefen sie OpenAPI-Schemas,
WebSocket-Nachrichten und implementierte Adaptervertraege.

### GG-TESTTYPE-005

Die Plattform MUSS End-to-End-Tests fuer die Demo unterstuetzen.

Akzeptanz: Ein E2E-Test startet die Demo, prueft Healthcheck, Szenarioausfuehrung,
Telemetrie, Persistenz und Replay-Diff.

### GG-TESTTYPE-006

Die Plattform SOLLTE Performance-Tests unterstuetzen.

Akzeptanz: Wenn Performance-Tests implementiert sind, pruefen sie die
Referenzumgebung, Tick-Dauer, Jitter, Telemetriepunkte/s und Replay-Diff-Status.

### GG-TESTTYPE-007

Die Plattform SOLLTE Security-Tests unterstuetzen.

Akzeptanz: Wenn Security-Tests implementiert sind, pruefen sie
Dependency-Scanning, bekannte kritische Schwachstellen und Eingabevalidierung.

## 21.3 Coverage-Anforderungen

### GG-COV-001

Die Plattform SOLLTE eine Mindest-Testabdeckung von 90 Prozent erreichen.

Akzeptanz: Der Coverage-Report weist die Gesamt-Coverage aus und dokumentiert
Abweichungen.

### GG-COV-002

Die Plattform SOLLTE mindestens 85 Prozent Branch-Coverage erreichen.

Akzeptanz: Der Coverage-Report weist Branch-Coverage separat aus.

### GG-COV-003

Kritische Domaenenlogik MUSS fuer den MVP mindestens 90 Prozent Coverage
erreichen.

Akzeptanz: Simulationskern, Scheduler, Replay-Diff, Szenario-Validierung und
Batteriemodell werden als kritische Domaenenlogik klassifiziert und im
Coverage-Report separat ausgewiesen. Zielwert fuer spaetere Releases ist 95
Prozent.

### GG-COV-004

Coverage DARF NICHT kuenstlich erzeugt werden.

Akzeptanz: Tests ohne fachliche Assertion, reine Getter-/Setter-Ausfuehrung und
Snapshots ohne Verhaltenspruefung gelten nicht als Qualitaetsnachweis.

### GG-COV-005

Getter/Setter-only-Tests gelten NICHT als ausreichender Qualitaetsnachweis.

Akzeptanz: Tests fuer Domain-Objekte pruefen Invarianten, Validierung,
Serialisierung oder fachliches Verhalten.

## 21.4 Quality Gates

### GG-QG-001

Der Build SOLLTE bei unterschrittener Coverage fehlschlagen.

Akzeptanz: Wenn Coverage-Gates aktiviert sind, bricht der CI-Build bei
Unterschreitung der dokumentierten Schwellwerte ab oder verlangt eine
dokumentierte Ausnahme.

### GG-QG-002

Der Build DARF bei kritischen oder hohen Security-Issues ohne dokumentierte
Ausnahme nicht erfolgreich sein.

Akzeptanz: Security-Scanning liefert Severity, betroffene Komponente und
Ausnahmeentscheidung. Kritische und hohe Befunde blockieren den Build, sofern
keine dokumentierte Ausnahme existiert.

### GG-QG-003

Der Build DARF bei Architekturverletzungen nicht erfolgreich sein.

Akzeptanz: Verletzungen von hexagonalen Modulgrenzen, Framework-Freiheit der
Domain oder zyklischen Abhaengigkeiten blockieren den Build.

### GG-QG-004

Der Build DARF bei fehlschlagenden Tests nicht erfolgreich sein.

Akzeptanz: Unit-, Integrations-, Architektur- und Demo-Abnahmetests liefern
einen nicht erfolgreichen CI-Status, wenn sie fehlschlagen.

### GG-QG-005

Der Build SOLLTE bei statischen Analysefehlern fehlschlagen.

Akzeptanz: Wenn statische Analyse aktiviert ist, blockieren Fehler oberhalb der
dokumentierten Severity-Schwelle den Build.

### GG-QG-006

Der Build DARF bei fehlgeschlagener OpenAPI-Validierung nicht erfolgreich sein.

Akzeptanz: OpenAPI-Spezifikation, Request-Schemas und Response-Schemas werden in
CI validiert.

### GG-QG-007

Der Build SOLLTE bei fehlgeschlagenen Datenschutz- und
Replay-Sicherheitspruefungen fehlschlagen.

Akzeptanz: Wenn Datenschutz- oder Replay-Sicherheitsregeln implementiert sind,
blockieren fehlgeschlagene Pruefungen den Build oder verlangen eine dokumentierte
Ausnahme.

## 21.5 Codeanalyse und Architekturvalidierung

### GG-QA-001

Statische Codeanalyse MUSS fuer Produktionscode verfuegbar sein.

Akzeptanz: Ein dokumentierter Befehl fuehrt statische Analyse lokal oder in CI
aus.

### GG-QA-002

SonarQube-Unterstuetzung SOLLTE bereitgestellt werden.

Akzeptanz: Wenn SonarQube genutzt wird, sind Projektkonfiguration,
Coverage-Import und Quality-Gate-Anbindung dokumentiert.

### GG-QA-003

Code-Smell-Pruefungen SOLLTEN Teil der statischen Analyse sein.

Akzeptanz: Die Analyse meldet Code Smells mit Datei, Regel und Severity.

### GG-QA-004

Duplication-Pruefungen SOLLTEN Teil der statischen Analyse sein.

Akzeptanz: Die Analyse weist duplizierte Bloecke aus und dokumentiert
Schwellwerte.

### GG-QA-005

Pruefungen auf Sicherheitsluecken MUESSEN fuer Abhaengigkeiten verfuegbar sein.

Akzeptanz: Ein dokumentierter Befehl oder CI-Schritt prueft direkte und
transitive Abhaengigkeiten auf bekannte Schwachstellen.

### GG-QA-006

Zyklische Abhaengigkeiten MUESSEN automatisiert erkannt werden.

Akzeptanz: Die Architekturvalidierung meldet Zyklen zwischen Modulen oder
Paketen als Build-Artefakt.

### GG-ARCHTEST-001

Hexagonale Modulgrenzen MUESSEN automatisiert geprueft werden.

Akzeptanz: Architekturtests stellen sicher, dass Domain-Module keine Adapter und
Adapter die Domain nur ueber Ports verwenden.

### GG-ARCHTEST-002

Infrastruktur DARF NICHT von konkreter Domain-Implementierung abhaengen, wenn
ein Port definiert ist.

Akzeptanz: Infrastrukturmodule importieren Port-Definitionen und DTOs, aber
keine internen Domain-Services oder konkreten Geraetemodell-Implementierungen,
sofern ein Port existiert.

### GG-ARCHTEST-003

Adapter DUERFEN KEINE Domaenenlogik enthalten.

Akzeptanz: Architekturtests und Code-Review pruefen, dass Adapter nur
Protokoll-, Format-, Transport- und Fehleruebersetzung enthalten.

### GG-ARCHTEST-004

Ports MUESSEN framework-unabhaengig bleiben.

Akzeptanz: Port-Definitionen importieren keine Web-, Persistenz-, Messaging-
oder UI-Frameworks.

### GG-ARCHTEST-005

Architekturtests MUESSEN Teil der CI-Pipeline sein.

Akzeptanz: Die CI-Pipeline fuehrt Architekturtests aus und veroeffentlicht den
Status als Build-Ergebnis.

---

# 22. CI/CD-Anforderungen

## GG-CICD-001

Die Plattform MUSS eine automatisierte Build-Pipeline bereitstellen.

Akzeptanz: Die Pipeline baut alle produktiven Artefakte reproduzierbar aus dem
Repository.

## GG-CICD-002

Die Pipeline MUSS Tests automatisch ausfuehren.

Akzeptanz: Unit-, Integrations-, Architektur- und Demo-Abnahmetests laufen in
der Pipeline oder sind dort als getrennte, dokumentierte Jobs verfuegbar.

## GG-CICD-003

Die Pipeline MUSS Quality Gates automatisch auswerten.

Akzeptanz: Teststatus, Architekturtests, OpenAPI-Validierung und Security-Scan
werden als maschinenlesbare Gate-Ergebnisse ausgewiesen.

## GG-CICD-004

Builds SOLLTEN containerisiert ausfuehrbar sein.

Akzeptanz: Die Pipeline kann Build- und Testschritte in dokumentierten
Container-Images ausfuehren.

## GG-CICD-005

Security-Scanning MUSS in der Pipeline verfuegbar sein.

Akzeptanz: Die Pipeline kann Abhaengigkeiten und Container-Images auf bekannte
Schwachstellen pruefen.

## GG-CICD-006

Dependency-Scanning MUSS in der Pipeline verfuegbar sein.

Akzeptanz: Die Pipeline erzeugt eine Liste direkter und transitiver
Abhaengigkeiten und meldet bekannte Schwachstellen oder Lizenzkonflikte.

## GG-CICD-007

Die Pipeline SOLLTE Artefakte automatisiert erzeugen.

Akzeptanz: Wenn Artefakterzeugung aktiviert ist, veroeffentlicht die Pipeline
Container-Images, Testberichte, Coverage-Berichte, OpenAPI-Spezifikation und
Demo-Abnahmeartefakte.

---

# 23. Deployment

## GG-DEPLOY-001

Die Plattform MUSS Docker Compose unterstuetzen.

Akzeptanz: Das Repository enthaelt eine dokumentierte Compose-Konfiguration, die
API, UI, Simulationsdienst und verpflichtende Persistenz lokal startet.

## GG-DEPLOY-002

Die Plattform MUSS offline lokal lauffaehig sein, nachdem Images und
Abhaengigkeiten bereitgestellt wurden.

Akzeptanz: Nach lokalem Bereitstellen der benoetigten Images und Abhaengigkeiten
kann die Demo ohne Internetzugriff gestartet und abgenommen werden.

## GG-DEPLOY-003

Die Plattform MUSS Linux-basiert deploybar sein.

Akzeptanz: Die dokumentierte Referenzumgebung basiert auf Linux x86_64 und ein
Healthcheck weist die lauffaehigen Dienste dort nach.

## GG-DEPLOY-004

Die Plattform SOLLTE DevContainer unterstuetzen.

Akzeptanz: Wenn DevContainer-Unterstuetzung bereitgestellt wird, enthaelt das
Repository eine dokumentierte DevContainer-Konfiguration mit Build-, Test- und
Abnahmebefehlen.

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

## GG-DEPLOY-007

Die Plattform SOLLTE Kubernetes-faehig deploybar sein.

Akzeptanz: Wenn Kubernetes-Deployment unterstuetzt wird, sind Manifeste oder
Helm/Kustomize-Artefakte fuer API, UI, Simulationsdienst und Persistenzadapter
dokumentiert.

## GG-DEPLOY-008

Rolling Updates SOLLTEN fuer spaetere verteilte Deployments unterstuetzt werden.

Akzeptanz: Wenn verteiltes Deployment implementiert ist, dokumentiert die
Plattform Update-Strategie, Healthcheck-Gating und Verhalten laufender
Simulationen.

## GG-DEPLOY-009

Zero-Downtime-Deployment KANN fuer nicht laufkritische Dienste unterstuetzt
werden.

Akzeptanz: Wenn Zero-Downtime-Deployment implementiert ist, sind betroffene
Dienste, Einschraenkungen und Ausschluss laufender Simulationen dokumentiert.

## GG-DEPLOY-010

Rollback-Unterstuetzung SOLLTE fuer verteilte Deployments bereitgestellt werden.

Akzeptanz: Wenn verteiltes Deployment implementiert ist, dokumentiert die
Plattform Rollback fuer API, UI, Simulationsdienst und Datenbankschema inklusive
Grenzen bei migrationsbedingten Datenmodell-Aenderungen.

## GG-DEPLOY-011

Simulations- und Abnahmelaeufe MUESSEN ohne externe Netzwerkverbindungen
ausfuehrbar sein.

Akzeptanz: Ein vollstaendiger Demo- oder Abnahmelauf inklusive Replay, Fault
Injection und Persistenz kann ohne aktive Netzwerkverbindungen ausserhalb des
lokalen Host- oder Container-Netzwerks durchgefuehrt werden.

---

# 24. Demo-System

## GG-DEMO-001

Die Plattform MUSS eine Demo-Umgebung bereitstellen.

Akzeptanz: Die Demo-Umgebung ist lokal startbar, dokumentiert und Teil des
Abnahmebefehls oder einer reproduzierbaren Demo-Abnahmepruefung.

## GG-DEMO-002

Die Demo MUSS ein simuliertes Netz enthalten.

Akzeptanz: Die Demo enthaelt mindestens einen Netzanschlusspunkt mit Frequenz-
und Spannungstelemetrie.

## GG-DEMO-003

Die Demo MUSS eine simulierte Batterie enthalten.

Akzeptanz: Die Demo enthaelt mindestens einen Batteriespeicher mit Leistungs- und
SOC-Telemetrie.

## GG-DEMO-004

Die Demo MUSS Live-Telemetrie enthalten.

Akzeptanz: Nach Start der Demo werden innerhalb von 30 s aktuelle
Telemetriepunkte ueber API oder WebSocket bereitgestellt.

## GG-DEMO-005

Die Demo MUSS mindestens ein Replay-Szenario enthalten.

Akzeptanz: Das Demo-Replay kann ueber den Abnahmebefehl oder die API gestartet
werden und liefert einen maschinenlesbaren Replay-Status.

## GG-DEMO-006

Die Demo SOLLTE Fault Injection enthalten.

Akzeptanz: Wenn Fault Injection in der Demo enthalten ist, kann mindestens ein
Fault reproduzierbar ausgeloest werden und erzeugt Telemetrie mit
Qualitaetsstatus sowie einen Alarm.

## GG-DEMO-007

Die Demo SOLLTE mindestens einen Agenten enthalten.

Akzeptanz: Wenn ein Agent in der Demo enthalten ist, erzeugt er dokumentierte
Steuerbefehle oder Nachrichten, die deterministisch replaybar sind.

## GG-DEMO-008

Die Demo MUSS eine klare Abnahmereihenfolge dokumentieren.

Akzeptanz: Die Dokumentation beschreibt Start, Healthcheck, Szenarioausfuehrung,
Fault Injection, Replay und Export in reproduzierbaren Schritten.

---

# 25. Abnahmeartefakte

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

## GG-TRACE-001

Das Lastenheft MUSS eine V-Modell-aehnliche Rueckverfolgbarkeitsmatrix
Anforderung→Design→Implementierung→Test fuehren.

Akzeptanz: Das Lastenheft fuehrt drei Tabellen — Anforderung→Design,
Anforderung→Implementierung (inkl. Status-Marker und Meilensteinverweis)
und Anforderung→Test (Testtyp gemaess `GG-TESTTYPE-001..007`). Jede
normative `GG-…`-Anforderung (`MUSS`/`SOLLTE`) ist spaetestens zur Abnahme
ihres Scopes in der Implementierungs-Tabelle mit einem
Implementierungsartefakt und in der Test-Tabelle mit einem Testtyp
verknuepft; offene Eintraege sind als `🔲` mit Verweis auf die Folgearbeit
markiert. Die drei Tabellen liegen in §27.1, §27.2 und §27.3 dieses
Dokuments (Lesehilfe — `GG-TRACE-001` ist die ID, die diese Matrix
benennt).

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

---

# 27. V-Modell-aehnliche Rueckverfolgbarkeit

Dieser Abschnitt verbindet jede Lastenheft-Anforderung mit ihrem Design-,
Implementierungs- und Testartefakt. Die drei Tabellen werden mit dem
Projektfortschritt gepflegt:

- Die Design-Tabelle (§27.1) ist gegen `spec/architecture.md` v0.1.0
  gepflegt (`GG-AR-*`-Kennungen).
- Die Implementierungs-Tabelle (§27.2) wird befuellt, sobald erste
  Code-Artefakte und Meilensteine definiert sind. Die Meilensteine
  `M1..Mn` leben in
  [`docs/plan/planning/in-progress/roadmap.md`](../docs/plan/planning/in-progress/roadmap.md);
  die `GG-FUTURE-*`-Anforderungen in diesem Lastenheft sind
  ausschliesslich `KANN`-Punkte und nicht der Meilenstein-Plan.
- Die Test-Tabelle (§27.3) ist bereits jetzt aus dem Lastenheft ableitbar.

Status-Marker fuer die Implementierungs-Tabelle:

- ✓ `M[N]` — implementiert (Liefergegenstand des angegebenen Meilensteins)
- 🔲 — nicht implementiert (mit Verweis auf offene Frage oder Folgearbeit)

---

## 27.1 Anforderung zu Design

Design-Artefakte beziehen sich auf [`spec/architecture.md`](architecture.md);
`GG-AR-*`-Kennungen sind dort definiert: Prinzipien `GG-AR-P-*`, Ports
`GG-AR-PORT-DRV-*` / `GG-AR-PORT-DRN-*`, Komponenten `GG-AR-COMP-*`,
Architektur-Tabus `GG-AR-TABU-*`, offene Punkte `GG-AR-OPEN-*`.
Querverweise nutzen Kennungen als primaere Referenz (siehe [`ADR 0004`](../docs/plan/adr/0004-identifier-based-cross-references.md));
`§…`-Hinweise sind nur Lesehilfen in Klammern, wo eine Sektion noch
keine eigene Kennung traegt.

| Lastenheft-Kennung | Design-Artefakt                                                                                  |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| GG-ARCH-001        | Schichtenmodell + `GG-AR-COMP-*`-Komponentenfamilie                                              |
| GG-ARCH-002        | `GG-AR-P-002` Hexagonale Architektur                                                              |
| GG-ARCH-003        | Dependency Rule + `GG-AR-TABU-001` / `GG-AR-TABU-002`                                             |
| GG-ARCH-004        | `GG-AR-COMP-DEVICES` + `GG-AR-PORT-DRN-007`                                                       |
| GG-ARCH-005        | `GG-AR-COMP-CORE` Tick-Loop + Domain-Event (`GG-AR-COMP-DOMAIN`)                                  |
| GG-ARCH-006        | `GG-AR-COMP-SCHED` Tie-Breaking + `GG-AR-P-008` Determinismus-Invariante                          |
| GG-ARCH-007        | `GG-AR-PORT-DRN-001` (`ClockPort`) + `GG-AR-TABU-005`                                              |
| GG-ARCH-008        | `GG-AR-P-007` Live- und Replay-Tick-Loop geteilt                                                  |
| GG-PRINC-001       | `GG-AR-P-001..014` Architekturprinzipien — SOLID gesamt als Architekturzusicherung; automatisierte Teilabdeckung siehe `GG-PRINC-002..006` |
| GG-PRINC-002       | SRP — `ruff` `PLR0902` (max-attributes), `PLR0904` (max-public-methods), `C901` (McCabe), `PLR0915` (max-statements); Restanteil bleibt Code-Review |
| GG-PRINC-003       | OCP — primaer Code-Review; AST-Heuristik (Verbot von `isinstance(x, ConcreteType)` in `core/*`) ist Folgearbeit |
| GG-PRINC-004       | LSP — `mypy --strict` Type-Check-Gate ([`ADR 0005`](../docs/plan/adr/0005-type-check-gate.md)) prueft Variance-Verstoesse in Subtypen; Restanteil Code-Review |
| GG-PRINC-005       | ISP — `ruff` `PLR0904` (max-public-methods, Schwelle 12), `PLR0903` (too-few-public-methods); mypy-Protocol-Konformitaet via [`ADR 0005`](../docs/plan/adr/0005-type-check-gate.md); Restanteil Code-Review |
| GG-PRINC-006       | DIP — `GG-AR-TABU-001/002` + `AC-CORE-NO-ADAPTERS`/`AC-CORE-NO-DRIVING`/`AC-NO-FW`/`AC-PORTS-NO-FW` (vier von fuenfzehn A-1-Contracts in [`ADR 0002`](../docs/plan/adr/0002-language-and-build-stack.md)) |
| GG-CC-002          | `GG-AR-TABU-003` (Adapter-Logikverbot)                                                            |
| GG-CC-003          | `GG-AR-TABU-002` (Domain ohne Framework-Imports)                                                  |
| GG-CC-004          | `GG-AR-TABU-004` (keine Zyklen)                                                                    |
| GG-CC-006          | `GG-AR-TABU-007` (keine God-Utility-Classes)                                                       |
| GG-CC-007          | `GG-AR-TABU-006` (immutable Domain-Objekte) + `GG-AR-COMP-DOMAIN`                                  |
| GG-CC-008          | `GG-AR-TABU-008` (explizite Fehlerbehandlung)                                                      |
| GG-CC-001          | `ruff` `PLR0915`/`PLR0912`/`PLR0913`/`PLR0911`/`C901` mit `max-statements=30`, `max-complexity=10` ([`ADR 0002`](../docs/plan/adr/0002-language-and-build-stack.md), A-1 `ruff`-Konfiguration); Restanteil bleibt Code-Review |
| GG-CC-005          | `ruff` `N` (pep8-naming, formale Konsistenz von Klassen-/Funktions-/Konstantennamen); fachliche Bedeutung der Namen bleibt Code-Review |
| GG-SIM-001..004    | `GG-AR-COMP-CORE` Tick-Loop + `GG-AR-P-008` Determinismus-Invariante                              |
| GG-SIM-005         | `GG-AR-PORT-DRV-005` (`SnapshotPort`)                                                              |
| GG-SIM-006         | `GG-AR-PORT-DRV-003` (`ReplayPort`) + `GG-AR-P-007` geteilter Tick-Loop                            |
| GG-SIM-007         | `GG-AR-COMP-CORE` Wall-Clock-Multiplikatoren (Replay-Faktoren)                                    |
| GG-SIM-008         | `GG-AR-PORT-DRV-001` (`RunControlPort`)                                                            |
| GG-SIM-009         | `GG-AR-COMP-DOMAIN` `RunMetadata` + `GG-AR-COMP-PERSIST` Schema                                    |
| GG-RT-001          | `GG-AR-COMP-CORE` Tick-Dauer 10ms–1s, MVP-Modus-Definition                                        |
| GG-RT-002          | `GG-AR-COMP-CORE` + `GG-AR-P-008` Determinismus-Invarianten                                       |
| GG-RT-003          | `GG-AR-COMP-DOMAIN` Quality-Markierung (`stale`) + `GG-AR-PORT-DRN-001`                            |
| GG-RT-004/005      | `GG-AR-COMP-OBS` Metriken + `GG-AR-COMP-CORE` Commit-Pipeline                                      |
| GG-RT-006          | `GG-AR-COMP-REPLAY` Replay-Faktor-Tabelle                                                          |
| GG-DATA-001..004   | `GG-AR-COMP-DOMAIN` (TelemetryPoint, Command, Quality)                                            |
| GG-DATA-005        | `GG-AR-COMP-DOMAIN` + `GG-AR-COMP-SCENARIO` kanonische Serialisierung                              |
| GG-DEV-001         | `GG-AR-COMP-DEVICES` Geraetemodell-Vertrag                                                         |
| GG-DEV-002         | `GG-AR-COMP-DOMAIN` `TelemetryPoint`                                                               |
| GG-DEV-003         | `GG-AR-COMP-DOMAIN` `Command` + REST/WS-API in `GG-AR-COMP-API`                                    |
| GG-DEV-010..018    | `GG-AR-COMP-DEVICES` (MVP- und SOLLTE-Modelle)                                                     |
| GG-BESS-001..008   | `GG-AR-COMP-DEVICES` (Batteriemodell) + `GG-AR-P-010` Eingabe-Sicherheit                           |
| GG-GRID-001..007   | `GG-AR-COMP-DEVICES` (Netzmodell)                                                                  |
| GG-SCN-001..008    | `GG-AR-COMP-SCENARIO` Validierungs-Pipeline                                                        |
| GG-REPLAY-001..006 | `GG-AR-COMP-REPLAY` + `GG-AR-PORT-DRV-003`                                                         |
| GG-REPLAY-007      | `GG-AR-COMP-REPLAY` Diff-Klassifikation                                                            |
| GG-FAULT-001..010  | `GG-AR-COMP-FAULTS` Fault-Injection-Architektur                                                    |
| GG-AGENT-001..008  | `GG-AR-COMP-AGENTS` Multi-Agent-Subsystem                                                          |
| GG-API-001         | `GG-AR-COMP-API` REST-Endpunkte (`/runs`, `/runs/{id}/...`)                                        |
| GG-API-002         | `GG-AR-COMP-API` WebSocket-Telemetrie                                                              |
| GG-API-003         | `GG-AR-COMP-API` OpenAPI                                                                            |
| GG-API-004         | `GG-AR-COMP-API` Fehlerformat                                                                       |
| GG-MQTT-001        | `GG-AR-COMP-PROTOCOLS` + `GG-AR-PORT-DRN-007`                                                       |
| GG-MODB-001        | `GG-AR-COMP-PROTOCOLS` + `GG-AR-PORT-DRN-007`                                                       |
| GG-OPCUA-001       | `GG-AR-COMP-PROTOCOLS` + `GG-AR-PORT-DRN-007`                                                       |
| GG-DNP3-001        | `GG-AR-COMP-PROTOCOLS` + `GG-AR-PORT-DRN-007`                                                       |
| GG-IEC-001         | `GG-AR-COMP-PROTOCOLS` + `GG-AR-PORT-DRN-007`                                                       |
| GG-SNMP-001        | `GG-AR-COMP-PROTOCOLS` + `GG-AR-PORT-DRN-007`                                                       |
| GG-LWM2M-001       | `GG-AR-COMP-PROTOCOLS` + `GG-AR-PORT-DRN-007`                                                       |
| GG-UI-001..009     | `GG-AR-COMP-UI`                                                                                     |
| GG-PERSIST-001..004 | `GG-AR-COMP-PERSIST` Schema + `GG-AR-PORT-DRN-002`                                                 |
| GG-PERSIST-005     | `GG-AR-COMP-PERSIST` (PostgreSQL Pflicht)                                                          |
| GG-PERSIST-006/007 | `GG-AR-COMP-PERSIST` optionale Adapter (Timescale / Influx)                                         |
| GG-PERSIST-008     | `GG-AR-COMP-PERSIST` Migrations-Schicht                                                             |
| GG-PERSIST-009     | `GG-AR-PORT-DRN-003` + `GG-AR-COMP-PERSIST` `RunRepositoryPort`                                     |
| GG-OTEL-001..004   | `GG-AR-COMP-OBS` + `GG-AR-PORT-DRN-008`                                                             |
| GG-SAFE-001..004   | `GG-AR-P-010` Sicherer Default + `GG-AR-COMP-CORE` Quality-Markierung                               |
| GG-SAFE-005        | `GG-AR-P-010` Sicherer Default (Fallback-Variante in `GG-AR-COMP-DEVICES`)                          |
| GG-SAFE-006        | `GG-AR-COMP-REPLAY` Diff + `GG-AR-COMP-OBS` Replay-Diff-Status                                      |
| GG-SAFE-007        | `GG-AR-P-011` Trennung Simulation/Produktion                                                        |
| GG-SAFE-008        | `GG-AR-COMP-API` Eingabe-Validierung + `GG-AR-COMP-SCENARIO` Scenario-Validator                     |
| GG-TESTTYPE-001..007 | `GG-AR-TEST-001`                                                                                  |
| GG-ARCHTEST-001..005 | `GG-AR-TABU-001..008` + `GG-AR-TEST-001`                                                          |
| GG-CICD-001..007   | `GG-AR-TEST-001` + `GG-AR-COMP-DEPLOY`                                                              |
| GG-DEPLOY-001..011 | `GG-AR-COMP-DEPLOY`                                                                                 |
| GG-DEMO-001..008   | `GG-AR-COMP-DEPLOY` (Compose-Demo) + `GG-AR-TEST-001` (E2E/Demo-Abnahme)                            |
| GG-ACCEPT-001..003 | `GG-AR-TEST-001` + `GG-TRACE-001`                                                                   |
| GG-TRACE-001       | Rueckverfolgbarkeitstabelle in `architecture.md` (§18) — Quelle fuer diese §27.1-Tabelle             |
| GG-TEST-001..008   | `GG-AR-TEST-001` (Replay-/Fault-/Determinismus-Tests)                                               |
| GG-COV-001..005    | `GG-AR-TEST-001` (Coverage-Block und Quality Gates)                                                 |
| GG-QG-001..007     | `GG-AR-TEST-001` (Quality Gates) + `GG-AR-COMP-DEPLOY` (CI-Gating)                                   |
| GG-QA-001..006     | `GG-AR-TEST-001` + `GG-AR-TABU-001..008` (statische Pruefungen)                                     |

### 27.1.1 Anforderungen ohne Design-Artefakt

Die folgenden Anforderungsfamilien sind **Scope-, Definitions- oder
Zukunftsanforderungen** und mappen bewusst auf kein
Design-Artefakt in `architecture.md`:

| Lastenheft-Kennung      | Begruendung                                                       |
| ----------------------- | ----------------------------------------------------------------- |
| GG-TERM-001..006        | n/a — normative Begriffsdefinition (Vokabular `MUSS`/`DARF NICHT`/`SOLLTE`/`KANN`) |
| GG-SEED-001             | n/a — Projekt-Seed-Konvention (Test-Setup-Vorgabe, keine Architektur) |
| GG-MVP-001..004         | n/a — Scope-Festlegung; Auspraegung lebt in einzelnen `GG-SIM/DEV/...`-IDs |
| GG-NONGOAL-001..005     | n/a — explizite Scope-Grenzen (negativ definierte Anforderung)     |
| GG-FUTURE-001..006      | n/a — `KANN`-Zukunftsanforderungen `GG-FUTURE-*`; Design folgt erst bei Aktivierung im Abnahmescope |

---

## 27.2 Anforderung zu Implementierung

Erstmalig befuellt im Rahmen der M2-Welle-0c-Lastenheft-Sweep
(2026-05-18). Eintraege folgen der Roadmap-Vorbelegung:
✓ `M1` = vom M1-Tick-Loop-Spine geliefert (Closure-Notiz
[`done/M1-tick-loop-spine.md`](../docs/plan/planning/done-archive/M1-tick-loop-spine.md));
🔲 `M[N]` = vorbelegt, Lieferziel des angegebenen Meilensteins
laut [`roadmap.md`](../docs/plan/planning/in-progress/roadmap.md);
🔲 `Post-MVP` = SOLLTE-Anforderung jenseits des MVP-Scopes
ohne aktiven Slice. Querverweise auf Module sind Pfade unterhalb
von `src/grid_gym/` bzw. `tools/` und `Dockerfile`/`Makefile`/
`deploy/` an der Repo-Wurzel.

**Range-Konvention** (Welle-0b-Review M-8): `001..005` fuer
zusammenhaengende Bereiche, `001..005, 008` fuer Loecher.
Reine `/`-Trennung (z. B. `006/007`) ist nicht mehr zugelassen,
weil sie maschinelle Range-Auswertung gegenueber `..` brittle
macht.

**Ausnahme** (Welle-0b-Review M-9): `GG-TERM-003` (§2 Glossar,
„kanonisches Ergebnis") taucht in §6..§25 auf, hat aber keinen
Implementierungs-Charakter — Behandlung in §27.1.1
(`GG-TERM-001..006 — n/a, normative Begriffsdefinition`).
Damit ist `GG-TERM-003` bewusst nicht in der Implementations-
Matrix unten.

| Lastenheft-Kennung   | Implementierung                                                                                                                                                                                                                                                                                                                                                                                | Status      |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| GG-SIM-001..004      | `hexagon/core/simulation/scheduler.py` (Tie-Breaking, `GG-ARCH-006`), `hexagon/core/simulation/tick_loop.py` (Tick-Pipeline + `RandomPort`/`ClockPort`-Injektion). Determinismus-Property in `tests/unit/hexagon/core/simulation/`.                                                                                                                                                            | ✓ M1        |
| GG-SIM-005           | `hexagon/core/simulation/tick_loop.py::snapshot/from_snapshot`, `hexagon/core/domain/snapshot.py` (`SnapshotEnvelope`), Composition via `hexagon/ports/driven/random.py::snapshot_as_mapping` (`ADR 0010`).                                                                                                                                                                                    | ✓ M1        |
| GG-SIM-006           | `hexagon/core/replay/mapper.py` (CSV/JSON-Lines-Import, `GG-REPLAY-001/002`), `hexagon/core/replay/diff.py` (Diff, `GG-REPLAY-007`). Tick-Prozessor wird in M3 produktiv mit Replay-Source verkabelt.                                                                                                                                                                                          | ✓ M1        |
| GG-SIM-007           | `hexagon/core/simulation/tick_loop.py` laeuft heute ohne Wall-Clock-Wait — der Aufrufer entscheidet ueber Tick-Frequenz (`tests/unit/hexagon/core/simulation/test_tick_loop.py`). Replay-Faktoren sind `GG-RT-006`.                                                                                                                                                                            | ✓ M1        |
| GG-SIM-008           | Snapshot/Resume traegt Pause/Resume de-facto (`TickLoop.from_snapshot`). Formale `RunControlPort`-API (`GG-AR-PORT-DRV-001`) kommt mit Multi-Agent / Run-Lifecycle.                                                                                                                                                                                                                          | 🔲 M3       |
| GG-SIM-009           | `hexagon/core/domain/run.py` (`RunMetadata`), `adapters/driven/persistence_postgres/` (Postgres-`runs`-Repository, M1 Welle 6c). Voller Export inklusive Telemetrie + Alarme braucht `TelemetrySinkPort` / `AlarmSinkPort` (M3).                                                                                                                                                              | ✓ M1 (partial), Telemetrie/Alarme 🔲 M3 |
| GG-RT-001            | `hexagon/core/scenario/loader.py` validiert `tick_ms` (10/100/1000) ueber Scenario-Schema. Demo-Konfiguration + Backpressure-Healthcheck sind `GG-RT-005`-Tail (M6).                                                                                                                                                                                                                          | ✓ M1 (Tick-Schritte), 🔲 M6 (Backpressure) |
| GG-RT-002            | `hexagon/core/simulation/scheduler.py` Tie-Breaking + Determinismus-Property; gleicher Seed → byte-identische Reihenfolge.                                                                                                                                                                                                                                                                    | ✓ M1        |
| GG-RT-003            | `hexagon/core/domain/quality.py` Enum-Wert `stale` vorhanden; `max_age`-basierte Markierung im Tick-Schritt 6 (Quality-Markierung) kommt mit M3 (`GG-AR-COMP-CORE` Quality-Pipeline). M2-Geraete liefern Wert+Quality-Tupel ohne stale-Logik.                                                                                                                                                | 🔲 M3       |
| GG-RT-004/005        | Performance-Benchmark (100 Geraete, 10.000 Punkte/s) — `GG-RT-005`-Akzeptanz ist M6-Pflicht-Item.                                                                                                                                                                                                                                                                                            | 🔲 M6       |
| GG-RT-006            | Replay-Faktor-Tabelle / Time-Multiplier; kommt mit Replay-Source-Integration in M3.                                                                                                                                                                                                                                                                                                            | 🔲 M3       |
| GG-DATA-001          | `hexagon/core/domain/telemetry.py::TelemetryPoint` (Frozen-Dataclass).                                                                                                                                                                                                                                                                                                                          | ✓ M1        |
| GG-DATA-002          | `TelemetryPoint.unit: str` Feld vorhanden. Einheiten-Whitelist-Enforcement ist Geraete-Emitter-Verantwortung (M2) — Domain-Klasse haelt nur den Stringtyp.                                                                                                                                                                                                                                    | ✓ M1 (Vertrag), 🔲 M2 (Geraete-Emitter) |
| GG-DATA-003          | `hexagon/core/domain/quality.py::Quality` Enum mit `valid/stale/estimated/limited/invalid/nan/missing/fault_injected`.                                                                                                                                                                                                                                                                         | ✓ M1        |
| GG-DATA-004          | `hexagon/core/domain/command_result.py::CommandResult` Enum mit `accepted/rejected/limited/expired/failed/ignored`.                                                                                                                                                                                                                                                                            | ✓ M1        |
| GG-DATA-005          | `hexagon/core/serialization/canonical.py::canonical_json` (`ADR 0002 §A-2`); `AC-NO-JSON` Whitelist auf dieses Modul. Payload-Canonical-Check `hexagon/core/serialization/snapshot_codec.py` (M2 Welle 0a, Trigger 014).                                                                                                                                                                       | ✓ M1        |
| GG-DEV-001           | `DeviceModel`-Protocol (`initialize`/`apply_command`/`tick`/`snapshot`/`telemetry` + `device_id`-Property + `from_snapshot`-Classmethod) in `hexagon/core/devices/_protocol.py` (M2 Welle 1). [`ADR 0013`](../docs/plan/adr/0013-device-model-protocol.md) `Accepted` mit Welle-1-Review-Schaerfungen (§§2.5-2.8 + §8). Geraete-Implementationen (`GG-DEV-010..014`) sind weiterhin M2 Welle 2..4. | ✓ M2 Welle 1 (Protocol), 🔲 M2 Welle 2..4 (Implementationen) |
| GG-DEV-002           | `TelemetryPoint` (M1 Welle 1) deckt das Datenmodell ab; das `telemetry()`-Surface ist mit dem Protocol (M2 Welle 1) verbindlich. Geraete-Implementationen emittieren TelemetryPoints ab Welle 2.                                                                                                                                                                                                | ✓ M1+Welle 1 (Vertrag), 🔲 M2 Welle 2..4 (Emitter) |
| GG-DEV-003           | `Command` + `CommandResult` (M1 Welle 1) decken das Datenmodell ab; `apply_command(cmd) -> CommandResult` ist mit dem Protocol (M2 Welle 1) verbindlich.                                                                                                                                                                                                                                       | ✓ M1+Welle 1 (Vertrag), 🔲 M2 Welle 2..4 (Emitter) |
| GG-DEV-010           | `BatteryDevice` in `hexagon/core/devices/battery/` (M2 Welle 2, [`ADR 0014`](../docs/plan/adr/0014-battery-snapshot-schema.md) `Accepted`). Minimalmodell, Snapshot-Roundtrip, Determinismus-Property ueber 100 Ticks, Trigger-013-Test mit `tick_ms=100`. Demo-Szenario folgt mit M2-Welle-6.                                                                                                                                                       | ✓ M2 Welle 2 |
| GG-DEV-011           | `PvDevice` in `hexagon/core/devices/pv/` (M2 Welle 3a, [`ADR 0016`](../docs/plan/adr/0016-pv-load-device-pattern.md) `Accepted`). Konstantes `rated_power_kw`-Erzeugungsmodell mit `set_power_kw`-Override; Sign-Vertrag-Pruefung + Snapshot-Roundtrip + Determinismus-Property ueber 100 Ticks.                                                                                                                                                    | ✓ M2 Welle 3a |
| GG-DEV-013           | `LoadDevice` in `hexagon/core/devices/load/` (M2 Welle 3b, [`ADR 0016`](../docs/plan/adr/0016-pv-load-device-pattern.md) `Accepted`). Spiegel zu PV; Sign-Konvention „Load verbraucht nicht-negativ".                                                                                                                                                                                                                                              | ✓ M2 Welle 3b |
| GG-DEV-012, 014      | MVP-Geraete `grid_connection`/`smart_meter` — M2-Welle-4.                                                                                                                                                                                                                                                                                                                                      | 🔲 M2       |
| GG-DEV-015..018      | SOLLTE-Geraete (`ev_charger`, `transformer`, `wind_turbine`, `diesel_generator`) — eigene Slices nach M2-Closure.                                                                                                                                                                                                                                                                              | 🔲 Post-MVP |
| GG-BESS-001..005, 008 | `BatteryDevice` + `BatteryConfig` + `validate_set_power_command` (M2 Welle 2, [`ADR 0014`](../docs/plan/adr/0014-battery-snapshot-schema.md) `Accepted`). SOC-Fortschreibung mit Wirkungsgrad, Ramp-Limit, SOC-Hard-Clamp, Initialvalidierung pro Feld.                                                                                                                                                                                              | ✓ M2 Welle 2 |
| GG-BESS-006/007      | SOLLTE: Temperatur, Zellspannungs-Delta — eigene Slices nach M2-Closure.                                                                                                                                                                                                                                                                                                                       | 🔲 Post-MVP |
| GG-GRID-001..004     | Netzbilanzmodell (Frequenz/Spannung/Lasten/Lastspruenge) — M2-Welle-5 (Slice-Plan §3 Welle 5, Modul `hexagon/core/grid_model/`).                                                                                                                                                                                                                                                              | 🔲 M2       |
| GG-GRID-005..007     | SOLLTE: Inselnetz, Transformatorgrenzen, Blindleistung — eigene Slices nach M2-Closure.                                                                                                                                                                                                                                                                                                        | 🔲 Post-MVP |
| GG-SCN-001..008      | `hexagon/core/scenario/loader.py` (Mapping-Input, Hash via `canonical_json`), `hexagon/core/scenario/validator.py` (`GG-SCN-008`-Vorab-Validierung inkl. Payload-Canonical via Trigger 014). YAML-Adapter ist M2/M3-Driven-Adapter, Mapping-Input ist hexagon-pur.                                                                                                                            | ✓ M1        |
| GG-REPLAY-001..003   | `hexagon/core/replay/mapper.py` (CSV/JSON-Lines, `time_mapping=monotonic|index`).                                                                                                                                                                                                                                                                                                              | ✓ M1        |
| GG-REPLAY-004..006   | Replay-Diff-Status / Telemetrie-Replay-Monitoring kommt mit M3 (`GG-SAFE-006`-Pfad).                                                                                                                                                                                                                                                                                                            | 🔲 M3       |
| GG-REPLAY-007        | `hexagon/core/replay/diff.py` (`diff_replay`, Trigger 013 `tick_ms`-Parameter in M2 Welle 2 (Commit `48f0106`) geliefert; Closure-Notiz [`done/013-replay-diff-tick-ms-parameter.md`](../docs/plan/planning/done-archive/013-replay-diff-tick-ms-parameter.md)).                                                                                                                                       | ✓ M1+M2     |
| GG-FAULT-001..010    | Fault-Injection-Subsystem (`hexagon/core/faults/`) — M3.                                                                                                                                                                                                                                                                                                                                       | 🔲 M3       |
| GG-AGENT-001..008    | Multi-Agent-Bus (`hexagon/core/agents/`) — M3.                                                                                                                                                                                                                                                                                                                                                  | 🔲 M3       |
| GG-API-001           | `adapters/driving/http_api/app.py::POST /runs` (Stub mit `RunRepositoryPort.save`). `GET /runs/{id}/...` (Lauf-Status, Telemetrie-Stream, Steuerung) kommt mit M3/M5.                                                                                                                                                                                                                          | ✓ M1 (Stub), 🔲 M3/M5 (volle Endpoint-Surface) |
| GG-API-002           | WebSocket-Telemetrie — M3 (`TelemetrySinkPort` + UI-Konsum).                                                                                                                                                                                                                                                                                                                                    | 🔲 M3       |
| GG-API-003           | `adapters/driving/http_api/app.py` exportiert `app.openapi()`; `make openapi-validate` (Dockerfile-Stage) prueft Spec gegen `openapi-spec-validator`.                                                                                                                                                                                                                                         | ✓ M1        |
| GG-API-004           | FastAPI/pydantic liefern impliziten Default-Fehlerformat; RFC-7807-konformer Body + Domain-Fehler-Mapping (`adapters/driving/http_api/error_translation.py`) kommt mit M3.                                                                                                                                                                                                                    | 🔲 M3       |
| GG-MQTT-001          | MQTT-Adapter (`adapters/driven/protocol_mqtt/`) — M4 Welle 2 ([`ADR 0031`](../docs/plan/adr/0031-mqtt-adapter-profile.md) `Provisional`; siehe [`spec/protocol_profiles.md`](protocol_profiles.md) §MQTT). Topic-Schema inline, `canonical_json`-Codec, QoS 0/1, Per-Target `queue.Queue`-Marshal, Mosquitto-Integration-Smoke.                                                                                                                       | ✅ M4       |
| GG-MODB-001          | Modbus-Adapter (`adapters/driven/protocol_modbus/`) — M4 Welle 3 + Slice 031 ([`ADR 0032`](../docs/plan/adr/0032-modbus-adapter-profile.md) `Provisional`; siehe [`spec/protocol_profiles.md`](protocol_profiles.md) §Modbus-TCP). Register-Schema inline, 5 Datatypes, direkt-sync, FC03/FC10-Defaults mit FC04/FC06-Overrides, in-process pymodbus-Smoke.                                                                                            | ✅ M4       |
| GG-OPCUA-001         | OPC-UA-Adapter (`adapters/driven/protocol_opcua/`) — M4 Welle 4 + Slice 032 ([`ADR 0033`](../docs/plan/adr/0033-opcua-adapter-profile.md) `Provisional`; siehe [`spec/protocol_profiles.md`](protocol_profiles.md) §OPC-UA). **Erster rein-async-Stack** im Repo via eigenen `OpcuaLoopThread`. 8 Datatypes, Polling-Read + Direct-Write, in-process `asyncua.Server`-Smoke.                                                                          | ✅ M4       |
| GG-DNP3-001          | DNP3-Adapter (`adapters/driven/protocol_dnp3/`) — M4 Welle 5a ([`ADR 0034`](../docs/plan/adr/0034-dnp3-adapter-profile.md) `Provisional`; siehe [`spec/protocol_profiles.md`](protocol_profiles.md) §DNP3). **Zwei-Library-Setup** `nfm-dnp3` (Master, MIT, produktiv) + `dnp3-outstation` (Outstation, MIT, **nur Test-Sibling**). Group/Variation-Set `{(1,1),(1,2),(30,1),(30,5)}`, Class-0-Polling-Read mit Resultat-Filter-by-Index. **Erfuellung ueber Pfad A** (Adapter geliefert); historische Akzeptanz erlaubte alternativ dokumentierten Out-of-Scope-Verzicht (Slice 034 F15: Audit-Trail-Note).            | ✅ M4       |
| GG-IEC-001           | IEC-61850-Adapter (`adapters/driven/protocol_iec61850/`) — M4 Welle 5b + Slice 033 ([`ADR 0035`](../docs/plan/adr/0035-iec61850-adapter-profile.md) `Provisional`; siehe [`spec/protocol_profiles.md`](protocol_profiles.md) §IEC-61850). **GPLv3-isoliert** per SPDX-Header pro Datei (Decision I-f; **erstmaliger Repo-Praezedenzfall** fuer GPL-isolierte Sub-Module in einem sonst MIT-Projekt). `pyiec61850-ng` als opt-in Extra `pip install grid-gym[iec61850]`. Datatype-Set `{bool,int32,float,string}` × FC `{MX,ST,SP,CF,DC}`. Integration-Smoke aktuell unter 2c-Mock-only-Fallback (Python-3.14-SWIG-Inkompat; Welle-6b-Schaerfung). **Erfuellung ueber Pfad A** (Adapter geliefert); historische Akzeptanz erlaubte alternativ dokumentierten Out-of-Scope-Verzicht (Slice 034 F15: Audit-Trail-Note). | ✅ M4       |
| GG-SNMP-001          | SNMP-Adapter (`adapters/driven/protocol_snmp/`) — Device-Management-/Telemetry-Folgearbeit. Profil, ADR, Library-Wahl, Smoke-Sibling und Implementierung sind noch offen; Trigger-Watch [`047-device-management-protocol-adapters.md`](../docs/plan/planning/open/047-device-management-protocol-adapters.md). Kein Support-Claim bis Adapter + Profil geliefert sind.                                                                                                                                        | 🔲 Open     |
| GG-LWM2M-001         | LwM2M-Adapter (`adapters/driven/protocol_lwm2m/`) — Device-Management-/Telemetry-Folgearbeit. Profil, ADR, Library-Wahl, Smoke-Sibling und Implementierung sind noch offen; Trigger-Watch [`047-device-management-protocol-adapters.md`](../docs/plan/planning/open/047-device-management-protocol-adapters.md). Kein Support-Claim bis Adapter + Profil geliefert sind.                                                                                                                                      | 🔲 Open     |
| GG-UI-001..009       | Web-UI (`ui/`-Modul) — M5.                                                                                                                                                                                                                                                                                                                                                                       | 🔲 M5       |
| GG-PERSIST-001       | `adapters/driven/persistence_postgres/` mit `runs`-Schema. Telemetrie-/Alarm-Schema folgt mit `TelemetrySinkPort` (M3).                                                                                                                                                                                                                                                                       | ✓ M1 (`runs`), 🔲 M3 (Telemetrie/Alarme) |
| GG-PERSIST-002..004  | Telemetrie-Persistenz, Alarm-Persistenz, Retention-Policies — M3.                                                                                                                                                                                                                                                                                                                              | 🔲 M3       |
| GG-PERSIST-005       | Postgres als Pflicht-Backend — `adapters/driven/persistence_postgres/` + `deploy/compose.yml` Postgres-Service.                                                                                                                                                                                                                                                                                | ✓ M1        |
| GG-PERSIST-006..007  | SOLLTE: Timescale / Influx — Post-MVP.                                                                                                                                                                                                                                                                                                                                                          | 🔲 Post-MVP |
| GG-PERSIST-008       | `alembic.ini` + `adapters/driven/persistence_postgres/migrations/` (`alembic upgrade head` in M1-Welle-6c). Folge-Migrations kommen mit Telemetrie/Alarm-Schema (M3).                                                                                                                                                                                                                          | ✓ M1        |
| GG-PERSIST-009       | `hexagon/ports/driven/run_repository.py::RunRepositoryPort` + `InMemoryRunRepository` (Welle 6b) + `PostgresRunRepository` (Welle 6c). Lauf-Loeschung via `DELETE /runs/{id}` — M3 mit der vollen API-Surface.                                                                                                                                                                                | ✓ M1 (Vertrag), 🔲 M3 (Delete-Endpoint) |
| GG-OTEL-001..004     | `LogPort`/`MetricsPort`/`TracePort` (`hexagon/ports/driven/observability.py`) + OTLP-Adapter — M3.                                                                                                                                                                                                                                                                                              | 🔲 M3       |
| GG-SAFE-001..004     | Quality-Markierung-Pipeline (`GG-RT-003`-Pfad) — M3 mit der Tick-Loop-Quality-Stage 6. `RandomPort`-Seeding (`GG-SEED-001`) ist `ADR 0007` (`Accepted` 2026-05-17).                                                                                                                                                                                                                          | ✓ M1 (Seed), 🔲 M3 (Quality-Pipeline) |
| GG-SAFE-005          | Geraete-Fallback-Verhalten (sicherer Default je Geraet) — M2 mit `BatteryDevice.apply_command` / Sicherheitsgrenzen-Validierung.                                                                                                                                                                                                                                                              | 🔲 M2       |
| GG-SAFE-006          | Replay-Diff-Status-Markierung — M3 mit Replay-Source-Integration.                                                                                                                                                                                                                                                                                                                              | 🔲 M3       |
| GG-SAFE-007          | Trennung Simulation/Produktion — `GG-NONGOAL-001` + `README.md`-Disclaimer. Architektur-Pruefung in `tools/arch_check.py` (`AC-HEXAGON-PURE`-Whitelist).                                                                                                                                                                                                                                       | ✓ M1        |
| GG-SAFE-008          | `hexagon/core/scenario/validator.py` (Eingabe-Validierung vor Tick) + `adapters/driving/http_api/app.py` (pydantic-Request-Schemas).                                                                                                                                                                                                                                                            | ✓ M1        |
| GG-TEST-001..018     | `tests/unit/**` (Property-/Smoke-/Negativ-Tests, 268 Tests M1+Welle-0a), `tests/integration/**` (Postgres-Roundtrip via testcontainers). Replay- / Fault- / Determinismus-Marker via `make test-replay` / `test-fault` / `test-determinism`.                                                                                                                                                  | ✓ M1 (Unit/Integration), 🔲 M3 (Fault) |
| GG-TESTTYPE-001..007 | Testtyp-Definitionen werden ueber pytest-Marker (`pyproject.toml` (`[tool.pytest.ini_options]`)) und Makefile-Targets erzwungen. E2E-/Demo-Marker kommen mit M5.                                                                                                                                                                                                                                                          | ✓ M1 (Unit/Integration/Determinism/Replay), 🔲 M5 (E2E/Demo) |
| GG-ARCHTEST-001..005 | `tools/arch_check.py` (AST + grimp-SCC) + `import-linter` (16 A-1-Contracts, `pyproject.toml [tool.importlinter]`). Aggregator `make arch-check`.                                                                                                                                                                                                                                              | ✓ M1        |
| GG-COV-001..002      | `Dockerfile::coverage-gate`-Stage (`--cov-fail-under=$COVERAGE_THRESHOLD`, Branch via `coverage.xml`-Parse).                                                                                                                                                                                                                                                                                    | ✓ M1        |
| GG-COV-003           | `Dockerfile::coverage-gate-critical`-Stage (`CRITICAL_COV_TARGETS`-Liste, 90%-Schwelle). Default-Gate ohne Override gruen ab M2-Welle-2 (Battery liefert `devices/battery` ≥ 90 %).                                                                                                                                                                                                            | ✓ M1 (mit Override), 🔲 M2 (Default-gruen) |
| GG-COV-004..005      | Coverage-Reporting-Artefakte (`coverage.xml`) + 95%-Ziel — M6 (`GG-CICD`-Haertung).                                                                                                                                                                                                                                                                                                              | 🔲 M6       |
| GG-QG-001..005       | `make gates`-Aggregator (lint, format-check, typecheck mypy --strict, arch-check 16 Contracts, test-unit, coverage-gate, coverage-gate-critical, dep-audit). Konfiguration in `pyproject.toml` + Dockerfile-Stages.                                                                                                                                                                          | ✓ M1        |
| GG-QG-006            | `Dockerfile::openapi-validate`-Stage exportiert `app.openapi()` und prueft per `openapi-spec-validator`.                                                                                                                                                                                                                                                                                       | ✓ M1        |
| GG-QG-007            | Image-Audit (`make image-audit`, trivy `--ignore-unfixed`). Production-Image-Hardening (Trigger 015) Welle-0b geschlossen.                                                                                                                                                                                                                                                                     | ✓ M1        |
| GG-QA-001..006       | `make lint` (ruff BLE/TRY/B/DTZ/S/TID/PLR*/N), `make typecheck` (mypy --strict, `ADR 0005`), `make dep-audit` (pip-audit `--strict`), `make image-audit` (trivy). SBOM ist `GG-CICD-007` (M6).                                                                                                                                                                                                | ✓ M1        |
| GG-CICD-001..006     | `Makefile`-Targets `gates` / `ci` / `fullbuild` decken den Build-/Test-/Gate-/Image-Pfad ab. GitHub-Actions-Matrix gegen 3.13+3.14 ist M6.                                                                                                                                                                                                                                                     | ✓ M1 (lokal), 🔲 M6 (CI-Matrix) |
| GG-CICD-007          | SBOM-Generierung (`make sbom VERSION=...` Stub vorhanden, scharf erst mit Artefakt-Veroeffentlichung) — Trigger 008 (`open/`), M6.                                                                                                                                                                                                                                                             | 🔲 M6       |
| GG-DEPLOY-001..003   | `Dockerfile` runtime-Stage (non-root, /health-HEALTHCHECK, Port 8080), `deploy/compose.yml` (postgres + api + simulation-Stub). Trigger 015 (Welle 0b) hat shebang-Rewrite / `uv sync --no-editable` / direkte uvicorn-Binary nachgezogen.                                                                                                                                                  | ✓ M1+0b     |
| GG-DEPLOY-004..010   | Offline-Faehigkeit (kein Internet-Zugriff zur Laufzeit, `--no-pull` build), Linux-x86_64-Referenz, Multi-Service-Compose mit Healthchecks. Kubernetes-Manifeste sind Post-MVP.                                                                                                                                                                                                                | ✓ M1 (Compose), 🔲 Post-MVP (Kubernetes) |
| GG-DEPLOY-011        | `make runtime`-Compose-Smoke pollt `/health` mit Timeout — Welle-0b-Verifikation gruen.                                                                                                                                                                                                                                                                                                          | ✓ M1+0b     |
| GG-DEMO-001..008     | Demo-Szenario `tests/integration/scenarios/mvp_demo.yaml` (`GG-MVP-002`-Pflicht) + Demo-UI-Lauf — M2-Welle-6 (Szenario) bzw. M5 (UI-Demo).                                                                                                                                                                                                                                                    | 🔲 M2/M5    |
| GG-ACCEPT-001..003   | Abnahme-Artefakte: Closure-Notizen in `docs/plan/planning/done/` + Slice-Plan-Stack. Spike-0-Closure (`done/spike-0.md`), M1-Closure (`done/M1-tick-loop-spine.md` + `done/M1-tick-loop-results.md`), Trigger-Closures (`done/0NN-*`).                                                                                                                                                       | ✓ M1        |
| GG-TRACE-001         | Diese §27.2-Tabelle + §27.1-Tabelle + §27.3-Tabelle. `make docs-check` (d-check) validiert Markdown-Querverweise (`make docs-check`). Welle 0c (2026-05-18) hat die §27.2-Befuellung mechanisch durchgefuehrt.                                                                                                                                                                                       | ✓ M1+0c     |

---

## 27.3 Anforderung zu Test

Die Testtypen entsprechen `GG-TESTTYPE-001..007`.
Die Tabelle deckt diejenigen Anforderungen ab, deren Testtyp bereits aus dem
Lastenheft ableitbar ist; weitere Eintraege folgen mit der Implementierung.

| Lastenheft-Kennung | Testtyp                          |
| ------------------ | -------------------------------- |
| GG-SIM-001         | Unit Test                        |
| GG-SIM-002         | Unit Test                        |
| GG-SIM-003         | Unit Test                        |
| GG-SIM-004         | Unit Test                        |
| GG-SIM-005         | Unit Test                        |
| GG-RT-001          | Unit Test                        |
| GG-RT-002          | Integration Test                 |
| GG-RT-003          | Unit Test                        |
| GG-DATA-001        | Unit Test                        |
| GG-DATA-002        | Unit Test                        |
| GG-DATA-003        | Unit Test                        |
| GG-BESS-001        | Unit Test                        |
| GG-BESS-002        | Unit Test                        |
| GG-BESS-005        | Unit Test                        |
| GG-GRID-001        | Unit Test                        |
| GG-GRID-003        | Unit Test                        |
| GG-SCN-001         | Validation/Unit Test             |
| GG-SCN-005         | Validation Test                  |
| GG-REPLAY-001      | Replay-Diff Test                 |
| GG-REPLAY-003      | Replay-Diff Test                 |
| GG-FAULT-001       | Integration Test                 |
| GG-FAULT-005       | Integration Test                 |
| GG-AGENT-001       | Unit Test                        |
| GG-AGENT-004       | Integration Test                 |
| GG-API-001         | API Contract Test                |
| GG-API-002         | API Contract Test                |
| GG-API-003         | API Contract Test                |
| GG-API-004         | API Contract Test                |
| GG-MQTT-001        | Integration Test                 |
| GG-MODB-001        | Integration Test                 |
| GG-OPCUA-001       | Integration Test                 |
| GG-DNP3-001        | Integration Test                 |
| GG-IEC-001         | Integration Test                 |
| GG-UI-001          | E2E Test                         |
| GG-UI-005          | E2E Test                         |
| GG-PERSIST-001     | Persistence Test                 |
| GG-PERSIST-006     | Persistence/Retention Test       |
| GG-OTEL-001        | Telemetrie Test                  |
| GG-OTEL-002        | Telemetrie Test                  |
| GG-SAFE-001        | Security Test                    |
| GG-SAFE-004        | Security Test                    |
| GG-ARCH-001        | Architekturtest                  |
| GG-ARCH-005        | Architekturtest                  |
| GG-CICD-001        | CI/CD Verification               |
| GG-DEPLOY-001      | Container Test                   |
| GG-DEMO-001        | E2E Test                         |
| GG-ACCEPT-001      | Acceptance/Documentation Test    |
| GG-TRACE-001       | Documentation Test (Self-Verification — Existenz und Pflege der drei Trace-Tabellen, Folgearbeit: `make docs-check` (d-check)) |

---
