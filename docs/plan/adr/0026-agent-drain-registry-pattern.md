# ADR 0026 — Agent-Drain + Registry + Snapshot + Lifecycle-Pattern (M3 Welle 4a)

**Status:** Provisional — Validierung erfolgt mit M3-Welle-4a-
C2-Merge (`da18c6d`): 921 Unit-Tests gruen (Welle-3-Endstand
889 → +32 Welle-4a-Tests), 14 Integration-Tests unveraendert,
`make gates` A-1 cache-frei gruen **ohne** Override (lint,
format-check, mypy `--strict`, arch-check 16/16, coverage
94.94 % line / >90 % branch, critical-coverage `core/agents`,
dep-audit), AC-PORTS-NO-OUT bleibt KEPT (16 Contracts).
Akzeptanz mit M3-Welle-7-Closure (gemeinsam mit ADR 0022,
ADR 0023 und Welle-4b-Folge-ADR oder einzeln).
**Datum:** 2026-05-21
**Status geaendert am:** 2026-05-21 — `Proposed → Provisional`
(M3-Welle-4a-C2-Merge `da18c6d`: feat-Commit liefert
TickLoop-`agents`-Kwarg + Schritt-A0v/A0a-Drain +
`_attach_agents()`-Lifecycle + `AgentMessageBus.consume_for` +
`agent_bus`/`pending_agent_commands` Sub-Snapshots +
Resume-Match-Checks + sechs neue Error-Klassen +
Builder-Symmetrie + 32 neue Tests; Welle-3-
`_set_agents_for_testing(...)`-Helper entfernt).
**Bezug:**
[`ADR 0007`](0007-random-port.md) §5
(`RandomPort.sub_port`-Vertrag fuer Per-Agent-Sub-Streams,
analog Fault-Stream-Pattern),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-
ADR-Pattern — diese ADR schaerft ADR 0023 §6 verbindliche
Welle-4-Konsequenzen ohne Supersede),
[`ADR 0013`](0013-device-model-protocol.md) §2.6 (Lifecycle-
Pre-init-Vertrag — `_attach_agents()` spiegelt
`_attach_devices()`),
[`ADR 0015`](0015-snapshot-envelope-v2.md) §2.3 (Sub-Snapshot-
Mapping ist erweiterbar; Welle 4a fuegt `agent_bus` +
`pending_agent_commands` additiv ein, ohne v2 → v3-Bump),
[`ADR 0018`](0018-smart-meter-device-pattern.md) §2.4
(`attach_sources`-Lifecycle-Pattern als Vorlage fuer
optionalen `attach_random`-Hook),
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) §6
(GridModel-v2-Overlay-Snapshot — Welle 4a verdrahtet ihn im
`build_tick_loop`-Builder als Single Source of Truth fuer
Resume-Match-Checks),
[`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
§2.4 (`build_tick_loop(...)`-Builder-Symmetrie; Welle 4a
ergaenzt `agents`-Kwarg) und §2.5/§2.7 (Vor-Tick-Block —
Welle 4a fuegt Schritt A0 vor Schritt A ein),
[`ADR 0022`](0022-fault-injection-protocol.md) §2.4 (TickLoop-
Hook-Pattern; Welle 4a spiegelt das mit eigenem Pre-Tick-
Slot fuer Agent-Command-Drain),
[`ADR 0023`](0023-agent-bus-protocol.md) §2.4 + §2.5 + §6
(Welle-3-Foundation; ADR 0026 schaerft §6 Welle-4-Konsequenzen),
[`ADR 0025`](0025-fault-recovery-pattern.md) (Pattern-Pendant:
ADR 0025 = Welle-2-Konkretisierung von Welle-1-ADR 0022;
ADR 0026 = Welle-4a-Konkretisierung von Welle-3-ADR 0023),
M3-Slice-Plan
[`in-progress/M3-faults-agents-observability.md`](../planning/in-progress/M3-faults-agents-observability.md)
§3 Welle 4 + Welle-4a-Slice-Doc
[`done/welle-4a.md`](../planning/done/welle-4a.md).
Lastenheft §15 Multi-Agent-System (`GG-AGENT-001..008`); §16
Kommunikationsschnittstellen (`GG-DATA-004` `Command`).
Architektur §6 Datenfluss Tick-Loop (Schritt 7 + neuer
Schritt A0), §14 Multi-Agent-Subsystem.

---

## 1. Kontext

M3-Welle-3 (`3dbe6af..6f8b09b`) hat die Multi-Agent-Foundation
produktiv abgeschlossen: `Agent`-Sub-Protocol +
`AgentMessageBus`-Core-Klasse + `AgentMessage`-frozen-
dataclass + TickLoop-Schritt-D2-Hook +
`_pending_agent_commands: list[Command]`-Buffer +
`agent_bus`-Builder-Symmetrie + `AgentBusError`-Family. 889
Unit-Tests + 14 Integration-Tests; `make gates` A-1 ohne
Override gruen. Vier Welle-3-Review-Folgen haben die
Foundation auf den heutigen Stand gebracht; mehrere
Pflicht-Themen wurden explizit nach Welle 4 verschoben (ADR 0023
§6 verbindliche Welle-4-Konsequenzen).

M3-Welle-4 ist die produktive Konkretisierung und wird in
zwei Teilwellen geliefert (Sub-Slicing nach M3-Slice-Plan §3
Sub-Slicing-Schwelle):

- **Welle 4a — Foundation-Plumbing** (diese ADR):
  Drain + Registry + Snapshot + Lifecycle. Keine konkreten
  Agent-Implementer; Welle-4a-Tests pinnen alle Pflicht-Pfade
  via NullAgent + `_OrderRecordingAgent`-Stubs.
- **Welle 4b — RuleBasedAgent + Scenario-Schema**: konkrete
  Implementer + `agents`-Top-Level-Block im Scenario-Schema +
  Property-Determinismus-Tests + konkrete Agent-Instanz-
  Snapshots + End-to-End-Demo-Szenario + Welle-4-Gate
  (`make fullbuild` ohne Override).

Pattern: ADR 0026 ist Schwester-ADR zu ADR 0023; Pattern-
Pendant zu ADR 0025 (Welle-2-Konkretisierung von Welle-1-
ADR 0022). Schaerfung-ohne-Supersede analog ADR 0011-Pattern.

Welle 4a deckt drei aus ADR 0023 §6 verbindlich an Welle 4
zugewiesene Themen ab:

- **Agent-Registry** im TickLoop (Welle-3-`_agents = ()` wird
  produktiv).
- **Drain-Pfad** fuer das in Welle 3 eingefuehrte
  `_pending_agent_commands`-Buffer (Welle-3-Review-Folge-2-
  F-1, Welle 3 hat Commands nur gepuffert, nicht ausgefuehrt).
- **Agent-Foundation-State-Snapshot** in `TickLoop.snapshot()`/
  `from_snapshot(...)` (Welle 3 hatte den Buffer ephemer
  gelassen; Snapshot zwischen Agent-Tick und Folgetick haette
  Commands verloren).

Welle 4a deckt zusaetzlich zwei Welle-3-Review-Folge-
Forward-Pointer ab:

- **Sub-Random-Stream-Konvention** `agent-{agent_id}` per
  optionalem Lifecycle-Hook (M-3 verschoben aus Welle 3).
- **Bus-Eviction-Spec** `consume_for(receiver)` mit
  Per-Receiver-Granularitaet (M-4 verschoben aus Welle 3).

---

## 2. Entscheidung

ADR 0026 fixiert sechs Punkte:

### 2.1 Drain-Pfad: Pre-Tick-Schritt A0 mit `apply_command`-direct

`TickLoop.tick()` erhaelt einen neuen Hook-Punkt **vor**
Schritt A (LoadEvent/Profile-Overlay, ADR 0021 §2.5), bewusst
zweigeteilt in eine Validierungs- (`A0v`) und eine Apply-
Phase (`A0a`):

```python
# Schritt A0v — Target-Validierung (vor clock.advance + scheduler.pop_due).
if self._pending_agent_commands:
    commands_to_apply = tuple(self._pending_agent_commands)
    for command in commands_to_apply:
        if command.target_device_id not in self._device_by_id:
            raise AgentInvalidCommandTargetError(command)
else:
    commands_to_apply = ()

# Welle-6a-Originalpfad: clock.advance + scheduler.pop_due.
self._clock.advance(self._tick_ms)
now = self._clock.now()
popped = tuple(self._scheduler.pop_due(now))

# ... Context-Aufbau, bucket_sums, manual_override_grid_ids, ...

with _tick_loop_decimal_context():
    # Schritt A0a — Apply der bereits validierten Commands.
    for command in commands_to_apply:
        target = self._device_by_id[command.target_device_id]
        target.apply_command(command)
        if isinstance(target, GridConnectionDevice):
            if target.device_id not in manual_override_grid_ids:
                manual_override_grid_ids.append(target.device_id)
    self._pending_agent_commands.clear()

    # Schritt A — Vor-Tick-Block (ADR 0021 §2.5).
    self._consume_load_inputs_into(...)
    # ...
```

**Atomizitaets-Vertrag** (A0v vor Clock/Scheduler-Mutation):
ein `AgentInvalidCommandTargetError` darf weder die Clock
fortschreiten lassen noch Scheduler-Events poppen noch
Devices partiell mutieren. A0v ist deshalb in der Konstruktor-
Pre-Phase **vor** `clock.advance(...)` platziert; ein
ungueltiges Target laesst den Tick komplett unangetastet.
A0a wendet danach die in A0v lokal kopierte Tuple in
Buffer-Reihenfolge an und leert `_pending_agent_commands`
erst nach **erfolgreichem** Apply-Durchlauf.

**Exception-Pfade**:

- `AgentInvalidCommandTargetError` ist der einzige Pfad mit
  Rollback-Atomizitaets-Versprechen (Buffer bleibt voll;
  Clock/Scheduler unangetastet; Retry/Resume sauber moeglich).
- Andere `apply_command(...)`-Exceptions (z. B. Pre-init-
  Vertragsverletzungen aus ADR 0013 §2.6) propagieren
  ungewrappt; Welle 4a verspricht **keine** Rollback-Atomizitaet
  fuer diese Pfade, laesst den Pending-Buffer aber ungeleert
  (so dass eine Welle-4b-Folge ihn explizit drainen kann).
- Fachliche Ablehnung durch in-contract Devices wird als
  `CommandResult` aus `apply_command(...)` zurueckgegeben —
  kein Exception-Pfad.

**Konflikt-Reihenfolge**:

- **LoadDevice-Baseline**: Schritt A wendet pro `LoadDevice`
  die Baseline aus `rated_power_kw` per `apply_command(
  set_power_kw)` an. Schritt A laeuft **nach** A0a; deshalb
  ueberschreibt die Baseline jeden Agent-Command auf ein
  `LoadDevice` im selben Tick. Ein Agent-Command auf einen
  `LoadDevice` ist nur dann final beobachtbar, wenn ein
  spaeteres `LoadProfile`/`LoadEvent` denselben Wert setzt
  oder eine Folge-ADR die Baseline-Regel aendert.
- **LoadEvent/Profile-Overlay**: gewinnt im selben Tick auf
  demselben Device (Welle-6b-Pattern „Event-Overlay nach
  Baseline").
- **GridConnection-Auto-Close** (Schritt C, ADR 0021 §2.7):
  ein Agent-Command auf eine `GridConnectionDevice.device_id`
  zaehlt als **manueller Override** und ergaenzt
  `manual_override_grid_ids`. Damit ueberschreibt Schritt C
  Auto-Close den Agent-Wert NICHT. LoadEvent/Profile-Overlay
  auf derselben GridConnection-ID gewinnt weiterhin (Schritt
  A laeuft nach A0a).

**Order-Vertrag** (GG-AGENT-008): Agent-Commands der
**vorigen** Ticks werden in der **aktuellen** Tick in den
Device-Command-Pfad eingespeist. Der final beobachtbare
Device-State folgt weiterhin der bestehenden TickLoop-
Praezedenz aus Schritt A/C — A0a aendert den Aufruf-Punkt,
nicht den TickLoop-Final-State-Algorithmus.

### 2.2 Registry-API: TickLoop-Konstruktor-Kwarg + Auto-Bus + Builder-Symmetrie

TickLoop-Konstruktor erhaelt einen neuen keyword-only-Kwarg
`agents: tuple[Agent, ...] = ()` (analog `devices=`,
`active_load_events=`, etc.):

```python
def __init__(
    self,
    *,
    ...
    fault_port: FaultPort | None = None,
    agent_bus: AgentMessageBus | None = None,
    agents: tuple[Agent, ...] = (),
) -> None:
    # ... bestehende Felder ...

    # Welle-4a: Agent-ID-Eindeutigkeit + Auto-Bus.
    seen_ids: set[str] = set()
    for agent in agents:
        if agent.agent_id in seen_ids:
            raise AgentDuplicateIdError(agent.agent_id)
        seen_ids.add(agent.agent_id)

    if agents and agent_bus is None:
        # Auto-Bus: nicht-leere agents ohne expliziten Bus
        # bekommen einen frischen AgentMessageBus, damit der
        # Tuple nicht still als No-op endet.
        agent_bus = AgentMessageBus()

    self._agent_bus: AgentMessageBus | None = agent_bus
    self._agents: tuple[Agent, ...] = agents
    self._pending_agent_commands: list[Command] = []
    self._attach_agents()
```

**Auto-Bus-Begruendung**: Welle-3-Hook in Schritt D2 skippt,
wenn `agent_bus is None`. Wuerde Welle 4a den `agents`-Kwarg
ohne Auto-Bus einfuehren, koennte ein Aufrufer produktive
Agents registrieren, ohne dass der Konstruktor erkennt, dass
sie nie laufen werden. Auto-Bus macht `agents=(...)`
produktiv erzwungen.

**Agent-ID-Eindeutigkeit**: `AgentDuplicateIdError` ist
typed Fail-Fast. Welle 3 hatte das nur im
`_set_agents_for_testing(...)`-Helper als ValueError; Welle
4a hebt es in den Konstruktor-Vertrag und gibt ihm eine
eigene typisierte Subklasse.

**Welle-3-`_set_agents_for_testing(...)` wird entfernt**:
Tests stellen via Konstruktor-Kwarg um. Pattern-Konsistenz
mit `devices=`.

**Builder-Symmetrie**:
`build_tick_loop(scenario, *, ..., agents=...)` reicht den
Tuple unveraendert in den Konstruktor durch. Welle 4a stellt
zusaetzlich sicher, dass der Builder
`GridModelBilanz(scenario.grid_model_config,
active_load_events=scenario.load_events,
active_load_profiles=scenario.load_profiles)` konstruiert,
damit der GridModel-v2-Overlay-Snapshot (ADR 0019 §6) den
produktiven Resume-Pfad in §2.6 absichert. Ohne
`grid_model_config` bleibt der Builder bei
`grid_model=None`; Overlay-only-Szenarien sind gueltig, haben
aber keinen snapshot-gestuetzten Overlay-Match-Check.

### 2.3 Lifecycle: `_attach_agents()` mit `set_run_id` + optionalem `attach_random`

Neue Lifecycle-Methode am TickLoop (analog
`_attach_devices()`):

```python
def _attach_agents(self) -> None:
    """Welle-4a: reicht run_id durch und attached optional
    einen Per-Agent-Sub-Random-Stream."""
    for agent in self._agents:
        agent.set_run_id(self._run_id)
        if isinstance(agent, _RandomAttachableAgent):
            agent.attach_random(
                self._random.sub_port(f"agent-{agent.agent_id}")
            )
```

`_attach_agents()` wird im Konstruktor **nach**
`_attach_devices()` aufgerufen, damit `_device_by_id` schon
gebaut ist (Welle-4a-Foundation laesst Agents keine Devices
referenzieren, aber Welle-4b-RuleBasedAgent koennte das
brauchen).

**`_RandomAttachableAgent`-Sub-Protocol** unter
`src/grid_gym/hexagon/core/agents/_protocol.py`:

```python
@runtime_checkable
class _RandomAttachableAgent(Agent, Protocol):
    """Optionales Sub-Protocol fuer Agents mit eigenem
    Sub-Random-Stream (Welle-4a, M-3-Konvention).

    `@runtime_checkable` ist Pflicht, sonst wirft Python beim
    `isinstance`-Check einen `TypeError` (siehe R-3 in
    welle-4a.md §7).
    """

    def attach_random(self, random: RandomPort) -> None:
        """Wird vom TickLoop einmal mit
        `RandomPort.sub_port(f"agent-{agent_id}")` aufgerufen.
        Agents, die keinen Sub-Stream brauchen, implementieren
        das Sub-Protocol nicht (Hasattr-frei dank `isinstance`).
        """
        ...
```

**Begruendung Sub-Protocol vs. Pflicht-Surface vs. Hasattr**:
Hasattr-Checks sind nicht typisierbar (mypy-Strict-Risiko).
Erweiterung der `Agent`-Pflicht-Surface wuerde RuleBasedAgents
ohne Stochastik zwingen, einen No-op-`attach_random` zu
implementieren. Sub-Protocol mit `@runtime_checkable` ist die
sauber typisierte Mitte (analog Welle-1-`FaultInjectableDevice`
zu `DeviceModel`, ADR 0022 §2.1).

### 2.4 Bus-Eviction: `consume_for(receiver)` als Direct-Inbox-Drain

Neue Methode am `AgentMessageBus`:

```python
def consume_for(self, receiver: str) -> Sequence[AgentMessage]:
    """Destruktive Direct-Inbox-Drain-Variante (Welle-4a,
    Welle-3-Review-Folge-M-4-Eviction-Spec).

    Liefert alle Nachrichten mit `message.receiver == receiver`
    in derselben Sortierung wie `drain_for(receiver)` UND
    entfernt nur diese aus dem Buffer. Broadcasts
    (`message.receiver == "*"`) bleiben bewusst im Buffer und
    werden weiter nicht-destruktiv ueber `drain_for(receiver)`
    ausgeliefert.

    `receiver == "*"` ist analog zu `drain_for("*")` verboten
    und wirft `AgentBusInvalidReceiverError` (Welle-3-Review-
    Folge-L-3-Vertrag).
    """
```

**Begruendung Direct-Inbox vs. Broadcast-destruktiv vs.
`evict_before`**:

- **`evict_before(simulation_time)`** waere Per-Tick-Eviction
  (alle Messages vor einer Zeit, unabhaengig vom Receiver).
  *Abgelehnt*: bricht Multi-Receiver-Szenarien — wenn Agent A
  um t=1000 publiziert und Agent B die Message erst um t=2000
  lesen will, wuerde `evict_before(t=1500)` die Message
  vorzeitig entfernen.
- **Destruktive Broadcast-Konsumption beim ersten
  `consume_for(...)`-Aufruf**: wuerde alle nachfolgenden
  Receiver vom Broadcast abschneiden. *Abgelehnt*: bricht
  GG-AGENT-008-Broadcast-Semantik.
- **Direct-Inbox-Drain** (gewaehlt): konsumiert nur
  `message.receiver == receiver`; Broadcasts bleiben
  unangetastet. *Vorteil*: schmale Eviction, keine
  Multi-Receiver-Brueche; registry-aware Fan-out/Watermark
  fuer Broadcasts bleibt Welle 4b oder spaetere Slice.

**Snapshot-Vertrag**: `consume_for(...)` veraendert den Buffer-
Inhalt, nicht das Schema-Format. Kein Bump v1 → v2 noetig.

### 2.5 Registry-/Drain-Fail-Fast-Errors

Welle 4a fuehrt zwei neue Error-Root-Klassen ein, getrennt
nach Subsystem:

```python
class AgentRegistryError(GridGymError):
    """TickLoop-Agent-Registry-Vertragsverletzungen
    (Welle-4a, ADR 0026 §2.5)."""


class AgentDuplicateIdError(AgentRegistryError):
    def __init__(self, agent_id: str) -> None:
        super().__init__(
            f"TickLoop received duplicate agent_id: {agent_id!r}"
        )


class AgentCommandDrainError(TickLoopError):
    """TickLoop-Schritt-A0-Drain-Vertragsverletzungen
    (Welle-4a, ADR 0026 §2.5). Erbt von TickLoopError, weil
    Drain ein TickLoop-internes Schritt-Vertragsproblem ist,
    kein AgentMessageBus-Fehler."""


class AgentInvalidCommandTargetError(AgentCommandDrainError):
    def __init__(self, command: Command) -> None:
        super().__init__(
            f"Schritt A0v: pending agent command targets "
            f"unknown device {command.target_device_id!r} "
            f"(command_id={command.command_id!r})"
        )
```

Plus fuenf neue TickLoop-Agent-Snapshot-Format-Errors fuer
die §2.6-Resume-Match-Checks:

- `TickLoopAgentSnapshotMissingKeysError`
- `TickLoopAgentSnapshotWrongTypeError`
- `TickLoopAgentSnapshotInvalidCommandResultError`
  (unbekannter `CommandResult`-String beim Pending-Buffer-
  Restore)
- `TickLoopAgentSnapshotDeviceMismatchError`
  (injizierte Device-ID/Typ/Snapshot-State passt nicht zum
  `devices.<type>.<id>`-Sub-Snapshot)
- `TickLoopAgentSnapshotGridModelMismatchError`
  (injiziertes `grid_model.snapshot()` passt nicht zum
  `grid_model`-Sub-Snapshot)
- `TickLoopAgentSnapshotLoadOverlayMismatchError`
  (injizierte `active_load_events`/`active_load_profiles`
  passen nicht zum persistierten GridModel-Overlay-State,
  wenn ein `grid_model`-Sub-Snapshot existiert)

Alle TickLoop-Agent-Snapshot-Format-Errors erben von
`TickLoopSnapshotFormatError` (Welle-0a-Pattern).

**Malformed `agent_bus`-Sub-Snapshots werden NICHT in
TickLoop-Agent-Errors gewrappt**: `AgentMessageBus.from_snapshot
(...)` hat bereits eine eigene `AgentBusSnapshot*`-Taxonomie
(Welle 3); TickLoop delegiert malformed `agent_bus`-Sub-
Snapshots unveraendert und propagiert die bestehenden
`AgentBusSnapshot*`-Errors unwrapped. Neue TickLoop-Agent-
Snapshot-Errors decken nur Agent-Foundation-State ab, den
TickLoop selbst parst (`pending_agent_commands`) oder gegen
Runtime-Dependencies matcht (Device/GridModel/LoadOverlay).

### 2.6 Snapshot-Vertrag: `agent_bus` + `pending_agent_commands` + Resume-Match-Checks

`TickLoop.snapshot()` haengt zwei neue Sub-Snapshots ein:

- **`agent_bus`** als Single-Instance-Sub-Snapshot, sobald
  `_agent_bus is not None` (Welle-3-`AgentMessageBus`-v1-
  Schema; ADR 0023 §2.2). Schluessel im
  `sub_snapshots`-Mapping: `"agent_bus"`.
- **`pending_agent_commands`** als Single-Instance-Sub-
  Snapshot, sobald `_pending_agent_commands` nicht leer ist.
  Format `{"version": 1, "commands": [...]}` mit den
  `Command`-Pflichtfeldern (`command_id`, `simulation_time`,
  `target_device_id`, `type`, `payload`, `validation_status`,
  `result`).
  - `result` wird als `CommandResult`-Stringwert serialisiert
    (z. B. `"ACCEPTED"`, `"IGNORED"`); beim Restore via
    `CommandResult(state["result"])` typisiert
    zurueckgeparst. Unbekannte Strings werfen
    `TickLoopAgentSnapshotInvalidCommandResultError`.
  - `payload` muss canonical-json-faehig bleiben (Mapping mit
    erlaubten Snapshot-Werten, analog bestehender Command-/
    Event-Payload-Grenzen).
  - Schluessel im `sub_snapshots`-Mapping:
    `"pending_agent_commands"`.

Diese Einhaenge-Regel ist bewusst asymmetrisch:
`agent_bus` ist ein Runtime-Capability-Signal. Ein leerer,
aber vorhandener Bus bedeutet, dass der TickLoop Agent-
Kommunikation aktiv verdrahtet hat und ein Resume diesen Bus
auch dann rekonstruieren muss, wenn dessen Message-Buffer leer
ist. `pending_agent_commands` ist dagegen nur eine
Arbeitsschlange fuer noch nicht angewendete Agent-Commands.
Ein leerer Pending-Buffer ist identisch zum Default-Zustand nach
Konstruktion/Restore und wird deshalb nicht als leerer Sub-
Snapshot persistiert. Das haelt neue Snapshots fuer agentenlose
oder gerade drain-leere Laeufe naeher an alten Snapshot-Formen
und vermeidet unnoetige Backward-Compat-Drift, ohne
Resume-Information zu verlieren.

`TickLoop.from_snapshot(...)` rekonstruiert beide Sub-
Snapshots, falls sie vorhanden sind, und nimmt optionale
Runtime-Dependency-Kwargs an:

```python
@classmethod
def from_snapshot(
    cls,
    state: Mapping[str, object],
    *,
    clock: ClockPort,
    random: RandomPort,
    devices: tuple[DeviceModel, ...] = (),
    grid_model: GridModelBilanz | None = None,
    active_load_events: tuple[LoadEvent, ...] = (),
    active_load_profiles: tuple[LoadProfile, ...] = (),
    fault_port: FaultPort | None = None,
    agents: tuple[Agent, ...] = (),
) -> "TickLoop":
    ...
```

**Auto-Bus-Praezedenz bei Resume**:

- Snapshot enthaelt `agent_bus`-Sub-Snapshot →
  `AgentMessageBus.from_snapshot(...)` rekonstruiert ihn.
- Snapshot enthaelt KEINEN `agent_bus`-Sub-Snapshot und
  `agents == ()` → `_agent_bus = None`, bestehender
  Welle-6a-Pfad unveraendert.
- Snapshot enthaelt KEINEN `agent_bus`-Sub-Snapshot und
  `agents != ()` injiziert → Restore erzeugt einen leeren
  `AgentMessageBus` (gleiche Auto-Bus-Regel wie im
  Konstruktor). Backward-kompatibel, weil alte Aufrufer
  ohne `agents=...` unveraendert `agent_bus=None` bekommen.

**Resume-Match-Checks**:

- **Device-Match**: Wenn Snapshot `devices.<type>.<id>`-Sub-
  Snapshots enthaelt und `devices` injiziert wird, muessen
  IDs **und** Typen **und** Device-Snapshot-States exakt
  passen. Mismatch → `TickLoopAgentSnapshotDeviceMismatchError`.
- **GridModel-Match**: Wenn Snapshot `grid_model`-Sub-
  Snapshot enthaelt und `grid_model` injiziert wird, muss
  `grid_model.snapshot()` exakt zum Sub-Snapshot-State
  passen. Mismatch →
  `TickLoopAgentSnapshotGridModelMismatchError`.
- **LoadOverlay-Match**: Wenn `grid_model`-Sub-Snapshot
  vorhanden ist und nicht-leere `active_load_events`/
  `active_load_profiles` injiziert werden, muessen die
  Tupel exakt zum persistierten GridModel-Overlay-State
  (ADR 0019 §6) passen. Mismatch →
  `TickLoopAgentSnapshotLoadOverlayMismatchError`. Ohne
  `grid_model`-Sub-Snapshot bleiben Overlay-only-Szenarien
  gueltig, haben aber keinen verlustfreien Match-Check —
  injizierte Tupel werden nur durchgereicht.
- **Pending-Command-Target-Match**: Wenn
  `pending_agent_commands`-Sub-Snapshot nicht leer ist und
  `devices` injiziert wird, muss jede
  `command.target_device_id` im `_device_by_id`-Lookup
  existieren. Mismatch im Restore (oder spaetestens im
  ersten Tick-A0v) → `AgentInvalidCommandTargetError`.

**Welle-4a-Foundation-State-Resume-Versprechen**: ein Resume
mit injizierten Devices + Agents wendet alle persistierten
`pending_agent_commands` genau einmal an (nach dem Restore
laeuft Schritt A0a beim ersten `tick()`-Aufruf). **Keine**
konkreten Agent-Instanz-Snapshots in Welle 4a:
`agents.<agent_type>.<agent_id>` bleibt Welle-4b-Material,
weil erst konkrete Implementer eigene Snapshot-Vertraege
liefern. Welle 4a verspricht deshalb **keinen** verlustfreien
Resume beliebiger Agent-Instanz-Zustaende; verlustfrei ist
nur der generische Foundation-State (`agent_bus` +
`pending_agent_commands`) plus die validierten Runtime-
Dependencies.

---

## 3. Begründung

**Drain-Pfad: drei Varianten** (vgl. §2.1):

1. **Scheduler-Push** — `Command` wird in `Event` gewrappt
   und ueber den Scheduler in die naechste Tick gepoppt.
   *Abgelehnt*: Scheduler ist fuer Events, nicht Commands.
   Command-zu-Event-Wrap ist Vorgriff auf M5-Material;
   `Scheduler.add(event)` hat keine Command-Surface.
2. **`apply_command`-direct in derselben Tick (D2-Hook)**
   — TickLoop ruft `device.apply_command(...)` direkt nach
   `agent.tick(...)` in Schritt D2. *Abgelehnt*: bricht
   GG-AGENT-008 Commit-Reihenfolge-Invariante (Commands
   wirken in derselben Tick, in der sie emittiert wurden);
   produziert Re-Iteration der Devices.
3. **Pre-Tick-Schritt A0 mit A0v/A0a-Aufteilung** (gewaehlt)
   — am Tick-Start, vor Step-A-Baseline/Profile/Event.
   *Vorteil*: konsistent mit GG-AGENT-008; analog Welle-6b-
   LoadEvent-Overlay-Pattern; kein Scheduler-Vorgriff; A0v-
   Validierung **vor** Clock/Scheduler-Mutation garantiert
   Atomizitaet bei `AgentInvalidCommandTargetError`.

**Registry-API: drei Varianten** (vgl. §2.2):

1. **Welle-3-`_set_agents_for_testing`-Helper bleibt
   Produktiv-API**. *Abgelehnt*: Naming-Konvention
   `_set_*_for_testing` signalisiert explizit Test-only;
   Welle-3-Helper hat keine Validierung im Produktiv-Pfad.
2. **Per-Agent-Add-API** (`tick_loop.add_agent(agent)`).
   *Abgelehnt*: Welle-6a-`TickLoop`-Konstruktor ist
   immutable nach `_attach_devices()`; Per-Add-API wuerde
   Lifecycle-Pre-init-Vertrag (ADR 0013 §2.6) brechen.
3. **Konstruktor-Kwarg + Auto-Bus** (gewaehlt). Spiegelt
   `devices=`-Pattern (Welle 6a). Auto-Bus verhindert,
   dass `agents=(...)` still als No-op endet.

**Lifecycle-Hook: drei Varianten** (vgl. §2.3):

1. **Konstruktor-Param `random` pro Agent**. *Abgelehnt*:
   Konstruktor-Bloat; trennt Domain-Konstruktion (z. B.
   Regel-Tabelle) von Lifecycle (Sub-Port-Ableitung).
2. **TickLoop injiziert RandomPort in `_attach_agents()`-
   Phase** (gewaehlt). Spiegelt Welle-6b-SmartMeter-
   `attach_sources`-Pattern (ADR 0018 §2.4).
   `@runtime_checkable`-Sub-Protocol macht den Hook
   typisierbar (kein Hasattr-Drift).
3. **Bus holt sich seinen Sub-Port selbst**. *Abgelehnt*:
   Bus haelt Welle-3-konform keinen `RandomPort`-Slot
   (Welle-3-Review-Folge M-3); Welle 4a fuehrt das auch
   nicht ein.

**Bus-Eviction: drei Varianten** (vgl. §2.4):

1. **`evict_before(simulation_time)`**. *Abgelehnt*:
   Per-Tick-Eviction bricht Multi-Receiver-Szenarien.
2. **Destruktive Broadcast-Konsumption beim ersten
   `consume_for(...)`-Aufruf**. *Abgelehnt*: bricht
   GG-AGENT-008-Broadcast-Semantik.
3. **Direct-Inbox-Drain** (gewaehlt): nur
   `message.receiver == receiver`; Broadcasts bleiben
   nicht-destruktiv.

**Error-Family-Trennung** (§2.5): drei Achsen waren denkbar:

1. **Alles unter `AgentBusError`**. *Abgelehnt*:
   `AgentBusError` ist Bus-Vertrag (Welle 3); Registry-
   Fail-Fast und TickLoop-Schritt-A0-Drain-Fehler sind
   keine Bus-Probleme.
2. **Alles unter `TickLoopError`**. *Abgelehnt*: Agent-
   Registry-Duplicate ist ein Konstruktor-Vertrag, kein
   TickLoop-Schritt-Problem.
3. **Drei Roots: `AgentRegistryError` (Konstruktor),
   `AgentCommandDrainError(TickLoopError)` (Schritt A0v),
   `TickLoop*SnapshotFormatError` (Resume-Match)** (gewaehlt).
   Jede Root traegt ihren eigenen semantischen Pfad;
   Aufrufer differenzieren typisiert.

**Snapshot-Vertrag** (§2.6): drei Varianten waren denkbar:

1. **Kein Sub-Snapshot in Welle 4a** (mein urspruenglicher
   C0-Scope). *Abgelehnt*: Welle 4a macht den Drain
   produktiv; ein Snapshot zwischen Agent-Tick (Schritt
   D2) und Folgetick (Schritt A0) wuerde alle Pending-
   Commands verlieren. Foundation-State-Persistierung ist
   Welle-4a-Pflicht.
2. **Konkrete Agent-Instanz-Snapshots in Welle 4a**.
   *Abgelehnt*: Welle 4a hat keine konkreten Implementer;
   `agents.<agent_type>.<agent_id>` braucht Implementer-
   spezifische Snapshot-Vertraege (Welle 4b).
3. **Foundation-State-Persistierung** (gewaehlt):
   `agent_bus` + `pending_agent_commands` + Resume-Match-
   Checks fuer die produktiven Runtime-Dependencies
   (Devices, GridModel, LoadOverlays).

**ADR 0026 vs. Schaerfung-ohne-Supersede in ADR 0023**:
ADR 0026 ist separate ADR. Begruendung: 6 substantielle
Entscheidungen (D1..D6 aus welle-4a.md) rechtfertigen
eigene ADR, analog ADR 0025 zu ADR 0022 fuer Recovery-
Pattern. ADR 0026 referenziert ADR 0023 §6 explizit als
„erfuellt durch diese ADR".

---

## 4. Reichweite

**In Scope (Welle 4a):**

- `Agent`-Protocol-Erweiterung um `_RandomAttachableAgent`-
  Sub-Protocol (optional).
- `AgentMessageBus.consume_for(receiver)`-Methode.
- TickLoop-Konstruktor-Kwarg `agents` + Auto-Bus + Agent-
  ID-Eindeutigkeits-Validierung + `_attach_agents()`-
  Lifecycle.
- TickLoop-Schritt A0v (Pre-Clock-Target-Validierung) + A0a
  (Apply nach Clock, vor Schritt A).
- TickLoop-Snapshot-Erweiterung: `agent_bus` +
  `pending_agent_commands` Sub-Snapshots; Auto-Bus-Praezedenz
  bei Resume; Resume-Match-Checks fuer Devices/GridModel/
  LoadOverlays/Pending-Command-Targets.
- `build_tick_loop(..., agents=...)`-Builder-Symmetrie +
  GridModelBilanz-Overlay-Verdrahtung.
- Neue Error-Klassen: `AgentRegistryError` +
  `AgentDuplicateIdError`; `AgentCommandDrainError` +
  `AgentInvalidCommandTargetError`; fuenf TickLoop-Agent-
  Snapshot-Format-Errors.
- Welle-3-`_set_agents_for_testing(...)` wird entfernt;
  Tests stellen auf Konstruktor-Kwarg um.
- Tests fuer alle Pflicht-Pfade (Drain-Order, A0-Fail-Fast-
  Atomizitaet, Lifecycle, Snapshot-Roundtrip, Resume-Match-
  Checks, `consume_for`-Destruktiv-Vertrag, Auto-Bus-Regel).

**Out of Scope (Welle 4b):**

- Konkrete `Agent`-Implementer (`RuleBasedAgent` o. ae.).
- Agent-Decision-Logik.
- `agents`-Top-Level-Block im Scenario-Schema +
  `_assert_agent_list`-Validator + `ScenarioAgent`-Domain-
  Modell.
- Konkrete Agent-Instanz-Snapshots
  (`agents.<agent_type>.<agent_id>`) in
  `TickLoop.snapshot()`.
- Agent-Factory-Map analog `_DEVICE_FACTORIES`.
- Property-Determinismus-Tests pro Agent-Implementer
  (`GG-AGENT-003`).
- Welle-4-Abschluss-Gate (`make fullbuild` ohne Override mit
  End-to-End-Demo-Szenario).

**Out of Scope (Welle 4c oder spaetere Folge):**

- Deadlines (`GG-AGENT-007`).
- Async-Kommunikation (`GG-AGENT-008`) — ADR-Folge zu ADR
  0007 `AsyncRandomPort`.
- LogPort/MetricsPort-Injektion in Bus/Agent — Welle 5/6
  (ADR 0024).
- Sub-Seed-Wortbreite (Trigger 011).
- RL-Adapter (`GG-FUTURE-001/002`).
- In-Tick-Wirksamkeit fuer Agent-Commands.
- Multi-Receiver-Watermark fuer `consume_for(...)`-
  Per-Receiver-Tracking bei Broadcasts.

---

## 5. Operative Artefakte

| Pfad                                                                | Aktion |
| ------------------------------------------------------------------- | ------ |
| `src/grid_gym/hexagon/core/agents/_protocol.py`                     | EDIT (`_RandomAttachableAgent`-Sub-Protocol mit `@runtime_checkable`) |
| `src/grid_gym/hexagon/core/agents/bus.py`                           | EDIT (`consume_for(receiver)` Direct-Inbox-destruktiv) |
| `src/grid_gym/hexagon/core/simulation/tick_loop.py`                 | EDIT (`agents=`-Kwarg + Auto-Bus + Duplicate-ID + Schritt-A0v/A0a + GridConnection-Override + Agent-Foundation-State-Snapshots + Resume-Kwargs/-Match-Checks + `_attach_agents()`; `_set_agents_for_testing` entfernt) |
| `src/grid_gym/hexagon/core/scenario/loader.py`                      | EDIT (`build_tick_loop(agents=)`-Symmetrie + GridModelBilanz-Overlay-Verdrahtung) |
| `src/grid_gym/hexagon/core/errors.py`                               | EDIT (`AgentRegistryError`/`AgentDuplicateIdError` + `AgentCommandDrainError`/`AgentInvalidCommandTargetError` + fuenf TickLoopAgentSnapshot-Errors) |
| `tests/unit/hexagon/core/agents/test_bus.py`                        | EDIT (`consume_for`-Direct-Inbox-Tests + Broadcast-Retention) |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_3_agent.py` → `test_tick_loop_welle_4a_agent.py` | RENAME + EDIT (Konstruktor-Kwarg statt `_set_agents_for_testing`, Duplicate-ID-Fail-Fast, Auto-Bus) |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_drain.py` | NEU (Schritt-A0-Drain-Tests inkl. GridConnection-Override + Fail-Fast-ohne-Partial-Mutation + LoadDevice-Baseline-gewinnt) |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_lifecycle.py` | NEU (`_attach_agents()`-Tests + `_RandomAttachableAgent`-Runtime-Check) |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_4a_snapshot.py` | NEU (`agent_bus` + `pending_agent_commands`-Roundtrip + CommandResult-/Payload-Validierung + Resume-Match-Checks) |
| `tests/unit/hexagon/core/scenario/test_loader_welle_6b.py`          | EDIT (`agents=`-Forwarding-Test + GridModelBilanz-Overlay-Snapshot-Absicherung) |

ADR-Cross-Refs (read-only fuer Welle 4a):
- ADR 0013 §2.6 zitiert in `_attach_agents()`-Docstring.
- ADR 0015 §2.3 zitiert in Sub-Snapshot-Slot-Konvention.
- ADR 0018 §2.4 zitiert in `_RandomAttachableAgent`-Docstring.
- ADR 0019 §6 zitiert im Builder-GridModel-Verdrahtungs-
  Kommentar.
- ADR 0021 §2.5 zitiert im Schritt-A0-Hook-Kommentar.
- ADR 0023 §2.4 + §2.5 + §6 zitiert mehrfach (Welle-3-
  Foundation, ADR 0026 schaerft §6).
- ADR 0025 zitiert als Pattern-Pendant (Welle-2-Konkretisierung
  fuer Faults; Welle-4a-Konkretisierung fuer Agents).
- Diese ADR wird mit M3-Welle-7-Closure auf `Accepted` gehoben
  (Pattern aus ADR 0017/0018/0021/0022/0023/0025).

---

## 6. Konsequenzen

**Positive Konsequenzen:**

- Welle-4b-Implementer hat eine vollstaendige Foundation-
  Schnittstelle: produktive `agents`-Registry am TickLoop,
  Drain-Pfad, Bus-Eviction, Lifecycle-Hook, Foundation-State-
  Snapshot.
- Welle-3-Pending-Buffer wird produktiv: `_pending_agent_commands`
  wird in Schritt A0a auf Devices angewendet; Snapshot/Restore
  verliert keine Commands.
- Welle-3-`_set_agents_for_testing(...)`-Helper ist entfernt;
  Tests nutzen die produktive Konstruktor-API.
- Sub-Random-Stream-Konvention `agent-{agent_id}` ist
  produktiv verdrahtet (Welle-3-Review-Folge M-3
  abgeschlossen).
- Bus-Eviction-Spec `consume_for(receiver)` ist produktiv
  (Welle-3-Review-Folge M-4 teilweise abgeschlossen;
  Broadcast-Watermark bleibt Welle 4b oder spaetere Slice).
- TickLoop-Resume mit injizierten Devices/Agents validiert
  Runtime-Dependencies typisiert; frische Instanzen mit
  passender ID werden nicht stille als verlustfreier Resume
  durchgewinkt.

**Verbindliche Konsequenzen fuer Welle 4b:**

- Welle-4b-Implementer muessen `Agent`-Protocol vollstaendig
  erfuellen (`agent_id`, `set_run_id`, `tick`, `snapshot`,
  `from_snapshot`); optional `_RandomAttachableAgent` fuer
  Stochastik.
- Welle 4b ergaenzt `agents.<agent_type>.<agent_id>`-Sub-
  Snapshots additiv per ADR 0015 §2.3 (kein Schema-Bump).
- Welle 4b liefert das `agents`-Top-Level-Block-Schema im
  Scenario plus `_assert_agent_list`-Validator (analog
  ADR 0022 §2.3 fuer Faults).
- Welle 4b verifiziert End-to-End: `make fullbuild` ohne
  Override mit Agent-Demo-Szenario.

**Restpost — Snapshot-Schema:**

- ADR 0015 bleibt v2; Welle 4a fuegt nur additive Sub-
  Snapshots ein.
- Welle 4b fuegt konkrete Agent-Instanz-Sub-Snapshots ein
  (additiv).
- Snapshot-Bump v2 → v3 bleibt M6-Material (`GG-PERSIST-*`-
  Slice).

**Pflege-Gleichheit:**

- `_DEVICE_FACTORIES` (Scenario-Loader,
  `src/grid_gym/hexagon/core/scenario/loader.py:60-65`) ist
  von Welle 4a **nicht** betroffen — Welle 4b fuegt eine
  parallele Agent-Factory-Map ein.
- `_DEVICE_TYPE_BY_CLASS_NAME` (TickLoop) bleibt unveraendert.
- `_BILANZ_SOURCE_BUCKETS` (TickLoop) bleibt unveraendert —
  Agents emittieren keine TelemetryPoints; Bilanz-Aggregation
  ist nicht beruehrt.

---

## 7. Nicht Gegenstand

**Konkrete Agent-Implementer** (`RuleBasedAgent`, andere) —
Welle 4b. Welle 4a hat keine produktiven Decision-Loops.

**Konkrete Agent-Instanz-Snapshots**
(`agents.<agent_type>.<agent_id>`) — Welle 4b. Welle 4a
persistiert nur generischen Foundation-State.

**`agents`-Top-Level-Block im Scenario-Schema** + Validator-
Haertung — Welle 4b. Welle 4a baut den Tuple ueber den
Builder-Kwarg, nicht ueber Scenario-Daten.

**GG-AGENT-007 Deadlines** — Welle 4c oder M5. Welle-4a-
`Agent.tick(context, bus)` hat kein Deadline-Argument; eine
zukuenftige `AgentContext`-Erweiterung ist Welle-4b-oder-
spaeter-Material.

**GG-AGENT-008 Async-Kommunikation** — ADR-Folge zu ADR 0007
`AsyncRandomPort`, kein Welle-4-Material.

**Observability-Ports** (`GG-OTEL-001..004`) — Welle 5/6
(ADR 0024).

**Sub-Seed-Wortbreite-Erhoehung** (Trigger 011) — bleibt in
`open/`, Aktivierungs-Kriterium nicht erreicht.

**RL-Adapter** (`GG-FUTURE-001/002`) — eigener Slice nach
M3-Welle-7.

**In-Tick-Wirksamkeit fuer Agent-Commands** — eigene ADR-
Folge, falls Welle 4b zeigt dass sie gebraucht wird. Welle
4a-Vertrag ist explizit „Commands aus voriger Tick wirken in
aktueller Tick" (GG-AGENT-008).

**Multi-Receiver-Watermark fuer Broadcasts** — Welle 4a-
`consume_for(...)` konsumiert nur Direct-Inbox; Broadcasts
bleiben nicht-destruktiv in `drain_for(...)`. Welle 4b oder
spaetere Slice verfeinert registry-aware Fan-out/Eviction.
