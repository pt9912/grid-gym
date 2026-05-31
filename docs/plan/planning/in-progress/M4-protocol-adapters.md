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
3. **Pro Adapter ein Integration-Smoke**: Pattern analog
   Welle 6c
   ([`../done/009-tests-integration-compose.md`](../done/009-tests-integration-compose.md)),
   aber Adapter duerfen begruendet auf in-process Server
   ausweichen, wenn Container-Lizenz oder Wartbarkeit dagegen
   sprechen. MQTT nutzt Mosquitto via testcontainers; Modbus
   nutzt seit Welle 3 bewusst einen in-process pymodbus-Server;
   OPC-UA entscheidet in Welle 4. (Begriff „Adapter-Smoke" aus
   Lastenheft Z. 1126/1135 ist inhaltlich identisch — dieser
   Slice-Plan verwendet konsequent „Integration-Smoke".)
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

Wellen sind atomar; jede Welle endet mit den im jeweiligen
Gate-Block benannten gruenen Gates. Code-Wellen 1..5 belegen
mindestens `make gates` ohne `CRITICAL_COV_TARGETS`-Override
sowie den jeweils noetigen Unit-/Integration-/Docs-Check;
`make fullbuild` ist das M4-Abschluss-Gate in Welle 6 (und
Closure-Sanity in Welle 7, falls Welle 6 nicht den finalen
Stand abdeckt). Ein Welle-lokaler `CRITICAL_COV_TARGETS`-
Override ist nur zulaessig, wenn der Gate-Block ihn explizit
dokumentiert. Default-Gate-Sprung erfolgt in den jeweiligen
Adapter-Wellen (Welle 2/3/4).

### Welle 0 — Vorabraeumung + Slice-Plan-Eroeffnung (Done 2026-05-26)

**Status:** Done. Slice-Begleit-Doc
[`../done/M4-welle-0.md`](../done/M4-welle-0.md) (gewandert
nach `done/` mit M4-Welle-1-Pre-C0 `556ae9f`). Reine
Doc-Welle ohne ADR-Lieferung.

- [x] **Slice-Begleit-Doc** —
  [`../done/M4-welle-0.md`](../done/M4-welle-0.md) als
  Welle-0-Decision-Liste + Trigger-Triage-Container; C0
  `d0bb16e`.
- [x] **M4-Slice-Plan** (dieses Dokument) — initiale
  Welle-Tabelle + Sub-Slicing-Schwelle + Anti-Erfolgs-
  kriterien; C1 `4451c60`.
- [x] **Review-Folge** — `9f4ee74` mit 3 High + 5 Medium +
  5 Low Findings: Decision-1-Widerspruch geloest, Checkbox-
  Zahl auf 7 korrigiert, `AC-ADAPTER-LIGHTWEIGHT`-Status-
  Drift entschaerft.
- [x] **Trigger-Triage (C2 `f832048`)** — Drift-Check
  der 17 Open-Trigger gegen M4-Scope (Detail-Begruendung
  in [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
  „Trigger-Drift-Notiz"; 13 Trigger triaged, davon 3
  M4-Drift mit Re-Eval-Pfad):
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

- [x] **Self-Close-Move** — `chore: git mv M4-welle-0.md
  -> done/` als M4-Welle-1-Pre-C0 (`556ae9f`, rename-only,
  memory-konform per `feedback_git_mv`).

**Welle-0-Gate (Done 2026-05-26):** kein Default-Gate-
Sprung; reines Doc-Arbeitspaket. `make docs-check` cache-
frei gruen (Verifikation in C0/C1/C2).
**Commit-Belege:** C0 `d0bb16e` + C1 `4451c60` +
Review-Folge `9f4ee74` + C2 `f832048` + Self-Close-Move
`556ae9f`.

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
[`../done/M4-welle-3.md`](../done/M4-welle-3.md) (nach
`done/` verschoben mit der Doku-Review-Folge 2026-05-31;
Welle-4-Pre-C0-Move entfaellt).
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
    Welle-6-Schaerfung. Review-Folge 2026-05-31:
    FC06 wird seit
    [`../done/031-modbus-adapter-review-folge.md`](../done/031-modbus-adapter-review-folge.md)
    im Config-Validator fail-fast auf Single-Register-
    Datatypes begrenzt.
  - [x] Decision M-e (Slave-Unit-ID, **final**): pro
    `ModbusRegisterConfig` optionales `unit_id: int |
    None = None` mit Parent-Fallback (Default `1`);
    Range `[1, 247]` per Modbus-Spec §4.1; Multi-Slave-
    Bus-Scenarios setzen ueberschreibend.
  - [x] Decision M-f (Test-Sibling, **final**): in-process
    `pymodbus.server.ModbusTcpServer` im Test-Code
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
  `pymodbus.server.ModbusTcpServer`-Thread (Decision M-f).
  End-to-End-Read/Write-Roundtrip gegen
  `ModbusDeviceProtocolPort` durch alle 5 Datatypes im
  Default-Profil (`big_endian`, kein Word-Swap,
  Parent-`unit_id=1`); expliziter `server.shutdown()` +
  `thread.join(timeout=5.0)`-Teardown. Byte-Order-/
  Word-Swap-Matrix und Unit-ID-Override sind Unit-/Mock-
  Test-Abdeckung; die bewusste E2E-Abgrenzung ist in
  [`../done/031-modbus-adapter-review-folge.md`](../done/031-modbus-adapter-review-folge.md)
  dokumentiert.
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
  Trigger ist aktivierungs-reif; die eigentliche
  Aktivierung bleibt ein separater Folge-Slice. Re-Eval-
  Notiz im Trigger-Body syncht mit Modbus-Beleg in C3.
- [x] **Review-Folge 2026-05-31** — Welle-3-Status
  bleibt `Done`; der eigene Folge-Slice
  [`031-modbus-adapter-review-folge.md`](../done/031-modbus-adapter-review-folge.md)
  hat FC06-Multi-Register-Guard, Read-/Write-
  Fehler-Taxonomie und die bewusste Smoke-Abgrenzung
  umgesetzt.

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
kein C3-Ersatz) + C3 (ADR 0032 →
`Provisional`, `M4-welle-3.md` → `Done`, diese §3-Welle-3-
Section auf Done, Top-Level-Doku-Sync in 6 Docs, Trigger-006-
Re-Eval mit Modbus-Beleg in Body) + Doku-Review-Folge
2026-05-31 (Move nach `done/`, Smoke-Abdeckung praezisiert,
Follow-up-Slice 031 angelegt).

### Welle 4 — OPC-UA-Adapter

**Status:** Pending. Vierte Code-Welle in M4 und der
**dritte konkrete Adapter** auf der `DeviceProtocolPort`-
Surface (`GG-AR-PORT-DRN-007`): OPC-UA ueber `asyncua`.
Welle 4 traegt erstmals einen **rein-async-Stack** produktiv
vor — ADR 0030 §2.1 hat die Sync-Surface-Brueckenkonstruktion
fuer asyncua bereits vorbelegt; Welle 4 implementiert sie
konkret.

- [ ] **ADR 0033** (vierter M4-ADR) — `Proposed` (C1) →
  `Provisional` (C3), mit OPC-UA-spezifischen Profil-
  Entscheidungen (Pattern analog ADR 0031/0032):
  - [ ] Decision O-a (Node-ID-Schema): inline im
    `protocol_ports`-Scenario-YAML-Block (Pattern-
    Praezedenz ADR 0031 §2.1 + ADR 0032 §2.1); pro
    `device_id` ein `OpcuaNodeConfig` mit Pflicht-Feldern
    `node_id`/`datatype`/`access`.
  - [ ] Decision O-b (async→sync-Bridge): asyncio-Loop in
    dediziertem Daemon-Thread (`run_coroutine_threadsafe`-
    Marshal); pymodbus-Direct-Sync-Decision-M-c ist **nicht**
    wiederverwendbar — asyncua erzwingt das Thread+Loop-
    Pattern.
  - [ ] Decision O-c (Datentyp-Set): OPC-UA-Built-In-Types-
    Mapping zu Python-`Decimal`/`int`/`str`/`bool`;
    konkretes Set in C1 fixiert.
  - [ ] Decision O-d (Read/Write-Pfad): `client.read_node()`
    + `client.write_node()` via Marshal; Subscription-Pfad
    bleibt Welle-6-Schaerfung offen.
  - [ ] Decision O-e (Test-Sibling): Wahl zwischen
    testcontainers (`open62541` o. ae. — Lizenz **vorher**
    pruefen!) und in-process `asyncua`-Server (Pattern-
    Praezedenz Welle 3 Decision M-f). Entscheidung in C1
    nach Lizenz-Check.
- [ ] **NEU** `src/grid_gym/adapters/driven/protocol_opcua/`-
  Modul (geplant ~6-7 Dateien analog `protocol_mqtt/`):
  `__init__.py` (Public-Reexports + Lastenheft-Z.-1161–1163-
  Pflichtnotiz) + `_config.py` (Decision O-a/O-c) +
  `_codec.py` (Datentyp-Konvertierung) + `_loop_thread.py`
  (Decision O-b async-Loop-Thread + Marshal) + `_port.py`
  (Decision O-b/O-d) + `_errors.py` (typed
  `DeviceProtocolPort*Error`-Subclasses).
  Modul-Docstring traegt Lastenheft-Z.-1161–1163-Pflicht
  (Simulations-/Testadapter, **keine** produktive
  Anlagensteuerung).
- [ ] **Unit-Tests** unter
  `tests/unit/adapters/driven/protocol_opcua/`:
  Config-Validation + Datentyp-Codec-Roundtrip +
  Async-Loop-Marshal + Lifecycle/Read+Write gegen mocked
  asyncua-Client.
- [ ] **Integration-Smoke** — `tests/integration/test_opcua_*_smoke.py`
  mit Server-Variante aus Decision O-e (Sibling-Container
  ODER in-process-`asyncua.Server`); End-to-End-Read/Write-
  Roundtrip durch das Decision-O-c-Datentyp-Set.
- [ ] **EDIT `tests/integration/compose.yml`** — Header-
  Kommentar-Sync zur Decision-O-e-Wahl (Sibling-Service
  hinzu **oder** in-process-Hinweis analog Welle 3).
- [ ] **EDIT `pyproject.toml`** — `asyncua>=1.1` (Pin nach
  C1-API-Stabilitaets-Check) in `[project] dependencies`;
  `asyncua`-Eintrag in AC-PORTS-NO-FW/AC-NO-FW-Forbidden-
  Listen pruefen (Welle-0-Vorbelegung).
- [ ] **EDIT `Dockerfile`** — `CRITICAL_COV_TARGETS`-
  Default um `adapters/driven/protocol_opcua` erweitert
  (Pattern analog Welle 2/3).
- [ ] **`AC-ADAPTER-LIGHTWEIGHT` greift fuer
  `protocol_opcua`** — `tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`-Filter erfasst den
  neuen Pfad **ohne Code-Aenderung**; Regression-geprueft
  via `make arch-check` (19/19 Contracts KEPT).
- [ ] **C3-Doc-Sync** — `M4-welle-4.md` Status
  `In Progress → Done`, ADR 0033 `Proposed → Provisional`,
  diese §3-Welle-4-Section auf Done, Top-Level-Doku-Sync
  (README + README.de + roadmap + spec/architecture +
  adr/README + done/README) auf den Welle-4-Endstand.

**Welle-4-Gate:** `make test-integration` gruen mit
OPC-UA-Smoke (Sibling-Container nach Lizenzfreigabe oder
begruendeter in-process `asyncua`-Server analog Welle-3-
Decision-M-f). `make test-unit` gruen mit den neuen
Unit-Test-Modulen. `make arch-check` weiter `19/19
Contracts KEPT`. `make gates` cache-frei gruen ohne
`CRITICAL_COV_TARGETS`-Override (Default-Liste um
`adapters/driven/protocol_opcua` erweitert).

### Welle 5 — DNP3 + IEC-61850 Disposition

**Status:** Pending. Disposition-Welle, **keine** zweite
Code-Welle wie 2/3/4. Roadmap §3 M4 DoD erlaubt explizit
„dokumentierter Verzicht via Out-of-Scope-Note". Welle 1
hat den Verzicht-Default bereits **provisorisch** in ADR
0030 §2.4 festgeschrieben; Welle 5 finalisiert ihn
(Variante A) **oder** zieht einen Mini-Spike (Variante B)
auf — Entscheidung faellt **erst zum Welle-5-Zeitpunkt**
nach asyncua-Erfahrung aus Welle 4.

**Variante A — dokumentierter Verzicht (Default):**

- [ ] **ADR-0030-§6-Verzicht-Anhang gefuellt** — DNP3-
  und IEC-61850-Verzicht-Begruendung im
  `DeviceProtocolPort`-Surface-ADR aus Welle 1
  konkret eingetragen (Lizenz/Maintenance-Last der
  `pydnp3`/`asyncio-iec61850`-Bibliotheken; Test-Sibling-
  Container schwer verfuegbar). Schaerfung des Welle-1-
  Decision-1-provisorisch-Default; **kein** Supersedes
  (Pattern ADR 0011).
- [ ] **Keine neue ADR** — Verzicht-Notiz ist Teil des
  Welle-1-ADR-Anhangs; kein separater DNP3-/IEC-ADR
  noetig (M4-Welle-0 §3 ADR-Vorbelegung „Obergrenze"
  honoriert).
- [ ] **`roadmap.md §3 M4 DoD` syncht** — `DNP3-Adapter`
  + `IEC-61850-Adapter`-Checkboxen als „dokumentierter
  Verzicht" markiert mit Verweis auf ADR-0030-Anhang.
- [ ] **Lastenheft §16-Notiz** — `GG-DNP3-001`/`GG-IEC-001`
  als „verschoben mit Begruendung" (Welle-6-Lastenheft-
  Sync-Material).

