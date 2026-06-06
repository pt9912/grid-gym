# Welle 4b-a — M6 Performance-Bench-Foundation (`GG-RT-004` + ADR 0041)

**Status:** Done 2026-06-06 — Liefer-Stack: C0 `f2fbcc0`
(Slice-Doc-Anlage; Welle-4b-Sub-Slicing-Beschluss in 4b-a/4b-b/
4b-c) + C1 `43569d2` (NEU ADR-0041 `Provisional`; M6-D-7-
Vorbelegung aufgeloest) + C1-Review-Folge `f4f4983` (4 Findings
adressiert: F1 HIGH GG-RT-004-Replay-Diff + F2 HIGH project.
optional-dependencies.perf statt dependency-groups.perf + F3
MEDIUM Baseline-Pfad-Konsistenz + F4 MEDIUM make perf-baseline-
update als Helper-Target) + C2 `5d8c497` (NEU pytest-benchmark
+ Dockerfile-perf-Stage + tests/perf/ Layer + Makefile-Targets;
GG-RT-004-Doppel-Akzeptanz produktiv; Maintainer-Dev-Host-
Baseline 519ms / 1.92 OPS) + C3 (dieser Commit; Status/DoD-Sync
+ Top-Level-Doku). Ausstehend: C4a Self-Close-Move + C4b
Cross-Doc-Refs-Sync.

Welle 4 ist gemaess Welle-4a-D-1 in 4a (Generated-Trivyignore-
Permit; abgeschlossen) + 4b (Performance-Benchmark) sub-geslict.
Welle 4b ist gemaess **Welle-4b-a-D-1** (§3) weiter in **4b-a
(Bench-Foundation + `GG-RT-004`) + 4b-b (`GG-RT-005` Telemetry-
Port-Bench) + 4b-c (`GG-RT-001` Backpressure-Healthcheck)** sub-
geslict — Pattern analog M5-Welle-6 Sub-Slicing in 6a/6b/6c. Welle
4b-a ist die **erste Sub-Sub-Welle** und liefert die Bench-
Foundation (pytest-benchmark + Dockerfile-Stage + `make perf`-
Target + Baseline-Pinning) plus das **100-Geraete-Bench-Szenario**
(`GG-RT-004` SOLLTE) plus die DoD-Bestaetigung fuer `GG-RT-002`
(M1-Determinismus) und `GG-RT-003` (M3-Stale-Markierung), die
heute schon produktiv erfuellt sind.

**Pre-C0 abgeschlossen (M6-Welle-4a-Closure-Folge):**

- C4a `3bc58b8` — `git mv M6-welle-4a.md → done/` (Self-
  Close-Move, rename-only).
- C4b `789ac50` — Cross-Doc-Refs-Sync nach Move.
- Post-Closure-Review-Folge `6601e9b` + `04042ec` —
  F2 HIGH (ADR-0044-§2.2-Vertragsbruch) + F3/F4 LOW + Lint-
  Refactor (siehe `done/M6-welle-4a.md §10`).

**Spec-Reife:** Inhaltlich final fuer Welle 4b-a. Welle-4b-a-
Decision-Liste (§3) schliesst Welle-4b-a-D-1..D-6: Sub-Slicing-
Beschluss, Bench-Framework-Final (loest M6-D-7-Vorbelegung auf),
Bench-Layout, 100-Geraete-Szenario-Form, Baseline-Pinning,
CI-Hook-Form.

---

## 1. Context

**Welle-4-Vorbelegung** in [`M6-perf-security-cicd.md §3.2 Welle 4`](M6-perf-security-cicd.md)
ist Performance-Benchmark mit `GG-RT-001..005`. Welle-4a-Sub-
Slicing hat 4a (Vulnignore-Pattern) als urgent-Praeludium
geliefert; Welle 4b traegt die eigentliche Performance-Substanz.
Welle 4b wird weiter sub-geslict, weil die drei `GG-RT`-Substanz-
Aenderungen voneinander unabhaengig sind und gemeinsam ueber die
300-Zeilen-Slice-Doc-Schwelle gehen (M6-perf-security-cicd.md §3
Sub-Slicing-Schwelle).

### 1.1 Existierende Substanz (vor Welle 4b-a)

- **Keine bestehende Bench-Substanz**: kein `tests/perf/`-
  Verzeichnis, kein `pytest-benchmark`-Dep, kein `make perf`-
  Target, kein Dockerfile-`perf`-Stage. Welle 4b-a ist
  **Greenfield** fuer das Bench-Pattern.
- **TickLoop-Determinismus-Property** (`GG-RT-002`) produktiv
  seit M1 (`hexagon/core/simulation/scheduler.py` Tie-Breaking;
  `tools/check_core_determinism.py` als A-1-Gate-Vorlauf;
  ADR 0007 Random-Port-Schema). Welle 4b-a bestaetigt die DoD
  ohne Code-Edit.
