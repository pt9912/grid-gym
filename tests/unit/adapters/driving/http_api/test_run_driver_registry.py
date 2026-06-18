"""Pins fuer `RunDriverRegistry` (Multi-Run-Execution S2, ADR 0069 §2.2).

Happy: register+start verfolgt aktiv; stop/stop_all beenden + entfernen.
Boundary: bounded concurrency (Reject vor Start). Negative: Doppel-Start;
stop unbekannter run_id = no-op. Plus Lifespan-Shutdown-Naht (stop_all).

Async-Methoden werden via `asyncio.run(...)` aus Sync-Tests gefahren (kein
pytest-asyncio-Modus konfiguriert).
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driving.http_api._run_driver_registry import RunDriverRegistry
from grid_gym.adapters.driving.http_api._run_driver_setup import (
    configure_run_driver_registry,
)
from grid_gym.adapters.driving.http_api.app import app
from grid_gym.hexagon.core.errors import (
    RunAlreadyActiveError,
    RunConcurrencyLimitError,
)


class _FakeDriver:
    """Minimaler `RunDriver`-Stub (start sync, stop async, is_running)."""

    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    @property
    def is_running(self) -> bool:
        return self.started and not self.stopped


def test_register_and_start_starts_and_tracks() -> None:
    registry = RunDriverRegistry(max_active_runs=2)
    driver = _FakeDriver()
    registry.register_and_start("run-1", driver)
    assert driver.started is True
    assert registry.is_active("run-1") is True
    assert registry.active_count == 1


def test_register_duplicate_run_id_raises() -> None:
    registry = RunDriverRegistry()
    registry.register_and_start("run-1", _FakeDriver())
    with pytest.raises(RunAlreadyActiveError):
        registry.register_and_start("run-1", _FakeDriver())
    assert registry.active_count == 1


def test_concurrency_limit_rejects_excess_before_start() -> None:
    registry = RunDriverRegistry(max_active_runs=1)
    registry.register_and_start("run-1", _FakeDriver())
    excess = _FakeDriver()
    with pytest.raises(RunConcurrencyLimitError):
        registry.register_and_start("run-2", excess)
    assert excess.started is False  # Reject vor Start — kein verwaister Task
    assert registry.is_active("run-2") is False
    assert registry.active_count == 1


def test_stop_removes_and_stops_driver() -> None:
    registry = RunDriverRegistry()
    driver = _FakeDriver()
    registry.register_and_start("run-1", driver)
    asyncio.run(registry.stop("run-1"))
    assert driver.stopped is True
    assert registry.is_active("run-1") is False
    assert registry.active_count == 0


def test_stop_unknown_run_id_is_noop() -> None:
    registry = RunDriverRegistry()
    asyncio.run(registry.stop("does-not-exist"))  # kein Fehler
    assert registry.active_count == 0


def test_stop_all_stops_every_driver() -> None:
    registry = RunDriverRegistry()
    first, second = _FakeDriver(), _FakeDriver()
    registry.register_and_start("run-1", first)
    registry.register_and_start("run-2", second)
    asyncio.run(registry.stop_all())
    assert first.stopped is True
    assert second.stopped is True
    assert registry.active_count == 0


def test_lifespan_shutdown_stops_all_registered_drivers() -> None:
    """Lifespan-Shutdown-Naht (app._lifespan finally): stop_all auf der
    konfigurierten Registry."""
    registry = RunDriverRegistry()
    driver = _FakeDriver()
    registry.register_and_start("run-1", driver)
    configure_run_driver_registry(registry)
    try:
        with TestClient(app):
            pass  # Startup + Shutdown des Lifespans
        assert driver.stopped is True
        assert registry.active_count == 0
    finally:
        app.state.run_driver_registry = None
