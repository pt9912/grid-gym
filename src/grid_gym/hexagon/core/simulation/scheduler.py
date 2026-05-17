"""Deterministischer Event-Scheduler (`GG-ARCH-005` / `GG-ARCH-006`).

`Scheduler` haelt die globale Event-Queue eines Simulationslaufs und
liefert beim Tick die faelligen Events in stabiler Reihenfolge zurueck.
Tie-Breaking-Tupel `(simulation_time, priority, source, sequence,
event_id)` per `GG-ARCH-006`.

Implementiert mit `heapq` (Min-Heap ueber den Sort-Key-Tupel). Events
selbst landen in einem `dict[event_id, Event]` neben dem Heap; die
Queue traegt nur die Sort-Keys, sodass `heapq` niemals Events direkt
vergleicht (Events sind nicht ordbar — `Event` ist Frozen-Dataclass
ohne `__lt__`).

Snapshot-Vertrag (Welle 3):
- `Scheduler.snapshot()` liefert ein `Mapping[str, object]` mit
  `version: int` (M1-Welle-1-Konvention aus `SnapshotEnvelope`) und
  `pending_events: list[dict]`. Die Events sind in Pop-Reihenfolge
  sortiert (deterministisch).
- `Scheduler.from_snapshot(state)` rekonstruiert den Scheduler aus
  einem solchen Mapping. Typisierte Format-Errors aus
  `core.errors.SchedulerSnapshotFormatError`-Hierarchie.

TODO(M1-Welle-4): Composition mit `RandomPort.snapshot()` (das
`bytes` liefert) im `SnapshotEnvelope` vereinheitlichen — heute
inkonsistente Snapshot-Rueckgabetypen zwischen Adapter
(`bytes`-canonical) und Domain-Scheduler (`Mapping`). Welle 4 oder
eine Folge-ADR klaert die Composition.
"""

from __future__ import annotations

import heapq
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Final

from grid_gym.hexagon.core.domain.event import Event
from grid_gym.hexagon.core.errors import (
    SchedulerDuplicateEventIdError,
    SchedulerSnapshotEventFieldError,
    SchedulerSnapshotMissingKeysError,
    SchedulerSnapshotVersionError,
    SchedulerSnapshotWrongTypeError,
)

_SNAPSHOT_VERSION: Final[int] = 1
"""Schema-Version des Scheduler-Snapshots.

Eine Erhoehung erfordert eine Folge-ADR analog zu `ADR 0009`.
"""

# Tie-Breaking-Tupel-Typ: (time, priority, source, sequence, event_id).
type _SortKey = tuple[int, int, str, int, str]


@dataclass(frozen=True, slots=True)
class _ParsedSchedulerSnapshot:
    """Geprueftes Snapshot-Payload mit allen Pflicht-Keys typisiert.

    Liegt im Scheduler-Modul, nicht in `domain/` — AC-DOMAIN-FROZEN
    gilt nur dort; `frozen=True, slots=True` hier rein pragmatisch.
    """

    version: int
    pending_events: list[Event]


