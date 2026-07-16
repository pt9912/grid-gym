# Spezifikation (Pflichtenheft) — grid-gym

> Mittlere V-Modell-Schicht (**Spezifikation**, `WIE-funktional/QS`) zwischen dem
> Vertrag (`lastenheft.md`, `WAS`) und der Architektur (`architecture.md`,
> `WIE-strukturell`). Sie verfeinert den Vertrag **aufwärts** und wird von der
> Architektur strukturell umgesetzt. Inhalt: interne Entwicklungs- und
> QS-Disziplin (SOLID-Prinzipien, Clean-Code-Konventionen, Determinismus-,
> Testarten-, Coverage-, Quality-Gate- und Codeanalyse-/Architekturtest-
> Konventionen) **samt ihrer Werkzeug-Durchsetzung** (`ruff`, `mypy`,
> Architektur-Gates). Die Kennungs-Präfixe (`GG-PRINC-*`, `GG-CC-*`, `GG-SEED-*`,
> `GG-TESTTYPE-*`, `GG-COV-*`, `GG-QG-*`, `GG-QA-*`, `GG-ARCHTEST-*`) bleiben
> unverändert; ihre Schicht-Zugehörigkeit ist diese Datei.

**Bezug (aufwärts):** [`lastenheft.md`](lastenheft.md) — der normative Vertrag.
**Geschwister-Dokument (schicht-intern):** [`protocol_profiles.md`](protocol_profiles.md)
— Wire-Level-Interface-Spezifikation der Protokolladapter.

---

## 1. Zweck und Einordnung

Diese Schicht beantwortet „**wie/womit wird spezifiziert und geprüft**", nicht
„was der Kunde will" (das bleibt der Vertrag) und nicht „wie ist das System
strukturiert" (das ist die Architektur). Die hier geführten Familien sind
**interne Disziplin**: sie binden Entwicklung und Qualitätssicherung, nicht die
fachliche Kundenabnahme. Wo ein Prinzip **automatisiert** durchgesetzt wird, ist
das Werkzeug (`ruff`-Regel, `mypy`-Gate, Architektur-Test) hier **erstklassig**
dokumentiert; wo die Durchsetzung eine Architektur-Zusicherung ist, zeigt
`architecture.md` **aufwärts** auf die betreffende Kennung hier (die
Spezifikation verweist nicht abwärts auf die Architektur).

Der Rest-Anteil, der sich nicht mechanisch prüfen lässt, bleibt **Code-Review**.

## 2. SOLID-Prinzipien (`GG-PRINC-*`)

### GG-PRINC-001 SOLID-Prinzipien
<a id="gg-princ-001"></a>

Das System MUSS nach SOLID-Prinzipien entwickelt werden.

Akzeptanz: Architekturentscheidungen und Code-Reviews pruefen
Einzelverantwortung, Erweiterbarkeit, Austauschbarkeit, kleine Schnittstellen
und Abhaengigkeiten gegen Abstraktionen fuer geaenderte Kernmodule.

**Durchsetzung:** SOLID gesamt als Architektur- und Review-Zusicherung;
automatisierte Teilabdeckung über die Einzelprinzipien PRINC-002..006
(SRP/OCP/LSP/ISP/DIP).

### GG-PRINC-002 Einzelverantwortung (SRP)
<a id="gg-princ-002"></a>

Klassen, Module und Services MUESSEN eine klare Einzelverantwortung besitzen.

Akzeptanz: Ein Modul hat einen fachlich benennbaren Grund fuer Aenderungen.
Vermischungen von Domain-Logik, Persistenz, Transport und UI-Logik werden durch
Architekturtests, Code-Review oder dokumentierte Ausnahme erkannt.

**Durchsetzung:** `ruff` `PLR0902` (max-attributes), `PLR0904` (max-public-methods),
`C901` (McCabe), `PLR0915` (max-statements); Restanteil Code-Review.

