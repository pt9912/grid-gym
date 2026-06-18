# Welle 3 — M6 CI/CD-Vollausbau (`GG-CICD-002/003/005/006` + Python-Matrix)

**Status:** Done 2026-06-05 — Liefer-Stack: C0 `08a8034`
(Slice-Doc-Anlage) + C2 `ce13253` (Code-Merge: 4 NEU
Workflows + Trigger-031-Aufloesung + pip-PYSEC-2026-196-
Drift-Fix; C1 entfaellt analog M5-Welle-2) + C3 `c8ecbe4`
(Status/DoD-Sync + Trigger-031-`open/ → done/`-Move +
Top-Level-Doku-Sync) + C3-Review-Folge (dieser Commit; 3
MED Findings adressiert: F1 Self-Close strukturell ueber
C4a/C4b; F2 Aktive-Welle-Drift in M6-perf-security-cicd.md
+ in-progress/README.md; F3 Matrix-Scope-Konsistenz in
§1.2 + §4 — test-integration ist NICHT Matrix). Ausstehend:
C4a Self-Close-Move + C4b Cross-Doc-Refs-Sync nach Move
(Pattern analog M6-Welle-2-C4a `c51d905`/C4b `b41b7fc`). Welle 3 ist die
**dritte Code-Welle in M6** und liefert die GitHub-Actions-
CI-Pflicht-Gates fuer alle lokal-Pflicht-Targets, plus
Python-3.13/3.14-Matrix gegen die existierenden 4 Slice-
025-Gates, plus die Aufloesung von Trigger 031 (`make
fullbuild`-CI-Gate aus M6-Welle-1-D-1-Vertagung).

**Pre-C0 abgeschlossen (M6-Welle-2-Closure-Folge):**

- C4a `c51d905` — `git mv M6-welle-2.md → done/` (Self-
  Close-Move, rename-only).
- C4b `b41b7fc` — Cross-Doc-Refs-Sync nach Move.
- Post-Closure-Korrekturen `febbd22..3ccf01d` — 4 Folge-
  Commits am `release.yml`-Stand (Welle-2-Substanz-
  Schaerfungen, nicht Welle-3-Substanz; siehe
  [`../done/M6-welle-2.md §10.6`](M6-welle-2.md)).

Kein Pre-C0c-Smoke-Probe-Run noetig — die 4 NEU Workflow-
Dateien folgen dem `release.yml`-Pattern aus Welle 2, das
durch actionlint + shellcheck + Trigger-032-Sensor-Pflicht
bereits substanziell verifiziert ist.

**Spec-Reife:** Inhaltlich final fuer Welle 3. Welle-3-
Decision-Liste (§3) schliesst M6-D-6 (Python-3.13/3.14-
Matrix) und Trigger-031-Aufloesungsform; plus NEU Welle-3-
spezifische Decisions D-1..D-5.

---

## 1. Context

[`M6-perf-security-cicd.md §3.2 Welle 3`](M6-perf-security-cicd.md)
hat Welle 3 als „CI/CD-Vollausbau" vorbelegt mit
4 NEU CI-Jobs (`test-unit` + `coverage-gate` + `dep-audit`
+ `image-audit`) + NEU Python-3.13/3.14-Matrix +
`GG-CICD-007`-Release-Workflow-Pre-Link (in Welle 2
bereits erledigt). Trigger 031 ([`../done/031-ci-make-fullbuild-gate.md`](031-ci-make-fullbuild-gate.md))
integriert sich als 5. Job (`make fullbuild`-CI-Pflicht-
Gate).

### 1.1 Existierende Substanz (vor Welle 3)

- **`.github/workflows/ci.yml`** (Slice 025): vier CI-
  Pflicht-Gates `lint`/`format-check`/`typecheck`/`arch-
  check`. Parallel-Pattern via `docker/build-push-action@v6`
  mit `cache-from/to: type=gha,scope=<target>`. Default-
  Python = `3.14` (im Dockerfile `ARG PYTHON_VERSION=3.14`).
- **`.github/workflows/release.yml`** (Welle 2; substantiell
  geschaerft in Welle-2-Post-Closure-Folgen 1-4): Tag-Push
  + workflow_dispatch + 3 Jobs (build-and-publish-image /
  produce-assets / create-release).
- **`Makefile`** Pflicht-Targets:
  - `make gates` = `lint`+`format-check`+`typecheck`+`arch-
    check`+`test-unit`+`coverage-gate`+`coverage-gate-
    critical`+`dep-audit`+`noqa-gate`+`spdx-check` (10 A-1-
    Gates).
  - `make ci` = `gates` + `test-integration` + `openapi-
    validate` + `image-audit`.
  - `make fullbuild` = `ci` + `build` + `runtime` (Compose-
    Smoke).
- **`Dockerfile`** Stages: alle 10 A-1-Gate-Targets + 4
  CI-Erweiterungs-Targets als separate Multi-Stage-Targets;
  Cache-isoliert pro Stage.

### 1.2 Welle-3-Lieferziel

Vier NEU GitHub-Actions-Workflow-Dateien plus Trigger-
031-Aufloesung:

1. **NEU `.github/workflows/tests.yml`** — `make test-unit`
   + `make test-integration` als CI-Pflicht-Jobs; Matrix-
   Scope nicht symmetrisch: **`test-unit` mit Python-
   3.13/3.14-Matrix** (`strategy.matrix.python-version`),
   **`test-integration` mit Default-Python (3.14)**.
   Begruendung fuer Asymmetrie: `test-integration` ist
   Compose-basiert (testcontainers + `tests/integration/
   compose.yml`); Compose-File-Edit fuer Matrix-Build-Args
   waere weiterer Welle-X-Refactoring-Bedarf (siehe Welle-
   3-D-2 in §3 fuer File-Ebenen-Decision). Deckt
   `GG-CICD-002`-MUSS (Tests automatisch ausgefuehrt;
   Unit + Integration als getrennte Jobs).
