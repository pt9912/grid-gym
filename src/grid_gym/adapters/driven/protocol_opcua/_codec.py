"""OPC-UA-Codec (M4 Welle 4, ADR 0033 §2.3).

Decision O-c: Konvertierung zwischen Python-Native-Typen
(`bool | int | Decimal | str`) und `asyncua.ua.Variant` mit
explizitem `VariantType` (Welle-4-Datatype-Set).

Asymmetrie analog ADR 0032 §2.2 (Modbus-Codec):

- **Encoding ist strikt** — Out-of-Range-Werte, NaN/Infinity bei
  Float/Double und Datentyp-Mismatches werfen typed Exceptions
  sofort.
- **Dekodierung ist tolerant** — Variant-Type-Mismatches landen
  als `OpcuaCodecDecodeError`.

Praezisions-Konvention fuer Float/Double: `Decimal(repr(float_value))`
analog Modbus-`float32`-Pfad (ADR 0032 §2.2; gleiche Wahl).
"""

from __future__ import annotations

import math
import struct
from decimal import Decimal
from typing import Any, Final

from asyncua import ua

from grid_gym.adapters.driven.protocol_opcua._config import OpcuaDatatype


# Mapping `OpcuaDatatype` -> `ua.VariantType` (asyncua-API).
_VARIANT_TYPE_BY_DATATYPE: Final[dict[OpcuaDatatype, ua.VariantType]] = {
    OpcuaDatatype.BOOLEAN: ua.VariantType.Boolean,
    OpcuaDatatype.INT16: ua.VariantType.Int16,
    OpcuaDatatype.UINT16: ua.VariantType.UInt16,
    OpcuaDatatype.INT32: ua.VariantType.Int32,
    OpcuaDatatype.UINT32: ua.VariantType.UInt32,
    OpcuaDatatype.FLOAT: ua.VariantType.Float,
    OpcuaDatatype.DOUBLE: ua.VariantType.Double,
    OpcuaDatatype.STRING: ua.VariantType.String,
}


# Wertebereiche fuer Integer-Datatypes (Encoding-Validation).
_INT_RANGES: Final[dict[OpcuaDatatype, tuple[int, int]]] = {
    OpcuaDatatype.INT16: (-(2**15), 2**15 - 1),
    OpcuaDatatype.UINT16: (0, 2**16 - 1),
    OpcuaDatatype.INT32: (-(2**31), 2**31 - 1),
    OpcuaDatatype.UINT32: (0, 2**32 - 1),
}

_FLOAT_DATATYPES: Final[frozenset[OpcuaDatatype]] = frozenset(
    {OpcuaDatatype.FLOAT, OpcuaDatatype.DOUBLE}
)


class OpcuaCodecError(ValueError):
    """Base-Klasse fuer Codec-Fehler (ADR 0033 §2.3)."""


class OpcuaCodecOutOfRangeError(OpcuaCodecError):
    """Eingabewert liegt ausserhalb des Datatype-Wertebereichs."""

    def __init__(
        self,
        value: int | float | Decimal,
        datatype: OpcuaDatatype,
        allowed: tuple[int, int],
    ) -> None:
        super().__init__(
            f"Wert {value!r} liegt ausserhalb des {datatype.value}-Wertebereichs {allowed}."
        )
        self.value: int | float | Decimal = value
        self.datatype: OpcuaDatatype = datatype
        self.allowed: tuple[int, int] = allowed


class OpcuaCodecNonFiniteError(OpcuaCodecError):
    """`Float`/`Double`-Eingabe ist NaN oder Infinity."""

    def __init__(self, value: float, datatype: OpcuaDatatype) -> None:
        super().__init__(
            f"`{datatype.value}`-Wert {value!r}: NaN/Infinity ist nicht serialisierbar."
        )
        self.value: float = value
        self.datatype: OpcuaDatatype = datatype


