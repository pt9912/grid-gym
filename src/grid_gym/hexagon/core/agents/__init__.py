"""Multi-Agent-Subsystem (M3 Welle 3, ADR 0023).

Public Re-exports:

- `Agent` — Sub-Protocol fuer Multi-Agent-Steuerung
  (ADR 0023 §2.1, `hexagon/core/agents/_protocol.py`).
- `AgentMessageBus` — Core-Klasse fuer deterministisch
  sortierte Inter-Agent-Kommunikation
  (ADR 0023 §2.2, `hexagon/core/agents/bus.py`).

Welle-3-Stand: nur Foundation. Konkrete Agent-Implementer
(`RuleBasedAgent` o. ae.) + Agent-Registry + Decision-Logik
kommen mit M3-Welle-4.
"""

from grid_gym.hexagon.core.agents._protocol import Agent, _RandomAttachableAgent
from grid_gym.hexagon.core.agents.bus import SNAPSHOT_VERSION, AgentMessageBus

__all__ = ["SNAPSHOT_VERSION", "Agent", "AgentMessageBus", "_RandomAttachableAgent"]
