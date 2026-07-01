# ADR 0064 — GridConnection-Q-Auto-Schluss + Transformer-Scheinleistung (M8 Welle 3c-b-2)

**Status:** Accepted — Validierung mit M8-Welle-3c-b-2-Lieferung
(static-gates + test-unit + `coverage-gate-critical` ≥ 90 % auf
`grid_model`/`devices/grid_connection` + `docs-check` + `accept-pin-check`
gruen; `S=sqrt(P²)==|P|`-Q=0-Regressionspin + Q≠0-Boundary-Pins +
Q-Absorptions-/Pin-Neutralitaets-Pins). **Schliesst [`GG-GRID-007`](../../../spec/lastenheft.md#gg-grid-007)**
(Trigger [`022`](../planning/done-archive/022-sollte-reactive-power.md)). Folge zu
[`ADR 0017`](0017-grid-connection-device-pattern.md) (GridConnection) +
Schaerfung zu [`ADR 0061`](0061-transformer-limit-bilanz-pattern.md)
(Transformer-Grenze) / [`ADR 0062`](0062-reactive-power-bilanz-pattern.md)
(Q-Bilanz); kein Supersede.
**Datum:** 2026-06-16
**Bezug:**
[`ADR 0017`](0017-grid-connection-device-pattern.md) §2.2/§2.7 (GridConnection
+ Auto-Schluss — der Q-Auto-Schluss spiegelt den P-Auto-Schluss),
[`ADR 0061`](0061-transformer-limit-bilanz-pattern.md) §2.2 (Transformer-`S`
— bis hier `|P|`, jetzt `sqrt(P²+Q²)`),
[`ADR 0062`](0062-reactive-power-bilanz-pattern.md) §2.1 (Q-Bilanz),
[`ADR 0063`](0063-pv-volt-var-q-emission-pattern.md) §2.4 (TickLoop-Q-
Aggregation — der GridConnection ist die zweite Q-Quelle/-Senke).
Slice-Plan [`M8-welle-3c.md`](../planning/done/M8-welle-3c.md) §4
(Re-Tranche 3c-b-2). Trigger
[`022`](../planning/done-archive/022-sollte-reactive-power.md) ([`GG-GRID-007`](../../../spec/lastenheft.md#gg-grid-007);
**mit dieser ADR aufgeloest**).

---

## 1. Kontext

Nach 3c-b-1 ([`ADR 0063`](0063-pv-volt-var-q-emission-pattern.md)) emittiert
das PV Q(U), der TickLoop aggregiert es in `imbalance_kvar`. **Offen:** im
netzgekoppelten Fall absorbiert real der Netzanschluss die Blindleistung
(wie er die Wirkleistung absorbiert), und die Transformer-Grenze
([`ADR 0061`](0061-transformer-limit-bilanz-pattern.md)) rechnete bis hier
auf `S ≈ |P|`. 3c-b-2 schliesst beides und **[`GG-GRID-007`](../../../spec/lastenheft.md#gg-grid-007)**:

- **GridConnection-Q-Auto-Schluss**: der Netzanschluss absorbiert den
  Q-Residual (parallel zum P-Auto-Schluss, [`ADR 0017`](0017-grid-connection-device-pattern.md)
  §2.7) und emittiert `reactive_power_kvar` — die zweite Q-Quelle/-Senke.
- **Transformer-Scheinleistung** `S = sqrt(P²+Q²)` statt `|P|`.

**Pin-neutral (opt-in):** ohne Q-Quelle (Q-frei) ist der Q-Residual `0`, der
GridConnection emittiert **kein** `reactive_power_kvar` (nicht `0 kvar`), und
`S = sqrt(P²+0) = |P|` bit-genau — die 3b-Boundary-Tests bleiben gruen, der
MVP-Demo-Telemetry-Stream unveraendert (`EXPECTED_DEMO_*` unberuehrt).

---

## 2. Entscheidung

### 2.1 GridConnection-Q-Auto-Schluss

Der TickLoop-Auto-Schluss ([`ADR 0017`](0017-grid-connection-device-pattern.md)
§2.7 / [`ADR 0063`](0063-pv-volt-var-q-emission-pattern.md) §2.4) berechnet
nach der ersten Iteration den **Q-Residual** = `reactive_kvar`-Bucket (Summe
der Nicht-Grid-Geraete-Q, z. B. PV-Q(U)). Er setzt den GridConnection-Q auf
`-Q_residual` (Absorption) — ueber den **`reactive_value`-Key** im
bestehenden `set_power_kw`-Auto-Schluss-`Command` (kein neuer Command-Typ;
der Auto-Schluss ist der einzige Q-Setzer des Slack-Netzanschlusses).

Der GridConnection emittiert `reactive_power_kvar` **opt-in** — nur wenn der
aktuelle Q ≠ 0 (sortiert zwischen `power_kw` und `voltage_v`). `Q == 0`
(Q-frei) → kein Punkt → byte-identisch. Kein Q-Clamp in Welle 3 (der Slack
absorbiert unbegrenzt; ein Q-Limit ist Post-Welle-3-Material).

Nach der zweiten Iteration ist `reactive_kvar`-Bucket = `PV_Q + (-PV_Q) = 0`
→ `imbalance_kvar = 0` (der Netzanschluss haelt die Spannung, wie beim
P-Auto-Schluss). Die Q-Spannungs-Deviation
([`ADR 0062`](0062-reactive-power-bilanz-pattern.md) §2.1) tritt damit nur
**ohne** absorbierenden Netzanschluss auf (Inselnetz) bzw. bei manuellem/
begrenztem Grid-Q.

### 2.2 Transformer-Scheinleistung `S = sqrt(P²+Q²)`

`GridModelBilanz.update(...)` bekommt einen additiven Parameter
`grid_connection_kvar: Decimal = 0` — die Q **durch den Modell-Trafo** (=
GridConnection-Q = `-Q_residual`, vom TickLoop durchgereicht). Der
Transformer-Constraint ([`ADR 0061`](0061-transformer-limit-bilanz-pattern.md)
§2.2) rechnet:

```
S = sqrt(grid_connection_kw² + grid_connection_kvar²)   # Decimal.sqrt, prec=28
```

**Q=0-Regressionspin:** `sqrt(P²+0) = sqrt(P²) = |P|` ist fuer terminierende
Decimals **exakt** (kein Rundungs-Drift) → die 3b-Boundary-Tests
(`grid_connection_kvar == 0`) bleiben byte-identisch. `Decimal.sqrt()` ist im
`prec=28`/`ROUND_HALF_EVEN`-Context deterministisch; das Ergebnis fliesst
quantisiert in `load_pu` wie bisher.

### 2.3 Snapshot (GridConnection) — opt-in, kein Versions-Bump

Der `GridConnectionSnapshot` (v1) bekommt additive
`current_reactive_power_kvar`/`pending_reactive_power_kvar`-Felder **opt-in**
(nur wenn ≠ 0 emittiert; `from_dict` liest sie optional, Default `0`) →
Q-frei byte-identisch (kein Versions-Bump; Pattern-Spiegel
[`ADR 0063`](0063-pv-volt-var-q-emission-pattern.md) §2.5).

### 2.4 Determinismus + Pin-Neutralitaet

- **Q-frei pin-neutral:** kein Q-Residual → kein GridConnection-Q-Punkt,
  `S = |P|`, GridConnection-Snapshot byte-identisch → `EXPECTED_DEMO_*` +
  3b-Boundary-Pins unberuehrt (Pflicht-Pin).
- **Q≠0:** der Netzanschluss absorbiert PV-Q, `S = sqrt(P²+Q²)` waechst,
  neue Boundary-Pins; ≥ 100-Tick-Determinismus.

---

## 3. Begruendung

**Q-Auto-Schluss spiegelt den P-Auto-Schluss:** der Netzanschluss ist der
Slack — fuer Wirk- **und** Blindleistung. Den Q-Residual genauso zu
absorbieren wie den P-Residual haelt das Modell konsistent (eine
Slack-Logik, ein `Command`-Pfad via `reactive_value`) und liefert das
physikalisch dominante Verhalten: ein starker Netzanschluss haelt die
Spannung, lokale Q-Quellen (PV-Q(U)) werden abgefuehrt.

**`grid_connection_kvar` getrennt vom `imbalance_kvar`:** der Transformer
traegt die **Netzaustausch**-Scheinleistung (`sqrt(grid_P²+grid_Q²)`), nicht
die Gesamt-Q-Bilanz (die nach Absorption `0` ist). Darum ein eigener
`update(...)`-Parameter statt `reactive_power_kvar` (das ist der Spannungs-
Q-Term). Bei `Q=0` faellt `sqrt(P²)` exakt auf `|P|` zusammen — die
3b-Verzahnung ohne Verhaltensbruch.

**Opt-in / kein 0-kvar-Punkt:** identisch zu
[`ADR 0063`](0063-pv-volt-var-q-emission-pattern.md) §3 — Q-frei darf den
Demo-Stream nicht aufblaehen.

---

## 4. Reichweite

Gilt fuer: `hexagon/core/devices/grid_connection/model.py` (Q-State +
`reactive_value`-Apply + opt-in Q-Telemetrie),
`hexagon/core/devices/grid_connection/snapshot.py` (opt-in Q-State),
`hexagon/core/grid_model/bilanz.py` (`grid_connection_kvar` + `S=sqrt`),
`hexagon/core/simulation/tick_loop.py` (Q-Auto-Schluss + `grid_connection_kvar`),
`tests/unit/hexagon/core/devices/grid_connection|grid_model|simulation/`.

Gilt NICHT fuer: Q-Limit/-Clamp am Netzanschluss (Post-Welle-3), Q(U) am
GridConnection (Slack absorbiert, regelt nicht), Synchron-/Asynchron-
maschinen-Detail, volle Lastflussrechnung.

---

## 5. Konsequenzen

**Was sich aendert:**

- GridConnection absorbiert + emittiert Q (opt-in); ist die zweite
  Q-Quelle/-Senke ([`GG-GRID-007`](../../../spec/lastenheft.md#gg-grid-007)-Akzeptanz: PV **und** GridConnection).
- Die Transformer-Grenze nutzt die echte Scheinleistung `S=sqrt(P²+Q²)`.
- **Welle 3 (Netz) + [`GG-GRID-007`](../../../spec/lastenheft.md#gg-grid-007) vollstaendig** (3a/3b/3c-a/3c-b-1/3c-b-2).

**Was load-bearing bleibt:**

- [`ADR 0017`](0017-grid-connection-device-pattern.md) §2.7 P-Auto-Schluss
  (unveraendert; Q ist der Spiegel).
- [`ADR 0061`](0061-transformer-limit-bilanz-pattern.md) Thermomodell
  (nur die `S`-Basis aendert sich; Q=0 bit-genau).
- `EXPECTED_DEMO_*` + 3b-Boundary-Pins (pin-neutral).

---

## 6. Akzeptanzkriterien (Trigger 022 — Closure)

- [ ] GridConnection-Q-Auto-Schluss (absorbiert Q-Residual) + opt-in
      Q-Telemetrie (`Q≠0` → Punkt; `Q=0` → kein Punkt).
- [ ] Transformer `S = sqrt(P²+Q²)`; `Q=0 → |P|`-Regressionspin (3b-Boundary
      gruen) + Q≠0-Boundary-Pins.
- [ ] GridConnection-Snapshot opt-in Q-State; ≥ 100-Tick-Determinismus;
      Q-frei `EXPECTED_DEMO_*` unberuehrt.
- [ ] static-gates + accept-pin-check gruen; NEU ADR `Accepted`;
      **Trigger 022 Resolved** → Welle 3 komplett.

---

## 7. Nicht Gegenstand dieser ADR

- **Q-Limit/-Clamp am Netzanschluss** — der Slack absorbiert in Welle 3
  unbegrenzt; ein Q-Limit ist Post-Welle-3-Material.
- **Q(U)-Regelung am GridConnection** — der Netzanschluss ist Slack
  (absorbiert), nicht volt-var-regelnd (das ist das PV,
  [`ADR 0063`](0063-pv-volt-var-q-emission-pattern.md)).
- **Synchron-/Asynchronmaschinen-Detail / volle Lastflussrechnung** —
  dauerhaft out-of-scope.
