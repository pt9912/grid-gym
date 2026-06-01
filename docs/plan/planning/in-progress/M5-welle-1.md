# Welle 1 — M5 HTTP-API-Surface + ADR-0036-Schaerfung

**Status:** In Progress — eroeffnet 2026-06-01 nach M5-Welle-
0-Closure (Liefer-Stack `d93ae57` C0 + `aa1db52` C0-Review +
`b8bef6c` C1 + `112efd3` C2 + Self-Close-Move `fd642df` +
Pre-C0-Sync `fb417b9` + **HTMX-FastAPI-Smoke-Probe-Run
`9c20dad`** mit 4 Probe-Tests).

Welle 1 ist die **erste Code-Welle in M5** und die
**Foundation-Welle** fuer den UI-Layer. Pattern analog
M4-Welle-1
([`../done/M4-welle-1.md`](../done/M4-welle-1.md)) —
Surface-Foundation vor konkreten UI-Implementern. Welle 1
liefert die volle HTTP-API-Surface (`GG-API-001..004`) auf
der die UI ab Welle 2 aufbaut; **kein** UI-Layout-Code in
Welle 1 (das ist Welle-2-Scope).

**Pre-C0 abgeschlossen (3 Commits):**

1. Pre-C0a `fd642df` — `git mv in-progress/M5-welle-0.md
   → done/` (rename-only).
2. Pre-C0b `fb417b9` — Cross-Doc-Refs-Sync nach Move
   (5 Files).
