# SPDX-License-Identifier: GPL-3.0-only
"""IEC-61850-Codec (M4 Welle 5b, ADR 0035 §2.3).

Decision I-c: Konvertierung zwischen `pyiec61850.mms.MMSClient.read_value`-
Ergebnissen und Python-Native:

- `datatype="bool"` → `bool` (`MmsType.BOOLEAN` mappt direkt).
- `datatype="int32"` → `int` (`MmsType.INT32` mappt direkt; `INT16`/
  `INT64`-Range-Werte werden via `int()` getypt; Out-of-Range
  `OverflowError`).
- `datatype="float"` → `Decimal(repr(float))` (Float-Praezisions-
  Konvention aus ADR 0032 §2.2; FLOAT32-Wire-Quantisierung wird
  in der Library bereits angewandt).
- `datatype="string"` → `str` (`MmsType.VISIBLE_STRING` mappt direkt).

**Container-vs-Leaf-Erkennung:** pyiec61850-ng-Probe-Run-Befund
2026-06-01 hat gezeigt, dass `read_value` bei strukturierten DAs
(z. B. falsche FC fuer ein konkretes Leaf) einen MmsValue-Container
als String-Repr (`'<MmsValue type=15>'`) zurueckliefert statt einen
primitiven Python-Wert. Codec erkennt das und wirft
`Iec61850CodecValueTypeError`.

Asymmetrie analog ADR 0032 §2.2 / ADR 0033 §2.3 / ADR 0034 §2.3:

- **Decoding ist tolerant** — unerwartete Library-Werte werden in
  typed `Iec61850CodecError` umgemantelt.
- **Encoding** ist Welle-6-Material (Write-Pfad; Adapter-Anti-
  Scope in Welle 5b).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Final

from grid_gym.adapters.driven.protocol_iec61850._errors import (
    Iec61850CodecOverflowError,
    Iec61850CodecValueTypeError,
)

# Library-spezifische String-Indikatoren fuer Container-MmsValue
# (Probe-Run-Befund 2026-06-01: type=15 ist STRUCTURE-Container).
_MMS_CONTAINER_PREFIX: Final[str] = "<MmsValue"

# Int32-Welle-5b-Range-Kontrolle. pyiec61850-ng-`int`-Returnwerte
# koennen aus einem int8/16/32/64-MMS-Wire-Layer kommen — der Codec
# pinnt auf Welle-5b-Allow-List int32.
_INT32_MIN: Final[int] = -(2**31)
_INT32_MAX: Final[int] = 2**31 - 1


def decode_mms_value(
    raw_value: Any, datatype: str, reference: str, fc: str
) -> bool | int | Decimal | str:
    """Wandelt einen `MMSClient.read_value()`-Returnwert in die
    Python-Native-Form um (ADR 0035 §2.3 Decision I-c).

    `reference` und `fc` werden nur fuer typed-Error-Reporting
    benutzt — der Codec ist stateless.
    """
    if _is_container_repr(raw_value):
        raise Iec61850CodecValueTypeError(reference, fc, datatype, repr(raw_value))

    if datatype == "bool":
        return _decode_bool(raw_value, reference)
    if datatype == "int32":
        return _decode_int32(raw_value, reference)
    if datatype == "float":
        return _decode_float(raw_value, reference)
    if datatype == "string":
        return _decode_string(raw_value, reference, fc)
    # Should not happen — Config-Validation pinnt datatype auf
    # die Welle-5b-Allow-List; jeder andere Pfad ist Konfig-Bug.
    raise Iec61850CodecValueTypeError(reference, fc, datatype, repr(raw_value))


def _is_container_repr(raw_value: Any) -> bool:
    """`MMSClient.read_value` liefert bei strukturierten DAs einen
    Library-internen Container-Stringify (`'<MmsValue type=15>'` o.ae.)
    statt einen primitiven Python-Wert.

    Heuristik: String, der mit `'<MmsValue'` beginnt, ist kein echter
    Welle-5b-Datatype-Wert.
    """
    return isinstance(raw_value, str) and raw_value.startswith(_MMS_CONTAINER_PREFIX)


def _decode_bool(raw_value: Any, reference: str) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    # pyiec61850-ng-Probe-Run-Befund 2026-06-01: Bool wird oft als
    # int (0/1) zurueck­geliefert, je nach CFG-DO-Struktur.
    if isinstance(raw_value, int) and not isinstance(raw_value, bool):
        if raw_value in (0, 1):
            return bool(raw_value)
        raise Iec61850CodecOverflowError(
            reference, "bool", raw_value, "bool-coercion erwartet 0 oder 1"
        )
    raise Iec61850CodecValueTypeError(reference, "?", "bool", type(raw_value).__name__)


def _decode_int32(raw_value: Any, reference: str) -> int:
    if isinstance(raw_value, bool):
        raise Iec61850CodecValueTypeError(reference, "?", "int32", "bool (not int32)")
    if not isinstance(raw_value, int):
        raise Iec61850CodecValueTypeError(reference, "?", "int32", type(raw_value).__name__)
    if not (_INT32_MIN <= raw_value <= _INT32_MAX):
        raise Iec61850CodecOverflowError(
            reference,
            "int32",
            raw_value,
            f"int32 range [{_INT32_MIN}, {_INT32_MAX}]",
        )
    return raw_value


def _decode_float(raw_value: Any, reference: str) -> Decimal:
    if isinstance(raw_value, bool):
        raise Iec61850CodecValueTypeError(reference, "?", "float", "bool (not float)")
    if not isinstance(raw_value, (float, int)):
        raise Iec61850CodecValueTypeError(reference, "?", "float", type(raw_value).__name__)
    try:
        return Decimal(repr(float(raw_value)))
    except (OverflowError, ValueError) as exc:
        raise Iec61850CodecOverflowError(reference, "float", raw_value, str(exc)) from exc


def _decode_string(raw_value: Any, reference: str, fc: str) -> str:
    if not isinstance(raw_value, str):
        raise Iec61850CodecValueTypeError(reference, fc, "string", type(raw_value).__name__)
    return raw_value
