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


class ModbusServerConfigInvalidWriteAddressError(ModbusServerConfigError):
    """Eine `WritableRegisterMapping.address` liegt ausserhalb `[0, 65534]` (das
    zweite `float32`-Register muss noch in den 16-bit-Adressraum passen)."""

    def __init__(self, target_device_id: str, command_type: str, address: int) -> None:
        super().__init__(
            f"ModbusServerConfig.write_map: address={address} fuer "
            f"({target_device_id}, {command_type}) ausserhalb [0, {_MAX_MAPPING_ADDRESS}]."
        )
        self.target_device_id: str = target_device_id
        self.command_type: str = command_type
        self.address: int = address


class ModbusServerConfigEmptyWriteFieldError(ModbusServerConfigError):
    """`WritableRegisterMapping.target_device_id`/`command_type` ist leer."""

    def __init__(self, field_name: str) -> None:
        super().__init__(f"ModbusServerConfig.write_map: {field_name} darf nicht leer sein.")
        self.field_name: str = field_name


class ModbusServerConfigRegisterOverlapError(ModbusServerConfigError):
    """Zwei Register-Mappings (Read und/oder Write) belegen dieselbe Adresse.

    Jeder `float32` belegt 2 aufeinanderfolgende Register; **jede** Holding-Adresse
    hat genau eine Rolle — entweder ein Messwert (`register_map`, Read) oder ein
    Sollwert (`write_map`, Inbound-Write). Read- und Write-Fenster duerfen sich
    darum weder untereinander noch gegenseitig ueberlappen."""

    def __init__(self, address: int) -> None:
        super().__init__(
            f"ModbusServerConfig: Register-Adresse {address} ist doppelt belegt "
            "(jedes float32 belegt 2 aufeinanderfolgende Register; jede Adresse ist "
            "entweder Read-Messwert oder Write-Sollwert, nie beides)."
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
class WritableRegisterMapping:
    """Ein **beschreibbares** Holding-Register-Fenster (Inbound-Write→`Command`,
    ADR 0076 §2.1).

    `address` ist das erste von **zwei** Registern (`float32`, Big-Endian). Ein
    Master-Write an dieses Fenster dekodiert den `float32` zu einem `Decimal` und
    stellt `Command(type=command_type, payload={"value": Decimal})` an
    `target_device_id` zu (Gegenrichtung zum lesenden `RegisterMapping`). `command_
    type` ist der fachliche Kommando-Typ des Zielgeraets (z. B. `"set_power_kw"`),
    **nicht** ein Metrik-Name — Mess- und Sollwert sind getrennte Register.
    """

    address: int
    target_device_id: str
    command_type: str


@dataclass(frozen=True, slots=True)
class ModbusServerConfig:
    """Modbus-Server-Profil (Field-Server Pull-Seite).

    `register_map` = **Read**-Messwerte (Holding-Register, `float32`).
    `write_map` = optionale **Inbound-Write**-Sollwerte (ADR 0076); leer (Default)
    → reines Read-Serving, byte-identisch/pin-neutral. Jede Holding-Adresse hat
    genau eine Rolle (Read **oder** Write, nie beides).

    Konstruktor validiert fail-fast (typed `ModbusServerConfigError`-Subclass).
    """

    bind_host: str
    bind_port: int
    register_map: tuple[RegisterMapping, ...]
    unit_id: int = 1
    write_map: tuple[WritableRegisterMapping, ...] = ()

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
        self._validate_write_map()
        self._validate_no_overlap()

    def _validate_addresses(self) -> None:
        for mapping in self.register_map:
            if not (0 <= mapping.address <= _MAX_MAPPING_ADDRESS):
                raise ModbusServerConfigInvalidAddressError(
                    mapping.device_id, mapping.metric, mapping.address
                )

    def _validate_write_map(self) -> None:
        for mapping in self.write_map:
            if not mapping.target_device_id:
                raise ModbusServerConfigEmptyWriteFieldError("target_device_id")
            if not mapping.command_type:
                raise ModbusServerConfigEmptyWriteFieldError("command_type")
            if not (0 <= mapping.address <= _MAX_MAPPING_ADDRESS):
                raise ModbusServerConfigInvalidWriteAddressError(
                    mapping.target_device_id, mapping.command_type, mapping.address
                )

    def _validate_no_overlap(self) -> None:
        # Read- und Write-Fenster teilen sich den Holding-Adressraum; jede Adresse
        # ist entweder Messwert oder Sollwert. Ein gemeinsamer `occupied`-Set faengt
        # Read/Read-, Write/Write- **und** Read/Write-Kollisionen in einem Durchlauf.
        occupied: set[int] = set()
        addresses = [mapping.address for mapping in self.register_map]
        addresses += [mapping.address for mapping in self.write_map]
        for address in addresses:
            for offset in range(_FLOAT32_REGISTERS):
                occupied_address = address + offset
                if occupied_address in occupied:
                    raise ModbusServerConfigRegisterOverlapError(occupied_address)
                occupied.add(occupied_address)