- **Stale-Markierung** (`GG-RT-003`) per `hexagon/core/domain/
  quality.py` `stale`-Quality-Marker; M3-Welle-6c-Pipeline.
  Welle 4b-a bestaetigt die DoD ohne Code-Edit.
- **M6-D-7-Vorbelegung** ([`../done/M6-welle-0.md §3 M6-D-7`](../done/M6-welle-0.md)):
  pytest-benchmark als Bench-Framework (existierend-leichtgewichtig-
  Praeferenz). Welle-4b-a-C1-ADR (`ADR 0041`) entscheidet final.
- **TickLoop-Snapshot-Schema v2** (`ADR 0015`): Bench-Lauf muss
  den existierenden Snapshot-Schreib-/Lese-Pfad nicht beruehren.
- **`make gates`** als 10-A-1-Gate-Aggregator; `make perf` wird
  NICHT in `make gates` integriert (Welle-4b-a-D-6).

### 1.2 Welle-4b-a-Lieferziel

Drei orthogonale Liefer-Items:

1. **NEU ADR-0041 `Provisional`** (Welle-4b-a-C1) — Performance-
   Bench-Pattern verankert: Framework-Wahl (pytest-benchmark)
   + Mess-Protokoll (Tick-Throughput, p95-Jitter, Baseline-
   Comparison-Form) + Regression-Schwelle (relativer Drift
   gegenueber gepinneter Baseline) + Bench-Locations-Konvention
   (`tests/perf/`) + Bench-Run-Form (separater Dockerfile-Stage
   + `make perf`-Target, NICHT in `make gates`).
2. **NEU `tests/perf/` + Dockerfile-Stage** (Welle-4b-a-C2) —
   pytest-benchmark-Dep NEU im `pyproject.toml`-`[project.
   optional-dependencies.perf]`-Block (opt-in via `--extra
   perf`; Pattern analog `iec61850`-Extra aus ADR 0035;
   `[dependency-groups.perf]` waere NICHT opt-in-konform und
   ist explizit verboten per ADR-0041 §2.1) + `uv.lock`-Sync;
   NEU Dockerfile-`perf`-Stage analog `test-unit`-Stage mit
   zusaetzlichem `--extra perf`-Flag im `uv sync`-Aufruf;
   NEU `tests/perf/test_tick_loop_bench.py` mit `GG-RT-004`-
   Bench (100 Geraete × 10.000 Ticks; **Doppel-Akzeptanz** per
   ADR-0041 §2.2 — `lost_events == 0` UND Replay-Diff-
   Determinismus ueber zwei Runs mit identischem Seed).
3. **NEU `make perf`-Target + Baseline-Pinning** (Welle-4b-a-
   C2) — `Makefile`-`perf`-Target ruft Dockerfile-`perf`-Stage
   auf mit `--benchmark-compare=tests/perf/baseline.json`
   (vollstaendiger Repo-Root-Pfad); Baseline
   `tests/perf/baseline.json` als versioniertes Snapshot der
   Bench-Resultate; pytest-benchmark-Compare-Mode gegen
   Baseline. Regression-Schwelle: 20 % Median-Drift bricht
   den Lauf (ADR-0041-§2.3 verankert die Schwelle). Plus NEU
   `Makefile`-`perf-baseline-update`-Helper-Target fuer
   Baseline-Updates (ADR-0041-§2.6); loest den Make-Option-
   Konflikt mit `--benchmark-save=...` (GNU Make
   interpretiert das als Make-Option und bricht).

### 1.3 Welle-4b-a-Anti-Scope

- **Kein `GG-RT-005` Telemetry-Port-Bench** — eigene Welle-4b-
  b-Substanz (10 000 Points/s am Telemetry-Port; braucht
  Probe + Mess-Methodik). Welle 4b-a deckt das nicht.
- **Kein `GG-RT-001` Backpressure-Healthcheck** — eigene Welle-
  4b-c-Substanz (Tick-Dauer-/p95-Jitter-/missed-Ticks-
  Telemetrie als NEU TickLoop-Healthcheck-Surface). Welle 4b-a
  beruehrt das `tick_loop.py` Healthcheck-Surface NICHT.
- **Keine `GG-RT-002` Determinismus-Substanz** — produktiv seit
  M1; Welle 4b-a bestaetigt nur DoD.
- **Keine `GG-RT-003` Stale-Markierung-Substanz** — produktiv
  seit M3; Welle 4b-a bestaetigt nur DoD.
- **Kein Snapshot-Envelope-v2-Body-Serialisierung** —
  carveouts §2.1 als M5-Erbschaft. M6-perf-security-cicd.md
  §3.2 Welle 4 hatte das als „opportunistisch falls Performance-
  Bench die Stub-Surface anfasst" markiert; Welle-4b-a-Bench-
  Surface beruehrt die Snapshot-Body-Struktur nicht. Bleibt
  Erbe fuer eine spaetere Welle.
