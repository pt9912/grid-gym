# Welle 1b-a — M7 Replay-Snapshot-Rekonstruktion (`ReplaySnapshotPort`)

**Status:** Done — C0 `58203f1` (Slice-Doc + Decision-Liste
1b-a-D-0..D-6 + DoD + Sub-Slicing-Beschluss 1b → 1b-a/1b-b +
`GG-TERM-002/003`-Equality-Scope-Korrektur am Gruppenplan + NEU
[Trigger 038](../open/038-gg-term-002-003-full-equality-matrix.md))
+ C1 `fb965c6` (NEU ADR 0048 `Provisional` — `ReplaySnapshotPort`-
Rekonstruktions-Pattern + 0047-Drift-Sync) + C2 `2b755d6` (Code:
`ReplaySnapshotPort` + `PostgresReplaySnapshotAdapter` + 8
Rekonstruktions-Smokes; **keine** neue Migration, kein Core-Change)
+ C3 (DoD §9 abgehakt; 1b-a → `Done`; `M7-welle-1.md` 1b-a → Done;
aktiver Slice → 1b-b). **Offen: C4a/C4b** (Self-Close-Move
`M7-welle-1b-a.md → done/` + Refs-Sync). Code + alle Gates
(`gates`/`test-integration`/`fullbuild`/`docs-check`) cache-frei
gruen 2026-06-09 — `make test-integration` 128 passed / 7 skipped
(8 neue Replay-Snapshot-Smokes inkl.).

Zweites Sub-Slice von **M7-Welle-1** (`GG-MVP-002`); erstes
Sub-Sub-Slice von **Welle 1b** per 1b-a-D-1 (Sub-Slicing-Beschluss,
Pattern analog [Welle-4b-a-D-1](M6-welle-4b-a.md)). 1b-a
liefert die **Persistenz-Lese-Substanz**: einen Driven
`ReplaySnapshotPort`, der aus den in **Welle 1a** persistierten
`telemetry_points` deterministisch geordnete `ReplaySample`-
Sequenzen rekonstruiert. **Kein Core-Change** in 1b-a (reiner
Driven-Adapter auf bestehender Domain). `GG-MVP-002` flippt erst
nach **1b-b** (TickLoop-Terminal-Hook + `replay_diff_status`-
Metrik + `GG-TERM-002/003`-Preflight + E2E-Audit-Doku).

Liefer-Reihenfolge C0 → C1 (NEU ADR 0048 `Provisional`) → C2
(Code) → C3 (Status/DoD-Sync) → C4a/C4b (Self-Close-Move).

---

## 1. Context

`GG-MVP-002` (E2E-Szenario + deterministisches Replay) ist im
**partial**-Stand (siehe [`M7-welle-1.md §1`](M7-welle-1.md)).
Welle **1a** hat Lücke 1 geschlossen — produktive Zeitreihen-
Persistenz ueber `TelemetrySinkPort` (Done 2026-06-09,
[`M7-welle-1a.md`](M7-welle-1a.md), ADR 0047). Offen
bleibt Lücke 2: die **End-to-End-Replay-Verkabelung** —
`diff_replay()` ist produktiv (Welle-5c-Audit), aber es fehlt
(a) eine Persistenz-Quelle, die `ReplaySample`-Sequenzen aus dem
persistierten Lauf liefert, und (b) ein Lauf-Lifecycle-Hook, der
`diff_replay()` aufruft + den `replay_diff_status` emittiert.

**Welle 1b ist per 1b-a-D-1 sub-sliced:**

- **1b-a (dieses Doc)** — NEU `ReplaySnapshotPort` (Driven) +
  Postgres-Adapter, der `ReplaySample`-Sequenzen aus den
  `telemetry_points` (1a) rekonstruiert. Reiner Lese-/Mapping-
  Layer; **kein** Core-Change. ADR 0048.
- **1b-b** — NEU TickLoop-Terminal-Hook im Core-Spine +
  `replay_diff_status`-Metrik (binaer) + `GG-TERM-002/003`-
  MVP-E2E-Replay-Preflight + `docs/user/replay-determinism-e2e.md`-
  Audit-Doku + `GG-MVP-002`-Flip. ADR 0049.

