# ADR 0041 — Performance-Bench-Pattern + Regression-Schwelle (M6 Welle 4b-a)

**Status:** Provisional — direkter `Proposed → Provisional`-
Sprung in M6-Welle-4b-a-C1 (dieser ADR). Loest die M6-Welle-0-
D-4-Vorbelegung und die M6-D-7-Bench-Framework-Vorbelegung auf.
`Accepted` folgt in M6-Welle-7-Closure-C1 gebuendelt mit ADR 0042
+ ADR 0043 + ADR 0044 (Pattern analog M5-Welle-7-C1 `62f988d`).
**Datum:** 2026-06-06
**Status geaendert am:** 2026-06-06 — `Proposed → Provisional`
mit M6-Welle-4b-a-C1 (dieser Commit).
**Bezug:**
[`ADR 0029`](0029-no-coverage-pragma-contract.md) (Quality-Gate-
Vertrag-Pattern-Vorbild — ADR 0029 fixiert die Coverage-Gate-
Disziplin als wiederverwendbaren A-1-Vertrag, ADR 0041 folgt
derselben Form fuer einen NICHT-A-1-Gate `make perf`),
[`ADR 0042`](0042-sbom-tool-and-release-pattern.md) (SBOM-Tool +
Release-Workflow; Schwester-Pattern fuer Tooling-Pflicht-Gate),
[`ADR 0043`](0043-image-audit-strategy.md) (Image-Audit-Strategie;
Schwester-Pattern fuer Quality-Gate-Vertrag mit Defer-Form),
[`ADR 0044`](0044-generated-trivyignore-permit.md) (Schaerfung an
ADR-0043; Schwester-Pattern fuer ADR-0011-Schaerfung).

---

## 1. Kontext

`GG-RT-004` SOLLTE (`spec/lastenheft.md §7`) verlangt einen
Benchmark-Lauf mit 100 simulierten Geraeten ueber 10 000 Ticks
„ohne verlorene Events und ohne nichtdeterministischen Replay-
Diff". `GG-RT-005` SOLLTE verlangt 10 000 Zeitreihenpunkte/s am
Telemetrie-Port. Beide Akzeptanzen sind heute weder gemessen noch
durch ein wiederholbares Pattern abgedeckt — grid-gym hat **keine
bestehende Bench-Substanz**:

- Kein `tests/perf/`-Verzeichnis.
- Kein `pytest-benchmark`-Dep (oder Alternativ-Bench-Tool).
- Kein `make perf`-Target.
- Kein Dockerfile-`perf`-Stage.
- Keine Baseline + Regression-Schwelle.

M6-Welle-0-D-4 hat ADR 0041 vorbelegt; M6-D-7 hat **pytest-
benchmark** als Framework-Vorbelegung gewaehlt mit der Begruendung
„existiert bereits, keine neue Dep, schneller Einstieg" — aber
die `[dependency-groups.perf]`-Substanz fehlt heute, der Dep ist
also tatsaechlich NEU.

Welle-4b ist gemaess Welle-4b-a-D-1 in **4b-a (Bench-Foundation
+ `GG-RT-004`) + 4b-b (`GG-RT-005`) + 4b-c (`GG-RT-001`
Backpressure-Healthcheck)** sub-geslict. Alle drei Sub-Wellen
brauchen ein gemeinsames Bench-Pattern; ADR 0041 verankert das
Pattern in Welle-4b-a, damit 4b-b und 4b-c additiv (ADR-0011-
Schaerfung) erweitern koennen.

Vor dieser ADR war im Repo keine kanonische Performance-Bench-
Pflicht-Strategie verankert:

- `make perf` ist NICHT im Makefile.
- `tests/perf/` ist nicht in der Test-Tree-Konvention etabliert.
- Regression-Schwelle ist nirgends dokumentiert.

Das ist eine Pattern-Lueck: ein zukuenftiger Reviewer kann nicht
aus Accepted-ADRs ableiten, welche Bench-Form ADR-konform ist
oder wie die Regression-Schwelle gepflegt wird.

---

## 2. Entscheidung

