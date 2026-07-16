# Spike-0 Ergebnisse (Detail-Records)

**Status:** Done — Spike-0 abgeschlossen 2026-05-15
**Datum:** 2026-05-15
**Bezug:** [`spike-0.md`](../done-archive/spike-0.md) §0 (Closure-Notiz),
[`ADR 0002`](../../adr/0002-language-and-build-stack.md) (`Accepted`),
[`ADR 0005`](../../adr/0005-type-check-gate.md) (`Accepted`)

---

## 1. Zweck

Detail-Records zur Acceptance-Entscheidung von [`ADR 0002`](../../adr/0002-language-and-build-stack.md) und
[`ADR 0005`](../../adr/0005-type-check-gate.md). Dokumentiert Welle-fuer-Welle den Gate-Status, die
18 Verstoss-Verifikationen aus Welle 4 (16 A-1-Contracts plus
[`AC-NO-IO-MOD`](../../adr/0002-language-and-build-stack.md#adr-0002--sprach--und-build-stack)-nested plus LSP-Variance via mypy — Branch × Gate
Matrix in §3) und die Befunde aus drei Reviews (zwei Pre-Acceptance,
ein Post-Acceptance — §4 und §6). Pre-Acceptance-Schaerfungen sind
per [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §3 erlaubt; alle Drift-Items wurden vor Acceptance
eingearbeitet (§5).

---

## 2. Welle-Status

| Welle | Liefergegenstand | Gates | Commit |
| ----- | ---------------- | ----- | ------ |
| 1 — Toolchain + Skelett | `pyproject.toml`, `uv.lock`, `.python-version`, `src/grid_gym/{hexagon/{core,ports},adapters}/`, `tools/arch_check.py`-Skelett, Smoke-Test | `make lint`/`format-check`/`typecheck`/`arch-check`/`test-unit`/`dep-audit`: **gruen** | `cb2246a` |
| 2 — A-2 Custom-Emitter | `hexagon/core/serialization/canonical.py` (79 stmts, 38 Branches), `test_canonical.py` (42 Tests inkl. 6 Property-Tests), `coverage-gate-critical` mit Build-Arg-Scope | `make test-unit` (44 passed), `make coverage-gate-critical CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization` (**100 % Line + Branch**) | `5298a0c` |
| 3 — `tools/arch_check.py` Contracts | Neun Contracts implementiert (HEXAGON-PURE, NO-JSON, NO-TIME, NO-RAND, DOMAIN-FROZEN, NO-GOD-UTILS, TYPED-ERRORS, NO-CYCLES, ADAPTER-LIGHTWEIGHT) | `make arch-check` mit allen Contracts gruen | `aed2189` |
| 3.1 — Review-Fixes (4 Commits) | Blocker B-1/B-2/B-3 + I-1 (Pfad-Matcher, SCC-Dedup, Tuple-Exception, NO-IO-MOD-nested); AST-Aliasing-Trio (I-2..I-8); canonical.py (Surrogate, Cycle, -0); Config-Sanity (mypy-Pin, ruff-preview-Caveat, Pfad-Normalisierung, Pfad-Existenz-Guard) | Alle Gates bleiben gruen; 55 Unit-Tests | `9d7a3fb`, `d0c8559`, `facd9aa`, `0e11ca8` |
| 4 — Verstoss-Verifikation | 18 verify-and-revert-Zyklen auf main; pro Contract exakt eine Violation, exakt das erwartete Gate rot | siehe §3 Matrix | (kein Commit — temp Files, sauber zurueckgerollt) |
| 5 — Acceptance-Hebung | [`ADR 0002`](../../adr/0002-language-and-build-stack.md) + [`ADR 0005`](../../adr/0005-type-check-gate.md) `Provisional → Accepted`; `architecture.md §19` [`GG-AR-OPEN-001`](../../adr/README.md#gg-ar-open-001) geschlossen; `roadmap.md §4` Vorbedingungen 1+3 abgehakt; Headers (Dockerfile/Makefile/pyproject.toml) auf verbindlichen Stack; Closure-Notiz `done/spike-0.md §0`; `make gates CRITICAL_COV_TARGETS=...serialization` gruen. | `make gates` gruen mit Spike-0-Override | `5763445`, `3645473`, `522ec17`, `5281d15` |
| 5.1 — Post-Acceptance-Konsistenz | Cross-Ref-Drift (`spec/architecture.md §1/§4.2/§7`, `Makefile`-Count, `README`-Projektstruktur, `roadmap`-Stand, `Dockerfile`-openapi-Kommentar) und Closure-Drift (`spike-0-results.md` Header/§1/§2, `spike-0.md §7`); M1-Vorbereitung (`roadmap §3`-Vorbelegung, `open/README` Trigger-Priorisierung, `Dockerfile` Path-Guard-Hinweis, `tests/arch/` Vollstaendigkeits-Test); Trigger 001 von `open/` → `next/` aktiviert | reine Doku-Edits, Gates bleiben gruen | folgt aus drittem Review |

---

## 3. Verstoss × Gate Matrix (Welle 4 — abgeschlossen 2026-05-15)

Pro Contract eine Violation auf `main` eingebaut, Gate verifiziert,
Violation sauber zurueckgerollt. `make arch-check` ist die
Aggregator-Stage `lint-imports` + `arch_check.py`; bei mehrfachem
Match (z. B. `import fastapi` triggert sowohl [`AC-NO-FW`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) via
`import-linter` als auch implizit [`AC-HEXAGON-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) via
`arch_check.py`) zeigt das `&&`-Shortcut des Aggregator-Stages
nur den erstausloesenden — beide sind in der Realitaet scharf.

| Contract | Erwartetes Gate | Erfolg | Test-Pattern | Violation-Detail |
| -------- | --------------- | ------ | ------------ | ---------------- |
| [`AC-HEXAGON-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `arch_check.py` | ✓ | `import requests` in `hexagon/core/__welle4__.py` | [`AC-HEXAGON-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)  __welle4__.py:3  import requests |
| [`AC-CORE-NO-ADAPTERS`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `import-linter` | ✓ | `from grid_gym.adapters import driving` in `hexagon/core/` | [`AC-CORE-NO-ADAPTERS`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) BROKEN |
| [`AC-CORE-NO-DRIVING`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `import-linter` | ✓ | `from grid_gym.hexagon.ports import driving` in `hexagon/core/` | [`AC-CORE-NO-DRIVING`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) BROKEN |
| [`AC-PORTS-NO-OUT`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `import-linter` | ✓ | `from grid_gym.hexagon.core import simulation` in `hexagon/ports/` | [`AC-PORTS-NO-OUT`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) BROKEN |
| [`AC-PORTS-NO-FW`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `import-linter` | ✓ | `import fastapi` in `hexagon/ports/` | [`AC-PORTS-NO-FW`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) BROKEN |
| [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `import-linter` | ✓ | `from grid_gym.hexagon.core import simulation` in `adapters/driving/` | [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) BROKEN |
| [`AC-ADAPTER-LIGHTWEIGHT`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `arch_check.py` | ✓ | Funktion mit zyklomatischer Komplexitaet 10 in `adapters/driving/` | `function 'overcomplicated' complexity 10 > 8` |
| [`AC-NO-FW`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `import-linter` | ✓ | `import fastapi` in `hexagon/core/` | [`AC-NO-FW`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) BROKEN |
| [`AC-NO-IO-MOD`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) (top-level) | `import-linter` | ✓ | `import socket` in `hexagon/core/` | [`AC-NO-IO-MOD`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) BROKEN |
| [`AC-NO-IO-MOD`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) (nested) | `arch_check.py` | ✓ | `import urllib.request` in `hexagon/core/` | [`AC-NO-IO-MOD`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)  __welle4__.py:3  import urllib.request |
| [`AC-NO-CYCLES`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `arch_check.py` | ✓ | Zwei Module zyklisch in `hexagon/core/` | [`AC-NO-CYCLES`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)  __welle4_a__ <-> __welle4_b__  cycle: a -> b -> a (kanonisch dedupliziert auf 1 Violation) |
| [`AC-NO-TIME`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) (Aufruf-Site) | `arch_check.py` | ✓ | `time.monotonic()` in `hexagon/core/`; in Welle 5 zusaetzlich `asyncio.get_event_loop().time()` (Commit `fb90154`) | [`AC-NO-TIME`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)  __welle4__.py:7  time.monotonic() (via alias or attribute) — use ClockPort |
| [`AC-NO-RAND`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) (Aufruf-Site) | `arch_check.py` | ✓ | `random.random()` via function-level import in `hexagon/core/` | [`AC-NO-RAND`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)  __welle4__.py:8  random.random() — use RandomPort |
| [`AC-NO-JSON`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `arch_check.py` | ✓ | `json.dumps(...)` in `hexagon/core/` | [`AC-NO-JSON`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)  __welle4__.py:7  json.dumps() — use canonical_json() |
| [`AC-DOMAIN-FROZEN`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `arch_check.py` | ✓ | Nicht-frozen Klasse `MutableTelemetry` in `hexagon/core/domain/` | [`AC-DOMAIN-FROZEN`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)  __welle4__.py:4  class 'MutableTelemetry' is not frozen |
| [`AC-NO-GOD-UTILS`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `arch_check.py` | ✓ | Modul `string_utils.py` in `hexagon/core/` | [`AC-NO-GOD-UTILS`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)  string_utils.py  forbidden module name: string_utils.py |
| [`AC-TYPED-ERRORS`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) | `arch_check.py` | ✓ | `except (ValueError, Exception):` Tuple-Form in `hexagon/core/` | [`AC-TYPED-ERRORS`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)  __welle4__.py:7  except Exception outside boundary-translation (validates Welle-3-Fix B-3) |
| LSP variance | `mypy --strict` | ✓ | Subklasse weitet Return-Typ `int` → `object` | `[override]` + `[explicit-override]` (mypy 2 errors in 1 file) |

**Ergebnis: 18 von 18 Contracts haben Zaehne.** Pro Violation exakt
das erwartete Gate rot, alle anderen gruen. [`AC-NO-IO-MOD`](../../adr/0002-language-and-build-stack.md#adr-0002--sprach--und-build-stack) ist zweimal
verifiziert (Top-Level via import-linter und nested via
arch_check.py).

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
- **ruff 0.15 Drift gegenueber [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §A-1:** Regeln `PLR0902`
  (too-many-instance-attributes) und `PLR0903` (too-few-public-methods)
  sind in ruff 0.15 nicht implementiert. `PLR0904`
  (too-many-public-methods) und `PLR0916` (too-many-boolean-expressions)
  stehen unter dem `preview`-Flag. `pyproject.toml` aktiviert
  `[tool.ruff.lint] preview = true` und entfernt die nicht
  implementierten Regeln. Restanteil bleibt Code-Review
  (Trigger 001). [`ADR-0002`](../../adr/0002-language-and-build-stack.md)-Schliff folgt als separater
  Pre-Acceptance-Commit ([`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §3 erlaubt).
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
[`GG-COV-003`](../../../../spec/spezifikation.md#gg-cov-003) — Simulation, Battery, Scenario, Replay). Wellen, die
nur einen Teilbereich implementieren, ueberschreiben per
`--build-arg`. Beispiel Welle 2:

```bash
make coverage-gate-critical CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization
```

Dadurch ist `make gates` ab Welle 2 in voller Tiefe ausfuehrbar,
sobald der Hauptprojekt-Code die volle kritische Domain abdeckt.

---

## 5. Drift-Liste fuer ADR-Pre-Acceptance-Schliff (eingearbeitet)

Alle zehn Items wurden vor Welle 5 in [`ADR 0002`](../../adr/0002-language-and-build-stack.md) / [`ADR 0005`](../../adr/0005-type-check-gate.md)
eingearbeitet (Commit `201daee`). [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §3 erlaubt
Pre-Acceptance-Schaerfungen mit Header-Eintrag
„Letzte inhaltliche Aenderung".

- **D-1 ✓** [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §A-1 `ruff`-Regel-Liste: `PLR0902`/`PLR0903`
  entfernen, `preview = true`-Hinweis mit Caveat zur impliziten
  Aktivierung weiterer Preview-Regeln in Gruppen-Praefixen
  (`B`, `S`, `N`, `TRY`, `RUF`), Restanteil als Code-Review-pflichtig.
- **D-2 ✓** [`ADR 0005`](../../adr/0005-type-check-gate.md) mypy-Floor: `>=1.13` → `>=2.0,<3.0`.
  pyproject.toml bereits gepinnt; [`ADR 0005`](../../adr/0005-type-check-gate.md) §5.1-Snippet und
  Header-Eintrag synchronisiert.
- **D-3 ✓** [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §A-1 [`AC-NO-IO-MOD`](../../adr/0002-language-and-build-stack.md#adr-0002--sprach--und-build-stack): aufgeteilt nach import-linter
  (Top-Level `socket`/`pathlib`) und `tools/arch_check.py`
  (`_check_no_io_mod_nested` fuer Subpakete `urllib.request`/
  `http.client`/`logging.handlers`).
- **D-4 ✓** [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §A-1 [`AC-DOMAIN-FROZEN`](../../adr/0002-language-and-build-stack.md#adr-0002--sprach--und-build-stack): `slots=True` Pflicht,
  `FrozenModel` als `ast.Name` ODER `ast.Attribute`, nur
  Top-Level-Klassen via `tree.body`.
- **D-5 ✓** [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §A-1: [`AC-HEXAGON-PURE`](../../adr/0002-language-and-build-stack.md#adr-0002--sprach--und-build-stack) als 16. Contract
  aufgenommen (war im Code seit Welle 3, in der Tabelle fehlend).
  „fuenfzehn" → „sechzehn" an sechs Stellen synchronisiert.
  Tabu-Abdeckungs-Matrix: [`GG-AR-TABU-002`](../../../../spec/architecture.md#architektur-tabus-build-architekturtest) ergaenzt.
- **D-6 ✓** [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §A-1 Operative Anforderung:
  `[tool.importlinter] include_external_packages = true` als
  Pflicht-Konfigurations-Schluessel dokumentiert.
- **D-7 ✓** [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §A-1 [`AC-NO-TIME`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) erfasst weiterhin
  `asyncio.get_event_loop().time` (war ADR-Pflicht, Implementation
  fehlte). Implementation in `tools/arch_check.py` ergaenzt
  (`_is_asyncio_event_loop_time_call` Variante A: Attribute-Call,
  Variante B: `from asyncio import get_event_loop`).
- **D-8 ✓** [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §6.1 Toolchain-Pinning: CI-Matrix-Behauptung
  abgeschwaecht. Heute `make ... PYTHON_VERSION=3.13` Override
  testbar; vollwertige GitHub-Actions-Matrix kommt als Folgewelle
  nach M1.
- **D-9 ✓** [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §A-2 Custom-Emitter-Snippet aktualisiert:
  sechs typisierte Fehlerklassen, `seen`-Zyklusabwehr,
  Signed-Zero-Normalisierung, Surrogate-Check, RFC-8259-
  U+2028/U+2029/U+007F-Note. Alternativ-Encoder-Vertrag um
  Cycle-Detection / Surrogate-Rejection / Signed-Zero verschaerft.
- **D-10 ✓** [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §A-1 [`AC-TYPED-ERRORS`](../../adr/0002-language-and-build-stack.md#adr-0002--sprach--und-build-stack): Tuple-Form
  (`except (Exception, ...):`, rekursiv) und Attribute-Form
  (`raise builtins.Exception(...)` / `except mod.Exception:`)
  ADR-konform dokumentiert.

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

### 6.2 Pre-Acceptance Code-Review — abgearbeitet 2026-05-15

Zweiter unabhaengiger Review durch `code-reviewer`-Subagent vor
Welle 5 (Acceptance-Hebung). Befunde: 3 Blocker, 8 Important,
mehrere Welle-6+/Cosmetic. Verdict war „Acceptance-Status: Nein —
nicht so wie heute spezifiziert" wegen drei strukturellen Problemen.

In zwei Commits abgearbeitet:

| Commit | Befunde | Datei |
| ------ | ------- | ----- |
| `fb90154` | B-A: `asyncio.get_event_loop().time` (Variante A: Attribute-Call; Variante B: `from asyncio import get_event_loop`) | `tools/arch_check.py` |
| `201daee` | B-B ([`AC-HEXAGON-PURE`](../../adr/0002-language-and-build-stack.md#adr-0002--sprach--und-build-stack) als 16. Contract im ADR), D-1..D-10 (alle Drift-Items in §A-1, §A-2, §6.1 von [`ADR 0002`](../../adr/0002-language-and-build-stack.md) sowie §5.1 von [`ADR 0005`](../../adr/0005-type-check-gate.md)) | `docs/plan/adr/0002-language-and-build-stack.md`, `docs/plan/adr/0005-type-check-gate.md` |
| (folgt) | B-C: Welle-5-Schritt-7 `make fullbuild` → `make gates` reduziert, Spike-0-Closure-Note-Struktur konkretisiert, Welle-5-Schritt-4/6 ergaenzt | `docs/plan/planning/done-archive/spike-0.md`, `spike-0-results.md` |

**Gate-Status nach B-A + D-1..D-10:** alle Welle-1..4-Gates bleiben
gruen. `make arch-check` faengt jetzt zusaetzlich
`asyncio.get_event_loop().time()` als [`AC-NO-TIME`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Verstoss.

**Important-Items I-A..I-K aus dem Review** (Docstring-Polituren in
`arch_check.py` und `canonical.py`): folgen als separater Commit
(nicht Acceptance-blockierend, aber sollten vor Welle 5 fertig sein).

Welle 4 muss nach den Implementation-Aenderungen (B-A asyncio)
einmalig nachgezogen werden — der Verstoss-Test fuer
`asyncio.get_event_loop().time()` wurde im Pre-Acceptance-Schliff-
Commit `fb90154` als Verifikations-Lauf bereits durchgefuehrt
(bewusst eingefuegter Verstoss → Detection bestaetigt → revert).
Matrix in §3 unter [`AC-NO-TIME`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) deshalb mit Note „inkl.
`asyncio.get_event_loop().time` (Welle 5)".
