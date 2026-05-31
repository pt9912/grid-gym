"""DNP3-Codec (M4 Welle 5a, ADR 0034 §2.3).

Decision D-c: Konvertierung zwischen `nfm-dnp3`-Object-Typen
(`AnalogInput`, `BinaryInput`) und Python-Native (`Decimal`).
Welle-5a-Group/Variation-Set:

- Group 1, Variation 1 (Binary Input, single-bit) → `Decimal(int(bool))`.
- Group 1, Variation 2 (Binary Input with flags) → `Decimal(int(bool))`.
- Group 30, Variation 1 (32-bit Integer Analog Input) → `Decimal(int)`.
- Group 30, Variation 5 (32-bit Float Analog Input) →
  `Decimal(repr(float))` (Float-Praezisions-Konvention aus
  ADR 0032 §2.2).

Asymmetrie analog ADR 0032 §2.2 / ADR 0033 §2.3:

- **Decoding ist tolerant** — wenn ein nfm-dnp3-Objekt ein
  unerwartetes Feld liefert (z. B. None-Wert), wird das in
  typed `Dnp3CodecError` umgemantelt.
- **Encoding** ist Welle-6-Material (Write-Pfad).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Final


# DNP3-Object-Group-Konstanten (ADR 0034 §2.3).
_GROUP_BINARY_INPUT: Final[int] = 1
_GROUP_ANALOG_INPUT: Final[int] = 30
_VARIATION_ANALOG_INT32: Final[int] = 1
_VARIATION_ANALOG_FLOAT32: Final[int] = 5


class Dnp3CodecError(ValueError):
    """Base-Klasse fuer DNP3-Codec-Fehler (ADR 0034 §2.3)."""


class Dnp3CodecGroupMismatchError(Dnp3CodecError):
    """Server hat ein Point-Objekt mit unerwarteter Group/Variation
    geliefert.

    Welle-5a-Adapter erwartet pro `Dnp3PointConfig.(group, variation)`
    ein spezifisches Objekt aus dem `nfm-dnp3.PollResult`. Falls die
    Library ein Objekt mit anderer Group liefert (z. B. Server-
    Misconfig), wird das hier typed gemeldet.
    """

    def __init__(self, expected: tuple[int, int], observed_type: str) -> None:
        super().__init__(
            f"Dnp3 codec: expected group/variation {expected}, observed object type {observed_type}."
        )
        self.expected: tuple[int, int] = expected
        self.observed_type: str = observed_type


class Dnp3CodecValueTypeError(Dnp3CodecError):
    """nfm-dnp3-Objekt-Wert ist nicht im erwarteten Python-Typ
    (z. B. `AnalogInput.value` ist `None` oder ein Sequenz)."""

    def __init__(self, observed_type: str, group: int, variation: int) -> None:
        super().__init__(
            f"Dnp3 codec: AnalogInput/BinaryInput.value ist {observed_type}; "
            f"erwartet Python-Native fuer group={group}/variation={variation}."
        )
        self.observed_type: str = observed_type
        self.group: int = group
        self.variation: int = variation


def decode_point_value(point: Any, group: int, variation: int) -> Decimal:
    """Wandelt ein `nfm-dnp3.AnalogInput`/`BinaryInput`-Objekt in einen
    `Decimal` um (ADR 0034 §2.3 Decision D-c).

    Liefert `Decimal` fuer alle Welle-5a-Group/Variation-Kombinationen:

    - Group 1/V1, 1/V2 (Binary) → `Decimal(int(bool(value)))`.
    - Group 30/V1 (Int32 Analog) → `Decimal(int(value))`.
    - Group 30/V5 (Float32 Analog) → `Decimal(repr(float(value)))`
      (Praezisions-Konvention aus ADR 0032 §2.2).
    """
    raw = getattr(point, "value", None)
    if raw is None:
        raise Dnp3CodecValueTypeError("None", group, variation)

    if group == _GROUP_BINARY_INPUT:
        return _decode_binary(raw, group, variation)
    if group == _GROUP_ANALOG_INPUT:
        return _decode_analog(raw, group, variation)
    # Should not happen — Config-Validation pinnt Group auf
    # Welle-5a-Allow-List; jeder andere Pfad ist Konfig-Bug.
    raise Dnp3CodecGroupMismatchError((group, variation), type(point).__name__)


def _decode_binary(raw: Any, group: int, variation: int) -> Decimal:
    """Group 1/V1 + 1/V2 (Binary Input) → `Decimal(int(bool))`."""
    if not isinstance(raw, bool):
        raise Dnp3CodecValueTypeError(type(raw).__name__, group, variation)
    return Decimal(int(raw))


def _decode_analog(raw: Any, group: int, variation: int) -> Decimal:
    """Group 30/V1 (Int32) und 30/V5 (Float32) Decoder."""
    if variation == _VARIATION_ANALOG_INT32:
        if not isinstance(raw, int) or isinstance(raw, bool):
            raise Dnp3CodecValueTypeError(type(raw).__name__, group, variation)
        return Decimal(raw)
    if variation == _VARIATION_ANALOG_FLOAT32:
        if not isinstance(raw, (float, int)) or isinstance(raw, bool):
            raise Dnp3CodecValueTypeError(type(raw).__name__, group, variation)
        return Decimal(repr(float(raw)))
    # Variation ist Welle-6-Schaerfung; Config-Validation sollte
    # das nie zulassen.
    raise Dnp3CodecGroupMismatchError((group, variation), "AnalogInput")
