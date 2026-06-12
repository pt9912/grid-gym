# Adapter-Profil-Index

Kanonischer Index aller `DeviceProtocolPort`-Implementer
(`GG-AR-PORT-DRN-007`) mit Verweisen auf Lastenheft-Cluster,
Adapter-ADRs, Welle-Lieferung und DoD-Belege.

**Geltungsbereich:** M4-Welle 2 bis Welle 5b (5 Adapter-
Pakete unter `src/grid_gym/adapters/driven/protocol_*/`).
Pattern-Praezedenz: jedes Profil ist inline im
`protocol_ports`-Block des Scenario-YAML konfigurierbar
(Decision-Praezedenz [`ADR 0031`](../docs/plan/adr/0031-mqtt-adapter-profile.md) §2.1 bis [`ADR 0035`](../docs/plan/adr/0035-iec61850-adapter-profile.md) §2.1).

**Stand:** 2026-06-01 (M4-Welle-6a-C1).

---

## Profil-Index-Tabelle

| Adapter         | ADR                                                                  | Status       | Lastenheft-Cluster | M4-Welle | DoD-Beleg                                                                                                                |
| --------------- | -------------------------------------------------------------------- | ------------ | ------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------ |
| **MQTT**        | [`ADR 0031`](../docs/plan/adr/0031-mqtt-adapter-profile.md)         | Provisional  | `GG-MQTT-001`      | Welle 2  | [`done/M4-welle-2.md`](../docs/plan/planning/done/M4-welle-2.md)                                                       |
| **Modbus-TCP**  | [`ADR 0032`](../docs/plan/adr/0032-modbus-adapter-profile.md)       | Provisional  | `GG-MODB-001`      | Welle 3  | [`done/M4-welle-3.md`](../docs/plan/planning/done/M4-welle-3.md) + [Slice 031](../docs/plan/planning/done/031-modbus-adapter-review-folge.md) |
| **OPC-UA**      | [`ADR 0033`](../docs/plan/adr/0033-opcua-adapter-profile.md)        | Provisional  | `GG-OPCUA-001`     | Welle 4  | [`done/M4-welle-4.md`](../docs/plan/planning/done/M4-welle-4.md) + [Slice 032](../docs/plan/planning/done/032-opcua-adapter-review-folge.md)  |
| **DNP3**        | [`ADR 0034`](../docs/plan/adr/0034-dnp3-adapter-profile.md)         | Provisional  | `GG-DNP3-001`      | Welle 5a | [`done/M4-welle-5a.md`](../docs/plan/planning/done/M4-welle-5a.md)                                                     |
| **IEC-61850**   | [`ADR 0035`](../docs/plan/adr/0035-iec61850-adapter-profile.md)     | Provisional  | `GG-IEC-001`       | Welle 5b | [`done/M4-welle-5b.md`](../docs/plan/planning/done/M4-welle-5b.md) + [Slice 033](../docs/plan/planning/done/033-iec61850-adapter-review-folge.md) |

**Status-Pfad:** Alle 5 ADRs sind aktuell `Provisional`. Die
geplante M4-Welle-7-Closure schaerft alle 5 auf `Accepted`
(siehe [M4-Slice-Plan](../docs/plan/planning/done/M4-protocol-adapters.md)
§3 Welle 7).

---

## MQTT — `protocol_mqtt`

**Lastenheft:** `GG-MQTT-001` (SOLLTE-Pflicht erfuellt mit
M4-Welle 2).
**ADR:** [0031 MQTT-Adapter-Profile](../docs/plan/adr/0031-mqtt-adapter-profile.md).
**Library:** `paho-mqtt>=2.0` (PyPI, EPL-2.0/EDL-1.0, Python-3
native, mit CallbackAPIVersion.VERSION2).
**Surface:** Pub/Sub via TCP zu Mosquitto-aequivalenten
Brokern.

