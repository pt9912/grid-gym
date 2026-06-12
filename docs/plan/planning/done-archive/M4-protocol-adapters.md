# Slice-Plan — M4 Protokolladapter — Done

**Status:** Done 2026-06-01 mit M4-Welle-7-Closure. Closure-
Belege in
[`../done/M4-results.md`](../done/M4-results.md);
6 M4-ADRs (0030..0035) auf `Accepted` (Welle-7-C1
`d2071f0`); 9 Wellen 0..6b geliefert + Welle 7 Closure.
**Self-Close-Move dieses Slice-Plans nach `done/` folgt
mit Welle-7-C4** (rename-only Commit per
`feedback_git_mv`-Konvention; Bezug-Linkpflege an
ADR 0030..0035 per ADR-0028-Verfahren als Folge-Commit).
Der Datei-Body unterhalb dieser Status-Klausel bleibt
historisches Artefakt der laufenden M4-Phase (Pattern aus
`done/M3-faults-agents-observability.md` und
`done/M2-devices.md`).

**Historischer Eroeffnungs-Header (Welle 0, 2026-05-26):**
In Progress mit M4-Welle-0 (`d0bb16e` Slice-Doc). Fuenf
Sub-Adapter (MQTT, Modbus TCP, OPC-UA, DNP3, IEC 61850)
ueber Welle 0..7 verteilt geliefert.

**Datum:** 2026-05-26 (in `in-progress/` direkt eroeffnet
ohne `next/`-Zwischenschritt; Welle-0-Doc-Hoheit fuer den
Hintergrund liegt in [`M4-welle-0.md`](M4-welle-0.md) §1).

**Bezug:**

- [`roadmap.md`](../in-progress/roadmap.md) §3 M4 (Lieferziel, DoD-
  Checkliste, Architekturartefakte).
- M3-Closure-Notiz
  [`../done/M3-faults-agents-observability.md`](M3-faults-agents-observability.md) +
  [`../done/M3-results.md`](../done/M3-results.md).
