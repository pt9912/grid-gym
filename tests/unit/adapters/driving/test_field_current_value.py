"""Tests fuer `CurrentValueProjection` (Field-Server Pull-Seite, ADR 0075 §2.2).

Last-write-wins pro `(device_id, metric)` aus `TickResult.emitted_telemetry`;
tick-frame-atomar (Referenz-Swap); `snapshot()` liefert eine Kopie.
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.adapters.driving._field_current_value import CurrentValueProjection
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.domain.tick_result import TickResult


def _point(
    *,
    device_id: str = "meter-1",
    metric: str = "voltage_v",
    value: str = "230.5",
    sequence: int = 0,
) -> TelemetryPoint:
    return TelemetryPoint(
        run_id="run-1",
        tick=0,
        simulation_time=0,
        device_id=device_id,
        metric=metric,
        value=Decimal(value),
        unit="V",
        quality=Quality.VALID,
        source="smart_meter.meter-1",
        sequence=sequence,
    )


def _result(*points: TelemetryPoint) -> TickResult:
    return TickResult(
        tick=0,
        simulation_time=0,
        popped_events=(),
        emitted_telemetry=points,
        emitted_alarms=(),
    )


def test_latest_none_before_any_tick() -> None:
    proj = CurrentValueProjection()
    assert proj.latest("meter-1", "voltage_v") is None


def test_update_stores_last_value_per_target_metric() -> None:
    proj = CurrentValueProjection()
    proj.update_from_tick(_result(_point(value="1"), _point(device_id="meter-2", value="2")))
    proj.update_from_tick(_result(_point(value="3")))  # meter-1/voltage_v ueberschrieben
    p1 = proj.latest("meter-1", "voltage_v")
    p2 = proj.latest("meter-2", "voltage_v")
    assert p1 is not None
    assert p1.value == Decimal("3")  # last-write-wins
    assert p2 is not None
    assert p2.value == Decimal("2")  # unberuehrt


def test_empty_tick_is_noop_keeps_prior() -> None:
    proj = CurrentValueProjection()
    proj.update_from_tick(_result(_point()))
    proj.update_from_tick(_result())  # kein emitted_telemetry → No-op
    p = proj.latest("meter-1", "voltage_v")
    assert p is not None
    assert p.value == Decimal("230.5")


def test_snapshot_is_a_copy_frozen_against_later_updates() -> None:
    """Tick-frame-Atomizitaet: eine `snapshot()`-Kopie bleibt stabil, waehrend
    ein spaeterer Tick die Projektion (via Referenz-Swap) fortschreibt."""
    proj = CurrentValueProjection()
    proj.update_from_tick(_result(_point(value="230.5")))
    snap = proj.snapshot()
    proj.update_from_tick(_result(_point(value="9")))
    assert snap["meter-1", "voltage_v"].value == Decimal("230.5")  # Kopie unveraendert
    live = proj.latest("meter-1", "voltage_v")
    assert live is not None
    assert live.value == Decimal("9")  # Projektion fortgeschrieben
