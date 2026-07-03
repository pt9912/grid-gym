"""Integration-Smoke fuer M7-Welle-1b-b (`GG-MVP-002` Replay-
Lifecycle; ADR 0049) gegen echtes Postgres (testcontainers).

Pinnt den Core-`TickLoop.finalize()`-Hook end-to-end ueber die
Postgres-Adapter (`PostgresTelemetrySinkAdapter` schreibt,
`PostgresReplaySnapshotAdapter` rekonstruiert, `PostgresRunRepository`
liefert die Preflight-Metadaten):

- **Clean (Headline-E2E):** zwei echte Demo-Szenario-Laeufe mit
  gleichem Seed → leerer Diff → `replay_diff_status = 1.0`
  (`GG-MVP-002` „leerer Replay-Diff").
- **Diverged:** preflight-gleiche Laeufe mit abweichender Telemetrie
  → fachlicher Delta → `replay_diff_status = 0.0` + maschinenlesbare
  `GG-SAFE-006`-Detail-Logs.
- **Preflight-Mismatch:** ungleicher `seed` → kein
  `replay_diff_status`, Reject-Log.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from decimal import Decimal

import psycopg
import pytest

from grid_gym.adapters.driven.observability_null.null_adapters import (
    NullLogAdapter,
    NullMetricsAdapter,
)
from grid_gym.adapters.driven.persistence_inmemory import InMemoryRunRepository
from grid_gym.adapters.driven.persistence_postgres import (
    PostgresReplaySnapshotAdapter,
    PostgresTelemetrySinkAdapter,
)
from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.scenario.loader import TickLoopWiring, build_tick_loop
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop

from tests.integration._constants import MVP_DEMO_SCENARIO_PATH
from tests.integration._yaml_scenario_loader import load_yaml_scenario
from tests.unit.hexagon.ports.driven._fakes import FakeClock

_REF = "lifecycle-run-a"
_CUR = "lifecycle-run-b"
_TICKS = 25


@dataclass(slots=True)
class _Adapters:
    repository: InMemoryRunRepository
    sink: PostgresTelemetrySinkAdapter
    snapshot: PostgresReplaySnapshotAdapter


@pytest.fixture
def adapters(postgres_dsn: tuple[str, str]) -> Iterator[_Adapters]:
    """**Postgres** Telemetry-Sink + Replay-Snapshot (der Integrations-
    Wert: echter `telemetry_points`-Round-Trip durch `finalize()`) auf
    derselben DB mit TRUNCATE-Reset. Das `run_repository` ist der
    In-Memory-Adapter — `PostgresRunRepository.update_status` ist ein
    M3-Welle-6c-`NotImplementedError`-Stub (keine Status-Spalte), und
    der produktive Status-/Demo-Pfad nutzt ohnehin
    `InMemoryRunRepository` (Lauf-Lifecycle-State + Preflight-
    Metadaten)."""
    psycopg_dsn, _ = postgres_dsn
    factory: Callable[[], psycopg.Connection] = lambda: psycopg.connect(psycopg_dsn)
    with factory() as conn, conn.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE telemetry_points")
        conn.commit()
    yield _Adapters(
        repository=InMemoryRunRepository(),
        sink=PostgresTelemetrySinkAdapter(connection_factory=factory),
        snapshot=PostgresReplaySnapshotAdapter(connection_factory=factory),
    )


def _meta(
    run_id: str,
    *,
    scenario_hash: str = "hash-1",
    schema_version: str = "v1",
    seed: int = 42,
    tick_ms: int = 1000,
    tool_version: str = "0.1.0",
) -> RunMetadata:
    """Preflight-valide Metadaten: die GG-TERM-Vollfelder sind
    befuellt (Slice 038 / ADR 0073 §2.6), sonst endete der
    `finalize()`-Preflight im `missing`-Reject statt im Diff."""
    return RunMetadata(
        run_id=run_id,
        scenario_hash=scenario_hash,
        schema_version=schema_version,
        seed=seed,
        tick_ms=tick_ms,
        started_at="",
        ended_at="",
        tool_version=tool_version,
        platform_arch="x86_64",
        enabled_adapters=("http_api", "persistence_inmemory"),
        sim_start_time=0,
        config_hash="c" * 64,
    )


def _point(*, run_id: str, simulation_time: int, value: str) -> TelemetryPoint:
    return TelemetryPoint(
        run_id=run_id,
        tick=simulation_time // 1000,
        simulation_time=simulation_time,
        device_id="battery-1",
        metric="power_kw",
        value=Decimal(value),
        unit="kW",
        quality=Quality.VALID,
        source="battery.battery-1",
        sequence=0,
    )


def _gauge_value(metrics: NullMetricsAdapter) -> list[dict[str, object]]:
    return [
        dict(record.kwargs)
        for record in metrics.call_records
        if record.method == "gauge" and record.kwargs.get("name") == "replay_diff_status"
    ]


def _minimal_loop(
    *,
    adapters: _Adapters,
    metrics: NullMetricsAdapter,
    log: NullLogAdapter,
    reference_run_id: str | None,
) -> TickLoop:
    return TickLoop(
        run_id=_CUR,
        tick_ms=1000,
        clock=FakeClock(),
        random=MersenneTwisterRandomPort(seed=42),
        scheduler=Scheduler(),
        run_repository=adapters.repository,
        telemetry_sink=adapters.sink,
        replay_snapshot=adapters.snapshot,
        replay_reference_run_id=reference_run_id,
        metrics_port=metrics,
        log_port=log,
    )


def test_two_run_demo_replay_is_clean(adapters: _Adapters) -> None:
    """Headline-`GG-MVP-002`-Beleg: zwei echte Demo-Laeufe mit
    gleichem Seed persistieren byte-identische Telemetrie; der
    `finalize()`-Hook difft Lauf B gegen Lauf A → leerer Diff →
    `replay_diff_status = 1.0`."""
    loaded = load_yaml_scenario(MVP_DEMO_SCENARIO_PATH)
    seed = loaded.scenario.simulation.seed
    tick_ms = loaded.scenario.simulation.tick_ms

    # Lauf A (Original): persistiert Telemetrie ueber den Sink.
    loop_a = build_tick_loop(
        loaded.scenario,
        run_id=_REF,
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=seed),
        wiring=TickLoopWiring(run_repository=adapters.repository, telemetry_sink=adapters.sink),
    )
    adapters.repository.save(
        _meta(_REF, scenario_hash=loaded.scenario_hash, seed=seed, tick_ms=tick_ms)
    )
    for _ in range(_TICKS):
        loop_a.tick()

    # Lauf B (Replay): gleiches Szenario/Seed; finalize() difft B vs A.
    metrics = NullMetricsAdapter(record_calls=True)
    log = NullLogAdapter(record_calls=True)
    loop_b = build_tick_loop(
        loaded.scenario,
        run_id=_CUR,
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=seed),
        wiring=TickLoopWiring(
            run_repository=adapters.repository,
            telemetry_sink=adapters.sink,
            replay_snapshot=adapters.snapshot,
            replay_reference_run_id=_REF,
            metrics_port=metrics,
            log_port=log,
        ),
    )
    adapters.repository.save(
        _meta(_CUR, scenario_hash=loaded.scenario_hash, seed=seed, tick_ms=tick_ms)
    )
    for _ in range(_TICKS):
        loop_b.tick()

    # C2-Review-Folge F1: gegen Vakuum-Pass absichern — der leere Diff
    # ist nur dann ein Determinismus-Beleg, wenn beide Laeufe auch
    # tatsaechlich Telemetrie persistiert haben. (diff_replay((),()) == ()
    # waere sonst trivial gruen.)
    expected = adapters.snapshot.read_samples(_REF)
    actual = adapters.snapshot.read_samples(_CUR)
    assert len(expected) > 0, "Lauf A muss Telemetrie persistiert haben (sonst Vakuum-Pass)"
    assert len(actual) == len(expected), "beide Laeufe muessen gleich viele Samples liefern"

    deltas = loop_b.finalize()

    assert deltas == ()
    (gauge,) = _gauge_value(metrics)
    assert gauge["value"] == pytest.approx(1.0)
    assert gauge["attributes"] == {
        "run_id": _CUR,
        "reference_run_id": _REF,
        "status": "clean",
    }


def test_diverged_runs_emit_status_zero_with_safe_006_details(adapters: _Adapters) -> None:
    """Preflight-gleiche Laeufe mit abweichender Telemetrie → fachlicher
    Delta → `replay_diff_status = 0.0` + `GG-SAFE-006`-Detail-Log."""
    adapters.sink.persist([_point(run_id=_REF, simulation_time=1000, value="1.50")])
    adapters.sink.persist([_point(run_id=_CUR, simulation_time=1000, value="9.99")])
    adapters.repository.save(_meta(_REF))
    adapters.repository.save(_meta(_CUR))
    metrics = NullMetricsAdapter(record_calls=True)
    log = NullLogAdapter(record_calls=True)

    deltas = _minimal_loop(
        adapters=adapters, metrics=metrics, log=log, reference_run_id=_REF
    ).finalize()

    assert len(deltas) == 1
    (gauge,) = _gauge_value(metrics)
    assert gauge["value"] == pytest.approx(0.0)
    assert gauge["attributes"]["status"] == "diverged"  # type: ignore[index]
    (delta_log,) = [
        dict(record.kwargs)
        for record in log.call_records
        if record.kwargs.get("event_id") == "replay_diff_delta"
    ]
    attributes = delta_log["attributes"]
    assert isinstance(attributes, dict)
    assert attributes["path"] == "sample[0].value"
    assert attributes["expected"] == "1.50"
    assert attributes["actual"] == "9.99"
    assert attributes["classification"] == "fachlich"


def test_preflight_seed_mismatch_skips_diff(adapters: _Adapters) -> None:
    """Ungleicher `seed` → Preflight-Reject vor dem Diff: kein
    `replay_diff_status`, Reject-Log."""
    adapters.sink.persist([_point(run_id=_REF, simulation_time=1000, value="1.50")])
    adapters.sink.persist([_point(run_id=_CUR, simulation_time=1000, value="1.50")])
    adapters.repository.save(_meta(_REF, seed=1))
    adapters.repository.save(_meta(_CUR, seed=2))
    metrics = NullMetricsAdapter(record_calls=True)
    log = NullLogAdapter(record_calls=True)

    deltas = _minimal_loop(
        adapters=adapters, metrics=metrics, log=log, reference_run_id=_REF
    ).finalize()

    assert deltas == ()
    assert _gauge_value(metrics) == []
    (reject,) = [
        dict(record.kwargs)
        for record in log.call_records
        if record.kwargs.get("event_id") == "replay_preflight_mismatch"
    ]
    assert reject["attributes"] == {
        "run_id": _CUR,
        "reference_run_id": _REF,
        "field": "seed",
    }
