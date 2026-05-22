# Welle 4a — Multi-Agent-Foundation-Plumbing

**Status:** Done — M3-Welle-4a-Closure am 2026-05-21
(`a24f733..da18c6d`, 6 Welle-4a-Kern-Commits + 3 User-Polish-
Commits + diesem C3-Status-Sync). Welle 4a liefert die
Multi-Agent-Foundation-Plumbing-Schicht; Welle 4b folgt mit
konkreten Agent-Implementern und End-to-End-Gate.

**DoD-Verifikation (Welle-Schluss):**

- `make test-unit`: **921 Tests gruen** (Welle-3-Endstand 889
  → +32 Welle-4a-Tests; davon 4 in `test_bus.py`
  (`consume_for`), 9 in `test_tick_loop_welle_4a_agent.py`
  (Konstruktor-Kwarg + Auto-Bus + Duplicate-ID), 3 in
  `test_tick_loop_welle_4a_drain.py` (A0v/A0a), 5 in
  `test_tick_loop_welle_4a_lifecycle.py` (`_attach_agents`),
  9 in `test_tick_loop_welle_4a_snapshot.py` (Agent-
  Foundation-State-Snapshot), 2 in
  `test_loader_welle_6b.py` (Builder-Symmetrie)).
- `make test-integration`: **14 Tests unveraendert gruen**
  (Welle-4a-Foundation hat keine neuen Integration-Tests;
  Welle-4b-End-to-End-Demo folgt).
- `make gates`: **A-1 gruen** ohne Override (lint,
  format-check, mypy `--strict`, arch-check 16/16, coverage
  94.94 % line / >90 % branch, critical-coverage `core/agents`,
  dep-audit).
- ADR 0026: `Proposed → Provisional` (Schwester-ADR zu
  ADR 0023; Pattern-Pendant zu ADR 0025 fuer Welle-2-
  Konkretisierung).
- AC-PORTS-NO-OUT bleibt KEPT (16 Contracts).
- Welle-3-`_set_agents_for_testing(...)`-Helper entfernt:
  `grep -rn "_set_agents_for_testing" tests/ src/` ist leer.

Welle 4 ist die produktive Konkretisierung des Multi-Agent-
Subsystems und wird in zwei Teilwellen geliefert (Sub-Slicing
nach M3-Slice-Plan §3 Sub-Slicing-Schwelle: 6+ Items mit ≥ 2
echten Architektur-Entscheidungen):

- **Welle 4a — Foundation-Plumbing** (dieses Dokument):
  ADR 0026 + TickLoop-Registry-API + Schritt-A0-Pre-Tick-Drain
  + `consume_for`-Bus-Eviction + Lifecycle-Hook +
  TickLoop-Agent-Foundation-State-Snapshot. **Keine** konkreten
  Agent-Implementer.
- **Welle 4b — RuleBasedAgent + Scenario-Schema**: konkrete
  Implementer + `agents`-Top-Level-Block + Property-Tests +
  Sub-Snapshot-Slot + End-to-End-Demo-Szenario +
  Welle-4-Gate (`make fullbuild` ohne Override).

Pattern: spiegelt M3-Welle-1 (Fault-Foundation) → M3-Welle-2
(Fault-Konkretisierung) eins zu eins für Agenten.

