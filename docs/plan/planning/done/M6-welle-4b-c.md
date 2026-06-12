# Welle 4b-c — M6 Backpressure-Healthcheck (`GG-RT-001` 10ms-Modus)

**Status:** Done 2026-06-06 — Liefer-Stack: C0 `c5543fd`
(Slice-Doc-Anlage + 6 Decisions D-1..D-6) + C0-Review-Folge
`aacc370` (7 Self-Review-Findings: F1 MEDIUM clock_source-
Pflicht + F2-F7 LOW) + C2 `a98f967` (NEU `TickLoopHealthcheck
Adapter` + Driver-Hook + `_healthcheck_router.py` Endpoint +
10 Unit-Tests + 3 Integration-Smokes; GG-RT-001-Akzeptanz
produktiv) + C2-Review-Folge `8785a6b` (7 Self-Review-Findings:
F1 MEDIUM Datei-Naming-Drift + F2-F7 LOW + try/finally-Wrap +
NEU 4 Driver-Hook-Unit-Tests) + C3 `7001989` (Status/DoD-Sync +
Welle-4-Subdivision-Komplett-Abschluss-Notiz + Top-Level-Doku)
+ C4a `7d8ac5a` (Self-Close-Move; `git mv` rename-only) + C4b
(dieser Commit; Cross-Doc-Refs-Sync nach Move + Hash-Slot-Fills
`<C3>` → `7001989` in 4 Docs + M6-perf-security-cicd-Ref
umgehakt von `in-progress` auf `../in-progress`).
Welle 4 ist gemaess Welle-4a-D-1 in 4a (Generated-Trivyignore-
Permit; abgeschlossen) + 4b (Performance-Benchmark) sub-geslict.
Welle 4b ist gemaess Welle-4b-a-D-1 weiter in 4b-a (Bench-
Foundation + `GG-RT-004`; abgeschlossen) + 4b-b (`GG-RT-005`
Telemetry-Port-Bench; abgeschlossen) + **4b-c (`GG-RT-001`
Backpressure-Healthcheck)** sub-geslict. Welle 4b-c ist die
**dritte und letzte Sub-Sub-Welle** und liefert die Tick-Dauer-
/p95-Jitter-/missed-Ticks-/Backpressure-Status-Telemetrie als
NEU Healthcheck-Surface fuer den 10ms-Tick-Modus.

**Pre-C0 abgeschlossen (M6-Welle-4b-b-Closure-Folge):**

- C4a `6145ea3` — `git mv M6-welle-4b-b.md → done/` (Self-
  Close-Move, rename-only).
- C4b `00f34ea` — Cross-Doc-Refs-Sync nach Move + Hash-Slot-
  Fills.

**Spec-Reife:** Inhaltlich final fuer Welle 4b-c. Welle-4b-c-
Decision-Liste (§3) schliesst Welle-4b-c-D-1..D-6: Healthcheck-
Architektur-Form, Wall-Clock-Mess-Mechanik, Window-Size, Metrik-
Schwellen, Healthcheck-Output-Surface, ADR-Bedarf.

---

## 1. Context

`GG-RT-001` MUSS (Lastenheft Z. 459-465):

> Die Plattform MUSS Simulationszyklen von 10 ms bis 1 s
> konfigurieren koennen.
>
> Akzeptanz: Die Demo-Konfiguration startet erfolgreich mit
> 10 ms, 100 ms und 1 s Tick-Groesse. Fuer 100 ms und 1 s Tick-
> Groesse verarbeitet die Demo 1.000 Ticks ohne Backpressure.
> Fuer 10 ms Tick-Groesse dokumentiert der Healthcheck **Tick-
> Dauer, p95-Jitter, verpasste Ticks und Backpressure-Status**;
> 10 ms ist fuer den MVP ein Mess- und Diagnosemodus, kein
> garantierter Echtzeitbetrieb.

### 1.1 Existierende Substanz (vor Welle 4b-c)

- **TickLoop in `hexagon/core/simulation/tick_loop.py`** (M1
  Welle 4) — produktiv mit `tick_ms` Konfiguration (Whitelist
  10/100/1000 ms per `GG-SIM-002`). Aktuell **keine Tick-
  Dauer-Mess-Substanz**: `tick()` ist eine Sim-Time-
  Fortschreibung ohne Wall-Clock-Mess. Backpressure-Status
  existiert nicht.
- **`/health`-Endpoint** (`adapters/driving/http_api/`) liefert
  Basis-Status (`{"status": "ok"}`); keine TickLoop-Performance-
  Metriken.
- **`ClockPort`** (`ports/driven/clock.py`) — **deterministische
  Sim-Time-Quelle**, NICHT Wall-Clock. Tick-Loop-Implementation
  ruft `clock.advance(tick_ms)` einmal pro Tick. Wall-Clock-
  Mess ist **NICHT** Teil des `ClockPort`-Vertrags.
- **`MetricsPort` + `LogPort` + `TracePort`** (ADR 0024 M3-Welle-
  5 Observability-Port-Trio) — Driven-Ports fuer Metriken/Logs/
  Traces; Null-Adapter aktiv, OTLP-Adapter optional. TickLoop
  ruft heute keine Healthcheck-spezifischen Hooks.
