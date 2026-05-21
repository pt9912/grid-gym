# Welle 4a — Multi-Agent-Foundation-Plumbing

**Status:** In Progress — eroeffnet am 2026-05-21 mit M3-Welle-
4a-Pre-C0-Rename (`a24f733`). Welle 4 ist die produktive
Konkretisierung des Multi-Agent-Subsystems und wird in zwei
Teilwellen geliefert (Sub-Slicing nach M3-Slice-Plan §3
Sub-Slicing-Schwelle: 6+ Items mit ≥ 2 echten Architektur-
Entscheidungen):

- **Welle 4a — Foundation-Plumbing** (dieses Dokument):
  ADR 0026 + TickLoop-Registry-API + Schritt-A0-Pre-Tick-Drain
  + `consume_for`-Bus-Eviction + Lifecycle-Hook. **Keine**
  konkreten Agent-Implementer.
- **Welle 4b — RuleBasedAgent + Scenario-Schema**: konkrete
  Implementer + `agents`-Top-Level-Block + Property-Tests +
  Sub-Snapshot-Slot + End-to-End-Demo-Szenario +
  Welle-4-Gate (`make fullbuild` ohne Override).

Pattern: spiegelt M3-Welle-1 (Fault-Foundation) → M3-Welle-2
(Fault-Konkretisierung) eins zu eins fuer Agenten.

