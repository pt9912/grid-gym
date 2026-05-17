"""TickLoop — die invariante Simulations-Spine (M1 Welle 4).

Der `TickLoop` verbindet `ClockPort`, `RandomPort` und `Scheduler` zu
einem deterministischen Tick-zu-Tick-Pfad (`GG-SIM-001`/`002`,
`GG-ARCH-008`). Welle 4 liefert den Kern ohne Geraete: pro `tick()`
schiebt der Loop die Sim-Zeit um `tick_ms` vorwaerts und liefert die
faelligen Events aus dem Scheduler in stabiler Reihenfolge.
Geraetemodelle in M2+ fuellen das `emitted_telemetry`-Feld in
`TickResult`.

Snapshot-Vertrag:
- `TickLoop.snapshot()` liefert ein `Mapping[str, object]` im
  `SnapshotEnvelope`-konformen Format (`hexagon.core.domain.snapshot`):
  `version`, `run_id`, `simulation_time`, `tick_count`, `tick_ms`,
  plus `sub_snapshots = {"scheduler": ..., "random_root": ...}`.
  `RandomPort.snapshot_as_mapping()` (`ADR 0010`) liefert dabei
  das random-sub-snapshot-Mapping direkt — keine Encoder-Logik in
  der Domain.
- `TickLoop.from_snapshot(state, *, clock, random)` rekonstruiert
  den Loop. Aufrufer injiziert `clock` und `random` als bereits
  restored Instanzen. Konsistenz wird typisiert geprueft:
  `clock.now() == state['simulation_time']` und
  `random.snapshot_as_mapping() == state['sub_snapshots']
  ['random_root']`. Mismatches fallen mit
  `TickLoopSnapshotClockMismatchError` bzw.
  `TickLoopSnapshotRandomMismatchError` auf.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.errors import (
    TickLoopSnapshotClockMismatchError,
    TickLoopSnapshotMissingKeysError,
    TickLoopSnapshotRandomMismatchError,
    TickLoopSnapshotVersionError,
    TickLoopSnapshotWrongTypeError,
)
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.ports.driven.clock import ClockPort
from grid_gym.hexagon.ports.driven.random import RandomPort

_SNAPSHOT_VERSION: Final[int] = 1
"""Schema-Version des TickLoop-Snapshots. Erhoehung -> Folge-ADR."""

_REQUIRED_KEYS: Final[frozenset[str]] = frozenset(
    {"version", "run_id", "simulation_time", "tick_count", "tick_ms", "sub_snapshots"}
)

_REQUIRED_SUB_SNAPSHOT_KEYS: Final[frozenset[str]] = frozenset({"scheduler", "random_root"})


class TickLoop:
    """Deterministischer Tick-Loop (`GG-SIM-001`/`002`).

    `tick_ms` ist die Schrittweite je `tick()`-Aufruf (10/100/1000
    per `GG-SIM-002`); `run_id` ist die stabile Lauf-Identitaet
    (`GG-DATA-001`); `tick_count` ist 0-basiert und zaehlt die
    bereits abgeschlossenen Ticks.
    """

    def __init__(
        self,
        *,
        run_id: str,
        tick_ms: int,
        clock: ClockPort,
        random: RandomPort,
        scheduler: Scheduler,
    ) -> None:
        self._run_id: str = run_id
        self._tick_ms: int = tick_ms
        self._clock: ClockPort = clock
        self._random: RandomPort = random
        self._scheduler: Scheduler = scheduler
        self._tick_count: int = 0

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def tick_ms(self) -> int:
        return self._tick_ms

    @property
    def tick_count(self) -> int:
        """Anzahl bereits abgeschlossener Ticks (0 vor dem ersten
        `tick()`-Aufruf)."""
        return self._tick_count

    def tick(self) -> TickResult:
        """Schiebt die Simulationszeit um `tick_ms` vor und liefert
        die faelligen Events in stabiler Reihenfolge.

        Welle-4-Scope (`GG-SIM-001`): Geraetemodelle existieren noch
        nicht; `emitted_telemetry` ist leer. M2+ erweitert die
        Methode um Geraete-`tick`-Aufrufe und Telemetry-Sammlung
        vor dem Commit.
        """
        self._clock.advance(self._tick_ms)
        now = self._clock.now()
        popped = tuple(self._scheduler.pop_due(now))
        result = TickResult(
            tick=self._tick_count,
            simulation_time=now,
            popped_events=popped,
            emitted_telemetry=(),
        )
        self._tick_count += 1
        return result

    def snapshot(self) -> Mapping[str, object]:
        """Liefert den TickLoop-State als `SnapshotEnvelope`-konformes
        Mapping (`GG-SIM-005`).

        `random_root` wird per `RandomPort.snapshot_as_mapping()`
        (`ADR 0010`) als Mapping eingebunden — keine Encoder-Logik
        in der Domain.
        """
        return {
            "version": _SNAPSHOT_VERSION,
            "run_id": self._run_id,
            "simulation_time": self._clock.now(),
            "tick_count": self._tick_count,
            "tick_ms": self._tick_ms,
            "sub_snapshots": {
                "scheduler": self._scheduler.snapshot(),
                "random_root": self._random.snapshot_as_mapping(),
            },
        }

    @classmethod
    def from_snapshot(
        cls,
        state: Mapping[str, object],
        *,
        clock: ClockPort,
        random: RandomPort,
    ) -> TickLoop:
        """Stellt einen `TickLoop` aus einem Snapshot wieder her.

        Aufrufer injiziert `clock` und `random` als bereits restored
        Instanzen (z. B. via `MersenneTwisterRandomPort.from_snapshot`
        und einer Clock, die per `advance` auf
        `state['simulation_time']` gebracht wurde).

        Konsistenz-Pruefungen:
        - `clock.now() == state['simulation_time']` →
          `TickLoopSnapshotClockMismatchError`.
        - `random.snapshot_as_mapping() == state['sub_snapshots']
          ['random_root']` → `TickLoopSnapshotRandomMismatchError`.

        Der `Scheduler` wird intern aus
        `state['sub_snapshots']['scheduler']` rekonstruiert.
        """
        parsed = _validate_tick_loop_snapshot(state)
        if parsed.version != _SNAPSHOT_VERSION:
            raise TickLoopSnapshotVersionError(_SNAPSHOT_VERSION, parsed.version)
        if clock.now() != parsed.simulation_time:
            raise TickLoopSnapshotClockMismatchError(parsed.simulation_time, clock.now())
        if random.snapshot_as_mapping() != parsed.random_root:
            raise TickLoopSnapshotRandomMismatchError
        scheduler = Scheduler.from_snapshot(parsed.scheduler)
        loop = cls(
            run_id=parsed.run_id,
            tick_ms=parsed.tick_ms,
            clock=clock,
            random=random,
            scheduler=scheduler,
        )
        loop._tick_count = parsed.tick_count
        return loop


# ---------------------------------------------------------------------------
# Snapshot-Validierung (Pattern parallel zu Welle 2/3 — Trigger 012
# generalisiert das in Welle 5+).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _ParsedTickLoopSnapshot:
    """Geprueftes Snapshot-Payload mit allen Pflicht-Keys typisiert.

    Liegt ausserhalb `domain/` — AC-DOMAIN-FROZEN gilt hier nicht;
    `frozen=True, slots=True` ist rein pragmatisch (Schreibschutz
    nach Validierung).
    """

    version: int
    run_id: str
    simulation_time: int
    tick_count: int
    tick_ms: int
    scheduler: Mapping[str, object]
    random_root: Mapping[str, object]


def _validate_tick_loop_snapshot(state: Mapping[str, object]) -> _ParsedTickLoopSnapshot:
    """Prueft Top-Level-Keys/-Typen und Sub-Snapshot-Konvention."""
    missing = _REQUIRED_KEYS - state.keys()
    if missing:
        raise TickLoopSnapshotMissingKeysError(sorted(missing))
    version = _require_int(state, "version")
    run_id = _require_str(state, "run_id")
    simulation_time = _require_int(state, "simulation_time")
    tick_count = _require_int(state, "tick_count")
    tick_ms = _require_int(state, "tick_ms")
    sub_snapshots = state["sub_snapshots"]
    if not isinstance(sub_snapshots, Mapping):
        raise TickLoopSnapshotWrongTypeError(
            "sub_snapshots", "Mapping", type(sub_snapshots).__name__
        )
    missing_subs = _REQUIRED_SUB_SNAPSHOT_KEYS - sub_snapshots.keys()
    if missing_subs:
        raise TickLoopSnapshotMissingKeysError(
            [f"sub_snapshots.{name}" for name in sorted(missing_subs)]
        )
    scheduler_state = _require_sub_mapping(sub_snapshots, "scheduler")
    random_state = _require_sub_mapping(sub_snapshots, "random_root")
    return _ParsedTickLoopSnapshot(
        version=version,
        run_id=run_id,
        simulation_time=simulation_time,
        tick_count=tick_count,
        tick_ms=tick_ms,
        scheduler=scheduler_state,
        random_root=random_state,
    )


def _require_int(state: Mapping[str, object], key: str) -> int:
    value = state[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TickLoopSnapshotWrongTypeError(key, "int", type(value).__name__)
    return value


def _require_str(state: Mapping[str, object], key: str) -> str:
    value = state[key]
    if not isinstance(value, str):
        raise TickLoopSnapshotWrongTypeError(key, "str", type(value).__name__)
    return value


def _require_sub_mapping(sub_snapshots: Mapping[str, object], name: str) -> Mapping[str, object]:
    value = sub_snapshots[name]
    if not isinstance(value, Mapping):
        raise TickLoopSnapshotWrongTypeError(
            f"sub_snapshots.{name}", "Mapping", type(value).__name__
        )
    return value
