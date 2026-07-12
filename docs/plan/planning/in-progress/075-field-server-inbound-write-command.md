# 075 — Field-Server Inbound-Write→Command (Exogen-Input-Recording)

**Status:** **Aktiv — in Arbeit (`in-progress/`, seit 2026-07-12).** Baut auf
[`074`](../done/074-field-server-modbus-server-adapter.md) (`DeviceServerPort`
Read-Serving, done) auf. Ausgegliedert aus dem urspruenglichen 074-Scope, weil
der Determinismus-Vertrag eigenes Design + eine dedizierte Folge-ADR braucht
([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §7).
**Fortschritt:** S0 ✓ (Folge-[`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md)
`Proposed`, **Modell B**) · **S1a ✓** (Kern-Naht: Vor-Tick-Schritt A0i +
`InboundCommandPort` + `InboundCommandBuffer`/Capture, unit-getestet) · S1b/S2
offen (Modbus-Write-Handler + Driver-Wiring + Materialisierung).
**Datum:** 2026-07-12
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

- Read-Serving ([`074`](../done/074-field-server-modbus-server-adapter.md)) ist replay-
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
| **S1b** | **Modbus-Write + Wiring + Materialisierung:** Modbus-Write-Register (FC06/FC16) am Server-Adapter-Rand → dekodieren → `InboundCommandBuffer.enqueue` (Cross-Thread); Driver-/Composition-Wiring (Buffer als `inbound_source` in den `TickLoop` **und** in den Server-Adapter injiziert); Capture append-only/wall-clock-frei per `run_id` (ueberlebt die [`ADR 0012`](../../adr/0012-api-simulation-two-processes.md)-Prozessgrenze) + Materialisierung in einen Szenario-`commands`-Block. **→ [`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md) `Provisional`** | Implementation |
| **S2** | **Determinismus-E2E:** der erfasste Write-Strom wird in einen Szenario-`commands`-Block **materialisiert** + ueber A0s zweimal abgespielt → byte-identische Telemetrie; Ordnung scenario→agent→inbound belegt. **Closure → [`ADR 0076`](../../adr/0076-inbound-write-exogenous-input-recording.md) `Accepted`** | Implementation |

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
  [`074`](../done/074-field-server-modbus-server-adapter.md).

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
- Vorgaenger: [`074`](../done/074-field-server-modbus-server-adapter.md).

## Risiken

- **Kern-Risiko = Determinismus** — genau der Grund der Ausgliederung; die
  Folge-ADR muss ein tragfaehiges Exogen-Input-Recording liefern, bevor Code
  entsteht.
- **Snapshot-Vertrag** — Option A koennte den [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
  §2.5-Stateless-Default amendieren (Schema-Bump-Pfad wie [`ADR 0030`](../../adr/0030-device-protocol-port-surface.md)
  §2.3).
- **Sicherheit** — beschreibbarer Feldbus ohne Auth; Nur-Sim-Netz-Note
  ([`GG-SAFE-007`](../../../../spec/lastenheft.md#gg-safe-007)).

## Aktivierung

Aktiviert nach [`074`](../done/074-field-server-modbus-server-adapter.md)-Closure
(2026-07-12) → `in-progress/`. Nach S2-Closure + `make fullbuild` →
[`../done/`](../done/).
