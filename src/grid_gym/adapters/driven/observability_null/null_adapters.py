"""Null-Adapter-Trio fuer das Observability-Port-Trio
(M3 Welle 5, ADR 0024 §2.5).

Drei Adapter unter einer Datei, weil die Implementierungen klein
sind (anders als der Mersenne-Twister-Adapter, der ein eigenes
Sub-Modul rechtfertigt):

- `NullLogAdapter(LogPort)` — frisst `log(...)`-Aufrufe stillschweigend.
- `NullMetricsAdapter(MetricsPort)` — frisst Counter/Gauge/Observe.
- `NullTraceAdapter(TracePort)` — manufakturiert deterministische
  `SpanContext`-Instanzen, frisst `end_span` und `record_event`.

Pflicht-Surface aller drei (auch im Default `record_calls=False`):

- `call_count: int` — Anzahl der ausgefuehrten Method-Aufrufe.
- `last_call: CallRecord | None` — letzter Aufruf als strukturierter
  Record (Methoden-Name + Args + Kwargs).

Opt-in-Surface bei `record_calls=True`:

- `call_records: Sequence[CallRecord]` — vollstaendige Aufruf-
  Historie, append-only.
- `clear_calls() -> None` — Reset (count → 0, last_call → None,
  call_records → []).

Loest M3-`welle-5.md §7 R-2`: Tests haben **immer** eine
strukturierte Assertion-Surface, ohne explizit `record_calls=True`
opt-in-en zu muessen.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final

from grid_gym.hexagon.ports.driven.observability import LogEntry, SpanContext

__all__ = [
    "CallRecord",
    "NullLogAdapter",
    "NullMetricsAdapter",
    "NullTraceAdapter",
]


@dataclass(frozen=True, slots=True)
class CallRecord:
    """Strukturierter Aufruf-Record (ADR 0024 §2.5).

    `method` ist der Methoden-Name (`"log"`, `"increment"`,
    `"start_span"`, …). `args` enthaelt positionale Argumente in der
    Reihenfolge der Method-Signatur; `kwargs` traegt die keyword-
    Argumente.

    `kwargs` ist `Mapping[str, object]` — Adapter speichert eine
    `dict`-Kopie der uebergebenen Kwargs (Caller-Mutation wird
    abgeschirmt).
    """

    method: str
    args: tuple[object, ...]
    kwargs: Mapping[str, object]


# Pre-defined dummy attributes-mapping so dataclass-field default
# can be a frozen-friendly factory.
_EMPTY_ATTRS: Final[Mapping[str, object]] = {}


@dataclass(slots=True)
class _CallTracker:
    """Gemeinsame `call_count`/`last_call`/`call_records`-Maschine.

    Wird von den drei Null-Adaptern intern instanziiert und ueber
    Properties exponiert. Trennt die Tracking-Mechanik von den
    Port-Signaturen, damit jede Adapter-Klasse nur ihre eigenen
    Methoden-Argumente kapseln muss.
    """

    record_calls: bool
    _call_count: int = 0
    _last_call: CallRecord | None = None
    _call_records: list[CallRecord] = field(default_factory=list)

    def track(self, method: str, args: tuple[object, ...], kwargs: Mapping[str, object]) -> None:
        record = CallRecord(method=method, args=args, kwargs=dict(kwargs))
        self._call_count += 1
        self._last_call = record
        if self.record_calls:
            self._call_records.append(record)

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def last_call(self) -> CallRecord | None:
        return self._last_call

    @property
    def call_records(self) -> Sequence[CallRecord]:
        # Tuple-Snapshot statt direkter List-Referenz — Aufrufer
        # koennen den Adapter-internen Buffer nicht versehentlich
        # mutieren.
        return tuple(self._call_records)

    def clear(self) -> None:
        self._call_count = 0
        self._last_call = None
        self._call_records = []


class NullLogAdapter:
    """Null-Adapter fuer `LogPort` (ADR 0024 §2.5).

    Frisst alle `log(...)`-Aufrufe ohne Sichtbarkeit. Test-Sichtbarkeit
    ueber die `call_count`/`last_call`/`call_records`-Properties.
    """

    def __init__(self, *, record_calls: bool = False) -> None:
        self._tracker = _CallTracker(record_calls=record_calls)

    def log(self, entry: LogEntry) -> None:
        kwargs: dict[str, object] = {
            "level": entry.level,
            "message": entry.message,
            "run_id": entry.run_id,
            "module": entry.module,
            "event_id": entry.event_id,
            "attributes": dict(entry.attributes) if entry.attributes is not None else None,
        }
        self._tracker.track("log", (), kwargs)

    @property
    def call_count(self) -> int:
        return self._tracker.call_count

    @property
    def last_call(self) -> CallRecord | None:
        return self._tracker.last_call

    @property
    def call_records(self) -> Sequence[CallRecord]:
        return self._tracker.call_records

    def clear_calls(self) -> None:
        self._tracker.clear()


class NullMetricsAdapter:
    """Null-Adapter fuer `MetricsPort` (ADR 0024 §2.5).

    Frisst `increment`/`gauge`/`observe`-Aufrufe; Test-Surface
    identisch zu `NullLogAdapter`.
    """

    def __init__(self, *, record_calls: bool = False) -> None:
        self._tracker = _CallTracker(record_calls=record_calls)

    def increment(
        self,
        name: str,
        value: int = 1,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        self._tracker.track(
            "increment",
            (),
            {
                "name": name,
                "value": value,
                "attributes": dict(attributes) if attributes is not None else None,
            },
        )

    def gauge(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        self._tracker.track(
            "gauge",
            (),
            {
                "name": name,
                "value": value,
                "attributes": dict(attributes) if attributes is not None else None,
            },
        )

    def observe(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        self._tracker.track(
            "observe",
            (),
            {
                "name": name,
                "value": value,
                "attributes": dict(attributes) if attributes is not None else None,
            },
        )

    @property
    def call_count(self) -> int:
        return self._tracker.call_count

    @property
    def last_call(self) -> CallRecord | None:
        return self._tracker.last_call

    @property
    def call_records(self) -> Sequence[CallRecord]:
        return self._tracker.call_records

    def clear_calls(self) -> None:
        self._tracker.clear()


class NullTraceAdapter:
    """Null-Adapter fuer `TracePort` (ADR 0024 §2.5).

    Manufakturiert deterministische `SpanContext`-Instanzen
    (`trace_id=f"null-trace-{n}"`, `span_id=f"null-span-{n}"`) pro
    `start_span`-Aufruf; n ist ein Adapter-interner Counter, der pro
    Adapter-Instanz bei 1 startet. Damit koennen nachgelagerte
    `end_span` / `record_event`-Aufrufe einen gueltigen Kontext
    fuehren.

    `end_span` und `record_event` akzeptieren `SpanContext` per
    Signatur — der **`None`-No-Op-Fallback** aus ADR 0024 §2.4 ist
    Adapter-Robustheit fuer defensive Aufrufer, die `end_span(None)`
    rufen, wenn der vorgelagerte `start_span` geskippt wurde. Der
    Null-Adapter respektiert das ohne Exception.
    """

    def __init__(self, *, record_calls: bool = False) -> None:
        self._tracker = _CallTracker(record_calls=record_calls)
        self._span_counter = 0

    def start_span(
        self,
        name: str,
        *,
        parent: SpanContext | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> SpanContext:
        self._span_counter += 1
        context = SpanContext(
            trace_id=f"null-trace-{self._span_counter}",
            span_id=f"null-span-{self._span_counter}",
            parent_span_id=parent.span_id if parent is not None else None,
        )
        self._tracker.track(
            "start_span",
            (),
            {
                "name": name,
                "parent": parent,
                "attributes": dict(attributes) if attributes is not None else None,
                "returned": context,
            },
        )
        return context

    def end_span(self, context: SpanContext | None) -> None:
        # ADR 0024 §2.4: `None`-Fallback ist erlaubtes Adapter-No-Op.
        # Type-Signatur deklariert `SpanContext`, der Adapter
        # absorbiert `None` defensiv ohne Exception.
        self._tracker.track("end_span", (), {"context": context})

    def record_event(
        self,
        context: SpanContext | None,
        name: str,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        # Selbe `None`-Adapter-Robustheit wie `end_span`.
        self._tracker.track(
            "record_event",
            (),
            {
                "context": context,
                "name": name,
                "attributes": dict(attributes) if attributes is not None else None,
            },
        )

    @property
    def call_count(self) -> int:
        return self._tracker.call_count

    @property
    def last_call(self) -> CallRecord | None:
        return self._tracker.last_call

    @property
    def call_records(self) -> Sequence[CallRecord]:
        return self._tracker.call_records

    def clear_calls(self) -> None:
        self._tracker.clear()
        self._span_counter = 0