### GG-PRINC-003 Offen/Geschlossen (OCP)
<a id="gg-princ-003"></a>

Erweiterungen SOLLTEN ohne Aenderung bestehender Kernlogik moeglich sein.

Akzeptanz: Neue Geraetemodelle, Szenario-Adapter und Persistenzadapter koennen
ueber definierte Ports, Registries oder Konfiguration ergaenzt werden, ohne den
Simulationskern fachlich zu veraendern.

**Durchsetzung:** primär Code-Review; AST-Heuristik (Verbot von
`isinstance(x, ConcreteType)` in `core/*`) ist Folgearbeit.

### GG-PRINC-004 Ersetzbarkeit (LSP)
<a id="gg-princ-004"></a>

Implementierungen MUESSEN ueber ihre definierten Schnittstellen austauschbar
sein.

Akzeptanz: Mindestens ein Port des Simulationskerns hat im Test eine alternative
Implementierung, die ohne Aenderung der Domain-Logik eingesetzt werden kann.

**Durchsetzung:** `mypy --strict` Type-Check-Gate (prüft Variance-Verstöße in
Subtypen); Restanteil Code-Review.

### GG-PRINC-005 Schnittstellentrennung (ISP)
<a id="gg-princ-005"></a>

Schnittstellen MUESSEN klein und fachlich getrennt sein.

Akzeptanz: Ports fuer Zeit, Eingaben, Ausgaben, Persistenz, Telemetrie und
Steuerbefehle sind getrennt dokumentiert. Adapter implementieren nur die Ports,
die sie fachlich benoetigen.

**Durchsetzung:** `ruff` `PLR0904` (max-public-methods, Schwelle 12), `PLR0903`
(too-few-public-methods); `mypy`-Protocol-Konformität; Restanteil Code-Review.

### GG-PRINC-006 Abhaengigkeitsinversion (DIP)
<a id="gg-princ-006"></a>

Abhaengigkeiten MUESSEN gegen Abstraktionen gerichtet sein.

Akzeptanz: Domain-Module haengen nicht direkt von Infrastruktur-, Framework-,
Transport- oder Datenbankpaketen ab. Diese Regel wird durch Architekturtests
oder statische Importpruefungen validiert.

**Durchsetzung:** `make arch-check` (import-linter + `tools/arch_check.py`,
Architektur-Tabus + Kern-ohne-Adapter/-Driving-Contracts); `mypy`-Protocol-
Konformität; Restanteil Code-Review.

## 3. Clean-Code-Konventionen (`GG-CC-*`)

### GG-CC-001 Kurze, fokussierte Methoden
<a id="gg-cc-001"></a>

Methoden und Funktionen SOLLTEN kurz und fokussiert sein.

Akzeptanz: Produktionscode ueberschreitet 30 logische Zeilen pro Methode oder
Funktion nur mit fachlicher Begruendung, z. B. fuer klar strukturierte Parser,
Tabellen oder generierten Code.

**Durchsetzung:** `ruff` `PLR0915`/`PLR0912`/`PLR0913`/`PLR0911`/`C901` mit
`max-statements=30`, `max-complexity=10`; Restanteil Code-Review.

### GG-CC-002 Adapter ohne Businesslogik
<a id="gg-cc-002"></a>

Infrastruktur-Adapter DUERFEN KEINE Businesslogik enthalten.

Akzeptanz: Adapter uebersetzen Protokolle, Datenformate und technische Fehler in
Ports und Domain-Typen. Fachliche Entscheidungen liegen im Simulationskern oder
in Geraetemodellen.

**Durchsetzung:** `make arch-check` (Architektur-Tabu Adapter-Logikverbot).

### GG-CC-003 Framework-freie Domain
<a id="gg-cc-003"></a>

Domain-Module DUERFEN KEINE Framework-Abhaengigkeiten enthalten.

Akzeptanz: Domain-Code importiert keine Web-, Datenbank-, Messaging-,
Container- oder UI-Frameworks.

