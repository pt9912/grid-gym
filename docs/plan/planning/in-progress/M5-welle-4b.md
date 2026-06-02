# Welle 4b — M5 Alarm-Aggregation + AlarmStreamPort + Alarm-Tabelle-UI

**Status:** In Progress 2026-06-02 — Pre-C0-Stack:
Pre-C0a `d1b0eb7` (Self-Close-Move M5-welle-4a.md → done/,
rename-only) + Pre-C0b `e325307` (Cross-Doc-Refs-Sync,
4 Files) + C0 (dieser Commit; Slice-Doc + Decisions
15/16/17 final aus C0-Pre-Research + Retro-Sync der
2→3-Decision-Forward-Pointer aus Welle-4a-Era).

Welle 4b ist die **Alarm-Welle** in M5 und der **zweite
Sub-Slice der Welle-4-Subdivision** (4a Replay-Controls +
4b Alarme; Pattern analog M4-Welle-5a/5b und M4-Welle-
6a/6b). Welle 4b erfuellt **`GG-UI-005`** (Alarm-
Visualisierung) und schliesst den langen Forward-Pointer
„AlarmSinkPort kommt mit M3" aus
[`ADR 0014 §6`](../../adr/0014-battery-snapshot-schema.md)
(Welle-2-Review M-3, 2026-05-18) — M3 ist ohne
AlarmSinkPort geschlossen worden; M5-Welle-4b loest die
Verantwortung produktiv aus.

**Sub-Slice-Motivation (Welle-4b-Decision-Inkrement):**

Die Welle-4a-Slice-Doc + ADR-0039-§3.2-Forward-Pointer
versprachen 2 Decisions (15/16, geplant) als Welle-4b-
Substanz. M5-Welle-4b-C0-Pre-Research deckte drei
distinkte Architektur-Concerns auf, die jeweils einen
eigenen Decision-Slot rechtfertigen:

1. **Decision 15: NEU Unified `Alarm`-Domain-Schema +
   Mapper-Familie.** Domain-Slot: das kanonische
   9-Feld-Schema aus
   [`spec/architecture.md`](../../../../spec/architecture.md)
   §Alarm produktiv anlegen + 5 typisierte Mapper-
   Funktionen von `BatteryAlarm`/`PvAlarm`/`LoadAlarm`/
   `GridConnectionAlarm`/`SmartMeterAlarm` auf die
   Unified-Form. Device-Alarms bleiben unveraendert.
2. **Decision 16: TickLoop-Alarm-Aggregation via
   `TickResult.emitted_alarms`.** Aggregations-Slot:
   `TickLoop.tick()` drainst alle Device-Alarms am Ende
   jedes Ticks deterministisch, mapped sie auf Unified-
   `Alarm`-Tupel und ergaenzt `TickResult` um ein neues
   `emitted_alarms`-Feld (parallel zu `emitted_telemetry`).
3. **Decision 17: AlarmStreamPort-Surface +
   `GET /runs/{id}/alarms`-History-Endpoint.** Adapter-
   Slot: NEU `AlarmStreamPort`-Driving-Port mit
   asyncio-Pub/Sub-Pattern (analog `TelemetryStreamPort`
   aus ADR 0038) + NEU REST-History-Endpoint fuer
   Initial-Load + Tab-Reload-Resilience. UI-Tabelle nutzt
   beide: GET fuer Hydration, WS fuer Live-Updates.

Die 3-Decision-Splittung trennt Domain-Modellierung
(Schema + Mapper) sauber von TickLoop-Vertrag
(Aggregation) und Adapter-Surface (Stream + REST).
Decision 17 ist die einzige mit neuem Driving-Port-Slot
(`GG-AR-PORT-DRV-*`-Familie); Decisions 15/16 sind
domain-intern.

**Pre-C0 abgeschlossen (2 Commits):**

1. Pre-C0a `d1b0eb7` — `git mv in-progress/M5-welle-4a.
   md → done/` (rename-only). Pattern aus Memory
   `feedback_git_mv`.
2. Pre-C0b `e325307` — Cross-Doc-Refs-Sync nach Move
   (4 Files: ADR 0039 + done/M5-welle-4a.md +
   in-progress/M5-ui-demo.md + in-progress/README.md).
   `make docs-check` cache-frei gruen.

**Kein Pre-C0c (Probe-Run):** Alle drei relevanten
Pattern sind bereits in der Substanz validiert:

- **`drain_alarms()`-Pattern** ist seit M2-Welle-2 (ADR
  0014 §2.5) produktiv in den 5 device-spezifischen
  Alarm-Familien (Battery seit `tick_loop_welle_4a_*`-
  Tests; ~41 Test-Files mit `drain_alarms`-Bezug).
  Welle-4b liest nur, mutiert die device-Implementation
  nicht.
- **`TickResult`-Erweiterung um zusaetzliches Feld** ist
  per ADR 0014 §2.5 + Welle-4a-`paused: bool = False`-
  Feld-Pattern abgesegnet (Default-Wert haelt
  Backward-Compat).
- **Asyncio-Pub/Sub-Stream-Surface** ist per Welle-3-
  Probe `5349923` server-side validiert (4 Tests:
  Single-Subscriber-Order, Multi-Subscriber-Fan-out,
  Drop-Oldest-Backpressure, Subscribe/Unsubscribe-
  Resource-Cleanup) — der Welle-4b-`AlarmStreamPort`
  uebernimmt das Pattern 1:1.
- **HTMX-Polling + REST-History-Hydration** ist per
  Welle-4a-`/runs/{id}/status`-1s-Polling produktiv
  bestaetigt.

**Spec-Reife:** Inhaltlich final fuer Welle 4b. **Welle-
4b-Decision-Liste** (§3) sammelt drei NEU Decisions
(15/16/17). NEU ADR 0040 (Alarm-Aggregation +
AlarmStreamPort) bildet C1 als `Proposed` und wird in C3
nach C2-Code-Merge auf `Provisional` gezogen
(Pattern-Praezedenz ADR 0030..0039).

---

## 1. Context

M5-Welle-4a
([`../done/M5-welle-4a.md`](../done/M5-welle-4a.md))
hat das Replay-Controls + TickLoop-Wiring produktiv
geliefert mit NEU `RunStatus`-Literal-Alias +
RunRepository-Extension + konsolidierter
`request(action)`-Methode + `GET /runs/{id}/status`-
Wiring + `POST /runs/{id}/control`-Wiring + NEU
`TickLoopRegistry`-Adapter + NEU `DemoTickLoopDriver` +
NEU UI-Page `GET /control` mit HTMX-Polling.
Welle-4a-Anti-Scope-Item: **„Keine Alarm-Aggregation /
AlarmStreamPort / Alarm-Tabelle-UI (Welle 4b)"**. Welle 4b
loest dieses Versprechen ein.

### 1.1 Existierende Substanz (M5-Welle-1+3+4a + M2 Devices)

- **HTTP-API-Surface** (Welle 1, ADR 0037 `Provisional`)
  + **Welle-4a-Wiring** (ADR 0039 `Provisional`): produktive
  `POST /runs/{run_id}/control` + `GET /status`-Wiring
  via NEU `TickLoopRegistry`-Adapter. `RunStatusResponse`-
  Schema + `RunState`-Re-Export aus `domain.run.RunStatus`.
- **TelemetryStreamPort** (Welle 3, ADR 0038
  `Provisional`): `subscribe(run_id) -> AsyncIterator
  [TelemetryPoint]` + `publish(point)` + bounded
  `asyncio.Queue` + Drop-Oldest. Welle-4b spiegelt das
  Pattern 1:1 fuer `AlarmStreamPort`.
- **UI-Foundation** (Welle 2 + 3 + 4a, ADR 0036 §6):
  `ui_router` + 3 Page-Routes (`/`, `/ui/health`,
  `/runs/{id}/dashboard` + `/runs/{id}/control`). Welle 4b
  fuegt eine vierte hinzu (`/runs/{id}/alarms`).
