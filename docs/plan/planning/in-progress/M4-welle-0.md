# Welle 0 — M4 Slice-Plan-Eroeffnung + Trigger-Triage

**Status:** In Progress — eroeffnet 2026-05-26. Vorabraeumung +
Slice-Plan-Eroeffnung fuer M4 (Protokolladapter — MQTT, Modbus,
OPC-UA, DNP3, IEC 61850). Kanonische M4-Slice-Spezifikation wird
mit C1 in `M4-protocol-adapters.md` (im selben Verzeichnis)
angelegt — dieses Welle-0-Doc ist der Index zur Welle, nicht
der Meilenstein-Slice-Plan selbst.

**Spec-Reife:** Inhaltlich final. Reines Doc-Arbeitspaket
(kein Code-Pfad-Wechsel; Pattern analog M3-Welle-0
[`done/welle-0.md`](../done/welle-0.md)). Welle-0-Decision-Liste
(§3) sammelt offene Fragen, entscheidet sie aber nicht —
Entscheidungen wandern in Welle 1 und den ersten M4-ADR.

## 1. Context

M3 ist seit 2026-05-25 mit Welle-7-Closure abgeschlossen
([`done/M3-faults-agents-observability.md`](../done/M3-faults-agents-observability.md),
[`done/M3-results.md`](../done/M3-results.md)). M4 ist laut
[`roadmap.md §3 M4`](roadmap.md) der naechste aktive Slice mit
fuenf Sub-Adaptern entlang
[`spec/lastenheft.md §16`](../../../../spec/lastenheft.md):

- **MQTT** (`GG-MQTT-001`, SOLLTE) — paho-mqtt; Topic-Schema,
  Payload-Format, QoS, Pub/Sub-Richtung; deterministischer
  Adapter-Smoke-Test.
- **Modbus TCP** (`GG-MODB-001`, SOLLTE) — pymodbus; Register-
  Mapping, Datentypen, Byte-Reihenfolge, Lese-/Schreiboperationen,
  Timeout-Verhalten.
- **OPC-UA** (`GG-OPCUA-001`, SOLLTE) — asyncua; Node-IDs,
  Datentypen, Lese-/Schreibpfade, Fehlerverhalten.
- **DNP3** (`GG-DNP3-001`, SOLLTE) — Points, Variations,
  Qualitaetsflags; **oder dokumentierter Verzicht** per
  Roadmap §3 M4 DoD.
- **IEC 61850** (`GG-IEC-001`, SOLLTE) — Logical Nodes,
  Datenattribute, Report-/Control-Verhalten; **oder
  dokumentierter Verzicht** per Roadmap §3 M4 DoD.

Cross-Cutting-Pflicht aus
[`spec/lastenheft.md`](../../../../spec/lastenheft.md) Z. 1161–1163:
Adapter sind klar als **Simulations- und Testadapter** zu
dokumentieren, **keine** produktive Anlagensteuerung.

**Architektur-Anker:**

- `GG-AR-PORT-DRN-007` (`DeviceProtocolPort`) —
  [`spec/architecture.md §7`](../../../../spec/architecture.md)
  Z. 249 + [`§8.2`](../../../../spec/architecture.md) Z. 510–512.
  Read/Write-Operationen mit Mapping auf `TelemetryPoint` /
  `Command`; Adapter dokumentieren Topic-, Register-, Node-
  bzw. LN/CDC-Profile.
- `GG-AR-COMP-PROTOCOLS` (Komponentensicht; Mapping
  [`spec/lastenheft.md §27`](../../../../spec/lastenheft.md)
  Z. 2166–2170).
- **Code-Status (2026-05-26):**
  `src/grid_gym/hexagon/ports/driven/` enthaelt
  `clock.py`/`fault.py`/`observability.py`/`random.py`/
  `run_repository.py` — **`device_protocol.py` fehlt**. Auch
  `src/grid_gym/adapters/driven/protocol_*` existiert noch
  nicht. Welle 1 ist die Port-Definition, Welle 2+ liefern
  die konkreten Adapter.

