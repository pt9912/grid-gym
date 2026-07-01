# ADR 0056 — Transformer-Device-Pattern (M8 Welle 2b)

**Status:** Accepted
**Datum:** 2026-06-14
**Bezug:**

- [`ADR 0013`](0013-device-model-protocol.md) — `DeviceModel`-Protocol
  (Pflicht-Surface).
- [`ADR 0017`](0017-grid-connection-device-pattern.md) — GridConnection-
  Pattern; Muster fuer **Set-Power-Command + Sign-Konvention +
  Energie-Akkumulation** (Trigger 017 nennt es als Leit-Muster).
- [`ADR 0022`](0022-fault-injection-protocol.md) /
  [`ADR 0025`](0025-fault-recovery-pattern.md) — `FaultInjectableDevice`
  + Recovery-Muster (Vorbild fuer den Winding-Fault).
- [`ADR 0055`](0055-ev-charger-device-pattern.md) — EV-Charger (M8-Welle-2a);
  gleiche Sub-Welle-Familie, gleiche 8-Naht-Integration.
- [`spec/lastenheft.md`](../../../spec/lastenheft.md#gg-dev-016) —
  [`GG-DEV-016`](../../../spec/lastenheft.md#gg-dev-016).
- [`017-sollte-transformer-device.md`](../planning/done-archive/017-sollte-transformer-device.md)
  — Trigger; [`M8-welle-2.md`](../planning/done/M8-welle-2.md) — Plan.

---

## 1. Kontext

[`GG-DEV-016`](../../../spec/lastenheft.md#gg-dev-016) definiert einen **Transformator** (SOLLTE). Trigger 017 pinnt
den Scope: ein **Geraetemodell** (kein Netzbilanz-Element — das ist
Trigger 021 / [`GG-GRID-006`](../../../spec/lastenheft.md#gg-grid-006)) mit **Wandlungsverhaeltnis**, **Kupfer-
(Last-)Verlusten**, **Eisen- (Leerlauf-)Verlusten** und einer
**Saettigungs-Kennlinie**. Stakeholder-Entscheidung (M8-Welle-2b):
zusaetzlich ein **Schutz-Fault** (`winding_fault`) fuer die vom Trigger
genannten Schutz-Szenarien (Ueberlast/Kurzschluss).

Das Geraet folgt dem **GridConnection-Set-Power-Muster**
([`ADR 0017`](0017-grid-connection-device-pattern.md)): eine steuerbare,
bidirektionale Durchsatz-Leistung am Primaeranschluss, mit kumulativer
Energie. Anders als GridConnection transformiert es Spannung
(`turns_ratio`) und zieht Verluste ab.

## 2. Entscheidung

### 2.1 Modul-Struktur

Submodul `hexagon/core/devices/transformer/` analog `grid_connection/`:
`config.py`, `model.py` (`TransformerDevice`, implementiert `DeviceModel`
+ `FaultInjectableDevice`), `snapshot.py`, `commands.py`, `__init__.py`.

### 2.2 Sign-Konvention

- `primary_power_kw > 0` = **Vorwaerts** (Primaer→Sekundaer, z. B. MS→NS).
- `primary_power_kw < 0` = **Rueckwaerts** (Sekundaer→Primaer).
- Der Set-Wert ist die **Primaer-Durchsatzleistung**; die Sekundaerseite
  liefert sie abzueglich der Verluste (Betrag reduziert, Vorzeichen
  erhalten). Beide Richtungen sind valide — **kein REJECTED fuer das
  Vorzeichen** (Spiegel ADR 0017 §2.4).

### 2.3 Config

`TransformerConfig` (frozen, `slots`, `Decimal`; `__post_init__`-
Validierung, Verstoss → `TransformerConfigInvalidValueError`):

- `rated_power_kw` — Nenn-Durchsatz (Saettigungs-/Ueberlast-Referenz),
  `> 0`.
- `primary_voltage_v` — Nenn-Primaerspannung, `> 0`.
- `turns_ratio` — Wandlungsverhaeltnis `n_p / n_s` (Primaer:Sekundaer),
  `> 0`. Sekundaer-Nennspannung = `primary_voltage_v / turns_ratio`.
- `no_load_loss_kw` — Eisen-/Leerlaufverlust (konstant bei energized),
  `>= 0`.
- `load_loss_kw` — Kupfer-/Lastverlust **bei Nennlast** (`rated`),
  `>= 0`; skaliert quadratisch mit dem Lastfaktor.

Loss-Parameter duerfen `0` sein (ideal-naher Transformator als
Test-Degenerat); die drei dimensionierenden Felder sind strikt `> 0`.

### 2.4 Verlust- + Saettigungsmodell

Pro Tick (Decimal-Localcontext, `prec=28`, `ROUND_HALF_EVEN`):

- **Saettigung** = harter Cap: `|primary_power_kw|` wird auf
  `rated_power_kw` begrenzt. Da der Cap konstant ist (kein
  zustandsabhaengiges Limit wie EV-SoC), passiert die Begrenzung
  **am Command** (`LIMITED` + Alarm), nicht pro Tick; der Tick re-clampt
  nur defensiv. Der harte Knie-Cap ist die bewusst einfachste
  Saettigungs-Approximation; eine weiche Kennlinie (gradueller
  Magnetisierungsstrom-Anstieg) ist eine spaetere Schaerfung.
- **Lastfaktor**: `load_factor = |primary_power_kw| / rated_power_kw`.
- **Verlust**: `loss_kw = no_load_loss_kw + load_loss_kw * load_factor**2`
  (Eisen konstant, Kupfer quadratisch).
- **Sekundaerleistung**: `secondary_power_kw = sign(primary_power_kw) *
  max(0, |primary_power_kw| - loss_kw)` — Verluste reduzieren den
  Betrag, Vorzeichen erhalten, Floor bei `0` (uebersteigt der Verlust
  den Eingang, wird nichts geliefert).
- **Wirkungsgrad**: `efficiency = |secondary_power_kw| / |primary_power_kw|`
  (bzw. `0` bei `primary_power_kw == 0`).
- **Sekundaerspannung**: `secondary_voltage_v = primary_voltage_v /
  turns_ratio` (konstant; Saettigungs-bedingter Spannungs-Droop ist
  out-of-scope).

**Standalone-Device-Vereinfachung**: bei `primary_power_kw == 0` ist der
Leerlaufverlust weiterhin praesent (`loss_kw = no_load_loss_kw`,
`secondary_power_kw = 0`). Der Transformer ist ein eigenstaendiges
Geraetemodell — die netzseitige Verlust-Verrechnung (Bilanz) ist
Trigger 021 ([`GG-GRID-006`](../../../spec/lastenheft.md#gg-grid-006)), nicht dieses Geraet.

### 2.5 Command-Surface

- `set_power_kw` (`value` kW, Primaer-Durchsatz): grobe Saettigungs-
  Cap-Pruefung gegen `[-rated_power_kw, +rated_power_kw]` (ausserhalb →
  `LIMITED` auf den Cap + Alarm, sonst `ACCEPTED`); setzt
  `_pending_power_kw`. Andere `Command.type` → `IGNORED`; fehlender /
  nicht-Decimal `value` → `IGNORED` (Adapter-Rand-Validierung, Spiegel
  ADR 0017 §2.4). Kein zustandsabhaengiger Per-Tick-Re-Clamp noetig
  (Cap ist konstant).

### 2.6 Fault-Injection

`TransformerDevice` implementiert `FaultInjectableDevice` (ADR 0022 §2.1).
Welle-2b-Closed-Set: **ein** Typ `FAULT_TYPE_WINDING_FAULT =
"winding_fault"` (NEU in `core.domain.fault`; Re-Export ueber
`core.faults.types`) — simuliert eine **Schutzausloesung** (Ueberlast/
Kurzschluss): solange aktiv, ist der Transformator isoliert/de-energized
⇒ `primary_power_kw`, `secondary_power_kw` und `loss_kw` hart `0`,
`throughput_kwh` eingefroren. `inject_fault`/`clear_fault` symmetrisch +
idempotent (ADR 0025 §2.4); unbekannter Typ → `FaultUnsupportedTypeError`;
Payload wird ignoriert (Welle-2b-Pragmatik analog Battery/EV).

### 2.7 Tick-Mechanik + Snapshot + Determinismus

- Tick:
  1. `winding_fault` aktiv ⇒ `primary_power_kw = secondary_power_kw =
     loss_kw = 0`; keine `throughput_kwh`-Akkumulation.
  2. Sonst `primary_power_kw = clamp(_pending_power_kw, ±rated)`;
     `loss_kw` + `secondary_power_kw` per §2.4; `throughput_kwh +=
     |secondary_power_kw| * (tick_ms / 3_600_000)`.
- Telemetrie (alphabetisch, `quantize(0.000001)`): `efficiency`,
  `loss_kw`, `primary_power_kw`, `secondary_power_kw`,
  `secondary_voltage_v`, `throughput_kwh`, `winding_fault` (`1`/`0`).
- `TransformerSnapshot` (`version=1`, Erst-Feld): `device_id`/`run_id`/
  `sequence`/`config`/`current_primary_power_kw`/`pending_power_kw`/
  `throughput_kwh` + `fault_state.winding_fault_active` (additiver Block,
  ADR 0025 §2.2-Konvention). `from_snapshot(snapshot()) == device`
  byte-stabil.
- Voll-`DeviceModel`-Surface inkl. `device_id`/`set_run_id`/
  `attach_random`; Pre-init-Guards + `initialize`-Once (ADR 0013/0017).

## 3. Begruendung

Last-/Leerlaufverluste + Saettigungs-Cap machen den Transformator fuer
Multi-Spannungsebenen- und Schutz-Szenarien brauchbar statt zum Stub.
Wiederverwendung des GridConnection-(Set-Power)-Musters haelt
Determinismus + Snapshot konsistent. Quadratischer Kupferverlust + harter
Saettigungs-Cap + Single-Fault-Typ sind die bewusst minimalen
Realismus-Stufen mit klarem Schaerfungspfad.

## 4. Reichweite + Operative Artefakte

Welle 2b-C2/C3 — Integrationspunkte (8 Naehte, Checkliste aus
[`M8-welle-2a.md`](../planning/done/M8-welle-2a.md) §4):

- `devices/transformer/`-Submodul; `_DEVICE_FACTORIES["transformer"]` in
  `core/scenario/loader.py`; `DEVICE_DECIMAL_PARAMS` um die neuen
  `Decimal`-Felder; `_DEVICE_TYPE_BY_CLASS_NAME["TransformerDevice"]`.
- `TransformerAlarm` (5-Feld-Schema) in den `alarm_mappers`-
  Power-Device-Union.
- NEU `FAULT_TYPE_WINDING_FAULT`; HTTP-`_FAULT_TYPE_TO_DEVICE_TYPE`
  `winding_fault → transformer`.
- `_runs_router._STATE_EXTRACTORS["transformer"]`; `CRITICAL_COV_TARGETS
  += devices/transformer`.

Akzeptanz [`GG-DEV-016`](../../../spec/lastenheft.md#gg-dev-016): Modell + Szenario-YAML-Beispiel + deterministischer
Smoke-Test (Verlust-/Saettigungs-Verlauf, `winding_fault`, Snapshot-
Roundtrip).

## 5. Konsequenzen

- Zweites SOLLTE-Geraet der Welle 2; bestaetigt die 8-Naht-Checkliste
  aus Welle 2a (EV-Charger).
- NEU Fault-Typ `winding_fault` im Closed-Set (`core.domain.fault`).
- Zweite `secondary_*`-Telemetrie-Familie (Spannungs-/Leistungs-
  Transformation).

## 6. Nicht Gegenstand dieser ADR

- Spannungsregelung via Stufenschalter (Tap-Changer) — Trigger 017
  explizit out-of-scope (eigener Trigger).
- Wicklungstemperatur / Alterung — M5+-Material (Trigger 017).
- Weiche Saettigungs-Kennlinie + Spannungs-Droop — Welle-3+-Schaerfung
  (harter Cap + konstante Sekundaerspannung reichen fuer Welle 2b).
- Netzbilanz-seitige Verlust-/Grenzen-Verrechnung — Trigger 021
  ([`GG-GRID-006`](../../../spec/lastenheft.md#gg-grid-006)), kein Geraetemodell.
- Weitere Transformer-Faults (Teilausfall, Oel-/Buchholz) — Folge-ADR.

## 7. Acceptance (Fitness Functions)

`Accepted` mit Welle 2b-C2/C3. Maschinell gebunden:

- **Device + Verlust-/Saettigungs-Math + Determinismus + Snapshot-
  Roundtrip** —
  [`tests/unit/hexagon/core/devices/transformer/test_transformer_device.py`](../../../tests/unit/hexagon/core/devices/transformer/test_transformer_device.py)
  + [`test_fault_injection.py`](../../../tests/unit/hexagon/core/devices/transformer/test_fault_injection.py)
  (`winding_fault`).
- **End-to-End-Wiring** —
  [`tests/integration/scenarios/transformer_demo.yaml`](../../../tests/integration/scenarios/transformer_demo.yaml)
  + [`test_transformer_scenario.py`](../../../tests/integration/test_transformer_scenario.py).
- **Map-Konsistenz** — `test_loader_factory_sync.py` +
  `test_yaml_loader_allowlist.py`.
- **Gates** — `make gates` gruen, inkl. `coverage-gate-critical` ≥ 90 %
  auf `src/grid_gym/hexagon/core/devices/transformer`.
