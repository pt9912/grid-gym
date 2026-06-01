# SPDX-License-Identifier: GPL-3.0-only
"""Lifecycle + Read-Pfad-Tests fuer `Iec61850DeviceProtocolPort`
(M4 Welle 5b, ADR 0035 §2.2/§2.4).

Deckt:

- `start()` ruft `client.connect()`; idempotent.
- `stop()` ruft `client.disconnect()`; idempotent.
- `read()` vor `start()` wirft `Iec61850PortReadNotStartedError`.
- `write()` vor `start()` wirft `Iec61850PortWriteNotStartedError`.
- `read()` auf write-Target wirft `Iec61850PortReadAccessMismatchError`.
- `write()` auf read-Target wirft `Iec61850PortWriteAccessMismatchError`.
- `write()` mit `access="write"`-Target wirft konsequent
  `Iec61850PortWriteNotImplementedError` (Welle-5b-Anti-Scope).
- Unbekanntes Target → `DeviceProtocolPortUnknownTargetError`.
- Connect-Fehler → `Iec61850PortConnectError`.
- pyiec61850-Library-Errors am Read-Pfad → typed Adapter-Errors.
- Codec-Decode-Fehler → `Iec61850PortReadFailedError`.
- Object-Reference-Not-Found → `Iec61850PortPointNotFoundError`.

Alle Tests laufen gegen einen Mock-Client (`client_factory`-
Hook), nicht gegen die echte `pyiec61850-ng`-Library. Damit
laufen sie auch ohne installiertes Optional-Extra
`grid-gym[iec61850]`.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock

import pytest

from grid_gym.adapters.driven.protocol_iec61850 import (
    Iec61850DeviceProtocolPort,
    Iec61850LnConfig,
    Iec61850PortConnectError,
    Iec61850PortPointNotFoundError,
    Iec61850PortReadAccessMismatchError,
    Iec61850PortReadFailedError,
    Iec61850PortReadNotStartedError,
    Iec61850PortWriteAccessMismatchError,
    Iec61850PortWriteNotImplementedError,
    Iec61850PortWriteNotStartedError,
    Iec61850ProtocolPortConfig,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPortReadError,
    DeviceProtocolPortUnknownTargetError,
    DeviceProtocolPortWriteError,
)


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


def _make_config() -> Iec61850ProtocolPortConfig:
    return Iec61850ProtocolPortConfig(
        host="127.0.0.1",
        ied_name="SimpleIO",
        port=10102,
        points={
            "battery1_voltage": Iec61850LnConfig(
                object_reference="simpleIOGenericIO/GGIO1.AnIn1.mag.f",
                functional_constraint="MX",
                datatype="float",
                access="read",
            ),
            "battery1_setpoint": Iec61850LnConfig(
                object_reference="simpleIOGenericIO/GGIO1.SPCSO1.Oper.ctlVal",
                functional_constraint="CF",
                datatype="float",
                access="write",
            ),
            "battery1_status": Iec61850LnConfig(
                object_reference="simpleIOGenericIO/GGIO1.Ind1.stVal",
                functional_constraint="ST",
                datatype="bool",
                access="read",
            ),
            "battery1_count": Iec61850LnConfig(
                object_reference="simpleIOGenericIO/GGIO1.IntIn1.stVal",
                functional_constraint="MX",
                datatype="int32",
                access="read",
            ),
            "battery1_label": Iec61850LnConfig(
                object_reference="simpleIOGenericIO/GGIO1.NamPlt.d",
                functional_constraint="DC",
                datatype="string",
                access="read",
            ),
        },
        response_timeout_s=2.0,
    )


def _make_mock_client(
    *,
    connect_raises: BaseException | None = None,
    read_value_raises: BaseException | None = None,
    read_value_return: Any = None,
) -> Any:
    client = MagicMock()
    if connect_raises is not None:
        client.connect = MagicMock(side_effect=connect_raises)
    else:
        client.connect = MagicMock(return_value=True)
    client.disconnect = MagicMock()
    if read_value_raises is not None:
        client.read_value = MagicMock(side_effect=read_value_raises)
    else:
        client.read_value = MagicMock(return_value=read_value_return)
    return client


def test_start_stop_lifecycle_idempotent() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)

    port.start()
    port.start()  # idempotent
    assert client.connect.call_count == 1

    port.stop()
    port.stop()  # idempotent
    assert client.disconnect.call_count == 1


def test_start_translates_connect_error() -> None:
    config = _make_config()
    client = _make_mock_client(connect_raises=OSError("connection refused"))
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)

    with pytest.raises(Iec61850PortConnectError) as exc_info:
        port.start()
    assert exc_info.value.host == "127.0.0.1"
    assert exc_info.value.port == 10102


def test_read_before_start_raises_typed_error() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)

    with pytest.raises(Iec61850PortReadNotStartedError) as exc_info:
        port.read("battery1_voltage")
    assert exc_info.value.target == "battery1_voltage"
    assert isinstance(exc_info.value, DeviceProtocolPortReadError)


def test_write_before_start_raises_typed_error() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)

    with pytest.raises(Iec61850PortWriteNotStartedError) as exc_info:
        port.write("battery1_setpoint", _make_command("battery1_setpoint", {"value": 1.0}))
    assert exc_info.value.target == "battery1_setpoint"
    assert isinstance(exc_info.value, DeviceProtocolPortWriteError)


def test_read_on_write_target_raises_access_mismatch() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(Iec61850PortReadAccessMismatchError):
            port.read("battery1_setpoint")
    finally:
        port.stop()


def test_write_on_read_target_raises_access_mismatch() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(Iec61850PortWriteAccessMismatchError):
            port.write("battery1_voltage", _make_command("battery1_voltage", {"value": 1.0}))
    finally:
        port.stop()


def test_write_with_write_target_raises_not_implemented() -> None:
    """Welle-5b-Anti-Scope: Write-Pfad ist nicht produktiv."""
    config = _make_config()
    client = _make_mock_client()
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(Iec61850PortWriteNotImplementedError) as exc_info:
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
    client = _make_mock_client()
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(DeviceProtocolPortUnknownTargetError) as exc_info:
            port.read("nonexistent")
        assert exc_info.value.target == "nonexistent"
    finally:
        port.stop()


def test_read_returns_telemetry_with_decoded_float() -> None:
    config = _make_config()
    client = _make_mock_client(read_value_return=230.5)
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        point = port.read("battery1_voltage")
        assert point is not None
        assert point.device_id == "battery1_voltage"
        assert point.source == "protocol_iec61850.battery1_voltage"
        assert point.metric == "MX.float"
        assert float(point.value) == pytest.approx(230.5)
        # client.read_value wurde mit korrekter reference + fc gerufen
        client.read_value.assert_called_once_with("simpleIOGenericIO/GGIO1.AnIn1.mag.f", "MX")
    finally:
        port.stop()


def test_read_returns_telemetry_with_decoded_int32() -> None:
    config = _make_config()
    client = _make_mock_client(read_value_return=42)
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        point = port.read("battery1_count")
        assert point is not None
        assert point.metric == "MX.int32"
        assert point.value == 42
    finally:
        port.stop()


def test_read_returns_telemetry_with_decoded_string() -> None:
    config = _make_config()
    client = _make_mock_client(read_value_return="battery-1")
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        point = port.read("battery1_label")
        assert point is not None
        assert point.metric == "DC.string"
        assert point.value == "battery-1"
        client.read_value.assert_called_once_with("simpleIOGenericIO/GGIO1.NamPlt.d", "DC")
    finally:
        port.stop()


def test_read_returns_telemetry_with_decoded_bool() -> None:
    config = _make_config()
    client = _make_mock_client(read_value_return=True)
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        point = port.read("battery1_status")
        assert point is not None
        assert point.metric == "ST.bool"
        assert point.value is True
    finally:
        port.stop()


def test_read_translates_library_read_error_to_read_failed() -> None:
    # `_PyIecReadError` ist im Adapter-Modul ein konkreter
    # pyiec61850-Type (mit installierter Library) ODER `Exception`
    # (im Optional-Extra-Off-Pfad). Wir werfen daher eine generische
    # `Exception` mit „read failed" als Library-Approximation —
    # der Adapter mantelt sie via `_PyIecMMSError`/`_PyIecReadError`-
    # Catch-Klausel.
    from grid_gym.adapters.driven.protocol_iec61850 import _port

    library_error = _port._PyIecReadError("read failed at server")
    config = _make_config()
    client = _make_mock_client(read_value_raises=library_error)
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(Iec61850PortReadFailedError) as exc_info:
            port.read("battery1_voltage")
        assert exc_info.value.target == "battery1_voltage"
        assert exc_info.value.reference == "simpleIOGenericIO/GGIO1.AnIn1.mag.f"
    finally:
        port.stop()


def test_read_translates_object_not_found_to_point_not_found_error() -> None:
    from grid_gym.adapters.driven.protocol_iec61850 import _port

    library_error = _port._PyIecReadError("Object reference not found")
    config = _make_config()
    client = _make_mock_client(read_value_raises=library_error)
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(Iec61850PortPointNotFoundError) as exc_info:
            port.read("battery1_voltage")
        assert exc_info.value.reference == "simpleIOGenericIO/GGIO1.AnIn1.mag.f"
    finally:
        port.stop()


def test_read_translates_codec_value_type_error_to_read_failed() -> None:
    """Library liefert MmsValue-Container statt Leaf — Codec wirft
    typed Error, Adapter mantelt in Iec61850PortReadFailedError."""
    config = _make_config()
    client = _make_mock_client(read_value_return="<MmsValue type=15>")
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(Iec61850PortReadFailedError):
            port.read("battery1_voltage")
    finally:
        port.stop()


def test_read_translates_int32_overflow_to_read_failed() -> None:
    config = _make_config()
    client = _make_mock_client(read_value_return=2**31)
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(Iec61850PortReadFailedError) as exc_info:
            port.read("battery1_count")
        assert "Overflow" in str(exc_info.value) or "range" in str(exc_info.value).lower()
    finally:
        port.stop()


def test_telemetry_point_quality_is_valid() -> None:
    from grid_gym.hexagon.core.domain.quality import Quality

    config = _make_config()
    client = _make_mock_client(read_value_return=230.5)
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        point = port.read("battery1_voltage")
        assert point is not None
        assert point.quality == Quality.VALID
    finally:
        port.stop()


def test_telemetry_point_value_is_decimal_for_float() -> None:
    config = _make_config()
    client = _make_mock_client(read_value_return=230.5)
    port = Iec61850DeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        point = port.read("battery1_voltage")
        assert point is not None
        assert isinstance(point.value, Decimal)
    finally:
        port.stop()
