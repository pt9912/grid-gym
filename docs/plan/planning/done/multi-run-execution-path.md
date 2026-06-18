# Multi-Run-Execution-Pfad (entsperrt Slice 039 Phase B)

**Status:** **Abgeschlossen (`done/`, 2026-06-18)** — S0..S4 geliefert + frischer
Welle-Review (HIGH/MEDIUM-Findings adressiert, danach statisch re-verifiziert);
Architektur [`ADR 0069`](../../adr/0069-multi-run-execution-and-scenario-store.md)
`Accepted`. Replay-Paar 039+040 mit-geschlossen (→ `done/`); `make gates`/`make
docs-check`/`make fullbuild` gruen. Residuen dokumentiert (§Risiken).
**Datum:** 2026-06-18
**Quelle:** Delta aus der 039/040-Replay-Paar-Analyse — Phase B
([`ADR 0068`](../../adr/0068-api-replay-binding-persistence.md) §2.4) haengt am
Run-Execution-/Multi-Run-Driver-Pfad, der bisher Anti-Scope war.

---

## Ziel

`POST /runs`-erzeugte Laeufe **ausfuehrbar** machen (per-Run-`TickLoop` +
Driver), sodass ein API-Replay-Lauf gebaut, getickt und von `finalize()` ueber
die persistierte `replay_of`-Bindung gedifft wird → [Trigger 039](039-api-replay-trigger-surface.md)
Phase B end-to-end schliessbar.

## Kontext / Ist

- `POST /runs` persistiert nur `RunMetadata` (`scenario_hash`/`seed`/`tick_ms`/
  `replay_of`) — **keine Ausfuehrung**; der Request traegt nur den `scenario_hash`,
  keinen Scenario-Content.
