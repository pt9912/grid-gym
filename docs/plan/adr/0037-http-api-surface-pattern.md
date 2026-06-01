# ADR 0037 — HTTP-API-Surface-Pattern (M5 Welle 1)

**Status:** Provisional — angelegt 2026-06-01 mit M5-Welle-1-C1
`d468e68` (Status `Proposed`); auf `Provisional` gezogen
2026-06-01 mit M5-Welle-1-C3 (dieser Commit) nach C2-Code-
Merge `ae630ce` (5 REST + 1 WebSocket + Pydantic-Schemas +
1600 unit + 41 integration Tests; 10/10 A-1-Gates gruen).
Die ADR schaerft die HTTP-API-Surface (`GG-API-001..004`)
aus
[`../../../spec/lastenheft.md §16`](../../../spec/lastenheft.md)
konkret fuer M5-Welle-1-Implementation und schliesst zwei
Decisions aus der M5-Welle-0-Decision-Liste (siehe
[`../planning/done/M5-welle-0.md §3`](../planning/done/M5-welle-0.md)
Decisions 4 + 9). Plus ein Roadmap-Typo-Fix als Welle-1-
Folge.

**Datum:** 2026-06-01 (M5-Welle-1-C1 `d468e68` → C3 dieser
Commit)

**Bezug:**

- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md)
  (Schaerfungs-ohne-Supersede-Pattern — ADR 0037 schaerft
  ADR 0030 §2.1 konkret fuer Driving-Ports und
  konkretisiert `GG-API-001..004` aus Lastenheft §16).
- [`ADR 0030`](0030-device-protocol-port-surface.md) §2.1
  (Adapter-Hexagon-Pattern; ADR 0037 spiegelt das Pattern
  auf die Driving-Side: `GG-AR-PORT-DRV-*`-Familie statt
  `GG-AR-PORT-DRN-*`).
- [`ADR 0036`](0036-ui-stack-choice.md) §2.1 + §6
  (Maintainer-Decision-Indication „Option 1: FastAPI +
  HTMX + Jinja2 + Chart.js" — ADR 0037 konkretisiert
  die HTTP-API-Surface, auf der die HTMX/Jinja2-UI ab
  Welle 2 aufbaut).
- [Lastenheft](../../../spec/lastenheft.md) §16
  (`GG-API-001..004` Kommunikationsschnittstellen mit
  REST + WebSocket + OpenAPI + Standard-Fehlerformat).
- [Architektur](../../../spec/architecture.md) §4.2
  (`GG-AR-PORT-DRV-*`-Driving-Port-Familie) + §5
  (`GG-AR-COMP-API`-Slot in `adapters/driving/http_api/`).
- [`../planning/done/M5-welle-0.md §3`](../planning/done/M5-welle-0.md)
  Decisions 4 + 9 + Decision-9-Roadmap-Typo-Notiz.
- [`../planning/done/M5-welle-1.md §3`](../planning/done/M5-welle-1.md)
  (Welle-1-Indications fuer beide Decisions; Self-Close-
  Move M5-Welle-2-Pre-C0a `c7c2641`).
- HTTP-API-Stub aus M1-Welle-7 in
  [`../../../src/grid_gym/adapters/driving/http_api/app.py`](../../../src/grid_gym/adapters/driving/http_api/app.py)
  (`/health` + `POST /runs`-Stub als M5-Welle-1-Foundation).

---

## 1. Kontext

M1-Welle-7 hat die HTTP-API-Surface als Stub angelegt
(`GET /health` + `POST /runs` + `GET /openapi.json`). M5-
Welle-1 erweitert sie zur vollen REST + WebSocket-Surface
gemaess `GG-API-001..004`. Zwei Architektur-Entscheidungen
muessen vor C2-Code-Lieferung geklaert werden:

- **Decision 4 (Replay-Controls-API-Vertrag)** — wie wird
  Start/Pause/Resume/Stop ueber REST exponiert?
- **Decision 9 (UICommandPort-Separation)** — gibt es einen
  separaten `UICommandPort`-Slot oder nutzt die UI die
  HTTP-API direkt?

Plus ein dritter, kleinerer Punkt:

