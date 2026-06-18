"""FastAPI-Router fuer `POST /scenarios` (Multi-Run-Execution S1,
ADR 0069 §2.1).

Ausgelagert aus `app.py`, damit der `AC-NO-GOD-UTILS`-Contract (max 5 public
top-level functions pro Modul) in `app.py` nicht reisst — Pattern analog
`_runs_router.py`/`_runs_action_router.py`.

Die Kanonisierung + Hash-Berechnung des geposteten Szenarios laeuft ueber die
per Hook-Inversion (ADR 0054) injizierte Composition-Bridge
(`_register_scenario_intake`); dieser Router importiert `load_scenario`
(`core.scenario`) **nicht** (`AC-ADAPTER-PURE`). `grid_gym.composition.asgi`
registriert die Bridge beim Import.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from grid_gym.adapters.driving.http_api._dependencies import get_scenario_store
from grid_gym.adapters.driving.http_api._schemas import (
    ErrorResponse,
    ScenarioCreateRequest,
    ScenarioCreateResponse,
)
from grid_gym.hexagon.core.errors import (
    ScenarioError,
    ScenarioHashMismatchError,
    SnapshotFormatError,
)
from grid_gym.hexagon.core.serialization.canonical import CanonicalSerializationError
from grid_gym.hexagon.ports.driven.scenario_store import ScenarioStorePort
from grid_gym.scenario_yaml import ScenarioYamlError

scenarios_router = APIRouter(tags=["scenarios"])


ScenarioIntake = Callable[[ScenarioStorePort, Mapping[str, object], str], str]
"""Signatur der Scenario-Intake-Bridge
(`composition.scenario_intake.intake_scenario`). Per `_register_scenario_intake`
aus dem Composition-Root injiziert (ADR 0054) — dieser Router importiert die
Bridge nicht direkt, sonst entstuende die indirekte Kette Adapter → composition
→ `core.scenario` (`AC-ADAPTER-PURE`, 041-C3b)."""


class _ScenarioIntakeNotRegisteredError(RuntimeError):
    """`POST /scenarios` aufgerufen, aber keine Scenario-Intake-Bridge
    registriert: die App lief ueber den reinen Adapter-Entrypoint statt
    `grid_gym.composition.asgi:app` (ADR 0069 §2.1 / ADR 0054)."""

    def __init__(self) -> None:
        super().__init__(
            "No scenario intake bridge is registered. Start the app via the "
            "composition entrypoint `grid_gym.composition.asgi:app`, not the "
            "bare adapter `grid_gym.adapters.driving.http_api:app`."
        )


def _raise_scenario_intake_unregistered(
    _store: ScenarioStorePort, _raw: Mapping[str, object], _claimed_hash: str
) -> str:
    """Fail-closed Default-Intake — aktiv, solange der Composition-Root keine
    Bridge registriert hat."""
    raise _ScenarioIntakeNotRegisteredError


_scenario_intake: ScenarioIntake = _raise_scenario_intake_unregistered


def _register_scenario_intake(intake: ScenarioIntake) -> None:
    """Injiziert die Scenario-Intake-Bridge (Composition Root,
    `grid_gym.composition.asgi`). Der `POST /scenarios`-Endpoint ruft sie."""
    global _scenario_intake
    _scenario_intake = intake


@scenarios_router.post(
    "/scenarios",
    response_model=ScenarioCreateResponse,
    status_code=201,
)
def post_scenarios(
    request: Annotated[ScenarioCreateRequest, ...],
    store: Annotated[ScenarioStorePort, Depends(get_scenario_store)],
) -> ScenarioCreateResponse:
    """Legt ein kanonisiertes Szenario unter seinem `scenario_hash` ab
    (Multi-Run-Execution S1, ADR 0069 §2.1 / `GG-SCN-003`/`GG-SCN-004`).

    Body: Szenario-Content (numerische Decimal-Felder als Strings, Variante A)
    + erwarteter `scenario_hash`. Die Kanonisierung + Hash-Berechnung laeuft
    ueber die injizierte Composition-Bridge (Hook-Inversion, ADR 0054).

    - Schema-Verletzung (inkl. `float` an einer Decimal-Stelle) → HTTP 422
      `invalid_scenario`.
    - Client-Hash != server-berechneter Hash → HTTP 422 `scenario_hash_mismatch`.
    """
    try:
        stored_hash = _scenario_intake(store, request.scenario, request.scenario_hash)
    except ScenarioHashMismatchError as exc:
        error = ErrorResponse(
            code="scenario_hash_mismatch",
            message=str(exc),
            details={"claimed": exc.claimed, "computed": exc.computed},
        )
        raise HTTPException(status_code=422, detail=error.model_dump()) from exc
    except (
        ScenarioError,
        SnapshotFormatError,
        ScenarioYamlError,
        CanonicalSerializationError,
    ) as exc:
        error = ErrorResponse(code="invalid_scenario", message=str(exc))
        raise HTTPException(status_code=422, detail=error.model_dump()) from exc
    return ScenarioCreateResponse(scenario_hash=stored_hash)
