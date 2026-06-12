# ADR 0033 — OPC-UA-Adapter-Profile (M4 Welle 4)

**Status:** Accepted — gezogen 2026-06-01 mit M4-Welle-7-C1
(dieser Commit; M4-Closure-Welle). Provisional-Schritt
2026-05-31 mit M4-Welle-4-C3 `7ad5baf`. Zusatz-Schaerfung
2026-05-31 durch Slice 032 (Welle-4-Review-Folge): Body
geschaerft an §2.1 (Optional-Felder-Klarstellung), §2.5
(Test-Server-Loop-Thread-Klarstellung) und §5 (Slice-032-
Entry); Code-Fixes in separatem feat-Commit.
Initial-Entwurf (`Proposed`) 2026-05-31 mit M4-Welle-4-C1
`74ed35b`; C2-Merge `78fdd7a` (feat `protocol_opcua/`-6-
Modul-Paket + 81 neue Unit-Tests + in-process asyncua-
Server-Integration-Smoke + `pyproject.toml`/`uv.lock`/
`Dockerfile`/`compose.yml`-Edits; `make test-unit` 1395
gruen, `make test-integration` 31 gruen (8 OPC-UA-Smokes),
`make arch-check` 19/19 KEPT, `make gates` cache-frei
gruen ohne `CRITICAL_COV_TARGETS`-Override) belegt die
Decisions O-a/O-b/O-c/O-d/O-e produktiv. Cross-Adapter-
OTel-Span-Wrap aus Welle 6a wrappt auch den OPC-UA-
Adapter ohne Adapter-Code-Diff. Status-Pfad:
`Proposed → Provisional` (2026-05-31 M4-Welle-4-C3 +
Slice-032-Schaerfung) → **Accepted** (2026-06-01
M4-Welle-7-C1, dieser Commit, analog ADR 0022..0027 +
0030 + 0031 + 0032).
**Datum:** 2026-05-31 (Erstfassung) / 2026-05-31 (Slice-032-Review-Folge) / 2026-06-01 (Accepted, M4-Welle-7-C1)
**Bezug:**
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md)
(Schaerfungs-ohne-Supersede-Pattern — ADR 0033 schaerft
ADR 0030 §2.1, ADR 0031 §2.1 und ADR 0032 §2.1 konkret fuer
OPC-UA, ohne den Sync-`DeviceProtocolPort`-Vertrag oder die
inline-Profile-Praezedenz zu ersetzen),
[`ADR 0030`](0030-device-protocol-port-surface.md) §2.1
(Sync-`Protocol`-Vertrag mit Adapter-internem
Thread+Loop-Marshal-Vorbelegung fuer rein-async-Stacks;
ADR 0030 nennt Welle 4 explizit als die Pruefstelle, an
der diese Konstruktion produktiv vorgetragen wird —
`asyncua` ist nur async und braucht damit das in MQTT
(`paho-loop_start()`) und Modbus (direkt-sync) **nicht**
verprobte Pattern) + §2.2 (Caller-Scope-Lifecycle) +
§2.3 (stateless aus Replay-Sicht — OPC-UA-Reconnect-State
ist volatile, kein Snapshot-Bump in Welle 4),
[`ADR 0031`](0031-mqtt-adapter-profile.md) §2.1
(Decision 4a inline-Profile-Pattern — ADR 0033 uebernimmt
das Pattern direkt fuer Node-ID-Schema; siehe §2.1 unten)
+ §2.2 (Decision 4b `canonical_json`-Codec — ADR 0033
**weicht ab**: OPC-UA benutzt `asyncua.ua.Variant`-Typ-
Konstruktoren direkt; kein JSON-Layer zwischen Adapter
und Wire-Format) + §2.4 (Decision 4d Per-Target Queue-
Marshal — **nicht** reusable; OPC-UA hat eigenes
`OpcuaLoopThread`-Marshal-Pattern, siehe §2.2 unten),
[`ADR 0032`](0032-modbus-adapter-profile.md) §2.1
(Decision M-a inline-Register-Schema — direkte Pattern-
Praezedenz fuer Decision O-a inline-Node-ID-Schema) +
§2.3 (Decision M-c direkt-sync — **nicht** reusable;
asyncua erzwingt das Thread+Loop-Pattern; siehe §2.2)
+ §2.6 (Decision M-f in-process-Server — direkt reusable
fuer Decision O-e: pymodbus liefert Server in derselben
BSD-Library, asyncua liefert Server in derselben
LGPL-Library; gleiches Pattern).
M4-Slice-Plan
[`done/M4-protocol-adapters.md`](../planning/done-archive/M4-protocol-adapters.md)
§3 Welle 4; M4-Welle-0-Decision-Liste
[`done/M4-welle-0.md`](../planning/done-archive/M4-welle-0.md) §3
Decision 2 (Sync vs. async-Vertrag — Welle-1-final
`sync-Protocol` greift hier produktiv: asyncua ist
rein-async, Welle-4-Adapter haelt einen eigenen
asyncio-Event-Loop-Thread) + Decision 4 (Profile-
Deklaration) + Decision 5 (Test-Sibling-Container —
asyncua-Server-Container-Lizenz nicht relevant, weil
in-process gewaehlt; siehe §2.5).
Lastenheft §16 (`GG-OPCUA-001`, Z. 1149–1163 SOLLTE-Cluster:
Node-ID-Schema + Datentypen + Read/Write-Operationen +
Fehlerverhalten + Adapter-Smoke).
Architektur §7 (`GG-AR-PORT-DRN-007` Driven-Ports-Tabelle —
ADR 0030 hat den Slot belegt; Welle 4 liefert dritten
Implementer) + §8.2 (Adapter-Interfaces-Driven-Beschreibung
— Node-ID-Schema konkretisiert die generische Beschreibung
fuer OPC-UA) + §16 (Deployment-Sicht — `protocol_opcua`-
Adapter lebt im `simulation`-Worker, kein eigener Compose-
Service; **kein** Test-Sibling-Service in
`tests/integration/compose.yml`, weil Welle 4 explizit
in-process testet — Pattern fortgefuehrt aus Welle 3).
M2-Welle-6c-Postgres-Sibling-Pattern + M4-Welle-2-
Mosquitto-Sibling-Pattern als testcontainers-Praezedenz;
M4-Welle-3-pymodbus-In-process-Pattern als
in-process-Praezedenz. **Welle 4 folgt der Welle-3-
Praezedenz** (siehe §2.5 Decision O-e).

