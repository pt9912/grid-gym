# ADR 0036 — UI-Stack-Wahl (M5)

**Status:** Accepted — gezogen 2026-06-04 mit M5-Welle-7-
C1 (dieser Commit; M5-Closure-Welle). Provisional-Schritt
2026-06-01 mit M5-Welle-1-C1 nach Pre-C0c-HTMX-FastAPI-
Smoke-Probe-Run `9c20dad` (4 Probe-Tests in `tests/
integration/test_m5_welle_1_htmx_probe.py` validieren die
drei kritischen Composition-Punkte server-side:
FastAPI-HTML-Response, HTMX-`HX-Request`-Pattern,
WebSocket-Server-Push). Initial-Entwurf (`Proposed`)
2026-06-01 mit Pre-M5-Welle-0-Sondierung (`f4a9ced`) +
Charting-Library-Sub-Decision (`e0c3f66`). Die ADR fixiert
**Option 1** (FastAPI + HTMX + Jinja2 + Chart.js) als
M5-UI-Stack; die drei anderen Optionen (1b SvelteKit-SPA,
2 React-SPA, 3 Streamlit ausgeschlossen) bleiben als
dokumentierte Alternativen fuer M6-Migration falls
Stakeholder-Druck spaeter aufkommt. Welle 1..6c haben den
Stack produktiv-belegt: 9 HTTP-/WS-Endpunkte + 7 UI-Pages
+ 80 Integration-Smokes (Pattern analog ADR 0030..0035 in
M4-Welle-7-C1 `d2071f0`).

