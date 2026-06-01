# Slice-Plan — M5 UI + Demo — In Progress

**Status:** In Progress — eroeffnet 2026-06-01 mit
M5-Welle-0-C1 (dieser Commit). Sieben Wellen 0..7 entlang
[`../../../../spec/lastenheft.md §16 + §17 + §24`](../../../../spec/lastenheft.md)
(`GG-API-001..004` + `GG-UI-001..009` + `GG-DEMO-001..008`).
Pre-M5-Welle-0-Sondierungs-ADR
[`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md)
ist mit Maintainer-Decision-Indication „Option 1
(FastAPI + HTMX + Jinja2 + Chart.js)" verankert; formale
Festschreibung in M5-Welle-1.

**Datum:** 2026-06-01 (in `in-progress/` direkt eroeffnet
ohne `next/`-Zwischenschritt; Welle-0-Doc-Hoheit fuer den
Hintergrund liegt in [`M5-welle-0.md`](../done/M5-welle-0.md) §1).

**Bezug:**

- [`roadmap.md`](roadmap.md) §3 M5 (Lieferziel, DoD-
  Checkliste, Architekturartefakte).
- M4-Closure-Notiz
  [`../done/M4-results.md`](../done/M4-results.md) §5
  „Welle-7-Erbschaft fuer M5+/M6+".
- [`M5-welle-0.md`](../done/M5-welle-0.md) §3 Decision-Liste
  (10 offene Decisions fuer Welle 1+) + §3 Trigger-
  Drift-Notiz.
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  als Driven-Port-Praezedenz fuer hexagonale Architektur
  (M5 erweitert die **Driving**-Port-Familie `DRV-*`).
- [`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md)
  als Pre-M5-Welle-0-Sondierungs-ADR.
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md)
  §16 (`GG-API-001..004`) + §17 (`GG-UI-001..009`) + §24
  (`GG-DEMO-001..008`).
- [`../../../../spec/architecture.md`](../../../../spec/architecture.md)
  §4.2 (`GG-AR-PORT-DRV-*`-Familie) + §5
  (`GG-AR-COMP-UI`-Slot in `ui/`) + §5
  (`GG-AR-COMP-API`-Slot in `adapters/driving/http_api/`).

---

## 1. Zweck

M5 liefert die UI- und Demo-Schicht als Krönung der M1..M4-
Foundation:

- **UI** (`GG-UI-001..009`): lokales Web-UI fuer Demo +
  Live-Telemetry + Zeitreihen + Replay-Steuerung +
  Alarme + Datenqualitaet sichtbar, optional Geraete-
  Grafik + Fault-Injection-Form + Sim-Zustand.
- **HTTP-API-Vervollstaendigung** (`GG-API-001..004`):
  die in M1-Welle-7 angelegte Stub-Surface
  (`POST /runs` + `/health`) wird zur vollen REST +
  WebSocket-Surface (Run-Status, Telemetrie-Stream,
  Steuerung, Pausieren, Resumieren, Stoppen, Snapshot,
  Fault-Injection).
- **Demo-System** (`GG-DEMO-001..008`): lokal startbare
  Demo-Umgebung nach `docker compose up` mit Live-
  Telemetry binnen 30s, mindestens 1 Replay-Szenario,
  dokumentierter Abnahmereihenfolge.

**Architektur-Familie:** UI + HTTP-API leben unter
`adapters/driving/` (Driving-Ports `GG-AR-PORT-DRV-*` aus
`architecture.md §4.2`). UI nutzt **nur** die durch HTTP-
API exponierte Surface — kein direkter Kern-Zugriff
(`GG-AR-PRINC-*` Hexagonal-Architektur-Disziplin).

**Pre-M5-Welle-0-Sondierungs-Decision (ADR 0036):**

- **UI-Stack:** FastAPI + HTMX + Jinja2 + Chart.js
  (Option 1; Single-Stack-Python; 10 A-1-Gates ohne
  Multi-Stack-Erweiterung).
- **Begruendung:** Architektur-Reinheit > UX-Glanz;
  Welle-Tempo > Multi-Tool-Build-Pipeline; `feedback_
  docker_only`-Treue.
