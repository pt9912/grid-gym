# M4 — Protocol Adapters — Closure-Ergebnisse

**Status:** Done (2026-06-01). M4-Abschluss-Gate `make gates`
cache-frei gruen **ohne** `CRITICAL_COV_TARGETS`-Override
mit 10 A-1-Gates (NEU `spdx-check` aus Welle 6b). `make
fullbuild` ist pre-existing rot wegen krb5-CVE-Drift in
Debian-13-Base (`CVE-2026-40356` u. a.; nicht durch M4-Code
verursacht; siehe §2 Defer-Pfad). Alle sechs M4-ADRs
(0030/0031/0032/0033/0034/0035) sind mit Welle-7-C1
`d2071f0` auf `Accepted` promoted.
**Bezug:** Slice-Plan
[`M4-protocol-adapters.md`](../done/M4-protocol-adapters.md);
Welle-Slice-Begleit-Docs
[`M4-welle-0.md`](M4-welle-0.md),
[`M4-welle-1.md`](M4-welle-1.md),
[`M4-welle-2.md`](M4-welle-2.md),
[`M4-welle-3.md`](M4-welle-3.md),
[`M4-welle-4.md`](M4-welle-4.md),
[`M4-welle-5a.md`](M4-welle-5a.md),
[`M4-welle-5b.md`](M4-welle-5b.md),
[`M4-welle-6a.md`](M4-welle-6a.md),
[`M4-welle-6b.md`](M4-welle-6b.md);
Roadmap [`../in-progress/roadmap.md`](../in-progress/roadmap.md)
§3 M4.

---

## 1. Welle-Tabelle

