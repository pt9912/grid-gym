# Geraete-Fallback + Replay-Determinismus (`GG-SAFE-005/006`)

**Quelle:** M6-Welle-5c (SOLLTE-Items + IP/Netz-Beschraenkung;
[`../plan/planning/done/M6-welle-5c.md`](../plan/planning/done/M6-welle-5c.md)).
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
| **Battery** | `hexagon/core/devices/battery/commands.py::validate_set_power_command` (REJECTED/LIMITED/SOC-Alarm-Outcome); `model.py::apply_command` ruft den Validator + clampt Power auf `[min_power_kw, max_power_kw]`. | `tests/unit/hexagon/core/devices/battery/test_commands.py` + Smoke `tests/integration/test_m6_welle_5c_safe_005_006_compose_smoke.py::test_safe_005_battery_fallback_canonical` | ✓ **Produktiv** |
| **Load** | `hexagon/core/devices/load/commands.py::validate_set_power_command` (REJECTED/LIMITED); `model.py::apply_command` mit Power-Clamp. | `tests/unit/hexagon/core/devices/load/test_commands.py` + Compose-Smoke `::test_safe_005_load_fallback_canonical` | ✓ **Produktiv** |
| **GridConnection** | `hexagon/core/devices/grid_connection/commands.py::validate_set_power_command` (REJECTED/LIMITED); `model.py::apply_command` mit Import/Export-Power-Clamp. | `tests/unit/hexagon/core/devices/grid_connection/test_commands.py` + Compose-Smoke `::test_safe_005_grid_connection_fallback_canonical` | ✓ **Produktiv** |
| **PV** | `hexagon/core/devices/pv/commands.py::validate_set_power_command` (REJECTED/LIMITED); `model.py::apply_command` mit Curtail-Clamp auf `[0, p_max_kw]`. | `tests/unit/hexagon/core/devices/pv/test_commands.py` + Compose-Smoke `::test_safe_005_pv_fallback_canonical` | ✓ **Produktiv** |

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
| **Per-Lauf-Status-Marker (`replay_diff_status`)** | ✗ **fehlt**: Architektur `spec/architecture.md §15` (Z. 820 + 823) listet `replay_diff_status` als Pflicht-Metrik („maschinenlesbarer Statuswert pro Lauf"); grep ueber `src/grid_gym/` nach `replay_diff_status` liefert null Treffer. | Smoke `::test_safe_006_diff_replay_status_deferred_via_trigger_036` `pytest.skip` mit Pointer auf Trigger 036. | ⚠ **Partial Lücke** → [Trigger 036](../plan/planning/open/036-safe-006-replay-diff-status-replay-source-integration.md) |
| **ReplaySource-Integration** | ✗ **fehlt**: Lastenheft Z. 2292 verlangt „M3 mit Replay-Source-Integration"; grep ueber `src/grid_gym/` nach `ReplaySource` liefert null Treffer. Der `diff_replay`-Algorithm ist eine Pure-Function ohne Lauf-Lifecycle-Anker. | siehe oben — gleicher Smoke. | ⚠ **Partial Lücke** → [Trigger 036](../plan/planning/open/036-safe-006-replay-diff-status-replay-source-integration.md) |

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

**Partial Lücke (Trigger 036):** Was im Lastenheft-
Akzeptanz-Wortlaut nicht steht, aber in der Lastenheft-
Traceability Z. 2292 explizit gemacht wird, ist der
Per-Lauf-Status-Marker plus die ReplaySource-Integration:

- `spec/architecture.md §15` (Z. 820 + 823) listet
  `replay_diff_status` als Pflicht-Metrik mit
  „maschinenlesbarem Statuswert pro Lauf" (z. B.
  `green` / `yellow` / `red`). Diese Metrik wird heute
  weder gesetzt noch ueber `MetricsPort` emittiert.
- Lastenheft Z. 2292 verlangt „Replay-Diff-Status-
  Markierung — M3 mit **Replay-Source-Integration**". Ein
  `ReplaySource`-Symbol existiert nicht im Code; der
  `diff_replay()`-Algorithm ist eine standalone
  Pure-Function ohne Lauf-Lifecycle-Anker.

Die [Trigger-036-Notiz](../plan/planning/open/036-safe-006-replay-diff-status-replay-source-integration.md)
verankert den Folge-Pfad: ein eigener Slice fuehrt die
Per-Lauf-Status-Metrik plus die ReplaySource-Integration
ein und schliesst die Partial-Lücke.

---

## Verifikation

`tests/integration/test_m6_welle_5c_safe_005_006_compose_smoke.py`
deckt mit 6 Integration-Smokes (4 SAFE-005 + 1 SAFE-006
Core-Diff + 1 SAFE-006 Trigger-036-Skip) den Vertrag in CI
ab. Plus die `make gates`-Aggregat-Substanz (Lint, Format,
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
- [Trigger 036 — `GG-SAFE-006` Replay-Diff-Status-Marker +
  ReplaySource-Integration](../plan/planning/open/036-safe-006-replay-diff-status-replay-source-integration.md):
  partial Lücke aus dem Welle-5c-Audit; verankert den
  Folge-Slice fuer die Lauf-Lifecycle-Verankerung.
- `spec/architecture.md §15` (Z. 820 + 823) —
  Architektur-Vorgabe fuer `replay_diff_status`-Metrik.