- **Decision RT (Roadmap-Typo)** — Roadmap §3 M5 erwaehnt
  `GG-AR-PORT-DRG-002` als „UICommandPort, sofern getrennt
  vom HTTP-API". Der Slot-Suffix `DRG-` ist ein Typo gegen
  Architektur-§4.2-Konvention `DRV-*` (Driving-Ports);
  `DRV-002` ist bereits `ScenarioPort` vergeben. Decision RT
  loest das auf.

ADR 0037 schaerft alle drei Punkte zusammen, weil sie
**zusammen** den HTTP-API-Surface-Pattern definieren — REST-
Vertrag (Decision 4) + Port-Familie-Boundary (Decision 9) +
Slot-Name-Bereinigung (Decision RT).

## 2. Entscheidung

### 2.1 Decision API-1 (entspricht Welle-0-Decision 4) — Replay-Controls via Action-Body

**Gewaehlt:** Variante **B** aus M5-Welle-1-Slice-Doc §3 —
`POST /runs/{id}/control` mit Body `{"action": "pause" |
"resume" | "stop"}`.

**Implementation-Pattern:**

```python
# in src/grid_gym/adapters/driving/http_api/app.py
@app.post("/runs/{run_id}/control")
def control_run(
    run_id: str,
    request: ControlRequest,  # action: Literal["pause", "resume", "stop"]
    run_repository: Annotated[RunRepositoryPort, Depends(get_run_repository)],
) -> ControlResponse:
    ...
```

**Begruendung:**

- **Kompakte Surface**: ein REST-Endpunkt pro Run statt drei
  Endpunkte (`/pause` + `/resume` + `/stop`). Reduziert die
  OpenAPI-Surface-Anzahl auf das semantische Minimum.
- **Erweiterungs-fest**: neue Actions (z. B. `restart`,
  `replay-step`) erweitern das `action`-Literal ohne neue
  Endpunkte. State-Transitions sind explizit im Body, nicht
  im URL-Pfad versteckt.
- **REST-Stilreinheit**: `POST /runs/{id}/control` ist
  semantisch ein State-Transition-Resource (Pattern analog
  Kubernetes-`/scale`, GitHub-`/dispatch`). Keine
  PATCH-Semantik mit impliziter Action-Detection (Variante
  C aus Slice-Doc §3).
- **Server-Side-Validation**: Pydantic-`Literal["pause",
  "resume", "stop"]` validiert die Action vor dem
  TickLoop-Call; ungueltige Actions werden zu 422 statt zu
  Runtime-Errors.

**Anti-Scope (Welle 1):** der Endpunkt ist in Welle 1 ein
**Stub** ohne echte `TickLoop`-Pause/Resume-Wiring. Welle 4
(Replay-Controls + Alarme) verbindet ihn produktiv mit dem
M1-`TickLoop`-Pause/Resume-Pattern.

**Variante-Vergleich (Slice-Doc §3 referenziert):**

| Variante | Pattern                                              | Pro                                            | Con                                                                |
| -------- | ---------------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------ |
| A        | `POST /runs/{id}/pause` + `.../resume` + `.../stop`  | REST-pur (Action im URL)                       | 3+ Endpunkte; erweitert sich linear pro neuer Action               |
| **B**    | `POST /runs/{id}/control` mit `{"action": "..."}`    | **Kompakt, erweiterungs-fest, REST-konform**   | Action-Validation im Body statt im URL-Schema                      |
| C        | `PATCH /runs/{id}` mit `{"status": "paused"}`        | REST-purer (State-Transition als Resource)     | Implizite State-Transition-Semantik unklar; nicht alle Action-States haben direktes State-Mapping (z. B. `restart`) |

### 2.2 Decision API-2 (entspricht Welle-0-Decision 9) — Kein separater UICommandPort

**Gewaehlt:** **Kein separater `UICommandPort`-Slot.** Die
UI nutzt die HTTP-API direkt via REST + WebSocket.

**Implementation-Pattern:**

- Die UI (`adapters/driving/ui/`, Welle 2) ruft die
  HTTP-API-REST-Endpunkte (z. B. `POST /runs/{id}/control`)
  per HTMX (`hx-post`-Pattern).
- Die UI subscribt `WS /runs/{id}/telemetry` direkt — kein
  Proxy-Layer.
- **Kein neuer Driving-Port-Slot** `GG-AR-PORT-DRV-?
  UICommandPort` wird angelegt.

