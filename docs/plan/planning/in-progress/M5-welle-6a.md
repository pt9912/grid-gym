# Welle 6a — M5 Fault-Flow (UI-Form-Validation + YAML-Fault-Demo)

**Status:** In Progress — eroeffnet 2026-06-03 mit C0
(dieser Commit). Welle 6 wurde am C0-Pre-Research-
Zeitpunkt (2026-06-03) in drei Sub-Slices unterteilt
(siehe §0 Sub-Slicing-Beschluss). Welle 6a deckt den
Fault-Flow-Sub-Bereich ab und schliesst die
`GG-DEMO-006`-Anti-Scope-Erbschaft aus Welle 5.

Welle 6a ist die **siebte Code-Welle** in M5 und die
erste **Welle-5-Anti-Scope-Aufnahme**: sie loest
`GG-DEMO-006` (Fault-Injection in Demo) per YAML-side
und liefert die `GG-UI-007`-Fault-Eingabe-Form mit
Server-Side-Cross-Field-Validation.

**Erfuellt:** `GG-UI-007` (1 SOLLTE) + `GG-DEMO-006`
(1 SOLLTE).

---

## 0. Sub-Slicing-Beschluss Welle 6 → 6a + 6b + 6c

Welle 6 hatte per `M5-ui-demo.md §3.2` ein breites
Lieferziel mit drei distinkten Sub-Bereichen:

| Sub-Bereich | Substanz | Welle |
| ----------- | -------- | ----- |
| Fault-Flow | `GG-UI-007` Form + `GG-DEMO-006` Demo-Fault | **6a** (dieser Slice) |
| UI-Visualization | `GG-UI-006` Geraete-Grafik + `GG-UI-008` Sim-Zustand-Dashboard | 6b |
| Abnahmedoku | `GG-DEMO-008` `docs/user/gg-demo-008-abnahme.md` | 6c |

**Sub-Slicing-Schwellen-Verifikation** (per
`M5-ui-demo.md §3` Praeambel: > 300 LOC Slice-Doc
ODER > 5 Code-Commits ODER mehr als zwei unabhaengige
Sub-Bereiche → Sub-Slicing):

- **Drei unabhaengige Sub-Bereiche** belegt
  (Fault-Substanz / Visualization-Substanz / Pure-Doku),
  → Sub-Slicing aktiviert.
- Pattern analog **M4-Welle-6 → 6a/6b**
  (Cross-Adapter-Hardening + IEC-61850-Lizenz-und-
  Smoke-Hardening; zwei distinkte Sub-Bereiche).

**Reihenfolge:** 6a → 6b → 6c (Abnahmedoku schliesst
ab, weil sie alle anderen Sub-Sections braucht).

**Welle-5-Anti-Scope-Aufnahme:** `GG-DEMO-006` und
`GG-DEMO-008` waren in Welle 5 (Slice-Doc
[`M5-welle-5.md`](../done/M5-welle-5.md) §1.3 + §10.1)
explizit auf Welle 6 verschoben — 6a nimmt 006, 6c
nimmt 008. `GG-UI-007` Form-Substanz war von Anfang an
Welle-6-Material; 6a buendelt sie mit dem
`GG-DEMO-006`-Trigger.

---

## 1. Context

### 1.1 Existierende Substanz (M3-Welle-2 + M5-Welle-1..5)

Welle 6a baut auf voll ausgereifter Fault-Infrastruktur
auf — alle Bausteine sind bereits produktiv:

**Fault-Backend (M3 Welle 1+2 + ADR 0022/0025):**

- `FaultPort`-Driven-Port-Protocol unter
  [`hexagon/ports/driven/fault.py`](../../../../src/grid_gym/hexagon/ports/driven/fault.py)
  mit `apply_active_faults(devices, context) -> None`.
- `BatteryFaultAdapter` unter
  `hexagon/core/faults/battery_fault_adapter.py` —
  Recovery-Engine fuer `cell_failure` mit half-open
  `[start, end)`-Aktivitaets-Check, idempotenter
  Inject-/Recovery-Transitionen, ScenarioFault-Konstruktor-
  Injection.
- `GridFaultAdapter` analog fuer `voltage_drop` auf
  `GridConnectionDevice`.
- `FaultInjectableDevice`-Protocol; Battery + Grid-
  Connection erfuellen es.
