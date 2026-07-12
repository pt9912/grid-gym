"""`InboundCommandPort` — driven-Port fuer den Field-Server-Write-Pfad
(ADR 0076 §2.1/§2.3).

Der `TickLoop` **pullt** pro Tick die faelligen Inbound-Writes (Schritt **A0i**,
nach A0s/A0a — Ordnung scenario→agent→inbound, ADR 0076 §2.3) und wendet sie als
`Command` auf die Zielgeraete an. „Driven", weil der Kern **auslesend** aufruft
(wie `ClockPort`/`RandomPort`); die Datenherkunft (ein externer Master-Write) ist
extern, die **Aufruf-Richtung** ist Kern → Port.

**Exogen-Input-Recording (ADR 0076 §2.1/§2.2)**: ein Live-Master-Write kommt zu
Wall-Clock-Zeit an; der Port puffert ihn adapterseitig (thread-sicher, mit
`arrival_sequence`) und loest ihn bei `drain_due` auf den **aktuellen** Tick auf
(`Command.simulation_time = context.simulation_time`). Der aufgeloeste Tick ist die
Source-of-Truth der Aufzeichnung — der Live-Lauf ist nicht aus
`(Szenario, Seed, tick_ms)` allein reproduzierbar, der **erfasste** Strom aber
deterministisch (Materialisierung → `commands`-Block → Replay ueber A0s).

**Stateless-Snapshot-Grenze (ADR 0075 §2.5 / ADR 0076 §2.4)**: der Puffer ist
**volatil** (adapterseitig, kein `SnapshotEnvelope`-Slot). Ein resumierter
Live-Lauf startet mit leerem Puffer; der Replay laeuft ohnehin ueber den
materialisierten `commands`-Block (A0s), nicht ueber diesen Port.

**`None`-Skip**: ohne konfigurierten `InboundCommandPort` ist Schritt A0i ein
No-op → Bestands-Laeufe byte-identisch (pin-neutral).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.device import DeviceTickContext


@runtime_checkable
class InboundCommandPort(Protocol):
    """Driven-Port: liefert die im aktuellen Tick anzuwendenden Inbound-Commands.

    `drain_due(context)` gibt die gepufferten Inbound-Writes als `Command`s
    zurueck — **aufgeloest** auf `context.simulation_time` und in stabiler
    `arrival_sequence`-Reihenfolge — und **entleert** den Puffer (die Writes sind
    damit auf diesen Tick fixiert). Ein leerer Puffer liefert `()`.
    """

    def drain_due(self, context: DeviceTickContext) -> tuple[Command, ...]:
        """Faellige Inbound-Commands fuer den aktuellen Tick (leert den Puffer)."""
        ...
