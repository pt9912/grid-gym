# Adapter-Profil-Index

**Projektname:** grid-gym
**Dokumenttyp:** Protokoll-Adapter-Profile
**Format:** Markdown
**Version:** 0.1.0
**Bezug:** [`lastenheft.md`](lastenheft.md)

---

Verbindliche Protokoll-Profile der fuenf `DeviceProtocolPort`-Adapter
(MQTT, Modbus-TCP, OPC-UA, DNP3, IEC-61850): je Adapter die Surface, das
Profil-Schema und die Konfiguration. Jedes Profil ist inline im
`protocol_ports`-Block des Scenario-YAML konfigurierbar. Bibliotheks-/
Implementierungswahl traegt die Sektion [Bibliothekswahl](#bibliothekswahl);
die Entscheidungs-Provenance (Profil-ADR, Lieferung, Review-Folgen, Status)
lebt in den jeweiligen Adapter-ADRs und im ADR-Index.

Die **driving-seitigen Server-/Outstation-Profile** (`DeviceServerPort`,
Field-Server — grid-gym als Feldbus-Server fuer ein externes EMS) fuehrt die
eigene Sektion **Server-Profile** unten; sie sind bewusst **getrennt** vom
driven-Master-Index oben (andere Rolle: bind/listen/serve statt connect/poll).

---

## Profil-Index-Tabelle

| Adapter | Lastenheft-Cluster |
| --- | --- |
| **MQTT** (`protocol_mqtt`) | [`GG-MQTT-001`](lastenheft.md#gg-mqtt-001) |
| **Modbus-TCP** (`protocol_modbus`) | [`GG-MODB-001`](lastenheft.md#gg-modb-001) |
| **OPC-UA** (`protocol_opcua`) | [`GG-OPCUA-001`](lastenheft.md#gg-opcua-001) |
| **DNP3** (`protocol_dnp3`) | [`GG-DNP3-001`](lastenheft.md#gg-dnp3-001) |
| **IEC-61850** (`protocol_iec61850`) | [`GG-IEC-001`](lastenheft.md#gg-iec-001) |

---

## MQTT — `protocol_mqtt`

**Lastenheft:** [`GG-MQTT-001`](lastenheft.md#gg-mqtt-001).
**Surface:** Pub/Sub via TCP zu Mosquitto-aequivalenten
Brokern.

| Profil-Item               | Wert                                                          |
| ------------------------- | ------------------------------------------------------------- |
| Topic-Schema              | `topics.<device_id>` mit `read`/`write`-Sub-Felder            |
| Payload-Codec             | `canonical_json`                                              |
| QoS-Defaults              | `QoS 0` Telemetry-Publish, `QoS 1` Command-Publish + Subscribe |
| Async-Bridge              | Per-Target `queue.Queue` mit Lazy-Init in paho-`on_message`   |
| Write-Pfad                | `client.publish()` direkt; QoS 1 garantiert Acknowledgement   |

**Anti-Scope:** kein TLS-/MQTT-5-Subset.

---

## Modbus-TCP — `protocol_modbus`

**Lastenheft:** [`GG-MODB-001`](lastenheft.md#gg-modb-001).
**Surface:** Function-Code-basierte Register-Reads/Writes
gegen Modbus-TCP-Slaves.

| Profil-Item               | Wert                                                          |
| ------------------------- | ------------------------------------------------------------- |
| Register-Schema           | `registers.<device_id>` mit `address`/`datatype`/`fc`/`access` |
| Datatype-Set              | `{int16, uint16, int32, uint32, float32}` (5 Typen)            |
| Async-Bridge              | **direkt-sync**                  |
| Function-Code-Mapping     | FC03 Read + FC10 Write Default; FC04/FC06 per Target-Override |
| Slave-Unit-ID             | Per-Target via `Iec61850LnConfig.slave_unit_id`                |
| Write-Pfad                | FC10/FC06 mit Multi-Register-Guard fuer FC06                  |

**Anti-Scope:** kein Modbus-RTU / Modbus-ASCII; kein TLS.

---

## OPC-UA — `protocol_opcua`

**Lastenheft:** [`GG-OPCUA-001`](lastenheft.md#gg-opcua-001).
**Surface:** OPC-UA-Client mit Node-ID-Read/Write.

| Profil-Item               | Wert                                                          |
| ------------------------- | ------------------------------------------------------------- |
| Node-ID-Schema            | `nodes.<device_id>` mit `node_id`/`datatype`/`access`         |
| Datatype-Set              | `{Boolean, Int16, UInt16, Int32, UInt32, Float, Double, String}` (8 Typen) |
| Async-Bridge              | asyncio-Loop-Bridge in Daemon-Thread (`OpcuaLoopThread`) |
| Read-Pfad                 | Polling-Read (Subscription out-of-scope)                     |
| Write-Pfad                | Direct-Write per Node-ID                                       |

**Anti-Scope:** keine OPC-UA-Security (Anonymous-Endpoint);
keine Subscription (Folge-Schaerfung via separate ADR).

---

## DNP3 — `protocol_dnp3`

**Lastenheft:** [`GG-DNP3-001`](lastenheft.md#gg-dnp3-001).
**Surface:** DNP3-Master mit Class-0-Polling-Read.

| Profil-Item               | Wert                                                         |
| ------------------------- | ------------------------------------------------------------- |
| Point-Schema              | `points.<device_id>` mit `group`/`variation`/`index`/`access` |
| Group/Variation-Set       | `{(1,1), (1,2), (30,1), (30,5)}` — Binary-Inputs + 32-bit Int/Float Analog-Inputs |
| Async-Bridge              | **direkt-sync**                               |
| Read-Pfad                 | Class-0-Integrity-Poll mit Resultat-Filter-by-Index           |
| Write-Pfad                | `Dnp3PortWriteNotImplementedError` (Anti-Scope)              |

**Anti-Scope:** kein Event-Class-Polling (Class 1/2/3);
keine DNP3-Security (IEEE 1815-2012 §10).

---

## IEC-61850 — `protocol_iec61850` (**GPL-isoliert**)

**Lastenheft:** [`GG-IEC-001`](lastenheft.md#gg-iec-001).
**Surface:** MMS-Client mit Per-Target `read_value(reference, fc)`.

| Profil-Item               | Wert                                                         |
| ------------------------- | ------------------------------------------------------------- |
| LN/CDC-Schema             | `points.<device_id>` mit `object_reference` (LD/LN.DO.DA) / `functional_constraint` / `datatype` / `access` |
| Datatype-Set + FC-Mapping | `{bool, int32, float, string}` × FC `{MX, ST, SP, CF, DC}` — Adapter-Default FC `MX` |
| Async-Bridge              | **direkt-sync** |
| Read-Pfad                 | Per-Target `MMSClient.read_value(reference, fc)`              |
| Write-Pfad                | `Iec61850PortWriteNotImplementedError` (Anti-Scope); bei Config-Konstruktion bereits abgelehnt |
| **Lizenz-Boundary**       | GPLv3-Isolation per SPDX-Header pro Datei (`# SPDX-License-Identifier: GPL-3.0-only`); `LICENSES/GPL-3.0.txt` + LICENSE-Hinweis-Block + READMEs-Sektion |

**Anti-Scope:** kein RCB-Subscription; kein
GOOSE-Publishing/Subscription; keine Sampled-
Values; keine IEC-61850-Security (TLS/IEC-62351);
kein aarch64-Wheel-Support (piwheels-Lage); kein Anschluss von
`pyiec61850.{tase2,sv,goose}`-Submodulen.

---

## Server-Profile — `DeviceServerPort` (Field-Server, driving)

Die **driving-seitige Server-/Outstation-Rolle** der Field-Server-Surface:
grid-gym exponiert seine **simulierten** Geraete als Feldbus-Server, damit ein
externes EMS (System-under-Test, z. B. `bess-ems`) sie als Master **pollt**
(HIL-Konkretisierung von [`GG-TEST-004`](lastenheft.md#gg-test-004)). Eigenes
Profil-Set — **nicht** Teil des driven-Master-Index oben. Simulation only; keine
produktive Anlagensteuerung; **Nur-Sim-Netz** (kein Auth/TLS). Provenance
(Field-Server-ADR + liefernde Slices): ADR-Index.

### Modbus-Server — `device_server_modbus` (Read-Serving)

**Surface:** `DeviceServerPort` (bind/listen/serve); ein externer Modbus-**Master**
pollt Holding-/Input-Register, die grid-gym aus der **Current-Value-Projektion**
(letzter emittierter Wert pro `(device_id, metric)`, tick-frame-atomar) fuellt.

| Profil-Item        | Wert                                                                 |
| ------------------ | -------------------------------------------------------------------- |
| Rolle              | Modbus-TCP-**Server/Slave** (Gegenrolle zu `protocol_modbus`-Master) |
| Register-Map       | `(device_id, metric)` → Start-Adresse, deterministisch sortiert      |
| Register-Datatype  | **`float32`** (2 Register, Big-Endian) — Default fuer fraktionale Telemetrie |
| Quality-Mapping    | `Quality` → Discrete-Input je `(device_id, metric)` (`VALID`=1; sonst 0) |
| Read-Pfad          | FC03 (Holding) / FC04 (Input), **Read-only** — kein Write/Inbound in 074 |
| Unit-ID            | ein Slave-Kontext, Unit-ID konfigurierbar (Default 1)                |
| Lifecycle          | bind/listen im adapter-internen Loop-Thread; Bind-in-use = harter Fehler |

**Encode + Gleichheits-Oracle** (Review-Fund): der Domaenen-`Decimal`-Wert wird
als `float32` kodiert (`Decimal` → `float` → IEEE-754-`float32`, 2 Register).
Beide Schritte sind verlustbehaftet, **aber deterministisch** — der E2E-Oracle
vergleicht darum **nicht** `Decimal == decoded`, sondern gegen die reproduzierbare
`float32`-Quantisierung: `erwartet = struct.unpack(">f", struct.pack(">f",
float(wert)))[0]` und `decoded_register_float == erwartet` (exakt, kein
Toleranz-Fudge). Die Genauigkeitsgrenze ist damit explizit (`float32` ~7
signifikante Stellen); Werte mit mehr Praezision ([`GG-DATA-005`](lastenheft.md#gg-data-005):
max. 6 Nachkommastellen) oder ausserhalb des `float32`-Bereichs verlieren
Genauigkeit — bewusste Grenze; ein scaled-`int32`-Encode (exakt fuer die
6-Dezimalstellen-Quantisierung, aber range-limitiert) ist Folge-Option.

**Anti-Scope (Slice 074):** kein Write/Inbound (Folge-Slice), kein
Modbus-RTU/ASCII, kein TLS, kein Multi-Unit-Fan-out.

---

## Cross-Adapter-Patterns

Alle 5 Adapter teilen ueber `DeviceProtocolPort`
folgende Eigenschaften:

1. **Sync-Vertrag:** `start()`/`stop()`/
   `read(target)`/`write(target, command)` sind alle sync;
   keine async-Surface am Port.
2. **Caller-Scope-Lifecycle:** TickLoop
   ruft `start_protocol_ports()` (FIFO) und
   `stop_protocol_ports()` (LIFO) mit Best-Effort-Partial-
   Cleanup via `__context__`-Chain.
3. **Stateless aus Replay-Sicht:**
   Reconnect-State, Session-State, IIN-Restart-Flag etc.
   sind volatile; das Snapshot-Schema traegt sie nicht.
4. **Inline-Profile-Pattern:** jedes
   Adapter-Profil ist inline im `protocol_ports`-Block des
   Scenario-YAML konfiguriert; kein separates
   `<adapter>_profiles`-Top-Level (YAGNI).
5. **Typed Errors** mit operation-spezifischer Taxonomie:
   Read-/Write-/Connect-/Disconnect-Subclasses haengen am
   passenden `DeviceProtocolPortReadError`/`-WriteError`/
   `-StartError`/`-StopError`-Vertrag.

### Cross-Adapter-Hardening

Zusaetzliche, fuer alle 5 Adapter geltende Haertung:

1. **OTel-Span-Wrap** — jeder `read(target)`/`write(target, command)`-Call
   wird in einen TracePort-Span umschlossen mit Standard-Attributen
   `adapter_type`/`target`/`reference`/`operation`/`latency_ms`.

---

## Bibliothekswahl

MQTT `paho-mqtt>=2.0` (EPL-2.0/EDL-1.0); Modbus-TCP `pymodbus>=3.6,<4.0`
(BSD-3-Clause); OPC-UA `asyncua>=1.2b2,<2.0` (LGPL-3.0); DNP3
`nfm-dnp3>=1.0,<2.0` (MIT, Master) + `dnp3-outstation>=0.2,<1.0`
(MIT, Test-Sibling); IEC-61850 `pyiec61850-ng>=1.6,<2.0` (GPLv3, optionales
Extra `grid-gym[iec61850]`).

**DNP3/IEC-Verzicht-Default:** der urspruengliche Verzicht ist durch die
Lieferung von DNP3 (M4) und IEC-61850 (M4) aufgeloest.
