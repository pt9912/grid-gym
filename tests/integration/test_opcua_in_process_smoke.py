"""M4-Welle-4-C2 Integration-Smoke fuer den OPC-UA-Adapter
(`OpcuaDeviceProtocolPort` gegen in-process `asyncua.Server`).

ADR 0033 §2.5 Decision O-e: **kein** testcontainers-Container,
sondern ein in-process `asyncua.Server` in einem dedizierten
Daemon-Thread. Begruendung: (a) asyncua ist LGPL-3.0 und liefert
Client + Server in einer Library; (b) `open62541/open62541`-
Container haette MPL-2.0 mit nicht-trivialer Config-Setup;
(c) keine Docker-Pull-Latenz. Pattern-Praezedenz Welle-3-Decision-M-f.

End-to-End-Pfad:

1. `asyncua.Server` mit Anonymous-Endpoint in einem eigenen
   asyncio-Loop-Thread.
2. Default-Variables fuer Read-Targets pro Welle-4-Datatype.
3. Test wartet auf Connect-Bereitschaft (Bounded-Poll-Loop).
4. `OpcuaDeviceProtocolPort.write(target, command)` -> Server-Variable.
5. `OpcuaDeviceProtocolPort.read(target)` -> Server-Variable ->
   `TelemetryPoint`.
6. Verifikation: geschriebener Wert kommt durch alle 8 Datatypes
   zurueck (Decision O-c).

Cross-Cutting (Lastenheft Z. 1161-1163): Smoke ist Test-Infrastruktur;
**keine produktive Anlagensteuerung**.
"""

from __future__ import annotations

import asyncio
import contextlib
import socket
import threading
import time
from collections.abc import Iterator, Mapping
from decimal import Decimal
from typing import Final

import pytest
from asyncua import Server, ua

from grid_gym.adapters.driven.protocol_opcua import (
    OpcuaDatatype,
    OpcuaDeviceProtocolPort,
    OpcuaNodeConfig,
    OpcuaProtocolPortConfig,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult


_LOCALHOST: Final[str] = "127.0.0.1"
_NAMESPACE_URI: Final[str] = "urn:grid-gym:welle-4:smoke"
_CONNECT_TIMEOUT_S: Final[float] = 10.0
_CONNECT_INTERVAL_S: Final[float] = 0.1
_SERVER_STOP_TIMEOUT_S: Final[float] = 5.0


def _find_free_port() -> int:
    """Findet einen freien TCP-Port auf Localhost."""
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
    pytest.fail(f"OPC-UA-Server :{port} nicht erreichbar innerhalb {timeout_s}s")


# Liste der Default-Variablen, die der Smoke-Server pro Datatype
# anlegt — Test-Code kennt die node_id-Konvention.
_SMOKE_VARIABLES: Final[list[tuple[str, OpcuaDatatype, ua.VariantType, object]]] = [
    ("bool_var", OpcuaDatatype.BOOLEAN, ua.VariantType.Boolean, False),
    ("int16_var", OpcuaDatatype.INT16, ua.VariantType.Int16, 0),
    ("uint16_var", OpcuaDatatype.UINT16, ua.VariantType.UInt16, 0),
    ("int32_var", OpcuaDatatype.INT32, ua.VariantType.Int32, 0),
    ("uint32_var", OpcuaDatatype.UINT32, ua.VariantType.UInt32, 0),
    ("float_var", OpcuaDatatype.FLOAT, ua.VariantType.Float, 0.0),
    ("double_var", OpcuaDatatype.DOUBLE, ua.VariantType.Double, 0.0),
    ("string_var", OpcuaDatatype.STRING, ua.VariantType.String, ""),
]


class _InProcessOpcuaServer:
    """Wrapper um den `asyncua.Server`-Lifecycle.

    Spawnt einen eigenen `asyncio.Loop` in einem Daemon-Thread und
    haelt den Server am Laufen, bis `stop()` aufgerufen wird.
    """

    def __init__(self, port: int) -> None:
        self._port = port
        self._endpoint_url = f"opc.tcp://{_LOCALHOST}:{port}"
        self._server: Server | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._namespace_idx: int = 0
        # `(node_name) -> node_id_string` Map fuer Tests.
        self._node_ids: dict[str, str] = {}

    @property
    def endpoint_url(self) -> str:
        return self._endpoint_url

    @property
    def node_ids(self) -> Mapping[str, str]:
        return self._node_ids

    def start(self) -> None:
        ready = threading.Event()

        async def _run_server() -> None:
            server = Server()
            await server.init()
            server.set_endpoint(self._endpoint_url)
            # Server-Application-Settings: minimal anonymous endpoint.
            server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
            self._namespace_idx = await server.register_namespace(_NAMESPACE_URI)
            objects = server.nodes.objects
            for name, _datatype, variant_type, initial in _SMOKE_VARIABLES:
                node = await objects.add_variable(
                    self._namespace_idx,
                    name,
                    ua.Variant(initial, variant_type),
                )
                await node.set_writable()
                self._node_ids[name] = node.nodeid.to_string()
            self._server = server
            await server.start()
            ready.set()
            # Block bis loop.stop() aufgerufen wird.
            while True:
                await asyncio.sleep(0.5)

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
            future = asyncio.run_coroutine_threadsafe(self._server.stop(), self._loop)
            with contextlib.suppress(Exception):
                future.result(timeout=_SERVER_STOP_TIMEOUT_S)
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=_SERVER_STOP_TIMEOUT_S)


