# 022 — SOLLTE: Blindleistung im Netzbilanzmodell (`GG-GRID-007`)

**Status:** In Arbeit (teil-geliefert) — **3c-a Done 2026-06-16**
([`ADR 0062`](../../adr/0062-reactive-power-bilanz-pattern.md) `Accepted`):
Q-Bilanz im `grid_model` (`imbalance_kvar` + Q-Spannungskopplung +
GridModelSnapshot v2→v3). **Offen: 3c-b** — Geraete-Q-Emission (PV-Q(U),
GridConnection-Q) + Device-Snapshots + TickLoop-Q-Aggregation + Transformer
`S=sqrt(P²+Q²)`. Trigger wird mit **3c-b** aufgeloest
([`M8-welle-3c.md`](../in-progress/M8-welle-3c.md) §4 Re-Tranche).
**Datum:** 2026-05-20
**Quelle:** [`done/M2-devices.md §4 Out-of-Scope`](../done-archive/M2-devices.md)
(Welle-7-Erbschaft); Lastenheft §11.5 (`GG-GRID-005..007`).

---

## Trigger

Lastenheft `GG-GRID-007` definiert **Blindleistung** als
SOLLTE-Item im Netzbilanzmodell. M2 deckt nur Wirkleistung
(`power_kw`) ab; alle Devices emittieren `power_kw`, und
`GridModelBilanz` ([`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md))
bilanziert nur Wirkleistung. Blindleistung (`reactive_power_kvar`)
ist relevant fuer Spannungshaltung, PV-Wechselrichter-
Charakteristiken (Q(U)-Regelung, cos-phi-Vorgabe) und Trafo-
Belastung (Scheinleistung).

## Erwartete Lieferung

- ADR-Folge als Erweiterung zu
  [`ADR 0019`](../../adr/0019-grid-model-bilanz-pattern.md)
  (Schaerfung-Pattern) mit Q-Spannungs-Kopplung:
  - `reactive_power_kvar`-Telemetry-Metric.
  - Q(U)-Regelkennlinie pro Geraet.
  - Bilanz-Erweiterung: `imbalance_kvar` parallel zu
    `imbalance_kw`.
- ADR-Folge zu [`ADR 0016`](../../adr/0016-pv-load-device-pattern.md)
  und [`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md)
  fuer Q-Emission pro Geraet (PV-Wechselrichter, GridConnection).
- Snapshot-Schema-Bump auf v3 (analog [`ADR 0015`](../../adr/0015-snapshot-envelope-v2.md) Pattern v1→v2),
  wenn das Bilanz-Mapping `imbalance_kvar` strukturierend
  ergaenzt.
- Determinismus-Property-Test fuer Q-Bilanz.

## Aktivierungs-Kriterium

- Use-Case-Story mit Spannungshaltung (z. B. PV-
  Q(U)-Regelung als Akzeptanzkriterium).
- ODER: M3-Faults-Slice mit „Blindleistungs-Defizit fuehrt
  zu Spannungseinbruch"-Szenario.

## Out-of-scope

- Detail-Modellierung von Synchron-/Asynchronmaschinen
  (Schenkelpol, Polradwinkel) — Power-Systems-Software-Domain,
  nicht grid-gym.
- Lastflussrechnung (Newton-Raphson) — grid-gym bleibt
  bei vereinfachter Bilanz-Aggregation; volle Lastflussrechnung
  ist eigenes ML-/Simulations-Projekt.
