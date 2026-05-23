# ADR 0029 — AC-NO-COVERAGE-PRAGMA als 11. tools/arch_check.py-Contract (Schaerfung von ADR 0002 §A-1)

**Status:** Accepted — kein Validierungs-Spike erforderlich.
Direkter `Proposed → Accepted`-Sprung per `ADR 0006 §2`-Klausel
(„ADR ohne Validierungsbedarf").
**Datum:** 2026-05-23
**Status geaendert am:** 2026-05-23 — `Proposed → Accepted`.
**Bezug:**
[`ADR 0002`](0002-language-and-build-stack.md) §A-1
(Architekturtests-Tabelle, schaerft diese ADR als reine Erweiterung),
[`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
§3 (Aenderungsregeln nach `Accepted`),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Schaerfung-ohne-
Supersedes-Pattern; ADR 0029 ist selbst eine Schaerfung in dieser
Form).

---

## 1. Kontext

`coverage.py` unterstuetzt Inline-Pragmas, die Code von der
Messung ausnehmen:

- `# pragma: no cover` — schliesst die markierte Zeile (oder den
  markierten Block) aus dem Statement-Coverage-Report aus.
- `# pragma: no branch` — schliesst die markierte Verzweigung
  aus dem Branch-Coverage-Report aus.
- `# pragma: exclude file` (Datei-Header) — schliesst die gesamte
  Datei aus.

In der Praxis erlauben diese Marker, schlecht oder gar nicht
getesteten Code zu verstecken, ohne dass die `make
coverage-gate`-/`coverage-gate-critical`-Schwellen (90/85 line,
90 critical-branch) anschlagen. Damit kann eine Welle den
Coverage-Gate technisch gruen halten, obwohl produktive Pfade
nicht testabgedeckt sind.

Bestaendiger Bestand vor dieser ADR (Inventar 2026-05-23):

- 29× `# pragma: no cover — Protocol-Stub` auf `...`-Ellipsis-
  Bodies in `hexagon/ports/driven/*.py` und
  `hexagon/core/*/_protocol.py`.
- 2× `# pragma: no cover` als defensive `isinstance`-Guards in
  `hexagon/core/scenario/validator.py` nach vorgelagerter
  `_assert_str`-Validation (dead code).
- 1× `# pragma: no cover — vorgelagert von initialize geblockt`
  als unreachable `return ()` in `hexagon/core/scenario/loader.py`.
- 1× `# pragma: no cover` an einem `if TYPE_CHECKING:`-Header
  in `hexagon/core/domain/scenario.py` (redundant — TYPE_CHECKING
  wird bereits ueber den separaten `exclude_lines`-Eintrag
  ausgeschlossen).

Alle vier Klassen lassen sich ohne Pragma-Annotation loesen:

- Protocol-Stubs werden ueber den `^\s*\.\.\.\s*$`-Regex in
  `[tool.coverage.report].exclude_lines` global ausgenommen
  (sie sind nie zur Laufzeit ausgefuehrt — `...` ist Typing-
  Marker, kein Test-Pfad).
- Defensive Dead-Code-Branches nach vorgelagerter Validation
  werden geloescht; statt `if not isinstance(...):` reicht ein
  `cast(...)` an der bereits validierten Stelle.
- Unreachable Fallback-Returns werden geloescht; der erreichbare
  Pfad wird direkt zurueckgegeben (ohne defensive Nullzeile).
- `if TYPE_CHECKING:`-Header sind bereits ueber den Standard-
  `exclude_lines`-Eintrag abgedeckt — der Pragma-Zusatz war
  redundant.

`ADR 0002 §A-1` listet zehn `tools/arch_check.py`-Contracts
(AC-HEXAGON-PURE, AC-NO-JSON, AC-NO-TIME, AC-NO-RAND,
AC-NO-IO-MOD nested, AC-DOMAIN-FROZEN, AC-NO-GOD-UTILS,
AC-TYPED-ERRORS, AC-NO-CYCLES, AC-ADAPTER-LIGHTWEIGHT) sowie
sechs `import-linter`-Contracts (sechzehn A-1-Contracts
insgesamt). Diese ADR fuegt einen elften `tools/arch_check.py`-
Contract hinzu (siebzehn A-1-Contracts insgesamt) — die
verbleibenden zehn arch_check-Contracts und die sechs
import-linter-Contracts bleiben **textlich unveraendert**
(`ADR 0006 §3` Accepted-Immutability).

---

## 2. Entscheidung

`tools/arch_check.py` `main()` wird um einen elften Check
ergaenzt:

**AC-NO-COVERAGE-PRAGMA** — kein Coverage-Pragma im Repo.

Implementierung (`_check_no_coverage_pragma`):

- Walked alle `*.py`-Dateien unter `src/grid_gym/**`.
- Pro Datei zeilenweise Suche nach den drei verbotenen Markern:
  - `pragma: no cover`
  - `pragma: no branch`
  - `pragma: exclude file`
- Jedes Vorkommen ist eine Violation
  (`AC-NO-COVERAGE-PRAGMA`, `{rel}:{lineno}`,
  `\`# {marker}\` verboten (Coverage-Gate-Disziplin)`).

Scope-Schnitt:

- **In-Scope:** `src/grid_gym/**`.
- **Out-of-Scope:** `tests/**`, `tools/**`, `docs/**`. Tests
  und Tooling werden nicht gescannt, weil dort legitime
  Pragma-Erwaehnungen in Test-Fixtures oder im
  Implementations-Code der Contract-Pruefung selbst auftreten
  duerfen (Self-Reference: `tools/arch_check.py` enthaelt die
  drei Marker-Strings in der Verbots-Konstante).

`coverage.report.exclude_lines` wird parallel angepasst:
`pragma: no cover` als Eintrag entfernt; stattdessen
`^\s*\.\.\.\s*$` aufgenommen (Protocol-Stub-Pattern). Beide
Aenderungen wirken zusammen — die Konfiguration laesst Pragmas
nicht mehr wirken, die Contract-Pruefung verbietet sie
zusaetzlich.

---

## 3. Begruendung

- **Coverage-Disziplin ist Gate-bezogen, nicht stylistisch.** Die
  drei Pragma-Marker sind die einzigen produktionsrelevanten
  Mechanismen, mit denen man einen Coverage-Gate (`>= 90/85`
  line, `>= 90` critical-branch) umgehen kann, ohne dass das
  in der Coverage-Zahl sichtbar wird. Andere „Skip"-Wege
  (`@pytest.mark.skip`, conditional imports) sind transparenter
  und ueber andere Gates erfasst.
- **Alternativen-Inventar zeigt, dass alle bisherigen
  Pragma-Vorkommen anders loesbar sind.** Protocol-Stubs ueber
  Regex-Exclude, Dead-Code per Loeschung, TYPE_CHECKING bereits
  abgedeckt. Keine offene Pragma-Anwendung blieb uebrig.
- **Schwester-Pattern zu AC-NO-TIME / AC-NO-RAND.** Beide
  verbieten Konstrukte projekt-weit, die in kontrollierten
  Konstellationen sinnvoll waeren, aber zu oft missbraucht
  werden (Wall-Clock im Determinismus-Kern bzw. Zufalls-Quellen
  ausserhalb `RandomPort`). AC-NO-COVERAGE-PRAGMA folgt
  derselben Logik fuer den Coverage-Gate-Disziplinraum.
- **Schaerfung ohne Supersedes (ADR 0011-Pattern).** ADR 0002
  bleibt textlich unveraendert; ADR 0029 ergaenzt die §A-1-
  Tabelle additiv um einen Eintrag. Konsistent zur Praezedenz
  ADR 0011, die genau diesen Pfad fuer §A-1-Erweiterungen
  vorsieht.

---

## 4. Reichweite

- ADR 0002 §A-1 bleibt textlich unveraendert (Accepted-
  Immutability per ADR 0006 §3).
- ADR 0029 wird im ADR-Index unter ADR 0002 in der
  „Schaerfungen / Folge-ADRs"-Spalte eingetragen (analog
  ADR 0008-Eintrag dort).
