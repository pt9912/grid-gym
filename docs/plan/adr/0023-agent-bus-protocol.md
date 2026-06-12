# ADR 0023 — Multi-Agent-Bus + Agent-Protocol (M3 Welle 3)

**Status:** Accepted — M3-Welle-7-Closure 2026-05-25 (C1.2).
Validierung lieferten Welle 3 (Foundation, `3dbe6af..d6f66fc`:
879 Unit-Tests gruen, AgentMessageBus + Agent-Protocol +
TickLoop-Schritt-D2-Hook produktiv), Welle 4a (Plumbing,
`a24f733..da18c6d`: 921 Unit-Tests, agents-Kwarg + Auto-Bus +
Schritt A0v/A0a + Drain/Registry/Lifecycle via ADR 0026), Welle 4b
(Konkretisierung, `8802dc0..ac7b47f`: 992 Unit-Tests +
19 Integration-Tests, RuleBasedAgent + Scenario-`agents`-Block
via ADR 0027, agents_demo.yaml + bidirektionaler Sub-Snapshot-
Resume-Match). `make gates` cache-frei gruen **ohne**
`CRITICAL_COV_TARGETS`-Override (Default-Liste enthaelt
`core/agents`); `make fullbuild` gruen; `AC-PORTS-NO-OUT` bleibt
KEPT.
**Datum:** 2026-05-21
**Status geaendert am:** 2026-05-25 — `Provisional → Accepted`
(M3-Welle-7-Closure-Lauf C1.2; ADR-Header-Schliff ohne
Architektur-Aenderung).
**Vorherige Aenderung (2026-05-21)** — `Proposed → Provisional`
(M3-Welle-3-C2-Merge `4fa122d` + Review-Folge `d6f66fc` Pre-
C3-Closure; ADR-Schaerfungen aus der Review-Folge (H-1, M-1
bis M-4) sind im jeweiligen §-Abschnitt mit
„Welle-3-Review-Folge"-Notiz markiert).
**Letzte inhaltliche Aenderung:** 2026-05-25 — `Provisional →
Accepted`-Closure-Schliff (Status-Update + Welle-3/4a/4b-Beleg
ergaenzt; keine Architektur-Aenderung).
**Bezug:**
[`ADR 0007`](0007-random-port.md) §5
(`RandomPort.sub_port`-Vertrag fuer Per-Agent-Sub-Streams,
analog Fault-Stream-Pattern; §6 listet
„`AsyncRandomPort` fuer asyncio-Multi-Agent-Bus
(`GG-AGENT-008`)" als bewusst zurueckgestellten Folge-Punkt),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-
ADR-Pattern — diese ADR erweitert `ADR 0002 §A-1`-Komponenten-
Liste um `GG-AR-COMP-AGENTS::Agent` + `AgentMessageBus`, ohne
Supersede),
[`ADR 0013`](0013-device-model-protocol.md) §2.8 (Protocol-
Evolution-Strategie fuer Post-MVP-Erweiterungen — `M3 Multi-
Agent` ist explizit als Beispiel genannt: separates Sub-
Protocol statt `DeviceModel`-Erweiterung),
[`ADR 0015`](0015-snapshot-envelope-v2.md) §2.3 (Sub-Snapshot-
Mapping ist erweiterbar; Welle 3 fuegt **keinen** neuen Sub-
Snapshot hinzu — Welle 4 wird `agents.<agent_type>.<agent_id>`
additiv einbringen),
[`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
§2.4 (`build_tick_loop(...)`-Builder-Symmetrie — Welle 3
ergaenzt `agent_bus`-Kwarg analog Welle-1-`fault_port`),
[`ADR 0022`](0022-fault-injection-protocol.md) (Welle-1-
Vorlage — Sub-Protocol + Hook-Pattern; ADR 0023 spiegelt das
**bewusst nicht 1:1** fuer den Bus selbst — siehe §3 Begruendung
„AgentBus vs. Driven-Port"),
M3-Slice-Plan
[`in-progress/M3-faults-agents-observability.md`](../planning/done/M3-faults-agents-observability.md)
§3 Welle 3.
Lastenheft §15 Multi-Agent-System (`GG-AGENT-001..008`).
Architektur §5 Komponentensicht (`GG-AR-COMP-AGENTS`),
§6 Datenfluss Tick-Loop (Schritt 7 „AgentPort (optional)
erzeugt Steuerentscheidungen"), §14 Multi-Agent-Subsystem
(„eigenes Kernmodul `hexagon/core/agents`", „eigener,
deterministisch sortierter `AgentMessageBus`"), §4.2 Driven-
Ports-Tabelle (listet **keinen** AgentPort/AgentBusPort —
AgentBus ist bewusst kein Driven-Port).

---

## 1. Kontext

M3-Welle-3 startet den **Multi-Agent-Sub-Bereich** des M3-
Slice-Plans. M3-Welle-1 (`46c7353`) hat die Fault-Foundation
(`FaultInjectableDevice` Sub-Protocol + `FaultPort` Driven-
Port + TickLoop-Vor-Tick-Hook) geliefert; M3-Welle-2
(`91d44e2`) hat die Fault-Konkretisierung (`BatteryFault`-/
`GridFault`-Adapter + Recovery-Logik + Fault-Demo-Szenario)
abgeschlossen.

Welle 3 liefert die **Multi-Agent-Foundation** — die
Architektur-Schichten, auf denen Welle 4 (`RuleBasedAgent` +
Decision-Loop) aufbauen wird. Welle 3 ist Foundation-only;
konkrete Agent-Implementer + Scenario-Schema-Erweiterung +
Decision-Logik kommen mit Welle 4 (analog Welle-1/Welle-2-
Pattern fuer Faults).

Architektur §14 ist sehr eindeutig:

> Agenten sind ein SOLLTE-Feature (`GG-AGENT-001`).
> Architektonisch sind sie ein eigenes Kernmodul
> `hexagon/core/agents`, das […] einen eigenen,
> deterministisch sortierten `AgentMessageBus`
> (`GG-AGENT-004/008`) nutzt.

Konsequenz fuer Welle 3: `AgentMessageBus` ist **Core-Klasse**
in `hexagon/core/agents/`, **kein** Driven-Port unter
`hexagon/ports/driven/`. Diese Pattern-Drift gegen ADR 0022
(`FaultPort` als Driven-Port) ist die zentrale Designent-
scheidung dieser ADR und wird in §3 ausfuehrlich begruendet.

Lastenheft `GG-AGENT-001..008` sind alle SOLLTE (keine MUSS).
Welle 3 deckt das Minimum-Skelett fuer [`GG-AGENT-001`](../../../spec/lastenheft.md#gg-agent-001)/002/003/
004/006 ab (Protocol + Test-Isolierung + Determinismus +
standardisierte Nachrichten + Snapshot-/Replay-Faehigkeit);
[`GG-AGENT-005`](../../../spec/lastenheft.md#gg-agent-005)/007/008 (konkurrierende Strategien, Deadlines,
Async-Kommunikation) bleiben Welle-4-Material oder werden
ueber separate ADR-Folgen entschieden.

Welle-1-Review-M-4 (`ADR 0022 §2.4` Exception-Propagation-
Vertrag) und das damit etablierte Hexagon-Boundary-Pattern
(typisierte `*Error`-Subklassen) gilt analog: ADR 0023 fuehrt
`AgentBusError` als Basis-Subklasse von `GridGymError` ein;
konkrete Welle-4-Subklassen werden in der Welle-4-Folge-ADR
spezifiziert.

---

## 2. Entscheidung

ADR 0023 fixiert sechs Punkte:

### 2.1 `Agent`-Sub-Protocol (eigenstaendig, nicht `DeviceModel`-erbend)

Neuer Protocol unter
`src/grid_gym/hexagon/core/agents/_protocol.py`:

```python
from typing import Protocol, runtime_checkable
from collections.abc import Mapping, Sequence
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.device import DeviceTickContext


@runtime_checkable
class Agent(Protocol):
    """Agent-Protocol fuer Multi-Agent-Steuerung (M3 Welle 3).

    Agents sind **keine** Geraete — sie haben weder
    `apply_command(...)` noch `telemetry()` noch Geraete-
    Tick-Surface. Sie konsumieren Welt-Zustand (ueber den
    AgentMessageBus) und produzieren `Command`s in den
    Scheduler. Per Architektur §14 sind Agents ein eigenes
    Kernmodul (`hexagon/core/agents`), nicht eine DeviceModel-
    Sub-Klasse.

    **Welle-3-Stand**: dieses Modul liefert nur den Protocol-
    Vertrag. Konkrete Implementer (`RuleBasedAgent`, etc.)
    kommen in Welle 4.
    """

    @property
    def agent_id(self) -> str:
        """Stabile Agent-Identitaet (analog `DeviceModel.device_id`).

        Pflicht-Pflicht: pro Run eindeutig, Snapshot-Roundtrip-
        invariant, primaere Sortier-Schluessel-Komponente im
        AgentMessageBus.
        """
        ...

    def set_run_id(self, run_id: str) -> None:
        """Wird vom TickLoop einmal nach Konstruktion aufgerufen
        (analog DeviceModel.set_run_id, ADR 0013 §2.6 Lifecycle-
        Pre-init-Vertrag)."""
        ...

    def tick(
        self,
        context: DeviceTickContext,
        bus: "AgentMessageBus",
    ) -> Sequence[Command]:
        """Agent-Tick: konsumiert Welt-Zustand (Bus-Nachrichten,
        context.simulation_time), produziert Commands.

        Aufruf-Punkt: TickLoop ruft pro Tick fuer jeden
        registrierten Agent genau einmal `agent.tick(context,
        bus)` zwischen Schritt D (zweite Device-Iteration) und
        Schritt E (`grid_model.update(...)`). Siehe §2.4.

        Determinismus-Vertrag (GG-AGENT-003): gleicher Seed +
        gleicher Eingabeverlauf (`context` + Bus-Nachrichten) →
        identische Command-Sequenz (byte-identische
        canonical_json-Serialisierung).

        Commit-Reihenfolge-Invariante (GG-AGENT-008): die vom
        Agent emittierten Commands gehen in den Scheduler und
        werden im **naechsten** Tick wirksam. Welle 3 verbietet
        in-Tick-Wirksamkeit; Welle 4 oder spaeter kann ADR-
        Folge schreiben.

        Welle-3-Foundation: Implementer-Anschluss kommt mit
        Welle 4; Welle 3 testet das Protocol gegen einen
        `NullAgent`-Stub.
        """
        ...

    def snapshot(self) -> Mapping[str, object]:
        """Persistiert lokalen Agent-Zustand (GG-AGENT-006).

        Roundtrip-Vertrag (analog ADR 0013 §2.4): `from_snapshot(
        snapshot())` muss byte-identische Agent-Instanz liefern
        (modulo `run_id`, der ueber `set_run_id(...)` neu
        gesetzt wird).
        """
        ...
```

**Closed-Set-Pattern**: `Agent` ist eigenstaendig, **nicht**
`Agent(DeviceModel, Protocol)`. Begruendung in §3 unten.

Re-export in `src/grid_gym/hexagon/core/agents/__init__.py`,
damit Aufrufer `from grid_gym.hexagon.core.agents import
Agent` schreiben koennen.

### 2.2 `AgentMessageBus`-Core-Klasse (kein Driven-Port)

Neue Core-Klasse unter
`src/grid_gym/hexagon/core/agents/bus.py`:

```python
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from grid_gym.hexagon.core.domain.agent_message import AgentMessage


class AgentMessageBus:
    """Deterministisch sortierter Message-Bus fuer Multi-Agent-
    Kommunikation (Architektur §14, GG-AGENT-004/008).

    **Architektur-Entscheidung** (siehe §3): AgentMessageBus
    ist eine **Core-Klasse**, kein Driven-Port. Per
    Architektur §14 ist „eigener, deterministisch sortierter
    AgentMessageBus" Teil des Kernmoduls; ein Driven-Port
    waere Architektur-Drift.

    Sortier-Vertrag fuer `drain_for(receiver)`:
    `(simulation_time, sender, sequence)`. Per-Tick-Sequenz-
    Counter ist Monoton-Property; Determinismus-Test pinnt
    das (analog M1-Welle-3-Scheduler-Tie-Breaking).
    """

    def __init__(self) -> None:
        self._buffer: list[AgentMessage] = []
        self._next_sequence: int = 0

    def publish(self, message: AgentMessage) -> None:
        """Append an den Buffer. Sequence-Counter ist
        Bus-Verantwortung — wenn `message.sequence` schon
        gesetzt ist, wird er respektiert (Test-Code-Pfad);
        andernfalls vergibt der Bus die naechste freie
        Nummer (Produktiv-Pfad)."""
        ...

    def drain_for(self, receiver: str) -> Sequence[AgentMessage]:
        """Liefert alle Nachrichten mit
        `message.receiver in (receiver, "*")`, sortiert nach
        `(simulation_time, sender, sequence)`.

        **Drain-Semantik (Welle 3)**: nicht-destruktiv —
        Nachrichten bleiben im Buffer; Welle 4 oder spaeter
        kann eine `consume_for(receiver)`-Variante einfuehren,
        die destruktiv liest.
        """
        ...

    def snapshot(self) -> Mapping[str, object]:
        """Buffer + Sequence-Counter als canonical_json-faehiges
        Mapping. Welle-3-Schema (`version=1`):

        ```json
        {
          "version": 1,
          "next_sequence": <int>,
          "messages": [<AgentMessage.snapshot()>, ...]
        }
        ```

        Wird in Welle-3-Default-TickLoop NICHT in das Top-
        Level-Snapshot eingehaengt — Welle-3-Default ist
        `agent_bus=None`. Welle-4-Konkretisierung wird einen
        Sub-Snapshot-Slot `agent_bus` additiv per ADR 0015 §2.3
        einfuehren.
        """
        ...

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> "AgentMessageBus":
        ...
```

**Welle-3-Buffer-Eviction-Vertrag** (Welle-3-Review-Folge M-4,
2026-05-21): Welle 3 hat **keine** Eviction-Strategie —
`drain_for(receiver)` ist nicht-destruktiv, der Buffer waechst
ueber die gesamte Lauf-Dauer. Bei realistischen
Multi-Agent-Szenarien (z. B. 5 Agents × 10 000 Ticks ×
1 Message/Tick = 50 000 Messages im Snapshot) wird das
problematisch. Welle-4-Pflicht-Spec: entweder
`consume_for(receiver)` mit Per-Receiver-Watermark
(destruktive Drain-Variante; Bus loescht Messages, sobald
alle adressierten Empfaenger sie konsumiert haben) oder per-
Tick-Eviction-Strategie (`evict_before(simulation_time)`).
ADR-Folge zu ADR 0023 §2.2 entscheidet das. Welle-3-
Foundation laesst das bewusst offen, weil ohne registrierte
Agents (`self._agents = ()` Welle-3-leer) der Buffer leer
bleibt und das Welle-4-Auswahl-Verhalten den Vertrag
mitdefiniert.

**Keine Driven-Port-Surface**: AgentMessageBus liegt unter
`hexagon/core/agents/`, nicht unter `hexagon/ports/driven/`.
Konsequenz: TickLoop-Konstruktor-Kwarg ist
`agent_bus: AgentMessageBus | None` (konkrete Klasse), nicht
`agent_bus: AgentBusPort | None` (Protocol). Begruendung in
§3.

### 2.3 `AgentMessage`-Domain-Modell (frozen dataclass)

Neue frozen dataclass unter
`src/grid_gym/hexagon/core/domain/agent_message.py`:

```python
from dataclasses import dataclass, field
from collections.abc import Mapping
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class AgentMessage:
    """Standardisierte Agent-Nachricht (GG-AGENT-004).

    Pflicht-Felder per `GG-AGENT-004`-Akzeptanz:
    `simulation_time`, `sender`, `receiver`, `message_type`,
    `payload`, `sequence`.
    """

    simulation_time: int  # ms; analog DeviceTickContext.simulation_time
    sender: str           # agent_id des Senders
    receiver: str         # agent_id des Empfaengers ODER "*" fuer Broadcast
    message_type: str     # Domain-spezifisch; keine Whitelist in Welle 3
    payload: Mapping[str, object]
    sequence: int         # per-Tick-monoton, vom Bus vergeben
```

**Frozen-Vertrag** (Welle-3-Review-Folge H-1, 2026-05-21):
[`AC-DOMAIN-FROZEN`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) (ADR 0002 §A-1) wird durch
`dataclass(frozen=True, slots=True)` erfuellt — Reassign
auf Felder wirft `FrozenInstanceError`. **Kein MappingProxy-
Wrap** auf `payload`, weil das Domain-Layer-Pattern in
`ScenarioFault.payload`, `Command.payload`, `Event.payload`
ebenfalls keinen Wrap verwendet (Welle-1/M1-Stand). Konsequenz:
Mutation des referenzierten Mappings durch den Aufrufer ist
technisch moeglich; per Konvention reichen Aufrufer ein
einmal konstruiertes `dict` ein und behalten keine Referenz.
Falls Welle-4-Konkretisierung doch hermetische Frozen-
Garantie braucht, ist das ein Domain-weites Refactor (alle
vier `payload`-Felder gleichzeitig), keine
`AgentMessage`-spezifische Aenderung.

### 2.4 TickLoop-Hook (Schritt 7 per Architektur §6)

`TickLoop.tick()` erhaelt einen neuen Hook-Punkt **nach**
Schritt D (zweite Device-Iteration, ADR 0021 §2.7) und
**vor** Schritt E (`grid_model.update(...)`):

```python
# Schritt D — Zweite Iteration (GridConnection ticken).
unknown_count += self._run_device_iteration(grid_devices, ...)

# Schritt D2 — Agent-Tick (ADR 0023 §2.4, Architektur §6 Schritt 7).
if self._agent_bus is not None:
    for agent in self._agents:
        self._pending_agent_commands.extend(
            agent.tick(context, self._agent_bus)
        )

# Schritt E — Bilanz-Aggregation.
if self._grid_model is not None:
    self._grid_model.update(...)
```

**Welle-3-Pending-Buffer-Vertrag** (Welle-3-Review-Folge-2 F-1,
2026-05-21): die vom Agent-Tick emittierten Commands landen
in `self._pending_agent_commands: list[Command]`. Welle-3-
Foundation **fuehrt sie nicht aus** — Drain ist Welle-4-
Material. Read-Only-Sicht via `TickLoop.pending_agent_commands
-> tuple[Command, ...]` (Property). Welle-4-Optionen fuer den
Drain-Pfad: (a) `Scheduler.push(...)` als Command-Event-Wrap;
(b) `apply_command(...)` direkt an Devices in der naechsten
Tick-Pre-Phase; (c) eigener `apply_pending_agent_commands(...)`-
Schritt im TickLoop. ADR-Folge zu ADR 0023 §2.4 entscheidet
das. Welle 4 muss zusaetzlich eine Eviction-Strategie
spezifizieren (analog M-4 fuer den `AgentMessageBus._buffer`).

**Snapshot-Frage zum Pending-Buffer**: Welle-3-Foundation
hebt den Buffer **nicht** in `TickLoop.snapshot()` ein —
er ist ephemer und geht bei Snapshot/Restore verloren. Welle 4
entscheidet die Persistenz (additiv im Sub-Snapshot-Mapping
per ADR 0015 §2.3) — relevant nur, wenn Welle 4 entscheidet,
dass Resume-Faehigkeit fuer In-Flight-Agent-Commands
notwendig ist.

**Order-Pflicht**: Agents laufen **nach** allen Telemetry-
Emissionen und **vor** `grid_model.update(...)`. Agents
sehen damit den fertigen Welt-Zustand der aktuellen Tick
(alle TelemetryPoints in `emitted`, alle Devices haben
getickt), aber ihre Commands gehen in den Pending-Buffer und
werden im **naechsten** Tick wirksam ([`GG-AGENT-008`](../../../spec/lastenheft.md#gg-agent-008)
Commit-Reihenfolge-Invariante).

**Exception-Propagation-Vertrag** (analog ADR 0022 §2.4):
Agent-Exceptions aus `agent.tick(...)` propagieren ungewrappt
aus `TickLoop.tick()` heraus. TickLoop fuegt kein try/except
hinzu — Welle-4-Implementer entscheiden selbst, ob sie
typisierte `AgentBusError`-Subklassen werfen oder einen
Alarm-Pfad ueber Welle-5/6-Observability emittieren.

**Welle-3-Stand**: TickLoop kennt **noch keine** registrierten
Agents — der `_agents`-Tuple ist Welle-3-leer (`()`). Welle 4
wird die Agent-Registry einbringen (entweder als TickLoop-
Konstruktor-Kwarg `agents: tuple[Agent, ...] = ()` oder als
Scenario-Loader-Builder-Verantwortung — entscheidet Welle 4).

### 2.5 `agent_bus: AgentMessageBus | None`-Kwarg ohne Default-Adapter

TickLoop-Konstruktor erhaelt einen neuen keyword-only-
Parameter (analog ADR 0022 §2.5 `fault_port`):

```python
def __init__(
    self,
    *,
    run_id: str,
    ...
    fault_port: FaultPort | None = None,
    agent_bus: AgentMessageBus | None = None,
) -> None:
    ...
    self._agent_bus: AgentMessageBus | None = agent_bus
    self._agents: tuple[Agent, ...] = ()  # Welle-3-leer, Welle-4-Material
```

**`None`-Default** (kein produktiver `NullAgentMessageBus`-
Adapter):
- Welle 3 hat keine registrierten Agents; alle bestehenden
  Tests setzen `agent_bus` nicht (default `None`); der Hook
  in §2.4 skippt sauber.
- Welle-4-Test-Code, der einen AgentMessageBus mocken will,
  instanziiert die echte `AgentMessageBus()`-Klasse direkt —
  sie hat keine externen Abhaengigkeiten (kein Driven-Port).
- `*,`-Marker (keyword-only) verhindert positional-Aufrufe;
  bestehende `TickLoop(...)`-Aufrufer brechen nicht.

**Builder-Symmetrie** (analog ADR 0021 §2.4 + ADR 0022 §2.5):
der Scenario-Loader-Builder
`build_tick_loop(scenario, *, clock, random_root, ...)`
wird in M3-Welle-3 um den `agent_bus: AgentMessageBus | None
= None`-Kwarg ergaenzt und reicht den Wert unveraendert an
den TickLoop-Konstruktor durch. Default bleibt `None`;
M2-Welle-6b-Tests, die `build_tick_loop` ohne Agent-Bus
aufrufen, bleiben gruen.

### 2.6 Observability-Vorgriff-Verbot (Welle-3-Scope-Klausel)

`AgentMessageBus` und `Agent` duerfen in Welle 3 **keine**
`LogPort`/`MetricsPort`/`TracePort`-Abhaengigkeiten haben.
Konsequenzen:

- Konstruktor von `AgentMessageBus` hat **keine** Observability-
  Ports-Kwargs.
- `Agent.tick(context, bus)` bekommt **keinen** LogPort/
  MetricsPort/TracePort als Parameter.
- Welle-3-Foundation emittiert **keine** Logs/Metrics/Traces.

**Begruendung** (siehe M3-Slice-Plan §5 Risiko „Observability-
Ports-Vorgriff durch Multi-Agent/Faults"): ADR 0024
(Observability-Foundation, Welle 5) definiert das Driven-
Port-Trio. Wenn ADR 0023 schon Ports injiziert, muesste sie
einen Null-Adapter spezifizieren (Welle-5-Material). Das ist
ein Vorgriff. Stattdessen verbietet ADR 0023 §2.6 die
Injektion und verschiebt die Wiring-Entscheidung in ADR 0024.

Wenn Welle 4 (RuleBasedAgent) einen Decision-Audit-Trail
braucht, schreibt sie eine ADR-Folge zu ADR 0023 (Schaerfung-
ohne-Supersede, ADR 0011-Pattern) oder wartet auf Welle 5/6.

**Trigger-011-Inaktivitaet**: Welle 3 hat < 100 Sub-Random-
Streams (typischerweise 1-10 Agents), weit unter Aktivierungs-
Schwelle (`> 10⁶ Sub-Ports pro Lauf` oder MLRandomPort-Spike,
siehe `open/011`). Trigger 011 bleibt in `open/`. Welle-4-
Konkretisierung pruefen erneut, falls RuleBasedAgent stochastische
Decisions hat.

---

## 3. Begründung

**Sub-Protocol vs. DeviceModel-Erweiterung**: ADR 0013 §2.8
sieht das explizit vor („FaultInjectableDevice(DeviceModel),
etc., nicht als Methoden-Erweiterung des Base"). ADR 0022
hat fuer Faults den DeviceModel-erbenden Pfad gewaehlt
(`FaultInjectableDevice(DeviceModel, Protocol)`), weil Faults
auf Geraeten wirken. ADR 0023 waehlt **eigenstaendiges**
`Agent`-Protocol, weil Agents **neben** den Geraeten stehen:

- Agents haben keine `apply_command(command)`-Surface — sie
  produzieren Commands, sie konsumieren keine.
- Agents haben keine `telemetry()`-Surface — sie publizieren
  Bus-Nachrichten, keine TelemetryPoints in den Telemetry-
  Sink.
- Agents haben kein `tick(context) -> Sequence[TelemetryPoint]`
  — ihre Tick-Methode liefert `Sequence[Command]`.

DeviceModel-Erbschaft wuerde Agents als Geraete typisieren,
was den `_devices: tuple[DeviceModel, ...]`-Tuple im TickLoop
verunreinigt (Devices und Agents wuerden in derselben
Iteration laufen). Konsistenz-Argument analog ADR 0022 §3:
Agent-vs-Device-Trennung bleibt klar.

**AgentBus als Core-Klasse vs. Driven-Port** (zentrale
Pattern-Drift-Entscheidung gegen ADR 0022):

Drei Varianten waren denkbar:

1. **AgentBus als Driven-Port** (Welle-1-Pattern: FaultPort).
   *Abgelehnt*: vier Gegenargumente.
   - **Architektur §14** schreibt explizit „eigenes Kernmodul
     `hexagon/core/agents`" + „eigener … AgentMessageBus" —
     ein Driven-Port unter `hexagon/ports/driven/` waere
     Architektur-Drift.
   - **Architektur §4.2** Driven-Ports-Tabelle listet
     **keinen** AgentPort/AgentBusPort. Driving-Ports
     listet einen abstrakten `AgentPort` als Schritt 7 im
     Tick-Loop-Diagramm, aber das ist die `Agent`-Schnittstelle
     selbst (Welle-3-`Agent`-Protocol), nicht der Bus.
   - **State-/Boundary-Argument** (Welle-3-Review-Folge M-2,
     2026-05-21): AgentBus haelt produktiven State (Message-
     Buffer, Sequence-Counter, Snapshot-Surface). Driven-Ports
     sind per Konvention die Boundary zu einem externen
     Adapter, nicht produktiver State-Trager — siehe
     `MersenneTwisterRandomPort` (ADR 0007 §5.2), der zwar
     statefull ist, aber als Adapter unter
     `adapters/driven/random_mt/` eine externe PRNG-Bibliothek
     kapselt. AgentBus hat **keine externe Boundary** (keine
     Bibliothek, kein Protokoll, kein Service); er ist reines
     Domain-Orchestrierungs-Modell. `AC-PORTS-NO-OUT` regelt
     Import-Direction (`hexagon/ports/` darf nicht `core/`
     importieren) und ist hier nicht das maßgebliche
     Argument; entscheidend ist die fehlende Adapter-Boundary.
   - **Test-Isolierungs-Argument**: [`GG-AGENT-002`](../../../spec/lastenheft.md#gg-agent-002) verlangt
     „isoliert testbar". Test-Isolierung wird ueber das
     `Agent`-Sub-Protocol erreicht: Test-Code instanziiert
     einen Mock-Agent direkt und ruft `agent.tick(context,
     bus)` an. Port-Mocking braucht es nicht.

2. **AgentBus als Per-Agent-Hook im TickLoop** — TickLoop
   iteriert `agents`-Tuple, ruft `agent.tick(context, bus)`,
   bus-Buffer ist lokale Variable im TickLoop.
   *Abgelehnt*: bus muss snapshot-/replay-faehig sein
   ([`GG-AGENT-003`](../../../spec/lastenheft.md#gg-agent-003) + [`GG-AGENT-006`](../../../spec/lastenheft.md#gg-agent-006)); lokale Variable ist nicht
   snapshot-faehig. Bus muss eigene Klasse sein.

3. **AgentBus als Core-Klasse** (gewaehlt) — eigene Klasse
   unter `hexagon/core/agents/bus.py`, vom TickLoop ueber
   Konstruktor-Kwarg injiziert. *Vorteil*: respektiert
   Architektur §14, traegt State sauber, ist snapshot-faehig,
   bleibt test-tauschbar (direkte Instanziierung im Test).

**TickLoop-Hook-Position (Schritt 7 vs. alternative
Positionen)**: drei Varianten waren denkbar:

1. **Vor erster Device-Iteration** (analog Faults, Schritt
   A2). *Abgelehnt*: Agents wuerden auf den Welt-Zustand der
   *vorherigen* Tick reagieren — Faults und LoadEvents der
   aktuellen Tick haetten noch nicht gewirkt. Architektur §6
   Schritt 7 widerspricht dem.

2. **Zwischen erster und zweiter Iteration** (Schritt C im
   aktuellen Code, vor GridConnection-Auto-Schluss).
   *Abgelehnt*: Agents wuerden vor dem GridConnection-Auto-
   Schluss laufen — der Welt-Zustand waere unvollstaendig
   (GridConnection.tick() hat noch nicht gelaufen). Analog
   Argument 1.

3. **Nach zweiter Iteration, vor grid_model.update**
   (gewaehlt, Architektur §6 Schritt 7). Agents sehen den
   fertigen Welt-Zustand (alle Devices haben getickt, alle
   Telemetry ist emittiert, GridConnection-Auto-Schluss ist
   gelaufen) und produzieren Commands fuer die naechste Tick.
   `grid_model.update(...)` ist Bilanz-Aggregation und sollte
   nicht durch Agent-Commands beeinflusst werden — also vor
   Bilanz, aber nach allen Telemetry-/State-Emissionen.

**In-Tick-Wirksamkeit verboten ([`GG-AGENT-008`](../../../spec/lastenheft.md#gg-agent-008))**: Agents
schreiben Commands in den Scheduler, der sie im **naechsten**
Tick poppt. Re-Iteration der Devices nach Agent-Commands
(„in-Tick-Wirksamkeit") wuerde die Commit-Reihenfolge
veraendern ([`GG-AGENT-008`](../../../spec/lastenheft.md#gg-agent-008) Akzeptanz: „Asynchrone Verarbeitung
darf die Commit-Reihenfolge eines Ticks nicht veraendern").
Welle 4 oder spaeter kann ADR-Folge schreiben, wenn ein Agent-
Typ in-Tick-Wirksamkeit braucht (z. B. Notfall-Trip-Agent
fuer Battery-Cell-Failure-Detektion).

**Observability-Vorgriff-Verbot**: ADR 0023 §2.6 spiegelt das
M3-Plan §5 Risiko. Alternativ haette ADR 0023 LogPort-
Injektion mit Null-Adapter spezifizieren koennen (Welle-3-
Vorgriff auf Welle 5/6). *Abgelehnt*: zwingt Welle 5 auf
einen bestimmten Null-Adapter-Vertrag, der vielleicht nicht
passt. Sauberer ist die strikte Trennung (Welle-3-Code ist
Observability-frei), und Welle 5/6 entscheidet das Wiring.

**Snapshot-Vertrag in Welle 3**: Welle-3-Default-TickLoop
hat `agent_bus=None`, also kein Sub-Snapshot. Test-Code
mit `agent_bus=<echtes Bus>` muss den Snapshot-Roundtrip
selbst pruefen — Welle 3 stellt das Tooling (`AgentMessageBus.
snapshot()` + `from_snapshot(...)`), aber bindet es noch
nicht in `TickLoop.snapshot()` ein. Welle 4 wird einen Sub-
Snapshot-Slot `agent_bus` (Single-Instance) und
`agents.<agent_type>.<agent_id>` (Multi-Instance) einfuehren,
beides additiv per ADR 0015 §2.3 ohne v2→v3-Bump.

---

## 4. Reichweite

**In Scope (Welle 3):**

- `Agent`-Protocol-Definition unter `hexagon/core/agents/`.
- `AgentMessageBus`-Core-Klasse unter `hexagon/core/agents/`.
- `AgentMessage`-Domain-Modell unter `hexagon/core/domain/`.
- `AgentBusError`-Basis in `core/errors.py`.
- TickLoop-Konstruktor-Kwarg + Hook-Aufruf-Punkt (Welle-3-
  Tuple ist leer; Welle 4 fuellt es).
- `build_tick_loop`-Builder-Symmetrie.
- Tests fuer Protocol-Adherence, AgentMessageBus-Determinismus,
  AgentMessage-Frozen-Vertrag, TickLoop-Hook-Order.
- `CRITICAL_COV_TARGETS`-Default-Erweiterung um
  `core/agents`. **Welle-3-Review-Folge M-1 (2026-05-21)**:
  `core/domain/agent_message.py` ist NICHT als separater
  CRITICAL_COV_TARGETS-Eintrag noetig — der Dockerfile-Stage
  `coverage-gate-critical` prueft `[ ! -d "${target}" ]`
  (Directory-Pflicht; Files sind nicht zulaessig). Die
  Coverage-Messung erfasst `agent_message.py` trotzdem
  vollstaendig, weil `core/agents/bus.py` das Modul importiert
  und damit alle Code-Pfade in der `--cov=core/agents`-Run-
  Reichweite landen.

**Out of Scope (Welle 4):**

- Konkrete `Agent`-Implementer (`RuleBasedAgent` o. ae.).
- Agent-Registry im TickLoop (`agents: tuple[Agent, ...]`).
- Decision-Logik (Welt-Zustand-Konsum → Command-Produktion).
- `agents`-Top-Level-Block im Scenario-Schema +
  `_assert_agent_list`-Validator (analog ADR 0022 §2.3 fuer
  Faults).
- Welle-4-Agent-Sub-Snapshot-Slot (`agents.<type>.<id>`).
- Konkurrierende Strategien (`GG-AGENT-005`) — Priorisierungs-
  Mechanismus.
- Property-Tests fuer Agent-Determinismus (`GG-AGENT-003`).

**Out of Scope (M3-Welle-7+ oder Welle-4-Folge):**

- Deadlines (`GG-AGENT-007`) — Welle 4 oder Welle-4-Folge.
- Async-Kommunikation (`GG-AGENT-008`) — eigene ADR-Folge zu
  ADR 0007 `AsyncRandomPort` (siehe ADR 0007 §6).
- LogPort/MetricsPort-Injektion in Bus/Agent — Welle 5/6
  (ADR 0024).
- Sub-Seed-Wortbreite-Erhoehung (Trigger 011) — bleibt in
  `open/`, Aktivierungs-Kriterium nicht erreicht.
- Snapshot-Schema-Bump v2 → v3 — additive Sub-Snapshots
  reichen; v3-Bump bleibt M6.
- RL-Adapter (`GG-FUTURE-001/002`).
- In-Tick-Wirksamkeit fuer Agent-Commands — eigene ADR-Folge,
  falls noetig.

---

## 5. Operative Artefakte

| Pfad                                                                | Aktion |
| ------------------------------------------------------------------- | ------ |
| `src/grid_gym/hexagon/core/agents/_protocol.py`                     | NEU (`Agent`-Protocol) |
| `src/grid_gym/hexagon/core/agents/bus.py`                           | NEU (`AgentMessageBus`) |
| `src/grid_gym/hexagon/core/agents/__init__.py`                      | EDIT (Re-exports) |
| `src/grid_gym/hexagon/core/domain/agent_message.py`                 | NEU (`AgentMessage`) |
| `src/grid_gym/hexagon/core/errors.py`                               | EDIT (`AgentBusError`-Basis) |
| `src/grid_gym/hexagon/core/simulation/tick_loop.py`                 | EDIT (Konstruktor-Kwarg + Hook) |
| `src/grid_gym/hexagon/core/scenario/loader.py`                      | EDIT (`build_tick_loop`-Symmetrie) |
| `tests/unit/hexagon/core/agents/__init__.py`                        | NEU |
| `tests/unit/hexagon/core/agents/test_protocol.py`                   | NEU |
| `tests/unit/hexagon/core/agents/test_bus.py`                        | NEU |
| `tests/unit/hexagon/core/domain/test_agent_message.py`              | NEU |
| `tests/unit/hexagon/core/simulation/test_tick_loop_welle_3_agent.py` | NEU |
| `Dockerfile`                                                        | EDIT (`CRITICAL_COV_TARGETS` + `core/agents`; siehe §4 In-Scope-Note zur `agent_message.py`-Erfassung) |

ADR-Cross-Refs (read-only fuer Welle 3):
- ADR 0013 §2.8 zitiert in `Agent`-Docstring.
- Architektur §14 zitiert in `AgentMessageBus`-Docstring.
- Architektur §6 Schritt 7 zitiert im TickLoop-Hook-Kommentar.
- ADR 0021 §2.4 + ADR 0022 §2.5 zitiert in Builder-Symmetrie-
  Notiz.
- Diese ADR wird mit M3-Welle-7-Closure auf `Accepted` gehoben
  (Pattern aus ADR 0017/0018/0021/0022).

---

## 6. Konsequenzen

**Positive Konsequenzen:**

- `DeviceModel`-Surface bleibt unveraendert; Agents stehen
  neben den Geraeten, nicht auf ihnen. M2-Tests bleiben gruen.
- TickLoop hat einen klar definierten Hook-Punkt analog Welle-
  1-Fault-Hook; Welle 4-Implementer kann sich einklinken.
- AgentMessageBus ist Core-Klasse mit Snapshot-Surface — voll
  snapshot-/replay-faehig ([`GG-AGENT-003`](../../../spec/lastenheft.md#gg-agent-003) + [`GG-AGENT-006`](../../../spec/lastenheft.md#gg-agent-006)
  Akzeptanz-Pfad fuer Welle 4 ist offen).
- Welle 4 hat eine klare Schnittstelle, an die
  `RuleBasedAgent` + Welle-4-Registry einsteigen koennen.
- Trigger 011 bleibt in `open/`, kein vorzeitiges ADR-Schreiben.

**Verbindliche Konsequenzen fuer Welle 4:**

- Welle-4-Agent-Implementer mussen `Agent`-Protocol-Surface
  vollstaendig erfuellen (`agent_id`, `set_run_id`, `tick`,
  `snapshot`/`from_snapshot`).
- Welle 4 entscheidet, wo die Agent-Registry sitzt
  (TickLoop-Kwarg vs. Scenario-Loader-Verantwortung) — beide
  Pfade sind in Welle-3-Foundation offen gehalten.
- Welle 4 schreibt eine eigene ADR-Folge fuer:
  - `agents`-Top-Level-Block im Scenario-Schema (analog
    Welle-1-`_assert_fault_list`).
  - Agent-Sub-Snapshot-Slot in `TickLoop.snapshot()` (analog
    Welle-6a-Devices-Sub-Snapshot).
  - Priorisierung konkurrierender Agents ([`GG-AGENT-005`](../../../spec/lastenheft.md#gg-agent-005)).

**Restpost — Snapshot-Schema:**

- ADR 0015 bleibt v2; Welle 3 fuegt keinen Sub-Snapshot-Key
  zur Default-`TickLoop.snapshot()` hinzu.
- AgentMessageBus haelt selbst eine `snapshot()`-Surface, aber
  sie wird in Welle 3 nicht in das Top-Level-Snapshot
  eingehaengt. Welle 4 wird das additiv tun.
- Snapshot-Bump v2 → v3 bleibt M6-Material (`GG-PERSIST-*`-
  Slice).

**Pflege-Gleichheit:**

- `_DEVICE_FACTORIES` (Scenario-Loader,
  `src/grid_gym/hexagon/core/scenario/loader.py:59-65`) ist
  von Welle 3 **nicht** betroffen — Agent-Faktoren sind
  Welle-4-Material.
- `_DEVICE_TYPE_BY_CLASS_NAME` (TickLoop) bleibt unveraendert.
- `_BILANZ_SOURCE_BUCKETS` (TickLoop) bleibt unveraendert —
  Agents emittieren keine TelemetryPoints; Bilanz-Aggregation
  ist nicht beruehrt.

---

## 7. Nicht Gegenstand

**Observability-Ports** (`GG-OTEL-001..004`,
`GG-AR-PORT-DRN-008`) — eigene ADR 0024 in M3-Welle-5+.
`LogPort`/`MetricsPort`/`TracePort` sind orthogonal zu
AgentMessageBus und kommen spaeter. ADR 0023 §2.6 verbietet
explizit den Vorgriff.

**RL-Adapter** (`GG-FUTURE-001/002`) — eigener Slice nach
M3-Welle-7. Welle-3-`Agent`-Protocol ist RL-faehig (Surface
unterscheidet sich nicht zwischen Rule-Based und RL), aber
der Trainings-Loop bleibt extern.

**Async-Kommunikation** (`GG-AGENT-008`) — Welle-3-Foundation
ist synchron. Async-Variante kommt mit ADR-Folge zu ADR 0007
`AsyncRandomPort` (siehe ADR 0007 §6), wenn ein konkreter
Slice das braucht. [`GG-AGENT-008`](../../../spec/lastenheft.md#gg-agent-008) Akzeptanz ist auch synchron
erfuellbar — „Async-Verarbeitung **darf** die Commit-
Reihenfolge nicht veraendern" ist ein Constraint, kein
Implementation-Pflicht-Pfad.

**Konkurrierende Strategien** (`GG-AGENT-005`) — Welle 4
oder Welle-4-Folge. Welle-3-Foundation hat kein
Priorisierungs-Konstrukt; Welle 4 wird es zusammen mit der
Agent-Registry einbringen.

**Deadlines** (`GG-AGENT-007`) — Welle 4 oder Welle-4-Folge.
Welle-3-`Agent.tick(context, bus)` hat kein Deadline-Argument;
Welle 4 entscheidet, ob das ueber `DeviceTickContext`-
Erweiterung (Vorgriff auf TickLoop-Kontrakt) oder ueber ein
separates `AgentContext` laeuft.

**In-Tick-Wirksamkeit** — Welle-3-`Agent.tick(...)` produziert
Commands fuer die naechste Tick. In-Tick-Wirksamkeit (Devices
re-iterieren nach Agent-Commands) waere eine eigene ADR-Folge,
falls Welle 4 oder ein spaeterer Slice das braucht.

**Snapshot-Schema-Bump v2 → v3** — additive Sub-Snapshots
reichen fuer Welle 4 (ADR 0015 §2.3). v3-Bump bleibt M6.

**Trigger 011 (Sub-Seed-Wortbreite)** — bleibt in `open/`.
Welle-3-Skala (< 100 Agents) erreicht Aktivierungs-Kriterium
(`> 10⁶ Sub-Ports`) nicht. Welle-4-Konkretisierung pruefen
erneut.
