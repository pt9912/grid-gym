# SPDX-License-Identifier: GPL-3.0-only
"""IEC-61850-Adapter-spezifische Subclasses der
`DeviceProtocolPort*Error`-Familie (M4 Welle 5b, ADR 0030 §4 +
ADR 0035).

Pattern analog `protocol_modbus/_errors.py` (M4-Welle-3 Slice-031),
`protocol_opcua/_errors.py` (M4-Welle-4 Slice-032) und
`protocol_dnp3/_errors.py` (M4-Welle-5a): Catch-All-Basen unter
`DeviceProtocolPortError` plus operation-spezifische Subclasses,
die zusaetzlich von `DeviceProtocolPortReadError`/
`DeviceProtocolPortWriteError` erben. Damit ist ein Caller-`except
DeviceProtocolPortReadError`-Pfad sauber catchable.

NEU gegenueber Welle 5a: `Iec61850PortLibraryNotInstalledError`
fuer Decision I-f (Lizenz-Boundary; `pyiec61850-ng` ist optional
Extra via `pip install grid-gym[iec61850]`).

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


class Iec61850PortLibraryNotInstalledError(DeviceProtocolPortStartError):
    """`import pyiec61850` ist gescheitert.

    Welle-5b-Decision-I-f stellt `pyiec61850-ng` als optionales
    Extra (`pip install grid-gym[iec61850]`) bereit. Wenn der
    Welle-1-`build_protocol_ports`-Hook fuer `type: iec61850`
    ohne installiertes Extra getriggert wird, faengt
    `protocol_iec61850/__init__.py` den `ImportError` und wirft
    diesen typed Error mit Install-Hinweis.
    """

    def __init__(self) -> None:
        super().__init__(
            "pyiec61850-ng nicht installiert — IEC-61850-Adapter benoetigt "
            "das optionale Extra. Install: pip install grid-gym[iec61850]"
        )


class Iec61850PortConnectError(DeviceProtocolPortStartError):
    """`pyiec61850.mms.MMSClient.connect()` ist gescheitert (Server
    nicht erreichbar, Handshake-Fehler, Timeout)."""

    def __init__(self, host: str, port: int, reason: str) -> None:
        super().__init__(f"IEC-61850-Connect zu {host}:{port} fehlgeschlagen: {reason}")
        self.host: str = host
        self.port: int = port


class Iec61850PortDisconnectError(DeviceProtocolPortStopError):
    """`pyiec61850.mms.MMSClient.disconnect()` hat einen Fehler geworfen."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"IEC-61850-Disconnect fehlgeschlagen: {reason}")


class Iec61850PortNotStartedError(DeviceProtocolPortError):
    """`read()`/`write()` wurde aufgerufen, bevor `start()`
    erfolgreich war.

    Operation-spezifische Subclasses haengen am passenden
    `DeviceProtocolPortReadError`/`DeviceProtocolPortWriteError`.
    Diese Basisklasse bleibt als stabiler Catch-All fuer beide
    Pfade erhalten.
    """

    def __init__(self, target: str, operation: str) -> None:
        super().__init__(
            f"Target {target!r}: IEC-61850-Client nicht gestartet — vor "
            f"{operation}() muss start() erfolgreich gelaufen sein."
        )
        self.target: str = target
        self.operation: str = operation


class Iec61850PortReadNotStartedError(Iec61850PortNotStartedError, DeviceProtocolPortReadError):
    """`read()` wurde vor erfolgreichem `start()` aufgerufen."""

    def __init__(self, target: str) -> None:
        super().__init__(target, "read")


class Iec61850PortWriteNotStartedError(Iec61850PortNotStartedError, DeviceProtocolPortWriteError):
    """`write()` wurde vor erfolgreichem `start()` aufgerufen."""

    def __init__(self, target: str) -> None:
        super().__init__(target, "write")


class Iec61850PortReadFailedError(DeviceProtocolPortReadError):
    """`pyiec61850.mms.MMSClient.read_value()` hat einen Fehler
    geworfen (Library-`ReadError`/`MMSError`-Famille)."""

    def __init__(self, target: str, reference: str, fc: str, reason: str) -> None:
        super().__init__(
            f"IEC-61850-Read fuer target={target!r} "
            f"(reference={reference!r}, fc={fc!r}) fehlgeschlagen: {reason}"
        )
        self.target: str = target
        self.reference: str = reference
        self.fc: str = fc


class Iec61850PortReadConnectionLostError(Iec61850PortReadFailedError):
    """Library hat `NotConnectedError` waehrend `read_value()`
    geworfen, **nachdem** `start()` erfolgreich gelaufen war —
    Session-Drop mid-flight (Server-Reboot, TCP-RST, Network-
    Partition).

    Semantisch verschieden zu `Iec61850PortReadNotStartedError`
    (Caller hat `start()` nie aufgerufen): der Read war legal,
    die Session ist mitten in der Simulation kollabiert. Caller-
    Recovery-Logik kann z. B. eine Backoff-Reconnect-Strategie
    ziehen statt `start()` neu aufzurufen (was bei einem nicht-
    gestarteten Adapter sinnvoll waere, aber nicht bei mid-flight-
    Drop).
    """

    def __init__(self, target: str, reference: str, fc: str) -> None:
        super().__init__(
            target,
            reference,
            fc,
            "connection lost mid-session (NotConnectedError post-start)",
        )


