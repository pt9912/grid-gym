"""M5-Welle-4b-Review-Fixes #3 + #8: TickLoop.from_snapshot
nimmt jetzt `run_repository`, `alarm_id_source` und
`control_state` als Kwargs entgegen.

Vorher hat `from_snapshot`:

- `_run_repository=None` gesetzt — `request("pause")` mutierte
  nur den Cache, nicht den persistierten Status.
- `_alarm_id_source` auf Production-`uuid.uuid4` gestellt —
  deterministische Test-Stubs gingen ueber den Resume verloren.
- `_control_state="pending"` gelassen — der erste Tick auto-
  flippte auf `running` und ein gepauster Snapshot startete
  silent durch.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator

from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import (
    FakeClock,
    FixedSeedRandom,
    InMemoryRunRepository,
)


def _make_loop(**kwargs: object) -> TickLoop:
    base: dict[str, object] = {
        "run_id": "welle-4b-resume",
        "tick_ms": 1000,
        "clock": FakeClock(),
        "random": FixedSeedRandom(seed=42),
        "scheduler": Scheduler(),
    }
    base.update(kwargs)
    return TickLoop(**base)  # type: ignore[arg-type]


def _counting_alarm_ids() -> Iterator[str]:
    counter = itertools.count()
    while True:
        yield f"alarm-{next(counter)}"


def test_from_snapshot_restores_paused_control_state() -> None:
    """Welle-4b-Review-Fix #3: bei `control_state="paused"`-Kwarg
    bleibt der resumed Loop pausiert; der erste Tick liefert
    `paused_result`."""
    loop = _make_loop()
    snapshot = loop.snapshot()
    # Restore-Clock muss simulation_time matchen (von tick_count=0).
    restore_clock = FakeClock()
    restored = TickLoop.from_snapshot(
        snapshot,
        clock=restore_clock,
        random=FixedSeedRandom(seed=42),
        control_state="paused",
    )
    assert restored.control_state == "paused"
    result = restored.tick()
    # paused_result hat tick_count=0 und keine emitted_alarms.
    assert result.tick == 0
    assert result.emitted_alarms == ()
    # Der Tick-Counter wird nicht inkrementiert (paused-Pfad).
    assert restored.tick_count == 0


def test_from_snapshot_default_control_state_is_pending() -> None:
    """Welle-4b-Review-Fix #3: ohne `control_state`-Kwarg bleibt
    der Loop auf `pending` (Backward-Compat fuer Aufrufer, die
    den Kwarg noch nicht setzen)."""
    loop = _make_loop()
    snapshot = loop.snapshot()
    restored = TickLoop.from_snapshot(
        snapshot,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
    )
    assert restored.control_state == "pending"


def test_from_snapshot_wires_run_repository_for_post_resume_mirroring() -> None:
    """Welle-4b-Review-Fix #8: `from_snapshot(run_repository=...)`
    wired den Mirror-Pfad — `request("pause")` nach Resume
    persistiert in das injizierte Repository."""
    repository = InMemoryRunRepository()
    # Seed-Run im Repository, damit `update_status` Funktioniert.
    from grid_gym.hexagon.core.domain.run import RunMetadata

    repository.save(
        RunMetadata(
            run_id="welle-4b-resume",
            scenario_hash="0" * 64,
            schema_version="grid-gym.scenario.v1",
            seed=42,
            tick_ms=1000,
            started_at="",
            ended_at="",
            tool_version="0.1.0",
        )
    )
    loop = _make_loop()
    snapshot = loop.snapshot()
    restored = TickLoop.from_snapshot(
        snapshot,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        run_repository=repository,
        control_state="running",
    )
    restored.request("pause")
    # Mirror-Pfad: Repository hat den State persistiert.
    assert repository.get_status("welle-4b-resume") == "paused"


def test_from_snapshot_preserves_deterministic_alarm_id_source() -> None:
    """Welle-4b-Review-Fix #8: `from_snapshot(alarm_id_source=...)`
    injiziert den Test-Stub. Ohne den Kwarg wuerde der resumed
    Loop UUIDv4 generieren und Test-Snapshot-Asserts brechen."""
    loop = _make_loop()
    snapshot = loop.snapshot()
    ids = _counting_alarm_ids()
    restored = TickLoop.from_snapshot(
        snapshot,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        alarm_id_source=lambda: next(ids),
    )
    # Direkter Property-Check ueber den injizierten Source —
    # ohne Devices laufen keine Alarms an, der Source wird aber
    # vom Konstruktor durchgereicht.
    assert restored._alarm_id_source() == "alarm-0"
    assert restored._alarm_id_source() == "alarm-1"