- YAML-Schema-Vorlage in
  [`tests/integration/scenarios/fault_demo.yaml`](../../../../tests/integration/scenarios/fault_demo.yaml)
  mit `faults:`-Block (start_simulation_time +
  duration_ms + target + type + payload + recovery).

**Scenario-Loader (M2-Welle-6b + ADR 0021):**

- `scenario/loader.py::_parse_faults` produktiv —
  liest `faults:`-Block aus dem validierten Mapping in
  `tuple[ScenarioFault, ...]`.
- `TickLoopWiring.fault_port: FaultPort | None = None`
  ist der Wiring-Slot in `build_tick_loop(...)`.

**HTTP-API + UI (M5-Welle-1..4b + Welle 5):**

- Welle-1-Stub `POST /runs/{run_id}/faults` validiert
  `FaultInjectionRequest`-Schema (fault_type +
  target + start_at_tick + duration_ticks +
  recovery); antwortet 201 + `fault_id` (uuid4) +
  `accepted=true`. **Kein** echter
  `FaultPort.activate`-Call.
- UI-Template-Konvention: `<page>.html` (full layout)
  + `_<page>_content.html` (HTMX-Partial), `_is_htmx_
  request`-Switch im Route-Handler.
- Welle-4b-Alarm-Pipeline produktiv: jeder Fault, der
  ein Device-Limit ausloest, emittiert einen
  `Alarm` ueber `TickResult.emitted_alarms` →
  `AlarmStreamPort` → UI-Page `/runs/{id}/alarms`.

**Demo-Pipeline (Welle 5):**

- `deploy/scenarios/gg-demo.yaml` ist Welle-5-NEU,
  hat `load_events:` + `load_profiles:` + `agents:`,
  hat aber **keinen `faults:`-Block**.
- `_demo_scenario_setup.configure_scenario_demo_run`
  baut `TickLoopWiring` ohne `fault_port` (Welle-5
  Anti-Scope).

Welle 6a ergaenzt diesen Stack um **kein neues
Architektur-Pattern, keinen neuen Port, keine
Adapter-Refactor** — nur:

1. `faults:`-Block in `gg-demo.yaml`.
2. `BatteryFaultAdapter`/`GridFaultAdapter`-
   Composition im Lifespan-Demo-Pfad.
3. UI-Page + Form mit HTMX-POST-Submit.
4. Server-Side-Cross-Field-Validation im POST-/faults-
   Handler.

### 1.2 Welle-6a-Lieferziel

Welle 6a liefert produktiv:

1. **GG-DEMO-006 erfuellt per YAML-side:**
   `gg-demo.yaml` bekommt einen `faults:`-Block mit 1
   Battery-`cell_failure` + 1 Grid-`voltage_drop`
   (analog `fault_demo.yaml`-Pattern). Deterministisch
   reproduzierbar mit `seed=42`.
2. **FaultPort-Composition im Demo-Lifespan-Pfad:**
   `_demo_scenario_setup.configure_scenario_demo_run`
   baut einen kombinierten FaultPort (Battery+Grid)
   und reicht ihn ueber `TickLoopWiring.fault_port`
   an `build_tick_loop(...)` durch. Default-Welle-4a-
   Pfad (`configure_demo_run` ohne Scenario) bleibt
   unveraendert.
3. **UI-Page `/runs/{run_id}/faults`** mit Form-
   Eingabe (fault_type + target + start_at_tick +
   duration_ticks + recovery). HTMX-POST gegen
   bestehenden `POST /runs/{id}/faults`. Pattern
   analog Welle-2-Demo-Page + Welle-4a-Control-Page.
   Navigation in `templates/navigation.html` um
   „Faults"-Link erweitert.
4. **Server-Side-Cross-Field-Validation** im POST-/
   faults-Handler:
   - `target_device_id` muss im laufenden Run-Scenario
     existieren (sonst 422 mit `ScenarioUnknownEvent
     TargetError`-Analoga).
   - `fault_type` muss zum Target-Device-Typ passen
     (Battery → `cell_failure`, GridConnection →
     `voltage_drop`); andere Kombinationen → 422.
   - HTMX-Partial-Response rendert den Form-Body neu
     mit Inline-Error-Block; Browser ohne HTMX
     bekommen plain 422.
5. **Determinismus-Hash-Pin-Update:** Welle-5-Smoke
   `test_m5_welle_5_demo_smoke.py` hat einen
   Scenario-Hash-Pin. Welle 6a aendert den Hash durch
   den `faults:`-Block — der Pin in §6 wird
   aktualisiert.
