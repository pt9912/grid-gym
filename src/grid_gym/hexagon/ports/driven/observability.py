"""Observability-Port-Trio (M3 Welle 5, ADR 0024 §2.1-§2.4).

Driven-Port-Trio fuer strukturierte Observability nach
`GG-AR-PORT-DRN-008` und Architektur §15:

- `LogPort` (`GG-OTEL-002`) — strukturierte Logs.
- `MetricsPort` (`GG-OTEL-003`) — Counter / Gauge / Observe.
- `TracePort` (`GG-OTEL-001`/`004`) — Spans + `SpanContext`-Vertrag.

Welle-5-Foundation liefert die drei Protocols + den projekt-eigenen
`SpanContext`-Record. Konkrete Adapter:

- Welle 5 (diese Welle): `adapters/driven/observability_null/`
  (Null-Adapter-Trio fuer Test-Default-Pfade).
- Welle 6: `adapters/driven/telemetry-otlp/` (produktiver OTLP-
  Adapter, mappt `SpanContext` auf den W3C-Trace-Standard).

**ADR-0024-Invariante (§2.1)**: keine OTLP-/SDK-Typen im Port-Layer.
`SpanContext` ist eine interne, projekt-eigene frozen dataclass —
String-basierte Identifier ohne W3C-Trace-Spec-Bindung. Der Core
bleibt damit OTLP-frei und laeuft ohne den OTLP-Stack.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class SpanContext:
    """Internes Span-Kontext-Modell (ADR 0024 §2.4).

    `trace_id` und `span_id` sind opaque String-Identifier — der
    Adapter waehlt das Format (UUID, W3C-Trace-Spec hex, deterministisch
    je Test-Run). `parent_span_id` traegt die Schachtelung; `None`
    markiert den Root-Span einer Trace-Kette.
    """

    trace_id: str
    span_id: str
    parent_span_id: str | None = None


@runtime_checkable
class LogPort(Protocol):
    """Strukturierte Logs (ADR 0024 §2.2; Lastenheft `GG-OTEL-002`,
    Architektur §15).

    Pflicht-Surface:

    - `log(level, message, *, run_id, module, event_id, attributes)`:
      strukturiertes Log-Event.

    Pflicht-Felder der Adapter-Sicht (Architektur §15): `ts`
    (Adapter setzt aus eigener Clock-Quelle), `level`, `run_id`,
    `module`, `event_id`, `message`. `attributes` traegt
    zusaetzliche strukturierte Payload ueber die Pflicht-Felder hinaus.

    `level` ist als String typisiert (keine Enum-Hierarchie im
    Port-Layer); Adapter sind frei in der Mapping-Wahl (z. B. auf
    `logging.DEBUG/INFO/WARNING/ERROR`). `ts` ist Adapter-
    Verantwortung — TickLoop und andere Core-Aufrufer haben per
    AC-NO-TIME keinen Wall-Clock-Zugang.
    """

    def log(  # noqa: PLR0913 — 6 Felder spiegeln das Pflicht-Set aus Architektur §15 `GG-OTEL-002` (`level`, `message`, `run_id`, `module`, `event_id`, `attributes`).
        self,
        level: str,
        message: str,
        *,
        run_id: str | None = None,
        module: str | None = None,
        event_id: str | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        """Emittiert ein strukturiertes Log-Event."""
        ...


@runtime_checkable
class MetricsPort(Protocol):
    """Metriken (ADR 0024 §2.3; Lastenheft `GG-OTEL-003`,
    Architektur §15).

    Drei Methoden decken die in Architektur §15 genannten Metrik-
    Familien ab:

    - `increment(name, value=1, attributes)`: monoton steigender
      Counter (z. B. `error_count`, `telemetry_points_total`).
    - `gauge(name, value, attributes)`: momentaner Wert
      (z. B. `event_queue_len`, `tick_index`).
    - `observe(name, value, attributes)`: Verteilung / Histogramm
      (z. B. `tick_duration_ms` — instrumentiert vom OTLP-Adapter
      via externer Wall-Clock, nicht aus TickLoop selbst, weil
      `AC-NO-TIME` Wall-Clock-Zugriff im Core verbietet).

    `name` ist String — kein zentrales Registry. Metric-Naming-
    Konvention lebt im OTLP-Adapter und in den Aufrufern.
    `attributes` ist Mapping-basierte Dimensionierung (OTLP-Labels).
    """

    def increment(
        self,
        name: str,
        value: int = 1,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        """Inkrementiert einen Counter."""
        ...

    def gauge(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        """Setzt einen Gauge-Wert."""
        ...

    def observe(
        self,
        name: str,
        value: float,
        *,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        """Beobachtet einen Verteilungs-Wert."""
        ...


@runtime_checkable
class TracePort(Protocol):
    """Traces + `SpanContext`-Vertrag (ADR 0024 §2.4; Lastenheft
    `GG-OTEL-001`/`004`, Architektur §15).

    `start_span` gibt den `SpanContext` zurueck — Aufrufer muss
    ihn fuer `end_span` und `record_event` weiterreichen.
    `parent` markiert die Schachtelung (Tick → Scheduler → Device
    → Adapter → Persistenz).

    **Adapter-Robustheit (ADR 0024 §2.4)**: falls ein Aufrufer
    `None` als `context` an `end_span` oder `record_event`
    weiterleitet (defensiver Programmierstil — z. B. wenn ein
    vorgelagerter Span nicht geoeffnet wurde), gilt **No-Op** als
    erlaubtes Fallback-Verhalten im Adapter. Das Type-System verlangt
    den Kontext nominell, der Adapter absorbiert `None` ohne
    Exception. Diese Invariante schuetzt vor Cascading-Failures
    bei optionalem Telemetrie-Verdrahten.
    """

    def start_span(
        self,
        name: str,
        *,
        parent: SpanContext | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> SpanContext:
        """Oeffnet einen Span und liefert den Kontext zurueck."""
        ...

    def end_span(self, context: SpanContext) -> None:
        """Schliesst einen offenen Span. No-Op bei `None`."""
        ...

    def record_event(
        self,
        context: SpanContext,
        name: str,
        attributes: Mapping[str, object] | None = None,
    ) -> None:
        """Haengt ein Event an einen offenen Span. No-Op bei `None`."""
        ...
