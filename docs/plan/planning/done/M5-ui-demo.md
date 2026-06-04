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

- [`roadmap.md`](../in-progress/roadmap.md) §3 M5 (Lieferziel, DoD-
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

### 3.1 Welle-Status-Tabelle

Quick-Glance ueber alle 8 M5-Wellen. Substanz-Detail
(Liefer-Hash-Stack, DoD-Checkboxen, C2-Realization-Notes,
Review-Findings, Test-Counts am Closure-Hash) lebt im
jeweiligen Welle-Slice-Doc unter `done/` bzw.
`in-progress/`.

| # | Titel | Status | Slice-Doc | Lastenheft-Coverage | ADRs |
| - | ----- | ------ | --------- | ------------------- | ---- |
| 0 | Slice-Plan-Eroeffnung + Trigger-Triage | Done 2026-06-01 | [`M5-welle-0.md`](../done/M5-welle-0.md) | Plan-Welle (10 Decisions vorbelegt) | ADR 0036 `Proposed` |
| 1 | HTTP-API-Surface | Done 2026-06-01 | [`M5-welle-1.md`](../done/M5-welle-1.md) | `GG-API-001..004` | ADRs 0036 + 0037 `Provisional` |
| 2 | UI-Foundation | Done 2026-06-01 | [`M5-welle-2.md`](../done/M5-welle-2.md) | UI-Foundation (Layout + Templates + HTMX/Chart.js) | — (C1 entfaellt) |
| 3 | Live-Telemetry-Dashboard | Done 2026-06-01 | [`M5-welle-3.md`](../done/M5-welle-3.md) | `GG-UI-001/002/003/009 + GG-API-002` | ADR 0038 `Provisional` |
| 4a | Replay-Controls + TickLoop-Wiring | Done 2026-06-02 | [`M5-welle-4a.md`](../done/M5-welle-4a.md) | `GG-UI-004` + Rest-`GG-API-001` | ADR 0039 `Provisional` |
| 4b | Alarme | Done 2026-06-02 | [`M5-welle-4b.md`](../done/M5-welle-4b.md) | `GG-UI-005`; loest ADR-0014-§6 Driving-Side | ADR 0040 `Provisional` |
| 5 | Demo-Pipeline + Scenario-Loader-Wiring | Done 2026-06-03 | [`M5-welle-5.md`](../done/M5-welle-5.md) (Self-Close-Move in C4a) | `GG-DEMO-001..005 + 007` (Anti: 006 + 008 → Welle 6) | — (C1 entfaellt) |
| 6a | Fault-Flow (UI-Form-Validation + YAML-Fault-Demo) | Done 2026-06-03 | [`M5-welle-6a.md`](../done/M5-welle-6a.md) (Self-Close-Move in C4a) | `GG-UI-007` + `GG-DEMO-006` | — (C1 entfaellt) |
| 6b | UI-Visualization (Geraete-Grafik + Sim-Zustand-Dashboard) | Done 2026-06-04 | [`M5-welle-6b.md`](../done/M5-welle-6b.md) (Self-Close-Move in C4a) | `GG-UI-006` + `GG-UI-008` | — (C1 entfaellt) |
| 6c | Abnahmedoku (Welle-5-Defer-Aufloesung) | Done 2026-06-04 | [`M5-welle-6c.md`](../done/M5-welle-6c.md) (Self-Close-Move in C4a) | `GG-DEMO-008` | — (C1 entfaellt) |
| 7 | M5-Closure | In Progress 2026-06-04 | [`M5-welle-7.md`](M5-welle-7.md) | M5-Closure (`done/M5-results.md` + S-1..S-6) | alle M5-ADRs → `Accepted` |

**Welle-4-Subdivision-Hinweis:** Die urspruenglich
monolithische Welle 4 wurde am M5-Welle-4a-C0-Pre-
Research-Zeitpunkt 2026-06-02 in zwei Sub-Slices
unterteilt, weil sich zwei distinkte Architektur-
Concerns mit eigenem ADR + Decisions-Slot
herauskristallisiert haben (Pattern analog M4-Welle-
5a/5b und M4-Welle-6a/6b). Welle 4a (RunStatus +
TickLoop-Control-Surface + Replay-Controls-UI) und
Welle 4b (Alarm-Aggregation + AlarmStreamPort + Alarm-
Tabelle-UI) liefern zusammen `GG-UI-004` + `GG-UI-005`.
Detail im jeweiligen Welle-Slice-Doc unter `done/`.

**Aktive Welle:** Welle 7 (M5-Closure). **Welle-6-
Subdivision komplett abgeschlossen 2026-06-04**: 6a
(`Done 2026-06-03`) + 6b (`Done 2026-06-04`) + 6c
(`Done 2026-06-04`). Welle 6c hat per
[`M5-welle-6c.md`](../done/M5-welle-6c.md) (C0 `3db9fcd` + C2
`0e604e4` + C3 dieser Commit) die Welle-5-Anti-Scope-
Erbschaft `GG-DEMO-008` aufgeloest — Abnahmedoku
[`../../../user/gg-demo-008-abnahme.md`](../../../user/gg-demo-008-abnahme.md)
lebt unter `docs/user/`. Welle-7-Slice-Doc entsteht in
Welle-7-C0.
Welle 6 ist per Welle-6a-C0-Sub-Slicing-Beschluss
2026-06-03 in drei Sub-Slices unterteilt (6a Fault-Flow
**Done 2026-06-03** + 6b UI-Visualization **Done
2026-06-04** + 6c Abnahmedoku Pending); pro Sub-Slice
eigener Slice-Doc. Pattern analog M4-Welle-6 → 6a/6b.

### 3.2 Pending-Wellen-Plan-Items

**Welle 6 ist per Welle-6a-C0 (2026-06-03) sub-gesliced**
(siehe [`M5-welle-6a.md`](../done/M5-welle-6a.md) §0 Sub-Slicing-
Beschluss + §3.1-Tabelle): 6a Fault-Flow (aktiv) + 6b
UI-Visualization + 6c Abnahmedoku. Pattern analog
M4-Welle-6 → 6a/6b.

**Welle 6b — UI-Visualization Done 2026-06-04** (Slice-
Doc [`M5-welle-6b.md`](../done/M5-welle-6b.md), Decisions
21/22/23 final 2026-06-03; C0 `efc2c10` + C2 `9fcb887`
+ C3 `580b2f0` + C4a `b30280e` Self-Close-Move + C4b
`3a6f150` Cross-Doc-Refs-Sync + Review-Folge `cd7cfc6`
mit 15/15 Findings F1..F15 adressiert). Volle Substanz lebt im Slice-Doc;
Quick-Glance:

- **GG-UI-006 (Geraete-Grafik)** — HTMX-Polling-
  Tabelle (4 Spalten ID/Typ/Zustand/Quality) ueber
  UI-Page `/runs/{id}/devices` mit HTMX-Polling auf
  NEU `GET /runs/{id}/devices/state` (JSON-Surface;
  URL-Realization-Note Slice-Doc §10.1: `/state`-Sub-
  Pfad wegen FastAPI-Routenkonflikt mit der UI-Page).
  Inline-SVG-Anlagengrafik bleibt Welle 7+/M6-Anti-
  Scope.
- **GG-UI-008 (Simulationszustaende)** — UI-Page
  `/runs/{id}/system` mit HTMX-Polling auf `/status`
  (1s) + `/health` (5s); Welle-4a-Endpunkte
  unveraendert.
- **Charting-Library-Re-Eval** — Decision 23 fixiert
  Chart.js (kein Plotly/ECharts-Spike).

**Welle 6c — Abnahmedoku (Plan-Items, TBD im Welle-
6c-C0-Slice-Doc):**

- **GG-DEMO-008 Abnahmedoku** unter
  `docs/user/gg-demo-008-abnahme.md` — Welle-5-C2-
  Folge-Entscheid 2026-06-03 (Range-Konsistenz mit
  `GG-DEMO-006`-Verschiebung). Schliesst die letzte
  Welle-5-Anti-Scope-Erbschaft auf; pure Doku ohne
  Code-Substanz.

**Welle 7 — Closure (Plan-Items, TBD im Welle-7-C0-
Slice-Doc):**

- Alle M5-ADRs auf `Accepted` (ADR 0036/0037/0038/
  0039/0040; ggf. weitere pro Welle).
- NEU `done/M5-results.md` mit Detail-Welle-Tabelle +
  Abnahme-Belege + Pro-Welle-Reviews + S-1..S-6-Sweep
  + Wandert-Nach (Pattern analog
  [`../done/M3-results.md`](../done/M3-results.md) +
  [`../done/M4-results.md`](../done/M4-results.md)).
- `roadmap.md §3 M5` 4 DoD-Checkboxen auf `[x]`;
  M5 auf `Done`; „Naechster aktiver Slice: M6".
- Top-Level-Doku-Sync (`README.md` / `README.de.md` /
  `AGENTS.md` / Status-Header).
- Self-Close-Move `M5-ui-demo.md → done/` (rename-
  only).
- Bezug-Linkpflege an M5-ADRs (ADR 0028).
- **M5-Welle-7-End-to-End-Sweep S-1..S-6:**
  - **S-1** M5-Vorabraeumungs-Item: Welle-0-Trigger-
    Triage + Welle-7-Sweep der in M5 dazu-gekommenen
    Trigger.
  - **S-2** Sub-Slicing-Schwelle eingehalten ueber
    Welle 1..6; Beleg-Tabelle.
  - **S-3** Default-`make gates` ohne
    `CRITICAL_COV_TARGETS`-Override cache-frei gruen
    am Welle-7-Closure-Hash.
  - **S-4** `make image-audit` cache-frei gruen
    ODER dokumentierter Defer-Pfad (krb5-CVE-Drift).
  - **S-5** ADR-Erweiterungs-Pattern fortgefuehrt
    (geplante ADR-Anzahl in M5: 1-3 ohne Supersedes
    per ADR 0011).
  - **S-6** Lastenheft-Coverage-Sweep nach M5-
    Closure (M6-Trigger erstellen, falls relevant).

**Welle-7-Gate:** `make fullbuild` cache-frei gruen
ODER dokumentierter Defer-Pfad. `make gates`
(10 A-1-Gates) als harter DoD-Gate.


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
