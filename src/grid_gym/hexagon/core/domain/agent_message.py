"""Agent-Nachricht-Datenmodell (M3 Welle 3, ADR 0023 §2.3).

Standardisierte Nachricht zwischen Agenten ueber den
`AgentMessageBus`. Pflicht-Felder per `GG-AGENT-004`-Akzeptanz:
`simulation_time`, `sender`, `receiver`, `message_type`,
`payload`, `sequence`.

Welle 3 modelliert die Nachricht als Frozen-Dataclass mit dem
gleichen `Mapping[str, object]`-Payload-Vertrag wie
`Command`/`Event`/`ScenarioFault` (`canonical_json`-vertraeglich).
Sortier-Schluessel im Bus (`AgentMessageBus.drain_for`):
`(simulation_time, sender, sequence)`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentMessage:
    """Eine Nachricht zwischen zwei Agenten (oder Broadcast).

    Felder gemaess `GG-AGENT-004`:
    - `simulation_time`: Sim-Zeit des Sendezeitpunkts in ms.
    - `sender`: `agent_id` des Senders.
    - `receiver`: `agent_id` des Empfaengers ODER `"*"` fuer
      Broadcast (per ADR 0023 §2.3 fester Wert; keine
      Whitelist sonstiger Pattern in Welle 3).
    - `message_type`: domain-spezifischer Nachrichtentyp;
      Wertebereich offen (Welle 4 schaerft pro Agent-Typ).
    - `payload`: Nachrichten-Parameter; `Mapping[str, object]`
      ist der `canonical_json`-Vertrag analog
      `Command.payload`/`Event.payload`.
    - `sequence`: per-Tick-monoton aufsteigend, vom Bus vergeben.
      Letztes Tie-Breaking-Glied bei `drain_for(...)`-Sortierung.
    """

    simulation_time: int
    sender: str
    receiver: str
    message_type: str
    payload: Mapping[str, object]
    sequence: int
