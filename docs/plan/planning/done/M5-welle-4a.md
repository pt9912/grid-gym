# Welle 4a — M5 Replay-Controls + TickLoop-Wiring

**Status:** Done 2026-06-02 — Liefer-Stack:
Pre-C0a `4517f51` (Self-Close-Move M5-welle-3.md → done/,
rename-only) + Pre-C0b `79c9712` (Cross-Doc-Refs-Sync,
4 Files) + C0 `3544dee` (Slice-Doc + Decisions 12/13/14) +
C1 `f1284c4` (NEU ADR 0039 `Proposed`) + C2 `9c188e0`
(RunStatus + RunRepository-Extension + TickLoop-Control-
Surface + 2 Endpoint-Wirings + TickLoopRegistry + UI-Page
+ Demo-Driver; +24 Unit + 1 Integration = 1650 unit + 50
integration; 10/10 A-1-Gates gruen) + C3 (dieser Commit;
ADR 0039 `Proposed → Provisional` + Status/DoD-Sync +
Top-Level-Doku-Sync).

Welle 4a ist die **Replay-Controls-Welle** in M5 und der
erste Sub-Slice einer **scope-induzierten Welle-4-
Subdivision** (4a Replay-Controls + 4b Alarme; Pattern
analog M4-Welle-5a/5b und M4-Welle-6a/6b). Welle 4a
erfuellt **`GG-UI-004` (Replay-Controls)** + den
Replay-Restcompletion-Anteil von **`GG-API-001`**
(`/runs/{id}/control` produktiv, nicht mehr Stub) +
einen Teil von **`GG-API-001`** „Status"-Akzeptanz
(`GET /runs/{id}/status`).

**Sub-Slice-Motivation (Welle-4-Subdivision):**

Die M5-ui-demo.md-Vorbelegung sah Welle 4 als monolithische
„Replay-Controls + Alarme"-Welle vor. M5-Welle-4-C0-Pre-
Research deckte zwei distinkte Architektur-Concerns auf,
die jeweils einen eigenen ADR + Decisions-Slot rechtfertigen:

- **Welle 4a (dieses Doc):** RunStatus-Tracking +
  TickLoop-Control-Surface + Replay-Controls-UI. NEU
  ADR 0039. 3 Decisions (12/13/14).
- **Welle 4b (folgt nach 4a-Self-Close-Move):** Alarm-
  Aggregation + AlarmStreamPort + Alarm-Tabelle-UI. NEU
  ADR 0040 (geplant). 2 Decisions (15/16, geplant).

Die Subdivision haelt C2-Code-Merges in handhabbarer
Groesse (Welle-3-C2 = 15 Files; ein monolithisches
Welle-4-C2 waere bei ~25-30 Files geendet) und trennt
zwei orthogonale Concerns (Run-Lifecycle vs Alarm-
Aggregation) sauber.

**Pre-C0 abgeschlossen (2 Commits):**

1. Pre-C0a `4517f51` — `git mv in-progress/M5-welle-3.md
   → done/` (rename-only). Pattern aus Memory
   `feedback_git_mv`.
2. Pre-C0b `79c9712` — Cross-Doc-Refs-Sync nach Move
   (4 Files: ADR 0038 + done/M5-welle-3.md +
   in-progress/M5-ui-demo.md + in-progress/README.md).
   `make docs-check` cache-frei gruen.

**Kein Pre-C0c (Probe-Run):** Das Cooperative-State-
Machine-Pattern fuer TickLoop-pause/resume/stop ist
seit M1 etabliert (synchroner `tick()`-Aufruf;
Guard-Check vor jedem Tick) und braucht keine
Architektur-Sondierung. Welle-1-HTMX-FastAPI-Probe
`9c20dad` + Welle-3-Asyncio-Pub/Sub-Probe `5349923`
decken die FastAPI-/HTMX-Mechanik bereits ab.

**Spec-Reife:** Inhaltlich final fuer Welle 4a. **Welle-
4a-Decision-Liste** (§3) sammelt drei NEU Decisions:

- **NEU Decision 12 (RunStatus-Tracking-Architektur)** —
  RunRepository-Extension mit `update_status` +
  `get_status`; NEU `RunStatus`-Literal-Alias
  (`pending`/`running`/`paused`/`stopped`/`completed`;
  Welle-1-`RunState`-Vokabel-aligned — C2-Realization-
  Anpassung gegenueber dem Slice-Doc-Original
  `idle`/`ended`).
- **NEU Decision 13 (TickLoop-Control-Surface)** —
  Cooperative state-machine mit konsolidierter
  `request(action)`-Methode (C2-Realization-Anpassung
  statt der Slice-Doc-Original-3-`request_pause`/
  `request_resume`/`request_stop` aus
  `PLR0904 max-public-methods=12`-Bestand); Guard vor
  `tick()`.
- **NEU Decision 14 (Replay-Status-Update-Pattern)** —
  HTMX-Polling auf `GET /runs/{id}/status` (1s-Trigger);
  WS-Surface bleibt fuer High-Frequency-Telemetry
  reserviert.

**C2-Realization-Notes (Welle-4a-C3-Sync):**

C2-Code-Merge `9c188e0` zog gegenueber dem C0-Slice-Doc-
Original vier produktive Anpassungen ein, die alle in
C3 (dieser Commit) dokumentiert sind:

1. **RunStatus-Vokabel** auf `pending`/`completed`
   umgestellt (statt `idle`/`ended`), weil Welle-1 das
   `RunState`-Literal in `_schemas.py` bereits mit
   diesen Werten ausgeliefert hat. Domain owns the
   type — `_schemas.py:RunState` ist jetzt direkter
   Re-Export von `domain.run.RunStatus`. ADR 0039 §2.1
   in C3 nachgezogen.
2. **`request(action)`-Konsolidierung** statt 3
   separater `request_pause`/`_resume`/`_stop`-
   Methoden, weil TickLoop bereits 11 Public-Methoden/
   Properties hat und die Welle-4a-Decision-13-
   Erweiterung um 3 weitere die `PLR0904
   max-public-methods=12`-Schwelle riss. Eine einzige
   `request(action: ControlAction)`-Methode dispatched
   ueber eine Modul-Konstante `_CONTROL_ACTION_TRANSITIONS`
   (pro Action `(target_state, allowed_from)`-Paarung).
   PLR0904-Per-File-Ignore in `pyproject.toml` aus
   demselben Grund ergaenzt (Pattern analog
   `devices/*/model.py` + `grid_model/bilanz.py`).
