# Welle 2 — M5 UI-Foundation (Jinja2 + HTMX + Chart.js)

**Status:** Done 2026-06-01 — Liefer-Stack:
Pre-C0a `c7c2641` (Self-Close-Move M5-welle-1.md → done/,
rename-only) + Pre-C0b `a0c8ba3` (Cross-Doc-Refs-Sync,
6 Files) + C0 `64d5129` (Slice-Doc + Decision 2 final
fixiert) + C2 `5234617` (UI-Foundation: Jinja2-Dep +
vendored HTMX/Chart.js + StaticFiles-Mount + 2 Page-
Routes + 4 Templates + 2 Partials + 18 Tests; +10 unit
+ 2 integration = 1610 unit + 43 integration; 10/10
A-1-Gates gruen) + C3 (dieser Commit; Status/DoD-Sync +
Top-Level-Doku-Sync).

Welle 2 ist die **UI-Foundation-Welle** in M5. Pattern
analog M4-Welle-2 ([`../done/M4-welle-2.md`](../done/M4-welle-2.md))
— erste konkrete Implementation nach der Surface-Foundation-
Welle (M5-Welle-1 lieferte die HTTP-API-Surface, M5-Welle-2
liefert den UI-Layer der diese Surface verwendet). Welle 2
liefert das **Jinja2-Templates-Skeleton** + die **HTMX/
Chart.js-Vendored-Assets** + den **FastAPI-Static-Mount**.
**Keine Live-Telemetry-Logik** in Welle 2 — das ist Welle-3-
Scope; Welle 2 baut nur die UI-Hülse, in die Welle 3
einsteigt.

**Pre-C0 abgeschlossen (2 Commits):**

1. Pre-C0a `c7c2641` — `git mv in-progress/M5-welle-1.md
   → done/` (rename-only). Pattern aus Memory
   `feedback_git_mv`.
2. Pre-C0b `a0c8ba3` — Cross-Doc-Refs-Sync nach Move
   (6 Files); Re-Verifikation per `make docs-check`.

**Welle-1-Probe deckt Welle-2-Probe-Bedarf:** Pre-C0c
(Static-Mount + Vendor-Asset-Probe) **bewusst NICHT
geliefert**, weil M5-Welle-1-Pre-C0c `9c20dad` HTMX +
Jinja2 + WebSocket bereits server-side validiert hat
(4 Tests gruen). Static-Mount + Vendoring sind FastAPI-
Doku-Standard-Boilerplate ohne neue Risiken.

**Spec-Reife:** Inhaltlich final fuer Welle 2. **Welle-2-
Decision-Liste** (§3) schliesst Decision 2 (UI-Layout-
Lokation) aus M5-Welle-0-§3-Decision-Liste; Welle-3-bis-6-
Decisions bleiben deferred.

---

## 1. Context

M5-Welle-1
([`../done/M5-welle-1.md`](../done/M5-welle-1.md)) hat die
HTTP-API-Surface (5 REST + 1 WebSocket-Endpunkt) unter
`src/grid_gym/adapters/driving/http_api/` produktiv
geliefert. Welle 2 setzt darauf die **UI-Hülse** auf: ein
Jinja2-Templates-Skeleton mit Base-Layout, eine Navigation
und zwei initiale Seiten (Health + Demo-Hello), sowie die
**vendored Static-Assets** (HTMX + Chart.js) gemaess
ADR-0036-§2.1-Maintainer-Indication.

### 1.1 Existierende Substanz (M5-Welle-1)

`src/grid_gym/adapters/driving/http_api/` (Stand
2026-06-01) liefert:

- `app.py` — FastAPI-`app`-Instanz + `/health`, `POST /runs`
  + 5 REST + 1 WS Welle-1-Endpunkte (via APIRouter-
  Mounts).
- `_dependencies.py` — `get_run_repository` +
  `_RunRepositoryNotConfiguredError`.
- `_schemas.py` — Pydantic-Models fuer alle Endpunkte.
- `_runs_router.py` + `_runs_action_router.py` —
  APIRouter-Module.

Welle 2 erweitert das um den parallel-laufenden UI-
Adapter unter `src/grid_gym/adapters/driving/ui/` und
einen StaticFiles-Mount + Page-Router-Include in
`app.py`.