- **Keine `make perf`-Integration in `make gates`** — Welle-
  4b-a-D-6 entscheidet das separat als Welle-Substanz.
- **Kein CI-Workflow `perf.yml`** — Welle 4b-a liefert `make
  perf` lokal; CI-Hook ist Welle-4b-Closure- oder M6-Welle-7-
  Closure-Material (sobald alle drei 4b-Sub-Wellen die Bench-
  Substanz tragen).
- **Keine Coverage-Pflicht fuer `tests/perf/`** — Bench-Tests
  sind Performance-Mess-Substanz, kein Coverage-Beitrag.
  `pyproject.toml`-`[tool.coverage.run].source`-Pfad bleibt
  unangetastet.

---

## 2. Scope

Welle 4b-a liefert **vier Items** ueber 3-4 Commits (C0..C3),
plus Self-Close-Folge C4a/C4b.

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses Dokument;
   in-progress/README.md-Bestand-Tabelle + M6-perf-security-
   cicd.md §3.1 Welle-4b in 4b-a/4b-b/4b-c gespalten.
2. **ADR-Substanz** (C1) — NEU ADR-0041 `Provisional`
   (Performance-Bench-Pattern); ADR-Index update; Decision-D-2
   geschlossen.
3. **Code-Substanz** (C2) — NEU `pyproject.toml`-`[dependency-
   groups.perf]`-Block + `uv.lock`-Sync + NEU Dockerfile-
   `perf`-Stage + NEU `tests/perf/test_tick_loop_bench.py` +
   NEU `tests/perf/baseline.json` + NEU `Makefile`-`perf`-
   Target. Lokal-Verifikation `make perf` cache-frei gruen.
4. **Status/DoD-Sync** (C3) — `M6-welle-4b-a.md` auf `Done`;
   `M6-perf-security-cicd.md §3.1` Welle-4b-a-Zeile auf
   `Done`; Top-Level-Doku-Sync (`README.md`/`README.de.md`
   `make perf`-Hinweis; `roadmap.md §3 M6` aktive Welle auf
   M6-Welle-4b-b).

Self-Close-Folge C4a/C4b laufen nach C3 als M6-Welle-4b-b-
Pre-C0a/Pre-C0b.

---

## 3. Architektur-Entscheidungen (Welle-4b-a-Decision-Liste)

### Welle-4b-a-D-1 — Welle-4b-Sub-Slicing-Beschluss

**Frage:** Wird Welle 4b als Single-Welle (alle `GG-RT-*`) oder
in 4b-a/4b-b/4b-c sub-geslict?

**Welle-4b-a-Final: Sub-Slicing in 4b-a + 4b-b + 4b-c.**
Begruendung:

- Die drei `GG-RT`-Substanz-Aenderungen (Bench-Foundation /
  Telemetry-Port-Bench / Backpressure-Healthcheck) sind
  voneinander unabhaengig und beruehren unterschiedliche
  Code-Pfade.
- Single-Welle-Slice-Doc waere > 400 Zeilen + Code-Diff > 5
  Commits — Sub-Slicing-Schwelle aus `M6-perf-security-cicd.md
  §3` greift.
- Pattern-Praezedenz: M5-Welle-6 Sub-Slicing 6a/6b/6c hatte
  drei thematisch getrennte Substanz-Bereiche (Fault-Flow /
  UI-Visualization / Abnahmedoku) und hat sich bewaehrt.

### Welle-4b-a-D-2 — Bench-Framework

**Frage:** Welches Bench-Framework? Aufloesung der M6-D-7-
Vorbelegung.

Optionen (aus M6-D-7):

- **A — pytest-benchmark** (existierend-leichtgewichtig).
- **B — pyperf** (Python-Standard; robuster fuer Mikro-Bench).
- **C — asv** (komplettes Bench-Suite-Tool).

**Welle-4b-a-Final: Option A (pytest-benchmark).** Begruendung:

- Konsistenz mit existierender pytest-Infrastruktur (test-unit/
  test-integration nutzen pytest; Dockerfile-Stages, Markers,
  Conftest, etc.).
- Kein neuer Tooling-Stack noetig; Mess-Substanz reicht
  vollkommen aus fuer `GG-RT-004` (100-Geraete-Throughput-
  Mess).
- pyperf waere fuer Mikro-Bench besser; aber `GG-RT-004` ist
  Makro (10 000 Ticks); pyperf-Praezision ist Overkill.
- asv waere fuer Time-Series-Bench-Tracking sinnvoll; aber
  grid-gym hat keine Continuous-Performance-Tracking-
  Infrastruktur und braucht sie nicht (Baseline-Pinning
  reicht).

### Welle-4b-a-D-3 — Bench-Locations + Naming

**Frage:** Wo leben die Bench-Tests?

Optionen:

- **A — `tests/perf/`** (eigene Top-Level-Test-Tree-Branch).
- **B — `tests/integration/perf/`** (Sub-Branch unter
  Integration).
