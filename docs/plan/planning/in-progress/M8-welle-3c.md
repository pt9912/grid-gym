# Welle 3c — Blindleistung im Netzbilanzmodell (`GG-GRID-007`)

**Status:** In Arbeit (re-tranchiert 3c-a/3c-b, siehe §4) — **3c-a Done
2026-06-16** ([`ADR 0062`](../../adr/0062-reactive-power-bilanz-pattern.md)
`Accepted`): Q-Bilanz im `grid_model` (`imbalance_kvar` + Q-Spannungskopplung
+ `voltage_sensitivity_v_per_kvar` opt-in + GridModelSnapshot v2→v3,
backward-compat; Q-frei bit-genau, Demo-Pins unberuehrt). **Offen: 3c-b** —
Geraete-Q-Emission (PV-Q(U), GridConnection-Q) + Device-Snapshots +
TickLoop-Q-Aggregation + Transformer `S=sqrt(P²+Q²)` (re-pinnt 3b-Boundary)
+ Demo-Telemetry-Re-Pin. **Trigger 022 bleibt offen bis 3c-b.**

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

- [~] **Q-Emission + Bilanz** (3c-a: Bilanz Done / 3c-b: Geraete-Q offen):
      `imbalance_kvar` parallel zu `imbalance_kw` in `GridModelBilanz` +
      Q-Spannungskopplung **Done** (3c-a,
      [`ADR 0062`](../../adr/0062-reactive-power-bilanz-pattern.md);
      ≥ 100-Tick-Determinismus, **Q-frei bit-genau** gepinnt).
      `reactive_power_kvar`-Telemetry + Q(U)-Kennlinie in den Q-Geraeten
      (PV, GridConnection) **offen (3c-b)**.
- [~] **Schema additiv + backward-compat** (3c-a: GridModelSnapshot Done /
      3c-b: Device-Snapshots offen): GridModelSnapshot **v2→v3** mit
      v1/v2-Lesepfad + Roundtrip-Pins **Done** (3c-a); PV-/GridConnection-
      Device-Snapshots **offen (3c-b)**.
- [~] **Gates**: 3c-a-Gates gruen (`coverage-gate-critical` ≥ 90 %
      `grid_model`); [`ADR 0062`](../../adr/0062-reactive-power-bilanz-pattern.md)
      `Accepted`. **Trigger 022 bleibt offen bis 3c-b**; die beruehrten
      Geraete-Module + Demo-Re-Pin folgen mit 3c-b.

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
