# 042 — Fault-Engine-Standort und `*FaultAdapter`-Naming

**Status:** Done 2026-06-13 (M8-Welle-1) — Rename umgesetzt
(`*FaultAdapter` → `*FaultEngine`, Dateien + Symbole), **keine
Compat-Aliase**, [`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md) `Accepted`.
**Datum:** 2026-06-09
**Bezug:**

- [`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md)
  — Standort- und Naming-Entscheidung.
- [`ADR 0022`](../../adr/0022-fault-injection-protocol.md)
  — `FaultInjectableDevice` + `FaultPort`.
- [`ADR 0025`](../../adr/0025-fault-recovery-pattern.md)
  — bestehendes Recovery-Pattern.
- [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)
  — getrennte [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Bridge-Bereinigung.
- [`spec/architecture.md`](../../../../spec/architecture.md)
  — [`GG-AR-COMP-FAULTS`](../../../../spec/architecture.md#5-komponentensicht).
- [`welle-2.md`](../done-archive/welle-2.md)
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

**Umsetzung 2026-06-13 (Done, C0..C3 in einem fullbuild-verifizierten
Schritt):** Rename `BatteryFaultAdapter` → `BatteryFaultEngine` /
`GridFaultAdapter` → `GridFaultEngine` (+ Dateien `*_fault_adapter.py`
→ `*_fault_engine.py` via `git mv`), 17 src-/test-/tools-Dateien;
`__init__`-Docstring + `spec/architecture.md` + `docs/user/observability.md`
auf „Core-Fault-Engine"; [`ADR 0025`](../../adr/0025-fault-recovery-pattern.md)-Pfad-Pflege. **Keine Compat-Aliase**
(alle In-Repo-Referenzen umbenannt, kein Uebergangsbedarf). Standort
bleibt `hexagon/core/faults` ([`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md) §2.1).

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
- Kein neuer [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-`ignore_imports`-Eintrag.