- **Migrationspfad:** Option 1b (SvelteKit-SPA) oder
  Plotly.js/ECharts in Welle 6+/M6 falls Stakeholder-
  Druck spaeter aufkommt.

## 2. Erfolgskriterien

- **MUSS-IDs erfuellt:**
  - `GG-API-001..004` (4 Items): REST-Endpunkte, WebSocket-
    Telemetrie, OpenAPI-Vertrag, standardisierte Fehler.
  - `GG-UI-001..005 + 009` (6 MUSS): Web-UI, Live-Telemetry,
    Zeitreihen, Replay-Controls, Alarme, Quality-Marker.
  - `GG-DEMO-001..005 + 008` (6 MUSS): Demo-Umgebung,
    Netz, Batterie, Live-Telemetry binnen 30s, Replay,
    Abnahmereihenfolge.
- **SOLLTE-IDs erfuellt oder dokumentiert verschoben:**
  - `GG-UI-006..008` (3 SOLLTE): Geraete-Grafik, Fault-
    Injection-Form, Sim-Zustand. **Welle 6**.
  - `GG-DEMO-006/007` (2 SOLLTE): Fault-Injection in Demo,
    Agent in Demo. **Welle 5/6**.
- **DoD-Gates:**
  - `make gates` cache-frei gruen am M5-Closure-Hash
    (10 A-1-Gates; kein `CRITICAL_COV_TARGETS`-Override).
  - `make docs-check` cache-frei gruen.
  - Welle-7-Closure-Gate analog M4-Welle-7: `make
    fullbuild` mit dokumentiertem krb5-CVE-Defer-Pfad
    (Base-Image-Bump bleibt M5-Welle-?-oder-spaeter-
    Material) ODER produktiv gruen falls Base-Image-Bump
    in M5-Welle-? eingezogen wird.
- **ADR-Lifecycle:**
  - ADR 0036 `Proposed → Provisional` (M5-Welle-1) →
    `Accepted` (M5-Welle-7-Closure).
  - Ggf. NEU ADR 0037 (HTTP-API-Surface, Decision 4 + 9
    aus M5-Welle-0-Decision-Liste).
  - Ggf. weitere NEU ADRs pro Welle analog M4-Welle-
    Pattern (z. B. ADR fuer WebSocket-vs-SSE in Welle 3,
    Demo-Pipeline-Pattern in Welle 5).

## 3. Liefer-Reihenfolge (Wellen)

**Sub-Slicing-Schwelle** (Praeambel, ueber alle Wellen
geltend): wenn eine Welle voraussichtlich > 300 Zeilen
Slice-Doc ODER > 5 Code-Commits ODER mehr als zwei
unabhaengige Sub-Bereiche umfasst, wird sie in
W-a/W-b sub-geslict (Pattern analog M4-Welle-5 → 5a/5b
und M4-Welle-6 → 6a/6b). Welle-Sub-Slicing wird in der
betreffenden Welle-C0-Slice-Doc beschlossen, nicht hier
vorab vorbelegt.

### Welle 0 — Slice-Plan-Eroeffnung + Trigger-Triage (Done 2026-06-01)

**Status:** Done. Welle-Slice-Begleit-Doc
[`M5-welle-0.md`](../done/M5-welle-0.md). Liefer-Hashes: C0
`d93ae57` (Slice-Doc) + C0-Review `aa1db52` (12 Findings
adressiert) + C1 `b8bef6c` (Slice-Plan-Eroeffnung —
dieses Dokument) + C2 (dieser Commit; Trigger-Triage +
NEU `open/010-base-image-krb5-cve-bump.md` +
Roadmap-Status-Flip via Decision 10).

### Welle 1 — HTTP-API-Surface + ADR 0036-Schaerfung (Done 2026-06-01)

**Status:** Done 2026-06-01. Foundation-Welle. Pattern
analog M4-Welle-1 (Surface-Foundation vor konkreten
Implementern). Welle-Slice-Begleit-Doc
[`M5-welle-1.md`](../done/M5-welle-1.md). Liefer-Hashes:
Pre-C0a `fd642df` + Pre-C0b `fb417b9` + Pre-C0c `9c20dad`
(HTMX-Probe) + C0 `e573f67` (Slice-Doc) + C1 `d468e68`
(ADRs) + C2 `ae630ce` (Code) + C3 `f9f514d`
(Status/DoD-Sync) + Self-Close-Move `c7c2641`
(M5-Welle-2-Pre-C0a, rename-only).

