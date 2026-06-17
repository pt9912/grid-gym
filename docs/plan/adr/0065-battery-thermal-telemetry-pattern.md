# ADR 0065 — Battery-Temperatur-Telemetrie (M8 Welle 4a)

**Status:** Accepted — Validierung mit M8-Welle-4a-Lieferung
(`make gates` gruen: lint/format-check/typecheck/arch-check/test-unit/
`coverage-gate-critical` ≥ 90 % auf `devices/battery` + `docs-check` +
`accept-pin-check`; ≥ 100-Tick-Determinismus-Property + Boundary-Pins
(Aufheiz-/Abkuehl-Monotonie, Steady-State gegen `theta_ss`) +
Inaktiv-Regressions-Pin (`thermal=None` byte-genau wie heute) +
opt-in-Snapshot-Roundtrip inkl. backward-compat-Lesepfad).
**Schliesst [`GG-BESS-006`](../../../spec/lastenheft.md#gg-bess-006)** (Trigger
[`023`](../planning/open/023-sollte-battery-temperature.md)).
Additive **Schaerfung** von
[`ADR 0014`](0014-battery-snapshot-schema.md) (Battery-Snapshot-/Telemetrie-
Vertrag) ohne Supersede — Erweiterungs-Pattern
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md); gleiche Thermo-Mechanik-
Familie wie [`ADR 0061`](0061-transformer-limit-bilanz-pattern.md).
**Datum:** 2026-06-17
**Bezug:**
[`ADR 0014`](0014-battery-snapshot-schema.md) §2.2/§2.4/§2.6 (Snapshot-Layout,
Tick-Telemetrie, Determinismus — diese ADR ergaenzt eine **additive opt-in
Telemetrie-/State-Flaeche**, der SOC-/Power-/Ramp-Kern bleibt unberuehrt),
[`ADR 0061`](0061-transformer-limit-bilanz-pattern.md) §2.2 (Single-Zonen-
Euler-Thermomodell — `theta += (theta_ss - theta)·(dt/tau)`; diese ADR
spiegelt die Mechanik auf das Battery-Pack),
[`ADR 0025`](0025-fault-recovery-pattern.md) §2.2 (additiver `fault_state`-
Block — diese ADR ist **strenger**: opt-in serialisiert statt immer
emittiert),
[`ADR 0063`](0063-pv-volt-var-q-emission-pattern.md) §2.3 (opt-in
Telemetrie-Emission an eine nested Config gebunden — Emission-Liste-Pattern),
[`ADR 0013`](0013-device-model-protocol.md) §2.4 (Snapshot-`version`-Erst-
Feld), [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Schaerfung-Pattern).
Slice-Plan [`M8-welle-4a.md`](../planning/done/M8-welle-4a.md);
Container [`M8-welle-4.md`](../planning/done/M8-welle-4.md). Trigger
[`023`](../planning/open/023-sollte-battery-temperature.md) ([`GG-BESS-006`](../../../spec/lastenheft.md#gg-bess-006),
Lastenheft §10.6; **mit dieser ADR aufgeloest**).

---

## 1. Kontext

[`ADR 0014`](0014-battery-snapshot-schema.md) deckt im Battery-Modell SOC,
Strom/Leistung, Ramp und (per [`ADR 0025`](0025-fault-recovery-pattern.md))
den `fault_state`-Block ab — **keine Temperatur**. Lastenheft [`GG-BESS-006`](../../../spec/lastenheft.md#gg-bess-006)
(Trigger [`023`](../planning/open/023-sollte-battery-temperature.md)) verlangt
**Temperatur-Telemetrie** als SOLLTE-Erweiterung. Der Trigger nennt zwei
Modell-Optionen: zustandsfrei (`power² · R_internal + ambient`) **oder**
stateful (thermische Masse + Kuehlpfad).

Welle 4a ist — wie die Netz-Wellen 3a/3b — eine **reine additive Geraete-
Schaerfung**: kein neues Geraet, kein neuer Port/Adapter-Typ, **keine
Bilanz-Beruehrung**. Temperatur ist eine geraete-interne Groesse, die als
`TelemetryPoint` emittiert wird, **nicht** in `GridModelBilanz` aggregiert
(im Gegensatz zur Transformer-Netz-Grenze aus
[`ADR 0061`](0061-transformer-limit-bilanz-pattern.md)). Der Thermo-Layer ist
**opt-in**: ohne `thermal`-Block (Default) ist das Verhalten bit-genau wie
unter [`ADR 0014`](0014-battery-snapshot-schema.md).

---

## 2. Entscheidung

### 2.1 Config — `ThermalConfig` (nested, opt-in)

`BatteryConfig` (`hexagon/core/devices/battery/config.py`) bekommt **ein
additives, optionales Feld**:

```
thermal: ThermalConfig | None = None
```

`None` (Default) = kein Thermomodell = bit-genau heutiges Verhalten (kein
`temperature_celsius`-Punkt, kein Snapshot-State). `ThermalConfig` ist eine
eigene Frozen-Dataclass (`slots=True`) mit `__post_init__`-Validierung
(Verstoss → `BatteryConfigInvalidValueError`):

| Feld | Einheit | Invariante |
|---|---|---|
| `ambient_temp_c` | degC | beliebiges `Decimal` (auch < 0: Tiefsttemperatur-Umgebung) |
| `thermal_rise_c_at_full_load` | K | `> 0` (Anstieg bei Volllast) |
| `thermal_time_constant_s` | s | `> 0` (thermische Traegheit Tau) |

Die No-float-Typpruefung ([`GG-DATA-005`](../../../spec/lastenheft.md#gg-data-005)) liegt — wie im Bestands-Battery-
Pattern — in den Parsern (`_thermal_from_params` / Snapshot-`assert_decimal`),
nicht im `ThermalConfig`-Konstruktor. Das nested-opt-in-Config-Layout
spiegelt `VoltVarConfig` aus
[`ADR 0063`](0063-pv-volt-var-q-emission-pattern.md) §2.2.

### 2.2 Thermomodell als stateful Single-Zonen-Euler

Spiegelt die Mechanik aus
[`ADR 0061`](0061-transformer-limit-bilanz-pattern.md) §2.2 (Top-Oil), auf das
Battery-Pack uebertragen. Pro Tick (im bestehenden Battery-Decimal-
Localcontext `prec=28`, `ROUND_HALF_EVEN`; `dt_s = tick_ms / 1000`):

```
load_pu   = abs(power_kw) / max(max_charge_kw, max_discharge_kw)
theta_ss  = ambient_temp_c + thermal_rise_c_at_full_load * load_pu^2
theta    += (theta_ss - theta) * (dt_s / thermal_time_constant_s)
```

`power_kw` ist die **tatsaechlich gefahrene** Tick-Power (post-Ramp,
post-SOC-Clamp/Derate) — Lade- wie Entladestrom heizen (Betrag). `theta`
(`temperature_celsius`) ist **akkumulierter Geraete-State**, je Tick auf
`Decimal("0.000001")` quantisiert (gebundene Stellenzahl + Snapshot-
Lesbarkeit, deterministisch im Context).

**Kaltstart auf `ambient_temp_c`** (C1-Entscheidung, §3): kein separater
`initial_temp_c`-Parameter — der Init-Wert ist die Umgebungstemperatur,
exakt wie der Top-Oil-State in
[`ADR 0061`](0061-transformer-limit-bilanz-pattern.md) §2.2 auf `ambient`
startet. Minimiert die Config-Flaeche.

**Kein Trip / kein Constraint:** anders als die Transformer-Netz-Grenze
emittiert das Battery-Thermomodell **kein** Event und keinen Alarm —
thermisches Derating/Notabschaltung ist M3-Material (§7). Welle 4a liefert
reine Telemetrie.

### 2.3 Telemetrie — opt-in `temperature_celsius`

Ein zusaetzlicher `TelemetryPoint` (`metric="temperature_celsius"`,
`unit="degC"`, SI-Stringtyp per [`GG-DATA-002`](../../../spec/lastenheft.md#gg-data-002)), **conditional** an den
`thermal`-Block gebunden (Emission-Liste-Pattern wie die opt-in Q-Telemetrie
aus [`ADR 0063`](0063-pv-volt-var-q-emission-pattern.md) §2.3): ohne
`thermal`-Block **kein** Punkt (nicht `0`). Der Punkt sortiert alphabetisch
hinter `soc_pct` (`power_kw` < `soc_kwh` < `soc_pct` < `temperature_celsius`)
→ die deterministische Metrik-Reihenfolge aus
[`ADR 0014`](0014-battery-snapshot-schema.md) §2.4 bleibt erhalten; der
monotone `sequence`-Counter zaehlt den vierten Punkt mit.

### 2.4 Snapshot — opt-in serialisiert, kein Versions-Bump

Schema bleibt `version=1`. Wie der opt-in Thermo-State aus
[`ADR 0061`](0061-transformer-limit-bilanz-pattern.md) §2.5, aber **strenger**
als der immer emittierte `fault_state`-Block aus
[`ADR 0025`](0025-fault-recovery-pattern.md):

- **Config-Block opt-in:** der `thermal`-Block wird im `config`-Sub-Mapping
  nur emittiert, wenn gesetzt. Default-Pfad → byte-identisch
  (`EXPECTED_DEMO_*` + Scenario-Hash unberuehrt). `from_dict` liest fehlende
  neue Config-Keys als inaktiv.
- **Thermo-State opt-in:** ein additiver Top-Level-Key `temperature_celsius`
  wird nur bei aktivem Block geschrieben; `from_dict` liest ihn optional
  (Default `None`). Alt-Snapshots ohne Key lesen als „kein Thermomodell"
  (v1-backward-compat-Lesepfad, kein Versions-Bump).

Begruendung des strengeren Opt-in (vs. `fault_state` immer emittiert): der
`fault_state`-Block existierte schon zum Zeitpunkt des Demo-Hash-Pins; eine
**neue** Default-aus-Telemetrie darf den netzgekoppelten MVP-Demo (Hash-Pins,
Replay-Baselines, Scenario-Hash) nicht verschieben — nur ein Szenario mit
`thermal`-Block traegt die neuen Keys.

### 2.5 Determinismus + Default-Stabilitaet

- **Inaktiv bit-genau:** der Thermo-Layer aktiviert sich nur bei
  `thermal is not None`; der SOC-/Power-/Ramp-Kern aus
  [`ADR 0014`](0014-battery-snapshot-schema.md) §2.4 bleibt textlich
  unveraendert (Regressions-Pin Pflicht: gleiche Trace, gleiche 3 Metriken).
- **Thermo-Determinismus:** Euler-Integration + Quantisierung laufen im
  bestehenden `prec=28`/`ROUND_HALF_EVEN`-Context; gleiche Eingangssequenz →
  byte-identische `temperature_celsius`-Spur ueber ≥ 100 Ticks (Hypothesis-
  Property). `RandomPort` wird **nicht** konsumiert (Temperatur ist
  deterministisch aus Last + Zeit; per-Zelle-Rauschen ist
  [`M8-welle-4b.md`](../planning/done/M8-welle-4b.md)).

---

## 3. Begruendung

**Stateful statt zustandsfrei:** der Trigger
[`023`](../planning/open/023-sollte-battery-temperature.md) nennt beide
Optionen. Ein zustandsfreies `power² · R + ambient` springt bei jedem
Lastwechsel instantan — physikalisch falsch fuer eine thermische Masse und
ohne Aussagekraft fuer spaetere Derating-/Alterungs-Slices. Die thermische
Traegheit Tau modelliert die Aufheiz-/Abkuehl-Dynamik **physikalisch** (das
Integral der Last zaehlt, nicht der Momentanwert) und ist bereits in
[`ADR 0061`](0061-transformer-limit-bilanz-pattern.md) als deterministischer
Euler etabliert — kein neues Modell-Risiko, ein bewaehrtes Muster.

**`load_pu²`-Naeherung:** Verluste (und damit Erwaermung) skalieren mit dem
Quadrat des Stroms — dieselbe ehrliche Vereinfachung wie
[`ADR 0061`](0061-transformer-limit-bilanz-pattern.md) §3.

**Kaltstart auf `ambient` statt `initial_temp_c`:** minimale Config-Flaeche;
deckt den Normalfall (Pack startet auf Umgebungstemperatur). Ein dedizierter
Startwert (vorgewaermtes Pack) ist ein eigener Slice, falls je gefordert.

**Opt-in statt Schema-Bump:** identische Begruendung wie
[`ADR 0061`](0061-transformer-limit-bilanz-pattern.md) §3 /
[`ADR 0063`](0063-pv-volt-var-q-emission-pattern.md) §3 — der additive Layer
darf die Demo-Hash-Pins nicht verschieben.

**Telemetrie statt Constraint:** Welle 4a liefert Sichtbarkeit; die
Reaktion darauf (Derating, Abschaltung) ist Safety-Logik und gehoert in den
M3-Fault-Slice (§7), nicht in eine Telemetrie-Welle.

---

## 4. Risiken / offene Design-Fragen

- **Euler-Stabilitaet:** `dt_s / tau` sollte `< 1` bleiben (Tau ≫ tick_ms);
  ein zu kleines Tau ueberschwingt, bleibt aber deterministisch. Szenario-
  Konfigurations-Hinweis, keine Config-Hard-Invariante (`tick_ms` erst zur
  Laufzeit bekannt) — spiegelt
  [`ADR 0061`](0061-transformer-limit-bilanz-pattern.md) §4.
- **State-Konsistenz:** `temperature_celsius` (State) und `thermal` (Config)
  muessen gemeinsam gesetzt/leer sein. Der Writer haelt das invariant; ein
  hand-gebauter Snapshot mit `thermal`-Block aber ohne `temperature_celsius`
  self-healt im naechsten Tick (ambient-Fallback im Narrowing).
- **YAML-Aktivierung:** der nested `thermal`-Block wird — wie `volt_var`
  ([`ADR 0063`](0063-pv-volt-var-q-emission-pattern.md)) und
  `transformer_limit` ([`ADR 0061`](0061-transformer-limit-bilanz-pattern.md))
  — von `scenario_yaml._coerce_decimals` aktuell **nicht** rekursiv str→Decimal-
  coerced; aktiviert wird der Block programmatisch (Tests via
  `ScenarioDevice.params` mit `Decimal`-Werten). Rekursive Nested-Coercion ist
  ein bestehender, geraete-uebergreifender Folge-Slice (betrifft alle drei
  opt-in-Bloecke), nicht Welle-4a-Scope.

---

## 5. Reichweite

Gilt fuer: `hexagon/core/devices/battery/config.py` (`ThermalConfig` + Feld),
`hexagon/core/devices/battery/model.py` (Euler-Step + State + opt-in
Emission + Params-Roundtrip), `hexagon/core/devices/battery/snapshot.py`
(opt-in Config-/State-Serialisierung),
`tests/unit/hexagon/core/devices/battery/`.

Gilt NICHT fuer: thermisches Derating/Notabschaltung (M3), aktive
Kuehlung/Heizung (HVAC-Slice), Zellebene-Thermodynamik bzw. Zellspannung
([`M8-welle-4b.md`](../planning/done/M8-welle-4b.md), [`GG-BESS-007`](../../../spec/lastenheft.md#gg-bess-007)),
Alterungs-/Kalender-Zyklen-Modelle (§7).

---

## 6. Akzeptanzkriterien (Trigger 023)

- [ ] `ThermalConfig` additiv + validiert; opt-in `thermal`-Feld auf
      `BatteryConfig` mit backward-compat-Default.
- [ ] Stateful Euler-`temperature_celsius`; opt-in `TelemetryPoint`
      (`unit="degC"`) **nur bei aktivem Block** (inaktiv → kein Punkt);
      ≥ 100-Tick-Determinismus-Property + Boundary-Pins (Aufheizen/Abkuehlen/
      Steady-State).
- [ ] `BatterySnapshot` opt-in serialisiert (kein Versions-Bump, v1-
      backward-compat-Lesepfad); Roundtrip byte-stabil.
- [ ] `make gates` gruen (`coverage-gate-critical` ≥ 90 % `devices/battery`);
      `accept-pin-check` gruen (`thermal=None` → `EXPECTED_DEMO_*` unberuehrt);
      diese ADR `Accepted`; Trigger 023 aufgeloest.

---

## 7. Nicht Gegenstand dieser ADR

- **Thermisches Derating / Sicherheits-Abschaltung** bei Ueber-/
  Untertemperatur — Constraint-/Fault-Logik (M3), nicht diese Telemetrie-
  Welle (Trigger [`023`](../planning/open/023-sollte-battery-temperature.md)
  Aktivierungs-Kriterium nennt den M3-Fault-Slice separat).
- **Aktive Kuehlung-/Heizung-Logik** — HVAC-Aggregat-Modellierung, nicht
  Battery-Verhalten.
- **Zellebene-Thermodynamik / Zellspannung** — Pack-Niveau bleibt;
  Zellauffloesung ist [`M8-welle-4b.md`](../planning/done/M8-welle-4b.md)
  ([`GG-BESS-007`](../../../spec/lastenheft.md#gg-bess-007)) bzw. eigener Slice.
- **Alterungs-/Lebensdauer-Modelle** (T-abhaengig) — eigener Trigger.
- **`initial_temp_c` / vorgewaermtes Pack** — Kaltstart auf `ambient` genuegt
  fuer das Ersatzmodell; ein dedizierter Startwert ist ein Folge-Slice.
