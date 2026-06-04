# M5 — UI + Demo — Closure-Ergebnisse

**Status:** Done (2026-06-04). M5-Abschluss-Gate `make gates`
cache-frei gruen **ohne** `CRITICAL_COV_TARGETS`-Override mit
10 A-1-Gates. `make fullbuild` ist pre-existing rot wegen
krb5-CVE-Drift in Debian-13-Base (M4-Welle-7-Erbschaft; siehe
§2 Defer-Pfad). Alle fuenf M5-ADRs (0036/0037/0038/0039/0040)
sind mit Welle-7-C1 `62f988d` auf `Accepted` promoted.
**Bezug:** Slice-Plan
[`M5-ui-demo.md`](../in-progress/M5-ui-demo.md);
Welle-Slice-Begleit-Docs
[`M5-welle-0.md`](M5-welle-0.md),
[`M5-welle-1.md`](M5-welle-1.md),
[`M5-welle-2.md`](M5-welle-2.md),
[`M5-welle-3.md`](M5-welle-3.md),
[`M5-welle-4a.md`](M5-welle-4a.md),
[`M5-welle-4b.md`](M5-welle-4b.md),
[`M5-welle-5.md`](M5-welle-5.md),
[`M5-welle-6a.md`](M5-welle-6a.md),
[`M5-welle-6b.md`](M5-welle-6b.md),
[`M5-welle-6c.md`](M5-welle-6c.md),
[`M5-welle-7.md`](../in-progress/M5-welle-7.md);
Roadmap [`../in-progress/roadmap.md`](../in-progress/roadmap.md)
§3 M5.

---

## 1. Welle-Tabelle

