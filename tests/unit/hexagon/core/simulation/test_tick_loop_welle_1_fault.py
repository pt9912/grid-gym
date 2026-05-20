"""M3-Welle-1-Tests fuer den TickLoop-FaultPort-Hook
(ADR 0022 §2.4 + §2.5).

Pinnt:
- TickLoop ruft `fault_port.apply_active_faults(devices, context)`
  pro Tick, wenn `fault_port` gesetzt ist.
- TickLoop ueberspringt den Hook, wenn `fault_port=None`
  (Default).
- Hook-Order: FaultPort-Aufruf laeuft VOR der ersten
  `_run_device_iteration` (d. h. vor `device.tick(...)`) —
  damit Devices in derselben Tick auf den gemutateten State
  reagieren koennen.
"""

from __future__ import annotations

from collections.abc import Sequence

from grid_gym.hexagon.core.devices._protocol import DeviceModel
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driven.fault import FaultPort
from tests.unit.hexagon.core.devices._fakes import NullDevice
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


class _OrderRecordingFaultPort:
    """Inline-Stub: zeichnet Aufruf-Reihenfolge auf.

    Welle-1-Test-Pattern; produktive Adapter kommen in Welle 2.
    """

    def __init__(self, recorder: list[str]) -> None:
        self._recorder = recorder

    def apply_active_faults(
        self,
        devices: Sequence[object],
        context: DeviceTickContext,
    ) -> None:
        self._recorder.append("fault_port.apply_active_faults")


class _OrderRecordingNullDevice(NullDevice):
    """NullDevice + Tick-Order-Recorder.

    Welle-1-Stub fuer den Order-Test: macht beim Tick einen
    Eintrag in den geteilten Recorder, damit der Test sieht
    ob FaultPort vor `tick()` lief.
    """

    def __init__(self, recorder: list[str]) -> None:
        super().__init__()
        self._recorder = recorder

    def tick(self, context):  # type: ignore[override, no-untyped-def]
        outcome = super().tick(context)
        self._recorder.append(f"device.tick:{self.device_id}")
        return outcome


def _make_loop(
    *,
    devices: tuple[DeviceModel, ...] = (),
    fault_port: FaultPort | None = None,
) -> TickLoop:
    return TickLoop(
        run_id="welle-1-fault-test",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=devices,
        fault_port=fault_port,
    )


def test_tick_loop_calls_fault_port_when_set() -> None:
    """ADR 0022 §2.4: TickLoop ruft den FaultPort-Hook pro Tick
    auf, wenn `fault_port` gesetzt ist."""
    recorder: list[str] = []
    port = _OrderRecordingFaultPort(recorder)
    loop = _make_loop(fault_port=port)
    loop.tick()
    assert recorder == ["fault_port.apply_active_faults"]


def test_tick_loop_skips_hook_when_fault_port_is_none() -> None:
    """ADR 0022 §2.5: `fault_port=None` (Default) skippt den
    Hook sauber — alle bestehenden Tests bleiben unveraendert."""
    loop = _make_loop(fault_port=None)
    # Sollte ohne Exception durchlaufen; kein FaultPort-Aufruf.
    result = loop.tick()
    # `tick` ist 0-indexed nach dem ersten Tick (TickResult-
    # Konvention); was wir hier wirklich pruefen: keine Exception
    # + erste Tick-Result-Instance ist konstruierbar ohne FaultPort.
    assert result.simulation_time == 1000  # tick_ms=1000 → simulation_time advanced


def test_tick_loop_calls_fault_port_before_first_device_tick() -> None:
    """ADR 0022 §2.4 Order-Pflicht: FaultPort wird VOR der
    ersten Device-Iteration aufgerufen, damit gemutete State
    in derselben Tick wirksam ist."""
    recorder: list[str] = []
    port = _OrderRecordingFaultPort(recorder)
    device = _OrderRecordingNullDevice(recorder)
    device.initialize(
        ScenarioDevice(id="null-1", type="null", params={}),
        FixedSeedRandom(seed=1),
    )
    loop = _make_loop(devices=(device,), fault_port=port)
    loop.tick()
    # FaultPort-Hook ist der erste Eintrag, danach Device-Tick.
    assert recorder[0] == "fault_port.apply_active_faults"
    assert "device.tick:null-1" in recorder
    assert recorder.index("fault_port.apply_active_faults") < recorder.index("device.tick:null-1")
