"""Unit-Tests fuer den Composition-Root-Demo-Stack-Builder (ADR 0079 §2.5 Decision C).

Pinnt die T3-Inversion: der Default-In-Memory-Stack (Repository/Telemetry/Registry/
Alarm) wird vom Composition-Root instanziiert (`configure_demo_stack`), nicht mehr
im HTTP-Adapter (`app.py`). Der `app.py`-Default-Builder ist fail-closed, solange
kein Composition-Root registriert.
"""

from __future__ import annotations

import pytest

from grid_gym.adapters.driven.alarm_stream_inmemory import (
    AlarmHistoryBuffer,
    InMemoryAlarmStream,
)
from grid_gym.adapters.driven.persistence_inmemory import InMemoryRunRepository
from grid_gym.adapters.driven.telemetry_stream_inmemory import InMemoryTelemetryStream
from grid_gym.adapters.driving.http_api._tick_loop_registry import TickLoopRegistry
from grid_gym.adapters.driving.http_api.app import (
    _DemoStackBuilderNotRegisteredError,
    _raise_demo_stack_builder_unregistered,
    app,
)
from grid_gym.composition._demo_stack import configure_demo_stack


def _reset_app_state() -> None:
    """Starlette-internes State-Dict leeren (Muster Welle-5-Demo-Smoke F15)."""
    app.state._state.clear()


def test_configure_demo_stack_wires_in_memory_base_stack() -> None:
    """`configure_demo_stack` setzt Repository/Telemetry/Registry/Alarm auf
    `app.state` — verhaltensgleich zur vormaligen Adapter-internen Instanziierung."""
    _reset_app_state()
    try:
        configure_demo_stack(app)
        assert isinstance(app.state.run_repository, InMemoryRunRepository)
        assert isinstance(app.state.telemetry_stream, InMemoryTelemetryStream)
        assert isinstance(app.state.tick_loop_registry, TickLoopRegistry)
        assert isinstance(app.state.alarm_stream, InMemoryAlarmStream)
        assert isinstance(app.state.alarm_history_buffer, AlarmHistoryBuffer)
    finally:
        _reset_app_state()


def test_default_demo_stack_builder_is_fail_closed() -> None:
    """Der `app.py`-Default-Builder wirft fail-closed (App via reinem Adapter-
    Entrypoint statt `composition.asgi`)."""
    with pytest.raises(_DemoStackBuilderNotRegisteredError):
        _raise_demo_stack_builder_unregistered(app)
