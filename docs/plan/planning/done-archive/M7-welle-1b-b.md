# Welle 1b-b — M7 Replay-Lifecycle: Terminal-Hook + `replay_diff_status` + GG-TERM-Preflight

**Status:** Done — C0 `c193788` (Slice-Doc + Decision-Liste
1b-b-D-0..D-9 + NEU
[Trigger 039](../done/039-api-replay-trigger-surface.md)) + C1
`021e8d7` (NEU ADR 0049 `Provisional` — Replay-Lifecycle) + C2
`6476267` (Code: Core-`TickLoop.finalize()`-Naht +
`replay_diff_status` + GG-TERM-Preflight + `InMemoryReplaySnapshot`
+ Demo-Wiring + Unit- + Zwei-Lauf-E2E-Smoke + Audit-Doku-Flips +
Trigger-036-Skip-Reaktivierung) + C3 (DoD §9 abgehakt; 1b-b →
`Done`; **`GG-MVP-002` ✓ produktiv** in roadmap; Trigger-036-Status
→ Closed). **Offen: C4a/C4b** (Self-Close-Move `M7-welle-1b-b.md`
**+ Gruppenplan `M7-welle-1.md`** + Trigger 036 → `done/` +
Refs-Sync). Code + alle Gates
(`gates`/`test-integration`/`fullbuild`/`docs-check`) cache-frei
gruen 2026-06-09 — `make test-integration` 132 passed / 6 skipped
(3 neue Replay-Lifecycle-Smokes + reaktivierter Pin).

Drittes (letztes) Sub-Slice von **Welle 1b** und Closure-Slice von
**M7-Welle-1** (`GG-MVP-002`): schliesst die zweite `GG-MVP-002`-
Lücke (deterministische End-to-End-Replay-Verkabelung). Setzt auf
**1a** (Persistenz, ADR 0047) + **1b-a** (`ReplaySnapshotPort`-Lese-
Substanz, ADR 0048) auf. **`GG-MVP-002` flippt mit diesem Slice**
(nach echtem Zwei-Lauf-Beleg). **Monolithisch** (1b-b-Maintainer-
Beschluss): der Flip darf nicht zerschnitten werden, und die Teile
(Hook braucht Referenz braucht Preflight) sind eng gekoppelt.

Liefer-Reihenfolge C0 → C1 (NEU ADR 0049 `Provisional`) → C2
(Code) → C3 (Status/DoD-Sync + Flip) → C4a/C4b (Self-Close-Move).

---

## 1. Context

`GG-MVP-002` ist im **partial**-Stand. Welle **1a** schloss die
Persistenz-Lücke (`telemetry_points`, ADR 0047); Welle **1b-a**
lieferte den `ReplaySnapshotPort` (ADR 0048), der aus den
persistierten Telemetrie-Zeitreihen deterministisch geordnete
`ReplaySample`-Sequenzen rekonstruiert. Offen bleibt die
**Lauf-Lifecycle-Verkabelung**: `diff_replay()` ist produktiv
(`GG-REPLAY-007`, Welle-5c-Audit), aber kein Lauf-Ende ruft es auf,
und es gibt keinen `replay_diff_status` (Architektur §15 Z. 820 +
823; Trigger 036).

### 1.1 Ist-Zustand (Code-verifiziert, 1b-b-C0-Audit)

- **Kein Core-Terminal-Seam.** `TickLoop` setzt `"completed"`
  **nie** automatisch (`tick_loop.py`: `_CONTROL_ACTION_TRANSITIONS`
  kennt nur `pause`/`resume`/`stop`; `"completed"` ist ein
  `RunStatus`-Literal ohne Auto-Transition). Terminierung ist
  immer externes `request("stop")` → `"stopped"`; `tick()` wirft
  bei terminalem State `TickLoopStoppedError`. Es gibt **kein**
  `finalize()`/End-of-Run-Hook.
- **Deterministische Run-End-Naht liegt im Driver.**
  `DemoTickLoopDriver._tick_forever()` verlaesst den Loop genau
  einmal bei `control_state in ("stopped", "completed")`
  (`_tick_loop_driver.py`). Kein Tick-Budget/keine Szenario-
  Dauer im Driver.
