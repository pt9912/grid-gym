# ADR 0041 — Performance-Bench-Pattern + Regression-Schwelle (M6 Welle 4b-a)

**Status:** Provisional — direkter `Proposed → Provisional`-
Sprung (dieser Commit).
**Datum:** 2026-06-06
**Status geaendert am:** 2026-06-06 — `Proposed → Provisional`.
**Bezug:**

- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — Lifecycle- und Supersedes-Pflichten, auf denen die
  Schaerfungs-ohne-Supersedes-Form aufbaut.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) —
  Schaerfung-ohne-Supersedes-Pattern (Pfad fuer spaetere
  Schaerfung von §2.2/§2.3).
- [`ADR 0029`](0029-no-coverage-pragma-contract.md) —
  Schwester-Pattern (Coverage-Gate-Vertrag); ADR 0041 folgt
  derselben Form fuer den NICHT-A-1-Gate `make perf`.
- [`ADR 0035`](0035-iec61850-adapter-profile.md) — Vorbild
  fuer Optional-Extra-Pattern (`iec61850`-Extra); ADR 0041
  uebernimmt dieselbe Form fuer den `perf`-Extra.

---

## 1. Kontext

[`GG-RT-004`](../../../spec/lastenheft.md#gg-rt-004) SOLLTE
verlangt einen Benchmark-Lauf mit 100 simulierten Geraeten ueber
10 000 Ticks „ohne verlorene Events und ohne
nichtdeterministischen Replay-Diff". Daneben gibt es weitere
Lastenheft-Akzeptanzen mit Bench-Charakter (z. B.
[`GG-RT-005`](../../../spec/lastenheft.md#gg-rt-005) SOLLTE
„10 000 Zeitreihenpunkte/s am Telemetrie-Port"), die auf
demselben Pattern aufsetzen koennen. Vor dieser ADR ist
`GG-RT-004` weder gemessen noch durch ein wiederholbares Pattern
abgedeckt — grid-gym hat **keine bestehende Bench-Substanz**:

- Kein `tests/perf/`-Verzeichnis.
- Kein `pytest-benchmark`-Dep (oder Alternativ-Bench-Tool).
- Kein `make perf`-Target.
- Kein Dockerfile-`perf`-Stage.
- Keine Baseline + Regression-Schwelle.

ADR 0041 verankert das Bench-Pattern als Foundation. Weitere
Bench-Tests (System-Throughput, Port-Durchsatz, etc.) koennen
additiv im selben `tests/perf/`-Layer und ueber dieselbe
Baseline-/Compare-Mechanik liegen — bei substanziellen
Erweiterungen am Mess-Protokoll oder an der Regression-Schwelle
per ADR-0011-Schaerfung.

Das ist eine Pattern-Luecke: ein zukuenftiger Reviewer kann nicht
aus Accepted-ADRs ableiten, welche Bench-Form ADR-konform ist
oder wie die Regression-Schwelle gepflegt wird.

---

## 2. Entscheidung

ADR 0041 fixiert sechs orthogonale Punkte:

### §2.1 Bench-Framework

**pytest-benchmark `>=4.0,<6.0`** als einziges zulaessiges Bench-
Framework fuer `make perf`. Aufloesung der M6-D-7-Vorbelegung.

Mechanik der Pflicht-Substanz:

- `pyproject.toml` `[project.optional-dependencies.perf]`-
  Eintrag (Pattern analog `iec61850`-Extra aus
  [ADR 0035](0035-iec61850-adapter-profile.md)):
  `perf = ["pytest-benchmark>=4.0,<6.0"]`. Der Default-
  `uv sync --all-groups`-Lauf im Dockerfile zieht das
  **NICHT**; nur ein expliziter `--extra perf`-Aufruf
  installiert pytest-benchmark.
- `[dependency-groups.perf]` waere NICHT opt-in-konform —
  `uv sync --all-groups` zieht alle dependency-groups
  produktiv, was die `make perf`-Substanz in alle Pflicht-
  Gate-Stages laden wuerde (Lint/Test/Coverage/etc.). Das
  ist explizit verboten — Bench-Dep darf weder `make gates`
  brechen koennen noch `make dep-audit` durch unerwartete
  Audits belasten.

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
- **`--benchmark-warmup=on`** (in `tests/perf/conftest.py`-
  Default-Marker fixiert).

Tests werden mit `pytest.mark.benchmark`-Decorator markiert oder
nutzen die `benchmark`-Fixture direkt. Jeder Bench-Test definiert
sein **Akzeptanz-Pruefen** (z. B. fuer `GG-RT-004`: „100 Geraete
× 10 000 Ticks ohne verlorene Events **UND** ohne
nichtdeterministischen Replay-Diff" via zwei Assert-Pflichten:
(a) Lost-Event-Counter == 0 nach dem Lauf und (b) Replay-
Determinismus-Vergleich (Snapshot-Gleichheit ueber zwei Runs
mit identischem Seed).

**Pflicht-Akzeptanz `GG-RT-004` produktiv** (Lastenheft Z. 486):
zwei Klassen-Asserts pro Bench-Test, der `GG-RT-004` adressiert.
Ein Bench-Test, der nur Throughput misst ohne den Replay-Diff zu
verifizieren, erfuellt die Lastenheft-Akzeptanz **NICHT** —
ADR-0041-konform ist nur die Doppel-Klasse.

### §2.3 Regression-Schwelle

**20 % Median-Drift gegenueber gepinneter Baseline bricht den
Lauf.** Die Schwelle ist:

- Datei-basiert: `tests/perf/baseline.json` als versionierter
  JSON-Snapshot (pytest-benchmark-natives Format).
- Pflicht-Gate: `make perf` ruft pytest-benchmark mit
  `--benchmark-compare=tests/perf/baseline.json --benchmark-
  compare-fail=median:20%` (Pfad ab Repo-Root); drift > 20 %
  bricht den Lauf mit EXIT≠0.
- Audit-Trail: Baseline-Updates erfordern explizite Commit-
  Messages (Pattern analog `uv.lock`-Pin-Updates; commit-
  subject-Konvention `perf: baseline update — <reason>`).

Schwellen-Anpassung (z. B. von 20 % auf 10 %) ist ADR-pflichtig
per ADR-0011-Pattern. Die 20 %-Default-Schwelle ist als
„plausibel, nicht empirisch validiert" gewaehlt; spaetere
Schaerfung ist moeglich.

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

- Bench-Lauf ist teuer (in der Groessenordnung von ~30-60s
  cache-frei). `make gates` muss schnell bleiben (< 90s
  lokal).
- Performance-Regression ist eine eigene Audit-Stufe — keine
  Verkoppelung mit Lint/Type/Coverage-Gates.
- Ein CI-Workflow `perf.yml` ist nicht Bestandteil dieser
  ADR; eine spaetere ADR (separate Schaerfung oder
  eigenstaendige ADR) kann entscheiden, ob ein CI-Hook
  noetig ist.

Dockerfile-`perf`-Stage analog `test-unit`-Stage, aber mit
**zusaetzlichem `--extra perf`-Flag** im `uv sync`-Aufruf
(Pflicht-Substanz fuer §2.1-Opt-In; ohne Flag ist pytest-
benchmark nicht installiert):

```dockerfile
FROM deps AS perf
# Pflicht: --extra perf zieht pytest-benchmark; weitere Extras
# (z. B. --extra iec61850) folgen der Dockerfile-Konvention.
RUN uv sync --frozen --all-groups --extra perf
COPY tests/perf/ tests/perf/
RUN uv run pytest tests/perf/ --benchmark-only \
    --benchmark-compare=tests/perf/baseline.json \
    --benchmark-compare-fail=median:20%
```

`make perf` baut die `perf`-Stage; cache-frei-Lauf erzwingt
saubere Bench-Substanz.

### §2.6 Baseline-Pinning

**`tests/perf/baseline.json`** als committed JSON-Snapshot der
Bench-Resultate. Format ist pytest-benchmark-nativ (`--benchmark-
save`/`--benchmark-compare`).

Update-Pattern (Pflicht-Substanz; `make perf-baseline-
update`-Helper-Target liefert den sicheren Pfad):

1. Maintainer fuehrt `make perf-baseline-update` im Dev-Host
   cache-frei aus. Das Target wrappt den Docker-Run mit dem
   `--benchmark-save=baseline`-Flag und kopiert das
   resultierende Snapshot per Bind-Mount nach
   `tests/perf/baseline.json` (Pattern analog dem Bind-Mount-
   Run von `make render-trivyignore`). **Nicht** direkt
   `make perf --benchmark-save=...` aufrufen — GNU Make
   interpretiert `--benchmark-save=...` als Make-Option und
   bricht mit `unrecognized option`.
2. Maintainer prueft das `tests/perf/baseline.json`-Diff
   und commitet mit Commit-Subject `perf: baseline update —
   <reason>` (z. B. „migration auf RTL-Helper, +6 %
   Throughput erwartet").
3. PR-Review prueft die Begruendung; Code-Review ueber
   `tests/perf/baseline.json`-Diff-Block.

Cross-Maschinen-Vergleich ist explizit NICHT garantiert
(Maintainer-Dev-Host vs. CI-Runner). Die Baseline pinnt nur
den Maintainer-Dev-Host. Ein CI-Hook (separate ADR oder
Folge-Slice) muss ggf. eine eigene CI-Baseline pflegen oder
die Schwelle Maschinen-spezifisch lockern.

---

## 3. Begruendung

- **Schwester-Pattern zu ADR 0029/0042/0043/0044.** ADR 0029
  fixiert Coverage-Gate-Vertrag (A-1-Pflicht), ADR 0042 fixiert
  SBOM/Release-Workflow-Vertrag, ADR 0043 fixiert Image-Audit-
  Vertrag, ADR 0044 schaerft ADR-0043. ADR 0041 folgt derselben
  Form fuer den `make perf`-Vertrag — Defer-Form ist explizit
  abweichend (NICHT in `make gates`/`make ci`), aber die
  Vertrag-Verankerungs-Substanz ist konsistent.
- **Erweiterungs-Surface fuer weitere Bench-Tests.** Zukuenftige
  System-/Throughput-Benchmarks koennen additiv im selben
  `tests/perf/`-Layer liegen und dieselbe Baseline-/Compare-
  Mechanik nutzen, ohne diese ADR zu brechen; substanzielle
  Schaerfungen am Mess-Protokoll oder an der Regression-
  Schwelle laufen ueber ADR-0011-Schaerfungs-ADRs.
- **Schaerfung ohne Supersedes (ADR 0011-Pattern als spaetere
  Option).** §2.2 (Mess-Protokoll) und §2.3 (Regression-
  Schwelle) koennen per ADR-0011-Schaerfung erweitert werden,
  ohne den Foundation-Vertrag zu brechen.
- **pytest-benchmark als praktische Wahl.** Das Framework
  ist in der Python-Bench-Welt verbreitet, hat eine stabile
  API und ist mit der pytest-Infrastruktur (Marker, Conftest,
  Fixtures, Dockerfile-Stage-Pattern) kompatibel.

---

## 4. Reichweite

- [ADR 0002](0002-language-and-build-stack.md) `§A-1`
  (10 A-1-Gates) bleibt textlich unveraendert. `make perf`
  ist KEIN A-1-Gate; explizit ausserhalb der Pflicht-Gate-
  Sammlung.
- `make gates`/`make ci`/`make fullbuild`-Aggregator-Substanz
  bleibt unveraendert.
- NEU `pyproject.toml`-`[project.optional-dependencies.perf]`-
  Block mit pytest-benchmark (Pattern analog `iec61850`-Extra
  aus [ADR 0035](0035-iec61850-adapter-profile.md));
  `uv.lock`-Sync. Default-`uv sync --all-groups` zieht es
  **NICHT** (opt-in via `--extra perf`).
  `[dependency-groups.perf]` waere NICHT opt-in-konform und
  ist explizit verboten.
- NEU `Dockerfile`-`perf`-Stage analog `test-unit`-Stage
  mit zusaetzlichem `--extra perf`-Flag im `uv sync`-Aufruf.
- NEU `tests/perf/`-Layer mit `__init__.py` + `conftest.py` +
  `test_tick_loop_bench.py` + `baseline.json`.
- NEU `Makefile`-`perf`-Target (PHONY).
- ADR-Index Aktive-ADRs-Tabelle ADR-0041-Zeile.
- `tests/perf/baseline.json` ist Daten-Datei, kein Source-
  Code; `pyproject.toml`-`[tool.coverage.run].source` bleibt
  unangetastet.

---

## 5. Lieferung

Lieferplan, Commit-Hashes und Verifikations-Gates fuer die
Erst-Anwendung der §2-Substanz leben in der zugehoerigen
Slice-Doc
[`M6-welle-4b-a.md`](../planning/done/M6-welle-4b-a.md).
Dort sind die NEU-Files (`pyproject.toml`-Perf-Extra,
`Dockerfile`-`perf`-Stage, `tests/perf/`-Layer,
`Makefile`-`perf`- und `perf-baseline-update`-Targets) mit
Commit-Hash dokumentiert. Status-Pfad (`Proposed →
Provisional → Accepted`): siehe Status-Header dieser ADR.

---

## 6. Konsequenzen

- **Positiv:** `make perf` ist explizit als ADR-verankerter
  Pflicht-Pfad gefuehrt. Reviewer koennen aus ADR-0041 ableiten,
  welche Bench-Form zulaessig ist und wie die Regression-
  Schwelle gepflegt wird.
- **Positiv:** `GG-RT-004` SOLLTE-Akzeptanz wird produktiv
  messbar; weitere Lastenheft-Akzeptanzen mit Bench-Charakter
  koennen auf demselben Pattern andocken (substanzielle
  Protokoll- oder Schwellen-Aenderungen per ADR-0011-
  Schaerfung).
- **Positiv:** opt-in-Extra `[project.optional-dependencies.
  perf]` belastet Default-Builds nicht (Default-`uv sync
  --all-groups` ohne `--extra perf` zieht es nicht; Pattern
  analog `iec61850`-Extra; `make dep-audit` bleibt Bench-
  Dep-frei).
- **Neutral:** `make perf` ist NICHT in `make gates`/`make ci`
  — Performance-Regression bricht NICHT den A-1-Gate-Lauf.
  Bewusste Entscheidung (Bench-Lauf zu teuer fuer A-1); bei
  spaeterem Compliance-Druck ist eine ADR-Schaerfung moeglich.
- **Neutral:** Maintainer-Dev-Host-Baseline ist nicht Cross-
  Maschinen-portable. Diese ADR beschliesst keinen CI-Hook;
  reale Drift gegen CI-Runner-Bench bleibt ein offener Punkt.
- **Neutral:** 20 % Median-Schwelle ist nicht empirisch
  validiert. Pinnt das als Default; spaetere Schaerfung per
  ADR-0011-Pattern moeglich.
- **Negativ:** NEU Dep zieht pytest-benchmark + py-cpuinfo +
  weitere Transitiv-Deps in `uv.lock`. Dep-Audit (`make dep-
  audit`) muss die NEU Deps gegen pip-audit pruefen.

---

## 7. Nicht Gegenstand dieser ADR

- **Wahl des Bench-Frameworks jenseits pytest-benchmark.**
  pyperf / asv waeren ADR-pflichtige Wechsel per ADR-0011-
  Schaerfung oder neuer ADR.
- **CI-Pflicht-Gate fuer `make perf`** (CI-Workflow
  `perf.yml`). Out-of-scope dieser ADR; sie verankert nur
  das lokale `make perf`-Pattern.
- **Continuous-Performance-Tracking** (asv-Webseite, History-
  DB, Time-Series-Plot). Out-of-scope; Baseline-Pinning +
  Manual-Update-Pattern reicht fuer die Foundation.
- **Cross-Maschinen-Bench-Vergleich.** Maintainer-Dev-Host vs.
  CI-Runner vs. Reviewer-Host koennen abweichen; ADR 0041
  pinnt nur die Maintainer-Dev-Host-Baseline. CI-Bench-
  Schwelle waere Schaerfungs-Material einer Folge-ADR.
- **`tests/perf/`-Coverage-Pflicht.** Bench-Tests sind nicht
  Coverage-relevant; `pyproject.toml`-`[tool.coverage.run].
  source` bleibt unveraendert.
- **Backpressure-Healthcheck-Surface** (`GG-RT-001`).
  Out-of-scope dieser ADR; sie deckt das Bench-Pattern,
  nicht die TickLoop-Healthcheck-Surface.
- **Snapshot-Envelope-v2-Body-Serialisierung** (carveouts).
  Orthogonale Substanz; out-of-scope dieser ADR.
- **Per-Geraete-Mikro-Bench.** ADR 0041 zielt auf System-
  Level-Bench (100 Geraete × 10 000 Ticks). Per-Geraete-
  Mikro-Bench (z. B. SmartMeter-Aggregation isoliert) ist
  Schaerfungs- oder Folge-Material.
