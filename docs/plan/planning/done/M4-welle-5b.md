# Welle 5b — M4 IEC-61850-Adapter (Spike)

**Status:** Done — geschlossen 2026-06-01 mit M4-Welle-5b-C3
(`docs(plan|adr)` Doc-Sync, dieser Commit). Eroeffnet
2026-06-01 nach M4-Welle-5a-Closure (`43d0b07` C0 + `b0fea7e`
C1 + `224b370` C2 + `6903a08` C3 + `76cbdcf` EoD-Sync +
`9fea2be` Self-Close-Move + `7b5abee` Pre-C0-Sync).

Welle 5b ist die **sechste Code-Welle** in M4 und der
**fuenfte konkrete Adapter** auf der `DeviceProtocolPort`-
Surface (`GG-AR-PORT-DRN-007`): IEC 61850 (MMS-Subset)
ueber die **eine** SWIG-Library `pyiec61850-ng` (Bindings
zu libiec61850 1.6 von MZ Automation, GPLv3). Welle 5b
loest den letzten in ADR 0030 §2.4 als „provisorisch"
markierten Verzicht-Default (IEC-61850) per Spike-Lieferung
auf (M4-Welle-5a hat den DNP3-Verzicht aufgeloest; M4-Welle-
7-Closure schaerft ADR 0030 §2.4 dann auf „aufgeloest fuer
DNP3 **und** IEC-61850").

Welle 5b fuehrt zwei **Pattern-Praezedenzfaelle erstmalig**
im Repo ein:

1. **Lizenz-Boundary innerhalb des Repos** — `protocol_iec61850/`
   und zugehoerige Tests stehen unter GPLv3, der Rest von
   grid-gym bleibt MIT (Dual-License-Policy ueber SPDX-Header
   pro Datei + `LICENSES/GPL-3.0.txt` + Hinweis-Block in
   Top-Level-`LICENSE` und beiden READMEs). Praezedenzfall
   fuer alle zukuenftigen GPL-Library-Bindings.
2. **SWIG-C-Bindings als Adapter-Library** — `pyiec61850-ng`
   ist die erste SWIG-/native-C-Library im Repo (vorher nur
   Pure-Python: `paho-mqtt`, `pymodbus`, `asyncua`, `nfm-dnp3`,
   `dnp3-outstation`). Wheel-Bezug auf manylinux1_x86_64 und
   Windows; **kein** aarch64-Wheel (Raspberry-Pi-64-bit
   bleibt Welle-6-Material).

**Liefer-Hashes:**

- C0 `19f820a` — `docs(plan): M4-welle-5b Slice-Doc (M4 Welle-5b IEC-61850 Beginn)`.
- C1 `88c1a33` — `docs(adr): ADR 0035 Proposed — IEC-61850-Adapter-Profile (M4 Welle 5b)`.
- C1-Review-Folge `da8aed9` — `docs(plan|adr): M4-Welle-5b-C1-Review-Folge — API-Korrektur + Lizenz-Refit + M4-protocol-adapters.md-Sync` (4 Findings adressiert: API-Namen read_value/write_value/Exception-Famille, IedServer-Modell-Pflicht via CFG-Fixture, Lizenz-Metadaten via Optional-Extra statt [project] dependencies, M4-protocol-adapters.md §3 Welle 5b Sync).
- C2 `944bca5` — `feat(welle-5b): protocol_iec61850 + Tests + 2c-Mock-Fallback + GPL-Lizenz-Boundary`.
- C3 `ca96bca` — `docs(plan|adr): M4-Welle-5b-C3 — Status/DoD-Sync + ADR 0035 -> Provisional + Top-Level-Doku-Sync`.
- **C2-Review-Folge (Slice 033, dieser Commit)** — `feat+docs(slice-033): IEC-61850-Adapter-Review-Folge — 15 Findings (10 HIGH + 5 MEDIUM) adressiert ohne ADR-Status-Aenderung` (siehe [`../done/033-iec61850-adapter-review-folge.md`](../done/033-iec61850-adapter-review-folge.md)).

**DoD-Verifikation (Welle-Schluss, Stand `944bca5` C2 +
dieser Commit):**

- `make test-unit`: **1537 Tests gruen** (Pre-Welle-5b-Stand
  1462 → Welle-5b-Endstand 1537 = +75 Unit-Tests; davon
  21 Config-Validation
  (`tests/unit/adapters/driven/protocol_iec61850/test_iec61850_config.py`),
  30 Codec-Roundtrip inkl. 4 hypothesis-Property-Tests pro
  Welle-5b-Datatype + Container-Repr-Rejection + Overflow-
  Pfade (`test_iec61850_codec.py`), 18 Protocol-Port-Lifecycle
  + Read-Pfad-Mock + Error-Translation + Anti-Scope-
  Verifikation (`test_iec61850_protocol_port.py`)).
- `make test-integration`: **35 passed + 4 skipped**
  (Pre-Welle-5b-Stand 35 → Welle-5b-Endstand 35 + 4 IEC-
  Smokes via `pytest.mark.skip` mit expliziter 2c-Fallback-
  Begruendung). Probe-Run-Befund 2026-06-01 hat MMSClient↔
  IedServer-Roundtrip auf Python 3.12 verifiziert (Float
  230.5→230.5, Int32 42→42, String "battery-1"→"battery-1");
  auf grid-gym-Docker-Stack Python 3.14 crasht
  `_pyiec61850.so` aber im SWIG-Layer (exit 139). Welle-6-
  Schaerfungspfade dokumentiert.
- `make arch-check`: **19/19 Contracts KEPT** (7
  lint-imports + 12 `tools/arch_check.py`);
  `AC-ADAPTER-LIGHTWEIGHT` erfasst `protocol_iec61850` ohne
  Filter-Edit (Pfad-Filter `bucket.startswith("protocol_")`
  in `tools/arch_check.py:1089` greift unveraendert).
- `make gates`: **alle 9 A-1-Gates gruen** ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste um
  `src/grid_gym/adapters/driven/protocol_iec61850` erweitert).
- ADR 0035: `Proposed → Provisional` (Decisions I-a/I-b/
  I-c/I-d/I-e/I-f alle **final**; Status-Pfad in
  [`../../adr/0035-iec61850-adapter-profile.md`](../../adr/0035-iec61850-adapter-profile.md) §5
  mit Hashes belegt).
- **Eine-Library-Setup**:
  `pyiec61850-ng>=1.6,<2.0` in
  `[project.optional-dependencies.iec61850]` (GPLv3, Beta
  `Development Status :: 4`, SWIG-Bindings zu libiec61850 1.6
  + Mbed TLS Apache 2.0; manylinux1_x86_64 + Windows-Wheels).
  **Nicht** in `[project] dependencies` und **nicht** in
  `[dependency-groups.dev]` (Drift-Risiko vermeiden,
  User-Vorgabe). Pattern-Praezedenz: Welle-3-Modbus mit
  pymodbus (eine Library fuer Client+Server), **nicht**
  Welle-5a-zwei-Library-Setup.
- **mypy-Override** fuer `pyiec61850.*` mit
  `ignore_missing_imports = true` (kein py.typed-Marker).
- **2c-Mock-only-Fallback aktiviert** (Decision I-e §2.5):
  Integration-Smoke wartet auf Welle-6-Schaerfung (Python-
  3.12-Runtime / Library-Upgrade / Wheel-Rebuild). Welle-5b-
  DoD ist via 18 Mock-Unit-Tests erfuellt.