- **Device-spezifische Alarm-Familien** (M2 Welle 2/3/4,
  ADR 0014/0016/0017/0018 §2.5):
  - `BatteryAlarm` / `PvAlarm` / `LoadAlarm` /
    `GridConnectionAlarm` — 5-Feld-Schema
    (`target_device_id`, `limit`, `limit_unit`,
    `result: CommandResult`, `command_id`).
  - `SmartMeterAlarm` — 4-Feld-Schema
    (`target_device_id`, `reason: str`, `result`,
    `command_id`; ohne `limit`/`limit_unit`).
  - Jedes Device hat `self._alarms: list[XxxAlarm]` +
    `alarms`-Property (Snapshot) + `drain_alarms()`-
    Methode (destruktiv).
- **TickLoop** (`hexagon/core/simulation/tick_loop.py`,
  M2 Welle 6a/b + M3 + M5 Welle 4a): keine Alarm-
  Behandlung. **Drain-Aufrufe fehlen** — die device-
  Alarms wachsen heute unbegrenzt im Device-internen
  Buffer. Welle 4b fuegt den Drain-Hook am Tick-Ende ein.
- **`spec/architecture.md` §Alarm-Schema (kanonisch):**
  `{alarm_id, run_id, simulation_time, target, code,
  severity, message, status, fault_id?}` — 9 Felder.
- **Forward-Pointer-Erbschaft:**
  - `ADR 0014 §6`: „AlarmSinkPort kommt mit M3" (Welle-
    2-Review M-3, 2026-05-18) — M3 ohne AlarmSinkPort
    geschlossen; Verantwortung auf M5-Welle-4b
    geschoben.
  - `PvAlarm`-Docstring (`pv/commands.py:53`): „Welle-6-
    TickLoop und M3-AlarmSinkPort sollen IMMER
    `(result, limit)` als Tupel auswerten" — fixiert den
    Mapper-Input fuer `code`/`message`-Ableitung.
  - `ADR 0039 §3.2` (Welle-4a-Forward): Pattern-Vorbild
    `TelemetryStreamPort`; AlarmStreamPort als Welle-4b-
    Substanz angekuendigt.

### 1.2 Welle-4b-Lieferziel

1. **NEU `Alarm`-Domain-Type** in `hexagon/core/domain/
   alarm.py` als frozen Dataclass (slots) mit 9 Feldern
   per `spec/architecture.md` §Alarm: `alarm_id: str`
   (UUIDv4), `run_id: str`, `simulation_time_ms: int`,
   `target: str`, `code: str`, `severity: AlarmSeverity`,
   `message: str`, `status: AlarmStatus`,
   `fault_id: str | None`. Plus NEU `AlarmSeverity`-
   Literal (3 Welle-4b-Werte: `"info"`/`"warning"`/
   `"critical"`) + NEU `AlarmStatus`-Literal (Welle-4b
   nur `"active"`; Lifecycle-Erweiterung auf
   `"acknowledged"`/`"resolved"` ist Welle 6+/M6-Anti-
   Scope-Material).
2. **NEU Mapper-Familie** in
   `hexagon/core/domain/alarm.py` (oder separate
   `_mappers.py`): 5 typisierte Funktionen
   `Alarm.from_battery_alarm(...)`,
   `Alarm.from_pv_alarm(...)`,
   `Alarm.from_load_alarm(...)`,
   `Alarm.from_grid_connection_alarm(...)`,
   `Alarm.from_smart_meter_alarm(...)`. Jede nimmt die
   raw device-Alarm-Instanz + `run_id` + `simulation_
   time_ms` + UUIDv4-Generator-Callable; mapped
   `(result, limit, limit_unit)` →
   `(code, severity, message)` per dokumentierter
   Heuristik (siehe §3.1).
3. **NEU `TickResult.emitted_alarms`-Feld** in
   `hexagon/core/domain/tick_result.py`: zusaetzliches
   `emitted_alarms: tuple[Alarm, ...] = ()`-Field mit
   Default-Wert (Backward-Compat; Pattern analog Welle-
   4a-`paused: bool = False`). Welle-4-Tests ohne
   Devices bekommen leeres Tupel.
4. **TickLoop-Alarm-Aggregations-Hook** in
   `hexagon/core/simulation/tick_loop.py`: am Ende des
   `_run_tick_body`, nach Bilanz-Aggregation, iteriert
   TickLoop ueber `self._devices`, ruft pro Device
   `device.drain_alarms()`, mapped jeden raw-Alarm auf
   Unified-`Alarm` (mit `self._run_id` + `simulation_
   time=now` + UUIDv4 pro Alarm) und sammelt die Tupel
   in `TickResult.emitted_alarms`. Deterministische
   Reihenfolge: Device-Iteration in Konstruktor-
   Reihenfolge (M2-Welle-6a-Pattern).
5. **NEU `AlarmStreamPort`-Driving-Port** unter
   `hexagon/ports/driving/alarm_stream.py`:
   `subscribe(run_id: str | None = None) ->
   AsyncIterator[Alarm]` + `publish(alarm: Alarm) ->
   None` + `subscriber_count`-Property. Surface 1:1
   parallel zu `TelemetryStreamPort` (ADR 0038 §2.1).
6. **NEU `InMemoryAlarmStream`-Driven-Adapter** unter
   `adapters/driven/alarm_stream_inmemory/`: asyncio-
   Pub/Sub mit bounded `asyncio.Queue(maxsize=64)` +
   Drop-Oldest-Backpressure (kleinerer Default als
   Telemetry weil Alarms typischerweise niederfrequent
   sind). Plus NEU `AlarmHistoryBuffer` (kein Port —
   adapter-internes Helper): in-memory Ring-Buffer der
   letzten N=200 Alarms fuer GET-History-Endpoint.
   Welle 5/M3-Welle-6c ersetzen das durch Postgres-
   Backing.
7. **TickLoop-Lifespan-Wiring**: nach jedem `tick()`-
   Aufruf publisht der `DemoTickLoopDriver` (oder ein
   neuer Hook im Driver) alle `TickResult.emitted_alarms`
   auf den `AlarmStreamPort`. Symmetrisch zur
   Telemetry-Publish-Wiring aus Welle 3.
8. **NEU REST-Endpoint `GET /runs/{run_id}/alarms`**
   in `_runs_router.py`: gibt die letzten N=50
   Alarms aus dem `AlarmHistoryBuffer` als JSON-Array
   zurueck (`AlarmsResponse`-Pydantic-Model mit
   `alarms: list[AlarmDto]`-Feld). 404 bei nicht-
   existentem Run (`GG-API-004`-Pattern).
9. **NEU WS-Endpoint `WS /runs/{run_id}/alarms-stream`**
   in `_runs_action_router.py`: subscribt am
   `AlarmStreamPort` mit `run_id`-Filter; pusht jeden
   Alarm als JSON (`asdict`-Serialisierung). Symmetrisch
   zur Welle-3-Telemetry-WS.
10. **NEU UI-Page `GET /runs/{run_id}/alarms`** in
    `ui/routes.py` + NEU `templates/alarms.html` +
    `_alarms_content.html`:
    - Initial-Render via HTMX-`hx-get` auf
      `/runs/{run_id}/alarms` (REST-History fuer
      Hydration).
    - Live-Update via HTMX-`hx-ext="ws"
      ws-connect="/runs/{run_id}/alarms-stream"`
      (analog Welle-3-Dashboard-WS-Bridge).
    - Tabellen-Layout mit 6 Pflicht-Spalten per
      `GG-UI-005`-Akzeptanz: **Zeit** (sim_time_ms) /
      **Ziel** (target) / **Schweregrad** (severity mit
      CSS-Klasse) / **Code** / **Nachricht** /
      **Status** (Welle-4b: immer `"active"`).
    - NEU 3 `AlarmSeverity`-CSS-Klassen analog Welle-3-
      Quality-Marker-Pattern (`severity-info`/
      `severity-warning`/`severity-critical`).
