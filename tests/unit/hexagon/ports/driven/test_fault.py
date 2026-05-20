"""Protocol-Shape-Tests fuer `FaultPort` (M3 Welle 1,
ADR 0022 §2.2).

Pattern aus `tests/unit/hexagon/ports/driven/test_clock.py`:
- Inline-Stub (kein Test-Fake-Modul, weil Welle 1 keinen
  produktiven Adapter hat).
- `isinstance(stub, FaultPort)` per `@runtime_checkable`.
- Methoden-Surface-Aufruf zur Sanity.
"""

from __future__ import annotations

from collections.abc import Sequence

from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.ports.driven.fault import FaultPort


class _RecordingFaultPort:
    """Inline-Stub: zeichnet `apply_active_faults`-Aufrufe auf.

    Welle-1-Stub. Produktive Adapter (`BatteryFaultAdapter`,
    `GridFaultAdapter`) kommen in Welle 2 unter
    `adapters/driven/fault_*/`.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[tuple[object, ...], DeviceTickContext]] = []

    def apply_active_faults(
        self,
        devices: Sequence[object],
        context: DeviceTickContext,
    ) -> None:
        self.calls.append((tuple(devices), context))


def test_recording_fault_port_satisfies_fault_port_protocol() -> None:
    """`@runtime_checkable` erlaubt isinstance-Check ohne
    explizite Subclass-Deklaration."""
    port = _RecordingFaultPort()
    assert isinstance(port, FaultPort)


def test_apply_active_faults_records_invocation() -> None:
    """Sanity: Methoden-Aufruf landet im Stub."""
    port = _RecordingFaultPort()
    context = DeviceTickContext(tick=0, simulation_time=0, tick_ms=1000)
    port.apply_active_faults((), context)
    assert len(port.calls) == 1
    assert port.calls[0][0] == ()
    assert port.calls[0][1] == context