**Variante B — sehr kleiner Spike (Opt-In):**

- [ ] **NEU ADR fuer DNP3-/IEC-Spike** (geplant
  **DNP3-/IEC-Spike-ADR**) mit reduziertem Scope (nur
  Read-Pfad, ein Profil). Pattern-Praezedenz ADR 0031/0032.
- [ ] **NEU** `src/grid_gym/adapters/driven/protocol_dnp3/`
  ODER `protocol_iec61850/` mit Library-Wrapper —
  konkret eine der beiden, nicht beide (Sub-Slicing-
  Schwelle); andere bleibt Verzicht-Variante A.
- [ ] **Integration-Smoke ODER Mock-only-Unit-Test** —
  abhaengig von Test-Sibling-Verfuegbarkeit; in-process-
  Pattern analog Welle-3-Decision-M-f bevorzugt.
- [ ] **`AC-ADAPTER-LIGHTWEIGHT` greift** fuer den neuen
  Protokoll-Pfad ohne Filter-Edit.
- [ ] **C3-Doc-Sync** — `M4-welle-5.md` Status, ADR
  `Proposed → Provisional`, diese §3-Welle-5-Section auf
  Done, Top-Level-Doku-Sync.

**Welle-5-Gate (Verzicht-Variante):** `make docs-check`
gruen mit Verzicht-Anhang im Welle-1-ADR.
**Welle-5-Gate (Spike-Variante):** `make test-integration`
gruen mit Spike-Smoke (oder Mock-only-Unit-Test).

