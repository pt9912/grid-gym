# Geraete-Fallback + Replay-Determinismus (`GG-SAFE-005/006`)

**Quelle:** M6-Welle-5c (SOLLTE-Items + IP/Netz-Beschraenkung;
[`../plan/planning/done/M6-welle-5c.md`](../plan/planning/done-archive/M6-welle-5c.md)).
**Stand:** 2026-06-07.

Dieses Dokument auditiert die produktive Substanz fuer die
beiden SOLLTE-Akzeptanzen `GG-SAFE-005` (Geraete-Fallback)
und `GG-SAFE-006` (Replay-Determinismus) aus dem Lastenheft
(§20). Pro ID werden Substanz-Pfade, Test-Pfade und
Lieferstatus dokumentiert.

---

## Übersicht

### `GG-SAFE-005` — Geraete-Fallback-Verhalten

Lastenheft Z. 1380-1385 verlangt: „Die Plattform SOLLTE
sichere Fallback-Zustaende unterstuetzen.
Akzeptanz: Wenn Fallback-Zustaende implementiert sind,
dokumentiert jeder betroffene Geraetetyp Ausloeser,
Zielzustand, Telemetrie und Recovery-Verhalten."

Lastenheft-Traceability Z. 2291 nennt explizit:
„`BatteryDevice.apply_command` / Sicherheitsgrenzen-
Validierung" als Ankertyp.

| Geraet | Substanz-Pfad | Test-Pfad | Status |
| ------ | ------------- | --------- | ------ |
| **Battery** | `hexagon/core/devices/battery/commands.py::validate_set_power_command` (REJECTED/LIMITED/SOC-Alarm-Outcome); `model.py::apply_command` ruft den Validator + clampt Power auf `[min_power_kw, max_power_kw]`. | `tests/unit/hexagon/core/devices/battery/test_commands.py` + Smoke `tests/integration/test_m6_welle_5c_safe_005_006_compose_smoke.py` (`test_safe_005_battery_fallback_canonical`) | ✓ **Produktiv** |
| **Load** | `hexagon/core/devices/load/commands.py::validate_set_power_command` (REJECTED/LIMITED); `model.py::apply_command` mit Power-Clamp. | `tests/unit/hexagon/core/devices/load/test_load_device.py` + Compose-Smoke `::test_safe_005_load_fallback_canonical` | ✓ **Produktiv** |
| **GridConnection** | `hexagon/core/devices/grid_connection/commands.py::validate_set_power_command` (REJECTED/LIMITED); `model.py::apply_command` mit Import/Export-Power-Clamp. | `tests/unit/hexagon/core/devices/grid_connection/test_grid_connection_device.py` + Compose-Smoke `::test_safe_005_grid_connection_fallback_canonical` | ✓ **Produktiv** |
| **PV** | `hexagon/core/devices/pv/commands.py::validate_set_power_command` (REJECTED/LIMITED); `model.py::apply_command` mit Curtail-Clamp auf `[0, p_max_kw]`. | `tests/unit/hexagon/core/devices/pv/test_pv_device.py` + Compose-Smoke `::test_safe_005_pv_fallback_canonical` | ✓ **Produktiv** |

### `GG-SAFE-006` — Replay-Diff-Determinismus

Lastenheft Z. 1387-1393 verlangt: „Nichtdeterministische
Simulationslaeufe SOLLTEN erkannt werden.
Akzeptanz: ... Replay-Diff, volatile Felder, betroffene
Ticks und Abweichungsklassifikation maschinenlesbar."

Lastenheft-Traceability Z. 2292: „Replay-Diff-Status-
Markierung — **M3 mit Replay-Source-Integration**."

| Akzeptanz-Komponente | Substanz-Pfad | Test-Pfad | Status |
| -------------------- | ------------- | --------- | ------ |
| **Replay-Diff** | `hexagon/core/replay/diff.py::diff_replay()` → `tuple[ReplayDelta, ...]`. | `tests/unit/hexagon/core/replay/test_diff.py` | ✓ **Produktiv** |
| **Volatile Felder** | `diff_replay(*, volatile_fields=None)` Parameter mit Default `_VOLATILE_FIELDS_DEFAULT = frozenset({"import_sequence"})`. | `tests/unit/hexagon/core/replay/test_diff.py` (pinnt Default + Override) | ✓ **Produktiv** |
| **Betroffene Ticks** | `ReplayDelta.tick = simulation_time // tick_ms` (Aggregation pro Tick im Diff-Algorithm). | `tests/unit/hexagon/core/replay/test_diff.py` (pinnt Tick-Aggregation) | ✓ **Produktiv** |
| **Abweichungsklassifikation** | `ReplayDeltaClassification` StrEnum mit `FACHLICH` / `VOLATIL`; `ReplayDelta.classification` pro Delta. | `tests/unit/hexagon/core/replay/test_diff.py` (pinnt beide Werte) | ✓ **Produktiv** |
| **Per-Lauf-Status-Marker (`replay_diff_status`)** | ✓ **produktiv** (M7-Welle-1b-b, [`ADR 0049`](../plan/adr/0049-replay-lifecycle-finalize-hook.md) §2.4): `TickLoop.finalize()` emittiert `metrics_port.gauge("replay_diff_status", 1.0 clean / 0.0 diverged, attributes={run_id, reference_run_id, status})` bei preflight-validem Vergleich. | `tests/integration/test_mvp_002_replay_lifecycle_smoke.py` (clean/diverged) + `tests/unit/hexagon/core/simulation/test_tick_loop_replay_finalize.py`. | ✓ **Produktiv** |
| **ReplaySource-Integration** | ✓ **produktiv** (M7-Welle-1b-a/1b-b, [`ADR 0048`](../plan/adr/0048-replay-snapshot-port-reconstruction.md)/0049): `ReplaySnapshotPort.read_samples(run_id)` rekonstruiert `expected`/`actual`-`ReplaySample`-Sequenzen aus den persistierten `telemetry_points`; der Core-`finalize()`-Hook ruft `diff_replay()` mit der expliziten `replay_reference_run_id`-Bindung. | `tests/integration/test_mvp_002_replay_snapshot_smoke.py` + `…_replay_lifecycle_smoke.py`. | ✓ **Produktiv** |

