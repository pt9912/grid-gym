"""Tests fuer `Scheduler` (M1 Welle 3, `GG-ARCH-006`).

Pinnt:
- Tie-Breaking `(time, priority, source, sequence, event_id)`.
- Permutation der Eingabe-Events veraendert die Pop-Reihenfolge
  NICHT (hypothesis-Property).
- `pop_due(time)`-Semantik (alle Events mit `event_time <= time`).
- Snapshot/Resume-Roundtrip.
- Typisierte Negativ-Pfade beim Snapshot-Format.
- Duplicate-`event_id`-Schutz.
"""

from __future__ import annotations

import random
from decimal import Decimal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from grid_gym.hexagon.core.domain.event import Event
from grid_gym.hexagon.core.errors import (
    SchedulerDuplicateEventIdError,
    SchedulerSnapshotEventFieldError,
    SchedulerSnapshotMissingKeysError,
    SchedulerSnapshotVersionError,
    SchedulerSnapshotWrongTypeError,
)
from grid_gym.hexagon.core.simulation.scheduler import Scheduler

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_event(
    event_id: str,
    *,
    simulation_time: int = 0,
    priority: int = 0,
    source: str = "src",
    sequence: int = 0,
    target: str = "tgt",
    type_: str = "tick",
) -> Event:
    return Event(
        event_id=event_id,
        simulation_time=simulation_time,
        source=source,
        target=target,
        type=type_,
        payload={},
        priority=priority,
        sequence=sequence,
    )


# ---------------------------------------------------------------------------
# Tie-Breaking-Smoketests
# ---------------------------------------------------------------------------


def test_pop_due_returns_empty_for_empty_scheduler() -> None:
    scheduler = Scheduler()
    assert scheduler.pop_due(100) == []
    assert scheduler.is_empty()
    assert len(scheduler) == 0


def test_pop_due_returns_events_sorted_by_time() -> None:
    scheduler = Scheduler()
    scheduler.add(_make_event("e1", simulation_time=200))
    scheduler.add(_make_event("e2", simulation_time=100))
    scheduler.add(_make_event("e3", simulation_time=150))
    due = scheduler.pop_due(1000)
    assert [event.event_id for event in due] == ["e2", "e3", "e1"]


def test_pop_due_uses_priority_as_secondary_key() -> None:
    """Bei gleichem `simulation_time` wird nach `priority` (asc) sortiert."""
    scheduler = Scheduler()
    scheduler.add(_make_event("e1", simulation_time=100, priority=10))
    scheduler.add(_make_event("e2", simulation_time=100, priority=1))
    scheduler.add(_make_event("e3", simulation_time=100, priority=5))
    due = scheduler.pop_due(100)
    assert [event.event_id for event in due] == ["e2", "e3", "e1"]


def test_pop_due_uses_source_as_tertiary_key() -> None:
    """`(time, priority, source, ...)`-Reihenfolge: gleicher time+priority,
    `source`-Lex entscheidet."""
    scheduler = Scheduler()
    scheduler.add(_make_event("e1", source="bravo"))
    scheduler.add(_make_event("e2", source="alpha"))
    scheduler.add(_make_event("e3", source="charlie"))
    due = scheduler.pop_due(100)
    assert [event.event_id for event in due] == ["e2", "e1", "e3"]


def test_pop_due_uses_sequence_then_event_id_as_final_keys() -> None:
    scheduler = Scheduler()
    scheduler.add(_make_event("e_b", sequence=1))
    scheduler.add(_make_event("e_a", sequence=1))
    scheduler.add(_make_event("e_x", sequence=0))
    due = scheduler.pop_due(100)
    # sequence=0 zuerst, dann sequence=1 mit event_id "e_a" vor "e_b".
    assert [event.event_id for event in due] == ["e_x", "e_a", "e_b"]


def test_pop_due_with_strict_time_window_keeps_future_events() -> None:
    """Nur Events mit `event_time <= time` werden gepoppt; spaetere
    bleiben in der Queue."""
    scheduler = Scheduler()
    scheduler.add(_make_event("e1", simulation_time=50))
    scheduler.add(_make_event("e2", simulation_time=150))
    due = scheduler.pop_due(100)
    assert [event.event_id for event in due] == ["e1"]
    assert len(scheduler) == 1
    rest = scheduler.pop_due(200)
    assert [event.event_id for event in rest] == ["e2"]


