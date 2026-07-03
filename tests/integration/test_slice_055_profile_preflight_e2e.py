"""Slice 055 — E2E-Sensor: produktiver Profil-Pfad → Replay-Preflight.

Faehrt die volle API-Kette mit dem **real registrierten**
Composition-Profil aus `grid_gym.composition.asgi` (Slice-038-
Review-INFO: die Kette war nur stueckweise gepinnt, der
Integration-Smoke hardcodete die Vollfelder):

1. `POST /scenarios` (Intake, ADR 0069 §2.1) mit kanonischem Hash.
2. Referenzlauf A: `POST /runs` → `POST /runs/{A}/start` → running.
3. Replay-Lauf B: `POST /runs` mit `replay_of=A` (ADR 0068) →
   start → running.
4. TestClient-Context-Exit → Lifespan-Shutdown →
   `RunDriverRegistry.stop_all()` → beide Driver stoppen; der
   `finalize()`-Preflight von B laeuft real auf der
   Run-End-Naht (ADR 0067 §2.4). Es gibt bewusst KEINE
   HTTP-Stop-Surface fuer per-Run-Driver (`/control` ist die
   Demo-Single-Run-Naht ueber die `TickLoopRegistry` → 503).
5. Asserts auf der persistierten Metadata-Ebene — das ist exakt
   der Preflight-Vertrag aus ADR 0073 §2.6: reale Profil-Werte
   (ConfigView-v1-Hash, kanonisierte `platform.machine()`,
   Adapter-Familie), 9-Felder-Gleichheit zwischen A und B,
   Vollfelder nicht-fehlend.

Dokumentierte Grenze (Slice-055-Anti-Scope): KEIN Clean-Diff-
Assert — API-Laeufe haben kein Tick-Budget (Auto-`completed`
out-of-scope per ADR 0049 §7), Wall-Clock-Stops liefern
nicht-deterministische Tick-Zahlen. Der Clean-Diff-Beleg lebt im
Zwei-Lauf-Lifecycle-Smoke (`test_mvp_002_replay_lifecycle_smoke`).
"""

from __future__ import annotations

import platform
import time

import pytest
from fastapi.testclient import TestClient

from grid_gym.adapters.driven.persistence_inmemory import (
    InMemoryRunRepository,
    InMemoryScenarioStore,
)
from grid_gym.adapters.driving.http_api._run_driver_registry import RunDriverRegistry
from grid_gym.adapters.driving.http_api._run_driver_setup import (
    configure_run_driver_registry,
)
from grid_gym.adapters.driving.http_api._run_execution_profile import (
    get_run_execution_profile,
)
from grid_gym.adapters.driving.http_api._scenario_setup import configure_scenario_store
from grid_gym.adapters.driving.http_api._tick_loop_registry import TickLoopRegistry
from grid_gym.adapters.driving.http_api.app import (
    configure_run_repository,
    configure_tick_loop_registry,
)

# Import des Composition-Entrypoints registriert das REALE Profil +
# Scenario-Intake + Driver-Builder per Hook-Inversion (ADR 0054) —
# genau die Verdrahtung, die dieser Sensor beweisen soll.
from grid_gym.composition.asgi import app
from grid_gym.hexagon.core.domain.run import (
    RunMetadata,
    canonical_platform_arch,
)
from grid_gym.hexagon.core.scenario.loader import load_scenario
from grid_gym.hexagon.core.serialization.config_view import config_hash_for
from grid_gym.scenario_yaml import coerce_scenario_mapping

pytestmark = pytest.mark.replay
"""`make test-replay`-Sensor-Zuordnung (GG-REPLAY-007 / Trigger 054):
der Sensor pinnt die Preflight-Vergleichsbasis des produktiven
API-Replay-Pfads."""

