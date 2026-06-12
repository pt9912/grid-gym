# 016 — SOLLTE: EV-Charger-Device (`GG-DEV-015`)

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-20
**Quelle:** [`done/M2-devices.md §4 Out-of-Scope`](../done-archive/M2-devices.md)
(Welle-7-Erbschaft); Lastenheft §9.4 (`GG-DEV-015..018`).

---

## Trigger

Lastenheft `GG-DEV-015` definiert ein **EV-Charger-Geraetemodell**
als SOLLTE-Item. M2 hat das aus Scope-Gruenden out-of-scope
gehalten und nur die fuenf MVP-MUSS-Geraete implementiert
(Battery, PV, Load, GridConnection, SmartMeter). Der MVP-Demo
(`tests/integration/scenarios/mvp_demo.yaml`, Welle 6c) kommt
ohne EV-Charger aus.

EV-Charger wird relevant, sobald eine Use-Case-Story Lade-Profile
mit Netzanschluss-Constraints erfordert (z. B. Demand-Response-
Szenarien, V2G-Demos).

## Erwartete Lieferung

- ADR-Folge analog [`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md)
  mit EV-spezifischen Akzeptanzkriterien (Lade-/Entlade-Curves,
  Stecker-Zustand, optional bidirektional fuer V2G).
- `src/grid_gym/hexagon/core/devices/ev_charger/`-Submodul mit
  `EvChargerDevice`, `EvChargerConfig`, Snapshot-Roundtrip-Test,
  Property-Test fuer Determinismus.
- `_DEVICE_FACTORIES["ev_charger"]`-Eintrag in
  `core/scenario/loader.py`.
- Scenario-Validator schaerft fuer neue `params`-Felder
  (max_charge_kw, max_discharge_kw fuer V2G, plug_state, etc.).
- `CRITICAL_COV_TARGETS`-Default um `devices/ev_charger`
  erweitert.

## Aktivierungs-Kriterium

- Use-Case-Story mit EV-Charger als Akzeptanzkriterium
  (z. B. V2G-Demo, Demand-Response-Pilot).
- ODER: M3-Faults-Slice braucht EV-Charger fuer
  Fault-Injection-Demo (z. B. Charger-Ausfall im Multi-Agent-
  Szenario).

## Out-of-scope

- Multi-EV-Pool / Smart-Charging-Logik — eigenes ML-Slice.
- Protokollanschluss (ISO 15118, OCPP) — Adapter-Slice
  separat (M4-Material).
