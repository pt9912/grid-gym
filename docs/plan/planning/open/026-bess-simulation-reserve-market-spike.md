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
  - keine neuen persistierten `float`-Felder im Kernzustand; bevorzugt `Decimal`.
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
  - Kein neuer `pandas`/`numpy`/`scipy`-Import im `src/grid_gym/hexagon/core/**/*.py`.  
    Nachweis (automatisch):  
    `BASE_BRANCH="${BASE_BRANCH:-origin/main}"`
    `mapfile -t CHANGED_CORE_FILES < <(git diff --name-only --diff-filter=AMR "$BASE_BRANCH"...HEAD -- 'src/grid_gym/hexagon/core/**/*.py')`
    `if [ "${#CHANGED_CORE_FILES[@]}" -gt 0 ]; then VIOLATION=0; for file in "${CHANGED_CORE_FILES[@]}"; do rg -n "^\\s*import\\s+(pandas|numpy|pd|np|scipy)|^\\s*from\\s+(pandas|numpy|scipy)\\s+import" "$file" && VIOLATION=1; done; [ "$VIOLATION" -eq 0 ] || { echo "Forbidden imports detected in core."; exit 1; }; else echo "No changed core files to check."; fi`
  - Persistierter Kernzustand in neuem Core-Code nutzt keine neuen `float`-Felder; bevorzugt `Decimal`/werte-stabile Typen.  
    Nachweis:
    - automatisiert: `python tools/check_core_determinism.py --mode state-floats -- "${CHANGED_CORE_FILES[@]}"`
    - manuell: Architektur-Review im neuen Core-Code, insbesondere persistierte State-/Snapshot-Felder.
  - `BatteryDevice` bleibt einziger Core-Adapterpfad (`set_power_kw`); keine neuen Kernentitäten mit Akku-Logik.  
    Nachweis (manuell): Architektur-Review im neuen Core-Code, keine neue Batteriemodelle oder alternative Command-Pfade.
- Determinismus:
  - Zufalls-/Nichtdeterminismusquellen im neuen Core-Code sind ausschließlich über einen expliziten `RandomPort` dokumentiert; andere Quellen sind ausgeschlossen.  
  Nachweis (automatisch):  
  `BASE_BRANCH="${BASE_BRANCH:-origin/main}"`
  `mapfile -t CHANGED_CORE_FILES < <(git diff --name-only --diff-filter=AMR "$BASE_BRANCH"...HEAD -- 'src/grid_gym/hexagon/core/**/*.py')`
  `if [ "${#CHANGED_CORE_FILES[@]}" -gt 0 ]; then python tools/check_core_determinism.py --mode determinism -- "${CHANGED_CORE_FILES[@]}"; fi`
  - Alle nicht-deterministischen Pfade sind als Scenario-Events modelliert und im Snapshot-Replay-relevant dokumentiert.  
    Nachweis (manuell): Gegenüberstellung Testfokus + Scenario-Doku auf vollständige Repräsentation.
- Daten/IO:
  - `numpy`/`pandas`/`scipy` dürfen nur in Adaptern/Utilities (nicht in `core`) auftauchen.  
    Nachweis (automatisch):
    `BASE_BRANCH="${BASE_BRANCH:-origin/main}"`
    `mapfile -t CHANGED_CORE_FILES < <(git diff --name-only --diff-filter=AMR "$BASE_BRANCH"...HEAD -- 'src/grid_gym/hexagon/core/**/*.py')`
    `if [ "${#CHANGED_CORE_FILES[@]}" -gt 0 ]; then VIOLATION=0; for file in "${CHANGED_CORE_FILES[@]}"; do rg -n "^\\s*import\\s+(pandas|numpy|pd|np|scipy)|^\\s*from\\s+(pandas|numpy|scipy)\\s+import" "$file" && VIOLATION=1; done; [ "$VIOLATION" -eq 0 ] || { echo "Forbidden imports detected in core."; exit 1; }; else echo "No changed core files to check."; fi`
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
    - `BASE_BRANCH="${BASE_BRANCH:-origin/main}"`
    - `mapfile -t CHANGED_CORE_FILES < <(git diff --name-only --diff-filter=AMR "$BASE_BRANCH"...HEAD -- 'src/grid_gym/hexagon/core/**/*.py')`
    - `if [ "${#CHANGED_CORE_FILES[@]}" -gt 0 ]; then python tools/check_core_determinism.py --mode determinism -- "${CHANGED_CORE_FILES[@]}"; fi` darf keine Treffer liefern.
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

### Zusatz: Robuster automatischer Kern-Check (AST-basiert, empfohlen)

Regex allein deckt nicht alle Import-/Alias-/Wrapper-Fälle ab. Für CI oder lokale Checks wird empfohlen, den folgenden deterministischen Kern-Scan als Script zu ergänzen:
Die referenzierte Implementierung liegt als `tools/check_core_determinism.py` vor.

