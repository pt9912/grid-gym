# 026 — BESS-Simulation als Vorlage fuer Reserve-Market-/LER-Agent

**Status:** Open — Trigger-Watch
**Lebenszyklus:** Open (Open-Phase), Aktivierung entschieden im Feld `Activation Gate`
**Datum:** 2026-05-24
**Quelle-Repo:** Fachliche Sichtung von [`BESS-Simulation`](https://github.com/flpp-signature/BESS-Simulation)
gegen den aktuellen `grid-gym`-Stand.
**Legal-Status:** Noch offen (`Commit/Tag`, `Lizenz`, `Freigabestatus`, `Prüfstelle` müssen vor Aktivierung konkret eingetragen werden).
**Owner:** [MUSS vor Aktivierung gesetzt werden]
**Slice-Slot:** [MUSS vor Aktivierung in `planning/planning/README.md` verlinkt werden]
**Activation Gate:** `Pending` (`Approved` oder `Blocked`)

## Aktivierungs-Preflight (Hard Gate)

Vor einem Slice-Start-Pull-Request müssen diese Felder befüllt sein:

- **Owner:** `<Team/Name>`
- **Slice-Eintrag:** `<Link in planning/planning/README.md>`
- **Activation Gate:** `Approved` (Go) oder `Blocked` (No-Go)
- **Legal Clearance (alle Felder):**
  - **Quelle/Repo:** `<Repo + URL + Commit/Tag>`
  - **Lizenz:** `<Lizenztyp + Version>`
  - **Freigabestatus:** `<Genehmigt/abgelehnt>`
  - **Prüfstelle + Datum:** `<Name + TT.MM.YYYY>`
  - **Nachweis:** `link-zum-legal-notes`

Wenn mindestens ein Feld auf `-` oder `TBD` bleibt, gilt der Spike als **No-Go**.

---

## Trigger

`BESS-Simulation` ist ein kleines Python-Tool fuer
BESS-Reservebereitstellung mit FCR/aFRR, Intraday-SOC-Restoration,
LER Alert/Recovery und freiwilligen FRR-Energiegeboten. Der Kern ist
fachlich relevant fuer `grid-gym`, aber nicht als Drop-in-Code geeignet.

Aktivieren, sobald eines der folgenden Themen konkret geplant wird:

- Reserve-Market-Agent fuer FCR/aFRR-Strategien.
- BESS-SOC-Management-Agent mit Intraday- bzw. Market-Schedule-Logik.
- LER-Demo mit Alert-State, Reserve-Mode und Recovery-Fenster.
- Forschungs-/Demo-Szenario, das Nichtlieferung von kontrahierten
  Reserven explizit vermeiden oder bewerten soll.

**Klare Leitplanke:** Es werden **kein Code, keine Dateien und keine
Code-Schnipsel** aus `BESS-Simulation` übernommen. Die Übernahme beschränkt
sich auf fachliche Konzepte, Regelideen und Testfälle als Vorlage.
Direkte Referenzierung konkreter Klassen-/Funktions-/Variablennamen oder
Signaturen aus dem Fremdcode ist ausgeschlossen.

## Go/No-Go-Kriterien (kurz)

**Go (Trigger aktiviert) wenn alle 6 Kriterien erfüllt sind):**

1) Produktives Ziel ist klar eingegrenzt auf **einen** dieser Use-Cases:
    - Reserve-Market-Agent für FCR/aFRR,
    - BESS-SOC-Management-Agent mit Intraday-/Market-Logik,
    - LER-Alert/Recovery-Demo,
    - Reserve-Unterlieferungs-Risiko-Analyse (Nichtlieferung kontrahierter Reserven) über dedizierten Agenten `ReserveUnderdeliveryRiskAgent`.

2) Es existiert mindestens ein **verbindlicher fachlicher Owner** (Name/Team) und
   ein Slice-Slot in `planning/planning/README.md`.

3) **M3-konforme technische Leitplanken** sind verbindlich bestätigt:
   - Keine unkontrollierten Zufalls-/Zeitquellen im Core (`random.*`, `np.random`, `secrets`, Zeitquellen),  
     außer explizit zugelassener `RandomPort`/Scenario-Event-Pfad.
   - keine neuen `pandas`/`numpy`/`scipy`-abhängigkeiten im Hexagon-Core,
   - keine neuen Nicht-Determinismuspfade ohne `RandomPort`/Events.