Kanonische Slice-Spezifikation:
[`M3-faults-agents-observability.md §3 Welle 4`](../in-progress/M3-faults-agents-observability.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht als Ersatz.

**Commit-Sequenz (geplant):**

- Pre-C0 `a24f733` — `chore(welle-4a): git mv welle-3.md → done/welle-3.md` (rename-only).
- C0 (dieses Dokument + M3-Sub-Slicing-Sync) —
  `docs(plan): welle-4a Slice-Doc`.
- C1 — `docs(adr): ADR 0026 Proposed — Agent-Drain + Registry
  + Snapshot + Lifecycle`.
- C2 — `feat(welle-4a): TickLoop-agents-Kwarg + Schritt-A0-
  Drain + AgentMessageBus.consume_for + Agent-Foundation-State-
  Snapshot + Lifecycle + Tests`.
- C3 — `docs(plan): Welle-4a Status/DoD-Sync` (ADR 0026 →
  Provisional, M3-Plan §3 Welle-4a-Done-Tag, welle-4a.md →
  Done; M3-Welle-4b als nächster Schritt vermerkt).

## 1. Context

M3-Welle-3 (`3dbe6af..6f8b09b`) hat die Multi-Agent-Foundation
produktiv abgeschlossen: `Agent`-Sub-Protocol +
`AgentMessageBus`-Core-Klasse + `AgentMessage`-frozen-
dataclass + TickLoop-Schritt-D2-Hook + `agent_bus`-Builder-
Symmetrie + `AgentBusError`-Family + Welle-3-Foundation-
Pending-Buffer (`_pending_agent_commands`). 889 Unit-Tests +
14 Integration-Tests; `make gates` A-1 ohne Override grün.

Vier Review-Folgen haben Welle-3-Foundation auf den heutigen
Stand gebracht — alle Findings wurden adressiert; mehrere
Pflicht-Themen wurden explizit nach Welle 4 verschoben.

ADR 0023 §4/§6/§7 + Welle-3-Review-Folgen 1-4 listen die
Welle-4-Forward-Pointer auf (siehe §2 In-Scope). Welle 4a
deckt **die Foundation-Plumbing-Schichten** ab — alles, das
keinen konkreten Agent-Implementer braucht. Welle 4b
liefert dann den RuleBasedAgent + Scenario-Schema +
End-to-End-Pfad.

## 2. Scope

**In Scope (Welle 4a):**

1. **ADR 0026** (geplant) — Agent-Drain + Registry +
   Snapshot + Lifecycle-Pattern als eigene ADR (analog ADR
   0025 zu ADR 0022 für Recovery-Pattern). Status-Lifecycle:
   - `Proposed` mit Welle-4a-C1 (separater
     `docs(adr)`-Commit).
   - `Provisional` mit Welle-4a-C3-Closure (nach dem
     C2-Code-Commit).
   - `Accepted` mit M3-Welle-7-Closure (gemeinsam mit
     ADR 0023 und Welle-4b-ADR-Folge oder einzeln, je nach
     Welle-7-Sequenzierung).
2. **TickLoop-Konstruktor erhält produktiven
   `agents`-Kwarg**:
   - `agents: tuple[Agent, ...] = ()` (keyword-only, analog
     `devices=`, `active_load_events=`, etc.).
   - Welle-3-Test-Helper `_set_agents_for_testing(...)` wird
     entfernt — Tests stellen via Konstruktor-Kwarg um.
   - Agent-IDs werden im Konstruktor eindeutig validiert;
     Duplikate werfen typisiert `AgentDuplicateIdError`.
   - Kopplung mit `agent_bus`: Wenn `agents != ()` und
     `agent_bus is None`, erzeugt der Konstruktor einen echten
     `AgentMessageBus`. `agent_bus=None` bleibt nur fuer
     agentenlose Runs der Skip-Pfad. Damit kann ein produktiver
     `agents`-Tuple nicht still als No-op registriert werden.
3. **`_attach_agents()`-Lifecycle-Hook** im
   TickLoop-Konstruktor (analog `_attach_devices()`):
   - Ruft `agent.set_run_id(self._run_id)` für jeden
     Agent.
   - Ruft `agent.attach_random(self._random.sub_port(
     f"agent-{agent_id}"))` für jeden Agent, der das
     optionale `_RandomAttachableAgent`-Sub-Protocol
     implementiert (`isinstance`-Check). Nicht alle Agent-Typen
     brauchen einen eigenen Random-Stream. Damit ist die
     Welle-3-Review-
     Folge-M-3-Konvention produktiv umgesetzt.
4. **Optionales Random-Lifecycle-Sub-Protocol** unter
   `src/grid_gym/hexagon/core/agents/_protocol.py`:
   `_RandomAttachableAgent.attach_random(random: RandomPort)
   -> None` (analog `SmartMeterDevice.attach_sources`-
   Pattern, ADR 0018 §2.4). Das Protocol ist
   `@runtime_checkable`, weil `_attach_agents()` es per
   `isinstance(agent, _RandomAttachableAgent)` prueft. **Keine
   Erweiterung der `Agent`-Pflicht-Surface**, damit
   RuleBasedAgents ohne Stochastik den Hook nicht
   implementieren müssen.
5. **TickLoop-Schritt A0 (Pre-Tick-Agent-Command-Drain)**:
   - Position: zweigeteilt am Tick-Start. **A0v** validiert vor
     `clock.advance(...)`/`scheduler.pop_due(...)` alle
     `target_device_id`-Lookups der aktuellen
     `self._pending_agent_commands` gegen `_device_by_id`.
     **A0a** wendet die bereits validierte Command-Liste nach
     `clock.advance(...)` und `scheduler.pop_due(...)`, aber
     **vor** Step-A-Baseline/Profile/Event, per
     `apply_command(...)` auf die Ziel-Devices an.
   - Verhalten: kopiert den Pending-Buffer in eine lokale
     `commands_to_apply`-Tuple, validiert alle Targets ohne
     Tick-/Scheduler-/Device-Mutation, wendet danach alle
     Commands in Buffer-Reihenfolge an und leert
     `self._pending_agent_commands` erst nach erfolgreichem
     Apply-Durchlauf. `AgentInvalidCommandTargetError` darf
     deshalb keine bereits fortgeschrittene Clock, keine
     gepoppten Scheduler-Events und keine partiell angewendeten
     Agent-Commands hinterlassen. Andere `apply_command(...)`-
     Exceptions sind kein `AgentInvalidCommandTargetError`-Pfad:
     In-Contract-Devices melden fachliche Ablehnung als
     `CommandResult`, waehrend Exceptions (z. B. Pre-init-
     Vertragsverletzungen) durchgereicht werden; Welle 4a
     verspricht dafuer keine Rollback-Atomizitaet, laesst den
     Pending-Buffer aber ungeleert.
   - Vertrag: Agent-Commands der vorigen Ticks werden in der
     **aktuellen** Tick in den Device-Command-Pfad eingespeist
     (GG-AGENT-008 Commit-Reihenfolge-Invariante: Commands
     werden nicht im selben Tick verarbeitet, in dem sie emittiert
     wurden). Der final beobachtbare Device-State folgt danach
     weiterhin der bestehenden TickLoop-Praezedenz aus Schritt A/C.
   - Reihenfolge bei Konflikt mit LoadDevice-Baseline:
     **Agent-Commands zuerst** (Schritt A0), dann Schritt-A-
     Baseline fuer jedes `LoadDevice`. Die Baseline gewinnt auf
     LoadDevices, weil `_consume_load_inputs_into(...)` pro Tick
     den `rated_power_kw`-Intent neu berechnet und per
     `apply_command(...)` setzt; ein Agent-Command auf ein
     `LoadDevice` ist damit nur dann final sichtbar, wenn ein
     spaeteres Profil/Event denselben Wert setzt oder die
     Baseline-Regel in einer Folge-ADR geaendert wird.
   - Reihenfolge bei Konflikt mit LoadEvent-Overlay:
     **Agent-Commands zuerst** (Schritt A0), dann LoadEvent-
     Overlay (Schritt A). LoadEvent gewinnt im selben Tick
     auf demselben Device — konsistent mit Welle-6b-Pattern
     „Event-Overlay nach Baseline".
   - Reihenfolge bei Konflikt mit GridConnection-Auto-Close:
     Ein Agent-Command auf eine `GridConnectionDevice`-ID zaehlt
     als manueller GridConnection-Override fuer diesen Tick und
     ergaenzt `manual_override_grid_ids`, damit Schritt C den
     Agent-Wert nicht direkt wieder ueberschreibt. LoadEvent-/
     Profile-Overlay auf derselben GridConnection-ID gewinnt
     weiter, weil Schritt A nach A0 laeuft.
6. **`AgentMessageBus.consume_for(receiver: str) ->
   Sequence[AgentMessage]`** (destruktive Direct-Inbox-Drain-
   Variante):
   - Liefert alle direkt an `receiver` adressierten Nachrichten
     (`message.receiver == receiver`) in derselben Sortierung wie
     `drain_for(...)` **und entfernt nur diese** aus dem Buffer.
   - `receiver="*"` bleibt wie bei `drain_for("*")` unzulaessig
     und wirft `AgentBusInvalidReceiverError`.
   - Broadcasts (`message.receiver == "*"`) bleiben in Welle 4a
     bewusst nicht-destruktiv und werden weiter nur ueber
     `drain_for(receiver)` ausgeliefert. Ein destruktiver
     Erstkonsum von Broadcasts wuerde andere Receiver
     abschneiden; registry-aware Fan-out/Watermark bleibt
     Welle 4b oder spaetere Folge.
   - Implementiert die Welle-3-Review-Folge-M-4-Eviction-Spec
     fuer private Agent-Inboxes, ohne Broadcast-Semantik zu
     brechen.
   - Snapshot-Schema-Erweiterung: kein Bump v1 → v2 noetig,
     solange kein `consumed_sequences`-/Watermark-State
     persistiert wird; Buffer-Inhalt wird nach Konsumption
     kleiner, aber das Schema-Format bleibt unverändert.
7. **TickLoop-Agent-Foundation-State-Snapshot**:
   - `TickLoop.snapshot()` hängt `agent_bus` als Sub-Snapshot ein,
     sobald `_agent_bus is not None`; verwendet wird das bereits in
     Welle 3 definierte `AgentMessageBus`-v1-Schema.
   - `TickLoop.snapshot()` hängt `pending_agent_commands` als
     Sub-Snapshot ein, sobald der Buffer nicht leer ist. Format:
     `{"version": 1, "commands": [...]}` mit den `Command`-
     Pflichtfeldern (`command_id`, `simulation_time`,
     `target_device_id`, `type`, `payload`, `validation_status`,
     `result`). `result` wird als `CommandResult`-Stringwert
     serialisiert und beim Restore typisiert zurückgeparst;
     `payload` muss canonical-json-faehig bleiben (Mapping mit
     erlaubten Snapshot-Werten, analog bestehender Command-/
     Event-Payload-Grenzen).
   - `TickLoop.from_snapshot(...)` rekonstruiert `agent_bus` und
     `_pending_agent_commands`, falls die Sub-Snapshots vorhanden
     sind. Fehlen sie und werden **keine** `agents` injiziert,
     bleibt der bestehende Welle-6a-Resume-Pfad unverändert
     (`agent_bus=None`, Pending-Buffer leer). Fehlt `agent_bus`,
     aber `agents != ()` wird injiziert, greift bewusst dieselbe
     Auto-Bus-Regel wie im Konstruktor: Restore erzeugt einen
     leeren `AgentMessageBus`, damit die injizierten Agents im
     Folgetick nicht still als No-op registriert sind. Das ist
     backward-kompatibel, weil alte Aufrufer ohne `agents=...`
     unverändert `agent_bus=None` bekommen.
   - Damit Pending-Commands nach Resume wirklich auf Devices
     wirken koennen, erhaelt `from_snapshot(...)` optionale
     Runtime-Dependency-Kwargs analog zum Konstruktor:
     `devices=()`, `grid_model=None`, `active_load_events=()`,
     `active_load_profiles=()`, `fault_port=None`, `agents=()`.
     Ohne diese Kwargs bleibt der heutige Welle-6a-Pfad ohne
     Devices/grid_model erhalten; mit ihnen wird der
     produktive Resume-Pfad fuer Welle 4a getestet.
   - Resume-Match-Checks: Wenn der Snapshot `devices.<type>.<id>`-
     Sub-Snapshots enthält und `devices` injiziert wird, muessen
     injizierte Device-IDs und Device-Typen exakt zu den
     Snapshot-Keys passen **und** jedes `device.snapshot()` muss
     exakt zum jeweiligen `devices.<type>.<id>`-Snapshot-State
     passen; sonst wuerde ein frisches Device mit gleicher ID als
     verlustfreier Resume durchgehen. Wenn der Snapshot einen
     `grid_model`-Sub-Snapshot enthält und `grid_model` injiziert
     wird, muss `grid_model.snapshot()` exakt zum Snapshot-State
     passen; sonst wuerde ein frisches GridModel als verlustfreier
     Resume durchgehen. Wenn ein `grid_model`-Sub-Snapshot
     vorhanden ist und nicht-leere `active_load_events`/
     `active_load_profiles` injiziert werden, muessen die
     injizierten Tupel exakt zum darin persistierten Overlay-State
     passen; Abweichungen werfen typisiert. Fehlt ein
     `grid_model`-Sub-Snapshot, bleiben Overlay-only-Szenarien ohne
     GridModel weiterhin gueltig: `from_snapshot(...)` darf die
     injizierten Overlay-Tupel in den Konstruktor durchreichen,
     verspricht aber keine snapshot-gestuetzte, verlustfreie
     Overlay-Validierung. Bei
     nicht-leerem `pending_agent_commands`-Sub-Snapshot und
     produktivem Resume muss jedes `target_device_id` in den
     injizierten Devices existieren; sonst wirft der Restore/erste
     Tick typisiert, statt einen scheinbar verlustfreien Resume mit
     frischen oder falschen Instanzen vorzutäuschen.
   - **Keine** konkreten Agent-Instanz-Snapshots in Welle 4a:
     `agents.<agent_type>.<agent_id>` bleibt Welle 4b, weil erst
     konkrete Implementer eigene Snapshot-Verträge liefern.
     Welle 4a verspricht deshalb **keinen** verlustfreien Resume
     beliebiger Agent-Instanz-Zustände; verlustfrei ist nur der
     generische Foundation-State (`agent_bus` +
     `pending_agent_commands`) plus die validierten Runtime-
     Dependencies.
   - Grund: Welle 4a macht `agents=` und den Pre-Tick-Drain
     produktiv. Ohne Persistenz für Bus + Pending-Buffer würde ein
     Snapshot zwischen Agent-Tick und Folgetick Commands bzw.
     Nachrichten verlieren.
8. **`build_tick_loop(..., agents=...)`-Builder-Symmetrie**:
   - Scenario-Loader-Builder erhält
     `agents: tuple[Agent, ...] = ()`-Kwarg (analog Welle-3
     `agent_bus`).
   - `agent_bus` bleibt optionaler Override; bei nicht-leeren
     `agents` greift dieselbe Auto-Bus-Regel wie im
     TickLoop-Konstruktor.
   - Wenn `grid_model_config` vorhanden ist, baut der Builder
     `GridModelBilanz(scenario.grid_model_config,
     active_load_events=scenario.load_events,
     active_load_profiles=scenario.load_profiles)`. Das macht den
     bereits existierenden GridModel-v2-Overlay-Snapshot zur
     Single Source of Truth fuer die Welle-4a-Resume-Match-Checks;
     ohne diese Verdrahtung wuerden produktive Scenario-Overlays im
     TickLoop laufen, aber nicht im `grid_model`-Sub-Snapshot
     auftauchen. `grid_model_config` wird dadurch nicht zur Pflicht:
     Overlay-only-Szenarien ohne GridModel bleiben gueltig, haben
     aber keinen snapshot-gestuetzten Overlay-Match-Check.
   - Default `()`-Tuple; Welle-4b-Scenario-Loader wird die
     Agent-Factory-Map (analog `_DEVICE_FACTORIES`) hier
     instanziieren.
9. **Agent-Registry-Errors** unter
   `src/grid_gym/hexagon/core/errors.py`: neue
   `AgentRegistryError(GridGymError)`-Root plus
   `AgentDuplicateIdError` — wird im TickLoop-Konstruktor
   geworfen, wenn `agents` doppelte `agent_id`-Werte enthält.
   Das macht die Welle-3-Helper-Defensive produktiv und
   typisiert, ohne Registry-Fehler als Bus-Fehler zu labeln.
10. **Agent-Command-Drain-Errors** unter
   `src/grid_gym/hexagon/core/errors.py`: neue
   `AgentCommandDrainError(TickLoopError)`-Root plus
   `AgentInvalidCommandTargetError` — wird in Schritt A0
   geworfen, wenn ein Agent-Command auf eine `target_device_id`
   zielt, die im `_device_by_id`-Lookup nicht existiert. Das ist
   ein TickLoop-/Device-Registry-Mismatch, kein
   `AgentMessageBus`-Vertragsfehler. Welle-3-Pending-Buffer hat
   keinen Validator; Welle 4a haertet das Fail-Fast.
11. **TickLoop-Agent-Snapshot-Format-Errors** unter
   `src/grid_gym/hexagon/core/errors.py`:
   `TickLoopAgentSnapshotMissingKeysError`,
   `TickLoopAgentSnapshotWrongTypeError`,
   `TickLoopAgentSnapshotInvalidCommandResultError`,
   `TickLoopAgentSnapshotDeviceMismatchError`,
   `TickLoopAgentSnapshotGridModelMismatchError` und
   `TickLoopAgentSnapshotLoadOverlayMismatchError`. Alle erben von
   `TickLoopSnapshotFormatError` oder einer bestehenden
   TickLoop-Snapshot-Root und werden fuer
   `pending_agent_commands`-/Runtime-Dependency-Mismatches im
   TickLoop-Resume-Pfad genutzt. Malformed `agent_bus`-Sub-
   Snapshots werden bewusst an `AgentMessageBus.from_snapshot(...)`
   delegiert; dessen bestehende `AgentBusSnapshot*`-Errors
   propagieren unwrapped. TickLoop-eigene Agent-Snapshot-Errors
   decken nur Agent-Foundation-State ab, den TickLoop selbst
   parst oder gegen Runtime-Dependencies matcht. Damit leaken
   `CommandResult(...)`-Parsefehler nicht als roher `ValueError`
   aus `from_snapshot(...)`.

**Anti-Scope (Welle 4b):**

- Konkrete `Agent`-Implementer (`RuleBasedAgent` o. ae.).
- Agent-Decision-Logik (Welt-Zustand-Konsum → Command-
  Produktion).
- `agents`-Top-Level-Block im Scenario-Schema +
  `_assert_agent_list`-Validator + `ScenarioAgent`-Domain-
  Modell.
- Konkrete Agent-Instanz-Snapshots (`agents.<agent_type>.
  <agent_id>`) in `TickLoop.snapshot()` — Welle 4a persistiert
  nur generischen Agent-Foundation-State (`agent_bus`,
  `pending_agent_commands`); Welle 4b fügt konkrete
  Implementer-Snapshots additiv per ADR 0015 §2.3 ein.
- Agent-Factory-Map analog `_DEVICE_FACTORIES`.
- Property-Determinismus-Tests pro Agent-Implementer
  (`GG-AGENT-003`).
- Welle-4-Abschluss-Gate (`make fullbuild` ohne Override
  mit End-to-End-Demo-Szenario).

**Anti-Scope (nach Welle 4a: Welle 4b, Welle 5/6 oder
spaetere Folge):**

- Deadlines (`GG-AGENT-007`) — bleibt explizit
  out-of-scope. Welle 4b kann das aufnehmen, wenn
  RuleBasedAgent das braucht; sonst eigene Folge-Slice
  (typischerweise Welle 4c oder M5).
- Async-Kommunikation (`GG-AGENT-008`) — ADR-Folge zu
  ADR 0007 `AsyncRandomPort`, kein Welle-4-Material.
- LogPort/MetricsPort-Injektion in Bus/Agent — Welle 5/6.
- Sub-Seed-Wortbreite (Trigger 011) — bleibt in `open/`.
- RL-Adapter (`GG-FUTURE-001/002`).
- In-Tick-Wirksamkeit (Agent-Commands wirken in derselben
  Tick) — eigene ADR-Folge.
- Multi-Receiver-Watermark für `consume_for(...)`-
  Per-Receiver-Tracking bei Broadcasts; Welle 4a haelt das
  Tracking nicht vor und konsumiert deshalb nur direkt
  adressierte Nachrichten destruktiv. Welle 4b oder spaetere
  Slice verfeinert registry-aware Fan-out/Eviction.

## 3. Architektur-Entscheidungen

Welle 4a bringt **eine neue ADR**: ADR 0026 (Agent-Drain +
Registry + Snapshot + Lifecycle-Pattern). Schwester-ADR zu
ADR 0023 (Welle 3 Foundation); Pattern-Pendant zu ADR 0025
(Welle 2 Recovery-Pattern, schärft ADR 0022).

**Drain-Pfad: Pre-Tick-Schritt A0 mit `apply_command`-direct**
(D1 aus Recherche-Brief). Drei Varianten waren denkbar:

1. **Scheduler-Push** — `Command` wird in `Event` gewrappt
   und über den Scheduler in den nächsten Tick gepoppt.
   *Abgelehnt*: Scheduler ist für Events, nicht Commands.
   Command-zu-Event-Wrap ist Vorgriff auf M5-Material;
   `Scheduler.add(event)` hat keine Command-Surface.
2. **`apply_command`-direct in derselben Tick (D2-Hook)**
   — TickLoop ruft `device.apply_command(...)` direkt nach
   `agent.tick(...)` in Schritt D2. *Abgelehnt*: bricht
   GG-AGENT-008 Commit-Reihenfolge-Invariante (Commands der
   aktuellen Tick wirken im selben Tick), produziert
   Re-Iteration der Devices.
3. **Pre-Tick-Schritt A0** (gewaehlt) — am Tick-Start, vor
   Step-A-Baseline/Profile/Event. A0 ist bewusst in
   Ziel-Validierung (A0v, vor `clock.advance(...)`/
   `scheduler.pop_due(...)`) und Anwendung (A0a, nach
   `clock.advance(...)`/`scheduler.pop_due(...)`) geteilt.
   Commands der vorigen Ticks werden im aktuellen Tick in den
   Device-Command-Pfad eingespeist; Step-A-Baseline/Profile/Event
   und Step-C-Auto-Close behalten ihre bestehende spaetere
   Praezedenz. *Vorteil*: konsistent mit GG-AGENT-008; analog
   Welle-6b-LoadEvent-Overlay-Pattern; kein Scheduler-Vorgriff;
   ein ungültiges Target kann den Tick nicht halb mutieren.

**Registry-API: TickLoop-Kwarg + Scenario-Loader-Builder**
(D2 aus Recherche-Brief). Analog Welle-6b-Devices-Pattern:
TickLoop-Konstruktor nimmt `agents`-Tuple direkt; Scenario-
Loader-Builder baut den Tuple aus `scenario.agents`-Domain-
Daten (Welle 4b). Welle-3-`_set_agents_for_testing(...)`-
Helper wird **entfernt** — Tests stellen auf
Konstruktor-Kwarg um. Nicht-leere `agents` erzwingen
produktiv eine Bus-Surface: wenn kein `agent_bus` injiziert
wurde, erzeugt der Konstruktor einen echten `AgentMessageBus`.
So bleibt `agent_bus=None` fuer agentenlose Runs der saubere
Skip-Pfad, waehrend `agents=(...)` nie still registriert und
dann wegen fehlendem Bus nicht getickt wird.

**Lifecycle: `_attach_agents()` mit `set_run_id` +
optional `attach_random`** (D5 aus Recherche-Brief). Drei
Varianten waren denkbar:

1. **Konstruktor-Param `random` pro Agent** — Agent-
   Konstruktor nimmt `RandomPort` direkt. *Abgelehnt*:
   Konstruktor-Bloat; trennt Domain-Konstruktion (z. B.
   Regel-Tabelle) von Lifecycle (Sub-Port-Ableitung).
2. **TickLoop-Konstruktor injiziert RandomPort an alle
   Agents in einer Phase** (`_attach_agents()`-Hook).
   *Gewaehlt*: spiegelt Welle-6b-SmartMeter-`attach_sources`-
   Pattern (ADR 0018 §2.4). RuleBasedAgent ohne Stochastik
   implementiert `attach_random` nicht — `_attach_agents()`
   prüft ein optionales Sub-Protocol
   (`isinstance(agent, _RandomAttachableAgent)`). Das
   Sub-Protocol muss deshalb `@runtime_checkable` sein; sonst
   wirft Python beim `isinstance`-Check einen `TypeError`.
3. **Agent zieht sich seinen Sub-Port selbst aus dem Bus**
   — Bus-Konstruktor nimmt `RandomPort`-Referenz.
   *Abgelehnt*: Bus haelt Welle-3-konform keinen
   `RandomPort`-Slot (Welle-3-Review-Folge M-3); Welle 4a
   fuehrt das auch nicht ein, weil der Bus selbst keine
   stochastischen Operationen hat.

**Drain-Eviction: `consume_for(receiver)` als private Inbox**
(D4 aus Recherche-Brief). Variante mit `evict_before(
simulation_time)` waere Per-Tick-Eviction (alle Messages vor
einer Zeit werden geloescht, unabhaengig vom Receiver).
*Abgelehnt*: bricht Multi-Receiver-Szenarien — wenn Agent A
um t=1000 publiziert und Agent B die Message erst um t=2000
lesen will, würde `evict_before(t=1500)` die Message
vorzeitig entfernen. Ebenfalls abgelehnt fuer Welle 4a:
destruktives Entfernen von Broadcasts beim ersten
`consume_for(...)`-Aufruf; das wuerde spaetere Receiver
abschneiden. Gewaehlt ist deshalb eine schmale Eviction:
`consume_for(receiver)` konsumiert nur `message.receiver ==
receiver`; Broadcasts bleiben nicht-destruktiv in
`drain_for(receiver)` bis Welle 4b oder eine Folge-Slice
registry-aware Fan-out/Watermark spezifiziert.

**Snapshot-Vertrag für Welle 4a**: Foundation-State wird
persistiert, konkrete Agent-Instanzen nicht. `agent_bus`
kommt als Single-Instance-Sub-Snapshot hinzu, sobald ein Bus
vorhanden ist (injiziert oder per Auto-Bus-Regel erzeugt);
`_pending_agent_commands` kommt als
`pending_agent_commands`-Sub-Snapshot hinzu, sobald der
Buffer nicht leer ist. Das verhindert Resume-Verlust zwischen
Agent-Tick und Folgetick. Der produktive Resume-Pfad erhaelt
optionale Runtime-Dependency-Kwargs (`devices`, `grid_model`,
`active_load_events`, `active_load_profiles`, `fault_port`,
`agents`), weil `TickLoop.from_snapshot(...)` die Device- und
Agent-Instanzen weiterhin nicht aus ihren Sub-Snapshots
rekonstruiert. Ohne diese Kwargs bleibt der bestehende
Welle-6a-Pfad unveraendert; mit ihnen kann ein Pending-
Command nach Resume genau einmal auf das Ziel-Device
angewendet werden. Produktiver Resume validiert dabei die
injizierten Devices gegen vorhandene `devices.<type>.<id>`-
Sub-Snapshot-Keys **und** gegen den exakten Device-Snapshot-
State, validiert ein injiziertes `grid_model` gegen den
vorhandenen `grid_model`-Sub-Snapshot, validiert injizierte
`active_load_events`/`active_load_profiles` gegen persistierte
GridModel-Overlay-Tupel, **wenn** ein `grid_model`-Sub-Snapshot
vorhanden ist, und prueft `pending_agent_commands` gegen die
injizierte Device-Registry, damit frische/falsche Runtime-
Instanzen nicht still als verlustfreier Resume durchgehen.
Ohne `grid_model`-Sub-Snapshot bleiben Overlay-only-Szenarien
gueltig, aber der Overlay-Zustand ist nicht Teil des
verlustfreien Agent-Foundation-State-Resume-Versprechens.
Fehlt der `agent_bus`-Sub-Snapshot, erzeugt Restore nur dann
einen leeren Bus, wenn `agents != ()` injiziert wurde; ohne
injizierte Agents bleibt der Welle-6a-Pfad bei `agent_bus=None`.
Welle-4b-RuleBasedAgent-
Konkretisierung fügt zusätzlich `agents.<agent_type>.
<agent_id>`-Sub-Snapshots additiv per ADR 0015 §2.3 ein.
ADR 0023 §6 verbindliche Welle-4-Konsequenz
„Agent-Sub-Snapshot-Slot in `TickLoop.snapshot()`" wird damit
geteilt: generischer Bus-/Pending-State in Welle 4a,
konkreter Agent-State in Welle 4b.

**ADR 0025-Pattern**: Welle 4a schärft ADR 0023 §6 ohne
Supersede (ADR 0011-Pattern). ADR 0023 bleibt
`Provisional`; Welle-4a-Closure produziert ADR 0026 als
neue ADR (analog ADR 0025 zu ADR 0022).

## 4. Liefer-Reihenfolge

### Pre-C0 — `chore`: git mv welle-3.md → done/welle-3.md (rename-only, `a24f733`)

Reiner Rename ohne Inhaltsumschreibung. `feedback_git_mv`-
Konvention.

### C0 — `docs(plan)`: welle-4a Slice-Doc (dieses Dokument)

Welle-4a-Start-Marker. Status: `In Progress`. Plus
`in-progress/README.md`-Sync:
- `welle-3.md`-Zeile entfernen (jetzt in `done/welle-3.md`).
- `welle-4a.md`-Zeile ergänzen.
- `M3-faults-agents-observability.md` §0 + §3 auf das
  4a/4b-Sub-Slicing synchronisieren, damit der kanonische M3-
  Plan schon ab C0 nicht mehr einen monolithischen Welle-4-
  Implementer-Scope beschreibt.

### C1 — `docs(adr)`: ADR 0026 Proposed

Neu: `docs/plan/adr/0026-agent-drain-registry-pattern.md`.
Inhalt (geplant, ~ 3000–4000 Wörter, Pattern aus ADR 0025):

- **Status**: `Proposed` (Datum 2026-05-21).
- **§1 Kontext**: Welle-3-Forward-Pointer + ADR 0023 §6.
- **§2 Entscheidung** (6 Sub-Sections):
  - §2.1 Drain-Pfad: Schritt A0 Pre-Tick mit `apply_command`-
    direct; A0v-Target-Validierung vor Clock-/Scheduler-
    Mutation; A0a-Apply vor Step-A-Baseline/Profile/Event;
    Step-A-LoadDevice-Baseline bleibt spaeter und gewinnt auf
    LoadDevices;
    Agent-Commands auf GridConnection-IDs zaehlen als
    manueller Override fuer Schritt C.
  - §2.2 Registry-API: TickLoop-Konstruktor-Kwarg + Scenario-
    Loader-Builder-Symmetrie; nicht-leere `agents` erzeugen
    bei fehlendem `agent_bus` automatisch einen echten
    `AgentMessageBus`; der Builder spiegelt LoadOverlay-Tupel in
    `GridModelBilanz`, damit der GridModel-v2-Overlay-Snapshot den
    produktiven Resume-Pfad absichert.
  - §2.3 Lifecycle: `_attach_agents()` mit `set_run_id` +
    optionalem, mit `@runtime_checkable` dekoriertem
    `_RandomAttachableAgent`-Sub-Protocol.
  - §2.4 Bus-Eviction: `consume_for(receiver)` als
    destruktive Direct-Inbox-Drain-Variante; Broadcasts
    bleiben nicht-destruktiv.
  - §2.5 Registry-/Drain-Fail-Fast:
    `AgentRegistryError`/`AgentDuplicateIdError` plus
    `AgentCommandDrainError`/`AgentInvalidCommandTargetError`;
    TickLoop-Agent-Snapshot-Format-Errors fuer Pending-Command-
    und Runtime-Dependency-Mismatches; malformed `agent_bus`-
    Sub-Snapshots propagieren bestehende `AgentBusSnapshot*`-
    Errors unwrapped.
  - §2.6 Snapshot-Vertrag: `agent_bus` + `pending_agent_commands`
    in `TickLoop.snapshot()`/`from_snapshot(...)`; optionale
    Runtime-Dependency-Kwargs fuer Resume mit Devices/Agents;
    Device-ID-/Typ- und Device-State-Match-Checks fuer
    injizierte Runtime-Instanzen; `grid_model`-Snapshot-Match
    fuer injiziertes GridModel; LoadOverlay-Match gegen
    persistierten GridModel-State, falls ein `grid_model`-
    Sub-Snapshot existiert; keine GridModel-Pflicht fuer
    Overlay-only-Szenarien; Auto-Bus-Praezedenz bei alten
    Snapshots ohne `agent_bus`; `pending_agent_commands.result`
    als `CommandResult`-String-Roundtrip;
    konkrete `agents.<type>.<id>`-Slots bleiben Welle 4b.
- **§3 Begründung**: drei Drain-Varianten, drei Registry-
  Varianten, drei Lifecycle-Varianten.
- **§4 Reichweite**: In-Scope-4a (Plumbing) / Out-Scope-4b
  (Konkretisierung).
- **§5 Operative Artefakte**: Dateipfade analog Critical-
  Files.
- **§6 Konsequenzen**: Welle-4b-Implementer hat klare
  Schnittstelle; Welle-3-`_set_agents_for_testing` entfernt;
  `agents`-Top-Level-Block im Scenario-Schema bleibt Welle-
  4b-Pflicht.
- **§7 Nicht Gegenstand**: GG-AGENT-007 Deadlines,
  GG-AGENT-008 Async, konkrete Agent-Instanz-Snapshots,
  Multi-Receiver-Watermark.

Plus `adr/README.md`-Zeile für ADR 0026 `Proposed`.

### C2 — `feat(welle-4a)`: TickLoop-Registry + Schritt-A0-Drain + consume_for + Tests

**Code (edit):**

1. `src/grid_gym/hexagon/core/agents/_protocol.py` —
   `attach_random(random: RandomPort) -> None`-Methode als
   **optionale** Surface über ein separates, mit
   `@runtime_checkable` dekoriertem
   `_RandomAttachableAgent`-Sub-Protocol.
2. `src/grid_gym/hexagon/core/agents/bus.py` —
   `consume_for(receiver: str) -> Sequence[AgentMessage]`-
   destruktive Direct-Inbox-Drain-Variante (keine Broadcast-
   Konsumption).
3. `src/grid_gym/hexagon/core/simulation/tick_loop.py`:
   - `agents: tuple[Agent, ...] = ()`-Kwarg (keyword-only).
   - Auto-Bus-Regel: `agents != () and agent_bus is None`
     normalisiert auf einen neuen `AgentMessageBus`.
   - `_attach_agents()`-Lifecycle (set_run_id + optional
     attach_random).
   - `agent_id`-Eindeutigkeits-Check mit
     `AgentDuplicateIdError`.
   - Schritt A0 Pre-Tick-Drain mit A0v-Zielvalidierung vor
     Clock-/Scheduler-Mutation und A0a-Apply vor Schritt A;
     Commands auf GridConnection-IDs ergaenzen
     `manual_override_grid_ids`.
   - `agent_bus`- und `pending_agent_commands`-Sub-Snapshots
     schreiben und beim `from_snapshot(...)` wiederherstellen;
     `CommandResult`-Stringwerte und Payload-Typen validieren.
   - `from_snapshot(...)` erhaelt optionale
     Runtime-Dependency-Kwargs (`devices`, `grid_model`,
     `active_load_events`, `active_load_profiles`,
     `fault_port`, `agents`) und reicht sie beim Resume in den
     Konstruktor durch; injizierte Devices werden gegen
     vorhandene `devices.<type>.<id>`-Snapshot-Keys und ihren
     exakten Device-Snapshot-State gematcht, injiziertes
     `grid_model` gegen den `grid_model`-Sub-Snapshot,
     injizierte LoadOverlay-Tupel gegen den persistierten
     GridModel-Overlay-State, falls ein `grid_model`-Sub-Snapshot
     existiert; ohne `grid_model`-Sub-Snapshot werden Overlays
     nur durchgereicht, nicht als verlustfrei validiert. Alte
     Snapshots ohne `agent_bus` folgen der expliziten Praezedenz
     `agents == ()` → `agent_bus=None`, `agents != ()` → leerer
     Auto-Bus.
   - Welle-3-`_set_agents_for_testing(...)` entfernt.
4. `src/grid_gym/hexagon/core/scenario/loader.py` —
   `build_tick_loop(..., agents=...)`-Builder-Symmetrie plus
   `GridModelBilanz(..., active_load_events=scenario.load_events,
   active_load_profiles=scenario.load_profiles)`, damit Scenario-
   Overlays im `grid_model`-Sub-Snapshot persistiert und fuer
   Welle-4a-Resume-Match-Checks nutzbar sind, sofern das Scenario
   einen GridModel-Block hat. Ohne `grid_model_config` bleiben
   Overlay-only-Szenarien gueltig; sie bekommen keinen GridModel-
   Overlay-Match-Check.
5. `src/grid_gym/hexagon/core/errors.py` —
   `AgentRegistryError`/`AgentDuplicateIdError` plus
   `AgentCommandDrainError`/`AgentInvalidCommandTargetError`;
   zusaetzlich
   `TickLoopAgentSnapshotMissingKeysError`,
   `TickLoopAgentSnapshotWrongTypeError`,
   `TickLoopAgentSnapshotInvalidCommandResultError`,
   `TickLoopAgentSnapshotDeviceMismatchError` und
   `TickLoopAgentSnapshotGridModelMismatchError` plus
   `TickLoopAgentSnapshotLoadOverlayMismatchError` fuer
   Agent-Foundation-Resume-Format-/Mismatch-Fehler.

**Tests (neu/edit):**

6. `tests/unit/hexagon/core/agents/test_bus.py` — Tests für
   `consume_for(...)`-Direct-Inbox-Destruktiv-Vertrag,
   Broadcast-Retention-Sanity, Roundtrip mit
   `drain_for(...)`-Parallel.
7. `tests/unit/hexagon/core/simulation/test_tick_loop_welle_3_agent.py`
   — Umstellung von `_set_agents_for_testing` auf
   Konstruktor-Kwarg; **Datei umbenannt** zu
   `test_tick_loop_welle_4a_agent.py` (Pattern-Konsistenz
   zur Welle-Bezeichnung); Duplicate-`agent_id`-Fall erwartet
   `AgentDuplicateIdError`; Test fuer Auto-Bus bei
   `agents != () and agent_bus is None`, damit registrierte
   Agents nicht still als No-op enden.
8. Neue Tests für Schritt-A0-Drain:
   `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_drain.py`
   — Drain-Order, Drain-vor-Step-A-Baseline/Profile/Event,
   Multi-Agent-Drain,
   LoadDevice-Baseline-gewinnt-gegen-Agent-Command,
   GridConnection-Agent-Command als manueller Auto-Close-
   Override, `AgentInvalidCommandTargetError`-Fail-Fast ohne
   Clock-/Scheduler-/Device-Partial-Mutation.
9. Neue Tests für `_attach_agents()`-Lifecycle:
   `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_lifecycle.py`
   — `set_run_id`-Aufruf, optionaler `attach_random`-Aufruf,
   Sub-Port-Namens-Konvention, kein `TypeError` beim
   `isinstance`-Check gegen `_RandomAttachableAgent`.
10. Neue Tests für Agent-Foundation-State-Snapshot:
    `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_snapshot.py`
    — `agent_bus`-Roundtrip, `pending_agent_commands`-Roundtrip,
    malformed-`agent_bus`-Sub-Snapshot propagiert
    `AgentBusSnapshot*` unwrapped,
    `CommandResult`-String-Roundtrip, Wrong-Type-/Unknown-Result-
    Rejects fuer Pending-Command-Snapshots, Device-ID-/Typ-
    und Device-State-Mismatch, GridModel-Snapshot-Mismatch sowie
    LoadOverlay-Mismatch bei injizierten Runtime-Dependencies
    **mit vorhandenem `grid_model`-Sub-Snapshot**,
    No-GridModel-Overlay-only-Backward-Compat,
    Auto-Bus-Praezedenz bei altem Snapshot ohne `agent_bus` plus
    `agents != ()`,
    Resume mit injizierten Devices/Agents wendet Pending-
    Commands genau einmal an, fehlende Sub-Snapshots bleiben
    backward-kompatibel leer.
11. `tests/unit/hexagon/core/scenario/test_loader_welle_6b.py`
    — `build_tick_loop(agents=...)`-Forwarding-Test (analog
    Welle-3-Review-Folge-3-L-1-Pattern) plus Assertion, dass
    `GridModelBilanz.active_load_events`/
    `.active_load_profiles` die Scenario-Overlays tragen.

### C3 — `docs(plan)`: Welle-4a Status/DoD-Sync

- `docs/plan/adr/0026-agent-drain-registry-pattern.md` —
  `Proposed → Provisional` mit Welle-4a-Merge-Hash (C2).
- `docs/plan/adr/README.md` — ADR 0026 auf `Provisional`.
- `docs/plan/planning/in-progress/M3-faults-agents-observability.md`
  — §0 Status: „Welle 4a abgeschlossen am 2026-05-21" mit
  Welle-4a-Commit-Stack; §3 Welle 4 mit Welle-4a-`Done`-
  Tag + Commit-Refs; „Naechster Schritt:
  Welle 4b (RuleBasedAgent + Scenario-Schema)".
- `docs/plan/planning/in-progress/welle-4a.md` (dieses
  Dokument) — auf `Done` nach C3-Closure.

## 5. Critical Files

| Pfad                                                                | Commit  | Aktion |
| ------------------------------------------------------------------- | ------- | ------ |
| `docs/plan/planning/in-progress/welle-3.md` → `done/welle-3.md`     | Pre-C0  | git mv (rename-only, `a24f733`) |
| `docs/plan/planning/in-progress/welle-4a.md`                        | C0      | NEU (dieses Dokument) |
| `docs/plan/planning/in-progress/README.md`                          | C0      | EDIT (welle-3→welle-4a) |
| `docs/plan/planning/in-progress/M3-faults-agents-observability.md`  | C0      | EDIT (§0 + §3 4a/4b-Sub-Slicing-Sync) |
| `docs/plan/adr/0026-agent-drain-registry-pattern.md`                | C1      | NEU |
| `docs/plan/adr/README.md`                                           | C1      | EDIT (ADR 0026 Zeile) |
| `src/grid_gym/hexagon/core/agents/_protocol.py`                     | C2      | EDIT (`@runtime_checkable`-deklarierte `_RandomAttachableAgent`-optional-Surface) |
| `src/grid_gym/hexagon/core/agents/bus.py`                           | C2      | EDIT (`consume_for(...)` Direct-Inbox-destruktiv, Broadcasts bleiben nicht-destruktiv) |
| `src/grid_gym/hexagon/core/simulation/tick_loop.py`                 | C2      | EDIT (`agents=`-Kwarg + Auto-Bus + Duplicate-ID-Fail-Fast + Schritt-A0-Drain inkl. A0v-Validierung + GridConnection-Override + Agent-Foundation-State-Snapshots + Resume-Kwargs/-Match-Checks + `_attach_agents()`; `_set_agents_for_testing` entfernt) |
| `src/grid_gym/hexagon/core/scenario/loader.py`                      | C2      | EDIT (`build_tick_loop(agents=)`-Symmetrie + GridModelBilanz-Overlay-Verdrahtung fuer Resume-Match-Checks) |
| `src/grid_gym/hexagon/core/errors.py`                               | C2      | EDIT (`AgentRegistryError`/`AgentDuplicateIdError` + `AgentCommandDrainError`/`AgentInvalidCommandTargetError` + TickLoop-Agent-Snapshot-Format-/Mismatch-Errors inkl. LoadOverlay-Mismatch) |
| `tests/unit/hexagon/core/agents/test_bus.py`                        | C2      | EDIT (`consume_for`-Direct-Inbox-Tests + Broadcast-Retention) |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_3_agent.py` → `test_tick_loop_welle_4a_agent.py` | C2 | RENAME + EDIT (Konstruktor-Kwarg statt `_set_agents_for_testing`, Duplicate-ID-Fail-Fast, Auto-Bus) |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_drain.py` | C2  | NEU (Schritt-A0-Drain-Tests inkl. GridConnection-Override + Fail-Fast-ohne-Partial-Mutation) |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_lifecycle.py` | C2 | NEU (`_attach_agents()`-Tests) |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_snapshot.py` | C2 | NEU (`agent_bus` + `pending_agent_commands`-Roundtrip + CommandResult-/Payload-Validierung + Resume-Kwargs/-Match-Checks) |
| `tests/unit/hexagon/core/scenario/test_loader_welle_6b.py`          | C2      | EDIT (`agents=`-Forwarding-Test + GridModelBilanz-Overlay-Snapshot-Absicherung) |
| `docs/plan/adr/0026-agent-drain-registry-pattern.md`                | C3      | EDIT (Status → Provisional) |
| `docs/plan/adr/README.md`                                           | C3      | EDIT (Status → Provisional) |
| `docs/plan/planning/in-progress/M3-faults-agents-observability.md`  | C3      | EDIT (§0 + §3 Welle 4a Closure-Refs) |
| `docs/plan/planning/in-progress/welle-4a.md`                        | C3      | EDIT (Status → Done) |

## 6. Verifikationspfad

End-to-End über `make`-Targets (Dockerfile-Stages, Docker-only
nach Repo-Konvention):

1. **`make test-unit`** — grün mit ~22–31 neuen Tests
   (`consume_for`-Direct-Inbox-Destruktiv-Vertrag,
   Broadcast-Retention, Schritt-A0-Drain-Order,
   LoadDevice-Baseline-gewinnt-gegen-Agent-Command,
   A0-Fail-Fast-ohne-Partial-Mutation,
   `_attach_agents()`-Lifecycle, Agent-Foundation-State-Snapshot,
   Pending-Command-Snapshot-Wrong-Type-/Unknown-Result-Rejects,
   `_RandomAttachableAgent`-Runtime-Check, Konstruktor-Kwarg-
   Forwarding, Auto-Bus bei `agents != ()`,
   GridConnection-Agent-Command als Auto-Close-Override,
   Resume mit injizierten Devices/Agents plus Device-ID-/Typ-
   und Device-State-Match-Checks, GridModel-Snapshot-Match,
   LoadOverlay-Match bei vorhandenem `grid_model`-Sub-Snapshot,
   No-GridModel-Overlay-only-Backward-Compat,
   Auto-Bus-Praezedenz fuer alte Snapshots ohne `agent_bus`,
   Duplicate-ID- und Command-Target-Fail-Fast).
   Test-Count steigt von 889
   (Welle-3-Endstand) auf ~911–920. Welle-3-Tests, die
   `_set_agents_for_testing(...)` nutzten, werden auf den
   Konstruktor-Kwarg umgestellt — Tests bleiben grün, nur
   die API-Aufruf-Syntax ändert sich.
2. **`make test-integration`** — bleibt 14 Tests grün
   (Welle 4a hat keine neuen Integration-Tests; Welle 4b
   bringt das End-to-End-Demo-Szenario).
3. **`make gates`** — grün ohne Override; AC-PORTS-NO-OUT
   bleibt 16 Contracts; `CRITICAL_COV_TARGETS` unverändert
   (`core/agents` ist seit Welle 3 enthalten und wird durch
   Welle-4a-Code weiter ausgenutzt).
4. **`make fullbuild`** — grün ohne Override (Welle 4a hat
   keine OTLP-Pflicht; M3-Welle-4-Abschluss-Gate folgt mit
   Welle 4b).
5. **ADR-0026-Status sichtbar `Provisional`** nach C3.
6. **ADR 0023 bleibt `Provisional`** (Welle 4a schärft
   ohne Supersede; keine Status-Aenderung).
7. **Agent-Foundation-State-Resume ist verlustfrei**: Snapshot mit
   `agent_bus`-Buffer und nicht-leerem
   `pending_agent_commands`-Buffer roundtript beide States;
   `TickLoop.from_snapshot(..., devices=..., agents=...)`
   baut den produktiven Resume-Pfad wieder auf und validiert
   injizierte Device-IDs/-Typen plus Device-Snapshot-State gegen
   vorhandene Device-Sub-Snapshots, ein injiziertes GridModel
   gegen den vorhandenen `grid_model`-Sub-Snapshot sowie
   injizierte LoadOverlay-Tupel gegen den persistierten
   GridModel-Overlay-State, wenn dieser Sub-Snapshot existiert.
   Ohne GridModel-Snapshot bleiben injizierte Overlays ein
   Runtime-Dependency-Durchreichpfad ohne verlustfreies
   Snapshot-Match-Versprechen. Ein Folgetick nach Resume wendet
   Pending-Commands nicht erneut und nicht gar nicht, sondern
   genau einmal an. Konkrete Agent-Instanz-Zustände sind in
   Welle 4a bewusst nicht Teil dieses Versprechens und werden mit
   `agents.<agent_type>.<agent_id>` in Welle 4b ergaenzt.
8. **Welle-3-`_set_agents_for_testing`-Helper ist entfernt**
   — Welle-4a-Code-Audit-Pflicht: `grep -rn
   "_set_agents_for_testing" tests/ src/` liefert kein
   Ergebnis nach C2.
9. **Rename-Historie**: `git log --follow done/welle-3.md`
   traceable über Pre-C0-Rename (`a24f733`).
10. **Git-Pattern**: 5 neue Welle-4a-Commits in der
   Reihenfolge `chore(welle-4a): git mv (Pre-C0)` →
   `docs(plan): welle-4a Slice-Doc (C0)` → `docs(adr): ADR
   0026 Proposed (C1)` → `feat(welle-4a): ... (C2)` →
   `docs(plan): Welle-4a Status/DoD-Sync (C3)`.

## 7. Risiken

- **R-1 — `_set_agents_for_testing(...)`-Entfernung bricht
  Welle-3-Tests**: mehrere Welle-3-Tests in
  `test_tick_loop_welle_3_agent.py` nutzen den Helper (aktuell
  sieben Call-Sites plus Doc-/Assertion-Referenzen).
  *Mitigation*: Welle 4a stellt sie atomar auf den
  Konstruktor-Kwarg um (im selben C2-Commit). Test-Datei
  wird in `test_tick_loop_welle_4a_agent.py` umbenannt
  (Pattern-Konsistenz zur Welle-Bezeichnung).
- **R-2 — Schritt-A0-Drain vs. LoadEvent-Overlay-Reihenfolge**:
  beide schreiben `apply_command(...)` an Devices. Zusaetzlich
  setzt Schritt A fuer jedes `LoadDevice` zuerst die bestehende
  Baseline aus `rated_power_kw`. Wenn ein Agent-Command auf ein
  `LoadDevice` zielt, gewinnt deshalb die LoadDevice-Baseline
  im selben Tick; wenn ein LoadEvent/Profile und ein Agent-
  Command auf dasselbe Device zielen, gewinnt danach Event/
  Profile (Welle-6b-Pattern „Event-Overlay nach Baseline").
  *Mitigation*: Schritt A0 drainet **zuerst** (Agent-Commands
  der vorigen Ticks), Schritt A wendet **danach** Baseline,
  Profile und LoadEvent an. Tests pinnen Baseline- und
  Event/Profile-Praezedenz explizit. Fuer GridConnection-Targets ergaenzt
  A0 `manual_override_grid_ids`, damit Schritt C Auto-Close den
  Agent-Command nicht sofort ueberschreibt; ein spaeterer
  LoadEvent/Profile-Overlay auf derselben GridConnection-ID
  gewinnt weiterhin.
- **R-2b — A0-Fail-Fast nach bereits mutierter Tick-State**:
  wenn ein ungueltiges `target_device_id` erst nach
  `clock.advance(...)`, `scheduler.pop_due(...)` oder nach
  einigen erfolgreichen `apply_command(...)`-Aufrufen erkannt
  wird, ist Resume/Retry nicht mehr sauber. *Mitigation*: A0
  besteht aus A0v (vollstaendige Target-Validierung gegen
  `_device_by_id`, vor Clock-/Scheduler-Mutation) und A0a
  (Apply der lokal kopierten Command-Liste); der Buffer wird
  erst nach erfolgreichem Apply-Durchlauf geleert. Test pinnt,
  dass `AgentInvalidCommandTargetError` keine Clock-Advance-,
  Scheduler-Pop- oder Device-Apply-Nebenwirkungen hinterlaesst.
  Unerwartete `apply_command(...)`-Exceptions sind getrennt:
  fachliche Ablehnungen muessen als `CommandResult` zurueckkommen,
  Exceptions propagieren ohne Rollback-Versprechen und ohne
  Buffer-Clear.
- **R-3 — `_attach_agents()` mit optionalem
  `_RandomAttachableAgent`-Sub-Protocol**: Hasattr ist nicht
  typisierbar (mypy-Strict-Risiko). *Mitigation*: ein separates,
  mit `@runtime_checkable` dekoriertes
  `_RandomAttachableAgent`-Sub-Protocol unter `_protocol.py`;
  `_attach_agents()` prueft via
  `isinstance(agent, _RandomAttachableAgent)` (analog
  Welle-1-`FaultInjectableDevice`-Pattern). Saubere
  Typisierung; keine Hasattr-Drift; kein Runtime-`TypeError`
  beim `isinstance`-Check.
- **R-4 — ADR 0026 vs. ADR-0023-Schärfung**: ADR 0026 ist
  separate ADR, kein Schärfung-ohne-Supersede in ADR 0023.
  *Mitigation*: 5 substantielle Entscheidungen rechtfertigen
  eigene ADR (analog ADR 0025 zu ADR 0022). ADR 0026
  referenziert ADR 0023 §6 explizit als „erfuellt durch
  diese ADR".
- **R-5 — Sub-Slicing 4a → 4b: Welle 4a closure ohne
  konkreten Agent**: ohne RuleBasedAgent-Beispiel ist
  Welle-4a-Code zwar test-getrieben getestet, aber nicht
  in einem produktiven Lauf geprueft. *Mitigation*:
  Welle-4a-Tests pinnen alle Pflicht-Pfade via NullAgent +
  `_OrderRecordingAgent`-Stubs (die jetzt das volle
  Protocol erfuellen). Welle 4b verifiziert End-to-End.
- **R-6 — Snapshot zwischen Agent-Tick und Folgetick verliert
  Commands**: Schritt D2 produziert Commands für den nächsten
  Tick; ein Resume vor Schritt A0 darf sie nicht verwerfen.
  *Mitigation*: Welle 4a persistiert `pending_agent_commands`
  als eigenen Sub-Snapshot und stellt ihn in
  `TickLoop.from_snapshot(...)` wieder her. Der produktive
  Resume-Test ruft `from_snapshot(..., devices=..., agents=...)`,
  damit `_device_by_id` und Agent-Registry wieder aufgebaut
  sind; Restore/Tests matchen injizierte Device-IDs/-Typen und
  den exakten Device-Snapshot-State gegen vorhandene Snapshot-
  Keys und pinnen den genau-einmal-Drain nach Resume.
- **R-6a — Begriff „Agent-State-Resume" waere zu stark**:
  Welle 4a persistiert nur `agent_bus` und
  `pending_agent_commands`, aber keine konkreten
  `agents.<agent_type>.<agent_id>`-Sub-Snapshots. Ein Resume mit
  injizierten Agents kann deshalb deren lokalen Zustand nicht
  pruefen. *Mitigation*: DoD und ADR 0026 sprechen explizit von
  **Agent-Foundation-State-Resume**; konkrete Agent-Instanz-
  Snapshots bleiben Welle 4b.
- **R-6b — Pending-Command-Snapshot ist formal zu weich**:
  ein `commands`-Eintrag mit falschem `result`-Typ, unbekanntem
  `CommandResult`-String oder nicht canonical-json-faehigem
  `payload` koennte erst spaet im Tick scheitern. *Mitigation*:
  Pending-Command-Restore validiert Pflichtfelder typisiert,
  parst `result` ueber `CommandResult(...)` und rejected
  strukturell falsche Payloads im Snapshot-Test; unbekannte
  `CommandResult`-Strings werden in
  `TickLoopAgentSnapshotInvalidCommandResultError` uebersetzt.
- **R-6bb — AgentBus-Snapshot-Errors doppelt gewrappt**:
  `AgentMessageBus.from_snapshot(...)` besitzt bereits eine
  eigene `AgentBusSnapshot*`-Taxonomie. Wenn TickLoop malformed
  `agent_bus`-Sub-Snapshots in neue `TickLoopAgentSnapshot*`-
  Errors uebersetzt, gehen bestehende Bus-Fehlerklassen und
  Tests verloren. *Mitigation*: TickLoop delegiert malformed
  `agent_bus`-Sub-Snapshots unveraendert an
  `AgentMessageBus.from_snapshot(...)` und propagiert dessen
  `AgentBusSnapshot*`-Errors unwrapped; neue TickLoop-Agent-
  Snapshot-Errors gelten nur fuer `pending_agent_commands` und
  Runtime-Dependency-Matches.
- **R-6c — Produktiver Resume mit falschem GridModel/LoadOverlay
  oder alter AgentBus-Luecke**: ein Snapshot kann `grid_model`-
  State und LoadOverlay-State enthalten, waehrend
  `from_snapshot(..., grid_model=..., active_load_events=...,
  active_load_profiles=...)` frische oder abweichende Runtime-
  Instanzen injiziert; gleichzeitig duerfen Overlay-only-
  Szenarien ohne `grid_model_config` nicht ungueltig werden.
  Ausserdem koennen alte Snapshots ohne `agent_bus` mit neuen
  `agents=...` wiederaufgenommen werden.
  *Mitigation*: injiziertes `grid_model.snapshot()` muss exakt zum
  `grid_model`-Sub-Snapshot passen, sonst
  `TickLoopAgentSnapshotGridModelMismatchError`; nicht-leere
  injizierte LoadOverlay-Tupel werden nur dann gegen persistierten
  GridModel-Overlay-State gematcht, wenn ein `grid_model`-
  Sub-Snapshot existiert, sonst bleiben sie Runtime-Dependencies
  ohne verlustfreies Snapshot-Match-Versprechen. Der
  `build_tick_loop(...)`-Builder muss dieselben Scenario-Overlays
  beim Bau von `GridModelBilanz` mitgeben, wenn
  `grid_model_config` vorhanden ist, damit Fresh-Start-Snapshots
  diesen State tragen. Fehlt `agent_bus`, bleibt `agent_bus=None`
  nur fuer `agents == ()`; bei `agents != ()` erzeugt Restore
  einen leeren Bus nach der Konstruktor-Auto-Bus-Regel und testet
  diese Praezedenz explizit.
- **R-7 — Nicht-leere `agents` ohne Bus werden still nicht
  getickt**: Welle-3-Hook skippt bei `agent_bus=None`. Wenn
  Welle 4a nur `agents=` ergaenzt, koennte der Builder
  produktive Agents registrieren, ohne dass sie laufen.
  *Mitigation*: Konstruktor und Builder normalisieren
  `agents != () and agent_bus is None` auf einen echten
  `AgentMessageBus`; Test pinnt, dass der Agent in diesem
  Fall getickt wird.

## 8. Wandert nach

- `done/welle-4a.md` mit M3-Welle-4b-Start als Pre-C0
  reiner-Rename-Commit (Memory-Konvention `feedback_git_mv`
  strikt). Welle 4b folgt direkt — kein `next/`-
  Zwischenschritt, weil das Sub-Slicing 4a/4b in M3-Plan §3
  vorab dokumentiert ist.
