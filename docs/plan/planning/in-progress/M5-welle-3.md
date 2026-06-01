# Welle 3 — M5 Live-Telemetry-Dashboard

**Status:** Done 2026-06-01 — Liefer-Stack:
Pre-C0a `8d60e16` (Self-Close-Move M5-welle-2.md → done/,
rename-only) + Pre-C0b `159f537` (Cross-Doc-Refs-Sync,
5 Files) + Pre-C0c `5349923` (Asyncio-Pub/Sub-Smoke-Probe-
Run, 4 Probe-Tests) + C0 `ab55ec7` (Slice-Doc + Decisions
3/7/11) + CI-Hotfix `3ba74ef` (Ruff SIM105 + format in
Probe-Datei) + C1 `9f3c00d` (NEU ADR 0038 `Proposed`) +
C2 `82bdf39` (Port + Adapter + WS-Wiring + Dashboard +
Tests; +16 Unit + 6 Integration = 1626 unit + 49
integration; 10/10 A-1-Gates gruen) + C3 (dieser Commit;
ADR 0038 `Proposed → Provisional` + Status/DoD-Sync +
Top-Level-Doku-Sync).

Welle 3 ist die **Live-Telemetry-Welle** in M5. Pattern
analog M4-Welle-3 ([`../done/M4-welle-3.md`](../done/M4-welle-3.md))
— zweite konkrete Adapter-Implementation nach der UI-
Foundation-Welle (M5-Welle-2 lieferte die UI-Huelse,
M5-Welle-3 fuellt sie mit Live-Telemetry-Inhalt). Welle 3
erfuellt **`GG-UI-002` (Live-Telemetry)**, **`GG-UI-003`
(Zeitreihen)** und **`GG-UI-009` (Quality-Marker)** aus
[Lastenheft §17](../../../../spec/lastenheft.md).

**Pre-C0 abgeschlossen (3 Commits):**

1. Pre-C0a `8d60e16` — `git mv in-progress/M5-welle-2.md
   → done/` (rename-only).
2. Pre-C0b `159f537` — Cross-Doc-Refs-Sync nach Move
   (5 Files).
3. Pre-C0c `5349923` — **Asyncio-Pub/Sub-Smoke-Probe-Run
   erfolgreich** (4 Tests in
   `tests/integration/test_m5_welle_3_async_pubsub_probe.
   py`). Server-side-Validation des geplanten
   `TelemetryStreamPort`-Patterns. Probe-Resultat: vier
   kritische Composition-Punkte funktionieren — Single-
   Subscriber-Order, Multi-Subscriber-Fan-out, Drop-
   Oldest-Backpressure bei bounded `asyncio.Queue`,
   Subscribe/Unsubscribe-Resource-Cleanup.

**Spec-Reife:** Inhaltlich final fuer Welle 3. **Welle-3-
Decision-Liste** (§3) sammelt drei Decisions:

- **Decision 3 (WebSocket vs SSE)** — durch
  [Lastenheft §16 `GG-API-002`](../../../../spec/lastenheft.md)
  bereits vorgegeben (**WebSocket Pflicht**). Welle 3
  bestaetigt das im ADR.
- **Decision 7 (Charting-Library-Final)** — Chart.js
  4.5.1, bereits durch M5-Welle-2-Vendoring belegt;
  Welle 3 bestaetigt durch produktiven Einsatz.
- **NEU Decision 11 (Telemetry-Source-Architektur)** —
  `TelemetryStreamPort` + `InMemoryTelemetryStream`-
  Adapter; final fixiert im C1-ADR 0038.

---

## 1. Context

M5-Welle-2
([`../done/M5-welle-2.md`](../done/M5-welle-2.md)) hat die
UI-Foundation unter `src/grid_gym/adapters/driving/ui/`
produktiv geliefert: 6 Templates + 3 vendored Static-
Assets + `StaticFiles`-Mount + `ui_router` mit 2 Page-
Routes (`GET /`, `GET /ui/health`).

M5-Welle-1
([`../done/M5-welle-1.md`](../done/M5-welle-1.md)) hat
zusaetzlich einen WebSocket-Endpoint `WS /runs/{id}/
telemetry` in `_runs_action_router.py` als
**Welle-1-Skeleton** angelegt — der pusht in Welle 1 noch
einen Timer-getriebenen Counter-Stub (3 Messages mit
`tick=0/1/2`, dann close). Welle 3 ersetzt diesen Stub
durch ein echtes Subscribe-Pattern auf einer Telemetry-
Source.

### 1.1 Existierende Substanz (M5-Welle-1 + M5-Welle-2)