4) Datenbedarf ist beschraenkt auf: vorhandene Szenario-Events + optionaler
   adaptergespeister CSV/Excel-Import (nicht als Kernformat).

5) Keine direkte Code-Übernahme: Es werden keine Klassen/Funktionen aus
   `BESS-Simulation` portiert oder in den Core übernommen. Direkte Referenz
   auf Fremdcode-APIs, Methodennamen oder Implementierungsdetails ist
   ausgeschlossen. Nur fachliche Muster, Regelideen und Ergebnislogik dienen
   als Vorlage.

6) Keine Rechtsblockade: externer Code- oder Daten-Repo-Zugriff ist
   dokumentiert als **nur als Vorlage**; keine Copy-Paste-Übernahme.

**Hinweis zur operativen Prüfung (nicht automatisierbar):**
Vor Pull-Request-Merge sind die folgenden manuellen Gate-Nachweise im PR-Text erforderlich:
- Zielbild-Entscheidungs-Log (welcher Use-Case, warum kein anderer)
- Owner/Team bestätigt mit Datum + Name
- Slice-Eintrag verlinkt und lesbar
- Rechts-Check notiert: Repo, Lizenz, Freigabestatus, Prüfstelle

**No-Go (keine Aktivierung):**

1) Kein Owner/kein klarer Scope im Ticketing/README.

2) Abweichung vom Grid-Gym-Core-Vertrag ist geplant:
   - neuer Battery-Core statt `BatteryDevice`-Kommandokette,
   - zufallsbasierte Kernlogik ohne reproduzierbaren Seed- oder
     Event-Mechanismus,
   - float-basierte Simulation als Vertragsgrundlage.

3) Es gibt sichtbare Abhängigkeiten, die direkt gegen Architekturrichtlinien
   verstoßen (pandas/Excel als Primär-IO im Core, neue Non-Determinism-Quellen).

4) Keine klare DoD-Definition für Algorithmus- und Integrationstests.

## Operative Go/No-Go- und DoD-Prüfchecks (hard; teils automatisch, teils manuell)

Alle Punkte gelten als Hard-Gates für die Aktivierung. Die Prüfinfos pro Punkt sind
direkt im Slice-PR zu dokumentieren.

- Architektur:
  - Kein neuer `pandas`/`numpy`/`scipy`-Import im `grid_gym/**/core/**`.  
    Nachweis (automatisch): `rg -n "^\\s*import\\s+(pandas|numpy|pd|np|scipy)|^\\s*from\\s+(pandas|numpy|scipy)\\s+import" grid_gym/**/core --glob '*.py'`
  - Persistierter Kernzustand in neuem Core-Code nutzt keine neuen `float`-Felder; bevorzugt `Decimal`/werte-stabile Typen.  
    Nachweis (manuell + Review): Kern-Data-Typen im neuen Core-Code auf `float` persistierte Felder prüfen.
  - `BatteryDevice` bleibt einziger Core-Adapterpfad (`set_power_kw`); keine neuen Kernentitäten mit Akku-Logik.  
    Nachweis (manuell): Architektur-Review im neuen Core-Code, keine neue Batteriemodelle oder alternative Command-Pfade.
- Determinismus:
  - Zufalls-/Nichtdeterminismusquellen im neuen Core-Code sind ausschließlich über einen expliziten `RandomPort` dokumentiert; andere Quellen sind ausgeschlossen.  
  Nachweis (automatisch):  
  `rg -n "random\\.(random|uniform|randint|choice|shuffle|randrange|sample)|secrets\\.|np\\.random|numpy\\.random|time\\.time\\(|time\\.perf_counter\\(|datetime\\.datetime\\.now\\(|datetime\\.datetime\\.utcnow\\(" grid_gym/**/core --glob '*.py'`
  - Alle nicht-deterministischen Pfade sind als Scenario-Events modelliert und im Snapshot-Replay-relevant dokumentiert.  
    Nachweis (manuell): Gegenüberstellung Testfokus + Scenario-Doku auf vollständige Repräsentation.
- Daten/IO:
  - `numpy`/`pandas` dürfen nur in Adaptern/Utilities (nicht in `core`) auftauchen.  
    Nachweis (automatisch): `rg -n "^\\s*import\\s+(pandas|numpy|pd|np|scipy)|^\\s*from\\s+(pandas|numpy|scipy)\\s+import" grid_gym/**/core --glob '*.py'`
  - Keine neuen Kernformate im YAML/Scenario; externe CSV-/Excel-Adapter nur als optionale Randintegration mit Adapternotiz.