| Welle | Datum        | Lieferung                                                                                                                                                                                                                                                                                                                              | Commits                                                                                                                                                                                                       |
| ----- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | 2026-06-01   | Vorabraeumung + Slice-Plan-Eroeffnung (`M5-ui-demo.md` als kanonische M5-Slice-Spezifikation; 10 Decisions vorbelegt) + Pre-M5-Welle-0-Sondierungs-ADR 0036 (`Proposed`) + Trigger-Triage (Trigger 010 base-image-krb5-bump als M4-Welle-7-Erbschaft).                                                                                  | `d93ae57` (C0 Slice-Doc), `aa1db52` (Review-Folge 12 Findings), `b8bef6c` (C1 NEU M5-ui-demo.md), `112efd3` (C2 Trigger-Triage + Status-Flip), Self-Close `fd642df`.                                           |
| 1     | 2026-06-01   | HTTP-API-Surface (5 REST + 1 WebSocket): `POST /runs` + `GET /runs/{id}` + `/status` + `/snapshot` + `POST /control` + `POST /faults` + `WS /telemetry`. 4 neue Module mit `AC-NO-GOD-UTILS`-Split (`_dependencies.py` + `_schemas.py` + `_runs_router.py` + `_runs_action_router.py`). ADR 0036 → `Provisional` + NEU ADR 0037 (HTTP-API-Surface-Pattern). +16 Unit + +2 Integration. | Pre-C0c `9c20dad` (HTMX-FastAPI-Smoke-Probe), C0 `e573f67`, C1 `d468e68` (NEU ADR 0037), C2 `ae630ce`, C3 `f9f514d`, Self-Close `c7c2641`.                                                                     |
| 2     | 2026-06-01   | UI-Foundation: 6 Templates (`base.html` + 5 Page/Partial-Paare) + 3 vendored Static-Assets (HTMX 2.0.9 + Chart.js 4.5.1 + `style.css`) + `_templates.py`-Jinja2-Factory + `routes.py`-APIRouter mit 2 Page-Routes. Jinja2 als neue Dep; `StaticFiles`-Mount auf `/static`. +10 Unit + +2 Integration.                                                                                  | C0 `64d5129`, C2 `5234617`, C3 `97c718f`, Self-Close `8d60e16`.                                                                                                                                                |
| 3     | 2026-06-01   | Live-Telemetry-Dashboard (`GG-UI-002/003/009 + GG-API-002`): NEU `TelemetryStreamPort` + `InMemoryTelemetryStream` + `DemoTelemetryGenerator` + WS-Subscribe-Wiring + UI-Page `/dashboard` mit Chart.js-Time-Series + 6-Zustands-Quality-Marker. NEU ADR 0038. +16 Unit + +6 Integration.                                                                                              | Pre-C0c `5349923` (Asyncio-Pub/Sub-Probe), C0 `ab55ec7`, C1 `9f3c00d` (NEU ADR 0038), C2 `82bdf39`, C3 `0e0473d`, Self-Close `4517f51`.                                                                        |
| 4a    | 2026-06-02   | Replay-Controls + TickLoop-Wiring (`GG-UI-004`): RunStatus-Literal + `RunRepositoryPort.update_status`/`get_status` + TickLoop `request(action)`-Konsolidierung + NEU `TickLoopRegistry` + NEU `DemoTickLoopDriver` + UI-Page `/control` + NEU `_demo_setup.py`-Komposition-Root. NEU ADR 0039. +24 Unit + +1 Integration.                                                              | C0 `3544dee` (Welle-4-Sub-Slicing), C1 `f1284c4` (NEU ADR 0039), C2 `9c188e0`, C3 `2b4e5b3`, Self-Close `d1b0eb7`.                                                                                             |
| 4b    | 2026-06-02   | Alarm-Aggregation + AlarmStreamPort + UI-Tabelle (`GG-UI-005`): NEU `Alarm`-Domain-Type + Mapper-Familie in `core/simulation/alarm_mappers.py` + `TickResult.emitted_alarms` + TickLoop-Drain-Hook + NEU `AlarmStreamPort` + NEU `InMemoryAlarmStream` + `AlarmHistoryBuffer` + REST `/alarms-history` + WS `/alarms-stream` + UI 6-Spalten-Tabelle + NEU `_alarm_setup.py`. NEU ADR 0040. Loest ADR-0014-§6-Forward-Pointer. +31 Unit + +1 Integration. | C0 `08b5ba7`, C1 `850cf85` (NEU ADR 0040), C2 `b7ac7b3`, C3 `4dca6aa`, Review-Folge `52afd1a`/`fe1db21`/`ced9661`/`1fba165` (15 Findings), Self-Close `a030c0e`.                                                |
| 5     | 2026-06-03   | Demo-Pipeline + Scenario-Loader-Wiring (`GG-DEMO-001..005 + 007`): NEU `deploy/scenarios/gg-demo.yaml` + NEU `__main__.py` (`python -m grid_gym demo`) + NEU `InMemoryRunRepository` + NEU `_demo_scenario_setup.py` + Lifespan-env-var-Branch `GRID_GYM_DEMO_SCENARIO_PATH` (Decision 6) + NEU `make demo`/`demo-stop` Targets + compose.yml Service-Konfiguration. +6 Integration. | Pre-C0b `45335eb`, C0 `155c421`, C2 `904ef47`, Doku-Sibling `5ab0f67` (M5-ui-demo.md 780→321 Zeilen), C3 `61f5156`, Review-Folge `0e2bc41` (15 Findings W5-F1..F15), Self-Close `da8d728`/`2c9d8da`.            |
| 6a    | 2026-06-03   | Fault-Flow (`GG-UI-007` + `GG-DEMO-006`): NEU `gg-demo.yaml`-`faults:`-Block (cell_failure Tick 900 + voltage_drop Tick 1200) + NEU `_compose_fault_port` Battery+Grid-Adapter-Composition + UI-Page `/faults` mit HTMX-Form + NEU `routes_faults.py`-Modul-Split AC-NO-GOD-UTILS + Cross-Field-Validation im POST-Handler (Decision 20) + NEU public `tick_loop.device_types`-Property. Welle-6-Sub-Slicing-Beschluss 6 → 6a/6b/6c. +7 Integration.  | C0 `1d6d85e`, C2 `db3a0c2`, C3 `ed8fa74`, Self-Close `70fb82c`/`b19aeae`, Review-Folge `1e3a793` (15 Findings F1..F15).                                                                                        |
| 6b    | 2026-06-04   | UI-Visualization (`GG-UI-006` + `GG-UI-008`): NEU `GET /runs/{id}/devices/state` JSON-Surface (URL-Realization-Note: `/state`-Sub-Pfad statt natuerlicher URL wegen FastAPI-Routenkonflikt mit UI-Page) + NEU `DevicesResponse`/`DeviceStateEntry`-Pydantic-Modelle + `_aggregate_quality`/`_extract_state_subset`-Helper + NEU `routes_visualization.py` + 4 Templates `devices.html`/`_devices_content.html`/`system.html`/`_system_content.html`. NEU public `tick_loop.devices`-Property (Review-Folge F9). +22 Unit + +16 Integration (kumuliert). | C0 `efc2c10`, C2 `9fcb887`, C3 `580b2f0`, Self-Close `b30280e`/`3a6f150`, Review-Folge `cd7cfc6` (15 Findings F1..F15).                                                                                        |
| 6c    | 2026-06-04   | Abnahmedoku (`GG-DEMO-008`): NEU `docs/user/gg-demo-008-abnahme.md` mit 6-Schritt-Abnahmereihenfolge (Start / Healthcheck / Scenario / Fault-Injection / Replay / Export) + Top-Level-Doku-Sync + Status-Block-Kompression auf User-Feedback. Reiner Doku-Slice ohne Code-Diff; Test-Counts unveraendert. Loest letzte Welle-5-Anti-Scope-Erbschaft auf.                                | C0 `3db9fcd`, C2 `0e604e4`, C3 `06bf338`, Self-Close `c317200`/`cfb9626`. EoD-Sync `01e4bf5` (Welle-6b-Closure-Chronik).                                                                                       |
| 7     | 2026-06-04   | Closure: 5 M5-ADRs (0036..0040) `Provisional → Accepted`; `done/M5-results.md` (dieses Dokument); `roadmap.md` M5 → `Done`; S-1..S-6-Sweep; `make fullbuild`-krb5-CVE-Defer-Pfad dokumentiert (M4-Erbschaft); Self-Close-Move `M5-ui-demo.md` + `M5-welle-7.md`.                                                                                                                       | C0 `c28a11b`, C1 `62f988d` (5 ADRs → Accepted), C2 (dieser Commit; M5-results.md), C3 (folgt; Roadmap-DoD + Top-Level-Sync), C4a/b (folgt; Self-Close-Move + Cross-Doc-Refs).                                  |