### 1.2 Welle-2-Lieferziel

Fuenf Sub-Items:

1. **UI-Adapter-Modul** unter
   `src/grid_gym/adapters/driving/ui/`:
   - `__init__.py` — Modul-Marker mit ADR-0036-Verweis.
   - `_templates.py` — `Jinja2Templates`-Factory
     (FastAPI-Standard-Pattern; private Helper-Modul mit
     `_`-Prefix gemaess Convention).
   - `routes.py` — Page-Routes via `APIRouter` (analog
     `_runs_router.py`-Pattern aus Welle 1):
     - `GET /` — Demo-Hello-Page (Base-Layout mit HTMX-
       Sanity-Check).
     - `GET /ui/health` — Healthcheck-UI-Seite (rendert
       `/health`-JSON via HTMX-Partial; Welle-2-Sanity).
   - `templates/base.html` — HTML-Base-Layout mit
     `<head>`-Block, `<nav>`-Partial-Include + Content-
     Block.
   - `templates/navigation.html` — Navigation-Partial
     (Links zu UI-Health + Demo-Hello + spaeter
     /runs/...).
   - `templates/health.html` — Healthcheck-UI-Seite.
   - `templates/demo.html` — Demo-Hello-Page mit HTMX-
     Sanity-Probe (Button mit `hx-get="/ui/health"`).
   - `static/htmx.min.js` — vendored HTMX 2.x (~14 KB).
   - `static/chart.umd.min.js` — vendored Chart.js 4.x
     (~70 KB).
   - `static/style.css` — CSS-Skeleton (Reset + Base-
     Layout-Grid; minimal).

2. **FastAPI-Mount-Erweiterung** in
   `src/grid_gym/adapters/driving/http_api/app.py`:
   - `StaticFiles`-Mount auf `/static`.
   - `app.include_router(ui_router)` (Pattern analog
     Welle-1-`include_router(runs_router)`).
   - Module-Docstring-Update um UI-Layer-Bezug.

3. **Jinja2-Dependency-Add** in `pyproject.toml`
   (`jinja2 >= 3.1, < 4.0`) + `uv.lock`-Sync via
   Docker-Build.

4. **Unit-Tests** unter
   `tests/unit/adapters/driving/ui/`:
   - `test_templates.py` — Jinja2Templates-Factory-Test
     (rendert ein Template ohne Crash; Helper-Lokation-
     Test).
   - `test_routes.py` — Page-Routes-Tests (3 Tests:
     GET / Status-200 + Content-Type-HTML; GET
     /ui/health 200 + HTMX-Partial-Resolution per
     `HX-Request`-Header; Static-Asset-Mount serves
     vendored Assets).

5. **Integration-Test** unter
   `tests/integration/test_m5_welle_2_ui_smoke.py` —
   End-to-End-UI-Smoke mit `TestClient`:
   - GET / → HTML + Asset-Tags sichtbar.
   - GET /static/htmx.min.js → 200 + Content-Type-JS.
   - GET /static/chart.umd.min.js → 200 + Content-Type-
     JS.
   - GET /ui/health full-page → Healthcheck-Sektion sichtbar.
   - GET /ui/health mit `HX-Request: true` → HTMX-
     Partial-Body ohne Base-Layout-Boilerplate.

### 1.3 Welle-2-Anti-Scope

- **Kein Live-Telemetry-Code** — `/runs/{id}/telemetry`-UI-
  Seite + Chart.js-Live-Update + HTMX-WS-Subscribe sind
  Welle-3-Scope. Welle 2 vendored Chart.js nur, ohne es zu
  benutzen (es ist im Bundle, aber kein Template inkludiert
  Chart.js noch).
- **Kein Replay-Controls-UI** — Pause/Resume/Stop-Buttons
  sind Welle-4-Scope.
- **Kein Scenario-Editor** — Welle-5-Scope (`GG-UI-006..008`).
- **Kein Fault-Injection-UI** — Welle-6-Scope.
- **Kein Demo-Compose-Service** — Welle-5-Scope.
- **Kein Frontend-Build-Step** (Vite/Webpack/etc.) — Vendored
  Static-Assets sind das gewuenschte Pattern (ADR-0036-§2.1).
