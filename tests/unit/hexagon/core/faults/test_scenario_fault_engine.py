"""Unit-Tests fuer die generische `ScenarioFaultEngine`
(M8 Welle 2, ADR 0059; generalisiert ADR 0025).

Pinnt:
- `FaultPort`-Protocol-Adherence.
- Filterung auf `supported_types` (fremde Typen sind No-Op).
- Window-Boundary half-open `[start, end)` (ADR 0025 §2.3).
- Idempotenz: kein doppelter `inject_fault` in aktiven Ticks.
- Auto-Recovery (`clear_fault`) beim Window-Ende.
- `register_manual_recovery`-Negativ-Pfad
  (`FaultUnknownReferenceError`) + Original-Index-`fault-{i}`-IDs.
- **ADR-0059-Kern**: eine Engine verarbeitet *mehrere* Fault-Typen
  (inkl. der drei neuen Welle-2-Typen) in EINEM `apply`-Pass; der
  Fault-Typ wird ans Ziel-Geraet durchgereicht — kein per-Typ-Code.
- End-to-End mit einem echten Geraet (Diesel/`genset_fault`).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

import pytest

from grid_gym.hexagon.core.devices.diesel_generator import DieselGeneratorDevice
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice, ScenarioFault
from grid_gym.hexagon.core.errors import FaultUnknownReferenceError, FaultUnsupportedTypeError
from grid_gym.hexagon.core.faults import ScenarioFaultEngine
from grid_gym.hexagon.core.faults.types import (
    FAULT_TYPE_CELL_FAILURE,
    FAULT_TYPE_CONNECTION_LOSS,
    FAULT_TYPE_GENSET_FAULT,
    FAULT_TYPE_VOLTAGE_DROP,
    FAULT_TYPE_WINDING_FAULT,
)
from grid_gym.hexagon.ports.driven.fault import FaultPort
from tests.unit.hexagon.core.devices._fakes import NullDevice
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom

# Slice 054: fault-Sensor-Traeger fuer `make test-fault`.
pytestmark = pytest.mark.fault

_ALL_TYPES = frozenset(
    {
        FAULT_TYPE_CELL_FAILURE,
        FAULT_TYPE_VOLTAGE_DROP,
        FAULT_TYPE_CONNECTION_LOSS,
        FAULT_TYPE_WINDING_FAULT,
        FAULT_TYPE_GENSET_FAULT,
    }
)


class _RecordingDevice(NullDevice):
    """Fake `FaultInjectableDevice` (analog `test_protocol.
    NullFaultInjectableDevice`): zeichnet inject/clear-Aufrufe je
    Fault-Typ auf, ohne typ-spezifische Validierung — isoliert das
    Engine-Scheduling vom Geraete-Physik-Verhalten."""

    def __init__(self) -> None:
        super().__init__()
        self.injected: list[str] = []
        self.cleared: list[str] = []

    def inject_fault(self, fault_type: str, payload: Mapping[str, object]) -> None:
        self.injected.append(fault_type)

    def clear_fault(self, fault_type: str) -> None:
        self.cleared.append(fault_type)


def _device(device_id: str) -> _RecordingDevice:
    device = _RecordingDevice()
    device.initialize(
        ScenarioDevice(id=device_id, type="fake", params={}),
        FixedSeedRandom(seed=42),
    )
    return device


def _fault(
    target: str,
    fault_type: str,
    start_simulation_time: int = 0,
    duration_ms: int = 5000,
) -> ScenarioFault:
    return ScenarioFault(
        start_simulation_time=start_simulation_time,
        duration_ms=duration_ms,
        target=target,
        type=fault_type,
        payload={},
        recovery="auto-recover-after-N-ticks",
    )


def _ctx(simulation_time: int) -> DeviceTickContext:
    return DeviceTickContext(
        tick=simulation_time // 1000, simulation_time=simulation_time, tick_ms=1000
    )


def test_engine_satisfies_fault_port_protocol() -> None:
    engine = ScenarioFaultEngine((), _ALL_TYPES)
    assert isinstance(engine, FaultPort)


def test_engine_ignores_unsupported_types() -> None:
    """Faults ausserhalb `supported_types` sind No-Op (kein inject)."""
    device = _device("dg-1")
    engine = ScenarioFaultEngine(
        (_fault("dg-1", FAULT_TYPE_CELL_FAILURE),),
        frozenset({FAULT_TYPE_GENSET_FAULT}),
    )
    engine.apply_active_faults((device,), _ctx(0))
    assert device.injected == []


def test_engine_activates_in_window_half_open() -> None:
    """ADR 0025 §2.3: aktiv ab start, inaktiv bei start+duration."""
    device = _device("dg-1")
    engine = ScenarioFaultEngine(
        (_fault("dg-1", FAULT_TYPE_GENSET_FAULT, start_simulation_time=0, duration_ms=5000),),
        _ALL_TYPES,
    )
    engine.apply_active_faults((device,), _ctx(0))
    assert device.injected == [FAULT_TYPE_GENSET_FAULT]
    # Window-Ende ist end-exclusive: bei 5000 kein erneutes inject.
    engine.apply_active_faults((device,), _ctx(5000))
    assert device.injected == [FAULT_TYPE_GENSET_FAULT]


def test_engine_inject_is_idempotent_across_active_ticks() -> None:
    device = _device("dg-1")
    engine = ScenarioFaultEngine(
        (_fault("dg-1", FAULT_TYPE_GENSET_FAULT, start_simulation_time=0, duration_ms=5000),),
        _ALL_TYPES,
    )
    engine.apply_active_faults((device,), _ctx(0))
    engine.apply_active_faults((device,), _ctx(1000))
    engine.apply_active_faults((device,), _ctx(2000))
    assert device.injected == [FAULT_TYPE_GENSET_FAULT]
    assert device.cleared == []


def test_engine_auto_recovers_at_window_end_with_same_type() -> None:
    """ADR 0059: `clear_fault` reicht denselben `fault.type` durch,
    der injiziert wurde (kein hartkodierter Typ)."""
    device = _device("dg-1")
    engine = ScenarioFaultEngine(
        (_fault("dg-1", FAULT_TYPE_GENSET_FAULT, start_simulation_time=0, duration_ms=2000),),
        _ALL_TYPES,
    )
    engine.apply_active_faults((device,), _ctx(0))  # aktiv
    engine.apply_active_faults((device,), _ctx(2000))  # Window-Ende → clear
    assert device.injected == [FAULT_TYPE_GENSET_FAULT]
    assert device.cleared == [FAULT_TYPE_GENSET_FAULT]


def test_engine_single_pass_handles_all_five_types() -> None:
    """ADR-0059-Kern: EINE Engine ueber alle bekannten Typen
    reicht jeden `fault.type` ans passende Ziel-Geraet — die drei
    neuen Welle-2-Typen funktionieren ohne per-Typ-Engine-Code."""
    battery = _device("battery-1")
    grid = _device("grid-1")
    ev = _device("ev-1")
    transformer = _device("tr-1")
    diesel = _device("dg-1")
    engine = ScenarioFaultEngine(
        (
            _fault("battery-1", FAULT_TYPE_CELL_FAILURE),
            _fault("grid-1", FAULT_TYPE_VOLTAGE_DROP),
            _fault("ev-1", FAULT_TYPE_CONNECTION_LOSS),
            _fault("tr-1", FAULT_TYPE_WINDING_FAULT),
            _fault("dg-1", FAULT_TYPE_GENSET_FAULT),
        ),
        _ALL_TYPES,
    )
    engine.apply_active_faults((battery, grid, ev, transformer, diesel), _ctx(0))
    assert battery.injected == [FAULT_TYPE_CELL_FAILURE]
    assert grid.injected == [FAULT_TYPE_VOLTAGE_DROP]
    assert ev.injected == [FAULT_TYPE_CONNECTION_LOSS]
    assert transformer.injected == [FAULT_TYPE_WINDING_FAULT]
    assert diesel.injected == [FAULT_TYPE_GENSET_FAULT]


def test_manual_recovery_uses_original_scenario_index_id() -> None:
    """ADR 0025 §2.1 + Welle-2-Review M-2: `fault-{i}` nutzt den
    Original-Index, stabil ueber gefilterte Typen. Ein nicht
    unterstuetzter Fault an Index 0 verschiebt die ID des
    unterstuetzten Faults an Index 1 NICHT."""
    device = _device("dg-1")
    engine = ScenarioFaultEngine(
        (
            _fault("other-1", "cell_failure"),  # Index 0, nicht in supported
            _fault("dg-1", FAULT_TYPE_GENSET_FAULT),  # Index 1
        ),
        frozenset({FAULT_TYPE_GENSET_FAULT}),
    )
    # fault-1 (Original-Index) muss registrierbar sein; fault-0 nicht.
    engine.register_manual_recovery("fault-1", "dg-1")
    with pytest.raises(FaultUnknownReferenceError):
        engine.register_manual_recovery("fault-0", "dg-1")


def test_manual_recovery_clears_active_fault() -> None:
    device = _device("dg-1")
    engine = ScenarioFaultEngine(
        (_fault("dg-1", FAULT_TYPE_GENSET_FAULT, start_simulation_time=0, duration_ms=10000),),
        _ALL_TYPES,
    )
    engine.apply_active_faults((device,), _ctx(0))  # aktiv
    engine.register_manual_recovery("fault-0", "dg-1")
    engine.apply_active_faults((device,), _ctx(1000))  # manual → clear trotz Fenster
    assert device.cleared == [FAULT_TYPE_GENSET_FAULT]


def test_manual_recovery_before_activation_is_noop_clear() -> None:
    """Manual-Recovery vor dem Window: currently_active ist False,
    also kein `clear_fault`-Aufruf — nur das Scheduling-Flag wird
    konsumiert (Branch `target is not None and currently_active`
    False-Pfad)."""
    device = _device("dg-1")
    engine = ScenarioFaultEngine(
        (_fault("dg-1", FAULT_TYPE_GENSET_FAULT, start_simulation_time=5000, duration_ms=5000),),
        _ALL_TYPES,
    )
    engine.register_manual_recovery("fault-0", "dg-1")
    engine.apply_active_faults((device,), _ctx(0))  # vor Window, nicht aktiv
    assert device.injected == []
    assert device.cleared == []


def test_inject_skipped_when_target_absent_in_window() -> None:
    """Branch `in_window and not currently_active` mit `target is
    None`: das Ziel-Geraet fehlt in der `devices`-Sequenz waehrend
    des Windows — kein inject, kein Crash (Scheduling-Flag wird
    trotzdem gesetzt)."""
    engine = ScenarioFaultEngine(
        (_fault("dg-1", FAULT_TYPE_GENSET_FAULT, start_simulation_time=0, duration_ms=5000),),
        _ALL_TYPES,
    )
    engine.apply_active_faults((), _ctx(0))  # Window aktiv, aber kein dg-1
    # Folge-Tick out-of-window mit Geraet: currently_active ist True
    # (Flag in Tick 0 gesetzt), also clear-Pfad mit Target.
    device = _device("dg-1")
    engine.apply_active_faults((device,), _ctx(5000))
    assert device.injected == []
    assert device.cleared == [FAULT_TYPE_GENSET_FAULT]


def test_clear_skipped_when_target_absent_after_window() -> None:
    """Branch `not in_window and currently_active` mit `target is
    None`: das Geraet verschwindet nach Aktivierung — Flag wird
    zurueckgesetzt, kein clear-Aufruf, kein Crash."""
    device = _device("dg-1")
    engine = ScenarioFaultEngine(
        (_fault("dg-1", FAULT_TYPE_GENSET_FAULT, start_simulation_time=0, duration_ms=2000),),
        _ALL_TYPES,
    )
    engine.apply_active_faults((device,), _ctx(0))  # aktiv (Geraet da)
    engine.apply_active_faults((), _ctx(2000))  # Window-Ende, Geraet weg
    assert device.injected == [FAULT_TYPE_GENSET_FAULT]
    assert device.cleared == []  # clear wurde uebersprungen (kein Target)


def test_non_injectable_device_in_list_is_skipped() -> None:
    """Branch `isinstance(device, FaultInjectableDevice)` False: ein
    Nicht-injizierbares Objekt in `devices` wird uebersprungen, das
    echte Ziel-Geraet daneben bekommt seinen Fault."""
    device = _device("dg-1")
    engine = ScenarioFaultEngine(
        (_fault("dg-1", FAULT_TYPE_GENSET_FAULT),),
        _ALL_TYPES,
    )
    engine.apply_active_faults((object(), device), _ctx(0))
    assert device.injected == [FAULT_TYPE_GENSET_FAULT]


def test_engine_propagates_unsupported_type_from_mistargeted_fault() -> None:
    """ADR 0059 §2.5 Wrong-Target-Edge: ein in `supported_types`
    erlaubter Typ auf ein Geraet, das ihn NICHT kennt, wirft beim
    Tick `FaultUnsupportedTypeError` (Geraet validiert; Engine
    reicht nur durch). Pinnt die neue Single-Engine-Wurf-Semantik,
    die der entfernte F12-Composite-Test nicht mehr deckt."""
    diesel = DieselGeneratorDevice()
    diesel.initialize(
        ScenarioDevice(
            id="dg-1",
            type="diesel_generator",
            params={
                "max_power_kw": Decimal("100"),
                "min_start_power_kw": Decimal("20"),
                "min_stop_power_kw": Decimal("10"),
                "fuel_capacity_l": Decimal("1000"),
                "initial_fuel_l": Decimal("1000"),
                "fuel_per_kwh_l": Decimal("0.3"),
                "ramp_kw_per_s": Decimal("1000"),
            },
        ),
        FixedSeedRandom(seed=42),
    )
    diesel.set_run_id("test")
    # cell_failure ist in supported_types, aber Diesel kennt nur genset_fault.
    engine = ScenarioFaultEngine(
        (_fault("dg-1", FAULT_TYPE_CELL_FAILURE, start_simulation_time=0, duration_ms=2000),),
        _ALL_TYPES,
    )
    with pytest.raises(FaultUnsupportedTypeError):
        engine.apply_active_faults((diesel,), _ctx(0))


def test_engine_end_to_end_on_real_diesel_device() -> None:
    """D-8-Beweis: die generische Engine mutiert den echten
    Physik-State eines neuen Geraets (Diesel `genset_fault`)."""
    diesel = DieselGeneratorDevice()
    diesel.initialize(
        ScenarioDevice(
            id="dg-1",
            type="diesel_generator",
            params={
                "max_power_kw": Decimal("100"),
                "min_start_power_kw": Decimal("20"),
                "min_stop_power_kw": Decimal("10"),
                "fuel_capacity_l": Decimal("1000"),
                "initial_fuel_l": Decimal("1000"),
                "fuel_per_kwh_l": Decimal("0.3"),
                "ramp_kw_per_s": Decimal("1000"),
            },
        ),
        FixedSeedRandom(seed=42),
    )
    diesel.set_run_id("test")
    engine = ScenarioFaultEngine(
        (_fault("dg-1", FAULT_TYPE_GENSET_FAULT, start_simulation_time=0, duration_ms=2000),),
        _ALL_TYPES,
    )
    engine.apply_active_faults((diesel,), _ctx(0))
    assert diesel._genset_fault_active is True
    engine.apply_active_faults((diesel,), _ctx(2000))  # Window-Ende → recover
    assert diesel._genset_fault_active is False
