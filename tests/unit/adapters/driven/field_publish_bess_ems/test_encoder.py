"""Tests fuer den reinen bess-ems-Feldvertrags-Encoder (Slice 077 S2a, ADR 0078).

Validiert **strukturell** gegen die vendored bess-ems-Fixtures (`fixtures/`,
Provenienz s. `PROVENANCE.md`): das Envelope-**Schema** ist die Typ-Autoritaet, die
**Golden-Vektoren** liefern die Feld-Praesenz (nicht wertgenau, ADR 0078 §2.6).
Zusaetzlich exakte Feld-Mapping-Pins (Flip/derive/rename) + fail-fast + die
`canonical_json`-Serialisierbarkeit (JSON-Zahlen, kein float).
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from grid_gym.adapters.driven.field_publish_bess_ems import (
    BessEmsEncoderMissingMetricError,
    command_id_from_payload,
    encode_command_ack,
    encode_fault,
    encode_status,
    encode_telemetry,
)
from grid_gym.hexagon.core.serialization.canonical import canonical_json

_FIXTURES = Path(__file__).parent / "fixtures"
_SCHEMA: dict[str, Any] = json.loads(
    (_FIXTURES / "mqtt-telemetry-envelope.schema.json").read_text(encoding="utf-8")
)
_GOLDEN: dict[str, Any] = json.loads(
    (_FIXTURES / "mqtt-golden-vectors.field.v1.json").read_text(encoding="utf-8")
)


def _telemetry_schema() -> dict[str, Any]:
    return _SCHEMA["$defs"]["telemetry"]


def _golden_payload(name: str) -> dict[str, Any]:
    case = next(c for c in _GOLDEN["cases"] if c["name"] == name)
    return case["payload"]


def _metrics(**over: Decimal) -> dict[str, Decimal]:
    """Vollstaendiger Battery-Metrik-Satz (alle Field-Envelope-Bloecke aktiv)."""
    base = {
        "soc_pct": Decimal("60.500000"),
        "power_kw": Decimal("0.000000"),
        "dc_voltage": Decimal("800.000000"),
        "soh_percent": Decimal("99.000000"),
        "reactive_power_kvar": Decimal("0.000000"),
        "temperature_celsius": Decimal("22.000000"),
    }
    return {**base, **over}


def _json_type_ok(value: object, schema_type: str) -> bool:
    if schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "number":  # unsere Zahlen sind Decimal (-> canonical_json-Zahl)
        return isinstance(value, Decimal)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "string":
        return isinstance(value, str)
    return False


# --- strukturell gegen Schema + Golden -------------------------------------


def test_telemetry_frame_covers_schema_required_with_correct_types() -> None:
    frame = encode_telemetry("asset-1", 0, _metrics(), available=True, fault_status="ok")
    schema = _telemetry_schema()
    assert set(frame.keys()) == set(schema["required"])  # alle 10 Pflichtfelder
    for field, spec in schema["properties"].items():
        assert _json_type_ok(frame[field], spec["type"]), f"{field}: {frame[field]!r}"


def test_telemetry_frame_field_presence_matches_golden() -> None:
    frame = encode_telemetry("asset-1", 0, _metrics(), available=True, fault_status="ok")
    assert set(frame.keys()) == set(_golden_payload("telemetry-nominal").keys())


def test_status_frame_matches_golden_structure() -> None:
    frame = encode_status(0, available=True, fault_status="ok")
    assert set(frame.keys()) == set(_golden_payload("status-nominal").keys())
    assert frame == {"available": True, "fault_status": "ok", "offset_millis": 0}


def test_fault_frame_matches_golden_structure() -> None:
    frame = encode_fault(2000, fault_status="overtemperature")
    assert frame is not None
    assert set(frame.keys()) == set(_golden_payload("fault-active").keys())


# --- Feld-Mapping-Pins (Flip / derive / rename / offset) --------------------


def test_field_mapping_pins() -> None:
    # Laden mit +250 kW -> active_power_kw = -250; dc_current = -250*1000/800 = -312.5.
    frame = encode_telemetry(
        "asset-1",
        1000,
        _metrics(power_kw=Decimal("250.000000"), soc_pct=Decimal("61.200000")),
        available=True,
        fault_status="ok",
    )
    assert frame["offset_millis"] == 1000
    assert frame["soc_percent"] == Decimal("61.200000")  # rename
    assert frame["active_power_kw"] == Decimal("-250.000000")  # Vorzeichen-Flip
    assert frame["dc_current"] == Decimal("-312.500000")  # abgeleitet
    assert frame["dc_voltage"] == Decimal("800.000000")
    assert frame["available"] is True
    assert frame["fault_status"] == "ok"


def test_active_power_and_dc_current_sign_on_discharge() -> None:
    # Entladen (grid-gym power -100) -> active_power_kw = +100, dc_current = +125.
    frame = encode_telemetry(
        "asset-1",
        0,
        _metrics(power_kw=Decimal("-100.000000")),
        available=True,
        fault_status="ok",
    )
    assert frame["active_power_kw"] == Decimal("100.000000")
    assert frame["dc_current"] == Decimal("125.000000")  # 100*1000/800


def test_offset_millis_is_int() -> None:
    frame = encode_telemetry("asset-1", 3600000, _metrics(), available=True, fault_status="ok")
    assert isinstance(frame["offset_millis"], int)


# --- fail-fast + Suppression -----------------------------------------------


def test_missing_required_metric_fails_fast() -> None:
    incomplete = _metrics()
    del incomplete["dc_voltage"]
    with pytest.raises(BessEmsEncoderMissingMetricError) as exc:
        encode_telemetry("asset-1", 0, incomplete, available=True, fault_status="ok")
    assert exc.value.asset_id == "asset-1"
    assert "dc_voltage" in exc.value.missing


@pytest.mark.parametrize("suppressed", ["ok", ""])
def test_fault_suppressed_for_ok_and_empty(suppressed: str) -> None:
    assert encode_fault(2000, fault_status=suppressed) is None


def test_fault_emitted_for_active_status() -> None:
    assert encode_fault(2000, fault_status="cell_failure") == {
        "fault_status": "cell_failure",
        "offset_millis": 2000,
    }


# --- Encoding-Vertrag: JSON-Zahlen (kein float) ----------------------------


def test_frame_is_canonical_json_serializable() -> None:
    # `Decimal` (<=6dp) + int + bool + str -> canonical_json ok (JSON-Zahlen, kein
    # float/String-Bruch gegen das Schema-`number`).
    frame = encode_telemetry(
        "asset-1", 0, _metrics(power_kw=Decimal("250.000000")), available=True, fault_status="ok"
    )
    canonical_json(frame)  # kein Raise


# --- command_ack-Echo (ADR 0078 §2.9) --------------------------------------


def _command_ack_schema() -> dict[str, Any]:
    return _SCHEMA["$defs"]["command_ack"]


def test_command_ack_covers_schema_required_with_correct_types() -> None:
    ack = encode_command_ack("cmd-1", "1970-01-01T00:00:00Z")
    schema = _command_ack_schema()
    assert set(schema["required"]) <= set(ack.keys())  # alle Pflichtfelder vorhanden
    assert isinstance(ack["command_id"], str)
    assert isinstance(ack["accepted"], bool)
    assert isinstance(ack["dispatched_at"], str)  # ISO-8601-String, keine Zahl


def test_command_ack_field_presence_matches_golden() -> None:
    ack = encode_command_ack("cmd-golden-nominal", "1970-01-01T00:00:00Z")
    assert set(ack.keys()) == set(_golden_payload("command-ack-accepted-echo").keys())
    assert ack["accepted"] is True
    assert ack["reason"] == "accepted"


def test_command_ack_echoes_command_id() -> None:
    ack = encode_command_ack("cmd-xyz", "2026-07-13T10:00:00Z")
    assert ack["command_id"] == "cmd-xyz"
    assert ack["dispatched_at"] == "2026-07-13T10:00:00Z"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"command_id": "cmd-9", "mode": "power"}, "cmd-9"),
        ({"mode": "power"}, None),  # command_id fehlt
        ({"command_id": ""}, None),  # leer
        ({"command_id": 42}, None),  # falscher Typ
    ],
)
def test_command_id_from_payload(payload: dict[str, Any], expected: str | None) -> None:
    assert command_id_from_payload(payload) == expected
