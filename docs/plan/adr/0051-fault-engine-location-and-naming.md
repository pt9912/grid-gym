# ADR 0051 — Fault-Engine-Standort und Adapter-Begriffsklaerung

**Status:** Proposed
**Datum:** 2026-06-09
**Bezug:**

- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — ADR-Lifecycle.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung
  ohne Supersedes.
- [`ADR 0022`](0022-fault-injection-protocol.md) —
  `FaultInjectableDevice` + `FaultPort`.
- [`ADR 0025`](0025-fault-recovery-pattern.md) —
  Recovery-Pattern und bestehende `BatteryFaultAdapter`-/
  `GridFaultAdapter`-Implementierungen.
- [`ADR 0050`](0050-adapter-pure-bridge-retirement.md) —
  `AC-ADAPTER-PURE`-Bridge-Rueckbau; verweist den
  Fault-Klassen-Standort auf diese Folgeentscheidung.
- [`spec/architecture.md`](../../../spec/architecture.md#driven-ports-vom-kern-aufgerufen) —
  `GG-AR-COMP-FAULTS` und `GG-AR-PORT-DRN-011`.
- [`welle-2.md`](../planning/done/welle-2.md) — historischer
  Welle-2-Plan; dokumentiert, dass `BatteryFaultAdapter` und
  `GridFaultAdapter` bewusst unter `hexagon/core/faults/` liegen.
- [`042-fault-engine-location-and-naming.md`](../planning/next/042-fault-engine-location-and-naming.md)
  — geplanter Umsetzungsslice.

---

## 1. Kontext

`BatteryFaultAdapter` und `GridFaultAdapter` liegen heute unter
`src/grid_gym/hexagon/core/faults/`. Das ist nicht zufaellig:
Welle 2 dokumentierte ausdruecklich, dass die Klassen **nicht** unter
`adapters/driven/fault_*` liegen, weil ein echter Adapter unter
`adapters/driven/` wegen `AC-ADAPTER-PURE` weder
`FaultInjectableDevice` noch `DeviceModel` importieren koennte.

Die Architektur beschreibt dieselben Klassen als Domain-
Orchestrierung, nicht als Uebersetzer eines externen Protokolls. ADR
0025 beschreibt sie zugleich als Recovery-Engines: Devices halten den
physischen Fault-State, die Fault-Klassen halten Scheduling,
Aktivitaetsfenster und Recovery-Entscheidungen.

Der Name `*FaultAdapter` ist trotzdem missverstaendlich. In der
Repo-Terminologie bedeutet `adapters/*` normalerweise Outer-Ring,
I/O-, Framework- oder Infrastruktur-Code. Hier ist `Adapter` aber im
Port-Pattern-Sinn gemeint: Die Klassen implementieren `FaultPort`,
sind aber fachlich Teil von `GG-AR-COMP-FAULTS`.

## 2. Entscheidung

### 2.1 Standort bleibt `hexagon/core/faults`

`BatteryFaultAdapter` und `GridFaultAdapter` bleiben fachlich im
Core-Fault-Komponentenbereich (`hexagon/core/faults`). Sie werden
nicht nach `grid_gym.adapters.driven.fault_*` verschoben.

Begruendung:

- Die Klassen treffen deterministische Fault-Recovery-Entscheidungen
  (`active`/`inactive`, half-open Windows, manual recovery) und sind
  damit fachliche Simulationslogik.
- Sie haengen an Core-Sub-Protocols (`FaultInjectableDevice`) und
  Core-Domain-Typen (`ScenarioFault`, `DeviceTickContext`).
- Ein Move nach `adapters/driven` wuerde eine falsche externe
  Boundary suggerieren. Es gibt keine externe Fault-Infrastruktur, die
  adaptiert wird.
- `FaultPort` bleibt der abstrakte Hook, den `TickLoop` aufruft. Die
  konkreten Fault-Engines sind eine Core-seitige Implementierung
  dieses Hooks.

### 2.2 Begriff: Core-Fault-Engine statt Outer-Ring-Adapter

Neue Doku und neue Code-Kommentare verwenden fuer diese Klassen den
Begriff **Core-Fault-Engine** oder **Fault-Engine**. Der alte Name
`*FaultAdapter` gilt als historische Benennung.

Ein spaeterer Umsetzungsslice darf die Klassen und Dateien umbenennen:

- `BatteryFaultAdapter` -> `BatteryFaultEngine`
- `GridFaultAdapter` -> `GridFaultEngine`
- `battery_fault_adapter.py` -> `battery_fault_engine.py`
- `grid_fault_adapter.py` -> `grid_fault_engine.py`

Wegen Repo-Regel erfolgt ein solcher Rename in zwei Schritten:

1. reiner `git mv`-/Symbol-Rename-Commit, soweit technisch sinnvoll,
2. danach Inhalts-/Doku-Rewrite.

### 2.3 Compatibility-Re-Exports sind erlaubt

Falls der Rename umgesetzt wird, duerfen fuer eine Uebergangsphase
Compatibility-Aliase im Paket-Interface bleiben:

```python
BatteryFaultAdapter = BatteryFaultEngine
GridFaultAdapter = GridFaultEngine
```

Diese Aliase muessen in Tests abgesichert und in einem Folge-Slice
wieder entfernt oder als dauerhaft historisches API markiert werden.
Kein Alias darf neue `grid_gym.adapters.*`-Imports erzeugen.

### 2.4 Move nach `adapters/driven/fault_*` nur bei neuer Boundary

Ein spaeterer Move nach `adapters/driven/fault_*` ist nur zulaessig,
wenn eine echte externe oder austauschbare Fault-Infrastruktur
eingefuehrt wird, z. B. ein remote Fault-Service, ein Plugin-System
mit externem Lifecycle oder ein Protokolladapter fuer Fault-Inputs.

Ein reiner Namenswunsch reicht nicht. In diesem Fall waere eine neue
ADR noetig, weil die Boundary und das `FaultPort`-Verstaendnis
fachlich geaendert wuerden.

## 3. Konsequenzen

Positive Konsequenzen:

- `AC-ADAPTER-PURE`-Rueckbau aus ADR 0050 bleibt fokussiert:
  HTTP-Adapter sehen `core.faults` nicht mehr, aber die Core-Fault-
  Logik muss nicht umziehen.
- Architektur und Code-Namen koennen wieder konsistenter werden.
- Die bestehende Welle-2-Entscheidung wird nicht still ueberschrieben,
  sondern additiv geschaerft.

Kosten und Risiken:

- Ein Rename beruehrt viele Tests, Doku-Referenzen und ADR-Index-
  Texte.
- Accepted ADRs werden nicht inhaltlich editiert; Doku-Drift wird ueber
  ADR 0051, README-/Plan-Sync und ggf. neue Code-Docstrings
  korrigiert.
- Compatibility-Aliase koennen laenger leben als geplant; der Slice
  braucht ein klares Removal- oder Dauerhaftigkeitskriterium.

## 4. Out-of-Scope

- Neue Fault-Typen.
- Neue Fault-Recovery-Semantik.
- Aenderung der `FaultPort.apply_active_faults(...)`-Signatur.
- Move nach `adapters/driven/fault_*` ohne neue externe Boundary.
- Direktes Umschreiben historischer Accepted-ADR-Texte.

## 5. Acceptance

ADR 0051 kann auf `Provisional` springen, sobald ein Umsetzungsslice
mindestens die Doku-/Code-Begriffsklaerung produktiv verankert und
`make docs-check` sowie die engsten Fault-Tests gruen sind.

`Accepted` ist sinnvoll, wenn entweder:

- die Rename-Entscheidung umgesetzt ist, oder
- bewusst entschieden wurde, die historischen Klassennamen dauerhaft
  beizubehalten und nur die Doku-Begriffsklaerung zu fuehren.
