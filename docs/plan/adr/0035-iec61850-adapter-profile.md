# ADR 0035 — IEC-61850-Adapter-Profile (M4 Welle 5b)

**Status:** Accepted — gezogen 2026-06-01 mit M4-Welle-7-C1
(dieser Commit; M4-Closure-Welle). Provisional-Schritt
2026-06-01 mit M4-Welle-5b-C3 (`docs(plan|adr)` Doc-Sync).
Initial-Entwurf (`Proposed`) 2026-06-01 mit M4-Welle-5b-C1
`88c1a33`; C1-Review-Folge `da8aed9` (API-Korrektur +
Lizenz-Refit + M4-protocol-adapters.md-Sync nach 4 Findings);
C2-Merge `944bca5` (feat: `protocol_iec61850/`-5-Modul-Paket
+ 75 neue Unit-Tests + Integration-Smoke unter 2c-Mock-only-
Fallback + GPL-Lizenz-Boundary-Files + pyproject/Dockerfile/
compose-Edits + uv.lock-Refresh; `make test-unit` 1537 gruen,
`make test-integration` 35 passed + 4 skipped, `make arch-check`
19/19 KEPT, `make gates` 9 A-1-Gates gruen ohne
`CRITICAL_COV_TARGETS`-Override) belegt die Decisions
I-a/I-b/I-c/I-d/I-e/I-f produktiv. Welle 6a + 6b haben die
Decision I-f (GPL-Boundary) per Static-Enforcement
gehaertet: SPDX-Header-Lint `make spdx-check` (10. A-1-
Gate) + `AC-IEC61850-GPL-BOUNDARY` arch_check-Contract
(14. Contract; 19 → 20 KEPT) + NEU `CONTRIBUTING.md` mit
Dual-License-Policy + Cross-Adapter-OTel-Span-Wrap aus
Welle 6a wrappt auch den IEC-61850-Adapter ohne
Adapter-Code-Diff.

**2c-Mock-only-Fallback aktiviert** (Decision I-e §2.5):
Probe-Run auf Python 3.12 lief sauber (Float/Int32/String-
Roundtrip MMSClient↔IedServer per CFG-Fixture verifiziert).
Auf dem grid-gym-Docker-Stack (Python 3.14) crasht
`_pyiec61850.so` aber im ersten `IedServer.start()`-Call mit
Segfault (exit 139, Stack-Trace in SWIG-`.so`). Vermutete
Ursache: pyiec61850-ng 1.6.1.2 manylinux1_x86_64-Wheel
deklariert zwar Python-3.14-Support in den Classifiers, aber
die SWIG-Bindings sind unter 3.14-ABI-Conditions nicht
erprobt. Integration-Smoke ist mit `pytest.mark.skip` und
expliziter Begruendung deaktiviert; Welle-5b-DoD ist via
18 Mock-Unit-Tests erfuellt (Lifecycle + Read-Pfad +
Error-Translation + Anti-Scope-Verifikation). **Welle-6-
Schaerfungspfade**: (a) Python-3.12-Runtime fixieren ODER
(b) pyiec61850-ng-Library-Upgrade abwarten ODER (c) Wheel
selbst gegen Python 3.14 rebuild.

Status-Pfad: `Proposed → Provisional` (2026-06-01
M4-Welle-5b-C3) → **Accepted** (2026-06-01 M4-Welle-7-C1,
dieser Commit, analog ADR 0022..0027 + 0030 + 0031 +
0032 + 0033 + 0034). Pattern analog ADR 0034 (M4-Welle-5a)
und ADR 0033 (M4-Welle-4) und ADR 0032 (M4-Welle-3) und
ADR 0031 (M4-Welle-2).

**Slice 033 (M4-Welle-5b-C2-Review-Folge 2026-06-01,
[`../planning/done/033-iec61850-adapter-review-folge.md`](../planning/done-archive/033-iec61850-adapter-review-folge.md)):**
15 Findings adressiert (10 HIGH + 5 MEDIUM) ohne ADR-Status-
Aenderung. Wichtigste Schaerfungen:

- **Optional-Extra-Off-Pfad-Hardening:** `_port.py` benutzt
  jetzt eine **private Sentinel-Exception-Klasse**
  (`_IecExtraOffSentinelError`) statt `Exception` als Alias
  fuer alle `_PyIec*Error`-Namen — die except-Reihenfolge
  in `start()`/`read()`/`stop()` bleibt auch ohne installiertes
  Extra korrekt narrow.
- **Decision I-b**: `start()` Factory-Call ist jetzt im
  try-Block; except-Tupel um `_PyIecMMSError` (Catch-All-
  Basis) erweitert. `stop()` State-Mutation **nach**
  `disconnect()` (vorher: vorher).
- **Decision I-c (Codec-Schaerfung)**: NaN/Infinity wird
  rejected (`Iec61850CodecOverflowError`); `int` ist kein
  valider `datatype='float'`-Wert mehr (silent
  Praezisionsverlust fuer Ints > 2**53 verhindert);
  Container-Repr-Check gated auf `datatype != "string"`
  (legitime `<MmsValue ...>`-Strings als Daten erlaubt).
- **Decision I-d (Read-Pfad-Schaerfung)**: NEU
  `Iec61850PortReadConnectionLostError` (Subclass von
  `Iec61850PortReadFailedError`) fuer mid-flight
  `NotConnectedError`. Caller kann jetzt 'forgot-start'
  (`ReadNotStartedError`) von 'session-dropped'
  (`ReadConnectionLostError`) unterscheiden.
- **Anti-Scope-Hardening (Decision I-c+I-d Folge)**:
  `_config._validate_single_ln_config` lehnt
  `access="write"` **bei Konstruktion** ab (vorher: erst
  zur Laufzeit in `port.write()`). Welle-6 reaktiviert den
  Write-Pfad.
- **TelemetryPoint.value-Vertrag (cross-Adapter-Pattern-
  Konsistenz)**: Bool/Int werden zu `Decimal(int(...))`
  gewandelt; String-Wert mappt auf `Decimal(0)` +
  `Quality.INVALID` + `source="protocol_iec61850.{target}#string={value}"`
  (Welle-4-Slice-032-Finding-3.1-Pattern).
- **Decision I-e (Test-Fixture-Hardening)**: Integration-
  Smoke-Fixture wrappt `IedServer`-Construction + `start()`
  jetzt im try-Block; `server: IedServer | None = None`-
  Sentinel mit `finally`-Gating fuer Welle-6-Reaktivierung.
- **Decision I-f (Lizenz-Boundary-Hardening)**:
  Dockerfile-`build-app`-Stage propagiert `--extra iec61850`
  (vorher: nur `deps`+`source` → Runtime-venv ohne
  Library, Production-Crash bei `type: iec61850`).
  `pyproject.toml`-Classifier ergaenzt um
  `License :: OSI Approved :: GNU General Public License v3 (GPLv3)`
  (SBOM-Tools sahen vorher nur MIT). `simpleIO.cfg`-Fixture
  hat jetzt SPDX-Header + Derivative-Work-Attribution zu
  `libiec61850/examples/server_example_config_file/model.cfg`.
- **Edge-Case**: `_default_client_factory` floort sub-
  Millisekunden-Timeouts auf 1ms (`max(1, int(...))`) —
  vorher konnte `response_timeout_s=0.0005` zu `timeout=0`
  werden, was libiec61850 uneinheitlich interpretierte.

Slice 033 ist Schaerfung-ohne-Supersede (Pattern ADR 0011);
ADR 0035 Status bleibt `Provisional`.

**Datum:** 2026-06-01

