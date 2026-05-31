# ADR 0032 — Modbus-TCP-Adapter-Profile (M4 Welle 3)

**Status:** Provisional — geschaerft 2026-05-30 mit M4-Welle-3-C3
(`docs(plan|adr)` Doc-Sync). Review-Folge 2026-05-31:
Welle-3-Smoke-Abdeckung praezisiert, FC06-Multi-Register-
Guard und Read-/Write-Fehler-Taxonomie in
[`done/031`](../planning/done/031-modbus-adapter-review-folge.md)
umgesetzt. Initial-Entwurf
(`Proposed`) 2026-05-30 mit M4-Welle-3-C1 `a86ac46`; C2-Merge
`d721982` (feat `protocol_modbus/`-5-Modul-Paket + 95 neue
Unit-Tests + in-process pymodbus-Server-Integration-Smoke +
`pyproject.toml`/`Dockerfile`/`compose.yml`-Edits; `make
test-unit` 1306 gruen, `make test-integration` 23 gruen,
`make arch-check` 19/19 KEPT, `make gates` cache-frei gruen
ohne `CRITICAL_COV_TARGETS`-Override) belegt die Decisions
M-a/M-b/M-c/M-d/M-e/M-f produktiv. Status-Pfad:
`Proposed → Provisional` (mit C3) → `Accepted`
(M4-Welle-7-Closure analog ADR 0022..0027 + 0030 + 0031).
**Datum:** 2026-05-30
**Bezug:**
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md)
(Schaerfungs-ohne-Supersede-Pattern — ADR 0032 schaerft
ADR 0030 §2.1 und ADR 0031 §2.1 konkret fuer Modbus, ohne
den Sync-`DeviceProtocolPort`-Vertrag oder die inline-
Profile-Praezedenz zu ersetzen),
[`ADR 0030`](0030-device-protocol-port-surface.md) §2.1
(Sync-`Protocol`-Vertrag; `pymodbus 3.x`-`ModbusTcpClient`
ist sync-by-design und passt damit **direkt** in die
Sync-`DeviceProtocolPort`-Surface — **kein** Adapter-
interner Thread+Queue-Marshal noetig, anders als bei MQTT
[ADR 0031 §2.4] und der angekuendigten OPC-UA-Welle 4
[`asyncua`, ADR 0030 §2.1-Konsequenz]) + §2.2 (Caller-
Scope-Lifecycle) + §2.3 (stateless aus Replay-Sicht —
Modbus-Reconnect-State ist volatile, kein Snapshot-Bump
in Welle 3),
[`ADR 0031`](0031-mqtt-adapter-profile.md) §2.1
(Decision 4a inline-Profile-Pattern — ADR 0032 uebernimmt
das Pattern direkt fuer Register-Schema; siehe §2.1 unten)
+ §2.2 (Decision 4b `canonical_json`-Codec — ADR 0032
**weicht ab**: Modbus benutzt `struct.pack`/`struct.unpack`
direkt auf Register-Bytes, kein JSON-Layer; siehe §2.2
unten) + §2.4 (Decision 4d Per-Target Queue-Marshal —
**nicht** reusable; siehe §2.3 unten),
[`ADR 0014`](0014-battery-snapshot-schema.md)
(Pattern-Praezedenz fuer Datentyp-Konvertierung am Adapter-
Rand: Battery-Snapshot-Codec verwendet ebenfalls
`struct`-aehnliche Asymmetrie — Adapter-Rand-Validation
ist strikt, Roundtrip ist tolerant),
[`ADR 0024`](0024-observability-port-trio.md) §4.5
(OTLP-Adapter-Praezedenz fuer Welle-6-Span-Wrap-Forward-
Pointer — Welle 3 wrappt **noch keine** Adapter-Calls).
M4-Slice-Plan
[`in-progress/M4-protocol-adapters.md`](../planning/in-progress/M4-protocol-adapters.md)
§3 Welle 3; M4-Welle-0-Decision-Liste
[`done/M4-welle-0.md`](../planning/done/M4-welle-0.md) §3
Decision 4 (Profile-Deklaration) + Decision 5
(Test-Sibling-Container — **Modbus-Container-Lizenz-
Risiko explizit dokumentiert**) + Decision 6
(`AC-ADAPTER-LIGHTWEIGHT`-Pfad-Filter).
Lastenheft §16 (`GG-MODB-001`, Z. 1134–1148 SOLLTE-Cluster:
Register-Mapping + Datentypen + Byte-Reihenfolge + Read/
Write-Operationen + Timeout-Verhalten + deterministischer
Adapter-Smoke-Test).
Architektur §7 (`GG-AR-PORT-DRN-007` Driven-Ports-Tabelle —
ADR 0030 hat den Slot belegt; Welle 3 liefert zweiten
Implementer) + §8.2 (Adapter-Interfaces-Driven-Beschreibung
— Register-Schema konkretisiert die generische
Beschreibung) + §16 (Deployment-Sicht — `protocol_modbus`-
Adapter lebt im `simulation`-Worker, kein eigener Compose-
Service; **kein** Test-Sibling-Service in
`tests/integration/compose.yml`, weil Welle 3 explizit
in-process testet).
M3-Welle-6c-Postgres-Sibling-Pattern + M4-Welle-2-
Mosquitto-Sibling-Pattern als Praezedenz fuer Sibling-
im-Test; **Welle 3 weicht bewusst ab** (siehe §2.6
Decision M-f).
Trigger 006
[`open/006`](../planning/open/006-mypy-strict-bytes.md)
(`mypy --strict-bytes`) — Modbus ist die erste produktive
`bytes`/`int`/`float`-Konvertierungs-Stelle im Repo;
C3-Re-Eval folgt mit konkretem Code-Beleg.

