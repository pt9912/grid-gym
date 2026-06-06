# Welle 4b-b — M6 Telemetry-Port-Throughput-Bench (`GG-RT-005`)

**Status:** Done 2026-06-06 — Liefer-Stack: C0 `beb5dee`
(Slice-Doc-Anlage) + C0-Review-Folge `f9620a3` (2 HIGH
Findings adressiert: D-3 No-Subscriber-False-Positive →
Single-Queue-Subscriber-Slot; D-2 canonical_json-API-Drift →
`canonical_json(mapping)` + Mapping/Decimal-Konversion) +
C0-Review-Folge-2 `935151e` (2 MEDIUM stale-Refs in §1.2 +
§4-C2) + C2 `a2feff7` (NEU `tests/perf/test_telemetry_port_
bench.py` + Baseline-Update; `GG-RT-005`-Doppel-Akzeptanz
produktiv: Payload ≤ 256 Byte UND Median ~1.27us pro publish
= ~788 000 Publish-OPS lokal, weit ueber der 10 000-SOLLTE-
Schwelle) + C3 `c8625f7` (Status/DoD-Sync + Top-Level-Doku) +
Post-C3-Review-Folge `1b77665` (7 Self-Review-Findings adressiert:
F1 HIGH ADR-0041-§2.2-Vertragsbruch — Bench-Konfig nicht
applied [betrifft auch Welle-4b-a; conftest.py pytest_configure
Hook + Baseline-Neumessung] + F2/F3 MEDIUM + F4-F7 LOW) + C4a
`6145ea3` (Self-Close-Move; `git mv` rename-only) + C4b (dieser
Commit; Cross-Doc-Refs-Sync nach Move + Hash-Slot-Fills `<C3>`
→ `c8625f7` in 4 Docs + M6-perf-security-cicd-Ref umgehakt von
`in-progress` auf `../in-progress`).

Welle 4 ist gemaess Welle-4a-D-1 in 4a (Generated-Trivyignore-
Permit; abgeschlossen) + 4b (Performance-Benchmark) sub-geslict.
Welle 4b ist gemaess Welle-4b-a-D-1 weiter in 4b-a (Bench-
Foundation + `GG-RT-004`; abgeschlossen) + **4b-b (`GG-RT-005`
Telemetry-Port-Bench)** + 4b-c (`GG-RT-001` Backpressure-
Healthcheck) sub-geslict. Welle 4b-b ist die **zweite Sub-Sub-
Welle** und liefert den Throughput-Bench am Telemetry-Port mit
`GG-RT-005`-Akzeptanz (≥ 10 000 Zeitreihenpunkte/s; Payloads
≤ 256 Byte).

**Pre-C0 abgeschlossen (M6-Welle-4b-a-Closure-Folge):**

- C4a `beb3401` — `git mv M6-welle-4b-a.md → done/` (Self-
  Close-Move, rename-only).
- C4b `17ad4fa` — Cross-Doc-Refs-Sync nach Move + Hash-Slot-Fills.

**Spec-Reife:** Inhaltlich final fuer Welle 4b-b. Welle-4b-b-
Decision-Liste (§3) schliesst Welle-4b-b-D-1..D-5: Mess-Punkt,
Payload-Form, Subscriber-Konsumtion, ADR-0041-Schaerfungs-
Bedarf, Bench-Datei-Layout.

---

## 1. Context

`GG-RT-005` SOLLTE (Lastenheft Z. 491): „Die Plattform SOLLTE
mindestens 10 000 Zeitreihenpunkte/s in der Referenzumgebung
verarbeiten koennen. Gemessen wird am Telemetrie-Port mit
Payloads bis 256 Byte je Punkt; Persistenz darf gepuffert
erfolgen."

### 1.1 Existierende Substanz (vor Welle 4b-b)

- **`TelemetryStreamPort`-Driving-Port** (ADR 0038, M5-Welle-3
  `82bdf39`) unter `src/grid_gym/hexagon/ports/driving/
  telemetry_stream.py`:
  - `publish(point: TelemetryPoint) -> None` (synchron;
    Producer-Pfad).
  - `subscribe(run_id) -> AsyncIterator[TelemetryPoint]`
    (asynchron; Konsumer-Pfad).
  - `subscriber_count -> int` (Test- + Observability-Sicht).
- **`InMemoryTelemetryStream`-Adapter** (M5-Welle-3 `82bdf39`)
  unter `src/grid_gym/adapters/driven/telemetry_stream_inmemory/`:
  - Bounded `asyncio.Queue(maxsize=128)` mit Drop-Oldest-
    Backpressure (ADR 0038 §2.2).
  - Per-Subscriber-Queue; Multi-Subscriber-Form.
