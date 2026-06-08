# Welle 1a — M7 Zeitreihen-Persistenz (`TelemetrySinkPort`)

**Status:** In Progress — C0 (Slice-Doc-Anlage; dieser Commit).
Erstes Sub-Slice von **M7-Welle-1** (`GG-MVP-002`) per Sub-
Slicing-Beschluss D-4-Final = B (siehe
[`M7-welle-1.md`](M7-welle-1.md)). Welle 1a liefert die
produktive Telemetrie-Zeitreihen-Persistenz; Welle 1b (Replay-
Lifecycle + `replay_diff_status`-Metrik) folgt. `GG-MVP-002`
flippt erst nach 1b.

Liefer-Reihenfolge C0 → C1 (NEU ADR 0047 `Provisional`) → C2
(Code) → C3 (Status/DoD-Sync) → C4a/C4b (Self-Close-Move).

---

## 1. Context

`GG-MVP-002` (E2E-Szenario + deterministisches Replay) ist im
**partial**-Stand mit zwei gekoppelten Lücken (siehe
[`M7-welle-1.md §1`](M7-welle-1.md)):

1. **Zeitreihen-Persistenz** fuer Telemetriepunkte fehlt
   (`GG-PERSIST-001`; `RunRepositoryPort` haelt nur Laufmetadaten/
   Status) — **Welle-1a-Scope (dieses Doc)**.
2. ReplaySource-Integration + `replay_diff_status`-Lifecycle-Hook
   fehlen — **Welle-1b-Scope**.

Welle 1a schliesst Lücke 1: persistierte, append-only,
deterministisch sortierbare Telemetrie-Zeitreihen ueber einen
NEU `TelemetrySinkPort` (Driven). Damit liefert 1a zugleich die
Persistenz-Quelle, auf die 1b den `ReplaySnapshotPort`/`expected`-
Sample-Strom aufsetzt (D-1.1-Timestamp-Lücke siehe
[`M7-welle-1.md §3 D-1.1`](M7-welle-1.md)).

### 1.1 Existierende Substanz (Code-verifiziert)

- `TelemetryPoint`-Domain (`src/grid_gym/hexagon/core/domain/
  telemetry.py`, `GG-DATA-001`): Felder `run_id`, `tick`,
  `simulation_time`, `device_id`, `metric`, `value` (`Decimal`),
  `unit`, `quality` (`Quality`), `source`, `sequence`.
- `PostgresRunRepository` + Alembic-Setup
  (`adapters/driven/persistence_postgres/`, `alembic.ini`,
  `migrations/`) — produktives Postgres-Adapter-Pattern als
  Vorbild fuer den Sink-Adapter.
- Live-Telemetrie via `TelemetryStreamPort` (Driving) — bleibt
  unberuehrt; 1a ergaenzt die **Driven**-Persistenz-Seite.
- **Kein** `TelemetrySinkPort`/`telemetry_points`-Schema (grep
  bestaetigt; nur Forward-Pointer-Docstring in `_schemas.py`).

---

## 2. Lieferziel (Welle-1a-C2)

1. **NEU `TelemetrySinkPort`** (Driven-Protocol unter
   `hexagon/ports/driven/`): append-only `persist(point(s))` +
   deterministisch sortiertes Lese-API fuer den Persistenz-Smoke
   (exakte Methoden-Surface in C0-D-2 / C1-ADR).
2. **NEU `PostgresTelemetrySinkAdapter`**
   (`adapters/driven/persistence_postgres/`) + **NEU Alembic-
   `telemetry_points`-Migration** mit allen `TelemetryPoint`-/
   `GG-PERSIST-001`-Pflichtfeldern.
3. **Sink-Wiring** in den produktiven Demo-/API-Lauf (Welle-5-
   Lifespan-Pfad), sodass derselbe Lauf Zeitreihen persistiert
   (Wiring-Form = C0-D-2).
4. **NEU ADR 0047 `Provisional`** (`TelemetrySinkPort`-Zeitreihen-
   Persistenz-Pattern + Sink-Wiring-Vertrag; C1).
5. **NEU `tests/integration/test_mvp_002_timeseries_persistence_
   smoke.py`** — Boundary-Pins: stabile Sortierung bei
   gleicher `simulation_time` (Tie via `sequence`), append-only-
   Wiederholungslesen ohne Duplikate, alle `GG-PERSIST-001`-/
   `TelemetryPoint`-Felder inkl. `unit`/`source`/`sequence`,
   kanonisch-stabile Ausgabe.