class OpcuaCodecPayloadTypeError(TypeError):
    """`Command.payload['value']` hat einen OPC-UA-fremden Type
    (erwartet `bool`/`int`/`Decimal`/`float`/`str` je nach Datatype)."""

    def __init__(self, observed_type: str, datatype: OpcuaDatatype) -> None:
        super().__init__(
            f"OPC-UA-Write erwartet kompatiblen Typ fuer {datatype.value!r}, "
            f"erhalten: {observed_type}"
        )
        self.observed_type: str = observed_type
        self.datatype: OpcuaDatatype = datatype


class OpcuaCodecDecodeError(OpcuaCodecError):
    """Decode-Pfad ist gescheitert (z. B. Variant-Value-`None`,
    unerwarteter Python-Typ)."""

    def __init__(self, observed_type: str, datatype: OpcuaDatatype) -> None:
        super().__init__(
            f"OPC-UA-Decode fuer {datatype.value!r} fehlgeschlagen: "
            f"Variant-Value-Typ {observed_type} nicht zuordenbar."
        )
        self.observed_type: str = observed_type
        self.datatype: OpcuaDatatype = datatype


def encode_value_to_variant(
    value: bool | int | Decimal | float | str,
    datatype: OpcuaDatatype,
) -> ua.Variant:
    """Serialisiert `value` in eine `asyncua.ua.Variant` (ADR 0033
    §2.3).

    Wirft `OpcuaCodecOutOfRangeError` bei Integer-Range-Verletzung,
    `OpcuaCodecNonFiniteError` bei NaN/Infinity-Float und
    `OpcuaCodecPayloadTypeError` bei Typ-Mismatch.
    """
    variant_type = _VARIANT_TYPE_BY_DATATYPE[datatype]
    if datatype is OpcuaDatatype.BOOLEAN:
        return ua.Variant(_coerce_bool(value, datatype), variant_type)
    if datatype is OpcuaDatatype.STRING:
        return ua.Variant(_coerce_string(value, datatype), variant_type)
    if datatype in _FLOAT_DATATYPES:
        return ua.Variant(_coerce_float(value, datatype), variant_type)
    return ua.Variant(_coerce_int(value, datatype), variant_type)


def decode_variant_to_value(
    variant: ua.Variant, datatype: OpcuaDatatype
) -> bool | int | Decimal | str:
    """Deserialisiert `variant` zu Python-Native (ADR 0033 §2.3).

    `Float`/`Double` -> `Decimal(repr(value))` (Praezisions-
    Konvention analog ADR 0032 §2.2). Wirft `OpcuaCodecDecodeError`,
    wenn der Variant-Wert keinen passenden Python-Typ traegt.
    """
    raw: Any = variant.Value
    if raw is None:
        raise OpcuaCodecDecodeError("None", datatype)
    if datatype is OpcuaDatatype.BOOLEAN:
        return _decode_bool(raw, datatype)
    if datatype is OpcuaDatatype.STRING:
        return _decode_string(raw, datatype)
    if datatype in _FLOAT_DATATYPES:
        return _decode_float(raw, datatype)
    return _decode_int(raw, datatype)


def _decode_bool(raw: Any, datatype: OpcuaDatatype) -> bool:
    if not isinstance(raw, bool):
        raise OpcuaCodecDecodeError(type(raw).__name__, datatype)
    return raw


def _decode_string(raw: Any, datatype: OpcuaDatatype) -> str:
    if not isinstance(raw, str):
        raise OpcuaCodecDecodeError(type(raw).__name__, datatype)
    return raw


