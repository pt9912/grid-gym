# Spike-0 Ergebnisse (Living Document)

**Status:** In Progress — wird bis Welle-5-Abschluss fortgeschrieben
**Datum:** 2026-05-15 (Welle 2 abgeschlossen)
**Bezug:** [`spike-0.md`](spike-0.md), [`ADR 0002`](../../adr/0002-language-and-build-stack.md),
[`ADR 0005`](../../adr/0005-type-check-gate.md)

---

## 1. Zweck

Pflicht-Artefakt fuer die Acceptance-Entscheidung zu `ADR 0002` und
`ADR 0005`. Dokumentiert Welle-fuer-Welle den Gate-Status, die
sechzehn Verstoss-Branches aus Welle 4 (Branch × Gate Matrix) und
auffaellige Befunde, die aus dem Pre-Acceptance-Schliff erlaubt sind
(`ADR 0006` §3).

---

## 2. Welle-Status

| Welle | Liefergegenstand | Gates | Commit |
| ----- | ---------------- | ----- | ------ |
| 1 — Toolchain + Skelett | `pyproject.toml`, `uv.lock`, `.python-version`, `src/grid_gym/{hexagon/{core,ports},adapters}/`, `tools/arch_check.py`-Skelett, Smoke-Test | `make lint`/`format-check`/`typecheck`/`arch-check`/`test-unit`/`dep-audit`: **gruen** | `cb2246a` |
| 2 — A-2 Custom-Emitter | `hexagon/core/serialization/canonical.py` (79 stmts, 38 Branches), `test_canonical.py` (42 Tests inkl. 6 Property-Tests), `coverage-gate-critical` mit Build-Arg-Scope | `make test-unit` (44 passed), `make coverage-gate-critical CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization` (**100 % Line + Branch**) | `5298a0c` |
| 3 — `tools/arch_check.py` Contracts | offen | offen | — |
| 4 — Verstoss-Branches | offen | offen | — |
| 5 — Acceptance-Hebung | offen | offen | — |

---

## 3. Verstoss-Branch × Gate Matrix (Welle 4)

Erwartung: pro Branch bricht **genau ein** Gate; alle anderen
bleiben gruen.

| Branch | Erwartetes rotes Gate | Status |
| ------ | --------------------- | ------ |
| `spike0/contract/AC-HEXAGON-PURE` | `make arch-check-custom` | offen |
| `spike0/contract/AC-CORE-NO-ADAPTERS` | `make arch-check-imports` | offen |
| `spike0/contract/AC-CORE-NO-DRIVING` | `make arch-check-imports` | offen |
| `spike0/contract/AC-PORTS-NO-OUT` | `make arch-check-imports` | offen |
| `spike0/contract/AC-PORTS-NO-FW` | `make arch-check-imports` | offen |
| `spike0/contract/AC-ADAPTER-PURE` | `make arch-check-imports` | offen |
| `spike0/contract/AC-ADAPTER-LIGHTWEIGHT` | `make arch-check-custom` | offen |
| `spike0/contract/AC-NO-FW` | `make arch-check-imports` | offen |
| `spike0/contract/AC-NO-IO-MOD` | `make arch-check-imports` | offen |
| `spike0/contract/AC-NO-CYCLES` | `make arch-check-custom` | offen |
| `spike0/contract/AC-NO-TIME` (Aufruf-Site) | `make arch-check-custom` | offen |
| `spike0/contract/AC-NO-RAND` (Aufruf-Site) | `make arch-check-custom` | offen |
| `spike0/contract/AC-NO-JSON` | `make arch-check-custom` | offen |
| `spike0/contract/AC-DOMAIN-FROZEN` | `make arch-check-custom` | offen |
| `spike0/contract/AC-NO-GOD-UTILS` | `make arch-check-custom` | offen |
| `spike0/contract/AC-TYPED-ERRORS` | `make arch-check-custom` | offen |
| `spike0/lsp-variance` | `make typecheck` | offen |

---

## 4. Befunde / Beifaenge

### 4.1 Befunde Welle 1

- **`make lock-refresh` distroless uv-Image fehlerhaft:** das offizielle
  `ghcr.io/astral-sh/uv:VERSION`-Image ist distroless (keine Shell,
  kein Python). `uv lock` benoetigt aber einen Sub-Prozess-Spawner.
  Loesung: `lock-refresh` laeuft jetzt im projekteigenen `base`-Stage
  (`python:3.14-slim` + `uv` 0.5.31 gepinnt) als aktueller User
  (`--user $(id -u):$(id -g)` plus `UV_CACHE_DIR=/tmp/uv-cache`).
  Damit gibt es keine root-owned `uv.lock` mehr im Tree.