11. **Unit-Tests** + Integration-Test:
    - `tests/unit/hexagon/core/domain/test_alarm.py`
      (~6 Tests: Schema-Frozen-Smoke + 5 Mapper-
      Smokes mit Property-artigen Asserts).
    - `tests/unit/hexagon/core/simulation/test_tick_
      loop_alarm_aggregation.py` (~5 Tests: leere
      Aggregation ohne Devices, Single-Device-Drain,
      Multi-Device-Order, deterministisch nach
      Konstruktor-Reihenfolge, UUIDv4-Uniqueness).
    - `tests/unit/adapters/driven/alarm_stream_
      inmemory/test_stream.py` (~5 Tests; Pattern
      parallel zu Welle-3-Stream-Tests).
    - `tests/unit/adapters/driving/http_api/test_runs_
      router.py` EDIT (+2 Tests fuer GET /alarms).
    - `tests/unit/adapters/driving/http_api/test_runs_
      action_router.py` EDIT (+2 Tests fuer WS-Alarm-
      Subscribe).
    - `tests/unit/adapters/driving/ui/test_alarms_
      route.py` CREATE (3 Tests: full-page, HTMX-
      partial, 404).
    - `tests/integration/test_m5_welle_4b_alarms_
      smoke.py` CREATE: End-to-End-Smoke (Run anlegen
      + TickLoop mit 1 Battery-Device registrieren +
      Force-Alarm via `apply_command` mit power >
      rated_power_kw → 1 LIMITED-Alarm in
      `TickResult.emitted_alarms` → publish auf
      Stream → GET /alarms zeigt ihn → WS pusht ihn).

### 1.3 Welle-4b-Anti-Scope

Welle 4b liefert **nicht**:

- **Alarm-Status-Lifecycle** (`acknowledged`/`resolved`).
  Welle-4b-Status ist immer `"active"`. Status-
  Transitions via UI-Action-Buttons + Backend-Update
  sind Welle 6+/M6-Material (analog OTel-Span-Wrap-
  Defer). `GG-UI-005`-Akzeptanz fordert „aktualisierbare
  Tabelle", nicht „quittierbare Alarme"; Live-Update via
  WS-Subscribe + Initial-Load via GET erfuellen das
  produktiv.
- **Postgres-Alarm-Persistenz** (`GG-PERSIST-004`).
  Welle 4b bleibt In-Memory (`AlarmHistoryBuffer` als
  Ring-Buffer der letzten N=200 Alarms); echte Postgres-
  Schema-Migration + alembic-Revision sind M3-Welle-6c-
  Material (parallel zu Welle-4a-`PostgresRunRepository.
  update_status`/`get_status`-`NotImplementedError`-
  Stub-Pattern). `PostgresAlarmRepository`-Klasse wird
  in Welle 4b NICHT angelegt — das Repo-Pattern fuer
  Alarms ist Domain-Slot-Frage fuer Welle-6c.
- **Device-Alarm-Klassen-Migration.** Die 5 device-
  spezifischen Alarm-Klassen bleiben **unveraendert**.
  Welle 4b fuegt ausschliesslich NEU Mapper-Funktionen
  hinzu; kein Device-Internal-Schema-Change. Die ~41
  existierenden device-Alarm-Tests bleiben passing.
  Hexagonal-Rationale: Devices kennen keinen `run_id` /
  `simulation_time` / `severity` — diese Felder sind
  Run-Kontext, der erst beim Aggregator-Aufruf bekannt
  ist.
- **`AlarmSinkPort`-Driven-Slot** (im Sinne von ADR
  0014 §6). Welle 4b liefert einen Driving-Port
  (`AlarmStreamPort` — UI/API konsumiert) und einen
  adapter-internen `AlarmHistoryBuffer`, NICHT einen
  Driven-Persistenz-Port (der ist Postgres-Material
  fuer M3-Welle-6c). Die ADR-0014-§6-Erwartung wird
  damit teilweise erfuellt (Stream + History-Snapshot)
  und teilweise auf Welle-6c verschoben (Persistenz).
  Welle-4b-C1-ADR-0040 dokumentiert den Split
  explizit.
- **Fault-Injection-`fault_id`-Mapping.**
  `Alarm.fault_id` bleibt in Welle 4b immer `None` —
  Devices haben heute kein Bindeglied zwischen
  Command-getriebenem Alarm und einem Fault-Event.
  Fault-induzierte Alarms (M3-Welle-1 FaultPort-Pattern)
  koennten in Welle 6+ den `fault_id` produktiv setzen;
  Welle-4b-Schema haelt den Slot offen.
- **Scenario-Loader / Multi-Run-Alarm-Multiplexing.**
  Welle 4b nutzt den Welle-4a-Demo-TickLoop + den
  Single-Run-Stream. Welle 5 (Scenario-Loader) wirt
  Multi-Run-Streams produktiv.
- **OTel-Span-Wrap fuer Alarm-Publish.** M6 oder
  separate Hardening-Welle (analog `_protocol_otel_wrap.
  py` aus M4-Welle-6a + `OtelSpanWrappedTelemetryStream`-
  M6-Material aus ADR 0038 §3.3).
- **Cooperative-Pause-on-Critical-Alarm.** Die in ADR
  0039 §3.2 angedeutete „Auto-Pause bei kritischen
  Alarmen"-Symmetrie ist Welle-6+/M6-Material. Welle 4b
  pusht nur; der TickLoop reagiert nicht auf die
  publishten Alarms.

---

## 2. Scope

Welle 4b liefert in 4 Liefer-Commits (C0..C3, plus C1-
ADR):

1. **Slice-Doc-Anlage + Retro-Sync** (C0, dieser Commit)
   — dieses Dokument + `in-progress/README.md`-Bestand+
   Aktive-Welle-Block + Retro-Sync der 2→3-Decision-
   Forward-Pointer in `M5-ui-demo.md §3 Welle 4b` +
   `roadmap.md §3 M5 Welle-4a-Abschluss-Block` +
   `ADR 0039 §3.2 Welle-4b-Folge`.
2. **NEU ADR 0040 (Alarm-Aggregation + AlarmStreamPort)**
   (C1) — verankert Decisions 15/16/17 mit Status
   `Proposed`; Status-Pfad `Proposed → Provisional` nach
   C2-Code-Merge in C3.
3. **Code-Implementation + Unit/Integration-Tests** (C2)
   — alle 11 Sub-Items der §1.2-Liste.
4. **Status/DoD-Sync + ADR 0040 `Provisional` + Top-
   Level-Doku-Sync** (C3) — inkl. `M5-ui-demo.md §3
   Welle 4b` Status `Pending → Done`; Welle-4-Container-
   Section auf „komplett abgeschlossen" mit 4a+4b.

---

## 3. Architektur-Entscheidungen (Welle-4b-Decisions)

### 3.1 Decision 15 (NEU Unified `Alarm`-Domain-Schema + Mapper-Familie) — final fixiert

**Frage:** Wie integriert das System die 5 heterogenen
device-spezifischen Alarm-Klassen mit dem kanonischen
9-Feld-`spec/architecture.md`-Schema? Devices kennen
keinen `run_id`/`simulation_time`/`severity` —
Run-Kontext-Felder muessen beim Aggregator-Aufruf
zugesteuert werden.

**Optionen:**

- **A: Device-Alarm-Klassen erweitern** — adde
  `run_id`/`simulation_time`/`severity`/`code`/`message`/
  `status`/`fault_id` in jede der 5 Klassen. Verworfen:
  bricht Hexagonal-Reinheit (Devices kennen kein
  Lauf-Kontext); hoher Test-Migration-Aufwand (~41 Tests
  + 5 Device-Implementations); semantisch falsch (Felder
  wie `severity` sind Cross-Device-/UI-Semantik, nicht
  Device-Concern).