**Begruendung:**

- **YAGNI**: ein Wrapper-Layer zwischen UI und HTTP-API
  haette nur dann Mehrwert, wenn die UI an mehrere
  Backends spricht oder zwischen REST und WebSocket
  mappt — beides nicht der Fall in M5.
- **Hexagonal-Disziplin gehalten**: die UI lebt unter
  `adapters/driving/ui/` und nutzt nur die durch HTTP-API
  exponierte Surface — kein direkter Kern-Zugriff
  (`GG-AR-PRINC-*`).
- **Konsistenz mit M4-Pattern**: M4-Welle-1 hat **einen**
  Driven-Port-Slot (`DeviceProtocolPort`) fuer alle fuenf
  Adapter-Implementer; M5-Welle-1 sollte analog **einen**
  Driving-Port-Slot (`HttpApiPort` via `app`-Mount) fuer
  alle Driving-Caller (UI + ggf. externe HTTP-Clients)
  haben — kein Sub-Slot pro Caller-Typ.

**Konsequenz fuer Roadmap §3 M5:** der Hinweis „sofern
getrennt vom HTTP-API" wird im Welle-1-C3-Doku-Sync als
**verworfen** markiert. Roadmap-Bullet wird umformuliert
auf „UI nutzt `GG-API-001/002/003` direkt — kein separater
UICommandPort-Slot (siehe ADR 0037 §2.2)".

### 2.3 Decision API-3 (Roadmap-Typo `DRG-002`) — Slot-Name verworfen

**Gewaehlt:** Slot-Name `GG-AR-PORT-DRG-002` wird
**verworfen**. Es gibt keinen neuen Driving-Port-Slot fuer
„UICommandPort" (siehe Decision API-2). Der Typo
`DRG-` ist semantisch ungebraucht; die naechste freie
Driving-Port-Slot-Nummer ist `DRV-?` (`DRV-002` ist
ScenarioPort vergeben; nicht-konfliktierende freie Slot-
Nummern wuerden bei Bedarf in einem zukuenftigen ADR
zugewiesen).

**Implementation-Pattern (C3-Top-Level-Doku-Sync):**

- `docs/plan/planning/in-progress/roadmap.md §3 M5` —
  Bullet aktualisiert (siehe Decision API-2-Konsequenz).
- Optional: `grep -rn "DRG-002" docs/ spec/`-Sweep zur
  Sicherheit; aktueller Treffer-Set: nur Roadmap §3 M5.

## 3. Konsequenzen

**Positiv:**

- **Kompakte HTTP-API-Surface** — 5 REST-Endpunkte +
  1 WebSocket statt 7-10 mit dedizierten Action-Pfaden.
  OpenAPI-Schema bleibt uebersichtlich.
- **Erweiterungs-fest** — neue Run-Actions sind eine
  Literal-Erweiterung im Pydantic-Schema, kein neuer
  Endpunkt.
- **Hexagonal-Disziplin gehalten** — UI nutzt
  HTTP-API direkt; kein UICommandPort-Wrapper-Layer.
- **Roadmap-Typo bereinigt** — kein DRG-Slot mehr in der
  Roadmap-Vorbelegung.

**Negativ:**

- **Action-Validation im Body** statt im URL — Reviewer,
  die REST-pur erwarten, sehen Variante B als „weniger
  RESTful" (Action im Body statt Resource-Sub-Pfad).
  Mitigation: Pydantic-`Literal`-Validation + dokumentierte
  Begruendung in §2.1.
- **Kein UICommandPort als Erweiterungs-Slot**: falls in
  Welle 6+/M6 ein zweites UI (z. B. Mobile-App) angedockt
  wird, das ein anderes Command-Vokabular braucht, muss
  die HTTP-API-REST-Surface erweitert werden — kein
  Wrapper-Layer zum Filtern. Akzeptabel weil YAGNI; bei
  Bedarf kann ein Wrapper als Folge-ADR (`ADR-0011`-
  Pattern) eingefuehrt werden.

**Neutral:**

