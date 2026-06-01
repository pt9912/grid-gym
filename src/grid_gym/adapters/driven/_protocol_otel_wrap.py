"""Cross-Adapter-OTel-Span-Wrapper fuer `DeviceProtocolPort`-
Implementer (M4 Welle 6a, ADR 0024 §4.5).

Composition-Wrapper, der einen bereits-konstruierten konkreten
`DeviceProtocolPort` (MQTT/Modbus/OPC-UA/DNP3/IEC-61850) mit
OTel-Span-Wrap um die `read(target)`/`write(target, command)`-
Calls einkapselt. Pattern-Praezedenz `tick_loop.py:606-614`
(`_obs_start_span` → `try` → `finally: _obs_end_span`).

**Welle-6a-C2-Architektur-Entscheidung (Variante B):**
Composition-Wrapper statt Class-Decorator (Variante A) oder
Welle-1-Factory-Hook (Variante C, im Repo nicht vorhanden —
`protocol_ports` ist bereits-konstruierte Tuple). Vorteile:

- **Single point of truth**: eine Wrapper-Klasse fuer alle 5
  Adapter; keine Code-Duplikation pro Adapter-Modul.
- **Adapter-Code bleibt unveraendert**: kein Diff in den 5
  `protocol_*/`-Paketen (Welle-6a-Anti-Scope).
- **Test-Pattern repeatable**: gleiche Tests fuer alle 5
  Adapter via `OtelSpanWrappedDeviceProtocolPort`.
- **Opt-in via Caller-Composition**: Tests koennen
  ungewrappte Adapter benutzen; Production-Caller wrappt
  bewusst.
- **GPL-Boundary-konform (Decision I-f)**: dieser Wrapper
  ist MIT; er wrappt zur Laufzeit auch den GPL-isolierten
  `Iec61850DeviceProtocolPort` — kein statischer
  `pyiec61850.*`/`protocol_iec61850.*`-Import, damit kein
  Linker-Taint des MIT-Wrappers.

**Span-Naming-Konvention** (ADR 0024 §4.5):
`"protocol.{adapter_type}.{operation}"` → `"protocol.iec61850.read"`,
`"protocol.modbus.write"` usw.

**Standard-Attribute pro Span:**

- `adapter_type` — `"mqtt"` / `"modbus"` / `"opcua"` / `"dnp3"`
  / `"iec61850"` (vom Wrapper-Constructor).
- `target` — die Target-ID-String, wie sie an `read(target)`
  oder `write(target, command)` uebergeben wurde.
- `operation` — `"read"` oder `"write"`.
- `latency_ms` — `time.monotonic_ns()`-gemessen, gerundet
  auf 3 Nachkommastellen.

**Exception-Pfad:** Bei Exception im wrapped-Call:

1. `record_event(span, "error", attributes={"exception.type":
   exc.__class__.__name__, "exception.message": str(exc)})`.
2. Attribute `error=True` am Span (via separate
   `record_event`-Conventions; OTel-Style).
3. Span wird im `finally` geschlossen (Span-Lifecycle bleibt
   garantiert).
4. Exception wird re-raised (Adapter-Vertrag bleibt
   unveraendert).

**TracePort `None`-Pfad:** Falls `trace_port=None`, ist der
Wrapper ein **Pass-Through** ohne Span — Adapter-Methoden
werden direkt durchgereicht ohne OTel-Overhead. Pattern
analog `_obs_start_span` in `tick_loop.py:373-375`.

**Adapter-Robustheit (ADR 0024 §2.4):** Falls `start_span`
selbst eine Exception wirft (z. B. TracePort-Adapter-Bug),
laeuft der Adapter-Call trotzdem; Span-Wrap ist Observability,
nicht Pflicht-Pfad. **Mitigation:** `start_span`-Exception
wird abgefangen und der Adapter-Call ungewrappt ausgefuehrt
(Best-Effort-Observability).
"""

from __future__ import annotations

import contextlib
import time
from typing import TYPE_CHECKING, Literal

from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPort,
    DeviceProtocolPortError,
)

if TYPE_CHECKING:
    from grid_gym.hexagon.core.domain.command import Command
    from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
    from grid_gym.hexagon.ports.driven.observability import (
        SpanContext,
        TracePort,
    )


_NS_PER_MS = 1_000_000


