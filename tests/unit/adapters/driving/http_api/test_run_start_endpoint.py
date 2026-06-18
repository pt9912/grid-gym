"""Pins fuer `POST /runs/{run_id}/start` (Multi-Run-Execution S3, ADR 0069 §2.4).

Happy: 202 + Registry-Aktivierung (Fake-Builder, mirror der composition.asgi-
Hook-Verdrahtung). Negative: 404 (Lauf fehlt), 422 (kein Scenario-Content),
409 (bereits aktiv), 429 (Concurrency-Limit), 500 (Builder/Registry nicht
konfiguriert).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import grid_gym.adapters.driving.http_api._run_start_router as start_router
from grid_gym.adapters.driven.persistence_inmemory import (
    InMemoryRunRepository,
    InMemoryScenarioStore,
)
from grid_gym.adapters.driving.http_api._run_driver_registry import RunDriverRegistry
from grid_gym.adapters.driving.http_api._run_driver_setup import (
    configure_run_driver_registry,
)
from grid_gym.adapters.driving.http_api._scenario_setup import configure_scenario_store
from grid_gym.adapters.driving.http_api.app import app, configure_run_repository
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.errors import ScenarioError
from grid_gym.hexagon.core.scenario.loader import load_scenario

_RAW = {
    "schema_version": "grid-gym.scenario.v1",
    "metadata": {"id": "demo", "name": "Demo Scenario"},
    "simulation": {"tick_ms": 100, "duration_s": 60, "seed": 42},
    "devices": [{"id": "grid-1", "type": "grid_connection", "params": {}}],
}


class _FakeDriver:
    """Minimaler `RunDriver`-Stub (start sync, stop async) — vermeidet eine
    echte asyncio-Tick-Schleife im Endpoint-Test."""

    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


def _fake_builder(
    _scenario: object, _run_id: str, _repository: object, _replay_of: str | None
) -> _FakeDriver:
    return _FakeDriver()


def _build_failing_builder(
    _scenario: object, _run_id: str, _repository: object, _replay_of: str | None
) -> object:
    # Simuliert einen load-valid-aber-build-invalid-Scenario (z. B. unvollstaendige
    # Device-Params): der echte build_run_driver wuerde hier eine SnapshotFormatError-
    # /ScenarioError-Familie werfen.
    raise ScenarioError("simulated scenario build failure")


def _metadata(run_id: str, scenario_hash: str) -> RunMetadata:
    return RunMetadata(
        run_id=run_id,
        scenario_hash=scenario_hash,
        schema_version="grid-gym.scenario.v1",
        seed=42,
        tick_ms=100,
        started_at="",
        ended_at="",
        tool_version="0.1.0",
    )


def _reset_app_state() -> None:
    app.state.run_repository = None
    app.state.scenario_store = None
    app.state.run_driver_registry = None


@pytest.fixture
def wired() -> Iterator[tuple[TestClient, str, RunDriverRegistry]]:
    """App mit Repository (1 gespeicherter Lauf) + Store (Scenario unter Hash)
    + Registry + registrierter Fake-Builder-Bridge."""
    loaded = load_scenario(_RAW)
    run_id = "run-1"
    repository = InMemoryRunRepository()
    repository.save(_metadata(run_id, loaded.scenario_hash))
    store = InMemoryScenarioStore()
    store.put(loaded.scenario_hash, loaded.scenario)
    registry = RunDriverRegistry()
    configure_run_repository(repository)
    configure_scenario_store(store)
    configure_run_driver_registry(registry)
    saved = start_router._run_driver_builder
    start_router._register_run_driver_builder(_fake_builder)
    try:
        with TestClient(app) as client:
            yield client, run_id, registry
    finally:
        start_router._run_driver_builder = saved
        _reset_app_state()


def test_start_run_registers_and_returns_202(
    wired: tuple[TestClient, str, RunDriverRegistry],
) -> None:
    client, run_id, registry = wired
    resp = client.post(f"/runs/{run_id}/start")
    assert resp.status_code == 202
    body = resp.json()
    assert body["run_id"] == run_id
    assert body["status"] == "running"
    assert registry.is_active(run_id) is True


def test_start_unknown_run_404(
    wired: tuple[TestClient, str, RunDriverRegistry],
) -> None:
    client, _run_id, _registry = wired
    resp = client.post("/runs/does-not-exist/start")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "run_not_found"


def test_start_without_scenario_content_422(
    wired: tuple[TestClient, str, RunDriverRegistry],
) -> None:
    client, run_id, _registry = wired
    # Store gegen einen leeren austauschen -> Scenario-Content fehlt.
    configure_scenario_store(InMemoryScenarioStore())
    resp = client.post(f"/runs/{run_id}/start")
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "scenario_content_not_found"


def test_start_already_active_409(
    wired: tuple[TestClient, str, RunDriverRegistry],
) -> None:
    client, run_id, _registry = wired
    assert client.post(f"/runs/{run_id}/start").status_code == 202
    resp = client.post(f"/runs/{run_id}/start")
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "run_already_active"


def test_start_concurrency_limit_429() -> None:
    loaded = load_scenario(_RAW)
    run_id = "run-2"
    repository = InMemoryRunRepository()
    repository.save(_metadata(run_id, loaded.scenario_hash))
    store = InMemoryScenarioStore()
    store.put(loaded.scenario_hash, loaded.scenario)
    registry = RunDriverRegistry(max_active_runs=1)
    registry.register_and_start("other-run", _FakeDriver())  # Limit ausgeschoepft
    configure_run_repository(repository)
    configure_scenario_store(store)
    configure_run_driver_registry(registry)
    saved = start_router._run_driver_builder
    start_router._register_run_driver_builder(_fake_builder)
    try:
        with TestClient(app) as client:
            resp = client.post(f"/runs/{run_id}/start")
        assert resp.status_code == 429
        assert resp.json()["detail"]["code"] == "run_concurrency_limit"
    finally:
        start_router._run_driver_builder = saved
        _reset_app_state()


def test_start_builder_not_registered_500() -> None:
    loaded = load_scenario(_RAW)
    run_id = "run-3"
    repository = InMemoryRunRepository()
    repository.save(_metadata(run_id, loaded.scenario_hash))
    store = InMemoryScenarioStore()
    store.put(loaded.scenario_hash, loaded.scenario)
    configure_run_repository(repository)
    configure_scenario_store(store)
    configure_run_driver_registry(RunDriverRegistry())
    saved = start_router._run_driver_builder
    start_router._run_driver_builder = start_router._raise_run_driver_builder_unregistered
    try:
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/runs/{run_id}/start")
        assert resp.status_code == 500
    finally:
        start_router._run_driver_builder = saved
        _reset_app_state()


def test_start_build_failure_422() -> None:
    """Builder wirft `ScenarioError`/`SnapshotFormatError` (Scenario load-valid,
    aber nicht baubar) → 422 `scenario_build_failed`."""
    loaded = load_scenario(_RAW)
    run_id = "run-5"
    repository = InMemoryRunRepository()
    repository.save(_metadata(run_id, loaded.scenario_hash))
    store = InMemoryScenarioStore()
    store.put(loaded.scenario_hash, loaded.scenario)
    configure_run_repository(repository)
    configure_scenario_store(store)
    configure_run_driver_registry(RunDriverRegistry())
    saved = start_router._run_driver_builder
    start_router._register_run_driver_builder(_build_failing_builder)
    try:
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/runs/{run_id}/start")
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "scenario_build_failed"
    finally:
        start_router._run_driver_builder = saved
        _reset_app_state()


def test_start_registry_not_configured_500() -> None:
    loaded = load_scenario(_RAW)
    run_id = "run-4"
    repository = InMemoryRunRepository()
    repository.save(_metadata(run_id, loaded.scenario_hash))
    store = InMemoryScenarioStore()
    store.put(loaded.scenario_hash, loaded.scenario)
    configure_run_repository(repository)
    configure_scenario_store(store)
    app.state.run_driver_registry = None  # Registry nicht konfiguriert
    try:
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/runs/{run_id}/start")
        assert resp.status_code == 500
    finally:
        _reset_app_state()