- `src/grid_gym/adapters/driving/http_api/_runs_action_router.py`
  — `ws_run_telemetry(websocket, run_id)` als Welle-1-
  Counter-Stub.
- `src/grid_gym/adapters/driving/ui/` — Jinja2-Templates +
  vendored Chart.js 4.5.1 + HTMX 2.0.9; Welle 3 ergaenzt
  eine neue Page-Route + ein neues Template + ein neues
  Inline-JS-Glue.
- Welle-1-Tests in
  `tests/unit/adapters/driving/http_api/test_runs_action_router.py`
  testen den Stub — die werden in C2 durch Welle-3-Tests
  ersetzt, die das echte Subscribe-Pattern verifizieren.

### 1.2 Welle-3-Lieferziel

Fuenf Sub-Items:

1. **NEU Driving-Port `TelemetryStreamPort`** unter
   `src/grid_gym/hexagon/ports/driving/telemetry_stream.
   py`:
   - `publish(point: TelemetryPoint) -> None` — Sync-
     Methode; pusht eine Message an alle aktiven
     Subscribers.
   - `async subscribe(run_id: str | None) -> AsyncIterator
     [TelemetryPoint]` — AsyncIterator; liefert
     publishte Messages, optional gefiltert nach Lauf-ID.
   - `subscriber_count` (Property) fuer Test-/Observability-
     Sichtbarkeit.
   - `TelemetryPoint`-Dataclass mit Feldern aus
     `GG-UI-002`-Akzeptanz: `run_id` + `device_id` +
     `metric` + `value` + `unit` + `simulation_time_ms`
     + `quality` (Literal `ok|stale|invalid|nan|missing|
     fault_injected`) + `sequence` (Pflicht laut
     `GG-API-002`).

2. **NEU Driven-Adapter `InMemoryTelemetryStream`** unter
   `src/grid_gym/adapters/driven/telemetry_stream_inmemory/`:
   - `stream.py` — Pub/Sub-Implementation mit bounded
     `asyncio.Queue` (Default-Size 128 pro Subscriber,
     Drop-Oldest-Backpressure analog Probe-Run).
   - `demo_generator.py` — Welle-3-Stub-Producer: ein
     periodischer Asyncio-Task, der einen synthetischen
     SOC-Sinus + Power-Sinus aus einem deterministischen
     Seed publisht (alle ~200ms). Welle 4/5/6 ersetzen
     diesen Stub durch echte TickLoop-Wiring.
   - `__init__.py` — Re-Export der Public-Surface.

3. **WS-Endpoint-Umstellung** in
   `_runs_action_router.py`:
   - `ws_run_telemetry` subscribt an den
     `TelemetryStreamPort` (statt Counter-Stub).
   - Pusht JSON-Repraesentation der `TelemetryPoint`-
     Datenklasse: `run_id`, `device_id`, `metric`,
     `value`, `unit`, `simulation_time_ms`, `quality`,
     `sequence`.
   - Filterung nach Lauf-ID per `subscribe(run_id=...)`.

4. **NEU UI-Page `GET /runs/{run_id}/dashboard`** unter
   `src/grid_gym/adapters/driving/ui/routes.py`:
   - Rendert `dashboard.html` mit Run-Detail + Live-
     Telemetry-Tabelle + Chart.js-Time-Series fuer Power
     + SOC.
   - HTMX-`hx-ext="ws"`-Pattern fuer WS-Subscribe:
     `<div hx-ext="ws" ws-connect="/runs/{{run_id}}/
     telemetry">` mit `<div id="telemetry-feed">` als
     Target.
   - Chart.js-Glue als Inline-`<script>` (kein neues
     Vendored-Asset noetig): hoert auf das `htmx:wsAfter
     Message`-Event und updated die Chart-Datasets.
   - **NEU HTMX-WS-Extension**: HTMX 2.0.9-Core kennt
     `hx-ext="ws"` als built-in-Extension; kein zusaetzliches
     JS-File noetig.

5. **Quality-Marker-Visualisierung (`GG-UI-009`)** im
   Dashboard-Template:
   - Tabellen-Row-Klassen `quality-stale`/`quality-
     invalid`/`quality-nan`/`quality-missing`/`quality-
     fault_injected` mit unterscheidbarem Styling
     (CSS-Update in `style.css`).
   - Chart.js-Point-Style-Override fuer non-OK-Quality
     (per Custom-Point-Style-Function).

### 1.3 Welle-3-Anti-Scope

- **Kein echtes TickLoop-Wiring** — der Producer in Welle 3
  ist ein deterministischer Demo-Generator
  (`demo_generator.py`), kein `TickLoop`-Subscriber.
  Welle 4 (Replay-Controls) wirt das echte Wiring an.