- M4-Welle-0-Slice-Begleit-Doc
  [`M4-welle-0.md`](M4-welle-0.md) (Welle-0-Decision-Liste +
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
- [`../done/welle-0.md`](welle-0.md) §3 (M3-Welle-0-
  Pattern fuer reine Doc-Welle).
- Offene Trigger
  [`../open/004`](../open/004-canonical-encoder-alternative-adr.md)
  (canonical encoder — potenziell MQTT-Payload-relevant) und
  [`../open/006`](006-mypy-strict-bytes.md)
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
   ([`../done/009-tests-integration-compose.md`](009-tests-integration-compose.md)),
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
[`../done/M4-welle-0.md`](M4-welle-0.md) (gewandert
nach `done/` mit M4-Welle-1-Pre-C0 `556ae9f`). Reine
Doc-Welle ohne ADR-Lieferung.

- [x] **Slice-Begleit-Doc** —
  [`../done/M4-welle-0.md`](M4-welle-0.md) als
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
  in [`../done/M4-welle-0.md`](M4-welle-0.md) §3
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
    [`006`](006-mypy-strict-bytes.md)
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
    [`008`](008-sbom-activation.md)
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
[`../done/M4-welle-1.md`](M4-welle-1.md) (gewandert
nach `done/` mit M4-Welle-2-Pre-C0 `81b5cba` + Pre-C0-Sync).
ADR 0030 ist `Provisional`.

- [x] **ADR 0030** (erster M4-ADR) fuer
  `DeviceProtocolPort`-Surface mit Entscheidungen aus
  [`M4-welle-0.md`](M4-welle-0.md) §3
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
[`../done/M4-welle-2.md`](M4-welle-2.md) (gewandert
nach `done/` mit M4-Welle-3-Pre-C0 `0d6ad6c` + Pre-C0-Sync).
ADR 0031 ist `Provisional`.

- [x] **ADR 0031** (zweiter M4-ADR) — `Provisional`
  mit C3 (2026-05-30) nach C1 `4e102b8` (Proposed) und
  C2 `f33bb4e` (feat-Merge). Vier Decisions aus
  [`../done/M4-welle-0.md`](M4-welle-0.md) §3
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
[`../done/M4-welle-3.md`](M4-welle-3.md) (nach
`done/` verschoben mit der Doku-Review-Folge 2026-05-31;
Welle-4-Pre-C0-Move entfaellt).
ADR 0032 ist `Provisional`.

- [x] **ADR 0032** (dritter M4-ADR) — `Provisional`
  mit C3 (2026-05-30) nach C1 `a86ac46` (Proposed) und
  C2 `d721982` (feat-Merge). Sechs Decisions aus
  [`../done/M4-welle-0.md`](M4-welle-0.md) §3
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
    [`../done/031-modbus-adapter-review-folge.md`](031-modbus-adapter-review-folge.md)
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
  [`../done/031-modbus-adapter-review-folge.md`](031-modbus-adapter-review-folge.md)
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
  [`031-modbus-adapter-review-folge.md`](031-modbus-adapter-review-folge.md)
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

### Welle 4 — OPC-UA-Adapter (Done 2026-05-31)

**Status:** Done. Slice-Begleit-Doc
[`../done/M4-welle-4.md`](M4-welle-4.md) (gewandert
nach `done/` mit M4-Welle-5-Pre-C0 `3bc015b`; Pattern
analog M4-Welle-1/2/3). ADR 0033 ist `Provisional`. Vierte Code-Welle in M4 und der
**dritte konkrete Adapter** auf der `DeviceProtocolPort`-
Surface (`GG-AR-PORT-DRN-007`): OPC-UA ueber `asyncua 1.2b2`.
Welle 4 traegt erstmals einen **rein-async-Stack** produktiv
vor — ADR 0030 §2.1 hat die Sync-Surface-Brueckenkonstruktion
fuer asyncua vorbelegt; Welle 4 implementiert sie konkret in
`_loop_thread.py` mit eigener `OpcuaLoopThread`-Klasse.

- [x] **ADR 0033** (vierter M4-ADR) — `Provisional` mit
  C3 (2026-05-31) nach C1 `74ed35b` (Proposed) und C2
  `78fdd7a` (feat-Merge). Fuenf Decisions alle **final**:
  - [x] Decision O-a (Node-ID-Schema, **final**): inline
    im `protocol_ports`-Scenario-YAML-Block (Pattern-
    Praezedenz ADR 0031 §2.1 + ADR 0032 §2.1); pro
    `device_id` ein `OpcuaNodeConfig` mit Pflicht-Feldern
    `node_id`/`datatype`/`access`. Numerische
    (`ns=N;i=M`) und String-Identifier (`ns=N;s=Ident`)
    in Welle 4; GUID/ByteString Welle-6-Schaerfung.
  - [x] Decision O-b (Async-Bridge, **final**): dedizierter
    `asyncio.AbstractEventLoop` in
    `threading.Thread(daemon=True)` mit
    `run_coroutine_threadsafe`-Marshal. Eigene Klasse
    `OpcuaLoopThread` als **erstes Repo-Pattern** dieser
    Art (ADR 0030 §2.1-Konsequenz produktiv vorgetragen);
    normativer Teardown-Vertrag (pending-Task-Cancel +
    `asyncio.gather(return_exceptions)` + `loop.stop` +
    `thread.join(timeout=5.0)`). pymodbus-Direct-Sync-
    Decision-M-c ist **nicht** wiederverwendbar.
  - [x] Decision O-c (Datentyp-Set, **final**): Welle-4-
    Minimum `{Boolean, Int16, UInt16, Int32, UInt32,
    Float, Double, String}` (8 Werte). Float/Double ->
    `Decimal(repr(float_value))` (Praezisions-Konsistenz
    mit ADR 0032 §2.2). `Byte`/`SByte`/`Int64`/`UInt64`/
    `DateTime`/`Guid`/`ByteString`/`ExtensionObject`
    Welle-6-Schaerfung offen.
  - [x] Decision O-d (Read/Write-Pfad, **final**):
    Polling-Read via `client.get_node(node_id).read_value()`
    + Direct-Write via `node.write_value(variant)`, beide
    gemarshalt durch `OpcuaLoopThread.run_coroutine`.
    Subscription-Pfad mit Monitored Items als Welle-6-
    Forward-Pointer.
  - [x] Decision O-e (Test-Sibling, **final**): in-process
    `asyncua.Server` (LGPL-3.0; Pattern-Praezedenz
    Welle-3-Decision-M-f). Verworfene Alternativen:
    `open62541/open62541` MPL-2.0 mit nicht-trivialer
    Container-Config; `OPCFoundation/UA-CPPServer` RCL mit
    Kommerz-Pfad; `prosysopc` proprietaer.
- [x] **NEU** `src/grid_gym/adapters/driven/protocol_opcua/`-
  Modul (6 Dateien): `__init__.py` (Public-Reexports +
  Lastenheft-Z.-1161–1163-Pflichtnotiz) + `_config.py`
  (Decision O-a/O-c mit Node-ID-Format-Validation) +
  `_codec.py` (Decision O-c `encode_value_to_variant` /
  `decode_variant_to_value`; `OpcuaCodecError`-Familie) +
  `_loop_thread.py` (Decision O-b `OpcuaLoopThread`-Klasse;
  geordneter Teardown-Vertrag) + `_port.py` (Decision O-b/
  O-d Lifecycle + Polling-Read + Direct-Write) +
  `_errors.py` (typed `DeviceProtocolPort*Error`-Subclasses
  inkl. Read/Write-Operation-Tax analog Slice-031-Pattern).
- [x] **Async-Loop-Thread produktiv** — `OpcuaLoopThread`-
  Klasse in `_loop_thread.py` mit geordnetem
  `start()`/`stop()`-Lifecycle und
  `run_coroutine_threadsafe`-Marshal-Helper. **Erstes
  produktives Thread+Loop-Konstruktions-Pattern im Repo.**
- [x] **NEU 81 Unit-Tests** unter
  `tests/unit/adapters/driven/protocol_opcua/`:
  10 Config-Validation + 34 Codec-Roundtrip (inkl.
  hypothesis-Property-Tests pro Datatype) + 9 Loop-Thread-
  Lifecycle/Cancellation/Timeout + 16 Protocol-Port-
  Lifecycle/Read+Write mit AsyncMock-`asyncua.Client` +
  8 Smoke-parametrisiert ueber alle 8 Datatypes.
- [x] **NEU Integration-Smoke** —
  `tests/integration/test_opcua_in_process_smoke.py` mit
  in-process `asyncua.Server` in eigenem asyncio-Loop-
  Thread (Decision O-e); Anonymous-Endpoint; End-to-End-
  Read/Write-Roundtrip durch alle 8 Datatypes
  (Decision O-c); expliziter `server.stop()` +
  `thread.join(timeout=5.0)`-Teardown.
- [x] **EDIT `tests/integration/compose.yml`** — Header-
  Kommentar-Sync ergaenzt um Decision-O-e-Notiz
  (in-process `asyncua.Server`, Pattern-Fortfuehrung aus
  Welle 3; Lizenz-Pragmatik LGPL-3.0 vs. MPL-2.0-
  Container-Alternativen).
- [x] **EDIT `pyproject.toml`** — `asyncua==1.2b2` in
  `[project] dependencies` (Beta-Pin wegen Python-3.14-
  Forward-Reference-Inkompat in 1.1.8; asyncua 1.2b2
  traegt den Python-3.14-Fix vor 1.2-final). mypy-Override
  `module = "asyncua.*"` mit `implicit_reexport=true`
  (1.2b2 hat py.typed aber kein `__all__`). `asyncua`-
  Eintrag in den AC-PORTS-NO-FW/AC-NO-FW-Forbidden-Listen
  unveraendert (Welle-0-Vorbelegung).
- [x] **EDIT `uv.lock`** — via `make lock-refresh`
  aktualisiert: 108 packages, asyncua 1.1.8 -> 1.2b2 +
  8 transitive Deps (aiosqlite, cffi, cryptography,
  pycparser, pyopenssl, python-dateutil, pytz).
- [x] **EDIT `Dockerfile`** — `CRITICAL_COV_TARGETS`-
  Default um `adapters/driven/protocol_opcua` erweitert
  (Pattern analog Welle 2/3).
- [x] **`AC-ADAPTER-LIGHTWEIGHT` greift fuer
  `protocol_opcua`** — `tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`-Filter erfasst den
  neuen Pfad **ohne Code-Aenderung**; `make arch-check`
  weiter `19/19 Contracts KEPT`.

**Welle-4-Gate (Done 2026-05-31):** `make test-integration`
gruen mit OPC-UA-In-Process-Smoke (23 → 31 Integration-
Tests, +8 Roundtrips). `make test-unit` gruen (1314 → 1395
= +81 Unit-Tests). `make arch-check` gruen (19/19 = 7
lint-imports + 12 `tools/arch_check.py`). `make gates`
cache-frei gruen ohne `CRITICAL_COV_TARGETS`-Override
(Default-Liste um `adapters/driven/protocol_opcua`
erweitert; Total-Coverage 95.16%, Critical-Coverage
90.95% Branch). `mypy --strict-bytes` cache-frei gruen
(OPC-UA-Adapter ist `--strict-bytes`-clean). **Commit-
Belege:** C0 `7937e70` (Slice-Doc) + C1 `74ed35b` (ADR
0033 Proposed) + C2 `78fdd7a` (feat: protocol_opcua + 81
Unit-Tests + In-Process-Integration-Smoke + pyproject/
uv.lock/Dockerfile/compose.yml-Edits) + C3 `7ad5baf`
(ADR 0033 → `Provisional`, `M4-welle-4.md` → `Done`,
diese §3-Welle-4-Section auf Done, Top-Level-Doku-Sync
in 5 Docs).

**Slice-032-Review-Folge (2026-05-31):** Code-Review der
Welle-4-Commits hat 6 HIGH + 11 MEDIUM Findings ergeben;
[`../done/032-opcua-adapter-review-folge.md`](032-opcua-adapter-review-folge.md)
hat alle 17 umgesetzt — Lifecycle-Lock + Start-Timeout in
`OpcuaLoopThread`, Exception-Filter-Erweiterung um
`RuntimeError`/`CancelledError` im Port,
`Quality.INVALID`-Markierung fuer String-Reads,
`Float`-32bit-Quantisierung im Codec, ADR-Body-
Schaerfungen an §2.1/§2.5. ADR 0033 bleibt `Provisional`.
Tests: 1395 → 1401 Unit-Tests, 31 Integration-Tests gruen.

### Welle 5 — DNP3 + IEC-61850 (Sub-Slicing in 5a + 5b)

**Status:** Pending. Disposition-Welle nach Welle-4-
Library-Recherche (2026-05-31): Python-Library-Lage fuer
DNP3 und IEC-61850 ist **besser als beim Welle-1-Provisional-
Verzicht angenommen**:

- **DNP3:** `dnp3-outstation` 0.2.0 (PyPI, MIT, Pure-Python,
  asyncio-native, IEEE-1815-2012-Level-1-Subset, aarch64-
  compatible) bietet eine produktiv-stabile Outstation-
  Implementierung ohne C-Backend-Lock-in. Strukturell
  sauberer als `asyncua` (LGPL + komplexe Wire-Pipeline).
- **IEC-61850:** `iec61850` 0.12.1 (PyPI, Apache-2.0,
  async-first, Rust-Backend via `iec61850-rust`, Py≥3.11)
  ist „Pre-Alpha" markiert, aber API-stabil genug fuer
  einen Spike.

**Sub-Slicing-Entscheidung** (per §3-Praeambel: > 1 Adapter
+ > 1 ADR + > 1 Smoke wuerde Schwelle reissen): Welle 5
wird in **Welle 5a** (DNP3) und **Welle 5b** (IEC-61850)
geteilt. Beide Sub-Wellen sind eigenstaendige Code-Wellen
mit eigenem Slice-Doc + ADR + protocol_*-Modul +
Integration-Smoke + DoD-Checkliste.

ADR 0030 §2.4 (Welle-1-provisorisches Verzicht-Default)
wird mit M4-Welle-7-Closure auf „aufgeloest durch Welle 5a/5b
Spike-Lieferung" geschaerft (ADR-0011-Pattern; kein
Supersedes). `roadmap.md §3 M4 DoD`-Checkboxen `DNP3-Adapter`
und `IEC-61850-Adapter` werden durch die Welle-5a/5b-
Lieferung produktiv abgehakt (statt „dokumentierter
Verzicht").

#### Welle 5a — DNP3-Adapter (Spike, Done 2026-05-31)

**Status:** Done. Slice-Begleit-Doc
[`../done/M4-welle-5a.md`](M4-welle-5a.md) (gewandert
nach `done/` mit M4-Welle-5b-Pre-C0 `9fea2be`; Pattern analog
M4-Welle-1..4 mit `556ae9f` / `81b5cba` / `0d6ad6c` /
`506c8ca` / `3bc015b`).
ADR 0034 ist `Provisional`. Fuenfte Code-Welle in M4 und
der **vierte konkrete Adapter** auf der
`DeviceProtocolPort`-Surface (`GG-AR-PORT-DRN-007`): DNP3
ueber das **Zwei-Library-Setup** `nfm-dnp3` (Master,
Produktiv-Dependency) + `dnp3-outstation` (Outstation, nur
Test-Sibling). Beide Libraries sind MIT, Pure-Python — keine
C-Backend-Lock-ins, kein LGPL.

- [x] **ADR 0034** (fuenfter M4-ADR) — `Provisional` mit
  C3 (2026-05-31) nach C1 `b0fea7e` (Proposed) und C2
  `224b370` (feat-Merge). Fuenf Decisions alle **final**
  (per C1-Probe-Run + C2-Smoke-Beleg):
  - [x] Decision D-a (Point-Schema, **final**): inline
    im `protocol_ports`-Block (Pattern-Praezedenz
    ADR 0031/0032/0033); `Dnp3PointConfig` mit
    Pflicht-Feldern `group`/`variation`/`index`/`access`.
  - [x] Decision D-b (Async-Bridge, **final**):
    **direkt-sync ohne Loop-Thread** (Pattern-Praezedenz
    Welle-3-Decision-M-c). C1-Probe-Run verifiziert:
    `nfm-dnp3.DNP3Master` ist 100% sync (alle public
    Methoden ohne async-Marker); kein
    `OpcuaLoopThread`-Reuse noetig. Welle-6-Forward-
    Pointer: falls `nfm-dnp3` in 2.x async wird, Folge-
    ADR via ADR-0011-Pattern.
  - [x] Decision D-c (Group/Variation-Set, **final**):
    Welle-5a-Minimum `{(1, 1), (1, 2), (30, 1), (30, 5)}`
    — Binary-Inputs single-bit + with-flags, plus
    32-bit Integer-Analog + 32-bit Float-Analog.
    Counter/Output/Event-Class-Groups bleiben Welle-6-
    Schaerfung. Float → `Decimal(repr(value))`
    (Praezisions-Konvention analog ADR 0032 §2.2).
  - [x] Decision D-d (Read-Pfad, **final**): **Class-0-
    Polling-Read mit Resultat-Filter-by-Index**
    (DNP3-spec-konformes Idiom). `master.read_class(0)`
    einmal pro `read(target)`, dann
    `_find_point(poll, point_cfg)` filtert
    `analog_inputs`/`binary_inputs` nach `index`.
    `read_analog_inputs(start, stop)`-Pfad verworfen
    wegen Wire-Compat-Limit (`dnp3-outstation` v0.2.0
    supportet nur qualifier 0x00/0x06; nfm-dnp3 schickt
    fuer Range-Reads qualifier 0x01).
  - [x] Decision D-e (Test-Sibling, **final**):
    in-process `dnp3_outstation.AsyncOutstation` in
    eigenem Daemon-Thread + `asyncio.Event`-Stop-Signal
    (Pattern aus Welle-4-Slice-032-Schaerfung).
- [x] **NEU**
  `src/grid_gym/adapters/driven/protocol_dnp3/`-Modul
  (5 Dateien): `__init__.py` (Public-Reexports +
  Lastenheft-Z.-1161–1163-Pflichtnotiz) + `_config.py`
  (Decision D-a mit Group/Variation-Allow-List) +
  `_codec.py` (Decision D-c; `decode_point_value(point,
  group, variation)` mit Helper `_decode_binary`/
  `_decode_analog` haelt McCabe-Komplexitaet unter
  AC-ADAPTER-LIGHTWEIGHT-Schwelle) + `_port.py`
  (Decision D-b direkt-sync + Decision D-d Class-0-Read
  mit Filter; `_find_point` matcht auf `index` —
  C2-Library-Bug-Find: `AnalogInput.__repr__` zeigt
  `idx=`, aber Feld heisst `index`) + `_errors.py`
  (typed `DeviceProtocolPort*Error`-Subclasses inkl.
  Read/Write-Operation-Tax analog Slice-031/032-Pattern
  + `Dnp3PortWriteNotImplementedError` fuer Welle-5a-
  Anti-Scope).
- [x] **Direkt-sync ohne Loop-Thread** — Pattern-
  Praezedenz Welle-3-Modbus-Decision-M-c produktiv
  vorgetragen (anders als Welle 4 OPC-UA mit
  `OpcuaLoopThread`). Adapter ist signifikant einfacher
  als `protocol_opcua/_port.py`.
- [x] **NEU 56 Unit-Tests** unter
  `tests/unit/adapters/driven/protocol_dnp3/`:
  17 Config-Validation + 16 Codec-Roundtrip (inkl.
  hypothesis-Property-Tests pro Group/Variation) +
  17 Protocol-Port-Lifecycle/Read-Pfad-gegen-mocked-
  Master + 6 Read-Pfad-Edge-Cases (alle Error-Pfade).
- [x] **NEU Integration-Smoke** —
  `tests/integration/test_dnp3_in_process_smoke.py`
  mit in-process `AsyncOutstation` in eigenem asyncio-
  Loop-Thread + `asyncio.Event`-Stop-Signal (Pattern
  aus Welle-4-Slice-032-Schaerfung); 3 Class-0-Read-
  Roundtrips parametriert pro Initial-Wert + 1
  Update-then-Read-Test.
- [x] **EDIT `tests/integration/compose.yml`** — Header-
  Kommentar-Sync ergaenzt um Decision-D-e-Notiz
  (Zwei-Library-Setup-Klarstellung; Wire-Compat-Beleg
  aus ADR 0034 §1; Pattern-Fortfuehrung aus Welle 3/4).
- [x] **EDIT `pyproject.toml`** — `nfm-dnp3>=1.0,<2.0`
  in `[project] dependencies` (Master); `dnp3-outstation>=0.2,<1.0`
  in `[dependency-groups.dev]` (Outstation, **nur** Test-
  Sibling). mypy-Overrides `module="dnp3py.*"` und
  `module="dnp3_outstation.*"` mit
  `ignore_missing_imports = true`.
- [x] **EDIT `uv.lock`** — via `make lock-refresh`
  aktualisiert: 110 packages, +nfm-dnp3 v1.0.1 +
  dnp3-outstation v0.2.0; keine transitiven Deps.
- [x] **EDIT `Dockerfile`** — `CRITICAL_COV_TARGETS`-
  Default um `adapters/driven/protocol_dnp3` erweitert.
- [x] **`AC-ADAPTER-LIGHTWEIGHT` greift fuer
  `protocol_dnp3`** — `tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`-Filter erfasst den
  neuen Pfad **ohne Code-Aenderung**; `make arch-check`
  weiter `19/19 Contracts KEPT`.

**Welle-5a-Gate (Done 2026-05-31):** `make test-integration`
gruen mit DNP3-In-Process-Smoke (31 → 35 Integration-Tests,
+4 Roundtrips). `make test-unit` gruen (1406 → 1462 = +56
Unit-Tests). `make arch-check` gruen (19/19 = 7
lint-imports + 12 `tools/arch_check.py`). `make gates`
cache-frei gruen ohne `CRITICAL_COV_TARGETS`-Override
(Default-Liste um `adapters/driven/protocol_dnp3`
erweitert). `mypy --strict-bytes` cache-frei gruen
(DNP3-Adapter ist `--strict-bytes`-clean). **Commit-Belege:**
C0 `43d0b07` (Slice-Doc) + C1 `b0fea7e` (ADR 0034
Proposed) + C2 `224b370` (feat: protocol_dnp3 + 56 Unit-
Tests + In-Process-Integration-Smoke + pyproject/uv.lock/
Dockerfile/compose.yml-Edits + Library-Bug-Find `idx` →
`index`) + C3 (dieser Commit; ADR 0034 → `Provisional`,
`M4-welle-5a.md` → `Done`, diese §3-Welle-5a-Section auf
Done, Top-Level-Doku-Sync in 5 Docs).

#### Welle 5b — IEC-61850-Adapter (Spike, Done 2026-06-01)

**Status:** Done. Slice-Begleit-Doc
[`../done/M4-welle-5b.md`](M4-welle-5b.md) (gewandert
nach `done/` mit M4-Welle-6-Pre-C0 `30860ed`; Pattern analog
M4-Welle-1..5a mit `556ae9f` / `81b5cba` / `0d6ad6c` /
`506c8ca` / `3bc015b` / `9fea2be`).
ADR 0035 ist `Provisional`. Per-Commit-Liefer-Hashes:
C0 `19f820a` (Slice-Doc), C1 `88c1a33` (ADR 0035 `Proposed`),
C1-Review-Folge `da8aed9` (API-Korrektur + Lizenz-Refit +
M4-protocol-adapters.md-Sync nach 4 Findings), C2 `944bca5`
(feat: `protocol_iec61850/`-5-Modul-Paket + 75 Unit-Tests +
Integration-Smoke unter 2c-Mock-only-Fallback + GPL-Lizenz-
Boundary-Files; 1537 Unit + 35 passed + 4 skipped
Integration; 19/19 Contracts KEPT; 9/9 Gates gruen ohne
Override), C3 `ca96bca` (ADR 0035 → `Provisional`,
M4-welle-5b.md → `Done`, diese §3-Section auf Done,
Top-Level-Doku-Sync), Slice 033 `7e0c91b` (C2-Review-Folge:
15 Findings 10 HIGH + 5 MEDIUM adressiert ohne ADR-Status-
Aenderung; siehe
[`../done/033-iec61850-adapter-review-folge.md`](033-iec61850-adapter-review-folge.md)).

**Library-Lage (verifiziert 2026-06-01):** produktive
Library ist `pyiec61850-ng>=1.6,<2.0` (PyPI, manylinux1_x86_64
+ Windows-Wheels fuer CPython 3.9..3.14, **GPLv3**, Beta,
SWIG-Bindings zu libiec61850 1.6 + Mbed TLS Apache 2.0).
**Eine** Library liefert sowohl `pyiec61850.mms.MMSClient`
(Client, top-level `__version__ = "1.6.1.2"`-stabil)
**als auch** `pyiec61850.server.IedServer` (in-process
Server, `__version__ = "0.1.0"`-Pre-Alpha im Submodul) —
Pattern analog Welle-3-Modbus mit pymodbus, **nicht**
Welle-5a-zwei-Library-Setup. Recherche-Vergleichs-Quellen:
PyPI + GitHub `f0rw4rd/pyiec61850-ng`, `mz-automation/libiec61850`,
`arthurazs/py61850` (MIT aber Pre-Alpha + nur GOOSE),
`keyvdir/pyiec61850` (Fork, fragiler Source-Build),
`stevenblair/rapid61850` (GPLv2 C-Code-Gen),
`khawkings/py_iec61850_cdc` (nur Data-Classes),
`robidev/iec61850_open_server` (libiec61850-derived).

- [x] **ADR 0035** (sechster M4-ADR) — `Proposed` (C1
  `88c1a33`) → `Provisional` (C3), mit sechs IEC-61850-
  spezifischen Profil-Entscheidungen (Pattern analog
  ADR 0031..0034 + NEU Decision I-f):
  - [x] Decision I-a (LN/CDC-Schema, **final** mit C1-
    Review-Folge): inline im `protocol_ports`-Block;
    pro `device_id` ein `Iec61850LnConfig` mit
    Pflicht-Feldern `object_reference` (LD/LN.DO.DA-
    Pfad), `functional_constraint` (`MX`/`ST`/`SP`/`CF`),
    `datatype` (`bool`/`int32`/`float`/`string`),
    `access` (`read`). Welle-5b-Minimum: MMS-Read.
  - [x] Decision I-b (Async-Bridge, **final**):
    **direkt-sync** wie Welle-3-Modbus-Decision-M-c und
    Welle-5a-DNP3-Decision-D-b. Kein OpcuaLoopThread-
    Reuse — `pyiec61850.mms.MMSClient` ist sync-Context-
    Manager (`__enter__`/`__exit__`/`connect`/`disconnect`/
    `read_value`/`write_value` alle sync).
  - [x] Decision I-c (Datatype-Set + FC-Mapping,
    **final**): `{bool, int32, float, string}` ×
    FC `{MX, ST, SP, CF}` mit Adapter-Default `MX`
    (Library-Default ist `ST`; Adapter setzt explizit).
    UINT/OCTET_STRING/UTC_TIME/Arrays/Structs Welle-6+-
    Schaerfung.
  - [x] Decision I-d (Read-Pfad, **final**): Per-Target
    MMS-Read via
    `MMSClient.read_value(object_reference, fc)`. RCB-
    Subscription + GOOSE Welle-6+. Write-Pfad Welle-5b-
    Anti-Scope (`Iec61850PortWriteNotImplementedError`
    **vor** Library-Call).
  - [x] Decision I-e (Test-Sibling, **final mit 2c-Mock-
    only-Fallback**): in-process
    `pyiec61850.server.IedServer(model_path=fixture)`
    mit minimalem CFG-Fixture unter
    `tests/integration/fixtures/iec61850/simpleIO.cfg`
    (libiec61850-natives Modell-Konfig-Format, kein
    SCL-XML; 4 Datatypes). Wire-Compat-Risiko zwischen
    MMSClient-1.6.1.2 ↔ IedServer-0.1.0 ist C2-Smoke-
    Pflicht; Mock-only-Fallback (Decision I-e wird zu
    „Mock-only" geschoben) falls CFG-Format oder Wire-
    Compat in C2 nicht stabil. **Wichtig:**
    argumentloser `IedServer()`-Konstruktor wirft
    `ModelError("No data model loaded")` bei `start()`
    — Modell-Pflicht ist hart.
  - [x] **NEU Decision I-f** (Lizenz-Boundary,
    **final**): GPLv3-Isolation auf
    `protocol_iec61850/*` + zugehoerige Tests via
    SPDX-Header pro Datei
    (`# SPDX-License-Identifier: GPL-3.0-only`);
    `pyiec61850-ng>=1.6,<2.0` als
    **`[project.optional-dependencies.iec61850]`**
    opt-in (nicht `[project] dependencies`, nicht
    `[dependency-groups.dev]`); NEU `LICENSES/GPL-3.0.txt`;
    EDIT Top-Level-`LICENSE` mit Hinweis-Block; EDIT
    `README.md` + `README.de.md` mit Lizenz-Sektion +
    Optional-Extra-Install-Hinweis. Rest grid-gym
    bleibt MIT. Erstmaliger Repo-Praezedenzfall fuer
    GPL-isolierte Sub-Module.
- [x] **NEU**
  `src/grid_gym/adapters/driven/protocol_iec61850/`-Modul
  (5 Dateien mit SPDX-Header: `__init__.py` mit
  ImportError-Guard fuer Decision I-f, `_config.py`,
  `_codec.py`, `_port.py`, `_errors.py` inkl.
  `Iec61850PortLibraryNotInstalledError`).
- [x] **Unit-Tests** unter
  `tests/unit/adapters/driven/protocol_iec61850/`
  (SPDX-Header).
- [x] **Integration-Smoke** unter
  `tests/integration/test_iec61850_in_process_smoke.py`
  mit `IedServer(model_path=fixture)` (SPDX-Header).
  ALTERNATIV (2c-Fallback): Mock-only-Smoke in
  `tests/unit/`.
- [x] **NEU `tests/integration/fixtures/iec61850/simpleIO.cfg`**
  minimales Welle-5b-Test-Modell (libiec61850-natives
  CFG-Format; 4 Datatypes; falls 2c-Fallback aktiv:
  Fixture entfaellt).
- [x] **NEU `LICENSES/GPL-3.0.txt`** Standard-GPL-3.0-
  Volltext.
- [x] **EDIT Top-Level-`LICENSE`** Hinweis-Block fuer
  GPL-Boundary + Optional-Extra-Hinweis.
- [x] **EDIT `README.md` + `README.de.md`** Lizenz-
  Hinweis-Sektion + Optional-Extra-Install-Hinweis.
- [x] **EDIT `tests/integration/compose.yml`** — Header-
  Kommentar-Sync (Decision-I-e in-process IedServer +
  Decision-I-f GPL-Boundary).
- [x] **EDIT `pyproject.toml`** —
  `[project.optional-dependencies] iec61850 = ["pyiec61850-ng>=1.6,<2.0"]`
  (Decision I-f opt-in; **nicht** in
  `[project] dependencies`, **nicht** in
  `[dependency-groups.dev]`); mypy-Override
  `module="pyiec61850.*"` mit
  `ignore_missing_imports = true`. Top-Level-MIT-
  Classifier bleibt.
- [x] **EDIT `Dockerfile`** — `CRITICAL_COV_TARGETS`-
  Default um `adapters/driven/protocol_iec61850`
  erweitert; Test-Stage installiert das Extra via
  `uv sync --extra iec61850` (oder aequivalent).
- [x] **`AC-ADAPTER-LIGHTWEIGHT` greift** ohne Filter-
  Edit (`bucket.startswith("protocol_")`).
- [x] **C3-Doc-Sync** — `M4-welle-5b.md` Status, ADR
  0035 `Proposed → Provisional`, diese §3-Welle-5b-
  Section auf Done, Top-Level-Doku-Sync.

**Welle-5b-Gate:** `make test-integration` gruen mit
IEC-61850-Smoke gegen CFG-Fixture (oder Mock-only-Unit-
Test im 2c-Fallback). `make gates` cache-frei gruen ohne
Override; mit `uv sync --extra iec61850` in der Test-
Stage.

**Welle-5b-Hauptrisiken** (HOCH→LOW):

- **CFG-Format-Validierung in C2** (HOCH): libiec61850-
  natives CFG-Format-Detail ist nur exemplarisch
  dokumentiert; 2c-Mock-only-Fallback explizit
  vorbelegt.
- **Wire-Compat MMSClient-1.6.1.2 ↔ IedServer-0.1.0**
  (HOCH): Server-Submodul ist Pre-Alpha;
  C2-Smoke-Pflicht.
- **GPL-Boundary-Policy Repo-Novum** (HOCH):
  Praezedenzfall fuer GPL-isolierte Sub-Module;
  Welle-6-Schaerfungs-Pfade (CONTRIBUTING.md-Sync,
  SPDX-Header-Konsistenz-Check, GPL-Boundary-Crossing-
  Contract).
- **`pyiec61850-ng` Beta** (MEDIUM): Pin
  `>=1.6,<2.0` + `uv.lock`-Pin.
- **SWIG-/C-native Library erstmalig im Repo** (MEDIUM):
  Context-Manager-Pattern kapselt Memory-Risiken.
- **Kein aarch64-Wheel** (LOW): grid-gym laeuft primaer
  x86_64; Welle-6-Material falls Bedarf.

### Welle 6 — Sub-Slicing in 6a + 6b nach Welle-5b-Erbschaft

**Sub-Slicing-Begruendung** (2026-06-01, M4-Welle-6-Sub-
Slicing-Refactor, dieser Commit-Anker): die in Welle 0
vorgesehene Welle 6 deckt **zwei strukturell verschiedene
Arten Arbeit** ab, die nach Welle-5b-Closure (insbesondere
nach Slice 033 Review-Folge) klar trennbar sind:

1. **Cross-Adapter-Mainstream-Hardening** — Items, die ueber
   alle 5 `protocol_*`-Adapter (Welle 2/3/4/5a/5b) hinweg
   wirken: Profil-Index, Lastenheft-/Architektur-Sync, OTel-
   Span-Wrap, AC-ADAPTER-LIGHTWEIGHT-Planted-Violator-
   Property-Test, Trigger-004/006-Re-Eval, compose.yml-
   Aufraeumung. **Welle 6a**.
2. **Welle-5b-Erbschaft** — Items, die spezifisch aus der
   Welle-5b-IEC-61850-Lieferung haengenbleiben: GPL-Boundary-
   Hardening (SPDX-Header-Konsistenz-Check in
   `tools/check_refs.py`, neuer arch_check-Contract gegen
   GPL-Boundary-Crossing aus MIT-Code), CONTRIBUTING.md-Sync
   mit GPL-Boundary-Policy, IedServer-Smoke-Reaktivierungs-
   Versuch (Python-3.12-Runtime / Library-Upgrade / Wheel-
   Rebuild). **Welle 6b**.

Pattern-Praezedenz: Welle-5-Sub-Slicing-Refactor
(`8f022a3`) trennte 5a (DNP3) und 5b (IEC-61850) wegen
unterschiedlicher Library-Pfade. Welle-6-Sub-Slicing trennt
6a (cross-adapter) und 6b (welle-5b-spezifisch) wegen
verschiedener Domain-Schwerpunkte (Mainstream-Pattern vs
Lizenz-/Distribution-Policy).

#### Welle 6a — Cross-Adapter-Hardening (Done 2026-06-01)

**Status:** Done — geschlossen 2026-06-01 mit
M4-Welle-6a-C4 (dieser Commit). Per-Commit-Liefer-Hashes:
C0 `9776dd9` (Slice-Doc), C1 `9312239` (Profil-Index +
Architektur/Lastenheft-Sync), C2 `9d3912f` (OTel-Span-
Wrap via Composition-Wrapper), Pre-C3 `81140e2` (git mv
trigger-006 → done/, rename-only), C3 `0a5e895` (Planted-
Violator-Test + `strict_bytes = true` + compose-
Aufraeumung + Trigger-004-Re-Eval-Defer), C4 (dieser
Commit; Status/DoD-Sync + Top-Level-Doku-Sync). Slice-
Begleit-Doc
[`../done/M4-welle-6a.md`](M4-welle-6a.md)
(Self-Close-Move `d1cb65d` als M4-Welle-6b-Pre-C0;
Pattern analog Welle 1..5b).

- [x] **Adapter-Profil-Index** unter
  `spec/protocol_profiles/` als kanonischem Spec-Pfad
  (oder begruendete andere Lokation): Profil-Index mit
  Verweisen auf die Pro-Adapter-ADRs 0031/0032/0033/0034/0035
  (alle 5 Welle-2..5b-Adapter-Profile).
- [x] **`tests/integration/compose.yml`-Aufraeumung** —
  Konsolidierung der Sibling-Services, Healthcheck-Sync,
  Volume-Hygiene; Header-Kommentar fuehrt jeden Sibling
  mit Lizenz + Test-Pfad-Referenz.
- [x] **Lastenheft §16-Implementierungs-Matrix-Sync** —
  `🔲 M4` → `✅ M4` fuer alle 5 umgesetzten Adapter
  (MQTT/Modbus/OPC-UA/DNP3/IEC-61850).
- [x] **Architektur §8.2 + §16-Sync** — Adapter-Verortung
  scharf setzen mit Welle-1-ADR-Pfad; OTel-Span-Wrap-
  Pattern dokumentiert.
- [x] **OTel-Span-Wrap fuer `protocol_*`-Adapter** —
  TracePort-Wrap der Read/Write-Calls fuer alle 5 Adapter
  (in Welle 2/3/4/5a/5b bewusst verschoben; ADR 0024 §4.5
  als Bezug).
- [x] **`AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-Property-
  Test** — die in
  [`../done/M4-welle-1.md`](M4-welle-1.md) §7
  als Folge-Pflicht markierte Welle-2-Mitigation
  (in Welle 2/3/4/5a/5b bewusst auf Welle 6 verschoben)
  wird jetzt eingezogen.
- [x] **Trigger-004-Re-Eval** — `canonical encoder`-
  Alternative (`orjson`/`msgspec`) gegen MQTT-Publish-
  Throughput-Druck pruefen; Entscheidung im Trigger-Body.
- [x] **Trigger-006-Folge-Slice eingezogen** —
  `--strict-bytes`-Aktivierung in `[tool.mypy]` plus
  Repo-Sweep (Slice 031-Folge; Re-Eval ist in M4-Welle-3
  positiv gelaufen, M4-Welle-6a zieht die Aktivierung
  produktiv).
- [x] **C4-Doc-Sync** — `M4-welle-6a.md` Status, diese
  §3-Welle-6a-Section auf Done, Top-Level-Doku-Sync.

**Welle-6a-Gate:** `make fullbuild` cache-frei gruen ohne
`CRITICAL_COV_TARGETS`-Override. Default-
`CRITICAL_COV_TARGETS` final fuer alle 5 Adapter.
`make arch-check` 19/19 (oder +1 falls ein neuer Contract
aus Welle 6a entsteht, z. B. `AC-ADAPTER-NO-TIME`).

#### Welle 6b — IEC-61850-Lizenz-und-Smoke-Hardening (Welle-5b-Erbschaft)

**Status:** Done — geschlossen 2026-06-01 mit M4-Welle-6b-
C4 (`docs(plan|adr)` Doc-Sync + NEU `CONTRIBUTING.md`,
dieser Commit). Liefer-Hashes: C0 `14d1bcb` (Slice-Doc) +
C1 `8947c62` (SPDX-Lint) + C2 `9e2bf39` (AC-IEC61850-GPL-
BOUNDARY-Contract 19 → 20) + C3 `2539574` (IedServer-
Smoke-Probe Pfad C + Slice-034-F13-Coverage-Schaerfung).

- [x] **SPDX-Header-Konsistenz-Check** — NEU
  `tools/check_spdx.py` + Dockerfile-Stage `spdx-check` +
  Makefile-Target + `make gates`-Integration (10. A-1-
  Gate). 11 GPL-Boundary-Files (5 src + 4 unit-tests +
  1 fixture + 1 integration-test) Lint-clean — C1
  `8947c62`.
- [x] **`arch_check.py`-Contract gegen GPL-Boundary-
  Crossing** — NEU `AC-IEC61850-GPL-BOUNDARY` in
  `tools/arch_check.py` (14. arch_check-Contract; 19 →
  20 KEPT). AST-Import-Scan ueber `src/grid_gym/**/*.py`
  ausser `protocol_iec61850/*`; faengt `ast.Import` +
  `ast.ImportFrom` (inkl. Sub-Modul-Pfade). Welle-1-
  Factory-Bruecken-Pfad ueber dynamischen `importlib.
  import_module(str)` bleibt contract-konform (kein
  statischer AST-Import-Knoten in MIT-Code) — C2
  `9e2bf39`.
- [x] **CONTRIBUTING.md-Sync mit GPL-Boundary-Policy** —
  NEU [`../../../../CONTRIBUTING.md`](../../../../CONTRIBUTING.md)
  mit Dual-License-Section: Default-Contribs MIT;
  `protocol_iec61850/*`-Aenderungen GPL-3.0-only mit
  SPDX-Header-Pflicht; Anleitung "Add a new GPL-isolated
  path" mit Verweis auf C1/C2-Tooling — C4 (dieser
  Commit).
- [x] **IedServer-Smoke-Reaktivierungs-Probe** — Drei-
  Pfad-Vorgehen mit Resultat **Pfad C aktiv**:
  - **Pfad A (passiv, tot):** `pyiec61850-ng`-PyPI-Stand
    2026-06-01 identisch zu Welle 5b (`1.6.1.2`); kein
    cp314-Manylinux-Wheel. Linux-Wheel ist ausschliesslich
    `py3-none-manylinux1_x86_64.whl` ohne cp-Tag → Python-
    3.14-Segfault bleibt.
  - **Pfad B (aktiv, ausgegliedert):** Dockerfile-Multi-
    Python-Setup ist Repo-Novum; eigener Slice-Trigger
    `036-iec61850-multi-python-test-stage.md` (ggf. ADR
    0036). Nicht in Welle-6b-Scope.
  - **Pfad C (aktiv):** Mock-only-Fallback bleibt mit
    konkretem Defer-Trigger
    [`../done/009-iec61850-smoke-reactivation.md`](009-iec61850-smoke-reactivation.md);
    `pytest.mark.skip`-Reason in `test_iec61850_in_
    process_smoke.py` mit Welle-6b-C3-Befund + Trigger-
    009-Verweis aktualisiert.
  — C3 `2539574`.
- [x] **Welle-6b-Smoke-Reaktivierung dokumentiert** —
  Pfad-C-Defer in
  [`../done/009-iec61850-smoke-reactivation.md`](009-iec61850-smoke-reactivation.md)
  mit konkreten Reaktivierungs-Pfaden A (passive Library-
  Watch) und B (eigener Slice-Trigger) plus "Erwartete
  Lieferung bei Trigger"-Section pro Pfad — C3 `2539574`.
- [x] **AC-ADAPTER-LIGHTWEIGHT-Coverage-Schaerfung**
  (Slice 034 F13 Vorlauf-Item) — `_is_adapter_
  lightweight_path` erweitert um flat-file
  `_protocol_*.py`-Cross-Adapter-Helper direkt unter
  `adapters/driven/` (3-Konditions-Filter: flat-file +
  `_protocol_`-Prefix + `.py`-Suffix); Property-Test
  mit 1 neuen Positiv-Pfad + 4 Praezisions-Assertions
  (Subdir-Negativ, `.pyi`-Negativ, Prefix-Praezision,
  Whitelist-Stabilitaet). Welle-6a-Cross-Adapter-
  Helper `_protocol_otel_wrap.py` haelt unter dem
  erweiterten Filter complexity <= 8 — C3 `2539574`.
- [x] **C4-Doc-Sync** — `M4-welle-6b.md` Status `Done`,
  diese §3-Welle-6b-Section auf Done (dieser Commit),
  Top-Level-Doku-Sync (in-progress/README.md,
  roadmap.md, README(s)).

**Welle-6b-Gate:** `make gates` cache-frei gruen mit
20/20 Contracts (neuer GPL-Boundary-Contract); SPDX-Header-
Lint integriert; entweder Integration-Smoke reaktiviert
**oder** Mock-only-Fallback explizit als M5/M6-Defer
dokumentiert.

**Welle-6b-Scope-Risiko:** falls Welle 5b in C2 bereits
den echten IedServer-Smoke geschafft haette (Pfad-B-
Variante), wuerde 6b auf Lizenz-/Boundary-Hardening
reduziert (keine Smoke-Reaktivierung mehr). Aktueller
Welle-5b-Stand: 2c-Mock-only-Fallback aktiv; Smoke-
Reaktivierung steht.

### Welle 7 — Closure (`Done` 2026-06-01)

**Status:** Done. M4-Closure-Welle abgeschlossen
2026-06-01 mit Welle-7-Stack (Pre-C0a `bf23458` +
Pre-C0b `5b2dc24` + C0 `af97fd7` + C0-Review `05a1417`
+ C1 `d2071f0` + C2 `0c644f0` + C3 `121e255` + C4a
`e745f10` + C4b `72e8357`). Detail-Belege in
[`../done/M4-results.md`](../done/M4-results.md);
Slice-Begleit-Doc
[`../done/M4-welle-7.md`](M4-welle-7.md)
(bleibt vorerst in `in-progress/`; Self-Close-Move folgt
als M5-Welle-0-Pre-C0).

- [x] **Alle M4-ADRs auf `Accepted`** — ADR
  0030/0031/0032/0033/0034/0035 (6 M4-ADRs); Pattern
  analog M3-Welle-7-C1.1..C1.6 — C1 `d2071f0`.
- [x] **`done/M4-protocol-adapters.md` Closure-Notiz** —
  dieses Dokument; Top-Status auf `Done` gezogen mit
  Welle-7-C3 `121e255` (vor dem `git mv` `e745f10`).
- [x] **`done/M4-results.md`** — Detail-Welle-Tabelle +
  Abnahme-Belege analog
  [`../done/M3-results.md`](../done/M3-results.md):
  10 A-1-Gates, 1584 Unit + 35 passed + 4 skipped
  Integration, 20 Contracts, Pro-Welle-Reviews —
  C2 `0c644f0`.
- [x] **`roadmap.md` M4-DoD-Checkboxen aktiviert** — alle
  7 Checkboxen `[x]`; IEC-61850-Box-Beschriftung
  S2-vorabschaerft; M4 auf `Done`; „Naechster aktiver
  Slice: M5" gesetzt — C3 `121e255`.
- [x] **Top-Level-Doku-Sync** —
  `README.md` / `README.de.md` / `AGENTS.md` / Status-
  Header in `roadmap.md` auf M4-Done-Stand. AGENTS.md
  §3 Quality-Gates auf 10 A-1-Gates gezogen (NEU
  `spdx-check`) per Audit-Folge — C3 `121e255` +
  Audit-Folge.
- [x] **Self-Close-Move** — `chore(welle-7): git mv
  in-progress/M4-protocol-adapters.md -> done/` —
  C4a `e745f10` (rename-only Commit per
  `feedback_git_mv`-Memory-Konvention).
- [x] **ADR-Bezug-Linkpflege an ADR 0030..0035** (Verfahren
  per ADR 0028 — Subjekte sind die 6 M4-ADRs, nicht
  ADR 0028 selbst): alle Bezug-Refs auf
  `planning/done/M4-protocol-adapters.md` umgelinkt —
  C4b `72e8357`. Kein Forwarder-Stub im alten
  `in-progress/`-Pfad.
- [x] **Open-Trigger fuer M4-Restposten** — Slice-Spec-
  DoD-Streichung (Welle-7-Slice-Doc-Review B3-Finding):
  Welle-6b-C3 hat Trigger 009 (IedServer-Smoke-
  Reaktivierung) bereits aufgemacht als einzige offene
  M4-Folge-Pflicht; alle anderen Welle-Folge-Slices
  (031..034) sind in `done/`. Welle 7 selbst macht
  keinen neuen Trigger.
- [x] **M4-Welle-7-End-to-End-Sweep S-1..S-6** (analog
  M3-Welle-7 §4) — dokumentiert in
  [`../done/M4-results.md §4`](../done/M4-results.md):
  - [x] **S-1** — Welle-0-Trigger-Triage + Welle-7-Sweep
    (Trigger 009 als einzige offene M4-Folge-Pflicht).
  - [x] **S-2** — Sub-Slicing-Schwelle aktiv eingesetzt
    (Welle 5 → 5a/5b; Welle 6 → 6a/6b); Beleg-Tabelle
    in `M4-results.md §4`.
  - [x] **S-3** — Default-`make gates` ohne
    `CRITICAL_COV_TARGETS`-Override cache-frei gruen am
    Welle-7-Closure-Hash (10 A-1-Gates).
  - [x] **S-4** — `make image-audit` **Defer-Pfad
    aktiviert** (pre-existing rot wegen krb5-CVE-Drift
    seit M3-Welle-7-`c61ab0d`; nicht durch M4-Code
    verursacht; Base-Image-Bump als M5-Welle-0-Trigger
    in `M4-results.md §5`-Erbschaft).
  - [x] **S-5** — ADR-Erweiterungs-Pattern fortgefuehrt:
    6 neue M4-ADRs (0030..0035) ohne Supersedes
    (ADR-0011-Pattern; manuell per `grep -l Supersedes:`
    verifiziert).
  - [x] **S-6** — Lastenheft-Coverage-Sweep nach
    M4-Closure: alle 5 `GG-*-001`-Cluster auf `✅ M4`
    (mit Slice-034-F15-Audit-Trail-Note); M5-Trigger
    bleibt UI/Demo-Material.

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

- ✓ `done/M4-protocol-adapters.md` (dieses
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