- **C — `tests/unit/perf/`** (Sub-Branch unter Unit).

**Welle-4b-a-Final: Option A (`tests/perf/`).** Begruendung:

- Bench-Tests sind weder Unit (kein Coverage-Beitrag) noch
  Integration (kein Compose-Sibling). Eigene Top-Level-
  Branche klar abgegrenzt.
- `make perf` als Pflicht-Target ist orthogonal zu `make
  test-unit` / `make test-integration` — Pfad-Trennung
  spiegelt das.
- Pattern-Praezedenz: viele Python-Projekte trennen `tests/
  perf/` analog (z. B. uvloop, sqlalchemy).

### Welle-4b-a-D-4 — 100-Geraete-Szenario-Form

**Frage:** Wie wird das 100-Geraete-Szenario fuer `GG-RT-004`
konstruiert?

Optionen:

- **A — Synthetisch in pytest-Fixture** (programmatisch
  100 Battery/PV/Load-Geraete im `_build_devices`-Pattern).
- **B — NEU YAML-Szenario** unter `tests/perf/fixtures/`.
- **C — Erweiterung des `mvp_demo.yaml`** mit 100-Geraete-
  Variante.

**Welle-4b-a-Final: Option A (Synthetisch in pytest-Fixture).**
Begruendung:

- Bench-Test-Substanz soll vom YAML-Loader entkoppelt sein
  (Loader-Drift macht Bench-Drift, nicht TickLoop-Drift). Die
  programmatische Fixture isoliert die Mess-Surface.
- Einfacher Maintenance-Pfad: Geraete-Anzahl ist Parameter,
  kein YAML-Edit noetig.
- Vorbild: M3-Welle-6c-Demo-Smoke nutzt programmatische
  Konstruktion (`InMemoryRunRepository`-Pattern); Pattern
  bewaehrt.

### Welle-4b-a-D-5 — Baseline-Pinning-Form

**Frage:** Wie wird die Bench-Baseline fuer Regression-Vergleich
gehalten?

Optionen:

- **A — Versioniert als `tests/perf/baseline.json`** (commit-
  gepinnt; Updates erfordern PR-Review).
- **B — Externe DB** (e. g. asv-DB; Continuous-Tracking).
- **C — `make perf` nur Run, keine Schwelle** (nur Sensor,
  kein Gate).

**Welle-4b-a-Final: Option A (committed `baseline.json`).**
Begruendung:

- Reproducible across Forks/Clones ohne externe DB.
- Audit-Trail im Git-Log: Baseline-Updates sind sichtbare
  Commits mit Begruendung (Pattern analog `uv.lock`-Pin).
- Regression-Schwelle 20 % Median-Drift bricht `make perf`
  (Option C als reiner Sensor-Modus waere nicht audit-
  belastbar). Schwelle in ADR-0041 §2 verankert.

### Welle-4b-a-D-6 — CI-Hook-Form

**Frage:** Wird `make perf` als A-1-Gate-Aggregat-Bestandteil
gefuehrt (`make gates` oder `make ci`) ODER als eigener Pfad?

**Welle-4b-a-Final: Eigener Pfad; NICHT in `make gates`/`make
ci`.** Begruendung:

- Bench-Lauf ist teuer (Welle-4b-a-C2-Verifikation: erwartet
  ~30-60s); `make gates` muss schnell bleiben (< 90s lokal).
- Performance-Regression ist eine eigene Audit-Stufe — keine
  Verkoppelung mit Lint/Type/Coverage-Gates.
- CI-Workflow `perf.yml` ist NICHT Welle-4b-a-Scope; spaetere
  Welle (4b-Closure oder M6-Welle-7) entscheidet, ob CI-Hook
  noetig.

---

## 4. Liefer-Reihenfolge (3-4 Commits)

### Pre-C0 — bereits erledigt (M6-Welle-4a-Closure-Folge)

- `3bc58b8` (Pre-C0a: `git mv M6-welle-4a.md → done/`).
- `789ac50` (Pre-C0b: Cross-Doc-Refs-Sync nach Move).
- `6601e9b` + `04042ec` (Post-Closure-Review-Folge; siehe
  `done/M6-welle-4a.md §10`).

### C0 — `docs(plan)`: M6-welle-4b-a Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU `M6-welle-4b-a.md` (dieses Dokument).
- `in-progress/README.md` Bestand-Tabelle um Welle-4b-a-Zeile
  + Aktive-Welle-Block auf M6-Welle-4b-a.
- `M6-perf-security-cicd.md §3.1` Welle-4b-Zeile in 4b-a/4b-b/
  4b-c gespalten (4b-a `In Progress 2026-06-06`; 4b-b + 4b-c
  bleiben `Pending`); §3.2 Welle-4-Block um Sub-Sub-Slicing-
  Notiz erweitert.

### C1 — `docs(adr)`: NEU ADR-0041 `Provisional`

