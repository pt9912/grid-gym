# ADR 0039 — Run-Control + RunStatus-Tracking (M5 Welle 4a)

**Status:** Provisional — angelegt 2026-06-02 mit M5-Welle-4a-
C1 `f1284c4` (Status `Proposed`); auf `Provisional` gezogen
2026-06-02 mit M5-Welle-4a-C3 (dieser Commit) nach C2-Code-
Merge `9c188e0` (RunStatus-Literal-Alias + RunRepository-
Extension + TickLoop-Control-Surface mit konsolidierter
`request(action)`-Methode + 2 Endpoint-Wirings auf
existierenden Welle-1-Stubs + NEU `TickLoopRegistry`-Adapter
+ NEU `DemoTickLoopDriver` + NEU UI-Page `GET /control` +
NEU `_demo_setup.py`-Komposition-Root; +24 Unit + 1
Integration = 1650 unit + 50 integration Tests gruen; 10/10
A-1-Gates ohne Override). Die ADR verankert die Replay-
Controls-Architektur fuer die `POST /runs/{id}/control`-
Wiring-Welle und schliesst drei NEUE Decisions (12/13/14)
aus dem Welle-4a-Slice-Doc. Sie definiert eine **Driven-
Port-Extension** (`RunRepositoryPort.update_status` +
`get_status`) plus eine **TickLoop-interne Cooperative-
State-Machine** (`_control_state` + `request(action)` +
Pre-Tick-Guard) plus ein **HTMX-Polling-Pattern** fuer den
UI-Status-Block (`GET /runs/{id}/status` mit 1s-Trigger).

**Datum:** 2026-06-02 (M5-Welle-4a-C1 `f1284c4` → C3 dieser
Commit)

**Bezug:**

- [`ADR 0007`](0007-random-port.md)
  (`RandomPort` als Reproduzierbarkeits-Foundation;
  `RunMetadata.seed` belegt das produktiv —
  `RunMetadata` ist `@dataclass(frozen=True)` und
  braucht stabile Equality, weshalb der RunStatus aus
  Decision 12 separat im Repository lebt statt als
  mutables Feld in `RunMetadata`).
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md)
  (Schaerfungs-ohne-Supersede-Pattern — ADR 0039
  konkretisiert `GG-API-001` + `GG-UI-004` aus
  Lastenheft §16/§17 fuer Welle-4a-Implementation).
- [`ADR 0015`](0015-snapshot-envelope-v2.md)
  (TickLoop-Snapshot-Envelope-v2: das NEU
  `_control_state`-Feld ist Run-Lifecycle-State, kein
  Tick-Determinismus-State — gehoert nicht in den
  Snapshot. `from_snapshot`-Resume setzt es auf
  `"running"` (Welle-6a-Pattern), statt es aus dem
  Snapshot zu rekonstruieren).
- [`ADR 0022`](0022-fault-injection-protocol.md) §2.4
  (FaultPort-TickLoop-Hook im Vor-Tick-Block ist der
  Cooperative-Hook-Praezedenzfall im `TickLoop.tick()`-
  Body — Decision 13 erweitert das Pattern um einen
  zweiten Pre-Tick-Guard fuer den `_control_state`).
- [`ADR 0036`](0036-ui-stack-choice.md) §2.5
  (UI-Stack HTMX + Chart.js — Welle 4a fuegt einen
  dritten Page-Route hinzu, der das HTMX-Polling-Pattern
  produktiv etabliert).
- [`ADR 0037`](0037-http-api-surface-pattern.md) §2.1 +
  §2.2 (Decision API-1 = `POST /runs/{id}/control` mit
  Action-Body; Decision API-2 = kein separater
  `UICommandPort`-Slot. Welle-4a-C2 wirt die Welle-1-
  Stub-Logik des `control`-Endpoints produktiv aus,
  ohne die Endpoint-Surface zu aendern; Decision 13
  liefert die TickLoop-seitige Anker-Methode).
- [`ADR 0038`](0038-telemetry-stream-port.md) §3.2
  (TelemetryStreamPort-Welle-4-Folge: der `demo_generator.
  py`-Stub aus Welle 3 wird durch echtes TickLoop-Wiring
  im Welle-4a-Lifespan-Driver ersetzt; ADR 0038-Surface
  bleibt unveraendert).
- [Lastenheft](../../../spec/lastenheft.md) §16
  (`GG-API-001` REST-Schnittstellen: Akzeptanz „REST
  bietet Endpunkte fuer Szenario-Start, Pause, Resume,
  Stop, Status, Snapshot und Fault Injection". Welle 4a
  schliesst den Pause/Resume/Stop/Status-Anteil; Snapshot
  ist Welle-1-`GET /snapshot`-Stub + Welle-6c-Postgres).