6. **Integration-Smoke** unter
   `tests/integration/test_m5_welle_6a_fault_smoke.py`:
   POST /faults mit Cross-Field-Validation-Fehler →
   422; POST mit gueltigem Payload → 201; YAML-side-
   Fault-Trigger im Demo-Run → 1 LIMITED-Alarm in
   AlarmHistoryBuffer.

### 1.3 Welle-6a-Anti-Scope

Welle 6a liefert **explizit nicht**:

- **Dynamic-FaultPort-Mutation** (POST /faults
  schreibt **nicht** in den laufenden FaultPort-
  State). Welle-1-Stub-Antwort 201+uuid bleibt; nur
  die Cross-Field-Validation kommt dazu. Echte
  dynamische Fault-Injection ueber UI ist Welle 7+/
  M6 Material und braucht ein eigenes ADR (Decision
  19 verankert das).
- **`GG-UI-006` Geraete-Grafik** — Welle 6b.
- **`GG-UI-008` Sim-Zustand-Dashboard** — Welle 6b.
- **`GG-DEMO-008` Abnahmedoku** — Welle 6c.
- **NEU FaultPort-Adapter-Klasse** unter
  `adapters/driven/fault_*/` — die existierenden
  `BatteryFaultAdapter`/`GridFaultAdapter` aus
  `hexagon/core/faults/` werden direkt in der
  Lifespan-Komposition genutzt (Welle-5-Pattern
  analog `_demo_scenario_setup`-Helper-Closures).
- **C1 ADR-Commit** — keine neuen Driving-Port-Slots,
  keine neuen Architektur-Vertraege; Pattern analog
  Welle-5-`64d5129` (Slice-Doc + Code ohne C1).

---

## 2. Scope

| Ebene | Welle-6a-Erweiterung | Welle-6a-Anti-Scope |
| ----- | -------------------- | ------------------- |
| Domain / Simulation | — | — |
| Scenario-Loader | — (`_build_faults` produktiv) | — |
| Adapters/driven | — | NEU FaultPort-Adapter-Klasse |
| Adapters/driving | UI-Page `/runs/{id}/faults` + Cross-Field-Validation im POST-Handler | Dynamic-FaultPort-Mutation |
| UI | NEU `templates/faults.html` + `_faults_content.html` + Navigation-Link | Geraete-Grafik, Sim-Zustand |
| Konfiguration / Deploy | `gg-demo.yaml` `faults:`-Block | Neue Compose-Konfiguration |
| Doku | — | `gg-demo-008-abnahme.md` (Welle 6c) |
| Tests | 1 Integration-Smoke + Welle-5-Smoke-Hash-Update | — |

---

## 3. Architektur-Entscheidungen (Welle-6a-Decisions)

### 3.1 NEU Decision 19 (Fault-Injection-Production-Pattern) — final fixiert

**Decision:** `GG-DEMO-006` wird **YAML-side** erfuellt
(`gg-demo.yaml` `faults:`-Block via `BatteryFault
Adapter`+`GridFaultAdapter`-Composition im
`_demo_scenario_setup`-Lifespan-Pfad). `GG-UI-007` ist
**Form-Validation-only**: Welle-1-Stub-Antwort
201+uuid bleibt im POST-/faults-Handler; die UI-Page
liefert nur die Form + Server-Side-Cross-Field-
Validation. **Dynamic-FaultPort-Mutation ueber UI ist
Anti-Scope.**

**Begruendung:**

- `GG-UI-007`-Akzeptanz: „eingegeben und vor
  Ausloesung validiert" — Form-Validation reicht.
- `GG-DEMO-006`-Akzeptanz: „reproduzierbar
  ausgeloest" — exakt der YAML-side-Use-Case
  (Determinismus per Seed).
- Dynamic-FaultPort-Mutation waere ein neues
  Architektur-Pattern: Mutable-Scenario-Faults-
  Liste, FaultPort-Re-Composition pro POST,
  Race-Condition-Behandlung (asyncio-Driver-Task +
  POST-Handler-Coroutine konkurrieren um
  scenario.faults). Das verlangt ein eigenes ADR
  und ist Welle-7+/M6-Material.

**Konsequenz:**

- Welle-1-Stub-Antwort von POST /faults bleibt 201+
  `accepted=true` (echo-only); die Welle-6a-Aenderung
  ist nur die Cross-Field-Validation davor.
