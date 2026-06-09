"""Integration-Smoke fuer M7-Welle-1b-a (`GG-MVP-002` Replay-
Snapshot-Rekonstruktion; ADR 0048).

Pinnt den `PostgresReplaySnapshotAdapter`-Vertrag gegen echtes
Postgres (testcontainers, Alembic-`0002_create_telemetry_points`):
geschrieben wird ueber den 1a-`PostgresTelemetrySinkAdapter`,
gelesen ueber den 1b-a-`PostgresReplaySnapshotAdapter` — beide auf
derselben `telemetry_points`-Tabelle (ADR 0048 §2.3, keine eigene
Tabelle).

- **Insertion-Reihenfolge:** `read_samples` liefert die
  `ReplaySample`s in `ORDER BY id`; `import_sequence` ist die
  0-basierte Position — auch bei Ties (zwei Geraete, gleiche
  `simulation_time`).
- **Timestamp-Derivation (D-1.1):** `timestamp == str(simulation_
  time)` — deterministisch, NICHT Wall-Clock.
- **Byte-Stabilitaet:** `value` round-trippt verlustfrei
  (`1.50` bleibt `1.50`).
- **Zwei-Lauf-Determinismus:** zwei `run_id`s mit identischer
  Telemetrie liefern strukturell identische `ReplaySample`-
  Sequenzen → `diff_replay()` ist leer (die `GG-MVP-002`-
  Akzeptanz „leerer Replay-Diff").
- **Leerer Lauf** → leeres Tupel.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from decimal import Decimal

import psycopg
import pytest

from grid_gym.adapters.driven.persistence_postgres import (
    PostgresReplaySnapshotAdapter,
    PostgresTelemetrySinkAdapter,
)
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.replay import ReplaySample
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.replay.diff import diff_replay


@pytest.fixture
def adapters(
    postgres_dsn: tuple[str, str],
) -> Iterator[tuple[PostgresTelemetrySinkAdapter, PostgresReplaySnapshotAdapter]]:
    """Frisches Sink-/Snapshot-Adapter-Paar pro Test mit TRUNCATE-
    Reset; beide teilen denselben `connection_factory` (= dieselbe
    `telemetry_points`-Tabelle aus Alembic-`head`)."""
    psycopg_dsn, _ = postgres_dsn
    factory: Callable[[], psycopg.Connection] = lambda: psycopg.connect(psycopg_dsn)
    with factory() as conn, conn.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE telemetry_points")
        conn.commit()
    yield (
        PostgresTelemetrySinkAdapter(connection_factory=factory),
        PostgresReplaySnapshotAdapter(connection_factory=factory),
    )


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


def test_read_samples_reconstructs_in_insertion_order(
    adapters: tuple[PostgresTelemetrySinkAdapter, PostgresReplaySnapshotAdapter],
) -> None:
    sink, snapshot = adapters
    sink.persist(
        [
            _point(simulation_time=1000, device_id="battery-1", sequence=0, value="1.0"),
            _point(simulation_time=2000, device_id="battery-1", sequence=0, value="2.0"),
            _point(simulation_time=3000, device_id="battery-1", sequence=0, value="3.0"),
        ]
    )
    samples = snapshot.read_samples("run-1")
    assert [s.simulation_time for s in samples] == [1000, 2000, 3000]
    assert [s.import_sequence for s in samples] == [0, 1, 2]


def test_timestamp_is_derived_from_simulation_time(
    adapters: tuple[PostgresTelemetrySinkAdapter, PostgresReplaySnapshotAdapter],
) -> None:
    # D-1.1/ADR 0048 §2.2: timestamp = str(simulation_time), NICHT
    # Wall-Clock — sonst byte-instabiler Self-Replay.
    sink, snapshot = adapters
    sink.persist([_point(simulation_time=42000, device_id="battery-1", sequence=0, value="1.0")])
    (sample,) = snapshot.read_samples("run-1")
    assert sample.timestamp == "42000"
    assert sample.timestamp == str(sample.simulation_time)


def test_import_sequence_breaks_ties_by_insertion_order(
    adapters: tuple[PostgresTelemetrySinkAdapter, PostgresReplaySnapshotAdapter],
) -> None:
    # Zwei Geraete, gleiche simulation_time, beide sequence=0 (Per-
    # Device-Counter nicht global eindeutig) → import_sequence
    # unterscheidet ueber die Insertion-Reihenfolge (id).
    sink, snapshot = adapters
    first = _point(simulation_time=1000, device_id="battery-1", sequence=0, value="1.0")
    second = _point(simulation_time=1000, device_id="battery-2", sequence=0, value="2.0")
    sink.persist([first, second])
    samples = snapshot.read_samples("run-1")
    assert [(s.device_id, s.import_sequence) for s in samples] == [
        ("battery-1", 0),
        ("battery-2", 1),
    ]


def test_value_is_byte_stable_roundtrip(
    adapters: tuple[PostgresTelemetrySinkAdapter, PostgresReplaySnapshotAdapter],
) -> None:
    sink, snapshot = adapters
    sink.persist([_point(simulation_time=1000, device_id="battery-1", sequence=0, value="1.50")])
    (sample,) = snapshot.read_samples("run-1")
    assert sample.value == Decimal("1.50")
    assert str(sample.value) == "1.50"


def test_two_runs_same_scenario_yield_empty_diff(
    adapters: tuple[PostgresTelemetrySinkAdapter, PostgresReplaySnapshotAdapter],
) -> None:
    # Kern-Akzeptanz GG-MVP-002: zwei Laeufe desselben Szenarios
    # (gleiche Telemetrie, nur andere run_id — run_id ist KEIN
    # ReplaySample-Feld) liefern strukturell identische Sample-
    # Sequenzen → leerer Replay-Diff.
    sink, snapshot = adapters
    series = [
        ("battery-1", 1000, "1.50"),
        ("battery-2", 1000, "2.25"),
        ("battery-1", 2000, "1.75"),
        ("battery-2", 2000, "2.00"),
    ]
    sink.persist(
        [
            _point(run_id="run-a", simulation_time=t, device_id=d, sequence=0, value=v)
            for d, t, v in series
        ]
        + [
            _point(run_id="run-b", simulation_time=t, device_id=d, sequence=0, value=v)
            for d, t, v in series
        ]
    )
    expected = snapshot.read_samples("run-a")
    actual = snapshot.read_samples("run-b")
    assert expected == actual
    assert diff_replay(expected, actual) == ()


def test_diverging_runs_produce_fachlich_delta(
    adapters: tuple[PostgresTelemetrySinkAdapter, PostgresReplaySnapshotAdapter],
) -> None:
    # Gegenprobe: ein abweichender value erzeugt einen fachlichen
    # Replay-Delta (nicht volatil).
    sink, snapshot = adapters
    sink.persist(
        [
            _point(
                run_id="run-a",
                simulation_time=1000,
                device_id="battery-1",
                sequence=0,
                value="1.50",
            ),
            _point(
                run_id="run-b",
                simulation_time=1000,
                device_id="battery-1",
                sequence=0,
                value="9.99",
            ),
        ]
    )
    deltas = diff_replay(snapshot.read_samples("run-a"), snapshot.read_samples("run-b"))
    assert len(deltas) == 1
    assert deltas[0].classification.value == "fachlich"


def test_empty_run_returns_empty_tuple(
    adapters: tuple[PostgresTelemetrySinkAdapter, PostgresReplaySnapshotAdapter],
) -> None:
    _sink, snapshot = adapters
    assert snapshot.read_samples("run-unknown") == ()


def test_reconstructs_full_replay_sample_fields(
    adapters: tuple[PostgresTelemetrySinkAdapter, PostgresReplaySnapshotAdapter],
) -> None:
    sink, snapshot = adapters
    sink.persist([_point(simulation_time=5000, device_id="grid-1", sequence=2, value="-0.125")])
    (sample,) = snapshot.read_samples("run-1")
    assert sample == ReplaySample(
        timestamp="5000",
        simulation_time=5000,
        device_id="grid-1",
        metric="power_kw",
        value=Decimal("-0.125"),
        unit="kW",
        import_sequence=0,
    )