- [Lastenheft](../../../spec/lastenheft.md) §17
  (`GG-UI-004` Replay-Steuerung-Akzeptanz: „UI bietet
  fuer einen vorhandenen Lauf mindestens Start, Pause,
  Resume, Stop und Anzeige des Replay-Status an").
- [Architektur](../../../spec/architecture.md) §4.2
  (`GG-AR-PORT-DRN-003` `RunRepositoryPort` — Welle 4a
  erweitert den Vertrag um `update_status` + `get_status`,
  symmetrisch zur Welle-1-`exists`-Extension).
- [`../planning/done/M5-welle-4a.md §3`](../planning/done/M5-welle-4a.md)
  (Welle-4a-Slice-Doc mit Decisions 12/13/14 final +
  C2-Realization-Notes).
- **Vorbild-Probes** — kein eigener Welle-4a-Probe noetig,
  weil Cooperative-State-Machine + HTMX-Polling-Pattern
  bereits durch zwei Vorlaeufer-Probes server-side
  validiert sind:
  - Welle-1-Probe `9c20dad` (HTMX-FastAPI-Smoke: Server-
    Templates rendern, HTMX-Request-Header, WS-Push).
  - Welle-3-Probe `5349923` (Asyncio-Pub/Sub-Smoke).

**C2-Realization-Notes (Welle-4a-C3-Sync):**

C2-Code-Merge `9c188e0` zog gegenueber dem C1-ADR-Original
vier produktive Anpassungen ein. Die Decisions 12/13/14
bleiben semantisch unveraendert; die Realization-Notes
sind Nomenklatur- und Architektur-Layering-Anpassungen:

1. **RunStatus-Vokabel** auf
   `pending`/`running`/`paused`/`stopped`/`completed`
   umgestellt (statt `idle`/`ended`-Original). Welle-1
   hat das `RunState`-Literal in `_schemas.py` mit
   diesen Werten ausgeliefert; Domain owns the type —
   `_schemas.py:RunState` ist Re-Export von
   `domain.run.RunStatus`. Pseudo-Code in §2.1/§2.2
   nutzt die finale Vokabel.
2. **`request(action)`-Konsolidierung** statt 3
   separater `request_pause`/`_resume`/`_stop`-Methoden:
   `TickLoop` hatte bereits 11 Public-Methoden/Properties
   (`PLR0904 max-public-methods=12`); 3 weitere haetten
   die Schwelle gerissen. Eine einzige `request(action:
   ControlAction)`-Methode dispatched ueber eine Modul-
   Konstante `_CONTROL_ACTION_TRANSITIONS` (pro Action
   `(target_state, allowed_from)`-Paarung). Decision-13-
   Transition-Matrix bleibt identisch; nur die
   Surface-Form ist anders. PLR0904-Per-File-Ignore in
   `pyproject.toml` ergaenzt (Pattern analog
   `devices/*/model.py` + `grid_model/bilanz.py`).
3. **`configure_demo_run`-Auslagerung** aus `app.py`
   nach NEU `_demo_setup.py` wegen
   `AC-NO-GOD-UTILS max=5 public top-level functions`
   pro Modul. `app.py` exportiert nur die drei
   `configure_*`-Injection-Punkte + `get_health` +
   `post_runs` (genau 5); `_demo_setup.py` kombiniert
   die drei zu einem Demo-Run-Bundle inkl. inline-
   `_DemoSimulationClock`-`ClockPort`-Impl.
4. **`AC-ADAPTER-PURE`-`ignore_imports`** in
   `pyproject.toml` verankert die Komposition-Root-
   Brueck-Erlaubnis fuer `_demo_setup.py` +
   `_tick_loop_registry.py` + `_tick_loop_driver.py` →
   `hexagon.core.simulation.{tick_loop,scheduler}`. Die
   §2.2-Option-C-Begruendung (kein `ControlPort`-Slot;
   YAGNI) ist damit architektonisch verankert; andere
   Adapter-Pakete duerfen `simulation` weiterhin nicht
   touchen.

---

## 1. Kontext

M5-Welle-1 hat die HTTP-API-Surface mit dem Endpoint
`POST /runs/{run_id}/control` angelegt — der nimmt einen
`ControlRequest`-Body mit `action: Literal["pause",
"resume", "stop"]` entgegen und gibt
`ControlResponse(accepted=True)` zurueck, ohne den
TickLoop tatsaechlich zu beruehren (Welle-1-Code-Kommentar:
„kein echtes TickLoop-Pause/Resume/Stop-Wiring
(Welle 4)").

M5-Welle-3 hat einen TelemetryStreamPort + Live-Telemetry-
Dashboard geliefert; der Producer ist ein
`DemoTelemetryGenerator`-Stub im FastAPI-Lifespan, der
synthetische TelemetryPoints alle ~200ms publisht — ohne
Bezug zu einem echten TickLoop-Tick. Welle-3-Anti-Scope:
„Kein echtes TickLoop-Wiring (Demo-Generator als Stub;
**Welle 4 ersetzt**)".

M5-Welle-4a loest diese zwei Forward-Pointer ein und
erfuellt `GG-UI-004` (Replay-Controls) + den Replay-
Restcompletion-Anteil `GG-API-001` (Pause/Resume/Stop/
Status-Endpunkte produktiv, nicht mehr Stub).

Drei Architektur-Concerns formen das Welle-4a-Pattern:

- **Run-Lifecycle-State.** Ein Lauf hat einen Status
  jenseits seiner Reproduzierbarkeits-Metadaten
  (Scenario-Hash, Seed, tick_ms). `pending` → `running` →
  `paused` ↔ `running` → `stopped`/`completed`. Wo lebt
  dieser State?
- **TickLoop-Control-Surface.** TickLoop ist seit M1
  synchron (`tick() -> TickResult`); kein interner
  Run-Loop, kein Threading. Wie kommuniziert ein HTTP-
  getriebener Pause-Befehl mit einem extern-getriebenen
  Tick?
- **UI-Status-Update-Frequenz.** Sim-Zeit + Tick-Zaehler
  + Run-Status muessen in der UI sichtbar sein. Welche
  Frequenz, welches Transport-Pattern?

## 2. Entscheidung

### 2.1 Decision 12 (RunStatus-Tracking-Architektur) — RunRepository-Extension

**Gewaehlt:** `RunRepositoryPort` wird um zwei
synchron-Methoden erweitert; `RunStatus` ist ein
`Literal`-Type-Alias mit 5 Zustaenden; `RunMetadata`
bleibt frozen.

**Surface-Konstruktion:**

```python
RunStatus = Literal[
    "pending", "running", "paused", "stopped", "completed"
]


class RunRepositoryPort(Protocol):
    # Welle-1-Surface (unveraendert):
    def save(self, metadata: RunMetadata) -> None: ...
    def get_by_id(self, run_id: str) -> RunMetadata: ...
    def exists(self, run_id: str) -> bool: ...

    # Welle-4a-Extension:
    def update_status(
        self, run_id: str, status: RunStatus
    ) -> None: ...
    """Persistiert den Run-Lifecycle-Status. Wirft
    RunNotFoundError, wenn der Lauf nicht persistiert
    ist (Konsistent mit get_by_id)."""

    def get_status(self, run_id: str) -> RunStatus: ...
    """Liest den Run-Lifecycle-Status. Wirft
    RunNotFoundError, wenn der Lauf nicht persistiert
    ist."""
```

**State-Semantik:**

| State        | Bedeutung                                                                  |
| ------------ | -------------------------------------------------------------------------- |
| `pending`       | Run persistiert, aber Tick-Driver noch nicht gestartet (initial)          |
| `running`    | Tick-Driver aktiv; `tick()` fortschreitet                                  |
| `paused`     | Tick-Driver aktiv, aber Tick-Guard blockt; `_tick_count` bleibt           |
| `stopped`    | Final-Terminierung durch Benutzer; kein Resume moeglich                    |
| `completed`      | Final-Terminierung durch Tick-Loop-Ende oder Lifespan-Shutdown            |

**Begruendung gegen Alternativen:**

- **Option A — `RunMetadata.status` als mutables Feld.**
  Bricht `RunMetadata`-Frozen-Equality und ADR-0007-
  Reproduktions-Garantie (`RunMetadata`-Hash muss stabil
  bleiben fuer Snapshot-Vergleich). **Verworfen.**
- **Option B — NEU separater `RunStatusPort`-Driven-Slot.**
  Eigener Port nur fuer Status. YAGNI — Status braucht
  denselben Lifecycle wie Metadaten (gleicher `run_id`-
  Schluessel, gleicher Multi-Run-Lookup); separater Port
  erhoeht die Adapter-Komplexitaet ohne Vorteil
  (Postgres-Implementation in M3 wuerde zwei Tabellen
  mit derselben Foreign-Key brauchen). **Verworfen.**
- **Option D — Nur TickLoop-internes Feld + Lookup ueber
  Registry.** RunStatus lebt komplett im TickLoop.
  Verworfen: M3-Welle-6c-Postgres-Replay-Sicht braucht
  Status nach Crash; bei Restart waere der State
  verloren. Decision 13 nutzt trotzdem ein internes
  TickLoop-Mirror-Feld, das aber als **Cache** der
  Repository-Wahrheit fungiert. **Verworfen.**

**Repository-Konsistenz:**

- `update_status` schreibt zuerst ins Repository, dann
  setzt der Caller (TickLoop oder Lifespan-Driver) das
  interne Cache-Feld. Bei `save()`-initialem Setup ist
  der Default-Status `"pending"` (Welle-4a-Spec; das
  Repository setzt `pending` automatisch waehrend
  `save()`).
- `get_status` ist ein direkter Repository-Read — die
  UI-Polling-Schleife (Decision 14) liest den State
  ueber `GET /runs/{id}/status` aus dem Repository,
  nicht aus dem TickLoop-Cache. Damit ist der UI-State
  konsistent mit dem persistierten State.

### 2.2 Decision 13 (TickLoop-Control-Surface) — Cooperative State-Machine

**Gewaehlt:** TickLoop bekommt ein internes
`_control_state: RunStatus`-Feld + 3 Public-Methoden
(`request_pause`/`request_resume`/`request_stop`); der
`tick()`-Body bekommt einen NEUEN Pre-Tick-Guard vor
dem produktiven Tick-Code.

**Surface-Konstruktion:**

```python
class TickLoop:
    def __init__(
        self,
        *,
        run_id: str,
        tick_ms: int,
        # ... Welle-6a-Surface unveraendert
        run_repository: RunRepositoryPort | None = None,
    ) -> None:
        # ...
        self._control_state: RunStatus = "pending"
        self._run_repository: RunRepositoryPort | None = run_repository

    def request_pause(self) -> None:
        """Setzt _control_state auf 'paused'.
        Erlaubt aus 'running' oder 'pending'; sonst
        TickLoopInvalidTransitionError."""

    def request_resume(self) -> None:
        """Setzt _control_state auf 'running'.
        Erlaubt aus 'paused' oder 'pending'; sonst
        TickLoopInvalidTransitionError."""

    def request_stop(self) -> None:
        """Setzt _control_state auf 'stopped'.
        Erlaubt aus 'pending', 'running' oder 'paused';
        sonst TickLoopInvalidTransitionError."""

    def tick(self) -> TickResult:
        # NEU Welle-4a-Pre-Tick-Guard:
        if self._control_state == "paused":
            return TickResult.paused(
                tick_count=self._tick_count,
                simulation_time_ms=self._tick_count * self._tick_ms,
            )
        if self._control_state in ("stopped", "completed"):
            raise TickLoopStoppedError(
                run_id=self._run_id,
                control_state=self._control_state,
            )
        if self._control_state == "pending":
            # Erster Tick flippt automatisch nach 'running'
            self._set_control_state("running")
        # ... existierender Welle-6a-Tick-Body
```

**State-Transitions-Matrix:**

| Aus / Nach   | `pending` | `running` | `paused` | `stopped` | `completed` |
| ------------ | ------ | --------- | -------- | --------- | ------- |
| `pending`       | —      | auto via `tick()` | `request_pause` | `request_stop` | (kein) |
| `running`    | —      | —         | `request_pause` | `request_stop` | auto bei Tick-Loop-Ende |
| `paused`     | —      | `request_resume` | —    | `request_stop` | (kein) |
| `stopped`    | —      | (Invalid) | (Invalid) | (idempotent no-op) | (kein) |
| `completed`      | —      | (Invalid) | (Invalid) | (Invalid) | (idempotent no-op) |

**Invalid-Transitions** werfen
`TickLoopInvalidTransitionError(current_state, target_state,
run_id)`; der HTTP-Adapter mapped das auf **409 Conflict**
mit `ErrorResponse(code="invalid_transition", ...)` (siehe
ADR 0037 §2 Error-Format `GG-API-004`).

**Begruendung gegen Alternativen:**

- **Option A — TickLoop bekommt internen Run-Loop +
  Threading + asyncio-Queue fuer Control-Messages.**
  Bricht das Tick-Loop-Determinismus-Versprechen
  (`GG-SIM-001`) und macht Snapshot-Tests instabil
  (Threading-Scheduler-Drift). Welle-6a hat den
  TickLoop-Sync-Vertrag explizit verankert. **Verworfen.**
- **Option C — Control-Events via NEU `ControlPort`-
  Driven-Slot.** Eigener Port nur fuer Pause-Events. Das
  Control-Flag ist ein triviales Enum-Triple und braucht
  keinen Adapter-Vertrag — die State-Transitions sind
  TickLoop-interne Logik, nicht externe Resource-Calls.
  **Verworfen.**

**Repository-Mirror-Sequenz:**

Jede `request_*`-Methode folgt diesem Pattern:

```python
def request_pause(self) -> None:
    self._guard_transition("paused")  # raises wenn invalid
    if self._run_repository is not None:
        self._run_repository.update_status(self._run_id, "paused")
    self._control_state = "paused"
```

Reihenfolge: zuerst Guard (Invalid-Transition catch),
dann Repository-Write (Persistenz-Wahrheit), dann
internes Feld-Set (Cache-Update). Falls Repository-Write
fehlschlaegt, bleibt der lokale Cache konsistent mit
der Repository-Wahrheit (kein Drift). Das Repository ist
**optional** im Konstruktor (Welle-6a-Pattern fuer
testbare TickLoop ohne Repository-Doppel); bei
`run_repository=None` skippt der Mirror-Step.

**Snapshot-Format-Compat (ADR 0015):**

Das `_control_state`-Feld geht **nicht** in den
Snapshot. Begruendung: Run-Lifecycle-State ist
orthogonal zum Tick-Determinismus (Snapshot-Equality
ist eine Aussage ueber Tick-Outputs, nicht ueber
Run-Status). `from_snapshot(state, *, clock, random)`
setzt `_control_state = "running"` als Default —
Welle-6a-Pattern. Konsequenz: bei Restart-Resume
startet der Run direkt in `running`, ohne Pause-State
zu rekonstruieren. Das ist akzeptable Welle-4a-
Vereinfachung; M3-Welle-6c-Postgres-Replay kann das
verfeinern (Status-Spalte zusaetzlich laden).

### 2.3 Decision 14 (Replay-Status-Update-Pattern) — HTMX-Polling

**Gewaehlt:** NEU `GET /runs/{run_id}/status`-REST-
Endpoint mit JSON-Response `{sim_time_ms: int,
tick_count: int, run_status: RunStatus}`; UI nutzt
HTMX-Polling mit `hx-trigger="every 1s"
hx-target="#status"`.

**UI-Template-Surface:**

```html
<div id="status"
     hx-get="/runs/{{ run_id }}/status"
     hx-trigger="every 1s"
     hx-target="this"
     hx-swap="outerHTML">
  {% include "_status_block.html" %}
</div>
```

**Endpoint-Surface:**

```python
@runs_router.get(
    "/runs/{run_id}/status",
    response_model=RunStatusResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_run_status(
    run_id: str,
    repository: Annotated[RunRepositoryPort, Depends(...)],
    tick_loop_registry: Annotated[TickLoopRegistry, Depends(...)],
) -> RunStatusResponse:
    metadata = _require_run(run_id, repository)
    status = repository.get_status(run_id)
    tick_loop = tick_loop_registry.tick_loop_for(run_id)
    return RunStatusResponse(
        run_id=run_id,
        run_status=status,
        tick_count=tick_loop.tick_count if tick_loop else 0,
        simulation_time_ms=(
            tick_loop.tick_count * metadata.tick_ms
            if tick_loop else 0
        ),
    )
```

**Begruendung gegen Alternativen:**

- **Option B — WS-Subscription** auf NEU `/runs/{id}/
  status-stream`. Overkill fuer 1Hz-Status-Updates;
  benoetigt zweite WS-Surface neben Telemetry-WS aus
  Welle 3; Browser-Reconnect-Verhalten waere ein
  Welle-4a-Anti-Scope-Item. **Verworfen.**
- **Option C — Embedded in Telemetry-WS.** Status-
  Updates als spezielle TelemetryPoint-Sub-Kategorie.
  Bricht ADR 0038 §2.1 TelemetryPoint-Semantik
  (TelemetryPoint = Geraete-Messung, nicht Run-
  Lifecycle); ein `device_id="__run__"` waere ein
  Antipattern. **Verworfen.**

**Polling-Konsistenz:**

- 1s-Trigger ist Welle-4a-Default (UI-Comfort fuer Demo);
  HTMX erlaubt `hx-trigger="every 500ms"` etc., falls
  zukuenftige Wellen feinere Update-Frequenz brauchen.
  Welle-4a dokumentiert das im Slice-Doc-§7 als Risiko
  (Multi-Tab-Polling-Last).
- Idempotente GET-Endpoints — kein State-Change durch
  Polling; trivial zu testen mit
  `fastapi.testclient.TestClient.get(...)`.

## 3. Konsequenzen

### 3.1 Welle-4a-Folge

- **Code-Merge (C2 `9c188e0`):** NEU `RunStatus`-Literal-
  Alias in `hexagon/core/domain/run.py`; RunRepositoryPort
  um 2 Methoden erweitert; InMemoryRunRepository-Helper
  + `PostgresRunRepository`-`NotImplementedError`-Stub
  aktualisiert; TickLoop um konsolidierte `request(action)`-
  Methode (statt 3 `request_*`-Wrappern; C2-Realization-
  Note) + Pre-Tick-Guard erweitert; NEU `TickResult.
  paused_result`-Classmethod-Factory; NEU Errors
  `TickLoopStoppedError` +
  `TickLoopInvalidTransitionError` in
  `hexagon/core/errors.py`.
- **HTTP-Adapter:** `POST /runs/{id}/control` ruft
  `tick_loop.request(request.action)` am TickLoop
  (Lookup ueber NEU `TickLoopRegistry`); Invalid-
  Transition mapped auf 409, TickLoop-not-active auf
  503. Welle-1-`GET /runs/{id}/status`-Stub ausgewirt
  auf RunRepository + TickLoopRegistry (kein NEU-
  Endpoint, sondern Wiring).
- **UI-Page:** NEU `GET /runs/{run_id}/control` rendert
  3 HTMX-POST-Buttons + Status-Polling-Block mit
  1s-Trigger; RunStatus-CSS-Klassen visualisieren den
  State (5 Zustaende, analog Welle-3-Quality-Marker-
  Pattern).
- **Lifespan-Demo-Driver:** FastAPI-Lifespan erzeugt
  einen Single-Demo-Run + Tick-Driver-asyncio-Task; bei
  Shutdown sauberes Task-Cancel + RunStatus → `completed`.
- **Tests:** ~12 neue Unit + 1 neue Integration; alle
  Welle-1-Tests fuer `control`-Stub auf produktives
  Wiring umgestellt (statt geloescht).

### 3.2 Welle-4b-Folge

- **Alarm-Aggregation + AlarmStreamPort** in Welle-4b-
  Pre-C0a `d1b0eb7` + Pre-C0b `e325307` + C0 eroeffnet
  (siehe
  [`../planning/in-progress/M5-welle-4b.md`](../planning/in-progress/M5-welle-4b.md));
  NEU ADR 0040 fuer C1 vorbereitet. **Welle-4b-C0-Pre-
  Research erweiterte den Welle-4a-Era-Plan von 2 auf
  3 Decisions** (15 NEU Unified `Alarm`-Domain-Schema +
  Mapper-Familie; 16 TickLoop-Aggregation via
  `TickResult.emitted_alarms`; 17 AlarmStreamPort-
  Surface + `GET /runs/{id}/alarms`-History-Endpoint).
  Pattern-Vorbild: ADR 0038 `TelemetryStreamPort` (NEU
  Driving-Port + asyncio-Pub/Sub-Adapter).
- **Alarm-Surface-Symmetrie:** Welle 4b kann den
  Cooperative-Pattern aus Decision 13 wiederverwenden,
  falls Alarm-Trigger den Run pausieren sollen
  (`AlarmSeverity.CRITICAL` → auto-pause). Forward-
  Pointer fuer Welle 4b dokumentiert.
- **NEU `AlarmStatusPort` (eventuell):** falls Welle 4b
  einen orthogonalen Status (`active`/`acknowledged`/
  `resolved`) braucht, koennte das Pattern aus
  Decision 12 (Repository-Extension) wiederverwendet
  werden — Welle-4b-Decision-Entscheidung.

### 3.3 Welle-5-Folge

- **TickLoopRegistry-Produktivierung:** Welle 4a liefert
  einen Single-Demo-Run-Stub unter `adapters/driving/
  http_api/_tick_loop_registry.py`. Welle 5 (Scenario-
  Loader + Demo-Pipeline) ersetzt ihn durch eine
  Multi-Run-Implementation, die Scenario-getriebene
  TickLoops aufnimmt (`POST /runs`-Endpoint wirt den
  Loader; `RunMetadata.scenario_hash` wird produktiv
  belegt).
- **Welle-5-Anti-Scope-Schutz:** Welle 4a touched
  `POST /runs` **nicht**; bleibt Welle-1-Stub.
- **TickLoop-Tick-Driver in Lifespan:** Welle 5 ersetzt
  den Single-Demo-Driver durch einen Multi-Run-Driver,
  der die Registry iteriert und pro aktivem Run einen
  asyncio-Task halt.

### 3.4 Welle-6-Folge / M6

- **OTel-Span-Wrap fuer Control-Actions:** analog
  `_protocol_otel_wrap.py` aus M4-Welle-6a koennte ein
  `_run_control_otel_wrap.py` jede `request_*`-Methode
  in eine Span mit Attributen `run_id`/`current_state`/
  `target_state`/`success` einwickeln. M6 oder eine
  separate Hardening-Welle.
- **Status-Push-Notifications:** Welle 6 koennte das
  Polling-Pattern um eine optionale WS-Push-Variante
  erweitern (HTMX `sse-connect` etc.); ADR 0039
  bleibt unveraendert (Decision 14 Polling-Default).
- **Multi-Tenant-RunStatus-Scoping:** wenn M6 Multi-
  Tenancy einfuehrt, koennte `update_status` um einen
  Tenant-Parameter erweitert werden; ADR-0039-
  Schaerfung-ohne-Supersede-Pattern (ADR 0011).

### 3.5 Architektur-Konsistenz

- **Pattern-Praezedenz Cooperative-Hook:** ADR 0022 §2.4
  (FaultPort-TickLoop-Hook im Vor-Tick-Block) hat das
  Cooperative-Hook-Pattern im TickLoop etabliert.
  Decision 13 erweitert es um einen zweiten Pre-Tick-
  Guard (`_control_state`-Check); kein Threading, kein
  Bruch der Sync-Tick-Semantik.
- **Pattern-Praezedenz Driven-Port-Extension:** Welle-1
  hat `RunRepositoryPort.exists` zur ursprünglichen
  `save`/`get_by_id`-Surface ergaenzt. Decision 12
  folgt demselben Pattern fuer `update_status` +
  `get_status`. Welle 1 hat damit den Praezedenzfall
  geschaffen, dass `RunRepositoryPort` ein wachsender
  Port ist (nicht atomar an einem Punkt eingefroren).
- **Pattern-Praezedenz HTMX-Polling:** ADR 0036 §2.4
  bestaetigt HTMX als UI-Stack; Welle 2 hat die HTMX-
  Basis geliefert; Welle 3 nutzt das HTMX-`hx-ext="ws"`-
  Pattern. Welle 4a liefert die HTMX-`hx-trigger="every
  Xs"`-Pattern produktiv (kein neuer Stack-Bestandteil,
  nur natives HTMX-Feature).

## 4. Out-of-Scope

- **Alarm-Aggregation + AlarmStreamPort.** Welle 4b mit
  NEU ADR 0040 geplant.
- **Scenario-Loader + Multi-Run-Registry.** Welle 5
  (Demo-Pipeline). Welle 4a liefert nur einen Single-
  Run-Stub.
- **Echte Postgres-Status-Persistenz.** M3-Welle-6c.
  Welle 4a bleibt In-Memory.
- **Snapshot-Status-Roundtrip.** Welle 4a setzt
  `_control_state` bei `from_snapshot`-Resume auf
  `"running"` (Welle-6a-Pattern). M3-Welle-6c-Postgres-
  Replay-Sicht koennte das verfeinern.
- **OTel-Span-Wrap fuer Control-Actions.** M6 oder
  separate Hardening-Welle (siehe §3.4).
- **WebSocket-Status-Push.** Welle 4a nutzt HTMX-
  Polling (Decision 14); WS-Variante deferred.
- **`POST /runs`-Scenario-Setup.** Welle-1-Stub bleibt
  unveraendert; Welle 5 (Scenario-Loader).
- **Start-Action via `POST /runs/{id}/control` mit
  `action: "start"`.** Decision API-1 (ADR 0037 §2.1)
  listet nur `pause`/`resume`/`stop`; ein expliziter
  `start` ist semantisch redundant zu `resume` aus
  `pending`. Decision 13 bietet einen idempotenten
  `request_resume`-Pfad aus `pending`.
- **`request_resume` von `stopped`-State.** Welle 4a
  behandelt `stopped` als terminal. `Resume` von einem
  gestoppten Run wuerde einen neuen Lauf bedeuten
  (`GG-DATA-001` neue `run_id`); das ist ein Welle-5-
  Scenario-Loader-Concern.

## 5. Status-Pfad

- **Proposed** — 2026-06-02 mit M5-Welle-4a-C1 `f1284c4`.
  Decisions 12/13/14 alle final entschieden im ADR-Body;
  Vorlaeufer-Probes Welle-1 `9c20dad` + Welle-3 `5349923`
  decken HTMX/Asyncio-Mechanik bereits ab.
- **Provisional** — 2026-06-02 mit M5-Welle-4a-C3 (dieser
  Commit) nach C2-Code-Merge `9c188e0`. Pattern analog
  ADR 0030..0038 (`Proposed → Provisional` mit C3 nach
  C2-Implementation-Merge; C2 belegt die Decisions
  produktiv im Code). C2-Realization-Notes (siehe oben
  unter „Bezug") dokumentieren vier Nomenklatur-/
  Architektur-Layering-Anpassungen — Decisions
  semantisch unveraendert.
- **Accepted** — geplant mit M5-Welle-7-Closure (analog
  ADR 0030..0038).

## 6. Folge-Pflichten

- **M5-Welle-4a-C2-Code-Merge `9c188e0`** belegt Decisions
  12/13/14 produktiv:
  - `src/grid_gym/hexagon/core/domain/run.py` — NEU
    `RunStatus`-Literal-Alias
    (`pending`/`running`/`paused`/`stopped`/`completed`).
  - `src/grid_gym/hexagon/ports/driven/run_repository.py`
    — `RunRepositoryPort` um `update_status` +
    `get_status` erweitert.
  - `src/grid_gym/hexagon/core/simulation/tick_loop.py`
    — `_control_state`-Feld + `control_state`-Property
    + konsolidierte `request(action)`-Methode (statt 3
    `request_*`-Wrappern; C2-Realization-Note §0) +
    Modul-Konstante `_CONTROL_ACTION_TRANSITIONS` +
    `_attach_control_state`-Helper + Pre-Tick-Guard.
  - `src/grid_gym/hexagon/core/domain/tick_result.py`
    — NEU `paused: bool = False`-Feld + NEU
    `TickResult.paused_result(...)`-Classmethod.
  - `src/grid_gym/hexagon/core/errors.py` — NEU
    `TickLoopStoppedError` +
    `TickLoopInvalidTransitionError`.
  - `src/grid_gym/adapters/driving/http_api/_runs_router.py`
    — `GET /runs/{id}/status`-Welle-1-Stub auf
    RunRepository + TickLoopRegistry ausgewirt.
  - `src/grid_gym/adapters/driving/http_api/_runs_action_router.py`
    — `POST /control`-Wiring an
    `TickLoopRegistry.tick_loop_for(run_id).request(action)`-
    Aufruf; 409-Mapping (Invalid-Transition) + 503-
    Mapping (TickLoop-not-active).
  - `src/grid_gym/adapters/driving/http_api/_schemas.py`
    — `RunState`-Alias auf Domain-`RunStatus` umgestellt.
  - `src/grid_gym/adapters/driving/http_api/_tick_loop_registry.py`
    — NEU (Single-Run-Demo-Registry +
    `get_tick_loop_registry`-Dependency).
  - `src/grid_gym/adapters/driving/http_api/_tick_loop_driver.py`
    — NEU `DemoTickLoopDriver`-Asyncio-Task-Wrapper
    mit Cooperative-State-Loop.
  - `src/grid_gym/adapters/driving/http_api/_demo_setup.py`
    — NEU `configure_demo_run`-Komposition-Root
    (Auslagerung aus `app.py` wegen
    `AC-NO-GOD-UTILS max=5 public top-level functions`).
  - `src/grid_gym/adapters/driving/http_api/app.py`
    — NEU `configure_tick_loop_registry`-Injection-Punkt
    + Lifespan-Driver-Start/Stop.
  - `src/grid_gym/adapters/driving/ui/routes.py` +
    `templates/control.html` +
    `_control_content.html` +
    `static/style.css` (5 RunStatus-CSS-Klassen) +
    `templates/navigation.html` — NEU UI-Page +
    HTMX-JSON-Encoding-Helper.
  - `src/grid_gym/adapters/driven/persistence_postgres/run_repository.py`
    — `update_status`/`get_status`-Stub mit
    `NotImplementedError` + M3-Welle-6c-Forward-Pointer.
  - `pyproject.toml` — PLR0904-Per-File-Ignore fuer
    `tick_loop.py` + `AC-ADAPTER-PURE`-`ignore_imports`-
    Block fuer Komposition-Root-Brueck-Erlaubnis.
- **M5-Welle-4a-C3 (dieser Commit)** zieht diese ADR auf
  `Provisional` mit C2-Code-Merge-Beleg + Status/DoD-
  Sync + Top-Level-Doku-Sync.
- **M5-Welle-4b** (Alarme) liefert ggf. eine
  symmetrische Status-Tracking-Erweiterung fuer
  Alarme; NEU ADR 0040 geplant (siehe §3.2).
- **M5-Welle-5** (Demo-Pipeline) ersetzt den Single-
  Demo-Run-Stub durch Multi-Run-Scenario-Setup; ADR
  0039 bleibt unveraendert (Surface-stabil).
- **M5-Welle-7-Closure** zieht diese ADR auf `Accepted`.
- **Optional Welle-6 oder M6:** OTel-Span-Wrap fuer
  Control-Actions (siehe §3.4); WS-Push-Variante fuer
  Status-Updates.

## 7. References

- [`ADR 0007`](0007-random-port.md)
  (`RandomPort`-Reproduzierbarkeits-Foundation;
  `RunMetadata.seed` produktiv).
- [`ADR 0015`](0015-snapshot-envelope-v2.md)
  (TickLoop-Snapshot-Envelope-v2; `_control_state`
  gehoert nicht in den Snapshot).
- [`ADR 0022`](0022-fault-injection-protocol.md) §2.4
  (FaultPort-TickLoop-Hook im Vor-Tick-Block als
  Cooperative-Pre-Tick-Hook-Praezedenzfall).
- [`ADR 0036`](0036-ui-stack-choice.md) §2.5
  (HTMX-UI-Stack).
- [`ADR 0037`](0037-http-api-surface-pattern.md) §2.1
  (Replay-Controls-API-Vertrag; Welle-4a-C2 wirt die
  produktive Logik aus).
- [`ADR 0038`](0038-telemetry-stream-port.md) §3.2
  (Welle-4-Folge: TickLoop-Wiring ersetzt Demo-
  Generator).
- [Lastenheft](../../../spec/lastenheft.md) §16
  `GG-API-001` (REST-Replay-Steuerung-Pflicht).
- [Lastenheft](../../../spec/lastenheft.md) §17
  `GG-UI-004` (Replay-Controls-UI-Akzeptanz).
- [Architektur](../../../spec/architecture.md) §4.2
  (`GG-AR-PORT-DRN-003` `RunRepositoryPort`).
- [`../planning/done/M5-welle-4a.md §3`](../planning/done/M5-welle-4a.md)
  (Welle-4a-Slice-Doc mit Decisions 12/13/14).
- **Vorbild-Probes** — keine eigene Welle-4a-Probe:
  - Welle-1-HTMX-FastAPI-Probe `9c20dad` — 4 Tests in
    [`../../../tests/integration/test_m5_welle_1_htmx_probe.py`](../../../tests/integration/test_m5_welle_1_htmx_probe.py)
    decken FastAPI-Templates + HTMX-Request-Header +
    WS-Push ab.
  - Welle-3-Asyncio-Pub/Sub-Probe `5349923` — 4 Tests
    in
    [`../../../tests/integration/test_m5_welle_3_async_pubsub_probe.py`](../../../tests/integration/test_m5_welle_3_async_pubsub_probe.py)
    decken asyncio-Pub/Sub-Pattern ab.
- Pattern-Praezedenz **Driven-Port-Extension**: Welle-1-
  `RunRepositoryPort.exists` (`GG-AR-PORT-DRN-003` als
  wachsender Port-Vertrag).
- Pattern-Praezedenz **Cooperative-Pre-Tick-Hook**: ADR
  0022 §2.4 (FaultPort-TickLoop-Hook im Vor-Tick-Block).
