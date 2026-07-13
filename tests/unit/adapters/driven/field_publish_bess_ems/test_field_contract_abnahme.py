"""S3-Abnahme: der bess-ems-Encoder gegen den **vollstaendigen** vendored Feldvertrag
(Slice 077 S3, ADR 0078 §2.6).

Zwei Achsen, systematisch ueber ALLE Frame-Typen:

1. **Schema-Validate** — der `telemetry`-Frame erfuellt `$defs.telemetry` (exakt die
   `required`-Felder, jeder Feld-JSON-Typ, **keine** Extra-Felder); der `command_ack`
   erfuellt `$defs.command_ack`.
2. **Struktureller Golden-Vergleich** — je Golden-Case (`telemetry-nominal`/`-charging`,
   `status-nominal`, `fault-active`, `fault-suppressed-ok`, `command-ack-accepted-echo`)
   produziert der Encoder ein struktur-gleiches Objekt (Feld-Praesenz/Namen + JSON-Typen;
   **nicht** wertgenau, ADR 0078 §2.6).

Der *autoritative* Beleg, dass die Frames wirklich bess-ems-konform sind, ist der
MQTT-only-E2E (`deploy/compose.bess-ems-sut.yml` + `deploy/scripts/bess-ems-sut-e2e.sh`):
die unveraenderte bess-ems-EMS konsumiert die Frames + verlaesst den Safety-Fallback.
Dieser Unit-Test ist der CI-Regression-Guard fuer dieselbe Konformitaet.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from grid_gym.adapters.driven.field_publish_bess_ems import (
    encode_command_ack,
    encode_fault,
    encode_status,
    encode_telemetry,
)

_FIXTURES = Path(__file__).parent / "fixtures"
_SCHEMA: dict[str, Any] = json.loads(
    (_FIXTURES / "mqtt-telemetry-envelope.schema.json").read_text(encoding="utf-8")
)
_GOLDEN: dict[str, Any] = json.loads(
    (_FIXTURES / "mqtt-golden-vectors.field.v1.json").read_text(encoding="utf-8")
)

_FULL_METRICS: dict[str, Decimal] = {
    "soc_pct": Decimal("60.500000"),
    "power_kw": Decimal("0.000000"),
    "dc_voltage": Decimal("800.000000"),
    "soh_percent": Decimal("99.000000"),
    "reactive_power_kvar": Decimal("0.000000"),
    "temperature_celsius": Decimal("22.000000"),
}


def _golden(name: str) -> dict[str, Any]:
    return next(c for c in _GOLDEN["cases"] if c["name"] == name)


def _def(name: str) -> dict[str, Any]:
    return _SCHEMA["$defs"][name]


def _json_type_ok(value: object, schema_type: str) -> bool:
    if schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "number":  # unsere Zahlen sind Decimal → canonical_json-Zahl
        return isinstance(value, Decimal)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "null":  # nullable Felder (z. B. command_ack.reason: [null,string])
        return value is None
    return False


def _validate_against_def(frame: dict[str, object], def_name: str) -> None:
    """Prueft `frame` gegen `$defs.<def_name>`: alle `required` present + typ-korrekt,
    jedes Feld in `properties`, **keine** Extra-Felder (additionalProperties=false-Geist)."""
    schema = _def(def_name)
    props: dict[str, Any] = schema["properties"]
    for req in schema["required"]:
        assert req in frame, f"{def_name}: Pflichtfeld {req!r} fehlt"
    extra = set(frame.keys()) - set(props.keys())
    assert not extra, f"{def_name}: unerwartete Felder {extra}"
    for field, value in frame.items():
        spec = props[field]
        types = spec["type"] if isinstance(spec["type"], list) else [spec["type"]]
        assert any(_json_type_ok(value, t) for t in types), f"{def_name}.{field}: {value!r}"


# --- Achse 1: Schema-Validate --------------------------------------------------


def test_telemetry_frame_validates_against_schema_def() -> None:
    frame = encode_telemetry(
        "single-bess-1", 1000, _FULL_METRICS, available=True, fault_status="ok"
    )
    _validate_against_def(frame, "telemetry")
    assert set(frame.keys()) == set(_def("telemetry")["required"])  # exakt 10, keine Luecke


def test_command_ack_validates_against_schema_def() -> None:
    ack = encode_command_ack("cmd-1", "2026-07-13T10:00:00Z")
    _validate_against_def(ack, "command_ack")


# --- Achse 2: struktureller Golden-Vergleich (alle Cases) ----------------------


def test_telemetry_nominal_matches_golden() -> None:
    frame = encode_telemetry("single-bess-1", 0, _FULL_METRICS, available=True, fault_status="ok")
    _assert_structural(frame, _golden("telemetry-nominal")["payload"])


def test_telemetry_charging_matches_golden() -> None:
    # grid-gym laedt mit +power_kw → active_power_kw negativ (Golden `telemetry-charging`).
    charging = {**_FULL_METRICS, "power_kw": Decimal("250.000000")}
    frame = encode_telemetry("single-bess-1", 0, charging, available=True, fault_status="ok")
    golden = _golden("telemetry-charging")["payload"]
    _assert_structural(frame, golden)
    assert frame["active_power_kw"] < 0  # Vorzeichen-Flip, wie im Golden


def test_status_nominal_matches_golden() -> None:
    frame = encode_status(0, available=True, fault_status="ok")
    _assert_structural(frame, _golden("status-nominal")["payload"])


def test_fault_active_matches_golden() -> None:
    frame = encode_fault(0, fault_status="cell_failure")
    assert frame is not None
    _assert_structural(frame, _golden("fault-active")["payload"])


def test_fault_suppressed_ok_produces_no_message() -> None:
    # Golden `fault-suppressed-ok`: bei `fault_status=ok` KEINE Nachricht auf dem Draht.
    case = _golden("fault-suppressed-ok")
    assert "payload" not in case or case.get("payload") is None
    assert encode_fault(0, fault_status="ok") is None


def test_command_ack_matches_golden() -> None:
    ack = encode_command_ack("cmd-golden-nominal", "1970-01-01T00:00:00Z")
    _assert_structural(ack, _golden("command-ack-accepted-echo")["payload"])


def _assert_structural(frame: dict[str, object], golden_payload: dict[str, Any]) -> None:
    """Feld-Praesenz/Namen gleich + je Feld JSON-Typ-vertraeglich mit dem Golden-Wert
    (nicht wertgenau, ADR 0078 §2.6)."""
    assert set(frame.keys()) == set(golden_payload.keys())
    for field, golden_value in golden_payload.items():
        assert _same_json_kind(frame[field], golden_value), (
            f"{field}: {frame[field]!r} vs golden {golden_value!r}"
        )


def _same_json_kind(value: object, golden_value: object) -> bool:
    # Der Golden-Vergleich prueft Feld-**Praesenz/Namen** + grobe JSON-Art; der strikte
    # Typ-Pin (integer vs number) lebt in Achse 1 (Schema-Validate). Ein Golden-JSON-`int`
    # ist mehrdeutig (integer-Feld `offset_millis` ODER number-Feld mit ganzzahligem
    # Wert wie `dc_current: 0`) — daher hier lenient int ODER Decimal.
    if isinstance(golden_value, bool):
        return isinstance(value, bool)
    if isinstance(golden_value, str):
        return isinstance(value, str)
    if isinstance(golden_value, int):
        return isinstance(value, (int, Decimal)) and not isinstance(value, bool)
    if isinstance(golden_value, float):  # number-Feld → unsere Decimal
        return isinstance(value, Decimal)
    return False


# Golden-Cases MIT Nachricht (payload), die oben je eine eigene Assertion haben.
_COVERED_MESSAGE_CASES = frozenset(
    {
        "telemetry-nominal",
        "telemetry-charging",
        "status-nominal",
        "fault-active",
        "command-ack-accepted-echo",
    }
)


def test_all_message_bearing_golden_cases_are_covered() -> None:
    # Drift-Guard: ein neuer/entfernter Golden-Message-Case (Vertrags-Bump) muss die
    # Abnahme oben nachziehen (Closure-Review LOW-c). `fault-suppressed-ok` traegt
    # bewusst KEINE payload → nicht in der Menge.
    with_payload = {c["name"] for c in _GOLDEN["cases"] if c.get("payload") is not None}
    assert with_payload == _COVERED_MESSAGE_CASES, (
        "Golden-Message-Cases verschoben — Abnahme anpassen: "
        f"golden={sorted(with_payload)} covered={sorted(_COVERED_MESSAGE_CASES)}"
    )