- **B: NEU unified `Alarm` + 5 Mapper** (final) —
  device-Alarms bleiben raw, Welle 4b fuegt einen
  Domain-Slot `hexagon/core/domain/alarm.py` mit
  Unified-`Alarm`-Frozen-Dataclass + 5 typisierten
  Mapper-Funktionen hinzu. Mapper sind reine Funktionen
  (kein Side-Effect, deterministisch), nehmen
  Run-Kontext (run_id, simulation_time_ms, alarm_id-
  Quelle) als zusaetzliche Argumente. Saubere Hexagonal-
  Architektur, kein Device-Internal-Touch.
- **C: Alarm-Schema im Adapter** — Adapter
  (`AlarmStream`) macht die Anreicherung. Verworfen:
  bricht Domain-vs-Adapter-Separation; Adapter sollten
  Transport sein, nicht Schema-Logik tragen; macht
  Mapper-Logik schwer testbar (braucht Adapter-Setup).

**Entscheidung: Option B** — NEU `Alarm`-Domain-Type +
5 Mapper-Funktionen.

**Surface-Konstruktion:**

```python
# hexagon/core/domain/alarm.py
from typing import Literal

AlarmSeverity = Literal["info", "warning", "critical"]
"""3-Welle-4b-Default; OTel-/syslog-aehnliche Hierarchie."""

AlarmStatus = Literal["active"]
"""Welle-4b: nur `active`; Lifecycle-Erweiterung
(`acknowledged`/`resolved`) ist Welle 6+/M6-Material."""


@dataclass(frozen=True, slots=True)
class Alarm:
    alarm_id: str            # UUIDv4
    run_id: str              # Lauf-Identitaet
    simulation_time_ms: int  # Tick-Zeitpunkt
    target: str              # = target_device_id
    code: str                # Mapper-Output, z.B. "power_clamp_limited"
    severity: AlarmSeverity
    message: str             # Mensch-lesbar
    status: AlarmStatus      # Welle-4b: "active"
    fault_id: str | None     # Welle 4b: immer None


# Mapper (vereinfacht):
def alarm_from_battery_alarm(
    raw: BatteryAlarm,
    *,
    run_id: str,
    simulation_time_ms: int,
    alarm_id: str,
) -> Alarm: ...
# analog: from_pv_alarm, from_load_alarm,
# from_grid_connection_alarm, from_smart_meter_alarm
```

**Mapping-Heuristik `(result, limit, limit_unit)` →
`(code, severity, message)`:**

Pattern aus `PvAlarm`-Docstring (§Welle-3-Review M-2):
„IMMER `(result, limit)` als Tupel auswerten".

| Device | `result` | Heuristik | `code` | `severity` | `message`-Template |
| --- | --- | --- | --- | --- | --- |
| Battery/PV/Load/GridConnection | `LIMITED` | Power-Clamp | `"power_clamp_limited"` | `"warning"` | `f"power command clamped to {limit} {limit_unit}"` |
| Battery/PV/Load/GridConnection | `REJECTED` | Sign- oder SOC-Reject | `"command_rejected"` | `"critical"` | `f"command rejected: limit {limit} {limit_unit}"` |
| SmartMeter | `LIMITED` (n/a) | — (SmartMeter rejecten nur) | — | — | — |
| SmartMeter | `REJECTED` | reason-codiert | `"smart_meter_rejected"` | `"warning"` | `f"smart-meter rejected: {reason}"` |

**Konsequenz:**
- 5 Mapper-Funktionen, jede ~5-10 Zeilen, alle reine
  Funktionen (deterministisch + side-effect-free).
- Property-Tests: gleiche Inputs → gleiche Outputs;
  UUIDv4 wird extern injiziert (nicht in Mapper
  generiert) damit Tests deterministisch sind.
- `Alarm` ist frozen + slots wie `RunMetadata` /
  `TelemetryPoint`; AC-DOMAIN-FROZEN-Compliance
  automatisch.

### 3.2 Decision 16 (TickLoop-Alarm-Aggregation via `TickResult.emitted_alarms`) — final fixiert

**Frage:** Wo werden die device-Alarms drained + auf
Unified-`Alarm` gemapped + aggregiert? Wer kennt
`run_id` + `simulation_time_ms`?

**Optionen:**

- **A: TickLoop drainst + mapped + sammelt in
  `TickResult.emitted_alarms`** (final) — am Ende des
  `_run_tick_body`, nach Bilanz-Aggregation. TickLoop
  kennt `run_id` (`self._run_id`) und `simulation_time`
  (aus dem `now`-Tick-Ende-Wert). Pattern parallel zu
  `TickResult.emitted_telemetry` (M2-Welle-6a-Pattern).
- **B: Separater `AlarmAggregator`-Klasse** — composition
  over inheritance. Verworfen: YAGNI; TickLoop hat
  bereits Devices-Iteration + run_id + clock; ein
  zusaetzlicher Aggregator dupliziert die Iteration ohne
  Vorteil. Welle-7-Refactor moeglich falls Multi-Run-
  Multiplexing kommt.
- **C: Adapter-Side-Drain (AlarmStream subscribt am
  Tick-Lifecycle)** — Adapter pollt periodisch.
  Verworfen: kein Lifecycle-Event-Bus etabliert;
  Polling-Latenz reisst Determinismus auf.

**Entscheidung: Option A** — TickLoop-internes Drain +
Map + Aggregate.

**Aggregations-Reihenfolge (deterministisch):**

```python
# Pseudocode in _run_tick_body, am Ende vor return:
alarms: list[Alarm] = []
for device in self._devices:  # Konstruktor-Reihenfolge
    raw_alarms = device.drain_alarms()
    for raw in raw_alarms:
        alarms.append(
            _map_device_alarm(  # dispatched per isinstance
                raw,
                run_id=self._run_id,
                simulation_time_ms=now,
                alarm_id=self._alarm_id_source.next(),
            )
        )

result = TickResult(
    tick=self._tick_count,
    simulation_time=now,
    popped_events=popped,
    emitted_telemetry=tuple(emitted),
    emitted_alarms=tuple(alarms),  # NEU
)
```

**UUIDv4-Source (deterministisch fuer Tests):**

`TickLoop.__init__` bekommt optional ein
`alarm_id_source: Callable[[], str] = uuid.uuid4`-
Argument. Production-Default ist `uuid.uuid4`; Tests
injizieren einen monoton zaehlenden Stub
(`itertools.count()` als String) fuer deterministische
Assertions. Pattern analog `random: RandomPort` aus M1.

**Konsequenz:**
- `TickLoop.__init__` bekommt einen optionalen Kwarg
  `alarm_id_source: Callable[[], str] | None = None`.
  Default `None` → in-Konstruktor auf `uuid.uuid4`
  resolved (kein Import-Top-Level-Side-Effect).
- `TickResult.emitted_alarms: tuple[Alarm, ...] = ()`
  mit Default-Wert (Backward-Compat).
- Keine Snapshot-Aenderung: `emitted_alarms` ist
  Tick-Output, nicht persistenter State. ADR 0015
  Snapshot-Format bleibt unangetastet — Pattern
  identisch zu `emitted_telemetry`.
- Tick-Determinismus bleibt (`GG-SIM-001`): gleiche
  Device-Reihenfolge + gleiche `drain_alarms`-Aufrufe +
  gleiche `alarm_id_source` → gleiche Output-Tupel.

### 3.3 Decision 17 (AlarmStreamPort-Surface + `GET /runs/{id}/alarms`-History-Endpoint) — final fixiert

**Frage:** Wie konsumiert die UI die Alarms? Live-Stream
(WS) vs. Polling-History (REST) vs. beides?