Code-Merge mit:

- NEU `docs/plan/adr/0041-performance-bench-pattern.md`
  `Provisional` (M6-Welle-0-D-4-Vorbelegung). §2.1 Framework-
  Wahl + §2.2 Mess-Protokoll + §2.3 Regression-Schwelle +
  §2.4 Locations + §2.5 Run-Form (NICHT in `make gates`).
- `docs/plan/adr/README.md` Aktive-ADRs-Tabelle um ADR-0041-
  Zeile (Pattern analog ADR-0042/ADR-0043/ADR-0044).

### C2 — `feat(perf)`: pytest-benchmark + tests/perf/ + make perf

Code-Merge mit:

- NEU `pyproject.toml`-`[project.optional-dependencies.perf]`-
  Block mit `pytest-benchmark>=4.0,<6.0` (Pattern analog
  `iec61850`-Extra aus ADR 0035; opt-in via `--extra perf`)
  + `uv lock`-Sync (NEU `uv.lock`-Eintrag).
- NEU `Dockerfile`-`perf`-Stage analog `test-unit`-Stage
  mit `--extra perf`-Flag:
  `uv sync --frozen --all-groups --extra iec61850 --extra perf`
  + `uv run pytest tests/perf/ --benchmark-only
  --benchmark-compare=tests/perf/baseline.json
  --benchmark-compare-fail=median:20%`.
- NEU `tests/perf/__init__.py` (Marker).
- NEU `tests/perf/conftest.py` mit Fixtures fuer
  100-Geraete-TickLoop-Konstruktion (synthetisch, programmatisch;
  keine YAML-Loader-Abhaengigkeit).
- NEU `tests/perf/test_tick_loop_bench.py` mit
  `test_tick_loop_100_devices_10000_ticks_throughput` (pytest-
  benchmark-Decorator; **`GG-RT-004`-Doppel-Akzeptanz** per
  ADR-0041 §2.2: `assert lost_events == 0` UND Replay-Diff-
  Determinismus `assert run_a.snapshot() == run_b.snapshot()`
  ueber zwei Runs mit identischem Seed).
- NEU `tests/perf/baseline.json` mit initialer Baseline
  (Local-Run vor C2-Commit; committed mit Hash-Anchor).
- NEU `Makefile`-`perf`-Target (PHONY) ruft Dockerfile-`perf`-
  Stage mit `--benchmark-compare=tests/perf/baseline.json
  --benchmark-compare-fail=median:20%`.
- NEU `Makefile`-`perf-baseline-update`-Helper-Target (PHONY)
  loest Make-Option-Konflikt mit `--benchmark-save=...`
  (Pattern analog `make render-trivyignore`: docker-run mit
  Bind-Mount, schreibt Snapshot direkt nach
  `tests/perf/baseline.json`).
- NEU Makefile-`PHONY`-Block + `help`-Block fuer `make perf`
  und `make perf-baseline-update`.
- **Verifikation (lokal vor C2-Commit):**
  - `make perf` cache-frei gruen (Bench-Lauf + Baseline-
    Compare).
  - `make gates` cache-frei gruen (10/10 A-1-Gates; Test-Counts
    unveraendert 1732/80/4 skipped).
  - `make fullbuild` cache-frei gruen.
  - `make docs-check` cache-frei gruen.

### C3 — `docs(plan)`: Status/DoD-Sync

**Welle-4b-a-Closure-Sync.**

- `M6-welle-4b-a.md` Status `In Progress → Done 2026-06-06`
  mit Liefer-Hash-Stack.
- `M6-perf-security-cicd.md §3.1` Welle-4b-a-Zeile `In
  Progress → Done` mit Closure-Hash + Aktive-Welle-Block auf
  M6-Welle-4b-b.
- **Top-Level-Doku-Sync:**
  - `README.md` + `README.de.md`: NEU `make perf`-Hinweis +
    `GG-RT-004`-Akzeptanz-Notiz.
  - `roadmap.md §3 M6` aktive-Welle-Block auf M6-Welle-4b-b
    + Welle-4b-a-Abschluss-Notiz mit Stack-Range.

### Welle-4b-a-Closure-Folge (nach C3, Pattern Welle-4a)

- C4a `git mv M6-welle-4b-a.md → done/` (rename-only).
- C4b Cross-Doc-Refs-Sync nach Move.

C4a/C4b dienen gleichzeitig als M6-Welle-4b-b-Pre-C0a/Pre-C0b.

---

## 5. Critical Files

**Welle-4b-a-NEU (geschrieben in C0/C1/C2):**

- `docs/plan/planning/in-progress/M6-welle-4b-a.md` (C0,
  dieser Commit).
- `docs/plan/adr/0041-performance-bench-pattern.md` (C1).
- `tests/perf/__init__.py` + `tests/perf/conftest.py` +
  `tests/perf/test_tick_loop_bench.py` + `tests/perf/
  baseline.json` (C2).

