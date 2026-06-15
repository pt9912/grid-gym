# 017 — SOLLTE: Transformer-Device (`GG-DEV-016`)

**Status:** Resolved — M8-Welle-2b (2026-06-14). Geliefert via
[`ADR 0056`](../../adr/0056-transformer-device-pattern.md) `Accepted` +
`hexagon/core/devices/transformer/`
([`M8-welle-2b.md`](../done/M8-welle-2b.md)). Doc-Archivierung
nach `done-archive/` folgt mit der M8-Meilenstein-Closure
(`carveouts.md` §3-Konvention).
**Datum:** 2026-05-20
**Quelle:** [`done/M2-devices.md §4 Out-of-Scope`](../done-archive/M2-devices.md)
(Welle-7-Erbschaft); Lastenheft §9.4 (`GG-DEV-015..018`).

---

## Trigger

Lastenheft `GG-DEV-016` definiert ein **Transformer-Geraetemodell**
als SOLLTE-Item. M2 hat das out-of-scope gehalten; der MVP-Demo
nutzt `GridConnectionDevice` als idealisierten Netzanschluss
ohne Transformator-Verluste oder -Grenzen.

Transformer-Device wird relevant, sobald Mittelspannungs-/
Niederspannungs-Konversion oder magnetische Saettigung im
Szenario modelliert werden muss.

## Erwartete Lieferung

- ADR-Folge analog [`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md)
  mit Transformer-spezifischen Akzeptanzkriterien (Wandlungs-
  verhaeltnis, Kupferverluste, Eisenverluste, Saettigungs-
  Kennlinie).
- `src/grid_gym/hexagon/core/devices/transformer/`-Submodul mit <!-- d-check:ignore (geplant: entsteht mit Trigger-Aktivierung) -->
  `TransformerDevice`, `TransformerConfig`, Snapshot-Roundtrip,
  Determinismus-Property-Test.
- Scenario-Validator + Loader-Factory-Eintrag.
- `CRITICAL_COV_TARGETS`-Default um `devices/transformer`
  erweitert.
- Klare Abgrenzung zu Trigger 021 (`GG-GRID-006`
  Transformatorgrenzen im Netzbilanzmodell) — Trigger 017 ist
  ein Geraetemodell, Trigger 021 ist eine Netzbilanz-
  Erweiterung.

## Aktivierungs-Kriterium

- Use-Case-Story mit Multi-Spannungsebene
  (MS-Sammelschiene, NS-Endkundenanschluss).
- ODER: Sicherheits-Szenario braucht Transformator-Schutz
  (Ueberlast, Kurzschluss) — Kopplung mit M3-Fault-Injection.

## Out-of-scope

- Detail-Modellierung von Wicklungstemperaturen / Alterung —
  M5+ Material.
- Spannungsregelung via Stufenschalter — eigener Trigger,
  falls aktiv.
