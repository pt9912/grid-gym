"""M3-Welle-4a-Tests fuer Agent-Foundation-State-Snapshot
(ADR 0026 §2.6).

Pinnt:
- `agent_bus` als Sub-Snapshot, wenn `_agent_bus is not None`.
- `pending_agent_commands` als Sub-Snapshot, wenn Buffer nicht leer.
- `CommandResult`-String-Roundtrip.
- `from_snapshot(..., devices=..., agents=...)` mit Resume-Match-
  Checks fuer Devices.
- Auto-Bus-Praezedenz bei Resume ohne `agent_bus`-Sub-Snapshot.
- Backward-Compat: alte Snapshots ohne Agent-Sub-Snapshots
  bleiben restorable.
"""

from __future__ import annotations

import pytest

from grid_gym.hexagon.core.agents import AgentMessageBus
from grid_gym.hexagon.core.domain.agent_message import AgentMessage
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.errors import (
    TickLoopAgentSnapshotInvalidCommandResultError,
    TickLoopAgentSnapshotWrongTypeError,
)
from grid_gym.hexagon.core.devices.pv import PvDevice
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.core.simulation.test_tick_loop_welle_4a_agent import (
    _OrderRecordingAgent,
)
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


def _make_loop(**kwargs: object) -> TickLoop:
    base: dict[str, object] = {
        "run_id": "welle-4a-snapshot",
        "tick_ms": 1000,
        "clock": FakeClock(),
        "random": FixedSeedRandom(seed=42),
        "scheduler": Scheduler(),
    }
    base.update(kwargs)
    return TickLoop(**base)  # type: ignore[arg-type]


