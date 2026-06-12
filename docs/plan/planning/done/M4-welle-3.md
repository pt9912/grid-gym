# Welle 3 — M4 Modbus-TCP-Adapter

**Status:** Done — geschlossen 2026-05-30 mit M4-Welle-3-C3
(`docs(plan|adr)` Doc-Sync). Doku-Review-Folge
2026-05-31: nach `done/` verschoben, Smoke-Abdeckung
praezisiert; Review-Folge
[`031-modbus-adapter-review-folge.md`](031-modbus-adapter-review-folge.md)
hat FC06-Guard, Read-/Write-Fehler-Taxonomie und die
bewusste Smoke-Abgrenzung umgesetzt. Eroeffnet
2026-05-30 nach M4-Welle-2-Closure (`3b633f6` C0 + `4e102b8`
C1 + `f33bb4e` C2 + `7e161f5` C3 + `0d6ad6c` Self-Close-Move
+ `9ba768b` Pre-C0-Sync). Welle 3 ist die **dritte Code-Welle**
in M4 und der **zweite konkrete Adapter** auf der
`DeviceProtocolPort`-Surface (`GG-AR-PORT-DRN-007`):
Modbus-TCP ueber `pymodbus 3.x`. Welle 3 nutzt das in
ADR 0031 §2.1 etablierte Decision-4a-Inline-Profile-Pattern
und schaerft es Modbus-spezifisch (Register-Schema statt
Topic-Schema, Datentyp- und Byte-Reihenfolge-Konvention,
Slave-Unit-ID).

**Liefer-Hashes:**

- C0 `8ef1e72` — `docs(plan): M4-welle-3 Slice-Doc (M4 Welle-3 Beginn)`.
- C1 `a86ac46` — `docs(adr): ADR 0032 Proposed — Modbus-TCP-Adapter-Profile (M4 Welle 3)`.
- C2 `d721982` — `feat(welle-3): protocol_modbus + Tests + In-Process-Smoke + Compose-Edit`.
- EoD-Sync `2b84361` — `docs: EoD-Sync 2026-05-30 — M4-Welle-3-C2-Stand in 3 Top-Level-Docs` (Zwischenstand, kein C3-Ersatz).
- C3 — `docs(plan|adr): M4-Welle-3-C3 — Status/DoD-Sync + ADR 0032 -> Provisional + Trigger-006-Re-Eval + Top-Level-Doku-Sync`.

**DoD-Verifikation (Welle-Schluss, Stand `d721982` C2 +
C3):**

- `make test-unit`: **1306 Tests gruen** (Pre-Welle-3-Stand
  1211 → Welle-3-Endstand 1306 = +95 Unit-Tests; davon
  ~25 Config-Validation
  (`tests/unit/adapters/driven/protocol_modbus/test_modbus_config.py`),
  ~30 Codec-Roundtrip mit hypothesis-Property-Tests pro
  5 Datatypes x 2 Byte-Order-Varianten + Word-Swap-Matrix
  (`test_modbus_codec.py`), ~24 Lifecycle + Read/Write
  mit mocked pymodbus-`ModbusTcpClient`
  (`test_modbus_protocol_port.py`), ~16 Function-Code-
  Override FC03/FC04/FC06/FC10
  (`test_modbus_function_codes.py`)).
- `make test-integration`: **23 Tests gruen** (Pre-Welle-3-
  Stand 22 → Welle-3-Endstand 23 = +1 Modbus-In-Process-
  Smoke; in-process `pymodbus.server.ModbusTcpServer` in
  `threading.Thread(daemon=True)`, End-to-End-Read/Write-
  Roundtrip durch alle 5 Datatypes im Default-Profil
  `byte_order="big_endian"`, `word_swap=false`,
  Parent-`unit_id=1`; expliziter `server.shutdown()` +
  `thread.join(timeout=5.0)`-Teardown. Byte-Order-/
  Word-Swap-Matrix und Unit-ID-Override sind in Unit-Tests
  bzw. Mock-Tests abgedeckt; die enge E2E-Abgrenzung ist
  in [`031-modbus-adapter-review-folge.md`](031-modbus-adapter-review-folge.md)
  bestaetigt).
- `make arch-check`: **19/19 Contracts KEPT** (7
  lint-imports + 12 `tools/arch_check.py`);
  `AC-ADAPTER-LIGHTWEIGHT` erfasst `protocol_modbus` ohne
  Filter-Edit (Pfad-Filter `bucket.startswith("protocol_")`
  in `tools/arch_check.py:1089` greift unveraendert).
- `make gates`: **alle 9 A-1-Gates gruen** ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste um
  `src/grid_gym/adapters/driven/protocol_modbus` erweitert).
- `make fullbuild`: `image-audit` weiter rot aus
  **dokumentiertem** Pre-existing krb5-CVE-Grund
  (`CVE-2026-40356`-Drift seit M3-Welle-7-`c61ab0d`,
  **nicht durch M4-Welle-3-Code verursacht**); Compose-Smoke
  selbst (in-process-Modbus-Server; kein neuer Sibling) gruen.
- ADR 0032: `Proposed → Provisional` (Decisions M-a/M-b/M-c/
  M-d/M-e/M-f alle **final**; Status-Pfad in
  [`../../adr/0032-modbus-adapter-profile.md`](../../adr/0032-modbus-adapter-profile.md) §5
  mit Hashes belegt).
- **Trigger-006-Re-Eval (`--strict-bytes`):** `mypy
  --strict-bytes` laeuft cache-frei **gruen** gegen
  `src/grid_gym/adapters/driven/protocol_modbus/` ohne
  zusaetzliche `# type: ignore`-Inflation (bestehende 2
  `# type: ignore[no-untyped-call]` in `_port.py:128/148`
  sind pymodbus-API-spezifisch, kein bytes-Bezug). Trigger
  ist aktivierungs-reif; die physische Bewegung bleibt ein
  separater Folge-Slice (siehe
  [`../done/006-mypy-strict-bytes.md`](../done/006-mypy-strict-bytes.md)).
- **Review-Folge 2026-05-31:** Welle 3 bleibt geliefert;
  Folge-Slice [`031`](031-modbus-adapter-review-folge.md)
  hat die Code-Schaerfungen umgesetzt: FC06 wird fuer
  Multi-Register-Datatypes fail-fast abgelehnt, Read-/
  Write-Fehler sind operation-spezifisch typisiert, und
  der Integration-Smoke bleibt bewusst ein Default-Profil-
  E2E-Test.

