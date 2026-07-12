"""`FieldPublishPort` Driven-Port (Field-Server-Surface, ADR 0075 §2.1).

Driven-Port-Vertrag fuer die **Push-Seite** der Field-Server-Surface: ein
externes EMS (System-under-Test, z. B. `bess-ems`) konsumiert grid-gyms
simulierte Geraetetelemetrie ueber einen Broker. Motivation ist die HIL/SUT-
Anbindung (`GG-TEST-004`, HIL-Konkretisierung; keine eigene `GG-*`-ID,
ADR 0075 §7).

**Schwester-Port (ADR 0075 §2.1)**: `FieldPublishPort` (Push, hier) und der
driving-seitige `DeviceServerPort` (Pull, Slice 074) sind zwei getrennt
typisierte Ports (ADR 0011-Schwester-Muster) — **kein** geteilter Vertrag. Der
gemeinsame Hebel ist die Current-Value-Projektion (Helper, ADR 0075 §2.2), die
nur die Pull-Seite braucht; die Push-Seite leitet jeden emittierten Punkt
direkt weiter.

**Domaenen-`TelemetryPoint` (ADR 0075 §2.1)**: `publish` nimmt den
Domaenen-`TelemetryPoint` (`GG-DATA-001`, `value: Decimal`) — wie
`DeviceProtocolPort`. Kein driven->driving-Import, keine `Decimal->float`-Lossy-
Konvertierung der driving-Stream-DTO.

**Placement / Lifecycle (ADR 0075 §2.3/§2.4)**: `start()`/`stop()` werden
**driver-getrieben** in der Kompositions-/Driver-Schicht gerufen (wo der
Telemetry-Fan-out lebt, `_tick_loop_driver`) — **nicht** ueber einen
`TickLoop`-Kwarg. Der Kern-`TickLoop` laeuft produktiv im `simulation`-Worker
ohne Broker (ADR 0012, Zwei-Prozess-Naht). Der Driver ruft `start()` vor dem
ersten Publish und `stop()` am Run-Ende (auch im Exception-Pfad).

**Stateless aus Replay-Sicht (ADR 0075 §2.5)**: Broker-Connection/Subscribe-
State ist **volatile** und wird **nicht** in `SnapshotEnvelope` persistiert.
Ohne konfigurierten Port ist der Run byte-identisch (kein Broker-Connect).

**Sim-/Test-Charakter (ADR 0075 §2.6, `GG-SAFE-007`/`GG-NONGOAL-001`)**: die
exponierte Surface dient simulierten Geraeten/Testaufbauten — **keine**
produktive Anlagensteuerung. Broker-Exposure ist eine Nur-Sim-Netz-Annahme
(Deployment-Note im Adapter).

**Adapter (Slice 073)**: `MqttFieldPublishAdapter` unter
`adapters/driven/field_publish_mqtt/` (paho-mqtt, adapter-interner Loop/Queue).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import GridGymError


@runtime_checkable
class FieldPublishPort(Protocol):
    """Driven-Port fuer die Field-Server-Push-Seite (ADR 0075 §2.1).

    Pflicht-Surface:

    - `start() -> None`: Broker-Connect. Wird vom Driver **vor** dem ersten
      `publish()` gerufen (Kompositions-Schicht, ADR 0075 §2.3/§2.4).
    - `publish(point) -> None`: exponiert einen emittierten
      `TelemetryPoint` (Push zum Broker). Der Driver ruft es je Punkt aus
      `TickResult.emitted_telemetry`.
    - `stop() -> None`: Disconnect. Wird vom Driver am Run-Ende (auch im
      Exception-Pfad) gerufen; idempotent nach erfolglosem `start()`.

    Adapter-Verantwortung (analog `DeviceProtocolPort`, ADR 0030 §4):

    1. **Sync-Surface**: alle Methoden sind sync; async-/Callback-Stacks
       (paho-mqtt-Loop-Thread) marshalen adapter-intern.
    2. **Idempotenz**: `stop()` nach erfolglosem/nicht-erfolgtem `start()`
       ist No-op.
    3. **Volatile State**: kein Snapshot-Slot; Reconnect ist
       Adapter-Verantwortung.
    4. **Sim-/Test-Doku**: Modul-Docstring dokumentiert den Sim-/Test-
       Charakter; keine Produktivsteuerung (`GG-SAFE-007`).
    """

    def start(self) -> None:
        """Broker-Connect. Wird vom Driver vor dem ersten `publish()`
        gerufen.

        Exception-Vertrag: `FieldPublishPortStartError` (oder Adapter-
        Subclass) bei Connect-Fehler; der Driver-Setup behandelt das
        analog zum `DeviceProtocolPort`-Start (kein Publish, wenn
        `start()` wirft).
        """
        ...

    def publish(self, point: TelemetryPoint) -> None:
        """Exponiert `point` nach aussen (Push zum Broker).

        Der Driver ruft es je emittiertem `TelemetryPoint`. Wirft
        `FieldPublishPortPublishError` (oder Adapter-Subclass) bei
        Sende-Fehlern.
        """
        ...

    def stop(self) -> None:
        """Disconnect. Wird vom Driver am Run-Ende gerufen.

        Idempotenz-Vertrag: `stop()` nach erfolglosem oder nicht-erfolgtem
        `start()` ist No-op, ohne zu werfen. Exception-Vertrag:
        `FieldPublishPortStopError` nur bei **harten** Disconnect-Fehlern.
        """
        ...


# ---------------------------------------------------------------------------
# Error-Hierarchie (ADR 0075 §2.1; Muster analog `DeviceProtocolPortError`)
# ---------------------------------------------------------------------------


class FieldPublishPortError(GridGymError):
    """Wurzel der `FieldPublishPort`-Vertragsverletzungen (ADR 0075).

    Adapter werfen typed Subclasses (`FieldPublishPortStartError`,
    `FieldPublishPortPublishError`, `FieldPublishPortStopError`).
    """


class FieldPublishPortStartError(FieldPublishPortError):
    """`start()` ist fehlgeschlagen — Adapter konnte nicht zum Broker
    connecten.

    Der Driver-Setup startet keinen Publish-Fan-out, wenn `start()` wirft
    (analog `DeviceProtocolPort`-Partial-Start-Vertrag, ADR 0030 §2.2).
    """


class FieldPublishPortPublishError(FieldPublishPortError):
    """`publish(point)` ist fehlgeschlagen — Adapter konnte den Punkt nicht
    zum Broker senden.

    Subclasses fuer Verbindungs- vs. Serialisierungs-Fehler folgen bei
    Bedarf im Adapter.
    """


class FieldPublishPortStopError(FieldPublishPortError):
    """`stop()` ist fehlgeschlagen — Adapter konnte nicht sauber vom Broker
    disconnecten.

    Idempotenz-Vertrag (ADR 0075 §2.1): `stop()` nach erfolglosem/nicht-
    erfolgtem `start()` ist No-op — diese Exception ist nur fuer **harte**
    Disconnect-Probleme reserviert.
    """
