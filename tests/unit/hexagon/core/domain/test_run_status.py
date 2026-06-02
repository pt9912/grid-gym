"""M5-Welle-4a-Tests fuer den `RunStatus`-Literal-Alias (ADR 0039
Decision 12).

Smoke-Tests: das Literal hat die fuenf Welle-4a-Werte
``pending``/``running``/``paused``/``stopped``/``completed`` und
ist ueber den Domain-Pfad importierbar (`hexagon.core.domain.run`).
Schema-Layer-Alias `RunState` zeigt auf denselben Type.
"""

from __future__ import annotations

import typing

from grid_gym.adapters.driving.http_api._schemas import RunState
from grid_gym.hexagon.core.domain.run import RunStatus


def test_run_status_literal_has_five_welle_4a_values() -> None:
    """ADR 0039 §2.1: RunStatus deckt die fuenf Lifecycle-States ab."""
    args = typing.get_args(RunStatus)
    assert set(args) == {"pending", "running", "paused", "stopped", "completed"}


def test_run_state_schema_alias_points_to_domain_run_status() -> None:
    """ADR 0039 §2.3: Schema-Layer-Alias `RunState` ist identisch
    zum Domain-`RunStatus` (kein eigenes Literal)."""
    assert RunState is RunStatus
