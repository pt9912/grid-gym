# ADR 0075 — Field-Server-Surface: Schwester-Ports `FieldPublishPort` (Push) + `DeviceServerPort` (Pull), Kompositions-Schicht

**Status:** Accepted (2026-07-12) — **beide** Schwester-Ports belegt: die
Push-Seite (`FieldPublishPort`, MQTT) und die Pull-Seite (`DeviceServerPort`,
Modbus-TCP-Server mit Read-Serving, bind/listen/serve), je review-gehaertet.
Zuvor Provisional (Push-Seite geliefert) und davor Proposed — Design-first,
gezogen 2026-07-12 aus einer Architektur-
Sichtung (README-Intro „stellt fuer ein EMS wie `bess-ems` simulierte Geraete
bereit" vs. Ist-Stand „alle fuenf Protokolladapter sind Client/Master") und
zwei adversarialen Reviews (Design + Plan), die den ersten Entwurf (ein
geteilter `DeviceEndpointPort` am Kern-`TickLoop`) gegen Code widerlegten.
Owner-Sign-off der revidierten Marschrichtung 2026-07-12: **zwei Schwester-Ports
in der Kompositions-Schicht**, Inbound-Writes ausgegliedert.
Status-Pfad (ADR 0006 §4, **kapazitaetsbasiert** — liefer-agnostisch): Proposed →
**Provisional**, sobald die Push-Seite (`FieldPublishPort`) mit einem ersten
Adapter + der Kompositions-Schicht-Naht produktiv belegt ist → **Accepted**,
sobald die Pull-Seite (`DeviceServerPort`, bind/listen/serve) mit Read-Serving
belegt ist. Das Delivery-Mapping (welche Slices/Wellen die Transitionen liefern)
lebt im **ADR-Index + Roadmap**, **nicht** im ADR-Body — ADRs bleiben
liefer-agnostisch (die bestehenden delivery-koppelnden ADRs zieht ein
Folge-Trigger auf dieselbe Konvention nach).
**Datum:** 2026-07-12
**Bezug:**

- [`ADR 0030`](0030-device-protocol-port-surface.md) — `DeviceProtocolPort`
  (driven, Client/Master). ADR 0075 ergaenzt die fehlende **Server-/Outstation-
  Gegenrolle** als **eigenstaendige Ports** (kein Supersedes,
  [`ADR 0011`](0011-schaerfung-ohne-abloesung.md)-Schwester-Port-Muster). Die
  connect-/stateless-Begruendung von ADR 0030 wird **nicht** pauschal gespiegelt
  (§2.4 begruendet Server-Lifecycle eigenstaendig).
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schwester-Port-/Schaerfung-
  ohne-Abloesung (Form-Anker; hier zwei parallel existierende Ports).
- [`ADR 0012`](0012-api-simulation-two-processes.md) — API- und Simulation-
  Prozess getrennt. **Zentral fuer die Naht-Wahl:** der Telemetry-Fan-out lebt
  im **API-Prozess-Driver**, nicht im Kern-`TickLoop` (§1).
- [`ADR 0038`](0038-telemetry-stream-port.md) — `TelemetryStreamPort`
  (fire-and-forget Pub/Sub, Drop-Oldest). ADR 0075 nutzt ihn **nicht** als
  Pull-Quelle; die Current-Value-Projektion (§2.2) wird aus
  `TickResult.emitted_telemetry` gespeist.
- [`ADR 0013`](0013-device-model-protocol.md) / [`ADR 0070`](0070-scenario-scheduled-device-commands.md)
  — `apply_command`-Pfad + scenario-scheduled-Command-Determinismus. Relevant
  **nur** fuer den **ausgegliederten** Inbound-Write-Pfad (§7), der eine eigene
  Slice + Folge-ADR bekommt.
- [`ADR 0022`](0022-fault-injection-protocol.md) §2.5 / [`ADR 0024`](0024-observability-port-trio.md)
  §2.1 — „neuer Port-Slot"-Muster.
- [`ADR 0050`](0050-adapter-pure-bridge-retirement.md) — `AC-ADAPTER-PURE`:
  Adapter typisieren gegen den Port, nicht gegen `core.*`.
