"""Tests fuer `ModbusDeviceServerAdapter` (Field-Server Pull-Seite, ADR 0075
§2.1/§2.4).

Lifecycle/Idempotenz/Fehler-Wrapping ueber einen **Fake-Runner** (kein echter
Socket) + der synchrone Bind-in-use-Hard-Error (`_preflight_bind`, echter
Socket). Die echte pymodbus-Bedienung verifiziert der Read-E2E (Slice 074 C2).
"""

from __future__ import annotations

import asyncio
import socket
from decimal import Decimal

import pytest

from grid_gym.adapters.driving._field_current_value import CurrentValueProjection
from grid_gym.adapters.driving._inbound_command_buffer import InboundCommandBuffer
from grid_gym.adapters.driving.device_server_modbus._adapter import (
    ModbusDeviceServerAdapter,
    _default_server_runner,
    _make_write_action,
    _preflight_bind,
)
from grid_gym.adapters.driving.device_server_modbus._config import (
    ModbusServerConfig,
    RegisterMapping,
    WritableRegisterMapping,
)
from grid_gym.adapters.driving.device_server_modbus._errors import (
    ModbusServerBindError,
    ModbusServerStopError,
    ModbusServerWiringError,
)
from grid_gym.adapters.driving.device_server_modbus._register_map import RegisterMap, encode_float32
from grid_gym.adapters.driving.device_server_modbus._write_map import InboundWriteDecoder
from grid_gym.hexagon.core.domain.device import DeviceTickContext


class _FakeRunningServer:
    def __init__(self, *, stop_error: Exception | None = None) -> None:
        self.stopped: int = 0
        self._stop_error = stop_error

    def stop(self) -> None:
        self.stopped += 1
        if self._stop_error is not None:
            raise self._stop_error


class _RecordingRunner:
    """Fake-Runner: zeichnet Aufrufe auf, liefert einen Fake-Server."""

    def __init__(
        self,
        *,
        start_error: Exception | None = None,
        stop_error: Exception | None = None,
    ) -> None:
        self.calls: list[tuple[ModbusServerConfig, RegisterMap, InboundCommandBuffer | None]] = []
        self._start_error = start_error
        self._stop_error = stop_error
        self.server: _FakeRunningServer | None = None

    def __call__(
        self,
        config: ModbusServerConfig,
        register_map: RegisterMap,
        inbound_buffer: InboundCommandBuffer | None = None,
    ) -> _FakeRunningServer:
        self.calls.append((config, register_map, inbound_buffer))
        if self._start_error is not None:
            raise self._start_error
        self.server = _FakeRunningServer(stop_error=self._stop_error)
        return self.server


def _config() -> ModbusServerConfig:
    return ModbusServerConfig(
        bind_host="127.0.0.1",
        bind_port=5020,
        register_map=(RegisterMapping("meter-1", "voltage_v", 0),),
    )


def _adapter(runner: _RecordingRunner) -> ModbusDeviceServerAdapter:
    return ModbusDeviceServerAdapter(_config(), CurrentValueProjection(), server_runner=runner)


# --- Lifecycle / Idempotenz -------------------------------------------------


def test_start_invokes_runner_with_register_map() -> None:
    runner = _RecordingRunner()
    _adapter(runner).start()
    assert len(runner.calls) == 1
    _config_arg, register_map, inbound_buffer = runner.calls[0]
    assert isinstance(register_map, RegisterMap)
    assert inbound_buffer is None  # ohne injizierten Puffer → reines Read-Serving


def test_start_threads_inbound_buffer_to_runner() -> None:
    # ADR 0076 §2.1: ein injizierter Puffer erreicht den Runner (Write-Callback).
    runner = _RecordingRunner()
    buffer = InboundCommandBuffer()
    config = ModbusServerConfig(
        bind_host="127.0.0.1",
        bind_port=5020,
        register_map=(RegisterMapping("meter-1", "voltage_v", 0),),
        write_map=(WritableRegisterMapping(2, "battery-1", "set_power_kw"),),
    )
    ModbusDeviceServerAdapter(
        config, CurrentValueProjection(), server_runner=runner, inbound_buffer=buffer
    ).start()
    assert runner.calls[0][2] is buffer


def test_double_start_is_noop() -> None:
    runner = _RecordingRunner()
    adapter = _adapter(runner)
    adapter.start()
    adapter.start()
    assert len(runner.calls) == 1  # zweiter start() ist No-op


def test_stop_shuts_down_running_server() -> None:
    runner = _RecordingRunner()
    adapter = _adapter(runner)
    adapter.start()
    adapter.stop()
    assert runner.server is not None
    assert runner.server.stopped == 1


def test_stop_without_start_is_noop() -> None:
    runner = _RecordingRunner()
    _adapter(runner).stop()  # kein Server → kein Fehler
    assert runner.server is None


def test_double_stop_is_noop() -> None:
    runner = _RecordingRunner()
    adapter = _adapter(runner)
    adapter.start()
    adapter.stop()
    adapter.stop()  # State ist zurueckgesetzt → No-op
    assert runner.server is not None
    assert runner.server.stopped == 1


def test_can_restart_after_stop() -> None:
    runner = _RecordingRunner()
    adapter = _adapter(runner)
    adapter.start()
    adapter.stop()
    adapter.start()
    assert len(runner.calls) == 2  # Rebind nach Stop erlaubt


# --- Fehler-Wrapping --------------------------------------------------------