---

## 1. Kontext

`GG-OPCUA-001` (Lastenheft §16 Z. 1149–1163) verlangt
einen OPC-UA-Adapter als **Simulations-/Testadapter** mit
deterministischem Adapter-Smoke-Test (mindestens ein
Read- und ein Write-Pfad). M4-Welle-2 hat den ersten
konkreten Implementer (`MqttDeviceProtocolPort`, ADR
0031 `Provisional`) produktiv geliefert; M4-Welle-3 den
zweiten (`ModbusDeviceProtocolPort`, ADR 0032
`Provisional`); Welle 4 liefert den dritten:
`OpcuaDeviceProtocolPort` unter
`src/grid_gym/adapters/driven/protocol_opcua/` ueber
`asyncua >= 1.1`.

ADR 0030 hat den **Sync-Vertrag** und den **Caller-Scope-
Lifecycle** finalisiert; ADR 0030 §2.1-Konsequenz nennt
Welle 4 als die Pruefstelle, an der die Adapter-interne
Thread+Loop-Marshal-Konstruktion fuer rein-async-Stacks
produktiv vorgetragen wird:

> Welle 4 (OPC-UA) tragt die Thread+Loop-Konstruktion fuer
> einen rein-async-Stack zum ersten Mal real. Falls sich
> dort die Wahl als zu schmerzhaft erweist, schaerft eine
> Folge-ADR den Vertrag (Schaerfung-ohne-Supersede per
> ADR 0011).

ADR 0031 hat das **inline-im-`protocol_ports`-Block**-
Profile-Pattern etabliert; ADR 0032 hat es Modbus-spezifisch
geschaerft (Register-Schema). ADR 0033 schaerft die fuer
den OPC-UA-Adapter notwendigen Sub-Entscheidungen
**konkret**:

- **Decision O-a (Node-ID-Schema)** — wo und wie werden
  Device-ID → Node-ID-Mappings deklariert?
- **Decision O-b (Async-Bridge)** — wie wird die rein-
  async asyncua-API gegen die sync-`DeviceProtocolPort`-
  Surface vermittelt?
- **Decision O-c (Datatype-Set)** — welche OPC-UA-Built-
  In-Types sind in Welle 4 unterstuetzt, und wie werden
  sie zu Python-Typen konvertiert?
- **Decision O-d (Read/Write-Pfad)** — wie werden
  Telemetry-Reads und Command-Writes auf asyncua-API-
  Calls abgebildet, und wo bleiben Subscription-Pfade
  Welle-6-Material?
- **Decision O-e (Test-Sibling)** — wie wird der OPC-UA-
  Server-Sibling im Integration-Test bereitgestellt?

Die M4-Welle-0-Decision-Liste
([`done/M4-welle-0.md`](../planning/done-archive/M4-welle-0.md) §3)
hat Decision 4 (Profile-Deklaration) als Adapter-
spezifische Frage markiert und Decision 5 (Test-Sibling-
Container) das Lizenz-Risiko von Server-Containern
allgemein adressiert. ADR 0033 entscheidet beide finale
fuer OPC-UA; Welle 5 (DNP3/IEC) kann das Pattern reusen
oder per Schaerfungs-ADR (ADR-0011-Pattern) ueberschreiben.

**Spannungsfeld:**

- **Rein-async-Stack vs. Sync-Surface:** `asyncua` ist
  rein-async (`asyncua.Client` ist `AsyncIO`-Coroutinen-
  basiert; es gibt keinen Sync-Wrapper in der Library
  selbst, abgesehen von einer experimentellen
  `asyncua.sync`-Submodule, die produktiv-instabil ist).
  Das passt **nicht** direkt in die Sync-
  `DeviceProtocolPort`-Surface aus ADR 0030 §2.1; ein
  Adapter-interner asyncio-Event-Loop-Thread + Marshal
  ist Pflicht.
- **Loop-Thread-Lifecycle:** der eigene asyncio-Loop muss
  bei `start()` sauber aufgesetzt und bei `stop()` mit
  geordnetem Task-Cancellation + Loop-Stop +
  Thread-Join abgebaut werden. Falls eine pending
  Coroutine den Loop-Stop blockiert, bleibt der
  Test-Prozess am Ende stecken. Daemon-Thread schuetzt
  vor Prozess-Aufhaengen bei katastrophalem Fehler, aber
  ein expliziter Teardown-Vertrag ist normativ.
- **OPC-UA-Datentyp-Vielfalt:** OPC-UA-Spec definiert
  ~25 Built-In-Types + benutzerdefinierte
  `ExtensionObject`-Strukturen + Arrays / Matrizen.
  Produktive Wechselrichter/Energiemeter benutzen
  meist `Boolean`/`Int32`/`UInt32`/`Float`/`Double`/
  `String`. Welle 4 deckt diese sieben Welle-4-Minimum-
  Datatypes ab; `Byte`/`SByte`/`Int64`/`UInt64`/
  `DateTime`/`Guid`/`ByteString`/`ExtensionObject`
  bleiben Welle-6-Schaerfung offen.
- **Subscription vs. Polling-Read:** OPC-UA ist auf
  Subscription-basiertes Reading ausgelegt (`Monitored
  Items` + `Subscription.subscribe_data_change`);
  Polling-Read (`Node.read_value()`) ist
  spec-konform, aber weniger effizient. Welle 4 deckt
  Polling-Read ab, weil das Polling-Pattern aus Welle 3
  (Modbus, direkt-sync) ueberinkrementell ueberfuehrt
  werden kann. Subscription-Pfad bleibt Welle-6-
  Schaerfung.
- **Server-Container-Lizenz vs. in-process:** Open-Source-
  OPC-UA-Server-Container existieren (`open62541/open62541`
  unter MPL-2.0; `OPCFoundation/UA-Server` unter
  RCL-Lizenz mit kommerziellem Pfad). Aber `asyncua` selbst
  (LGPL-3.0 fuer Library-Usage) bringt einen produktiven
  `asyncua.Server` mit — Welle 4 nutzt ihn (Pattern-
  Praezedenz Welle-3-Decision-M-f). LGPL-3.0 ist fuer
  Library-Linking ok; das Repo bleibt unter MIT-Lizenz,
  asyncua wird via uv.lock gepinnt und nicht modifiziert.