| Profil-Item               | Decision                       | Welle-2-Wert                                                  |
| ------------------------- | ------------------------------ | ------------------------------------------------------------- |
| Topic-Schema              | Decision 4a (inline)           | `topics.<device_id>` mit `read`/`write`-Sub-Felder            |
| Payload-Codec             | Decision 4b                    | `canonical_json` (Trigger 004 fuer `orjson`/`msgspec`-Re-Eval) |
| QoS-Defaults              | Decision 4c                    | `QoS 0` Telemetry-Publish, `QoS 1` Command-Publish + Subscribe |
| Async-Bridge              | Decision 4d                    | Per-Target `queue.Queue` mit Lazy-Init in paho-`on_message`   |
| Test-Sibling              | M4-Welle-2-DoD                 | Mosquitto-Container (`testcontainers`-spawn; EPL-2.0/EDL-1.0)   |
| Write-Pfad                | (produktiv)                    | `client.publish()` direkt; QoS 1 garantiert Acknowledgement   |

**Anti-Scope:** kein TLS-/MQTT-5-Subset; bleibt M5/M6-
Schaerfung.

---

## Modbus-TCP — `protocol_modbus`

**Lastenheft:** `GG-MODB-001` (SOLLTE-Pflicht erfuellt mit
M4-Welle 3 + Review-Folge Slice 031).
**ADR:** [0032 Modbus-TCP-Adapter-Profile](../docs/plan/adr/0032-modbus-adapter-profile.md).
**Library:** `pymodbus>=3.6,<4.0` (PyPI, BSD-3-Clause,
Pure-Python, sync-Client + in-process-Server).
**Surface:** Function-Code-basierte Register-Reads/Writes
gegen Modbus-TCP-Slaves.

| Profil-Item               | Decision                       | Welle-3-Wert                                                  |
| ------------------------- | ------------------------------ | ------------------------------------------------------------- |
| Register-Schema           | Decision M-a (inline)          | `registers.<device_id>` mit `address`/`datatype`/`fc`/`access` |
| Datatype-Set              | Decision M-d                   | `{int16, uint16, int32, uint32, float32}` (5 Typen)            |
| Async-Bridge              | Decision M-c                   | **direkt-sync** (pymodbus ist sync-by-design)                  |
| Function-Code-Mapping     | Decision M-e                   | FC03 Read + FC10 Write Default; FC04/FC06 per Target-Override |
| Slave-Unit-ID             | Decision M-f                   | Per-Target via `Iec61850LnConfig.slave_unit_id`                |
| Test-Sibling              | M4-Welle-3-DoD                 | In-process pymodbus-Server (Daemon-Thread)                     |
| Write-Pfad                | (produktiv)                    | FC10/FC06 mit Multi-Register-Guard fuer FC06 (Slice 031)       |

**Slice 031** (M4-Welle-3-Review-Folge): FC06-Multi-
Register-Guard fail-fast, Read-/Write-Fehler-Taxonomie
operation-spezifisch, Codec-/Payload-Fehler am Adapter-Rand
in `DeviceProtocolPort*Error` uebersetzt.

**Anti-Scope:** kein Modbus-RTU / Modbus-ASCII (Welle 6+);
kein TLS (Welle 6 oder M6).

---

## OPC-UA — `protocol_opcua`

**Lastenheft:** `GG-OPCUA-001` (SOLLTE-Pflicht erfuellt mit
M4-Welle 4 + Review-Folge Slice 032).
**ADR:** [0033 OPC-UA-Adapter-Profile](../docs/plan/adr/0033-opcua-adapter-profile.md).
**Library:** `asyncua>=1.2b2,<2.0` (PyPI, LGPL-3.0, asyncio-
native, mit Python-3.14-Forward-Reference-Fix der in
1.1.8 fehlt).
**Surface:** OPC-UA-Client mit Node-ID-Read/Write.