- **NEU Lizenz-Boundary** (Decision I-f, **erstmaliger Repo-
  Praezedenzfall**): GPLv3-Isolation auf `protocol_iec61850/*`
  + zugehoerige Tests via SPDX-Header pro Datei
  (`# SPDX-License-Identifier: GPL-3.0-only`). NEU
  `LICENSES/GPL-3.0.txt` (Standard-GPL-3.0-Volltext); EDIT
  Top-Level-`LICENSE` mit Hinweis-Block; EDIT `README.md` +
  `README.de.md` mit Lizenz-Sektion + Optional-Extra-
  Install-Beispielen. Rest grid-gym bleibt MIT (Top-Level-
  MIT-Classifier unveraendert).
- **Probe-Run-Library-Findings 2026-06-01**:
  - Reference-Konvention: pyiec61850-ng konkateniert
    MODEL-Name + LD-Name ohne Trennzeichen
    (`simpleIO`+`GenericIO` → `simpleIOGenericIO`).
  - MMSClient-API: `read_value(reference, fc)`/
    `write_value(reference, value)` mit FC-Default `"ST"`
    (Library); Adapter-Default `"MX"` ueberschreibt explizit.
  - Exception-Famille: `MMSError`/`LibraryNotFoundError`/
    `ConnectionFailedError`/`NotConnectedError`/`ReadError`/
    `WriteError`/`MemoryError`/`FileTransferError` (kein
    `MMSClientError`/`ObjectReferenceError` wie urspruenglich
    angenommen — siehe C1-Review-Folge).
  - IedServer-Modell-Pflicht: `IedServer()` ohne `model_path`
    wirft `start()` `ModelError("No data model loaded")` —
    Welle-5b liefert deshalb `simpleIO.cfg`-Fixture im
    libiec61850-nativen Format (kein SCL-XML).