---

## 2. Entscheidung

ADR 0033 legt fuenf Profile-Decisions fest.

### 2.1 Decision O-a — Node-ID-Schema inline im `protocol_ports`-Block (final)

Node-ID-Profile werden **inline** im `protocol_ports`-
Scenario-YAML-Block deklariert. Pattern uebernommen
direkt von ADR 0031 §2.1 (MQTT Topic-Schema inline) und
ADR 0032 §2.1 (Modbus Register-Schema inline).

**Skizze (finale Signatur in Welle-4-C2-feat):**

```yaml
protocol_ports:
  - type: opcua
    endpoint_url: "opc.tcp://192.168.1.50:4840"
    timeout_s: 5.0
    nodes:
      battery1_soc:
        node_id: "ns=2;i=1001"
        datatype: "Float"
        access: "read"
      battery1_power:
        node_id: "ns=2;i=1002"
        datatype: "Int32"
        access: "read"
      battery1_setpoint:
        node_id: "ns=2;s=Battery.Setpoint"
        datatype: "Int16"
        access: "write"
      pv1_yield:
        node_id: "ns=3;i=42"  # Namespace 3 wird aus node_id extrahiert
        datatype: "Double"
        access: "read"
```

Konkretes YAML-Schema (Pflicht-Felder, Optional-Felder,
Default-Werte pro Feld) wird in C2 in einer `mypy --strict`-
sauberen `OpcuaProtocolPortConfig`-frozen-dataclass (analog
`MqttProtocolPortConfig` aus Welle 2 und
`ModbusProtocolPortConfig` aus Welle 3) und einer
Validator-Routine fixiert.

**Begruendung:**

- Pattern-Konsistenz mit ADR 0031 §2.1 + ADR 0032 §2.1:
  ein einheitliches Konstrukt `protocol_ports:
  list[<typ-spezifische-Config>]` ueber alle Adapter
  macht Scenarios lesbar und reduziert Loader-Komplexitaet.
- Node-ID-Schemas sind **per Target eindeutig** (jede
  Device-ID hat ihre eigene Node-ID), genauso wie
  MQTT-Topics und Modbus-Register — Inline-Wachstum
  bleibt handhabbar.
- Separate Profile-Section haette dieselben Nachteile
  wie in ADR 0031 §3 A1 / ADR 0032 §3 A1 verworfen
  (zusaetzlicher Top-Level-Schluessel + Profile-Lookup-
  Indirektion); Welle 4 spart das ein.
- OPC-UA-Node-IDs haben mehrere Formate (`ns=N;i=M`
  numerisch, `ns=N;s=String`, `ns=N;g=GUID`,
  `ns=N;b=ByteString`). Welle 4 unterstuetzt **numerisch
  und String** (haeufigste Form bei Industrie-Servern);
  GUID/ByteString-Identifier bleiben Welle-6-Schaerfung.

**Konsequenz:** `OpcuaProtocolPortConfig`-frozen-dataclass
unter
`src/grid_gym/adapters/driven/protocol_opcua/_config.py`
mit Pflicht-Feldern `endpoint_url: str`, `timeout_s: float
= 5.0`, `nodes: Mapping[str, OpcuaNodeConfig]` (Mapping
von `device_id` auf Node-Profil). `OpcuaNodeConfig` mit
Pflicht-Feldern `node_id: str` (Format `"ns=N;i=M"` oder
`"ns=N;s=Identifier"`), `datatype: OpcuaDatatype`,
`access: Literal["read", "write"]`. Konstruktor-Validation
mit `OpcuaConfigError`-Familie (analog `ModbusConfigError`-
Familie aus Welle 3). **Slice-032-Schaerfung (Welle-4-Review-
Folge Finding 6.4):** Namespace-Index und Identifier-Type
werden direkt aus dem `node_id`-String extrahiert
(`_NODE_ID_PATTERN`-Regex in `_config.py`); separate
Optional-Felder `namespace_index`/`identifier_type` sind
**nicht** Teil des Welle-4-Schemas (YAGNI — kein Welle-4-
Use-Case fuer Override). Welle-6-Schaerfung kann sie via
ADR-0011-Pattern nachziehen, falls Multi-Namespace-Targets
sie tatsaechlich brauchen.

### 2.2 Decision O-b — Async-Bridge via dediziertem asyncio-Loop-Thread (final)

`OpcuaDeviceProtocolPort` haelt einen **dedizierten
`asyncio.AbstractEventLoop`** in einem eigenen
`threading.Thread(daemon=True)`. Sync-Aufrufe von
`read()` und `write()` marshalen via
`asyncio.run_coroutine_threadsafe(coro, loop).result(timeout)`
in den Loop-Thread.

**Modulstruktur:** `_loop_thread.py` mit Klasse
`OpcuaLoopThread`:

```text
class OpcuaLoopThread:
    def start(self) -> None:
        # `asyncio.new_event_loop()`; `Thread(target=loop.run_forever, daemon=True)`
        # `.start()`; idempotent.
        ...

    def stop(self, *, timeout_s: float = 5.0) -> None:
        # `loop.call_soon_threadsafe(loop.stop)`; `thread.join(timeout=timeout_s)`
        # `loop.close()`; idempotent.
        ...

    def run_coroutine(self, coro: Awaitable[T], *, timeout_s: float) -> T:
        # `asyncio.run_coroutine_threadsafe(coro, loop).result(timeout_s)`
        ...
```

**Lifecycle in `OpcuaDeviceProtocolPort`:**

- `start()`: `loop_thread.start()` + `loop_thread.run_coroutine(client.connect(), timeout_s=...)`.
- `stop()`: `loop_thread.run_coroutine(client.disconnect(), timeout_s=...)` + `loop_thread.stop(timeout_s=...)`.
- `read(target)`: `loop_thread.run_coroutine(node.read_value(), timeout_s=...)` + Codec-Decode.
- `write(target, command)`: Codec-Encode + `loop_thread.run_coroutine(node.write_value(variant), timeout_s=...)`.