- `_demo_scenario_setup` baut `BatteryFaultAdapter`
  + `GridFaultAdapter` und komponiert sie zu einem
  FaultPort (kleiner Helper `_compose_fault_port(
  faults)`); reicht ihn an `TickLoopWiring.fault_port`
  durch.
- Demo-Run zeigt die YAML-faults reproduzierbar im
  Dashboard (Telemetry-Quality + Alarm) — Welle-4b-
  Alarm-Pipeline drainst sie ueber
  `TickResult.emitted_alarms`.

**Out-of-Scope:**

- Eigener Dynamic-FaultPort-Adapter unter
  `adapters/driving/http_api/`.
- ScenarioFault-Mutability-Refactor.
- Re-Composition-Pattern fuer FaultPort bei
  Live-Submission.

### 3.2 NEU Decision 20 (UI-Form Cross-Field-Validation) — final fixiert

**Decision:** `POST /runs/{run_id}/faults` bekommt
eine **Cross-Field-Validation** zusaetzlich zur
heutigen Pydantic-Schema-Validierung:

1. **`target_device_id`-Resolution:** muss im
   `TickLoopRegistry` registrierten Run-Scenario
   existieren. Welle-6a-Lookup ueber die Demo-Run-ID;
   Multi-Run-Lookup ist Welle 6+ (analog Welle-5-
   Anti-Scope Multi-Run-Driver-Registry).
2. **`fault_type ↔ Device-Typ`-Whitelist:**
   - Battery-Device + `fault_type == "cell_failure"` → OK.
   - GridConnection-Device + `fault_type == "voltage_
     drop"` → OK.
   - Andere Kombinationen → 422.

**Failure-Response:**

- Plain HTTP-Client (kein `HX-Request`-Header) →
  422 mit `ErrorResponse`-Body (`code` = `"fault_
  invalid_target"` oder `"fault_invalid_type_for_
  target"`, `message`, `details`, `run_id`).
- HTMX-Sub-Request → 422 mit Partial-HTML-Body
  (Form-Felder wiederholt + Inline-Error-Block ueber
  betroffenem Input). HTMX rendert das Partial in
  das `hx-target`-Element der Form ein.

**Begruendung:**

- `GG-UI-007`-Akzeptanz „vor Ausloesung validiert"
  verlangt Cross-Field-Check (nicht nur Schema).
- Bestehende `ScenarioUnknownEventTargetError`-/
  `ScenarioUnknownFaultTargetError`-Patterns aus
  `scenario/validator.py` zeigen das Vokabular fuer
  die Error-Codes.
- 422 statt 400, weil Pydantic + FastAPI fuer
  Validation-Errors standardmaessig 422 nutzen
  (`HTTPException`-Konsistenz).

**Out-of-Scope:**

- Multi-Device-Typ-Faults (z. B. `over_temperature`
  fuer alle Devices). Welle-6a beschraenkt sich auf
  die zwei produktiven Fault-Typen aus M3-Welle-2.
- Frontend-Pre-Validation (JS) — HTMX-POST roundtrips
  per Tastenklick; Server bleibt einzige Validation-
  Quelle.
- Whitelist-Erweiterung fuer Welle-7+/M6-Fault-Typen.

---

## 4. Liefer-Reihenfolge (3..4 Commits)

### Pre-C0 — bereits erledigt (Welle-5-Closure)

1. **Welle-5-C4a** `da8d728` — Self-Close-Move
   `M5-welle-5.md → done/` (rename-only).
2. **Welle-5-C4b** `2c9d8da` — Cross-Doc-Refs-Sync
   nach Move (5 Refs).

Welle 6a startet damit direkt mit C0 (kein eigener
Pre-C0a/Pre-C0b noetig — die Konvention macht Welle-5-
Closure-Move zum effektiven Pre-C0 der Folge-Welle).

### C0 — `docs(plan)`: M5-welle-6a Slice-Doc + Decisions 19/20

**Dieser Commit.** Schreibt
`docs/plan/planning/in-progress/M5-welle-6a.md` mit:

- §0 Sub-Slicing-Beschluss Welle 6 → 6a/6b/6c.
- Decisions 19/20 final fixiert (siehe §3).
- Scope + Anti-Scope (Welle-1-Stub-Antwort bleibt;
  Dynamic-FaultPort deferiert).