- Die Test-Konstante in
  `tests/unit/test_arch_check_registration.py`
  (`_EXPECTED_CHECK_FUNCTIONS` und
  `expected_arch_check_contracts`) wird auf 11 angehoben —
  der Test ist genau dafuer gebaut, dass ein neuer Contract
  eine sichtbare ADR-Korrespondenz hat.
- `tools/arch_check.py`-Header-Docstring listet den 11.
  Contract.
- `pyproject.toml [tool.coverage.report] exclude_lines` wird
  auf das neue Set (`raise NotImplementedError`,
  `if TYPE_CHECKING:`, `^\s*\.\.\.\s*$`) umgestellt — ohne
  `pragma: no cover`.

---

## 5. Operative Artefakte (Erstanwendung)

Mit dieser ADR sind die folgenden konkreten Aufraeum-Schritte
verbunden (alle in einem Commit, siehe Welle-5-Folge-Commit):

1. **Pragma-Removal** (32 Vorkommen):
   - 29× Protocol-Stub-Pragmas aus `hexagon/ports/driven/*.py`
     und `hexagon/core/*/_protocol.py` gestrichen.
   - 2× defensive `isinstance`-Guards in `validator.py`
     ersetzt durch `cast(str, ...)` an der bereits
     `_assert_str`-validierten Stelle.
   - 1× unreachable `return ()`-Fallback in `loader.py`
     geloescht; erreichbarer `list`-Pfad wird direkt
     zurueckgegeben.
   - 1× `# pragma: no cover` am `if TYPE_CHECKING:`-Header in
     `scenario.py` entfernt (Standard-`exclude_lines`-Eintrag
     deckt es ohnehin ab).