- **Keine `noqa`-Marker**, kein `# type: ignore` ohne
  Begruendung.

## 2. Scope

Welle 2 liefert **vier Items** ueber 3..4 Commits (C0..C3,
ggf. C1-ADR-Schaerfung optional):

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses
   Dokument.
2. **C1 (optional)** — ADR-0036-§-Schaerfung um Welle-2-
   Decision 2 (UI-Layout-Lokation final fixiert auf
   `src/grid_gym/adapters/driving/ui/`); ALTERNATIV
   Welle-2-Slice-Doc-§3-Body trägt die Decision direkt
   ohne ADR-Edit. **Indication:** Welle-2-Slice-Doc-§3
   trägt es; ADR 0036 ist `Provisional` und Welle-7-
   Closure-Schaerfung passt darauf besser. **C1 entfaellt,
   Welle 2 lieferte in 3 Commits (C0/C2/C3).**
3. **UI-Adapter-Code + Jinja2-Dep + Tests** (C2) —
   `src/grid_gym/adapters/driving/ui/` + `pyproject.toml`-
   Edit + Static-Mount in `app.py` + Unit-Tests +
   Integration-Test.
4. **Status/DoD-Sync** (C3) — `M5-welle-2.md` auf `Done`,
   `M5-ui-demo.md §3 Welle 2` DoD-Boxen abgehakt, Top-
   Level-Doku-Sync.

## 3. Architektur-Entscheidungen (Welle-2-Decisions)

### 3.1 Decision 2 (UI-Layout-Lokation) — final fixiert

**Frage:** Wo lebt der Jinja2/HTMX/Chart.js-Stack?

**Optionen aus M5-Welle-0-§3:**

- **A (gewaehlt)** — `src/grid_gym/adapters/driving/ui/`
  (Hexagonal-Architektur-Konsistenz).
- **B** — `ui/` Top-Level (architecture.md §5
  Vorbelegung).
- **C** — Hybrid: Templates+Routes in `adapters/driving/
  ui/`, nur Static unter Top-Level `ui/static/`.

**Gewaehlt:** **Option A** — `src/grid_gym/adapters/
driving/ui/`. Begruendung:

1. **Hexagonal-Architektur-Konsistenz.** Der UI-Layer ist
   ein **Driving-Adapter** (er ruft Domain-Logik per HTTP-
   API auf, analog zu wie der HTTP-API-Adapter selbst
   bereits ein Driving-Adapter ist). Alle anderen
   Driving-Adapter (`http_api/`) und alle Driven-Adapter
   (`protocol_mqtt/`, `protocol_modbus/`, etc.) leben unter
   `src/grid_gym/adapters/{driving,driven}/`. Eine UI-
   Layout-Lokation ausserhalb dieses Pattern waere ein
   semantischer Ausreisser.
2. **`AC-ADAPTER-LIGHTWEIGHT`-Contract** ([`../../../../tools/arch_check.py`](../../../../tools/arch_check.py))
   erfasst den Pfad bereits ohne Filter-Erweiterung
   (`_is_adapter_lightweight_path` returns `True` fuer alle
   Pfade unter `src/grid_gym/adapters/driving/`). Zyklomatische-
   Komplexitaet-Limit (`<= 8`) ist fuer UI-Routes
   angemessen (Routes machen typischerweise wenig Logik,
   nur Template-Rendering).
3. **architecture.md §5 vorbelegt** Top-Level `ui/`, das ist
   eine **alte Vorbelegung aus Pre-M1-Zeit** (Spike-0-
   Material) bevor die Hexagonal-Adapter-Struktur stabil
   war. Welle 2 schliesst das durch Schaerfung im Welle-2-
   C3-Top-Level-Doku-Sync (architecture.md §5 oder Welle-
   2-Folge-Edit).
4. **Python-Package-Konsistenz.** Module unter
   `src/grid_gym/` sind im Package-Namespace `grid_gym.*`,
   was die Imports trivial macht. Top-Level `ui/` waere
   ausserhalb des Packages — entweder mit
   `pyproject.toml`-`tool.uv.packages-include`-Hack oder
   per `sys.path`-Manipulation. Beides waere
   Pakettheorie-Bruch.
