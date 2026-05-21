"""Tests fuer `AgentMessageBus` (M3 Welle 3, ADR 0023 §2.2).

Pinnt:

- Sequence-Vergabe: `publish(message_with_sequence=-1)` vergibt
  monoton aufsteigende Sequence-Nummern.
- `drain_for(receiver)`-Sortier-Vertrag:
  `(simulation_time, sender, sequence)`.
- Broadcast (`receiver="*"`) wird an jeden Drain-Aufrufer
  ausgeliefert.
- Snapshot-Roundtrip ist byte-stabil (`from_snapshot(snapshot())`
  liefert ==-identischen Bus).
- Typed-Errors bei Snapshot-Format-Verstoessen.
- Drain ist nicht-destruktiv (Welle-3-Vertrag, ADR 0023 §2.2).
"""

from __future__ import annotations

import pytest

from grid_gym.hexagon.core.agents import SNAPSHOT_VERSION, AgentMessageBus
from grid_gym.hexagon.core.domain.agent_message import AgentMessage
from grid_gym.hexagon.core.errors import (
    AgentBusError,
    AgentBusInvalidReceiverError,
    AgentBusInvalidSequenceError,
    AgentBusSnapshotFormatError,
    AgentBusSnapshotMissingKeysError,
    AgentBusSnapshotVersionError,
    AgentBusSnapshotWrongTypeError,
)


def _msg(
    *,
    sim: int = 1000,
    sender: str = "agent-a",
    receiver: str = "agent-b",
    msg_type: str = "ping",
    payload: dict[str, object] | None = None,
    sequence: int = -1,
) -> AgentMessage:
    return AgentMessage(
        simulation_time=sim,
        sender=sender,
        receiver=receiver,
        message_type=msg_type,
        payload=payload or {},
        sequence=sequence,
    )


def test_publish_assigns_monotonic_sequence_when_sentinel() -> None:
    """ADR 0023 §2.2: `sequence=-1` ist Sentinel; Bus vergibt
    naechste freie Nummer."""
    bus = AgentMessageBus()
    bus.publish(_msg(sequence=-1))
    bus.publish(_msg(sequence=-1))
    bus.publish(_msg(sequence=-1))
    drained = bus.drain_for("agent-b")
    assert [m.sequence for m in drained] == [0, 1, 2]


def test_publish_with_explicit_sequence_advances_counter() -> None:
    """Wenn der Aufrufer einen expliziten `sequence`-Wert setzt,
    ueberholt der Counter ihn — naechster Sentinel-Publish landet
    danach."""
    bus = AgentMessageBus()
    bus.publish(_msg(sequence=100))
    bus.publish(_msg(sequence=-1))  # → 101
    drained = bus.drain_for("agent-b")
    assert [m.sequence for m in drained] == [100, 101]


def test_publish_with_lower_explicit_sequence_does_not_rewind_counter() -> None:
    """Out-of-Order-Tests duerfen den Counter nicht zurueckrollen —
    Welle-3-Robustheit: explicit `sequence=5` nach `sequence=10`
    laesst den Counter bei 11."""
    bus = AgentMessageBus()
    bus.publish(_msg(sequence=10))
    bus.publish(_msg(sequence=5))
    bus.publish(_msg(sequence=-1))
    drained = bus.drain_for("agent-b")
    # Sortierung primaer nach simulation_time (1000=1000=1000), dann
    # sender (alle "agent-a"), dann sequence aufsteigend.
    assert [m.sequence for m in drained] == [5, 10, 11]


def test_drain_for_returns_only_matching_receiver() -> None:
    """ADR 0023 §2.2: `drain_for(receiver)` filtert auf
    `receiver==<arg>` oder `receiver=="*"` (Broadcast)."""
    bus = AgentMessageBus()
    bus.publish(_msg(sender="agent-x", receiver="agent-a", sequence=-1))
    bus.publish(_msg(sender="agent-x", receiver="agent-b", sequence=-1))
    bus.publish(_msg(sender="agent-x", receiver="*", sequence=-1))
    drained_a = bus.drain_for("agent-a")
    drained_b = bus.drain_for("agent-b")
    drained_c = bus.drain_for("agent-c")
    assert {m.receiver for m in drained_a} == {"agent-a", "*"}
    assert {m.receiver for m in drained_b} == {"agent-b", "*"}
    assert {m.receiver for m in drained_c} == {"*"}


