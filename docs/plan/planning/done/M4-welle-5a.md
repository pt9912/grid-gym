# Welle 5a — M4 DNP3-Adapter (Spike)

**Status:** Done — geschlossen 2026-05-31 mit M4-Welle-5a-C3
(`docs(plan|adr)` Doc-Sync, dieser Commit). Eroeffnet
2026-05-31 nach M4-Welle-4-Closure (`7937e70` C0 + `74ed35b` C1 + `78fdd7a`
C2 + `7ad5baf` C3 + `45bcf97` Slice-032-feat + `e8fc116`
Slice-032-docs + `1c2dfa3` Slice-032-Nachzug + `3bc015b`
Self-Close-Move + `34e64e6` Pre-C0-Sync) und Sub-Slicing-
Refactor `8f022a3` (§3 Welle 5 in 5a/5b geteilt).

Welle 5a ist die **fuenfte Code-Welle** in M4 und der
**vierte konkrete Adapter** auf der `DeviceProtocolPort`-
Surface (`GG-AR-PORT-DRN-007`): DNP3 (IEEE 1815-2012) ueber
die Pure-Python-Libraries `nfm-dnp3` (Master/Client) und
`dnp3-outstation` (Outstation, nur Test-Sibling). Welle 5a
loest den in ADR 0030 §2.4 als „provisorisch" markierten
DNP3-Verzicht-Default per Spike-Lieferung auf (M4-Welle-7-
Closure schaerft dann ADR 0030 §2.4 auf „aufgeloest").

**Liefer-Hashes:**

- C0 `43d0b07` — `docs(plan): M4-welle-5a Slice-Doc (M4 Welle-5a DNP3 Beginn)`.
- C1 `b0fea7e` — `docs(adr): ADR 0034 Proposed — DNP3-Adapter-Profile (M4 Welle 5a)`.
- C2 `224b370` — `feat(welle-5a): protocol_dnp3 + Tests + In-Process-Smoke + Compose-Edit`.
- C3 (dieser Commit) — `docs(plan|adr): M4-Welle-5a-C3 — Status/DoD-Sync + ADR 0034 -> Provisional + Top-Level-Doku-Sync`.

**DoD-Verifikation (Welle-Schluss, Stand `224b370` C2 +
dieser Commit):**

- `make test-unit`: **1462 Tests gruen** (Pre-Welle-5a-Stand
  1406 → Welle-5a-Endstand 1462 = +56 Unit-Tests; davon
  17 Config-Validation
  (`tests/unit/adapters/driven/protocol_dnp3/test_dnp3_config.py`),
  16 Codec-Roundtrip inkl. hypothesis-Property-Tests pro
  Welle-5a-Group/Variation
  (`test_dnp3_codec.py`), 17 Protocol-Port-Lifecycle/Read-
  Pfad-gegen-mocked-Master incl. Read/Write-Tax-Pfade
  (`test_dnp3_protocol_port.py`)).
- `make test-integration`: **35 Tests gruen** (Pre-Welle-5a-
  Stand 31 → Welle-5a-Endstand 35 = +4 DNP3-In-Process-
  Smoke-Roundtrips: 3 Class-0-Read pro Initial-Wert + 1
  Update-then-Read; in-process
  `dnp3_outstation.AsyncOutstation` in eigenem Daemon-
  Thread + `asyncio.Event`-Stop-Signal).
- `make arch-check`: **19/19 Contracts KEPT** (7
  lint-imports + 12 `tools/arch_check.py`);
  `AC-ADAPTER-LIGHTWEIGHT` erfasst `protocol_dnp3` ohne
  Filter-Edit (Pfad-Filter `bucket.startswith("protocol_")`
  in `tools/arch_check.py:1089` greift unveraendert).
- `make gates`: **alle 9 A-1-Gates gruen** ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste um
  `src/grid_gym/adapters/driven/protocol_dnp3` erweitert).
- `make fullbuild`: Compose-Smoke selbst (in-process
  AsyncOutstation; kein neuer Sibling) gruen; `image-audit`
  weiter rot aus dem **dokumentierten** Pre-existing krb5-
  CVE-Grund (M3-Welle-7-`c61ab0d`-Drift; **nicht durch
  M4-Welle-5a-Code verursacht**).
- ADR 0034: `Proposed → Provisional` (Decisions D-a/D-b/
  D-c/D-d/D-e alle **final**; Status-Pfad in
  [`../../adr/0034-dnp3-adapter-profile.md`](../../adr/0034-dnp3-adapter-profile.md) §5
  mit Hashes belegt).
- **Zwei-Library-Setup**:
  `nfm-dnp3>=1.0,<2.0` in `[project] dependencies` (MIT,
  Pure-Python, Beta `Development Status :: 4`);
  `dnp3-outstation>=0.2,<1.0` in `[dependency-groups.dev]`
  (MIT, Pure-Python, asyncio-native, IEEE-1815-2012-Level-
  1-Subset, **nur** Test-Sibling). Wire-Compat zwischen
  beiden Libraries per C1-Probe-Run **und** C2-Smoke
  verifiziert (Class-0-Read-Roundtrip; qualifier 0x01
  inkompatibel — siehe ADR 0034 §1 + §3 A4).
- **mypy-Overrides** fuer `dnp3py.*` und
  `dnp3_outstation.*` mit `ignore_missing_imports = true`
  (beide Libraries liefern kein py.typed-Marker).
