# Welle 4b — Battery-Zellspannung-Telemetrie (`GG-BESS-007`)

**Status:** **Done (2026-06-17)** — zweite Sub-Welle der BESS-Telemetrie-Welle,
additive Schaerfung des Battery-Modells mit erstem Battery-`RandomPort`-
Konsument. Geliefert via
[`ADR 0066`](../../adr/0066-battery-cell-voltage-telemetry-pattern.md)
`Accepted` (Schaerfung zu
[`ADR 0014`](../../adr/0014-battery-snapshot-schema.md), kein Supersede).
Trigger [`024`](../open/024-sollte-battery-cell-voltage.md) aufgeloest.
`make gates` + `docs-check` + `accept-pin-check` gruen
(`coverage-gate-critical` 96 % auf `devices/battery`). Doc-Verschiebung nach
`done/` erfolgt als Gruppe mit der Welle-4-Gesamt-Closure (siehe
[`M8-welle-4.md`](M8-welle-4.md) §1).

**Container:** [`M8-welle-4.md`](M8-welle-4.md) §3 (Welle-4-C0-Plan,
Reihenfolge 4a → 4b — bewusst zuletzt: Tuple-Feld + Rausch-Quelle);
[`roadmap.md`](../in-progress/roadmap.md) §4 M8. Trigger:
[`024`](../open/024-sollte-battery-cell-voltage.md) (`GG-BESS-007`, Lastenheft
§10.6; mit dieser Welle aufzuloesen).

---

## 1. Lieferziel

Eine **Zellspannungs-Telemetrie** als opt-in Erweiterung des `BatteryDevice`:
das Pack wird in `n_cells` Zellen aufgeloest, jede mit eigener Spannung
(`nominal_pack_voltage_v / n_cells`, optional ueberlagert mit seeded
Rauschen). Heute deckt der Battery-Snapshot
([`ADR 0014`](../../adr/0014-battery-snapshot-schema.md)) nur Pack-Niveau (SOC)
ab. Emittiert wird **aggregiert** `cell_voltage_delta_v` (`max-min`) als
normativer `GG-BESS-007`-Akzeptanzpunkt; `min_cell_voltage_v` /
`max_cell_voltage_v` koennen als Debug-/Boundary-Kontext hinzukommen (bounded
Telemetrie statt N Metriken). **Ohne
aktive Zell-Config bleibt das Verhalten bit-genau wie heute** (kein Feld,
kein Punkt).

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [x] **Config + Zell-Modell**: opt-in `CellConfig` (nested) additiv in
      `BatteryConfig` (`nominal_pack_voltage_v: Decimal` + `n_cells: int` +
      `noise_amplitude_v: Decimal = 0`), Default = inaktiv; fehlende neue
      Config-Keys lesen als inaktive Defaults. `BatteryDevice` berechnet
      `cell_voltages_v` — bei `noise=0` alle Zellen identisch
      (`nominal_pack_voltage_v / n_cells`, kein `RandomPort`-Zug), bei
      `noise>0` per-Zelle + per-Tick seeded Rauschen via
      `random.sub_port("cell-<idx>").sub_port("tick-<t>")` (**tick-gekeyt →
      resume-kontinuierlich**); ≥ 100-Tick-Determinismus-Property;
      Resume-Pins: aktives Rauschen + `from_snapshot` ohne `attach_random`
      wirft fail-loud, mit `attach_random` byte-kontinuierlich.
- [x] **Telemetrie + Snapshot opt-in**: aggregierte
      `cell_voltage_delta_v`-`TelemetryPoint` (`unit="V"`, `max-min`)
      **nur bei aktiver Config** (alphabetisch zuerst); `min/max_cell_voltage_v`
      als Debug-Kontext deferred. `BatterySnapshot` traegt `cell_voltages_v:
      tuple[Decimal, ...]` **additiv opt-in serialisiert** (nur Non-Empty, kein
      Versions-Bump, v1-Lesepfad); inaktive Zell-Defaults nicht im
      Snapshot-`config`-Mapping; Roundtrip byte-stabil inkl. Tuple-Kanonik.
- [x] **Gates + Pin-neutral**: lint/format/typecheck/arch/test-unit/
      `coverage-gate-critical` 96 % auf `devices/battery` (kein neuer
      Target) + `docs-check` + **`accept-pin-check` gruen**
      ([`deploy/scenarios/gg-demo.yaml`](../../../../deploy/scenarios/gg-demo.yaml)
      ohne Zell-Config → `EXPECTED_DEMO_*` unberuehrt);
      [`ADR 0066`](../../adr/0066-battery-cell-voltage-telemetry-pattern.md)
      `Accepted`; Trigger 024 aufgeloest.

## 3. Design-Skizze (C1)