Kanonische Slice-Spezifikation:
[`M3-faults-agents-observability.md §3 Welle 4`](M3-faults-agents-observability.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht als Ersatz.

**Commit-Sequenz (geplant):**

- Pre-C0 `a24f733` — `chore(welle-4a): git mv welle-3.md → done/welle-3.md` (rename-only).
- C0 (dieses Dokument) — `docs(plan): welle-4a Slice-Doc`.
- C1 — `docs(adr): ADR 0026 Proposed — Agent-Drain + Registry
  + Lifecycle`.
- C2 — `feat(welle-4a): TickLoop-agents-Kwarg + Schritt-A0-
  Drain + AgentMessageBus.consume_for + Lifecycle + Tests`.
- C3 — `docs(plan): Welle-4a Status/DoD-Sync` (ADR 0026 →
  Provisional, M3-Plan §3 Welle-4a-Done-Tag, welle-4a.md →
  Done; M3-Welle-4b als naechster Schritt vermerkt).

## 1. Context

M3-Welle-3 (`d6f66fc`) hat die Multi-Agent-Foundation
produktiv abgeschlossen: `Agent`-Sub-Protocol +
`AgentMessageBus`-Core-Klasse + `AgentMessage`-frozen-
dataclass + TickLoop-Schritt-D2-Hook + `agent_bus`-Builder-
Symmetrie + `AgentBusError`-Family + Welle-3-Foundation-
Pending-Buffer (`_pending_agent_commands`). 889 Unit-Tests +
14 Integration-Tests; `make gates` A-1 ohne Override gruen.

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
   Lifecycle-Pattern als eigene ADR (analog ADR 0025 zu
   ADR 0022 fuer Recovery-Pattern). Status-Lifecycle:
   - `Proposed` mit Welle-4a-C1 (separater
     `docs(adr)`-Commit).
  - `Provisional` mit Welle-4a-C2-Merge.
  - `Accepted` mit M3-Welle-7-Closure (gemeinsam mit
    ADR 0023 und Welle-4b-ADR-Folge oder einzeln, je nach
    Welle-7-Sequenzierung).
2. **TickLoop-Konstruktor erhaelt produktiven
   `agents`-Kwarg**:
   - `agents: tuple[Agent, ...] = ()` (keyword-only, analog
     `devices=`, `active_load_events=`, etc.).
   - Welle-3-Test-Helper `_set_agents_for_testing(...)` wird
     entfernt — Tests stellen via Konstruktor-Kwarg um.
3. **`_attach_agents()`-Lifecycle-Hook** im
   TickLoop-Konstruktor (analog `_attach_devices()`):
   - Ruft `agent.set_run_id(self._run_id)` fuer jeden
     Agent.
   - Ruft `agent.attach_random(self._random.sub_port(
     f"agent-{agent_id}"))` fuer jeden Agent, der das
     optionale `_RandomAttachableAgent`-Sub-Protocol
     implementiert (`isinstance`-Check). Nicht alle Agent-Typen
     brauchen einen eigenen Random-Stream. Damit ist die
     Welle-3-Review-
     Folge-M-3-Konvention produktiv umgesetzt.
4. **`Agent`-Protocol-Erweiterung** unter
   `src/grid_gym/hexagon/core/agents/_protocol.py` um
   optionale `attach_random(random: RandomPort) -> None`-
   Methode (analog `SmartMeterDevice.attach_sources`-
   Pattern, ADR 0018 §2.4). **Welle-4a-Sub-Protocol** statt
   Erweiterung der Pflicht-Surface, damit RuleBasedAgents
   ohne Stochastik den Hook nicht implementieren muessen.
5. **TickLoop-Schritt A0 (Pre-Tick-Agent-Command-Drain)**:
   - Position: am Tick-Start, **vor** Schritt A (LoadEvent-/
     Profile-Overlay), aber nach `clock.advance(...)` und
     `scheduler.pop_due(...)`.
   - Verhalten: drainet `self._pending_agent_commands`,
     wendet `apply_command(...)` auf das jeweilige
     `target_device_id`-Device an (via `_device_by_id`-
     Lookup), dann `self._pending_agent_commands.clear()`.
   - Vertrag: Agent-Commands der vorigen Ticks werden in der
     **aktuellen** Tick wirksam (GG-AGENT-008 Commit-
     Reihenfolge-Invariante: Commands werden nicht im selben
     Tick verarbeitet, in dem sie emittiert wurden).
   - Reihenfolge bei Konflikt mit LoadEvent-Overlay:
     **Agent-Commands zuerst** (Schritt A0), dann LoadEvent-
     Overlay (Schritt A). LoadEvent gewinnt im selben Tick
     auf demselben Device — konsistent mit Welle-6b-Pattern
     „Event-Overlay nach Baseline".
6. **`AgentMessageBus.consume_for(receiver: str) ->
   Sequence[AgentMessage]`** (destruktive Drain-Variante):
   - Liefert alle Nachrichten fuer `receiver` (oder
     Broadcasts) **und entfernt sie** aus dem Buffer.
   - Implementiert die Welle-3-Review-Folge-M-4-Eviction-
     Spec (`consume_for` mit Per-Receiver-Watermark).
   - Per-Receiver-Watermark in Welle 4a noch **nicht**
     gebraucht (nicht-destruktiver `drain_for` und
     destruktiver `consume_for` existieren parallel) —
     Welle-4b-Implementer entscheiden, welche Variante
     RuleBasedAgent verwendet.
   - Snapshot-Schema-Erweiterung: kein Bump v1 → v2 noetig;
     Buffer-Inhalt wird nach Konsumption kleiner, aber das
     Schema-Format bleibt unveraendert.
7. **`build_tick_loop(..., agents=...)`-Builder-Symmetrie**:
   - Scenario-Loader-Builder erhaelt
     `agents: tuple[Agent, ...] = ()`-Kwarg (analog Welle-3
     `agent_bus`).
   - Default `()`-Tuple; Welle-4b-Scenario-Loader wird die
     Agent-Faktoren-Map (analog `_DEVICE_FACTORIES`) hier
     instanziieren.
8. **`AgentInvalidCommandTargetError`** unter
   `src/grid_gym/hexagon/core/errors.py` als neue Subklasse
   von `AgentBusError` — wird in Schritt A0 geworfen, wenn
   ein Agent-Command auf eine `target_device_id` zielt, die
   im `_device_by_id`-Lookup nicht existiert. Welle-3-
   Pending-Buffer hat keinen Validator; Welle 4a haertet das
   Fail-Fast.

**Anti-Scope (Welle 4b):**

- Konkrete `Agent`-Implementer (`RuleBasedAgent` o. ae.).
- Agent-Decision-Logik (Welt-Zustand-Konsum → Command-
  Produktion).
- `agents`-Top-Level-Block im Scenario-Schema +
  `_assert_agent_list`-Validator + `ScenarioAgent`-Domain-
  Modell.
- Sub-Snapshot-Slots (`agent_bus`, `agents.<agent_type>.
  <agent_id>`) in `TickLoop.snapshot()` — Welle 4a hat keine
  registrierten Agents per Default; Welle 4b fuegt die Sub-
  Snapshots additiv per ADR 0015 §2.3 ein.
- Agent-Faktoren-Map analog `_DEVICE_FACTORIES`.
- Property-Determinismus-Tests pro Agent-Implementer
  (`GG-AGENT-003`).
- Welle-4-Abschluss-Gate (`make fullbuild` ohne Override
  mit End-to-End-Demo-Szenario).

**Anti-Scope (M3-Welle-7+ oder spaetere Folge):**

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
- Multi-Receiver-Watermark fuer `consume_for(...)`-
  Per-Receiver-Tracking; Welle 4a haelt das Tracking nicht
  vor, weil ohne registrierte Agents im Default-Pfad nicht
  benoetigt. Welle 4b oder spaetere Slice verfeinert.

## 3. Architektur-Entscheidungen

Welle 4a bringt **eine neue ADR**: ADR 0026 (Agent-Drain +
Registry + Lifecycle-Pattern). Schwester-ADR zu ADR 0023
(Welle 3 Foundation); Pattern-Pendant zu ADR 0025 (Welle 2
Recovery-Pattern, schaerft ADR 0022).

**Drain-Pfad: Pre-Tick-Schritt A0 mit `apply_command`-direct**
(D1 aus Recherche-Brief). Drei Varianten waren denkbar:

1. **Scheduler-Push** — `Command` wird in `Event` gewrappt
   und ueber den Scheduler in den naechsten Tick gepoppt.
   *Abgelehnt*: Scheduler ist fuer Events, nicht Commands.
   Command-zu-Event-Wrap ist Vorgriff auf M5-Material;
   `Scheduler.add(event)` hat keine Command-Surface.
2. **`apply_command`-direct in derselben Tick (D2-Hook)**
   — TickLoop ruft `device.apply_command(...)` direkt nach
   `agent.tick(...)` in Schritt D2. *Abgelehnt*: bricht
   GG-AGENT-008 Commit-Reihenfolge-Invariante (Commands der
   aktuellen Tick wirken im selben Tick), produziert
   Re-Iteration der Devices.
3. **Pre-Tick-Schritt A0** (gewaehlt) — am Tick-Start, vor
Schritt A (LoadEvent-Overlay). Commands der vorigen Ticks
   wirken im aktuellen Tick. *Vorteil*: konsistent mit
   GG-AGENT-008; analog Welle-6b-LoadEvent-Overlay-Pattern;
   kein Scheduler-Vorgriff.

**Registry-API: TickLoop-Kwarg + Scenario-Loader-Builder**
(D2 aus Recherche-Brief). Analog Welle-6b-Devices-Pattern:
TickLoop-Konstruktor nimmt `agents`-Tuple direkt; Scenario-
Loader-Builder baut den Tuple aus `scenario.agents`-Domain-
Daten (Welle 4b). Welle-3-`_set_agents_for_testing(...)`-
Helper wird **entfernt** — Tests stellen auf
Konstruktor-Kwarg um.

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
   (`isinstance(agent, _RandomAttachableAgent)`).
3. **Agent zieht sich seinen Sub-Port selbst aus dem Bus**
   — Bus-Konstruktor nimmt `RandomPort`-Referenz.
   *Abgelehnt*: Bus haelt Welle-3-konform keinen
   `RandomPort`-Slot (Welle-3-Review-Folge M-3); Welle 4a
   fuehrt das auch nicht ein, weil der Bus selbst keine
   stochastischen Operationen hat.

**Drain-Eviction: `consume_for(receiver)` destruktiv**
(D4 aus Recherche-Brief). Variante mit `evict_before(
simulation_time)` waere Per-Tick-Eviction (alle Messages vor
einer Zeit werden geloescht, unabhaengig vom Receiver).
*Abgelehnt*: bricht Multi-Receiver-Szenarien — wenn Agent A
um t=1000 publiziert und Agent B die Message erst um t=2000
lesen will, wuerde `evict_before(t=1500)` die Message
vorzeitig entfernen. Per-Receiver-Granularitaet ist die
robuste Wahl.

**Snapshot-Vertrag fuer Welle 4a**: kein Sub-Snapshot-Slot
fuer `_pending_agent_commands` oder Agents in
`TickLoop.snapshot()`. Welle-4a-Default-TickLoop hat
`agents=()`; `_pending_agent_commands` bleibt leer.
Welle-4b-RuleBasedAgent-Konkretisierung fuegt die Sub-
Snapshot-Slots additiv per ADR 0015 §2.3 ein. ADR 0023 §6
verbindliche Welle-4-Konsequenz „Agent-Sub-Snapshot-Slot
in `TickLoop.snapshot()`" wird damit auf Welle 4b
verschoben.

**ADR 0025-Pattern**: Welle 4a schaerft ADR 0023 §6 ohne
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
- `welle-4a.md`-Zeile ergaenzen.

### C1 — `docs(adr)`: ADR 0026 Proposed

Neu: `docs/plan/adr/0026-agent-drain-registry-pattern.md`.
Inhalt (geplant, ~ 3000–4000 Woerter, Pattern aus ADR 0025):

- **Status**: `Proposed` (Datum 2026-05-21).
- **§1 Kontext**: Welle-3-Forward-Pointer + ADR 0023 §6.
- **§2 Entscheidung** (5 Sub-Sections):
  - §2.1 Drain-Pfad: Schritt A0 Pre-Tick mit `apply_command`-
    direct.
  - §2.2 Registry-API: TickLoop-Konstruktor-Kwarg + Scenario-
    Loader-Builder-Symmetrie.
  - §2.3 Lifecycle: `_attach_agents()` mit `set_run_id` +
    optionalem `_RandomAttachableAgent`-Sub-Protocol.
  - §2.4 Bus-Eviction: `consume_for(receiver)` destruktiv +
    Per-Receiver-Granularitaet.
  - §2.5 `AgentInvalidCommandTargetError`-Fail-Fast in
    Schritt A0.
- **§3 Begruendung**: drei Drain-Varianten, drei Registry-
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
  GG-AGENT-008 Async, Sub-Snapshot-Slots, Multi-Receiver-
  Watermark.

Plus `adr/README.md`-Zeile fuer ADR 0026 `Proposed`.

### C2 — `feat(welle-4a)`: TickLoop-Registry + Schritt-A0-Drain + consume_for + Tests

**Code (edit):**

1. `src/grid_gym/hexagon/core/agents/_protocol.py` —
   `attach_random(random: RandomPort) -> None`-Methode als
   **optionale** Surface via separates
   `_RandomAttachableAgent`-Sub-Protocol.
2. `src/grid_gym/hexagon/core/agents/bus.py` —
   `consume_for(receiver: str) -> Sequence[AgentMessage]`-
   destruktive Drain-Variante.
3. `src/grid_gym/hexagon/core/simulation/tick_loop.py`:
   - `agents: tuple[Agent, ...] = ()`-Kwarg (keyword-only).
   - `_attach_agents()`-Lifecycle (set_run_id + optional
     attach_random).
   - Schritt A0 Pre-Tick-Drain (vor Schritt A).
   - Welle-3-`_set_agents_for_testing(...)` entfernt.
4. `src/grid_gym/hexagon/core/scenario/loader.py` —
   `build_tick_loop(..., agents=...)`-Builder-Symmetrie.
5. `src/grid_gym/hexagon/core/errors.py` —
   `AgentInvalidCommandTargetError`-Subklasse von
   `AgentBusError`.

**Tests (neu/edit):**

6. `tests/unit/hexagon/core/agents/test_bus.py` — Tests fuer
   `consume_for(...)`-Destruktiv-Vertrag, Watermark-
   Sanity, Roundtrip mit drain_for-Parallel.
7. `tests/unit/hexagon/core/simulation/test_tick_loop_welle_3_agent.py`
   — Umstellung von `_set_agents_for_testing` auf
   Konstruktor-Kwarg; **Datei umbenannt** zu
   `test_tick_loop_welle_4a_agent.py` (Pattern-Konsistenz
   zur Welle-Bezeichnung).
8. Neue Tests fuer Schritt-A0-Drain:
   `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_drain.py`
   — Drain-Order, Drain-vor-LoadEvent, Multi-Agent-Drain,
   `AgentInvalidCommandTargetError`-Fail-Fast.
9. Neue Tests fuer `_attach_agents()`-Lifecycle:
   `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_lifecycle.py`
   — `set_run_id`-Aufruf, optionaler `attach_random`-Aufruf,
   Sub-Port-Namens-Konvention.
10. `tests/unit/hexagon/core/scenario/test_loader_welle_6b.py`
    — `build_tick_loop(agents=...)`-Forwarding-Test (analog
    Welle-3-Review-Folge-3-L-1-Pattern).

### C3 — `docs(plan)`: Welle-4a Status/DoD-Sync

- `docs/plan/adr/0026-agent-drain-registry-pattern.md` —
  `Proposed → Provisional` mit Welle-4a-Merge-Hash (C2).
- `docs/plan/adr/README.md` — ADR 0026 auf `Provisional`.
- `docs/plan/planning/in-progress/M3-faults-agents-observability.md`
  — §0 Status: „Welle 4a abgeschlossen am 2026-05-21" mit
  Welle-4a-Commit-Stack; §3 Welle 4 mit Sub-Slicing-Note
  + Welle-4a-`Done`-Tag + Commit-Refs; „Naechster Schritt:
  Welle 4b (RuleBasedAgent + Scenario-Schema)".
- `docs/plan/planning/in-progress/welle-4a.md` (dieses
  Dokument) — auf `Done` nach C3-Closure.

## 5. Critical Files

| Pfad                                                                | Commit  | Aktion |
| ------------------------------------------------------------------- | ------- | ------ |
| `docs/plan/planning/in-progress/welle-3.md` → `done/welle-3.md`     | Pre-C0  | git mv (rename-only, `a24f733`) |
| `docs/plan/planning/in-progress/welle-4a.md`                        | C0      | NEU (dieses Dokument) |
| `docs/plan/planning/in-progress/README.md`                          | C0      | EDIT (welle-3→welle-4a) |
| `docs/plan/adr/0026-agent-drain-registry-pattern.md`                | C1      | NEU |
| `docs/plan/adr/README.md`                                           | C1      | EDIT (ADR 0026 Zeile) |
| `src/grid_gym/hexagon/core/agents/_protocol.py`                     | C2      | EDIT (`attach_random`-optional-Surface) |
| `src/grid_gym/hexagon/core/agents/bus.py`                           | C2      | EDIT (`consume_for(...)` destruktiv) |
| `src/grid_gym/hexagon/core/simulation/tick_loop.py`                 | C2      | EDIT (`agents=`-Kwarg + Schritt-A0-Drain + `_attach_agents()`; `_set_agents_for_testing` entfernt) |
| `src/grid_gym/hexagon/core/scenario/loader.py`                      | C2      | EDIT (`build_tick_loop(agents=)`-Symmetrie) |
| `src/grid_gym/hexagon/core/errors.py`                               | C2      | EDIT (`AgentInvalidCommandTargetError`) |
| `tests/unit/hexagon/core/agents/test_bus.py`                        | C2      | EDIT (consume_for-Tests) |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_3_agent.py` → `test_tick_loop_welle_4a_agent.py` | C2 | RENAME + EDIT (Konstruktor-Kwarg statt `_set_agents_for_testing`) |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_drain.py` | C2  | NEU (Schritt-A0-Drain-Tests) |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_lifecycle.py` | C2 | NEU (`_attach_agents()`-Tests) |
| `tests/unit/hexagon/core/scenario/test_loader_welle_6b.py`          | C2      | EDIT (`agents=`-Forwarding-Test) |
| `docs/plan/adr/0026-agent-drain-registry-pattern.md`                | C3      | EDIT (Status → Provisional) |
| `docs/plan/adr/README.md`                                           | C3      | EDIT (Status → Provisional) |
| `docs/plan/planning/in-progress/M3-faults-agents-observability.md`  | C3      | EDIT (§0 + §3 Welle 4a Closure) |
| `docs/plan/planning/in-progress/welle-4a.md`                        | C3      | EDIT (Status → Done) |

## 6. Verifikationspfad

End-to-End ueber `make`-Targets (Dockerfile-Stages, Docker-only
nach Repo-Konvention):

1. **`make test-unit`** — gruen mit ~12–18 neuen Tests
   (consume_for-Destruktiv-Vertrag, Schritt-A0-Drain-Order,
   `_attach_agents()`-Lifecycle, Konstruktor-Kwarg-
   Forwarding, Fail-Fast-Errors). Test-Count steigt von 889
   (Welle-3-Endstand) auf ~901–907. Welle-3-Tests, die
   `_set_agents_for_testing(...)` nutzten, werden auf den
   Konstruktor-Kwarg umgestellt — Tests bleiben gruen, nur
   die API-Aufruf-Syntax aendert sich.
2. **`make test-integration`** — bleibt 14 Tests gruen
   (Welle 4a hat keine neuen Integration-Tests; Welle 4b
   bringt das End-to-End-Demo-Szenario).
3. **`make gates`** — gruen ohne Override; AC-PORTS-NO-OUT
   bleibt 16 Contracts; `CRITICAL_COV_TARGETS` unveraendert
   (`core/agents` ist seit Welle 3 enthalten und wird durch
   Welle-4a-Code weiter ausgenutzt).
4. **`make fullbuild`** — gruen ohne Override (Welle 4a hat
   keine OTLP-Pflicht; M3-Welle-4-Abschluss-Gate folgt mit
   Welle 4b).
5. **ADR-0026-Status sichtbar `Provisional`** nach C3.
6. **ADR 0023 bleibt `Provisional`** (Welle 4a schaerft
   ohne Supersede; keine Status-Aenderung).
7. **Welle-3-`_set_agents_for_testing`-Helper ist entfernt**
   — Welle-4a-Code-Audit-Pflicht: `grep -rn
   "_set_agents_for_testing" tests/ src/` liefert kein
   Ergebnis nach C2.
8. **Rename-Historie**: `git log --follow done/welle-3.md`
   traceable ueber Pre-C0-Rename (`a24f733`).
9. **Git-Pattern**: 5 neue Welle-4a-Commits in der
   Reihenfolge `chore(welle-4a): git mv (Pre-C0)` →
   `docs(plan): welle-4a Slice-Doc (C0)` → `docs(adr): ADR
   0026 Proposed (C1)` → `feat(welle-4a): ... (C2)` →
   `docs(plan): Welle-4a Status/DoD-Sync (C3)`.

## 7. Risiken

- **R-1 — `_set_agents_for_testing(...)`-Entfernung bricht
  Welle-3-Tests**: vier Welle-3-Tests in
  `test_tick_loop_welle_3_agent.py` nutzen den Helper.
  *Mitigation*: Welle 4a stellt sie atomar auf den
  Konstruktor-Kwarg um (im selben C2-Commit). Test-Datei
  wird in `test_tick_loop_welle_4a_agent.py` umbenannt
  (Pattern-Konsistenz zur Welle-Bezeichnung).
- **R-2 — Schritt-A0-Drain vs. LoadEvent-Overlay-Reihenfolge**:
  beide schreiben `apply_command(...)` an Devices. Wenn ein
  LoadEvent und ein Agent-Command auf dasselbe Device im
  selben Tick zielen, gewinnt LoadEvent (Welle-6b-Pattern
  „Event-Overlay nach Baseline"). *Mitigation*: Schritt A0
  drainet **zuerst** (Agent-Commands der vorigen Ticks),
  Schritt A wendet **danach** LoadEvent/Profile-Overlay an.
  Test pinnt das explizit.
- **R-3 — `_attach_agents()` mit optionalem
  `_RandomAttachableAgent`-Sub-Protocol**: Hasattr ist nicht
  typisierbar (mypy-Strict-Risiko). *Mitigation*: separate
  `_RandomAttachableAgent`-
  Sub-Protocol unter `_protocol.py`; `_attach_agents()`
  prueft via `isinstance(agent, _RandomAttachableAgent)`
  (analog Welle-1-`FaultInjectableDevice`-Pattern).
  Saubere Typisierung; keine Hasattr-Drift.
- **R-4 — ADR 0026 vs. ADR-0023-Schaerfung**: ADR 0026 ist
  separate ADR, kein Schaerfung-ohne-Supersede in ADR 0023.
  *Mitigation*: 5 substantielle Entscheidungen rechtfertigen
  eigene ADR (analog ADR 0025 zu ADR 0022). ADR 0026
  referenziert ADR 0023 §6 explizit als „erfuellt durch
  diese ADR".
- **R-5 — Sub-Slicing 4a → 4b: Welle 4a closure ohne
  konkreten Agent**: ohne RuleBasedAgent-Beispiel ist
  Welle-4a-Code zwar test-getrieben getestet, aber nicht
  in einem produktiven Lauf gepruefte. *Mitigation*:
  Welle-4a-Tests pinnen alle Pflicht-Pfade via NullAgent +
  `_OrderRecordingAgent`-Stubs (die jetzt das volle
  Protocol erfuellen). Welle 4b verifiziert End-to-End.

## 8. Wandert nach

- `done/welle-4a.md` mit M3-Welle-4b-Start als Pre-C0
  reiner-Rename-Commit (Memory-Konvention `feedback_git_mv`
  strikt). Welle 4b folgt direkt — kein `next/`-
  Zwischenschritt, weil das Sub-Slicing 4a/4b in M3-Plan §3
  vorab dokumentiert ist.
