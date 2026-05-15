"""Kanonische JSON-Serialisierung fuer grid-gym (ADR 0002 §A-2).

Wurzel-Vertrag (`GG-DATA-005`): deterministische, byte-identische
Ausgabe fuer semantisch identische Eingaben. Stabile
(lexikographische) Schluesselreihenfolge, Fixed-Point-Notation fuer
`Decimal`, kein `float`, kein NaN/Infinity, UTF-8-Bytes als
Ergebnistyp. Stdlib-only — bewusst kein `json.dumps`, weil dieser
`Decimal` weder nativ noch zuverlaessig ueber `default=` als
JSON-Zahl emittieren kann.

`AC-NO-JSON` (ADR 0002 §A-1) whitelistet dieses Modul als einzige
Stelle, an der direkte `json`-Serialisierung erlaubt waere — die
heutige Custom-Emitter-Implementierung nutzt das `json`-Modul
jedoch nicht. Domain-Code MUSS `canonical_json` aufrufen, statt
`json.dumps` direkt zu verwenden.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from grid_gym.hexagon.core.errors import GridGymError

# JSON RFC 8259: Steuerzeichen unterhalb 0x20 MUESSEN als `\u00XX`
# escaped werden. RFC-konform werden NICHT escaped:
# - `0x7F` (DEL)
# - `U+2028` (line separator) und `U+2029` (paragraph separator)
# Beide sind RFC-zulaessig als literale Zeichen. Pre-ES2019-JavaScript
# wuerde an U+2028/U+2029 bei `eval()`-style Parsing scheitern; moderne
# `JSON.parse` ist davon nicht betroffen. Wenn ein Konsument doch
# eval-basiert parst, muss er einen modernen JSON-Parser nutzen.
_CONTROL_CHAR_THRESHOLD = 0x20

# Unicode-Surrogat-Bereich (UTF-16-Halbpaare). Unpaarte Surrogate sind
# weder gueltiges UTF-8 noch gueltiges JSON (`RFC 8259 §7`) und brechen
# beim `.encode("utf-8")` mit einem ungetypten `UnicodeEncodeError`.
# Wir lehnen sie deshalb frueh mit typisiertem Fehler ab.
_SURROGATE_LOW = 0xD800
_SURROGATE_HIGH = 0xDFFF

# Direkt-Escape-Tabelle fuer JSON (RFC 8259).
_ESCAPE_MAP: dict[str, str] = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


class CanonicalSerializationError(GridGymError):
    """Wurzel der Vertragsverletzungen aus ADR 0002 §A-2."""


class FloatNotAllowedError(CanonicalSerializationError):
    """`float` ist im kanonischen Pfad verboten.

    Float-Werte muessen an der Domain-Eingangsgrenze
    (Pydantic-Validator, Scenario-Loader, Adapter-Mapping) in
    `Decimal` mit max. 6 Nachkommastellen quantisiert werden
    (`GG-DATA-005`).
    """

    def __init__(self) -> None:
        super().__init__(
            "float not allowed in canonical output — convert to Decimal "
            "at domain ingress (GG-DATA-005)"
        )


class NonFiniteDecimalError(CanonicalSerializationError):
    """`Decimal("NaN")`/`Decimal("Infinity")` sind in kanonischen
    Ausgaben nicht erlaubt.

    Solche Werte erscheinen in Telemetrie ausschliesslich als
    Qualitaetsfeld (`quality = "nan"` / `"invalid"`), nicht als
    numerischer Wert (`GG-DATA-003`).
    """

    def __init__(self) -> None:
        super().__init__("NaN/Infinity not allowed in canonical output")


class NonStringDictKeyError(CanonicalSerializationError):
    """Dict-Schluessel MUESSEN `str` sein."""

    def __init__(self) -> None:
        super().__init__("dict keys must be str")


class UnsupportedTypeError(CanonicalSerializationError):
    """Typ der Eingabe liegt ausserhalb des erlaubten Wertebereichs."""

    def __init__(self, type_name: str) -> None:
        super().__init__(f"unsupported type: {type_name}")


class SurrogateNotAllowedError(CanonicalSerializationError):
    """Unpaartes Surrogate-Codepoint (U+D800..U+DFFF) im String.

    Weder gueltiges UTF-8 noch gueltiges JSON (`RFC 8259 §7`).
    Adapter, die rohe Bytes hochheben, muessen Surrogate vorher
    bereinigen.
    """

    def __init__(self) -> None:
        super().__init__("surrogate code points are not allowed in canonical output")


class CircularReferenceError(CanonicalSerializationError):
    """Selbst-referenzierende Datenstruktur (z. B. `a = []; a.append(a)`).

    `canonical_json` ist deterministisch und endlich — Zyklen wuerden
    in unbegrenzter Rekursion enden. Domain-Code darf solche Strukturen
    nicht an den Encoder weitergeben.
    """

    def __init__(self) -> None:
        super().__init__("circular reference detected in input")


def canonical_json(value: object) -> bytes:
    """Serialisiert `value` deterministisch nach UTF-8-Bytes.

    Erlaubte Eingabe-Typen: `None`, `bool`, `int`, `Decimal`, `str`,
    `dict[str, ...]`, `list[...]`, `tuple[...]`.

    Verboten: `float` (`FloatNotAllowedError`),
    `Decimal("NaN")`/`Decimal("Infinity")` (`NonFiniteDecimalError`),
    `bytes` und andere unbekannte Typen (`UnsupportedTypeError`),
    Dict-Keys die nicht `str` sind (`NonStringDictKeyError`),
    Surrogate-Codepoints in Strings (`SurrogateNotAllowedError`),
    selbst-referenzierende Container (`CircularReferenceError`).

    Eigenschaften:
    - Deterministisch by-construction: Dict-Schluessel werden
      lexikographisch sortiert; Listen-/Tuple-Reihenfolge bleibt
      erhalten; `Decimal(-0)` wird zu `Decimal(0)` normalisiert
      (byte-Stabilitaet ueber Vorzeichen).
    - `Decimal` wird in Fixed-Point-Notation (`format(d, "f")`)
      emittiert; Tail-Nullen bleiben erhalten (Quantisierung
      gehoert an die Domain-Eingangsgrenze).
    - Strings folgen RFC 8259 (Steuerzeichen werden zu `\\u00XX`).
    """
    parts: list[str] = []
    _emit(value, parts, seen=set())
    return "".join(parts).encode("utf-8")


def _emit(value: object, out: list[str], seen: set[int]) -> None:
    """Dispatched recursively auf den Type von `value`.

    `seen` traegt `id()` der gerade in Bearbeitung befindlichen
    Container, damit `CircularReferenceError` deterministisch frueh
    feuert statt am Python-Rekursionslimit zu sterben.

    Thread-Affinitaet: `seen` wird durch den Call-Stack einer einzelnen
    `canonical_json`-Invocation gereicht. Gemeinsame Nutzung ueber
    Threads ist NICHT unterstuetzt — wer `_emit` als privates Sub-API
    aus mehreren Threads ansprechen will, muss pro Thread ein eigenes
    `seen`-Set anlegen.
    """
    if value is None:
        out.append("null")
    elif value is True:
        out.append("true")
    elif value is False:
        out.append("false")
    elif isinstance(value, int):
        # `bool` wird oben per Identitaet behandelt; eigene
        # Unterklassen von `bool` fallen hier rein und werden als
        # Integer emittiert (Python-Standard-Verhalten).
        out.append(str(value))
    elif isinstance(value, Decimal):
        _emit_decimal(value, out)
    elif isinstance(value, str):
        out.append(_emit_string(value))
    elif isinstance(value, dict):
        _emit_dict(value, out, seen)
    elif isinstance(value, list | tuple):
        _emit_array(value, out, seen)
    elif isinstance(value, float):
        raise FloatNotAllowedError
    else:
        raise UnsupportedTypeError(type(value).__name__)


def _emit_decimal(value: Decimal, out: list[str]) -> None:
    """Emittiert einen `Decimal` in Fixed-Point-Notation.

    Vor-Bedingung (Domain-Eingangsgrenze, NICHT hier geprueft):
    Decimals werden auf max. 6 Nachkommastellen quantisiert ueber
    `Decimal(str(value)).quantize(Decimal("0.000001"),
    rounding=ROUND_HALF_EVEN)`. Eingaben mit grossem negativem
    Exponent (z. B. `Decimal("0E-100")`) wuerden hier 100-stellige
    Strings emittieren — moeglich, aber unter Annahme der
    Quantisierung nicht erreichbar.
    """
    if not value.is_finite():
        raise NonFiniteDecimalError
    # Signed-Zero-Normalisierung: `Decimal("-0")` → `Decimal("0")`,
    # `Decimal("-0.0")` → `Decimal("0.0")`. Verhindert, dass
    # semantisch identische Nullen byte-distinkt serialisiert werden
    # (Determinismus-Invariante GG-DATA-005).
    if value.is_zero():
        value = value.copy_abs()
    out.append(format(value, "f"))


def _emit_dict(value: dict[Any, Any], out: list[str], seen: set[int]) -> None:
    container_id = id(value)
    if container_id in seen:
        raise CircularReferenceError
    seen.add(container_id)
    try:
        sorted_keys: list[str] = []
        for key in value:
            if not isinstance(key, str):
                raise NonStringDictKeyError
            sorted_keys.append(key)
        sorted_keys.sort()
        out.append("{")
        for index, key in enumerate(sorted_keys):
            if index:
                out.append(",")
            out.append(_emit_string(key))
            out.append(":")
            _emit(value[key], out, seen)
        out.append("}")
    finally:
        seen.discard(container_id)


def _emit_array(
    value: list[Any] | tuple[Any, ...], out: list[str], seen: set[int]
) -> None:
    container_id = id(value)
    if container_id in seen:
        raise CircularReferenceError
    seen.add(container_id)
    try:
        out.append("[")
        for index, item in enumerate(value):
            if index:
                out.append(",")
            _emit(item, out, seen)
        out.append("]")
    finally:
        seen.discard(container_id)


def _emit_string(text: str) -> str:
    """Emittiert einen JSON-String (RFC 8259).

    Wird sowohl fuer Dict-Keys (in `_emit_dict`) als auch fuer
    String-Werte (in `_emit`) verwendet. Der Surrogate-Check greift in
    beiden Pfaden — Surrogate-Codepoints in Keys oder Werten werden
    gleichermassen mit `SurrogateNotAllowedError` abgelehnt.
    """
    buf: list[str] = ['"']
    for char in text:
        if char in _ESCAPE_MAP:
            buf.append(_ESCAPE_MAP[char])
        elif _SURROGATE_LOW <= ord(char) <= _SURROGATE_HIGH:
            raise SurrogateNotAllowedError
        elif ord(char) < _CONTROL_CHAR_THRESHOLD:
            buf.append(f"\\u{ord(char):04x}")
        else:
            buf.append(char)
    buf.append('"')
    return "".join(buf)