---

## 1. Kontext

`GG-MODB-001` (Lastenheft §16 Z. 1134–1148) verlangt einen
Modbus-TCP-Adapter als **Simulations-/Testadapter** mit
deterministischem Adapter-Smoke-Test (mindestens ein Read-
und ein Write-Pfad). M4-Welle-2 hat den ersten konkreten
Implementer (`MqttDeviceProtocolPort`, ADR 0031
`Provisional`) produktiv geliefert; Welle 3 liefert den
zweiten: `ModbusDeviceProtocolPort` unter
`src/grid_gym/adapters/driven/protocol_modbus/` ueber
`pymodbus 3.x`.

ADR 0030 hat den **Sync-Vertrag** und den **Caller-Scope-
Lifecycle** finalisiert. ADR 0031 hat das **inline-im-
`protocol_ports`-Block**-Profile-Pattern etabliert. ADR
0032 schaerft die fuer den Modbus-Adapter notwendigen
Sub-Entscheidungen **konkret**:

- **Decision M-a (Register-Schema)** — wo und wie werden
  Device-ID → Register-Adresse-Mappings deklariert?
- **Decision M-b (Datatype + Byte/Word-Order)** — welche
  Datentypen sind in Welle 3 unterstuetzt, und welche
  Byte/Word-Order-Defaults gelten?
- **Decision M-c (Polling-Pattern)** — wie wird die
  Sync-Surface bedient, ohne Background-Thread?
- **Decision M-d (Function-Code-Mapping)** — welche
  Modbus-Function-Codes greifen pro Default-Pfad
  (Telemetry-Read, Command-Write)?
- **Decision M-e (Slave-Unit-ID)** — wie wird die
  Modbus-Slave-Adresse pro Target deklariert?
- **Decision M-f (Test-Sibling)** — wie wird der Modbus-
  Server-Sibling im Integration-Test bereitgestellt?

Die M4-Welle-0-Decision-Liste
([`done/M4-welle-0.md`](../planning/done/M4-welle-0.md) §3)
hat Decision 4 (Profile-Deklaration) als Adapter-
spezifische Frage markiert und Decision 5 (Test-Sibling-
Container) das **Modbus-Container-Lizenz-Risiko** explizit
genannt. ADR 0032 entscheidet beide finale fuer Modbus;
Welle 4 (OPC-UA-ADR) und Welle 5 (DNP3/IEC-Spike-ADR)
koennen das Pattern reusen oder per Schaerfungs-ADR
(ADR-0011-Pattern) ueberschreiben.

**Spannungsfeld:**

- **Sync vs. Background-Polling:** pymodbus 3.x bietet
  einen sync-`ModbusTcpClient`, der `read_holding_registers`
  als blocking-Call macht (typische Roundtrip-Latenz
  10-100 ms). Das passt **direkt** in die Sync-
  `DeviceProtocolPort`-Surface, aber: bei vielen Targets
  pro Tick summieren sich die Calls. Welle-6 (Cross-
  Adapter-Hardening) koennte Background-Polling
  einfuehren — Welle 3 entscheidet bewusst gegen den
  Komplexitaets-Sprung.
- **Datentyp-Defaults vs. Hersteller-Profile:**
  Modbus-Spec lässt die Byte/Word-Order weitgehend offen
  — `big_endian` ist die Default-Konvention, aber
  konkrete Wechselrichter-Hersteller (SMA, Fronius,
  Huawei) weichen ab. Welle 3 setzt einen sinnvollen
  Default und macht ihn per Target ueberschreibbar.
- **Modbus-Server-Container-Lizenz:** Free-Modbus-
  Server-Container sind selten und haben meist
  restriktive Lizenzen (`oitc/modbus-server` ist GPL
  mit kommerziellem Pfad; `mtoinen/modbus-server`
  ohne klare Lizenz). pymodbus selbst ist BSD-3-
  Clause und liefert einen produktiven
  `ModbusTcpServer` mit — Welle 3 nutzt den.
- **Function-Code-Vielfalt:** Modbus-Spec definiert
  ~20 Function-Codes; produktive Wechselrichter
  benutzen meist FC03/FC04 (Read) und FC06/FC10
  (Write). Welle 3 deckt diese vier ab; Coil-/
  Discrete-Input-Codes (FC01/FC02/FC05/FC0F) bleiben
  Welle-6-Schaerfung offen.

