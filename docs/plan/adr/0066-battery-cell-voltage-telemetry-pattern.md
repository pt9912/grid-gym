# ADR 0066 — Battery-Zellspannung-Telemetrie (M8 Welle 4b)

**Status:** Accepted — Validierung mit M8-Welle-4b-Lieferung
(`make gates` gruen: lint/format-check/typecheck/arch-check/test-unit/
`coverage-gate-critical` ≥ 90 % auf `devices/battery` + `docs-check` +
`accept-pin-check`; ≥ 100-Tick-Determinismus-Property + Boundary-Pins
(noise=0-Gleichstand, noise>0-Delta-Bounded) + Resume-Fail-Loud-Pin
(aktives Rauschen ohne `attach_random` → fail-loud) + Inaktiv-Regressions-Pin
(`cell=None` byte-genau wie heute) + opt-in-Snapshot-Roundtrip inkl.
Tuple-Kanonik + v1-backward-compat-Lesepfad).
**Schliesst `GG-BESS-007`** (Trigger
[`024`](../planning/in-progress/M8-welle-4b.md)).
Additive **Schaerfung** von
[`ADR 0014`](0014-battery-snapshot-schema.md) (Battery-Snapshot-/Telemetrie-
Vertrag) ohne Supersede — Erweiterungs-Pattern
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md); Schwester-Slice zu
[`ADR 0065`](0065-battery-thermal-telemetry-pattern.md) (4a Temperatur).
**Datum:** 2026-06-17
**Bezug:**
[`ADR 0014`](0014-battery-snapshot-schema.md) §2.2/§2.4/§2.6 (Snapshot-Layout,
Tick-Telemetrie, Determinismus — diese ADR ergaenzt eine **additive opt-in
Telemetrie-/State-Flaeche** und den **ersten Battery-`RandomPort`-Konsum**),
[`ADR 0007`](0007-random-port.md) §5.2 (`RandomPort.sub_port`-Sub-Seed-
Konvention — pro Zelle ein Sub-Stream),
[`ADR 0057`](0057-wind-turbine-device-pattern.md) §2.4/§2.6 (erster
`RandomPort`-Konsument + `attach_random`-Resume-Vertrag — Praezedenz),
[`ADR 0065`](0065-battery-thermal-telemetry-pattern.md) (4a — opt-in
Telemetrie-Pattern + `## Historie`-freie zeitlose Linie),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Schaerfung-Pattern).
Slice-Plan [`M8-welle-4b.md`](../planning/in-progress/M8-welle-4b.md);
Container [`M8-welle-4.md`](../planning/in-progress/M8-welle-4.md). Trigger
[`024`](../planning/open/024-sollte-battery-cell-voltage.md) (`GG-BESS-007`,
Lastenheft §10.6; **mit dieser ADR aufgeloest**).

---

## 1. Kontext

[`ADR 0014`](0014-battery-snapshot-schema.md) deckt das Battery-Modell nur auf
**Pack-Niveau** ab (SOC, Strom/Leistung, Ramp). Lastenheft `GG-BESS-007`
(Trigger [`024`](../planning/open/024-sollte-battery-cell-voltage.md)) verlangt
**Zellspannungs-Telemetrie**: das Pack in `n_cells` Zellen aufgeloest, je mit
eigener Spannung, optional mit seeded Rauschen. Welle 4b ist die zweite
BESS-Telemetrie-Sub-Welle (nach 4a Temperatur) und der **erste
`RandomPort`-Konsument im Battery-Geraet** (Praezedenz:
[`ADR 0057`](0057-wind-turbine-device-pattern.md) Wind).

Wie 4a eine **reine additive Geraete-Schaerfung**: kein neues Geraet, kein
neuer Port/Adapter-Typ, **keine Bilanz-Beruehrung** (Zellspannung ist
geraete-interne Telemetrie). Der Zell-Layer ist **opt-in**: ohne `cell`-Block
(Default) ist das Verhalten bit-genau wie unter
[`ADR 0014`](0014-battery-snapshot-schema.md).

