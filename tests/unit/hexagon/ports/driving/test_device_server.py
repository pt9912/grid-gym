"""Protocol-Shape-Tests fuer `DeviceServerPort` (Field-Server Pull-Seite,
ADR 0075 §2.1). Muster aus `test_field_publish.py` (Inline-Stub,
`@runtime_checkable`, Lifecycle, `*Error`-Hierarchie)."""

from __future__ import annotations

import pytest

from grid_gym.hexagon.core.errors import GridGymError
from grid_gym.hexagon.ports.driving.device_server import (
    DeviceServerPort,
    DeviceServerPortError,
    DeviceServerPortStartError,
    DeviceServerPortStopError,
)


class _RecordingDeviceServer:
    """Inline-Stub: zeichnet bind/listen (`start`) + close (`stop`) auf."""

    def __init__(self) -> None:
        self.start_calls: int = 0
        self.stop_calls: int = 0

    def start(self) -> None:
        self.start_calls += 1

    def stop(self) -> None:
        self.stop_calls += 1


def test_recording_stub_satisfies_device_server_port_protocol() -> None:
    """`@runtime_checkable` erlaubt isinstance ohne explizite Subclass."""
    assert isinstance(_RecordingDeviceServer(), DeviceServerPort)


def test_lifecycle_methods_record_invocation() -> None:
    server = _RecordingDeviceServer()
    server.start()
    server.stop()
    server.stop()
    assert server.start_calls == 1
    assert server.stop_calls == 2


def test_device_server_port_error_is_grid_gym_error_subclass() -> None:
    assert issubclass(DeviceServerPortError, GridGymError)


@pytest.mark.parametrize(
    "subclass",
    [DeviceServerPortStartError, DeviceServerPortStopError],
)
def test_typed_errors_inherit_from_device_server_port_error(
    subclass: type[DeviceServerPortError],
) -> None:
    """Adapter kann pauschal `DeviceServerPortError` catchen."""
    assert issubclass(subclass, DeviceServerPortError)