- **C2-Library-Bug-Find:** `AnalogInput`-Field heisst
  `.index`, nicht `.idx` (letzteres ist nur die
  `__repr__`-Kurzform). Adapter und Test-Mocks
  entsprechend gefixt; ADR-0034-Status-Header
  dokumentiert.

Kanonische Slice-Spezifikation:
[`M4-protocol-adapters.md §3 Welle 5a`](../done/M4-protocol-adapters.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht Ersatz.

**Spec-Reife:** Decisions D-a/D-b/D-c/D-d/D-e durch
C1-Probe-Runs und C2-Smoke-Belege final. Decision D-b
ist **direkt-sync** (Welle-3-Modbus-Pattern-Praezedenz)
— `nfm-dnp3.DNP3Master` ist sync-by-design (C1-Probe-Run
verifiziert: alle public Methoden ohne async-Marker).

---

## 1. Context

M4-Welle-4 hat den dritten konkreten `DeviceProtocolPort`-
Implementer produktiv geliefert (`OpcuaDeviceProtocolPort`,
ADR 0033 `Provisional`) ueber `asyncua 1.2b2` mit eigenem
`OpcuaLoopThread`-Marshal — **erster rein-async-Stack** im
Repo. Slice-032-Review-Folge (6 HIGH + 11 MEDIUM Findings)
hat die Loop-Thread-Konstruktion produktiv-stabil
geschaerft (Lifecycle-Lock, Teardown-Race, Exception-Filter).

Welle 5a ist der **vierte konkrete Implementer**:

- NEU `src/grid_gym/adapters/driven/protocol_dnp3/`-Modul
  mit `nfm-dnp3 1.0.x`-Wrapper als `DeviceProtocolPort`-
  Implementer (`GG-DNP3-001`).
- NEU ADR 0034 (DNP3-Adapter-Profile) als Surface-relevanter
  Adapter-ADR. DNP3-spezifische Decisions: Point-Schema
  (Group/Variation/Index), Async-Bridge-Wahl (vermutlich
  direkt-sync wie Modbus), Function-Code-Mapping,
  Read-Qualifier, Test-Sibling.
- NEU Integration-Smoke via **in-process `dnp3-outstation`-
  Server** (Pattern-Praezedenz Welle-3-Decision-M-f mit
  pymodbus + Welle-4-Decision-O-e mit asyncua-Server).

**Library-Lage (verifiziert 2026-05-31 via PyPI):**

- **Master/Client: `nfm-dnp3` 1.0.1** (PyPI, MIT, Pure-
  Python, `dnp3py` als Import-Name, Beta `Development
  Status :: 4`). Bietet `DNP3Master`-Klasse mit voller
  Protocol-Stack-Implementierung (Data Link / Transport /
  Application Layer), TCP/IP-Kommunikation, Class-0/1/2/3-
  Polling, CRC-16. Primaer sync API mit Thread-Lock-Schutz
  (`DNP3Master supports concurrent use (open/close/
  requests protected by a lock)`). Python 3.9+. Repo
  `fxodell/dnp3py`.
- **Outstation/Server (nur Test-Sibling): `dnp3-outstation`
  0.2.0** (PyPI, MIT, Pure-Python, asyncio-native,
  IEEE-1815-2012-Level-1-Subset, aarch64-compatible).
  `joenarvaez/dnp3-outstation`. Group 30 / Variation 5
  (32-bit float analog inputs) als Minimum-Profile; READ
  qualifier 0x06 (class-0 / integrity poll) und 0x00
  (8-bit range) supported. Interop **mit dem rust `dnp3`
  v1.6 master crate** verifiziert (laut README) — Interop
  mit `nfm-dnp3` ist **nicht** vorab verifiziert und ist
  Welle-5a-C2-Verifikations-Pflicht (siehe §7 Risiken).

**Architektonische Folge:**

- Welle 5a hat **zwei** Python-Pakete als Dependency
  (`nfm-dnp3` produktiv, `dnp3-outstation` als Test-only),
  weil keine Library beide Seiten produktiv-stabil
  abdeckt. Pattern-Praezedenz: Welle-3-Modbus mit pymodbus
  hat **eine** Library fuer Client+Server. Welle 5a weicht
  bewusst ab — der Sub-Slicing-Refactor `8f022a3` hat das
  bereits dokumentiert.
- `dnp3-outstation` wird als **Dev-Dependency** in
  `pyproject.toml` `[dependency-groups.dev]` oder
  `[project.optional-dependencies.test]` gepinnt (nicht
  in `[project] dependencies`), weil sie nur fuer den
  Integration-Smoke benoetigt wird. Production-Adapter
  laeuft mit `nfm-dnp3` alleine.

Welle 5a liefert **keinen** IEC-61850-Adapter (Welle 5b)
und **keinen** OTel-Span-Wrap der Adapter-Calls (Welle 6).

---

## 2. Scope

**In Scope:**

1. NEU `docs/plan/adr/0034-dnp3-adapter-profile.md` in C1
   als `Proposed`. Entscheidungen:
   - **Decision D-a (Point-Schema, final)**: Point-Profile
     werden **inline** im `protocol_ports`-Scenario-YAML-
     Block deklariert. Pattern uebernommen direkt von
     ADR 0031 §2.1 / ADR 0032 §2.1 / ADR 0033 §2.1.
     Pro `device_id` ein `Dnp3PointConfig` mit Pflicht-
     Feldern `group`/`variation`/`index`/`access`.
   - **Decision D-b (Async-Bridge, in C1 fixiert)**:
     **direkt-sync** wie Modbus-Decision-M-c (`nfm-dnp3`
     ist primaer sync). Kein Adapter-interner Loop-Thread.
     Alternative (verworfen-bedingt): `OpcuaLoopThread`-
     Reuse, falls `nfm-dnp3`-API tatsaechlich async-
     dominanter waere als die README zeigt.
   - **Decision D-c (Datatype + Group/Variation-Set,
     final)**: Welle-5a-Minimum:
     - Group 1 (Binary Input, single-bit) — Python `bool`.
     - Group 30 / Variation 5 (32-bit float analog) —
       Python `Decimal(repr(float))` analog Welle-3-
       Modbus-`float32`-Pfad.
     - Group 30 / Variation 1 (32-bit integer analog) —
       Python `int`.
     Andere Groups (Counter, Binary Output, Analog Output)
     Welle-6+-Schaerfung.
   - **Decision D-d (Read-Pfad, final)**: Polling-Read via
     `DNP3Master.read_class(class_=0, ...)` (integrity
     poll, qualifier 0x06) als Default. Per-Target-Override
     via `DNP3Master.read_range(group, variation, start,
     stop)` (qualifier 0x00). Subscription-/Event-Class-
     Polling (Class 1/2/3) bleibt Welle-6-Schaerfung.
   - **Decision D-e (Test-Sibling, final)**: **in-process
     `dnp3-outstation` Server** in eigenem
     `threading.Thread(daemon=True)` mit asyncio-Loop
     (`dnp3-outstation` ist asyncio-native). Pattern-
     Praezedenz Welle-3-M-f + Welle-4-O-e. Wire-Compat
     gegen `nfm-dnp3`-Master ist **nicht** vorab
     verifiziert — C2 muss explizit testen, dass die
     beiden Libraries miteinander reden (siehe §7
     Risiken).
2. NEU
   `src/grid_gym/adapters/driven/protocol_dnp3/__init__.py`:
   `Dnp3DeviceProtocolPort`-Klasse als
   `DeviceProtocolPort`-Implementer.
   - `start()`: `DNP3Master(config).open()` (sync,
     blocking; thread-safe per Lib-Doku). Idempotent.
   - `stop()`: `master.close()`. Idempotent.
   - `read(target)`: Lookup `Dnp3PointConfig` per
     `device_id`; `master.read_range(group, variation,
     index, index)` ODER `master.read_class(0)` mit
     Resultat-Filter; Wert -> Python-Native via Codec;
     `TelemetryPoint` verpacken.
   - `write(target, command)`: Lookup `Dnp3PointConfig`;
     Welle-5a-Minimum **nur Read** — Write-Pfad wirft
     `OpcuaPortWriteAccessMismatchError`-aequivalent.
     Welle-6-Schaerfung kann Write-Pfad einfuehren.
   - Modul-Docstring mit Lastenheft-Z. 1161–1163-Pflicht:
     **„Simulations-/Testadapter; keine produktive
     Anlagensteuerung"**.
3. NEU
   `src/grid_gym/adapters/driven/protocol_dnp3/_config.py`
   mit `Dnp3ProtocolPortConfig` + `Dnp3PointConfig`-
   frozen-dataclasses; Konstruktor-Validation mit
   `Dnp3ConfigError`-Familie (analog `ModbusConfigError`-
   Familie aus Welle 3 + `OpcuaConfigError`-Familie aus
   Welle 4).
4. NEU
   `src/grid_gym/adapters/driven/protocol_dnp3/_codec.py`
   mit `decode_point_value`-Helfer (DNP3-Group/Variation-
   spezifische Datentyp-Konvertierung; Pattern analog
   Welle-3/4-Codecs). Asymmetrie analog ADR 0032 §2.2:
   Encoding strikt (Welle-6 falls Writes), Decoding
   tolerant.
5. NEU
   `src/grid_gym/adapters/driven/protocol_dnp3/_port.py`
   mit `Dnp3DeviceProtocolPort`-Hauptklasse (Decision D-b
   direkt-sync, Decision D-d Polling-Read; nfm-dnp3-
   Exception-Translation).
6. NEU
   `src/grid_gym/adapters/driven/protocol_dnp3/_errors.py`
   mit typed `DeviceProtocolPort*Error`-Subclasses
   inkl. Read/Write-Operation-Tax analog Slice-031/032-
   Pattern.
7. Unit-Tests unter
   `tests/unit/adapters/driven/protocol_dnp3/`:
   - `test_dnp3_config.py`: Konstruktor-Validation
     (Group/Variation-Allowlist, Index-Range,
     Access-Check).
   - `test_dnp3_codec.py`: Datentyp-Roundtrip pro
     Welle-5a-Type (Binary / Int32 / Float32); hypothesis-
     Property-Tests.
   - `test_dnp3_protocol_port.py`: Lifecycle + Read-Pfad
     gegen mocked `DNP3Master`-Klasse.
8. NEU
   `tests/integration/test_dnp3_in_process_smoke.py`:
   - In-process `dnp3-outstation` Server in eigenem
     Daemon-Thread (asyncio-Loop intern).
   - Test wartet auf Connect-Bereitschaft (Bounded-Poll-
     Loop).
   - End-to-End-Read-Roundtrip: `Dnp3DeviceProtocolPort.read(target)`
     -> Server-Datablock -> `TelemetryPoint` durch alle
     Decision-D-c-Group/Variation-Kombinationen.
   - Teardown: Server-Stop + Thread-Join.
9. EDIT `tests/integration/compose.yml`-Header-Kommentar:
   Decision-D-e-Notiz (in-process `dnp3-outstation` als
   Test-Sibling, Pattern-Fortfuehrung aus Welle 3/4).
10. EDIT `pyproject.toml`: `nfm-dnp3>=1.0,<2.0` in
    `[project] dependencies`; `dnp3-outstation>=0.2,<1.0`
    in `[dependency-groups.dev]` (Test-only). Sichtbarkeit
    in AC-PORTS-NO-FW/AC-NO-FW Forbidden-Listen pruefen
    (vermutlich nicht vorbelegt — C1-Edit noetig).
11. EDIT `Dockerfile`: `CRITICAL_COV_TARGETS`-Default um
    `src/grid_gym/adapters/driven/protocol_dnp3`
    erweitert (Pattern analog Welle 2/3/4).
12. C3-Doc-Sync zieht `M4-welle-5a.md`-Status auf `Done`
    und schaerft ADR 0034 von `Proposed` auf
    `Provisional`. Endgueltige Akzeptanz erst mit
    M4-Welle-7-Closure.
13. `make arch-check` weiter `19/19 Contracts KEPT` —
    `AC-ADAPTER-LIGHTWEIGHT` greift fuer `protocol_dnp3`
    via `tools/arch_check.py:1089`
    `bucket.startswith("protocol_")`. Welle-1/2/3/4-
    Regression-Schutz bleibt aktiv.

**Anti-Scope:**

- **Kein IEC-61850-Adapter** (Welle 5b).
- **Kein DNP3-Write-Pfad** (Master-side Direct-Operate /
  Select-Before-Operate). Welle-5a-Minimum ist Read-only.
  Welle 6+ kann Write-Pfad einfuehren.
- **Kein DNP3-Event-Class-Polling** (Class 1/2/3).
  Welle-5a-Minimum ist Class-0-Integrity-Poll. Welle-6-
  Schaerfung offen via ADR 0011.
- **Kein OTel-Span-Wrap** der DNP3-Adapter-Calls.
  Welle-6-Material (ADR 0024 `TracePort`).
- **Keine DNP3-Security (Secure Authentication, IEEE
  1815-2012 §10)** — Welle-5a-Smoke laeuft mit
  Plain-DNP3. Welle-6 oder M6-Material.
- **Kein RandomPort-Determinismus** fuer Point-Indizes.
- **Keine Scenario-Schema-Erweiterung** jenseits des
  Decision-D-a-Pattern.
- **Keine Welle-2/3/4-Adapter-Aenderungen**. Welle-5a-
  DNP3-ADR (0034) ist **Erweiterung**, kein Supersedes
  zu ADR 0031/0032/0033.
- **Keine Bewegung der Open-Trigger**.
- **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md`
  (`DNP3-Adapter`-Checkbox bleibt ungehakt bis Welle 7
  trotz Lieferung; Sweep mit Welle 7).
- **Kein `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-
  Property-Test** (Welle-6-Material; Pattern fortgefuehrt
  aus Welle 2/3/4).
- **Kein gemeinsamer Loop-Thread-Reuse** zwischen
  `protocol_opcua/` und `protocol_dnp3/` (selbst falls
  Decision D-b auf Async-Bridge faellt) — Welle-6-
  Schaerfung kann das nach `_async_bridge/` extrahieren.

---

## 3. Architektur-Entscheidungen

Welle 5a bringt **eine** neue ADR: **ADR 0034**
(`docs/plan/adr/0034-dnp3-adapter-profile.md`), Status-Pfad
`Proposed → Provisional → Accepted`:

- **`Proposed`** mit C1: Initial-Entwurf mit Decision-
  D-a/b/c/d/e-Vorschlaegen + Begruendung + Alternativen +
  Konsequenzen. Pattern analog ADR 0031/0032/0033.
- **`Provisional`** mit C2-Merge: feat-Commit liefert
  `protocol_dnp3/`-Modul + Tests + Integration-Smoke gruen.
- **`Accepted`** mit M4-Welle-7-Closure.

**Bezug:**

- [`spec/architecture.md §7`](../../../../spec/architecture.md)
  Z. 249 (`GG-AR-PORT-DRN-007` Driven-Ports-Tabelle).
- [`spec/lastenheft.md §16`](../../../../spec/lastenheft.md)
  (`GG-DNP3-001` Cluster).
- [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
  Decision-Liste.
- [`../done/M4-protocol-adapters.md`](../done/M4-protocol-adapters.md) §3
  Welle 5a (kanonische Slice-Spezifikation).
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  §2.1 (Sync-Vertrag — `nfm-dnp3` ist sync und passt
  direkt) + §2.2 (Caller-Scope-Lifecycle) + §2.3 (stateless
  aus Replay-Sicht) + §2.4 (DNP3-Verzicht-Default aus
  Welle 1 wird durch Welle-5a-Lieferung aufgeloest;
  M4-Welle-7-Closure schaerft ADR 0030 §2.4 entsprechend).
- [`../../adr/0031-mqtt-adapter-profile.md`](../../adr/0031-mqtt-adapter-profile.md)
  §2.1 (inline-Profile-Pattern).
- [`../../adr/0032-modbus-adapter-profile.md`](../../adr/0032-modbus-adapter-profile.md)
  §2.1 (inline-Register-Schema) + §2.3 (direkt-sync, ohne
  Loop-Thread — Pattern-Praezedenz fuer Welle-5a-Decision-
  D-b).
- [`../../adr/0033-opcua-adapter-profile.md`](../../adr/0033-opcua-adapter-profile.md)
  §2.2 (Async-Bridge via `OpcuaLoopThread`) + §2.5
  (in-process-Server als Test-Sibling — Pattern-Praezedenz
  fuer Welle-5a-Decision-D-e).
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md).
- [`../done/032-opcua-adapter-review-folge.md`](../done/032-opcua-adapter-review-folge.md)
  als Pattern-Praezedenz fuer Slice-Doc-Schaerfungen nach
  Code-Review-Folge (falls Welle-5a-Review aehnliche
  Findings ergibt).

**Vorbelegungs-Liste fuer Welle 5b** (kommt nach 5a):

- ADR 0035 IEC-61850-Adapter-Profile mit
  `iec61850 0.12.x`-Library. Decisions I-a..I-e analog
  Welle-5a-D-a..D-e, aber: `iec61850` ist async (Rust-
  Backend), also Welle-5b-Decision-I-b muss vermutlich
  auf `OpcuaLoopThread`-Reuse-Pattern setzen.

---

## 4. Liefer-Reihenfolge (4 Commits)

### C0 — `docs(plan)`: M4-welle-5a Slice-Doc (Welle-Beginn)

- Dieses Dokument als Welle-Start-Marker. Status:
  `In Progress`.
- Kein README-Sync noetig: `in-progress/README.md` zeigt
  bereits „Naechster aktiver Schritt: M4-Welle-5
  (DNP3/IEC-Disposition)". Welle-5a-Doc-Eintrag in
  `in-progress/README.md` kommt **nicht** als eigener
  Bestand-Tabellen-Zeile (analog M4-Welle-1..4; Welle-N-
  Docs sind Tracking, nicht Roadmap-Bestand).

### C1 — `docs(adr)`: ADR 0034 Proposed — DNP3-Adapter-Profile

- NEU `docs/plan/adr/0034-dnp3-adapter-profile.md` als
  `Proposed`. Inhalts-Skizze:
  - §1 Kontext (`GG-DNP3-001`, ADR-0030-Surface-Bezug,
    ADR-0031/0032/0033-Pattern-Praezedenz, zwei-Library-
    Setup `nfm-dnp3` + `dnp3-outstation`).
  - §2 Entscheidung mit Sub-Sections:
    - §2.1 Decision D-a (Point-Schema inline) +
      Konsequenzen.
    - §2.2 Decision D-b (Async-Bridge: direkt-sync wie
      Modbus, **falls** `nfm-dnp3`-API das stuetzt; sonst
      `OpcuaLoopThread`-Reuse) + Konsequenzen.
    - §2.3 Decision D-c (Group/Variation-Set + Codec) +
      Konsequenzen.
    - §2.4 Decision D-d (Read-Pfad: Class-0-Integrity-Poll
      + Per-Target-Range-Read) + Konsequenzen.
    - §2.5 Decision D-e (Test-Sibling: in-process
      `dnp3-outstation`) + Konsequenzen (Wire-Compat-
      Risiko zwischen den beiden Libraries explizit
      dokumentiert).
  - §3 Alternativen.
  - §4 Konsequenzen (`AC-ADAPTER-LIGHTWEIGHT`-Pflicht,
    Welle-5b-Implementer-Auflage, Welle-6-Schaerfungs-
    Pfade).
  - §5 Status-Pfad (`Proposed → Provisional → Accepted`).
- EDIT `docs/plan/adr/README.md` (neue Zeile fuer
  ADR 0034 mit `Proposed`-Status).

### C2 — `feat(welle-5a)`: protocol_dnp3 + Tests + In-Process-Smoke + Compose-Edit

- NEU `src/grid_gym/adapters/driven/protocol_dnp3/`-Modul.
- NEU 3 Unit-Test-Module (Config / Codec / Protocol-Port).
- NEU `tests/integration/test_dnp3_in_process_smoke.py`.
- EDIT `tests/integration/compose.yml` Header-Kommentar.
- EDIT `pyproject.toml` (`nfm-dnp3` in `[project]
  dependencies`; `dnp3-outstation` in `[dependency-groups.dev]`).
- EDIT `Dockerfile` (`CRITICAL_COV_TARGETS` +
  `protocol_dnp3`).
- EDIT `uv.lock` via `make lock-refresh`.
- `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override.
- `make test-integration` gruen mit DNP3-In-Process-Smoke.
- `make arch-check` weiter `19/19 Contracts KEPT`.

### C3 — `docs(plan|adr)`: Welle-5a Status/DoD-Sync + ADR-Schaerfung

- ADR 0034 `Proposed → Provisional` mit C2-Merge-Beleg.
- `M4-welle-5a.md`-Status `In Progress → Done` mit
  C0/C1/C2-Hashes + DoD-Verifikation-Block + DoD-
  Checkliste (Pattern analog M4-welle-4.md §9).
- `M4-protocol-adapters.md §3 Welle 5a`: Done-Status mit
  Commit-Belegen; DoD-Checkboxen abgehakt.
- README.md / README.de.md / roadmap.md /
  adr/README.md / in-progress/README.md: M4-Status-Sync
  analog M4-Welle-4-C3 `7ad5baf`.

---

## 5. Critical Files

| Pfad                                                                              | Commit | Aktion                                          |
| --------------------------------------------------------------------------------- | ------ | ----------------------------------------------- |
| `docs/plan/planning/in-progress/M4-welle-5a.md`                                   | C0     | NEU (dieses Dokument)                           |
| `docs/plan/adr/0034-dnp3-adapter-profile.md`                                      | C1     | NEU (`Proposed`)                                |
| `docs/plan/adr/README.md`                                                         | C1     | EDIT (ADR-0034-Zeile)                           |
| `src/grid_gym/adapters/driven/protocol_dnp3/__init__.py`                          | C2     | NEU                                             |
| `src/grid_gym/adapters/driven/protocol_dnp3/_config.py`                           | C2     | NEU                                             |
| `src/grid_gym/adapters/driven/protocol_dnp3/_codec.py`                            | C2     | NEU                                             |
| `src/grid_gym/adapters/driven/protocol_dnp3/_port.py`                             | C2     | NEU                                             |
| `src/grid_gym/adapters/driven/protocol_dnp3/_errors.py`                           | C2     | NEU                                             |
| `tests/unit/adapters/driven/protocol_dnp3/__init__.py`                            | C2     | NEU                                             |
| `tests/unit/adapters/driven/protocol_dnp3/test_dnp3_config.py`                    | C2     | NEU                                             |
| `tests/unit/adapters/driven/protocol_dnp3/test_dnp3_codec.py`                     | C2     | NEU                                             |
| `tests/unit/adapters/driven/protocol_dnp3/test_dnp3_protocol_port.py`             | C2     | NEU                                             |
| `tests/integration/test_dnp3_in_process_smoke.py`                                 | C2     | NEU                                             |
| `tests/integration/compose.yml`                                                   | C2     | EDIT (Header-Kommentar)                         |
| `pyproject.toml`                                                                  | C2     | EDIT (`nfm-dnp3` + `dnp3-outstation`)           |
| `uv.lock`                                                                         | C2     | EDIT (via `make lock-refresh`)                  |
| `Dockerfile`                                                                      | C2     | EDIT (`CRITICAL_COV_TARGETS` + `protocol_dnp3`) |
| `docs/plan/adr/0034-dnp3-adapter-profile.md`                                      | C3     | EDIT (`Proposed → Provisional`)                 |
| `docs/plan/adr/README.md`                                                         | C3     | EDIT (Status-Spalte `Provisional`)              |
| `docs/plan/planning/in-progress/M4-welle-5a.md`                                   | C3     | EDIT (Status → Done; DoD)                       |
| `docs/plan/planning/done/M4-protocol-adapters.md`                          | C3     | EDIT (§3 Welle 5a DoD-Checkboxen abgehakt)      |
| `README.md` + `README.de.md` + `docs/plan/planning/in-progress/roadmap.md` + `docs/plan/planning/in-progress/README.md` | C3 | EDIT (M4-Status-Sync — Welle 5a `Done`, ADR 0034 `Provisional`) |

---

## 6. Verifikationspfad

1. **C0 (Slice-Doc)**: `make docs-check` cache-frei gruen.
2. **C1 (ADR Proposed)**: `make docs-check` gruen.
3. **C2 (feat)**:
   - `make test-unit` gruen (1406 → ~1440+ Tests; ~30-40
     neue Tests).
   - `make test-integration` gruen mit DNP3-In-Process-Smoke
     (31 → 32+ Integration-Tests).
   - `make arch-check` 19/19 KEPT.
   - `make gates` cache-frei gruen ohne Override.
   - `mypy --strict-bytes` gruen.
4. **C3 (Doc-Sync)**: `make docs-check` gruen mit
   Welle-5a-Endstand in 5 Docs.

---

## 7. Risiken

- **Wire-Compat zwischen `nfm-dnp3` und `dnp3-outstation`
  nicht vorab garantiert** (HOCH). `dnp3-outstation`-README
  sagt nur Interop gegen den rust `dnp3` v1.6 master crate
  ist verifiziert. Bei Welle-5a-C2 muss das Integration-
  Smoke explizit demonstrieren, dass `nfm-dnp3.DNP3Master`
  einen `dnp3-outstation`-Server lesen kann. *Mitigation*:
  C1 macht einen schnellen Wire-Compat-Probe-Run vor der
  Adapter-Implementierung; bei negativem Ergebnis fallback
  auf `nfm-dnp3`-eigenen Loopback-Test (siehe
  `examples/`-Pfad der Library) oder Mock-only-Smoke.
- **`nfm-dnp3` ist Beta** (`Development Status :: 4`)
  (MEDIUM). API kann zwischen Minor-Versionen breaking
  changes haben. *Mitigation*: Pin `>=1.0,<2.0` plus
  `uv.lock`-Pinning auf 1.0.1 macht den Stand stabil;
  Welle-6 kann auf eine stabilere Release upgraden.
- **`dnp3-outstation` ist v0.2.0** (MEDIUM). Pure-Python-
  Implementierung; Reifegrad-Risiko. Es wird nur als
  Test-Sibling verwendet — Production-Adapter-Pfad ist
  davon entkoppelt. *Mitigation*: Pin `>=0.2,<1.0`; bei
  Drift kann Welle 6 die Library wechseln (z. B. zur
  rust-`dnp3`-Master-Library + opendnp3-Outstation in
  Docker-Sibling), ohne den Adapter-Code zu touchen
  (Wire-Format ist stabil per IEEE 1815-2012).
- **`nfm-dnp3`-API ist primaer sync mit Thread-Locks**
  (LOW). Falls die internen `master.read_*`-Calls aber
  doch async-dominant sind (z. B. internes `asyncio.run`),
  ist Decision-D-b auf `OpcuaLoopThread`-Reuse umzustellen.
  *Mitigation*: C1 macht einen API-Probe-Run; ADR 0034
  §2.2 dokumentiert beide Pfade als reversibel.
- **DNP3-Read-Pfad braucht Class-0-Integrity-Poll vor
  Per-Range-Read** (LOW). `nfm-dnp3` koennte einen
  Connection-Lifecycle-Vertrag haben, der Class-0 als
  Pflicht-Erststep nach Connect verlangt. *Mitigation*:
  C1 prueft API-Doc/Examples; Adapter-`start()` ruft
  Class-0-Read als Init-Step, falls noetig.
- **Sub-Slicing-Schwelle wieder grenzwertig** (LOW).
  Welle 5a = 1 Adapter + 1 ADR + 1 Integration-Smoke =
  Sub-Slicing-Obergrenze (analog Welle 4). *Mitigation*:
  C2-Scope ist normativ in §2 In-Scope-Liste fixiert.
- **Welle-5b-Drift durch Welle-5a-Erfahrung** (LOW). Falls
  Welle 5a zeigt, dass die zwei-Library-Konstruktion
  unpraktikabel ist, koennte Welle 5b auf Variante A
  zurueckfallen. *Mitigation*: Sub-Slicing erlaubt
  Welle-5a-und-5b-Disposition separat; Welle 5b waertet
  Welle-5a-Closure ab.

---

## 8. Wandert nach

- `done/M4-welle-5a.md` mit M4-Welle-5b-Pre-C0-Move
  (Pattern aus M3 und M4-Welle-1..4: `welle-5a.md` wandert
  mit M4-Welle-5b-Pre-C0 nach `done/`).
- ADR 0034 bleibt in `docs/plan/adr/` (kein Move; nur
  Status-Updates).
- `M4-protocol-adapters.md` bleibt in `in-progress/` bis
  M4-Welle-7-Closure.
- M4-Welle-5b-Naechster-Schritt: IEC-61850-Adapter
  (`iec61850 0.12.x`).

---

## 9. DoD-Checkliste (Welle-Schluss, mit C3 abgehakt)

Pattern analog M4-welle-4.md §9. Belege siehe
**DoD-Verifikation**-Block im Status-Header oben + §4
Liefer-Reihenfolge fuer die per-Commit-Aktion.

**In-Scope-Items (alle abgehakt mit C3):**

- [x] **ADR 0034 angelegt** — `Proposed` (C1 `b0fea7e`) →
  `Provisional` (dieser Commit), mit Decisions D-a/D-b/
  D-c/D-d/D-e alle **final** (Point-Schema inline,
  direkt-sync, Group/Variation-Set {1/V1, 1/V2, 30/V1,
  30/V5}, Class-0-Polling-Read mit Filter, in-process
  `dnp3-outstation` Test-Sibling). Code:
  [`../../adr/0034-dnp3-adapter-profile.md`](../../adr/0034-dnp3-adapter-profile.md).
- [x] **DNP3-Port produktiv** — `Dnp3DeviceProtocolPort`
  als `DeviceProtocolPort`-Implementer unter
  [`../../../../src/grid_gym/adapters/driven/protocol_dnp3/`](../../../../src/grid_gym/adapters/driven/protocol_dnp3/)
  (5 Dateien: `__init__.py` + `_config.py` + `_codec.py`
  + `_port.py` + `_errors.py`). Modul-Docstring in
  `__init__.py` traegt Lastenheft-Z.-1161–1163-Pflicht
  (Simulations-/Testadapter, **keine** produktive
  Anlagensteuerung). NEU mit C2 `224b370`.
- [x] **Wire-Compat verifiziert** — C1-Probe-Run
  2026-05-31 + C2-Integration-Smoke
  ([`../../../../tests/integration/test_dnp3_in_process_smoke.py`](../../../../tests/integration/test_dnp3_in_process_smoke.py))
  demonstrieren `nfm-dnp3.DNP3Master.read_class(0)` ↔
  `dnp3_outstation.AsyncOutstation`-Roundtrip durch
  Group 30/V5 (Float-Analog). `read_analog_inputs(start,
  stop)` mit qualifier 0x01 ist bewusst nicht abgedeckt
  (Wire-Compat-Limit; ADR 0034 §1 + §3 A4).
- [x] **Unit-Tests fuer 3 Test-Aspekte** — 56 neue
  Tests (1406 → 1462): 17 Config-Validation + 16
  Codec-Roundtrip (inkl. hypothesis-Property-Tests pro
  Group/Variation) + 17 Protocol-Port-Lifecycle + 6
  Read-Pfad-Edge-Cases (alle Error-Pfade). Code:
  [`../../../../tests/unit/adapters/driven/protocol_dnp3/`](../../../../tests/unit/adapters/driven/protocol_dnp3/).
- [x] **Integration-Smoke produktiv** —
  [`../../../../tests/integration/test_dnp3_in_process_smoke.py`](../../../../tests/integration/test_dnp3_in_process_smoke.py)
  spawnt `AsyncOutstation` in eigenem asyncio-Loop-Thread
  + `asyncio.Event`-Stop-Signal (Pattern aus Welle-4-
  Slice-032-Schaerfung); 3 parametrierte Class-0-Read-
  Roundtrips + 1 Update-then-Read; expliziter Server-
  Shutdown via `outstation.shutdown()` + `loop.stop` +
  `thread.join`.
- [x] **`tests/integration/compose.yml` Header-Kommentar
  syncht** — Welle-5a-C2-Edit dokumentiert die bewusste
  Decision-D-e-Wahl (in-process `AsyncOutstation` statt
  testcontainers-Sibling), Zwei-Library-Setup-
  Klarstellung und Wire-Compat-Hinweis aus ADR 0034 §1.
- [x] **`pyproject.toml` erweitert** — `nfm-dnp3>=1.0,<2.0`
  in `[project] dependencies` (Master, MIT, Pure-Python,
  Beta `Development Status :: 4`); `dnp3-outstation>=0.2,<1.0`
  in `[dependency-groups.dev]` (Outstation, MIT, Pure-
  Python, asyncio-native, **nur** Test-Sibling). mypy-
  Overrides `module="dnp3py.*"` und
  `module="dnp3_outstation.*"` mit
  `ignore_missing_imports = true` (beide Libraries ohne
  py.typed). `nfm-dnp3`/`dnp3-outstation`-Eintraege in
  AC-PORTS-NO-FW/AC-NO-FW-Forbidden-Listen pruefen
  blieb unveraendert (`dnp3py`/`dnp3_outstation` werden
  nur in `adapters/driven/protocol_dnp3/` und
  `tests/integration/test_dnp3_*` importiert).
- [x] **EDIT `uv.lock`** — via `make lock-refresh`
  aktualisiert: 110 packages (+nfm-dnp3 v1.0.1,
  +dnp3-outstation v0.2.0; keine transitiven Deps —
  beide Libraries sind Pure-Python ohne externe
  Abhaengigkeiten).
- [x] **`Dockerfile` erweitert** — `CRITICAL_COV_TARGETS`-
  Default um `src/grid_gym/adapters/driven/protocol_dnp3`
  ergaenzt (Pattern analog `protocol_mqtt`/`protocol_modbus`/
  `protocol_opcua`-Eintraege aus M4-Welle-2/3/4-C2).
- [x] **`AC-ADAPTER-LIGHTWEIGHT` greift fuer
  `protocol_dnp3`** — `tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`-Filter erfasst den
  neuen Pfad **ohne Code-Aenderung**; `make arch-check`
  weiter `19/19 Contracts KEPT`.

**Anti-Scope-Items (alle gehalten):**

- [x] **Kein IEC-61850-Adapter** in C2 — verifiziert:
  keine neue Datei unter
  `adapters/driven/protocol_iec61850/`. Welle 5b folgt.
- [x] **Kein DNP3-Write-Pfad** (Master-side Direct-Operate)
  in C2 — verifiziert: `Dnp3DeviceProtocolPort.write()`
  wirft konsequent `Dnp3PortWriteNotImplementedError`
  fuer alle `access="write"`-Targets (Welle-5a-Anti-
  Scope).
- [x] **Kein DNP3-Event-Class-Polling** (Class 1/2/3) in
  C2 — verifiziert: Adapter ruft nur
  `master.read_class(0)`; kein Class-1/2/3-Pfad im
  `_port.py`.
- [x] **Kein OTel-Span-Wrap** der DNP3-Adapter-Calls —
  verifiziert: kein Import von
  `adapters/driven/telemetry_otlp/` in `protocol_dnp3/`;
  TracePort-Wrap bleibt Welle-6-Material.
- [x] **Keine DNP3-Security** (Plain-DNP3 fuer Smoke) —
  verifiziert: kein Secure-Authentication-Layer (IEEE
  1815-2012 §10) im Welle-5a-Code; Smoke-Endpoint ist
  Plain-DNP3.
- [x] **Kein RandomPort-Determinismus** — verifiziert:
  `Dnp3PointConfig` hat keinen Auto-Generierungs-Pfad
  fuer Index/Group/Variation.
- [x] **Keine Scenario-Schema-Erweiterung** jenseits des
  Decision-D-a-Pattern — verifiziert: kein Touch an
  `scenario/validator.py` und kein neuer YAML-Top-Level-
  Block.
- [x] **Keine Welle-2/3/4-Adapter-Aenderungen** —
  verifiziert: kein Edit an
  `src/grid_gym/adapters/driven/protocol_{mqtt,modbus,opcua}/`
  in C2.
- [x] **Keine Bewegung der Open-Trigger** — verifiziert:
  `docs/plan/planning/open/` unveraendert.
- [x] **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md` —
  verifiziert: `roadmap.md` §3 M4 Checkboxen weiterhin
  alle ungehakt (4 von 7 DoD-Items geliefert nach
  Welle 5a: MQTT + Modbus + OPC-UA + DNP3; Sweep in
  Welle 7).
- [x] **Kein `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-
  Property-Test** in Welle 5a — verifiziert: nur Smoke-
  Regression-Schutz via `make arch-check`. Welle-1-§7-
  Folge-Pflicht bleibt auf Welle 6 verschoben (Pattern
  fortgefuehrt aus Welle 2/3/4).
- [x] **Kein gemeinsamer Loop-Thread-Reuse** zwischen
  `protocol_opcua/` und `protocol_dnp3/` — verifiziert:
  `Dnp3DeviceProtocolPort` ist direkt-sync ohne
  `OpcuaLoopThread`-Import. Welle-6-Schaerfung kann das
  generische Loop-Thread-Pattern nach `_async_bridge/`
  extrahieren, falls Welle 5b (`iec61850`) das nutzen
  will.