2. **NEU `.github/workflows/coverage.yml`** — `make
   coverage-gate` + `make coverage-gate-critical` als CI-
   Pflicht-Jobs (Default-Python; Matrix nicht noetig —
   Coverage ist Code-Stand-bezogen, nicht Python-Version-
   spezifisch); deckt `GG-CICD-003`-MUSS-Anteil (Quality
   Gates maschinenlesbar; Coverage-Schwelle als
   maschinenlesbare Pipe-Output).
3. **NEU `.github/workflows/dep-audit.yml`** — `make
   dep-audit` (`pip-audit --strict`) als CI-Pflicht-Job
   (Default-Python; `dep-audit` ist
   `uv.lock`-stand-bezogen, nicht Python-Version-
   spezifisch); deckt `GG-CICD-005`+`GG-CICD-006`-MUSS
   (Security-Scanning + Dependency-Scanning).
4. **NEU `.github/workflows/fullbuild.yml`** — `make
   fullbuild` als CI-Pflicht-Job (Default-Python; Compose-
   Smoke ist Service-Container-bezogen); deckt
   `GG-CICD-003`-MUSS-Anteil (`openapi-validate` +
   `image-audit`) plus Compose-Smoke (`runtime`-Pollung).
   **Loest Trigger 031 auf** — Welle-1-D-1-Vertagung als
   Welle-3-C2-Closure.

Plus opportunistisch: KEINE URL-Versionierung `/api/v1`-
Substanz (M6-D-3-Vorbelegung war Welle-3-„opportunistisch"
ODER M6-Welle-X; Welle 3 bleibt scope-eng auf CI-Substanz).

### 1.3 Welle-3-Anti-Scope

- **Kein SBOM-Workflow-Edit** — `release.yml` (Welle-2-
  Substanz) bleibt unangetastet. `make sbom` ist Welle-2-
  Pflicht und steht in `release.yml`; Welle 3 wiederholt
  das nicht.
- **Keine Performance-Bench** — `GG-RT-005`-Bench ist
  Welle-4-Scope.
- **Kein Security-Audit** — `GG-SAFE-001..008` ist Welle-
  5-Scope (Eingabevalidierung etc.).
- **Kein Deploy-Hardening-Vollausbau** — `GG-DEPLOY-*`
  ist Welle-6-Scope; Welle 3 macht `make fullbuild` in CI
  (inkl. image-audit + compose smoke), aber kein zusaetz-
  liches Hardening-Substanz.
- **Kein IEC-Smoke-Pfad-B** — Trigger 009 + Multi-Python-
  Test-Stage im Dockerfile ist Welle-6-Scope. Python-
  Matrix in Welle 3 ist GitHub-Actions-Matrix-Wrapping,
  nicht Dockerfile-Multi-Python-Stage.
- **Keine URL-Versionierung `/api/v1`** — `Deferred`-Item
  aus `carveouts.md §2.1`; bleibt Welle-X-Material.
- **Kein `.trivyignore`** — ADR 0043 §2.2 verankert
  `open/`-Trigger als einzige Defer-Form.
- **Kein `actionlint`-Pre-Commit-Hook** — Dev-Tooling-
  Substanz (Trigger-007-Pattern); bleibt M7+ oder
  spaetere Welle.

---

## 2. Scope

Welle 3 liefert **vier Items** ueber 4 Commits (C0..C3),
plus Self-Close-Folge C4a/C4b. **Single-Welle-Vorbelegung**
(siehe §3 Welle-3-D-5 Sub-Slicing-Beobachtung).

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses
   Dokument.
2. **C1 entfaellt** — keine ADR-Substanz erwartet (Pattern
   analog M5-Welle-2 `5234617`). Welle-3-Decisions (D-1..
   D-5) sind im C0-Slice-Doc-§3-Body fixiert; ADR 0002
   §6.1-Matrix-Substanz wird produktiv in C2 umgesetzt,
   ohne ADR-Schaerfung. Falls in C2 substanzielle Multi-
   File-Workflow-Architektur-Drift auftaucht, kann C1
   nachtraeglich entstehen.
3. **Code-Merge** (C2) — NEU 4 Workflow-Dateien
   (`tests.yml`/`coverage.yml`/`dep-audit.yml`/`fullbuild.
   yml`); lokal-Verifikation via actionlint + shellcheck
   + `make gates`/`make ci`/`make fullbuild`; Trigger 031
   `git mv open/ → done/` Move mit Closure-Notiz analog
   Trigger 010 + Trigger 008.
4. **Status/DoD-Sync** (C3) — `M6-welle-3.md` auf `Done`,
   `M6-perf-security-cicd.md §3.1` Welle-3-Zeile auf
   `Done`; `carveouts.md §2.X` Trigger-031-Eintrag auf
   `Aufgeloest in M6-Welle-3-C2` (Welle-1-Vertagung hatte
   den nicht eingepflegt — hier nachgepflegt); Top-Level-
   Doku-Sync (`README.md`/`README.de.md` NEU CI-Workflow-
   Hinweis; `roadmap.md §3 M6` aktive Welle auf M6-Welle-4
   + Welle-3-Abschluss-Notiz).

Self-Close-Folge C4a/C4b laufen nach C3 als M6-Welle-4-
Pre-C0a/Pre-C0b.

---

## 3. Architektur-Entscheidungen (Welle-3-Decision-Liste)

Welle 3 schliesst diese Decisions aus
[`../done/M6-welle-0.md §3`](M6-welle-0.md):

### M6-D-6 — Python-3.13/3.14-Matrix

**Frage:** Wird GitHub-Actions auf eine Test-Matrix mit
beiden Python-Versionen erweitert (Spike-0-Closure-D-8 +
ADR 0002 §6.1)?