- **`diff_replay()`** (`hexagon/core/replay/diff.py`):
  `diff_replay(expected, actual, *, tick_ms=1000,
  volatile_fields=None) -> tuple[ReplayDelta, ...]`. Pure-Function,
  heute nur in Unit-Tests aufgerufen. `volatile_fields`-Default
  `frozenset({"import_sequence"})`.
- **`ReplayDelta`** traegt **alle vier** `GG-SAFE-006`-Detailfelder
  bereits: `path`/`expected`/`actual` (Replay-Diff), `tick`
  (betroffene Ticks), `device_id`, `classification`
  (`fachlich`/`volatil`).
- **`ReplaySnapshotPort.read_samples(run_id) -> tuple[ReplaySample,
  ...]`** (1b-a, ADR 0048): `PostgresReplaySnapshotAdapter`
  vorhanden; **kein** In-Memory-Adapter (1b-a-deferred).
- **`MetricsPort.gauge(name, value, *, attributes)`** (ADR 0024)
  produktiv; `TickLoop._obs_gauge(...)` emittiert mit
  `attributes={"run_id": …}`. Kein neuer Port-Method-Bedarf.
- **`RunMetadata`** (frozen): `run_id`, `scenario_hash`,
  `schema_version`, `seed`, `tick_ms`, `started_at`, `ended_at`,
  `tool_version`. `started_at`/`ended_at` sind heute beim `save()`
  **leer** und werden nirgends gesetzt; `RunMetadata` ist
  immutable (kein Timestamp-Update-Pfad). `run_repository`
  (Driven) ist im `TickLoop` injiziert (`get_by_id`/`get_status`/
  `update_status`).
- **Keine Referenz-Lauf-Verknuepfung** existiert (grep: kein
  `ReplaySource`, kein `reference_run_id`, kein Scenario-/`POST
  /runs`-Replay-Feld).
- **Skipped Smoke** `test_safe_006_diff_replay_status_deferred_via_
  trigger_036` (`tests/integration/test_m6_welle_5c_safe_005_006_
  compose_smoke.py`) markiert die Lücke — wird in 1b-b-C2
  reaktiviert.

---

## 2. Lieferziel (Welle-1b-b-C2)

1. **NEU Core-`TickLoop.finalize()`-Naht** (idempotent): fuehrt
   bei Lauf-Ende den Replay-Diff + die Metrik-Emission + die
   `GG-SAFE-006`-Detail-Evidence aus. Der `DemoTickLoopDriver`
   ruft `finalize()` am Loop-Exit — der Driver traegt **keine**
   Diff-Logik (1b-b-D-1).
2. **Referenz-Bindung als Core-Runtime-Kwargs:** NEU keyword-only
   `replay_snapshot: ReplaySnapshotPort | None = None` +
   `replay_reference_run_id: str | None = None` (beide `None` →
   `finalize()` no-op). `expected = read_samples(reference_run_id)`,
   `actual = read_samples(run_id)` (1b-b-D-2).
3. **`GG-TERM-002/003`-MVP-Preflight** ueber 5 `RunMetadata`-
   Felder (`scenario_hash`/`schema_version`/`seed`/`tick_ms`/
   `tool_version`) vor dem Diff; Mismatch → Reject (kein Diff,
   strukturierter Log), per-Feld-Boundary-Tests (1b-b-D-3).
4. **`replay_diff_status`-Metrik** (binaer-Gauge 0.0 diverged /
   1.0 clean, `attributes={run_id, reference_run_id, status}`,
   nur bei preflight-validem Vergleich; 1b-b-D-4).
5. **`GG-SAFE-006`-Detail-Evidence:** `finalize()` emittiert die
   `ReplayDelta`-Details (path/expected/actual/tick/device_id/
   classification) maschinenlesbar via `log_port` (1b-b-D-5).
6. **NEU `InMemoryReplaySnapshot`** (`persistence_inmemory/`) fuer
   den Demo-/Test-Pfad (1b-b-D-8).