**Welle-4b-a-MODIFY (in C0/C1/C2/C3):**

- `docs/plan/planning/in-progress/README.md` (C0 + C3).
- `docs/plan/planning/in-progress/M6-perf-security-cicd.md`
  (C0 + C3) — §3.1 Welle-Status-Tabelle (4b → 4b-a + 4b-b +
  4b-c gespalten); §3.2 Welle-4-Block um Sub-Sub-Slicing-Notiz.
- `docs/plan/adr/README.md` (C1) — ADR-Index Aktive-ADRs-
  Tabelle um ADR-0041-Zeile.
- `pyproject.toml` (C2) — NEU `[dependency-groups.perf]`-
  Block.
- `uv.lock` (C2) — Lock-Sync nach Dep-Add.
- `Dockerfile` (C2) — NEU `perf`-Stage.
- `Makefile` (C2) — NEU `perf`-Target.
- `docs/plan/planning/in-progress/roadmap.md` (C3) — §3 M6
  aktive-Welle-Block + Welle-4b-a-Abschluss-Notiz.
- `README.md` + `README.de.md` (C3) — NEU `make perf`-Hinweis.

**Welle-4b-a-UNBERUEHRT (kein Edit):**

- Aller Code unter `src/grid_gym/` (Welle 4b-a ist Bench-
  Substanz; kein Python-Produktiv-Code-Pfad-Wechsel).
- Alle Tests unter `tests/unit/` und `tests/integration/`
  (Test-Counts bleiben 1732/80/4).
- ADRs 0001..0044 (Welle 4b-a fuegt NEU ADR-0041 hinzu;
  Bestehende `Provisional`/`Accepted`-Texte bleiben
  unangetastet).
- Alle GitHub-Actions-Workflows (Welle-3-/4a-Substanz
  unangetastet; kein NEU `perf.yml`-Workflow in Welle 4b-a).
- `deploy/compose.yml` + `deploy/security/vulnignore.yaml`
  + `tools/render_trivyignore.py` (Welle-4a-Substanz
  unangetastet).

---

## 6. Verifikationspfad

**Welle-4b-a-Gate:**

- `make docs-check` cache-frei gruen ueber alle Welle-4b-a-
  Commits.
- `make gates` cache-frei gruen (10/10 A-1-Gates; Test-Counts
  unveraendert 1732/80/4 skipped).
- `make ci` cache-frei gruen.
- `make fullbuild` cache-frei gruen ohne `CRITICAL_COV_
  TARGETS`-Override.
- `make perf` cache-frei gruen (Bench-Lauf + Baseline-Compare;
  `GG-RT-004`-Doppel-Akzeptanz per ADR-0041 §2.2: 100 Geraete ×
  10 000 Ticks ohne verlorene Events UND ohne nichtdeterministischen
  Replay-Diff ueber zwei Runs mit identischem Seed).

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur Doc-Substanz.
- C1 prueft ADR-0041-Body + ADR-Index-Konsistenz.
- C2 prueft Dep-Sync + Dockerfile-Stage + `tests/perf/`-Layout
  + Bench-Run + Baseline-Compare.
- C3 prueft Status-Flip + Top-Level-Doku-Sync.

**Abnahme-Verifikation (Lastenheft):**

- `GG-RT-002` (Determinismus) produktiv seit M1 (`hexagon/
  core/simulation/scheduler.py` Tie-Breaking); Welle-4b-a-
  DoD bestaetigt durch `tools/check_core_determinism.py`-
  A-1-Gate-Pflicht-Lauf in `make gates`.
- `GG-RT-003` (Stale-Markierung) produktiv seit M3-Welle-6c
  (`hexagon/core/domain/quality.py`-`stale`-Enum-Wert +
  TickLoop-Quality-Stage); Welle-4b-a-DoD bestaetigt durch
  bestehende Unit-Tests `tests/unit/hexagon/core/domain/
  test_quality.py`.
- `GG-RT-004` (100 Geraete × 10 000 Ticks SOLLTE) produktiv
  in Welle-4b-a-C2 via `tests/perf/test_tick_loop_bench.py`
  mit Doppel-Akzeptanz (lost_events + Replay-Diff per ADR-
  0041 §2.2 — Lastenheft Z.486 verlangt beide Klassen).

**Verbleibendes Item (bedingt):**

- Reale Cross-Maschinen-Bench-Vergleich. `tests/perf/
  baseline.json` ist auf dem Maintainer-Dev-Host gemessen;
  CI-Runner-Bench (GitHub-Actions ubuntu-latest) kann
  abweichen. Welle-4b-a beschliesst KEINEN CI-Hook (Welle-
  4b-a-D-6); spaetere Welle entscheidet ggf. CI-Bench-
  Schwelle.

---

## 7. Risiken