**Deployment-Sicht (`spec/architecture.md §16`):** §16 listet
`service: simulation` als „Worker / Tick-Loop" ohne explizite
Adapter-Verortung. Daraus folgt — weil Driven-Adapter in
derselben Prozessgrenze wie die Tick-Loop laufen — dass die
Protokolladapter **kein** eigener Compose-Service sind,
sondern im `simulation`-Container leben. Diese Folgerung
wird in Welle 1 im ersten M4-ADR festgeschrieben (und ist
bis dahin keine Spec-Aussage, sondern Welle-0-Inferenz).
Test-Sibling-Container fuer Broker (mosquitto, modbus-server,
opcua-server) wandern in `tests/integration/compose.yml`
(Trigger-009-Pattern).

Welle 0 leistet die Vorabraeumung:

- M4-Slice-Plan wird in `in-progress/` eroeffnet
  (Vorbelegung Welle 0..7 + Out-of-Scope + Risiken +
  Akzeptanz-/Exit-Kriterien).
- Welle-0-Decision-Liste (§3) sammelt offene Fragen.
- Trigger-Triage: Cross-Check der offenen Trigger gegen
  M4-Scope.

Keine Code-Aenderungen in Welle 0; das spiegelt das
M3-Welle-0-Pattern (reine Doc-Welle).

## 2. Scope

**In Scope:**

1. `docs/plan/planning/in-progress/M4-protocol-adapters.md`
   als neuer M4-Slice-Plan mit Vorbelegung Welle 0..7,
   Out-of-Scope, Risiken + Fallback, Akzeptanz-/Exit-Kriterien
   (Pattern analog
   [`done/M3-faults-agents-observability.md`](../done/M3-faults-agents-observability.md)
   und [`done/M2-devices.md`](../done/M2-devices.md)).
2. Welle-0-Decision-Liste als §3 in
   `M4-protocol-adapters.md` aufnehmen (Entscheidungen
   bleiben offen; werden in Welle 1 + erstem M4-ADR
   getroffen).
3. Trigger-Triage:
   - 004 (`canonical-encoder-Alternative`) — Cross-Check gegen
     M4: MQTT-Payloads sind `bytes`; ein performanterer
     Encoder koennte den Payload-Pfad treffen.
   - 006 (`--strict-bytes`) — Cross-Check gegen M4:
     Modbus-Register und MQTT-Payloads sind `bytes`/`int`/
     `float`; `--strict-bytes` koennte erstmals scharf an
     der `bytes`/`bytearray`-Grenze ziehen.
   - 005 / 007 (`pyright`-Re-Eval / Pre-Commit) —
     Dev-Experience-Trigger, M4-nicht-blockend.
   - 008 (`make sbom`) — M6 mit Release-Workflow,
     M4-fremd.
   - 011 (`MLRandomPort`-Sub-Seed) — Multi-Agent-Trigger,
     M4-fremd.
   - 026 (BESS-Reserve-Market-Spike) — Multi-Agent-/RL-
     Folge, M4-fremd.
   - 030 (RL-Adapter) — Multi-Agent-Folge, M4-fremd.
   - 016..024 (SOLLTE-Geraete/Netz/Battery aus
     M2-Welle-7-Erbschaft) — eigene Slices nach M4,
     M4-fremd.
4. `in-progress/README.md`-Sync:
   `M4-welle-0.md`-Zeile ergaenzen,
   `M4-protocol-adapters.md`-Zeile ergaenzen (mit C1).

**Anti-Scope:**

- Keine Code-Aenderungen. Welle 0 ist reines Doc-
  Arbeitspaket (analog M3-Welle-0).
- Keine neue ADR. Vorbelegung von M4-ADRs (z. B.
  `DeviceProtocolPort`-Surface, Sync/Async-Bridge,
  pro-Adapter-Profile, DNP3+IEC-Verzicht) erfolgt mit
  Welle 1+, nicht in Welle 0.
- Keine M4-DoD-Checkbox-Aktivierung in `roadmap.md` — die
  bleibt `[ ]` bis zur jeweiligen Welle-N-Lieferung.
- Keine Bewegung der `004/006/011/016..024/026/030`-Trigger
  aus `open/`. Trigger-Triage ist nur eine **Doc-Notiz**
  (welche Trigger sind M4-relevant); keine Datei-Moves.