ADR 0041 fixiert sechs orthogonale Punkte:

### §2.1 Bench-Framework

**pytest-benchmark `>=4.0,<6.0`** als einziges zulaessiges Bench-
Framework fuer `make perf`. Aufloesung der M6-D-7-Vorbelegung.

Begruendung:

- Konsistenz mit pytest-Infrastruktur (Marker, Conftest,
  Fixtures, Dockerfile-Stage-Pattern).
- `GG-RT-004`/`GG-RT-005` sind Makro-Bench (10 000 Ticks bzw.
  10 000 Points/s); pyperf-Praezision ist Overkill, asv-
  Continuous-Tracking ist Tooling-Overhead ohne klaren Mehrwert.

Framework-Wechsel ist ADR-pflichtig per ADR-0011-Pattern.

### §2.2 Mess-Protokoll

Pflicht-Parameter fuer alle `tests/perf/`-Bench-Tests:

- **Mess-Statistik:** `median` (default in pytest-benchmark;
  resilienter gegen Outlier als `mean`).
- **`--benchmark-min-rounds=10`** als Mindest-Rundenzahl pro
  Bench (vier Outlier-Toleranz).
- **`--benchmark-disable-gc`** waehrend des Mess-Fensters
  (deterministische GC-Pause-Eliminierung).
- **`--benchmark-warmup=on`** (Welle-4b-a verifiziert; in
  `tests/perf/conftest.py`-Default-Marker fixiert).

