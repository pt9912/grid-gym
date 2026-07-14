"""Default-In-Memory-Demo-Stack-Builder (Composition Root, ADR 0079 §2.5 Decision C).

Instanziiert die driven-In-Memory-Adapter (`InMemoryRunRepository` /
`InMemoryTelemetryStream` / `InMemoryAlarmStream` + `AlarmHistoryBuffer`) und den
`TickLoopRegistry` und verdrahtet sie ueber die `app.py`-`configure_*`-Naht auf
`app.state`. Vorher lag diese Instanziierung im HTTP-Adapter (`app.py`-Lifespan-
env-Branch) — ein Adapter->driven-Adapter-Import, den a-checks `lateral-adapter`-Regel
flaggt (ADR 0079 §2.1). Der Composition-Root darf driven-Adapter kennen.

`app.py` ruft den hier registrierten Builder ueber `_demo_stack_builder(app_)`; ist
kein Builder registriert (App via reinem Adapter-Entrypoint), faellt der env-Branch
fail-closed (ADR 0079 §2.5, Muster `_register_scenario_configurator`).
"""

from __future__ import annotations

from fastapi import FastAPI

from grid_gym.adapters.driven.alarm_stream_inmemory import (
    AlarmHistoryBuffer,
    InMemoryAlarmStream,
)
from grid_gym.adapters.driven.persistence_inmemory import InMemoryRunRepository
from grid_gym.adapters.driven.telemetry_stream_inmemory import InMemoryTelemetryStream
from grid_gym.adapters.driving.http_api._tick_loop_registry import TickLoopRegistry
from grid_gym.adapters.driving.http_api.app import (
    configure_run_repository,
    configure_telemetry_stream,
    configure_tick_loop_registry,
)


def configure_demo_stack(app_: FastAPI) -> None:
    """Instanziiert + verdrahtet den Default-In-Memory-Demo-Stack auf `app_.state`
    (ADR 0079 §2.5 Decision C).

    Wird vom `app.py`-Lifespan-env-Branch **einmal** (F9-Sentinel-geschuetzt) vor
    dem Scenario-Konfigurator gerufen. Komponenten + Reihenfolge spiegeln exakt die
    vorherige Adapter-interne Instanziierung (verhaltensgleich): Repository/Telemetry/
    Registry ueber die `app.py`-`configure_*`-Naht (Singleton), Alarm-Stream +
    History-Buffer direkt auf `app_.state` (wie zuvor in `app.py`).
    """
    configure_run_repository(InMemoryRunRepository())
    configure_telemetry_stream(InMemoryTelemetryStream())
    configure_tick_loop_registry(TickLoopRegistry())
    app_.state.alarm_stream = InMemoryAlarmStream()
    app_.state.alarm_history_buffer = AlarmHistoryBuffer()
