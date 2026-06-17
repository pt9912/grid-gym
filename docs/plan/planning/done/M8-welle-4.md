# Welle 4 — M8 BESS-Telemetrie (`GG-BESS-006/007`)

**Status:** **Done (2026-06-17)** — beide Sub-Wellen geliefert:
**4a (Temperatur, `GG-BESS-006`)** via
[`ADR 0065`](../../adr/0065-battery-thermal-telemetry-pattern.md) und
**4b (Zellspannung, `GG-BESS-007`)** via
[`ADR 0066`](../../adr/0066-battery-cell-voltage-telemetry-pattern.md) — beide
`Accepted`, additive Telemetrie-Schaerfungen des Battery-Modells
(`BatteryDevice`, [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md)) aus
Lastenheft §10.6. Reine Geraete-Submodul-Erweiterung in `devices/battery/` —
**kein neues Geraet, kein neuer Port/Adapter-Typ, keine Bilanz-Aenderung**.
Trigger 023/024 aufgeloest; `make gates` + `docs-check` + `accept-pin-check`
gruen. Mit dieser Closure wandert die Welle-4-Gruppe (Container + 4a + 4b)
nach `done/` (wie Welle 2/3).

**Container:** Meilenstein-Scope in [`roadmap.md`](../in-progress/roadmap.md) §4 M8;
Welle-Triage in [`M8-welle-0.md`](M8-welle-0.md) §1.1 (Welle 4 =
`T-023/024`). Voraussetzung (Welle 3, Netz) abgeschlossen
([`M8-welle-3.md`](M8-welle-3.md)). Aufbau auf
[`ADR 0014`](../../adr/0014-battery-snapshot-schema.md) (Battery-Snapshot-
Schema) als **Schaerfung ohne Abloesung** — wie
[`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md) etabliert; das
Battery-Sub-Snapshot ist per
[`ADR 0015`](../../adr/0015-snapshot-envelope-v2.md) §2.3 frei additiv
erweiterbar (Envelope bleibt unveraendert).

---

## 1. Zweck + Architektur-Familie

Beide Sub-Wellen erweitern dasselbe Battery-Submodul
(`src/grid_gym/hexagon/core/devices/battery/`: `config.py`, `model.py`,
`snapshot.py`). Heutiger Stand
([`ADR 0014`](../../adr/0014-battery-snapshot-schema.md)): der
`BatterySnapshot` (`version=1`) traegt SOC, Strom/Leistung und Ramp;
[`ADR 0025`](../../adr/0025-fault-recovery-pattern.md) hat den
`fault_state`-Block additiv ohne Versions-Bump ergaenzt. Welle 4 setzt die
additive No-Bump-Disziplin fort, waehlt fuer neue Default-aus-Telemetrie aber
einen strengeren **opt-in serialisiert**-Vertrag: inaktive Temperatur-/
Zellspannungsfelder werden gar nicht geschrieben.

| Sub-Welle | ID | Trigger | Wesen | Charakteristik |
|---|---|---|---|---|
| 4a Temperatur | `GG-BESS-006` | [`023`](../open/023-sollte-battery-temperature.md) | Stateful-Telemetry | `temperature_celsius` aus normalisiertem Lastfaktor (`load_pu²`) + Umgebung + Zeitkonstante; opt-in Thermo-Config; analog dem Top-Oil-Thermomodell aus [`ADR 0061`](../../adr/0061-transformer-limit-bilanz-pattern.md) |
| 4b Zellspannung | `GG-BESS-007` | [`024`](../open/024-sollte-battery-cell-voltage.md) | Schema (tuple) + `RandomPort` | `nominal_pack_voltage_v` + `n_cells` + `cell_voltages_v: tuple[Decimal, ...]`; opt-in per-Zelle Rauschen via `RandomPort.sub_port("cell-<idx>")`; normative aggregierte `cell_voltage_delta_v`-Telemetrie, optional ergaenzt um `min/max_cell_voltage_v` |

**Architektur-Erbschaft:** kein neuer Driving-/Driven-Port und **keine
Bilanz-Beruehrung** — Temperatur/Zellspannung sind Geraete-interne Groessen,
die als `TelemetryPoint` emittiert werden (Metric ist generisch, SI-Einheit
per `GG-DATA-002`), nicht in `GridModelBilanz` aggregiert. Pro Sub-Welle eine
ADR-Folge als **Erweiterung** von
[`ADR 0014`](../../adr/0014-battery-snapshot-schema.md) (Schaerfung-Pattern,
kein Supersede). `devices/battery/` liegt bereits in `CRITICAL_COV_TARGETS`
(`Dockerfile`) → **kein neuer Coverage-Target-Eintrag** (wie Welle 3).

## 2. Erfolgskriterien (DoD je Sub-Welle)

- ADR-Folge (Status `Accepted`) als Schaerfung von
  [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md) (kein Supersede),
  mit modell-/telemetrie-spezifischen Akzeptanzkriterien.
- `BatteryConfig`-Erweiterung: neue Felder **additiv + opt-in** mit
  backward-compat-Default (Bestands-Szenarien unveraendert ladbar;
  Default-Pfad = heutiges Verhalten bit-genau). Snapshot-`config`-Mapping bleibt
  ebenfalls default-neutral: neue Config-Keys werden bei inaktivem Feature nicht
  geschrieben, und `from_dict` akzeptiert fehlende neue Keys als inaktive
  Defaults.
- `BatterySnapshot` additiv erweitert: **opt-in serialisiert** (Feld nur bei
  aktivem Feature im Mapping → roundtrip byte-identisch, **kein Versions-Bump**;
  strenger als der immer emittierte `fault_state`-Block aus
  [`ADR 0025`](../../adr/0025-fault-recovery-pattern.md)); v1-Lesepfad fuer
  Altschnappschuesse.
- Neue Telemetry-Metric(s) **nur bei aktiver Config** (kein Feature →
  **kein** Punkt, nicht `0`); Determinismus-Property-Test (gleicher Seed →
  identische Trace, `AC-NO-RAND`). RandomPort-konsumierende Features brauchen
  zusaetzlich Resume-Pins (`from_snapshot` + `attach_random`; fehlender
  `attach_random` fail-loud typisiert).
- `make gates` gruen (A-1-Gates), `coverage-gate-critical` ≥ 90 % auf
  `devices/battery` (ohne neuen Target); bei Snapshot-Aenderung Roundtrip-Pin
  **inkl. v1-backward-compat-Lesepfad**.
- **`EXPECTED_DEMO_*`-Hash-Pins unberuehrt**: die Battery im Abnahme-Szenario
  [`deploy/scenarios/gg-demo.yaml`](../../../../deploy/scenarios/gg-demo.yaml)
  aktiviert die neuen Felder **nicht** → keine neue Telemetrie; die
  Scenario-Hash-Default-Strip-Regel fuer neue Battery-Defaults ist Teil der
  C1-Umsetzung → byte-stabil (`accept-pin-check` gruen).

## 3. Tranchierung (Sub-Slicing)

Zwei **unabhaengig aktivierbare** Trigger (023/024 nennen sich gegenseitig
explizit „unabhaengig aktivierbar") mit **distinkten** Schema-/Telemetrie-
Flaechen (skalares `temperature_celsius` vs. `cell_voltages_v`-Tuple) und
einer **neuen Determinismus-Flaeche in 4b** (erster Battery-`RandomPort`-
Konsument, per-Zelle Rauschen). Auch wenn das die Sub-Slicing-Schwelle
([`M8-welle-0.md`](M8-welle-0.md) §2.4: > 2 unabhaengige Sub-Bereiche)
nur **streift** (genau zwei), wird je Trigger getrancht — fuer saubere
Einzel-Trigger-Closure und um die zwei unabhaengigen additiven Schema-
Schritte nicht in einem Commit zu vermischen. Reihenfolge **4a → 4b**
(skalare Telemetrie zuerst, das Tuple-/Rausch-Feld mit eigener
Telemetrie-Aggregations-Frage zuletzt). Jede Sub-Welle aktiviert ihren
`open/`-Trigger und loest ihn bei Closure auf.

- **Welle 4-C0 — Eroeffnung** (dieser Plan): Bestaetigung gegen
  [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md), Reihenfolge,
  opt-in/Pin-neutral-Strategie. Sensor: `make docs-check`.
- **Welle 4a — Battery-Temperatur** ([`M8-welle-4a.md`](M8-welle-4a.md),
  `GG-BESS-006`, [`023`](../open/023-sollte-battery-temperature.md), NEU ADR):
  `temperature_celsius` als Geraete-State + Telemetrie. T-Modell als
  **stateful Single-Zonen-Thermomodell** (analog dem Top-Oil-Euler aus
  [`ADR 0061`](../../adr/0061-transformer-limit-bilanz-pattern.md):
  `theta += (theta_ss − theta)·(dt/τ)`, `theta_ss = T_ambient + rise·load_pu²`)
  — stateful ist fuer 4a fixiert; C1 entscheidet nur Parameter-Namen,
  Initialwert und Rundung. Opt-in Thermo-Config
  (`thermal_rise_c_at_full_load`/`T_ambient`/`τ` o. Ae.); Snapshot und
  eingebettete Config additiv opt-in (kein Bump, fehlende neue Config-Keys =
  inaktiv). Derating/thermische Constraints **out-of-scope** (§5, M3-Material).
- **Welle 4b — Battery-Zellspannung** ([`M8-welle-4b.md`](M8-welle-4b.md),
  `GG-BESS-007`, [`024`](../open/024-sollte-battery-cell-voltage.md), NEU ADR):
  `nominal_pack_voltage_v: Decimal` + `n_cells: int` +
  `cell_voltages_v: tuple[Decimal, ...]`. Vereinfacht alle Zellen identisch
  (`nominal_pack_voltage_v / n_cells`); erweitert per-Zelle mit seeded
  `RandomPort.sub_port("cell-<idx>")`-Rauschen (deterministisch).
  Telemetrie **aggregiert**: `cell_voltage_delta_v` als normativer
  `GG-BESS-007`-Akzeptanzpunkt (`max-min`), optional `min_cell_voltage_v` +
  `max_cell_voltage_v` als Debug-/Boundary-Kontext statt N Punkte — bounded
  Telemetrie-Flaeche; per-Zelle als Alternative (Design-Item). Snapshot
  additiv opt-in.

**Schwellen-Hinweis:** sollte eine Sub-Welle selbst > 300 Zeilen / > 5
Commits werden (4b ist Kandidat wegen Tuple-Feld + Rausch-Quelle + Telemetrie-
Aggregation), wird sie nach demselben Schema weiter getrancht.

## 4. Risiken

- **Pin-Neutralitaet (beide):** [`deploy/scenarios/gg-demo.yaml`](../../../../deploy/scenarios/gg-demo.yaml)
  enthaelt eine Battery — jede **immer-aktive** Telemetrie/State-Erweiterung
  wuerde `EXPECTED_DEMO_TELEMETRY_STREAM_HASH` brechen. Zwingend **opt-in im
  Szenario** (Feld nur bei gesetzter Config), Snapshot **opt-in serialisiert**,
  Scenario-Hash strippt neue Battery-Default-Felder — exakt die Welle-3-
  Disziplin.
- **Spannungsquelle (4b):** `BatteryConfig` enthaelt heute keinen Pack-
  Spannungswert. 4b muss deshalb `nominal_pack_voltage_v` als expliziten
  opt-in Parameter einfuehren und validieren; SOC-/OCV-Kennlinien bleiben
  ausserhalb dieses Telemetrie-Slices.
- **Determinismus (4b):** per-Zelle Rauschen ueber `RandomPort.sub_port`
  braucht stabile Sub-Seed-Ableitung (vgl. Trigger
  [`011`](../open/011-mlrandomport-subseed-width.md), Sub-Seed-Breite) +
  `Decimal`-Rundungs-Disziplin — kein Float-Drift im Snapshot/Telemetrie.
- **Stateful T (4a):** ein zustandsbehaftetes Thermomodell fuehrt akkumulierten
  State (`temperature_celsius`) → muss in den Snapshot, und der Roundtrip muss
  byte-stabil bleiben (gleiche τ-Euler-Integration wie 3b).
- **Config-Opt-in (beide):** `BatterySnapshot.to_dict()` bettet heute alle
  `BatteryConfig`-Felder ein. Neue Default-Config-Keys duerfen deshalb im
  inaktiven Pfad nicht unbemerkt in Snapshots/Scenario-Pins auftauchen;
  `from_dict` muss Alt-Snapshots ohne diese Keys als inaktiv lesen.
- **Coverage:** `devices/battery` ist bereits coverage-critical; neue Branches
  (opt-in-Pfade) duerfen die ≥ 90 %-Schwelle nicht druecken — die
  Default-aus-Pfade brauchen ebenfalls Tests.

## 5. Nicht-Ziele

- **Thermisches Derating / Sicherheits-Abschaltung** bei Ueber-/
  Untertemperatur oder Zell-Ueberspannung — Constraint-/Fault-Logik ist
  M3-Material, nicht diese Telemetrie-Welle (Trigger 023/024
  Aktivierungs-Kriterium nennt den M3-Fault-Slice separat).
- **Aktive Kuehlung-/Heizung-Logik** — HVAC-Aggregat-Modellierung, nicht
  Battery-Verhalten (Trigger 023 Out-of-scope).
- **Zell-Chemie-Detailmodelle** (Li-Ion / LiFePO4 / Solid-State) +
  **Zellebene-Thermodynamik** — Domain ist Spannungs-/Temperatur-Verhalten
  auf Pack-Niveau, nicht Elektrochemie (Trigger 023/024 Out-of-scope).
- **Balancing-Regelung** (aktiver Zellausgleich) — Telemetrie erkennt
  Abweichungen, die Ausgleichs-Logik ist eigener Trigger.
- **Alterungs-/Kalender-Zyklen-Modelle** — T-abhaengig, aber eigener Slice.

## 6. DoD (Welle 4-C0)

- [x] `M8-welle-4.md` angelegt (dieser Plan) + Slice-Plaene
      [`M8-welle-4a.md`](M8-welle-4a.md)/[`M8-welle-4b.md`](M8-welle-4b.md).
- [x] Scope fixiert: beide (`T-023/024`/`GG-BESS-006/007`) in Welle 4,
      Telemetrie-Schaerfung von
      [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md).
- [x] Reihenfolge fixiert: **4a Temperatur → 4b Zellspannung** (skalare
      Telemetrie vor Tuple-/Rausch-Feld).
- [x] Pin-/Schema-Strategie fixiert: beide additiv + **opt-in** ohne
      Versions-Bump (strengere Opt-in-Serialisierung als `fault_state`);
      [`deploy/scenarios/gg-demo.yaml`](../../../../deploy/scenarios/gg-demo.yaml)
      aktiviert nichts → `EXPECTED_DEMO_*` unberuehrt. Konkrete Feld-/
      Telemetrie-Liste ist Slice-Design-Item (4a/4b §3).
- [x] `make docs-check` gruen.
