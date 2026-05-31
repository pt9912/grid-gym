# Slice-Plan — M4 Protokolladapter — In Progress

**Status:** In Progress — eroeffnet 2026-05-26 mit M4-Welle-0
(`d0bb16e` Slice-Doc + diesem Commit). Fuenf Sub-Adapter
(MQTT, Modbus TCP, OPC-UA, DNP3, IEC 61850) werden ueber
Welle 0..7 verteilt geliefert. M4-Slice-Plan wandert nach
`done/` mit Welle-7-Closure.

**Datum:** 2026-05-26 (in `in-progress/` direkt eroeffnet
ohne `next/`-Zwischenschritt; Welle-0-Doc-Hoheit fuer den
Hintergrund liegt in [`M4-welle-0.md`](../done/M4-welle-0.md) §1).

**Bezug:**

- [`roadmap.md`](roadmap.md) §3 M4 (Lieferziel, DoD-
  Checkliste, Architekturartefakte).
- M3-Closure-Notiz
  [`../done/M3-faults-agents-observability.md`](../done/M3-faults-agents-observability.md) +
  [`../done/M3-results.md`](../done/M3-results.md).
- M4-Welle-0-Slice-Begleit-Doc
  [`M4-welle-0.md`](../done/M4-welle-0.md) (Welle-0-Decision-Liste +
  Trigger-Triage).