6. Audit-Doku-Vorbereitung: `docs/user/replay-determinism-e2e.md`
   entsteht in **1b** (markiert `GG-MVP-002` erst nach 1b als ✓);
   1a liefert die Persistenz-Sektion als Vorlauf, falls C0 sie
   schon schneidet.

---

## 3. Architektur-Entscheidungen (Welle-1a)

### 1a-D-0 — Persistenz-Surface (aus Gruppenplan uebernommen)

**Final: NEU `TelemetrySinkPort` (Driven)** — Gruppenplan
[`M7-welle-1.md §3 D-0`](M7-welle-1.md) (Option A). **NICHT**
`RunRepositoryPort` (Laufmetadaten/Status), **NICHT** die Live-
Stream-Surface (Stream-/Persistenz-Trennung; Adapter-Purity).

### 1a-D-1 — `telemetry_points`-Schema

**Frage:** Welche Spalten + Indizes?

Vorbelegung (C1-ADR fixiert): Spalten = `TelemetryPoint`-Felder
(`run_id`, `tick`, `simulation_time`, `device_id`, `metric`,
`value`, `unit`, `quality`, `source`, `sequence`).
Deterministische Sortier-/Tie-Break-Invariante ueber
`(run_id, simulation_time, sequence)`; `value` als **`TEXT`** mit
kanonischer `str(Decimal)`-Serialisierung (ADR-0021-§2.9-Pattern,
analog `TelemetryPoint.value`-`str()`-Wrap) — **NICHT `NUMERIC`**:
dessen Scale-Normalisierung (`1.50` → `1.5`) wuerde die
byte-stabile Round-Trip-Vorbedingung fuer den 1b-Replay-Diff
brechen (siehe R2). Append-only — kein `UPDATE`/`DELETE` im
Sink-Vertrag. ADR 0047 (C1) fixiert den `TEXT`-Vertrag.

### 1a-D-2 — Sink-Wiring-Position

**Frage:** Wer ruft `TelemetrySinkPort.persist(...)`?

Optionen:
- **A** — Core-`TickLoop` emittiert direkt an einen optionalen
  `telemetry_sink`-Kwarg (analog `random`/`run_repository`-
  Injection); deterministisch, aber Core kennt dann einen
  weiteren Driven-Port.
- **B** — Adapter-Side-Tee: der `DemoTickLoopDriver` (bzw. ein
  Sink-Drain-Hook) persistiert die pro Tick emittierten
  `TelemetryPoint`s parallel zum Stream — haelt den Core frei,
  doppelt aber die Drain-Logik.

Vorbelegung: **A** (Core-Kwarg, keyword-only, `None`-default →
no-op; konsistent mit `run_repository`/`fault_port`-Pattern und
deterministisch). C1-ADR 0047 verifiziert gegen AC-PORTS-NO-OUT +
AC-ADAPTER-PURE und entscheidet final.

### 1a-D-3 — ADR-Bedarf

**Final: NEU ADR 0047 `Provisional`** (Welle-1a-C1) —
`TelemetrySinkPort`-Zeitreihen-Persistenz-Pattern + Schema +
Sink-Wiring-Vertrag. Naechste freie Nummer 0047 (letzte vergebene
`0046-multi-python-test-stage-pattern.md`). Welle 1b traegt
ADR 0048 (Replay-Lifecycle).

---

## 4. Liefer-Reihenfolge

- **C0** (dieser Commit) — Slice-Doc + Decision-Liste + DoD.
- **C1** — NEU ADR 0047 `Provisional` (Surface + Schema + Wiring).
- **C2** — Code: `TelemetrySinkPort` + `PostgresTelemetrySink
  Adapter` + Alembic-`telemetry_points`-Migration + Sink-Wiring +
  Persistenz-Smoke.
- **C3** — Status/DoD-Sync (1a `Done`; `M7-welle-1.md`-Welle-
  Tabelle 1a → Done; aktiver Slice 1b).
- **C4a/C4b** — Self-Close-Move `M7-welle-1a.md → done/` + Refs.

---

## 5. Critical Files