2. **`tools/arch_check.py` Erweiterung**:
   - Neue Funktion `_check_no_coverage_pragma(repo_root,
     src_root)`.
   - Registrierung in `main()` (11. Contract-Position).
   - Header-Docstring um den 11. Contract erweitert.

3. **`tests/unit/test_arch_check_registration.py` Update**:
   - `_EXPECTED_CHECK_FUNCTIONS` um `_check_no_coverage_pragma`
     erweitert.
   - `expected_arch_check_contracts = 10 → 11`.
   - Test-Docstring entsprechend angepasst.

4. **`pyproject.toml [tool.coverage.report]` Anpassung**:
   - `"pragma: no cover"` aus `exclude_lines` entfernt.
   - `"^\\s*\\.\\.\\.\\s*$"` aufgenommen (Protocol-Stub-Pattern).
   - Konfigurations-Kommentar erweitert um Verweis auf
     AC-NO-COVERAGE-PRAGMA.

5. **`docs/plan/adr/README.md`** (ADR-Index):
   - Neue Zeile fuer ADR 0029 in „Aktive ADRs" eingefuegt.
   - ADR-0002-Zeile in der „Schaerfungen / Folge-ADRs"-Spalte
     um den Querverweis auf ADR 0029 erweitert.

`make gates` bleibt cache-frei gruen ohne Override (Welle-5-
Hygiene-Folge, integriert sich in das Welle-5-DoD-Bild).

---

## 6. Konsequenzen

- **Positiv:** Coverage-Gates werden nicht mehr von Pragma-
  Annotationen unterlaufen. Der `make coverage-gate`-Anstieg
  oder -Abfall reflektiert die tatsaechliche Test-Abdeckung
  produktiver Pfade.
- **Positiv:** Defensive Dead-Code-Branches werden mit der
  Erstanwendung geloescht — das Repo verliert vier Stellen
  unerreichbaren Codes (`_assert_str`-Folge-Guards,
  `SmartMeterConfig`-Fallback).
- **Neutral:** Protocol-Stubs sind weiterhin von der Coverage
  ausgenommen, aber jetzt ueber Regex-Pattern statt einzelner
  Pragma-Annotationen. Skaliert besser bei neuen Protocols.
- **Neutral:** Der `tests/unit/test_arch_check_registration.py`-
  Test traegt jetzt 11 statt 10 erwartete Contracts; jeder
  weitere arch_check-Contract braucht weiterhin Folge-ADR plus
  Test-Konstant-Update — Disziplin-Pfad bleibt.

---

## 7. Nicht Gegenstand dieser ADR

- Scope-Erweiterung von `AC-NO-COVERAGE-PRAGMA` auf `tests/**`
  oder `tools/**` — bleibt explizit `src/grid_gym/**`-only.
  Falls sich in Tests legitime Pragma-Anwendungen herauskristal-
  lisieren (z. B. ein bewusst nicht-getesteter Print-Branch
  in einem Test-Helper), folgt eine Folge-ADR.
- Aenderung der Coverage-Schwellen (90/85 line, 90 critical-
  branch). Schwellen bleiben unveraendert; nur die Marker-
  Disziplin wird gehaertet.
- Migration bestehender `coverage.report.exclude_lines`-
  Eintraege auf eine andere Regex-Bibliothek oder Repository-
  globale Pattern-Sammlung — `pyproject.toml`-lokale Eintraege
  bleiben die Konfigurationsquelle.
- Wahl eines anderen Test-Coverage-Tools (`coverage.py` vs.
  `pytest-cov` vs. `slipcover`). Steht orthogonal zur Marker-
  Disziplin.