**Test-Bilanz-Drift ueber M5:** 1584 Unit + 39 Integration
(Welle-1-Start) → **1722 Unit + 80 Integration** (Welle-7-
Closure) + 4 skipped (IEC-61850-2c-Mock-only-Fallback,
M4-Erbschaft).

**Endstand:** 9 HTTP-/WS-Endpunkte + 7 UI-Pages + 1 End-User-
Abnahmedoku produktiv unter `docs/user/`. Welle-Self-Close-
Move-Pattern (Pflicht per `planning/README.md`) ist in allen
9 produktiv-Wellen + Welle 7 eingehalten.

---

## 2. Abnahme-Belege

- **`make gates`-Gate (harter Welle-7-DoD-Gate):** cache-frei
  gruen **ohne** `CRITICAL_COV_TARGETS`-Override mit 10 A-1-
  Gates: `lint`, `format-check`, `typecheck` (mypy `--strict`
  + `strict_bytes = true`), `arch-check` (20 Contracts),
  `test-unit`, `coverage-gate` (90 % line / 85 % branch),
  `coverage-gate-critical` (90 % critical domain),
  `dep-audit`, `noqa-gate`, `spdx-check`.
- **`make test-integration`:** 80 passed + 4 skipped (IEC-
  61850-2c-Mock-only-Fallback per ADR 0035 §2.5; Trigger 009
  fuer Reaktivierung).
- **`make docs-check`:** cache-frei gruen ueber alle
  Markdown-Refs in der Repo.
- **`make openapi-validate`:** cache-frei gruen
  (`artifacts/openapi.json` validates against OpenAPI 3.1
  per `openapi-spec-validator`).
- **`make fullbuild`-Defer-Pfad (Pre-existing-Drift):**
  `image-audit` ist seit M3-Welle-7-`c61ab0d` pre-existing
  rot wegen 4 neuer HIGH-CVEs in Debian-13-Base
  (`CVE-2026-40356` u. a. in krb5-Paketen). **Nicht durch
  M5-Code verursacht** — Base-Image-Bump bleibt Trigger 010
  (M4-Welle-7-Erbschaft); M6 oder eigener Slice-Trigger
  loest ihn auf.

