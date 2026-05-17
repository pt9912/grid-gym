"""Tests fuer `TickLoop` (M1 Welle 4, `GG-SIM-001`/`002`/`005`).

Pinnt:
- Determinismus: zwei TickLoops mit identischem Seed + Setup
  liefern byte-identische TickResult-Sequenzen via canonical_json.
- Snapshot/Resume (`GG-SIM-005`): snapshot nach n Ticks ->
  from_snapshot -> Rest identisch zu ununterbrochenem Lauf.
- `tick()`-Semantik: tick-Nummer + simulation_time stimmen.
- Snapshot-Konsistenz-Pruefungen (clock/random mismatches).
- Typisierte Snapshot-Format-Negativ-Pfade.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

import pytest

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.event import Event
from grid_gym.hexagon.core.errors import (
    TickLoopSnapshotClockMismatchError,
    TickLoopSnapshotMissingKeysError,
    TickLoopSnapshotRandomMismatchError,
    TickLoopSnapshotVersionError,
    TickLoopSnapshotWrongTypeError,
)
from grid_gym.hexagon.core.serialization.canonical import canonical_json
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_event(event_id: str, simulation_time: int) -> Event:
    return Event(
        event_id=event_id,
        simulation_time=simulation_time,
        source="src",
        target="tgt",
        type="tick",
        payload={},
        priority=0,
        sequence=0,
    )


def _build_loop(
    *,
    seed: int = 42,
    tick_ms: int = 100,
    events: tuple[Event, ...] = (),
) -> TickLoop:
    scheduler = Scheduler()
    for event in events:
        scheduler.add(event)
    return TickLoop(
        run_id="run-1",
        tick_ms=tick_ms,
        clock=FakeClock(),
        random=MersenneTwisterRandomPort(seed=seed),
        scheduler=scheduler,
    )


# ---------------------------------------------------------------------------
# Tick-Semantik
# ---------------------------------------------------------------------------


def test_tick_count_starts_at_zero_and_increments() -> None:
    loop = _build_loop()
    assert loop.tick_count == 0
    result_0 = loop.tick()
    assert result_0.tick == 0
    assert loop.tick_count == 1
    result_1 = loop.tick()
    assert result_1.tick == 1
    assert loop.tick_count == 2


def test_tick_advances_clock_by_tick_ms() -> None:
    loop = _build_loop(tick_ms=100)
    result = loop.tick()
    assert result.simulation_time == 100
    next_result = loop.tick()
    assert next_result.simulation_time == 200


def test_tick_returns_due_events_in_tie_breaking_order() -> None:
    events = (
        _make_event("e2", 100),
        _make_event("e1", 50),
        _make_event("e3", 150),
    )
    loop = _build_loop(tick_ms=100, events=events)
    first = loop.tick()
    assert [event.event_id for event in first.popped_events] == ["e1", "e2"]
    second = loop.tick()
    assert [event.event_id for event in second.popped_events] == ["e3"]


def test_tick_returns_empty_telemetry_in_welle_4() -> None:
    """Geraetemodelle existieren noch nicht — `emitted_telemetry`
    bleibt leer."""
    loop = _build_loop()
    assert loop.tick().emitted_telemetry == ()


# ---------------------------------------------------------------------------
# Determinismus-Property (`GG-SIM-001`)
# ---------------------------------------------------------------------------


def test_two_loops_with_same_seed_yield_byte_identical_results() -> None:
    """Zwei TickLoops mit identischem Setup + Seed produzieren
    byte-identische canonical_json-Exports der TickResult-Sequenz."""
    events = (
        _make_event("e1", 100),
        _make_event("e2", 200),
        _make_event("e3", 300),
    )
    loop_a = _build_loop(seed=42, tick_ms=100, events=events)
    loop_b = _build_loop(seed=42, tick_ms=100, events=events)
    results_a = [asdict(loop_a.tick()) for _ in range(5)]
    results_b = [asdict(loop_b.tick()) for _ in range(5)]
    assert canonical_json(results_a) == canonical_json(results_b)


def test_different_seeds_yield_different_sub_port_streams() -> None:
    """Sanity-Check: gleicher Setup, unterschiedliche Seeds —
    obwohl Welle 4 noch keine Geraete-Konsumenten hat, ist die
    `random.snapshot_as_mapping()` zwischen den Loops verschieden.
    """
    loop_a = _build_loop(seed=1)
    loop_b = _build_loop(seed=2)
    # Beide ticken einmal — random-state wird nicht angefasst, weil
    # Welle 4 keine Geraete hat, aber der initiale State unterscheidet
    # sich.
    loop_a.tick()
    loop_b.tick()
    snapshot_a = loop_a.snapshot()
    snapshot_b = loop_b.snapshot()
    sub_a = snapshot_a["sub_snapshots"]
    sub_b = snapshot_b["sub_snapshots"]
    assert isinstance(sub_a, Mapping)
    assert isinstance(sub_b, Mapping)
    assert sub_a["random_root"] != sub_b["random_root"]


# ---------------------------------------------------------------------------
# Snapshot / Resume (`GG-SIM-005`)
# ---------------------------------------------------------------------------


def test_snapshot_has_envelope_keys_and_sub_snapshots() -> None:
    loop = _build_loop()
    snap = loop.snapshot()
    assert snap["version"] == 1
    assert snap["run_id"] == "run-1"
    assert snap["tick_count"] == 0
    assert snap["tick_ms"] == 100
    sub = snap["sub_snapshots"]
    assert isinstance(sub, Mapping)
    assert set(sub.keys()) == {"scheduler", "random_root"}


def test_snapshot_is_canonical_json_compatible() -> None:
    """Snapshot-Mapping geht ohne Encoder-Error durch canonical_json
    (Welle-1-Konvention: alle sub_snapshots sind Mappings)."""
    loop = _build_loop(events=(_make_event("e1", 50),))
    loop.tick()
    canonical_json(loop.snapshot())  # darf nicht werfen


def test_resume_continues_byte_identical_to_uninterrupted_run() -> None:
    """`GG-SIM-005`: nach Snapshot fortgesetzt → ab Snapshot
    gleiche Werte wie ein ununterbrochener Lauf."""
    events = (_make_event(f"e{i}", i * 50) for i in range(1, 10))
    event_tuple = tuple(events)

    uninterrupted = _build_loop(seed=42, tick_ms=100, events=event_tuple)
    full_run = [asdict(uninterrupted.tick()) for _ in range(8)]

    # Zweiter Lauf: snapshot nach 3 Ticks, dann from_snapshot, dann
    # weitere 5 Ticks.
    interrupted = _build_loop(seed=42, tick_ms=100, events=event_tuple)
    head = [asdict(interrupted.tick()) for _ in range(3)]
    snapshot = interrupted.snapshot()

    # Resume: clock + random bereits restored injizieren.
    resumed_clock = FakeClock()
    sim_time = snapshot["simulation_time"]
    assert isinstance(sim_time, int)
    resumed_clock.advance(sim_time)
    sub = snapshot["sub_snapshots"]
    assert isinstance(sub, Mapping)
    random_payload = sub["random_root"]
    assert isinstance(random_payload, Mapping)
    resumed_random = MersenneTwisterRandomPort.from_snapshot(canonical_json(random_payload))
    resumed = TickLoop.from_snapshot(snapshot, clock=resumed_clock, random=resumed_random)
    tail = [asdict(resumed.tick()) for _ in range(5)]

    assert canonical_json(head + tail) == canonical_json(full_run)


def test_resume_preserves_tick_count() -> None:
    loop = _build_loop()
    for _ in range(7):
        loop.tick()
    snap = loop.snapshot()
    resumed_clock = FakeClock()
    sim_time = snap["simulation_time"]
    assert isinstance(sim_time, int)
    resumed_clock.advance(sim_time)
    sub = snap["sub_snapshots"]
    assert isinstance(sub, Mapping)
    random_payload = sub["random_root"]
    assert isinstance(random_payload, Mapping)
    resumed_random = MersenneTwisterRandomPort.from_snapshot(canonical_json(random_payload))
    resumed = TickLoop.from_snapshot(snap, clock=resumed_clock, random=resumed_random)
    assert resumed.tick_count == 7
    # Naechster tick() liefert tick == 7.
    assert resumed.tick().tick == 7


# ---------------------------------------------------------------------------
# Snapshot-Konsistenz-Pruefungen (Clock/Random-Mismatch)
# ---------------------------------------------------------------------------


def test_from_snapshot_rejects_clock_mismatch() -> None:
    loop = _build_loop()
    loop.tick()
    snap = loop.snapshot()
    # Falsch initialisierte Clock (steht bei 0 statt simulation_time).
    wrong_clock = FakeClock()
    sub = snap["sub_snapshots"]
    assert isinstance(sub, Mapping)
    random_payload = sub["random_root"]
    assert isinstance(random_payload, Mapping)
    resumed_random = MersenneTwisterRandomPort.from_snapshot(canonical_json(random_payload))
    with pytest.raises(TickLoopSnapshotClockMismatchError):
        TickLoop.from_snapshot(snap, clock=wrong_clock, random=resumed_random)


def test_from_snapshot_rejects_random_mismatch() -> None:
    loop = _build_loop(seed=42)
    loop.tick()
    snap = loop.snapshot()
    sim_time = snap["simulation_time"]
    assert isinstance(sim_time, int)
    resumed_clock = FakeClock()
    resumed_clock.advance(sim_time)
    # Falsche Random-Instanz: anderer Seed.
    wrong_random = MersenneTwisterRandomPort(seed=999)
    with pytest.raises(TickLoopSnapshotRandomMismatchError):
        TickLoop.from_snapshot(snap, clock=resumed_clock, random=wrong_random)


# ---------------------------------------------------------------------------
# Snapshot-Format-Negativ-Pfade
# ---------------------------------------------------------------------------


def _minimal_state() -> dict[str, object]:
    return {
        "version": 1,
        "run_id": "r",
        "simulation_time": 0,
        "tick_count": 0,
        "tick_ms": 100,
        "sub_snapshots": {
            "scheduler": {"version": 1, "pending_events": []},
            "random_root": {
                "version": 1,
                "seed": 0,
                "sub_path": [],
                "rng_version": 3,
                "rng_state": [0] * 625,
            },
        },
    }


def test_from_snapshot_rejects_missing_top_level_key() -> None:
    state = _minimal_state()
    del state["run_id"]
    with pytest.raises(TickLoopSnapshotMissingKeysError):
        TickLoop.from_snapshot(state, clock=FakeClock(), random=MersenneTwisterRandomPort(seed=0))


def test_from_snapshot_rejects_wrong_run_id_type() -> None:
    state = _minimal_state()
    state["run_id"] = 42
    with pytest.raises(TickLoopSnapshotWrongTypeError):
        TickLoop.from_snapshot(state, clock=FakeClock(), random=MersenneTwisterRandomPort(seed=0))


def test_from_snapshot_rejects_bool_int_field() -> None:
    """`bool` ist `int`-Subklasse — fuer int-Felder explizit
    abgelehnt."""
    state = _minimal_state()
    state["tick_count"] = True
    with pytest.raises(TickLoopSnapshotWrongTypeError):
        TickLoop.from_snapshot(state, clock=FakeClock(), random=MersenneTwisterRandomPort(seed=0))


def test_from_snapshot_rejects_non_mapping_sub_snapshots() -> None:
    state = _minimal_state()
    state["sub_snapshots"] = "not-a-mapping"
    with pytest.raises(TickLoopSnapshotWrongTypeError):
        TickLoop.from_snapshot(state, clock=FakeClock(), random=MersenneTwisterRandomPort(seed=0))


def test_from_snapshot_rejects_missing_sub_snapshot() -> None:
    state = _minimal_state()
    sub = state["sub_snapshots"]
    assert isinstance(sub, dict)
    del sub["random_root"]
    with pytest.raises(TickLoopSnapshotMissingKeysError):
        TickLoop.from_snapshot(state, clock=FakeClock(), random=MersenneTwisterRandomPort(seed=0))


def test_from_snapshot_rejects_unknown_version() -> None:
    state = _minimal_state()
    state["version"] = 99
    with pytest.raises(TickLoopSnapshotVersionError):
        TickLoop.from_snapshot(state, clock=FakeClock(), random=MersenneTwisterRandomPort(seed=0))
