"""M3-Welle-5-Tests fuer die TickLoop-Observability-Hooks
(ADR 0024 §2.6).

Pinnt:

- Default `log_port=None`/`metrics_port=None`/`trace_port=None`
  skippt alle Hooks (Welle-1..4-Tests bleiben kompatibel).
- Mit Null-Adaptern (`record_calls=False`-Default) sind die
  Hook-Aufrufe ueber `call_count` + `last_call` sichtbar
  (loest welle-5.md §7 R-2).
- TickLoop emittiert `tick_begin`/`tick_end` Logs pro Tick.
- TickLoop emittiert `gauge('event_queue_len', ...)` nach
  `scheduler.pop_due(...)`.
- TickLoop oeffnet `tick.cycle`-Span pro Tick.
- TickLoop wickelt `fault.inject`-Span um den Fault-Apply
  (Welle-1-Schritt-A2-Position, ADR 0022 §2.4).
- TickLoop wickelt `agent.tick`-Span pro Agent-Tick
  (Welle-3-Schritt-D2-Position, ADR 0023 §2.4).
- Span-Schachtelung: fault- + agent-Spans tragen
  `tick.cycle.span_id` als `parent_span_id`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Self

from grid_gym.adapters.driven.observability_null import (
    NullLogAdapter,
    NullMetricsAdapter,
    NullTraceAdapter,
)
from grid_gym.hexagon.core.agents import AgentMessageBus
from grid_gym.hexagon.core.devices._protocol import DeviceModel
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


class _RecordingFaultPort:
    """Inline-Stub: ein No-Op-FaultPort, der Hook-Aufrufe nur fuer
    Sichtbarkeit zaehlt (eigentliche Fault-Logik ist Welle-2-Material).
    """

    def __init__(self) -> None:
        self.calls = 0

    def apply_active_faults(
        self,
        devices: Sequence[object],
        context: DeviceTickContext,
    ) -> None:
        self.calls += 1


class _NullAgent:
    """Minimaler Agent fuer Welle-5-Hook-Test."""

    SNAPSHOT_VERSION: int = 1

    def __init__(self, agent_id: str) -> None:
        self._agent_id = agent_id

    @property
    def agent_id(self) -> str:
        return self._agent_id

    def set_run_id(self, run_id: str) -> None:
        return

    def tick(
        self,
        context: DeviceTickContext,
        bus: AgentMessageBus,
    ) -> Sequence[Command]:
        return ()

    def snapshot(self) -> Mapping[str, object]:
        return {"version": self.SNAPSHOT_VERSION, "agent_id": self._agent_id}

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        agent_id = state["agent_id"]
        assert isinstance(agent_id, str)
        return cls(agent_id=agent_id)


def _make_loop(
    *,
    devices: tuple[DeviceModel, ...] = (),
    fault_port: object | None = None,
    agents: tuple[_NullAgent, ...] = (),
    log_port: NullLogAdapter | None = None,
    metrics_port: NullMetricsAdapter | None = None,
    trace_port: NullTraceAdapter | None = None,
) -> TickLoop:
    return TickLoop(
        run_id="welle-5-obs-test",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=devices,
        fault_port=fault_port,  # type: ignore[arg-type]
        agents=agents,  # type: ignore[arg-type]
        log_port=log_port,
        metrics_port=metrics_port,
        trace_port=trace_port,
    )


# --- Default skip path -------------------------------------------------------


def test_default_no_observability_ports_skips_hooks() -> None:
    """ADR 0024 §2.6: keine Ports → kein Hook-Aufruf, kein Throw."""
    loop = _make_loop()
    result = loop.tick()
    assert result.tick == 0


# --- LogPort hooks -----------------------------------------------------------


def test_log_port_receives_tick_begin_and_tick_end_per_tick() -> None:
    log = NullLogAdapter(record_calls=True)
    loop = _make_loop(log_port=log)
    loop.tick()
    loop.tick()
    log_calls = list(log.call_records)
    # 2 ticks x 2 logs (begin + end) = 4 log calls
    assert len(log_calls) == 4
    event_ids = [r.kwargs["event_id"] for r in log_calls]
    assert event_ids == ["tick-0", "tick-0", "tick-1", "tick-1"]
    messages = [r.kwargs["message"] for r in log_calls]
    assert messages == ["tick_begin", "tick_end", "tick_begin", "tick_end"]


def test_log_port_log_carries_run_id_and_module() -> None:
    """ADR 0024 §2.2: LogPort.log bekommt `run_id` + `module` (Pflicht-
    Felder fuer `GG-OTEL-002` aus Architektur §15)."""
    log = NullLogAdapter()
    loop = _make_loop(log_port=log)
    loop.tick()
    last = log.last_call
    assert last is not None
    assert last.kwargs["run_id"] == "welle-5-obs-test"
    assert last.kwargs["module"] == "tick_loop"


# --- MetricsPort hooks -------------------------------------------------------


def test_metrics_port_emits_event_queue_len_gauge() -> None:
    """ADR 0024 §2.6: gauge('event_queue_len', ...) nach
    scheduler.pop_due."""
    metrics = NullMetricsAdapter(record_calls=True)
    loop = _make_loop(metrics_port=metrics)
    loop.tick()
    gauge_calls = [r for r in metrics.call_records if r.method == "gauge"]
    assert len(gauge_calls) == 1
    assert gauge_calls[0].kwargs["name"] == "event_queue_len"
    # Leerer Scheduler → 0.0
    value = gauge_calls[0].kwargs["value"]
    assert isinstance(value, float)
    assert int(value) == 0


def test_metrics_port_emits_tick_count_counter() -> None:
    """ADR 0024 §2.6: increment('tick_count') am Tick-Ende."""
    metrics = NullMetricsAdapter(record_calls=True)
    loop = _make_loop(metrics_port=metrics)
    loop.tick()
    loop.tick()
    increment_calls = [r for r in metrics.call_records if r.method == "increment"]
    assert len(increment_calls) == 2
    assert all(r.kwargs["name"] == "tick_count" for r in increment_calls)


# --- TracePort hooks ---------------------------------------------------------


def test_trace_port_opens_and_closes_tick_cycle_span() -> None:
    """ADR 0024 §2.6: `tick.cycle`-Span umfasst die Tick-Arbeit."""
    trace = NullTraceAdapter(record_calls=True)
    loop = _make_loop(trace_port=trace)
    loop.tick()
    starts = [r for r in trace.call_records if r.method == "start_span"]
    ends = [r for r in trace.call_records if r.method == "end_span"]
    assert len(starts) == 1
    assert starts[0].kwargs["name"] == "tick.cycle"
    assert len(ends) == 1


def test_trace_port_wraps_fault_inject_with_parent_tick_span() -> None:
    """ADR 0024 §2.6: fault.inject-Span hat tick.cycle als parent."""
    trace = NullTraceAdapter(record_calls=True)
    fault_port = _RecordingFaultPort()
    loop = _make_loop(trace_port=trace, fault_port=fault_port)
    loop.tick()
    assert fault_port.calls == 1
    starts = [r for r in trace.call_records if r.method == "start_span"]
    # zwei Spans: tick.cycle + fault.inject
    names = [r.kwargs["name"] for r in starts]
    assert names == ["tick.cycle", "fault.inject"]
    tick_span_ctx = starts[0].kwargs["returned"]
    fault_parent = starts[1].kwargs["parent"]
    # Welle-5-Review-Folge L-4: `==` statt `is` — SpanContext ist
    # frozen dataclass; ein `_CallTracker`-Refactor mit deepcopy oder
    # Pickle-Roundtrip wuerde sonst die Tests still brechen.
    assert fault_parent == tick_span_ctx


def test_trace_port_wraps_each_agent_tick_with_parent_tick_span() -> None:
    """ADR 0024 §2.6: pro Agent ein `agent.tick`-Span mit Tick-Parent."""
    trace = NullTraceAdapter(record_calls=True)
    agents = (_NullAgent("agent-a"), _NullAgent("agent-b"))
    loop = _make_loop(trace_port=trace, agents=agents)
    loop.tick()
    starts = [r for r in trace.call_records if r.method == "start_span"]
    names = [r.kwargs["name"] for r in starts]
    assert names == ["tick.cycle", "agent.tick", "agent.tick"]
    agent_ids = [r.kwargs["attributes"]["agent_id"] for r in starts[1:]]
    assert agent_ids == ["agent-a", "agent-b"]
    tick_span_ctx = starts[0].kwargs["returned"]
    # Welle-5-Review-Folge L-4: siehe oben (Equality statt Identitaet).
    for r in starts[1:]:
        assert r.kwargs["parent"] == tick_span_ctx


# --- Span balance ------------------------------------------------------------


def test_trace_port_starts_equal_ends_in_happy_path() -> None:
    """Jeder geoeffnete Span wird auch geschlossen."""
    trace = NullTraceAdapter(record_calls=True)
    fault_port = _RecordingFaultPort()
    agents = (_NullAgent("agent-1"),)
    loop = _make_loop(trace_port=trace, fault_port=fault_port, agents=agents)
    loop.tick()
    starts = sum(1 for r in trace.call_records if r.method == "start_span")
    ends = sum(1 for r in trace.call_records if r.method == "end_span")
    assert starts == ends == 3  # tick.cycle + fault.inject + agent.tick


# --- Skip granularitaet (port-spezifisch) -----------------------------------


def test_metrics_only_does_not_emit_logs_or_spans() -> None:
    """Granulare Verdrahtung: nur `metrics_port` injiziert →
    keine Log-/Trace-Aufrufe."""
    metrics = NullMetricsAdapter(record_calls=True)
    log = NullLogAdapter(record_calls=True)
    trace = NullTraceAdapter(record_calls=True)
    # Nur metrics; log und trace bleiben Standalone-Instanzen ohne
    # Verdrahtung, dienen nur als Reference-Beobachtung.
    loop = _make_loop(metrics_port=metrics)
    loop.tick()
    assert metrics.call_count > 0
    assert log.call_count == 0
    assert trace.call_count == 0
