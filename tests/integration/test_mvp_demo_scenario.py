"""M2-Welle-6c End-to-End-Tests fuer das MVP-Demo-Szenario.

Zwei Pflicht-Akzeptanzen aus `M2-devices.md §3 Welle 6c`
(`GG-MVP-002`):

1. **Determinismus**: zwei `TickLoop`-Laeufe mit gleichem
   `M2_DEMO_SEED` liefern byte-identische
   `TickResult.emitted_telemetry` ueber `MIN_DETERMINISM_TICKS`
   Ticks.
2. **Postgres-Roundtrip**: `RunMetadata` aus dem Lauf wird ueber
   `PostgresRunRepository.save(...)` persistiert und per
   `get_by_id(...)` byte-identisch zurueckgelesen.

YAML-Parsing lebt im Test-Helper
`tests/integration/_yaml_scenario_loader.py` (Anti-Scope: kein
produktiver YAML-Adapter unter `src/`, ADR 0021 §2.1).
"""

from __future__ import annotations

import uuid

from grid_gym.adapters.driven.persistence_postgres import PostgresRunRepository
from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.run import RunMetadata
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.scenario.loader import LoadedScenario, build_tick_loop

from tests.integration._constants import (
    DEMO_TOOL_VERSION,
    M2_DEMO_SEED,
    MIN_DETERMINISM_TICKS,
    MVP_DEMO_SCENARIO_PATH,
)
from tests.integration._yaml_scenario_loader import load_yaml_scenario
from tests.unit.hexagon.ports.driven._fakes import FakeClock


def _drive_demo(loaded: LoadedScenario, *, ticks: int) -> tuple[TelemetryPoint, ...]:
    loop = build_tick_loop(
        loaded.scenario,
        run_id="welle-6c-demo",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed),
    )
    collected: list[TelemetryPoint] = []
    for _ in range(ticks):
        result = loop.tick()
        collected.extend(result.emitted_telemetry)
    return tuple(collected)


def test_demo_scenario_telemetry_is_byte_identical_across_runs() -> None:
    """`M2-devices.md §3 Welle 6c`: zwei Laeufe mit gleichem Seed
    erzeugen byte-identische `TickResult.emitted_telemetry` ueber
    `MIN_DETERMINISM_TICKS=100` Ticks (`GG-MVP-002`).

    Positiv-Assertion (Welle-6c-Review M-2): alle 5 MVP-Geraete
    plus die SmartMeter-Aggregation muessen tatsaechlich Telemetry
    emittieren — sonst bliebe eine Silent-Empty-Telemetry-
    Regression (beide Laeufe gleich-broken) unbemerkt."""
    loaded = load_yaml_scenario(MVP_DEMO_SCENARIO_PATH)
    assert loaded.scenario.simulation.seed == M2_DEMO_SEED
    telemetry_a = _drive_demo(loaded, ticks=MIN_DETERMINISM_TICKS)
    telemetry_b = _drive_demo(loaded, ticks=MIN_DETERMINISM_TICKS)
    assert telemetry_a == telemetry_b
    device_ids = {point.device_id for point in telemetry_a}
    assert device_ids >= {"pv-1", "load-1", "battery-1", "grid-1", "meter-1"}, (
        f"GG-MVP-002 verlangt Telemetry aller 5 MVP-Geraete; gesehen: {device_ids}"
    )
    assert any(
        point.device_id == "meter-1" and point.metric == "aggregated_power_kw"
        for point in telemetry_a
    ), "SmartMeter muss `aggregated_power_kw` emittieren (ADR 0018 §2.4)"


def test_demo_scenario_run_roundtrips_through_postgres(
    repository: PostgresRunRepository,
) -> None:
    """`M2-devices.md §3 Welle 6c`: `runs`-Zeile persistiert + byte-
    identisch zurueckgelesen (`GG-DATA-001`, `GG-TERM-003`)."""
    loaded = load_yaml_scenario(MVP_DEMO_SCENARIO_PATH)
    metadata = RunMetadata(
        run_id=str(uuid.uuid4()),
        scenario_hash=loaded.scenario_hash,
        schema_version=loaded.scenario.schema_version,
        seed=loaded.scenario.simulation.seed,
        tick_ms=loaded.scenario.simulation.tick_ms,
        started_at="2026-05-20T08:00:00Z",
        ended_at="2026-05-20T08:01:40Z",
        tool_version=DEMO_TOOL_VERSION,
    )
    repository.save(metadata)
    assert repository.get_by_id(metadata.run_id) == metadata
