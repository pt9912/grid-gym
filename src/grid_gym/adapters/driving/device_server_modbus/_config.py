"""Konfiguration fuer den Modbus-Server-Adapter (Field-Server Pull-Seite,
ADR 0075 §2.1; Profil: `spec/protocol_profiles.md` „Server-Profile").

Simulation only — grid-gym als Modbus-TCP-**Server/Slave**, damit ein externes
EMS (System-under-Test) als Master die simulierten Geraetewerte **pollt**; keine
produktive Anlagensteuerung ([`GG-SAFE-007`], [`GG-NONGOAL-001`]); Nur-Sim-Netz.

`ModbusServerConfig` ist eine frozen-dataclass mit expliziter, deterministischer
**Register-Map** (`(device_id, metric)` → Start-Adresse; jeder Wert ist `float32`
= 2 aufeinanderfolgende Holding-Register). Der Konstruktor validiert fail-fast
(typed `ModbusServerConfigError`-Familie).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

_MIN_PORT: Final[int] = 1
_MAX_PORT: Final[int] = 65535
_MIN_UNIT_ID: Final[int] = 1
_MAX_UNIT_ID: Final[int] = 247
_FLOAT32_REGISTERS: Final[int] = 2
# Ein float32 belegt address..address+1; die hoechste zulaessige Start-Adresse
# ist damit 65534 (das zweite Register muss noch in den 16-bit-Adressraum passen).
_MAX_REGISTER_ADDRESS: Final[int] = 65535
_MAX_MAPPING_ADDRESS: Final[int] = _MAX_REGISTER_ADDRESS - (_FLOAT32_REGISTERS - 1)


class ModbusServerConfigError(ValueError):
    """Base-Klasse fuer `ModbusServerConfig`-Validation-Fehler."""


class ModbusServerConfigEmptyFieldError(ModbusServerConfigError):
    """String-Pflichtfeld ist leer."""

    def __init__(self, field_name: str) -> None:
        super().__init__(f"ModbusServerConfig.{field_name} darf nicht leer sein.")
        self.field_name: str = field_name


class ModbusServerConfigInvalidPortError(ModbusServerConfigError):
    """`bind_port` ausserhalb des TCP-Port-Bereichs."""

    def __init__(self, value: int) -> None:
        super().__init__(
            f"ModbusServerConfig.bind_port={value}: muss in [{_MIN_PORT}, {_MAX_PORT}] liegen."
        )
        self.value: int = value


class ModbusServerConfigInvalidUnitIdError(ModbusServerConfigError):
    """`unit_id` ausserhalb des zulaessigen Server-Slave-Bereichs (1..247).

    `0` ist die Modbus-Broadcast-Adresse; ein `SimDevice(id=0)` wuerde als
    Catch-all fuer **jede** gepollte Unit-ID antworten — als konkrete
    Slave-Adresse unzulaessig (Review-Fund C2)."""

    def __init__(self, value: int) -> None:
        super().__init__(
            f"ModbusServerConfig.unit_id={value}: muss in [{_MIN_UNIT_ID}, {_MAX_UNIT_ID}] liegen "
            "(0 = Broadcast, unzulaessig)."
        )
        self.value: int = value


class ModbusServerConfigInvalidAddressError(ModbusServerConfigError):
    """Eine `RegisterMapping.address` liegt ausserhalb `[0, 65534]` (das zweite
    `float32`-Register muss noch in den 16-bit-Adressraum passen)."""

    def __init__(self, device_id: str, metric: str, address: int) -> None:
        super().__init__(
            f"ModbusServerConfig.register_map: address={address} fuer "
            f"({device_id}, {metric}) ausserhalb [0, {_MAX_MAPPING_ADDRESS}]."
        )
        self.device_id: str = device_id
        self.metric: str = metric
        self.address: int = address


class ModbusServerConfigEmptyRegisterMapError(ModbusServerConfigError):
    """`register_map` ist leer; mindestens ein Eintrag noetig."""

    def __init__(self) -> None:
        super().__init__("ModbusServerConfig.register_map darf nicht leer sein.")


class ModbusServerConfigRegisterOverlapError(ModbusServerConfigError):
    """Zwei Register-Mappings ueberlappen (jeder `float32` belegt 2 Register)."""

    def __init__(self, address: int) -> None:
        super().__init__(
            f"ModbusServerConfig.register_map: Register-Adresse {address} ist doppelt "
            "belegt (jedes float32 belegt 2 aufeinanderfolgende Register)."
        )
        self.address: int = address


@dataclass(frozen=True, slots=True)
class RegisterMapping:
    """Eine `(device_id, metric)` → Holding-Register-Adresse-Zuordnung.

    `address` ist das erste von **zwei** Registern (`float32`, Big-Endian).
    """

    device_id: str
    metric: str
    address: int


@dataclass(frozen=True, slots=True)
class ModbusServerConfig:
    """Modbus-Server-Profil (Field-Server Pull-Seite, Read-Serving).

    Konstruktor validiert fail-fast (typed `ModbusServerConfigError`-Subclass).
    """

    bind_host: str
    bind_port: int
    register_map: tuple[RegisterMapping, ...]
    unit_id: int = 1

    def __post_init__(self) -> None:
        if not self.bind_host:
            raise ModbusServerConfigEmptyFieldError("bind_host")
        if not (_MIN_PORT <= self.bind_port <= _MAX_PORT):
            raise ModbusServerConfigInvalidPortError(self.bind_port)
        if not (_MIN_UNIT_ID <= self.unit_id <= _MAX_UNIT_ID):
            raise ModbusServerConfigInvalidUnitIdError(self.unit_id)
        if not self.register_map:
            raise ModbusServerConfigEmptyRegisterMapError
        self._validate_addresses()
        self._validate_no_overlap()

    def _validate_addresses(self) -> None:
        for mapping in self.register_map:
            if not (0 <= mapping.address <= _MAX_MAPPING_ADDRESS):
                raise ModbusServerConfigInvalidAddressError(
                    mapping.device_id, mapping.metric, mapping.address
                )

    def _validate_no_overlap(self) -> None:
        occupied: set[int] = set()
        for mapping in self.register_map:
            for offset in range(_FLOAT32_REGISTERS):
                address = mapping.address + offset
                if address in occupied:
                    raise ModbusServerConfigRegisterOverlapError(address)
                occupied.add(address)
