"""`DeviceProtocolPort` Driven-Port (M4 Welle 1, ADR 0030 §2.1).

Driven-Port-Vertrag fuer externe Feldprotokoll-Adapter (MQTT,
Modbus TCP, OPC-UA, DNP3, IEC 61850 — `GG-AR-PORT-DRN-007`).
Welle-1-Surface ist bewusst minimal; konkrete Methoden-
Signaturen (Multi-Target-Read, Subscribe-Pattern, Batched-Write)
schaerft Welle-2-Adapter-ADR.

**Welle-1-Stand**: dieses Modul liefert nur den Protocol-
Vertrag + `*Error`-Subsystem. Konkrete Adapter
(`MqttDeviceProtocolAdapter`, `ModbusDeviceProtocolAdapter`,
...) leben ab Welle 2 unter `adapters/driven/protocol_*/`
(siehe ADR 0030 §4 Konsequenzen).

**Sync-Charakter (ADR 0030 §2.1)**: `DeviceProtocolPort` ist
ein sync-`typing.Protocol`. Async-Stacks (`asyncua`, ggf.
DNP3/IEC) marshalen Calls adapter-intern ueber einen
Event-Loop-Thread + Queue.

**Lifecycle (ADR 0030 §2.2)**: `start()` und `stop()` werden
vom Caller ueber `TickLoop.start_protocol_ports()` /
`TickLoop.stop_protocol_ports()` getrieben (Caller-Scope,
nicht `TickLoop.run()` — die Methode existiert nicht; siehe
ADR 0030 §2.2 Alternative A3).

**Stateless aus Replay-Sicht (ADR 0030 §2.3)**: Reconnect-
State (z. B. Modbus-Read-Cursor, MQTT-Subscribe-Acks) ist
**volatile** und wird **nicht** in `SnapshotEnvelope`
persistiert. Snapshot-Restore-Pfad ruft `start()` regulaer
wie aus Cold-Start.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import GridGymError


@runtime_checkable
class DeviceProtocolPort(Protocol):
    """Driven-Port fuer externe Feldprotokoll-Adapter
    (ADR 0030 §2.1).

    Pflicht-Surface (Welle-1-Minimum):

    - `start() -> None`: Adapter-Connect / Subscribe. Wird
      vom Caller ueber `TickLoop.start_protocol_ports()`
      **vor** dem ersten `TickLoop.tick()`-Aufruf gerufen.
    - `stop() -> None`: Adapter-Disconnect / Unsubscribe.
      Wird vom Caller ueber `TickLoop.stop_protocol_ports()`
      **nach** dem letzten `TickLoop.tick()`-Aufruf (oder
      bei Exception, wenn der Caller-`try/finally` greift)
      gerufen.
    - `read(target) -> TelemetryPoint | None`: liest den
      aktuellen Wert fuer das gegebene Target und mappt
      ihn auf einen `TelemetryPoint`. Gibt `None` zurueck,
      wenn der Adapter aktuell keinen Wert haben kann
      (z. B. MQTT-Subscribe ohne empfangene Message,
      Modbus-Register noch ungelesen).
    - `write(target, command) -> None`: schreibt das Command
      auf das Target (Publish / Register-Write / Node-Write).

    Konkrete Methoden-Signaturen (Multi-Target-Read,
    Subscribe-Pattern, Batched-Write) werden in
    Welle-2-Adapter-ADR geschaerft. Welle-1-Code liefert
    nur den Protocol-Vertrag + Welle-2-Adapter setzen den
    konkreten Profil-Vertrag.

    Adapter-Verantwortung (Welle 2+, ADR 0030 §4):

    1. **Sync-Surface**: alle Methoden sind sync; async-
       Stacks marshalen intern.
    2. **Reconnect-Logik**: `start()` ist Connect/Subscribe,
       `read()`/`write()` muessen Reconnect bei Verbindungs-
       Verlust transparent versuchen (Retry-Backoff).
    3. **Stateless-Snapshot**: kein `protocol_ports`-Sub-
       Snapshot-Slot; Reconnect-State ist volatile.
    4. **Lifecycle-Idempotenz**: `start()` darf nicht
       mehrfach connecten; `stop()` darf nach erfolglosem
       `start()` als No-op aufgerufen werden.
    5. **Cross-Cutting-Doku** (Lastenheft Z. 1161-1163):
       Modul-README/Docstring dokumentiert den Test-/
       Simulationscharakter; keine Produktivsteuerungs-
       Versprechen.
    """

    def start(self) -> None:
        """Connect / Subscribe. Wird vom Caller vor dem
        ersten Tick gerufen.

        Exception-Vertrag: `DeviceProtocolPortStartError`
        (oder Adapter-spezifische Subclass) bei Connect-
        Fehler. `TickLoop.start_protocol_ports()` macht
        Best-Effort-Cleanup in LIFO und propagiert die
        Original-Exception (ADR 0030 §2.2).
        """
        ...

    def stop(self) -> None:
        """Disconnect / Unsubscribe. Wird vom Caller nach
        dem letzten Tick (oder im `try/finally`-Fall bei
        Exception) gerufen.

        Idempotenz-Vertrag: `stop()` darf nach erfolglosem
        oder nicht-erfolgtem `start()` als No-op aufgerufen
        werden, ohne zu werfen.

        Exception-Vertrag: `DeviceProtocolPortStopError`
        (oder Adapter-spezifische Subclass) bei harten
        Disconnect-Fehlern. `TickLoop.stop_protocol_ports()`
        propagiert die Exception aus dem letzten Stop —
        Welle-2-Schaerfung kann ein
        `BaseExceptionGroup`-Pattern einfuehren, falls
        mehrere Stops fehlschlagen.
        """
        ...

    def read(self, target: str) -> TelemetryPoint | None:
        """Liest den aktuellen Wert fuer `target`.

        Gibt `None` zurueck, wenn der Adapter aktuell keinen
        Wert hat (z. B. MQTT-Subscribe ohne empfangene
        Message, Modbus-Register noch ungelesen). Wirft
        `DeviceProtocolPortUnknownTargetError`, wenn das
        Target nicht im Adapter-Profil registriert ist.
        """
        ...

    def write(self, target: str, command: Command) -> None:
        """Schreibt `command` auf `target` (Publish /
        Register-Write / Node-Write).

        Wirft `DeviceProtocolPortUnknownTargetError`, wenn
        das Target nicht im Adapter-Profil registriert ist.
        Wirft `DeviceProtocolPortWriteError` bei
        Schreibfehlern.
        """
        ...


# ---------------------------------------------------------------------------
# Error-Hierarchie (ADR 0030 §2.1 + §4)
# ---------------------------------------------------------------------------


class DeviceProtocolPortError(GridGymError):
    """Wurzel der `DeviceProtocolPort`-Vertragsverletzungen
    (M4 Welle 1, ADR 0030).

    Adapter werfen typed Subclasses (z. B.
    `DeviceProtocolPortStartError` bei Connect-Fehlern,
    `DeviceProtocolPortUnknownTargetError` bei
    nicht-registrierten Targets). Welle-1-Surface ist
    bewusst minimal; Welle 2+ kann pro Adapter spezifische
    Subclasses einfuehren (Pattern analog
    `OtlpAdapterConfigError`-Familie aus M3-Welle-6).
    """


class DeviceProtocolPortStartError(DeviceProtocolPortError):
    """`start()` ist fehlgeschlagen — Adapter konnte nicht
    connecten / subscriben.

    Wird im Caller-Pfad
    (`TickLoop.start_protocol_ports()`) gefangen, fuehrt
    Best-Effort-Cleanup in LIFO aus und propagiert dann die
    Original-Exception (ADR 0030 §2.2 Partial-Start-Failure-
    Vertrag).
    """


class DeviceProtocolPortStopError(DeviceProtocolPortError):
    """`stop()` ist fehlgeschlagen — Adapter konnte nicht
    sauber disconnecten / unsubscriben.

    Idempotenz-Vertrag (ADR 0030 §2.1): wenn `stop()` nach
    erfolglosem oder nicht-erfolgtem `start()` aufgerufen
    wird, soll es No-op sein — `DeviceProtocolPortStopError`
    ist nur fuer **harte** Disconnect-Probleme reserviert
    (z. B. Netzwerk-Reset bricht waehrend Abbau).
    """


class DeviceProtocolPortReadError(DeviceProtocolPortError):
    """`read(target)` ist fehlgeschlagen — Adapter konnte
    den Wert nicht lesen oder nicht auf `TelemetryPoint`
    mappen.

    `None`-Rueckgabe ist kein Fehler, sondern
    „aktuell-kein-Wert" (z. B. MQTT-Subscribe noch ohne
    Message). Subclasses fuer Mapping-Fehler vs.
    Verbindungs-Fehler folgen in Welle 2+.
    """


class DeviceProtocolPortWriteError(DeviceProtocolPortError):
    """`write(target, command)` ist fehlgeschlagen —
    Adapter konnte das Command nicht senden.

    Subclasses fuer Verbindungs-Fehler vs. Validation-Fehler
    folgen in Welle 2+.
    """


class DeviceProtocolPortUnknownTargetError(DeviceProtocolPortError):
    """`target` ist nicht im Adapter-Profil registriert.

    Pre-Dispatch-Pflichtcheck im Adapter — sowohl `read()`
    als auch `write()` werfen diese typed Exception, bevor
    sie ueberhaupt den externen Aufruf machen. Pattern
    analog `ScenarioUnknownDeviceTypeError` (ADR 0021
    §2.5).
    """

    def __init__(self, target: str, *, available_targets: tuple[str, ...] = ()) -> None:
        if available_targets:
            available = ", ".join(repr(t) for t in available_targets)
            message = (
                f"DeviceProtocolPort: target {target!r} ist nicht im "
                f"Adapter-Profil registriert (verfuegbar: {available})"
            )
        else:
            message = (
                f"DeviceProtocolPort: target {target!r} ist nicht im Adapter-Profil registriert"
            )
        super().__init__(message)
        self.target: str = target
        self.available_targets: tuple[str, ...] = available_targets
