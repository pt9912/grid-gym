# Scenario-Scheduled Device Commands (schliesst Trigger 046)

**Status:** **Abgeschlossen (`done/`, 2026-06-18)** — S0..S3 geliefert;
[`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md) `Accepted`.
`commands`-Block + ScenarioCommandEngine + TickLoop-A0s-Naht + 4 nicht-idle
SOLLTE-E2E; Trigger 046 mit-geschlossen. `make gates`/`make docs-check`/`make
fullbuild` gruen.
**Datum:** 2026-06-18
**Quelle:** [Trigger 046](046-command-driven-integration-e2e.md) (Forward-Gap
aus M8-Welle-2a..2d): die vier SOLLTE-Geraete fahren idle, weil der `devices`-Layer
keinen scenario-scheduled-Command-Mechanismus kennt.

---

## Ziel

Einen scenario-deklarierten, tick-genauen Command-Zeitplan (`commands`-Block,
analog `faults`) einfuehren und damit je SOLLTE-Geraet
([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015)..018) einen **nicht-idle**
Command-E2E fuehren (Snapshot-Assertion auf die Geraete-Reaktion).

## Kontext / Ist

- Commands erreichen `apply_command` heute nur ueber Agents
  ([`ADR 0027`](../../adr/0027-rule-based-agent-scenario-pattern.md)) + Inline-Load-
  Overlay; **kein** scenario-deklarierter `devices`-Command-Pfad.
- Faults sind das Template: `faults`-Block → `ScenarioFault` →
  [`ScenarioFaultEngine`](../../adr/0059-generic-scenario-fault-engine.md) →
  `TickLoop` Schritt A2.
- Command-Apply-Pfad existiert: `_pending_agent_commands` → `_apply_pending_agent_commands`
  → `_device_by_id[target].apply_command` (wird wiederverwendet).

## Kern-Decision ([`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md))

Top-Level-`commands`-Block (mirror `faults`), Punkt-in-der-Zeit (`simulation_time`,
kein Fenster), `ScenarioCommand`-Domain + `Scenario.commands` (default leer,
pin-neutral), `ScenarioCommandEngine` + Vor-Tick-Naht (scenario-Commands vor
Agent-Commands), `scenario_hash` deckt `commands` ab (Variante A, Decimal-Strings).

## Slice-Schnitt (rollen-getrennt)

| Slice | Inhalt | Rolle / Artefakt |
| --- | --- | --- |
| **S0** ✓ | [`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md) `Proposed → Provisional` (2026-06-18); Schema/Platzierung/Determinismus-Reihenfolge mitgetragen. `Accepted` bei Closure | Architect / ADR |
| **S1** ✓ | `commands`-Schema + `ScenarioCommand`-Domain + `Scenario.commands` + Loader (`_build_commands`/`_build_command`) + Validator-Strang + `scenario_yaml`-Decimal-Coercion der Payloads + `canonical_json`/`scenario_hash`-Abdeckung. Pins: Happy/Boundary/Negative (inkl. unbekanntes `target` → Reject; pin-neutral ohne `commands`) | Implementation |
| **S2** ✓ | `ScenarioCommandEngine` (`due_commands(context)`) + `TickLoop`-Vor-Tick-Naht (faellige Commands → Apply-Pfad, scenario-vor-Agent-Reihenfolge) + `build_tick_loop`-Verdrahtung aus `scenario.commands`. Pins: tick-genaue Zustellung, Reihenfolge-Determinismus, Resume-Kontinuitaet | Implementation |
| **S3** ✓ | **Nicht-idle Integration-E2E je SOLLTE-Geraet** (Trigger-046-Closure): EV (`set_charge_power` → `power_kw`), Transformer (`set_power_kw` → `primary_power_kw`), Diesel (`set_power_kw` → `power_kw`/`running`), Wind (`IGNORED`-Beleg). Bestehende Idle-Smokes bleiben (pin-neutral) | Implementation |

## DoD

- Ein Szenario plant ein Command tick-genau an ein SOLLTE-Geraet; das Geraet
  reagiert sichtbar im Snapshot/Telemetrie am geplanten Tick.
- Determinismus: gleicher `scenario_hash` + Seed → identische Command-Zustellung →
  byte-identische Telemetrie ([`GG-SIM-001`](../../../../spec/lastenheft.md#gg-sim-001)/004,
  [`GG-MVP-002`](../../../../spec/lastenheft.md#gg-mvp-002)).
- Pin-neutral: Szenarien ohne `commands` → `scenario_hash` + alle Bestands-Pins
  (inkl. vier SOLLTE-Idle-Smokes) bit-genau unveraendert.
- `make gates` + `make docs-check` gruen; Wellen-Closure zusaetzlich `make fullbuild`.

## Entsperrt

[Trigger 046](046-command-driven-integration-e2e.md) (S3-Closure → `done/`).

## Risiken

- **Reihenfolge-Determinismus** scenario- vs. Agent-Commands → in
  [`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md) §2.3 festgelegt
  (scenario vor Agent), Pin in S2.
- **Hash-Drift**: `commands`-Feld defaultet leer → keine Drift fuer Bestands-
  Szenarien; explizit pin-neutral-getestet (S1).
- **Wind ohne Command-Surface** → E2E belegt nur `IGNORED` (kein State-Delta);
  bewusst, in [`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md)
  §2.5 verankert.

## Bezug

- [`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md) (Architektur).
- [`ADR 0022`](../../adr/0022-fault-injection-protocol.md)/[`ADR 0059`](../../adr/0059-generic-scenario-fault-engine.md)
  (Fault-Template) + [`ADR 0013`](../../adr/0013-device-model-protocol.md)
  (`apply_command`) + [`ADR 0027`](../../adr/0027-rule-based-agent-scenario-pattern.md)
  (Agent-Command-Pfad) + [`ADR 0021`](../../adr/0021-scenario-loader-and-tick-loop-event-wiring.md)
  (Loader/TickLoop-Naht).

## Aktivierung

Aktiviert 2026-06-18 (S0). S1..S3 geliefert; die Wellen-Closure (alle Slices Done
+ `make fullbuild` gruen) hat den Plan + Trigger 046 am 2026-06-18 nach `done/`
bewegt.