**Optionen:**

- **A: Nur WS-Subscribe** (analog `TelemetryStreamPort`).
  Verworfen: Tab-Reload verliert die History; Initial-
  Render ist leer bis erster neuer Alarm; UX-feindlich
  fuer niederfrequente Alarms.
- **B: Nur GET-Polling** (analog Welle-4a-Status-
  Endpoint). Verworfen: 1s-Polling fuer potenziell
  niederfrequente Alarms ist verschwenderisch und hat
  Update-Latenz; Live-Feeling fehlt.
- **C: Beide — WS-Subscribe + GET-History-Endpoint**
  (final). UI-Tabelle nutzt `hx-get` auf
  `/runs/{id}/alarms` fuer Initial-Hydration + `hx-ext=
  "ws" ws-connect="/runs/{id}/alarms-stream"` fuer
  Live-Updates. Best-of-both: schnelle Initial-Load
  ohne Wartepause + Live-Feeling fuer neue Alarms +
  Resilience gegen WS-Reconnect (HTMX `ws-ext` kann
  reconnect, History bleibt persistent in der UI).

**Entscheidung: Option C** — beide.

**`AlarmStreamPort`-Surface (1:1 parallel zu
`TelemetryStreamPort`, ADR 0038 §2.1):**

```python
# hexagon/ports/driving/alarm_stream.py
class AlarmStreamPort(Protocol):
    def publish(self, alarm: Alarm) -> None:
        """Sync-publish; pusht an alle aktiven Subscribers."""

    async def subscribe(
        self, run_id: str | None = None
    ) -> AsyncIterator[Alarm]:
        """Async-Generator; liefert publishte Alarms,
        optional nach run_id gefiltert. Subscriber-Slot
        wird im finally-Block freigegeben."""

    @property
    def subscriber_count(self) -> int: ...
```

**`InMemoryAlarmStream`-Adapter:**

- asyncio-Pub/Sub mit bounded `asyncio.Queue(maxsize=64)`
  (kleinerer Default als Telemetry's 128, weil Alarms
  niederfrequent).
- Drop-Oldest-Backpressure via `contextlib.suppress
  (asyncio.QueueEmpty)`-Drain im `publish`.
- `try/finally`-Cleanup im `subscribe`-AsyncGenerator
  (Welle-3-Pattern unveraendert).

**`AlarmHistoryBuffer`-Adapter-Helper:**

- In-Memory-Ring-Buffer der letzten N=200 Alarms (FIFO).
- Welle-4b-Stub fuer Postgres-Persistenz (M3-Welle-6c).
- Public-Methode `get_recent(run_id: str | None, limit:
  int = 50) -> tuple[Alarm, ...]` fuer GET-Endpoint.

**REST-Endpoint `GET /runs/{run_id}/alarms`:**

- Path: `/runs/{run_id}/alarms`.
- Query-Param: `?limit=50` (default; max 200).
- Response: `AlarmsResponse{alarms: list[AlarmDto]}`
  als JSON-Array (neueste zuerst).
- 404 mit `GG-API-004`-`code="run_not_found"` analog
  Welle-1-Pattern.
- `tags=["runs"]` fuer OpenAPI-Schema-Konsistenz.

**WS-Endpoint `WS /runs/{run_id}/alarms-stream`:**

- Path: `/runs/{run_id}/alarms-stream` (separat von
  `/alarms`, damit der REST-GET-Pfad nicht mit dem WS-
  Upgrade-Pfad kollidiert; symmetrisch zur Welle-3-
  `/telemetry` vs `/runs/{id}/dashboard`-Trennung).
- Subscribt am `AlarmStreamPort` mit `run_id`-Filter.
- 1008-Close (Policy-Violation) bei nicht-existentem
  Run (Welle-1+3-Pattern).
- JSON-Payload via `dataclasses.asdict(alarm)`.

**Konsequenz:**
- 1 NEU Driving-Port + 1 NEU Driven-Adapter (Pattern
  identisch zu Welle 3).
- 1 NEU REST-Endpoint (`GET /alarms`).
- 1 NEU WS-Endpoint (`WS /alarms-stream`).
- 1 NEU UI-Page (`GET /runs/{id}/alarms`).
- OpenAPI-Schema-Erweiterung (REST-Endpoint im
  Schema; WS bewusst nicht — analog ADR 0037 §3-
  Klarstellung).

---

## 4. Liefer-Reihenfolge (4 Commits)

### Pre-C0 — bereits erledigt

- Pre-C0a `d1b0eb7` (Self-Close-Move; rename-only).
- Pre-C0b `e325307` (Cross-Doc-Refs-Sync, 4 Files).

### C0 — `docs(plan)`: M5-welle-4b Slice-Doc + Retro-Sync

Slice-Doc-Anlage (dieses Dokument) +
`in-progress/README.md`-Bestand + Aktive-Welle-Marker
auf Welle-4b-C0 + **Retro-Sync der Welle-4a-Era-
Forward-Pointer** in 3 Docs:

- `docs/plan/planning/in-progress/M5-ui-demo.md §3
  Welle 4b`: 2→3-Decisions umgestellt; konkrete
  Decision-15/16/17-Bullets statt Platzhalter-„NEU
  Decision 15 (Alarm-Aggregation-Architektur)" +
  Forward-Pointer-Update auf `Slice-Begleit-Doc
  [M5-welle-4b.md]`.
- `docs/plan/planning/in-progress/roadmap.md §3 M5`:
  Welle-4a-Abschluss-Block-Subdivision-Hinweis von
  „NEU ADR 0040 geplant mit Decisions 15/16" auf
  „...mit Decisions 15/16/17" umgestellt.
- `docs/plan/adr/0039-run-control-and-status-tracking.
  md §3.2`: Welle-4b-Folge-Bullet von „2 Decisions
  (15/16, geplant)" auf „3 Decisions (15/16/17, final
  aus C0-Pre-Research)" umgestellt.

### C1 — `docs(adr)`: NEU ADR 0040 (Alarm-Aggregation + AlarmStreamPort)

Erzeugt `docs/plan/adr/0040-alarm-aggregation-and-stream-
port.md` (~400-500 Zeilen) mit Status `Proposed`:

- §1 Context — `GG-UI-005` UI-Akzeptanz + `ADR 0014 §6`
  Forward-Pointer-Erbschaft + `spec/architecture.md`-
  Alarm-Schema-Verankerung + Welle-4a-Anti-Scope-Item.
- §2 Decisions:
  - §2.1 Decision 15 (Schema + Mapper-Familie).
  - §2.2 Decision 16 (TickLoop-Aggregation).
  - §2.3 Decision 17 (Stream-Port + History-Endpoint).
- §3 Konsequenzen:
  - Welle-4b-Folge, Welle-5-Folge, Welle-6c-Persistenz-
    Folge, M6-OTel-Folge, Architektur-Konsistenz.
- §4 Out-of-Scope (Status-Lifecycle, Postgres,
  Device-Migration, AlarmSinkPort-Driven-Slot,
  fault_id-Mapping, Multi-Run-Multiplexing, OTel-Wrap,
  Cooperative-Pause-on-Critical).
- §5 Status-Pfad (`Proposed → Provisional` mit C3 nach
  C2-Code-Merge; `Accepted` mit M5-Welle-7).
- §6 Folge-Pflichten — Welle-4b-C2-Code-Merge-File-
  Liste + Welle-4b-C3-Promotion + Welle-5/Welle-6c-
  Forward-Pointer.
- §7 References — `spec/architecture.md §Alarm`,
  `spec/lastenheft.md GG-UI-005 + GG-PERSIST-004`,
  ADR 0014 §6, ADR 0038 (Pattern-Vorbild),
  ADR 0039 §3.2 (Welle-4b-Forward).

