# 075 — Field-Server Inbound-Write→Command (Exogen-Input-Recording)

**Status:** **Geplant (`next/`, 2026-07-12)** — konkret geplant, noch nicht
aktiv; **haengt an** [`074`](../in-progress/074-field-server-modbus-server-adapter.md)
(`DeviceServerPort` Read-Serving). Ausgegliedert aus dem urspruenglichen
074-Scope, weil der Determinismus-Vertrag eigenes Design + eine dedizierte
Folge-ADR braucht ([`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md)
§7).
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

- Read-Serving ([`074`](../in-progress/074-field-server-modbus-server-adapter.md)) ist replay-
  sicher (Projektion = reine Funktion der emittierten Telemetrie). **Schreiben**
  bricht das: der Command-Zeitpunkt haengt an der realen Ankunft des Live-Writes,
  nicht an gehashten Scenario-Daten.
- [`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md)-
  Determinismus stammt aus `simulation_time`-**geplanten**, im `scenario_hash`
  erfassten Commands — eine andere Achse als extern getaktete Live-Writes.
- [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §2.5
  verbietet Server-State im Snapshot; ein Write-Record-Pfad muss diese Grenze
  respektieren oder bewusst amendieren.

## Kern-Decision (dedizierte Folge-ADR, Nummer bei Aktivierung vergeben)

Eine **eigene ADR** entscheidet zwischen (mind.) zwei Optionen — der Slice-Start
(S0) zieht sie `Proposed → Provisional`:

- **(A) Write-Journal + deterministische Re-Injektion:** jeder Inbound-Write
  wird mit dem **aufgeloesten Sim-Tick** in ein Lauf-Journal geschrieben; Replay
  speist die Writes aus dem Journal statt vom Live-Master → reproduzierbar. Naht
  in den bestehenden Vor-Tick-Command-Pfad
  ([`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md),
  [`ADR 0013`](../../adr/0013-device-model-protocol.md) `apply_command`).
- **(B) HIL-Live-Run = record-only:** Live-Writes werden als nicht-replaybar
  deklariert; ein Live-Run kann als neues Szenario/Command-Set **materialisiert**
  werden, das dann deterministisch replaybar ist.

Die ADR waehlt/kombiniert und versoehnt das mit
[`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §2.5.

## Slice-Schnitt (rollen-getrennt)

| Slice | Inhalt | Rolle / Artefakt |
| --- | --- | --- |
| **S0** | Dedizierte Folge-ADR `Proposed → Provisional`: Exogen-Input-Recording-Modell (A/B), Determinismus-Vertrag, Snapshot-Grenze | Architect / ADR |
| **S1** | Write→`Command`-Naht: Modbus-Write-Register → Pending-Command ueber den Vor-Tick-Pfad; Sim-Tick-Aufloesung + Journal (Option A) bzw. record-only-Materialisierung (Option B) | Implementation |
| **S2** | **Determinismus-E2E:** derselbe erfasste Write-Strom → byte-identische Telemetrie ueber zwei Laeufe; Reihenfolge scenario-vor-agent-vor-inbound (oder wie in S0 fixiert) | Implementation |

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
  [`074`](../in-progress/074-field-server-modbus-server-adapter.md).

## Bezug

- [`ADR 0075`](../../adr/0075-field-server-surface-device-endpoint-port.md) §7
  (Ausgliederungs-Begruendung).
- [`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md) (Vor-Tick-
  Command-Naht) + [`ADR 0013`](../../adr/0013-device-model-protocol.md)
  (`apply_command`) + [`ADR 0012`](../../adr/0012-api-simulation-two-processes.md)
  (Prozess-Grenze).
- [`GG-TEST-004`](../../../../spec/lastenheft.md#gg-test-004) (HIL,
  vollstaendige SUT-Steuerbarkeit).
- Vorgaenger: [`074`](../in-progress/074-field-server-modbus-server-adapter.md).

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

**Nach** [`074`](../in-progress/074-field-server-modbus-server-adapter.md)-Closure und einem
konkreten HIL-Steuerungs-Bedarf. Bis dahin `next/`. Bei Aktivierung →
[`../in-progress/`](../in-progress/); nach S2-Closure + `make fullbuild` →
[`../done/`](../done/).
