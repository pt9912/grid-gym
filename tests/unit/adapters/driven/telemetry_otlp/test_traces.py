"""Tests fuer `OtlpTraceAdapter` (M3 Welle 6 C1.3b, ADR 0024 §4.5.1 + §4.5.5).

Pinnt:

- Protocol-Conformance (`isinstance(adapter, TracePort)` via
  `@runtime_checkable`).
- `start_span` liefert einen `SpanContext` mit hex-formatierten
  `trace_id` (32 chars) und `span_id` (16 chars).
- Parent-Child-Schachtelung: Child-Span teilt die `trace_id` des
  Parents; `parent_span_id` matched die Parent-`span_id`.
- `end_span(context)` schliesst den zugehoerigen OTel-Span; spaetere
  `end_span(same_context)`-Aufrufe sind silent No-Op (Idempotenz).
- **`| None`-Robustheit** (ADR 0024 §4.5.1): `end_span(None)` und
  `record_event(None, ...)` sind No-Op statt Exception.
- Attributes werden 1:1 an OTel weitergereicht.
- Tests verwenden `InMemorySpanExporter` als In-Process-Sink (kein
  Live-Collector noetig).
- `time.*`/`datetime`-Freiheit (ADR 0024 §4.5.5 D-4) wird zentral
  vom `AC-OTLP-ADAPTER-NO-TIME`-Contract in `tools/arch_check.py`
  geprueft (AST-basiert, keine Substring-Heuristik).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from grid_gym.adapters.driven.telemetry_otlp import OtlpTraceAdapter
from grid_gym.hexagon.ports.driven.observability import SpanContext, TracePort


@pytest.fixture
def span_exporter() -> Iterator[InMemorySpanExporter]:
    """Liefert einen frisch initialisierten In-Memory-Span-Exporter."""
    exporter = InMemorySpanExporter()
    yield exporter
    exporter.clear()


@pytest.fixture
def adapter(span_exporter: InMemorySpanExporter) -> Iterator[OtlpTraceAdapter]:
    """Verdrahtet `OtlpTraceAdapter` mit einem `SimpleSpanProcessor`-Sink.

    `SimpleSpanProcessor` exportiert synchron beim `span.end()` —
    keine Flush-Pflicht in den Tests selbst (das Buffer-Flush-
    Protokoll aus ADR 0024 §4.5.7 ist Welle-6-C3-Smoke-Material;
    Unit-Tests umgehen es per Sync-Processor).
    """
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    yield OtlpTraceAdapter(provider, instrumentation_name="grid-gym-test")
    provider.shutdown()


# --- Protocol-Conformance ----------------------------------------------------


def _accept_trace_port(port: TracePort) -> TracePort:
    """Statischer Pin (mypy `--strict`): erzwingt strikte `TracePort`-Konformitaet
    trotz der `| None`-Adapter-Robustheit in `end_span`/`record_event`
    (ADR 0024 §4.5.1 — Adapter-spezifische Erweiterung, Protocol bleibt strikt).
    """
    return port


def test_adapter_implements_trace_port(adapter: OtlpTraceAdapter) -> None:
    assert isinstance(adapter, TracePort)
    # Statischer Pin gegen Review-Folge-H-1: `OtlpTraceAdapter.end_span`/
    # `.record_event` haben `SpanContext | None`-Signatur (ADR 0024 §4.5.1);
    # das Protocol verlangt strikt `SpanContext`. Der Adapter-Parameter ist
    # damit kontravariant breiter — Liskov-konform. mypy `--strict` validiert
    # das hier; Runtime-`isinstance` allein wuerde Signatur-Drift nicht
    # fangen, weil `@runtime_checkable` nur Method-Namen prueft.
    _accept_trace_port(adapter)


# --- start_span surface ------------------------------------------------------


def test_start_span_returns_spancontext_with_hex_ids(
    adapter: OtlpTraceAdapter,
) -> None:
    context = adapter.start_span("test.span")
    assert isinstance(context, SpanContext)
    assert len(context.trace_id) == 32
    assert len(context.span_id) == 16
    assert all(c in "0123456789abcdef" for c in context.trace_id)
    assert all(c in "0123456789abcdef" for c in context.span_id)
    assert context.parent_span_id is None
    adapter.end_span(context)


def test_start_span_root_has_no_parent(adapter: OtlpTraceAdapter) -> None:
    context = adapter.start_span("root")
    assert context.parent_span_id is None
    adapter.end_span(context)


def test_start_span_child_inherits_trace_id_from_parent(
    adapter: OtlpTraceAdapter,
) -> None:
    parent = adapter.start_span("parent")
    child = adapter.start_span("child", parent=parent)
    try:
        assert child.trace_id == parent.trace_id
        assert child.span_id != parent.span_id
        assert child.parent_span_id == parent.span_id
    finally:
        adapter.end_span(child)
        adapter.end_span(parent)


def test_start_span_with_attributes_propagates_to_exporter(
    adapter: OtlpTraceAdapter,
    span_exporter: InMemorySpanExporter,
) -> None:
    context = adapter.start_span(
        "with.attrs",
        attributes={"feature": "welle-6", "test": True},
    )
    adapter.end_span(context)
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span_attrs = dict(spans[0].attributes or {})
    assert span_attrs.get("feature") == "welle-6"
    assert span_attrs.get("test") is True


# --- end_span lifecycle ------------------------------------------------------


def test_end_span_finalizes_span(
    adapter: OtlpTraceAdapter,
    span_exporter: InMemorySpanExporter,
) -> None:
    context = adapter.start_span("finalize.test")
    assert len(span_exporter.get_finished_spans()) == 0
    adapter.end_span(context)
    assert len(span_exporter.get_finished_spans()) == 1


def test_end_span_idempotent_after_close(
    adapter: OtlpTraceAdapter,
    span_exporter: InMemorySpanExporter,
) -> None:
    """Doppelter `end_span` ist silent (`Span` ist nicht mehr im `_active_spans`-Cache)."""
    context = adapter.start_span("idempotent.test")
    adapter.end_span(context)
    # Zweites end_span — kein Exception, kein zusaetzlicher exportierter Span.
    adapter.end_span(context)
    assert len(span_exporter.get_finished_spans()) == 1


# --- None-Robustheit (ADR 0024 §4.5.1) ---------------------------------------


def test_end_span_none_is_noop(
    adapter: OtlpTraceAdapter,
    span_exporter: InMemorySpanExporter,
) -> None:
    """`end_span(None)` darf keine Exception werfen (ADR 0024 §4.5.1)."""
    adapter.end_span(None)
    assert len(span_exporter.get_finished_spans()) == 0


def test_record_event_none_is_noop(adapter: OtlpTraceAdapter) -> None:
    """`record_event(None, ...)` darf keine Exception werfen (ADR 0024 §4.5.1)."""
    adapter.record_event(None, "event-name")
    adapter.record_event(None, "event-name", attributes={"key": "value"})


def test_record_event_with_stale_context_is_silent(
    adapter: OtlpTraceAdapter,
) -> None:
    """`record_event` auf einen veralteten Kontext (Span bereits `end`-ed) ist silent."""
    context = adapter.start_span("stale.test")
    adapter.end_span(context)
    # Span ist nicht mehr aktiv — Event darf nicht crashen.
    adapter.record_event(context, "after-end")


# --- record_event-Pfad -------------------------------------------------------


def test_record_event_attaches_to_active_span(
    adapter: OtlpTraceAdapter,
    span_exporter: InMemorySpanExporter,
) -> None:
    context = adapter.start_span("event.test")
    adapter.record_event(context, "step.start", attributes={"phase": "init"})
    adapter.record_event(context, "step.done")
    adapter.end_span(context)
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    event_names = [e.name for e in spans[0].events]
    assert "step.start" in event_names
    assert "step.done" in event_names


# --- Cache-Lifecycle ---------------------------------------------------------


def test_active_spans_cleaned_after_end(adapter: OtlpTraceAdapter) -> None:
    """Internes `_active_spans`-Mapping enthaelt keinen Eintrag nach `end_span`."""
    context = adapter.start_span("cleanup.test")
    assert context.span_id in adapter._active_spans
    adapter.end_span(context)
    assert context.span_id not in adapter._active_spans


# --- Modul-Importe ----------------------------------------------------------
#
# `time.*`/`datetime`-Freiheit (ADR 0024 §4.5.5 D-4) wird zentral vom
# `AC-OTLP-ADAPTER-NO-TIME`-Contract per AST geprueft, nicht hier per
# Substring-Inspektion (Review-Folge H-2). Siehe `tools/arch_check.py`.
