"""Modbus-TCP-Adapter-Profile-Konfiguration (M4 Welle 3, ADR 0032 §2.1).

`ModbusProtocolPortConfig` ist eine frozen-dataclass mit dem inline-im-
`protocol_ports`-Block deklarierten Register-Schema (Decision M-a).
Pro `device_id` traegt `ModbusRegisterConfig` Address + Datatype +
Access (Decision M-b/M-d/M-e). Validation-Errors werfen typed Sub-
Exceptions analog `MqttConfigError`-Familie aus M4-Welle-2.

Welle-3-Felder (`ModbusProtocolPortConfig`):

- `host` — Modbus-TCP-Server-Hostname (Default-frei; Pflicht).
- `port` — TCP-Port (Default `502`; Modbus-TCP-Standard).
- `unit_id` — Parent-Slave-ID (Default `1`; per Register
  ueberschreibbar).
- `timeout_s` — Connect-/Read-/Write-Timeout in Sekunden
  (Default `5.0`).
- `registers` — Mapping `device_id` -> `ModbusRegisterConfig`
  (Decision M-a inline-Schema). Mindestens ein Eintrag noetig.

Welle-3-Felder (`ModbusRegisterConfig`):

- `address` — 0-basierte Register-Adresse (Modbus-Spec; Pflicht).
- `datatype` — `ModbusDatatype` Enum (Decision M-b: int16, uint16,
  int32, uint32, float32).
- `access` — `"read"` oder `"write"` (Pflicht).
- `byte_order` — `"big_endian"` (Default per Decision M-b) oder
  `"little_endian"`.
- `word_swap` — `False` (Default per Decision M-b) oder `True`
  (relevant nur fuer Multi-Register-Datatypes).
- `function_code` — `None` (Default per Decision M-d: FC03 fuer
  read, FC06/FC10 fuer write) oder explizit `{1, 2, 3, 4, 5, 6,
  15, 16}`. Welle 3 unterstuetzt nur `{3, 4, 6, 16}` (siehe
  `_ALLOWED_FUNCTION_CODES`).
- `unit_id` — `None` (Parent-Fallback) oder explizit
  `[1, 247]` (Modbus-Spec §4.1 Range; Decision M-e).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final, Literal


_DEFAULT_PORT: Final[int] = 502
_DEFAULT_UNIT_ID: Final[int] = 1
_DEFAULT_TIMEOUT_S: Final[float] = 5.0
_DEFAULT_BYTE_ORDER: Final[str] = "big_endian"
_DEFAULT_WORD_SWAP: Final[bool] = False
_MIN_PORT: Final[int] = 1
_MAX_PORT: Final[int] = 65535
_MIN_UNIT_ID: Final[int] = 1
_MAX_UNIT_ID: Final[int] = 247

# Modbus-Spec Function-Code-Konstanten (ADR 0032 §2.4).
_FC_READ_HOLDING_REGISTERS: Final[int] = 3
_FC_WRITE_SINGLE_REGISTER: Final[int] = 6
_FC_WRITE_MULTIPLE_REGISTERS: Final[int] = 16
_SINGLE_REGISTER: Final[int] = 1
_MAX_REGISTER_ADDRESS: Final[int] = 0xFFFF

# Welle-3-Allow-List fuer Function-Codes (ADR 0032 §2.4).
# Coil-Codes (1/2/5/15) bleiben Welle-6-Schaerfung.
_ALLOWED_FUNCTION_CODES: Final[frozenset[int]] = frozenset({3, 4, 6, 16})
_ALLOWED_BYTE_ORDERS: Final[frozenset[str]] = frozenset({"big_endian", "little_endian"})


class ModbusDatatype(StrEnum):
    """Erlaubte Datatypes in Welle 3 (ADR 0032 §2.2 Decision M-b).

    `int64`/`uint64`/`float64`/`string`/`bool-array` sind
    Welle-6-Schaerfungspfad (ADR 0011); nicht hier.
    """

    INT16 = "int16"
    UINT16 = "uint16"
    INT32 = "int32"
    UINT32 = "uint32"
    FLOAT32 = "float32"


# Wie viele 16-bit Modbus-Register braucht jeder Datatype?
_DATATYPE_REGISTER_COUNT: Final[Mapping[ModbusDatatype, int]] = MappingProxyType(
    {
        ModbusDatatype.INT16: 1,
        ModbusDatatype.UINT16: 1,
        ModbusDatatype.INT32: 2,
        ModbusDatatype.UINT32: 2,
        ModbusDatatype.FLOAT32: 2,
    }
)


def datatype_register_count(datatype: ModbusDatatype) -> int:
    """Liefert die Register-Anzahl fuer einen `ModbusDatatype`."""
    return _DATATYPE_REGISTER_COUNT[datatype]


class ModbusConfigError(ValueError):
    """Base-Klasse fuer `ModbusProtocolPortConfig`-Validation-Fehler
    (ADR 0032 §2.1).

    Erbt von `ValueError`, damit defensiv-coded Aufrufer den Standard-
    Konstruktor-Fehler-Pfad nicht aendern muessen. Konkrete Fehlerfaelle
    werfen Subklassen mit strukturierten Konstruktor-Parametern
    (TRY003-Konvention, Message-Bildung in Subklasse).
    """


class ModbusConfigEmptyFieldError(ModbusConfigError):
    """String-Pflichtfeld (`host`) ist leer."""

    def __init__(self, field_name: str) -> None:
        super().__init__(f"ModbusProtocolPortConfig.{field_name} darf nicht leer sein.")
        self.field_name: str = field_name


class ModbusConfigInvalidPortError(ModbusConfigError):
    """`port` liegt ausserhalb des TCP-Port-Bereichs."""

    def __init__(self, value: int) -> None:
        super().__init__(
            f"ModbusProtocolPortConfig.port={value}: muss in [{_MIN_PORT}, {_MAX_PORT}] liegen."
        )
        self.value: int = value


class ModbusConfigInvalidUnitIdError(ModbusConfigError):
    """`unit_id` liegt ausserhalb des Modbus-Slave-Bereichs
    (Modbus-Spec §4.1)."""

    def __init__(self, value: int, context: str) -> None:
        super().__init__(
            f"ModbusProtocolPortConfig.{context}.unit_id={value}: "
            f"muss in [{_MIN_UNIT_ID}, {_MAX_UNIT_ID}] liegen "
            "(Modbus-Spec §4.1: 0=Broadcast, 248-255 reserviert)."
        )
        self.value: int = value
        self.context: str = context


class ModbusConfigInvalidTimeoutError(ModbusConfigError):
    """`timeout_s` ist nicht > 0."""

    def __init__(self, value: float) -> None:
        super().__init__(f"ModbusProtocolPortConfig.timeout_s={value} muss > 0 sein.")
        self.value: float = value


class ModbusConfigEmptyRegistersError(ModbusConfigError):
    """`registers` ist leer; mindestens ein Eintrag noetig."""

    def __init__(self) -> None:
        super().__init__("ModbusProtocolPortConfig.registers darf nicht leer sein.")


class ModbusConfigInvalidAddressError(ModbusConfigError):
    """Register-Adresse ist negativ oder ueber 65535
    (Modbus-Spec §4.2)."""

    def __init__(self, value: int, device_id: str) -> None:
        super().__init__(
            f"ModbusRegisterConfig({device_id!r}).address={value}: "
            "muss in [0, 65535] liegen (Modbus-Spec §4.2)."
        )
        self.value: int = value
        self.device_id: str = device_id


class ModbusConfigInvalidByteOrderError(ModbusConfigError):
    """`byte_order` ist nicht in der Welle-3-Allow-List."""

    def __init__(self, value: str, device_id: str) -> None:
        allowed = sorted(_ALLOWED_BYTE_ORDERS)
        super().__init__(
            f"ModbusRegisterConfig({device_id!r}).byte_order={value!r}: muss in {allowed} liegen."
        )
        self.value: str = value
        self.device_id: str = device_id


class ModbusConfigInvalidFunctionCodeError(ModbusConfigError):
    """`function_code` ist nicht in der Welle-3-Allow-List
    (ADR 0032 §2.4)."""

    def __init__(self, value: int, device_id: str) -> None:
        allowed = sorted(_ALLOWED_FUNCTION_CODES)
        super().__init__(
            f"ModbusRegisterConfig({device_id!r}).function_code={value}: "
            f"muss in {allowed} liegen (Welle-3-Allow-List: FC03/FC04/"
            "FC06/FC10; Coil-Codes FC01/FC02/FC05/FC15 sind Welle-6-"
            "Schaerfung)."
        )
        self.value: int = value
        self.device_id: str = device_id


class ModbusConfigInvalidAccessError(ModbusConfigError):
    """`access` ist nicht `"read"` oder `"write"`."""

    def __init__(self, value: str, device_id: str) -> None:
        super().__init__(
            f'ModbusRegisterConfig({device_id!r}).access={value!r}: muss "read" oder "write" sein.'
        )
        self.value: str = value
        self.device_id: str = device_id


class ModbusConfigFunctionCodeAccessMismatchError(ModbusConfigError):
    """`function_code` passt nicht zu `access` (z. B. FC03 mit
    `access="write"`)."""

    def __init__(self, function_code: int, access: str, device_id: str) -> None:
        super().__init__(
            f"ModbusRegisterConfig({device_id!r}): function_code={function_code} "
            f"passt nicht zu access={access!r} (FC03/FC04 sind read; "
            "FC06/FC10 sind write)."
        )
        self.function_code: int = function_code
        self.access: str = access
        self.device_id: str = device_id


@dataclass(frozen=True, slots=True)
class ModbusRegisterConfig:
    """Register-Profil fuer ein einzelnes Target (Decision M-a inline-
    Schema).

    Pflicht-Felder: `address`, `datatype`, `access`. Optional-Felder
    mit Welle-3-Defaults aus ADR 0032 §2.2/§2.4/§2.5.
    """

    address: int
    datatype: ModbusDatatype
    access: Literal["read", "write"]
    byte_order: str = _DEFAULT_BYTE_ORDER
    word_swap: bool = _DEFAULT_WORD_SWAP
    function_code: int | None = None
    unit_id: int | None = None


@dataclass(frozen=True, slots=True)
class ModbusProtocolPortConfig:
    """Modbus-TCP-Adapter-Profile (Decision M-a inline-Schema im
    Scenario-YAML).

    Konstruktor validiert fail-fast — Konstruktor-Aufrufer (Scenario-
    Loader oder Test) bekommt sofort eine typed `ModbusConfigError`-
    Subclass bei fehlerhafter Konfig.
    """

    host: str
    registers: Mapping[str, ModbusRegisterConfig]
    port: int = _DEFAULT_PORT
    unit_id: int = _DEFAULT_UNIT_ID
    timeout_s: float = _DEFAULT_TIMEOUT_S

    def __post_init__(self) -> None:
        self._validate()
        # Immutable nach Konstruktion (Pattern analog
        # MqttProtocolPortConfig aus Welle 2).
        object.__setattr__(self, "registers", MappingProxyType(dict(self.registers)))

    def _validate(self) -> None:
        if not self.host:
            raise ModbusConfigEmptyFieldError("host")
        if not (_MIN_PORT <= self.port <= _MAX_PORT):
            raise ModbusConfigInvalidPortError(self.port)
        if not (_MIN_UNIT_ID <= self.unit_id <= _MAX_UNIT_ID):
            raise ModbusConfigInvalidUnitIdError(self.unit_id, "<parent>")
        if self.timeout_s <= 0:
            raise ModbusConfigInvalidTimeoutError(self.timeout_s)
        if not self.registers:
            raise ModbusConfigEmptyRegistersError
        for device_id, reg_cfg in self.registers.items():
            _validate_single_register_config(device_id, reg_cfg)


def _validate_single_register_config(device_id: str, reg_cfg: ModbusRegisterConfig) -> None:
    """Prueft Pflicht-Felder und Wertebereiche fuer einen einzelnen
    `ModbusRegisterConfig`. Wirft typed Errors mit Kontext."""
    if not (0 <= reg_cfg.address <= _MAX_REGISTER_ADDRESS):
        raise ModbusConfigInvalidAddressError(reg_cfg.address, device_id)
    if reg_cfg.byte_order not in _ALLOWED_BYTE_ORDERS:
        raise ModbusConfigInvalidByteOrderError(reg_cfg.byte_order, device_id)
    if reg_cfg.access not in ("read", "write"):
        raise ModbusConfigInvalidAccessError(reg_cfg.access, device_id)
    if reg_cfg.function_code is not None:
        _validate_function_code(reg_cfg.function_code, reg_cfg.access, device_id)
    if reg_cfg.unit_id is not None and not (_MIN_UNIT_ID <= reg_cfg.unit_id <= _MAX_UNIT_ID):
        raise ModbusConfigInvalidUnitIdError(reg_cfg.unit_id, device_id)


_READ_FUNCTION_CODES: Final[frozenset[int]] = frozenset({3, 4})
_WRITE_FUNCTION_CODES: Final[frozenset[int]] = frozenset({6, 16})


def _validate_function_code(function_code: int, access: str, device_id: str) -> None:
    """Prueft `function_code` gegen Allow-List + Access-Vertraeglichkeit."""
    if function_code not in _ALLOWED_FUNCTION_CODES:
        raise ModbusConfigInvalidFunctionCodeError(function_code, device_id)
    is_read_fc = function_code in _READ_FUNCTION_CODES
    is_write_fc = function_code in _WRITE_FUNCTION_CODES
    if (access == "read" and not is_read_fc) or (access == "write" and not is_write_fc):
        raise ModbusConfigFunctionCodeAccessMismatchError(function_code, access, device_id)


def resolve_function_code(reg_cfg: ModbusRegisterConfig) -> int:
    """Loest `function_code=None` auf Default-FC (ADR 0032 §2.4) auf.

    - `access="read"`, kein Override: FC03 (Read Holding Registers).
    - `access="write"`, single-register datatype, kein Override:
      FC06 (Write Single Register).
    - `access="write"`, multi-register datatype, kein Override:
      FC10 (Write Multiple Registers).
    """
    if reg_cfg.function_code is not None:
        return reg_cfg.function_code
    if reg_cfg.access == "read":
        return _FC_READ_HOLDING_REGISTERS
    # access == "write"
    register_count = datatype_register_count(reg_cfg.datatype)
    return (
        _FC_WRITE_SINGLE_REGISTER
        if register_count == _SINGLE_REGISTER
        else _FC_WRITE_MULTIPLE_REGISTERS
    )


def resolve_unit_id(reg_cfg: ModbusRegisterConfig, parent_unit_id: int) -> int:
    """Loest `unit_id=None` auf Parent-`unit_id` auf (ADR 0032 §2.5)."""
    if reg_cfg.unit_id is not None:
        return reg_cfg.unit_id
    return parent_unit_id
