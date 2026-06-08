"""Integration-Smoke fuer M7-Welle-1a (`GG-MVP-002` Zeitreihen-
Persistenz; ADR 0047).

Pinnt den `PostgresTelemetrySinkAdapter`-Vertrag gegen echtes
Postgres (testcontainers, Alembic-`0002_create_telemetry_points`):

- **Insertion-Reihenfolge bei Ties:** zwei Geraete mit gleicher
  `simulation_time` + gleicher (Per-Device-)`sequence` kommen in
  Persist-Reihenfolge zurueck (`ORDER BY id`) — NICHT interleaved.
- **Byte-Stabilitaet:** `value` als `TEXT`/`str(Decimal)` bewahrt
  die Scale (`1.50` bleibt `1.50`, nicht `1.5`) — Welle-1b-Replay-
  Diff-Vorbedingung.
- **Alle `GG-PERSIST-001`-/`TelemetryPoint`-Felder** round-trippen.
- **Append-only:** wiederholtes `persist` haengt an (kein
  Overwrite); Idempotenz-Wiederholungslesen.
- **Per-`run_id`-Filterung.**
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from decimal import Decimal

import psycopg
import pytest

from grid_gym.adapters.driven.persistence_postgres import PostgresTelemetrySinkAdapter
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint


@pytest.fixture
def telemetry_sink(
    postgres_dsn: tuple[str, str],
) -> Iterator[PostgresTelemetrySinkAdapter]:
    """Frischer `PostgresTelemetrySinkAdapter` pro Test mit
    TRUNCATE-Reset (`telemetry_points`-Tabelle aus Alembic-`head`).
    Pattern analog der `repository`-Fixture in `conftest.py`."""
    psycopg_dsn, _ = postgres_dsn
    factory: Callable[[], psycopg.Connection] = lambda: psycopg.connect(psycopg_dsn)
    with factory() as conn, conn.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE telemetry_points")
        conn.commit()
    yield PostgresTelemetrySinkAdapter(connection_factory=factory)


def _point(
    *,
    run_id: str = "run-1",
    simulation_time: int,
    device_id: str,
    sequence: int,
    value: str,
    quality: Quality = Quality.VALID,
) -> TelemetryPoint:
    return TelemetryPoint(
        run_id=run_id,
        tick=simulation_time // 1000,
        simulation_time=simulation_time,
        device_id=device_id,
        metric="power_kw",
        value=Decimal(value),
        unit="kW",
        quality=quality,
        source=f"battery.{device_id}",
        sequence=sequence,
    )


def test_read_ordered_preserves_insertion_order_on_ties(
    telemetry_sink: PostgresTelemetrySinkAdapter,
) -> None:
    # Zwei Geraete, gleiche simulation_time, beide sequence=0 (Per-
    # Device-Counter ist NICHT global eindeutig) → Insertion-
    # Reihenfolge muss erhalten bleiben (ORDER BY id).
    points = [
        _point(simulation_time=1000, device_id="battery-1", sequence=0, value="1.50"),
        _point(simulation_time=1000, device_id="battery-2", sequence=0, value="2.25"),
        _point(simulation_time=2000, device_id="battery-1", sequence=0, value="3.00"),
    ]
    telemetry_sink.persist(points)
    assert telemetry_sink.read_ordered("run-1") == tuple(points)


def test_value_is_byte_stable_text(
    telemetry_sink: PostgresTelemetrySinkAdapter,
) -> None:
    # TEXT bewahrt die Decimal-Scale; NUMERIC wuerde `1.50` → `1.5`
    # normalisieren und den 1b-Replay-Diff brechen.
    telemetry_sink.persist(
        [_point(simulation_time=1000, device_id="battery-1", sequence=0, value="1.50")]
    )
    (read_back,) = telemetry_sink.read_ordered("run-1")
    assert read_back.value == Decimal("1.50")
    assert str(read_back.value) == "1.50"


def test_all_persist_001_fields_roundtrip(
    telemetry_sink: PostgresTelemetrySinkAdapter,
) -> None:
    point = _point(
        simulation_time=5000,
        device_id="grid-1",
        sequence=2,
        value="-0.125",
        quality=Quality.STALE,
    )
    telemetry_sink.persist([point])
    (read_back,) = telemetry_sink.read_ordered("run-1")
    assert read_back == point  # frozen-dataclass-Gleichheit ueber alle 10 Felder


def test_persist_is_append_only(
    telemetry_sink: PostgresTelemetrySinkAdapter,
) -> None:
    first = _point(simulation_time=1000, device_id="battery-1", sequence=0, value="1.0")
    second = _point(simulation_time=2000, device_id="battery-1", sequence=0, value="2.0")
    telemetry_sink.persist([first])
    telemetry_sink.persist([second])
    assert telemetry_sink.read_ordered("run-1") == (first, second)
    # Idempotenz-Wiederholungslesen: derselbe Read liefert dasselbe.
    assert telemetry_sink.read_ordered("run-1") == (first, second)


def test_read_ordered_filters_by_run_id(
    telemetry_sink: PostgresTelemetrySinkAdapter,
) -> None:
    a = _point(run_id="run-a", simulation_time=1000, device_id="battery-1", sequence=0, value="1.0")
    b = _point(run_id="run-b", simulation_time=1000, device_id="battery-1", sequence=0, value="2.0")
    telemetry_sink.persist([a, b])
    assert telemetry_sink.read_ordered("run-a") == (a,)
    assert telemetry_sink.read_ordered("run-b") == (b,)


def test_empty_persist_is_noop(
    telemetry_sink: PostgresTelemetrySinkAdapter,
) -> None:
    telemetry_sink.persist([])
    assert telemetry_sink.read_ordered("run-1") == ()