**Bezug:**
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md)
(Schaerfungs-ohne-Supersede-Pattern — ADR 0035 schaerft
ADR 0030 §2.1 und §2.4 konkret fuer IEC-61850, ohne den
Sync-`DeviceProtocolPort`-Vertrag oder den Welle-1-Verzicht-
Default zu ersetzen; M4-Welle-7-Closure schaerft ADR 0030
§2.4 dann auf „durch Welle-5a-Spike-Lieferung (DNP3) **und**
Welle-5b-Spike-Lieferung (IEC-61850) aufgeloest"),
[`ADR 0030`](0030-device-protocol-port-surface.md) §2.1
(Sync-`Protocol`-Vertrag; `pyiec61850.mms.MMSClient` ist
als sync-Context-Manager implementiert — alle relevanten
Public-Methoden (`__enter__`/`__exit__`/`read`/`write`) sind
sync per Library-Recherche-Befund 2026-06-01 — und passt
damit **direkt** in die Sync-`DeviceProtocolPort`-Surface,
analog Welle-3-Modbus und Welle-5a-DNP3 **ohne** Adapter-
internen Thread+Loop-Marshal) + §2.2 (Caller-Scope-Lifecycle)
+ §2.3 (stateless aus Replay-Sicht — IEC-61850-MMS-Session-
State + Report-Control-Block-State sind volatile) + §2.4
(Welle-1-IEC-61850-Verzicht-Default; Welle 5b loest ihn per
Spike-Lieferung auf — Pattern ADR 0011),
[`ADR 0031`](0031-mqtt-adapter-profile.md) §2.1
(Decision 4a inline-Profile-Pattern — ADR 0035 uebernimmt
das Pattern direkt fuer LN/CDC-Schema),
[`ADR 0032`](0032-modbus-adapter-profile.md) §2.1
(Decision M-a inline-Register-Schema — direkte Pattern-
Praezedenz fuer Decision I-a inline-LN/CDC-Schema) +
§2.3 (Decision M-c direkt-sync — direkte Pattern-
Praezedenz fuer Decision I-b: pyiec61850-ng ist sync wie
pymodbus + nfm-dnp3) + §2.6 (Decision M-f in-process-
Server — direkte Pattern-Praezedenz fuer Decision I-e:
**eine** Library liefert Client + Server, anders als
Welle 5a),
[`ADR 0033`](0033-opcua-adapter-profile.md) §2.2
(Decision O-b `OpcuaLoopThread` — Pattern explizit
**nicht** uebernommen in Welle 5b, weil pyiec61850-ng
sync ist),
[`ADR 0034`](0034-dnp3-adapter-profile.md) §2.1
(Decision D-a inline-Point-Schema) + §2.2 (Decision D-b
direkt-sync) + §2.5 (Decision D-e in-process-Outstation
als Test-Sibling). Welle 5b weicht von Welle 5a bewusst
in zwei Punkten ab: **eine** Library statt zwei
(Welle-3-Modbus-Pattern), und **NEU Decision I-f Lizenz-
Boundary** (GPL-Isolation auf `protocol_iec61850/*`).
M4-Slice-Plan
[`done/M4-protocol-adapters.md`](../planning/done-archive/M4-protocol-adapters.md)
§3 Welle 5b; M4-Welle-0-Decision-Liste
[`done/M4-welle-0.md`](../planning/done-archive/M4-welle-0.md) §3
Decision 1 (DNP3/IEC-Disposition — Welle 1 hat den
Verzicht-Default provisorisch gewaehlt; Welle 5a hat den
DNP3-Teil aufgeloest, Welle 5b loest den IEC-61850-Teil
auf).
Lastenheft §16 (`GG-IEC-001` SOLLTE-Cluster: Logical
Nodes, Common Data Classes, Datenattribute, MMS-Service-
Mapping + deterministischer Adapter-Smoke).
Architektur §7 (`GG-AR-PORT-DRN-007` Driven-Ports-Tabelle
— ADR 0030 hat den Slot belegt; Welle 5b liefert
**fuenften** Implementer und schliesst die Adapter-Mantel-
Welle in M4) + §8.2 (Adapter-Interfaces-Driven-
Beschreibung — LN/CDC-Schema konkretisiert die generische
Beschreibung fuer IEC-61850).

---

## 1. Kontext

`GG-IEC-001` (Lastenheft §16, Z. 1155-1157) verlangt einen
IEC-61850-Adapter als **Simulations-/Testadapter** mit
deterministischem Adapter-Smoke-Test. M4-Welle-2 hat
MQTT (ADR 0031 `Provisional`), Welle 3 Modbus (ADR 0032
`Provisional`), Welle 4 OPC-UA (ADR 0033 `Provisional`),
Welle 5a DNP3 (ADR 0034 `Provisional`) produktiv geliefert;
Welle 5b liefert den **fuenften und letzten** konkreten
M4-Adapter: `Iec61850DeviceProtocolPort` unter
`src/grid_gym/adapters/driven/protocol_iec61850/` ueber
**eine** SWIG-Library:

- **Master/Client + In-process-Server (eine Library):**
  `pyiec61850-ng` 1.6.1.2 (PyPI, **GPLv3**, Beta
  `Development Status :: 4`, Python >=3.9, manylinux1_x86_64
  + Windows-Wheels fuer CPython 3.9..3.14). SWIG-Bindings
  zu **libiec61850 1.6** (MZ Automation, GPLv3) inkl.
  Mbed TLS (Apache 2.0). Library-Recherche-Befund 2026-06-01
  hat verifiziert:
  - **Client:** `pyiec61850.mms.MMSClient`-Context-Manager
    mit sync `read_value(reference, fc)`/
    `write_value(reference, value)`-API (Constructor:
    `MMSClient(host=None, port=None, timeout=..., max_pdu_size=..., tls=...)`;
    `__enter__` auto-connect-t falls `host` im Constructor;
    `disconnect()` als idempotenter Stop). FC akzeptiert
    String (`"ST"`/`"MX"`/`"SP"`/`"CF"`/...) oder
    int-Enum (`iec61850.IEC61850_FC_*`); Library-Default
    ist `"ST"`, Welle-5b-Adapter-Default ist `"MX"` (siehe
    Decision I-c). Top-Level-Version 1.6.1.2-stabil.
    Exception-Famille: `MMSError` (Top-Level),
    `LibraryNotFoundError`, `ConnectionError`,
    `ConnectionFailedError`, `ConnectionTimeoutError`,
    `NotConnectedError`, `ReadError`, `WriteError`,
    `OperationError`, `FileTransferError`.
  - **In-process-Server:** `pyiec61850.server.IedServer`
    mit Context-Manager + Lifecycle (`start(port=102)` /
    `stop()`) + Update-Methoden (`update_boolean` /
    `update_int32` / `update_float` / `update_visible_string`
    / `update_quality` / `update_timestamp`) + Control-
    Handler-Hook + GOOSE-Publishing-Hook (Welle-5b-Anti-
    Scope) + Model-Lock-Hook. **Modell-Pflicht:**
    `IedServer.__init__(model_path=None, config=None)`
    akzeptiert einen optionalen `model_path`-Pfad; falls
    `None`, wirft `start()` **explizit**
    `ModelError("No data model loaded")`. Welle-5b-Smoke
    laedt damit ein minimales CFG-Fixture (siehe
    Decision I-e). Server-Submodul ist
    `__version__ = "0.1.0"` (Pre-Alpha in dem Submodul;
    Wire-Compat mit Client wahrscheinlich OK, weil beide
    gegen libiec61850 1.6 im selben Wheel gelinkt sind,
    aber **nicht** vorab verifiziert — C2-Smoke ist die
    Wire-Compat-Pflicht).
  - **Submodule (Welle-5b-Anti-Scope):**
    `pyiec61850.goose` (GOOSE-Pub/Sub),
    `pyiec61850.sv` (Sampled Values),
    `pyiec61850.tase2` (TASE.2/ICCP) bleiben Welle-6+-
    Material.
  - **Low-Level SWIG-Wrapper:** `pyiec61850.pyiec61850`
    (direkter Bindings-Layer). Welle-5b-Anti-Scope —
    der Adapter referenziert nur die High-Level-Wrapper.

ADR 0030 hat den **Sync-Vertrag** und **Caller-Scope-
Lifecycle** finalisiert; ADR 0030 §2.4 hat den
**IEC-61850-Verzicht-Default provisorisch** gewaehlt
(Welle 1 2026-05-26). ADR 0035 schaerft die fuer den
IEC-61850-Adapter notwendigen Sub-Entscheidungen
**konkret** und loest damit den ADR-0030-§2.4-Verzicht-
Default fuer IEC-61850 per Spike-Lieferung auf (Pattern
ADR 0011; M4-Welle-7-Closure schaerft ADR 0030 §2.4
entsprechend — DNP3 und IEC-61850 beide aufgeloest).

ADR 0031 hat das **inline-im-`protocol_ports`-Block**-
Profile-Pattern etabliert; ADR 0032 hat es Modbus-
spezifisch geschaerft (Register-Schema); ADR 0033 fuer
OPC-UA (Node-ID-Schema); ADR 0034 fuer DNP3 (Point-
Schema); ADR 0035 schaerft Decision-I-a..I-f:

- **Decision I-a (LN/CDC-Schema)** — wo und wie werden
  Device-ID → IEC-61850-Object-Reference-Mappings
  deklariert?
- **Decision I-b (Async-Bridge)** — wie wird der
  pyiec61850-ng-Sync-Charakter gegen die sync-
  `DeviceProtocolPort`-Surface vermittelt?
- **Decision I-c (Datatype-Set + FC-Mapping)** — welche
  MMS-Datentypen und Functional-Constraints sind in
  Welle 5b unterstuetzt?
- **Decision I-d (Read-Pfad)** — wie wird die
  pyiec61850-ng-API auf den `DeviceProtocolPort.read()`-
  Call abgebildet?
- **Decision I-e (Test-Sibling)** — wie wird der
  IEC-61850-Server-Sibling im Integration-Test
  bereitgestellt?
- **NEU Decision I-f (Lizenz-Boundary)** — wie wird die
  GPL-Isolation zwischen `protocol_iec61850/*` (GPLv3
  via pyiec61850-ng/libiec61850) und Rest-grid-gym (MIT)
  organisiert?

**Spannungsfeld:**

- **Lizenz-Asymmetrie:** `pyiec61850-ng` ist die einzige
  produktiv-stabile Python-IEC-61850-Library mit MMS-
  Support, sie ist GPLv3 (libiec61850-Bindings). grid-gym
  ist MIT. Reine MIT-Alternativen (`py61850` — Pre-Alpha,
  nur GOOSE-Publisher) sind nicht produktiv-reif.
  Kommerzielle Lizenz bei MZ Automation ist kein Open-
  Source-Weg. Welle 5b muss eine Lizenz-Boundary-Decision
  treffen, die die GPL-Pflicht auf `protocol_iec61850/*`
  isoliert und den Rest des Projekts MIT haelt — das ist
  ein **Repo-Novum** (Praezedenzfall fuer alle zukuenftigen
  GPL-Library-Bindings).
- **Wire-Compat MMSClient ↔ IedServer:** Server-Submodul
  ist `__version__ = "0.1.0"` (Pre-Alpha in dem Submodul),
  waehrend Client `MMSClient` aus Top-Level-`1.6.1.2`-
  Stand kommt. Beide sind im selben Wheel gegen
  libiec61850 1.6-`.so` gelinkt — Wire-Compat ist deshalb
  **wahrscheinlich** OK (gleicher Wire-Layer), aber
  **nicht** vorab verifiziert. C2-Smoke ist die Wire-
  Compat-Verifikations-Pflicht. Bei negativem Ergebnis
  Mock-only-Fallback (Decision I-e wird zu „mock-only"
  geschoben) — Welle-5b-DoD bleibt erfuellbar.
- **SWIG-/C-native Library erstmalig im Repo:** vorher
  nur Pure-Python (paho-mqtt, pymodbus, asyncua, nfm-dnp3,
  dnp3-outstation). `pyiec61850-ng` liefert pre-built
  manylinux1_x86_64-Wheels + Windows-Wheels (CPython
  3.9..3.14); kein aarch64-Wheel (Raspberry-Pi-64
  Welle-6-Material). Memory-Management-Risiken (SWIG +
  C-Library) sind durch Context-Manager-Pattern weitgehend
  gekapselt.

---

## 2. Entscheidung

ADR 0035 legt sechs Profile-Decisions fest.

### 2.1 Decision I-a — LN/CDC-Schema inline im `protocol_ports`-Block (final)

LN-/CDC-Profile werden **inline** im `protocol_ports`-
Scenario-YAML-Block deklariert. Pattern uebernommen
direkt von ADR 0031 §2.1 (MQTT Topic-Schema inline),
ADR 0032 §2.1 (Modbus Register-Schema inline), ADR 0033
§2.1 (OPC-UA Node-ID-Schema inline), ADR 0034 §2.1
(DNP3 Point-Schema inline).

**Skizze (finale Signatur in Welle-5b-C2-feat):**

```yaml
protocol_ports:
  - type: iec61850
    host: "192.168.1.50"
    port: 102
    ied_name: "SimpleIO"
    response_timeout_s: 5.0
    points:
      battery1_voltage:
        object_reference: "SimpleIOGenericIO/GGIO1.AnIn1.mag.f"
        functional_constraint: "MX"   # Measurand-Tree (Default)
        datatype: "float"
        access: "read"
      battery1_status:
        object_reference: "SimpleIOGenericIO/GGIO1.Ind1.stVal"
        functional_constraint: "ST"   # Status (FC-Override)
        datatype: "bool"
        access: "read"
      battery1_count:
        object_reference: "SimpleIOGenericIO/GGIO1.IntIn1.stVal"
        functional_constraint: "MX"
        datatype: "int32"
        access: "read"
      battery1_label:
        object_reference: "SimpleIOGenericIO/GGIO1.NamPlt.d"
        functional_constraint: "CF"   # Configuration (FC-Override)
        datatype: "string"
        access: "read"
```

**Konsequenzen:**

- **YAGNI:** kein separates `iec61850_profiles`-Top-Level-
  Schema noetig. Welle-1-/Welle-2-/Welle-3-/Welle-4-/
  Welle-5a-Konsistenz: ALLE Adapter-Profile sind inline.
- **Validator-Pflicht:** `_config.py` validiert pro
  Target: `object_reference` als nicht-leerer String mit
  mindestens einem `/` (LD/LN.DO.DA-Pattern); `datatype`
  in `{bool, int32, float, string}` (Welle-5b-Allowlist —
  siehe Decision I-c); `functional_constraint` in
  `{MX, ST, SP, CF}` (Welle-5b-Allowlist; siehe
  Decision I-c); `access == "read"` (Welle-5b-Minimum;
  Write-Pfad Welle-6+).
- **Scenario-Loader bleibt IEC-61850-frei** (AC-HEXAGON-
  PURE): `hexagon/core/scenario/loader.py` darf
  `Iec61850ProtocolPortConfig` nicht direkt parsen —
  Welle-1-Konsequenz aus ADR 0030 §2.1.
- **CID/SCD/ICD-File-Import (61850-Spec-Pflicht-Format):**
  nicht in Welle 5b. Welle-6-Schaerfung kann den
  Object-Reference-String aus einer SCD-Datei
  auto-generieren (`pyiec61850.server.IedServer` akzeptiert
  einen `model_path`-Argument, das einen SCL/CFG-Pfad
  laedt). Welle-5b-Minimum: Runtime-Model ohne SCL-Datei.

### 2.2 Decision I-b — Direkt-Sync (kein Adapter-interner Loop-Thread, final)

Der Adapter ruft `pyiec61850.mms.MMSClient`-Methoden
**direkt** aus dem `DeviceProtocolPort`-Caller-Kontext
auf. **Kein** Adapter-interner Thread/Loop-Marshal.
Pattern-Praezedenz: Welle-3-Modbus-Decision-M-c
(pymodbus sync direkt) + Welle-5a-DNP3-Decision-D-b
(nfm-dnp3 sync direkt). Welle-5b folgt diesem Pattern,
**nicht** dem Welle-4-OPC-UA-Decision-O-b
(`OpcuaLoopThread`-async-Bridge).

**Begruendung (Library-Recherche-Befund 2026-06-01):**

- `pyiec61850.mms.MMSClient` ist als sync-Context-
  Manager implementiert: `with MMSClient(host, port) as
  client: client.read_value(ref, fc)`. Alle relevanten
  Public-Methoden (`__enter__`/`__exit__`/`connect`/
  `disconnect`/`read_value`/`write_value`) sind sync.
- Low-Level-`pyiec61850.pyiec61850` (SWIG-Wrapper-Layer)
  exponiert ebenfalls sync C-Bindings.
- Kein async-Pfad in der Library — `OpcuaLoopThread`-
  Reuse-Pattern ist nicht noetig und waere
  Over-Engineering.

**Konsequenzen:**

- **Adapter-Komplexitaet minimal:** `_port.py` hat
  keinen Loop-Thread, keine `asyncio.run_coroutine_threadsafe`-
  Marshal-Pfade, kein `OpcuaLoopThreadStartTimeoutError`-
  aequivalent.
- **`AC-ADAPTER-LIGHTWEIGHT` greift unveraendert**
  (`tools/arch_check.py:1089` `bucket.startswith("protocol_")`
  — kein neuer Pfad-Filter noetig).
- **SWIG-Memory-Management:** der Adapter haelt
  `MMSClient` als Instance-Attribut zwischen `start()`
  und `stop()`. Context-Manager-`__enter__/__exit__`
  ist idempotent — wiederholtes `start()` ist no-op,
  `stop()` ist no-op nach `stop()`. Welle-6-Schaerfung
  kann hier ein typed Lifecycle-Lock einfuehren falls
  Race-Conditions auftreten.

### 2.3 Decision I-c — MMS-Datatype-Set + FC-Mapping (final)

Welle-5b-Minimum unterstuetzt **vier** MMS-Datentypen
mit **vier** Functional-Constraints. Pattern-Praezedenz:
Welle-3-Decision-M-d (5 Datatypes), Welle-4-Decision-O-c
(8 Datatypes), Welle-5a-Decision-D-c (3 Group/Variation-
Werte).

**Datatypes (Welle-5b-Allowlist):**

| `datatype`-YAML | MMS-Typ | Python-Native | Server-Update | Client-Read |
|---|---|---|---|---|
| `bool` | `BOOLEAN` | `bool` | `update_boolean(ref, val)` | `MMSClient.read_value(ref, fc)` → `bool` |
| `int32` | `INT32` | `int` | `update_int32(ref, val)` | `MMSClient.read_value(ref, fc)` → `int` |
| `float` | `FLOAT32` | `Decimal(repr(float))` | `update_float(ref, val)` | `MMSClient.read_value(ref, fc)` → `float` (Codec wickelt auf `Decimal`) |
| `string` | `VISIBLE_STRING` | `str` | `update_visible_string(ref, val)` | `MMSClient.read_value(ref, fc)` → `str` |

**Codec-Asymmetrie (analog ADR 0032 §2.2):** Decoding ist
**tolerant** (akzeptiert auch IEC-61850-fremde Numerik
wie `bytes`/`bytearray`-Encodings via `int.from_bytes`-
Fallback), Encoding ist **strikt** (Welle-6 falls Writes
eingefuehrt werden). Decoder-Quality-Annotation:
`Quality.GOOD` als Default; `Quality.QUESTIONABLE` falls
Codec einen `OverflowError` fangen muss (analog Welle-4-
Float-Quantisierung aus Slice 032).

**Functional-Constraints (Welle-5b-Allowlist):**

| `functional_constraint`-YAML | IEC-61850-Semantik | Welle-5b-Default-Verwendung |
|---|---|---|
| `MX` | Measurand-Subtree (Default) | Float-/Int-Mess-Daten (Voltage, Current, Power) |
| `ST` | Status-Subtree | Boolean-Stati (Open/Closed, Fault) |
| `SP` | Setpoint-Subtree | Konfigurierbare Sollwerte (read-only in Welle 5b) |
| `CF` | Configuration-Subtree | Konfigurations-Strings (Labels, Modell-Namen) |

**FC-Default ist `MX`** (Measurand-Subtree) — das ist der
am haeufigsten verwendete FC fuer Read-Pfade in IEC-61850.
Per-Target-Override via `functional_constraint`-Feld in
`Iec61850LnConfig`.

**Andere MMS-Datentypen** (`INT8/16/64`, `UINT*`,
`OCTET_STRING`, `BIT_STRING`, `UTC_TIME`, Arrays, Structs)
bleiben Welle-6+-Schaerfung (ADR-0011-Pfad).

**Andere FCs** (`SV`, `CO`, `EX`, `OR`) bleiben Welle-6+-
Schaerfung — die selten verwendeten Sub-Trees brauchen
keinen Welle-5b-Spike-Support.

**Konsequenzen:**

- `_codec.py` exponiert `decode_mms_value(value: object,
  datatype: Literal["bool", "int32", "float", "string"])
  → bool | int | Decimal | str` als Public-API.
- Property-Tests via `hypothesis` (Pattern-Praezedenz
  Welle-5a-Codec-Property-Tests): Roundtrip-Test pro
  Datatype gegen den jeweiligen `IedServer.update_*`-Pfad.
- `_errors.py` exponiert typed
  `Iec61850CodecOverflowError` (analog Welle-5a-DNP3-
  Codec-Errors).

### 2.4 Decision I-d — Per-Target MMS-Read mit FC-Override (final)

Der `DeviceProtocolPort.read(target)`-Call mapped auf
`MMSClient.read_value(object_reference, functional_constraint)`
**pro Target**. Kein Subscription-/Report-Control-Block-
Pfad (Welle-6+).

**Read-Sequenz:**

1. `_port._find_point(target.device_id) → Iec61850LnConfig`
   (Welle-5b-Anti-Scope-Check: `access == "read"` sonst
   `Iec61850PortReadAccessMismatchError`).
2. `self._client.read_value(point.object_reference, point.functional_constraint)
   → raw_value` (sync, blocking). FC ist als
   Two-Letter-String (`"MX"`/`"ST"`/`"SP"`/`"CF"`)
   uebergeben (pyiec61850-ng-Library-Konvertierung auf
   den int-Enum erfolgt intern). Adapter-Default ist
   `"MX"` (gesetzt im `_config.py`-Default, nicht dem
   Library-Default `"ST"` ueberlassen).
3. `decode_mms_value(raw_value, point.datatype) →
   Python-Native`.
4. `TelemetryPoint`-Verpackung mit `Quality.GOOD` (oder
   `Quality.QUESTIONABLE` bei Codec-Overflow).

**Error-Translation** (pyiec61850-ng-Exception-Famille
aus `pyiec61850.mms`):

- `LibraryNotFoundError` →
  `Iec61850PortLibraryNotInstalledError` (NEU, klare
  Meldung: „Install with: `pip install grid-gym[iec61850]`";
  Decision-I-f-Folge — Library ist optional extra).
- `ConnectionFailedError` /
  `ConnectionTimeoutError` →
  `Iec61850PortConnectError` (mit `cause`-Attribut).
- `NotConnectedError` →
  `Iec61850PortReadNotStartedError`.
- `ReadError` → `Iec61850PortReadFailedError` (mit
  `cause`-Attribut). Object-Reference-Not-Found wird
  als `ReadError` mit spezifischer Library-Message
  geliefert (pyiec61850-ng hat **kein** separates
  `ObjectReferenceError`); Adapter mappt das per
  Substring-Match auf `Iec61850PortPointNotFoundError`,
  falls die Library-Message Object-Reference-Hinweise
  traegt — sonst bleibt `Iec61850PortReadFailedError`.
- `WriteError` → `Iec61850PortWriteFailedError`
  (Welle-6-Material; Welle-5b-Anti-Scope wirft
  `Iec61850PortWriteNotImplementedError` **vor**
  Library-Call).
- `MMSError` (Top-Level-Catch-All) →
  `Iec61850PortReadFailedError`.

**Write-Pfad (Anti-Scope Welle 5b):** `write(target,
command)` wirft `Iec61850PortWriteNotImplementedError`
fuer alle Targets **vor** dem Library-Call. Welle-6-
Schaerfung kann `MMSClient.write_value(ref, value)`
einfuehren (Anmerkung: pyiec61850-ng-Write-API ist
`write_value(reference, value)` ohne separates FC-
Argument — FC wird im Reference-String mit
`[FC]`-Suffix kodiert, z. B. `"LD0/MMXU1.TotW.mag.f[MX]"`,
oder ueber FC-Default `"ST"`).

**Konsequenzen:**

- **Per-Read-Latency** ist Welle-5b-Anti-Scope (kein
  Tick-Caching, kein Batch-Read). Welle-6-Schaerfung
  kann Tick-Caching cross-Adapter einfuehren.
- **Quality-Annotation** ist Welle-5b-Minimum
  (`GOOD`/`QUESTIONABLE`); IEC-61850-Spec-Quality-
  Sub-Codes (`validity`, `overflow`, `outOfRange`,
  `oldData`) bleiben Welle-6+-Schaerfung.

### 2.5 Decision I-e — In-Process `pyiec61850.server.IedServer` mit CFG-Fixture als Test-Sibling (final mit 2c-Mock-only-Fallback)

Integration-Smoke spawned einen **in-process** IEC-61850-
Server unter `tests/integration/test_iec61850_in_process_smoke.py`
via `pyiec61850.server.IedServer(model_path=fixture_path)`-
Context-Manager. Pattern-Praezedenz: Welle-3-Decision-M-f
(pymodbus-Server) + Welle-4-Decision-O-e (asyncua-Server)
+ Welle-5a-Decision-D-e (dnp3-outstation-Server). **Eine**
Library wie Welle 3 und 4, **nicht** zwei wie Welle 5a.

**Modell-Pflicht:** `IedServer.__init__(model_path=None,
config=None)` akzeptiert einen optionalen `model_path`;
falls `None`, wirft `start()` **explizit**
`ModelError("No data model loaded")`. Welle-5b-Smoke MUSS
deshalb ein Modell mitliefern — der argumentlose
`IedServer()`-Konstruktor-Pfad ist **nicht** lauffaehig.

**Fixture-Skizze:**

NEU `tests/integration/fixtures/iec61850/simpleIO.cfg` —
minimales libiec61850-natives Modell-Konfig-Format
(Format: libiec61850-`IedModel_createFromConfigFile`-
kompatibel, **kein** SCL-XML). Eine `LogicalDevice`
`simpleIOGenericIO`, eine `LogicalNode` `GGIO1`, vier
DataObjects fuer die 4 Welle-5b-Datatypes:

```
# Welle-5b minimal Test-Modell — libiec61850-CFG-Format
MODEL(SimpleIO){
  LD(simpleIOGenericIO){
    LN(GGIO1){
      DO(AnIn1){             # float32 Analog-Input
        DA(mag.f) FC(MX) FLOAT32;
      }
      DO(IntIn1){            # int32 Integer-Input
        DA(stVal)   FC(MX) INT32;
      }
      DO(Ind1){              # bool Indication
        DA(stVal)   FC(ST) BOOLEAN;
      }
      DO(NamPlt){            # string Konfig-Label
        DA(d)       FC(CF) VISIBLE_STRING_64;
      }
    }
  }
}
```

(Exaktes CFG-Format-Detail — Trennzeichen, Pflicht-/
Optional-Felder — wird in C2 anhand der pyiec61850-ng-
Examples + libiec61850-Source `mz-automation/libiec61850/
examples/server_example_basic_io` fixiert.)

**Smoke-Architektur (korrigiert):**

```python
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "iec61850" / "simpleIO.cfg"

def test_iec61850_read_roundtrip_smoke() -> None:
    with IedServer(model_path=str(FIXTURE_PATH)) as server:
        server.start(port=10102)
        server.update_float(
            "simpleIOGenericIO/GGIO1.AnIn1.mag.f", 230.5
        )
        server.update_boolean(
            "simpleIOGenericIO/GGIO1.Ind1.stVal", True
        )
        # ... wait for connect readiness via bounded poll
        config = Iec61850ProtocolPortConfig(
            host="127.0.0.1", port=10102, ied_name="SimpleIO",
            ...
        )
        with Iec61850DeviceProtocolPort(config) as adapter:
            point = adapter.read(target=...)
        assert point.value == Decimal("230.5")
        # server context manager handles stop() + cleanup
```

**Anti-Scope:** kein SCL-Import allgemein, kein
generischer Modell-Loader — nur das Welle-5b-Spike-
Fixture deckt die 4 Datatypes. SCL/CID/ICD-File-Import
(IEC-61850-Spec-Pflicht-Format) bleibt Welle-6-
Schaerfung (siehe §2.1 Decision I-a Konsequenzen).

**Wire-Compat-Risiko:** `pyiec61850.mms.MMSClient` ist
Top-Level-`__version__ = "1.6.1.2"` (stabile Client-API),
waehrend `pyiec61850.server.__version__ = "0.1.0"` (Pre-
Alpha im Server-Submodul). Beide sind in einem Wheel
ausgeliefert und gegen die gleiche libiec61850-1.6-`.so`
gelinkt — Wire-Compat ist **wahrscheinlich** OK, aber
**nicht** vorab verifiziert. **C2-Smoke ist die Wire-
Compat-Verifikations-Pflicht**.

**Mock-only-Fallback (2c, explizit dokumentiert):**
Falls C2-Smoke zeigt, dass entweder das CFG-Format
nicht schnell stabil validierbar ist ODER die Wire-
Compat zwischen Client-1.6.1.2 und Server-0.1.0 gebrochen
ist, faellt Decision I-e auf „Mock-only-Smoke" zurueck —
`tests/integration/test_iec61850_in_process_smoke.py`
wird durch eine Mock-Client-/Mock-Server-Konstruktion in
`tests/unit/adapters/driven/protocol_iec61850/`
ersetzt. Welle-5b-DoD bleibt erfuellbar (Welle-5b-DoD
verlangt **Adapter-Lieferung** und **Tests**, nicht
zwingend Integration-Smoke). **Welle 6** bekommt den
echten `IedServer`-Smoke als Schaerfungspfad.

**Konsequenzen:**

- `pyiec61850-ng>=1.6,<2.0` in
  `[project.optional-dependencies.iec61850]` (siehe
  Decision I-f) — **nicht** `[project] dependencies`.
  Tests laufen via Docker/Makefile-Target mit explizitem
  extra-Flag (`uv sync --extra iec61850`).
- mypy-Override fuer `pyiec61850.*` mit
  `ignore_missing_imports = true` (kein py.typed-Marker).
- `tests/integration/compose.yml`-Header-Kommentar-Sync
  in C2 dokumentiert die Decision-I-e-Wahl (in-process-
  Sibling mit CFG-Fixture; kein neuer Container-Service).
- NEU `tests/integration/fixtures/iec61850/simpleIO.cfg`
  als minimales Welle-5b-Test-Modell (4 Datatypes; kein
  generischer SCL-Loader).

### 2.6 NEU Decision I-f — Lizenz-Boundary GPLv3-Isolation auf `protocol_iec61850/*` (final)

**Erstmaliger Praezedenzfall im Repo** fuer GPL-isolierte
Sub-Module in einem sonst MIT-lizenzierten Projekt.

**Problemstellung:**

- `pyiec61850-ng` ist **GPLv3** (libiec61850-Bindings,
  MZ Automation; libiec61850 selbst ist Dual-Licensed
  GPLv3/Commercial — die Open-Source-Variante ist GPLv3).
- grid-gym ist **MIT** ([`LICENSE`](../../../LICENSE)).
- Direkt-Imports von `pyiec61850.*` in `src/` machen die
  importierende Datei nach FSF-Auslegung zu einem
  derivative work von libiec61850 — sie muesste daher
  bei Distribution unter GPLv3 stehen.
- Pure-Python-MIT-Alternativen (`py61850` — Pre-Alpha,
  nur GOOSE-Publisher) sind nicht produktiv-reif.
- Kommerzielle MZ-Automation-Lizenz ist kein Open-Source-
  Weg.

**Decision:**

`src/grid_gym/adapters/driven/protocol_iec61850/*` +
zugehoerige Tests
(`tests/unit/adapters/driven/protocol_iec61850/*` +
`tests/integration/test_iec61850_*.py`) werden
**GPLv3-isoliert** via SPDX-Header pro Datei UND
`pyiec61850-ng` wird ueber **Optional-Extra** opt-in
gemacht — Top-Level-`pip install grid-gym` bleibt MIT-
sauber, GPL wird per `pip install grid-gym[iec61850]`
bewusst aktiviert:

```python
# SPDX-License-Identifier: GPL-3.0-only
```

Rest grid-gym bleibt MIT. Dual-License-Setup ueber
mehrere Komponenten:

1. **SPDX-Header pro Datei** in der GPL-Boundary:
   `# SPDX-License-Identifier: GPL-3.0-only` als erste
   Code-Zeile in jeder `.py`-Datei unter
   `protocol_iec61850/`, `test_iec61850_*.py`,
   `tests/unit/adapters/driven/protocol_iec61850/*.py`.
2. **NEU `[project.optional-dependencies.iec61850]`**
   in `pyproject.toml`:
   ```toml
   [project.optional-dependencies]
   iec61850 = ["pyiec61850-ng>=1.6,<2.0"]
   ```
   `pyiec61850-ng` ist **nicht** in `[project] dependencies`
   und **nicht** doppelt in `[dependency-groups.dev]`
   (Drift-Risiko vermeiden). CI/Tests muessen das Extra
   explizit installieren — via `uv sync --extra iec61850`
   im Dockerfile- oder Makefile-Target.
3. **NEU `LICENSES/GPL-3.0.txt`** mit Standard-GPL-3.0-
   Volltext (verbatim von `https://www.gnu.org/licenses/gpl-3.0.txt`).
4. **EDIT Top-Level-`LICENSE`** mit Hinweis-Block am
   Ende: „Except for `src/grid_gym/adapters/driven/protocol_iec61850/`
   and its corresponding tests
   (`tests/unit/adapters/driven/protocol_iec61850/` and
   `tests/integration/test_iec61850_*.py`), which link
   against the GPLv3-licensed `pyiec61850-ng` /
   `libiec61850` library and are therefore distributed
   under GPL-3.0-only — see `LICENSES/GPL-3.0.txt`. The
   `pyiec61850-ng` library itself is installed via the
   optional extra `pip install grid-gym[iec61850]`; the
   default `pip install grid-gym` ships only MIT-licensed
   code."
5. **EDIT `README.md` + `README.de.md`** mit Lizenz-
   Hinweis-Sektion + Optional-Extra-Install-Hinweis.
6. **Top-Level-MIT-Classifier in `pyproject.toml`
   bleibt unveraendert** — der beschreibt das Top-Level-
   Werk, das MIT bleibt; GPL-Boundary ist File-Level
   via SPDX dokumentiert und Distribution-Level via
   Optional-Extra getrennt.
7. **Loader/Factory-Hook ImportError-tolerant:** der
   Welle-1-`build_protocol_ports`-Hook (`type: iec61850`
   im Scenario-YAML) **muss** ImportError abfangen und
   eine klare typed Fehlermeldung
   `Iec61850PortLibraryNotInstalledError("Install with:
   pip install grid-gym[iec61850]")` werfen — sonst
   bricht der Loader bei nicht-installierter Extra
   mit `ModuleNotFoundError: No module named 'pyiec61850'`.

**Praezedenz-Faelle (extern):**

- ffmpeg-Python-Wrapper in MIT-Projekten (ffmpeg ist
  LGPL/GPL; Wrapper-Code GPL-isoliert).
- GTK-Bindings in MIT-Tools (GTK ist LGPL; Bindings
  GPL-/LGPL-isoliert).
- Linux-Kernel-Tree: GPLv2 Kernel + GPLv2-only Modules
  + Userland-Tools mit eigener Lizenz.

**Konsequenzen:**

- **Linting-Pflicht:** SPDX-Header in allen 12 neuen
  Files (5 `protocol_iec61850/*.py` + 4
  `tests/unit/adapters/driven/protocol_iec61850/*.py` +
  1 `tests/integration/test_iec61850_*.py` + 2 `__init__.py`
  unter `tests/unit/adapters/driven/protocol_iec61850/`).
  Welle-6-Schaerfung kann `tools/check_refs.py` um einen <!-- d-check:ignore (historisch: check_refs abgeloest durch d-check, 766ae8c) -->
  SPDX-Header-Konsistenz-Check erweitern.
- **CONTRIBUTING.md-Sync** (falls vorhanden) ist
  Welle-6-Material; Welle-5b-Minimum ist nur SPDX +
  Top-Level-LICENSE + README.
- **Distribution-Aufwand:** wer grid-gym als gebundeltes
  Docker-Image oder Wheel distribuiert UND das
  `protocol_iec61850/`-Modul mitliefert, muss die GPL-
  Pflicht fuer dieses Modul einhalten (Source-Offenlegung
  fuer libiec61850 + pyiec61850-ng + den GPL-isolierten
  Adapter-Code). Andere Module bleiben MIT-distribuierbar.
- **Import-Hygiene-Pflicht:** kein MIT-Code in
  grid-gym darf direkt aus `protocol_iec61850/`
  importieren — `protocol_iec61850/` wird ueber den
  Plugin-Hook (Welle-1-`build_protocol_ports`) gelaedt,
  nicht ueber direkte Imports. Damit bleibt der MIT-
  Code MIT-konform (er linkt nicht gegen GPL-Code).
- **AC-Contract-Folge:** `arch_check.py` koennte in
  Welle-6 einen Contract bekommen, der verbietet, dass
  `src/grid_gym/`-MIT-Code direkt aus `protocol_iec61850/`
  importiert. Welle-5b-Minimum: nur SPDX-Header und
  Dokumentation; AC-Contract Welle-6.

---

## 3. Alternativen

**A1 (verworfen) — Separate `iec61850_profiles`-Top-
Level-Section:** wuerde Decision I-a auf eine eigene
Schluessel-Section verlagern. Verworfen wegen YAGNI
(siehe ADR 0031 §3 A1 / ADR 0032 §3 A1 / ADR 0033 §3 A1
/ ADR 0034 §3 A1).

**A2 (verworfen) — Adapter-interner asyncio-Loop-
Thread (`OpcuaLoopThread`-Reuse):** verworfen, weil
`pyiec61850-ng` sync ist (Library-Recherche-Befund
2026-06-01: MMSClient + IedServer beide sync-Context-
Manager). Kein Loop-Marshal noetig. Welle 4 OPC-UA hat
den Pfad (asyncua ist async); Welle 5b folgt Welle-3-
Modbus + Welle-5a-DNP3-Pattern (sync direkt).

**A3 (verworfen) — Datatype-Set inklusive UINT-Typen +
OCTET_STRING + UTC_TIME + Arrays + Structs ab Welle 5b:**
wuerde Welle-5b-Codec-Komplexitaet vervielfachen.
Verworfen wegen YAGNI; ADR-0011-Schaerfungspfad bleibt
offen fuer Welle-6.

**A4 (verworfen) — Subscription-/Report-Control-Block-
Polling ab Welle 5b:** IEC-61850-Spec hat einen
mechanismus-spezifischen Subscription-Pfad (RCB:
Report Control Block). Verworfen wegen YAGNI — Welle-5b-
Minimum ist Per-Target-Read, RCB ist Welle-6-Schaerfung.

**A5 (verworfen, nach Lizenz-Check) — `pyiec61850`
(MZ-Automation-Original) statt `pyiec61850-ng`:** das
Original hat keinen PyPI-Wheel und braucht einen
Source-Build via cmake+swig. Verworfen, weil
`pyiec61850-ng` der besser-gepackte Fork mit pre-built
manylinux1-Wheels ist (gleicher GPLv3-Code, aber bessere
Distribution-Story).

**A6 (verworfen, nach Lizenz-Check) — `py61850`
(arthurazs, MIT, Pure-Python):** waere die einzige MIT-
Library und damit ohne Lizenz-Boundary-Pflicht.
Verworfen, weil:

- Library ist Pre-Alpha (88 Commits, keine Releases,
  20 GitHub-Stars).
- Implementiert **nur** GOOSE-Publisher, **kein** MMS.
- Welle-5b-Minimum ist MMS-Read (`DeviceProtocolPort.read()`-
  Vertrag).
- Library ist nicht auf PyPI — muesste als git-Dependency
  rein.

**A7 (verworfen, nach Lizenz-Check) — `keyvdir/pyiec61850`
Fork als alternative Server-Library (zwei-Library-Setup
wie Welle 5a):** der keyvdir-Fork liefert Server+Client
in einer Library, aber:

- Kein PyPI-Wheel, nur Source-Build via cmake+swig.
- mbedtls-2.16.0 ist EoL (heute mbedtls 3.x); Build-
  Fragilitaet.
- 15 Commits total, kein Release-Tag, libiec61850
  unpinned (clont `master`).
- ABI-Koexistenz-Risiko mit `pyiec61850-ng` (beide
  brauchen libiec61850.so).
- Auch GPLv3 — kein Lizenz-Vorteil ggue. `pyiec61850-ng`.

Verworfen — `pyiec61850-ng` mit Server-Submodul liefert
**eine** Library fuer beide Seiten und ist die
pragmatischere Wahl.

**A8 (verworfen) — Disposition-Only-Lieferung (kein
Adapter):** Welle 5b liefert nur ADR 0035 als „Welle 5b
liefert keinen Adapter — Lizenz-Inkompatibilitaet" und
laesst die Roadmap-Checkbox als „bewusst nicht geliefert"
stehen. Verworfen, weil:

- Lizenz-Boundary-Decision I-f ist machbar — Praezedenzen
  existieren (ffmpeg-Python-Wrapper, GTK-Bindings).
- IEC-61850 ist im Lastenheft `SOLLTE`, nicht `MUSS` —
  Disposition-Only waere spec-konform, aber liefert
  weniger Wert.
- M4-Welle-7-Closure-Story wird sauberer mit
  vollstaendiger Adapter-Mantel-Welle.

**A9 (verworfen) — Test-only Spike (`pyiec61850-ng`
nur in `[dependency-groups.dev]`, kein Adapter unter
`src/`):** waere lizenzsauberer (GPL nur in Tests, nicht
in distribuiertem Code). Verworfen, weil:

- Liefert keinen produktiven Wert — der Adapter waere
  nur eine Test-Mock-Konstruktion.
- Roadmap-`IEC-61850-Adapter`-Checkbox kann mit Test-
  only-Spike nicht ehrlich abgehakt werden.
- Welle-6-Schaerfung muesste den Adapter dann nochmal
  produktiv ziehen — doppelter Aufwand.

**A10 (verworfen) — testcontainers + `iec61850_open_server`-
Docker-Image als Sibling:** wuerde das in-process-Pattern
von Welle 3/4/5a brechen und zum Welle-2-MQTT-mosquitto-
Sibling-Stil zurueckkehren. Verworfen, weil:

- `pyiec61850.server.IedServer` ist als in-process-Server
  verfuegbar — Welle-3-/Welle-4-/Welle-5a-Pattern bleibt
  konsistent.
- testcontainer-Setup ist Welle-2-MQTT-Pattern, aber
  bringt extra Docker-Build-/Pull-Aufwand fuer eine
  Welle, die keinen externen Sibling braucht.

**A11 (verworfen) — aarch64-Source-Build von
`pyiec61850-ng` in Dockerfile:** wuerde Raspberry-Pi-64-
bit-Builds ermoeglichen. Verworfen, weil:

- Welle-5b-Anti-Scope (kein aarch64-Support).
- Build-Aufwand erheblich (cmake + swig + mbedtls +
  libiec61850 von Source).
- grid-gym laeuft primaer x86_64/manylinux1 — kein
  Bedarf aktuell.

Welle-6-Schaerfung kann den aarch64-Build-Pfad einfuehren,
falls Raspberry-Pi-64-Bedarf entsteht.

**A12 (verworfen) — SCL/CID/ICD-File-Import als
Welle-5b-Pflicht:** IEC-61850-Spec definiert SCL
(Substation Configuration Language) als
XML-Konfigurationsformat. Verworfen, weil:

- Welle-5b-Minimum ist Runtime-Model ohne SCL-Datei.
- SCL-Parser-Implementierung ist eigener Welle-Aufwand.
- Welle-6-Schaerfung kann SCL-Import nachziehen
  (`pyiec61850.server.IedServer` akzeptiert einen
  `model_path`-Argument).

---

## 4. Konsequenzen

- **Welle-5b-C2-Implementierungs-Pflicht** (`feat(welle-5b):
  protocol_iec61850 + Tests + In-Process-Smoke + GPL-
  Lizenz-Boundary`):
  - NEU `src/grid_gym/adapters/driven/protocol_iec61850/__init__.py`
    mit `Iec61850DeviceProtocolPort` als
    `DeviceProtocolPort`-Implementer (ADR 0030 §2.1) +
    SPDX-Header.
  - NEU `src/grid_gym/adapters/driven/protocol_iec61850/_config.py`
    (`Iec61850ProtocolPortConfig` + `Iec61850LnConfig`
    frozen-dataclasses, Decision I-a-Schema) + SPDX-Header.
  - NEU `src/grid_gym/adapters/driven/protocol_iec61850/_codec.py`
    (`decode_mms_value`-Funktion, Decision I-c) + SPDX-
    Header.
  - NEU `src/grid_gym/adapters/driven/protocol_iec61850/_port.py`
    (Decision I-b direkt-sync; Decision I-d Per-Target-
    Read; pyiec61850-ng-Exception-Translation) + SPDX-
    Header.
  - NEU `src/grid_gym/adapters/driven/protocol_iec61850/_errors.py`
    (typed `DeviceProtocolPort*Error`-Subclasses
    inkl. Read/Write-Operation-Tax analog Slice-031/032-
    Pattern: `Iec61850PortConnectError`,
    `Iec61850PortDisconnectError`,
    `Iec61850PortReadNotStartedError`,
    `Iec61850PortReadAccessMismatchError`,
    `Iec61850PortReadFailedError`,
    `Iec61850PortPointNotFoundError`,
    `Iec61850PortWriteNotImplementedError`,
    `Iec61850CodecOverflowError`) + SPDX-Header.
  - **Modul-Docstring** mit Lastenheft-Z. 1155–1157-
    Pflicht: „Simulations-/Testadapter; keine produktive
    Anlagensteuerung" + GPLv3-Lizenz-Hinweis.
  - 3 Unit-Test-Module unter
    `tests/unit/adapters/driven/protocol_iec61850/`
    (Config / Codec / Protocol-Port) + SPDX-Header in
    allen Files.
  - 1 Integration-Smoke unter
    `tests/integration/test_iec61850_in_process_smoke.py`
    (Decision I-e) + SPDX-Header.
- **NEU `LICENSES/GPL-3.0.txt`** (Standard-GPL-3.0-
  Volltext, Decision I-f).
- **EDIT Top-Level-`LICENSE`** mit Hinweis-Block fuer
  GPL-Boundary auf `protocol_iec61850/*` (Decision I-f).
- **EDIT `README.md` + `README.de.md`** mit Lizenz-
  Hinweis-Sektion (Decision I-f).
- **`tests/integration/compose.yml`-Header-Kommentar-
  Sync (C2 EDIT):** dokumentiert die bewusste Decision-
  I-e-Wahl (in-process-Smoke; **eine** Library wie
  Welle 3 + 4, **anders als** Welle 5a) und Decision-
  I-f-Lizenz-Boundary-Hinweis.
- **`pyproject.toml`-Erweiterung** (Decision I-f):
  - NEU `[project.optional-dependencies] iec61850 =
    ["pyiec61850-ng>=1.6,<2.0"]`. **Nicht** in
    `[project] dependencies` und **nicht** doppelt in
    `[dependency-groups.dev]` (Drift-Risiko vermeiden).
  - mypy-Override `module="pyiec61850.*"` mit
    `ignore_missing_imports = true` (kein py.typed-
    Marker).
  - `pyiec61850-ng`-Sichtbarkeit in [`AC-PORTS-NO-FW`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)/
    AC-NO-FW-Forbidden-Listen — Welle-0-Vorbelegung
    pruefen; ggf. C2-Edit.
  - Top-Level-MIT-Classifier bleibt unveraendert
    (Decision I-f).
- **`Dockerfile`-Sync** (Decision I-f-Folge): die
  Stage(s), in denen `make test-unit`/`make test-integration`/
  `make gates` laufen, muessen das Extra explizit
  installieren — `uv sync --extra iec61850` oder
  aequivalent. C2-Edit legt das Detail fest (es kann eine
  separate `--target iec61850-deps`-Stage werden, oder
  das Extra wird unter `--all-extras` im Default-Sync
  mitgenommen).
- **`Makefile`-/CI-Sync** (Decision I-f-Folge): falls
  Welle 6 ein separates `make test-iec61850`-Target
  einfuehrt, kann der Default-`make gates`-Pfad
  konfigurieren, ob IEC-61850-Smoke laeuft. Welle-5b-
  Minimum: IEC-61850-Smoke laeuft im Default-Pfad
  (`uv sync --extra iec61850` im Dockerfile-`source`-
  Stage), keine konditionale Skip-Logik.
- **Loader-Hook ImportError-Schutz** (Decision I-f-Folge):
  `build_protocol_ports(scenario.protocol_ports)`-Hook
  muss `ImportError` aus `import pyiec61850` abfangen
  und in
  `Iec61850PortLibraryNotInstalledError("Install with:
  pip install grid-gym[iec61850]")` uebersetzen.
  Welle-5b-C2 implementiert das im
  `protocol_iec61850/__init__.py`-Top-Level-Try-Block
  ODER im Welle-1-Factory-Hook.
- **`Dockerfile`-Erweiterung:** `CRITICAL_COV_TARGETS`-
  Default um `src/grid_gym/adapters/driven/protocol_iec61850`
  erweitert (Pattern analog Welle 2/3/4/5a).
- **`AC-ADAPTER-LIGHTWEIGHT` greift unveraendert**
  (`tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`).
- **Scenario-Loader bleibt IEC-61850-frei** (AC-HEXAGON-
  PURE): analog zur Welle-2/3/4/5a-Konsequenz aus
  ADR 0031/0032/0033/0034 §4
  (`hexagon/core/scenario/loader.py` darf
  `Iec61850ProtocolPortConfig` nicht direkt parsen).
- **Caller-Scope-Lifecycle bleibt ADR-0030-Vertrag:**
  Caller wrappen `loop.start_protocol_ports()` /
  `loop.stop_protocol_ports()` in `try/finally`.
- **Snapshot-Vertrag bleibt v2** (ADR 0030 §2.3):
  IEC-61850-Adapter ist stateless aus Replay-Sicht;
  MMS-Session-State und RCB-Subscription-State sind
  volatile.
- **OTel-Span-Wrap der Adapter-Calls:** ADR 0035 wrappt
  Adapter-Calls **nicht** mit OTel-Spans. Welle 6 ist
  der Zeitpunkt fuer den `TracePort`-Wrap (cross-Adapter
  fuer alle 5 `protocol_*`-Adapter aus Welle 2/3/4/5a/5b).
- **M4-Welle-7-Closure-Folge-Pflicht:**
  - ADR 0030 §2.4 (IEC-61850-Verzicht-Default aus
    Welle 1) wird durch Welle-5b-Spike-Lieferung
    aufgeloest — Welle 7 schaerft ADR 0030 §2.4 auf
    „durch Welle-5a (DNP3) **und** Welle-5b (IEC-61850)
    aufgeloest" (Pattern ADR 0011).
  - ADR 0035 `Provisional → Accepted` analog ADR
    0022..0027 + 0030 + 0031 + 0032 + 0033 + 0034.
  - Roadmap §3 M4 DoD-Checkbox `IEC-61850-Adapter` wird
    in Welle 7 abgehakt (gemeinsam mit DNP3/OPC-UA/
    Modbus/MQTT).
- **Welle-6-Schaerfungs-Pfade:**
  - IEC-61850-Write-Pfad (MMSClient.write fuer
    Setpoint/Konfigurations-Updates). Welle-5b-Minimum
    ist Read-only.
  - IEC-61850-Report-Control-Block-Subscription
    (RCB-Polling oder asynchrones Subscribe).
  - GOOSE-Publishing/Subscription via
    `pyiec61850.goose`-Submodul.
  - Sampled-Values (IEC-61850-9-2) via
    `pyiec61850.sv`-Submodul.
  - IEC-61850-Security (TLS, IEC-62351-3, IEC-62351-6).
  - SCL/CID/ICD-File-Import via
    `IedServer(model_path=...)`-Argument.
  - aarch64-Wheel-Support (Source-Build oder
    upstream-Wheel falls verfuegbar).
  - **`tools/check_refs.py`-SPDX-Header-Konsistenz-Check <!-- d-check:ignore (historisch: check_refs abgeloest durch d-check, 766ae8c) -->
    fuer GPL-Boundary-Files** (Decision-I-f-Folge-
    Pflicht).
  - **`CONTRIBUTING.md`-Sync** (falls vorhanden) mit
    GPL-Boundary-Policy.
  - **`arch_check.py`-Contract gegen GPL-Boundary-
    Crossing:** verbietet, dass `src/grid_gym/`-MIT-Code
    direkt aus `protocol_iec61850/` importiert.
  - Cross-Adapter-Tick-Caching (generisches Pattern,
    nicht IEC-61850-spezifisch).
  - **Adapter-Profil-Index** unter
    `spec/protocol_profiles/` mit Verweisen auf <!-- d-check:ignore (historisch: als Einzeldatei spec/protocol_profiles.md realisiert) -->
    ADR 0031..0035.

---

## 5. Status-Pfad

- **Proposed** — 2026-06-01 (M4-Welle-5b-C1, dieser
  Commit). Initial-Entwurf nach Library-Recherche-Befund
  2026-06-01 (`pyiec61850-ng`-API-Inspektion via PyPI/
  GitHub gegen Top-Level-MMSClient + Server-Submodul +
  Submodule-Liste; Lizenz-Inspektion `pyiec61850-ng`
  GPLv3 + libiec61850 GPLv3 + Mbed TLS Apache 2.0;
  Vergleichs-Inspektion mit Alternativen `pyiec61850`
  (MZ-original), `keyvdir/pyiec61850`, `py61850`,
  `rapid61850`, `py_iec61850_cdc`, `iec61850_open_server`
  zum Aufdecken der Lizenz-/Reife-Lage). Decisions
  I-a..I-f durch Library-Recherche-Ergebnisse
  vorbelegt. Wire-Compat-Verifikation (MMSClient-1.6.1.2
  ↔ IedServer-0.1.0) ist **C2-Smoke-Pflicht** — nicht
  C1-Probe-Run (anders als Welle 5a, wo der C1-Probe-Run
  obligatorisch war wegen zwei-Library-Wire-Compat-
  Risiko). Welle 5b braucht den C1-Probe-Run nicht, weil
  beide Komponenten aus einem Wheel kommen und gegen
  die gleiche libiec61850-`.so` gelinkt sind.
- **Provisional** — geplant 2026-06-XX (M4-Welle-5b-C3)
  nach C2-Merge (feat-Commit: `protocol_iec61850/`-5-
  Modul-Paket — `__init__.py` + `_config.py` + `_codec.py`
  + `_port.py` + `_errors.py` — mit Unit-Tests
  (Config-Validation + Codec-Roundtrip inkl. hypothesis-
  Property-Tests + Protocol-Port-Lifecycle) +
  In-Process-Integration-Smoke gegen
  `pyiec61850.server.IedServer`-Sibling;
  `pyproject.toml`-Pin `pyiec61850-ng>=1.6,<2.0` in
  `[project.optional-dependencies.iec61850]` (Decision
  I-f: opt-in via `pip install grid-gym[iec61850]`) +
  mypy-Override `module="pyiec61850.*"` mit
  `ignore_missing_imports = true`; `uv.lock`-Refresh;
  `Dockerfile`-Edit (`CRITICAL_COV_TARGETS` um
  `adapters/driven/protocol_iec61850` erweitert +
  `uv sync --extra iec61850` in der Test-Stage);
  `compose.yml`-Header-Kommentar-Sync zu Decision-I-e
  in-process-IedServer mit CFG-Fixture; **NEU
  `tests/integration/fixtures/iec61850/simpleIO.cfg`**
  als minimales Test-Modell; **NEU GPL-Boundary-Files**
  (`LICENSES/GPL-3.0.txt` + `LICENSE`-Hinweis-Block +
  README-Lizenz-Sektion + SPDX-Header in 12 Files).
  Verifikation cache-frei: `make test-unit` gruen,
  `make test-integration` gruen mit IEC-61850-Smoke
  (oder Mock-only-Fallback bei Wire-Compat-Bruch),
  `make arch-check` 19/19 KEPT, `make gates` 9 A-1-
  Gates gruen ohne `CRITICAL_COV_TARGETS`-Override.
- **Accepted** — 2026-06-01 mit M4-Welle-7-C1 (dieser
  Commit, M4-Closure-Welle; analog ADR 0022..0027 + 0030
  + 0031 + 0032 + 0033 + 0034). Voraussetzung erfuellt:
  Welle 6a (Cross-Adapter-OTel-Span-Wrap) wrappt auch
  IEC-61850 ohne Adapter-Code-Diff; Welle 6b (Lizenz-
  Smoke-Hardening) hat die GPL-Boundary-Decision I-f
  per zwei Static-Checks gehaertet (`make spdx-check` als
  10. A-1-Gate + `AC-IEC61850-GPL-BOUNDARY` als 14.
  arch_check-Contract) + NEU `CONTRIBUTING.md` mit Dual-
  License-Policy. IedServer-Smoke-Reaktivierung bleibt
  unter 2c-Mock-only-Fallback mit Trigger 009 (Welle-6b-
  C3-Pfad-A-Probe-Run-Befund: pyiec61850-ng 1.6.1.2
  identisch zu Welle-5b-Stand, kein cp314-Manylinux-
  Wheel).
  Folge-Pflicht: M4-Welle-7-Closure schaerft ADR 0030
  §2.4 (Welle-1-IEC-61850-Verzicht-Default) auf „durch
  Welle-5a-Spike-Lieferung (DNP3) **und** Welle-5b-
  Spike-Lieferung (IEC-61850) aufgeloest" (Pattern
  ADR 0011).
