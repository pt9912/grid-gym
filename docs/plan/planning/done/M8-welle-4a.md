# Welle 4a — Battery-Temperatur-Telemetrie (`GG-BESS-006`)

**Status:** **Done (2026-06-17)** — erste Sub-Welle der BESS-Telemetrie-Welle,
additive Schaerfung des Battery-Modells. Geliefert via
[`ADR 0065`](../../adr/0065-battery-thermal-telemetry-pattern.md) `Accepted`
(Schaerfung zu [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md), kein
Supersede). Trigger [`023`](../open/023-sollte-battery-temperature.md)
aufgeloest. `make gates` + `docs-check` + `accept-pin-check` gruen
(`coverage-gate-critical` 96 % auf `devices/battery`). Doc-Verschiebung nach
`done/` erfolgt als Gruppe mit der Welle-4-Gesamt-Closure (siehe
[`M8-welle-4.md`](M8-welle-4.md) §1).

**Container:** [`M8-welle-4.md`](M8-welle-4.md) §3 (Welle-4-C0-Plan,
Reihenfolge 4a → 4b); [`roadmap.md`](../in-progress/roadmap.md) §4 M8. Trigger:
[`023`](../open/023-sollte-battery-temperature.md) ([`GG-BESS-006`](../../../../spec/lastenheft.md#gg-bess-006), Lastenheft
§10.6; mit dieser Welle aufzuloesen).

---

## 1. Lieferziel

Eine **Temperatur-Telemetrie** als opt-in Erweiterung des `BatteryDevice`
(`src/grid_gym/hexagon/core/devices/battery/`): das Pack fuehrt eine
`temperature_celsius`-Groesse, getrieben aus normalisiertem Lastfaktor
(`load_pu²`) + Umgebungstemperatur + Temperaturanstieg bei Volllast, und
emittiert sie als `TelemetryPoint`. Heute deckt der Battery-Snapshot
([`ADR 0014`](../../adr/0014-battery-snapshot-schema.md)) nur SOC, Strom/
Leistung, Ramp und den additiven `fault_state`-Block ab — Temperatur fehlt.
**Ohne aktive Thermo-Config bleibt das Verhalten bit-genau wie heute** (kein
Feld, kein Punkt).

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [x] **Config + Thermo-Modell**: opt-in `ThermalConfig` (nested) additiv in
      `BatteryConfig` (`config.py`: `ambient_temp_c` /
      `thermal_rise_c_at_full_load` / `thermal_time_constant_s`), Default =
      inaktiv; fehlende neue Config-Keys in alten Snapshots/Szenarien lesen
      als inaktive Defaults. `BatteryDevice` rechnet `temperature_celsius`
      als **stateful Single-Zonen-Euler** (`theta += (theta_ss - theta)·(dt/tau)`,
      `theta_ss = ambient + rise_at_full_load·load_pu²`, analog
      [`ADR 0061`](../../adr/0061-transformer-limit-bilanz-pattern.md));
      ≥ 100-Tick-Determinismus-Property + Aufheiz-/Abkuehl-/Steady-State-Pins.
      C1: Parameter-Namen fixiert, **Kaltstart auf `ambient_temp_c`** (kein
      `initial_temp_c`), Rundung `Decimal("0.000001")` ROUND_HALF_EVEN.
- [x] **Telemetrie + Snapshot opt-in**: `temperature_celsius`-`TelemetryPoint`
      (`unit="degC"`, SI per [`GG-DATA-002`](../../../../spec/lastenheft.md#gg-data-002)) **nur bei aktiver Config**
      (inaktiv → kein Punkt, alphabetisch hinter `soc_pct`); `BatterySnapshot`
      traegt den T-State **additiv opt-in serialisiert** (kein Versions-Bump,
      v1-Lesepfad fuer Altschnappschuesse, strenger als der immer emittierte
      `fault_state`-Block aus
      [`ADR 0025`](../../adr/0025-fault-recovery-pattern.md)); neue Thermo-
      Config-Keys werden bei inaktivem Feature nicht ins Snapshot-`config`-
      Mapping geschrieben; Roundtrip byte-stabil.
- [x] **Gates + Pin-neutral**: lint/format/typecheck/arch/test-unit/
      `coverage-gate-critical` 96 % auf `devices/battery` (kein neuer
      Target) + `docs-check` + **`accept-pin-check` gruen**
      ([`deploy/scenarios/gg-demo.yaml`](../../../../deploy/scenarios/gg-demo.yaml)
      ohne Thermo-Config → `EXPECTED_DEMO_*` unberuehrt);
      [`ADR 0065`](../../adr/0065-battery-thermal-telemetry-pattern.md)
      `Accepted`; Trigger 023 aufgeloest.

## 3. Design-Skizze (C1)

- **Config** (`battery/config.py`): additive opt-in Felder fuer normalisiertes
  Thermomodell (`thermal_rise_c_at_full_load`, `ambient_temp_c`,
  `thermal_time_constant_s`, ggf. `initial_temp_c`); `__post_init__` validiert
  Positivitaet/Konsistenz im Bestands-Pattern
  (`BatteryConfigInvalidValueError`). Default-Defense: fehlen die Felder, ist
  das Thermo-Modell inaktiv.
- **Modell** (`battery/model.py`): `theta_oil`-Aequivalent als akkumulierter
  Geraete-State; pro Tick Euler-Schritt mit kanonischer `Decimal`-Rundung
  (`prec=28`, `ROUND_HALF_EVEN`, quantize `0.000001`) — kein Float-Drift.
  `load_pu = abs(power_kw) / max(max_charge_kw, max_discharge_kw)` speist
  `theta_ss = ambient + rise_at_full_load * load_pu²`; τ ist die thermische
  Traegheit.
- **Telemetrie**: ein zusaetzlicher `TelemetryPoint` (`temperature_celsius`)
  zwischen den Bestands-Metriken, **conditional** an die Config gebunden
  (Emission-Liste-Pattern wie die opt-in Q-Telemetrie der GridConnection in
  [`ADR 0064`](../../adr/0064-grid-connection-q-transformer-apparent-power.md)).
- **Snapshot** (`battery/snapshot.py`): additives Feld
  (`temperature_celsius: Decimal = Decimal(0)`), `to_dict` schreibt den Key
  **opt-in** (nur bei aktivem Thermo-State), `from_dict` liest opt-in mit
  Default — Bestands-Snapshots roundtrip-faehig **ohne** Versions-Bump.
  Das eingebettete `config`-Mapping bleibt ebenfalls opt-in: inaktive
  Thermo-Defaults werden nicht geschrieben, fehlende neue Config-Keys lesen als
  inaktiv.

## 4. Risiken / offene Design-Fragen

- **Stateful-Thermo-Pfad**: τ-Euler spiegelt die etablierte 3b-Mechanik und
  macht Temperatur zu persistentem Geraete-State; Snapshot-State und
  Roundtrip-Pins muessen deshalb Teil von C1/C2 bleiben.
- **Init-Temperatur**: kalter Start auf `ambient` vs. dedizierter
  `initial_temp_c` — Default-Festlegung im ADR.
- **Config-Snapshot-Compat**: `BatterySnapshot` serialisiert heute alle
  `BatteryConfig`-Felder. 4a muss den neuen Thermo-Default deshalb explizit aus
  dem inaktiven Snapshot-`config`-Mapping heraushalten und Alt-Snapshots ohne
  diese Keys akzeptieren.
- **Default-Stabilitaet**: ohne Thermo-Config muss der Tick bit-identisch zum
  heutigen Battery-Pfad bleiben (Regressions-Pin; kein Telemetrie-Punkt).

## 5. Nicht-Ziele (dieser Slice)

- Thermisches **Derating** / Sicherheits-Abschaltung bei Uebertemperatur —
  Constraint-/Fault-Logik (M3), nicht diese Telemetrie-Welle.
- Aktive Kuehlung/Heizung — HVAC-Slice (Trigger 023 Out-of-scope).
- Zellebene-Thermodynamik — Pack-Niveau bleibt; Zellauffloesung ist
  [`M8-welle-4b.md`](M8-welle-4b.md) (Spannung) bzw. eigener Slice.
- Alterungs-/Lebensdauer-Modelle (T-abhaengig) — eigener Trigger.