7. **Demo-Wiring** (`_demo_scenario_setup.py`): `replay_snapshot`
   in die `TickLoopWiring` (Demo-Lauf hat keine Referenz →
   `finalize()` no-op); Driver triggert `finalize()`.
8. **NEU `tests/integration/test_mvp_002_replay_lifecycle_
   smoke.py`** — **Zwei-Lauf-E2E**: Lauf A (Original, persistiert)
   + Lauf B (`replay_reference_run_id = A`) → Preflight gruen +
   leerer Diff → `replay_diff_status = 1.0`; Divergenz-Lauf →
   fachlicher Delta + `0.0`; per-Feld-Preflight-Mismatch-Rejects.
9. **Audit-Doku:** NEU `docs/user/replay-determinism-e2e.md`
   (`GG-MVP-002` ✓ produktiv) + Flip `docs/user/safe-005-006-
   fallback-determinism.md` `GG-SAFE-006` ⚠ → ✓ + Reaktivierung
   des Trigger-036-Skip-Smokes.
10. **`GG-MVP-002`-Flip** (roadmap + lastenheft-Traceability) +
    **Trigger 036 → `done/`**.
11. **NEU ADR 0049 `Provisional`** (Replay-Lifecycle; C1).

**Anti-Scope (1b-b NICHT):** oeffentliche API-Replay-Bedienung
(POST /runs `replay_of` + `RunMetadata`-Spalte + Migration) →
**Trigger 039** (1b-b-D-7); `started_at`/`ended_at`-Timestamp-
Setzen (eigener Scope); volle `GG-TERM-002/003`-Matrix → Trigger
038; `GG-REPLAY-004..006` (beschleunigtes Replay / Replay-Pause-
Resume / Delta-Analysen-API, SOLLTE) → bleiben offen (1b-b-D-9).

---

## 3. Architektur-Entscheidungen (Welle-1b-b)

### 1b-b-D-0 — Lifecycle-Hook-Schicht (aus Gruppenplan)

**Final: Core-Spine** (Gruppenplan [`M7-welle-1.md §3 D-3`](M7-welle-1.md)
Option A, ADR 0049). **NICHT** Driving-Adapter: Live + Replay
teilen denselben Tick-Prozessor; der Hook gehoert in den Spine
(GG-AR-P-003/GG-AR-P-007), sonst persistierte/diffte ein
headless-Runner ohne Driver nicht.

### 1b-b-D-1 — Terminal-Naht-Form

**Frage:** Wie wird der Core-Hook realisiert, wenn heute kein
Core-Terminal-Seam existiert (nur Driver-Loop-Exit)?

**Final: NEU idempotente Core-`TickLoop.finalize()`-Methode.** Der
Driver erkennt weiterhin das Loop-Ende (`control_state` terminal),
ruft aber nur `finalize()` — die **Diff-Logik
(`diff_replay()`/`replay_diff_status`/SAFE-006-Evidence) sitzt im
Core**, nicht im Driver. `finalize()` ist **idempotent**
(`_finalized`-Flag → Mehrfachaufruf von Driver + Lifespan-`stop()`
ist sicher). `finalize()` aendert `control_state` **nicht**:
`"completed"` bleibt semantisch vorhanden, wird aber nicht vom
Core auto-gesetzt (Ist-Zustand korrekt geschlossen; ein Auto-
`completed` braeuchte ein Tick-Budget/Szenario-Ende, das es nicht
gibt — out-of-scope). **Begruendung:** haelt GG-AR-P-003/007 sauber
(Adapter triggert, Core entscheidet) und ist der minimale Eingriff
gegen den heutigen `control_state`-Pfad.

### 1b-b-D-2 — Referenzlauf-Verknuepfung

**Frage:** Woher kommt `expected` (der Vergleichslauf)?

**Final: explizite Runtime-Bindung** ueber NEU keyword-only
Core-Kwargs `replay_snapshot: ReplaySnapshotPort | None` +
`replay_reference_run_id: str | None` (beide `None` → `finalize()`
no-op). `expected = replay_snapshot.read_samples(replay_reference_
run_id)`, `actual = replay_snapshot.read_samples(run_id)`.