### Welle 6 — Cross-Adapter-Hardening

**Status:** Pending. Querschnitts-Welle ohne weiteren
konkreten Adapter; haertet die in Welle 2/3/4 angesammelten
Decisions und schliesst die in den frueheren Wellen bewusst
verschobenen Folge-Pflichten (`AC-ADAPTER-LIGHTWEIGHT`-
Planted-Violator-Property-Test, OTel-Span-Wrap der Adapter-
Calls, Trigger-004/006-Re-Eval-Notizen).

- [ ] **Adapter-Profil-Index** unter
  `spec/protocol_profiles/` als kanonischem Spec-Pfad
  (oder begruendete andere Lokation): Profil-Index mit
  Verweisen auf die Pro-Adapter-ADRs aus Welle 2/3/4
  (0031/0032/0033 + ggf. Welle-5-Spike-ADR).
- [ ] **`tests/integration/compose.yml`-Aufraeumung** —
  Konsolidierung der Sibling-Services, Healthcheck-Sync,
  Volume-Hygiene; Header-Kommentar fuehrt jeden Sibling
  mit Lizenz + Test-Pfad-Referenz.
- [ ] **Lastenheft §16-Implementierungs-Matrix-Sync** —
  `🔲 M4` → `✅ M4` fuer alle umgesetzten Adapter;
  `🟡 M4` mit Verzicht-Notiz fuer DNP3/IEC, falls
  Welle 5 Variante A gewaehlt hat.