def test_drain_for_is_deterministic_independent_of_publish_order() -> None:
    """ADR 0023 §2.2 Sortier-Vertrag: gleiche Nachrichten in
    verschiedener Publish-Reihenfolge → gleiche `drain_for(...)`-
    Reihenfolge."""
    bus1 = AgentMessageBus()
    bus1.publish(_msg(sim=2000, sender="agent-b", sequence=-1))
    bus1.publish(_msg(sim=1000, sender="agent-a", sequence=-1))
    bus1.publish(_msg(sim=1000, sender="agent-b", sequence=-1))

    bus2 = AgentMessageBus()
    bus2.publish(_msg(sim=1000, sender="agent-b", sequence=2))
    bus2.publish(_msg(sim=2000, sender="agent-b", sequence=0))
    bus2.publish(_msg(sim=1000, sender="agent-a", sequence=1))

    drained1 = bus1.drain_for("agent-b")
    drained2 = bus2.drain_for("agent-b")
    keys1 = [(m.simulation_time, m.sender, m.sequence) for m in drained1]
    keys2 = [(m.simulation_time, m.sender, m.sequence) for m in drained2]
    assert keys1 == keys2


def test_drain_for_is_non_destructive() -> None:
    """ADR 0023 §2.2 Welle-3-Drain-Semantik: nach `drain_for(...)`
    bleibt der Buffer voll — Welle 4 darf eine destruktive
    `consume_for`-Variante einfuehren, aber die existiert nicht
    in Welle 3."""
    bus = AgentMessageBus()
    bus.publish(_msg(sequence=-1))
    assert len(bus.drain_for("agent-b")) == 1
    assert len(bus.drain_for("agent-b")) == 1


def test_snapshot_roundtrip_is_byte_stable() -> None:
    """ADR 0015 §2.3 Sub-Snapshot-Roundtrip-Vertrag: zwei
    Snapshots vor und nach Restore sind ==-identisch."""
    bus = AgentMessageBus()
    bus.publish(_msg(sender="agent-a", receiver="agent-b", sequence=-1))
    bus.publish(_msg(sender="agent-c", receiver="*", payload={"nested": {"k": 1}}, sequence=-1))
    snapshot_before = bus.snapshot()
    restored = AgentMessageBus.from_snapshot(snapshot_before)
    snapshot_after = restored.snapshot()
    assert snapshot_after == snapshot_before
    assert restored == bus


def test_snapshot_version_is_one_in_welle_3() -> None:
    """Welle-3-Schema-Version ist 1 (ADR 0023 §2.2)."""
    bus = AgentMessageBus()
    assert bus.snapshot()["version"] == SNAPSHOT_VERSION == 1


def test_from_snapshot_rejects_unknown_version() -> None:
    """Typed-Error bei Schema-Drift (Welle-0a-Codec-Pattern)."""
    with pytest.raises(AgentBusSnapshotVersionError):
        AgentMessageBus.from_snapshot({"version": 999, "next_sequence": 0, "messages": []})


def test_from_snapshot_rejects_missing_keys() -> None:
    """Pflicht-Keys-Pruefung."""
    with pytest.raises(AgentBusSnapshotMissingKeysError):
        AgentMessageBus.from_snapshot({"version": 1})  # missing next_sequence + messages


def test_from_snapshot_rejects_non_mapping_payload() -> None:
    """Format-Pruefung: top-level state muss Mapping sein."""
    with pytest.raises(AgentBusSnapshotFormatError):
        AgentMessageBus.from_snapshot("not a mapping")  # type: ignore[arg-type]


def test_from_snapshot_rejects_wrong_type_next_sequence() -> None:
    """Typed-Error wenn `next_sequence` kein int ist."""
    with pytest.raises(AgentBusSnapshotWrongTypeError):
        AgentMessageBus.from_snapshot({"version": 1, "next_sequence": "5", "messages": []})


