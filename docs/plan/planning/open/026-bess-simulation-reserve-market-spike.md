# 026 — BESS-Simulation als Vorlage fuer Reserve-Market-/LER-Agent

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-24
**Quelle-Repo:** Fachliche Sichtung von [`BESS-Simulation`](https://github.com/flpp-signature/BESS-Simulation)
gegen den aktuellen `grid-gym`-Stand.

---

## Trigger

`/Development/grid/BESS-Simulation/` ist ein kleines Python-Tool fuer
BESS-Reservebereitstellung mit FCR/aFRR, Intraday-SOC-Restoration,
LER Alert/Recovery und freiwilligen FRR-Energiegeboten. Der Kern ist
fachlich relevant fuer `grid-gym`, aber nicht als Drop-in-Code geeignet.

Aktivieren, sobald eines der folgenden Themen konkret geplant wird:

- Reserve-Market-Agent fuer FCR/aFRR-Strategien.
- BESS-SOC-Management-Agent mit Intraday- bzw. Market-Schedule-Logik.
- LER-Demo mit Alert-State, Reserve-Mode und Recovery-Fenster.
- Forschungs-/Demo-Szenario, das Nichtlieferung von kontrahierten
  Reserven explizit vermeiden oder bewerten soll.

## Einschaetzung

**Nutzwert: hoch als fachliche Vorlage.** Das Projekt enthaelt
konkrete Algorithmen fuer:

- Worst-Case-Energiebedarf aus FCR, FRR, geplanten ID-Trades,
  Wirkungsgrad und Selbstentladung (`BESS.E_worst`).
- Exhaustive Worst-Case-Pruefung ueber einen Lookahead-Horizont
  (`BESS.exhaustive_worst_case`).
- LER Alert-State-Handling inklusive `TminLER`, Reserve-Mode-
  Transition und Recovery-Zeitfenster.
- Freiwillige FRR-Bid-Ermittlung aus verbleibender Leistung und
  Energie nach Worst-Case-Absicherung.
- Zwei-BESS-Fleet-Logik und optionales Minimum-Cycling.

**Nutzwert: niedrig als technische Codebasis.** Direkte Uebernahme
passt nicht zu den bestehenden `grid-gym`-Vertraegen:

- Excel-Config ist layout-gekoppelt (`settings.xlsx`,
  `config.py::ConfigurationManager`) statt YAML-/Scenario-Loader.
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

- ADR oder Slice-Plan fuer einen `ReserveMarketAgent` bzw.
  `BessSocManagementAgent`, der bestehende `BatteryDevice`-Instanzen
  ueber Commands steuert statt ein neues Battery-Modell einzufuehren.
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
- Globale Zufallsquelle, mutable `pandas.Series` als Core-State oder
  Float-basierte Replay-Pfade.

## Migrationsskizze

1. Fachliche Regeln aus `BESS.E_worst`,
   `BESS.exhaustive_worst_case`, `BESS.reserve_mode_act`,
   `BESS.check_recovery` und `BESS.volunt_FRR` isolieren.
2. Kleine, typed Dataclasses fuer Schedules und Reserveverpflichtungen
   definieren.
3. Algorithmen gegen explizite Sequenzen testen, nicht gegen
   `pandas.Series`.
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