def test_pop_due_returns_empty_when_no_events_are_due() -> None:
    scheduler = Scheduler()
    scheduler.add(_make_event("e1", simulation_time=500))
    assert scheduler.pop_due(100) == []
    assert len(scheduler) == 1


# ---------------------------------------------------------------------------
# Hypothesis-Property: Permutation der Eingabe ist irrelevant
# ---------------------------------------------------------------------------

_safe_text_short = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    min_size=1,
    max_size=8,
)


@st.composite
def _event_list(draw: st.DrawFn) -> list[Event]:
    """Erzeugt eine Liste von 1..8 Events mit garantiert eindeutigen
    `event_id`s; die anderen Felder duerfen kollidieren, damit das
    Tie-Breaking durch alle 5 Komponenten getestet wird."""
    event_count = draw(st.integers(min_value=1, max_value=8))
    event_ids = draw(
        st.lists(_safe_text_short, min_size=event_count, max_size=event_count, unique=True)
    )
    events: list[Event] = []
    for event_id in event_ids:
        events.append(
            _make_event(
                event_id,
                simulation_time=draw(st.integers(min_value=0, max_value=10)),
                priority=draw(st.integers(min_value=-3, max_value=3)),
                source=draw(st.sampled_from(["alpha", "bravo", "charlie"])),
                sequence=draw(st.integers(min_value=0, max_value=5)),
            )
        )
    return events


@given(events=_event_list())
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
def test_permutation_of_inputs_yields_identical_pop_order(events: list[Event]) -> None:
    """Zwei Scheduler mit identischen Events in unterschiedlicher
    Eingabe-Reihenfolge liefern die gleiche Pop-Reihenfolge
    (GG-ARCH-006 Tie-Breaking-Stabilitaet)."""
    scheduler_a = Scheduler()
    for event in events:
        scheduler_a.add(event)
    order_a = [event.event_id for event in scheduler_a.pop_due(10**9)]

    rng = random.Random(42)
    shuffled = events.copy()
    rng.shuffle(shuffled)
    scheduler_b = Scheduler()
    for event in shuffled:
        scheduler_b.add(event)
    order_b = [event.event_id for event in scheduler_b.pop_due(10**9)]

    assert order_a == order_b


def test_five_events_same_time_permutation_smoke() -> None:
    """Slice-Plan-Smoke: 5 Events mit identischem `simulation_time`,
    in randomisierter Eingabereihenfolge → identische Ausgabe."""
    base = [
        _make_event("evt_1", simulation_time=100, priority=0, source="a", sequence=0),
        _make_event("evt_2", simulation_time=100, priority=0, source="a", sequence=1),
        _make_event("evt_3", simulation_time=100, priority=0, source="b", sequence=0),
        _make_event("evt_4", simulation_time=100, priority=1, source="a", sequence=0),
        _make_event("evt_5", simulation_time=100, priority=-1, source="a", sequence=0),
    ]
    expected = [
        event.event_id
        for event in sorted(
            base,
            key=lambda e: (e.simulation_time, e.priority, e.source, e.sequence, e.event_id),
        )
    ]
    rng = random.Random(7)
    for _ in range(10):
        permutation = base.copy()
        rng.shuffle(permutation)
        scheduler = Scheduler()
        for event in permutation:
            scheduler.add(event)
        assert [event.event_id for event in scheduler.pop_due(100)] == expected


# ---------------------------------------------------------------------------
# Duplicate-event_id-Schutz
# ---------------------------------------------------------------------------


def test_add_rejects_duplicate_event_id_typed() -> None:
    scheduler = Scheduler()
    scheduler.add(_make_event("dup"))
    with pytest.raises(SchedulerDuplicateEventIdError):
        scheduler.add(_make_event("dup", simulation_time=500))


# ---------------------------------------------------------------------------
# Snapshot / from_snapshot
# ---------------------------------------------------------------------------


def test_snapshot_emits_version_and_pending_events_in_pop_order() -> None:
    scheduler = Scheduler()
    scheduler.add(_make_event("e1", simulation_time=200))
    scheduler.add(_make_event("e2", simulation_time=100))
    snapshot = scheduler.snapshot()
    assert snapshot["version"] == 1
    pending = snapshot["pending_events"]
    assert isinstance(pending, list)
    # pop-order: e2 (t=100) zuerst.
    assert [entry["event_id"] for entry in pending] == ["e2", "e1"]