- **Kein Replay-Controls-UI** — Pause/Resume/Stop-Buttons
  sind Welle-4-Scope.
- **Kein Fault-Injection-UI** — Welle-6-Scope; Quality-
  Marker `fault_injected` ist zwar visualisiert, aber
  ohne UI zum Auslösen.
- **Kein Scenario-Editor** — Welle-5-Scope.
- **Kein OTel-Span-Wrap fuer den Stream** — analog
  M4-Welle-Pattern (Wrap kommt mit M6 oder einer eigenen
  Cross-Adapter-Hardening-Welle).
- **Keine `noqa`-Marker**.

## 2. Scope

Welle 3 liefert **fuenf Items** ueber 4 Commits
(C0..C3, plus optional C1-ADR):

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses
   Dokument.
2. **NEU ADR 0038 (TelemetryStreamPort)** (C1) — verankert
   Decision 11. Plus Decision 3 + 7 Bestaetigung im ADR-
   Body als Welle-3-Welle-Indication.
3. **NEU Port + NEU Adapter + WS-Wiring + UI-Page +
   Tests** (C2) — alle 5 Sub-Items der §1.2-Liste.
4. **Status/DoD-Sync** (C3).

## 3. Architektur-Entscheidungen (Welle-3-Decisions)

### 3.1 Decision 3 (WebSocket vs SSE) — durch Lastenheft fixiert

**Frage:** WebSocket oder Server-Sent-Events (SSE) fuer
den Live-Telemetry-Pfad?

**Auswertung:** [Lastenheft §16
`GG-API-002`](../../../../spec/lastenheft.md) schreibt
explizit **WebSocket** vor: "Die Plattform MUSS WebSocket-
Telemetrie fuer Live-Ansichten unterstuetzen. Akzeptanz:
WebSocket-Nachrichten enthalten Lauf-ID, Simulationszeit,
Sequenznummer und Telemetrie-Payload." Decision 3 ist
damit **vorgegeben** — Welle 3 implementiert WebSocket.

**Gewaehlt:** **WebSocket**. Begruendung:
1. Lastenheft-Pflicht (`GG-API-002`).
2. Welle-1-Endpoint `WS /runs/{id}/telemetry` existiert
   bereits als Welle-1-Skeleton — Welle 3 ersetzt nur
   die Producer-Logik, nicht die Surface.
3. HTMX 2.0.9 traegt `hx-ext="ws"` als built-in-Extension
   (kein zusaetzliches Vendoring).
4. Bidirektional erweiterbar: Welle 4 kann die Control-
   Pfade (Pause/Resume) auch ueber denselben WS senden,
   falls die HTTP-API-Variante zu high-latency wird.

**Konsequenz:** Welle 3 implementiert kein SSE-Fallback.
SSE-Pattern bleibt als alternative Spec-Compliance-Pfad
fuer Browser-Umgebungen ohne WebSocket-Support (sehr
seltener Edge-Case) auf der M6-Wishlist.

### 3.2 Decision 7 (Charting-Library-Final) — bestaetigt

**Frage:** Welche Charting-Library wird produktiv fuer
die Zeitreihen-Visualisierung (`GG-UI-003`) verwendet?

**Auswertung:** ADR 0036 §2.5 hat die Maintainer-
Indication Chart.js gesetzt. M5-Welle-2-Vendoring hat
Chart.js 4.5.1 unter `static/chart.umd.min.js` produktiv
abgelegt. Welle 3 nutzt es jetzt zum ersten Mal.

**Gewaehlt:** **Chart.js 4.5.1**. Begruendung:
1. ADR-0036-§2.5-Indication bestaetigt durch produktive
   Anwendung in Welle 3 (`update()`-Pattern bei WS-Push).
2. Bundle-Groesse 208 KB ist akzeptabel fuer ein
   Visualisierungs-Demo (eine Groessen-Klasse kleiner
   als z. B. ECharts mit ~900 KB).
3. UMD-Build (`chart.umd.min.js`) erzeugt einen Window-
   globalen `Chart`-Symbol → passt zum HTMX-Pattern ohne
   separaten Bundler.
4. MIT-Lizenz, kompatibel zu grid-gym-MIT.

**Konsequenz:** ADR 0036 wird in C1 nicht modifiziert
(Indication ist seit M5-Welle-1-C1 `Provisional`). Welle 3
verlinkt im Slice-Doc-§7-References auf ADR 0036 als
gerne genutzte Quelle.

### 3.3 Decision 11 (Telemetry-Source-Architektur) — final fixiert

