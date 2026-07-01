# Welle 3c — Blindleistung im Netzbilanzmodell (`GG-GRID-007`)

**Status:** **Done 2026-06-16** (re-tranchiert 3c-a → 3c-b-1 → 3c-b-2,
siehe §4) — **3c-a**
([`ADR 0062`](../../adr/0062-reactive-power-bilanz-pattern.md) `Accepted`):
Q-Bilanz im `grid_model` (`imbalance_kvar` + Q-Spannungskopplung +
`voltage_sensitivity_v_per_kvar` opt-in + GridModelSnapshot v2→v3). **3c-b-1**
([`ADR 0063`](../../adr/0063-pv-volt-var-q-emission-pattern.md)
`Accepted`): erste Q-Quelle — `DeviceTickContext.grid_voltage_v` (lagged) +
opt-in PV-`VoltVarConfig`-Q(U) + TickLoop-`reactive_kvar`-Aggregation →
`grid_model.update`; Q-frei pin-neutral. **3c-b-2**
([`ADR 0064`](../../adr/0064-grid-connection-q-transformer-apparent-power.md)
`Accepted`): GridConnection-Q-Auto-Schluss (Spiegel zum P-Slack) +
Transformer `S=sqrt(P²+Q²)` (re-pinnt 3b-Boundary als Q=0-Regressionspin) +
opt-in GridConnection-Snapshot-Q. **Trigger 022 aufgeloest — [`GG-GRID-007`](../../../../spec/lastenheft.md#gg-grid-007)
komplett; M8-Welle 3 (Netz) abgeschlossen.**

**Container:** [`M8-welle-3.md`](M8-welle-3.md) §3 (Welle-3-C0-Plan,
Reihenfolge 3a → 3b → 3c — bewusst zuletzt); [`roadmap.md`](../in-progress/roadmap.md)
§4 M8. Design (C1): NEU ADR-Folge (Schaerfung zu
[`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md)) + Q-Emission als
Folge zu [`ADR 0016`](../../adr/0016-pv-load-device-pattern.md) (PV) /
[`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md). Trigger:
[`022`](../done-archive/022-sollte-reactive-power.md) ([`GG-GRID-007`](../../../../spec/lastenheft.md#gg-grid-007), Lastenheft
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

- [x] **Q-Emission + Bilanz**: `imbalance_kvar` parallel zu `imbalance_kw`
      in `GridModelBilanz` + Q-Spannungskopplung **Done** (3c-a,
      [`ADR 0062`](../../adr/0062-reactive-power-bilanz-pattern.md);
      ≥ 100-Tick-Determinismus, **Q-frei bit-genau** gepinnt).
      `reactive_power_kvar`-Telemetry + Q(U)-Kennlinie in den Q-Geraeten
      **Done**: PV-Q(U) (3c-b-1,
      [`ADR 0063`](../../adr/0063-pv-volt-var-q-emission-pattern.md)) +
      GridConnection-Q-Auto-Schluss (3c-b-2,
      [`ADR 0064`](../../adr/0064-grid-connection-q-transformer-apparent-power.md)).
- [x] **Schema additiv + backward-compat**: GridModelSnapshot **v2→v3** mit
      v1/v2-Lesepfad + Roundtrip-Pins **Done** (3c-a); PV- (3c-b-1) +
      GridConnection-Device-Snapshots (3c-b-2) tragen Q **opt-in** (kein
      Versions-Bump, Q-frei byte-identisch).
- [x] **Gates**: alle Slice-Gates gruen (`coverage-gate-critical` ≥ 90 %
      `grid_model`); [`ADR 0062`](../../adr/0062-reactive-power-bilanz-pattern.md)/
      [`ADR 0063`](../../adr/0063-pv-volt-var-q-emission-pattern.md)/
      [`ADR 0064`](../../adr/0064-grid-connection-q-transformer-apparent-power.md)
      `Accepted`. **Trigger 022 aufgeloest**; Demo pin-neutral (Q-frei) ueber
      alle drei Slices.

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
  ggf. `D-1` ([`carveouts.md`](../in-progress/carveouts.md)).
- **Determinismus**: Q(U)-Kennlinie + `sqrt`-Praezision (`Decimal`,
  [`AC-NO-RAND`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)).

## 5. Nicht-Ziele (dieser Slice)

- Detail-Modellierung von Synchron-/Asynchronmaschinen (Schenkelpol,
  Polradwinkel) — Power-Systems-Software-Domain, nicht grid-gym.
- Volle Lastflussrechnung (Newton-Raphson) — grid-gym bleibt bei
  vereinfachter Bilanz-Aggregation.
