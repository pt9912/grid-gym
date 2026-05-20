# ADR 0025 — Fault-Recovery-Pattern (M3 Welle 2)

**Status:** Proposed — Welle-2-Erstwurf, geplant mit
M3-Welle-2-Merge auf `Provisional` zu heben (Pattern aus
ADR 0021/ADR 0022). Akzeptanz mit M3-Welle-7-Closure
(gemeinsam mit ADR 0023 Multi-Agent + ADR 0024 Observability
oder einzeln, je nach Welle-7-Closure-Sequenzierung).
**Datum:** 2026-05-20
**Status geaendert am:** (noch keine Status-Wechsel — `Proposed`
ist initial)
**Bezug:**
[`ADR 0022`](0022-fault-injection-protocol.md) §2.4
(Fault-Injection-Hook im Vor-Tick-Block + Exception-
Propagation-Vertrag + GridConnection-Voltage/Frequency-Only-
Constraint — Welle 2 erfuellt alle drei Welle-1-Review-M-3/4/5-
Constraints; ADR 0025 schaerft §2.4 um die Recovery-Engine
ohne Supersede),
[`ADR 0022`](0022-fault-injection-protocol.md) §2.1
(`FaultInjectableDevice(DeviceModel)`-Sub-Protocol mit
`inject_fault(fault_type, payload) -> None` — Welle-2-
Implementer setzen Device-State-Flags, Adapter zaehlt
Recovery-Ticks),
[`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
§2.5 (LoadEvent-Half-Open-Window-Pattern — Recovery-Window
spiegelt das gleiche `[start, end)`-Verhalten),
[`ADR 0014`](0014-battery-snapshot-schema.md) +
[`ADR 0017`](0017-grid-connection-device-pattern.md)
(Battery- + GridConnection-Snapshot-Patterns; Welle 2 erweitert
beide additiv um einen `fault_state`-Block ohne v2→v3-Bump),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md)
(Erweiterungs-ADR-Pattern — diese ADR erweitert ADR 0022 §2.4
um Recovery-Semantik, kein Supersedes).
M3-Slice-Plan
[`in-progress/M3-faults-agents-observability.md`](../planning/in-progress/M3-faults-agents-observability.md)
§3 Welle 2.
Lastenheft §14 Fault Injection (`GG-FAULT-001..010`;
insbesondere die Recovery-Pflicht aus
`GG-FAULT-003`/`004`/`005`).

---

## 1. Kontext

M3-Welle-1 (`46c7353` Endstand) hat die Fault-Foundation
geliefert. ADR 0022 §2.4 hat das `recovery: str`-Feld aus
`ScenarioFault` durchgereicht, aber **kein** semantisches
Verhalten gepinnt. Welle 2 muss diese Luecke schliessen, damit
`BatteryFaultAdapter` + `GridFaultAdapter` wissen, wann ein
aktiver Fault zurueckzunehmen ist.

Drei Beobachtungen aus dem Welle-1-Stand:

**Beobachtung 1 — `recovery`-Feld ist heute unspezifiziert.**
`ScenarioFault.recovery: str`
(`src/grid_gym/hexagon/core/domain/scenario.py:113`) ist
syntaktisch validiert (`_assert_str` im Welle-5-Validator),
aber der Wertebereich ist offen. M3-Slice-Plan
§3 Welle 1 hat drei Modi vorgeschlagen
(`auto-recover-after-N-ticks` / `manual-via-command` /
`permanent`), aber keine Spezifikation. Welle 2 muss
mindestens zwei davon implementieren (per M3-Slice-Plan
§3 Welle 2 DoD-Item 3).

**Beobachtung 2 — `permanent` braucht Lauf-uebergreifende
Persistenz, die heute nicht existiert.** Ein `permanent`-Fault
muesste durch Snapshot/Resume hindurch persistieren. M6-Slice
(`GG-PERSIST-*`) ist dafuer das richtige Welle-Material;
Welle 2 verschiebt `permanent` daher in Welle 3+/M6.

**Beobachtung 3 — Recovery-State-Lokalisation ist
Architektur-Entscheidung.** Zwei Plausible Varianten:

1. State im Device (`BatteryDevice._cell_failure_remaining_ticks: int`).
2. State im Adapter (`BatteryFaultAdapter._active_faults: dict[(fault_id, target_id), int]`).

Welle 2 entscheidet sich fuer Variante 2 (siehe §2.2): Device
kapselt **Physik** (Flag + Effekt), Adapter kapselt
**Scheduling** (wann ist der Fault aktiv? wann recovern?).
Trennt die Verantwortlichkeiten sauber.

---

## 2. Entscheidung

ADR 0025 fixiert fuenf Punkte:

### 2.1 Recovery-Modi: zwei in Welle 2 produktiv

**Welle-2-In-Scope** (`recovery`-Feld-Werte):

- **`auto-recover-after-N-ticks`** (Default): N ist die
  `duration_ms / tick_ms`-abgeleitete Tick-Anzahl
  (siehe §2.3 fuer Window-Vertrag). Nach Window-Ende setzt
  der Adapter den Device-`_<fault_type>_active`-Flag auf
  `False`.
- **`manual-via-command`**: der Fault ist aktiv vom
  `start_simulation_time` bis zu einem expliziten Command,
  der den Recovery ausloest. Welle 2 fixiert das
  Command-Format als Bestandteil von ADR 0025:

  - **Command-Intent**: `manual-recover-fault`.
  - **Payload-Pflicht-Felder**:
    - `fault_id` (string): Identifier aus
      `scenario.faults[i]` (Welle-2-Konvention: implizit
      `f"fault-{i}"` bei nicht gesetztem expliziten Feld;
      M3-Welle-3 kann ein optionales `fault.id`-Feld
      hinzufuegen).
    - `target_device_id` (string): muss zum Fault-Target
      passen (Adapter prueft Konsistenz).
  - **Payload-Optional-Felder**:
    - `correlation_id` (string): fuer Observability-
      Korrelation in Welle 5/6.
  - **Semantik**: Adapter setzt
    `(fault_id, target_device_id)`-State auf „aufgeloest"
    und ruft `device.inject_fault(fault_type, payload)` mit
    einer „recover"-Markierung NICHT — stattdessen mutiert
    der Adapter den `_<fault_type>_active`-Flag direkt ueber
    eine private Device-Methode oder ueber einen weiteren
    `inject_fault`-Aufruf mit speziellem Payload-Marker.
    Welle 2 implementiert die direkt-Mutation-Variante
    (Device exponiert `_clear_<fault_type>`-Helper).
  - **Prioritaet**: ein gueltiges `manual-recover-fault`
    setzt `auto-recover-after-N-ticks` im selben Tick sofort
    ausser Kraft (Manual-Override schlaegt Auto-Schedule).
  - **Fehlerfall**: unbekannter `fault_id` oder
    `target_device_id` → typisierter
    `FaultUnknownReferenceError`; Type-Mismatch in Payload
    → `FaultInvalidPayloadError`. Beide propagieren
    ungewrappt aus `TickLoop.tick()` (ADR 0022 §2.4 Exception-
    Propagation-Vertrag).

**Welle-2-Out-of-Scope** (verschoben):

- **`permanent`** (aus M3-Slice-Plan §3 Welle 1): braucht
  Lauf-uebergreifende Persistenz. Verschoben auf Welle 3+
  (mit AgentBus-ADR 0023) oder M6 (mit `GG-PERSIST-*`-
  Migration).

### 2.2 Recovery-State im Adapter, nicht im Device

**State-Lokalisation**:

- **Device** (`BatteryDevice`, `GridConnectionDevice`)
  haelt **nur** einen Boolean-Flag pro Fault-Typ:
  - `BatteryDevice._cell_failure_active: bool`
  - `GridConnectionDevice._voltage_drop_active: bool`
  Plus die Effekt-Felder, die durch den Flag gesteuert werden
  (z. B. Battery-`max_discharge_kw` reduziert; Grid-
  `_pending_voltage_v` mutiert).
- **Adapter** (`BatteryFaultAdapter`, `GridFaultAdapter`)
  haelt das **Scheduling**:
  - `_active_faults: dict[tuple[str, str], int]` mit Key
    `(fault_id, target_device_id)` und Wert
    `remaining_ticks` (fuer `auto-recover-after-N-ticks`).
  - `_pending_recoveries: set[tuple[str, str]]` fuer
    `manual-via-command` (wenn der Command kommt, wird der
    Key entfernt + Device-Flag geclearched).

**Begruendung**:

- Device-State bleibt **physik-getrieben** (Sub-Snapshot
  Pflichten + Roundtrip-Vertrag aus ADR 0014/0017 bleiben
  einfach: ein Boolean-Feld dazu, kein Counter).
- Adapter-State ist **scheduling-getrieben** und kann sich in
  Welle 3+ aendern (z. B. Recovery-Telemetry-Emit), ohne den
  Device-Snapshot-Vertrag zu brechen.
- Trennt Verantwortlichkeiten sauber: Device weiss, wie der
  Fault wirkt (Physik); Adapter weiss, wann der Fault aktiv
  ist (Time).

**Snapshot-Konsequenz**: Battery- und GridConnection-
Sub-Snapshots erweitern sich additiv um einen
`fault_state`-Block mit den Boolean-Flags. ADR 0015 §2.3
(Sub-Snapshot-Mapping ist erweiterbar) erlaubt das ohne
v2 → v3-Bump. Adapter-State (Counter, Pending-Sets) ist
**nicht** persistiert in Welle 2 — Resume-Verhalten ueber
Lauf-Grenzen hinweg ist M6-Material.

### 2.3 Recovery-Window-Vertrag (half-open `[start, end)`)

Spiegelt das Welle-6b-LoadEvent-Pattern aus
[`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
§2.5:

- **Start-Inklusiv**: Bei `context.simulation_time ==
  fault.start_simulation_time` ist der Fault aktiv.
- **End-Exklusiv**: Bei `context.simulation_time ==
  fault.start_simulation_time + fault.duration_ms` ist der
  Fault NICHT mehr aktiv (Recovery hat im vorherigen Tick
  stattgefunden).
- **Tick-Step-Alignment**: das Window-Ende fallt im
  TickLoop-Vor-Tick-Block-Schritt-A2 (ADR 0022 §2.4) auf die
  exakte Recovery-Tick. Der Adapter:
  1. Prueft `now >= start_simulation_time + duration_ms`.
  2. Falls ja, ruft Device-`_clear_<fault_type>`-Helper.
  3. Entfernt den Eintrag aus `_active_faults`.

**Boundary-Tests** (in C2 Property-Tests):
- `now == start_simulation_time`: aktiv.
- `now == start_simulation_time + duration_ms - tick_ms`:
  letzte aktive Tick.
- `now == start_simulation_time + duration_ms`: erste
  inaktive Tick (Recovery).

### 2.4 `inject_fault`-Idempotenz

Wiederholte Aufrufe von `device.inject_fault(fault_type,
payload)` fuer denselben aktiven Fault sind **No-Op**.
Adapter prueft `_<fault_type>_active` vor Re-Injection und
ruft `inject_fault` nur beim **Uebergang** `inactive → active`.

**Begruendung**: TickLoop ruft den Adapter pro Tick einmal;
ohne Idempotenz wuerde der Device-Effekt jeden Tick
wiederholt angewandt (z. B. `max_discharge_kw` mehrfach
halbiert). Idempotenz haelt den Effekt stabil ueber das
Window.

**Adapter-Pflicht** (Welle 2): bei `apply_active_faults(...)`
- pro Fault pruefen: ist `(fault_id, target_device_id)` neu
  aktiv geworden? → einmal `inject_fault`.
- ist der Fault nicht mehr aktiv (Window vorbei oder
  manueller Recovery)? → `_clear_<fault_type>`.
- ist der Fault unveraendert aktiv? → No-Op (Skip-Aufruf
  auf das Device).

### 2.5 Recovery-Telemetry: nicht in Welle 2

Welle 2 emittiert **keine** Recovery-spezifische Telemetry
(weder „Fault aktiv" noch „Fault recovered"). Die Telemetry-
Mutation des Devices selbst (z. B. Battery-Telemetry zeigt
gedrosselten `discharge_kw`-Wert) ist beobachtbar, aber kein
eigener `Fault.event`-Stream.

**Begruendung**: Welle 5/6 liefert
`LogPort`/`MetricsPort`/`TracePort` (ADR 0024); Fault-
Telemetry passt dort hinein. Welle-2-Eintrag in die
Telemetry-Surface waere ein Vorgriff auf Observability-
Architektur, die noch nicht entschieden ist.

**Konsequenz fuer Welle 5/6**: AgentBus + Observability
koennen `FaultPort`-Adapter erweitern (z. B. via
Decorator-Pattern) oder eine eigene Telemetry-Pipeline
anhaengen. Welle-2-Adapter ist dafuer offen (keine
versiegelte API).

---

## 3. Begründung

**State im Adapter vs. im Device** (gewaehlt: Adapter):

Drei Architektur-Optionen:

1. **State im Device** (`Battery._cell_failure_remaining_ticks: int`):
   Device weiss, wann es recovert. *Vorteil*: einzige State-
   Source, Snapshot-Pflicht klar. *Nachteil*: Device-Modell
   wird scheduling-bewusst — Vermischung von Physik und
   Time-Logik. Refactoring in Welle 3+ wuerde Devices
   beruehren (z. B. fuer Multi-Fault-Support).
2. **State gespalten** (Device traegt Flag, Adapter traegt
   Counter): `Battery._cell_failure_active: bool` +
   `BatteryFaultAdapter._remaining_ticks: int`. *Vorteil*:
   Separation of Concerns. *Nachteil*: Resume ueber Lauf-
   Grenzen wuerde beide State-Quellen koordinieren muessen
   (M6-Material; jetzt out-of-scope).
3. **State komplett im Adapter** (`Battery` ist stateless
   bezueglich `cell_failure`): Adapter haelt sowohl Flag als
   auch Counter; Device hat keine `_cell_failure_active`-
   Variable. *Nachteil*: Device-`tick()` muss bei jedem
   Aufruf den Adapter fragen „bin ich gerade gefaultet?" —
   Inversion of Control, bricht die Welle-6a-Vorbedingungs-
   Trennung (Devices sind autark im `tick()`-Pfad).

Welle 2 waehlt Variante 2 (gespalten): Device-Flag fuer
Physik + Snapshot-Roundtrip; Adapter-Counter fuer
Scheduling. Snapshot-Pflicht bleibt einfach (Boolean
additiv); Adapter-State ist out-of-snapshot in Welle 2
(siehe §2.5 + §6 Konsequenzen).

**`permanent` zurueckgestellt**:

Ein `permanent`-Fault muesste durch `from_snapshot(...)`
hindurch persistieren, damit Resume-Lauf den Fault wieder
aktiviert. Welle-2-Snapshot-Erweiterung (Boolean-Flag im
Sub-Snapshot) reicht dafuer **technisch** aus, aber:

- Die `(fault_id, target_device_id)`-Korrelation zwischen
  Scenario-File und Snapshot ist nicht trivial (Scenario-
  File aendert sich nicht im Snapshot; die Frage „welcher
  Fault aus dem aktuellen Scenario ist im Snapshot-Stand
  noch aktiv?" braucht eine Resume-Strategie).
- Fault-IDs sind heute implizit (`f"fault-{i}"` aus der
  Liste); Resume mit anderem Scenario-File ist undefiniert.

M6 `GG-PERSIST-*` wird beides loesen (Snapshot-Migration +
Fault-ID-Konvention). Welle 2 verschiebt `permanent`
absichtlich dorthin.

**Half-open Recovery-Window**:

Welle-6b-LoadEvent (ADR 0021 §2.5) hat das `[start, end)`-
Pattern etabliert. ADR 0025 spiegelt es identisch — Konsistenz
und Tick-Step-Alignment sind in beiden Faellen wichtig.
Closed-Inclusive (`[start, end]`) wuerde einen Off-By-One-
Tick produzieren, dessen Debug-Aufwand kein Welle-2-Item
rechtfertigt.

---

## 4. Reichweite

**In Scope (Welle 2):**

- `auto-recover-after-N-ticks` Recovery-Modus.
- `manual-via-command` Recovery-Modus inkl. Command-Format-
  Definition.
- `inject_fault`-Idempotenz-Vertrag (Adapter-Pflicht).
- Recovery-State-Lokalisation (Adapter haelt Scheduling;
  Device haelt Boolean-Flag).
- Snapshot-Erweiterung Battery + GridConnection um
  `fault_state`-Block (additiv).
- Typisierte Fehler-Klassen `FaultUnsupportedTypeError`,
  `FaultInvalidPayloadError`, `FaultUnknownReferenceError`.

**Out of Scope (Welle 3+):**

- `permanent`-Recovery-Modus (Welle 3+ oder M6).
- Multi-Fault-Concurrent auf demselben Device (Welle 3
  oder ADR-Folge zu ADR 0025).
- Recovery-Telemetry (Welle 5/6 Observability).
- Adapter-State-Persistenz (M6 `GG-PERSIST-*`).
- Cross-Device-Fault-Cascades (z. B. „Battery-cell_failure
  triggert auch GridConnection-voltage_drop") — out-of-scope
  ueber Welle 7.

---

## 5. Operative Artefakte

| Pfad                                                                | Aktion |
| ------------------------------------------------------------------- | ------ |
| `src/grid_gym/hexagon/core/devices/battery/model.py`                | EDIT (`inject_fault` + `_clear_cell_failure` + `_cell_failure_active`-State) |
| `src/grid_gym/hexagon/core/devices/battery/snapshot.py`             | EDIT (`fault_state`-Block) |
| `src/grid_gym/hexagon/core/devices/grid_connection/model.py`        | EDIT (`inject_fault` + `_clear_voltage_drop` + `_pending_voltage_v`) |
| `src/grid_gym/hexagon/core/devices/grid_connection/snapshot.py`     | EDIT (`fault_state`-Block) |
| `src/grid_gym/adapters/driven/fault_battery/battery_fault_adapter.py` | NEU (Recovery-Engine + Idempotenz) |
| `src/grid_gym/adapters/driven/fault_grid/grid_fault_adapter.py`     | NEU (Recovery-Engine + Idempotenz) |
| `src/grid_gym/hexagon/core/errors.py`                               | EDIT (`FaultUnsupportedTypeError`, `FaultInvalidPayloadError`, `FaultUnknownReferenceError`) |

ADR-Cross-Refs (read-only fuer Welle 2):
- ADR 0022 §2.4 (Exception-Propagation + GridConnection-
  Constraint) wird vom Welle-2-Code respektiert.
- ADR 0014/0017 bleiben `Accepted` (additiv erweitert ueber
  Sub-Snapshot).

---

## 6. Konsequenzen

**Positive Konsequenzen:**

- BatteryDevice + GridConnectionDevice bleiben snapshot-
  roundtrip-faehig mit einem einzigen zusaetzlichen Boolean
  pro Fault-Typ.
- Adapter haelt die Scheduling-Logik isoliert; Welle 3/4/5+
  koennen den Adapter durch Decorator-Pattern erweitern.
- `manual-via-command` ist konkret genug, dass Welle 3
  (Multi-Agent) direkt Recovery-Commands ausloesen kann.

**Verbindliche Konsequenzen fuer Welle 2-C2:**

- Battery-Snapshot v2 (additive `fault_state.cell_failure_active`)
  muss roundtrip-stabil sein (Welle-1-Pattern aus ADR 0013 §2.4).
- GridConnection-Snapshot v2 (additive
  `fault_state.voltage_drop_active`) ebenso, plus
  `_pending_voltage_v` und `_current_voltage_v` als Welle-2-
  Neufelder (Default = `nominal_voltage_v` aus Config).
- Adapter-Konstruktor-Signatur:
  `BatteryFaultAdapter(faults: tuple[ScenarioFault, ...],
   random: RandomPort)` — Scenario-Loader-Integration
  ist Welle-3-Material (heute manuelle Test-Konstruktion).

**Welle-3-/4-Forward-Pointer:**

- Multi-Agent-Bus (ADR 0023) konsumiert
  `manual-recover-fault`-Commands ueber den Standard-Command-
  Pfad.
- Observability (ADR 0024) emittiert Recovery-Events ueber
  MetricsPort/TracePort.

**Pflege-Gleichheit:**

- `_DEVICE_FACTORIES` (Scenario-Loader,
  `loader.py:59-65`) ist unveraendert — Fault-Adapter sind
  nicht ueber Loader-Factory dispatched.
- `_DEVICE_TYPE_BY_CLASS_NAME` (TickLoop,
  `tick_loop.py:115-121`) unveraendert.

---

## 7. Nicht Gegenstand

**`permanent`-Recovery-Modus** — Welle 3+/M6 (siehe §3
Begruendung).

**Multi-Fault-Concurrent** (zwei Faults gleichzeitig auf
demselben Device, z. B. `cell_failure` + `temperature_runaway`)
— Welle 3 oder ADR-Folge zu ADR 0025.

**Recovery-Telemetry** (`MetricsPort.observe(fault_recovered,
labels)`) — Welle 5/6 mit ADR 0024.

**Adapter-State-Persistenz** (Resume-Verhalten ueber
Snapshot-Boundary) — M6 `GG-PERSIST-*`.

**Cross-Device-Fault-Cascades** (Battery-Fault triggert
Grid-Fault) — out-of-scope ueber Welle 7.

**Property-Test-Permutation fuer Multi-Fault-Ordering** —
Welle 2 testet nur Single-Fault-Determinismus pro Fault-Typ;
Permutation kommt mit Multi-Fault in Welle 3+.

**M4-Protokolladapter** (Fault-Trigger ueber Modbus/OPC-UA) —
M4.

**SOLLTE-Geraete-Faults** (EV-Charger, Transformer, Wind,
Diesel) — eigene Slices nach M3-Closure
(Open-Triggers `016..019`).
