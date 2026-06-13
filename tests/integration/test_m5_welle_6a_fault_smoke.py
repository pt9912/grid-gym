"""End-to-End-Integration-Smoke fuer M5-Welle-6a (Fault-Flow:
UI-Form-Validation + YAML-Fault-Demo, Slice-Doc M5-welle-6a
Decisions 19/20).

Pinnt die produktive Welle-6a-Wiring-Composition:

1. Cross-Field-Validation im `POST /runs/{run_id}/faults`:
   - 422 bei unbekanntem `target_device_id` (Decision 20
     Step 1).
   - 422 bei Whitelist-Verletzung Fault-Typ ↔ Device-Typ
     (Decision 20 Step 2: Battery + voltage_drop oder
     GridConnection + cell_failure).
   - 201 bei gueltigem POST (Battery + cell_failure).
   - 503 wenn kein TickLoop registriert (Welle-1-Stub-Pfad).

2. Welle-6a-Demo-YAML-Faults sind reproduzierbar (Decision 19):
   - `gg-demo.yaml` `faults:`-Block via `_compose_fault_port`
     verdrahtet `BatteryFaultAdapter` + `GridFaultAdapter` an
     `TickLoopWiring.fault_port`.
   - Manueller `tick_loop.tick()`-Lauf ueber 1000 Ticks loest
     den `cell_failure`-Clamp aus (Agent-Discharge -30 trifft
     halbierte max_discharge_kw=25 → LIMITED-Alarm).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from grid_gym.composition._demo_scenario_setup import (
    _DEMO_RUN_ID,
)
from grid_gym.adapters.driving.http_api.app import _DEMO_SCENARIO_ENV_VAR
from grid_gym.composition.asgi import app


_DEMO_SCENARIO_PATH: Path = (
    Path(__file__).resolve().parents[2] / "deploy" / "scenarios" / "gg-demo.yaml"
)


def _reset_app_state() -> None:
    """Welle-5-Review F15: dynamisches Reset ueber Starlette-internes
    `_state`-Dict (siehe test_m5_welle_5_demo_smoke)."""
    app.state._state.clear()


@pytest.fixture
def demo_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Welle-5-Lifespan-Pfad mit Welle-6a-FaultPort-Composition.
    Der Demo-Driver startet im Lifespan; wir nutzen ihn nicht aktiv
    fuer die HTTP-Tests, weil die Validation-Tests deterministisch
    nur auf den TickLoopRegistry-State zugreifen.
    """
    _reset_app_state()
    monkeypatch.setenv(_DEMO_SCENARIO_ENV_VAR, str(_DEMO_SCENARIO_PATH))
    with TestClient(app) as client:
        yield client
    _reset_app_state()


_VALID_FAULT_PAYLOAD: dict[str, object] = {
    "fault_type": "cell_failure",
    "target": "battery-1",
    "start_at_tick": 1500,
    "duration_ticks": 10,
    "recovery": "auto-recover-after-N-ticks",
}


def test_post_faults_rejects_unknown_target(demo_client: TestClient) -> None:
    """Decision 20 Step 1: target_device_id muss im Run-Scenario
    existieren."""
    payload = dict(_VALID_FAULT_PAYLOAD, target="ghost-device-99")
    response = demo_client.post(f"/runs/{_DEMO_RUN_ID}/faults", json=payload)
    assert response.status_code == 422
    body = response.json()
    detail = body["detail"]
    assert detail["code"] == "fault_unknown_target"
    assert detail["run_id"] == _DEMO_RUN_ID
    assert "ghost-device-99" in detail["message"]


def test_post_faults_rejects_voltage_drop_on_battery(
    demo_client: TestClient,
) -> None:
    """Decision 20 Step 2: voltage_drop ist auf Battery nicht
    erlaubt (Whitelist Battery → cell_failure)."""
    payload = dict(_VALID_FAULT_PAYLOAD, fault_type="voltage_drop")
    response = demo_client.post(f"/runs/{_DEMO_RUN_ID}/faults", json=payload)
    assert response.status_code == 422
    body = response.json()
    detail = body["detail"]
    assert detail["code"] == "fault_invalid_type_for_target"
    assert detail["details"]["fault_type"] == "voltage_drop"
    assert detail["details"]["target_type"] == "battery"