- **`TelemetryPoint`-Domain-Type** (M5-Welle-3 `82bdf39`)
  unter `src/grid_gym/hexagon/ports/driving/telemetry_stream.
  py`: 8 Felder (`run_id`/`device_id`/`metric`/`value`/`unit`/
  `simulation_time_ms`/`quality`/`sequence`).
- **`canonical_json`-Serialization** (M2-Welle-0a) — kanonische
  Byte-Mess-Form fuer Payload-Groesse (`spec/lastenheft.md
  §GG-RT-005`-Schwelle).
- **Welle-4b-a Bench-Foundation** (M6-Welle-4b-a; ADR-0041):
  pytest-benchmark als opt-in-Extra; Dockerfile-`perf`-Stage;
  `tests/perf/`-Layer mit `baseline.json`-Pinning; `make perf`
  + `make perf-baseline-update`-Targets. **Welle 4b-b nutzt
  diese Foundation 1:1** ohne strukturelle Erweiterung.
- **Keine bestehende Telemetry-Bench-Substanz**: kein
  `tests/perf/test_telemetry_port_bench.py`; kein Baseline-
  Eintrag fuer Telemetry-Throughput.

### 1.2 Welle-4b-b-Lieferziel

Drei orthogonale Liefer-Items:

1. **NEU `tests/perf/test_telemetry_port_bench.py`** (Welle-4b-
   b-C2) — `test_gg_rt_005_telemetry_port_publish_throughput`
   misst `TelemetryStreamPort.publish()`-Rate gegen
   `InMemoryTelemetryStream`. **Doppel-Akzeptanz** per
   `GG-RT-005`-Spec (Z.491-495):
   - **Payload-Schwelle**: jeder TelemetryPoint kanonisch
     serialisiert ≤ 256 Byte (Assert vor dem Bench-Lauf via
     lokalen Helper `_canonical_point_payload(point) ->
     bytes`, der `dataclasses.asdict(point)` plus `value:
     float → Decimal(repr(value))`-Konversion macht und
     dann `canonical_json(mapping)` ruft — siehe §3 Welle-
     4b-b-D-2 fuer den API-Realitaet-Block).
   - **Throughput-Schwelle**: Bench misst Publish-OPS; PASS
     wenn die Median-OPS ≥ 10 000 (Akzeptanz-Assertion im
     Test selbst, NICHT in der Baseline-Compare-Schwelle —
     Baseline-Compare bleibt ADR-0041 §2.3 20 %-Median-Drift,
     plus die harte Lastenheft-Schwelle als getrennter
     Assert).
2. **NEU Baseline-Eintrag** in `tests/perf/baseline.json`
   (Welle-4b-b-C2) — erzeugt via `make perf-baseline-update`
   nach Test-Implementation; Maintainer-Dev-Host-Mess.
3. **C0/C3 Doc-Substanz** (Welle-4b-b-C0 + C3) — Slice-Doc +
   Status/DoD-Sync; M6-perf-security-cicd.md §3.1-Welle-4b-b-
   Zeile + Top-Level-Doku.

### 1.3 Welle-4b-b-Anti-Scope

- **Kein WebSocket-Endpoint-Bench** — der WS-Konsum-Pfad
  (`WS /runs/{run_id}/telemetry`) ist Adapter-Schicht; Welle-
  4b-b misst nur den Port-Inlet (`publish`).
- **Keine ADR-0041-Schaerfung** — Welle-4b-b-D-4 Final: das
  bestehende Pattern reicht (`make perf` baut den Dockerfile-
  `perf`-Stage, der jetzt zwei Bench-Tests laeuft statt einen;
  keine Mess-Protokoll-Aenderung noetig).
- **Keine TickLoop-Integration** — der Test publisht
  TelemetryPoints direkt, nicht ueber TickLoop+Devices. Das
  isoliert die Mess-Surface auf `TelemetryStreamPort.publish`.
- **Kein Multi-Subscriber-Bench** — Welle-4b-b misst Single-
  Subscriber-Drain-Pfad (default `InMemoryTelemetryStream`-
  Bedienform). Multi-Subscriber-Skalierung ist Welle-X/Welle-
  4b-Closure-Material.
- **Keine Persistenz-Mess** — Lastenheft sagt explizit
  „Persistenz darf gepuffert erfolgen"; Persistenz-Pfad
  (`PostgresAlarmRepository`-aequivalent fuer Telemetry) ist
  NICHT Welle-4b-b-Scope.