---

## 2. Entscheidung

ADR 0032 legt sechs Profile-Decisions fest.

### 2.1 Decision M-a — Register-Schema inline im `protocol_ports`-Block (final)

Register-Profile werden **inline** im `protocol_ports`-
Scenario-YAML-Block deklariert. Pattern uebernommen
direkt von ADR 0031 §2.1 (MQTT Topic-Schema inline).

**Skizze (finale Signatur in Welle-3-C2-feat):**

```yaml
protocol_ports:
  - type: modbus_tcp
    host: "192.168.1.50"
    port: 502
    unit_id: 1
    timeout_s: 5.0
    registers:
      battery1_soc:
        address: 40001
        datatype: "uint16"
        access: "read"
        # function_code: 3 (Default-FC03 fuer read)
      battery1_power:
        address: 40003
        datatype: "int32"
        access: "read"
        byte_order: "big_endian"
        word_swap: false
      battery1_setpoint:
        address: 40010
        datatype: "int16"
        access: "write"
        # function_code: 6 (Default-FC06 fuer write-single-register)
      pv1_yield:
        address: 40100
        datatype: "float32"
        access: "read"
        unit_id: 2  # Override: anderer Slave auf demselben Bus
```

Konkretes YAML-Schema (Pflicht-Felder, Optional-Felder,
Default-Werte pro Feld) wird in C2 in einer `mypy --strict`-
sauberen `ModbusProtocolPortConfig`-frozen-dataclass
(analog `MqttProtocolPortConfig` aus Welle 2) und einer
Validator-Routine fixiert.

**Begruendung:**

- Pattern-Konsistenz mit ADR 0031 §2.1: ein einheitliches
  Konstrukt `protocol_ports: list[<typ-spezifische-
  Config>]` ueber alle Adapter macht Scenarios lesbar
  und reduziert Loader-Komplexitaet.
- Register-Schemas sind **per Target eindeutig** (jede
  Device-ID hat ihre eigenen Register), genauso wie
  MQTT-Topics — Inline-Wachstum bleibt handhabbar.
- Separate Profile-Section haette dieselben Nachteile
  wie in ADR 0031 §3 A1 verworfen (zusaetzlicher
  Top-Level-Schluessel + Profile-Lookup-Indirektion);
  Welle 3 spart das ein.
- Welle 4 (OPC-UA) wird vermutlich dieselbe Inline-
  Praezedenz nehmen koennen (Node-ID-Schema ist analog
  pro Server eindeutig).

**Konsequenz:** `ModbusProtocolPortConfig`-frozen-dataclass
unter
`src/grid_gym/adapters/driven/protocol_modbus/_config.py`
mit Pflicht-Feldern `host: str`, `port: int = 502`,
`unit_id: int = 1`, `timeout_s: float = 5.0`,
`registers: Mapping[str, ModbusRegisterConfig]` (Mapping
von `device_id` auf Register-Profil). `ModbusRegisterConfig`
mit Pflicht-Feldern `address: int`, `datatype:
ModbusDatatype`, `access: Literal["read", "write"]`;
Optional-Feldern `byte_order: Literal["big_endian",
"little_endian"] = "big_endian"`, `word_swap: bool =
False`, `function_code: int | None = None` (None ->
Default-FC pro `access`), `unit_id: int | None = None`
(None -> Parent-Config-`unit_id`). Konstruktor-Validation
mit `ModbusConfigError`-Familie (analog
`MqttConfigError`-Familie aus Welle 2).

### 2.2 Decision M-b — Datatype-Set + Byte/Word-Order-Defaults (final)

Erlaubter Datatype-Set in Welle 3:

- **`int16`** — signed 16-bit (1 Register).
- **`uint16`** — unsigned 16-bit (1 Register).
- **`int32`** — signed 32-bit (2 Register).
- **`uint32`** — unsigned 32-bit (2 Register).
- **`float32`** — IEEE-754 single precision (2 Register).

`int64`/`uint64`/`float64`/`string`/`bool-array` bleiben
**Welle-6-Schaerfungspfad** offen via ADR 0011.

**Byte-Order-Default:** `big_endian` (Modbus-TCP-Spec
§4.1; Standard-Konvention fuer Multi-Register-Werte).

**Word-Swap-Default:** `false` (Konvention der meisten
Wechselrichter-Hersteller fuer `int32`/`uint32`/`float32`).

Per-Target ueberschreibbar via `byte_order`/`word_swap`-
Felder in `ModbusRegisterConfig` (Decision M-a).

**Konvertierung:** `struct.pack`/`struct.unpack` mit
Format-String aus Datatype + Byte-Order:

```text
"int16"   -> ">h"  oder "<h"
"uint16"  -> ">H"  oder "<H"
"int32"   -> ">i"  oder "<i"
"uint32"  -> ">I"  oder "<I"
"float32" -> ">f"  oder "<f"
```

`word_swap=true` rotiert die zwei Register vor dem
`unpack` (relevant nur fuer Multi-Register-Datatypes).

