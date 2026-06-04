# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.

## Bestand

| Datei                     | Gegenstand                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`roadmap.md`](roadmap.md)              | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status.                                                  |
| [`M5-ui-demo.md`](../done/M5-ui-demo.md) | M5-Slice-Plan (UI + Demo; Vorbelegung Welle 0..7 + Out-of-Scope + Risiken + Verifikationspfad; Pattern analog `done/M4-protocol-adapters.md`). |
| [`M5-welle-5.md`](../done/M5-welle-5.md) | Welle-5-Slice-Doc (M5 Demo-Pipeline + Scenario-Loader-Wiring). — **Done 2026-06-03** + Self-Close-Move `da8d728` + Cross-Doc-Refs-Sync `2c9d8da`. |
| [`M5-welle-6a.md`](../done/M5-welle-6a.md) | Welle-6a-Slice-Doc (M5 Fault-Flow: UI-Form-Validation + YAML-Fault-Demo). — **Done 2026-06-03** + Self-Close-Move `70fb82c` + Cross-Doc-Refs-Sync `b19aeae` + Review-Folge `1e3a793` (15/15 Findings). |
| [`M5-welle-6b.md`](../done/M5-welle-6b.md) | Welle-6b-Slice-Doc (M5 UI-Visualization: Geraete-Grafik + Sim-Zustand-Dashboard). — **Done 2026-06-04** + Self-Close-Move `b30280e` + Cross-Doc-Refs-Sync `3a6f150` (6 Refs) + Review-Folge `cd7cfc6` (15/15 Findings F1..F15). |
| [`M5-welle-6c.md`](../done/M5-welle-6c.md) | Welle-6c-Slice-Doc (M5 Abnahmedoku `GG-DEMO-008`; letzte Welle-6-Sub-Slice, reiner Doku-Slice). — **Done 2026-06-04** + Self-Close-Move `c317200` + Cross-Doc-Refs-Sync `cfb9626`. |
| [`M5-welle-7.md`](../done/M5-welle-7.md) | Welle-7-Slice-Doc (M5-Closure-Welle: ADR-Accepts + `done/M5-results.md` + DoD-Sweep + Self-Close-Move `M5-ui-demo.md`). — **In Progress 2026-06-04** mit C0 (dieser Commit). |

