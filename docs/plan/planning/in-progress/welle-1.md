# Welle 1 — Fault-Foundation: FaultPort + FaultInjectableDevice + Scenario-Validator-Härtung + TickLoop-Hook

**Status:** In Progress — Slice-Begleit-Dokument angelegt
2026-05-20. M3-Welle-1 ist die erste Code-Welle in M3; baut auf
der M3-Welle-0-Slice-Plan-Eroeffnung (`cfb7a72..3e6170d`) auf.
Kanonische Slice-Spezifikation:
[`M3-faults-agents-observability.md §3 Welle 1`](M3-faults-agents-observability.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht Ersatz.

**Spec-Reife:** Inhaltlich final (ADR- und Architektur-Entscheidungen abgeschlossen).
**Umsetzungsstatus:** `In Progress` — Welle-Closure (C3) ersetzt
die finalen Commit-Hashes im Header und zieht den Slice auf `Done`.

## 1. Context

M3-Welle-0 (`cfb7a72` Slice-Doc + `4bd2673` Slice-Plan +
`f5de006` Trigger-Triage + `3e6170d` Review-Folge) hat die
M3-Doc-Foundation gelegt: M3-Slice-Plan mit Welle 0..7
Vorbelegung, Trigger-Triage gegen offene M2-Erbschaft, drei
ADR-Kandidaten (0022 Faults, 0023 Multi-Agent, 0024
Observability) skizziert.

Welle 1 ist die **Fault-Foundation**: erstes konkretes Code-
Stueck unter `hexagon/core/faults/`, neuer Driven-Port
`FaultPort`, Scenario-Validator-Haertung gegen unbekannte
Fault-Targets, TickLoop-Hook. Welle 1 schreibt **noch keine
konkreten Fault-Implementierungen** (das ist Welle 2: BatteryFault
`cell_failure`, GridFault `voltage_drop`, Recovery, Property-
Tests).

User-bestaetigte Design-Entscheidungen aus M3-Welle-1-Plan-Mode
(2026-05-20):

- **Validator-Haertung**: nur Target-Existenz (symmetrisch zu
  Events). Keine Type-Whitelist, keine semantische Validation
  (kein Vorgriff auf Welle-2-Semantik).
- **`NullFaultPort`**: KEINER. TickLoop akzeptiert
  `*, fault_port: FaultPort | None = None` (keyword-only, Default `None`);
  Hook wird uebersprungen wenn `None`. Tests verwenden Inline-Stubs.
- **Commit-Shape**: 4 Commits + welle-0-Move (= 5 Commits
  total), Pattern aus M2-Welle-6b (`8c26498`+`c58dbc2`+
  `0f1c597`+`93f784f`).

## 2. Scope

**In Scope:**

1. **ADR 0022** (Fault-Injection-Protocol + Scenario-Schema-
   Erweiterung) `Proposed` → `Provisional` mit Welle-1-Merge.
2. **`FaultInjectableDevice(DeviceModel)` Sub-Protocol** unter
   `src/grid_gym/hexagon/core/faults/_protocol.py` (per ADR 0013
   §2.8: keine Erweiterung der Base-`DeviceModel`).
3. **`FaultPort` Driven-Port** unter
   `src/grid_gym/hexagon/ports/driven/fault.py` mit
   `apply_active_faults(devices, context) -> None`
   (Orchestrierung, nicht Per-Device-Hook).
4. **Scenario-Validator-Haertung** —
   `ScenarioUnknownFaultTargetError` in `core/errors.py`;
   `_assert_fault_list` prueft Target-Existenz (analog
   `_assert_event_list`) mit optionalem `devices`-Parameter
   (`devices: Sequence[DeviceModel] | None = None`) für Signatur-
   Rückwärtskompat.
5. **TickLoop-Hook** — `fault_port: FaultPort | None`-Kwarg im
   Konstruktor; Hook im Vor-Tick-Block nach
   `_consume_load_inputs_into`, vor erster
   `_run_device_iteration`; Hook wird nur ausgeführt wenn das
   `fault_port` gesetzt ist (`None` skippt den Hook).
6. **Tests** (4 neue Test-Dateien):
   - Protocol-Adherence fuer `FaultInjectableDevice`
     (Pattern aus `tests/unit/hexagon/core/devices/test_protocol_contract.py`).
   - Protocol-Shape fuer `FaultPort` (Pattern aus
     `tests/unit/hexagon/ports/driven/test_clock.py`).
   - Validator-Negativ-Test fuer
     `ScenarioUnknownFaultTargetError`.
   - TickLoop-Hook-Order-Test (3 Tests: with-Port, ohne Port,
     Order vs. `device.tick(...)`).
7. **`CRITICAL_COV_TARGETS`-Default** im Dockerfile (Zeile 235)
   um `src/grid_gym/hexagon/core/faults` erweitert.

**Anti-Scope:**

- Konkrete Fault-Adapter (`BatteryFaultAdapter`,
  `GridFaultAdapter`) — Welle 2.
- Konkrete Fault-Typen (`cell_failure`, `voltage_drop`) —
  Welle 2.
- Recovery-Logik (`auto-recover-after-N-ticks` etc.) — Welle 2.
- Property-Tests fuer Fault-Determinismus — Welle 2.
- Type-Whitelist im Validator — verschoben auf Welle 2 oder
  spaeter (out-of-scope per User-Klaerung).
- Snapshot-Persistierung von Fault-State — M6
  `GG-PERSIST-*`-Slice.
- Multi-Agent-Bus, Observability-Ports — Welle 3+/5+.
- Integrationstest fuer Fault-Demo-Szenario — Welle 2 (mit
  konkreten Implementations).

## 3. Architektur-Entscheidungen

Welle 1 bringt **eine neue ADR**: ADR 0022 (Fault-Injection-
Protocol + Scenario-Schema-Erweiterung). Status-Lifecycle:

- `Proposed` mit Welle-1-C1 (separater `docs(adr)`-Commit).
- `Provisional` mit Welle-1-C2-Merge (`feat(welle-1)`).
- `Accepted` mit M3-Welle-7-Closure.

ADR 0022 erweitert ADR 0013 §2.8 (Sub-Protocol-Mandate) — kein
Supersede, reine Schaerfung. `FaultInjectableDevice` ist nicht
Teil der Base-`DeviceModel`-Surface, sondern eine Sub-Protocol-
Erweiterung mit `inject_fault(fault_type, payload)`.

Forward-Pointer (out-of-scope fuer Welle 1):

- ADR 0023 (Multi-Agent, geplant in Welle 3).
- ADR 0024 (Log/Metrics/Trace, geplant in Welle 5).
- Snapshot-Schema-Bump v2 → v3 (nur falls Welle-2-State-
  Modellierung das erzwingt; sonst M6).

## 4. Liefer-Reihenfolge (5 Commits)

### Pre-C0 — `chore(welle-1)`: `git mv welle-0.md → done/`

Reiner Rename-Commit ohne Inhalts-Edit. Memory-Konvention
`feedback_git_mv` strikt eingehalten (Lehrstunde aus M3-Welle-0-
Review-Folge M-1/M-2, wo der Move + Mini-Rewrite in einem
Commit kam — Welle 1 macht es jetzt sauber). `git diff --cached
--stat -M` zeigt 100% Similarity nach `git mv`.

### C0 — `docs(plan)`: welle-1 Slice-Doc (Welle-Beginn)

Dieses Dokument als Welle-Start-Marker. Status: `In Progress`.
Kein Code. Plus `in-progress/README.md`-Sync:
- `welle-0.md`-Zeile entfernt (Datei jetzt in `done/`).
- `welle-1.md`-Zeile ergaenzt.

### C1 — `docs(adr)`: ADR 0022 Proposed

Neu: `docs/plan/adr/0022-fault-injection-protocol.md`
(~ 4000 Woerter, Pattern aus ADR 0021). Inhalt:

- **Status**: `Proposed` (Datum 2026-05-20).
- **§1 Kontext**: Welle-6b-LoadEvent-Pattern als Vorbild;
  M1-Welle-5-Validator-Strukturvertrag; ADR 0013 §2.8
  Sub-Protocol-Mandate.
- **§2 Entscheidung** (6 Sub-Sections):
  - §2.1 `FaultInjectableDevice(DeviceModel)` Sub-Protocol mit
    `inject_fault(fault_type, payload)`.
  - §2.2 `FaultPort` Driven-Port mit
    `apply_active_faults(devices, context)`.
  - §2.3 Scenario-Schema unveraendert; Validator-Erweiterung
    additiv (Target-Existenz).
  - §2.4 TickLoop-Hook im Vor-Tick-Block.
   - §2.5 `FaultPort | None`-Kwarg mit Default `None`, explizit als
     keyword-only, damit bestehende positional Aufrufe von
     `TickLoop` stabil bleiben.
  - §2.6 Snapshot-Vertrag: kein State in Welle 1; v3-Bump
    verschoben.
- **§3 Begruendung**: Sub-Protocol vs. Base-Erweiterung;
  Orchestrierung vs. Per-Device-Hook;
  ScenarioFault-Wiederverwendung.
- **§4 Reichweite**: In/Out fuer Welle 1.
- **§5 Operative Artefakte**: Dateipfade analog Critical-Files.
- **§6 Konsequenzen**: TickLoop-Konstruktor + Coverage-Default-
  Erweiterung + Welle-2-Vorgriff.
- **§7 Nicht Gegenstand**: RL-Adapter, Multi-Agent, OTLP,
  konkrete Fault-Typen, Recovery-Logik, Snapshot-Migration.

Plus `adr/README.md`-Zeile fuer ADR 0022 `Proposed`.

### C2 — `feat(welle-1)`: FaultPort + Sub-Protocol + Validator + Hook + Tests

**Code (neu):**

1. `src/grid_gym/hexagon/core/faults/_protocol.py` —
   `FaultInjectableDevice(DeviceModel, Protocol)` mit
   `inject_fault(fault_type: str, payload: Mapping[str, object])`.
2. `src/grid_gym/hexagon/core/faults/__init__.py` — Re-export.
3. `src/grid_gym/hexagon/ports/driven/fault.py` —
   `FaultPort(Protocol)` mit
   `apply_active_faults(devices: Sequence[DeviceModel], context: DeviceTickContext)`.
4. `src/grid_gym/hexagon/ports/driven/__init__.py` — keine Änderung:
   Im bestehenden Projektstil werden Driven-Port-Protokolle (z. B.
   `clock`, `random`) derzeit via Modul-Imports verwendet, nicht über
   Paket-Re-Exports.

**Code (edit):**

5. `src/grid_gym/hexagon/core/errors.py` — neuer
   `ScenarioUnknownFaultTargetError(ScenarioSchemaError)`
   analog `ScenarioUnknownEventTargetError`.
6. `src/grid_gym/hexagon/core/scenario/validator.py` —
  `_assert_fault_list` mit Target-Existenz-Check (Signatur-
  Erweiterung um optionalen
  `devices: Sequence[DeviceModel] | None = None`-Parameter; spiegelt
  `_assert_event_list`).
7. `src/grid_gym/hexagon/core/simulation/tick_loop.py` —
  Konstruktor-Kwarg `*, fault_port: FaultPort | None = None`;
  Hook im Vor-Tick-Block.

**Tests (neu):**

8. `tests/unit/hexagon/core/faults/__init__.py` — leer.
9. `tests/unit/hexagon/core/faults/test_protocol.py` —
   `NullFaultInjectableDevice` als Test-Fake; Protocol-
   Adherence-Tests.
10. `tests/unit/hexagon/ports/driven/test_fault.py` — Inline-
   Stub mit `apply_active_faults`-Methode; Protocol-Shape-Test.
11. `tests/unit/hexagon/core/scenario/test_validator_fault_target.py`
    — Negativ + Happy-Path.
12. `tests/unit/hexagon/core/simulation/test_tick_loop_welle_1_fault.py`
    — drei Tests:
    - `test_tick_loop_calls_fault_port_when_set`
    - `test_tick_loop_skips_hook_when_fault_port_is_none`
    - `test_tick_loop_calls_fault_port_before_first_device_tick`
      (Order-Pinning).

**Build-Konfiguration:**

12. `Dockerfile` — `CRITICAL_COV_TARGETS`-ARG-Default um
    `src/grid_gym/hexagon/core/faults` erweitert.

### C3 — `docs(plan)`: Welle-1 Status/DoD-Sync

- `docs/plan/adr/0022-fault-injection-protocol.md` —
  `Proposed → Provisional` mit Welle-1-Merge-Hash (C2).
- `docs/plan/adr/README.md` — ADR 0022 auf `Provisional`.
- `docs/plan/planning/in-progress/M3-faults-agents-observability.md` —
  §0 Status-Block: „Welle 1 abgeschlossen am 2026-05-20"
  ergaenzt; §3 Welle 1 mit `Done`-Tag + Commit-Refs;
  „Naechster Schritt: Welle 2 (Battery-Fault + Grid-Fault
  konkret)".
- `docs/plan/planning/in-progress/welle-1.md` (dieses Dokument)
  — Status auf `Done` mit C0/C1/C2/C3-Hashes; Hash-Platzhalter
  ersetzt.

## 5. Critical Files

| Pfad                                                                | Commit  | Aktion |
| ------------------------------------------------------------------- | ------- | ------ |
| `docs/plan/planning/in-progress/welle-0.md` → `done/welle-0.md`     | Pre-C0  | git mv (rename-only) |
| `docs/plan/planning/in-progress/welle-1.md`                         | C0      | NEU (dieses Dokument) |
| `docs/plan/planning/in-progress/README.md`                          | C0      | EDIT (welle-0→welle-1) |
| `docs/plan/adr/0022-fault-injection-protocol.md`                    | C1      | NEU |
| `docs/plan/adr/README.md`                                           | C1      | EDIT (ADR 0022 Zeile) |
| `src/grid_gym/hexagon/core/faults/_protocol.py`                     | C2      | NEU |
| `src/grid_gym/hexagon/core/faults/__init__.py`                      | C2      | EDIT (re-export) |
| `src/grid_gym/hexagon/ports/driven/fault.py`                        | C2      | NEU |
| `src/grid_gym/hexagon/core/errors.py`                               | C2      | EDIT (`ScenarioUnknownFaultTargetError`) |
| `src/grid_gym/hexagon/core/scenario/validator.py`                   | C2      | EDIT (`_assert_fault_list` Target-Check) |
| `src/grid_gym/hexagon/core/simulation/tick_loop.py`                 | C2      | EDIT (Konstruktor + Hook) |
| `src/grid_gym/hexagon/ports/driven/__init__.py`                     | C2      | KEIN |
| `tests/unit/hexagon/core/faults/__init__.py`                        | C2      | NEU |
| `tests/unit/hexagon/core/faults/test_protocol.py`                   | C2      | NEU |
| `tests/unit/hexagon/ports/driven/test_fault.py`                     | C2      | NEU |
| `tests/unit/hexagon/core/scenario/test_validator_fault_target.py`   | C2      | NEU |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_1_fault.py`| C2      | NEU |
| `Dockerfile`                                                        | C2      | EDIT (`CRITICAL_COV_TARGETS` + `core/faults`) |
| `docs/plan/adr/0022-fault-injection-protocol.md`                    | C3      | EDIT (Status → Provisional) |
| `docs/plan/adr/README.md`                                           | C3      | EDIT (Status → Provisional) |
| `docs/plan/planning/in-progress/M3-faults-agents-observability.md`  | C3      | EDIT (§0 + §3 Welle 1 Closure) |
| `docs/plan/planning/in-progress/welle-1.md`                         | C3      | EDIT (Status → Done) |

## 6. Verifikationspfad

End-to-End ueber `make`-Targets (Dockerfile-Stages, Docker-only
nach Repo-Konvention):

1. **`make test-unit`** — gruen mit ~6–8 neuen Tests (Protocol-
   Adherence + Validator-Negativ + TickLoop-Hook-Order). Test-
   Count steigt von 762 auf ~768–770.
2. **`make test-integration`** — unveraendert gruen (9 Tests;
   kein Integrationstest-Pfad in Welle 1).
3. **`make gates`** — gruen ohne Override;
   `CRITICAL_COV_TARGETS`-Default um `core/faults` erweitert;
   Coverage ≥ 90 % Line + Branch auf neuen Modulen.
4. **`make fullbuild`** — gruen ohne Override (Sanity-Check;
   Welle-Gate ist eigentlich `make test-unit` + `make gates`,
   aber fullbuild verifiziert Compose-Smoke).
5. **ADR-0022-Status sichtbar `Provisional`** nach C3 in
   `docs/plan/adr/0022-fault-injection-protocol.md` und
   `docs/plan/adr/README.md`.
6. **Rename-Historie**: `git log --follow done/welle-0.md`
   zeigt komplette Historie ueber den Pre-C0-Rename hinweg
   (100% Similarity erwartet).
7. **Git-Pattern**: 5 neue Commits in der Reihenfolge
   `chore(welle-1): git mv welle-0.md → done/ (Pre-C0)` →
   `docs(plan): welle-1 Slice-Doc (C0)` →
   `docs(adr): ADR 0022 Proposed (C1)` →
   `feat(welle-1): FaultPort + Sub-Protocol + Validator + Hook + Tests (C2)` →
   `docs(plan): Welle-1 Status/DoD-Sync (C3)`. `git log
   --oneline -5` zeigt diese fuenf Hashes.

## 7. Risiken

- **Welle-2-Vorgriff durch ungenutzten Hook**: TickLoop ruft
  `fault_port.apply_active_faults(...)` an, aber kein
  produktiver Adapter existiert. *Mitigation*: TickLoop-Hook
  skippt sauber bei `fault_port=None`; alle bestehenden Tests
  bleiben gruen (kein Test setzt `fault_port`). Welle-2-Adapter
  steigt dann nahtlos ein.
- **Snapshot-Schema-Bump-Risiko**: FaultPort selbst haelt
  keinen State in Welle 1, aber Welle-2-Implementations koennen
  Fault-State haben (z. B. `cell_failure_active: bool` in
  BatteryDevice). Das wuerde Snapshot-Schema v2 → v3 erfordern
  (ADR 0015-Pattern). *Mitigation*: ADR 0022 §2.6 + §7
  dokumentieren explizit, dass Snapshot-Bump erst mit Welle 2
  oder M6 kommt; Welle-1-Code ist v2-kompatibel.
- **Sub-Slicing-Schwelle nicht ausgeloest**: Welle 1 hat 7
  Liefer-Items (ADR + Port + Sub-Protocol + Validator + Hook +
  Tests + Default-Gate), davon 1 echte Architektur-Entscheidung
  (ADR 0022). Liegt **unter** der Sub-Slicing-Schwelle aus
  `M3-faults-agents-observability.md §3` (> 6 Items mit ≥ 2
  Architektur-Entscheidungen). *Fallback*: falls ADR 0022 in
  C1-Review zu gross wird, kann Sub-Protocol in Welle 1a und
  Port + Hook in Welle 1b geteilt werden.
- **Memory-Konvention `feedback_git_mv`**: Pre-C0 ist
  ausdruecklich reiner Rename (keine Inhalts-Edits) zur strikten
  Einhaltung der Memory-Regel. M3-Welle-0-Finding M-1 hat die
  Konvention formal verletzt; Welle 1 macht es richtig.

## 8. Wandert nach

- `done/welle-1.md` mit M3-Welle-7-Closure (analog
  `welle-6c.md` → `welle-7.md` → `done/` Pattern aus M2).
