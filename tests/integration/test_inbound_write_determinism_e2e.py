"""E2E: Inbound-Write-Determinismus via Materialisierung (Slice 075 S2, ADR 0076
§2.1/§2.2, Modell B).

Der **Kern-Nachweis**, der die Ausgliederung ueberhaupt begruendet: ein Inbound-
Write ist ein exogener Wall-Clock-Input, aber der **erfasste** Strom ist
deterministisch. Ablauf:

1. **„Live"-Lauf**: ein `InboundCommandBuffer` fuettert den `TickLoop` als
   `inbound_source` (Schritt A0i); ein Write wird an einem definierten Tick
   gepuffert (die pymodbus-Master→Buffer-Naht deckt `test_write_e2e.py` bereits
   ab — der Determinismus-Nachweis ist davon unabhaengig).
2. **Materialisieren**: `materialize_inbound_writes(buffer.capture())` →
   Szenario-`commands`-Block.
3. **Replay 2x** (reiner A0s-Pfad, **kein** `inbound_source`): byte-identische
   Telemetrie — und deckungsgleich mit der „Live"-Telemetrie des kommandierten
   Geraets (Materialisierung ist **faithful** fuer ein agenten-freies Ziel; die
   Agent-Konflikt-Grenze pinnt `test_tick_loop_inbound_commands.py`).

Agenten-frei (EV-Charger-Demo) → A0i-Live und A0s-Replay wirken am selben Tick
**vor** `tick()` auf denselben Zustand → byte-treu.
"""

from __future__ import annotations

from decimal import Decimal

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.adapters.driving._inbound_command_buffer import (
    InboundCommandBuffer,
    materialize_inbound_writes,
)
from grid_gym.hexagon.core.domain.scenario import Scenario, ScenarioCommand
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.scenario.loader import (
    TickLoopWiring,
    build_tick_loop,
    load_scenario,
)
from grid_gym.scenario_yaml import read_scenario_yaml

from tests.integration._constants import (
    EV_CHARGER_DEMO_SCENARIO_PATH,
    EV_CHARGER_DEMO_TICKS,
)
from tests.unit.hexagon.ports.driven._fakes import FakeClock

# EV-Charger-Demo hat tick_ms=1000 → der 2. Tick (0-basiert Index 1) hat now=2000;
# der Inbound-Write wird davor gepuffert und dort auf now=2000 aufgeloest.
_INBOUND_TICK_INDEX = 1
_TARGET = "ev-1"
_COMMAND_TYPE = "set_charge_power"
_CHARGE_POWER_KW = Decimal("11")
# Gemeinsame run_id fuer alle Vergleichs-Laeufe: `TelemetryPoint.run_id` ist ein
# Feld → Full-Point-Gleichheit braucht denselben Tag (Muster
# `test_scenario_commands_e2e`).
_RUN_ID = "slice-075-determinism"


def _drive_live(scenario: Scenario, buffer: InboundCommandBuffer) -> tuple[TelemetryPoint, ...]:
    """Fahrt den Lauf mit dem Buffer als `inbound_source` (A0i) + puffert den
    Write vor dem `_INBOUND_TICK_INDEX`-Tick."""
    loop = build_tick_loop(
        scenario,
        run_id=_RUN_ID,
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=scenario.simulation.seed),
        wiring=TickLoopWiring(inbound_source=buffer),
    )
    collected: list[TelemetryPoint] = []
    for index in range(EV_CHARGER_DEMO_TICKS):
        if index == _INBOUND_TICK_INDEX:
            buffer.enqueue(_TARGET, _COMMAND_TYPE, {"value": _CHARGE_POWER_KW})
        collected.extend(loop.tick().emitted_telemetry)
    return tuple(collected)


def _drive_replay(scenario: Scenario, *, run_id: str = _RUN_ID) -> tuple[TelemetryPoint, ...]:
    """Fahrt den materialisierten Lauf ueber den reinen A0s-Pfad (kein
    `inbound_source`)."""
    loop = build_tick_loop(
        scenario,
        run_id=run_id,
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=scenario.simulation.seed),
    )
    collected: list[TelemetryPoint] = []
    for _ in range(EV_CHARGER_DEMO_TICKS):
        collected.extend(loop.tick().emitted_telemetry)
    return tuple(collected)


def _materialized_scenario(
    raw: dict[str, object], commands: tuple[ScenarioCommand, ...]
) -> Scenario:
    command_dicts = [
        {
            "simulation_time": command.simulation_time,
            "target": command.target,
            "type": command.type,
            "payload": dict(command.payload),
        }
        for command in commands
    ]
    return load_scenario({**raw, "commands": command_dicts}).scenario


def _device_telemetry(
    telemetry: tuple[TelemetryPoint, ...], device_id: str
) -> tuple[TelemetryPoint, ...]:
    return tuple(point for point in telemetry if point.device_id == device_id)


def _values(telemetry: tuple[TelemetryPoint, ...], device_id: str, metric: str) -> list[Decimal]:
    return [p.value for p in telemetry if p.device_id == device_id and p.metric == metric]


def test_captured_inbound_stream_replays_byte_identical_and_faithful() -> None:
    raw = read_scenario_yaml(EV_CHARGER_DEMO_SCENARIO_PATH)
    base_scenario = load_scenario(raw).scenario

    # 1. „Live"-Lauf mit Inbound-Write (A0i).
    buffer = InboundCommandBuffer()
    live = _drive_live(base_scenario, buffer)

    # Der Write wurde erfasst — Source-of-Truth der Aufzeichnung (ADR 0076 §2.1).
    capture = buffer.capture()
    assert len(capture) == 1
    assert capture[0].resolved_sim_tick == 2000
    assert capture[0].target_device_id == _TARGET

    # 2. Materialisieren → Szenario-`commands`-Block.
    commands = materialize_inbound_writes(capture)
    materialized = _materialized_scenario(raw, commands)
    assert materialized.commands == commands  # 1:1-Materialisierung

    # 3. Replay 2x → byte-identisch (Determinismus; zwei unabhaengige TickLoop-
    #    Instanzen aus demselben `(Szenario+commands, Seed, tick_ms)`).
    replay_1 = _drive_replay(materialized)
    replay_2 = _drive_replay(materialized)
    assert replay_1 == replay_2

    # Der materialisierte Write treibt das Geraet sichtbar (nicht der Idle-Lauf).
    assert max(_values(replay_1, _TARGET, "power_kw")) > Decimal("0")

    # Faithful: die Telemetrie des kommandierten (agenten-freien) Geraets ist im
    # Replay deckungsgleich mit dem „Live"-Lauf (A0i-Effekt == A0s-Effekt).
    assert _device_telemetry(replay_1, _TARGET) == _device_telemetry(live, _TARGET)


def test_no_inbound_write_is_pin_neutral() -> None:
    # Ohne Inbound-Write bleibt der Lauf byte-identisch zum reinen Szenario-Lauf
    # (der Buffer ist leer → A0i No-op, keine Materialisierung).
    raw = read_scenario_yaml(EV_CHARGER_DEMO_SCENARIO_PATH)
    scenario = load_scenario(raw).scenario
    buffer = InboundCommandBuffer()
    loop = build_tick_loop(
        scenario,
        run_id="slice-075-idle",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=scenario.simulation.seed),
        wiring=TickLoopWiring(inbound_source=buffer),
    )
    with_source = tuple(
        point for _ in range(EV_CHARGER_DEMO_TICKS) for point in loop.tick().emitted_telemetry
    )
    plain = _drive_replay(scenario, run_id="slice-075-idle")
    assert with_source == plain
    assert buffer.capture() == ()
