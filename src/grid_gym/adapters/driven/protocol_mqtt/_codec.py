"""MQTT-Payload-Codec (M4 Welle 2, ADR 0031 §2.2).

Decision 4b: `canonical_json` (M2-Welle-0a-Stand, Trigger 014-Quelle)
fuer Encoding. Dekodierung ueber Standard-`json.loads` mit
`parse_float=Decimal`-Hook, damit `TelemetryPoint.value` (Decimal)
nicht durch einen Float-Zwischenschritt verlustbehaftet wird.

Asymmetrie (Pattern uebernommen vom Snapshot-Codec aus Trigger 014):

- **Encoding ist strikt** — `canonical_json` wirft typed
  Exceptions bei verbotenen Typen (z. B. `FloatNotAllowedError`),
  sodass Adapter-Aufrufer Fehler sofort sichtbar bekommen.
- **Dekodierung ist tolerant** — `json.loads` akzeptiert standard-
  JSON; fehlende Pflicht-Felder oder Type-Mismatch landen als
  `MqttCodecDecodeError` (Welle-2-Surface).

Welle-2-Surface-Minimum: Encode/Decode pro Telemetry + Command.
Welle 3 (Modbus) und Welle 4 (OPC-UA) bauen eigene Codec-Module;
das hier ist MQTT-spezifisch.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Final, TypeVar, cast

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.serialization.canonical import canonical_json

_EnumT = TypeVar("_EnumT", Quality, CommandResult)


_TELEMETRY_FIELDS: Final[tuple[str, ...]] = (
    "run_id",
    "tick",
    "simulation_time",
    "device_id",
    "metric",
    "value",
    "unit",
    "quality",
    "source",
    "sequence",
)

_COMMAND_FIELDS: Final[tuple[str, ...]] = (
    "command_id",
    "simulation_time",
    "target_device_id",
    "type",
    "payload",
    "validation_status",
    "result",
)


class MqttCodecError(ValueError):
    """Base-Klasse fuer MQTT-Codec-Fehler (ADR 0031 §2.2).

    Encode-Fehler delegieren an `canonical_json` (eigene Hierarchie);
    diese Klasse adressiert nur **Decode-Fehler** auf der MQTT-
    Adapter-Seite (Empfang-Pfad).
    """


class MqttCodecDecodeError(MqttCodecError):
    """Decode der Payload ist fehlgeschlagen (Top-Level)."""


class MqttCodecJsonDecodeError(MqttCodecDecodeError):
    """Payload ist nicht als JSON parsbar."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"MQTT-Payload ist nicht JSON: {reason}")
        self.reason: str = reason


class MqttCodecUtf8DecodeError(MqttCodecDecodeError):
    """Payload ist nicht als UTF-8 decodierbar.

    Spezialfall von `MqttCodecJsonDecodeError`, weil paho-mqtt
    `bytes` liefert und `json.loads` sie intern decoded — wenn das
    schon dort scheitert, ist es ein UTF-8-Problem, kein JSON-
    Strukturproblem.
    """

    def __init__(self, cause: UnicodeDecodeError) -> None:
        super().__init__(f"MQTT-Payload ist nicht UTF-8: {cause}")
        self.cause: UnicodeDecodeError = cause


class MqttCodecPayloadShapeError(MqttCodecDecodeError):
    """Payload-Top-Level ist kein JSON-Objekt (Mapping)."""

    def __init__(self, observed_type: str) -> None:
        super().__init__(
            f"MQTT-Payload-Top-Level muss ein JSON-Objekt sein, war {observed_type!r}."
        )
        self.observed_type: str = observed_type


class MqttCodecMissingFieldError(MqttCodecDecodeError):
    """Pflicht-Feld fehlt in der Payload."""

    def __init__(self, field_name: str, present_fields: tuple[str, ...]) -> None:
        present = ", ".join(sorted(present_fields)) or "<keine>"
        super().__init__(f"MQTT-Payload: Pflicht-Feld {field_name!r} fehlt (vorhanden: {present}).")
        self.field_name: str = field_name


class MqttCodecInvalidEnumError(MqttCodecDecodeError):
    """Enum-String-Wert ist nicht in der `Quality`/`CommandResult`-Domain."""

    def __init__(self, field_name: str, value: object, allowed: tuple[str, ...]) -> None:
        allowed_str = ", ".join(sorted(allowed))
        super().__init__(
            f"MQTT-Payload: Feld {field_name!r}={value!r} ist kein "
            f"gueltiger Enum-Wert (erlaubt: {allowed_str})."
        )
        self.field_name: str = field_name


def encode_telemetry(point: TelemetryPoint) -> bytes:
    """Serialisiert `point` deterministisch nach UTF-8-JSON-Bytes
    (ADR 0031 §2.2).

    Felder werden direkt auf JSON-Keys gemappt; `Decimal`/`StrEnum`
    fallen in den `canonical_json`-Standard-Pfad. Determinismus
    by-construction (Trigger 014-Quelle).
    """
    payload: dict[str, object] = {
        "run_id": point.run_id,
        "tick": point.tick,
        "simulation_time": point.simulation_time,
        "device_id": point.device_id,
        "metric": point.metric,
        "value": point.value,
        "unit": point.unit,
        "quality": point.quality.value,
        "source": point.source,
        "sequence": point.sequence,
    }
    return canonical_json(payload)