def test_runner_bind_error_propagates_as_start_error() -> None:
    # Ein Runner, der bereits typisiert wirft (ModbusServerBindError), propagiert 1:1.
    runner = _RecordingRunner(
        start_error=ModbusServerBindError("127.0.0.1", 5020, OSError("in use"))
    )
    with pytest.raises(ModbusServerBindError):
        _adapter(runner).start()


def test_runner_bare_oserror_is_wrapped_as_bind_error() -> None:
    # Sicherheitsnetz: nackter OSError → typisierter ModbusServerBindError.
    runner = _RecordingRunner(start_error=OSError("address already in use"))
    with pytest.raises(ModbusServerBindError):
        _adapter(runner).start()


def test_stop_oserror_is_wrapped_as_stop_error() -> None:
    runner = _RecordingRunner(stop_error=OSError("close failed"))
    adapter = _adapter(runner)
    adapter.start()
    with pytest.raises(ModbusServerStopError):
        adapter.stop()
    # State wird auch im Fehlerfall zurueckgesetzt (Best-Effort-Cleanup).
    assert adapter._running is None


# --- Preflight-Bind (echter Socket) ----------------------------------------


def test_preflight_bind_free_port_succeeds() -> None:
    # Ephemeren Port ergattern, wieder freigeben, dann pruefen: bindbar → kein Fehler.
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    _preflight_bind("127.0.0.1", port)  # kein Raise


def test_preflight_bind_occupied_port_raises() -> None:
    occupant = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    occupant.bind(("127.0.0.1", 0))
    occupant.listen(1)
    port = occupant.getsockname()[1]
    try:
        with pytest.raises(ModbusServerBindError):
            _preflight_bind("127.0.0.1", port)
    finally:
        occupant.close()


# --- Default-Runner: synchroner Bind-in-use-Hard-Error ----------------------


def test_default_runner_bind_in_use_is_hard_error() -> None:
    # Belegter Port → schon der Preflight-Bind wirft (vor dem C2-Deferral).
    occupant = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    occupant.bind(("127.0.0.1", 0))
    occupant.listen(1)
    port = occupant.getsockname()[1]
    config = ModbusServerConfig(
        bind_host="127.0.0.1",
        bind_port=port,
        register_map=(RegisterMapping("meter-1", "voltage_v", 0),),
    )
    register_map = RegisterMap(config, CurrentValueProjection())
    try:
        with pytest.raises(ModbusServerBindError):
            _default_server_runner(config, register_map)
    finally:
        occupant.close()


# --- Inbound-Write-SimAction-Diskriminator (ADR 0076; Review-Fund Slice 075) ---


def _write_config() -> ModbusServerConfig:
    return ModbusServerConfig(
        bind_host="127.0.0.1",
        bind_port=5020,
        register_map=(RegisterMapping("meter-1", "voltage_v", 0),),
        write_map=(WritableRegisterMapping(10, "battery-1", "set_power_kw"),),
    )


def _run_action(
    buffer: InboundCommandBuffer,
    function_code: int,
    address: int,
    set_values: list[int] | None,
) -> None:
    action = _make_write_action(InboundWriteDecoder(_write_config()), buffer)
    count = len(set_values) if set_values is not None else 1
    asyncio.run(action(function_code, 0, address, count, [], set_values))


def _drained_types(buffer: InboundCommandBuffer) -> list[str]:
    ctx = DeviceTickContext(tick=0, simulation_time=1000, tick_ms=1000)
    return [command.type for command in buffer.drain_due(ctx)]


@pytest.mark.parametrize("function_code", [6, 16, 23])
def test_write_action_enqueues_for_holding_write_codes(function_code: int) -> None:
    # FC06/FC16/FC23 auf ein volles float32-Fenster -> Command. FC23 war der
    # Review-Fund Slice 075 (vorher stumm gedroppt).
    buffer = InboundCommandBuffer()
    _run_action(buffer, function_code, 10, list(encode_float32(Decimal("42.5"))))
    assert _drained_types(buffer) == ["set_power_kw"]


def test_write_action_ignores_refresh_fc03_push() -> None:
    # Der interne Refresh nutzt FC03 (Read-Code als Block-Selektor) -> nie enqueue,
    # auch wenn der geschriebene Bereich ein Sollwert-Fenster ueberdeckt.
    buffer = InboundCommandBuffer()
    _run_action(buffer, 3, 0, [0] * 10 + [1, 2])
    assert _drained_types(buffer) == []


def test_write_action_ignores_read() -> None:
    # set_values is None == Read -> nie enqueue.
    buffer = InboundCommandBuffer()
    _run_action(buffer, 3, 0, None)
    assert _drained_types(buffer) == []


def test_write_action_skips_partial_single_register_write() -> None:
    # FC06 kann nur ein halbes float32-Fenster schreiben -> uebersprungen.
    buffer = InboundCommandBuffer()
    _run_action(buffer, 6, 10, [encode_float32(Decimal("42.5"))[0]])
    assert _drained_types(buffer) == []


def test_write_map_without_inbound_buffer_is_rejected() -> None:
    # Beschreibbare Fenster ohne Puffer -> Fehlkonfiguration (Master-Writes wuerden
    # still verworfen). Fail-fast bei Konstruktion (Review-Fund Slice 075).
    with pytest.raises(ModbusServerWiringError):
        ModbusDeviceServerAdapter(_write_config(), CurrentValueProjection())


def test_write_map_with_inbound_buffer_constructs() -> None:
    # write_map + Puffer -> valide Verdrahtung, kein Fehler (kein start()/Bind).
    ModbusDeviceServerAdapter(
        _write_config(), CurrentValueProjection(), inbound_buffer=InboundCommandBuffer()
    )