---

## 2. Entscheidung

### 2.1 Config — `CellConfig` (nested, opt-in)

`BatteryConfig` (`hexagon/core/devices/battery/config.py`) bekommt **ein
additives, optionales Feld** `cell: CellConfig | None = None`. `None` (Default)
= kein Zell-Modell = bit-genau heutiges Verhalten. `CellConfig` ist eine
Frozen-Dataclass (`slots=True`) mit `__post_init__`-Validierung (Verstoss →
`BatteryConfigInvalidValueError`):

| Feld | Typ | Invariante |
|---|---|---|
| `nominal_pack_voltage_v` | `Decimal` | `> 0` (Pack-Nennspannung) |
| `n_cells` | `int` | `>= 1` |
| `noise_amplitude_v` | `Decimal` | `>= 0` (Default `0`) |

`nominal_pack_voltage_v` ist die **neue, explizite Spannungsquelle** — die
Bestands-`BatteryConfig` trug keinen Pack-Spannungswert; SOC-/OCV-Kennlinien
bleiben out-of-scope (§7). Die No-float-/Typpruefung (`GG-DATA-005`) liegt —
wie im Bestands-Battery-Pattern — in den Parsern (`_cell_from_params` /
Snapshot-`assert_*`), nicht im Konstruktor.

### 2.2 Zellspannungs-Berechnung (pro Tick, derived)

Basisspannung je Zelle: `base = nominal_pack_voltage_v / n_cells`.

- **`noise_amplitude_v == 0`:** alle Zellen identisch `base` — rein
  deterministisch, **kein `RandomPort`-Zug** (kein `attach_random` noetig).
- **`noise_amplitude_v > 0`:** pro Zelle `i` und Tick `t`

  ```
  draw    = random.sub_port(f"cell-{i}").sub_port(f"tick-{t}").next_float()  # [0,1)
  noise   = (draw * 2 - 1) * noise_amplitude_v                               # [-amp, +amp)
  cell_i  = base + noise
  ```

  Die zweistufige Sub-Port-Ableitung macht das Rauschen **per-Zelle
  unabhaengig** (Sub-Name `cell-<idx>`) **und per-Tick variierend + tick-
  gekeyt** (Sub-Name `tick-<t>`). Da `sub_port` zustandslos vom Parent-Seed
  ableitet ([`ADR 0007`](0007-random-port.md) §5.2), ist der Wert fuer ein
  gegebenes `(seed, cell, tick)` reproduzierbar — **unabhaengig von der
  Aufrufreihenfolge und von Resume**. `_cell_voltages` ist damit **derived**
  (jeder Tick neu berechnet), kein akkumulierter State.

Alle Werte werden auf `Decimal("0.000001")` (`ROUND_HALF_EVEN`, im bestehenden
`prec=28`-Battery-Context) quantisiert — kein Float-Drift.

### 2.3 Telemetrie — opt-in aggregiertes `cell_voltage_delta_v`

Ein zusaetzlicher `TelemetryPoint` (`metric="cell_voltage_delta_v"`,
`unit="V"`, SI per `GG-DATA-002`) = `max(cells) - min(cells)`, **conditional**
an den `cell`-Block gebunden (kein Block → **kein** Punkt). **Aggregiert statt
N per-Zelle-Punkte**: der Telemetrie-Strom bleibt **bounded** (ein Punkt
unabhaengig von `n_cells`), und der Demo-Hash bliebe `n_cells`-unabhaengig.
`min_cell_voltage_v`/`max_cell_voltage_v` als Debug-Kontext sind ein
moeglicher Folge-Punkt (deferred, §7). Die Emission wird vor Ausgabe
**alphabetisch nach Metrikname sortiert** ([`ADR 0014`](0014-battery-snapshot-schema.md)
§2.4) — `cell_voltage_delta_v` sortiert vor `power_kw`; ohne opt-in Metriken
bleibt die Bestands-Reihenfolge byte-identisch.

