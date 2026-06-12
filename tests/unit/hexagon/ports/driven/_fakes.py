"""Test-Doubles fuer die Driven-Ports (M1 Welle 2/6b).

`FakeClock` ist die einzige `ClockPort`-Implementation, die Welle 2
fuer Tests bereitstellt — eine produktive `SimulationClock` wird in
Welle 4 mit dem TickLoop gebaut.

`MersenneTwisterRandomPort` ist gleichzeitig die produktive
`RandomPort`-Implementation und das, was im ADR-0007-Akzeptanztext
als „FixedSeedRandom"-Test-Helper bezeichnet wird. Wir re-exportieren
ihn unter dem ADR-Namen, damit Tests dem Akzeptanztext folgen
koennen, ohne dass es zwei Klassen mit gleichem Verhalten gibt.

`InMemoryRunRepository` ist der Welle-6b-Test-Helper fuer den
`RunRepositoryPort`. Welle 6c liefert die produktive
`PostgresRunRepository`-Implementation; bis dahin reicht der
In-Memory-Fake fuer Unit-Tests + FastAPI-Wiring.

`RecordedSpan`/`RecordingTracePort` sind das geteilte
`TracePort`-Test-Double der Protocol-Wrapper-Tests
(M7-Welle-3b-C2-Review-Folge F3: vorher 1:1-Kopien in
`test_protocol_otel_wrap.py` + `test_protocol_comm_failure_
wrap.py`; Dedup-Praezedenz 3a-F3).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.run import RunMetadata, RunStatus
from grid_gym.hexagon.core.errors import (
    RunAlreadyExistsError,
    RunNotFoundError,
)
from grid_gym.hexagon.ports.driven.clock import SimulationTime
from grid_gym.hexagon.ports.driven.observability import SpanContext


@dataclass(slots=True)
class FakeClock:
    """`ClockPort`-Implementation, die durch `advance()` getrieben wird.

    Bewusst veraenderlich (`frozen=False`): `advance()` mutiert den
    internen Zaehler. AC-DOMAIN-FROZEN gilt nicht — Tests liegen
    nicht unter `hexagon/core/domain/`.
    """

    _now: SimulationTime = 0

    def now(self) -> SimulationTime:
        return self._now

    def advance(self, delta_ms: int) -> None:
        if delta_ms <= 0:
            raise ValueError(f"delta_ms must be positive, got {delta_ms}")
        self._now += delta_ms


@dataclass
class RecordedSpan:
    """Aufgezeichneter Span fuer Test-Assertions."""

    name: str
    attributes: dict[str, object]
    events: list[tuple[str, dict[str, object]]] = field(default_factory=list)
    ended: bool = False


class RecordingTracePort:
    """`TracePort`-Test-Double, das alle Span-Open/Event/Close-
    Calls aufzeichnet und in einer Liste exposes (geteilt von
    den Protocol-Wrapper-Tests; Review-Folge 3b-F3)."""

    def __init__(self) -> None:
        self.spans: list[RecordedSpan] = []
        # context → span-index mapping
        self._index: dict[SpanContext, int] = {}

    def start_span(
        self,
        name: str,
        *,
        parent: SpanContext | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> SpanContext:
        recorded = RecordedSpan(name=name, attributes=dict(attributes or {}))
        idx = len(self.spans)
        self.spans.append(recorded)
        context = SpanContext(
            trace_id=f"trace-{idx}",
            span_id=f"span-{idx}",
            parent_span_id=None,
        )
        self._index[context] = idx
        return context

    def end_span(self, context: SpanContext) -> None:
        idx = self._index.get(context)
        if idx is None:
            return
        self.spans[idx].ended = True

    def record_event(
        self,
        context: SpanContext,
        name: str,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        idx = self._index.get(context)
        if idx is None:
            return
        self.spans[idx].events.append((name, dict(attributes or {})))


FixedSeedRandom = MersenneTwisterRandomPort
"""ADR-0007-§4a-AC2-Alias fuer den produktiven RandomPort.

Tests konstruieren `FixedSeedRandom(seed=...)`, die Implementierung
ist `MersenneTwisterRandomPort`. Verhindert eine zweite Test-Variante
mit divergentem Verhalten.
"""


class InMemoryRunRepository:
    """`RunRepositoryPort`-Test-Double mit dict-basiertem Store.

    Welle 6b: liefert das Wiring fuer FastAPI-Tests, ohne dass eine
    Datenbank laufen muss. Welle 6c bringt `PostgresRunRepository`
    als produktive Implementation; bestehende Tests gegen
    `RunRepositoryPort` koennen dann gegen beide Implementationen
    laufen (testcontainers fuer Postgres).

    Welle-4a-Extension (ADR 0039 Decision 12): zweiter Dict
    `_status_store` haelt den `RunStatus`-Lifecycle-State neben den
    Metadaten. `save` initialisiert auf ``"pending"``;
    `update_status`/`get_status` mutieren bzw. lesen den State.

    `frozen=False`/keine Dataclass: explizit zustandsbehaftet,
    interne `_store`-Mutation. AC-DOMAIN-FROZEN gilt nicht (Test-
    Code unter `tests/`).
    """

    def __init__(self) -> None:
        self._store: dict[str, RunMetadata] = {}
        self._status_store: dict[str, RunStatus] = {}

    def save(self, metadata: RunMetadata) -> None:
        if metadata.run_id in self._store:
            raise RunAlreadyExistsError(metadata.run_id)
        self._store[metadata.run_id] = metadata
        self._status_store[metadata.run_id] = "pending"

    def get_by_id(self, run_id: str) -> RunMetadata:
        if run_id not in self._store:
            raise RunNotFoundError(run_id)
        return self._store[run_id]

    def exists(self, run_id: str) -> bool:
        return run_id in self._store

    def update_status(self, run_id: str, status: RunStatus) -> None:
        if run_id not in self._store:
            raise RunNotFoundError(run_id)
        self._status_store[run_id] = status

    def get_status(self, run_id: str) -> RunStatus:
        if run_id not in self._store:
            raise RunNotFoundError(run_id)
        return self._status_store[run_id]

    def ping(self) -> bool:
        """Readiness-Probe (M6 Welle 6, `GG-DEPLOY-006`). Test-Double
        ohne externes Backend → immer ``True``. Smokes, die einen
        DB-Ausfall simulieren, ueberschreiben `ping` per Subklasse
        oder monkeypatch."""
        return True