Welle-0-Vorbelegung: **Ja**, in M6-Welle-3.

**Welle-3-Final:** **Ja, Python-3.13/3.14-Matrix produktiv
in `tests.yml`** (Unit + Integration). Begruendung in
Welle-3-D-2 unten.

### Welle-3-D-1 — Workflow-Datei-Granularitaet

**Frage:** Alle CI-Jobs in `ci.yml`-Erweiterung ODER
separate Workflow-Dateien?

Optionen:

- **A — `ci.yml`-Monolith**: alle Jobs in bestehender
  `ci.yml` (8+ Jobs in einer Datei).
- **B — Separate Files** pro Job-Familie: `tests.yml` +
  `coverage.yml` + `dep-audit.yml` + `fullbuild.yml`.

**Welle-3-Final: Option B (Separate Files).** Begruendung:

- Lifecycle-Klarheit: Trigger 031 (`fullbuild`) hat
  eigenen Trigger-Filter-Bedarf (z. B. `paths:
  Dockerfile`); kollidiert mit `ci.yml`-Generic-Trigger.
- Skalierung: Welle 4+ (Performance-Bench) wird vermutlich
  ein eigener `perf.yml`-Workflow; konsistentes Pattern.
- GitHub-Actions-Standard im OSS-Ecosystem (eines pro
  Concern). `ci.yml` bleibt fuer die 4 Slice-025-Pflicht-
  Gates (lint/format-check/typecheck/arch-check); NEU
  Workflows fuer die restlichen 4+ Gates.

### Welle-3-D-2 — Python-Matrix-Scope (welche Workflows?)

**Frage:** Bekommen alle 4 NEU Workflows die Python-3.13/
3.14-Matrix?

**Welle-3-Final: NUR `tests.yml` mit Matrix.** Begruendung:

- **`tests.yml`** — Tests sind direkt Python-Version-
  abhaengig (Unicode/Typing/Runtime-Library-Behavior pro
  Python-Version unterscheidbar). Matrix produktiv
  noetig zur Spike-0-Closure-D-8-Erfuellung.
- **`coverage.yml`** — Coverage misst Code-Stand-Pfade,
  nicht Python-Version-Verhalten. Eine Matrix wuerde
  dieselbe Coverage-Schwelle doppelt pruefen. Default-
  Python (3.14) reicht.
- **`dep-audit.yml`** — `pip-audit` prueft `uv.lock`-
  Eintraege gegen CVE-DB; Python-Version-agnostisch.
  Default-Python (3.14) reicht.
- **`fullbuild.yml`** — Compose-Smoke + image-audit sind
  Service-Container-/Image-bezogen; nicht Python-Version-
  spezifisch. Default-Python (3.14) reicht. Plus: `make
  fullbuild` ist teuer (~10min); Matrix wuerde Compute-
  Last verdoppeln ohne Substanz-Mehrwert.

ADR 0002 §6.1-Substanz produktiv erfuellt durch
`tests.yml`-Matrix-Coverage; weitere Matrix-Verbreitung
ist YAGNI.

### Welle-3-D-3 — `fullbuild.yml`-Trigger-Strategie

**Frage:** Welche Trigger fuer den teuersten Workflow
(`make fullbuild` ~10min)?

Optionen:

- **A — Push/PR auf alle Pfade** (wie `ci.yml`): jeder
  Doc-Commit triggert fullbuild. ~10min pro Push.
  Verschwendet Compute fuer doc-only-Aenderungen.
- **B — Push/PR mit `paths`-Filter**: nur bei Aenderungen
  an Dockerfile/Makefile/src/tests/pyproject/uv.lock/
  deploy/. Doc-Aenderungen umgehen.
- **C — Hybrid: Push/PR mit Path-Filter PLUS
  workflow_dispatch**: Standard-Pattern plus Manual-
  Trigger fuer Force-Runs.

**Welle-3-Final: Option C (Hybrid).** Begruendung:

- Doc-only-Aenderungen (Makdown-Updates) muessen nicht
  `fullbuild` triggern; das ist verschwendete Compute.
- Realistische Path-Liste: `Dockerfile` / `Makefile` /
  `src/**` / `tests/**` / `pyproject.toml` / `uv.lock` /
  `deploy/**` / `.github/workflows/fullbuild.yml` (self-
  reference) — deckt alle echten Build-Substanz-Pfade.
- `workflow_dispatch`-Fallback fuer Force-Runs (z. B. nach
  Base-Image-Drift, Trivy-DB-Update). Konsistent mit
  Welle-2-`release.yml`.

`tests.yml`/`coverage.yml`/`dep-audit.yml` bleiben bei
Push/PR ohne Path-Filter (Standard-Pattern wie `ci.yml`).

### Welle-3-D-4 — Trigger-031-Aufloesungs-Form

**Frage:** Wie wird Trigger 031 in der `fullbuild.yml`-
Substanz konkret aufgeloest?