- Kein `git mv`-Restposten aus M3 (M3-Welle-7-Closure hat
  alle Restposten bereits nach `done/` gewandert; anders
  als M3-Welle-0, das damals `welle-7.md` aus M2 erbte).

## 3. Architektur-Entscheidungen

Welle 0 bringt **keine neue ADR**. ADR-Status-Verifikation
fuer M3-ADRs (0022..0027) wurde in M3-Welle-7 abgeschlossen,
alle `Accepted`. Welle 0 sammelt nur die Vorbelegung der
M4-ADR-Kandidaten in `M4-protocol-adapters.md §3` und die
Welle-0-Decision-Liste.

**Vorbelegungs-Liste M4-ADRs** (wird in C1 in
`M4-protocol-adapters.md` aufgenommen):

- **ADR-NNNN** (Provisional in M4-Welle-1):
  `DeviceProtocolPort`-Surface — Protocol-Vertrag, Read/Write-
  Operationen, Mapping auf `TelemetryPoint` / `Command`,
  Lifecycle (`start` / `stop`), Sync/Async-Bridge-Pattern
  (siehe Welle-0-Decision-Liste 2 + 3).
- **ADR-NNNN** (Provisional in M4-Welle-2): MQTT-Adapter-
  Profil — Topic-Schema, QoS-Defaults, Payload-Codec.
- **ADR-NNNN** (Provisional in M4-Welle-3): Modbus-TCP-
  Adapter-Profil — Register-Mapping, Byte-Reihenfolge,
  Timeout-Verhalten.
- **ADR-NNNN** (Provisional in M4-Welle-4): OPC-UA-Adapter-
  Profil — Node-ID-Schema, Sub/Pub-Verhalten,
  async->sync-Bridge.
- **ADR-NNNN** (Provisional in M4-Welle-5): DNP3 + IEC-61850
  Disposition — entweder Verzicht-Notiz mit Begruendung
  (Roadmap §3 M4 DoD erlaubt das) oder Spike-Slice mit
  reduziertem Scope.

Zahl der ADRs ist eine **Obergrenze**; Welle 5 kann als
Anhang zum `DeviceProtocolPort`-Surface-ADR (Welle 1)
konsolidiert werden, falls die Verzicht-Variante
(Decision 1a) gewinnt — ein eigener ADR ist dann
ueberdimensioniert.

Die genaue Nummerierung bleibt offen bis M4-Welle-1 (ADRs
werden in der Reihenfolge ihrer `Proposed`-Datierung
vergeben; letzte vergebene ADR ist 0029).

### Welle-0-Decision-Liste (offene Fragen)

Diese Punkte werden in Welle 0 **nur gesammelt**, nicht
entschieden. Entscheidungen wandern in Welle 1 (ADR
`DeviceProtocolPort`-Surface) bzw. in die jeweilige
Sub-Welle.

1. **DNP3 + IEC-61850 Disposition.** Roadmap §3 M4 DoD
   erlaubt explizit „dokumentierter Verzicht via
   Out-of-Scope-Note". Optionen:
   - (a) Welle 5 als Verzicht-ADR (Begruendung:
     Lizenz/Maintenance-Last der `pydnp3`/`asyncio-iec61850`-
     Bibliotheken; Test-Sibling-Container schwer
     verfuegbar).
   - (b) Welle 5 als Spike mit reduziertem Scope (nur
     Read-Pfad, ein Profil).
   - Entscheidung: Welle 1 (gemeinsam mit erstem M4-ADR).
2. **Sync vs. async Adapter-Vertrag.** TickLoop ist sync;
   `paho-mqtt` ist sync, `asyncua` und die meisten
   DNP3/IEC-Stacks sind async. `pymodbus` ≥ 3 bietet
   beides (`ModbusTcpClient` sync und `AsyncModbusTcpClient`
   async) — die konkrete Variante wird per Welle-1-
   Entscheidung festgenagelt. Optionen:
   - (a) `DeviceProtocolPort` als sync-Protocol;
     async-Stacks bekommen Adapter-internen Event-Loop-
     Thread + Queue (Pattern aus
     [`telemetry_otlp/`](../../../../src/grid_gym/adapters/driven/telemetry_otlp/)
     pruefen).
   - (b) `DeviceProtocolPort` als async-Protocol;
     TickLoop bekommt einen Sync->Async-Adapter-Shim.
   - Entscheidung: Welle 1 in ersten M4-ADR
     (`DeviceProtocolPort`-Surface).