def test_from_snapshot_roundtrip_preserves_pop_order() -> None:
    scheduler = Scheduler()
    for event_id, sim_time in [("e1", 200), ("e2", 100), ("e3", 150)]:
        scheduler.add(_make_event(event_id, simulation_time=sim_time))
    snapshot = scheduler.snapshot()
    restored = Scheduler.from_snapshot(snapshot)
    assert [event.event_id for event in restored.pop_due(1000)] == ["e2", "e3", "e1"]


def test_from_snapshot_preserves_payload_with_decimal() -> None:
    """Event-payload mit `Decimal` ueberlebt den Snapshot-Roundtrip
    (Welle 3 bleibt auf Mapping-Ebene; canonical_json-Bytes-Layer
    kommt in Welle 4)."""
    event = Event(
        event_id="e1",
        simulation_time=100,
        source="bess",
        target="grid",
        type="dispatch",
        payload={"setpoint_kw": Decimal("1.500000")},
        priority=0,
        sequence=0,
    )
    scheduler = Scheduler()
    scheduler.add(event)
    snapshot = scheduler.snapshot()
    restored = Scheduler.from_snapshot(snapshot)
    popped = restored.pop_due(1000)
    assert popped[0].payload == {"setpoint_kw": Decimal("1.500000")}


# ---------------------------------------------------------------------------
# Snapshot-Format-Negativ-Pfade (typisiert)
# ---------------------------------------------------------------------------


def test_from_snapshot_rejects_missing_keys() -> None:
    with pytest.raises(SchedulerSnapshotMissingKeysError):
        Scheduler.from_snapshot({"version": 1})


def test_from_snapshot_rejects_wrong_version_type() -> None:
    with pytest.raises(SchedulerSnapshotWrongTypeError):
        Scheduler.from_snapshot({"version": "1", "pending_events": []})


def test_from_snapshot_rejects_bool_version() -> None:
    """`bool` ist `int`-Subklasse — Schema-Versionen sind aber
    Ganzzahlen."""
    with pytest.raises(SchedulerSnapshotWrongTypeError):
        Scheduler.from_snapshot({"version": True, "pending_events": []})


def test_from_snapshot_rejects_non_list_pending_events() -> None:
    with pytest.raises(SchedulerSnapshotWrongTypeError):
        Scheduler.from_snapshot({"version": 1, "pending_events": "not-a-list"})


def test_from_snapshot_rejects_unknown_version() -> None:
    with pytest.raises(SchedulerSnapshotVersionError):
        Scheduler.from_snapshot({"version": 99, "pending_events": []})


def test_from_snapshot_rejects_non_dict_event_entry() -> None:
    with pytest.raises(SchedulerSnapshotEventFieldError):
        Scheduler.from_snapshot({"version": 1, "pending_events": ["not-a-dict"]})


def test_from_snapshot_rejects_event_with_missing_field() -> None:
    payload = {
        "version": 1,
        "pending_events": [
            {
                "event_id": "e1",
                "simulation_time": 0,
                "source": "src",
                "target": "tgt",
                "type": "tick",
                "priority": 0,
                "sequence": 0,
                # `payload` fehlt
            }
        ],
    }
    with pytest.raises(SchedulerSnapshotEventFieldError):
        Scheduler.from_snapshot(payload)


def test_from_snapshot_rejects_event_with_wrong_field_type() -> None:
    payload = {
        "version": 1,
        "pending_events": [
            {
                "event_id": "e1",
                "simulation_time": "not-an-int",
                "source": "src",
                "target": "tgt",
                "type": "tick",
                "payload": {},
                "priority": 0,
                "sequence": 0,
            }
        ],
    }
    with pytest.raises(SchedulerSnapshotEventFieldError):
        Scheduler.from_snapshot(payload)


def test_from_snapshot_rejects_event_with_bool_int_field() -> None:
    """bool wird in int-Feldern explizit abgelehnt (analog Welle 2)."""
    payload = {
        "version": 1,
        "pending_events": [
            {
                "event_id": "e1",
                "simulation_time": True,
                "source": "src",
                "target": "tgt",
                "type": "tick",
                "payload": {},
                "priority": 0,
                "sequence": 0,
            }
        ],
    }
    with pytest.raises(SchedulerSnapshotEventFieldError):
        Scheduler.from_snapshot(payload)
