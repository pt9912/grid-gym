"""Trigger-013-Pflicht-Test (`replay-diff-tick-ms-parameter`).

Schliesst Trigger 013 mechanisch: laeuft das BatteryDevice mit
`tick_ms=100` ueber mehrere Ticks, exportiert die Telemetry als
ReplaySamples, vergleicht via `diff_replay(expected, actual,
tick_ms=100)` byte-stabil. Bei `tick_ms != 1000` darf der diff
trotzdem `()` liefern (keine Abweichungen), weil expected ==
actual.

Trigger 013 selbst hat in dieser Welle (M2 Welle 2) den
`tick_ms`-Kwarg zu `diff_replay` hinzugefuegt; dieser Test pinnt:
- Defaultverhalten unveraendert (`tick_ms=1000`).
- `tick_ms=100` setzt `ReplayDelta.tick = simulation_time // 100`.
- `tick_ms=0`/negativ wirft `ReplayInvalidTickMsError`.
- Identische Battery-Spur liefert `()`-Diff.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.replay import (
    ReplayDeltaClassification,
    ReplaySample,
)
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import ReplayInvalidTickMsError
from grid_gym.hexagon.core.replay.diff import diff_replay
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom


def _scenario_device() -> ScenarioDevice:
    return ScenarioDevice(
        id="battery-1",
        type="battery",
        params={
            "capacity_kwh": Decimal("1000"),
            "initial_soc_pct": Decimal("50"),
            "min_soc_pct": Decimal("10"),
            "max_soc_pct": Decimal("90"),
            "max_charge_kw": Decimal("500"),
            "max_discharge_kw": Decimal("500"),
            "charge_efficiency": Decimal("0.95"),
            "discharge_efficiency": Decimal("0.95"),
            "ramp_kw_per_s": Decimal("50"),
        },
    )


def _telemetry_to_replay_samples(
    telemetry: tuple[TelemetryPoint, ...],
) -> tuple[ReplaySample, ...]:
    """Wandelt Battery-Telemetrie in ReplaySamples — mit
    `import_sequence=0`, damit sample-zu-sample-Vergleich klappt."""
    return tuple(
        ReplaySample(
            timestamp=f"sim+{p.simulation_time}ms",
            simulation_time=p.simulation_time,
            device_id=p.device_id,
            metric=p.metric,
            value=p.value,
            unit=p.unit,
            import_sequence=0,
        )
        for p in telemetry
    )


def _run_battery_at_tick_ms(tick_ms: int, ticks: int) -> tuple[TelemetryPoint, ...]:
    device = BatteryDevice()
    device.initialize(_scenario_device(), FixedSeedRandom(seed=0))
    device.apply_command(
        Command(
            command_id="cmd-1",
            simulation_time=0,
            target_device_id="battery-1",
            type="set_power_kw",
            payload={"value": Decimal("100")},
            validation_status="validated",
            result=CommandResult.IGNORED,
        )
    )
    out: list[TelemetryPoint] = []
    for tick in range(ticks):
        outcome = device.tick(
            DeviceTickContext(tick=tick, simulation_time=tick * tick_ms, tick_ms=tick_ms)
        )
        out.extend(outcome.telemetry)
    return tuple(out)


# ---------------------------------------------------------------------------
# Trigger 013: tick_ms-Kwarg zu diff_replay
# ---------------------------------------------------------------------------


def test_diff_replay_default_tick_ms_is_1000() -> None:
    """Defaultverhalten unveraendert (Welle-5-Kompatibilitaet)."""
    sample = ReplaySample(
        timestamp="t",
        simulation_time=5000,
        device_id="d",
        metric="m",
        value=Decimal("1"),
        unit="u",
        import_sequence=0,
    )
    # Erzeuge expected/actual mit unterschiedlichem `value`, damit
    # diff_replay einen Delta liefert (dort lesen wir den tick aus).
    actual = ReplaySample(
        timestamp="t",
        simulation_time=5000,
        device_id="d",
        metric="m",
        value=Decimal("2"),
        unit="u",
        import_sequence=0,
    )
    deltas = diff_replay([sample], [actual])
    assert len(deltas) == 1
    # simulation_time=5000, tick_ms-Default=1000 → tick=5.
    assert deltas[0].tick == 5


def test_diff_replay_tick_ms_100_yields_finer_tick() -> None:
    """Welle-2-Pflicht-Test: bei `tick_ms=100` und
    `simulation_time=500` ist `tick=5` (heutige Default-Semantik
    waere `tick=0`). Trigger-013-Closure."""
    expected = ReplaySample(
        timestamp="t",
        simulation_time=500,
        device_id="battery-1",
        metric="soc_pct",
        value=Decimal("50"),
        unit="pct",
        import_sequence=0,
    )
    actual = ReplaySample(
        timestamp="t",
        simulation_time=500,
        device_id="battery-1",
        metric="soc_pct",
        value=Decimal("51"),  # Drift
        unit="pct",
        import_sequence=0,
    )
    deltas = diff_replay([expected], [actual], tick_ms=100)
    assert len(deltas) == 1
    assert deltas[0].tick == 5  # Trigger-013-Kernaussage


def test_diff_replay_invalid_tick_ms_raises_typed_error() -> None:
    sample = ReplaySample(
        timestamp="t",
        simulation_time=0,
        device_id="d",
        metric="m",
        value=Decimal("0"),
        unit="u",
        import_sequence=0,
    )
    with pytest.raises(ReplayInvalidTickMsError):
        diff_replay([sample], [sample], tick_ms=0)
    with pytest.raises(ReplayInvalidTickMsError):
        diff_replay([sample], [sample], tick_ms=-100)


# ---------------------------------------------------------------------------
# Trigger 013 mit echtem Battery-Trace (Slice-Plan §3 Welle 2)
# ---------------------------------------------------------------------------


def test_battery_trace_at_tick_ms_100_diff_is_empty() -> None:
    """Welle-2-Pflicht-Test (Slice-Plan §3 Welle 2): laeuft das
    Battery mit `tick_ms=100` ueber 10 Ticks, exportiert die
    Telemetry, vergleicht expected == actual via
    `diff_replay(..., tick_ms=100)` byte-stabil → leerer Diff.
    Schliesst Trigger 013 mechanisch."""
    trace = _run_battery_at_tick_ms(tick_ms=100, ticks=10)
    expected = _telemetry_to_replay_samples(trace)
    actual = _telemetry_to_replay_samples(trace)
    deltas = diff_replay(expected, actual, tick_ms=100)
    assert deltas == ()


def test_battery_trace_diff_classifies_value_drift_as_fachlich() -> None:
    """Negativ-Pfad: zwei Battery-Laufe mit unterschiedlichen
    initialen SOCs liefern fachliche Drift-Deltas mit
    `classification=FACHLICH`. Pinnt die diff-Klassifikation
    fuer Welle-2-Battery-Werte."""
    trace_a = _run_battery_at_tick_ms(tick_ms=100, ticks=5)
    # Zweite Battery mit anderem initial_soc_pct.
    device_b = BatteryDevice()
    sd_b = ScenarioDevice(
        id="battery-1",
        type="battery",
        params={
            "capacity_kwh": Decimal("1000"),
            "initial_soc_pct": Decimal("80"),  # 50 -> 80 = drift
            "min_soc_pct": Decimal("10"),
            "max_soc_pct": Decimal("90"),
            "max_charge_kw": Decimal("500"),
            "max_discharge_kw": Decimal("500"),
            "charge_efficiency": Decimal("0.95"),
            "discharge_efficiency": Decimal("0.95"),
            "ramp_kw_per_s": Decimal("50"),
        },
    )
    device_b.initialize(sd_b, FixedSeedRandom(seed=0))
    trace_b: list[TelemetryPoint] = []
    for tick in range(5):
        outcome = device_b.tick(
            DeviceTickContext(tick=tick, simulation_time=tick * 100, tick_ms=100)
        )
        trace_b.extend(outcome.telemetry)

    expected = _telemetry_to_replay_samples(trace_a)
    actual = _telemetry_to_replay_samples(tuple(trace_b))
    deltas = diff_replay(expected, actual, tick_ms=100)
    assert len(deltas) > 0
    assert all(d.classification is ReplayDeltaClassification.FACHLICH for d in deltas)
