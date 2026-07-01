# ADR 0062 — Blindleistung im Netzbilanzmodell: Q-Bilanz + Schema-Bump (M8 Welle 3c-a)

**Status:** Accepted — Validierung mit M8-Welle-3c-a-Lieferung
(lint/format/typecheck/arch-check/test-unit/`coverage-gate-critical`
≥ 90 % auf `grid_model`/`docs-check`/`accept-pin-check` gruen;
Q-Bilanz-/Spannungskopplungs-Pins + Determinismus-Property +
Q-frei-Regressions-Pin + v2→v3-Backward-Compat-Roundtrip). Schaerfung von
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) ohne Supersedes
(Erweiterungs-Pattern [`ADR 0011`](0011-schaerfung-ohne-abloesung.md);
gleiche Familie wie [`ADR 0060`](0060-island-grid-bilanz-pattern.md)/[`ADR 0061`](0061-transformer-limit-bilanz-pattern.md)).
**Datum:** 2026-06-16
**Bezug:**
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.2/§2.4/§2.5/§2.6
(Imbalance-/Spannungs-Formel, Snapshot, Lifecycle — diese ADR ergaenzt
**Blindleistung parallel** zur Wirkleistungsbilanz, ohne den
Frequenz-Kern zu beruehren),
[`ADR 0020`](0020-load-profile-and-event-pattern.md) §2.6 (v1→v2-
Backward-Compat-Lesepfad — 3c-a spiegelt das Muster fuer v2→v3),
[`ADR 0060`](0060-island-grid-bilanz-pattern.md) §2.4 (opt-in Config-
Serialisierung im Snapshot + Scenario-Hash — die `voltage_sensitivity_v_per_kvar`
nutzt dasselbe Muster),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-ADR-
Pattern). Slice-Plan
[`M8-welle-3c.md`](../planning/done/M8-welle-3c.md) (§4 Re-Tranche
3c-a/3c-b); Container
[`M8-welle-3.md`](../planning/done/M8-welle-3.md). Trigger
[`022`](../planning/done-archive/022-sollte-reactive-power.md) ([`GG-GRID-007`](../../../spec/lastenheft.md#gg-grid-007),
Lastenheft §11.5; **teilweise** — Geraete-Q-Emission in 3c-b).

---

## 1. Kontext

[`ADR 0019`](0019-grid-model-bilanz-pattern.md) modelliert nur
**Wirkleistung**: `imbalance_kw` treibt Frequenz und Spannung proportional;
Blindleistung (`Q`) ist explizit out-of-scope (§7). Lastenheft [`GG-GRID-007`](../../../spec/lastenheft.md#gg-grid-007)
(Trigger [`022`](../planning/done-archive/022-sollte-reactive-power.md)) verlangt
**Blindleistung im Netzbilanzmodell**: `reactive_power_kvar` pro
Q-emittierendem Geraet (PV-Wechselrichter mit Q(U)-Kennlinie, GridConnection),
`imbalance_kvar` parallel zu `imbalance_kw`, plus die Schein­leistungs-Basis
`S = sqrt(P²+Q²)` fuer die Transformer-Grenze
([`ADR 0061`](0061-transformer-limit-bilanz-pattern.md)).

**Re-Tranche (Slice-Plan §4):** der volle Slice beruehrt mehrere Geraete +
Snapshot-Schemata und ueberschreitet die Tranchierungs-Schwelle. Diese ADR
deckt **3c-a** — die **Q-Bilanz im `grid_model`**:

- `imbalance_kvar` + Q-Spannungskopplung in `GridModelBilanz`.
- `GridModelSnapshot` v2→v3 (additives `last_imbalance_kvar`, backward-compat).
- `voltage_sensitivity_v_per_kvar` als additives, opt-in Config-Feld.

**Deferred auf 3c-b** (eigene ADR, Folge zu
[`ADR 0016`](0016-pv-load-device-pattern.md)/[`ADR 0017`](0017-grid-connection-device-pattern.md)):
Geraete-Q-Emission (PV-Q(U), GridConnection-Q) + Device-Snapshots +
TickLoop-Q-Aggregation + Transformer `S = sqrt(P²+Q²)` (re-pinnt die
3b-Boundary-Tests) + Demo-Telemetry-Re-Pin. **In 3c-a emittiert kein Geraet
Q** → `reactive_power_kvar` ist zur Laufzeit `0` (Test-Helper speisen Q,
wie der Welle-5a-Bilanz-Kern vor der TickLoop-Verdrahtung).

**Q-frei = bit-genau:** ohne Q-Eingang (`reactive_power_kvar == 0`) liefert
die Bilanz byte-identische Frequenz-/Spannungs-/Snapshot-Spuren wie unter
[`ADR 0019`](0019-grid-model-bilanz-pattern.md).

---

## 2. Entscheidung

### 2.1 `imbalance_kvar` + Q-Spannungskopplung

`GridModelBilanz.update(...)` bekommt einen additiven, optionalen Parameter
`reactive_power_kvar: Decimal = 0` (die aggregierte Blindleistung; in 3c-a
vom Test-Helper, ab 3c-b vom TickLoop-Q-Bucket). Die Bilanz fuehrt:

```
imbalance_kvar = reactive_power_kvar           # parallel zu imbalance_kw
voltage_v = nominal_voltage_v
          + voltage_sensitivity_v_per_kw   * imbalance_kw
          + voltage_sensitivity_v_per_kvar * imbalance_kvar
frequency_hz = nominal_frequency_hz + k_f * imbalance_kw   # Q-frei (unveraendert)
```

**Sign-Konvention** (Spiegel zu [`ADR 0019`](0019-grid-model-bilanz-pattern.md)
§2.2): positives `imbalance_kvar` (Blindleistungs-Ueberschuss / kapazitive
Einspeisung) → Spannung steigt; negatives (induktive Last) → Spannung faellt.
**Q wirkt nur auf die Spannung, nicht auf die Frequenz** (physikalisch:
Q-Spannung, P-Frequenz). Die bestehenden Safety-Clamps
([`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.3) greifen unveraendert
auf das (nun Q-erweiterte) `raw_volt`. `last_imbalance_kvar` ist neue
Property + Snapshot-State.

`reactive_power_kvar == 0` → der Q-Term ist `0` → `voltage_v` bit-identisch
zum heutigen Wert (Regressions-Pin Pflicht).

### 2.2 `voltage_sensitivity_v_per_kvar` — additives, opt-in Config-Feld

`GridModelConfig` bekommt `voltage_sensitivity_v_per_kvar: Decimal` mit
**Default** `Decimal("0.2")` (≈ 2× `voltage_sensitivity_v_per_kw`; Q koppelt
staerker an die Spannung als P). `__post_init__` validiert `> 0` (Decimal,
[`GG-DATA-005`](../../../spec/lastenheft.md#gg-data-005) no-float).

**Opt-in-Serialisierung** (Spiegel zu
[`ADR 0060`](0060-island-grid-bilanz-pattern.md) §2.4): das Feld wird im
Snapshot-`config`-Sub-Mapping und in der Scenario-Hash-`asdict`-Form **nur
emittiert/behalten, wenn es vom Default abweicht**. Default → byte-identisch
(`EXPECTED_DEMO_*` + Scenario-Hash unberuehrt). Begruendung: der Q-frei-Demo
setzt das Feld nicht; sein Wert ist fuer Q-frei ohnehin irrelevant
(`k_vq * 0 = 0`). Backward-compat-Lesepfad: fehlt das Feld, gilt der Default.

### 2.3 `GridModelSnapshot` v2 → v3

Das **Bilanz-Output** `last_imbalance_kvar` ist — anders als das opt-in
Config-Feld — ein **Kern-Zustand parallel zu `last_imbalance_kw`** und wird
darum **immer** emittiert. Das rechtfertigt einen sauberen Versions-Bump
(Pattern-Spiegel zum v1→v2-Bump,
[`ADR 0020`](0020-load-profile-and-event-pattern.md) §2.6):

- `SNAPSHOT_VERSION` v2 → v3; `_SUPPORTED_VERSIONS = {1, 2, 3}`.
- `to_dict()` emittiert v3 mit `last_imbalance_kvar` als Pflicht-Top-Level-Key.
- `from_dict()`:
  - v1/v2 (ohne `last_imbalance_kvar`): backward-compat → `last_imbalance_kvar
    = 0` (Q-frei).
  - v3: liest das Feld als Pflicht.

**Kein Demo-Pin-Effekt:** die `EXPECTED_DEMO_*`-Pins hashen den
**Telemetry-Stream** (`TickResult.emitted_telemetry`) und den
**Scenario-Hash** (Config) — **nicht** den `GridModelSnapshot`. Der v3-Bump
ist damit pin-neutral; die Demo-Telemetry-Re-Pin entsteht erst in 3c-b mit
der Geraete-Q-Telemetrie. `SnapshotEnvelope`
([`ADR 0015`](0015-snapshot-envelope-v2.md)) bleibt unveraendert (Q steckt
im Sub-Snapshot, nicht im Envelope-Body).

### 2.4 Determinismus

- **Q-frei bit-genau:** ohne Q-Eingang ist die volle Frequenz-/Spannungs-/
  Snapshot-Spur byte-identisch (Connected-Kern textlich unveraendert bis auf
  den additiven Q-Term, der bei `Q=0` verschwindet).
- **Q-Determinismus:** der Q-Spannungs-Term laeuft im bestehenden
  `prec=28`/`ROUND_HALF_EVEN`-Context; gleiche `(P, Q)`-Sequenz →
  byte-identische Spur ueber ≥ 100 Ticks (Hypothesis-Property).
- **Kein `sqrt` in 3c-a:** die Schein­leistung `S = sqrt(P²+Q²)` (mit der
  `Decimal`-`sqrt`-Praezisions-Frage) ist 3c-b-Material (Transformer-Grenze).

---

## 3. Begruendung

**Q nur auf die Spannung:** im vereinfachten Bilanzmodell koppelt
Wirkleistung an die Frequenz, Blindleistung an die Spannung — die saubere
Trennung haelt den Frequenz-Kern (`imbalance_kw`-Pfad) bit-genau und
modelliert die physikalisch dominante Q-U-Kopplung. Eine Q-Frequenz-Kopplung
waere im Single-Bus-Proportionalmodell nicht rechtfertigbar.

**Config-Feld opt-in, Snapshot-State per Bump:** zwei additive Groessen, zwei
Mechanismen — bewusst:
- `voltage_sensitivity_v_per_kvar` ist **Config-Input**; opt-in haelt den
  Q-frei-Demo (Scenario-Hash) byte-stabil, konsistent zu 3a/3b.
- `last_imbalance_kvar` ist **Bilanz-Output parallel zu `last_imbalance_kw`**;
  ein opt-in-Weglassen waere asymmetrisch (warum ist `kw` immer da, `kvar`
  bedingt?). Der Versions-Bump macht es zum First-Class-Feld — und ist
  pin-neutral (§2.3), also „kostenlos".

**3c-a vor 3c-b:** die Q-Bilanz + Schema-Migration zuerst isoliert
liefern (grid_model-only, kein Geraet, kein TickLoop, kein Demo-Re-Pin)
haelt den Diff klein und die Migration getrennt von der breiten
Geraete-Q-Emission (Slice-Plan §4 Re-Tranche).

---

## 4. Reichweite

Gilt fuer: `hexagon/core/grid_model/config.py`
(`voltage_sensitivity_v_per_kvar`), `hexagon/core/grid_model/bilanz.py`
(`reactive_power_kvar`-Input + `imbalance_kvar` + Q-Spannungskopplung +
v3-Snapshot), `hexagon/core/grid_model/snapshot.py` (v2→v3 + opt-in Config),
`hexagon/core/scenario/loader.py` + `validator.py` (YAML-Feld + Scenario-
Hash-opt-in), `tests/unit/hexagon/core/grid_model|scenario/`.

Gilt NICHT fuer (→ 3c-b): Geraete-Q-Emission (PV-Q(U), GridConnection-Q),
Device-Snapshots (`reactive_power_kvar`-Feld), TickLoop-Q-Aggregation,
Transformer `S = sqrt(P²+Q²)` + 3b-Boundary-Re-Pin, Demo-Telemetry-Re-Pin.
Out-of-scope (§5/3c §5): Synchron-/Asynchronmaschinen-Detail, volle
Lastflussrechnung.

---

## 5. Konsequenzen

**Was sich aendert:**

- `GridModelBilanz` traegt `last_imbalance_kvar` + Q-Spannungskopplung;
  `GridModelConfig` ein opt-in `voltage_sensitivity_v_per_kvar`-Feld.
- `GridModelSnapshot` ist v3; v1/v2-Snapshots bleiben backward-compat lesbar.
- Bestands-Tests, die `version == 2` pinnen, ziehen auf v3 nach (additive
  Migration, kein Verhaltenswechsel bei `Q=0`).

**Was load-bearing bleibt:**

- [`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.2 Imbalance-/Frequenz-
  Kern (unveraendert; Q ist additiv auf der Spannung).
- [`ADR 0015`](0015-snapshot-envelope-v2.md) `SnapshotEnvelope` (unberuehrt).
- `EXPECTED_DEMO_*`-Pins (pin-neutral in 3c-a).

**Was offen bleibt (3c-b):** Geraete-Q-Emission + Device-Snapshots +
TickLoop-Q-Bucket + Transformer-`S` + Demo-Re-Pin.

---

## 6. Akzeptanzkriterien (Trigger 022 — teilweise, Rest 3c-b)

- [ ] `imbalance_kvar` parallel zu `imbalance_kw`; Q-Spannungskopplung;
      `voltage_sensitivity_v_per_kvar` additiv + opt-in.
- [ ] `GridModelSnapshot` v2→v3 mit v1/v2-Backward-Compat-Lesepfad;
      Roundtrip alt+neu gepinnt.
- [ ] ≥ 100-Tick-Determinismus; `Q=0` bit-genau wie heute (Regressions-Pin);
      `EXPECTED_DEMO_*` unberuehrt.
- [ ] `make gates` gruen; NEU ADR `Accepted`. **Trigger 022 bleibt offen bis
      3c-b** (Geraete-Q-Emission).

---

## 7. Nicht Gegenstand dieser ADR

- **Geraete-Q-Emission** (PV-Q(U), GridConnection-Q) + Device-Snapshots — 3c-b.
- **Schein­leistung `S = sqrt(P²+Q²)`** + Transformer-Grenz-Re-Pin
  ([`ADR 0061`](0061-transformer-limit-bilanz-pattern.md)) — 3c-b.
- **Demo-Telemetry-Re-Pin** — 3c-b (Geraete-Q-Telemetrie aendert den Stream).
- **Synchron-/Asynchronmaschinen-Detail / volle Lastflussrechnung** —
  Power-Systems-Domain, dauerhaft out-of-scope.