Plus `docs/plan/adr/README.md`-Tabellen-Zeile fuer 0040
(Status `Proposed` mit Commit-Hash-Verweis auf C1-
Commit).

### C2 — `feat(welle-4b)`: Alarm-Domain + TickLoop-Aggregation + Stream-Port + Adapter + 2 Endpoints + UI + Tests

Liefert alle 11 Sub-Items der §1.2-Liste:

1. NEU `hexagon/core/domain/alarm.py` mit `Alarm`-
   Dataclass + `AlarmSeverity`/`AlarmStatus`-Literals
   + 5 Mapper-Funktionen.
2. EDIT `hexagon/core/domain/tick_result.py`: NEU
   `emitted_alarms: tuple[Alarm, ...] = ()`-Feld.
3. EDIT `hexagon/core/simulation/tick_loop.py`:
   `alarm_id_source: Callable[[], str] | None = None`
   Konstruktor-Param + `_attach_alarm_id_source`-
   Helper + Drain+Map+Aggregate-Hook in
   `_run_tick_body` vor `return`.
4. NEU `hexagon/ports/driving/alarm_stream.py` mit
   `AlarmStreamPort`-Protocol.
5. NEU `adapters/driven/alarm_stream_inmemory/`-Paket:
   `__init__.py` (Re-Export) + `stream.py` (Pub/Sub) +
   `history_buffer.py` (Ring-Buffer).
6. EDIT `adapters/driving/http_api/_dependencies.py`:
   NEU `get_alarm_stream` + `get_alarm_history_buffer`
   FastAPI-Dependencies + Not-Configured-Errors.
7. EDIT `adapters/driving/http_api/_runs_router.py`:
   NEU `GET /runs/{run_id}/alarms` mit
   `AlarmsResponse`-Schema (Pydantic).
8. EDIT `adapters/driving/http_api/_runs_action_router.
   py`: NEU `WS /runs/{run_id}/alarms-stream` mit
   Subscribe-Pattern.
9. EDIT `adapters/driving/http_api/_schemas.py`:
   NEU `AlarmDto` + `AlarmsResponse`-Pydantic-Models.
10. EDIT `adapters/driving/http_api/_demo_setup.py`:
    Demo-TickLoop bekommt eine `BatteryDevice`-Instanz
    + DemoTickLoopDriver publisht
    `TickResult.emitted_alarms` auf den Stream + den
    History-Buffer. (Optional fuer Welle 4b — koennte
    auch nur 0 Alarms im Demo geben; entscheidet sich
    am Demo-UX-Aspekt waehrend C2.)
11. NEU `adapters/driving/http_api/app.py`:
    `configure_alarm_stream`-Injection-Punkt; Lifespan-
    Wiring im `_lifespan`.
12. NEU UI: `templates/alarms.html` +
    `_alarms_content.html` + EDIT `routes.py` (NEU
    `GET /runs/{run_id}/alarms`-Page) + EDIT
    `static/style.css` (3 AlarmSeverity-CSS-Klassen) +
    EDIT `templates/navigation.html` (Alarms-Link).
13. NEU Tests (siehe §1.2.11; ~25-28 neue Unit + 1
    Integration).

### C3 — `docs(plan|adr)`: Welle-4b Status/DoD-Sync + Top-Level-Doku-Sync

Status-/DoD-Sync nach C2-Code-Merge:

- `M5-welle-4b.md §0 Status` von `In Progress → Done`
  mit Liefer-Hashes (C0/C1/C2/C3) + DoD-Verifikation.
- `M5-ui-demo.md §3 Welle 4b` Status `Pending → Done`
  mit Liefer-Hashes; alle Welle-4b-Bullets abgehakt.
  Plus optional: Welle-4-Container-Section-Header von
  „Subdivision 4a/4b" auf „komplett Done" aktualisieren
  (analog Welle-3-Container-Pattern).
- `M5-welle-4b.md §9 DoD-Checkliste` Items abhaken.
- ADR 0040 `Proposed → Provisional` mit C2-Code-Merge-
  Beleg.
- Top-Level-Doku-Sync:
  - `docs/plan/planning/in-progress/roadmap.md §3 M5`
    aktualisiert mit Welle-4b-Bullet-Belegung; ADR-
    Status-Update.
  - `docs/plan/planning/in-progress/README.md` —
    Welle-4b-Abschluss-Block + Welle-5-aktiv-Marker
    (Welle 5 = Demo-Pipeline ist der naechste Slice).
  - `README.md` + `README.de.md` — Test-Counts
    aktualisiert; Slice-Liste.
  - `docs/plan/adr/README.md`-Tabellen-Zeile fuer
    0040 auf `Provisional`.

## 5. Critical Files

| Datei                                                                                | Phase | Aktion                                                                |
| ------------------------------------------------------------------------------------ | ----- | --------------------------------------------------------------------- |
| `docs/plan/planning/in-progress/M5-welle-4b.md`                                      | C0    | CREATE (dieses Dokument)                                              |
| `docs/plan/planning/in-progress/README.md`                                           | C0    | EDIT (Bestand-Zeile + Aktive-Welle-Marker auf 4b-C0)                  |
| `docs/plan/planning/in-progress/M5-ui-demo.md`                                       | C0    | EDIT (§3 Welle 4b 2→3 Decisions; Retro-Sync)                          |
| `docs/plan/planning/in-progress/roadmap.md`                                          | C0    | EDIT (§3 M5 Welle-4a-Abschluss-Block 2→3 Decisions; Retro-Sync)       |
| `docs/plan/adr/0039-run-control-and-status-tracking.md`                              | C0    | EDIT (§3.2 Welle-4b-Folge 2→3 Decisions; Retro-Sync)                  |
| `docs/plan/adr/0040-alarm-aggregation-and-stream-port.md`                            | C1    | CREATE (NEU ADR; Status `Proposed`)                                   |
| `docs/plan/adr/README.md`                                                            | C1    | EDIT (Tabellen-Zeile fuer 0040)                                       |
| `src/grid_gym/hexagon/core/domain/alarm.py`                                          | C2    | CREATE (`Alarm` + Literals + 5 Mapper)                                |
| `src/grid_gym/hexagon/core/domain/tick_result.py`                                    | C2    | EDIT (`emitted_alarms`-Feld)                                          |
| `src/grid_gym/hexagon/core/simulation/tick_loop.py`                                  | C2    | EDIT (`alarm_id_source`-Kwarg + Drain-Hook)                           |
| `src/grid_gym/hexagon/ports/driving/alarm_stream.py`                                 | C2    | CREATE (Protocol)                                                     |
| `src/grid_gym/adapters/driven/alarm_stream_inmemory/__init__.py`                     | C2    | CREATE                                                                |
| `src/grid_gym/adapters/driven/alarm_stream_inmemory/stream.py`                       | C2    | CREATE                                                                |
| `src/grid_gym/adapters/driven/alarm_stream_inmemory/history_buffer.py`               | C2    | CREATE                                                                |
| `src/grid_gym/adapters/driving/http_api/_dependencies.py`                            | C2    | EDIT (`get_alarm_stream` + `get_alarm_history_buffer`)                |
| `src/grid_gym/adapters/driving/http_api/_runs_router.py`                             | C2    | EDIT (`GET /alarms`)                                                  |
| `src/grid_gym/adapters/driving/http_api/_runs_action_router.py`                      | C2    | EDIT (`WS /alarms-stream`)                                            |
| `src/grid_gym/adapters/driving/http_api/_schemas.py`                                 | C2    | EDIT (`AlarmDto` + `AlarmsResponse`)                                  |
| `src/grid_gym/adapters/driving/http_api/_demo_setup.py`                              | C2    | EDIT (Demo-Battery + Alarm-Publish-Wiring; optional)                  |
| `src/grid_gym/adapters/driving/http_api/app.py`                                      | C2    | EDIT (`configure_alarm_stream` + Lifespan)                            |
| `src/grid_gym/adapters/driving/ui/routes.py`                                         | C2    | EDIT (`GET /runs/{id}/alarms`-Page)                                   |
| `src/grid_gym/adapters/driving/ui/templates/alarms.html`                             | C2    | CREATE                                                                |
| `src/grid_gym/adapters/driving/ui/templates/_alarms_content.html`                    | C2    | CREATE                                                                |
| `src/grid_gym/adapters/driving/ui/templates/navigation.html`                         | C2    | EDIT (Alarms-Link)                                                    |
| `src/grid_gym/adapters/driving/ui/static/style.css`                                  | C2    | EDIT (3 AlarmSeverity-CSS-Klassen)                                    |
| `tests/unit/hexagon/core/domain/test_alarm.py`                                       | C2    | CREATE                                                                |
| `tests/unit/hexagon/core/simulation/test_tick_loop_alarm_aggregation.py`             | C2    | CREATE                                                                |
| `tests/unit/adapters/driven/alarm_stream_inmemory/test_stream.py`                    | C2    | CREATE                                                                |
| `tests/unit/adapters/driving/http_api/test_runs_router.py`                           | C2    | EDIT (+2 Tests fuer `/alarms`)                                        |
| `tests/unit/adapters/driving/http_api/test_runs_action_router.py`                    | C2    | EDIT (+2 Tests fuer WS-Stream)                                        |
| `tests/unit/adapters/driving/ui/test_alarms_route.py`                                | C2    | CREATE                                                                |
| `tests/integration/test_m5_welle_4b_alarms_smoke.py`                                 | C2    | CREATE                                                                |
| `docs/plan/planning/in-progress/M5-ui-demo.md`                                       | C3    | EDIT (§3 Welle 4b Status + DoD-Boxen)                                 |
| `docs/plan/planning/in-progress/roadmap.md`                                          | C3    | EDIT (§3 M5-Welle-4b-Bullet)                                          |
| `docs/plan/planning/in-progress/README.md`                                           | C3    | EDIT (Welle-4b-Abschluss + Welle-5-aktiv)                             |
| `README.md` + `README.de.md`                                                         | C3    | EDIT (Test-Counts + Slice-Liste)                                      |