**R1 — pytest-benchmark-Dep-Schwergewicht.** pytest-benchmark
zieht `py-cpuinfo` + `pytest-benchmark` als Transitive-Deps;
`uv.lock` waechst.
**Mitigation:** Dep-Group `[dependency-groups.perf]` als
opt-in (nicht in `[project.dependencies]`); Default-`uv sync`
ohne `--group perf` zieht es nicht. `make perf` als
einziger Konsumer.

**R2 — Bench-Resultat-Instabilitaet auf Dev-Host.** Bench-
Resultate variieren je nach Host-Last (Background-Prozesse,
CPU-Throttling); 20 %-Median-Schwelle koennte False-Positive
brechen.
**Mitigation:** pytest-benchmark `--benchmark-disable-gc` +
`--benchmark-min-rounds=10` als Default in `tests/perf/
conftest.py`-Marker; Maintainer-Run-Doku im README erwaehnt
„unter Last neu messen".

**R3 — Baseline-Drift-Konflikte.** Baseline-Updates erfordern
PR-Review-Aufmerksamkeit. Bei legitimer Performance-
Verbesserung muss Maintainer die Baseline neu pinnen.
**Mitigation:** ADR-0041 §2.3 verankert das Update-Pattern
(commit-message-Pflicht „perf: baseline update — <reason>";
manueller `make perf-baseline-update`-Helper-Target oder
einfacher `make perf --benchmark-save=...`-Workflow).

**R4 — `make perf` cache-frei-Laufzeit.** Bench-Lauf ist
~30-60s ohne Cache; mit Cache ~5-15s.
**Mitigation:** Dockerfile-Stage-Cache nutzt `tests/perf/
__init__.py`-Layer-Trennung; Dev-Workflow `make perf-quick`
mit `--benchmark-min-rounds=3`-Override moeglich (Welle-4b-
Closure entscheidet).

**R5 — 20 %-Median-Schwelle zu strikt / zu locker.** 20 %
ist eine plausible-aber-nicht-empirisch-validierte
Defaultschwelle.
**Mitigation:** ADR-0041 §2.3 verankert die initialie
Schwelle; spaetere Schaerfung per ADR-0011-Pattern
(`ADR-0050`+ falls aus Bench-Erfahrung andere Schwelle
besser).

**R6 — Welle-4b-a-Sub-Sub-Slicing-Komplexitaet.** 4 Sub-
Slices in einer Welle (4a + 4b-a + 4b-b + 4b-c) sind
Pattern-Drift gegen M5-Welle-4 (nur 4a + 4b) und
M5-Welle-6 (6a + 6b + 6c).
**Mitigation:** Welle-4b-a-D-1 verankert den Beschluss
inhaltlich; M6-perf-security-cicd.md §3.1 listet die vier
Zeilen explizit; Slice-Doc-Naming `M6-welle-4b-a.md` mit
Bindestrich-Trennung als visuelle Marker.

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack**: sobald
  `M6-welle-4b-a.md` Status `Done` erreicht (am Ende von C3),
  schliesst die Welle ihre eigene Commit-Sequenz mit einem
  reinen `git mv M6-welle-4b-a.md → ../done/M6-welle-4b-a.md`
  (C4a) + Cross-Doc-Refs-Sync (C4b). Pattern analog M6-Welle-
  4a-C4a `3bc58b8`/C4b `789ac50`.
- C4a/C4b dienen gleichzeitig als M6-Welle-4b-b-Pre-C0a/
  Pre-C0b.
- NEU ADR 0041 wird in C1 angelegt; `Provisional → Accepted`
  in M6-Welle-7-Closure-C1 gebuendelt mit ADR 0042 + ADR 0043
  + ADR 0044 (Pattern analog M5-Welle-7-C1 `62f988d`).

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **C0 — NEU `M6-welle-4b-a.md`** mit §1..§9-Struktur
  (dieser Commit).
- [x] **C0 — `in-progress/README.md`** Bestand-Tabelle
  um `M6-welle-4b-a.md`-Eintrag + Aktive-Welle-Block auf
  M6-Welle-4b-a.
- [x] **C0 — `M6-perf-security-cicd.md §3.1`** Welle-4b-
  Zeile in 4b-a/4b-b/4b-c gespalten; 4b-a `Pending → In
  Progress 2026-06-06`.
- [x] **C1 — NEU `docs/plan/adr/0041-performance-bench-
  pattern.md`** `Provisional` (M6-D-7-Vorbelegung
  aufgeloest).
- [x] **C1 — `docs/plan/adr/README.md`** ADR-Index um
  ADR-0041-Zeile ergaenzt.
- [x] **C2 — NEU `pyproject.toml`-`[project.optional-
  dependencies.perf]`** + `uv.lock`-Sync mit
  `pytest-benchmark>=4.0,<6.0` (opt-in via `--extra perf`;
  Pattern analog `iec61850`-Extra aus ADR 0035).
- [x] **C2 — NEU `Dockerfile`-`perf`-Stage** analog
  `test-unit` mit `--extra perf`-Flag im `uv sync`-Aufruf.
