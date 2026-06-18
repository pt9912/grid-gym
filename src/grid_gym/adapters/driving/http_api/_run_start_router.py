"""FastAPI-Router fuer `POST /runs/{run_id}/start` (Multi-Run-Execution S3,
ADR 0069 §2.4).

Verbindet Scenario-Store (S1) + RunDriverRegistry (S2): loest das im Store
hinterlegte Scenario per `scenario_hash` auf, baut den per-Run-`TickLoop` und
startet ihn als Driver in der Registry.

Der per-Run-Loop-Bau (`build_tick_loop`, `core.scenario`) laeuft ueber die per
Hook-Inversion (ADR 0054) injizierte Composition-Bridge
(`_register_run_driver_builder`); dieser Router importiert `core.scenario`
**nicht** (`AC-ADAPTER-PURE`). `grid_gym.composition.asgi` registriert die
Bridge beim Import. Ausgelagert aus `app.py` (`AC-NO-GOD-UTILS`).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from grid_gym.adapters.driving.http_api._dependencies import (
    get_run_repository,
    get_scenario_store,
)
from grid_gym.adapters.driving.http_api._run_driver_registry import (
    RunDriver,
    RunDriverRegistry,
    get_run_driver_registry,
)
from grid_gym.adapters.driving.http_api._schemas import ErrorResponse, RunStartResponse
from grid_gym.hexagon.core.domain.scenario import Scenario
from grid_gym.hexagon.core.errors import (
    RunAlreadyActiveError,
    RunConcurrencyLimitError,
    RunNotFoundError,
    ScenarioError,
    SnapshotFormatError,
)
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort
from grid_gym.hexagon.ports.driven.scenario_store import ScenarioStorePort

runs_start_router = APIRouter(tags=["runs"])


RunDriverBuilder = Callable[[Scenario, str, RunRepositoryPort], RunDriver]
"""Signatur der per-Run-Driver-Bau-Bridge (Composition: baut `TickLoop` +
`DemoTickLoopDriver` aus einem Scenario). Per `_register_run_driver_builder`
injiziert (Hook-Inversion, ADR 0054) — dieser Router importiert
`build_tick_loop` (`core.scenario`) nicht (`AC-ADAPTER-PURE`)."""


class _RunDriverBuilderNotRegisteredError(RuntimeError):
    """`POST /runs/{id}/start` aufgerufen, aber keine Driver-Bau-Bridge
    registriert: die App lief ueber den reinen Adapter-Entrypoint statt
    `grid_gym.composition.asgi:app` (ADR 0069 §2.4 / ADR 0054)."""

    def __init__(self) -> None:
        super().__init__(
            "No run-driver builder is registered. Start the app via the "
            "composition entrypoint `grid_gym.composition.asgi:app`, not the "
            "bare adapter `grid_gym.adapters.driving.http_api:app`."
        )


def _raise_run_driver_builder_unregistered(
    _scenario: Scenario, _run_id: str, _repository: RunRepositoryPort
) -> RunDriver:
    """Fail-closed Default — aktiv, solange der Composition-Root keine Bridge
    registriert hat."""
    raise _RunDriverBuilderNotRegisteredError


_run_driver_builder: RunDriverBuilder = _raise_run_driver_builder_unregistered


def _register_run_driver_builder(builder: RunDriverBuilder) -> None:
    """Injiziert die per-Run-Driver-Bau-Bridge (Composition Root,
    `grid_gym.composition.asgi`). Der `POST /runs/{id}/start`-Endpoint ruft sie."""
    global _run_driver_builder
    _run_driver_builder = builder


@runs_start_router.post(
    "/runs/{run_id}/start",
    response_model=RunStartResponse,
    status_code=202,
)
async def post_run_start(
    run_id: str,
    repository: Annotated[RunRepositoryPort, Depends(get_run_repository)],
    scenario_store: Annotated[ScenarioStorePort, Depends(get_scenario_store)],
    registry: Annotated[RunDriverRegistry, Depends(get_run_driver_registry)],
) -> RunStartResponse:
    """Startet einen persistierten Lauf (Multi-Run-Execution S3, ADR 0069 §2.4).

    Loest das im Store hinterlegte Scenario per `scenario_hash` auf, baut den
    per-Run-`TickLoop` (Composition-Bridge) und startet ihn in der
    `RunDriverRegistry`.

    - Lauf nicht persistiert → HTTP 404 `run_not_found`.
    - kein Scenario-Content im Store → HTTP 422 `scenario_content_not_found`.
    - Scenario load-valid, aber nicht baubar → HTTP 422 `scenario_build_failed`.
    - Lauf laeuft bereits → HTTP 409 `run_already_active`.
    - Concurrency-Limit erreicht → HTTP 429 `run_concurrency_limit`.
    """
    try:
        metadata = repository.get_by_id(run_id)
    except RunNotFoundError as exc:
        error = ErrorResponse(
            code="run_not_found",
            message=f"Run {run_id!r} not found.",
            run_id=run_id,
        )
        raise HTTPException(status_code=404, detail=error.model_dump()) from exc

    scenario = scenario_store.get(metadata.scenario_hash)
    if scenario is None:
        error = ErrorResponse(
            code="scenario_content_not_found",
            message=(
                f"No scenario content stored for hash {metadata.scenario_hash!r}; "
                "POST it to /scenarios before starting the run."
            ),
            run_id=run_id,
        )
        raise HTTPException(status_code=422, detail=error.model_dump())

    try:
        driver = _run_driver_builder(scenario, run_id, repository)
    except (ScenarioError, SnapshotFormatError) as exc:
        # Das Scenario laedt (POST /scenarios), laesst sich aber nicht in einen
        # TickLoop bauen (z. B. unvollstaendige Device-Params) — Client-Daten-
        # Problem, kein Server-Fehler.
        error = ErrorResponse(
            code="scenario_build_failed",
            message=(
                f"Stored scenario for run {run_id!r} could not be built into a tick loop: {exc}"
            ),
            run_id=run_id,
        )
        raise HTTPException(status_code=422, detail=error.model_dump()) from exc
    try:
        registry.register_and_start(run_id, driver)
    except RunAlreadyActiveError as exc:
        error = ErrorResponse(code="run_already_active", message=str(exc), run_id=run_id)
        raise HTTPException(status_code=409, detail=error.model_dump()) from exc
    except RunConcurrencyLimitError as exc:
        error = ErrorResponse(code="run_concurrency_limit", message=str(exc), run_id=run_id)
        raise HTTPException(status_code=429, detail=error.model_dump()) from exc

    return RunStartResponse(run_id=run_id, status="running")
