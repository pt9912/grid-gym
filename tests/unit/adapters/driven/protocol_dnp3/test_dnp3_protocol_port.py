"""Lifecycle + Read-Pfad-Tests fuer `Dnp3DeviceProtocolPort`
(M4 Welle 5a, ADR 0034 §2.2/§2.4).

Deckt:

- `start()` ruft `master.open()`; idempotent.
- `stop()` ruft `master.close()`; idempotent.
- `read()` vor `start()` wirft `Dnp3PortReadNotStartedError`.
- `write()` vor `start()` wirft `Dnp3PortWriteNotStartedError`.
- `read()` auf write-Target wirft `Dnp3PortReadAccessMismatchError`.
- `write()` auf read-Target wirft `Dnp3PortWriteAccessMismatchError`.
- `write()` mit `access="write"`-Target wirft konsequent
  `Dnp3PortWriteNotImplementedError` (Welle-5a-Anti-Scope).
- Unbekanntes Target → `DeviceProtocolPortUnknownTargetError`.
- Connect-Fehler → `Dnp3PortConnectError`.
- DNP3-Library-Errors am Read-Pfad → `Dnp3PortReadFailedError`.
- Codec-Decode-Fehler → `Dnp3PortReadFailedError`.
- Point nicht im Poll-Resultat → `Dnp3PortPointNotInPollResultError`.
- Class-0-Read mit `success=False` → `Dnp3PortReadFailedError`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock

import pytest
from dnp3py import DNP3CommunicationError, DNP3TimeoutError

from grid_gym.adapters.driven.protocol_dnp3 import (
    Dnp3DeviceProtocolPort,
    Dnp3PointConfig,
    Dnp3PortConnectError,
    Dnp3PortPointNotInPollResultError,
    Dnp3PortReadAccessMismatchError,
    Dnp3PortReadFailedError,
    Dnp3PortReadNotStartedError,
    Dnp3PortWriteAccessMismatchError,
    Dnp3PortWriteNotImplementedError,
    Dnp3PortWriteNotStartedError,
    Dnp3ProtocolPortConfig,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPortReadError,
    DeviceProtocolPortUnknownTargetError,
    DeviceProtocolPortWriteError,
)


@dataclass
class _MockPoint:
    """Mock fuer `nfm-dnp3.AnalogInput`/`BinaryInput`."""

    index: int
    value: object


@dataclass
class _MockPollResult:
    """Mock fuer `nfm-dnp3.PollResult`."""

    success: bool = True
    analog_inputs: list[Any] = field(default_factory=list)
    binary_inputs: list[Any] = field(default_factory=list)
    error: str = ""


def _make_command(target: str, payload: Mapping[str, object]) -> Command:
    return Command(
        command_id=f"cmd-{target}",
        simulation_time=0,
        target_device_id=target,
        type="set",
        payload=payload,
        validation_status="validated",
        result=CommandResult.ACCEPTED,
    )


def _make_config() -> Dnp3ProtocolPortConfig:
    return Dnp3ProtocolPortConfig(
        host="127.0.0.1",
        port=20000,
        master_address=1,
        outstation_address=10,
        points={
            "battery1_voltage": Dnp3PointConfig(group=30, variation=5, index=0, access="read"),
            "battery1_setpoint": Dnp3PointConfig(group=30, variation=5, index=10, access="write"),
            "battery1_status": Dnp3PointConfig(group=1, variation=1, index=0, access="read"),
        },
        response_timeout_s=2.0,
    )


def _make_mock_master(
    *,
    open_raises: BaseException | None = None,
    read_class_raises: BaseException | None = None,
    poll: _MockPollResult | None = None,
) -> Any:
    master = MagicMock()
    master.open = MagicMock(side_effect=open_raises)
    master.close = MagicMock()
    if read_class_raises is not None:
        master.read_class = MagicMock(side_effect=read_class_raises)
    else:
        if poll is None:
            poll = _MockPollResult(
                success=True,
                analog_inputs=[_MockPoint(index=0, value=42.5)],
            )
        master.read_class = MagicMock(return_value=poll)
    return master


def test_start_stop_lifecycle_idempotent() -> None:
    config = _make_config()
    master = _make_mock_master()
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)

    port.start()
    port.start()  # idempotent
    assert master.open.call_count == 1

    port.stop()
    port.stop()  # idempotent
    assert master.close.call_count == 1


def test_start_translates_connect_error() -> None:
    config = _make_config()
    master = _make_mock_master(open_raises=OSError("connection refused"))
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)

    with pytest.raises(Dnp3PortConnectError) as exc_info:
        port.start()
    assert exc_info.value.host == "127.0.0.1"
    assert exc_info.value.port == 20000


def test_read_before_start_raises_typed_error() -> None:
    config = _make_config()
    master = _make_mock_master()
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)

    with pytest.raises(Dnp3PortReadNotStartedError) as exc_info:
        port.read("battery1_voltage")
    assert exc_info.value.target == "battery1_voltage"
    assert isinstance(exc_info.value, DeviceProtocolPortReadError)


def test_write_before_start_raises_typed_error() -> None:
    config = _make_config()
    master = _make_mock_master()
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)

    with pytest.raises(Dnp3PortWriteNotStartedError) as exc_info:
        port.write("battery1_setpoint", _make_command("battery1_setpoint", {"value": 1.0}))
    assert exc_info.value.target == "battery1_setpoint"
    assert isinstance(exc_info.value, DeviceProtocolPortWriteError)


def test_read_on_write_target_raises_access_mismatch() -> None:
    config = _make_config()
    master = _make_mock_master()
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)
    port.start()
    try:
        with pytest.raises(Dnp3PortReadAccessMismatchError):
            port.read("battery1_setpoint")
    finally:
        port.stop()


def test_write_on_read_target_raises_access_mismatch() -> None:
    config = _make_config()
    master = _make_mock_master()
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)
    port.start()
    try:
        with pytest.raises(Dnp3PortWriteAccessMismatchError):
            port.write("battery1_voltage", _make_command("battery1_voltage", {"value": 1.0}))
    finally:
        port.stop()


def test_write_with_write_target_raises_not_implemented() -> None:
    """Welle-5a-Anti-Scope: Write-Pfad ist nicht produktiv."""
    config = _make_config()
    master = _make_mock_master()
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)
    port.start()
    try:
        with pytest.raises(Dnp3PortWriteNotImplementedError) as exc_info:
            port.write(
                "battery1_setpoint",
                _make_command("battery1_setpoint", {"value": 100.0}),
            )
        assert exc_info.value.target == "battery1_setpoint"
        assert isinstance(exc_info.value, DeviceProtocolPortWriteError)
    finally:
        port.stop()


def test_unknown_target_read_raises() -> None:
    config = _make_config()
    master = _make_mock_master()
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)
    port.start()
    try:
        with pytest.raises(DeviceProtocolPortUnknownTargetError) as exc_info:
            port.read("nonexistent")
        assert exc_info.value.target == "nonexistent"
    finally:
        port.stop()


def test_read_returns_telemetry_with_decoded_float() -> None:
    config = _make_config()
    master = _make_mock_master(
        poll=_MockPollResult(
            success=True,
            analog_inputs=[_MockPoint(index=0, value=42.5)],
        )
    )
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)
    port.start()
    try:
        point = port.read("battery1_voltage")
        assert point is not None
        assert point.device_id == "battery1_voltage"
        assert point.source == "protocol_dnp3.battery1_voltage"
        assert point.metric == "g30v5"
        assert float(point.value) == pytest.approx(42.5)
    finally:
        port.stop()


def test_read_returns_telemetry_with_decoded_binary() -> None:
    config = _make_config()
    master = _make_mock_master(
        poll=_MockPollResult(
            success=True,
            binary_inputs=[_MockPoint(index=0, value=True)],
        )
    )
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)
    port.start()
    try:
        point = port.read("battery1_status")
        assert point is not None
        assert point.metric == "g1v1"
        assert point.value == Decimal(1)
    finally:
        port.stop()


def test_read_translates_communication_error_to_read_failed() -> None:
    config = _make_config()
    master = _make_mock_master(read_class_raises=DNP3CommunicationError("connection lost"))
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)
    port.start()
    try:
        with pytest.raises(Dnp3PortReadFailedError) as exc_info:
            port.read("battery1_voltage")
        assert exc_info.value.target == "battery1_voltage"
        assert exc_info.value.group == 30
    finally:
        port.stop()


def test_read_translates_timeout_to_read_failed() -> None:
    config = _make_config()
    master = _make_mock_master(read_class_raises=DNP3TimeoutError("response timeout"))
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)
    port.start()
    try:
        with pytest.raises(Dnp3PortReadFailedError):
            port.read("battery1_voltage")
    finally:
        port.stop()


def test_read_fails_when_poll_success_is_false() -> None:
    config = _make_config()
    master = _make_mock_master(
        poll=_MockPollResult(success=False, error="server iin error"),
    )
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)
    port.start()
    try:
        with pytest.raises(Dnp3PortReadFailedError) as exc_info:
            port.read("battery1_voltage")
        assert "poll error" in str(exc_info.value)
    finally:
        port.stop()


def test_read_fails_when_point_not_in_poll_result() -> None:
    config = _make_config()
    master = _make_mock_master(
        poll=_MockPollResult(
            success=True,
            analog_inputs=[_MockPoint(index=99, value=1.0)],  # falscher idx
        )
    )
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)
    port.start()
    try:
        with pytest.raises(Dnp3PortPointNotInPollResultError) as exc_info:
            port.read("battery1_voltage")
        assert exc_info.value.target == "battery1_voltage"
        assert exc_info.value.index == 0
    finally:
        port.stop()


def test_read_translates_codec_value_type_error_to_read_failed() -> None:
    """Server liefert AnalogInput.value=None — Codec wirft typed
    Error, Adapter mantelt in Dnp3PortReadFailedError."""
    config = _make_config()
    master = _make_mock_master(
        poll=_MockPollResult(
            success=True,
            analog_inputs=[_MockPoint(index=0, value=None)],
        )
    )
    port = Dnp3DeviceProtocolPort(config, client_factory=lambda _cfg: master)
    port.start()
    try:
        with pytest.raises(Dnp3PortReadFailedError):
            port.read("battery1_voltage")
    finally:
        port.stop()
