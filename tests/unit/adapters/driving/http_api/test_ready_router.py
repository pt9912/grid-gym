"""Unit-Tests fuer den `/ready`-Router (`_ready_router.py`,
M6 Welle 6; `GG-DEPLOY-006`).

Nutzt `fastapi.testclient.TestClient` (in-process, kein echtes
Backend) — deckt die HTTP-Statusabbildung des `get_ready`-Handlers
ab (200 bei `healthy`/`degraded`, 503 bei `unhealthy`). Die
Three-State-Probe-Logik selbst ist in `test_health_adapter.py`
unit-getestet; hier geht es um die Router-/HTTP-Schicht. Der
End-to-End-Wiring-Pfad ist zusaetzlich in
`tests/integration/test_m6_welle_6_deploy_smoke.py` gepinnt.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from grid_gym.adapters.driving.http_api import app
from grid_gym.adapters.driving.http_api._tick_loop_registry import TickLoopRegistry
from grid_gym.adapters.driving.http_api.app import (
    configure_run_repository,
    configure_tick_loop_registry,
)
from tests.unit.hexagon.ports.driven._fakes import InMemoryRunRepository


class _DbDownRepository(InMemoryRunRepository):
    """`RunRepositoryPort`-Fake mit ausgefallenem Backend (`ping()`
    → `False`)."""

    def ping(self) -> bool:
        return False


def test_ready_returns_200_when_not_unhealthy() -> None:
    configure_run_repository(InMemoryRunRepository())
    # Leere Registry → `simulation` degraded (Stub), DB/UI/API
    # healthy → Top-Level degraded → HTTP 200 (kein 503).
    configure_tick_loop_registry(TickLoopRegistry())

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"healthy", "degraded"}
    assert set(body["components"]) == {"api", "ui", "db", "simulation"}


def test_ready_returns_503_when_db_unhealthy() -> None:
    configure_run_repository(_DbDownRepository())
    configure_tick_loop_registry(TickLoopRegistry())

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"
