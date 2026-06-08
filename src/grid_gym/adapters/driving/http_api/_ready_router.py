"""FastAPI-Router fuer den Readiness-Endpoint `GET /ready`
(M6 Welle 6; `GG-DEPLOY-006` Three-State-Readiness).

Ein REST-Endpoint:

- `GET /ready` — Three-State-Status (`healthy`/`degraded`/
  `unhealthy`) plus Komponenten-Breakdown ueber die vier
  Lastenheft-Pflicht-Komponenten (`api`/`ui`/`db`/`simulation`)
  mit Ursachen-String pro Komponente (Lastenheft Z. 1876-1879).

Separates Modul gegen `app.py`-Wuchs (`AC-NO-GOD-UTILS` max 5
public top-level functions; Pattern analog `_healthcheck_router.py`
/ `_runs_action_router.py`). Probe-Orchestrierung im
`_health_adapter.ReadinessProbeAdapter` (Welle-6-D-2/D-6).

`GET /health` (Liveness) bleibt in `app.py` und unveraendert — ein
Container mit hakendem Postgres ist nicht „liveness-tot" (ein
Restart wuerde das Symptom verschlimmern). Readiness signalisiert
`503`, Liveness `200`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from grid_gym.adapters.driving.http_api._dependencies import (
    get_run_repository,
)
from grid_gym.adapters.driving.http_api._health_adapter import (
    ReadinessProbeAdapter,
)
from grid_gym.adapters.driving.http_api._schemas import ReadyResponse
from grid_gym.adapters.driving.http_api._tick_loop_registry import (
    TickLoopRegistry,
    get_tick_loop_registry,
)
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort

ready_router = APIRouter(tags=["meta"])


@ready_router.get("/ready", response_model=ReadyResponse)
async def get_ready(
    response: Response,
    repository: Annotated[RunRepositoryPort, Depends(get_run_repository)],
    tick_loop_registry: Annotated[TickLoopRegistry, Depends(get_tick_loop_registry)],
) -> ReadyResponse:
    """Readiness-Probe (M6 Welle 6, `GG-DEPLOY-006`, Lastenheft
    Z. 1876-1879).

    Probt die vier Lastenheft-Pflicht-Komponenten (`api`/`ui`/`db`/
    `simulation`) ueber den `ReadinessProbeAdapter` und aggregiert
    den Three-State-Status (Welle-6-D-2). HTTP-Status: `200` bei
    `healthy`/`degraded`, `503` bei `unhealthy` (Kubernetes-
    Readiness-Konvention).
    """
    adapter = ReadinessProbeAdapter(
        run_repository=repository,
        simulation_healthcheck=tick_loop_registry.any_healthcheck_adapter(),
    )
    report = await adapter.check()
    if report.status == "unhealthy":
        response.status_code = 503
    return report