Kanonische Slice-Spezifikation:
[`M4-protocol-adapters.md §3 Welle 3`](../done/M4-protocol-adapters.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht Ersatz.

**Spec-Reife:** Inhaltlich final. Decisions aus
[`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
Decision-Liste (analog ADR 0031 §2.1 Pattern uebertragen)
werden in C1 (ADR 0032 Proposed) konkret gewaehlt;
C2 (feat) implementiert die gewaehlte Variante.

---

## 1. Context

M4-Welle-2 hat den ersten konkreten `DeviceProtocolPort`-
Implementer produktiv geliefert (`MqttDeviceProtocolPort`,
ADR 0031 `Provisional`):

- 7-Modul-Paket unter
  [`../../../../src/grid_gym/adapters/driven/protocol_mqtt/`](../../../../src/grid_gym/adapters/driven/protocol_mqtt/)
  mit `MqttProtocolPortConfig`-frozen-dataclass +
  `canonical_json`-Codec + Per-Target `queue.Queue`-
  Marshal am paho-Loop-Thread-Boundary.
- Decision 4a inline-Topic-Schema im `protocol_ports`-
  Scenario-YAML-Block — etabliert das Pattern fuer Welle 3
  (Register-Schema) und Welle 4 (Node-ID-Schema).
- Integration-Smoke via testcontainers gegen
  `eclipse-mosquitto:2`-Sibling.
- ADR 0031 `Provisional` mit Decisions 4a/4b/4c/4d
  alle **final**; Decision 4d (Per-Target Queue +
  Lazy-Init) ist **MQTT-spezifisch** und wird in Welle 3
  durch eine **andere** Decision-Klasse abgeloest, weil
  pymodbus-Sync-Clients keinen Callback-Marshal brauchen
  (siehe §3 Decision M-c).

Welle 3 ist der **zweite konkrete Implementer**:

- NEU `src/grid_gym/adapters/driven/protocol_modbus/`-Modul
  mit `pymodbus 3.x`-Wrapper als `DeviceProtocolPort`-
  Implementer (`GG-MODB-001`).
- NEU ADR 0032 (Modbus-TCP-Adapter-Profile) als Surface-
  relevanter Adapter-ADR. Modbus-spezifische Decisions:
  Register-Schema, Datentyp/Byte-Reihenfolge, Polling-
  Pattern, Function-Code-Mapping, Slave-Unit-ID.
  Pattern-Praezedenz [`ADR 0031`](../../adr/0031-mqtt-adapter-profile.md)
  fuer Decision-Anlage; Modbus-Schaerfung folgt der
  ADR-0011-Konvention (Schaerfung-ohne-Supersede).
- NEU Integration-Smoke via **in-process
  pymodbus-Server** (nicht testcontainers): umgeht das in
  [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
  Decision 5 dokumentierte Modbus-Server-Container-Lizenz-
  Risiko (kommerziell-restriktive Images wie
  `oitc/modbus-server`); pymodbus ist BSD-lizensiert und
  liefert einen produktiven `ModbusTcpServer` mit, der im
  Test-Prozess als Thread laeuft. Pattern analog
  M2-Welle-6c-Postgres-Sibling (Sibling-Container) **mit
  bewusstem Verzicht** auf testcontainers fuer Welle 3.
- EDIT `tests/integration/compose.yml`-Kommentar-Sync (kein
  neuer Sibling-Service, weil pymodbus-Server in-process
  laeuft — Kommentar dokumentiert die bewusste Entscheidung
  fuer den naechsten Wave-Walker).
- EDIT `pyproject.toml`: `pymodbus`-Dependency
  (`pymodbus` ist in den AC-PORTS-NO-FW/AC-NO-FW-
  Forbidden-Listen bereits vorgemerkt — Welle 3 zieht den
  produktiven Floor in `[project] dependencies`).
- EDIT `Dockerfile`: `CRITICAL_COV_TARGETS`-Default um
  `src/grid_gym/adapters/driven/protocol_modbus` erweitert
  (Pattern analog `protocol_mqtt`-Eintrag aus
  M4-Welle-2-C2 `f33bb4e`).

Welle 3 liefert **keine** OPC-UA-/DNP3-/IEC-Adapter
(Welle 4/5) und **keinen** OTel-Span-Wrap der Adapter-Calls
(Welle 6).

**Trigger-006-Re-Eval-Forderung:** Modbus-Adapter-Code
ist der **erste** produktive `bytes`/`int`/`float`-
Konvertierungs-Pfad im Repo (Register-Bytes ->
`int16`/`int32`/`float32`). Trigger 006 (`--strict-bytes`)
wartet seit M3 auf eine Stelle, an der die Pruefung
ohne `# type: ignore`-Inflation greifen koennte — Welle 3
ist diese Stelle. **C3 macht die Re-Eval-Notiz** in Trigger
006 fest und entscheidet, ob `--strict-bytes` jetzt
aktiviert wird (Trigger nach `next/` ziehen) oder weiter
in `open/` bleibt mit konkretem M4-Welle-3-Code-Beleg.

---

## 2. Scope

**In Scope:**

1. NEU `docs/plan/adr/0032-modbus-adapter-profile.md` in C1
   als `Proposed`. Entscheidungen:
   - **Decision M-a (Register-Schema, final)**: Register-
     Profil-Deklaration **inline** im `protocol_ports`-
     Scenario-YAML-Block (Pattern-Praezedenz ADR 0031 §2.1).
     Pro `device_id` ein `MqttTopicConfig`-Analog
     `ModbusRegisterConfig` mit Pflicht-Feldern
     `address`/`datatype`/`access`; Optional-Feldern
     `byte_order`/`word_swap`/`unit_id`/`function_code`.
   - **Decision M-b (Datatype + Byte/Word-Order, final)**:
     Erlaubter Datatype-Set `{int16, uint16, int32, uint32,
     float32}` (Welle-3-Minimum; `int64`/`float64` +
     `string`/`bool-array` als Welle-6-Schaerfungspfad
     offen via ADR 0011). Byte-Order-Default `big_endian`
     (Modbus-TCP-Spec); `word_swap` Default `false`
     (Konvention der meisten Wechselrichter-Hersteller).
     Per-Target ueberschreibbar.
   - **Decision M-c (Polling, final)**: **kein** Background-
     Polling-Thread. `read(target)` ruft
     `client.read_holding_registers(...)` direkt synchron
     gegen den Modbus-Server. pymodbus-`ModbusTcpClient`
     ist sync-by-design und passt damit **ohne** Thread-
     Marshal direkt in die Sync-`DeviceProtocolPort`-
     Surface (ADR 0030 §2.1). Vorteil gegenueber MQTT
     (Decision 4d): keine Queue, keine Lazy-Init, kein
     Callback-Boundary — `_port.py` ist signifikant
     einfacher als das MQTT-Pendant.
   - **Decision M-d (Function-Code-Mapping, final)**:
     Telemetry-Reads ueber **FC03** (Read Holding
     Registers) als Default; Command-Writes ueber **FC10**
     (Write Multiple Registers) als Default. Per-Target
     ueberschreibbar fuer FC04 (Read Input Registers,
     read-only-Devices) und FC06 (Write Single Register,
     simple Setpoint). Coil-/Discrete-Input-Function-Codes
     (FC01/FC02/FC05/FC0F) bleiben Welle-6-Schaerfung
     offen.
   - **Decision M-e (Slave-Unit-ID, final)**: Pro Target
     ein `unit_id: int = 1` Pflichtfeld (Modbus-Slave-
     Adresse). Default 1 ist die paho-mqtt-/Wechselrichter-
     Konvention; Multi-Slave-Bus-Scenarios setzen
     ueberschreibend.
   - **Decision M-f (Test-Sibling, final)**: **In-process
     `pymodbus.server.ModbusTcpServer`** im Test-Code
     (`tests/integration/test_modbus_in_process_smoke.py`),
     **kein** testcontainers-Container. Begruendung:
     (a) Modbus-Server-Container haben restriktive
     Lizenzen (siehe
     [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
     Decision 5); (b) pymodbus selbst (BSD-lizensiert)
     bringt einen produktiven Modbus-Server mit, der in
     einem `threading.Thread` im Test-Prozess laeuft;
     (c) keine `compose.yml`-Erweiterung, keine
     testcontainers-Abhaengigkeit, keine Docker-Image-
     Pull-Latenz.
2. NEU
   `src/grid_gym/adapters/driven/protocol_modbus/__init__.py`:
   `ModbusDeviceProtocolPort`-Klasse als
   `DeviceProtocolPort`-Implementer.
   - `start()`: `pymodbus.client.ModbusTcpClient(host,
     port)` konstruieren + `client.connect()` (sync
     blocking call). Idempotent.
   - `stop()`: `client.close()`. Idempotent.
   - `read(target)`: Lookup `ModbusRegisterConfig` per
     `device_id`; `client.read_holding_registers(address,
     count, device_id=unit_id)`; Bytes -> `int16`/`int32`/
     `float32` via `struct.unpack` mit Datatype-Konfig;
     verpacken in `TelemetryPoint`.
   - `write(target, command)`: Lookup `ModbusRegisterConfig`;
     `command.payload[<datatype-Key>]` -> Bytes via
     `struct.pack`; `client.write_registers(address,
     values, device_id=unit_id)`.
   - Modul-Docstring mit Lastenheft-Z. 1161–1163-Pflicht:
     **„Simulations-/Testadapter; keine produktive
     Anlagensteuerung"**.
3. NEU
   `src/grid_gym/adapters/driven/protocol_modbus/_config.py`
   mit `ModbusProtocolPortConfig` + `ModbusRegisterConfig`-
   frozen-dataclasses; Konstruktor-Validation mit
   `ModbusConfigError`-Familie (analog `MqttConfigError`-
   Familie aus Welle 2).
4. NEU
   `src/grid_gym/adapters/driven/protocol_modbus/_codec.py`
   mit `encode_command_to_registers` /
   `decode_registers_to_telemetry`-Helfern (Datentyp-
   Konvertierung; `struct.pack`/`struct.unpack` mit
   Byte-Order-Auswahl).
5. Unit-Tests unter
   `tests/unit/adapters/driven/protocol_modbus/`:
   - `test_modbus_config.py`: Konstruktor-Validation
     (Datatype-Allowlist, Function-Code-Allowlist,
     Address-Range, Slave-Unit-ID-Range).
   - `test_modbus_codec.py`: Datentyp-Roundtrip pro
     Type (int16/uint16/int32/uint32/float32) mit
     Byte-Order-Varianten (`big_endian`+`word_swap`-
     Matrix); Roundtrip-Property-Tests via
     `hypothesis`.
   - `test_modbus_protocol_port.py`: Lifecycle + Read/
     Write gegen mocked `pymodbus.client.ModbusTcpClient`.
   - `test_modbus_function_codes.py`: Per-Target-
     Function-Code-Override; FC03/FC04 Read-Pfad-
     Unterschied; FC06/FC10 Write-Pfad-Unterschied.
6. NEU `tests/integration/test_modbus_in_process_smoke.py`:
   - In-process `pymodbus.server.ModbusTcpServer` in
     `threading.Thread(target=server.serve_forever,
     daemon=True)` mit `ServerContext` aus dem Test-Code.
   - End-to-End-Roundtrip:
     `ModbusDeviceProtocolPort.write(target, command)`
     -> Server schreibt Register;
     `ModbusDeviceProtocolPort.read(target)` -> Server
     liefert die geschriebenen Register zurueck (als
     `TelemetryPoint`).
   - Tests fuer alle 5 Datatypes im Default-Profil
     (`big_endian`, kein Word-Swap, Parent-`unit_id=1`);
     Byte-Order-/Word-Swap-Matrix bleibt Unit-/Mock-
     Test-Abdeckung.
7. EDIT `tests/integration/compose.yml`-Header-Kommentar:
   Hinweis aufnehmen, dass M4-Welle-3-Modbus-Smoke
   **in-process** laeuft (kein eigener Sibling) — Pattern-
   Praezedenz fuer Welle 4 (asyncua, ebenfalls Lizenz-
   sensibel) und potenziell Welle 5 (DNP3/IEC).
8. EDIT `pyproject.toml`: `pymodbus>=3.6` in `[project]
  dependencies`. `pymodbus`-Eintrag in den
   AC-PORTS-NO-FW/AC-NO-FW-Forbidden-Listen ist
   Welle-0-vorbelegt — keine Aenderung an den
   `[[tool.importlinter.contracts]]`-Bloecken noetig.
9. EDIT `Dockerfile`: `CRITICAL_COV_TARGETS`-Default um
   `src/grid_gym/adapters/driven/protocol_modbus`
   erweitert (Pattern analog `protocol_mqtt`-Eintrag aus
   M4-Welle-2-C2 `f33bb4e`).
10. **Trigger-006-Re-Eval** in C3: konkrete Pruefung, ob
    `mypy --strict-bytes` jetzt mit dem Modbus-Code ohne
    `# type: ignore`-Inflation greift; Entscheidung
    dokumentieren (Trigger nach `next/` ziehen ODER
    Welle-6-Forward-Pointer). Trigger-Body in
    `docs/plan/planning/done/006-mypy-strict-bytes.md`
    aktualisieren.
11. C3-Doc-Sync zieht `M4-welle-3.md`-Status auf `Done`
    und schaerft ADR 0032 von `Proposed` auf
    `Provisional`. (Endgueltige Akzeptanz erst mit
    M4-Welle-7-Closure.)
12. `make arch-check` weiter `19/19 Contracts KEPT` —
    `AC-ADAPTER-LIGHTWEIGHT` greift fuer `protocol_modbus`
    via `tools/arch_check.py:1089`
    `bucket.startswith("protocol_")`. Welle-1/2-Smoke-
    Regression-Schutz bleibt aktiv; Welle 3 prueft, dass
    der Filter den neuen `protocol_modbus/`-Pfad ohne
    Code-Aenderung erfasst.

**Anti-Scope:**

- **Keine OPC-UA-/DNP3-/IEC-Adapter** unter
  `src/grid_gym/adapters/driven/protocol_*/`. Welle 4 OPC-
  UA, Welle 5 DNP3/IEC-Disposition.
- **Kein OTel-Span-Wrap** der Modbus-Adapter-Calls.
  Span-Wrap-Pattern fuer `protocol_*`-Adapter ist Welle-6-
  Material (Cross-Adapter-Hardening; ADR 0024
  `TracePort` als Bezug).
- **Kein RandomPort-Determinismus** fuer Slave-Unit-IDs
  oder Register-Adressen — Welle-3-Default-Werte reichen.
- **Keine Scenario-Schema-Erweiterung jenseits des
  Decision-M-a-Pattern**. Welle 3 fuegt **keinen** neuen
  Top-Level-YAML-Block hinzu; das Register-Schema sitzt
  inline im `protocol_ports`-Block analog ADR 0031 §2.1.
- **Keine Welle-2-MQTT-Adapter-Aenderungen**. Welle-3-
  Modbus-ADR (0032) ist **Erweiterung**, kein Supersedes
  zu ADR 0031.
- **Keine testcontainers-Modbus-Server-Sibling**.
  Decision M-f waehlt explizit den in-process-Pfad
  (Lizenz- + Komplexitaets-Reduktion).
- **Keine Bewegung der 17 Open-Trigger** mit **einer
  Ausnahme**: Trigger 006 (`--strict-bytes`) wird in C3
  re-evaluiert (Modbus-Bytes-Pfad ist der erste
  produktive Beleg). Entscheidung fliesst in den Trigger-
  Body; physische Bewegung (von `open/` nach `next/`)
  passiert nur bei positiver Re-Eval.
- **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md`.
  Welle 3 liefert genau **einen** der 7 DoD-Items
  (`GG-MODB-001`); der DoD-Sweep folgt mit Welle 6.
- **Kein `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-
  Property-Test**. Die in M4-welle-1 §7 als Folge-Pflicht
  markierte Welle-2-Mitigation wurde in Welle 2 bewusst
  nach Welle 6 verschoben — Welle 3 setzt das Pattern
  fort.

---

## 3. Architektur-Entscheidungen

Welle 3 bringt **eine** neue ADR: **ADR 0032**
(`docs/plan/adr/0032-modbus-adapter-profile.md`),
Status-Pfad `Proposed → Provisional → Accepted`:

- **`Proposed`** mit C1 (dieser Welle): Initial-Entwurf
  mit Decision-M-a/b/c/d/e/f-Vorschlaegen + Begruendung +
  Alternativen + Konsequenzen. Pattern analog ADR 0031
  (M4-Welle-2-C1).
- **`Provisional`** mit C2-Merge (feat-Commit, der die
  Decision-Variante implementiert + Tests gruen +
  Integration-Smoke gruen).
- **`Accepted`** mit M4-Welle-7-Closure (analog ADR
  0022..0027 + 0030 + 0031).

**Bezug:**

- [`spec/architecture.md §7`](../../../../spec/architecture.md#7-domain-modell-skizze)
  Z. 249 (`GG-AR-PORT-DRN-007` Tabelle — Surface bleibt
  ADR-0030-Vertrag) +
  [`§8.2`](../../../../spec/architecture.md#82-adapter-interfaces-driven) Z. 510–512
  (Adapter-Interfaces-Driven-Beschreibung).
- [`spec/lastenheft.md §16`](../../../../spec/lastenheft.md#16-kommunikationsschnittstellen)
  Z. 1134–1148 (`GG-MODB-001`: SOLLTE-Cluster fuer
  Register-Mapping + Datentypen + Byte-Reihenfolge +
  Read/Write-Operationen + Timeout-Verhalten +
  Adapter-Smoke).
- [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
  Decision-Liste (Item 4 Profile-Deklaration + Item 5
  Test-Sibling-Container — **explizit Lizenz-Risiko
  fuer Modbus dokumentiert**; Item 6
  `AC-ADAPTER-LIGHTWEIGHT`-Pfad-Filter).
- [`M4-protocol-adapters.md`](../done/M4-protocol-adapters.md) §3
  Welle 3 (kanonische Slice-Spezifikation).
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  §2.1 (Sync-Vertrag — pymodbus-Sync-Client passt **ohne**
  Thread-Marshal direkt in die Sync-Surface; das ist die
  **einfachste** Welle-2/3/4-Implementierungs-Variante) +
  §2.2 (Caller-Scope-Lifecycle) + §2.3 (stateless aus
  Replay-Sicht — Modbus-Reconnect-State ist volatile,
  kein Snapshot-Bump in Welle 3).
- [`../../adr/0031-mqtt-adapter-profile.md`](../../adr/0031-mqtt-adapter-profile.md)
  §2.1 (Decision 4a inline-Profile-Pattern — ADR 0032
  uebernimmt das Pattern direkt fuer Register-Schema)
  + §2.2 (Decision 4b `canonical_json`-Codec —
  ADR 0032 **weicht ab**: Modbus benutzt
  `struct.pack`/`struct.unpack` direkt auf Bytes; kein
  JSON-Layer zwischen Adapter und Register).
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  als Pattern-Anker: ADR 0032 schaerft ADR 0030 §2.1
  Modbus-spezifisch, ohne den Sync-Vertrag zu ersetzen.
- M3-Welle-6c-Postgres-Sibling-Pattern (Praezedenz fuer
  Sibling-im-Test); M4-Welle-2-Mosquitto-Sibling-Pattern
  als zweite Praezedenz. **Welle 3 weicht bewusst ab** mit
  in-process-Server (Decision M-f).

**Vorbelegungs-Liste fuer M4-Folge-ADRs** (kommen ab
Welle 4; werden nicht in Welle 3 angelegt):

- Welle 4: ADR fuer OPC-UA-Adapter-Profil
  (`asyncua`-Wrapper — Node-ID-Schema; **erster** rein-
  async-Stack, traegt die Thread+Loop-Marshal-Konstruktion
  produktiv vor; siehe ADR 0030 §2.1 Konsequenz +
  ADR 0031 §2.4 Callback-Marshal-Pattern als nicht-
  reusable-Praezedenz).
- Welle 5: optional ADR fuer DNP3/IEC-Spike (oder
  Anhang-Verzicht-Notiz zu ADR 0030 §6).

---

## 4. Liefer-Reihenfolge (4 Commits)

### C0 — `docs(plan)`: M4-welle-3 Slice-Doc (Welle-Beginn)

- Dieses Dokument als Welle-Start-Marker. Status:
  `In Progress`.
- Kein README-Sync noetig: `in-progress/README.md` zeigt
  bereits nach M4-Welle-3-Pre-C0-Sync `9ba768b` „Naechster
  aktiver Schritt: M4-Welle-3 (Modbus-TCP-Adapter …)".
  Welle-3-Doc-Eintrag in `in-progress/README.md` kommt
  **nicht** als eigener Bestand-Tabellen-Zeile (analog
  M3-Welle-1..6 + M4-Welle-1/2; Welle-N-Docs sind
  Tracking, nicht Roadmap-Bestand).

### C1 — `docs(adr)`: ADR 0032 Proposed — Modbus-TCP-Adapter-Profile

- NEU `docs/plan/adr/0032-modbus-adapter-profile.md` als
  `Proposed`. Inhalts-Skizze:
  - §1 Kontext (`GG-MODB-001`, ADR-0030-Surface-Bezug,
    ADR-0031-Pattern-Praezedenz, pymodbus-Sync-Charakter-
    Begruendung).
  - §2 Entscheidung mit Sub-Sections:
    - §2.1 Decision M-a (Register-Schema inline) +
      Konsequenzen.
    - §2.2 Decision M-b (Datatype + Byte/Word-Order) +
      Konsequenzen (Trigger-006-Re-Eval-Hinweis).
    - §2.3 Decision M-c (Polling — direkt-sync, kein
      Background-Thread) + Konsequenzen.
    - §2.4 Decision M-d (Function-Code-Mapping) +
      Konsequenzen.
    - §2.5 Decision M-e (Slave-Unit-ID) +
      Konsequenzen.
    - §2.6 Decision M-f (Test-Sibling in-process) +
      Konsequenzen.
  - §3 Alternativen (jeweils 1–2 Varianten je Decision).
  - §4 Konsequenzen (`AC-ADAPTER-LIGHTWEIGHT`-Pflicht,
    Welle-4-Implementer-Auflagen, Trigger-006-Re-Eval).
  - §5 Status-Pfad (`Proposed → Provisional → Accepted`).
- Kein Code-Pfad-Touch.
- Pattern analog M4-Welle-2-C1 `4e102b8` (ADR 0031
  Proposed) und M4-Welle-1-C1 `b840e7a` (ADR 0030
  Proposed).

### C2 — `feat(welle-3)`: protocol_modbus + Tests + In-Process-Smoke + Compose-Edit

- NEU `src/grid_gym/adapters/driven/protocol_modbus/`-
  Modul (Datei-Aufstellung in §5 Critical Files).
- NEU 4 Unit-Test-Module unter
  `tests/unit/adapters/driven/protocol_modbus/`.
- NEU `tests/integration/test_modbus_in_process_smoke.py`.
- EDIT `tests/integration/compose.yml` (Header-Kommentar-
  Sync zum in-process-Modbus-Smoke).
- EDIT `pyproject.toml` (`pymodbus>=3.6` in `[project]
  dependencies`).
- EDIT `Dockerfile` (`CRITICAL_COV_TARGETS`-Default um
  `adapters/driven/protocol_modbus` erweitert).
- `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste muss um
  `protocol_modbus` erweitert sein, sonst Override-
  Pflicht).
- `make test-integration` gruen mit Modbus-Smoke (in-
  process-Server, **kein** Container-Pull).
- `make arch-check` weiter `19/19 Contracts KEPT`:
  `AC-ADAPTER-LIGHTWEIGHT` greift fuer `protocol_modbus`
  ohne Code-Aenderung.

### C3 — `docs(plan|adr)`: Welle-3 Status/DoD-Sync + ADR-Schaerfung + Trigger-006-Re-Eval

- ADR 0032 `Proposed → Provisional` mit C2-Merge-Beleg.
- `M4-welle-3.md`-Status `In Progress → Done` mit
  C0/C1/C2-Hashes + DoD-Verifikation-Block + DoD-
  Checkliste (Pattern analog M4-welle-2.md §9).
- `M4-protocol-adapters.md §3 Welle 3`: Done-Status mit
  Commit-Belegen; Decisions-Vorbelegung-Liste in C3
  durchgehakt.
- README.md / README.de.md / roadmap.md / spec/
  architecture.md / adr/README.md: M4-Status-Sync analog
  M4-Welle-2-C3 `7e161f5` — Welle 3 `Done`, ADR 0032
  `Provisional`, „Naechster aktiver Schritt:
  M4-Welle-4 (OPC-UA-Adapter)".
- done/README.md: M4-welle-3.md-Bestand-Zeile (analog
  M4-welle-2.md-Zeile).
- **Trigger-006-Re-Eval-Notiz** in
  `docs/plan/planning/done/006-mypy-strict-bytes.md`:
  konkrete Pruefung mit dem Modbus-Code; Entscheidung
  dokumentieren (`# type: ignore`-Zahlen vor/nach
  `--strict-bytes`-Aktivierung). Wenn positiv: Trigger
  nach `next/` ziehen (separater Folge-Slice).

---

## 5. Critical Files

| Pfad                                                                              | Commit | Aktion                                          |
| --------------------------------------------------------------------------------- | ------ | ----------------------------------------------- |
| `docs/plan/planning/done/M4-welle-3.md`                                           | C0/self-close | NEU als `in-progress/M4-welle-3.md`, nach Welle-Schluss nach `done/` gewandert |
| `docs/plan/adr/0032-modbus-adapter-profile.md`                                    | C1     | NEU (`Proposed`)                                |
| `docs/plan/adr/README.md`                                                         | C1     | EDIT (ADR-0032-Zeile)                           |
| `src/grid_gym/adapters/driven/protocol_modbus/__init__.py`                        | C2     | NEU (`ModbusDeviceProtocolPort` + Modul-Docstring) |
| `src/grid_gym/adapters/driven/protocol_modbus/_config.py`                         | C2     | NEU (`ModbusProtocolPortConfig` + `ModbusRegisterConfig`) |
| `src/grid_gym/adapters/driven/protocol_modbus/_codec.py`                          | C2     | NEU (Datentyp-Konvertierung; `struct.pack`/`unpack`) |
| `src/grid_gym/adapters/driven/protocol_modbus/_port.py`                           | C2     | NEU (Decision M-c direkt-sync; Lifecycle)       |
| `src/grid_gym/adapters/driven/protocol_modbus/_errors.py`                         | C2     | NEU (typed `DeviceProtocolPort*Error`-Subclasses) |
| `tests/unit/adapters/driven/protocol_modbus/__init__.py`                          | C2     | NEU                                             |
| `tests/unit/adapters/driven/protocol_modbus/test_modbus_config.py`                | C2     | NEU (Konstruktor-Validation)                    |
| `tests/unit/adapters/driven/protocol_modbus/test_modbus_codec.py`                 | C2     | NEU (Datentyp-Roundtrip + hypothesis-Property)  |
| `tests/unit/adapters/driven/protocol_modbus/test_modbus_protocol_port.py`         | C2     | NEU (Lifecycle + Read/Write gegen mocked Client)|
| `tests/unit/adapters/driven/protocol_modbus/test_modbus_function_codes.py`        | C2     | NEU (Decision-M-d-Function-Code-Override)       |
| `tests/integration/test_modbus_in_process_smoke.py`                               | C2     | NEU (in-process `pymodbus.server.ModbusTcpServer` + E2E) |
| `tests/integration/compose.yml`                                                   | C2     | EDIT (Header-Kommentar zum in-process-Smoke)    |
| `pyproject.toml`                                                                  | C2     | EDIT (`pymodbus>=3.6` in `[project] dependencies`) |
| `Dockerfile`                                                                      | C2     | EDIT (`CRITICAL_COV_TARGETS` + `protocol_modbus`) |
| `docs/plan/adr/0032-modbus-adapter-profile.md`                                    | C3     | EDIT (`Proposed → Provisional`)                 |
| `docs/plan/adr/README.md`                                                         | C3     | EDIT (Status-Spalte `Provisional`)              |
| `docs/plan/planning/done/M4-welle-3.md`                                           | C3/self-close | EDIT (Status → Done; Hashes; DoD-Verifikation; §9 DoD-Checkliste) + Move nach `done/` |
| `docs/plan/planning/done/M4-protocol-adapters.md`                          | C3     | EDIT (§3 Welle 3 Done-Sync)                     |
| `docs/plan/planning/done/006-mypy-strict-bytes.md`                                | C3     | EDIT (Trigger-006-Re-Eval-Notiz mit Modbus-Beleg) |
| `README.md` + `README.de.md` + `docs/plan/planning/in-progress/roadmap.md` + `spec/architecture.md` | C3 | EDIT (M4-Status-Sync — Welle 3 `Done`, ADR 0032 `Provisional`, „Naechster aktiver Schritt: M4-Welle-4") |
| `docs/plan/planning/done/README.md`                                               | C3     | EDIT (M4-welle-3.md-Bestand-Zeile; analog M4-welle-2.md-Zeile) |

---

## 6. Verifikationspfad

1. **C0 (Slice-Doc)**: `make docs-check` cache-frei gruen
   (alle Link-Targets aufgeloest — insbesondere
   `../done/M4-welle-0.md`, `../done/M4-welle-1.md`,
   `../done/M4-welle-2.md`, `M4-protocol-adapters.md`,
   `../../adr/0030-…md`, `../../adr/0031-…md`,
   `../../adr/0011-…md`,
   `../../../../spec/{architecture,lastenheft}.md`,
   `../../../../src/grid_gym/adapters/driven/protocol_mqtt/`).
2. **C1 (ADR Proposed)**: `make docs-check` gruen (neuer
   ADR-Pfad existiert, `docs/plan/adr/README.md` synced).
3. **C2 (feat)**:
   - `make test-unit` gruen (1211 → 1230+ Tests; ~30 neue
     Tests: 6 Config + 10 Codec mit hypothesis-Properties
     + 8 Protocol-Port + 6 Function-Code — feste Zahl in
     C3 belegt).
   - `make test-integration` gruen mit Modbus-In-Process-
     Smoke (22 → 23 Integration-Tests; in-process-Server
     spawnt + End-to-End-Read/Write-Roundtrip durch alle
     5 Datatypes laeuft).
   - `make arch-check` gruen — `19/19 Contracts KEPT` (7
     lint-imports + 12 `tools/arch_check.py`);
     `AC-ADAPTER-LIGHTWEIGHT` erfasst `protocol_modbus`
     ohne Filter-Aenderung.
   - `make gates` cache-frei gruen ohne
     `CRITICAL_COV_TARGETS`-Override (Default-Liste um
     `adapters/driven/protocol_modbus` erweitert).
   - `make fullbuild`: in-process-Smoke selbst gruen
     (keine neuen Siblings); `image-audit` bleibt rot aus
     dem **dokumentierten** Pre-existing krb5-CVE-Grund
     (M3-Welle-7-`c61ab0d`-Drift; **nicht durch
     M4-Welle-3-Code verursacht**).
4. **C3 (Doc-Sync)**: `make docs-check` gruen mit
   geupdateten Status-Headern in 9 Docs (8 aus dem
   M4-Welle-2-Closure-Pattern + ADR 0032 selbst). Plus
   Trigger 006-Re-Eval-Notiz.

---

## 7. Risiken

- **`pymodbus 3.x`-API-Drift gegenueber 3.6-Floor**:
  pymodbus 3.x hat zwischen Minor-Versionen API-
  Aenderungen am `read_holding_registers`-Kwarg-
  Pattern (`unit` -> `slave` -> `device_id`). *Mitigation*:
  C2-Tests pinnen konkrete Kwarg-Namen; `make lock-refresh`
  zieht eine bestimmte Version, die in `uv.lock`
  festgehalten ist (Supply-Chain-Defense).
- **In-process-Server-Lifecycle-Flakiness im Integration-
  Test**: `pymodbus.server.ModbusTcpServer.serve_forever()`
  ist ein blocking-Call; im Test-Thread muss der Server
  sauber beendet werden. Falls der Stop-Pfad blockiert
  oder Race-Conditions auftreten, bleibt der Test-Prozess
  am Ende stecken. *Mitigation*: C2-Smoke benutzt
  `daemon=True`-Thread (toetet sich automatisch beim
  Prozess-Ende) und explizite `server.shutdown()` +
  `thread.join(timeout=5.0)` im Teardown.
- **Decision-M-b-Datatype-Wahl bricht reale Wechselrichter-
  Profile**: `big_endian` + `word_swap=false` ist
  Konvention, aber konkrete Hersteller (z. B. SMA, Fronius,
  Huawei) weichen ab. Wenn das Welle-3-Default-Profil
  nicht passt, muessen Welle-6-Schaerfungs-Tests konkrete
  Hersteller-Profile pinnen. *Mitigation*: ADR 0032 §2.2
  dokumentiert die Wahl als `Provisional` (nach C2-Merge);
  Per-Target-Override (`byte_order`/`word_swap`-Kwargs)
  haelt den Konfig-Pfad offen.
- **Decision-M-c-direkt-sync bricht bei Slow-Modbus-
  Devices**: ein `read()`-Call blockiert das TickLoop-
  Thread fuer den Modbus-Roundtrip (typisch 10-100 ms).
  Bei vielen Targets pro Tick koennten sich die Calls
  summieren und die Tick-Latenz sprengen. *Mitigation*:
  Welle 6 (Cross-Adapter-Hardening) kann Background-
  Polling pro Folge-ADR einfuehren (ADR-0011-Pattern;
  ADR-0032 §2.3 dokumentiert die Welle-3-Default-Wahl
  als reversibel). Welle-3-Test-Smoke benutzt
  Low-Latency-Loopback (in-process), daher keine Smoke-
  Latenz-Pruefung.
- **Decision-M-f-in-process-Server bricht bei Async-
  pymodbus-Migration**: pymodbus 3.x hat parallel zur
  Sync-API einen Async-Pfad. Wenn pymodbus die Sync-API
  in 4.x deprecaten sollte, muss Welle-3-Code in
  Welle-6+-Folge migriert werden. *Mitigation*: ADR
  0030 §2.1 sieht Adapter-internes Async->Sync-Marshal
  vor (analog Welle-4-OPC-UA-Pattern); pymodbus-Async
  ist deshalb kein Vertrag-Bruch, sondern ein interner
  Refactor. Pin-Strategie `>=3.6,<4.0` verhindert
  silent-Major-Drift.
- **Sub-Slicing-Schwelle hart hit**: Welle 3 = 1 Adapter
  + 1 ADR + 1 Integration-Smoke = exakt die Sub-Slicing-
  Obergrenze (`M4-protocol-adapters.md` §3 Praeambel).
  Falls das `pymodbus.server.ModbusTcpServer`-In-process-
  Setup zusaetzliche Schritte triggert (z. B. ein zweiter
  Integration-Smoke fuer Concurrent-Slave-IDs), bricht
  die Schwelle. *Mitigation*: C2-Scope ist normativ in §2
  In-Scope-Liste fixiert; jede Erweiterung waehrend C2
  erfordert Sub-Slice-Bezeichnung (`Welle 3a/3b`).
- **Trigger 006 (`--strict-bytes`) re-aktiviert sich
  positiv und sprengt den Welle-3-Scope**: wenn die
  C3-Re-Eval zeigt, dass `--strict-bytes` jetzt ohne
  `# type: ignore`-Inflation greift, koennte das als
  zusaetzlicher Slice in Welle 3 einfliessen. *Mitigation*:
  C3-Re-Eval ist **Notizen + Trigger-Move-Entscheidung
  only** — die Aktivierung selbst ist Folge-Slice (Welle-6-
  oder eigener Trigger-Slice). Welle-3-Scope bleibt
  Modbus-Adapter.
- **`pymodbus`-Lizenz-Drift**: pymodbus ist BSD-3-Clause
  (verifiziert per `pymodbus`-PyPI); falls upstream zu
  einer restriktiven Lizenz wechselt, koennte Welle 3
  blockieren. *Mitigation*: Floor `>=3.6` + `uv.lock`-
  Pin haelt eine spezifische Version stabil; Folge-Welle
  prueft Upstream-Drift.

---

## 8. Wandert nach

- `done/M4-welle-3.md` ist mit der Doku-Review-Folge
  2026-05-31 vollzogen. Der frueher geplante
  M4-Welle-4-Pre-C0-Move ist damit entfallen.
- ADR 0032 bleibt in `docs/plan/adr/` (kein Move; nur
  Status-Updates).
- `M4-protocol-adapters.md` bleibt in `in-progress/` bis
  M4-Welle-7-Closure.
- M4-Welle-4-Naechster-Schritt: OPC-UA-Adapter
  (`asyncua`-Wrapper). **Erster** rein-async-Stack —
  traegt die Thread+Loop-Marshal-Konstruktion (siehe ADR
  0030 §2.1) produktiv vor; Decision M-c (Welle-3-direkt-
  sync) ist **nicht** wiederverwendbar fuer Welle 4 —
  asyncua erzwingt das Thread+Loop-Pattern.

---

## 9. DoD-Checkliste (Welle-Schluss, mit C3 abgehakt)

Pattern analog M4-welle-2.md §9. Belege siehe
**DoD-Verifikation**-Block im Status-Header oben + §4
Liefer-Reihenfolge fuer die per-Commit-Aktion.

**In-Scope-Items (alle abgehakt mit C3):**

- [x] **ADR 0032 angelegt** — `Proposed` (C1 `a86ac46`) →
  `Provisional` (C3), mit Decisions M-a/M-b/M-c/
  M-d/M-e/M-f alle **final** (inline Register-Schema, 5
  Datatypes mit Byte-Order-/Word-Swap-Matrix, direkt-sync
  ohne Thread-Marshal, FC03/FC10-Defaults mit FC04/FC06-
  Overrides, Slave-Unit-ID per Target, in-process
  pymodbus-Server fuer Smoke). Code:
  [`../../adr/0032-modbus-adapter-profile.md`](../../adr/0032-modbus-adapter-profile.md).
  Review-Folge:
  [`031-modbus-adapter-review-folge.md`](031-modbus-adapter-review-folge.md)
  hat den FC06-Config-Guard fuer Multi-Register-Datatypes
  geliefert.
- [x] **Modbus-Port produktiv** — `ModbusDeviceProtocolPort`
  als `DeviceProtocolPort`-Implementer unter
  [`../../../../src/grid_gym/adapters/driven/protocol_modbus/`](../../../../src/grid_gym/adapters/driven/protocol_modbus/)
  (5 Dateien: `__init__.py` + `_config.py` + `_codec.py`
  + `_port.py` + `_errors.py`). Modul-Docstring in
  `__init__.py` traegt Lastenheft-Z.-1161–1163-Pflicht
  (Simulations-/Testadapter, **keine** produktive
  Anlagensteuerung). NEU mit C2 `d721982`.
- [x] **Unit-Tests fuer 4 Test-Aspekte** — 95 neue Tests
  (1211 → 1306): ~25 Config-Validation + ~30 Codec-
  Roundtrip (inkl. hypothesis-Property-Tests pro
  Datatype + Byte-Order/Word-Swap-Matrix) + ~24 Lifecycle/
  Read+Write mit mocked pymodbus-Client + ~16 Function-
  Code-Override. Code:
  [`../../../../tests/unit/adapters/driven/protocol_modbus/`](../../../../tests/unit/adapters/driven/protocol_modbus/).
- [x] **Integration-Smoke produktiv** —
  [`../../../../tests/integration/test_modbus_in_process_smoke.py`](../../../../tests/integration/test_modbus_in_process_smoke.py)
  spawnt `pymodbus.server.ModbusTcpServer` in
  `threading.Thread(target=server.serve_forever,
  daemon=True)`; End-to-End-Read/Write-
  Roundtrip gegen `ModbusDeviceProtocolPort` durch alle
  5 Datatypes im Default-Profil; expliziter
  `server.shutdown()` + `thread.join(timeout=5.0)`-Teardown.
  Byte-Order-/Word-Swap-Matrix und Unit-ID-Override sind
  nicht Teil dieses E2E-Smokes; die bewusste Abgrenzung ist
  in
  [`031-modbus-adapter-review-folge.md`](031-modbus-adapter-review-folge.md)
  dokumentiert.
- [x] **`tests/integration/compose.yml` Header-Kommentar
  syncht** — Welle-3-C2-Edit dokumentiert die bewusste
  Decision-M-f-Wahl (in-process pymodbus-Server statt
  testcontainers-Sibling) als Pattern-Praezedenz fuer
  Welle 4 (asyncua) und Welle 5 (DNP3/IEC).
- [x] **`pyproject.toml` erweitert** — `pymodbus>=3.6,<4.0`
  in `[project] dependencies` (Floor 3.6 wegen API-Stabilitaet;
  Pin `<4.0` schuetzt gegen Sync-API-Deprecation in 4.x —
  ADR 0032 §2.3 Konsequenz-Hinweis); `pymodbus`-Eintrag in
  den AC-PORTS-NO-FW/AC-NO-FW-Forbidden-Listen unveraendert
  (Welle-0-Vorbelegung).
- [x] **`Dockerfile` erweitert** — `CRITICAL_COV_TARGETS`-
  Default um
  `src/grid_gym/adapters/driven/protocol_modbus` ergaenzt
  (Pattern analog `protocol_mqtt`-Eintrag aus
  M4-Welle-2-C2 `f33bb4e`).
- [x] **`AC-ADAPTER-LIGHTWEIGHT` greift fuer
  `protocol_modbus`** — `tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`-Filter erfasst den
  neuen Pfad **ohne Code-Aenderung**; `make arch-check`
  weiter `19/19 Contracts KEPT`.
- [x] **C3-Doc-Sync** — `M4-welle-3.md` Status
  `In Progress → Done` (C3), ADR 0032
  `Proposed → Provisional` (C3),
  `M4-protocol-adapters.md §3 Welle 3` Done-Markierung
  (C3), Top-Level-Doku-Sync in 6 Docs
  (`README.md` + `README.de.md` + `roadmap.md` +
  `spec/architecture.md` (keine §7-Aenderung — ADR 0030
  bleibt Surface-Vertrag) + `adr/README.md`-Zeile 52
  (ADR 0032 `Proposed → Provisional`) + `done/README.md`)
  auf den Welle-3-Endstand.
- [x] **Trigger-006-Re-Eval** —
  [`../done/006-mypy-strict-bytes.md`](../done/006-mypy-strict-bytes.md)
  syncht mit konkretem Modbus-Code-Beleg: `mypy
  --strict-bytes` laeuft cache-frei **gruen** gegen
  `src/grid_gym/adapters/driven/protocol_modbus/` ohne
  zusaetzliche `# type: ignore`-Inflation (bestehende 2
  `# type: ignore[no-untyped-call]` in `_port.py:128/148`
  sind pymodbus-API-spezifisch, kein bytes-Bezug).
  Entscheidung: Trigger ist aktivierungs-reif; die
  eigentliche Aktivierung bleibt ein separater Folge-Slice.

**Anti-Scope-Items (alle gehalten):**

- [x] **Keine OPC-UA-/DNP3-/IEC-Adapter** in C2 —
  verifiziert: keine neue Datei unter
  `adapters/driven/protocol_{opcua,dnp3,iec}/`.
- [x] **Kein OTel-Span-Wrap** der Modbus-Adapter-Calls —
  verifiziert: kein Import von
  `adapters/driven/telemetry_otlp/` in `protocol_modbus/`;
  TracePort-Wrap bleibt Welle-6-Material.
- [x] **Kein RandomPort-Determinismus** fuer Slave-/
  Register-Adressen — verifiziert: `ModbusRegisterConfig`
  hat keinen Auto-Generierungs-Pfad fuer Adressen;
  Welle-3-Default-Werte und explizite Per-Target-Config
  decken alle Use-Cases ab.
- [x] **Keine Scenario-Schema-Erweiterung jenseits des
  Decision-M-a-Pattern** — verifiziert: kein Touch an
  `scenario/validator.py` und kein neuer YAML-Top-Level-
  Block. `ModbusProtocolPortConfig` ist Adapter-intern;
  Scenario-Integration bleibt Welle-3-frei per
  AC-HEXAGON-PURE.
- [x] **Keine Welle-2-MQTT-Adapter-Aenderungen** —
  verifiziert: kein Edit an
  `src/grid_gym/adapters/driven/protocol_mqtt/` in C2.
- [x] **Keine testcontainers-Modbus-Server-Sibling**
  (Decision M-f) — verifiziert: in-process-Pfad
  produktiv via `pymodbus.server.ModbusTcpServer`-Thread;
  kein neuer `compose.yml`-Sibling-Service; keine
  Docker-Image-Pull-Latenz.
- [x] **Keine Bewegung der 17 Open-Trigger** mit
  Ausnahme der Trigger-006-Re-Eval-Notiz — verifiziert:
  `docs/plan/planning/open/` unveraendert; nur Body von
  `006-mypy-strict-bytes.md` mit Modbus-Beleg
  aktualisiert. Physischer Move (`git mv open/ → next/`)
  ist Folge-Slice.
- [x] **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md` —
  verifiziert: `roadmap.md` §3 M4 Checkboxen weiterhin
  alle ungehakt (2 von 7 DoD-Items geliefert: MQTT
  Welle 2 + Modbus Welle 3; Sweep in Welle 6).
- [x] **Kein `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-
  Property-Test** in Welle 3 — verifiziert: nur Smoke-
  Regression-Schutz via `make arch-check`. Welle-1-§7-
  Folge-Pflicht bleibt auf Welle 6 verschoben (Pattern
  fortgefuehrt aus M4-Welle-2-C3 `7e161f5`).