def _command(command_id: str, target: str = "pv-1") -> Command:
    from decimal import Decimal

    return Command(
        command_id=command_id,
        simulation_time=1000,
        target_device_id=target,
        type="set_power_kw",
        payload={"power_kw": Decimal("5")},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _initialized_pv_device(device_id: str = "pv-1") -> PvDevice:
    from decimal import Decimal

    device = PvDevice()
    device.initialize(
        ScenarioDevice(
            id=device_id,
            type="pv",
            params={"rated_power_kw": Decimal("10")},
        ),
        FixedSeedRandom(seed=1),
    )
    device.set_run_id("welle-4a-snapshot")
    return device


def test_snapshot_omits_agent_bus_when_none() -> None:
    """ADR 0026 §2.6: `agent_bus`-Sub-Snapshot nur, wenn
    `_agent_bus is not None`."""
    loop = _make_loop()
    snapshot = loop.snapshot()
    sub_snapshots = snapshot["sub_snapshots"]
    assert isinstance(sub_snapshots, dict)
    assert "agent_bus" not in sub_snapshots
    assert "pending_agent_commands" not in sub_snapshots


def test_snapshot_includes_agent_bus_when_present() -> None:
    """ADR 0026 §2.6: `agent_bus`-Sub-Snapshot wird eingehaengt,
    sobald `_agent_bus is not None`."""
    bus = AgentMessageBus()
    loop = _make_loop(agent_bus=bus)
    snapshot = loop.snapshot()
    sub_snapshots = snapshot["sub_snapshots"]
    assert isinstance(sub_snapshots, dict)
    assert "agent_bus" in sub_snapshots


def test_snapshot_serializes_pending_commands_with_string_result() -> None:
    """ADR 0026 §2.6: `result` wird als `CommandResult`-String
    serialisiert."""
    device = _initialized_pv_device("pv-1")
    recorder: list[str] = []
    agent = _OrderRecordingAgent("agent-x", recorder)
    cmd = _command("cmd-1")
    agent.queue_emission((cmd,))
    loop = _make_loop(
        devices=(device,),
        agent_bus=AgentMessageBus(),
        agents=(agent,),
    )
    loop.tick()  # Agent emittiert Command in D2 → Buffer.
    assert loop.pending_agent_commands == (cmd,)
    snapshot = loop.snapshot()
    sub_snapshots = snapshot["sub_snapshots"]
    assert isinstance(sub_snapshots, dict)
    pending = sub_snapshots["pending_agent_commands"]
    assert isinstance(pending, dict)
    commands = pending["commands"]
    assert isinstance(commands, tuple)
    assert len(commands) == 1
    serialized = commands[0]
    assert serialized["result"] == "IGNORED"
    assert serialized["command_id"] == "cmd-1"


def test_from_snapshot_restores_pending_commands() -> None:
    """ADR 0026 §2.6 Roundtrip: `from_snapshot(...)` rekonstruiert
    `_pending_agent_commands` aus Sub-Snapshot."""
    device = _initialized_pv_device("pv-1")
    recorder: list[str] = []
    agent = _OrderRecordingAgent("agent-x", recorder)
    cmd = _command("cmd-1")
    agent.queue_emission((cmd,))
    loop = _make_loop(
        devices=(device,),
        agent_bus=AgentMessageBus(),
        agents=(agent,),
    )
    loop.tick()  # Buffer hat 1 Command
    snapshot = loop.snapshot()
    # Restore via from_snapshot mit den gleichen Runtime-Dependencies.
    clock2 = FakeClock()
    clock2.advance(loop._clock.now())  # type: ignore[attr-defined]
    # Random-Match-Check via snapshot_as_mapping; FixedSeedRandom
    # ist deterministisch mit gleichem Seed.
    random2 = FixedSeedRandom(seed=42)
    restored_device = _initialized_pv_device("pv-1")
    # Device-Snapshot-Match: das injizierte Device muss in seinem
    # initialen State sein, NACHDEM die Tick im Original lief.
    # Da der Test nur 1 Tick fuer den Buffer braucht, ist das
    # device hier nicht im selben State. Wir muessen das Device
    # snapshot-konsistent restoren.
    restored_device_snapshot = device.snapshot()
    restored_device = type(device).from_snapshot(restored_device_snapshot)
    restored_device.set_run_id("welle-4a-snapshot")
    restored_agent = _OrderRecordingAgent("agent-x", [])
    restored = TickLoop.from_snapshot(
        snapshot,
        clock=clock2,
        random=random2,
        devices=(restored_device,),
        agents=(restored_agent,),
    )
    assert len(restored.pending_agent_commands) == 1
    assert restored.pending_agent_commands[0].command_id == "cmd-1"


def test_from_snapshot_rejects_unknown_command_result() -> None:
    """ADR 0026 §2.6: unbekannter `CommandResult`-String wirft
    `TickLoopAgentSnapshotInvalidCommandResultError`."""
    loop = _make_loop()
    snapshot = dict(loop.snapshot())
    sub_snapshots = dict(snapshot["sub_snapshots"])  # type: ignore[arg-type]
    sub_snapshots["pending_agent_commands"] = {
        "version": 1,
        "commands": [
            {
                "command_id": "cmd-x",
                "simulation_time": 1000,
                "target_device_id": "null-1",
                "type": "set_power_kw",
                "payload": {"power_kw": 5},
                "validation_status": "validated",
                "result": "MOON_RESULT",  # unbekannt
            },
        ],
    }
    snapshot["sub_snapshots"] = sub_snapshots
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    with pytest.raises(TickLoopAgentSnapshotInvalidCommandResultError):
        TickLoop.from_snapshot(snapshot, clock=clock2, random=random2)


def test_from_snapshot_rejects_pending_commands_wrong_type() -> None:
    """ADR 0026 §2.6: `pending_agent_commands` muss Mapping sein."""
    loop = _make_loop()
    snapshot = dict(loop.snapshot())
    sub_snapshots = dict(snapshot["sub_snapshots"])  # type: ignore[arg-type]
    sub_snapshots["pending_agent_commands"] = "not a mapping"
    snapshot["sub_snapshots"] = sub_snapshots
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    with pytest.raises(TickLoopAgentSnapshotWrongTypeError):
        TickLoop.from_snapshot(snapshot, clock=clock2, random=random2)


def test_from_snapshot_auto_bus_for_old_snapshot_with_agents() -> None:
    """ADR 0026 §2.6 Auto-Bus-Praezedenz: alte Snapshots ohne
    `agent_bus`-Sub-Snapshot mit `agents != ()` injiziert bekommen
    einen leeren `AgentMessageBus` (Konstruktor-Auto-Bus-Regel)."""
    # Alter Snapshot ohne agent_bus-Sub-Snapshot (welle-3-style).
    loop = _make_loop()
    snapshot = loop.snapshot()
    # Resume mit injizierten Agents → Auto-Bus.
    recorder: list[str] = []
    agent = _OrderRecordingAgent("agent-x", recorder)
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    restored = TickLoop.from_snapshot(snapshot, clock=clock2, random=random2, agents=(agent,))
    # Auto-Bus aktiv: `_agent_bus` ist nicht None.
    assert restored._agent_bus is not None  # type: ignore[attr-defined]
    # Bus ist leer (frisch erzeugt).
    assert restored._agent_bus.next_sequence == 0  # type: ignore[attr-defined,union-attr]


def test_from_snapshot_backward_compat_without_agents() -> None:
    """ADR 0026 §2.6 Backward-Compat: alte Snapshots ohne
    `agent_bus` und ohne `agents=...`-Injektion folgen
    Welle-6a-Pfad (`agent_bus=None`)."""
    loop = _make_loop()
    snapshot = loop.snapshot()
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    restored = TickLoop.from_snapshot(snapshot, clock=clock2, random=random2)
    assert restored._agent_bus is None  # type: ignore[attr-defined]
    assert restored.pending_agent_commands == ()


def test_from_snapshot_rejects_agent_bus_wrong_type() -> None:
    """ADR 0026 §2.6: `agent_bus`-Sub-Snapshot muss Mapping sein."""
    loop = _make_loop()
    snapshot = dict(loop.snapshot())
    sub_snapshots = dict(snapshot["sub_snapshots"])  # type: ignore[arg-type]
    sub_snapshots["agent_bus"] = "not a mapping"
    snapshot["sub_snapshots"] = sub_snapshots
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    with pytest.raises(TickLoopAgentSnapshotWrongTypeError):
        TickLoop.from_snapshot(snapshot, clock=clock2, random=random2)


def test_from_snapshot_rejects_pending_commands_missing_keys() -> None:
    """ADR 0026 §2.6: `pending_agent_commands` Pflicht-Keys
    `version`/`commands` muessen vorhanden sein."""
    from grid_gym.hexagon.core.errors import (
        TickLoopAgentSnapshotMissingKeysError,
    )

    loop = _make_loop()
    snapshot = dict(loop.snapshot())
    sub_snapshots = dict(snapshot["sub_snapshots"])  # type: ignore[arg-type]
    sub_snapshots["pending_agent_commands"] = {"version": 1}  # missing commands
    snapshot["sub_snapshots"] = sub_snapshots
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    with pytest.raises(TickLoopAgentSnapshotMissingKeysError):
        TickLoop.from_snapshot(snapshot, clock=clock2, random=random2)


def test_from_snapshot_rejects_command_entry_missing_field() -> None:
    """ADR 0026 §2.6: Pflichtfelder pro Command-Eintrag."""
    from grid_gym.hexagon.core.errors import (
        TickLoopAgentSnapshotMissingKeysError,
    )

    loop = _make_loop()
    snapshot = dict(loop.snapshot())
    sub_snapshots = dict(snapshot["sub_snapshots"])  # type: ignore[arg-type]
    sub_snapshots["pending_agent_commands"] = {
        "version": 1,
        "commands": [{"command_id": "x"}],  # missing all other fields
    }
    snapshot["sub_snapshots"] = sub_snapshots
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    with pytest.raises(TickLoopAgentSnapshotMissingKeysError):
        TickLoop.from_snapshot(snapshot, clock=clock2, random=random2)


def test_from_snapshot_rejects_command_entry_wrong_type_per_field() -> None:
    """ADR 0026 §2.6: pro Pflichtfeld Type-Check."""
    base_command = {
        "command_id": "x",
        "simulation_time": 1000,
        "target_device_id": "pv-1",
        "type": "set_power_kw",
        "payload": {},
        "validation_status": "ok",
        "result": "IGNORED",
    }
    for field, bad_value in [
        ("command_id", 123),
        ("simulation_time", "1000"),
        ("target_device_id", 123),
        ("type", 123),
        ("payload", "not-mapping"),
        ("validation_status", 123),
        ("result", 123),
    ]:
        bad_command = dict(base_command)
        bad_command[field] = bad_value
        loop = _make_loop()
        snapshot = dict(loop.snapshot())
        sub_snapshots = dict(snapshot["sub_snapshots"])  # type: ignore[arg-type]
        sub_snapshots["pending_agent_commands"] = {
            "version": 1,
            "commands": [bad_command],
        }
        snapshot["sub_snapshots"] = sub_snapshots
        clock2 = FakeClock()
        random2 = FixedSeedRandom(seed=42)
        with pytest.raises(TickLoopAgentSnapshotWrongTypeError):
            TickLoop.from_snapshot(snapshot, clock=clock2, random=random2)


def test_from_snapshot_rejects_command_entry_not_mapping() -> None:
    """ADR 0026 §2.6: Eintrag in `commands` muss Mapping sein."""
    loop = _make_loop()
    snapshot = dict(loop.snapshot())
    sub_snapshots = dict(snapshot["sub_snapshots"])  # type: ignore[arg-type]
    sub_snapshots["pending_agent_commands"] = {
        "version": 1,
        "commands": ["not a mapping"],
    }
    snapshot["sub_snapshots"] = sub_snapshots
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    with pytest.raises(TickLoopAgentSnapshotWrongTypeError):
        TickLoop.from_snapshot(snapshot, clock=clock2, random=random2)


def test_from_snapshot_rejects_pending_commands_wrong_commands_type() -> None:
    """ADR 0026 §2.6: `commands` muss Sequence sein (kein str)."""
    loop = _make_loop()
    snapshot = dict(loop.snapshot())
    sub_snapshots = dict(snapshot["sub_snapshots"])  # type: ignore[arg-type]
    sub_snapshots["pending_agent_commands"] = {
        "version": 1,
        "commands": "not a list",
    }
    snapshot["sub_snapshots"] = sub_snapshots
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    with pytest.raises(TickLoopAgentSnapshotWrongTypeError):
        TickLoop.from_snapshot(snapshot, clock=clock2, random=random2)


def test_from_snapshot_rejects_pending_commands_wrong_version_type() -> None:
    """ADR 0026 §2.6: `version` muss int sein."""
    loop = _make_loop()
    snapshot = dict(loop.snapshot())
    sub_snapshots = dict(snapshot["sub_snapshots"])  # type: ignore[arg-type]
    sub_snapshots["pending_agent_commands"] = {
        "version": "1",  # str, not int
        "commands": [],
    }
    snapshot["sub_snapshots"] = sub_snapshots
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    with pytest.raises(TickLoopAgentSnapshotWrongTypeError):
        TickLoop.from_snapshot(snapshot, clock=clock2, random=random2)


def test_from_snapshot_grid_model_mismatch_raises() -> None:
    """ADR 0026 §2.6: injiziertes `grid_model.snapshot()` muss zum
    persistierten Sub-Snapshot passen."""
    from decimal import Decimal

    from grid_gym.hexagon.core.errors import (
        TickLoopAgentSnapshotGridModelMismatchError,
    )
    from grid_gym.hexagon.core.grid_model import GridModelBilanz, GridModelConfig

    config = GridModelConfig(
        nominal_frequency_hz=Decimal("50"),
        frequency_sensitivity_hz_per_kw=Decimal("0.001"),
        frequency_clamp_min_hz=Decimal("45"),
        frequency_clamp_max_hz=Decimal("55"),
        nominal_voltage_v=Decimal("400"),
        voltage_sensitivity_v_per_kw=Decimal("0.1"),
        voltage_clamp_min_v=Decimal("280"),
        voltage_clamp_max_v=Decimal("520"),
    )
    grid_model = GridModelBilanz(config)
    loop = _make_loop(grid_model=grid_model)
    snapshot = loop.snapshot()
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    # Fresh grid_model in geaendertem State — Mismatch.
    different_grid = GridModelBilanz(config)
    different_grid.update(
        generation_kw=Decimal("50"),
        load_kw=Decimal("10"),
        storage_kw=Decimal("0"),
        grid_connection_kw=Decimal("0"),
    )
    with pytest.raises(TickLoopAgentSnapshotGridModelMismatchError):
        TickLoop.from_snapshot(snapshot, clock=clock2, random=random2, grid_model=different_grid)


def test_from_snapshot_load_overlay_mismatch_raises() -> None:
    """ADR 0026 §2.6: nicht-leere injizierte LoadOverlays muessen
    bei vorhandenem `grid_model`-Sub-Snapshot zum persistierten
    State passen."""
    from decimal import Decimal

    from grid_gym.hexagon.core.errors import (
        TickLoopAgentSnapshotLoadOverlayMismatchError,
    )
    from grid_gym.hexagon.core.grid_model import GridModelBilanz, GridModelConfig
    from grid_gym.hexagon.core.grid_model.loads import LoadEvent, LoadProfile

    config = GridModelConfig(
        nominal_frequency_hz=Decimal("50"),
        frequency_sensitivity_hz_per_kw=Decimal("0.001"),
        frequency_clamp_min_hz=Decimal("45"),
        frequency_clamp_max_hz=Decimal("55"),
        nominal_voltage_v=Decimal("400"),
        voltage_sensitivity_v_per_kw=Decimal("0.1"),
        voltage_clamp_min_v=Decimal("280"),
        voltage_clamp_max_v=Decimal("520"),
    )
    event_a = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("10"),
        target_device_id="load-a",
        power_kw=Decimal("100"),
    )
    event_b = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("10"),
        target_device_id="load-b",
        power_kw=Decimal("200"),
    )
    grid_model = GridModelBilanz(config, active_load_events=(event_a,))
    loop = _make_loop(grid_model=grid_model)
    snapshot = loop.snapshot()
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    # Mismatched events injected.
    with pytest.raises(TickLoopAgentSnapshotLoadOverlayMismatchError):
        TickLoop.from_snapshot(
            snapshot,
            clock=clock2,
            random=random2,
            active_load_events=(event_b,),
        )


