"""End-to-End-Integration-Smoke fuer M5-Welle-6b (UI-Visualization:
Devices-API + Devices-Page + System-Page, Slice-Doc M5-welle-6b
Decisions 21/22).

Pinnt die produktive Welle-6b-Wiring-Composition:

1. `GET /runs/{run_id}/devices/state` (Decision 21; URL-Slot
   per C3-Realization-Note auf `/state`-Sub-Pfad gehoben, weil
   die natuerliche `/devices`-URL der UI-Page gehoert):
   - 404 bei nicht-existentem Run (GG-API-004-Envelope).
   - 200 mit allen 5 MVP-Devices + per-Typ Pflicht-State-Subset +
     `quality="valid"` initial (Pre-Tick-Fall).
   - Decimal-Werte als Strings (canonical_json-Konsistenz).
   - Worst-case-Quality-Aggregation: ein FAULT_INJECTED-
     TelemetryPoint im `_last_telemetry` → Device-quality wird
     `fault_injected`.

2. `GET /runs/{run_id}/devices` UI-Page (Decision 22; GG-UI-006):
   - 404 bei nicht-existentem Run.
   - 200 mit HTMX-Polling-Tabelle (poll-target
     `/runs/{run_id}/devices/state`) + Inline-JS-Render-Hook.

3. `GET /runs/{run_id}/system` UI-Page (Decision 22; GG-UI-008):
   - 404 bei nicht-existentem Run.
   - 200 mit Run-Status-Polling-Block + Service-Health-Polling-
     Block.
"""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driving.http_api._demo_scenario_setup import (
    _DEMO_RUN_ID,
)
from grid_gym.adapters.driving.http_api.app import _DEMO_SCENARIO_ENV_VAR, app
from grid_gym.hexagon.core.devices.battery.model import BatteryDevice
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint


_DEMO_SCENARIO_PATH: Path = (
    Path(__file__).resolve().parents[2] / "deploy" / "scenarios" / "gg-demo.yaml"
)


def _reset_app_state() -> None:
    """Welle-5-Review F15: dynamisches Reset ueber Starlette-internes
    `_state`-Dict (siehe test_m5_welle_5_demo_smoke)."""
    app.state._state.clear()