- [x] **Pre-C0** — HTMX-FastAPI-Smoke-Probe-Run `9c20dad`
  (Maintainer-Decision-Indication-Validierung; Welle-0-
  Decision 1 / N1-Review-Folge). Probe verifiziert:
  FastAPI rendert Jinja2-Template, HTMX-Element triggert
  Server-Call, WS-Push aktualisiert Partial. 4 Probe-
  Tests in
  `tests/integration/test_m5_welle_1_htmx_probe.py`
  gruen — ADR-0036-Maintainer-Decision-Indication
  server-side validiert.
- [x] **ADR 0036 `Proposed → Provisional`** mit Probe-
  Run-Beleg `9c20dad` (Welle-1-C1 `d468e68`).
- [x] **HTTP-API-Surface produktiv** unter
  `src/grid_gym/adapters/driving/http_api/` (Welle-1-C2
  `ae630ce`):
  - REST-Endpunkte: `GET /runs/{id}`, `GET /runs/{id}/
    status`, `POST /runs/{id}/control` (action: pause/
    resume/stop, gemaess Welle-0-Decision 4 = ADR 0037
    Decision API-1), `GET /runs/{id}/snapshot`,
    `POST /runs/{id}/faults`. Aufgeteilt auf 2 APIRouter-
    Module (`_runs_router.py` GET + `_runs_action_router.
    py` POST/WS) wegen `AC-NO-GOD-UTILS`.
  - WebSocket: `WS /runs/{id}/telemetry` fuer Live-
    Telemetry-Stream (`GG-API-002`); Welle-1-Skeleton
    pusht 3 Counter-Messages + Close; 1008-Close fuer
    nicht-existente Runs.
  - OpenAPI-Schema produktiv erweitert (`make openapi-
    validate` gruen; WS bewusst nicht im Schema, ADR
    0037 §3-Klarstellung).
  - Standardisierte Fehlerformate (`GG-API-004`: `code`,
    `message`, `details`, `run_id`) via
    `ErrorResponse`-Pydantic-Model.
- [x] **Decision 4 (Replay-Controls-API-Vertrag)** final
  im Welle-1-C1-ADR 0037 §2.1 als **Decision API-1**:
  `POST /runs/{id}/control` mit Action-Body
  (Variante B; kompakte Surface, erweiterungs-fest).
- [x] **Decision 9 (UICommandPort-Separation)** final im
  Welle-1-C1-ADR 0037 §2.2 als **Decision API-2**:
  **kein separater Slot**; UI nutzt HTTP-API direkt via
  REST + WebSocket (YAGNI). Plus Roadmap-Typo-Fix
  `GG-AR-PORT-DRG-002 → Verwerfung` (ADR 0037 §2.3
  Decision API-3); in C3 in `roadmap.md §3 M5`
  produktiv.
- [x] **Unit-Tests** fuer alle neuen Endpunkte: 6 Tests
  in `test_runs_router.py` + 10 Tests in
  `test_runs_action_router.py` (HTTP-Status-Codes,
  Body-Schemas, WebSocket-Connect-Lifecycle).
- [x] **Integration-Test**
  `test_m5_welle_1_http_api_smoke.py` produktiv mit
  `fastapi.testclient.TestClient`-Pattern (End-to-End-
  Workflow + OpenAPI-Schema-Validation).
- [x] **C3 Doc-Sync** — Status/DoD-Sync + Top-Level-
  Doku-Sync (5 Docs).

**Welle-1-Gate:** `make gates` cache-frei gruen ohne
Override **erfuellt** (10/10 A-1-Gates; 1600 unit + 41
integration Tests passed).

### Welle 2 — UI-Foundation (Pending)

**Status:** Pending. UI-Layout + Chart.js-Vendoring +
Routing-Layer.