Tests werden mit `pytest.mark.benchmark`-Decorator markiert oder
nutzen die `benchmark`-Fixture direkt. Jeder Bench-Test definiert
sein **Akzeptanz-Pruefen** (z. B. „100 Geraete × 10 000 Ticks
ohne verlorene Events" via `assert tick_loop.lost_events == 0`).

### §2.3 Regression-Schwelle

**20 % Median-Drift gegenueber gepinneter Baseline bricht den
Lauf.** Die Schwelle ist:

- Datei-basiert: `tests/perf/baseline.json` als versionierter
  JSON-Snapshot (pytest-benchmark-natives Format).
- Pflicht-Gate: `make perf` ruft pytest-benchmark `--benchmark-
  compare=baseline.json --benchmark-compare-fail=median:20%`;
  drift > 20 % brikt den Lauf mit EXIT≠0.
- Audit-Trail: Baseline-Updates erfordern explizite Commit-
  Messages (Pattern analog `uv.lock`-Pin-Updates; commit-
  subject-Konvention `perf: baseline update — <reason>`).

Schwellen-Anpassung (z. B. von 20 % auf 10 %) ist ADR-pflichtig
per ADR-0011-Pattern. Welle-4b-a-Erst-Anwendung pinnt 20 % als
„plausible-aber-nicht-empirisch-validierte Default-Schwelle";
spaetere Schaerfung moeglich.

### §2.4 Bench-Locations

**`tests/perf/`** als kanonisches Verzeichnis fuer alle Bench-
Tests. Begruendung:

- Bench-Tests sind weder Unit (kein Coverage-Beitrag) noch
  Integration (kein Compose-Sibling). Eigene Top-Level-Test-
  Tree-Branche.
- `coverage`-Pflicht (`make coverage-gate`/`coverage-gate-
  critical`) gilt **NICHT** fuer `tests/perf/` — bench-Tests
  sind Performance-Mess-Substanz.
- `tests/perf/baseline.json` ist als Daten-Datei in
  `tests/perf/` verankert (kein separater `data/perf/`-Pfad).

Pattern-Praezedenz: viele Python-Projekte trennen `tests/perf/`
analog (uvloop, sqlalchemy).

### §2.5 Run-Form

**Separater Dockerfile-Stage `perf` + `make perf`-Target.**
`make perf` ist NICHT Bestandteil von `make gates` (10 A-1-
Gates) oder `make ci`/`make fullbuild`. Begruendung:

- Bench-Lauf ist teuer (Welle-4b-a-C2-Verifikation: ~30-60s
  cache-frei). `make gates` muss schnell bleiben (< 90s
  lokal).
- Performance-Regression ist eine eigene Audit-Stufe — keine
  Verkoppelung mit Lint/Type/Coverage-Gates.
- CI-Workflow `perf.yml` ist NICHT Welle-4b-a-Scope; spaetere
  Welle (M6-Welle-7-Closure oder explizite Pflicht-Slice)
  entscheidet, ob CI-Hook noetig.

Dockerfile-`perf`-Stage analog `test-unit`-Stage: `uv sync
--frozen --all-groups --extra iec61850` + `uv run pytest
tests/perf/ --benchmark-only --benchmark-compare=tests/perf/
baseline.json --benchmark-compare-fail=median:20%`.

`make perf` baut die `perf`-Stage; cache-frei-Lauf erzwingt
saubere Bench-Substanz.

### §2.6 Baseline-Pinning

**`tests/perf/baseline.json`** als committed JSON-Snapshot der
Bench-Resultate. Format ist pytest-benchmark-nativ (`--benchmark-
save`/`--benchmark-compare`).

Update-Pattern:

1. Maintainer fuhrt `make perf --benchmark-save=new-baseline`
   im Dev-Host cache-frei aus.
2. Kopiert/Renamed `.benchmarks/.../new-baseline.json` zu
   `tests/perf/baseline.json`.
3. Commit-Subject `perf: baseline update — <reason>` (z. B.
   „migration auf RTL-Helper, +6 % Throughput erwartet").
4. PR-Review prueft die Begruendung; Code-Review ueber
   `tests/perf/baseline.json`-Diff-Block.

Cross-Maschinen-Vergleich ist explizit NICHT garantiert
(Maintainer-Dev-Host vs. CI-Runner). Welle-4b-a-Erst-Anwendung
pinnt nur Maintainer-Dev-Host-Baseline. CI-Hook (Welle-4b-
Closure oder M6-Welle-7-Material) muss ggf. eine eigene CI-
Baseline pflegen oder die Schwelle Maschinen-spezifisch
lockern.

---

## 3. Begruendung

- **Schwester-Pattern zu ADR 0029/0042/0043/0044.** ADR 0029
  fixiert Coverage-Gate-Vertrag (A-1-Pflicht), ADR 0042 fixiert
  SBOM/Release-Workflow-Vertrag, ADR 0043 fixiert Image-Audit-
  Vertrag, ADR 0044 schaerft ADR-0043. ADR 0041 folgt derselben
  Form fuer den `make perf`-Vertrag — Defer-Form ist explizit
  abweichend (NICHT in `make gates`/`make ci`), aber die
  Vertrag-Verankerungs-Substanz ist konsistent.
- **Sub-Slicing-Konsistenz.** Welle 4b ist in 4b-a/4b-b/4b-c
  sub-geslict; alle drei brauchen das Bench-Pattern. ADR-0041
  in Welle-4b-a verankert das Pattern fuer 4b-b und 4b-c als
  Konsumenten (Schaerfung via ADR-0011-Pattern moeglich).
- **Schaerfung ohne Supersedes (ADR 0011-Pattern als spaetere
  Option).** Welle-4b-b/4b-c koennen ADR 0041 §2.2 (Mess-
  Protokoll) und §2.3 (Regression-Schwelle) per ADR-0011-
  Schaerfung erweitern, ohne den Welle-4b-a-Vertrag zu
  brechen.
- **pytest-benchmark als praktische Vorbelegung.** M6-D-7
  hat pytest-benchmark vorbelegt; das Framework ist in der
  Python-Bench-Welt verbreitet, hat eine stabile API und
  ist mit der pytest-Infrastruktur kompatibel.

---

## 4. Reichweite

- ADR 0002 `§A-1` (10 A-1-Gates) bleibt textlich unveraendert.
  `make perf` ist KEIN A-1-Gate; explizit ausserhalb der
  Pflicht-Gate-Sammlung.
- `make gates`/`make ci`/`make fullbuild`-Aggregator-Substanz
  bleibt unveraendert in Welle-4b-a-C2.
- NEU `pyproject.toml`-`[dependency-groups.perf]`-Block mit
  pytest-benchmark; `uv.lock`-Sync. Default-`uv sync` ohne
  `--group perf` zieht es nicht (opt-in).
- NEU `Dockerfile`-`perf`-Stage analog `test-unit`-Stage.
- NEU `tests/perf/`-Layer mit `__init__.py` + `conftest.py` +
  `test_tick_loop_bench.py` + `baseline.json`.
- NEU `Makefile`-`perf`-Target (PHONY).
- ADR-Index Aktive-ADRs-Tabelle ADR-0041-Zeile.
- `tests/perf/baseline.json` ist Daten-Datei, kein Source-
  Code; `pyproject.toml`-`[tool.coverage.run].source` bleibt
  unangetastet.

---

## 5. Operative Artefakte (Erstanwendung in M6-Welle-4b-a)

Mit dieser ADR sind die folgenden Welle-4b-a-Substanz-Items
verbunden:

1. **M6-Welle-4b-a-C0** (`f2fbcc0`):
   - NEU `docs/plan/planning/in-progress/M6-welle-4b-a.md`
     (Slice-Doc-Anlage; Welle-4b-Sub-Slicing-Beschluss in
     4b-a/4b-b/4b-c per D-1; 6 Decisions fixiert).
   - `in-progress/README.md` + `M6-perf-security-cicd.md`
     §3.1 Welle-4b-Zeile in drei Sub-Sub-Wellen gespalten.

2. **M6-Welle-4b-a-C1** (dieser Commit):
   - NEU `docs/plan/adr/0041-performance-bench-pattern.md`
     (`Provisional`, dieser Text).
   - `docs/plan/adr/README.md` Aktive-ADRs-Tabelle um
     ADR-0041-Zeile ergaenzt (Pattern analog ADR 0042 +
     0043 + 0044).

3. **M6-Welle-4b-a-C2** (`<TBD>`):
   - NEU `pyproject.toml`-`[dependency-groups.perf]`-Block
     mit `pytest-benchmark>=4.0,<6.0`.
   - NEU `uv.lock`-Sync (NEU pytest-benchmark + py-cpuinfo +
     ggf. weitere Transitiv-Deps).
   - NEU `Dockerfile`-`perf`-Stage.
   - NEU `tests/perf/__init__.py` + `tests/perf/conftest.py` +
     `tests/perf/test_tick_loop_bench.py` (`GG-RT-004`-Bench)
     + `tests/perf/baseline.json` (Maintainer-Dev-Host-Lauf).
   - NEU `Makefile`-`perf`-Target.
   - Verifikation: `make perf` cache-frei gruen
     (Baseline-Compare-Schwelle 20 % Median-Drift; Bench-
     Akzeptanz `100 Geraete × 10 000 Ticks ohne verlorene
     Events`). `make gates`/`make ci`/`make fullbuild` cache-
     frei gruen ohne `CRITICAL_COV_TARGETS`-Override.

4. **M6-Welle-4b-a-C3** (`<TBD>`; Closure-Sync):
   - `M6-welle-4b-a.md` Status `In Progress → Done`.
   - `M6-perf-security-cicd.md §3.1` Welle-4b-a-Zeile auf
     `Done`; Aktive-Welle-Block auf Welle 4b-b.
   - Top-Level-Doku-Sync (`README.md`/`README.de.md` NEU
     `make perf`-Hinweis; `roadmap.md §3 M6` aktive-Welle-
     Block auf Welle 4b-b).

5. **M6-Welle-4b-b** + **M6-Welle-4b-c** (Folge-Sub-Sub-
   Wellen):
   - Koennen ADR-0041-§2.2 (Mess-Protokoll) und §2.3
     (Regression-Schwelle) per ADR-0011-Schaerfung erweitern,
     ohne den Welle-4b-a-Vertrag zu brechen.

6. **M6-Welle-7-Closure-C1** (Folge-Welle):
   - ADR 0041 `Provisional → Accepted` gebuendelt mit
     ADR 0042 + ADR 0043 + ADR 0044 (Pattern analog
     M5-Welle-7-C1 `62f988d`).

`make gates` bleibt cache-frei gruen ohne Override in C1 + C2
+ C3 (10/10 A-1-Gates; Test-Counts unveraendert 1732/80/4
skipped — Bench-Tests sind nicht im Unit-Test-Count).

---

## 6. Konsequenzen

- **Positiv:** `make perf` ist explizit als ADR-verankerter
  Pflicht-Pfad gefuehrt. Reviewer koennen aus ADR-0041 ableiten,
  welche Bench-Form zulaessig ist und wie die Regression-
  Schwelle gepflegt wird.
- **Positiv:** `GG-RT-004` SOLLTE-Akzeptanz produktiv messbar
  in Welle-4b-a-C2; 4b-b/4b-c erweitern auf `GG-RT-005`/`GG-
  RT-001` mit demselben Pattern.
- **Positiv:** opt-in-Dep-Group `[dependency-groups.perf]`
  belastet Default-Builds nicht (regular `uv sync` ohne
  `--group perf` zieht es nicht).
- **Neutral:** `make perf` ist NICHT in `make gates`/`make ci`
  — Performance-Regression bricht NICHT den A-1-Gate-Lauf.
  Bewusste Entscheidung (Bench-Lauf zu teuer fuer A-1); bei
  spaeterem Compliance-Druck ist eine ADR-Schaerfung moeglich.
- **Neutral:** Maintainer-Dev-Host-Baseline ist nicht
  Cross-Maschinen-portable. Welle-4b-a beschliesst KEINEN CI-
  Hook (M6-Welle-7-Closure entscheidet); reale Drift gegen
  CI-Runner-Bench bleibt ein offener Punkt.
- **Neutral:** 20 % Median-Schwelle ist nicht empirisch
  validiert. Welle-4b-a pinnt das als Default; spaetere
  Schaerfung per ADR-0011-Pattern moeglich.
- **Negativ:** NEU Dep zieht pytest-benchmark + py-cpuinfo +
  weitere Transitiv-Deps in `uv.lock`. Dep-Audit (`make dep-
  audit`) muss die NEU Deps gegen pip-audit pruefen.

---

## 7. Nicht Gegenstand dieser ADR

- **Wahl des Bench-Frameworks jenseits pytest-benchmark.**
  pyperf / asv waeren ADR-pflichtige Wechsel per ADR-0011-
  Schaerfung oder neuer ADR.
- **CI-Pflicht-Gate fuer `make perf`** (CI-Workflow
  `perf.yml`). Ist Welle-4b-Closure-Material oder spaeter;
  ADR 0041 verankert nur das lokale `make perf`-Pattern.
- **Continuous-Performance-Tracking** (asv-Webseite, History-
  DB, Time-Series-Plot). Bleibt out-of-scope; Baseline-Pinning
  + Manual-Update-Pattern reicht fuer den Welle-4b-a-Scope.
- **Cross-Maschinen-Bench-Vergleich.** Maintainer-Dev-Host vs.
  CI-Runner vs. Reviewer-Host koennen abweichen; ADR 0041
  pinnt nur die Maintainer-Dev-Host-Baseline. CI-Bench-
  Schwelle waere Welle-4b-Closure- oder spaeter-Material.
- **`tests/perf/`-Coverage-Pflicht.** Bench-Tests sind nicht
  Coverage-relevant; `pyproject.toml`-`[tool.coverage.run].
  source` bleibt unveraendert.
- **Backpressure-Healthcheck-Surface** (`GG-RT-001`). Ist
  Welle-4b-c-Substanz; ADR 0041 deckt das Bench-Pattern, nicht
  die TickLoop-Healthcheck-Surface.
- **Snapshot-Envelope-v2-Body-Serialisierung** (carveouts
  §2.1). Ist M5-Erbschaft; Welle-4b-a-Anti-Scope; ggf.
  Welle-4b-b/4b-c-opportunistisch.
- **Per-Geraete-Mikro-Bench.** ADR 0041 zielt auf System-
  Level-Bench (100 Geraete × 10 000 Ticks). Per-Geraete-
  Mikro-Bench (z. B. SmartMeter-Aggregation isoliert) ist
  spaeter / Welle-X-Material.
