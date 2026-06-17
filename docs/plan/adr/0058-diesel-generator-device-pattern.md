# ADR 0058 — Diesel-Generator-Device-Pattern (M8 Welle 2d)

**Status:** Accepted
**Datum:** 2026-06-14
**Bezug:**

- [`ADR 0013`](0013-device-model-protocol.md) — `DeviceModel`-Protocol.
- [`ADR 0014`](0014-battery-snapshot-schema.md) — Battery-Pattern; Muster
  fuer eine **endliche Ressource + Ramp-Limit + Set-Power-Command +
  Alarm** (Trigger 019 nennt es als Leit-Muster, weil Diesel ebenfalls
  eine endliche Ressource hat).
- [`ADR 0022`](0022-fault-injection-protocol.md) /
  [`ADR 0025`](0025-fault-recovery-pattern.md) — `FaultInjectableDevice`
  + Recovery (Vorbild fuer den Genset-Fault).
- [`ADR 0055`](0055-ev-charger-device-pattern.md) /
  [`ADR 0056`](0056-transformer-device-pattern.md) /
  [`ADR 0057`](0057-wind-turbine-device-pattern.md) — gleiche Sub-Welle-
  Familie (M8 Welle 2).
- [`spec/lastenheft.md`](../../../spec/lastenheft.md#gg-dev-018) —
  [`GG-DEV-018`](../../../spec/lastenheft.md#gg-dev-018) (Geraetetyp `diesel_generator`).
- [`019-sollte-diesel-device.md`](../planning/open/019-sollte-diesel-device.md)
  — Trigger; [`M8-welle-2.md`](../planning/done/M8-welle-2.md) — Plan.

---

## 1. Kontext

[`GG-DEV-018`](../../../spec/lastenheft.md#gg-dev-018) definiert einen **Dieselgenerator** (SOLLTE). Trigger 019
pinnt den Scope: ein **dispatchbarer Generator mit endlicher Ressource**
nach dem Battery-Muster ([`ADR 0014`](0014-battery-snapshot-schema.md)) —
Kraftstoff-Vorrat (l), Verbrauch (l/kWh), Min-Startleistung, Ramp-Limit
und **Anfahr-/Abstell-Hysterese**. Stakeholder-Entscheidung
(M8-Welle-2d): zusaetzlich ein **Schutz-Fault** (`genset_fault`) fuer die
Notstrom-/Resilienz-Szenarien aus Trigger 019 (Diesel als Backup-Quelle).

Geraetetyp-String **`diesel_generator`** (Lastenheft §27.2-kanonisch);
Submodul + Klasse folgen der dir==type-Konvention
(`diesel_generator/` + `DieselGeneratorDevice`).

## 2. Entscheidung

### 2.1 Modul-Struktur

Submodul `hexagon/core/devices/diesel_generator/`: `config.py`,
`model.py` (`DieselGeneratorDevice`, `DeviceModel` +
`FaultInjectableDevice`), `snapshot.py`, `commands.py`, `__init__.py`.

### 2.2 Sign-Konvention

`power_kw >= 0` = Erzeugung (Generator; Diesel absorbiert nie). Ein
negativer Set-Wert wird auf `0` geclampt (`LIMITED`).

### 2.3 Config

`DieselGeneratorConfig` (frozen, `slots`, `Decimal`; `__post_init__`,
Verstoss → `DieselGeneratorConfigInvalidValueError` bzw.
`DieselGeneratorConfigInconsistentRangeError`):

- `max_power_kw` — Nenn-Maximalleistung, `> 0`.
- `min_start_power_kw` — Soll-Schwelle zum **Anfahren**, `> 0`,
  `<= max_power_kw`.
- `min_stop_power_kw` — Soll-Schwelle, unter der ein laufender Genset
  **abstellt**, `>= 0`, `< min_start_power_kw` (Hysterese-Band).
- `fuel_capacity_l` — Tankgroesse, `> 0`.
- `initial_fuel_l` — Start-Kraftstoff, `0 <= x <= fuel_capacity_l`.
- `fuel_per_kwh_l` — Verbrauch (l/kWh), `> 0`.
- `ramp_kw_per_s` — Leistungsaenderung pro Sekunde, `> 0`.

### 2.4 Anfahr-/Abstell-Hysterese (Zustandsmaschine)

Zustand `running ∈ {False, True}`. Pro Tick (vor der Leistungsberechnung):

- **STOPPED → RUNNING**: `requested >= min_start_power_kw` **und**
  `fuel_l > 0`.
- **RUNNING → STOPPED**: `requested < min_stop_power_kw` (Hysterese-Band
  zwischen `min_stop` und `min_start` verhindert schnelles Takten).
- `STOPPED`: `power_kw = 0` (instant), kein Kraftstoffverbrauch.

### 2.5 Tick-Mechanik (Leistung + Ramp + Kraftstoff)

Bei `RUNNING` (Decimal-Localcontext, `prec=28`, `ROUND_HALF_EVEN`):

1. **Ramp** ([`GG-BESS-004`](../../../spec/lastenheft.md#gg-bess-004)-Spiegel): `new_power` naehert sich `requested`
   um maximal `ramp_kw_per_s * dt_s` an; geclampt auf `[0, max_power_kw]`.
   Anfahren rampt von `0` hoch; Abstellen setzt instant `0` (kein
   Ramp-Down — bewusste Minimal-Vereinfachung).
2. **Kraftstoff-Limit**: `fuel_needed = new_power * dt_hours *
   fuel_per_kwh_l`. Reicht der Tank nicht (`fuel_needed > fuel_l`), wird
   `new_power` auf den verfuegbaren Rest reduziert
   (`fuel_l / (dt_hours * fuel_per_kwh_l)`), `fuel_l → 0` und `running →
   False` (leergefahren). Sonst `fuel_l -= fuel_needed`. So sind
   `power_kw`-Telemetrie und Kraftstoffverbrauch konsistent (nie Energie
   ohne Kraftstoff).
3. `generated_kwh += new_power * dt_hours`.

`fuel_l == 0` bei STOPPED verhindert ein Anfahren (§2.4) — ein
leergefahrener Genset bleibt aus, bis (Welle-3+) nachgetankt wird.

### 2.6 Command-Surface

- `set_power_kw` (`value` kW): grobe Clamp-Pruefung auf
  `[0, max_power_kw]` (negativ → `LIMITED 0`; `> max` → `LIMITED max`;
  sonst `ACCEPTED`); setzt `_pending_power_kw`. `LIMITED` emittiert einen
  `DieselGeneratorAlarm` (5-Feld-Schema). Andere `Command.type` /
  nicht-Decimal `value` → `IGNORED`. Die Hysterese-/Ramp-/Kraftstoff-
  Begrenzung passiert pro Tick (§2.4/§2.5), nicht am Command.

### 2.7 Fault-Injection

`FaultInjectableDevice` (ADR 0022 §2.1). Welle-2d-Closed-Set: **ein** Typ
`FAULT_TYPE_GENSET_FAULT = "genset_fault"` (NEU in `core.domain.fault` +
Re-Export) — Schutzausloesung: solange aktiv, `running = False`,
`power_kw = 0`, kein Kraftstoffverbrauch. `inject_fault`/`clear_fault`
symmetrisch + idempotent (ADR 0025 §2.4); unbekannter Typ →
`FaultUnsupportedTypeError`; Payload ignoriert.

### 2.8 Snapshot + Determinismus + Bilanz

- Telemetrie (alphabetisch, `quantize(0.000001)`): `fuel_l`,
  `generated_kwh`, `genset_fault` (`1`/`0`), `power_kw`, `running`
  (`1`/`0`).
- `DieselGeneratorSnapshot` (`version=1`, Erst-Feld): `device_id`/
  `run_id`/`sequence`/`config`/`fuel_l`/`current_power_kw`/
  `pending_power_kw`/`running` (bool) /`generated_kwh` +
  `fault_state.genset_fault_active`. NEU `snapshot_codec.assert_bool`
  fuer das `running`-Top-Level-Flag. `from_snapshot(snapshot()) ==
  device` byte-stabil.
- **Bilanz-Naht** (Lerneintrag Welle-2c): `diesel_generator` →
  `"generation"` in `_BILANZ_SOURCE_BUCKETS`, sonst faellt die Diesel-
  `power_kw` als `unknown_source` aus der Netzbilanz (Generator im Grid
  unsichtbar).
- Voll-`DeviceModel`-Surface; Pre-init-Guards + `initialize`-Once.

## 3. Begruendung

Kraftstoff-Vorrat + Verbrauch + Hysterese machen den Diesel fuer
Inselnetz-/Notstrom-Szenarien brauchbar (dispatchbare Backup-Quelle mit
endlicher Reichweite). Wiederverwendung des Battery-(endliche-Ressource +
Ramp + Set-Power)-Musters haelt Determinismus + Snapshot konsistent.
Harte Start/Stop-Hysterese + lineares Kraftstoff-Modell + Single-Fault-Typ
sind die bewusst minimalen Realismus-Stufen mit klarem Schaerfungspfad.

## 4. Reichweite + Operative Artefakte

Welle 2d-C2/C3 — Integrationspunkte (8-Naht-Checkliste aus
[`M8-welle-2a.md`](../planning/done/M8-welle-2a.md) §4 **plus** die
in Welle 2c gelernte Bilanz-Naht):

- `devices/diesel_generator/`-Submodul;
  `_DEVICE_FACTORIES["diesel_generator"]`; `DEVICE_DECIMAL_PARAMS` um die
  6 neuen `Decimal`-Felder (`ramp_kw_per_s` ist schon gelistet);
  `_DEVICE_TYPE_BY_CLASS_NAME["DieselGeneratorDevice"]`.
- `DieselGeneratorAlarm` in die `alarm_mappers`-Power-Device-Union.
- NEU `FAULT_TYPE_GENSET_FAULT`; HTTP-`_FAULT_TYPE_TO_DEVICE_TYPE`
  `genset_fault → diesel_generator`.
- `_runs_router._STATE_EXTRACTORS["diesel_generator"]`;
  `CRITICAL_COV_TARGETS += devices/diesel_generator`.
- **`_BILANZ_SOURCE_BUCKETS["diesel_generator"] = "generation"`**.
- NEU `snapshot_codec.assert_bool` (geteilter Codec-Primitive fuer das
  `running`-Bool).

Akzeptanz [`GG-DEV-018`](../../../spec/lastenheft.md#gg-dev-018): Modell + Szenario-YAML-Beispiel + deterministischer
Smoke-Test (Anfahr-/Abstell-Hysterese, Kraftstoff-Run-Dry, Ramp,
`genset_fault`, Snapshot-Roundtrip).

## 5. Konsequenzen

- Viertes (letztes) SOLLTE-Geraet der Welle 2; erstes Geraet mit einer
  **Zustandsmaschine** (running-Hysterese) + endlicher nicht-elektrischer
  Ressource (Kraftstoff).
- NEU Fault-Typ `genset_fault`; NEU `snapshot_codec.assert_bool`.

## 6. Nicht Gegenstand dieser ADR

- Emissions-Modellierung (CO2/NOx), Wartung/Verfuegbarkeit — Trigger 019
  out-of-scope.
- Nachtanken zur Laufzeit, Ramp-Down beim Abstellen, Warmlauf/
  Mindestlaufzeit — Welle-3+-Schaerfung.
- Inselnetz-Bilanzmodell selbst — Trigger 020 ([`GG-GRID-005`](../../../spec/lastenheft.md#gg-grid-005)).
- Weitere Genset-Faults (Ueberhitzung, Oeldruck) — Folge-ADR.

## 7. Acceptance (Fitness Functions)

`Accepted` mit Welle 2d-C2/C3. Maschinell gebunden:

- **Hysterese + Kraftstoff + Ramp + Determinismus + Snapshot-Roundtrip**
  —
  [`tests/unit/hexagon/core/devices/diesel_generator/test_diesel_generator_device.py`](../../../tests/unit/hexagon/core/devices/diesel_generator/test_diesel_generator_device.py)
  + [`test_fault_injection.py`](../../../tests/unit/hexagon/core/devices/diesel_generator/test_fault_injection.py).
- **End-to-End-Wiring** —
  [`tests/integration/scenarios/diesel_demo.yaml`](../../../tests/integration/scenarios/diesel_demo.yaml)
  + [`test_diesel_scenario.py`](../../../tests/integration/test_diesel_scenario.py).
- **Map-Konsistenz** — `test_loader_factory_sync.py` +
  `test_yaml_loader_allowlist.py`.
- **Gates** — `make gates` gruen, inkl. `coverage-gate-critical` ≥ 90 %
  auf `src/grid_gym/hexagon/core/devices/diesel_generator`.