- WebSocket-Endpoint (`WS /runs/{id}/telemetry`) ist
  **nicht** im OpenAPI-Schema (OpenAPI 3.x-Standard:
  WebSocket-Endpunkte sind nicht Teil des OpenAPI-Specs).
  `make openapi-validate` prueft nur REST. WebSocket-
  Vertrag wird im Welle-3-Slice-Doc + ggf. Welle-3-ADR
  separat dokumentiert.

## 4. Out-of-Scope

- **Echte `TickLoop`-Pause/Resume-Wiring** — Welle 4.
- **Echte `FaultPort`-Submit-Wiring** — Welle 6.
- **Echte `TelemetrySinkPort`-WebSocket-Producer** — Welle 3.
- **Multi-User-Auth** — M6 (`GG-SAFE-001..006`).
- **Rate-Limiting / API-Throttling** — M6.
- **GraphQL- oder gRPC-Alternativen** — strukturell
  ausgeschlossen fuer M5; `GG-API-001..004` verlangt REST
  + WebSocket explizit.

## 5. Status-Pfad

- **Proposed** — 2026-06-01 mit M5-Welle-1-C1 `d468e68`
  (zusammen mit ADR-0036-Schaerfung auf `Provisional`).
  Decision API-1/2/3 alle final entschieden im ADR-Body.
- **Provisional** — 2026-06-01 mit M5-Welle-1-C3 (dieser
  Commit) nach C2-Code-Merge `ae630ce`. Pattern analog
  ADR 0030..0035 in M4-Welle-1-bis-5b (`Proposed →
  Provisional` mit C3 nach C2-Implementation-Merge; C2
  belegt die Decisions produktiv im Code). Belege:
  Decision API-1 produktiv in
  `_runs_action_router.py:post_run_control` mit
  `ControlRequest.action: Literal["pause","resume","stop"]`-
  Body-Validation; Decision API-2 produktiv durch
  Abwesenheit eines `UICommandPort`-Slots im Repo;
  Decision API-3 in C3 (dieser Commit) durch
  `roadmap.md §3 M5`-Edit (`GG-AR-PORT-DRG-002` → Verwerfung).
- **Accepted** — geplant mit M5-Welle-7-Closure (analog
  ADR 0030..0036).

## 6. Folge-Pflichten

- **M5-Welle-1-C2-Code-Merge** belegt Decisions API-1/2
  produktiv (5 REST-Endpunkte + 1 WebSocket + Pydantic-
  Schema). C3 zieht ADR 0037 auf `Provisional`.
- **M5-Welle-1-C3-Top-Level-Doku-Sync** korrigiert
  Roadmap-Typo (Decision API-3) + dokumentiert ADR
  0037-Status in `docs/plan/adr/README.md`.
- **M5-Welle-2-C0-Slice-Doc** kann ADR 0037-Decisions als
  Grundlage fuer UI-HTMX-`hx-*`-Pattern verwenden
  (z. B. `<button hx-post="/runs/{{id}}/control"
  hx-vals='{"action": "pause"}'>Pause</button>`).
- **M5-Welle-7-Closure** zieht ADR 0037 auf `Accepted`.

## 7. References

- [`ADR 0030`](0030-device-protocol-port-surface.md) §2.1
  (Hexagonal-Pattern, gespiegelt auf Driving-Side).
- [`ADR 0036 §2.1 + §6`](0036-ui-stack-choice.md)
  (UI-Stack-Wahl mit FastAPI + HTMX; ADR 0037 liefert
  die HTTP-API-Surface, auf der HTMX-UI aufbaut).
- [Lastenheft §16](../../../spec/lastenheft.md)
  (`GG-API-001..004`).
- [Architektur §4.2 + §5](../../../spec/architecture.md)
  (Driving-Port-Familie `GG-AR-PORT-DRV-*`,
  `GG-AR-COMP-API`-Slot).
- [`../planning/done/M5-welle-0.md §3`](../planning/done/M5-welle-0.md)
  Decisions 4 + 9 + Decision-9-Roadmap-Typo-Notiz.
- [`../planning/done/M5-welle-1.md §3`](../planning/done/M5-welle-1.md)
  (Welle-1-Indications fuer beide Decisions; Self-Close-
  Move M5-Welle-2-Pre-C0a `c7c2641`).
- **HTMX-FastAPI-Smoke-Probe-Run** `9c20dad` (validiert
  die Composition-Pattern, auf denen ADR 0037 aufbaut).