**Welle-3-Final:** `fullbuild.yml` IST Trigger-031-
Aufloesung. C3 macht `git mv open/031-ci-make-fullbuild-
gate.md → done/031-ci-make-fullbuild-gate.md` mit
Closure-Notiz-Block (Pattern analog Trigger 010 in
M6-Welle-1-C3 + Trigger 008 in M6-Welle-2-C3). Plus
`carveouts.md §2.X`-Eintrag (Trigger 031 wurde in Welle-
1-C2 nicht in carveouts.md eingepflegt; hier nachgepflegt
als „Aufgeloest in M6-Welle-3-C2 `<C2-Hash>`"-Eintrag).

### Welle-3-D-5 — Sub-Slicing-Beobachtung

**Frage:** Wird Welle 3 als Single-Welle oder Sub-Slicing
3a/3b geliefert?

**Welle-3-C0-Vorbelegung: Single-Welle.** Begruendung:

- 4 NEU Workflow-Dateien sind kausal verbunden (CI-
  Vollausbau-Pflicht-Gates aus demselben Lastenheft-
  Block `GG-CICD-002/003/005/006`).
- Welle-2-Vorbild: 1 NEU `release.yml` mit 3 Jobs +
  Makefile/Dockerfile-Pflichtscope = 1 Welle; Welle-3-
  Substanz ist im selben Volumen-Bereich (4 NEU
  Workflow-Dateien ohne fundamentale Tool-Substanz; jeder
  Workflow ruft existierende `make`-Targets auf).
- Doc-Volumen-Schwelle (>300 Zeilen Slice-Doc): zur C0-
  Zeit beobachtet, in C0-Review-Folge final.

**Sub-Slicing-Beobachtung in C2:** Falls eine Workflow-
Substanz waehrend C2 unerwartet substanziell wird
(z. B. wenn `fullbuild.yml`-Compose-Smoke-CI komplexer
wird als erwartet — Docker-in-Docker, Service-Container
Tunneling, Caching-Strategie), wird in C2 nachtraeglich
auf Sub-Slicing 3a (test/coverage/dep-audit) / 3b
(fullbuild + Trigger 031) gewechselt.

Welle 3 trifft **keine** dieser Decisions:

- M6-D-1/D-2/D-3/D-3b — bereits in M6-Welle-0-C2
  entschieden.
- M6-D-5 — bereits in M6-Welle-1-C2 aufgeloest.
- M6-D-7 (Bench-Framework) — Welle-4-Scope.

---

## 4. Liefer-Reihenfolge (3-4 Commits)

### Pre-C0 — bereits erledigt (M6-Welle-2-Closure-Folge)

- `c51d905` (Pre-C0a: `git mv M6-welle-2.md → done/`).
- `b41b7fc` (Pre-C0b: Cross-Doc-Refs-Sync nach Move).
- `febbd22..3ccf01d` (4 Post-Closure-Korrekturen am Welle-
  2-`release.yml`-Stand — Welle-2-Substanz-Pflege, kein
  Welle-3-Pre-C0).

### C0 — `docs(plan)`: M6-welle-3 Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU [`M6-welle-3.md`](M6-welle-3.md) mit §1..§9-
  Struktur.
- `in-progress/README.md` Bestand-Tabelle um Welle-3-
  Zeile ergaenzt; Aktive-Welle-Block bestaetigt auf
  M6-Welle-3.
- `M6-perf-security-cicd.md §3.1` Welle-3-Zeile `Pending
  → In Progress 2026-06-05`.

### C1 entfaellt

Welle-3-Decisions (D-1..D-5) sind im C0-Slice-Doc-§3-Body
fixiert; ADR 0002 §6.1-Matrix-Substanz wird produktiv in
C2 ohne ADR-Schaerfung umgesetzt. Pattern analog M5-Welle-
2 `5234617` (kein C1-ADR; Decision-Substanz im Slice-Doc-
Body verankert).

### C2 — `feat(ci)`: 4 NEU Workflows + Trigger-031-Closure

Code-Merge mit:

- **NEU `.github/workflows/tests.yml`** (Pflicht):
  - Trigger: `push.branches: [main]` + `pull_request.
    branches: [main]` ohne Path-Filter.
  - 2 Jobs: `test-unit` (mit `strategy.matrix.python-
    version: ['3.13', '3.14']`) + `test-integration` (mit
    Default-Python; Compose-basiert, siehe §1.2 +
    Welle-3-D-2).
  - Cache: `type=gha,scope=test-unit-<python>` (Per-
    Python-Cache-Scope) fuer `test-unit`; Default-Cache
    fuer `test-integration`.
- **NEU `.github/workflows/coverage.yml`** (Pflicht):
  - Trigger: `push.branches: [main]` + `pull_request.
    branches: [main]` ohne Path-Filter.
  - Default-Python (3.14).
  - 2 Jobs: `coverage-gate` + `coverage-gate-critical`.
- **NEU `.github/workflows/dep-audit.yml`** (Pflicht):
  - Trigger: `push.branches: [main]` + `pull_request.
    branches: [main]` ohne Path-Filter.
  - Default-Python (3.14).
  - 1 Job: `dep-audit`.
- **NEU `.github/workflows/fullbuild.yml`** (Pflicht;
  Trigger-031-Aufloesung):
  - Trigger: `push.branches: [main]` + `pull_request.
    branches: [main]` mit **Paths-Filter** (Dockerfile/
    Makefile/src/tests/pyproject.toml/uv.lock/deploy/
    .github/workflows/fullbuild.yml) + `workflow_dispatch`.
  - Default-Python (3.14).
  - 1 Job: `make fullbuild` (umfasst gates + test-
    integration + openapi-validate + image-audit + build
    + runtime/compose-smoke).
- **`carveouts.md §2.X`** NEU Trigger-031-Eintrag (in
  Welle-1-C2 vergessen; hier nachgepflegt mit
  `Aufgeloest in M6-Welle-3-C2`-Marker).
- **Verifikation (lokal vor C2-Commit):**
  - `actionlint` (Docker `rhysd/actionlint:latest`)
    EXIT=0 auf alle 4 NEU Workflows + bestehende ci.yml +
    release.yml (5 Workflows total).
  - `shellcheck` (Docker `koalaman/shellcheck:stable`)
    auf alle eingebetteten `run:`-Bloecke EXIT=0.
  - `make gates` cache-frei gruen (10/10 A-1-Gates).
  - `make ci` cache-frei gruen.
  - `make fullbuild` cache-frei gruen.
  - `make docs-check` cache-frei gruen.

### C3 — `docs(plan)`: Status/DoD-Sync + Trigger-031-Move

**Welle-3-Closure-Sync.**

- `M6-welle-3.md` Status `In Progress → Done` mit Liefer-
  Hash-Stack.
- `M6-perf-security-cicd.md §3.1` Welle-3-Zeile `In
  Progress → Done` mit Closure-Hash + §3 Naechster-Slice-
  Block auf Welle 4 (Performance-Bench).
- **Trigger 031 `open/ → done/`-Move**: `git mv open/031-
  ci-make-fullbuild-gate.md done/`; Closure-Notiz-Block
  im done-Trigger; `carveouts.md §2.X` Trigger-031-Eintrag
  auf `Aufgeloest`; `open/README.md` Trigger-031-Zeile
  auf `done/`-Pfad mit `Closed`-Marker.
- **Top-Level-Doku-Sync:**
  - `README.md` + `README.de.md`: NEU CI-Workflow-Hinweis
    (5 GitHub-Actions-Workflows aktiv: ci/release/tests/
    coverage/dep-audit/fullbuild) + Python-3.13/3.14-
    Matrix-Erwaehnung.
  - `roadmap.md §3 M6` aktive-Welle-Block auf M6-Welle-4
    (Performance-Bench) + Welle-3-Abschluss-Notiz +
    `GG-CICD-002/003/005/006` DoD-Checkboxen auf `[x]`.

### Welle-3-Closure-Folge (nach C3, Pattern Welle-2)

- C4a `git mv M6-welle-3.md → done/` (rename-only).
- C4b Cross-Doc-Refs-Sync nach Move.

C4a/C4b dienen gleichzeitig als M6-Welle-4-Pre-C0a/Pre-
C0b.

---

## 5. Critical Files

**Welle-3-NEU (geschrieben in C0/C2):**

- `docs/plan/planning/in-progress/M6-welle-3.md` (C0,
  dieser Commit).
- `.github/workflows/tests.yml` (C2) — NEU 2-Job-Workflow
  mit Python-3.13/3.14-Matrix.
- `.github/workflows/coverage.yml` (C2) — NEU 2-Job-
  Workflow (Default-Python).
- `.github/workflows/dep-audit.yml` (C2) — NEU 1-Job-
  Workflow (Default-Python).
- `.github/workflows/fullbuild.yml` (C2) — NEU 1-Job-
  Workflow mit Paths-Filter + workflow_dispatch.

**Welle-3-MODIFY (in C0/C2/C3):**

- `docs/plan/planning/in-progress/README.md` (C0 + C3) —
  Bestand-Tabelle + Aktive-Welle-Block.
- `docs/plan/planning/in-progress/M6-perf-security-cicd.md`
  (C0 + C3) — §3.1 Welle-Status-Tabelle.
- `docs/plan/planning/in-progress/roadmap.md` (C3) — §3
  M6 aktive-Welle-Block + Welle-3-Abschluss-Block +
  `GG-CICD-002/003/005/006` DoD-Checkboxen.
- `docs/plan/planning/in-progress/carveouts.md` (C2 + C3)
  — NEU Trigger-031-Eintrag (vergessen in Welle 1; hier
  nachgepflegt) + auf `Aufgeloest` flippen in C3.
- `docs/plan/planning/open/README.md` (C3) — Trigger-031-
  Zeile auf `done/`-Pfad umgehakt.
- `docs/plan/planning/open/031-ci-make-fullbuild-gate.md`
  → `docs/plan/planning/done/031-ci-make-fullbuild-gate.md`
  (C3, `git mv` als Teil des C3-Commits; Closure-Notiz-
  Block analog Trigger 010 + 008).
- `README.md` + `README.de.md` (C3) — NEU CI-Workflow-
  Hinweis + Python-Matrix-Erwaehnung.

**Welle-3-UNBERUEHRT (kein Edit):**

- Aller Code unter `src/` (Welle 3 ist CI-Substanz, kein
  Python-Code-Pfad-Wechsel).
- Alle Tests unter `tests/` (Test-Counts bleiben
  1722/80).
- `Dockerfile` (Welle-1/2-Substanz bereits stabil; Welle
  3 ruft die bestehenden Stages auf).
- `Makefile` (Welle-2-Pflichtscope unangetastet; Welle 3
  ruft die bestehenden Targets auf).
- `.github/workflows/ci.yml` (Slice-025-Substanz
  unangetastet; Welle 3 fuegt 4 NEU Workflows neben
  `ci.yml`).
- `.github/workflows/release.yml` (Welle-2-Substanz
  unangetastet).
- ADRs 0001..0043 (Welle 3 erstellt keine NEU ADRs;
  ADR 0002 §6.1-Substanz wird produktiv ohne ADR-
  Schaerfung umgesetzt).

---

## 6. Verifikationspfad

**Welle-3-Gate:**

- `make docs-check` cache-frei gruen ueber alle Welle-3-
  Commits.
- `make gates` cache-frei gruen (10/10 A-1-Gates; Test-
  Counts unveraendert 1722/80/4 skipped).
- `make ci` cache-frei gruen.
- `make fullbuild` cache-frei gruen ohne `CRITICAL_COV_
  TARGETS`-Override.
- **`actionlint`** (Docker-Image-Variante) EXIT=0 auf
  alle 6 Workflows (`ci.yml` + `release.yml` + `tests.
  yml` + `coverage.yml` + `dep-audit.yml` + `fullbuild.
  yml`).
- **`shellcheck`** (Docker-Image-Variante) auf alle
  eingebetteten `run:`-Bloecke EXIT=0.

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur Doc-Substanz.
- C2 prueft alle 4 NEU Workflows + Lint-Substanz + alle
  bestehenden Gates gruen.
- C3 prueft Status-Flip + Trigger-031-Move + Top-Level-
  Doku-Sync.

**Abnahme-Verifikation (Lastenheft):**

- `GG-CICD-002` (Tests automatisch ausgefuehrt) produktiv
  erfuellt via `tests.yml`.
- `GG-CICD-003` (Quality Gates maschinenlesbar) produktiv
  erfuellt via `coverage.yml` + bestehendes `ci.yml` +
  `fullbuild.yml`.
- `GG-CICD-005` (Security-Scanning) produktiv erfuellt
  via `fullbuild.yml` (image-audit-Anteil).
- `GG-CICD-006` (Dependency-Scanning) produktiv erfuellt
  via `dep-audit.yml`.
- ADR 0002 §6.1 (Python-3.13/3.14-Matrix) produktiv
  erfuellt via `tests.yml`-Matrix.

**Verbleibendes Item (bedingt; analog Welle 2):**

- Reale GitHub-Actions-Run-Verifikation aller 4 NEU
  Workflows. Lokal verifiziert (actionlint + shellcheck
  + make-Targets); echter GitHub-Lauf folgt mit Push
  (User-Operation). Falls Trigger 032-Sensor-Pattern
  fortgesetzt: NEU `open/`-Trigger fuer Welle-3-CI-
  Workflow-Run-Sensor — oder als Erweiterung von
  Trigger 032 (Multi-Workflow-Sensor-Substanz).

---

## 7. Risiken

**R1 — `make fullbuild`-CI-Performance.** Compose-Smoke
+ image-audit + build + ci sind ~10min Compute pro Lauf.
Bei jedem Push/PR ist das teuer.
**Mitigation:** Paths-Filter in `fullbuild.yml` reduziert
Doc-only-Trigger; `workflow_dispatch`-Fallback fuer
Force-Runs. GHA-Cache (type=gha,scope=<target>) reduziert
Re-Build-Last erheblich.

**R2 — Python-Matrix-Compute-Doppelung.** Jeder Matrix-
Job laeuft alle Stages; Cache-Scope pro Python-Version
ist wichtig (`scope=test-unit-3.13` vs. `scope=test-unit-
3.14`), sonst Cache-Konflikte.
**Mitigation:** Cache-Scope explizit pro Python-Version
parametrisiert.

**R3 — Workflow-Datei-Anzahl-Drift.** Welle 3 fuegt 4 NEU
Workflows hinzu (auf jetzt 6 total: ci/release/tests/
coverage/dep-audit/fullbuild). Welle 4+ wird weitere
ergaenzen (z. B. perf.yml).
**Mitigation:** Konsistentes Pattern (eine Workflow-Datei
pro Concern); keine Workflow-Konsolidierung in Welle 3
(YAGNI).

**R4 — `tests.yml`-Matrix faengt Python-3.13-spezifische
Regressionen.** Welle-3-C2 fuehrt erstmals Python-3.13-
CI durch — koennte versteckte Test-Failures aufdecken
die im Dev-Default (3.14) nicht sichtbar waren.
**Mitigation:** Lokal-Test mit `PYTHON_VERSION=3.13`-
Override vor Push; falls Probleme: Test-Fixes in C2-
Substanz integriert ODER Matrix-Job-`continue-on-error`
fuer 3.13 mit NEU `open/`-Trigger fuer Folge-Slice.

**R5 — Welle-2-Carveouts-Drift.** Trigger 031 wurde in
Welle-1-C2 nicht in `carveouts.md` eingepflegt (User-
Befund). Welle 3 muss das nachpflegen (C2-Substanz).
**Mitigation:** §5 Critical Files Welle-3-MODIFY
explizit `carveouts.md` mit Trigger-031-Eintrag-Pflicht.

**R6 — Workflow-Run-Sensor-Pattern fortgesetzt.** Wie
in Welle 2 (Trigger 032) kann lokal nicht der reale
GitHub-Actions-Run verifiziert werden. Welle 3 bringt
4 weitere Workflows — Sensor-Pflicht waechst.
**Mitigation:** Welle-3-C3 entscheidet, ob NEU `open/`-
Trigger fuer Welle-3-Sensor-Run angelegt wird ODER
Trigger 032 zu Multi-Workflow-Sensor erweitert wird.

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack** (per
  [`../README.md`](../README.md) Wave-Self-Close-Commit-
  Konvention): sobald `M6-welle-3.md` Status `Done`
  erreicht (am Ende von C3), schliesst die Welle ihre
  eigene Commit-Sequenz mit einem reinen `git mv
  M6-welle-3.md → ../done/M6-welle-3.md` (C4a) +
  Cross-Doc-Refs-Sync (C4b). Pattern analog M6-Welle-2-
  C4a `c51d905`/C4b `b41b7fc`.
- C4a/C4b dienen gleichzeitig als M6-Welle-4-Pre-C0a/
  Pre-C0b.
- Keine NEU ADRs (Welle 3 ohne C1-ADR).
- Trigger 031 (`open/031-ci-make-fullbuild-gate.md`)
  wandert in C3 nach `done/`.

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **C0 — NEU `M6-welle-3.md`** mit §1..§9-Struktur
  (dieser Commit).
- [x] **C0 — `in-progress/README.md`** Bestand-Tabelle
  um `M6-welle-3.md`-Eintrag ergaenzt + Aktive-Welle-
  Block auf M6-Welle-3 bestaetigt.
- [x] **C0 — `M6-perf-security-cicd.md §3.1`** Welle-3-
  Zeile `Pending → In Progress` mit C0-Hash-Stub.
- [x] **C1 entfaellt** — keine ADR-Substanz; Welle-3-
  Decisions D-1..D-5 im C0-Slice-Doc-§3-Body fixiert
  (Pattern analog M5-Welle-2 `5234617`).
- [x] **C2 — NEU `.github/workflows/tests.yml`** mit
  Python-3.13/3.14-Matrix; 2 Jobs (`test-unit` Matrix +
  `test-integration` Default-Python) (`ce13253`).
- [x] **C2 — NEU `.github/workflows/coverage.yml`** mit
  2 Jobs (`coverage-gate` + `coverage-gate-critical`)
  (`ce13253`).
- [x] **C2 — NEU `.github/workflows/dep-audit.yml`** mit
  1 Job (`dep-audit`) (`ce13253`).
- [x] **C2 — NEU `.github/workflows/fullbuild.yml`** mit
  Paths-Filter + workflow_dispatch; 1 Job (`make
  fullbuild`); Trigger-031-Aufloesungs-Substanz
  (`ce13253`).
- [x] **C2 — `carveouts.md`** NEU Trigger-031-Eintrag
  (Welle-1-Vergesslichkeit nachgepflegt) plus NEU
  Trigger-032-Eintrag (Welle-2-Vergesslichkeit
  nachgepflegt) (`ce13253`); in C3 auf `Aufgeloest`
  geflippt.
- [x] **C2 — `actionlint`** EXIT=0 auf alle 6 Workflows
  (`Found 0 errors in 6 files`; v1.7.12).
- [x] **C2 — `shellcheck`** entfaellt — beide `run:`-
  Bloecke (`tests.yml` test-integration + `fullbuild.yml`)
  sind einzeilige Make-Aufrufe (`make test-integration`
  / `make fullbuild`); kein eingebetteter Shell-Code.
- [x] **C2 — `make gates`** cache-frei gruen ohne Override
  (10/10 A-1-Gates inkl. dep-audit nach `pip 26.1.1 →
  26.1.2`-Drift-Fix im selben C2-Commit; Test-Counts
  unveraendert 1722/80/4 skipped).
- [x] **C2 — `make ci`** cache-frei gruen (verifiziert via
  `make fullbuild`-Lauf).
- [x] **C2 — `make fullbuild`** cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override (`[fullbuild] full
  closure: ci + runtime image + compose smoke green`).
- [x] **C2 — Sub-Slicing-Beobachtung** entschieden:
  Single-Welle bestaetigt; Code-Diff scope-eng (4 NEU
  Workflow-YAMLs + 1 uv.lock-Drift-Fix + 1 carveouts-
  Pflege).
- [x] **C3 — `M6-welle-3.md`** Status `In Progress →
  Done 2026-06-05` mit Liefer-Hash-Stack `08a8034..
  c36f734` (C3 `c8ecbe4` + C3-Review-Folge `affdff7` +
  C4a `3b6d9bf` + C4b `c36f734`).
- [x] **C3 — `M6-perf-security-cicd.md §3.1`** Welle-3-
  Zeile `In Progress → Done` mit Closure-Hash + §3
  Naechster-Slice-Block auf Welle 4 ausgerichtet + §0
  Status-Block aktive Welle auf Welle 4.
- [x] **C3 — Trigger 031** `git mv open/031-* → done/
  031-*` + Closure-Notiz-Block im done-Trigger (Pattern
  analog Trigger 010 + 008) + `carveouts.md`-Eintrag
  auf `Aufgeloest in M6-Welle-3-C2 `ce13253`` geflippt
  + `open/README.md`-Sync (Trigger-031-Zeile auf
  `done/`-Pfad mit `Closed`-Marker).
- [x] **C3 — `README.md` + `README.de.md`** NEU CI-
  Workflow-Hinweis (6 GitHub-Actions-Workflows; Python-
  3.13/3.14-Matrix-Erwaehnung) in beiden Sprachen.
- [x] **C3 — `roadmap.md §3 M6`** aktive-Welle-Block
  auf M6-Welle-4 ausgerichtet + Welle-3-Abschluss-Notiz
  mit Stack-Range + 6 DoD-Checkboxen geflippt
  (`GG-CICD-002/003/006` + Python-Matrix + image-audit +
  Compose-Smoke).
- [x] **C3 — `in-progress/README.md`** Bestand-Tabelle
  Welle-3-Zeile auf `Done` + Aktive-Welle-Block auf
  M6-Welle-4.
- [x] **C3 — `make docs-check`** cache-frei gruen.
- [ ] **C3 — Reale Workflow-Run-Sensor-Check**
  (Folge-Operation analog Welle 2): **kein NEU `open/`-
  Trigger** angelegt — Welle-3-Workflows triggern bei
  jedem Push automatisch (im Gegensatz zum Release-
  Workflow, der Tag-Push oder Manual-Dispatch braucht).
  Sensor-Check passiert beim naechsten Push der C2/C3-
  Hashes ohne explizites User-Triggern; Restrisiko-
  Inventar bleibt analog Welle 2 (5 GitHub-Actions-
  Standard-Pattern-Klassen). Pointer auf done-Trigger-
  031 § „Verbleibendes Restrisiko".

**Anti-Scope-Verifikation (Welle 3 NICHT):**

- [x] Kein SBOM-Workflow-Edit (`release.yml` unangetastet).
- [x] Keine Performance-Bench (Welle-4-Scope; `GG-RT-005`).
- [x] Kein Security-Audit (Welle-5-Scope; `GG-SAFE-*`).
- [x] Kein Deploy-Hardening-Vollausbau (Welle-6-Scope;
  `GG-DEPLOY-*`).
- [x] Kein IEC-Smoke-Pfad-B (Welle-6-Scope; Trigger 009).
- [x] Keine URL-Versionierung `/api/v1` (`Deferred`-Item;
  M6-Welle-X-Material).
- [x] Keine ADR-Substanz-Erweiterung (Welle 3 ohne C1).

---

## 10. Post-Closure-Korrekturen-Index (Pflege nach Welle-3-C4b)

**Pflege-Pattern:** analog ADR 0028 Link-Maintenance und Welle-
2-Done-Slice-Doc §10.6. Die hier dokumentierte Substanz ist
Welle-3-Stand zum C4b-Closure-Zeitpunkt (`c36f734`); nach Closure
entdeckte Drifts in der CI-Workflow-Substanz werden in Folge-
Commits korrigiert, OHNE die Closure-Substanz oben zu revidieren.
Dieser Index listet die kanonischen Post-Closure-Korrektur-Hashes.

**Korrektur-Stack:**

| Commit | Stufe | Substanz |
| ------ | ----- | -------- |
| `0891f65` | Post-Push-CI-Fix | **F1 HIGH** `.python-version=3.14` blockierte test-unit Python-3.13-Matrix-Branch (uv-sync „No interpreter found"). Korrektur: `.python-version` aus `Dockerfile`-COPY-Block entfernt; Python-Version-Truth allein aus `ARG PYTHON_VERSION`. **F2 HIGH (Versuch; spaeter als wirkungslos entlarvt)** `otel/opentelemetry-collector-contrib:0.152.1` hatte CVE-2026-42504. Korrektur-Versuch: Image-Pin `0.152.1 → 0.153.0`. Lokal-Verifikation **war falsch positiv** wegen Stale-Trivy-Cache-DB. |
| `ede21ad` | Stale-DB-Drift-Aufloesung | Trivy-Host-Cache-Mount (`-v "$HOME/.cache/trivy:/root/.cache/"`) aus `Makefile` Z.282 + Z.291 entfernt. Lokale `make image-audit`-Laeufe mit alter Cache-DB hatten NEU veroeffentlichte CVEs nicht gemeldet — falsch-positive „lokal-gruen, CI-rot"-Diskrepanz. Performance-Wert war marginal (~25s Ersparnis pro Re-Run); CI hatte den Cache de facto nie. Konsequenz: `make image-audit` aufgedeckt als rot wegen CVE-2026-42504 in `0.153.0` (Image-Bump in `0891f65` war wirkungslos — `0.153.0` baut ebenfalls gegen `go1.26.3`). NEU `done/033-otel-collector-go-stdlib-cve-bump.md`-Trigger als ADR-0043-konformer Defer-Pfad (Pattern analog Trigger 010 fuer krb5). |

**Aktueller Workflow-Stand** (Post-Closure-Korrektur-Stand
nach `ede21ad`):

- `Makefile` `OTEL_COLLECTOR_IMAGE ?= otel/opentelemetry-
  collector-contrib:0.153.0` (Z.35) — Trigger 033
  ([`../done/033-otel-collector-go-stdlib-cve-bump.md`](../done/033-otel-collector-go-stdlib-cve-bump.md))
  verankert den Defer-Pfad bis OTel-Release mit
  `go1.26.4+`-Build.
- `Makefile` `image-audit` (Z.279-296) ohne Trivy-Host-
  Cache-Mount; Begruendungs-Kommentar verankert.
- `Dockerfile` deps-Stage `COPY pyproject.toml uv.lock ./`
  (ohne `.python-version`); Python-Version-Truth aus
  `ARG PYTHON_VERSION` (Z.23) ueber `FROM
  python:${PYTHON_VERSION}-slim`.
- `pyproject.toml` `requires-python = ">=3.13"` +
  `uv.lock` `requires-python = ">=3.13"` decken beide
  Matrix-Branches (3.13 + 3.14) korrekt ab.
- Alle 4 NEU Welle-3-Workflows (tests/coverage/dep-audit/
  fullbuild) plus ci.yml + release.yml unveraendert
  gegenueber Welle-3-C2 `ce13253`.
- `actionlint` (v1.7.12) EXIT=0 auf alle 6 Workflows
  unveraendert.

**Sensor-Run-Status nach `ede21ad`** (lokal ≡ CI):

- Tests / Coverage / Dep-Audit / CI: **gruen**.
- Fullbuild: **rot** wegen CVE-2026-42504 in OTel-
  Collector (Trigger 033 verankert den Defer-Pfad).
- Aufloesungs-Pfad: OTel-Bump auf `0.154.0+` sobald
  upstream verfuegbar (erwartete OTel-Release-Linie
  2026-06-09 bis 2026-06-12 per ~14-Tage-Kadenz).

---

## References

- [`../done/M6-welle-0.md §3 M6-D-6`](M6-welle-0.md)
  — M6-Welle-0-Decision-Vorbelegung Python-3.13/3.14-Matrix.
- [`../done/M6-welle-1.md §3 Welle-1-D-1`](M6-welle-1.md)
  + [`../done/M6-welle-1.md §10.2`](M6-welle-1.md)
  — Trigger-031-Vertagungs-Substanz aus Welle 1.
- [`../done/M6-welle-2.md`](M6-welle-2.md) —
  M6-Welle-2-Slice-Doc (Pattern-Vorbild fuer Welle-3-
  Workflow-Substanz).
- [`M6-perf-security-cicd.md §3.2 Welle 3`](M6-perf-security-cicd.md)
  — M6-Slice-Plan Welle-3-Vorbelegung.
- [`../done/031-ci-make-fullbuild-gate.md`](031-ci-make-fullbuild-gate.md)
  — Trigger 031 mit Aktivierungs-Substanz.
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md#gg-cicd-002)
  §22 `GG-CICD-002/003/005/006`-Akzeptanz.
- [`../../adr/0002-language-and-build-stack.md §6.1`](../../adr/0002-language-and-build-stack.md)
  — Python-3.13/3.14-Matrix-Pflicht-Quelle.
- [`../../../../.github/workflows/ci.yml`](../../../../.github/workflows/ci.yml)
  — Slice-025-Pflicht-Gates-Workflow (Pattern-Vorbild).
- [`../../../../.github/workflows/release.yml`](../../../../.github/workflows/release.yml)
  — Welle-2-Release-Workflow (Pattern-Vorbild fuer Multi-
  Job + Concurrency + Permissions).
- [`../done/spike-0.md`](spike-0.md) §6.1 — Spike-
  0-Closure-Decision D-8 (Python-Matrix-Verschiebung auf
  M6).
- [`../done/spike-0-results.md`](../done/spike-0-results.md)
  — Slice-025-Stand (4 CI-Pflicht-Gates).