- Nachweise im Slice-PR:
  - Jeder Punkt aus der DoD ist mit Test-/Code-Nachweis verlinkt.
  - Snapshot-Feldliste ist vollständig dokumentiert: `reserve_mode`, `recovery_time`, `T_FCR`, geplante `MarketSchedule`.

## 1-Page-DoD fuer Aktivierung (MVP-Definition)

Aktivierung ist nur dann abgeschlossen, wenn **in einem Slice-Start-Pull-Request** alle Punkte vorliegen:

- **ADR/Plan**: Ein ADR oder Slice-Plan legt Scope auf **einen** Zielagenten fest  
  (`ReserveMarketAgent`, `BessSocManagementAgent`, `LerRecoveryAgent` oder `ReserveUnderdeliveryRiskAgent`).
- **Datenmodell**: Typed Dataclasses für mindestens
  `ReserveProduct`, `MarketSchedule`, `AlertState`/`RecoveryState` sind definiert.
- **Algorithmen-Portabilität**: Die fachliche Logik wird in eigenen, konformen
  Kernfunktionen neu implementiert (nicht als Portierung von fremdem Quellcode),
  je ein Satz expliziter Beispieltests.
- **Core-Vertrag**: Steuerung erfolgt ausschließlich über
  `set_power_kw`-Kommandos an bestehende `BatteryDevice`-Instanzen; kein neues
  Battery-Modell im Core.
- **Determinismus**: Keine unkontrollierten Zufalls-/Zeitquellen im Core; entweder
  `RandomPort` oder explizite Scenario-Events, inklusive Snapshot-relevanter
  Feldliste (`reserve_mode`, `recovery_time`, `T_FCR`, geplante Schedules).
  - Nachweis:
    - `rg -n "random\\.(random|uniform|randint|choice|shuffle|randrange|sample)|secrets\\.|np\\.random|numpy\\.random|time\\.time\\(|time\\.perf_counter\\(|datetime\\.datetime\\.now\\(|datetime\\.datetime\\.utcnow\\(" grid_gym/**/core --glob '*.py'` darf keine Treffer liefern.
- **Testnachweis**: mind. 1 Unit-Test je Kernfunktion + 1 Integrationstest
  (Battery + GridModel + Agent) sind im Scope.
- **Hard-Gate-Nachweis**: PR enthält einen Abschnitt "Validation Checklist" mit mindestens den oben definierten operativen Checks (inkl. Screenshot/Link auf Command-Output o. Ä.).
- **No-Negotiation**: Kein Excel-Settings-Format als neues Kanonisches
  Szenarioformat; optionaler Adapter (z. B. CSV/Excel) nur am Rand.
- **Rechtliche Freigabe**: Lizenz- und IP-Prüfung der Referenzquelle ist
  dokumentiert (Repository, Lizenztyp, Freigabenote), inklusive Prüfstelle und
  Datum, und der PR enthält den Legal-Nachweis als DoD-Beitrag.
- **Preflight vollständig**: Die Felder in **Aktivierungs-Preflight**
  (`Owner`, `Slice-Eintrag`, `Legal Clearance`) sind mit konkreten Werten
  belegt.
- **Go-Live-Entscheidung**: Dokument-Lebenszyklus bleibt **Open** als Planungsstatus.
  Die Aktivierung ist nur bei `Activation Gate: Approved` erlaubt.
  Für ein No-Go gilt `Activation Gate: Blocked`.

## Einschaetzung

**Nutzwert: hoch als fachliche Vorlage.** Das Projekt enthält konzeptionelle
Verfahrenslogiken fuer:

- Worst-Case-Energiebedarf aus FCR, FRR, geplanten ID-Trades, Wirkungsgrad und
  Selbstentladung.
- Exhaustive Worst-Case-Prüfung ueber einen Lookahead-Horizont.
- LER Alert-State-Handling inklusive Mindestaktivierungszeit, Reserve-Mode-
  Transition und Recovery-Zeitfenster.
- Freiwillige FRR-Bid-Ermittlung aus verbleibender Leistung und Energie nach
  Worst-Case-Absicherung.
