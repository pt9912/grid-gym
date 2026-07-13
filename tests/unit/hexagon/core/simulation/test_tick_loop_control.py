"""M5-Welle-4a-Tests fuer die TickLoop-Control-Surface (ADR 0039
Decision 13).

Pinnt:

- `_control_state`-Default ist ``"pending"``.
- `request_pause`/`request_resume`/`request_stop` fuehren die
  State-Transitions aus der ADR-0039-Matrix durch.
- Invalid-Transitions werfen `TickLoopInvalidTransitionError`
  mit `current_state`/`target_state`.
- `tick()` mit `_control_state == "paused"` ist ein No-op (kein
  Tick-Fortschritt; `TickResult.paused=True`).
- `tick()` mit terminalen States wirft `TickLoopStoppedError`.
- Erster Tick aus ``"pending"`` flippt auto nach ``"running"``.
- Repository-Mirror-Sequenz: `update_status` wird vor dem
  internen Feld-Set gerufen (Persistenz-Wahrheit zuerst).
"""

from __future__ import annotations

import pytest

from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.errors import (
    TickLoopInvalidTransitionError,
    TickLoopStoppedError,
)
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import (
    FakeClock,
    FixedSeedRandom,
    InMemoryRunRepository,
)


def _make_loop(*, run_repository: InMemoryRunRepository | None = None) -> TickLoop:
    return TickLoop(
        run_id="welle-4a-control-test",
        tick_ms=100,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        run_repository=run_repository,
    )


def _seeded_repo(run_id: str = "welle-4a-control-test") -> InMemoryRunRepository:
    repo = InMemoryRunRepository()
    metadata = RunMetadata(
        run_id=run_id,
        scenario_hash="0" * 64,
        schema_version="grid-gym.scenario.v1",
        seed=42,
        tick_ms=100,
        started_at="",
        ended_at="",
        tool_version="0.1.0",
    )
    repo.save(metadata)
    return repo


# ---------------------------------------------------------------------------
# Default-State + Properties
# ---------------------------------------------------------------------------


def test_control_state_default_is_pending() -> None:
    """ADR 0039 §2.2: TickLoop startet im State ``pending``."""
    loop = _make_loop()
    assert loop.control_state == "pending"


# ---------------------------------------------------------------------------
# Transitions (6 erlaubte Pfade)
# ---------------------------------------------------------------------------


def test_request_start_from_pending_flips_to_running() -> None:
    """Slice 078 (`GG-UI-004`): `start` aus `pending` → `running`."""
    loop = _make_loop()
    assert loop.control_state == "pending"
    loop.request("start")
    assert loop.control_state == "running"


def test_request_start_from_running_is_idempotent_noop() -> None:
    """Slice 078 (`GG-UI-004`): `start` auf einem bereits laufenden Lauf ist ein
    idempotenter No-op (`current == target == running` → kein State-Wechsel, kein
    Fehler; derselbe No-op-Pfad wie `resume`/`pause`/`stop` auf ihrem Zielstate)."""
    loop = _make_loop()
    loop.request("resume")  # pending → running
    loop.request("start")  # No-op
    assert loop.control_state == "running"


def test_request_start_from_paused_raises_invalid_transition() -> None:
    """Slice 078 (`GG-UI-004`): `start` ist **nur** aus `pending` gueltig — aus
    `paused` (≠ Zielstate `running`, nicht in `allowed_from`) eine Invalid-Transition
    (409). Unterscheidet `start` klar von `resume` (das aus `paused` erlaubt ist)."""
    loop = _make_loop()
    loop.request("pause")  # pending → paused
    with pytest.raises(TickLoopInvalidTransitionError) as exc_info:
        loop.request("start")
    assert exc_info.value.current_state == "paused"
    assert exc_info.value.target_state == "running"


