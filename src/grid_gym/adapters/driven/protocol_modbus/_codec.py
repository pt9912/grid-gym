"""Modbus-Register-Codec (M4 Welle 3, ADR 0032 §2.2).

Decision M-b: `struct.pack`/`struct.unpack` mit Format-String aus
`(datatype, byte_order)` konvertiert zwischen
`(value: int|Decimal, ModbusDatatype, byte_order, word_swap)` und
`tuple[int, ...]` (Register-Liste).

Asymmetrie analog ADR 0031 §2.2:

- **Encoding ist strikt** — Out-of-Range-Werte werfen typed
  Exceptions sofort (`ModbusCodecOutOfRangeError`,
  `ModbusCodecNonFiniteError`).
- **Dekodierung ist tolerant** — fehlende Register oder ungueltige
  Datatype-Konfiguration landen als `ModbusCodecDecodeError`.

`word_swap=True` rotiert die zwei Register vor `pack`/nach `unpack`
(relevant nur fuer Multi-Register-Datatypes wie `int32`/`float32`).
"""

from __future__ import annotations

import math
import struct
from decimal import Decimal
from typing import Final

from grid_gym.adapters.driven.protocol_modbus._config import (
    ModbusDatatype,
    datatype_register_count,
)

# struct-Format-String pro Datatype (ohne Byte-Order-Praefix).
_FORMAT_BY_DATATYPE: Final[dict[ModbusDatatype, str]] = {
    ModbusDatatype.INT16: "h",
    ModbusDatatype.UINT16: "H",
    ModbusDatatype.INT32: "i",
    ModbusDatatype.UINT32: "I",
    ModbusDatatype.FLOAT32: "f",
}

# Bytes-pro-Register im Modbus-TCP-Wire-Format (Modbus-Spec §4.1).
_BYTES_PER_REGISTER: Final[int] = 2
# Register-Anzahl bei Multi-Register-Datatypes (int32/uint32/float32).
_TWO_REGISTERS: Final[int] = 2

# Wertebereiche fuer Encoding-Validation.
_INT_RANGES: Final[dict[ModbusDatatype, tuple[int, int]]] = {
    ModbusDatatype.INT16: (-(2**15), 2**15 - 1),
    ModbusDatatype.UINT16: (0, 2**16 - 1),
    ModbusDatatype.INT32: (-(2**31), 2**31 - 1),
    ModbusDatatype.UINT32: (0, 2**32 - 1),
}


class ModbusCodecError(ValueError):
    """Base-Klasse fuer Modbus-Codec-Fehler (ADR 0032 §2.2)."""


class ModbusCodecOutOfRangeError(ModbusCodecError):
    """Eingabewert liegt ausserhalb des Datatype-Wertebereichs."""

    def __init__(
        self, value: int | float, datatype: ModbusDatatype, allowed: tuple[int, int]
    ) -> None:
        super().__init__(
            f"Wert {value!r} liegt ausserhalb des {datatype.value}-Wertebereichs {allowed}."
        )
        self.value: int | float = value
        self.datatype: ModbusDatatype = datatype
        self.allowed: tuple[int, int] = allowed


class ModbusCodecNonFiniteError(ModbusCodecError):
    """`float32`-Eingabe ist NaN oder Infinity."""

    def __init__(self, value: float) -> None:
        super().__init__(f"`float32`-Wert {value!r}: NaN/Infinity ist nicht serialisierbar.")
        self.value: float = value


class ModbusCodecRegisterCountMismatchError(ModbusCodecError):
    """Register-Liste hat nicht die fuer den Datatype erwartete Laenge."""

    def __init__(self, datatype: ModbusDatatype, expected: int, actual: int) -> None:
        super().__init__(f"`{datatype.value}` braucht {expected} Register, erhalten: {actual}.")
        self.datatype: ModbusDatatype = datatype
        self.expected: int = expected
        self.actual: int = actual