def test_from_snapshot_rejects_bool_as_int_next_sequence() -> None:
    """`bool` ist int-Subklasse; explizit ausgeschlossen analog
    `NonIntegerSubSnapshotVersionError`-Pattern."""
    with pytest.raises(AgentBusSnapshotWrongTypeError):
        AgentMessageBus.from_snapshot({"version": 1, "next_sequence": True, "messages": []})


def test_from_snapshot_rejects_non_sequence_messages() -> None:
    """`messages` muss Sequence sein (kein str/bytes)."""
    with pytest.raises(AgentBusSnapshotWrongTypeError):
        AgentMessageBus.from_snapshot({"version": 1, "next_sequence": 0, "messages": "not a list"})


def test_from_snapshot_rejects_malformed_message_entry() -> None:
    """Element in `messages` muss Mapping sein."""
    with pytest.raises(AgentBusSnapshotWrongTypeError):
        AgentMessageBus.from_snapshot(
            {"version": 1, "next_sequence": 0, "messages": ["not a mapping"]}
        )


def test_from_snapshot_rejects_message_missing_field() -> None:
    """Pflicht-Felder pro Message-Eintrag."""
    incomplete = {"simulation_time": 0, "sender": "a"}  # missing receiver, type, payload, sequence
    with pytest.raises(AgentBusSnapshotMissingKeysError):
        AgentMessageBus.from_snapshot({"version": 1, "next_sequence": 0, "messages": [incomplete]})


def test_agent_bus_is_not_hashable() -> None:
    """Bus ist mutable; Hashing ist per Vertrag ausgeschlossen."""
    bus = AgentMessageBus()
    with pytest.raises(TypeError, match="not hashable"):
        hash(bus)


def test_agent_bus_errors_inherit_from_agent_bus_error_base() -> None:
    """Alle AgentBus-spezifischen Format-Errors erben von
    `AgentBusError` (ADR 0023 §2.6 Exception-Family)."""
    assert issubclass(AgentBusSnapshotFormatError, AgentBusError)
    assert issubclass(AgentBusSnapshotMissingKeysError, AgentBusError)
    assert issubclass(AgentBusSnapshotWrongTypeError, AgentBusError)
    assert issubclass(AgentBusSnapshotVersionError, AgentBusError)
    # Welle-3-Review-Folge L-2 + L-3 (2026-05-21): Defensive-
    # Validation-Errors erben ebenfalls von AgentBusError.
    assert issubclass(AgentBusInvalidSequenceError, AgentBusError)
    assert issubclass(AgentBusInvalidReceiverError, AgentBusError)


def test_publish_rejects_sequence_below_minus_one() -> None:
    """Welle-3-Review-Folge L-2 (2026-05-21): `sequence < -1`
    wirft typisiert; sonst wuerde der Wert in der Sortier-Logik
    vor den echten Sequenzen 0,1,2,... landen."""
    bus = AgentMessageBus()
    with pytest.raises(AgentBusInvalidSequenceError):
        bus.publish(_msg(sequence=-2))


def test_publish_accepts_sentinel_minus_one() -> None:
    """Sentinel `-1` bleibt zulaessig (L-2-Schaerfung verbietet
    nur `< -1`)."""
    bus = AgentMessageBus()
    bus.publish(_msg(sequence=-1))  # darf NICHT werfen
    assert bus.next_sequence == 1


def test_drain_for_rejects_broadcast_wildcard() -> None:
    """Welle-3-Review-Folge L-3 (2026-05-21): `drain_for("*")`
    ist verboten — `"*"` ist Publish-Pfad-Broadcast, kein
    Drain-Pfad-Wildcard."""
    bus = AgentMessageBus()
    bus.publish(_msg(receiver="*", sequence=-1))
    with pytest.raises(AgentBusInvalidReceiverError):
        bus.drain_for("*")


def test_next_sequence_property_reflects_counter() -> None:
    """Test-Accessor: `next_sequence` ist Sicht auf Counter."""
    bus = AgentMessageBus()
    assert bus.next_sequence == 0
    bus.publish(_msg(sequence=-1))
    assert bus.next_sequence == 1
    bus.publish(_msg(sequence=42))
    assert bus.next_sequence == 43