**Frage:** Wie kommt die Live-Telemetry vom Simulator-
Kern zum UI-Browser?

**Optionen:**

- **A (gewaehlt)** — NEU Driving-Port
  `TelemetryStreamPort` + `InMemoryTelemetryStream`-
  Adapter im `adapters/driven/`-Baum. Pub/Sub-Pattern
  mit bounded `asyncio.Queue` und Drop-Oldest-
  Backpressure. WS-Endpoint subscribt sich.
- **B** — In-Memory-Broadcaster ohne Port-Surface
  (`app.state.telemetry_broadcaster`). Bricht
  Hexagonal-Konsistenz.
- **C** — Welle-3-Stub-Only ohne Surface (Counter-Stub
  bleibt). Erfuellt `GG-UI-002` nur halb.

**Gewaehlt:** **Option A**. Begruendung:

1. **Hexagonal-Architektur-Konsistenz.** Das UI-Frontend
   ist ein Driving-Adapter (loest UI-Events aus). Eine
   reine Stream-Surface (`subscribe(run_id) ->
   AsyncIterator[TelemetryPoint]`) ist die natuerliche
   Driving-Side-Surface dafuer. Pattern analog zum
   `DeviceProtocolPort` aus M4-Welle-1.
2. **Probe-Run `5349923`** validiert das Pattern
   server-side. 4 Tests gruen: Single-Subscriber-Order,
   Fan-out, Drop-Oldest-Backpressure, Resource-Cleanup.
3. **Adapter-Austauschbarkeit.** Welle 3 liefert
   `InMemoryTelemetryStream` als Stand-Wiring (Demo-
   Generator als Producer). Welle 4 ersetzt den
   Generator durch TickLoop-Wiring **ohne den Port zu
   touchieren**.
4. **Test-Pattern.** Driving-Ports bekommen einen Test-
   Fake (analog `tests/unit/hexagon/ports/driven/
   _fakes.py:InMemoryRunRepository` aus M1). Welle 3
   nutzt das produktive `InMemoryTelemetryStream`
   direkt als Test-Subject — die Klasse erfuellt zwei
   Rollen.
5. **`GG-API-002`-Erfuellung.** Decision-11-Surface
   produziert `TelemetryPoint`-Records mit
   `simulation_time_ms` + `sequence` + Telemetrie-
   Payload — passt 1:1 zur Akzeptanz.

**Architektur-Konsequenz:** ADR 0038 verankert die
Surface-Surface + Subscriber-Lifecycle + Backpressure-
Strategie. Welle 4 (Replay-Controls) bringt das
TickLoop-Wiring an die `publish()`-Methode.

## 4. Liefer-Reihenfolge (4 Commits)

### Pre-C0 — bereits erledigt

- Pre-C0a `8d60e16` (Self-Close-Move; rename-only).
- Pre-C0b `159f537` (Cross-Doc-Refs-Sync, 5 Files).
- Pre-C0c `5349923` (Asyncio-Pub/Sub-Smoke-Probe-Run).

### C0 — `docs(plan)`: M5-welle-3 Slice-Doc

**Diff:** dieses Dokument + `in-progress/README.md`-
Bestand-Eintrag + Aktive-Welle-Marker.

### C1 — `docs(adr)`: NEU ADR 0038 (TelemetryStreamPort)

**Diff:**

- NEU `docs/plan/adr/0038-telemetry-stream-port.md`
  (~250 Zeilen) mit Status `Proposed`:
  - §1 Kontext (M5-Welle-3-Spezifikum, GG-API-002 als
    Akzeptanz-Anker).
  - §2 Entscheidung:
    - §2.1 **Decision 11** Surface-Definition
      (`subscribe`/`publish`/`TelemetryPoint`).
    - §2.2 Bounded-Queue + Drop-Oldest-Backpressure
      (Probe-Run-Beleg `5349923`).
    - §2.3 Subscriber-Lifecycle (try/finally; cleanup
      garantiert in `aclose()`).
  - §3 Konsequenzen (Welle-4-TickLoop-Wiring; Welle-6-
    OTel-Span-Wrap; M6-SSE-Fallback).
  - §4 Out-of-Scope (kein TickLoop-Wiring, kein OTel,
    kein Persistence-Sink).
  - §5 Status-Pfad (`Proposed → Provisional` mit C3
    nach C2-Code-Merge; `Accepted` mit M5-Welle-7).
  - §6 Folge-Pflichten.
- `docs/plan/adr/README.md`-Tabellen-Zeile fuer
  ADR 0038.
- ggf. Welle-3-Slice-Doc-Aktualisierung (Hash-Verweis
  auf C1-Commit).

