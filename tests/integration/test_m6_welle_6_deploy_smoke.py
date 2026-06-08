"""Integration-Smoke fuer M6-Welle-6 (Deploy-Hardening; `GG-DEPLOY-006`
`/ready`-Three-State + `GG-DEPLOY-004` DevContainer + Trigger 009
versions-bedingter Skip-Marker).

Pinnt die produktive Welle-6-C2-Wiring:

1. `GET /ready` mit allen Backends gruen → `healthy` (HTTP 200);
   vier Komponenten `api`/`ui`/`db`/`simulation`.
2. DB-Ausfall (`RunRepositoryPort.ping()` → `False`) → `db`
   `unhealthy`, Top-Level `unhealthy` (HTTP 503).
3. Ohne aktiven TickLoop → `simulation` `degraded` (Sub-Form B),
   kein Pseudo-Ausfall (HTTP 200).
4. TickLoop-Backpressure-Mapping: `ok` → `simulation` `healthy`;
   `delayed` → `degraded` mit `missed_ticks_count` in der Ursache.
5. `.devcontainer/devcontainer.json` traegt die drei Pflicht-
   Befehle (Build/Test/Abnahme; Quell-Datei-Inspektion).
6. `.devcontainer/devcontainer.json` pinnt die `base`-Stage
   (`build.dockerfile`/`target`, kein floating `image:`-Tag).
7. `tests/integration/test_iec61850_in_process_smoke.py` traegt
   einen versions-bedingten `pytest.mark.skipif`-Marker (kein
   blanker `skip`).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driving.http_api import app
from grid_gym.adapters.driving.http_api._tick_loop_healthcheck import (
    TickLoopHealthcheckAdapter,
)
from grid_gym.adapters.driving.http_api._tick_loop_registry import TickLoopRegistry
from grid_gym.adapters.driving.http_api.app import (
    configure_run_repository,
    configure_tick_loop_registry,
)
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import (
    FakeClock,
    FixedSeedRandom,
    InMemoryRunRepository,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEVCONTAINER = _REPO_ROOT / ".devcontainer" / "devcontainer.json"
_IEC_SMOKE = Path(__file__).parent / "test_iec61850_in_process_smoke.py"
_TICK_MS = 10


class _DbDownRepository(InMemoryRunRepository):
    """`RunRepositoryPort`-Fake mit ausgefallenem Backend: `ping()`
    liefert `False` (simuliert nicht-erreichbare DB; Welle-6-D-2)."""

    def ping(self) -> bool:
        return False


def _register_simulation_healthcheck(
    registry: TickLoopRegistry,
    repository: InMemoryRunRepository,
) -> TickLoopHealthcheckAdapter:
    """Registriert einen TickLoop-Healthcheck-Adapter (Sub-Form A);
    leeres Window → `backpressure_status == "ok"` → `simulation`
    `healthy`. Gibt den Adapter fuer `record_tick_duration`-Override
    im Mapping-Test zurueck."""
    tick_loop = TickLoop(
        run_id="deploy-ready-run",
        tick_ms=_TICK_MS,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        run_repository=repository,
    )
    registry.register(tick_loop)
    adapter = TickLoopHealthcheckAdapter(tick_loop, window_size=100)
    registry.register_healthcheck_adapter(tick_loop.run_id, adapter)
    return adapter


@pytest.fixture
def ready_client() -> Iterator[tuple[TestClient, TickLoopRegistry]]:
    """App mit frischem InMemoryRunRepository (ping → True) +
    Registry mit einem `ok`-TickLoop-Healthcheck-Adapter — der
    Canonical-Healthy-Pfad."""
    configure_run_repository(InMemoryRunRepository())
    registry = TickLoopRegistry()
    configure_tick_loop_registry(registry)
    repository = InMemoryRunRepository()
    _register_simulation_healthcheck(registry, repository)
    with TestClient(app) as client:
        yield client, registry


def test_deploy_006_ready_endpoint_three_state_canonical(
    ready_client: tuple[TestClient, TickLoopRegistry],
) -> None:
    client, _ = ready_client

    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    components = body["components"]
    for name in ("api", "ui", "db", "simulation"):
        assert components[name]["state"] == "healthy", name


def test_deploy_006_ready_endpoint_unhealthy_when_db_down() -> None:
    configure_run_repository(_DbDownRepository())
    registry = TickLoopRegistry()
    configure_tick_loop_registry(registry)
    _register_simulation_healthcheck(registry, InMemoryRunRepository())

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unhealthy"
    db = body["components"]["db"]
    assert db["state"] == "unhealthy"
    assert db["reason"]


def test_deploy_006_ready_endpoint_simulation_stub_reflects_degraded() -> None:
    configure_run_repository(InMemoryRunRepository())
    # Registry OHNE Healthcheck-Adapter → Sub-Form B (Stub).
    configure_tick_loop_registry(TickLoopRegistry())

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    simulation = body["components"]["simulation"]
    assert simulation["state"] == "degraded"
    assert "stub" in simulation["reason"]


def test_deploy_006_ready_endpoint_tickloop_status_mapping(
    ready_client: tuple[TestClient, TickLoopRegistry],
) -> None:
    client, registry = ready_client
    adapter = registry.any_healthcheck_adapter()
    assert adapter is not None

    # Leeres Window → backpressure ok → simulation healthy.
    ok_body = client.get("/ready").json()
    assert ok_body["components"]["simulation"]["state"] == "healthy"

    # Ein Tick langsamer als tick_ms → delayed → simulation degraded.
    adapter.record_tick_duration(float(_TICK_MS) * 2)
    delayed_body = client.get("/ready").json()
    simulation = delayed_body["components"]["simulation"]
    assert simulation["state"] == "degraded"
    assert "missed 1 ticks" in simulation["reason"]


def test_deploy_004_devcontainer_config_present() -> None:
    source = _DEVCONTAINER.read_text(encoding="utf-8")
    for command in ("Build", "Test", "Abnahme"):
        assert command in source, command


def test_deploy_004_devcontainer_build_section_pins_base_stage() -> None:
    config = json.loads(_DEVCONTAINER.read_text(encoding="utf-8"))
    build = config["build"]
    assert build["dockerfile"] == "../Dockerfile"
    assert build["target"] == "base"
    # Kein floating `:latest`-Image-Tag — die Stage wird gebaut.
    assert "image" not in config


def test_trigger_009_iec61850_skipmark_is_versions_conditional() -> None:
    source = _IEC_SMOKE.read_text(encoding="utf-8")
    assert "pytestmark = pytest.mark.skipif(" in source
    assert "sys.version_info >= (3, 13)" in source
