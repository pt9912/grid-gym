# ADR 0069 — Multi-Run-Execution: per-Run-Driver + Scenario-Store (Accepted)

**Status:** Accepted — die Validierung lief ueber S1..S4 des
[Slice-Plans](../planning/done/multi-run-execution-path.md) (geliefert + frischer
Welle-Review, [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md) §2);
mit der Wellen-Closure 2026-06-18 sind `make gates`/`make docs-check`/`make fullbuild`
gruen — die A1-/Expliziter-Start-Richtung ist damit immutable beschlossen
(A3-Fallback verworfen, §3).
**Datum:** 2026-06-18
**Status geaendert am:** 2026-06-18 — `Proposed → Provisional` (S0; Owner-
Mittragung der A1-/Expliziter-Start-Richtung), dann `Provisional → Accepted`
(Wellen-Closure; S1..S4 geliefert + Review-Findings adressiert, gates gruen).
**Letzte inhaltliche Aenderung:** 2026-06-18 — §2.3 verfeinert (Telemetrie-Sink
**geteilt**, keyed by `run_id`, statt separater Sink-Objekte; Seed-Quelle
praezisiert) + §2.5 In-Memory-vs-Postgres-Replay-Realisierung ergaenzt. Pre-
Acceptance-Schaerfung ([`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md) §4), vor S4.
**Bezug:**

- [`ADR 0039`](0039-run-control-and-status-tracking.md) Decision 13 —
  `TickLoopRegistry`/Driver als Single-Run-Stub; diese ADR hebt sie additiv auf
  Multi-Run (kein Supersedes, Pattern [`ADR 0011`](0011-schaerfung-ohne-abloesung.md)).
- [`ADR 0068`](0068-api-replay-binding-persistence.md) §2.4 — der
  `finalize()`-Konsum der persistierten `replay_of`-Bindung (Phase B) hing am
  Run-Execution-Pfad; diese ADR liefert ihn.
- [`ADR 0067`](0067-run-end-seam-and-partial-run.md) — driver-unabhaengige
  Run-End-Naht (`run_session()`), auf der die per-Run-Ausfuehrung aufsetzt.
- [`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) §2.2 — `finalize()`-
  Konsumnaht, hier end-to-end aktiviert.
- [`ADR 0048`](0048-replay-snapshot-port-reconstruction.md) —
  `ReplaySnapshotPort` (Referenz-Sample-Rekonstruktion).
- [`ADR 0037`](0037-http-api-surface-pattern.md) — HTTP-Surface; NEU
  `POST /scenarios` + `POST /runs/{id}/start`.
- [`ADR 0045`](0045-http-api-request-strict-validation.md) — Strict-Request-
  Mode fuer die neuen Request-Bodies.
- [`ADR 0002`](0002-language-and-build-stack.md) — Architektur-Gates
  (`make arch-check`, Hexagonal-Reinheit).
- [Trigger 039](../planning/done/039-api-replay-trigger-surface.md)
  (entsperrt) + [Trigger 040](../planning/done/040-replay-finalize-headless-run-end-seam.md)
  (Schwester-Slice).

---

## 1. Kontext

`POST /runs` ([`GG-API-001`](../../../spec/lastenheft.md#gg-api-001)) persistiert
heute nur `RunMetadata` (`scenario_hash`/`seed`/`tick_ms`/`replay_of`) — **ohne
Ausfuehrung**. Getickt wird **genau ein** Demo-Lauf (`demo-run-0001`), gebaut aus
einer Scenario-YAML (Env-Var-Pfad) und getrieben von **einem**
`DemoTickLoopDriver`; die `TickLoopRegistry` ([`ADR 0039`](0039-run-control-and-status-tracking.md)
Decision 13) ist ein Single-Run-Stub. Zwei Folgen:

1. Ein API-erstellter Lauf wird nie gebaut/getickt — der `scenario_hash` im
   Request ist nur eine Referenz, der Server kann daraus **keinen** Scenario-
   Content rekonstruieren (kein Store keyed by Hash).
2. [`ADR 0068`](0068-api-replay-binding-persistence.md) §2.4 (Phase B) bleibt
   blockiert: `finalize()` konsumiert die persistierte `replay_of`-Bindung erst,
   wenn fuer einen API-Lauf ein `TickLoop` gebaut wird.

`Multi-Run-Driver-Registry` ist bisher bewusst Anti-Scope (M5-Welle-5). Diese ADR
hebt den Anti-Scope auf — als Vorbedingung fuer die Phase-B-Schliessung.

---

## 2. Entscheidung

### §2.1 Scenario-Store (Variante A1) — Content-Aufloesung per Hash

NEU driven `ScenarioStorePort.get(scenario_hash) -> Scenario | None` + InMemory-
und Postgres-Adapter; NEU `POST /scenarios` nimmt den kanonischen Scenario-Body,
kanonisiert ihn ueber den bestehenden I/O-freien `load_scenario`, pinnt den
Content unter seinem `scenario_hash` ([`GG-SCN-003`](../../../spec/lastenheft.md#gg-scn-003)/[`GG-SCN-004`](../../../spec/lastenheft.md#gg-scn-004))
und echot den Hash. Client-Hash ≠ server-berechneter Hash → **HTTP 422**.
`POST /runs` bleibt **unveraendert** hash-referenziert; der Executor loest den
Content per Hash auf. Inline-Body (A2) und Server-Library (A3) verworfen —
Begruendung §3.

### §2.2 RunDriverRegistry — per-Run-Lifecycle + bounded concurrency

Generalisierung der `TickLoopRegistry` zu einem per-`run_id`-Driver-Mapping:
registriert/startet/stoppt einen Driver je aktivem Lauf. **Bounded concurrency**
(konfigurierbares Maximum aktiver Laeufe; Ueberschuss → typisierter Reject statt
unbounded Task-Spawn, anschluss an [`GG-RT-001`](../../../spec/lastenheft.md#gg-rt-001)-
Backpressure). Lifespan-Shutdown stoppt **alle** Driver; jeder `finalize()` ist
ueber `run_session()` ([`ADR 0067`](0067-run-end-seam-and-partial-run.md))
garantiert.

### §2.3 Per-Run-Isolation (Determinismus)

Jeder Lauf bekommt **eigenen** Clock + Random-Root; **kein** geteilter
Determinismus-State zwischen parallelen Laeufen
([`GG-MVP-002`](../../../spec/lastenheft.md#gg-mvp-002)). Der `RandomPort`-
Wurzelseed kommt aus `scenario.simulation.seed` — das Scenario (hash-
identifiziert) ist die Quelle der Sim-Parameter (wie `tick_ms`,
[`GG-SIM-002`](../../../spec/lastenheft.md#gg-sim-002)); `RunMetadata.seed`
([`GG-SEED-001`](../../../spec/lastenheft.md#gg-seed-001)) ist der protokollierte
Request-Wert. `build_tick_loop` wird pro Lauf aufgerufen.

**Telemetrie-Sink: geteilt, keyed by `run_id`** (S4-Verfeinerung). Der
Telemetrie-Sink + die `ReplaySnapshotPort`-Sicht darueber sind **nicht** separate
Objekte je Lauf, sondern ein **gemeinsamer** Store, der pro `run_id` isoliert
liest (`read_ordered(run_id)`). Grund: der Replay-Diff (§2.5) liest in **einer**
`replay_snapshot`-Instanz die Samples **beider** Laeufe (`reference_run_id` +
eigener `run_id`); separate Sink-Objekte je Lauf machten den Cross-Run-Diff
unmoeglich. Die Isolation bleibt ueber den `run_id`-Key gewahrt; nur Clock und
Random-Root sind objekt-getrennt je Lauf.

### §2.4 Run-Start-Semantik — explizit

NEU `POST /runs/{id}/start` baut den per-Run-Loop, registriert + startet den
Driver. **409** wenn bereits laufend/terminal; **404/422** wenn kein Scenario-
Content im Store. Auto-Start bei Create verworfen — er wuerde jede `POST /runs`
eine Ressource binden (§3).

### §2.5 Replay-Konsumnaht = Slice 039 Phase B

Beim per-Run-Loop-Bau liest der Executor `metadata.replay_of`; ist es gesetzt,
verdrahtet er `replay_reference_run_id = metadata.replay_of` + `replay_snapshot`
(Referenz-Samples via [`ADR 0048`](0048-replay-snapshot-port-reconstruction.md)).
`finalize()` ([`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) §2.2) difft an
der `run_session()`-Naht. Der Runtime-Kwarg `replay_reference_run_id` bleibt
**expliziter Override** (Test/Demo; byte-stabil: `replay_of=None` → no-op). Damit
konsumiert `finalize()` die **persistierte** Bindung end-to-end →
[Trigger 039](../planning/done/039-api-replay-trigger-surface.md) Phase B
erfuellt; das Replay-Paar 039+040 schliesst.

**Sample-Quelle der Referenz.** In-Memory (diese Welle): die Referenz-Samples
liegen im **geteilten** Telemetrie-Sink (§2.3, keyed by `run_id`) — der
Referenzlauf muss im selben Prozess gelaufen sein. Deployment-Pfad: der
Postgres-`ReplaySnapshotAdapter` ([`ADR 0048`](0048-replay-snapshot-port-reconstruction.md))
rekonstruiert die Referenz aus der persistierten Telemetrie — **deferred** (kein
Postgres-Adapter in dieser Welle).

### §2.6 Hexagonal-Reinheit

`ScenarioStorePort` ist ein driven Port; Store/Registry/Driver leben im Adapter-
Ring. Der Core-Spine (`TickLoop`/`finalize()`) bleibt **unveraendert** — er
konsumiert bereits `replay_reference_run_id`/`run_repository`; die persistierte
Aufloesung passiert im Adapter-Wiring (alternativ ein minimaler Core-Lookup
`run_repository.get(run_id).replay_of` — offene S4-Plan-Decision). `make
arch-check` ([`ADR 0002`](0002-language-and-build-stack.md)) verifiziert die
Schichtung.

---

## 3. Begruendung

- **A1 (Store) statt A2/A3.** Die hash-referenzierte `POST /runs`-Surface
  ([`ADR 0037`](0037-http-api-surface-pattern.md)) bleibt schlank; die
  `scenario_hash`-Identitaet bleibt die Lauf-Klammer ([`GG-SCN-003`](../../../spec/lastenheft.md#gg-scn-003)).
  Inline-Body (A2) blaeht jeden Run-Request; Server-Library (A3) sperrt Clients
  auf vorinstallierte Scenarios — beides verfehlt die API-getriebene
  Reproduzierbarkeit.
- **Expliziter Start.** `POST /runs` (Buchung) von `POST /runs/{id}/start`
  (Ressourcen-Allokation) zu trennen, haelt Create idempotent + billig und macht
  die concurrency-Grenze am Start-Pfad durchsetzbar.
- **Per-Run-Isolation.** Determinismus ([`GG-MVP-002`](../../../spec/lastenheft.md#gg-mvp-002))
  verlangt, dass parallele Laeufe sich keinen Clock/Random teilen — sonst
  korreliert die Tick-Reihenfolge.
- **Schaerfung ohne Supersedes ([`ADR 0011`](0011-schaerfung-ohne-abloesung.md)).**
  [`ADR 0039`](0039-run-control-and-status-tracking.md)/[`ADR 0049`](0049-replay-lifecycle-finalize-hook.md)/[`ADR 0068`](0068-api-replay-binding-persistence.md)
  bleiben textlich unveraendert; diese ADR ergaenzt das Execution-Subsystem
  additiv.

---

## 4. Reichweite

- NEU `ScenarioStorePort` + InMemory/Postgres-Adapter + `POST /scenarios`
  (`_schemas.py`/`app.py`).
- NEU `RunDriverRegistry` (Generalisierung `TickLoopRegistry`) + per-Run-Driver-
  Generalisierung von `DemoTickLoopDriver` + concurrency-Cap + Lifespan-
  Shutdown-all.
- NEU `POST /runs/{id}/start` + 409/404/422-Semantik.
- Replay-Konsum-Wiring (Slice 039 Phase B) + per-Run-Telemetrie-Sink.
- Happy/Boundary/Negative-Pins je Slice + Postgres-Integration-Smokes.
- **Unberuehrt:** Core-`TickLoop`/`finalize()`/`diff_replay()`,
  `control_state`-Matrix ([`ADR 0039`](0039-run-control-and-status-tracking.md)),
  der einzelne Demo-Lauf-Pfad.

---

## 5. Konsequenzen

- **Positiv:** API-erstellte Laeufe sind ausfuehrbar; Slice 039 Phase B wird
  schliessbar; der Headless-Pfad ([`GG-MVP-003`](../../../spec/lastenheft.md#gg-mvp-003))
  bekommt ein produktives Multi-Run-Substrat.
- **Neutral:** neue API-Surface (`POST /scenarios`, `POST /runs/{id}/start`) +
  ein Scenario-Store-Adapter.
- **Risiko:** Ressourcen unter vielen parallelen Laeufen → durch concurrency-Cap
  + Reject begrenzt; Determinismus durch Per-Run-Isolation gewahrt.

---

## 6. Nicht Gegenstand dieser ADR

- **Auto-`completed`-Transition** / Tick-Budget ([`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) §7).
- **Asynchroner/entkoppelter Diff** ([`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) §2.6).
- **Multi-Node/verteilte Laeufe** ([Trigger 037](../planning/open/037-deploy-007-010-multi-node-deployment.md)).
- **UI fuer Multi-Run** (eigener Scope).
