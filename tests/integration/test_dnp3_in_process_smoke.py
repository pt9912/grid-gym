"""M4-Welle-5a-C2 Integration-Smoke fuer den DNP3-Adapter
(`Dnp3DeviceProtocolPort` gegen in-process `dnp3_outstation.AsyncOutstation`).

ADR 0034 §2.5 Decision D-e: **kein** testcontainers-Container,
sondern ein in-process `AsyncOutstation` in einem dedizierten
Daemon-Thread + asyncio-Loop. Begruendung: (a) `dnp3-outstation`
ist MIT, Pure-Python, asyncio-native, IEEE-1815-2012-Level-1-
Subset; (b) Pattern-Praezedenz Welle-3-Decision-M-f (pymodbus
in-process) + Welle-4-Decision-O-e (asyncua in-process); (c)
keine Docker-Pull-Latenz.

End-to-End-Pfad (C1-Probe-Run verifiziert):

1. `AsyncOutstation` in eigenem asyncio-Loop-Thread + `asyncio.Event`-
   Stop-Signal (Pattern aus Welle-4-Slice-032-Schaerfung).
2. Default-Werte fuer Analog-Inputs via `outstation.set_analog(idx,
   value)` vor dem `await server.start()`.
3. Test wartet via `_wait_for_port_open` + `ready.wait` bis Server
   bereit ist; Init-Errors werden im Thread gecaped und im Caller
   reraised.
4. `Dnp3DeviceProtocolPort.read(target)` macht
   `master.read_class(0)` und filtert nach Point-Index — End-to-
   End-Roundtrip durch Decision-D-c-Group/Variation-Set
   (Group 30/V5).
5. Teardown: `outstation.shutdown()` + `loop.stop()` +
   `thread.join`.

**Wire-Compat-Limitation** (ADR 0034 §1 + §3 A4): qualifier 0x01
(Per-Index-Range-Read via `read_analog_inputs(start, stop)`) wird
von `dnp3-outstation` v0.2.0 verworfen. Welle-5a benutzt deshalb
**ausschliesslich** den Class-0-Polling-Pfad — der Smoke deckt
das ab.

Cross-Cutting (Lastenheft Z. 1161-1163): Smoke ist Test-
Infrastruktur; **keine produktive Anlagensteuerung**.
"""

from __future__ import annotations

import asyncio
import contextlib
import socket
import threading
import time
from collections.abc import Iterator
from decimal import Decimal
from typing import Final

import pytest
from dnp3_outstation import AsyncOutstation

from grid_gym.adapters.driven.protocol_dnp3 import (
    Dnp3DeviceProtocolPort,
    Dnp3PointConfig,
    Dnp3ProtocolPortConfig,
)


_LOCALHOST: Final[str] = "127.0.0.1"
_MASTER_ADDR: Final[int] = 1
_OUTSTATION_ADDR: Final[int] = 10
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
    pytest.fail(f"DNP3-Outstation :{port} nicht erreichbar innerhalb {timeout_s}s")


# Pre-konfigurierte Analog-Input-Werte fuer den Smoke-Test.
# Welle-5a deckt Group 30/V5 (Float32) ab; Werte sind exakt-
# darstellbar in float32 fuer deterministischen Roundtrip.
_INITIAL_ANALOGS: Final[list[tuple[int, float]]] = [
    (0, 42.5),
    (1, -123.75),
    (2, 1000000.0),
]


