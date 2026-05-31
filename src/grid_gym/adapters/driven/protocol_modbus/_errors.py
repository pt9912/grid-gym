"""Modbus-Adapter-spezifische Subclasses der
`DeviceProtocolPort*Error`-Familie (M4 Welle 3, ADR 0030 §4 +
ADR 0032).

Pattern analog `protocol_mqtt/_errors.py` aus M4-Welle-2: ADR 0030 §4
erlaubt Welle-2+-Adaptern, pro Adapter spezifische Subclasses
unterhalb der `DeviceProtocolPort*Error`-Wurzel einzufuehren. Jede
Subklasse traegt strukturierte Konstruktor-Parameter und baut die
Message in `__init__` — das loest `TRY003` per Codebase-Konvention.
"""

from __future__ import annotations

from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPortError,
    DeviceProtocolPortReadError,
    DeviceProtocolPortStartError,
    DeviceProtocolPortStopError,
    DeviceProtocolPortWriteError,
)


class ModbusPortConnectError(DeviceProtocolPortStartError):
    """`ModbusTcpClient.connect()` ist auf OS-Ebene gescheitert
    (z. B. Server nicht erreichbar, Connect-Timeout)."""

    def __init__(self, host: str, port: int, reason: str) -> None:
        super().__init__(f"Modbus-TCP-Connect zu {host}:{port} fehlgeschlagen: {reason}")
        self.host: str = host
        self.port: int = port


class ModbusPortDisconnectError(DeviceProtocolPortStopError):
    """`ModbusTcpClient.close()` hat einen OS-Fehler geworfen."""

    def __init__(self, cause: OSError) -> None:
        super().__init__(f"Modbus-TCP-Disconnect fehlgeschlagen: {cause}")


class ModbusPortNotStartedError(DeviceProtocolPortError):
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


class ModbusPortReadNotStartedError(ModbusPortNotStartedError, DeviceProtocolPortReadError):
    """`read()` wurde vor erfolgreichem `start()` aufgerufen."""

    def __init__(self, target: str) -> None:
        super().__init__(target, "read")


class ModbusPortWriteNotStartedError(ModbusPortNotStartedError, DeviceProtocolPortWriteError):
    """`write()` wurde vor erfolgreichem `start()` aufgerufen."""

    def __init__(self, target: str) -> None:
        super().__init__(target, "write")


class ModbusPortReadFailedError(DeviceProtocolPortReadError):
    """pymodbus-Read-Call hat einen Modbus-Server-Fehler geliefert
    (z. B. Slave-Exception-Response) oder ein OS-Error trat auf."""

    def __init__(self, target: str, address: int, reason: str) -> None:
        super().__init__(
            f"Modbus-Read fuer target={target!r} (address={address}) fehlgeschlagen: {reason}"
        )
        self.target: str = target
        self.address: int = address


class ModbusPortWriteFailedError(DeviceProtocolPortWriteError):
    """pymodbus-Write-Call hat einen Modbus-Server-Fehler geliefert
    oder ein OS-Error trat auf."""

    def __init__(self, target: str, address: int, reason: str) -> None:
        super().__init__(
            f"Modbus-Write fuer target={target!r} (address={address}) fehlgeschlagen: {reason}"
        )
        self.target: str = target
        self.address: int = address


class ModbusPortMissingCommandPayloadError(DeviceProtocolPortWriteError):
    """`Command.payload` enthaelt keinen `value`-Key fuer
    Modbus-Write."""

    def __init__(self, target: str) -> None:
        super().__init__(
            f"Target {target!r}: Command.payload braucht einen "
            "`value`-Key fuer Modbus-Write (ADR 0032 §2.4 "
            "Function-Code-Mapping)."
        )
        self.target: str = target


class ModbusPortAccessMismatchError(DeviceProtocolPortError):
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


class ModbusPortReadAccessMismatchError(ModbusPortAccessMismatchError, DeviceProtocolPortReadError):
    """`read()` wurde auf einem nicht lesbaren Target versucht."""

    def __init__(self, target: str, configured: str) -> None:
        super().__init__(target, configured, "read")


class ModbusPortWriteAccessMismatchError(
    ModbusPortAccessMismatchError, DeviceProtocolPortWriteError
):
    """`write()` wurde auf einem nicht schreibbaren Target versucht."""

    def __init__(self, target: str, configured: str) -> None:
        super().__init__(target, configured, "write")