```
#!/usr/bin/env python3
"""Core-Checks für neue Dateien im hexagon/core.

Einsatz:
  python tools/check_core_determinism.py --mode determinism --mode state-floats -- <files...>
"""
from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable
from pathlib import Path
import re
import sys

FORBIDDEN_MODULES = {"random", "secrets", "uuid", "time", "datetime", "numpy"}
ALLOWED_IDENTIFIERS = {"RandomPort", "ScenarioEvent", "RandomEvent", "EventPort"}


def _collect_forbidden_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_MODULES:
                    aliases[alias.asname or root] = root
        if isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            root = node.module.split(".")[0]
            if root in FORBIDDEN_MODULES:
                for alias in node.names:
                    if alias.name == "*":
                        aliases[f"*from:{root}"] = root
                    else:
                        aliases[alias.asname or alias.name] = root
    return aliases


def _call_root_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        child = node
        while isinstance(child, ast.Attribute):
            value = child.value
            if isinstance(value, ast.Name):
                return value.id
            child = value
    return None


def _has_float_annotation(annotation: ast.AST | None) -> bool:
    if annotation is None:
        return False
    return re.search(r"(?<![.\\w])float(?![\\w])", ast.unparse(annotation)) is not None


def _is_float_call(node: ast.Call) -> bool:
    return (isinstance(node.func, ast.Name) and node.func.id == "float") or (
        isinstance(node.func, ast.Attribute) and node.func.attr == "float"
    )


def _is_dataclass_decorator(expr: ast.expr) -> bool:
    if isinstance(expr, ast.Name) and expr.id == "dataclass":
        return True
    if isinstance(expr, ast.Attribute) and expr.attr == "dataclass":
        return True
    if isinstance(expr, ast.Call):
        return _is_dataclass_decorator(expr.func)
    return False


def _is_dataclass(node: ast.ClassDef) -> bool:
    return any(_is_dataclass_decorator(dec) for dec in node.decorator_list)


def _check_determinism(tree: ast.AST, file: Path, aliases: dict[str, str]) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_MODULES:
                    violations.append(f"{file}:{node.lineno}:{node.col_offset}: forbidden import '{alias.name}'")

        if isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            root = node.module.split(".")[0]
            if root in FORBIDDEN_MODULES and any(alias.name == "*" for alias in node.names):
                violations.append(f"{file}:{node.lineno}:{node.col_offset}: forbidden wildcard import from '{node.module}'")
            elif root in FORBIDDEN_MODULES:
                violations.append(f"{file}:{node.lineno}:{node.col_offset}: forbidden from-import '{node.module}'")

        if isinstance(node, ast.Call):
            root = _call_root_name(node.func)
            if not root or root in ALLOWED_IDENTIFIERS:
                continue
            mapped = aliases.get(root)
            if mapped in FORBIDDEN_MODULES:
                violations.append(
                    f"{file}:{node.lineno}:{node.col_offset}: forbidden core-call '{ast.unparse(node.func)}()' via '{mapped}'"
                )
    return violations


def _check_state_floats(tree: ast.AST, file: Path) -> list[str]:
    violations: list[str] = []

    def walk(node: ast.AST, in_dataclass: bool = False) -> None:
        if isinstance(node, ast.ClassDef):
            dataclass_scope = in_dataclass or _is_dataclass(node)
            for stmt in node.body:
                walk(stmt, in_dataclass=dataclass_scope)
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return

        if in_dataclass and isinstance(node, ast.AnnAssign):
            if _has_float_annotation(node.annotation):
                violations.append(f"{file}:{node.lineno}:{node.col_offset}: typed float field '{ast.unparse(node.target)}'")
            if isinstance(node.value, ast.Call) and _is_float_call(node.value):
                violations.append(f"{file}:{node.lineno}:{node.col_offset}: float() default in persisted field '{ast.unparse(node.target)}'")

        for child in ast.iter_child_nodes(node):
            walk(child, in_dataclass)

    walk(tree, False)
    return violations


def _check_files(paths: Iterable[Path], modes: tuple[str, ...]) -> list[str]:
    bad: list[str] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        aliases = _collect_forbidden_aliases(tree)
        if "determinism" in modes:
            bad.extend(_check_determinism(tree, path, aliases))
        if "state-floats" in modes:
            bad.extend(_check_state_floats(tree, path))
    return bad


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--mode", action="append", required=True, choices=("determinism", "state-floats"))
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    bad = _check_files([Path(p) for p in args.files], tuple(args.mode))
    for violation in bad:
        print(violation)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

Beachtung:
- Bei der Code-Bewertung muss die Freigabeliste auf erlaubte Zufalls-/Zeitquellen (`RandomPort`, Scenario-Event-Pfade) explizit dokumentiert und im Skript (`tools/check_core_determinism.py`) berücksichtigt werden.
- Für Float-Felder sind neben `float`-Typannotationen auch `float(...)`-Konvertierungen im persistierten State/Dataclass-Pfad zu prüfen.

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