| Profil-Item               | Decision                       | Welle-4-Wert                                                  |
| ------------------------- | ------------------------------ | ------------------------------------------------------------- |
| Node-ID-Schema            | Decision O-a (inline)          | `nodes.<device_id>` mit `node_id`/`datatype`/`access`         |
| Datatype-Set              | Decision O-c                   | `{Boolean, Int16, UInt16, Int32, UInt32, Float, Double, String}` (8 Typen) |
| Async-Bridge              | Decision O-b                   | **eigener `OpcuaLoopThread`** — asyncio-Loop in Daemon-Thread; **erstes Repo-Pattern dieser Art** |
| Read-Pfad                 | Decision O-d                   | Polling-Read (Subscription Welle-6+)                          |
| Test-Sibling              | Decision O-e                   | In-process `asyncua.Server` (LGPL-3.0; eigener Loop-Thread)   |
| Write-Pfad                | (produktiv)                    | Direct-Write per Node-ID                                       |

**Slice 032** (M4-Welle-4-Review-Folge): 6 HIGH + 11 MEDIUM
Findings — Lifecycle-Lock im `OpcuaLoopThread`, Start-
Timeout, Port-Exception-Filter um `RuntimeError`/
`CancelledError`, `Quality.INVALID`-String-Read,
Float32-Quantisierung, `asyncio.Event`-Stop-Signal in
Smoke-Server.

**Anti-Scope:** keine OPC-UA-Security (Anonymous-Endpoint;
Welle 6 oder M6); keine Subscription (Welle-6-Schaerfung
via separate ADR).

---

## DNP3 — `protocol_dnp3`

**Lastenheft:** `GG-DNP3-001` (SOLLTE-Pflicht erfuellt mit
M4-Welle 5a — Spike-Lieferung).
**ADR:** [0034 DNP3-Adapter-Profile](../docs/plan/adr/0034-dnp3-adapter-profile.md).
**Library:** `nfm-dnp3>=1.0,<2.0` (PyPI, MIT, Pure-Python,
sync API mit Thread-Lock-Schutz) **als Master**;
`dnp3-outstation>=0.2,<1.0` (PyPI, MIT, Pure-Python,
asyncio-native) **nur als Test-Sibling** in
`[dependency-groups.dev]`.
**Surface:** DNP3-Master mit Class-0-Polling-Read.

| Profil-Item               | Decision                       | Welle-5a-Wert                                                 |
| ------------------------- | ------------------------------ | ------------------------------------------------------------- |
| Point-Schema              | Decision D-a (inline)          | `points.<device_id>` mit `group`/`variation`/`index`/`access` |
| Group/Variation-Set       | Decision D-c                   | `{(1,1), (1,2), (30,1), (30,5)}` — Binary-Inputs + 32-bit Int/Float Analog-Inputs |
| Async-Bridge              | Decision D-b                   | **direkt-sync** (nfm-dnp3 sync; Pattern-Praezedenz Welle-3-M-c) |
| Read-Pfad                 | Decision D-d                   | Class-0-Integrity-Poll mit Resultat-Filter-by-Index           |
| Test-Sibling              | Decision D-e                   | In-process `dnp3_outstation.AsyncOutstation` (Daemon-Thread + asyncio-Loop) |
| Write-Pfad                | (Welle-5a-Anti-Scope)          | `Dnp3PortWriteNotImplementedError`; Welle-6-Schaerfung        |

**C2-Library-Bug-Find:** `nfm-dnp3.AnalogInput.__repr__`
zeigt `idx=0`, das tatsaechliche Attribut heisst aber
`.index` — `_port._find_point` benutzt `getattr(point,
"index", None)`.

**Anti-Scope:** kein Event-Class-Polling (Class 1/2/3,
Welle-6-Schaerfung); keine DNP3-Security (IEEE 1815-2012
§10, Welle 6 oder M6).

---