| Welle | Datum        | Lieferung                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Commits                                                                                                                                                                                                       |
| ----- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | 2026-05-26   | Vorabraeumung + Slice-Plan-Eroeffnung (`M4-protocol-adapters.md` als kanonische M4-Slice-Spezifikation) + Trigger-Triage (S-1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | `d0bb16e` (C0 Slice-Doc), `4451c60` (C1 Slice-Plan-Eroeffnung), `9f4ee74` (Review-Folge 13 Findings), C2 Trigger-Triage                                                                                        |
| 1     | 2026-05-30   | ADR 0030 `DeviceProtocolPort-Surface` (Proposed → Provisional); `DeviceProtocolPort`-Protocol + `TickLoop`-Lifecycle-Methoden + 6 typed-Errors + 23 neue Unit-Tests                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | `f8cbe9d` (C0), `b840e7a` (C1 ADR Proposed), `d09adf3` (C2 Implementation), `5f03bbf` (C3), `82f947c` (Linter-Folge), Self-Close `81b5cba`                                                                     |
| 2     | 2026-05-30   | ADR 0031 `MQTT-Adapter-Profile` (Provisional); `protocol_mqtt`-Modul + QoS-0/1 + Per-Target `queue.Queue`-Marshal + Mosquitto-Integration-Smoke + 50 neue Unit-Tests                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | `3b633f6` (C0), `4e102b8` (C1 ADR), `f33bb4e` (C2 Implementation), `7e161f5` (C3), `b7bf40d` (Review-Folge), `51b8694` (Linter), Self-Close `0d6ad6c`                                                          |
| 3     | 2026-05-30   | ADR 0032 `Modbus-TCP-Adapter-Profile` (Provisional); `protocol_modbus`-5-Modul-Paket + 5 Datatypes + FC03/FC10-Defaults + in-process pymodbus-Smoke + 95 neue Unit-Tests; Slice 031 (Review-Folge 8 Findings)                                                                                                                                                                                                                                                                                                                                                                                                                          | `8ef1e72` (C0), `a86ac46` (C1 ADR), `d721982` (C2 Implementation), `7e0a5e6` (C3), Slice 031 `b8cd7e1`, Self-Close `506c8ca`                                                                                   |
| 4     | 2026-05-31   | ADR 0033 `OPC-UA-Adapter-Profile` (Provisional); **Erster rein-async-Stack** via `OpcuaLoopThread`; 8 Datatypes; Polling-Read + Direct-Write; in-process `asyncua.Server`-Smoke; 81 neue Unit-Tests; Slice 032 (Review-Folge 6 HIGH + 11 MEDIUM)                                                                                                                                                                                                                                                                                                                                                                                       | `7937e70` (C0), `74ed35b` (C1 ADR), `78fdd7a` (C2 Implementation), `7ad5baf` (C3), Slice 032 feat `45bcf97` + doc `e8fc116` + Nachzug `1c2dfa3`, Self-Close `3bc015b`                                          |
| 5a    | 2026-05-31   | ADR 0034 `DNP3-Adapter-Profile` (Provisional); **Zwei-Library-Setup** `nfm-dnp3` (Master, MIT) + `dnp3-outstation` (Outstation, MIT, Test-Sibling); Group/Variation-Set {(1,1),(1,2),(30,1),(30,5)}; Class-0-Polling-Read mit Filter; 56 neue Unit-Tests + 4 Integration-Smokes; C2-Library-Bug-Find `AnalogInput.index` (nicht `.idx`)                                                                                                                                                                                                                                                                                              | `43d0b07` (C0), `b0fea7e` (C1 ADR), `224b370` (C2 Implementation), `6903a08` (C3), `76cbdcf` (EoD-Sync), Self-Close `9fea2be`                                                                                  |
| 5b    | 2026-06-01   | ADR 0035 `IEC-61850-Adapter-Profile` (Provisional); **Erstmaliger GPL-isolierter Sub-Module-Praezedenzfall** im Repo (Decision I-f via SPDX-Header pro Datei + `LICENSES/GPL-3.0.txt` + Optional-Extra `pip install grid-gym[iec61850]`); `pyiec61850-ng` als **erste SWIG-/C-native Library** im Repo; 4 Datatypes × FC `{MX,ST,SP,CF,DC}`; In-Process-Smoke unter **2c-Mock-only-Fallback** (Python-3.14-SWIG-Segfault); 75 neue Unit-Tests; Slice 033 (Review-Folge 15 Findings 10 HIGH + 5 MEDIUM)                                                                                                                                  | Pre-C0a `9fea2be`, Pre-C0b `7b5abee`, C0 `19f820a`, C1 `88c1a33`, C1-Review-Folge `da8aed9`, C2 `944bca5`, C3 `ca96bca`, Slice 033 `7e0c91b`, Self-Close `30860ed`                                             |
| 6a    | 2026-06-01   | Cross-Adapter-Hardening Mainstream: OTel-Span-Wrap fuer alle 5 Adapter via `OtelSpanWrappedDeviceProtocolPort`-Composition-Wrapper (ADR 0024 §4.5; Adapter-Code-Diff: NULL); Adapter-Profil-Index `spec/protocol_profiles.md`; Lastenheft §16 auf `✅ M4` × 5; `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-Test (Welle-1-§7-Folge-Pflicht); `[tool.mypy] strict_bytes = true` (Trigger-006-Closure); compose.yml-Header-Konsolidierung; Slice 034 (Review-Folge 15 Findings 1 HIGH + 6 MEDIUM + 4 LOW-MED + 4 LOW; F13 als Welle-6b-Vorlauf)                                                                                              | Sub-Slicing `838d904`, C0 `9776dd9`, C1 `9312239`, C2 `9d3912f`, Pre-C3 `81140e2`, C3 `0a5e895`, C4 `69b37f1`, Slice 034 `bde8fdb`, Hash-Sync `b6a778d`, Self-Close `d1cb65d`, Pre-C0-Sync `7b0e3e4`           |
| 6b    | 2026-06-01   | IEC-61850-Lizenz-und-Smoke-Hardening (Welle-5b-Erbschaft + Slice-034-F13-Vorlauf): NEU `tools/check_spdx.py` als 10. A-1-Gate `make spdx-check`; NEU `AC-IEC61850-GPL-BOUNDARY` als 14. arch_check-Contract (19 → 20 KEPT; AST-Import-Scan); NEU Top-Level `CONTRIBUTING.md` mit Dual-License-Policy; IedServer-Smoke-Reaktivierungs-Probe Pfad-A-Befund (PyPI-Stand identisch zu Welle 5b) → Pfad C aktiv mit Trigger 009; Slice-034-F13-Coverage-Schaerfung (`_is_adapter_lightweight_path` erweitert um Cross-Adapter-Helper `_protocol_*.py`); 18 neue Unit-Tests                                                                  | C0 `14d1bcb`, C1 `8947c62`, C2 `9e2bf39`, C3 `2539574`, C4 `314ccae`, Self-Close `bf23458`, Pre-C0-Sync `5b2dc24`                                                                                              |
| 7     | 2026-06-01   | Closure: sechs M4-ADRs (0030..0035) `Provisional → Accepted`; `done/M4-results.md` (dieses Dokument); `roadmap.md` M4 → `Done`; S-1..S-6-Sweep; `make fullbuild`-krb5-CVE-Defer-Pfad dokumentiert; Self-Close-Move `M4-protocol-adapters.md` + Bezug-Linkpflege ADR 0030..0035; Closure-Konsistenz-Audit (DoD-Boxen + Status-Header + AGENTS.md-Gates-Liste)                                                                                                                                                                                                                                                                            | Pre-C0a `bf23458`, Pre-C0b `5b2dc24`, C0 `af97fd7`, C0-Review `05a1417`, C1 `d2071f0` (6 ADRs → Accepted), C2 `0c644f0` (M4-results.md), C3 `121e255` (Roadmap-DoD + Top-Level-Sync), C4a `e745f10` (git mv), C4b `72e8357` (Cross-Doc-Refs + ADR-Bezug-Linkpflege), Audit-Folge (Closure-Konsistenz)               |

## 2. Abnahme-Belege

- **`make gates`-Gate (harter Welle-7-DoD-Gate)**: cache-frei
  gruen **ohne** `CRITICAL_COV_TARGETS`-Override mit **10
  A-1-Gates**: `lint`, `format-check`, `typecheck`
  (mypy `--strict` + `strict_bytes = true`), `arch-check`
  (20 Contracts), `test-unit`, `coverage-gate` (90 % line /
  85 % branch), `coverage-gate-critical` (90 % critical
  domain), `dep-audit`, `noqa-gate` (Slice 027), **NEU
  `spdx-check`** (Welle 6b — GPL-3.0-only-Header in
  IEC-61850-Boundary).
- **`make fullbuild`-Defer-Pfad (Pre-existing-Drift)**:
  `image-audit` ist seit M3-Welle-7-`c61ab0d` pre-existing
  rot wegen 4 neuer HIGH-CVEs in Debian-13-Base
  (`CVE-2026-40356` u. a. in krb5-Paketen; Fix
  `1.21.3-5+deb13u1` verfuegbar). **Nicht durch M4-Code
  verursacht** — Base-Image-Bump ist separater Stack
  ausserhalb M4-Welle-7-Scope; eigener Trigger-Slice in
  M5-Welle-0 oder fruehestmoeglicher Schaerfungs-Welle
  vorgesehen. Welle 7 macht keinen Base-Image-Bump.
- **Default-`CRITICAL_COV_TARGETS`** (Stand `d2071f0`):
  unveraendert ggue. M3-Welle-7-Stand
  ([`M3-results.md §2`](M3-results.md)); 12 Targets,
  Coverage ≥ 90 % Line + Branch.
- **Unit-Tests**: **1584** (Welle-6b-Endstand; +446 ggue.
  M3-Welle-7-Stand von 1138; +473 ggue. M2-Welle-7-Stand
  von 762).
- **Integration-Tests**: **35 passed + 4 skipped**
  (Welle-6b-Endstand; +14 ggue. M3-Welle-7-Stand von 21).
  Skipped: 4 IEC-61850-In-Process-Smokes via
  `pytest.mark.skip` mit 2c-Mock-only-Fallback-Begruendung
  + Trigger-009-Verweis (Welle-6b-C3-Pfad-C-Defer).
- **Pro-Welle Test-Inkrement** ggue. M3-Welle-7-Stand
  (1138 → 1584, +446 unique):
  - Welle 1 (`DeviceProtocolPort`): **+23** (Surface +
    Lifecycle).
  - Welle 2 (MQTT): **+50** (Codec + Marshal +
    Adapter-Lifecycle).
  - Welle 3 (Modbus): **+95** (5 Datatypes + Byte-Order-
    Matrix + Codec + Lifecycle).
  - Welle 3-Slice 031: **+8** (FC06-Multi-Register-Guard
    + Operation-spezifischer Catch + Codec-Wrap).
  - Welle 4 (OPC-UA): **+81** (8 Datatypes +
    `OpcuaLoopThread` + Codec + Lifecycle).
  - Welle 4-Slice 032: **+6** (Loop-Thread-Lifecycle +
    Marshal-Pfad + String-Read-Quality.INVALID +
    Float-32bit-Quantisierung).
  - Welle 5a (DNP3): **+56** (Group/Variation-Codec +
    Config + Port-Lifecycle).
  - Welle 5b (IEC-61850): **+75** (Codec + Config +
    Port + Mock-Client-Tests).
  - Welle 5b-Slice 033: **+4** (Sentinel-Exception-
    Klasse + `Iec61850PortReadConnectionLostError` +
    `Quality.INVALID`-String-Fallback +
    Sub-Millisekunden-Timeout-Floor).
  - Welle 6a (OTel-Span-Wrap + Planted-Violator):
    **+20** (13 OTel-Span-Wrap + 7 AC-ADAPTER-
    LIGHTWEIGHT-Planted-Violator-Tests).
  - Welle 6a-Slice 034: **+10** (4 OTel-Wrap-Negativ-
    Tests fuer F1/F2/F3 + 2 Planted-Violator-
    Praezisions-Tests).
  - Welle 6b (SPDX + GPL-Boundary + F13): **+18** (9
    SPDX-Lint + 8 GPL-Boundary-Property + 1 F13-Cross-
    Adapter-Helper-Positiv).
- **Total-Coverage**: konsistent ≥ 90 % line + 85 %
  branch via `make coverage-gate`; 90 % critical-domain
  via `make coverage-gate-critical`.
- **A-1-Contracts**: **20** (`make arch-check` 6 import-
  linter + 14 arch_check). 13 arch_check-Contracts aus
  M3 (inkl. `AC-NO-COVERAGE-PRAGMA` aus M3-Welle-5b +
  `AC-OTLP-ADAPTER-NO-TIME` aus M3-Welle-6 + `AC-TICK-
  LOOP-PRIVATE-RESUME-ERRORS` aus M3-Slice-028) plus
  **NEU 14. `AC-IEC61850-GPL-BOUNDARY`** aus M4-Welle-6b
  (Decision I-f Static-Enforcement; AST-Import-Scan ueber
  `src/grid_gym/**/*.py` ausser `protocol_iec61850/*`).
- **`make image-audit`**: pre-existing rot (Defer-Pfad
  siehe oben).
- **`make dep-audit`**: gruen (pip-audit ohne
  Schwachstellen; inkl. `paho-mqtt`, `pymodbus`,
  `asyncua`, `nfm-dnp3`, `dnp3-outstation`,
  `pyiec61850-ng` als Optional-Extra).
- **`make noqa-gate`**: gruen (kein `# noqa`-Marker;
  M3-Slice-027-Compliance ueber M4 durchgehalten).
- **`make spdx-check`** (Welle-6b-NEU): gruen — alle 11
  GPL-Boundary-Files (5 `protocol_iec61850/`-Module + 4
  Unit-Tests + 1 Fixture + 1 Integration-Smoke) tragen
  `SPDX-License-Identifier: GPL-3.0-only`.
- **Trigger-006-Closure** produktiv: `strict_bytes =
  true` in `pyproject.toml` aktiv seit M4-Welle-6a-C3
  `0a5e895`; Trigger-Doc gewandert nach
  [`006-mypy-strict-bytes.md`](006-mypy-strict-bytes.md).
- **5 `DeviceProtocolPort`-Implementer produktiv** —
  alle 5 Cluster aus Lastenheft §16 `GG-MQTT-001` /
  `GG-MODB-001` / `GG-OPCUA-001` / `GG-DNP3-001` /
  `GG-IEC-001` auf `✅ M4` (mit Slice-034-F15-Audit-
  Trail-Note „Erfuellung ueber Pfad A").

## 3. Pro-Welle-Reviews

| Welle | Externer Review                                                                                       | Review-Fix-Commit(s)                                                                                                                                                                  |
| ----- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | ✓ Welle-0-Review-Folge (3 High + 5 Medium + 5 Low)                                                    | `9f4ee74` (kombiniert in feat-Commit) + C2-Status-Flip                                                                                                                                |
| 1     | ✓ ADR-0030-Review (initial) + Linter-Folge                                                            | in C2-Commit `d09adf3` kombiniert; `82f947c` (Linter-Folge fuer mypy-strict-bytes-Vorlauf)                                                                                             |
| 2     | ✓ Welle-2-Review-Folge + Linter-Folge                                                                 | `b7bf40d` (Review-Folge), `51b8694` (Linter-Folge)                                                                                                                                    |
| 3     | ✓ Slice 031 (Welle-3-Review-Folge 8 Findings: FC06-Multi-Register-Guard, operation-spezifische Errors) | [`done/031-modbus-adapter-review-folge.md`](031-modbus-adapter-review-folge.md); Self-Close `0d6ad6c`                                                                                  |
| 4     | ✓ Slice 032 (Welle-4-Review-Folge 6 HIGH + 11 MEDIUM)                                                 | [`done/032-opcua-adapter-review-folge.md`](032-opcua-adapter-review-folge.md); `45bcf97` (feat) + `e8fc116` (doc) + `1c2dfa3` (Nachzug)                                               |
| 5a    | ✓ DoD-EoD-Sync (Welle-5a-Closure-Hash + Test-Counts)                                                  | `76cbdcf` (EoD-Sync) — keine separate Review-Folge noetig (C2-Library-Bug-Find `AnalogInput.index` in C3 dokumentiert)                                                                  |
| 5b    | ✓ C1-Review-Folge (4 Findings: API-Korrektur + Lizenz-Refit + IedServer-Modell-Pflicht + Sync) + Slice 033 (C2-Review-Folge 15 Findings 10 HIGH + 5 MEDIUM) | `da8aed9` (C1-Review), [`done/033-iec61850-adapter-review-folge.md`](033-iec61850-adapter-review-folge.md) `7e0c91b`                                                                   |
| 6a    | ✓ Slice 034 (Welle-6a-Closure-Review 15 Findings 1 HIGH + 6 MEDIUM + 4 LOW-MED + 4 LOW; F13 als Welle-6b-Vorlauf) | [`done/034-iec61850-otel-wrap-review-folge.md`](034-iec61850-otel-wrap-review-folge.md) `bde8fdb` + Hash-Sync `b6a778d`                                                                |
| 6b    | ✓ keine separate Review-Folge (Welle 6b ist Welle-5b-Erbschafts-Hardening + Slice-034-F13-Vorlauf; in C1..C4 sauber durchgezogen) | n/a (C0..C4 ohne Review-Folge geliefert)                                                                                                                                              |
| 7     | ✓ Welle-7-Slice-Doc-Review (3 Blocker + 3 Schaerfungen + 5 Polish)                                    | `05a1417` (Slice-Doc Review-Folge) — Inhaltliche Schaerfung des Welle-7-Plans VOR C1; keine Code-Diffs                                                                                  |

## 4. S-1..S-6-Verification (M4-Welle-7-End-to-End-Sweep)

Spiegelt das M3-Welle-7-Pattern (siehe
[`M3-results.md §4`](M3-results.md)); referenziert
[`M4-protocol-adapters.md §3 Welle 7`](../done/M4-protocol-adapters.md)
S-1..S-6-Items:

- **S-1 (M4-Vorabraeumungs-Item, Trigger-Triage in
  Welle 0; Resultat-Sweep in Welle 7)** — erfuellt in
  Welle 0 (`d0bb16e..C2-Trigger-Triage`); alle relevanten
  M3-Open-Trigger explizit als out-of-scope oder direkt
  fuer M4-relevant markiert. Welle-7-Sweep prueft die in
  M4 dazu-gekommenen Triggers: **Trigger 009 (IEC-61850-
  In-Process-Smoke Reaktivierung)** wurde in Welle-6b-C3
  produktiv aufgemacht (Pfad-C-Defer mit konkretem
  Aktivierungs-Pfad A passiv ODER Pfad B aktiv); alle
  anderen Welle-Folge-Slices 031/032/033/034 sind in
  `done/` produktiv eingezogen, keine weitere M4-Folge-
  Pflicht verbleibt.
- **S-2 (Sub-Slicing-Schwelle)** — erfuellt in
  [`M4-protocol-adapters.md §3 Praeambel`](../done/M4-protocol-adapters.md);
  **aktiv eingesetzt** in zwei Faellen:
  - **Welle 5 → 5a / 5b**: DNP3-Spike (5a) und IEC-61850-
    Spike (5b) waren zu unterschiedlich (Wire-Compat-
    Setup vs GPL-Boundary), um in einer Welle geliefert
    zu werden. Sub-Slicing-Refactor mit eigenen Slice-
    Docs.
  - **Welle 6 → 6a / 6b**: Cross-Adapter-Mainstream (6a:
    OTel-Span-Wrap + Profil-Index + Planted-Violator)
    vs IEC-61850-Lizenz-Folge (6b: SPDX-Lint + GPL-
    Boundary-Contract + CONTRIBUTING.md). Sub-Slicing
    `838d904` 2026-06-01.
  Welle 0/1/2/3/4 sind als einzelne Wellen unter der
  Schwelle geblieben.
- **S-3 (Default-Gate ohne Override)** — erfuellt seit
  M3-Welle-4b (`b5ba33a`); M4 hat die Tradition gehalten,
  `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override am Welle-7-Closure-Hash
  `d2071f0` (10 A-1-Gates inkl. neuer `spdx-check`).
- **S-4 (M4-spezifisches `make image-audit`-Resultat
  ODER dokumentierter Defer-Pfad)** — **Defer-Pfad
  aktiviert**. `make image-audit` ist pre-existing rot
  seit M3-Welle-7-`c61ab0d` wegen krb5-CVE-Drift in
  Debian-13-Base (`CVE-2026-40356` u. a.). M4-Code hat
  das Problem **nicht verursacht** — Adapter-Deps
  (`paho-mqtt`, `pymodbus`, `asyncua`, `nfm-dnp3`,
  `dnp3-outstation`, `pyiec61850-ng` als Optional-Extra)
  haben keine eigene CVE-Last; sie sind via `make
  dep-audit` gruen. Base-Image-Bump auf Debian-13.x mit
  krb5-Fix ist eigener Slice-Trigger in M5-Welle-0 oder
  fruehestmoeglicher Schaerfungs-Welle. Image-Pin-
  Trigger wegen Adapter-Deps-Image-Size war nicht
  notwendig — `pyiec61850-ng` ist Optional-Extra und
  laueft im Default-Build nicht mit.
- **S-5 (ADR-Erweiterungs-Pattern, ohne Supersedes)** —
  erfuellt durch **sechs neue M4-ADRs** (0030/0031/0032/
  0033/0034/0035), alle als Schaerfungen ohne Supersedes
  (ADR-0011-Pattern konsequent fortgefuehrt). ADR 0030
  ist neuer Port-Slot; ADR 0031/0032/0033/0034/0035 sind
  Adapter-Profile, die ADR 0030 konkret fuer den
  jeweiligen Adapter schaerfen, ohne den Sync-
  `DeviceProtocolPort`-Vertrag zu ersetzen. Verifikation:
  keine Supersedes-Eintraege in den sechs ADRs (manuell
  geprueft per
  `grep -l "Supersedes:" docs/plan/adr/003[0-5]*.md` —
  kein Treffer).
- **S-6 (Lastenheft-Coverage-Sweep nach M4-Closure)** —
  erfuellt in Welle 6a-C1 (initial `9312239`) +
  M4-Welle-7-Re-Sweep:
  - `GG-MQTT-001`: erfuellt durch Welle 2 (ADR 0031;
    `protocol_mqtt/` + Mosquitto-Smoke). **✅ M4**.
  - `GG-MODB-001`: erfuellt durch Welle 3 + Slice 031
    (ADR 0032; `protocol_modbus/` + in-process
    pymodbus-Smoke). **✅ M4**.
  - `GG-OPCUA-001`: erfuellt durch Welle 4 + Slice 032
    (ADR 0033; `protocol_opcua/` + `OpcuaLoopThread` +
    in-process asyncua-Smoke). **✅ M4**.
  - `GG-DNP3-001`: erfuellt durch Welle 5a (ADR 0034;
    `protocol_dnp3/` + dnp3-outstation-Smoke). **✅ M4**
    via Pfad A (Adapter geliefert) — historische
    Akzeptanz erlaubte alternativ dokumentierten
    Out-of-Scope-Verzicht (Slice-034-F15-Audit-Trail-
    Note).
  - `GG-IEC-001`: erfuellt durch Welle 5b + Slice 033 +
    Welle 6b (ADR 0035 inkl. Decision I-f GPL-Boundary;
    `protocol_iec61850/` mit SPDX-Header + AC-Contract;
    Integration-Smoke unter 2c-Mock-only-Fallback mit
    Trigger 009). **✅ M4** via Pfad A (Adapter
    geliefert) — historische Akzeptanz erlaubte
    alternativ dokumentierten Out-of-Scope-Verzicht.
  - `GG-OTEL-001..004`: bereits M3-erfuellt; M4-Welle-
    6a hat das OTel-Span-Wrap-Pattern fuer Adapter
    eingezogen (ADR 0024 §4.5).
  - **M5-Trigger** (UI-Anbindung `GG-UI-001..009`,
    `GG-AGENT-007/008`-Deadlines/Async): bleiben fuer
    M5+/Welle-4c+ aktiv (siehe §5 unten).

## 5. Welle-7-Erbschaft fuer M5+/M6+

Diese Items sind explizit als M4-Closure-Restposten in
`open/` aktiviert oder bleiben aktiv:

**IEC-61850-In-Process-Smoke Reaktivierung**
([`Trigger 009`](../done/009-iec61850-smoke-reactivation.md)):

- Aktuell aktiv via Pfad C (Mock-only-Fallback). Konkrete
  Reaktivierungs-Pfade:
  - **Pfad A passiv**: `pyiec61850-ng` publishet
    `cp314-cp314-manylinux*.whl` ODER `cp310-abi3-
    manylinux*.whl`-ABI3-Wheel mit Python-3.14-Support.
    Bestaetigung via `pip download --python-version 3.14
    --platform manylinux2014_x86_64 --no-deps`.
  - **Pfad B aktiv**: Dockerfile-Multi-Python-Test-Stage
    (eigener Slice `036-iec61850-multi-python-test-
    stage.md` in M5-Welle-0 oder fruehestmoeglicher
    Schaerfungs-Welle; ggf. ADR 0036). Repo-Novum-
    Material.

**Base-Image-Bump fuer krb5-CVE-Drift** (impliziter
M3-Closure-Restposten, in M4-Welle-7 als Defer-Pfad
verlaengert):

- Pre-existing rot seit M3-Welle-7-`c61ab0d`; M4-Welle-7
  hat den Defer-Pfad in `M4-results.md §2 + §4 S-4` und
  `M4-welle-7.md §7 Risiken` dokumentiert. Eigener Slice
  in M5-Welle-0 oder fruehestmoeglicher Schaerfungs-Welle.

**M4-Forward-Linked Triggers** (bereits vor M4 vermerkt,
jetzt re-triaged):

- Trigger 004 (canonical encoder alternative ADR) —
  *Defer auf M5/M6* (M4-Welle-6a-C3-Decision; kein
  gemessener Performance-Druck am Telemetrie-Pfad).
- Trigger 006 (`--strict-bytes`) — *Closed* mit M4-Welle-
  6a-C3 (`[tool.mypy] strict_bytes = true` produktiv;
  Trigger-Doc nach `done/` gewandert).

**OTel-Span-Wrap-Pattern aus Welle 6a:**

- `OtelSpanWrappedDeviceProtocolPort`-Composition-Wrapper
  als wiederverwendbares Pattern fuer M5+/M6+ falls
  weitere Adapter-Typen dazu kommen (z. B. `SmartMeter`-
  Adapter, `WeatherStation`-Adapter).
- Slice-034-Lehren fuer Wrapper-Design: separate
  `contextlib.suppress`-Bloecke fuer Span-Lifecycle-
  Garantie; operation-spezifischer Exception-Catch
  (read/write); `Literal`-Typed Constructor-Argumente.

**GPL-Boundary-Pattern aus Welle 5b + 6b:**

- SPDX-Header-Lint-Tool `tools/check_spdx.py` ist
  generisches Pattern; bei zukuenftigen GPL-isolierten
  Sub-Modulen (z. B. `protocol_dlms/` falls je
  notwendig) wird `_DEFAULT_GPL_PATHS` erweitert.
- `AC-IEC61850-GPL-BOUNDARY`-Pattern ist Vorbild fuer
  zukuenftige Boundary-Contracts (z. B. `AC-DLMS-GPL-
  BOUNDARY` falls je notwendig). Anleitung „Add a new
  GPL-isolated path" in [`CONTRIBUTING.md`](../../../../CONTRIBUTING.md).

**M5-naechster-Schritt:**

- M5 (UI + Demo) ist als naechster aktiver Slice
  gesetzt. Welle 0 (Slice-Plan-Eroeffnung + Trigger-
  Triage) ist die erste M5-Welle.

**SOLLTE-Geraete/-Netz/-Battery aus M2-Welle-7-Erbschaft**
+ **Multi-Agent-Erweiterungen aus M3-Welle-7-Erbschaft**
bleiben weiterhin als eigene Slices nach M4-Closure
aktiv (siehe
[`M2-devices-results.md §5`](M2-devices-results.md) +
[`M3-results.md §5`](M3-results.md), Trigger
[`016..024`](../open/) + Trigger 030 RL-Adapter).

## 6. M4-Wandert-Nach

- ✓ `in-progress/M4-welle-0.md` → ✓ `done/M4-welle-0.md`
  (Self-Close-Move `556ae9f`).
- ✓ `in-progress/M4-welle-1.md` → ✓ `done/M4-welle-1.md`
  (Self-Close-Move `81b5cba`).
- ✓ `in-progress/M4-welle-2.md` → ✓ `done/M4-welle-2.md`
  (Self-Close-Move `0d6ad6c`).
- ✓ `in-progress/M4-welle-3.md` → ✓ `done/M4-welle-3.md`
  (Self-Close-Move `506c8ca`).
- ✓ `in-progress/M4-welle-4.md` → ✓ `done/M4-welle-4.md`
  (Self-Close-Move `3bc015b`).
- ✓ `in-progress/M4-welle-5a.md` → ✓ `done/M4-welle-5a.md`
  (Self-Close-Move `9fea2be`).
- ✓ `in-progress/M4-welle-5b.md` → ✓ `done/M4-welle-5b.md`
  (Self-Close-Move `30860ed`).
- ✓ `in-progress/M4-welle-6a.md` → ✓ `done/M4-welle-6a.md`
  (Self-Close-Move `d1cb65d`).
- ✓ `in-progress/M4-welle-6b.md` → ✓ `done/M4-welle-6b.md`
  (Self-Close-Move `bf23458`).
- ⏳ `done/M4-welle-7.md` (Slice-Begleit, dieses
  Closure-Dokument lebt parallel dazu) → `done/M4-welle-
  7.md` mit End-of-Wave-Move folgt als M5-Welle-0-Pre-C0
  (analog M3-Welle-7-Pattern).
- ⏳ `done/M4-protocol-adapters.md` →
  `done/M4-protocol-adapters.md` folgt in M4-Welle-7-C4
  als Self-Close-Move (rename-only) + Welle-7-Folge-
  Commit fuer Cross-Doc-Refs + Bezug-Linkpflege an
  ADR 0030..0035 (Verfahren per
  [`../../adr/0028-link-maintenance-accepted-adr-bezug.md`](../../adr/0028-link-maintenance-accepted-adr-bezug.md)).
- M5 wechselt jetzt von `Vorbelegung` (in
  `roadmap.md §3 M5`) auf `Naechster aktiver Slice` —
  der M5-Slice-Plan wird mit M5-Welle-0-Start eroeffnet.

## 7. Nicht-vollzogene Items (bewusst)

- **`make fullbuild` cache-frei gruen**: bewusst NICHT
  in Welle 7 produktiviert. Pre-existing rot seit
  M3-Welle-7-`c61ab0d` wegen krb5-CVE-Drift in
  Debian-13-Base; Base-Image-Bump ist separater Stack
  ausserhalb M4-Welle-7-Scope (siehe §2 + §4 S-4 + §5
  Welle-7-Erbschaft). `make gates` (10 A-1-Gates) ist
  der harte Welle-7-DoD-Gate.
- **IEC-61850-In-Process-Smoke produktiv reaktiviert**:
  bewusst NICHT in Welle 6b/Welle 7 gemacht. Pfad-A-
  Probe-Run-Befund (PyPI-Stand identisch zu Welle 5b)
  hat Pfad A als tot identifiziert; Pfad B ist Repo-
  Novum und verdient eigenen Slice (siehe §5 Welle-7-
  Erbschaft). Welle-6b-C3 hat Pfad C aktiv mit
  Trigger 009 belassen.
- **M5-Slice-Plan-Material**: bewusst NICHT in Welle 7.
  Der M5-Slice-Plan wird mit M5-Welle-0-Start eroeffnet
  (analog M3-Welle-7-Closure und M4-Welle-0-Start-
  Pattern).
- **`tool_version`-Bump**: bleibt auf `0.1.0`
  (`pyproject.toml`); ein Release-Bump kommt mit M6
  (`GG-CICD-007` Release-Workflow + Trigger 008 SBOM-
  Aktivierung).
- **Snapshot-v2→v3-Lese-Migrations-Pfad**: bleibt M6-
  Material (`GG-PERSIST-*`-Slice, M3-Welle-7-Erbschaft
  verlaengert; M4 hat den Snapshot-Vertrag nicht
  beruehrt — Adapter-Code laeuft komplett ausserhalb
  des `TickLoop.snapshot`-Pfads).
- **`GG-AGENT-007/008`-Deadlines/Async**: bleibt Welle-
  4c+/M5-Material (M3-Welle-7-Erbschaft).
- **`GG-SAFE-001..006`-Sicherheits-Audit**: bleibt M6-
  Material (M3-Welle-7-Erbschaft).
- **M4-Status-Header in
  `M4-protocol-adapters.md`**: bleibt nach End-of-Wave-
  Move (in C4) `In Progress` als historisches Artefakt
  im Datei-Body; der `Done`-Status ist im Closure-Block
  gesetzt. Inkonsistenz bewusst (Pattern aus
  `done/M3-faults-agents-observability.md` und
  `done/M2-devices.md`; siehe
  [`M3-results.md §7`](M3-results.md)).