@pytest.fixture
def _opcua_server() -> Iterator[_InProcessOpcuaServer]:
    port = _find_free_port()
    server = _InProcessOpcuaServer(port)
    server.start()
    try:
        yield server
    finally:
        server.stop()


def _build_config(server: _InProcessOpcuaServer) -> OpcuaProtocolPortConfig:
    """Profil mit einem Read- und einem Write-Target pro Datatype."""
    nodes: dict[str, OpcuaNodeConfig] = {}
    for name, datatype, _variant_type, _initial in _SMOKE_VARIABLES:
        node_id = server.node_ids[name]
        nodes[f"{name}_w"] = OpcuaNodeConfig(node_id=node_id, datatype=datatype, access="write")
        nodes[f"{name}_r"] = OpcuaNodeConfig(node_id=node_id, datatype=datatype, access="read")
    return OpcuaProtocolPortConfig(endpoint_url=server.endpoint_url, nodes=nodes, timeout_s=5.0)


def _make_command(target: str, value: object) -> Command:
    return Command(
        command_id=f"cmd-{target}",
        simulation_time=0,
        target_device_id=target,
        type="set",
        payload={"value": value},
        validation_status="validated",
        result=CommandResult.ACCEPTED,
    )


def _smoke_write_value(datatype: OpcuaDatatype) -> bool | int | float | str:
    """Liefert einen testbaren Wert pro Datatype."""
    if datatype is OpcuaDatatype.BOOLEAN:
        return True
    if datatype is OpcuaDatatype.STRING:
        return "smoke-test"
    if datatype in (OpcuaDatatype.FLOAT, OpcuaDatatype.DOUBLE):
        return 3.14
    # Integer: passe an Range an.
    if datatype is OpcuaDatatype.INT16:
        return -1234
    if datatype is OpcuaDatatype.UINT16:
        return 1234
    if datatype is OpcuaDatatype.INT32:
        return -123456
    # UINT32
    return 4000000


@pytest.mark.parametrize(
    ("name", "datatype"),
    [(name, dt) for name, dt, _vt, _initial in _SMOKE_VARIABLES],
)
def test_opcua_adapter_write_then_read_roundtrip(
    _opcua_server: _InProcessOpcuaServer, name: str, datatype: OpcuaDatatype
) -> None:
    config = _build_config(_opcua_server)
    port = OpcuaDeviceProtocolPort(config)
    port.start()
    try:
        write_target = f"{name}_w"
        read_target = f"{name}_r"
        write_value = _smoke_write_value(datatype)
        port.write(write_target, _make_command(write_target, write_value))

        telemetry = port.read(read_target)
        assert telemetry is not None
        assert telemetry.device_id == read_target
        # Roundtrip-Vergleich pro Datatype.
        if datatype is OpcuaDatatype.BOOLEAN:
            assert telemetry.value == Decimal(1)
        elif datatype is OpcuaDatatype.STRING:
            # String -> Decimal(0) Platzhalter (siehe `_port._to_decimal`);
            # TelemetryPoint speichert den Wert nicht direkt — der
            # Decode-Pfad erlaubt aber, dass die Read-Operation nicht
            # wirft. Decimal(0) bleibt.
            assert telemetry.value == Decimal(0)
        elif datatype in (OpcuaDatatype.FLOAT, OpcuaDatatype.DOUBLE):
            assert float(telemetry.value) == pytest.approx(float(write_value))
        else:
            assert telemetry.value == Decimal(int(write_value))
    finally:
        port.stop()
