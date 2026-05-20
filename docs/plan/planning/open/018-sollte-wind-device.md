# 018 — SOLLTE: Wind-Device (`GG-DEV-017`)

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-20
**Quelle:** [`done/M2-devices.md §4 Out-of-Scope`](../done/M2-devices.md)
(Welle-7-Erbschaft); Lastenheft §9.4 (`GG-DEV-015..018`).

---

## Trigger

Lastenheft `GG-DEV-017` definiert ein **Wind-Generator-Modell**
als SOLLTE-Item. M2 deckt nur PV (`PvDevice`) als
Erneuerbare-Einspeise-Variante ab; Wind hat eigene Charakteristiken
(Windgeschwindigkeits-Leistungs-Kurve, Schaltzustaende
„unter/im/ueber Nennwindbereich").

Wind wird relevant fuer realistische Erneuerbare-Mix-Szenarien
(z. B. Demand-Response mit PV + Wind, Speicher-Optimierung).

## Erwartete Lieferung

- ADR-Folge analog [`ADR 0016`](../../adr/0016-pv-load-device-pattern.md)
  (PV-Pattern) mit Wind-spezifischen Akzeptanzkriterien
  (cut-in-/cut-out-/rated-Wind-Geschwindigkeiten, kubisch-
  proportionale Leistungskennlinie zwischen cut-in und Nennwind).
- `src/grid_gym/hexagon/core/devices/wind/`-Submodul mit
  `WindDevice`, `WindConfig`, Property-Test fuer Determinismus.
- Profile-Eingang (analog `LoadProfile`) fuer Windgeschwindigkeit;
  alternativ stochastisches Modell mit Seed.
- Scenario-Validator + Loader-Factory-Eintrag.
- `CRITICAL_COV_TARGETS`-Default um `devices/wind` erweitert.

## Aktivierungs-Kriterium

- Use-Case-Story mit Wind als zweiter Erneuerbarer-Quelle.
- ODER: Stochastik-Slice (Erweiterung von `RandomPort`-
  Sub-Streams fuer Wettervariablen).

## Out-of-scope

- Detail-Aerodynamik / Turbinen-Mechanik — Domain ist
  Power-Output, keine Mechanik.
- Wakes / Park-Effekte bei mehreren Turbinen — eigener Trigger,
  falls aktiv.