def test_from_snapshot_load_profile_mismatch_raises() -> None:
    """ADR 0026 §2.6: gleiche Mismatch-Logik fuer load_profiles."""
    from decimal import Decimal

    from grid_gym.hexagon.core.errors import (
        TickLoopAgentSnapshotLoadOverlayMismatchError,
    )
    from grid_gym.hexagon.core.grid_model import GridModelBilanz, GridModelConfig
    from grid_gym.hexagon.core.grid_model.loads import LoadProfile

    config = GridModelConfig(
        nominal_frequency_hz=Decimal("50"),
        frequency_sensitivity_hz_per_kw=Decimal("0.001"),
        frequency_clamp_min_hz=Decimal("45"),
        frequency_clamp_max_hz=Decimal("55"),
        nominal_voltage_v=Decimal("400"),
        voltage_sensitivity_v_per_kw=Decimal("0.1"),
        voltage_clamp_min_v=Decimal("280"),
        voltage_clamp_max_v=Decimal("520"),
    )
    profile_a = LoadProfile(
        target_device_id="load-a",
        tick_values=(Decimal("100"),),
        tick_ms=1000,
    )
    profile_b = LoadProfile(
        target_device_id="load-b",
        tick_values=(Decimal("200"),),
        tick_ms=1000,
    )
    grid_model = GridModelBilanz(config, active_load_profiles=(profile_a,))
    loop = _make_loop(grid_model=grid_model)
    snapshot = loop.snapshot()
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    with pytest.raises(TickLoopAgentSnapshotLoadOverlayMismatchError):
        TickLoop.from_snapshot(
            snapshot,
            clock=clock2,
            random=random2,
            active_load_profiles=(profile_b,),
        )


