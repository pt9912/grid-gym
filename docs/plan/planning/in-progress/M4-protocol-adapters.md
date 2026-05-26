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
   (neu in Welle 1; aktuell fehlt die Datei).
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

### Welle 1 — DeviceProtocolPort-Foundation

- ADR-Folge (geplant **erster M4-ADR**) fuer
  `DeviceProtocolPort`-Surface mit Entscheidungen aus
  [`M4-welle-0.md`](../done/M4-welle-0.md) §3 Decision-Liste:
  - Decision 2 (Sync vs. async Vertrag, **final**):
    sync-`Protocol` mit Adapter-internem Thread/Queue
    **oder** async-`Protocol` mit TickLoop-Shim — ADR
    setzt die Antwort scharf. Vergleichsmuster
    [`telemetry_otlp/`](../../../../src/grid_gym/adapters/driven/telemetry_otlp/)
    pruefen.
  - Decision 3 (Lifecycle, **final**): `start`/`stop` bei
    Service-Boot in `bootstrap` **oder** bei
    `TickLoop.run()`-Start — ADR setzt die Antwort scharf.
  - Decision 7 (Snapshot-Pflicht, **final**): ADR schreibt
    den stateless-Default aus Replay-Sicht fest
    (Reconnect-State volatile); Reversibilitaet ist via
    ADR-0015-Pattern dokumentiert (Schema-Bump faellig,
    falls Welle 3+ Persistenz-Bedarf zeigt).
  - Decision 1 (DNP3 + IEC-61850 Disposition,
    **provisorisch**): ADR schreibt den Verzicht-Default
    provisorisch fest (Option a aus
    [`M4-welle-0.md`](../done/M4-welle-0.md) §3 Decision 1).
    Finale Disposition in Welle 5, informiert durch
    asyncua-Erfahrung aus Welle 4.
- NEU `src/grid_gym/hexagon/ports/driven/device_protocol.py`
  mit `DeviceProtocolPort`-Protocol + Read/Write-Methode(n)
  + Lifecycle-Hooks + `*Error`-Subsystem.
- `AC-ADAPTER-LIGHTWEIGHT`-Pfad-Filter (Decision 6) ist
  bereits aktiv (`tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`). Welle 1 prueft nur,
  dass die `protocol_*`-Erfassung gruen ist (Sanity
  `make arch-check`), **bevor** Welle 2 den ersten
  Adapter liefert — keine Filter-Aenderung noetig.
- Unit-Tests fuer das Protocol (Pattern aus
  `tests/unit/hexagon/ports/`).

**Welle-1-Gate:** `make test-unit` gruen mit
`DeviceProtocolPort`-Protocol-Test. Default-
`CRITICAL_COV_TARGETS` bleibt unveraendert (Adapter-
Erweiterung kommt mit Welle 2).

### Welle 2 — MQTT-Adapter

- ADR-Folge (geplant **MQTT-Adapter-ADR**) mit Decision 4
  (Profile-Deklaration; MQTT setzt das Pattern: Topic
  inline im Szenario-YAML, separat oder hybrid).
- NEU `src/grid_gym/adapters/driven/protocol_mqtt/` mit
  `paho-mqtt`-Wrapper:
  - Topic-Schema-Mapping (Device-ID → Topic).
  - Payload-Codec (Telemetry → JSON, Command → JSON;
    Trigger-004-Drift bleibt parkbar).
  - QoS-Default, Pub/Sub-Richtung, Fehlerverhalten.
- NEU Integration-Smoke via testcontainers
  (`eclipse-mosquitto:2`; Reserve `flashmq`/`amqtt` als
  in-process Broker bei Lizenz-Bruch — siehe
  [`M4-welle-0.md`](../done/M4-welle-0.md) §3 Decision 5).
- `tests/integration/compose.yml`-Erweiterung um
  Mosquitto-Sibling.

**Welle-2-Gate:** `make test-integration` gruen mit
MQTT-Smoke. Default-`CRITICAL_COV_TARGETS` um
`adapters/driven/protocol_mqtt` erweitert.

### Welle 3 — Modbus-TCP-Adapter

- ADR-Folge (geplant **Modbus-TCP-Adapter-ADR**) mit
  Modbus-spezifischen Profil-Entscheidungen (Register-
  Mapping, Byte-Reihenfolge, Datentyp-Konvention).
- NEU `src/grid_gym/adapters/driven/protocol_modbus/` mit
  `pymodbus`-Wrapper (Sync- oder Async-Client je nach
  Welle-1-Entscheidung):
  - Register-Mapping (Device-ID → Coil/Holding-Register-
    Adressraum).
  - Datentypen (`int16`/`int32`/`float32`), Byte-
    Reihenfolge (Big/Little-Endian, Word-Swap).
  - Timeout-Verhalten + Read/Write-Smoke (Lese- und
    Schreibpfad als Lastenheft-Akzeptanz Z. 1135–1136).
- Trigger-006-Re-Eval: `--strict-bytes` an den
  Modbus-Bytes-Pfaden pruefen. Falls scharf machbar:
  Trigger nach `next/` ziehen.
- Integration-Smoke via testcontainers (Modbus-Server-
  Container — Lizenz **vorher** pruefen; Fallback in-process
  Mini-Server).

**Welle-3-Gate:** `make test-integration` gruen mit
Modbus-Smoke. Default-`CRITICAL_COV_TARGETS` um
`adapters/driven/protocol_modbus` erweitert.

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