class Iec61850PortPointNotFoundError(Iec61850PortReadFailedError):
    """`read_value()` ist mit einer Object-Reference-Not-Found-
    Message gescheitert.

    pyiec61850-ng hat **kein** separates `ObjectReferenceError`;
    der Adapter mappt `ReadError`-Library-Messages, die auf einen
    fehlenden Object-Reference hinweisen, auf diese Subklasse.
    Fallback bleibt `Iec61850PortReadFailedError`.
    """

    def __init__(self, target: str, reference: str, fc: str) -> None:
        super().__init__(
            target,
            reference,
            fc,
            "object reference not found in IEC-61850 model",
        )


class Iec61850PortWriteFailedError(DeviceProtocolPortWriteError):
    """`pyiec61850.mms.MMSClient.write_value()` hat einen Fehler
    geworfen.

    Welle-5b-Minimum: Write-Pfad ist **nicht** produktiv (siehe
    ADR 0035 §2.4 + §4 Konsequenzen). Diese Klasse existiert fuer
    Welle-6-Schaerfung; Welle 5b wirft sie nur im Access-Mismatch-
    Pfad ueber `Iec61850PortWriteAccessMismatchError` (separates
    Subclass).
    """

    def __init__(self, target: str, reference: str, fc: str, reason: str) -> None:
        super().__init__(
            f"IEC-61850-Write fuer target={target!r} "
            f"(reference={reference!r}, fc={fc!r}) fehlgeschlagen: {reason}"
        )
        self.target: str = target
        self.reference: str = reference
        self.fc: str = fc


class Iec61850PortAccessMismatchError(DeviceProtocolPortError):
    """`read()` auf einem `access="write"`-Target oder umgekehrt.

    Operation-spezifische Subclasses haengen am passenden
    `DeviceProtocolPortReadError`/`DeviceProtocolPortWriteError`.
    Diese Basisklasse bleibt als stabiler Catch-All fuer beide
    Pfade erhalten.
    """

    def __init__(self, target: str, configured: str, attempted: str) -> None:
        super().__init__(
            f"Target {target!r}: configured access={configured!r}, aber {attempted}() versucht."
        )
        self.target: str = target
        self.configured: str = configured
        self.attempted: str = attempted


class Iec61850PortReadAccessMismatchError(
    Iec61850PortAccessMismatchError, DeviceProtocolPortReadError
):
    """`read()` wurde auf einem nicht lesbaren Target versucht."""

    def __init__(self, target: str, configured: str) -> None:
        super().__init__(target, configured, "read")


class Iec61850PortWriteAccessMismatchError(
    Iec61850PortAccessMismatchError, DeviceProtocolPortWriteError
):
    """`write()` wurde auf einem nicht schreibbaren Target versucht."""

    def __init__(self, target: str, configured: str) -> None:
        super().__init__(target, configured, "write")


class Iec61850PortWriteNotImplementedError(DeviceProtocolPortWriteError):
    """Welle-5b-Adapter ist Read-only — `write()` auf einem
    `access="write"`-Target ist konfigurations-konsistent, aber
    die Welle-5b-Implementierung lehnt es konsequent ab (ADR 0035
    Anti-Scope; Welle-6 fuehrt Write-Pfad ein)."""

    def __init__(self, target: str) -> None:
        super().__init__(
            f"Target {target!r}: IEC-61850-Write-Pfad ist Welle-5b-Anti-Scope "
            "(siehe ADR 0035 §2.4; Welle-6-Schaerfung)."
        )
        self.target: str = target


class Iec61850CodecError(DeviceProtocolPortError):
    """Wurzel der IEC-61850-Codec-Fehler (Datatype-Mismatch /
    Overflow / Decode-Fail)."""


class Iec61850CodecValueTypeError(Iec61850CodecError):
    """`decode_mms_value` hat einen unerwarteten Library-Value-Typ
    bekommen (z. B. `MmsValue type=15` Container statt Leaf-Wert)."""

    def __init__(self, reference: str, fc: str, expected_datatype: str, actual_repr: str) -> None:
        super().__init__(
            f"Codec-Decode fuer reference={reference!r} fc={fc!r}: "
            f"erwarteter datatype={expected_datatype!r}, "
            f"erhalten {actual_repr}"
        )
        self.reference: str = reference
        self.fc: str = fc
        self.expected_datatype: str = expected_datatype


class Iec61850CodecOverflowError(Iec61850CodecError):
    """`decode_mms_value` hat einen Overflow oder Out-of-Range-Fehler
    bei der Konvertierung in die Python-Native-Form gefangen
    (Pattern analog Welle-4-Slice-032-Codec-Overflow-Handling)."""

    def __init__(self, reference: str, datatype: str, raw_value: object, reason: str) -> None:
        super().__init__(
            f"Codec-Overflow fuer reference={reference!r} datatype={datatype!r}: "
            f"raw_value={raw_value!r}, reason={reason}"
        )
        self.reference: str = reference
        self.datatype: str = datatype
