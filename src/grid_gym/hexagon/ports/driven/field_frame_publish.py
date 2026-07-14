"""`FieldFramePublishPort` Driven-Port fuer die Tick-Frame-Push-Seite (ADR 0079 §2.4).

Schwester-Port zu `FieldPublishPort` (ADR 0075, per-Punkt): waehrend `FieldPublishPort`
je emittiertem `TelemetryPoint` publisht, aggregiert dieser Port je Tick den
**vollstaendigen** `TickResult` zu einem breiten Feld-Frame (bess-ems-Envelope,
ADR 0078 §2.1) und published ihn als **eine** Einheit. Getrennter Vertrag
(ADR-0075-Schwester-Muster, kein geteilter Port — per-Punkt vs. Tick-Frame).

ADR 0079 Decision B fuehrt den Port ein, damit der Driver (`_tick_loop_driver`) die
Tick-Frame-Publisher gegen einen Port statt gegen den konkreten
`BessEmsFieldPublishAdapter` typisiert (a-check `lateral-adapter`-konform, ADR 0079 §2.1).

**Placement/Lifecycle (analog `FieldPublishPort`, ADR 0075 §2.3/§2.4):** `start()`/
`stop()` werden **driver-getrieben** in der Kompositions-/Driver-Schicht gerufen (wo
`TickResult` je Tick vollstaendig sichtbar ist, ADR 0078 §2.1); der Driver ruft
`start()` vor dem ersten `publish_tick()` und `stop()` am Run-Ende (auch im
Exception-Pfad).

**Stateless aus Replay-Sicht (ADR 0078 §2.7):** zustandslose Projektion des
`TickResult`, kein Snapshot-Slot. Ohne konfigurierten Port byte-identisch.

**Sim-/Test-Charakter (`GG-SAFE-007`, ADR 0078 §2.8):** simuliertes Feld, keine
produktive Anlagensteuerung; Broker-Exposure ist Nur-Sim-Netz-Annahme.

Heutiger Implementer: `BessEmsFieldPublishAdapter`
(`adapters/driven/field_publish_bess_ems/`), der ihn strukturell erfuellt.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from grid_gym.hexagon.core.domain.tick_result import TickResult


@runtime_checkable
class FieldFramePublishPort(Protocol):
    """Driven-Port fuer die Tick-Frame-Push-Seite (ADR 0079 §2.4).

    Pflicht-Surface:

    - `start() -> None`: Broker-Connect (+ optionaler Command-Subscribe). Wird vom
      Driver **vor** dem ersten `publish_tick()` gerufen.
    - `publish_tick(result) -> None`: aggregiert den **vollstaendigen** `TickResult`
      zu einem breiten Feld-Frame und published ihn. Der Driver ruft es je Tick.
    - `stop() -> None`: Disconnect am Run-Ende (auch im Exception-Pfad), idempotent
      nach erfolglosem `start()`.

    Adapter-Verantwortung (analog `FieldPublishPort`, ADR 0075 §2.1): Sync-Surface
    (async-/Callback-Stacks adapter-intern marshalen), idempotenter `stop()`,
    volatiler Broker-State (kein Snapshot), Sim-/Test-Doku.
    """

    def start(self) -> None:
        """Broker-Connect (+ optionaler Command-Subscribe). Wird vom Driver vor dem
        ersten `publish_tick()` gerufen."""
        ...

    def publish_tick(self, result: TickResult) -> None:
        """Aggregiert `result` zu einem breiten Feld-Frame und published ihn (Push
        zum Broker). Der Driver ruft es je Tick aus dem Telemetrie-Fan-out."""
        ...

    def stop(self) -> None:
        """Disconnect am Run-Ende. Idempotent nach erfolglosem/nicht-erfolgtem
        `start()`, ohne zu werfen."""
        ...
