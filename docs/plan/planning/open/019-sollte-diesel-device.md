# 019 — SOLLTE: Diesel-Device (`GG-DEV-018`)

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-20
**Quelle:** [`done/M2-devices.md §4 Out-of-Scope`](../done-archive/M2-devices.md)
(Welle-7-Erbschaft); Lastenheft §9.4 (`GG-DEV-015..018`).

---

## Trigger

Lastenheft `GG-DEV-018` definiert ein **Diesel-Generator-Modell**
als SOLLTE-Item. M2 deckt das nicht ab; der MVP-Demo nutzt
`GridConnectionDevice` fuer den Energiebilanz-Ausgleich (Auto-
Schluss). Diesel ist relevant fuer Inselnetz-Szenarien
(Notstrom, Black-Start) und Hybrid-Off-Grid-Setups.

## Erwartete Lieferung

- ADR-Folge analog [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md)
  (Battery-Pattern, weil Diesel ebenfalls eine endliche Ressource
  hat) mit Diesel-spezifischen Akzeptanzkriterien (Kraftstoff-
  Vorrat in Litern, Verbrauch in l/kWh, Min-Startleistung,
  Ramp-Limits, Anfahr-/Abstell-Hysterese).
- `src/grid_gym/hexagon/core/devices/diesel/`-Submodul mit
  `DieselDevice`, `DieselConfig`, Determinismus-Property-Test.
- Scenario-Validator + Loader-Factory-Eintrag.
- `CRITICAL_COV_TARGETS`-Default um `devices/diesel` erweitert.
- Klare Abgrenzung zu Trigger 020 (`GG-GRID-005` Inselnetz) —
  Diesel ist eine Quelle im Inselnetz, das Bilanzmodell selbst
  ist eigener Trigger.

## Aktivierungs-Kriterium

- Use-Case-Story mit Inselnetz oder Notstrom-Demo.
- ODER: M3-Fault-Slice braucht Diesel als Backup-Quelle
  fuer „Hauptnetz faellt aus"-Szenarien.

## Out-of-scope

- Emissions-Modellierung (CO2, NOx) — eigener Trigger im
  Sustainability-Modul, falls aktiv.
- Wartungsintervalle / Verfuegbarkeit — Domain ist
  Power-Output, keine Asset-Management-Logik.