def encode_command(command: Command) -> bytes:
    """Serialisiert `command` deterministisch nach UTF-8-JSON-Bytes
    (ADR 0031 §2.2).

    `Command.payload` ist bereits `Mapping[str, object]` mit
    `canonical_json`-kompatiblen Werten (siehe `command.py`-
    Docstring); wir kopieren das Mapping in ein normales `dict`,
    damit `canonical_json` es sicher iterieren kann.
    """
    payload: dict[str, object] = {
        "command_id": command.command_id,
        "simulation_time": command.simulation_time,
        "target_device_id": command.target_device_id,
        "type": command.type,
        "payload": dict(command.payload),
        "validation_status": command.validation_status,
        "result": command.result.value,
    }
    return canonical_json(payload)


def decode_telemetry(payload_bytes: bytes) -> TelemetryPoint:
    """Dekodiert UTF-8-JSON-Bytes zurueck zu `TelemetryPoint`.

    Numerische Werte werden ueber `parse_float=Decimal` direkt nach
    `Decimal` decodiert (sonst waere `point.value` durch einen
    Float-Zwischenschritt verlustbehaftet — siehe Trigger 014).
    """
    data = _parse_json_object(payload_bytes, _TELEMETRY_FIELDS)
    quality_value = _require_field(data, "quality")
    quality = _parse_enum_value(Quality, "quality", quality_value)
    return TelemetryPoint(
        run_id=_require_str(data, "run_id"),
        tick=_require_int(data, "tick"),
        simulation_time=_require_int(data, "simulation_time"),
        device_id=_require_str(data, "device_id"),
        metric=_require_str(data, "metric"),
        value=_require_decimal(data, "value"),
        unit=_require_str(data, "unit"),
        quality=quality,
        source=_require_str(data, "source"),
        sequence=_require_int(data, "sequence"),
    )


def decode_command(payload_bytes: bytes) -> Command:
    """Dekodiert UTF-8-JSON-Bytes zurueck zu `Command`.

    Symmetrisch zu `encode_command`. `payload`-Inhalt wird als
    `Mapping[str, object]` gehalten (kein Schema-Check auf
    Sub-Feldern; Welle-3+-Adapter koennen schaerfen).
    """
    data = _parse_json_object(payload_bytes, _COMMAND_FIELDS)
    result_value = _require_field(data, "result")
    result = _parse_enum_value(CommandResult, "result", result_value)
    inner_payload = _require_mapping(data, "payload")
    return Command(
        command_id=_require_str(data, "command_id"),
        simulation_time=_require_int(data, "simulation_time"),
        target_device_id=_require_str(data, "target_device_id"),
        type=_require_str(data, "type"),
        payload=inner_payload,
        validation_status=_require_str(data, "validation_status"),
        result=result,
    )


def _parse_json_object(payload_bytes: bytes, expected_fields: tuple[str, ...]) -> dict[str, object]:
    """Parst Bytes als JSON-Objekt; wirft typed Fehler bei Fehlschlag."""
    try:
        raw = json.loads(payload_bytes, parse_float=Decimal)
    except json.JSONDecodeError as exc:
        raise MqttCodecJsonDecodeError(str(exc)) from exc
    except UnicodeDecodeError as exc:
        raise MqttCodecUtf8DecodeError(exc) from exc
    if not isinstance(raw, dict):
        raise MqttCodecPayloadShapeError(type(raw).__name__)
    # Fruehe Pflicht-Field-Pruefung gibt klare Fehler statt KeyError
    # tief im Konstruktor.
    present = tuple(raw.keys())
    for field_name in expected_fields:
        if field_name not in raw:
            raise MqttCodecMissingFieldError(field_name, present)
    return cast(dict[str, object], raw)


def _require_field(data: dict[str, object], field_name: str) -> object:
    """Liest ein Pflicht-Feld; KeyError waere ein Programmier-Fehler
    nach `_parse_json_object`-Vor-Check, deshalb hier `cast`-frei."""
    return data[field_name]


def _require_str(data: dict[str, object], field_name: str) -> str:
    value = _require_field(data, field_name)
    if not isinstance(value, str):
        raise MqttCodecMissingFieldError(field_name, tuple(data.keys()))
    return value


def _require_int(data: dict[str, object], field_name: str) -> int:
    value = _require_field(data, field_name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise MqttCodecMissingFieldError(field_name, tuple(data.keys()))
    return value


def _require_decimal(data: dict[str, object], field_name: str) -> Decimal:
    value = _require_field(data, field_name)
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise MqttCodecMissingFieldError(field_name, tuple(data.keys()))
    if isinstance(value, int):
        return Decimal(value)
    raise MqttCodecMissingFieldError(field_name, tuple(data.keys()))


def _require_mapping(data: dict[str, object], field_name: str) -> dict[str, object]:
    value = _require_field(data, field_name)
    if not isinstance(value, dict):
        raise MqttCodecMissingFieldError(field_name, tuple(data.keys()))
    return cast(dict[str, object], value)


def _parse_enum_value(
    enum_cls: type[_EnumT],
    field_name: str,
    raw_value: object,
) -> _EnumT:
    if not isinstance(raw_value, str):
        allowed = tuple(member.value for member in enum_cls)
        raise MqttCodecInvalidEnumError(field_name, raw_value, allowed)
    try:
        return enum_cls(raw_value)
    except ValueError as exc:
        allowed = tuple(member.value for member in enum_cls)
        raise MqttCodecInvalidEnumError(field_name, raw_value, allowed) from exc
