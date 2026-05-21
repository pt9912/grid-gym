"""Welle-6b-Loader-Tests (ADR 0021).

Pinnt die `build_devices(...)`-Factory + `build_tick_loop(...)`-
Builder-Vertraege:

- Device-Factory-Dispatch nach `ScenarioDevice.type`.
- SmartMeter `attach_sources(...)`-Verdrahtung nach allen
  Devices.
- `ScenarioUnknownDeviceTypeError` fuer unbekannten Typ.
- `ScenarioMissingSourceDeviceError` fuer SmartMeter ohne
  passende Quell-Device-ID.
- `build_tick_loop(...)` reicht GridModelConfig + LoadEvents +
  LoadProfiles an den `TickLoop` durch.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.devices.pv import PvDevice
from grid_gym.hexagon.core.devices.smart_meter import SmartMeterDevice
from grid_gym.hexagon.core.domain.scenario import (
    Scenario,
    ScenarioDevice,
    ScenarioMetadata,
    ScenarioSimulation,
)
from grid_gym.hexagon.core.errors import (
    ScenarioInvalidLoadTargetError,
    ScenarioMissingSourceDeviceError,
    ScenarioUnknownDeviceTypeError,
)
from grid_gym.hexagon.core.grid_model import GridModelConfig
from grid_gym.hexagon.core.grid_model.loads import LoadEvent, LoadProfile
from grid_gym.hexagon.core.scenario.loader import (
    build_devices,
    build_tick_loop,
    load_scenario,
    _parse_grid_model_config,
    parse_load_events,
    parse_load_profiles,
)
from tests.unit.hexagon.ports.driven._fakes import FakeClock

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _pv_device(device_id: str = "pv-1") -> ScenarioDevice:
    return ScenarioDevice(
        id=device_id,
        type="pv",
        params={"rated_power_kw": Decimal("500")},
    )


def _load_device(device_id: str = "load-1") -> ScenarioDevice:
    return ScenarioDevice(
        id=device_id,
        type="load",
        params={"rated_power_kw": Decimal("300")},
    )


def _grid_device(device_id: str = "grid-1") -> ScenarioDevice:
    return ScenarioDevice(
        id=device_id,
        type="grid_connection",
        params={
            "nominal_voltage_v": Decimal("400"),
            "max_import_kw": Decimal("1000"),
            "max_export_kw": Decimal("1000"),
        },
    )


def _battery_device(device_id: str = "battery-1") -> ScenarioDevice:
    return ScenarioDevice(
        id=device_id,
        type="battery",
        params={
            "capacity_kwh": Decimal("100"),
            "initial_soc_pct": Decimal("50"),
            "min_soc_pct": Decimal("0"),
            "max_soc_pct": Decimal("100"),
            "max_charge_kw": Decimal("50"),
            "max_discharge_kw": Decimal("50"),
            "charge_efficiency": Decimal("1"),
            "discharge_efficiency": Decimal("1"),
            "ramp_kw_per_s": Decimal("100"),
        },
    )


def _smart_meter(
    device_id: str = "meter-1",
    aggregate_ids: tuple[str, ...] = ("pv-1",),
) -> ScenarioDevice:
    return ScenarioDevice(
        id=device_id,
        type="smart_meter",
        params={
            "aggregate_device_ids": list(aggregate_ids),
            "aggregate_metric_name": "power_kw",
        },
    )


def _grid_model_config() -> GridModelConfig:
    return GridModelConfig(
        nominal_frequency_hz=Decimal("50"),
        frequency_sensitivity_hz_per_kw=Decimal("0.001"),
        frequency_clamp_min_hz=Decimal("45"),
        frequency_clamp_max_hz=Decimal("55"),
        nominal_voltage_v=Decimal("400"),
        voltage_sensitivity_v_per_kw=Decimal("0.1"),
        voltage_clamp_min_v=Decimal("280"),
        voltage_clamp_max_v=Decimal("520"),
    )


def _scenario(
    devices: tuple[ScenarioDevice, ...] = (),
    *,
    tick_ms: int = 1000,
    grid_model_config: GridModelConfig | None = None,
    load_events: tuple[LoadEvent, ...] = (),
    load_profiles: tuple[LoadProfile, ...] = (),
) -> Scenario:
    return Scenario(
        schema_version="grid-gym.scenario.v1",
        metadata=ScenarioMetadata(id="welle-6b", name="Welle 6b Test"),
        simulation=ScenarioSimulation(tick_ms=tick_ms, duration_s=60, seed=42),
        devices=devices,
        events=(),
        replay=None,
        faults=(),
        grid_model_config=grid_model_config,
        load_events=load_events,
        load_profiles=load_profiles,
    )


# ---------------------------------------------------------------------------
# build_devices: Factory-Dispatch (ADR 0021 §2.2)
# ---------------------------------------------------------------------------


def test_build_devices_dispatches_all_known_types() -> None:
    """ADR 0021 §2.2: Factory-Map deckt alle Welle-6b-Typen ab."""
    random_root = MersenneTwisterRandomPort(seed=42)
    devices = build_devices(
        (
            _pv_device("pv-1"),
            _load_device("load-1"),
            _grid_device("grid-1"),
            _battery_device("battery-1"),
            _smart_meter("meter-1", aggregate_ids=("pv-1",)),
        ),
        random_root,
    )
    assert len(devices) == 5
    assert isinstance(devices[0], PvDevice)
    assert isinstance(devices[1], LoadDevice)
    assert isinstance(devices[2], GridConnectionDevice)
    # Battery class assertion
    from grid_gym.hexagon.core.devices.battery import BatteryDevice

    assert isinstance(devices[3], BatteryDevice)
    assert isinstance(devices[4], SmartMeterDevice)


def test_build_devices_preserves_scenario_order() -> None:
    """ADR 0021 §2.2 + §2.9: Devices kommen in Scenario-Definitions-
    Reihenfolge zurueck (Determinismus-Pflicht)."""
    random_root = MersenneTwisterRandomPort(seed=42)
    devices = build_devices(
        (_load_device("load-1"), _pv_device("pv-1")),
        random_root,
    )
    assert devices[0].device_id == "load-1"
    assert devices[1].device_id == "pv-1"


def test_build_devices_raises_on_unknown_type() -> None:
    """ADR 0021 §2.2: Unbekannter `ScenarioDevice.type` →
    `ScenarioUnknownDeviceTypeError` (statt KeyError oder silent-
    Skip)."""
    random_root = MersenneTwisterRandomPort(seed=42)
    unknown = ScenarioDevice(id="x-1", type="hydroelectric", params={})
    with pytest.raises(ScenarioUnknownDeviceTypeError):
        build_devices((unknown,), random_root)


def test_build_devices_attaches_smart_meter_sources() -> None:
    """ADR 0021 §2.2 + ADR 0018 §2.3: SmartMeter wird per
    `attach_sources(...)` mit dem Devices-Mapping verdrahtet."""
    random_root = MersenneTwisterRandomPort(seed=42)
    devices = build_devices(
        (
            _pv_device("pv-1"),
            _smart_meter("meter-1", aggregate_ids=("pv-1",)),
        ),
        random_root,
    )
    meter = devices[1]
    assert isinstance(meter, SmartMeterDevice)
    # Sanity-Check: erste Tick darf nicht knallen (sources gesetzt).
    from grid_gym.hexagon.core.domain.device import DeviceTickContext

    pv = devices[0]
    assert isinstance(pv, PvDevice)
    pv.tick(DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000))
    meter.tick(DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000))


def test_build_devices_raises_when_smart_meter_source_missing() -> None:
    """ADR 0021 §2.2: SmartMeter referenziert eine Geraete-ID, die
    nicht in `scenario.devices` ist → Fail-fast vor dem ersten
    Tick mit `ScenarioMissingSourceDeviceError`."""
    random_root = MersenneTwisterRandomPort(seed=42)
    with pytest.raises(ScenarioMissingSourceDeviceError):
        build_devices(
            (_smart_meter("meter-1", aggregate_ids=("ghost-source",)),),
            random_root,
        )


# ---------------------------------------------------------------------------
# build_tick_loop: Builder-Verdrahtung (ADR 0021 §2.4)
# ---------------------------------------------------------------------------


def test_build_tick_loop_without_grid_model_keeps_bilanz_none() -> None:
    """ADR 0021 §2.4: ohne `scenario.grid_model_config` bleibt
    `TickLoop._grid_model = None`. M1-Welle-4-Pfad bleibt intakt."""
    scenario = _scenario(devices=(_pv_device(),))
    loop = build_tick_loop(
        scenario,
        run_id="run-6b",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
    )
    assert loop._grid_model is None  # type: ignore[attr-defined]


def test_build_tick_loop_constructs_grid_model_when_config_present() -> None:
    """ADR 0021 §2.4: `scenario.grid_model_config` → produktiver
    `GridModelBilanz` im TickLoop."""
    scenario = _scenario(
        devices=(_pv_device(),),
        grid_model_config=_grid_model_config(),
    )
    loop = build_tick_loop(
        scenario,
        run_id="run-6b",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
    )
    assert loop._grid_model is not None  # type: ignore[attr-defined]


def test_build_tick_loop_forwards_run_id_and_tick_ms() -> None:
    """ADR 0021 §2.4: Builder reicht run_id durch + entnimmt
    tick_ms aus `scenario.simulation`."""
    scenario = _scenario(devices=(_pv_device(),), tick_ms=100)
    loop = build_tick_loop(
        scenario,
        run_id="run-builder",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
    )
    assert loop.run_id == "run-builder"
    assert loop.tick_ms == 100


def test_build_tick_loop_forwards_load_events_and_profiles() -> None:
    """ADR 0021 §2.4 + §2.5: LoadEvents/Profiles aus Scenario landen
    in den TickLoop-Konstruktor-Feldern."""
    event = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("10"),
        target_device_id="load-1",
        power_kw=Decimal("250"),
    )
    profile = LoadProfile(
        target_device_id="load-1",
        tick_values=(Decimal("100"), Decimal("200")),
        tick_ms=1000,
    )
    scenario = _scenario(
        devices=(_load_device("load-1"),),
        load_events=(event,),
        load_profiles=(profile,),
    )
    loop = build_tick_loop(
        scenario,
        run_id="run-6b",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
    )
    assert loop._active_load_events == (event,)  # type: ignore[attr-defined]
    assert loop._active_load_profiles == (profile,)  # type: ignore[attr-defined]


def test_build_tick_loop_rejects_load_event_on_pv_target() -> None:
    """Welle-6b-Review M-6 (ADR 0021 §2.5/§2.7): LoadEvent darf nur
    auf LoadDevice oder GridConnectionDevice zielen. PV-Target →
    `ScenarioInvalidLoadTargetError` im Builder."""
    scenario = _scenario(
        devices=(_pv_device("pv-1"),),
        load_events=(
            LoadEvent(
                start_s=Decimal("0"),
                duration_s=Decimal("1"),
                target_device_id="pv-1",
                power_kw=Decimal("100"),
            ),
        ),
    )
    with pytest.raises(ScenarioInvalidLoadTargetError):
        build_tick_loop(
            scenario,
            run_id="run-6b",
            clock=FakeClock(),
            random_root=MersenneTwisterRandomPort(seed=42),
        )


def test_build_tick_loop_rejects_load_profile_on_battery_target() -> None:
    """Welle-6b-Review M-6: LoadProfile auf Battery-Target ist
    unzulaessig — Fail-fast im Builder."""
    scenario = _scenario(
        devices=(_battery_device("battery-1"),),
        load_profiles=(
            LoadProfile(
                target_device_id="battery-1",
                tick_values=(Decimal("10"),),
                tick_ms=1000,
            ),
        ),
    )
    with pytest.raises(ScenarioInvalidLoadTargetError):
        build_tick_loop(
            scenario,
            run_id="run-6b",
            clock=FakeClock(),
            random_root=MersenneTwisterRandomPort(seed=42),
        )


def test_build_devices_rejects_invalid_aggregate_ids_type() -> None:
    """Welle-6b-Review L-2: `aggregate_device_ids` mit Falsch-Typ
    (z. B. int) wird im `device.initialize(...)`-Pfad durch
    `WrongTypeError` (Subsystem='smart_meter') geblockt — der
    Helper `_smart_meter_aggregate_ids` faellt nie auf den
    Falsch-Typ-Pfad (siehe Kommentar im Helper)."""
    from grid_gym.hexagon.core.errors import WrongTypeError

    bad = ScenarioDevice(
        id="meter-1",
        type="smart_meter",
        params={
            "aggregate_device_ids": 42,  # int statt list[str]
            "aggregate_metric_name": "power_kw",
        },
    )
    random_root = MersenneTwisterRandomPort(seed=42)
    with pytest.raises(WrongTypeError):
        build_devices((_pv_device("pv-1"), bad), random_root)


# ---------------------------------------------------------------------------
# Welle-6b-Review H-4 — Validator + Parse-Helfer + load_scenario-Roundtrip
# ---------------------------------------------------------------------------


def _minimal_raw_mapping() -> dict[str, object]:
    return {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "welle-6b", "name": "Welle 6b Roundtrip"},
        "simulation": {"tick_ms": 1000, "duration_s": 60, "seed": 42},
        "devices": [
            {
                "id": "load-1",
                "type": "load",
                "params": {"rated_power_kw": Decimal("100")},
            },
        ],
    }


def test_load_scenario_with_grid_model_section_populates_config() -> None:
    """Welle-6b-Review H-4: ADR 0021 §2.3 verlangt, dass die
    `grid_model`-Sektion vom Validator/Loader durchgereicht wird."""
    raw = _minimal_raw_mapping()
    raw["grid_model"] = {
        "nominal_frequency_hz": Decimal("50"),
        "frequency_sensitivity_hz_per_kw": Decimal("0.001"),
        "frequency_clamp_min_hz": Decimal("45"),
        "frequency_clamp_max_hz": Decimal("55"),
        "nominal_voltage_v": Decimal("400"),
        "voltage_sensitivity_v_per_kw": Decimal("0.1"),
        "voltage_clamp_min_v": Decimal("280"),
        "voltage_clamp_max_v": Decimal("520"),
    }
    loaded = load_scenario(raw)
    assert loaded.scenario.grid_model_config is not None
    assert loaded.scenario.grid_model_config.nominal_frequency_hz == Decimal("50")


def test_load_scenario_with_load_events_populates_tuple() -> None:
    """Welle-6b-Review H-4: `load_events`-Sektion wird in
    `Scenario.load_events` als Tupel persistiert."""
    raw = _minimal_raw_mapping()
    raw["load_events"] = [
        {
            "start_s": Decimal("0"),
            "duration_s": Decimal("5"),
            "target_device_id": "load-1",
            "power_kw": Decimal("50"),
        },
    ]
    loaded = load_scenario(raw)
    assert len(loaded.scenario.load_events) == 1
    assert loaded.scenario.load_events[0].target_device_id == "load-1"
    assert loaded.scenario.load_events[0].power_kw == Decimal("50")


def test_load_scenario_with_load_profiles_populates_tuple() -> None:
    """Welle-6b-Review H-4: `load_profiles`-Sektion wird in
    `Scenario.load_profiles` als Tupel persistiert."""
    raw = _minimal_raw_mapping()
    raw["load_profiles"] = [
        {
            "target_device_id": "load-1",
            "tick_values": [Decimal("10"), Decimal("20")],
            "tick_ms": 1000,
        },
    ]
    loaded = load_scenario(raw)
    assert len(loaded.scenario.load_profiles) == 1
    assert loaded.scenario.load_profiles[0].tick_values == (
        Decimal("10"),
        Decimal("20"),
    )


def test_parse_helpers_default_to_empty_when_section_missing() -> None:
    """Welle-6b-Review H-4: `parse_*`-Funktionen liefern leere
    Defaults (None/leere Tupel) wenn die Top-Level-Sektion fehlt."""
    raw = _minimal_raw_mapping()
    assert _parse_grid_model_config(raw) is None
    assert parse_load_events(raw) == ()
    assert parse_load_profiles(raw) == ()


def test_load_scenario_validator_rejects_load_event_with_float_power() -> None:
    """Welle-6b-Review H-4: Validator faengt float-Injektion in
    Decimal-Feldern ab (GG-DATA-005 no-float)."""
    from grid_gym.hexagon.core.errors import ScenarioWrongTypeError

    raw = _minimal_raw_mapping()
    raw["load_events"] = [
        {
            "start_s": Decimal("0"),
            "duration_s": Decimal("5"),
            "target_device_id": "load-1",
            "power_kw": 50.0,  # float — Validator muss raisen
        },
    ]
    with pytest.raises(ScenarioWrongTypeError):
        load_scenario(raw)


def test_load_scenario_validator_rejects_load_event_unknown_target() -> None:
    """Welle-6b-Review H-4: LoadEvent.target_device_id muss in
    `devices` definiert sein — sonst
    `ScenarioUnknownEventTargetError`."""
    from grid_gym.hexagon.core.errors import ScenarioUnknownEventTargetError

    raw = _minimal_raw_mapping()
    raw["load_events"] = [
        {
            "start_s": Decimal("0"),
            "duration_s": Decimal("5"),
            "target_device_id": "ghost-load",
            "power_kw": Decimal("50"),
        },
    ]
    with pytest.raises(ScenarioUnknownEventTargetError):
        load_scenario(raw)


# ---------------------------------------------------------------------------
# Welle-2-Items-7-10-Review M-1 — build_tick_loop fault_port forwarding
# ---------------------------------------------------------------------------


def test_build_tick_loop_forwards_fault_port_default_is_none() -> None:
    """Welle-2-Review M-1: ohne `fault_port=`-Kwarg bleibt
    `TickLoop._fault_port = None` (ADR 0022 §2.5 +
    M3-Welle-1-Welle-Vertrag)."""
    scenario = _scenario(devices=(_pv_device(),))
    loop = build_tick_loop(
        scenario,
        run_id="run-fault-default",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
    )
    assert loop._fault_port is None  # type: ignore[attr-defined]


def test_build_tick_loop_forwards_fault_port_kwarg() -> None:
    """Welle-2-Review M-1: expliziter `fault_port=`-Kwarg landet
    in `TickLoop._fault_port`. ADR 0022 §2.5 + ADR 0025 §2.1:
    Builder reicht den Port unveraendert durch."""
    from collections.abc import Sequence

    from grid_gym.hexagon.core.domain.device import DeviceTickContext

    class _FaultPortStub:
        def __init__(self) -> None:
            self.calls: list[tuple[int, int]] = []

        def apply_active_faults(
            self,
            devices: Sequence[object],
            context: DeviceTickContext,
        ) -> None:
            del devices
            self.calls.append((context.tick, context.simulation_time))

    stub = _FaultPortStub()
    scenario = _scenario(devices=(_pv_device(),))
    loop = build_tick_loop(
        scenario,
        run_id="run-fault-stub",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
        fault_port=stub,
    )
    assert loop._fault_port is stub  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# M3-Welle-3-Review-Folge-3 L-1 — build_tick_loop agent_bus forwarding
# ---------------------------------------------------------------------------


def test_build_tick_loop_forwards_agent_bus_default_is_none() -> None:
    """M3-Welle-3-Review-Folge-3 L-1 (2026-05-21): ohne
    `agent_bus=`-Kwarg bleibt `TickLoop._agent_bus = None`
    (ADR 0023 §2.5 + Welle-3-Foundation-Vertrag). Spiegelt
    das `fault_port`-Default-Pattern aus Welle 2."""
    scenario = _scenario(devices=(_pv_device(),))
    loop = build_tick_loop(
        scenario,
        run_id="run-agent-default",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
    )
    assert loop._agent_bus is None  # type: ignore[attr-defined]


def test_build_tick_loop_forwards_agent_bus_kwarg() -> None:
    """M3-Welle-3-Review-Folge-3 L-1 (2026-05-21): expliziter
    `agent_bus=`-Kwarg landet in `TickLoop._agent_bus`.
    ADR 0023 §2.5: Builder reicht den Bus unveraendert durch
    (Builder-Symmetrie zu ADR 0021 §2.4 + ADR 0022 §2.5)."""
    from grid_gym.hexagon.core.agents import AgentMessageBus

    bus = AgentMessageBus()
    scenario = _scenario(devices=(_pv_device(),))
    loop = build_tick_loop(
        scenario,
        run_id="run-agent-bus",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
        agent_bus=bus,
    )
    assert loop._agent_bus is bus  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# M3-Welle-4a (ADR 0026 §2.2): build_tick_loop(agents=)-Symmetrie
# + GridModelBilanz-Overlay-Verdrahtung
# ---------------------------------------------------------------------------


def test_build_tick_loop_forwards_agents_kwarg() -> None:
    """ADR 0026 §2.2: produktiver `agents`-Kwarg landet in
    `TickLoop._agents` (Builder-Symmetrie zur Konstruktor-API)."""
    from collections.abc import Mapping, Sequence
    from typing import Self

    from grid_gym.hexagon.core.agents import Agent, AgentMessageBus
    from grid_gym.hexagon.core.domain.command import Command
    from grid_gym.hexagon.core.domain.device import DeviceTickContext

    class _NullAgent:
        SNAPSHOT_VERSION: int = 1

        @property
        def agent_id(self) -> str:
            return "agent-x"

        def set_run_id(self, run_id: str) -> None:
            pass

        def tick(
            self,
            context: DeviceTickContext,
            bus: AgentMessageBus,
        ) -> Sequence[Command]:
            return ()

        def snapshot(self) -> Mapping[str, object]:
            return {"version": self.SNAPSHOT_VERSION}

        @classmethod
        def from_snapshot(cls, state: Mapping[str, object]) -> Self:  # noqa: ARG003 — Test-Stub mit Protocol-Surface
            return cls()

    agent = _NullAgent()
    scenario = _scenario(devices=(_pv_device(),))
    loop = build_tick_loop(
        scenario,
        run_id="run-agents",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
        agents=(agent,),
    )
    assert loop._agents == (agent,)  # type: ignore[attr-defined]
    # Auto-Bus-Regel: nicht-leere agents ohne expliziten Bus →
    # automatischer AgentMessageBus.
    assert loop._agent_bus is not None  # type: ignore[attr-defined]


def test_build_tick_loop_wires_grid_model_with_overlays() -> None:
    """ADR 0026 §2.2 + §2.6: bei vorhandenem `grid_model_config`
    konstruiert der Builder das GridModel mit den Scenario-
    LoadOverlay-Tupeln (Single Source of Truth fuer Resume-
    Match-Checks)."""
    event = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("10"),
        target_device_id="load-1",
        power_kw=Decimal("250"),
    )
    profile = LoadProfile(
        target_device_id="load-1",
        tick_values=(Decimal("100"), Decimal("200")),
        tick_ms=1000,
    )
    scenario = _scenario(
        devices=(_load_device("load-1"),),
        grid_model_config=_grid_model_config(),
        load_events=(event,),
        load_profiles=(profile,),
    )
    loop = build_tick_loop(
        scenario,
        run_id="run-overlays",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
    )
    assert loop._grid_model is not None  # type: ignore[attr-defined]
    # GridModel persistiert die Overlays in seinem Snapshot.
    grid_state = loop._grid_model.snapshot()  # type: ignore[attr-defined]
    assert grid_state["active_load_events"] != []
    assert grid_state["active_load_profiles"] != []


def test_build_tick_loop_smoke_runs_one_tick() -> None:
    """ADR 0021 §2.4: voller Builder + erster Tick laeuft
    durch (kein Throw, Telemetrie wird emittiert)."""
    scenario = _scenario(
        devices=(
            _pv_device("pv-1"),
            _load_device("load-1"),
            _grid_device("grid-1"),
        ),
        grid_model_config=_grid_model_config(),
    )
    loop = build_tick_loop(
        scenario,
        run_id="run-6b",
        clock=FakeClock(),
        random_root=MersenneTwisterRandomPort(seed=42),
    )
    result = loop.tick()
    sources = {p.source for p in result.emitted_telemetry}
    assert "pv" in sources
    assert "load" in sources
    assert "grid_connection" in sources