**Legende**:
- ✓ Produktiv: Akzeptanz vollstaendig erfuellt + Smoke-/Unit-
  Test pinnt das in CI.
- ⚠ Partial Lücke: Sub-Substanz existiert, voller Akzeptanz-
  Umfang nicht abgedeckt; Trigger verankert den Folge-Pfad.
- ✗ Lücke: keine produktive Substanz; Trigger verankert den
  Folge-Pfad.

---

## Detail pro ID

### `GG-SAFE-005` — Sichere Fallback-Zustaende

**Lastenheft-Akzeptanz (Z. 1380-1385)**: „Die Plattform
SOLLTE sichere Fallback-Zustaende unterstuetzen.
Akzeptanz: Wenn Fallback-Zustaende implementiert sind,
dokumentiert jeder betroffene Geraetetyp Ausloeser,
Zielzustand, Telemetrie und Recovery-Verhalten."

Die Substanz folgt einem einheitlichen Pattern an allen vier
M2-Lastenheft-Geraeten (Battery / Load / GridConnection / PV):

1. **Ausloeser** — REST-Endpoint `POST /runs/{id}/control`
   reicht `set_active_power_kw` (oder Geraete-Aequivalent)
   in `DeviceCommandPort.apply_command(...)` durch. Der
   Validator `validate_set_power_command(...)` prueft pro
   Geraet die Sicherheitsgrenzen.
2. **Zielzustand** — Outcome ist eine `dataclass(frozen=True)`
   mit einem Klassifikator (`REJECTED` / `LIMITED` /
   `ACCEPTED`) plus `applied_power_kw`. `REJECTED` laesst
   den State unveraendert; `LIMITED` clampt den Power auf
   den Sicherheits-Wertebereich (`[min, max]`,
   `[0, p_max]` etc.).
3. **Telemetrie** — Alle drei Outcome-Faelle werden ueber
   die Quality-Pipeline (`GG-SAFE-001..004`-Substanz; siehe
   [`safe-001-004-quality-pipeline.md`](safe-001-004-quality-pipeline.md))
   bzw. die `AlarmPort`-Emission abgebildet:
   - `REJECTED` → Alarm-Event mit `reason`-Code und
     `limit_value` / `limit_unit` (`"kW"` fuer Power-
     Clamps, `"pct"` fuer SOC-Alarms an Battery).
   - `LIMITED` → Alarm-Event + clamped Power-Wert,
     sodass der Lauf weitergeht statt aufzugeben.
4. **Recovery-Verhalten** — Pure-Function-Validator hat
   keinen versteckten State; sobald der naechste Command
   im Sicherheits-Wertebereich liegt, akzeptiert der
   Geraete-Adapter ihn ohne Roundtrip. Recovery ist also
   implizit „naechster konformer Command".

### `GG-SAFE-006` — Replay-Determinismus-Erkennung

**Lastenheft-Akzeptanz (Z. 1387-1393)**: „Nichtdeterministische
Simulationslaeufe SOLLTEN erkannt werden.
Akzeptanz: Wenn Erkennung nichtdeterministischer Laeufe
implementiert ist, meldet die Plattform Replay-Diff,
volatile Felder, betroffene Ticks und Abweichungsklassifikation
maschinenlesbar."

Der **Core-Diff-Algorithm** `diff_replay()` in
`src/grid_gym/hexagon/core/replay/diff.py` deckt die vier
Lastenheft-genannten Akzeptanz-Komponenten vollstaendig ab:

- **Replay-Diff** — die Funktion vergleicht zwei
  `Sequence[ReplaySample]`-Eingaben (`expected` / `actual`)
  und liefert `tuple[ReplayDelta, ...]` mit `path` /
  `tick` / `classification` pro Delta.