- [ ] **Architektur §8.2 + §16-Sync** — Adapter-Verortung
  scharf setzen mit Welle-1-ADR-Pfad; OTel-Span-Wrap-
  Pattern dokumentiert.
- [ ] **OTel-Span-Wrap fuer `protocol_*`-Adapter** —
  TracePort-Wrap der Read/Write-Calls (in Welle 2/3/4
  bewusst verschoben; ADR 0024 §4.5 als Bezug).
- [ ] **`AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-Property-
  Test** — die in
  [`../done/M4-welle-1.md`](../done/M4-welle-1.md) §7
  als Folge-Pflicht markierte Welle-2-Mitigation
  (in Welle 2/3 bewusst auf Welle 6 verschoben) wird
  jetzt eingezogen.
- [ ] **Trigger-004-Re-Eval** — `canonical encoder`-
  Alternative (`orjson`/`msgspec`) gegen MQTT-Publish-
  Throughput-Druck pruefen; Entscheidung im Trigger-Body.
- [ ] **Trigger-006-Folge-Slice eingezogen** —
  `--strict-bytes`-Aktivierung in `[tool.mypy]` plus
  Repo-Sweep (Slice 031-Folge; Re-Eval ist in M4-Welle-3
  positiv gelaufen, M4-Welle-6 zieht die Aktivierung
  produktiv).
- [ ] **C3-Doc-Sync** — `M4-welle-6.md` Status, diese
  §3-Welle-6-Section auf Done, Top-Level-Doku-Sync.

**Welle-6-Gate:** `make fullbuild` cache-frei gruen ohne
`CRITICAL_COV_TARGETS`-Override (M4-Abschluss-Gate; analog
M3-Welle-6-Gate). Default-`CRITICAL_COV_TARGETS` final.
`make arch-check` 19/19 (oder +1 falls ein neuer Contract
aus Welle 6 entsteht, z. B. `AC-ADAPTER-NO-TIME`).

### Welle 7 — Closure (1/2 Tag)

**Status:** Pending. M4-Closure-Welle analog M3-Welle 7;
zieht alle M4-ADRs auf `Accepted`, etabliert
`done/M4-results.md` und faehrt den End-to-End-Sweep
S-1..S-6.

- [ ] **Alle M4-ADRs auf `Accepted`** — ADR
  0030/0031/0032/0033 + ggf. Welle-5-Spike-ADR;
  Pattern analog M3-Welle-7-C1.1..C1.6.
- [ ] **`done/M4-protocol-adapters.md` Closure-Notiz** —
  zusammenfassende Welle-Tabelle mit C0/C1/C2/C3-Hashes
  pro Welle, Test-Counts, Sub-Slicing-Belege, DoD-Erfuellung.
- [ ] **`done/M4-results.md`** — Detail-Welle-Tabelle +
  Abnahme-Belege (Pattern analog
  [`../done/M3-results.md`](../done/M3-results.md)):
  `make fullbuild`-Stand, Test-Bilanz (Unit + Integration),
  Coverage, Contracts, Per-Welle-Reviews.
- [ ] **`roadmap.md` M4-DoD-Checkboxen aktiviert** — alle
  7 Checkboxen in `roadmap.md §3 M4` als `[x]` markiert;
  M4 auf `Done`; „Naechster aktiver Slice: M5" gesetzt.
- [ ] **Top-Level-Doku-Sync** —
  `README.md` / `README.de.md` / `AGENTS.md` / Status-
  Header in `roadmap.md` auf M4-Done-Stand syncen
  (Pattern aus M3-Welle-7-Folge `52fa4f8` / `6c5df38` /
  `0b3164a`).
- [ ] **Self-Close-Move** — `chore: git mv
  M4-protocol-adapters.md → done/` (Memory-Konvention
  `feedback_git_mv`: Move-Only-Commit ohne Inhalts-Edit;
  Body-Updates folgen in separatem Commit). `M4-welle-0.md`
  wurde bereits mit M4-Welle-1-Pre-C0 (`556ae9f`) gemoved
  — **kein** erneuter Move in Welle 7.
- [ ] **ADR-0028-Linkpflege nach Self-Close-Move** — alle
  M4-ADRs mit `Bezug:` auf
  `planning/in-progress/M4-protocol-adapters.md` werden auf
  `planning/done/M4-protocol-adapters.md` nachgezogen.
  Kein Forwarder-Stub im alten `in-progress/`-Pfad.
- [ ] **Open-Trigger fuer M4-Restposten erzeugt** — z. B.
  neue MQTT-Codec-Optimierungs-Trigger aus 004-Re-Eval
  (falls Welle 6 ihn nicht produktiv eingezogen hat).
- [ ] **M4-Welle-7-End-to-End-Sweep S-1..S-6** (analog
  M3-Welle-7 §4) — dokumentiert in
  `done/M4-results.md §4`:
  - [ ] **S-1** — M4-spezifisches Vorabraeumungs-Item
    (Trigger-Triage in Welle 0; Resultat-Sweep in Welle 7).
  - [ ] **S-2** — Sub-Slicing-Schwelle (§3 Praeambel oben)
    eingehalten ueber Welle 1..6; Beleg-Tabelle.
  - [ ] **S-3** — Default-`make gates` ohne
    `CRITICAL_COV_TARGETS`-Override cache-frei gruen am
    Welle-7-Closure-Hash.
  - [ ] **S-4** — `make image-audit` cache-frei gruen
    (oder dokumentierter Defer-Pfad). Pruefung, ob die
    neu eingefuehrten Adapter-Deps (`paho-mqtt`,
    `pymodbus`, `asyncua` + ggf. DNP3/IEC-Stack) die
    Runtime-Image-Size-Schwelle ueberschreiten. Falls ja:
    Image-Pin-Trigger erstellen.
  - [ ] **S-5** — ADR-Erweiterungs-Pattern fortgefuehrt
    (4..5 neue ADRs ohne Supersedes; `Schaerfung-ohne-
    Supersedes` per ADR 0011 dokumentiert).
  - [ ] **S-6** — Lastenheft-Coverage-Sweep nach
    M4-Closure (M5-Trigger erstellen, falls relevant).

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

Beim Welle-7-Move entstehen keine Forwarder-Stubs. Wenn dann
`Accepted`-ADRs auf den bisherigen `in-progress/`-Pfad zeigen,
werden deren `Bezug:`-Links gemaess
[`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md)
direkt auf den neuen `done/`-Pfad gepflegt.