- **Config** (`battery/config.py`): `nominal_pack_voltage_v: Decimal` +
  `n_cells: int` opt-in (Default `None`/`0` = inaktiv) + optionale Rausch-
  Amplitude; `__post_init__` validiert `nominal_pack_voltage_v > 0` und
  `n_cells ≥ 1` wenn gesetzt (Bestands-Error-Pattern). Snapshot-`config`
  schreibt inaktive Zell-Defaults nicht und liest fehlende neue Keys als
  inaktiv.
- **Modell** (`battery/model.py`): erster Battery-`RandomPort`-Konsument fuer
  Rauschen — `RandomPort.sub_port("cell-<idx>")` pro Zelle, deterministische
  Sub-Seed-Ableitung (vgl. Trigger
  [`011`](../open/011-mlrandomport-subseed-width.md)). Ohne Rausch-Amplitude
  sind alle Zellen identisch (`nominal_pack_voltage_v / n_cells`), rein
  deterministisch ohne `RandomPort`-Zug. Mit Rausch-Amplitude ist
  `attach_random` nach `from_snapshot` Pflicht; fehlt er, wirft der Tick
  typisiert statt nicht-deterministisch still weiterzulaufen. Kanonische
  `Decimal`-Rundung, kein Float-Drift.
- **Telemetrie**: **aggregiert** mit `cell_voltage_delta_v = max-min` statt N
  per-Zelle-Punkte — erfuellt das `GG-BESS-007`-Akzeptanzkriterium und haelt
  die Telemetrie-Flaeche bounded. `min_cell_voltage_v`/`max_cell_voltage_v`
  koennen als Debug-/Boundary-Kontext ergaenzen; per-Zelle-Emission ist die
  Alternative (Design-Item; Trigger 024 laesst beide offen).
- **Snapshot** (`battery/snapshot.py`): additives Tuple-Feld
  (`cell_voltages_v: tuple[Decimal, ...] = ()`), `to_dict` schreibt den Key
  **opt-in** (nur bei `n_cells`), `from_dict` liest opt-in mit Default —
  Bestands-Snapshots roundtrip-faehig **ohne** Versions-Bump; Tuple kanonisch
  serialisiert (geordnete Liste von `Decimal`-Strings). Das eingebettete
  `config`-Mapping bleibt ebenfalls opt-in: inaktive Zell-Defaults werden nicht
  geschrieben, fehlende neue Config-Keys lesen als inaktiv.

## 4. Risiken / offene Design-Fragen

- **Determinismus der Rausch-Quelle**: die Sub-Seed-Ableitung pro Zelle muss
  stabil + kollisionsfrei sein (Trigger
  [`011`](../open/011-mlrandomport-subseed-width.md), Sub-Seed-Breite) — ein
  Drift bricht den Determinismus-Pin. Resume braucht eigene Pins:
  `from_snapshot` rekonstruiert Battery-State ohne RandomPort; aktive
  Rausch-Config darf erst nach `attach_random` weiterlaufen.
- **Spannungsquelle**: heutige Battery-Config hat keinen Pack-
  Spannungsparameter. C1/ADR muessen `nominal_pack_voltage_v` als explizite
  opt-in Quelle fixieren; SOC-/OCV-Kennlinien oder Zell-Chemie bleiben
  Nicht-Ziel.
- **Telemetrie-Aggregation**: `cell_voltage_delta_v` ist normativ; C1
  entscheidet nur, ob `min_cell_voltage_v`/`max_cell_voltage_v` zusaetzlich als
  Debug-/Boundary-Kontext emittiert werden. Per-Zelle blaeht den Stream und
  macht den Hash `n_cells`-abhaengig.
- **Tuple-Roundtrip**: leeres Tuple (inaktiv) muss byte-identisch zum
  heutigen Snapshot bleiben (opt-in weglassen, nicht `[]` schreiben).
- **Config-Snapshot-Compat**: `BatterySnapshot` serialisiert heute alle
  `BatteryConfig`-Felder. 4b muss den neuen Zell-Default deshalb explizit aus
  dem inaktiven Snapshot-`config`-Mapping heraushalten und Alt-Snapshots ohne
  diese Keys akzeptieren.
- **Default-Stabilitaet**: ohne Zell-Config bit-identisch zum heutigen
  Battery-Pfad (Regressions-Pin; kein Telemetrie-Punkt).

## 5. Nicht-Ziele (dieser Slice)

- **Balancing-Regelung** (aktiver Zellausgleich) — Telemetrie erkennt
  Abweichungen, die Ausgleichs-Logik ist eigener Trigger.
- **Sicherheitsabschaltung** bei Zell-Ueber-/Unterspannung — Constraint-/
  Fault-Logik (M3), nicht diese Telemetrie-Welle.
- **Zell-Chemie-Detailmodelle** (Li-Ion / LiFePO4 / Solid-State) — Domain ist
  Spannungsverhalten, nicht Elektrochemie (Trigger 024 Out-of-scope).
- **Temperatur-Telemetrie** — [`M8-welle-4a.md`](M8-welle-4a.md)
  (`GG-BESS-006`), unabhaengig aktivierbar.
