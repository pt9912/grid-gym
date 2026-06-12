# 030 — RL-Adapter ueber den Multi-Agent-Bus (`GG-FUTURE-001/002`)

**Status:** Open — Trigger-Watch (M3-Welle-7-Closure-Restposten
2026-05-25).
**Datum:** 2026-05-25.
**Quelle:** Lastenheft `GG-FUTURE-001/002` (RL-faehiges
Multi-Agent-System); M3-Welle-7-Closure-Notiz in
[`../done/M3-results.md`](../done/M3-results.md) §5.

---

## Trigger

Das Multi-Agent-Subsystem aus M3-Welle 3/4 ist RL-faehig — der
`AgentMessageBus` ([`ADR 0023`](../../adr/0023-agent-bus-protocol.md)) plus die `Agent`-Sub-Protocol-Surface
([`ADR 0023`](../../adr/0023-agent-bus-protocol.md) §2.1) erlauben Agent-Implementer mit beliebigem internen
Verhalten, inklusive RL-Policies. Welle 4b hat mit `RuleBasedAgent`
einen ersten konkreten Implementer geliefert; ein RL-Adapter ist
das naechste konkrete Use-Case-Beispiel.

Der RL-**Trainings-Loop** bleibt **extern** (Gym/PettingZoo,
Ray RLlib, Stable-Baselines3 o. ae.) — der Adapter ist die
Bruecke zwischen einem extern trainierten Policy-Objekt und dem
TickLoop-Vertrag (Agent-Protocol).

## Erwartete Lieferung

- **Adapter-Modul** `src/grid_gym/adapters/driven/rl_agent/` <!-- d-check:ignore (geplant: entsteht mit Trigger-Aktivierung) -->
  (oder `core/agents/rl_agent/`, je nach Architektur-Entscheidung):
  - `RlAgentAdapter` (oder `RlAgent`) implementiert das
    `Agent`-Sub-Protocol; `tick(...)` ruft eine extern injizierte
    Policy-Funktion auf, deren Output zu `Command`-Objekten
    serialisiert wird.
  - Snapshot-bar: das Policy-Objekt wird **nicht** im Snapshot
    serialisiert (Cross-Process-Re-Hydration ist Trainer-
    Verantwortung); Snapshot traegt nur agent-id +
    Configuration-Hash, damit ein Resume die identische Policy
    erwartet.
- **Zielplattform-Triage** (eigener ADR):
  - **Option A: Gym/PettingZoo**-Style API
    (`observation → action`-Loop) als minimaler externer
    Vertrag; passt fuer Single-Agent + Multi-Agent.
  - **Option B: Ray RLlib**-Style API
    (`compute_actions(obs_batch)`); skaliert horizontal.
  - **Option C: Stable-Baselines3**-Style API
    (`policy.predict(obs)`); simpler Single-Agent-Pfad.
- **End-to-End-Demo** im Stil von
  `tests/integration/scenarios/agents_demo.yaml` mit einer
  Trainings-Episode (z. B. BESS-SOC-Management oder Reserve-
  Market-Bid-Strategie).
- **ADR** mit Zielplattform-Decision + Snapshot-Pattern fuer
  Resume-Determinismus.

## Aktivierungs-Kriterium

Aktivierung sobald **eines** der folgenden Ereignisse eintritt:

- **Externe RL-Workload** braucht das `grid-gym`-Simulator als
  Trainings-Environment (z. B. ein Forschungs-Use-Case oder eine
  Demo).
- **BESS-Simulation-Reserve-Market-Spike** (Trigger 026,
  [`open/026-bess-simulation-reserve-market-spike.md`](026-bess-simulation-reserve-market-spike.md))
  wird aktiv und braucht einen RL-Strategie-Implementer.
- **Multi-Agent-Erweiterungs-Slice** (Welle 4c+) bringt das als
  konkrete Folge-Welle ein.

## Wandert nach

- `next/`, sobald die Zielplattform-Triage eine Decision hat und
  ein Slice-Plan vorliegt,
- `in-progress/`, wenn das Slice aktiv geplant ist,
- `done/`, wenn das Adapter-Modul + End-to-End-Demo + ADR
  produktiv sind.

## Bezug

- Lastenheft `GG-FUTURE-001/002` (RL-faehiges Multi-Agent-
  System).
- [`ADR 0023`](../../adr/0023-agent-bus-protocol.md) (`AgentBus Protocol`) §2.1 — `Agent`-Sub-Protocol-
  Surface, die der RL-Adapter implementieren wird.
- [`ADR 0026`](../../adr/0026-agent-drain-registry-pattern.md) (`Agent Drain Registry Pattern`) — Registry +
  Lifecycle-Pattern fuer den RL-Adapter (`_attach_agents()` +
  `set_run_id` + optional `_RandomAttachableAgent.attach_random`
  fuer deterministischen Trainings-Replay).
- [`ADR 0027`](../../adr/0027-rule-based-agent-scenario-pattern.md) (`Rule-Based Agent Scenario Pattern`) — Pattern-
  Pendant; RL-Adapter ist ein Schwester-Implementer zu
  `RuleBasedAgent`.
- M3-Welle-7-Closure in
  [`../done/M3-results.md`](../done/M3-results.md) §5 fuehrt
  diesen Trigger als M3-Restposten.
