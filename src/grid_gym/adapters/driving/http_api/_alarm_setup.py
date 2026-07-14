"""Welle-4b-Alarm-Setup: setzt `AlarmStreamPort` + `AlarmHistoryBuffer`
auf `app.state` fuer die laufende App (M5 Welle 4b, ADR 0040
Decision 17).

Ausgelagert aus `app.py`, damit der `AC-NO-GOD-UTILS`-Contract
(max 5 public top-level functions pro Modul) in `app.py` nicht
gerissen wird. Pattern analog Welle-4a-`_demo_setup.py`.
"""

from __future__ import annotations

from grid_gym.adapters.driving.http_api.app import app
from grid_gym.hexagon.ports.driven.alarm_history import AlarmHistoryPort
from grid_gym.hexagon.ports.driving.alarm_stream import AlarmStreamPort


def configure_alarm_stream(
    stream: AlarmStreamPort,
    history_buffer: AlarmHistoryPort,
) -> None:
    """Setzt den `AlarmStreamPort` + den `AlarmHistoryBuffer` fuer
    die laufende App (M5 Welle 4b, ADR 0040 Decision 17).

    Aufrufer (uvicorn-Entry, Tests, `configure_demo_run`)
    injizieren beide Komponenten vor dem ersten Request. Die
    REST- und WS-Endpunkte (`GET /runs/{id}/alarms` +
    `WS /runs/{id}/alarms-stream`) sowie die UI-Page lesen aus
    `app.state.alarm_stream` und `app.state.alarm_history_buffer`.
    """
    app.state.alarm_stream = stream
    app.state.alarm_history_buffer = history_buffer