def test_from_snapshot_load_overlay_match_passes() -> None:
    """ADR 0026 §2.6: matching LoadOverlays geht durch."""
    from decimal import Decimal

    from grid_gym.hexagon.core.grid_model import GridModelBilanz, GridModelConfig
    from grid_gym.hexagon.core.grid_model.loads import LoadEvent

    config = GridModelConfig(
        nominal_frequency_hz=Decimal("50"),
        frequency_sensitivity_hz_per_kw=Decimal("0.001"),
        frequency_clamp_min_hz=Decimal("45"),
        frequency_clamp_max_hz=Decimal("55"),
        nominal_voltage_v=Decimal("400"),
        voltage_sensitivity_v_per_kw=Decimal("0.1"),
        voltage_clamp_min_v=Decimal("280"),
        voltage_clamp_max_v=Decimal("520"),
    )
    event = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("10"),
        target_device_id="load-a",
        power_kw=Decimal("100"),
    )
    grid_model = GridModelBilanz(config, active_load_events=(event,))
    loop = _make_loop(grid_model=grid_model)
    snapshot = loop.snapshot()
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    # Same grid_model + same events → kein Mismatch.
    TickLoop.from_snapshot(
        snapshot,
        clock=clock2,
        random=random2,
        active_load_events=(event,),
    )