**Begruendung:**

- Welle-3-Minimum reicht fuer produktive
  Wechselrichter/Energiemeter-Profile (Power in `int32`,
  SOC in `uint16`, Voltage in `float32` etc.).
- `int64`/`float64` sind in der Energie-Domain selten
  und brauchen 4 Register pro Wert — schaerft sich erst
  bei konkretem Bedarf.
- `string`/`bool-array` sind Modbus-Spec-Sonderfaelle
  (Serial-Number-Reads, Multi-Coil-Bitmaps); kein
  Welle-3-Use-Case.
- `big_endian`-Default ist Modbus-Spec-Konvention;
  `word_swap=false`-Default deckt SMA/Fronius/Huawei-
  Produkte ab (Wechselrichter-Erfahrungswert).

**Konsequenz:** `_codec.py`-Modul (`encode_command_to_registers`
+ `decode_registers_to_telemetry`-Funktionen) konvertiert
zwischen `(value: int|Decimal, datatype, byte_order,
word_swap)` und `tuple[int, ...]` (Register-Liste). Codec
hat eigene typed Errors fuer (a) Out-of-Range-Werte,
(b) NaN/Infinity bei `float32`, (c) Unsupported-Datatype-
Kombinationen mit Word-Swap. Pattern analog
`_codec.py`-Modul aus Welle 2.

**Trigger-006-Re-Eval-Hinweis:** Modbus-Codec ist die
erste Stelle im Repo mit produktivem
`bytes`/`int`/`float`-Konvertierungs-Pfad. C3 prueft, ob
`mypy --strict-bytes` jetzt ohne `# type: ignore`-Inflation
greift; Entscheidung im Trigger-006-Body.

### 2.3 Decision M-c — Direkt-Sync (kein Background-Polling-Thread, final)

`ModbusDeviceProtocolPort` benutzt **keinen** Background-
Polling-Thread. `read(target)` ruft
`client.read_holding_registers(address, count,
device_id=unit_id)` **direkt synchron** gegen den Modbus-
Server. `write(target, command)` ruft analog
`client.write_register(address, value, device_id=unit_id)`
oder `client.write_registers(...)` direkt.