- **Kein `GG-RT-001` Backpressure-Healthcheck** — Welle-4b-c-
  Scope (Tick-Dauer/p95-Jitter/missed-Ticks-Telemetrie).
- **Keine 256-Byte-Payload-Validierung im Produktiv-Code** —
  Welle-4b-b prueft die Payload-Schwelle als Bench-Test-
  Assertion (nicht als runtime-Check im Adapter). Eine
  produktive Payload-Schwellen-Pflege ware ADR-pflichtige
  Erweiterung.

---

## 2. Scope

Welle 4b-b liefert **drei Items** ueber 3 Commits (C0..C3),
plus Self-Close-Folge C4a/C4b.

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses Dokument;
   in-progress/README.md-Bestand-Tabelle + M6-perf-security-
   cicd.md §3.1 Welle-4b-b-Zeile auf `In Progress`.
2. **C1 entfaellt** — keine ADR-Substanz; Welle-4b-b-D-4
   Final: ADR-0041 reicht ohne Schaerfung. Pattern analog
   M5-Welle-2 `5234617` (Slice-Doc-Body verankert die
   Welle-Decisions).
3. **Code-Substanz** (C2) — NEU `tests/perf/
   test_telemetry_port_bench.py` mit `test_gg_rt_005_
   telemetry_port_publish_throughput` (Doppel-Akzeptanz:
   Payload ≤ 256 Byte UND Median-OPS ≥ 10 000); NEU
   Baseline-Eintrag in `tests/perf/baseline.json`. Lokal-
   Verifikation `make perf` cache-frei gruen.
4. **Status/DoD-Sync** (C3) — `M6-welle-4b-b.md` auf `Done`;
   `M6-perf-security-cicd.md §3.1` Welle-4b-b-Zeile auf
   `Done`; Top-Level-Doku-Sync (`README.md`/`README.de.md`
   NEU `GG-RT-005`-Akzeptanz-Notiz im `make perf`-Block;
   `roadmap.md §3 M6` aktive Welle auf M6-Welle-4b-c).

Self-Close-Folge C4a/C4b laufen nach C3 als M6-Welle-4b-c-
Pre-C0a/Pre-C0b.

---

## 3. Architektur-Entscheidungen (Welle-4b-b-Decision-Liste)

### Welle-4b-b-D-1 — Mess-Punkt

**Frage:** Wo wird der Telemetry-Throughput gemessen?

Optionen:

- **A — `TelemetryStreamPort.publish()`-Inlet** (Producer-
  Pfad).
- **B — `TelemetryStreamPort.subscribe()`-Drain** (Konsumer-
  Pfad; AsyncIterator-Throughput).
- **C — End-to-End** (`publish` → `subscribe` Roundtrip mit
  echtem `asyncio.Queue`-Pump).

**Welle-4b-b-Final: Option A (`publish`-Inlet).** Begruendung:

- Lastenheft Z.494: „Gemessen wird am Telemetrie-Port mit
  Payloads bis 256 Byte je Punkt" — der „Telemetrie-Port" ist
  semantisch der `TelemetryStreamPort.publish()`-Inlet
  (Producer-Surface; ADR 0038 §2.1).
- Option B mischt Konsumer-Bottleneck (asyncio-Loop-Sched)
  in die Mess-Substanz; Welle-4b-b-Anti-Scope verbietet
  Multi-Subscriber-Substanz.
- Option C (End-to-End) ist Roundtrip-Mess; misst nicht den
  reinen Producer-Pfad. Persistenz ist explizit gepuffert
  zulaessig — Roundtrip ist `GG-RT-005`-irrelevant.

### Welle-4b-b-D-2 — Payload-Form

**Frage:** Wie wird die ≤ 256-Byte-Payload-Schwelle gemessen?

Optionen:

- **A — `canonical_json(asdict_mit_decimal)`-Byte-Mess**
  (kanonische Serialization-Form; M2-Welle-0a-Vertrag).
- **B — `pickle`-Byte-Mess** (Python-spezifisch).
- **C — Field-by-Field-Byte-Sum** (manuelle Berechnung).

**Welle-4b-b-Final: Option A (`canonical_json`).** Begruendung:

- Lastenheft sagt „Payloads bis 256 Byte" ohne Format-
  Spezifikation; aber grid-gym-kanonisches Serialization-
  Format ist `canonical_json` (ADR 0007, M2-Welle-0a Trigger
  014). Reviewer koennen aus dieser Form auf Payload-
  Schwelle schliessen.
