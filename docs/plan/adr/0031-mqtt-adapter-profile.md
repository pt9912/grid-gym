# ADR 0031 — MQTT-Adapter-Profile (M4 Welle 2)

**Status:** Accepted — gezogen 2026-06-01 mit M4-Welle-7-C1
(dieser Commit; M4-Closure-Welle). Provisional-Schritt
2026-05-30 mit M4-Welle-2-C3 nach M4-Welle-2-C2-Merge
`f33bb4e` (feat: `protocol_mqtt`-Modul + 50 neue Unit-Tests
+ Mosquitto-Integration-Smoke; `make gates` cache-frei gruen
ohne `CRITICAL_COV_TARGETS`-Override; 19/19 Contracts KEPT).
Decisions 4a/4b/4c/4d sind produktiv ueber M4-Welle-2..6b
gehalten; Cross-Adapter-OTel-Span-Wrap aus Welle 6a wrappt
auch den MQTT-Adapter ohne Adapter-Code-Diff.
Status-Pfad: Proposed (2026-05-30 `4e102b8`) → Provisional
(2026-05-30 M4-Welle-2-C3) → **Accepted** (2026-06-01
M4-Welle-7-C1, dieser Commit).
**Datum:** 2026-05-30 (Erstfassung) / 2026-05-30 (Provisional-Schaerfung) / 2026-06-01 (Accepted, M4-Welle-7-C1)
**Bezug:**
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md)
(Schaerfungs-ohne-Supersede-Pattern — ADR 0031 schaerft
ADR 0030 §2.1 konkret fuer MQTT, ohne den Sync-
`DeviceProtocolPort`-Vertrag zu ersetzen),
[`ADR 0030`](0030-device-protocol-port-surface.md) §2.1
(Sync-`Protocol`-Vertrag; paho-mqtt-Halb-Sync-Begruendung:
paho-mqtt laeuft per `loop_start()` in einem internen
Thread, Callbacks feuern aus diesem Thread — ADR 0030 §2.1
hat den **Callback->Sync-Port-Marshal adapter-intern via
thread-sichere `queue.Queue`** als Welle-2-Implementer-
Auflage vorbelegt; ADR 0031 §2.4 macht das konkret) +
§2.2 (Caller-Scope-Lifecycle — Welle-2-MQTT-Adapter muss
im Caller-`try/finally` gewrappt werden; keine TickLoop-
Aenderung) + §2.3 (stateless aus Replay-Sicht — MQTT-
Reconnect-State ist volatile, kein Snapshot-Bump),
[`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
§2.4 (Builder-Symmetrie-Pattern fuer Scenario-Loader-Kwargs
— `protocol_ports` ist seit M4-Welle-1-C2 in `TickLoopWiring`
+ `build_tick_loop` integriert; ADR 0031 fuegt nur das
Adapter-Profile-Parsing hinzu, ohne den
`TickLoopWiring`-Vertrag zu aendern) + §2.5
(Scenario-YAML-Top-Level-Block-Pattern: Praezedenz fuer
Decision 4a-Wahl),
[`Trigger 014`](../planning/done-archive/014-generic-snapshot-format-codec.md)
(`canonical_json`-Source: M2-Welle-0a-Closure unter
`src/grid_gym/hexagon/core/serialization/canonical.py`;
Pattern-Praezedenz fuer Decision 4b deterministische
Serialisierung — Welle 2-MQTT-Adapter benutzt dieselbe
Encoder-Routine, ohne sie zu reimplementieren),
[`ADR 0024`](0024-observability-port-trio.md) §4.5
(OTLP-Adapter-Praezedenz fuer Welle-6-Span-Wrap-Forward-
Pointer — Welle 2 wrappt **noch keine** Adapter-Calls; das
ist Welle-6-Material).
M4-Slice-Plan
[`done/M4-protocol-adapters.md`](../planning/done-archive/M4-protocol-adapters.md)
§3 Welle 2; M4-Welle-0-Decision-Liste
[`done/M4-welle-0.md`](../planning/done-archive/M4-welle-0.md) §3
Decision 4 (Profile-Deklaration) + Decision 5
(Test-Sibling-Container) + Decision 6
(`AC-ADAPTER-LIGHTWEIGHT`-Pfad-Filter).
Lastenheft §16 (`GG-MQTT-001`, Z. 1120–1133 SOLLTE-Cluster:
Topic-Schema + Payload-Format + QoS + Pub/Sub-Richtung +
Fehlerverhalten + deterministischer Adapter-Smoke-Test +
Cross-Cutting-Pflicht „Simulations-/Testadapter").
Architektur §7 (`GG-AR-PORT-DRN-007` Driven-Ports-Tabelle
— ADR 0030 hat den Slot belegt; Welle 2 liefert ersten
Implementer) + §8.2 (Adapter-Interfaces-Driven-
Beschreibung — Topic-Schema-Profile konkretisiert die
generische Beschreibung) + §16 (Deployment-Sicht —
`protocol_mqtt`-Adapter lebt im `simulation`-Worker, kein
eigener Compose-Service; **Mosquitto-Sibling ist
Test-Infrastruktur unter `tests/integration/compose.yml`**,
nicht im Produktions-Deployment).
M3-Welle-6 als Pattern-Anker:
[`done/M3-welle-6.md`](../planning/done-archive/M3-welle-6.md) +
[`tests/integration/test_otlp_compose_smoke.py`](../../../tests/integration/test_otlp_compose_smoke.py)
(testcontainers-Sibling-Pattern; Compose-Erweiterung um
neuen Service; Healthcheck-Wait-Loop).

---

## 1. Kontext

`GG-MQTT-001` (Lastenheft §16 Z. 1120–1133) verlangt einen
MQTT-Adapter als **Simulations-/Testadapter** mit
deterministischem Adapter-Smoke-Test. M4-Welle-1 hat die
`DeviceProtocolPort`-Surface (ADR 0030 `Provisional`)
produktiv geliefert; Welle 2 liefert den ersten konkreten
Implementer auf dieser Surface: `MqttDeviceProtocolPort`
unter `src/grid_gym/adapters/driven/protocol_mqtt/`.

ADR 0030 hat den **Sync-Vertrag** und den **Caller-Scope-
Lifecycle** finalisiert. ADR 0031 schaerft die fuer den
MQTT-Adapter notwendigen Sub-Entscheidungen **konkret**:

- **Decision 4a (Topic-Schema-Deklaration)** — wo und wie
  werden Device-ID → Topic-Mappings deklariert?
- **Decision 4b (Payload-Codec)** — wie werden Telemetry-
  und Command-Payloads serialisiert?
- **Decision 4c (QoS-Default)** — welcher paho-mqtt-
  QoS-Level gilt pro Richtung?
- **Decision 4d (Callback->Sync-Marshal)** — wie wird der
  paho-mqtt-Loop-Thread-Callback gegen die Sync-`read()`-
  Surface gemarshalt?

Die M4-Welle-0-Decision-Liste
([`done/M4-welle-0.md`](../planning/done-archive/M4-welle-0.md) §3)
hat Decision 4 als Adapter-spezifische Frage markiert
(„MQTT setzt das Pattern; Modbus + OPC-UA folgen oder
schaerfen pro Adapter-ADR"). ADR 0031 entscheidet Decision
4a..4d **final** fuer MQTT; Welle 3 (Modbus-ADR) und
Welle 4 (OPC-UA-ADR) koennen das Pattern reusen oder per
Schaerfungs-ADR (ADR-0011-Pattern) ueberschreiben.

**Spannungsfeld:**

- **Topic-Schema-Lokalisation:** Scenarios sind heute
  YAML-Top-Level-Bloecke (`devices`, `agents`, `faults`,
  `events`, `load_events`, `load_profiles`, `grid_model`).
  MQTT-Topics gehoeren entweder zum Adapter-Profil
  (inline in `protocol_ports`-Block) **oder** zu einer
  eigenen Top-Level-Section (`mqtt_profiles`). Trade-off:
  Inline ist einfacher zu lesen fuer kleine Topic-Mengen
  (≤ 10 Devices); separat skaliert besser und erlaubt
  Profile-Reuse zwischen Scenarios.
- **Payload-Codec:** Das Repo hat seit M2-Welle-0a einen
  `canonical_json`-Encoder (deterministisch + sortiert,
  `serialization/canonical.py::canonical_json`). MQTT
  koennte `canonical_json` direkt benutzen oder einen
  perform-orientierten Encoder (`orjson`/`msgspec`)
  evaluieren. Trigger 004
  ([`open/004`](../planning/open/004-canonical-encoder-alternative-adr.md))
  haelt die Re-Eval offen; ADR 0031 entscheidet
  **Welle-2-Default** und legt die Re-Eval-Bedingung fest.
- **QoS-Wahl:** paho-mqtt-QoS-Level 0/1/2 haben jeweils
  Latenz/Reliability-Trade-offs. Test-Smoke ist
  niedrig-Frequenz; produktive Simulationen koennten
  hoher Frequenz haben. Default-Wahl muss Test-stabil
  und Demo-realistisch sein.
- **Callback-Threading:** ADR 0030 §2.1 hat den Sync-
  Vertrag final beschlossen — der MQTT-Adapter muss den
  paho-Loop-Thread-Callback (`on_message`) gegen `read()`
  marshallen. Die Wahl zwischen Single-Queue +
  Target-Filter und Per-Target-Queue-Dict hat Latenz-
  und Memory-Implikationen.

---

## 2. Entscheidung

ADR 0031 legt vier Profile-Decisions fest.

### 2.1 Decision 4a — Topic-Schema inline im `protocol_ports`-Block (final)

Topic-Profile werden **inline** im `protocol_ports`-
Scenario-YAML-Block deklariert. Eine separate
`mqtt_profiles`-Top-Level-Section wird in Welle 2 **nicht**
eingefuehrt; sie bleibt als Schaerfungs-Optionspfad fuer
Welle 6 (Cross-Adapter-Hardening) offen.

**Skizze (finale Signatur in Welle-2-C2-feat):**

```yaml
protocol_ports:
  - type: mqtt
    broker_host: "localhost"
    broker_port: 1883
    client_id: "grid-gym-sim"
    topics:
      battery1:
        telemetry: "grid/devices/battery/1/telemetry"
        command: "grid/devices/battery/1/command"
        qos_publish: 0
        qos_subscribe: 1
      pv1:
        telemetry: "grid/devices/pv/1/telemetry"
        # command/qos_* via Decision-4c-Default
```

Konkretes YAML-Schema (Pflicht-Felder, Optional-Felder,
Default-Werte pro Feld) wird in C2 in einer `mypy --strict`-
sauberen `MqttProtocolPortConfig`-frozen-dataclass (analog
`OtlpAdapterConfig` aus M3-Welle-6) und einer Validator-
Routine fixiert.

**Begruendung:**

- Pattern-Praezedenz: `OtlpAdapterConfig` (ADR 0024 §4.5)
  ist ebenfalls inline im Adapter-Block. Das hat sich in
  M3-Welle-6 als gut lesbar erwiesen.
- M4-Welle-2-Scenarios haben typischerweise ≤ 10 Devices —
  Inline-Wachstum bleibt handhabbar.
- Separate Profile-Section haette zwei zusaetzliche
  Schritte: (a) neuer Top-Level-Schluessel
  `mqtt_profiles`, (b) Profile-Lookup-Indirektion. Welle 2
  spart beides ein und gewinnt Klarheit.
- Reuse-Bedarf zwischen Scenarios ist hypothetisch — wenn
  er konkret wird (z. B. Welle 6 Cross-Adapter-Hardening
  oder M5 UI-Editor), schaerft eine Folge-ADR per
  ADR-0011-Pattern. Welle 2 dokumentiert die Reusability-
  Option explizit als reversibel.
- Welle 3 (Modbus) wird vermutlich dieselbe Inline-
  Praezedenz nehmen koennen (Register-Schema ist analog
  pro Adapter eindeutig); Welle 4 (OPC-UA) auch, weil
  Node-ID-Schema pro Server eindeutig ist.

**Konsequenz:** `MqttProtocolPortConfig`-frozen-dataclass
unter `src/grid_gym/adapters/driven/protocol_mqtt/_config.py`
mit Pflicht-Feldern `broker_host`, `broker_port`,
`client_id`, `topics: Mapping[str, MqttTopicConfig]` (Mapping
von `device_id` auf Topic-Profil). Optional-Felder mit
Defaults aus Decision 4c. Scenario-Loader (`hexagon/core/
scenario/loader.py`) bekommt einen `_parse_mqtt_protocol_port_config`-
Helfer **im Adapter-Bereich** (nicht im Core-Loader, weil
Loader-Code MQTT-frei bleiben muss — siehe §4
Konsequenzen + [`AC-HEXAGON-PURE`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)).

### 2.2 Decision 4b — Payload-Codec `canonical_json` (final, mit Trigger-004-Re-Eval-Pfad)

Telemetry- und Command-Payloads werden mit
`canonical_json` (Pfad
`src/grid_gym/hexagon/core/serialization/canonical.py::
canonical_json`, M2-Welle-0a-Stand; Quelle und Begruendung
siehe Trigger 014 `done/014-generic-snapshot-format-codec.md`)
serialisiert. Encoding: deterministisches JSON (sortierte
Keys, kein Whitespace, UTF-8-Bytes); Decoding: Standard
`json.loads()` (asymmetrisch — Lesen ist tolerant,
Schreiben ist strikt; Pattern uebernommen von der
Snapshot-/Replay-Asymmetrie aus Trigger 014).

**Begruendung:**

- Determinismus ist Cross-Cutting im Repo (`canonical_json`
  wird vom Snapshot-Layer, Replay-Determinismus, Trace-ID-
  Generierung benutzt). MQTT-Publish soll diesem Pattern
  folgen — Replay-Determinismus ueberlebt damit auch fuer
  MQTT-spezifische Test-Scenarios.
- Performance-Druck ist in Welle 2 **nicht** messbar:
  Test-Smoke ist niedrig-Frequenz (Tick-Loop-Standard,
  nicht Stress-Test); Produktivnutzung in Welle 6+ folgt
  realistischen Frequenz-Profilen.
- `orjson`/`msgspec` als Welle-2-Default wuerde Trigger 004
  praeventiv aktivieren, ohne dass der Bedarf belegt ist —
  YAGNI.

**Re-Eval-Bedingung:** Welle 6 (Cross-Adapter-Hardening)
prueft, ob der MQTT-Publish-Throughput im realen Compose-
Smoke unter realistischen Frequenz-Profilen
(`telemetry_hz > 100` pro Device) messbar zum Bottleneck
wird. Falls ja: Trigger 004 aktivieren mit einer Folge-ADR
(`orjson` als bevorzugte Alternative — siehe Trigger-
Body); falls nein: Trigger 004 explizit als „Welle-6-
Stand re-evaluiert, kein Aktivierungs-Bedarf" notieren.

**Konsequenz:** `_codec.py`-Modul (oder inline in
`__init__.py`, falls AC-ADAPTER-LIGHTWEIGHT-Schwelle nicht
gerissen) mit zwei Funktionen:
`encode_telemetry(payload) -> bytes` (Wrapper um
`canonical_json`) und `decode_telemetry(payload: bytes) ->
TelemetryPoint` (mit `json.loads` + `pydantic`-Validierung).
Symmetrisch fuer Command. Pattern-Praezedenz: M2-Welle-6a-
`snapshot_codec.py`.

### 2.3 Decision 4c — QoS-Default 0 fuer Telemetry, 1 fuer Commands (final, ueberschreibbar)

paho-mqtt-QoS-Defaults:

- **Telemetry-Publishes:** `QoS 0` (fire-and-forget, at-
  most-once). High-volume; Verlust einzelner Nachrichten
  bei Verbindungsabbruch ist tolerabel; Replay-Determinismus
  haengt nicht am MQTT-Publish-Erfolg (sondern am
  TickLoop-Snapshot, der ohnehin alle 4c-Stati persistiert).
- **Command-Publishes:** `QoS 1` (acknowledged, at-least-
  once). Kommandos muessen ankommen; Duplikat-Empfang ist
  idempotent (Welle-3-Modbus + Welle-4-OPC-UA spezifizieren
  Idempotenz-Vertraege per Adapter-ADR).
- **Subscribe-Pfade:** `QoS 1` als Default (at-least-once
  liefert Telemetry zuverlaessig; Duplikat-Empfang wird
  auf der Adapter-Seite per `_seen_message_ids`-Cache
  dedupliziert — Pattern in C2 konkret).

**Begruendung:**

- paho-mqtt-Doku „QoS 0 ist Standard fuer Telemetry-Daten;
  QoS 1 fuer kritische Kontroll-Pfade" (vgl. paho-mqtt-
  Tutorial + MQTT-Spec §4.3 Quality of Service).
- QoS 2 (exactly-once, 4-Message-Handshake) ist fuer Test-
  Smoke Overkill; Latenz-Overhead ohne Reliability-Gewinn
  in Sim-Kontext.
- Override-Pfad: pro `topics.<device_id>.qos_publish` und
  `qos_subscribe` (Decision 4a-Inline-Schema). Scenarios
  koennen pro Topic die Wahl ueberschreiben.

**Konsequenz:** `MqttTopicConfig.qos_publish: int = 0`,
`qos_subscribe: int = 1` als Pflicht-Felder mit Defaults.
Validator erzwingt `qos in {0, 1, 2}` (ScenarioInvalid-
MqttQosError, neue typed Exception). Welle 6 prueft
Telemetry-Frequenz-Profile gegen Default-QoS-0 und
schaerft ggf.

### 2.4 Decision 4d — Per-Target-`queue.Queue` mit Lazy-Init im paho-mqtt-Callback (final)

`MqttDeviceProtocolPort` haelt ein internes
`dict[device_id, queue.Queue[TelemetryPoint]]`. Der
paho-mqtt-`on_message`-Callback (laeuft im paho-internen
Loop-Thread) macht:

1. Topic → `device_id`-Lookup ueber den (in C1-Decision-4a
   festgelegten) Topic-Mapping-Index (Reverse-Lookup).
2. Lazy-Init der Per-Target-Queue, falls noch nicht
   vorhanden (`self._queues.setdefault(device_id,
   queue.Queue())`).
3. `decode_telemetry(msg.payload)` → `TelemetryPoint`.
4. `queue.put_nowait(point)`.

`read(target)` macht:

```text
q = self._queues.get(target)
if q is None:
    return None
try:
    return q.get_nowait()
except queue.Empty:
    return None
```

`write(target, command)` macht:

```text
topic = self._resolve_command_topic(target)
qos = self._resolve_command_qos(target)
payload_bytes = encode_command(command)
self._client.publish(topic, payload_bytes, qos=qos)
```

`client.publish()` ist laut paho-mqtt-Doku thread-safe;
es ist kein zusaetzlicher Lock noetig.

**Begruendung:**

- **Per-Target-Queue statt Single-Queue:** O(1) `read`-
  Latenz pro Target; keine Single-Queue-Filter-Schleife
  (die im Worst-Case ueber n-1 Fremd-Messages skippen
  muesste). Memory-Overhead ist proportional zu
  `target_count`, also gleich zu `device_count` —
  vernachlaessigbar.
- **Lazy-Init im Callback:** Vermeidet die Pflicht, alle
  Targets in `start()` aufzulisten; passt zu Decision 4a
  (Topics werden im Scenario deklariert, aber zur Laufzeit
  koennen weitere unsubscribed-Topics auftauchen — bei
  Subscribe `#`-Wildcards).
- **`queue.Queue` (nicht `collections.deque`):** Queue ist
  thread-safe ohne externen Lock; deque braucht expliziten
  `threading.Lock`. paho-mqtt-Loop-Thread → TickLoop-Thread
  ist genau **ein** Producer/Consumer-Paar; Queue ist die
  natuerliche Wahl.
- **`get_nowait` statt `get(timeout=0)`:** Konsistent mit
  Decision-3-`read()`-Kontrakt aus ADR 0030 §2.1 („non-
  blocking, returns `None` wenn nichts da"). `get(timeout=0)`
  haette dieselbe Semantik aber zusaetzlichen Funktions-
  Overhead.
- **Per-Topic-Decode im Callback (nicht in `read`):** Spart
  Latenz im Sync-`read()`-Pfad — die Decode-Arbeit
  passiert im paho-Loop-Thread. Pattern analog OTel-SDK
  `BatchSpanProcessor`-Worker-Thread.

**Konsequenz:** `MqttDeviceProtocolPort.__init__` erhaelt
`config: MqttProtocolPortConfig` (Decision 4a) +
`client_factory: Callable[[], paho.mqtt.client.Client] |
None = None` (Default `None` ruft `paho.mqtt.client.Client()`
direkt — Test-Override-Hook fuer mocked Client). Innere
Felder: `_queues: dict[str, queue.Queue]`, `_topic_index:
dict[str, str]` (Topic → device_id Reverse-Index, gebaut
in `start()` aus `config.topics`).

**Exception-Behandlung im Callback:** `on_message`-
Exceptions (z. B. `decode_telemetry`-Fehlschlag) werden in
der Welle-2-Variante **geschluckt + geloggt** (TBD: gegen
`LogPort` aus ADR 0024 §2.2 — wenn `log_port` per Kwarg
uebergeben wurde) und **nicht** an den Loop-Thread
propagiert (paho-Loop-Thread wuerde sonst sterben und
Reconnect ausloesen). Welle 6 schaerft den Fehler-Pfad
(strukturierte Error-Metriken + Dead-Letter-Topic-Option).

---

## 3. Alternativen

**A1 (verworfen) — Separate `mqtt_profiles`-Top-Level-
Section:** wuerde Decision 4a auf eine eigene Schluessel-
Section verlagern (`mqtt_profiles.<profile_name>`) und
`protocol_ports`-Eintraege mit `profile: <name>` referenzieren
lassen. Verworfen wegen YAGNI: Welle-2-Scenarios haben ≤ 10
Devices; Profile-Reuse-Bedarf ist hypothetisch. Wenn er
konkret wird, schaerft Welle 6 per ADR-0011-Pattern.

**A2 (verworfen) — `orjson` als Default-Codec:** wuerde
Trigger 004 (`canonical encoder` Alternative) praeventiv
aktivieren und ggue. `canonical_json` ~5-10x Throughput
gewinnen. Verworfen, weil (a) Test-Smoke keinen
messbaren Perf-Druck zeigt, (b) Determinismus-Bruch
gegenueber Snapshot-/Replay-Pfaden (die `canonical_json`
zwingend nutzen), (c) `orjson` haette zusaetzliche
Library-Dependency ohne Welle-2-Beleg. Re-Eval-Pfad in
§2.2 dokumentiert.

**A3 (verworfen) — `QoS 1` als Default fuer Telemetry:**
wuerde at-least-once-Delivery garantieren, aber Latenz-
Overhead pro Publish (PUBACK-Roundtrip). Bei
hoher Telemetry-Frequenz (> 100 Hz) bricht QoS 1 den
paho-mqtt-Loop unter Last. Verworfen — QoS-Override pro
Topic (Decision 4c-Konsequenz) erlaubt selektiven Upgrade,
wo noetig.

**A4 (verworfen) — Single-`queue.Queue` mit Target-Tag:**
wuerde Per-Target-State sparen, aber `read(target)`
braeuchte eine Filter-Schleife (skip fremde Targets) mit
Worst-Case-O(n) Latenz und Probleme beim Fremd-Target-
Aufstauen (Messages anderer Targets blockieren die Queue,
wenn niemand sie liest). Verworfen.

**A5 (verworfen) — `collections.deque` + `threading.Lock`
statt `queue.Queue`:** deque hat schnellere Append/Pop-
Performance, aber `queue.Queue` ist genau fuer Producer/
Consumer-Pattern ausgelegt (interne Locking + Semaphore-
Logik). Performance-Gewinn waere im Welle-2-Smoke
unsichtbar; Bug-Risiko durch manuelles Locking steigt.

**A6 (verworfen) — Eigene paho-mqtt-Loop-Thread-Variante
(`loop_forever()` in eigenem Thread):** wuerde
`loop_start()`/`loop_stop()`-Lifecycle umgehen und einen
eigenen `threading.Thread`-Lifecycle bauen. Verworfen, weil
paho-mqtt's `loop_start()` bereits die Standard-Pattern-
Variante ist (interne Thread-Verwaltung, Reconnect-Logik
inklusive). Eigenbau erhoeht Code-Komplexitaet ohne
Mehrwert.

**A7 (verworfen) — Exception aus Callback an Caller
propagieren:** wuerde Fehlschlaege bei `decode_telemetry`
sichtbar machen, aber paho-Loop-Thread sterben lassen und
Reconnect ausloesen (paho-mqtt-Verhalten bei Callback-
Exception). Verworfen — Welle 2 wuenscht stabile Smoke-
Tests; Fehler werden geschluckt+geloggt, Welle 6 fuegt
strukturierte Metriken hinzu.

**A8 (verworfen) — Sync-Connect in `start()` (blockierend
bis Mosquitto verbunden):** wuerde Verbindungs-Status am
Welle-Start sicherstellen. Verworfen, weil (a) paho-mqtt-
`connect()` ist asynchron designed (Connect-ACK landet im
`on_connect`-Callback), (b) sync-Wrap waere `connect()` +
Polling-Schleife — anti-Pattern, das paho-mqtt-Doku
explizit ablehnt, (c) Lazy-Connect-Pattern in Welle-2-
Adapter erlaubt `start()` ohne sofortigen Broker-
Verbindungs-Erfolg (Reconnect-Backoff aus paho-mqtt-
SDK uebernimmt).

---

## 4. Konsequenzen

- **Welle-2-C2-Implementierungs-Pflicht** (`feat(welle-2):
  protocol_mqtt + Tests + Integration-Smoke + Compose-
  Edit`):
  - NEU `src/grid_gym/adapters/driven/protocol_mqtt/__init__.py`
    mit `MqttDeviceProtocolPort` als
    `DeviceProtocolPort`-Implementer (ADR 0030 §2.1).
  - NEU `src/grid_gym/adapters/driven/protocol_mqtt/_config.py`
    (`MqttProtocolPortConfig` + `MqttTopicConfig` frozen-
    dataclasses, Decision 4a-Schema).
  - NEU `src/grid_gym/adapters/driven/protocol_mqtt/_codec.py`
    (`encode_telemetry`/`encode_command` + Decode-
    Symmetrien, Decision 4b — falls AC-ADAPTER-LIGHTWEIGHT-
    Schwelle die Trennung erfordert; sonst inline in
    `__init__.py`).
  - **Modul-Docstring** mit Lastenheft-Z. 1161–1163-
    Pflicht: „Simulations-/Testadapter; keine produktive
    Anlagensteuerung". Cross-Cutting-Pflicht ist
    Adapter-spezifisch (Welle 6 prueft sweepartig fuer alle
    `protocol_*`-Module).
  - 4 Unit-Test-Module unter
    `tests/unit/adapters/driven/protocol_mqtt/`.
  - 1 Integration-Smoke unter
    `tests/integration/test_mqtt_compose_smoke.py`.
- **`tests/integration/compose.yml`-Erweiterung:**
  `mosquitto`-Service mit `eclipse-mosquitto:2.0.<patch>`-
  Image (Patch-Pin in C2). Healthcheck via
  `mosquitto_sub -t '$SYS/broker/uptime' -C 1`. Port 1883
  exponiert. Lizenz EPL-2.0/EDL-1.0 (redistributable;
  Welle-0-Decision-5-Note in
  [`done/M4-welle-0.md`](../planning/done-archive/M4-welle-0.md)
  §3 hat die Vorabklaerung dokumentiert).
- **`pyproject.toml`-Erweiterung:** `paho-mqtt>=2.0` in
  `[project] dependencies`. `paho`-Eintrag in den
  AC-PORTS-NO-FW- und AC-NO-FW-Forbidden-Listen ist
  Welle-0-vorbelegt — keine Aenderung an den
  `[[tool.importlinter.contracts]]`-Bloecken noetig.
- **`Dockerfile`-Erweiterung:** `CRITICAL_COV_TARGETS`-
  Default um `src/grid_gym/adapters/driven/protocol_mqtt`
  erweitert (Pattern analog `telemetry_otlp`-Eintrag aus
  M3-Welle-6-`c61ab0d`). `make gates` cache-frei gruen
  ohne `CRITICAL_COV_TARGETS`-Override.
- **`AC-ADAPTER-LIGHTWEIGHT` greift unveraendert**
  (`tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`). Welle 2 muss nur
  Smoke-Regression-Schutz pruefen — der Welle-1-§7-
  Folge-Pflicht-Planted-Violator-Property-Test bleibt
  Welle-6-Material (siehe
  [`../planning/done/M4-welle-1.md`](../planning/done-archive/M4-welle-1.md)
  §7 Folge-Mitigation; Welle-2-`M4-welle-2.md`
  §2-Anti-Scope hat den Verzicht normativ festgeschrieben).
- **Scenario-Loader bleibt MQTT-frei** ([`AC-HEXAGON-PURE`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)):
  `hexagon/core/scenario/loader.py` darf
  `MqttProtocolPortConfig` nicht direkt parsen. Stattdessen
  liefert das Adapter-Modul eine `parse_mqtt_config(yaml_block)
  -> MqttProtocolPortConfig`-Factory-Funktion, die der
  Loader generisch ueber die ADR-0030-`protocol_ports`-
  Kwarg-Surface aufruft (Plugin-Pattern analog
  `_AGENT_PLUGIN_FACTORIES` aus ADR 0027 §2.3 — Welle 2
  loest die konkrete Verkabelung; siehe Welle-2-C2-
  Verifikations-Pfad).
- **Caller-Scope-Lifecycle bleibt ADR-0030-Vertrag:**
  Caller wrappen `loop.start_protocol_ports()` /
  `loop.stop_protocol_ports()` in `try/finally` um die
  Tick-Schleife (ADR 0030 §2.2 Pattern). MQTT-Adapter
  haengt sich in dieses Pattern ein; **keine** Aenderung
  an TickLoop.
- **Snapshot-Vertrag bleibt v2** (ADR 0030 §2.3):
  MQTT-Adapter ist stateless aus Replay-Sicht; Reconnect-
  State (subscribe-acks, in-flight publish-acks) ist
  volatile. Reversibilitaet via ADR-0015-Pattern; Welle 6
  prueft, ob Welle-2-Erfahrung eine Schaerfung verlangt.
- **OTel-Span-Wrap der Adapter-Calls:** ADR 0031 wrappt
  Adapter-Calls **nicht** mit OTel-Spans. Welle 6 (Cross-
  Adapter-Hardening) ist der Zeitpunkt fuer den
  `TracePort`-Wrap (ADR 0024 §2.4 als Bezug).
- **Welle-3-Implementer-Auflage (Modbus-Adapter):** Welle
  3 darf Decision-4a-Inline-Pattern reusen oder per
  Folge-ADR per ADR-0011-Pattern schaerfen, falls Register-
  Schema andere Anforderungen hat (z. B. Byte-Reihenfolge
  als Per-Register-Optional). Decision 4b/4c/4d sind
  MQTT-spezifisch — Welle 3 entscheidet pro Decision neu.
- **Welle-4-Implementer-Auflage (OPC-UA-Adapter):** Welle
  4 traegt erstmals einen rein-async-Stack (`asyncua`).
  Decision 4d (Callback-Marshal) ist dort komplexer:
  eigener `asyncio.Loop` in einem dedizierten Thread +
  `run_coroutine_threadsafe` als Marshal-Brücke. ADR 0031
  §2.4 ist **nicht** direkt reusable; Welle 4 schreibt
  eigene Marshal-Decision.

---

## 5. Status-Pfad

- **Proposed** — 2026-05-30 (M4-Welle-2-C1 `4e102b8`).
  Initial-Entwurf.
- **Provisional** — 2026-05-30 (M4-Welle-2-C3, dieser
  Commit). M4-Welle-2-C2-Merge `f33bb4e` (feat) lieferte
  `src/grid_gym/adapters/driven/protocol_mqtt/`-Modul
  (7 Dateien: `__init__.py` + `_config.py` + `_codec.py` +
  `_topic_resolver.py` + `_port.py` + `_errors.py` +
  `error_translation.py`), 4 Unit-Test-Module (50 neue
  Tests: 1161 → 1211), Integration-Smoke gegen
  Mosquitto-Sibling (`tests/integration/test_mqtt_compose_smoke.py`,
  21 → 22 Integration-Tests), `compose.yml`-Kommentar-Sync,
  `pyproject.toml`-Erweiterung (`paho-mqtt>=2.0`),
  `uv.lock`-Refresh (`paho-mqtt v2.1.0`),
  `Dockerfile`-`CRITICAL_COV_TARGETS`-Erweiterung um
  `adapters/driven/protocol_mqtt`. `make arch-check` 19/19
  KEPT (7 lint-imports + 12 `tools/arch_check.py`);
  `make gates` cache-frei gruen ohne Override (alle 9
  A-1-Gates).
- **Accepted** — 2026-06-01 mit M4-Welle-7-C1 (dieser
  Commit, M4-Closure-Welle; analog ADR 0022..0027 + 0030).
  Voraussetzung erfuellt: Welle 3 (Modbus, ADR 0032),
  Welle 4 (OPC-UA, ADR 0033), Welle 5a (DNP3, ADR 0034)
  und Welle 5b (IEC-61850, ADR 0035) haben ihre Profile
  per ADR-0011-Pattern (Schaerfung-ohne-Supersede)
  dokumentiert; keine 4a-Pattern-Rueckwirkungs-Schaerfung.
