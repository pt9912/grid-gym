# ADR 0077 — Battery-Field-Envelope-Vollstaendigkeit: soh/dc_voltage/reactive-Emissionen + Fault-Status-Surface

**Status:** Proposed (2026-07-13) — die **Richtung** ist entschieden (drei additive
opt-in Battery-Emissionen + eine Fault-Status-Surface, damit die Battery-Telemetrie
den bess-ems-Feldenvelope-Vertrag deckt), die Modelle sind design-first fixiert, die
Implementierung steht aus. Fundament fuer [`ADR 0078`](0078-bess-ems-field-contract-publisher.md)
(der Publisher konsumiert diese Emissionen).
**Datum:** 2026-07-13
**Bezug:**

- [`ADR 0075`](0075-field-server-surface-device-endpoint-port.md) §7 — die
  Field-Server-Surface exponiert grid-gyms Geraete an ein externes EMS; dieser ADR
  vervollstaendigt die **Battery-Emissionsseite**, damit ein konformer Frame
  ([`ADR 0078`](0078-bess-ems-field-contract-publisher.md)) ueberhaupt bildbar ist.
- [`ADR 0065`](0065-battery-thermal-telemetry-pattern.md) (opt-in `temperature_celsius` via
  `ThermalConfig`) + [`ADR 0066`](0066-battery-cell-voltage-telemetry-pattern.md) (opt-in
  `cell_voltage_delta_v` via `CellConfig`) — das **etablierte opt-in-Sub-Config-
  Muster**, dem die drei neuen Bloecke folgen (`None` = aus, byte-identisch,
  `FIELD_NAMES`-Tupel fuer Snapshot).
- [`ADR 0025`](0025-fault-recovery-pattern.md) (`inject_fault`/`clear_fault`,
  `_<fault_type>_active`-Flags, snapshot-erfasst) — die Quelle der neuen
  Fault-Status-Surface.
- [`ADR 0014`](0014-battery-snapshot-schema.md) §2.4 (alphabetisch-sortierte,
  deterministische Emissions-Reihenfolge) + [`GG-DATA-005`](../../../spec/lastenheft.md#gg-data-005) (6-Nachkommastellen-
  Quantisierung der Telemetrie).
