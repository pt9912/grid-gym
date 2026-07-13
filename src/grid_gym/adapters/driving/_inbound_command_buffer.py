"""Inbound-Command-Buffer + Capture fuer den Field-Server-Write-Pfad
(`InboundCommandPort`-Impl, ADR 0076 §2.1/§2.3).

Der gemeinsame, **adapterseitige** Hebel der Write-Seite (Modbus jetzt; kuenftige
Pull-Server teilen ihn): ein externer Master-Write wird **thread-sicher**
gepuffert (der Feldbus-Server laeuft in einem eigenen Loop-Thread, entkoppelt vom
`TickLoop.tick()`), mit einer monotonen `arrival_sequence` versehen und bei
`drain_due` auf den **aktuellen** Tick aufgeloest (`Command.simulation_time =
context.simulation_time`).

**Capture (ADR 0076 §2.1/§2.2)**: jeder aufgeloeste Write wird als
`InboundWriteCapture` festgehalten — die **Source-of-Truth** der Aufzeichnung
(aufgeloester Sim-Tick + `arrival_sequence`). `capture()` liefert sie fuer die
Materialisierung in einen Szenario-`commands`-Block (Replay ueber A0s, S2).

**Volatil (ADR 0075 §2.5 / ADR 0076 §2.4)**: Puffer **und** Capture sind
Laufzeit-State im Adapter, **kein** `SnapshotEnvelope`-Slot; ein resumierter
Live-Lauf startet leer, der Replay laeuft ueber den materialisierten Strom.

**Determinismus**: die Anwendungs-Reihenfolge folgt `arrival_sequence` (bei
Enqueue vergeben), **nicht** der Cross-Thread-Ankunftsordnung — die ist selbst
nicht-deterministisch und darf die Semantik nicht bestimmen.
"""

from __future__ import annotations

import threading
from collections.abc import Mapping
from dataclasses import dataclass

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioCommand

_INBOUND_VALIDATION_STATUS = "inbound"


@dataclass(frozen=True, slots=True)
class InboundWriteCapture:
    """Ein aufgeloester Inbound-Write (Aufzeichnung, ADR 0076 §2.1).

    Materialisiert 1:1 auf einen `ScenarioCommand` (`simulation_time = tick`,
    `target`/`type`/`payload`); `arrival_sequence` erhaelt die stabile
    Anwendungs-Reihenfolge bei Same-Tick-Multiplizitaet.
    """

    resolved_sim_tick: int
    target_device_id: str
    command_type: str
    payload: Mapping[str, object]
    arrival_sequence: int


@dataclass(frozen=True, slots=True)
class _PendingWrite:
    target_device_id: str
    command_type: str
    payload: Mapping[str, object]
    arrival_sequence: int


class InboundCommandBuffer:
    """Thread-sicherer Inbound-Write-Puffer; `InboundCommandPort`-Impl.

    `enqueue(...)` (vom Server-Loop-Thread) puffert einen Write mit
    `arrival_sequence`; `drain_due(context)` (vom Tick-Loop-Thread) loest die
    Puffer-Writes auf den aktuellen Tick auf, leert den Puffer und zeichnet sie
    als `InboundWriteCapture` auf.
    """

    def __init__(self) -> None:
        self._lock: threading.Lock = threading.Lock()
        self._pending: list[_PendingWrite] = []
        self._capture: list[InboundWriteCapture] = []
        self._next_sequence: int = 0

    def enqueue(
        self,
        target_device_id: str,
        command_type: str,
        payload: Mapping[str, object],
    ) -> int:
        """Puffert einen Inbound-Write (Server-Loop-Thread). Gibt die vergebene
        `arrival_sequence` zurueck. Auf den Tick aufgeloest wird erst bei
        `drain_due` (Next-Tick-Semantik, ADR 0076 §2.3)."""
        with self._lock:
            sequence = self._next_sequence
            self._next_sequence += 1
            self._pending.append(
                _PendingWrite(target_device_id, command_type, dict(payload), sequence)
            )
            return sequence

    def drain_due(self, context: DeviceTickContext) -> tuple[Command, ...]:
        """Faellige Inbound-Commands fuer den aktuellen Tick (ADR 0076 §2.3):
        loest die Puffer-Writes auf `context.simulation_time` auf (stabile
        `arrival_sequence`-Ordnung), leert den Puffer und zeichnet sie auf."""
        with self._lock:
            pending = sorted(self._pending, key=lambda write: write.arrival_sequence)
            self._pending = []
            commands: list[Command] = []
            for write in pending:
                self._capture.append(
                    InboundWriteCapture(
                        resolved_sim_tick=context.simulation_time,
                        target_device_id=write.target_device_id,
                        command_type=write.command_type,
                        payload=write.payload,
                        arrival_sequence=write.arrival_sequence,
                    )
                )
                commands.append(
                    Command(
                        command_id=f"inbound-cmd-{write.arrival_sequence}",
                        simulation_time=context.simulation_time,
                        target_device_id=write.target_device_id,
                        type=write.command_type,
                        payload=write.payload,
                        validation_status=_INBOUND_VALIDATION_STATUS,
                        result=CommandResult.IGNORED,
                    )
                )
            return tuple(commands)

    def capture(self) -> tuple[InboundWriteCapture, ...]:
        """Aufzeichnung der bisher aufgeloesten Inbound-Writes (fuer die
        Materialisierung in einen Szenario-`commands`-Block, ADR 0076 §2.1).

        **Lebensdauer = Run-Session** (Review-Fund Slice 075): der Puffer ist
        append-only fuer die Dauer des Laufs (kein Pruning) — die Aufzeichnung ist
        die Source-of-Truth und muss bis zur Materialisierung am Run-Ende
        vollstaendig bleiben. Der Puffer ist volatil (kein Snapshot-Slot); ein
        resumierter Live-Lauf startet leer. Fuer eine unbegrenzt lange Live-Session
        mit sehr vielen Writes waere ein Roll-off nach Materialisierung ein additiver
        Folgeschritt (heute: Session-scoped, HIL-Laeufe sind begrenzt)."""
        with self._lock:
            return tuple(self._capture)


def materialize_inbound_writes(
    captures: tuple[InboundWriteCapture, ...],
) -> tuple[ScenarioCommand, ...]:
    """Materialisiert eine Inbound-Write-Capture in einen Szenario-`commands`-Block
    (ADR 0076 §2.1/§2.2).

    Jeder `InboundWriteCapture` mappt **1:1** auf einen `ScenarioCommand`
    (`simulation_time = resolved_sim_tick`, `target`/`type`/`payload`) — ein
    Inbound-Write ist strukturgleich zu einem scenario-scheduled Command
    ([`ADR 0070`](0070)). Die Reihenfolge ist deterministisch nach
    `(resolved_sim_tick, arrival_sequence)`; damit spielt der materialisierte Strom
    ueber den Vor-Tick-Pfad A0s **byte-identisch** ab (S2, `scenario_hash` deckt
    `commands`), unabhaengig von der nicht-deterministischen Cross-Thread-
    Ankunftsordnung des Live-Laufs.
    """
    ordered = sorted(captures, key=lambda write: (write.resolved_sim_tick, write.arrival_sequence))
    return tuple(
        ScenarioCommand(
            simulation_time=write.resolved_sim_tick,
            target=write.target_device_id,
            type=write.command_type,
            payload=write.payload,
        )
        for write in ordered
    )