- **KEIN Self-Replay gegen dieselbe `run_id`** als Determinismus-
  Beleg — das waere nur ein Read-/Idempotenz-Test (tautologisch
  leer). Der Beleg braucht **zwei getrennte Laeufe**.
- **KEINE implizite Auto-Auswahl** („letzter passender Lauf") —
  zu mehrdeutig + schlecht auditierbar.
- Die Bindung ist in 1b-b **Runtime/Test/Demo-intern** (kein
  oeffentliches API-Feld → 1b-b-D-7).

### 1b-b-D-3 — `GG-TERM-002/003`-MVP-Preflight

**Final: Preflight ueber 5 vorhandene `RunMetadata`-Felder**
(`scenario_hash`, `schema_version`, `seed`, `tick_ms`,
`tool_version`) via `run_repository.get_by_id(reference_run_id)` +
`get_by_id(run_id)`. Bei Ungleichheit eines Felds → **Reject vor
`diff_replay()`**: kein `replay_diff_status` (kein valider
Vergleich), strukturierter `log_port`-Record mit dem/den
abweichenden Feld(ern). C2 liefert **per-Feld**-Boundary-Tests
(ein generischer Mismatch reicht nicht). Volle Matrix
(`platform_arch`/`enabled_adapters`/`sim_start_time`/`config_hash`)
bleibt Carveout
[Trigger 038](../done/038-gg-term-002-003-full-equality-matrix.md)
(1b-a-D-6). Begruendung der Reject-Semantik: ein Replay-Diff
zwischen ungleich-konfigurierten Laeufen ist fachlich
bedeutungslos; die binaere Metrik bleibt nur fuer **valide**
Vergleiche definiert (1b-b-D-4).

### 1b-b-D-4 — `replay_diff_status`-Kodierung

**Final: binaerer Gauge** (Gruppenplan D-2 Option A, ADR 0049):
`metrics_port.gauge("replay_diff_status", value, attributes={
"run_id": …, "reference_run_id": …, "status": …})` mit
**`value = 1.0` (clean: kein fachlicher Delta) / `0.0` (diverged:
≥1 fachlicher Delta)**; `status`-Attribut `"clean"`/`"diverged"`.
Volatile Deltas (`import_sequence`) zaehlen **nicht** als
Divergenz. Emittiert **nur bei preflight-validem Vergleich** (so
bedeutet die Metrik stets „ein valider Replay-Vergleich lief und
war clean/diverged"). Keine neue `MetricsPort`-Methode
(ADR-0024-Vertrag gewahrt; Gruppenplan R3). Severity-Stufen sind
additive ADR-0011-Schaerfung, falls spaeter gewollt.

### 1b-b-D-5 — `GG-SAFE-006`-Detail-Evidence

**Final:** `finalize()` emittiert die `ReplayDelta`-Details
(`path`/`expected`/`actual`/`tick`/`device_id`/`classification`)
maschinenlesbar via `log_port` (strukturierter Record pro Delta
oder Delta-Aggregat). Die vier `GG-SAFE-006`-Akzeptanzfelder
liegen **bereits** in `ReplayDelta`; 1b-b liefert den **integrierten
Lifecycle-Pfad**, der sie emittiert. Der Divergenz-Smoke pinnt
alle vier Felder maschinenlesbar → `docs/user/safe-005-006-
fallback-determinism.md` flippt `GG-SAFE-006` ⚠ → ✓ produktiv +
Trigger 036 → `done/`.

### 1b-b-D-6 — Ausfuehrungsmodell

**Final: synchron in `finalize()`** (Gruppenplan R2). Der Diff ist
durch die Lauf-Laenge beschraenkt; fuer Demo-/Abnahme-Skala
unkritisch. Eine asynchrone Entkopplung (mit explizitem
Lifecycle-/Drain-Vertrag, kein Fire-and-forget) waere eine
additive ADR-0011-Schaerfung bei Last-Druck. Die Lauf-Status-
Transition blockiert nicht auf unbounded Diff-Arbeit, weil
`finalize()` nach dem terminalen `control_state` laeuft (der Lauf
ist bereits gestoppt).

### 1b-b-D-7 — Oeffentliche API-Replay-Bedienung (Scope-Schalter)

**Final: NICHT in 1b-b** → NEU
[Trigger 039](../done/039-api-replay-trigger-surface.md). Die
1b-b-Referenz-Bindung (1b-b-D-2) ist Runtime/Test/Demo-intern. Ein
oeffentliches `POST /runs` `replay_of`-Feld + `RunMetadata`-
`replay_of`-Spalte + Alembic-Migration + `RunCreateRequest`-Strict-
Schaerfung (ADR 0045) ist ein **eigener API-/Schema-Scope mit
Migration** und wird explizit defert. **Begruendung:** der
`GG-MVP-002`-Determinismus-Beleg („laesst sich deterministisch
replayen", Lastenheft Z. 130-135) wird durch den **Zwei-Lauf-E2E-
Smoke** ehrlich erbracht; das „ueber API" der Akzeptanz bindet an
den **Szenario-Start** (vorhandener `POST /runs`-Pfad), nicht an
eine API-getriggerte Replay-Bedienung. **Risiko R1** haelt die
Reviewer-Lesart fest, falls API-getriggertes Replay doch fuer den
Flip gefordert wird.

### 1b-b-D-8 — `InMemoryReplaySnapshot`

**Final: NEU `InMemoryReplaySnapshot`** (`adapters/driven/
persistence_inmemory/`), das ueber dieselbe `TelemetryPoint →
ReplaySample`-Mapping-Konvention (ADR 0048 §2.2) aus dem
`InMemoryTelemetrySink`-Store rekonstruiert. Vorbild: 1a-
`InMemoryTelemetrySink`. Noetig fuer das Demo-Wiring + Unit-
Testbarkeit (1b-a hatte den Postgres-Adapter; der In-Memory-Pfad
fehlte).

### 1b-b-D-9 — ADR-Bedarf + `GG-REPLAY-004..006`-Bundling

**Final: NEU ADR 0049 `Provisional`** (Replay-Lifecycle: Terminal-
Naht + `replay_diff_status`-Vertrag + Preflight + SAFE-006-
Detail-Vertrag). **`GG-REPLAY-004..006`** (beschleunigtes Replay /
Replay-Pause-Resume / Delta-Analysen-API; alle SOLLTE,
Lastenheft `🔲 M3`) sind **NICHT** in 1b-b — sie teilen zwar den
Lauf-Lifecycle, sind aber eigene SOLLTE-Substanz ohne
`GG-MVP-002`-Akzeptanz-Bezug; bleiben offen.

---

## 4. Liefer-Reihenfolge

- **C0** (dieser Commit) — Slice-Doc + Decision-Liste 1b-b-D-0..
  D-9 + DoD + NEU Trigger 039.
- **C1** — NEU ADR 0049 `Provisional`.
- **C2** — Code: Core-`finalize()` + Referenz-Kwargs + Preflight +
  `replay_diff_status` + SAFE-006-Log + `InMemoryReplaySnapshot` +
  Demo-Wiring + Zwei-Lauf-E2E-Smoke + Audit-Doku-Flips +
  Trigger-036-Skip-Reaktivierung.
- **C3** — Status/DoD-Sync + `GG-MVP-002`-Flip (roadmap +
  lastenheft-Traceability) + Trigger 036 → `done/`.
- **C4a/C4b** — Self-Close-Move `M7-welle-1b-b.md → done/` +
  Refs-Sync; **M7-welle-1.md-Gruppenplan wandert mit nach
  `done/`** (1a+1b komplett).

---

## 5. Critical Files

**NEU (C0/C1/C2):** `M7-welle-1b-b.md` (C0);
`docs/plan/planning/done/039-api-replay-trigger-surface.md` (C0);
`docs/plan/adr/0049-…md` (C1);
`src/grid_gym/adapters/driven/persistence_inmemory/replay_snapshot.py`
(C2); `docs/user/replay-determinism-e2e.md` (C2);
`tests/integration/test_mvp_002_replay_lifecycle_smoke.py` (C2).
**MODIFY (C2):** `hexagon/core/simulation/tick_loop.py` (NEU
`finalize()` + `replay_snapshot`/`replay_reference_run_id`-Kwargs);
`hexagon/core/scenario/loader.py` (`build_tick_loop`-Symmetrie fuer
die neuen Kwargs); `adapters/driving/http_api/_tick_loop_driver.py`
(Driver triggert `finalize()` am Loop-Exit);
`adapters/driving/http_api/_demo_scenario_setup.py` (Wiring);
`adapters/driven/persistence_inmemory/__init__.py` (Re-Export);
`docs/user/safe-005-006-fallback-determinism.md` (`GG-SAFE-006`
⚠ → ✓); `tests/integration/test_m6_welle_5c_safe_005_006_compose_
smoke.py` (Skip-Reaktivierung); `docs/plan/adr/README.md` (C1).
**MODIFY (C3):** `M7-welle-1.md` (1b-b → Done, Gruppen-Closure);
`roadmap.md` + `spec/lastenheft.md`-Traceability (`GG-MVP-002` ✓);
`open/README.md` + `open/036…` (→ `done/`).
**UNBERUEHRT:** `diff_replay()`-Core-Algorithm (nur aufgerufen),
`ReplaySample`/`ReplayDelta`-Domain, `telemetry_points`-Schema,
`ReplaySnapshotPort` (1b-a), ADR 0047/0048.

---

## 6. Verifikationspfad

- `make gates` cache-frei gruen (inkl. `arch-check`: Core haelt
  nur Driven-Port-Protokolle als Kwargs — Praezedenz
  `run_repository`/`telemetry_sink`/`metrics_port`).
- `make test-integration` gruen inkl. NEU Zwei-Lauf-Replay-
  Lifecycle-Smoke + reaktiviertem Trigger-036-Smoke.
- `make fullbuild` + `make docs-check` cache-frei gruen.

---

## 7. Risiken

- **R1 Flip-Lesart `GG-MVP-002`.** Falls Reviewer „laesst sich
  deterministisch replayen" als **API-getriggertes** Replay lesen
  (statt Zwei-Lauf-E2E-Beleg), muss Trigger 039 (oeffentliche
  API-Bedienung) in 1b-b oder ein 1b-c vorgezogen werden.
  Mitigation: C0/ADR 0049 dokumentiert die Akzeptanz-Lesart
  explizit (1b-b-D-7); der Zwei-Lauf-Smoke ist der harte Beleg.
- **R2 `finalize()`-Idempotenz + Aufruf-Stellen.** Driver-Loop-
  Exit **und** Lifespan-`stop()` koennen `finalize()` aufrufen.
  Mitigation: `_finalized`-Flag; Smoke pinnt Doppel-Aufruf =
  einmalige Emission.
- **R3 Preflight-Reject-Observability.** Bei Mismatch kein
  `replay_diff_status` → Beobachter unterscheidet „kein Replay
  konfiguriert" nicht von „Preflight rejected". Mitigation:
  strukturierter `log_port`-Record mit dem abweichenden Feld;
  Smoke pinnt den Reject-Log.
- **R4 In-Memory-Determinismus.** `InMemoryReplaySnapshot` muss
  exakt dieselbe `TelemetryPoint → ReplaySample`-Mapping-Konvention
  wie der Postgres-Adapter (ADR 0048 §2.2) liefern. Mitigation:
  geteilte Mapping-Konvention; Smoke vergleicht beide Pfade gegen
  dieselbe Erwartung.

---

## 8. Wandert nach

Self-Close-Move `M7-welle-1b-b.md → done/` (C4a) + Refs-Sync
(C4b) nach 1b-b-C3. **Mit 1b-b-Closure ist M7-Welle-1 komplett**
(1a + 1b-a + 1b-b) — der Gruppenplan
[`M7-welle-1.md`](M7-welle-1.md) wandert in derselben C4-Sequenz
nach `done/`.

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] C0 — Slice-Doc §1..§9 + Decision-Liste 1b-b-D-0..D-9 + NEU
      Trigger 039.
- [x] C1 — NEU ADR 0049 `Provisional` (Terminal-Naht +
      `replay_diff_status` + Preflight + SAFE-006-Detail-Vertrag).
- [x] C2 — Core-`finalize()` + `replay_snapshot`/`replay_reference_
      run_id`-Kwargs + Preflight + `replay_diff_status` + SAFE-006-
      Log + `InMemoryReplaySnapshot` + Demo-Wiring.
- [x] C2 — Zwei-Lauf-E2E-Smoke: Original + Replay → Preflight gruen
      + leerer Diff + `replay_diff_status = 1.0`; Divergenz →
      fachlicher Delta + `0.0`; per-Feld-Preflight-Mismatch-Rejects;
      `finalize()`-Idempotenz. (Unit + Integration.)
- [x] C2 — `GG-SAFE-006`-Detailfelder (path/expected/actual/tick/
      device_id/classification) maschinenlesbar gepinnt; Trigger-
      036-Skip-Smoke reaktiviert + gruen.
- [x] **`make test-integration` cache-frei gruen** (Postgres-
      testcontainers) — fuehrt den Zwei-Lauf-Replay-Lifecycle-Smoke
      als Kern-Evidence aus. (2026-06-09: 132 passed / 6 skipped.)
- [x] `make gates` + `make fullbuild` + `make docs-check` gruen.
- [x] C2 — NEU `docs/user/replay-determinism-e2e.md` + Flip
      `docs/user/safe-005-006-…` `GG-SAFE-006` ⚠ → ✓.
- [x] C3 — 1b-b `Done`; **`GG-MVP-002` ✓ produktiv** (roadmap;
      Lastenheft-Impl-Matrix fuehrt `GG-MVP-001..004` als
      „n/a — Scope-Festlegung", Z. 2205 — kein Per-ID-Marker zu
      flippen); Trigger 036 → Closed (Move `done/` in C4a);
      M7-Welle-1 komplett (Gruppenplan → `done/` in C4).

**Anti-Scope (1b-b NICHT):** oeffentliche API-Replay-Bedienung
(Trigger 039), `started_at`/`ended_at`-Setzen, volle GG-TERM-Matrix
(Trigger 038), `GG-REPLAY-004..006`, Auto-`completed`-Transition,
Severity-Stufen-Metrik, asynchroner Diff.

---

## References

- [`M7-welle-1.md`](M7-welle-1.md) — GG-MVP-002-Gruppenplan
  (D-2/D-3 Replay-Lifecycle; wandert mit 1b-b nach `done/`).
- [`M7-welle-1b-a.md`](M7-welle-1b-a.md) — Welle 1b-a
  (`ReplaySnapshotPort`, ADR 0048); liefert die Sample-Lese-Quelle.
- [`M7-welle-1a.md`](M7-welle-1a.md) — Welle 1a
  (Persistenz, ADR 0047).
- [`M7-mvp-completion.md`](M7-mvp-completion.md) — M7-Meilenstein-
  Slice-Plan.
- [Trigger 036](036-safe-006-replay-diff-status-replay-source-integration.md)
  — wird mit 1b-b-C3 nach `done/` aufgeloest.
- [Trigger 038](../done/038-gg-term-002-003-full-equality-matrix.md)
  — volle GG-TERM-002/003-Matrix (Carveout).
- [Trigger 039](../done/039-api-replay-trigger-surface.md) —
  oeffentliche API-Replay-Bedienung (1b-b-D-7-Carveout).
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md#gg-mvp-002)
  (`GG-MVP-002`, `GG-SAFE-006`, `GG-REPLAY-002/003/007`,
  `GG-TERM-002/003`).
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — Schaerfungs-Pattern fuer ADR 0049.
- [`../../adr/0024-observability-port-trio.md`](../../adr/0024-observability-port-trio.md)
  — `MetricsPort`/`LogPort`-Vertrag.
- [`../../adr/0048-replay-snapshot-port-reconstruction.md`](../../adr/0048-replay-snapshot-port-reconstruction.md)
  — `ReplaySnapshotPort` + Mapping-Konvention (1b-a).