## IEC-61850 — `protocol_iec61850` (**GPL-isoliert**)

**Lastenheft:** `GG-IEC-001` (SOLLTE-Pflicht erfuellt mit
M4-Welle 5b — Spike-Lieferung + Slice 033 Review-Folge).
**ADR:** [0035 IEC-61850-Adapter-Profile](../docs/plan/adr/0035-iec61850-adapter-profile.md).
**Library:** `pyiec61850-ng>=1.6,<2.0` (PyPI, **GPLv3**,
Beta `Development Status :: 4`, SWIG-Bindings zu libiec61850
1.6 + Mbed TLS Apache 2.0; manylinux1_x86_64 + Windows-
Wheels). **Optionales Extra** via `pip install grid-gym[iec61850]`.
**Surface:** MMS-Client mit Per-Target `read_value(reference, fc)`.

| Profil-Item               | Decision                       | Welle-5b-Wert                                                 |
| ------------------------- | ------------------------------ | ------------------------------------------------------------- |
| LN/CDC-Schema             | Decision I-a (inline)          | `points.<device_id>` mit `object_reference` (LD/LN.DO.DA) / `functional_constraint` / `datatype` / `access` |
| Datatype-Set + FC-Mapping | Decision I-c                   | `{bool, int32, float, string}` × FC `{MX, ST, SP, CF, DC}` — Adapter-Default FC `MX` |
| Async-Bridge              | Decision I-b                   | **direkt-sync** (pyiec61850-ng MMSClient ist sync-Context-Manager; Pattern-Praezedenz Welle-3-M-c + Welle-5a-D-b) |
| Read-Pfad                 | Decision I-d                   | Per-Target `MMSClient.read_value(reference, fc)`              |
| Test-Sibling              | Decision I-e                   | In-process `pyiec61850.server.IedServer(model_path=fixture)` (libiec61850-natives CFG-Format); **aktuell 2c-Mock-only-Fallback** wegen Python-3.14-SWIG-Inkompat — Welle-6b reaktiviert |
| Write-Pfad                | (Welle-5b-Anti-Scope)          | `Iec61850PortWriteNotImplementedError`; bei Config-Konstruktion bereits abgelehnt (Slice 033) |
| **Lizenz-Boundary**       | **NEU Decision I-f**           | GPLv3-Isolation per SPDX-Header pro Datei (`# SPDX-License-Identifier: GPL-3.0-only`); `LICENSES/GPL-3.0.txt` + LICENSE-Hinweis-Block + READMEs-Sektion; **erstmaliger Repo-Praezedenzfall** fuer GPL-isolierte Sub-Module in einem sonst MIT-Projekt |

**Slice 033** (M4-Welle-5b-C2-Review-Folge): 15 Findings
(10 HIGH + 5 MEDIUM) — Sentinel-Exception-Klasse statt
`Exception`-Alias im Optional-Extra-Off-Pfad, `_PyIecMMSError`-
Catch-All in `start()`, `stop()`-State-Mutation NACH
`disconnect()`, NaN/Inf-Reject + int-Reject in
`_decode_float`, Container-Check gated auf non-string,
NEU `Iec61850PortReadConnectionLostError` fuer mid-flight-
NotConnected, Config-Anti-Scope-write-Reject bei Konstruktion,
`TelemetryPoint.value`-Decimal-Wrap mit `Quality.INVALID`-
String-Fallback, Sub-Millisekunden-Timeout-Floor, Dockerfile-
`build-app`-Stage `--extra iec61850`-Propagation,
`simpleIO.cfg`-SPDX-Header + Derivative-Work-Attribution,
`pyproject.toml`-GPL-Classifier.

**Anti-Scope:** kein RCB-Subscription (Welle-6+); kein
GOOSE-Publishing/Subscription (Welle-6+); keine Sampled-
Values (Welle-6 oder M6); keine IEC-61850-Security (TLS/
IEC-62351; Welle 6 oder M6); kein aarch64-Wheel-Support
(piwheels-Lage; Welle-6 falls Bedarf); kein Anschluss von
`pyiec61850.{tase2,sv,goose}`-Submodulen.

