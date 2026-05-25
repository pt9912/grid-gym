# 028 — Import-Contract fuer modul-lokale `_*Error`-Klassen in `tick_loop.py`

**Status:** In Progress — aktiviert 2026-05-25 (Move open → in-progress).
**Quelle:** Code-Reviewer-Findings auf Slice 027 (Commits
`b1bf914..83b1c50`); Slice 027 Review-Folge L-5.
**Ziel:** Verhindern, dass die zehn modul-lokalen Resume-Diagnostik-
Sub-Klassen (`_DeviceMissingSubSnapshotError`, `_AgentSnapshotDiffersError`,
etc., siehe `src/grid_gym/hexagon/core/simulation/tick_loop.py:1299..1391`)
ausserhalb des Moduls importiert werden.
**Scope-Entscheidung (2026-05-25):** Option 2 wird **generisch** auf
das `tick_loop`-Modul angewandt — verboten ist **jeder** `from
grid_gym.hexagon.core.simulation.tick_loop import _<...>`-Import
ausserhalb des `tick_loop.py`-Moduls selbst (nicht nur die zehn
Resume-Error-Klassen). Begruendung: Akzeptanz §3 spricht von „ein
bewusster Verstoss `from tick_loop import _DeviceMissingSubSnapshotError`
bricht `make arch-check`" — Sub-Klassen sind nur das aktuelle
Anwendungs-Beispiel. Eine generische Regel auf Modul-Ebene faengt
auch kuenftige modul-lokale Underscore-Helfer ohne Re-Triage.
Nicht Teil dieses AC: private Imports aus anderen Hexagon-Modulen
(eigene Folge-ADR, wenn ueberhaupt).

---

## 1. Kontext

Slice 027 Paket B (Commit `e779951`) hat zehn typisierte Sub-Klassen
modul-lokal in `tick_loop.py` definiert (Resume-Diagnostik-Spezialisierungen
von `TickLoopAgentSnapshotDeviceMismatchError`,
`TickLoopAgentSnapshotGridModelMismatchError`,
`TickLoopAgentSnapshotLoadOverlayMismatchError`,
`TickLoopAgentInstanceSnapshotMismatchError`). Jede traegt die spezifische
Diagnose-Message in `__init__`; Aufrufer reichen strukturierte Args durch.

Python-Konvention: Underscore-Prefix signalisiert „nicht public". Aber das
ist nur soziale Konvention — `from grid_gym.hexagon.core.simulation.tick_loop
import _DeviceMissingSubSnapshotError` funktioniert technisch und faengt
weder `import-linter` noch `tools/arch_check.py` ab.

Tests fangen aktuell ueber die Public-Base-Klassen (z. B.
`pytest.raises(TickLoopAgentSnapshotDeviceMismatchError)`). Reviewer-Sorge:
ein zukuenftiger Refactor koennte versehentlich auf die Sub-Klassen
zugreifen und damit den Refactor-Bewegungsspielraum einschraenken.

## 2. Vorgehen

Optionen:

1. **Neuer import-linter-Contract**:
   ```toml
   [[tool.importlinter.contracts]]
   name = "AC-TICK-LOOP-PRIVATE-ERRORS"
   type = "forbidden"
   source_modules = ["grid_gym"]
   forbidden_modules = ["grid_gym.hexagon.core.simulation.tick_loop._*Error"]
   ```
   Problem: import-linter unterstuetzt keine Wildcard-Forbidden-Modules
   am Symbol-Level (nur Modul-Level). Funktioniert nur, wenn die Sub-
   Klassen in ein Sub-Modul `tick_loop/_resume_errors.py` ausgelagert
   werden.

2. **Neuer arch_check-Contract** in `tools/arch_check.py`:
   `AC-TICK-LOOP-PRIVATE-RESUME-ERRORS` mit AST-basiertem Check, der
   alle `from grid_gym.hexagon.core.simulation.tick_loop import _xxx`-
   Statements in `src/**` und `tests/**` ausserhalb des `tick_loop.py`-
   Moduls selbst meldet.

3. **`__all__`-Block** in `tick_loop.py` — beschraenkt `from tick_loop
   import *`-Verhalten, aber NICHT direkten Symbol-Import. Reine Doc-
   Konvention; faengt keine Verstoesse maschinell.

**Empfehlung:** Option 2 — neuer arch_check-Contract.

## 3. Akzeptanz

- Neuer Contract `AC-TICK-LOOP-PRIVATE-RESUME-ERRORS` in
  `tools/arch_check.py` registriert (13. arch_check-Contract).
- `_EXPECTED_CHECK_FUNCTIONS` in `tests/unit/test_arch_check_registration.py`
  + `expected_arch_check_contracts`-Count auf 13 angehoben.
- `Makefile`-Help-Text `(19 A-1-Contracts: 6 import-linter + 13 arch_check)`.
- `make gates`-`arch-check (19 contracts)` gruen.
- Smoke-Test: ein bewusster Verstoss (`from tick_loop import
  _DeviceMissingSubSnapshotError` in einem Test) bricht `make arch-check`
  mit klarer Message.

## 4. Wandert nach

`done/028-tick-loop-private-error-import-contract.md` mit Closure-Notiz,
nachdem der Contract `Kept` ist.

## 5. Bezug

- Slice 027 Review-Folge L-5 (Reviewer-Empfehlung: „Optional — ... fuer
  die Welle 5b/6-Hardening. Nicht fuer diesen Slice.")
- ADR 0002 §A-1 (arch_check-Contract-Pattern; siehe ADR 0029
  `AC-NO-COVERAGE-PRAGMA` und ADR 0024 §4.5.5 `AC-OTLP-ADAPTER-NO-TIME`
  als Praezedenz fuer eng-skoperte Contracts).
