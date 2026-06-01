"""Cross-Adapter-OTel-Span-Wrapper fuer `DeviceProtocolPort`-
Implementer (M4 Welle 6a, ADR 0024 §4.5; Slice 034 Review-Folge).

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

**Standard-Attribute pro Span** (Slice 034 Schaerfung):

- `adapter_type` — eines aus `{"mqtt","modbus","opcua","dnp3",
  "iec61850"}` (Constructor-Whitelist via `Literal`-Typ).
- `target` — die Target-ID-String aus dem `read`/`write`-Call.
- `operation` — `"read"` oder `"write"`.
- `reference` — Adapter-spezifische Referenz-ID (z. B. IEC-61850
  `IED/LD/LN.Object`-Path); **optional**, nur gesetzt falls
  Caller eine `reference` am Constructor uebergeben hat.

**Event-encoded Latency** (Slice 034 Schaerfung):

`latency_ms` ist KEIN Span-Attribut (TracePort-Protocol hat
keine `set_attribute`-Surface; Attribute koennen nur bei
`start_span` gesetzt werden, latency ist da noch nicht bekannt).
Stattdessen wird ein separates `record_event(span, "latency",
attributes={"latency_ms": float})` emittiert. Downstream-OTLP-
Collector kann zusaetzlich die Span-Duration (start_time →
end_time) auswerten — beide Werte sind konsistent, da der
Latency-Capture die gesamte Span-Dauer inkl. `start_span`-
Overhead abbildet (Slice 034 F12: `start_ns` wird VOR
`_safe_start_span` gemessen).

**Exception-Pfad:** Bei typed `DeviceProtocolPort{Read,Write}Error`:

1. `record_event(span, "error", attributes={"exception.type":
   exc.__class__.__name__, "exception.message": str(exc)})`.
2. Span wird im `finally` geschlossen (Span-Lifecycle bleibt
   garantiert — Slice 034 F1: `record_event` + `end_span` in
   separaten Try/Except-Bloecken, nicht im gemeinsamen
   `suppress(Exception)`).
3. Exception wird re-raised (Adapter-Vertrag bleibt
   unveraendert).

**Operation-spezifischer Catch** (Slice 034 F3): `read()`-
Wrapper faengt nur `DeviceProtocolPortReadError`; `write()`-
Wrapper faengt nur `DeviceProtocolPortWriteError`. Falsche
Operation-zugeordnete Errors (z. B. `ReadError` aus `write()`)
propagieren raw OHNE `error`-Event-Attribution — der Wrapper
attribuiert nur typed-korrekte Adapter-Fehler. Library-Bugs
oder Adapter-Bugs (raw `RuntimeError`, `socket.timeout`)
propagieren ebenfalls raw.

**TracePort `None`-Pfad:** Falls `trace_port=None`, ist der
Wrapper ein **Pass-Through** ohne Span — Adapter-Methoden
werden direkt durchgereicht ohne OTel-Overhead. Pattern
analog `_obs_start_span` in `tick_loop.py:373-375`.

**Adapter-Robustheit (ADR 0024 §2.4):** TracePort-Adapter-
Bugs (Exceptions aus `start_span`/`record_event`/`end_span`
selbst) duerfen den Adapter-Call nicht crashen. Best-Effort-
Observability — eng-gefasste Exception-Tuples in allen drei
Best-Effort-Helpern (`_safe_start_span`, `_safe_end_span`,
`_record_exception`) sorgen fuer **sichtbare Signale** bei
unbekannten Library-Exceptions statt stiller Swallow (Slice
034 F9: einheitliches Catch-Tupel ueber alle drei Helper).

**Trace-Parent-Span-Anti-Scope (Slice 034 F5):** Der Wrapper
ruft `TracePort.start_span` OHNE `parent=`-Argument auf —
Adapter-Spans sind aus Wrapper-Sicht Root-Spans. Trace-
Chain-Propagation (Tick → Phase → Adapter) ist OTLP-
Adapter-Sache via OTel-ContextVars (W3C-Trace-Context-
Standard); der Wrapper bleibt context-var-naiv und delegiert
die Parent-Detection an die OTel-SDK-Schicht. Welle-7-
Closure pruft ob ein expliziter `parent_provider`-Hook
notwendig ist.
"""

from __future__ import annotations

import contextlib
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPort,
    DeviceProtocolPortReadError,
    DeviceProtocolPortWriteError,
)

if TYPE_CHECKING:
    from grid_gym.hexagon.core.domain.command import Command
    from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
    from grid_gym.hexagon.ports.driven.observability import (
        SpanContext,
        TracePort,
    )


_NS_PER_MS = 1_000_000

AdapterType = Literal["mqtt", "modbus", "opcua", "dnp3", "iec61850"]
"""Welle-6a-Whitelist fuer `adapter_type`. Slice 034 F11:
typed-narrow statt freier String — Caller-Mistakes
(`"IEC61850"` vs `"iec61850"`) sind static-type-errors."""

# Slice 034 F9: einheitliches Best-Effort-Catch-Tupel ueber
# alle drei Helper. ADR 0024 §2.4-Adapter-Robustheit; unbekannte
# Exceptions duerfen propagieren (sichtbares Signal statt
# stiller Swallow).
_BEST_EFFORT_OBSERVABILITY_EXCEPTIONS: tuple[type[BaseException], ...] = (
    RuntimeError,
    AttributeError,
    TypeError,
    ValueError,
    KeyError,
    OSError,
)