- [ ] **UI-Layout-Lokation final** (Welle-0-Decision 2):
  `src/grid_gym/adapters/driving/ui/` (Hexagonal-
  Architektur-Konsistenz) ODER `ui/` Top-Level
  (architecture.md §5 vorbelegt). Slice-Doc-Decision.
- [ ] **Jinja2-Templates-Skeleton** unter
  `<ui-lokation>/templates/`: Base-Layout, Navigation,
  Healthcheck-Page, „Hello"-Demo-Page.
- [ ] **Static-Assets** unter `<ui-lokation>/static/`:
  Chart.js vendored (~70 KB Single-File ohne CDN, gemaess
  Welle-0-Decision 8 = ADR-0036-§2.1-Bestaetigung), CSS-
  Skeleton, HTMX-Vendored (`htmx.min.js`, ~14 KB).
- [ ] **FastAPI-Mount** in `app.py`: Jinja2-Templates +
  StaticFiles-Mount; Routing fuer Base-Pages.
- [ ] **AC-ADAPTER-LIGHTWEIGHT-Filter-Erweiterung** falls
  Cross-Driving-Helper unter `adapters/driving/_*.py`
  entstehen (Welle-0-Welle-6b-C3-F13-Erbschafts-Hinweis;
  ggf. analog zu Welle-6b-C3-Pfad-Filter-Update).
- [ ] **Unit-Tests** fuer Template-Rendering-Pattern +
  Static-Asset-Mount.
- [ ] **C3 Doc-Sync** — Status/DoD-Sync.

**Welle-2-Gate:** `make gates` cache-frei gruen ohne
Override. **UI lokal erreichbar nach `docker compose up`**
(`GG-UI-001` MUSS erfuellt).

### Welle 3 — Live-Telemetry-Dashboard (Pending)

**Status:** Pending. Erfuellt `GG-UI-002/003/009` (Live-
Telemetry-Anzeige + Zeitreihen + Quality-Marker).

- [ ] **Decision 3 (WebSocket vs SSE)** final im Slice-
  Doc mit Probe-Run-Beleg. Default-Indication: FastAPI
  `@app.websocket` (Welle-1-Surface bereits da). SSE-
  Alternative nur falls WebSocket-Setup im Demo-Compose
  fragiler ist als Server-Sent-Events.
- [ ] **Decision 7 (Charting-Library-Final)** final =
  Chart.js (ADR-0036-§2.5-Maintainer-Indication
  bestaetigt im Slice-Doc).
- [ ] **Live-Telemetry-Page** unter `/runs/{id}/telemetry`:
  - HTMX-Element mit `hx-ext="ws"` (oder SSE-Aequivalent)
    fuer WS-Subscription.
  - Telemetry-Tabelle (Geraet/Metrik/Wert/Einheit/Sim-
    Zeit/Quality) als HTMX-Partial-Refresh.
  - Zeitreihen-Chart fuer mind. 1 Leistung + 1 SOC
    (Chart.js `update()`-Pattern bei WS-Push).
- [ ] **Quality-Marker-Visualisierung** (`GG-UI-009`):
  Quality-Statuse `stale`/`invalid`/`nan`/`missing`/
  `fault_injected` per Custom-Point-Style + Tabellen-
  Row-Highlight unterscheidbar.
- [ ] **Unit-Tests** + Integration-Test (WS-Smoke).
- [ ] **C3 Doc-Sync**.

**Welle-3-Gate:** `make gates` + `make test-integration`
mit Live-Telemetry-Smoke gruen.

### Welle 4 — Replay-Controls + Alarme (Pending)

**Status:** Pending. Erfuellt `GG-UI-004/005` (Replay-
Steuerung + Alarme).

- [ ] **Replay-Controls-Page** unter `/runs/{id}/control`:
  Start/Pause/Resume/Stop-Buttons (HTMX-POST gegen
  Welle-1-API); Status-Anzeige (Sim-Zeit, Tick-Zaehler,
  Run-Status).
- [ ] **Alarme-Tabelle** unter `/runs/{id}/alarms`:
  Tabellen-Layout (Zeit/Ziel/Severity/Code/Message/
  Status) mit HTMX-Polling oder WS-Subscription.
- [ ] **Unit-Tests** + Integration-Test.
- [ ] **C3 Doc-Sync**.