- [`GG-TEST-004`](../../../spec/lastenheft.md#gg-test-004) (HIL, SOLLTE) —
  motivierende Anforderung (EMS als System-under-Test an simulierte Geraete
  koppeln).
- [`GG-NONGOAL-001`](../../../spec/lastenheft.md#gg-nongoal-001) /
  [`GG-SAFE-007`](../../../spec/lastenheft.md#gg-safe-007) — Sim/Prod-Trennung.
- [`spec/protocol_profiles.md`](../../../spec/protocol_profiles.md) — Profil-
  Index (aktuell auf die fuenf driven-Master-Adapter gerahmt; Server-Profile
  bekommen eine **eigene** Sektion, keine Einmischung in den Master-Index).

---

## 1. Kontext

**Beobachtete Asymmetrie (verifiziert, C0-Sichtung + zwei Code-Reviews):**

- Alle fuenf Protokolladapter (`adapters/driven/protocol_*/`) sind
  [`ADR 0030`](0030-device-protocol-port-surface.md)-`DeviceProtocolPort` in
  **Client-/Master-Rolle** (MQTT `client.publish()`, Modbus
  `ModbusTcpClient.connect()`, OPC-UA-Client, DNP3-Master, IEC-MMS-Client) —
  **driven**, der Kern ruft nach aussen.
- Die einzigen **driving**-Adapter sind `adapters/driving/http_api/` + `ui/`;
  die driving-Ports ([`GG-AR-PORT-DRV-001..007`](../../../spec/architecture.md#driving-ports-vom-kern-angeboten))
  sind API-/CLI-Use-Case-Ports, **kein** Feldbus-Server. Fuer den HIL/SUT-Fall
  (EMS als Feldbus-Master pollt simulierte Geraete) fehlt die Server-Seite.

**Naht-Realitaet (das, was den ersten Entwurf gekippt hat):**

- Der Telemetry-Fan-out sitzt **nicht** im Kern-Spine. Der Kern-`TickLoop` haelt
  `telemetry_sink` (driven) + `protocol_ports`, aber **keinen**
  `TelemetryStreamPort` und **kein** `publish`
  (`hexagon/core/simulation/tick_loop.py`). Der Stream-Publish passiert im
  **http_api-Driver** (`_tick_loop_driver._publish_emitted_telemetry`), der
  `TickResult.emitted_telemetry` liest und Domain→Port mappt; der WS-Konsument
  subscribt in der **Kompositions-/App-Schicht**. Per
  [`ADR 0012`](0012-api-simulation-two-processes.md) laeuft der Kern-Loop
  produktiv im `simulation`-Worker — dort existiert der Stream **gar nicht**.
- `TelemetryStreamPort` ist fire-and-forget mit **Drop-Oldest-FIFO** ueber alle
  Points (`adapters/driven/telemetry_stream_inmemory/`) — **keine** „letzter
  Wert pro Ziel/Metrik JETZT"-Abfrage. Als Quelle fuer einen Pull-Server (der
  Master pollt zu beliebiger Zeit) ungeeignet.
- Das driving-DTO traegt bereits `value: float` (lossy aus Domain-`Decimal`
  gecastet in `_to_port_telemetry_point`) — jeder Pull-Server-Register-Encode
  ist ein **zweiter** Verlustschritt.

**Kern-Einsicht (revidiert):** Push (grid-gym → Broker) und Pull (Master pollt
grid-gym) sind **verschiedene Rollen** — Push ist driven-foermig, Pull ist echt
driving (bind/listen/serve). Ein einziger geteilter Port verwischt sie. Der
**wiederverwendbare Hebel** ist **nicht** ein Port, sondern (a) eine
**Current-Value-Projektion** (last-value pro `(target, metric)`, tick-frame-
atomar, aus `TickResult.emitted_telemetry`), die jeder Pull-Server teilt, und
(b) die **Kompositions-Schicht-Naht** (Driver-Level-Lifecycle + Fan-out-
Entrypoint), wo `telemetry_stream`/`alarm_stream` bereits sitzen.

---

## 2. Entscheidung

ADR 0075 legt zwei Schwester-Ports in der **Kompositions-/Driver-Schicht** fest
(**nicht** als Kern-`TickLoop`-Kwarg).

### §2.1 Zwei Schwester-Ports (statt eines geteilten Ports)

- **`FieldPublishPort`** (driven), `hexagon/ports/driven/field_publish.py`:
  `start()` (Broker-Connect) / `publish(point: TelemetryPoint) -> None` (ein
  emittierter Punkt) / `stop()` (Disconnect, idempotent). Push zu einem Broker;
  verhaltensnah zu `telemetry_sink.persist()` + `DeviceProtocolPort`-Lifecycle,
  aber **driver-getrieben** (nicht `TickLoop`). Erster Adapter:
  `adapters/driven/field_publish_mqtt/` (paho-mqtt).
- **`DeviceServerPort`** (driving), `hexagon/ports/driving/device_server.py`:
  `start()`/`stop()` = bind/listen/serve. Ein externer Master pollt; der Adapter
  serviert Register aus der Current-Value-Projektion. Erster Pull-Adapter:
  `adapters/driving/device_server_modbus/` (`pymodbus`-Server).
- Beide teilen die **Current-Value-Projektion** (§2.2) als **Helper-Modul** —
  **keinen** Port-Vertrag ([`ADR 0011`](0011-schaerfung-ohne-abloesung.md)-
  Schwester-Muster; die zwei Rollen bleiben getrennt typisiert).
- `TelemetryPoint` ist der **Domaenen**-Typ (`hexagon/core/domain/telemetry`,
  [`GG-DATA-001`](../../../spec/lastenheft.md#gg-data-001)) — wie bei
  `DeviceProtocolPort` (driven-Port → Domaenen-DTO, **kein** driven→driving-
  Import; volle `Decimal`-Fidelity statt des `Decimal→float`-Verlusts der
  driving-Stream-DTO). Der Driver speist `publish()` direkt aus
  `TickResult.emitted_telemetry`.

### §2.2 Geteilter Hebel: Current-Value-Projektion (Helper, kein Port)

Ein Helper-Modul (Kompositions-Schicht) haelt eine **last-write-wins**-Projektion
`(target, metric) → letzter TelemetryPoint`, gespeist aus
`TickResult.emitted_telemetry` (**nicht** aus dem Drop-Oldest-Stream). Die
Projektion ist **tick-frame-atomar**: sie wird pro Tick als geschlossener Frame
aktualisiert (ein Poll sieht nie einen halb-aktualisierten Frame).

- **Push-Seite (`FieldPublishPort`)** braucht die Projektion **nicht** — sie
  leitet jeden emittierten Punkt direkt weiter (deshalb ist die Push-Seite
  leichter und baut sie **nicht**; der frueher angenommene „Push-Adapter macht
  den Pull-Adapter duenn"-Anspruch entfaellt bewusst).
- **Pull-Seite (`DeviceServerPort`)** materialisiert die Projektion — sie ist
  die Foundation, die **jeder** kuenftige Pull-Server (Modbus jetzt; DNP3-
  Outstation/OPC-UA-Server/IEC-Server spaeter) teilt. Erstmalig mit dem ersten
  Pull-Server gebaut.
- **Quality-Marker** ([`ADR 0074`](0074-metric-quality-fault-stage-stale-nan.md):
  `STALE`/`NAN`) reisen im `TelemetryPoint`; der Server mappt sie protokoll-
  spezifisch (der Modbus-Server mappt sie auf Discrete-Inputs/Flags).

### §2.3 Placement: Kompositions-/Driver-Schicht, kein Kern-`TickLoop`-Kwarg

Beide Ports werden **wie `telemetry_stream`/`alarm_stream`** in der Driver-/App-
Schicht verdrahtet (der Driver liest `TickResult.emitted_telemetry` und speist
Publisher/Projektion). **Kein** `field_endpoints`-Kwarg am Kern-`TickLoop` — das
war der Fehler des ersten Entwurfs: der Kern-Loop laeuft im `simulation`-Worker
ohne Stream/Fan-out ([`ADR 0012`](0012-api-simulation-two-processes.md), §1).

- Der sync/async-Ubergang bleibt **im API-Prozess**: die Projektion + der
  Server-Loop-Thread leben dort, wo der Fan-out liegt; kein Cross-Loop-Zugriff
  auf loop-affine Stream-Queues (Review-Fund).

### §2.4 Server-Lifecycle eigenstaendig (nicht ADR-0030-Spiegel)

`DeviceServerPort.start()` = bind + listen + serve. **Bind-in-use (Port belegt)
ist ein harter Fehler vor dem ersten Tick** (kein Lazy-Connect-Analogon).
`stop()` = Listener graceful drainen/schliessen. FIFO-Start/LIFO-Stop +
Best-Effort-Partial-Cleanup werden aus
[`ADR 0030`](0030-device-protocol-port-surface.md) §2.2 uebernommen, die
**connect-orientierte Begruendung dagegen nicht** — die Naht wird vom Driver
gehalten, nicht vom Kern-Loop.

`FieldPublishPort` (Push) = connect + publish, driven-foermig (wie ein Sink);
`None`-Skip im Driver-Setup, Replay-Pfad ohne Broker-Connect.

### §2.5 Determinismus / Replay: Read-Serving ist replay-sicher, Server-State volatil

Die Current-Value-Projektion ist eine **reine Funktion** der emittierten
Telemetrie (deterministisch, sim-zeit-getrieben, `AC-NO-TIME`). Server-State
(Sockets, Register-Map-Materialisierung, Subscriber-Listen) ist **volatil** und
wird **nicht** in `SnapshotEnvelope` persistiert; ein Resume startet die Ports
regulaer. **Kein** Snapshot-Schema-Bump. Read-Serving + Push bringen gegenueber
einem Run ohne Field-Ports **kein** Verhalten-/Byte-Delta (Bestands-Pins
unberuehrt).

### §2.6 Sim-/Test-Charakter (Cross-Cutting-Doku-Pflicht)

Jeder Field-Adapter dokumentiert den Sim-/Test-Charakter
([`GG-NONGOAL-001`](../../../spec/lastenheft.md#gg-nongoal-001) /
[`GG-SAFE-007`](../../../spec/lastenheft.md#gg-safe-007)); keine Produktiv-
Steuerung. Die exponierten Surfaces (MQTT-Broker, Modbus-TCP ohne Auth) tragen
eine Nur-Sim-Netz-Deployment-Note — fuer **beide** Slices (Review-Fund: der
erste Entwurf hatte sie nur auf der Pull-Seite).

---

## 3. Begruendung

- **Zwei Rollen, zwei Ports.** Push (driven, Kern pusht raus) und Pull (driving,
  bind/listen/serve) sind strukturell verschieden; ein geteilter Port haette sie
  verwaschen und dieselbe Kritik geerntet wie die in §4 A1 verworfene
  `DeviceProtocolPort`-Wiederverwendung.
- **Hebel = Projektion + Naht, nicht Port.** Der wiederverwendbare Teil ist die
  Current-Value-Projektion (jeder Pull-Server teilt sie) und die Kompositions-
  Schicht-Verdrahtung — ehrlich verortet, statt einem Push-Adapter faelschlich
  eine „macht den Pull-Server duenn"-Rolle anzudichten.
- **Naht folgt der Prozess-Realitaet.** Fan-out + Stream leben im API-Prozess-
  Driver ([`ADR 0012`](0012-api-simulation-two-processes.md)); die Field-Ports
  gehoeren dorthin, nicht an den Kern-Loop.

---

## 4. Alternativen

- **A1 (verworfen) — ein geteilter `DeviceEndpointPort` fuer Push + Pull
  (erster Entwurf).** Von beiden Reviews widerlegt: verwischt zwei Transport-
  Rollen unter einer losen Klammer („Zustand exponieren"), die ebenso den
  bestehenden driven `telemetry_sink` + `DeviceProtocolPort.write` beschreibt —
  schneidet keinen scharfen Port.
- **A2 (verworfen) — `field_endpoints`-Kwarg am Kern-`TickLoop` (Spiegel von
  `protocol_ports`).** Der Kern-Loop laeuft im `simulation`-Worker ohne Stream/
  Fan-out ([`ADR 0012`](0012-api-simulation-two-processes.md)); `protocol_ports`-
  Lifecycle wird produktiv nicht einmal aufgerufen. Falsche Schicht.
- **A3 (verworfen) — Pull-Server direkt aus dem `TelemetryStreamPort`.**
  Fire-and-forget + Drop-Oldest-FIFO kann „letzter Wert JETZT" nicht liefern;
  ein Master-Poll saehe Luecken/stale Register. Deshalb die eigene Projektion.
- **A4 (verworfen) — Inbound-Write als Teil der Pull-Server-Lieferung mit „bis Tick-Grenze puffern".**
  Ein Live-Master-Write ist exogener Input zu Wall-Clock-Zeit; die Tick-
  Zuordnung ist im Live-Run genau die reale Ankunft → nicht replaybar. Gehoert
  in ein eigenes Kapazitaets-Inkrement + eine Folge-ADR mit
  Exogen-Input-Recording (§7).

---

## 5. Lieferschnitt (kapazitaetsbasiert)

Design-first (diese ADR), dann in drei Kapazitaets-Inkrementen — bewusst
**liefer-agnostisch** beschrieben; welche Slices/Wellen sie liefern, steht im
**ADR-Index + Roadmap**, nicht hier:

1. **Push-Seite (`FieldPublishPort`):** der Port + die Kompositions-Schicht-Naht
   (Driver-Lifecycle + Fan-out-Entrypoint gegen den Produkt-Surface) + das
   grid-gym↔`bess-ems`-Integrationsgeschirr (Compose mit Broker). Baut die
   Current-Value-Projektion **nicht** (reiner Push). → zieht die ADR auf
   `Provisional`.
2. **Pull-Seite (`DeviceServerPort`, Read-Serving):** der Port + die geteilte
   Current-Value-Projektion + Register-Map-Encode + Read-E2E. **Ohne**
   Inbound-Write. → zieht die ADR (mit Closure) auf `Accepted`.
3. **Inbound-Write→Command (ausgegliedert):** loest das Exogen-Input-Recording
   und bringt eine **dedizierte Folge-ADR** (§7); versoehnt Live-Writes mit dem
   geschlossenen Self-Replay-Modell.

Jedes Inkrement traegt Akzeptanzkriterien, Verifikationspfad und Release-Feld im
liefernden Slice; die Verifikation (`make gates`/`make docs-check`/`make
fullbuild`) lebt in dessen Closure.

---

## 6. Konsequenzen

- **Positiv:** die HIL/SUT-Anbindung ([`GG-TEST-004`](../../../spec/lastenheft.md#gg-test-004))
  wird real; ein EMS kann simulierte Geraete ueber Feldbus lesen (Read-Serving),
  ohne dass grid-gyms Determinismus bricht.
- **Positiv:** additive Ports in der Driver-Schicht, `None`-Skip → Bestands-Runs
  byte-identisch.
- **Neutral:** neue Adapter-Familien `adapters/driven/field_publish_*/` +
  `adapters/driving/device_server_*/`; `AC-ADAPTER-PURE`/`AC-ADAPTER-LIGHTWEIGHT`
  greifen.
- **Bewusste Grenze:** Live-Inbound-Steuerung ist **nicht** replaybar und darum
  ausgegliedert (§7); bis der Inbound-Write-Pfad geliefert ist, ist der
  Field-Server **read-serving-only**.

---

## 7. Nicht Gegenstand dieser ADR / offene Punkte

- **Inbound-Write→Command** — ausgegliedert in ein eigenes Kapazitaets-Inkrement
  (§5) + eine dedizierte Folge-ADR. Grund: ein Live-Master-Write ist exogener Input
  ohne `simulation_time`; grid-gyms geschlossenes Self-Replay
  (`(Szenario, Seed, tick_ms)`) hat keinen Exogen-Input-Recording-Pfad, und §2.5
  verbietet Server-State im Snapshot. Die Folge-ADR loest Record/Replay
  (Write→Journal mit erfasstem Sim-Tick → deterministische Re-Injektion) oder
  scopt HIL-Live-Runs explizit als record-only/nicht-replaybar.
- **Anforderungs-Verankerung (entschieden 2026-07-12):** die Field-Server-
  Surface ist eine **HIL-Konkretisierung von**
  [`GG-TEST-004`](../../../spec/lastenheft.md#gg-test-004) (SOLLTE) — **keine**
  eigene `GG-*`-ID. Die liefernden Slices dokumentieren die vier
  [`GG-TEST-004`](../../../spec/lastenheft.md#gg-test-004)-Akzeptanz-Aspekte
  (Testgrenzen, Simulationsadapter, erwartete Signale, deterministisches
  Replay-Verhalten); **kein** neuer normativer Anforderungs-Eintrag, **kein**
  `lastenheft.md`-Edit.
- **DNP3-Outstation / OPC-UA-Server / IEC-Server** — weitere Pull-Server auf
  `DeviceServerPort` + geteilter Projektion; eigene Slices bei Bedarf.
- **Register-Map-/Encode-Genauigkeit** — der `Decimal→float`-DTO-Verlust plus
  `Decimal→16-bit`-Register-Verlust braucht einen definierten Gleichheits-Oracle
  (mit der Pull-Seite, §5).
- **Auth/Security** — Deployment-/Profil-Thema je Slice (Nur-Sim-Netz).
- **`bess-ems`-Seite** — liegt im Schwesterprojekt; ADR 0075 liefert die
  grid-gym-Seite + das Integrationsgeschirr.