- [`GG-TEST-004`](../../../spec/lastenheft.md#gg-test-004) (HIL/SUT-Konsum durch ein
  externes EMS) + [`GG-BESS-001`](../../../spec/lastenheft.md#gg-bess-001)..008.

---

## 1. Kontext

Der bess-ems-Feldenvelope (Schwesterrepo, `mqtt-telemetry-envelope.schema.json`,
`$defs.telemetry.required`) verlangt **zehn** Felder je Tick+Asset: `offset_millis`,
`soc_percent`, `soh_percent`, `active_power_kw`, `reactive_power_kvar`, `dc_voltage`,
`dc_current`, `temperature_celsius`, `available`, `fault_status`. grid-gyms Battery
emittiert heute drei Bestands-Metriken (`power_kw`, `soc_kwh`, `soc_pct`) + zwei
opt-in (`temperature_celsius`, `cell_voltage_delta_v`).

Die **adapter-seitige Uebersetzung** (Umbenennung, Vorzeichen, `offset_millis`,
`dc_current`-Ableitung) ist Gegenstand von
[`ADR 0078`](0078-bess-ems-field-contract-publisher.md). Was dort **nicht**
adapter-seitig erfindbar ist, sind drei **echte physikalische Groessen** und der
**Fault-Zustand** — sie muessen im Geraetemodell entstehen (Determinismus,
Snapshot-Erfassung, physikalische Ehrlichkeit), nicht als Adapter-Konstanten:

- `soh_percent` — State of Health (Alterung).
- `dc_voltage` — DC-Bus-/Pack-Klemmenspannung.
- `reactive_power_kvar` — Blindleistung.
- `available` / `fault_status` — betrieblicher Zustand aus aktiven Faults.

`dc_current` ist **abgeleitet** (`= active_power_kw·1000 / dc_voltage`, P=V·I) und
lebt darum im Adapter ([`ADR 0078`](0078-bess-ems-field-contract-publisher.md) §2.2),
nicht hier.

**Entscheidung „voll modelliert" (User, 2026-07-13):** echte Emissionsmodelle statt
dokumentierter Adapter-Defaults — der `fault`-Topic + das Safe-Stop-Verhalten des EMS
werden dadurch real exercisebar (ein Default `available=true`/`fault_status="ok"`
haette den E2E-Abnahmepunkt verfehlt).

---

## 2. Entscheidung

### §2.1 Drei additive opt-in Sub-Config-Bloecke (Muster [`ADR 0065`](0065-battery-thermal-telemetry-pattern.md)/[`ADR 0066`](0066-battery-cell-voltage-telemetry-pattern.md))

`BatteryConfig` erhaelt drei neue **opt-in** Felder, je `None`-Default:

- `health: HealthConfig | None`
- `dc_bus: DcBusConfig | None`
- `reactive: ReactiveConfig | None`

Jeder Block ist eine frozen-dataclass mit `__post_init__`-Wertebereich-Validierung
(typisierte `BatteryConfigInvalidValueError`), einem `FIELD_NAMES`-Tupel (No-float +
Snapshot-Serialisierung) und emittiert **seine** Metrik nur bei aktivem Block. **Alle
Bloecke `None` → bit-genau heutiges Verhalten** (keine neuen Punkte, `scenario_hash`/
Snapshot unveraendert) — dieselbe pin-neutrale Invariante wie 0065/0066.

### §2.2 `soh_percent` — HealthConfig (Nominal + deterministische EFC-Degradation)

`HealthConfig(initial_soh_pct, degradation_pct_per_full_cycle=0)`. SOH ist
Geraete-State (`_soh_pct`), kaltgestartet auf `initial_soh_pct`. Pro Tick akkumuliert
ein **Equivalent-Full-Cycle**-Zaehler aus dem Energiedurchsatz
(`efc += |energy_delta_kwh| / (2·capacity_kwh)`), und
`soh = initial_soh_pct − degradation_pct_per_full_cycle·efc` (geklemmt `≥ 0`). Bei
`degradation=0` (Default) ist SOH **konstant** ueber den Lauf — physikalisch ehrlich
(reale Degradation ist ueber Sim-Laufzeiten vernachlaessigbar; der Vertrag verlangt
nur einen plausiblen, deterministischen Wert). `_soh_pct` + `_efc` sind
Snapshot-State.

### §2.3 `dc_voltage` — DcBusConfig (OCV-vs-SOC + IR-Drop) und die Zellmodell-Versoehnung

`DcBusConfig(nominal_voltage_v, ocv_soc_slope_v=0, internal_resistance_ohm=0)`. Die
DC-Bus-/Pack-Klemmenspannung als deterministisches Modell:

    ocv    = nominal_voltage_v + ocv_soc_slope_v·(soc_frac − 0.5)
    i_dc   = power_kw·1000 / ocv        # grid-gym-Vorzeichen: Laden = +
    dc_voltage = ocv + i_dc·internal_resistance_ohm

**IR-Drop-Vorzeichen (Review-Fund):** die Klemmenspannung liegt beim **Laden**
(Strom in die Batterie, `i_dc > 0`) **ueber** OCV, beim Entladen darunter — daher
`+ i_dc·R` (mit grid-gyms Laden-=-**+**-Konvention). Bei `ocv_soc_slope_v=0` **und**
`internal_resistance_ohm=0` (Default) ist `dc_voltage = nominal_voltage_v` konstant.
Der Golden-Vektor (`telemetry-charging.dc_voltage=798.5 < 800`) ist **strukturell/
illustrativ**, nicht physikalisch stimmig (er senkt die Ladespannung); das Modell wird
**nicht** darauf gefittet — der Golden-Vergleich ist wertfrei (§2.6/[`ADR 0078`](0078-bess-ems-field-contract-publisher.md) §2.6).

**Versoehnung mit [`ADR 0066`](0066-battery-cell-voltage-telemetry-pattern.md) (Review-Punkt).**
`CellConfig` traegt bereits `nominal_pack_voltage_v` (die Summen-Nennspannung des
Packs); `dc_voltage` ist **dieselbe physikalische Groesse** (Pack-Klemmenspannung).
Um **kein zweites Spannungskonzept** einzufuehren:

- Die Bloecke bleiben **unabhaengig** (opt-in-Symmetrie zu 0065/0066), modellieren aber
  bewusst getrennte Aspekte: `cell` = Zell-**Spreizung** (`cell_voltage_delta_v`),
  `dc_bus` = Pack-**Klemmenspannung** (`dc_voltage`).
- Sind **beide** aktiv, **validiert** `BatteryConfig.__post_init__`
  `dc_bus.nominal_voltage_v == cell.nominal_pack_voltage_v` (typisierter Fehler bei
  Divergenz) — eine Nennspannung, zwei Sichten. So bleibt die Single-Source erhalten,
  ohne die Bloecke hart zu koppeln.

### §2.4 `reactive_power_kvar` — ReactiveConfig (Power-Factor)

`ReactiveConfig(power_factor=1)` mit `0 < power_factor ≤ 1`. Blindleistung aus der
Wirkleistung ueber einen konstanten Leistungsfaktor:

    reactive_power_kvar = |power_kw| · q_factor,   q_factor = sqrt(1 − pf²) / pf

**Vollstaendig libm-frei (Review-Kleinigkeit a):** `tan(acos(pf))` ist identisch
`sqrt(1 − pf²)/pf` und damit **rein in `Decimal`** rechenbar (`Decimal.sqrt()`, kein
`float`/`math`) — passt zum [`GG-DATA-005`](../../../spec/lastenheft.md#gg-data-005)-Geist.
`q_factor` wird **einmal bei Konstruktion** aus dem `Decimal`-`pf` vorgerechnet; der
Tick multipliziert nur `|power_kw|·q_factor`. Bei `power_factor=1` (Default) ist `Q=0`.
Vorzeichenkonvention (kapazitiv/induktiv) ist im Feldenvelope nicht spezifiziert →
positiv (Betrag), Verfeinerung deferred.

### §2.5 Fault-Status-Surface — `available` / `fault_status` aus aktiven Faults

Die Battery erhaelt zwei **berechnete Read-Properties** (kein neuer State — sie lesen
die bestehenden `_<fault_type>_active`-Flags aus [`ADR 0025`](0025-fault-recovery-pattern.md),
die bereits snapshot-erfasst sind):

- `fault_status: str` — `"ok"`, wenn kein device-adressierter Fault aktiv ist; sonst
  der Fault-Typ-String des aktiven Faults (heute nur `"cell_failure"`; neue
  device-Fault-Typen tragen sich additiv ein). Bei mehreren aktiven Faults gewinnt eine
  **deterministische Prioritaetsordnung** (fixe Typ-Reihenfolge, in der ADR-Impl-Notiz
  gepinnt).
- `available: bool` — `False` gdw. ein **betriebsverhindernder** Fault aktiv ist
  (Closed-Set, heute `cell_failure`); sonst `True`.

Diese Surface ist **kein** Telemetrie-Punkt (sie geht nicht in `emitted_telemetry`) —
sie wird vom Publisher ([`ADR 0078`](0078-bess-ems-field-contract-publisher.md))
je Tick abgefragt und in `status`/`fault`-Topics uebersetzt. Damit bleibt der
Telemetrie-Strom ([`GG-DATA-004`](../../../spec/lastenheft.md#gg-data-004)) unberuehrt; die Fault-Status-Surface ist eine
**Projektion** des Fault-State.

### §2.6 Determinismus + Snapshot-Grenze

- Neuer State (`_soh_pct`, `_efc`) ist **snapshot-erfasst** (additive Sub-Snapshot-
  Slots, Muster 0065/0066); `dc_voltage`/`reactive` sind **zustandslos** (reine
  Funktion aus `power_kw`/`soc`), die Fault-Surface liest bestehende Flags.
- Alle Bloecke `None` → keine neuen Punkte, kein neuer State → **pin-neutral**.

### §2.7 Quantisierung

Alle neuen numerischen Emissionen quantisieren auf 6 Nachkommastellen
(`ROUND_HALF_EVEN`, `_QUANTUM`), konsistent mit den Bestands-Emissionen ([`GG-DATA-005`](../../../spec/lastenheft.md#gg-data-005)).

---

## 3. Begruendung

- **Ein ADR, drei ko-motivierte Modelle.** Anders als 0065/0066 (unabhaengige
  M8-Features zu verschiedenen Zeiten) entstehen soh/dc_voltage/reactive **gemeinsam**
  fuer **ein** Ziel (bess-ems-Envelope-Vollstaendigkeit); ein gebuendelter ADR mit drei
  Modell-§§ ist ehrlicher als drei Mini-ADRs (User-Entscheid Buendelung).
- **Modelle bewusst simpel + deterministisch.** Jedes Default-Verhalten (kein
  Degradations-/OCV-/PF-Effekt) ist ein **konstanter** Wert — deckt den
  quasi-statischen Golden-Vektor, laesst aber echte Physik zu, wenn konfiguriert. Kein
  `float`-`math` im Tick (vorberechnete `Decimal`-Faktoren).
- **Fault-Surface als Projektion, kein Telemetrie-Eingriff.** `available`/`fault_status`
  aus bestehenden Flags abgeleitet — kein neuer Fault-State, keine Snapshot-Erweiterung
  fuer die Surface, der `emitted_telemetry`-Vertrag bleibt unberuehrt.
- **Additiv/opt-in.** Bestands-Laeufe byte-identisch; nur eine explizit konfigurierte
  Battery traegt die neuen Felder.

---

## 4. Alternativen

- **Adapter-Defaults (verworfen, User-Entscheid „voll modelliert"):** soh/dc_voltage/
  reactive/available/fault_status als statische Publisher-Konstanten. Kleiner, aber
  `available=true`/`fault_status="ok"` waeren nie faultig → der `fault`-Topic + der
  Safe-Stop-E2E ([`ADR 0078`](0078-bess-ems-field-contract-publisher.md) §2.6) waeren
  nicht belegbar.
- **Voll-dynamische Modelle (verworfen als Primaer):** echte SOH-Degradations-Kinetik,
  temperatur-/altersabhaengige OCV-Kurven, Q(U)-Regelung. Physikalisch reicher, aber
  fuer den bess-ems-Smoke nicht noetig (Golden nutzt quasi-statische Werte) — die
  Config-Bloecke halten den Pfad **additiv offen** (Slope/Resistance/Degradation-
  Parameter existieren bereits).
- **Je-Metrik-ADR (verworfen, Buendelung):** Praezedenz 0065/0066, aber hier
  ko-motiviert + je trivial.

---

## 5. Lieferschnitt

Design-first (diese ADR); Implementierung im [`Slice 077`](../planning/next/077-bess-ems-conformant-field-publisher.md)-S1
(Battery-Emissionen + Fault-Surface, additiv/unit-getestet). Der Publisher-Konsum
liegt in S2 ([`ADR 0078`](0078-bess-ems-field-contract-publisher.md)).

---

## 6. Konsequenzen

- **Positiv:** die Battery-Telemetrie deckt den bess-ems-Envelope (mit dem Publisher);
  echte Fault-Sichtbarkeit macht den Safe-Stop-E2E fahrbar; opt-in → Bestands-Laeufe
  byte-identisch.
- **Neutral:** drei neue Config-Bloecke + zwei Snapshot-Slots (`_soh_pct`/`_efc`); die
  `dc_bus`↔`cell`-Nennspannungs-Validierung.
- **Bewusste Grenze:** die Modelle sind quasi-statisch by default; echte
  Degradations-/OCV-/Q-Dynamik ist konfigurier-, aber nicht smoke-noetig.

---

## 7. Nicht Gegenstand dieser ADR

- **Feld-Mapping + Publisher** (Umbenennung, Vorzeichen-Flip, `offset_millis`,
  `dc_current`-Ableitung, Topics, Kadenz) — [`ADR 0078`](0078-bess-ems-field-contract-publisher.md).
- **MQTT-`command`/`command_ack`-Konsum** — bess-ems haelt den Command-Loop deferred;
  die Schreib-Richtung existiert ueber Modbus ([`ADR 0076`](0076-inbound-write-exogenous-input-recording.md)).
- **Exakte Fault-Prioritaets- + `available`-Closed-Set-Semantik** bei mehreren
  device-Fault-Typen — heute trivial (nur `cell_failure`); die S1-Impl-Notiz pinnt die
  Ordnung, wenn ein zweiter device-Battery-Fault existiert.
