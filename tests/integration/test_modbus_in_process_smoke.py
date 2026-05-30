"""M4-Welle-3-C2 Integration-Smoke fuer den Modbus-TCP-Adapter
(`ModbusDeviceProtocolPort` gegen in-process pymodbus-Server).

ADR 0032 §2.6 Decision M-f: **kein** testcontainers-Container,
sondern ein in-process `pymodbus`-Server in einem Daemon-Thread.
Begruendung: (a) Modbus-Server-Container haben restriktive
Lizenzen (M4-Welle-0 §3 Decision 5); (b) pymodbus ist BSD-3-Clause
und liefert produktiven Server mit; (c) keine Docker-Pull-Latenz.

End-to-End-Pfad:

1. `ModbusTcpServer` mit `ModbusServerContext` + `ModbusSequentialDataBlock`
   im Daemon-Thread via `asyncio.run(server.serve_forever())`.
2. Test wartet auf Connect-Bereitschaft (Bounded-Poll-Loop).
3. `ModbusDeviceProtocolPort.write(target, command)` -> Server-Datablock.
4. `ModbusDeviceProtocolPort.read(target)` -> Server-Datablock -> TelemetryPoint.
5. Verifikation: geschriebener Wert kommt durch alle 5 Datatypes zurueck.

Cross-Cutting (Lastenheft Z. 1161-1163): Smoke ist Test-Infrastruktur;
**keine produktive Anlagensteuerung**.
"""

from __future__ import annotations

import asyncio
import contextlib
import socket
import threading
import time
from collections.abc import Iterator
from types import MappingProxyType
from typing import Final

import pytest
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import ModbusTcpServer