1b-a liefert die Lese-Surface, auf die der 1b-b-Terminal-Hook die
`expected`/`actual`-`ReplaySample`-Stroeme aufsetzt (die in
[`M7-welle-1.md §3 D-1.1`](M7-welle-1.md) markierte Timestamp-
Lücke wird hier final aufgeloest — 1b-a-D-3).

### 1.1 Existierende Substanz (Code-verifiziert)

- **`ReplaySample`-Domain** (`src/grid_gym/hexagon/core/domain/
  replay.py:31-52`, `GG-REPLAY-001/002/003`): Frozen-Dataclass,
  Felder `timestamp` (`str`, Original-Zeitstempel „unveraendert
  gespeichert" `GG-REPLAY-002`), `simulation_time` (`int`),
  `device_id`, `metric`, `value` (`Decimal`), `unit`,
  `import_sequence` (`int`, Tie-Break-Counter `GG-REPLAY-003`).
- **`diff_replay()`** (`hexagon/core/replay/diff.py:63-160`,
  `GG-REPLAY-007` ✓ produktiv): konsumiert
  `Iterable[ReplaySample]` `expected`/`actual`, keyword-only
  `tick_ms: int = 1000`, `volatile_fields: frozenset[str] | None`
  (Default `frozenset({"import_sequence"})`); liefert
  `tuple[ReplayDelta, ...]` (`ReplayDelta`: `path`, `expected`,
  `actual`, `tick`, `device_id`, `classification`
  `fachlich`/`volatil`). `tick = expected.simulation_time //
  tick_ms`.
- **`TelemetrySinkPort`** (1a; `hexagon/ports/driven/
  telemetry_sink.py:35-62`): `persist(Sequence[TelemetryPoint])`
  + `read_ordered(run_id) -> tuple[TelemetryPoint, ...]`
  (Insertion-Reihenfolge via `ORDER BY id`). Postgres-Adapter
  `adapters/driven/persistence_postgres/
  telemetry_sink_repository.py`; `value` als `TEXT` mit
  kanonischem `str(Decimal)` (ADR 0047 §2.4).
- **`TelemetryPoint`** (`core/domain/telemetry.py`,
  `GG-PERSIST-001`): `run_id`, `tick`, `simulation_time`,
  `device_id`, `metric`, `value` (`Decimal`), `unit`, `quality`,
  `source`, `sequence`. **Fuehrt KEINEN Original-`timestamp`-
  String** — das ist die D-1.1-Lücke (siehe 1b-a-D-3).
- **Kein** `ReplaySourcePort`/`ReplaySnapshotPort` (grep
  bestaetigt). Nur Forward-Pointer-Docstring in ADR 0047 §2.1
  („… (Welle 1b) den `ReplaySnapshotPort`-Sample-Strom").
  `SnapshotPort` (`GG-AR-PORT-DRV-005`, **Driving**, ADR 0015) ist
  die Envelope-Snapshot-Surface — **nicht** die Persistenz-Quelle
  (Schichten-Twist, siehe 1b-a-D-2).
- **Alembic-Head** `0002_create_telemetry_points`
  (`down_revision = 0001_create_runs`). 1b-a fuegt **keine**
  Migration hinzu (1b-a-D-4).

---

## 2. Lieferziel (Welle-1b-a-C2)

1. **NEU `ReplaySnapshotPort`** (Driven-Protocol unter
   `hexagon/ports/driven/replay_snapshot.py`): read-only API, das
   fuer eine `run_id` eine deterministisch geordnete
   `tuple[ReplaySample, ...]` rekonstruiert. Exakte Surface =
   1b-a-D-2.
2. **NEU `PostgresReplaySnapshotAdapter`**
   (`adapters/driven/persistence_postgres/
   replay_snapshot_repository.py`): liest `telemetry_points`
   (1a) und mappt `TelemetryPoint` → `ReplaySample` mit
   kanonischer Timestamp- + `import_sequence`-Rekonstruktion
   (1b-a-D-3). **Keine** neue Tabelle/Migration (1b-a-D-4).
3. **NEU ADR 0048 `Provisional`** (`ReplaySnapshotPort`-
   Rekonstruktions-Pattern + Timestamp-Derivations-Vertrag +
   No-New-Table-Entscheidung; C1).
4. **NEU `tests/integration/test_mvp_002_replay_snapshot_
   smoke.py`** — Boundary-Pins: deterministische Sortierung,
   Timestamp-Derivation aus `simulation_time` (NICHT Wall-Clock),
   `import_sequence`-Tie-Break aus Insertion-Order, `value`-
   byte-stabiler Round-Trip, **Zwei-Lauf-Determinismus** (zwei
   getrennte `run_id`s desselben Szenarios liefern identische
   `ReplaySample`-Felder modulo `run_id` → `diff_replay()` leer).
5. **Anti-Scope (1b-a NICHT):** kein TickLoop-Terminal-Hook,
   keine `replay_diff_status`-Metrik, kein `GG-TERM-002/003`-
   Preflight, keine `docs/user/replay-determinism-e2e.md`, kein
   `GG-MVP-002`-Flip, keine neue Migration (alles 1b-b bzw.
   entfaellt).

---

## 3. Architektur-Entscheidungen (Welle-1b-a)

### 1b-a-D-0 — Persistenz-Quelle (aus Gruppenplan uebernommen)

**Final: NEU `ReplaySnapshotPort` (Driven)** — Gruppenplan
[`M7-welle-1.md §3 D-1`](M7-welle-1.md) (Option A). **NICHT**
`RunRepositoryPort` (nur Laufmetadaten/Status), **NICHT**
`SnapshotPort` (Driving — Schichten-Twist).

### 1b-a-D-1 — Sub-Slicing-Beschluss 1b → 1b-a + 1b-b

**Final: Sub-Sliced.** 1b-a = `ReplaySnapshotPort`-Lese-Substanz
(ADR 0048); 1b-b = TickLoop-Terminal-Hook + `replay_diff_status`-
Metrik + `GG-TERM-002/003`-Preflight + E2E-Audit-Doku +
`GG-MVP-002`-Flip (ADR 0049). **Begruendung:** zwei unabhaengige
Substanzen mit unterschiedlichem Blast-Radius — 1b-a ist ein
**reiner Driven-Adapter** auf bestehender Domain (`make
arch-check` belegt: kein Core-Import-Change), 1b-b schaerft den
**Core-Spine** (neue Terminal-Naht im `TickLoop`, die heute nicht
existiert — nur Pre-Tick-Guards + Driver-seitige Terminal-
Detection). Getrennte Review-Surfaces; repo-konsistent (M4/M5/
M6-Welle-4 alle sub-sliced, Pattern Welle-4b → 4b-a/b/c per
Welle-4b-a-D-1). `GG-MVP-002` flippt erst nach 1b-b.

### 1b-a-D-2 — `ReplaySnapshotPort`-Surface

**Final: Driven read-only Protocol** mit einer Methode
`read_samples(run_id: str) -> tuple[ReplaySample, ...]`,
deterministisch geordnet (Sortier-Invariante 1b-a-D-3). Nur
Core-Domain `ReplaySample` (AC-PORTS-NO-OUT; Vorbild
`TelemetrySinkPort.read_ordered`). **NICHT** in
`TelemetrySinkPort` mitfuehren (Trennung: Sink = Telemetrie
persistieren; Snapshot-Source = `ReplaySample` rekonstruieren —
unterschiedliche Domain-Typen, unterschiedliche Konsumenten).
**NICHT** `SnapshotPort` (Driving) wiederverwenden (Persistenz-
Quelle aus Driving-Surface = Schichten-Twist, Gruppenplan D-1).

### 1b-a-D-3 — Snapshot→`ReplaySample`-Rekonstruktion (= Gruppen-D-1.1)

**Frage:** Wie wird `TelemetryPoint` (10 Felder, **ohne**
Original-`timestamp`) auf `ReplaySample` (7 Felder, **mit**
`timestamp`) gemappt?

**Final:**

- `simulation_time`, `device_id`, `metric`, `unit` ← direkt.
- `value` ← `Decimal(str(...))` aus der `TEXT`-Spalte (1a
  garantiert byte-stabilen Round-Trip; ADR 0047 §2.4).
- `import_sequence` ← **globale Insertion-Order pro Lauf**
  (`telemetry_points.id`-aufsteigend → 0-basierter Counter,
  identische Basis wie `read_ordered`s `ORDER BY id`); das ist der
  deterministische Tie-Break (`GG-REPLAY-003`).
- **`timestamp` (die Lücke)** ← **kanonische deterministische
  Ableitung aus `simulation_time`**: `timestamp =
  str(simulation_time)`. **NICHT** aus `RunMetadata.started_at`
  (Wall-Clock — unterscheidet sich zwischen Laeufen und wuerde
  den byte-stabilen Self-Replay, also die `GG-MVP-002`-Akzeptanz,
  brechen). **Begruendung:** `GG-REPLAY-002` definiert
  `timestamp` als „unveraendert gespeicherten" Original-
  Zeitstempel; fuer **simulations-erzeugte** (nicht extern
  aufgezeichnete) Laeufe gibt es keinen externen Original-
  Stempel — der kanonische `simulation_time`-String **ist** der
  stabile Original-Wert. Zwei Laeufe desselben Szenarios erzeugen
  identische `simulation_time` → identischen `timestamp` → leerer
  Diff. Erzwungene Determinismus-Wahl; ADR 0048 (C1) fixiert den
  Derivations-Vertrag. Falls 1b-b spaeter externe Replay-Quellen
  mit echtem Original-Stempel braucht, ist das eine additive
  ADR-0011-Schaerfung (Zusatzspalte), kein Bruch dieses Vertrags.

### 1b-a-D-4 — Migrations-Bedarf

**Final: KEINE neue Migration in 1b-a.** Der
`ReplaySnapshotPort`-Adapter liest die bestehende 1a-Tabelle
`telemetry_points`; alle `ReplaySample`-Substanzen liegen dort
(Timestamp **abgeleitet**, nicht gespeichert). Gruppenplan-R1-
Mitigation explizit: „Falls `ReplaySample`-Sequenzen schon in der
Snapshot-Envelope-Sektion liegen, entfaellt die zweite
Migration." **Abweichung von Gruppenplan-D-1-Option-A-Wortlaut
(„eigene Tabelle")** — hier aufgeloest: keine separate Tabelle
noetig, da 1a's Schema die Substanz traegt. Haelt 1b-a-Scope
schmal (Alembic-Head bleibt `0002`).

### 1b-a-D-5 — ADR-Bedarf

**Final: NEU ADR 0048 `Provisional`** (Welle-1b-a-C1) —
`ReplaySnapshotPort`-Rekonstruktions-Pattern + Timestamp-
Derivations-Vertrag + No-New-Table-Entscheidung. Naechste freie
Nummer 0048 (letzte vergebene `0047-telemetry-sink-…`). 1b-b
traegt ADR 0049 (Replay-Lifecycle).

### 1b-a-D-6 — `GG-TERM-002/003`-Equality-Scope (1b-weite Entscheidung, hier verankert)

**Final (Maintainer-Beschluss):** 1b implementiert nur einen
**MVP-E2E-Replay-Preflight** ueber die bereits stabil
strukturierten `RunMetadata`-Felder `scenario_hash`,
`schema_version`, `seed`, `tick_ms`, `tool_version`.

**NICHT in 1b:** `platform_arch`, `enabled_adapters`/
Adapterprofile, `sim_start_time`, separater `config_hash`,
`RunMetadata`-Migration, `ReplayComparisonMetadata`-Envelope.

**Das ist KEINE vollstaendige Operationalisierung von
`GG-TERM-002/003`.** Das Lastenheft nennt mehr Pflichtfelder —
u. a. Plattformarchitektur, Konfiguration, Startzeit im
Simulationszeitmodell und aktivierte Adapter
([`spec/lastenheft.md` GG-TERM-002/003](../../../../spec/lastenheft.md#gg-term-002)).
Verankert als **dokumentierter `GG-TERM-002/003`-Carveout**; die
volle Matrix wird per ADR-0011-Pattern auf
[Trigger 038](../open/038-gg-term-002-003-full-equality-matrix.md)
(NEU, dieser C0) defert. **Scope-Korrektur am Gruppenplan
[`M7-welle-1.md`](M7-welle-1.md) §2.5 + §3 + R4 erfolgt in diesem
C0.** Der Preflight-Vertrag + die Carveout-Aussage landen formal
in **ADR 0049 (1b-b)**; Boundary-Pins einzeln fuer die 5 Felder
(1b-b). **Begruendung:** `started_at`/`ended_at` sind heute
Wall-Clock, nicht Simulationszeit (`core/domain/run.py`);
aktivierte Adapter + Plattformarchitektur liegen nicht
strukturiert in `RunMetadata`; ein Vollausbau waere Migration +
Canonicalization-Entscheidung + Public-Contract-Schaerfung und
wuerde 1b vom Replay-Lifecycle-Beleg wegziehen. Praktische
1b-Formulierung: „Replay-Diff wird nur ausgefuehrt, wenn die
vorhandenen deterministischen Vergleichsmetadaten gleich sind;
fehlende Vollfelder bleiben als dokumentierter
`GG-TERM-002/003`-Carveout offen."

---

## 4. Liefer-Reihenfolge

- **C0** (dieser Commit) — Slice-Doc + Decision-Liste 1b-a-D-0..
  D-6 + DoD; Gruppenplan-Sub-Slicing-/Equality-Scope-Korrektur;
  NEU Trigger 038.
- **C1** — NEU ADR 0048 `Provisional` (Surface + Rekonstruktion +
  No-New-Table).
- **C2** — Code: `ReplaySnapshotPort` + `PostgresReplaySnapshot
  Adapter` + Rekonstruktions-Smoke.
- **C3** — Status/DoD-Sync (1b-a `Done`; `M7-welle-1.md` 1b-a →
  Done; aktiver Slice 1b-b).
- **C4a/C4b** — Self-Close-Move `M7-welle-1b-a.md → done/` + Refs.

---

## 5. Critical Files

**NEU (C0/C1/C2):** `M7-welle-1b-a.md` (C0);
`docs/plan/planning/open/038-gg-term-002-003-full-equality-matrix.md`
(C0); `docs/plan/adr/0048-…md` (C1);
`src/grid_gym/hexagon/ports/driven/replay_snapshot.py` (C2);
`src/grid_gym/adapters/driven/persistence_postgres/
replay_snapshot_repository.py` (C2);
`tests/integration/test_mvp_002_replay_snapshot_smoke.py` (C2).
**MODIFY:** [`M7-welle-1.md`](M7-welle-1.md) (C0 — 1b-Sub-Slicing
+ Equality-Scope-Korrektur §2.5/§3/R4); `docs/plan/adr/README.md`
(C1).
**UNBERUEHRT:** `telemetry_points`-Schema (1a — read-only
gelesen), `diff_replay()`-Core, `TickLoop` (1b-b),
`TelemetrySinkPort`, `RunRepositoryPort`/`RunMetadata` (1b-D-6:
keine Migration).

---

## 6. Verifikationspfad

- `make gates` cache-frei gruen ohne Override (inkl. `arch-check`:
  kein neuer Core-Import — 1b-a ist reiner Driven-Adapter).
- `make test-integration` (Postgres-testcontainers) gruen inkl.
  NEU Rekonstruktions-Smoke.
- `make fullbuild` cache-frei gruen.
- `make docs-check` gruen.

---

## 7. Risiken

- **R1 Timestamp-Determinismus.** Falsche Ableitung (Wall-Clock)
  wuerde Self-Replay byte-instabil machen. Mitigation:
  Ableitung ausschliesslich aus `simulation_time` (1b-a-D-3);
  Smoke pinnt identischen `timestamp` ueber zwei Laeufe.
- **R2 `import_sequence`-Rekonstruktion.** Muss exakt der
  `read_ordered`-`ORDER BY id`-Basis folgen, sonst driften
  Tie-Breaks. Mitigation: gleiche `id`-Order-Basis;
  Smoke-Boundary-Pin auf Tie-Fall.
- **R3 Scope-Leak nach 1b-b.** Versehentliche Core-/Hook-/
  Metrik-Arbeit in 1b-a. Mitigation: Anti-Scope §2.5;
  `arch-check` belegt, dass `hexagon/core/**` unveraendert bleibt.

---

## 8. Wandert nach

Self-Close-Move `M7-welle-1b-a.md → done/` (C4a) + Refs-Sync
(C4b) nach 1b-a-C3. `M7-welle-1.md`-Gruppenplan bleibt in
`in-progress/` bis 1a+1b (= 1b-a+1b-b) geschlossen sind.

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] C0 — Slice-Doc §1..§9 + Decision-Liste 1b-a-D-0..D-6 +
      Gruppenplan-Korrektur (1b-Sub-Slicing + Equality-Scope) +
      NEU Trigger 038.
- [x] C1 — NEU ADR 0048 `Provisional` (Surface + Rekonstruktion +
      Timestamp-Derivation + No-New-Table).
- [x] C2 — `ReplaySnapshotPort` + `PostgresReplaySnapshotAdapter`
      + Rekonstruktions-Smoke; **keine** neue Migration.
- [x] C2 — Smoke pinnt deterministische Sortierung, Timestamp-
      Derivation aus `simulation_time`, `import_sequence`-Tie-
      Break, `value`-Round-Trip, Zwei-Lauf-Determinismus
      (`diff_replay()` leer modulo `run_id`).
      (8 Smokes inkl. Divergenz-fachlich-Gegenprobe + leerer Lauf.)
- [x] **`make test-integration` cache-frei gruen** (Postgres-
      testcontainers) — fuehrt den Rekonstruktions-Smoke als
      Kern-Evidence aus; laeuft **NICHT** in `make gates`/
      coverage-gate (das misst nur `tests/unit/`).
      (2026-06-09: 128 passed / 7 skipped.)
- [x] `make gates` + `make fullbuild` + `make docs-check` gruen.
- [x] C3 — 1b-a `Done`; `M7-welle-1.md` 1b-a → Done; aktiver
      Slice 1b-b.

**Anti-Scope (1b-a NICHT):** kein TickLoop-Terminal-Hook, keine
`replay_diff_status`-Metrik, kein `GG-TERM-002/003`-Preflight,
keine `docs/user/replay-determinism-e2e.md`, kein `GG-MVP-002`-
Flip, keine neue Alembic-Migration (alles 1b-b bzw. entfaellt).

---

## References

- [`M7-welle-1.md`](M7-welle-1.md) — GG-MVP-002-Gruppenplan +
  D-0..D-5 (Sub-Slicing + Equality-Scope hier in C0 verfeinert).
- [`M7-welle-1a.md`](M7-welle-1a.md) — Welle 1a
  (Zeitreihen-Persistenz, ADR 0047); liefert die `telemetry_
  points`-Lese-Quelle fuer 1b-a.
- [`M7-mvp-completion.md`](M7-mvp-completion.md) — M7-Meilenstein-
  Slice-Plan.
- [Trigger 038](../open/038-gg-term-002-003-full-equality-matrix.md)
  — volle `GG-TERM-002/003`-Equality-Matrix (1b-D-6-Carveout).
- [`../done/036-safe-006-replay-diff-status-replay-source-integration.md`](036-safe-006-replay-diff-status-replay-source-integration.md)
  — Trigger 036 (wird in 1b-b aufgeloest).
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md#gg-mvp-002)
  (`GG-MVP-002`, `GG-REPLAY-002/003/007`, `GG-TERM-002/003`).
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — Schaerfungs-Pattern fuer ADR 0048 + Trigger-038-Defer.
- [`../../adr/0047-telemetry-sink-timeseries-persistence.md`](../../adr/0047-telemetry-sink-timeseries-persistence.md)
  — 1a-Persistenz-Vertrag (`TEXT`-`value`-Byte-Stabilitaet).
