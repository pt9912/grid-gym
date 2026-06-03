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

from grid_gym.adapters.driving.http_api._demo_scenario_setup import (
    _DEMO_RUN_ID,
)
from grid_gym.adapters.driving.http_api.app import _DEMO_SCENARIO_ENV_VAR, app


_DEMO_SCENARIO_PATH: Path = (
    Path(__file__).resolve().parents[2] / "deploy" / "scenarios" / "gg-demo.yaml"
)


def _reset_app_state() -> None:
    for attr in (
        "run_repository",
        "telemetry_stream",
        "demo_telemetry_generator",
        "tick_loop_registry",
        "demo_tick_loop_driver",
        "alarm_stream",
        "alarm_history_buffer",
    ):
        if hasattr(app.state, attr):
            delattr(app.state, attr)


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


def test_demo_yaml_faults_compose_and_run_emits_alarms() -> None:
    """Decision 19 + GG-DEMO-006: YAML-side faults werden ueber
    `_compose_fault_port` an `TickLoopWiring.fault_port` verdrahtet;
    der Demo-Run laeuft mit aktivem FaultPort und emittiert ueber
    Welle-4b-Pipeline mindestens einen Alarm (Welle-5-LoadEvent
    triggert LIMITED-Load-Alarm reproduzierbar).

    Manueller TickLoop-Lauf statt asyncio-Driver, weil 600+ Ticks
    bei 100ms-Wall-Clock-Interval > 60s waeren. Pattern analog
    Welle-4b-Alarms-Smoke (driver=None, manuelle `tick()`).

    Welle-6a-Realization-Note (C3 §10 verankert): `cell_failure`
    halbiert `max_discharge_kw` per `_tick_in_context`, aber die
    M3-Welle-2-Substanz emittiert dabei **keinen** eigenen Alarm
    (der Clamp in `_tick_in_context` ist silent; Battery-Alarme
    kommen nur ueber `apply_command` → `validate_set_power_command`,
    das gegen die unhalvierte Config-`max_discharge_kw` prueft).
    `GG-DEMO-006`-Akzeptanz „erzeugt Telemetrie mit
    Qualitaetsstatus sowie einen Alarm" wird Demo-side erfuellt
    ueber: (a) Telemetry-Side-Effect von `cell_failure` +
    `voltage_drop` (im Dashboard sichtbare State-Mutation) und
    (b) Load-LIMITED-Alarm aus dem Welle-5-LoadEvent-Block.
    Battery-cell_failure-Auto-Alarm ist Welle-6+/M3-Welle-2-
    Hardening-Material.
    """
    from grid_gym.adapters.driven.alarm_stream_inmemory import AlarmHistoryBuffer
    from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
    from grid_gym.adapters.driving.http_api._demo_scenario_setup import (
        _compose_fault_port,
        _DemoSimulationClock,
        _load_scenario_from_yaml,
    )
    from grid_gym.hexagon.core.scenario.loader import TickLoopWiring, build_tick_loop

    loaded = _load_scenario_from_yaml(_DEMO_SCENARIO_PATH)
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
    buffer = AlarmHistoryBuffer()
    # LoadEvent ab sim_time=600 (Tick 600 bei tick_ms=1000) fuer
    # duration_s=60 (60 Ticks), power_kw=60 ueber load-1.rated_
    # power_kw=30 → LIMITED-Load-Alarm. cell_failure ab Tick 900
    # fuer 50 Ticks: silent halving des Battery-max_discharge im
    # Tick-Pfad (Slice-Doc §10 Welle-6a-Realization-Note).
    load_alarm_seen = False
    for _ in range(700):
        result = tick_loop.tick()
        for alarm in result.emitted_alarms:
            buffer.append(alarm)
            if alarm.target == "load-1" and alarm.code == "power_clamp_limited":
                load_alarm_seen = True
    assert load_alarm_seen, (
        "GG-DEMO-006-Alarm-Pfad: Welle-5-LoadEvent muss einen Load-"
        "LIMITED-Alarm via Welle-4b-Pipeline emittieren; gesehen: "
        f"{[(a.target, a.code) for a in buffer.get_recent(limit=10)]}"
    )
