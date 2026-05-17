"""Frozen- und Canonical-Roundtrip-Tests fuer die M1-Domain-Klassen.

Property-Tests pruefen pro Klasse:
- Frozen-Garantie: Attribut-Set wirft `dataclasses.FrozenInstanceError`
  (Slice-Plan M1 Welle 1 §3).
- Canonical-Roundtrip-Stabilitaet: `canonical_json(asdict(obj))`
  liefert byte-stabile Ausgabe ueber wiederholte Konstruktion mit
  gleichen Feldern.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.event import Event
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.serialization.canonical import (
    FloatNotAllowedError,
    canonical_json,
)

# ---------------------------------------------------------------------------
# Strategien (deckungsgleich mit test_canonical.py)
# ---------------------------------------------------------------------------

# String-Werte ohne Surrogate (`canonical_json` lehnt sie ab).
_safe_text = st.text(alphabet=st.characters(blacklist_categories=("Cs",)))
_safe_dict_key = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)), min_size=1, max_size=16
)
_safe_decimal = st.decimals(
    min_value=Decimal("-1000000000"),
    max_value=Decimal("1000000000"),
    allow_nan=False,
    allow_infinity=False,
    places=6,
)
# Payload-Werte beschraenken sich auf die canonical-erlaubten Skalare;
# nested dicts/lists sind Welle-1-Out-of-Scope (Geraete-Payloads
# bringen das ggf. in M2).
_payload_scalar = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(2**31), max_value=2**31 - 1),
    _safe_decimal,
    _safe_text,
)
_payload = st.dictionaries(_safe_dict_key, _payload_scalar, max_size=4)
_quality = st.sampled_from(list(Quality))
_command_result = st.sampled_from(list(CommandResult))


# ---------------------------------------------------------------------------
# RunMetadata
# ---------------------------------------------------------------------------


@given(
    run_id=_safe_text,
    scenario_hash=_safe_text,
    schema_version=_safe_text,
    seed=st.integers(min_value=0, max_value=2**32 - 1),
    tick_ms=st.sampled_from([10, 100, 1000]),
    started_at=_safe_text,
    ended_at=_safe_text,
    tool_version=_safe_text,
)
def test_run_metadata_canonical_roundtrip_is_stable(
    run_id: str,
    scenario_hash: str,
    schema_version: str,
    seed: int,
    tick_ms: int,
    started_at: str,
    ended_at: str,
    tool_version: str,
) -> None:
    """Zwei identisch konstruierte `RunMetadata`-Instanzen ergeben
    byte-identische `canonical_json`-Ausgaben."""
    a = RunMetadata(
        run_id=run_id,
        scenario_hash=scenario_hash,
        schema_version=schema_version,
        seed=seed,
        tick_ms=tick_ms,
        started_at=started_at,
        ended_at=ended_at,
        tool_version=tool_version,
    )
    b = RunMetadata(
        run_id=run_id,
        scenario_hash=scenario_hash,
        schema_version=schema_version,
        seed=seed,
        tick_ms=tick_ms,
        started_at=started_at,
        ended_at=ended_at,
        tool_version=tool_version,
    )
    assert canonical_json(asdict(a)) == canonical_json(asdict(b))


def test_run_metadata_is_frozen() -> None:
    """Attribut-Set wirft `FrozenInstanceError` (AC-DOMAIN-FROZEN)."""
    meta = RunMetadata(
        run_id="r",
        scenario_hash="h",
        schema_version="v1",
        seed=0,
        tick_ms=100,
        started_at="2026-01-01T00:00:00Z",
        ended_at="2026-01-01T00:01:00Z",
        tool_version="0.1.0",
    )
    with pytest.raises(FrozenInstanceError):
        meta.seed = 1  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TelemetryPoint
# ---------------------------------------------------------------------------


@given(
    run_id=_safe_text,
    tick=st.integers(min_value=0, max_value=2**31 - 1),
    simulation_time=st.integers(min_value=0, max_value=2**31 - 1),
    device_id=_safe_text,
    metric=_safe_text,
    value=_safe_decimal,
    unit=_safe_text,
    quality=_quality,
    source=_safe_text,
    sequence=st.integers(min_value=0, max_value=2**31 - 1),
)
def test_telemetry_point_canonical_roundtrip_is_stable(
    run_id: str,
    tick: int,
    simulation_time: int,
    device_id: str,
    metric: str,
    value: Decimal,
    unit: str,
    quality: Quality,
    source: str,
    sequence: int,
) -> None:
    a = TelemetryPoint(
        run_id=run_id,
        tick=tick,
        simulation_time=simulation_time,
        device_id=device_id,
        metric=metric,
        value=value,
        unit=unit,
        quality=quality,
        source=source,
        sequence=sequence,
    )
    b = TelemetryPoint(
        run_id=run_id,
        tick=tick,
        simulation_time=simulation_time,
        device_id=device_id,
        metric=metric,
        value=value,
        unit=unit,
        quality=quality,
        source=source,
        sequence=sequence,
    )
    assert canonical_json(asdict(a)) == canonical_json(asdict(b))


def test_telemetry_point_is_frozen() -> None:
    point = TelemetryPoint(
        run_id="r",
        tick=0,
        simulation_time=0,
        device_id="d",
        metric="power",
        value=Decimal("0"),
        unit="kW",
        quality=Quality.VALID,
        source="bess",
        sequence=0,
    )
    with pytest.raises(FrozenInstanceError):
        point.tick = 1  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


@given(
    command_id=_safe_text,
    simulation_time=st.integers(min_value=0, max_value=2**31 - 1),
    target_device_id=_safe_text,
    type_=_safe_text,
    payload=_payload,
    validation_status=_safe_text,
    result=_command_result,
)
def test_command_canonical_roundtrip_is_stable(
    command_id: str,
    simulation_time: int,
    target_device_id: str,
    type_: str,
    payload: dict[str, object],
    validation_status: str,
    result: CommandResult,
) -> None:
    a = Command(
        command_id=command_id,
        simulation_time=simulation_time,
        target_device_id=target_device_id,
        type=type_,
        payload=payload,
        validation_status=validation_status,
        result=result,
    )
    b = Command(
        command_id=command_id,
        simulation_time=simulation_time,
        target_device_id=target_device_id,
        type=type_,
        payload=dict(payload),
        validation_status=validation_status,
        result=result,
    )
    assert canonical_json(asdict(a)) == canonical_json(asdict(b))


def test_command_is_frozen() -> None:
    cmd = Command(
        command_id="c",
        simulation_time=0,
        target_device_id="d",
        type="set_power_setpoint",
        payload={"setpoint_kw": Decimal("1.500000")},
        validation_status="validated",
        result=CommandResult.ACCEPTED,
    )
    with pytest.raises(FrozenInstanceError):
        cmd.result = CommandResult.REJECTED  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


@given(
    event_id=_safe_text,
    simulation_time=st.integers(min_value=0, max_value=2**31 - 1),
    source=_safe_text,
    target=_safe_text,
    type_=_safe_text,
    payload=_payload,
    priority=st.integers(min_value=-1000, max_value=1000),
    sequence=st.integers(min_value=0, max_value=2**31 - 1),
)
def test_event_canonical_roundtrip_is_stable(
    event_id: str,
    simulation_time: int,
    source: str,
    target: str,
    type_: str,
    payload: dict[str, object],
    priority: int,
    sequence: int,
) -> None:
    a = Event(
        event_id=event_id,
        simulation_time=simulation_time,
        source=source,
        target=target,
        type=type_,
        payload=payload,
        priority=priority,
        sequence=sequence,
    )
    b = Event(
        event_id=event_id,
        simulation_time=simulation_time,
        source=source,
        target=target,
        type=type_,
        payload=dict(payload),
        priority=priority,
        sequence=sequence,
    )
    assert canonical_json(asdict(a)) == canonical_json(asdict(b))


def test_event_is_frozen() -> None:
    event = Event(
        event_id="e",
        simulation_time=0,
        source="bess",
        target="grid",
        type="dispatch",
        payload={"setpoint_kw": Decimal("1.0")},
        priority=0,
        sequence=0,
    )
    with pytest.raises(FrozenInstanceError):
        event.priority = 1  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TickResult (M1 Welle 4)
# ---------------------------------------------------------------------------


def _make_event(event_id: str, simulation_time: int = 0) -> Event:
    return Event(
        event_id=event_id,
        simulation_time=simulation_time,
        source="src",
        target="tgt",
        type="tick",
        payload={},
        priority=0,
        sequence=0,
    )


def test_tick_result_is_frozen() -> None:
    result = TickResult(tick=0, simulation_time=0, popped_events=(), emitted_telemetry=())
    with pytest.raises(FrozenInstanceError):
        result.tick = 1  # type: ignore[misc]


def test_tick_result_canonical_roundtrip_is_stable_with_events() -> None:
    events = (_make_event("e1", 100), _make_event("e2", 200))
    a = TickResult(tick=3, simulation_time=200, popped_events=events, emitted_telemetry=())
    b = TickResult(tick=3, simulation_time=200, popped_events=events, emitted_telemetry=())
    assert canonical_json(asdict(a)) == canonical_json(asdict(b))


def test_tick_result_empty_emitted_telemetry_serialises_as_empty_array() -> None:
    """Welle 4 emittiert keine Telemetry — Feld bleibt leerer Tupel,
    `canonical_json` serialisiert das als `[]`."""
    result = TickResult(tick=0, simulation_time=0, popped_events=(), emitted_telemetry=())
    raw = canonical_json(asdict(result))
    assert b'"emitted_telemetry":[]' in raw


# ---------------------------------------------------------------------------
# Payload-Canonical-Vertrag — Negativ-Pfad
# ---------------------------------------------------------------------------
#
# Pinnt, dass `Command.payload`/`Event.payload` die Wertebereich-Verbote von
# `canonical_json` transitiv erben — Domain-Klassen fuehren keine eigene
# Payload-Validierung (Welle-1-Scope), aber jeder Versuch, ein nicht-canonical-
# faehiges Payload zu serialisieren, MUSS in einer typisierten Subklasse
# (`FloatNotAllowedError`) enden, nicht in `ValueError`/`TypeError`. M2+-
# Geraete-Payload-Validierung schaerft das spaeter; Welle 1 dokumentiert nur,
# dass der Domain-Pfad die Encoder-Vertrage nicht umgeht.


def test_command_with_float_payload_fails_canonical_serialization_typed() -> None:
    cmd = Command(
        command_id="c",
        simulation_time=0,
        target_device_id="d",
        type="set_power_setpoint",
        payload={"setpoint_kw": 1.5},  # type: ignore[dict-item]
        validation_status="validated",
        result=CommandResult.ACCEPTED,
    )
    with pytest.raises(FloatNotAllowedError):
        canonical_json(asdict(cmd))


def test_event_with_float_payload_fails_canonical_serialization_typed() -> None:
    event = Event(
        event_id="e",
        simulation_time=0,
        source="bess",
        target="grid",
        type="dispatch",
        payload={"setpoint_kw": 1.5},  # type: ignore[dict-item]
        priority=0,
        sequence=0,
    )
    with pytest.raises(FloatNotAllowedError):
        canonical_json(asdict(event))