class ModbusCodecDecodeError(ModbusCodecError):
    """Decode-Pfad ist gescheitert (z. B. `struct.unpack`-Fehler)."""


class ModbusCodecStructUnpackError(ModbusCodecDecodeError):
    """`struct.unpack` ist gescheitert (Format-String / Byte-Anzahl-
    Mismatch). Wrapper um die Library-Exception mit kontextueller
    Format-String-Information."""

    def __init__(self, fmt: str, reason: str) -> None:
        super().__init__(f"struct.unpack(fmt={fmt!r}) failed: {reason}")
        self.fmt: str = fmt


class ModbusCodecOddBytesError(ModbusCodecDecodeError):
    """Byte-Anzahl beim Register-Zusammenbau ist nicht gerade
    (Modbus-Register sind 16-bit, also durch 2 teilbar)."""

    def __init__(self, byte_count: int) -> None:
        super().__init__(
            f"Byte-Anzahl {byte_count} ist nicht gerade (Modbus-Register sind 16-bit)."
        )
        self.byte_count: int = byte_count


class ModbusCodecPayloadTypeError(TypeError):
    """`Command.payload['value']` hat einen Modbus-fremden Type
    (erwartet `int`/`Decimal`/`float`)."""

    def __init__(self, observed_type: str) -> None:
        super().__init__(f"Modbus-Write erwartet int/Decimal/float, erhalten: {observed_type}")
        self.observed_type: str = observed_type


def encode_value_to_registers(
    value: int | Decimal | float,
    datatype: ModbusDatatype,
    byte_order: str,
    word_swap: bool,
) -> tuple[int, ...]:
    """Serialisiert `value` in eine Tuple von 16-bit Register-Worten
    (ADR 0032 §2.2).

    Wirft `ModbusCodecOutOfRangeError` fuer Integer-Datatypes, wenn
    `value` ausserhalb des Wertebereichs liegt. Wirft
    `ModbusCodecNonFiniteError` fuer `float32`, wenn `value` NaN/
    Infinity ist.
    """
    if datatype is ModbusDatatype.FLOAT32:
        return _encode_float32(_to_float(value), byte_order, word_swap)
    return _encode_int(
        _to_int_for_datatype(value, datatype),
        datatype,
        byte_order,
        word_swap,
    )


def decode_registers_to_value(
    registers: tuple[int, ...] | list[int],
    datatype: ModbusDatatype,
    byte_order: str,
    word_swap: bool,
) -> Decimal:
    """Deserialisiert eine Tuple von 16-bit Register-Worten in eine
    `Decimal`-Repraesentation (ADR 0032 §2.2).

    Wirft `ModbusCodecRegisterCountMismatchError` wenn die Anzahl
    nicht zum Datatype passt. Wirft `ModbusCodecDecodeError` bei
    `struct.unpack`-Fehler.
    """
    expected = datatype_register_count(datatype)
    if len(registers) != expected:
        raise ModbusCodecRegisterCountMismatchError(datatype, expected, len(registers))
    ordered = _apply_word_swap(tuple(registers), word_swap)
    raw_bytes = _registers_to_bytes(ordered)
    return _unpack_value(raw_bytes, datatype, byte_order)


# ---------------------------------------------------------------------------
# Private Helpers
# ---------------------------------------------------------------------------


def _to_int_for_datatype(value: int | Decimal | float, datatype: ModbusDatatype) -> int:
    """Konvertiert `value` zu `int` fuer einen Integer-Datatype mit
    Range-Check."""
    if isinstance(value, bool):
        as_int = int(value)
    elif isinstance(value, int):
        as_int = value
    elif isinstance(value, Decimal | float):
        as_int = int(value)
    else:
        raise ModbusCodecOutOfRangeError(value, datatype, _INT_RANGES[datatype])
    low, high = _INT_RANGES[datatype]
    if not (low <= as_int <= high):
        raise ModbusCodecOutOfRangeError(as_int, datatype, (low, high))
    return as_int