**Durchsetzung:** `make arch-check` (Architektur-Tabu Domain ohne Framework-Imports).

### GG-CC-004 Keine Zyklen
<a id="gg-cc-004"></a>

Module DUERFEN KEINE zyklischen Abhaengigkeiten besitzen.

Akzeptanz: Eine automatisierte Modul- oder Importanalyse meldet Zyklen als
Architekturverletzung.

**Durchsetzung:** `make arch-check` (Architektur-Tabu keine Zyklen).

### GG-CC-005 Sprechende Namen
<a id="gg-cc-005"></a>

Fachliche Namen MUESSEN eindeutig und sprechend sein.

Akzeptanz: Oeffentliche Typen, Ports, Events, Commands, Metriken und
Qualitaetszustaende verwenden Begriffe aus Szenarioformat, Datenmodell oder
Dokumentation konsistent.

**Durchsetzung:** `ruff` `N` (pep8-naming, formale Namenskonsistenz); die
fachliche Bedeutung der Namen bleibt Code-Review.

### GG-CC-006 Keine God-Utility-Classes
<a id="gg-cc-006"></a>

Statische Utility-God-Classes DUERFEN NICHT eingefuehrt werden.

Akzeptanz: Wiederverwendbare Logik wird fachlich verortet oder als kleine,
zweckgebundene Funktion bzw. Komponente implementiert.

**Durchsetzung:** `make arch-check` (Architektur-Tabu keine God-Utility-Classes).

### GG-CC-007 Immutable Domain-Objekte
<a id="gg-cc-007"></a>

Immutable Domain-Objekte SOLLTEN bevorzugt werden.

Akzeptanz: Events, Commands, Telemetriepunkte, Snapshots und Szenario-Modelle
sind unveraenderlich oder behandeln Mutation explizit und lokal begrenzt.

**Durchsetzung:** `make arch-check` (Architektur-Tabu immutable Domain-Objekte);
Restanteil Code-Review.

### GG-CC-008 Explizite Fehlerbehandlung
<a id="gg-cc-008"></a>

Fehlerbehandlung MUSS explizit erfolgen.

Akzeptanz: Fehlerpfade liefern typisierte Fehler, Statuswerte oder dokumentierte
Exceptions. Fehler werden nicht stillschweigend verschluckt und nicht nur ueber
unklassifizierte Strings signalisiert.

**Durchsetzung:** `make arch-check` (Architektur-Tabu explizite Fehlerbehandlung).

## 4. Determinismus- und Test-Konventionen (`GG-SEED-*`)

### GG-SEED-001 Seedbare Zufallsquellen
<a id="gg-seed-001"></a>

Alle Zufallsquellen MUESSEN explizit seedbar sein.

Akzeptanz: Zufallsquellen ohne dokumentierten Seed verhindern die
Determinismus-Abnahme. Seeds werden in Laufmetadaten exportiert und bei Replay
wiederverwendet.

**Durchsetzung:** interne Test-/Setup-Konvention; der *Kundenwunsch* Determinismus
liegt aufwärts im Vertrag (`GG-SIM-*` / `GG-RT-*`), `GG-SEED-001` ist das *Wie*.
`make test-determinism` deckt Seed-/Scheduler-/Ausgabe-Determinismus ab.

## 5. Testarten (`GG-TESTTYPE-*`)

**Durchsetzung:** `make test-unit` (Unit + Property), `make test-integration`
(Integration über reale Adapter/Container), `make arch-check` + `make a-check`
(Architekturtests), `make openapi-validate` (Contract/OpenAPI), `make fullbuild`
(E2E-Demo-Smoke); Performance-/Security-Testarten via `make dep-audit` /
`make image-audit` + optionale Perf-Suite.

### GG-TESTTYPE-001 Unit-Tests
<a id="gg-testtype-001"></a>

