"""OTLP-Trace-Adapter (M3 Welle 6, ADR 0024 §4.5.1 + §4.5.5).

Implementiert `TracePort` und reicht Spans an die OTel-SDK weiter.
Per ADR 0024 §4.5.5 (D-4) wird **kein** `time.*` importiert — Start-/
End-Zeitpunkte werden vom OTel-Span/SDK selbst gesetzt
(`tracer.start_span()` setzt `StartTime`, `span.end()` setzt
`EndTime`). `AC-NO-TIME` bleibt damit auch im Adapter-Code KEPT.

Per ADR 0024 §4.5.1 (L-2) traegt der Adapter die `| None`-Robustheit
fuer `end_span` und `record_event` — wenn ein defensiver Aufrufer
`None` weiterleitet (z. B. weil ein vorgelagerter `start_span`
geskippt wurde), gilt **No-Op** statt Exception. Das Port-Protocol
bleibt strikt (siehe ADR 0024 §2.4); die Robustheit ist Adapter-
Verantwortung.

Mapping unseres `SpanContext` (drei String-Felder) auf den OTel-
W3C-Trace-Standard:

- `trace_id` ← lower-case hex der OTel-`trace_id` (32 chars, kein
  Prefix).
- `span_id` ← lower-case hex der OTel-`span_id` (16 chars, kein
  Prefix).
- `parent_span_id` ← unsere eigene Aufrufer-Sicht (vom `start_span`-
  Parameter durchgereicht); der OTLP-Exporter zieht die echte
  W3C-Parent-Beziehung aus dem OTel-Span-Kontext.

State: der Adapter haelt ein `dict[str, otel_trace.Span]`-Mapping
von unserer `span_id` auf das OTel-Span-Objekt, damit `end_span`
und `record_event` den korrekten Span finden. Bei `end_span` wird
der Eintrag entfernt; das schuetzt vor Leaks ueber lange TickLoop-
Laeufe (Welle-5-`tick.cycle`-Span pro Tick).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final, cast

from opentelemetry import trace as otel_trace
from opentelemetry.context import Context as OtelContext
from opentelemetry.sdk.trace import TracerProvider

from grid_gym.hexagon.ports.driven.observability import SpanContext

__all__ = ["OtlpTraceAdapter"]

# Hex-Format-Breiten fuer W3C-Trace-Spec (128-bit / 64-bit).
_TRACE_ID_HEX_WIDTH: Final[int] = 32
_SPAN_ID_HEX_WIDTH: Final[int] = 16


class OtlpTraceAdapter:
    """Trace-Adapter fuer OTLP-gRPC-Export (M3 Welle 6).

    Implementiert `TracePort` (`start_span`/`end_span`/`record_event`).
    Konstruktor erwartet ein bereits konfiguriertes `TracerProvider` —
    der Adapter besitzt es nicht, sondern bekommt es injiziert
    (typisch von `build_otlp_adapters(config)` in C1.3c).

    Thread-Safety: nicht thread-safe (Welle-6-Use-Case: single-threaded
    TickLoop). Der OTel-Tracer selbst ist thread-safe; nur das interne
    `_active_spans`-Mapping ist es nicht.
    """

    def __init__(
        self,
        tracer_provider: TracerProvider,
        *,
        instrumentation_name: str = "grid-gym",
    ) -> None:
        self._tracer = tracer_provider.get_tracer(instrumentation_name)
        # Mapping von unserer `span_id` (hex-String) auf den OTel-Span.
        # Aufraeumung erfolgt in `end_span`; ein TickLoop-Lauf erzeugt
        # so viele Eintraege wie offene Spans pro Tick (typisch 1-3).
        self._active_spans: dict[str, otel_trace.Span] = {}

    def start_span(
        self,
        name: str,
        *,
        parent: SpanContext | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> SpanContext:
        """Oeffnet einen Span und liefert den `SpanContext` zurueck."""
        otel_attrs = self._to_otel_attributes(attributes)
        otel_context: OtelContext | None = None
        if parent is not None:
            parent_otel_span = self._active_spans.get(parent.span_id)
            if parent_otel_span is not None:
                otel_context = otel_trace.set_span_in_context(parent_otel_span)
        otel_span = self._tracer.start_span(
            name,
            context=otel_context,
            attributes=otel_attrs,
        )
        span_ctx = otel_span.get_span_context()
        our_span_id = format(span_ctx.span_id, f"0{_SPAN_ID_HEX_WIDTH}x")
        our_trace_id = format(span_ctx.trace_id, f"0{_TRACE_ID_HEX_WIDTH}x")
        parent_span_id = parent.span_id if parent is not None else None
        context = SpanContext(
            trace_id=our_trace_id,
            span_id=our_span_id,
            parent_span_id=parent_span_id,
        )
        self._active_spans[our_span_id] = otel_span
        return context

    def end_span(self, context: SpanContext | None) -> None:
        """Schliesst einen offenen Span. `None`-Robustheit per ADR §4.5.1."""
        if context is None:
            return
        otel_span = self._active_spans.pop(context.span_id, None)
        if otel_span is not None:
            otel_span.end()
        # else: Span war nie gestartet oder schon geschlossen — silent
        # No-Op statt Exception (Adapter-Robustheit).

    def record_event(
        self,
        context: SpanContext | None,
        name: str,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        """Haengt ein Event an einen offenen Span. `None`-Robustheit per ADR §4.5.1."""
        if context is None:
            return
        otel_span = self._active_spans.get(context.span_id)
        if otel_span is None:
            # Defensiv — Aufrufer haelt einen veralteten Context.
            return
        otel_span.add_event(name, attributes=self._to_otel_attributes(attributes))

    @staticmethod
    def _to_otel_attributes(
        attributes: Mapping[str, object] | None,
    ) -> Mapping[str, Any] | None:
        """Konvertiert unsere Mapping-basierten Attributes zu einem OTel-konformen `dict`.

        Liefert `None` (statt leerem dict) zurueck, wenn keine Attributes
        gegeben sind — das matched die OTel-API-Default-Konvention und
        macht Test-Asserts auf `attributes is None` einfacher.

        Rueckgabetyp ist bewusst `Mapping[str, Any]` (statt der strikteren
        OTel-`AttributeValue`-Union): der Port-Layer akzeptiert
        `Mapping[str, object]` (ADR 0024 §2.2-§2.4), und die OTel-SDK
        validiert Wert-Typen zur Laufzeit; ein engerer Compile-Time-Vertrag
        wuerde den Port-Adapter-Vertrag ohne Mehrwert verengen.
        """
        if attributes is None:
            return None
        return cast("Mapping[str, Any]", dict(attributes))
