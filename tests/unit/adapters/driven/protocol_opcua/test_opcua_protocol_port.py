"""Lifecycle + Read/Write-Tests fuer `OpcuaDeviceProtocolPort`
(M4 Welle 4, ADR 0033 §2.2/§2.4).

Deckt:

- `start()` ruft `client.connect()` (Coroutine, gemarshalled).
- `stop()` ruft `client.disconnect()` und baut Loop-Thread ab.
- Idempotenz Start/Stop.
- `read()` vor `start()` wirft `OpcuaPortReadNotStartedError`.
- `write()` vor `start()` wirft `OpcuaPortWriteNotStartedError`.
- `read()` auf write-Target wirft `OpcuaPortReadAccessMismatchError`.
- `write()` auf read-Target wirft `OpcuaPortWriteAccessMismatchError`.
- Unbekanntes Target wirft `DeviceProtocolPortUnknownTargetError`.
- Connect-Fehler wird in `OpcuaPortConnectError` umgemantelt.
- Read-/Write-Failure wird in `OpcuaPortRead/WriteFailedError`
  umgemantelt.
- Codec-Encode-Fehler wird in `OpcuaPortWriteFailedError` umgemantelt.
- Codec-Decode-Fehler wird in `OpcuaPortReadFailedError` umgemantelt.
- `command.payload` ohne `value` wirft
  `OpcuaPortMissingCommandPayloadError`.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from asyncua import ua
from asyncua.ua import uaerrors

from grid_gym.adapters.driven.protocol_opcua import (
    OpcuaDatatype,
    OpcuaDeviceProtocolPort,
    OpcuaNodeConfig,
    OpcuaPortConnectError,
    OpcuaPortMissingCommandPayloadError,
    OpcuaPortReadAccessMismatchError,
    OpcuaPortReadFailedError,
    OpcuaPortReadNotStartedError,
    OpcuaPortWriteAccessMismatchError,
    OpcuaPortWriteFailedError,
    OpcuaPortWriteNotStartedError,
    OpcuaProtocolPortConfig,
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


def _make_config() -> OpcuaProtocolPortConfig:
    return OpcuaProtocolPortConfig(
        endpoint_url="opc.tcp://localhost:14840",
        nodes={
            "battery1_soc": OpcuaNodeConfig(
                node_id="ns=2;i=1001",
                datatype=OpcuaDatatype.FLOAT,
                access="read",
            ),
            "battery1_setpoint": OpcuaNodeConfig(
                node_id="ns=2;i=1002",
                datatype=OpcuaDatatype.INT16,
                access="write",
            ),
        },
        timeout_s=2.0,
    )


def _make_mock_client(
    *,
    read_value: Any = 50.0,
    connect_raises: BaseException | None = None,
    read_raises: BaseException | None = None,
    write_raises: BaseException | None = None,
) -> Any:
    client = MagicMock()
    client.connect = AsyncMock(side_effect=connect_raises)
    client.disconnect = AsyncMock()

    node = MagicMock()
    if read_raises is not None:
        node.read_value = AsyncMock(side_effect=read_raises)
    else:
        node.read_value = AsyncMock(return_value=read_value)
    if write_raises is not None:
        node.write_value = AsyncMock(side_effect=write_raises)
    else:
        node.write_value = AsyncMock()

    client.get_node = MagicMock(return_value=node)
    return client


def test_start_stop_lifecycle_idempotent() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)

    port.start()
    port.start()  # idempotent
    assert client.connect.await_count == 1

    port.stop()
    port.stop()  # idempotent
    assert client.disconnect.await_count == 1


def test_start_translates_connect_error() -> None:
    config = _make_config()
    client = _make_mock_client(connect_raises=OSError("connection refused"))
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)

    with pytest.raises(OpcuaPortConnectError) as exc_info:
        port.start()
    assert "opc.tcp://localhost:14840" in str(exc_info.value)


def test_read_before_start_raises_typed_error() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)

    with pytest.raises(OpcuaPortReadNotStartedError) as exc_info:
        port.read("battery1_soc")
    assert exc_info.value.target == "battery1_soc"
    # Catchable als DeviceProtocolPortReadError.
    assert isinstance(exc_info.value, DeviceProtocolPortReadError)


def test_write_before_start_raises_typed_error() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)

    with pytest.raises(OpcuaPortWriteNotStartedError) as exc_info:
        port.write("battery1_setpoint", _make_command("battery1_setpoint", {"value": 42}))
    assert exc_info.value.target == "battery1_setpoint"
    assert isinstance(exc_info.value, DeviceProtocolPortWriteError)


def test_read_on_write_target_raises_access_mismatch() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(OpcuaPortReadAccessMismatchError):
            port.read("battery1_setpoint")
    finally:
        port.stop()


def test_write_on_read_target_raises_access_mismatch() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(OpcuaPortWriteAccessMismatchError):
            port.write("battery1_soc", _make_command("battery1_soc", {"value": 42}))
    finally:
        port.stop()


def test_unknown_target_read_raises() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(DeviceProtocolPortUnknownTargetError) as exc_info:
            port.read("nonexistent")
        assert exc_info.value.target == "nonexistent"
    finally:
        port.stop()


def test_read_returns_telemetry_point_with_decoded_value() -> None:
    config = _make_config()
    client = _make_mock_client(read_value=42.5)
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        point = port.read("battery1_soc")
        assert point is not None
        assert point.device_id == "battery1_soc"
        assert point.source == "protocol_opcua.battery1_soc"
        # Decimal via repr fuer Float.
        assert isinstance(point.value, Decimal)
        assert float(point.value) == pytest.approx(42.5)
    finally:
        port.stop()


def test_read_translates_uaerror_to_read_failed() -> None:
    config = _make_config()
    client = _make_mock_client(read_raises=uaerrors.BadNotConnected("not connected"))
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(OpcuaPortReadFailedError) as exc_info:
            port.read("battery1_soc")
        assert exc_info.value.target == "battery1_soc"
        assert exc_info.value.node_id == "ns=2;i=1001"
    finally:
        port.stop()


def test_read_translates_codec_decode_error_to_read_failed() -> None:
    config = _make_config()
    # Server liefert einen String, obwohl Datatype = FLOAT.
    client = _make_mock_client(read_value="not-a-float")
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(OpcuaPortReadFailedError):
            port.read("battery1_soc")
    finally:
        port.stop()


def test_write_writes_variant_via_node() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        port.write("battery1_setpoint", _make_command("battery1_setpoint", {"value": 1000}))
        # Verify write_value called.
        node = client.get_node.return_value
        assert node.write_value.await_count == 1
        variant_arg = node.write_value.await_args.args[0]
        assert isinstance(variant_arg, ua.Variant)
        assert variant_arg.Value == 1000
        assert variant_arg.VariantType is ua.VariantType.Int16
    finally:
        port.stop()


def test_write_missing_value_raises_typed_error() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(OpcuaPortMissingCommandPayloadError):
            port.write("battery1_setpoint", _make_command("battery1_setpoint", {}))
    finally:
        port.stop()


def test_write_translates_uaerror_to_write_failed() -> None:
    config = _make_config()
    client = _make_mock_client(write_raises=uaerrors.BadUserAccessDenied("denied"))
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(OpcuaPortWriteFailedError):
            port.write("battery1_setpoint", _make_command("battery1_setpoint", {"value": 100}))
    finally:
        port.stop()


def test_write_translates_codec_encode_error_to_write_failed() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        # Int16 mit Out-of-Range-Wert.
        with pytest.raises(OpcuaPortWriteFailedError):
            port.write("battery1_setpoint", _make_command("battery1_setpoint", {"value": 2**20}))
    finally:
        port.stop()


def test_read_string_target_marks_quality_invalid_with_original_string() -> None:
    """Slice-032-Schaerfung (Finding 3.1): String-Reads markieren
    `Quality.INVALID` und kodieren den Original-String im
    `source`-Feld, damit Downstream-Konsumenten den Sentinel-Wert
    `Decimal(0)` nicht als echten Messwert missinterpretieren."""
    from grid_gym.hexagon.core.domain.quality import Quality

    config = OpcuaProtocolPortConfig(
        endpoint_url="opc.tcp://localhost:14840",
        nodes={
            "string_r": OpcuaNodeConfig(
                node_id="ns=2;s=Inverter.Serial",
                datatype=OpcuaDatatype.STRING,
                access="read",
            ),
        },
    )
    client = _make_mock_client(read_value="SN-12345")
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        point = port.read("string_r")
        assert point is not None
        assert point.value == Decimal(0)
        assert point.quality is Quality.INVALID
        assert point.source == "protocol_opcua.string_r#string=SN-12345"
    finally:
        port.stop()


def test_read_int_target_returns_telemetry_with_decimal_value() -> None:
    """Integer-Reads -> Decimal direkt (kein Float-Repr-Pfad)."""
    config = OpcuaProtocolPortConfig(
        endpoint_url="opc.tcp://localhost:14840",
        nodes={
            "int_r": OpcuaNodeConfig(
                node_id="ns=2;i=100",
                datatype=OpcuaDatatype.INT32,
                access="read",
            ),
        },
    )
    client = _make_mock_client(read_value=12345)
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        point = port.read("int_r")
        assert point is not None
        assert point.value == Decimal(12345)
    finally:
        port.stop()


def test_write_unsupported_payload_type_raises_write_failed() -> None:
    config = _make_config()
    client = _make_mock_client()
    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        with pytest.raises(OpcuaPortWriteFailedError):
            port.write(
                "battery1_setpoint",
                _make_command("battery1_setpoint", {"value": [1, 2, 3]}),
            )
    finally:
        port.stop()


def test_read_marshals_coroutine_through_loop_thread() -> None:
    """Slice-032-Schaerfung (Finding 4.1): explizit pruefen, dass
    `read()` die Coroutine ueber den Loop-Thread marshalt — nicht
    direkt im Caller-Thread ausfuehrt. Bei einer Refactor-Regression
    (z. B. `asyncio.run` statt `run_coroutine`) muss der Test rot
    werden.

    Mechanik: AsyncMock-`read_value` cached die `current_thread`-ID
    und der Test verifiziert, dass diese **nicht** der Test-Thread-ID
    entspricht."""
    import threading as _threading

    config = _make_config()
    captured: dict[str, int] = {}

    async def _capturing_read() -> float:
        # `await asyncio.sleep(0)` macht die Coroutine wirklich async
        # und triggert ruff's RUF029 nicht; gleichzeitig laesst es den
        # Loop-Thread-Marshal real laufen.
        import asyncio as _asyncio

        await _asyncio.sleep(0)
        captured["thread_id"] = _threading.get_ident()
        return 42.5

    client = MagicMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    node = MagicMock()
    node.read_value = _capturing_read
    client.get_node = MagicMock(return_value=node)

    port = OpcuaDeviceProtocolPort(config, client_factory=lambda _cfg: client)
    port.start()
    try:
        caller_thread_id = _threading.get_ident()
        port.read("battery1_soc")
        assert "thread_id" in captured
        # Coroutine wurde im Loop-Thread ausgefuehrt, NICHT im Caller-Thread.
        assert captured["thread_id"] != caller_thread_id
    finally:
        port.stop()