Die Plattform MUSS Unit-Tests unterstuetzen.

Akzeptanz: Unit-Tests koennen lokal ohne Container gestartet werden.

### GG-TESTTYPE-002 Integrationstests
<a id="gg-testtype-002"></a>

Die Plattform MUSS Integrationstests unterstuetzen.

Akzeptanz: Integrationstests pruefen mindestens API, Persistenz und Telemetrie
ueber reale Adapter- oder Containergrenzen.

### GG-TESTTYPE-003 Architekturtests
<a id="gg-testtype-003"></a>

Die Plattform MUSS Architekturtests unterstuetzen.

Akzeptanz: Architekturtests pruefen Modulgrenzen und Abhaengigkeitsrichtung.

### GG-TESTTYPE-004 Contract-Tests
<a id="gg-testtype-004"></a>

Die Plattform SOLLTE Contract-Tests unterstuetzen.

Akzeptanz: Wenn Contract-Tests implementiert sind, pruefen sie OpenAPI-Schemas,
WebSocket-Nachrichten und implementierte Adaptervertraege.

### GG-TESTTYPE-005 End-to-End-Demo-Tests
<a id="gg-testtype-005"></a>

Die Plattform MUSS End-to-End-Tests fuer die Demo unterstuetzen.

Akzeptanz: Ein E2E-Test startet die Demo, prueft Healthcheck, Szenarioausfuehrung,
Telemetrie, Persistenz und Replay-Diff.

### GG-TESTTYPE-006 Performance-Tests
<a id="gg-testtype-006"></a>

Die Plattform SOLLTE Performance-Tests unterstuetzen.

Akzeptanz: Wenn Performance-Tests implementiert sind, pruefen sie die
Referenzumgebung, Tick-Dauer, Jitter, Telemetriepunkte/s und Replay-Diff-Status.

### GG-TESTTYPE-007 Security-Tests
<a id="gg-testtype-007"></a>

Die Plattform SOLLTE Security-Tests unterstuetzen.

Akzeptanz: Wenn Security-Tests implementiert sind, pruefen sie
Dependency-Scanning, bekannte kritische Schwachstellen und Eingabevalidierung.

## 6. Coverage-Anforderungen (`GG-COV-*`)

**Durchsetzung:** `make coverage-gate` (90 % Line / 85 % Branch),
`make coverage-gate-critical` (90 % kritische Domäne); künstliche Coverage bleibt
Code-Review + pytest-Marker (kein rein ausführungsgetriebener Nachweis).

### GG-COV-001 Mindest-Testabdeckung 90 %
<a id="gg-cov-001"></a>

Die Plattform SOLLTE eine Mindest-Testabdeckung von 90 Prozent erreichen.

Akzeptanz: Der Coverage-Report weist die Gesamt-Coverage aus und dokumentiert
Abweichungen.

### GG-COV-002 Branch-Coverage 85 %
<a id="gg-cov-002"></a>

Die Plattform SOLLTE mindestens 85 Prozent Branch-Coverage erreichen.

Akzeptanz: Der Coverage-Report weist Branch-Coverage separat aus.

### GG-COV-003 Kritische-Domaene-Coverage 90 %
<a id="gg-cov-003"></a>

Kritische Domaenenlogik MUSS fuer den MVP mindestens 90 Prozent Coverage
erreichen.

Akzeptanz: Simulationskern, Scheduler, Replay-Diff, Szenario-Validierung und
Batteriemodell werden als kritische Domaenenlogik klassifiziert und im
Coverage-Report separat ausgewiesen. Zielwert fuer spaetere Releases ist 95
Prozent.

### GG-COV-004 Keine kuenstliche Coverage
<a id="gg-cov-004"></a>

Coverage DARF NICHT kuenstlich erzeugt werden.

Akzeptanz: Tests ohne fachliche Assertion, reine Getter-/Setter-Ausfuehrung und
Snapshots ohne Verhaltenspruefung gelten nicht als Qualitaetsnachweis.