3. **Adapter-Lifecycle.** Wo werden Adapter konnektiert?
   Optionen:
   - (a) Bei Service-Boot in `bootstrap` (analog
     `persistence_postgres`).
   - (b) Bei `TickLoop.run()`-Start (Adapter sind tick-
     lebenslang, nicht prozess-lebenslang).
   - Entscheidung: Welle 1 in ersten M4-ADR.
4. **Protokoll-Profile-Deklaration.** Wo stehen Topic /
   Register / Node-ID / LN-CDC pro Device? Optionen:
   - (a) Inline im Szenario-YAML pro Device-Eintrag (neuer
     `protocol:`-Sub-Block analog `agents:`).
   - (b) Separates `protocol_profile.yaml` pro Adapter
     (Mapping `device_id` → Topic/Register/Node).
   - (c) Hybrid: Default-Mapping per Konvention,
     Profile-Overrides im Szenario.
   - Entscheidung: Welle 2 (erste konkrete Adapter-Welle —
     MQTT setzt das Pattern).
5. **Test-Sibling-Container.** Welche Broker brauchen
   testcontainers (Pattern aus
   [`done/009-tests-integration-compose.md`](../done/009-tests-integration-compose.md))?
   - MQTT: `eclipse-mosquitto:2` (gut verfuegbar; Reserve
     bei Lizenz-Bruch: in-process Broker via `flashmq` /
     `amqtt`).
   - Modbus: `oitc/modbus-server` o. ae. (Spike noetig —
     Image-Lizenz pruefen).
   - OPC-UA: `open62541/open62541` o. ae. (Spike noetig).
   - DNP3 / IEC: container-Verfuegbarkeit ist
     Disposition-Treiber fuer Decision 1.
   - Entscheidung: pro Welle (2/3/4) mit der jeweiligen
     Adapter-Welle.
6. **`AC-ADAPTER-LIGHTWEIGHT` fuer `protocol_*`.** Der
   Architektur-Test muss alle `protocol_*`-Module
   erfassen (kein Sickern von Fachlogik in Adapter).
   - Code-Pfad: `tools/arch_check.py` —
     `_check_adapter_lightweight()` (Z. 1093) + Pfad-
     Filter `_is_adapter_lightweight_path()` (Z. 1067).
     Welle 1 prueft, ob der Pfad-Filter `protocol_*`
     bereits erfasst oder explizit ergaenzt werden muss.
   - Entscheidung: Welle 1 in ersten M4-ADR-Anhang
     (Contract-Listing).
7. **Snapshot-Pflicht fuer Adapter.** Sind
   `DeviceProtocolPort`-Adapter snapshot-relevant
   (Reconnect-State, In-Flight-Acks)? ADR 0015
   (Sub-Snapshot-Codec) gibt das additive Pattern vor.
   - Default-Vorschlag: Adapter sind stateless aus
     Replay-Sicht (Telemetry/Commands fliessen ueber
     `TickLoop`-Sub-Snapshots); Reconnect-State ist
     volatile.
   - Entscheidung: Welle 1 in ersten M4-ADR.

### Trigger-Drift-Notiz (zur Aufnahme in C2)

- **004** (`canonical-encoder-Alternative`): M4-Drift-
  Pruefung — MQTT-Payloads sind `bytes`, ein
  performanterer JSON-Encoder (`orjson` / `msgspec`)
  koennte den MQTT-Publish-Pfad bedienen. **Aktivierung**:
  erst bei messbarem Perf-Druck am MQTT-Publish-Throughput;
  bleibt in `open/`.