### 2.4 Snapshot — opt-in serialisiert, kein Versions-Bump

Schema bleibt `version=1`. Wie 4a:

- **Config-Block opt-in:** der `cell`-Block (mit `n_cells: int`) wird im
  `config`-Sub-Mapping nur bei aktivem Modell emittiert. Default-Pfad →
  byte-identisch (`EXPECTED_DEMO_*` + Scenario-Hash unberuehrt).
- **State opt-in:** `cell_voltages_v: tuple[Decimal, ...]` wird als geordnete
  Decimal-Liste **nur bei Non-Empty** geschrieben (leeres Tuple → kein Key →
  bit-identisch). `from_dict` liest es opt-in (Default `()`); Alt-Snapshots
  ohne Key lesen als „kein Zell-Modell" (v1-backward-compat).

### 2.5 Determinismus + Resume

- **Inaktiv bit-genau:** der Zell-Layer aktiviert sich nur bei
  `cell is not None`; ohne Block kein `RandomPort`-Zug, keine Telemetrie, kein
  State — Regressions-Pin Pflicht.
- **Determinismus:** gleicher Seed + gleiche Tick-Folge → byte-identische
  `cell_voltage_delta_v`-Spur ueber ≥ 100 Ticks (Hypothesis-Property).
- **Resume-Vertrag (Praezedenz [`ADR 0057`](0057-wind-turbine-device-pattern.md)
  §2.6):** `from_snapshot` rekonstruiert `_cell_voltages`, laesst `_random`
  aber `None`. Bei aktivem Rauschen (`noise_amplitude_v > 0`) wirft der erste
  Tick ohne vorheriges `attach_random` **fail-loud** (`DeviceNotInitialized
  Error`), statt still nicht-deterministisch zu laufen. Nach `attach_random`
  laeuft die Spur deterministisch weiter — **dank der tick-gekeyten
  Sub-Ports byte-kontinuierlich** mit einem ununterbrochenen Lauf (kein
  Fresh-Start-Bruch wie bei Wind).

---

## 3. Begruendung

**Sub-Port pro Zelle (statt Ziehung vom Haupt-Port):** macht jede Zelle zu
einem **unabhaengigen** Rausch-Stream — das Hinzufuegen/Entfernen einer Zelle
verschiebt die Stroeme anderer Zellen nicht (anders als konsekutive
Haupt-Port-Ziehungen). Zweite Stufe `tick-<t>`: per-Tick-Variation **ohne**
gecachten Sub-Port-State — und damit Resume-Kontinuitaet geschenkt.

**Aggregiertes `cell_voltage_delta_v` (statt N per-Zelle):** erfuellt das
`GG-BESS-007`-Akzeptanzkriterium (Zellabweichung sichtbar) und haelt die
Telemetrie-Flaeche + den Demo-Hash bounded und `n_cells`-unabhaengig.

**`noise=0` ohne `RandomPort`:** der einfachste Zell-Fall (Gleichstand) bleibt
RNG-frei testbar und braucht kein `attach_random` — nur das echte Rauschen
zieht den Port (analog Wind „min == max", aber hier ohne Zug, da kein
Stream-Konsistenz-Zwang besteht: tick-gekeyte Sub-Ports sind ordnungs-
unabhaengig).

**Opt-in statt Schema-Bump:** identische Begruendung wie
[`ADR 0065`](0065-battery-thermal-telemetry-pattern.md) §3 — der additive
Layer darf die Demo-Hash-Pins nicht verschieben.

---

## 4. Risiken / offene Design-Fragen

- **Sub-Seed-Stabilitaet:** die Sub-Seed-Ableitung pro Zelle/Tick muss stabil
  + kollisionsfrei sein (Trigger
  [`011`](../planning/open/011-mlrandomport-subseed-width.md), Sub-Seed-
  Breite). Ein Drift bricht den Determinismus-Pin.