def _to_float(value: int | Decimal | float) -> float:
    """Konvertiert `value` zu `float` fuer `float32`-Encoding."""
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    raise ModbusCodecNonFiniteError(float("nan"))


def _encode_int(
    int_value: int,
    datatype: ModbusDatatype,
    byte_order: str,
    word_swap: bool,
) -> tuple[int, ...]:
    """Packt eine Integer in 1 oder 2 Register-Worte."""
    fmt = _byte_order_prefix(byte_order) + _FORMAT_BY_DATATYPE[datatype]
    raw_bytes = struct.pack(fmt, int_value)
    registers = _bytes_to_registers(raw_bytes)
    return _apply_word_swap(registers, word_swap)


def _encode_float32(float_value: float, byte_order: str, word_swap: bool) -> tuple[int, ...]:
    """Packt einen `float32` in 2 Register-Worte. NaN/Infinity ->
    `ModbusCodecNonFiniteError`."""
    if not math.isfinite(float_value):
        raise ModbusCodecNonFiniteError(float_value)
    fmt = _byte_order_prefix(byte_order) + "f"
    raw_bytes = struct.pack(fmt, float_value)
    registers = _bytes_to_registers(raw_bytes)
    return _apply_word_swap(registers, word_swap)


def _unpack_value(raw_bytes: bytes, datatype: ModbusDatatype, byte_order: str) -> Decimal:
    """`struct.unpack` -> `Decimal` (mit String-Roundtrip fuer Float-
    Praezisions-Tracking)."""
    fmt = _byte_order_prefix(byte_order) + _FORMAT_BY_DATATYPE[datatype]
    try:
        (raw_value,) = struct.unpack(fmt, raw_bytes)
    except struct.error as exc:
        raise ModbusCodecStructUnpackError(fmt, str(exc)) from exc
    if datatype is ModbusDatatype.FLOAT32:
        # Float -> Decimal via str() bewahrt die paho-mqtt-aehnliche
        # Praezisions-Wahl (siehe TelemetryPoint-Vertrag).
        return Decimal(repr(raw_value))
    return Decimal(raw_value)


def _byte_order_prefix(byte_order: str) -> str:
    """`struct`-Praefix `>` (big-endian) oder `<` (little-endian)."""
    return ">" if byte_order == "big_endian" else "<"


def _bytes_to_registers(raw_bytes: bytes) -> tuple[int, ...]:
    """Wandelt eine Byte-Folge in 16-bit Register-Worte
    (big-endian-pro-Register; Modbus-Spec §4.1)."""
    if len(raw_bytes) % _BYTES_PER_REGISTER != 0:
        # Sollte nicht passieren — alle Datatypes sind register-
        # aligned. Defensive Pruefung mit typed Error.
        raise ModbusCodecOddBytesError(len(raw_bytes))
    return tuple(
        (raw_bytes[i] << 8) | raw_bytes[i + 1]
        for i in range(0, len(raw_bytes), _BYTES_PER_REGISTER)
    )


def _registers_to_bytes(registers: tuple[int, ...]) -> bytes:
    """Wandelt 16-bit Register-Worte in eine Byte-Folge zurueck
    (big-endian-pro-Register; Modbus-Spec §4.1)."""
    out = bytearray()
    for reg in registers:
        out.append((reg >> 8) & 0xFF)
        out.append(reg & 0xFF)
    return bytes(out)


def _apply_word_swap(registers: tuple[int, ...], word_swap: bool) -> tuple[int, ...]:
    """Rotiert die zwei Register-Worte bei Multi-Register-Datatypes
    (`int32`/`uint32`/`float32`) wenn `word_swap=True`. Einzelregister
    bleiben unveraendert."""
    if not word_swap or len(registers) != _TWO_REGISTERS:
        return registers
    return (registers[1], registers[0])