**NEU (C0/C1/C2):** `M7-welle-1a.md` (C0);
`docs/plan/adr/0047-…md` (C1);
`src/grid_gym/hexagon/ports/driven/telemetry_sink.py` (C2);
`src/grid_gym/adapters/driven/persistence_postgres/
telemetry_sink_repository.py` (C2);
`…/persistence_postgres/migrations/versions/0002_create_telemetry_points.py`
(C2; schlichter Sequenzname analog `0001_create_runs.py`, kein
Hash/Timestamp); `tests/integration/test_mvp_002_timeseries_
persistence_smoke.py` (C2).
**MODIFY:** Sink-Wiring im Welle-5-Lifespan-Pfad
(`_demo_scenario_setup.py`) + ggf. `TickLoop`-Kwarg (1a-D-2);
`docs/plan/adr/README.md` (C1); `M7-welle-1.md` Welle-Tabelle (C3);
**Stale-Forward-Ref-Cleanup** in
`adapters/driving/http_api/_schemas.py` (Docstring-Forward-Pointer
„TelemetrySinkPort (Welle 3)" → „M7-Welle-1a"; C2). Die analoge
`(Welle 3)`-Erwaehnung in
[`ADR 0037`](../../adr/0037-http-api-surface-pattern.md) bleibt
**unveraendert historisch** (Accepted-Immutability per ADR 0006 §3)
— kein Edit.
**UNBERUEHRT:** `RunRepositoryPort` + `TelemetryStreamPort` (Live-
Pfad), `diff_replay()`-Core (1b), `/health`/`/ready`.

---

## 6. Verifikationspfad

- `make gates` cache-frei gruen ohne Override.
- `make test-integration` (Postgres-testcontainers) gruen inkl.
  NEU Persistenz-Smoke.
- `make fullbuild` cache-frei gruen.
- `make docs-check` gruen.

---

## 7. Risiken

- **R1 Sink-Wiring vs. AC-PORTS.** 1a-D-2 Option A fuegt dem Core
  einen Driven-Port-Kwarg hinzu. Mitigation: keyword-only +
  `None`-default (no-op), Pattern exakt wie `run_repository`/
  `fault_port`; C1-ADR + `make arch-check` verifizieren.
- **R2 Decimal-Persistenz-Kanonik.** `value` muss byte-stabil
  round-trippen (1b-Replay-Diff-Vorbedingung). Mitigation:
  kanonische `str(Decimal)`-Serialisierung + Smoke-Boundary-Pin.
- **R3 Migrations-Reihenfolge.** `0002`-Migration nach dem
  bestehenden `0001_create_runs`. Mitigation: Alembic-`down_
  revision`-Kette + Integration-Test rollt `head` auf.

---

## 8. Wandert nach

Self-Close-Move `M7-welle-1a.md → done/` (C4a) + Refs-Sync (C4b)
nach 1a-C3. `M7-welle-1.md`-Gruppenplan bleibt in `in-progress/`
bis 1a+1b geschlossen sind.

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [ ] C0 — Slice-Doc §1..§9 + Decision-Liste 1a-D-0..D-3.
- [ ] C1 — NEU ADR 0047 `Provisional` (Surface + Schema + Wiring).
- [ ] C2 — `TelemetrySinkPort` + Postgres-Adapter + `telemetry_
      points`-Migration + Sink-Wiring + Persistenz-Smoke.
- [ ] C2 — Smoke pinnt Sortier-Tie, Append-only-Idempotenz, alle
      `GG-PERSIST-001`-Felder.
- [ ] **`make test-integration` cache-frei gruen** (Postgres-
      testcontainers) — fuehrt den Persistenz-Smoke als Kern-
      Evidence aus; laeuft **NICHT** in `make gates`/coverage-gate
      (das misst nur `tests/unit/`). Ohne diese Zeile haekt C3
      sonst „gruen" ab, ohne dass der Smoke je lief.
- [ ] `make gates` + `make fullbuild` + `make docs-check` gruen.
- [ ] C3 — 1a `Done`; `M7-welle-1.md` 1a → Done; aktiver Slice 1b.

**Anti-Scope (1a NICHT):** kein `ReplaySnapshotPort`, kein
Lifecycle-Hook, keine `replay_diff_status`-Metrik (alles 1b);
kein Query-/Export-API ueber den Smoke-Bedarf hinaus.

---

## References

- [`M7-welle-1.md`](M7-welle-1.md) — GG-MVP-002-Gruppenplan +
  Sub-Slicing-Beschluss + D-0..D-5.
- [`M7-mvp-completion.md`](M7-mvp-completion.md) — M7-Meilenstein-
  Slice-Plan.
- [`../open/036-safe-006-replay-diff-status-replay-source-integration.md`](../open/036-safe-006-replay-diff-status-replay-source-integration.md)
  — Trigger 036 (wird in 1b aufgeloest).
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md)
  (`GG-MVP-002`, `GG-PERSIST-001`, `GG-DATA-001`).
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — Schaerfungs-Pattern fuer ADR 0047.