**Welle-4-Gate:** `make gates` gruen.

### Welle 5 — Demo-Pipeline (Pending)

**Status:** Pending. Erfuellt `GG-DEMO-001..005 + 008`
(6 MUSS), ggf. `GG-DEMO-006/007` (2 SOLLTE — Welle 5
oder Welle 6).

- [ ] **Decision 5 (Demo-Szenario-Inhalt)** final im
  Slice-Doc: kanonisches Demo-Szenario mit mind. 1
  Netzanschluss + 1 Batterie; weitere optional.
- [ ] **Decision 6 (Demo-Reproduzierbarkeits-Pflicht)**
  final: `make demo` als Pflicht-Target ODER `python -m
  grid_gym demo`-Module. Slice-Doc-Entscheidung.
- [ ] **NEU Demo-Compose-Erweiterung** in
  `deploy/compose.yml`: grid-gym-Runtime + UI + ggf.
  Postgres-Sibling fuer Replay-Telemetry-Speicher
  (`GG-PERSIST-001`-Stub aus M3).
- [ ] **NEU Demo-Szenario-YAML** unter
  `tests/integration/scenarios/demo.yaml` (oder
  `deploy/demo-scenario.yaml`): Geraete-Konfiguration,
  Initial-State, Tick-Anzahl.
- [ ] **NEU `make demo` Makefile-Target** (oder
  Aequivalent): `docker compose up` + Healthcheck +
  Szenario-Start + Live-Telemetry-Anzeige.
- [ ] **NEU `docs/user/demo.md`** mit Abnahmereihenfolge
  (`GG-DEMO-008`).
- [ ] **GG-DEMO-006 (Fault-Injection in Demo)** —
  optional in Welle 5 ODER in Welle 6 (mit `GG-UI-007`-
  Form).
- [ ] **GG-DEMO-007 (Agent in Demo)** — optional in
  Welle 5 (Multi-Agent-Setup aus M3 vorhanden; ggf.
  `RuleBasedAgent` als Demo-Agent).
- [ ] **C3 Doc-Sync**.

**Welle-5-Gate:** `make gates` gruen. **`make demo`
laeuft lokal binnen 30s** (`GG-DEMO-001..004` MUSS).

### Welle 6 — SOLLTE-Features (Pending)

**Status:** Pending. Erfuellt `GG-UI-006..008` (3 SOLLTE).
Plus ggf. `GG-DEMO-006/007` falls in Welle 5 nicht
gemacht.

- [ ] **GG-UI-006 (Geraete-Grafik)**: mindestens MVP-
  Geraetetypen (battery/pv/load/grid_connection/
  smart_meter) mit ID + Typ + Zustand + Quality.
  Implementierungs-Detail: HTMX-Partial pro Geraet oder
  inline-SVG-Pattern.
- [ ] **GG-UI-007 (Fault-Injection-Eingabe-Form)**: Form
  mit Typ/Ziel/Startzeit/Dauer/Recovery-Verhalten +
  Server-side-Validation + Welle-1-API-Submit.
- [ ] **GG-UI-008 (Simulationszustaende)**: Dashboard-
  Page mit Laufstatus + Sim-Zeit + Tick-Zaehler +
  Dienst-Zustand.
- [ ] **Charting-Library-Re-Eval** (Welle-0-Decision 7
  Folge): falls Chart.js-Limitationen in Welle 3/4
  sichtbar werden, hier ggf. Upgrade-Sondierung zu
  Plotly.js/ECharts. Default: bleibt Chart.js.
- [ ] **C3 Doc-Sync**.

**Welle-6-Gate:** `make gates` gruen.

**Welle-6-Sub-Slicing-Risiko:** falls die 3 SOLLTE-
Features einzeln zu gross werden, kann Welle 6 → 6a/6b
sub-geslict werden (Pattern analog M4-Welle-6 → 6a/6b).

### Welle 7 — Closure (Pending)

**Status:** Pending. M5-Closure-Welle analog M3-Welle-7
und M4-Welle-7.

- [ ] **Alle M5-ADRs auf `Accepted`** (mindestens
  ADR 0036; ggf. ADR 0037 fuer HTTP-API-Surface, weitere
  pro Welle).
