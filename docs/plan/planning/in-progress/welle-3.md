# Welle 3 — Multi-Agent-Foundation

**Status:** In Progress — eroeffnet 2026-05-21 mit M3-Welle-3-Pre-C0-Rename
(`3dbe6af`). Welle 3 baut auf M3-Welle-1-Fault-Foundation
(`46c7353`) und M3-Welle-2-Fault-Konkretisierung
(`91d44e2`) auf: Fault-Subsystem ist abgeschlossen, M3-Slice-Plan §3
wechselt jetzt vom Faults-Sub-Bereich in den
Multi-Agent-Sub-Bereich. Welle 3 ist Foundation-only —
**konkrete Agent-Typen (`RuleBasedAgent`) kommen in Welle 4**,
analog zum Faults-Pattern (Welle 1 Foundation → Welle 2
Konkretisierung).

Kanonische Slice-Spezifikation:
[`M3-faults-agents-observability.md §3 Welle 3`](M3-faults-agents-observability.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-Tracking,
nicht Ersatz.

**Commit-Sequenz (geplant):**

- Pre-C0 `3dbe6af` — `chore(welle-3): git mv welle-2.md → done/` (rename-only).
- C0 (dieses Dokument) — `docs(plan): welle-3 Slice-Doc`.
- C1 — `docs(adr): ADR 0023 Proposed — Multi-Agent-Bus + Agent-Protocol`.
- C2 — `feat(welle-3): AgentBus-Foundation + Agent-Protocol + TickLoop-Hook + Tests`.
- C3 — `docs(plan): Welle-3 Status/DoD-Sync` (ADR 0023 →
  Provisional, M3-Plan §3 Welle-3-Done-Tag, welle-3.md →
  Done).

## 1. Context

M3-Welle-2 hat das Fault-Subsystem produktiv geschlossen
(`91d44e2` Endstand, 840 Unit-Tests + 14 Integration-Tests,
ADR 0022 `Provisional` + ADR 0025 `Provisional`):

- `FaultInjectableDevice(DeviceModel)`-Sub-Protocol +
  `FaultPort`-Driven-Port + TickLoop-Vor-Tick-Hook (Schritt A2).
- `BatteryFaultAdapter` + `GridFaultAdapter` unter
  `hexagon/core/faults/` (Domain-Orchestrierung, **nicht**
  externe Adapter — AC-ADAPTER-PURE verbietet den Pfad
  `adapters/driven/` fuer FaultPort).
- `cell_failure` + `voltage_drop` mit
  `auto-recover-after-N-ticks` + `manual-via-command`.

M3-Welle-3 startet jetzt den **Multi-Agent-Sub-Bereich**. Per
[`architecture.md §14`](../../../../spec/architecture.md#14-multi-agent-subsystem-optional):

> Agenten sind ein eigenes Kernmodul `hexagon/core/agents`,
> das […] einen eigenen, deterministisch sortierten
> `AgentMessageBus` nutzt.

Konsequenz fuer Welle 3: `AgentMessageBus` ist **Core-Klasse**,
**kein** Driven-Port — anders als FaultPort in Welle 1. Diese
Designentscheidung wird in ADR 0023 §3 gegen den FaultPort-Praezedenzfall
begruendet (siehe §3 unten).

Welle-3-Lieferumfang ist Foundation-Skelett:

- `Agent`-Sub-Protocol (analog `FaultInjectableDevice`).
- `AgentMessageBus`-Core-Klasse mit deterministisch sortiertem
  Puffer.
- `AgentMessage`-Domain-Modell (frozen dataclass mit Pflicht-
  Feldern aus `GG-AGENT-004`).
- TickLoop-Hook-Punkt **nach** Schritt D (zweite Device-
  Iteration) und **vor** Schritt E (`grid_model.update(...)`),
  analog `architecture.md §6` Tick-Loop Schritt 7
  („AgentPort (optional) erzeugt Steuerentscheidungen").
- Sub-Random-Stream-Konvention `RandomPort.sub_port(f"agent-{agent_id}")` (ADR 0007 §5.1).

Was Welle 3 **NICHT** liefert (Welle-4-Material):

- Konkrete `Agent`-Implementer (z. B. `RuleBasedAgent`).
- Agent-Decision-Logik (Welt-Zustand → Commands).
- Agents-Top-Level-Block im Scenario-Schema +
  `_assert_agent_list`-Validator.
- Konkurrierende-Strategien-Priorisierung (`GG-AGENT-005`).
- Deadline-Handling (`GG-AGENT-007`).
- Async-Kommunikation (`GG-AGENT-008`) — Welle-3-Foundation
  ist synchron; Async-Variante kommt mit ADR-Folge zu ADR 0007
  `AsyncRandomPort` (siehe ADR 0007 §6).
- LogPort/MetricsPort-Injektion in AgentBus (Welle-5/6-Material,
  siehe Risiko R-2 unten).
- Konkrete Agent-Sub-Snapshots (Welle-4-Material).

## 2. Scope

**In Scope (Welle 3):**

1. **ADR 0023** (geplant) — Multi-Agent-Bus + Agent-Protocol
   als Erweiterung der `DeviceModel`-Protokoll-Familie (ADR
   0013 §2.8). Status-Lifecycle:
   - `Proposed` mit Welle-3-C1 (separater `docs(adr)`-Commit).
   - `Provisional` mit Welle-3-C2-Merge.
   - `Accepted` mit M3-Welle-7-Closure (gemeinsam mit ADR 0022
     und ADR 0024 oder einzeln, je nach Welle-7-Sequenzierung).
2. **`Agent`-Sub-Protocol** unter
   `src/grid_gym/hexagon/core/agents/_protocol.py` mit
   Pflicht-Surface:
   - `agent_id: str`-Property.
   - `tick(context, bus) -> Sequence[Command]` — Agent-Tick-
     Methode; `context: DeviceTickContext` analog `DeviceModel`,
     `bus: AgentMessageBus` als Schreib-/Lese-Vehikel fuer
     Nachrichten.
   - `snapshot() -> Mapping[str, object]` + `from_snapshot(...)`
     fuer GG-AGENT-006 (Snapshot-/Replay-Faehigkeit).
   - `set_run_id(run_id: str) -> None` analog Welle-6a-Pattern
     fuer DeviceModel (TickLoop-Attach in Konstruktor).
3. **`AgentMessageBus`-Core-Klasse** unter
   `src/grid_gym/hexagon/core/agents/bus.py` mit:
   - `publish(message: AgentMessage) -> None` — Buffer-Append.
   - `drain_for(receiver: str) -> Sequence[AgentMessage]` —
     deterministisch sortierte Liste pro Empfaenger (Sortier-
     Vertrag: `(simulation_time, sender, sequence)`), damit bei
     gleichzeitigen Events stabiler Reihenfolgen-Output entsteht.
   - `snapshot() -> Mapping[str, object]` + `from_snapshot(...)`.
   - Konstruktor-Injection fuer `RandomPort.sub_port("agents")`
     als Bus-Sub-Stream-Quelle (Welle-3-Foundation nutzt das
     nicht; Welle 4/5 kann pro Agent eigene Substreams über
     `RandomPort.sub_port(f\"agent-{agent_id}\")` anbinden —
     analog Welle-2-Battery-Seed-Independence).
4. **`AgentMessage`-Domain-Modell** unter
   `src/grid_gym/hexagon/core/domain/agent_message.py` als
   frozen dataclass mit den `GG-AGENT-004`-Pflicht-Feldern:
   - `simulation_time: int` (ms).
   - `sender: str` (`agent_id`).
   - `receiver: str` (`agent_id` oder `"*"` fuer Broadcast).
   - `message_type: str` (Domain-spezifisch; keine Whitelist
     in Welle 3).
   - `payload: Mapping[str, object]` (frozen via
     `dict`-snapshot bei `__post_init__`).
   - `sequence: int` (per-Tick-monoton aufsteigend, vom Bus
     vergeben).
5. **TickLoop-Konstruktor** erhaelt neuen keyword-only-Kwarg
   `agent_bus: AgentMessageBus | None = None` (analog ADR 0022
   §2.5 `fault_port`). Default `None` skippt den Hook.
6. **TickLoop-Hook-Position**: zwischen Schritt D (zweite
   Device-Iteration) und Schritt E (`grid_model.update(...)`)
   im aktuellen `tick_loop.py:300-345`-Block. Begruendung:
   Architektur §6 Tick-Loop Schritt 7 sieht Agents NACH der
   Geraete-Iteration und VOR Commit; AgentBus-Hook landet
   damit nach allen Telemetry-Emissionen, sodass Agents auf
   den fertigen Welt-Zustand reagieren koennen.
   **Konkret**: pro registriertem Agent ruft TickLoop
   `agent.tick(context, bus) -> Sequence[Command]`; emittierte
   Commands gehen in den `Scheduler` und werden im **naechsten**
   Tick wirksam (Welle-3-Foundation; in-Tick-Wirksamkeit ist
   Welle-4-Decision).
7. **Sub-Random-Stream-Konvention**:
   `RandomPort.sub_port(f"agent-{agent_id}")` als Per-Agent-
   Stream-Vehikel (analog Fault-Stream-Konvention aus ADR 0007
   §5.1 / ADR 0013 §4). Trigger 011 (Sub-Seed-Wortbreite) wird
   in Welle 3 **explizit NICHT aktiviert** — Welle-3-Skala
   liegt bei < 100 Sub-Streams, weit unter 10⁶-Aktivierungs-
   schwelle.
8. **`AgentBusError`-Family** unter
   `src/grid_gym/hexagon/core/errors.py` als Basis-Subklasse
   von `GridGymError`. Welle-3-Surface enthaelt nur die Basis;
   konkrete Subklassen (`AgentUnknownReceiverError` etc.) kommen
   mit Welle 4.
9. **`build_tick_loop`-Builder-Symmetrie**: der Scenario-
   Loader-Builder aus ADR 0021 §2.4 wird um den
   `agent_bus: AgentMessageBus | None = None`-Kwarg erweitert
   und reicht den Wert unveraendert an den TickLoop-Konstruktor
   durch. Default bleibt `None`; bestehende Tests bleiben
   gruen.
10. **`CRITICAL_COV_TARGETS`-Default** im Dockerfile um
    `src/grid_gym/hexagon/core/agents` und
    `src/grid_gym/hexagon/core/domain/agent_message.py`
    erweitert.

**Anti-Scope:**

- Konkrete `Agent`-Implementer (`RuleBasedAgent` etc.) — Welle 4.
- Decision-Logik (Welt-Zustand → Commands) — Welle 4.
- Agents-Top-Level-Block im Scenario-Schema +
  `_assert_agent_list` — Welle 4.
- `GG-AGENT-005` Konkurrierende Strategien — Welle 4 oder
  Welle-4-Folge.
- `GG-AGENT-007` Deadlines — Welle 4 oder Welle-4-Folge.
- `GG-AGENT-008` Async-Kommunikation — Welle 4-Folge oder
  ADR-Folge zu ADR 0007 `AsyncRandomPort`.
- LogPort/MetricsPort-Injektion in AgentBus — Welle 5/6
  (Observability-Sub-Bereich).
- Multi-Fault-Concurrent-Agent-Application — separater Slice
  nach M3-Welle-7.
- RL-Adapter (`GG-FUTURE-001/002`) — eigener Slice nach M3.
- Snapshot-Schema-Bump v2 → v3 — additive Sub-Snapshots
  (Welle 4) reichen; v3-Bump bleibt M6.

## 3. Architektur-Entscheidungen

Welle 3 bringt **eine neue ADR**: ADR 0023 (Multi-Agent-Bus +
Agent-Protocol). Status-Lifecycle siehe §2 Punkt 1.

**Sub-Protocol-Pattern**: `Agent` ist ein eigenstaendiges
Protocol — **NICHT** `Agent(DeviceModel, Protocol)`. Agents
sind keine Geraete; sie haben weder `apply_command(...)` noch
`telemetry()` noch `tick(context) -> Sequence[TelemetryPoint]`.
ADR 0023 §2.1 begruendet den Unterschied gegen ADR 0022 §2.1
(FaultInjectableDevice **erbt** von DeviceModel, weil Faults
auf Geraeten wirken; Agents stehen **neben** den Geraeten).

**AgentBus als Core-Klasse, nicht Driven-Port** (zentrale
Pattern-Drift-Entscheidung gegen ADR 0022):

- ADR 0022 hat `FaultPort` als Driven-Port modelliert.
- ADR 0023 modelliert `AgentMessageBus` als **Core-Klasse**.
- Begruendung in ADR 0023 §3:
  1. Architektur §14 schreibt explizit „eigenes Kernmodul
     `hexagon/core/agents`" und „eigener AgentMessageBus" —
     Driven-Port waere Architektur-Drift.
  2. Architektur §4.2 Driven-Ports-Tabelle listet
     **keinen** AgentPort/AgentBusPort.
  3. AgentBus haelt produktiven State (Message-Buffer,
     Sequence-Counter, Snapshot-Surface). Driven-Ports sind
     per ADR 0002 §A-1 zustandsfreie Protocols (`AC-PORTS-NO-OUT` erzwingt das); ein zustandsbehafteter Port waere
     Pattern-Bruch.
  4. Test-Isolierung (`GG-AGENT-002`) wird ueber das `Agent`-
     Sub-Protocol erreicht, nicht ueber Port-Mocking. Agents
     ohne laufende Gesamtsimulation testen heisst: `Agent`-
     Instanz mit `AgentMessageBus`-Test-Doubles im Unit-Test
     direkt instanziieren.

**TickLoop-Hook-Position** (Schritt 7 per Architektur §6):
zwischen Schritt D und E im aktuellen `tick_loop.py`-Code.
Konkrete Position-Entscheidung:

- **NACH** zweiter Device-Iteration (alle Telemetry emittiert,
  Welt-Zustand stabil).
- **VOR** `grid_model.update(...)` (Bilanz-Aggregation soll
  nicht durch Agent-Commands beeinflusst werden — Agents
  schreiben in den Scheduler, nicht direkt auf Devices).

Order-Pflicht: Agents emittieren Commands, die im **naechsten**
Tick wirksam werden — keine in-Tick-Mutation. Begruendung:
GG-AGENT-008 sagt explizit „Asynchrone Verarbeitung darf die
Commit-Reihenfolge eines Ticks nicht veraendern". In-Tick-Wirksamkeit
(Re-Iteration der Devices nach Agent-Commands)
ist eine eigene Entscheidung fuer Welle 4 oder spaeter.

**Observability-Vorgriff-Klausel** (M3-Plan §5 Risiko
„Observability-Ports-Vorgriff durch Multi-Agent/Faults"):
ADR 0023 §2.6 verbietet explizit `LogPort`/`MetricsPort`/
`TracePort`-Injektion in `AgentMessageBus`/`Agent` in Welle 3.
Welle-3-Foundation emittiert **keine** Logs/Metrics/Traces.
ADR 0024 (Observability-Foundation, Welle 5) entscheidet das
Wiring; bis dahin ist Agent-Decision-Audit-Trail
out-of-scope. Wenn Welle 4 (RuleBasedAgent-Konkretisierung)
ein Audit-Bedarf findet, schreibt sie eine ADR-Folge zu
ADR 0023.

**Trigger 011 nicht aktiv**: Sub-Seed-Wortbreite-Frage
(`open/011`) wird in Welle 3 **explizit NICHT** entschieden.
Aktivierungs-Kriterium ist `> 10⁶ Sub-Ports pro Lauf` oder
`MLRandomPort`-Spike — Welle-3-Foundation hat < 100 Sub-Ports
(typischerweise 1-10 Agents pro Scenario). Trigger 011
bleibt in `open/`. Welle-4-Konkretisierung pruefen erneut,
falls RuleBasedAgent stochastische Decisions hat.

**Snapshot-Vertrag** (analog ADR 0022 §2.6): Welle-3-Foundation
fuegt **keinen** neuen Sub-Snapshot-Key in
`TickLoop.snapshot()` hinzu. AgentMessageBus haelt zwar State
(Message-Buffer, Sequence-Counter), aber:

- Welle 3 registriert **keine** Agents in der Default-
  `TickLoop`-Konfiguration; `agent_bus=None` ist Default.
- Wenn ein Test einen `agent_bus` setzt, ist es Test-
  Verantwortung, den Snapshot-Roundtrip selbst zu pruefen.
- Welle-4-Konkretisierung wird einen Sub-Snapshot-Slot
  `agents.<agent_type>.<agent_id>` einfuehren — additiv per
  ADR 0015 §2.3, ohne Schema-Bump.

ADR 0007/0013/0014/0015/0017/0021/0022 bleiben **alle
`Accepted` bzw. `Provisional` unveraendert**; Welle 3 schaerft
ohne Supersede.

## 4. Liefer-Reihenfolge

### Pre-C0 — `chore`: git mv welle-2.md → done/ (rename-only, `3dbe6af`)

Reiner Rename ohne Inhaltsumschreibung — `feedback_git_mv`-Konvention.
Welle-2-Slice-Begleit-Doc wandert von
`in-progress/` nach `done/`, damit C0 ein neues
`welle-3.md` in `in-progress/` eroeffnen kann ohne
Pfad-Kollision.

### C0 — `docs(plan)`: welle-3 Slice-Doc (dieses Dokument)

Dieses Dokument als Welle-Start-Marker. Status:
`In Progress`. Kein Code. Plus
`in-progress/README.md`-Sync:
- `welle-2.md`-Zeile entfernen (jetzt in `done/`).
- `welle-3.md`-Zeile ergaenzen.

### C1 — `docs(adr)`: ADR 0023 Proposed

Neu: `docs/plan/adr/0023-agent-bus-protocol.md`. Inhalt
(geplant, ~ 3000–4000 Woerter, Pattern aus ADR 0022):

- **Status**: `Proposed` (Datum 2026-05-21).
- **§1 Kontext**: M3-Welle-3 startet Multi-Agent-Sub-Bereich;
  Architektur §14 schreibt eigenes Kernmodul + AgentMessageBus
  vor.
- **§2 Entscheidung** (6 Sub-Sections):
  - §2.1 `Agent`-Protocol unter `hexagon/core/agents/_protocol.py`.
  - §2.2 `AgentMessageBus`-Core-Klasse unter
    `hexagon/core/agents/bus.py`.
  - §2.3 `AgentMessage`-Domain-Modell unter
    `hexagon/core/domain/agent_message.py`.
  - §2.4 TickLoop-Hook-Position (Schritt 7).
  - §2.5 `agent_bus: AgentMessageBus | None`-Kwarg mit
    Default `None` (analog `fault_port`).
  - §2.6 Observability-Vorgriff-Verbot fuer Welle 3.
- **§3 Begruendung**:
  - AgentBus vs. Driven-Port: Pattern-Drift gegen ADR 0022,
    begruendet mit Architektur §14 + zustandsbehaftete
    Surface.
  - Agent-Protocol vs. DeviceModel-Erweiterung: Agents sind
    keine Geraete, ADR 0013 §2.8-konform via separates
    Protocol.
  - TickLoop-Hook-Position: Schritt 7 per Architektur §6;
    in-Tick-Wirksamkeit verboten (GG-AGENT-008).
- **§4 Reichweite**: In (Welle 3) — Protocol + Bus + Domain +
  TickLoop-Hook + Builder-Symmetrie. Out (Welle 4+) — konkrete
  Agents, Decision-Logik, Async-Variante, Scenario-Schema-
  Erweiterung.
- **§5 Operative Artefakte**: Dateipfade analog Critical-Files.
- **§6 Konsequenzen**: Welle-4-Implementer hat klare
  Schnittstelle; AgentMessage-Domain-Modell ist canonical_json-
  stabil; Trigger 011 bleibt in `open/`.
- **§7 Nicht Gegenstand**: konkurrierende Strategien
  (GG-AGENT-005), Deadlines (GG-AGENT-007), Async
  (GG-AGENT-008), Observability-Wiring (Welle 5/6).

Plus `adr/README.md`-Zeile fuer ADR 0023 `Proposed`.

### C2 — `feat(welle-3)`: AgentBus-Foundation + Tests

**Code (neu):**

1. `src/grid_gym/hexagon/core/agents/_protocol.py` — `Agent`-
   Sub-Protocol.
2. `src/grid_gym/hexagon/core/agents/bus.py` — `AgentMessageBus`-
   Core-Klasse.
3. `src/grid_gym/hexagon/core/agents/__init__.py` — Re-exports
   (`Agent`, `AgentMessageBus`).
4. `src/grid_gym/hexagon/core/domain/agent_message.py` —
   `AgentMessage`-frozen-dataclass.

**Code (edit):**

5. `src/grid_gym/hexagon/core/simulation/tick_loop.py` —
   `agent_bus: AgentMessageBus | None = None`-Kwarg im
   Konstruktor + Hook zwischen Schritt D und E.
6. `src/grid_gym/hexagon/core/scenario/loader.py` (oder wo der
   Builder lebt) — `build_tick_loop(agent_bus=...)`-Symmetrie.
7. `src/grid_gym/hexagon/core/errors.py` — `AgentBusError`-
   Basis-Subklasse von `GridGymError`.
8. `Dockerfile` — `CRITICAL_COV_TARGETS` + `core/agents` und
   `core/domain/agent_message.py`.

**Tests (neu):**

9. `tests/unit/hexagon/core/agents/__init__.py` +
   `test_protocol.py` — Protocol-Conformance (`NullAgent`-
   Stub-Pattern aus M2-Welle-1).
10. `tests/unit/hexagon/core/agents/test_bus.py` —
    Determinismus-Sort + Snapshot-Roundtrip + Sequence-
    Monotonie.
11. `tests/unit/hexagon/core/domain/test_agent_message.py` —
    Frozen-Vertrag + canonical_json-Stabilitaet (analog M1-
    Welle-1-Pattern).
12. `tests/unit/hexagon/core/simulation/test_tick_loop_welle_3_agent.py` —
    Hook-Order: (a) None-Default skippt sauber; (b) mit
    AgentBus + `NullAgent` werden Commands in den Scheduler
    geschoben; (c) TickResult bleibt deterministisch.

### C3 — `docs(plan)`: Welle-3 Status/DoD-Sync

- `docs/plan/adr/0023-agent-bus-protocol.md` —
  `Proposed → Provisional` mit Welle-3-Merge-Hash (C2).
- `docs/plan/adr/README.md` — ADR 0023 auf `Provisional`.
- `docs/plan/planning/in-progress/M3-faults-agents-observability.md`
  — §0 Status: „Welle 3 abgeschlossen am 2026-05-21" mit
  Welle-3-Commit-Stack; §3 Welle 3 mit `Done`-Tag + Commit-
  Refs; „Naechster Schritt: Welle 4 (Multi-Agent-Subsystem
  konkret)".
- `docs/plan/planning/in-progress/welle-3.md` (dieses
  Dokument) — auf `Done` nach C3-Closure.

## 5. Critical Files

| Pfad                                                                | Commit  | Aktion |
| ------------------------------------------------------------------- | ------- | ------ |
| `docs/plan/planning/in-progress/welle-2.md` → `done/welle-2.md`     | Pre-C0  | git mv (rename-only, `3dbe6af`) |
| `docs/plan/planning/in-progress/welle-3.md`                         | C0      | NEU (dieses Dokument) |
| `docs/plan/planning/in-progress/README.md`                          | C0      | EDIT (welle-2→welle-3) |
| `docs/plan/adr/0023-agent-bus-protocol.md`                          | C1      | NEU |
| `docs/plan/adr/README.md`                                           | C1      | EDIT (ADR 0023 Zeile) |
| `src/grid_gym/hexagon/core/agents/_protocol.py`                     | C2      | NEU (`Agent`-Protocol) |
| `src/grid_gym/hexagon/core/agents/bus.py`                           | C2      | NEU (`AgentMessageBus`) |
| `src/grid_gym/hexagon/core/agents/__init__.py`                      | C2      | EDIT (Re-exports) |
| `src/grid_gym/hexagon/core/domain/agent_message.py`                 | C2      | NEU (`AgentMessage`-frozen) |
| `src/grid_gym/hexagon/core/simulation/tick_loop.py`                 | C2      | EDIT (Kwarg + Hook) |
| `src/grid_gym/hexagon/core/scenario/loader.py`                      | C2      | EDIT (`build_tick_loop` Symmetrie) |
| `src/grid_gym/hexagon/core/errors.py`                               | C2      | EDIT (`AgentBusError`-Basis) |
| `tests/unit/hexagon/core/agents/__init__.py`                        | C2      | NEU |
| `tests/unit/hexagon/core/agents/test_protocol.py`                   | C2      | NEU |
| `tests/unit/hexagon/core/agents/test_bus.py`                        | C2      | NEU |
| `tests/unit/hexagon/core/domain/test_agent_message.py`              | C2      | NEU |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_3_agent.py` | C2     | NEU |
| `Dockerfile`                                                        | C2      | EDIT (`CRITICAL_COV_TARGETS` + `core/agents` + `core/domain/agent_message.py`) |
| `docs/plan/adr/0023-agent-bus-protocol.md`                          | C3      | EDIT (Status → Provisional) |
| `docs/plan/adr/README.md`                                           | C3      | EDIT (Status → Provisional) |
| `docs/plan/planning/in-progress/M3-faults-agents-observability.md`  | C3      | EDIT (§0 + §3 Welle 3 Closure) |
| `docs/plan/planning/in-progress/welle-3.md`                         | C3      | EDIT (Status → Done) |

## 6. Verifikationspfad

End-to-End ueber `make`-Targets (Dockerfile-Stages, Docker-only
nach Repo-Konvention):

1. **`make test-unit`** — gruen mit ~6–10 neuen Tests
   (Protocol-Conformance, AgentMessageBus-Determinism, Snapshot-
   Roundtrip, AgentMessage-Frozen-Vertrag, TickLoop-Hook-Order).
   Test-Count steigt von 840 (Welle-2-Stand) auf ~846–850.
2. **`make test-integration`** — bleibt 14 Tests gruen (Welle-3-
   Foundation hat keine neuen Integration-Tests; Welle-4-
   Konkretisierung wird das nachholen).
3. **`make gates`** — gruen ohne Override;
   `CRITICAL_COV_TARGETS`-Default um `core/agents` und
   `core/domain/agent_message.py` erweitert; Coverage ≥ 90 %
   Line + Branch auf neuen Modulen.
4. **`make fullbuild`** — gruen ohne Override; AC-PORTS-NO-OUT
   bleibt 16 Contracts (AgentBus liegt in `core/`, nicht in
   `ports/`).
5. **ADR-0023-Status sichtbar `Provisional`** nach C3.
6. **ADR-0007/0013/0021/0022 unveraendert** (Welle 3 schaerft
   ohne Supersede; keine Status-Aenderung).
7. **Trigger 011 unveraendert in `open/`** (Welle 3 hat
   Aktivierungs-Schwelle nicht erreicht).
8. **Rename-Historie**: `git log --follow done/welle-2.md`
   traceable ueber Pre-C0-Rename (`3dbe6af`).
9. **Git-Pattern**: 5 neue Welle-3-Commits in der Reihenfolge
   `chore(welle-3): git mv (Pre-C0)` → `docs(plan): welle-3 Slice-Doc (C0)` → `docs(adr): ADR 0023 Proposed (C1)` →
   `feat(welle-3): ... (C2)` → `docs(plan): Welle-3 Status/DoD-Sync (C3)`. `git log --oneline -5` zeigt diese
   fuenf Hashes.

## 7. Risiken

- **R-1 — AgentBus-vs-FaultPort-Pattern-Drift**: ADR 0023
  bricht das Pattern von ADR 0022 (Driven-Port). Risiko: Code-
  Reviewer fragt „warum nicht Port?". *Mitigation*: ADR 0023
  §3 hat eine 4-Punkt-Begruendung (Architektur §14 + State +
  Test-Isolierung + ADR 0002 §A-1 zustandsfreie Ports).
  Welle-3-Implementer pruefen vor C1, dass die Begruendung
  vollstaendig ist.
- **R-2 — Observability-Vorgriff durch Welle-4-RuleBasedAgent**:
  Welle-3-Foundation verbietet LogPort/MetricsPort-Injektion;
  wenn Welle 4 doch ein Decision-Audit-Trail braucht, muss
  ADR-Folge zu ADR 0023 geschrieben werden. *Mitigation*: ADR
  0023 §2.6 dokumentiert das Verbot explizit; Welle-4-Slice-
  Doc pruefen vor C0, ob Audit-Bedarf besteht.
- **R-3 — Sub-Slicing-Schwelle**: Welle 3 hat 10 In-Scope-Items
  + 4 echte Decisions (AgentBus-Pattern, TickLoop-Position,
  Observability-Vorgriff, Trigger-011-Inaktivitaet). Liegt
  knapp UEBER der M3-Slice-Plan-§3-Schwelle (> 6 Items mit
  ≥ 2 echte Architektur-Entscheidungen). *Fallback*: Welle 3
  splittet in 3a (Agent-Protocol + AgentMessage-Domain) und 3b
  (AgentMessageBus-Core + TickLoop-Hook + Builder-Symmetrie).
  Wird erst entschieden, wenn C2 die Sub-Slicing-Schwelle
  ueberschreitet.
- **R-4 — TickLoop-Hook-Position-Sensitivitaet**: Schritt 7
  per Architektur §6 ist „NACH zweiter Device-Iteration und
  VOR `grid_model.update`". Wenn ein Agent-Command in derselben
  Tick wirken soll (z. B. „Schalte Battery auf Discharge"),
  muesste die Position vor Schritt B (erste Iteration) liegen
  — dann wuerden Agents aber auf den Welt-Zustand der
  *vorherigen* Tick reagieren. *Mitigation*: Welle-3-Vertrag
  ist explizit „Commands wirken im naechsten Tick"; in-Tick-
  Wirksamkeit ist Welle-4-Decision (oder eigene Slice).
- **R-5 — Async-Kommunikation (GG-AGENT-008) als Vorgriff**:
  Welle-3-Foundation ist synchron; AgentMessageBus.drain hat
  keine async-Variante. Wenn Welle 4 doch Async braucht, muss
  ADR-Folge zu ADR 0007 `AsyncRandomPort` (siehe ADR 0007 §6)
  her. *Mitigation*: GG-AGENT-008 sagt explizit „Asynchrone
  Verarbeitung darf die Commit-Reihenfolge eines Ticks nicht
  veraendern" — Async ist erlaubt, aber nicht zwingend;
  Welle-3-Foundation deckt den synchronen Pflicht-Pfad ab.

## 8. Wandert nach

- `done/welle-3.md` mit M3-Welle-4-Start als Pre-C0 reiner-
  Rename-Commit (analog Welle-2 → done/ in M3-Welle-3-Pre-C0
  `3dbe6af`; analog Welle-1 → done/ in M3-Welle-2-Pre-C0
  `0ecc773`). Memory-Konvention `feedback_git_mv` strikt.
