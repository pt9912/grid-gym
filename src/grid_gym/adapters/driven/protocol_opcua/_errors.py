"""OPC-UA-Adapter-spezifische Subclasses der
`DeviceProtocolPort*Error`-Familie (M4 Welle 4, ADR 0030 §4 +
ADR 0033).

Pattern analog `protocol_modbus/_errors.py` aus M4-Welle-3 (Slice-031-
Folge): Catch-All-Basen unter `DeviceProtocolPortError` plus
operation-spezifische Subclasses, die zusaetzlich von
`DeviceProtocolPortReadError`/`DeviceProtocolPortWriteError`
erben. Damit ist ein Caller-`except DeviceProtocolPortWriteError`-
Pfad sauber catchable.

Jede Subklasse traegt strukturierte Konstruktor-Parameter und baut
die Message in `__init__` (TRY003-Konvention).
"""

from __future__ import annotations

from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPortError,
    DeviceProtocolPortReadError,
    DeviceProtocolPortStartError,
    DeviceProtocolPortStopError,
    DeviceProtocolPortWriteError,
)


class OpcuaPortConnectError(DeviceProtocolPortStartError):
    """`asyncua.Client.connect()` ist gescheitert (Server nicht
    erreichbar, Handshake-Fehler, Timeout)."""

    def __init__(self, endpoint_url: str, reason: str) -> None:
        super().__init__(f"OPC-UA-Connect zu {endpoint_url} fehlgeschlagen: {reason}")
        self.endpoint_url: str = endpoint_url


class OpcuaPortDisconnectError(DeviceProtocolPortStopError):
    """`asyncua.Client.disconnect()` hat einen Fehler geworfen."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"OPC-UA-Disconnect fehlgeschlagen: {reason}")


class OpcuaPortNotStartedError(DeviceProtocolPortError):
    """`read()`/`write()` wurde aufgerufen, bevor `start()`
    erfolgreich war.

    Operation-spezifische Subclasses haengen am passenden
    `DeviceProtocolPortReadError`/`DeviceProtocolPortWriteError`.
    Diese Basisklasse bleibt als stabiler Catch-All fuer beide Pfade
    erhalten.
    """

    def __init__(self, target: str, operation: str) -> None:
        super().__init__(
            f"Target {target!r}: Client nicht gestartet — vor "
            f"{operation}() muss start() erfolgreich gelaufen sein."
        )
        self.target: str = target
        self.operation: str = operation


class OpcuaPortReadNotStartedError(OpcuaPortNotStartedError, DeviceProtocolPortReadError):
    """`read()` wurde vor erfolgreichem `start()` aufgerufen."""

    def __init__(self, target: str) -> None:
        super().__init__(target, "read")


class OpcuaPortWriteNotStartedError(OpcuaPortNotStartedError, DeviceProtocolPortWriteError):
    """`write()` wurde vor erfolgreichem `start()` aufgerufen."""

    def __init__(self, target: str) -> None:
        super().__init__(target, "write")


class OpcuaPortReadFailedError(DeviceProtocolPortReadError):
    """asyncua-Read-Call hat einen Server-Fehler geliefert (z. B.
    BadNotConnected, BadSessionClosed) oder eine Codec-Fehler-
    Translation ist gescheitert."""

    def __init__(self, target: str, node_id: str, reason: str) -> None:
        super().__init__(
            f"OPC-UA-Read fuer target={target!r} (node_id={node_id!r}) fehlgeschlagen: {reason}"
        )
        self.target: str = target
        self.node_id: str = node_id


class OpcuaPortWriteFailedError(DeviceProtocolPortWriteError):
    """asyncua-Write-Call hat einen Server-Fehler geliefert oder eine
    Codec-Encode-Translation ist gescheitert."""

    def __init__(self, target: str, node_id: str, reason: str) -> None:
        super().__init__(
            f"OPC-UA-Write fuer target={target!r} (node_id={node_id!r}) fehlgeschlagen: {reason}"
        )
        self.target: str = target
        self.node_id: str = node_id


class OpcuaPortMissingCommandPayloadError(DeviceProtocolPortWriteError):
    """`Command.payload` enthaelt keinen `value`-Key fuer OPC-UA-Write."""

    def __init__(self, target: str) -> None:
        super().__init__(
            f"Target {target!r}: Command.payload braucht einen "
            "`value`-Key fuer OPC-UA-Write (ADR 0033 §2.4)."
        )
        self.target: str = target


class OpcuaPortAccessMismatchError(DeviceProtocolPortError):
    """`read()` auf einem `access="write"`-Target oder umgekehrt.

    Operation-spezifische Subclasses haengen am passenden
    `DeviceProtocolPortReadError`/`DeviceProtocolPortWriteError`.
    Diese Basisklasse bleibt als stabiler Catch-All fuer beide Pfade
    erhalten.
    """

    def __init__(self, target: str, configured: str, attempted: str) -> None:
        super().__init__(
            f"Target {target!r}: configured access={configured!r}, aber {attempted}() versucht."
        )
        self.target: str = target
        self.configured: str = configured
        self.attempted: str = attempted


class OpcuaPortReadAccessMismatchError(OpcuaPortAccessMismatchError, DeviceProtocolPortReadError):
    """`read()` wurde auf einem nicht lesbaren Target versucht."""

    def __init__(self, target: str, configured: str) -> None:
        super().__init__(target, configured, "read")


class OpcuaPortWriteAccessMismatchError(OpcuaPortAccessMismatchError, DeviceProtocolPortWriteError):
    """`write()` wurde auf einem nicht schreibbaren Target versucht."""

    def __init__(self, target: str, configured: str) -> None:
        super().__init__(target, configured, "write")
