"""`AgentMessageBus` Core-Klasse (M3 Welle 3, ADR 0023 §2.2).

Deterministisch sortierter Message-Bus fuer Multi-Agent-
Kommunikation (Architektur §14, `GG-AGENT-004`/`008`).

**Architektur-Entscheidung** (ADR 0023 §3): Der Bus ist eine
**Core-Klasse**, kein Driven-Port. Begruendung:

1. Architektur §14 schreibt explizit „eigenes Kernmodul
   `hexagon/core/agents`" + „eigener … `AgentMessageBus`".
2. Architektur §4.2 Driven-Ports-Tabelle listet **keinen**
   AgentBus-Port.
3. AgentBus haelt produktiven State (Buffer, Sequence-Counter,
   Snapshot-Surface) **ohne** externe Adapter-Boundary.
   Driven-Ports sind per Konvention Adapter-Boundary
   (`MersenneTwisterRandomPort` ist Port + stateful + externe
   PRNG-Library); AgentBus kapselt keine externe Library,
   kein Protokoll, keinen Service — er ist reines Domain-
   Orchestrierungs-Modell (Welle-3-Review-Folge M-2,
   2026-05-21).
4. Test-Isolierung (`GG-AGENT-002`) wird ueber das `Agent`-
   Sub-Protocol erreicht (direkte Instanziierung im Test);
   Port-Mocking ist nicht noetig.

Sortier-Vertrag fuer `drain_for(receiver)`: `(simulation_time,
sender, sequence)` — letztes Tie-Breaking-Glied ist die
per-Bus-monoton aufsteigende `sequence`-Nummer (analog
Welle-1-Scheduler-Tie-Breaking).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Final, cast, override

from grid_gym.hexagon.core.domain.agent_message import AgentMessage
from grid_gym.hexagon.core.errors import (
    AgentBusInvalidReceiverError,
    AgentBusInvalidSequenceError,
    AgentBusSnapshotMissingKeysError,
    AgentBusSnapshotNotAMappingError,
    AgentBusSnapshotVersionError,
    AgentBusSnapshotWrongTypeError,
)

SNAPSHOT_VERSION: Final[int] = 1
"""Bus-Snapshot-Schema-Version (ADR 0023 §2.2 + ADR 0015 §2.3).

