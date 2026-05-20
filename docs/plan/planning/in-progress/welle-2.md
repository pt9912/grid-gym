# Welle 2 — Battery- und Grid-Fault-Konkretisierung

**Status:** In Progress — Slice-Begleit-Dokument angelegt (pre-C3; Closure wechselt auf `Done`)
2026-05-20. M3-Welle-2 baut auf der M3-Welle-1-Foundation
(`712d73b..46c7353`) auf: Welle 1 hat `FaultInjectableDevice`-
Sub-Protocol + `FaultPort`-Driven-Port + TickLoop-Hook +
Validator-Haertung geliefert; Welle 2 fuellt diese Schichten
mit konkreten Adapter-Implementierungen, Fault-Typen und
Recovery-Logik. Kanonische Slice-Spezifikation:
[`M3-faults-agents-observability.md §3 Welle 2`](M3-faults-agents-observability.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht Ersatz.

**Spec-Reife:** Inhaltlich final (ADR- und Architektur-
Entscheidungen aus Welle-1-Review M-3/M-4/M-5 beruecksichtigt).
**Umsetzungsstatus:** `In Progress` — Welle-Closure ersetzt die
finalen Commit-Hashes im Header und zieht den Slice auf `Done`.

## 1. Context

M3-Welle-1 hat die Fault-Foundation produktiv geliefert
(`46c7353` Endstand, 776 Unit-Tests, ADR 0022 `Provisional`):

- `FaultInjectableDevice(DeviceModel, Protocol)`-Sub-Protocol
  mit `inject_fault(fault_type, payload) -> None`.
- `FaultPort`-Driven-Port mit
  `apply_active_faults(devices, context) -> None` (Welle-1-
  Surface `Sequence[object]` wegen AC-PORTS-NO-OUT).
- TickLoop-Vor-Tick-Block-Schritt-A2 (Hook nach LoadEvent-
  Overlay, vor erster Device-Iteration).
- Scenario-Validator-Target-Existenz-Check
  (`ScenarioUnknownFaultTargetError`).

Was Welle 1 NICHT geliefert hat (Welle-2-Material):

- Konkrete `FaultInjectableDevice`-Implementer (BatteryDevice,
  GridConnectionDevice).
- Konkrete `FaultPort`-Adapter (`BatteryFaultAdapter`,
  `GridFaultAdapter`).
- Konkrete Fault-Typen (`cell_failure`, `voltage_drop`).
- Recovery-Logik (`auto-recover-after-N-ticks`,
  `manual-via-command`).
- End-to-End-Fault-Demo-Szenario.
- Property-Tests fuer Fault-Determinismus.

Welle 2 schliesst diese Liste vollstaendig ab. Welle-1-Review-
M-4 (Exception-Propagation-Contract) und M-5 (Fault-on-
GridConnection-Constraint, Voltage/Frequency only) sind bereits
in ADR 0022 §2.4 dokumentiert und steuern jetzt das Welle-2-
Adapter-Design.

## 2. Scope

**In Scope:**

1. **ADR 0025** (geplant) — Recovery-Pattern fuer Faults
   (`auto-recover-after-N-ticks` Default + `manual-via-command`
   alternativer Pfad) ALS Erweiterung zu ADR 0022 §2.4
   (Schaerfung ohne Supersedes, ADR 0011-Pattern).
   `manual-via-command` ist in dieser Welle konkretisiert:

   - Command-Intent: `manual-recover-fault`.
   - Payload: `fault_id` (string, Pflicht), `target_device_id`
     (string, Pflicht), optional `correlation_id` (string).
   - Semantik: Der Adapter setzt den Ziel-Fault im
     `(fault_id, target_device_id)`-State auf aufgelöst und räumt
     die aktiven Device-Flags auf.
   - Priorität: Ein gültiges `manual-recover-fault` setzt
     `auto-recover-after-N-ticks` im selben Tick sofort außer
     Kraft.
   - Fehlerfall: unbekannte IDs oder falscher Typ werfen
     typisierte `FaultPort*Error`-Subklassen.
   Status
   `Proposed` → `Provisional` mit Welle-2-Merge → `Accepted`
   mit M3-Welle-7-Closure.
2. **`BatteryDevice` implementiert `FaultInjectableDevice`** —
   neue `inject_fault(fault_type, payload)`-Methode, die fuer
   `fault_type="cell_failure"` einen `_cell_failure_active`-
   State setzt; Effekt in der naechsten `tick()`: reduzierter
   `max_discharge_kw` (Welle-2-Default: 50 % bzw. konfigurierbar
   via Payload).
3. **`GridConnectionDevice` implementiert `FaultInjectableDevice`** —
   neue `inject_fault(fault_type, payload)`-Methode fuer
   `fault_type="voltage_drop"`, mutiert
   `_pending_voltage_v`-State (NEU in Welle 2; Welle-1-Review-
   M-5 verbietet `_pending_power_kw`-Mutation). Effekt in
   `tick()`: reduzierte `voltage_v`-Telemetry; Auto-Schluss
   bleibt unberuehrt.
4. **`BatteryFaultAdapter`** unter
   `src/grid_gym/hexagon/core/faults/` mit
   - Konstruktor-Injection von `scenario.faults`-Liste +
     `RandomPort` (fuer eventuelle Stochastik in Welle-3+/M3).
   - `apply_active_faults(devices, context)` filtert via
     `isinstance(d, FaultInjectableDevice)` + `device_id`-
     Match + Welle-1-Aktivitaets-Window
     (`start_simulation_time <= now < start + duration_ms`).
   - Recovery-State pro `(fault_id, target_device_id)`-Paar:
     `auto-recover-after-N-ticks` setzt `_cell_failure_active
     = False` nach Window-Ende.
5. **`GridFaultAdapter`** unter
   `src/grid_gym/hexagon/core/faults/` mit identischem
   Pattern, aber spezialisiert auf `voltage_drop` →
   `GridConnectionDevice._pending_voltage_v`.
6. **Snapshot-Erweiterung** fuer BatteryDevice und
   GridConnectionDevice: neue Sub-Snapshot-Felder
   (`fault_state`-Block additiv). KEIN Snapshot-Schema-Bump
   v2 → v3 noetig (additiv im Sub-Snapshot, ADR 0015 §2.3
   ist explizit erweiterbar). ADR 0014/0017 Status-
   Verifikation: bleiben `Accepted`; Welle 2 schaerft ohne
   Supersede.
7. **End-to-End-Fault-Demo-Szenario**:
   `tests/integration/scenarios/fault_demo.yaml` mit MVP-
   Demo-Erweiterung — 2 Faults (1 Battery-cell_failure, 1
   Grid-voltage_drop) mit nicht-ueberlappenden Windows.
8. **Integrationstest** (`test_fault_demo_scenario.py`):
   - Determinismus-Lauf (zwei Runs mit gleichem Seed →
     byte-identische `TickResult.emitted_telemetry`, analog
     Welle-6c-Pattern).
   - Recovery-Test: Battery-`max_discharge_kw` waehrend
     Fault-Window halbiert, nach Window auf voll.
   - Grid-`voltage_v`-Mutation waehrend Fault-Window
     dokumentiert.
9. **Unit-Property-Tests** (Hypothesis):
   - Per-Fault-Determinismus pro Fault-Typ:
     - `cell_failure` (`fault_battery`) und
     - `voltage_drop` (`fault_grid`).
     (gleicher Seed + Fault-Sequenz → identische Telemetry).
   - Recovery-Window-Boundary-Pinning (half-open `[start, end)`,
     analog Welle-6b-LoadEvent-Pattern).
10. **`CRITICAL_COV_TARGETS`-Default** im Dockerfile um
    `src/grid_gym/hexagon/core/faults` und
    `src/grid_gym/hexagon/core/faults` erweitert
    (Welle-1-Stand-`core/faults` bleibt mit drin).

**Anti-Scope:**

- Weitere Fault-Typen (`overcurrent`, `temperature_runaway`,
  `island_mode_failure` aus `GG-FAULT-005..010`) — eigene
  Slices nach M3-Welle-7 oder M3-Folge-Slices.
- Multi-Fault-Concurrent-Application (zwei Faults gleichzeitig
  aufs selbe Device) — Welle 3 oder ADR-Folge.
- Fault-Telemetry-Export zu Observability (`MetricsPort`,
  `TracePort`) — Welle 5/6 (Observability-Sub-Bereich).
- Multi-Agent-Konsum von Fault-Events — Welle 3/4 (Multi-
  Agent-Sub-Bereich).
- Snapshot-Schema-Bump v2 → v3 — additive Sub-Snapshot-Felder
  reichen; v3-Bump bleibt M6 (`GG-PERSIST-*`).
- Fault-Persistenz ueber Lauf-Grenzen hinweg — Welle 5+/M6.
- UI-Visualisierung von Fault-Events — M5.

## 3. Architektur-Entscheidungen

Welle 2 bringt **eine neue ADR**: ADR 0025 (Fault-Recovery-
Pattern). Erweitert ADR 0022 §2.4 als Schaerfung-ohne-
Supersedes (ADR 0011-Pattern).

Status-Lifecycle ADR 0025:

- `Proposed` mit Welle-2-C1 (separater `docs(adr)`-Commit).
- `Provisional` mit Welle-2-C2-Merge (`feat(welle-2)`).
- `Accepted` mit M3-Welle-7-Closure.

**ADR-0014/0017-Verifikation**: Welle 2 erweitert BatteryDevice
und GridConnectionDevice **additiv** (neue `inject_fault`-
Methode, additive Sub-Snapshot-Felder). ADR 0014 (Battery-
Snapshot-Schema) und ADR 0017 (GridConnection-Pattern) bleiben
**unveraendert `Accepted`**; Welle-2-Aenderungen sind reine
Sub-Protocol-Erweiterungen (FaultInjectableDevice-Implementer-
Anschluss).

**C2-Umsetzungsgrenze**: Welle 2 implementiert in C2 ausschließlich
`auto-recover-after-N-ticks` und `manual-via-command` inklusive
Recovery-Window-Verhalten. `permanent` und Recovery-Telemetrie sind
nicht in Scope dieser Welle und verbleiben in Welle 3+/M6.

**Adapter-Placement** (entschieden in Welle 2, korrigiert in
Welle-2-Review-Folge H-1):
`BatteryFaultAdapter` und `GridFaultAdapter` leben unter
`src/grid_gym/hexagon/core/faults/`, NICHT unter
`src/grid_gym/adapters/driven/fault_*/` (wie im ersten Plan-
Entwurf vorgesehen). AC-ADAPTER-PURE (`pyproject.toml:317`)
verbietet `grid_gym.adapters` den Import von
`grid_gym.hexagon.core.faults` und `grid_gym.hexagon.core.devices`
— ein echter Adapter unter `adapters/driven/` koennte
`FaultInjectableDevice` + `DeviceModel` nicht typisieren. Die
„FaultAdapter"-Klassen sind Domain-Orchestrierung, kein
externer Adapter — `core/faults/` ist die korrekte Hexagon-
Schicht. Klassennamen behalten ihren `Adapter`-Suffix, weil
sie das `FaultPort`-Protocol implementieren (Adapter im Pattern-
Sinne).

**Welle-1-Review-Constraints** (aus Welle-1-Review M-3/M-4/M-5
in ADR 0022 §2.4 dokumentiert; Welle 2 erfuellt sie):

- **M-3 Type-Surface**: Welle-2-Adapter casten/filtern intern
  via `isinstance(d, FaultInjectableDevice)`. Port-Surface
  bleibt `Sequence[object]`. Welle-3+/M3-Welle-7 koennen ein
  `_DeviceIdentifiable`-Protocol unter `core/domain/`
  einfuehren (out-of-scope fuer Welle 2).
- **M-4 Exception-Propagation**: Welle-2-Adapter werfen
  typisierte `FaultPort*Error`-Subklassen (z. B.
  `FaultUnsupportedTypeError` fuer unbekannten `fault_type`).
  Aufrufer-Verantwortung; TickLoop wrappt nicht.
- **M-5 GridConnection-Constraint**: Welle-2-`GridFaultAdapter`
  mutiert ausschliesslich `_pending_voltage_v` (neu in Welle 2),
  NICHT `_pending_power_kw`. `_pending_voltage_v` wird vom
  Welle-6b-Auto-Schluss nicht beruehrt.

## 4. Liefer-Reihenfolge (5 Commits)

### C0 — `docs(plan)`: welle-2 Slice-Doc (Welle-Beginn)

Dieses Dokument als Welle-Start-Marker. Status: `In Progress`.
Kein Code. Plus `in-progress/README.md`-Sync:
- `welle-1.md`-Zeile entfernt (Datei jetzt in `done/`).
- `welle-2.md`-Zeile ergaenzt.

### C1 — `docs(adr)`: ADR 0025 Proposed

Neu: `docs/plan/adr/0025-fault-recovery-pattern.md` (~ 3500
Woerter, Pattern aus ADR 0022). Inhalt:

- **Status**: `Proposed` (Datum 2026-05-20).
- **§1 Kontext**: ADR 0022 §2.4 hat `recovery: str`-Feld
  durchgereicht, aber kein semantisches Verhalten gepinnt.
  Welle 2 braucht eine Recovery-Engine im FaultPort-Adapter.
- **§2 Entscheidung** (5 Sub-Sections):
  - §2.1 Recovery-Modi: `auto-recover-after-N-ticks` (Default)
    + `manual-via-command` (alternativer Pfad). `permanent`
    aus M3-Slice-Plan §3 Welle 1 wird zu Welle 3+ verschoben.
  - §2.2 Recovery-State im Adapter (nicht im Device): pro
    `(fault_id, target_device_id)`-Paar zaehlt der Adapter
    `remaining_ticks` herunter. Device kennt nur
    `_<fault_type>_active`-Flag, nicht die Zeit.
  - §2.3 Recovery-Window-Vertrag: half-open `[start, end)`
    analog Welle-6b-LoadEvent (ADR 0021 §2.5).
  - §2.4 `inject_fault(fault_type, payload)`-Idempotenz:
    wiederholte Aufrufe fuer denselben aktiven Fault sind
    No-Op (Adapter prueft `_<fault_type>_active` vor
    Re-Injection).
  - §2.5 Recovery-Telemetry: optional in Welle 5 (Observability-
    Anschluss) — Welle 2 emittiert NICHT.
- **§3 Begruendung**: warum State im Adapter (Sub-Slicing-
  Trennung: Device kapselt Physik, Adapter kapselt Scheduling);
  warum `permanent` zurueckgestellt (braucht ADR-Folge fuer
  Lauf-uebergreifende Persistenz, M6-Material).
- **§4 Reichweite**: In (Welle 2) — auto-recover-after-N-ticks
  + manual-via-command. Out (Welle 3+) — permanent,
  Multi-Fault, Recovery-Telemetry.
- **§5 Operative Artefakte**: Dateipfade analog Critical-Files.
- **§6 Konsequenzen**: BatteryDevice + GridConnectionDevice
  brauchen `_*_active`-Flag; Adapter brauchen Recovery-State.
- **§7 Nicht Gegenstand**: Multi-Fault-Concurrent (Welle 3+),
  Fault-Telemetry (Welle 5), Snapshot-Persistenz ueber Lauf
  hinaus (M6).

Plus `adr/README.md`-Zeile fuer ADR 0025 `Proposed`.

### C2 — `feat(welle-2)`: BatteryFault + GridFault + Adapter + Tests

**Code (neu):**

1. `src/grid_gym/hexagon/core/faults/__init__.py` +
   `battery_fault_adapter.py` —
   `BatteryFaultAdapter(FaultPort)` mit Recovery-Engine fuer
   `cell_failure`.
2. `src/grid_gym/hexagon/core/faults/__init__.py` +
   `grid_fault_adapter.py` —
   `GridFaultAdapter(FaultPort)` mit Recovery-Engine fuer
   `voltage_drop`.
3. `tests/integration/scenarios/fault_demo.yaml` — End-to-End-
   Demo mit 2 Faults.

**Code (edit):**

4. `src/grid_gym/hexagon/core/devices/battery/model.py` +
   `snapshot.py` — `BatteryDevice.inject_fault(fault_type,
   payload)` + `_cell_failure_active`-State + Snapshot-Feld
   `fault_state.cell_failure_active: bool`.
5. `src/grid_gym/hexagon/core/devices/grid_connection/model.py`
   + `snapshot.py` — `GridConnectionDevice.inject_fault(...)`
   + `_pending_voltage_v`-State + Snapshot-Feld
   `fault_state.voltage_drop_active: bool`.
6. `src/grid_gym/hexagon/core/errors.py` — typed
   `FaultUnsupportedTypeError(GridGymError)` +
   `FaultInvalidPayloadError(GridGymError)` (analog
   Welle-1-Pattern).
7. `Dockerfile` — `CRITICAL_COV_TARGETS`-Default bleibt
   unveraendert (`hexagon/core/faults` ist seit Welle 1 drin;
   Adapter-Code lebt in `core/faults/`, NICHT unter
   `adapters/driven/`, weil AC-ADAPTER-PURE den Import von
   `core.faults`/`core.devices` aus `grid_gym.adapters` verbietet).

**Tests (neu):**

8. `tests/unit/hexagon/core/faults/__init__.py` +
   `test_adapter.py` — Adapter-Verhalten + Recovery-Engine.
9. `tests/unit/hexagon/core/faults/__init__.py` +
   `test_adapter.py` — analog.
10. `tests/unit/hexagon/core/devices/battery/test_fault_injection.py`
    — BatteryDevice.inject_fault-Vertrag + Snapshot-Roundtrip
    mit `_cell_failure_active`-State.
11. `tests/unit/hexagon/core/devices/grid_connection/test_fault_injection.py`
    — analog.
12. `tests/unit/hexagon/core/faults/test_recovery_window.py` —
    Welle-6b-LoadEvent-Boundary-Pattern fuer Recovery
    (half-open `[start, end)`).
13. `tests/unit/hexagon/core/faults/test_manual_recovery.py` —
    `manual-recover-fault`-Contract (Payload-Validierung, Idempotenz,
    Priorisierung gegenüber Auto-Recovery).
14. `tests/integration/test_fault_demo_scenario.py` (3 Tests):
    - Determinismus-Vergleich (zwei Runs, byte-identische
      Telemetry).
    - Battery-`max_discharge_kw` waehrend Fault-Window
      halbiert, nach Window auf voll (Recovery).
    - Grid-`voltage_v`-Mutation waehrend Fault-Window
      (Voltage faellt; `power_kw` bleibt durch Auto-Schluss
      gesteuert).

**Tests (Hypothesis-Property):**

15. `tests/unit/hexagon/core/faults/test_determinism.py`
    — `cell_failure`-Pfad; gleicher Seed + Fault-Sequenz → byte-
    identische Telemetry (Pattern aus M2-Welle-6c, ADR 0021 §2.9).
16. `tests/unit/hexagon/core/faults/test_determinism.py`
    — `voltage_drop`-Pfad; gleicher Seed + Fault-Sequenz → byte-
    identische Telemetry (Pattern aus M2-Welle-6c, ADR 0021 §2.9).

### C3 — `docs(plan)`: Welle-2 Status/DoD-Sync

- `docs/plan/adr/0025-fault-recovery-pattern.md` —
  `Proposed → Provisional` mit Welle-2-Merge-Hash (C2).
- `docs/plan/adr/README.md` — ADR 0025 auf `Provisional`.
- `docs/plan/planning/in-progress/M3-faults-agents-observability.md`
  — §0 Status: „Welle 2 abgeschlossen am 2026-05-20" mit
  Welle-2-Commit-Stack; §3 Welle 2 mit `Done`-Tag + Commit-
  Refs; „Naechster Schritt: Welle 3 (Multi-Agent-Foundation)".
- `docs/plan/planning/in-progress/welle-2.md` (dieses Dokument)
  — auf `Done` nach C3-Closure.

## 5. Critical Files

| Pfad                                                                | Commit  | Aktion |
| ------------------------------------------------------------------- | ------- | ------ |
| `docs/plan/planning/in-progress/welle-1.md` → `done/welle-1.md`     | Pre-C0  | git mv (rename-only, `0ecc773`) |
| `docs/plan/planning/in-progress/welle-2.md`                         | C0      | NEU (dieses Dokument) |
| `docs/plan/planning/in-progress/README.md`                          | C0      | EDIT (welle-1→welle-2) |
| `docs/plan/adr/0025-fault-recovery-pattern.md`                      | C1      | NEU |
| `docs/plan/adr/README.md`                                           | C1      | EDIT (ADR 0025 Zeile) |
| `src/grid_gym/hexagon/core/errors.py`                               | C2      | EDIT (`FaultUnsupportedTypeError`, `FaultInvalidPayloadError`) |
| `src/grid_gym/hexagon/core/devices/battery/model.py`                | C2      | EDIT (`inject_fault` + `_cell_failure_active`) |
| `src/grid_gym/hexagon/core/devices/battery/snapshot.py`             | C2      | EDIT (`fault_state`-Block additiv) |
| `src/grid_gym/hexagon/core/devices/grid_connection/model.py`        | C2      | EDIT (`inject_fault` + `_pending_voltage_v`) |
| `src/grid_gym/hexagon/core/devices/grid_connection/snapshot.py`     | C2      | EDIT (`fault_state`-Block additiv) |
| `src/grid_gym/hexagon/core/faults/__init__.py`            | C2      | NEU |
| `src/grid_gym/hexagon/core/faults/battery_fault_adapter.py` | C2    | NEU |
| `src/grid_gym/hexagon/core/faults/__init__.py`               | C2      | NEU |
| `src/grid_gym/hexagon/core/faults/grid_fault_adapter.py`     | C2      | NEU |
| `tests/integration/scenarios/fault_demo.yaml`                       | C2      | NEU |
| `tests/unit/hexagon/core/faults/__init__.py`              | C2      | NEU |
| `tests/unit/hexagon/core/faults/test_adapter.py`          | C2      | NEU |
| `tests/unit/hexagon/core/faults/test_determinism.py`      | C2      | NEU |
| `tests/unit/hexagon/core/faults/test_determinism.py`         | C2      | NEU |
| `tests/unit/hexagon/core/faults/__init__.py`                 | C2      | NEU |
| `tests/unit/hexagon/core/faults/test_adapter.py`             | C2      | NEU |
| `tests/unit/hexagon/core/devices/battery/test_fault_injection.py`   | C2      | NEU |
| `tests/unit/hexagon/core/devices/grid_connection/test_fault_injection.py` | C2 | NEU |
| `tests/unit/hexagon/core/faults/test_recovery_window.py`            | C2      | NEU |
| `tests/unit/hexagon/core/faults/test_manual_recovery.py`             | C2      | NEU |
| `tests/integration/test_fault_demo_scenario.py`                     | C2      | NEU |
| `Dockerfile`                                                        | C2      | EDIT (`CRITICAL_COV_TARGETS` + 2 Adapter-Pfade) |
| `docs/plan/adr/0025-fault-recovery-pattern.md`                      | C3      | EDIT (Status → Provisional) |
| `docs/plan/adr/README.md`                                           | C3      | EDIT (Status → Provisional) |
| `docs/plan/planning/in-progress/M3-faults-agents-observability.md`  | C3      | EDIT (§0 + §3 Welle 2 Closure) |
| `docs/plan/planning/in-progress/welle-2.md`                         | C3      | EDIT (Status → Done) |

## 6. Verifikationspfad

End-to-End ueber `make`-Targets (Dockerfile-Stages, Docker-only
nach Repo-Konvention):

1. **`make test-unit`** — gruen mit ~16–21 neuen Tests
   (Adapter-Verhalten, Device-Inject, Snapshot-Roundtrip,
   Recovery-Window, Determinismus-Property). Test-Count steigt
   von 776 auf ~792–797.
2. **`make test-integration`** — gruen mit
   `test_fault_demo_scenario.py` (3 Tests): Determinismus,
   Battery-Recovery, Grid-Voltage-Mutation. Total: 9 + 3 = 12
   Integration-Tests.
3. **`make gates`** — gruen ohne Override;
   `CRITICAL_COV_TARGETS`-Default um zwei Adapter-Pfade
   erweitert; Coverage ≥ 90 % Line + Branch auf neuen
   Modulen.
4. **`make fullbuild`** — gruen ohne Override (M3-Welle-2-
   Welle-Gate aus M3-Slice-Plan §3: `make test-integration`
   mit `fault_demo.yaml`).
5. **ADR-0025-Status sichtbar `Provisional`** nach C3.
6. **ADR-0014/0017-Status unveraendert `Accepted`** (Welle 2
   schaerft additiv; keine Status-Aenderung).
7. **Rename-Historie**: `git log --follow done/welle-1.md`
   traceable ueber Pre-C0-Rename (`0ecc773`).
8. **Git-Pattern**: 5 neue Welle-2-Commits in der Reihenfolge
   `chore(welle-2): git mv (Pre-C0)` → `docs(plan): welle-2
   Slice-Doc (C0)` → `docs(adr): ADR 0025 Proposed (C1)` →
   `feat(welle-2): ... (C2)` → `docs(plan): Welle-2 Status/DoD-
   Sync (C3)`. `git log --oneline -5` zeigt diese fuenf Hashes.

## 7. Risiken

- **Snapshot-Schema-Bump-Versuchung**: BatteryDevice +
  GridConnectionDevice erweitern ihre Sub-Snapshots additiv
  (neuer `fault_state`-Block). ADR 0015 §2.3 erlaubt das
  explizit, KEIN v2 → v3 Bump noetig. *Mitigation*: Welle-2-
  Implementer prueft, dass `from_snapshot(snapshot()) ==
  device` byte-stabil bleibt (alte Snapshots ohne `fault_state`
  duerfen weiter lesbar sein — `_cell_failure_active = False`-
  Default). Falls Welle-2-Implementer doch einen Schema-Bump
  braucht, **STOP** und ADR-Folge zu ADR 0015 schreiben.
- **GridConnection-`_pending_voltage_v`-Neufeld**: Welle 6a
  hat GridConnection ohne Voltage-State geliefert (nur
  `import_kwh`/`export_kwh`). Welle 2 fuegt
  `_pending_voltage_v` hinzu — additiv, aber TICK-Loop-relevant
  (Telemetry-`voltage_v` muss in jedem Tick emittiert werden,
  nicht nur bei Fault). *Mitigation*: Default-Wert ist
  `nominal_voltage_v` aus `GridConnectionConfig`; Fault mutiert
  das Pending-Feld; TickLoop committed das Pending-Feld im
  `tick()`-Schritt analog `_pending_power_kw`.
- **Sub-Slicing-Schwelle**: Welle 2 hat 10 In-Scope-Items
  + 2 Devices + 2 Adapter + ADR 0025. Liegt knapp UEBER der
  M3-Slice-Plan-§3-Schwelle (> 6 Items mit ≥ 2 echte
  Architektur-Entscheidungen — ADR 0025 + Voltage-State).
  *Fallback*: Welle 2 splittet in 2a (BatteryFault +
  Recovery-Engine) und 2b (GridFault + Voltage-State +
  Integrationstest). Wird erst entschieden, wenn C2 die
  Sub-Slicing-Schwelle ueberschreitet.
- **Recovery-Engine in Adapter vs. in Device**: Welle 2 packt
  die Recovery-Logik in den Adapter (ADR 0025 §2.2). Wenn
  spaeter ein Fault-Typ persistierte Recovery braucht
  (z. B. `cell_failure` mit Hardware-Reset-Trigger), muesste
  der Device-State erweitert werden. *Mitigation*: ADR 0025 §4
  haelt das explizit als Out-of-Scope; M6 `GG-PERSIST-*`
  entscheidet.
- **Welle-1-Review-M-5-Hammer**: Welle 2 muss zwingend
  Voltage-State (nicht Power-Flow) mutieren fuer GridFault.
  *Mitigation*: ADR 0025 §3 Begruendung referenziert ADR 0022
  §2.4 explizit; Code-Review-Checkliste enthaelt einen
  expliziten Punkt „GridFaultAdapter darf `_pending_power_kw`
  NICHT mutieren".

## 8. Wandert nach

- `done/welle-2.md` mit M3-Welle-3-Start als Pre-C0 reiner-
  Rename-Commit (analog Welle-0 → done/ in M3-Welle-1-Pre-C0
  `712d73b`; analog Welle-1 → done/ in M3-Welle-2-Pre-C0
  `0ecc773`). Memory-Konvention `feedback_git_mv` strikt.