- **006** (`--strict-bytes`): M4-Drift-Pruefung —
  Modbus-Register und MQTT-Payloads forcieren erstmals
  produktive `bytes`/`int`/`float`-Konvertierungen im
  Adapter-Code. **Aktivierung**: nach M4-Welle-3
  (Modbus) erneut pruefen, ob `--strict-bytes` jetzt
  ohne `# type: ignore`-Inflation greift; bleibt vorerst
  in `open/`.
- **005 / 007 / 008 / 011 / 016..024 / 026 / 030**: alle
  M4-fremd, keine Aenderung am Aktivierungs-Trigger.
  Bleiben in `open/`.

## 4. Liefer-Reihenfolge (3 Commits)

### C0 — `docs(plan)`: M4-welle-0 Slice-Doc

- Dieses Dokument als Welle-Start-Marker. Status:
  `In Progress`.
- `in-progress/README.md`-Sync: `M4-welle-0.md`-Zeile
  ergaenzt.
- **Kein `git mv`** in C0 — anders als M3-Welle-0 erbt
  M4-Welle-0 keinen Restposten (M3-Welle-7-Closure hat
  bereits alles nach `done/` gewandert; siehe
  [`done/M3-faults-agents-observability.md`](../done/M3-faults-agents-observability.md)
  §6).

### C1 — `docs(plan)`: M4-Slice-Plan eroeffnen — protocol-adapters

