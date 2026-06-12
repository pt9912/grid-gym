# Roadmap — grid-gym

**Status:** M1..M7 abgeschlossen — **der MVP ist geliefert** (M7 mit Welle-X-Closure 2026-06-12, [`../done/M7-results.md`](../done/M7-results.md); M6 mit Welle 7 Closure 2026-06-08, [`../done/M6-results.md`](../done/M6-results.md); M5 mit Welle 7 Closure 2026-06-04, [`../done/M5-results.md`](../done/M5-results.md)). **M7 abgeschlossen 2026-06-12**: alle vier `GG-MVP-*`-Punkte + alle vier `GG-SAFE-001..004` produktiv; fuenf M7-ADRs 0047/0048/0049/0052/0053 `Accepted` (0050/0051 bleiben `Proposed`, Welle-X-D-2). **Release v0.1.0 publiziert 2026-06-12** (Tag-Push → erster realer `release.yml`-Lauf: GHCR-Image + 5 Assets + SBOM-Digest-Bindung; Trigger 032 aufgeloest). **Aktiver Slice: keiner — Post-MVP-Trigger-Watch** (Welle-X-D-4): offene Trigger 033/037/038/039/040 + Trigger-Gated-Bestand ([`carveouts.md`](carveouts.md)) tragen dokumentierte Aktivierungs-Bedingungen; dazu zwei vorbereitete `next/`-Plaene ([`041`](../next/041-adapter-pure-ignore-imports-rueckbau.md) [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Rueckbau + [`042`](../next/042-fault-engine-location-and-naming.md) Fault-Engine-Naming — Umsetzungsslices fuer [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/0051, Aktivierung per Mandat). Ein neuer Meilenstein/Slice entsteht bei Trigger-Aktivierung oder Stakeholder-Mandat.
**Stand:** 2026-06-12

- **Meilensteine:** M1 `Done` (Welle 0..7), M2 `Done` (Welle 0..7),
  M3 `Done` (Welle 0..7), **M4 `Done`** (Welle 0..7 abgeschlossen
  2026-06-01 mit Welle-7-Closure `4567222`/`72e8357`/`e9aabd9` +
  Pre-M5-Sync `7f5beb8`; 6 M4-ADRs 0030..0035 auf `Accepted`; Slice-
  Plan + Welle-7-Doc nach `done/` gewandert; M4-Abschluss-Belege in
  [`../done/M4-results.md`](../done/M4-results.md). Welle-Detail
  unten zur Historie erhalten: Welle 0 `Done`;
  **Welle 1 `Done`** geschlossen 2026-05-30 mit C0 `f8cbe9d` +
  C1 `b840e7a` + Review-Folge `ad3dff8` + H4-Korrektur `111c464`
  + C2 `d09adf3` + EoD-Sync `f8ed791` + C3 `5f03bbf` +
  Linter-Folge `82f947c` + Self-Close-Move `81b5cba` +
  Pre-C0-Sync `f1f9db1`; **Welle 2 `Done`** geschlossen
  2026-05-30 mit C0 `3b633f6` + C1 `4e102b8` + C2 `f33bb4e` +
  C3 `7e161f5` + Self-Close-Move `0d6ad6c` + Pre-C0-Sync
  `9ba768b`; **Welle 3 `Done`** geschlossen 2026-05-30 mit
  C0 `8ef1e72` + C1 `a86ac46` + C2 `d721982` + EoD-Sync
  `2b84361` (3 Top-Level-Docs auf C2-Stand) + C3
  ([`ADR 0032`](../../adr/0032-modbus-adapter-profile.md) → `Provisional`, `M4-welle-3.md` → `Done`,
  Top-Level-Doku-Sync in 6 Docs, Trigger-006-Re-Eval mit
  Modbus-Beleg positiv) + Doku-Review-Folge 2026-05-31
  (Move von `M4-welle-3.md` nach `done/`, Smoke-Abdeckung
  praezisiert, Folge-Slice
  [`031`](../done-archive/031-modbus-adapter-review-folge.md)
  mit FC06-Guard und Fehler-Taxonomie umgesetzt);
  **Welle 4 `Done`** geschlossen 2026-05-31 mit C0 `7937e70`
  + C1 `74ed35b` + C2 `78fdd7a` (feat: `protocol_opcua/`-6-
  Modul-Paket + 81 Unit-Tests + 8 In-Process-Integration-
  Smokes + asyncua-Pin auf `>=1.2b2,<2.0` wegen Python-3.14-
  Inkompat in 1.1.8 + mypy-Override `implicit_reexport`)
  + C3 `7ad5baf` ([`ADR 0033`](../../adr/0033-opcua-adapter-profile.md) → `Provisional`, `M4-welle-4.md`
  → `Done`, Top-Level-Doku-Sync in 5 Docs) + Slice-032-
  Review-Folge 2026-05-31
  ([`../done/032-opcua-adapter-review-folge.md`](../done-archive/032-opcua-adapter-review-folge.md);
  6 HIGH + 11 MEDIUM Code-Review-Findings adressiert:
  Lifecycle-Lock + Start-Timeout in `OpcuaLoopThread`,
  Port-Exception-Filter um `RuntimeError`/`CancelledError`,
  Quality.INVALID fuer String-Reads, Float32-Quantisierung,
  Pin-Range, Smoke-Server-`asyncio.Event`) + Nachzug
  `1c2dfa3` (3 Findings: Node-ID-Integer-Check, Codec-
  Overflow-Wrap, Doku-Drift) + Self-Close-Move `3bc015b`
  (`M4-welle-4.md` aus `in-progress/` nach `done/`));
  **Welle 5 Sub-Slicing** in 5a/5b nach Library-Recherche
  (`8f022a3` + Pre-C0-Sync `34e64e6`); **Welle 5a `Done`**
  geschlossen 2026-05-31 mit C0 `43d0b07` + C1 `b0fea7e`
  ([`ADR 0034`](../../adr/0034-dnp3-adapter-profile.md) Proposed nach zwei C1-Probes — `nfm-dnp3`-Master-
  API-Inspektion + `dnp3-outstation`-Wire-Compat-Probe) +
  C2 `224b370` (feat: `protocol_dnp3/`-5-Modul-Paket + 56
  Unit-Tests inkl. hypothesis-Codec-Properties + 4 In-
  Process-`dnp3-outstation.AsyncOutstation`-Smokes + Pin
  `nfm-dnp3>=1.0,<2.0` produktiv und `dnp3-outstation>=0.2,<1.0`
  als dev-only Test-Sibling + mypy-Overrides + C2-Library-
  Bug-Find: `AnalogInput.index` statt `.idx` aus `__repr__`)
  + C3 `6903a08` ([`ADR 0034`](../../adr/0034-dnp3-adapter-profile.md) → `Provisional`, `M4-welle-5a.md`
  → `Done` mit Liefer-Hashes + DoD-Verifikation + §9 DoD-
  Checkliste komplett abgehakt, Top-Level-Doku-Sync in 5
  Docs) + Self-Close-Move `9fea2be` (`M4-welle-5a.md` aus
  `in-progress/` nach `done/` als M4-Welle-5b-Pre-C0,
  rename-only); **Welle 5b `Done`** geschlossen 2026-06-01
  mit C0 `19f820a` (Slice-Doc) + C1 `88c1a33` ([`ADR 0035`](../../adr/0035-iec61850-adapter-profile.md)
  Proposed) + C1-Review-Folge `da8aed9` (API-Korrektur
  read_value/write_value + Lizenz-Refit Optional-Extra +
  M4-protocol-adapters.md-Sync nach 4 Findings) + C2
  `944bca5` (feat: `protocol_iec61850/`-5-Modul-Paket inkl.
  ImportError-Guard fuer Optional-Extra + 75 neue Unit-
  Tests inkl. hypothesis-Codec-Properties + Integration-
  Smoke unter **2c-Mock-only-Fallback** aktiv + NEU
  `LICENSES/GPL-3.0.txt` + LICENSE-Hinweis-Block + READMEs-
  Lizenz-Sektion + SPDX-Header in 11 Files + NEU
  `tests/integration/fixtures/iec61850/simpleIO.cfg`
  libiec61850-natives CFG-Modell + `pyproject.toml`-Pin
  `pyiec61850-ng>=1.6,<2.0` als `[project.optional-dependencies.iec61850]`
  opt-in + mypy-Override + `Dockerfile`-`uv sync --extra iec61850`
  + `CRITICAL_COV_TARGETS`-Erweiterung +
  `compose.yml`-Header-Sync; **erstmaliger Repo-Praezedenzfall**
  fuer GPL-isolierte Sub-Module in einem sonst MIT-Projekt;
  Probe-Run auf Python 3.12 lief Float/Int32/String-
  Roundtrip sauber durch, aber grid-gym-Docker Python 3.14
  segfaultet im `_pyiec61850.so`-SWIG-Layer — Welle-6-
  Schaerfungspfade dokumentiert) + C3 `ca96bca`
  ([`ADR 0035`](../../adr/0035-iec61850-adapter-profile.md) → `Provisional`, `M4-welle-5b.md` → `Done` mit
  Liefer-Hashes + DoD-Verifikation + §9 DoD-Checkliste
  komplett abgehakt, Top-Level-Doku-Sync in 5 Docs) +
  **Slice 033 `7e0c91b`** (C2-Review-Folge: 15 Findings
  10 HIGH + 5 MEDIUM aus 5-Angle-Code-Review adressiert ohne
  ADR-Status-Aenderung — Sentinel-Exception-Klasse statt
  `Exception`-Alias im Optional-Extra-Off-Pfad,
  `_PyIecMMSError`-Catch-All in `start()`, `stop()`
  State-Mutation NACH `disconnect()`, NaN/Inf-Reject +
  int-Reject in `_decode_float`, Container-Check gated auf
  non-string-Datatype, NEU `Iec61850PortReadConnectionLostError`
  fuer mid-flight-NotConnected, Config-Anti-Scope-write-Reject
  bei Konstruktion, `TelemetryPoint.value`-Decimal-Wrap mit
  `Quality.INVALID`-String-Fallback Welle-4-Pattern,
  Sub-Millisekunden-Timeout-Floor, `Dockerfile`-`build-app`-
  Stage `--extra iec61850`-Propagation, `simpleIO.cfg`-SPDX-
  Header + Derivative-Work-Attribution zu libiec61850/MZ
  Automation, `pyproject.toml`-GPL-Classifier ergaenzt) +
  Self-Close-Move `30860ed` (`M4-welle-5b.md` aus
  `in-progress/` nach `done/` als M4-Welle-6-Pre-C0,
  rename-only); **Welle 6 Sub-Slicing** in 6a/6b nach
  Welle-5b-Erbschaft (`838d904`); **Welle 6a `Done`**
  geschlossen 2026-06-01 mit C0 `9776dd9` (Slice-Doc) +
  C1 `9312239` (Adapter-Profil-Index unter
  `spec/protocol_profiles.md` mit 5 Adapter-Eintraegen +
  Lastenheft-§16 `✅ M4` x 5 + Architektur-§8.2 OTel-Wrap-
  Pattern-Forward-Pointer) + C2 `9d3912f` (OTel-Span-Wrap
  fuer alle 5 protocol_*-Adapter via
  `OtelSpanWrappedDeviceProtocolPort`-Composition-Wrapper
  mit Standard-Attributen `adapter_type`/`target`/
  `operation`/`latency_ms`; Adapter-Code-Diff NULL) +
  Pre-C3 `81140e2` (git mv trigger-006 → done/, rename-
  only) + C3 `0a5e895` (NEU
  `test_arch_check_planted_violator.py` mit 7 Tests fuer
  Welle-1-§7-Folge-Pflicht-Closure + `[tool.mypy]
  strict_bytes = true` Aktivierung mit Trigger-006-Closure
  + `compose.yml`-Header-Konsolidierung mit 2-Tabellen-
  Sibling-Inventar + Trigger-004-Re-Eval-Defer auf M5/M6)
  + C4 `69b37f1` (Status/DoD-Sync) + **Slice 034 `bde8fdb`**
  (Review-Folge: 1 HIGH + 6 MEDIUM + 4 LOW-MEDIUM + 4 LOW
  Findings adressiert; F13 als Welle-6b-Vorlauf-Item) +
  Hash-Sync `b6a778d` + **Self-Close-Move `d1cb65d`** als
  M4-Welle-6b-Pre-C0 (rename-only) + Pre-C0-Sync `7b0e3e4`.
  1537 → 1566 Unit-Tests (+29 unique mit 19 OTel-Span-Wrap
  inkl. Slice-034-Fixes + 6 Planted-Violator + 4 Slice-034-
  Adapter-Tests). **Welle 6b (IEC-61850-Lizenz-und-Smoke-
  Hardening) abgeschlossen 2026-06-01** mit C0 `14d1bcb`
  (Slice-Doc) + C1 `8947c62` (NEU `tools/check_spdx.py` +
  10. A-1-Gate `make spdx-check`; 11 GPL-Boundary-Files
  Lint-clean) + C2 `9e2bf39` (NEU `AC-IEC61850-GPL-
  BOUNDARY`-arch_check-Contract, 19 → 20 KEPT;
  AST-Import-Scan ueber MIT-Code) + C3 `2539574`
  (IedServer-Smoke-Probe Pfad-A-Befund: PyPI-Stand
  identisch zu Welle 5b, kein cp314-Manylinux-Wheel
  → Pfad C aktiv mit Trigger 009; plus Slice-034-F13-
  Coverage-Schaerfung `_is_adapter_lightweight_path`
  erweitert um `_protocol_*.py`-Cross-Adapter-Helper)
  + C4 (dieser Commit; Status/DoD-Sync + NEU
  `CONTRIBUTING.md` mit Dual-License-Policy). 1566 →
  1584 Unit-Tests (+18 unique: 9 SPDX-Lint + 8 GPL-
  Boundary-Property + 1 F13-Cross-Adapter-Helper-
  Positiv). 10/10 A-1-Gates gruen (NEU 10.
  `spdx-check`); 20/20 Contracts KEPT (NEU 14.
  `AC-IEC61850-GPL-BOUNDARY`).
- **Aktiver Slice: keiner — Post-MVP-Trigger-Watch** (M7
  MVP-Abschluss abgeschlossen 2026-06-12,
  [`../done/M7-results.md`](../done/M7-results.md); M6 Performance +
  Security + CI/CD-Haertung abgeschlossen 2026-06-08). M5-Closure
  2026-06-04 mit Welle-7-Hash-Stack
  `c28a11b`/`62f988d`/`5087c8a`/`9978e21`/`e21795f`/
  `667be09`/`015eada`; M5-Slice-Plan und alle 10 Welle-
  Docs in [`../done/`](../done/). Historischer Aktive-
  Slice-Stand (M5-Welle-4b-Closure 2026-06-02) per
  Welle-Closure-Erbschafts-Narrativ unten erhalten.
  Welle 4b 2026-06-02 mit `b7ac7b3` + C3 `4dca6aa` +
  Review-Folge `52afd1a`/`fe1db21`/`ced9661`/`1fba165`
  — 15 Findings adressiert.
  **Welle 5 (Demo-Pipeline + Scenario-Loader-Wiring)
  abgeschlossen 2026-06-03** mit Pre-C0a `a030c0e` +
  Pre-C0b `45335eb` + C0 `155c421` (Slice-Doc +
  Decisions 5/6/18 final) + C2 `904ef47` (Code-Merge:
  NEU `deploy/scenarios/gg-demo.yaml` + NEU
  `__main__.py` + NEU produktiver
  `InMemoryRunRepository` + NEU
  `_demo_scenario_setup.py` + `app.py`-Lifespan-env-
  var-Branch + NEU `make demo`/`demo-stop` + NEU
  Welle-5-Smoke + Decision-18-Praezisierung in
  `compose.yml` per Service-Konfiguration +
  `GG-DEMO-008`-Defer auf Welle 6) + Doku-Sibling-
  Stack `5ab0f67`/`64c0fd9`/`5fe5082` + C3
  `61f5156` (Status/DoD-Sync + §10 C2-Realization-
  Notes) + C4a `da8d728` (Self-Close-Move) +
  C4b `2c9d8da` (Cross-Doc-Refs-Sync, 5 Refs) +
  Review-Folge `0e2bc41` (high-effort `/code-review`
  → 15 Findings W5-F1..F15 adressiert: TickLoop-
  Telemetry-Publish + Validation-First-Reorder +
  Decimal-Coercion-Wrap + Lifespan-Sentinel +
  Driver-Already-Configured-Guard + path.is_file-
  Check + tick_interval_s=min(...) +
  __main__-Path-Resolution + Makefile-Wait-Timeout +
  dynamisches _reset_app_state). Lastenheft-Akzeptanz
  `GG-DEMO-001..005 + 007` produktiv; `GG-DEMO-006` +
  `GG-DEMO-008` Anti-Scope-Forward-Pointer auf
  Welle 6.
  **Welle 6 ist per Welle-6a-C0 (2026-06-03) sub-
  gesliced** in 6a (Fault-Flow) + 6b (UI-
  Visualization) + 6c (Abnahmedoku); pro Sub-Slice
  eigener Slice-Doc. Pattern analog M4-Welle-6 →
  6a/6b.
  **Welle 6a (Fault-Flow: UI-Form-Validation + YAML-
  Fault-Demo) abgeschlossen 2026-06-03** mit C0
  `1d6d85e` (Slice-Doc
  [`M5-welle-6a.md`](../done-archive/M5-welle-6a.md) + Sub-
  Slicing-Beschluss + Decisions 19/20 final) + C2
  `db3a0c2` (Code-Merge: YAML-faults +
  `_compose_fault_port` Battery+Grid-Composition + UI-
  Faults-Page mit HTMX-Form + `routes_faults.py`-Split
  [`AC-NO-GOD-UTILS`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) + Cross-Field-Validation im POST-
  Handler + `tick_loop.device_types`-Property + 7
  Integration-Tests + Welle-1-Test-Refactor) + C3
  `ed8fa74` (Status/DoD-Sync + §10 C2-Realization-
  Notes) + C4a `70fb82c` (Self-Close-Move) +
  C4b `b19aeae` (Cross-Doc-Refs-Sync, 8 Refs) +
  Review-Folge `1e3a793` (high-effort `/code-review`
  → 15 Findings F1..F15 adressiert). Lastenheft-Akzeptanz
  `GG-UI-007` + `GG-DEMO-006` produktiv;
  Welle-5-Anti-Scope-Aufnahme erfolgreich (Battery-
  cell_failure-Auto-Alarm bleibt Welle-6+/M3-Welle-2-
  Hardening-Material — Slice-Doc §10.1).
  **Welle 6b (UI-Visualization: `GG-UI-006` Geraete-
  Grafik + `GG-UI-008` Sim-Zustand-Dashboard)
  abgeschlossen 2026-06-04** mit C0 `efc2c10` (Slice-
  Doc [`M5-welle-6b.md`](../done-archive/M5-welle-6b.md) + Decisions
  21/22/23 final) + C2 `9fcb887` (Code-Merge: NEU
  `GET /runs/{id}/devices/state` JSON-Surface in
  `_runs_router.py` + NEU `DevicesResponse`/
  `DeviceStateEntry`-Pydantic-Modelle + NEU
  `_aggregate_quality`/`_extract_state_subset`-Helper
  + NEU `routes_visualization.py`-Modul-Split
  `AC-NO-GOD-UTILS` analog Welle-6a `routes_faults.py` + NEU
  UI-Pages `/runs/{id}/devices` (HTMX-1s-Polling-
  Tabelle) + `/runs/{id}/system` (HTMX-Polling auf
  /status 1s + /health 5s) + 4 Templates + Navigation
  + 13 Integration-Tests + 15 Unit-Tests) + C3
  `580b2f0` (Status/DoD-Sync + §10 C2-Realization-
  Notes) + C4a `b30280e` (Self-Close-Move) + C4b
  `3a6f150` (Cross-Doc-Refs-Sync, 6 Refs) + **Review-
  Folge `cd7cfc6`** (high-effort `/code-review` →
  15/15 Findings F1..F15 adressiert; XSS-Haertung
  DOM-API + textContent, Pre-init-silent-drop, .get()-
  Quality-Fallback, truthy-coerce Fault-Flags, NEU
  public `tick_loop.devices` Property, NEU
  `_require_run_or_404`-Helper + `is_htmx_request` in
  `_templates.py`, `QUALITY_SEVERITY` nach
  `core/domain/quality.py`). 1696 → 1722 Unit-Tests
  (+26); 64 → 80 Integration (+16). Lastenheft-
  Akzeptanz `GG-UI-006 + GG-UI-008` produktiv.
  **Welle-6b-Realization-Notes** (Slice-Doc §10):
  JSON-URL wandert auf `/runs/{id}/devices/state`-
  Sub-Pfad (UI-Page behaelt natuerliche URL; Pattern
  analog Welle-4b-Alarms `/alarms-history`); Adapter-
  internes `_DeviceView`-Protocol haelt
  [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)
  ein. Decision 23: Chart.js bleibt (kein
  Plotly/ECharts-Spike).
  **Welle 6c (Abnahmedoku `GG-DEMO-008`) abgeschlossen
  2026-06-04** mit C0 `3db9fcd` (Slice-Doc
  [`M5-welle-6c.md`](../done-archive/M5-welle-6c.md)) + C2 `0e604e4`
  (NEU `docs/user/gg-demo-008-abnahme.md` mit
  6-Schritt-Abnahmereihenfolge per `GG-DEMO-008`
  Lastenheft §24; Top-Level-Doku-Sync + Status-Block-
  Kompression auf User-Feedback) + C3 (dieser Commit;
  Status/DoD-Sync + Welle-6-Subdivision-Abschluss-Note).
  Ausstehend: C4a Self-Close-Move + C4b Cross-Doc-Refs-
  Sync. Test-Counts unveraendert (1722/80; reiner Doku-
  Slice). Welle-5-Anti-Scope-Erbschaft `GG-DEMO-008`
  aufgeloest; letzte Welle-6-Sub-Slice.
  **Welle-6-Subdivision komplett 2026-06-04** (6a
  Fault-Flow + 6b UI-Visualization + 6c Abnahmedoku;
  drei Sub-Slices analog M4-Welle-6 → 6a/6b-Pattern).
  **Welle 7 (M5-Closure) eroeffnet 2026-06-04** mit C0
  (Slice-Doc [`M5-welle-7.md`](../done-archive/M5-welle-7.md); Pattern
  analog M4-Welle-7). Welle-7-Substanz: 5 M5-ADRs
  (0036..0040) `Provisional → Accepted` (C1), NEU
  `done/M5-results.md` mit Welle-Tabelle/Abnahme-Belegen/
  S-1..S-6-Sweep (C2), `roadmap.md §4 M5` DoD-Checkboxen
  + M5 auf `Done` + „Aktiver Slice: M6" (C3),
  Self-Close-Move `M5-ui-demo.md` + `M5-welle-7.md` →
  `done/` (C4a/b). Welle 7 hat keinen Code-Diff, keine
  neuen Tests, keine neuen ADRs (nur Status-Flips).
- **ADRs:** 0022/0023/0024/0025/0026/0027 `Accepted` (M3-Welle-7
  C1.1..C1.6); 0028 + 0029 `Accepted` (Schaerfung-ohne-Supersede-
  Pflege von [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §3 bzw. [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §A-1); **0030 `Accepted`**
  (M4-Welle-1 `DeviceProtocolPort`-Surface; `Accepted`
  2026-06-01 mit M4-Welle-7-C1); **0031 `Accepted`** (M4-Welle-2
  MQTT-Adapter-Profile mit Decisions 4a/4b/4c/4d alle final;
  `Accepted` 2026-06-01 mit M4-Welle-7-C1 `d2071f0`); **0032 `Accepted`**
  (M4-Welle-3 Modbus-TCP-Adapter-Profile mit Decisions
  M-a/M-b/M-c/M-d/M-e/M-f alle final — inline Register-Schema,
  5 Datatypes mit Byte-Order-Matrix, direkt-sync ohne
  Thread-Marshal, FC03/FC10-Defaults, Slave-Unit-ID per Target,
  in-process pymodbus-Server-Smoke; `Accepted` 2026-06-01 mit
  M4-Welle-7-C1). Review-Folge
  [`031`](../done-archive/031-modbus-adapter-review-folge.md)
  hat FC06-Multi-Register-Guard, Read-/Write-
  Fehler-Taxonomie und bewusste Smoke-Abgrenzung
  umgesetzt. **0033 `Accepted`** (M4-Welle-4 OPC-UA-
  Adapter-Profile mit Decisions O-a/O-b/O-c/O-d/O-e alle
  final — inline Node-ID-Schema, Async-Bridge via
  `OpcuaLoopThread` (erstes Repo-Pattern dieser Art),
  8-Datatype-Set, Polling-Read + Direct-Write, in-process
  `asyncua.Server`-Smoke; `Accepted` 2026-06-01 mit
  M4-Welle-7-C1). **0034 `Accepted`** (M4-Welle-5a
  DNP3-Adapter-Profile mit Decisions D-a/D-b/D-c/D-d/D-e
  alle final — inline Point-Schema mit
  Group/Variation-Allowlist `{(1,1),(1,2),(30,1),(30,5)}`,
  zwei-Library-Setup `nfm-dnp3` produktiv +
  `dnp3-outstation` dev-only, direkt-sync wie Modbus,
  Class-0-Integrity-Poll + filter-by-index, write-Pfad
  Welle-5b-Anti-Scope; `Accepted` 2026-06-01 mit
  M4-Welle-7-C1). **0035 `Accepted`** (M4-Welle-5b IEC-61850-
  Adapter-Profile mit Decisions I-a/I-b/I-c/I-d/I-e/I-f
  alle final — inline LN/CDC-Schema mit FC-Allow-List
  `{MX,ST,SP,CF,DC}` und Datatype-Allow-List
  `{bool,int32,float,string}`, eine-Library-Setup
  `pyiec61850-ng` als Optional-Extra
  `[project.optional-dependencies.iec61850]`, direkt-sync
  wie Modbus + DNP3, Per-Target MMS-Read mit FC-Override,
  in-process IedServer mit CFG-Fixture als Test-Sibling
  **mit 2c-Mock-only-Fallback aktiv** (Python-3.14-SWIG-
  Inkompat), **NEU Decision I-f Lizenz-Boundary** GPLv3-
  Isolation auf `protocol_iec61850/*` per SPDX-Header
  (erstmaliger Repo-Praezedenzfall fuer GPL-isolierte Sub-
  Module in einem sonst MIT-Projekt); `Accepted` 2026-06-01
  mit M4-Welle-7-C1). **M5-ADRs:** **0036 `Provisional`**
  (Pre-M5-Welle-0 UI-Stack-Choice — FastAPI + HTMX + Jinja2
  + Chart.js; Maintainer-Decision in M5-Welle-0); **0037
  `Provisional`** (M5-Welle-1 HTTP-API-Surface-Pattern;
  Decision API-3 verwirft `UICommandPort`-Slot
  `GG-AR-PORT-DRG-002` zugunsten direkter REST+WS-Nutzung);
  **0038 `Provisional`** (M5-Welle-3 TelemetryStreamPort);
  **0039 `Provisional`** (M5-Welle-4a Run-Control +
  RunStatus-Tracking); **0040 `Provisional`** (M5-Welle-4b
  Alarm-Aggregation + AlarmStreamPort). `Accepted` geplant
  mit M5-Welle-7-Closure.
- **Tests:** 1696 Unit + 51 Integration passed + 4 skipped
  (Stand nach M5-Welle-4b-Closure inkl. Review-Folge; +112
  Unit ggue. M4-Welle-6b: +16 Welle 1 HTTP-API + +10 Welle 2
  UI-Foundation + +16 Welle 3 Live-Telemetry + +24 Welle 4a
  Replay-Controls + +31 Welle 4b Alarm-Aggregation + +15
  Welle-4b-Review-Folge. +16 Integration: +2 Welle 1 +
  +2 Welle 2 + +6 Welle 3 + +1 Welle 4a + +1 Welle 4b. M4-
  Closure-Snapshot ist die Basis-Linie: 1584 Unit + 35
  passed + 4 skipped Integration nach M4-Welle-6b; +441 Unit
  ggue.
  M3-Closure [+23 Welle 1 + +50 Welle 2 + +95 Welle 3 +
  +8 Review-Folge 031 + +81 Welle 4 fuer OPC-UA + +6
  Slice-032 fuer Loop-Thread-Lifecycle/Marshal-Pfad/
  String-Read-Quality.INVALID/Float32-Quantisierung +
  +56 Welle 5a fuer DNP3 + +75 Welle 5b fuer IEC-61850
  + +29 Welle 6a fuer Cross-Adapter-Hardening inkl. Slice
  034 (19 OTel-Span-Wrap-Tests inkl. F1/F2/F3-Negativ-
  Tests + 6 [`AC-ADAPTER-LIGHTWEIGHT`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Planted-Violator-Tests
  + 4 Slice-034-Adapter-Tests + 7 Slice-033-Review-Folge-
  Updates)] + 14 Integration-Tests [Mosquitto-MQTT-Smoke
  aus Welle 2 + in-process-pymodbus-Server-Smoke aus
  Welle 3 + 8 in-process-`asyncua.Server`-Smokes aus
  Welle 4 + 4 in-process-`dnp3-outstation.AsyncOutstation`-
  Smokes aus Welle 5a (3 Class-0-Read-Roundtrips +
  1 Update-then-Read); Welle-5b-IEC-Smokes via
  `pytest.mark.skip` mit 2c-Fallback-Begruendung
  inaktiv — Probe-Run auf Python 3.12 lief sauber durch,
  aber grid-gym-Docker Python 3.14 segfaultet im
  `_pyiec61850.so`-SWIG-Layer; Welle-6b-Reaktivierungs-
  Probe steht aus]).
- **Build:** `make gates` cache-frei gruen ohne Override
  (10 A-1-Gates inkl. `spdx-check` aus M4-Welle-6b).
  `make fullbuild` war von M6-Welle-1-C2 `b514170`
  (2026-06-05) bis M6-Welle-3-Post-Push `0891f65`
  (2026-06-05) cache-frei gruen; **aktuell wieder in
  Defer-Pfad** wegen CVE-2026-42504 (Go-stdlib MIME-
  Header-DoS) im `otel/opentelemetry-collector-
  contrib:0.153.0`-Sibling. Aufgedeckt durch Trivy-
  Host-Cache-Mount-Entfernung `ede21ad` (Stale-DB-Drift-
  Aufloesung). Trigger 033
  ([`../open/033-otel-collector-go-stdlib-cve-bump.md`](../open/033-otel-collector-go-stdlib-cve-bump.md))
  als [`ADR-0043`](../../adr/0043-image-audit-strategy.md)-konformer Defer-Pfad; Aufloesung sobald
  OTel-Release > 0.153.0 gegen `go1.26.4+` gebaut ist
  (erwartet 2026-06-09..06-12). Trigger 010 (krb5-CVE)
  bleibt aufgeloest seit Welle-1-C2; [`ADR 0043`](../../adr/0043-image-audit-strategy.md)
  `Provisional` verankert die Image-Audit-Strategie als
  Quality-Gate-Vertrag.
- **Trigger-006-Re-Eval (M4-Welle-3-C3, 2026-05-30):**
  positiv. `mypy --strict-bytes` laeuft cache-frei gruen gegen
  `src/grid_gym/adapters/driven/protocol_modbus/` ohne
  zusaetzliche `# type: ignore`-Inflation (bestehende 2
  `# type: ignore[no-untyped-call]` in `_port.py:128/148`
  sind pymodbus-API-spezifisch, kein bytes-Bezug). Trigger
  ist aktivierungs-reif; Aktivierung selbst ist Folge-Slice
  (`[tool.mypy] strict_bytes = true` plus Sweep-Pruefung).
- **Contracts:** 20 A-1 (6 lint-imports + 14 `tools/arch_check.py`
  inkl. `AC-OTLP-ADAPTER-NO-TIME`, `AC-TICK-LOOP-PRIVATE-
  RESUME-ERRORS` und NEU `AC-IEC61850-GPL-BOUNDARY` aus
  M4-Welle-6b; `AC-NO-IO-MOD` ist in beiden Tools enforced
  und zaehlt als ein logischer Contract — kanonische
  Konvention per [`../done/M4-results.md`](../done/M4-results.md));
  `AC-ADAPTER-LIGHTWEIGHT` erfasst `protocol_*`
  weiter via `tools/arch_check.py:1089` (Regression-Schutz in
  Welle-1-C2 verifiziert, in Welle 2 + 3 produktiv bestaetigt;
  Welle-6b-C3 erweitert den Filter um Cross-Adapter-Helper
  `_protocol_*.py` per Slice-034-F13-Folge).

**Bezug:** [Lastenheft](../../../../spec/lastenheft.md), [Architektur](../../../../spec/architecture.md)

---

## 1. Zweck

Diese Roadmap fuehrt die Meilensteine, die sich aus dem Lastenheft und
der Architektur ergeben. Sie ist die Quelle fuer die Status-Spalte
der `GG-TRACE-001`-Implementierungsmatrix
([Lastenheft §27.2](../../../../spec/lastenheft.md#272-anforderung-zu-implementierung))
mit `M[N]`-Markern. §3 (MVP-Abnahmescope) liefert die
Stakeholder-Sicht auf `GG-MVP-001..004`; §4 die
Meilenstein-Detail-Sicht; §5 die `GG-AR-OPEN-*`-
Vorbedingungen.

`GG-AR-OPEN-001` (Sprach- und Build-Wahl) ist mit `ADR 0002`
(`Accepted` 2026-05-15) geschlossen. M1 (Tick-Loop-Spine) ist seit
2026-05-17 `Done` — Closure-Notiz in
[`done/M1-tick-loop-spine.md`](../done-archive/M1-tick-loop-spine.md) +
Welle-Tabelle in
[`done/M1-tick-loop-results.md`](../done/M1-tick-loop-results.md).
M2..M6 sind vorbelegt (Scope-Skizze hier, aktive Slice-Plaene
wandern bei Aktivierung nach `next/` bzw. `in-progress/`).
**M5 abgeschlossen 2026-06-04** (siehe
[`../done/M5-results.md`](../done/M5-results.md)). Aktiver
Slice: **M6 (Performance + Security + CI/CD-Haertung)** —
Vorbelegung in §3 M6; Slice-Plan entsteht in M6-Welle-0.
(M4 ist abgeschlossen,
siehe [`done/M4-results.md`](../done/M4-results.md).)

M2 ist abgeschlossen: Slice-Plan ist nach `done/` gewandert
([`done/M2-devices.md`](../done-archive/M2-devices.md)) inkl. Welle-7-Closure
([`done/M2-devices-results.md`](../done/M2-devices-results.md)).
M3 ist abgeschlossen: Slice-Plan ist nach `done/` gewandert
([`done/M3-faults-agents-observability.md`](../done-archive/M3-faults-agents-observability.md))
inkl. Welle-7-Closure
([`done/M3-results.md`](../done/M3-results.md)).

---

## 2. Konvention

- Meilensteine werden fortlaufend numeriert (`M1`, `M2`, …).
- Jeder Meilenstein hat:
  - **Lieferziel** (was wird umgesetzt),
  - **Lastenheft-IDs** (`GG-*`),
  - **Architekturartefakte** (`GG-AR-*`),
  - **DoD-Checkliste** (Markdown-Checkboxen, einzeln pruefbar),
  - **Status** (Pending / In Progress / Done).
- Abgeschlossene Meilensteine wandern als Closure-Notiz nach
  `docs/plan/planning/done/`.
- Themes fuer kommende Meilensteine werden in `docs/plan/planning/next/`
  als Scope-Skizze gefuehrt, sobald die Vorbelegung hier konkret wird.
- DoD-Checkboxen werden NICHT in der Roadmap abgehakt, solange der
  Meilenstein offen ist — die Closure-Notiz in `done/` traegt den
  finalen Stand.

---

## 3. MVP-Abnahmescope

Cross-cutting Abnahmekriterien aus Lastenheft §3 — Status-
Snapshot pro `GG-MVP-*`-ID. Diese Tabelle ist die
Stakeholder-Sicht; die einzelnen `GG-SIM/DEV/REPLAY/DEPLOY/
...`-IDs sind in §4 pro Meilenstein detailliert. Lastenheft-
Traceability §27.2 Z. 2205: `GG-MVP-001..004` ist
„Scope-Festlegung; Auspraegung lebt in einzelnen
`GG-SIM/DEV/...`-IDs" — diese Tabelle macht die Auspraegung
maschinenlesbar.

| ID | Akzeptanz (Lastenheft §3, Z. 123-150) | Stand 2026-06-07 | Substanz / Verankerung |
| --- | --- | --- | --- |
| **[`GG-MVP-001`](../../../../spec/lastenheft.md#gg-mvp-001)** | Lokaler Single-Node-Betrieb (API + UI + Simulationskern + Persistenz + Demo-Szenario via Docker Compose). | ✓ **produktiv** | `make demo` startet `deploy/compose.yml`-Stack (postgres + api + simulation-Stub + otel-collector); UI ist im `api`-Container (FastAPI-HTMX); Demo-Szenario `deploy/scenarios/gg-demo.yaml` via `GRID_GYM_DEMO_SCENARIO_PATH`. Welle-5c-Host-Bind-Hardening (`carveouts.md §2.7`). |
| **[`GG-MVP-002`](../../../../spec/lastenheft.md#gg-mvp-002)** | E2E-Szenario mit GridConnection + PV + Last + Smart Meter + Batteriespeicher; startet ueber API + Live-Telemetrie + Persistenz + deterministisches Replay. | ✓ **produktiv** | Szenario-Start (POST /runs) ✓ + Live-Telemetrie (WebSocket) ✓ + Laufmetadaten-Persistenz (`PostgresRunRepository`) ✓ + **Zeitreihen-Persistenz** ✓ (`TelemetrySinkPort` + `telemetry_points`, [`ADR 0047`](../../adr/0047-telemetry-sink-timeseries-persistence.md), M7-Welle-1a) + **deterministisches Replay-E2E** ✓ (`ReplaySnapshotPort` [`ADR 0048`](../../adr/0048-replay-snapshot-port-reconstruction.md) + Core-`TickLoop.finalize()`-Hook + `replay_diff_status` + `GG-TERM-002/003`-MVP-Preflight [`ADR 0049`](../../adr/0049-replay-lifecycle-finalize-hook.md), M7-Welle-1b; Zwei-Lauf-Beleg in `tests/integration/test_mvp_002_replay_lifecycle_smoke.py`; Audit `docs/user/replay-determinism-e2e.md`). Geliefert ueber M7-Welle-1 (1a + 1b-a + 1b-b); Trigger 036 aufgeloest. Carveouts: volle `GG-TERM`-Matrix (Trigger 038) + oeffentliche API-Replay-Bedienung (Trigger 039). |
| **[`GG-MVP-003`](../../../../spec/lastenheft.md#gg-mvp-003)** | CLI/Script fuer Abnahmepruefungen — ein Befehl fuehrt deterministische Replay-Pruefung + Szenario-Validierung + Demo-Healthcheck aus + liefert maschinenlesbaren Status. | ✓ **produktiv** | `make accept` + `tools/accept.py` (M7-Welle-2): orchestriert no-fail-fast Step A (Szenario-Validierung `load_scenario` + Hash-Pin) → B (Headless-Zwei-Lauf-Determinismus via `build_tick_loop` + `diff_replay` + Telemetry-Stream-Hash-Pin) → C (`/ready`-Healthcheck) und schreibt den `AbnahmeReport` (Pydantic-strict) als JSON-only-stdout mit Tri-State-Exit 0/1/2 (D-9). Geteilter `tools/_demo_replay.py`-Helper + CI-Drift-Lint `tools/check_demo_scenario_pin.py` (`make ci`-Gate, D-8). Doku `docs/user/abnahme-cli.md`. Geliefert M7-Welle-2 (commits `33ac255` + `92d10f5`). |
| **[`GG-MVP-004`](../../../../spec/lastenheft.md#gg-mvp-004)** | Demo offline ausfuehrbar (keine Cloud / kein Internet / keine realen Feldgeraete zur Laufzeit). | ✓ **produktiv** | `--no-pull`-Build-Pattern (Welle 0b/1); `deploy/compose.yml`-Services haben keine externen Cloud-Abhaengigkeiten; alle Adapter sind Container-intern oder Sibling-Compose; deckungsgleich mit `GG-DEPLOY-002` (Offline-MUSS) + `GG-DEPLOY-011` (Offline-Lauf-MUSS). |

**Aktivierungs-Pfade fuer offene Punkte:**

- **[`GG-MVP-002`](../../../../spec/lastenheft.md#gg-mvp-002) Zeitreihen-Persistenz + Replay-E2E** → **✓ geliefert
  ueber M7-Welle-1** (1a Persistenz / 1b-a `ReplaySnapshotPort` /
  1b-b Replay-Lifecycle; [`ADR 0047`](../../adr/0047-telemetry-sink-timeseries-persistence.md)/0048/0049). Trigger 036
  aufgeloest. Rest-Carveouts: volle `GG-TERM`-Matrix (Trigger 038),
  oeffentliche API-Replay-Bedienung (Trigger 039),
  `GG-REPLAY-004..006` (SOLLTE, offen).
- **[`GG-MVP-003`](../../../../spec/lastenheft.md#gg-mvp-003) Abnahme-CLI** → **✓ geliefert ueber M7-Welle-2**
  (`make accept` + `tools/accept.py` + Shared
  `src/grid_gym/scenario_yaml.py`; D-10-Revision C; commits
  `33ac255` + `92d10f5`). **Damit alle vier `GG-MVP-*`-Punkte
  produktiv** — offen im M7-Meilenstein bleibt nur die Safety-Closure
  `GG-SAFE-003/004` (M7-Welle-3, Trigger 034/035).

---

## 4. Meilensteine

### M1 — Tick-Loop-Spine (`Done`)

- **Lieferziel:** deterministischer Tick-Loop ohne Geraete:
  `ClockPort` (Driven), `RandomPort` (Driven, eigener ADR),
  Scheduler mit stabiler Tie-Breaking-Regel, Domain-Modelle
  (`Telemetry`, `Command`, `Event`, `Scenario`, `ReplaySample` als
  Frozen-Dataclasses), `canonical_json`-Anbindung an Snapshot-Pfad,
  minimaler FastAPI-Adapter + Postgres-Persistenz fuer `runs`.
  Geraetemodelle (Battery, PV, Load, ...) folgen in M2+.
- **Lastenheft-IDs:** `GG-SIM-001..005`, `GG-DATA-001..005`,
  `GG-ARCH-005..008`, `GG-PRINC-001..006`, `GG-SCN-001..008`,
  `GG-REPLAY-001..003`/`007`, `GG-API-001`/`003`,
  `GG-PERSIST-003`/`009` (minimaler `runs`-Repository).
- **Architekturartefakte:** `GG-AR-COMP-CORE`, `GG-AR-COMP-DOMAIN`,
  `GG-AR-COMP-SCHED`, `GG-AR-PORT-DRN-001` (`ClockPort`),
  `GG-AR-PORT-DRN-003` (`RunRepositoryPort`),
  `GG-AR-PORT-DRN-010` (`RandomPort` — via
  [`ADR 0007`](../../adr/0007-random-port.md)).
- **DoD-Checkliste:**
  - [x] Welle 0 — Vorbereitung ([`ADR 0007`](../../adr/0007-random-port.md) Provisional, Trigger 001,
        Lock-Refresh) (2026-05-15).
  - [x] Welle 1 — Domain-Modelle (`Quality`/`CommandResult`/
        `RunMetadata`/`TelemetryPoint`/`Command`/`Event`/
        `SnapshotEnvelope`) (2026-05-17).
  - [x] Welle 2 — Driven-Ports (`ClockPort`/`RandomPort` +
        `MersenneTwisterRandomPort` Adapter, [`ADR 0007`](../../adr/0007-random-port.md) Accepted)
        (2026-05-17).
  - [x] Welle 3 — Scheduler mit Tie-Breaking
        `(time, priority, source, sequence, event_id)` (`GG-ARCH-006`)
        (2026-05-17).
  - [x] Welle 4 — TickLoop + Snapshot-Envelope-Composition
        (`GG-SIM-005`, [`ADR 0010`](../../adr/0010-randomport-snapshot-as-mapping.md)) (2026-05-17).
  - [x] Welle 5 — Scenario + Replay (`GG-SCN-001..008`,
        `GG-REPLAY-001..003/007`) (2026-05-17).
  - [x] Welle 6a — FastAPI-Adapter + `make openapi-validate` gruen
        (2026-05-17).
  - [x] Welle 6b — `RunRepositoryPort` + `InMemoryRunRepository`
        + FastAPI-Wiring (2026-05-17).
  - [x] Welle 6c — `PostgresRunRepository` + alembic + Integration-
        Tests via testcontainers; Triggers 009 + 010
        (`tests/integration/compose.yml` + `deploy/compose.yml`)
        (2026-05-17).
  - [x] Welle 6d — `make fullbuild` gruen mit explizitem
        `CRITICAL_COV_TARGETS`-Override (Default-Gate haengt an
        M2-`devices/battery`, siehe Abnahme-Hinweis unten)
        (2026-05-17).
  - [x] Welle 7 — Closure-Notiz
        [`done/M1-tick-loop-spine.md`](../done-archive/M1-tick-loop-spine.md)
        + Welle-Tabelle in
        [`done/M1-tick-loop-results.md`](../done/M1-tick-loop-results.md);
        Triggers 009 + 010 nach `done/`, Trigger 015 (Production-
        Image-Hardening) in `open/` (2026-05-17).
  - [x] M1 als Ganzes auf Status `Done` gehoben und Slice-Plan
        nach `done/` gewandert (2026-05-17).
- **Abnahme-Hinweis:** Default-`make gates` (ohne
  `CRITICAL_COV_TARGETS`-Override) bleibt rot, solange
  `devices/battery` als Default-Critical-Target fehlt. Das ist
  per Slice-Plan-§3-Welle-4-§3-Welle-5-Doku erwartet — M1-DoD-
  Box „Welle 6d" akzeptiert den expliziten Override-Pfad als
  M1-Abschluss. Volle Default-Gruen-Linie schliesst M2 (siehe
  M2-DoD).
- **Status:** Done (2026-05-17) — Closure-Notiz
  [`done/M1-tick-loop-spine.md`](../done-archive/M1-tick-loop-spine.md),
  Welle-Tabelle
  [`done/M1-tick-loop-results.md`](../done/M1-tick-loop-results.md).

### M2 — Geraetemodelle

**Slice-Plan:** [`done/M2-devices.md`](../done-archive/M2-devices.md)
(Closure-Notiz); Welle-Tabelle + Abnahme-Belege:
[`done/M2-devices-results.md`](../done/M2-devices-results.md);
Welle-6c-Slice-Begleit:
[`done/welle-6c.md`](../done-archive/welle-6c.md).

- **Lieferziel:** produktive Geraetemodelle (Battery/BESS, PV,
  Load, Smart Meter, Grid Connection) als Konsumenten des
  Tick-Loops. `TickResult.emitted_telemetry` ist dann nicht mehr
  leer — Geraete emittieren `TelemetryPoint`-Tupel pro Tick.
  Geraete-Faults (mindestens Schnittstelle) und Snapshot-Versionierung
  pro Geraet.
- **Lastenheft-IDs:** `GG-DEV-001..014`, `GG-BESS-001..008`,
  `GG-GRID-001..007`. Plus Anschluss an
  `GG-SCN-001` (Geraete-Definitionen im Scenario werden produktiv
  konsumiert).
- **Architekturartefakte:** `GG-AR-COMP-DEVICES`, je Geraetetyp
  ein Submodul unter `hexagon/core/devices/`. `RandomPort.sub_port`-
  Konventionen fuer Geraete-Fault-Streams.
- **DoD-Checkliste:**
  - [x] `Battery`/BESS-Modell mit Lade-/Entlade-Vertrag
        (`GG-BESS-001..008`) — M2 Welle 2, [`ADR 0014`](../../adr/0014-battery-snapshot-schema.md) `Accepted`.
  - [x] `PV`-Modell — M2 Welle 3a, [`ADR 0016`](../../adr/0016-pv-load-device-pattern.md) `Accepted`.
        Welle-3-Minimum (konstantes `rated_power_kw`-Modell);
        Generationsprofil-Eingang ist Welle-5-Material.
  - [x] `Load`-Modell — M2 Welle 3b, [`ADR 0016`](../../adr/0016-pv-load-device-pattern.md) `Accepted`.
  - [x] `SmartMeter`-Modell — M2 Welle 4b (`94efb2a`),
        [`ADR 0018`](../../adr/0018-smart-meter-device-pattern.md) `Accepted`.
  - [x] `GridConnection`-Modell (`GG-GRID-001..007`) — M2 Welle 4a
        (`b73b44a`), [`ADR 0017`](../../adr/0017-grid-connection-device-pattern.md) `Accepted`.
  - [x] `TickLoop.tick()` ruft Geraete-`tick()`s in stabiler
        Reihenfolge auf; Telemetry-Sammlung pro Tick deterministisch
        sortiert — M2 Welle 6a (`27a441f`); Welle-6c (`c31052c`)
        pinnt die Determinismus-Pflicht zusaetzlich per
        Permutations-Property-Test + MVP-Demo-Determinismus-Run.
  - [x] Geraete-Snapshot-Sub-Snapshots in `SnapshotEnvelope`-
        Composition (Trigger 014 generischer Codec in Welle 0a
        geliefert — siehe `done/014-generic-snapshot-format-codec.md`)
        — M2 Welle 6a (`27a441f`), [`ADR 0015`](../../adr/0015-snapshot-envelope-v2.md) `Accepted`.
  - [x] Default-`make gates` ohne `CRITICAL_COV_TARGETS`-Override
        gruen — `devices/battery`, `devices/pv`, `devices/load`
        haben ≥ 90 % Line + Branch (Welle-3-Review-C-1 hat den
        Default-`CRITICAL_COV_TARGETS` um PV/Load erweitert).
  - [x] M1-DoD-Restposten (M1 Welle 6d/7) sind als
        `done/M1-tick-loop-spine.md` geschlossen — M1 ist seit
        2026-05-17 `Done`.
- **Status:** Done (2026-05-20). M2-Abschluss-Gate
  `make fullbuild` cache-frei gruen **ohne**
  `CRITICAL_COV_TARGETS`-Override seit Welle-6c-Feat
  (`c31052c`). Welle 7 (M2-Closure, 2026-05-20) hat
  `done/M2-devices.md` + `done/welle-6c.md` +
  `done/M2-devices-results.md` etabliert und 9 SOLLTE-Open-
  Trigger (`016..024`) in `open/` aktiviert.

**Aktiver Slice: keiner — Post-MVP-Trigger-Watch** (M7
abgeschlossen 2026-06-12; M6 abgeschlossen 2026-06-08).
**M5 ist `Done`** (2026-06-04,
siehe [`done/M5-results.md`](../done/M5-results.md)): 10
Wellen 0..6c geliefert (Sub-Slicing 4 → 4a/4b + 6 → 6a/6b/
6c); fuenf M5-ADRs (0036/0037/0038/0039/0040) auf
`Accepted`; `make gates` cache-frei gruen ohne Override
mit 10 A-1-Gates; 1722 Unit-Tests + 80 passed + 4 skipped
Integration-Tests; Lastenheft-Scope `GG-API-001..004` +
`GG-UI-001..009` + `GG-DEMO-001..008` alle erfuellt.
**`make fullbuild`** war zur M5-Closure noch pre-existing
rot wegen krb5-CVE-Drift (M4-Welle-7-Erbschaft Trigger
010; nicht durch M5 verursacht); **aufgeloest in M6-Welle-
1-C2 `b514170` (2026-06-05) ohne Code-Edit** durch
Debian-13.5-Upstream-Drift + Trigger-015-Pattern. M4 ist `Done` (2026-06-01,
siehe [`done/M4-results.md`](../done/M4-results.md)): 9
Wellen 0..6b geliefert (5 produktive Adapter + 2 Cross-
Adapter-Hardening-Wellen); sechs M4-ADRs (0030/0031/0032/
0033/0034/0035) auf `Accepted`; `make gates` cache-frei
gruen ohne Override mit 10 A-1-Gates inkl. NEU
`spdx-check`; 1584 Unit-Tests + 35 passed + 4 skipped
Integration-Tests; 20 A-1-Contracts (14 arch_check inkl.
NEU `AC-IEC61850-GPL-BOUNDARY`). `make fullbuild`
war zur M4-Closure noch pre-existing rot wegen krb5-CVE-
Drift seit M3-Welle-7-`c61ab0d` (nicht durch M4 verursacht;
Base-Image-Bump als M5-Welle-0-Trigger); aufgeloest in
M6-Welle-1-C2 `b514170` (2026-06-05) ohne Code-Edit
(Debian-13.5-Upstream-Drift; siehe
[`../done/010-base-image-krb5-cve-bump.md`](../done-archive/010-base-image-krb5-cve-bump.md)). M3 ist `Done` (2026-05-25,
siehe [`done/M3-results.md`](../done/M3-results.md)): drei Sub-
Bereiche (Faults, Multi-Agent, Observability) ueber Welle 0..7
geliefert; sechs M3-ADRs (0022/0023/0024/0025/0026/0027) auf
`Accepted`; `make fullbuild` cache-frei gruen ohne Override mit
OTLP-Collector-Sibling; **bei M3-Closure 1138 Unit-Tests + 21
Integration-Tests**; 96 % Total-Coverage; 19 A-1-Contracts
(M3-Closure-Stand: in M3-Doku als „6 import-linter + 13
arch_check" beschrieben; tatsaechlicher Split ueber alle M3+M4-
Wellen hinweg: **7 lint-imports + 12 `tools/arch_check.py`** =
19, siehe Welle-1-Linter-Folge `82f947c`).

### M3 — Faults + Multi-Agent + Observability (`Done` 2026-05-25)

- **Lieferziel:** produktive Fault-Injection (`GG-FAULT-001..010`),
  Multi-Agent-Subsystem (`GG-AGENT-001..008`) und
  OpenTelemetry-Anbindung (`GG-OTEL-001..004`).
- **Lastenheft-IDs:** `GG-FAULT-001..010`, `GG-AGENT-001..008`,
  `GG-OTEL-001..004`, `GG-SAFE-001..006` (sicherheitsrelevante
  Pfad-Kennzeichnung der Fault-Klassen).
- **Architekturartefakte:** `GG-AR-COMP-FAULTS`,
  `GG-AR-COMP-AGENTS`, `GG-AR-PORT-DRN-008`
  (`LogPort`/`MetricsPort`/`TracePort`).
- **DoD-Checkliste:**
  - [x] Fault-Definitions im Scenario werden vor `tick()` validiert
        (`GG-SCN-006`) und im Tick-Loop ausgeloest
        (M3-Welle-1 + Welle-2: [`ADR 0022`](../../adr/0022-fault-injection-protocol.md) + [`ADR 0025`](../../adr/0025-fault-recovery-pattern.md)).
  - [x] Mindestens ein konkreter Fault-Typ pro
        `Battery`/`Grid`-Achse implementiert: Battery
        `cell_failure` + Grid `voltage_drop` (M3-Welle-2-Closure
        `91d44e2`).
  - [x] Recovery-Verhalten je Fault dokumentiert + getestet:
        `auto-recover-after-N-ticks` + `manual-via-command`
        ([`ADR 0025`](../../adr/0025-fault-recovery-pattern.md) §2.1; Property-Tests fuer half-open
        `[start, end)`-Window + Unit-Tests fuer manuelle
        Recovery; `permanent`-Modus auf Welle 3+/M6 verschoben).
  - [x] Multi-Agent-Bus implementiert (`GG-AGENT-001..006`):
        Foundation (Welle 3: `Agent`-Protocol + `AgentMessageBus` +
        `AgentMessage` + TickLoop-Schritt-D2-Hook + Pending-Buffer),
        Foundation-Plumbing (Welle 4a: produktive
        `agents`-Registry + Schritt-A0v/A0a-Drain +
        `_attach_agents()`-Lifecycle + `consume_for(...)` +
        Foundation-State-Snapshot) und Konkretisierung (Welle 4b:
        `RuleBasedAgent` mit Hybrid Rules + Plugin-Hook +
        Scenario-`agents`-Top-Level-Block (nested Mapping) +
        bidirektionaler `agents.<type>.<id>`-Sub-Snapshot-Resume-
        Match + End-to-End-Demo `tests/integration/scenarios/
        agents_demo.yaml`) sind `Done`. `GG-AGENT-007` Deadlines
        und `GG-AGENT-008` Async bleiben Welle-4c+/M5-Material;
        RL-Adapter (`GG-FUTURE-001/002`) bleiben Folge-Slice.
  - [x] `LogPort`/`MetricsPort`/`TracePort` mit OTLP-Adapter
        (M3-Welle-5 Foundation + M3-Welle-6 OTLP-Adapter; ADR
        0024 `Accepted` mit M3-Welle-7-C1.3 `d13e1f3`).
  - [x] Property-Tests fuer Fault-Determinismus
        (gleicher Seed + Fault-Sequenz → gleicher Telemetry-Export)
        in M3-Welle-2: Hypothesis-half-open-Window + Per-Seed-
        Determinismus + Welle-2-Seed-Independence.
  - [x] Default-`make gates` ohne `CRITICAL_COV_TARGETS`-Override
        gruen — Default-Liste um `core/faults`, `core/agents`,
        `adapters/driven/telemetry_otlp` erweitert (Pfad-Form
        mit Underscore, siehe `done/M3-welle-6.md` DoD-Note).
  - [x] `make fullbuild` gruen ohne Override — Welle-6-C2
        (`c61ab0d`) liefert cache-frei gruen mit OTLP-Collector-
        Sibling im Compose-Smoke + Trivy-Image-Audit fuer beide
        Tags (`grid-gym-runtime` + `$(OTEL_COLLECTOR_IMAGE)`).
  - [x] M3-Welle-7-End-to-End-Sweep (S-1..S-6, analog M2-Welle-7
        §4) — dokumentiert in
        [`done/M3-results.md`](../done/M3-results.md) §4.

### M4 — Protokolladapter (`Done` 2026-06-01)

M4-Abschluss-Belege in
[`../done/M4-results.md`](../done/M4-results.md);
Slice-Plan in
[`M4-protocol-adapters.md`](../done-archive/M4-protocol-adapters.md)
(wandert nach `done/` mit Welle-7-C4-Self-Close-Move).
9 Wellen 0..6b geliefert (5 produktive Adapter +
2 Cross-Adapter-Hardening-Wellen); 6 M4-ADRs
(0030..0035) auf `Accepted` mit M4-Welle-7-C1
`d2071f0`.

- **Lieferziel:** produktive Driven-Adapter fuer die in Spec §16
  genannten Protokolle (`GG-MQTT/MODB/OPCUA/DNP3/IEC-001`).
- **Lastenheft-IDs:** `GG-MQTT-001..00X`, `GG-MODB-001..00X`,
  `GG-OPCUA-001..00X`, `GG-DNP3-001..00X`, `GG-IEC-001..00X`.
- **Architekturartefakte:** `GG-AR-PORT-DRN-007`
  (`DeviceProtocolPort`), pro Protokoll ein
  `adapters/driven/protocol_<name>/`-Modul.
- **DoD-Checkliste:**
  - [x] MQTT-Adapter (paho-mqtt) mit Topic-Mapping zu Geraete-
        Telemetry/Commands. — Welle 2 `Done`.
  - [x] Modbus-Adapter (pymodbus). — Welle 3 `Done` +
        Slice-031-Review-Folge.
  - [x] OPC-UA-Adapter (asyncua). — Welle 4 `Done` +
        Slice-032-Review-Folge.
  - [x] DNP3-Adapter (oder dokumentierter Verzicht via
        `Out-of-Scope`-Note). — Welle 5a `Done` (Spike-Adapter
        mit `nfm-dnp3` + `dnp3-outstation`).
  - [x] IEC-61850-Adapter (oder dokumentierter Verzicht). —
        Welle 5b `Done` (Spike-Adapter mit `pyiec61850-ng` als
        GPL-isoliertes Optional-Extra; Decision I-f via SPDX-
        Header pro Datei) + Slice 033 Review-Folge + Welle 6b
        Lizenz-/Smoke-Hardening (SPDX-Lint,
        [`AC-IEC61850-GPL-BOUNDARY`](../../adr/0035-iec61850-adapter-profile.md)-Contract,
        CONTRIBUTING.md). IedServer-In-
        Process-Smoke aktuell unter 2c-Mock-only-Fallback mit
        Trigger 009 (Welle-6b-C3-Pfad-A-Befund: PyPI-Stand
        identisch zu Welle 5b).
  - [x] [`AC-ADAPTER-LIGHTWEIGHT`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) bleibt fuer alle protocol_*-Module
        gruen (kein Fachlogik-Sickern). — Welle 1..6b green;
        Welle-6b-C3 erweitert den Filter um Cross-Adapter-Helper
        `_protocol_*.py` (Slice-034-F13-Folge).
  - [x] Integration-Tests pro Adapter via testcontainers (analog
        Welle 6c). — In-Process-Smokes statt testcontainers wo
        moeglich (Modbus, OPC-UA, DNP3); Mosquitto-MQTT-Smoke
        via Compose-Sibling; IEC-61850-Smoke via 2c-Mock-only-
        Fallback (Trigger 009).

### M5 — UI + Demo (`Done` 2026-06-04)

Welle 0 eroeffnet 2026-06-01 mit Slice-Doc + Slice-Plan
([`M5-welle-0.md`](../done-archive/M5-welle-0.md) + [`M5-ui-demo.md`](../done-archive/M5-ui-demo.md))
+ Pre-M5-Welle-0-Sondierungs-ADR
[`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md)
mit Maintainer-Decision-Indication „Option 1 (FastAPI +
HTMX + Jinja2 + Chart.js)". **Welle 0 abgeschlossen
2026-06-01** mit C0 `d93ae57` + C0-Review `aa1db52` (12
Findings) + C1 `b8bef6c` (NEU `M5-ui-demo.md`) + C2
`112efd3` (Trigger-Triage + Status-Flip).

**Welle 1 (HTTP-API-Surface + [`ADR-0036`](../../adr/0036-ui-stack-choice.md)-Schaerfung)
abgeschlossen 2026-06-01** mit Pre-C0a `fd642df`
(`git mv`) + Pre-C0b `fb417b9` (Cross-Doc-Refs-Sync) +
Pre-C0c `9c20dad` (HTMX-FastAPI-Smoke-Probe-Run; 4 Probe-
Tests) + C0 `e573f67` (Slice-Doc) + C1 `d468e68` (ADR
0036 → `Provisional` + NEU [`ADR 0037`](../../adr/0037-http-api-surface-pattern.md) `Proposed`) + C2
`ae630ce` (HTTP-API-Surface produktiv: 5 REST + 1 WS-
Endpunkt unter `src/grid_gym/adapters/driving/http_api/`
in 4 Modulen + Pydantic-Schemas + 16 Unit + 2 Integration-
Tests) + C3 `f9f514d` ([`ADR 0037`](../../adr/0037-http-api-surface-pattern.md) → `Provisional` +
Status/DoD-Sync + Roadmap-Typo-Fix `GG-AR-PORT-DRG-002`
→ Verwerfung per [`ADR 0037`](../../adr/0037-http-api-surface-pattern.md) Decision API-3). 1584 → 1600
Unit-Tests (+16); 39 → 41 Integration (+2). 10/10 A-1-
Gates gruen.

**Welle 2 (UI-Foundation) abgeschlossen 2026-06-01** mit
Pre-C0a `c7c2641` (Self-Close-Move; rename-only) +
Pre-C0b `a0c8ba3` (Cross-Doc-Refs-Sync) + C0 `64d5129`
(Slice-Doc mit Decision 2 final auf
`src/grid_gym/adapters/driving/ui/`) + C2 `5234617`
(UI-Foundation produktiv: Jinja2-Dep + vendored HTMX
2.0.9 + Chart.js 4.5.1 + StaticFiles-Mount +
`ui_router` mit 2 Page-Routes + 6 Templates + 18 Tests)
+ C3 `97c718f`. Welle 2 verzichtete bewusst auf
C1-ADR-Commit (Decision 2 im Slice-Doc-Body fixiert;
[`ADR 0036`](../../adr/0036-ui-stack-choice.md) nimmt Layout-Realisierung bei M5-Welle-7-Closure
auf). 1600 → 1610 Unit-Tests (+10); 41 → 43 Integration
(+2). 10/10 A-1-Gates gruen.

**Welle 3 (Live-Telemetry-Dashboard) abgeschlossen
2026-06-01** mit Pre-C0a `8d60e16` (Self-Close-Move) +
Pre-C0b `159f537` (Cross-Doc-Refs-Sync) + Pre-C0c
`5349923` (Asyncio-Pub/Sub-Smoke-Probe-Run; 4 Probe-
Tests) + C0 `ab55ec7` (Slice-Doc mit Decisions 3/7/11
final) + CI-Hotfix `3ba74ef` (Ruff SIM105 + format in
Probe-Datei) + C1 `9f3c00d` (NEU [`ADR 0038`](../../adr/0038-telemetry-stream-port.md) `Proposed`)
+ C2 `82bdf39` (Live-Telemetry produktiv: NEU
`TelemetryStreamPort` Driving-Port + NEU
`InMemoryTelemetryStream`-Adapter mit
`DemoTelemetryGenerator` als Stub-Producer + WS-
Subscribe-Pattern + Dashboard-UI mit Chart.js-Time-
Series + 6-Zustands-Quality-Marker; 16 neue Unit + 2
Integration-Tests) + C3 `0e0473d` ([`ADR 0038`](../../adr/0038-telemetry-stream-port.md) `Proposed →
Provisional`). 1610 → 1626 Unit-Tests (+16); 43 → 49
Integration (+6 inkl. 4 Probe-Tests). Lastenheft-Akzeptanz
`GG-API-002` + `GG-UI-002/003/009` produktiv. 10/10 A-1-
Gates gruen.

**Welle 4a (Replay-Controls + TickLoop-Wiring) abgeschlossen
2026-06-02** mit Pre-C0a `4517f51` (Self-Close-Move) +
Pre-C0b `79c9712` (Cross-Doc-Refs-Sync) + C0 `3544dee`
(Slice-Doc mit Decisions 12/13/14 final + Welle-4-
Subdivision-Motivation) + C1 `f1284c4` (NEU [`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md)
`Proposed`) + C2 `9c188e0` (RunStatus-Literal-Alias +
RunRepository-Extension `update_status`/`get_status` +
TickLoop-Control-Surface mit konsolidierter
`request(action)`-Methode + Pre-Tick-Guard +
`TickResult.paused_result`-Factory + 2 Endpoint-Wirings
auf existierenden Welle-1-Stubs `GET /status` +
`POST /control` + NEU `TickLoopRegistry`-Adapter + NEU
`DemoTickLoopDriver` + NEU UI-Page `GET /control` mit
HTMX-Polling + NEU `_demo_setup.py`-Komposition-Root;
24 neue Unit + 1 Integration-Test) + C3 (dieser Commit;
[`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md) `Proposed → Provisional`). 1626 → 1650 Unit-
Tests (+24); 49 → 50 Integration (+1). Lastenheft-
Akzeptanz `GG-UI-004` + Replay-Restcompletion-Anteil
`GG-API-001` produktiv. 10/10 A-1-Gates gruen. **Welle-
4-Subdivision** (4a/4b; Pattern analog M4-Welle-5a/5b und
M4-Welle-6a/6b) komplett abgeschlossen 2026-06-02.

**Welle 4b (Alarm-Aggregation + AlarmStreamPort + Alarm-
Tabelle-UI) abgeschlossen 2026-06-02** mit Pre-C0a
`d1b0eb7` (Self-Close-Move) + Pre-C0b `e325307` (Cross-
Doc-Refs-Sync) + C0 `08b5ba7` (Slice-Doc mit 3 Decisions
15/16/17 + Retro-Sync der Welle-4a-Era-2→3-Decision-
Forward-Pointer in 3 Docs) + C1 `850cf85` (NEU [`ADR 0040`](../../adr/0040-alarm-aggregation-and-stream-port.md)
`Proposed`) + C2 `b7ac7b3` (NEU `Alarm`-Domain-Type mit
9-Feld-Schema per `spec/architecture.md §Alarm` + Mapper-
Familie in `core/simulation/alarm_mappers.py` mit Union-
typed `alarm_from_power_device_alarm` konsolidiert + NEU
`TickResult.emitted_alarms`-Feld + TickLoop-Drain-Hook
mit `alarm_id_source`-Kwarg + NEU `AlarmStreamPort` +
NEU `InMemoryAlarmStream` mit Drop-Oldest-Backpressure +
NEU `AlarmHistoryBuffer`-Ring-Buffer (N=200) + NEU REST-
`/alarms-history`-Endpoint + NEU WS-`/alarms-stream`-
Endpoint + NEU UI-Page mit 6-Spalten-Tabelle + HTMX-
Hydration + WS-Live-Update + NEU `_alarm_setup.py`-
Komposition-Root + DemoTickLoopDriver-Erweiterung; 31
neue Unit + 1 Integration-Test) + C3 (dieser Commit;
[`ADR 0040`](../../adr/0040-alarm-aggregation-and-stream-port.md) `Proposed → Provisional` + 4 C2-Realization-
Notes). 1650 → 1681 Unit-Tests (+31); 50 → 51 Integration
(+1). Lastenheft-Akzeptanz `GG-UI-005` produktiv;
[`ADR-0014`](../../adr/0014-battery-snapshot-schema.md)-§6-Forward-Pointer („AlarmSinkPort kommt mit
M3") Driving-Side-Anteil produktiv aufgeloest (Postgres-
Persistenz bleibt M3-Welle-6c). 10/10 A-1-Gates gruen.
**Welle-4b-Review-Folge** (2026-06-02, nach C3): xhigh-
effort `/code-review` deckte 15 Findings auf — alle in
einer Folge-Lieferung adressiert ohne ADR-Aenderung
(rein Bug-Fixes + Forward-Defense; siehe `M5-welle-4b.md
§10`). 1681 → 1696 Unit-Tests (+15).

**Welle 5 (Demo-Pipeline + Scenario-Loader-Wiring) `Done`
2026-06-03** — eroeffnet 2026-06-02 mit Pre-C0a `a030c0e`
(Self-Close-Move `M5-welle-4b.md → done/`, rename-only) +
Pre-C0b `45335eb` (Cross-Doc-Refs-Sync nach Move, 5 Files) +
C0 `155c421` (Slice-Doc
[`M5-welle-5.md`](../done-archive/M5-welle-5.md) + Decisions 5/6/18 final +
Sub-Slicing-Risk-Verifikation — Single-Slice ohne
Splittung). Welle 5 ist die **Demo-Welle** in M5: erfuellt
`GG-DEMO-001..005` (5 MUSS) plus `GG-DEMO-007` (1 SOLLTE
eng inkludiert: RuleBasedAgent im kanonischen Demo-YAML
ohne Agent-UI). `GG-DEMO-008` (Abnahmedoku) ist auf Welle 6
verschoben (C2-Folge-Entscheid 2026-06-03: Filename +
Substanz-Konsistenz mit `GG-DEMO-006`-Verschiebung;
Welle-6-Pfad `docs/user/gg-demo-008-abnahme.md`).
Lieferziel: (1) kanonisches Demo-YAML
unter `deploy/scenarios/gg-demo.yaml` mit 5 MVP-Devices + 1
LoadProfile + 1 LoadEvent + 1 RuleBasedAgent + `seed=42`-
Determinismus; (2) `make demo`-Pflicht-Target mit
`docker compose up` + Healthcheck-Wait + UI unter
`http://localhost:8000` in unter 30s; (3) Lifespan-Demo-
Pfad-Erweiterung in `_demo_setup.py` ueber
`GRID_GYM_DEMO_SCENARIO_PATH`-Env (Default-Pfad
unveraendert fuer Welle-4a/4b-Integration-Tests); (4)
`python -m grid_gym demo`-Sekundaer-Surface mit
`__main__.py`-Entry-Point; (5) Integration-
Smoke-Test `test_m5_welle_5_demo_smoke.py` ohne Container.
**Anti-Scope:** keine Multi-Run-Driver-Registry
(`_DemoTickLoopDriverAlreadyConfiguredError` aus Welle-4b-
Fix #13 schuetzt Single-Run), kein Snapshot-Resume in Demo
(Welle-6+/M6-Material), `GG-DEMO-006` Fault-Injection +
`GG-DEMO-008` Abnahmedoku deferiert auf Welle 6
(`GG-UI-007`-Form-Substanz-Kopplung + Range-Konsistenz),
keine neue Compose-Topologie (Decision 18),
kein C1-ADR-Commit (Pattern analog Welle 2 `64d5129`).
**Naechster Schritt:** C1 → C2 → C3.

- **Lieferziel:** Visualisierungs- und Demo-Layer
  (`GG-UI-001..009`, `GG-DEMO-001..00X`).
- **Lastenheft-IDs:** `GG-UI-001..009`, Demo-System aus Spec §24.
- **Architekturartefakte:** `GG-AR-COMP-UI`. **Hinweis:**
  Slot `GG-AR-PORT-DRG-002` (`UICommandPort`) ist mit
  M5-Welle-1-C3 [`verworfen`](../../adr/0037-http-api-surface-pattern.md)
  ([`ADR 0037`](../../adr/0037-http-api-surface-pattern.md) Decision API-3 — Typo gegen `GG-AR-PORT-DRV-*`-
  Konvention und semantisch ueberfluessig nach Decision
  API-2: UI nutzt HTTP-API direkt via REST + WebSocket
  ohne separaten Driving-Port-Slot).
- **DoD-Checkliste:**
  - [x] Web-UI mit Live-Telemetry-Stream
        (`GG-UI-001..006`) — Welle 2 (Foundation) + 3
        (Dashboard) + 6b (Devices-Page).
  - [x] Scenario-Editor (`GG-UI-006..008`) — Welle 5
        (`gg-demo.yaml`-Loader) + 6a (Fault-Form) + 6b
        (Devices/System-Pages). Nicht Inline-WYSIWYG-
        Editor; Scenario-Editing laeuft ueber YAML-Datei
        + `make demo` (Welle-7-Closure-Interpretation:
        ausreichend fuer MVP).
  - [x] Demo-Lauf reproduzierbar via `make demo` —
        Welle 5 (Demo-Pipeline + Lifespan-env-var) +
        Welle 6c (Abnahmedoku
        [`../../../user/gg-demo-008-abnahme.md`](../../../user/gg-demo-008-abnahme.md)).
  - [x] UI nutzt nur `GG-API-001`/`002`/`003` — kein direkter
        Kern-Zugriff. **`UICommandPort`-Slot bewusst nicht
        verwendet** ([`ADR 0037`](../../adr/0037-http-api-surface-pattern.md) Decision API-2).

### M6 — Performance + Security + CI/CD-Haertung (`Done` 2026-06-08)

**Slice-Plan:**
[`M6-perf-security-cicd.md`](../done-archive/M6-perf-security-cicd.md)
(angelegt M6-Welle-0-C1 `e050035`). **M6 abgeschlossen
2026-06-08 mit Welle 7 (M6-Closure)**: [`ADR 0041`](../../adr/0041-performance-bench-pattern.md)..0046
`Provisional → Accepted` (W7-C1), NEU
[`M6-results.md`](../done/M6-results.md) (W7-C2),
Roadmap-DoD-Sweep + Top-Level-Sync (W7-C3), Self-Close-Move
`M6-perf-security-cicd.md` + `M6-welle-7.md` → `done/`
(W7-C4a/C4b). Pattern analog M4-/M5-Welle-7. **M6-Welle-6
(Deploy-Hardening + IEC-Smoke-Pfad-B; `GG-DEPLOY-001..011`
+ Trigger 009) abgeschlossen 2026-06-08** (siehe
[`M6-welle-6.md`](../done-archive/M6-welle-6.md)) mit Stack C0 `fab6a8c`
(Slice-Doc) / C1 `1d478e3` (NEU [`ADR 0046`](../../adr/0046-multi-python-test-stage-pattern.md) `Provisional`) /
C2 `f07e996` (feat: `GG-DEPLOY-006` NEU `/ready`-Endpoint
mit Three-State-Status + Komponenten-Breakdown
(api/ui/db/simulation) / `GG-DEPLOY-004` NEU
`.devcontainer/`-Konfig / Trigger 009 NEU Dockerfile-
`iec61850-test`-Stage auf Python 3.12 + Makefile-Target
`test-iec61850`; inkl. Code-Review-BLOCKER-Fix simulation-
Healthcheck-Wiring) / C3 `79563c0` (Status/DoD-Sync) / C4a
`79ac725` (Self-Close-Move rename-only) + C4b `d8dd8d2`
(Cross-Doc-Refs-Sync).
`GG-DEPLOY-001..006/011` ✓ produktiv, `GG-DEPLOY-007..010`
⏸ M7+; Trigger 009 aufgeloest (`open → done`); NEU [`ADR 0046`](../../adr/0046-multi-python-test-stage-pattern.md)
`Multi-Python-Test-Stage-Pattern` bleibt `Provisional` bis
M6-Welle-7-Closure. Self-Close-Folge C4a/C4b dient als
M6-Welle-7-Pre-C0a/Pre-C0b.
**M6-Welle-5c abgeschlossen 2026-06-07** mit Stack
`4b76ff7..C4b dieser Commit` (siehe
[`M6-welle-5c.md`](../done-archive/M6-welle-5c.md); `GG-SAFE-005` ✓ produktiv
an 4 Geraeten (Battery/Load/GridConnection/PV) per
Lastenheft-Traceability Z. 2291; `GG-SAFE-006` ⚠ partial
(Core-Diff-Algorithm `diff_replay` ✓ produktiv; Per-Lauf-
Status-Marker `replay_diff_status` + `ReplaySourcePort`-
Verkabelung fehlen → NEU Trigger 036); Demo-Compose-`ports`-
Hardening per `carveouts.md §2.7`-Auflage; 6 NEU Integration-
Smokes + Audit-Doku
[`../../../user/safe-005-006-fallback-determinism.md`](../../../user/safe-005-006-fallback-determinism.md)
+ Maintainer-Doku
[`../../../user/demo-compose-hardening.md`](../../../user/demo-compose-hardening.md)).
**Welle-5-Subdivision (5a + 5b + 5c) komplett abgeschlossen
2026-06-07** per Welle-5a-D-1-Sub-Slicing-Beschluss; alle
acht `GG-SAFE-*`-Lastenheft-IDs auditiert (sechs ✓ produktiv,
zwei ⚠ partial mit `open/`-Triggern 034/035/036).
**M6-Welle-5b abgeschlossen 2026-06-07** mit Stack `0d3bb61..
C3 dieser Commit` (siehe [`M6-welle-5b.md`](../done-archive/M6-welle-5b.md);
NEU [ADR 0045](../../adr/0045-http-api-request-strict-validation.md)
`Provisional`; alle 6 [`GG-SAFE-007`](../../../../spec/lastenheft.md#gg-safe-007)-Surfaces + 6 [`GG-SAFE-008`](../../../../spec/lastenheft.md#gg-safe-008)-
Surfaces ✓ produktiv; 11 NEU Integration-Smokes; Audit-Doku
[`../../../user/safe-007-008-sim-prod-input-validation.md`](../../../user/safe-007-008-sim-prod-input-validation.md)).
**Welle-4-Subdivision komplett abgeschlossen 2026-06-06**:
4a Vulnignore-Pattern + 4b-a Bench-Foundation + 4b-b
`GG-RT-005`-Telemetry-Bench + 4b-c `GG-RT-001`-Backpressure-
Healthcheck (alle vier Sub-Slices Done).
**M6-Welle-0 abgeschlossen 2026-06-04** mit Stack
`282a8cb..960f6ed` (siehe
[`../done/M6-welle-0.md`](../done-archive/M6-welle-0.md)).
**M6-Welle-1 abgeschlossen 2026-06-05** mit Stack
`4b1b3e9..d51d6e7` (siehe
[`M6-welle-1.md`](../done-archive/M6-welle-1.md); inkl. C4a `1fbd0ac`
Self-Close-Move + C4b `d51d6e7` Cross-Doc-Refs-Sync):
Trigger-010-Aufloesung ohne Code-Edit durch Debian-13.5-
Upstream-Patch-Drift + Trigger-015-Pattern; NEU [`ADR 0043`](../../adr/0043-image-audit-strategy.md)
`Provisional` (Image-Audit-Strategie); Welle-1-D-1 (CI-
Pflicht-Gate fuer `make fullbuild`) auf M6-Welle-3 vertagt
ueber NEU [`../done/031-ci-make-fullbuild-gate.md`](../done-archive/031-ci-make-fullbuild-gate.md).
**M6-Welle-2 abgeschlossen 2026-06-05** mit Stack
`0cc28f3..b41b7fc` (siehe
[`M6-welle-2.md`](../done-archive/M6-welle-2.md); Self-Close-Move-Folge
Stack umfasst C0/2 Review-Folgen/C1/C2/C3/C3-Sensor-
Erweiterung + C4a `c51d905` Self-Close-Move + C4b `b41b7fc`
Cross-Doc-Refs-Sync): Trigger-
008-Aufloesung durch C2 `235395e` (NEU `.github/workflows/
release.yml` mit Tag-Push + workflow_dispatch + 3 Jobs +
1 GHCR-Push + 5 Release-Asset-Files; Makefile `make sbom`-
Scan-Ziel von Source-Tree auf Runtime-Image; Dockerfile
test-unit JUnit-XML + coverage-gate HTML-Report); NEU
[`ADR 0042`](../../adr/0042-sbom-tool-and-release-pattern.md) `Provisional` (SBOM-Tool + Release-Workflow-
Pattern; Accept in M6-Welle-7-Closure-C1 gebuendelt mit
[`ADR 0041`](../../adr/0041-performance-bench-pattern.md) + [`ADR 0043`](../../adr/0043-image-audit-strategy.md)).
**M6-Welle-3 abgeschlossen 2026-06-05** mit Stack
`08a8034..c36f734` (siehe
[`M6-welle-3.md`](../done-archive/M6-welle-3.md); Self-Close-Move-
Folge C4a/C4b ausstehend als Welle-4-Pre-C0a/Pre-C0b):
NEU 4 GitHub-Actions-Workflows (`tests.yml`/`coverage.yml`/
`dep-audit.yml`/`fullbuild.yml`); Python-3.13/3.14-Matrix
in `tests.yml`; Trigger 031 (`make fullbuild`-CI-Gate aus
Welle-1-D-1-Vertagung) aufgeloest und nach `done/` gewandert;
pip-PYSEC-2026-196-Drift im `uv.lock` behoben (`pip
26.1.1 → 26.1.2`). C1 entfaellt (keine ADR-Substanz;
Pattern analog M5-Welle-2).
**M6-Welle-4a abgeschlossen 2026-06-06** mit Stack
`9bb6a92..789ac50` (C0 + C1 `94dff9e` NEU [`ADR-0044`](../../adr/0044-generated-trivyignore-permit.md)
`Provisional` (Generated-Trivyignore-Permit; [`ADR-0011`](../../adr/0011-schaerfung-ohne-abloesung.md)-
Schaerfung an [`ADR-0043`](../../adr/0043-image-audit-strategy.md) §2.2) + C2 `8fbd17c` NEU `tools/
render_trivyignore.py` (Python+PyYAML; m-trace-Pattern-
Import) + `deploy/security/vulnignore.yaml` mit CVE-2026-
42504-Eintrag + Makefile-`render-trivyignore`-Target +
`image-audit`-`--ignorefile`-Erweiterung + C3 `f19837f`
Closure-Sync + Post-Push-CI-Fix `f46e789` simulation-
Healthcheck Always-Healthy gegen Compose-v2-`--wait`-
Strictness + C4a `3bc58b8` Self-Close-Move + C4b `789ac50`
Cross-Doc-Refs-Sync): `make fullbuild` cache-frei
gruen ueber generierte `.trivyignore` lokal UND CI-Sensor
(Lauf 27055273876) — erstmalig seit `fullbuild.yml`-Anlage
in M6-Welle-3-C2 `ce13253`. Trigger 033 bleibt OFFEN als
Stable-Watch (vulnignore-Pattern ist Temp-Deferral; echte
Aufloesung weiter bei OTel-Stable-Release 0.154.0+ mit
`go1.26.4+`).
**M6-Welle-4b-a abgeschlossen 2026-06-06** mit Stack
`f2fbcc0..76a2f40` (C0 + C1 `43569d2` NEU [`ADR-0041`](../../adr/0041-performance-bench-pattern.md) `Provisional`
(Performance-Bench-Pattern + Regression-Schwelle; M6-D-7-
Vorbelegung aufgeloest) + C1-Review-Folge `f4f4983` (4
Findings: F1 HIGH [`GG-RT-004`](../../../../spec/lastenheft.md#gg-rt-004)-Replay-Diff + F2 HIGH opt-in-
Extra-Pattern + F3/F4 MEDIUM) + C2 `5d8c497` NEU pytest-
benchmark Dep + Dockerfile-perf-Stage + tests/perf/ Layer +
Makefile-Targets + Maintainer-Dev-Host-Baseline + C3 dieser
Commit Closure-Sync): `GG-RT-004`-Doppel-Akzeptanz produktiv
(100 Geraete x 10 000 Ticks ohne verlorene Events UND ohne
nichtdeterministischen Replay-Diff per [`ADR-0041`](../../adr/0041-performance-bench-pattern.md) §2.2; Bench-
Median 519ms / 1.92 OPS; Regression-Schwelle 20% Median-
Drift gegen tests/perf/baseline.json per [`ADR-0041`](../../adr/0041-performance-bench-pattern.md) §2.3).
**M6-Welle-4b-b abgeschlossen 2026-06-06** mit Stack
`beb5dee..c8625f7` (C0 `beb5dee` Slice-Doc + C0-Review-Folge
`f9620a3` (2 HIGH Findings: D-3 No-Subscriber-False-Positive
+ D-2 canonical_json-API-Drift) + C0-Review-Folge-2 `935151e`
(2 MEDIUM stale-Refs) + C2 `a2feff7` NEU `tests/perf/
test_telemetry_port_bench.py` + Baseline-Update + C3 dieser
Commit Closure-Sync): `GG-RT-005`-Doppel-Akzeptanz produktiv
(Payload ≤ 256 Byte canonical-serialisiert UND ~788 000
Publish-OPS lokal weit ueber der 10 000-SOLLTE-Schwelle;
Single-Queue-Subscriber-Slot-Setup vermeidet das No-Op-False-
Positive aus dem C0-Erstwurf).
**M6-Welle-4b-c abgeschlossen 2026-06-06** mit Stack
`c5543fd..7001989` (C0 + C0-Review-Folge `aacc370` (7 Self-Review-
Findings: F1 MEDIUM clock_source-Pflicht + F2-F7 LOW) + C2
`a98f967` (NEU `TickLoopHealthcheckAdapter` + Driver-Hook +
`_healthcheck_router.py`-Endpoint + 14 Unit-Tests + 3
Integration-Smokes) + C2-Review-Folge `8785a6b` (7 Self-
Review-Findings: F1 MEDIUM Datei-Naming-Drift + F2-F7 LOW +
try/finally-Wrap + 4 NEU Driver-Hook-Unit-Tests) + C3 dieser
Commit Closure-Sync): `GG-RT-001` MUSS-Akzeptanz produktiv
(Tick-Dauer/p95-Jitter/missed-Ticks/Backpressure-Status fuer
10ms-Modus via NEU Adapter-Side `_tick_loop_healthcheck.py` +
`GET /runs/{id}/healthcheck`-Endpoint; Core unangetastet,
[`AC-NO-TIME`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-konform). **Welle-4-Subdivision komplett**: 4a +
4b-a/b/c alle Done; aktive Welle wandert auf Welle 5
(Security-Audit + Eingabevalidierung).
**M6-Welle-5a abgeschlossen 2026-06-06** mit Stack
`4b36185..52cb698` (C0 `4b36185` Slice-Doc-Anlage +
Welle-5-Sub-Slicing-Beschluss + C2 `4c1a693` NEU
`tests/integration/test_m6_welle_5a_safe_001_004_smoke.py`
mit 7 Smokes + NEU `docs/user/safe-001-004-quality-pipeline.
md` Audit-Tabelle + NEU 2 `open/`-Triggers 034
(`GG-SAFE-004` `max_age`-stale-Quality-Lücke) + 035
(`GG-SAFE-003` Adapter-Comm-Failure partial Lücke) +
C2-Review-Folge `52cb698` (6 Self-Review-Findings F1..F6
adressiert: MEDIUM F1 Slice-Doc-§1.1-Factual-Fix +
5 LOW F2..F6) + C3 Closure-Sync dieser Commit):
`GG-SAFE-001..004`-MUSS audited (001/002 ✓ produktiv;
003 ⚠ partial Lücke → Trigger 035; 004 ✗ Lücke → Trigger
034); C1 entfaellt (Welle-5a-D-5). Self-Close-Folge C4a/C4b
folgt als Welle-5b-Pre-C0a/Pre-C0b.
Welle 5b/5c Slice-Docs entstehen pro Welle-X-C0. Carveout-
Triage-Eingangsbestand:
[`carveouts.md`](carveouts.md) (31 Items; 3 Trigger
`Active in M6-Welle-X` per Welle-0-C2 — Trigger 010 +
Trigger 008 + Trigger 031 alle `Aufgeloest`).


- **Lieferziel:** harte Performance-Schranken aus `GG-RT-001..005`,
  Sicherheits-Audit (`GG-SAFE-001..006`,
  `GG-SBOM-001..00X` ueber Trigger 008), CI/CD-Vollausbau
  (`GG-CICD-001..00X`).
- **Lastenheft-IDs:** `GG-RT-001..005`, `GG-SAFE-001..006`,
  `GG-CICD-001..00X`, `GG-DEPLOY-001..00X`.
- **DoD-Checkliste:**
  - [ ] 10.000-Points/s-Benchmark (`GG-RT-005`) reproduzierbar.
  - [x] SBOM-Generierung im CI (Trigger 008 nach `done/`) —
        produktiv mit M6-Welle-2-C2 `235395e` via NEU
        `.github/workflows/release.yml` `produce-assets`-Job
        (Syft v1.17.0 gegen Runtime-Image, CycloneDX-JSON;
        [`ADR 0042`](../../adr/0042-sbom-tool-and-release-pattern.md) `Provisional`).
  - [x] GitHub-Actions-Workflow gegen Python 3.13 + 3.14
        (Spike-0-Closure-D-8 + [`ADR 0002`](../../adr/0002-language-and-build-stack.md) §6.1) — produktiv mit
        M6-Welle-3-C2 `ce13253` via NEU `.github/workflows/
        tests.yml` `strategy.matrix.python-version: ['3.13',
        '3.14']` (test-unit-Job; test-integration laeuft mit
        Default-Python wegen Compose-Substanz; Welle-3-D-2).
  - [x] Image-Audit (`make image-audit`) inkl. Vuln-Scan in CI —
        produktiv mit M6-Welle-3-C2 `ce13253` als Teil von
        `make fullbuild` in `fullbuild.yml`.
  - [x] Container-Smoke-Test mit `deploy/compose.yml`
        (`make runtime` pollt `/health`) — produktiv mit
        M6-Welle-3-C2 `ce13253` als Teil von `make fullbuild`
        in `fullbuild.yml`.
  - [x] **CI-Erweiterung um Tests** (`GG-CICD-002`) — produktiv
        mit M6-Welle-3-C2 `ce13253` via NEU `tests.yml`:
        `test-unit` (Python-3.13/3.14-Matrix) + `test-
        integration` (Default-Python). Slice 025 §2-M6-
        Vertagung damit aufgeloest.
  - [x] **CI-Erweiterung um Coverage-Gates** (`GG-CICD-003`) —
        produktiv mit M6-Welle-3-C2 `ce13253` via NEU
        `coverage.yml`: `coverage-gate` (90% Line / 85% Branch)
        + `coverage-gate-critical` (90% Critical-Domain) als
        separate Jobs.
  - [x] **CI-Erweiterung um Dependency-Audit** (`GG-CICD-006`) —
        produktiv mit M6-Welle-3-C2 `ce13253` via NEU
        `dep-audit.yml`. Plus pre-existing pip-PYSEC-2026-196-
        Drift im `uv.lock` mitbehoben (`pip 26.1.1 → 26.1.2`),
        damit der Gate von Anfang an gruen ist. `make
        dep-audit` (`pip-audit`) — meldet
        bekannte Schwachstellen direkter und transitiver
        Abhaengigkeiten. Slice 025 §2 ausgelagert; lokal
        Pflicht via `make gates`.
  - [x] **Release-Workflow** (`GG-CICD-007`) — produktiv mit
        M6-Welle-2-C2 `235395e`: NEU `.github/workflows/
        release.yml` mit Tag-Push (`v*.*.*`) + workflow_
        dispatch + 3 Jobs (build-and-publish-image / produce-
        assets / create-release) + 6 publizierte Artefakte
        (1 GHCR-Push `ghcr.io/<repo>:<tag>` + 5 GitHub-
        Release-Asset-Files: SBOM + JUnit-XML + Coverage-
        HTML-Tarball + OpenAPI-JSON + Demo-Abnahme-MD). ADR
        0042 `Provisional` verankert SBOM-Tool/Scan-Ziel +
        Release-Workflow-Pattern als Quality-Gate-Vertrag
        (Schwester zu [`ADR 0029`](../../adr/0029-no-coverage-pragma-contract.md)/0043).

### M7 — MVP-Abschluss (`Done` 2026-06-12)

**Slice-Plan:** entsteht in M7-Welle-0 (Pattern analog
M6-Welle-0). M7 ist der Container fuer die nach M6 verbliebene
MVP-Arbeit plus die offenen Trigger; eroeffnet als Handoff der
M6-Welle-7-Closure (Entscheidung 2026-06-08, M6-welle-7-Review-
Befund 3 — M2..M6 waren vorbelegt, M7 ist NEU).

**Vorbelegter Scope** (Scope-Skizze; konkrete Slice-Plaene
wandern bei Aktivierung nach `in-progress/`):

- `GG-MVP-002` ReplaySource-Integration — **aktiv als M7-Welle-1**
  (Gruppenplan [`M7-welle-1.md`](../done-archive/M7-welle-1.md); sub-sliced **1a**
  Zeitreihen-Persistenz / **1b** Replay-Lifecycle +
  `replay_diff_status`, per D-4-Final B); aktiviert Trigger 036
  (in 1b).
- `GG-MVP-003` Abnahme-CLI (`make accept` + `tools/accept.py`)
  — **Done 2026-06-10 als M7-Welle-2** (Plan
  [`M7-welle-2.md`](../done-archive/M7-welle-2.md); `GG-MVP-003` ✓ produktiv).
- Offene `open/`-Trigger: 033 (OTel-Collector-CVE Stable-Watch),
  034 (`GG-SAFE-004` max_age), 035 (`GG-SAFE-003` Comm-Failure),
  036 (`GG-SAFE-006` replay_diff_status), 037 (`GG-DEPLOY-007..
  010` Multi-Node-Deployment).

**In Progress seit 2026-06-08.** M7-Welle-0 (Slice-Plan-
Eroeffnung + Trigger-Triage; NEU `M7-mvp-completion.md` +
carveouts-Triage 034/035 → `Active in M7-Welle-3`)
**abgeschlossen** (C0..C4b). **M7-Welle-1** (`GG-MVP-002`) aktiv,
sub-sliced 1a/1b (D-4-Final B; Gruppenplan
[`M7-welle-1.md`](../done-archive/M7-welle-1.md)). **M7-Welle-1a Done 2026-06-09**
([`M7-welle-1a.md`](../done-archive/M7-welle-1a.md); Zeitreihen-Persistenz,
NEU `TelemetrySinkPort` + [`ADR 0047`](../../adr/0047-telemetry-sink-timeseries-persistence.md)). **Welle 1b weiter sub-sliced**
(1b-a-D-1): 1b-a (`ReplaySnapshotPort`, [`ADR 0048`](../../adr/0048-replay-snapshot-port-reconstruction.md)) + 1b-b
(Lifecycle-Hook + `replay_diff_status` + `GG-TERM-002/003`-MVP-
Preflight, [`ADR 0049`](../../adr/0049-replay-lifecycle-finalize-hook.md)). **M7-Welle-1b-a Done 2026-06-09**
([`M7-welle-1b-a.md`](../done-archive/M7-welle-1b-a.md); `ReplaySnapshotPort`-
Rekonstruktion aus `telemetry_points`). **M7-Welle-1b-b Done
2026-06-09** ([`M7-welle-1b-b.md`](../done-archive/M7-welle-1b-b.md); Closure —
Core-`finalize()`-Naht + `replay_diff_status` + GG-TERM-Preflight +
Zwei-Lauf-E2E-Beleg, [`ADR 0049`](../../adr/0049-replay-lifecycle-finalize-hook.md)). **`GG-MVP-002` ✓ produktiv**;
**M7-Welle-1 komplett** (1a + 1b-a + 1b-b; Gruppenplan wandert mit
der 1b-b-C4-Sequenz nach `done/`). Trigger 036 aufgeloest;
oeffentliche API-Replay-Bedienung deferred via
[Trigger 039](../open/039-api-replay-trigger-surface.md).
**M7-Welle-2 Done 2026-06-10** (`GG-MVP-003` Abnahme-CLI;
[`M7-welle-2.md`](../done-archive/M7-welle-2.md); `make accept` + `tools/accept.py` +
Shared `src/grid_gym/scenario_yaml.py`, D-1..D-10 final mit D-10-
Revision C, Replay-Step standalone wegen
[Trigger 040](../open/040-replay-finalize-headless-run-end-seam.md);
commits `33ac255` + `92d10f5`). **`GG-MVP-003` ✓ produktiv → alle vier
`GG-MVP-*`-Punkte produktiv** (001/002/003/004). **Aktiver Slice
jetzt: M7-Welle-3** (Safety-Closure `GG-SAFE-003/004`; Trigger 034
[`max_age`](../done-archive/034-safe-004-max-age-stale-quality.md) + 035
[Comm-Failure](../done-archive/035-safe-003-comm-failure-missing-quality.md)),
**aktiviert mit Welle-3-C0 2026-06-11**: Gruppenplan
[`M7-welle-3.md`](../done-archive/M7-welle-3.md), sub-sliced **3a**
(`max_age`-`STALE`-Stage, [`M7-welle-3a.md`](../done-archive/M7-welle-3a.md),
zuerst; [`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md)) + **3b** (Adapter-Comm-Failure + Alarm; Slice-Doc
via 3b-C0; ADR-Nummer 0053 reserviert) per Welle-3-D-1.
**M7-Welle-3a Done 2026-06-11** (`max_age_ms`-Kwarg +
Core-`STALE`-Stage + [`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md); commits `23c614a` + Review-Folge
`5a9960a`) — **`GG-SAFE-004` ✓ produktiv** (Audit-Flip in
`docs/user/safe-001-004-quality-pipeline.md`); Trigger 034 Closed.
**M7-Welle-3b Done 2026-06-12** (`GG-SAFE-003` Comm-Failure,
Trigger 035; [`M7-welle-3b.md`](../done-archive/M7-welle-3b.md); NEU
`CommFailureGuardedDeviceProtocolPort`-Wrapper +
`adapter_communication_lost`-Alarm-Vertrag, [`ADR 0053`](../../adr/0053-comm-failure-wrapper-missing-quality-alarm.md); commits
`3f28be1` + Review-Folge `82704b1`; 3b-D-1 = voller
Akzeptanz-Umfang via Test-Sibling, kein Carveout) —
**`GG-SAFE-003` ✓ produktiv**; Trigger 035 Closed. **M7-Welle-3
komplett — alle vier `GG-SAFE-001..004` produktiv.**
**M7-Welle-X Done 2026-06-12** (M7-Closure;
[`M7-welle-X.md`](../done-archive/M7-welle-X.md)): fuenf M7-ADRs
0047/0048/0049/0052/0053 `Provisional → Accepted` (0050/0051
bleiben `Proposed` per X-D-2 — eigene Lifecycle-Bedingungen,
Umsetzungsslices kein M7-Lieferpunkt) + NEU
[`done/M7-results.md`](../done/M7-results.md)
(MVP-Abschluss-Kriterium gepinnt). **M7 ist abgeschlossen —
der MVP ist geliefert** (alle vier `GG-MVP-*` + alle vier
`GG-SAFE-001..004` produktiv). **Post-M7: Trigger-Watch, kein
M8-Auto-Open (X-D-4)** — offene Trigger 033/037/038/039/040 +
Trigger-Gated-Bestand; neuer Meilenstein bei
Trigger-Aktivierung oder Stakeholder-Mandat.

---

## 5. Vorbedingungen

Vor M1 muessen folgende Punkte geklaert sein:

- [x] **`GG-AR-OPEN-001` Sprach- und Build-Wahl** — geschlossen mit
      `ADR 0002` (`Accepted` 2026-05-15) und synchron `ADR 0005`
      (`Accepted` 2026-05-15). Spike-0 Closure-Notiz:
      [`docs/plan/planning/done/spike-0.md`](../done-archive/spike-0.md).
- [x] **`GG-AR-OPEN-002` API/Simulation als ein oder zwei Prozesse**
      — geschlossen mit
      [`ADR 0012`](../../adr/0012-api-simulation-two-processes.md)
      (`Accepted` 2026-05-17): zwei Prozesse, Postgres als
      Persistenz-Bus. Welle-6c-`deploy/compose.yml` hat den
      Pattern de-facto implementiert; [`ADR 0012`](../../adr/0012-api-simulation-two-processes.md) formalisiert
      nachtraeglich. `spec/architecture.md` §19
      `GG-AR-OPEN-002`-Zeile entsprechend auf `Geschlossen`.
- [x] **Initiales Repository-Layout** gemaess der Hexagonalen Sicht
      (`GG-AR-P-002`, `GG-AR-TABU-001..008`) — sprachunabhaengig in
      `spec/architecture.md` §4.2 mit `hexagon/`-Gruppierung fixiert;
      Python-Paketnamen (`src/grid_gym/hexagon/{core,ports}/`,
      `src/grid_gym/adapters/`) durch `ADR 0002` §6.1 (`Accepted`
      2026-05-15) verbindlich.
- [x] **Trigger 001 (Code-Review-Doku + PR-Template)** — Post-
      Acceptance-Vorbedingung aus dem Dritten Spike-0-Review
      ([`done/spike-0-results.md`](../done/spike-0-results.md) §6).
      Erfuellt 2026-05-15 mit
      [`docs/user/code-review.md`](../../../user/code-review.md) und
      `.github/PULL_REQUEST_TEMPLATE.md`; Closure-Notiz in
      [`done/001-code-review-doc.md`](../done-archive/001-code-review-doc.md).
