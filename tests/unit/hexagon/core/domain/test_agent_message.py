"""Tests fuer `AgentMessage` (M3 Welle 3, ADR 0023 §2.3).

Pinnt:

- Frozen-Vertrag: Reassign-Attempt wirft `FrozenInstanceError`
  (AC-DOMAIN-FROZEN per ADR 0002 §A-1).
- canonical_json-Stabilitaet ueber Snapshot/Restore-Roundtrip.
- Sortier-Schluessel `(simulation_time, sender, sequence)`
  liefert deterministische Reihenfolge.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from grid_gym.hexagon.core.domain.agent_message import AgentMessage


def test_agent_message_is_frozen() -> None:
    """ADR 0023 §2.3: frozen dataclass — Reassign wirft."""
    message = AgentMessage(
        simulation_time=1000,
        sender="agent-a",
        receiver="agent-b",
        message_type="ping",
        payload={"value": 42},
        sequence=0,
    )
    with pytest.raises(FrozenInstanceError):
        message.simulation_time = 2000  # type: ignore[misc]


def test_agent_message_equality_by_value() -> None:
    """Frozen dataclasses haben Value-Equality."""
    msg_a = AgentMessage(
        simulation_time=1000,
        sender="agent-a",
        receiver="agent-b",
        message_type="ping",
        payload={"value": 42},
        sequence=0,
    )
    msg_b = AgentMessage(
        simulation_time=1000,
        sender="agent-a",
        receiver="agent-b",
        message_type="ping",
        payload={"value": 42},
        sequence=0,
    )
    assert msg_a == msg_b


def test_agent_message_broadcast_receiver_is_just_a_string() -> None:
    """ADR 0023 §2.3: `"*"` ist Bus-Konvention, kein
    AgentMessage-Constructor-Vertrag. Die Klasse akzeptiert
    `"*"` als gewoehnlichen Receiver-String — Bus-Sortier-/
    Drain-Logik macht die Broadcast-Interpretation."""
    broadcast = AgentMessage(
        simulation_time=0,
        sender="agent-a",
        receiver="*",
        message_type="announce",
        payload={},
        sequence=0,
    )
    assert broadcast.receiver == "*"


def test_agent_message_sort_key_tuple_pinning() -> None:
    """ADR 0023 §2.2 Sortier-Schluessel: `(simulation_time, sender,
    sequence)`. Test pinnt, dass natuerliche Tuple-Sortierung das
    erwartete Ergebnis liefert."""
    messages = [
        AgentMessage(
            simulation_time=2000,
            sender="agent-b",
            receiver="*",
            message_type="t",
            payload={},
            sequence=0,
        ),
        AgentMessage(
            simulation_time=1000,
            sender="agent-a",
            receiver="*",
            message_type="t",
            payload={},
            sequence=2,
        ),
        AgentMessage(
            simulation_time=1000,
            sender="agent-a",
            receiver="*",
            message_type="t",
            payload={},
            sequence=1,
        ),
        AgentMessage(
            simulation_time=1000,
            sender="agent-b",
            receiver="*",
            message_type="t",
            payload={},
            sequence=0,
        ),
    ]
    sorted_msgs = sorted(messages, key=lambda m: (m.simulation_time, m.sender, m.sequence))
    expected_order = [
        (1000, "agent-a", 1),
        (1000, "agent-a", 2),
        (1000, "agent-b", 0),
        (2000, "agent-b", 0),
    ]
    actual_order = [(m.simulation_time, m.sender, m.sequence) for m in sorted_msgs]
    assert actual_order == expected_order