- **Volatile Felder** — `volatile_fields`-Parameter mit
  Default `_VOLATILE_FIELDS_DEFAULT =
  frozenset({"import_sequence"})`; ein Feldname in diesem
  Set wird als `VOLATIL` klassifiziert statt als
  `FACHLICH`, sodass Reviewer-getriebene Diff-Vergleiche
  bewusst-instabile Felder ignorieren koennen.
- **Betroffene Ticks** — `ReplayDelta.tick =
  simulation_time // tick_ms`; der Default `tick_ms=1000`
  ist Tick-Bucket-konsistent zur Lauf-Loop.
- **Abweichungsklassifikation** — `ReplayDeltaClassification`
  StrEnum mit zwei Werten (`FACHLICH` / `VOLATIL`)
  maschinenlesbar pro Delta.

**Geschlossen (M7-Welle-1b-a/1b-b, [`ADR 0048`](../plan/adr/0048-replay-snapshot-port-reconstruction.md)/0049):** der
Per-Lauf-Status-Marker plus die ReplaySource-Integration sind
jetzt produktiv im Lauf-Lifecycle verankert:

- `spec/architecture.md §15` (Z. 820 + 823) listet
  `replay_diff_status` als Pflicht-Metrik. `TickLoop.finalize()`
  (Core-Spine, [`ADR 0049`](../plan/adr/0049-replay-lifecycle-finalize-hook.md) §2.1/§2.4) emittiert sie als binaeren
  `metrics_port.gauge("replay_diff_status", 1.0 clean / 0.0
  diverged, attributes={run_id, reference_run_id, status})` bei
  preflight-validem Vergleich (`GG-TERM-002/003`-MVP-Preflight
  ueber 5 `RunMetadata`-Felder; volle Matrix Carveout Trigger
  038).
- Die ReplaySource-Integration laeuft ueber den
  `ReplaySnapshotPort` ([`ADR 0048`](../plan/adr/0048-replay-snapshot-port-reconstruction.md)): `read_samples(run_id)`
  rekonstruiert `expected`/`actual`-`ReplaySample`-Sequenzen aus
  den persistierten `telemetry_points`; der `finalize()`-Hook
  difft die explizit gebundene `replay_reference_run_id` gegen
  den aktuellen Lauf. Die vier Detailfelder
  (path/expected/actual/tick/device_id/classification) emittiert
  `finalize()` maschinenlesbar via `log_port`.

[Trigger 036](../plan/planning/done-archive/036-safe-006-replay-diff-status-replay-source-integration.md)
ist damit aufgeloest (→ `done/` mit M7-Welle-1b-b-C3). Die
**oeffentliche API-Replay-Bedienung** (POST /runs `replay_of`)
bleibt separater Scope ([Trigger 039](../plan/planning/open/039-api-replay-trigger-surface.md)).

---

## Verifikation

`tests/integration/test_m6_welle_5c_safe_005_006_compose_smoke.py`
deckt mit 6 Integration-Smokes (4 SAFE-005 + 1 SAFE-006
Core-Diff + 1 SAFE-006-Integration-Audit-Pin) den Vertrag in
CI ab; das `replay_diff_status`-Lifecycle-Verhalten ist in
`tests/integration/test_mvp_002_replay_lifecycle_smoke.py`
(+ `tests/unit/…/test_tick_loop_replay_finalize.py`) end-to-end
gepinnt. Plus die `make gates`-Aggregat-Substanz (Lint, Format,
Typecheck, Arch-Check, Tests, Coverage, Dep-Audit, NoQA,
SPDX, plus Image-Audit ueber `make ci` / `make fullbuild`).

---

## Architektur-Bezug

- [ADR 0011 — Schaerfung ohne Abloesung](../plan/adr/0011-schaerfung-ohne-abloesung.md):
  Pattern fuer additive Sicherheitsgrenzen-Validierung am
  Geraete-Kern, ohne den `DeviceCommandPort`-Vertrag
  aufzuweichen.
- [`safe-001-004-quality-pipeline.md`](safe-001-004-quality-pipeline.md):
  Schwester-Audit fuer die Quality-Pipeline-Substanz, die
  die `LIMITED`/`REJECTED`-Outcomes telemetriert.
- [`safe-007-008-sim-prod-input-validation.md`](safe-007-008-sim-prod-input-validation.md):
  Schwester-Audit fuer die MUSS-Akzeptanzen aus der
  Welle-5b.
- [ADR 0048 — ReplaySnapshotPort](../plan/adr/0048-replay-snapshot-port-reconstruction.md)
  + [ADR 0049 — Replay-Lifecycle](../plan/adr/0049-replay-lifecycle-finalize-hook.md):
  loesen die `GG-SAFE-006`-Lauf-Lifecycle-Verankerung (Trigger
  036 → `done/`).
- [`replay-determinism-e2e.md`](replay-determinism-e2e.md):
  `GG-MVP-002`-E2E-Replay-Determinismus-Audit (Schwester-Doku).
- `spec/architecture.md §15` (Z. 820 + 823) —
  Architektur-Vorgabe fuer `replay_diff_status`-Metrik.