class Scheduler:
    """Deterministischer Event-Scheduler (`GG-ARCH-005`/`GG-ARCH-006`).

    Heap-basierter Min-Scheduler ueber dem Tie-Breaking-Tupel
    `(simulation_time, priority, source, sequence, event_id)`.
    `event_id` ist garantiert eindeutig — `add` lehnt Duplikate
    typisiert ab, damit Sort-Keys nie kollidieren.
    """

    def __init__(self) -> None:
        self._queue: list[_SortKey] = []
        self._events_by_id: dict[str, Event] = {}

    def __len__(self) -> int:
        return len(self._queue)

    def __bool__(self) -> bool:
        """`bool(scheduler)` ist `True`, solange Events anstehen."""
        return bool(self._queue)

    def add(self, event: Event) -> None:
        """Fuegt `event` in die Queue ein.

        Wirft `SchedulerDuplicateEventIdError`, wenn die `event_id`
        bereits in der Queue ist — Sort-Key-Eindeutigkeit ist
        Voraussetzung fuer stabiles Tie-Breaking.
        """
        if event.event_id in self._events_by_id:
            raise SchedulerDuplicateEventIdError(event.event_id)
        sort_key: _SortKey = (
            event.simulation_time,
            event.priority,
            event.source,
            event.sequence,
            event.event_id,
        )
        heapq.heappush(self._queue, sort_key)
        self._events_by_id[event.event_id] = event

    def pop_due(self, time: int) -> list[Event]:
        """Liefert alle Events mit `simulation_time <= time` in stabiler
        Sortier-Reihenfolge.

        Mutiert die Queue (gepopte Events werden entfernt). Wiederholte
        Aufrufe mit gleichem `time` liefern eine leere Liste, sobald
        alle faelligen Events einmal abgeholt sind.
        """
        due: list[Event] = []
        while self._queue and self._queue[0][0] <= time:
            sort_key = heapq.heappop(self._queue)
            event_id = sort_key[4]
            due.append(self._events_by_id.pop(event_id))
        return due

    def snapshot(self) -> Mapping[str, object]:
        """Serialisiert den Queue-State als `canonical_json`-faehiges
        Mapping.

        Pending-Events werden in Pop-Reihenfolge (sortiert nach
        Sort-Key) als Liste von Dicts ausgegeben; das ist
        deterministisch ueber Heap-Implementation-Details.
        """
        pending_in_pop_order = [self._events_by_id[sort_key[4]] for sort_key in sorted(self._queue)]
        return {
            "version": _SNAPSHOT_VERSION,
            "pending_events": [asdict(event) for event in pending_in_pop_order],
        }

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Scheduler:
        """Stellt einen Scheduler aus einem `snapshot()`-Mapping wieder her.

        Wirft Subklassen von `SchedulerSnapshotFormatError` bei
        strukturell kaputtem Snapshot und `SchedulerSnapshotVersionError`
        bei unbekannter `version`. Aufrufer (Welle 4) nutzen das beim
        Resume eines persistierten Laufs.
        """
        parsed = _validate_snapshot(state)
        if parsed.version != _SNAPSHOT_VERSION:
            raise SchedulerSnapshotVersionError(_SNAPSHOT_VERSION, parsed.version)
        scheduler = cls()
        for event in parsed.pending_events:
            scheduler.add(event)
        return scheduler


_REQUIRED_KEYS: Final[frozenset[str]] = frozenset({"version", "pending_events"})

_EVENT_FIELDS_TYPED: Final[tuple[tuple[str, type], ...]] = (
    ("event_id", str),
    ("simulation_time", int),
    ("source", str),
    ("target", str),
    ("type", str),
    ("priority", int),
    ("sequence", int),
)
"""Skalar-Felder eines `Event`-Dicts mit erwartetem Python-Typ.

`payload` (`Mapping[str, object]`) wird separat geprueft, weil sein
Wertebereich nicht statisch typisierbar ist.
"""


def _validate_snapshot(state: Mapping[str, object]) -> _ParsedSchedulerSnapshot:
    """Prueft Pflicht-Keys, Typen und Event-Dicts. Wirft typisierte
    `SchedulerSnapshotFormatError`-Subklassen."""
    missing = _REQUIRED_KEYS - state.keys()
    if missing:
        raise SchedulerSnapshotMissingKeysError(sorted(missing))
    version = state["version"]
    if isinstance(version, bool) or not isinstance(version, int):
        raise SchedulerSnapshotWrongTypeError("version", "int", type(version).__name__)
    pending_raw = state["pending_events"]
    if not isinstance(pending_raw, list):
        raise SchedulerSnapshotWrongTypeError("pending_events", "list", type(pending_raw).__name__)
    pending: list[Event] = [
        _event_from_dict(index, entry) for index, entry in enumerate(pending_raw)
    ]
    return _ParsedSchedulerSnapshot(version=version, pending_events=pending)