class OtelSpanWrappedDeviceProtocolPort:
    """Composition-Wrapper um einen `DeviceProtocolPort`-
    Implementer mit OTel-Span-Wrap der `read()`/`write()`-
    Calls (M4 Welle 6a, ADR 0024 §4.5; Slice 034 Review-Folge).

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
    - `adapter_type` — `AdapterType`-Literal aus der
      Welle-6a-Whitelist (`"mqtt"`/`"modbus"`/`"opcua"`/
      `"dnp3"`/`"iec61850"`). Slice 034 F11.
    - `reference` — optionaler Adapter-spezifischer
      Referenz-Identifier (z. B. IEC-61850 IED/LD-Path);
      wird als Span-Attribut emittiert falls != None.
      Slice 034 F2.
    """

    def __init__(
        self,
        wrapped: DeviceProtocolPort,
        trace_port: "TracePort | None",
        adapter_type: AdapterType,
        reference: str | None = None,
    ) -> None:
        self._wrapped: DeviceProtocolPort = wrapped
        self._trace_port: "TracePort | None" = trace_port
        self._adapter_type: AdapterType = adapter_type
        self._reference: str | None = reference

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
        optional `reference`) und `latency`-Event.

        Bei `DeviceProtocolPortReadError` (Slice 034 F3:
        operation-spezifischer Catch) wird ein
        `record_event("error", ...)` am Span angehaengt;
        Span wird im `finally` geschlossen; Exception
        re-raised.
        """
        return self._call_with_span_read(target)

    def write(self, target: str, command: "Command") -> None:
        """`write()` gewrappt in einen OTel-Span; analog
        `read()`, faengt nur `DeviceProtocolPortWriteError`
        (Slice 034 F3)."""
        self._call_with_span_write(target, command)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_with_span_read(
        self,
        target: str,
    ) -> "TelemetryPoint | None":
        """Span-gewrappter `read`-Call. Slice 034 F12:
        `start_ns` VOR `_safe_start_span` (inkludiert
        `start_span`-Overhead in `latency_ms`)."""
        start_ns = time.monotonic_ns()
        span = self._safe_start_span("read", target)
        # Slice 034 F8: properly typed Callable statt `object`.
        method: Callable[[str], "TelemetryPoint | None"] = self._wrapped.read
        try:
            result = method(target)
        except DeviceProtocolPortReadError as exc:
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
        """Span-gewrappter `write`-Call. Slice 034 F12:
        `start_ns` VOR `_safe_start_span`. Slice 034 F3:
        operation-spezifischer Catch (nur
        `DeviceProtocolPortWriteError`)."""
        start_ns = time.monotonic_ns()
        span = self._safe_start_span("write", target)
        try:
            self._wrapped.write(target, command)
        except DeviceProtocolPortWriteError as exc:
            self._record_exception(span, exc)
            raise
        finally:
            self._safe_end_span(span, start_ns)

    def _safe_start_span(
        self, operation: Literal["read", "write"], target: str
    ) -> "SpanContext | None":
        """Oeffnet einen Span; Best-Effort-Observability —
        TracePort-Adapter-Bugs (eng-gefasstes Catch-Tupel)
        crashen den Adapter-Call nicht (ADR 0024 §2.4)."""
        if self._trace_port is None:
            return None
        attributes: dict[str, object] = {
            "adapter_type": self._adapter_type,
            "target": target,
            "operation": operation,
        }
        # Slice 034 F2: `reference` ist optional Span-Attribut.
        if self._reference is not None:
            attributes["reference"] = self._reference
        try:
            return self._trace_port.start_span(
                f"protocol.{self._adapter_type}.{operation}",
                attributes=attributes,
            )
        except _BEST_EFFORT_OBSERVABILITY_EXCEPTIONS:
            return None

    def _safe_end_span(self, span: "SpanContext | None", start_ns: int) -> None:
        """Schliesst einen offenen Span mit `latency`-Event.

        Slice 034 F1 + F9: `record_event` und `end_span`
        sind in SEPARATEN Best-Effort-Try-Bloecken — bricht
        `record_event` selbst (z. B. Library-Bug), wird
        `end_span` trotzdem ausgefuehrt. Span-Lifecycle-
        Garantie wiederhergestellt.
        """
        if self._trace_port is None or span is None:
            return
        latency_ms = round((time.monotonic_ns() - start_ns) / _NS_PER_MS, 3)
        with contextlib.suppress(*_BEST_EFFORT_OBSERVABILITY_EXCEPTIONS):
            self._trace_port.record_event(
                span,
                "latency",
                attributes={"latency_ms": latency_ms},
            )
        with contextlib.suppress(*_BEST_EFFORT_OBSERVABILITY_EXCEPTIONS):
            self._trace_port.end_span(span)

    def _record_exception(
        self,
        span: "SpanContext | None",
        exc: DeviceProtocolPortReadError | DeviceProtocolPortWriteError,
    ) -> None:
        """Haengt ein `error`-Event an den offenen Span.

        Slice 034 F9: gleiches Catch-Tupel wie
        `_safe_start_span`/`_safe_end_span`. Slice 034
        Doc-Schaerfung: `exc`-Typ ist auf die typed-
        DPP-Errors verengt (wird nur aus den Operation-
        spezifischen Except-Klauseln aufgerufen).
        """
        if self._trace_port is None or span is None:
            return
        with contextlib.suppress(*_BEST_EFFORT_OBSERVABILITY_EXCEPTIONS):
            self._trace_port.record_event(
                span,
                "error",
                attributes={
                    "exception.type": exc.__class__.__name__,
                    "exception.message": str(exc),
                },
            )
