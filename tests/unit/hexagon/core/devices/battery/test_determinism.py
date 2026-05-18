"""Determinismus-Property-Test fuer `BatteryDevice` (ADR 0014 §2.6).

`hypothesis @given(seed=integers())`: gleicher Seed + identische
Command-Sequenz + identische Tick-Folge → byte-identische
SOC-Spur ueber ≥ 100 Ticks.

Welle-2-Battery konsumiert den `RandomPort` zwar nicht (Welle 3+
Fault-Injection wird es), aber die Property-Form ist
zukunftssicher: sobald randomisierte Anteile dazukommen, prueft
der Test sie automatisch mit.
"""

from __future__ import annotations

from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom

_TICKS = 100
"""Welle-2-Pflicht (`M2-devices.md §3 Welle 2`): ≥ 100 Ticks."""


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


def _command(value: Decimal, command_id: str) -> Command:
    return Command(
        command_id=command_id,
        simulation_time=0,
        target_device_id="battery-1",
        type="set_power_kw",
        payload={"value": value},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _run_battery(seed: int, command_powers: tuple[Decimal, ...]) -> tuple[TelemetryPoint, ...]:
    """Konstruiert eine Battery, applied die Command-Sequenz vor Tick 0
    (last-wins), faehrt 100 Ticks bei `tick_ms=1000`, gibt die
    aggregierte Telemetry-Sequenz zurueck."""
    device = BatteryDevice()
    device.initialize(_scenario_device(), FixedSeedRandom(seed=seed))
    for index, power in enumerate(command_powers):
        device.apply_command(_command(power, command_id=f"cmd-{index}"))
    out: list[TelemetryPoint] = []
    for tick in range(_TICKS):
        outcome = device.tick(
            DeviceTickContext(tick=tick, simulation_time=tick * 1000, tick_ms=1000)
        )
        out.extend(outcome.telemetry)
    return tuple(out)


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
@settings(deadline=None, max_examples=25)
def test_same_seed_produces_byte_identical_soc_trace(seed: int) -> None:
    """ADR 0014 §2.6 + Slice-Plan §3 Welle 2: gleicher Seed +
    identische Command-Sequenz → byte-identische SOC-Spur ueber
    100 Ticks."""
    command_powers = (Decimal("250"),)
    trace_a = _run_battery(seed, command_powers)
    trace_b = _run_battery(seed, command_powers)
    assert trace_a == trace_b


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
@settings(deadline=None, max_examples=10)
def test_different_command_sequences_produce_different_traces(seed: int) -> None:
    """Sanity-Check: unterschiedliche Command-Sequenzen liefern
    unterschiedliche Traces — der Determinismus-Vertrag macht das
    Geraet nicht zustandslos."""
    trace_a = _run_battery(seed, (Decimal("250"),))
    trace_b = _run_battery(seed, (Decimal("-250"),))
    assert trace_a != trace_b


def test_full_100_tick_trace_has_300_telemetry_points() -> None:
    """100 Ticks * 3 Metriken (power_kw, soc_kwh, soc_pct) = 300
    Telemetrie-Punkte; pinnt die Telemetrie-Surface gegen
    Regressionen (z. B. wenn jemand eine zusaetzliche Metrik
    ohne Doku einfuegt)."""
    trace = _run_battery(seed=42, command_powers=(Decimal("100"),))
    assert len(trace) == 300