def _event_from_dict(index: int, raw: object) -> Event:
    """Rekonstruiert ein `Event` aus einem dict-Eintrag in
    `pending_events`. Wirft `SchedulerSnapshotEventFieldError` bei
    fehlendem oder falsch typisiertem Feld (Skalar oder Payload).

    Vier-Phasen-Aufbau (Welle-3-Review N1):
    1. Dict-Form pruefen (`_assert_event_dict_shape`).
    2. Skalar-Felder typisiert pruefen
       (`_assert_scalar_fields_typed`).
    3. Payload als `Mapping[str, canonical-kompatibel]` pruefen
       (`_assert_payload_canonical`, Welle-3-Review S2 — frueher
       Stop, damit ein Float-Payload nicht erst beim
       canonical_json-Encoder in Welle 4 bricht).
    4. `Event`-Instanz konstruieren.
    """
    entry = _assert_event_dict_shape(index, raw)
    _assert_scalar_fields_typed(index, entry)
    payload = _assert_payload_canonical(index, entry)
    return Event(
        event_id=entry["event_id"],  # type: ignore[arg-type]
        simulation_time=entry["simulation_time"],  # type: ignore[arg-type]
        source=entry["source"],  # type: ignore[arg-type]
        target=entry["target"],  # type: ignore[arg-type]
        type=entry["type"],  # type: ignore[arg-type]
        payload=payload,
        priority=entry["priority"],  # type: ignore[arg-type]
        sequence=entry["sequence"],  # type: ignore[arg-type]
    )


def _assert_event_dict_shape(index: int, raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise SchedulerSnapshotEventFieldError(index, "<entry>", "dict", type(raw).__name__)
    return raw


def _assert_scalar_fields_typed(index: int, raw: dict[str, object]) -> None:
    """Prueft die Skalar-Felder eines Event-Dicts gemaess `_EVENT_FIELDS_TYPED`.

    `bool` wird fuer int-Felder explizit ausgeschlossen (bool ist
    int-Subklasse, aber Felder wie `simulation_time` sind keine
    Wahrheitswerte).
    """
    for field, expected_type in _EVENT_FIELDS_TYPED:
        if field not in raw:
            raise SchedulerSnapshotEventFieldError(index, field, expected_type.__name__, "missing")
        value = raw[field]
        if expected_type is int and isinstance(value, bool):
            raise SchedulerSnapshotEventFieldError(index, field, "int", "bool")
        if not isinstance(value, expected_type):
            raise SchedulerSnapshotEventFieldError(
                index, field, expected_type.__name__, type(value).__name__
            )


def _assert_payload_canonical(index: int, raw: dict[str, object]) -> Mapping[str, object]:
    """Prueft, dass `payload` ein `Mapping[str, ...]` mit
    canonical_json-kompatiblen Werten ist (Welle-3-Review S2).

    Erlaubte Wertebereich (Spiegel von
    `serialization/canonical.py::canonical_json`):
    `None`, `bool`, `int`, `Decimal`, `str`, `dict[str, ...]`,
    `list`, `tuple`. Verboten: `float`, `complex`, `bytes`,
    non-`str`-Dict-Keys und alles Andere.

    Wirft `SchedulerSnapshotEventFieldError` mit
    `field="payload.<pfad>"` bei Verstoss.
    """
    if "payload" not in raw:
        raise SchedulerSnapshotEventFieldError(index, "payload", "Mapping", "missing")
    payload = raw["payload"]
    if not isinstance(payload, Mapping):
        raise SchedulerSnapshotEventFieldError(index, "payload", "Mapping", type(payload).__name__)
    _walk_payload(index, "payload", payload)
    return payload


def _walk_payload(index: int, path: str, value: object) -> None:
    """Rekursiver Walk durch einen Payload-Wert; wirft bei
    canonical-inkompatiblem Wert."""
    if value is None or isinstance(value, bool | int | Decimal | str):
        # `bool` ist `int`-Subklasse — fuer Payload-Werte explizit
        # erlaubt (`canonical_json` emittiert `true`/`false`).
        return
    if isinstance(value, Mapping):
        for key, sub_value in value.items():
            if not isinstance(key, str):
                raise SchedulerSnapshotEventFieldError(
                    index, f"{path}.<key>", "str", type(key).__name__
                )
            _walk_payload(index, f"{path}.{key}", sub_value)
        return
    if isinstance(value, list | tuple):
        for sub_index, sub_value in enumerate(value):
            _walk_payload(index, f"{path}[{sub_index}]", sub_value)
        return
    raise SchedulerSnapshotEventFieldError(
        index, path, "canonical-compatible", type(value).__name__
    )
