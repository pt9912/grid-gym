"""DNP3-Adapter-spezifische Subclasses der
`DeviceProtocolPort*Error`-Familie (M4 Welle 5a, ADR 0030 §4 +
ADR 0034).

Pattern analog `protocol_modbus/_errors.py` aus M4-Welle-3 (Slice-031-
Folge) und `protocol_opcua/_errors.py` aus M4-Welle-4 (Slice-032-
Folge): Catch-All-Basen unter `DeviceProtocolPortError` plus
operation-spezifische Subclasses, die zusaetzlich von
`DeviceProtocolPortReadError`/`DeviceProtocolPortWriteError`
erben. Damit ist ein Caller-`except DeviceProtocolPortReadError`-
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


class Dnp3PortConnectError(DeviceProtocolPortStartError):
    """`nfm-dnp3.DNP3Master.open()` ist gescheitert (Server nicht
    erreichbar, Handshake-Fehler, Timeout)."""

    def __init__(self, host: str, port: int, reason: str) -> None:
        super().__init__(f"DNP3-Connect zu {host}:{port} fehlgeschlagen: {reason}")
        self.host: str = host
        self.port: int = port


class Dnp3PortDisconnectError(DeviceProtocolPortStopError):
    """`nfm-dnp3.DNP3Master.close()` hat einen Fehler geworfen."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"DNP3-Disconnect fehlgeschlagen: {reason}")


class Dnp3PortNotStartedError(DeviceProtocolPortError):
    """`read()`/`write()` wurde aufgerufen, bevor `start()`
    erfolgreich war.

    Operation-spezifische Subclasses haengen am passenden
    `DeviceProtocolPortReadError`/`DeviceProtocolPortWriteError`.
    Diese Basisklasse bleibt als stabiler Catch-All fuer beide Pfade
    erhalten.
    """

    def __init__(self, target: str, operation: str) -> None:
        super().__init__(
            f"Target {target!r}: DNP3-Master nicht gestartet — vor "
            f"{operation}() muss start() erfolgreich gelaufen sein."
        )
        self.target: str = target
        self.operation: str = operation


class Dnp3PortReadNotStartedError(Dnp3PortNotStartedError, DeviceProtocolPortReadError):
    """`read()` wurde vor erfolgreichem `start()` aufgerufen."""

    def __init__(self, target: str) -> None:
        super().__init__(target, "read")


class Dnp3PortWriteNotStartedError(Dnp3PortNotStartedError, DeviceProtocolPortWriteError):
    """`write()` wurde vor erfolgreichem `start()` aufgerufen."""

    def __init__(self, target: str) -> None:
        super().__init__(target, "write")


class Dnp3PortReadFailedError(DeviceProtocolPortReadError):
    """`nfm-dnp3.DNP3Master.read_class(0)` hat einen Server-Fehler
    geliefert (Communication / CRC / Protocol / Timeout) oder das
    konfigurierte Point ist nicht im Poll-Resultat enthalten."""

    def __init__(self, target: str, group: int, variation: int, index: int, reason: str) -> None:
        super().__init__(
            f"DNP3-Read fuer target={target!r} (group={group}, variation={variation}, "
            f"index={index}) fehlgeschlagen: {reason}"
        )
        self.target: str = target
        self.group: int = group
        self.variation: int = variation
        self.index: int = index


class Dnp3PortWriteFailedError(DeviceProtocolPortWriteError):
    """`nfm-dnp3.DNP3Master`-Write-Call hat einen Server-Fehler
    geliefert.

    Welle-5a-Minimum: Write-Pfad ist **nicht** produktiv (siehe
    ADR 0034 §2.1 + §4 Konsequenzen). Diese Klasse existiert fuer
    Welle-6-Schaerfung; Welle 5a wirft sie nur im
    `Access-Mismatch`-Pfad.
    """

    def __init__(self, target: str, group: int, variation: int, index: int, reason: str) -> None:
        super().__init__(
            f"DNP3-Write fuer target={target!r} (group={group}, variation={variation}, "
            f"index={index}) fehlgeschlagen: {reason}"
        )
        self.target: str = target
        self.group: int = group
        self.variation: int = variation
        self.index: int = index


class Dnp3PortAccessMismatchError(DeviceProtocolPortError):
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


class Dnp3PortReadAccessMismatchError(Dnp3PortAccessMismatchError, DeviceProtocolPortReadError):
    """`read()` wurde auf einem nicht lesbaren Target versucht."""

    def __init__(self, target: str, configured: str) -> None:
        super().__init__(target, configured, "read")


class Dnp3PortWriteAccessMismatchError(Dnp3PortAccessMismatchError, DeviceProtocolPortWriteError):
    """`write()` wurde auf einem nicht schreibbaren Target versucht."""

    def __init__(self, target: str, configured: str) -> None:
        super().__init__(target, configured, "write")


class Dnp3PortWriteNotImplementedError(DeviceProtocolPortWriteError):
    """Welle-5a-Adapter ist Read-only — `write()` mit
    `access="write"`-Target ist konfigurations-konsistent, aber die
    Welle-5a-Implementierung lehnt es konsequent ab (ADR 0034
    Anti-Scope; Welle-6 fuehrt Write-Pfad ein)."""

    def __init__(self, target: str) -> None:
        super().__init__(
            f"Target {target!r}: DNP3-Write-Pfad ist Welle-5a-Anti-Scope "
            "(siehe ADR 0034 §2.1; Welle-6-Schaerfung)."
        )
        self.target: str = target


class Dnp3PortPointNotInPollResultError(Dnp3PortReadFailedError):
    """`read_class(0)` ist erfolgreich gelaufen, aber das
    konfigurierte Point (group/variation/index) ist nicht im
    Poll-Resultat enthalten (z. B. Server-Misconfig oder Outstation
    hat das Point nicht freigegeben)."""

    def __init__(self, target: str, group: int, variation: int, index: int) -> None:
        super().__init__(
            target,
            group,
            variation,
            index,
            "point nicht im Class-0-Poll-Resultat",
        )
