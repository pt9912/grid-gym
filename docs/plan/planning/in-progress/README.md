# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.

## Bestand

| Datei                     | Gegenstand                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`roadmap.md`](roadmap.md)              | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status.                                                  |
| [`M5-ui-demo.md`](M5-ui-demo.md) | M5-Slice-Plan (UI + Demo; Vorbelegung Welle 0..7 + Out-of-Scope + Risiken + Verifikationspfad; Pattern analog `done/M4-protocol-adapters.md`). |
| [`M5-welle-3.md`](M5-welle-3.md) | Welle-3-Slice-Doc (M5 Live-Telemetry-Dashboard: NEU `TelemetryStreamPort` + `InMemoryTelemetryStream` + WS-Subscribe-Pattern + Chart.js-Time-Series + Quality-Marker; `GG-UI-002/003/009` + `GG-API-002`) — `In Progress` 2026-06-01; bleibt in `in-progress/` bis Self-Close-Move als M5-Welle-4-Pre-C0. |

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

**Aktive Welle:** M5-Welle-3 (Live-Telemetry-Dashboard)
eroeffnet 2026-06-01 mit Pre-C0a `8d60e16` (Self-Close-
Move `M5-welle-2.md → done/`, rename-only) + Pre-C0b
`159f537` (Cross-Doc-Refs-Sync nach Move) + Pre-C0c
`5349923` (Asyncio-Pub/Sub-Smoke-Probe-Run mit 4 Probe-
Tests gruen — Pattern fuer Welle-3-`TelemetryStreamPort`
server-side validiert) + C0 (dieser Commit; Slice-Doc-
Anlage [`M5-welle-3.md`](M5-welle-3.md) mit **Decision
3** WebSocket per Lastenheft-Pflicht (`GG-API-002`) +
**Decision 7** Chart.js 4.5.1 bestaetigt produktiv +
**NEU Decision 11** `TelemetryStreamPort` (Driving) +
`InMemoryTelemetryStream`-Adapter; Surface in C1
verankert). Geplante Lieferung in 3 weiteren Commits:
C1 (NEU ADR 0038 fuer Decision 11), C2 (Port + Adapter
+ WS-Wiring + UI-Page + Quality-Marker + Tests), C3
(Status/DoD-Sync).
