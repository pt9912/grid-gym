# 024 — SOLLTE: Battery-Zellspannung-Telemetry (`GG-BESS-007`)

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-20
**Quelle:** [`done/M2-devices.md §4 Out-of-Scope`](../done/M2-devices.md)
(Welle-7-Erbschaft); Lastenheft §10.6 (`GG-BESS-006`/`007`).

---

## Trigger

Lastenheft `GG-BESS-007` definiert **Zellspannung-Telemetry**
als SOLLTE-Erweiterung des Battery-Modells. M2 deckt
([`ADR 0014`](../../adr/0014-battery-snapshot-schema.md)) nur
Pack-Niveau (SOC) ab. Zellspannung ist relevant fuer
- Balancing-Logik (Zellabweichungen erkennen + ausgleichen),
- Sicherheitsabschaltung bei Ueber-/Unterspannung,
- Fault-Injection (M3) mit Zelldefekten.

## Erwartete Lieferung

- ADR-Folge als Erweiterung zu
  [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md)
  mit Zell-Modell:
  - Konfigurierbare Zellzahl `n_cells: int`.
  - Vereinfacht: alle Zellen identisch; `cell_voltage_v =
    pack_voltage / n_cells`.
  - Erweitert: pro Zelle individueller Wert mit Rausch-Quelle
    aus `RandomPort.sub_port("cell-<idx>")`.
- Battery-Snapshot um `cell_voltages_v: tuple[Decimal, ...]`
  Feld erweitert.
- Telemetry-Metric `cell_voltage_v` pro Zelle (oder aggregated:
  `min_cell_voltage_v` + `max_cell_voltage_v`).
- Determinismus-Property-Test (gleicher Seed →
  identische Zellspannungs-Trace).

## Aktivierungs-Kriterium

- Use-Case-Story mit Zell-Balancing oder Sicherheitsabschaltung.
- ODER: M3-Fault-Slice mit „defekte Zelle"-Demo.

## Out-of-scope

- Zell-Chemie-Detailmodelle (Li-Ion / LiFePO4 /
  Solid-State) — Domain ist Spannungsverhalten, nicht
  Elektrochemie.
- Kombination mit Trigger 023 (Temperatur): unabhaengig
  aktivierbar, koennen aber gemeinsam aktiviert werden.