def test_from_snapshot_device_mismatch_raises() -> None:
    """ADR 0026 §2.6: injizierte Device-IDs muessen passen."""
    from grid_gym.hexagon.core.errors import (
        TickLoopAgentSnapshotDeviceMismatchError,
    )

    device = _initialized_pv_device("pv-1")
    loop = _make_loop(devices=(device,))
    snapshot = loop.snapshot()
    clock2 = FakeClock()
    clock2.advance(loop._clock.now()) if loop._clock.now() > 0 else None  # type: ignore[attr-defined]
    random2 = FixedSeedRandom(seed=42)
    # Inject a different PV device with different ID — mismatch.
    different_device = _initialized_pv_device("pv-2")
    with pytest.raises(TickLoopAgentSnapshotDeviceMismatchError):
        TickLoop.from_snapshot(snapshot, clock=clock2, random=random2, devices=(different_device,))


def test_from_snapshot_rejects_extra_persisted_devices() -> None:
    """ADR 0026 §2.6 + Welle-4a-Review-Folge I-1 (2026-05-22): wenn
    der Snapshot mehr Devices persistiert als injiziert werden, wirft
    `TickLoopAgentSnapshotDeviceMismatchError` — kein stiller Subset-
    Restore."""
    from grid_gym.hexagon.core.errors import (
        TickLoopAgentSnapshotDeviceMismatchError,
    )

    device_a = _initialized_pv_device("pv-1")
    device_b = _initialized_pv_device("pv-2")
    loop = _make_loop(devices=(device_a, device_b))
    snapshot = loop.snapshot()
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    # Nur 1 von 2 Devices injizieren → bidirektionaler Check schlaegt zu.
    only_a = _initialized_pv_device("pv-1")
    with pytest.raises(TickLoopAgentSnapshotDeviceMismatchError, match="pv-2"):
        TickLoop.from_snapshot(snapshot, clock=clock2, random=random2, devices=(only_a,))