M3 ist mit Welle 7 vollstaendig abgeschlossen
(2026-05-25, siehe
[`../done/M3-results.md`](../done/M3-results.md)). **M4** ist
mit Welle 0 am 2026-05-26 eroeffnet; Welle 1
(`DeviceProtocolPort`-Foundation), Welle 2 (MQTT-Adapter),
Welle 3 (Modbus-TCP-Adapter), Welle 4 (OPC-UA-Adapter,
**erster rein-async-Stack** im Repo), Welle 5a (DNP3-
Adapter-Spike, **zwei-Library-Setup** `nfm-dnp3` +
`dnp3-outstation`) und Welle 5b (IEC-61850-Adapter-Spike,
**erster GPL-isolierter Sub-Module-Praezedenzfall** im Repo
+ **erste SWIG-/C-native Library**) sind abgeschlossen;
Welle 5b mit ADR 0035 `Provisional` (`Proposed` per
`88c1a33` → C1-Review-Folge `da8aed9` → `Provisional` per
C3 `ca96bca`) und C2-Merge `944bca5` + Slice-033-Review-
Folge `7e0c91b` (15 Findings 10 HIGH + 5 MEDIUM ohne ADR-
Status-Aenderung adressiert). 2c-Mock-only-Fallback fuer
IEC-Integration-Smoke bleibt aktiv (Welle-6b-Reaktivierung
steht). **Welle 6a (Cross-Adapter-Hardening Mainstream)
abgeschlossen 2026-06-01** mit C0 `9776dd9` + C1 `9312239`
+ C2 `9d3912f` + Pre-C3 `81140e2` + C3 `0a5e895` + C4
`69b37f1` + **Slice 034 Review-Folge `bde8fdb`** (1 HIGH
+ 6 MEDIUM + 4 LOW-MEDIUM + 4 LOW Findings adressiert,
F13 als Welle-6b-Vorlauf-Item dokumentiert) + Hash-Sync
`b6a778d` + **Self-Close-Move `d1cb65d`** (rename-only)
+ Pre-C0-Sync (dieser Commit). 1537 → 1566 Unit-Tests
(+29 mit 19 OTel-Span-Wrap + 6 AC-ADAPTER-LIGHTWEIGHT-
Planted-Violator + 4 Slice-034-Adapter-Tests).
Welle-0..5b- und Welle-6a-Docs sind alle nach
[`../done/M4-welle-0.md`](../done/M4-welle-0.md),
[`../done/M4-welle-1.md`](../done/M4-welle-1.md),
[`../done/M4-welle-2.md`](../done/M4-welle-2.md),
[`../done/M4-welle-3.md`](../done/M4-welle-3.md),
[`../done/M4-welle-4.md`](../done/M4-welle-4.md),
[`../done/M4-welle-5a.md`](../done/M4-welle-5a.md),
[`../done/M4-welle-5b.md`](../done/M4-welle-5b.md),
[`../done/M4-welle-6a.md`](../done/M4-welle-6a.md) bzw.
[`../done/M4-welle-6b.md`](../done/M4-welle-6b.md)
gewandert (Self-Close-Moves `556ae9f` / `81b5cba` /
`0d6ad6c` / `506c8ca` / `3bc015b` / `9fea2be` / `30860ed`
/ `d1cb65d` / `bf23458`). Der kanonische M4-Slice-Plan
[`M4-protocol-adapters.md`](../done/M4-protocol-adapters.md)
ist nach `done/` gewandert (Self-Close-Move `e745f10` als
M4-Welle-7-C4; Bezug-Linkpflege an ADR 0030..0035 per
ADR-0028-Verfahren).
**Welle 6b (IEC-61850-Lizenz-und-Smoke-Hardening, Welle-5b-
Erbschaft + Slice-034-F13-Vorlauf-Item) abgeschlossen
2026-06-01** mit C0 `14d1bcb` (Slice-Doc) + C1 `8947c62`
(SPDX-Header-Lint via NEU `tools/check_spdx.py` + 10.
A-1-Gate `make spdx-check`) + C2 `9e2bf39` (NEU
`AC-IEC61850-GPL-BOUNDARY` arch_check-Contract, 19 → 20
KEPT; AST-Import-Scan; 8 Property-Tests) + C3 `2539574`
(IedServer-Smoke-Probe Pfad C aktiv mit Trigger 009 nach
PyPI-Pfad-A-Befund: Library-Stand identisch zu Welle 5b,
kein cp314-Manylinux-Wheel; plus Slice-034-F13-Coverage-
Schaerfung `_is_adapter_lightweight_path` erweitert um
flat-file `_protocol_*.py`-Cross-Adapter-Helper) + C4
`314ccae` (Status/DoD-Sync + NEU `CONTRIBUTING.md` mit
Dual-License-Policy + Top-Level-Doku-Sync) + **Self-Close-
Move `bf23458`** als M4-Welle-7-Pre-C0 (rename-only) +
Pre-C0-Sync (dieser Commit). 1566 → 1584 Unit-Tests (+18
unique: 9 SPDX-Lint + 8 GPL-Boundary-Property + 1 F13-
Cross-Adapter-Helper-Positiv). 10/10 A-1-Gates gruen (10.
NEU `spdx-check`); 20/20 Contracts KEPT (14. NEU
`AC-IEC61850-GPL-BOUNDARY`).

**M4 abgeschlossen 2026-06-01** mit Welle 7 (M4-Closure):
C0 `af97fd7` (Slice-Doc) + C0-Review `05a1417` (8
Findings: 3 Blocker + 3 Schaerfungen + 5 Polish) + C1
`d2071f0` (6 M4-ADRs von `Provisional` auf `Accepted`)
+ C2 `0c644f0` (NEU [`../done/M4-results.md`](../done/M4-results.md)
mit Welle-Tabelle/Abnahme-Belegen/Pro-Welle-Reviews/
S-1..S-6-Sweep/Wandert-Nach) + C3 (dieser Commit;
Roadmap-M4-DoD-Sweep + Top-Level-Doku-Sync). Ausstehend:
C4 (Self-Close-Move `M4-protocol-adapters.md` nach
`done/` + ADR-0030..0035-Bezug-Linkpflege per ADR-0028-
Verfahren).