**Lastenheft-Coverage (M5-Scope) — alle erfuellt:**

| Lastenheft-ID                   | Anforderung                                                                                              | Produzierende Welle | Beleg (Test/Doku)                                                                                                                                              |
| ------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GG-API-001` Run-Erzeugung      | `POST /runs` mit Pydantic-Schema + `RunRepository.save`.                                                 | 1                   | `tests/integration/test_m5_welle_1_htmx_probe.py` + `tests/unit/adapters/driving/http_api/test_runs_router.py`.                                                |
| `GG-API-002` WS-Telemetrie      | `WS /runs/{id}/telemetry` mit `TelemetryStreamPort.subscribe`.                                            | 3                   | `tests/integration/test_m5_welle_3_async_pubsub_probe.py`.                                                                                                     |
| `GG-API-003` OpenAPI-Vertrag    | `GET /openapi.json` mit OpenAPI 3.1.                                                                      | 1                   | `make openapi-validate`.                                                                                                                                       |
| `GG-API-004` GG-API-004-Envelope | Strukturierte Fehler `{code, message, details, run_id}` ueber alle Endpoints.                            | 1+4a+4b+6a+6b       | 404/422-Asserts in allen Welle-Smokes.                                                                                                                         |
| `GG-UI-001` UI-Layout           | Web-UI mit Navigation.                                                                                   | 2                   | `templates/base.html` + `navigation.html`.                                                                                                                     |
| `GG-UI-002` Live-Telemetry      | Chart.js-Time-Series via HTMX-WS.                                                                        | 3                   | `tests/integration/test_m5_welle_2_ui_smoke.py` (UI-Foundation) + Dashboard-Page.                                                                              |
| `GG-UI-003` Zeitreihen          | Time-Series-Rendering pro Device.                                                                        | 3                   | `_dashboard_content.html` + Chart.js-Config.                                                                                                                   |
| `GG-UI-004` Replay-Controls     | Pause/Resume/Stop UI mit HTMX-POST.                                                                       | 4a                  | `tests/integration/test_m5_welle_4a_replay_controls_smoke.py`.                                                                                                 |
| `GG-UI-005` Alarm-Tabelle       | 6-Spalten-UI mit Live-Updates.                                                                            | 4b                  | `tests/integration/test_m5_welle_4b_alarms_smoke.py`.                                                                                                          |
| `GG-UI-006` Geraete-Grafik      | HTMX-Polling-Tabelle Devices/State/Quality.                                                              | 6b                  | `tests/integration/test_m5_welle_6b_visualization_smoke.py`.                                                                                                   |
| `GG-UI-007` Fault-Form          | UI-Form mit Cross-Field-Validation.                                                                       | 6a                  | `tests/integration/test_m5_welle_6a_fault_smoke.py`.                                                                                                           |
| `GG-UI-008` Sim-Zustand         | UI-Page `/system` mit Status + Health.                                                                    | 6b                  | `tests/integration/test_m5_welle_6b_visualization_smoke.py`.                                                                                                   |
| `GG-UI-009` Quality-Marker      | 6-Zustands-Quality-Visualisierung.                                                                       | 3+6b                | Welle-3-Dashboard + Welle-6b-Devices-Page.                                                                                                                     |
| `GG-DEMO-001..005` MUSS-IDs     | Demo-Umgebung + Netz + Batterie + Live-Telemetry binnen 30 s + Replay.                                   | 5                   | `tests/integration/test_m5_welle_5_demo_smoke.py` + Welle-5-Determinismus-Hash-Pin.                                                                            |
| `GG-DEMO-006` Demo-Faults       | YAML-side Fault-Injection (`cell_failure` + `voltage_drop`).                                              | 6a                  | `test_m5_welle_6a_fault_smoke.py::test_demo_yaml_faults_compose_and_apply_during_windows`.                                                                     |
| `GG-DEMO-007` Demo-Agent        | RuleBasedAgent in der Demo-YAML.                                                                          | 5                   | `gg-demo.yaml` + Welle-5-Smoke.                                                                                                                                |
| `GG-DEMO-008` Abnahmereihenfolge | Doku mit 6 Schritten (Start / Health / Scenario / Fault / Replay / Export).                              | 6c                  | [`docs/user/gg-demo-008-abnahme.md`](../../../user/gg-demo-008-abnahme.md).                                                                                    |

---

## 3. Pro-Welle-Reviews

Vier produktiv-Wellen haben einen `/code-review`-Pass mit je
15 Findings durchlaufen (Welle-Self-Pflicht-Pattern; Welle 0
und Welle-1..3+4a+5..6a..6c hatten keinen hoch-Effort-Review,
da die Substanz kleiner war ODER spaeter doch durch eine
Welle-Folge geschaerft wurde).

| Welle | Review-Folge-Hash | Findings | Cluster-Highlights                                                                                                          |
| ----- | ----------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 4b    | `52afd1a` + `fe1db21` + `ced9661` + `1fba165` | 15/15 | F1 Template-XSS-Haertung (3 Findings); F2 HTTP-Stabilitaet (404-vs-500 + Deque-Race); F3 Driver-Lifecycle (Late-Wiring + Task-Exception); F4 Domain/Resume (Tick-Atomicity + `_control_state`). |
| 5     | `0e2bc41`         | 15/15    | W5-F1..F15 (Demo-Pipeline + Scenario-Loader Haertung); Stichworte siehe Welle-5-EoD-Sync `0f982b4`.                          |
| 6a    | `1e3a793`         | 15/15    | F1..F15 (Fault-Flow + Cross-Field-Validation); siehe Welle-6a-EoD-Sync `0f982b4`.                                            |
| 6b    | `cd7cfc6`         | 15/15    | F1 Devices-Inline-JS-XSS via DOM-API + textContent; F2 Pre-init-silent-drop; F3 Truthy-Coerce Fault-Flags; F4 RunStatus-Null-Guards; F5 `_QUALITY_SEVERITY.get()`-Fallback; F6 Error-State-Branch; F7 String-Coerce; F8 Smoke-Test-Race-Fix; F9 NEU public `tick_loop.devices`-Property; F10/F13/F14 UI-Adapter-Cleanup; F11/F12/F15 Helper-Cleanup + `QUALITY_SEVERITY` nach `core/domain/quality.py`. |

**Welle 6c kein Review:** reine Doku-Welle (1 Markdown-Datei
+ README-Pointer), `/code-review` ist code-zentriert; manuelle
Doku-Pruefung gegen `GG-DEMO-008`-Akzeptanztext war
ausreichend.

---

## 4. S-1..S-6 Verification (M5-Welle-7-End-to-End-Sweep)

**S-1 — M5-Vorabraeumungs-Item + Welle-7-Sweep neuer Trigger.**

- Welle-0-C2 `112efd3` hat Trigger-Triage durchgefuehrt;
  Trigger 010 (base-image-krb5-bump) als M4-Welle-7-
  Erbschaft explizit aufgenommen.
- Keine neuen M5-Trigger eroeffnet (alle M5-Welle-Risiken
  blieben innerhalb der Welle-Slice-Docs adressiert).

**S-2 — Sub-Slicing-Schwelle eingehalten.**

- **Welle 4** wurde am C0-Pre-Research-Zeitpunkt 2026-06-02
  in **4a/4b** sub-gesliced (RunStatus + TickLoop-Control vs.
  Alarm-Aggregation + AlarmStreamPort — zwei distinkte ADRs
  + Decisions-Slots).
- **Welle 6** wurde am Welle-6a-C0-Sub-Slicing-Beschluss
  2026-06-03 in **6a/6b/6c** sub-gesliced (Fault-Flow + UI-
  Visualization + Abnahmedoku — drei distinkte Lastenheft-
  Substanz-Anteile).
- **Pattern analog M4-Welle-5 → 5a/5b und M4-Welle-6 →
  6a/6b.** Sub-Slicing-Schwelle (> 300 Zeilen Slice-Doc ODER
  > 5 Code-Commits ODER > 2 unabhaengige Sub-Bereiche) in
  beiden M5-Faellen produktiv-belegt.

**S-3 — Default-`make gates` ohne CRITICAL_COV_TARGETS-Override
cache-frei gruen am Welle-7-Closure-Hash.**

- Verifiziert am Welle-7-C1 `62f988d` + Welle-7-C2 (dieser
  Commit). Pattern analog M4-Welle-7-S-3.

**S-4 — `make image-audit` Defer-Pfad.**

- Pre-existing rot wegen Debian-13-krb5-CVE-Drift (M4-Welle-
  7-Erbschaft Trigger 010); nicht durch M5-Code verursacht.
- Defer-Pfad dokumentiert: Trigger 010 bleibt offen; M6
  oder eigener Slice loest ihn.

**S-5 — ADR-Erweiterungs-Pattern fortgefuehrt.**

- 5 neue M5-ADRs ohne Supersedes (per ADR 0011):
  0036 (UI-Stack), 0037 (HTTP-API-Surface), 0038
  (TelemetryStreamPort), 0039 (Run-Control), 0040 (Alarm-
  Stream-Port).
- **Soll-Wert war 1-3 ADRs pro Meilenstein, Ist-Wert ist
  5.** Begruendung: M5 hat **fuenf separate Decision-Konzerne**
  (UI-Stack-Wahl, HTTP-API-Surface-Pattern, Telemetry-
  Stream-Surface, Run-Control + Status, Alarm-Aggregation +
  Stream) — jeder dieser Konzerne ist eine distinkte
  Architektur-Decision mit eigener Welle-Lieferung +
  ADR-Body-Substanz. Drei Optionen waeren gewesen: (a) ADRs
  zusammenfassen (gegen ADR-0011-Schaerfungs-ohne-Supersede-
  Pattern), (b) Decisions ohne ADR (gegen ADR-0006-Decision-
  Locality), (c) status quo (5 fokussierte ADRs). Maintainer-
  Entscheid: (c) — pattern-konsistent mit M3 (6 ADRs) und
  M4 (6 ADRs).

**S-6 — Lastenheft-Coverage-Sweep nach M5-Closure.**

- Alle M5-Scope-IDs erfuellt (siehe §2 Tabelle). Keine
  offenen M5-Anforderungen.
- M6-Trigger-Sichtung: 0 neue Trigger durch M5-Lieferungen
  eroeffnet (alle Welle-Anti-Scope-Items waren bereits in
  Lastenheft §22 (`GG-PERFORM-*`) / §23 (`GG-SAFE-*`) etc.
  verankert).

---

## 5. Welle-7-Erbschaft fuer M6+

**Architektonische Erbschaft** (per M5-Slice-Docs §10-Notes
+ Welle-6b-URL-Realization):

- **URL-Versionierung Welle 7+/M6:** Welle-4b
  `/alarms-history` + Welle-6b `/devices/state` haben das
  „natuerliche-URL-UI + suffixed-URL-JSON"-Pattern etabliert
  (Welle-6b-C3-Realization-Note §10.1). Ein `/api/v1`-Mount-
  Prefix in M6 wuerde die Konvention konsolidieren bevor
  weitere Endpoints denselben Mismatch reproduzieren.
- **Snapshot-Envelope-v2-Serialisierung:** `GET /snapshot`
  liefert heute nur den `schema_ref`-Pointer; volle
  Envelope-Body-Serialisierung bleibt M6-Material (ADR 0015
  v2-Snapshot-Erbschaft).
- **CSV/JSONL-Export-Endpunkte:** Welle-6c-Abnahmedoku
  dokumentiert WS-Streams als Export-Surface; Datei-Export
  ist `GG-ACCEPT-003`-Welle-7-Welle-7-Material (M6 oder
  separater Slice).
- **Inline-SVG-Geraete-Grafik:** Welle-6b liefert HTMX-
  Polling-Tabelle als `GG-UI-006`-Erfuellung; Inline-SVG-
  Anlagenschaltbild ist M6-Material.
- **Dynamische Fault-Activation:** `POST /faults` ist
  Welle-6a-Form-Validation-only (Decision 19); dynamische
  TickLoop-Activation bleibt M6-Material.
- **IEC-61850-Smoke-Reaktivierung:** Trigger 009 bleibt
  offen; M6 oder ein separater Slice (Python-3.12-Test-
  Stage ODER `pyiec61850-ng` 2.0.x mit cp314-Wheel) loest
  ihn.
- **Welle-3-Pre-init-Defense-Pattern:** Welle-6b-Review-
  F2 (`_extract_state_subset` silent-drop) verallgemeinert
  fuer andere device-iterierende Endpoints — Welle-7+/M6-
  Pattern fuer alle zukuenftigen Driving-Adapter, die
  `device.snapshot()` konsumieren.

**ADR-Erbschaft:**

- ADRs 0036..0040 alle `Accepted` (Welle-7-C1 `62f988d`);
  keine offenen Migrations-Klauseln.
- ADR 0036 §2.5 Migrations-Pfad SvelteKit-SPA + Plotly/
  ECharts bleibt dokumentiert fuer Stakeholder-Druck-
  Eskalation.

**`make fullbuild`-Defer-Pfad** (Pre-existing-Drift M4-Welle-
7-Erbschaft):

- Trigger 010 (Base-Image-krb5-Bump) bleibt offen.
- `make fullbuild` rot wegen Debian-13-krb5-CVE; nicht
  durch M5-Code verursacht.

---

## 6. M5-ADR-Decision-Sweep

5 ADRs auf `Accepted` mit Welle-7-C1 `62f988d` (M5-Closure-
Welle). Pro-ADR Status-Header + §5 Status-Pfad-Body-Block
konsistent.

| ADR  | Titel                                          | Welle  | Decisions               | Status-Pfad                                                                          |
| ---- | ---------------------------------------------- | ------ | ----------------------- | ------------------------------------------------------------------------------------ |
| 0036 | UI-Stack-Choice                                | 1..6c  | Option 1 + Chart.js     | Proposed 2026-06-01 → Provisional 2026-06-01 (M5-W1-C1) → **Accepted 2026-06-04**.   |
| 0037 | HTTP-API-Surface-Pattern                       | 1+4a   | API-1/2/3               | Proposed 2026-06-01 (M5-W1-C1) → Provisional 2026-06-01 (M5-W1-C3) → **Accepted 2026-06-04**. |
| 0038 | TelemetryStreamPort + WS-Subscribe             | 3      | 11a/b/c                 | Proposed 2026-06-01 (M5-W3-C1) → Provisional 2026-06-01 (M5-W3-C3) → **Accepted 2026-06-04**. |
| 0039 | Run-Control + Status-Tracking                  | 4a     | 12/13/14                | Proposed 2026-06-02 (M5-W4a-C1) → Provisional 2026-06-02 (M5-W4a-C3) → **Accepted 2026-06-04**. |
| 0040 | Alarm-Aggregation + Stream-Port                | 4b     | 15/16/17                | Proposed 2026-06-02 (M5-W4b-C1) → Provisional 2026-06-02 (M5-W4b-C3) → **Accepted 2026-06-04**. |

**Welle-Substanz-Decisions** (ohne eigene ADR, im Slice-
Doc-Body verankert):

- Welle 0: 10 Decisions vorbelegt (Slice-Plan-Substanz).
- Welle 2: Decision 2 (UI-Adapter-Lokation).
- Welle 5: Decisions 5/6/18 (Demo-Pipeline + Scenario-Loader
  + compose.yml).
- Welle 6a: Decisions 19/20 (Fault-Flow + Cross-Field-
  Validation).
- Welle 6b: Decisions 21/22/23 (Devices-API-Surface + UI-
  Pages + Charting-Re-Eval).

**Keine Supersedes** in M5 (pattern-konsistent mit M3 + M4;
per ADR 0011).

---

## 7. M5-Wandert-Nach

**Beim Welle-7-C4a Self-Close-Move** (nach C3):

- `M5-ui-demo.md` (in-progress) → `done/`.
- `M5-welle-7.md` (in-progress) → `done/`.

**Lebend bleibt** (kein Move):

- `docs/user/gg-demo-008-abnahme.md` (End-User-Doku;
  Welle-6c-Lieferung).
- Welle-6c-Anti-Scope-Items (CSV/JSONL-Export, Inline-SVG,
  Tutorial) — explizit M6/Welle-7+/Welle-?-Material.

**Roadmap-Sweep (C3)** flippt:

- `roadmap.md §3 M5` Status `In Progress → Done`.
- `roadmap.md` Header + §3-Block: „Aktiver Slice: M6
  (Performance + Security + CI/CD)".
- M5-DoD-Checkboxen alle abhaken (4 Items).

---

## 8. Nicht-vollzogene Items (bewusst)

- **Snapshot-Envelope-v2-Serialisierung** (`GET /snapshot`-
  Body) — bleibt M6.
- **CSV/JSONL-Export** — `GG-ACCEPT-003`-Welle-7 oder M6.
- **Inline-SVG-Geraete-Grafik** — M6.
- **Dynamische Fault-Activation** ueber HTTP-Form — M6
  (Welle-6a Decision 19 Anti-Scope).
- **Inline-SVG-Anlagenschaltbild** — M6 (Welle-6b Anti-
  Scope).
- **WebSocket-Live-Stream `/devices`** — M6 (Welle-6b Anti-
  Scope; HTMX-1s-Polling reicht fuer Demo).
- **Tutorial / Onboarding-Doku** (`GG-ACCEPT-001`) —
  M5-Welle-7-Closure (`done/M5-results.md` ist die formale
  Doku; eine separate Tutorial-Doku gehoert zu
  M5-Welle-7-Closure-Erbschaft oder M6).
- **Multi-User + Auth** — M6 (`GG-SAFE-008` IP-/Netz-
  Beschraenkung im Demo-Compose; nicht im UI-Layer).
- **SvelteKit-SPA / React-SPA Migration** — M6+ falls
  Stakeholder-Druck (ADR 0036 §2.5 Migrations-Pfad).
- **Plotly.js / ECharts** — M6+ falls Chart.js-Limitationen
  in Welle 3/4/6b sichtbar werden (ADR 0036 §2.5 +
  Welle-6b-Decision-23-Re-Eval).
- **Base-Image-krb5-Bump** (Trigger 010) — M4-Welle-7-
  Erbschaft; M6 oder eigener Slice.
- **IEC-61850-Smoke-Reaktivierung** (Trigger 009) —
  M4-Welle-6b-Erbschaft; M6 oder eigener Slice.

---

## References

- Slice-Plan: [`M5-ui-demo.md`](../in-progress/M5-ui-demo.md).
- Welle-Slice-Docs: [`M5-welle-0.md`](M5-welle-0.md),
  [`M5-welle-1.md`](M5-welle-1.md),
  [`M5-welle-2.md`](M5-welle-2.md),
  [`M5-welle-3.md`](M5-welle-3.md),
  [`M5-welle-4a.md`](M5-welle-4a.md),
  [`M5-welle-4b.md`](M5-welle-4b.md),
  [`M5-welle-5.md`](M5-welle-5.md),
  [`M5-welle-6a.md`](M5-welle-6a.md),
  [`M5-welle-6b.md`](M5-welle-6b.md),
  [`M5-welle-6c.md`](M5-welle-6c.md),
  [`M5-welle-7.md`](../in-progress/M5-welle-7.md).
- M5-ADRs:
  [`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md),
  [`../../adr/0037-http-api-surface-pattern.md`](../../adr/0037-http-api-surface-pattern.md),
  [`../../adr/0038-telemetry-stream-port.md`](../../adr/0038-telemetry-stream-port.md),
  [`../../adr/0039-run-control-and-status-tracking.md`](../../adr/0039-run-control-and-status-tracking.md),
  [`../../adr/0040-alarm-aggregation-and-stream-port.md`](../../adr/0040-alarm-aggregation-and-stream-port.md).
- Lastenheft:
  [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md)
  §16 (`GG-API-001..004`) + §17 (`GG-UI-001..009`) + §24
  (`GG-DEMO-001..008`).
- End-User-Abnahmedoku:
  [`../../../user/gg-demo-008-abnahme.md`](../../../user/gg-demo-008-abnahme.md).
- Roadmap:
  [`../in-progress/roadmap.md`](../in-progress/roadmap.md)
  §3 M5.
- M-Closure-Pattern-Vorbilder:
  [`M4-results.md`](M4-results.md) + [`M3-results.md`](M3-results.md).