**Teardown-Vertrag (Decision O-b normativ):**

- `OpcuaLoopThread.stop()` muss pending Tasks bei Bedarf
  cancellen, bevor der Loop stoppt. C2-Implementierung:
  - Sammelt `asyncio.all_tasks(loop)` via
    `loop.call_soon_threadsafe`.
  - Cancelt jede Task; wartet mit
    `asyncio.gather(*tasks, return_exceptions=True)` (Timeout 1 s).
  - Ruft `loop.call_soon_threadsafe(loop.stop)`.
  - `thread.join(timeout_s)`.
  - `loop.close()`.
- Falls `thread.join` den Timeout reisst, bleibt der
  Daemon-Thread aktiv; der Test-Prozess kann trotzdem
  beendet werden (Daemon-Semantik). Ein Warning-Log
  dokumentiert den Pfad fuer Debugging.

**Begruendung:**

- `asyncua` ist rein-async — kein Sync-Wrapper produktiv;
  ein adapter-interner Loop-Thread ist die einzige saubere
  Bridge zur Sync-`DeviceProtocolPort`-Surface aus ADR
  0030 §2.1.
- ADR 0030 §2.1-Konsequenz hat Welle 4 explizit als
  Pruefstelle benannt; Welle 4 liefert das Pattern
  produktiv.
- `run_coroutine_threadsafe(...).result(timeout)` ist
  Standard-asyncio-API mit klarer Timeout-Semantik —
  `TimeoutError` bei Timeout, original-Exception sonst.
  Damit ist die Fehler-Propagation an den Sync-Aufrufer
  sauber.
- Eigene Klasse `OpcuaLoopThread` statt inline in
  `_port.py`: das Marshal-Pattern ist Welle-4-spezifisch
  produktiv, kann aber von Welle 5 (DNP3/IEC, falls
  Spike — `asyncio-iec61850`/`pydnp3-async` o. ae.)
  und Welle 6 (Cross-Adapter-Hardening) reused werden.
  Single-Source-of-Truth lohnt sich.
- **Pattern-Praezedenz nicht im Repo**: `telemetry_otlp`
  ist single-threaded, `protocol_mqtt`-Loop ist paho-
  intern, `protocol_modbus` ist direkt-sync. Welle 4 ist
  die erste Konstruktion dieser Art. Folge-ADR-Pfad
  (Schaerfung-ohne-Supersede per ADR 0011) bleibt offen,
  falls die Konstruktion produktive Schwaechen zeigt.

**Konsequenz:** `OpcuaLoopThread` lebt unter
`src/grid_gym/adapters/driven/protocol_opcua/_loop_thread.py`
mit eigenem Test-Modul
`tests/unit/adapters/driven/protocol_opcua/test_opcua_loop_thread.py`
(start/stop idempotent, Teardown bei pending Tasks,
Cancellation-Semantik, Timeout-Propagation). Welle-6-
Schaerfung kann die Klasse nach
`src/grid_gym/adapters/driven/_async_bridge/` oder
aequivalent extrahieren, wenn Welle 5+ sie tatsaechlich
reusen; bis dahin bleibt sie Welle-4-lokal.

### 2.3 Decision O-c — Datatype-Set + Konvertierung Python ↔ `asyncua.ua.Variant` (final)

Erlaubter Datatype-Set in Welle 4:

- **`Boolean`** — Python `bool`.
- **`Int16`** — signed 16-bit, Python `int`.
- **`UInt16`** — unsigned 16-bit, Python `int`.
- **`Int32`** — signed 32-bit, Python `int`.
- **`UInt32`** — unsigned 32-bit, Python `int`.
- **`Float`** — IEEE-754 single precision, Python `Decimal` (via `repr(float_value)`).
- **`Double`** — IEEE-754 double precision, Python `Decimal` (via `repr(float_value)`).
- **`String`** — Python `str`.

`Byte`/`SByte`/`Int64`/`UInt64`/`DateTime`/`Guid`/
`ByteString`/`ExtensionObject` bleiben **Welle-6-
Schaerfungspfad** offen via ADR 0011.

**Konvertierung:** `asyncua.ua.Variant(value, VariantType.<Name>)`
mit konkretem `VariantType` aus Decision-O-c-Set;
Decode via `variant.Value` (Python-Native-Typ) + Cast
zu `Decimal` fuer Float/Double (Praezisions-Konvention
analog ADR 0032 §2.2).

**Begruendung:**

- Welle-4-Minimum reicht fuer produktive
  Wechselrichter-/Energiemeter-Profile (SOC in `Float`,
  Power in `Int32`, Status in `Boolean`, Seriennummer
  in `String`).
- `Int64`/`UInt64` sind in der Energie-Domain selten
  und brauchen Python-`int`-Roundtrip mit Range-Check
  (Decimal-Konversion verlustfrei); Schaerft sich erst
  bei konkretem Bedarf.
- `DateTime` ist OPC-UA-spec-konform fuer Zeitstempel,
  aber Welle-4-Adapter erhaelt Zeitstempel aus
  ADR-0030-§2.2-`ClockPort` (SimulationTime), nicht aus
  OPC-UA-Servern; das vermeidet `AC-NO-TIME`-Drift im
  Adapter.
- `Guid`/`ByteString`/`ExtensionObject` sind OPC-UA-
  spec-Sonderfaelle (UUID-Identifier, Binary-Payload,
  benutzerdefinierte Strukturen); kein Welle-4-Use-Case.
- `Float`/`Double` -> `Decimal` via `repr(float_value)`
  ist Konsistenz mit ADR 0032 §2.2 Modbus-Codec
  (gleiche Praezisions-Wahl).

**Konsequenz:** `_codec.py`-Modul (`encode_value_to_variant`
+ `decode_variant_to_value`-Funktionen) konvertiert
zwischen `(value: int | Decimal | bool | str, datatype:
OpcuaDatatype)` und `asyncua.ua.Variant`. Codec hat
eigene typed Errors fuer (a) Out-of-Range-Werte (Integer-
Datatypes), (b) NaN/Infinity bei `Float`/`Double`,
(c) Typ-Mismatch bei `encode` (z. B. `str` zu `Int32`),
(d) Variant-Type-Mismatch beim Decode. Pattern analog
`_codec.py`-Modul aus Welle 3.