3. **`configure_demo_run`-Auslagerung** aus `app.py`
   nach NEU `_demo_setup.py`, weil
   `AC-NO-GOD-UTILS max=5 public top-level functions`
   pro Modul gilt. `app.py` exportiert nur die drei
   `configure_*`-Injection-Punkte + `get_health` +
   `post_runs` (genau 5); `_demo_setup.py` kombiniert
   die drei zu einem Demo-Run-Bundle inkl. inline-
   `_DemoSimulationClock`.
4. **`AC-ADAPTER-PURE`-`ignore_imports`** in
   `pyproject.toml` verankert die Komposition-Root-
   Brueck-Erlaubnis fuer `_demo_setup.py` +
   `_tick_loop_registry.py` + `_tick_loop_driver.py`
   → `hexagon.core.simulation.{tick_loop,scheduler}`.
   ADR 0039 §2.2 Option C verwarf einen separaten
   `ControlPort` (YAGNI: Control-Flag triviales Enum-
   Triple, keine Substituierbarkeit noetig); die
   Hexagonal-Architektur-Ausnahme ist damit produktiv
   verankert. Andere Adapter-Pakete duerfen
   `simulation` weiterhin nicht touchen.

Substanziell hat sich keine Decision veraendert — die
Realization-Notes sind Nomenklatur- und Architektur-
Layering-Anpassungen, keine semantischen Bruchstellen.

---

## 1. Context

M5-Welle-3
([`../done/M5-welle-3.md`](../done/M5-welle-3.md)) hat das
Live-Telemetry-Dashboard produktiv geliefert mit NEU
`TelemetryStreamPort` + `InMemoryTelemetryStream`-Adapter
+ `DemoTelemetryGenerator` als **Stub-Producer**. Der
Demo-Generator publisht alle ~200ms ein synthetisches
TelemetryPoint-Bundle ohne Bezug zu einem echten Lauf —
Welle-3-Anti-Scope-Item: „Kein echtes TickLoop-Wiring
(Demo-Generator als Stub; **Welle 4 ersetzt**)". Welle 4a
loest dieses Versprechen ein.

### 1.1 Existierende Substanz (M5-Welle-1 + M5-Welle-3)

