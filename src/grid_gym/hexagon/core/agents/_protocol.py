"""`Agent`-Protocol (M3 Welle 3, ADR 0023 §2.1).

Agent-Protocol-Vertrag fuer Multi-Agent-Steuerung. Im Gegensatz
zu `FaultInjectableDevice` (ADR 0022 §2.1) ist `Agent` **kein**
Sub-Protocol von `DeviceModel` — Agents stehen neben den
Geraeten, nicht auf ihnen.

Architektur §14: Agenten sind ein eigenes Kernmodul, das ueber
einen eigenen `AgentMessageBus` deterministisch kommuniziert.
ADR 0013 §2.8-konform: keine Erweiterung der `DeviceModel`-
Surface; Welle-4-Implementer (`RuleBasedAgent` etc.) erfuellen
direkt dieses Protocol.

**Welle-3-Stand**: dieses Modul liefert nur den Protocol-
Vertrag. Konkrete Implementer kommen in Welle 4.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Protocol, Self, runtime_checkable

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.ports.driven.random import RandomPort

if TYPE_CHECKING:
    # Forward-Reference vermeidet zyklischen Import: `_protocol`
    # wird vom `bus`-Modul (indirekt) gelesen, gleichzeitig braucht
    # `tick(...)` den `AgentMessageBus`-Typ. TYPE_CHECKING-Block
    # macht das nur fuer Mypy sichtbar; zur Laufzeit ist der
    # Forward-Ref-String ausreichend.
    from grid_gym.hexagon.core.agents.bus import AgentMessageBus


@runtime_checkable
class Agent(Protocol):
    """Agent-Protocol fuer Multi-Agent-Steuerung (ADR 0023 §2.1).

    Pflicht-Surface:

    - `agent_id`-Property: stabile Agent-Identitaet.
    - `set_run_id(run_id)`: Lifecycle-Hook (analog
      `DeviceModel.set_run_id`, ADR 0013 §2.6).
    - `tick(context, bus) -> Sequence[Command]`: Agent-Tick;
      konsumiert Welt-Zustand, produziert Commands.
    - `snapshot()` + `from_snapshot(state)`: Snapshot-/Replay-
      Faehigkeit (`GG-AGENT-003` + `GG-AGENT-006`).

    `@runtime_checkable` erlaubt `isinstance(obj, Agent)` —
    die Pruefung erfasst das Vorhandensein der Methoden-Surface
    (nicht Signaturen). Welle-4-Adapter nutzen das fuer „ist
    dieses Objekt ein Agent?"-Entscheidungen.

    **Welle-3-Stand**: nur Vertrag; konkrete Implementer
    (`RuleBasedAgent` o. ae.) in Welle 4.
    """

    @property
    def agent_id(self) -> str:
        """Stabile Agent-Identitaet (analog `DeviceModel.device_id`).

        Pflicht-Pflicht: pro Run eindeutig, Snapshot-Roundtrip-
        invariant. Primaere Sortier-Schluessel-Komponente fuer
        Bus-Nachrichten (`AgentMessage.sender`/`.receiver`).
        """
        ...

    def set_run_id(self, run_id: str) -> None:
        """Wird vom TickLoop einmal nach Konstruktion aufgerufen.

        Analog `DeviceModel.set_run_id` (ADR 0013 §2.6 Lifecycle-
        Pre-init-Vertrag): Agent darf `run_id` fuer Logging/
        Tagging in den Bus-Nachrichten verwenden. Idempotenz-
        Vertrag ist Welle-4-Decision; Welle-3-Protocol verlangt
        nur die Methode.
        """
        ...

    def tick(
        self,
        context: DeviceTickContext,
        bus: "AgentMessageBus",
    ) -> Sequence[Command]:
        """Agent-Tick: liefert Commands fuer die naechste Tick.

        TickLoop ruft pro Tick fuer jeden registrierten Agent
        einmal `agent.tick(context, bus)` zwischen Schritt D
        (zweite Device-Iteration) und Schritt E
        (`grid_model.update(...)`). Siehe ADR 0023 §2.4 und
        Architektur §6 Schritt 7.

        **Welt-Zustand-Konsum**: `context.simulation_time`/
        `context.tick`/`context.tick_ms` analog `DeviceModel.tick`;
        Bus-Nachrichten ueber `bus.drain_for(agent_id)`. Welle 4
        wird einen optionalen `TelemetryQueryPort` (oder
        aequivalent) hinzufuegen, falls Decision-Logik
        Live-Telemetry braucht — Welle-3-Protocol hat das nicht.

        **Command-Produktion**: returns `Sequence[Command]`.
        Commands werden im **naechsten** Tick wirksam (GG-AGENT-008
        Commit-Reihenfolge-Invariante). Welle 4 entscheidet, wo
        die Commands gepuffert werden — Welle-3-Foundation
        verdrahtet die Anwendung nicht.

        Determinismus-Vertrag (`GG-AGENT-003`): gleicher Seed +
        gleicher Eingabeverlauf (Bus-Nachrichten + context) →
        identische Command-Sequenz.
        """
        ...

    def snapshot(self) -> Mapping[str, object]:
        """Persistiert lokalen Agent-Zustand (`GG-AGENT-006`).

        Roundtrip-Vertrag (analog ADR 0013 §2.4): `from_snapshot(
        snapshot())` muss eine ==-identische Agent-Instanz liefern
        (modulo `run_id`, der ueber `set_run_id(...)` nach
        Restore neu gesetzt wird).

        Snapshot-Format: `Mapping[str, object]` mit Pflicht-Key
        `"version": int` (ADR 0015 §2.3 Sub-Snapshot-Konvention).
        Konkrete Schema-Felder pro Agent-Typ sind Welle-4-Material.
        """
        ...

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        """Rekonstruiert den Agent aus einem `snapshot()`-Mapping
        (Welle-3-Review-Folge-2 F-2, 2026-05-21).

        Vertrag analog ADR 0013 §2.4 (DeviceModel-Pattern):
        `from_snapshot(snapshot()) == agent` ist byte-stabil.
        Mismatch zwischen `state["version"]` und der erwarteten
        Version wirft typisiert `VersionError(subsystem=
        "<agent-type>", expected=N, found=...)` aus dem
        Welle-0a-Generic-Codec
        (`hexagon/core/serialization/snapshot_codec.py`).
        Strukturelle Mismatches werfen `MissingKeysError`/
        `WrongTypeError` analog.

        `run_id` wird **nicht** aus dem Snapshot rekonstruiert —
        Aufrufer muss nach `from_snapshot(...)` explizit
        `set_run_id(run_id)` aufrufen (analog DeviceModel-
        Resume-Pattern, ADR 0013 §2.6 Lifecycle-Pre-init-Vertrag).

        Konkrete Implementationen kommen mit Welle 4
        (`RuleBasedAgent` etc.). Welle-3-Test-Pattern: `NullAgent`-
        Stub liefert die Baseline-Implementation.
        """
        ...


@runtime_checkable
class _RandomAttachableAgent(Agent, Protocol):
    """Optionales Sub-Protocol fuer Agents mit eigenem Per-Agent-
    Sub-Random-Stream (M3 Welle 4a, ADR 0026 §2.3).

    `_attach_agents()` am TickLoop prueft via
    `isinstance(agent, _RandomAttachableAgent)`, ob ein Agent
    einen Sub-Random-Stream braucht. Agents ohne Stochastik
    implementieren das Sub-Protocol nicht und bekommen damit
    weder einen Sub-Port noch einen No-op-Hook aufgezwungen.

    `@runtime_checkable` ist Pflicht, sonst wirft Python beim
    `isinstance(...)`-Check einen `TypeError` (vgl. R-3 in
    welle-4a.md §7).

    Sub-Port-Namens-Konvention (ADR 0026 §2.3 + Welle-3-Review-
    Folge M-3): `RandomPort.sub_port(f"agent-{agent_id}")`.
    Damit ist die Stream-Ableitung pro Agent deterministisch
    und unabhaengig von anderen Agents oder Devices.
    """

    def attach_random(self, random: RandomPort) -> None:
        """Wird vom TickLoop einmal aufgerufen, mit dem
        Per-Agent-Sub-Random-Stream
        (`random_root.sub_port(f"agent-{agent_id}")`).

        Idempotenz-Vertrag: Welle-4a-Foundation ruft den Hook
        genau einmal in `_attach_agents()` (analog
        `SmartMeterDevice.attach_sources`, ADR 0018 §2.4).
        Welle-4-Implementer entscheiden, ob sie Mehrfach-Aufrufe
        idempotent halten — Welle 4a-Protocol verlangt nur den
        Einmal-Aufruf-Vertrag.
        """
        ...


@runtime_checkable
class AgentPlugin(Protocol):
    """Optionales Plugin-Sub-Protocol fuer `RuleBasedAgent`-
    Decision-Hooks (M3 Welle 4b, ADR 0027 §2.3).

    Welle-4b liefert die Hook-Surface + Factory-Map, aber **keine**
    konkreten Plugin-Implementer. Welle 4c+ kann z. B.
    `LearnedPolicyPlugin` / `MPCControllerPlugin` registrieren.

    Plugin-Restore-Vertrag (ADR 0027 §2.3, Welle-4b-Review-Folge
    F-2): `from_snapshot(state)` rekonstruiert den Plugin-Zustand
    **ausschliesslich** aus dem Plugin-Snapshot — keine Scenario-
    `plugin_params`-Abhaengigkeit. Scenario-Params fliessen nur
    in den Fresh-Start-Pfad ein (Konstruktor/Factory). Drift-
    Detection zwischen Scenario und Snapshot ist Aufrufer-Pflicht.
    """

    def decide(
        self,
        context: DeviceTickContext,
        bus: "AgentMessageBus",
        params: Mapping[str, object],
    ) -> Sequence[Command]:
        """Plugin-Decision-Pfad analog `Agent.tick(...)`.

        Welle-4b-Vertrag: `params` ist das Scenario-`plugin_params`-
        Mapping (read-only). Determinismus-Vertrag (`GG-AGENT-003`)
        gilt: gleicher Seed + gleicher Eingabeverlauf → identische
        Command-Sequenz.
        """
        ...

    def snapshot(self) -> Mapping[str, object]:
        """Persistiert Plugin-lokalen Zustand.

        Format: `Mapping[str, object]` mit Pflicht-Key
        `"version": int` (ADR 0015 §2.3 Sub-Snapshot-Konvention).
        """
        ...

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> "AgentPlugin":
        """Rekonstruiert das Plugin aus seinem Snapshot.

        Plugin-Snapshot ist Single Source of Truth (ADR 0027 §2.3).
        Scenario-Params werden hier nicht erwartet.
        """
        ...
