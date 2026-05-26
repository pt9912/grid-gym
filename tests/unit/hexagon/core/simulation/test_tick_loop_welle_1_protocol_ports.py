"""M4-Welle-1-Tests fuer den TickLoop-DeviceProtocolPort-
Lifecycle (ADR 0030 §2.2).

Pinnt:

- `start_protocol_ports()` startet die Ports in FIFO-Reihenfolge.
- `stop_protocol_ports()` stoppt die Ports in LIFO-Reihenfolge.
- Beide sind No-op bei `protocol_ports=None` (Default).
- Beide sind No-op nach erfolglosem Start (Idempotenz).
- Partial-Start-Failure: bereits gestartete Ports werden in
  LIFO mit `stop()` abgebaut; Original-Exception propagiert;
  erste Cleanup-Exception haengt als `__context__` an die
  Original-Start-Exception (Python-Auto-Context wird vorher
  gebrochen).
- `stop_protocol_ports()` ist nach erfolgreichem
  `start_protocol_ports()` einmal aktiv, beim zweiten Aufruf
  No-op (Idempotenz).
- Caller-Scope-Pattern aus ADR 0030 §2.2 funktioniert
  (try/finally-Block laeuft sauber durch).
"""

from __future__ import annotations

import pytest

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPort,
    DeviceProtocolPortStartError,
    DeviceProtocolPortStopError,
)
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


class _RecordingPort:
    """Inline-Stub: zeichnet Aufruf-Reihenfolge ueber einen
    geteilten Recorder auf."""

    def __init__(self, label: str, recorder: list[str]) -> None:
        self._label = label
        self._recorder = recorder

    def start(self) -> None:
        self._recorder.append(f"start:{self._label}")

    def stop(self) -> None:
        self._recorder.append(f"stop:{self._label}")

    def read(self, target: str) -> None:
        return None

    def write(self, target: str, command: Command) -> None:
        return None


class _StartFailingPort:
    """Stub: wirft beim ersten `start()`-Aufruf eine
    `DeviceProtocolPortStartError`."""

    def __init__(self, label: str, recorder: list[str]) -> None:
        self._label = label
        self._recorder = recorder

    def start(self) -> None:
        self._recorder.append(f"start-fail:{self._label}")
        raise DeviceProtocolPortStartError(f"start failed in {self._label}")

    def stop(self) -> None:
        self._recorder.append(f"stop:{self._label}")

    def read(self, target: str) -> None:
        return None

    def write(self, target: str, command: Command) -> None:
        return None


class _StopFailingPort:
    """Stub: `start()` erfolgreich, `stop()` wirft."""

    def __init__(self, label: str, recorder: list[str]) -> None:
        self._label = label
        self._recorder = recorder

    def start(self) -> None:
        self._recorder.append(f"start:{self._label}")

    def stop(self) -> None:
        self._recorder.append(f"stop-fail:{self._label}")
        raise DeviceProtocolPortStopError(f"stop failed in {self._label}")

    def read(self, target: str) -> None:
        return None

    def write(self, target: str, command: Command) -> None:
        return None


def _make_loop(
    *,
    protocol_ports: tuple[DeviceProtocolPort, ...] | None = None,
) -> TickLoop:
    return TickLoop(
        run_id="welle-1-protocol-port-test",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        protocol_ports=protocol_ports,
    )


# ---------------------------------------------------------------------------
# None-Default-Skip (Replay-Mode-Pfad)
# ---------------------------------------------------------------------------


def test_start_protocol_ports_is_no_op_when_none() -> None:
    """ADR 0030 §2.2: `protocol_ports=None` skippt den Lifecycle
    vollstaendig (Replay-Mode-Pfad)."""
    loop = _make_loop(protocol_ports=None)
    # Sollte ohne Exception durchlaufen.
    loop.start_protocol_ports()
    loop.stop_protocol_ports()


def test_default_kwarg_is_none() -> None:
    """`protocol_ports`-Default ist `None` (Pattern analog
    `fault_port`/`agent_bus`/`log_port`-Defaults)."""
    loop = TickLoop(
        run_id="default-test",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
    )
    # Ohne expliziten Kwarg ist der Lifecycle No-op.
    loop.start_protocol_ports()
    loop.stop_protocol_ports()


# ---------------------------------------------------------------------------
# Erfolgs-Pfad: FIFO start, LIFO stop
# ---------------------------------------------------------------------------


def test_start_protocol_ports_runs_fifo() -> None:
    """ADR 0030 §2.2: `start()` in FIFO-Reihenfolge (Tuple-Index
    aufsteigend)."""
    recorder: list[str] = []
    ports = (
        _RecordingPort("a", recorder),
        _RecordingPort("b", recorder),
        _RecordingPort("c", recorder),
    )
    loop = _make_loop(protocol_ports=ports)
    loop.start_protocol_ports()
    assert recorder == ["start:a", "start:b", "start:c"]


def test_stop_protocol_ports_runs_lifo() -> None:
    """ADR 0030 §2.2: `stop()` in LIFO-Reihenfolge (Tuple-Index
    absteigend) — falls Adapter N auf Ressourcen von N-1
    angewiesen ist, wird er vor N-1 abgebaut."""
    recorder: list[str] = []
    ports = (
        _RecordingPort("a", recorder),
        _RecordingPort("b", recorder),
        _RecordingPort("c", recorder),
    )
    loop = _make_loop(protocol_ports=ports)
    loop.start_protocol_ports()
    recorder.clear()
    loop.stop_protocol_ports()
    assert recorder == ["stop:c", "stop:b", "stop:a"]