---

## Cross-Adapter-Patterns

Alle 5 Adapter teilen ueber `DeviceProtocolPort`
(`GG-AR-PORT-DRN-007`) folgende Eigenschaften:

1. **Sync-Vertrag** ([`ADR 0030`](../docs/plan/adr/0030-device-protocol-port-surface.md) §2.1): `start()`/`stop()`/
   `read(target)`/`write(target, command)` sind alle sync;
   keine async-Surface am Port.
2. **Caller-Scope-Lifecycle** ([`ADR 0030`](../docs/plan/adr/0030-device-protocol-port-surface.md) §2.2): TickLoop
   ruft `start_protocol_ports()` (FIFO) und
   `stop_protocol_ports()` (LIFO) mit Best-Effort-Partial-
   Cleanup via `__context__`-Chain.
3. **Stateless aus Replay-Sicht** ([`ADR 0030`](../docs/plan/adr/0030-device-protocol-port-surface.md) §2.3):
   Reconnect-State, Session-State, IIN-Restart-Flag etc.
   sind volatile; Snapshot-Schema bleibt v2 in M4.
4. **Inline-Profile-Pattern** ([`ADR 0031`](../docs/plan/adr/0031-mqtt-adapter-profile.md)..0035 §2.1): jedes
   Adapter-Profil ist inline im `protocol_ports`-Block des
   Scenario-YAML konfiguriert; kein separates
   `<adapter>_profiles`-Top-Level (YAGNI).
5. **Typed Errors** mit operation-spezifischer Taxonomie
   (Slice 031-Pattern, Welle-3+): Read-/Write-/Connect-/
   Disconnect-Subclasses haengen am passenden
   `DeviceProtocolPortReadError`/`-WriteError`/
   `-StartError`/`-StopError`-Vertrag.

### Welle-6a-Folge (Cross-Adapter-Hardening)

Welle 6a haertet diese Pattern-Decisions:

1. **OTel-Span-Wrap** ([`ADR 0024`](../docs/plan/adr/0024-observability-port-trio.md) §4.5 Forward-Pointer) —
   jeder `read(target)`/`write(target, command)`-Call wird
   in einen TracePort-Span umschlossen mit Standard-
   Attributen `adapter_type`/`target`/`reference`/
   `operation`/`latency_ms`. Welle-6a-C2 implementiert das
   fuer alle 5 Adapter via Decorator-/Composition-/Welle-1-
   Factory-Hook-Pattern.
2. **`AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-Property-
   Test** (Welle-1-§7-Folge-Pflicht) — Welle-6a-C3 zieht
   den Test produktiv ein.
3. **`tools/check_refs.py`** verifiziert die Markdown-
   Konsistenz zwischen `spec/protocol_profiles.md` (diesem
   Index) und den 5 Adapter-ADRs.

---

## Welle-7-Closure

**M4-Welle-7** (Closure-Welle) schaerft alle 5 Adapter-ADRs
von `Provisional` auf `Accepted` und erzeugt
`done/M4-results.md` mit der Cross-Adapter-Welle-Tabelle
(C0/C1/C2/C3-Hashes pro Welle, Test-Counts, Coverage,
Contracts, Per-Welle-Reviews).

**[`ADR 0030`](../docs/plan/adr/0030-device-protocol-port-surface.md) §2.4** (Welle-1-DNP3/IEC-Verzicht-Default) wird
mit Welle-7-Closure auf „durch Welle-5a (DNP3) **und**
Welle-5b (IEC-61850) aufgeloest" geschaerft (Pattern
[`ADR 0011`](../docs/plan/adr/0011-schaerfung-ohne-abloesung.md)).
