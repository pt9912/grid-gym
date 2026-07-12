# 072 — Dedizierter `stale_data`-Fault (Stale Data)

**Status:** Done — geliefert 2026-07-12
([`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) §2.3,
Slice B). Design entschieden 2026-07-11.
**Datum:** 2026-07-11 (geplant) / 2026-07-12 (geschlossen)
**Quelle:** GG-FAULT-Konsolidierung (RTM meldete 0 Waisen, verbarg die Luecke).
[`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002) (MUSS) hatte keinen
dedizierten Fault-Typ. Slice A ([`071`](071-gg-fault-003-nan-injection.md),
`nan_injection`) lieferte die **Foundation** (metrik-adressierte Quality-Fault-
Spine-Stage `QualityFaultRuntime` + `_apply_quality_fault_stage`, Validator-Muster,
Whitelist-Entkopplung). **Dieser Slice B** ergaenzte nur das **stateful
stale-Verhalten** obenauf.

---

## Kontext / Befund

[`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002)-Akzeptanz: „Ein
Stale-Data-Fault kann fuer ein Ziel und eine Metrik aktivieren, dass der letzte
gueltige Wert weitergeliefert wird, bis `max_age` ueberschritten ist. Danach wird
der Qualitaetsstatus `stale` gesetzt."

Das ist der **zweite metrik-adressierte Quality-Fault** (Zwilling zu
[`GG-FAULT-003`](../../../../spec/lastenheft.md#gg-fault-003) `nan_injection`).
Der Unterschied zu Slice A: `stale_data` ist **stateful** — es braucht einen
per-`(device_id, metric)` **Last-Value-Cache** und dessen **opt-in
Snapshot-Serialisierung**. Das ist die von
[`ADR 0053`](../../adr/0053-comm-failure-wrapper-missing-quality-alarm.md) §7
reservierte, jetzt konkret geforderte additive Schaerfung.

## Tranchen ([`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) §2.1/§2.3/§2.5/§2.7)

- **C1 — Konstante:** `FAULT_TYPE_STALE_DATA = "stale_data"` als Single Source in
  `hexagon/core/domain/fault.py` + Re-Export `types.py`. (Der
  [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) §2.1-
  Payload-Vertrag nennt sie bereits.)
- **C2 — Validator:** fuer `type == "stale_data"` MUSS `payload` `metric: str`
  **und** `max_age_ms: int > 0` tragen (Nachbar zu `_assert_nan_injection_payload`
  in `hexagon/core/scenario/validator.py`; typisierter Fehler, kein stiller
  Unsinn).