### 2.4 Decision O-d — Polling-Read + Direct-Write via asyncua-API (final)

**Read-Pfad (`access: "read"`):**

```python
async def _read_node(self, target: str, node_cfg: OpcuaNodeConfig) -> Decimal | int | bool | str:
    node = self._client.get_node(node_cfg.node_id)
    variant: ua.Variant = await node.read_value()
    return decode_variant_to_value(variant, node_cfg.datatype)
```

**Write-Pfad (`access: "write"`):**

```python
async def _write_node(self, target: str, command: Command) -> None:
    node_cfg = self._resolve_node_config(target)
    variant = encode_value_to_variant(command.payload["value"], node_cfg.datatype)
    node = self._client.get_node(node_cfg.node_id)
    await node.write_value(variant)
```

Beide Coroutinen werden via `OpcuaLoopThread.run_coroutine`
gemarshalt (Decision O-b).

**Subscription-Pfad (verschoben auf Welle 6):**

OPC-UA-Subscription-basiertes Reading (`Subscription.subscribe_data_change`
+ Monitored Items) ist effizienter als Polling-Read fuer
Hochfrequenz-Telemetry, bringt aber:

- Lifecycle-Komplexitaet (Subscription-Setup in `start()`,
  Cleanup in `stop()`, Reconnect-Resubscribe-Logik).
- Callback-Marshal-Pattern (asyncua-Subscription-Callbacks
  feuern aus dem Loop-Thread; Daten muessten via Queue
  an `read()` zurueck).
- Snapshot-Drift-Risiko (Subscription-State persistiert
  sich, ist aber volatile per ADR 0030 §2.3).

Welle 4 verzichtet bewusst; Welle 6 (Cross-Adapter-
Hardening) oder eine Folge-ADR (`ADR-0011`-Pattern)
fuehrt den Subscription-Pfad ein, falls Welle 6 zeigt,
dass Polling-Read die Tick-Latenz sprengt.

**Begruendung:**

- Polling-Read passt **direkt** in das aus Welle 3
  (Modbus, direkt-sync) etablierte Pattern: `read(target)`
  ruft eine Coroutine, die unmittelbar einen einzelnen
  Server-Roundtrip macht. Tick-Latenz-Implikation analog
  Welle-3-Decision-M-c (typische OPC-UA-Roundtrip-Latenz
  5–50 ms).
- Subscription-Pfad ist erheblich komplexer und nicht
  Welle-4-Minimum-Material.
- `write_value(variant)` ist atomar gegenueber dem
  OPC-UA-Server; FC-Mapping wie in Modbus existiert
  nicht (OPC-UA hat ein einheitliches Read/Write-Modell).

**Konsequenz:** `_port.py`-`read()` ruft direkt
`OpcuaLoopThread.run_coroutine(self._read_node(...))`;
`write()` analog. Kein Function-Code-Dispatcher (anders
als Modbus); keine Subscription-Lifecycle. `_port.py`
ist signifikant einfacher als `protocol_mqtt/_port.py`
(keine Callback-Queue) und vergleichbar mit
`protocol_modbus/_port.py` (kein Dispatcher), aber mit
dem zusaetzlichen Marshal-Layer aus Decision O-b.

**Reconnect-Verhalten:** asyncua wirft
`asyncua.ua.uaerrors.BadNotConnected` oder
`asyncio.TimeoutError` bei Verbindungs-Verlust waehrend
`read()`/`write()`. Diese werden in typed
`OpcuaPortReadFailedError`/`OpcuaPortWriteFailedError`
umgemantelt (analog Slice-031-Pattern aus M4-Welle-3
fuer Modbus). Welle 4 macht **keinen** Auto-Reconnect-
Loop — Caller-Pflicht, falls noetig.

### 2.5 Decision O-e — In-Process `asyncua.Server` fuer Integration-Smoke (final)

**Test-Sibling-Variante in Welle 4:** **in-process
`asyncua.Server`** im Test-Code
(`tests/integration/test_opcua_in_process_smoke.py`),
**kein** testcontainers-Container.

**Setup:**

```text
1. Test setzt einen `asyncua.Server` mit Node-Default-
   Werten auf (Endpoint `opc.tcp://localhost:<port>`).
2. Eigener Test-internes Loop-Thread-Konstrukt
   (`_InProcessOpcuaServer` in
   `tests/integration/test_opcua_in_process_smoke.py`) mit
   `asyncio.new_event_loop()` + `Thread(daemon=True)`
   spawnt den Server-Loop. Slice-032-Schaerfung (Welle-4-
   Review-Folge Finding 6.3): Test verwendet **bewusst
   NICHT** die produktive `OpcuaLoopThread`-Klasse —
   der Server-Lifecycle (asyncio.Event-basiertes Stop-
   Signal + `server.stop()`-Coroutine) ist substanziell
   anders als der Client-Lifecycle (Connect/Disconnect),
   und Test-Server-Loop-Logik gehoert nicht in die
   produktive `OpcuaLoopThread`-Surface.
3. Test wartet via Connect-Check (`_wait_for_port_open`)
   bis Server bereit ist; Init-Errors werden im Thread
   gecaped und im Caller reraised (Slice-032 Finding 7.3).
4. End-to-End-Read/Write-Roundtrip via
   `OpcuaDeviceProtocolPort` durch alle 8 Datatypes
   (Decision-O-c-Set).
5. Teardown: `server.stop()`-Coroutine + `stop_signal.set()`
   + `loop.stop()` + `thread.join(timeout=5.0)`.
