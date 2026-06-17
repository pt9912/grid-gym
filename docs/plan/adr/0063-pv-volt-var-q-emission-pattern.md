# ADR 0063 — PV-Q(U)-Emission + Spannungs-Feedback (M8 Welle 3c-b-1)

**Status:** Accepted — Validierung mit M8-Welle-3c-b-1-Lieferung
(static-gates + test-unit + `coverage-gate-critical` ≥ 90 % auf
`grid_model`/`devices/pv` + `docs-check` + `accept-pin-check` gruen;
Q(U)-Deadband-/Droop-/Clamp-Pins + Lagged-Feedback-Determinismus +
Q-frei-Pin-Neutralitaet). Folge zu
[`ADR 0016`](0016-pv-load-device-pattern.md) (PV-Geraet) und Schaerfung-
Familie zu [`ADR 0062`](0062-reactive-power-bilanz-pattern.md) (Q-Bilanz);
kein Supersede.
**Datum:** 2026-06-16
**Bezug:**
[`ADR 0016`](0016-pv-load-device-pattern.md) §2.2/§2.5 (PV-Telemetrie +
Sign-Konvention — Q ist additive Telemetrie neben `power_kw`),
[`ADR 0062`](0062-reactive-power-bilanz-pattern.md) §2.1 (Q-Bilanz +
Q-Spannungskopplung — 3c-b-1 speist den `reactive_power_kvar`-Eingang),
[`ADR 0013`](0013-device-model-protocol.md) §2.1 (`DeviceTickContext` —
3c-b-1 ergaenzt `grid_voltage_v`),
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.7 (Determinismus).
Slice-Plan [`M8-welle-3c.md`](../planning/done/M8-welle-3c.md) §4
(Re-Tranche 3c-b-1/3c-b-2). Trigger
[`022`](../planning/open/022-sollte-reactive-power.md) ([`GG-GRID-007`](../../../spec/lastenheft.md#gg-grid-007);
**teilweise** — schliesst mit 3c-b-2).

---

## 1. Kontext

[`ADR 0062`](0062-reactive-power-bilanz-pattern.md) (3c-a) hat die
**Q-Bilanz im `grid_model`** geliefert (`imbalance_kvar` +
Q-Spannungskopplung), aber **kein Geraet emittiert Q** — der
`reactive_power_kvar`-Eingang der Bilanz ist zur Laufzeit `0`. 3c-b-1
liefert die **erste Q-Quelle**: der PV-Wechselrichter mit einer
**Q(U)-Kennlinie** (Volt-Var), plus die Infrastruktur, die den
Spannungs-Eingang an die Geraete bringt und die Geraete-Q in die Bilanz
aggregiert.

**Re-Tranche (Slice-Plan §4):** 3c-b-1 deckt PV-Q(U) + Feedback-Infra +
Q-Aggregation. **Deferred auf 3c-b-2:** GridConnection-Q-Auto-Schluss,
Transformer-Scheinleistung `S = sqrt(P²+Q²)` (re-pinnt die 3b-Boundary-
Tests), Trigger-022-Closure.

**Pin-neutral (opt-in):** die Q-Emission ist **opt-in pro Geraet** — ein PV
**ohne** konfigurierte Q(U)-Kurve emittiert **keine** `reactive_power_kvar`-
Telemetrie (nicht `0 kvar` — gar keinen Punkt). Der Q-freie MVP-Demo
konfiguriert keine Q(U)-Kurve → Telemetry-Stream unveraendert →
`EXPECTED_DEMO_*` unberuehrt (konsistent mit 3a/3b/3c-a).

---

## 2. Entscheidung

### 2.1 Spannungs-Feedback: `DeviceTickContext.grid_voltage_v`

`DeviceTickContext` ([`ADR 0013`](0013-device-model-protocol.md)) bekommt
ein additives, optionales Feld `grid_voltage_v: Decimal | None = None`.
Der TickLoop fuellt es **vor** der Geraete-Iteration mit der **aktuellen
`GridModelBilanz.voltage_v`** — das ist die Spannung aus dem **vorigen**
Tick (`grid_model.update(...)` laeuft erst **nach** der Iteration). Damit
ist die Q(U)-Kopplung **lagged** (explizit, ohne Iteration) und
deterministisch.

`None` = keine Spannungsinformation (kein `grid_model` im Loop bzw.
Standalone-Konstruktion). Ein Q(U)-Geraet emittiert dann **kein** Q (es
kann ohne Spannung nicht auswerten). Bestands-Geraete (ohne Q(U)) ignorieren
das Feld → bit-genau.

### 2.2 PV-Volt-Var: `VoltVarConfig` (opt-in)

`PvConfig` bekommt ein additives, optionales `volt_var: VoltVarConfig | None
= None`. `VoltVarConfig` ist eine eigene Frozen-Dataclass mit Validierung
(`PvConfigInvalidValueError`):

| Feld | Einheit | Invariante |
|---|---|---|
| `reference_voltage_v` | V | `> 0` (Q=0 in der Deadband um diese Spannung) |
| `deadband_v` | V | `>= 0` (Halbbreite der Deadband) |
| `droop_kvar_per_v` | kvar/V | `> 0` (Steigung ausserhalb der Deadband) |
| `max_kvar` | kvar | `> 0` (Betrags-Clamp) |

**Q(U)-Auswertung** (gegen `grid_voltage_v = U`):

```
dv          = U - reference_voltage_v
abs_excess  = max(0, |dv| - deadband_v)
magnitude   = min(droop_kvar_per_v * abs_excess, max_kvar)
Q           = -magnitude   wenn dv > 0   (hohe Spannung → induktiv absorbieren)
            = +magnitude   wenn dv < 0   (niedrige Spannung → kapazitiv einspeisen)
            = 0            wenn dv == 0
```

Sign-Konvention spiegelt [`ADR 0062`](0062-reactive-power-bilanz-pattern.md)
§2.1: `+Q` (Einspeisung) hebt die Spannung — also speist das Geraet bei
**niedriger** Spannung `+Q` ein (**negatives** Feedback, stabilisierend).

### 2.3 Q-Telemetrie (opt-in)

Hat das PV eine `volt_var`-Kurve **und** ist `context.grid_voltage_v`
gesetzt, emittiert `tick()` **zusaetzlich** zum `power_kw`-Punkt einen
`reactive_power_kvar`-`TelemetryPoint` (`source="pv"`, `unit="kvar"`).
**Ohne Kurve (oder ohne Spannung): kein Q-Punkt** — nicht `0 kvar`, gar
kein Punkt (Trigger-022-Pin-Neutralitaet). Decimal-Quantisierung wie
`power_kw`.

### 2.4 TickLoop-Q-Aggregation

Die Geraete-Iteration aggregiert `reactive_power_kvar`-Telemetrie
**vorzeichenrichtig** in einen `reactive_kvar`-Bilanz-Bucket (Summe ueber
alle Q-Geraete; kein `_BILANZ_SOURCE_BUCKETS`-Vorzeichen-Flip — die Geraete
emittieren signiertes Q). Der Bucket wird als `reactive_power_kvar` an
`grid_model.update(...)` ([`ADR 0062`](0062-reactive-power-bilanz-pattern.md)
§2.1) gereicht. Ohne Q-Geraet ist der Bucket `0` → Bilanz wie 3c-a.

### 2.5 Snapshot (PV) — opt-in, kein Versions-Bump

Der `PvSnapshot` (v1) bettet `PvConfig` ein. `volt_var` wird im
`config`-Sub-Mapping **opt-in** serialisiert (nur wenn gesetzt) →
Q-frei-PV byte-identisch (kein Versions-Bump; Pattern-Spiegel
[`ADR 0060`](0060-island-grid-bilanz-pattern.md) §2.4). `from_dict` liest
`volt_var` optional (fehlt → `None`). Der `GridModelSnapshot` ist von 3c-b-1
**nicht** beruehrt (Q ist Geraete-Telemetrie + Bilanz-Input, kein neuer
Bilanz-State ueber 3c-a hinaus).

### 2.6 Determinismus + Pin-Neutralitaet

- **Q-frei pin-neutral:** ohne `volt_var` keine Q-Telemetrie → Stream +
  PV-Snapshot byte-identisch → `EXPECTED_DEMO_*` unberuehrt (Pflicht-Pin).
- **Lagged-Feedback-Determinismus:** gleiche Geraete-/Input-Sequenz →
  byte-identische Q-/Spannungs-Spur ueber ≥ 100 Ticks (Hypothesis;
  Decimal-Context). Die Lag (voriger-Tick-Spannung) ist explizit, ohne
  Iteration.

---

## 3. Begruendung

**Lagged statt iterativ:** echte Volt-Var-Regelung ist eine Fixpunkt-
Iteration (Q ↔ U). Im quasi-statischen, vereinfachten Bilanzmodell ist die
**explizite Lag** (Geraet nutzt die Spannung des vorigen Ticks) Standard:
deterministisch, ohne Konvergenz-/Abbruch-Heuristik, ohne Float-Iteration.
Bei vernuenftigen `droop`/`k_vq` konvergiert das System ueber Ticks; die
Property pinnt die Determinismus-Eigenschaft unabhaengig davon.

**`grid_voltage_v` im Context statt Port:** die Spannung ist ein
Tick-Eingang wie `tick_ms`/`simulation_time` — `DeviceTickContext` ist der
etablierte Kanal. Ein eigener Port waere fuer einen reinen Lese-Skalar
ueberdimensioniert. `None`-Default haelt Bestands-Konstruktionen + Nicht-Q-
Geraete bit-genau.

**Opt-in / kein 0-kvar-Punkt:** ein `0 kvar`-Punkt fuer jedes Q-faehige
Geraet wuerde den Demo-Telemetry-Stream aufblaehen und `EXPECTED_DEMO_*`
ohne fachlichen Grund verschieben. „Keine Kurve → kein Punkt" haelt den
additiven Zuwachs byte-neutral (Welle-3-Linie) und macht Q-Emission zu
einer bewusst konfigurierten Faehigkeit.

---

## 4. Reichweite

Gilt fuer: `hexagon/core/domain/device.py` (`DeviceTickContext.grid_voltage_v`),
`hexagon/core/devices/pv/config.py` (`VoltVarConfig` + Feld),
`hexagon/core/devices/pv/model.py` (Q(U)-Auswertung + Telemetrie +
Param-Parsing), `hexagon/core/devices/pv/snapshot.py` (opt-in `volt_var`),
`hexagon/core/simulation/tick_loop.py` (lagged `grid_voltage_v` +
`reactive_kvar`-Bucket → `grid_model.update`),
`tests/unit/hexagon/core/devices/pv|simulation|domain/`.

Gilt NICHT fuer (→ 3c-b-2): GridConnection-Q-Auto-Schluss, Transformer
`S = sqrt(P²+Q²)` + 3b-Boundary-Re-Pin, Trigger-022-Closure. Out-of-scope:
Synchron-/Asynchronmaschinen-Detail, volle Lastflussrechnung.

---

## 5. Konsequenzen

**Was sich aendert:**

- `DeviceTickContext` traegt `grid_voltage_v` (optional, Default `None`).
- PV kann eine Volt-Var-Kurve tragen + Q(U)-Telemetrie emittieren.
- Der TickLoop verdrahtet die lagged Grid-Spannung + die Q-Aggregation in
  die 3c-a-Bilanz.

**Was load-bearing bleibt:**

- [`ADR 0016`](0016-pv-load-device-pattern.md) PV-`power_kw`-Pfad
  (unveraendert; Q ist additiv).
- [`ADR 0062`](0062-reactive-power-bilanz-pattern.md) Q-Bilanz (3c-b-1
  speist nur den Eingang).
- `EXPECTED_DEMO_*` (pin-neutral via opt-in).

**Was offen bleibt (3c-b-2):** GridConnection-Q, Transformer-`S`,
Trigger-022-Closure.

---

## 6. Akzeptanzkriterien (Trigger 022 — teilweise)

- [ ] `DeviceTickContext.grid_voltage_v` (lagged) verdrahtet.
- [ ] PV-`VoltVarConfig` opt-in + Q(U)-Auswertung (Deadband/Droop/Clamp/
      Vorzeichen) + Q-Telemetrie nur bei Kurve.
- [ ] TickLoop-`reactive_kvar`-Aggregation → `grid_model.update`.
- [ ] Q-frei: `EXPECTED_DEMO_*` + PV-Snapshot byte-identisch (Pin);
      ≥ 100-Tick-Lagged-Feedback-Determinismus.
- [ ] static-gates + accept-pin-check gruen; NEU ADR `Accepted`.
      **Trigger 022 schliesst mit 3c-b-2.**

---

## 7. Nicht Gegenstand dieser ADR

- **GridConnection-Q-Auto-Schluss** — 3c-b-2.
- **Transformer-Scheinleistung `S = sqrt(P²+Q²)`** + 3b-Boundary-Re-Pin
  ([`ADR 0061`](0061-transformer-limit-bilanz-pattern.md)) — 3c-b-2.
- **Iterative Volt-Var-Fixpunkt-Regelung** — die explizite Lag genuegt fuer
  das vereinfachte Bilanzmodell.
- **Synchron-/Asynchronmaschinen-Detail / volle Lastflussrechnung** —
  dauerhaft out-of-scope.
