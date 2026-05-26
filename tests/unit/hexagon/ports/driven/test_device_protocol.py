"""Protocol-Shape-Tests fuer `DeviceProtocolPort` (M4 Welle 1,
ADR 0030 §2.1).

Pattern aus `tests/unit/hexagon/ports/driven/test_fault.py`:
- Inline-Stub (kein Test-Fake-Modul, weil Welle 1 keinen
  produktiven Adapter hat).
- `isinstance(stub, DeviceProtocolPort)` per
  `@runtime_checkable`.
- Methoden-Surface-Aufruf zur Sanity.
- `*Error`-Hierarchie-Verifikation.
"""

from __future__ import annotations

import pytest

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.errors import GridGymError
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPort,
    DeviceProtocolPortError,
    DeviceProtocolPortReadError,
    DeviceProtocolPortStartError,
    DeviceProtocolPortStopError,
    DeviceProtocolPortUnknownTargetError,
    DeviceProtocolPortWriteError,
)


class _RecordingDeviceProtocolPort:
    """Inline-Stub: zeichnet Lifecycle- und I/O-Aufrufe auf.

    Welle-1-Stub. Produktive Adapter
    (`MqttDeviceProtocolAdapter` etc.) kommen ab Welle 2 unter
    `adapters/driven/protocol_*/`.
    """

    def __init__(self) -> None:
        self.start_calls: int = 0
        self.stop_calls: int = 0
        self.reads: list[str] = []
        self.writes: list[tuple[str, Command]] = []

    def start(self) -> None:
        self.start_calls += 1

    def stop(self) -> None:
        self.stop_calls += 1

    def read(self, target: str) -> None:
        self.reads.append(target)

    def write(self, target: str, command: Command) -> None:
        self.writes.append((target, command))


def test_recording_stub_satisfies_device_protocol_port_protocol() -> None:
    """`@runtime_checkable` erlaubt isinstance-Check ohne
    explizite Subclass-Deklaration."""
    port = _RecordingDeviceProtocolPort()
    assert isinstance(port, DeviceProtocolPort)


def test_lifecycle_methods_record_invocation() -> None:
    """Sanity: start/stop landen im Stub."""
    port = _RecordingDeviceProtocolPort()
    port.start()
    port.start()
    port.stop()
    assert port.start_calls == 2
    assert port.stop_calls == 1


def test_read_returns_none_for_no_value_available() -> None:
    """Welle-1-Vertrag: `read()` darf `None` zurueckgeben, wenn
    der Adapter aktuell keinen Wert hat (ADR 0030 §2.1)."""
    port = _RecordingDeviceProtocolPort()
    result = port.read("device-1")
    assert result is None
    assert port.reads == ["device-1"]


def test_write_records_target_and_command() -> None:
    """Sanity: write speichert (target, command)."""
    port = _RecordingDeviceProtocolPort()
    command = Command(
        command_id="cmd-1",
        simulation_time=0,
        target_device_id="device-1",
        type="set_power_kw",
        payload={"power_kw": "1.0"},
        validation_status="validated",
        result=CommandResult.ACCEPTED,
    )
    port.write("device-1", command)
    assert port.writes == [("device-1", command)]


# ---------------------------------------------------------------------------
# Error-Hierarchie (ADR 0030 §2.1 + §4)
# ---------------------------------------------------------------------------


def test_device_protocol_port_error_is_grid_gym_error_subclass() -> None:
    """Pattern-Konsistenz mit anderen Driven-Port-Errors (z. B.
    `OtlpAdapterConfigError` -> `GridGymError`)."""
    assert issubclass(DeviceProtocolPortError, GridGymError)


@pytest.mark.parametrize(
    "subclass",
    [
        DeviceProtocolPortStartError,
        DeviceProtocolPortStopError,
        DeviceProtocolPortReadError,
        DeviceProtocolPortWriteError,
        DeviceProtocolPortUnknownTargetError,
    ],
)
def test_typed_errors_inherit_from_device_protocol_port_error(
    subclass: type[DeviceProtocolPortError],
) -> None:
    """Alle typed Sub-Errors erben vom Wurzel-Error (Welle-2-
    Adapter koennen also pauschal `DeviceProtocolPortError`
    catchen)."""
    assert issubclass(subclass, DeviceProtocolPortError)


def test_unknown_target_error_captures_target_and_available() -> None:
    """Pre-Dispatch-Pflichtcheck (ADR 0030 §2.1): die typed
    Exception traegt `target` und `available_targets` als
    Attribute, damit Caller programmatisch reagieren koennen
    (z. B. Re-Issue mit korrigiertem Target)."""
    err = DeviceProtocolPortUnknownTargetError(
        "device-99",
        available_targets=("device-1", "device-2"),
    )
    assert err.target == "device-99"
    assert err.available_targets == ("device-1", "device-2")
    assert "device-99" in str(err)
    assert "device-1" in str(err)
    assert "device-2" in str(err)


def test_unknown_target_error_message_without_available_targets() -> None:
    """Welle-1-Surface-Minimum: `available_targets` ist optional
    (Adapter mit dynamischem Target-Set kann es leer lassen)."""
    err = DeviceProtocolPortUnknownTargetError("device-99")
    assert err.target == "device-99"
    assert err.available_targets == ()
    assert "device-99" in str(err)
    assert "verfuegbar" not in str(err)
