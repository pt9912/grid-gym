# Welle 3c — Blindleistung im Netzbilanzmodell (`GG-GRID-007`)

**Status:** Geplant (M8-Welle-3c) — dritte Sub-Welle, **cross-cutting**
(beruehrt mehrere Geraete + Snapshot-Schemata). **Noch nicht umgesetzt** —
DoD (§2) offen. **Re-Tranche-Kandidat** (3c-a/3c-b, siehe §4).

**Container:** [`M8-welle-3.md`](M8-welle-3.md) §3 (Welle-3-C0-Plan,
Reihenfolge 3a → 3b → 3c — bewusst zuletzt); [`roadmap.md`](roadmap.md)
§4 M8. Design (C1): NEU ADR-Folge (Schaerfung zu
[`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md)) + Q-Emission als
Folge zu [`ADR 0016`](../../adr/0016-pv-load-device-pattern.md) (PV) /
[`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md). Trigger:
[`022`](../open/022-sollte-reactive-power.md) (`GG-GRID-007`, Lastenheft
§11.5; mit dieser Welle aufzuloesen).

---

## 1. Lieferziel

**Blindleistung im Netzmodell**: `reactive_power_kvar` pro
Q-emittierendem Geraet (PV-Wechselrichter mit Q(U)-Kennlinie,
GridConnection), `imbalance_kvar` parallel zu `imbalance_kw` in
`GridModelBilanz`, plus die zugehoerige additive Snapshot-Erweiterung.
Der mit Abstand groesste Slice der Netz-Welle — bewusst zuletzt, nach den
lokalen Schaerfungen 3a/3b.

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [ ] **Q-Emission + Bilanz**: `reactive_power_kvar`-Telemetry +
      Q(U)-Kennlinie in den Q-Geraeten (PV, GridConnection);
      `imbalance_kvar` parallel zu `imbalance_kw` in `GridModelBilanz`
      (`src/grid_gym/hexagon/core/grid_model/bilanz.py`); ≥ 100-Tick-
      Determinismus; **Q-frei = heutiges Verhalten bit-genau**.
- [ ] **Schema additiv + backward-compat**: Roundtrip alt+neu gepinnt,
      Lesepfad fuer die jeweilige Vorversion (analog dem GridModelSnapshot-
      v1→v2-Bump, [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md)/[`ADR 0020`](../../adr/0020-load-profile-and-event-pattern.md)).
      **Konkrete Schema-Liste = C1-Design-Item** (§3).
- [ ] **Gates**: `make gates` gruen (`coverage-gate-critical` ≥ 90 % auf
      `grid_model` + die beruehrten Geraete-Module); NEU ADR(s) `Accepted`;
      Trigger 022 aufgeloest.

## 3. Design-Skizze (C1)

- **Q-Emission**: PV-Wechselrichter Q(U) (spannungsabhaengig),
  GridConnection-Q. `reactive_power_kvar` als neue Metric eines
  `TelemetryPoint` (`src/grid_gym/hexagon/core/domain/telemetry.py` —
  Metric ist generisch, `source`-Tag wie bei `power_kw`).
- **Bilanz**: `imbalance_kvar` = Summe der Q-Beitraege, parallel zur
  Wirkleistungsbilanz (`bilanz.py`-Erweiterung); Q-Spannungs-Kopplung
  (Q beeinflusst `voltage_v`).
- **Multi-Schema-Migration** (eigentliches C1-Design-Item — **nicht** im
  C0-Plan fixiert): das additive Q-Feld beruehrt **mehrere** Schemata:
  - **GridModelSnapshot** (heute v2): Bilanz-Q (`imbalance_kvar`) → v2→v3
    mit v2-Backward-Compat-Lesepfad (analog v1→v2,
    [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md)/[`ADR 0020`](../../adr/0020-load-profile-and-event-pattern.md)).
  - **PV- + GridConnection-Device-Snapshots**: additives
    `reactive_power_kvar`-Feld (eigener additiver Schritt mit
    Default-Defense fuer Altschnappschuesse).
  - **SnapshotEnvelope** ([`ADR 0015`](../../adr/0015-snapshot-envelope-v2.md)):
    **unveraendert** — Q steckt in den Sub-Snapshots, nicht im
    Envelope-Body.
- **Scheinleistung**: `S = sqrt(P² + Q²)` — kanonische `Decimal`-Rundung
  (Design-Frage: sqrt-Praezision); verzahnt mit der 3b-Trafo-Grenze
  ([`M8-welle-3b.md`](M8-welle-3b.md)), die bis hier auf `|P|` rechnet —
  **3c re-pinnt deren Boundary-Tests** auf `S`.

## 4. Risiken / offene Design-Fragen

- **Schema-Migration breit**: mehrere Snapshots gleichzeitig
  (GridModelSnapshot v2→v3 + Device-Snapshots) → **Re-Tranche-Kandidat**:
  3c-a (Q-Bilanz + GridModelSnapshot-Bump) vor 3c-b (Geraete-Q-Emission +
  Device-Snapshots), falls > 300 Zeilen / > 5 Commits.
- **Replay/Export**: der Schema-Bump beruehrt Replay-/Export-Konsumenten
  und die `EXPECTED_DEMO_*`-Hash-Pins; Backward-Compat zwingend; beruehrt
  ggf. `D-1` ([`carveouts.md`](carveouts.md)).
- **Determinismus**: Q(U)-Kennlinie + `sqrt`-Praezision (`Decimal`,
  `AC-NO-RAND`).

## 5. Nicht-Ziele (dieser Slice)

- Detail-Modellierung von Synchron-/Asynchronmaschinen (Schenkelpol,
  Polradwinkel) — Power-Systems-Software-Domain, nicht grid-gym.
- Volle Lastflussrechnung (Newton-Raphson) — grid-gym bleibt bei
  vereinfachter Bilanz-Aggregation.