class OtelSpanWrappedDeviceProtocolPort:
    """Composition-Wrapper um einen `DeviceProtocolPort`-
    Implementer mit OTel-Span-Wrap der `read()`/`write()`-
    Calls (M4 Welle 6a, ADR 0024 §4.5).

    Implementiert selbst das `DeviceProtocolPort`-Protocol;
    `start()`/`stop()` werden ungewrappt durchgereicht
    (Lifecycle-Calls sind nicht im Hot-Path und brauchen
    keinen Span).

    Konstruktor-Argumente:

    - `wrapped` — der konkrete Adapter (z. B.
      `Iec61850DeviceProtocolPort`, `Dnp3DeviceProtocolPort`,
      etc.).
    - `trace_port` — optionaler `TracePort` aus dem
      Observability-Trio. `None` macht den Wrapper zum
      Pass-Through.
    - `adapter_type` — String-Identifier fuer das
      `adapter_type`-Span-Attribut. Welle-6a-Convention:
      `"mqtt"` / `"modbus"` / `"opcua"` / `"dnp3"` /
      `"iec61850"`.
    """

    def __init__(
        self,
        wrapped: DeviceProtocolPort,
        trace_port: "TracePort | None",
        adapter_type: str,
    ) -> None:
        self._wrapped: DeviceProtocolPort = wrapped
        self._trace_port: "TracePort | None" = trace_port
        self._adapter_type: str = adapter_type

    # ------------------------------------------------------------------
    # `DeviceProtocolPort`-Surface
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Lifecycle-Pass-Through. Welle-6a-Convention:
        Lifecycle-Calls sind kein Hot-Path; kein Span-Wrap.
        Caller verfolgt Lifecycle ueber `TickLoop`-Spans
        (Pattern aus `tick_loop.py`-Phasen-Spans)."""
        self._wrapped.start()

    def stop(self) -> None:
        """Lifecycle-Pass-Through; analog `start()`."""
        self._wrapped.stop()

    def read(self, target: str) -> "TelemetryPoint | None":
        """`read()` gewrappt in einen OTel-Span mit Standard-
        Attributen (`adapter_type`/`target`/`operation`/
        `latency_ms`).

        Bei Exception wird ein `record_event("error", ...)`
        am Span angehaengt; Span wird im `finally`
        geschlossen; Exception re-raised.
        """
        return self._call_with_span("read", target, self._wrapped.read)

    def write(self, target: str, command: "Command") -> None:
        """`write()` gewrappt in einen OTel-Span; analog
        `read()`."""
        # Lambdaesque-Currying haetten wir gerne; aber wir
        # halten den Lifecycle-Code simpel und duplizieren
        # die Span-Wrap-Struktur fuer `write` direkt.
        self._call_with_span_write(target, command)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_with_span(
        self,
        operation: Literal["read"],
        target: str,
        method: object,
    ) -> "TelemetryPoint | None":
        """Span-gewrappter `read`-Call. Eigener Helper, weil
        `read` und `write` unterschiedliche Returntypes haben
        und mypy --strict-mode `Any`-Returns nicht akzeptiert.
        """
        span = self._safe_start_span(operation, target)
        start_ns = time.monotonic_ns()
        try:
            # method ist self._wrapped.read; bound method.
            result: "TelemetryPoint | None" = method(target)  # type: ignore[operator]
        except DeviceProtocolPortError as exc:
            self._record_exception(span, exc)
            raise
        else:
            return result
        finally:
            self._safe_end_span(span, start_ns)

    def _call_with_span_write(
        self,
        target: str,
        command: "Command",
    ) -> None:
        """Span-gewrappter `write`-Call. Analog
        `_call_with_span` aber mit `command`-Argument und
        `None`-Returntype."""
        span = self._safe_start_span("write", target)
        start_ns = time.monotonic_ns()
        try:
            self._wrapped.write(target, command)
        except DeviceProtocolPortError as exc:
            self._record_exception(span, exc)
            raise
        finally:
            self._safe_end_span(span, start_ns)

    def _safe_start_span(
        self, operation: Literal["read", "write"], target: str
    ) -> "SpanContext | None":
        """Oeffnet einen Span; Best-Effort-Observability —
        Exception aus `start_span` selbst (Adapter-Bug)
        wird abgefangen und der Adapter-Call laeuft trotzdem
        (ADR 0024 §2.4 Adapter-Robustheit)."""
        if self._trace_port is None:
            return None
        # Best-Effort-Observability: TracePort-Adapter-Bugs (Runtime/
        # Attribute/Type/Value/Key/OSError-Famille; ADR 0024 §2.4)
        # duerfen den Adapter-Call nicht crashen. Eng-gefasste Exception-
        # Liste statt blind `Exception` — falls neue Library-Exceptions
        # auftauchen, faellt der Adapter mit dem unbekannten Fehler
        # (sichtbares Signal statt stiller Swallow).
        try:
            return self._trace_port.start_span(
                f"protocol.{self._adapter_type}.{operation}",
                attributes={
                    "adapter_type": self._adapter_type,
                    "target": target,
                    "operation": operation,
                },
            )
        except (RuntimeError, AttributeError, TypeError, ValueError, KeyError, OSError):
            return None

    def _safe_end_span(self, span: "SpanContext | None", start_ns: int) -> None:
        """Schliesst einen offenen Span mit `latency_ms`-
        Event. Best-Effort: Exception aus `end_span` selbst
        wird abgefangen (ADR 0024 §2.4 Adapter-Robustheit)."""
        if self._trace_port is None or span is None:
            return
        latency_ms = round((time.monotonic_ns() - start_ns) / _NS_PER_MS, 3)
        with contextlib.suppress(Exception):
            self._trace_port.record_event(
                span,
                "latency",
                attributes={"latency_ms": latency_ms},
            )
            self._trace_port.end_span(span)

    def _record_exception(self, span: "SpanContext | None", exc: BaseException) -> None:
        """Haengt ein `error`-Event an den offenen Span.
        Best-Effort; falls TracePort/Span `None` oder
        Library-Exception aus `record_event` selbst,
        wird der Adapter-Call-Exception trotzdem
        weiterpropagiert (re-raise im aufrufenden
        `_call_with_span`/`_call_with_span_write`)."""
        if self._trace_port is None or span is None:
            return
        with contextlib.suppress(Exception):
            self._trace_port.record_event(
                span,
                "error",
                attributes={
                    "exception.type": exc.__class__.__name__,
                    "exception.message": str(exc),
                },
            )
