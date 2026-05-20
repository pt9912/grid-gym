# 021 — SOLLTE: Transformatorgrenzen im Netzbilanzmodell (`GG-GRID-006`)

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-20
**Quelle:** [`done/M2-devices.md §4 Out-of-Scope`](../done/M2-devices.md)
(Welle-7-Erbschaft); Lastenheft §11.5 (`GG-GRID-005..007`).

---

## Trigger

Lastenheft `GG-GRID-006` definiert **Transformatorgrenzen** im
Netzbilanzmodell als SOLLTE-Item. M2 deckt das nicht ab;
`GridModelBilanz` ([`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md))
kennt aktuell nur Frequenz- und Spannungs-Clamps, aber keine
Wandlungs-Grenzen oder Saettigung.

Klare Abgrenzung zu Trigger 017 (`GG-DEV-016` Transformer-Device):
Trigger 017 ist ein eigenstaendiges Geraetemodell; Trigger 021
ist eine **Erweiterung des Bilanzmodells** um Trafo-Grenzwerte
(z. B. Ueberlast-Schutzkennlinien, thermische Grenzen).

## Erwartete Lieferung

- ADR-Folge als Erweiterung zu
  [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md)
  (Schaerfung-Pattern, kein Supersede) mit Transformator-
  Grenzwerten:
  - `max_apparent_power_kva`, `overload_curve` (Zeit-Strom-
    Kennlinie).
  - Thermisches Modell (vereinfacht): Top-Oil-Temperatur,
    Hot-Spot-Temperatur.
- Erweiterung von `GridModelConfig` um Transformator-Block.
- TickLoop ruft Grenz-Check pro Tick; bei Verletzung wird ein
  `GridConstraintViolationEvent` emittiert (Pattern wie
  `BatteryConfigInvalidValueError`).
- Determinismus-Property-Test.

## Aktivierungs-Kriterium

- Use-Case-Story mit Ueberlast-Schutz (z. B. PV-Mittagspitze
  ueberschreitet Trafo-Nennleistung).
- ODER: M3-Fault-Slice mit Ueberhitzungs-Demo.

## Out-of-scope

- Schutzgeraete-Logik (Distanzschutz, Differentialschutz) —
  M4-Material (Protokolladapter zu Schutzrelais).
- Reparatur-Zeiten / Asset-Management — Domain ist
  elektrisches Verhalten, keine Asset-Lifecycle-Logik.