- Es tickt **genau ein** Demo-Lauf (`demo-run-0001`); `TickLoopRegistry` ist ein
  Single-Run-Stub ([`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md)
  Decision 13).
- `finalize()` konsumiert heute nur den Runtime-Kwarg `replay_reference_run_id`,
  nicht die persistierte `RunMetadata.replay_of`.

## Kern-Decision — Scenario-Aufloesung (A1, [`ADR 0069`](../../adr/0069-multi-run-execution-and-scenario-store.md) §2.1)

Ein **Scenario-Store** keyed by `scenario_hash`: `POST /scenarios` pinnt den
kanonischen Content; der Executor loest ihn per Hash auf. `POST /runs` bleibt
hash-referenziert ([`GG-SCN-003`](../../../../spec/lastenheft.md#gg-scn-003)/[`GG-SCN-004`](../../../../spec/lastenheft.md#gg-scn-004)).
Alternativen (Inline-Body / Server-Library) verworfen.

## Slice-Schnitt (rollen-getrennt)

| Slice | Inhalt | Rolle / Artefakt |
| --- | --- | --- |
| **S0** | [`ADR 0069`](../../adr/0069-multi-run-execution-and-scenario-store.md) `Proposed → Provisional` ✓ (2026-06-18); Scenario-Aufloesung (A1) + Start-Semantik mitgetragen. `Accepted` folgt bei Implementierungs-Closure | Architect / ADR |
| **S1** ✓ | `ScenarioStorePort` + InMemory-Store + `POST /scenarios` + Hash-Mismatch-Reject — **geliefert 2026-06-18** (commit `4f3a8b2`): Intake-Bridge im Composition-Root (Hook-Inversion), Endpoint/Setup in dedizierten Sub-Modulen (God-Modul-Vermeidung, max 5 public Funktionen). Happy/Boundary/Negative-Pins, `make gates` gruen. | Implementation |
| **S2** ✓ | `RunDriverRegistry` (Generalisierung `TickLoopRegistry`) + per-Run-Driver + concurrency-Cap + Lifespan-Shutdown-all — **geliefert 2026-06-18**: `register_and_start`/`stop`/`stop_all`, `RunConcurrencyLimitError`/`RunAlreadyActiveError`, Lifespan-Naht (`finalize()`-garantiert). Pins inkl. Shutdown. | Implementation |
| **S3** ✓ | `POST /runs/{id}/start` + 404/422/409/429-Semantik + per-Run-Telemetrie-Sink — **geliefert 2026-06-18**: Scenario aus Store (S1) → Composition-Bridge `build_run_driver` (Hook-Inversion) → `RunDriverRegistry` (S2). NEU `RunStartResponse`; Pins inkl. Build-Failure-422. | Implementation |
| **S4** ✓ | **Replay-Konsumnaht (039 Phase B):** `build_run_driver` verdrahtet `replay_of` → `finalize()` difft gegen den Referenzlauf (geteilter Sink, §2.3-Verfeinerung) — **geliefert 2026-06-18**. Pin: echter Cross-Run-Diff. Schliesst 039 Phase B; Paar-Closure 039+040 mit der Wellen-Closure. | Implementation |

Postgres-Paritaet + Integration-Smoke je Slice (Replay-Disziplin: Happy/
Boundary/Negative).

## DoD

- API-Lauf laesst sich anlegen → starten → tickt → terminiert; `finalize()`
  feuert genau einmal (`run_session()`, [`ADR 0067`](../../adr/0067-run-end-seam-and-partial-run.md)).
- Ein `POST /runs replay_of=<ref>`-Lauf difft beim Lauf-Ende gegen den
  Referenzlauf (`replay_diff_status` gesetzt), **ohne** Runtime-Kwarg.
- Bounded concurrency: Ueberschuss-Laeufe typisiert rejected statt unbounded
  Task-Spawn.
- Determinismus: zwei identische Laeufe (gleicher `scenario_hash`/`seed`) leerer
  Diff ([`GG-MVP-002`](../../../../spec/lastenheft.md#gg-mvp-002)).
- `make gates` + `make docs-check` gruen; Welle-/Meilenstein-Closure zusaetzlich
  `make fullbuild`.

## Entsperrt

[Trigger 039](039-api-replay-trigger-surface.md) Phase B (S4)
+ Replay-Paar-Closure 039+040. Profitiert: Headless-Abnahme-CLI
([`GG-MVP-003`](../../../../spec/lastenheft.md#gg-mvp-003)).

## Risiken

- **Scope-Ballon** an der Scenario-Aufloesung → A3 (Server-Library) als
  Minimal-Fallback, falls A1 zu gross wird.
- **Ressourcen/Concurrency** (viele Laeufe) → Cap + Reject ([`GG-RT-001`](../../../../spec/lastenheft.md#gg-rt-001)).
- **Determinismus** unter parallelen Drivern → strikte Per-Run-Isolation
  (Clock/Random/Sink).
- **Welle-Review (durchgefuehrt, frischer Reviewer-Kontext) — Findings + Resolution:**
  - **HIGH (geloest):** Start-Endpoint-`except` fing nur
    `ScenarioError`/`SnapshotFormatError`, **nicht** die Device-Config-Fehler
    (`*ConfigError` = `GridGymError`) → 500 statt 422. Fix: `except GridGymError`
    + repraesentativer Pin (`grid_connection max_import_kw=0` → 422
    `scenario_build_failed`).
  - **MEDIUM (geloest):** (a) Execution-Seed jetzt aus `RunMetadata.seed`
    (`build_run_driver` liest die Metadata; deckt sich mit dem Replay-Preflight-
    Feld). (b) `RunDriverRegistry`-Cap zaehlt jetzt **aktive** statt registrierte
    Driver (`_evict_terminated` + `is_running`); terminierte Laeufe geben ihren
    Slot frei + sind neu startbar. (c) LOW: terminale Laeufe → 409
    `run_already_terminal`; Start-Echo `status="accepted"`.
  - **Residuen (dokumentiert, deferred):** der geteilte In-Memory-Sink ist
    unbounded + prozess-weit (Showcase; Postgres-`ReplaySnapshot` nach
    [`ADR 0048`](../../adr/0048-replay-snapshot-port-reconstruction.md) =
    Deployment-Fix), `read_ordered` ist O(n·m); **kein** Runtime-`POST /runs/{id}/
    stop` auf die `RunDriverRegistry` — Slots frei nur bei natuerlicher Termination
    / Lifespan-Shutdown (API-Laeufe haben mangels Tick-Budget kein Auto-Ende).
    Beide vor [`ADR 0069`](../../adr/0069-multi-run-execution-and-scenario-store.md)-Acceptance bewusst zu tragen (oder Folge-Slice).

## Bezug

- [`ADR 0069`](../../adr/0069-multi-run-execution-and-scenario-store.md) (Architektur).
- [`ADR 0037`](../../adr/0037-http-api-surface-pattern.md)/[`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md)/[`ADR 0045`](../../adr/0045-http-api-request-strict-validation.md)/[`ADR 0048`](../../adr/0048-replay-snapshot-port-reconstruction.md)/[`ADR 0049`](../../adr/0049-replay-lifecycle-finalize-hook.md)/[`ADR 0067`](../../adr/0067-run-end-seam-and-partial-run.md)/[`ADR 0068`](../../adr/0068-api-replay-binding-persistence.md).
- [Trigger 039](039-api-replay-trigger-surface.md) + [Trigger 040](040-replay-finalize-headless-run-end-seam.md).

## Aktivierung

Aktiviert 2026-06-18 (S0 + S1) — Plan nach `in-progress/` verschoben (rename-only).
Folge-Slices S2–S4 geliefert; die Welle-Closure (alle Slices Done + `make fullbuild`
gruen) hat den Plan 2026-06-18 nach `done/` bewegt.
