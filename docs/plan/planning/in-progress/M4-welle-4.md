# Welle 4 — M4 OPC-UA-Adapter

**Status:** In Progress — eroeffnet 2026-05-31 nach
M4-Welle-3-Closure (`8ef1e72` C0 + `a86ac46` C1 + `d721982`
C2 + `2b84361` EoD-Sync + `0ce578a` C3 + `506c8ca`
Self-Close-Move + `0ab956a` Slice-031-feat + `faa3ecc`
Slice-031-docs). Welle 4 ist die **vierte Code-Welle** in
M4 und der **dritte konkrete Adapter** auf der
`DeviceProtocolPort`-Surface (`GG-AR-PORT-DRN-007`):
OPC-UA ueber `asyncua`. Welle 4 traegt erstmals einen
**rein-async-Stack** produktiv vor — ADR 0030 §2.1 hat
die Sync-Surface-Brueckenkonstruktion fuer asyncua bereits
vorbelegt (Thread+Loop-Marshal); Welle 4 implementiert sie
konkret und etabliert das Pattern fuer Welle 5 (DNP3/IEC,
falls Spike).

Kanonische Slice-Spezifikation:
[`M4-protocol-adapters.md §3 Welle 4`](M4-protocol-adapters.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht Ersatz.

**Spec-Reife:** Inhaltlich final fuer Decisions O-a/O-c/O-d
(Node-ID-Schema, Datentyp-Set, Read/Write-Pfad). Decision
O-b (async->sync-Bridge) und Decision O-e (Test-Sibling)
werden in C1 (ADR 0033 Proposed) konkret gewaehlt; C2
(feat) implementiert die gewaehlte Variante.

---

## 1. Context

M4-Welle-2 hat den ersten konkreten `DeviceProtocolPort`-
Implementer produktiv geliefert (`MqttDeviceProtocolPort`,
ADR 0031 `Provisional`) ueber `paho-mqtt 2.x` (sync-Client
mit internem Loop-Thread + Callback-Boundary).

M4-Welle-3 hat den zweiten konkreten Implementer geliefert
(`ModbusDeviceProtocolPort`, ADR 0032 `Provisional`) ueber
`pymodbus 3.x` (sync-Client direkt — **kein** Thread-
Marshal noetig, Decision M-c). Slice-031-Folge hat
FC06-Datatype-Guard + Read/Write-Fehler-Taxonomie
nachgezogen.

Welle 4 ist der **dritte konkrete Implementer**:

- NEU `src/grid_gym/adapters/driven/protocol_opcua/`-Modul
  mit `asyncua`-Wrapper als `DeviceProtocolPort`-Implementer
  (`GG-OPCUA-001`).
- NEU ADR 0033 (OPC-UA-Adapter-Profile) als Surface-
  relevanter Adapter-ADR. OPC-UA-spezifische Decisions:
  Node-ID-Schema, async->sync-Bridge-Konstruktion,
  Datentyp-Set, Read/Write-Pfad, Test-Sibling-Variante.
  Pattern-Praezedenz
  [`ADR 0031`](../../adr/0031-mqtt-adapter-profile.md) §2.1
  (inline-Profile) + [`ADR 0032`](../../adr/0032-modbus-adapter-profile.md) §2.1
  (Adapter-Konfig-Schema); ADR-0011-Konvention (Schaerfung-
  ohne-Supersede).
- NEU Integration-Smoke — Variante wird in C1 nach
  Lizenz-Pruefung (`open62541` Sibling vs. in-process
  `asyncua.Server`) festgelegt. Welle-3-Decision-M-f-Pattern
  (in-process-Server) ist die bevorzugte Variante, weil
  `asyncua` selbst sowohl Client als auch Server in einer
  Library liefert.

**Async-Stack-Forderung:** ADR 0030 §2.1-Konsequenz
nennt Welle 4 explizit als die Stelle, an der das
Thread+Loop-Marshal-Pattern produktiv vorgetragen wird:

> Welle 4 (OPC-UA) tragt die Thread+Loop-Konstruktion fuer
> einen rein-async-Stack zum ersten Mal real. Falls sich
> dort die Wahl als zu schmerzhaft erweist, schaerft eine
> Folge-ADR den Vertrag (Schaerfung-ohne-Supersede per
> ADR 0011) — entweder durch async-`Protocol`-Ergaenzung
> oder durch dedizierten `AsyncDeviceProtocolPort` als
> **Schwester-Port**.

Welle 4 ist diese Pruefstelle: scheitert der adapter-
interne Thread+Loop-Marshal an einem operativen Problem
(z. B. asyncio-Cancellation-Semantik im teardown,
Backpressure-Drift, Cleanup-Race), ist die Wahl
**reversibel** ueber eine Welle-6-Schaerfungs-ADR. Welle 4
implementiert die in ADR 0030 §2.1 begruendete
Default-Wahl und dokumentiert Reversibilitaet im ADR-0033-
Konsequenzen-Block.

**Decision-O-b-Konstruktion (Skizze, finale Wahl in C1):**

Der Adapter haelt einen dedizierten `asyncio.AbstractEventLoop`
in einem Daemon-Thread, der bei `start()` aufgesetzt und bei
`stop()` mit `loop.call_soon_threadsafe(loop.stop)` +
`thread.join(timeout=...)` sauber abgebaut wird. Sync-
Aufrufe von `read()` und `write()` marshalen via
`asyncio.run_coroutine_threadsafe(coro, loop).result(timeout)`.
Pattern-Praezedenz ist nicht im Repo (`telemetry_otlp`
ist single-threaded, `protocol_mqtt`-Loop ist paho-intern,
`protocol_modbus` ist direkt-sync), aber Standard-asyncua-
Doku „Synchronous wrapper" zeigt den Pfad.

---

## 2. Scope

**In Scope:**

1. NEU `docs/plan/adr/0033-opcua-adapter-profile.md` in C1
   als `Proposed`. Entscheidungen:
   - **Decision O-a (Node-ID-Schema, final)**: Node-ID-
     Profil-Deklaration **inline** im `protocol_ports`-
     Scenario-YAML-Block (Pattern-Praezedenz ADR 0031 §2.1
     + ADR 0032 §2.1). Pro `device_id` ein
     `OpcuaNodeConfig` mit Pflicht-Feldern
     `node_id`/`datatype`/`access`; Optional-Feldern
     `namespace_index`/`identifier_type`.
   - **Decision O-b (Async-Bridge, in C1 fixiert)**:
     Adapter-interner asyncio-Loop in eigenem Daemon-Thread
     (`start()` spawnt; `stop()` schliesst geordnet ab) +
     `run_coroutine_threadsafe`-Marshal in
     `read()`/`write()`. Alternative ware ein per-Call
     `asyncio.run(...)` (schlechter Fit fuer Verbindungs-
     persistenz, deshalb verworfen).
   - **Decision O-c (Datatype-Set, in C1 fixiert)**:
     Erlaubter OPC-UA-Built-In-Types-Set als Welle-4-
     Minimum (`Boolean`, `Int16`, `UInt16`, `Int32`,
     `UInt32`, `Float`, `Double`, `String`). `Byte`/
     `SByte`/`Int64`/`UInt64`/`DateTime`/`Guid`/
     `ByteString`/`ExtensionObject` bleiben Welle-6-
     Schaerfungspfad offen via ADR 0011. Konvertierung
     zu Python-`Decimal`/`int`/`str`/`bool` analog
     ADR 0032 §2.2-Pattern (`Decimal` aus `repr` fuer
     Float-Praezision).
   - **Decision O-d (Read/Write-Pfad, final)**:
     Telemetry-Reads ueber `client.get_node(node_id).read_value()`
     (async-Coroutine, gemarshalled via O-b). Command-
     Writes ueber `node.write_value(value, varianttype)`.
     Subscription-Pfad (Monitored Items, `Subscription.subscribe_data_change`)
     bleibt Welle-6-Schaerfung offen — Welle 4 deckt
     Polling-Read + Direct-Write ab (analog
     ADR 0032 §2.3).
   - **Decision O-e (Test-Sibling, in C1 fixiert)**:
     Wahl zwischen testcontainers (`open62541/open62541`
     o. ae. — Lizenz **vor C1** pruefen) und **in-process
     `asyncua.Server`** (Pattern-Praezedenz Welle-3-
     Decision-M-f). Bevorzugte Wahl ist in-process,
     weil `asyncua` (LGPL-3.0) selbst sowohl Client als
     auch Server liefert; `open62541/open62541`-Image-
     Lizenz ist Mozilla MPL-2.0 (verifizierungsbeduerftig
     in C1).
2. NEU
   `src/grid_gym/adapters/driven/protocol_opcua/__init__.py`:
   `OpcuaDeviceProtocolPort`-Klasse als
   `DeviceProtocolPort`-Implementer.
   - `start()`: spawnt Daemon-Thread mit
     `asyncio.new_event_loop()` + `run_forever()`;
     marshalled `client.connect()` (async) ueber
     `run_coroutine_threadsafe`. Idempotent (zweiter
     Aufruf no-op, wenn bereits laufend).
   - `stop()`: `client.disconnect()` (async, gemarshalled)
     + `loop.call_soon_threadsafe(loop.stop)` +
     `thread.join(timeout=5.0)`. Idempotent.
   - `read(target)`: Lookup `OpcuaNodeConfig` per
     `device_id`; `await client.get_node(node_id).read_value()`
     (gemarshalled); OPC-UA-Variant zu Python-Typ via
     Decision-O-c-Codec; `TelemetryPoint` verpacken.
   - `write(target, command)`: Lookup `OpcuaNodeConfig`;
     `command.payload['value']` zu OPC-UA-Variant via
     Codec; `await node.write_value(variant)` (gemarshalled).
   - Modul-Docstring mit Lastenheft-Z. 1161–1163-Pflicht:
     **„Simulations-/Testadapter; keine produktive
     Anlagensteuerung"**.
3. NEU
   `src/grid_gym/adapters/driven/protocol_opcua/_config.py`
   mit `OpcuaProtocolPortConfig` + `OpcuaNodeConfig`-
   frozen-dataclasses; Konstruktor-Validation mit
   `OpcuaConfigError`-Familie (analog
   `ModbusConfigError`-Familie aus Welle 3).
4. NEU
   `src/grid_gym/adapters/driven/protocol_opcua/_codec.py`
   mit `encode_value_to_variant` /
   `decode_variant_to_value`-Helfern (Datentyp-Konvertierung
   zwischen Python `Decimal|int|float|bool|str` und
   `asyncua.ua.Variant`). Asymmetrie analog ADR 0032 §2.2:
   Encoding strikt mit typed Errors, Decoding tolerant
   mit `OpcuaCodecDecodeError` am Adapter-Rand.
5. NEU
   `src/grid_gym/adapters/driven/protocol_opcua/_loop_thread.py`
   mit `OpcuaLoopThread`-Klasse: kapselt
   `asyncio.new_event_loop()` + `threading.Thread(daemon=True)`
   + `run_coroutine_threadsafe`-Helper. Erste Pattern-
   Konstruktion fuer Welle 5+ (DNP3/IEC, falls Spike) und
   Welle 6 (Cross-Adapter-Hardening).
6. NEU
   `src/grid_gym/adapters/driven/protocol_opcua/_port.py`
   mit `OpcuaDeviceProtocolPort`-Hauptklasse (Decision O-b
   Lifecycle + Decision O-d Dispatcher; asyncua-Exception-
   Translation).
7. NEU
   `src/grid_gym/adapters/driven/protocol_opcua/_errors.py`
   mit typed `DeviceProtocolPort*Error`-Subclasses fuer
   Connect/Disconnect/Read/Write/Unknown-Target;
   Pattern analog `protocol_modbus/_errors.py` aus
   Slice-031-Folge (Read/Write-Operation-spezifische
   Subclasses unter Catch-All-Basen).
8. Unit-Tests unter
   `tests/unit/adapters/driven/protocol_opcua/`:
   - `test_opcua_config.py`: Konstruktor-Validation
     (Datatype-Allowlist, Node-ID-Format,
     Namespace-Index-Range).
   - `test_opcua_codec.py`: Datentyp-Roundtrip pro
     Welle-4-Type (Boolean/Int16/UInt16/Int32/UInt32/
     Float/Double/String) mit `asyncua.ua.Variant`-
     Roundtrip; hypothesis-Property-Tests fuer numerische
     Typen.
   - `test_opcua_loop_thread.py`: `OpcuaLoopThread`-
     Lifecycle (start/stop idempotent, geordnetes Teardown,
     Cancellation-Verhalten bei Exceptions).
   - `test_opcua_protocol_port.py`: Lifecycle + Read/
     Write gegen mocked `asyncua.Client` (AsyncMock).
9. NEU `tests/integration/test_opcua_*_smoke.py` (Name
   je nach Decision O-e — `test_opcua_in_process_smoke.py`
   bei in-process-Variante, `test_opcua_compose_smoke.py`
   bei testcontainers-Variante):
   - In-process: `asyncua.Server` in eigenem Daemon-Thread;
     End-to-End-Read/Write-Roundtrip durch Decision-O-c-
     Datatype-Set; expliziter `server.stop()`-Teardown.
   - testcontainers (Fallback): `open62541/open62541`-
     Image-Sibling mit Anonymous-Endpoint-Config.
10. EDIT `tests/integration/compose.yml`-Kommentar-Sync:
    Decision-O-e-Wahl dokumentieren (in-process oder
    Sibling-Service).
11. EDIT `pyproject.toml`: `asyncua>=1.1` in `[project]
    dependencies`. `asyncua`-Eintrag in den
    AC-PORTS-NO-FW/AC-NO-FW-Forbidden-Listen pruefen
    (Welle-0-Vorbelegung; ggf. Welle-4-C1-Edit).
12. EDIT `Dockerfile`: `CRITICAL_COV_TARGETS`-Default um
    `src/grid_gym/adapters/driven/protocol_opcua`
    erweitert (Pattern analog `protocol_mqtt`/
    `protocol_modbus`-Eintraege aus M4-Welle-2-C2 /
    M4-Welle-3-C2).
13. C3-Doc-Sync zieht `M4-welle-4.md`-Status auf `Done`
    und schaerft ADR 0033 von `Proposed` auf
    `Provisional`. (Endgueltige Akzeptanz erst mit
    M4-Welle-7-Closure.)
14. `make arch-check` weiter `19/19 Contracts KEPT` —
    `AC-ADAPTER-LIGHTWEIGHT` greift fuer `protocol_opcua`
    via `tools/arch_check.py:1089`
    `bucket.startswith("protocol_")`. Welle-1/2/3-Smoke-
    Regression-Schutz bleibt aktiv; Welle 4 prueft, dass
    der Filter den neuen `protocol_opcua/`-Pfad ohne
    Code-Aenderung erfasst.

**Anti-Scope:**

- **Keine DNP3-/IEC-Adapter** unter
  `src/grid_gym/adapters/driven/protocol_*/`. Welle 5
  DNP3/IEC-Disposition (Verzicht-Default oder Spike).
- **Kein OPC-UA-Subscription-Pfad** (Monitored Items,
  `Subscription.subscribe_data_change`) — Polling-Read
  reicht fuer Welle 4; Subscription bleibt Welle-6-
  Schaerfung offen via ADR 0011.
- **Kein OTel-Span-Wrap** der OPC-UA-Adapter-Calls.
  Span-Wrap-Pattern fuer `protocol_*`-Adapter ist Welle-6-
  Material (Cross-Adapter-Hardening; ADR 0024
  `TracePort` als Bezug).
- **Keine OPC-UA-Security** (UserNameIdentityToken,
  X509-Zertifikate, Encryption-Suites) — Welle-4-Smoke
  laeuft mit Anonymous-Endpoint. Security ist Welle-6-
  Material oder eigener M6-Slice (`GG-SAFE-*`).
- **Kein RandomPort-Determinismus** fuer Node-IDs oder
  Namespace-Indizes — Welle-4-Default-Werte reichen.
- **Keine Scenario-Schema-Erweiterung jenseits des
  Decision-O-a-Pattern**. Welle 4 fuegt **keinen** neuen
  Top-Level-YAML-Block hinzu; das Node-ID-Schema sitzt
  inline im `protocol_ports`-Block analog ADR 0031/0032.
- **Keine Welle-2-MQTT-/Welle-3-Modbus-Adapter-
  Aenderungen**. Welle-4-OPC-UA-ADR (0033) ist
  **Erweiterung**, kein Supersedes zu ADR 0031/0032.
- **Keine Bewegung der Open-Trigger** — Welle 4 schaerft
  keinen bestehenden Trigger; Trigger-006-Folge-Slice
  (`--strict-bytes`-Aktivierung) bleibt Welle-6-Material.
- **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md`.
  Welle 4 liefert 1 der 7 DoD-Items (`GG-OPCUA-001`);
  der DoD-Sweep folgt mit Welle 7.
- **Kein `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-
  Property-Test**. Die in M4-welle-1 §7 als Folge-Pflicht
  markierte Welle-2-Mitigation wurde in Welle 2/3 bewusst
  nach Welle 6 verschoben — Welle 4 setzt das Pattern
  fort.
- **Keine in-Welle-4-Schaerfungs-ADR** fuer den ADR-0030-
  Sync-Vertrag, selbst wenn die Thread+Loop-Konstruktion
  sich als unschoen erweist. Solche Schaerfungen sind
  Welle-6-Material (Pattern ADR 0011); Welle 4
  dokumentiert nur die Reversibilitaet.

---

## 3. Architektur-Entscheidungen

Welle 4 bringt **eine** neue ADR: **ADR 0033**
(`docs/plan/adr/0033-opcua-adapter-profile.md`),
Status-Pfad `Proposed → Provisional → Accepted`:

- **`Proposed`** mit C1 (dieser Welle): Initial-Entwurf
  mit Decision-O-a/b/c/d/e-Vorschlaegen + Begruendung +
  Alternativen + Konsequenzen. Pattern analog ADR 0031
  (M4-Welle-2-C1) und ADR 0032 (M4-Welle-3-C1).
- **`Provisional`** mit C2-Merge (feat-Commit, der die
  Decision-Variante implementiert + Tests gruen +
  Integration-Smoke gruen).
- **`Accepted`** mit M4-Welle-7-Closure (analog ADR
  0022..0027 + 0030 + 0031 + 0032).

**Bezug:**

- [`spec/architecture.md §7`](../../../../spec/architecture.md)
  Z. 249 (`GG-AR-PORT-DRN-007` Tabelle — Surface bleibt
  ADR-0030-Vertrag) +
  [`§8.2`](../../../../spec/architecture.md) Z. 510–512
  (Adapter-Interfaces-Driven-Beschreibung).
- [`spec/lastenheft.md §16`](../../../../spec/lastenheft.md)
  Z. 1149–1163 (`GG-OPCUA-001`: SOLLTE-Cluster fuer
  Node-ID-Schema + Datentypen + Read/Write-Operationen +
  Fehlerverhalten + Adapter-Smoke).
- [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
  Decision-Liste (Item 2 Sync-/Async-Vertrag — Welle-1-
  Entscheidung „sync-Protocol + Adapter-internes Marshal"
  greift hier produktiv; Item 4 Profile-Deklaration —
  inline-Pattern aus ADR 0031/0032 wird uebernommen;
  Item 5 Test-Sibling — in-process bevorzugt analog
  Welle-3-Decision-M-f).
- [`M4-protocol-adapters.md`](M4-protocol-adapters.md) §3
  Welle 4 (kanonische Slice-Spezifikation mit DoD-
  Checkliste).
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  §2.1 (Sync-Vertrag mit Adapter-internem Thread+Loop-
  Marshal-Vorbelegung fuer rein-async-Stacks; Welle 4
  ist die Pruefstelle) + §2.2 (Caller-Scope-Lifecycle —
  FIFO-Start, LIFO-Stop) + §2.3 (stateless aus
  Replay-Sicht — OPC-UA-Reconnect-State ist volatile,
  kein Snapshot-Bump in Welle 4).
- [`../../adr/0031-mqtt-adapter-profile.md`](../../adr/0031-mqtt-adapter-profile.md)
  §2.1 (Decision 4a inline-Profile-Pattern — ADR 0033
  uebernimmt das Pattern direkt fuer Node-ID-Schema)
  + §2.4 (Decision 4d Per-Target Queue-Marshal —
  **nicht** reusable; OPC-UA hat eigene Marshal-Klasse,
  siehe Decision O-b).
- [`../../adr/0032-modbus-adapter-profile.md`](../../adr/0032-modbus-adapter-profile.md)
  §2.1 (Decision M-a inline-Register-Schema — Pattern-
  Praezedenz fuer Decision O-a inline-Node-ID-Schema)
  + §2.3 (Decision M-c direkt-sync — **nicht** reusable;
  asyncua erzwingt das Thread+Loop-Pattern) + §2.6
  (Decision M-f in-process-Server — reusable fuer
  Decision O-e).
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  als Pattern-Anker: ADR 0033 schaerft ADR 0030 §2.1
  OPC-UA-spezifisch, ohne den Sync-Vertrag zu ersetzen.
- M4-Welle-2-Mosquitto-Sibling-Pattern (testcontainers)
  als Praezedenz; M4-Welle-3-pymodbus-In-process-Pattern
  als Praezedenz. Welle 4 entscheidet in C1 (Decision
  O-e) zwischen den beiden.

**Vorbelegungs-Liste fuer M4-Folge-ADRs** (kommen ab
Welle 5; werden nicht in Welle 4 angelegt):

- Welle 5: optional ADR fuer DNP3/IEC-Spike (oder
  Anhang-Verzicht-Notiz zu ADR 0030 §6).
- Welle 6: ggf. Schaerfungs-ADR fuer OPC-UA-Subscription-
  Pfad (`Monitored Items`) oder Cross-Adapter-OTel-
  Span-Wrap.

---

## 4. Liefer-Reihenfolge (4 Commits)

### C0 — `docs(plan)`: M4-welle-4 Slice-Doc (Welle-Beginn)

- Dieses Dokument als Welle-Start-Marker. Status:
  `In Progress`.
- Kein README-Sync noetig: `in-progress/README.md` zeigt
  bereits nach M4-Welle-4-Pre-C0-Sync (`faa3ecc`)
  „Naechster aktiver Schritt: M4-Welle-4 (OPC-UA-Adapter
  …)". Welle-4-Doc-Eintrag in `in-progress/README.md` kommt
  **nicht** als eigener Bestand-Tabellen-Zeile (analog
  M3-Welle-1..6 + M4-Welle-1/2/3; Welle-N-Docs sind
  Tracking, nicht Roadmap-Bestand).

### C1 — `docs(adr)`: ADR 0033 Proposed — OPC-UA-Adapter-Profile

- NEU `docs/plan/adr/0033-opcua-adapter-profile.md` als
  `Proposed`. Inhalts-Skizze:
  - §1 Kontext (`GG-OPCUA-001`, ADR-0030-Surface-Bezug,
    ADR-0031/0032-Pattern-Praezedenz, asyncua-async-
    Charakter-Begruendung; Lizenz-Pruefung asyncua
    LGPL-3.0 + ggf. `open62541` MPL-2.0).
  - §2 Entscheidung mit Sub-Sections:
    - §2.1 Decision O-a (Node-ID-Schema inline) +
      Konsequenzen.
    - §2.2 Decision O-b (Async-Bridge: Thread+Loop
      adapter-intern) + Konsequenzen (Cancellation-
      Semantik, Teardown-Vertrag, Backpressure-Hinweis).
    - §2.3 Decision O-c (Datatype-Set + Konvertierung) +
      Konsequenzen.
    - §2.4 Decision O-d (Read/Write-Pfad) + Konsequenzen
      (Subscription-Pfad als Welle-6-Forward-Pointer).
    - §2.5 Decision O-e (Test-Sibling: in-process
      bevorzugt) + Konsequenzen.
  - §3 Alternativen (jeweils 1–2 Varianten je Decision;
    A1 separate `opcua_profiles`-Section verworfen,
    A2 per-Call `asyncio.run` verworfen, A3 erweiterter
    Datatype-Set verworfen, A4 Subscription-First-Pfad
    verworfen, A5 testcontainers verworfen-bedingt nach
    Lizenz-Pruefung, A6 separater `AsyncDeviceProtocolPort`-
    Schwester-Port verworfen).
  - §4 Konsequenzen (`AC-ADAPTER-LIGHTWEIGHT`-Pflicht,
    Welle-5-Implementer-Auflagen, Welle-6-Schaerfungs-
    Pfade).
  - §5 Status-Pfad (`Proposed → Provisional → Accepted`).
- EDIT `docs/plan/adr/README.md` (neue Zeile fuer
  ADR 0033 mit `Proposed`-Status).
- Kein Code-Pfad-Touch.
- Pattern analog M4-Welle-3-C1 `a86ac46` (ADR 0032
  Proposed) und M4-Welle-2-C1 `4e102b8` (ADR 0031
  Proposed).

### C2 — `feat(welle-4)`: protocol_opcua + Tests + Integration-Smoke + Compose-Edit

- NEU `src/grid_gym/adapters/driven/protocol_opcua/`-
  Modul (Datei-Aufstellung in §5 Critical Files).
- NEU 4 Unit-Test-Module unter
  `tests/unit/adapters/driven/protocol_opcua/`.
- NEU `tests/integration/test_opcua_*_smoke.py` (Name
  nach Decision O-e).
- EDIT `tests/integration/compose.yml` (Header-Kommentar-
  Sync zur Decision-O-e-Wahl; ggf. neuer Sibling-Service
  bei testcontainers-Variante).
- EDIT `pyproject.toml` (`asyncua>=1.1` in `[project]
  dependencies`; ggf. Forbidden-Listen-Korrektur).
- EDIT `Dockerfile` (`CRITICAL_COV_TARGETS`-Default um
  `adapters/driven/protocol_opcua` erweitert).
- `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste muss um
  `protocol_opcua` erweitert sein, sonst Override-
  Pflicht).
- `make test-integration` gruen mit OPC-UA-Smoke (Variante
  nach Decision O-e).
- `make arch-check` weiter `19/19 Contracts KEPT`:
  `AC-ADAPTER-LIGHTWEIGHT` greift fuer `protocol_opcua`
  ohne Code-Aenderung.

### C3 — `docs(plan|adr)`: Welle-4 Status/DoD-Sync + ADR-Schaerfung

- ADR 0033 `Proposed → Provisional` mit C2-Merge-Beleg.
- `M4-welle-4.md`-Status `In Progress → Done` mit
  C0/C1/C2-Hashes + DoD-Verifikation-Block + DoD-
  Checkliste (Pattern analog M4-welle-3.md §9).
- `M4-protocol-adapters.md §3 Welle 4`: Done-Status mit
  Commit-Belegen; DoD-Checkboxen alle abgehakt.
- README.md / README.de.md / roadmap.md /
  adr/README.md: M4-Status-Sync analog M4-Welle-3-C3
  `0ce578a` — Welle 4 `Done`, ADR 0033 `Provisional`,
  „Naechster aktiver Schritt: M4-Welle-5
  (DNP3/IEC-Disposition)".
- done/README.md: M4-welle-4.md-Bestand-Zeile folgt mit
  M4-Welle-5-Pre-C0-Sync (Pattern analog M4-Welle-3
  `9ba768b` / Slice-031 `faa3ecc`).

---

## 5. Critical Files

| Pfad                                                                              | Commit | Aktion                                          |
| --------------------------------------------------------------------------------- | ------ | ----------------------------------------------- |
| `docs/plan/planning/in-progress/M4-welle-4.md`                                    | C0     | NEU (dieses Dokument)                           |
| `docs/plan/adr/0033-opcua-adapter-profile.md`                                     | C1     | NEU (`Proposed`)                                |
| `docs/plan/adr/README.md`                                                         | C1     | EDIT (ADR-0033-Zeile)                           |
| `src/grid_gym/adapters/driven/protocol_opcua/__init__.py`                         | C2     | NEU (Public-Reexports + Modul-Docstring mit Lastenheft-Z.-1161–1163-Pflicht) |
| `src/grid_gym/adapters/driven/protocol_opcua/_config.py`                          | C2     | NEU (`OpcuaProtocolPortConfig` + `OpcuaNodeConfig`) |
| `src/grid_gym/adapters/driven/protocol_opcua/_codec.py`                           | C2     | NEU (Datentyp-Konvertierung Python ↔ `asyncua.ua.Variant`) |
| `src/grid_gym/adapters/driven/protocol_opcua/_loop_thread.py`                     | C2     | NEU (asyncio-Loop-Thread + Marshal-Helper)       |
| `src/grid_gym/adapters/driven/protocol_opcua/_port.py`                            | C2     | NEU (Decision O-b Lifecycle; Decision O-d Dispatcher) |
| `src/grid_gym/adapters/driven/protocol_opcua/_errors.py`                          | C2     | NEU (typed `DeviceProtocolPort*Error`-Subclasses inkl. Read/Write-Operation-Tax analog Slice-031-Pattern) |
| `tests/unit/adapters/driven/protocol_opcua/__init__.py`                           | C2     | NEU                                             |
| `tests/unit/adapters/driven/protocol_opcua/test_opcua_config.py`                  | C2     | NEU (Konstruktor-Validation)                    |
| `tests/unit/adapters/driven/protocol_opcua/test_opcua_codec.py`                   | C2     | NEU (Datentyp-Roundtrip + hypothesis-Property)  |
| `tests/unit/adapters/driven/protocol_opcua/test_opcua_loop_thread.py`             | C2     | NEU (Lifecycle + Cancellation + Teardown)       |
| `tests/unit/adapters/driven/protocol_opcua/test_opcua_protocol_port.py`           | C2     | NEU (Lifecycle + Read/Write gegen mocked Client)|
| `tests/integration/test_opcua_*_smoke.py`                                         | C2     | NEU (Name nach Decision O-e)                    |
| `tests/integration/compose.yml`                                                   | C2     | EDIT (Header-Kommentar zur Decision-O-e-Wahl; ggf. neuer Sibling) |
| `pyproject.toml`                                                                  | C2     | EDIT (`asyncua>=1.1` in `[project] dependencies`) |
| `Dockerfile`                                                                      | C2     | EDIT (`CRITICAL_COV_TARGETS` + `protocol_opcua`) |
| `docs/plan/adr/0033-opcua-adapter-profile.md`                                     | C3     | EDIT (`Proposed → Provisional`)                 |
| `docs/plan/adr/README.md`                                                         | C3     | EDIT (Status-Spalte `Provisional`)              |
| `docs/plan/planning/in-progress/M4-welle-4.md`                                    | C3     | EDIT (Status → Done; Hashes; DoD-Verifikation; §9 DoD-Checkliste) |
| `docs/plan/planning/in-progress/M4-protocol-adapters.md`                          | C3     | EDIT (§3 Welle 4 DoD-Checkboxen abgehakt)       |
| `README.md` + `README.de.md` + `docs/plan/planning/in-progress/roadmap.md` + `docs/plan/adr/README.md` | C3 | EDIT (M4-Status-Sync — Welle 4 `Done`, ADR 0033 `Provisional`, „Naechster aktiver Schritt: M4-Welle-5") |
| `docs/plan/planning/in-progress/README.md`                                        | C3     | EDIT („Naechster aktiver Schritt"-Zeile auf M4-Welle-5) |

---

## 6. Verifikationspfad

1. **C0 (Slice-Doc)**: `make docs-check` cache-frei gruen
   (alle Link-Targets aufgeloest — insbesondere
   `../done/M4-welle-0.md`, `../done/M4-welle-1.md`,
   `../done/M4-welle-2.md`, `../done/M4-welle-3.md`,
   `../done/031-modbus-adapter-review-folge.md`,
   `M4-protocol-adapters.md`, `../../adr/0030-…md`,
   `../../adr/0031-…md`, `../../adr/0032-…md`,
   `../../adr/0011-…md`,
   `../../../../spec/{architecture,lastenheft}.md`).
2. **C1 (ADR Proposed)**: `make docs-check` gruen (neuer
   ADR-Pfad existiert, `docs/plan/adr/README.md` synced).
3. **C2 (feat)**:
   - `make test-unit` gruen (1314 → 1360+ Tests; ~45-50
     neue Tests: 8 Config + 12 Codec mit hypothesis-Properties
     + 10 Loop-Thread + 12 Protocol-Port + 6
     Cross-Adapter-Lifecycle — feste Zahl in C3 belegt).
   - `make test-integration` gruen mit OPC-UA-Smoke (23 →
     24 Integration-Tests).
   - `make arch-check` gruen — `19/19 Contracts KEPT` (7
     lint-imports + 12 `tools/arch_check.py`);
     `AC-ADAPTER-LIGHTWEIGHT` erfasst `protocol_opcua`
     ohne Filter-Aenderung.
   - `make gates` cache-frei gruen ohne
     `CRITICAL_COV_TARGETS`-Override (Default-Liste um
     `adapters/driven/protocol_opcua` erweitert).
   - `make fullbuild`: Integration-Smoke selbst gruen
     (Variante nach Decision O-e); `image-audit` bleibt
     rot aus dem **dokumentierten** Pre-existing krb5-CVE-
     Grund (M3-Welle-7-`c61ab0d`-Drift; **nicht durch
     M4-Welle-4-Code verursacht**).
4. **C3 (Doc-Sync)**: `make docs-check` gruen mit
   geupdateten Status-Headern in 7 Docs (M4-welle-4.md,
   ADR 0033, ADR README, M4-protocol-adapters.md, README,
   README.de, roadmap; plus in-progress/README).

---

## 7. Risiken

- **Thread+Loop-Marshal-Teardown-Race**: der dedizierte
  asyncio-Loop muss bei `stop()` sauber abgebaut werden;
  `loop.call_soon_threadsafe(loop.stop)` +
  `thread.join(timeout=5.0)` muss alle in-flight-Tasks
  abrechnen. Falls eine pending Coroutine das Loop-Stop
  blockiert, bleibt der Test-Prozess am Ende stecken.
  *Mitigation*: C2-Teardown ruft erst `loop.run_until_complete(
  asyncio.gather(*pending, return_exceptions=True))` mit
  Timeout, dann `loop.stop()`; Daemon-Thread schuetzt vor
  Prozess-Aufhaengen bei katastrophalem Fehler.
- **asyncua-Library-API-Drift**: `asyncua` ist eine
  community-getriebene Python-Library mit gelegentlichen
  API-Aenderungen (`Variant`-Konstruktor-Signaturen,
  `Subscription`-Lifecycle, `Server`-Endpoint-Config).
  *Mitigation*: Floor-Pin `>=1.1,<2.0` mit `uv.lock`-
  Pinning auf eine spezifische Version; C2-Tests pinnen
  konkrete Methoden-Signaturen; `make lock-refresh` zieht
  eine bestimmte Version.
- **Decision-O-b-Konstruktion broker an Reconnect-Drift**:
  bei OPC-UA-Server-Verbindungs-Verlust waehrend `read()`
  / `write()` wirft asyncua eine `ConnectionError`/
  `BadSessionClosed`-Variante. Wenn die Adapter-interne
  Loop diese Exception nicht sauber an den Sync-Aufrufer
  zurueckpropagiert, bleibt der Caller blockiert.
  *Mitigation*: `run_coroutine_threadsafe(coro,
  loop).result(timeout=...)` mit expliziten Timeouts
  (`OpcuaProtocolPortConfig.read_timeout_s`,
  `.write_timeout_s`); Exception-Translation in
  `ModbusPortReadFailedError`-aequivalente
  `OpcuaPortReadFailedError`-Familie analog Slice-031-Pattern.
- **Decision-O-c-Datatype-Wahl bricht reale OPC-UA-
  Server-Profile**: konkrete Geraete (Wechselrichter,
  Energiemeter, Industrie-Steuerungen) benutzen oft
  herstellerspezifische `ExtensionObject`-Strukturen
  oder `ByteString`-Felder, die im Welle-4-Minimum-Set
  fehlen. *Mitigation*: ADR 0033 §2.3 dokumentiert die
  Welle-4-Wahl als `Provisional`; Per-Target-Override
  (`identifier_type`) haelt den Konfig-Pfad fuer Welle-6-
  Schaerfung offen.
- **Decision-O-e-Lizenz-Pruefung scheitert**: falls
  `open62541/open62541`-Image-Lizenz (MPL-2.0) nicht
  redistributable ist oder fuer den Container-Pull aus
  einer privaten Registry kommt, faellt die testcontainers-
  Variante. *Mitigation*: in-process `asyncua.Server` ist
  der Default-Pfad (Lizenz LGPL-3.0 fuer Library-Usage;
  Pattern Welle-3-Decision-M-f); Welle-4-C1 prueft
  Lizenz **vor** der Test-Sibling-Wahl.
- **Sub-Slicing-Schwelle hart hit**: Welle 4 = 1 Adapter
  + 1 ADR + 1 Integration-Smoke = exakt die Sub-Slicing-
  Obergrenze (`M4-protocol-adapters.md` §3 Praeambel).
  Falls der asyncua-Loop-Thread-Setup zusaetzliche
  Schritte triggert (z. B. ein zweiter Integration-Smoke
  fuer Subscription-Pfad), bricht die Schwelle.
  *Mitigation*: C2-Scope ist normativ in §2 In-Scope-
  Liste fixiert; jede Erweiterung waehrend C2 erfordert
  Sub-Slice-Bezeichnung (`Welle 4a/4b`).
- **`asyncua`-Lizenz-Drift**: asyncua ist LGPL-3.0
  (verifiziert per asyncua-PyPI); falls upstream zu einer
  restriktiveren Lizenz wechselt, koennte Welle 4
  blockieren. *Mitigation*: Floor `>=1.1` + `uv.lock`-
  Pin haelt eine spezifische Version stabil; Folge-Welle
  prueft Upstream-Drift.
- **Welle-5-Disposition haengt von Welle-4-Erfahrung
  ab**: ADR 0030 §2.4 (Decision 1 provisorisch) erwartet,
  dass die asyncua-Erfahrung aus Welle 4 die DNP3/IEC-
  Disposition in Welle 5 informiert (Verzicht vs. Spike).
  *Mitigation*: Welle-4-C3-Doc-Sync traegt die operativen
  Erfahrungen mit dem Thread+Loop-Pattern in
  `M4-welle-4.md §1`/§7 ein; Welle 5 zitiert sie bei
  ihrer Disposition.

---

## 8. Wandert nach

- `done/M4-welle-4.md` mit M4-Welle-5-Pre-C0-Move (Pattern
  aus M3 und M4-Welle-1/2/3: `welle-4.md` wandert mit
  M4-Welle-5-Pre-C0 nach `done/`; `chore(welle-5): git mv`-
  Commit + Pre-C0-Sync-Folge-Commit, Memory-Konvention
  `feedback_git_mv`).
- ADR 0033 bleibt in `docs/plan/adr/` (kein Move; nur
  Status-Updates).
- `M4-protocol-adapters.md` bleibt in `in-progress/` bis
  M4-Welle-7-Closure.
- M4-Welle-5-Naechster-Schritt: DNP3/IEC-Disposition
  (Verzicht-Default oder Spike-Opt-In) — Entscheidung
  informiert durch asyncua-Erfahrung aus Welle 4. Welle-5-
  Variante A (Verzicht) ist Default; Variante B (Spike)
  ist Opt-In.

---

## 9. DoD-Checkliste (Welle-Schluss, mit C3 abgehakt)

Skelett — wird in C3 abgehakt. Pattern analog
M4-welle-3.md §9.

**In-Scope-Items (alle abzuhaken mit C3):**

- [ ] **ADR 0033 angelegt** — `Proposed` (C1) →
  `Provisional` (C3), mit Decisions O-a/O-b/O-c/O-d/O-e
  alle **final**.
- [ ] **OPC-UA-Port produktiv** — `OpcuaDeviceProtocolPort`
  als `DeviceProtocolPort`-Implementer unter
  `src/grid_gym/adapters/driven/protocol_opcua/`; Modul-
  Docstring traegt Lastenheft-Z.-1161–1163-Pflicht
  (Simulations-/Testadapter-Notiz).
- [ ] **Async-Loop-Thread produktiv** —
  `OpcuaLoopThread`-Klasse in `_loop_thread.py` mit
  geordnetem `start()`/`stop()`-Lifecycle und
  `run_coroutine_threadsafe`-Marshal-Helper; erstes
  produktives Thread+Loop-Konstruktions-Pattern im Repo
  (ADR 0030 §2.1-Konsequenz produktiv vorgetragen).
- [ ] **Unit-Tests fuer 4 Test-Aspekte** —
  Config-Validation + Datentyp-Codec-Roundtrip +
  Loop-Thread-Lifecycle + Protocol-Port-Lifecycle/Read+Write;
  ~45-50 neue Tests (feste Zahl in C3).
- [ ] **Integration-Smoke produktiv** —
  `tests/integration/test_opcua_*_smoke.py` mit
  Variante nach Decision O-e (in-process `asyncua.Server`
  ODER `open62541`-Sibling) + End-to-End-Read/Write-
  Roundtrip durch das Decision-O-c-Datatype-Set.
- [ ] **`tests/integration/compose.yml` Header-Kommentar
  syncht** — Decision-O-e-Notiz zur Smoke-Variante
  (in-process oder Sibling-Service).
- [ ] **`pyproject.toml` erweitert** — `asyncua>=1.1`
  in `[project] dependencies`; `asyncua`-Eintrag in den
  AC-PORTS-NO-FW/AC-NO-FW-Forbidden-Listen ggf. korrigiert
  (Welle-0-Vorbelegung pruefen).
- [ ] **`Dockerfile` erweitert** — `CRITICAL_COV_TARGETS`-
  Default um `src/grid_gym/adapters/driven/protocol_opcua`.
- [ ] **`AC-ADAPTER-LIGHTWEIGHT` greift fuer
  `protocol_opcua`** — `tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`-Filter erfasst den
  neuen Pfad ohne Code-Aenderung; `make arch-check`
  weiter `19/19 Contracts KEPT`.
- [ ] **C3-Doc-Sync** — `M4-welle-4.md` Status
  `In Progress → Done`, ADR 0033 `Proposed → Provisional`,
  `M4-protocol-adapters.md §3 Welle 4` DoD-Checkboxen
  alle abgehakt, Top-Level-Doku-Sync (README/README.de/
  roadmap/adr/README/in-progress/README) auf den
  Welle-4-Endstand.

**Anti-Scope-Items (alle zu halten):**

- [ ] **Keine DNP3-/IEC-Adapter** in C2.
- [ ] **Kein OPC-UA-Subscription-Pfad** (Monitored
  Items) in C2; Polling-Read reicht.
- [ ] **Kein OTel-Span-Wrap** der OPC-UA-Adapter-Calls.
- [ ] **Keine OPC-UA-Security** (User/X509/Encryption);
  Anonymous-Endpoint fuer Smoke.
- [ ] **Kein RandomPort-Determinismus** fuer Node-IDs.
- [ ] **Keine Scenario-Schema-Erweiterung jenseits des
  Decision-O-a-Pattern** (kein neuer YAML-Top-Level-
  Block).
- [ ] **Keine Welle-2-MQTT-/Welle-3-Modbus-Adapter-
  Aenderungen**.
- [ ] **Keine Bewegung der Open-Trigger**.
- [ ] **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md`
  (3 von 7 DoD-Items geliefert nach Welle 4: MQTT +
  Modbus + OPC-UA; Sweep in Welle 7).
- [ ] **Kein `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-
  Property-Test** in Welle 4 (bewusst nach Welle 6
  verschoben; Welle-1-§7-Folge-Pflicht honoriert).
- [ ] **Keine in-Welle-4-Schaerfungs-ADR** fuer den
  ADR-0030-Sync-Vertrag (Reversibilitaet dokumentiert,
  Schaerfung ist Welle-6-Material).
