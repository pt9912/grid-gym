"""Pins fuer `build_run_driver` + Replay-Konsumnaht (Multi-Run-Execution S3/S4,
ADR 0069 §2.4/§2.5).

S3: baut aus einem kanonisierten Scenario einen ungestarteten per-Run-Driver.
S4: bei gesetztem `replay_of` difft `finalize()` den Lauf gegen seinen
Referenzlauf — Samples aus dem **geteilten** Telemetrie-Sink (§2.3-Verfeinerung).
"""

from __future__ import annotations

from grid_gym.adapters.driven.persistence_inmemory import (
    InMemoryRunRepository,
    InMemoryTelemetrySink,
)
from grid_gym.adapters.driving.http_api._tick_loop_driver import DemoTickLoopDriver
from grid_gym.composition._demo_scenario_setup import build_run_driver
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.domain.scenario import Scenario
from grid_gym.hexagon.core.scenario.loader import LoadedScenario, load_scenario
from grid_gym.scenario_yaml import coerce_scenario_mapping

_RAW = {
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


def _loaded() -> LoadedScenario:
    """Baubares Minimal-Scenario (grid_connection mit vollstaendigen Params)."""
    return load_scenario(coerce_scenario_mapping(_RAW))


def _scenario() -> Scenario:
    return _loaded().scenario


def _metadata(run_id: str, scenario_hash: str, replay_of: str | None = None) -> RunMetadata:
    return RunMetadata(
        run_id=run_id,
        scenario_hash=scenario_hash,
        schema_version="grid-gym.scenario.v1",
        seed=42,
        tick_ms=100,
        started_at="",
        ended_at="",
        tool_version="0.1.0",
        replay_of=replay_of,
    )


def test_build_run_driver_returns_unstarted_driver_for_run() -> None:
    repository = InMemoryRunRepository()
    driver = build_run_driver(
        _scenario(),
        "run-xyz",
        repository,
        replay_of=None,
        telemetry_sink=InMemoryTelemetrySink(),
    )
    assert isinstance(driver, DemoTickLoopDriver)
    assert driver.tick_loop_run_id == "run-xyz"
    assert driver.is_running is False  # gebaut, nicht gestartet


def test_replay_run_diffs_against_reference_via_shared_sink() -> None:
    """Lauf B (`replay_of=A`) difft beim `finalize()` gegen A — Referenz-Samples
    aus dem **geteilten** Sink. Identische Laeufe → leerer Diff."""
    loaded = _loaded()
    scenario, scenario_hash = loaded.scenario, loaded.scenario_hash
    sink = InMemoryTelemetrySink()  # geteilt ueber beide Laeufe
    repository = InMemoryRunRepository()
    repository.save(_metadata("run-a", scenario_hash))
    repository.save(_metadata("run-b", scenario_hash, replay_of="run-a"))

    driver_a = build_run_driver(scenario, "run-a", repository, replay_of=None, telemetry_sink=sink)
    loop_a = driver_a._tick_loop
    for _ in range(3):
        loop_a.tick()
    loop_a.finalize()  # A ohne Referenz → no-op; A-Samples liegen im geteilten Sink

    driver_b = build_run_driver(
        scenario, "run-b", repository, replay_of="run-a", telemetry_sink=sink
    )
    loop_b = driver_b._tick_loop
    for _ in range(3):
        loop_b.tick()
    deltas = loop_b.finalize()  # liest A + B aus dem geteilten Sink → Diff

    assert deltas == ()  # identische Laeufe → leerer Replay-Diff (verifiziert)


def test_no_replay_diff_when_replay_of_none() -> None:
    """`replay_of=None` → `finalize()` ist no-op (kein Referenzlauf)."""
    loaded = _loaded()
    repository = InMemoryRunRepository()
    repository.save(_metadata("run-solo", loaded.scenario_hash))
    driver = build_run_driver(
        loaded.scenario,
        "run-solo",
        repository,
        replay_of=None,
        telemetry_sink=InMemoryTelemetrySink(),
    )
    loop = driver._tick_loop
    loop.tick()
    assert loop.finalize() == ()


def test_asgi_shared_sink_builder_builds_driver() -> None:
    """Der in `composition.asgi` registrierte Wrapper bindet den geteilten Sink
    und baut einen Driver."""
    from grid_gym.composition.asgi import _build_run_driver_with_shared_sink

    repository = InMemoryRunRepository()
    driver = _build_run_driver_with_shared_sink(_scenario(), "run-asgi", repository, None)
    assert isinstance(driver, DemoTickLoopDriver)
    assert driver.tick_loop_run_id == "run-asgi"