### C2 — `feat(welle-3)`: TelemetryStreamPort + Adapter + WS + UI + Tests

**Diff (gross):**

- NEU
  `src/grid_gym/hexagon/ports/driving/telemetry_stream.py`
  — Port-Surface + `TelemetryPoint`-Dataclass +
  `TelemetryStreamPort`-Protocol.
- NEU
  `src/grid_gym/adapters/driven/telemetry_stream_inmemory/__init__.py`
  + `stream.py` + `demo_generator.py`.
- `src/grid_gym/adapters/driving/http_api/_runs_action_router.py`
  — `ws_run_telemetry` umgestellt auf Subscribe-Pattern.
- NEU
  `src/grid_gym/adapters/driving/ui/templates/dashboard.html`
  + `_dashboard_content.html` Partial.
- `src/grid_gym/adapters/driving/ui/routes.py` — neue
  Page-Route `GET /runs/{run_id}/dashboard`.
- `src/grid_gym/adapters/driving/ui/static/style.css` —
  Quality-Marker-Klassen (5 Zustaende).
- `src/grid_gym/adapters/driving/http_api/app.py` —
  Demo-Generator-Startup-Hook (FastAPI-Lifespan oder
  `@app.on_event("startup")` — Decision in C2 nach
  FastAPI-Doku).
- NEU
  `tests/unit/hexagon/ports/driving/test_telemetry_stream.py`
  — Port-Surface-Smoke (Dataclass-Construct, Type-Hints).
- NEU
  `tests/unit/adapters/driven/telemetry_stream_inmemory/`
  — Unit-Tests fuer Pub/Sub-Mechanik + Drop-Oldest +
  Cleanup (~6 Tests).
- `tests/unit/adapters/driving/http_api/test_runs_action_router.py`
  — Welle-1-Counter-Stub-Tests an Subscribe-Pattern
  angepasst.
- NEU `tests/unit/adapters/driving/ui/test_dashboard.py`
  — Dashboard-Page-Rendering-Tests.
- NEU
  `tests/integration/test_m5_welle_3_live_telemetry_smoke.py`
  — End-to-End-Smoke (Page laden + WS-Connect +
  Telemetry-Updates empfangen).
- `tests/integration/test_m5_welle_3_async_pubsub_probe.py`
  — bleibt als Probe-Beleg unveraendert.
- `pyproject.toml` — falls neue Dep noetig (eventuell
  nicht, da asyncio + FastAPI Standard).

### C3 — `docs(plan|adr)`: Welle-3 Status/DoD-Sync + Top-Level-Doku-Sync

**Diff:**

- `M5-welle-3.md §0 Status` von `In Progress → Done` mit
  Liefer-Hashes (C0/C1/C2/C3) + DoD-Verifikation.
- `M5-ui-demo.md §3 Welle 3` Status `Pending → Done` mit
  Hashes; 8 DoD-Boxen abgehakt.
- `M5-welle-3.md §9 DoD-Checkliste` Items abhaken.
- ADR 0038 `Proposed → Provisional` mit C2-Code-Merge-
  Beleg.
- Top-Level-Doku-Sync (5 Docs):
  - `docs/plan/planning/in-progress/README.md` — Welle-
    3-Bestand-Eintrag + Aktive-Welle-Marker auf
    M5-Welle-4.
  - `docs/plan/planning/in-progress/roadmap.md` — §3
    M5-Welle-3-Bullet-Belegung; ADR-Status-Update.
  - `README.md` + `README.de.md` — Test-Counts
    aktualisiert; M5-Tabellen-Zeile + Slice-Liste.

## 5. Critical Files

