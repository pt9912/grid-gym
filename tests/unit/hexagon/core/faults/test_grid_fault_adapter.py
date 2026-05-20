"""Unit-Tests fuer `GridFaultAdapter` (M3 Welle 2, ADR 0025).

Pinnt analog `test_battery_fault_adapter.py`:
- Window-Boundary half-open `[start, end)` (ADR 0025 §2.3).
- Idempotenz (ADR 0025 §2.4).
- Recovery (auto + manual).
- `FaultPort`-Protocol-Adherence.
- `register_manual_recovery`-Negativ-Pfad.
- `fault-{i}`-ID-Konvention mit Original-Scenario-Index
  (Welle-2-Review M-2).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice, ScenarioFault
from grid_gym.hexagon.core.errors import FaultUnknownReferenceError
from grid_gym.hexagon.core.faults import GridFaultAdapter
from grid_gym.hexagon.ports.driven.fault import FaultPort


def _grid_device() -> GridConnectionDevice:
    device = GridConnectionDevice()
    device.initialize(
        ScenarioDevice(
            id="grid-1",
            type="grid_connection",
            params={
                "nominal_voltage_v": Decimal("400"),
                "max_import_kw": Decimal("1000"),
                "max_export_kw": Decimal("1000"),
            },
        ),
        MersenneTwisterRandomPort(seed=42),
    )
    device.set_run_id("test")
    return device


def _voltage_drop_fault(
    start_simulation_time: int = 0,
    duration_ms: int = 5000,
) -> ScenarioFault:
    return ScenarioFault(
        start_simulation_time=start_simulation_time,
        duration_ms=duration_ms,
        target="grid-1",
        type="voltage_drop",
        payload={},
        recovery="auto-recover-after-N-ticks",
    )


def test_adapter_satisfies_fault_port_protocol() -> None:
    adapter = GridFaultAdapter(faults=())
    assert isinstance(adapter, FaultPort)


def test_adapter_activates_fault_in_window() -> None:
    device = _grid_device()
    adapter = GridFaultAdapter(faults=(_voltage_drop_fault(),))
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    assert device._voltage_drop_active is True
    assert device._pending_voltage_v == Decimal("200")


def test_adapter_skips_fault_outside_window() -> None:
    device = _grid_device()
    adapter = GridFaultAdapter(faults=(_voltage_drop_fault(),))
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=5, simulation_time=5000, tick_ms=1000),
    )
    assert device._voltage_drop_active is False


def test_adapter_auto_recovers_after_window() -> None:
    device = _grid_device()
    adapter = GridFaultAdapter(faults=(_voltage_drop_fault(duration_ms=2000),))
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    assert device._voltage_drop_active is True
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=2, simulation_time=2000, tick_ms=1000),
    )
    assert device._voltage_drop_active is False
    # Recovery restauriert nominal_voltage_v.
    assert device._pending_voltage_v == Decimal("400")


def test_adapter_idempotent_inject(monkeypatch: pytest.MonkeyPatch) -> None:
    device = _grid_device()
    calls: list[str] = []
    original = device.inject_fault

    def recording(fault_type: str, payload: object) -> None:
        calls.append(fault_type)
        original(fault_type, payload)  # type: ignore[arg-type]

    monkeypatch.setattr(device, "inject_fault", recording)

    adapter = GridFaultAdapter(faults=(_voltage_drop_fault(),))
    for tick_num in range(3):
        adapter.apply_active_faults(
            (device,),
            DeviceTickContext(tick=tick_num, simulation_time=tick_num * 1000, tick_ms=1000),
        )
    assert calls == ["voltage_drop"]


def test_adapter_manual_recovery_clears_flag() -> None:
    device = _grid_device()
    adapter = GridFaultAdapter(faults=(_voltage_drop_fault(duration_ms=10000),))
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    assert device._voltage_drop_active is True
    adapter.register_manual_recovery("fault-0", "grid-1")
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=1, simulation_time=1000, tick_ms=1000),
    )
    assert device._voltage_drop_active is False


@pytest.mark.parametrize(
    ("fault_id", "target_device_id"),
    [
        ("fault-99", "grid-1"),
        ("fault-0", "grid-99"),
        ("fault-99", "grid-99"),
    ],
)
def test_register_manual_recovery_rejects_unknown_reference(
    fault_id: str, target_device_id: str
) -> None:
    adapter = GridFaultAdapter(faults=(_voltage_drop_fault(),))
    with pytest.raises(FaultUnknownReferenceError):
        adapter.register_manual_recovery(fault_id, target_device_id)


def test_adapter_ignores_non_voltage_drop_faults() -> None:
    device = _grid_device()
    cell_failure_fault = ScenarioFault(
        start_simulation_time=0,
        duration_ms=5000,
        target="grid-1",
        type="cell_failure",  # Battery-Typ; wird vom Grid-Adapter ignoriert
        payload={},
        recovery="auto-recover-after-N-ticks",
    )
    adapter = GridFaultAdapter(faults=(cell_failure_fault,))
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    assert device._voltage_drop_active is False


def test_adapter_handles_missing_target_silently_without_inject() -> None:
    """Welle-2b-Review F1 (Mirror C2a-M-3): wenn `device_by_id` den
    Target nicht enthaelt, wird kein `inject_fault` aufgerufen; Adapter-
    State bleibt korrekt (`_active_faults[key] = True`)."""
    adapter = GridFaultAdapter(faults=(_voltage_drop_fault(),))
    adapter.apply_active_faults(
        (),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    assert adapter._active_faults["fault-0", "grid-1"] is True


def test_adapter_manual_recovery_before_window_does_not_crash() -> None:
    """Welle-2b-Review F1 (Mirror C2a-M-3): Manual-Recovery bevor der
    Fault aktiviert wurde, laeuft sauber durch (kein `clear_fault`-
    Call, weil `currently_active = False`)."""
    device = _grid_device()
    adapter = GridFaultAdapter(
        faults=(_voltage_drop_fault(start_simulation_time=10000, duration_ms=5000),)
    )
    adapter.register_manual_recovery("fault-0", "grid-1")
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    assert ("fault-0", "grid-1") not in adapter._pending_manual_recoveries
    assert device._voltage_drop_active is False


def test_adapter_does_not_mutate_pending_power_kw() -> None:
    """Welle-2b-Review F3 (ADR 0022 §2.4 GridConnection-Constraint):
    `apply_active_faults` mutiert NIE `_pending_power_kw`. Adapter-
    Boundary-Pin zusaetzlich zum device-level
    `test_inject_voltage_drop_does_not_mutate_pending_power_kw`."""
    device = _grid_device()
    pending_before = device._pending_power_kw
    current_before = device._current_power_kw
    adapter = GridFaultAdapter(faults=(_voltage_drop_fault(),))
    adapter.apply_active_faults(
        (device,),
        DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000),
    )
    assert device._pending_power_kw == pending_before
    assert device._current_power_kw == current_before


def test_adapter_fault_id_uses_original_scenario_index() -> None:
    """Welle-2-Review M-2 (Spiegel zu Battery-Test): `fault-{i}`-
    ID-Konvention nutzt den Original-Scenario-Index."""
    cell_failure_first = ScenarioFault(
        start_simulation_time=0,
        duration_ms=5000,
        target="grid-1",
        type="cell_failure",  # gefiltert
        payload={},
        recovery="auto-recover-after-N-ticks",
    )
    voltage_drop_middle = _voltage_drop_fault()
    adapter = GridFaultAdapter(faults=(cell_failure_first, voltage_drop_middle))
    # Scenario-Index 1, nicht 0 (gefilterter Index).
    adapter.register_manual_recovery("fault-1", "grid-1")
    with pytest.raises(FaultUnknownReferenceError):
        adapter.register_manual_recovery("fault-0", "grid-1")