Welle 3 fuehrt v1 ein; Welle-4-Erweiterungen (z. B.
destruktive Drain-Semantik mit `consumed_sequences`-Set)
wuerden v1 → v2 bumpen.
"""


class _AgentMessageBusUnhashableError(TypeError):
    """`AgentMessageBus` ist mutable und damit nicht hashable.

    Python-Konvention: `__hash__` wirft `TypeError` fuer unhashable
    Types. Modulokale Sub-Klasse mit `__init__`-Message (Slice 027
    Paket B TRY003-Drop).
    """

    def __init__(self) -> None:
        super().__init__("AgentMessageBus is mutable and not hashable")


class AgentMessageBus:
    """Deterministisch sortierter Message-Bus (ADR 0023 §2.2).

    Welle-3-Foundation:

    - Buffer ist eine `list[AgentMessage]` in Einfuege-
      Reihenfolge.
    - `publish(message)` haengt an; Sequence-Counter wird
      vom Bus vergeben, wenn `message.sequence == -1`
      (Sentinel fuer „bitte vergeben").
    - `drain_for(receiver)` liefert eine deterministisch
      sortierte Liste; **nicht-destruktiv** (Welle-4-
      Material: optionale destruktive `consume_for`-
      Variante).
    - `snapshot()`/`from_snapshot(state)` sind ADR 0015 §2.3-
      Sub-Snapshot-kompatibel.
    """

    def __init__(self) -> None:
        self._buffer: list[AgentMessage] = []
        self._next_sequence: int = 0

    @property
    def next_sequence(self) -> int:
        """Vorschau auf die naechste Sequence-Nummer (Test-Accessor).

        Welle-4-Code kann via `publish(...)` ohne expliziten
        Sequence-Counter publizieren (Sentinel `sequence=-1`);
        diese Property pinnt den Vergabe-Zaehler fuer Tests.
        """
        return self._next_sequence

    def publish(self, message: AgentMessage) -> None:
        """Append an den Buffer.

        **Sequence-Vergabe**: wenn `message.sequence == -1`,
        vergibt der Bus die naechste freie Nummer. Wenn der
        Aufrufer explizit eine `sequence`-Nummer setzt
        (Test-Code-Pfad), wird sie respektiert; der Bus
        aktualisiert `_next_sequence` aber NUR, wenn die
        explizite Nummer hoeher ist als der aktuelle Zaehler.
        Damit bleibt der Counter monoton, auch wenn Tests
        Out-of-Order-Sequenzen einspielen.

        Welle-4-Material: Idempotenz-Vertrag fuer Duplicate-
        Sender + Whitelist fuer `receiver`-Patterns.

        Welle-3-Review-Folge L-2 (2026-05-21): `sequence < -1`
        wirft `AgentBusInvalidSequenceError` (sonst wuerde der
        Wert in der Sortier-Logik vor den echten Sequenzen
        0, 1, 2, ... landen und den Determinismus-Vertrag
        verzerren).
        """
        if message.sequence < -1:
            raise AgentBusInvalidSequenceError(message.sequence)
        if message.sequence == -1:
            normalized = replace(message, sequence=self._next_sequence)
            self._next_sequence += 1
        else:
            normalized = message
            if message.sequence >= self._next_sequence:
                self._next_sequence = message.sequence + 1
        self._buffer.append(normalized)

    def drain_for(self, receiver: str) -> Sequence[AgentMessage]:
        """Liefert alle Nachrichten mit
        `message.receiver in (receiver, "*")`, sortiert nach
        `(simulation_time, sender, sequence)`.

        **Drain-Semantik (Welle 3)**: nicht-destruktiv —
        Nachrichten bleiben im Buffer. Welle 4 kann eine
        destruktive `consume_for(receiver)`-Variante einfuehren,
        wenn ein Agent-Typ explizit „nur einmal lesen"-
        Semantik braucht.

        `"*"` ist Broadcast-Adressierung am **Publish-Pfad**
        (ADR 0023 §2.3): Nachrichten mit
        `message.receiver = "*"` werden an jeden
        `drain_for(...)`-Aufrufer ausgeliefert. Welle-3-Review-
        Folge L-3 (2026-05-21): `drain_for("*")` selbst ist
        verboten — der Aufruf wuerde nur Broadcasts liefern
        (nicht alles), was semantisch fragwuerdig ist. Wir
        werfen `AgentBusInvalidReceiverError` typisiert ab.
        """
        if receiver == "*":
            raise AgentBusInvalidReceiverError(receiver)
        matches = [message for message in self._buffer if message.receiver in (receiver, "*")]
        # Welle-3-Sortier-Vertrag (ADR 0023 §2.2): primaer
        # simulation_time aufsteigend, dann sender lexikographisch,
        # dann sequence aufsteigend. Damit ist die Iteration
        # deterministisch unabhaengig von Publish-Reihenfolge.
        matches.sort(
            key=lambda m: (m.simulation_time, m.sender, m.sequence),
        )
        return tuple(matches)

    def consume_for(self, receiver: str) -> Sequence[AgentMessage]:
        """Destruktive Direct-Inbox-Drain-Variante (M3 Welle 4a,
        ADR 0026 §2.4).

        Liefert alle direkt an `receiver` adressierten
        Nachrichten (`message.receiver == receiver`) in
        derselben Sortierung wie `drain_for(receiver)` UND
        entfernt nur diese aus dem Buffer. Broadcasts
        (`message.receiver == "*"`) bleiben bewusst im Buffer
        und werden weiter nicht-destruktiv ueber
        `drain_for(receiver)` ausgeliefert.

        `receiver == "*"` ist analog zu `drain_for("*")`
        verboten und wirft `AgentBusInvalidReceiverError`
        (Welle-3-Review-Folge L-3-Vertrag).

        Welle-4a-Eviction-Spec (Welle-3-Review-Folge M-4):
        registry-aware Broadcast-Fan-out/Watermark bleibt
        Welle 4b oder spaetere Folge — ein destruktiver
        Broadcast-Konsum beim ersten `consume_for(...)`-
        Aufruf wuerde alle nachfolgenden Receiver
        abschneiden.

        Snapshot-Schema-Erweiterung: kein Bump v1 → v2 noetig,
        solange kein `consumed_sequences`/Watermark-State
        persistiert wird; der Buffer wird nach Konsumption
        kleiner, aber das Schema-Format bleibt unveraendert.
        """
        if receiver == "*":
            raise AgentBusInvalidReceiverError(receiver)
        # Direct-Inbox-Filter: NUR `message.receiver == receiver`,
        # Broadcasts (`receiver == "*"`) bleiben unangetastet.
        matches: list[AgentMessage] = []
        retained: list[AgentMessage] = []
        for message in self._buffer:
            if message.receiver == receiver:
                matches.append(message)
            else:
                retained.append(message)
        self._buffer = retained
        matches.sort(
            key=lambda m: (m.simulation_time, m.sender, m.sequence),
        )
        return tuple(matches)

    def snapshot(self) -> Mapping[str, object]:
        """Persistiert Buffer + Sequence-Counter als
        canonical_json-faehiges Mapping.

        Welle-3-Schema (`version=1`):

        ```json
        {
          "version": 1,
          "next_sequence": <int>,
          "messages": [
            {
              "simulation_time": <int>,
              "sender": <str>,
              "receiver": <str>,
              "message_type": <str>,
              "payload": <dict>,
              "sequence": <int>
            },
            ...
          ]
        }
        ```

        Wird in Welle-3-Default-`TickLoop.snapshot()` NICHT
        eingehaengt — Welle-3-Default ist `agent_bus=None`.
        Welle 4 fuegt einen Sub-Snapshot-Slot `agent_bus`
        additiv per ADR 0015 §2.3 ein.
        """
        return {
            "version": SNAPSHOT_VERSION,
            "next_sequence": self._next_sequence,
            "messages": tuple(
                {
                    "simulation_time": m.simulation_time,
                    "sender": m.sender,
                    "receiver": m.receiver,
                    "message_type": m.message_type,
                    "payload": dict(m.payload),
                    "sequence": m.sequence,
                }
                for m in self._buffer
            ),
        }

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> "AgentMessageBus":
        """Rekonstruiert einen Bus aus seinem Snapshot.

        Roundtrip-Vertrag: `from_snapshot(bus.snapshot())` liefert
        einen ==-identischen Bus (Buffer-Inhalt + next_sequence
        byte-stabil). Typed-Errors bei Format-Verstoessen analog
        Welle-0a-Codec-Pattern.
        """
        if not isinstance(state, Mapping):
            raise AgentBusSnapshotNotAMappingError(type(state).__name__)
        missing = sorted({"version", "next_sequence", "messages"} - set(state))
        if missing:
            raise AgentBusSnapshotMissingKeysError(missing)
        version = state["version"]
        if version != SNAPSHOT_VERSION:
            raise AgentBusSnapshotVersionError(SNAPSHOT_VERSION, version)
        next_sequence = state["next_sequence"]
        if not isinstance(next_sequence, int) or isinstance(next_sequence, bool):
            raise AgentBusSnapshotWrongTypeError(
                "next_sequence", "int", type(next_sequence).__name__
            )
        messages_raw = state["messages"]
        if not isinstance(messages_raw, Sequence) or isinstance(messages_raw, (str, bytes)):
            raise AgentBusSnapshotWrongTypeError(
                "messages", "Sequence", type(messages_raw).__name__
            )
        bus = cls()
        bus._next_sequence = next_sequence
        for index, raw in enumerate(messages_raw):
            if not isinstance(raw, Mapping):
                raise AgentBusSnapshotWrongTypeError(
                    f"messages[{index}]", "Mapping", type(raw).__name__
                )
            bus._buffer.append(_message_from_mapping(raw, index))
        return bus

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AgentMessageBus):
            return NotImplemented
        return self._next_sequence == other._next_sequence and self._buffer == other._buffer

    @override
    def __hash__(self) -> int:
        # Bus ist mutable (publish() veraendert den Buffer); kein
        # Hashing per Vertrag. `__eq__` reicht fuer Test-Vergleich.
        raise _AgentMessageBusUnhashableError


def _message_from_mapping(raw: Mapping[str, object], index: int) -> AgentMessage:
    """Helfer: rekonstruiert einen `AgentMessage` aus dem Snapshot-
    Mapping mit typed Errors."""
    required = ("simulation_time", "sender", "receiver", "message_type", "payload", "sequence")
    missing = [key for key in required if key not in raw]
    if missing:
        raise AgentBusSnapshotMissingKeysError([f"messages[{index}].{key}" for key in missing])
    sim_time = raw["simulation_time"]
    if not isinstance(sim_time, int) or isinstance(sim_time, bool):
        raise AgentBusSnapshotWrongTypeError(
            f"messages[{index}].simulation_time", "int", type(sim_time).__name__
        )
    sender = raw["sender"]
    if not isinstance(sender, str):
        raise AgentBusSnapshotWrongTypeError(
            f"messages[{index}].sender", "str", type(sender).__name__
        )
    receiver = raw["receiver"]
    if not isinstance(receiver, str):
        raise AgentBusSnapshotWrongTypeError(
            f"messages[{index}].receiver", "str", type(receiver).__name__
        )
    message_type = raw["message_type"]
    if not isinstance(message_type, str):
        raise AgentBusSnapshotWrongTypeError(
            f"messages[{index}].message_type", "str", type(message_type).__name__
        )
    payload = raw["payload"]
    if not isinstance(payload, Mapping):
        raise AgentBusSnapshotWrongTypeError(
            f"messages[{index}].payload", "Mapping", type(payload).__name__
        )
    sequence = raw["sequence"]
    if not isinstance(sequence, int) or isinstance(sequence, bool):
        raise AgentBusSnapshotWrongTypeError(
            f"messages[{index}].sequence", "int", type(sequence).__name__
        )
    return AgentMessage(
        simulation_time=sim_time,
        sender=sender,
        receiver=receiver,
        message_type=message_type,
        payload=cast(Mapping[str, object], dict(payload)),
        sequence=sequence,
    )