- [ ] **`done/M5-protocol-adapters.md` Closure-Notiz** —
  Status auf `Done` mit Welle-Stack-Hashes.
- [ ] **NEU `done/M5-results.md`** — Detail-Welle-Tabelle
  + Abnahme-Belege + Pro-Welle-Reviews + S-1..S-6-Sweep
  + Wandert-Nach-Section (Pattern analog
  [`../done/M3-results.md`](../done/M3-results.md) und
  [`../done/M4-results.md`](../done/M4-results.md)).
- [ ] **`roadmap.md` M5-DoD-Checkboxen aktiviert** — alle
  4 Items in `roadmap.md §3 M5` als `[x]`; M5 auf
  `Done`; „Naechster aktiver Slice: M6" setzen.
- [ ] **Top-Level-Doku-Sync** — `README.md` /
  `README.de.md` / `AGENTS.md` / Status-Header in
  `roadmap.md` auf M5-Done-Stand.
- [ ] **Self-Close-Move** — `chore: git mv
  M5-ui-demo.md → done/` (rename-only).
- [ ] **Bezug-Linkpflege an M5-ADRs** (Verfahren per
  ADR 0028) — alle M5-ADRs zeigen auf `planning/done/
  M5-ui-demo.md`.
- [ ] **M5-Welle-7-End-to-End-Sweep S-1..S-6** (analog
  M3-Welle-7 §4 + M4-Welle-7 §4):
  - [ ] **S-1** — M5-Vorabraeumungs-Item: Welle-0-
    Trigger-Triage + Welle-7-Sweep der in M5 dazu-
    gekommenen Trigger.
  - [ ] **S-2** — Sub-Slicing-Schwelle eingehalten ueber
    Welle 1..6; Beleg-Tabelle.
  - [ ] **S-3** — Default-`make gates` ohne
    `CRITICAL_COV_TARGETS`-Override cache-frei gruen
    am Welle-7-Closure-Hash.
  - [ ] **S-4** — `make image-audit` cache-frei gruen
    ODER dokumentierter Defer-Pfad (krb5-CVE-Drift aus
    M3-Welle-7-Erbschaft + M4-Welle-7-Erbschaft; ggf.
    in M5-Welle-? produktiv gefixt mit Base-Image-Bump).
  - [ ] **S-5** — ADR-Erweiterungs-Pattern fortgefuehrt
    (geplante ADR-Anzahl in M5: 1-3 ohne Supersedes per
    ADR 0011).
  - [ ] **S-6** — Lastenheft-Coverage-Sweep nach
    M5-Closure (M6-Trigger erstellen, falls relevant).

**Welle-7-Gate:** `make fullbuild` cache-frei gruen ODER
dokumentierter Defer-Pfad. `make gates` (10 A-1-Gates)
als harter DoD-Gate.

## 4. Out-of-Scope (bleibt fuer M6+)

- **Produktive Anlagensteuerung** (Lastenheft Z.
  1161–1163) — strukturell ausgeschlossen.
- **`GG-PERSIST-001..009`-Vollausbau** — Snapshot-v2→v3-
  Migrations-Lese-Pfad bleibt M6 (M3-/M4-Welle-7-
  Erbschaft).
- **`GG-RT-001..005`** (10000-Points/s-Benchmark) — M6.
- **`GG-SAFE-001..006`** (Sicherheits-Audit) — M6.
- **`GG-SBOM-001..00X`** (SBOM-Generierung) — M6 mit
  Trigger 008.
- **UI-Multi-User / Auth** — M6 (Lastenheft `GG-SAFE-
  008` IP-/Netz-Beschraenkung im Demo-Compose; nicht im
  UI-Layer).
- **Migration zu SvelteKit-SPA oder React-SPA** —
  Welle 6+/M6+ falls Stakeholder-Druck (ADR 0036
  Migrations-Pfad).
- **Plotly.js / ECharts als Charting-Library** —
  Welle 6+/M6+ falls Chart.js-Limitationen in
  Welle 3/4 sichtbar werden (ADR 0036 §2.5).

## 5. Risiken und Fallback