- **C3 — Runtime/Stage:** `QualityFaultRuntime` (aus Slice 071) um `stale_data`
  erweitern:
  - per-`(device_id, metric)` **Last-Valid-Value-Cache** `(value, sim_time)`.
  - **Update-Regel:** liegt fuer `(device_id, metric)` **kein** aktiver
    `stale_data`-Fault an und ist der Punkt `Quality.VALID` → `(value, sim_time)`
    cachen. **Reihenfolge beachten** (Risiko unten): Cache mit dem *echten*
    Vorwert fuellen, nicht mit dem eingefrorenen.
  - **Aktiv:** emittierter Wert → gecachter Last-Valid-Wert; solange
    `(now − cached_sim_time) ≤ max_age_ms` Quality unveraendert; sobald
    `(now − cached_sim_time) > max_age_ms` (strikt `>`,
    [`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md) §2.5) →
    `quality=STALE`. Severity-Override: `STALE`(3) ersetzt nur Niedrigeres.
  - **Kein gueltiger Vorwert** (Fault ab Tick 0) → keine Wert-Weiterlieferung,
    nur `STALE`-Markierung ab `max_age` (ehrliche Grenze,
    [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) §2.3).
- **C4 — Snapshot:** Last-Value-Cache **opt-in** im `TickLoop`-Snapshot
  serialisieren (leer/abwesend ohne aktiven Quality-Fault → byte-identisch, kein
  Versions-Bump; Muster [`070`](070-gg-fault-004-frequency-drop.md)/[`071`](071-gg-fault-003-nan-injection.md)-Opt-in).
  **Neu ggue. Slice A** (dort war der Runtime-State rein transient — hier muss der
  Cache den Roundtrip ueberleben, damit Resume mitten im Stale-Fenster den
  letzten gueltigen Wert nicht verliert).
- **C5 — Whitelist:** `stale_data` in `_QUALITY_FAULT_TYPES`
  (`composition/_demo_scenario_setup.py`) + `_METRIC_ADDRESSED_FAULT_TYPES`
  (`adapters/driving/http_api/_runs_action_router.py`) — analog Slice 071.
- **C6 — Kein Alarm:** [`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002)
  fordert **nur** `quality=stale` ([`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) §2.5;
  Alarm-bei-STALE ist [`GG-SAFE-003`](../../../../spec/lastenheft.md#gg-safe-003)-Scope).
- **C7 — Tests:** inject/Window/Last-Value-Forwarding/`max_age`-Grenze (`>` stale
  / `==` nicht / frisch nicht)/kein-Vorwert-Markierung/Severity/Snapshot-Roundtrip
  mit+ohne Fault/byte-identisch-ohne-Fault/Determinismus/Koexistenz mit der
  `max_age`-Stage ([`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md)).
- **C8 — Doku + Closure:** `traceability.md` §27.3-Zeile
  [`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002) = Unit Test;
  CHANGELOG `[Unreleased]`; Roadmap-Nachzug; Self-Move nach `done/`.

## DoD

- [x] `stale_data` als dedizierter Fault-Typ; letzter gueltiger Wert wird
      weitergeliefert, bis `max_age` ueberschritten → `quality=STALE`.
- [x] Last-Value-Cache **opt-in** im Snapshot (byte-identisch ohne Quality-Fault,
      kein Versions-Bump); Resume mitten im Fenster verliert den Vorwert nicht.
- [x] `make gates`, `make docs-check`, `make doc-trace`, `make test-determinism`,
      `make accept-pin-check` gruen; `doc-trace` zeigt
      [`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002) abgedeckt.
- [x] `traceability.md` §27.3 + CHANGELOG `[Unreleased]`.
- [x] Adversarialer statischer Review (read-only, kein uv/pip/python) vor Commit.

**Release-Entscheidung:** nein — Sammlung unter `[Unreleased]` zusammen mit
[`070`](070-gg-fault-004-frequency-drop.md)/[`071`](071-gg-fault-003-nan-injection.md)
(SemVer-Ziel Minor, additiv). Kein eigener Tag.

## Verification-Evidence (2026-07-12)

**Rolle:** Implementation → Verifier. **Geliefert (Tranchen C1..C8):**

- **C1** `FAULT_TYPE_STALE_DATA = "stale_data"` (Single Source `hexagon/core/domain/fault.py`
  + Re-Export `hexagon/core/faults/types.py`).
- **C2** Validator `_assert_stale_data_payload`: `payload.metric: str` + `max_age_ms:
  int > 0` Pflicht (`ScenarioMissingKeysError`/`ScenarioWrongTypeError`/NEU
  `ScenarioInvalidStaleDataMaxAgeError`).
- **C3** `QualityFaultRuntime` um `stale_data` erweitert: per-`(device_id, metric)`-
  Last-Valid-Value-Cache; Cache-Update **vor** Rewrite (echter Vorwert); Forwarding
  + STALE-Grenze `(now − cached_time) > max_age_ms` (strikt); kein-Vorwert-Pfad
  (ehrliche Grenze via eigener Sim-Zeit); Severity-Override.
- **C4** Opt-in `quality_fault_last_value_cache`-Sub-Snapshot (`cache_snapshot`/
  `restore_cache`), Helper `_append_quality_fault_cache_snapshot` (C901-Budget);
  Restore in `TickLoop.from_snapshot` in den re-injizierten Runtime.
- **C5** Whitelists: `_QUALITY_FAULT_TYPES` (`_demo_scenario_setup.py`) +
  `_METRIC_ADDRESSED_FAULT_TYPES` (`_runs_action_router.py`).
- **C6** Kein Alarm ([`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) §2.5) — testgepinnt.
- **C7** Tests: `tests/unit/hexagon/core/simulation/test_tick_loop_quality_fault_stale.py`
  (Forwarding/Fenster/`>`-`==`-frisch-Grenze/kein-Vorwert/Severity/kein-Alarm/
  Snapshot-Roundtrip mit+ohne Fault/Determinismus/Koexistenz `max_age`-Stage) +
  `tests/unit/hexagon/core/scenario/test_validator_stale_data_payload.py`.
- **C8** `traceability.md` §27.3 ([`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002)
  = Unit Test) + CHANGELOG `[Unreleased]` + Roadmap-Nachzug + Self-Move
  `next/ → done/`.

**Ausgefuehrte Sensoren (Docker/make, alle gruen):** `make gates` (lint,
format-check, typecheck `--strict`, arch-check 20 Contracts, test-unit,
coverage-gate 90/85, coverage-gate-critical 90, dep-audit, noqa-gate, spdx-check),
`make test-fault` (185 passed), `make test-determinism`, `make accept-pin-check`
(Demo-Pins **unveraendert** → byte-identisch bestaetigt), `make docs-check`
(0 Befunde), `make doc-trace` (151 Reqs / 0 Waisen;
[`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002) →
[`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md),
Slice 071+072, ok). **Adversarialer statischer Review:** read-only durchgefuehrt
(kein uv/pip/python).

**Nicht ausgefuehrt:** `make ci`/`make fullbuild` (Integration/Image-Audit) — kein
Adapter-/Runtime-Image-/Persistenz-Delta in diesem Slice (rein Core-Spine +
Validator + Whitelist-Konstanten); CI bleibt das Netz.

## Betroffene Kennungen

[`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002) (MUSS), Bezug
[`GG-FAULT-003`](../../../../spec/lastenheft.md#gg-fault-003) (nan-Zwilling /
Foundation), [`GG-DATA-003`](../../../../spec/lastenheft.md#gg-data-003)
(`Quality.STALE`). Architektur:
[`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) §2.3 (fixiert),
[`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md) (`max_age`-STALE-
Praezedenz + Grenzsemantik), [`ADR 0053`](../../adr/0053-comm-failure-wrapper-missing-quality-alarm.md)
(reservierte Last-Value-Cache-Schaerfung). Code: `hexagon/core/domain/fault.py`,
`hexagon/core/faults/types.py`, `hexagon/core/simulation/quality_fault.py`,
`hexagon/core/simulation/tick_loop.py` (Snapshot), `hexagon/core/scenario/validator.py`,
`composition/_demo_scenario_setup.py`, `adapters/driving/http_api/_runs_action_router.py`.

## Risiken

- **Snapshot-Determinismus:** der Cache muss den Roundtrip ueberleben, aber
  **opt-in** bleiben (kein Versions-Bump). Muster
  [`070`](070-gg-fault-004-frequency-drop.md)/[`071`](071-gg-fault-003-nan-injection.md)
  folgen (leer → keine Keys → byte-identisch). **STOP-und-melden**, falls
  korrektes Resume mehr als ein opt-in-Feld braucht.
- **Cache-Update-Timing:** sicherstellen, dass der Cache mit dem *echten* Vorwert
  aktualisiert wird (bevor der Fault den Wert einfriert), nicht mit dem bereits
  eingefrorenen — sonst „friert" der Cache auf sich selbst.
- **Koexistenz mit der `max_age`-Stage** ([`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md)):
  beide setzen `STALE`; severity-idempotent, aber Testabdeckung fuer die
  Reihenfolge (Quality-Fault-Stage vor `max_age`-Stage).

