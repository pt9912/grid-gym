# 020 — SOLLTE: Inselnetz-Bilanzmodell (`GG-GRID-005`)

**Status:** Resolved — M8-Welle-3a (2026-06-16). Geliefert via
[`ADR 0060`](../../adr/0060-island-grid-bilanz-pattern.md) `Accepted`
+ `GridModelConfig.is_islanded`/`forming_device_id` + TickLoop-Insel-Fork
(Forming-Geraet als Slack) ([`M8-welle-3a.md`](../done/M8-welle-3a.md)).
Doc-Archivierung nach `done-archive/` folgt mit der M8-Meilenstein-Closure
([`carveouts.md`](../in-progress/carveouts.md) §3-Konvention).
**Datum:** 2026-05-20
**Quelle:** [`done/M2-devices.md §4 Out-of-Scope`](../done-archive/M2-devices.md)
(Welle-7-Erbschaft); Lastenheft §11.5 ([`GG-GRID-005`](../../../../spec/lastenheft.md#gg-grid-005)..007).

---

## Trigger

Lastenheft [`GG-GRID-005`](../../../../spec/lastenheft.md#gg-grid-005) definiert ein **Inselnetz-
Bilanzmodell** als SOLLTE-Item. M2 deckt nur Netzanschluss-
gebundene Bilanz (`GridModelBilanz` mit `grid_connection`-
Auto-Schluss, [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md))
ab. Inselnetz unterscheidet sich: kein externer Slack-Bus,
Frequenz/Spannung muss von einem internen Quellgeraet gehalten
werden (typischerweise Diesel- oder Battery-Inverter mit
Grid-Forming-Mode).

## Erwartete Lieferung

- ADR-Folge analog [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md)
  mit Inselnetz-spezifischen Akzeptanzkriterien:
  - Grid-Forming-Geraet-Election (welches Geraet haelt Frequenz).
  - Frequenz-/Spannungs-Toleranzen ohne externen Slack.
  - Black-Start-Sequenz (Initialisierung ohne Netzanschluss).
- Erweiterung von `GridModelConfig` um Inselnetz-Parameter
  (`is_islanded: bool`, `forming_device_id: str | None`).
- TickLoop-Auto-Schluss-Logik: in Inselnetz wird **kein**
  `grid_connection` als Slack genommen; stattdessen das
  Grid-Forming-Geraet.
- Determinismus-Property-Test fuer Inselnetz-Bilanz.

## Aktivierungs-Kriterium

- Use-Case-Story mit Inselnetz / Microgrid / Off-Grid-Demo.
- ODER: M3-Fault-Slice mit „Netzanschluss faellt aus,
  Microgrid muss einspringen"-Szenario.

## Out-of-scope

- Schwarzstart-Synchronisation zwischen mehreren Inselnetzen
  — eigener Trigger, falls aktiv.
- Lastabwurfschemata (Load-Shedding) — separater Trigger im
  Multi-Agent-Kontext.