pymodbus-`ModbusTcpClient` ist sync-by-design (siehe
pymodbus-3.x-Doku Section „Synchronous Client") und
passt damit **ohne Adapter-internen Thread+Queue-Marshal**
direkt in die Sync-`DeviceProtocolPort`-Surface aus
ADR 0030 §2.1.

**Vorteil gegenueber MQTT (Decision 4d aus ADR 0031 §2.4):**

- Kein `dict[device_id, queue.Queue]`-Marshal-State.
- Kein `_on_message`-Callback-Boundary mit BLE001-
  Per-File-Ignore.
- Kein `error_translation.py`-Modul.
- `_port.py` ist signifikant einfacher (geschaetzt
  ~50 % kleiner als `protocol_mqtt/_port.py`).

**Begruendung:**

- pymodbus-Sync-Client ist der natuerliche Fit fuer die
  Sync-Surface.
- Background-Polling-Threads adden Komplexitaet
  (Lifecycle, Locking, Backpressure) ohne
  Welle-3-Use-Case.
- Tick-Latenz-Implikation ist real, aber **akzeptabel
  fuer Welle 3** (typische Sim-Scenarios haben < 20
  Modbus-Targets pro Tick; bei 50 ms Roundtrip ergibt
  sich < 1 s Tick-Block — unter `GG-RT-002`-Schwelle).

**Konsequenz:** `ModbusDeviceProtocolPort.read()` ist
blocking. Falls Welle 6+ Hochfrequenz-Telemetry-Scenarios
beweisen, dass das die Tick-Cadence sprengt, kann eine
Folge-ADR (ADR-0011-Pattern) ein Background-Polling-
Pattern einfuehren — ohne den `DeviceProtocolPort`-
Vertrag zu aendern (Adapter-intern). Welle 3
dokumentiert die direkt-sync-Wahl explizit als
**reversibel**.

**Reconnect-Verhalten:** pymodbus-Client macht Connect
in `start()` blocking; bei Verbindungs-Verlust waehrend
`read()`/`write()` wird `ModbusIOException` geworfen,
das in einen typed `DeviceProtocolPortReadError`/
`DeviceProtocolPortWriteError` umgemantelt wird (analog
MQTT-`MqttPortPublishFailedError` aus Welle 2). Welle
3 macht **keinen** Auto-Reconnect-Loop — Caller-Pflicht,
falls noetig.

### 2.4 Decision M-d — Function-Code-Mapping (final, ueberschreibbar)

**Default-Function-Codes:**

- **Telemetry-Reads (`access: "read"`):** `FC03` (Read
  Holding Registers, Modbus-Spec §5.3). Default fuer
  Wechselrichter-/Energiemeter-Telemetry.
- **Command-Writes (`access: "write"`, single value):**
  `FC06` (Write Single Register, Modbus-Spec §5.6).
  Default fuer Setpoint-Commands mit einem Register-Wert.
- **Command-Writes (`access: "write"`, multi-register
  value, z. B. `int32`/`uint32`/`float32`):** `FC10`
  (Write Multiple Registers, Modbus-Spec §5.16). Wird
  **automatisch** gewaehlt, wenn der Datatype ueber 1
  Register hinausgeht.

**Override-Pfad:** `function_code: int | None = None`
pro `ModbusRegisterConfig`. Erlaubte Welle-3-Werte sind
`3`, `4`, `6` und `16`:

- `3` (Read Holding Registers, FC03) — explizite Default-
  Wahl fuer Read-Targets.
- `4` (Read Input Registers, FC04) — fuer read-only-
  Devices; statt FC03.
- `6` (Write Single Register, FC06) — fuer Single-Register-
  Writes.
- `16` (Write Multiple Registers, FC10) — fuer Multi-
  Register-Writes oder Slaves, die auch Single-Register-
  Writes nur ueber FC10 akzeptieren.

Coil-/Discrete-Input-Codes (`1`, `2`, `5`, `15`) bleiben
Welle-6-Schaerfungspfad.

**Validation:** `ModbusRegisterConfig`-Validator prueft in
Welle 3 Allow-List, Access-Vertraeglichkeit (kein FC03
mit `access="write"`, kein FC06 mit `access="read"`) und
seit Review-Folge 2026-05-31 datatype-spezifisch, dass
FC06 nur fuer Single-Register-Datatypes erlaubt ist
([`done/031`](../planning/done/031-modbus-adapter-review-folge.md)).

**Begruendung:**

- FC03/FC10 sind die Wechselrichter-Standard-Codes
  (Erfahrungswert aus SMA/Fronius/Huawei-Profilen).
- FC04 ist haeufig bei produktiven Energiemetern (nur
  Read-Pfad noetig).
- FC06 ist atomischer als FC10 fuer Single-Register-
  Writes (kein 4-Register-Multi-Write-Roundtrip).
- Coil-Codes (FC01/FC02/FC05/FC0F) verschoben auf
  Welle 6, weil Welle-3-Use-Cases (Wechselrichter-
  Telemetry) keine Coil-Domain haben.

**Konsequenz:** `_port.py`-`read()` dispatcht
function_code -> `client.read_holding_registers(...)`
oder `client.read_input_registers(...)`; `write()`
dispatcht function_code -> `client.write_register(...)`
oder `client.write_registers(...)`. Default-Resolver
(`access -> function_code`) im `_config.py`. FC06 fuer
Multi-Register-Datatypes wird seit
[`done/031`](../planning/done/031-modbus-adapter-review-folge.md)
fail-fast als Config-Fehler abgelehnt.

### 2.5 Decision M-e — Slave-Unit-ID per Target (final)

Pro `ModbusRegisterConfig` ein optionales
`unit_id: int | None = None`-Feld. Wenn `None`, faellt
es auf die Parent-`ModbusProtocolPortConfig.unit_id`
zurueck (Default `1`).

**Begruendung:**

- Multi-Slave-Bus-Scenarios sind real (z. B. ein
  Modbus-Gateway, das mehrere serielle RTU-Slaves
  ueber TCP exponiert) — aber selten.
- Single-Slave-Default `1` deckt die haeufigste
  Topologie (1 Wechselrichter pro TCP-Verbindung) ab.
- Per-Target-Override haelt Multi-Slave-Faelle offen
  ohne separaten `protocol_ports`-Eintrag pro Slave.

**Range:** `unit_id` muss in `[1, 247]` liegen
(Modbus-Spec §4.1; `0` ist Broadcast, `248-255` sind
reserviert). Konstruktor-Validation in
`ModbusConfigError`-Familie.

**Konsequenz:** `_port.py` reicht `unit_id` als
`device_id=`-Kwarg an pymodbus-Calls weiter. Die aktuelle
pymodbus-3.13-API benutzt `device_id`; Tests pinnen diesen
konkreten Kwarg-Namen, `uv.lock` haelt die aufgeloeste
Version fest.

### 2.6 Decision M-f — In-Process pymodbus-Server fuer Integration-Smoke (final)

**Test-Sibling-Variante in Welle 3:** **in-process
`pymodbus.server.ModbusTcpServer`** im Test-Code
(`tests/integration/test_modbus_in_process_smoke.py`),
**kein** testcontainers-Container.

**Setup:**

```text
1. Test setzt eine `ModbusDataStore` mit Register-
   Default-Werten auf.
2. `threading.Thread(target=server.serve_forever,
   daemon=True)` spawnt den `ModbusTcpServer`.
3. Test wartet ~100 ms auf Server-Bereitschaft (oder
   pollt mit Connect-Check).
4. End-to-End-Read/Write-Roundtrip via
   `ModbusDeviceProtocolPort` durch alle 5 Datatypes im
   Default-Profil (`big_endian`, kein Word-Swap,
   Parent-`unit_id=1`).
5. Teardown: `server.shutdown()` + `thread.join(timeout=5.0)`.
```

**Begruendung:**

- **Lizenz-Sicherheit:** Modbus-Server-Container haben
  restriktive Lizenzen (M4-Welle-0 §3 Decision 5
  dokumentiert: `oitc/modbus-server` GPL+Kommerz-Pfad,
  `mtoinen/modbus-server` ohne klare Lizenz).
  pymodbus selbst ist BSD-3-Clause (verifiziert per
  pymodbus-PyPI-Metadata) und liefert produktiven
  Server mit.
- **CI-Latenz:** Kein Docker-Image-Pull, kein
  Container-Boot-Wait. Der pymodbus-Server kommt im
  Test-Prozess in < 100 ms hoch.
- **Realitaet:** pymodbus-Server implementiert
  Modbus-Spec vollstaendig fuer FC03/FC04/FC06/FC10
  — das gleiche, was Welle-3-Adapter abruft. Tests
  pruefen damit `client <-> server`-Compatibility
  innerhalb derselben Library.
- **Praezedenz:** M2-Welle-6c-Postgres-Sibling +
  M4-Welle-2-Mosquitto-Sibling sind beide Container-
  basiert, weil produktive Server (Postgres,
  Mosquitto) im Test-Container leichter zu fahren
  sind als als Library. Modbus ist umgekehrt:
  pymodbus liefert sowohl Client als auch Server,
  und das Server-Modul ist produktiv-stabil.

**Konsequenz:**

- **Keine `tests/integration/compose.yml`-
  Erweiterung** in Welle 3. Header-Kommentar (C2 EDIT)
  dokumentiert die bewusste Entscheidung als
  Pattern-Praezedenz fuer Folge-Wellen (Welle 4
  asyncua koennte analog in-process testen — siehe
  asyncua-`Server`-API).
- **Keine testcontainers-`DockerContainer`-Fixture.**
- **Daemon-Thread-Lifecycle:** `daemon=True` schuetzt
  den Test-Prozess vor haengenden Threads bei
  Test-Failure; expliziter `server.shutdown()` +
  `thread.join(timeout=5.0)` im Teardown.
- **Port-Auswahl:** `0` (OS waehlt freien Port) oder
  fester Hoch-Port (z. B. `15020`) — C2-Entscheidung;
  Default-Vorschlag fester Port fuer Reproduzierbarkeit
  in Debug-Sessions.

---

## 3. Alternativen

**A1 (verworfen) — Separate `modbus_profiles`-Top-Level-
Section:** wuerde Decision M-a auf eine eigene Schluessel-
Section verlagern. Verworfen wegen YAGNI (siehe ADR 0031
§3 A1; Welle-3-Scenarios haben dieselbe Skalierung wie
Welle-2-Scenarios — ≤ 10 Targets pro Adapter).

**A2 (verworfen) — Datatype-Set inklusive `int64`/
`float64`/`string` ab Welle 3:** wuerde Welle-3-Codec-
Komplexitaet verdoppeln (4-Register-Datatypes,
String-Padding-Konventionen). Verworfen wegen YAGNI;
ADR-0011-Schaerfungspfad bleibt offen.

**A3 (verworfen) — Background-Polling-Thread mit
`dict[device_id, deque[TelemetryPoint]]`-Cache:** wuerde
`read()`-Latenz vom TickLoop-Thread entkoppeln, aber
Adapter-Komplexitaet drastisch erhoehen (Polling-
Cadence-Konfig, Cache-Invalidation, Backpressure-
Strategie). Verworfen — Welle-3-Use-Cases brauchen das
nicht; Welle 6+ kann per Folge-ADR nachziehen.

**A4 (verworfen) — pymodbus-Async-Client + asyncio-
Loop-Thread (analog Welle-4-OPC-UA-Plan):** wuerde
ein Async-Pattern in Welle 3 vorzeitig vorziehen.
Verworfen, weil pymodbus-Sync-Client der natuerlichere
Fit ist und Welle 4 das Async-Pattern produktiv vortraegt
(asyncua hat keinen Sync-Wrapper).

**A5 (verworfen) — `little_endian`-Default fuer
Byte-Order:** waere SMA-spezifisch (manche SMA-Inverter
benutzen Little-Endian fuer `float32`). Verworfen —
Modbus-Spec-Default ist Big-Endian; Per-Target-Override
deckt SMA-Faelle ab.

**A6 (verworfen) — `unit_id` als Pflicht-Feld pro
`ModbusRegisterConfig` (statt Optional mit Parent-
Fallback):** wuerde Multi-Slave-Faelle nativer
unterstuetzen, aber Single-Slave-Scenarios mit
Boilerplate belasten. Verworfen — Welle-3-Default-1-
Fallback ist der haeufigere Fall.

**A7 (verworfen) — `oitc/modbus-server`-Container als
Sibling:** waere konsistent mit Welle-2-Mosquitto-Pattern.
Verworfen wegen Lizenz-Risiko (siehe Decision M-f
Begruendung) und unnoetiger Komplexitaet (Docker-Pull,
Container-Boot, port-mapping in Sibling-Mode).

**A8 (verworfen) — Eigener Mini-Modbus-Server im
Test-Code (statt pymodbus-Server):** waere komplett
unabhaengig von pymodbus-Server-API-Drift, aber duplexte
Modbus-Spec im Test-Code. Verworfen — pymodbus-Server
ist BSD-3-Clause + produktiv-stabil; Re-Implementation
waere unnoetige Wartungslast.

**A9 (verworfen) — Coil-Function-Codes (FC01/FC02/FC05/
FC0F) ab Welle 3:** wuerde Bool-Datatype + Coil-Pfad
hinzufuegen. Verworfen wegen YAGNI; Welle-6-Schaerfung
offen.

---

## 4. Konsequenzen

- **Welle-3-C2-Implementierungs-Pflicht** (`feat(welle-3):
  protocol_modbus + Tests + In-Process-Smoke +
  Compose-Edit`):
  - NEU `src/grid_gym/adapters/driven/protocol_modbus/__init__.py`
    mit `ModbusDeviceProtocolPort` als
    `DeviceProtocolPort`-Implementer (ADR 0030 §2.1).
  - NEU `src/grid_gym/adapters/driven/protocol_modbus/_config.py`
    (`ModbusProtocolPortConfig` + `ModbusRegisterConfig`
    frozen-dataclasses, Decision M-a/M-b/M-d/M-e-
    Schema; `ModbusDatatype`-Enum mit 5 Werten).
  - NEU `src/grid_gym/adapters/driven/protocol_modbus/_codec.py`
    (`encode_command_to_registers` /
    `decode_registers_to_telemetry`-Funktionen,
    Decision M-b).
  - NEU `src/grid_gym/adapters/driven/protocol_modbus/_port.py`
    (Decision M-c direkt-sync; Lifecycle; Function-
    Code-Dispatcher; pymodbus-Exception-Translation).
  - NEU `src/grid_gym/adapters/driven/protocol_modbus/_errors.py`
    (typed `DeviceProtocolPort*Error`-Subclasses fuer
    Connect/Disconnect/Read/Write/Unknown-Target;
    Pattern analog `protocol_mqtt/_errors.py`).
  - **Modul-Docstring** mit Lastenheft-Z. 1161–1163-
    Pflicht: „Simulations-/Testadapter; keine produktive
    Anlagensteuerung". Cross-Cutting-Pflicht ist
    Adapter-spezifisch (Welle 6 prueft sweepartig fuer
    alle `protocol_*`-Module).
  - 4 Unit-Test-Module unter
    `tests/unit/adapters/driven/protocol_modbus/`.
  - 1 Integration-Smoke unter
    `tests/integration/test_modbus_in_process_smoke.py`
    (Decision M-f).
- **`tests/integration/compose.yml`-Header-Kommentar-
  Sync (C2 EDIT):** dokumentiert die bewusste Decision-
  M-f-Wahl (in-process-Smoke; kein neuer Sibling-
  Service) als Pattern-Praezedenz fuer Folge-Wellen.
- **`pyproject.toml`-Erweiterung:** `pymodbus>=3.6,<4.0`
  in `[project] dependencies`. Pin `<4.0` schuetzt
  gegen Sync-API-Deprecation in 4.x (siehe Decision
  M-c Konsequenz-Hinweis). `pymodbus`-Eintrag in den
  AC-PORTS-NO-FW- und AC-NO-FW-Forbidden-Listen ist
  Welle-0-vorbelegt — keine Aenderung an den
  `[[tool.importlinter.contracts]]`-Bloecken noetig.
- **`Dockerfile`-Erweiterung:** `CRITICAL_COV_TARGETS`-
  Default um `src/grid_gym/adapters/driven/protocol_modbus`
  erweitert (Pattern analog `protocol_mqtt`-Eintrag aus
  M4-Welle-2-C2 `f33bb4e`). `make gates` cache-frei
  gruen ohne `CRITICAL_COV_TARGETS`-Override.
- **`AC-ADAPTER-LIGHTWEIGHT` greift unveraendert**
  (`tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`). Welle 3 muss nur
  Smoke-Regression-Schutz pruefen — der Welle-1-§7-
  Folge-Pflicht-Planted-Violator-Property-Test bleibt
  Welle-6-Material (siehe
  [`../planning/done/M4-welle-1.md`](../planning/done/M4-welle-1.md)
  §7 Folge-Mitigation; Welle-2-Verzicht wurde in
  ADR 0031 §4 dokumentiert; Welle 3 setzt das Pattern
  fort).
- **Scenario-Loader bleibt Modbus-frei** (AC-HEXAGON-
  PURE): analog zur Welle-2-Konsequenz aus ADR 0031 §4
  (`hexagon/core/scenario/loader.py` darf
  `ModbusProtocolPortConfig` nicht direkt parsen;
  Adapter-Plugin-Pattern).
- **Caller-Scope-Lifecycle bleibt ADR-0030-Vertrag:**
  Caller wrappen `loop.start_protocol_ports()` /
  `loop.stop_protocol_ports()` in `try/finally` um
  die Tick-Schleife. Modbus-Adapter haengt sich
  identisch zum MQTT-Adapter in dieses Pattern ein;
  **keine** Aenderung an TickLoop.
- **Snapshot-Vertrag bleibt v2** (ADR 0030 §2.3):
  Modbus-Adapter ist stateless aus Replay-Sicht;
  Reconnect-State (TCP-Socket-Status) ist volatile.
  Reversibilitaet via ADR-0015-Pattern.
- **OTel-Span-Wrap der Adapter-Calls:** ADR 0032 wrappt
  Adapter-Calls **nicht** mit OTel-Spans. Welle 6 ist
  der Zeitpunkt fuer den `TracePort`-Wrap (ADR 0024
  §2.4 als Bezug).
- **Trigger-006-Re-Eval-Pflicht (C3):** Welle-3-Modbus-
  Code ist der erste produktive `bytes`/`int`/`float`-
  Konvertierungs-Pfad im Repo. C3 prueft mit konkretem
  `_codec.py`-Code, ob `mypy --strict-bytes` jetzt ohne
  `# type: ignore`-Inflation greift. Trigger-006-Body
  in `docs/plan/planning/open/006-mypy-strict-bytes.md`
  wird mit Modbus-Beleg synced (Zahlen vor/nach
  potentieller Aktivierung) und entweder nach `next/`
  gezogen (positiv) oder bleibt in `open/` (negativ).
- **Welle-4-Implementer-Auflage (OPC-UA-Adapter):**
  Welle 4 traegt erstmals einen rein-async-Stack
  (`asyncua`). Decision M-c (Welle-3-direkt-sync) ist
  **nicht** direkt reusable; Welle 4 schreibt eigene
  Marshal-Decision analog Welle-2-Decision-4d (Thread+
  Loop-Pattern), aber dort wird ein **dedizierter
  asyncio.Loop in eigenem Thread** das natuerliche
  Konstrukt sein, nicht `queue.Queue` wie bei
  paho-mqtt.
- **Welle-5-Implementer-Auflage (DNP3/IEC):** falls
  Welle 5 produktiv wird (Spike), erweitert sie das
  Pattern fuer den jeweiligen Stack — DNP3/IEC haben
  eigene Decisions (Points/Logical-Nodes statt
  Register/Topic).

---

## 5. Status-Pfad

- **Proposed** — 2026-05-30 (M4-Welle-3-C1 `a86ac46`).
  Initial-Entwurf; Review-Schleife offen.
- **Provisional** — 2026-05-30 (M4-Welle-3-C3) nach
  C2-Merge `d721982` (feat-Commit:
  `protocol_modbus/`-5-Modul-Paket + 95 neue Unit-Tests
  (~25 Config-Validation + ~30 Codec-Roundtrip inkl.
  hypothesis-Property-Tests + ~24 Lifecycle/Read+Write
  mit mocked pymodbus-Client + ~16 Function-Code-
  Override) + 1 In-Process-Integration-Smoke
  (`tests/integration/test_modbus_in_process_smoke.py`)
  + `compose.yml`-Kommentar-Sync + `pyproject.toml`-Edit
  (`pymodbus>=3.6,<4.0`) + `Dockerfile`-Edit
  (`CRITICAL_COV_TARGETS` um
  `adapters/driven/protocol_modbus`); `make test-unit`
  1306 gruen, `make test-integration` 23 gruen mit
  Modbus-In-Process-Smoke, `make arch-check` weiter
  19/19 Contracts KEPT, `make gates` cache-frei gruen
  ohne `CRITICAL_COV_TARGETS`-Override). Trigger
  006-Re-Eval mit Modbus-Code-Beleg ebenfalls in C3
  abgeschlossen: `mypy --strict-bytes` laeuft ohne
  zusaetzliche `# type: ignore`-Inflation gegen den
  Modbus-Code (siehe
  [`open/006`](../planning/open/006-mypy-strict-bytes.md);
  Trigger ist aktivierungs-reif; Aktivierung bleibt
  separater Folge-Slice).
  Doku-Review-Folge 2026-05-31: Integration-Smoke ist
  als Default-Profil-E2E-Test dokumentiert; Byte-Order-/
  Word-Swap-Matrix und Unit-ID-Override sind nicht als
  E2E-Smoke geliefert. Review-Folge
  [`done/031`](../planning/done/031-modbus-adapter-review-folge.md)
  hat FC06-Multi-Register-Guard, Read-/Write-Fehler-
  Taxonomie und Adapter-Rand-Fehleruebersetzung umgesetzt.
- **Accepted** — geplant mit M4-Welle-7-Closure
  (analog ADR 0022..0027 + 0030 + 0031). Voraussetzung:
  Welle 4 (OPC-UA) implementiert ihren Adapter ohne
  Decision-M-a-Pattern-Schaerfungs-ADR (oder die
  Schaerfung ist explizit dokumentiert,
  ADR-0011-Pattern); Welle 5 (DNP3/IEC) klaert ihre
  Disposition.