- Option B (pickle) waere Python-spezifisch; nicht audit-
  belastbar.
- Option C (manuelle Berechnung) bricht die Adapter-
  Boundary; Payload-Format-Drift wuerde Mess-Drift verursachen.

**API-Realitaet** (Welle-4b-b-C0-Review-Folge-Schaerfung;
gegen `src/grid_gym/hexagon/core/serialization/canonical.py
:125` verifiziert):

- Die canonical-Form ist **`canonical_json(value) -> bytes`**,
  NICHT `canonical_json.dumps(...)`.
- Der Encoder lehnt **`float`** explizit ab (`FloatNotAllowed
  Error`) und akzeptiert keine **Dataclasses**.
- `TelemetryPoint` hat `value: float` und ist eine
  `@dataclass(frozen=True, slots=True)`.

**Pflicht-Konversion** vor der Mess: `dataclasses.asdict
(point)` + `value: float → Decimal(repr(value))`-Replacement
(Pattern analog `_to_canonical_mapping` in
`hexagon/core/devices/_telemetry.py`-aequivalent — Welle-4b-b-
C2 prueft die Existenz vor und schreibt sonst lokalen
Konversion-Helper im Bench-Test-File). Der serialisierte
Bytes-Length-Mess passiert dann ueber das Mapping, nicht
ueber das frozen Dataclass.

### Welle-4b-b-D-3 — Subscriber-Konsumtion

**Frage:** Mit oder ohne aktiven Subscriber bei der Mess?

Optionen:

- **A — Ohne Subscriber** (Drop-Oldest greift nicht; Queue
  bleibt leer; pure `publish`-Throughput).
- **B — Mit Single-Queue-Subscriber-Slot ohne asyncio-Loop**
  (Queue programmatisch im `_subscribers`-List angemeldet,
  niemand drained; publish-Pfad faehrt ueber Drop-Oldest-Logik
  voll).
- **C — Mit aktivem asyncio-Subscriber-Drainer** (Subscriber-
  Loop konsumiert die Queue parallel; voller End-to-End-
  Throughput).

**Welle-4b-b-Final: Option B (Single-Queue-Subscriber-Slot).**