- **HTTP-API-Surface** (Welle 1, ADR 0037 `Provisional`):
  - `POST /runs/{run_id}/control` mit `ControlRequest`-
    Body (`action: ControlAction = Literal["pause",
    "resume", "stop"]`) — **Welle-1-Stub**: gibt
    `ControlResponse(accepted=True)` zurueck, ruft aber
    keine TickLoop-Methode (Welle-1-Code-Kommentar:
    „kein echtes TickLoop-Pause/Resume/Stop-Wiring
    (Welle 4)").
  - `RunRepositoryPort` mit `save`/`get_by_id`/`exists`
    (Welle 1, `GG-AR-PORT-DRN-003`). **Kein Status-
    Feld** in `RunMetadata` — Welle 4a fuegt es hinzu.
- **UI-Foundation** (Welle 2, ADR 0036 §6 Layout-Realisierung):
  - `ui_router` mit 2 Page-Routes + Live-Telemetry-
    Dashboard aus Welle 3 (`GET /runs/{id}/dashboard`).
  - HTMX 2.0.9 + Jinja2-Templates + Base-Layout.
- **TelemetryStreamPort** (Welle 3, ADR 0038
  `Provisional`):
  - `subscribe(run_id) -> AsyncIterator[TelemetryPoint]`
    + `publish(point)`.
  - `InMemoryTelemetryStream` produktiv mit asyncio-Pub/
    Sub + Drop-Oldest-Backpressure.
  - `DemoTelemetryGenerator` als Stub-Producer (Welle 4a
    behaelt ihn vorerst aktiv; Welle 5 ersetzt durch
    Scenario-getriebenes TickLoop-Publish).
- **TickLoop** (`hexagon/core/simulation/tick_loop.py`,
  seit M1; M6a-Welle-6a-Hardening produktiv):
  - Synchroner `tick() -> TickResult`-Aufruf; kein
    interner Run-Loop.
  - **Kein** internes Control-State-Feld (idle/running/
    paused/stopped/ended). Tick-Aufrufer (heute: Tests
    + Welle-5-Scenario-Runner geplant) treibt den Loop.
  - `from_snapshot(state, *, clock, random)` produktiv
    (Welle-6a-Pattern) — Snapshot-Resume-Faehigkeit.

### 1.2 Welle-4a-Lieferziel

1. **NEU `RunStatus`-Literal-Alias** in
   `hexagon/core/domain/run.py`: 5 Zustaende
   `idle`/`running`/`paused`/`stopped`/`ended`.
   Frozen-Dataclass-vertraeglich, keine Mutation an
   `RunMetadata` (Status liegt separat im Repository,
   nicht in der Lauf-Metadata-Frozen-Struktur).
2. **RunRepositoryPort-Extension** (`hexagon/ports/
   driven/run_repository.py`): zwei neue Methoden
   `update_status(run_id, status)` +
   `get_status(run_id) -> RunStatus`. Welle-1-Methoden
   (`save`/`get_by_id`/`exists`) bleiben unveraendert
   (Backward-Compat). `InMemoryRunRepository`-Test-
   Helper aus Welle 1 erweitert.
3. **NEU TickLoop-Control-Surface** in
   `hexagon/core/simulation/tick_loop.py`:
   - Internes `_control_state: RunStatus`-Feld; Default
     `idle` beim Konstruktor.
   - 3 neue Public-Methoden: `request_pause()`,
     `request_resume()`, `request_stop()`. Cooperative
     (kein Threading; nur Flag-Set).
   - `tick()`-Guard: wenn `_control_state == "paused"`,
     returnt eine NEU `TickResult.paused()` ohne Tick-
     Fortschritt; wenn `"stopped"` oder `"ended"`,
     wirft NEU `TickLoopStoppedError`; sonst normales
     Tick-Verhalten.
   - `request_resume()` aus `"paused"` flippt nach
     `"running"`; aus `"stopped"`/`"ended"` Idempotenz-
     Fehler (`TickLoopInvalidTransitionError`).
4. **NEU `GET /runs/{run_id}/status`-Endpoint** in
   `_runs_router.py`: gibt JSON
   `{sim_time_ms, tick_count, run_status}` zurueck.
   404 bei nicht-existentem Run (`GG-API-004`-Pattern).
   `tags=["runs"]` (`runs`-Cluster).
5. **`POST /runs/{run_id}/control`-Wiring** in
   `_runs_action_router.py`: ersetzt Welle-1-Stub durch
   echten Aufruf: liest `request.action`, ruft die
   passende `TickLoop.request_*`-Methode (ueber NEU
   `TickLoopRegistry`-Lookup `tick_loop_for(run_id)`),
   und propagiert das Resultat in `ControlResponse`.
   Bei Invalid-Transition: 409 Conflict mit
   `ErrorResponse(code="invalid_transition", ...)`.
6. **NEU `TickLoopRegistry`-Driving-Adapter** unter
   `adapters/driving/http_api/_tick_loop_registry.py`
   (Welle-4a-Stub: Single-Run-Demo-Setup; produktive
   Multi-Run-Implementation in Welle 5 mit Scenario-
   Loader). Hexagonal: kein neuer Driving-Port-Slot
   (analog ADR 0037 Decision API-2 fuer
   `UICommandPort` — UI/API holt den TickLoop direkt
   ueber Adapter-State, kein neuer Port-Vertrag).
7. **NEU UI-Page `GET /runs/{run_id}/control`** in
   `ui/routes.py` + `templates/control.html` +
   `_control_content.html`:
   - 3 HTMX-Buttons (Pause/Resume/Stop) mit
     `hx-post="/runs/{run_id}/control" hx-vals='{"action":
     "pause"}'` etc.
   - Status-Block mit
     `hx-get="/runs/{run_id}/status" hx-trigger="every
     1s" hx-target="#status"` (Polling-Pattern,
     Decision 14).
   - Anzeige: Sim-Zeit (ms), Tick-Zaehler, Run-Status
     (mit CSS-Klasse pro Zustand, analog Quality-Marker
     aus Welle 3).
8. **Demo-Wiring** im FastAPI-Lifespan:
   - Welle 4a erzeugt beim Startup einen `TickLoop`-
     Demo-Instance mit `run_id="demo-run-001"`,
     `tick_ms=100`, und einen asyncio-Task, der den
     `tick()` periodisch aufruft (`asyncio.sleep(0.1)`-
     Loop). Bei `paused`-Guard kein Fortschritt; bei
     `stopped` Task-Cancel.
   - Das ersetzt teilweise den Welle-3-Demo-Generator:
     der `DemoTelemetryGenerator` bleibt als parallel-
     Source aktiv, der **neue** Tick-Loop-Driver
     publisht zusaetzliche Tick-getriebene
     TelemetryPoints (echte `simulation_time_ms` aus
     `TickLoop._tick_count * tick_ms`).
9. **Unit-Tests** + Integration-Test:
   - `tests/unit/hexagon/core/simulation/test_tick_
     loop_control.py` (Welle-4a-State-Machine-Tests:
     6 Transitions + 2 Error-Cases).
   - `tests/unit/hexagon/core/domain/test_run_status.py`
     (Literal-Alias-Smoke; 1 Test).
   - `tests/unit/adapters/driving/http_api/test_runs_
     router.py` EDIT: 2 neue Tests fuer
     `/runs/{id}/status`-Endpoint.
   - `tests/unit/adapters/driving/http_api/test_runs_
     action_router.py` EDIT: bestehende `control`-Tests
     auf produktives Wiring umgestellt (vorher: nur
     `accepted=True`; jetzt: pruefen, dass Status-
     Update sichtbar wird).
   - `tests/unit/adapters/driving/ui/test_control_
     route.py` CREATE (3 Tests: full-page render,
     HTMX-partial, 404-on-missing-run).
   - `tests/integration/test_m5_welle_4a_replay_
     controls_smoke.py` CREATE: End-to-End-Smoke
     (Startup → GET /control-Page → POST pause →
     GET /status zeigt `paused` → POST resume → tick-
     count steigt wieder).

### 1.3 Welle-4a-Anti-Scope

Welle 4a liefert **nicht**:

- **Alarm-Aggregation + AlarmStreamPort + Alarm-Tabelle-
  UI.** Folgt in Welle 4b (NEU ADR 0040 geplant,
  Decisions 15/16).
- **Scenario-Loader + Multi-Run-TickLoopRegistry.** Das
  ist Welle 5 (Scenario-Editor + Demo-Pipeline). Welle
  4a liefert nur einen Single-Demo-Run im Lifespan.
- **Echte Run-Persistenz mit Status-Roundtrip.** Welle
  4a bleibt In-Memory (`InMemoryRunRepository`); Welle-
  6c-Postgres ist M3-Material.
- **Fault-Injection-UI.** `GG-UI-007` ist Welle 6.
- **Scenario-Editor.** `GG-UI-006..008` (ausser 004/005)
  ist Welle 5.
- **OTel-Span-Wrap fuer Control-Actions.** M6 oder
  separate Hardening-Welle.
- **Run-Start-Action (`POST /runs`).** Welle-1-Stub
  bleibt unveraendert (gibt UUID-Run zurueck ohne
  Scenario-Setup). Welle 5 wirt den Scenario-Loader an.

---

## 2. Scope

Welle 4a liefert in 4 Liefer-Commits (C0..C3, plus C1-
ADR):

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses
   Dokument + `in-progress/README.md`-Aktive-Welle-Block-
   Update.
2. **NEU ADR 0039 (Run-Control + RunStatus-Tracking)**
   (C1) — verankert Decisions 12/13/14 mit Status
   `Proposed`; Status-Pfad `Proposed → Provisional` nach
   C2-Code-Merge in C3.
3. **Code-Implementation + Unit/Integration-Tests** (C2)
   — alle 9 Sub-Items der §1.2-Liste.
4. **Status/DoD-Sync + ADR 0039 `Provisional` + Top-
   Level-Doku-Sync** (C3) — inkl. `M5-ui-demo.md §3`-
   Refactor (Welle 4 → Welle 4a + Welle 4b, Welle 4a
   abgehakt).

---

## 3. Architektur-Entscheidungen (Welle-4a-Decisions)

### 3.1 Decision 12 (RunStatus-Tracking-Architektur) — final fixiert

**Frage:** Wo lebt der in-flight `RunStatus`
(`idle`/`running`/`paused`/`stopped`/`ended`)? `RunMetadata`
ist `@dataclass(frozen=True)` und tracked nur
Reproduzierbarkeits-Metadaten (Scenario-Hash, Seed,
tick_ms etc.); ein mutables Status-Feld wuerde die
Frozen-Equality-Semantik brechen.

**Optionen:**

- **A: `RunMetadata.status` als mutables Feld** —
  Frozen-Dataclass aufgeben. Verworfen: bricht
  Welle-1-Snapshot-Equality-Tests und ADR-0007-Reproduktions-
  Garantie (`RunMetadata`-Hash muss stabil bleiben).
- **B: NEU separater `RunStatusPort`-Driven-Slot** —
  eigener Port nur fuer Status. Verworfen: YAGNI;
  Status braucht denselben Lifecycle wie Metadaten
  (gleicher `run_id`-Schluessel, gleicher Multi-Run-
  Lookup), separater Port erhoeht die Adapter-Komplexitaet
  ohne Vorteil.
- **C: RunRepository-Extension** (final) —
  zwei neue Methoden `update_status(run_id, status)` +
  `get_status(run_id) -> RunStatus`. `RunMetadata`
  bleibt unveraendert frozen. In-Memory-Implementation
  haelt ein Dict `{run_id: RunStatus}` neben dem
  Metadaten-Dict; Postgres-Implementation in M3 kriegt
  eine Spalte. Symmetrisch zur existierenden
  `exists(run_id)`-Lookup-API.
- **D: TickLoop-internes Feld + Lookup ueber Registry**
  — `RunStatus` lebt komplett im TickLoop. Verworfen:
  Restart-Persistenz unmoeglich (M3-Welle-6c-
  Postgres-Replay-Sicht braucht Status nach Crash);
  Decision 13 (TickLoop-Control-Surface) braucht
  trotzdem ein internes Mirror-Feld, das aber als
  **Cache** der Repository-Wahrheit fungiert.

**Entscheidung: Option C** — RunRepository-Extension.
TickLoop spiegelt das Feld intern fuer Tick-Guard-Hot-
Path (Performance: kein Repository-Read pro Tick); bei
`request_*`-Methoden ist der TickLoop verantwortlich, das
Repository nachzuziehen (`repo.update_status(run_id,
new_state)`).

**Konsequenz:** ADR 0039 verankert das Pattern als
Welle-4a-Sub-Decision 12. Hexagonal-Architektur bleibt
intakt (Driven-Port-Vertrag erweitert, kein neuer Port).

### 3.2 Decision 13 (TickLoop-Control-Surface) — final fixiert

**Frage:** Wie kommuniziert eine HTTP-getriebene Control-
Aktion (`POST /runs/{id}/control`) mit dem TickLoop?
TickLoop ist seit M1 synchron (`tick() -> TickResult`),
kein eingebauter Run-Loop oder Threading.

**Optionen:**

- **A: TickLoop bekommt einen internen Run-Loop +
  Threading + asyncio-Queue fuer Control-Messages** —
  bricht das Tick-Loop-Determinismus-Versprechen
  (`GG-SIM-001`) und macht Snapshot-Tests instabil.
  Verworfen.
- **B: Externer Run-Loop-Driver (FastAPI-Lifespan-
  asyncio.Task) ruft `tick()` periodisch; TickLoop
  bleibt sync mit Control-Flag-Guard** (final) —
  Cooperative state-machine, kein Threading,
  Determinismus bleibt. Pattern analog
  ADR 0023-`FaultPort`-Pre-Tick-Hook.
- **C: Control-Events via NEU `ControlPort`-Driven-
  Slot** — eigener Port nur fuer Pause-Events.
  Verworfen: YAGNI; das Control-Flag ist ein
  triviales Boolean-Triple und braucht keinen
  Adapter-Vertrag.

**Entscheidung: Option B** — Cooperative state-machine.

**Surface:**

- **Internes Feld** `_control_state: RunStatus` (Default
  `"idle"`).
- **Public-Methoden:**
  - `request_pause()` — flippt `running` → `paused`;
    aus `idle`/`paused`/`stopped`/`ended` Idempotenz-
    Fehler (`TickLoopInvalidTransitionError` mit aktueller
    + gewuenschter State).
  - `request_resume()` — flippt `paused` → `running`;
    aus `idle` zusaetzlich erlaubt (initialer Start);
    `stopped`/`ended` Idempotenz-Fehler.
  - `request_stop()` — flippt aus jedem aktiven State
    auf `stopped`; aus `ended` Idempotenz-Fehler.
- **Tick-Guard** vor jedem `tick()`-Body:
  - `"paused"` → NEU `TickResult.paused()` (kein
    Tick-Fortschritt; `_tick_count` bleibt; Snapshot
    bleibt stabil).
  - `"stopped"`/`"ended"` → NEU
    `TickLoopStoppedError`.
  - `"idle"` → behandelt wie `"running"` (initialer
    Tick; flippt das State auf `"running"` als Side-
    Effect, damit Folge-Ticks die Status-Persistenz
    korrekt setzen).
- **Repository-Mirror:** jede `request_*`-Methode ruft
  `repository.update_status(run_id, new_state)` BEVOR
  das interne Feld geflippt wird (atomare Sequenz fuer
  Read-Konsistenz aus `GET /runs/{id}/status`).

**Konsequenz:** TickLoop bleibt synchron + deterministisch.
Snapshot-Format aus ADR 0008 bleibt unveraendert
(`_control_state` ist Run-Lifecycle-State, nicht Tick-
State; wird beim `from_snapshot`-Resume **nicht** aus
dem Snapshot geladen, sondern auf `"running"` gesetzt
— Welle-6a-Pattern).

### 3.3 Decision 14 (Replay-Status-Update-Pattern) — final fixiert

**Frage:** Wie aktualisiert die UI den Status-Block
(Sim-Zeit, Tick-Zaehler, Run-Status)? Optionen:
HTMX-Polling vs WS-Subscription vs SSE.

**Optionen:**

- **A: HTMX-Polling** auf NEU `GET /runs/{id}/status`
  mit `hx-trigger="every 1s"` (final) — niedrigfrequente
  Status-Updates (1Hz reicht fuer Sim-Zeit-Anzeige);
  idempotente GET-Endpunkte; trivial zu testen
  (`TestClient.get(...)`); HTMX-natives Pattern.
- **B: WS-Subscription** auf NEU `/runs/{id}/status-
  stream` — overkill fuer 1Hz-Status; benoetigt
  zweite WS-Surface neben Telemetry-WS aus Welle 3.
  Verworfen.
- **C: Embedded in Telemetry-WS** — Status-Updates
  als spezielle TelemetryPoint-Sub-Kategorie.
  Verworfen: bricht ADR 0038 TelemetryPoint-
  Semantik (TelemetryPoint = Geraete-Messung, nicht
  Run-Lifecycle).

**Entscheidung: Option A** — HTMX-Polling mit
1s-Trigger.

**Konsequenz:** ADR 0038 (`TelemetryStreamPort`) bleibt
unangetastet; Welle 3 WS-Surface bleibt fuer High-
Frequency-Telemetry reserviert. Welle 4a fuegt einen
neuen REST-GET-Endpoint hinzu (`GET /runs/{id}/status`),
der das `OpenAPI`-Schema erweitert.

---

## 4. Liefer-Reihenfolge (4 Commits)

### Pre-C0 — bereits erledigt

- Pre-C0a `4517f51` (Self-Close-Move; rename-only).
- Pre-C0b `79c9712` (Cross-Doc-Refs-Sync, 4 Files).

### C0 — `docs(plan)`: M5-welle-4a Slice-Doc

Slice-Doc-Anlage (dieses Dokument) +
`in-progress/README.md`-Aktive-Welle-Block-Update
(Welle-3-Abschluss bereits in Pre-C0b finalisiert;
C0 ergaenzt nur den Bestand-Tabellen-Eintrag und
flippt den Aktive-Welle-Marker auf Welle 4a-C0).

### C1 — `docs(adr)`: NEU ADR 0039 (Run-Control + RunStatus-Tracking)

Erzeugt `docs/plan/adr/0039-run-control-and-status-
tracking.md` (~280 Zeilen) mit Status `Proposed`:

- §1 Context — `GG-API-001` Replay-Steuerung-Pflicht +
  Welle-1-Stub-Notiz + Welle-3-Demo-Generator-Anti-Scope.
- §2 Decisions:
  - §2.1 Decision 12 (Status-Tracking via
    Repository-Extension).
  - §2.2 Decision 13 (Cooperative TickLoop-State-
    Machine).
  - §2.3 Decision 14 (HTMX-Polling fuer Status).
- §3 Konsequenzen — Snapshot-Format unveraendert,
  Welle-4b-Forward-Pointer fuer `AlarmStatus`-
  Persistenz-Symmetrie.
- §4 Alternativen-Diskussion (jeweils warum verworfen).
- §5 Status-Pfad (`Proposed → Provisional` mit C3
  nach C2-Code-Merge; `Accepted` mit M5-Welle-7).
- §6 Bezuege: `GG-API-001`, `GG-SIM-001`, `GG-AR-PORT-
  DRN-003`, ADR 0007 (Reproduzierbarkeit), ADR 0008
  (Snapshot), ADR 0023 (FaultPort-Pre-Tick-Hook-Pattern,
  Cooperative-State-Vorlaeufer), ADR 0037 (HTTP-API-
  Surface), ADR 0038 (TelemetryStreamPort-Symmetrie).
- §7 References — Welle-4a-Slice-Doc; Probe-Vorlaufer
  Welle-1 `9c20dad`.

Plus `docs/plan/adr/README.md`-Tabellen-Zeile fuer 0039
(Status `Proposed` mit Commit-Hash-Verweis auf C1-
Commit).

### C2 — `feat(welle-4a)`: RunStatus + TickLoop-Control + Endpoints + UI + Tests

Liefert alle 9 Sub-Items der §1.2-Liste:

1. NEU `RunStatus`-Literal-Alias in `hexagon/core/
   domain/run.py` + Re-Export aus `hexagon/core/
   domain/__init__.py`.
2. RunRepositoryPort-Extension (`update_status` +
   `get_status`) + InMemoryRunRepository-Update.
3. TickLoop-Control-Surface (`_control_state` +
   `request_pause`/`request_resume`/`request_stop` +
   Tick-Guard + `TickResult.paused()`-Factory + NEU
   Errors `TickLoopStoppedError` +
   `TickLoopInvalidTransitionError`).
4. NEU `GET /runs/{run_id}/status`-Endpoint in
   `_runs_router.py` + NEU `RunStatusResponse`-
   Pydantic-Model in `_schemas.py`.
5. POST `/runs/{run_id}/control`-Wiring in
   `_runs_action_router.py` (ersetzt Stub durch
   TickLoopRegistry-Lookup + `request_*`-Call +
   Error-Mapping 409 fuer Invalid-Transition).
6. NEU `TickLoopRegistry`-Driving-Adapter unter
   `adapters/driving/http_api/_tick_loop_registry.py`
   (Single-Run-Stub fuer Welle 4a; produktive Multi-
   Run-Variante in Welle 5).
7. NEU UI-Page `GET /runs/{run_id}/control` in
   `ui/routes.py` + `templates/control.html` +
   `_control_content.html` mit 3 HTMX-Buttons +
   Status-Polling-Block.
8. Demo-Wiring in `app.py`-Lifespan: erzeugt einen
   Demo-TickLoop + Tick-Driver-Task; bei Shutdown
   sauberes Task-Cancel + RunStatus → `ended`.
9. Unit-Tests + Integration-Test (siehe §1.2.9).

Plus CSS-Klassen-Erweiterung in `style.css` fuer
RunStatus-Visualisierung (5 Klassen analog Welle-3-
Quality-Marker-Pattern).

### C3 — `docs(plan|adr)`: Welle-4a Status/DoD-Sync + Top-Level-Doku-Sync

Status-/DoD-Sync nach C2-Code-Merge:

- `M5-welle-4a.md §0 Status` von `In Progress → Done` mit
  Liefer-Hashes (C0/C1/C2/C3) + DoD-Verifikation.
- **`M5-ui-demo.md §3 Welle 4` Refactor:** Section in
  `Welle 4a — Replay-Controls + TickLoop-Wiring (Done
  YYYY-MM-DD)` + `Welle 4b — Alarme (Pending)` aufgeteilt;
  Welle 4a abgehakt.
- `M5-welle-4a.md §9 DoD-Checkliste` Items abhaken.
- ADR 0039 `Proposed → Provisional` mit C2-Code-Merge-
  Beleg + Welle-4a-Lieferung-Detail im §1.
- Top-Level-Doku-Sync:
  - `docs/plan/planning/in-progress/roadmap.md §3 M5`
    aktualisiert mit Welle-4a-Bullet-Belegung; ADR-
    Status-Update.
  - `docs/plan/planning/in-progress/README.md` —
    Welle-4a-Abschluss-Block + Welle-4b-aktiv-Marker.
  - `README.md` + `README.de.md` — Test-Counts
    aktualisiert; Slice-Liste.

## 5. Critical Files

| Datei                                                                                | Phase | Aktion                                                                |
| ------------------------------------------------------------------------------------ | ----- | --------------------------------------------------------------------- |
| `docs/plan/planning/in-progress/M5-welle-4a.md`                                      | C0    | CREATE (dieses Dokument)                                              |
| `docs/plan/planning/in-progress/README.md`                                           | C0    | EDIT (Bestand-Zeile + Aktive-Welle-Marker auf 4a-C0)                  |
| `docs/plan/adr/0039-run-control-and-status-tracking.md`                              | C1    | CREATE (NEU ADR; Status `Proposed`)                                   |
| `docs/plan/adr/README.md`                                                            | C1    | EDIT (Tabellen-Zeile fuer 0039)                                       |
| `src/grid_gym/hexagon/core/domain/run.py`                                            | C2    | EDIT (`RunStatus`-Literal-Alias hinzu)                                |
| `src/grid_gym/hexagon/core/domain/__init__.py`                                       | C2    | EDIT (Re-Export `RunStatus`)                                          |
| `src/grid_gym/hexagon/ports/driven/run_repository.py`                                | C2    | EDIT (`update_status` + `get_status` Methoden)                        |
| `src/grid_gym/hexagon/core/simulation/tick_loop.py`                                  | C2    | EDIT (`_control_state` + `request_*` Methoden + Tick-Guard)           |
| `src/grid_gym/hexagon/core/errors.py`                                                | C2    | EDIT (NEU `TickLoopStoppedError` + `TickLoopInvalidTransitionError`)  |
| `src/grid_gym/adapters/driving/http_api/_runs_router.py`                             | C2    | EDIT (`GET /runs/{id}/status`-Endpoint)                               |
| `src/grid_gym/adapters/driving/http_api/_runs_action_router.py`                      | C2    | EDIT (`POST /runs/{id}/control`-Wiring)                               |
| `src/grid_gym/adapters/driving/http_api/_schemas.py`                                 | C2    | EDIT (`RunStatusResponse`-Model + 409-Error-Variant)                  |
| `src/grid_gym/adapters/driving/http_api/_tick_loop_registry.py`                      | C2    | CREATE (Single-Run-Demo-Registry)                                     |
| `src/grid_gym/adapters/driving/http_api/app.py`                                      | C2    | EDIT (Lifespan-Demo-TickLoop + Tick-Driver-Task)                      |
| `src/grid_gym/adapters/driving/ui/templates/control.html`                            | C2    | CREATE (Replay-Controls-Page)                                         |
| `src/grid_gym/adapters/driving/ui/templates/_control_content.html`                   | C2    | CREATE (HTMX-Partial)                                                 |
| `src/grid_gym/adapters/driving/ui/routes.py`                                         | C2    | EDIT (neue Page-Route `/runs/{id}/control`)                           |
| `src/grid_gym/adapters/driving/ui/static/style.css`                                  | C2    | EDIT (RunStatus-Klassen)                                              |
| `tests/unit/hexagon/core/domain/test_run_status.py`                                  | C2    | CREATE                                                                |
| `tests/unit/hexagon/core/simulation/test_tick_loop_control.py`                       | C2    | CREATE (6 Transitions + 2 Error-Cases)                                |
| `tests/unit/adapters/driving/http_api/test_runs_router.py`                           | C2    | EDIT (+2 Tests fuer `/status`)                                        |
| `tests/unit/adapters/driving/http_api/test_runs_action_router.py`                    | C2    | EDIT (control-Tests auf produktives Wiring umgestellt)                |
| `tests/unit/adapters/driving/ui/test_control_route.py`                               | C2    | CREATE (3 Tests)                                                      |
| `tests/integration/test_m5_welle_4a_replay_controls_smoke.py`                        | C2    | CREATE (End-to-End-Smoke)                                             |
| `docs/plan/planning/in-progress/M5-ui-demo.md`                                       | C3    | EDIT (§3 Welle 4 → Welle 4a + Welle 4b; 4a Status/DoD-Boxen)          |
| `docs/plan/planning/in-progress/roadmap.md`                                          | C3    | EDIT (§3 M5-Welle-4a-Bullet)                                          |
| `docs/plan/planning/in-progress/README.md`                                           | C3    | EDIT (Welle-4a-Abschluss + Welle-4b-aktiv)                            |
| `README.md` + `README.de.md`                                                         | C3    | EDIT (Test-Counts + Slice-Liste)                                      |

## 6. Verifikationspfad

**Welle-4a-DoD:**

1. `M5-welle-4a.md` produktiv mit §1-§9.
2. **NEU ADR 0039** mit Status `Proposed → Provisional`
   nach C2.
3. **NEU `RunStatus`-Literal-Alias** in `hexagon/core/
   domain/run.py`.
4. **RunRepositoryPort-Extension** mit `update_status` +
   `get_status`; `InMemoryRunRepository`-Test-Helper
   aktualisiert.
5. **TickLoop-Control-Surface** produktiv (`request_*`-
   Methoden + Tick-Guard).
6. **NEU `GET /runs/{id}/status`-Endpoint** mit
   `RunStatusResponse`-Schema.
7. **POST `/runs/{id}/control`-Wiring** produktiv (kein
   Stub mehr).
8. **NEU `TickLoopRegistry`-Adapter** unter `adapters/
   driving/http_api/`.
9. **NEU UI-Page `GET /runs/{id}/control`** produktiv.
10. **Lifespan-Demo-TickLoop** wird beim Startup
    erzeugt + getrieben.
11. **Unit-Tests** (~12 neue) + **Integration-Test**
    (1 neuer).
12. `make test-unit` gruen (1626 + ~12 = ~1638).
13. `make test-integration` gruen (49 + 1 = 50).
14. `make arch-check` 20/20 KEPT.
15. `make typecheck` mit `strict_bytes` gruen.
16. `make gates` cache-frei gruen ohne Override.
17. `make docs-check` cache-frei gruen.
18. `make openapi-validate` cache-frei gruen.

**Welle-4a-Gate:** `make gates` + `make docs-check` +
`make openapi-validate` cache-frei gruen ohne Override.

## 7. Risiken

- **TickLoop-Control-State-Race bei async Tick-Driver
  + sync `request_*`.** Wenn der Lifespan-asyncio-Task
  gerade `tick()` ausfuehrt, koennte ein `request_pause`-
  Aufruf mid-tick laufen. Mitigation: `request_*`-
  Methoden setzen nur das Flag (Atomic-Write); der
  Guard greift erst **vor** dem naechsten `tick()`,
  nicht mid-tick. Dokumentiert in ADR 0039 §3.
- **Demo-TickLoop-Lifespan-Cleanup.** Analog
  Welle-3-Demo-Generator: wenn der Tick-Driver-Task
  beim Shutdown nicht sauber gecanceled wird, leakt er.
  Mitigation: FastAPI-`lifespan`-Context mit
  expliziter `task.cancel()` + `await task` + RunStatus
  → `ended` Update. Welle-3-Pattern wiederverwendet.
- **RunStatus-Status-Polling-Last (HTMX every 1s).**
  Bei mehreren UI-Tabs koennten mehrere Polling-Requests
  parallel laufen. Mitigation: Welle 4a beobachtet
  Single-Demo-Run; produktive Multi-Run-Skalierung ist
  Welle-5-Verantwortung. Performance-Note in ADR 0039.
- **Snapshot-Format-Compat mit `_control_state`.**
  `from_snapshot` (Welle-6a-Pattern) muss `_control_state`
  korrekt initialisieren. Entscheidung in Decision 13:
  Resume aus Snapshot setzt State auf `"running"`
  (statt aus Snapshot-State zu rekonstruieren). Welle-
  6a-Pattern: `_control_state` ist Run-Lifecycle, nicht
  Tick-Determinism — gehört nicht in den Snapshot.
- **Invalid-Transition-Error-Mapping auf 409 vs 422.**
  HTTP-Konvention: 409 = Conflict (Resource-State-
  Konflikt), 422 = Unprocessable Entity (Validation-
  Fehler). Pause auf bereits-`ended`-Run ist
  Resource-State-Konflikt → 409. Dokumentiert in
  `GG-API-004`-Error-Code-Liste.
- **Backward-Compat fuer Welle-1-`control`-Stub-Tests.**
  Welle-1-Tests fuer `POST /runs/{id}/control`
  pruefen nur `accepted=True`. Welle 4a aendert das
  Verhalten — die Tests muessen aktualisiert werden
  (statt geloescht, weil die Endpoint-Surface gleich
  bleibt). C2-EDIT, nicht C2-CREATE.

## 8. Wandert nach

- Bei C3-Closure: `M5-welle-4a.md` bleibt in
  `in-progress/` (Pattern analog Welle 1+2+3). Self-
  Close-Move folgt als M5-Welle-4b-Pre-C0.
- `M5-ui-demo.md` bleibt in `in-progress/` bis
  M5-Welle-7-Closure.
- Welle 4b (Alarme: Aggregation + AlarmStreamPort +
  Alarm-Tabelle-UI) als naechster aktiver Schritt nach
  Welle 4a; NEU ADR 0040 geplant mit Decisions 15/16.
- Welle 5 (Demo-Pipeline + Scenario-Loader) ersetzt den
  Single-Run-Demo-TickLoop durch Multi-Run-Scenario-
  Setup; `TickLoopRegistry` wird produktiv.

## 9. DoD-Checkliste (mit C3 abgehakt)

- [x] **NEU ADR 0039 `Proposed → Provisional`** mit
  C2-Code-Merge-Beleg `9c188e0`.
- [x] **NEU `RunStatus`-Literal-Alias** in
  `hexagon/core/domain/run.py` mit 5 Welle-1-aligned-
  Werten (`pending`/`running`/`paused`/`stopped`/
  `completed`); `_schemas.py:RunState` als
  Re-Export-Alias.
- [x] **RunRepositoryPort-Extension** mit
  `update_status` + `get_status`; InMemory-Helper
  + `PostgresRunRepository`-Stub
  (`NotImplementedError` mit M3-Welle-6c-Forward-
  Pointer) aktualisiert; Welle-1-Methoden
  (`save`/`get_by_id`/`exists`) unveraendert.
- [x] **TickLoop-Control-Surface** produktiv:
  `_control_state` + `control_state`-Property +
  konsolidierte `request(action: ControlAction)`-
  Methode (Konsolidierung statt 3 `request_*` aus
  `PLR0904`-Bestand; siehe C2-Realization-Notes §0)
  + Pre-Tick-Guard + `TickResult.paused_result(...)`-
  Classmethod + NEU `TickLoopStoppedError` +
  `TickLoopInvalidTransitionError`.
- [x] **`GET /runs/{id}/status`** produktiv mit
  `RunStatusResponse`-Schema + OpenAPI-Eintrag
  (Welle-1-Stub aus `_runs_router.py` produktiv
  ausgewirt — kein NEU-Endpoint, sondern Wiring auf
  RunRepository + TickLoopRegistry).
- [x] **POST `/runs/{id}/control`-Wiring** produktiv;
  Welle-1-Stub-Verhalten abgeschafft; 409 bei Invalid-
  Transition; 503 bei `tick_loop_not_active`.
- [x] **NEU `TickLoopRegistry`-Adapter** unter
  `adapters/driving/http_api/_tick_loop_registry.py`.
- [x] **NEU UI-Page `GET /runs/{run_id}/control`** mit
  3 HTMX-POST-Buttons + 1s-Status-Polling-Block +
  Inline-JSON-Encoding-Helper (HTMX-default form-encodes;
  Welle-1-`ControlRequest` erwartet JSON).
- [x] **RunStatus-CSS-Klassen** (5 Zustaende) in
  `style.css` (Color-Schema pro State + Button-Styling).
- [x] **Lifespan-Demo-TickLoop** + Tick-Driver-Task
  produktiv via NEU `_demo_setup.py:configure_demo_run`
  (Auslagerung aus `app.py` wegen
  `AC-NO-GOD-UTILS max=5 public top-level functions`;
  siehe C2-Realization-Notes §0); sauberes Shutdown-
  Task-Cancel.
- [x] **Unit-Tests** (24 neue) — Domain (`test_run_
  status.py` 2) + TickLoop-Control-State-Machine
  (`test_tick_loop_control.py` 13) + `/status`-Wiring
  (`test_runs_router.py` +2) + `/control`-Wiring
  (`test_runs_action_router.py` +3) + UI-Route
  (`test_control_route.py` 3) + Welle-1-Smoke
  Anpassungen.
- [x] **Integration-Test**
  `test_m5_welle_4a_replay_controls_smoke.py` produktiv
  (End-to-End-Workflow: Run + TickLoop + pause/resume/
  stop ueber HTTP + Status-Polling + UI-Page-Render).
- [x] **`make test-unit`** gruen: **1650 passed** (+24
  vs Welle-3-Endstand 1626).
- [x] **`make test-integration`** gruen: **50 passed**
  + 4 skipped (+1 vs Welle-3-Endstand 49).
- [x] **`make arch-check`** 20/20 KEPT (keine neuen
  Ports — Repository-Extension; NEU `AC-ADAPTER-PURE`-
  `ignore_imports`-Block fuer `_demo_setup.py` +
  `_tick_loop_registry.py` + `_tick_loop_driver.py` →
  `hexagon.core.simulation.{tick_loop,scheduler}` als
  Komposition-Root-Brueck-Erlaubnis verankert ADR 0039
  §2.2 Option C produktiv).
- [x] **`make typecheck`** mit `strict_bytes` gruen
  (kein `# type: ignore`).
- [x] **`make gates`** cache-frei gruen ohne Override
  (10/10 A-1-Gates).
- [x] **`make docs-check`** cache-frei gruen.
- [x] **`make openapi-validate`** cache-frei gruen
  (`/control`-UI-Route mit `tags=["ui"]`).
- [x] **`GG-UI-004` (Replay-Controls)** erfuellt durch
  Control-Page + Pause/Resume/Stop-Buttons +
  Status-Anzeige (Sim-Zeit + Tick-Counter + Run-State).
- [x] **`GG-API-001` (Replay-Restcompletion)** erfuellt
  durch `POST /control`-Wiring + `GET /status`-Wiring.
- [x] **C3-Top-Level-Doku-Sync** produktiv: 8 Docs auf
  Welle-4a-Closure-Stand (`M5-welle-4a.md §0/§9`,
  `M5-ui-demo.md §3 Welle 4 → Welle 4a + Welle 4b`,
  `in-progress/README.md`, `in-progress/roadmap.md §3
  M5`, `README.md` + `README.de.md`-Test-Counts + ADR
  0039 + `docs/plan/adr/README.md`).

**Anti-Scope-Verifikation (Welle 4a NICHT):**

- [x] Keine Alarm-Aggregation / AlarmStreamPort / Alarm-
  Tabelle-UI (Welle 4b).
- [x] Kein Scenario-Loader / Multi-Run-Registry (Welle 5).
- [x] Keine Postgres-Status-Persistenz (M3-Welle-6c;
  `PostgresRunRepository.update_status`/`get_status`
  werfen `NotImplementedError` mit Forward-Pointer).
- [x] Kein Fault-Injection-UI (Welle 6).
- [x] Kein OTel-Span-Wrap fuer Control-Actions (M6).
- [x] Keine `noqa`-Marker.

---

## References

- [`../done/M5-welle-3.md`](../done/M5-welle-3.md) —
  Welle-3-Closure (Live-Telemetry-Dashboard;
  TelemetryStreamPort + Demo-Generator als Stub-Producer,
  den Welle 4a um echte Tick-Loop-Wiring ergaenzt).
- [`../done/M5-welle-1.md`](../done/M5-welle-1.md) —
  Welle-1-HTTP-API-Surface (`POST /runs/{id}/control`-
  Stub, den Welle 4a produktiv wirt).
- [`../done/M5-welle-0.md`](../done/M5-welle-0.md) §3
  Decision 4 (Replay-Controls-API-Vertrag bereits
  final via ADR 0037 Decision API-1; Welle 4a nutzt
  ohne Aenderung).
- [`M5-ui-demo.md`](M5-ui-demo.md) §3 Welle
  4 (kanonische Slice-Spezifikation; Welle-4a-C3 refactort
  die Section in 4a + 4b).
- [`../../adr/0037-http-api-surface-pattern.md`](../../adr/0037-http-api-surface-pattern.md)
  §2.1 Decision API-1 (POST-mit-Action-Body; Welle 4a
  wirt die produktive Logik).
- [`../../adr/0038-telemetry-stream-port.md`](../../adr/0038-telemetry-stream-port.md)
  §2 (TelemetryStreamPort als Welle-3-Vorlaeufer; Welle
  4a fuegt einen zweiten REST-GET-Status-Endpunkt hinzu,
  kein zweiter Stream).
- [`../../../../spec/lastenheft.md §16`](../../../../spec/lastenheft.md)
  (`GG-API-001` Replay-Steuerung-Pflicht).
- [`../../../../spec/lastenheft.md §17`](../../../../spec/lastenheft.md)
  (`GG-UI-004` Replay-Controls-Akzeptanz).
- M5-Welle-Pattern-Vorbilder:
  [`../done/M5-welle-1.md`](../done/M5-welle-1.md)
  (Surface-Foundation),
  [`../done/M5-welle-3.md`](../done/M5-welle-3.md)
  (Port + Adapter + UI in einer Welle).
- Sub-Wellen-Subdivision-Pattern:
  [`../done/M4-welle-5a.md`](../done/M4-welle-5a.md) +
  [`../done/M4-welle-5b.md`](../done/M4-welle-5b.md)
  (zwei-Library-DNP3 + Smoke-Hardening) und
  [`../done/M4-welle-6a.md`](../done/M4-welle-6a.md) +
  [`../done/M4-welle-6b.md`](../done/M4-welle-6b.md)
  (Mainstream + IEC-61850-Lizenz-Hardening).