_RAW: dict[str, object] = {
    "schema_version": "grid-gym.scenario.v1",
    "metadata": {"id": "slice-055", "name": "Profile Preflight E2E"},
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

_STATUS_DEADLINE_S = 10.0
_STATUS_POLL_S = 0.05

# ADR 0073 §2.6: die 9 Felder der vollen GG-TERM-002/003-Equality-
# Matrix. Bewusst lokal gepinnt statt aus `tick_loop` importiert
# (AC-TICK-LOOP-PRIVATE-RESUME-ERRORS verbietet den modul-privaten
# Import); ein 10. Feld muss diesen Sensor bewusst nachziehen.
_PREFLIGHT_FIELDS: tuple[str, ...] = (
    "scenario_hash",
    "schema_version",
    "seed",
    "tick_ms",
    "tool_version",
    "platform_arch",
    "enabled_adapters",
    "sim_start_time",
    "config_hash",
)


def _await_running(client: TestClient, run_id: str) -> None:
    """Pollt `GET /runs/{id}/status`, bis der Driver den ersten Tick
    gespiegelt hat (Wall-Clock-Deadline gegen Haenger)."""
    deadline = time.monotonic() + _STATUS_DEADLINE_S
    while time.monotonic() < deadline:
        status = client.get(f"/runs/{run_id}/status").json()["state"]
        if status == "running":
            return
        time.sleep(_STATUS_POLL_S)
    raise AssertionError(f"run {run_id!r} did not reach 'running' within deadline")


def _create_and_start(client: TestClient, scenario_hash: str, *, replay_of: str | None) -> str:
    """`POST /runs` (erbt das Composition-Profil) + `POST /start`."""
    payload: dict[str, object] = {
        "scenario_hash": scenario_hash,
        "seed": 42,
        "tick_ms": 100,
    }
    if replay_of is not None:
        payload["replay_of"] = replay_of
    created = client.post("/runs", json=payload)
    assert created.status_code == 201, created.text
    run_id = str(created.json()["run_id"])
    started = client.post(f"/runs/{run_id}/start")
    assert started.status_code == 202, started.text
    _await_running(client, run_id)
    return run_id


def test_api_runs_inherit_real_profile_and_form_valid_preflight_basis() -> None:
    repository = InMemoryRunRepository()
    configure_run_repository(repository)
    configure_scenario_store(InMemoryScenarioStore())
    configure_run_driver_registry(RunDriverRegistry())
    configure_tick_loop_registry(TickLoopRegistry())
    loaded = load_scenario(coerce_scenario_mapping(_RAW))

    with TestClient(app) as client:
        intake = client.post(
            "/scenarios",
            json={"scenario": _RAW, "scenario_hash": loaded.scenario_hash},
        )
        assert intake.status_code == 201, intake.text
        run_a = _create_and_start(client, loaded.scenario_hash, replay_of=None)
        run_b = _create_and_start(client, loaded.scenario_hash, replay_of=run_a)
    # Context-Exit: Lifespan-Shutdown → `stop_all()` → beide Driver
    # gestoppt; `finalize()` (inkl. realem 9-Felder-Preflight fuer B)
    # ist auf der Run-End-Naht gelaufen (ADR 0067 §2.4).
    assert repository.get_status(run_a) in ("stopped", "completed")
    assert repository.get_status(run_b) in ("stopped", "completed")

    meta_a: RunMetadata = repository.get_by_id(run_a)
    meta_b: RunMetadata = repository.get_by_id(run_b)

    # 1) Reales Composition-Profil (nicht Fixture-Werte): ConfigView-
    #    v1-Hash, kanonisierte Maschinen-Arch, Adapter-Familie
    #    (ADR 0073 §2.3-§2.5 / composition/_execution_profile.py).
    profile = get_run_execution_profile()
    assert profile.enabled_adapters == ("http_api", "persistence_inmemory")
    assert profile.config_hash == config_hash_for(max_age_ms=None)
    assert profile.platform_arch == canonical_platform_arch(platform.machine())
    assert profile.platform_arch != ""

    for meta in (meta_a, meta_b):
        assert meta.platform_arch == profile.platform_arch
        assert meta.enabled_adapters == profile.enabled_adapters
        assert meta.config_hash == profile.config_hash
        assert meta.sim_start_time == 0

    # 2) Persistente Replay-Bindung (ADR 0068).
    assert meta_b.replay_of == run_a
    assert meta_a.replay_of is None

    # 3) Preflight-Vergleichsbasis (ADR 0073 §2.6): alle 9 Felder
    #    gleich, Vollfelder nicht-fehlend — der reale finalize()-
    #    Preflight von Lauf B hatte damit einen validen Vergleich
    #    (kein missing-/Mismatch-Reject).
    for field in _PREFLIGHT_FIELDS:
        assert getattr(meta_a, field) == getattr(meta_b, field), field
    assert meta_a.platform_arch and meta_a.enabled_adapters and meta_a.config_hash