**Korrektur gegenueber C0-Erstwurf:** der C0-Erstwurf hatte
Option A („Ohne Subscriber") gewaehlt — Code-Review hat
aufgedeckt, dass `InMemoryTelemetryStream.publish()` bei
`subscriber_count == 0` eine **leere Schleife** macht (siehe
`src/grid_gym/adapters/driven/telemetry_stream_inmemory/
stream.py:39-44`); kein Queue-Write, kein Drop-Oldest. Das
waere ein false-positive-Bench (10 000 OPS via No-Op). Die
korrigierte Form misst den realen publish-Pfad.

Begruendung Option B:

- Mess-Surface bleibt scharf am `publish`-Inlet (Welle-4b-b-
  D-1) UND der publish-Pfad fuehrt jetzt **echte Arbeit aus**:
  `subscriber.full()`-Check, `get_nowait()`-Drop-Oldest,
  `put_nowait()`-Queue-Schreibe.
- Option A ist nach Code-Review verworfen (false-positive-
  Risiko HIGH).
- Option C mischt asyncio-Scheduling in den Mess-Pfad und
  bricht ADR-0038 §2.2 implizit (Drainer als Race-
  Bedingung); nicht reproduzierbar genug.
- Implementierungs-Pflicht (C2): die Bench-Test-Implementation
  haengt eine `asyncio.Queue(maxsize=128)` programmatisch
  direkt in `stream._subscribers` ein (umgeht den `async def
  subscribe()`-Pfad bewusst, weil der asyncio-Kontext braucht).
  Die Queue wird nie gedrained — Drop-Oldest greift ab dem
  129. Publish (realistic worst-case-Path).

### Welle-4b-b-D-4 — ADR-0041-Schaerfungs-Bedarf

**Frage:** Erfordert Welle-4b-b eine ADR-0041-Schaerfung per
ADR-0011?

**Welle-4b-b-Final: Nein.** Begruendung:

- ADR-0041 §2.1 (pytest-benchmark) + §2.2 (Mess-Protokoll) +
  §2.3 (Regression-Schwelle) + §2.4 (Locations) + §2.5 (Run-
  Form) + §2.6 (Baseline-Pinning) decken Welle-4b-b ohne
  Aenderung.
- Welle-4b-b fuegt nur einen weiteren Test in `tests/perf/`
  hinzu; `make perf` ruft pytest-benchmark gegen alle Tests
  unter `tests/perf/` ohne Test-spezifische Anpassung.
- Lastenheft-Akzeptanz `GG-RT-005` (10 000 OPS-Schwelle) ist
  Test-spezifisch und in der Bench-Test-Datei als Assert
  verankert; nicht in ADR-0041-§2-Vertrag noetig.

### Welle-4b-b-D-5 — Bench-Datei-Layout

**Frage:** Eine Datei mit beiden Bench-Tests (`test_tick_
loop_bench.py` + Telemetry-Bench) oder getrennte Dateien?

Optionen:

- **A — Getrennte Dateien** (`test_telemetry_port_bench.py`
  separat von `test_tick_loop_bench.py`).
- **B — Eine Datei** (Telemetry-Bench in `test_tick_loop_
  bench.py` hinzugefuegt).

**Welle-4b-b-Final: Option A (Getrennte Dateien).**
Begruendung:

- Subject-Separation: TickLoop-Bench misst TickLoop-Tick-
  Overhead; Telemetry-Bench misst Port-Throughput. Zwei
  unterschiedliche Mess-Subjects → zwei Dateien.
- Vorbild: M5-Welle-3 hat `test_telemetry_stream.py` und
  `test_tick_loop_subscribe.py` analog getrennt.
- Bench-Resultate in `baseline.json` werden per Test-Name
  unterschieden — Datei-Trennung ist Lese-bequem fuer den
  Maintainer-Update-Pfad.

---

## 4. Liefer-Reihenfolge (3 Commits)

### Pre-C0 — bereits erledigt (M6-Welle-4b-a-Closure-Folge)

- `beb3401` (Pre-C0a: `git mv M6-welle-4b-a.md → done/`).
- `17ad4fa` (Pre-C0b: Cross-Doc-Refs-Sync nach Move +
  Hash-Slot-Fills).

### C0 — `docs(plan)`: M6-welle-4b-b Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU `M6-welle-4b-b.md` (dieses Dokument).
- `in-progress/README.md` Bestand-Tabelle um Welle-4b-b-Zeile
  + Aktive-Welle-Block auf M6-Welle-4b-b.
- `M6-perf-security-cicd.md §3.1` Welle-4b-b-Zeile `Pending
  → In Progress 2026-06-06`; Status-Block oben aktive Welle
  auf 4b-b.

### C1 entfaellt

Welle-4b-b-Decisions (D-1..D-5) sind im C0-Slice-Doc-§3-Body
fixiert; Welle-4b-b-D-4 schliesst die ADR-0041-Schaerfungs-
Frage Negativ aus. Pattern analog M5-Welle-2 `5234617` (kein
C1-ADR; Decision-Substanz im Slice-Doc-Body verankert).

### C2 — `feat(perf)`: GG-RT-005 Telemetry-Port-Bench

Code-Merge mit:

- NEU `tests/perf/test_telemetry_port_bench.py`:
  - `test_gg_rt_005_telemetry_port_publish_throughput`
    (pytest-benchmark; misst `InMemoryTelemetryStream.
    publish(point)`-Rate mit Single-Queue-Subscriber-Slot
    per Welle-4b-b-D-3 — Setup haengt `asyncio.Queue(maxsize
    =128)` programmatisch in `stream._subscribers` ein, damit
    `publish` realen Queue-Manipulation-Pfad faehrt; Drop-
    Oldest greift ab dem 129. Publish).
  - Doppel-Akzeptanz per `GG-RT-005`-Spec:
    - Vor dem Bench-Lauf: jeder TelemetryPoint kanonisch
      ≤ 256 Byte via Helper-Konversion
      `_canonical_point_payload(point) -> bytes`:
      konvertiert `point` per `dataclasses.asdict()`, ersetzt
      `value: float → Decimal(repr(value))` (Pflicht weil
      `canonical_json` `float` ablehnt; Welle-4b-b-D-2-
      Substanz), ruft `canonical_json(mapping)` und assertet
      `len(result) <= 256`.
    - Setup: `asyncio.Queue(maxsize=128)` programmatisch in
      `stream._subscribers` einhaengen (Welle-4b-b-D-3-
      Substanz; bypasst den `async def subscribe()`-Pfad).
    - Nach dem Bench-Lauf: Median-OPS ≥ 10 000
      (`assert benchmark.stats["median"] <= 1e-4` —
      1e-4 Sekunden pro Publish ≈ 10 000 OPS).
- Baseline-Update `tests/perf/baseline.json` via `make perf-
  baseline-update`; committed mit Hash-Anchor.
- **Verifikation (lokal vor C2-Commit):**
  - `make perf` cache-frei gruen (`GG-RT-005`-Akzeptanz; OPS
    ≥ 10 000 Median; Baseline-Compare innerhalb 20 % Drift).
  - `make gates` cache-frei gruen (10/10 A-1-Gates; Test-
    Counts unveraendert; `tests/perf/` ist nicht im
    Default-Path).
  - `make ci` cache-frei gruen.
  - `make fullbuild` cache-frei gruen.
  - `make docs-check` cache-frei gruen.

### C3 — `docs(plan)`: Status/DoD-Sync

**Welle-4b-b-Closure-Sync.**

- `M6-welle-4b-b.md` Status `In Progress → Done 2026-06-06`
  mit Liefer-Hash-Stack.
- `M6-perf-security-cicd.md §3.1` Welle-4b-b-Zeile `In
  Progress → Done` mit Closure-Hash + Aktive-Welle-Block auf
  M6-Welle-4b-c.
- **Top-Level-Doku-Sync:**
  - `README.md` + `README.de.md`: `make perf`-Block-
    Erweiterung um `GG-RT-005`-Akzeptanz-Notiz (10 000
    Points/s + ≤ 256 Byte).
  - `roadmap.md §3 M6` aktive-Welle-Block auf M6-Welle-4b-c
    + Welle-4b-b-Abschluss-Notiz mit Stack-Range.

### Welle-4b-b-Closure-Folge (nach C3, Pattern Welle-4b-a)

- C4a `git mv M6-welle-4b-b.md → done/` (rename-only).
- C4b Cross-Doc-Refs-Sync nach Move + Hash-Slot-Fills.

C4a/C4b dienen gleichzeitig als M6-Welle-4b-c-Pre-C0a/Pre-C0b.

---

## 5. Critical Files

**Welle-4b-b-NEU (geschrieben in C0/C2):**

- `docs/plan/planning/in-progress/M6-welle-4b-b.md` (C0,
  dieser Commit).
- `tests/perf/test_telemetry_port_bench.py` (C2).

**Welle-4b-b-MODIFY (in C0/C2/C3):**

- `docs/plan/planning/in-progress/README.md` (C0 + C3).
- `docs/plan/planning/in-progress/M6-perf-security-cicd.md`
  (C0 + C3) — §3.1 Welle-4b-b-Zeile Status-Flip + Aktive-
  Welle-Block.
- `tests/perf/baseline.json` (C2) — NEU Eintrag fuer
  `test_gg_rt_005_telemetry_port_publish_throughput`.
- `docs/plan/planning/in-progress/roadmap.md` (C3) — §3 M6
  aktive-Welle-Block + Welle-4b-b-Abschluss-Notiz.
- `README.md` + `README.de.md` (C3) — NEU `GG-RT-005`-
  Akzeptanz-Notiz im `make perf`-Block.

**Welle-4b-b-UNBERUEHRT (kein Edit):**

- Aller Code unter `src/grid_gym/` (Welle 4b-b ist Bench-
  Test-Substanz; kein Python-Produktiv-Code-Pfad-Wechsel).
- ADRs 0001..0044 (Welle 4b-b ohne C1-ADR; Welle-4b-b-D-4
  schliesst ADR-0041-Schaerfungs-Bedarf negativ aus).
- `pyproject.toml`/`uv.lock`/`Dockerfile`/`Makefile` (Welle-
  4b-a-Substanz unangetastet; Welle 4b-b nutzt das bestehende
  Pattern 1:1).
- Alle GitHub-Actions-Workflows.

---

## 6. Verifikationspfad

**Welle-4b-b-Gate:**

- `make docs-check` cache-frei gruen.
- `make gates` cache-frei gruen.
- `make ci` cache-frei gruen.
- `make fullbuild` cache-frei gruen.
- `make perf` cache-frei gruen (jetzt zwei Tests: TickLoop-
  Bench + Telemetry-Port-Bench; beide gegen Baseline-Compare
  20 % Median-Drift; plus Test-eigene Akzeptanz-Asserts).

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur Doc-Substanz.
- C2 prueft Telemetry-Bench-Test + Baseline-Update + alle
  bestehenden Gates gruen.
- C3 prueft Status-Flip + Top-Level-Doku-Sync.

**Abnahme-Verifikation:**

- `GG-RT-005` SOLLTE-Akzeptanz produktiv via Welle-4b-b-C2:
  10 000 Zeitreihenpunkte/s am Telemetry-Port mit Payloads
  ≤ 256 Byte gemessen + assertiert.

---

## 7. Risiken

**R1 — `InMemoryTelemetryStream`-publish-leere-Schleife.**
Bei `subscriber_count == 0` ist `publish()` eine leere
Schleife (kein Queue-Write, kein Drop-Oldest); ein „Ohne
Subscriber"-Bench wuerde 10 000 OPS via No-Op erfuellen,
ohne den Port-Vertrag echt zu verarbeiten. Das ist der
C0-Erstwurf-False-Positive-Risiko (aufgedeckt in Welle-4b-
b-C0-Review-Folge).
**Mitigation:** Welle-4b-b-D-3 Final ist nach Code-Review
auf Option B (Single-Queue-Subscriber-Slot) gewechselt; die
Bench-Test-Setup haengt eine Queue programmatisch in
`stream._subscribers` ein, damit `publish` realen Queue-
Manipulation-Pfad faehrt. Limitation: Single-Subscriber-
Profil; Multi-Subscriber-Skalierung ist Welle-X/Welle-4b-
Closure-Material.

**R2 — 10 000 OPS-Schwelle haerter als Maintainer-Dev-Host-
Realitaet.** Welle-4b-a-Bench (519ms pro Lauf = 1.92 OPS) zeigt,
dass der Host-Performance-Stand das ggf. nicht trifft.
**Mitigation:** Welle-4b-b-C2 misst den Bench lokal vor Commit;
falls 10 000 OPS nicht erreicht werden, ist das ein Welle-
Substanz-Befund (Real-Optimierungs-Bedarf am
`InMemoryTelemetryStream`). Dann waere die Welle-Substanz
Code-Pfad-Aenderung statt nur Bench-Test.

**R3 — TelemetryPoint-Serialization-Groesse-Drift.** Felder-
Werte (`run_id`, `device_id`, `metric`, `value`-float-precision)
beeinflussen die canonical_json-Byte-Groesse signifikant. Ein
Lauf mit langem `run_id` koennte > 256 Byte sein.
**Mitigation:** Welle-4b-b-C2-Test pinnt knappe Default-Werte
(`run_id="run-bench"`, `device_id="dev-001"`, `metric="power"`,
etc.) + verifiziert die ≤ 256-Byte-Schwelle vor dem Bench-
Lauf (Assert in Test-Body).

**R4 — Baseline-Eintrag Cross-Maschinen-Drift.** Wie bei
Welle-4b-a-`GG-RT-004`-Baseline: Maintainer-Dev-Host vs.
CI-Runner divergieren.
**Mitigation:** ADR-0041 §2.6 verankert das schon; keine
Welle-4b-b-spezifische Mitigation noetig.

**R5 — Welle-4b-b-Sub-Sub-Slicing-Tiefe.** 4 Sub-Slices in
Welle 4 (4a + 4b-a + 4b-b + 4b-c) sind Pattern-Drift; siehe
Welle-4b-a §7 R6.
**Mitigation:** Welle-4b-a-D-1 verankert den Beschluss
inhaltlich; in M6-Welle-7-Closure-Sweep wird der Pattern-Drift
als Lehre verankert.

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack**: sobald
  `M6-welle-4b-b.md` Status `Done` erreicht (am Ende von C3),
  schliesst die Welle ihre eigene Commit-Sequenz mit einem
  reinen `git mv M6-welle-4b-b.md → ../done/M6-welle-4b-b.md`
  (C4a) + Cross-Doc-Refs-Sync (C4b). Pattern analog M6-Welle-
  4b-a-C4a `beb3401`/C4b `17ad4fa`.
- C4a/C4b dienen gleichzeitig als M6-Welle-4b-c-Pre-C0a/
  Pre-C0b.
- Keine NEU ADRs (Welle 4b-b ohne C1-ADR).

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **C0 — NEU `M6-welle-4b-b.md`** mit §1..§9-Struktur
  (dieser Commit).
- [x] **C0 — `in-progress/README.md`** Bestand-Tabelle
  um `M6-welle-4b-b.md`-Eintrag + Aktive-Welle-Block auf
  M6-Welle-4b-b.
- [x] **C0 — `M6-perf-security-cicd.md §3.1`** Welle-4b-b-
  Zeile `Pending → In Progress 2026-06-06`; Status-Block
  oben aktive Welle auf 4b-b.
- [x] **C1 entfaellt** — Welle-4b-b-D-4 schliesst ADR-0041-
  Schaerfungs-Bedarf negativ aus; Pattern analog M5-Welle-2
  `5234617`.
- [x] **C2 — NEU `tests/perf/test_telemetry_port_bench.py`**
  mit `test_gg_rt_005_telemetry_port_publish_throughput`
  (Doppel-Akzeptanz: Payload ≤ 256 Byte UND Median-OPS ≥
  10 000).
- [x] **C2 — Baseline-Update** `tests/perf/baseline.json`
  via `make perf-baseline-update` (NEU Eintrag fuer den
  Telemetry-Test).
- [x] **C2 — `make perf`** cache-frei gruen (beide Tests;
  `GG-RT-005`-Akzeptanz: Median-OPS ≥ 10 000; Baseline-
  Compare innerhalb 20 % Median-Drift).
- [x] **C2 — `make gates`** cache-frei gruen (10/10 A-1-
  Gates; Test-Counts unveraendert).
- [x] **C2 — `make ci`** cache-frei gruen.
- [x] **C2 — `make fullbuild`** cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override.
- [x] **C3 — `M6-welle-4b-b.md`** Status `In Progress →
  Done 2026-06-06` mit Liefer-Hash-Stack.
- [x] **C3 — `M6-perf-security-cicd.md §3.1`** Welle-4b-b-
  Zeile `In Progress → Done` mit Closure-Hash + Aktive-
  Welle-Block auf Welle 4b-c.
- [x] **C3 — `README.md` + `README.de.md`** NEU
  `GG-RT-005`-Akzeptanz-Notiz im `make perf`-Block.
- [x] **C3 — `roadmap.md §3 M6`** aktive-Welle-Block auf
  M6-Welle-4b-c + Welle-4b-b-Abschluss-Notiz mit Stack-Range.
- [x] **C3 — `in-progress/README.md`** Bestand-Tabelle
  Welle-4b-b-Zeile auf `Done` + Aktive-Welle-Block auf
  M6-Welle-4b-c.
- [x] **C3 — `make docs-check`** cache-frei gruen.

**Anti-Scope-Verifikation (Welle 4b-b NICHT):**

- [x] Kein WebSocket-Endpoint-Bench (Adapter-Schicht; Welle-
  Closure-Material).
- [x] Keine ADR-0041-Schaerfung (Welle-4b-b-D-4).
- [x] Keine TickLoop-Integration (Mess-Surface isoliert).
- [x] Kein Multi-Subscriber-Bench (Welle-4b-Closure-Scope).
- [x] Keine Persistenz-Mess (Lastenheft: gepuffert
  zulaessig).
- [x] Kein `GG-RT-001` Backpressure-Healthcheck (Welle-4b-c-
  Scope).
- [x] Keine produktive 256-Byte-Payload-Schwellen-Schaerfung
  (Bench-Test-Assert only).

---

## References

- [`../done/M6-welle-4b-a.md`](../done/M6-welle-4b-a.md) —
  Welle-4b-a Bench-Foundation (pytest-benchmark + Dockerfile-
  Stage + tests/perf/ Layer + Makefile-Targets); Welle 4b-b
  nutzt die Foundation 1:1.
- [`../done/M6-welle-0.md §3 M6-D-7`](../done/M6-welle-0.md)
  — pytest-benchmark-Vorbelegung (in Welle-4b-a-C1 final
  aufgeloest).
- [`M6-perf-security-cicd.md §3.2 Welle 4`](../in-progress/M6-perf-security-cicd.md)
  — M6-Slice-Plan Welle-4-Vorbelegung + Sub-Slicing-Notiz.
- [`../../../../spec/lastenheft.md §7 GG-RT-005`](../../../../spec/lastenheft.md)
  — Lastenheft-Akzeptanz (10 000 Points/s + ≤ 256 Byte).
- [`../../adr/0041-performance-bench-pattern.md`](../../adr/0041-performance-bench-pattern.md)
  — Bench-Pattern-Vertrag (Welle-4b-b nutzt das ohne
  Schaerfung; Welle-4b-b-D-4).
- [`../../adr/0038-telemetry-stream-port.md`](../../adr/0038-telemetry-stream-port.md)
  — TelemetryStreamPort-Vertrag (`publish`/`subscribe`/
  `subscriber_count`; Welle-4b-b misst `publish`-Pfad).
- pytest-benchmark Doku: https://pytest-benchmark.readthedocs.io/