- **AC-NO-TIME** (Architektur-Verbot per `ADR 0002 §A-1`,
  `tools/arch_check.py`, `pyproject.toml`-Ruff-Konfig): Fachlogik
  in `hexagon/core/**` darf keine Wall-Clock-Quelle nutzen
  (`time.time`/`time.monotonic`/`time.perf_counter`/`datetime.
  now`/`datetime.utcnow` etc.). Adapter haben Erlaubnis ueber
  `per-file-ignores`-DTZ-/-TID-Ausnahmen.
- **Welle-4b-a-Bench-Foundation** (M6-Welle-4b-a; ADR-0041) —
  pytest-benchmark-Pattern; `tests/perf/` Layer; `make perf`-
  Target. Welle-4b-c nutzt das fuer einen optionalen
  Verifikations-Bench (10ms-Tick-Lauf unter Last) als
  Anti-Scope-Substanz.

### 1.2 Welle-4b-c-Lieferziel

Drei orthogonale Liefer-Items (final fixiert via Welle-4b-c-D-1):

1. **NEU `TickLoopHealthcheckAdapter`** (Welle-4b-c-C2) im
   driving-Adapter-Layer
   (`adapters/driving/http_api/_tick_loop_healthcheck.py`).
   Adapter-Side-Mess vermeidet AC-NO-TIME-Bruch im Core; nutzt
   `time.perf_counter()` per default mit per-file-DTZ-Ausnahme.
   Wrapt `TickLoop.tick()`-Aufrufe und misst Wall-Clock-Dauer;
   haelt einen Ring-Buffer der letzten N Tick-Dauern.

   **Pflicht-Clock-Injection (C0-Review-Folge-F1):** Konstruktor
   bekommt `clock_source: Callable[[], float] = time.perf_
   counter` als Default-Argument mit Test-Override-Pflicht.
   Unit-Tests injizieren Fake-Clock fuer deterministische
   Duration-Sequences; ohne Injection waeren Tests real-time-
   abhaengig (flaky).

2. **NEU HTTP-Endpoint `GET /runs/{run_id}/healthcheck`**
   (Welle-4b-c-C2) im FastAPI-API-Adapter:
   - **Output (JSON)**:
     - `tick_duration_ms_p50`: Median der jüngsten N Tick-Dauern.
     - `tick_duration_ms_p95`: 95-Perzentil-Jitter.
     - `missed_ticks_count`: Anzahl Ticks mit
       Wall-Clock-Dauer > `tick_ms`.
     - `backpressure_status`: `"ok"` wenn `missed_ticks_count
       == 0` im Window; `"delayed"` sonst.
     - `tick_ms`: Konfigurierte Tick-Groesse (Convenience-Read,
       identisch zu RunMetadata-tick_ms; vermeidet Round-Trip
       gegen `/status` fuer Consumer, nicht-kritisches Feld —
       Welle-4b-c-C0-Review-Folge-F3).
     - `window_size`: Anzahl Ticks im jüngsten Mess-Fenster.
   - Auch HTML-Variante (Optional; HTMX-konsumierbar in der UI;
     siehe Welle-4b-c-D-5).

3. **NEU Unit-Tests** (`tests/unit/adapters/driving/http_api/
   test_tick_loop_healthcheck.py`) und **NEU Integration-Smoke**
   (`tests/integration/test_m6_welle_4b_c_healthcheck_smoke.py`):
   pruefen Adapter-Side-Mess + Endpoint-Output. **Kein neuer
   Bench-Test** in `tests/perf/`; die `make perf`-Surface bleibt
   unangetastet (Welle-4b-c-D-1-Anti-Scope-Substanz).

### 1.3 Welle-4b-c-Anti-Scope

- **Keine TickLoop-Core-Aenderung** — die Healthcheck-Mess-
  Substanz lebt vollstaendig im Driving-Adapter-Layer (Welle-
  4b-c-D-1). TickLoop in Core bleibt AC-NO-TIME-konform und
  unangetastet; `tick()`-Signatur unveraendert.
- **Keine `ClockPort`-Erweiterung** — Sim-Time-Quelle bleibt
  scharf von Wall-Clock-Mess getrennt.
- **Keine NEU ADR** — Welle-4b-c-D-6 schliesst den ADR-
  Schaerfungs-Bedarf negativ aus (Adapter-Side-Mess folgt
  bestehenden Adapter-Konventionen).