| Datei                                                                                | Phase | Aktion                                                                |
| ------------------------------------------------------------------------------------ | ----- | --------------------------------------------------------------------- |
| `docs/plan/planning/in-progress/M5-welle-3.md`                                       | C0    | CREATE (dieses Dokument)                                              |
| `docs/plan/adr/0038-telemetry-stream-port.md`                                        | C1    | CREATE (NEU ADR; Status `Proposed`)                                   |
| `docs/plan/adr/README.md`                                                            | C1    | EDIT (Tabellen-Zeile fuer 0038)                                       |
| `src/grid_gym/hexagon/ports/driving/telemetry_stream.py`                             | C2    | CREATE (Port-Surface + `TelemetryPoint`-Dataclass)                    |
| `src/grid_gym/adapters/driven/telemetry_stream_inmemory/__init__.py`                 | C2    | CREATE (Modul-Marker)                                                 |
| `src/grid_gym/adapters/driven/telemetry_stream_inmemory/stream.py`                   | C2    | CREATE (Pub/Sub-Adapter)                                              |
| `src/grid_gym/adapters/driven/telemetry_stream_inmemory/demo_generator.py`           | C2    | CREATE (Welle-3-Stub-Producer)                                        |
| `src/grid_gym/adapters/driving/http_api/_runs_action_router.py`                      | C2    | EDIT (`ws_run_telemetry` → Subscribe-Pattern)                         |
| `src/grid_gym/adapters/driving/http_api/app.py`                                      | C2    | EDIT (Startup-Hook fuer Demo-Generator-Task)                          |
| `src/grid_gym/adapters/driving/ui/templates/dashboard.html`                          | C2    | CREATE (Live-Telemetry-Dashboard-Page)                                |
| `src/grid_gym/adapters/driving/ui/templates/_dashboard_content.html`                 | C2    | CREATE (HTMX-Partial)                                                 |
| `src/grid_gym/adapters/driving/ui/routes.py`                                         | C2    | EDIT (neue Page-Route `/runs/{id}/dashboard`)                         |
| `src/grid_gym/adapters/driving/ui/static/style.css`                                  | C2    | EDIT (Quality-Marker-Klassen)                                         |
| `tests/unit/hexagon/ports/driving/test_telemetry_stream.py`                          | C2    | CREATE                                                                |
| `tests/unit/adapters/driven/telemetry_stream_inmemory/test_stream.py`                | C2    | CREATE (~6 Tests)                                                     |
| `tests/unit/adapters/driving/http_api/test_runs_action_router.py`                    | C2    | EDIT (WS-Tests an Subscribe-Pattern angepasst)                        |
| `tests/unit/adapters/driving/ui/test_dashboard.py`                                   | C2    | CREATE                                                                |
| `tests/integration/test_m5_welle_3_live_telemetry_smoke.py`                          | C2    | CREATE (End-to-End-Smoke)                                             |
| `docs/plan/planning/in-progress/M5-ui-demo.md`                                       | C3    | EDIT (§3 Welle 3 Status + DoD-Boxen)                                  |
| `docs/plan/planning/in-progress/roadmap.md`                                          | C3    | EDIT (§3 M5-Welle-3-Bullet)                                           |
| `docs/plan/planning/in-progress/README.md`                                           | C3    | EDIT (Welle-3-Abschluss + Welle-4-aktiv)                              |
| `README.md` + `README.de.md`                                                         | C3    | EDIT (Test-Counts + Slice-Liste + M5-Tabellen-Zeile)                  |

## 6. Verifikationspfad

**Welle-3-DoD:**

1. `M5-welle-3.md` produktiv mit §1-§9.
2. **NEU ADR 0038** mit Status `Proposed → Provisional`
   nach C2.
3. **NEU `TelemetryStreamPort`** produktiv unter
   `src/grid_gym/hexagon/ports/driving/`.
4. **NEU `InMemoryTelemetryStream`** produktiv unter
   `src/grid_gym/adapters/driven/`.
5. **WS-Endpoint** auf Subscribe-Pattern umgestellt mit
   Run-ID-Filterung.
6. **Demo-Generator-Task** wird beim FastAPI-Lifespan-
   Startup angelegt.
7. **NEU UI-Page `GET /runs/{id}/dashboard`** produktiv.
8. **Quality-Marker-Visualisierung** (5 Zustaende)
   sichtbar.
9. **`GG-UI-002` + `GG-UI-003` + `GG-UI-009`-Akzeptanz**
   erfuellt.
10. **`GG-API-002`-Akzeptanz** erfuellt (WS-Nachrichten
    enthalten `run_id`, `simulation_time_ms`, `sequence`,
    Telemetrie-Payload).
11. **Unit-Tests** + **Integration-Test**.
12. `make test-unit` gruen (1610 + ~12..15 Welle-3-Tests).
13. `make test-integration` gruen (47 + 1..2 Welle-3-Tests).
14. `make arch-check` 20/20 KEPT.
15. `make typecheck` mit `strict_bytes` gruen.
16. `make gates` cache-frei gruen ohne Override.
17. `make docs-check` cache-frei gruen.
18. `make openapi-validate` cache-frei gruen.

**Welle-3-Gate:** `make gates` + `make docs-check` +
`make openapi-validate` cache-frei gruen ohne Override.

## 7. Risiken

- **WebSocket-Lifespan vs Demo-Generator-Cleanup.** Wenn
  der Demo-Generator-Task beim FastAPI-Shutdown nicht
  korrekt gecanceled wird, leakt ein Task ueber den
  Server-Lebenszyklus hinaus. Mitigation: FastAPI-
  `lifespan`-Context-Manager (Recipe aus FastAPI-Doku);
  C2-Unit-Test prueft Cleanup explizit.