def test_request_start_mirrors_to_run_repository() -> None:
    """Slice 078: der `start`-Flip persistiert ueber den Repository-Mirror."""
    repo = _seeded_repo()
    loop = _make_loop(run_repository=repo)
    loop.request("start")
    assert repo.get_status("welle-4a-control-test") == "running"


def test_request_pause_from_pending_flips_state() -> None:
    loop = _make_loop()
    loop.request("pause")
    assert loop.control_state == "paused"


def test_request_resume_from_paused_flips_state() -> None:
    loop = _make_loop()
    loop.request("pause")
    loop.request("resume")
    assert loop.control_state == "running"


def test_request_stop_from_running_flips_state() -> None:
    loop = _make_loop()
    loop.request("resume")  # pending → running
    loop.request("stop")
    assert loop.control_state == "stopped"


def test_request_stop_from_paused_flips_state() -> None:
    loop = _make_loop()
    loop.request("pause")
    loop.request("stop")
    assert loop.control_state == "stopped"


def test_request_pause_is_idempotent_no_op_from_paused() -> None:
    """Idempotente Wiederholung auf demselben State ist No-op."""
    loop = _make_loop()
    loop.request("pause")
    loop.request("pause")
    assert loop.control_state == "paused"


def test_request_stop_is_idempotent_no_op_from_stopped() -> None:
    loop = _make_loop()
    loop.request("stop")
    loop.request("stop")
    assert loop.control_state == "stopped"


# ---------------------------------------------------------------------------
# Invalid-Transitions
# ---------------------------------------------------------------------------


def test_request_resume_from_stopped_raises_invalid_transition() -> None:
    loop = _make_loop()
    loop.request("stop")
    with pytest.raises(TickLoopInvalidTransitionError) as exc_info:
        loop.request("resume")
    assert exc_info.value.current_state == "stopped"
    assert exc_info.value.target_state == "running"


def test_request_pause_from_stopped_raises_invalid_transition() -> None:
    loop = _make_loop()
    loop.request("stop")
    with pytest.raises(TickLoopInvalidTransitionError):
        loop.request("pause")


# ---------------------------------------------------------------------------
# Pre-Tick-Guard
# ---------------------------------------------------------------------------


def test_tick_when_paused_returns_paused_result_no_progress() -> None:
    """ADR 0039 §2.2: `tick()` im `paused`-State skippt den Body."""
    loop = _make_loop()
    loop.request("pause")
    result = loop.tick()
    assert result.paused is True
    assert result.popped_events == ()
    assert result.emitted_telemetry == ()
    assert loop.tick_count == 0  # kein Fortschritt


def test_tick_when_stopped_raises_tick_loop_stopped_error() -> None:
    loop = _make_loop()
    loop.request("stop")
    with pytest.raises(TickLoopStoppedError):
        loop.tick()


def test_first_tick_from_pending_auto_flips_to_running() -> None:
    """ADR 0039 §2.2: erster produktiver Tick flippt `pending` →
    `running` als Side-Effect."""
    loop = _make_loop()
    assert loop.control_state == "pending"
    loop.tick()
    assert loop.control_state == "running"
    assert loop.tick_count == 1


# ---------------------------------------------------------------------------
# Repository-Mirror-Sequenz
# ---------------------------------------------------------------------------


def test_request_pause_mirrors_to_run_repository() -> None:
    """ADR 0039 §2.2: `request_*`-Methoden persistieren den Status
    via Repository, bevor sie den lokalen Cache mutieren."""
    repo = _seeded_repo()
    loop = _make_loop(run_repository=repo)
    loop.request("pause")
    assert repo.get_status("welle-4a-control-test") == "paused"


def test_tick_auto_flip_mirrors_to_run_repository() -> None:
    """ADR 0039 §2.2: Auto-Flip `pending` → `running` im ersten Tick
    persistiert auch ueber den Repository-Mirror."""
    repo = _seeded_repo()
    loop = _make_loop(run_repository=repo)
    loop.tick()
    assert repo.get_status("welle-4a-control-test") == "running"
