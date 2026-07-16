# Spezifikation (Pflichtenheft) — grid-gym

> Mittlere V-Modell-Schicht (**Spezifikation**, `WIE-funktional/QS`) zwischen dem
> Vertrag (`lastenheft.md`, `WAS`) und der Architektur (`architecture.md`,
> `WIE-strukturell`). Sie verfeinert den Vertrag **aufwärts** und wird von der
> Architektur strukturell umgesetzt. Inhalt: interne Entwicklungs- und
> QS-Disziplin (SOLID-Prinzipien, Clean-Code-Konventionen, Determinismus-/
> Test-Konventionen) **samt ihrer Werkzeug-Durchsetzung** (`ruff`, `mypy`,
> Architektur-Gates). Die Kennungs-Präfixe (`GG-PRINC-*`, `GG-CC-*`, `GG-SEED-*`)
> bleiben unverändert; ihre Schicht-Zugehörigkeit ist diese Datei.

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

## 5. Offene Spezifikationspunkte (`GG-SPEC-OPEN-*`)

Offene Punkte dieser Schicht (analog „Offene architektonische Punkte" in
`architecture.md`). Geschlossene Zeilen zitieren die auflösende Entscheidung.

| Kennung | Frage / offener Punkt | Status |
| ------- | --------------------- | ------ |
| <a id="gg-spec-open-001"></a>`GG-SPEC-OPEN-001` | §27.1-Positivtabelle von einer handgepflegten/gegateten Tabelle zum **Generator/Report** promoten (von `doc-trace` aus den Bezug-Spalten erzeugt), sobald das Konsistenz-Gate die Bezug-Quelle sauber erzwingt | Offen — Ausführung in einem Folge-Slice des Spec-Schichtungs-Arcs (Traceability-Finalisierung) |
