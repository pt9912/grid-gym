# Replay-Determinismus E2E (`GG-MVP-002`)

Audit-Doku fuer die [`GG-MVP-002`](../../spec/lastenheft.md#gg-mvp-002)-Akzeptanz (Lastenheft Z. 130-135):

> Der MVP MUSS mindestens ein End-to-End-Szenario mit
> Netzanschlusspunkt, PV, Lastprofil, Smart Meter und
> Batteriespeicher enthalten. Akzeptanz: Das Szenario startet
> ueber API, erzeugt Live-Telemetrie, persistiert Zeitreihen und
> **laesst sich deterministisch replayen** (byte-identische
> kanonische Ergebnisdateien oder leerer Replay-Diff).

Geliefert ueber **M7-Welle-1** in drei Sub-Slices: 1a (Zeitreihen-
Persistenz, [`ADR 0047`](../plan/adr/0047-telemetry-sink-timeseries-persistence.md)), 1b-a (`ReplaySnapshotPort`, [`ADR 0048`](../plan/adr/0048-replay-snapshot-port-reconstruction.md)),
1b-b (Replay-Lifecycle, [`ADR 0049`](../plan/adr/0049-replay-lifecycle-finalize-hook.md)).

---

## Akzeptanz-Komponenten

| Komponente | Substanz-Pfad | Test-Pfad | Status |
| ---------- | ------------- | --------- | ------ |
| **Szenario startet ueber API** | `POST /runs` + Demo-Szenario `deploy/scenarios/gg-demo.yaml` (5 Pflicht-Entitaeten: GridConnection + PV + Last + Smart Meter + Batteriespeicher). | `tests/integration/test_mvp_demo_scenario.py` | ✓ Produktiv |
| **Live-Telemetrie** | WebSocket-Streams `/runs/{id}/telemetry` + `/runs/{id}/alarms-stream`. | M5-Welle-2-/4b-Smokes | ✓ Produktiv |
| **Persistiert Zeitreihen** | `TelemetrySinkPort` (Driven) + `PostgresTelemetrySinkAdapter` → `telemetry_points` (append-only, `value` byte-stabil als `TEXT`/`str(Decimal)`); Core-Spine-Wiring pro Tick ([`ADR 0047`](../plan/adr/0047-telemetry-sink-timeseries-persistence.md)). | `tests/integration/test_mvp_002_timeseries_persistence_smoke.py` | ✓ Produktiv (1a) |
| **Deterministisch replaybar** | `ReplaySnapshotPort.read_samples(run_id)` rekonstruiert `ReplaySample`-Sequenzen aus `telemetry_points` (Timestamp deterministisch aus `simulation_time`, [`ADR 0048`](../plan/adr/0048-replay-snapshot-port-reconstruction.md)); `TickLoop.finalize()` difft `expected`/`actual` via `diff_replay()` + emittiert `replay_diff_status` nach [`GG-TERM-002`](../../spec/lastenheft.md#gg-term-002)/003-Preflight ([`ADR 0049`](../plan/adr/0049-replay-lifecycle-finalize-hook.md)). | `tests/integration/test_mvp_002_replay_snapshot_smoke.py` + `…_replay_lifecycle_smoke.py` + `tests/unit/…/test_tick_loop_replay_finalize.py` | ✓ Produktiv (1b-a/1b-b) |

---

## Determinismus-Pfad

1. **Persistenz (1a).** Jeder Tick persistiert
   `TickResult.emitted_telemetry` append-only ueber den
   `TelemetrySinkPort` aus dem Core-Spine. `value` wird als
   kanonischer `str(Decimal)` in einer `TEXT`-Spalte gehalten —
   byte-stabiler Round-Trip ist die Vorbedingung fuer den
   Replay-Diff.

2. **Rekonstruktion (1b-a).** `ReplaySnapshotPort` liest die
   persistierten Punkte eines Laufs in Insertion-Reihenfolge
   (`ORDER BY id`) und mappt sie auf `ReplaySample`s. Der
   Original-`timestamp` wird **deterministisch aus
   `simulation_time` abgeleitet** (`str(simulation_time)`), nicht
   aus Wall-Clock — sonst waere der Self-/Zwei-Lauf-Replay
   byte-instabil.

3. **Lifecycle-Diff (1b-b).** Am Lauf-Ende ruft der Driver den
   idempotenten Core-Hook `TickLoop.finalize()`. Mit einer
   expliziten `replay_reference_run_id`-Bindung difft er
   `actual = read_samples(run_id)` gegen
   `expected = read_samples(reference_run_id)` — nach einem
   [`GG-TERM-002`](../../spec/lastenheft.md#gg-term-002)/003-MVP-Preflight (Gleichheit von
   `scenario_hash`, `schema_version`, `seed`, `tick_ms`,
   `tool_version`). Ergebnis: `replay_diff_status`-Gauge
   (`1.0` clean / `0.0` diverged) + maschinenlesbare
   [`GG-SAFE-006`](../../spec/lastenheft.md#gg-safe-006)-Detail-Logs.

**Zwei-Lauf-Beleg:** `test_mvp_002_replay_lifecycle_smoke.py`
faehrt zwei echte Demo-Szenario-Laeufe mit gleichem Seed,
persistiert beide nach Postgres und belegt ueber den
`finalize()`-Hook einen **leeren Diff** (`replay_diff_status =
1.0`) — die [`GG-TERM-002`](../../spec/lastenheft.md#gg-term-002)-Akzeptanz „leerer Replay-Diff".

---

## Carveouts

- **[`GG-TERM-002`](../../spec/lastenheft.md#gg-term-002)/003 volle Equality-Matrix** (`platform_arch`,
  `enabled_adapters`, `sim_start_time`, separater `config_hash`)
  ist nicht Teil des MVP-Preflights —
  [Trigger 038](../plan/planning/open/038-gg-term-002-003-full-equality-matrix.md).
- **Oeffentliche API-Replay-Bedienung** (POST /runs `replay_of`-
  Feld + persistente `RunMetadata`-Bindung) ist deferred —
  [Trigger 039](../plan/planning/open/039-api-replay-trigger-surface.md).
  Der Determinismus-Beleg laeuft ueber den Zwei-Lauf-E2E-Smoke;
  die Referenz-Bindung ist heute Runtime/Test/Demo-intern.
- **[`GG-REPLAY-004`](../../spec/lastenheft.md#gg-replay-004)..006** (beschleunigtes Replay / Replay-Pause-
  Resume / Delta-Analysen-API; SOLLTE) bleiben offen.

---

## Architektur-Bezug

- [ADR 0047 — TelemetrySinkPort Zeitreihen-Persistenz](../plan/adr/0047-telemetry-sink-timeseries-persistence.md)
- [ADR 0048 — ReplaySnapshotPort Rekonstruktion](../plan/adr/0048-replay-snapshot-port-reconstruction.md)
- [ADR 0049 — Replay-Lifecycle: Terminal-Hook + `replay_diff_status` + GG-TERM-Preflight](../plan/adr/0049-replay-lifecycle-finalize-hook.md)
- [`safe-005-006-fallback-determinism.md`](safe-005-006-fallback-determinism.md)
  — [`GG-SAFE-006`](../../spec/lastenheft.md#gg-safe-006)-Schwester-Audit (mit 1b-b ✓ produktiv).
- `spec/lastenheft.md` — [`GG-MVP-002`](../../spec/lastenheft.md#gg-mvp-002), [`GG-TERM-002`](../../spec/lastenheft.md#gg-term-002)/003,
  [`GG-REPLAY-002`](../../spec/lastenheft.md#gg-replay-002)/003/007, [`GG-SAFE-006`](../../spec/lastenheft.md#gg-safe-006).