- **Tuple-Roundtrip:** leeres Tuple (inaktiv/pre-Tick) muss byte-identisch zum
  heutigen Snapshot bleiben (opt-in weglassen, nicht `[]` schreiben).
- **Config-Snapshot-Compat:** der neue Zell-Default darf im inaktiven Pfad
  nicht in Snapshots/Scenario-Pins auftauchen; `from_dict` liest fehlende neue
  Keys als inaktiv.

---

## 5. Reichweite

Gilt fuer: `hexagon/core/devices/battery/config.py` (`CellConfig` + Feld),
`hexagon/core/devices/battery/model.py` (Zell-Berechnung + `RandomPort`-Konsum
+ opt-in Emission + Params-Roundtrip), `hexagon/core/devices/battery/
snapshot.py` (opt-in Config-/State-Serialisierung),
`tests/unit/hexagon/core/devices/battery/`.

Gilt NICHT fuer: Balancing-Regelung, Sicherheitsabschaltung bei Zell-Ueber-/
Unterspannung (M3), Zell-Chemie-Detailmodelle, SOC-/OCV-Kennlinien,
Temperatur ([`ADR 0065`](0065-battery-thermal-telemetry-pattern.md)),
voller stand-kontinuierlicher Multi-Geraete-RNG-Resume (§7).

---

## 6. Akzeptanzkriterien (Trigger 024)

- [ ] `CellConfig` additiv + validiert; opt-in `cell`-Feld auf
      `BatteryConfig` mit backward-compat-Default.
- [ ] `cell_voltages_v` aus Basis + (opt.) seeded per-Zelle-Rauschen; opt-in
      `cell_voltage_delta_v`-`TelemetryPoint` (`unit="V"`) **nur bei aktivem
      Block**; ≥ 100-Tick-Determinismus-Property + Resume-Fail-Loud-Pin.
- [ ] `BatterySnapshot` opt-in serialisiert (Config-`cell`-Block +
      `cell_voltages_v`-Tuple, kein Versions-Bump, v1-Lesepfad); Roundtrip
      byte-stabil inkl. Tuple-Kanonik.
- [ ] `make gates` gruen (`coverage-gate-critical` ≥ 90 % `devices/battery`);
      `accept-pin-check` gruen (`cell=None` → `EXPECTED_DEMO_*` unberuehrt);
      diese ADR `Accepted`; Trigger 024 aufgeloest.

---

## 7. Nicht Gegenstand dieser ADR

- **Balancing-Regelung** (aktiver Zellausgleich) — Telemetrie erkennt
  Abweichungen, die Ausgleichs-Logik ist eigener Trigger.
- **Sicherheitsabschaltung** bei Zell-Ueber-/Unterspannung — Constraint-/
  Fault-Logik (M3).
- **Zell-Chemie-Detailmodelle** (Li-Ion / LiFePO4 / Solid-State) + SOC-/OCV-
  Kennlinien — Domain ist Spannungsverhalten auf Pack-/Zell-Niveau, nicht
  Elektrochemie.
- **Per-Zelle-Telemetrie** (`cell_voltage_v` pro Zelle) bzw.
  `min/max_cell_voltage_v` — moegliche Debug-Erweiterung; aggregiertes
  `cell_voltage_delta_v` genuegt fuer `GG-BESS-007`.
- **Voller stand-kontinuierlicher Multi-Geraete-RNG-Resume** — der Snapshot
  des `RandomPort` selbst ist TickLoop-/Adapter-Material
  ([`ADR 0057`](0057-wind-turbine-device-pattern.md) §2.6).
- **Temperatur-Telemetrie** — [`ADR 0065`](0065-battery-thermal-telemetry-pattern.md)
  (`GG-BESS-006`), unabhaengig aktivierbar.
