"""Headless-Demo-Replay-Helper fuer die Abnahme-CLI (M7-Welle-2,
GG-MVP-003; Slice-Doc D-8 + D-10).

**tools-intern** (Leading-Underscore = kein API-Vertrag). Geteilte
Substanz zwischen `tools/accept.py` (Step B) und
`tools/check_demo_scenario_pin.py` (CI-Drift-Lint), damit beide
**bauartbedingt identisch** rechnen — Duplikation waere genau die
Drift-Quelle, die der Lint verhindern soll.

`run_demo_replay` ist **kein** neuer Driver, sondern ein duenner
Wrapper um den produktiven `build_tick_loop` (`loader.py`) +
einen minimalen deterministischen Step-Clock + die Fault-Composition
aus `scenario.faults` (repliziert die `_demo_scenario_setup`-
Composition; D-10 Option A — `tools/` ist nicht Core-`src/`, ADR
0021 §2.1 zielt auf den Hexagon-Core, nicht auf Ops-Tooling).
`agents` verdrahtet `build_tick_loop` selbst aus `scenario.agents`.

Determinismus-Vertrag: `run_repository=None` + `telemetry_sink=None`
+ `alarm_id_source=None` (Default-Wiring) → die Projektion traegt
**keine** volatilen Felder; zwei Laeufe mit gleichem Seed liefern
byte-identische `emitted_telemetry`.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import asdict

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import Scenario, ScenarioFault
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.faults import BatteryFaultAdapter, GridFaultAdapter
from grid_gym.hexagon.core.scenario.loader import TickLoopWiring, build_tick_loop
from grid_gym.hexagon.core.serialization.canonical import canonical_json

# Dieselbe Tick-Zahl wie der produktive Determinismus-Test
# (`tests/integration/_constants.py::MIN_DETERMINISM_TICKS`); hier als
# tools-interne Konstante gespiegelt (kein Test-Import aus `tools/`).
MIN_DETERMINISM_TICKS: int = 100

# Fault-Typen, fuer die `BatteryFaultAdapter`/`GridFaultAdapter` einen
# Filter halten (Spiegel von `_demo_scenario_setup._KNOWN_FAULT_TYPES`).
_KNOWN_FAULT_TYPES: frozenset[str] = frozenset({"cell_failure", "voltage_drop"})


class _UnknownFaultTypeError(ValueError):
    """Eine `faults[].type` ohne Adapter-Filter (Spiegel der
    http_api-internen Fail-Fast-Pruefung; verhindert silent-no-op
    Faults im Abnahme-Replay)."""


class _StepClock:
    """Minimaler deterministischer `ClockPort` (now/advance), getrieben
    durch `TickLoop.tick()`. Spiegel von `FakeClock`/
    `_DemoSimulationClock` ohne Wall-Clock-Quelle (AC-NO-TIME)."""

    def __init__(self) -> None:
        self._now = 0

    def now(self) -> int:
        return self._now

    def advance(self, delta_ms: int) -> None:
        # Nur vom TickLoop.tick() mit `tick_ms > 0` getrieben (am
        # TickLoop-Konstruktor validiert); kein eigener Guard noetig.
        self._now += delta_ms


class _FaultPortComposition:
    """Delegiert `apply_active_faults` an `BatteryFaultAdapter` +
    `GridFaultAdapter` (Reihenfolge Battery → Grid; deterministisch,
    ADR 0025 §2.4). Spiegel der `_demo_scenario_setup`-Composition."""

    def __init__(self, faults: tuple[ScenarioFault, ...]) -> None:
        self._battery_adapter = BatteryFaultAdapter(faults)
        self._grid_adapter = GridFaultAdapter(faults)

    def apply_active_faults(
        self,
        devices: Sequence[object],
        context: DeviceTickContext,
    ) -> None:
        self._battery_adapter.apply_active_faults(devices, context)
        self._grid_adapter.apply_active_faults(devices, context)


def _compose_fault_port(faults: tuple[ScenarioFault, ...]) -> _FaultPortComposition | None:
    """`None` bei leerer Fault-Liste; sonst die Battery+Grid-Composition.
    Fail-fast bei unbekanntem `fault.type` (sonst silent no-op)."""
    if not faults:
        return None
    for fault in faults:
        if fault.type not in _KNOWN_FAULT_TYPES:
            raise _UnknownFaultTypeError(fault.type)
    return _FaultPortComposition(faults)


def run_demo_replay(
    scenario: Scenario,
    *,
    seed: int,
    ticks: int = MIN_DETERMINISM_TICKS,
) -> tuple[TelemetryPoint, ...]:
    """Faehrt das Szenario `ticks` Ticks headless ueber den produktiven
    `build_tick_loop` und sammelt `TickResult.emitted_telemetry`.

    Verdrahtet `faults` (Composition) + `agents` (durch `build_tick_loop`
    aus `scenario.agents`); kein FastAPI/Postgres noetig."""
    loop = build_tick_loop(
        scenario,
        run_id="abnahme-demo-replay",
        clock=_StepClock(),
        random_root=MersenneTwisterRandomPort(seed=seed),
        wiring=TickLoopWiring(fault_port=_compose_fault_port(scenario.faults)),
    )
    collected: list[TelemetryPoint] = []
    for _ in range(ticks):
        result = loop.tick()
        collected.extend(result.emitted_telemetry)
    return tuple(collected)


def hash_telemetry_stream(stream: tuple[TelemetryPoint, ...]) -> str:
    """Kanonischer SHA-256 ueber den Telemetry-Stream (Pflicht-Vertrag,
    damit Lint und CLI identisch rechnen): `sha256(canonical_json(
    list_of_telemetry_dicts)).hexdigest()` — dieselbe Primitive wie
    `LoadedScenario.scenario_hash` (`loader.py`), hier auf einer `list`.
    `canonical_json` akzeptiert Top-Level-`list` und liefert `bytes`
    (C0-Audit-Pflicht verifiziert)."""
    payload = [asdict(point) for point in stream]
    return hashlib.sha256(canonical_json(payload)).hexdigest()
