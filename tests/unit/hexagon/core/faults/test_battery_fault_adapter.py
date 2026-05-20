"""Unit-Tests fuer `BatteryFaultAdapter` (M3 Welle 2, ADR 0025).

Pinnt:
- Window-Boundary half-open `[start, end)` (ADR 0025 §2.3).
- Idempotenz: kein doppelter `inject_fault`-Aufruf in aktiven
  Ticks (ADR 0025 §2.4).
- Recovery: Adapter ruft `_clear_cell_failure` beim Uebergang
  active → inactive (auto-recover oder manual-via-command).
- `FaultPort`-Protocol-Adherence.
- `register_manual_recovery`-Negativ-Pfad
  (`FaultUnknownReferenceError`).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice, ScenarioFault
from grid_gym.hexagon.core.errors import FaultUnknownReferenceError
from grid_gym.hexagon.core.faults import BatteryFaultAdapter
from grid_gym.hexagon.ports.driven.fault import FaultPort


def _battery_device() -> BatteryDevice:
    device = BatteryDevice()
    device.initialize(
        ScenarioDevice(
            id="battery-1",
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
        ),
        MersenneTwisterRandomPort(seed=42),
    )
    # Welle-2-Review L-6: set_run_id im Fixture analog
    # test_fault_injection.py (Welle-3-Telemetry-Pruefungen).
    device.set_run_id("test")
    return device


def _cell_failure_fault(
    start_simulation_time: int = 0,
    duration_ms: int = 5000,
) -> ScenarioFault:
    return ScenarioFault(
        start_simulation_time=start_simulation_time,
        duration_ms=duration_ms,
        target="battery-1",
        type="cell_failure",
        payload={},
        recovery="auto-recover-after-N-ticks",
    )


def test_adapter_satisfies_fault_port_protocol() -> None:
    """`@runtime_checkable` erlaubt isinstance-Check."""
    adapter = BatteryFaultAdapter(faults=())
    assert isinstance(adapter, FaultPort)


def test_adapter_activates_fault_in_window() -> None:
    """ADR 0025 §2.3: half-open `[start, end)` — Fault aktiv ab
    start_simulation_time."""
    device = _battery_device()
    adapter = BatteryFaultAdapter(
        faults=(_cell_failure_fault(start_simulation_time=0, duration_ms=5000),)
    )
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    assert device._cell_failure_active is True


def test_adapter_skips_fault_outside_window() -> None:
    """ADR 0025 §2.3: end-exclusive — bei
    `now == start + duration_ms` ist der Fault inaktiv."""
    device = _battery_device()
    adapter = BatteryFaultAdapter(
        faults=(_cell_failure_fault(start_simulation_time=0, duration_ms=5000),)
    )
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=5, simulation_time=5000, tick_ms=1000),
    )
    assert device._cell_failure_active is False


def test_adapter_auto_recovers_after_window() -> None:
    """ADR 0025 §2.2: Adapter setzt Device-Flag bei Window-Ende
    zurueck (active → inactive)."""
    device = _battery_device()
    adapter = BatteryFaultAdapter(
        faults=(_cell_failure_fault(start_simulation_time=0, duration_ms=2000),)
    )
    # Tick im Fenster → aktiv.
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    assert device._cell_failure_active is True
    # Tick nach dem Fenster → Recovery, Flag wieder False.
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=2, simulation_time=2000, tick_ms=1000),
    )
    assert device._cell_failure_active is False


def test_adapter_idempotent_inject_in_active_window(monkeypatch: pytest.MonkeyPatch) -> None:
    """ADR 0025 §2.4: Adapter ruft `inject_fault` nur beim
    Uebergang inactive → active, nicht bei jedem Tick im
    Fenster."""
    device = _battery_device()
    calls: list[str] = []
    original = device.inject_fault

    def recording_inject(fault_type: str, payload: object) -> None:
        calls.append(fault_type)
        original(fault_type, payload)  # type: ignore[arg-type]

    monkeypatch.setattr(device, "inject_fault", recording_inject)

    adapter = BatteryFaultAdapter(
        faults=(_cell_failure_fault(start_simulation_time=0, duration_ms=5000),)
    )
    # Drei Ticks im Fenster — inject_fault soll nur EINMAL aufgerufen werden.
    for tick_num in range(3):
        adapter.apply_active_faults(
            (device,),
            DeviceTickContext(tick=tick_num, simulation_time=tick_num * 1000, tick_ms=1000),
        )
    assert calls == ["cell_failure"]


def test_adapter_manual_recovery_clears_flag_immediately() -> None:
    """ADR 0025 §2.1: `manual-recover-fault` schlaegt
    Auto-Schedule (Manual-Override-Prioritaet)."""
    device = _battery_device()
    adapter = BatteryFaultAdapter(
        faults=(_cell_failure_fault(start_simulation_time=0, duration_ms=10000),)
    )
    # Erst aktivieren.
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    assert device._cell_failure_active is True
    # Manual-Recovery registrieren.
    adapter.register_manual_recovery("fault-0", "battery-1")
    # Naechster Tick verarbeitet die manuelle Recovery.
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=1, simulation_time=1000, tick_ms=1000),
    )
    assert device._cell_failure_active is False


@pytest.mark.parametrize(
    ("fault_id", "target_device_id"),
    [
        ("fault-99", "battery-1"),  # fault_id falsch
        ("fault-0", "battery-99"),  # target_device_id falsch (Welle-2-Review L-5)
        ("fault-99", "battery-99"),  # beide falsch
    ],
)
def test_register_manual_recovery_rejects_unknown_reference(
    fault_id: str, target_device_id: str
) -> None:
    """ADR 0025 §2.1: unbekannte `(fault_id, target_device_id)`-
    Kombination wirft `FaultUnknownReferenceError` — beide Felder
    werden geprueft (Welle-2-Review L-5)."""
    adapter = BatteryFaultAdapter(faults=(_cell_failure_fault(),))
    with pytest.raises(FaultUnknownReferenceError):
        adapter.register_manual_recovery(fault_id, target_device_id)


def test_adapter_fault_id_uses_original_scenario_index() -> None:
    """Welle-2-Review M-2: `fault-{i}`-ID-Konvention zaehlt
    ueber den ORIGINAL-Index in `scenario.faults`, NICHT ueber
    den gefilterten Index. ADR 0025 §2.1 pinnt das Verhalten.

    Setup: 3 Faults im Scenario, davon nur der mittlere ist
    `cell_failure`. Der Adapter kennt ihn als `fault-1` (sein
    Scenario-Index), NICHT als `fault-0` (was sein gefilterter
    Index waere).

    Rationale: Welle-3+ kann ein optionales `fault.id`-Feld
    hinzufuegen; bis dahin ist `fault-{scenario_index}` die
    stabilste implizite Konvention (nicht-`cell_failure`-Faults
    veraendern die Indexierung nicht).
    """
    voltage_drop_first = ScenarioFault(
        start_simulation_time=0,
        duration_ms=5000,
        target="battery-1",
        type="voltage_drop",  # nicht cell_failure → wird gefiltert
        payload={},
        recovery="auto-recover-after-N-ticks",
    )
    cell_failure_middle = _cell_failure_fault()
    overcurrent_last = ScenarioFault(
        start_simulation_time=0,
        duration_ms=5000,
        target="battery-1",
        type="overcurrent",  # nicht cell_failure
        payload={},
        recovery="auto-recover-after-N-ticks",
    )
    adapter = BatteryFaultAdapter(
        faults=(voltage_drop_first, cell_failure_middle, overcurrent_last)
    )
    # Der Scenario-Index ist 1, nicht 0 (gefilterter Index).
    adapter.register_manual_recovery("fault-1", "battery-1")  # darf nicht werfen
    # `fault-0` ist NICHT bekannt (Scenario-Index 0 ist voltage_drop, wurde gefiltert).
    with pytest.raises(FaultUnknownReferenceError):
        adapter.register_manual_recovery("fault-0", "battery-1")


def test_adapter_handles_missing_target_silently_without_inject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Welle-2-Review M-3 (Branch-Coverage): wenn `device_by_id`
    den Target nicht enthaelt (Device-Liste leer oder Target
    fehlt), wird kein `inject_fault` aufgerufen, und der Adapter-
    State bleibt korrekt.
    """
    adapter = BatteryFaultAdapter(faults=(_cell_failure_fault(),))
    # Leere Devices-Liste — Target kann nicht aufgeloest werden.
    adapter.apply_active_faults(
        (),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    # Adapter-State zeigt aktiv (Window erreicht), aber kein
    # Device-Call moeglich.
    assert adapter._active_faults["fault-0", "battery-1"] is True


def test_adapter_manual_recovery_before_window_does_not_crash() -> None:
    """Welle-2-Review M-3 (Branch-Coverage): Manual-Recovery
    bevor der Fault aktiviert wurde (`currently_active = False`)
    laeuft sauber durch — `target._clear_*` wird nur bei
    `currently_active` aufgerufen.
    """
    device = _battery_device()
    adapter = BatteryFaultAdapter(
        faults=(_cell_failure_fault(start_simulation_time=10000, duration_ms=5000),)
    )
    # Manual-Recovery zu fruh (Fault noch nicht im Window).
    adapter.register_manual_recovery("fault-0", "battery-1")
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    # Adapter ist sauber — kein Crash, Pending-Set leer.
    assert ("fault-0", "battery-1") not in adapter._pending_manual_recoveries
    assert device._cell_failure_active is False


def test_adapter_ignores_non_cell_failure_faults() -> None:
    """Welle-2-Closed-Set: nur `cell_failure` wird konsumiert.
    Andere Typen werden ignoriert (Grid-Faults gehen in den
    GridFaultAdapter)."""
    device = _battery_device()
    voltage_drop_fault = ScenarioFault(
        start_simulation_time=0,
        duration_ms=5000,
        target="battery-1",
        type="voltage_drop",
        payload={},
        recovery="auto-recover-after-N-ticks",
    )
    adapter = BatteryFaultAdapter(faults=(voltage_drop_fault,))
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    assert device._cell_failure_active is False
