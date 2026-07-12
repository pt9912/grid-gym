"""Shape-Pin fuer `InboundCommandPort` (driven, ADR 0076 §2.1).

Runtime-checkable Protocol: der adapterseitige `InboundCommandBuffer` erfuellt
den Port; ein Typ ohne `drain_due` nicht.
"""

from __future__ import annotations

from grid_gym.adapters.driving._inbound_command_buffer import InboundCommandBuffer
from grid_gym.hexagon.ports.driven.inbound_command import InboundCommandPort


def test_buffer_satisfies_inbound_command_port() -> None:
    assert isinstance(InboundCommandBuffer(), InboundCommandPort)


def test_non_conforming_type_is_not_a_port() -> None:
    class _NotAPort:
        pass

    assert not isinstance(_NotAPort(), InboundCommandPort)
