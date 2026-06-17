# 023 — SOLLTE: Battery-Temperatur-Telemetry (`GG-BESS-006`)

**Status:** **Resolved 2026-06-17** — M8-Welle-4a. Geliefert via
[`ADR 0065`](../../adr/0065-battery-thermal-telemetry-pattern.md) `Accepted`
+ opt-in `ThermalConfig` auf `BatteryConfig` (stateful Single-Zonen-Euler,
analog [`ADR 0061`](../../adr/0061-transformer-limit-bilanz-pattern.md))
+ opt-in `temperature_celsius`-Telemetrie (`unit="degC"`) + opt-in
Snapshot-Serialisierung ohne Versions-Bump
([`M8-welle-4a.md`](../in-progress/M8-welle-4a.md)). Doc-Archivierung nach
`done-archive/` folgt mit der M8-Meilenstein-Closure.
**Datum:** 2026-05-20
**Quelle:** [`done/M2-devices.md §4 Out-of-Scope`](../done-archive/M2-devices.md)
(Welle-7-Erbschaft); Lastenheft §10.6 (`GG-BESS-006`/`007`).

---

## Trigger

Lastenheft `GG-BESS-006` definiert **Temperatur-Telemetry** als
SOLLTE-Erweiterung des Battery-Modells. M2 deckt
([`ADR 0014`](../../adr/0014-battery-snapshot-schema.md)) nur
SOC, Strom, Spannung, Ramp ab. Temperatur ist relevant fuer
- thermische Sicherheits-Constraints (Lade-/Entlade-Derating bei
  hoher Temperatur),
- Alterungs-Modelle (Kalender-/Zyklen-Alterung sind T-abhaengig),
- Fault-Injection (M3) mit thermischen Anomalien.

## Erwartete Lieferung

- ADR-Folge als Erweiterung zu
  [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md)
  (Schaerfung-Pattern, kein Supersede) mit T-Modell:
  - Vereinfacht: T als zustandsfreie Berechnung aus
    `power_kw**2 * R_internal` + `T_ambient` + Zeitkonstante.
  - Alternativ: stateful T mit thermischer Masse + Kuehlpfad.
- Battery-Snapshot um `temperature_celsius`-Feld erweitert
  (additiv; Snapshot-Schema bleibt v2-kompatibel, weil das
  Sub-Snapshot per [`ADR 0015`](../../adr/0015-snapshot-envelope-v2.md) §2.3 frei erweiterbar ist).
- Telemetry-Metric `temperature_celsius` (SI-Einheit per
  `GG-DATA-002`).
- Property-Test fuer T-Determinismus.

## Aktivierungs-Kriterium

- Use-Case-Story mit thermischem Battery-Management.
- ODER: M3-Fault-Slice mit „Battery-Ueberhitzung loest
  Notabschaltung aus"-Szenario.

## Out-of-scope

- Zellebene-Thermodynamik — Battery-Modell bleibt auf Pack-
  Niveau; Zellauffloesung waere eigenes Slice.
- Aktive Kuehlung-/Heizung-Logik — Domain ist Battery-Verhalten,
  Kuehl-Aggregat-Modellierung ist HVAC-Slice.
- Kombination mit Trigger 024 (Zellspannungen): unabhaengig
  aktivierbar, koennen aber gemeinsam aktiviert werden.