5. **Vorbild M4-Welle-2.** M4-Welle-2 (MQTT-Adapter) hat
   das Pattern etabliert: Adapter unter
   `adapters/driven/protocol_mqtt/` mit Templates-aequiva-
   lentem `_*.py`-Helper-Pattern. Welle 2 wendet dasselbe
   auf die Driving-Side an.

**Architektur-Konsequenz:** Decision 2 wird **NICHT** als
ADR-0036-Schaerfung verankert (kein C1-Commit), sondern hier
im Slice-Doc-§3-Body. ADR 0036 ist `Provisional` und
schliesst bei M5-Welle-7-Closure direkt auf `Accepted`.
Welle-7-Closure kann die Layout-Lokation dann als
Welle-2-Realisierung-Beleg in den ADR-Body aufnehmen
(Pattern analog ADR 0030 §6 Verzicht-Anhang-Slot, der mit
M4-Welle-7-C1 von Provisional-Indication auf Accepted-
Realisierung gezogen wurde).

### 3.2 Decision 8 (Bundle-Auslieferungs-Pattern) — bestaetigt

ADR-0036-§2.1-Maintainer-Indication: **vendored Static-
Asset, kein CDN**. Welle 2 bestaetigt das produktiv durch
das Ablegen von `htmx.min.js` + `chart.umd.min.js` unter
`src/grid_gym/adapters/driving/ui/static/`. Pattern-
Begruendung:

- **Offline-Reproduzierbarkeit** (`GG-DEMO-001..008`-DoD).
- **Keine externe Network-Dependency** in
  `docker compose up`-Demo-Pfad.
- **Bundle-Groesse minimal:** HTMX ~14 KB + Chart.js
  ~70 KB = ~84 KB Static-Assets im Repo. Pattern-Praezedenz:
  M3-Welle-6-OTLP-Adapter brachte ~XX KB Dep zum Repo,
  vendored Static-Assets sind eine Groessen-Klasse kleiner.