- Lastenheft §16 (`GG-MQTT-001`, `GG-MODB-001`,
  `GG-OPCUA-001`, `GG-DNP3-001`, `GG-IEC-001` — alle SOLLTE;
  Z. 1120–1163 inkl. Cross-Cutting-Pflicht
  „Simulations-/Testadapter, keine produktive
  Anlagensteuerung").
- Architektur §7 (`GG-AR-PORT-DRN-007` —
  `DeviceProtocolPort`) + §8.2 (Read/Write-Operationen +
  Topic-/Register-/Node-/LN/CDC-Profile) + §16 (Deployment-
  Sicht: keine eigenen Container; Adapter leben im
  `simulation`-Worker — Welle-0-Inferenz, Welle-1-ADR
  setzt die Aussage scharf).
- [`../done/welle-0.md`](../done/welle-0.md) §3 (M3-Welle-0-
  Pattern fuer reine Doc-Welle).
- Offene Trigger
  [`../open/004`](../open/004-canonical-encoder-alternative-adr.md)
  (canonical encoder — potenziell MQTT-Payload-relevant) und
  [`../open/006`](../open/006-mypy-strict-bytes.md)
  (`--strict-bytes` — potenziell Modbus-Register-relevant).

---

## 1. Zweck

M4 liefert fuenf Driven-Adapter ueber `GG-AR-PORT-DRN-007`
(`DeviceProtocolPort`) als Bruecke zwischen externen
Feldprotokollen und dem Tick-Loop-Vertrag:

- **MQTT** (`GG-MQTT-001`): Topic-Schema, Payload-Format,
  QoS, Pub/Sub-Richtung, Fehlerverhalten + Zuordnung zu
  Simulationszeit; deterministischer Adapter-Smoke-Test.
- **Modbus TCP** (`GG-MODB-001`): Register-Mapping,
  Datentypen, Byte-Reihenfolge, Read/Write-Operationen,
  Timeout-Verhalten; deterministischer Adapter-Smoke-Test
  mit mindestens einem Read- und einem Write-Pfad.
- **OPC-UA** (`GG-OPCUA-001`): Node-IDs, Datentypen,
  Read/Write-Pfade, Fehlerverhalten + Zuordnung zu
  Simulationszeit.
- **DNP3** (`GG-DNP3-001`): Points, Variations,
  Qualitaetsflags, Fehlerverhalten — **oder** dokumentierter
  Verzicht via Roadmap §3 M4 DoD.
- **IEC 61850** (`GG-IEC-001`): Logical Nodes,
  Datenattribute, Report-/Control-Verhalten — **oder**
  dokumentierter Verzicht via Roadmap §3 M4 DoD.

Cross-Cutting-Pflicht aus Lastenheft Z. 1161–1163: Adapter
sind klar als **Simulations- und Testadapter** zu
dokumentieren; **keine** produktive Anlagensteuerung.

M4 schliesst die DoD-Restposten fuer M4 in `roadmap.md §3 M4`
(7 Checkboxen: MQTT, Modbus, OPC-UA, DNP3, IEC-61850,
`AC-ADAPTER-LIGHTWEIGHT`, Integration-Tests). Welle 7
schliesst M4 in `done/M4-protocol-adapters.md` ab.

---

## 2. Erfolgskriterien

1. **`DeviceProtocolPort`-Surface produktiv**:
   `GG-AR-PORT-DRN-007` — Protocol-Vertrag mit Read/Write-
   Operationen, Lifecycle (`start`/`stop`), Sync/Async-
   Bridge-Pattern (Decision in Welle 1). Code-Pfad:
   `src/grid_gym/hexagon/ports/driven/device_protocol.py`
   (neu in Welle 1 — geliefert mit C2 `d09adf3`; Welle-1
   Closure 2026-05-30, siehe §3 Welle 1).
2. **Mindestens drei produktive Adapter**: MQTT (Welle 2)
   + Modbus (Welle 3) + OPC-UA (Welle 4). DNP3 und
   IEC 61850 (Welle 5) sind entweder produktiv **oder**
   dokumentiert verzichtet.
3. **Pro Adapter ein Integration-Smoke via
   testcontainers**: Pattern analog Welle 6c
   ([`../done/009-tests-integration-compose.md`](../done/009-tests-integration-compose.md)).
   Mosquitto fuer MQTT, Modbus-Server-Container fuer Modbus,
   OPC-UA-Server-Container fuer OPC-UA. (Begriff
   „Adapter-Smoke" aus Lastenheft Z. 1126/1135 ist
   inhaltlich identisch — dieser Slice-Plan verwendet
   konsequent „Integration-Smoke".)
4. **`AC-ADAPTER-LIGHTWEIGHT` greift fuer alle
   `adapters/driven/protocol_*`-Module**: kein Sickern von
   Fachlogik in Adapter (Roadmap §3 M4 DoD). Code-Pfad:
   `tools/arch_check.py:_check_adapter_lightweight()`
   (Z. 1093) + `_is_adapter_lightweight_path()` (Z. 1067) —
   der Pfad-Filter erfasst `protocol_*` bereits seit
   M3-Welle-6 (Z. 1089: `bucket.startswith("protocol_")`).
   Welle 1 verifiziert nur, dass kein Adapter-Commit aus
   Welle 2+ die Erfassung versehentlich aufweicht
   (Regression-Schutz, keine Filter-Ergaenzung noetig).
5. **Adapter sind als Simulations-/Testadapter
   dokumentiert** (Lastenheft Z. 1161–1163): jedes
   Adapter-Modul hat README-Notiz oder Modul-Docstring mit
   „Simulations-/Testadapter; keine produktive
   Anlagensteuerung".
6. **Default-`make gates` ohne `CRITICAL_COV_TARGETS`-
   Override gruen**: Default-Liste wird in Welle 2/3/4
   schrittweise um `adapters/driven/protocol_*` erweitert
   (vor Closure).
7. **`make fullbuild` gruen ohne Override**:
   M4-Abschluss-Gate (analog M3-Welle-6-Gate). Compose-Smoke
   bleibt cache-frei gruen mit den bisherigen Sibling-
   Containern + ggf. neuen Protokoll-Brokern in
   `tests/integration/compose.yml`.
8. **End-to-End-Sweep S-1..S-6 (analog M3-Welle-7 §4)** mit
   M4-spezifischen S-Items (siehe §3 Welle 7 unten).

**Anti-Erfolgskriterien** (bewusst NICHT in M4):

- Keine produktive Anlagensteuerung (Lastenheft Z. 1161–1163
  ist strukturell).
- Keine UI-Anbindung der Adapter (UI = M5).
- Keine Performance-Benchmarks (`GG-RT-004/005`) — M6.
- Keine RL-Adapter (`GG-FUTURE-001/002`) — Folge-Slice
  ueber Trigger
  [`../open/030`](../open/030-rl-adapter.md).
- Keine SOLLTE-Geraete/Netz/Battery (Trigger
  [`../open/016..024`](../open/)) — eigene Slices nach M4.

---

## 3. Liefer-Reihenfolge (Wellen)

**Sub-Slicing-Schwelle** (scharf): Eine Welle wird **vor**
dem Start in 2 oder mehr Sub-Wellen geteilt, wenn sie
**gleichzeitig** mehr als eine der folgenden drei Kategorien
in einem Commit landen wuerde:

- mehr als einen Protokoll-Adapter (`protocol_<name>/`),
- mehr als einen neuen ADR,
- mehr als einen Integration-Smoke (testcontainers-
  Sibling) in `tests/integration/compose.yml`.

Default: Welle-Bezeichnung `Welle Na/Nb/...` mit Eintrag in
den Closure-Ergebnissen.

Wellen sind atomar; jede Welle endet mit einem gruenen
`make fullbuild`-Lauf oder einem dokumentierten Welle-lokalen
`CRITICAL_COV_TARGETS`-Override. Default-Gate-Sprung erfolgt
in den jeweiligen Adapter-Wellen (Welle 2/3/4).

### Welle 0 — Vorabraeumung + Slice-Plan-Eroeffnung (in progress)

- Slice-Begleit-Doc [`M4-welle-0.md`](../done/M4-welle-0.md) (C0
  `d0bb16e`).
- M4-Slice-Plan (dieses Dokument, C1 `4451c60`).
- Review-Folge `9f4ee74` (3 High + 5 Medium + 5 Low
  Findings; Decision-1-Widerspruch geloest, Checkbox-Zahl
  korrigiert, `AC-ADAPTER-LIGHTWEIGHT`-Status-Drift
  entschaerft).
- M4-Welle-0-Trigger-Triage (C2): Drift-Check der 17 Open-
  Trigger gegen M4-Scope; Detail-Begruendung in
  [`M4-welle-0.md`](../done/M4-welle-0.md) §3 „Trigger-Drift-Notiz".
  - Open-Trigger
    [`004`](../open/004-canonical-encoder-alternative-adr.md)
    (`canonical encoder` Alternative `orjson`/`msgspec`) —
    **M4-Drift**: MQTT-Payloads sind `bytes`; ein
    performanterer JSON-Encoder koennte den MQTT-Publish-
    Pfad bedienen. **Aktivierung**: erst bei messbarem
    Perf-Druck am MQTT-Publish-Throughput; bleibt in
    `open/`. Welle 6 (Cross-Adapter-Hardening) haelt die
    Re-Eval-Notiz fest.
  - Open-Trigger
    [`005`](../open/005-pyright-vs-mypy-reeval.md)
    (`pyright`-vs-`mypy`-Re-Eval) — **M4-nicht-blockend**.
    Adapter-Module fuehren keine neuen generischen Protocols
    ein. **Aktivierung**: unveraendert (bei generischen
    Protocols in `ports/*`); bleibt in `open/`.
  - Open-Trigger
    [`006`](../open/006-mypy-strict-bytes.md)
    (`--strict-bytes`) — **M4-Drift**: Modbus-Register
    forcieren erstmals produktive `bytes`/`int`/`float`-
    Konvertierungen im Adapter-Code (Welle 3); MQTT-
    Payloads beruehren `bytes`/`bytearray` (Welle 2).
    **Aktivierung**: nach M4-Welle-3 (Modbus) re-evaluieren,
    ob `--strict-bytes` jetzt ohne `# type: ignore`-Inflation
    greift; bleibt vorerst in `open/`. Welle 6 haelt die
    Re-Eval-Notiz fest.
  - Open-Trigger
    [`007`](../open/007-pyright-precommit-adr.md)
    (`pyright` als Pre-Commit-Hook) — **M4-nicht-blockend**:
    Dev-Experience-Trigger. **Aktivierung**: unveraendert
    (bei Editor-Parity-Druck); bleibt in `open/`.
  - Open-Trigger
    [`008`](../open/008-sbom-activation.md)
    (`make sbom`) — **M4-fremd**: gehoert zum Release-
    Workflow in M6. **Aktivierung**: unveraendert (mit
    erster Artefakt-Veroeffentlichung); bleibt in `open/`.
  - Open-Trigger
    [`011`](../open/011-mlrandomport-subseed-width.md)
    (`MLRandomPort` Sub-Seed-Wortbreite) — **M4-fremd**:
    Multi-Agent-Trigger. **Aktivierung**: unveraendert
    (bei hochskalierter Multi-Agent-Welle); bleibt in
    `open/`.
  - Open-Trigger
    [`016..019`](../open/) (SOLLTE-Geraete:
    EV-Charger/Transformer/Wind/Diesel) — **M4-fremd**:
    keine Geraete-Erweiterung in M4. **Aktivierung**:
    unveraendert (eigene Slices nach M4); bleiben in
    `open/`.
  - Open-Trigger
    [`020..022`](../open/) (SOLLTE-Netz: Inselnetz,
    Transformatorgrenzen, Blindleistung) — **M4-fremd**:
    keine Netz-Erweiterung in M4. **Aktivierung**:
    unveraendert; bleiben in `open/`.
  - Open-Trigger
    [`023..024`](../open/) (SOLLTE-Battery:
    Temperatur, Zellspannung) — **M4-fremd**: keine
    Battery-Erweiterung in M4. **Aktivierung**:
    unveraendert; bleiben in `open/`.
  - Open-Trigger
    [`026`](../open/026-bess-simulation-reserve-market-spike.md)
    (BESS-Reserve-Market-Spike) — **M4-fremd**: Multi-
    Agent-/RL-Folge-Slice. **Aktivierung**: unveraendert;
    bleibt in `open/`.
  - Open-Trigger
    [`030`](../open/030-rl-adapter.md) (RL-Adapter ueber
    Multi-Agent-Bus) — **M4-fremd**: Multi-Agent-Folge-
    Slice. **Aktivierung**: unveraendert; bleibt in
    `open/`.

**Welle-0-Gate:** kein Default-Gate-Sprung; reines Doc-
Arbeitspaket. `make docs-check` cache-frei gruen
(Verifikation in C0/C1/C2).

### Welle 1 — DeviceProtocolPort-Foundation (Done 2026-05-30)

**Status:** Done. Slice-Begleit-Doc
[`../done/M4-welle-1.md`](../done/M4-welle-1.md) (gewandert
nach `done/` mit M4-Welle-2-Pre-C0 `81b5cba` + Pre-C0-Sync).
ADR 0030 ist `Provisional`.

- [x] **ADR 0030** (erster M4-ADR) fuer
  `DeviceProtocolPort`-Surface mit Entscheidungen aus
  [`M4-welle-0.md`](../done/M4-welle-0.md) §3
  Decision-Liste — `Provisional` mit C3 (2026-05-30):
  - [x] Decision 2 (Sync vs. async Vertrag, **final**):
    sync-`Protocol`; Adapter-interner Thread/Queue oder
    asyncio-Event-Loop-Thread fuer async-Stacks
    (`asyncua`, ggf. DNP3/IEC). ADR §2.1.
  - [x] Decision 3 (Lifecycle, **final**): expliziter
    Caller-Scope via
    `TickLoop.start_protocol_ports()` /
    `stop_protocol_ports()` (FIFO-Start, LIFO-Stop,
    idempotent, Best-Effort-Partial-Cleanup mit
    `__context__`-Chain). **Kein** `TickLoop.run()`.
    ADR §2.2.
  - [x] Decision 7 (Snapshot-Pflicht, **final**):
    stateless aus Replay-Sicht; Reconnect-State volatile.
    Reversibilitaet via ADR-0015-Pattern (Schema-Bump
    v2 → v3 als Folge-ADR, falls Welle 3+ Persistenz-
    Bedarf zeigt). ADR §2.3.
  - [x] Decision 1 (DNP3 + IEC-61850 Disposition,
    **provisorisch**): Verzicht-Default. Finale
    Disposition in Welle 5, informiert durch
    asyncua-Erfahrung aus Welle 4. ADR §2.4 +
    §6 Verzicht-Anhang-Slot.
- [x] **NEU**
  `src/grid_gym/hexagon/ports/driven/device_protocol.py`
  mit `DeviceProtocolPort`-Protocol +
  `start`/`stop`/`read`/`write` + `*Error`-Subsystem.
- [x] **EDIT**
  `src/grid_gym/hexagon/core/simulation/tick_loop.py`:
  `protocol_ports`-Konstruktor-Kwarg (Tuple, keyword-only,
  `None`-Default) + Lifecycle-Methoden (Welle-1-C2-Bonus
  ueber das urspruengliche Scope hinaus — die Lifecycle-
  Mechanik gehoert organisch zum Port-Vertrag).
- [x] `AC-ADAPTER-LIGHTWEIGHT`-Pfad-Filter (Decision 6) —
  Regression-geprueft (`tools/arch_check.py:1089`
  `bucket.startswith("protocol_")` greift unveraendert);
  19/19 Contracts KEPT (7 lint-imports + 12
  `tools/arch_check.py`; finales Gates-Echo:
  `arch-check (19 contracts)`).
- [x] **Unit-Tests** (+23: 1138 → 1161): 12 fuer
  Port-Protocol-Vertragsverhalten + 11 fuer
  TickLoop-Lifecycle.

**Welle-1-Gate (Done 2026-05-30):** `make test-unit` gruen
mit `DeviceProtocolPort`-Protocol- und TickLoop-Lifecycle-
Tests (1138 → 1161 = +23). `make arch-check` + `make gates`
cache-frei gruen ohne `CRITICAL_COV_TARGETS`-Override.
Default-`CRITICAL_COV_TARGETS` unveraendert (Adapter-
Erweiterung kommt mit Welle 2/3/4).
**Commit-Belege:** C0 `f8cbe9d` (Slice-Doc) + C1 `b840e7a`
(ADR 0030 Proposed) + Review-Folge `ad3dff8` (3H + 4M + 5L)
+ H4-Korrektur `111c464` (Decision 3 auf Caller-Scope) +
C2 `d09adf3` (feat) + EoD-Sync `f8ed791` (Top-Level-Doku) +
C3 (dieser Commit; ADR 0030 → `Provisional`, `M4-welle-1.md`
→ `Done`, diese §3-Welle-1-Section auf Done).

### Welle 2 — MQTT-Adapter (Done 2026-05-30)

**Status:** Done. Slice-Begleit-Doc
[`../done/M4-welle-2.md`](../done/M4-welle-2.md) (gewandert
nach `done/` mit M4-Welle-3-Pre-C0 `0d6ad6c` + Pre-C0-Sync).
ADR 0031 ist `Provisional`.

- [x] **ADR 0031** (zweiter M4-ADR) — `Provisional`
  mit C3 (2026-05-30) nach C1 `4e102b8` (Proposed) und
  C2 `f33bb4e` (feat-Merge). Vier Decisions aus
  [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
  Decision 4 alle **final**:
  - [x] Decision 4a (Topic-Schema, **final**): inline im
    `protocol_ports`-Scenario-YAML-Block;
    `MqttProtocolPortConfig.topics: Mapping[device_id,
    MqttTopicConfig]`. Kein separater
    `mqtt_profiles`-Top-Level (YAGNI; Welle-6-
    Schaerfungspfad bleibt offen via ADR 0011).
  - [x] Decision 4b (Payload-Codec, **final**):
    `canonical_json` (Trigger-014-Quelle); Trigger 004
    bleibt in `open/` mit Re-Eval-Bedingung „messbarer
    Perf-Druck am MQTT-Publish-Throughput in Welle 6".
  - [x] Decision 4c (QoS, **final**): `QoS 0` Telemetry,
    `QoS 1` Commands, `QoS 1` Subscribe — pro Topic
    ueberschreibbar.
  - [x] Decision 4d (Callback->Sync-Marshal, **final**):
    Per-Target `queue.Queue` mit Lazy-Init im paho-mqtt-
    `on_message`-Callback. `read()` macht `get_nowait()`
    (nicht-blockierend); `write()` ruft
    `client.publish()` direkt (thread-safe per
    paho-Doku). Callback-Exceptions werden via
    `safe_callback` geschluckt+geloggt (`error_translation.py`
    mit BLE001-per-file-ignore aus Welle-0-Vorbelegung).
- [x] **NEU**
  `src/grid_gym/adapters/driven/protocol_mqtt/`-Modul
  (7 Dateien): `__init__.py` (Public-Reexports +
  Lastenheft-Z.-1161–1163-Pflichtnotiz) + `_config.py`
  (Decision 4a) + `_codec.py` (Decision 4b) +
  `_topic_resolver.py` (Decision 4d-Helper) + `_port.py`
  (Decision 4d Hauptklasse) + `_errors.py` (5 typed
  Sub-Errors) + `error_translation.py`
  (BLE001-Callback-Boundary).
- [x] **NEU Integration-Smoke** via testcontainers
  (`eclipse-mosquitto:2`-Sibling mit Inline-Anonymous-
  Config). End-to-End-Pub/Sub-Roundtrip gegen
  `MqttDeviceProtocolPort` mit Bounded-Poll-Loops.
- [x] **EDIT `tests/integration/compose.yml`** (Header-
  Kommentar-Sync: Postgres + otel-collector + Mosquitto
  als testcontainers-Siblings dokumentiert).
- [x] **EDIT `pyproject.toml`** (`paho-mqtt>=2.0` in
  `[project] dependencies`); **EDIT `uv.lock`**
  (`paho-mqtt v2.1.0` via `make lock-refresh`); **EDIT
  `Dockerfile`** (`CRITICAL_COV_TARGETS`-Erweiterung um
  `adapters/driven/protocol_mqtt`).
- [x] `AC-ADAPTER-LIGHTWEIGHT`-Pfad-Filter — erfasst
  `protocol_mqtt` ohne Filter-Aenderung; 19/19 Contracts
  KEPT.

**Welle-2-Gate (Done 2026-05-30):** `make test-integration`
gruen mit MQTT-Smoke gegen Mosquitto-Sibling (21 → 22
Integration-Tests). `make test-unit` gruen (1161 → 1211 =
+50 Unit-Tests). `make arch-check` gruen (19/19 = 7
lint-imports + 12 `tools/arch_check.py`). `make gates`
cache-frei gruen ohne `CRITICAL_COV_TARGETS`-Override
(Default-Liste um `adapters/driven/protocol_mqtt`
erweitert). **Commit-Belege:** C0 `3b633f6` (Slice-Doc) +
C1 `4e102b8` (ADR 0031 Proposed) + C2 `f33bb4e` (feat:
protocol_mqtt + Tests + Integration-Smoke + Compose/
pyproject/Dockerfile-Edits) + C3 (dieser Commit; ADR 0031
→ `Provisional`, `M4-welle-2.md` → `Done`, diese §3-
Welle-2-Section auf Done, Top-Level-Doku-Sync in 5 Docs).

### Welle 3 — Modbus-TCP-Adapter (Done 2026-05-30)

**Status:** Done. Slice-Begleit-Doc
[`M4-welle-3.md`](M4-welle-3.md) (bleibt in `in-progress/`
bis M4-Welle-4-Pre-C0-Move; Pattern analog M4-Welle-1/2).
ADR 0032 ist `Provisional`.

- [x] **ADR 0032** (dritter M4-ADR) — `Provisional`
  mit C3 (2026-05-30) nach C1 `a86ac46` (Proposed) und
  C2 `d721982` (feat-Merge). Sechs Decisions aus
  [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
  Decision-Liste (analog ADR-0031-Pattern fuer Modbus
  uebertragen) alle **final**:
  - [x] Decision M-a (Register-Schema, **final**):
    inline im `protocol_ports`-Scenario-YAML-Block
    (Pattern-Praezedenz ADR 0031 §2.1);
    `ModbusProtocolPortConfig.registers: Mapping[device_id,
    ModbusRegisterConfig]` mit Pflicht-Feldern
    `address`/`datatype`/`access` und Optional-Feldern
    `byte_order`/`word_swap`/`unit_id`/`function_code`.
  - [x] Decision M-b (Datatype + Byte/Word-Order,
    **final**): erlaubter Datatype-Set
    `{int16, uint16, int32, uint32, float32}`; Byte-Order-
    Default `big_endian` (Modbus-TCP-Spec §4.1), Word-
    Swap-Default `false`; Per-Target ueberschreibbar.
    `int64`/`float64`/`string`/`bool-array` bleiben
    Welle-6-Schaerfungspfad offen via ADR 0011.
  - [x] Decision M-c (Polling-Pattern, **final**):
    **kein** Background-Polling-Thread; `read(target)`
    ruft `client.read_holding_registers(...)` direkt
    synchron — pymodbus-`ModbusTcpClient` passt **ohne
    Thread-Marshal** in die Sync-`DeviceProtocolPort`-
    Surface (ADR 0030 §2.1). Signifikant einfacher als
    MQTT-Decision-4d (keine `queue.Queue`-Marshal,
    keine Callback-Boundary). Tick-Latenz-Implikation
    als reversibel dokumentiert.
  - [x] Decision M-d (Function-Code-Mapping, **final**):
    Defaults FC03 (Read Holding Registers) fuer
    `access: "read"` und FC10 (Write Multiple Registers)
    bzw. FC06 (Write Single Register) fuer
    `access: "write"`; Per-Target ueberschreibbar fuer
    FC04 (Read Input Registers) und Multi-Register-
    Writes. Coil-Codes (FC01/FC02/FC05/FC0F) bleiben
    Welle-6-Schaerfung.
  - [x] Decision M-e (Slave-Unit-ID, **final**): pro
    `ModbusRegisterConfig` optionales `unit_id: int |
    None = None` mit Parent-Fallback (Default `1`);
    Range `[1, 247]` per Modbus-Spec §4.1; Multi-Slave-
    Bus-Scenarios setzen ueberschreibend.
  - [x] Decision M-f (Test-Sibling, **final**): in-process
    `pymodbus.server.StartTcpServer` im Test-Code
    (`tests/integration/test_modbus_in_process_smoke.py`),
    **kein** testcontainers-Container. Lizenz-Sicherheit
    (pymodbus BSD-3-Clause statt restriktiver Modbus-
    Server-Container-Lizenzen) + CI-Latenz-Reduktion
    (kein Docker-Image-Pull); Pattern-Praezedenz fuer
    Welle 4 (asyncua) und Welle 5 (DNP3/IEC).
- [x] **NEU**
  `src/grid_gym/adapters/driven/protocol_modbus/`-Modul
  (5 Dateien): `__init__.py` (Public-Reexports +
  Lastenheft-Z.-1161–1163-Pflichtnotiz) + `_config.py`
  (Decision M-a/M-b/M-d/M-e) + `_codec.py` (Decision M-b
  mit `struct.pack`/`struct.unpack`) + `_port.py`
  (Decision M-c direkt-sync; Function-Code-Dispatcher) +
  `_errors.py` (typed `DeviceProtocolPort*Error`-
  Subclasses).
- [x] **NEU Integration-Smoke** via in-process
  `pymodbus.server.StartTcpServer`-Thread (Decision M-f).
  End-to-End-Read/Write-Roundtrip gegen
  `ModbusDeviceProtocolPort` durch alle 5 Datatypes +
  Byte-Order-/Word-Swap-Matrix; expliziter
  `server.shutdown()` + `thread.join(timeout=5.0)`-Teardown.
- [x] **EDIT `tests/integration/compose.yml`** (Header-
  Kommentar-Sync: bewusste Decision-M-f-Notiz —
  in-process-Modbus-Server statt Sibling-Service als
  Pattern-Praezedenz fuer Folge-Wellen).
- [x] **EDIT `pyproject.toml`** (`pymodbus>=3.6,<4.0` in
  `[project] dependencies`); **EDIT `Dockerfile`**
  (`CRITICAL_COV_TARGETS`-Erweiterung um
  `adapters/driven/protocol_modbus`).
- [x] `AC-ADAPTER-LIGHTWEIGHT`-Pfad-Filter — erfasst
  `protocol_modbus` ohne Filter-Aenderung; 19/19 Contracts
  KEPT.
- [x] **Trigger-006-Re-Eval (`--strict-bytes`):**
  positive Re-Eval. `mypy --strict-bytes` laeuft
  cache-frei gruen gegen
  `src/grid_gym/adapters/driven/protocol_modbus/` ohne
  zusaetzliche `# type: ignore`-Inflation (bestehende 2
  `# type: ignore[no-untyped-call]` in `_port.py:128/148`
  sind pymodbus-API-spezifisch, kein bytes-Bezug).
  Trigger wandert nach `next/` als separater Folge-Slice
  (Memory-Konvention `feedback_git_mv`: erst `git mv`,
  dann Body-Schaerfung). Re-Eval-Notiz im Trigger-Body
  syncht mit Modbus-Beleg in C3.

**Welle-3-Gate (Done 2026-05-30):** `make test-integration`
gruen mit Modbus-In-Process-Smoke (22 → 23 Integration-
Tests). `make test-unit` gruen (1211 → 1306 = +95
Unit-Tests). `make arch-check` gruen (19/19 = 7 lint-imports
+ 12 `tools/arch_check.py`). `make gates` cache-frei gruen
ohne `CRITICAL_COV_TARGETS`-Override (Default-Liste um
`adapters/driven/protocol_modbus` erweitert). `mypy
--strict-bytes` cache-frei gruen am Modbus-Bytes-Pfad
(Trigger-006-Re-Eval positiv). **Commit-Belege:** C0
`8ef1e72` (Slice-Doc) + C1 `a86ac46` (ADR 0032 Proposed)
+ C2 `d721982` (feat: protocol_modbus + 95 Unit-Tests +
In-Process-Integration-Smoke + Compose/pyproject/Dockerfile-
Edits) + EoD-Sync `2b84361` (3 Top-Level-Docs auf C2-Stand,
kein C3-Ersatz) + C3 (dieser Commit; ADR 0032 →
`Provisional`, `M4-welle-3.md` → `Done`, diese §3-Welle-3-
Section auf Done, Top-Level-Doku-Sync in 6 Docs, Trigger-006-
Re-Eval mit Modbus-Beleg in Body).

### Welle 4 — OPC-UA-Adapter

- ADR-Folge (geplant **OPC-UA-Adapter-ADR**) mit
  OPC-UA-spezifischen Profil-Entscheidungen (Node-ID-Schema,
  Sub/Pub-Verhalten, async->sync-Bridge konkret an
  `asyncua`).
- NEU `src/grid_gym/adapters/driven/protocol_opcua/` mit
  `asyncua`-Wrapper:
  - Node-ID-Schema (Device-ID → Node-ID-Konvention).
  - Read/Write-Pfade, Fehlerverhalten.
  - async->sync-Bridge nach Welle-1-Entscheidung.
- Integration-Smoke via testcontainers
  (`open62541/open62541` o. ae. — Lizenz **vorher**
  pruefen; Fallback in-process `asyncua`-Server).

**Welle-4-Gate:** `make test-integration` gruen mit
OPC-UA-Smoke. Default-`CRITICAL_COV_TARGETS` um
`adapters/driven/protocol_opcua` erweitert.

### Welle 5 — DNP3 + IEC-61850 Disposition

- Roadmap §3 M4 DoD erlaubt explizit „dokumentierter
  Verzicht via Out-of-Scope-Note".
- Default: **dokumentierter Verzicht** mit klarer
  Begruendung (Lizenz/Maintenance-Last der
  `pydnp3`/`asyncio-iec61850`-Bibliotheken; Test-Sibling-
  Container schwer verfuegbar). Opt-In: **sehr kleiner
  Spike** (nur Read-Pfad, ein Profil) — die Entscheidung
  faellt **erst zum Welle-5-Zeitpunkt**, abhaengig von
  der Bibliotheks-/Testcontainer-Lage und der
  asyncua-Erfahrung aus Welle 4. Welle 1 hat den Verzicht
  bereits **provisorisch** im Surface-ADR festgeschrieben
  (siehe Welle 1 oben + Decision 1 in
  [`M4-welle-0.md`](../done/M4-welle-0.md)).
- Bei Verzicht: keine eigene ADR — Verzicht-Notiz wird
  Anhang zum `DeviceProtocolPort`-Surface-ADR aus Welle 1
  (siehe [`M4-welle-0.md`](../done/M4-welle-0.md) §3
  ADR-Vorbelegung „Obergrenze").
- Bei Spike: ADR-Folge (geplant **DNP3-/IEC-Spike-ADR**)
  mit reduziertem Scope + Integration-Smoke (oder
  Mock-only, falls kein Testcontainer verfuegbar).

**Welle-5-Gate (Verzicht-Variante):** `make docs-check`
gruen mit Verzicht-Anhang im Welle-1-ADR.
**Welle-5-Gate (Spike-Variante):** `make test-integration`
gruen mit Spike-Smoke (oder Mock-only-Unit-Test).

### Welle 6 — Cross-Adapter-Hardening

- Gemeinsame Mapping-Doku unter
  `docs/spec/protocol_profiles/` o. ae. (genaue Lokation in
  Welle 6): Adapter-Profil-Index mit Verweisen auf die
  Pro-Adapter-ADRs aus Welle 2/3/4.
- `tests/integration/compose.yml`-Aufraeumung: Konsolidierung
  der Sibling-Services, Healthcheck-Sync, Volume-Hygiene.
- Lastenheft- + Architektur-Sync:
  - Lastenheft §16-Implementierungs-Matrix: `🔲 M4` → `✅ M4`
    fuer alle umgesetzten Adapter; `🟡 M4` mit
    Verzicht-Notiz fuer DNP3/IEC, falls Decision 1a
    gewinnt.
  - Architektur §8.2 + §16: Adapter-Verortung scharf
    setzen (Welle-1-ADR-Pfad).
- Trigger 004/006 Re-Eval-Notiz: nach Welle 2/3 Drift
  pruefen, Entscheidung in C-Body dokumentieren.

**Welle-6-Gate:** `make fullbuild` gruen ohne Override
(M4-Abschluss-Gate). Default-`CRITICAL_COV_TARGETS` final.

### Welle 7 — Closure (1/2 Tag)

- Alle M4-ADRs (Welle 1/2/3/4 + ggf. Welle 5-Spike) auf
  `Accepted`.
- `done/M4-protocol-adapters.md` Closure-Notiz +
  `done/M4-results.md` Welle-Tabelle (Pattern analog
  `done/M3-results.md`).
- `roadmap.md`: M4 auf `Done`, M4-DoD-Checkboxen
  aktivieren, `Naechster aktiver Slice: M5` setzen.
- `README.md` / `README.de.md` / `AGENTS.md` / Status-Header
  in `roadmap.md` auf M4-Done-Stand syncen (Pattern aus
  M3-Welle-7-Folge `52fa4f8`/`6c5df38`/`0b3164a`).
- Self-Close-Move: `M4-protocol-adapters.md` per `git mv`
  nach `done/` (Memory-Konvention `feedback_git_mv`:
  Move-Only-Commit, kein Rewrite). `M4-welle-0.md` wurde
  bereits mit M4-Welle-1-Pre-C0-Move (`556ae9f`) nach
  `done/M4-welle-0.md` ueberfuehrt — kein erneuter Move in
  Welle 7.
- Open-Trigger fuer M4-Restposten (z. B. neue MQTT-Codec-
  Optimierungs-Trigger aus 004-Re-Eval).
- M4-Welle-7-End-to-End-Sweep (analog M3-Welle-7 §4):
  S-1..S-6-Verification ist Pflicht-Punkt:
  - S-1 — M4-spezifisches Vorabraeumungs-Item
    (Trigger-Triage in Welle 0).
  - S-2 — Sub-Slicing-Schwelle (§3 Praeambel oben).
  - S-3 — Default-Gate ohne Override.
  - S-4 — kein M4-spezifisches Image-Hardening-Trigger
    erwartet; aber `make image-audit` pruefen, ob die neu
    eingefuehrten Adapter-Deps (`paho-mqtt`, `pymodbus`,
    `asyncua` sowie ggf. DNP3/IEC-Stack) die Runtime-
    Image-Size-Schwelle ueberschreiten. Falls ja:
    Image-Pin-Trigger erstellen.
  - S-5 — ADR-Erweiterungs-Pattern fortgefuehrt (1..5
    neue ADRs ohne Supersedes).
  - S-6 — Lastenheft-Coverage-Sweep nach M4-Closure (M5-
    Trigger erstellen, falls relevant).

---

## 4. Out-of-Scope (bleibt fuer M5+/M6+)

- **Produktive Anlagensteuerung** (Lastenheft Z. 1161–1163)
  — strukturell ausgeschlossen.
- **UI-Anbindung der Adapter** (`GG-UI-001..009`) — M5.
- **Performance-Benchmarks** (`GG-RT-004/005`) — M6.
- **SBOM-Generierung** (Trigger 008) — M6 mit Release-
  Workflow.
- **RL-Adapter** (`GG-FUTURE-001/002`) — eigener Slice ueber
  Trigger [`../open/030`](../open/030-rl-adapter.md).
- **SOLLTE-Geraete** (`GG-DEV-015..018`) — Trigger
  [`../open/016..019`](../open/), eigene Slices nach M4.
- **SOLLTE-Netz** (`GG-GRID-005..007`) — Trigger
  [`../open/020..022`](../open/), eigene Slices nach M4.
- **SOLLTE-Battery** (`GG-BESS-006/007`) — Trigger
  [`../open/023..024`](../open/), eigene Slices nach M4.

---

## 5. Risiken und Fallback

- **Fuenf-Sub-Adapter-Vermischung**: M4 hat fuenf distinkte
  Adapter — Risiko einer Mega-Welle, die zerfaellt.
  *Fallback*: Sub-Slicing-Schwelle (§3 Praeambel) ist scharf
  formuliert; jede Welle 2..5 liefert genau einen Adapter
  plus seinen ADR plus seinen Integration-Smoke.
- **Sync/Async-Bridge bricht Welle 1**: TickLoop ist sync,
  `asyncua` und DNP3/IEC-Stacks sind async, `pymodbus` kann
  beides. Wenn die Welle-1-Entscheidung ungluecklich faellt,
  zahlen Welle 4 + Welle 5 die Komplexitaets-Rechnung.
  *Fallback*: Welle 1 entscheidet **bewusst vorlaeufig**
  (ADR-Pattern „Provisional"); falls Welle 4 (OPC-UA)
  zeigt, dass die Bridge schmerzt, traegt eine
  Welle-4-ADR-Folge die Schaerfung.
- **DNP3/IEC-Disposition kippt nach Welle 4**: asyncua-
  Erfahrung aus Welle 4 koennte die Verzicht-Variante
  (Decision 1a) im Welle 5 attraktiver oder unattraktiver
  machen. *Fallback*: Welle 5 entscheidet **erst zum
  Welle-5-Zeitpunkt** (nicht praeventiv); die Verzicht-
  Variante ist Default, der Spike ist Opt-In.
- **Test-Sibling-Container-Lizenz**: Modbus- und OPC-UA-
  Server-Container haben oft restriktive Lizenzen.
  *Fallback*: Welle 2/3/4 klaeren Lizenz **vor** der
  Adapter-Implementierung; Fallback ist ein eigener
  Mini-Server im Test-Code (Pattern aus
  `tests/integration/`).
- **`AC-ADAPTER-LIGHTWEIGHT` bricht spaet**: wenn ein
  Adapter unbeabsichtigt Fachlogik einsammelt (z. B. Unit-
  Konvertierung im MQTT-Codec), schlaegt der Architektur-
  Test erst in Welle 2+ an. *Fallback*: der Pfad-Filter
  greift bereits (`tools/arch_check.py:1089`); Welle 1
  verifiziert den Regression-Schutz per
  `make arch-check`, **bevor** Welle 2 den ersten Adapter
  liefert. Welle 2 darf nicht mit rotem
  `AC-ADAPTER-LIGHTWEIGHT` starten.
- **Snapshot-Schema-Drift durch Reconnect-State**: falls
  Decision 7 (stateless) sich in Welle 3+ als zu eng
  herausstellt (z. B. Modbus-Read-Cursor muss persistent
  sein), wird ein Snapshot-Schema-Bump faellig. *Fallback*:
  Welle 1 dokumentiert den stateless-Default als
  reversibel; ein Schema-Bump folgt dem ADR-0015-Pattern.
- **Trigger-004/006-Drift**: ein performanterer Encoder
  oder `--strict-bytes` wuerde an Welle 2/3 zerren.
  *Fallback*: beide Trigger bleiben in `open/`; M4-Welle-6
  haelt die Re-Eval-Notiz fest, kein In-M4-Implementierungs-
  Zwang.

---

## 6. Wandert nach

- ✓ `in-progress/M4-protocol-adapters.md` (dieses
  Dokument, eroeffnet 2026-05-26 mit M4-Welle-0).
- `done/M4-protocol-adapters.md` mit Closure-Notiz nach
  Welle 7.
- `done/M4-results.md` (Welle-Tabelle + Abnahme-Belege,
  Pattern aus
  [`../done/M3-results.md`](../done/M3-results.md)).
- `archive/`-Pfad nur, falls M4 umgeplant wird (z. B. M4
  nur MQTT/Modbus, M5 = OPC-UA + DNP3 + IEC, M6+ neu
  nummeriert).

Forwarder-Stub-Pflicht entsteht erst, wenn ein
`Accepted`-ADR auf den `in-progress/`-Pfad zeigt (M4-Welle-1
liefert den ersten M4-ADR; der Stub kommt dann mit Welle 7
nach M1/M2/M3-Pattern).

---

## 7. Verifikationspfad

| Erfolg                                                | Verifikation |
| ----------------------------------------------------- | ------------ |
| `DeviceProtocolPort`-Surface + Lifecycle              | `make test-unit` mit Protocol-Test (Welle 1) |
| MQTT-Adapter + Topic-Mapping                          | `make test-integration` mit Mosquitto-Sibling-Smoke (Welle 2) |
| Modbus-Adapter + Register-Mapping + R/W-Smoke         | `make test-integration` mit Modbus-Sibling-Smoke (Welle 3) |
| OPC-UA-Adapter + Node-ID-Schema + R/W-Smoke           | `make test-integration` mit OPC-UA-Sibling-Smoke (Welle 4) |
| DNP3/IEC: produktiv ODER Verzicht-Notiz               | `make test-integration` (Spike) ODER `make docs-check` (Verzicht-Anhang) (Welle 5) |
| `AC-ADAPTER-LIGHTWEIGHT` fuer alle `protocol_*`       | `make arch-check` gruen (Default, ueber alle Wellen) |
| „Simulations-/Testadapter"-Dokumentationspflicht      | `make docs-check` + Adapter-Modul-Docstring-Review (Welle 6) |
| Default-`make gates` ohne Override                    | `make gates` (Default-`CRITICAL_COV_TARGETS` um `adapters/driven/protocol_*` erweitert) (Welle 2/3/4) |
| `make fullbuild` gruen ohne Override                  | `make fullbuild` — **M4-Abschluss-Gate** (Welle 6) |
| Alle M4-ADRs `Accepted`                               | Doc-Review: `docs/plan/adr/00NN-*.md` Status `Accepted` (Welle 7) |
| End-to-End-Sweep S-1..S-6                             | Closure-Notiz: `done/M4-results.md §4` mit Per-S-Item-Belegen (Welle 7) |
