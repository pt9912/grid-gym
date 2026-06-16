# Welle 4a — Battery-Temperatur-Telemetrie (`GG-BESS-006`)

**Status:** Geplant (M8-Welle-4a) — erste Sub-Welle der BESS-Telemetrie-Welle,
additive Schaerfung des Battery-Modells. Liefert via NEU ADR (Nummer bei
Slice-Eroeffnung, Schaerfung zu
[`ADR 0014`](../../adr/0014-battery-snapshot-schema.md), kein Supersede).
Trigger [`023`](../open/023-sollte-battery-temperature.md) wird mit dieser
Sub-Welle aufgeloest.

**Container:** [`M8-welle-4.md`](M8-welle-4.md) §3 (Welle-4-C0-Plan,
Reihenfolge 4a → 4b); [`roadmap.md`](roadmap.md) §4 M8. Trigger:
[`023`](../open/023-sollte-battery-temperature.md) (`GG-BESS-006`, Lastenheft
§10.6; mit dieser Welle aufzuloesen).

---

## 1. Lieferziel

Eine **Temperatur-Telemetrie** als opt-in Erweiterung des `BatteryDevice`
(`src/grid_gym/hexagon/core/devices/battery/`): das Pack fuehrt eine
`temperature_celsius`-Groesse, getrieben aus der Verlustleistung
(`power_kw² · R_internal`) + Umgebungstemperatur, und emittiert sie als
`TelemetryPoint`. Heute deckt der Battery-Snapshot
([`ADR 0014`](../../adr/0014-battery-snapshot-schema.md)) nur SOC, Strom/
Leistung, Ramp und das Fault-Flag ab — Temperatur fehlt. **Ohne aktive
Thermo-Config bleibt das Verhalten bit-genau wie heute** (kein Feld, kein
Punkt).

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [ ] **Config + Thermo-Modell**: opt-in Thermo-Parameter additiv in
      `BatteryConfig` (`config.py`, z. B. `internal_resistance_ohm` /
      `ambient_temp_c` / `thermal_time_constant_s`), Default = inaktiv;
      `BatteryDevice` rechnet `temperature_celsius` als **stateful Single-
      Zonen-Euler** (`theta += (theta_ss − theta)·(dt/τ)`,
      `theta_ss = ambient + rise·load_pu²`, analog
      [`ADR 0061`](../../adr/0061-transformer-limit-bilanz-pattern.md));
      ≥ 100-Tick-Determinismus-Property (gleicher Seed/Input → identische
      T-Trace). Modell-Tiefe (zustandsfrei vs. stateful) ist C1-Entscheid.
- [ ] **Telemetrie + Snapshot opt-in**: `temperature_celsius`-`TelemetryPoint`
      (SI per `GG-DATA-002`) **nur bei aktiver Config** (inaktiv → kein
      Punkt); `BatterySnapshot` traegt den T-State **additiv opt-in
      serialisiert** (kein Versions-Bump, v1-Lesepfad fuer Altschnappschuesse,
      wie `cell_failure_active`); Roundtrip byte-stabil.
- [ ] **Gates + Pin-neutral**: lint/format/typecheck/arch/test-unit/
      `coverage-gate-critical` ≥ 90 % auf `devices/battery` (kein neuer
      Target) + `docs-check` + **`accept-pin-check` gruen** (mvp_demo-Battery
      ohne Thermo-Config → `EXPECTED_DEMO_*` unberuehrt); NEU ADR `Accepted`;
      Trigger 023 aufgeloest.

## 3. Design-Skizze (C1)

- **Config** (`battery/config.py`): additive opt-in Felder; `__post_init__`
  validiert Positivitaet/Konsistenz im Bestands-Pattern
  (`BatteryConfigInvalidValueError`). Default-Defense: fehlen die Felder, ist
  das Thermo-Modell inaktiv.
- **Modell** (`battery/model.py`): `theta_oil`-Aequivalent als akkumulierter
  Geraete-State; pro Tick Euler-Schritt mit kanonischer `Decimal`-Rundung
  (`prec=28`, `ROUND_HALF_EVEN`, quantize `0.000001`) — kein Float-Drift.
  Die Verlustleistung speist `theta_ss`; τ ist die thermische Traegheit.
- **Telemetrie**: ein zusaetzlicher `TelemetryPoint` (`temperature_celsius`)
  zwischen den Bestands-Metriken, **conditional** an die Config gebunden
  (Emission-Liste-Pattern wie die opt-in Q-Telemetrie der GridConnection in
  [`ADR 0064`](../../adr/0064-grid-connection-q-transformer-apparent-power.md)).
- **Snapshot** (`battery/snapshot.py`): additives Feld
  (`temperature_celsius: Decimal = Decimal(0)`), `to_dict` schreibt den Key
  **opt-in** (nur bei aktivem Thermo-State), `from_dict` liest opt-in mit
  Default — Bestands-Snapshots roundtrip-faehig **ohne** Versions-Bump.

## 4. Risiken / offene Design-Fragen

- **Modell-Tiefe**: zustandsfrei (`T = ambient + power²·R`, sofort) vs.
  stateful (τ-Euler, traege). Stateful spiegelt die etablierte 3b-Mechanik
  und ist physikalisch ehrlicher, kostet aber Snapshot-State — C1-Entscheid.
- **Init-Temperatur**: kalter Start auf `ambient` vs. dedizierter
  `initial_temp_c` — Default-Festlegung im ADR.
- **Default-Stabilitaet**: ohne Thermo-Config muss der Tick bit-identisch zum
  heutigen Battery-Pfad bleiben (Regressions-Pin; kein Telemetrie-Punkt).

## 5. Nicht-Ziele (dieser Slice)

- Thermisches **Derating** / Sicherheits-Abschaltung bei Uebertemperatur —
  Constraint-/Fault-Logik (M3), nicht diese Telemetrie-Welle.
- Aktive Kuehlung/Heizung — HVAC-Slice (Trigger 023 Out-of-scope).
- Zellebene-Thermodynamik — Pack-Niveau bleibt; Zellauffloesung ist
  [`M8-welle-4b.md`](M8-welle-4b.md) (Spannung) bzw. eigener Slice.
- Alterungs-/Lebensdauer-Modelle (T-abhaengig) — eigener Trigger.
