"""Unit-Tests fuer `InMemoryTelemetrySink` (M7 Welle 1a, ADR 0047).

Pinnt den `TelemetrySinkPort`-Vertrag fuer die in-memory-Variante:
append-only, Insertion-Reihenfolge, Per-`run_id`-Filterung,
verlustfreier `TelemetryPoint`-Roundtrip. Der Postgres-Adapter
wird separat im Integration-Smoke
(`tests/integration/test_mvp_002_timeseries_persistence_smoke.py`)
gegen echtes Postgres geprueft.
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.adapters.driven.persistence_inmemory import InMemoryTelemetrySink
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint


def _point(
    *,
    run_id: str = "run-1",
    simulation_time: int,
    device_id: str,
    sequence: int,
    value: str = "1.50",
) -> TelemetryPoint:
    return TelemetryPoint(
        run_id=run_id,
        tick=simulation_time // 1000,
        simulation_time=simulation_time,
        device_id=device_id,
        metric="power_kw",
        value=Decimal(value),
        unit="kW",
        quality=Quality.VALID,
        source=f"battery.{device_id}",
        sequence=sequence,
    )


def test_persist_then_read_ordered_preserves_insertion_order() -> None:
    sink = InMemoryTelemetrySink()
    # Tie bei gleicher simulation_time: zwei Geraete, beide sequence=0
    # → Insertion-Reihenfolge (battery-1 vor battery-2) muss erhalten
    # bleiben (Per-Device-sequence ist NICHT global eindeutig).
    points = [
        _point(simulation_time=1000, device_id="battery-1", sequence=0),
        _point(simulation_time=1000, device_id="battery-2", sequence=0),
        _point(simulation_time=2000, device_id="battery-1", sequence=0),
    ]
    sink.persist(points)
    assert sink.read_ordered("run-1") == tuple(points)


def test_persist_is_append_only_across_calls() -> None:
    sink = InMemoryTelemetrySink()
    first = _point(simulation_time=1000, device_id="battery-1", sequence=0)
    second = _point(simulation_time=2000, device_id="battery-1", sequence=0)
    sink.persist([first])
    sink.persist([second])
    # Wiederholtes persist haengt an (kein Overwrite); read liefert beide.
    assert sink.read_ordered("run-1") == (first, second)


def test_read_ordered_filters_by_run_id() -> None:
    sink = InMemoryTelemetrySink()
    a = _point(run_id="run-a", simulation_time=1000, device_id="battery-1", sequence=0)
    b = _point(run_id="run-b", simulation_time=1000, device_id="battery-1", sequence=0)
    sink.persist([a, b])
    assert sink.read_ordered("run-a") == (a,)
    assert sink.read_ordered("run-b") == (b,)


def test_empty_persist_is_noop() -> None:
    sink = InMemoryTelemetrySink()
    sink.persist([])
    assert sink.read_ordered("run-1") == ()


def test_decimal_value_roundtrips_lossless() -> None:
    sink = InMemoryTelemetrySink()
    point = _point(simulation_time=1000, device_id="battery-1", sequence=0, value="1.50")
    sink.persist([point])
    (read_back,) = sink.read_ordered("run-1")
    assert read_back.value == Decimal("1.50")
