"""Pin fuer `build_run_driver` (Multi-Run-Execution S3, ADR 0069 §2.4).

Baut aus einem kanonisierten Scenario einen per-Run-`DemoTickLoopDriver` —
ungestartet; der Aufrufer (`POST /runs/{id}/start`) registriert ihn.
"""

from __future__ import annotations

from grid_gym.adapters.driven.persistence_inmemory import InMemoryRunRepository
from grid_gym.adapters.driving.http_api._tick_loop_driver import DemoTickLoopDriver
from grid_gym.composition._demo_scenario_setup import build_run_driver
from grid_gym.hexagon.core.domain.scenario import Scenario
from grid_gym.hexagon.core.scenario.loader import load_scenario
from grid_gym.scenario_yaml import coerce_scenario_mapping


def _scenario() -> Scenario:
    """Baubares Minimal-Scenario: `grid_connection` mit vollstaendigen
    Pflicht-Params (Decimal-Felder als Strings → `coerce_scenario_mapping`)."""
    raw = {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "demo", "name": "Demo Scenario"},
        "simulation": {"tick_ms": 100, "duration_s": 60, "seed": 42},
        "devices": [
            {
                "id": "grid-1",
                "type": "grid_connection",
                "params": {
                    "nominal_voltage_v": "400",
                    "max_import_kw": "1000",
                    "max_export_kw": "1000",
                },
            }
        ],
    }
    return load_scenario(coerce_scenario_mapping(raw)).scenario


def test_build_run_driver_returns_unstarted_driver_for_run() -> None:
    repository = InMemoryRunRepository()
    driver = build_run_driver(_scenario(), "run-xyz", repository)
    assert isinstance(driver, DemoTickLoopDriver)
    assert driver.tick_loop_run_id == "run-xyz"
    assert driver.is_running is False  # gebaut, nicht gestartet
