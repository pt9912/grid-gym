"""Unit-Tests fuer den `TickLoop.finalize()`-Replay-Lifecycle-Hook
(M7 Welle 1b-b, ADR 0049 §2.1..§2.5).

Pinnt den Core-Spine-Vertrag mit In-Memory-Fakes:

- **Clean:** zwei Laeufe mit identischer Telemetrie → leerer Diff →
  `replay_diff_status = 1.0` (`status="clean"`).
- **Diverged:** abweichender `value` → fachlicher Delta →
  `replay_diff_status = 0.0` (`status="diverged"`) + maschinen-
  lesbare `GG-SAFE-006`-Detail-Logs (path/expected/actual/tick/
  device_id/classification).
- **Preflight-Mismatch:** ungleiches `RunMetadata`-Feld → kein
  `replay_diff_status`, strukturierter Reject-Log (per-Feld).
- **No-op** ohne Replay-Bindung; **Idempotenz** bei Doppelaufruf.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.adapters.driven.observability_null.null_adapters import (
    NullLogAdapter,
    NullMetricsAdapter,
)
from grid_gym.adapters.driven.persistence_inmemory import (
    InMemoryReplaySnapshot,
    InMemoryTelemetrySink,
)
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import (
    FakeClock,
    FixedSeedRandom,
    InMemoryRunRepository,
)

_REF = "run-a"
_CUR = "run-b"


def _point(*, run_id: str, simulation_time: int, device_id: str, value: str) -> TelemetryPoint:
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
        sequence=0,
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
    return RunMetadata(
        run_id=run_id,
        scenario_hash=scenario_hash,
        schema_version=schema_version,
        seed=seed,
        tick_ms=tick_ms,
        started_at="",
        ended_at="",
        tool_version=tool_version,
    )


def _make_finalize_loop(
    *,
    sink: InMemoryTelemetrySink,
    repo: InMemoryRunRepository,
    metrics: NullMetricsAdapter,
    log: NullLogAdapter,
    reference_run_id: str | None,
) -> TickLoop:
    return TickLoop(
        run_id=_CUR,
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        run_repository=repo,
        telemetry_sink=sink,
        replay_snapshot=InMemoryReplaySnapshot(sink),
        replay_reference_run_id=reference_run_id,
        metrics_port=metrics,
        log_port=log,
    )


def _gauge_calls(metrics: NullMetricsAdapter, name: str) -> list[dict[str, object]]:
    return [
        dict(record.kwargs)
        for record in metrics.call_records
        if record.method == "gauge" and record.kwargs.get("name") == name
    ]


def _log_calls(log: NullLogAdapter, event_id: str) -> list[dict[str, object]]:
    return [
        dict(record.kwargs)
        for record in log.call_records
        if record.kwargs.get("event_id") == event_id
    ]


def test_clean_replay_emits_status_one() -> None:
    sink = InMemoryTelemetrySink()
    series = [(1000, "bat-1", "1.50"), (1000, "bat-2", "2.25"), (2000, "bat-1", "1.75")]
    sink.persist(
        [_point(run_id=_REF, simulation_time=t, device_id=d, value=v) for t, d, v in series]
    )
    sink.persist(
        [_point(run_id=_CUR, simulation_time=t, device_id=d, value=v) for t, d, v in series]
    )
    repo = InMemoryRunRepository()
    repo.save(_meta(_REF))
    repo.save(_meta(_CUR))
    metrics = NullMetricsAdapter(record_calls=True)
    log = NullLogAdapter(record_calls=True)
    loop = _make_finalize_loop(
        sink=sink, repo=repo, metrics=metrics, log=log, reference_run_id=_REF
    )

    deltas = loop.finalize()

    assert deltas == ()
    (gauge,) = _gauge_calls(metrics, "replay_diff_status")
    assert gauge["value"] == pytest.approx(1.0)
    assert gauge["attributes"] == {
        "run_id": _CUR,
        "reference_run_id": _REF,
        "status": "clean",
    }


def test_diverged_replay_emits_status_zero_and_safe_006_details() -> None:
    sink = InMemoryTelemetrySink()
    sink.persist([_point(run_id=_REF, simulation_time=1000, device_id="bat-1", value="1.50")])
    sink.persist([_point(run_id=_CUR, simulation_time=1000, device_id="bat-1", value="9.99")])
    repo = InMemoryRunRepository()
    repo.save(_meta(_REF))
    repo.save(_meta(_CUR))
    metrics = NullMetricsAdapter(record_calls=True)
    log = NullLogAdapter(record_calls=True)
    loop = _make_finalize_loop(
        sink=sink, repo=repo, metrics=metrics, log=log, reference_run_id=_REF
    )

    deltas = loop.finalize()

    assert len(deltas) == 1
    (gauge,) = _gauge_calls(metrics, "replay_diff_status")
    assert gauge["value"] == pytest.approx(0.0)
    assert gauge["attributes"] == {
        "run_id": _CUR,
        "reference_run_id": _REF,
        "status": "diverged",
    }
    # GG-SAFE-006: alle vier Detailfelder maschinenlesbar im Log.
    (delta_log,) = _log_calls(log, "replay_diff_delta")
    attributes = delta_log["attributes"]
    assert isinstance(attributes, dict)
    assert attributes["path"] == "sample[0].value"
    assert attributes["expected"] == "1.50"
    assert attributes["actual"] == "9.99"
    assert attributes["tick"] == 1
    assert attributes["device_id"] == "bat-1"
    assert attributes["classification"] == "fachlich"


@pytest.mark.parametrize(
    ("field", "ref_kwargs", "cur_kwargs"),
    [
        ("scenario_hash", {"scenario_hash": "h-a"}, {"scenario_hash": "h-b"}),
        ("schema_version", {"schema_version": "v1"}, {"schema_version": "v2"}),
        ("seed", {"seed": 1}, {"seed": 2}),
        ("tick_ms", {"tick_ms": 1000}, {"tick_ms": 100}),
        ("tool_version", {"tool_version": "0.1.0"}, {"tool_version": "0.2.0"}),
    ],
)
def test_preflight_mismatch_skips_diff_and_logs_field(
    field: str,
    ref_kwargs: dict[str, object],
    cur_kwargs: dict[str, object],
) -> None:
    sink = InMemoryTelemetrySink()
    sink.persist([_point(run_id=_REF, simulation_time=1000, device_id="bat-1", value="1.50")])
    sink.persist([_point(run_id=_CUR, simulation_time=1000, device_id="bat-1", value="1.50")])
    repo = InMemoryRunRepository()
    repo.save(_meta(_REF, **ref_kwargs))  # type: ignore[arg-type]
    repo.save(_meta(_CUR, **cur_kwargs))  # type: ignore[arg-type]
    metrics = NullMetricsAdapter(record_calls=True)
    log = NullLogAdapter(record_calls=True)
    loop = _make_finalize_loop(
        sink=sink, repo=repo, metrics=metrics, log=log, reference_run_id=_REF
    )

    deltas = loop.finalize()

    assert deltas == ()
    assert _gauge_calls(metrics, "replay_diff_status") == []
    (reject,) = _log_calls(log, "replay_preflight_mismatch")
    assert reject["attributes"] == {
        "run_id": _CUR,
        "reference_run_id": _REF,
        "field": field,
    }


def test_finalize_is_noop_without_replay_binding() -> None:
    sink = InMemoryTelemetrySink()
    repo = InMemoryRunRepository()
    repo.save(_meta(_CUR))
    metrics = NullMetricsAdapter(record_calls=True)
    log = NullLogAdapter(record_calls=True)
    loop = _make_finalize_loop(
        sink=sink, repo=repo, metrics=metrics, log=log, reference_run_id=None
    )

    assert loop.finalize() == ()
    assert _gauge_calls(metrics, "replay_diff_status") == []


def test_finalize_is_idempotent() -> None:
    sink = InMemoryTelemetrySink()
    sink.persist([_point(run_id=_REF, simulation_time=1000, device_id="bat-1", value="1.50")])
    sink.persist([_point(run_id=_CUR, simulation_time=1000, device_id="bat-1", value="1.50")])
    repo = InMemoryRunRepository()
    repo.save(_meta(_REF))
    repo.save(_meta(_CUR))
    metrics = NullMetricsAdapter(record_calls=True)
    log = NullLogAdapter(record_calls=True)
    loop = _make_finalize_loop(
        sink=sink, repo=repo, metrics=metrics, log=log, reference_run_id=_REF
    )

    first = loop.finalize()
    second = loop.finalize()

    assert first == ()
    assert second == ()
    # Zweiter Aufruf ist No-op (`_finalized`-Flag) → genau eine Emission.
    assert len(_gauge_calls(metrics, "replay_diff_status")) == 1


def test_missing_reference_metadata_is_clean_reject_not_crash() -> None:
    # C2-Review-Folge F2: fehlende Referenz-Lauf-Metadaten → sauberer
    # Reject (Log, kein replay_diff_status), KEIN RunNotFoundError-Crash
    # im Terminal-Pfad. (Referenz-Telemetrie + -Metadaten fehlen; nur der
    # aktuelle Lauf ist gespeichert.)
    sink = InMemoryTelemetrySink()
    sink.persist([_point(run_id=_CUR, simulation_time=1000, device_id="bat-1", value="1.50")])
    repo = InMemoryRunRepository()
    repo.save(_meta(_CUR))  # _REF bewusst NICHT gespeichert
    metrics = NullMetricsAdapter(record_calls=True)
    log = NullLogAdapter(record_calls=True)
    loop = _make_finalize_loop(
        sink=sink, repo=repo, metrics=metrics, log=log, reference_run_id=_REF
    )

    assert loop.finalize() == ()  # kein Crash
    assert _gauge_calls(metrics, "replay_diff_status") == []
    (reject,) = _log_calls(log, "replay_preflight_mismatch")
    assert reject["attributes"] == {
        "run_id": _CUR,
        "reference_run_id": _REF,
        "field": "run_metadata_missing",
    }
