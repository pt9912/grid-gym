"""Tests fuer den `TelemetryStreamPort`-Vertrag (M5 Welle 3, ADR 0038).

Pruefen nur die Port-Surface (Dataclass-Felder, Type-Aliases).
Implementierungs-Tests fuer `InMemoryTelemetryStream` leben
unter `tests/unit/adapters/driven/telemetry_stream_inmemory/`.
"""

from __future__ import annotations

from dataclasses import fields
from typing import get_args

import pytest

from grid_gym.hexagon.ports.driving.telemetry_stream import (
    TelemetryPoint,
    TelemetryQuality,
)


def test_telemetry_point_is_frozen_dataclass_with_slots() -> None:
    """Welle-3-Convention: `TelemetryPoint` ist immutable + slots-optimiert."""
    assert TelemetryPoint.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    point = TelemetryPoint(
        run_id="r0",
        device_id="battery-1",
        metric="power",
        value=12.5,
        unit="kW",
        simulation_time_ms=100,
        quality="ok",
        sequence=7,
    )
    assert point.run_id == "r0"
    # Value-Roundtrip ist exakt — `12.5` ist IEEE-754-exakt
    # darstellbar; eine `math.isclose`-Toleranz waere
    # ueberflussige Schutzschicht.
    assert point.value == pytest.approx(12.5)


def test_telemetry_point_field_names_match_gg_api_002() -> None:
    """`GG-API-002` + `GG-UI-002`-Akzeptanz: alle Felder vorhanden."""
    field_names = {f.name for f in fields(TelemetryPoint)}
    assert field_names == {
        "run_id",
        "device_id",
        "metric",
        "value",
        "unit",
        "simulation_time_ms",
        "quality",
        "sequence",
    }


def test_telemetry_quality_literal_covers_six_states() -> None:
    """`GG-UI-009`-Akzeptanz: 6 Quality-Zustaende."""
    assert set(get_args(TelemetryQuality)) == {
        "ok",
        "stale",
        "invalid",
        "nan",
        "missing",
        "fault_injected",
    }
