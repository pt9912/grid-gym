"""Unit-Tests fuer `ReadinessProbeAdapter` (M6 Welle 6;
`GG-DEPLOY-006` `/ready`-Three-State-Readiness).

Testet den Driving-Adapter direkt (ohne HTTP-Surface) ueber
`asyncio.run`, analog zum `asyncio.run`-Pattern der uebrigen
async-Adapter-Unit-Tests (kein pytest-asyncio-Plugin im Repo).

Deckt die vier Komponenten-Probes (`api`/`ui`/`db`/`simulation`),
die Aggregations-Regel (Welle-6-D-2) und den Exception-/Timeout-
Mapping-Pfad (`return_exceptions=True` → `unhealthy`) ab. Die
`ui`-Probe nutzt das reale `base.html`-Template (im Source-Stage
vorhanden); die `db`- und `simulation`-Abhaengigkeiten werden
ueber Duck-Typed-Fakes injiziert.
"""

from __future__ import annotations

import asyncio
from typing import cast

from grid_gym.adapters.driving.http_api._health_adapter import (
    ReadinessProbeAdapter,
)
from grid_gym.adapters.driving.http_api._schemas import ReadyResponse
from grid_gym.adapters.driving.http_api._tick_loop_healthcheck import (
    TickLoopHealthcheckAdapter,
)
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort


class _PingRepository:
    """Minimaler `RunRepositoryPort`-Fake: nur `ping()` wird vom
    `/ready`-Adapter gelesen."""

    def __init__(self, *, result: bool) -> None:
        self._result = result

    def ping(self) -> bool:
        return self._result


class _RaisingRepository:
    """`RunRepositoryPort`-Fake, dessen `ping()` einen Backend-Fehler
    wirft (Postgres nicht erreichbar) — testet den Exception-Mapping-
    Pfad auf `unhealthy`."""

    def ping(self) -> bool:
        raise RuntimeError("backend unreachable")


class _FakeSimHealthcheck:
    """Minimaler `TickLoopHealthcheckAdapter`-Fake: nur
    `healthcheck()` wird vom `/ready`-Adapter gelesen."""

    def __init__(self, *, status: str, missed: int = 0) -> None:
        self._status = status
        self._missed = missed

    def healthcheck(self) -> dict[str, object]:
        return {
            "backpressure_status": self._status,
            "missed_ticks_count": self._missed,
            "tick_duration_ms_p50": 0.0,
            "tick_duration_ms_p95": 0.0,
            "tick_ms": 10,
            "window_size": 0,
        }


def _ping_repository(*, result: bool) -> RunRepositoryPort:
    return cast(RunRepositoryPort, _PingRepository(result=result))


def _sim(*, status: str, missed: int = 0) -> TickLoopHealthcheckAdapter:
    return cast(TickLoopHealthcheckAdapter, _FakeSimHealthcheck(status=status, missed=missed))


def _run_check(adapter: ReadinessProbeAdapter) -> ReadyResponse:
    return asyncio.run(adapter.check())


def test_all_components_healthy_aggregates_healthy() -> None:
    adapter = ReadinessProbeAdapter(
        run_repository=_ping_repository(result=True),
        simulation_healthcheck=_sim(status="ok"),
    )
    report = _run_check(adapter)
    assert report.status == "healthy"
    assert {name: comp.state for name, comp in report.components.items()} == {
        "api": "healthy",
        "ui": "healthy",
        "db": "healthy",
        "simulation": "healthy",
    }


def test_db_ping_false_aggregates_unhealthy() -> None:
    adapter = ReadinessProbeAdapter(
        run_repository=_ping_repository(result=False),
        simulation_healthcheck=_sim(status="ok"),
    )
    report = _run_check(adapter)
    assert report.status == "unhealthy"
    assert report.components["db"].state == "unhealthy"
    assert report.components["db"].reason is not None


def test_db_ping_exception_mapped_to_unhealthy() -> None:
    adapter = ReadinessProbeAdapter(
        run_repository=cast(RunRepositoryPort, _RaisingRepository()),
        simulation_healthcheck=_sim(status="ok"),
    )
    report = _run_check(adapter)
    assert report.status == "unhealthy"
    db = report.components["db"]
    assert db.state == "unhealthy"
    assert db.reason is not None
    assert "RuntimeError" in db.reason


def test_simulation_without_adapter_is_degraded_stub() -> None:
    adapter = ReadinessProbeAdapter(
        run_repository=_ping_repository(result=True),
        simulation_healthcheck=None,
    )
    report = _run_check(adapter)
    assert report.status == "degraded"
    simulation = report.components["simulation"]
    assert simulation.state == "degraded"
    assert simulation.reason is not None
    assert "stub" in simulation.reason


def test_simulation_delayed_is_degraded_with_missed_count() -> None:
    adapter = ReadinessProbeAdapter(
        run_repository=_ping_repository(result=True),
        simulation_healthcheck=_sim(status="delayed", missed=3),
    )
    report = _run_check(adapter)
    assert report.status == "degraded"
    simulation = report.components["simulation"]
    assert simulation.state == "degraded"
    assert simulation.reason == "tick delayed; missed 3 ticks"