## 6. Verifikationspfad

**Welle-4b-DoD:**

1. `M5-welle-4b.md` produktiv mit §1-§9.
2. **NEU ADR 0040** mit Status `Proposed → Provisional`
   nach C2.
3. **NEU `Alarm`-Domain-Type** + `AlarmSeverity` +
   `AlarmStatus` Literals + 5 Mapper produktiv.
4. **`TickResult.emitted_alarms`** Feld mit Default
   `()`; bestehende Tests passing ohne Aenderung.
5. **TickLoop-Drain-Hook** produktiv mit
   `alarm_id_source`-Injection; deterministisch.
6. **NEU `AlarmStreamPort`** unter `hexagon/ports/
   driving/`.
7. **NEU `InMemoryAlarmStream` + `AlarmHistoryBuffer`**
   unter `adapters/driven/alarm_stream_inmemory/`.
8. **NEU `GET /runs/{id}/alarms`** + **NEU `WS /runs/
   {id}/alarms-stream`** produktiv.
9. **NEU UI-Page `GET /runs/{run_id}/alarms`** mit
   6-Spalten-Tabelle + WS-Live-Update + HTMX-History-
   Hydration.
10. **Unit-Tests** (~25-28 neue) + **Integration-Test**
    (1 neuer).
11. `make test-unit` gruen (1650 + ~25-28).
12. `make test-integration` gruen (50 + 1).
13. `make arch-check` 20/20 KEPT (NEU Port unter
    `hexagon/ports/driving/`; NEU Adapter unter
    `adapters/driven/alarm_stream_inmemory/`; ggf.
    `AC-ADAPTER-PURE`-`ignore_imports`-Extension fuer
    Demo-Setup-Erweiterung).
14. `make typecheck` mit `strict_bytes` gruen.
15. `make gates` cache-frei gruen ohne Override.
16. `make docs-check` cache-frei gruen.
17. `make openapi-validate` cache-frei gruen (NEU
    `/alarms`-Endpoint im Schema).
18. **`GG-UI-005`-Akzeptanz** erfuellt durch 6-Spalten-
    Tabelle + Live-Update.

**Welle-4b-Gate:** `make gates` + `make docs-check` +
`make openapi-validate` cache-frei gruen ohne Override.

## 7. Risiken

- **Mapper-Heuristik-Drift.** Die `(result, limit)` →
  `(code, severity, message)`-Mapping-Tabelle aus §3.1
  ist Welle-4b-Best-Effort; ein zukuenftiges Welle-7-
  Device (z. B. `WindDevice`) koennte neue Alarm-
  Semantik mitbringen, die nicht in die 3-Severity-
  Hierarchie passt. Mitigation: jede Mapper-Funktion
  ist eine Funktion (nicht eine Methode); neue Device-
  Familien adden eine neue Funktion ohne bestehenden
  Code zu touchen. Pattern-Test stellt sicher, dass
  jede device-Alarm-Klasse einen Mapper hat.
- **TickResult-Field-Compat.** `emitted_alarms`-Field
  mit Default `()` ist backward-kompatibel, aber
  Tests die `TickResult` per positional-args
  konstruieren (anti-pattern; tests sollen kwargs
  benutzen) koennten brechen. Mitigation: Welle-4b-C2
  prueft alle ~50 `TickResult(...)`-Konstruktor-
  Stellen; kwargs-only ist seit M2 etabliert.
- **AlarmStream-Lifespan-Cleanup-Race.** Analog Welle-
  3-Demo-Generator + Welle-4a-DemoTickLoopDriver: wenn
  der Stream beim Shutdown nicht sauber gecanceled
  wird, leaken Subscribers. Mitigation: FastAPI-
  Lifespan-Pattern aus Welle 3 + Welle 4a wiederverwendet.
- **History-Buffer-Memory-Bloat bei Long-Runs.**
  Ring-Buffer mit N=200 ist Welle-4b-Default. Bei
  Welle-6c-Postgres-Migration wird der Buffer abgeloest;
  bis dahin gilt der Trade-off „neueste Alarms ueberleben,
  alte gehen verloren bei Tab-Reload nach langer
  Inaktivitaet". Akzeptabel fuer Demo-UX.
- **UUIDv4-Collision (theoretisch).** Mitigation:
  `alarm_id_source` ist injizierbar; Tests nutzen
  monoton zaehlenden Stub, Production nutzt `uuid.
  uuid4()` (Kollisionswahrscheinlichkeit
  vernachlaessigbar).
- **WS-Endpoint-Path-Konflikt `/alarms` vs
  `/alarms-stream`.** REST-GET `/alarms` und
  WS `/alarms-stream` sind explizit verschiedene Paths,
  damit `GET /alarms` nicht versehentlich als WS-
  Upgrade-Pfad interpretiert wird. Pattern analog
  Welle-3-`/dashboard` (REST) vs `/telemetry` (WS).
- **Anti-Scope-Slippage Status-Lifecycle.** UI koennte
  „acknowledged"-Button verlocken; Welle-4b-Anti-Scope
  haelt das raus. Mitigation: UI-Template enthaelt
  KEINE Action-Buttons fuer Status-Mutation; Welle-4b-
  C0-Slice-Doc verankert das explizit.

## 8. Wandert nach

- Bei C3-Closure: `M5-welle-4b.md` bleibt in
  `in-progress/` (Pattern analog Welle 1+2+3+4a). Self-
  Close-Move folgt als M5-Welle-5-Pre-C0.
- `M5-ui-demo.md` bleibt in `in-progress/` bis
  M5-Welle-7-Closure.
