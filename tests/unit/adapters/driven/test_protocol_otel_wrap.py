"""Cross-Adapter-OTel-Span-Wrap-Tests (M4 Welle 6a, ADR 0024 §4.5).

Verifiziert dass der `OtelSpanWrappedDeviceProtocolPort`-
Composition-Wrapper:

- `read()` und `write()` in einem Span mit Standard-Attributen
  (`adapter_type`/`target`/`operation`/`latency_ms`) wrappt.
- Span auch bei Exception schliesst (`finally`-Pfad);
  Exception wird re-raised.
- Bei TracePort=None Pass-Through bleibt (kein Span,
  Adapter-Call direkt).
- Lifecycle-Calls (`start()`/`stop()`) ungewrappt durchreicht.
- Adapter-spezifische Errors (z. B. `Iec61850PortReadFailedError`)
  als `record_event("error", ...)` registriert werden.

Tests verwenden Mock-Adapter und einen NullTraceAdapter
(`RecordingNullTraceAdapter`) zur Span-Aufzeichnung —
keine echte OTel-Library-Dependency.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

import pytest

from grid_gym.adapters.driven._protocol_otel_wrap import (
    OtelSpanWrappedDeviceProtocolPort,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPortReadError,
    DeviceProtocolPortWriteError,
)
from grid_gym.hexagon.ports.driven.observability import SpanContext


# ---------------------------------------------------------------------------
# Test-Helpers
# ---------------------------------------------------------------------------


@dataclass
class _RecordedSpan:
    """Aufgezeichneter Span fuer Test-Assertions."""

    name: str
    attributes: dict[str, object]
    events: list[tuple[str, dict[str, object]]] = field(default_factory=list)
    ended: bool = False


class _RecordingTracePort:
    """Test-Double, das alle Span-Open/Event/Close-Calls
    aufzeichnet und in einer Liste exposes."""

    def __init__(self) -> None:
        self.spans: list[_RecordedSpan] = []
        # context → span-index mapping
        self._index: dict[SpanContext, int] = {}

    def start_span(
        self,
        name: str,
        *,
        parent: SpanContext | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> SpanContext:
        recorded = _RecordedSpan(
            name=name,
            attributes=dict(attributes or {}),
        )
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


def _make_telemetry_point(target: str, value: object = 42.0) -> TelemetryPoint:
    return TelemetryPoint(
        run_id="run-test",
        tick=0,
        simulation_time=0,
        device_id=target,
        metric="test",
        value=value,
        unit="",
        quality=Quality.VALID,
        source=f"test.{target}",
        sequence=0,
    )


def _make_command(target: str) -> Command:
    return Command(
        command_id=f"cmd-{target}",
        simulation_time=0,
        target_device_id=target,
        type="set",
        payload={"value": 1.0},
        validation_status="validated",
        result=CommandResult.ACCEPTED,
    )


def _make_mock_adapter(
    *,
    read_return: Any = None,
    read_raises: BaseException | None = None,
    write_raises: BaseException | None = None,
) -> Any:
    adapter = MagicMock()
    adapter.start = MagicMock()
    adapter.stop = MagicMock()
    if read_raises is not None:
        adapter.read = MagicMock(side_effect=read_raises)
    else:
        adapter.read = MagicMock(return_value=read_return)
    if write_raises is not None:
        adapter.write = MagicMock(side_effect=write_raises)
    else:
        adapter.write = MagicMock(return_value=None)
    return adapter


# ---------------------------------------------------------------------------
# read() Span-Wrap
# ---------------------------------------------------------------------------


def test_read_opens_and_ends_span_with_standard_attributes() -> None:
    expected_point = _make_telemetry_point("battery1_voltage", value=230.5)
    adapter = _make_mock_adapter(read_return=expected_point)
    trace = _RecordingTracePort()
    wrapped = OtelSpanWrappedDeviceProtocolPort(adapter, trace_port=trace, adapter_type="iec61850")

    result = wrapped.read("battery1_voltage")

    assert result is expected_point
    adapter.read.assert_called_once_with("battery1_voltage")
    assert len(trace.spans) == 1
    span = trace.spans[0]
    assert span.name == "protocol.iec61850.read"
    assert span.attributes["adapter_type"] == "iec61850"
    assert span.attributes["target"] == "battery1_voltage"
    assert span.attributes["operation"] == "read"
    assert span.ended is True


def test_read_records_latency_event() -> None:
    adapter = _make_mock_adapter(read_return=_make_telemetry_point("t1"))
    trace = _RecordingTracePort()
    wrapped = OtelSpanWrappedDeviceProtocolPort(adapter, trace_port=trace, adapter_type="modbus")
    wrapped.read("t1")

    span = trace.spans[0]
    latency_events = [e for e in span.events if e[0] == "latency"]
    assert len(latency_events) == 1
    _, latency_attrs = latency_events[0]
    assert "latency_ms" in latency_attrs
    # Mock-Call ist ~Mikrosekunden; latency_ms muss non-negative float sein.
    assert isinstance(latency_attrs["latency_ms"], float)
    assert latency_attrs["latency_ms"] >= 0.0


def test_read_exception_records_error_event_and_reraises() -> None:
    # Welle-6a-Convention: Adapter werfen typed
    # `DeviceProtocolPortReadError`-Subclasses (Vertrag aus
    # ADR 0030 §2.1). Library-Errors werden adapter-intern
    # gemappt. Der Wrapper fängt nur typed DPP-Errors;
    # Library-Bugs propagieren raw.
    library_error = DeviceProtocolPortReadError("read failed at server")
    adapter = _make_mock_adapter(read_raises=library_error)
    trace = _RecordingTracePort()
    wrapped = OtelSpanWrappedDeviceProtocolPort(adapter, trace_port=trace, adapter_type="dnp3")

    with pytest.raises(DeviceProtocolPortReadError, match="read failed"):
        wrapped.read("target-x")

    # Span wurde geoeffnet und geschlossen trotz Exception.
    assert len(trace.spans) == 1
    span = trace.spans[0]
    assert span.ended is True

    # Error-Event ist aufgezeichnet.
    error_events = [e for e in span.events if e[0] == "error"]
    assert len(error_events) == 1
    _, error_attrs = error_events[0]
    assert error_attrs["exception.type"] == "DeviceProtocolPortReadError"
    assert error_attrs["exception.message"] == "read failed at server"


def test_read_returns_none_when_adapter_returns_none() -> None:
    adapter = _make_mock_adapter(read_return=None)
    trace = _RecordingTracePort()
    wrapped = OtelSpanWrappedDeviceProtocolPort(adapter, trace_port=trace, adapter_type="mqtt")

    result = wrapped.read("subscriber-t1")

    assert result is None
    assert len(trace.spans) == 1
    assert trace.spans[0].ended is True


# ---------------------------------------------------------------------------
# write() Span-Wrap
# ---------------------------------------------------------------------------


def test_write_opens_and_ends_span_with_standard_attributes() -> None:
    adapter = _make_mock_adapter()
    trace = _RecordingTracePort()
    wrapped = OtelSpanWrappedDeviceProtocolPort(adapter, trace_port=trace, adapter_type="opcua")
    cmd = _make_command("setpoint-1")

    wrapped.write("setpoint-1", cmd)

    adapter.write.assert_called_once_with("setpoint-1", cmd)
    assert len(trace.spans) == 1
    span = trace.spans[0]
    assert span.name == "protocol.opcua.write"
    assert span.attributes["adapter_type"] == "opcua"
    assert span.attributes["target"] == "setpoint-1"
    assert span.attributes["operation"] == "write"
    assert span.ended is True


def test_write_exception_records_error_event_and_reraises() -> None:
    library_error = DeviceProtocolPortWriteError("bad register value")
    adapter = _make_mock_adapter(write_raises=library_error)
    trace = _RecordingTracePort()
    wrapped = OtelSpanWrappedDeviceProtocolPort(adapter, trace_port=trace, adapter_type="modbus")
    cmd = _make_command("hr-1")

    with pytest.raises(DeviceProtocolPortWriteError, match="bad register"):
        wrapped.write("hr-1", cmd)

    span = trace.spans[0]
    assert span.ended is True
    error_events = [e for e in span.events if e[0] == "error"]
    assert len(error_events) == 1
    _, error_attrs = error_events[0]
    assert error_attrs["exception.type"] == "DeviceProtocolPortWriteError"


# ---------------------------------------------------------------------------
# None-TracePort Pass-Through
# ---------------------------------------------------------------------------


def test_read_passes_through_when_trace_port_is_none() -> None:
    expected_point = _make_telemetry_point("t1")
    adapter = _make_mock_adapter(read_return=expected_point)
    wrapped = OtelSpanWrappedDeviceProtocolPort(adapter, trace_port=None, adapter_type="mqtt")

    result = wrapped.read("t1")

    assert result is expected_point
    adapter.read.assert_called_once_with("t1")


def test_write_passes_through_when_trace_port_is_none() -> None:
    adapter = _make_mock_adapter()
    wrapped = OtelSpanWrappedDeviceProtocolPort(adapter, trace_port=None, adapter_type="dnp3")
    cmd = _make_command("t1")

    wrapped.write("t1", cmd)

    adapter.write.assert_called_once_with("t1", cmd)


def test_read_exception_reraises_when_trace_port_is_none() -> None:
    library_error = DeviceProtocolPortReadError("read failed")
    adapter = _make_mock_adapter(read_raises=library_error)
    wrapped = OtelSpanWrappedDeviceProtocolPort(adapter, trace_port=None, adapter_type="iec61850")

    with pytest.raises(DeviceProtocolPortReadError, match="read failed"):
        wrapped.read("t1")


# ---------------------------------------------------------------------------
# Lifecycle Pass-Through
# ---------------------------------------------------------------------------


def test_start_passes_through_without_span() -> None:
    adapter = _make_mock_adapter()
    trace = _RecordingTracePort()
    wrapped = OtelSpanWrappedDeviceProtocolPort(adapter, trace_port=trace, adapter_type="mqtt")

    wrapped.start()

    adapter.start.assert_called_once()
    # Welle-6a-Convention: Lifecycle nicht im Hot-Path; kein Span.
    assert len(trace.spans) == 0


def test_stop_passes_through_without_span() -> None:
    adapter = _make_mock_adapter()
    trace = _RecordingTracePort()
    wrapped = OtelSpanWrappedDeviceProtocolPort(adapter, trace_port=trace, adapter_type="modbus")

    wrapped.stop()

    adapter.stop.assert_called_once()
    assert len(trace.spans) == 0


# ---------------------------------------------------------------------------
# Adapter-Robustheit (ADR 0024 §2.4)
# ---------------------------------------------------------------------------


def test_read_succeeds_when_start_span_raises() -> None:
    """Falls `TracePort.start_span` selbst eine Exception wirft
    (TracePort-Adapter-Bug), laeuft der Adapter-Call trotzdem
    durch — Best-Effort-Observability (ADR 0024 §2.4)."""
    expected_point = _make_telemetry_point("t1")
    adapter = _make_mock_adapter(read_return=expected_point)
    broken_trace = MagicMock()
    broken_trace.start_span = MagicMock(side_effect=RuntimeError("trace lib bug"))
    wrapped = OtelSpanWrappedDeviceProtocolPort(
        adapter, trace_port=broken_trace, adapter_type="dnp3"
    )

    result = wrapped.read("t1")

    # Adapter-Call ging trotz Trace-Bug durch.
    assert result is expected_point
    adapter.read.assert_called_once_with("t1")


def test_read_succeeds_when_end_span_raises() -> None:
    """Falls `TracePort.end_span` eine Exception wirft, wird
    der Adapter-Returnwert trotzdem zurueckgegeben — die
    Span-Cleanup-Exception ist Adapter-intern."""
    expected_point = _make_telemetry_point("t1")
    adapter = _make_mock_adapter(read_return=expected_point)
    semi_broken_trace = MagicMock()
    fake_context = SpanContext(trace_id="t", span_id="s", parent_span_id=None)
    semi_broken_trace.start_span = MagicMock(return_value=fake_context)
    semi_broken_trace.record_event = MagicMock()
    semi_broken_trace.end_span = MagicMock(side_effect=RuntimeError("end bug"))
    wrapped = OtelSpanWrappedDeviceProtocolPort(
        adapter, trace_port=semi_broken_trace, adapter_type="opcua"
    )

    result = wrapped.read("t1")

    assert result is expected_point