Status-Pfad: Proposed (2026-06-01 `f4a9ced` + Charting-Sub-
Decision `e0c3f66`) → Provisional (2026-06-01 M5-Welle-1-C1
nach Probe-Run-Validation) → **Accepted** (dieser Commit;
M5-Welle-7-Closure).
**Datum:** 2026-06-01 (Erstfassung) / 2026-06-01 (Provisional-Schaerfung, M5-Welle-1-C1)
**Bezug:**
[`ADR 0001`](0001-documentation-and-planning-structure.md)
(ADR-Pattern + Planning-Struktur);
[`ADR 0002`](0002-language-and-build-stack.md) §A-1 (10 A-1-
Gates inkl. NEU `spdx-check`; Multi-Stack-Bruch durch
ein Frontend-Build-Layer waere eine **Schaerfung-mit-
Erweiterung** dieses Vertrages);
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Pattern fuer
ADR-Erweiterungen ohne Supersedes; ADR 0036 nutzt das Pattern
zur Vorbereitung des M5-Welle-1-Decision-ADRs analog wie
ADR 0030 fuer M4);
[`ADR 0030`](0030-device-protocol-port-surface.md) §2.1
(Adapter-Hexagon-Pattern; UI ist `adapters/driving/`-Layer
analog HTTP-API);
[Lastenheft](../../../spec/lastenheft.md#17-visualisierung) §17 (`GG-UI-001..009`)
+ §24 (`GG-DEMO-001..008`);
[Architektur](../../../spec/architecture.md#5-komponentensicht) §5 (`GG-AR-COMP-UI`-
Slot in `ui/`).

M5-Slice-Plan
[`../planning/done/M4-results.md §5`](../planning/done/M4-results.md)
nennt **M5 (UI + Demo)** als naechsten aktiven Slice; die
Slice-Plan-Eroeffnung erfolgt mit M5-Welle-0. Diese ADR ist
**bewusst vor Welle 0 angelegt**, weil die UI-Stack-Wahl ein
**architektonisches Multi-Stack-Risiko** ist (Multi-Tool-
Buildchain, neue Gates, Lizenz-Boundary-Komplexitaet), das
Welle 0 (Slice-Plan-Eroeffnung) braucht als Entscheidungs-
Material — nicht erst Welle 1.

---

## 1. Kontext

### 1.1 Lastenheft-Pflicht

[`spec/lastenheft.md §17`](../../../spec/lastenheft.md#17-visualisierung) listet
**neun UI-Anforderungen** fuer M5:

| ID            | Verbindlichkeit | Inhalt                                                                          |
| ------------- | --------------- | ------------------------------------------------------------------------------- |
| `GG-UI-001`   | MUSS            | Web-UI lokal nach `docker compose up` erreichbar                                |
| `GG-UI-002`   | MUSS            | Live-Telemetry-Anzeige (Geraet/Metrik/Wert/Einheit/Sim-Zeit/Quality)            |
| `GG-UI-003`   | MUSS            | Zeitreihen-Charts (mind. 1 Leistungs- + 1 SOC-Metrik)                           |
| `GG-UI-004`   | MUSS            | Replay-Steuerung (Start/Pause/Resume/Stop + Status)                             |
| `GG-UI-005`   | MUSS            | Alarme-Tabelle (Zeit/Ziel/Severity/Code/Message/Status)                         |
| `GG-UI-006`   | SOLLTE          | Geraete-Grafik (mind. MVP-Geraetetypen)                                         |
| `GG-UI-007`   | SOLLTE          | Fault-Injection-Eingabe-Form (Typ/Ziel/Startzeit/Dauer/Recovery)                |
| `GG-UI-008`   | SOLLTE          | Simulationszustaende (Laufstatus/Sim-Zeit/Tick-Zaehler/Dienst-Zustand)          |
| `GG-UI-009`   | MUSS            | Datenqualitaet sichtbar (`stale/invalid/nan/missing/fault_injected`)            |

Plus [`§24 Demo-System`](../../../spec/lastenheft.md#24-demo-system) (`GG-DEMO-
001..008`) als MUSS: lokale Demo-Umgebung nach
`docker compose up`-Start, Live-Telemetry binnen 30s,
mindestens 1 Replay-Szenario, dokumentierte Abnahmereihenfolge.

### 1.2 Existierende Substanz im Repo

Stand 2026-06-01 (M4-Closure):

- **FastAPI** `>=0.136` + **uvicorn[standard]** `>=0.47` in
  `[project] dependencies` seit M1-Welle-7.
- [`src/grid_gym/adapters/driving/http_api/app.py`](../../../src/grid_gym/adapters/driving/http_api/app.py)
  exportiert `app` mit `/health` + `POST /runs`-Stub.
- **`httpx >=0.27`** als Test-Client.
- **`make openapi-validate`**-Dockerfile-Stage validiert
  `app.openapi()` gegen `openapi-spec-validator` (M1).
- [`deploy/compose.yml`](../../../deploy/compose.yml) als
  produktiver Compose-File mit `otel-collector`-Sibling
  und Sibling-Services aus M2..M4.
- **`GG-AR-COMP-UI`-Slot** in
  [`spec/architecture.md §5`](../../../spec/architecture.md#5-komponentensicht) auf
  `ui/`-Top-Level-Verzeichnis vorbelegt; das Verzeichnis
  existiert **noch nicht**.

### 1.3 Architektur-Constraints aus M1..M4-Closure

- **Hexagonale Architektur:** UI lebt in `adapters/driving/`-
  Layer (siehe `GG-AR-PORT-DRG-002` Vorbelegung). Kein
  direkter Kern-Zugriff; UI nutzt **nur**
  `GG-API-001`/`002`/`003` (siehe Roadmap §3 M5-DoD).
- **10 A-1-Gates** (`make gates`) als harte CI-Pflicht
  ([`ADR 0002`](0002-language-and-build-stack.md) §A-1 +
  M4-Welle-6b-`spdx-check`-Erweiterung).
- **`make arch_check` 20 Contracts** als Architektur-
  Disziplin-Backbone (`mypy --strict`, `arch_check.py` mit
  14 Contracts inkl. `AC-ADAPTER-LIGHTWEIGHT` +
  `AC-IEC61850-GPL-BOUNDARY`).
- **User-Memory `feedback_docker_only`:** alle Builds/Tests/
  Gates ueber Dockerfile-Stages via `make`; keine lokale
  Python-/Tool-Installation.
- **Lizenz-MIT-Reinheit** als Default (nur
  `protocol_iec61850/*` ist GPL-3.0-only-Boundary, siehe
  [`ADR 0035`](0035-iec61850-adapter-profile.md) §I-f).

### 1.4 Sondierungs-Kontext

Diese ADR ist das Ergebnis einer Pre-M5-Welle-0-Sondierung
zwischen dem grid-gym-Maintainer und einem AI-Coding-Agent
(2026-06-01). Drei sinnvolle Optionen wurden identifiziert
und gegeneinander abgewogen; eine vierte Option (Streamlit/
Plotly Dash) wurde sondiert und als **untauglich** ausgewaehlt
(siehe §4.4 unten).

---

## 2. Entscheidung

**Diese ADR ist im Status `Proposed` mit Maintainer-
Decision-Indication 2026-06-01** (siehe Block direkt
unter §2-Header). Sie
listet drei realistische UI-Stack-Optionen plus eine
ausgeschlossene vierte Option, inklusive Trade-off-
Analyse, Welle-Plan-Impact und Sub-Decisions (Charting-
Library). Die finale Decision-Festschreibung erfolgt **in
M5-Welle-1-ADR-Schaerfung** auf `Provisional` (Pattern
analog ADR 0030 → 0035 — `Provisional` nach C2-Merge mit
Code-Beleg, `Accepted` mit M5-Welle-7-Closure).

**Maintainer-Decision-Indication 2026-06-01 (vor M5-Welle-
0-Eroeffnung):**

- **UI-Stack:** Option 1 (FastAPI + HTMX + Jinja2).
- **Charting-Library:** Chart.js (Default-Sub-Wahl gemaess
  §2.5-Empfehlungs-Matrix fuer Option-1-Stack).

Begruendung (zusammengefasst aus Sondierungs-Gespraech
2026-06-01): Architektur-Reinheit + Single-Stack-Python +
10 statt 15 A-1-Gates + Welle-Tempo + `feedback_docker_
only`-Treue priorisiert ueber UX-Glanz. Migrationspfad zu
Option 1b oder Charting-Upgrade auf Plotly.js/ECharts
bleibt in M5-Welle-6 offen falls Stakeholder-Druck
spaeter aufkommt (siehe §2.5-Welle-Plan-Impact-Tabelle).
Vollstaendige Decision-Festschreibung erfolgt in M5-Welle-
1 mit Probe-Run-Beleg (Pattern analog ADR 0030 §2.1
„Welle 4 traegt die Konstruktion zuerst real").

### 2.1 Option 1 — FastAPI + HTMX + Jinja2 + Chart.js

Server-Side-Rendered UI mit Hypertext-driven Interactions
(HTMX-Pattern): FastAPI rendert HTML-Templates (Jinja2);
HTMX-Attribute auf HTML-Elementen triggern Server-Calls fuer
Partials. Live-Telemetry via WebSocket (FastAPI `@app.
websocket`) mit HTMX-WS-Plugin oder via Server-Sent-Events
(SSE). Charts via Chart.js (vendored, ~70 KB Static-Asset
ohne CDN-Abhaengigkeit).

**Lizenzen:** HTMX BSD-2-Clause; Jinja2 BSD-3-Clause;
Chart.js MIT. Alle MIT-kompatibel.

**Repo-Impact:**

- NEU `ui/`-Verzeichnis als `adapters/driving/ui/`-Sub-Layer
  (oder `ui/`-Top-Level analog Lastenheft-§17-Vorbelegung;
  Welle-2-Entscheidung).
- **Keine** neuen Build-Tools — `uv` + `make` bleiben Single-
  Source-of-Truth.
- **Keine** zusaetzlichen `make gates`-Stages — die 10 A-1-
  Gates decken den Python-Code-Pfad **vollstaendig** ab.
- `arch_check`-Pattern reproduzierbar (UI-Code unter
  `adapters/driving/ui/` mit `AC-ADAPTER-LIGHTWEIGHT`-
  Komplexitaets-Gate, falls Welle-6b-Slice-034-F13-Erweiterung
  greift).

**Welle-Plan-Impact:** ~6 Wellen analog M3/M4-Pattern (Welle
0 Slice-Plan + Welle 1 HTTP-API-Surface + Welle 2 UI-
Foundation + Welle 3 Live-Telemetry + Welle 4 Replay-
Controls/Alarme + Welle 5 Demo-Pipeline + Welle 6 SOLLTE-
Features + Welle 7 Closure).

### 2.2 Option 1b — FastAPI-Backend + SvelteKit-SPA-Frontend

SvelteKit `@sveltejs/kit 2.61.1` mit `@sveltejs/adapter-
static 3.0.10` (SPA-Mode mit Fallback-HTML): Vite + Svelte +
TypeScript bauen eine SPA, die FastAPI als statischen Asset
serviert (`app.mount("/", StaticFiles(directory="ui/dist",
html=True))`). Live-Telemetry via Browser-`WebSocket`-Client
+ Svelte-Stores fuer Reaktivitaet. **Wichtig:** Nicht
SvelteKit-SSR-Mode (separate Node-Production-Runtime) und
nicht reiner Static-Adapter ohne Fallback — der SPA-Mode mit
Fallback ist der einzige sinnvolle Sub-Mode fuer grid-gym.

**Lizenzen:** SvelteKit MIT; Vite MIT; TypeScript Apache-2.0;
Svelte MIT. Alle MIT-kompatibel.

**Repo-Impact:**

- NEU `ui/`-Verzeichnis mit `package.json`/`package-lock.
  json`/`vite.config.ts`/`svelte.config.js`/`tsconfig.json`/
  `src/`/etc. (typisches SvelteKit-Project-Layout).
- **NEU Multi-Stage-Dockerfile** mit `ui-build`-Stage auf
  `node:20-bookworm-slim`-Basis (~300 MB Build-Layer; nicht in
  Production-Image). Production-Image wird um ~1 MB groesser
  (statische Assets).
- **NEU 5 `make gates`-Stages:** `ui-lint` (eslint + prettier),
  `ui-typecheck` (`tsc --noEmit`), `ui-test` (vitest mit
  Coverage), `ui-coverage-gate` (analog 90/85% fuer TS), `ui-
  dep-audit` (`npm audit --omit=dev`). Plus optional `ui-
  bundle-size-gate` und `ui-openapi-types-gate`. **Effektiv:**
  `make gates` waechst von **10 auf 15 (+5 oder mehr)**.
- **arch_check-Disziplin-Luecke:** TypeScript hat **kein**
  `arch_check.py`-Aequivalent. `tsc --strict` ist Best-Effort;
  `eslint-plugin-sonarjs` deckt Cyclomatic-Limit aehnlich,
  aber nicht identisch. `AC-ADAPTER-LIGHTWEIGHT`-Aequivalent
  in TS fehlt.
- **OpenAPI-Codegen-Pipeline** notwendig: FastAPI `app.
  openapi()` → `openapi-typescript`-Codegen → `ui/src/lib/
  api-types.ts`. Plus `ui-openapi-types-gate`, der prueft,
  dass die generierten Types nicht driften
  (`git diff --exit-code` nach Re-Generation).

**Welle-Plan-Impact:** ~7-8 Wellen — extra Welle fuer
Frontend-Build-Pipeline-Setup + Gates-Integration (Welle 2
wird zur reinen Infrastruktur-Welle; Welle 3 ist erstes
sichtbares UI).

### 2.3 Option 2 — FastAPI-Backend + React-SPA-Frontend

React 18.x + Vite-Build (oder Create-React-App, aktuell als
deprecated markiert) als Standard-SPA-Architektur. Aehnlich
zu Option 1b, aber mit klassischem React-Stack statt
Svelte-Compile-time-Framework.

**Lizenzen:** React MIT; Vite MIT; TypeScript Apache-2.0.
Alle MIT-kompatibel.

**Repo-Impact:** Analog zu Option 1b (Multi-Stack-Bruch),
aber:

- **Bundle-Size groesser** als SvelteKit (React-Runtime ~140
  KB minified vs Svelte-Compile-Output ~10-30 KB pro Page).
- **npm-Trans-Deps-Tree groesser** (typisch 300-500 Pakete
  fuer ein modernes React-SPA-Setup vs 150-250 fuer
  SvelteKit).
- **TypeScript-Disziplin-Aequivalent zu mypy --strict**
  konfigurierbar, aber nicht so streng wie SvelteKit-
  Defaults (React-Ecosystem ist toleranter gegenueber
  `any`-Types).

**Welle-Plan-Impact:** Wie Option 1b (~7-8 Wellen).

### 2.4 Option 3 (ausgeschlossen) — Streamlit / Plotly Dash

Python-only UI-Framework (Streamlit oder Plotly Dash). Wurde
als pragmatischer Mittelweg sondiert, aber als untauglich
ausgewaehlt aus folgenden Gruenden:

1. **Eigener Server-Lifecycle:** Streamlit hat einen eigenen
   `streamlit run`-Process (nicht ASGI/WSGI-kompatibel) und
   laeuft NEBEN FastAPI als zweiter Compose-Service. Dash
   nutzt einen integrierten Flask-Server.
2. **State-Management nicht deterministisch:** Streamlit's
   Session-State-basiertes Modell bricht das deterministic-
   Sim-Steuerungs-Pattern (Re-Run pro Klick, fragile Forms-
   Submit-Logik).
3. **WebSocket-Pfad ungeloest:** Streamlit hat **keinen
   direkten `@app.websocket`-Support** fuer Live-Telemetry;
   externe Komponenten (z. B. `streamlit-autorefresh`) sind
   Polling-basiert und brechen das Live-Telemetry-Pattern
   aus `GG-API-002`.
4. **Replay-Controls fragil:** Forms-Submit-Mechanismus in
   Streamlit triggert Re-Run der gesamten Seite; nicht
   kompatibel mit dem `start_run/pause_run/resume_run`-
   Idiom aus `GG-UI-004`.

Diese Option ist **bewusst nicht** als Empfehlung in §2.1-§2.3
gefuehrt.

### 2.5 Charting-Library-Sub-Decision (orthogonal zur Stack-Wahl)

Drei realistische Charting-Libraries fuer
`GG-UI-002/003/009` (Live-Telemetry + Zeitreihen + Quality-
Status). Diese Sub-Decision ist **orthogonal zur Stack-Wahl
in §2.1/2.2/2.3** — jede der UI-Stack-Optionen kann mit
jeder der drei Charting-Libraries kombiniert werden. Final-
Decision-Schritt: **M5-Welle-3-Slice-Doc** (Live-Telemetry-
Dashboard) verankert die konkrete Wahl als Implementations-
Detail; ADR 0036 listet hier die drei Optionen + Trade-offs.

#### Option Chart.js (Default in §2.1)

| Aspekt              | Wert                                  |
| ------------------- | ------------------------------------- |
| Lizenz              | MIT                                   |
| Bundle-Size         | **~70 KB** minified                   |
| Rendering           | Canvas                                |
| Time-Series-Support | OK (line/area/scatter)                |
| Live-Streaming      | Native `update()`-API; ~30 FPS OK     |
| Multi-Axis          | Ja                                    |
| Zoom/Pan            | Plugin (`chartjs-plugin-zoom` ~10 KB) |
| Scientific-Grade    | **Mittel** — keine echte time-Axis    |

**Passt zu:** Option 1 (HTMX) als Single-File-Vendoring
trivial; passt zur Single-Stack-Philosophie.

#### Option Plotly.js

| Aspekt              | Wert                                                                  |
| ------------------- | --------------------------------------------------------------------- |
| Lizenz              | MIT                                                                   |
| Bundle-Size         | **~3 MB** (Full) / **~1.5 MB** (Basic) / **~250 KB** (`plotly.js-strict`) |
| Rendering           | SVG + WebGL (fuer grosse Datasets)                                    |
| Time-Series-Support | **Excellent** (native `datetime`-Axis)                                |
| Live-Streaming      | `Plotly.extendTraces()` fuer Append; `Plotly.animate()` smooth        |
| Multi-Axis          | Ja, native; auch 3D + Maps                                            |
| Zoom/Pan            | Eingebaut                                                             |
| Scientific-Grade    | **Hoch** — Error-Bars, Statistical-Plots, Export-PNG/SVG eingebaut    |

**Passt zu:** Option 1b (SvelteKit-SPA) als
tree-shaking-faehiges npm-Modul; oder Option 1 (HTMX) mit
`plotly.js-strict`-Sub-Bundle (~250 KB) falls Maintainer
scientific-Replay-Reports priorisiert.

#### Option Apache ECharts

| Aspekt              | Wert                                              |
| ------------------- | ------------------------------------------------- |
| Lizenz              | **Apache-2.0** (nicht MIT, aber kompatibel)       |
| Bundle-Size         | **~1 MB** (Full) / **~300 KB** (tree-shaken Subset) |
| Rendering           | Canvas + SVG (waehlbar)                           |
| Time-Series-Support | **Excellent** (native `time`-Axis)                |
| Live-Streaming      | `setOption({...})` Dynamic-Data; auf grosse Datasets ausgelegt |
| Multi-Axis          | Ja, Dashboard-fokussiert                          |
| Zoom/Pan            | Eingebaut (`dataZoom`-Komponente)                 |
| Scientific-Grade    | **Hoch** — gut fuer Dashboards, weniger fuer scientific notation |

**Passt zu:** Option 1b (SvelteKit-SPA) als
tree-shaking-faehiges npm-Modul mit besserer Live-
Streaming-Performance bei grossen Datasets (Canvas-Render
vs Plotly-SVG).

#### Trade-off-Matrix Charting-Libraries

| Kriterium fuer grid-gym                | Chart.js                | Plotly.js                          | ECharts                          |
| -------------------------------------- | ----------------------- | ---------------------------------- | -------------------------------- |
| Bundle-Size Production                 | **~70 KB ✅**           | 250 KB-3 MB ⚠️                     | 300 KB-1 MB ⚠️                   |
| Lizenz                                 | MIT ✅                  | MIT ✅                             | Apache-2.0 (kompatibel)          |
| Time-Series-Qualitaet                  | OK                      | **Excellent**                      | **Excellent**                    |
| Live-Streaming-Performance             | OK (~30 FPS)            | Mittel (SVG-lag bei 1000+ Points)  | **Gut** (Canvas-Render)          |
| Replay-Diagramme (Audit-Trail-Export)  | OK                      | **Excellent** (PNG/SVG nativ)      | **Gut**                          |
| Quality-Marker (`stale/nan/fault`)     | Custom Point-Style      | Native `marker.color`-Array        | Native Symbol-Mapping            |
| Multi-Metric-Dashboard                 | OK                      | **Excellent**                      | **Excellent** (Dashboard-DNA)    |
| Lernkurve                              | **Leicht**              | Mittel (grosse API-Surface)        | Mittel (Config-Object-getrieben) |
| Build-Pipeline-Impact                  | Vendoring trivial       | Tree-shaking noetig                | Tree-shaking noetig              |

#### Empfehlungs-Matrix pro UI-Stack-Option

| UI-Stack (§2.1/2.2) | **Chart.js** | **Plotly.js (strict)** | **ECharts** |
| ------------------- | ------------ | ---------------------- | ----------- |
| Option 1 (HTMX)     | **Empfohlen** — Single-File-Vendoring; passt zur Single-Stack-Philosophie; +70 KB | Moeglich (mit `plotly.js-strict ~250 KB`); falls scientific Replay-Reports Prioritaet sind | Weniger geeignet (Apache-2.0 nicht MIT; +300 KB als Static-Asset ohne Tree-Shaking-Build-Pipeline aufwendiger) |
| Option 1b (SvelteKit-SPA) | Moeglich (kein Vorteil aus SPA-Setup); +70 KB im Bundle | **Empfohlen** falls scientific-Grade gefragt — Tree-shaking via Vite reduziert auf ~250 KB | **Empfohlen** falls Dashboard-Look gefragt — Tree-shaking auf ~300 KB; Canvas-Performance bei grossen Datasets besser als Plotly |

#### Per-Welle-Plan-Impact

- **Welle 1 (HTTP-API-Surface):** unverändert; Charting-
  Library ist UI-spezifisch.
- **Welle 3 (Live-Telemetry-Dashboard):** Charting-Library-
  Wahl wird hier final festgelegt im Welle-3-Slice-Doc.
  Pattern analog M4-Welle-2-MQTT-Library-Wahl (`paho-mqtt
  2.x`) im Welle-2-Slice-Doc + ADR-Body.
- **Welle 6 (SOLLTE-Features [`GG-UI-006`](../../../spec/lastenheft.md#gg-ui-006)/007/008):** falls
  Welle 3 mit Chart.js startet, kann hier ein Upgrade auf
  Plotly.js/ECharts erwogen werden, falls UX-Druck steigt.
  Migration ist nicht trivial (Config-Modelle unterschied-
  lich), aber Welle-Sub-Slicing kann das auffangen.

---

## 3. Konsequenzen

### 3.1 Konsequenzen bei Wahl Option 1 (HTMX)

**Positiv:**

- **Architektur-Reinheit:** Single-Stack-Python; `make gates`
  + `arch_check.py` + `mypy --strict` decken **100 % des
  Code-Pfads** ab.
- **Welle-Tempo:** ~6 Wellen, kein Setup-Welle-Overhead.
- **Lizenz-MIT-Reinheit:** alle Deps MIT/BSD; kein npm-Trans-
  Deps-Audit-Risiko.
- **User-Memory `feedback_docker_only`-Treue:** Single-Tool
  (`uv`) reicht; kein `npm` zusaetzlich.
- **Determinismus:** Server-Side-Rendering eliminiert Client-
  State-Drift.

**Negativ:**

- **UX-Glanz:** "Server-driven UI fuehlt sich behaebig an" —
  weniger reactive als Svelte/React-SPAs.
- **Replay-Forms-Validation server-side:** bei komplexen
  Forms (z. B. Fault-Injection §[`GG-UI-007`](../../../spec/lastenheft.md#gg-ui-007) mit nested
  Konfiguration) sperriger als client-side-validation.
- **Lernkurve fuer Devs, die nur React/Vue kennen:** HTMX
  hat ein eigenes Mental-Model.

**Neutral:**

- Chart.js + WS-Push-Pattern fuer Sub-Sekunde-Updates ist
  weniger erprobt — Probe-Run in M5-Welle-1-Probe noetig.

### 3.2 Konsequenzen bei Wahl Option 1b (SvelteKit-SPA)

**Positiv:**

- **UX-Glanz:** Reactive Charts mit Svelte-Stores; "modernes
  Demo-Look-and-Feel" fuer Stakeholder-Show-Cases.
- **TypeScript first-class:** bessere statische Sicherheit
  fuer komplexe Forms (z. B. Fault-Injection).
- **Compile-time-Output klein:** ~10-30 KB pro Page (vs ~140
  KB React-Runtime).
- **Modulares Component-Pattern:** Geraete-Grafik (`GG-UI-
  006`) ist mit Svelte-Components einfacher als mit HTMX-
  Partials.

**Negativ:**

- **Multi-Stack-Bruch:** Node.js + npm/pnpm + Vite/TS als
  zweite Build-Toolchain neben `uv`. Multi-Stage-Dockerfile-
  Komplexitaet.
- **`make gates`-Inflation:** 10 → 15 Stages. Reviewer-
  Aufwand pro PR steigt.
- **`arch_check`-Disziplin-Luecke** in `ui/` — TypeScript
  hat kein direktes Aequivalent.
- **Welle-Anzahl** +1-2 Wellen fuer Frontend-Setup.
- **OpenAPI-Codegen-Drift-Risiko** als zusaetzliche
  Pipeline-Disziplin.
- **`npm audit`-Disziplin-Druck:** Trans-Deps-Tree waechst
  schleichend.

**Neutral:**

- Lizenz-Audit ist **niedriger als befuehrt** wenn strikt
  `--omit=dev` gefahren wird (Svelte ist Compile-time → 0
  Runtime-Deps in Production).

### 3.3 Konsequenzen bei Wahl Option 2 (React-SPA)

**Positiv:** Industry-Standard, groesste Community, viele
UI-Komponenten-Libraries verfuegbar.

**Negativ:** Alle Cons aus Option 1b plus:

- **Bundle-Size groesser** (React-Runtime ~140 KB).
- **npm-Trans-Deps-Tree groesser** (~300-500 Pakete).
- **TypeScript-Disziplin schwacher** als SvelteKit-Defaults.

→ **Option 2 ist gegenueber Option 1b strikt schlechter** in
allen messbaren Aspekten (Bundle, Deps, Disziplin-Aequivalent)
ohne klare Pros, die ueber Option 1b hinausgehen. Sie ist
nur fuer Maintainer relevant, die explizit React-Expertise
mitbringen und kein Svelte lernen wollen.

---

## 4. Trade-off-Analyse-Matrix

| Aspekt                                          | Option 1 (HTMX) | Option 1b (SvelteKit-SPA) | Option 2 (React-SPA) |
| ----------------------------------------------- | --------------- | ------------------------- | -------------------- |
| Single-Stack-Python                             | ✅ Ja           | ❌ Nein (Node + Build)    | ❌ Nein              |
| `make gates`-Anzahl                             | **10**          | 15+                       | 15+                  |
| `arch_check`-Coverage                           | **100 %**       | ~50 % (TS hat keine Entsprechung) | ~50 %         |
| `mypy --strict`-Aequivalent                     | **N/A**         | `tsc --strict`            | `tsc --strict`       |
| Welle-Anzahl                                    | **~6**          | ~7-8                      | ~7-8                 |
| npm-Trans-Deps                                  | **0**           | ~150-250 (dev)            | ~300-500 (dev)       |
| Bundle-Size (Production)                        | ~70 KB (Chart.js) | **~30-100 KB**         | ~140-300 KB          |
| Lizenz-Audit-Komplexitaet                       | **`pip-audit` reicht** | + `npm audit`        | + `npm audit`        |
| `feedback_docker_only`-Treue                    | **Direkt**      | Multi-Tool-Dockerfile     | Multi-Tool           |
| UX fuer Live-Charts                             | OK (Chart.js + WS) | **Besser** (Reactive)  | **Besser** (Reactive)|
| Forms-Validation (Fault-Inj)                    | Server-side     | **Client + Server**       | **Client + Server**  |
| TypeScript first-class                          | Nein            | ✅ Ja                     | ✅ Ja                |
| "Modern Demo-Look"                              | OK              | ✅ Ja                     | ✅ Ja                |
| Dev-Onboarding-Aufwand                          | HTMX-Lernkurve  | TS+Svelte                 | TS+React             |
| Reactive-Charts Sub-Sek-Updates                 | WS-Push-Pattern | **Native Stores**         | **State-Mgmt-Lib**   |

**Punkte-Zaehlung (subjektiv, fuer Vergleichbarkeit):**

- **Option 1 (HTMX):** 11 Pro + 4 Con (Architektur-Reinheit
  +5 Pro-Wertung).
- **Option 1b (SvelteKit-SPA):** 8 Pro + 7 Con (UX-Glanz
  +3 Pro-Wertung).
- **Option 2 (React-SPA):** 6 Pro + 9 Con (strikt schlechter
  als 1b in allen Aspekten ausser Industry-Standard).

---

## 5. Status-Pfad

- **Proposed** — 2026-06-01 (`f4a9ced` Pre-M5-Welle-0-
  Sondierungs-ADR + `e0c3f66` Charting-Library-Sub-
  Decision §2.5). Decision-Material vollstaendig mit
  Maintainer-Decision-Indication „Option 1 (HTMX +
  Chart.js)".
- **Provisional** — 2026-06-01 (M5-Welle-1-C1, dieser
  Commit) nach Pre-C0c-HTMX-FastAPI-Smoke-Probe-Run
  `9c20dad` (Probe-Tests validierten Server-Side die drei
  kritischen Composition-Punkte: FastAPI HTML-Response,
  HTMX `HX-Request`-Pattern, WebSocket Server-Push).
  **Option 1 (FastAPI + HTMX + Jinja2 + Chart.js)
  fixiert**; Optionen 1b/2/3 bleiben als dokumentierte
  Alternativen fuer Welle-6+/M6-Migration. Pattern analog
  [`ADR 0030`](0030-device-protocol-port-surface.md)
  (M4-Welle-1-Proposed-zu-Provisional nach C2-Code-Merge;
  hier nach Pre-C0c-Probe-Run statt nach Welle-1-C2-Merge
  weil die Stack-Validation **vor** der C0-Slice-Doc-
  Anlage erfolgt ist).
- **Accepted** — geplant mit M5-Welle-7-Closure (analog
  ADR 0030..0035, alle in M4-Welle-7-C1 `d2071f0` auf
  `Accepted` gezogen).

---

## 6. Empfehlung an M5-Welle-1

**Diese ADR enthaelt keine verbindliche Empfehlung**, sondern
zwei klare Aussagen:

1. **Option 2 (React-SPA) ist gegenueber Option 1b
   (SvelteKit-SPA) strikt unterlegen** und sollte nur
   gewaehlt werden, wenn Maintainer-Skill explizit React-
   only ist.
2. **Option 3 (Streamlit/Dash) ist untauglich** und sollte
   nicht in M5-Welle-1-Probe einbezogen werden.

Die Entscheidung zwischen **Option 1 (HTMX)** und **Option
1b (SvelteKit-SPA)** ist ein **bewusster Architektur-
Tradeoff** zwischen:

- **Reinheit + Tempo + Disziplin** (Option 1)
- **UX-Glanz + Stakeholder-Anspruch + 1-2 zusaetzliche Wellen
  + 5 zusaetzliche Gates** (Option 1b)

Der grid-gym-Maintainer entscheidet das in M5-Welle-1 nach
folgendem Kriterium:

- **Wenn grid-gym primaer Validierungs-/Testplattform ist
  (interne Devs/Researchers):** Option 1 (HTMX).
- **Wenn grid-gym auch Show-Case fuer Stakeholder/Marketing
  ist:** Option 1b (SvelteKit-SPA).
- **Bei Unsicherheit:** Option 1 (HTMX) zuerst — Migration
  HTMX → SvelteKit-SPA ist machbar, wenn UX-Druck spaeter
  steigt (Templates-zu-Components-Refactor; nicht trivial,
  aber realistisch). Migration SvelteKit-SPA → HTMX waere
  praktisch nie sinnvoll (Architektur-Vereinfachung wird
  selten gemacht).

---

## 7. Folge-Pflichten

- **M5-Welle-0** (Slice-Plan-Eroeffnung): Diese ADR in
  Decision-Liste §3 als „Decision 1 (UI-Stack-Wahl)" mit
  **Maintainer-Decision-Indication „Option 1 + Chart.js"**
  (siehe §2-Header) vermerken; M5-Welle-1 als Decision-
  Welle markieren.
- **M5-Welle-1** (UI-Stack-Decision-Festschreibung + HTTP-
  API-Surface):
  - ADR-Schaerfung auf `Provisional` mit Choice-
    Festlegung (Maintainer-Indication validiert oder
    revidiert nach Probe-Run).
  - Welle 1 enthaelt die HTTP-API-Surface-Erweiterung
    (`GG-API-001/002` Endpoint-Vervollstaendigung +
    WebSocket-Route fuer Live-Telemetry). UI-Foundation
    (Jinja2-Templates + `adapters/driving/ui/`-Layout +
    Chart.js-Vendoring) folgt in Welle 2.
  - **Frueher Plan-Entwurf (Option 1b SvelteKit-SPA)
    ist NICHT mehr Welle-1-Material** — diese Pfade
    sind durch die Maintainer-Indication ausgeklammert,
    bleiben aber als dokumentierte Fallback-Optionen
    in §2.2 + §2.3 fuer Welle-6+/M6-Migration falls
    spaeter Stakeholder-Druck steigt.
- **M5-Welle-3** (Live-Telemetry-Dashboard): Charting-
  Library-Sub-Decision in Welle-3-Slice-Doc verankern
  (Maintainer-Indication: **Chart.js**; Welle 3 entscheidet
  endgueltig im Slice-Doc-Body und Welle 3 C2 traegt es
  produktiv).
- **M5-Welle-7-Closure:** ADR 0036 auf `Accepted` gezogen
  (analog ADR 0030..0035 in M4-Welle-7-C1 `d2071f0`).

---

## 8. References

- [`ADR 0030`](0030-device-protocol-port-surface.md) — Pattern
  fuer Vor-Welle-1-Sondierungs-ADR; ADR 0036 nutzt das
  gleiche Lifecycle-Pattern (`Proposed → Provisional →
  Accepted`).
- [`ADR 0035 §I-f`](0035-iec61850-adapter-profile.md) — GPL-
  Boundary-Pattern; relevant **falls** SvelteKit-Option
  spaeter eine GPL-lizenzierte Komponente in `ui/`
  einfuehrt (aktuell **keine** GPL-Komponente in der
  Sondierung).
- [Lastenheft §17](../../../spec/lastenheft.md#17-visualisierung) +
  [§24](../../../spec/lastenheft.md#24-demo-system) — UI-Pflicht + Demo-System.
- [Architektur §5 + §8.2](../../../spec/architecture.md#5-komponentensicht) —
  `GG-AR-COMP-UI`-Slot + Adapter-Hexagon-Pattern.
- [`../planning/done/M4-results.md §5`](../planning/done/M4-results.md)
  — M4-Welle-7-Erbschaft: M5 als naechster aktiver Slice;
  Trigger 009 + Base-Image-Bump als M5-Welle-0-Folge-Pflichten.
- **Sondierungs-Gespraech 2026-06-01** zwischen Maintainer
  und AI-Coding-Agent. Drei Optionen + ausgeschlossene
  vierte Option (Streamlit/Dash) als Konversations-
  Resultat.