```

**Begruendung:**

- **Lizenz-Sicherheit:** OPC-UA-Server-Container-
  Optionen:
  - `open62541/open62541` ist MPL-2.0 (Mozilla Public
    License) — redistributable, aber nicht-trivial in
    der Container-Konfiguration (eigenes
    `nodeset`-Setup, Anonymous-Endpoint manuell).
  - `OPCFoundation/UA-CPPServer` ist RCL-Lizenz mit
    kommerziellem Pfad — nicht akzeptabel ohne
    Lizenz-Audit.
  - `prosysopc/prosys-opc-ua-simulation-server` ist
    proprietaer — nicht akzeptabel.

  `asyncua` selbst ist LGPL-3.0 (Library-Usage erlaubt
  unter MIT-konformem Linking; verifiziert per
  asyncua-PyPI-Metadata) und liefert einen produktiven
  Server in derselben Library mit. Pattern-Praezedenz
  Welle 3 (pymodbus liefert Server, BSD-3-Clause).
- **CI-Latenz:** Kein Docker-Image-Pull, kein
  Container-Boot-Wait. Der asyncua-Server kommt in
  derselben Python-Runtime hoch.
- **Realitaet:** asyncua-Server implementiert die OPC-
  UA-Spec-Funktionen, die der asyncua-Client abruft —
  Tests pruefen damit `client <-> server`-Compatibility
  innerhalb derselben Library (gleiche Konsistenz wie
  Welle 3 pymodbus).
- **Praezedenz:** M2-Welle-6c-Postgres-Sibling +
  M4-Welle-2-Mosquitto-Sibling sind Container-basiert,
  weil produktive Server (Postgres, Mosquitto) im
  Test-Container leichter zu fahren sind als als
  Library. OPC-UA folgt der Welle-3-Modbus-Logik
  umgekehrt: asyncua liefert sowohl Client als auch
  Server, und das Server-Modul ist produktiv-stabil.

**Konsequenz:**

- **Keine `tests/integration/compose.yml`-Erweiterung**
  in Welle 4. Header-Kommentar (C2 EDIT) dokumentiert
  die bewusste Entscheidung als Pattern-Fortfuehrung
  aus Welle 3 (in-process-Server-Pattern als
  Praezedenz fuer Welle 5 DNP3/IEC, falls Spike).
- **Keine testcontainers-`DockerContainer`-Fixture.**
- **Daemon-Loop-Thread-Lifecycle:** der Test verwendet
  eigene `OpcuaLoopThread`-Instanz fuer den Server
  (separat vom Client-Adapter-Loop-Thread); beide werden
  geordnet abgebaut.
- **Port-Auswahl:** `0` (OS waehlt freien Port) oder
  fester Hoch-Port (z. B. `14840`) — C2-Entscheidung;
  Default-Vorschlag fester Port fuer Reproduzierbarkeit
  in Debug-Sessions.
- **Endpoint-Sicherheit:** Anonymous-Endpoint
  (`SecurityPolicy.None`); kein User/Password/X509
  fuer den Welle-4-Smoke. OPC-UA-Security ist Welle-6-
  Material oder eigener M6-Slice (`GG-SAFE-*`).

---

## 3. Alternativen

**A1 (verworfen) — Separate `opcua_profiles`-Top-Level-
Section:** wuerde Decision O-a auf eine eigene Schluessel-
Section verlagern. Verworfen wegen YAGNI (siehe ADR 0031
§3 A1 und ADR 0032 §3 A1; Welle-4-Scenarios haben
dieselbe Skalierung wie Welle-2/3-Scenarios — ≤ 10
Targets pro Adapter).

**A2 (verworfen) — Per-Call `asyncio.run(coro)` ohne
persistenten Loop:** wuerde fuer jeden `read()`/`write()`
einen frischen Event-Loop aufsetzen. Verworfen, weil
`asyncua.Client.connect()` einen Session-State haelt, der
zwischen Calls persistieren muss; per-Call-Loop wuerde
bei jedem Call neu connecten — quadratisch teurer und
incompatible mit Subscription-Pfaden (Welle 6).

**A3 (verworfen) — Datatype-Set inklusive `Int64`/
`Double`-Erweiterung + `DateTime`/`Guid`/`ByteString`
ab Welle 4:** wuerde Welle-4-Codec-Komplexitaet
verdoppeln (8 → 13+ Datatypes mit Sonderfall-
Konvertierungen). Verworfen wegen YAGNI; ADR-0011-
Schaerfungspfad bleibt offen.

**A4 (verworfen) — Subscription-First-Pfad (Monitored
Items + `subscribe_data_change`) ab Welle 4:** wuerde
Subscription-Lifecycle + Callback-Marshal-Pattern in
Welle 4 erzwingen. Verworfen — Welle 4 deckt Polling-
Read (Pattern aus Welle 3 fortgefuehrt); Subscription
bleibt Welle-6-Schaerfung mit konkretem Latenz-Beleg.

**A5 (verworfen, nach Lizenz-Pruefung) — testcontainers
`open62541/open62541` als Sibling:** waere konsistent
mit Welle-2-Mosquitto-Pattern. Verworfen wegen:
- MPL-2.0 ist redistributable, aber Container-Setup
  ist nicht-trivial (eigenes Nodeset, Anonymous-Endpoint-
  Config-Manipulation).
- Welle-3-Praezedenz hat in-process-Pattern etabliert;
  Welle 4 setzt den Pfad fort.
- in-process ist schneller in CI (kein Docker-Pull,
  kein Boot-Wait).

**A6 (verworfen) — Separater
`AsyncDeviceProtocolPort`-Schwester-Port:** wuerde einen
eigenen async-`Protocol`-Vertrag fuer rein-async-Stacks
einfuehren (TickLoop-Konstruktor-Kwarg zusaetzlich zu
`protocol_ports`). Verworfen — ADR 0030 §2.1 hat den
Sync-Vertrag bewusst als universellen Vertrag gewaehlt,
mit Adapter-internem Marshal als Konsequenz.
Schwester-Port-Pfad ist via ADR-0011-Schaerfung **offen**,
aber Welle 4 muss zuerst das Default-Pattern produktiv
testen. Falls Welle 4 zeigt, dass Thread+Loop-Marshal
operativ unpraktikabel ist, kann Welle 6 die Schwester-
Port-ADR ziehen.

**A7 (verworfen) — `asyncua.sync`-Submodule als
Sync-Wrapper:** asyncua liefert eine experimentelle
`asyncua.sync`-Submodule, die das Async-API in eine
Sync-Fassade wrappt. Verworfen, weil:
- `asyncua.sync` ist als „experimentell" markiert
  (asyncua-Doku) und API-instabil zwischen Minor-
  Versionen.
- Eigene Thread+Loop-Konstruktion ist transparent,
  testbar und unter Welle-4-Kontrolle.
- Pattern-Praezedenz fuer Welle 5+ liefert nur die
  selbst-gebaute Konstruktion (asyncua.sync ist asyncua-
  spezifisch und nicht reusable).

**A8 (verworfen) — Eigener Mini-OPC-UA-Server im
Test-Code:** waere komplett unabhaengig von asyncua-
Server-API-Drift, aber duplexte OPC-UA-Spec im
Test-Code. Verworfen — asyncua-Server ist LGPL-3.0
+ produktiv-stabil; Re-Implementation waere unnoetige
Wartungslast (analog ADR 0032 §3 A8 fuer pymodbus).

---

## 4. Konsequenzen

- **Welle-4-C2-Implementierungs-Pflicht** (`feat(welle-4):
  protocol_opcua + Tests + In-Process-Smoke +
  Compose-Edit`):
  - NEU `src/grid_gym/adapters/driven/protocol_opcua/__init__.py`
    mit `OpcuaDeviceProtocolPort` als
    `DeviceProtocolPort`-Implementer (ADR 0030 §2.1).
  - NEU `src/grid_gym/adapters/driven/protocol_opcua/_config.py`
    (`OpcuaProtocolPortConfig` + `OpcuaNodeConfig`
    frozen-dataclasses, Decision O-a/O-c-Schema;
    `OpcuaDatatype`-Enum mit 8 Werten).
  - NEU `src/grid_gym/adapters/driven/protocol_opcua/_codec.py`
    (`encode_value_to_variant` /
    `decode_variant_to_value`-Funktionen, Decision O-c).
  - NEU `src/grid_gym/adapters/driven/protocol_opcua/_loop_thread.py`
    (Decision O-b `OpcuaLoopThread`-Klasse + Marshal-
    Helper; geordneter Teardown-Vertrag).
  - NEU `src/grid_gym/adapters/driven/protocol_opcua/_port.py`
    (Decision O-b/O-d direkt-Polling-Read + Direct-
    Write; Lifecycle; asyncua-Exception-Translation).
  - NEU `src/grid_gym/adapters/driven/protocol_opcua/_errors.py`
    (typed `DeviceProtocolPort*Error`-Subclasses
    inkl. Read/Write-Operation-Tax analog Slice-031-
    Pattern: `OpcuaPortReadNotStartedError`,
    `OpcuaPortWriteNotStartedError`,
    `OpcuaPortReadAccessMismatchError`,
    `OpcuaPortWriteAccessMismatchError`,
    `OpcuaPortReadFailedError`,
    `OpcuaPortWriteFailedError`,
    `OpcuaPortMissingCommandPayloadError` etc.).
  - **Modul-Docstring** mit Lastenheft-Z. 1161–1163-
    Pflicht: „Simulations-/Testadapter; keine
    produktive Anlagensteuerung". Cross-Cutting-Pflicht
    ist Adapter-spezifisch (Welle 6 prueft sweepartig
    fuer alle `protocol_*`-Module).
  - 4 Unit-Test-Module unter
    `tests/unit/adapters/driven/protocol_opcua/`.
  - 1 Integration-Smoke unter
    `tests/integration/test_opcua_in_process_smoke.py`
    (Decision O-e).
- **`tests/integration/compose.yml`-Header-Kommentar-
  Sync (C2 EDIT):** dokumentiert die bewusste Decision-
  O-e-Wahl (in-process-Smoke; kein neuer Sibling-
  Service) als Pattern-Fortfuehrung aus Welle 3.
- **`pyproject.toml`-Erweiterung:** `asyncua>=1.1,<2.0`
  in `[project] dependencies`. Pin `<2.0` schuetzt
  gegen Major-API-Drift. `asyncua`-Eintrag in den
  AC-PORTS-NO-FW- und AC-NO-FW-Forbidden-Listen ist
  Welle-0-vorbelegt — Welle-4-C1 prueft ggf.
  Erweiterung fuer asyncua-Submodulen.
- **`Dockerfile`-Erweiterung:** `CRITICAL_COV_TARGETS`-
  Default um `src/grid_gym/adapters/driven/protocol_opcua`
  erweitert (Pattern analog `protocol_mqtt`/
  `protocol_modbus`-Eintraege aus M4-Welle-2-C2
  `f33bb4e` und M4-Welle-3-C2 `d721982`). `make gates`
  cache-frei gruen ohne `CRITICAL_COV_TARGETS`-Override.
- **`AC-ADAPTER-LIGHTWEIGHT` greift unveraendert**
  (`tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`). Welle 4 muss nur
  Smoke-Regression-Schutz pruefen — der Welle-1-§7-
  Folge-Pflicht-Planted-Violator-Property-Test bleibt
  Welle-6-Material (Pattern fortgefuehrt aus Welle 2/3).
- **Scenario-Loader bleibt OPC-UA-frei** (AC-HEXAGON-
  PURE): analog zur Welle-2/3-Konsequenz aus ADR 0031 §4
  / ADR 0032 §4 (`hexagon/core/scenario/loader.py` darf
  `OpcuaProtocolPortConfig` nicht direkt parsen;
  Adapter-Plugin-Pattern).
- **Caller-Scope-Lifecycle bleibt ADR-0030-Vertrag:**
  Caller wrappen `loop.start_protocol_ports()` /
  `loop.stop_protocol_ports()` in `try/finally` um
  die Tick-Schleife. OPC-UA-Adapter haengt sich
  identisch zum MQTT-/Modbus-Adapter in dieses Pattern
  ein; **keine** Aenderung an TickLoop.
- **Snapshot-Vertrag bleibt v2** (ADR 0030 §2.3):
  OPC-UA-Adapter ist stateless aus Replay-Sicht;
  Reconnect-State (TCP-Socket + asyncua-Session) ist
  volatile. Reversibilitaet via ADR-0015-Pattern.
- **OTel-Span-Wrap der Adapter-Calls:** ADR 0033 wrappt
  Adapter-Calls **nicht** mit OTel-Spans. Welle 6 ist
  der Zeitpunkt fuer den `TracePort`-Wrap (ADR 0024
  §2.4 als Bezug; Pattern fortgefuehrt aus Welle 2/3).
- **OPC-UA-Subscription-Pfad als Welle-6-Schaerfung
  reserviert:** falls Welle 6 (Cross-Adapter-Hardening)
  oder eine M6-Performance-Welle zeigt, dass Polling-
  Read die Tick-Latenz sprengt, kann eine Folge-ADR
  (ADR-0011-Pattern) den Subscription-Pfad einfuehren —
  inkl. Callback-Marshal-Queue (Pattern aus Welle 2 MQTT
  Decision 4d reusable) und Subscription-Lifecycle in
  `start()`/`stop()`.
- **Async-Bridge-Reversibilitaet:** falls die Decision-
  O-b-Thread+Loop-Konstruktion operativ unpraktikabel
  ist (z. B. Teardown-Race nicht handhabbar, Cancellation-
  Semantik instabil), kann Welle 6 eine Schaerfungs-ADR
  ziehen — entweder mit async-`Protocol`-Ergaenzung zu
  `DeviceProtocolPort` oder mit dediziertem
  `AsyncDeviceProtocolPort`-Schwester-Port (siehe
  ADR 0030 §2.1-Konsequenz). Welle 4 dokumentiert die
  direkt-async-Wahl explizit als reversibel.
- **Welle-5-Implementer-Auflage (DNP3/IEC-Disposition):**
  Welle 5 entscheidet Verzicht (Default) vs. Spike
  (Opt-In) informiert durch Welle-4-Erfahrung mit dem
  asyncua-Thread+Loop-Pattern. Falls Welle 4 zeigt, dass
  das Pattern produktiv tragfaehig ist, ist der DNP3/
  IEC-Spike-Pfad operativ realistisch (mit
  `OpcuaLoopThread`-aequivalentem Reuse). Falls Welle 4
  Schmerzen zeigt, ist der Verzicht-Pfad der saubere
  Weg.
- **Welle-6-Implementer-Auflagen:**
  - OTel-Span-Wrap fuer alle `protocol_*`-Adapter
    (Welle-2/3/4-bewusst-verschoben).
  - `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-Property-
    Test (Welle-1-§7-Folge-Pflicht).
  - OPC-UA-Subscription-Pfad (optional, je nach Bedarf).
  - Cross-Adapter-Profil-Index unter
    `spec/protocol_profiles/`.

