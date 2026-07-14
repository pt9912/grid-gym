# 080 — Delivery-Audit: Simulation-/Replay-Lifecycle (Verifikations-Slice)

**Status:** **Abgeschlossen (`done/`, 2026-07-14). Doku-only, kein Release.** Erster
**Verifikations-Slice** (User-Entscheid 2026-07-14): stellt für einen `— | Trace`-MUSS-
Cluster fest, ob das Feature schon implementiert ist — verankert die verifizierten IDs
hier, sodass `make doc-trace` sie als geliefert attribuiert (aus „—" wird „Slice 080",
**abgeleitet, nicht handgepflegt**). **Ergebnis: alle 6 erfüllt, 0 versteckte Lücken**,
2 dokumentierte deferred *Surfaces* (Trigger-Kandidaten).
**Datum:** 2026-07-14

---

## Motivation

`make doc-trace` zeigt eine Reihe MUSS-Anforderungen als `— | Trace | ok`: design-/test-
gemappt (non-orphan), aber **ohne Liefervehikel** in der `Slices`-Spalte — weil die
eingefrorenen M1..M8-Docs die IDs nicht namentlich nennen (`docs/plan/traceability.md`
§27-Caveat: die `Slices`-Spalte ist advisory, „belastbarer Liefer-Status steht im Code/
Tests"). Das ist genau das Muster, das bei den Quality-Faults
([`070`](070-gg-fault-004-frequency-drop.md)/[`071`](071-gg-fault-003-nan-injection.md)/[`072`](072-gg-fault-002-stale-data.md))
drei echte MUSS-Lücken verbarg — **dort** war es eine echte Feature-Lücke, nicht bloss
eine fehlende Attribution.

> **Konventions-Warnung (dieser Slice-Typ):** `doc-trace` attribuiert **jede** in einem
> Slice-Doc genannte Requirement-ID an diesen Slice — es kann „geliefert" nicht von „als
> Beispiel erwähnt" unterscheiden. Ein Verifikations-Slice darf deshalb **nur** die IDs
> nennen, die er tatsächlich verifiziert; Beispiele/Referenzen laufen über **Slice-Nummern**
> (deren Dateinamen sind lowercase und matchen das Uppercase-ID-Pattern nicht).

**Vehikel = Slice, kein neues Dokument** (slice-getrieben, [`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md)):
ein Verifikations-Slice geht einen Requirement-Cluster gegen Code+Test durch. Findet er
„gebaut" → IDs hier verankert (doc-trace-Attribution, driftfrei — die ID landet einmal im
`done/`-Doc, doc-trace leitet fortan ab; **kein Rückfall in die in Slice 066 entfernte
handgepflegte §27.2-Tabelle**). Findet er „Lücke" → Folge-Implementierungs-Slice (Muster
[`070`](070-gg-fault-004-frequency-drop.md)/[`071`](071-gg-fault-003-nan-injection.md)/[`072`](072-gg-fault-002-stale-data.md)).

## Scope (Familie: Simulation-/Replay-Lifecycle)

| Anforderung | Prio | Verdict | Code-Artefakt | Test-Beleg |
| --- | --- | --- | --- | --- |
| [`GG-SIM-004`](../../../../spec/lastenheft.md#gg-sim-004) Parallele Geräte-Sim (determ. im Tick) | MUSS | ✅ geliefert | `hexagon/core/simulation/scheduler.py` (Tie-Break-Sort), `tick_loop.py` (Device-Iteration je Tick) | `tests/unit/hexagon/core/simulation/test_scheduler.py` — `test_permutation_of_inputs_yields_identical_pop_order` (Permutations-Invarianz) |
| [`GG-SIM-006`](../../../../spec/lastenheft.md#gg-sim-006) Replay-Simulation | MUSS | ✅ geliefert | `tick_loop.py` konsumiert `ReplaySnapshotPort` als Eingabe in **denselben** Tick-Prozessor (Akzeptanz wörtlich) | `tests/integration/test_mvp_002_replay_lifecycle_smoke.py` — `test_two_run_demo_replay_is_clean` |
| [`GG-SIM-008`](../../../../spec/lastenheft.md#gg-sim-008) Pause/Resume | MUSS | ✅ geliefert | `tick_loop.py` `_control_state == "paused"` → `tick()` No-op ([`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md)) | `tests/unit/hexagon/core/simulation/test_tick_loop_control.py` (paused = kein Tick-Fortschritt) |
| [`GG-SIM-009`](../../../../spec/lastenheft.md#gg-sim-009) Exportierbare Läufe | MUSS | ✅ Substanz geliefert (⚠) | `hexagon/core/serialization/canonical.py` + `snapshot_codec.py` (dokumentiertes canonical-JSON-Format) + Persistenz (Metadaten/Telemetrie/Alarme) + Golden-Files | Datenvollständigkeit **bewiesen** durch funktionierenden Replay-Determinismus + Golden-Vergleich (`test_mvp_002_replay_lifecycle_smoke.py`) — der Export enthält per Konstruktion „alle für det. Replay + Golden nötigen Daten" |
| [`GG-REPLAY-005`](../../../../spec/lastenheft.md#gg-replay-005) Replay-Pause/Resume (API+CLI) | SOLLTE | ⚠ Teil (akzeptiert) | API: geteilter Live-/Replay-Tick-Loop ([`GG-ARCH-008`](../../../../spec/lastenheft.md#gg-arch-008)) + `POST /control`; **CLI = dokumentierter Stub** (`__main__.py`: „`replay` ist M6+-Forward-Pointer") | `test_tick_loop_control.py` (API-Pfad) |
| [`GG-REPLAY-006`](../../../../spec/lastenheft.md#gg-replay-006) Replay-Delta-Analyse | SOLLTE | ✅ geliefert | `hexagon/core/replay/diff.py` (Feld-für-Feld-Vergleich, `replay_diff_status`-Verdict + Delta-Liste) | `test_mvp_002_replay_lifecycle_smoke.py::test_diverged_runs_emit_status_zero_with_safe_006_details` |

## Befund

- **Alle 4 MUSS + 2 SOLLTE erfüllt.** Keine versteckte funktionale Lücke wie beim
  GG-FAULT-Cluster — die Features existieren + sind akzeptanz-getestet.
- **Zwei dokumentierte deferred *Surfaces*** (nicht Substanz-Lücken):
  1. [`GG-SIM-009`](../../../../spec/lastenheft.md#gg-sim-009): der HTTP-`GET /runs/{id}/snapshot`-Endpoint ist ein
     Welle-1-Stub. Die **Anforderung** verlangt „Export in dokumentiertem Format", nicht
     diesen Endpoint — die Substanz (canonical-Snapshot + Golden) ist erfüllt. Der bequeme
     HTTP-Export bleibt Trigger-Kandidat.
  2. [`GG-REPLAY-005`](../../../../spec/lastenheft.md#gg-replay-005): CLI-Replay-Pause/Resume ist ein dokumentierter
     M6+-Stub. SOLLTE-**konditional** („wenn implementiert, dann API+CLI") → akzeptierter
     Teil-Stand, kein Bruch. Trigger-Kandidat für eine Replay-CLI.

## DoD

- Jede In-Scope-Anforderung hat ein Code- **und** Test-Artefakt oder einen dokumentierten
  Deferral-Grund (Tabelle oben). ✅
- IDs im `done/`-Slice-Doc verankert → `make doc-trace` attribuiert sie an Slice 080
  (`— | Trace` → `Slice 080 | Trace`). ✅ (verifiziert)
- Doku-only, **kein Runtime-Delta → kein Release** (Muster [Kein-Doku-only-Release]).

## Bezug

- [`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) (slice-getrieben),
  [`docs/plan/traceability.md`](../../traceability.md) (§27-Caveat: `Slices`-Spalte advisory),
  [`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md) (Run-Control/Pause/Resume).
- Folge-Slices dieses Musters für die übrigen `— | Trace`-MUSS-Familien
  (`GG-OTEL-*`, `GG-PERSIST-*`, `GG-FAULT-*`, `GG-GRID-*`, `GG-DEMO-*`, `GG-DEPLOY-*`, …).