- **WS-Disconnect waehrend Subscribe-Loop.** Wenn der
  Browser-Tab schliesst, kann der WS-Subscribe-Loop in
  `await queue.get()` haengen, bis der naechste publish
  durchgeht. Mitigation: `WebSocketDisconnect`-Catch und
  `async for` cleanup; Pattern aus Probe-Run-Test
  bewaehrt.
- **Quality-Marker-CSS-Drift.** Die 5 Quality-Zustaende
  brauchen visuell unterscheidbare Styling (Color +
  Iconographie). Mitigation: Welle-3-Smoke-Test prueft
  CSS-Klassen-Anwesenheit, nicht den visuellen Effekt
  (M6-Visual-Diff-Tests koennten das verfeinern).
- **Chart.js-Memory-Bloat bei Long-Run-Sessions.**
  Chart-Datasets ohne Pruning wachsen unbegrenzt.
  Mitigation: das Inline-JS pruned alte Punkte ueber ein
  `MAX_POINTS = 200`-Sliding-Window. Welle-3-Pruning-
  Pattern dokumentiert in Slice-Doc-§3.
- **TickLoop-Sequence-Wraparound.** `sequence: int` mit
  Python-`int` ist unbegrenzt, aber JSON-Serializer
  rundet ab `>= 2^53`. Mitigation: das Welle-3-Demo-
  Generator-Modul produziert `sequence`-Werte als
  Modulo `2^53` (frei waehlbar, weil Demo-Stream;
  Welle-4-TickLoop-Wiring kann das Pattern aendern).
- **GG-API-002-Schema-Konsistenz.** Welle-1-Counter-
  Stub-Tests testen ein Schema `{run_id, tick, value}`.
  Welle 3 ersetzt es durch ein deutlich reicheres
  Schema. Mitigation: Welle-1-Counter-Stub-Tests werden
  in C2 ueberschrieben (nicht behalten als Backward-
  Compat).

## 8. Wandert nach

- Bei C3-Closure: `M5-welle-3.md` bleibt in
  `in-progress/` (Pattern analog Welle 1+2). Self-Close-
  Move folgt als M5-Welle-4-Pre-C0.
- `M5-ui-demo.md` bleibt in `in-progress/` bis
  M5-Welle-7-Closure.
- Welle 4 (Replay-Controls + Alarme) als naechster
  aktiver Schritt: `POST /runs/{id}/control`-Wiring an
  `TickLoop`, Replay-Controls-UI, Alarm-Tabelle.

## 9. DoD-Checkliste (mit C3 abgehakt)

- [x] **NEU ADR 0038 `Proposed → Provisional`** mit
  C2-Code-Merge-Beleg `82bdf39`.
- [x] **NEU `TelemetryStreamPort`** in
  `src/grid_gym/hexagon/ports/driving/telemetry_stream.
  py` mit Protocol-Surface +
  `TelemetryPoint`-Dataclass (frozen, slots) +
  `TelemetryQuality`-Literal-Alias.
- [x] **NEU `InMemoryTelemetryStream`** in
  `src/grid_gym/adapters/driven/telemetry_stream_inmemory/`
  mit `stream.py` (Pub/Sub mit bounded `asyncio.Queue`
  + Drop-Oldest) + `demo_generator.py` (asyncio-Task mit
  4 Points/Tick) + `__init__.py`.
- [x] **WS-Endpoint umgestellt** auf Subscribe-Pattern;
  filtert nach Run-ID; bei nicht konfiguriertem Stream
  Close-Code 1011.
- [x] **Demo-Generator-Task** im FastAPI-Lifespan-
  Context-Manager (`_lifespan`) gestartet und sauber
  gecanceled.
- [x] **NEU UI-Page `GET /runs/{run_id}/dashboard`** mit
  Run-Detail + Live-Telemetry-Tabelle + Chart.js-Time-
  Series + Repository-Dependency fuer 404.
- [x] **HTMX-`hx-ext="ws"`-Pattern** im Dashboard-
  Template produktiv (`<div ws-connect="/runs/{run_id}/
  telemetry">`).
- [x] **Quality-Marker-Visualisierung** (6 Zustaende:
  ok/stale/invalid/nan/missing/fault_injected) mit
  unterscheidbarem CSS-Styling in `style.css`.
- [x] **Unit-Tests** fuer Port + Adapter + WS-Subscribe +
  Dashboard-Route: 3 + 6 + 4 + 3 = 16 neue Unit-Tests
  + 1 modifizierter WS-Test (`test_runs_action_router.
  py`).