- **HTMX-Pattern unerprobt im Repo:** Welle-1-Pre-C0-
  HTMX-FastAPI-Smoke-Probe ist Pflicht (Welle-0-Decision
  1 / N1-Review-Folge). Bei Misserfolg: Welle-1-Sub-
  Slicing oder Stack-Wahl-Re-Sondierung (sehr
  unwahrscheinlich).
- **WebSocket-Stabilitaet im Demo-Compose:** WS-Reconnect-
  Pattern + Browser-Tab-Sleep-Handling sind in
  Welle 3 zu probieren. Fallback: SSE (Welle-0-Decision
  3-Alternative).
- **Chart.js-Live-Streaming-Performance:** bei > 1000
  Datapoints koennte Canvas-Rerender langsam werden.
  Mitigation: rollendes-Window-Pattern (nur die letzten
  N Punkte zeigen) oder ECharts-Upgrade in Welle 6+.
- **Demo-Compose-Komplexitaet:** Welle 5 erweitert
  `deploy/compose.yml` um UI-Service + ggf. Postgres-
  Sibling. Risiko: `make demo` braucht > 30s (`GG-DEMO-
  004`-Verletzung). Mitigation: Image-Pre-Pull in
  Healthcheck-Pattern.
- **AC-ADAPTER-LIGHTWEIGHT-Erweiterung:** falls Welle 2
  Cross-Driving-Helper unter `adapters/driving/_*.py`
  einfuehrt, ist analog Welle-6b-C3-Pfad-Filter-Update
  noetig (Slice-034-F13-Erbschaft).
- **`make fullbuild`-krb5-CVE-Drift** bleibt
  pre-existing rot bis Base-Image-Bump. M5 macht keinen
  Bump (Welle-7-Closure dokumentiert Defer-Pfad analog
  M4-Welle-7), es sei denn ein eigener Slice-Trigger
  wird in M5 angelegt.

## 6. Wandert nach

- Bei Welle-7-Closure: `M5-ui-demo.md` → `done/M5-ui-
  demo.md` (Self-Close-Move analog `M4-protocol-
  adapters.md` in M4-Welle-7-C4 `e745f10`).
- Pre-C0-Self-Close-Moves der einzelnen Welle-Slice-Docs
  (`M5-welle-N.md` → `done/`) folgen dem Pattern Welle
  0..6b aus M4 (rename-only Commit per `feedback_git_
  mv`-Memory-Konvention).
- M6 wechselt mit M5-Welle-7-Closure von `Vorbelegung`
  auf `Naechster aktiver Slice`.

## 7. Verifikationspfad

**M5-DoD (Gesamtmeilenstein):**

1. `make gates` cache-frei gruen am M5-Closure-Hash
   (10 A-1-Gates; harter DoD-Gate).
2. `make docs-check` cache-frei gruen.
3. `make test-integration` enthaelt mind. 1 UI-Smoke
   (HTTP-API + WS-Connect + Replay-Steuerung).
4. `make demo` (oder Aequivalent) startet lokal binnen
   30s mit Live-Telemetry.
5. Alle M5-ADRs (mindestens ADR 0036; ggf. weitere) auf
   `Accepted`.
6. `roadmap.md §3 M5` 4 DoD-Checkboxen alle `[x]`; M5
   auf `Done`.
7. `done/M5-results.md` produktiv mit §1-§7 (Welle-
   Tabelle + Abnahme-Belege + Pro-Welle-Reviews +
   S-1..S-6-Sweep + Wandert-Nach + Nicht-vollzogene
   Items).
8. `make fullbuild` cache-frei gruen ODER dokumentierter
   Defer-Pfad in `M5-results.md §2` (analog M4-Welle-7-
   krb5-CVE-Defer).

**Pro-Welle-Gates:** siehe §3-Welle-spezifische Gates
(`Welle-N-Gate:` jeweils am Ende der Welle-N-Section).

**Sub-Slicing-Schwelle:** §3-Praeambel — pro Welle
gepruft, ob C-Schwelle ueberschritten wird.

**Pattern-Praezedenz fuer Welle-7-Closure:**
[`../done/M3-results.md`](../done/M3-results.md) und
[`../done/M4-results.md`](../done/M4-results.md).