### GG-COV-005 Keine Getter/Setter-only-Tests
<a id="gg-cov-005"></a>

Getter/Setter-only-Tests gelten NICHT als ausreichender Qualitaetsnachweis.

Akzeptanz: Tests fuer Domain-Objekte pruefen Invarianten, Validierung,
Serialisierung oder fachliches Verhalten.

## 7. Quality Gates (`GG-QG-*`)

**Durchsetzung:** gebündelt in `make gates` — `coverage-gate` (Coverage),
`dep-audit`/`image-audit` (Security), `arch-check`/`a-check` (Architektur),
`test-unit` (Test), `lint`/`typecheck` (Static-Analysis), `openapi-validate`
(OpenAPI); Datenschutz-/Replay-Guard-Prüfungen als eigene Test-Marker. Fehlschlag
bricht den CI-Build oder verlangt eine dokumentierte Ausnahme.

### GG-QG-001 Coverage-Gate
<a id="gg-qg-001"></a>

Der Build SOLLTE bei unterschrittener Coverage fehlschlagen.

Akzeptanz: Wenn Coverage-Gates aktiviert sind, bricht der CI-Build bei
Unterschreitung der dokumentierten Schwellwerte ab oder verlangt eine
dokumentierte Ausnahme.

### GG-QG-002 Security-Gate
<a id="gg-qg-002"></a>

Der Build DARF bei kritischen oder hohen Security-Issues ohne dokumentierte
Ausnahme nicht erfolgreich sein.

Akzeptanz: Security-Scanning liefert Severity, betroffene Komponente und
Ausnahmeentscheidung. Kritische und hohe Befunde blockieren den Build, sofern
keine dokumentierte Ausnahme existiert.

### GG-QG-003 Architektur-Gate
<a id="gg-qg-003"></a>

Der Build DARF bei Architekturverletzungen nicht erfolgreich sein.

Akzeptanz: Verletzungen von hexagonalen Modulgrenzen, Framework-Freiheit der
Domain oder zyklischen Abhaengigkeiten blockieren den Build.

### GG-QG-004 Test-Gate
<a id="gg-qg-004"></a>

Der Build DARF bei fehlschlagenden Tests nicht erfolgreich sein.

Akzeptanz: Unit-, Integrations-, Architektur- und Demo-Abnahmetests liefern
einen nicht erfolgreichen CI-Status, wenn sie fehlschlagen.

### GG-QG-005 Static-Analysis-Gate
<a id="gg-qg-005"></a>

Der Build SOLLTE bei statischen Analysefehlern fehlschlagen.

Akzeptanz: Wenn statische Analyse aktiviert ist, blockieren Fehler oberhalb der
dokumentierten Severity-Schwelle den Build.

### GG-QG-006 OpenAPI-Gate
<a id="gg-qg-006"></a>

Der Build DARF bei fehlgeschlagener OpenAPI-Validierung nicht erfolgreich sein.

Akzeptanz: OpenAPI-Spezifikation, Request-Schemas und Response-Schemas werden in
CI validiert.

### GG-QG-007 Datenschutz-Gate
<a id="gg-qg-007"></a>

Der Build SOLLTE bei fehlgeschlagenen Datenschutz- und
Replay-Sicherheitspruefungen fehlschlagen.

Akzeptanz: Wenn Datenschutz- oder Replay-Sicherheitsregeln implementiert sind,
blockieren fehlgeschlagene Pruefungen den Build oder verlangen eine dokumentierte
Ausnahme.

## 8. Codeanalyse und Architekturvalidierung (`GG-QA-*`, `GG-ARCHTEST-*`)