- **Kein `GG-RT-001` 10ms-Modus-Bench** in `tests/perf/` —
  ein realer Last-Lauf unter 10ms ist wertvoll, aber nicht
  Welle-4b-c-Pflicht (Lastenheft sagt „10 ms ist fuer den MVP
  ein Mess- und Diagnosemodus, kein garantierter
  Echtzeitbetrieb"). Optional als Welle-4b-Closure-Material
  oder M6-Welle-7-Sweep.
- **Keine Persistenz der Healthcheck-Metriken** — Adapter-
  interner Ring-Buffer (in-memory; verloren bei Restart);
  Postgres-Persistenz waere `GG-PERSIST-005`-Material (Welle-X
  oder M3-Welle-6c-Erbschaft).
- **Kein WebSocket-Push** — Healthcheck ist Polling-orientiert
  (HTTP-GET); Live-Stream waere ADR-0038-Erweiterung (Welle-X).
- **Keine OTLP-Adapter-Erweiterung** — MetricsPort/LogPort/
  TracePort-Emission der Healthcheck-Werte ist Welle-X- oder
  M6-Welle-5-Material; Welle 4b-c nutzt nur den HTTP-Endpoint.
- **Keine Multi-Run-Aggregation** — pro Run ein eigener Ring-
  Buffer; cross-Run-Aggregate ist Welle-X-Material.

---

## 2. Scope

Welle 4b-c liefert **drei Items** ueber 3 Commits (C0..C3),
plus Self-Close-Folge C4a/C4b.

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses Dokument;
   in-progress/README.md-Bestand-Tabelle + M6-perf-security-
   cicd.md §3.1 Welle-4b-c-Zeile auf `In Progress`.
2. **C1 entfaellt** — Welle-4b-c-D-6 schliesst ADR-Schaerfungs-
   Bedarf negativ aus (Adapter-Side-Implementierung folgt
   bestehenden ADR-0024 + ADR-0037-Adapter-Konventionen ohne
   neuen Vertrag).
3. **Code-Substanz** (C2) — NEU
   `_tick_loop_healthcheck.py`-Adapter + NEU
   `GET /runs/{run_id}/healthcheck`-Endpoint + NEU Unit- und
   Integration-Tests; Lokal-Verifikation `make gates`/`make ci`/
   `make fullbuild` cache-frei gruen.
4. **Status/DoD-Sync** (C3) — `M6-welle-4b-c.md` auf `Done`;
   `M6-perf-security-cicd.md §3.1` Welle-4b-c-Zeile auf
   `Done`; Top-Level-Doku-Sync (`README.md`/`README.de.md`
   NEU `GG-RT-001`-Healthcheck-Endpoint-Hinweis; `roadmap.md
   §3 M6` aktive Welle auf M6-Welle-5 (Security-Audit)).

Self-Close-Folge C4a/C4b laufen nach C3 als M6-Welle-5-Pre-C0a/
Pre-C0b und schliessen damit **die gesamte Welle 4** (4a + 4b-
a/b/c) ab.

---

## 3. Architektur-Entscheidungen (Welle-4b-c-Decision-Liste)

### Welle-4b-c-D-1 — Healthcheck-Architektur-Form

**Frage:** Wo lebt die Wall-Clock-Mess-Substanz?

Optionen:

- **A — Driving-Adapter-Side** (
  `adapters/driving/http_api/_tick_loop_healthcheck.py`-Adapter
  wrapt TickLoop-`tick()`-Aufrufe extern; Adapter darf
  `time.perf_counter()` direkt nutzen ueber per-file-DTZ-
  Erlaubnis; Core bleibt AC-NO-TIME-konform und unangetastet).
- **B — NEU `WallClockPort` Driven-Port** (Core erhaelt
  einen NEU Port-Slot fuer Wall-Clock-Mess; TickLoop misst
  intern; AC-NO-TIME-Aussage muss per ADR geschaerft werden um
  den NEU Port-Slot zu erlauben; Welle-Substanz ist deutlich
  groesser).
- **C — Existing-MetricsPort-Hook** (TickLoop emittiert pro
  Tick `metrics.observe("tick_duration_ms", value)`; ein
  Adapter-Side-Collector aggregiert; benoetigt Core-`time.
  perf_counter()`-Zugriff = AC-NO-TIME-Bruch ohne ADR-
  Schaerfung).

**Welle-4b-c-Final: Option A (Driving-Adapter-Side).**
Begruendung:

- Minimaler Core-Touch: TickLoop unveraendert; ADR-0002
  §A-1 bleibt unangetastet.
- AC-NO-TIME-Verbot bleibt im Core verankert (kein neuer Port-
  Slot mit Wall-Clock-Surface; keine ADR-Schaerfung).
- Pattern-Praezedenz **erweitert** (C0-Review-Folge-F2):
  M5-Welle-4a `TickLoopRegistry`-Adapter + `DemoTickLoopDriver`
  (siehe ADR 0039) wrappen TickLoop-**Lifecycle** Driving-
  Side. Welle-4b-c fuegt eine **Mess-Verantwortung** dazu via
  eigene Sub-Adapter-Klasse (`TickLoopHealthcheckAdapter`),
  damit der `DemoTickLoopDriver` SRP-konform bleibt — die
  Mess-Sub-Adapter-Klasse erhaelt eine `record_tick_duration`-
  API, die der Driver pro `tick()`-Wrap aufruft.
- Mess-Latency ist akzeptabel: ein `time.perf_counter()`-Call
  pro Tick im Adapter (vor + nach `tick()`-Aufruf) ist im
  10ms-Modus 100 Hz, ergo Mess-Overhead < 1% des Tick-Budgets.

### Welle-4b-c-D-2 — Wall-Clock-Mess-Mechanik

**Frage:** Welche Wall-Clock-API im Driving-Adapter?

Optionen:

- **A — `time.perf_counter()`** (monoton, Sub-Millisekunden-
  Praezision; Python-Standard; nicht von Wall-Clock-Sprung
  beeinflusst).
- **B — `time.monotonic()`** (monoton, Millisekunden-
  Praezision).
- **C — `datetime.now(tz=UTC)`** (Wall-Clock; betrifft von
  System-Clock-Sprung; AC-NO-TIME-Bann per `datetime.utcnow`-
  banned-API).

**Welle-4b-c-Final: Option A (`time.perf_counter()`).**
Begruendung:

- Beste Praezision (Sub-Microsekunden); fuer den 10ms-Tick-
  Modus eindeutig ueberlegen.
- Monoton (immun gegen System-Clock-Adjustments; pytest-
  benchmark nutzt das aus demselben Grund).
- Steht im Adapter; per-file-DTZ-Ausnahme aus pyproject.toml
  Z.341 (`"src/grid_gym/adapters/**" = ["DTZ", "TID"]`) gilt
  bereits.

### Welle-4b-c-D-3 — Window-Size

**Frage:** Ueber wie viele juengste Ticks wird das p50/p95
gemessen?

Optionen:

- **A — Fix 100 Ticks** (10ms-Modus: 1 Sekunde Window;
  100ms-Modus: 10 Sekunden; 1000ms-Modus: 100 Sekunden).
- **B — Fix 1000 Ticks** (10ms-Modus: 10 Sekunden; 100ms-
  Modus: 100 Sekunden; 1000ms-Modus: ~17 Minuten).
- **C — Tick-ms-adaptiv** (z. B. `max(100, 5 * 1000 /
  tick_ms)` — immer ~5 Sekunden Window).

**Welle-4b-c-Final: Option A (fix 100 Ticks).** Begruendung:

- Einfach zu implementieren (collections.deque mit
  maxlen=100); keine tick_ms-Conditional-Logic.
- 10ms-Modus-Fenster von 1s ist relevant fuer
  Backpressure-Detection (ein Aussetzer wird sichtbar);
  Lastenheft-Akzeptanz ist 10ms-Modus-spezifisch.
- 100ms-/1000ms-Modus-Fenster (10s/100s) sind ausreichend fuer
  Status-Diagnose; Welle-X kann Window-Size konfigurierbar
  machen wenn noetig.

### Welle-4b-c-D-4 — Backpressure-Status-Schwelle

**Frage:** Wann ist `backpressure_status == "delayed"`?

Optionen:

- **A — Jeder einzelne verpasste Tick** (1 Tick > tick_ms im
  Window → `delayed`).
- **B — Schwellwert (z. B. 5%) verpasster Ticks** (5+ Ticks
  > tick_ms im 100er-Window → `delayed`).
- **C — Permanente Marke nach erstem Miss** (latch-Behavior;
  `delayed` bleibt bis explizit reset).

**Welle-4b-c-Final: Option A (jeder einzelne).** Begruendung:

- Lastenheft Akzeptanz „verpasste Ticks" ist binaer; jedes
  Verpassen ist ein Diagnose-Signal.
- Option B wuerde 5%-Schwelle erfordern (ADR-pflichtige
  Schaerfung); fuer den MVP-Mess-Modus zu viel Substanz.
- Option C (latch) waere unfreundlich fuer Recovery-Detection.

### Welle-4b-c-D-5 — Healthcheck-Output-Surface

**Frage:** HTTP-JSON-only oder auch HTML-Variante?

Optionen:

- **A — Nur JSON** (`Accept: application/json`-Default).
- **B — JSON + HTML-Page** (HTMX-konsumierbar; eingebettet in
  UI-Run-Detail-Seite).
- **C — JSON + HTML-Page + WebSocket-Live-Stream**
  (Live-Update-Variante).

**Welle-4b-c-Final: Option A (Nur JSON).** Begruendung:

- Minimaler Scope; HTMX-Visualisierung ist UX-Polish-Substanz
  (Welle-X / M7+).
- Pattern-Praezedenz: `GET /runs/{run_id}/status` (M5-Welle-4a
  ADR 0039) ist JSON-only; Healthcheck folgt der Form.
- WebSocket-Live-Stream wuerde ADR-0038-Erweiterung
  erfordern; out-of-scope.

### Welle-4b-c-D-6 — ADR-Schaerfungs-Bedarf

**Frage:** Erfordert Welle-4b-c eine NEU ADR oder ADR-0024-/
ADR-0037-Schaerfung?

**Welle-4b-c-Final: Nein.** Begruendung:

- ADR-0024 (Observability-Port-Trio) wird NICHT geandert; die
  Healthcheck-Substanz lebt im Adapter, nicht im Port-Layer.
- ADR-0037 (HTTP-API-Surface) Pattern fuer NEU Endpoint
  (`GET /runs/{run_id}/healthcheck`) ist additiv; folgt der
  bestehenden Run-Sub-Resource-Form (`/status`, `/control`,
  `/alarms-history`, `/devices/state`) ohne neuen Vertrag.
- AC-NO-TIME-Verbot im Core bleibt intakt; Adapter haben
  per-file-DTZ-Ausnahme. Welle-4b-c-D-1-Architekturwahl
  (Adapter-Side) vermeidet den ADR-Schaerfungs-Pfad.
- Pattern analog M5-Welle-2 `5234617` (kein C1-ADR; Decision-
  Substanz im Slice-Doc-Body verankert).

---

## 4. Liefer-Reihenfolge (3 Commits)

### Pre-C0 — bereits erledigt (M6-Welle-4b-b-Closure-Folge)

- `6145ea3` (Pre-C0a: `git mv M6-welle-4b-b.md → done/`).
- `00f34ea` (Pre-C0b: Cross-Doc-Refs-Sync nach Move +
  Hash-Slot-Fills).

### C0 — `docs(plan)`: M6-welle-4b-c Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU `M6-welle-4b-c.md` (dieses Dokument).
- `in-progress/README.md` Bestand-Tabelle um Welle-4b-c-Zeile
  + Aktive-Welle-Block auf M6-Welle-4b-c.
- `M6-perf-security-cicd.md §3.1` Welle-4b-c-Zeile `Pending
  → In Progress 2026-06-06`; Status-Block oben aktive Welle
  auf 4b-c.

### C1 entfaellt

Welle-4b-c-Decisions (D-1..D-6) sind im C0-Slice-Doc-§3-Body
fixiert; Welle-4b-c-D-6 schliesst die ADR-Schaerfungs-Frage
Negativ aus.

### C2 — `feat(perf)`: GG-RT-001 Backpressure-Healthcheck

Code-Merge mit:

- NEU `src/grid_gym/adapters/driving/http_api/_tick_loop_
  healthcheck.py`:
  - `TickLoopHealthcheckAdapter`-Klasse mit:
    - Konstruktor: `(tick_loop: TickLoop, window_size: int =
      100)`.
    - `record_tick_duration(duration_ms: float)`-Methode
      (vom Driver aufgerufen pro tick()-Wrap; Ring-Buffer
      append).
    - `healthcheck() -> dict[str, object]`-Methode (liefert
      JSON-Mapping mit allen 6 Feldern; Welle-4b-c-§1.2).
- Hooks im bestehenden `_tick_loop_driver.py` (C0-Review-Folge-
  F4: konkrete Datei-Wahl statt vorheriger Disjunktion mit
  `_demo_setup.py`) um `time.perf_counter()`-Mess pro tick()-
  Aufruf und `record_tick_duration`-Call.
- NEU `_healthcheck_router.py`-Sub-Modul mit dem `GET /runs/
  {run_id}/healthcheck`-Endpoint (C0-Review-Folge-F6 +
  C2-Review-Folge-F1-Naming-Praezisierung: separater Router
  statt `_runs_router.py`-Erweiterung; **http_api-Layer-
  Konvention** `_..._router.py` (Pattern analog
  `_runs_action_router.py` aus M5-Welle-1), NICHT
  UI-Layer-Konvention `routes_*.py`; haelt AC-NO-GOD-UTILS
  ein):
  - 200 + JSON-Body wenn Run existiert UND Healthcheck-Adapter
    aktiv.
  - 404 wenn Run nicht existiert (Pattern analog `/status`).
- NEU `tests/unit/adapters/driving/http_api/
  test_tick_loop_healthcheck.py` mit:
  - `test_healthcheck_no_recorded_ticks_returns_zero_values`.
  - `test_healthcheck_records_tick_durations`.
  - `test_healthcheck_p95_jitter_calculated_correctly`.
  - `test_healthcheck_missed_ticks_counted` (10ms-tick mit
    Duration > 10ms).
  - `test_healthcheck_backpressure_status_ok_when_no_misses`.
  - `test_healthcheck_backpressure_status_delayed_after_miss`.
  - `test_healthcheck_window_size_caps_buffer`.
- NEU `tests/integration/test_m6_welle_4b_c_healthcheck_smoke.
  py`:
  - End-to-End: Run anlegen + TickLoop registrieren + ein paar
    tick()s ausfuehren + `GET /runs/{id}/healthcheck` ruft
    200 + erwartete Felder.
- **Verifikation (lokal vor C2-Commit):**
  - `make gates` cache-frei gruen (10/10 A-1-Gates; NEU Test-
    Counts).
  - `make ci` cache-frei gruen.
  - `make fullbuild` cache-frei gruen.
  - `make docs-check` cache-frei gruen.

### C3 — `docs(plan)`: Status/DoD-Sync

**Welle-4b-c-Closure-Sync.**

- `M6-welle-4b-c.md` Status `In Progress → Done 2026-06-06`
  mit Liefer-Hash-Stack.
- `M6-perf-security-cicd.md §3.1` Welle-4b-c-Zeile `In
  Progress → Done` mit Closure-Hash + Aktive-Welle-Block auf
  Welle 5 (Security-Audit + Eingabevalidierung).
- **Top-Level-Doku-Sync:**
  - `README.md` + `README.de.md`: NEU `GG-RT-001`-Healthcheck-
    Endpoint-Hinweis (`GET /runs/{id}/healthcheck` mit
    Beispiel-Output).
  - `roadmap.md §3 M6` aktive-Welle-Block auf M6-Welle-5 +
    Welle-4b-c-Abschluss-Notiz mit Stack-Range + Welle-4-
    Subdivision-Abschluss-Notiz (4a + 4b-a/b/c komplett).

### Welle-4b-c-Closure-Folge (nach C3, Pattern Welle-4b-b)

- C4a `git mv M6-welle-4b-c.md → done/` (rename-only).
- C4b Cross-Doc-Refs-Sync nach Move + Hash-Slot-Fills.

C4a/C4b dienen gleichzeitig als M6-Welle-5-Pre-C0a/Pre-C0b
und schliessen damit die **gesamte Welle 4** (4a + 4b-a/b/c)
ab.

---

## 5. Critical Files

**Welle-4b-c-NEU (geschrieben in C0/C2):**

- `docs/plan/planning/in-progress/M6-welle-4b-c.md` (C0,
  dieser Commit).
- `src/grid_gym/adapters/driving/http_api/_tick_loop_
  healthcheck.py` (C2).
- `tests/unit/adapters/driving/http_api/
  test_tick_loop_healthcheck.py` (C2).
- `tests/integration/test_m6_welle_4b_c_healthcheck_smoke.py`
  (C2).

**Welle-4b-c-MODIFY (in C0/C2/C3):**

- `docs/plan/planning/in-progress/README.md` (C0 + C3).
- `docs/plan/planning/in-progress/M6-perf-security-cicd.md`
  (C0 + C3) — §3.1 Welle-4b-c-Zeile Status-Flip + Aktive-
  Welle-Block.
- `src/grid_gym/adapters/driving/http_api/_healthcheck_
  router.py` (C2, NEU per C0-Review-Folge-F6 + C2-Review-
  Folge-F1-Naming-Praezisierung) — NEU `GET /runs/{id}/
  healthcheck`-Route mit eigenem APIRouter; in `app.py` via
  `include_router` eingebunden (Pattern analog
  `_runs_action_router.py` aus M5-Welle-1; http_api-Layer-
  Konvention `_..._router.py`).
- `src/grid_gym/adapters/driving/http_api/_tick_loop_driver.py`
  (C2, konkret per C0-Review-Folge-F4) — `time.perf_counter()`-
  Hooks um `tick()`-Wrap; `record_tick_duration`-Call an den
  Healthcheck-Adapter.
- `src/grid_gym/adapters/driving/http_api/app.py` (C2) —
  `include_router(healthcheck_router)`-Anschluss (analog
  bestehender Router-Anschluss-Pattern via Modul-Top-Level-
  Import + include_router-Call).
- `docs/plan/planning/in-progress/roadmap.md` (C3) — §3 M6
  aktive-Welle-Block + Welle-4b-c-Abschluss-Notiz + Welle-4-
  Subdivision-Abschluss-Notiz.
- `README.md` + `README.de.md` (C3) — NEU `/healthcheck`-
  Endpoint-Hinweis.

**Welle-4b-c-UNBERUEHRT (kein Edit):**

- `src/grid_gym/hexagon/core/simulation/tick_loop.py` —
  Welle-4b-c-D-1 verankert Adapter-Side; Core unangetastet.
- `src/grid_gym/hexagon/ports/driven/clock.py` — Sim-Time-
  Port-Vertrag unveraendert.
- ADRs 0001..0044 (Welle 4b-c ohne C1-ADR; D-6 schliesst
  Schaerfungs-Bedarf negativ aus).
- `pyproject.toml`/`uv.lock`/`Dockerfile`/`Makefile`
  (Welle-4b-a/b-Substanz unangetastet; Welle 4b-c bringt
  keine neuen Deps oder Build-Stages).
- Alle GitHub-Actions-Workflows.

---

## 6. Verifikationspfad

**Welle-4b-c-Gate:**

- `make docs-check` cache-frei gruen.
- `make gates` cache-frei gruen (`tests/unit/`-Count: 1732
  → ~1739 [+7 Healthcheck-Unit-Tests]; `tests/integration/`-
  Count: 80 → 81 [+1 Welle-4b-c-Smoke]; `tests/perf/`
  unveraendert bei 2 Bench-Tests — Welle-4b-c aendert die
  Bench-Surface nicht; C0-Review-Folge-F7-Klarstellung).
- `make ci` cache-frei gruen.
- `make fullbuild` cache-frei gruen.

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur Doc-Substanz.
- C2 prueft Adapter + Endpoint + Tests + alle bestehenden
  Gates gruen.
- C3 prueft Status-Flip + Top-Level-Doku-Sync.

**Abnahme-Verifikation:**

- `GG-RT-001` MUSS-Akzeptanz produktiv via Welle-4b-c-C2:
  - 10ms/100ms/1000ms Tick-Modi konfigurierbar (bereits seit
    M1; Welle-4b-c bestaetigt DoD).
  - 100ms/1000ms-Modus verarbeitet 1000 Ticks ohne
    Backpressure (existing M3-Welle-6c-Demo-Smoke deckt das
    teilweise; Welle-4b-c-Integration-Smoke verifiziert
    explizit).
  - 10ms-Modus-Healthcheck dokumentiert Tick-Dauer, p95-
    Jitter, verpasste Ticks, Backpressure-Status (NEU in
    Welle-4b-c).

---

## 7. Risiken

**R1 — Wall-Clock-Mess-Overhead beeinflusst 10ms-Tick-Budget.**
`time.perf_counter()` ist sehr leicht (Sub-Microsekunden),
aber bei 100 Hz (10ms-Modus) wird der Mess-Overhead messbar.
**Mitigation:** `time.perf_counter()`-Aufrufe sind ~50ns auf
modernem x86; selbst bei 200ns Overhead = 0.002% des 10ms-
Tick-Budgets. Akzeptabel.

**R2 — `time.perf_counter()`-Praezisions-Drift auf
unterschiedlichen Plattformen.** Linux/macOS/Windows haben
unterschiedliche perf_counter-Aufloesungen.
**Mitigation:** GitHub-Actions-CI laeuft auf ubuntu-latest;
Maintainer-Dev-Host ist Linux. Plattform-Drift ist nicht
Welle-4b-c-Scope (Maintainer-Dev-Host-Konsistenz reicht).

**R3 — Healthcheck-Endpoint-Race-Conditions.** Der Driver
schreibt in den Ring-Buffer waehrend der Endpoint liest.
**Mitigation (C0-Review-Folge-F5-praezisiert):** Welle-4b-c-
Annahme ist **single-thread asyncio-Driver** (analog ADR-0039
`DemoTickLoopDriver` der den FastAPI-Lifespan-Event-Loop
nutzt); im asyncio-Cooperative-Modell sind `deque.append()`
und das Lesen mehrerer Elemente in `healthcheck()` atomic
zueinander, weil zwischen `await`-Punkten keine andere
Coroutine laufen kann. **Multi-Thread-Driver waere Anti-Scope-
Bruch** und braucht explizite Lock-Schutz (Welle-X-Material).
collections.deque ist `append`-atomic per CPython-Implementation
(GIL); das deckt die Backup-Sicherheit bei zukuenftigen
Multi-Thread-Drivern partiell ab, aber nicht voll fuer das
p95-Lesen — Welle-4b-c verlaesst sich auf die single-thread-
Annahme.

**R4 — Healthcheck-Endpoint kennt keine aktiven TickLoops.**
`TickLoopRegistry` muss Healthcheck-Adapter-Verbindung
exposen.
**Mitigation:** Welle-4b-c-C2 erweitert `TickLoopRegistry` um
`get_healthcheck_adapter(run_id)`-Methode (analog zu
`get(run_id)`); Pattern aus ADR 0039.

**R5 — Welle-4b-c-Window-Size-Konstante (100) wird zu klein.**
Bei 1000ms-Modus deckt 100 Ticks = 100 Sekunden — eventuell
zu wenig fuer langfristige Trend-Detection.
**Mitigation:** Welle-4b-c-D-3 Final bestaetigt 100 als
ausreichend fuer MVP; Welle-X kann tick_ms-adaptiv schaerfen.

**R6 — Welle-4-Subdivision-Komplexitaet (4 Sub-Slices).**
4a + 4b-a/b/c sind Pattern-Drift gegen M5-Welle-4 (nur
4a/4b); analog Welle-4b-a-§7 R6 + Welle-4b-b-§7 R5.
**Mitigation:** Welle-4b-c-C3 verankert Welle-4-Subdivision-
Abschluss-Notiz (analog M5-Welle-6c-Subdivision-Abschluss
2026-06-04); M6-Welle-7-Closure-Sweep traegt die Lehre.

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack**: sobald
  `M6-welle-4b-c.md` Status `Done` erreicht (am Ende von C3),
  schliesst die Welle ihre eigene Commit-Sequenz mit einem
  reinen `git mv M6-welle-4b-c.md → ../done/M6-welle-4b-c.md`
  (C4a) + Cross-Doc-Refs-Sync (C4b). Pattern analog M6-Welle-
  4b-b-C4a `6145ea3`/C4b `00f34ea`.
- C4a/C4b dienen gleichzeitig als M6-Welle-5-Pre-C0a/Pre-C0b
  UND schliessen die **gesamte Welle 4** (4a + 4b-a/b/c) ab.
- Keine NEU ADRs (Welle 4b-c ohne C1-ADR; D-6).

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **C0 — NEU `M6-welle-4b-c.md`** mit §1..§9-Struktur
  (dieser Commit).
- [x] **C0 — `in-progress/README.md`** Bestand-Tabelle
  um `M6-welle-4b-c.md`-Eintrag + Aktive-Welle-Block auf
  M6-Welle-4b-c.
- [x] **C0 — `M6-perf-security-cicd.md §3.1`** Welle-4b-c-
  Zeile `Pending → In Progress 2026-06-06`; Status-Block
  oben aktive Welle auf 4b-c.
- [x] **C1 entfaellt** — Welle-4b-c-D-6 schliesst ADR-
  Schaerfungs-Bedarf negativ aus.
- [x] **C2 — NEU `_tick_loop_healthcheck.py`** mit
  `TickLoopHealthcheckAdapter`-Klasse (Welle-4b-c-D-1 +
  D-2 + D-3 + D-4-konform); Pflicht-`clock_source:
  Callable[[], float] = time.perf_counter` (C0-Review-Folge-
  F1) im Konstruktor; Default-Argument fuer Production,
  Test-Override per Fake-Clock-Injection.
- [x] **C2 — `time.perf_counter()`-Hooks** in
  `_tick_loop_driver.py` (C0-Review-Folge-F4 konkret) um
  `tick()`-Wrap + `record_tick_duration`-Call.
- [x] **C2 — NEU `_healthcheck_router.py`-Sub-Modul** (C0-
  Review-Folge-F6) mit dem `GET /runs/{run_id}/healthcheck`-
  Endpoint (6-Feld-JSON-Output per Welle-4b-c-D-5 + §1.2);
  in `app.py` per `include_router` eingebunden.
- [x] **C2 — NEU Unit-Tests** in `tests/unit/adapters/
  driving/http_api/test_tick_loop_healthcheck.py` (≥ 7
  Tests gemaess §4-C2-Substanz-Liste).
- [x] **C2 — NEU Integration-Smoke** in `tests/integration/
  test_m6_welle_4b_c_healthcheck_smoke.py` (End-to-End:
  Run + tick + GET /healthcheck).
- [x] **C2 — `make gates`** cache-frei gruen (10/10 A-1-
  Gates; `tests/unit/`: 1732 → ~1739 [+7]; `tests/integration/`:
  80 → 81 [+1]; `tests/perf/` unveraendert bei 2 Bench-Tests
  — C0-Review-Folge-F7-Klarstellung).
- [x] **C2 — `make ci`** cache-frei gruen.
- [x] **C2 — `make fullbuild`** cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override.
- [x] **C3 — `M6-welle-4b-c.md`** Status `In Progress →
  Done 2026-06-06` mit Liefer-Hash-Stack.
- [x] **C3 — `M6-perf-security-cicd.md §3.1`** Welle-4b-c-
  Zeile `In Progress → Done` mit Closure-Hash + Aktive-
  Welle-Block auf Welle 5.
- [x] **C3 — `README.md` + `README.de.md`** NEU
  `GG-RT-001`-Healthcheck-Endpoint-Hinweis.
- [x] **C3 — `roadmap.md §3 M6`** aktive-Welle-Block auf
  M6-Welle-5 + Welle-4b-c-Abschluss-Notiz + Welle-4-
  Subdivision-Abschluss-Notiz.
- [x] **C3 — `in-progress/README.md`** Bestand-Tabelle
  Welle-4b-c-Zeile auf `Done` + Aktive-Welle-Block auf
  M6-Welle-5.
- [x] **C3 — `make docs-check`** cache-frei gruen.

**Anti-Scope-Verifikation (Welle 4b-c NICHT):**

- [x] Keine TickLoop-Core-Aenderung (Welle-4b-c-D-1).
- [x] Keine `ClockPort`-Erweiterung.
- [x] Keine NEU ADR (Welle-4b-c-D-6).
- [x] Kein `GG-RT-001` 10ms-Modus-Bench in `tests/perf/`.
- [x] Keine Persistenz der Healthcheck-Metriken.
- [x] Kein WebSocket-Push.
- [x] Keine OTLP-Adapter-Erweiterung.
- [x] Keine Multi-Run-Aggregation.

---

## References

- [`../done/M6-welle-4b-b.md`](../done/M6-welle-4b-b.md) —
  Welle-4b-b Telemetry-Port-Bench (abgeschlossen); Welle 4b-c
  ist die letzte Sub-Sub-Welle in 4b.
- [`../done/M6-welle-4b-a.md`](../done/M6-welle-4b-a.md) —
  Welle-4b-a Bench-Foundation (ADR-0041).
- [`M6-perf-security-cicd.md §3.2 Welle 4`](M6-perf-security-cicd.md)
  — M6-Slice-Plan Welle-4-Vorbelegung + Sub-Slicing-Notiz.
- [`../../../../spec/lastenheft.md §7 GG-RT-001`](../../../../spec/lastenheft.md#7-echtzeit-und-zeitmodell)
  — Lastenheft-Akzeptanz (10ms/100ms/1000ms-Tick-Modi +
  Healthcheck-Doku im 10ms-Modus).
- [`../../adr/0024-observability-port-trio.md`](../../adr/0024-observability-port-trio.md)
  — Observability-Port-Trio (Welle-4b-c nutzt das NICHT;
  Adapter-Side-Mess vermeidet ADR-Schaerfung).
- [`../../adr/0037-http-api-surface-pattern.md`](../../adr/0037-http-api-surface-pattern.md)
  — HTTP-API-Surface-Pattern (Welle-4b-c-NEU Endpoint folgt
  der bestehenden Run-Sub-Resource-Form additiv).
- [`../../adr/0039-run-control-and-status-tracking.md`](../../adr/0039-run-control-and-status-tracking.md)
  — TickLoopRegistry/DemoTickLoopDriver-Pattern (Welle-4b-c
  haengt Healthcheck-Hooks dort an).
- [`../../adr/0002-language-and-build-stack.md §A-1`](../../adr/0002-language-and-build-stack.md)
  — AC-NO-TIME-Verbot im Core (Welle-4b-c-D-1 respektiert
  das via Adapter-Side-Mess).