- [x] **C2 — NEU `tests/perf/`** mit `__init__.py` +
  `conftest.py` + `test_tick_loop_bench.py` + `baseline.
  json`.
- [x] **C2 — NEU `Makefile`-`perf`-Target** (PHONY) +
  NEU `perf-baseline-update`-Helper-Target (PHONY; loest
  Make-Option-Konflikt mit `--benchmark-save`) +
  Help-Block-Erweiterung.
- [x] **C2 — `make perf`** cache-frei gruen lokal
  (`GG-RT-004`-Doppel-Akzeptanz per ADR-0041 §2.2:
  100 Geraete × 10 000 Ticks ohne verlorene Events UND
  ohne nichtdeterministischen Replay-Diff; Baseline-Compare
  gegen `tests/perf/baseline.json` innerhalb 20 % Median-Drift).
- [x] **C2 — `make gates`** cache-frei gruen (10/10 A-1-
  Gates; Test-Counts unveraendert 1732/80/4 skipped).
- [x] **C2 — `make ci`** cache-frei gruen lokal.
- [x] **C2 — `make fullbuild`** cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override lokal.
- [x] **C3 — `M6-welle-4b-a.md`** Status `In Progress →
  Done 2026-06-06` mit Liefer-Hash-Stack.
- [x] **C3 — `M6-perf-security-cicd.md §3.1`** Welle-4b-a-
  Zeile `In Progress → Done` mit Closure-Hash + Aktive-
  Welle-Block auf Welle 4b-b.
- [x] **C3 — `README.md` + `README.de.md`** NEU
  `make perf`-Hinweis + `GG-RT-004`-Akzeptanz-Notiz.
- [x] **C3 — `roadmap.md §3 M6`** aktive-Welle-Block auf
  M6-Welle-4b-b + Welle-4b-a-Abschluss-Notiz mit Stack-Range.
- [x] **C3 — `in-progress/README.md`** Bestand-Tabelle
  Welle-4b-a-Zeile auf `Done` + Aktive-Welle-Block auf
  M6-Welle-4b-b.
- [x] **C3 — `make docs-check`** cache-frei gruen.

**Anti-Scope-Verifikation (Welle 4b-a NICHT):**

- [x] Kein `GG-RT-005` Telemetry-Port-Bench (Welle-4b-b-Scope).
- [x] Kein `GG-RT-001` Backpressure-Healthcheck (Welle-4b-c-
  Scope).
- [x] Keine `GG-RT-002` Determinismus-Substanz-Aenderung
  (M1-Produktiv-Stand).
- [x] Keine `GG-RT-003` Stale-Markierung-Substanz-Aenderung
  (M3-Welle-6c-Produktiv-Stand).
- [x] Kein Snapshot-Envelope-v2-Body-Serialisierung
  (carveouts §2.1 als M5-Erbschaft).
- [x] Keine `make perf`-Integration in `make gates`/`make ci`
  (Welle-4b-a-D-6).
- [x] Kein CI-Workflow `perf.yml` (M6-Welle-7-Closure-Material
  oder spaeter).
- [x] Keine Coverage-Pflicht fuer `tests/perf/`.

---

## References

- [`../done/M6-welle-4a.md`](../done/M6-welle-4a.md) —
  M6-Welle-4a-Slice-Doc (Vorbild fuer Slice-Struktur +
  Sub-Slicing-Pattern + Post-Closure-Korrektur-Stack).
- [`../done/M6-welle-0.md §3 M6-D-7`](../done/M6-welle-0.md)
  — M6-D-7-Bench-Framework-Vorbelegung (pytest-benchmark).
- [`M6-perf-security-cicd.md §3.2 Welle 4`](M6-perf-security-cicd.md)
  — M6-Slice-Plan Welle-4-Vorbelegung (Performance-Bench).
- [`../../../../spec/lastenheft.md §7 GG-RT-001..006`](../../../../spec/lastenheft.md)
  — Lastenheft-Akzeptanz fuer `GG-RT-002` + `GG-RT-003` +
  `GG-RT-004`.
- [`../../adr/0007-random-port.md §5.2`](../../adr/0007-random-port.md)
  — Determinismus-Vertrag (`GG-RT-002`-Substanz-Quelle).
- [`../../adr/0015-snapshot-envelope-v2.md`](../../adr/0015-snapshot-envelope-v2.md)
  — Snapshot-Schema (Bench-Surface beruehrt das nicht).
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — Schaerfungs-Pattern (ADR-0041 nutzt das nicht — ADR-0041
  ist eigenstaendiger Vertrag).
- pytest-benchmark Doku: https://pytest-benchmark.readthedocs.io/
- M5-Welle-6-Sub-Slicing-Pattern (Pattern-Vorbild fuer 3-way
  Sub-Slicing): `../done/M5-welle-6a.md` + `M5-welle-6b.md` +
  `M5-welle-6c.md`.