- Welle 5 (Demo-Pipeline + Scenario-Loader) als
  naechster aktiver Schritt nach Welle 4b; Welle-4-
  Subdivision (4a + 4b) damit komplett abgeschlossen.

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [ ] **NEU ADR 0040 `Proposed → Provisional`** mit
  C2-Code-Merge-Beleg.
- [ ] **NEU `Alarm`-Domain-Type** mit 9-Feld-Schema +
  `AlarmSeverity` + `AlarmStatus` Literals + 5
  typisierte Mapper-Funktionen.
- [ ] **`TickResult.emitted_alarms`-Feld** mit Default
  `()` (Backward-Compat).
- [ ] **TickLoop-Drain-Hook** produktiv;
  `alarm_id_source: Callable[[], str] | None = None`-
  Konstruktor-Param; deterministische Aggregations-
  Reihenfolge nach Device-Konstruktor-Index.
- [ ] **NEU `AlarmStreamPort`** unter
  `hexagon/ports/driving/alarm_stream.py`.
- [ ] **NEU `InMemoryAlarmStream`** + **NEU
  `AlarmHistoryBuffer`** unter `adapters/driven/
  alarm_stream_inmemory/`.
- [ ] **NEU `GET /runs/{run_id}/alarms`** mit
  `AlarmsResponse`-Schema + OpenAPI-Eintrag.
- [ ] **NEU `WS /runs/{run_id}/alarms-stream`** mit
  Subscribe-Pattern + 1008-Close fuer unknown Runs.
- [ ] **NEU UI-Page `GET /runs/{run_id}/alarms`** mit
  6-Spalten-Tabelle (Zeit/Ziel/Schweregrad/Code/
  Nachricht/Status) + HTMX-Hydration + WS-Live-Update.
- [ ] **3 AlarmSeverity-CSS-Klassen** in
  `style.css` (`severity-info`/`severity-warning`/
  `severity-critical`).
- [ ] **Lifespan-Wiring**: `_demo_setup.py` publisht
  `TickResult.emitted_alarms` auf den Stream + History-
  Buffer; `configure_alarm_stream`-Injection-Punkt.
- [ ] **Unit-Tests** (~25-28 neue) — Domain +
  Aggregation + Stream + Endpoints + UI-Route.
- [ ] **Integration-Test**
  `test_m5_welle_4b_alarms_smoke.py` produktiv (End-
  to-End-Workflow).
- [ ] **`make test-unit`** gruen (~1675-1678 passed).
- [ ] **`make test-integration`** gruen (51 passed).
- [ ] **`make arch-check`** 20/20 KEPT.
- [ ] **`make typecheck`** mit `strict_bytes` gruen.
- [ ] **`make gates`** cache-frei gruen ohne Override.
- [ ] **`make docs-check`** cache-frei gruen.
- [ ] **`make openapi-validate`** cache-frei gruen.
- [ ] **`GG-UI-005` (Alarm-Visualisierung)** erfuellt
  durch Alarms-Page + 6-Pflicht-Spalten +
  Live-Update via WS + Initial-Hydration via GET.
- [ ] **ADR-0014-§6-Forward-Pointer aufgeloest**:
  „AlarmSinkPort kommt mit M3" → Welle 4b liefert
  Driving-Port + History-Buffer; Postgres-Persistenz
  weiter auf M3-Welle-6c-Material verschoben (ADR 0040
  dokumentiert den Split explizit).
- [ ] **C3-Top-Level-Doku-Sync** produktiv: 6+ Docs
  auf Welle-4b-Closure-Stand (`M5-welle-4b.md §0/§9`,
  `M5-ui-demo.md §3 Welle 4b`, `in-progress/README.md`,
  `in-progress/roadmap.md §3 M5`, `README.md` +
  `README.de.md`-Test-Counts + ADR 0040 +
  `docs/plan/adr/README.md`).

**Anti-Scope-Verifikation (Welle 4b NICHT):**

- [ ] Kein Status-Lifecycle (`acknowledged`/`resolved`);
  `AlarmStatus`-Literal hat NUR `"active"`.
- [ ] Keine Postgres-Alarm-Persistenz (M3-Welle-6c).
- [ ] Keine Device-Alarm-Klassen-Migration (5 Klassen
  bleiben unveraendert; 41+ existierende Tests passing).
- [ ] Kein `AlarmSinkPort`-Driven-Slot (ADR 0014 §6
  partial; voller Sink ist Welle-6c).
- [ ] Kein `fault_id`-Mapping in Welle 4b (Schema-
  Feld bleibt offen, immer `None`).
- [ ] Kein Scenario-Loader / Multi-Run-Multiplexing
  (Welle 5).
- [ ] Kein OTel-Span-Wrap (M6).
- [ ] Keine Cooperative-Pause-on-Critical-Alarm-
  Symmetrie (Welle 6+).
- [ ] Keine UI-Action-Buttons fuer Status-Mutationen.
- [ ] Keine `noqa`-Marker.

---

## References

- [`../done/M5-welle-4a.md`](../done/M5-welle-4a.md) —
  Welle-4a-Closure (Replay-Controls + TickLoop-Wiring;
  Welle-4a-Anti-Scope-Item: „Keine Alarm-Aggregation /
  AlarmStreamPort / Alarm-Tabelle-UI (Welle 4b)" loest
  Welle 4b ein).
- [`../done/M5-welle-3.md`](../done/M5-welle-3.md) —
  Welle-3-Closure (TelemetryStreamPort als Pattern-
  Vorbild fuer `AlarmStreamPort` per Decision 17).
- [`M5-ui-demo.md`](M5-ui-demo.md) §3 Welle 4b
  (kanonische Slice-Spezifikation; Welle-4b-C0
  Retro-Sync der 2→3-Decision-Forward-Pointer).
- [`../../adr/0014-battery-snapshot-schema.md`](../../adr/0014-battery-snapshot-schema.md)
  §6 — „AlarmSinkPort kommt mit M3" Forward-Pointer-
  Erbschaft; Welle 4b loest den Driving-Port + History-
  Snapshot-Anteil aus, Postgres-Persistenz bleibt
  Welle-6c-Material.
- [`../../adr/0038-telemetry-stream-port.md`](../../adr/0038-telemetry-stream-port.md)
  — Pattern-Vorbild fuer `AlarmStreamPort` (Decision 17);
  Welle-4b spiegelt Surface + Backpressure + Lifecycle.
- [`../../adr/0039-run-control-and-status-tracking.md`](../../adr/0039-run-control-and-status-tracking.md)
  §3.2 — Welle-4a-Forward-Pointer „Alarm-Aggregation +
  AlarmStreamPort kommt in Welle 4b mit NEU ADR 0040".
- [`../../../../spec/lastenheft.md §17`](../../../../spec/lastenheft.md)
  (`GG-UI-005` Alarm-Visualisierung-Akzeptanz: 6 Pflicht-
  Spalten Zeit/Ziel/Schweregrad/Code/Nachricht/Status).
- [`../../../../spec/lastenheft.md §23`](../../../../spec/lastenheft.md)
  (`GG-PERSIST-004` Alarm-Historien-Persistenz —
  M3-Welle-6c-Material, Welle-4b-Anti-Scope).
- [`../../../../spec/architecture.md §Alarm`](../../../../spec/architecture.md)
  (kanonisches 9-Feld-Schema; Welle-4b implementiert
  produktiv).
- Pattern-Praezedenz **Sub-Wellen-Subdivision**:
  [`../done/M5-welle-4a.md`](../done/M5-welle-4a.md)
  §0 (Welle-4-Subdivision-Motivation) — Welle 4b ist
  der zweite Sub-Slice; Welle-4-Container damit
  komplett bei Welle-4b-C3-Closure.
- M5-Welle-Pattern-Vorbilder:
  [`../done/M5-welle-3.md`](../done/M5-welle-3.md)
  (Driving-Port + Adapter + Stream-Subscribe-UI in
  einer Welle).