---

## 7. Verifikationspfad

| Erfolg                                                | Verifikation |
| ----------------------------------------------------- | ------------ |
| `DeviceProtocolPort`-Surface + Lifecycle              | `make test-unit` mit Protocol-Test (Welle 1) |
| MQTT-Adapter + Topic-Mapping                          | `make test-integration` mit Mosquitto-Sibling-Smoke (Welle 2) |
| Modbus-Adapter + Register-Mapping + R/W-Smoke         | `make test-integration` mit in-process Modbus-Smoke (Welle 3) |
| OPC-UA-Adapter + Node-ID-Schema + R/W-Smoke           | `make test-integration` mit OPC-UA-Smoke gegen Sibling-Container oder begruendeten in-process `asyncua`-Server (Welle 4) |
| DNP3/IEC: produktiv ODER Verzicht-Notiz               | `make test-integration` (Spike) ODER `make docs-check` (Verzicht-Anhang) (Welle 5) |
| `AC-ADAPTER-LIGHTWEIGHT` fuer alle `protocol_*`       | `make arch-check` gruen (Default, ueber alle Wellen) |
| „Simulations-/Testadapter"-Dokumentationspflicht      | `make docs-check` + Adapter-Modul-Docstring-Review (Welle 6) |
| Default-`make gates` ohne Override                    | `make gates` (Default-`CRITICAL_COV_TARGETS` um `adapters/driven/protocol_*` erweitert) (Welle 2/3/4) |
| `make fullbuild` gruen ohne Override                  | `make fullbuild` — **M4-Abschluss-Gate** (Welle 6) |
| Alle M4-ADRs `Accepted`                               | Doc-Review: `docs/plan/adr/00NN-*.md` Status `Accepted` (Welle 7) |
| End-to-End-Sweep S-1..S-6                             | Closure-Notiz: `done/M4-results.md §4` mit Per-S-Item-Belegen (Welle 7) |