Kanonische Slice-Spezifikation:
[`M4-protocol-adapters.md §3 Welle 5b`](../done/M4-protocol-adapters.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht Ersatz.

**Spec-Reife:** Decisions I-a/I-b/I-c/I-d/I-e/I-f durch
Library-Recherche-Befund 2026-06-01 (siehe §1 Context)
vorbelegt; final-Markierung erfolgt mit C1-Probe-Runs +
C2-Smoke-Belegen. Decision I-b ist **direkt-sync** (nicht
OpcuaLoopThread-Reuse wie urspruengliche M4-Slice-Plan-
Vorbelegung) — `pyiec61850-ng.MMSClient` ist als
Context-Manager mit sync `read()`/`write()`-API
implementiert (Welle-3-Modbus- + Welle-5a-DNP3-Pattern-
Praezedenz, **nicht** Welle-4-OPC-UA).

---

## 1. Context

M4-Welle-5a hat den vierten konkreten `DeviceProtocolPort`-
Implementer produktiv geliefert (`Dnp3DeviceProtocolPort`,
ADR 0034 `Provisional`) ueber die zwei-Library-Konstruktion
`nfm-dnp3` (Master, produktiv) + `dnp3-outstation`
(Outstation, Test-only) — erster M4-Adapter, der **mehrere**
PyPI-Pakete benoetigt, weil keine einzelne Library beide
Seiten produktiv-stabil abdeckt.

Welle 5b ist der **fuenfte konkrete Implementer** und kehrt
zu **einer** Library zurueck (Welle-3-Modbus-Pattern), weil
die Library-Recherche 2026-06-01 gezeigt hat, dass
`pyiec61850-ng` Client (`MMSClient`) **und** in-process-
Server (`IedServer`) in einem Wheel liefert:

- NEU `src/grid_gym/adapters/driven/protocol_iec61850/`-Modul
  mit `pyiec61850-ng 1.6.x`-Wrapper als `DeviceProtocolPort`-
  Implementer (`GG-IEC-001`).
- NEU ADR 0035 (IEC-61850-Adapter-Profile) als Surface-
  relevanter Adapter-ADR. IEC-61850-spezifische Decisions:
  LN/CDC-Schema, Async-Bridge-Wahl (direkt-sync wie
  Modbus + DNP3), MMS-Read-Pfad, FC-Handling, Test-Sibling
  und **NEU Decision I-f Lizenz-Boundary** (GPL-Isolation).
- NEU Integration-Smoke via **in-process `pyiec61850.server.
  IedServer`** in eigenem Daemon-Thread (Pattern-Praezedenz
  Welle-3-Decision-M-f mit pymodbus + Welle-4-Decision-O-e
  mit asyncua-Server + Welle-5a-Decision-D-e mit
  dnp3-outstation; **eine Library** wie Welle 3, **nicht**
  zwei wie Welle 5a).

**Library-Lage (verifiziert 2026-06-01 via PyPI + GitHub):**

- **Adapter-Library (Master/Client + Server):
  `pyiec61850-ng` 1.6.1.2** (PyPI, **GPLv3**, Beta
  `Development Status :: 4`, Python >=3.9, manylinux1_x86_64
  + Windows-Wheels fuer CPython 3.9..3.14). SWIG-Bindings zu
  **libiec61850 1.6** (MZ Automation, GPLv3) inkl. Mbed TLS
  (Apache 2.0). Liefert:
  - **Client** als `pyiec61850.mms.MMSClient`-Context-Manager
    mit sync `read_value(ref, fc)`/`write_value(ref, value)`-API
    + Low-Level-
    SWIG-Wrappers via `pyiec61850.pyiec61850`.
  - **In-process-Server** als `pyiec61850.server.IedServer`
    mit Context-Manager + Lifecycle (`start(port=102)` /
    `stop()`) + Update-Methoden (`update_boolean` /
    `update_int32` / `update_float` / `update_visible_string`
    / `update_quality` / `update_timestamp`) + Control-
    Handler-Hook + GOOSE-Publishing-Hook + Model-Lock.
    Server-Submodul ist `__version__ = "0.1.0"` (Pre-Alpha
    in der Server-Subklasse; Client-MMSClient hingegen
    `1.6.1.2`-stabil).

**Architektonische Folge:**

- Welle 5b hat **ein** Python-Paket als produktive
  Dependency. Pattern-Praezedenz: Welle-3-Modbus mit
  pymodbus (eine Library fuer Client + in-process-Server).
  Welle 5b weicht vom Welle-5a-zwei-Library-Pattern bewusst
  ab — `pyiec61850-ng` deckt beide Seiten ab.
- `pyiec61850-ng` steht in
  `[project.optional-dependencies.iec61850]` als opt-in
  Extra (Decision I-f, Review-Folge 2026-06-01) — Top-
  Level-`pip install grid-gym` bleibt MIT-sauber, GPL
  wird per `pip install grid-gym[iec61850]` aktiviert.
  **Keine** Eintragung in `[project] dependencies` oder
  `[dependency-groups.dev]` (Drift-Risiko vermeiden);
  CI installiert das Extra explizit via Dockerfile-
  `uv sync --extra iec61850`.
- **NEU GPLv3-Lizenz-Boundary**: `src/grid_gym/adapters/driven/protocol_iec61850/*`
  + `tests/unit/adapters/driven/protocol_iec61850/*` +
  `tests/integration/test_iec61850_*` werden GPLv3-isoliert
  via SPDX-Header `// SPDX-License-Identifier: GPL-3.0-only`
  pro Datei. Rest grid-gym bleibt MIT. Praezedenzfall:
  ffmpeg-Python-Wrapper in MIT-Projekten, GTK-Bindings in
  MIT-Tools.

Welle 5b liefert **keinen** OTel-Span-Wrap der Adapter-Calls
(Welle 6) und **keinen** Welle-2/3/4/5a-Adapter-Touch.

---

## 2. Scope

**In Scope:**

1. NEU `docs/plan/adr/0035-iec61850-adapter-profile.md` in
   C1 als `Proposed`. Entscheidungen (alle bereits durch
   Library-Recherche 2026-06-01 vorbelegt, C1-Probe-Runs
   verifizieren):
   - **Decision I-a (LN/CDC-Schema, final)**: LN-Profile
     werden **inline** im `protocol_ports`-Scenario-YAML-
     Block deklariert. Pattern uebernommen direkt von
     ADR 0031 §2.1 / ADR 0032 §2.1 / ADR 0033 §2.1 /
     ADR 0034 §2.1. Pro `device_id` ein `Iec61850LnConfig`
     mit Pflicht-Feldern `object_reference` (LD/LN.DO.DA-
     Pfad), `functional_constraint` (FC: `MX`/`SP`/`ST`/
     `CF` Default `MX` fuer Measurand-Reads),
     `datatype` (`bool`/`int32`/`float`/`string`),
     `access` (`read`).
   - **Decision I-b (Async-Bridge, final)**: **direkt-sync**
     wie Welle-3-Modbus-Decision-M-c und Welle-5a-DNP3-
     Decision-D-b. Kein Adapter-interner Loop-Thread.
     Begruendung: `pyiec61850.mms.MMSClient` ist als
     sync-Context-Manager implementiert (`__enter__` /
     `__exit__` + sync `read()`/`write()`). Alternative
     (verworfen): `OpcuaLoopThread`-Reuse aus Welle 4 — nicht
     noetig, weil keine async-Komponente vorhanden.
   - **Decision I-c (Datatype-Set + FC-Mapping, final)**:
     Welle-5b-Minimum:
     - `bool` → MMS `BOOLEAN` (Server-API
       `update_boolean`, Client-API `read(...)` liefert
       `bool`).
     - `int32` → MMS `INT32` (Server-API `update_int32`,
       Client-API `read(...)` liefert `int`).
     - `float` → MMS `FLOAT32` (Server-API `update_float`,
       Client-API `read(...)` liefert `float`; Python-
       `Decimal(repr(float))`-Codec analog Welle-3-Modbus-
       `float32`-Pfad).
     - `string` → MMS `VISIBLE_STRING` (Server-API
       `update_visible_string`, Client-API `read(...)`
       liefert `str`).
     Andere MMS-Typen (`INT8/16/64`, `UINT*`, `OCTET_STRING`,
     `BIT_STRING`, `UTC_TIME`, Arrays, Structs) Welle-6+-
     Schaerfung.
   - **Decision I-d (Read-Pfad, final)**: Per-Target-Read
     via `MMSClient.read_value(object_reference, fc)`. FC-Default
     `MX` (Measurand-Sub-Tree); FC-Override per Target via
     `Iec61850LnConfig.functional_constraint`-Feld.
     Subscription/Report-Control-Block-Polling bleibt
     Welle-6-Schaerfung.
   - **Decision I-e (Test-Sibling, final)**: **in-process
     `pyiec61850.server.IedServer`** in eigenem
     `threading.Thread(daemon=True)` + Context-Manager-Stop
     (gleiche Library wie Adapter, kein zweites Setup).
     Pattern-Praezedenz Welle-3-M-f (pymodbus) +
     Welle-4-O-e (asyncua) + Welle-5a-D-e (dnp3-outstation;
     **dort** zwei-Library wegen Library-Lage). Wire-Compat
     zwischen `MMSClient` und `IedServer` ist
     **nicht vorab garantiert**, weil beide Submodule
     unterschiedliche `__version__`-Staende haben (Client
     1.6.1.2, Server 0.1.0 Pre-Alpha; siehe §7 Risiken).
     C1 muss explizit per Probe-Run testen.
   - **NEU Decision I-f (Lizenz-Boundary, final)**:
     `src/grid_gym/adapters/driven/protocol_iec61850/*`
     + `tests/unit/adapters/driven/protocol_iec61850/*`
     + `tests/integration/test_iec61850_*` werden
     GPLv3-isoliert via SPDX-Header
     `// SPDX-License-Identifier: GPL-3.0-only` (Python:
     `# SPDX-License-Identifier: GPL-3.0-only`). NEU
     `LICENSES/GPL-3.0.txt` mit Standard-GPL-3.0-Text.
     EDIT Top-Level-`LICENSE` mit Hinweis-Block
     („Except for `src/grid_gym/adapters/driven/protocol_iec61850/`
     and its tests, which are GPL-3.0-only — see
     `LICENSES/GPL-3.0.txt`"). EDIT `README.md` +
     `README.de.md` mit Lizenz-Hinweis-Sektion. Rest
     grid-gym bleibt MIT.
2. NEU
   `src/grid_gym/adapters/driven/protocol_iec61850/__init__.py`:
   `Iec61850DeviceProtocolPort`-Klasse als
   `DeviceProtocolPort`-Implementer.
   - SPDX-Header `# SPDX-License-Identifier: GPL-3.0-only`.
   - `start()`: `MMSClient.__enter__()` (sync, blocking).
     Idempotent.
   - `stop()`: `MMSClient.__exit__()`. Idempotent.
   - `read(target)`: Lookup `Iec61850LnConfig` per
     `device_id`; `client.read_value(object_reference, fc)`
     (FC als Two-Letter-String wie `"MX"`/`"ST"`/`"SP"`/
     `"CF"`); Wert -> Python-Native via Codec;
     `TelemetryPoint` verpacken. Error-Translation:
     `pyiec61850.mms.NotConnectedError` →
     `Iec61850PortReadNotStartedError`;
     `pyiec61850.mms.ConnectionFailedError`/
     `ConnectionTimeoutError` →
     `Iec61850PortConnectError`;
     `pyiec61850.mms.ReadError` →
     `Iec61850PortReadFailedError`;
     `pyiec61850.mms.LibraryNotFoundError` →
     `Iec61850PortLibraryNotInstalledError`.
   - `write(target, command)`: Welle-5b-Minimum **nur Read**
     — Write-Pfad wirft
     `Iec61850PortWriteNotImplementedError` (Pattern aus
     Welle 5a fuer DNP3). Welle-6-Schaerfung kann Write-
     Pfad einfuehren.
   - Modul-Docstring mit Lastenheft-Z. 1155–1157-Pflicht:
     **„Simulations-/Testadapter; keine produktive
     Anlagensteuerung"** (analog Welle 5a) **und**
     GPLv3-Lizenz-Hinweis.
3. NEU `src/grid_gym/adapters/driven/protocol_iec61850/_config.py`
   mit `Iec61850ProtocolPortConfig` + `Iec61850LnConfig`-
   frozen-dataclasses; Konstruktor-Validation mit
   `Iec61850ConfigError`-Familie (analog `Dnp3ConfigError`-
   Familie aus Welle 5a + `OpcuaConfigError`-Familie aus
   Welle 4). SPDX-Header.
4. NEU `src/grid_gym/adapters/driven/protocol_iec61850/_codec.py`
   mit `decode_mms_value`-Helfer (MMS-Datatype-spezifische
   Konvertierung; Pattern analog Welle-3/4/5a-Codecs).
   Asymmetrie analog ADR 0032 §2.2: Encoding strikt
   (Welle-6 falls Writes), Decoding tolerant. SPDX-Header.
5. NEU `src/grid_gym/adapters/driven/protocol_iec61850/_port.py`
   mit `Iec61850DeviceProtocolPort`-Hauptklasse (Decision
   I-b direkt-sync, Decision I-d MMS-Read; pyiec61850-
   Exception-Translation). SPDX-Header.
6. NEU `src/grid_gym/adapters/driven/protocol_iec61850/_errors.py`
   mit typed `DeviceProtocolPort*Error`-Subclasses
   inkl. Read/Write-Operation-Tax analog Slice-031/032-
   Pattern. SPDX-Header.
7. Unit-Tests unter
   `tests/unit/adapters/driven/protocol_iec61850/` (alle
   mit SPDX-Header):
   - `test_iec61850_config.py`: Konstruktor-Validation
     (FC-Allowlist, Object-Reference-Format, Datatype-
     Check).
   - `test_iec61850_codec.py`: MMS-Datatype-Roundtrip pro
     Welle-5b-Type (bool/int32/float/string); hypothesis-
     Property-Tests.
   - `test_iec61850_protocol_port.py`: Lifecycle + Read-
     Pfad gegen mocked `MMSClient`-Klasse.
8. NEU `tests/integration/test_iec61850_in_process_smoke.py`
   (mit SPDX-Header):
   - In-process `pyiec61850.server.IedServer` in eigenem
     Daemon-Thread (Context-Manager fuer Cleanup).
   - Test wartet auf Connect-Bereitschaft (Bounded-Poll-
     Loop).
   - End-to-End-Read-Roundtrip:
     `Iec61850DeviceProtocolPort.read(target)` ↔ Server-
     `update_*` -> `TelemetryPoint` durch alle
     Decision-I-c-Datatypes.
   - Teardown: Server-Stop via Context-Manager + Thread-
     Join.
9. EDIT `tests/integration/compose.yml`-Header-Kommentar:
   Decision-I-e-Notiz (in-process `IedServer` als Test-
   Sibling, Pattern-Fortfuehrung aus Welle 3/4/5a; **eine**
   Library wie Welle 3, anders als Welle 5a).
10. EDIT `pyproject.toml`:
    - NEU `[project.optional-dependencies.iec61850]
      = ["pyiec61850-ng>=1.6,<2.0"]` als opt-in Extra
      (Decision I-f). **Nicht** in
      `[project] dependencies` und **nicht** in
      `[dependency-groups.dev]`.
    - mypy-Override `module="pyiec61850.*"` mit
      `ignore_missing_imports = true` (kein py.typed-Marker).
    - Classifier-Liste pruefen: aktueller Top-Level-MIT-
      Classifier bleibt; **kein** GPL-Classifier hinzufuegen
      (das beschreibt das Top-Level-Werk, das MIT bleibt;
      GPL-Boundary ist File-Level via SPDX dokumentiert).
11. NEU `LICENSES/GPL-3.0.txt` mit Standard-GPL-3.0-Text
    (verbatim aus `https://www.gnu.org/licenses/gpl-3.0.txt`).
12. EDIT Top-Level-`LICENSE` mit Hinweis-Block am Ende:
    „Except for `src/grid_gym/adapters/driven/protocol_iec61850/`
    and its corresponding tests
    (`tests/unit/adapters/driven/protocol_iec61850/` and
    `tests/integration/test_iec61850_*.py`), which link
    against the GPLv3-licensed `pyiec61850-ng` /
    `libiec61850` library and are therefore distributed
    under GPL-3.0-only — see `LICENSES/GPL-3.0.txt`."
13. EDIT `README.md` + `README.de.md` mit Lizenz-Hinweis-
    Sektion (Hinweis am Anfang oder im „License"-Block).
14. EDIT `Dockerfile`: `CRITICAL_COV_TARGETS`-Default um
    `src/grid_gym/adapters/driven/protocol_iec61850`
    erweitert (Pattern analog Welle 2/3/4/5a).
15. EDIT `uv.lock` via `make lock-refresh`.
16. C3-Doc-Sync zieht `M4-welle-5b.md`-Status auf `Done`
    und schaerft ADR 0035 von `Proposed` auf
    `Provisional`. Endgueltige Akzeptanz erst mit
    M4-Welle-7-Closure.
17. `make arch-check` weiter `19/19 Contracts KEPT` —
    `AC-ADAPTER-LIGHTWEIGHT` greift fuer `protocol_iec61850`
    via `tools/arch_check.py:1089`
    `bucket.startswith("protocol_")`. Welle-1/2/3/4/5a-
    Regression-Schutz bleibt aktiv.

**Anti-Scope:**

- **Kein IEC-61850-Write-Pfad** (`MMSClient.write(...)`).
  Welle-5b-Minimum ist Read-only. Welle 6+ kann Write-
  Pfad einfuehren.
- **Kein IEC-61850-Report-Control-Block-Subscription**.
  Welle-5b-Minimum ist Per-Target-Read. Welle-6-
  Schaerfung offen via ADR 0011.
- **Kein GOOSE-Publishing/Subscription**.
  `pyiec61850.server.IedServer` exponiert
  `enable_goose_publishing()` — Welle-5b-Anti-Scope.
- **Kein IEC-61850-9-2 Sampled-Values**. Welle-6 oder
  M6-Material.
- **Kein OTel-Span-Wrap** der IEC-61850-Adapter-Calls.
  Welle-6-Material (ADR 0024 `TracePort`).
- **Keine IEC-61850-Security (TLS + IEC-62351-3,
  IEC-62351-6)** — Welle-5b-Smoke laeuft mit Plain-MMS.
  Welle-6 oder M6-Material.
- **Kein RandomPort-Determinismus** fuer
  Object-Reference-Strings.
- **Keine Scenario-Schema-Erweiterung** jenseits des
  Decision-I-a-Pattern.
- **Keine Welle-2/3/4/5a-Adapter-Aenderungen**. Welle-5b-
  IEC-ADR (0035) ist **Erweiterung**, kein Supersedes
  zu ADR 0031/0032/0033/0034.
- **Keine Bewegung der Open-Trigger**.
- **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md`
  (`IEC-61850-Adapter`-Checkbox bleibt ungehakt bis
  Welle 7 trotz Lieferung; Sweep mit Welle 7).
- **Kein `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-
  Property-Test** (Welle-6-Material; Pattern fortgefuehrt
  aus Welle 2/3/4/5a).
- **Kein gemeinsamer Loop-Thread-Reuse** zwischen
  `protocol_opcua/` und `protocol_iec61850/` (alle anderen
  Adapter ausser `protocol_opcua/` sind direkt-sync,
  einschliesslich Welle 5b).
- **Kein aarch64-Wheel-Support** — piwheels liefert
  `pyiec61850-ng` nur fuer armv7l (32-bit Pi); aarch64-
  Build-Support fuer Raspberry-Pi-64 bleibt Welle-6-
  Material (oder externer Source-Build-Pfad).
- **Kein Anschluss von `pyiec61850.tase2` / `pyiec61850.sv` /
  `pyiec61850.goose`-Submodulen** — Welle-5b-Minimum ist
  ausschliesslich `pyiec61850.mms` + `pyiec61850.server`.

---

## 3. Architektur-Entscheidungen

Welle 5b bringt **eine** neue ADR: **ADR 0035**
(`docs/plan/adr/0035-iec61850-adapter-profile.md`),
Status-Pfad `Proposed → Provisional → Accepted`:

- **`Proposed`** mit C1: Initial-Entwurf mit Decision-
  I-a/b/c/d/e/f-Vorschlaegen + Begruendung + Alternativen +
  Konsequenzen. Pattern analog ADR 0031/0032/0033/0034
  + NEU Decision I-f (Lizenz-Boundary) als
  Praezedenzfall fuer GPL-isolierte Sub-Module.
- **`Provisional`** mit C2-Merge: feat-Commit liefert
  `protocol_iec61850/`-Modul + Tests + Integration-Smoke
  gruen + Lizenz-Boundary-Files (`LICENSES/GPL-3.0.txt`,
  `LICENSE`-Edit, README-Edits, SPDX-Header).
- **`Accepted`** mit M4-Welle-7-Closure.

**Bezug:**

- [`spec/architecture.md §7`](../../../../spec/architecture.md)
  Z. 249 (`GG-AR-PORT-DRN-007` Driven-Ports-Tabelle —
  Welle 5b loest IEC-61850-Verzicht-Default aus §2.4 auf).
- [`spec/lastenheft.md §16`](../../../../spec/lastenheft.md)
  Z. 1155-1157 (`GG-IEC-001` Cluster — SOLLTE-Pflicht;
  Welle 5b liefert die SOLLTE-Erfuellung).
- [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
  Decision-Liste.
- [`../done/M4-protocol-adapters.md`](../done/M4-protocol-adapters.md) §3
  Welle 5b (kanonische Slice-Spezifikation).
- [`../done/M4-welle-5a.md`](../done/M4-welle-5a.md) als
  Pattern-Praezedenz: Adapter-Modul-Struktur (5 Dateien:
  `__init__/_config/_codec/_port/_errors`), Codec-
  Asymmetrie, in-process-Server in Daemon-Thread, ADR-
  Status-Pfad. Welle-5b weicht ab in: eine Library statt
  zwei (Welle-3-Modbus-Pattern), und neue Lizenz-Boundary-
  Decision I-f.
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  §2.1 (Sync-Vertrag — `pyiec61850.mms.MMSClient` ist sync
  und passt direkt) + §2.2 (Caller-Scope-Lifecycle) + §2.3
  (stateless aus Replay-Sicht) + §2.4 (IEC-61850-Verzicht-
  Default aus Welle 1 wird durch Welle-5b-Lieferung
  aufgeloest; M4-Welle-7-Closure schaerft ADR 0030 §2.4
  entsprechend — DNP3 und IEC-61850 beide aufgeloest).
- [`../../adr/0031-mqtt-adapter-profile.md`](../../adr/0031-mqtt-adapter-profile.md)
  §2.1 (inline-Profile-Pattern).
- [`../../adr/0032-modbus-adapter-profile.md`](../../adr/0032-modbus-adapter-profile.md)
  §2.1 (inline-Register-Schema) + §2.3 (direkt-sync, ohne
  Loop-Thread — Pattern-Praezedenz fuer Welle-5b-Decision-
  I-b).
- [`../../adr/0033-opcua-adapter-profile.md`](../../adr/0033-opcua-adapter-profile.md)
  §2.2 (Async-Bridge via `OpcuaLoopThread` — explizit
  **nicht** uebernommen in Welle 5b).
- [`../../adr/0034-dnp3-adapter-profile.md`](../../adr/0034-dnp3-adapter-profile.md)
  §2.5 (in-process-Outstation als Test-Sibling — Pattern-
  Praezedenz fuer Welle-5b-Decision-I-e; aber **eine**
  Library statt zwei).
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md).

**Vorbelegungs-Liste fuer Welle 6** (kommt nach 5b):

- **OTel-Span-Wrap** fuer alle 5 `protocol_*`-Adapter
  (Welle 2/3/4/5a/5b; ADR 0024 §4.5).
- **`AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-Property-Test**
  (Welle-1-§7-Folge-Pflicht; fortlaufend verschoben).
- **Adapter-Profil-Index** unter `spec/protocol_profiles/`
  mit Verweisen auf ADR 0031..0035.

---

## 4. Liefer-Reihenfolge (4 Commits)

### C0 — `docs(plan)`: M4-welle-5b Slice-Doc (Welle-Beginn)

- Dieses Dokument als Welle-Start-Marker. Status:
  `In Progress`.
- Kein zusaetzlicher README-Sync noetig: Pre-C0b-Sync
  `7b5abee` hat den Welle-5b-Library-Recherche-Befund
  bereits in `in-progress/README.md` und `roadmap.md`
  verankert. C0-Slice-Doc-Eintrag in `in-progress/README.md`
  kommt nicht als eigener Bestand-Tabellen-Zeile (analog
  M4-Welle-1..5a; Welle-N-Docs sind Tracking, nicht
  Roadmap-Bestand).

### C1 — `docs(adr)`: ADR 0035 Proposed — IEC-61850-Adapter-Profile

- NEU `docs/plan/adr/0035-iec61850-adapter-profile.md` als
  `Proposed`. Inhalts-Skizze:
  - §1 Kontext (`GG-IEC-001`, ADR-0030-Surface-Bezug,
    ADR-0031..0034-Pattern-Praezedenz, eine-Library-Setup
    `pyiec61850-ng` Client + Server, GPLv3-Library-Lizenz).
  - §2 Entscheidung mit Sub-Sections:
    - §2.1 Decision I-a (LN/CDC-Schema inline) +
      Konsequenzen.
    - §2.2 Decision I-b (Async-Bridge: direkt-sync wie
      Modbus + DNP3, nicht OpcuaLoopThread-Reuse) +
      Konsequenzen.
    - §2.3 Decision I-c (Datatype-Set + FC-Mapping) +
      Konsequenzen.
    - §2.4 Decision I-d (Read-Pfad: Per-Target MMS-Read
      mit FC-Override) + Konsequenzen.
    - §2.5 Decision I-e (Test-Sibling: in-process
      `pyiec61850.server.IedServer`) + Konsequenzen
      (Wire-Compat-Risiko zwischen MMSClient-1.6.1.2 und
      IedServer-0.1.0-Pre-Alpha explizit dokumentiert).
    - **§2.6 NEU Decision I-f (Lizenz-Boundary)** +
      Konsequenzen. Praezedenzfall-Begruendung:
      `pyiec61850-ng` ist GPLv3 (libiec61850-Bindings),
      grid-gym ist MIT. Dual-License-Setup via SPDX-Header
      pro Datei, `LICENSES/GPL-3.0.txt`, Top-Level-
      `LICENSE`-Hinweis, READMEs. Erklaerungs-Notiz:
      Welle-6/7-Pflicht ist `CONTRIBUTING.md`-Sync (falls
      vorhanden) — Welle-5b-Minimum ist nur SPDX +
      Top-Level-LICENSE.
  - §3 Alternativen (drei Pfade vor Decision I-f):
    Disposition-only (kein Adapter), test-only Spike
    (GPL nur in `[dependency-groups.dev]`), oder MIT-
    `py61850`-GOOSE-Spike (Pre-Alpha-Library mit anti-Scope-
    MMS). Begruendung warum Decision I-f (Dual-License
    mit GPL-Boundary auf `protocol_iec61850/*`) gewaehlt
    wurde.
  - §4 Konsequenzen (`AC-ADAPTER-LIGHTWEIGHT`-Pflicht,
    Welle-6/7-Implementer-Auflagen, Welle-6-Schaerfungs-
    Pfade einschliesslich CONTRIBUTING.md-Sync).
  - §5 Status-Pfad (`Proposed → Provisional → Accepted`).
- EDIT `docs/plan/adr/README.md` (neue Zeile fuer
  ADR 0035 mit `Proposed`-Status).

### C2 — `feat(welle-5b)`: protocol_iec61850 + Tests + In-Process-Smoke + GPL-Lizenz-Boundary

- NEU `src/grid_gym/adapters/driven/protocol_iec61850/`-Modul
  (5 Dateien, alle mit SPDX-Header).
- NEU 3 Unit-Test-Module (alle mit SPDX-Header):
  Config / Codec / Protocol-Port.
- NEU `tests/integration/test_iec61850_in_process_smoke.py`
  (mit SPDX-Header).
- NEU `LICENSES/GPL-3.0.txt` (Standard-GPL-3.0-Volltext).
- EDIT `LICENSE` (Hinweis-Block GPL-Boundary).
- EDIT `README.md` + `README.de.md` (Lizenz-Hinweis-
  Sektion).
- EDIT `tests/integration/compose.yml` Header-Kommentar.
- EDIT `pyproject.toml` (`pyiec61850-ng` in `[project]
  dependencies`; mypy-Override).
- EDIT `Dockerfile` (`CRITICAL_COV_TARGETS` +
  `protocol_iec61850`).
- EDIT `uv.lock` via `make lock-refresh`.
- `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override.
- `make test-integration` gruen mit IEC-61850-In-Process-
  Smoke.
- `make arch-check` weiter `19/19 Contracts KEPT`.

### C3 — `docs(plan|adr)`: Welle-5b Status/DoD-Sync + ADR-Schaerfung

- ADR 0035 `Proposed → Provisional` mit C2-Merge-Beleg.
- `M4-welle-5b.md`-Status `In Progress → Done` mit
  C0/C1/C2-Hashes + DoD-Verifikation-Block + DoD-
  Checkliste (Pattern analog Welle-5a §9).
- `M4-protocol-adapters.md §3 Welle 5b`: Done-Status mit
  Commit-Belegen; DoD-Checkboxen abgehakt.
- README.md / README.de.md / roadmap.md /
  adr/README.md / in-progress/README.md: M4-Status-Sync
  analog M4-Welle-5a-C3 `6903a08`.

---

## 5. Critical Files

| Pfad                                                                              | Commit | Aktion                                                |
| --------------------------------------------------------------------------------- | ------ | ----------------------------------------------------- |
| `docs/plan/planning/in-progress/M4-welle-5b.md`                                   | C0     | NEU (dieses Dokument)                                 |
| `docs/plan/adr/0035-iec61850-adapter-profile.md`                                  | C1     | NEU (`Proposed`)                                      |
| `docs/plan/adr/README.md`                                                         | C1     | EDIT (ADR-0035-Zeile)                                 |
| `src/grid_gym/adapters/driven/protocol_iec61850/__init__.py`                      | C2     | NEU (GPLv3, SPDX-Header)                              |
| `src/grid_gym/adapters/driven/protocol_iec61850/_config.py`                       | C2     | NEU (GPLv3, SPDX-Header)                              |
| `src/grid_gym/adapters/driven/protocol_iec61850/_codec.py`                        | C2     | NEU (GPLv3, SPDX-Header)                              |
| `src/grid_gym/adapters/driven/protocol_iec61850/_port.py`                         | C2     | NEU (GPLv3, SPDX-Header)                              |
| `src/grid_gym/adapters/driven/protocol_iec61850/_errors.py`                       | C2     | NEU (GPLv3, SPDX-Header)                              |
| `tests/unit/adapters/driven/protocol_iec61850/__init__.py`                        | C2     | NEU (GPLv3, SPDX-Header)                              |
| `tests/unit/adapters/driven/protocol_iec61850/test_iec61850_config.py`            | C2     | NEU (GPLv3, SPDX-Header)                              |
| `tests/unit/adapters/driven/protocol_iec61850/test_iec61850_codec.py`             | C2     | NEU (GPLv3, SPDX-Header)                              |
| `tests/unit/adapters/driven/protocol_iec61850/test_iec61850_protocol_port.py`     | C2     | NEU (GPLv3, SPDX-Header)                              |
| `tests/integration/test_iec61850_in_process_smoke.py`                             | C2     | NEU (GPLv3, SPDX-Header)                              |
| `tests/integration/fixtures/iec61850/simpleIO.cfg`                                | C2     | NEU (libiec61850-natives CFG-Modell-Format; 4 Datatypes) |
| `LICENSES/GPL-3.0.txt`                                                            | C2     | NEU (Standard-GPL-3.0-Volltext)                       |
| `LICENSE`                                                                         | C2     | EDIT (Hinweis-Block am Ende: GPL-Boundary)            |
| `README.md` + `README.de.md`                                                      | C2     | EDIT (Lizenz-Hinweis-Sektion)                         |
| `tests/integration/compose.yml`                                                   | C2     | EDIT (Header-Kommentar)                               |
| `pyproject.toml`                                                                  | C2     | EDIT (NEU `[project.optional-dependencies.iec61850] = ["pyiec61850-ng>=1.6,<2.0"]` + mypy-Override) |
| `uv.lock`                                                                         | C2     | EDIT (via `make lock-refresh --all-extras` o.ä.)      |
| `Dockerfile`                                                                      | C2     | EDIT (`CRITICAL_COV_TARGETS` + `protocol_iec61850` + `uv sync --extra iec61850` in Test-Stage) |
| `docs/plan/adr/0035-iec61850-adapter-profile.md`                                  | C3     | EDIT (`Proposed → Provisional`)                       |
| `docs/plan/adr/README.md`                                                         | C3     | EDIT (Status-Spalte `Provisional`)                    |
| `docs/plan/planning/in-progress/M4-welle-5b.md`                                   | C3     | EDIT (Status → Done; DoD)                             |
| `docs/plan/planning/done/M4-protocol-adapters.md`                          | C3     | EDIT (§3 Welle 5b DoD-Checkboxen abgehakt)            |
| `README.md` + `README.de.md` + `docs/plan/planning/in-progress/roadmap.md` + `docs/plan/planning/in-progress/README.md` | C3 | EDIT (M4-Status-Sync — Welle 5b `Done`, ADR 0035 `Provisional`) |

---

## 6. Verifikationspfad

1. **C0 (Slice-Doc)**: `make docs-check` cache-frei gruen.
2. **C1 (ADR Proposed)**: `make docs-check` gruen.
3. **C2 (feat)**:
   - `make test-unit` gruen (1462 → ~1500+ Tests; ~30-40
     neue Tests analog Welle 5a-Stand).
   - `make test-integration` gruen mit IEC-61850-In-Process-
     Smoke (35 → 39+ Integration-Tests).
   - `make arch-check` 19/19 KEPT.
   - `make gates` cache-frei gruen ohne Override.
   - `mypy --strict-bytes` gruen (mit Override fuer
     `pyiec61850.*`).
   - SPDX-Header in allen 12 neuen Files verifiziert
     (visuelle Pruefung + ggf. `tools/check_refs.py`-
     Erweiterung in Welle-6).
4. **C3 (Doc-Sync)**: `make docs-check` gruen mit
   Welle-5b-Endstand in 5+ Docs.

---

## 7. Risiken

- **CFG-Format-Validierung in C2** (HOCH, neu nach C1-
  Review-Folge 2026-06-01). `IedServer(model_path=fixture)`
  erwartet ein libiec61850-natives CFG-Format
  (`IedModel_createFromConfigFile`-kompatibel). Format-
  Detail (Pflichtfelder, Trennzeichen, supported DataTypes)
  ist nur in `mz-automation/libiec61850/examples/server_example_basic_io`
  exemplarisch dokumentiert. *Mitigation*: C2 macht erst
  einen Format-Probe-Run mit dem Library-Example-CFG als
  Basis und schaerft auf das Welle-5b-Spike-Fixture
  (4 Datatypes). **2c-Mock-only-Fallback explizit
  dokumentiert** (Decision I-e §2.5) falls C2 zeigt, dass
  CFG-Format nicht schnell stabil aufgeht.
- **Wire-Compat zwischen MMSClient-1.6.1.2 und IedServer-
  0.1.0 nicht vorab garantiert** (HOCH). `pyiec61850-ng`-
  Server-Submodul ist `__version__ = "0.1.0"` (Pre-Alpha
  in dem Submodul), waehrend der Client `MMSClient` aus
  Top-Level-`1.6.1.2`-Stand kommt. Beide sind in einem
  Wheel ausgeliefert und gegen die gleiche libiec61850-
  1.6-`.so` gelinkt — Wire-Compat ist deshalb
  **wahrscheinlich** OK (gleicher Wire-Layer), aber
  **nicht** verifiziert. *Mitigation*: C1 macht einen
  schnellen Wire-Compat-Probe-Run (in-process IedServer
  + MMSClient + Bool-Read-Roundtrip) **vor** der Adapter-
  Implementierung. Bei negativem Ergebnis Fallback auf
  Mock-only-Smoke (Decision I-e wird zu „mock-only"
  geschoben) — Welle-5b-DoD bleibt erfuellbar.
- **GPL-Boundary-Policy ist Repo-Novum** (HOCH).
  Erstmaliger Praezedenzfall fuer GPL-isolierte Sub-Module
  im sonst MIT-lizenzierten grid-gym. Risiko: spaetere
  Contributors koennten versehentlich GPL-isolierten Code
  in MIT-Module kopieren, oder umgekehrt. *Mitigation*:
  SPDX-Header pro Datei + Top-Level-`LICENSE`-Hinweis +
  README-Lizenz-Sektion + `tools/check_refs.py`-Erweiterung
  in Welle 6 (SPDX-Header-Konsistenz pruefen).
  CONTRIBUTING.md-Sync ist Welle-6-Material.
- **`pyiec61850-ng` ist Beta** (`Development Status :: 4`)
  (MEDIUM). API kann zwischen Minor-Versionen breaking
  changes haben. *Mitigation*: Pin `>=1.6,<2.0` plus
  `uv.lock`-Pinning auf 1.6.1.2 macht den Stand stabil;
  Welle-6 kann auf eine stabilere Release upgraden falls
  vorhanden.
- **SWIG-Bindings als erste C-native Library im Repo**
  (MEDIUM). Vorher waren alle Adapter-Libraries Pure-
  Python. Memory-Management-Risiken (Reference-Cycles,
  use-after-free) sind theoretisch moeglich. *Mitigation*:
  Context-Manager-Pattern (`MMSClient.__enter__/__exit__`
  + `IedServer.__enter__/__exit__`) + Pre-built manylinux1-
  Wheel kapselt die Risiken weitgehend ein.
- **Kein aarch64-Wheel auf piwheels** (LOW). Raspberry-Pi-
  64-bit-Builds koennen `pyiec61850-ng` nicht ueber pip
  installieren. *Mitigation*: grid-gym laeuft primaer
  x86_64/manylinux1 (Dockerfile-Builds + Compose-Smokes).
  Welle-6 kann optional Source-Build-Pfad fuer aarch64
  einfuehren, falls Bedarf entsteht.
- **`pyiec61850-ng`-API ist nur in README + Source-Code
  dokumentiert** (LOW). Keine offizielle Sphinx-/RTD-Doc.
  *Mitigation*: C1 macht einen API-Probe-Run gegen
  `pyiec61850.server.IedServer` + `pyiec61850.mms.MMSClient`;
  Adapter-Code referenziert nur die in C1 verifizierten
  API-Pfade.
- **Welle-5b ist letzter konkreter M4-Adapter** (LOW).
  M4-Welle-7-Closure danach. Falls Welle 5b unerwartet
  scheitert (z. B. Wire-Compat-Bruch + Mock-only-Fallback),
  schaerft Welle 7 ADR 0030 §2.4 entsprechend auf
  „aufgeloest fuer DNP3, dokumentierter Teilverzicht fuer
  IEC-61850". *Mitigation*: M4-Welle-7-Closure ist auf
  beide Pfade vorbereitet.

---

## 8. Wandert nach

- `done/M4-welle-5b.md` mit M4-Welle-6-Pre-C0-Move
  (Pattern aus M3 und M4-Welle-1..5a: `welle-5b.md`
  wandert mit M4-Welle-6-Pre-C0 nach `done/`).
- ADR 0035 bleibt in `docs/plan/adr/` (kein Move; nur
  Status-Updates).
- `M4-protocol-adapters.md` bleibt in `in-progress/` bis
  M4-Welle-7-Closure.
- M4-Welle-6-Naechster-Schritt: Cross-Adapter-Hardening
  (OTel-Span-Wrap der 5 `protocol_*`-Adapter, Adapter-
  Profil-Index unter `spec/protocol_profiles/`,
  `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-Property-Test
  als Welle-1-§7-Folge-Pflicht-Closure).

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

Pattern analog M4-welle-5a.md §9. Belege wird mit C3
**DoD-Verifikation**-Block im Status-Header oben + §4
Liefer-Reihenfolge fuer die per-Commit-Aktion ergaenzt.

**In-Scope-Items (mit C3 abzuhaken):**

- [x] **ADR 0035 angelegt** — `Proposed` (C1) →
  `Provisional` (C3), mit Decisions I-a/I-b/I-c/I-d/I-e/I-f
  alle **final**.
- [x] **IEC-61850-Port produktiv** —
  `Iec61850DeviceProtocolPort` als `DeviceProtocolPort`-
  Implementer unter
  `src/grid_gym/adapters/driven/protocol_iec61850/` (5
  Dateien: `__init__.py` + `_config.py` + `_codec.py` +
  `_port.py` + `_errors.py`). Modul-Docstring in
  `__init__.py` traegt Lastenheft-Z.-1155–1157-Pflicht
  (Simulations-/Testadapter, **keine** produktive
  Anlagensteuerung) + GPLv3-Lizenz-Hinweis.
- [x] **Wire-Compat verifiziert** — C1-Probe-Run +
  C2-Integration-Smoke demonstrieren
  `MMSClient.read_value(...)` ↔ `IedServer(model_path=fixture)`-
  Roundtrip durch alle Welle-5b-Datatypes
  (bool/int32/float/string); ODER 2c-Mock-only-Fallback,
  falls CFG-Format-/Wire-Compat-Verifikation in C2 nicht
  stabil aufgeht.
- [x] **Unit-Tests fuer 3 Test-Aspekte** — Config-
  Validation + Codec-Roundtrip (inkl. hypothesis-
  Property-Tests pro Datatype) + Protocol-Port-Lifecycle.
- [x] **Integration-Smoke produktiv** —
  `tests/integration/test_iec61850_in_process_smoke.py`
  spawnt `IedServer(model_path=fixture)` in eigenem
  Daemon-Thread mit Context-Manager-Cleanup;
  parametrierte Read-Roundtrips pro Datatype gegen das
  CFG-Fixture. ALTERNATIV (2c-Fallback): Mock-only-Smoke
  in `tests/unit/adapters/driven/protocol_iec61850/`
  falls CFG-Format oder Wire-Compat in C2 nicht stabil.
- [x] **NEU `tests/integration/fixtures/iec61850/simpleIO.cfg`**
  als minimales Welle-5b-Test-Modell (4 Datatypes:
  `AnIn1.mag.f`/`IntIn1.stVal`/`Ind1.stVal`/`NamPlt.d`
  in `simpleIOGenericIO/GGIO1`). libiec61850-natives
  CFG-Format (kein SCL-XML). Falls 2c-Fallback aktiv:
  Fixture wird **nicht** geliefert; DoD-Item wird
  „n/a (Mock-only-Fallback)" markiert.
- [x] **NEU Loader-Hook ImportError-tolerant** —
  `protocol_iec61850/__init__.py` faengt `ImportError`
  beim `import pyiec61850`-Versuch und wirft typed
  `Iec61850PortLibraryNotInstalledError("Install with:
  pip install grid-gym[iec61850]")`. Welle-1-
  `build_protocol_ports`-Hook propagiert das als
  ScenarioConfigError o.ä.
- [x] **`tests/integration/compose.yml` Header-Kommentar
  syncht** — Welle-5b-C2-Edit dokumentiert die Decision-
  I-e-Wahl (in-process `IedServer`, eine-Library wie
  Welle 3, anders als Welle 5a).
- [x] **`pyproject.toml` erweitert** —
  `pyiec61850-ng>=1.6,<2.0` in
  `[project.optional-dependencies.iec61850]` (Decision
  I-f opt-in; **nicht** in `[project] dependencies`);
  mypy-Override `module="pyiec61850.*"` mit
  `ignore_missing_imports = true`. Top-Level-MIT-
  Classifier bleibt unveraendert.
- [x] **EDIT `uv.lock`** — via `make lock-refresh`
  aktualisiert.
- [x] **`Dockerfile` erweitert** — `CRITICAL_COV_TARGETS`-
  Default um `src/grid_gym/adapters/driven/protocol_iec61850`
  ergaenzt.
- [x] **`AC-ADAPTER-LIGHTWEIGHT` greift fuer
  `protocol_iec61850`** — `tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`-Filter erfasst den
  neuen Pfad **ohne Code-Aenderung**; `make arch-check`
  weiter `19/19 Contracts KEPT`.
- [x] **NEU `LICENSES/GPL-3.0.txt`** — Standard-GPL-3.0-
  Volltext.
- [x] **EDIT Top-Level-`LICENSE`** — Hinweis-Block am Ende
  fuer GPL-Boundary auf `protocol_iec61850/*`.
- [x] **EDIT `README.md` + `README.de.md`** — Lizenz-
  Hinweis-Sektion.
- [x] **SPDX-Header in allen 12 neuen Files** —
  `# SPDX-License-Identifier: GPL-3.0-only` (Python-Style)
  verbatim.

**Anti-Scope-Items (mit C3 zu verifizieren):**

- [x] **Kein IEC-61850-Write-Pfad** in C2 — verifiziert:
  `Iec61850DeviceProtocolPort.write()` wirft konsequent
  `Iec61850PortWriteNotImplementedError`.
- [x] **Kein IEC-61850-Report-Control-Block-Subscription**
  in C2 — verifiziert: Adapter ruft nur
  `MMSClient.read_value(...)`; kein RCB-Pfad im `_port.py`;
  kein direkter Low-Level-`pyiec61850.pyiec61850`-Import.
- [x] **Kein GOOSE-Publishing/Subscription** in C2 —
  verifiziert: kein Aufruf von
  `IedServer.enable_goose_publishing()`.
- [x] **Kein IEC-61850-9-2 Sampled-Values** in C2 —
  verifiziert: keine Imports aus `pyiec61850.sv`-Submodul.
- [x] **Kein OTel-Span-Wrap** der IEC-61850-Adapter-Calls
  — verifiziert: kein Import von
  `adapters/driven/telemetry_otlp/` in `protocol_iec61850/`.
- [x] **Keine IEC-61850-Security** — verifiziert: kein
  TLS-Init im Welle-5b-Code; Smoke-Endpoint ist Plain-MMS.
- [x] **Kein RandomPort-Determinismus** — verifiziert:
  `Iec61850LnConfig` hat keinen Auto-Generierungs-Pfad
  fuer Object-Reference-Strings.
- [x] **Keine Scenario-Schema-Erweiterung** jenseits des
  Decision-I-a-Pattern — verifiziert: kein Touch an
  `scenario/validator.py`.
- [x] **Keine Welle-2/3/4/5a-Adapter-Aenderungen** —
  verifiziert: kein Edit an
  `src/grid_gym/adapters/driven/protocol_{mqtt,modbus,opcua,dnp3}/`.
- [x] **Keine Bewegung der Open-Trigger** — verifiziert:
  `docs/plan/planning/open/` unveraendert.
- [x] **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md` —
  verifiziert: `roadmap.md` §3 M4 Checkboxen weiterhin
  alle ungehakt (5 von 7 DoD-Items geliefert nach
  Welle 5b: MQTT + Modbus + OPC-UA + DNP3 + IEC-61850;
  Sweep in Welle 7).
- [x] **Kein `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-
  Property-Test** in Welle 5b — verifiziert: nur Smoke-
  Regression-Schutz via `make arch-check`. Welle-1-§7-
  Folge-Pflicht bleibt auf Welle 6 verschoben.
- [x] **Kein gemeinsamer Loop-Thread-Reuse** —
  verifiziert: `Iec61850DeviceProtocolPort` ist direkt-
  sync ohne `OpcuaLoopThread`-Import.
- [x] **Kein aarch64-Wheel-Support** — verifiziert:
  keine Build-Pfad-Erweiterung im Dockerfile fuer
  aarch64; piwheels-Lage als Risiko dokumentiert,
  Welle-6-Material.
- [x] **Kein Anschluss von `pyiec61850.{tase2,sv,goose}`-
  Submodulen** — verifiziert: nur Imports aus
  `pyiec61850.mms` und `pyiec61850.server`.