class _InProcessDnp3Outstation:
    """Wrapper um den `AsyncOutstation`-Lifecycle.

    Pattern aus Welle-4-Slice-032-Schaerfung: eigene asyncio-Loop
    in Daemon-Thread + `asyncio.Event`-Stop-Signal + Init-
    Exception-Capture.
    """

    def __init__(self, port: int) -> None:
        self._port = port
        self._outstation: AsyncOutstation | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._init_error: BaseException | None = None
        self._stop_signal: asyncio.Event | None = None

    @property
    def port(self) -> int:
        return self._port

    def set_analog(self, idx: int, value: float) -> None:
        """Setzt einen Analog-Input-Wert. Funktioniert nur nach
        `start()`."""
        if self._outstation is None:
            msg = "InProcessDnp3Outstation: not started yet"
            raise RuntimeError(msg)
        self._outstation.set_analog(idx, value)

    def start(self) -> None:
        ready = threading.Event()

        async def _run_outstation() -> None:
            outstation = AsyncOutstation(
                host=_LOCALHOST,
                port=self._port,
                master_addr=_MASTER_ADDR,
                outstation_addr=_OUTSTATION_ADDR,
            )
            for idx, value in _INITIAL_ANALOGS:
                outstation.set_analog(idx, value)
            self._outstation = outstation
            await outstation.start()
            self._stop_signal = asyncio.Event()
            ready.set()
            await self._stop_signal.wait()

        def _thread_target() -> None:
            loop = asyncio.new_event_loop()
            self._loop = loop
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_run_outstation())
            except BaseException as exc:  # Setup-Capture
                self._init_error = exc
                ready.set()

        self._thread = threading.Thread(target=_thread_target, daemon=True)
        self._thread.start()
        if not ready.wait(timeout=_CONNECT_TIMEOUT_S):
            pytest.fail(f"DNP3-Outstation kam nicht innerhalb {_CONNECT_TIMEOUT_S}s hoch")
        if self._init_error is not None:
            raise self._init_error
        _wait_for_port_open(_LOCALHOST, self._port, _CONNECT_TIMEOUT_S)
        # Kurze zusaetzliche Settle-Phase: TCP-Listen ist nach
        # `_wait_for_port_open` offen, aber `dnp3-outstation`-internes
        # Setup (Datalink-Layer-Init) braucht noch ein paar
        # Iterationen im asyncio-Loop, bevor der erste Master-Poll
        # sauber durchgeht. C1-Probe-Run hatte ein
        # `time.sleep(0.3)`-Wait an dieser Stelle.
        time.sleep(0.3)

    def stop(self) -> None:
        if self._outstation is not None and self._loop is not None:
            future = asyncio.run_coroutine_threadsafe(self._outstation.shutdown(), self._loop)
            with contextlib.suppress(Exception):
                future.result(timeout=_SERVER_STOP_TIMEOUT_S)
            if self._stop_signal is not None:
                self._loop.call_soon_threadsafe(self._stop_signal.set)
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=_SERVER_STOP_TIMEOUT_S)


@pytest.fixture
def _dnp3_outstation() -> Iterator[_InProcessDnp3Outstation]:
    port = _find_free_port()
    outstation = _InProcessDnp3Outstation(port)
    outstation.start()
    try:
        yield outstation
    finally:
        outstation.stop()


def _build_config(outstation: _InProcessDnp3Outstation) -> Dnp3ProtocolPortConfig:
    """Profil mit einem Read-Target pro vor-konfiguriertem
    Analog-Input."""
    points: dict[str, Dnp3PointConfig] = {}
    for idx, _value in _INITIAL_ANALOGS:
        points[f"analog_{idx}"] = Dnp3PointConfig(group=30, variation=5, index=idx, access="read")
    return Dnp3ProtocolPortConfig(
        host=_LOCALHOST,
        port=outstation.port,
        master_address=_MASTER_ADDR,
        outstation_address=_OUTSTATION_ADDR,
        points=points,
        response_timeout_s=5.0,
    )


@pytest.mark.parametrize(
    ("idx", "expected_value"),
    _INITIAL_ANALOGS,
)
def test_dnp3_adapter_class0_read_roundtrip(
    _dnp3_outstation: _InProcessDnp3Outstation,
    idx: int,
    expected_value: float,
) -> None:
    """End-to-End: Master connect + read_class(0) + Filter-by-Index
    + Decode liefert den vor-konfigurierten Analog-Input-Wert."""
    config = _build_config(_dnp3_outstation)
    port = Dnp3DeviceProtocolPort(config)
    port.start()
    try:
        target = f"analog_{idx}"
        # Erster Read koennte device_restart=True liefern, aber
        # dnp3-outstation self-clears das Flag — das Resultat hat
        # trotzdem alle Analog-Inputs (C1-Probe verifiziert).
        telemetry = port.read(target)
        assert telemetry is not None
        assert telemetry.device_id == target
        assert telemetry.source == f"protocol_dnp3.{target}"
        assert telemetry.metric == "g30v5"
        assert isinstance(telemetry.value, Decimal)
        assert float(telemetry.value) == pytest.approx(expected_value)
    finally:
        port.stop()


def test_dnp3_adapter_read_after_value_update(
    _dnp3_outstation: _InProcessDnp3Outstation,
) -> None:
    """Wert-Update im Outstation wird vom Master im naechsten
    `read_class(0)`-Roundtrip gesehen."""
    config = _build_config(_dnp3_outstation)
    port = Dnp3DeviceProtocolPort(config)
    port.start()
    try:
        # First read — initial value 42.5.
        telemetry = port.read("analog_0")
        assert telemetry is not None
        assert float(telemetry.value) == pytest.approx(42.5)

        # Update outstation value.
        _dnp3_outstation.set_analog(0, 99.25)

        # Second read should see the new value.
        telemetry = port.read("analog_0")
        assert telemetry is not None
        assert float(telemetry.value) == pytest.approx(99.25)
    finally:
        port.stop()
