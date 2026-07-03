# 055 — E2E-Sensor: produktiver Profil-Pfad → Replay-Preflight

**Status:** **Done** (Closure 2026-07-03 — Sensor gruen im Bestand,
Release-Entscheidung **nein** vollzogen: Test-only-Delta unter
`[Unreleased]`). Direkt aktiviert 2026-07-03 per Maintainer-Mandat;
Quelle: INFO-Befund des unabhaengigen Slice-038-Post-Release-Reviews.
**Datum:** 2026-07-03
**Release-Entscheidung:** **nein** — reines Test-Delta (Integration-
Sensor) ohne Runtime-Aenderung; sammelt unter
[`CHANGELOG.md`](../../../../CHANGELOG.md) `[Unreleased]`
([`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) D-3, Regel „kein Doku-only-Release").
**Quelle:** Slice-038-Review-INFO
([`../done/038-gg-term-002-003-full-equality-matrix.md`](../done/038-gg-term-002-003-full-equality-matrix.md)):
„Kein Test faehrt POST /runs (mit dem real registrierten
Composition-Profil) → start → finalize durch den Preflight; die
Kette ist nur stueckweise gepinnt."

---

## Scope

Ein Integrationstest, der die produktive Kette am Stueck faehrt —
mit dem **real registrierten** Composition-Profil aus
`grid_gym.composition.asgi` (nicht mit Fixture-Werten):

1. App ueber den Composition-Entrypoint (Import registriert
   Profil + Scenario-Intake + Driver-Builder per Hook-Inversion,
   [`ADR 0054`](../../adr/0054-composition-asgi-entrypoint-and-scenario-hook.md)).
2. `POST /scenarios` (Intake, [`ADR 0069`](../../adr/0069-multi-run-execution-and-scenario-store.md) §2.1) →
   `POST /runs` (Referenzlauf A) → `POST /runs/{A}/start` → running.
3. `POST /runs` mit `replay_of=A` (Replay-Lauf B,
   [`ADR 0068`](../../adr/0068-api-replay-binding-persistence.md)) → start → running; Stop beider
   Laeufe ueber den Lifespan-Shutdown
   (`RunDriverRegistry.stop_all()`) — per-Run-Driver haben bewusst
   keine HTTP-Stop-Surface (`/control` ist die Demo-Single-Run-
   Naht ueber die `TickLoopRegistry`); der `finalize()`-Preflight
   von B laeuft real auf der Run-End-Naht
   ([`ADR 0067`](../../adr/0067-run-end-seam-and-partial-run.md) §2.4).
4. **Asserts auf der persistierten Metadata-Ebene** (= der
   Preflight-Vertrag aus [`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) §2.6):
   - beide Laeufe tragen das **reale** Profil: `enabled_adapters ==
     ("http_api", "persistence_inmemory")`, `config_hash ==
     config_hash_for(max_age_ms=None)` (ConfigView v1),
     `platform_arch` = kanonisierte `platform.machine()` (nicht leer),
     `sim_start_time == 0`;
   - alle 9 Preflight-Felder sind zwischen A und B gleich und die
     Vollfelder nicht-fehlend → der reale Preflight hat eine
     valide Vergleichsbasis (kein `missing`-/Mismatch-Reject);
   - `B.replay_of == A` (persistente Bindung).
5. Der Test traegt den `replay`-pytest-Marker (zahlt auf die
   [`054`](../open/054-pytest-marker-drift-sensor-targets.md)-Sensor-Familie ein).

## Anti-Scope (dokumentierte Grenze)

- **Kein Clean-Diff-Assert ueber die API:** API-Laeufe haben kein
  Tick-Budget (Auto-`completed` ist explizit out-of-scope,
  [`ADR 0049`](../../adr/0049-replay-lifecycle-finalize-hook.md) §7) — Wall-Clock-Stops liefern
  nicht-deterministische Tick-Zahlen, ein `replay_diff_status`-
  Vergleich waere flaky. Der Clean-Diff-Beleg lebt weiterhin im
  Zwei-Lauf-Lifecycle-Smoke
  (`test_mvp_002_replay_lifecycle_smoke.py`) und im
  `build_run_driver`-Unit-Pin. Ein deterministisches API-Tick-
  Budget waere eine eigene Folge-Arbeit
  ([`ADR-0011`](../../adr/0011-schaerfung-ohne-abloesung.md)-Schaerfung an
  [`ADR 0049`](../../adr/0049-replay-lifecycle-finalize-hook.md)).
- **Kein MetricsPort-Wiring** fuer `build_run_driver` — der
  produktive API-Pfad emittiert heute keinen
  `replay_diff_status`-Gauge; das Nachruesten waere Runtime-Delta
  und damit ein eigener Slice.

## DoD-Checkliste (abgehakt 2026-07-03)

- [x] Integrationstest
      `tests/integration/test_slice_055_profile_preflight_e2e.py`
      faehrt die Kette gegen den echten Composition-Entrypoint;
      `replay`-Marker (zweiter Traeger nach Slice 038).
- [x] `make test-integration` gruen (165 passed / 4 skipped) +
      `make test-replay` gruen + `make gates` gruen +
      `make docs-check` gruen.
- [x] CHANGELOG `[Unreleased]`-Eintrag (Test-Sensor).
- [x] Self-Move nach `done/` (reiner `git mv`) + Link-/Bestand-
      Pflege; Release-Entscheidung **nein** vollzogen (Test-only,
      kein Runtime-Delta — Regel „kein Doku-only-Release").

## Verification Evidence (Kurzform, 2026-07-03)

- Scope: Slice `055`; IDs [`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/003,
  [`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) §2.3-§2.6,
  [`ADR 0067`](../../adr/0067-run-end-seam-and-partial-run.md) §2.4 (Shutdown-Naht),
  [`ADR 0068`](../../adr/0068-api-replay-binding-persistence.md)/[`ADR 0069`](../../adr/0069-multi-run-execution-and-scenario-store.md) (API-Pfad).
- Sensors: `make test-integration` 165 passed / 4 skipped;
  `make test-replay` Exit 0; `make gates` gruen; `make docs-check`
  263 Dateien / 0 Befunde. Nicht ausgefuehrt: `make fullbuild`
  (kein Runtime-/Image-Delta; Test-only).
- Replay/Golden: neuer Case (produktiver Profil-Pfad); keine
  bestehenden Cases geaendert; Anti-Scope Clean-Diff dokumentiert.
- Carveouts: neu keine; [`054`](../open/054-pytest-marker-drift-sensor-targets.md)
  unveraendert offen (dieser Slice liefert den zweiten
  `replay`-Marker-Traeger, nicht den Sweep).

## Wandert nach

`done/`, sobald der Sensor gruen im Bestand ist.