def test_from_snapshot_grid_model_resume_tolerates_tuple_list_drift() -> None:
    """ADR 0026 §2.6 + Welle-4a-Review-Folge I-2 (2026-05-22): nested
    `tuple` im live-Snapshot vs. `list` im persistierten Snapshot ist
    nach canonical_json-Vergleich equivalent — kein False-Positive-
    Mismatch nach Persistence-Roundtrip."""
    from decimal import Decimal

    from grid_gym.hexagon.core.grid_model import GridModelBilanz, GridModelConfig
    from grid_gym.hexagon.core.grid_model.loads import LoadEvent

    config = GridModelConfig(
        nominal_frequency_hz=Decimal("50"),
        frequency_sensitivity_hz_per_kw=Decimal("0.001"),
        frequency_clamp_min_hz=Decimal("45"),
        frequency_clamp_max_hz=Decimal("55"),
        nominal_voltage_v=Decimal("400"),
        voltage_sensitivity_v_per_kw=Decimal("0.1"),
        voltage_clamp_min_v=Decimal("280"),
        voltage_clamp_max_v=Decimal("520"),
    )
    event = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("10"),
        target_device_id="load-a",
        power_kw=Decimal("100"),
    )
    grid_model = GridModelBilanz(config, active_load_events=(event,))
    loop = _make_loop(grid_model=grid_model)
    snapshot = dict(loop.snapshot())
    sub_snapshots = dict(snapshot["sub_snapshots"])  # type: ignore[arg-type]
    # Simuliere Persistence-Roundtrip: GridModel-Sub-Snapshot in eine
    # Form bringen, in der nested tuples zu lists werden — Drift, die
    # `dict() != dict()` als Mismatch falsch-positiv markieren wuerde.
    grid_state = dict(sub_snapshots["grid_model"])  # type: ignore[arg-type]
    if "active_load_events" in grid_state:
        grid_state["active_load_events"] = [
            dict(entry)
            for entry in grid_state["active_load_events"]  # type: ignore[union-attr]
        ]
    sub_snapshots["grid_model"] = grid_state
    snapshot["sub_snapshots"] = sub_snapshots
    clock2 = FakeClock()
    random2 = FixedSeedRandom(seed=42)
    # Fresh GridModel mit identischem State (tuple in live-Snapshot).
    same_grid = GridModelBilanz(config, active_load_events=(event,))
    # Darf NICHT raisen — canonical_json normalisiert tuple/list.
    TickLoop.from_snapshot(
        snapshot,
        clock=clock2,
        random=random2,
        grid_model=same_grid,
        active_load_events=(event,),
    )