**Quelle:** HTMX von [htmx.org GitHub-Releases](https://github.com/bigskysoftware/htmx/releases) v2.x;
Chart.js von [chartjs.org GitHub-Releases](https://github.com/chartjs/Chart.js/releases) v4.x.
Beide MIT-lizenziert (passend zu grid-gym-Lizenz). C2-Commit
dokumentiert Version + SHA256-Hash der vendored Files in
einer NEU `static/VENDORED.md`-Datei (Pattern analog zu wie
M3-Welle-6-OTLP-Adapter seine Dep-Pin dokumentiert).

### 3.3 Welle 2 trifft KEINE dieser Decisions

- Decision 3 (WebSocket vs SSE) — Welle 3.
- Decision 5 (Demo-Szenario-Inhalt) — Welle 5.
- Decision 6 (Demo-Reproduzierbarkeits-Pflicht) — Welle 5.
- Decision 7 (Charting-Library-Final) — Welle 3 (mit
  realer Time-Series-Anwendung); Welle 2 vendored
  Chart.js nur, ohne es zu nutzen.

## 4. Liefer-Reihenfolge (3 Commits)

### Pre-C0 — bereits erledigt

- Pre-C0a `c7c2641` (Self-Close-Move; rename-only).
- Pre-C0b `a0c8ba3` (Cross-Doc-Refs-Sync, 6 Files).
- **Pre-C0c entfaellt** — Welle-1-Probe `9c20dad` deckt
  Welle-2-Probe-Bedarf (HTMX + Jinja2 + WS server-side
  validiert; Static-Mount + Vendoring sind FastAPI-
  Boilerplate ohne neue Risiken).

### C0 — `docs(plan)`: M5-welle-2 Slice-Doc

**Diff:** dieses Dokument + `in-progress/README.md`-
Bestand-Eintrag.

### C2 — `feat(welle-2)`: UI-Foundation + Jinja2-Dep + Tests

**Diff:**

- `pyproject.toml` — `jinja2 >= 3.1, < 4.0` zu
  `[project] dependencies` hinzu (Jinja2 ist FastAPI-
  Standard-Templating; nicht in
  FastAPI-Default-Install). Plus `uv.lock`-Sync via
  Docker-Build.
- NEU `src/grid_gym/adapters/driving/ui/__init__.py` —
  Modul-Marker.
- NEU `src/grid_gym/adapters/driving/ui/_templates.py` —
  Jinja2Templates-Factory `get_templates() -> Jinja2Templates`
  mit Pfad-Resolution via `Path(__file__).parent /
  "templates"`.
- NEU `src/grid_gym/adapters/driving/ui/routes.py` —
  Page-Routes `ui_router = APIRouter(tags=["ui"])` mit 2
  Endpunkten (`GET /` Demo-Hello, `GET /ui/health`
  Healthcheck).
- NEU `src/grid_gym/adapters/driving/ui/templates/base.html`
  — HTML5-Base-Layout: `<head>` mit `<title>` + `<meta>`-
  Tags + Static-CSS + Static-HTMX-Script-Include;
  `<nav>`-Partial-Include; Content-Block via Jinja2
  `{% block content %}{% endblock %}`.
- NEU `templates/navigation.html` — Nav-Partial.
- NEU `templates/health.html` — Healthcheck-UI-Seite mit
  HTMX-Sanity-Probe.
- NEU `templates/demo.html` — Demo-Hello-Page.
- NEU `src/grid_gym/adapters/driving/ui/static/htmx.min.js`
  — vendored HTMX 2.x (MIT).
- NEU `static/chart.umd.min.js` — vendored Chart.js 4.x
  (MIT).
- NEU `static/style.css` — CSS-Skeleton.
- NEU `src/grid_gym/adapters/driving/ui/static/VENDORED.md`
  — Vendor-Version + SHA256-Hash + Lizenz-Refs.
- `src/grid_gym/adapters/driving/http_api/app.py` —
  Edit:
  - `StaticFiles`-Mount auf `/static`.
  - `app.include_router(ui_router)`.
  - Docstring-Update.
- NEU `tests/unit/adapters/driving/ui/__init__.py`.
- NEU `tests/unit/adapters/driving/ui/test_templates.py`
  — `get_templates()`-Smoke + Template-Rendering-Test.
- NEU `tests/unit/adapters/driving/ui/test_routes.py` —
  3 Tests: GET / 200 HTML + GET /ui/health 200 + HTMX-
  Partial-Pfad bei `HX-Request: true`.
- NEU `tests/integration/test_m5_welle_2_ui_smoke.py` —
  End-to-End-UI-Smoke (HTML + Asset-Mount + HTMX-
  Partial).

### C3 — `docs(plan)`: Welle-2 Status/DoD-Sync + Top-Level-Doku-Sync

**Diff:**

- `M5-welle-2.md §0 Status` von `In Progress → Done` mit
  Liefer-Hashes (C0/C2/C3) + DoD-Verifikation.
- `M5-ui-demo.md §3 Welle 2` Status `Pending → Done` mit
  Hashes; 7 DoD-Boxen abgehakt.
- `M5-welle-2.md §9 DoD-Checkliste` Items abhaken.
- Top-Level-Doku-Sync (5 Docs):
  - `docs/plan/planning/in-progress/README.md` — Welle-
    2-Eintrag + Naechster aktiver Schritt M5-Welle-3.
  - `docs/plan/planning/in-progress/roadmap.md` — Welle-
    2-Bullet-Belegung in §3 M5.
  - `README.md` + `README.de.md` — Test-Counts
    aktualisiert; M5-Tabellen-Zeile um Welle-2-Detail
    ergaenzt.
  - `AGENTS.md` — falls M5-spezifische Marker (analog
    M4-Welle-6b-`spdx-check`-Sync), sonst kein Edit.

## 5. Critical Files

| Datei                                                                                | Phase | Aktion                                                                |
| ------------------------------------------------------------------------------------ | ----- | --------------------------------------------------------------------- |
| `docs/plan/planning/in-progress/M5-welle-2.md`                                       | C0    | CREATE (dieses Dokument)                                              |
| `pyproject.toml`                                                                     | C2    | EDIT (`jinja2 >= 3.1, < 4.0`)                                         |
| `src/grid_gym/adapters/driving/ui/__init__.py`                                       | C2    | CREATE (Modul-Marker)                                                 |
| `src/grid_gym/adapters/driving/ui/_templates.py`                                     | C2    | CREATE (`get_templates()`-Factory)                                    |
| `src/grid_gym/adapters/driving/ui/routes.py`                                         | C2    | CREATE (2 Page-Routes via APIRouter)                                  |
| `src/grid_gym/adapters/driving/ui/templates/*.html`                                  | C2    | CREATE (4 Templates: base, navigation, health, demo)                  |
| `src/grid_gym/adapters/driving/ui/static/*`                                          | C2    | CREATE (3 vendored + VENDORED.md)                                     |
| `src/grid_gym/adapters/driving/http_api/app.py`                                      | C2    | EDIT (StaticFiles-Mount + `include_router(ui_router)`)                |
| `tests/unit/adapters/driving/ui/test_*.py`                                           | C2    | CREATE (2 Unit-Test-Files)                                            |
| `tests/integration/test_m5_welle_2_ui_smoke.py`                                      | C2    | CREATE (Integration-Test)                                             |
| `docs/plan/planning/in-progress/M5-ui-demo.md`                                       | C3    | EDIT (§3 Welle 2 Status → Done + DoD-Boxen)                           |
| `docs/plan/planning/in-progress/roadmap.md`                                          | C3    | EDIT (§3 M5-Welle-2-Bullet)                                           |
| `docs/plan/planning/in-progress/README.md`                                           | C3    | EDIT (Welle-2-Bestand + Naechster Schritt)                            |
| `README.md` + `README.de.md`                                                         | C3    | EDIT (Test-Counts + Slice-Liste + M5-Tabellen-Zeile)                  |

## 6. Verifikationspfad

**Welle-2-DoD:**

1. `M5-welle-2.md` produktiv mit §1-§9.
2. **UI-Adapter-Modul produktiv** unter
   `src/grid_gym/adapters/driving/ui/`: `routes.py` +
   `_templates.py` + 4 Templates + 3 Static-Assets +
   `VENDORED.md`.
3. **Jinja2-Dep produktiv** in `pyproject.toml`.
4. **FastAPI-Mount produktiv** in `app.py`:
   `StaticFiles` auf `/static` + `include_router(ui_router)`.
5. **Unit-Tests** fuer Templates + Routes; **Integration-
   Test** mit Asset-Mount + HTMX-Partial-Pfad.
6. `make test-unit` gruen mit neuen Tests
   (~1600 + 5..7 Welle-2-Unit-Tests).
7. `make test-integration` gruen (~41 + 1..3 Welle-2-
   Integration-Tests).
8. `make arch-check` 20/20 KEPT (kein
   `AC-ADAPTER-LIGHTWEIGHT`-Verstoss; Routes haben
   minimale Komplexitaet).
9. `make typecheck` mit `strict_bytes` gruen.
10. `make gates` cache-frei gruen ohne Override.
11. `make docs-check` cache-frei gruen.
12. `make openapi-validate` cache-frei gruen
    (`GG-API-003` — UI-Routes sind nicht
    OpenAPI-relevant aber `/health` + Welle-1-Endpunkte
    bleiben sichtbar).
13. **`GG-UI-001` (UI lokal erreichbar)** erfuellt durch
    Smoke-Test gegen GET / und GET /ui/health.

**Welle-2-Gate:** `make gates` + `make docs-check` +
`make openapi-validate` cache-frei gruen ohne Override.

## 7. Risiken

- **Jinja2-Dep-Add bricht Build?** Pyproject-Edit ist
  trivial (eine Zeile in `[project] dependencies`), aber
  `uv.lock`-Sync braucht Dockerfile-Stage-Trigger. Welle 2
  laeuft `make rebuild` einmal nach dem
  pyproject-Edit, um `uv.lock` zu aktualisieren; danach
  `make gates` cache-frei. Mitigation: C2 macht den
  Jinja2-Dep-Add **vor** dem Code-Add (sequenzielle Sub-
  Steps innerhalb von C2 falls Dep-Add fehlschlaegt).
- **Static-Asset-Vendoring vs Lizenz-Boundary:** HTMX +
  Chart.js sind beide MIT. Pattern-Praezedenz aus M4-Welle-
  5b (IEC-61850 GPL-Boundary) ist hier nicht relevant —
  MIT in MIT-Projekt ist transparent. Aber `VENDORED.md`-
  Doku ist Pflicht-Item fuer Welle-2-C2: Version + SHA256-
  Hash + Lizenz-Pointer, damit M6-Sicherheits-Audit
  reproduzierbar nachvollziehen kann was vendored ist.
- **`AC-ADAPTER-LIGHTWEIGHT`-Filter-Erweiterung noetig?**
  Antwort: nein. `_is_adapter_lightweight_path` returns
  `True` fuer alle Pfade unter `src/grid_gym/adapters/
  driving/` (Welle-6b-C3-F13-Schaerfung war nur fuer
  `driven/`-Layer Flat-File-Helper, nicht fuer
  `driving/`). Welle 2 dokumentiert das im Slice-Doc-§3
  und bestaetigt im C3.
- **Welle-1-FastAPI-Lifecycle-Konflikt:** Welle 1 hat
  `app` als `Final[FastAPI]` mit M1-Welle-6a/6b
  Welle-1-Endpunkten + Router-Mounts am Module-Ende.
  Welle 2 fuegt **vor** den Welle-1-Router-Mounts den
  Static-Mount + UI-Router-Mount ein? Oder am Ende? Reihenfolge
  ist irrelevant fuer FastAPI (Routen werden nach URL-
  Pattern dispatched, nicht nach Reihenfolge), aber Code-
  Style: Welle-2-Mounts kommen am Ende der bestehenden
  Mount-Sektion.
- **OpenAPI-Schema-Pollution:** UI-Routes (`GET /`,
  `GET /ui/health`) erscheinen automatisch im OpenAPI-
  Schema. Das ist akzeptabel (`GG-API-003`-Akzeptanz: das
  Schema deckt **alle** HTTP-Endpunkte ab; UI-Routes
  bekommen den `tags=["ui"]`-Marker, damit das Schema
  sinnvoll gegliedert bleibt). Welle 2 verifiziert per
  Integration-Test, dass die Routes im Schema sichtbar
  sind aber den `ui`-Tag tragen.

## 8. Wandert nach

- Bei C3-Closure: `M5-welle-2.md` bleibt vorerst in
  `in-progress/` (Pattern analog Welle 1). Self-Close-Move
  folgt als M5-Welle-3-Pre-C0.
- `M5-ui-demo.md` bleibt in `in-progress/` bis
  M5-Welle-7-Closure.
- Welle 3 (Live-Telemetry-Dashboard) als naechster aktiver
  Schritt mit Decision 3 (WebSocket vs SSE) + Decision 7
  (Charting-Library-Final).

## 9. DoD-Checkliste (mit C3 abgehakt)

- [x] **UI-Adapter-Modul produktiv** unter
  `src/grid_gym/adapters/driving/ui/`: 6 Templates
  (`base.html`, `navigation.html`, `demo.html` +
  `_demo_content.html` Partial, `health.html` +
  `_health_content.html` Partial) + 3 Static-Assets
  (`htmx.min.js` 51 KB, `chart.umd.min.js` 204 KB,
  `style.css`) + `VENDORED.md` + `routes.py` +
  `_templates.py` + `__init__.py`.
- [x] **`jinja2>=3.1,<4.0`** in
  `pyproject.toml`-`[project] dependencies` produktiv
  (uv.lock-Sync `Added jinja2 v3.1.6`). Plus
  `AC-PORTS-NO-FW` + `AC-NO-FW` Forbidden-Listen um
  `jinja2` erweitert (analog Pattern fuer `fastapi` etc.).
- [x] **`StaticFiles`-Mount auf `/static`** produktiv in
  `app.py` mit absolutem Pfad
  `Path(__file__).parent.parent / "ui" / "static"`.
- [x] **`app.include_router(ui_router)`** produktiv in
  `app.py` direkt nach den Welle-1-Run-Routern.
- [x] **Unit-Tests** fuer Templates + Routes:
  `test_templates.py` (3 Tests: Factory-Type + Pfad-
  Resolution + Render-Smoke) + `test_routes.py` (7 Tests:
  GET / Full + HTMX-Partial; GET /ui/health Full + HTMX-
  Partial; HTMX-JS + Chart-JS + CSS Static-Mount).
- [x] **Integration-Test** `test_m5_welle_2_ui_smoke.py`
  produktiv mit `TestClient` (2 Tests: End-to-End-
  Workflow + OpenAPI-Schema-Check mit `tags=["ui"]`-
  Marker).
- [x] **`make test-unit`** gruen: 1610 passed (+10 vs
  Welle-1-Endstand 1600).
- [x] **`make test-integration`** gruen: 43 passed + 4
  skipped (+2 vs Welle-1-Endstand 41).
- [x] **`make arch-check`** 20/20 KEPT (7 import-linter
  inkl. `jinja2`-Forbidden-Erweiterung + 13 arch_check).
- [x] **`make typecheck`** mit `strict_bytes` gruen
  (kein neuer `# type: ignore`-Marker; 141 source files
  +3 vs Welle-1-Endstand 138).
- [x] **`make gates`** cache-frei gruen ohne Override
  (10/10 A-1-Gates).
- [x] **`make docs-check`** cache-frei gruen.
- [x] **`make openapi-validate`** cache-frei gruen
  (`GG-API-003`; UI-Routes mit `tags=["ui"]`).
- [x] **`VENDORED.md`** produktiv unter `static/` mit
  HTMX 2.0.9 + Chart.js 4.5.1 + SHA256-Hashes +
  Upstream-URLs + MIT-Lizenz-Refs + Pflegeanleitung.
- [x] **`GG-UI-001`-Akzeptanz** (UI lokal erreichbar)
  erfuellt durch `test_full_ui_foundation_workflow`-
  Smoke-Test.
- [x] **C3-Top-Level-Doku-Sync** produktiv: 5 Docs auf
  Welle-2-Closure-Stand (`M5-welle-2.md §0/§9`,
  `M5-ui-demo.md §3 Welle 2`, `in-progress/README.md`,
  `in-progress/roadmap.md §3 M5`, `README.md` +
  `README.de.md`-Test-Counts).

**Anti-Scope-Verifikation (Welle 2 NICHT):**

- [x] Kein Live-Telemetry-Code (kein WS-Subscribe,
  kein Chart.js-Update; das ist Welle 3).
- [x] Kein Replay-Controls-UI (Welle 4).
- [x] Kein Scenario-Editor (Welle 5).
- [x] Kein Fault-Injection-UI (Welle 6).
- [x] Kein Demo-Compose-Service (Welle 5).
- [x] Kein Frontend-Build-Step (Vite/Webpack/etc.).
- [x] Keine `noqa`-Marker.

---

## References

- [`../done/M5-welle-1.md`](../done/M5-welle-1.md) — Welle-
  1-Closure (HTTP-API-Surface-Foundation, die Welle 2 als
  UI-Hülse aufschlägt).
- [`../done/M5-welle-0.md`](../done/M5-welle-0.md) §3
  Decision 2 (UI-Layout-Lokation; Welle 2 trifft die finale
  Wahl).
- [`M5-ui-demo.md`](../in-progress/M5-ui-demo.md) §3 Welle 2
  (kanonische Slice-Spezifikation).
- [`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md)
  §2.1 (Maintainer-Indication „FastAPI + HTMX + Jinja2 +
  Chart.js"; vendored Static-Asset-Pattern).
- [`../../adr/0037-http-api-surface-pattern.md`](../../adr/0037-http-api-surface-pattern.md)
  (HTTP-API-Surface, auf der die UI aufbaut).
- [`../../../../spec/lastenheft.md §17`](../../../../spec/lastenheft.md)
  (`GG-UI-001..009` Visualisierungs-Anforderungen).
- [`../../../../spec/architecture.md §4.2`](../../../../spec/architecture.md)
  (Driving-Port-Familie; UI als Driving-Adapter parallel
  zum HTTP-API).
- [`../../../../tools/arch_check.py`](../../../../tools/arch_check.py)
  `AC-ADAPTER-LIGHTWEIGHT` (Contract erfasst neue UI-
  Lokation ohne Filter-Erweiterung).
- Pattern-Praezedenz Welle-2-Foundation:
  [`../done/M4-welle-2.md`](../done/M4-welle-2.md)
  (MQTT-Adapter als erste konkrete Implementation nach
  M4-Welle-1-Foundation).