- **Dockerfile `source`-Stage brauchte `LICENSE` + `README.md`:**
  `pyproject.toml` referenziert beide; hatchling scheitert beim
  editable Install ohne sie. `COPY LICENSE README.md ./` in den
  source-Stage ergaenzt.
- **ruff 0.15 Drift gegenueber ADR 0002 §A-1:** Regeln `PLR0902`
  (too-many-instance-attributes) und `PLR0903` (too-few-public-methods)
  sind in ruff 0.15 nicht implementiert. `PLR0904`
  (too-many-public-methods) und `PLR0916` (too-many-boolean-expressions)
  stehen unter dem `preview`-Flag. `pyproject.toml` aktiviert
  `[tool.ruff.lint] preview = true` und entfernt die nicht
  implementierten Regeln. Restanteil bleibt Code-Review
  (Trigger 001). ADR-0002-Schliff folgt als separater
  Pre-Acceptance-Commit (`ADR 0006` §3 erlaubt).
- **import-linter `include_external_packages = true` notwendig:**
  sobald `forbidden_modules` externe Pakete enthaelt (`fastapi`,
  `socket`, etc.), muss diese Top-Level-Konfiguration gesetzt sein.
- **import-linter unterstuetzt keine Subpakete externer Pakete:**
  `urllib.request`, `http.client`, `logging.handlers` koennen nicht
  in `forbidden_modules` stehen — werden in Welle 3 ueber AST-
  Pruefung in `tools/arch_check.py` abgedeckt.

### 4.2 Befund Welle 2: Coverage-Gate-Schienen

Das `coverage-gate-critical`-Stage hat zwei aufeinanderfolgende
Schienen:

1. **pytest-cov `--cov-fail-under=90`** prueft die **kombinierte
   Coverage** (Lines + Branches gemeinsam).
2. **Python-XML-Check** liest `branch-rate` aus `coverage-critical.xml`
   und prueft die **reine Branch-Coverage**.

**Verifiziert:**

- pytest-cov-Schiene: Helper-Funktion mit 16 uncovered statements
  eingebaut, Coverage fiel auf 79.73 % (kombiniert), Stage rot
  mit `FAIL Required test coverage of 90% not reached`. Nach
  Revert wieder 100 %.
- XML-Schiene **in Isolation**: synthetische `coverage-critical.xml`
  mit `branch-rate="0.5"` in einen Container gefuettert; Python-
  Check meldet `50.00% < 90.00%`, exit 1. Sanity mit
  `branch-rate="0.95"`: exit 0.

**Erkenntnis:** Die XML-Schiene laesst sich im normalen Python-
Code-Pfad **nicht isoliert** ausloesen. coverage.py mit `--cov-branch`
decomposiert one-line `if cond: body` nicht in separate Branch-Arcs
(empirisch in drei Helper-Varianten geprueft: ternaere Expressions,
one-line ifs, for-loop). Statement-Level-Branches (`if`/`else` ueber
mehrere Zeilen) fuehren immer dazu, dass Line- und Branch-Coverage
zusammen fallen — uncovered Branch impliziert uncovered Line.
Damit feuert pytest-cov's kombinierter Check immer zuerst.

**Konsequenz fuer die Spike-0-Bewertung:** die XML-Branch-Schiene
ist **defense-in-depth** und nicht Hauptgate. Sie aktiviert sich nur
bei manuell konstruierten Edge-Cases (z. B. wenn jemand
`--cov-fail-under` aus der pytest-cov-Konfiguration herausnimmt
oder die Schwelle absenkt). Das ist akzeptabel; der Stage bleibt
defensiv konfiguriert. Eine Vereinfachung (Entfernen des
XML-Checks) waere moeglich, aber unnoetig — der Mehraufwand ist
~10 Zeilen Python.

### 4.3 Befund Welle 2: Coverage-Gate Build-Arg-Parametrisierung

Der `coverage-gate-critical`-Stage akzeptiert jetzt
`ARG CRITICAL_COV_TARGETS` (Default: kritische Domain laut
`GG-COV-003` — Simulation, Battery, Scenario, Replay). Wellen, die
nur einen Teilbereich implementieren, ueberschreiben per
`--build-arg`. Beispiel Welle 2:

```bash
make coverage-gate-critical CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization
```

Dadurch ist `make gates` ab Welle 2 in voller Tiefe ausfuehrbar,
sobald der Hauptprojekt-Code die volle kritische Domain abdeckt.

---

## 5. Drift-Liste fuer ADR-Pre-Acceptance-Schliff

Wird vor Welle 5 (Acceptance-Hebung) eingearbeitet:

- **ADR 0002 §A-1 `ruff`-Regel-Liste:** `PLR0902`/`PLR0903` entfernen
  (in ruff 0.15 nicht implementiert), `preview = true`-Hinweis fuer
  `PLR0904`/`PLR0916` aufnehmen plus Caveat zur impliziten Aktivierung
  weiterer Preview-Regeln in Gruppen-Praefixen (`B`, `S`, `N`, `TRY`,
  `RUF`), Restanteil als Code-Review-pflichtig markieren.
- **ADR 0005 `mypy`-Versions-Floor:** `>=1.13` → `>=2.0` (mypy 2.x
  ist die aktuelle Major; im Lock 2.1.0). `pyproject.toml` ist bereits
  auf `mypy>=2.0,<3.0` gepinnt; ADR 0005 muss vor Acceptance synchron
  ziehen.
- **ADR 0002 §A-1 `AC-NO-IO-MOD`:** Hinweis ergaenzen, dass
  `urllib.request`/`http.client`/`logging.handlers` ueber
  `tools/arch_check.py` (`_check_no_io_mod_nested`) abgedeckt werden,
  nicht ueber `import-linter` (Subpakete externer Pakete sind dort
  nicht erlaubt).
- **ADR 0002 §A-1 `AC-DOMAIN-FROZEN`:** klarstellen, dass `slots=True`
  zusaetzlich zu `frozen=True` gefordert ist (jetzt im
  `_has_frozen_dataclass_decorator` enforced) und dass `FrozenModel`
  als literaler Klassenname erkannt wird (sowohl `ast.Name` als auch
  `ast.Attribute`).

## 6. Reviews

### 6.1 Code-Review nach Welle 3 — abgearbeitet 2026-05-15

Unabhaengiger Review durch `code-reviewer`-Subagent identifizierte
4 Blocker, 8 Important, 10 Cosmetic. In vier Commits behoben
(`9d7a3fb`, `d0c8559`, `facd9aa`, plus Config-Sanity):

| Commit | Befunde | Datei |
| ------ | ------- | ----- |
| `9d7a3fb` | B-1 (adapter-path fnmatch), B-2 (NO-CYCLES dedup), B-3 (TYPED-ERRORS Tuple-Form), I-1 (NO-IO-MOD-NESTED), I-8 (raise-Attribute) | `tools/arch_check.py` |
| `d0c8559` | I-2..I-8 AST-Aliasing-Trio (`import X as Y`, `from X import Y`), I-5 DOMAIN-FROZEN (top-level-only, slots=True, Attribute-base), I-6 NO-GOD-UTILS Doku, I-7 ADAPTER-LIGHTWEIGHT cyclomatic (IfExp/Match/Comprehension) | `tools/arch_check.py` |
| `facd9aa` | I-13 SurrogateNotAllowedError, I-14 CircularReferenceError, C-5 Signed-Zero-Normalisierung, 11 neue Tests | `canonical.py`, `test_canonical.py` |
| Config-Sanity | I-9 mypy-Pin `>=2.0,<3.0`, I-10 preview-Caveat dokumentiert, I-11 FrozenModel-Note, I-12 Pfad-Normalisierung, I-15 U+2028/U+2029 RFC-Note, I-17 coverage-gate-critical Pfad-Existenz-Guard | `pyproject.toml`, `Dockerfile`, `arch_check.py`, `canonical.py` |

**Gate-Status nach Fixes:** alle Welle-1/2/3-Gates bleiben gruen
(`make lint`/`format-check`/`typecheck`/`arch-check`/`test-unit`/
`coverage-gate-critical` mit `CRITICAL_COV_TARGETS=...serialization`).
Pfad-Existenz-Guard in `coverage-gate-critical` verifiziert durch
negativen Test: ohne Override schlaegt der Stage mit
`target dir missing: src/grid_gym/hexagon/core/devices/battery`
fail-fast ab.

Restbestand cosmetic (nicht blockierend, kann jederzeit nachgezogen
werden): C-1, C-2, C-3, C-4, C-7, C-8, C-9, C-10 — siehe Original-
Review-Findings.
