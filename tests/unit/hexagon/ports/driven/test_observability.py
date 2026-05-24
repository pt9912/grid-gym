"""Protocol-Shape-Tests fuer das Observability-Port-Trio
(M3 Welle 5, ADR 0024 §2.1-§2.4).

Pattern aus `tests/unit/hexagon/ports/driven/test_fault.py`:
- Inline-Stubs (kein Test-Fake-Modul, weil die Null-Adapter aus
  `adapters/driven/observability_null/` bereits eine produktive
  Default-Implementation sind).
- `isinstance(stub, <Port>)` per `@runtime_checkable`.
- Methoden-Surface-Aufruf zur Sanity.
"""

from __future__ import annotations

from collections.abc import Mapping

from grid_gym.hexagon.ports.driven.observability import (
    LogEntry,
    LogPort,
    MetricsPort,
    SpanContext,
    TracePort,
)


class _StubLogPort:
    def log(self, entry: LogEntry) -> None:
        _ = entry


class _StubMetricsPort:
    def increment(
        self,
        name: str,
        value: int = 1,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        pass

    def gauge(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        pass

    def observe(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        pass


class _StubTracePort:
    def start_span(
        self,
        name: str,
        *,
        parent: SpanContext | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> SpanContext:
        return SpanContext(trace_id="t", span_id="s")

    def end_span(self, context: SpanContext) -> None:
        pass

    def record_event(
        self,
        context: SpanContext,
        name: str,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        pass


def test_stub_log_port_satisfies_log_port_protocol() -> None:
    assert isinstance(_StubLogPort(), LogPort)


def test_stub_metrics_port_satisfies_metrics_port_protocol() -> None:
    assert isinstance(_StubMetricsPort(), MetricsPort)


def test_stub_trace_port_satisfies_trace_port_protocol() -> None:
    assert isinstance(_StubTracePort(), TracePort)


def test_span_context_is_frozen() -> None:
    """ADR 0024 §2.4: `SpanContext` ist frozen dataclass."""
    ctx = SpanContext(trace_id="t1", span_id="s1")
    try:
        ctx.trace_id = "other"  # type: ignore[misc]
    except (AttributeError, TypeError):
        return
    msg = "SpanContext must be frozen (ADR 0024 §2.4)"
    raise AssertionError(msg)


def test_span_context_parent_defaults_to_none() -> None:
    """ADR 0024 §2.4: Root-Spans haben `parent_span_id=None`."""
    ctx = SpanContext(trace_id="t1", span_id="s1")
    assert ctx.parent_span_id is None


def test_span_context_carries_parent_chain() -> None:
    """ADR 0024 §2.4: Nested Spans tragen `parent_span_id`."""
    ctx = SpanContext(trace_id="t1", span_id="s2", parent_span_id="s1")
    assert ctx.parent_span_id == "s1"