---

## 5. Status-Pfad

- **Proposed** — 2026-05-31 (M4-Welle-4-C1 `74ed35b`).
  Initial-Entwurf; Review-Schleife offen.
- **Provisional** — 2026-05-31 (M4-Welle-4-C3 `7ad5baf`)
  nach C2-Merge `78fdd7a` (feat-Commit:
  `protocol_opcua/`-6-Modul-Paket — `__init__.py` +
  `_config.py` + `_codec.py` + `_loop_thread.py` +
  `_port.py` + `_errors.py` — mit 81 neuen Unit-Tests
  (10 Config-Validation + 34 Codec-Roundtrip inkl.
  hypothesis-Property-Tests + 9 Loop-Thread-Lifecycle +
  16 Protocol-Port-Lifecycle/Read+Write mit AsyncMock +
  8 In-Process-Integration-Smoke parametrisiert ueber
  alle 8 Datatypes); `pyproject.toml`-Pin
  `asyncua==1.2b2` (Beta-Release wegen Python-3.14-
  Forward-Reference-Inkompat in 1.1.8) + mypy-Override
  `implicit_reexport=true` fuer `asyncua.*`;
  `uv.lock`-Refresh mit 108 packages (asyncua 1.1.8
  -> 1.2b2 + 8 transitive Deps); `Dockerfile`-Edit
  (`CRITICAL_COV_TARGETS` um
  `adapters/driven/protocol_opcua` erweitert);
  `compose.yml`-Header-Kommentar-Sync zu Decision-O-e
  in-process-asyncua-Server. Verifikation cache-frei:
  `make test-unit` 1395 gruen, `make test-integration`
  31 gruen (23 → 31, +8 OPC-UA-Roundtrips), `make
  arch-check` 19/19 KEPT, `make gates` 9 A-1-Gates
  gruen ohne `CRITICAL_COV_TARGETS`-Override.
- **Slice-032-Schaerfung** — 2026-05-31 (Welle-4-Review-
  Folge,
  [`done/032-opcua-adapter-review-folge.md`](../planning/done-archive/032-opcua-adapter-review-folge.md)).
  ADR bleibt `Provisional`, Body geschaerft an drei
  Stellen: §2.1 Konsequenz (Optional-Felder
  `namespace_index`/`identifier_type` aus dem Schema
  entfernt; Welle-4-YAGNI), §2.5 Setup-Skizze (Test-
  Server-Loop ist bewusst getrennt von der produktiven
  `OpcuaLoopThread`-Klasse), §2.2 Doku-Drift zum
  `loop.close()`-Konditional. Code-Schaerfungen
  (Lifecycle-Lock, Start-Timeout, Exception-Filter-
  Erweiterung, String-Read-Quality.INVALID,
  Float-32bit-Quantisierung, Surrogate-Blacklist) in
  separatem feat-Commit.
- **Accepted** — 2026-06-01 mit M4-Welle-7-C1 (dieser
  Commit, M4-Closure-Welle; analog ADR 0022..0027 + 0030
  + 0031 + 0032). Voraussetzung erfuellt: Welle 5a
  (DNP3, ADR 0034), Welle 5b (IEC-61850, ADR 0035) per
  ADR-0011-Pattern dokumentiert; Welle 6a (Cross-Adapter-
  OTel-Span-Wrap) und Welle 6b (GPL-Boundary) sind
  orthogonal zur Thread+Loop-Konstruktion — keine
  Schwester-Port-ADR notwendig (`OpcuaLoopThread`-Pattern
  ist OPC-UA-spezifisch und bleibt in §2.5 dokumentiert).
  Welle 6 prueft, ob die Thread+Loop-Konstruktion Welle-6-
  Schaerfungs-Bedarf zeigt (Schwester-Port-ADR vs.
  Reuse-as-is). Folge-Pflicht: asyncua-Pin auf
  `>=1.2,<2.0` ziehen, sobald 1.2 final auf PyPI ist
  (Welle-6- oder M6-Material).
