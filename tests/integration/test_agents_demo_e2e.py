"""M3-Welle-4b End-to-End-Test fuer das Agents-Demo-Szenario.

Welle-4b-Abnahme (ADR 0027 §2.5 + §2.6, welle-4b.md §6):
- 60 Ticks ohne Crash mit zeitgesteuertem `RuleBasedAgent`.
- Snapshot enthaelt `agents.rule_based.bess-controller` als
  Sub-Snapshot (ADR 0027 §2.4).
- Snapshot/Restore-Roundtrip ist byte-stabil.
- Determinismus: zwei Laeufe mit gleichem Seed liefern identische
  `TickResult.emitted_telemetry`.
"""

from __future__ import annotations

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.scenario.loader import LoadedScenario, build_tick_loop
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop

from tests.integration._constants import AGENTS_DEMO_SCENARIO_PATH, AGENTS_DEMO_TICKS
from tests.integration._yaml_scenario_loader import load_yaml_scenario
from tests.unit.hexagon.ports.driven._fakes import FakeClock


def _build_loop(loaded: LoadedScenario, *, run_id: str = "welle-4b-demo") -> TickLoop:
    return build_tick_loop(
        loaded.scenario,
        run_id=run_id,
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed),
    )


def test_agents_demo_runs_60_ticks_without_crash() -> None:
    """ADR 0027 §2.6: 60 Ticks decken alle drei zeitgesteuerten
    Phasen ab (Idle/Charge/Discharge)."""
    loaded = load_yaml_scenario(AGENTS_DEMO_SCENARIO_PATH)
    loop = _build_loop(loaded)
    for _ in range(AGENTS_DEMO_TICKS):
        loop.tick()
    # 60 ticks gelaufen ohne Exception.
    assert loop.tick_count == AGENTS_DEMO_TICKS


def test_agents_demo_snapshot_contains_agent_instance_slot() -> None:
    """ADR 0027 §2.4: Snapshot enthaelt
    `agents.rule_based.bess-controller`."""
    loaded = load_yaml_scenario(AGENTS_DEMO_SCENARIO_PATH)
    loop = _build_loop(loaded)
    for _ in range(15):  # genug, um Phase 2 (Charge) zu erreichen
        loop.tick()
    snap = loop.snapshot()
    sub = snap["sub_snapshots"]
    assert isinstance(sub, dict)
    assert "agents.rule_based.bess-controller" in sub


def test_agents_demo_snapshot_roundtrip_is_byte_stable() -> None:
    """ADR 0027 §2.4 Roundtrip-Vertrag: Snapshot → from_snapshot →
    Snapshot ist byte-stabil.

    Welle-4b-Test-Pattern: wir injizieren die exakten Loop-Objekte
    (Devices/GridModel/Agents) wieder in `from_snapshot(...)`.
    Dies ist der Welle-4a-Resume-Pfad (ADR 0026 §2.6) — ein
    Frisch-Re-Build aus dem Scenario wuerde die Resume-Match-
    Checks scheitern lassen, weil PV/Battery-Initial-State sub-
    Random-Stream-abhaengig ist und der zwei Build-Operationen
    nicht byte-identisch macht. Echter Persistence-Roundtrip
    (canonical_json → bytes → zurueck) bleibt M6/M3-Welle-5
    Material.
    """
    loaded = load_yaml_scenario(AGENTS_DEMO_SCENARIO_PATH)
    loop_a = _build_loop(loaded)
    snap_before = loop_a.snapshot()
    restored = TickLoop.from_snapshot(
        snap_before,
        clock=FakeClock(),
        random=MersenneTwisterRandomPort(seed=loaded.scenario.simulation.seed),
        devices=loop_a._devices,  # type: ignore[attr-defined]
        grid_model=loop_a._grid_model,  # type: ignore[attr-defined]
        active_load_events=loaded.scenario.load_events,
        active_load_profiles=loaded.scenario.load_profiles,
        agents=loop_a._agents,  # type: ignore[attr-defined]
    )
    snap_after = restored.snapshot()
    assert snap_before == snap_after


def test_agents_demo_is_deterministic_across_two_runs() -> None:
    """ADR 0027 §2.3 Determinismus-Vertrag (GG-AGENT-003): zwei
    Laeufe mit gleichem Seed liefern identische Telemetry-Sequenzen.
    """
    loaded = load_yaml_scenario(AGENTS_DEMO_SCENARIO_PATH)

    def _collect_telemetry() -> tuple[object, ...]:
        loop = _build_loop(loaded)
        out: list[object] = []
        for _ in range(AGENTS_DEMO_TICKS):
            result = loop.tick()
            out.extend(result.emitted_telemetry)
        return tuple(out)

    a = _collect_telemetry()
    b = _collect_telemetry()
    assert a == b


def test_agents_demo_battery_soc_moves_during_charge_phase() -> None:
    """ADR 0027 §2.6 + Welle-4b-Review-Folge F-3 (2026-05-22):
    Demo-Test prueft, dass die `set_power_kw`-Commands aus
    Phase 2 (Charge, Tick 10..29) tatsaechlich auf der Battery
    wirksam sind — nicht nur "kein Crash". Battery-SoC nach
    Phase 2 muss sich von Initial unterscheiden.

    Ohne diese Assertion wuerde ein stilles Battery-Reject
    (z. B. Payload-Format-Drift) unbemerkt bleiben und das
    Welle-4b-Plumbing als gruen erscheinen, obwohl die
    Decision-Logik nichts bewirkt."""
    from grid_gym.hexagon.core.devices.battery import BatteryDevice

    loaded = load_yaml_scenario(AGENTS_DEMO_SCENARIO_PATH)
    loop = _build_loop(loaded)
    battery = next(
        d
        for d in loop._devices
        if isinstance(d, BatteryDevice)  # type: ignore[attr-defined]
    )
    initial_snapshot = battery.snapshot()
    initial_soc_kwh = initial_snapshot["soc_kwh"]
    # Fahre Phase 1 (Idle Tick 0..9) + Phase 2 (Charge Tick 10..29)
    # = 30 Ticks. Buffer-Drain-Delay (A0a wendet Tick-N-Command in
    # Tick N+1 an) verschiebt das Wirken um eine Tick — daher 31
    # Ticks fuer mindestens 20 Charge-Apply-Phasen.
    for _ in range(31):
        loop.tick()
    after_charge_snapshot = battery.snapshot()
    after_charge_soc_kwh = after_charge_snapshot["soc_kwh"]
    assert after_charge_soc_kwh != initial_soc_kwh, (
        f"Battery-SoC nach Charge-Phase sollte sich von Initial "
        f"({initial_soc_kwh}) unterscheiden — sah {after_charge_soc_kwh}. "
        "Stilles Battery-Reject? Welle-4b-Demo-Plumbing nicht wirksam."
    )
