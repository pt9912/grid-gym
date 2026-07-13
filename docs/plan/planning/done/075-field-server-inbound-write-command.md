# 075 — Field-Server Inbound-Write→Command (Exogen-Input-Recording)

**Status:** **Done (`done/`, 2026-07-13).** Baut auf
[`074`](074-field-server-modbus-server-adapter.md) (`DeviceServerPort`
Read-Serving, done) auf. Ausgegliedert aus dem urspruenglichen 074-Scope, weil
der Determinismus-Vertrag eigenes Design + eine dedizierte Folge-ADR braucht
([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §7).
**Fortschritt:** S0 ✓ (Folge-[`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md)
**Modell B**) · **S1a ✓** (Kern-Naht: Vor-Tick-Schritt A0i +
`InboundCommandPort` + `InboundCommandBuffer`/Capture, unit-getestet) · **S1b ✓**
(Modbus-Write→`Command`-Naht [`SimAction`/FC06/FC16] + `write_map`/`InboundWrite
Decoder` + `TickLoopWiring.inbound_source` + Materialisierungs-Helper +
Real-pymodbus-Write-E2E → [`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md)
**`Provisional`**) · **S2 ✓** (Determinismus-E2E: materialisierter Strom 2x
byte-identisch + faithful; Agent-Konflikt-Grenze gepinnt → [`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md)
**`Accepted`**).
**Datum:** 2026-07-13 (done; aktiviert 2026-07-12)
**Quelle:** Design- + Plan-Review 2026-07-12 — ein Live-Master-Write ist
**exogener** Input zu Wall-Clock-Zeit; grid-gyms geschlossenes Self-Replay
(`(Szenario, Seed, tick_ms)`, rekonstruiert aus persistierter Telemetrie) kennt
keinen Exogen-Input-Recording-Pfad.

---

## Ziel

Dem `DeviceServerPort` einen **Inbound-Write-Pfad** geben: ein externer Master
schreibt einen Sollwert (Modbus-Write-Register/-Coil) → grid-gym traegt ihn als
`Command` in den Kern zurueck — **und** loest das Determinismus-/Replay-Problem
(Live-Write ist reproduzierbar wiederholbar), statt es zu verstecken.

## Kontext / Ist

- Read-Serving ([`074`](074-field-server-modbus-server-adapter.md)) ist replay-
  sicher (Projektion = reine Funktion der emittierten Telemetrie). **Schreiben**
  bricht das: der Command-Zeitpunkt haengt an der realen Ankunft des Live-Writes,
  nicht an gehashten Scenario-Daten.
- [`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md)-
  Determinismus stammt aus `simulation_time`-**geplanten**, im `scenario_hash`
  erfassten Commands — eine andere Achse als extern getaktete Live-Writes.
- [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §2.5
  verbietet Server-State im Snapshot; ein Write-Record-Pfad muss diese Grenze
  respektieren oder bewusst amendieren.

## Kern-Decision ([`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md))

S0 hat nach gegroundetem A/B-Design-Assessment **Modell B** festgezurrt
([`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md),
`Proposed`): **record-only + Materialisierung**, Capture-Format bewusst
**Option-A-kompatibel** (A = Write-Journal/Runtime-Re-Injektion additiv
nachruestbar, §2.6).

- Ein angewandter Write wird als `(aufgeloester_sim_tick, target, type, payload,
  arrival_sequence)` erfasst → in einen Szenario-`commands`-Block
  **materialisiert** → ueber den bereits gepinnten Vor-Tick-Pfad **A0s**
  ([`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md),
  [`ADR 0013`](../../adr/0013-device-model-protocol.md) `apply_command`) replayt →
  **byte-identisch by construction** (`scenario_hash` deckt `commands`).
- **Kein** Snapshot-Bump ([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
  §2.5 gewahrt); die A0i-Faelligkeit wird statuslos re-abgeleitet.
- **Ehrlicher Vertrag:** der Live-Lauf ist nicht aus `(Szenario, Seed, tick_ms)`
  allein reproduzierbar (Tick-Aufloesung des Wall-Clock-Arrivals ist exogen); die
  Capture ist die Source-of-Truth, der materialisierte Strom replayt deterministisch.

## Slice-Schnitt (rollen-getrennt)

| Slice | Inhalt | Rolle / Artefakt |
| --- | --- | --- |
| **S0** ✓ | Dedizierte Folge-[`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md) (`Proposed`): Exogen-Input-Recording-Modell **B** entschieden (record-only + Materialisierung, Capture Option-A-kompatibel), Determinismus-Vertrag + Snapshot-Grenze fixiert; gegroundetes A/B-Design-Assessment am Command-/Replay-/Snapshot-Code | Architect / ADR |
| **S1a** ✓ | **Kern-Naht (pymodbus-frei, unit-getestet):** driven `InboundCommandPort` (`hexagon/ports/driven/inbound_command.py`; Kern *pullt* pro Tick) + additive Vor-Tick-Stufe **A0i** im `TickLoop` (Ordnung scenario→agent→inbound, `None`-Skip → Bestands-Laeufe byte-identisch, defensiver Skip fuer unbekannte Targets) + `InboundCommandBuffer` (`adapters/driving/_inbound_command_buffer.py`: thread-sicherer Puffer, `arrival_sequence`, Next-Tick-Aufloesung auf `context.simulation_time`, `InboundWriteCapture`-Aufzeichnung). Buffer/Capture volatil (kein Snapshot-Slot) | Implementation |
| **S1b** ✓ | **Modbus-Write + Wiring + Materialisierung:** Modbus-Write-Register (FC06/FC16) am Server-Adapter-Rand via pymodbus-`SimAction`-Hook → `InboundWriteDecoder` (`write_map`, `float32`→`Decimal`, pymodbus-frei) → `InboundCommandBuffer.enqueue` (Cross-Thread, Diskriminator gegen FC03-Refresh); Wiring: **ein** geteilter Buffer als `inbound_source` (via `TickLoopWiring`/`build_tick_loop`) **und** in den `ModbusDeviceServerAdapter` injiziert; `materialize_inbound_writes(capture())` → Szenario-`commands`-Block. Real-pymodbus-Write-E2E (Master-`write_registers` → Command am Zielgeraet) + Config-/Decoder-/Materialisierungs-Unit-Tests. **→ [`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md) `Provisional`** (`make gates` + `make docs-check` gruen) | Implementation |
| **S2** ✓ | **Determinismus-E2E:** der erfasste Write-Strom wird in einen Szenario-`commands`-Block **materialisiert** + ueber A0s **zweimal byte-identisch** abgespielt (`test_inbound_write_determinism_e2e.py`) + deckungsgleich mit dem „Live"-Lauf des kommandierten (agenten-freien) Geraets. Ordnung scenario→agent→inbound + die **Materialisierungs-Grenze** (Agent-auf-gleichem-Ziel divergiert → bewusste Modell-B-Grenze) gepinnt (`test_pre_tick_command_order_...`, [`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md) §7). **Closure → `Accepted`** | Implementation |

## S1b — Ist-Stand (done 2026-07-13)

Geliefert (`make gates` + `make docs-check` gruen):

- **Write-Intercept** (`_adapter.py`): pymodbus-3.13-`SimDevice(action=...)`-Hook
  (`_make_write_action`). Signatur verifiziert **am realen Server** (`simruntime.
  __check_block` ruft `action` bei jedem Register-Zugriff). **Diskriminator:** nur
  `function_code ∈ {FC06, FC16}` **und** `set_values is not None` → Inbound-Write;
  der interne Refresh-Push nutzt FC03 (`async_setValues` mit dem Read-Code als
  Block-Selektor), Reads liefern `set_values is None` → beide fallen durch. Der
  Hook gibt **immer `None`** zurueck (erlaubt den Write, stoert den Refresh nicht).
- **Reverse-Map** (`_write_map.py`, pymodbus-frei): `WritableRegisterMapping`
  (`address → target_device_id, command_type`) in `ModbusServerConfig.write_map`
  (getrennt vom Read-`register_map`; jede Holding-Adresse eine Rolle).
  `InboundWriteDecoder.decode(...)` + totales `decode_float32` (nicht-endliche
  Bitmuster verworfen). `payload={"value": Decimal}`.
- **Wiring**: **ein** geteilter `InboundCommandBuffer` → als `inbound_source` durch
  `TickLoopWiring`/`build_tick_loop` **und** als `inbound_buffer` in den
  `ModbusDeviceServerAdapter`/Runner. In-Process-Hoehe wie 074 (keine env-var-
  Lifespan-Naht — siehe „Offen/Trigger" unten).
- **Materialisierung**: `materialize_inbound_writes(capture())` → `ScenarioCommand`s
  (sortiert nach `(resolved_sim_tick, arrival_sequence)`).
- **Tests**: Real-pymodbus-Write-E2E (`test_write_e2e.py`: Master-`write_registers`
  → Command am Zielgeraet; Refresh/Reads enqueuen nicht) + Decoder/Config/
  Materialisierungs-Unit-Tests.

## S2 — Ist-Stand (done 2026-07-13)

Determinismus-E2E geliefert (`tests/integration/test_inbound_write_determinism_e2e.py`,
Muster `test_scenario_commands_e2e.py`):

- **„Live"-Lauf** (agenten-freie EV-Charger-Demo): `build_tick_loop` mit
  `wiring.inbound_source=buffer`, Write an definiertem Tick gepuffert (A0i); kein
  realer Socket (die S1b-E2E deckt Master→Buffer bereits ab).
- **Materialisieren**: `materialize_inbound_writes(capture())` → `commands`-Block
  → neues `Scenario`.
- **Replay 2x** (reiner A0s-Pfad, kein `inbound_source`) → **byte-identisch** +
  deckungsgleich mit der „Live"-Ziel-Telemetrie (Materialisierung **faithful**).
- **Pin-neutral** ohne Inbound-Write (leerer Buffer → A0i No-op).

### Gepinnte Design-Entscheidung: Materialisierungs-Grenze ([`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md) §7)

Die **Live**-Ordnung ist `scenario→agent→inbound` (A0i, inbound **nach** Agent,
last-wins) — gepinnt in `test_pre_tick_command_order_is_scenario_then_agent_then_
inbound`. Die Materialisierung legt Inbound-Writes in den `commands`-Block = **A0s**
= **vor** Agent. **Konsequenz:** fuer ein Ziel **ohne** Agent im selben Tick ist der
Replay **faithful** (A0i-Live == A0s-Replay). Kommandiert ein Agent dasselbe Ziel im
selben Tick, gewinnt live der Inbound, im Replay der Agent → **Divergenz**.
**Entscheidung (mit User bestaetigt 2026-07-13):** als **bewusste Modell-B-Grenze**
akzeptiert + mit Pin-Test dokumentiert (HIL+Agent-auf-gleichem-Ziel ist heute kein
realer Bedarf; eine A0i-treue Materialisierung waere Option-A-Territorium, §2.6/§7
der Folge-ADR).

## DoD

- Ein Master-Write erreicht das Zielgeraet als `Command` am erwarteten Tick;
  das Geraet reagiert sichtbar (Snapshot/Telemetrie).
- **Determinismus belegt:** der erfasste Write-Strom ist reproduzierbar → zwei
  Laeufe byte-identisch (das Kern-Risiko, das die Ausgliederung ueberhaupt
  begruendet).
- Snapshot-Grenze respektiert oder in der Folge-ADR bewusst amendiert.
- Pin-neutral ohne Inbound-Writes; `make gates` + `make docs-check` +
  `make fullbuild` gruen.
- **Release-Entscheidung:** ja (Minor); SemVer-Ziel naechster Minor nach
  [`074`](074-field-server-modbus-server-adapter.md).

## Bezug

- [`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md)
  (Kern-Entscheidung: Modell B, Determinismus-Vertrag, A0i-Ordnung, Snapshot-Grenze).
- [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §7
  (Ausgliederungs-Begruendung).
- [`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md) (Vor-Tick-
  Command-Naht) + [`ADR 0013`](../../adr/0013-device-model-protocol.md)
  (`apply_command`) + [`ADR 0012`](../../adr/0012-api-simulation-two-processes.md)
  (Prozess-Grenze).
- [`GG-TEST-004`](../../../../spec/lastenheft.md#gg-test-004) (HIL,
  vollstaendige SUT-Steuerbarkeit).
- Vorgaenger: [`074`](074-field-server-modbus-server-adapter.md).

## Risiken

- **Kern-Risiko = Determinismus** — genau der Grund der Ausgliederung; die
  Folge-ADR muss ein tragfaehiges Exogen-Input-Recording liefern, bevor Code
  entsteht.
- **Snapshot-Vertrag** — Option A koennte den [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
  §2.5-Stateless-Default amendieren (Schema-Bump-Pfad wie [`ADR 0030`](../../adr/0030-device-protocol-port-surface.md)
  §2.3).
- **Sicherheit** — beschreibbarer Feldbus ohne Auth; Nur-Sim-Netz-Note
  ([`GG-SAFE-007`](../../../../spec/lastenheft.md#gg-safe-007)).

## Offen / Trigger-Kandidaten

- **Env-var-Lifespan-Naht (Read + Write).** Der Modbus-Server (Read aus 074 **und**
  der Write-Pfad aus S1b) ist auf **In-Process-Naht-Hoehe** verdrahtet
  (`ModbusDeviceServerAdapter` + `DemoTickLoopDriver.device_server_provider` +
  `TickLoopWiring.inbound_source`), aber **nicht** als env-var-Opt-in im
  Composition-Root (`_demo_scenario_setup.py`) wie die Push-Seite
  (`GRID_GYM_FIELD_PUBLISH_MQTT_BROKER`). 074 hat das fuer Read bewusst nicht
  geliefert; S1b haelt die Symmetrie. Eine gemeinsame Read+Write-Lifespan-Naht
  (inkl. `write_map`-Config-Parsing) ist ein **Trigger-Kandidat**, wenn ein
  End-to-End-`make demo`-Master-Write gebraucht wird.
- **Quality-Fault-artige Payload-Validierung** am Write-Rand: der Decoder verwirft
  nicht-endliche `float32`, validiert aber keinen fachlichen Wertebereich (das
  Geraet klemmt/ignoriert selbst, `apply_command`-Vertrag). Analog zur bekannten
  HTTP-Runtime-Injection-Grenze.

## Aktivierung

Aktiviert nach [`074`](074-field-server-modbus-server-adapter.md)-Closure
(2026-07-12) → `in-progress/`. **S2-Closure + `make fullbuild` gruen (2026-07-13)
→ `done/`.**
