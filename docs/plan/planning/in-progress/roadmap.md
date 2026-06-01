# Roadmap — grid-gym

**Status:** Aktiv — Vorbedingungen 1+3+4 geschlossen, M1+M2+M3+M4 abgeschlossen (M4 mit Welle 7 Closure 2026-06-01, [`../done/M4-results.md`](../done/M4-results.md)). **Naechster aktiver Slice: M5** (UI + Demo).
**Stand:** 2026-06-01

- **Meilensteine:** M1 `Done` (Welle 0..7), M2 `Done` (Welle 0..7),
  M3 `Done` (Welle 0..7), **M4 `In Progress`** (Welle 0 `Done`;
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
  (ADR 0032 → `Provisional`, `M4-welle-3.md` → `Done`,
  Top-Level-Doku-Sync in 6 Docs, Trigger-006-Re-Eval mit
  Modbus-Beleg positiv) + Doku-Review-Folge 2026-05-31
  (Move von `M4-welle-3.md` nach `done/`, Smoke-Abdeckung
  praezisiert, Folge-Slice
  [`031`](../done/031-modbus-adapter-review-folge.md)
  mit FC06-Guard und Fehler-Taxonomie umgesetzt);
  **Welle 4 `Done`** geschlossen 2026-05-31 mit C0 `7937e70`
  + C1 `74ed35b` + C2 `78fdd7a` (feat: `protocol_opcua/`-6-
  Modul-Paket + 81 Unit-Tests + 8 In-Process-Integration-
  Smokes + asyncua-Pin auf `>=1.2b2,<2.0` wegen Python-3.14-
  Inkompat in 1.1.8 + mypy-Override `implicit_reexport`)
  + C3 `7ad5baf` (ADR 0033 → `Provisional`, `M4-welle-4.md`
  → `Done`, Top-Level-Doku-Sync in 5 Docs) + Slice-032-
  Review-Folge 2026-05-31
  ([`../done/032-opcua-adapter-review-folge.md`](../done/032-opcua-adapter-review-folge.md);
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
  (ADR 0034 Proposed nach zwei C1-Probes — `nfm-dnp3`-Master-
  API-Inspektion + `dnp3-outstation`-Wire-Compat-Probe) +
  C2 `224b370` (feat: `protocol_dnp3/`-5-Modul-Paket + 56
  Unit-Tests inkl. hypothesis-Codec-Properties + 4 In-
  Process-`dnp3-outstation.AsyncOutstation`-Smokes + Pin
  `nfm-dnp3>=1.0,<2.0` produktiv und `dnp3-outstation>=0.2,<1.0`
  als dev-only Test-Sibling + mypy-Overrides + C2-Library-
  Bug-Find: `AnalogInput.index` statt `.idx` aus `__repr__`)
  + C3 `6903a08` (ADR 0034 → `Provisional`, `M4-welle-5a.md`
  → `Done` mit Liefer-Hashes + DoD-Verifikation + §9 DoD-
  Checkliste komplett abgehakt, Top-Level-Doku-Sync in 5
  Docs) + Self-Close-Move `9fea2be` (`M4-welle-5a.md` aus
  `in-progress/` nach `done/` als M4-Welle-5b-Pre-C0,
  rename-only); **Welle 5b `Done`** geschlossen 2026-06-01
  mit C0 `19f820a` (Slice-Doc) + C1 `88c1a33` (ADR 0035
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
  (ADR 0035 → `Provisional`, `M4-welle-5b.md` → `Done` mit
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
- **Aktiver Slice:** M4 (Protokolladapter — MQTT, Modbus,
  OPC-UA, DNP3, IEC 61850). **Naechster aktiver Schritt:**
  M4-Welle-7 (M4-Closure analog M3-Welle-7) — ADR 0030..
  0035 von `Provisional` auf `Accepted`; NEU `done/
  M4-results.md` mit Meilenstein-Zusammenfassung;
  Roadmap-M4-DoD-Checkboxen-Sweep; End-to-End-Sweep
  S-1..S-6; `make fullbuild` cache-frei gruen als
  Welle-7-Closure-Gate; Self-Close-Move Welle-6b-Doc
  nach `done/`; Self-Close-Move `M4-protocol-adapters.md`
  nach `done/` mit Welle-7-Closure-Hash.
- **ADRs:** 0022/0023/0024/0025/0026/0027 `Accepted` (M3-Welle-7
  C1.1..C1.6); 0028 + 0029 `Accepted` (Schaerfung-ohne-Supersede-
  Pflege von ADR 0006 §3 bzw. ADR 0002 §A-1); **0030 `Accepted`**
  (M4-Welle-1 `DeviceProtocolPort`-Surface; `Accepted` geplant
  mit M4-Welle-7-Closure); **0031 `Accepted`** (M4-Welle-2
  MQTT-Adapter-Profile mit Decisions 4a/4b/4c/4d alle final;
  `Accepted` 2026-06-01 mit M4-Welle-7-C1 `d2071f0`); **0032 `Accepted`**
  (M4-Welle-3 Modbus-TCP-Adapter-Profile mit Decisions
  M-a/M-b/M-c/M-d/M-e/M-f alle final — inline Register-Schema,
  5 Datatypes mit Byte-Order-Matrix, direkt-sync ohne
  Thread-Marshal, FC03/FC10-Defaults, Slave-Unit-ID per Target,
  in-process pymodbus-Server-Smoke; `Accepted` geplant mit
  M4-Welle-7-Closure). Review-Folge
  [`031`](../done/031-modbus-adapter-review-folge.md)
  hat FC06-Multi-Register-Guard, Read-/Write-
  Fehler-Taxonomie und bewusste Smoke-Abgrenzung
  umgesetzt. **0033 `Accepted`** (M4-Welle-4 OPC-UA-
  Adapter-Profile mit Decisions O-a/O-b/O-c/O-d/O-e alle
  final — inline Node-ID-Schema, Async-Bridge via
  `OpcuaLoopThread` (erstes Repo-Pattern dieser Art),
  8-Datatype-Set, Polling-Read + Direct-Write, in-process
  `asyncua.Server`-Smoke; `Accepted` geplant mit
  M4-Welle-7-Closure). **0034 `Accepted`** (M4-Welle-5a
  DNP3-Adapter-Profile mit Decisions D-a/D-b/D-c/D-d/D-e
  alle final — inline Point-Schema mit
  Group/Variation-Allowlist `{(1,1),(1,2),(30,1),(30,5)}`,
  zwei-Library-Setup `nfm-dnp3` produktiv +
  `dnp3-outstation` dev-only, direkt-sync wie Modbus,
  Class-0-Integrity-Poll + filter-by-index, write-Pfad
  Welle-5b-Anti-Scope; `Accepted` geplant mit M4-Welle-7-
  Closure). **0035 `Accepted`** (M4-Welle-5b IEC-61850-
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
  Module in einem sonst MIT-Projekt); `Accepted` geplant
  mit M4-Welle-7-Closure).
- **Tests:** 1584 Unit + 35 Integration passed + 4 skipped
  (Stand nach M4-Welle-6b-Closure; +441 Unit-Tests ggue.
  M3-Closure [+23 Welle 1 + +50 Welle 2 + +95 Welle 3 +
  +8 Review-Folge 031 + +81 Welle 4 fuer OPC-UA + +6
  Slice-032 fuer Loop-Thread-Lifecycle/Marshal-Pfad/
  String-Read-Quality.INVALID/Float32-Quantisierung +
  +56 Welle 5a fuer DNP3 + +75 Welle 5b fuer IEC-61850
  + +29 Welle 6a fuer Cross-Adapter-Hardening inkl. Slice
  034 (19 OTel-Span-Wrap-Tests inkl. F1/F2/F3-Negativ-
  Tests + 6 AC-ADAPTER-LIGHTWEIGHT-Planted-Violator-Tests
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
  (9 A-1-Gates). `make fullbuild` aktuell rot wegen 4 neuer
  HIGH-CVEs in Debian-13-Base (`CVE-2026-40356` in krb5-Paketen,
  Fix `1.21.3-5+deb13u1` verfuegbar) — Pre-existing-Drift seit
  M3-Welle-7-`c61ab0d`, **nicht durch M4-Welle-3-Code verursacht**;
  Base-Image-Bump in separatem Stack.
- **Trigger-006-Re-Eval (M4-Welle-3-C3, 2026-05-30):**
  positiv. `mypy --strict-bytes` laeuft cache-frei gruen gegen
  `src/grid_gym/adapters/driven/protocol_modbus/` ohne
  zusaetzliche `# type: ignore`-Inflation (bestehende 2
  `# type: ignore[no-untyped-call]` in `_port.py:128/148`
  sind pymodbus-API-spezifisch, kein bytes-Bezug). Trigger
  ist aktivierungs-reif; Aktivierung selbst ist Folge-Slice
  (`[tool.mypy] strict_bytes = true` plus Sweep-Pruefung).
- **Contracts:** 19 A-1 (7 lint-imports + 12 `tools/arch_check.py`
  inkl. `AC-OTLP-ADAPTER-NO-TIME` und `AC-TICK-LOOP-PRIVATE-
  RESUME-ERRORS`); `AC-ADAPTER-LIGHTWEIGHT` erfasst `protocol_*`
  weiter via `tools/arch_check.py:1089` (Regression-Schutz in
  Welle-1-C2 verifiziert, in Welle 2 + 3 produktiv bestaetigt).

**Bezug:** [Lastenheft](../../../../spec/lastenheft.md), [Architektur](../../../../spec/architecture.md)

---

## 1. Zweck

Diese Roadmap fuehrt die Meilensteine, die sich aus dem Lastenheft und
der Architektur ergeben. Sie ist die Quelle fuer die Status-Spalte
der `GG-TRACE-001`-Implementierungsmatrix
([Lastenheft §27.2](../../../../spec/lastenheft.md#272-anforderung-zu-implementierung))
mit `M[N]`-Markern.

`GG-AR-OPEN-001` (Sprach- und Build-Wahl) ist mit `ADR 0002`
(`Accepted` 2026-05-15) geschlossen. M1 (Tick-Loop-Spine) ist seit
2026-05-17 `Done` — Closure-Notiz in
[`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md) +
Welle-Tabelle in
[`done/M1-tick-loop-results.md`](../done/M1-tick-loop-results.md).
M2..M6 sind vorbelegt (Scope-Skizze hier, aktive Slice-Plaene
wandern bei Aktivierung nach `next/` bzw. `in-progress/`).
Aktiver Slice: **M5 (UI + Demo)** — Slice-Plan wird mit
M5-Welle-0-Start eroeffnet. (M4 ist abgeschlossen, siehe
[`done/M4-results.md`](../done/M4-results.md).)

M2 ist abgeschlossen: Slice-Plan ist nach `done/` gewandert
([`done/M2-devices.md`](../done/M2-devices.md)) inkl. Welle-7-Closure
([`done/M2-devices-results.md`](../done/M2-devices-results.md)).
M3 ist abgeschlossen: Slice-Plan ist nach `done/` gewandert
([`done/M3-faults-agents-observability.md`](../done/M3-faults-agents-observability.md))
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

## 3. Meilensteine

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
  - [x] Welle 0 — Vorbereitung (ADR 0007 Provisional, Trigger 001,
        Lock-Refresh) (2026-05-15).
  - [x] Welle 1 — Domain-Modelle (`Quality`/`CommandResult`/
        `RunMetadata`/`TelemetryPoint`/`Command`/`Event`/
        `SnapshotEnvelope`) (2026-05-17).
  - [x] Welle 2 — Driven-Ports (`ClockPort`/`RandomPort` +
        `MersenneTwisterRandomPort` Adapter, ADR 0007 Accepted)
        (2026-05-17).
  - [x] Welle 3 — Scheduler mit Tie-Breaking
        `(time, priority, source, sequence, event_id)` (`GG-ARCH-006`)
        (2026-05-17).
  - [x] Welle 4 — TickLoop + Snapshot-Envelope-Composition
        (`GG-SIM-005`, ADR 0010) (2026-05-17).
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
        [`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md)
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
  [`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md),
  Welle-Tabelle
  [`done/M1-tick-loop-results.md`](../done/M1-tick-loop-results.md).

### M2 — Geraetemodelle

**Slice-Plan:** [`done/M2-devices.md`](../done/M2-devices.md)
(Closure-Notiz); Welle-Tabelle + Abnahme-Belege:
[`done/M2-devices-results.md`](../done/M2-devices-results.md);
Welle-6c-Slice-Begleit:
[`done/welle-6c.md`](../done/welle-6c.md).

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
        (`GG-BESS-001..008`) — M2 Welle 2, ADR 0014 `Accepted`.
  - [x] `PV`-Modell — M2 Welle 3a, ADR 0016 `Accepted`.
        Welle-3-Minimum (konstantes `rated_power_kw`-Modell);
        Generationsprofil-Eingang ist Welle-5-Material.
  - [x] `Load`-Modell — M2 Welle 3b, ADR 0016 `Accepted`.
  - [x] `SmartMeter`-Modell — M2 Welle 4b (`94efb2a`),
        ADR 0018 `Accepted`.
  - [x] `GridConnection`-Modell (`GG-GRID-001..007`) — M2 Welle 4a
        (`b73b44a`), ADR 0017 `Accepted`.
  - [x] `TickLoop.tick()` ruft Geraete-`tick()`s in stabiler
        Reihenfolge auf; Telemetry-Sammlung pro Tick deterministisch
        sortiert — M2 Welle 6a (`27a441f`); Welle-6c (`c31052c`)
        pinnt die Determinismus-Pflicht zusaetzlich per
        Permutations-Property-Test + MVP-Demo-Determinismus-Run.
  - [x] Geraete-Snapshot-Sub-Snapshots in `SnapshotEnvelope`-
        Composition (Trigger 014 generischer Codec in Welle 0a
        geliefert — siehe `done/014-generic-snapshot-format-codec.md`)
        — M2 Welle 6a (`27a441f`), ADR 0015 `Accepted`.
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

**Aktiver Slice: M5.** M4 ist `Done` (2026-06-01,
siehe [`done/M4-results.md`](../done/M4-results.md)): 9
Wellen 0..6b geliefert (5 produktive Adapter + 2 Cross-
Adapter-Hardening-Wellen); sechs M4-ADRs (0030/0031/0032/
0033/0034/0035) auf `Accepted`; `make gates` cache-frei
gruen ohne Override mit 10 A-1-Gates inkl. NEU
`spdx-check`; 1584 Unit-Tests + 35 passed + 4 skipped
Integration-Tests; 20 A-1-Contracts (14 arch_check inkl.
NEU `AC-IEC61850-GPL-BOUNDARY`). `make fullbuild`
pre-existing rot wegen krb5-CVE-Drift seit M3-Welle-7-
`c61ab0d` (nicht durch M4 verursacht; Base-Image-Bump
als M5-Welle-0-Trigger). M3 ist `Done` (2026-05-25,
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
        (M3-Welle-1 + Welle-2: ADR 0022 + ADR 0025).
  - [x] Mindestens ein konkreter Fault-Typ pro
        `Battery`/`Grid`-Achse implementiert: Battery
        `cell_failure` + Grid `voltage_drop` (M3-Welle-2-Closure
        `91d44e2`).
  - [x] Recovery-Verhalten je Fault dokumentiert + getestet:
        `auto-recover-after-N-ticks` + `manual-via-command`
        (ADR 0025 §2.1; Property-Tests fuer half-open
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
[`M4-protocol-adapters.md`](../done/M4-protocol-adapters.md)
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
        Lizenz-/Smoke-Hardening (SPDX-Lint, AC-IEC61850-GPL-
        BOUNDARY-Contract, CONTRIBUTING.md). IedServer-In-
        Process-Smoke aktuell unter 2c-Mock-only-Fallback mit
        Trigger 009 (Welle-6b-C3-Pfad-A-Befund: PyPI-Stand
        identisch zu Welle 5b).
  - [x] AC-ADAPTER-LIGHTWEIGHT bleibt fuer alle protocol_*-Module
        gruen (kein Fachlogik-Sickern). — Welle 1..6b green;
        Welle-6b-C3 erweitert den Filter um Cross-Adapter-Helper
        `_protocol_*.py` (Slice-034-F13-Folge).
  - [x] Integration-Tests pro Adapter via testcontainers (analog
        Welle 6c). — In-Process-Smokes statt testcontainers wo
        moeglich (Modbus, OPC-UA, DNP3); Mosquitto-MQTT-Smoke
        via Compose-Sibling; IEC-61850-Smoke via 2c-Mock-only-
        Fallback (Trigger 009).

### M5 — UI + Demo (`In Progress` 2026-06-01)

Welle 0 eroeffnet 2026-06-01 mit Slice-Doc + Slice-Plan
([`M5-welle-0.md`](M5-welle-0.md) + [`M5-ui-demo.md`](M5-ui-demo.md))
+ Pre-M5-Welle-0-Sondierungs-ADR
[`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md)
mit Maintainer-Decision-Indication „Option 1 (FastAPI +
HTMX + Jinja2 + Chart.js)". Liefer-Stack zur Zeit: C0
`d93ae57` + C0-Review `aa1db52` (12 Findings) + C1
`b8bef6c` (NEU `M5-ui-demo.md`) + C2 (dieser Commit;
Trigger-Triage + Status-Flip).

- **Lieferziel:** Visualisierungs- und Demo-Layer
  (`GG-UI-001..009`, `GG-DEMO-001..00X`).
- **Lastenheft-IDs:** `GG-UI-001..009`, Demo-System aus Spec §24.
- **Architekturartefakte:** `GG-AR-COMP-UI`,
  `GG-AR-PORT-DRG-002` (`UICommandPort`, sofern getrennt vom
  HTTP-API).
- **DoD-Checkliste:**
  - [ ] Web-UI mit Live-Telemetry-Stream
        (`GG-UI-001..006`).
  - [ ] Scenario-Editor (`GG-UI-006..008`).
  - [ ] Demo-Lauf reproduzierbar via `make demo` o. ae.
  - [ ] UI nutzt nur `GG-API-001`/`002`/`003` — kein direkter
        Kern-Zugriff.

### M6 — Performance + Security + CI/CD-Haertung (Vorbelegung)

- **Lieferziel:** harte Performance-Schranken aus `GG-RT-001..005`,
  Sicherheits-Audit (`GG-SAFE-001..006`,
  `GG-SBOM-001..00X` ueber Trigger 008), CI/CD-Vollausbau
  (`GG-CICD-001..00X`).
- **Lastenheft-IDs:** `GG-RT-001..005`, `GG-SAFE-001..006`,
  `GG-CICD-001..00X`, `GG-DEPLOY-001..00X`.
- **DoD-Checkliste:**
  - [ ] 10.000-Points/s-Benchmark (`GG-RT-005`) reproduzierbar.
  - [ ] SBOM-Generierung im CI (Trigger 008 nach `done/`).
  - [ ] GitHub-Actions-Workflow gegen Python 3.13 + 3.14
        (Spike-0-Closure-D-8 + ADR 0002 §6.1).
  - [ ] Image-Audit (`make image-audit`) inkl. Vuln-Scan in CI.
  - [ ] Container-Smoke-Test mit `deploy/compose.yml`
        (`make runtime` pollt `/health`).
  - [ ] **CI-Erweiterung um Tests** (`GG-CICD-002`): `make
        test-unit` + `make test-integration` als CI-Jobs neben
        den vier Slice-025-Pflicht-Gates. Heute Repo-seitig in
        `make gates` enthalten, aber nicht GitHub-seitig
        enforced; Slice 025 §2 hatte das bewusst auf M6
        verschoben.
  - [ ] **CI-Erweiterung um Coverage-Gates** (`GG-CICD-003`):
        `make coverage-gate` (90 % Line / 85 % Branch) +
        `make coverage-gate-critical` (90 % auf
        `CRITICAL_COV_TARGETS`) als CI-Jobs. Slice 025 §2
        ausgelagert; lokal Pflicht via `make gates`.
  - [ ] **CI-Erweiterung um Dependency-Audit** (`GG-CICD-006`):
        `make dep-audit` (`pip-audit`) als CI-Job — meldet
        bekannte Schwachstellen direkter und transitiver
        Abhaengigkeiten. Slice 025 §2 ausgelagert; lokal
        Pflicht via `make gates`.
  - [ ] **Release-Workflow** (`GG-CICD-007`): GitHub-Actions-
        Release-Pipeline, die bei Tag-Push `make sbom`
        (Trigger 008), Container-Images, Test-/Coverage-
        Reports und OpenAPI-Spec als Release-Assets
        publiziert. Aktivierungs-Bedingung fuer Trigger 008
        und damit Grundvoraussetzung fuer die SBOM-DoD oben.

---

## 4. Vorbedingungen

Vor M1 muessen folgende Punkte geklaert sein:

- [x] **`GG-AR-OPEN-001` Sprach- und Build-Wahl** — geschlossen mit
      `ADR 0002` (`Accepted` 2026-05-15) und synchron `ADR 0005`
      (`Accepted` 2026-05-15). Spike-0 Closure-Notiz:
      [`docs/plan/planning/done/spike-0.md`](../done/spike-0.md).
- [x] **`GG-AR-OPEN-002` API/Simulation als ein oder zwei Prozesse**
      — geschlossen mit
      [`ADR 0012`](../../adr/0012-api-simulation-two-processes.md)
      (`Accepted` 2026-05-17): zwei Prozesse, Postgres als
      Persistenz-Bus. Welle-6c-`deploy/compose.yml` hat den
      Pattern de-facto implementiert; ADR 0012 formalisiert
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
      [`done/001-code-review-doc.md`](../done/001-code-review-doc.md).