- [x] **Integration-Test**
  `test_m5_welle_3_live_telemetry_smoke.py` produktiv
  (End-to-End-Workflow + OpenAPI-Schema-Check).
- [x] **`make test-unit`** gruen: ~1626 passed (+16 vs
  Welle-2-Endstand 1610).
- [x] **`make test-integration`** gruen: 49 passed + 4
  skipped (+6 vs Welle-2-Endstand 43; 4 Probe-Tests
  + 2 neue Welle-3-Smokes).
- [x] **`make arch-check`** 20/20 KEPT (neuer Port unter
  `hexagon/ports/driving/`; neuer Adapter unter
  `adapters/driven/telemetry_stream_inmemory/`;
  `AC-ADAPTER-LIGHTWEIGHT` erfasst beide automatisch).
- [x] **`make typecheck`** mit `strict_bytes` gruen
  (kein `# type: ignore`; 145 source files +4 vs Welle-
  2-Endstand 141).
- [x] **`make gates`** cache-frei gruen ohne Override
  (10/10 A-1-Gates).
- [x] **`make docs-check`** cache-frei gruen.
- [x] **`make openapi-validate`** cache-frei gruen
  (Dashboard-Route mit `tags=["ui"]`).
- [x] **`GG-UI-002` (Live-Telemetry)** erfuellt durch
  Dashboard + WS-Subscribe + Tabellen-Update bei
  `htmx:wsAfterMessage`.
- [x] **`GG-UI-003` (Zeitreihen)** erfuellt durch
  Chart.js-Time-Series (3 Datensaetze: battery-power,
  battery-soc, grid-power) mit MAX_POINTS=200 Sliding-
  Window.
- [x] **`GG-UI-009` (Quality-Marker)** erfuellt durch
  6 CSS-Klassen + Row-Class-Update im Inline-JS.
- [x] **`GG-API-002` (WebSocket-Telemetrie)** erfuellt
  mit Run-ID + Simulationszeit + Sequenznummer + Geraet
  + Metrik + Wert + Einheit + Quality.
- [x] **C3-Top-Level-Doku-Sync** produktiv: 6 Docs auf
  Welle-3-Closure-Stand (`M5-welle-3.md §0/§9`,
  `M5-ui-demo.md §3 Welle 3`, `in-progress/README.md`,
  `in-progress/roadmap.md §3 M5`, `README.md` +
  `README.de.md`-Test-Counts + ADR 0038 +
  `docs/plan/adr/README.md`).

**Anti-Scope-Verifikation (Welle 3 NICHT):**

- [x] Kein echtes TickLoop-Wiring (Demo-Generator als
  Stub; Welle 4 ersetzt).
- [x] Kein Replay-Controls-UI (Welle 4).
- [x] Kein Fault-Injection-UI (Welle 6).
- [x] Kein Scenario-Editor (Welle 5).
- [x] Kein OTel-Span-Wrap fuer den Stream (M6 oder
  separate Hardening-Welle).
- [x] Keine `noqa`-Marker.

---

## References

- [`../done/M5-welle-2.md`](../done/M5-welle-2.md) — Welle-
  2-Closure (UI-Foundation, die Welle 3 nun mit Live-
  Telemetry-Inhalt fuellt).
- [`../done/M5-welle-0.md`](../done/M5-welle-0.md) §3
  Decision 11 (Welle 3 trifft die finale Wahl).
- [`M5-ui-demo.md`](M5-ui-demo.md) §3 Welle 3 (kanonische
  Slice-Spezifikation).
- [`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md)
  §2.5 (Chart.js-Sub-Decision, Welle 3 bestaetigt
  produktiv).
- [`../../adr/0037-http-api-surface-pattern.md`](../../adr/0037-http-api-surface-pattern.md)
  (WS-Endpoint aus Welle 1; Welle 3 stellt Producer um).
- [`../../../../spec/lastenheft.md §16`](../../../../spec/lastenheft.md)
  (`GG-API-002` WebSocket-Telemetrie-Pflicht).
- [`../../../../spec/lastenheft.md §17`](../../../../spec/lastenheft.md)
  (`GG-UI-002/003/009` Live-Telemetry +
  Zeitreihen + Quality-Marker).
- Asyncio-Pub/Sub-Smoke-Probe-Run `5349923` (validiert
  das Welle-3-Pattern server-side).
- Pattern-Praezedenz Welle-3-Implementation:
  [`../done/M4-welle-3.md`](../done/M4-welle-3.md)
  (Modbus-Adapter als zweite konkrete Implementation in
  M4 nach DeviceProtocolPort-Foundation).
