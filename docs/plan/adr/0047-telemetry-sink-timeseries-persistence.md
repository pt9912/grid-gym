# ADR 0047 — TelemetrySinkPort Zeitreihen-Persistenz (M7 Welle 1a)

**Status:** Provisional — direkter `Proposed → Provisional`-
Sprung (dieser Commit, M7-Welle-1a-C1).
**Datum:** 2026-06-08
**Status geaendert am:** 2026-06-08 — `Proposed → Provisional`.
**Bezug:**

- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — Lifecycle-/Status-Pfad.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung-
  ohne-Supersedes-Pattern (Form-Anker; ADR 0047 schaerft das
  bestehende Driven-Port-/Postgres-Persistenz-Pattern additiv,
  ohne ADR 0039 abzuloesen).
- [`ADR 0039`](0039-run-control-and-status-tracking.md) —
  `RunRepositoryPort` als Driven-Port, den der Core-`TickLoop`
  per keyword-only-Kwarg haelt + aus dem Spine aufruft
  (Wiring-Vorbild fuer den Sink).
- [`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
  §2.9 — kanonische `Decimal`-/Byte-Stabilitaets-Konvention
  (`str(Decimal)`-Wrap), Vorbild fuer die `value`-Persistenz.
- [`ADR 0015`](0015-snapshot-envelope-v2.md) — Snapshot-/
  Serialisierungs-Pattern (kanonische String-Form).
- [`M7-welle-1a.md`](../planning/done/M7-welle-1a.md) —
  Slice-Doc (Decisions 1a-D-0..D-3); ADR 0047 fixiert sie.
- [Trigger 036](../planning/open/036-safe-006-replay-diff-status-replay-source-integration.md)
  + [`M7-welle-1.md`](../planning/in-progress/M7-welle-1.md) —
  Replay-Source-Integration (Welle 1b) konsumiert die hier
  persistierten Zeitreihen; 1b-Substanz traegt ADR 0048
  (`ReplaySnapshotPort`, 1b-a) + ADR 0049 (Replay-Lifecycle,
  1b-b) per 1b-a-D-1-Sub-Slicing.

---

## 1. Kontext

`GG-MVP-002` (E2E-Szenario + deterministisches Replay) ist im
**partial**-Stand: Laufmetadaten persistiert `PostgresRunRepository`
(`GG-PERSIST-003`), aber **Telemetrie-Zeitreihen** (`GG-PERSIST-001`)
werden nicht produktiv persistiert. Die Lastenheft-Akzeptanz
(Z. 130-135) verlangt „persistiert Zeitreihen". Die
[`M7-welle-1.md`](../planning/in-progress/M7-welle-1.md)-Sub-Slicing-
Entscheidung (D-4 = B) schneidet die Zeitreihen-Persistenz als
**Welle 1a** (dieser ADR); die `ReplaySnapshotPort`-Substanz ist
**Welle 1b-a** (ADR 0048), die Lifecycle-/`replay_diff_status`-
Substanz **Welle 1b-b** (ADR 0049) per 1b-a-D-1-Sub-Slicing.

**Code-Ist-Stand (verifiziert):**

- `TelemetryPoint`-Domain (`hexagon/core/domain/telemetry.py`,
  `GG-DATA-001`): `run_id`, `tick`, `simulation_time`,
  `device_id`, `metric`, `value` (`Decimal`), `unit`, `quality`
  (`Quality`-StrEnum), `source`, `sequence`.
- Der Core-`TickLoop` produziert pro Tick eine **deterministisch
  sortierte** `TickResult.emitted_telemetry: tuple[TelemetryPoint,
  ...]` (Device-Reihenfolge × Per-Device-`sequence`).
- Der **Live-Stream** (`TelemetryStreamPort`, **Driving**) wird
  **adapter-seitig** vom `DemoTickLoopDriver._publish_emitted_
  telemetry` aus `TickResult.emitted_telemetry` gepublisht.
- Der Core-`TickLoop` haelt bereits `run_repository`
  (`RunRepositoryPort`, **Driven**, keyword-only, `None`-default)
  und ruft es aus dem Spine (Status-Mirror).
- **Kein** `TelemetrySinkPort`, kein `telemetry_points`-Schema,
  kein Sink-Adapter.

---

## 2. Entscheidung

ADR 0047 fixiert vier Punkte fuer die Welle-1a-Zeitreihen-
Persistenz.

### §2.1 `TelemetrySinkPort` (Driven-Protocol)

NEU `hexagon/ports/driven/telemetry_sink.py` mit einem
append-only-Driven-Vertrag:

```python
class TelemetrySinkPort(Protocol):
    def persist(self, points: Sequence[TelemetryPoint]) -> None: ...
    def read_ordered(self, run_id: str) -> tuple[TelemetryPoint, ...]: ...
```

- **`persist`** ist **append-only** (kein `UPDATE`/`DELETE` im
  Vertrag) und **batch** (eine `Sequence` pro Tick = die
  `TickResult.emitted_telemetry`), um Per-Tick-I/O zu amortisieren.
- **`read_ordered`** liefert alle Punkte eines Laufs in
  **Insertion-Reihenfolge** (Surrogat-`id`, §2.2), die die
  deterministische `emitted_telemetry`-Reihenfolge (Device-Major ×
  Per-Device-`sequence`) exakt reproduziert. **C2-Realization-Note:**
  `(simulation_time, sequence)` ist als Sortier-Key **NICHT
  eindeutig** — `sequence` wird per-device-per-tick vergeben (zwei
  Geraete teilen `sequence` bei gleicher `simulation_time`); nur die
  Insertion-Reihenfolge (`id`) reproduziert die Emission
  unzweideutig. Lese-Surface fuer den 1a-Persistenz-Smoke und
  (Welle 1b) den `ReplaySnapshotPort`-Sample-Strom.
- Der Port nutzt den **Core-Domain**-`TelemetryPoint`
  (`core.domain.telemetry`), **nicht** das gleichnamige
  Driving-Stream-DTO. Import von `core.domain` in einem Driven-
  Port ist AC-PORTS-NO-OUT-konform (Praezedenz: `RunRepositoryPort`
  → `core.domain.run`).

### §2.2 `telemetry_points`-Postgres-Schema

NEU Alembic-Migration `0002_create_telemetry_points.py`
(`down_revision = 0001_create_runs`). Spalten = `TelemetryPoint`-
Pflichtfelder:

| Spalte | Typ | Hinweis |
| ------ | --- | ------- |
| `id` | BIGINT IDENTITY | Surrogat-Primary-Key; aufsteigend = Insertion-Reihenfolge (C2-Realization, §2.4). |
| `run_id` | TEXT | FK-Semantik zu `runs.run_id` (kein harter FK noetig; Lauf-Scope). |
| `tick` | INTEGER | |
| `simulation_time` | BIGINT | ms ab Lauf-Start. |
| `device_id` | TEXT | |
| `metric` | TEXT | |
| `value` | **TEXT** | kanonische `str(Decimal)`-Serialisierung (siehe §2.4). |
| `unit` | TEXT | |
| `quality` | TEXT | `Quality`-StrEnum-Wert (`valid`/`stale`/…). |
| `source` | TEXT | |
| `sequence` | INTEGER | Per-Device-Tie-Break-Counter. |

- **Deterministische Sortier-Invariante (C2-Realization):**
  `read_ordered` macht `WHERE run_id = %s ORDER BY id` —
  Insertion-Reihenfolge reproduziert die Emission. Index auf
  `(run_id, id)`. `(simulation_time, sequence)` ist als Sort-Key
  verworfen, weil `sequence` per-device-per-tick und damit nicht
  global eindeutig ist (zwei Geraete teilen `sequence` bei
  gleicher `simulation_time`); ein Surrogat-`id` ist die einzige
  unzweideutige Insertion-Order-Quelle.
- **`value` ist `TEXT`, NICHT `NUMERIC`**: `NUMERIC` wuerde die
  Scale normalisieren (`1.50` → `1.5`) und die byte-stabile
  Round-Trip-Vorbedingung fuer den Welle-1b-Replay-Diff brechen.
  `str(Decimal)` bewahrt die exakte Schreibweise (§2.4).
- **Append-only:** die Migration vergibt keinen Mechanismus fuer
  `UPDATE`/`DELETE`; der Sink-Adapter macht ausschliesslich
  `INSERT`.

### §2.3 Sink-Wiring — Core-Spine (NICHT Adapter-Tee)

Der **Core-`TickLoop`** ruft `TelemetrySinkPort.persist(...)` aus
dem Spine, ueber einen NEU keyword-only-Konstruktor-Kwarg
`telemetry_sink: TelemetrySinkPort | None = None` (`None` →
No-op-Skip). Pro Tick persistiert der Spine die berechnete
`TickResult.emitted_telemetry`-Sequenz (nach der Telemetry-
Aggregation, vor/nach dem `run_repository`-Status-Mirror —
Reihenfolge in C2 fixiert).

**Begruendung (Driven vs. Driving):** Der Sink ist ein **Driven**-
Port; Driven-Ports werden per Hexagonal-Konvention **aus dem Core-
Spine** aufgerufen — exakt wie `RunRepositoryPort` (ADR 0039).
Der Adapter-seitige Live-Stream-Pfad (`DemoTickLoopDriver` →
`TelemetryStreamPort`) ist **kein** Gegenbeleg: `TelemetryStreamPort`
ist ein **Driving**-Port (Adapter pusht an Subscriber), eine
andere Kategorie. Ein Adapter-Tee fuer die **Persistenz** wuerde
die Driven-Persistenz an einen konkreten Driver
(`DemoTickLoopDriver`) koppeln — ein headless-Runner (Welle-1b-
Replay, `GG-MVP-003`-Abnahme-CLI) wuerde dann ohne den Driver
nicht persistieren. Der Core-Kwarg persistiert dagegen **jeder**
`TickLoop`-Lauf deterministisch.

**Hexagonal-Reinheit:** Der Core importiert nur das
`TelemetrySinkPort`-Protocol (kein `psycopg`); der
`PostgresTelemetrySinkAdapter` traegt die Library-Abhaengigkeit
(AC-NO-FW bleibt gewahrt, Praezedenz `run_repository`/`psycopg`).
`make arch-check` (AC-PORTS-NO-OUT + AC-NO-FW) verifiziert in C2.

### §2.4 Byte-Stabilitaets-Vertrag (`value`)

`value` wird als `str(Decimal)` persistiert und unveraendert
zurueckgelesen — keine Float-Konversion, keine Scale-
Normalisierung. Damit ist die persistierte Zeitreihe byte-stabil
gegen den Re-Run (Welle-1b-`diff_replay()`-Vorbedingung;
`GG-AR-P-008`-Determinismus + ADR 0021 §2.9). Der 1a-Persistenz-
Smoke pinnt: Round-Trip `Decimal → TEXT → Decimal` ist
verlustfrei + die `read_ordered`-Reihenfolge ist ueber den
Surrogat-`id` (Insertion-Reihenfolge) stabil — auch bei Ties
(zwei Geraete mit gleicher `simulation_time` + gleicher per-device
`sequence`), siehe §2.1/§2.2-C2-Realization.

---

## 3. Begruendung

- **`GG-PERSIST-001`-Pflicht liefern.** Die Zeitreihen-Persistenz
  ist die erste der zwei `GG-MVP-002`-Lücken; ohne sie bleibt die
  Lastenheft-Akzeptanz „persistiert Zeitreihen" offen.
- **Driven-Port-Konsistenz (ADR 0039).** Der Sink folgt exakt dem
  `RunRepositoryPort`-Pattern: Driven-Protocol + Postgres-Adapter
  via `connection_factory` + keyword-only-Core-Kwarg + `None`-no-op.
  Kein neues Architektur-Konzept.
- **Byte-Stabilitaet als 1b-Vorbedingung.** Die `TEXT`-`value`-
  Entscheidung (statt `NUMERIC`) ist nicht kosmetisch — sie ist
  die Voraussetzung fuer den deterministischen Replay-Diff in
  Welle 1b.
- **Schaerfung ohne Supersedes (ADR 0011).** ADR 0039
  (`RunRepositoryPort`) bleibt textlich unveraendert; ADR 0047
  ergaenzt einen zweiten, orthogonalen Driven-Persistenz-Port.

---

## 4. Reichweite

- NEU `hexagon/ports/driven/telemetry_sink.py` +
  `adapters/driven/persistence_postgres/telemetry_sink_repository.py`
  + Alembic-`0002_create_telemetry_points.py` (C2).
- `TickLoop.__init__` bekommt einen keyword-only-Kwarg
  `telemetry_sink` + einen Per-Tick-Persist-Step (C2);
  `build_tick_loop`-Symmetrie analog `run_repository`.
- Sink-Verdrahtung im produktiven Demo-/API-Lifespan-Pfad
  (`_demo_scenario_setup.py`, C2).
- ADR-Index Aktive-ADRs-Tabelle NEU ADR-0047-Zeile.
- **Unberuehrt:** `RunRepositoryPort` (Laufmetadaten/Status),
  `TelemetryStreamPort` (Live-Stream, Driving), ADR 0039
  (`Accepted`-Immutability). `ReplaySnapshotPort` ist **Welle
  1b-a** (ADR 0048); Lifecycle-Hook + `replay_diff_status`-Metrik
  sind **Welle 1b-b** (ADR 0049) — nicht Gegenstand von ADR 0047.

---

## 5. Lieferung

Lieferplan, Commit-Hashes + Verifikations-Gates leben in der
Slice-Doc [`M7-welle-1a.md`](../planning/done/M7-welle-1a.md)
(C2: Code-Substanz; C2-Verifikation inkl. `make test-integration`-
Persistenz-Smoke). Status-Pfad (`Proposed → Provisional →
Accepted`): siehe Status-Header; `Accepted` mit M7-Welle-X-Closure
(gebuendelt mit ADR 0048 + ADR 0049).

---

## 6. Konsequenzen

- **Positiv:** `GG-PERSIST-001`-Zeitreihen-Persistenz produktiv;
  liefert zugleich die deterministische Lese-Surface, auf die
  Welle 1b den `ReplaySnapshotPort`-Sample-Strom aufsetzt.
- **Positiv:** `TEXT`-`value` garantiert Byte-Stabilitaet → 1b-
  Replay-Diff arbeitet auf exakt persistierten Werten.
- **Neutral:** Der Core haelt einen zweiten Driven-Port-Kwarg
  (`telemetry_sink` neben `run_repository`). Hexagonal konsistent;
  `None`-default haelt bestehende Tests/Pfade no-op.
- **Neutral (Perf):** Per-Tick-Batch-`INSERT` aus dem Spine. Fuer
  Demo-/Abnahme-Lauf-Skala unkritisch; ein Batch-/Flush-Tuning
  (z. B. N-Tick-Puffer) waere eine additive ADR-0011-Schaerfung,
  falls eine spaetere Last-Welle es braucht.
- **Neutral:** `run_id` ohne harten FK auf `runs` (Lauf-Scope-
  Konvention; vermeidet Migrations-Kopplung). Ein FK waere eine
  spaetere additive Schaerfung.
- **Achtung (In-Memory-Variante):** `InMemoryTelemetrySink` (Demo-
  Pfad) ist **unbounded by design** — anders als die bounded
  Geschwister `AlarmHistoryBuffer` (`deque(maxlen)`) und
  `InMemoryTelemetryStream` (`Queue(maxsize)`). Ein Ring-Buffer
  ginge nicht, weil `read_ordered` fuer den 1b-Replay den
  **vollstaendigen** Lauf liefern muss. Konsequenz: die In-Memory-
  Variante ist Showcase-/Test-Scope (kurzlebig); ein Dauer-Demo
  akkumuliert RAM unbeschraenkt. Die disk-bounded Persistenz ist
  `PostgresTelemetrySinkAdapter`.

---

## 7. Nicht Gegenstand dieser ADR

- **`ReplaySnapshotPort` + Snapshot→`ReplaySample`-Rekonstruktion**
  (M7-welle-1.md D-1/D-1.1) — Welle 1b-a, ADR 0048.
- **Core-Spine-Lifecycle-Hook + `diff_replay()`-Aufruf +
  `replay_diff_status`-Metrik** (D-2/D-3 des Gruppenplans) —
  Welle 1b-b, ADR 0049.
- **`GG-TERM-002`/`GG-TERM-003`-Equality** — MVP-Preflight Welle
  1b-b (ADR 0049); volle Matrix Carveout Trigger 038.
- **Query-/Export-API** ueber `read_ordered` (Smoke-Bedarf)
  hinaus — eigener spaeterer Scope.
- **Batch-/Async-Flush-Tuning** — additive Schaerfung bei Last-
  Druck; 1a persistiert synchron per Tick-Batch.
- **Harter FK / Cascade-Delete `telemetry_points` → `runs`** —
  spaetere additive Schaerfung.
