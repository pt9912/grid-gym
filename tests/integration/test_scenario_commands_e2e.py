"""E2E: scenario-scheduled Commands treiben die SOLLTE-Geraete (S3, ADR 0070,
Trigger 046).

Schliesst Trigger 046: je SOLLTE-Geraet faehrt ein **nicht-idle** Lauf, bei dem
ein via `commands`-Block geplanter Steuerbefehl (Schritt A0s, ADR 0070 §2.3) das
Geraet sichtbar im Telemetrie-Snapshot reagieren laesst — statt des heutigen
Idle-Smokes. Der Command wird in das bestehende Demo-Szenario injiziert (gleiche
Geraete wie der Idle-Smoke), faellig an Tick 2 (`simulation_time=2000`,
`tick_ms=1000`).

Wind nimmt keine Commands (ADR 0057 §2.1) -> IGNORED-Beleg: der Command wird
zugestellt, aber die Wind-Telemetrie bleibt byte-identisch zum Idle-Lauf.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.domain.scenario import Scenario
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.scenario.loader import build_tick_loop, load_scenario
from grid_gym.scenario_yaml import read_scenario_yaml

from tests.integration._constants import (
    DIESEL_DEMO_SCENARIO_PATH,
    DIESEL_DEMO_TICKS,
    EV_CHARGER_DEMO_SCENARIO_PATH,
    EV_CHARGER_DEMO_TICKS,
    TRANSFORMER_DEMO_SCENARIO_PATH,
    TRANSFORMER_DEMO_TICKS,
    WIND_TURBINE_DEMO_SCENARIO_PATH,
    WIND_TURBINE_DEMO_TICKS,
)
from tests.integration._yaml_scenario_loader import load_yaml_scenario
from tests.unit.hexagon.ports.driven._fakes import FakeClock

# Faellig an Tick 2 (now=2000) bei tick_ms=1000 — frueh genug, dass der Effekt
# den Grossteil des 60-Tick-Laufs praegt.
_COMMAND_SIMULATION_TIME = 2000


def _scenario_with_command(
    path: Path, *, target: str, command_type: str, payload: dict[str, object]
) -> Scenario:
    raw = read_scenario_yaml(path)
    command = {
        "simulation_time": _COMMAND_SIMULATION_TIME,
        "target": target,
        "type": command_type,
        "payload": payload,
    }
    return load_scenario({**raw, "commands": [command]}).scenario


def _drive(scenario: Scenario, *, run_id: str, ticks: int) -> tuple[TelemetryPoint, ...]:
    loop = build_tick_loop(
        scenario,
        run_id=run_id,
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=scenario.simulation.seed),
    )
    collected: list[TelemetryPoint] = []
    for _ in range(ticks):
        collected.extend(loop.tick().emitted_telemetry)
    return tuple(collected)


def _values(telemetry: tuple[TelemetryPoint, ...], device_id: str, metric: str) -> list[Decimal]:
    return [p.value for p in telemetry if p.device_id == device_id and p.metric == metric]


def test_ev_charger_set_charge_power_command_charges() -> None:
    scenario = _scenario_with_command(
        EV_CHARGER_DEMO_SCENARIO_PATH,
        target="ev-1",
        command_type="set_charge_power",
        payload={"value": Decimal("11")},
    )
    telemetry = _drive(scenario, run_id="welle-046-ev", ticks=EV_CHARGER_DEMO_TICKS)
    power = _values(telemetry, "ev-1", "power_kw")
    soc = _values(telemetry, "ev-1", "soc")
    assert power[0] == Decimal("0.000000")  # Tick 1 (now=1000) noch idle
    assert max(power) > Decimal("0")  # Command -> Laden
    assert soc[-1] > Decimal("0.200000")  # SoC steigt durch das Laden


def test_transformer_set_power_kw_command_drives_throughput() -> None:
    scenario = _scenario_with_command(
        TRANSFORMER_DEMO_SCENARIO_PATH,
        target="tr-1",
        command_type="set_power_kw",
        payload={"value": Decimal("500")},
    )
    telemetry = _drive(scenario, run_id="welle-046-tr", ticks=TRANSFORMER_DEMO_TICKS)
    primary = _values(telemetry, "tr-1", "primary_power_kw")
    assert primary[0] == Decimal("0.000000")  # Tick 1 noch ohne Durchsatz
    assert max(primary) > Decimal("0")  # Command -> Durchsatz


def test_diesel_set_power_kw_command_starts_genset() -> None:
    scenario = _scenario_with_command(
        DIESEL_DEMO_SCENARIO_PATH,
        target="dg-1",
        command_type="set_power_kw",
        payload={"value": Decimal("60")},
    )
    telemetry = _drive(scenario, run_id="welle-046-dg", ticks=DIESEL_DEMO_TICKS)
    power = _values(telemetry, "dg-1", "power_kw")
    running = _values(telemetry, "dg-1", "running")
    assert max(power) > Decimal("0")  # Command (>= min_start_power_kw) -> Erzeugung
    assert max(running) == Decimal("1.000000")  # Generator startet


def test_wind_command_is_ignored_and_telemetry_unchanged() -> None:
    """Wind nimmt keine Commands (ADR 0057 §2.1): ein geplanter `set_power_kw`
    wird zugestellt, aber IGNORED -> Wind-Telemetrie byte-identisch zum Idle-Lauf
    (gleicher Seed -> gleiche stochastische Wind-Ziehung)."""
    idle = _drive(
        load_yaml_scenario(WIND_TURBINE_DEMO_SCENARIO_PATH).scenario,
        run_id="welle-046-wt",
        ticks=WIND_TURBINE_DEMO_TICKS,
    )
    commanded = _drive(
        _scenario_with_command(
            WIND_TURBINE_DEMO_SCENARIO_PATH,
            target="wt-1",
            command_type="set_power_kw",
            payload={"value": Decimal("999")},
        ),
        run_id="welle-046-wt",
        ticks=WIND_TURBINE_DEMO_TICKS,
    )
    wt_idle = [p for p in idle if p.device_id == "wt-1"]
    wt_commanded = [p for p in commanded if p.device_id == "wt-1"]
    assert wt_commanded == wt_idle
