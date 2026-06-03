"""End-to-End-Integration-Smoke fuer M5-Welle-5 (Demo-Pipeline
+ Scenario-Loader-Wiring, Slice-Doc M5-welle-5 Decisions 5/6/18).

Pinnt die produktive Welle-5-Lifespan-Verdrahtung:

1. ``GRID_GYM_DEMO_SCENARIO_PATH`` zeigt auf
   ``deploy/scenarios/gg-demo.yaml``.
2. ``TestClient(app)`` triggert den Lifespan-env-var-Branch.
3. Der Lifespan verdrahtet `InMemoryRunRepository` +
   `InMemoryTelemetryStream` + `TickLoopRegistry` +
   `InMemoryAlarmStream`/`AlarmHistoryBuffer` +
   `configure_scenario_demo_run` und startet den
   `DemoTickLoopDriver`.
4. ``GET /runs/demo-run-0001`` zeigt die RunMetadata aus dem
   Scenario-Hash.
5. ``GET /runs/demo-run-0001/status`` zeigt den Lifecycle-State
   (pending/running).
6. ``GET /runs/demo-run-0001/alarms-history`` ist erreichbar
   (leere History ist OK; LoadEvent triggert erst bei
   simulation_time=600s).
7. Determinismus (Slice-Doc §6 + R5): zwei Aufrufe von
   `_load_scenario_from_yaml` liefern denselben
   `scenario_hash` (Decision 5 `seed=42` + canonical_json-
   Roundtrip).

R2 (Slice-Doc §7): der `python -m grid_gym demo`-Uvicorn-Pfad
wird in diesem Smoke **nicht** exerciert — `make demo` ist der
Container-Smoke (manuelle Verifikation per GG-DEMO-008).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driving.http_api._demo_scenario_setup import (
    _DEMO_RUN_ID,
    _load_scenario_from_yaml,
)
from grid_gym.adapters.driving.http_api.app import _DEMO_SCENARIO_ENV_VAR, app


_DEMO_SCENARIO_PATH: Path = (
    Path(__file__).resolve().parents[2] / "deploy" / "scenarios" / "gg-demo.yaml"
)


def _reset_app_state() -> None:
    """Welle-5-Smoke-Isolierung: vorhergehende Smoke-Tests setzen
    `configure_*` ueber Modul-globalen ``app.state``; ohne Reset
    wuerde der Welle-5-Lifespan-env-var-Branch die bereits
    gesetzte Komponenten erkennen und skippen."""
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
    """Setzt env-var + reset App-State + `TestClient(app)` mit
    Welle-5-Lifespan-Pfad."""
    _reset_app_state()
    monkeypatch.setenv(_DEMO_SCENARIO_ENV_VAR, str(_DEMO_SCENARIO_PATH))
    with TestClient(app) as client:
        yield client
    _reset_app_state()


def test_demo_scenario_yaml_exists() -> None:
    """Slice-Doc §5: kanonisches Demo-YAML liegt unter
    `deploy/scenarios/gg-demo.yaml` und ist YAML-lesbar."""
    assert _DEMO_SCENARIO_PATH.is_file()


def test_demo_lifespan_wires_run_and_returns_metadata(
    demo_client: TestClient,
) -> None:
    """Slice-Doc §6 (Welle-5-Gate): GET /runs/demo-run-0001 → 200
    nach Lifespan-env-var-Pfad."""
    response = demo_client.get(f"/runs/{_DEMO_RUN_ID}")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == _DEMO_RUN_ID
    assert body["seed"] == 42
    assert body["tick_ms"] == 1000


def test_demo_status_endpoint_reachable_after_lifespan(
    demo_client: TestClient,
) -> None:
    """Welle-4a-/-5 Status-Endpoint laeuft auf dem
    `InMemoryRunRepository`-Lifecycle-State; `pending` oder
    `running` sind beide gueltige Welle-5-Antworten (Driver-
    Race)."""
    response = demo_client.get(f"/runs/{_DEMO_RUN_ID}/status")
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == _DEMO_RUN_ID
    assert body["state"] in {"pending", "running"}


def test_demo_alarms_history_endpoint_reachable(
    demo_client: TestClient,
) -> None:
    """Welle-4b Alarms-History-Endpoint laeuft auf dem
    `AlarmHistoryBuffer`-Singleton; LoadEvent triggert erst bei
    simulation_time=600s, Welle-5-Smoke laeuft viel kuerzer —
    leere History ist OK, 200-Status pinnt die Wiring."""
    response = demo_client.get(f"/runs/{_DEMO_RUN_ID}/alarms-history")
    assert response.status_code == 200
    body = response.json()
    assert "alarms" in body
    assert isinstance(body["alarms"], list)


def test_demo_scenario_hash_is_deterministic() -> None:
    """Slice-Doc §6 Determinismus + R5: zwei Aufrufe des
    Demo-YAML-Loaders liefern denselben `scenario_hash`. Der
    Hash ist die Single-Source-of-Truth fuer die canonical_json-
    Reproduzierbarkeit der Decision-5-Demo (seed=42 fixiert in
    der YAML)."""
    first = _load_scenario_from_yaml(_DEMO_SCENARIO_PATH)
    second = _load_scenario_from_yaml(_DEMO_SCENARIO_PATH)
    assert first.scenario_hash == second.scenario_hash


def test_demo_scenario_hash_pin_for_drift_detection() -> None:
    """Slice-Doc §7 R5: Welle-5-Smoke pinnt den Hash, damit
    jeder spaetere Welle-6+/Device-Change in der Demo-YAML
    bewusst sichtbar wird.

    Welle-6a-Review F10: konkreten Hash-Wert pinnen statt nur
    Laenge (64 hex chars). Ohne Wert-Pin passierte der
    Welle-6a-faults+agent-Edit (`-20`→`-30`) den Test
    unentdeckt; ADR-0021-§2.9-Determinismus-Garantie war
    Demo-side ungesichert. Update-Pflicht bei jedem
    bewussten YAML-Edit (siehe Welle-6a-§10.x-Realization-
    Notes-Pflege).
    """
    loaded = _load_scenario_from_yaml(_DEMO_SCENARIO_PATH)
    expected_hash = "00ac59d8c2fb163a826e42d3da0f584400b7592915292caebb0a3ce879e591c6"
    assert loaded.scenario_hash == expected_hash, (
        f"scenario_hash drift! Expected {expected_hash} "
        f"(post-Welle-6a-faults-block), got {loaded.scenario_hash}. "
        "If the YAML edit was intentional, update the pin here "
        "in the same PR + add a Welle-6a/6b/... §10 Realization-Note."
    )