**Durchsetzung:** `make lint` (ruff — statische Analyse + Code-Smells + Naming),
`make dep-audit` (Abhängigkeits-Sicherheit), `make arch-check` (import-linter +
`tools/arch_check.py`: Zyklen + Modulgrenzen) + `make a-check` (Hexagon-Schicht-/
Richtungs-Reinheit); SonarQube-/Duplication-Anbindung optional und dokumentiert.
Die Architekturtests laufen als eigener CI-Job.

### GG-QA-001 Statische Codeanalyse
<a id="gg-qa-001"></a>

Statische Codeanalyse MUSS fuer Produktionscode verfuegbar sein.

Akzeptanz: Ein dokumentierter Befehl fuehrt statische Analyse lokal oder in CI
aus.

### GG-QA-002 SonarQube-Unterstuetzung
<a id="gg-qa-002"></a>

SonarQube-Unterstuetzung SOLLTE bereitgestellt werden.

Akzeptanz: Wenn SonarQube genutzt wird, sind Projektkonfiguration,
Coverage-Import und Quality-Gate-Anbindung dokumentiert.

### GG-QA-003 Code-Smell-Pruefungen
<a id="gg-qa-003"></a>

Code-Smell-Pruefungen SOLLTEN Teil der statischen Analyse sein.

Akzeptanz: Die Analyse meldet Code Smells mit Datei, Regel und Severity.

### GG-QA-004 Duplication-Pruefungen
<a id="gg-qa-004"></a>

Duplication-Pruefungen SOLLTEN Teil der statischen Analyse sein.

Akzeptanz: Die Analyse weist duplizierte Bloecke aus und dokumentiert
Schwellwerte.

### GG-QA-005 Abhaengigkeits-Sicherheitspruefung
<a id="gg-qa-005"></a>

Pruefungen auf Sicherheitsluecken MUESSEN fuer Abhaengigkeiten verfuegbar sein.

Akzeptanz: Ein dokumentierter Befehl oder CI-Schritt prueft direkte und
transitive Abhaengigkeiten auf bekannte Schwachstellen.

### GG-QA-006 Zyklen-Erkennung
<a id="gg-qa-006"></a>

Zyklische Abhaengigkeiten MUESSEN automatisiert erkannt werden.

Akzeptanz: Die Architekturvalidierung meldet Zyklen zwischen Modulen oder
Paketen als Build-Artefakt.

### GG-ARCHTEST-001 Modulgrenzen-Test
<a id="gg-archtest-001"></a>

Hexagonale Modulgrenzen MUESSEN automatisiert geprueft werden.

Akzeptanz: Architekturtests stellen sicher, dass Domain-Module keine Adapter und
Adapter die Domain nur ueber Ports verwenden.

### GG-ARCHTEST-002 Infra-Domain-Entkopplung
<a id="gg-archtest-002"></a>

Infrastruktur DARF NICHT von konkreter Domain-Implementierung abhaengen, wenn
ein Port definiert ist.

Akzeptanz: Infrastrukturmodule importieren Port-Definitionen und DTOs, aber
keine internen Domain-Services oder konkreten Geraetemodell-Implementierungen,
sofern ein Port existiert.

### GG-ARCHTEST-003 Adapter-Logik-Verbot
<a id="gg-archtest-003"></a>

Adapter DUERFEN KEINE Domaenenlogik enthalten.

Akzeptanz: Architekturtests und Code-Review pruefen, dass Adapter nur
Protokoll-, Format-, Transport- und Fehleruebersetzung enthalten.

### GG-ARCHTEST-004 Framework-freie Ports
<a id="gg-archtest-004"></a>

Ports MUESSEN framework-unabhaengig bleiben.

Akzeptanz: Port-Definitionen importieren keine Web-, Persistenz-, Messaging-
oder UI-Frameworks.

### GG-ARCHTEST-005 Architekturtests in CI
<a id="gg-archtest-005"></a>

Architekturtests MUESSEN Teil der CI-Pipeline sein.

Akzeptanz: Die CI-Pipeline fuehrt Architekturtests aus und veroeffentlicht den
Status als Build-Ergebnis.