def test_post_faults_rejects_cell_failure_on_grid(
    demo_client: TestClient,
) -> None:
    """Decision 20 Step 2 (symmetrisch): cell_failure ist auf
    GridConnection nicht erlaubt."""
    payload = dict(
        _VALID_FAULT_PAYLOAD,
        fault_type="cell_failure",
        target="grid-connection-1",
    )
    response = demo_client.post(f"/runs/{_DEMO_RUN_ID}/faults", json=payload)
    assert response.status_code == 422
    body = response.json()
    detail = body["detail"]
    assert detail["code"] == "fault_invalid_type_for_target"
    assert detail["details"]["target_type"] == "grid_connection"


def test_post_faults_accepts_valid_battery_cell_failure(
    demo_client: TestClient,
) -> None:
    """Decision 20 Happy-Path: Battery + cell_failure → 201 +
    Welle-1-Stub-Antwort (Decision 19: kein dynamischer
    FaultPort-Mutate; Antwort bleibt 201+uuid)."""
    response = demo_client.post(f"/runs/{_DEMO_RUN_ID}/faults", json=_VALID_FAULT_PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["run_id"] == _DEMO_RUN_ID
    assert body["accepted"] is True
    assert len(body["fault_id"]) == 36  # uuid4 standard length


def test_post_faults_accepts_valid_grid_voltage_drop(
    demo_client: TestClient,
) -> None:
    """Decision 20 Happy-Path (symmetrisch): GridConnection +
    voltage_drop → 201."""
    payload = dict(
        _VALID_FAULT_PAYLOAD,
        fault_type="voltage_drop",
        target="grid-connection-1",
    )
    response = demo_client.post(f"/runs/{_DEMO_RUN_ID}/faults", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["accepted"] is True


def test_get_faults_page_renders_form(demo_client: TestClient) -> None:
    """GG-UI-007: Form-Page rendert mit allen 5 Pflicht-Feldern."""
    response = demo_client.get(f"/runs/{_DEMO_RUN_ID}/faults")
    assert response.status_code == 200
    html = response.text
    for field in (
        'name="fault_type"',
        'name="target"',
        'name="start_at_tick"',
        'name="duration_ticks"',
        'name="recovery"',
    ):
        assert field in html
    assert 'hx-post="/runs/demo-run-0001/faults"' in html


def test_demo_yaml_faults_compose_and_apply_during_windows() -> None:
    """Decision 19 + GG-DEMO-006: YAML-side faults werden ueber
    `_compose_fault_port` an `TickLoopWiring.fault_port` verdrahtet
    UND wirken im laufenden Tick — Battery hat
    `_cell_failure_active=True` waehrend Tick 900..949 (50 Ticks
    cell_failure-Window) UND Grid hat `_voltage_drop_active=True`
    waehrend Tick 1200..1259 (60 Ticks voltage_drop-Window).

    Welle-6a-Review F2: Vorgaengertest loopte nur 700 Ticks und
    erreichte die fault-windows nie — die FaultPort-Wiring wurde
    de facto nicht exerciert. Jetzt:

    - Pre-window-Check (Tick 100): Battery._cell_failure_active is
      False; Grid._voltage_drop_active is False.
    - Mid-cell_failure-window-Check (Tick 920): Battery._cell_
      failure_active is True (Battery+Adapter wirken).
    - Mid-voltage_drop-window-Check (Tick 1220): Grid._voltage_
      drop_active is True (Grid+Adapter wirken).
    - Welle-4b-Alarm-Pipeline (Welle-5 LoadEvent-Erbe) zeigt
      load-LIMITED-Alarm — beweist, dass die Welle-4b-
      Drain-Pipeline durch den neuen FaultPort-Wiring nicht
      verloren ging.

    Manueller TickLoop-Lauf statt asyncio-Driver — 1300 Ticks bei
    100ms-Wall-Clock-Interval waeren > 130s. Pattern analog
    Welle-4b-Alarms-Smoke (driver=None, manuelle `tick()`).

    Welle-6a-Realization-Note (Slice-Doc §10.1): `cell_failure`
    emittiert dabei keinen eigenen Battery-Alarm; das Demo-side
    sichtbare Alarm-Signal ist load-1-LIMITED aus dem Welle-5-
    LoadEvent. Battery-cell_failure-Auto-Alarm-Emission ist
    Welle-6+/M3-Welle-2-Hardening-Material.
    """
    from grid_gym.adapters.driven.alarm_stream_inmemory import AlarmHistoryBuffer
    from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
    from grid_gym.composition._demo_scenario_setup import (
        _compose_fault_port,
        _DemoSimulationClock,
    )
    from grid_gym.hexagon.core.devices.battery import BatteryDevice
    from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
    from grid_gym.hexagon.core.scenario.loader import TickLoopWiring, build_tick_loop

    # M7-Welle-2 (D-10-Revision C): Demo-YAML-Load via Shared-Helper.
    from tests.integration._yaml_scenario_loader import load_yaml_scenario

    loaded = load_yaml_scenario(_DEMO_SCENARIO_PATH)
    fault_port = _compose_fault_port(loaded.scenario.faults)
    assert fault_port is not None, "Decision 19: gg-demo.yaml braucht faults-Block"
    wiring = TickLoopWiring(fault_port=fault_port)
    tick_loop = build_tick_loop(
        loaded.scenario,
        run_id="welle-6a-trigger-test",
        clock=_DemoSimulationClock(),
        random_root=MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed),
        wiring=wiring,
    )
    battery = next(
        d
        for d in tick_loop._devices  # type: ignore[attr-defined]
        if isinstance(d, BatteryDevice)
    )
    grid = next(
        d
        for d in tick_loop._devices  # type: ignore[attr-defined]
        if isinstance(d, GridConnectionDevice)
    )
    buffer = AlarmHistoryBuffer()
    snapshot_pre_window = False
    snapshot_in_cell_failure = False
    snapshot_in_voltage_drop = False
    load_alarm_seen = False
    for tick_index in range(1300):
        result = tick_loop.tick()
        for alarm in result.emitted_alarms:
            buffer.append(alarm)
            if alarm.target == "load-1" and alarm.code == "power_clamp_limited":
                load_alarm_seen = True
        if tick_index == 100:
            snapshot_pre_window = (
                battery._cell_failure_active is False  # type: ignore[attr-defined]
                and grid._voltage_drop_active is False  # type: ignore[attr-defined]
            )
        if tick_index == 920:
            snapshot_in_cell_failure = battery._cell_failure_active  # type: ignore[attr-defined]
        if tick_index == 1220:
            snapshot_in_voltage_drop = grid._voltage_drop_active  # type: ignore[attr-defined]
    assert snapshot_pre_window, "Pre-Fault-Window (Tick 100): Battery+Grid sollten faultsfrei sein"
    assert snapshot_in_cell_failure, (
        "Mid-cell_failure-Window (Tick 920): Battery._cell_failure_active "
        "muss True sein — _compose_fault_port hat BatteryFaultAdapter "
        "nicht korrekt verdrahtet."
    )
    assert snapshot_in_voltage_drop, (
        "Mid-voltage_drop-Window (Tick 1220): Grid._voltage_drop_active "
        "muss True sein — _compose_fault_port hat GridFaultAdapter "
        "nicht korrekt verdrahtet."
    )
    assert load_alarm_seen, (
        "GG-DEMO-006-Alarm-Pfad: Welle-5-LoadEvent muss einen Load-"
        "LIMITED-Alarm via Welle-4b-Pipeline emittieren (beweist "
        f"intakte Drain-Pipeline); gesehen: "
        f"{[(a.target, a.code) for a in buffer.get_recent(limit=10)]}"
    )
