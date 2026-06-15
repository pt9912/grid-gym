# ADR 0057 — Wind-Turbine-Device-Pattern (M8 Welle 2c)

**Status:** Accepted
**Datum:** 2026-06-14
**Bezug:**

- [`ADR 0013`](0013-device-model-protocol.md) — `DeviceModel`-Protocol.
- [`ADR 0016`](0016-pv-load-device-pattern.md) — PV/Load-Pattern; Muster
  fuer einen **Erneuerbare-Einspeise-Generator** (Trigger 018 nennt es
  als Leit-Muster).
- [`ADR 0007`](0007-random-port.md) — `RandomPort` (deterministisch-
  reproduzierbare Zufallsquelle + `sub_port`-Konvention); Wind ist das
  **erste Geraet, das den `RandomPort` tatsaechlich konsumiert**.
- [`ADR 0055`](0055-ev-charger-device-pattern.md) /
  [`ADR 0056`](0056-transformer-device-pattern.md) — gleiche Sub-Welle-
  Familie (M8 Welle 2), gleiche Integrations-Naht-Checkliste.
- [`spec/lastenheft.md`](../../../spec/lastenheft.md#gg-dev-017) —
  `GG-DEV-017` (Geraetetyp `wind_turbine`).
- [`018-sollte-wind-device.md`](../planning/open/018-sollte-wind-device.md)
  — Trigger; [`M8-welle-2.md`](../planning/done/M8-welle-2.md) — Plan.

---

## 1. Kontext

`GG-DEV-017` definiert eine **Windkraftanlage** (SOLLTE). Trigger 018
pinnt den Scope: ein **Generator-Geraetemodell** analog PV
([`ADR 0016`](0016-pv-load-device-pattern.md)) mit einer **kubischen
Leistungskennlinie** zwischen cut-in- und Nennwindgeschwindigkeit und
Schaltzustaenden unter/im/ueber Nennbereich. Stakeholder-Entscheidung
(M8-Welle-2c): der Windgeschwindigkeits-Eingang ist **stochastisch** —
pro Tick aus einer seeded `RandomPort`-Verteilung gezogen
(deterministisch via Seed), nicht command- oder profilgetrieben.

Der Geraetetyp-String ist **`wind_turbine`** (Lastenheft §27.2-kanonisch);
Submodul + Klasse folgen der dir==type-Konvention der Welle-2-Geraete
(`wind_turbine/` + `WindTurbineDevice`).

## 2. Entscheidung

### 2.1 Modul-Struktur

Submodul `hexagon/core/devices/wind_turbine/`: `config.py`, `model.py`
(`WindTurbineDevice`, implementiert `DeviceModel`), `snapshot.py`,
`__init__.py`. **Kein `commands.py`** und **kein Alarm** — Wind ist
stochastisch getrieben, nimmt keine Steuerbefehle (`apply_command` →
`IGNORED`). **Kein Fault** (Spiegel PV; Turbinen-Schutz waere ein
Folge-Trigger).

### 2.2 Sign-Konvention

`power_kw >= 0` = Einspeisung (Erzeugung), Spiegel PV
([`ADR 0016`](0016-pv-load-device-pattern.md) §2.2). Wind entlaedt nie.

### 2.3 Config

`WindTurbineConfig` (frozen, `slots`, `Decimal`; `__post_init__`,
Verstoss → `WindTurbineConfigInvalidValueError` bzw.
`WindTurbineConfigInconsistentRangeError`):

- `rated_power_kw` — Nennleistung, `> 0`.
- `cut_in_speed_ms` — Einschalt-Windgeschwindigkeit, `>= 0`.
- `rated_speed_ms` — Nennwindgeschwindigkeit, `> cut_in_speed_ms`.
- `cut_out_speed_ms` — Abschalt-Windgeschwindigkeit, `> rated_speed_ms`.
- `min_wind_speed_ms` — untere Grenze der stochastischen Ziehung, `>= 0`.
- `max_wind_speed_ms` — obere Grenze, `>= min_wind_speed_ms` (Gleichheit
  erlaubt = **konstanter Wind**; macht die Kennlinie RNG-frei testbar).

### 2.4 Stochastischer Windgeschwindigkeits-Eingang

Pro Tick (Decimal-Localcontext, `prec=28`, `ROUND_HALF_EVEN`):

`wind_speed_ms = min_wind_speed_ms + next_float() * (max_wind_speed_ms -
min_wind_speed_ms)`

— **eine** `RandomPort.next_float()`-Ziehung pro Tick (uniform in
`[min, max)`; `next_float()` ist `Decimal[0,1)`, 6-NK,
`ADR 0007 §5.2`). Bei `min == max` ist der Faktor `0` → konstanter Wind
(die Ziehung erfolgt trotzdem, der Stream bleibt sequenz-konsistent).
Determinismus: gleicher Seed + gleiche Aufruf-Reihenfolge → identische
Wind-Folge (`ADR 0007 §5.1`).

### 2.5 Kubische Leistungskennlinie

Aus `wind_speed_ms = v`:

- `v < cut_in_speed_ms` ODER `v >= cut_out_speed_ms` → `0` (unter
  Einschalt- bzw. ueber Abschaltgeschwindigkeit — Turbine feathered).
- `cut_in_speed_ms <= v < rated_speed_ms` → **kubisch**:
  `rated_power_kw * (v**3 - cut_in**3) / (rated**3 - cut_in**3)`
  (Windleistung ∝ `v**3`; normiert auf `0` bei cut-in, `rated_power_kw`
  bei Nennwind — stetig an beiden Enden).
- `rated_speed_ms <= v < cut_out_speed_ms` → `rated_power_kw` (flach).

Die kubische Normierung ist die physikalisch begruendete
Minimal-Kennlinie; eine geglaettete/Hysterese-behaftete Form (z. B.
Abschalt-Hysterese) ist eine spaetere Schaerfung.

### 2.6 Tick-Mechanik + Snapshot + Determinismus

- Tick: Wind ziehen (§2.4) → Leistung aus Kennlinie (§2.5) →
  `generated_kwh += power_kw * (tick_ms / 3_600_000)`; `current_power_kw`
  + `current_wind_speed_ms` fortschreiben.
- Telemetrie (alphabetisch, `quantize(0.000001)`): `generated_kwh`,
  `power_kw`, `wind_speed_ms`.
- `WindTurbineSnapshot` (`version=1`, Erst-Feld): `device_id`/`run_id`/
  `sequence`/`config`/`current_power_kw`/`current_wind_speed_ms`/
  `generated_kwh`. **Kein `fault_state`** (kein Fault). Der `RandomPort`
  ist NICHT Teil des Geraete-Snapshots — der Root-`RandomPort` wird vom
  `TickLoop` persistiert/restored, das Geraet bekommt seinen Sub-Stream
  per `attach_random` nach `from_snapshot` re-attached
  (`ADR 0007 §5` + `ADR 0013 §2.6`; das ist der Zweck der seit M2
  vorgehaltenen `attach_random`-Hooks). `from_snapshot(snapshot()) ==
  device` byte-stabil (Random aus dem `==`-Vergleich ausgenommen).
- **Resume-Grenze (Welle-2c, Review-Folge)**: Geraete-`from_snapshot`
  setzt `_random` **nicht**; der erste Tick wirft fail-loud
  `DeviceNotInitializedError`, bis `attach_random` lief. **Voller
  stand-kontinuierlicher Resume stochastischer Geraete ist NICHT Teil
  von Welle 2c**: (a) der `TickLoop`-Resume-Pfad ruft `attach_random`
  fuer Geraete derzeit nicht auf (kein Geraet konsumierte bisher
  Random), und (b) selbst mit Re-Attach liefert `root.sub_port(name)`
  den Sub-Stream nur im **Initial-Zustand** (deterministisch ueber den
  Namen, unabhaengig von der bisherigen Ziehungs-Anzahl, ADR 0007 §5.2)
  — die per-Geraet-Stream-Position wird nirgends persistiert. Ein
  mid-run resumter stochastischer Lauf setzt daher NICHT
  byte-kontinuierlich fort. **Fresh-Start-Laeufe sind voll
  deterministisch** (gleicher Seed → gleiche Folge) — das ist der heute
  genutzte Pfad. Per-Geraet-Random-State im `SnapshotEnvelope` ist ein
  Folge-Slice (§6).

## 3. Begruendung

Die stochastische Ziehung macht Wind zum ersten echten `RandomPort`-
Konsumenten und liefert variable Erneuerbaren-Einspeisung fuer
Mix-Szenarien — ohne neue Profil-/Wiring-Infrastruktur (die wuerde der
Profil-Eingang aus Trigger 018 verlangen). Die kubische Kennlinie + der
uniforme `[min, max)`-Zug sind die bewusst minimalen Realismus-Stufen mit
klarem Schaerfungspfad; `min == max` haelt die Kennlinie deterministisch
testbar.

## 4. Reichweite + Operative Artefakte

Welle 2c-C2/C3 — Integrationspunkte (Teilmenge der 8-Naht-Checkliste aus
[`M8-welle-2a.md`](../planning/done/M8-welle-2a.md) §4; **keine**
Alarm-/Fault-Naht):

- `devices/wind_turbine/`-Submodul; `_DEVICE_FACTORIES["wind_turbine"]`;
  `DEVICE_DECIMAL_PARAMS` um die 5 neuen `Decimal`-Felder;
  `_DEVICE_TYPE_BY_CLASS_NAME["WindTurbineDevice"]`.
- `_runs_router._STATE_EXTRACTORS["wind_turbine"]`; `CRITICAL_COV_TARGETS
  += devices/wind_turbine`.

Akzeptanz `GG-DEV-017`: Modell + Szenario-YAML-Beispiel + deterministischer
Smoke-Test (Kennlinien-Werte, stochastische Determinismus-Property,
Snapshot-Roundtrip).

## 5. Konsequenzen

- Erster produktiver `RandomPort`-Konsument — aktiviert die seit M2
  vorgehaltene `attach_random`-Resume-Mechanik real.
- Drittes SOLLTE-Geraet der Welle 2; bestaetigt die Geraete-Checkliste
  ohne Command/Alarm/Fault-Naehte (command-loses Generator-Profil).

## 6. Nicht Gegenstand dieser ADR

- Windgeschwindigkeits-**Profil** (analog `LoadProfile`) — Trigger-018-
  Alternative, eigener Slice (braucht Loader-Profil-Wiring).
- Geglaettete Kennlinie / Abschalt-Hysterese / Gauss-/Weibull-Verteilung
  — Welle-3+-Schaerfung (uniform + harter cut-out reichen fuer 2c).
- Wakes / Park-Effekte, Aerodynamik / Turbinen-Mechanik — Trigger 018
  out-of-scope.
- Turbinen-Schutz-Fault — Folge-Trigger, falls ein Szenario ihn braucht.
- **Stand-kontinuierlicher Resume stochastischer Geraete** — der
  per-Geraet `sub_port`-Stream-Stand muss dafuer im `SnapshotEnvelope`
  persistiert + vom `TickLoop`-Resume re-attached werden (§2.6).
  Folge-Slice; Welle 2c liefert nur den Fresh-Start-Pfad
  (voll deterministisch) + den fail-loud Resume-Guard.

## 7. Acceptance (Fitness Functions)

`Accepted` mit Welle 2c-C2/C3. Maschinell gebunden:

- **Kennlinie + stochastischer Zug + Determinismus + Snapshot-Roundtrip**
  —
  [`tests/unit/hexagon/core/devices/wind_turbine/test_wind_turbine_device.py`](../../../tests/unit/hexagon/core/devices/wind_turbine/test_wind_turbine_device.py)
  (Kennlinien-Werte via `min == max`-Konstantwind + direkter Curve-Test;
  ≥ 100-Tick-Determinismus-Property; `attach_random`-Resume-Lifecycle).
- **End-to-End-Wiring** —
  [`tests/integration/scenarios/wind_turbine_demo.yaml`](../../../tests/integration/scenarios/wind_turbine_demo.yaml)
  + [`test_wind_turbine_scenario.py`](../../../tests/integration/test_wind_turbine_scenario.py).
- **Map-Konsistenz** — `test_loader_factory_sync.py` +
  `test_yaml_loader_allowlist.py`.
- **Gates** — `make gates` gruen, inkl. `coverage-gate-critical` ≥ 90 %
  auf `src/grid_gym/hexagon/core/devices/wind_turbine`.