- Zwei-BESS-Fleet-Logik und optionales Minimum-Cycling.

**Nutzwert: niedrig als technische Codebasis.** Direkte Uebernahme
passt nicht zu den bestehenden `grid-gym`-Vertraegen:

- Excel-Config ist layout-gekoppelt statt YAML-/Scenario-Loader.
- Core-Code nutzt `pandas`, `numpy`, `float` und globale
  `random.random()`-Entscheidungen; `grid-gym` fordert deterministische
  Ports, `Decimal`-Semantik im Core und Replay-faehige Snapshots.
- Output ist Excel/Matplotlib-orientiert statt Telemetrie-/Persistenz-
  Adapter.
- Keine Tests im Ordner gefunden.
- Keine sichtbare License-Datei im Ordner gefunden; vor Code-
  Uebernahme waere Lizenzklaerung Pflicht.
- Architektur passt nicht zur Hexagon-Struktur (`core`, `ports`,
  `adapters`) und wuerde Import-/Strict-Type-Gates brechen.

## Erwartete Lieferung

Bei Aktivierung als eigener Slice:

- ADR oder Slice-Plan fuer einen der Zielagenten  
  (`ReserveMarketAgent`, `BessSocManagementAgent`, `LerRecoveryAgent` oder  
  `ReserveUnderdeliveryRiskAgent`) und bestehende
  `BatteryDevice`-Instanzen ueber Commands steuert statt ein neues
  Battery-Modell einzufuehren.
- Domain-Typen fuer Reserveprodukte und Market-Schedules, z. B.
  FCR-Kapazitaet, FRR-Up/Down-Kapazitaet, ID-Schedule,
  Alert-State-Status.
- Pure-Core-Implementierung der fachlichen Algorithmen ohne
  `pandas`/`numpy` im Hexagon-Core:
  - Worst-Case-Energiebedarf,
  - Lookahead-Faehigkeitspruefung,
  - LER Reserve-/Recovery-State,
  - optionale FRR-Bid-Reduktion.
- Scenario-YAML-Erweiterung fuer Frequenz-/FRR-Zeitreihen oder
  einen Adapter-Spike fuer externe CSV/Excel-Daten am Rand.
- Deterministische Markt-Clearing-Entscheidung ueber `RandomPort`
  oder rein explizite Scenario-Events; keine Nutzung von
  `random.random()`.
- Snapshot-/Resume-Vertrag fuer Agent-State (`reserve_mode`,
  `recovery_time`, `T_FCR`, geplante ID-/FRR-Schedules).
- Unit-Tests fuer die Algorithmen und mindestens ein
  Integrationstest mit Battery + GridModel + Agent.

## Nicht uebernehmen

- `BESS` als Ersatz fuer `BatteryDevice`. Das bestehende Device deckt
  SOC-Fortschreibung, Ramp-Limits, Snapshots, Telemetrie und Fault-State
  bereits im `grid-gym`-Vertrag ab.
- Excel-Output und Matplotlib-Visualizer.
- Excel-Settings-Layout als kanonisches Szenarioformat.
- Globale Zufallsquelle, tabellarische Zeitreihen als Core-State oder
  Float-basierte Replay-Pfade.

## Migrationsskizze

1. Fachliche Regeln zu:
   - Worst-Case-Energiebedarf,
   - Lookahead-basierter Worst-Case-Prüfung,
   - Alert-/Recovery-Zustandswechseln und
   - optionaler FRR-Gewinn-/Gebotsanpassung
   fachlich abkoppeln.
2. Kleine, typed Dataclasses fuer Schedules und Reserveverpflichtungen
   definieren.
3. Algorithmen gegen explizite Sequenzen testen, nicht gegen
   tabellarische Repräsentationen.
4. Einen Agent bauen, der daraus `set_power_kw`-Commands an Battery-
   Devices erzeugt.
5. Optional spaeter CSV/Excel-Zeitreihen als Adapter-Import anbieten,
   aber nie als Core-Abhaengigkeit.

## Out-of-scope

- Marktpreisoptimierung oder Erlosmodell.
- Vollstaendige europaeische Regulatorik-Abdeckung.
- Ersatz des bestehenden Battery-Device-Modells.
- UI fuer Reserveprodukte.
- Validierung gegen die originale Paper-/Zenodo-Datenbasis; das waere
  ein separater Reproduktions-Spike.
