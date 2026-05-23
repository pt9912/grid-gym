"""Tests fuer das Null-Adapter-Trio (M3 Welle 5, ADR 0024 §2.5).

Drei Adapter unter `adapters/driven/observability_null/`:

- `NullLogAdapter` — frisst `log(...)`.
- `NullMetricsAdapter` — frisst `increment`/`gauge`/`observe`.
- `NullTraceAdapter` — manufakturiert deterministische
  `SpanContext`-Instanzen, frisst `end_span`/`record_event`.

Pinnt:

- Pflicht-Surface `call_count`/`last_call` ist im Default
  `record_calls=False` verfuegbar (loest M3-`welle-5.md §7 R-2`).
- Opt-in `record_calls=True` aktiviert `call_records`-History +
  `clear_calls()`.
- `NullTraceAdapter` traegt die `parent_span_id`-Kette und
  absorbiert `None`-Kontexte (ADR 0024 §2.4 Adapter-No-Op).
- Alle drei Adapter erfuellen das jeweilige Port-Protocol
  (`isinstance`-Check per `@runtime_checkable`).
"""

from __future__ import annotations

from grid_gym.adapters.driven.observability_null import (
    CallRecord,
    NullLogAdapter,
    NullMetricsAdapter,
    NullTraceAdapter,
)
from grid_gym.hexagon.ports.driven.observability import (
    LogPort,
    MetricsPort,
    SpanContext,
    TracePort,
)


# --- Protocol-Conformance ----------------------------------------------------


def test_null_log_adapter_satisfies_log_port() -> None:
    assert isinstance(NullLogAdapter(), LogPort)


def test_null_metrics_adapter_satisfies_metrics_port() -> None:
    assert isinstance(NullMetricsAdapter(), MetricsPort)


def test_null_trace_adapter_satisfies_trace_port() -> None:
    assert isinstance(NullTraceAdapter(), TracePort)


# --- Default-Surface (record_calls=False) ------------------------------------


def test_null_log_adapter_default_tracks_call_count_and_last_call() -> None:
    adapter = NullLogAdapter()
    assert adapter.call_count == 0
    assert adapter.last_call is None
    adapter.log("info", "hello", run_id="r1", module="m", event_id="e")
    assert adapter.call_count == 1
    last = adapter.last_call
    assert last is not None
    assert last.method == "log"
    assert last.kwargs["level"] == "info"
    assert last.kwargs["message"] == "hello"
    assert last.kwargs["run_id"] == "r1"


def test_null_metrics_adapter_default_tracks_all_three_methods() -> None:
    adapter = NullMetricsAdapter()
    adapter.increment("c", 3)
    adapter.gauge("g", 1.5)
    adapter.observe("o", 2.0, attributes={"agent": "a-1"})
    assert adapter.call_count == 3
    last = adapter.last_call
    assert last is not None
    assert last.method == "observe"
    assert last.kwargs["attributes"] == {"agent": "a-1"}


def test_null_log_adapter_default_does_not_collect_full_history() -> None:
    """Default `record_calls=False`: call_records bleibt leer
    (M3-welle-5.md §2 + ADR 0024 §2.5)."""
    adapter = NullLogAdapter()
    adapter.log("info", "one")
    adapter.log("info", "two")
    assert adapter.call_count == 2
    assert tuple(adapter.call_records) == ()


# --- Opt-in `record_calls=True` ---------------------------------------------


def test_null_log_adapter_record_calls_collects_history() -> None:
    adapter = NullLogAdapter(record_calls=True)
    adapter.log("info", "one")
    adapter.log("warn", "two")
    records = list(adapter.call_records)
    assert len(records) == 2
    assert records[0].kwargs["message"] == "one"
    assert records[1].kwargs["level"] == "warn"


def test_null_metrics_adapter_clear_calls_resets_full_state() -> None:
    adapter = NullMetricsAdapter(record_calls=True)
    adapter.increment("c")
    adapter.gauge("g", 1.0)
    assert adapter.call_count == 2
    adapter.clear_calls()
    assert adapter.call_count == 0
    assert adapter.last_call is None
    assert tuple(adapter.call_records) == ()


# --- NullTraceAdapter-Spezifika ---------------------------------------------


def test_null_trace_adapter_returns_deterministic_span_context() -> None:
    """ADR 0024 §2.5: NullTraceAdapter manufakturiert deterministische
    SpanContext-IDs pro Aufruf."""
    adapter = NullTraceAdapter()
    s1 = adapter.start_span("a")
    s2 = adapter.start_span("b")
    assert isinstance(s1, SpanContext)
    assert s1.trace_id == "null-trace-1"
    assert s1.span_id == "null-span-1"
    assert s1.parent_span_id is None
    assert s2.span_id == "null-span-2"


def test_null_trace_adapter_propagates_parent_span_id() -> None:
    """ADR 0024 §2.4: nested Spans tragen die Schachtelung."""
    adapter = NullTraceAdapter()
    parent = adapter.start_span("outer")
    child = adapter.start_span("inner", parent=parent)
    assert child.parent_span_id == parent.span_id


def test_null_trace_adapter_end_span_accepts_none_per_no_op_fallback() -> None:
    """ADR 0024 §2.4: `None`-Kontext ist erlaubtes Adapter-No-Op."""
    adapter = NullTraceAdapter()
    adapter.end_span(None)  # should NOT raise
    # Aufruf wird trotzdem getrackt (Test-Sichtbarkeit).
    assert adapter.call_count == 1
    last = adapter.last_call
    assert last is not None
    assert last.method == "end_span"
    assert last.kwargs["context"] is None


def test_null_trace_adapter_record_event_accepts_none_per_no_op_fallback() -> None:
    adapter = NullTraceAdapter()
    adapter.record_event(None, "ev")  # should NOT raise
    assert adapter.call_count == 1


def test_null_trace_adapter_clear_calls_resets_span_counter() -> None:
    """`clear_calls()` resettet auch den span_counter, damit
    nachfolgende `start_span`-Aufrufe wieder bei `null-trace-1`
    beginnen (Test-Wiederholbarkeit)."""
    adapter = NullTraceAdapter()
    first = adapter.start_span("a")
    adapter.clear_calls()
    second = adapter.start_span("b")
    assert first.span_id == second.span_id == "null-span-1"


# --- CallRecord-Verhalten ----------------------------------------------------


def test_call_record_is_frozen() -> None:
    record = CallRecord(method="log", args=(), kwargs={"level": "info"})
    try:
        record.method = "other"  # type: ignore[misc]
    except (AttributeError, TypeError):
        return
    msg = "CallRecord must be frozen"
    raise AssertionError(msg)


def test_null_log_adapter_isolates_attributes_copy() -> None:
    """Caller-Mutation des `attributes`-Mappings darf den
    Record-Speicher NICHT veraendern."""
    adapter = NullLogAdapter()
    attrs: dict[str, object] = {"k": "v"}
    adapter.log("info", "msg", attributes=attrs)
    attrs["k"] = "MUTATED"
    last = adapter.last_call
    assert last is not None
    stored = last.kwargs["attributes"]
    assert stored == {"k": "v"}