## Review-Folge (adversarialer statischer Review, 2026-07-12)

Keine HIGH-Findings; Kern (Cache-Timing, Grenzsemantik, Severity, Determinismus,
NaN-Regression) bestaetigt. Adressiert:

- **MEDIUM-1 (behoben):** der Last-Value-Cache wurde fuer *jeden* VALID-Punkt
  eines Szenarios mit `stale_data`-Fault gefuehrt (Snapshot-Bloat, gegen die
  §2.7-Minimal-Intent). Fix: `QualityFaultRuntime._stale_targets` scoped den
  Cache auf die tatsaechlich adressierten `(device, metric)`-Paare (Test
  `test_cache_only_holds_stale_target_pairs`).
- **MEDIUM-2 / LOW-4 / LOW-5 (Test-Luecken geschlossen):** NaN+Stale auf
  demselben Key (NaN dominiert), Severity-Gate mit gefuelltem Cache (schlechtere
  Quality wird nicht wert-ersetzt), nan-only-Snapshot byte-identisch.
- **LOW-3 (dokumentiert):** die Wert-Weiterlieferung ist an den §2.6-Severity-Gate
  gebunden — ein Live-Punkt schlechterer Quality wird nicht durch den
  eingefrorenen Vorwert maskiert (Code-Kommentar in `_rewrite_point`).

**Bekannte Grenze (kein Slice-072-Regress, Slice-A-Muster):** der HTTP-Runtime-
Fault-Injection-Pfad (`POST /runs/{id}/faults`) validiert fuer metrik-adressierte
Quality-Faults **kein** `metric`/`max_age_ms` (nur Target-Existenz) — die
Payload-Schaerfung lebt allein im Scenario-Validator. Geteilt mit `nan_injection`
(Slice 071); ein Runtime-Payload-Vertrag waere additive Folgearbeit (Trigger-
Kandidat), nicht Gegenstand dieses Slices.