**Welle 0 (M5-Slice-Plan-Eroeffnung + Trigger-Triage)
abgeschlossen 2026-06-01** mit C0 `d93ae57` (Slice-Doc)
+ C0-Review `aa1db52` (12 Findings) + C1 `b8bef6c` (NEU
`M5-ui-demo.md`) + C2 `112efd3` (Trigger-Triage +
Status-Flip) + Self-Close-Move `fd642df` (rename-only) +
Pre-C0-Sync (dieser Commit). NEU
`open/010-base-image-krb5-cve-bump.md` als expliziter
Trigger der M4-Welle-7-Erbschaft; `roadmap.md §3 M5`
von `Vorbelegung` auf `In Progress` geflippt (Decision 10
in Welle-0-C2 entschieden); Pre-M5-Welle-0-Sondierungs-
ADR
[`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md)
verankert mit Maintainer-Decision-Indication „Option 1
(FastAPI + HTMX + Jinja2 + Chart.js)" (`f4a9ced` +
`e0c3f66`). Welle-0-Slice-Doc nach `done/M5-welle-0.md`
gewandert (`fd642df` rename-only; Pattern analog M4-Welle-
0 Self-Close-Move `556ae9f`).

**Welle 1 (M5-Welle-1 HTTP-API-Surface + ADR-0036/0037-
Schaerfung) abgeschlossen 2026-06-01** mit Pre-C0a
`fd642df` (`git mv M5-welle-0.md → done/`) + Pre-C0b
`fb417b9` (Cross-Doc-Refs-Sync) + Pre-C0c `9c20dad`
(HTMX-FastAPI-Smoke-Probe-Run; 4 Probe-Tests gruen) +
C0 `e573f67` (Slice-Doc
[`M5-welle-1.md`](../done/M5-welle-1.md)) + C1 `d468e68`
(ADR 0036 `Proposed → Provisional` mit Probe-Run-Beleg
`9c20dad` + NEU ADR 0037 `Proposed` „HTTP-API-Surface-
Pattern" mit Decisions API-1 = Replay-Controls via
`POST /runs/{id}/control`-Action-Body + API-2 = kein
separater `UICommandPort`-Slot + API-3 = Roadmap-Typo
`GG-AR-PORT-DRG-002` verworfen) + C2 `ae630ce` (HTTP-API-
Surface-Implementation: 5 REST + 1 WebSocket-Endpunkt
unter `src/grid_gym/adapters/driving/http_api/` in 4
neuen Modulen — `_dependencies.py` + `_schemas.py` +
`_runs_router.py` + `_runs_action_router.py`; APIRouter-
Splitting wegen `AC-NO-GOD-UTILS`-Limit; +16 Unit + +2
Integration-Tests) + C3 `f9f514d` (ADR 0037 `Proposed →
Provisional` + Status/DoD-Sync + Top-Level-Doku-Sync inkl.
Roadmap-Typo-Fix `GG-AR-PORT-DRG-002` → Verwerfung in
`roadmap.md §3 M5`) + Self-Close-Move `c7c2641`
(rename-only) + Pre-C0-Sync (dieser Commit). 1584 → 1600
Unit-Tests (+16); 39 → 41 Integration (+2). 10/10 A-1-
Gates gruen cache-frei ohne Override.

**Welle 2 (M5-Welle-2 UI-Foundation) abgeschlossen
2026-06-01** mit Pre-C0a `c7c2641` (Self-Close-Move
`M5-welle-1.md → done/`, rename-only) + Pre-C0b `a0c8ba3`
(Cross-Doc-Refs-Sync nach Move) + C0 `64d5129` (Slice-
Doc-Anlage [`M5-welle-2.md`](../done/M5-welle-2.md) mit
**Decision 2 final fixiert** auf
`src/grid_gym/adapters/driving/ui/` per Hexagonal-
Architektur-Konsistenz; Pre-C0c entfiel weil Welle-1-
Probe `9c20dad` HTMX/Jinja2/WS bereits server-side
deckte) + C2 `5234617` (UI-Foundation produktiv: 6
Templates inkl. 2 Partials + 3 vendored Static-Assets
HTMX 2.0.9 + Chart.js 4.5.1 + `style.css` + `VENDORED.
md` + `_templates.py`-Jinja2-Factory + `routes.py`-
APIRouter mit 2 Page-Routes + 18 neuen Tests; Jinja2-
Dep `>=3.1,<4.0` mit `uv lock`-Sync `Added jinja2
v3.1.6`; `AC-PORTS-NO-FW` + `AC-NO-FW`-Forbidden-Listen
um `jinja2` erweitert; `StaticFiles`-Mount auf `/static`
+ `include_router(ui_router)` in `app.py`) + C3 `97c718f`
(Status/DoD-Sync + Top-Level-Doku-Sync) + Self-Close-Move
`8d60e16` (rename-only) + Pre-C0-Sync (dieser Commit).
Welle 2 verzichtete bewusst auf einen C1-ADR-Commit
(Decision 2 im Slice-Doc-§3-Body fixiert; ADR 0036 nimmt
Layout-Realisierung bei M5-Welle-7-Closure als Welle-2-
Beleg auf, Pattern analog ADR 0030 §6). 1600 → 1610
Unit-Tests (+10); 41 → 43 Integration (+2). 10/10 A-1-
Gates gruen cache-frei ohne Override.

**Welle 3 (M5-Welle-3 Live-Telemetry-Dashboard)
abgeschlossen 2026-06-01** mit Pre-C0a `8d60e16` (Self-
Close-Move `M5-welle-2.md → done/`, rename-only) +
Pre-C0b `159f537` (Cross-Doc-Refs-Sync nach Move) +
Pre-C0c `5349923` (Asyncio-Pub/Sub-Smoke-Probe-Run mit
4 Probe-Tests; Pattern server-side validiert) + C0
`ab55ec7` (Slice-Doc mit **Decision 3** WebSocket per
Lastenheft-Pflicht (`GG-API-002`) + **Decision 7**
Chart.js 4.5.1 bestaetigt + **NEU Decision 11**
`TelemetryStreamPort`) + CI-Hotfix `3ba74ef` (Ruff
SIM105 + format in der Pre-C0c-Probe-Datei) + C1
`9f3c00d` (NEU ADR 0038 `Proposed`) + C2 `82bdf39`
(Live-Telemetry produktiv: NEU `TelemetryStreamPort`
unter `hexagon/ports/driving/` + NEU
`InMemoryTelemetryStream` + `DemoTelemetryGenerator`
unter `adapters/driven/telemetry_stream_inmemory/` +
WS-Subscribe-Wiring + NEU UI-Page
`GET /runs/{run_id}/dashboard` mit HTMX-`hx-ext="ws"` +
Chart.js-Time-Series + 6-Zustands-Quality-Marker; 16
neue Unit + 2 Integration-Tests + Welle-1-Smoke-
Anpassung) + C3 `0e0473d` (ADR 0038 `Proposed →
Provisional` + Status/DoD-Sync + Top-Level-Doku-Sync) +
Self-Close-Move `4517f51` (rename-only) + Pre-C0-Sync
(dieser Commit). 1610 → 1626 Unit-Tests (+16); 43 → 49
Integration (+6). Lastenheft-Akzeptanz `GG-API-002` +
`GG-UI-002/003/009` produktiv. 10/10 A-1-Gates gruen
cache-frei ohne Override.

**Welle 4a (M5-Welle-4a Replay-Controls + TickLoop-Wiring)
abgeschlossen 2026-06-02** mit Pre-C0a `4517f51` (Self-
Close-Move `M5-welle-3.md → done/`, rename-only) + Pre-C0b
`79c9712` (Cross-Doc-Refs-Sync nach Move) + C0 `3544dee`
(Slice-Doc mit Decisions 12/13/14 final + Welle-4-Subdivision-
Motivation) + C1 `f1284c4` (NEU ADR 0039 `Proposed`) + C2
`9c188e0` (RunStatus-Literal-Alias + RunRepository-Extension
+ TickLoop-Control-Surface mit konsolidierter
`request(action)`-Methode + 2 Endpoint-Wirings auf
existierenden Welle-1-Stubs + NEU `TickLoopRegistry`-Adapter
+ NEU `DemoTickLoopDriver` + NEU UI-Page `GET /control` +
NEU `_demo_setup.py`-Komposition-Root + 24 neue Unit + 1
Integration-Test) + C3 `2b4e5b3` (ADR 0039 `Proposed →
Provisional` + Status/DoD-Sync + Top-Level-Doku-Sync) +
Self-Close-Move `d1b0eb7` (rename-only) + Pre-C0-Sync
(dieser Commit). 1626 → 1650 Unit-Tests (+24); 49 → 50
Integration (+1). Lastenheft-Akzeptanz `GG-UI-004` +
Replay-Restcompletion-Anteil `GG-API-001` produktiv. 10/10
A-1-Gates gruen cache-frei ohne Override. **C2-Realization-
Notes** (Welle-4a-C3-Sync, siehe Slice-Doc §0 + ADR 0039
§0): RunStatus-Vokabel auf `pending`/`completed` umgestellt
(Welle-1-`RunState`-Alignment); `request(action)`-
Konsolidierung statt 3 `request_*`-Wrapper (PLR0904-
Schwelle); `configure_demo_run` nach NEU `_demo_setup.py`
ausgelagert (AC-NO-GOD-UTILS); `AC-ADAPTER-PURE`-
`ignore_imports`-Block verankert ADR-0039-§2.2-Option-C-
Begruendung (kein separater `ControlPort`-Slot).

**Welle 4b (M5-Welle-4b Alarm-Aggregation + AlarmStreamPort
+ Alarm-Tabelle-UI) abgeschlossen 2026-06-02** mit Pre-C0a
`d1b0eb7` (Self-Close-Move `M5-welle-4a.md → done/`,
rename-only) + Pre-C0b `e325307` (Cross-Doc-Refs-Sync nach
Move) + C0 `08b5ba7` (Slice-Doc mit Decisions 15/16/17
final + Retro-Sync der Welle-4a-Era-2→3-Decision-Forward-
Pointer in `M5-ui-demo.md §3 Welle 4b`, `roadmap.md §3
M5`, ADR 0039 §3.2) + C1 `850cf85` (NEU ADR 0040
`Proposed`) + C2 `b7ac7b3` (NEU `Alarm`-Domain-Type +
Mapper-Familie in `core/simulation/alarm_mappers.py` +
`TickResult.emitted_alarms`-Feld + TickLoop-Drain-Hook +
NEU `AlarmStreamPort` + NEU `InMemoryAlarmStream` + NEU
`AlarmHistoryBuffer` + NEU REST-`/alarms-history` + NEU
WS-`/alarms-stream` + NEU UI-Page mit 6-Spalten-Tabelle +
NEU `_alarm_setup.py`-Komposition-Root + 31 neue Unit +
1 Integration-Test) + C3 `4dca6aa` (ADR 0040
`Proposed → Provisional` + Status/DoD-Sync + Top-Level-
Doku-Sync + 4 C2-Realization-Notes verankert). 1650 → 1681
Unit-Tests (+31); 50 → 51 Integration (+1). Lastenheft-
Akzeptanz `GG-UI-005` produktiv; ADR-0014-§6-Forward-
Pointer („AlarmSinkPort kommt mit M3") Driving-Side-Anteil
produktiv aufgeloest (Postgres-Persistenz bleibt M3-Welle-
6c). 10/10 A-1-Gates gruen cache-frei ohne Override.
**C2-Realization-Notes** (Welle-4b-C3-Sync, siehe Slice-Doc
§0 + ADR 0040 §0): REST-Pfad `/alarms-history` statt
`/alarms` (FastAPI-Routenkonflikt mit UI-Page); Mapper-
Familie in `core/simulation/alarm_mappers.py` statt
`core/domain/alarm.py` (AC-PORTS-NO-OUT); Power-Mapper-
Konsolidierung 4→1 zu `alarm_from_power_device_alarm`
Union-typed (AC-NO-GOD-UTILS); `_alarm_setup.py`-
Auslagerung aus `app.py` (AC-NO-GOD-UTILS).

**Welle-4b-Review-Folge** (2026-06-02, nach C3): xhigh-
effort `/code-review` deckte 15 Findings in der Welle-4b-
Substanz auf — alle in einer Folge-Lieferung adressiert
(siehe `done/M5-welle-4b.md §10`). 4 Cluster: F1 Template-
Haertung `52afd1a` (#6 XSS / #10 JSON-Parse / #14
`run_id`-Escape); F2 HTTP-Stabilitaet `52afd1a` (#7 404-
vs-500 / #15 Modul-Pfad / #5 Deque-Race); F3 Driver-
Lifecycle `fe1db21` (#1 Late-Wiring / #2 Task-Exception /
#9 stop()-Mirror / #12 Buffer-vor-Stream / #13 Orphan-
Guard); F4 Domain/Resume `ced9661` (#4 Tick-Atomicity /
#11 Loader-Kwargs / #8 `from_snapshot`-Kwargs / #3
`_control_state`-Resume); Doku-Sync `1fba165`. Keine
ADR-Aenderung — rein Bug-Fixes + Forward-Defense. 1681
→ 1696 Unit-Tests (+15); 10/10 A-1-Gates gruen cache-
frei.

**Welle-4-Subdivision (4a + 4b) komplett abgeschlossen
2026-06-02.** Self-Close-Move `M5-welle-4b.md → done/`
mit Welle-5-Pre-C0a `a030c0e` (rename-only;
Pattern `feedback_git_mv`).

**Welle 5 (M5-Welle-5 Demo-Pipeline +
Scenario-Loader-Wiring) abgeschlossen 2026-06-03** mit
Pre-C0a `a030c0e` (Self-Close-Move
`M5-welle-4b.md → done/`, rename-only) + Pre-C0b
`45335eb` (Cross-Doc-Refs-Sync nach Move, 5 Files) +
C0 `155c421` (Slice-Doc + Decisions 5/6/18 final +
Sub-Slicing-Risk-Verifikation; Single-Slice ohne
Splittung) + C2 `904ef47` (Code-Merge: NEU
`deploy/scenarios/gg-demo.yaml` + NEU
`src/grid_gym/__main__.py` + NEU
`src/grid_gym/adapters/driven/persistence_inmemory/
InMemoryRunRepository` + NEU
`src/grid_gym/adapters/driving/http_api/
_demo_scenario_setup.py` + Lifespan-env-var-Branch in
`app.py` + NEU `make demo`/`make demo-stop` Targets +
NEU `tests/integration/test_m5_welle_5_demo_smoke.py`
+ Decision-18-Praezisierung in `compose.yml` per
Service-Konfiguration (Port-Mapping `8000:8080` +
`GRID_GYM_DEMO_SCENARIO_PATH`-env + readonly
Scenario-Volume-Mount) + Rename `demo.yaml →
gg-demo.yaml` (range-neutral) + `GG-DEMO-008`-Defer
auf Welle 6 fuer Range-Konsistenz). Plus Doku-Sibling-
Stack `5ab0f67` (M5-ui-demo.md-Restrukturierung
780→321 Zeilen mit NEU §3.1 Welle-Status-Tabelle) +
C2-Plan-Sync `64c0fd9` (Slice-Doc §4 C3-Plan + §9
DoD-Liste an C2-Realitaet angleichen) + Doku-Sibling
`5fe5082` (README.md + README.de.md Status-Sections
kondensieren — Per-Welle-Breakdowns raus). Plus C3
(dieser Commit; Status/DoD-Sync + §10 C2-Realization-
Notes). Ausstehend: C4a Self-Close-Move
`M5-welle-5.md → done/` (rename-only) + C4b
Cross-Doc-Refs-Sync nach Move (Pattern analog
Welle-4b `a030c0e`/`45335eb`). 1681 → 1681 Unit-Tests
(+0); 51 → 57 Integration (+6 Welle-5-Smoke inkl.
Determinismus-Hash-Pin). Lastenheft-Akzeptanz
`GG-DEMO-001..005 + 007` produktiv; `GG-DEMO-006`
(Fault-Injection in Demo) + `GG-DEMO-008`
(Abnahmedoku) explizit auf Welle 6 verschoben (§1.3
Anti-Scope-Block; C2-Folge-Entscheid 2026-06-03 in
§10.1).

**Welle 6a (M5-Welle-6a Fault-Flow: UI-Form-
Validation + YAML-Fault-Demo) abgeschlossen 2026-06-03**
mit C0 `1d6d85e` (Slice-Doc + Sub-Slicing-Beschluss
Welle 6 → 6a/6b/6c + Decisions 19/20 final) + C2
`db3a0c2` (Code-Merge: NEU `gg-demo.yaml`-`faults:`-
Block + NEU `_compose_fault_port` Battery+Grid-Adapter-
Composition in `_demo_scenario_setup` + NEU UI-Page
`/runs/{id}/faults` mit HTMX-Form + NEU
`routes_faults.py`-Modul-Split AC-NO-GOD-UTILS +
NEU Cross-Field-Validation im `POST /runs/{id}/faults`-
Handler + NEU public `tick_loop.device_types`-Property
+ NEU Welle-6a-Integration-Smoke (7 Tests) + Welle-1-
Tests-Refactor an Welle-6a-Vertrag) + C3 (dieser
Commit; Status/DoD-Sync + §10 C2-Realization-Notes).
Ausstehend: C4a Self-Close-Move `M5-welle-6a.md →
done/` + C4b Cross-Doc-Refs-Sync nach Move. 1681 →
1681 Unit-Tests (+0; 4 NEU Welle-6a-Unit-Tests sind
in den bestehenden Test-Modulen integriert); 57 → 64
Integration (+7 Welle-6a-Smoke). Lastenheft-Akzeptanz
`GG-UI-007` (Form + Cross-Field-Validation) +
`GG-DEMO-006` (YAML-side Fault-Injection) produktiv;
Welle-5-Anti-Scope-Aufnahme erfolgreich. **Welle-6a-
Realization-Note** (Slice-Doc §10.1): Battery-
`cell_failure`-Auto-Alarm-Emission ist Welle-6+/M3-
Welle-2-Hardening-Material; `GG-DEMO-006`-Akzeptanz
„Telemetrie mit Qualitaetsstatus sowie einen Alarm"
wird ueber Telemetry-Side-Effect von Faults + den
vorhandenen Welle-5-LoadEvent-LIMITED-Alarm erfuellt.

**Welle 6b (M5-Welle-6b UI-Visualization: Geraete-
Grafik + Sim-Zustand-Dashboard) abgeschlossen 2026-06-04**
mit C0 `efc2c10` (Slice-Doc + Decisions 21/22/23 final)
+ C2 `9fcb887` (Code-Merge: NEU `GET /runs/{id}/devices/
state` JSON-Surface in `_runs_router.py` + NEU
`DevicesResponse`/`DeviceStateEntry`-Pydantic-Modelle +
NEU `_aggregate_quality`/`_extract_state_subset`-Helper
+ NEU `routes_visualization.py`-Schwester-Modul mit
zwei Page-Routes + NEU 4 Templates `devices.html` +
`_devices_content.html` + `system.html` +
`_system_content.html` + Navigation um „Devices"/
„System" erweitert + NEU Integration-Smoke 13 Tests +
NEU Unit-Tests 15 Tests) + C3 `580b2f0` (Status/DoD-Sync
+ §10 C2-Realization-Notes) + C4a `b30280e` (Self-Close-
Move `M5-welle-6b.md → done/`, rename-only) + C4b
`3a6f150` (Cross-Doc-Refs-Sync nach Move, 6 Refs) +
**Review-Folge `cd7cfc6`** (high-effort `/code-review`
→ 15/15 Findings F1..F15 adressiert in 7 Clustern:
F1/F4/F7 XSS-Haertung via DOM-API + textContent;
F2/F5/F6 Pre-init-silent-drop + .get()-Quality-Fallback
+ Error-State-Branch; F3 truthy-coerce fuer Fault-Flags;
F8 Smoke-Test-Race-Fix via tick_loop.request(„pause")
+ 3 NEU Tests; F9 NEU public `tick_loop.devices`-
Property; F10/F13/F14 UI-Adapter-Cleanup (Docstring +
NEU `_require_run_or_404`-Helper + `is_htmx_request` in
`_templates.py`); F11/F12/F15 Helper-Cleanup +
`QUALITY_SEVERITY` nach `core/domain/quality.py`).
1696 → 1722 Unit-Tests (+26; 15 Helpers + 4 Review-
Folge-Tests + 7 Drift); 64 → 80 Integration (+16; 13
Welle-6b-Smoke + 3 Review-Folge-Smoke F1/F2/F5).
Lastenheft-Akzeptanz `GG-UI-006 + GG-UI-008` produktiv.
10/10 A-1-Gates gruen cache-frei ohne Override.
**Welle-6b-Realization-Notes** (Slice-Doc §10):
URL-Split Decision-21-JSON wandert auf `/runs/{id}/
devices/state`-Sub-Pfad (UI-Page behaelt natuerliche
URL `/runs/{id}/devices`; Pattern analog Welle-4b-
Alarms `/alarms-history`); Adapter-internes
`_DeviceView`-Protocol haelt AC-ADAPTER-PURE ein
(keine `hexagon.core.devices`-Direct-Imports).

**Welle 6c (M5-Abnahmedoku `GG-DEMO-008`) abgeschlossen
2026-06-04** mit C0 `3db9fcd` (Slice-Doc) + C2 `0e604e4`
(NEU `docs/user/gg-demo-008-abnahme.md` mit 6-Schritt-
Abnahmereihenfolge: Start / Healthcheck / Scenario /
Fault-Injection / Replay / Export; plus Top-Level-Doku-
Sync + Status-Block-Kompression auf User-Feedback) + C3
(dieser Commit; Status/DoD-Sync + Welle-6-Subdivision-
Abschluss-Note). Ausstehend: C4a Self-Close-Move
`M5-welle-6c.md → done/` + C4b Cross-Doc-Refs-Sync.
Test-Counts unveraendert (1722/80; reiner Doku-Slice).
Lastenheft-Akzeptanz `GG-DEMO-008` produktiv; letzte
Welle-5-Anti-Scope-Erbschaft aufgeloest.

**Welle-6-Subdivision komplett 2026-06-04:** 6a Fault-
Flow (`Done 2026-06-03`) + 6b UI-Visualization (`Done
2026-06-04`) + 6c Abnahmedoku (`Done 2026-06-04`). Drei
Sub-Slices, drei klare Substanz-Anteile (`GG-UI-007` +
`GG-DEMO-006` / `GG-UI-006` + `GG-UI-008` /
`GG-DEMO-008`).

**Welle 7 (M5-Closure) abgeschlossen 2026-06-04** mit C0
`c28a11b` (Slice-Doc) + C1 `62f988d` (5 M5-ADRs
0036..0040 `Provisional → Accepted`) + C2 `5087c8a` (NEU
[`../done/M5-results.md`](../done/M5-results.md)
Closure-Artefakt mit 8 Sektionen) + C2-Review-Folge
`9978e21` (7 Findings 1 HIGH + 2 MEDIUM + 4 LOW
adressiert) + C3 (dieser Commit; `roadmap.md §3 M5`
DoD-Checkboxen abhaken + M5 auf `Done` + „Aktiver Slice:
M6" + Top-Level-Doku-Sync). Ausstehend: C4a Self-Close-
Move `M5-ui-demo.md` + `M5-welle-7.md` nach `done/` +
C4b Cross-Doc-Refs-Sync.

**M5 ist `Done` (2026-06-04)** — 10 Wellen 0..6c geliefert
(Sub-Slicing 4 → 4a/4b + 6 → 6a/6b/6c); 5 M5-ADRs
(0036..0040) auf `Accepted`; Lastenheft-Scope
`GG-API-001..004` + `GG-UI-001..009` + `GG-DEMO-001..008`
alle erfuellt; 1722 Unit-Tests + 80 Integration + 4
skipped; 10/10 A-1-Gates gruen cache-frei ohne Override.
Detail-Closure-Artefakt:
[`../done/M5-results.md`](../done/M5-results.md).

**Aktiver Slice:** **M6 (Performance + Security + CI/CD-
Haertung)** — Vorbelegung in `roadmap.md §3 M6`; Slice-Plan
entsteht in M6-Welle-0. M5-Welle-7-Erbschaft fuer M6 in
[`../done/M5-results.md §5`](../done/M5-results.md):
URL-Versionierung (`/api/v1`-Mount), Snapshot-Envelope-v2-
Body-Serialisierung, CSV/JSONL-Export, Inline-SVG-Geraete-
Grafik, dynamische Fault-Activation, IEC-61850-Smoke-
Reaktivierung (Trigger 009), `make fullbuild`-krb5-CVE-
Defer-Pfad (Trigger 010 M4-Erbschaft).