def _decode_float(raw: Any, datatype: OpcuaDatatype) -> Decimal:
    """Decode `Float`/`Double` aus Variant-Value zu `Decimal`.

    Slice-032-Schaerfung (Welle-4-Review-Folge Finding 3.2 + 3.3):

    - `Float` (32-bit): quantisiere auf 32-bit-Praezision via
      `struct.pack('!f', x)` / `struct.unpack`, damit das `Decimal`
      nur die im Wire-Format transportierten Stellen traegt
      (sonst speichert `repr(float)` 17 Stellen, die nicht real sind).
    - `OverflowError` aus `float(int)` bei riesigen Integern faengt
      in typed `OpcuaCodecDecodeError`.
    """
    if not isinstance(raw, (float, int)) or isinstance(raw, bool):
        raise OpcuaCodecDecodeError(type(raw).__name__, datatype)
    try:
        as_float = float(raw)
    except OverflowError as exc:
        raise OpcuaCodecDecodeError("OverflowError", datatype) from exc
    if datatype is OpcuaDatatype.FLOAT:
        # 32-bit-Quantisierung: pack/unpack erzwingt IEEE-754 single
        # precision; das `Decimal` traegt nur die Wire-Praezision.
        as_float = struct.unpack("!f", struct.pack("!f", as_float))[0]
    return Decimal(repr(as_float))


def _decode_int(raw: Any, datatype: OpcuaDatatype) -> int:
    if not isinstance(raw, int) or isinstance(raw, bool):
        raise OpcuaCodecDecodeError(type(raw).__name__, datatype)
    return raw


# ---------------------------------------------------------------------------
# Private Helpers
# ---------------------------------------------------------------------------


def _coerce_bool(value: object, datatype: OpcuaDatatype) -> bool:
    if isinstance(value, bool):
        return value
    raise OpcuaCodecPayloadTypeError(type(value).__name__, datatype)


def _coerce_string(value: object, datatype: OpcuaDatatype) -> str:
    if isinstance(value, str):
        return value
    raise OpcuaCodecPayloadTypeError(type(value).__name__, datatype)


def _coerce_int(value: object, datatype: OpcuaDatatype) -> int:
    """Akzeptiert int/Decimal/float (kein bool) und range-checkt.

    Slice-032-Nachzug (Welle-4-Review Finding 2):
    `int(Decimal("Infinity"))` wirft `OverflowError`,
    `int(float("nan"))` wirft `ValueError`. Beide werden in
    typed `OpcuaCodecOutOfRangeError` umgemantelt, damit die
    Adapter-Surface dem `DeviceProtocolPort`-Vertrag entspricht.
    """
    if isinstance(value, bool):
        raise OpcuaCodecPayloadTypeError("bool", datatype)
    if isinstance(value, int):
        as_int = value
    elif isinstance(value, (Decimal, float)):
        try:
            as_int = int(value)
        except (OverflowError, ValueError) as exc:
            raise OpcuaCodecOutOfRangeError(value, datatype, _INT_RANGES[datatype]) from exc
    else:
        raise OpcuaCodecPayloadTypeError(type(value).__name__, datatype)
    low, high = _INT_RANGES[datatype]
    if not (low <= as_int <= high):
        raise OpcuaCodecOutOfRangeError(as_int, datatype, (low, high))
    return as_int


def _coerce_float(value: object, datatype: OpcuaDatatype) -> float:
    """Akzeptiert int/Decimal/float (kein bool) und NaN-Check.

    Slice-032-Nachzug (Welle-4-Review Finding 2):
    `float(10**400)` wirft `OverflowError`,
    `float(Decimal("Infinity"))` ist ein finiter Float ueber
    `inf`, der vom `math.isfinite`-Check abgefangen wird —
    aber `float(Decimal("NaN"))` kommt durch. Beide Pfade
    werden in typed `OpcuaCodecNonFiniteError` umgemantelt
    (NaN/Inf werden als nicht-finit klassifiziert).
    """
    if isinstance(value, bool):
        raise OpcuaCodecPayloadTypeError("bool", datatype)
    if isinstance(value, float):
        as_float = value
    elif isinstance(value, (int, Decimal)):
        try:
            as_float = float(value)
        except (OverflowError, ValueError) as exc:
            # Riesige Integer / Decimal-Inf wandern in
            # NonFiniteError (semantisch: nicht-darstellbarer
            # Float-Wert).
            raise OpcuaCodecNonFiniteError(float("inf"), datatype) from exc
    else:
        raise OpcuaCodecPayloadTypeError(type(value).__name__, datatype)
    if not math.isfinite(as_float):
        raise OpcuaCodecNonFiniteError(as_float, datatype)
    return as_float