@pytest.fixture
def demo_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Welle-5-Lifespan-Pfad mit Welle-6b-Devices-Endpoint. Lifespan
    konfiguriert via `GRID_GYM_DEMO_SCENARIO_PATH` den vollen
    Demo-Stack inklusive TickLoopRegistry + 5 MVP-Geraete."""
    _reset_app_state()
    monkeypatch.setenv(_DEMO_SCENARIO_ENV_VAR, str(_DEMO_SCENARIO_PATH))
    with TestClient(app) as client:
        yield client
    _reset_app_state()


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/devices/state (Decision 21 JSON-Surface)
# ---------------------------------------------------------------------------


def test_get_devices_state_returns_404_for_unknown_run(demo_client: TestClient) -> None:
    """GG-API-004-Envelope: 404 mit `code=run_not_found` bei
    nicht-existentem Run."""
    response = demo_client.get("/runs/ghost-run-9999/devices/state")
    assert response.status_code == 404
    body = response.json()
    detail = body["detail"]
    assert detail["code"] == "run_not_found"
    assert detail["run_id"] == "ghost-run-9999"


def test_get_devices_returns_all_five_mvp_devices(demo_client: TestClient) -> None:
    """Decision 21: Demo-Scenario hat 5 MVP-Geraete; jeder Eintrag
    traegt `device_id` + `device_type` + `state` + `quality`."""
    response = demo_client.get(f"/runs/{_DEMO_RUN_ID}/devices/state")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == _DEMO_RUN_ID
    devices = body["devices"]
    assert len(devices) == 5
    by_type = {entry["device_type"]: entry for entry in devices}
    assert set(by_type) == {"battery", "pv", "load", "grid_connection", "smart_meter"}
    for entry in devices:
        assert "device_id" in entry
        assert "state" in entry
        assert entry["quality"] in {q.value for q in Quality}


def test_get_devices_battery_state_subset(demo_client: TestClient) -> None:
    """Decision 21 §3.1: Battery-State-Subset hat genau `soc_kwh`,
    `current_power_kw`, `cell_failure_active`. Decimals als Strings."""
    response = demo_client.get(f"/runs/{_DEMO_RUN_ID}/devices/state")
    devices = response.json()["devices"]
    battery_entry = next(e for e in devices if e["device_type"] == "battery")
    assert set(battery_entry["state"]) == {
        "soc_kwh",
        "current_power_kw",
        "cell_failure_active",
    }
    assert isinstance(battery_entry["state"]["soc_kwh"], str)
    assert isinstance(battery_entry["state"]["current_power_kw"], str)
    assert isinstance(battery_entry["state"]["cell_failure_active"], bool)
    # Pre-Tick-Fall: cell_failure_active=False (Demo-Scenario startet
    # ohne aktiven Fault).
    assert battery_entry["state"]["cell_failure_active"] is False


def test_get_devices_pv_load_state_subsets(demo_client: TestClient) -> None:
    """Decision 21 §3.1: PV + Load haben jeweils nur
    `current_power_kw` (als String)."""
    response = demo_client.get(f"/runs/{_DEMO_RUN_ID}/devices/state")
    devices = response.json()["devices"]
    for device_type in ("pv", "load"):
        entry = next(e for e in devices if e["device_type"] == device_type)
        assert set(entry["state"]) == {"current_power_kw"}
        assert isinstance(entry["state"]["current_power_kw"], str)


def test_get_devices_grid_connection_state_subset(demo_client: TestClient) -> None:
    """Decision 21 §3.1: GridConnection-State hat `current_power_kw`,
    `current_voltage_v`, `voltage_drop_active`."""
    response = demo_client.get(f"/runs/{_DEMO_RUN_ID}/devices/state")
    devices = response.json()["devices"]
    entry = next(e for e in devices if e["device_type"] == "grid_connection")
    assert set(entry["state"]) == {
        "current_power_kw",
        "current_voltage_v",
        "voltage_drop_active",
    }
    assert isinstance(entry["state"]["current_voltage_v"], str)
    assert isinstance(entry["state"]["voltage_drop_active"], bool)


def test_get_devices_smart_meter_has_empty_state(demo_client: TestClient) -> None:
    """Decision 21 §3.1: SmartMeter hat keinen eigenen Power-State
    (reiner Aggregator) und liefert `state={}`."""
    response = demo_client.get(f"/runs/{_DEMO_RUN_ID}/devices/state")
    devices = response.json()["devices"]
    entry = next(e for e in devices if e["device_type"] == "smart_meter")
    assert entry["state"] == {}


def test_get_devices_quality_aggregates_fault_injected(
    demo_client: TestClient,
) -> None:
    """Decision 21 Worst-case-Quality-Aggregation: ein einzelner
    `FAULT_INJECTED`-TelemetryPoint im `_last_telemetry`-Buffer eines
    Devices propagiert auf die device-level `quality`.

    Welle-6b-Smoke-Pragmatismus: kein MVP-Device emittiert aktuell
    `FAULT_INJECTED`-Telemetry (alle haengen an `Quality.VALID`).
    Wir injizieren das Quality-Marker direkt in den `_last_telemetry`-
    Buffer der Battery, damit der `_aggregate_quality`-Pfad des
    Endpoints exerciert wird ohne neue Device-Emission-Logik."""
    registry = app.state.tick_loop_registry
    tick_loop = registry.tick_loop_for(_DEMO_RUN_ID)
    assert tick_loop is not None
    battery = next(
        d
        for d in tick_loop._devices  # type: ignore[attr-defined]
        if isinstance(d, BatteryDevice)
    )
    fault_point = TelemetryPoint(
        run_id=_DEMO_RUN_ID,
        tick=0,
        simulation_time=0,
        device_id=battery.device_id,
        metric="power_kw",
        value=Decimal("0.000"),
        unit="kW",
        quality=Quality.FAULT_INJECTED,
        source="battery",
        sequence=0,
    )
    battery._last_telemetry = (fault_point,)  # type: ignore[attr-defined]
    response = demo_client.get(f"/runs/{_DEMO_RUN_ID}/devices/state")
    assert response.status_code == 200
    devices = response.json()["devices"]
    battery_entry = next(e for e in devices if e["device_type"] == "battery")
    assert battery_entry["quality"] == "fault_injected"


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/devices UI-Page (Decision 22; GG-UI-006)
# ---------------------------------------------------------------------------


def test_get_devices_page_returns_404_for_unknown_run(
    demo_client: TestClient,
) -> None:
    """Decision 22: UI-Page liefert 404 mit GG-API-004-Envelope bei
    nicht-existentem Run."""
    response = demo_client.get("/runs/ghost-run-9999/devices", headers={"accept": "text/html"})
    assert response.status_code == 404


def test_get_devices_page_renders_polling_table(demo_client: TestClient) -> None:
    """GG-UI-006: Page rendert HTMX-Polling-Tabelle (poll-target
    ist die JSON-State-Surface auf `/devices/state`) + Inline-JS-
    Render-Hook."""
    response = demo_client.get(f"/runs/{_DEMO_RUN_ID}/devices")
    assert response.status_code == 200
    html = response.text
    assert "Devices —" in html
    assert _DEMO_RUN_ID in html
    assert f'hx-get="/runs/{_DEMO_RUN_ID}/devices/state"' in html
    assert 'hx-trigger="every 1s"' in html
    assert 'id="devices-table"' in html


def test_get_devices_page_partial_for_htmx_request(demo_client: TestClient) -> None:
    """Decision 22: HX-Request-Header → Partial-Content (kein
    <base> Layout)."""
    response = demo_client.get(
        f"/runs/{_DEMO_RUN_ID}/devices",
        headers={"hx-request": "true"},
    )
    assert response.status_code == 200
    assert "<html" not in response.text.lower()
    assert 'id="devices-table"' in response.text


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/system UI-Page (Decision 22; GG-UI-008)
# ---------------------------------------------------------------------------


def test_get_system_page_returns_404_for_unknown_run(
    demo_client: TestClient,
) -> None:
    """Decision 22: System-Page liefert 404 bei nicht-existentem
    Run."""
    response = demo_client.get("/runs/ghost-run-9999/system")
    assert response.status_code == 404


def test_get_system_page_renders_status_and_health_blocks(
    demo_client: TestClient,
) -> None:
    """GG-UI-008: System-Page rendert beide Polling-Bloecke
    (Run-Status auf `/status` 1s; Service-Health auf `/health` 5s)."""
    response = demo_client.get(f"/runs/{_DEMO_RUN_ID}/system")
    assert response.status_code == 200
    html = response.text
    assert "System Status —" in html
    assert _DEMO_RUN_ID in html
    # Run-Status-Polling
    assert f'hx-get="/runs/{_DEMO_RUN_ID}/status"' in html
    assert 'hx-trigger="every 1s"' in html
    assert 'id="system-run-status"' in html
    # Service-Health-Polling
    assert 'hx-get="/health"' in html
    assert 'hx-trigger="every 5s"' in html
    assert 'id="system-service-health"' in html


def test_get_system_page_partial_for_htmx_request(demo_client: TestClient) -> None:
    """Decision 22: HX-Request-Header → Partial-Content."""
    response = demo_client.get(
        f"/runs/{_DEMO_RUN_ID}/system",
        headers={"hx-request": "true"},
    )
    assert response.status_code == 200
    assert "<html" not in response.text.lower()
    assert 'id="system-run-status"' in response.text
