# Welle 2 — M4 MQTT-Adapter

**Status:** Done — geschlossen 2026-05-30 mit M4-Welle-2-C3
(`docs(plan|adr)` Doc-Sync, dieser Commit). Eroeffnet
2026-05-30 nach M4-Welle-1-Closure (`5f03bbf` C3 + `82f947c`
Linter-Folge + `81b5cba` Self-Close-Move + `f1f9db1`
Pre-C0-Sync + `b7bf40d` Review-Folge + `51b8694`
`M4-protocol-adapters.md` §2.1-Stale-Notiz-Sync). Welle 2 war
die **zweite Code-Welle** in M4 und hat den **ersten
konkreten Adapter** auf der `DeviceProtocolPort`-Surface
(`GG-AR-PORT-DRN-007`) geliefert: MQTT ueber `paho-mqtt 2.x`
mit Mosquitto-Sibling-Integration-Smoke. Welle 2 hat das
Pattern fuer Decision 4 (Topic/Register/Node-Profil-
Deklaration aus
[`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
Decision 4) gesetzt und die Mosquitto-Sibling-Test-Praezedenz
fuer Welle 3 (Modbus) und Welle 4 (OPC-UA) etabliert.

**Liefer-Hashes:**

- C0 `3b633f6` — `docs(plan): M4-welle-2 Slice-Doc (M4 Welle-2 Beginn)`.
- C1 `4e102b8` — `docs(adr): ADR 0031 Proposed — MQTT-Adapter-Profile (M4 Welle 2)`.
- C2 `f33bb4e` — `feat(welle-2): protocol_mqtt + Tests + Integration-Smoke + Compose-Edit`.
- C3 (dieser Commit) — `docs(plan|adr): M4-Welle-2-C3 — Status/DoD-Sync + ADR 0031 -> Provisional + Top-Level-Doku-Sync`.

**DoD-Verifikation (Welle-Schluss, Stand `f33bb4e` C2 +
dieser Commit):**

- `make test-unit`: **1211 Tests gruen** (Pre-Welle-2-Stand
  1161 → Welle-2-Endstand 1211 = +50 Unit-Tests; davon 11
  Codec-Roundtrip
  (`tests/unit/adapters/driven/protocol_mqtt/test_mqtt_codec.py`),
  16 Topic-Resolver + Config-Validation
  (`test_mqtt_topic_resolver.py`), 17 Lifecycle + Read/Write
  mit mocked paho-Client (`test_mqtt_protocol_port.py`) und
  6 Callback-Marshal (`test_mqtt_callback_marshal.py`:
  Per-Target-Queue-Lazy-Init, FIFO-Drain, Decode-Fehler-
  Swallowing)).
- `make test-integration`: **22 Tests gruen** (Pre-Welle-2-
  Stand 21 → Welle-2-Endstand 22 = +1 MQTT-Compose-Smoke
  gegen Mosquitto-Sibling via testcontainers; End-to-End-
  Pub/Sub-Roundtrip + Bounded-Poll-Loop).
- `make arch-check`: **19/19 Contracts KEPT** (7
  lint-imports + 12 `tools/arch_check.py`);
  `AC-ADAPTER-LIGHTWEIGHT` erfasst `protocol_mqtt` ohne
  Filter-Edit (Pfad-Filter `bucket.startswith("protocol_")`
  greift; McCabe-Komplexitaets-Schwelle in
  `_config._validate_topics` per Refactor in 3 modul-lokale
  Helpers eingehalten).
- `make gates`: **alle 9 A-1-Gates gruen** ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste um
  `src/grid_gym/adapters/driven/protocol_mqtt` erweitert).
- `make fullbuild`: `image-audit` weiter rot aus
  **dokumentiertem** Pre-existing krb5-CVE-Grund
  (`CVE-2026-40356`-Drift seit M3-Welle-7-`c61ab0d`,
  **nicht durch M4-Welle-2-Code verursacht**); Compose-Smoke
  selbst (mit neuem Mosquitto-Sibling) gruen.
- ADR 0031: `Proposed → Provisional` (Decisions 4a/4b/4c/4d
  alle **final**; Status-Pfad in
  [`../../adr/0031-mqtt-adapter-profile.md`](../../adr/0031-mqtt-adapter-profile.md) §5
  mit Hashes belegt).

Kanonische Slice-Spezifikation:
[`M4-protocol-adapters.md §3 Welle 2`](M4-protocol-adapters.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht Ersatz.

**Spec-Reife:** Inhaltlich final. Decisions aus
[`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
Decision 4 (Profile-Deklaration; MQTT setzt das Pattern)
werden in C1 (ADR 0031 Proposed) konkret gewaehlt; C2
(feat) implementiert die gewaehlte Variante.

---

## 1. Context

M4-Welle-1 hat die `DeviceProtocolPort`-Surface produktiv
geliefert (ADR 0030 `Provisional`, `81b5cba` Self-Close-Move
+ `f1f9db1` Pre-C0-Sync):

- Driven-Port `DeviceProtocolPort` mit `start`/`stop`/`read`
  /`write` + `*Error`-Subsystem
  ([`../../../../src/grid_gym/hexagon/ports/driven/device_protocol.py`](../../../../src/grid_gym/hexagon/ports/driven/device_protocol.py)).
- `TickLoop`-Erweiterung mit
  `protocol_ports`-Konstruktor-Kwarg +
  `start_protocol_ports()` / `stop_protocol_ports()`
  (FIFO/LIFO/idempotent + Best-Effort-Partial-Cleanup mit
  `__context__`-Chain).
- Scenario-Loader-Builder-Symmetrie (+8 Zeilen):
  `protocol_ports`-Feld in `TickLoopWiring` + Threading
  durch `build_tick_loop`.
- ADR 0030 hat Decisions 2 (Sync), 3 (Caller-Scope-Lifecycle),
  7 (Stateless-Replay) **final** beschlossen und Decision 1
  (DNP3/IEC) **provisorisch** als Verzicht-Default
  vorgemerkt.

Welle 2 ist der **erste konkrete Implementer** auf dieser
Surface:

- NEU `src/grid_gym/adapters/driven/protocol_mqtt/`-Modul
  mit `paho-mqtt`-Wrapper als `DeviceProtocolPort`-
  Implementer (`GG-MQTT-001`).
- NEU ADR 0031 (MQTT-Adapter-Profile) als Surface-relevanter
  Adapter-ADR. Decisions aus
  [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
  Decision 4 (Topic/Register/Node-Profil-Deklaration):
  MQTT setzt das Pattern (inline-YAML vs. separat vs.
  hybrid; Welle 3 Modbus + Welle 4 OPC-UA folgen dem
  Pattern).
- NEU Integration-Smoke via testcontainers
  (`eclipse-mosquitto:2`-Sibling), Pattern analog
  M3-Welle-6c-OTLP-Compose-Smoke
  ([`../done/M3-welle-6.md`](../done/M3-welle-6.md);
  Code-Pfad
  [`../../../../tests/integration/test_otlp_compose_smoke.py`](../../../../tests/integration/test_otlp_compose_smoke.py)).
- EDIT `tests/integration/compose.yml`-Erweiterung um
  `mosquitto`-Sibling-Service (Healthcheck + Port-Binding).
- EDIT `pyproject.toml`: `paho-mqtt`-Dependency
  (`paho` ist in den AC-PORTS-NO-FW/AC-NO-FW-
  Forbidden-Listen bereits vorgemerkt — Welle 2 zieht den
  produktiven Floor in `[project] dependencies`).
- EDIT `Dockerfile`: `CRITICAL_COV_TARGETS`-Default um
  `src/grid_gym/adapters/driven/protocol_mqtt` erweitert
  (Pattern analog `telemetry_otlp`-Eintrag aus
  M3-Welle-6).

Welle 2 liefert **keine** Modbus-/OPC-UA-/DNP3-/IEC-Adapter
(diese kommen ab Welle 3) und **kein** OTel-Span-Wrap der
Adapter-Calls (Welle 6).

---

## 2. Scope

**In Scope:**

1. NEU `docs/plan/adr/0031-mqtt-adapter-profile.md` in C1
   als `Proposed`. Entscheidungen:
   - **Decision 4a (Topic-Schema, final)**: Topic-Profil-
     Deklaration im Scenario-YAML — entweder **inline** im
     `protocol_ports`-Block (Default-Vorschlag, einfacher
     Read-Pfad fuer kleine Topic-Mengen), **separat** als
     eigene Top-Level-Section (skaliert besser auf > 100
     Topics, vermeidet inline-YAML-Wachstum) oder **hybrid**
     (Default-Profile separat, Per-Scenario-Override inline).
     ADR 0031 setzt die Wahl scharf; Pattern-Praezedenz ist
     `load_events`/`load_profiles` aus ADR 0021 §2.4
     (Welle-5b-`grid_model`-Block).
   - **Decision 4b (Payload-Codec, final)**: Payload-
     Encoding fuer Telemetry/Command — `canonical_json`
     (M2-Welle-0a-Stand, deterministisch + sortiert) als
     Default-Wahl; Trigger 004 (`canonical encoder`
     Alternative `orjson`/`msgspec`) bleibt in `open/` und
     wird in Welle 6 (Cross-Adapter-Hardening) re-evaluiert,
     wenn MQTT-Publish-Throughput-Druck messbar ist.
   - **Decision 4c (QoS-Default, final)**: Publish-QoS
     pro Richtung — `QoS 0` (fire-and-forget) fuer
     Telemetry-Publishes (high-volume, Verlust-tolerant),
     `QoS 1` (at-least-once) fuer Command-Publishes
     (Steuerungs-Befehle muessen ankommen). Pattern-
     Praezedenz: paho-mqtt-Doku „QoS Level 1 for command
     channels". Override-Pfad ueber das Topic-Profile.
   - **Decision 4d (Threading-Marshal, final)**: paho-mqtt-
     Callbacks (`on_message`, `on_connect`,
     `on_disconnect`) feuern aus dem `loop_start()`-
     internen Thread. ADR 0031 schreibt den
     **Callback->Sync-Port-Marshal** via thread-sichere
     `queue.Queue` normativ fest: `read(target)` zieht
     aus der Queue (nicht-blockierend mit Default-
     Timeout); `write(target, command)` ruft paho-mqtt
     `publish()` direkt, weil das thread-safe ist (siehe
     paho-mqtt-Doku „client.publish() is thread-safe").
     Pattern wurde in ADR 0030 §2.1-Begruendung schon
     vorbelegt — ADR 0031 macht es konkret.
2. NEU
   `src/grid_gym/adapters/driven/protocol_mqtt/__init__.py`:
   `MqttDeviceProtocolPort`-Klasse als
   `DeviceProtocolPort`-Implementer.
   - `start()`: Adapter-internes `paho.mqtt.client.Client()`-
     Setup + `connect()` + `subscribe(...)` fuer alle
     im Profile deklarierten Subscribe-Topics +
     `loop_start()`.
   - `stop()`: `loop_stop()` + `disconnect()`; idempotent
     bei Doppel-Stop.
   - `read(target) -> TelemetryPoint | None`: zieht
     nicht-blockierend aus der Adapter-internen
     `queue.Queue` (Default-Timeout 0 ms; konfigurierbar
     via Topic-Profile).
   - `write(target, command) -> None`: serialisiert
     `command` ueber `canonical_json` + `client.publish(
     topic=resolve_topic(target), payload=bytes,
     qos=resolve_qos(target))`.
   - Modul-Docstring mit Lastenheft-Z. 1161–1163-Pflicht:
     **„Simulations-/Testadapter; keine produktive
     Anlagensteuerung"**.
3. NEU
   `src/grid_gym/adapters/driven/protocol_mqtt/_codec.py`
   (optional, falls Codec-Logik > 30 Statements wird —
   sonst inline in `__init__.py` halten gemaess
   AC-ADAPTER-LIGHTWEIGHT). Konkrete Trennung wird in C2
   nach Code-Komplexitaets-Messung entschieden.
4. Unit-Tests unter
   `tests/unit/adapters/driven/protocol_mqtt/`:
   - `test_mqtt_protocol_port.py`: Lifecycle (start/stop +
     Idempotenz), Read/Write-Vertragsverhalten gegen
     mocked `paho.mqtt.client.Client`.
   - `test_mqtt_codec.py`: Payload-Codec (Telemetry ->
     `canonical_json`, Command -> `canonical_json`;
     Roundtrip-Tests).
   - `test_mqtt_topic_resolver.py`: Topic-Schema-Mapping
     (Device-ID -> Topic) gegen Decision-4a-Profile.
   - `test_mqtt_callback_marshal.py`: Callback aus paho-
     internem Thread + Queue-Drain via `read()` (Property:
     n Callbacks -> n Queue-Eintraege; Order-Pinning).
5. NEU `tests/integration/test_mqtt_compose_smoke.py`:
   - End-to-End-Smoke: `TickLoop` mit `MqttDeviceProtocolPort`
     als `protocol_ports`-Eintrag; Mosquitto-Sibling
     spawnt via testcontainers (`eclipse-mosquitto:2`).
   - Publish-Pfad: TickLoop ruft `port.write(target,
     command)`; Test-Subscriber prueft, dass die Message
     im Mosquitto-Broker landet (subscribe ueber
     `paho-mqtt`-Test-Client).
   - Subscribe-Pfad: Test-Publisher schickt Telemetry-
     Message; `port.read(target)` zieht sie nach dem
     naechsten Tick aus der Queue.
   - Pattern analog
     [`tests/integration/test_otlp_compose_smoke.py`](../../../../tests/integration/test_otlp_compose_smoke.py)
     (testcontainers + `wait_for_container` + assertions
     auf Sibling-State).
6. EDIT `tests/integration/compose.yml`: neuer
   `mosquitto`-Sibling-Service mit
   `eclipse-mosquitto:2`-Image, Healthcheck via
   `mosquitto_sub -t '$$SYS/broker/uptime' -C 1`, Port
   `1883` exponiert. Lizenz-Pflichtcheck **vor** Image-
   Pin: `eclipse-mosquitto:2` ist EPL-2.0/EDL-1.0
   (Eclipse-Distribution; free + redistributable;
   siehe Welle-2-Decision-5-Note in
   [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
   Decision 5).
7. EDIT `pyproject.toml`: `paho-mqtt`-Dependency in
   `[project] dependencies` mit Floor `>=2.0` (aktueller
   PyPI-Stand-Verifikation in C2). `paho`-Import-Linter-
   Eintrag ist bereits in den AC-PORTS-NO-FW/AC-NO-FW-
   Forbidden-Listen (Welle-0-Vorbelegung); keine
   Aenderung an den `[[tool.importlinter.contracts]]`-
   Bloecken noetig.
8. EDIT `Dockerfile`: `CRITICAL_COV_TARGETS`-Default um
   `src/grid_gym/adapters/driven/protocol_mqtt` erweitert
   (Pattern analog `src/grid_gym/adapters/driven/
   telemetry_otlp`-Eintrag aus M3-Welle-6-`c61ab0d`).
9. C3-Doc-Sync zieht `M4-welle-2.md`-Status auf `Done` und
   schaerft ADR 0031 von `Proposed` auf `Provisional`.
   (Endgueltige Akzeptanz erst mit M4-Welle-7-Closure.)
10. `make arch-check` weiter `19/19 Contracts KEPT` —
    `AC-ADAPTER-LIGHTWEIGHT` greift fuer `protocol_mqtt`
    via `tools/arch_check.py:1089`
    `bucket.startswith("protocol_")`. Welle-1-Smoke-
    Regression-Schutz bleibt aktiv; Welle-2 prueft, dass
    der Filter den neuen `protocol_mqtt/`-Pfad ohne
    Code-Aenderung erfasst.

**Anti-Scope:**

- **Keine Modbus-/OPC-UA-/DNP3-/IEC-Adapter** unter
  `src/grid_gym/adapters/driven/protocol_*/`. Diese kommen
  ab Welle 3 (Modbus), Welle 4 (OPC-UA), Welle 5
  (DNP3/IEC-Disposition).
- **Kein OTel-Span-Wrap** der MQTT-Adapter-Calls. Span-
  Wrap-Pattern fuer `protocol_*`-Adapter ist Welle-6-
  Material (Cross-Adapter-Hardening; ADR 0024
  `TracePort` als Bezug).
- **Kein RandomPort-Determinismus** fuer Topic-IDs oder
  Client-IDs. paho-mqtt-Default-Client-ID-Generierung
  reicht fuer Welle 2; Welle 6 schaerft ggf. nach.
- **Keine Scenario-Schema-Erweiterung jenseits des
  Decision-4a-Pattern**. Welle 2 fuegt ggf. einen
  `protocol_ports`-Top-Level-Block hinzu, aber **keine**
  generischen Topic-/Register-/Node-Schemas, die ueber
  MQTT hinausgehen — Welle 3/4 erweitern das Schema bei
  Bedarf pro Adapter.
- **Keine Bewegung der 17 Open-Trigger**. Insbesondere
  bleibt Trigger 004 (`canonical encoder` Alternative)
  in `open/` — die Re-Eval-Notiz wird in C3 ergaenzt
  (Stand: kein messbarer Perf-Druck am MQTT-Publish-
  Throughput in Welle-2-Stand).
- **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md`.
  Welle 2 liefert genau **einen** der 7 DoD-Items
  (`GG-MQTT-001`); der DoD-Sweep folgt mit Welle 6.
- **Kein `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-
  Property-Test**. Die in M4-welle-1 §7 als Folge-Pflicht
  markierte Welle-2-Mitigation wird **bewusst nach
  Welle 6** geschoben (Cross-Adapter-Hardening) — Welle 2
  fuegt nur Smoke-Regression-Schutz hinzu, weil der
  Welle-2-Scope (Adapter + ADR + Smoke + Compose) bereits
  auf der Sub-Slicing-Schwelle liegt.

---

## 3. Architektur-Entscheidungen

Welle 2 bringt **eine** neue ADR: **ADR 0031**
(`docs/plan/adr/0031-mqtt-adapter-profile.md`),
Status-Pfad `Proposed → Provisional → Accepted`:

- **`Proposed`** mit C1 (dieser Welle): Initial-Entwurf
  mit Decision-4a/b/c/d-Vorschlaegen + Begruendung +
  Alternativen + Konsequenzen. Pattern analog ADR 0030
  (M4-Welle-1-C1).
- **`Provisional`** mit C2-Merge (feat-Commit, der die
  Decision-Variante implementiert + Tests gruen +
  Integration-Smoke gruen).
- **`Accepted`** mit M4-Welle-7-Closure (analog ADR
  0022..0027 + 0030).

**Bezug:**

- [`spec/architecture.md §7`](../../../../spec/architecture.md)
  Z. 249 (`GG-AR-PORT-DRN-007` Tabelle — Surface bleibt
  ADR-0030-Vertrag) +
  [`§8.2`](../../../../spec/architecture.md) Z. 510–512
  (Adapter-Interfaces-Driven-Beschreibung).
- [`spec/lastenheft.md §16`](../../../../spec/lastenheft.md)
  Z. 1120–1133 (`GG-MQTT-001`: SOLLTE-Cluster fuer
  Topic-Schema + Payload-Format + QoS + Pub/Sub-Richtung +
  Adapter-Smoke).
- [`../done/M4-welle-0.md`](../done/M4-welle-0.md) §3
  Decision-Liste (Item 4 Profile-Deklaration + Item 5
  Test-Sibling-Container + Item 6
  `AC-ADAPTER-LIGHTWEIGHT`-Pfad-Filter).
- [`M4-protocol-adapters.md`](M4-protocol-adapters.md) §3
  Welle 2 (kanonische Slice-Spezifikation).
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  §2.1 (Sync-Vertrag + paho-mqtt-Halb-Sync-Begruendung;
  Welle-2-Implementer-Auflage in §4) + §2.2 (Caller-
  Scope-Lifecycle — Welle 2 muss MQTT-Adapter im
  Caller-`try/finally` wrappen; keine Aenderung an
  TickLoop noetig).
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  als Pattern-Anker: ADR 0031 schaerft ADR 0030 §2.1
  ohne Supersede (Adapter-Profil ist Adapter-spezifisch,
  ADR-0030-Surface bleibt invariant).
- M3-Welle-6 als Test-Pattern-Anker:
  [`../done/M3-welle-6.md`](../done/M3-welle-6.md) und
  [`../../../../tests/integration/test_otlp_compose_smoke.py`](../../../../tests/integration/test_otlp_compose_smoke.py)
  (testcontainers-Sibling-Smoke + Compose-Erweiterung +
  `wait_for_container`-Pattern).

**Vorbelegungs-Liste fuer M4-Folge-ADRs** (kommen ab
Welle 3; werden nicht in Welle 2 angelegt):

- Welle 3: ADR fuer Modbus-TCP-Adapter-Profil (Decision
  4a-Analog: Register-Schema; Decision 4d-Analog:
  pymodbus-sync-Client fuegt sich direkt in Sync-Port
  ein, kein Marshal-Pattern noetig).
- Welle 4: ADR fuer OPC-UA-Adapter-Profil (Decision
  4a-Analog: Node-ID-Schema; Decision 4d-Analog:
  asyncua + asyncio-Loop-in-eigenem-Thread —
  Marshal-Pattern komplexer als MQTT).
- Welle 5: optional ADR fuer DNP3/IEC-Spike (oder
  Anhang-Verzicht-Notiz zu ADR 0030 §6).

---

## 4. Liefer-Reihenfolge (4 Commits)

### C0 — `docs(plan)`: M4-welle-2 Slice-Doc (Welle-Beginn) — **Done `3b633f6`**

- Dieses Dokument als Welle-Start-Marker. Status:
  `In Progress` → (in C3) `Done`.
- Kein README-Sync noetig: `in-progress/README.md` zeigt
  bereits nach M4-Welle-2-Pre-C0-Sync `f1f9db1` „Naechster
  aktiver Schritt: M4-Welle-2 (MQTT-Adapter …)". Welle-2-
  Doc-Eintrag in `in-progress/README.md` kommt **nicht**
  als eigener Bestand-Tabellen-Zeile (analog
  M3-Welle-1..6 + M4-Welle-1; Welle-N-Docs sind Tracking,
  nicht Roadmap-Bestand).

### C1 — `docs(adr)`: ADR 0031 Proposed — MQTT-Adapter-Profile — **Done `4e102b8`**

- NEU `docs/plan/adr/0031-mqtt-adapter-profile.md` als
  `Proposed`. Inhalts-Skizze:
  - §1 Kontext (`GG-MQTT-001`, ADR-0030-Surface-Bezug,
    paho-mqtt-Halb-Sync-Begruendung aus ADR 0030 §2.1).
  - §2 Entscheidung mit Sub-Sections:
    - §2.1 Decision 4a (Topic-Schema-Deklaration) +
      Konsequenzen.
    - §2.2 Decision 4b (Payload-Codec) + Konsequenzen
      (Trigger 004 Re-Eval-Hinweis).
    - §2.3 Decision 4c (QoS-Default) + Konsequenzen.
    - §2.4 Decision 4d (Callback->Sync-Marshal) +
      Konsequenzen.
  - §3 Alternativen (jeweils 1–2 Varianten je Decision).
  - §4 Konsequenzen (`AC-ADAPTER-LIGHTWEIGHT`-Pflicht,
    Welle-3/4-Implementer-Auflagen, Welle-6-Span-Wrap-
    Forward-Pointer).
  - §5 Status-Pfad (`Proposed → Provisional → Accepted`).
- Kein Code-Pfad-Touch.
- Pattern analog M4-Welle-1-C1 `b840e7a` (ADR 0030
  Proposed).

### C2 — `feat(welle-2)`: protocol_mqtt + Tests + Integration-Smoke + Compose-Edit — **Done `f33bb4e`**

- NEU `src/grid_gym/adapters/driven/protocol_mqtt/__init__.py`
  (+ optional `_codec.py`, falls noetig — AC-ADAPTER-
  LIGHTWEIGHT-Schwellen-Messung in C2 entscheidet).
- NEU 4 Unit-Test-Module unter
  `tests/unit/adapters/driven/protocol_mqtt/`.
- NEU `tests/integration/test_mqtt_compose_smoke.py`.
- EDIT `tests/integration/compose.yml` (Mosquitto-Sibling
  + Healthcheck).
- EDIT `pyproject.toml` (`paho-mqtt>=2.0` in `[project]
  dependencies`).
- EDIT `Dockerfile` (`CRITICAL_COV_TARGETS`-Default um
  `adapters/driven/protocol_mqtt` erweitert).
- `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste muss um
  `protocol_mqtt` erweitert sein, sonst Override-Pflicht).
- `make test-integration` gruen mit MQTT-Smoke
  (Mosquitto-Sibling).
- `make arch-check` weiter `19/19 Contracts KEPT`:
  `AC-ADAPTER-LIGHTWEIGHT` greift fuer `protocol_mqtt`
  ohne Code-Aenderung.

### C3 — `docs(plan|adr)`: Welle-2 Status/DoD-Sync + ADR-Schaerfung — **Done (dieser Commit)**

- ADR 0031 `Proposed → Provisional` mit C2-Merge-Beleg.
- `M4-welle-2.md`-Status `In Progress → Done` mit
  C0/C1/C2-Hashes + DoD-Verifikation-Block + DoD-
  Checkliste (Pattern analog M4-welle-1.md §9).
- `M4-protocol-adapters.md §3 Welle 2`: Done-Status mit
  Commit-Belegen; Decisions-Vorbelegung-Liste in C3
  durchgehakt.
- README.md / README.de.md / roadmap.md / spec/
  architecture.md / adr/README.md: M4-Status-Sync analog
  M4-Welle-1-Review-Folge `b7bf40d` — Welle 2 `Done`,
  ADR 0031 `Provisional`, „Naechster aktiver Schritt:
  M4-Welle-3 (Modbus-Adapter)".
- done/README.md: M4-welle-2.md-Bestand-Zeile (analog
  M4-welle-1.md-Zeile; mit Pre-C0-Sync `f1f9db1`-
  Erbschafts-Hinweis).
- Trigger-004-Re-Eval-Notiz: keine Aktivierung in
  Welle 2, weil kein messbarer Perf-Druck am MQTT-
  Publish-Throughput; bleibt in `open/`. Welle 6
  haelt die finale Re-Eval-Notiz fest.

---

## 5. Critical Files

| Pfad                                                                          | Commit | Aktion                                          |
| ----------------------------------------------------------------------------- | ------ | ----------------------------------------------- |
| `docs/plan/planning/in-progress/M4-welle-2.md`                                | C0     | NEU (dieses Dokument)                           |
| `docs/plan/adr/0031-mqtt-adapter-profile.md`                                  | C1     | NEU (`Proposed`)                                |
| `docs/plan/adr/README.md`                                                     | C1     | EDIT (ADR-0031-Zeile)                           |
| `src/grid_gym/adapters/driven/protocol_mqtt/__init__.py`                      | C2     | NEU (`MqttDeviceProtocolPort` + Modul-Docstring)|
| `src/grid_gym/adapters/driven/protocol_mqtt/_codec.py`                        | C2     | NEU (optional, Codec-Helfer; nur falls AC-ADAPTER-LIGHTWEIGHT-Schwelle naht) |
| `tests/unit/adapters/driven/protocol_mqtt/__init__.py`                        | C2     | NEU                                             |
| `tests/unit/adapters/driven/protocol_mqtt/test_mqtt_protocol_port.py`         | C2     | NEU (Lifecycle + Read/Write gegen mocked Client)|
| `tests/unit/adapters/driven/protocol_mqtt/test_mqtt_codec.py`                 | C2     | NEU (Payload-Codec-Roundtrip)                   |
| `tests/unit/adapters/driven/protocol_mqtt/test_mqtt_topic_resolver.py`        | C2     | NEU (Decision-4a-Topic-Schema-Mapping)          |
| `tests/unit/adapters/driven/protocol_mqtt/test_mqtt_callback_marshal.py`      | C2     | NEU (Decision-4d-Queue-Marshal-Order)           |
| `tests/integration/test_mqtt_compose_smoke.py`                                | C2     | NEU (testcontainers + Mosquitto-Sibling-E2E)    |
| `tests/integration/compose.yml`                                               | C2     | EDIT (`mosquitto`-Sibling-Service + Healthcheck)|
| `pyproject.toml`                                                              | C2     | EDIT (`paho-mqtt>=2.0` in `[project] dependencies`) |
| `Dockerfile`                                                                  | C2     | EDIT (`CRITICAL_COV_TARGETS` + `protocol_mqtt`) |
| `docs/plan/adr/0031-mqtt-adapter-profile.md`                                  | C3     | EDIT (`Proposed → Provisional`)                 |
| `docs/plan/adr/README.md`                                                     | C3     | EDIT (Status-Spalte `Provisional`)              |
| `docs/plan/planning/in-progress/M4-welle-2.md`                                | C3     | EDIT (Status → Done; Hashes; DoD-Verifikation; §9 DoD-Checkliste) |
| `docs/plan/planning/in-progress/M4-protocol-adapters.md`                      | C3     | EDIT (§3 Welle 2 Done-Sync)                     |
| `README.md` + `README.de.md` + `docs/plan/planning/in-progress/roadmap.md` + `spec/architecture.md` | C3 | EDIT (M4-Status-Sync — Welle 2 `Done`, ADR 0031 `Provisional`, „Naechster aktiver Schritt: M4-Welle-3") |
| `docs/plan/planning/done/README.md`                                           | C3     | EDIT (M4-welle-2.md-Bestand-Zeile; analog M4-welle-1.md-Zeile) |

---

## 6. Verifikationspfad

1. **C0 (Slice-Doc)**: `make docs-check` cache-frei gruen
   (alle Link-Targets aufgeloest — insbesondere
   `../done/M4-welle-0.md`, `../done/M4-welle-1.md`,
   `M4-protocol-adapters.md`, `../../adr/0030-…md`,
   `../../adr/0011-…md`,
   `../../../../spec/{architecture,lastenheft}.md`,
   `../../../../tests/integration/test_otlp_compose_smoke.py`,
   `../../../../src/grid_gym/hexagon/ports/driven/device_protocol.py`).
2. **C1 (ADR Proposed)**: `make docs-check` gruen (neuer
   ADR-Pfad existiert, `docs/plan/adr/README.md` synced).
3. **C2 (feat)**:
   - `make test-unit` gruen (1161 → 1185+ Tests; ~24 neue
     Tests: 4 Lifecycle + 6 Codec + 6 Topic-Resolver +
     8 Callback-Marshal — feste Zahl in C3 belegt).
   - `make test-integration` gruen mit MQTT-Smoke
     (Mosquitto-Sibling spawnt + Pub/Sub-E2E gegen
     `MqttDeviceProtocolPort` + bisherige 21 Integration-
     Tests bleiben gruen — Total ≥ 22).
   - `make arch-check` gruen — `19/19 Contracts KEPT` (7
     lint-imports + 12 `tools/arch_check.py`);
     `AC-ADAPTER-LIGHTWEIGHT` erfasst `protocol_mqtt`
     ohne Filter-Aenderung.
   - `make gates` cache-frei gruen ohne
     `CRITICAL_COV_TARGETS`-Override (Default-Liste um
     `adapters/driven/protocol_mqtt` erweitert).
   - `make fullbuild`: Compose-Smoke selbst gruen
     (Mosquitto-Sibling + bisherige Postgres/OTel-
     Collector-Siblings); `image-audit` bleibt rot aus
     dem **dokumentierten** Pre-existing krb5-CVE-Grund
     (M3-Welle-7-`c61ab0d`-Drift; **nicht durch
     M4-Welle-2-Code verursacht** — siehe ADR 0030
     §0-Note + roadmap.md-Bottom-Section).
4. **C3 (Doc-Sync)**: `make docs-check` gruen mit
   geupdateten Status-Headern in 9 Docs (8 aus dem
   M4-Welle-1-Closure-Pattern + ADR 0031 selbst).

---

## 7. Risiken

- **paho-mqtt-Threading bricht Sync-Surface**: paho-mqtt-
  Callbacks feuern aus `loop_start()`-internem Thread.
  Wenn der Queue-Marshal (Decision 4d) falsch
  synchronisiert, kann `read(target)` veraltete Daten
  liefern oder Race-Conditions im Test triggern. *Mitigation*:
  C2-Tests pinnen die Callback-Marshal-Order
  (`test_mqtt_callback_marshal.py`); thread-sichere
  `queue.Queue` ist Standard-Pattern; Default-Timeout 0 ms
  bewahrt Sync-Port-Vertrag (kein Block).
- **Mosquitto-Sibling-Flakiness in Integration-Test**:
  testcontainers-Container-Start hat Latenz-Schwankungen;
  `paho-mqtt`-Connect-Backoff koennte den Test bei
  langsamem Start flaky machen. *Mitigation*: explizite
  Healthcheck-Wait-Loop im Test (Pattern analog
  `tools/wait_otel_collector.py` aus M3-Welle-6c);
  Mosquitto `mosquitto_sub -t '$SYS/broker/uptime' -C 1`
  als deterministischer Bereitschafts-Marker.
- **Decision-4a-Wahl bricht Welle 3 (Modbus)**: falls
  Topic-Schema-Pattern (inline vs. separat vs. hybrid) so
  spezifisch wird, dass es auf Register-Schema (Welle 3)
  oder Node-ID-Schema (Welle 4) nicht uebertragbar ist,
  muss ADR 0031 in Welle 3 per Folge-ADR geschaerft
  werden. *Mitigation*: ADR 0031 §2.1 dokumentiert die
  Wahl als `Provisional` (nach C2-Merge), nicht `Accepted`
  — der Schaerfungspfad ist offen, bis Welle 3 das Pattern
  real probiert. ADR 0031 §4 Forward-Pointer auf Welle
  3/4-Adapter-ADRs.
- **`AC-ADAPTER-LIGHTWEIGHT`-Schwelle bei Codec**: wenn
  Payload-Codec (Decision 4b) + Topic-Resolver (Decision
  4a) + Callback-Marshal (Decision 4d) zusammen
  AC-ADAPTER-LIGHTWEIGHT-Komplexitaets-Limits (Statements
  pro Funktion, McCabe-Komplexitaet) sprengen, muss in C2
  in Sub-Module gesplittet werden (`_codec.py`,
  `_topic_resolver.py`, `_marshal.py`). *Mitigation*: C2
  misst die Komplexitaet pro Funktion; Sub-Modul-Split ist
  vorgesehen und im §5 Critical Files schon vermerkt. **Der
  in M4-welle-1 §7 vorbelegte Planted-Violator-Property-
  Test bleibt bewusst auf Welle 6 verschoben** — die
  Welle-2-Sub-Slicing-Schwelle erlaubt ihn nicht zusaetzlich.
- **Sub-Slicing-Schwelle hart hit**: Welle 2 = 1 Adapter
  + 1 ADR + 1 Integration-Smoke = exakt die Sub-Slicing-
  Obergrenze (`M4-protocol-adapters.md` §3 Praeambel).
  Falls die paho-mqtt-Wrapper-Komplexitaet zusaetzliche
  Schritte triggert (z. B. eine zweite ADR fuer Codec-
  Decision oder ein zweiter Integration-Test fuer
  Reconnect-Verhalten), bricht die Schwelle. *Mitigation*:
  C2-Scope ist normativ in §2 In-Scope-Liste fixiert; jede
  Erweiterung waehrend C2 erfordert Sub-Slice-Bezeichnung
  (`Welle 2a/2b`).
- **Trigger 004 (canonical_encoder) re-aktiviert sich**:
  wenn `canonical_json`-Serialisierung im MQTT-Publish-
  Pfad messbar zum Throughput-Bottleneck wird (z. B. bei
  hoher Telemetry-Frequenz im Mosquitto-Sibling-Smoke),
  triggert Trigger 004 (`orjson`/`msgspec`-Alternative).
  *Mitigation*: Welle 2-C2-Smoke hat moderate Frequenz
  (Tick-Loop-Standard, nicht Stress-Test); Trigger 004
  bleibt in `open/` mit Re-Eval-Notiz in Welle 6.
- **`eclipse-mosquitto:2`-Lizenz / Image-Pin-Drift**:
  Lizenz EPL-2.0/EDL-1.0 ist redistributable; aber Image-
  Pinning (`eclipse-mosquitto:2.0.18` o. ae. statt nur
  `:2`) hilft gegen Auto-Major-Bumps. *Mitigation*: C2
  pinnt das Image auf eine spezifische Patch-Version
  (Floor matcht aktueller Welle-2-Zeitpunkt; `make
  fullbuild`-Run dokumentiert die Wahl).
- **`make fullbuild`-`image-audit` weiter rot**: krb5-CVE
  bleibt durch Welle 2 unbeeinflusst. *Mitigation*: Welle
  2-C3-Sync hebt den Pre-existing-Drift-Hinweis aus
  M4-Welle-1 ohne Aenderung in alle Top-Level-Docs; der
  Base-Image-Bump-Stack bleibt unabhaengiges Arbeitspaket.

---

## 8. Wandert nach

- `done/M4-welle-2.md` mit M4-Welle-3-Pre-C0-Move (Pattern
  aus M3 und M4-Welle-1: `welle-2.md` wandert mit
  M4-Welle-3-Pre-C0 nach `done/`; `chore(welle-3): git mv`-
  Commit + Pre-C0-Sync-Folge-Commit, Memory-Konvention
  `feedback_git_mv`).
- ADR 0031 bleibt in `docs/plan/adr/` (kein Move; nur
  Status-Updates).
- `M4-protocol-adapters.md` bleibt in `in-progress/` bis
  M4-Welle-7-Closure.
- M4-Welle-3-Naechster-Schritt: Modbus-TCP-Adapter
  (`pymodbus`-Wrapper + Register-Mapping + Modbus-Sibling-
  Smoke). Welle-2-Pattern fuer Decision 4a-Profile-
  Deklaration ist die Praezedenz, gegen die Welle 3
  Register-Schema entscheidet.

---

## 9. DoD-Checkliste (Welle-Schluss, mit C3 abgehakt)

Pattern analog M4-welle-1.md §9. Belege siehe
**DoD-Verifikation**-Block im Status-Header oben + §4
Liefer-Reihenfolge fuer die per-Commit-Aktion.

**In-Scope-Items (alle abgehakt mit C3):**

- [x] **ADR 0031 angelegt** — `Proposed` (C1 `4e102b8`) →
  `Provisional` (dieser Commit), mit Decisions 4a/4b/4c/4d
  alle **final** (Topic-Schema inline, `canonical_json`-
  Codec, QoS 0/1, Per-Target `queue.Queue` mit Lazy-Init).
  Code:
  [`../../adr/0031-mqtt-adapter-profile.md`](../../adr/0031-mqtt-adapter-profile.md).
- [x] **MQTT-Port produktiv** — `MqttDeviceProtocolPort`
  als `DeviceProtocolPort`-Implementer unter
  [`../../../../src/grid_gym/adapters/driven/protocol_mqtt/`](../../../../src/grid_gym/adapters/driven/protocol_mqtt/)
  (7 Dateien: `__init__.py` + `_config.py` + `_codec.py` +
  `_topic_resolver.py` + `_port.py` + `_errors.py` +
  `error_translation.py`). Modul-Docstring in
  `__init__.py` traegt Lastenheft-Z.-1161–1163-Pflicht
  (Simulations-/Testadapter, **keine** produktive
  Anlagensteuerung). NEU mit C2 `f33bb4e`.
- [x] **Unit-Tests fuer 4 Test-Aspekte** — 50 neue Tests
  (1161 → 1211): 11 Codec-Roundtrip + 16 Topic-Resolver +
  17 Lifecycle/Read+Write + 6 Callback-Marshal. Code:
  [`../../../../tests/unit/adapters/driven/protocol_mqtt/`](../../../../tests/unit/adapters/driven/protocol_mqtt/).
- [x] **Integration-Smoke produktiv** —
  [`../../../../tests/integration/test_mqtt_compose_smoke.py`](../../../../tests/integration/test_mqtt_compose_smoke.py)
  spawnt `eclipse-mosquitto:2`-Sibling via testcontainers
  (Inline-Config mit `allow_anonymous true`); End-to-End-
  Pub/Sub-Roundtrip gegen `MqttDeviceProtocolPort` +
  Bounded-Poll-Loops mit 5-Sekunden-Timeout.
- [x] **`tests/integration/compose.yml` syncht** —
  Header-Kommentar listet `mosquitto`-Sibling neben
  Postgres + otel-collector (alle via testcontainers,
  kein eigener Compose-Service). Lizenz EPL-2.0/EDL-1.0
  redistributable.
- [x] **`pyproject.toml` erweitert** — `paho-mqtt>=2.0`
  in `[project] dependencies` (Floor 2.0 wegen
  `CallbackAPIVersion.VERSION2`); `paho`-Eintrag in den
  AC-PORTS-NO-FW/AC-NO-FW-Forbidden-Listen unveraendert
  (Welle-0-Vorbelegung). `uv.lock` via `make lock-refresh`
  aktualisiert: `paho-mqtt v2.1.0`.
- [x] **`Dockerfile` erweitert** — `CRITICAL_COV_TARGETS`-
  Default um
  `src/grid_gym/adapters/driven/protocol_mqtt` ergaenzt
  (Pattern analog `telemetry_otlp`-Eintrag aus
  M3-Welle-6-`c61ab0d`).
- [x] **`AC-ADAPTER-LIGHTWEIGHT` greift fuer
  `protocol_mqtt`** — `tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`-Filter erfasst den
  neuen Pfad **ohne Code-Aenderung**; `make arch-check`
  weiter `19/19 Contracts KEPT`. McCabe-Komplexitaets-
  Schwelle in `_config._validate_topics` per Refactor in
  drei modul-lokale Helpers (`_validate_single_topic_config`/
  `_collect_topic_strings`/`_assert_unique_topics`) eingehalten.
- [x] **C3-Doc-Sync** — `M4-welle-2.md` Status
  `In Progress → Done` (dieser Commit), ADR 0031
  `Proposed → Provisional` (dieser Commit),
  `M4-protocol-adapters.md §3 Welle 2` Done-Markierung
  (dieser Commit), Top-Level-Doku-Sync in 5 Docs
  (`README.md` + `README.de.md` + `roadmap.md` +
  `spec/architecture.md` + `adr/README.md`-Zeile 31)
  auf den Welle-2-Endstand. `done/README.md`-Bestand-Zeile
  folgt mit M4-Welle-3-Pre-C0-Sync (Pattern analog
  M4-Welle-1 `f1f9db1`).

**Anti-Scope-Items (alle gehalten):**

- [x] **Keine Modbus-/OPC-UA-/DNP3-/IEC-Adapter** in C2 —
  verifiziert: keine neue Datei unter
  `adapters/driven/protocol_{modbus,opcua,dnp3,iec}/`.
- [x] **Kein OTel-Span-Wrap** der MQTT-Adapter-Calls —
  verifiziert: kein Import von
  `adapters/driven/telemetry_otlp/` in `protocol_mqtt/`;
  TracePort-Wrap bleibt Welle-6-Material.
- [x] **Kein RandomPort-Determinismus** fuer Topic-/
  Client-IDs — verifiziert: `MqttProtocolPortConfig.client_id`
  ist explizites Pflichtfeld (kein Auto-Generierungs-Pfad);
  paho-mqtt-Default-Client-ID kommt nie zum Einsatz.
- [x] **Keine Scenario-Schema-Erweiterung jenseits des
  Decision-4a-Pattern** — verifiziert: kein Touch an
  `scenario/validator.py` und kein neuer YAML-Top-Level-
  Block. `MqttProtocolPortConfig` ist Adapter-intern,
  Loader bleibt MQTT-frei per AC-HEXAGON-PURE (Scenario-
  YAML-Parsing via separater `parse_mqtt_config`-Factory
  ist Welle-3-Material oder Folge-Welle-Schaerfungspfad).
- [x] **Keine Bewegung der 17 Open-Trigger** — verifiziert:
  `docs/plan/planning/open/` unveraendert. Trigger 004
  (`canonical encoder`-Alternative) bleibt offen; Re-Eval
  durch Welle 6 (Cross-Adapter-Hardening).
- [x] **Kein M4-DoD-Checkbox-Abhaken** in `roadmap.md` —
  verifiziert: `roadmap.md` §3 M4 Checkboxen alle
  weiterhin ungehakt (1 von 7 DoD-Items geliefert; Sweep
  in Welle 6).
- [x] **Kein `AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-
  Property-Test** in Welle 2 — verifiziert: nur Smoke-
  Regression-Schutz via `make arch-check`. Welle-1-§7-
  Folge-Pflicht bleibt auf Welle 6 verschoben (siehe
  [`../done/M4-welle-1.md`](../done/M4-welle-1.md) §7
  Folge-Mitigation).