- Liefer-Reihenfolge (C0 → C2 → C3 → C4a/b).
- Critical Files + Verifikationspfad + Risiken.
- DoD-Checkliste (initial leer; C3 hakt ab).

Keine ADR-Aenderung in C0 — Welle 6a hat keinen
neuen Driving-Port-Slot und keinen neuen Architektur-
Vertrag (Decision 19 ist explizit „kein neues
Pattern"; ADR 0022/0025 sind unveraendert anwendbar).

### C1 — **bewusst entfaellt** (Pattern Welle-1 + Welle-5)

Welle 6a fuehrt **keinen neuen Driving-Port** und
**keinen neuen Architektur-Vertrag** ein. Decision 19
ist explizit Anti-Pattern-Decision (kein Dynamic-
FaultPort); Decision 20 ist Validation-Logic im
bestehenden Handler. Falls C2-Pre-Research eine
unerwartete neue Vertrags-Substanz findet, kann C1
als `docs(adr): M5-Welle-6a-C1 — NEU ADR 0041 (...)`
nachgereicht werden — heute kein Anlass.

### C2 — `feat(welle-6a)`: Demo-Faults + UI-Form + Cross-Field-Validation

**Code-Merge** mit:

- `deploy/scenarios/gg-demo.yaml`: NEU `faults:`-Block
  (1 Battery-`cell_failure` von z. B.
  `start_simulation_time=200000` (Tick 200) fuer
  `duration_ms=10000` (10 Ticks) + 1 Grid-`voltage_
  drop` von `start_simulation_time=400000` (Tick 400)
  fuer `duration_ms=5000` (5 Ticks)).
- Erweiterung `src/grid_gym/adapters/driving/http_api/
  _demo_scenario_setup.configure_scenario_demo_run`:
  NEU `_compose_fault_port(loaded.scenario.faults)`-
  Helper, der Battery+GridFault-Adapter komponiert
  (oder einen schmalen `_FaultPortComposition`-
  Wrapper); `TickLoopWiring.fault_port=...` durchreichen.
- NEU `src/grid_gym/adapters/driving/ui/templates/
  faults.html` (full layout) +
  `_faults_content.html` (HTMX-Partial). Form mit
  5 Feldern; HTMX-Attribute `hx-post`, `hx-target`,
  `hx-swap` analog Welle-4a-Control-Page.
- Erweiterung `src/grid_gym/adapters/driving/ui/
  routes.py`: NEU `GET /runs/{run_id}/faults`-Route
  + `_is_htmx_request`-Switch.
- Erweiterung `src/grid_gym/adapters/driving/http_api/
  _runs_action_router.post_run_faults`: Cross-Field-
  Validation per Decision 20.
- `templates/navigation.html`: NEU „Faults"-Link.
- NEU `tests/integration/test_m5_welle_6a_fault_smoke.py`
  (Lifespan-Demo-Pfad + POST-Validation-Cases + YAML-
  Fault-Trigger + AlarmHistoryBuffer-Check).
- Welle-5-Smoke
  `tests/integration/test_m5_welle_5_demo_smoke.py`
  Hash-Pin-Update (faults-Block aendert den Scenario-
  Hash; bewusster Refresh).
- Tests: Coverage-Gates gruen halten, `make gates`
  cache-frei gruen.

### C3 — `docs(plan)`: Welle-6a Status/DoD-Sync + Top-Level-Doku-Sync

**Status/DoD-Sync** mit:

- `M5-welle-6a.md` Status `In Progress → Done`
  + ggf. §10 C2-Realization-Notes (falls vorhanden).
- `M5-ui-demo.md §3.1 Welle-Status-Tabelle` Zeile
  Welle 6a NEU einfuegen (heute steht Welle 6 als
  Pending-Aggregate; Welle 6a/6b/6c bekommen je
  eine Zeile nach Sub-Slicing-Beschluss).
- `in-progress/README.md` Welle-6a-Closure-Block +
  Welle-6b-Aktive-Welle-Marker.
- `in-progress/roadmap.md` Welle-6a-Closure-Entry.
- `README.md` + `README.de.md` Test-Counts (1681u +
  57i → neu) + GG-UI-007/DEMO-006-Coverage-Bullet.

### C4 — `chore`: Self-Close-Move + Cross-Doc-Refs-Sync

Pflicht-Closure-Sequenz per
[`planning/README.md`](README.md) Wave-Self-Close-
Commit-Konvention:

- **C4a** — `chore: git mv in-progress/M5-welle-6a.md
  → done/` (rename-only, kein Inhalts-Edit; Memory
  `feedback_git_mv`-Konvention).
- **C4b** — Cross-Doc-Refs-Sync nach Move: relative
  Pfade in `done/M5-welle-6a.md` + Verweise aus
  `M5-ui-demo.md §3.1` + `in-progress/README.md` +
  `roadmap.md` auf den `../done/`-Pfad. Pattern
  analog Welle-5-C4b `2c9d8da`.

---

## 5. Critical Files

**Welle-6a-NEU (geschrieben in C2):**

- `src/grid_gym/adapters/driving/ui/templates/
  faults.html` + `_faults_content.html`.
- `tests/integration/test_m5_welle_6a_fault_smoke.py`.

**Welle-6a-MODIFY (in C2):**

- `deploy/scenarios/gg-demo.yaml` — NEU `faults:`-Block.
- `src/grid_gym/adapters/driving/http_api/
  _demo_scenario_setup.py` —
  `_compose_fault_port(...)` + `TickLoopWiring.fault_
  port`-Wiring.
- `src/grid_gym/adapters/driving/http_api/
  _runs_action_router.py` — Cross-Field-Validation
  im `post_run_faults`-Handler.
- `src/grid_gym/adapters/driving/ui/routes.py` —
  NEU `GET /runs/{run_id}/faults`-Route.
- `src/grid_gym/adapters/driving/ui/templates/
  navigation.html` — NEU „Faults"-Link.
- `tests/integration/test_m5_welle_5_demo_smoke.py` —
  Hash-Pin-Update.

**Welle-6a-UNBERUEHRT (kein Edit):**

- `deploy/compose.yml` — Decision 18 weiter aktiv.
- `BatteryFaultAdapter`/`GridFaultAdapter`-
  Klassen unter `hexagon/core/faults/` — werden nur
  konsumiert.
- `FaultPort`-Protocol — unveraendert.
- Welle-4b-Alarm-Pipeline.
- Scenario-Loader + Validator.

---

## 6. Verifikationspfad

**Welle-6a-Gate (per `M5-ui-demo.md §3.1` neue Zeile):**

- `make gates` cache-frei gruen ohne Override.
- `make demo` lokal: Demo-Run zeigt im Dashboard die
  YAML-faults reproduzierbar (Battery-cell_failure-
  Alarm bei Tick 200; Grid-voltage_drop-Alarm bei
  Tick 400).
- UI-Page `/runs/demo-run-0001/faults` rendert das
  Form-Layout; Form-Submit mit ungueltigem
  `target_device_id` → 422 mit Inline-Error.

**Test-Verifikation:**

- `make test-unit` gruen (kein Regress vs 1681).
- `make test-integration` gruen:
  - NEU `test_m5_welle_6a_fault_smoke.py` als NEU
    (57 → 58+).
  - Welle-5-Smoke-Hash-Pin auf neuen `gg-demo.yaml`-
    Stand.
- Coverage-Gates gruen.

**Abnahme-Verifikation (Lastenheft):**

- `GG-UI-007` (Form + Cross-Field-Validation
  produktiv).
- `GG-DEMO-006` (Fault im Demo reproduzierbar mit
  Telemetry-Quality-Marker + Alarm).

---

## 7. Risiken

**R1 — Alarm-Pipeline-Wiring fuer Demo-Faults.**
Welle-4b-Alarm-Pipeline emittiert Alarme ueber
`TickResult.emitted_alarms`. Battery-`cell_failure`
ist M3-Welle-2-Substanz; emittiert sie automatisch
einen Welle-4b-Unified-`Alarm`? **Mitigation:** C2-
Pre-Research bestaetigt den Pfad mit
`make test-integration` (existierender
`test_fault_demo_scenario.py`); falls Alarm-Emission
fehlt, Welle-6a-C2 ergaenzt den Mapper in
`core/simulation/alarm_mappers.py` (kleines Add-On,
nicht ADR-pflichtig).

**R2 — Cross-Field-Validation-Komplexitaet.** Der
POST-/faults-Handler braucht Zugriff auf den
TickLoopRegistry, um die Device-Liste des aktiven
Runs zu lesen. Welle-1-Stub hat heute nur
`get_run_repository`-Dependency.
**Mitigation:** zusaetzliche Dependency
`get_tick_loop_registry` einhaengen (Welle-4a-Pattern
analog). Die Devices liegen als
`TickLoop._devices`-private-Field — Welle-6a baut
einen schmalen `_tick_loop_devices(run_id)`-Helper
auf der TickLoopRegistry.

**R3 — HTMX-Partial-Error-Layout.** Form-Inline-
Error braucht ein konsistentes Partial-Layout, das
sowohl 422 als auch 201 sauber rendert.
**Mitigation:** Pattern analog Welle-4a-Control-Page
Status-Block (HTMX-Polling rendert State-Updates in
ein Sub-Partial; Welle-6a nutzt dasselbe Pattern fuer
Error vs. Success).

**R4 — `gg-demo.yaml` `faults`-Block-Determinismus.**
Der Hash-Pin im Welle-5-Smoke aendert sich. Wenn
Welle 6b oder spaetere Wellen weitere YAML-Aenderungen
machen, drueckt der Pin entweder durch oder muss
erneut aktualisiert werden.
**Mitigation:** Hash-Pin bleibt nur im Welle-5-Smoke;
neue Welle-6a-Smoke-Test pinnt eigenen Hash (zwei
Pins, einer pro Smoke). Beim naechsten YAML-Edit ist
der Update-Bedarf klar lokalisiert.

**R5 — `BatteryFaultAdapter`/`GridFaultAdapter`-
Composition zu FaultPort.** Beide implementieren
`FaultPort.apply_active_faults`. Eine Komposition
muss beide pro Tick aufrufen (mit `devices`-Filter).
**Mitigation:** kleiner privater
`_FaultPortComposition`-Klasse in
`_demo_scenario_setup.py`, die beide Adapter haelt
und sequenziell delegiert. Pattern analog Welle-5-
`_alarm_*_provider`-Closures.

---

## 8. Wandert nach

- Bei C3-Closure: `M5-welle-6a.md` bleibt in
  `in-progress/` bis C4a Self-Close-Move (Pattern
  analog Welle-1..5).
- `M5-ui-demo.md` bleibt in `in-progress/` bis
  M5-Welle-7-Closure.
- Welle 6b (`GG-UI-006` Geraete-Grafik +
  `GG-UI-008` Sim-Zustand-Dashboard) als naechster
  aktiver Schritt nach Welle 6a.
- Welle 6c (`GG-DEMO-008` Abnahmedoku) als
  Welle-6-Abschluss nach Welle 6b.

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [ ] **`gg-demo.yaml` `faults:`-Block** mit 1
  Battery-`cell_failure` + 1 Grid-`voltage_drop`
  (Decision 19 YAML-side-Erfuellung).
- [ ] **`_demo_scenario_setup.configure_scenario_
  demo_run` FaultPort-Composition** ueber
  Battery+Grid-FaultAdapter; `TickLoopWiring.fault_
  port` durchgereicht.
- [ ] **NEU UI-Page `/runs/{run_id}/faults`** mit
  Form + HTMX-POST-Submit.
- [ ] **Cross-Field-Validation** im POST-/faults-
  Handler per Decision 20 (target_device_id
  resolves + fault_type ↔ Device-Typ-Whitelist).
- [ ] **`templates/navigation.html`** „Faults"-Link.
- [ ] **NEU `tests/integration/
  test_m5_welle_6a_fault_smoke.py`** mit:
  - POST mit ungueltigem `target_device_id` → 422.
  - POST mit Battery+`voltage_drop` → 422
    (Whitelist-Verletzung).
  - POST mit Battery+`cell_failure` → 201.
  - Lifespan-Demo-Run nach N Ticks: Battery-
    Alarm in AlarmHistoryBuffer.
- [ ] **Welle-5-Smoke Hash-Pin** auf neuen
  `gg-demo.yaml`-Stand aktualisiert (1 Zeile).
- [ ] **`make test-unit`** gruen (kein Regress vs
  1681).
- [ ] **`make test-integration`** gruen mit dem
  neuen Welle-6a-Smoke (58 statt 57).
- [ ] **`make arch-check`** alle Contracts kept.
- [ ] **`make typecheck`** gruen.
- [ ] **`make gates`** cache-frei gruen ohne
  Override.
- [ ] **`make docs-check`** cache-frei gruen.
- [ ] **`make demo`** zeigt YAML-Faults im Dashboard
  reproduzierbar (manuelle Verifikation).
- [ ] **`GG-UI-007 + GG-DEMO-006`** erfuellt;
  Welle-1-Stub-Antwort (201+uuid) bleibt im POST-
  Handler.
- [ ] **`M5-ui-demo.md §3.1 Welle-Status-Tabelle`**
  Welle-6a-Zeile NEU eingefuegt (Sub-Slicing-
  Folge); Welle-6-Aggregat-Zeile entweder gestrichen
  oder als Klammer fuer 6a/6b/6c umformuliert.
- [ ] **`in-progress/README.md`** Welle-6a-Closure-
  Block + Welle-6b-Aktive-Welle-Marker.
- [ ] **`roadmap.md`** Welle-6a-Closure-Entry +
  Welle-6b-Forward-Pointer.
- [ ] **Top-Level-Doku-Sync** (`README.md` +
  `README.de.md` Test-Counts + GG-UI-007/DEMO-006-
  Bullet).
- [ ] **NEU C4 Self-Close-Move + Cross-Doc-Refs-
  Sync** als zwei separate Folge-Commits nach C3
  (Wave-Self-Close-Commit-Konvention; Pattern analog
  Welle-5 `da8d728`/`2c9d8da`).

**Anti-Scope-Verifikation (Welle 6a NICHT):**

- [ ] Keine Dynamic-FaultPort-Mutation im POST-
  Handler (Decision 19; Welle-1-Stub-Antwort bleibt
  semantisch unveraendert, nur Validation kommt
  davor).
- [ ] Kein eigener FaultPort-Adapter unter
  `adapters/driven/fault_*/`.
- [ ] Kein `GG-UI-006` Geraete-Grafik (Welle 6b).
- [ ] Kein `GG-UI-008` Sim-Zustand-Dashboard
  (Welle 6b).
- [ ] Kein `GG-DEMO-008` Abnahmedoku (Welle 6c).
- [ ] Kein C1-ADR-Commit (kein neuer Port, kein
  neuer Vertrag).
- [ ] Keine Multi-Run-Fault-Submission (Welle-5-
  Anti-Scope Multi-Run-Driver-Registry bleibt).

---

## References

- [`M5-ui-demo.md`](M5-ui-demo.md) §3.2 Welle 6
  Plan-Items (kanonische Sub-Slicing-Aufnahme; Welle-
  6a Fault-Flow-Sub-Bereich).
- [`../done/M5-welle-5.md`](../done/M5-welle-5.md)
  §1.3 + §10.1 — Welle-5-Anti-Scope-Erbschaft fuer
  `GG-DEMO-006` und `GG-DEMO-008` (in Welle-6-Defer
  per Folge-Entscheid 2026-06-03).
- [`../done/M5-welle-4b.md`](../done/M5-welle-4b.md)
  — Welle-4b-Alarm-Pipeline (Welle-6a-Demo-Faults
  nutzen sie unveraendert; Decision-19-YAML-side-
  Begruendung).
- [`../../adr/0022-fault-injection-protocol.md`](../../adr/0022-fault-injection-protocol.md)
  — FaultPort-Protocol + TickLoop-Vor-Tick-Hook-Vertrag.
- [`../../adr/0025-fault-recovery-pattern.md`](../../adr/0025-fault-recovery-pattern.md)
  — Welle-2-Fault-State-Modell + Recovery-Engine
  (BatteryFaultAdapter/GridFaultAdapter).
- [`../../adr/0021-scenario-loader-and-tick-loop-event-wiring.md`](../../adr/0021-scenario-loader-and-tick-loop-event-wiring.md)
  — Scenario-Loader + `TickLoopWiring.fault_port`-Slot.
- [`../../../../spec/lastenheft.md §17 + §24`](../../../../spec/lastenheft.md)
  `GG-UI-007` + `GG-DEMO-006` Akzeptanztexte.
- Pattern-Vorbild **Sub-Slicing-Beschluss**:
  [`../done/M4-welle-6a.md`](../done/M4-welle-6a.md)
  §0 (Welle 6 → 6a Cross-Adapter + 6b IEC-61850-
  Hardening).
- Pattern-Vorbild **Welle-ohne-C1**:
  [`../done/M5-welle-5.md`](../done/M5-welle-5.md)
  + Welle-5-Slice-Doc §4 C1 (bewusst entfaellt;
  kein neuer Port, kein neuer Vertrag).
