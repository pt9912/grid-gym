"""Pins fuer `build_run_driver` + Replay-Konsumnaht (Multi-Run-Execution S3/S4,
ADR 0069 §2.4/§2.5).

S3: baut aus einem kanonisierten Scenario einen ungestarteten per-Run-Driver.
S4: bei gesetztem `metadata.replay_of` difft `finalize()` den Lauf gegen seinen
Referenzlauf — Samples aus dem **geteilten** Telemetrie-Sink (§2.3-Verfeinerung).
Seed + `replay_of` liest `build_run_driver` aus der persistierten `RunMetadata`.
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


def _save(repository: InMemoryRunRepository, run_id: str, replay_of: str | None = None) -> str:
    """Persistiert RunMetadata (build_run_driver liest Seed + replay_of daraus);
    gibt den scenario_hash zurueck."""
    loaded = _loaded()
    repository.save(
        RunMetadata(
            run_id=run_id,
            scenario_hash=loaded.scenario_hash,
            schema_version="grid-gym.scenario.v1",
            seed=42,
            tick_ms=100,
            started_at="",
            ended_at="",
            tool_version="0.1.0",
            replay_of=replay_of,
        )
    )
    return loaded.scenario_hash


def test_build_run_driver_returns_unstarted_driver_for_run() -> None:
    repository = InMemoryRunRepository()
    _save(repository, "run-xyz")
    driver = build_run_driver(
        _scenario(), "run-xyz", repository, telemetry_sink=InMemoryTelemetrySink()
    )
    assert isinstance(driver, DemoTickLoopDriver)
    assert driver.tick_loop_run_id == "run-xyz"
    assert driver.is_running is False  # gebaut, nicht gestartet


def test_replay_run_diffs_against_reference_via_shared_sink() -> None:
    """Lauf B (`metadata.replay_of=A`) difft beim `finalize()` gegen A —
    Referenz-Samples aus dem **geteilten** Sink. Identische Laeufe → leerer Diff."""
    scenario = _scenario()
    sink = InMemoryTelemetrySink()  # geteilt ueber beide Laeufe
    repository = InMemoryRunRepository()
    _save(repository, "run-a")
    _save(repository, "run-b", replay_of="run-a")

    driver_a = build_run_driver(scenario, "run-a", repository, telemetry_sink=sink)
    loop_a = driver_a._tick_loop
    for _ in range(3):
        loop_a.tick()
    loop_a.finalize()  # A ohne Referenz → no-op; A-Samples liegen im geteilten Sink

    driver_b = build_run_driver(scenario, "run-b", repository, telemetry_sink=sink)
    loop_b = driver_b._tick_loop
    for _ in range(3):
        loop_b.tick()
    deltas = loop_b.finalize()  # liest A + B aus dem geteilten Sink → Diff

    assert deltas == ()  # identische Laeufe → leerer Replay-Diff (verifiziert)


def test_no_replay_diff_when_replay_of_none() -> None:
    """`metadata.replay_of=None` → `finalize()` ist no-op (kein Referenzlauf)."""
    repository = InMemoryRunRepository()
    _save(repository, "run-solo")
    driver = build_run_driver(
        _scenario(), "run-solo", repository, telemetry_sink=InMemoryTelemetrySink()
    )
    loop = driver._tick_loop
    loop.tick()
    assert loop.finalize() == ()


def test_asgi_shared_sink_builder_builds_driver() -> None:
    """Der in `composition.asgi` registrierte Wrapper bindet den geteilten Sink
    und baut einen Driver."""
    from grid_gym.composition.asgi import _build_run_driver_with_shared_sink

    repository = InMemoryRunRepository()
    _save(repository, "run-asgi")
    driver = _build_run_driver_with_shared_sink(_scenario(), "run-asgi", repository)
    assert isinstance(driver, DemoTickLoopDriver)
    assert driver.tick_loop_run_id == "run-asgi"