- NEU `docs/plan/planning/in-progress/M4-protocol-adapters.md`
  mit Vorbelegung:
  - §1 Zweck (fuenf Sub-Adapter, Lastenheft-Anschluss,
    Cross-Cutting-Pflicht „Simulations-/Testadapter").
  - §2 Erfolgskriterien (Akzeptanz-/Exit-Kriterien,
    Default-`make gates`-Erweiterung um `adapters/driven/
    protocol_*`).
  - §3 Liefer-Reihenfolge (Welle 0..7 vorbelegt mit
    Sub-Slicing-Schwelle analog M3 §3 + Welle-0-
    Decision-Liste).
  - §4 Out-of-Scope (UI/M5-Material, Performance-
    Benchmarks/M6, RL-Adapter-Anbindung, M2-SOLLTE-
    Trigger 016..024).
  - §5 Risiken + Fallback (Sync/Async-Bridge, DNP3/IEC-
    Disposition, Test-Container-Lizenz, AC-ADAPTER-
    LIGHTWEIGHT-Drift).
  - §6 Wandert nach (`done/`).
  - §7 Verifikationspfad.
- `in-progress/README.md`-Sync:
  `M4-protocol-adapters.md`-Zeile ergaenzt.
- **C1-Groesse**: Pattern-Treue zu M3-Welle-0 (`done/M3-
  faults-agents-observability.md` = 836 Zeilen) heisst
  monolithischer C1. Erst splitten in C1a (§1/§2/§4/§7) +
  C1b (§3 Vorbelegung + §5 Risiken), falls die M4-
  Vorbelegung deutlich groesser als M3-Niveau wird.

### C2 — `docs(plan)`: M4-Welle-0 Trigger-Triage

- Trigger-Triage-Notiz in `M4-protocol-adapters.md §3
  Welle 0`:
  - 004 / 006 — M4-Drift-Pruefung dokumentieren (siehe
    §3 Trigger-Drift-Notiz oben).
  - 005 / 007 / 008 / 011 / 016..024 / 026 / 030 —
    M4-fremd, kein Drift.
- `M4-welle-0.md`-Status-Header von `In Progress` auf
  `Done` ziehen; C2-Commit-Hash einsetzen.

## 5. Critical Files

| Pfad                                                                | Commit | Aktion                            |
| ------------------------------------------------------------------- | ------ | --------------------------------- |
| `docs/plan/planning/in-progress/M4-welle-0.md`                      | C0     | NEU                               |
| `docs/plan/planning/in-progress/README.md`                          | C0     | EDIT (M4-welle-0.md ergaenzt)     |
| `docs/plan/planning/in-progress/M4-protocol-adapters.md`            | C1     | NEU                               |
| `docs/plan/planning/in-progress/README.md`                          | C1     | EDIT (M4-Slice-Plan ergaenzt)     |
| `docs/plan/planning/in-progress/M4-protocol-adapters.md`            | C2     | EDIT (Welle-0-Triage-Notiz)       |
| `docs/plan/planning/in-progress/M4-welle-0.md`                      | C2     | EDIT (Status → Done)              |

## 6. Verifikationspfad

1. `in-progress/`-Bestand: enthaelt `roadmap.md`, `README.md`,
   `M4-welle-0.md` (neu) und nach C1 zusaetzlich
   `M4-protocol-adapters.md`.
2. `done/`-Bestand: unveraendert ggue. M3-Welle-7-Closure
   (kein M4-Welle-0-Move).
3. `open/`-Bestand: 17 Trigger-Files (`004`..`008`, `011`,
   `016..024`, `026`, `030`) plus `README.md` — 18 Dateien
   total; keine Datei-Moves in Welle 0.
4. `make gates`-Sanity: gruen (Doc-only-Edits sollten den
   Code-Pfad nicht treffen).
5. Git-Pattern: drei neue M4-Welle-0-Commits in der
   Reihenfolge `docs(plan): M4-welle-0 Slice-Doc (C0)` →
   `docs(plan): M4-Slice-Plan eroeffnen (C1)` →
   `docs(plan): M4-Welle-0 Trigger-Triage (C2)`.
6. Roadmap-Status-Header bleibt unveraendert
   („Naechster aktiver Slice: M4 (Protokolladapter …)") —
   ein M4-Welle-1-Start-Commit wird den Header spaeter
   auf „M4 In Progress" ziehen.

## 7. Risiken

- **Welle-0-Decision-Liste sammelt zu viel, Welle 1
  zerfaellt.** 7 offene Fragen — wenn Welle 1 alle
  gleichzeitig im ersten M4-ADR entscheiden will,
  ueberzieht sie. *Mitigation*: Welle 1 entscheidet nur
  Fragen 1 + 2 + 3 + 7 (Port-Surface-relevant); Fragen
  4 + 5 + 6 wandern in Welle 2 (MQTT als erstes konkretes
  Adapter-Beispiel).
- **DNP3/IEC-Disposition kippt nach Welle 4.** Wenn
  asyncua-Erfahrung aus Welle 4 zeigt, dass async-Stacks
  in einer sync-`DeviceProtocolPort`-Surface schmerzhaft
  sind, wird die Verzicht-Variante (Decision 1a)
  attraktiver. *Mitigation*: Decision 1 ist in Welle 1
  bewusst **vorlaeufig** (Verzicht-Default), wird in
  Welle 5 final festgeschrieben.
- **Test-Sibling-Container-Lizenz.** Modbus- und OPC-UA-
  Server-Container haben oft restriktive Lizenzen
  (kommerzielle Pruefung). *Mitigation*: Welle 2/3/4
  klaeren Lizenz **vor** der Adapter-Implementierung;
  Fallback ist ein eigener Mini-Server im Test-Code
  (analog `tests/integration/`-Pattern).
- **AC-ADAPTER-LIGHTWEIGHT bricht spaet.** Wenn ein
  Adapter unbeabsichtigt Fachlogik einsammelt (z. B.
  Unit-Konvertierung im MQTT-Codec), schlaegt der
  Architektur-Test erst in Welle 2+ an. *Mitigation*:
  Welle 1 erweitert den Architektur-Test **vor** dem
  ersten Adapter-Commit; Welle 2 darf nicht mit rotem
  AC-ADAPTER-LIGHTWEIGHT starten.
- **Snapshot-Schema-Drift durch Reconnect-State.** Falls
  Decision 7 (stateless) sich in Welle 3+ als zu eng
  herausstellt (z. B. Modbus-Read-Cursor muss persistent
  sein), wird ein Snapshot-Schema-Bump faellig. *Mitigation*:
  Welle 1 dokumentiert den stateless-Default als
  reversibel; ein Schema-Bump folgt dem ADR-0015-Pattern.

## 8. Wandert nach

- `done/M4-welle-0.md` mit M4-Welle-7-Closure-Slice
  (analog `welle-0.md` → `done/welle-0.md` aus M3).
- `M4-protocol-adapters.md` wandert nach `done/` mit
  M4-Welle-7-Closure.
