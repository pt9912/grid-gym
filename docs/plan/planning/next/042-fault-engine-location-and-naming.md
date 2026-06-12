# 042 — Fault-Engine-Standort und `*FaultAdapter`-Naming

**Status:** Next — Scope skizziert, noch nicht aktiv
**Datum:** 2026-06-09
**Bezug:**

- [`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md)
  — Standort- und Naming-Entscheidung.
- [`ADR 0022`](../../adr/0022-fault-injection-protocol.md)
  — `FaultInjectableDevice` + `FaultPort`.
- [`ADR 0025`](../../adr/0025-fault-recovery-pattern.md)
  — bestehendes Recovery-Pattern.
- [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)
  — getrennte `AC-ADAPTER-PURE`-Bridge-Bereinigung.
- [`spec/architecture.md`](../../../../spec/architecture.md)
  — `GG-AR-COMP-FAULTS`.
- [`welle-2.md`](../done/welle-2.md)
  — historische Standortentscheidung fuer `hexagon/core/faults`.

---

## 1. Ziel

Dieser Slice klaert die missverstaendliche Benennung
`BatteryFaultAdapter`/`GridFaultAdapter`. Die Klassen liegen bewusst
unter `hexagon/core/faults`; sie sind Core-Fault-Engines, keine
Outer-Ring-Adapter unter `grid_gym.adapters`.

Der Slice ist getrennt von
[`041-adapter-pure-ignore-imports-rueckbau.md`](041-adapter-pure-ignore-imports-rueckbau.md):
041 entfernt Adapter->Core-Imports; 042 klaert, wie die Fault-Klassen
langfristig heissen und dokumentiert sind.

## 2. Tranchierung

### C0 — Referenz-Audit

- Alle produktiven Imports, Tests und Doku-Referenzen auf
  `BatteryFaultAdapter`, `GridFaultAdapter`,
  `battery_fault_adapter.py`, `grid_fault_adapter.py` erfassen.
- Entscheiden, ob Symbol-Rename jetzt sinnvoll ist oder ob zunaechst
  nur Doku-/Docstring-Begriffsklaerung erfolgt.
- Sensor: `rg`-Audit + Handoff-Liste.

### C1 — Doku-Begriffsklaerung

- Neue Doku spricht von Core-Fault-Engine.
- Historische Stellen bleiben unveraendert, wenn sie in Accepted ADRs
  liegen; stattdessen [`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md) und diese Slice-Notiz referenzieren.
- Falls lebende Doku oder `spec/architecture.md` falsche Dateinamen
  oder missverstaendliche Adapter-Begriffe fuehrt, diese
  aktualisieren.
- Sensor: `make docs-check`.

### C2 — Optionaler Symbol-/Datei-Rename

Nur wenn C0 den Rename als sinnvoll bestaetigt:

- `BatteryFaultAdapter` -> `BatteryFaultEngine`
- `GridFaultAdapter` -> `GridFaultEngine`
- `battery_fault_adapter.py` -> `battery_fault_engine.py`
- `grid_fault_adapter.py` -> `grid_fault_engine.py`

Repo-Regel beachten:

1. reiner Rename-/Move-Commit (`git mv` fuer Dateien),
2. Inhalts-/Import-/Doku-Rewrite im Folgecommit.

Compatibility-Aliase im Paket-Interface sind erlaubt, wenn bestehende
Tests oder externe Imports sonst unnoetig brechen.

### C3 — Tests und Gate-Sync

- Fault-Unit-Tests auf neue Namen oder Compatibility-Aliase
  aktualisieren.
- Integration-Fault-Composition pruefen.
- Sensoren:
  - engste Fault-Unit-Tests,
  - `make arch-check`,
  - `make docs-check`,
  - bei Symbol-Rename nach Moeglichkeit `make gates`.

## 3. Nicht-Ziele

- Kein Move nach `adapters/driven/fault_*`, solange keine echte externe
  Fault-Boundary existiert.
- Keine neue Fault-Semantik.
- Keine Aenderung an `FaultPort.apply_active_faults(...)`.
- Kein direktes Umschreiben historischer Accepted-ADR-Texte.

## 4. DoD

- [`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md) ist im ADR-Index gelistet.
- Lebende Doku benennt die Klassen als Core-Fault-Engines oder
  dokumentiert den historischen `*Adapter`-Namen explizit.
- Wenn ein Rename erfolgt: Dateien und Symbole folgen der
  Rename-Commit-Regel, Tests sind angepasst, Compatibility-Aliase sind
  bewusst entschieden.
- `make docs-check` gruen.
- Kein neuer `AC-ADAPTER-PURE`-`ignore_imports`-Eintrag.