from grid_gym.adapters.driven.protocol_modbus import (
    ModbusDatatype,
    ModbusDeviceProtocolPort,
    ModbusProtocolPortConfig,
    ModbusRegisterConfig,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult

_LOCALHOST: Final[str] = "127.0.0.1"
_DATABLOCK_SIZE: Final[int] = 200
_CONNECT_TIMEOUT_S: Final[float] = 5.0
_CONNECT_INTERVAL_S: Final[float] = 0.05
_SERVER_STOP_TIMEOUT_S: Final[float] = 5.0


def _find_free_port() -> int:
    """Findet einen freien TCP-Port auf Localhost (Race mit Server-
    Spawn ist akzeptabel — testcontainers macht es genauso)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((_LOCALHOST, 0))
        return sock.getsockname()[1]


def _wait_for_port_open(host: str, port: int, timeout_s: float) -> None:
    """Bounded-Poll: failt nach `timeout_s`, sonst kehrt sofort
    zurueck, sobald der Server akzeptiert."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(_CONNECT_INTERVAL_S)
    pytest.fail(f"Modbus-Server :{port} nicht erreichbar innerhalb {timeout_s}s")


class _InProcessServer:
    """Wrapper um den pymodbus-Server-Lifecycle.

    Spawnt `ModbusTcpServer.serve_forever()` in einem Daemon-Thread
    via `asyncio.run`. Cleanup via `server.shutdown()` plus
    `thread.join(timeout)`.
    """

    def __init__(self, port: int) -> None:
        self._port = port
        # pymodbus 3.13: ModbusSequentialDataBlock konstruiert intern
        # SimData(address-1, ...); `address=0` wuerde dort `-1`
        # erzeugen und an der `0 <= address`-Pruefung scheitern.
        # Daher Start bei 1; deckt Register-Indizes 1..200 ab.
        self._datablock = ModbusSequentialDataBlock(address=1, values=[0] * _DATABLOCK_SIZE)
        device_context = ModbusDeviceContext(
            hr=self._datablock,  # holding registers (FC03)
            ir=self._datablock,  # input registers (FC04) — gleiche Daten
        )
        self._context = ModbusServerContext(devices=device_context, single=True)
        self._server: ModbusTcpServer | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    @property
    def port(self) -> int:
        return self._port

    @property
    def datablock(self) -> ModbusSequentialDataBlock:
        return self._datablock

    def start(self) -> None:
        ready = threading.Event()

        async def _run_server() -> None:
            # `ModbusTcpServer.__init__` ruft `asyncio.get_running_loop()`
            # auf — die Konstruktion MUSS innerhalb des Loops passieren.
            self._server = ModbusTcpServer(context=self._context, address=(_LOCALHOST, self._port))
            ready.set()
            await self._server.serve_forever()

        def _thread_target() -> None:
            loop = asyncio.new_event_loop()
            self._loop = loop
            asyncio.set_event_loop(loop)
            with contextlib.suppress(Exception):
                loop.run_until_complete(_run_server())

        self._thread = threading.Thread(target=_thread_target, daemon=True)
        self._thread.start()
        ready.wait(timeout=_CONNECT_TIMEOUT_S)
        _wait_for_port_open(_LOCALHOST, self._port, _CONNECT_TIMEOUT_S)

    def stop(self) -> None:
        if self._server is not None and self._loop is not None:
            future = asyncio.run_coroutine_threadsafe(self._server.shutdown(), self._loop)
            with contextlib.suppress(Exception):
                future.result(timeout=_SERVER_STOP_TIMEOUT_S)
        if self._thread is not None:
            self._thread.join(timeout=_SERVER_STOP_TIMEOUT_S)


@pytest.fixture
def _modbus_server() -> Iterator[_InProcessServer]:
    port = _find_free_port()
    server = _InProcessServer(port)
    server.start()
    try:
        yield server
    finally:
        server.stop()


def _build_config(port: int) -> ModbusProtocolPortConfig:
    """Profil mit einem Read- und einem Write-Target pro Datatype."""
    return ModbusProtocolPortConfig(
        host=_LOCALHOST,
        port=port,
        unit_id=1,
        registers={
            "int16_w": ModbusRegisterConfig(
                address=10, datatype=ModbusDatatype.INT16, access="write"
            ),
            "int16_r": ModbusRegisterConfig(
                address=10, datatype=ModbusDatatype.INT16, access="read"
            ),
            "uint16_w": ModbusRegisterConfig(
                address=20, datatype=ModbusDatatype.UINT16, access="write"
            ),
            "uint16_r": ModbusRegisterConfig(
                address=20, datatype=ModbusDatatype.UINT16, access="read"
            ),
            "int32_w": ModbusRegisterConfig(
                address=30, datatype=ModbusDatatype.INT32, access="write"
            ),
            "int32_r": ModbusRegisterConfig(
                address=30, datatype=ModbusDatatype.INT32, access="read"
            ),
            "uint32_w": ModbusRegisterConfig(
                address=40, datatype=ModbusDatatype.UINT32, access="write"
            ),
            "uint32_r": ModbusRegisterConfig(
                address=40, datatype=ModbusDatatype.UINT32, access="read"
            ),
            "float32_w": ModbusRegisterConfig(
                address=50, datatype=ModbusDatatype.FLOAT32, access="write"
            ),
            "float32_r": ModbusRegisterConfig(
                address=50, datatype=ModbusDatatype.FLOAT32, access="read"
            ),
        },
    )


def _make_command(target: str, value: int | float) -> Command:
    return Command(
        command_id=f"cmd-{target}",
        simulation_time=0,
        target_device_id=target,
        type="set",
        payload=MappingProxyType({"value": value}),
        validation_status="validated",
        result=CommandResult.ACCEPTED,
    )


def test_modbus_adapter_roundtrip_through_all_datatypes(
    _modbus_server: _InProcessServer,
) -> None:
    """End-to-End-Pfad: Adapter schreibt einen Wert pro Datatype in
    den in-process Server-Datablock und liest ihn zurueck."""
    config = _build_config(_modbus_server.port)
    port = ModbusDeviceProtocolPort(config)
    try:
        port.start()

        # int16 (signed)
        port.write("int16_w", _make_command("int16_w", -1234))
        point = port.read("int16_r")
        assert point is not None
        assert int(point.value) == -1234

        # uint16
        port.write("uint16_w", _make_command("uint16_w", 54321))
        point = port.read("uint16_r")
        assert point is not None
        assert int(point.value) == 54321

        # int32
        port.write("int32_w", _make_command("int32_w", -123456789))
        point = port.read("int32_r")
        assert point is not None
        assert int(point.value) == -123456789

        # uint32
        port.write("uint32_w", _make_command("uint32_w", 3000000000))
        point = port.read("uint32_r")
        assert point is not None
        assert int(point.value) == 3000000000

        # float32
        port.write("float32_w", _make_command("float32_w", 3.14))
        point = port.read("float32_r")
        assert point is not None
        assert abs(float(point.value) - 3.14) < 0.001
    finally:
        port.stop()