3. Pre-C0c `9c20dad` — **HTMX-FastAPI-Smoke-Probe-Run
   erfolgreich** (4 Tests in
   `tests/integration/test_m5_welle_1_htmx_probe.py`).
   Server-Side-Validation der ADR-0036-Maintainer-
   Decision-Indication („Option 1: FastAPI + HTMX +
   Jinja2 + Chart.js"). Probe-Resultat: drei kritische
   Composition-Punkte funktionieren — FastAPI HTML-
   Rendering + HTMX `HX-Request`-Pattern + WebSocket
   Server-Push.

**Spec-Reife:** Inhaltlich final fuer Welle 1. **Welle-1-
Decision-Liste** (§3) sammelt die offenen Welle-0-
Decisions, die in Welle 1 zu entscheiden sind (1, 4, 9 aus
M5-Welle-0-§3-Liste); Welle-2-bis-6-Decisions bleiben
deferred.

---

## 1. Context

M5-Welle-0
([`../done/M5-welle-0.md`](../done/M5-welle-0.md)) hat den
M5-Slice-Plan
([`M5-ui-demo.md`](M5-ui-demo.md)) produktiv eroeffnet mit
7 Wellen 0..7. Welle 1 traegt die HTTP-API-Surface, die
Welle 2 (UI-Foundation) und Welle 3 (Live-Telemetry) als
Driving-Port-Schnittstelle benoetigen.

### 1.1 Existierende Substanz (M1-Welle-7)

`src/grid_gym/adapters/driving/http_api/app.py` (~120
Zeilen Stand 2026-06-01):

- `GET /health` — Liveness-Probe (Dockerfile-`HEALTHCHECK`).
- `POST /runs` — `GG-API-001`-Stub: persistiert einen neuen
  Lauf via `RunRepositoryPort` (M1-Welle-6b).
- `GET /openapi.json` — automatisch generiert
  (`GG-API-003`).

Welle 1 erweitert das produktiv um die volle
REST + WebSocket-Surface aus Lastenheft §16
(`GG-API-001..004`).

### 1.2 Welle-1-Lieferziel

Vier Sub-Items:

1. **HTTP-API-Surface-Erweiterung** unter
   `src/grid_gym/adapters/driving/http_api/app.py`:
   - `GET /runs/{id}` — Run-Status + Metadaten.
   - `GET /runs/{id}/status` — kompakter Status-Endpunkt
     (analog `GG-API-001`-Akzeptanz: „Status").
   - `POST /runs/{id}/control` — Steuerung (action: pause/
     resume/stop, gemaess Decision 4).
   - `GET /runs/{id}/snapshot` — Snapshot-Export.
   - `POST /runs/{id}/faults` — Fault-Injection-Submit.
   - `WS /runs/{id}/telemetry` — Live-Telemetry-Stream
     (`GG-API-002`).
   - Standardisierte Fehlerformate (`GG-API-004`).
2. **ADR-0036-Schaerfung** auf `Provisional` mit Probe-
   Run-Beleg (`9c20dad`).
3. **Decisions 4 + 9** aus Welle-0-Decision-Liste final
   im Welle-1-C1-ADR (potenziell NEU **ADR 0037 — HTTP-
   API-Surface-Pattern**).
4. **Roadmap-Typo-Fix** `GG-AR-PORT-DRG-002 → DRV-?` aus
   Welle-0-S3-Review-Folge-Notiz; ggf. neue Decision in
   Welle 1.

### 1.3 Welle-1-Anti-Scope

- **Kein UI-Layout-Code** — `ui/`-Verzeichnis (oder
  `adapters/driving/ui/`) wird **nicht** in Welle 1
  angelegt. Jinja2-Templates + HTMX-Vendoring + Chart.js
  kommen in Welle 2.
- **Kein WebSocket-Daten-Producer** — der WS-Endpoint in
  Welle 1 ist ein Skeleton, das einen Stub-Stream liefert
  (z. B. einen Timer-getriebenen Counter-Push analog
  Probe-Test); die echte Telemetrie-Producer-Integration
  (mit `TelemetrySinkPort` aus M3) folgt in Welle 3.
- **Kein Replay-Steuerungs-Backend-Code** — `POST /runs/
  {id}/control` triggert keine echte Run-Pause/Resume in
  Welle 1; das `TickLoop`-Pause/Resume-Pattern ist
  vorhanden (M1), aber die Wiring an die HTTP-API-Surface
  ist Welle-2/3-Material. Welle 1 liefert nur die REST-
  Surface mit Stub-Bodies.
- **Kein Demo-Compose-Service** — Welle 5 liefert das
  produktive Demo-Compose.
- **Kein Fault-Injection-Backend** — `POST /runs/{id}/
  faults` ist Skeleton; die echte `FaultPort`-Wiring
  (aus M3-Welle-1) folgt in Welle 6.
- **Kein Multi-User-Auth** — M6-Material.

## 2. Scope

Welle 1 liefert **vier Items** ueber 4 Commits (C0..C3):

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses
   Dokument.
2. **ADR-0036-Schaerfung** auf `Provisional` (C1) — mit
   Probe-Run-Beleg + ggf. NEU ADR 0037 (HTTP-API-Surface-
   Pattern, Decisions 4 + 9 + UICommandPort-Frage).
3. **HTTP-API-Surface-Implementation** (C2) — REST-
   Endpunkte + WS-Skeleton + OpenAPI-Schema-Erweiterung
   + Unit-Tests + Integration-Test.
4. **Status/DoD-Sync** (C3) — `M5-welle-1.md` auf `Done`,
   `M5-ui-demo.md §3 Welle 1` DoD-Boxen abgehakt, Top-
   Level-Doku-Sync (Roadmap-Typo-Fix mitnehmen).

## 3. Architektur-Entscheidungen (Welle-1-Decisions)

Welle 1 schliesst diese Decisions aus
[`../done/M5-welle-0.md §3`](../done/M5-welle-0.md):

- **Decision 1 (UI-Stack-Wahl, ADR 0036)** — final.
  Maintainer-Indication „Option 1 (FastAPI + HTMX + Jinja2
  + Chart.js)" durch Probe-Run `9c20dad` validiert. Welle-
  1-C1 zieht ADR 0036 von `Proposed → Provisional` mit
  Probe-Run-Hash als Beleg.
- **Decision 4 (Replay-Controls-API-Vertrag)** — final
  im Welle-1-C1-ADR 0037. Variante:
  - **A** `POST /runs/{id}/{action}` mit literalen Action-
    Endpunkten (`/pause`/`/resume`/`/stop`) — REST-pur,
    aber explodiert die Endpunkt-Anzahl pro Action.
  - **B (Indication)** `POST /runs/{id}/control` mit
    `{"action": "pause|resume|stop"}` im Body — kompakte
    Surface, ein Endpunkt pro Run. Pattern analog vielen
    REST-APIs mit Verb-im-Body fuer State-Transitions.
  - **C** `PATCH /runs/{id}` mit `{"status": "paused|
    running|stopped"}` — REST-pur-er, aber implizite
    State-Transition-Semantik unklar.
  Welle-1-Indication: **B** (kompakte Surface, klare
  Semantik). C1-ADR-Body fixiert das oder begruendet
  Alternative.
- **Decision 9 (UICommandPort-Separation)** — final im
  Welle-1-C1-ADR 0037. Frage: separater Driving-Port
  fuer UI-getriebene Commands oder Wiederverwendung der
  HTTP-API-REST-Surface? Welle-1-Indication: **kein
  separater Port** — die UI ruft die HTTP-API via REST
  + WebSocket; ein `UICommandPort` waere eine Wrapper-
  Schicht ohne klaren Mehrwert. Roadmap-Hinweis „sofern
  getrennt vom HTTP-API" wird so interpretiert dass die
  HTTP-API selbst der UI-Command-Pfad ist. Plus
  **Roadmap-Typo-Fix:** `GG-AR-PORT-DRG-002` (Typo) →
  Verwerfung des Slot-Namens. Roadmap §3 M5 wird in C3
  korrigiert: „UI nutzt `GG-API-001/002/003` —
  `UICommandPort` als separater Slot **verworfen**".

Welle 1 trifft **keine** dieser Decisions:

- Decision 2 (UI-Layout-Lokation) — Welle 2.
- Decision 3 (WebSocket vs SSE) — Welle 3 (Live-Telemetry-
  Producer-Wiring).
- Decision 5 (Demo-Szenario-Inhalt) — Welle 5.
- Decision 6 (Demo-Reproduzierbarkeits-Pflicht) — Welle 5.
- Decision 7 (Charting-Library-Final) — Welle 3.
- Decision 8 (Bundle-Auslieferungs-Pattern) — Welle 2-
  Bestaetigung (Maintainer-Default = vendored Static-
  Asset; ADR-0036-§2.1).
- Decision 10 — bereits in Welle-0-C2 entschieden
  (Roadmap-Status-Flip auf `In Progress`).

## 4. Liefer-Reihenfolge (4 Commits)

### Pre-C0 — bereits erledigt

Drei Commits aus Welle-0-Closure-Folge:

- `fd642df` (Pre-C0a: `git mv`).
- `fb417b9` (Pre-C0b: Cross-Doc-Refs-Sync).
- `9c20dad` (Pre-C0c: HTMX-FastAPI-Smoke-Probe-Run).

### C0 — `docs(plan)`: M5-welle-1 Slice-Doc

**Diff:** dieses Dokument + `in-progress/README.md`-
Bestand-Eintrag.

### C1 — `docs(adr)`: ADR 0036 → Provisional + ggf. NEU ADR 0037

**Diff:**

- `docs/plan/adr/0036-ui-stack-choice.md` — Status-Header
  `Proposed → Provisional` mit Probe-Run-Beleg-Block
  (`9c20dad` als Validation-Hash); Status-Pfad-Body-Block
  aktualisiert. Pattern analog ADR-0030..0035-Status-
  Wechsel in M4-Welle-7-C1 `d2071f0`.
- Plus ADR-0036-§2-Header: Maintainer-Decision-Indication-
  Block beibehalten, plus Welle-1-Probe-Run-Validation-
  Notiz ergaenzt.
- Plus `docs/plan/adr/README.md`-Zeile fuer ADR 0036
  Status-Update.
- **Optional** NEU `docs/plan/adr/0037-http-api-surface-
  pattern.md` mit Status `Proposed`, falls Decisions 4 +
  9 + Roadmap-Typo-Fix als eigenstaendige ADR-Material-
  Schwelle ueberschreiten. Sonst werden die drei
  Entscheidungen kurz im Welle-1-Slice-Doc §3
  dokumentiert (Welle-Pattern: ADR wenn Architektur-
  Decision, Slice-Doc-Body wenn Implementations-
  Detail).
- Welle-1-Indication fuer ADR-0037-Entscheidung:
  **ADR 0037 NEU** (Decision 4 ist eine REST-API-Pattern-
  Entscheidung, die ueber Welle 1 hinaus relevant ist —
  spaetere Wellen muessen wissen, ob `/runs/{id}/control`
  oder `/runs/{id}/pause` der Standard ist).

### C2 — `feat(welle-1)`: HTTP-API-Surface + Tests

**Diff:**

- `src/grid_gym/adapters/driving/http_api/app.py` —
  Erweiterung um 5 REST-Endpunkte + 1 WebSocket-Endpunkt:
  - `GET /runs/{id}` — Run-Detail-Response (Pydantic-
    Model `RunDetailResponse` mit `run_id`, `state`,
    `metadata`).
  - `GET /runs/{id}/status` — kompakter Status (`RunStatus
    Response` mit `state`, `simulation_time`,
    `tick_count`).
  - `POST /runs/{id}/control` — Action-Body (`ControlRequest`
    mit `action: Literal["pause", "resume", "stop"]`).
    Stub-Body in Welle 1; echte Wiring an `TickLoop`
    folgt in Welle 4.
  - `GET /runs/{id}/snapshot` — Snapshot-Export-Endpoint;
    Stub gibt `{"snapshot_envelope_v2_schema_ref": ...}`-
    Placeholder.
  - `POST /runs/{id}/faults` — Fault-Injection-Submit;
    Stub-Body. Echte `FaultPort`-Wiring folgt in Welle 6.
  - `WS /runs/{id}/telemetry` — Skeleton mit Timer-
    getriebenem Counter-Push (analog Probe-Run); echte
    Telemetrie-Producer-Wiring folgt in Welle 3.
- `src/grid_gym/adapters/driving/http_api/_schemas.py`
  (NEU) — Pydantic-Models fuer alle Request/Response-
  Bodies + Error-Format (`GG-API-004`-Standard:
  `code`/`message`/`details`/`run_id`).
- `tests/unit/adapters/driving/http_api/` (ggf. NEU
  Verzeichnis) — Unit-Tests fuer alle neuen Endpunkte:
  - HTTP-Status-Codes (200/404/422).
  - Pydantic-Body-Schemas (Validation-Pfad).
  - WebSocket-Connect-Lifecycle (`accept`/`send_json`/
    `close` ohne Crash).
- `tests/integration/test_m5_welle_1_http_api_smoke.py`
  (NEU) — Integration-Test mit `httpx.AsyncClient`-
  Pattern + WebSocket-Subscribe.
- `tests/integration/test_m5_welle_1_htmx_probe.py`
  bleibt unveraendert als Pre-C0-Probe-Resultat-Beleg
  (wird in Welle-2-C2 entweder ersetzt oder zu Smoke-
  Test umgebaut).

### C3 — `docs(plan|adr)`: Welle-1 Status/DoD-Sync + Top-Level-Doku-Sync

**Diff:**

- `M5-welle-1.md §0 Status` von `In Progress → Done` mit
  Liefer-Hashes (C0/C1/C2/C3) + DoD-Verifikation.
- `M5-ui-demo.md §3 Welle 1`-Section: Status `Pending →
  Done` mit Hashes; DoD-Boxen abgehakt.
- `M5-welle-1.md §9 DoD-Checkliste` Items abhaken (siehe
  §9 unten).
- Top-Level-Doku-Sync (5 Docs):
  - `docs/plan/planning/in-progress/README.md` — Welle-1-
    Eintrag + Naechster-aktiver-Schritt M5-Welle-2.
  - `docs/plan/planning/in-progress/roadmap.md` — Welle-
    1-Bullet-Belegung in §3 M5; ADR-Status-Update fuer
    0036 + ggf. 0037; **Roadmap-Typo-Fix
    `GG-AR-PORT-DRG-002` → Verwerfung** (Welle-0-
    Decision-9-Folge).
  - `README.md` + `README.de.md` — Wave-1-Tabellen-Zeile
    (HTTP-API-Surface produktiv); Test-Counts aktualisiert.
  - `AGENTS.md` — falls M5-spezifische Marker (analog
    M4-Welle-6b-`spdx-check`-Sync), sonst kein Edit.

## 5. Critical Files

| Datei                                                                                | Phase | Aktion                                                                |
| ------------------------------------------------------------------------------------ | ----- | --------------------------------------------------------------------- |
| `docs/plan/planning/in-progress/M5-welle-1.md`                                       | C0    | CREATE (dieses Dokument)                                              |
| `docs/plan/adr/0036-ui-stack-choice.md`                                              | C1    | EDIT (`Proposed → Provisional` mit Probe-Run-Beleg)                   |
| `docs/plan/adr/0037-http-api-surface-pattern.md`                                     | C1    | CREATE (Decisions 4 + 9 + Roadmap-Typo-Fix; Status `Proposed`)        |
| `docs/plan/adr/README.md`                                                            | C1    | EDIT (Status-Update 0036; NEU 0037-Zeile)                             |
| `src/grid_gym/adapters/driving/http_api/app.py`                                      | C2    | EDIT (5 REST + 1 WS Endpunkte; Schema-Wiring)                         |
| `src/grid_gym/adapters/driving/http_api/_schemas.py`                                 | C2    | CREATE (Pydantic-Models + Error-Format)                               |
| `tests/unit/adapters/driving/http_api/test_*.py`                                     | C2    | CREATE (Unit-Tests pro Endpunkt)                                      |
| `tests/integration/test_m5_welle_1_http_api_smoke.py`                                | C2    | CREATE (Integration-Test)                                             |
| `docs/plan/planning/in-progress/M5-ui-demo.md`                                       | C3    | EDIT (§3 Welle 1 Status → Done + DoD-Boxen)                           |
| `docs/plan/planning/in-progress/roadmap.md`                                          | C3    | EDIT (§3 M5-Welle-1-Bullet + Roadmap-Typo-Fix)                        |
| `docs/plan/planning/in-progress/README.md`                                           | C3    | EDIT (Welle-1-Bestand + Naechster Schritt)                            |
| `README.md` + `README.de.md`                                                         | C3    | EDIT (Wave-1-Tabellen-Zeile + Test-Counts)                            |

## 6. Verifikationspfad

**Welle-1-DoD:**

1. `M5-welle-1.md` produktiv mit §1-§9.
2. **ADR 0036 auf `Provisional`** mit Probe-Run-Beleg
   `9c20dad`.
3. **ADR 0037 NEU** (Decisions 4 + 9 + Roadmap-Typo-Fix)
   mit Status `Proposed`.
4. **HTTP-API-Surface produktiv** unter
   `src/grid_gym/adapters/driving/http_api/app.py`: 5
   neue REST-Endpunkte + 1 WS-Endpunkt + Schema-Models.
5. **`GG-API-001..004`-Akzeptanz erfuellt** (REST fuer
   Steuerung + WS-Telemetry + OpenAPI + Fehlerformat).
6. **Unit-Tests** fuer alle neuen Endpunkte; **Integration-
   Test** mit `httpx.AsyncClient` + WS-Connect.
7. `make test-unit` gruen; `make test-integration` gruen
   (40+ Tests).
8. `make arch-check` 20/20 KEPT.
9. `make typecheck` mit `strict_bytes` gruen.
10. `make gates` cache-frei gruen ohne Override.
11. `make docs-check` cache-frei gruen.
12. `make openapi-validate` cache-frei gruen
    (`GG-API-003`).
13. **Roadmap-Typo-Fix** produktiv in `roadmap.md §3 M5`.

**Welle-1-Gate:** `make gates` + `make docs-check` +
`make openapi-validate` cache-frei gruen ohne Override.

## 7. Risiken

- **ADR-0037-Scope-Schwellwert:** falls Decisions 4 + 9
  + Roadmap-Typo-Fix zusammen weniger als ~200 Zeilen
  Body produzieren, koennten sie statt einer eigenen ADR
  als Welle-1-Slice-Doc-§3-Body-Schaerfung dokumentiert
  werden. C1-Implementations-Entscheidung; nicht hier
  vorab. Default-Plan: **ADR 0037 NEU** (Pattern-Treue
  zu M4 wo jede Welle eine ADR hatte).
- **HTTP-API-Stub-vs-Echte-Wiring-Linie:** Welle 1
  liefert nur Skeleton-Bodies fuer `POST /runs/{id}/
  control` + `POST /runs/{id}/faults` + `WS /runs/{id}/
  telemetry`. Risiko: Welle 2/3/4 muss diese Stubs durch
  echte Logik ersetzen; falls die Stub-Schema-Wahl
  schlecht ist, ist das ein Schema-Bruch. Mitigation:
  C2-Code-Review prueft Schema-Pattern-Konsistenz mit
  M3-`TickLoop`-/`FaultPort`-/`TelemetrySinkPort`-
  Surfaces.
- **WebSocket-Reconnect-Pattern unerprobt:** Pre-C0-Probe
  validiert einen einfachen Push-Loop; echtes
  Reconnect-Handling (Tab-Sleep, Network-Drop) ist
  Welle-3-Material. Welle 1 liefert ein
  Skeleton-Pattern, das in Welle 3 erweitert wird.
- **OpenAPI-Schema-Validation bei WebSocket:**
  `make openapi-validate` prueft nur REST. Welle 1 muss
  klarstellen, dass WS-Endpunkte **nicht** im OpenAPI
  abgebildet werden (analog OpenAPI-3.x-Standard:
  WebSocket-Endpunkte sind nicht Teil des OpenAPI-Specs).
  C3-Doku verankert das.
- **`GG-AR-PORT-DRG-002`-Typo-Sweep:** Roadmap-Typo-Fix
  in C3 — pruefen ob andere Docs den falschen Slot-
  Namen referenzieren (`grep -rn "DRG-002" docs/
  spec/`); Welle-0-S3-Review hat das schon angemerkt.

## 8. Wandert nach

- Bei C3-Closure: `M5-welle-1.md` bleibt vorerst in
  `in-progress/` (Pattern analog Welle 0..6b/Welle 7 aus
  M4). Self-Close-Move folgt als M5-Welle-2-Pre-C0.
- `M5-ui-demo.md` bleibt in `in-progress/` bis
  M5-Welle-7-Closure.
- Welle 2 (UI-Foundation) als naechster aktiver Schritt
  mit ggf. NEU ADR fuer UI-Layout-Lokation (Decision 2).

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [ ] **ADR 0036 auf `Provisional`** mit Probe-Run-Beleg
  `9c20dad` (Welle-1-C1).
- [ ] **ADR 0037 NEU** (Decisions 4 + 9 + Roadmap-Typo-
  Fix) mit Status `Proposed` (Welle-1-C1).
- [ ] **ADR-0036-Bezug-Linie** in ADR-Body verlinkt auf
  Welle-1-C1-Commit-Hash als Provisional-Schaerfungs-
  Beleg.
- [ ] **5 REST-Endpunkte produktiv** unter
  `src/grid_gym/adapters/driving/http_api/app.py`:
  `GET /runs/{id}`, `GET /runs/{id}/status`,
  `POST /runs/{id}/control`, `GET /runs/{id}/snapshot`,
  `POST /runs/{id}/faults`.
- [ ] **WebSocket-Endpunkt produktiv:**
  `WS /runs/{id}/telemetry` mit Skeleton-Push.
- [ ] **Pydantic-Schema-Models** in
  `_schemas.py` produktiv (Request + Response + Error).
- [ ] **Unit-Tests** fuer alle neuen Endpunkte (HTTP-
  Codes, Body-Schemas, WS-Lifecycle).
- [ ] **Integration-Test**
  `test_m5_welle_1_http_api_smoke.py` produktiv mit
  `httpx.AsyncClient`-Pattern.
- [ ] **`make test-unit`** gruen mit neuen Tests; Test-
  Count-Increment dokumentiert.
- [ ] **`make test-integration`** gruen (40+ Tests).
- [ ] **`make arch-check`** 20/20 KEPT.
- [ ] **`make typecheck`** mit `strict_bytes` gruen
  (kein neuer `# type: ignore`-Marker).
- [ ] **`make gates`** cache-frei gruen ohne Override.
- [ ] **`make docs-check`** cache-frei gruen.
- [ ] **`make openapi-validate`** cache-frei gruen
  (`GG-API-003`).
- [ ] **Roadmap-Typo-Fix** `GG-AR-PORT-DRG-002` →
  Verwerfung in `roadmap.md §3 M5` (Welle-1-C3).
- [ ] **C3-Top-Level-Doku-Sync** produktiv: 5 Docs auf
  Welle-1-Closure-Stand.

**Anti-Scope-Verifikation (Welle 1 NICHT):**

- [ ] Kein UI-Layout-Code (kein `ui/`-Verzeichnis-
  Anlage; das ist Welle 2).
- [ ] Kein Jinja2-Dep-Add (kommt mit Welle 2).
- [ ] Kein WebSocket-Daten-Producer-Wiring (Welle 3).
- [ ] Kein Replay-Steuerungs-Backend-Code (`POST
  /control` ist Stub; Welle 4 wirkt).
- [ ] Kein Demo-Compose-Service (Welle 5).
- [ ] Kein Fault-Injection-Backend (`POST /faults` ist
  Stub; Welle 6).
- [ ] Keine `noqa`-Marker.

---

## References

- [`../done/M5-welle-0.md`](../done/M5-welle-0.md) — Welle-
  0-Closure mit 10-Item-Decision-Liste (Welle 1 schliesst
  Decisions 1 + 4 + 9).
- [`M5-ui-demo.md`](M5-ui-demo.md) §3 Welle 1 (kanonische
  Slice-Spezifikation).
- [`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md)
  — Pre-M5-Welle-0-Sondierungs-ADR (Welle 1 zieht es auf
  `Provisional`).
- [`../../../../spec/lastenheft.md §16`](../../../../spec/lastenheft.md)
  (`GG-API-001..004` Kommunikationsschnittstellen).
- [`../../../../spec/architecture.md §4.2 + §5`](../../../../spec/architecture.md)
  (Driving-Port-Familie `GG-AR-PORT-DRV-*`;
  `GG-AR-COMP-API`-Slot).
- HTMX-FastAPI-Smoke-Probe-Run `9c20dad` (Probe-Validation
  fuer ADR-0036-Maintainer-Decision-Indication).
- Pattern-Praezedenz Welle-1-Foundation:
  [`../done/M4-welle-1.md`](../done/M4-welle-1.md)
  (`DeviceProtocolPort`-Foundation in M4).