def test_caller_scope_pattern_try_finally() -> None:
    """ADR 0030 §2.2: das Caller-Scope-Pattern funktioniert."""
    recorder: list[str] = []
    ports = (_RecordingPort("a", recorder), _RecordingPort("b", recorder))
    loop = _make_loop(protocol_ports=ports)
    loop.start_protocol_ports()
    try:
        loop.tick()
        recorder.append("tick-done")
    finally:
        loop.stop_protocol_ports()
    assert recorder == [
        "start:a",
        "start:b",
        "tick-done",
        "stop:b",
        "stop:a",
    ]


# ---------------------------------------------------------------------------
# Idempotenz: stop() darf doppelt gerufen werden
# ---------------------------------------------------------------------------


def test_stop_protocol_ports_is_idempotent_after_success() -> None:
    """ADR 0030 §2.2: zweiter `stop_protocol_ports()`-Aufruf ist
    No-op."""
    recorder: list[str] = []
    ports = (_RecordingPort("a", recorder),)
    loop = _make_loop(protocol_ports=ports)
    loop.start_protocol_ports()
    loop.stop_protocol_ports()
    recorder.clear()
    loop.stop_protocol_ports()
    assert recorder == []


def test_stop_protocol_ports_is_idempotent_without_prior_start() -> None:
    """ADR 0030 §2.2: `stop_protocol_ports()` ohne
    vorherigen `start_protocol_ports()` ist No-op."""
    recorder: list[str] = []
    ports = (_RecordingPort("a", recorder),)
    loop = _make_loop(protocol_ports=ports)
    loop.stop_protocol_ports()
    assert recorder == []


# ---------------------------------------------------------------------------
# Partial-Start-Failure-Vertrag (ADR 0030 §2.2)
# ---------------------------------------------------------------------------


def test_partial_start_failure_cleans_up_in_lifo() -> None:
    """ADR 0030 §2.2: wirft `protocol_ports[1].start()` eine
    Exception, wird `protocol_ports[0].stop()` als Best-Effort-
    Cleanup in LIFO gerufen."""
    recorder: list[str] = []
    ports = (
        _RecordingPort("a", recorder),
        _StartFailingPort("b", recorder),
        _RecordingPort("c", recorder),
    )
    loop = _make_loop(protocol_ports=ports)
    with pytest.raises(DeviceProtocolPortStartError):
        loop.start_protocol_ports()
    # `start:a` OK, `start-fail:b` wirft, Cleanup ruft `stop:a`.
    # `start:c` wird gar nicht gerufen.
    assert recorder == ["start:a", "start-fail:b", "stop:a"]


def test_partial_start_failure_at_index_zero_does_no_cleanup() -> None:
    """Wenn der erste Port direkt failt, gibt es nichts zu
    cleanen."""
    recorder: list[str] = []
    ports = (
        _StartFailingPort("a", recorder),
        _RecordingPort("b", recorder),
    )
    loop = _make_loop(protocol_ports=ports)
    with pytest.raises(DeviceProtocolPortStartError):
        loop.start_protocol_ports()
    assert recorder == ["start-fail:a"]


def test_partial_start_failure_clears_started_indices() -> None:
    """Nach Partial-Start-Failure ist `stop_protocol_ports()`
    No-op (Cleanup ist schon in `start_protocol_ports()` gelaufen,
    interner Tracking-Buffer ist geleert)."""
    recorder: list[str] = []
    ports = (
        _RecordingPort("a", recorder),
        _StartFailingPort("b", recorder),
    )
    loop = _make_loop(protocol_ports=ports)
    with pytest.raises(DeviceProtocolPortStartError):
        loop.start_protocol_ports()
    recorder.clear()
    loop.stop_protocol_ports()
    assert recorder == []


def test_partial_start_failure_with_cleanup_exception_chains_context() -> None:
    """ADR 0030 §2.2: wirft die Cleanup-Schleife selbst eine
    Exception (in einem `stop()`), wird die erste Cleanup-
    Exception als `__context__` an die Original-Start-Exception
    gehaengt. Python-Auto-Context wird vorher gebrochen, um
    Zyklen zu vermeiden."""
    recorder: list[str] = []
    ports = (
        _StopFailingPort("a", recorder),
        _StartFailingPort("b", recorder),
    )
    loop = _make_loop(protocol_ports=ports)
    with pytest.raises(DeviceProtocolPortStartError) as exc_info:
        loop.start_protocol_ports()
    # Order: start:a OK, start-fail:b wirft, Cleanup stop-fail:a wirft.
    assert recorder == ["start:a", "start-fail:b", "stop-fail:a"]
    # Original-Start-Exception hat die Cleanup-Stop-Exception als
    # __context__ (ADR-konform; Auto-Context wurde gebrochen, kein
    # Zyklus).
    assert isinstance(exc_info.value.__context__, DeviceProtocolPortStopError)
    # Die Cleanup-Stop-Exception darf keinen __context__ mehr haben
    # (sonst waere es ein Zyklus zurueck zur Start-Exception).
    assert exc_info.value.__context__.__context__ is None
