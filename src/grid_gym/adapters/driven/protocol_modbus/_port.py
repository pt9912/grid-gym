"""`ModbusDeviceProtocolPort` — Modbus-TCP-Adapter als
`DeviceProtocolPort`-Implementer (M4 Welle 3, ADR 0032).

Sync-Surface (ADR 0030 §2.1) direkt gegen pymodbus-`ModbusTcpClient`
(sync-by-design); **kein** Adapter-interner Thread+Queue-Marshal
noetig (Decision M-c, ADR 0032 §2.3 — signifikant einfacher als
Welle-2-MQTT).

Simulations-/Testadapter (Lastenheft Z. 1161-1163); **keine
produktive Anlagensteuerung**.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Final

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusException

from grid_gym.adapters.driven.protocol_modbus._codec import (
    ModbusCodecPayloadTypeError,
    decode_registers_to_value,
    encode_value_to_registers,
)
from grid_gym.adapters.driven.protocol_modbus._config import (
    ModbusProtocolPortConfig,
    ModbusRegisterConfig,
    datatype_register_count,
    resolve_function_code,
    resolve_unit_id,
)
from grid_gym.adapters.driven.protocol_modbus._errors import (
    ModbusPortAccessMismatchError,
    ModbusPortConnectError,
    ModbusPortDisconnectError,
    ModbusPortMissingCommandPayloadError,
    ModbusPortNotStartedError,
    ModbusPortReadFailedError,
    ModbusPortWriteFailedError,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPortUnknownTargetError,
)

if TYPE_CHECKING:
    pass


# Type-Alias fuer den Client-Factory-Hook (Tests reichen einen Mock
# durch).
ClientFactory = Callable[[ModbusProtocolPortConfig], ModbusTcpClient]

# Modbus-Spec Function-Code-Konstanten (ADR 0032 §2.4).
_FC_READ_HOLDING_REGISTERS: Final[int] = 3
_FC_READ_INPUT_REGISTERS: Final[int] = 4
_FC_WRITE_SINGLE_REGISTER: Final[int] = 6


@dataclass(frozen=True, slots=True)
class _ModbusRequest:
    """Konsolidierter Parameter-Block fuer pymodbus-Calls (loest
    PLR0913 in `_do_read`/`_do_write` ohne Args-Inflation)."""

    function_code: int
    address: int
    unit_id: int
    target: str


def _default_client_factory(
    config: ModbusProtocolPortConfig,
) -> ModbusTcpClient:
    """Default-Client-Factory: pymodbus 3.x `ModbusTcpClient` mit
    den Config-Parametern.

    Trennt das Konstruktor-Detail vom Adapter-Pfad, damit Tests den
    Client mocken koennen, ohne die Welle-3-Default-Wahl zu
    duplizieren.
    """
    return ModbusTcpClient(
        host=config.host,
        port=config.port,
        timeout=config.timeout_s,
    )


class ModbusDeviceProtocolPort:
    """Modbus-TCP-Adapter (Simulations-/Testadapter; keine produktive
    Anlagensteuerung).

    Implementiert `DeviceProtocolPort` (ADR 0030 §2.1). pymodbus-Sync-
    Client wird **direkt** vom TickLoop-Thread aufgerufen (Decision
    M-c, ADR 0032 §2.3) — kein Background-Polling, kein Thread-
    Marshal, kein Queue-State.

    Lifecycle ist idempotent: Doppel-`start()` ist No-op nach erstem
    erfolgreichem Connect; `stop()` nach erfolglosem `start()` ist
    No-op.
    """

    def __init__(
        self,
        config: ModbusProtocolPortConfig,
        *,
        client_factory: ClientFactory | None = None,
    ) -> None:
        self._config: ModbusProtocolPortConfig = config
        self._client_factory: ClientFactory = client_factory or _default_client_factory
        self._client: ModbusTcpClient | None = None
        self._started: bool = False

    # ------------------------------------------------------------------
    # `DeviceProtocolPort`-Surface (ADR 0030 §2.1)
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Connect zum Modbus-Server. Idempotent."""
        if self._started:
            return
        client = self._client_factory(self._config)
        try:
            connected = client.connect()  # type: ignore[no-untyped-call]
        except (OSError, ConnectionException) as exc:
            raise ModbusPortConnectError(self._config.host, self._config.port, str(exc)) from exc
        if not connected:
            raise ModbusPortConnectError(
                self._config.host,
                self._config.port,
                "ModbusTcpClient.connect() returned False",
            )
        self._client = client
        self._started = True

    def stop(self) -> None:
        """Disconnect. Idempotent — Doppel-Stop ist No-op."""
        if not self._started or self._client is None:
            return
        client = self._client
        self._client = None
        self._started = False
        try:
            client.close()  # type: ignore[no-untyped-call]
        except OSError as exc:
            raise ModbusPortDisconnectError(exc) from exc

    def read(self, target: str) -> TelemetryPoint | None:
        """Liest Register vom Server, dekodiert + verpackt in
        `TelemetryPoint` (Decision M-c direkt-sync).

        Wirft `DeviceProtocolPortUnknownTargetError`, wenn das Target
        nicht im Profil ist. Wirft `ModbusPortAccessMismatchError`,
        wenn das Target als `access="write"` konfiguriert ist.
        """
        reg_cfg = self._resolve_register_config(target)
        if reg_cfg.access != "read":
            raise ModbusPortAccessMismatchError(target, reg_cfg.access, "read")
        client = self._require_client(target, "read")
        request = _ModbusRequest(
            function_code=resolve_function_code(reg_cfg),
            address=reg_cfg.address,
            unit_id=resolve_unit_id(reg_cfg, self._config.unit_id),
            target=target,
        )
        register_count = datatype_register_count(reg_cfg.datatype)
        registers = self._do_read(client, request, register_count)
        value = decode_registers_to_value(
            registers, reg_cfg.datatype, reg_cfg.byte_order, reg_cfg.word_swap
        )
        return _build_telemetry_point(target, reg_cfg, value)

    def write(self, target: str, command: Command) -> None:
        """Encodiert `command.payload["value"]` zu Register-Worten und
        sendet sie an den Server (Decision M-c direkt-sync).

        Wirft `DeviceProtocolPortUnknownTargetError` bei unbekanntem
        Target, `ModbusPortAccessMismatchError` bei
        `access="read"`-Targets, `ModbusPortMissingCommandPayloadError`
        wenn `command.payload` keinen `value`-Key hat.
        """
        reg_cfg = self._resolve_register_config(target)
        if reg_cfg.access != "write":
            raise ModbusPortAccessMismatchError(target, reg_cfg.access, "write")
        client = self._require_client(target, "write")
        value = command.payload.get("value")
        if value is None:
            raise ModbusPortMissingCommandPayloadError(target)
        registers = encode_value_to_registers(
            _coerce_value(value),
            reg_cfg.datatype,
            reg_cfg.byte_order,
            reg_cfg.word_swap,
        )
        request = _ModbusRequest(
            function_code=resolve_function_code(reg_cfg),
            address=reg_cfg.address,
            unit_id=resolve_unit_id(reg_cfg, self._config.unit_id),
            target=target,
        )
        self._do_write(client, request, registers)

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _resolve_register_config(self, target: str) -> ModbusRegisterConfig:
        if target not in self._config.registers:
            raise DeviceProtocolPortUnknownTargetError(
                target,
                available_targets=tuple(sorted(self._config.registers.keys())),
            )
        return self._config.registers[target]

    def _require_client(self, target: str, operation: str) -> ModbusTcpClient:
        if self._client is None:
            raise ModbusPortNotStartedError(target, operation)
        return self._client

    def _do_read(
        self,
        client: ModbusTcpClient,
        request: _ModbusRequest,
        register_count: int,
    ) -> tuple[int, ...]:
        # pymodbus 3.13 hat `slave=` zu `device_id=` umbenannt
        # (frueher: pymodbus 2.x `unit=` -> 3.x `slave=` -> 3.13+ `device_id=`).
        # Pin `>=3.6,<4.0` in pyproject.toml haelt die 3.x-Linie; konkrete
        # `device_id=`-Wahl folgt der aktuellen Library-API.
        try:
            if request.function_code == _FC_READ_HOLDING_REGISTERS:
                response = client.read_holding_registers(
                    address=request.address,
                    count=register_count,
                    device_id=request.unit_id,
                )
            else:  # _FC_READ_INPUT_REGISTERS
                response = client.read_input_registers(
                    address=request.address,
                    count=register_count,
                    device_id=request.unit_id,
                )
        except (ModbusException, OSError) as exc:
            raise ModbusPortReadFailedError(request.target, request.address, str(exc)) from exc
        if response.isError():
            raise ModbusPortReadFailedError(request.target, request.address, repr(response))
        return tuple(response.registers)

    def _do_write(
        self,
        client: ModbusTcpClient,
        request: _ModbusRequest,
        registers: tuple[int, ...],
    ) -> None:
        # `device_id=`-Kwarg analog `_do_read` (pymodbus 3.13-Konvention).
        try:
            if request.function_code == _FC_WRITE_SINGLE_REGISTER:
                response = client.write_register(
                    address=request.address,
                    value=registers[0],
                    device_id=request.unit_id,
                )
            else:  # _FC_WRITE_MULTIPLE_REGISTERS (16)
                response = client.write_registers(
                    address=request.address,
                    values=list(registers),
                    device_id=request.unit_id,
                )
        except (ModbusException, OSError) as exc:
            raise ModbusPortWriteFailedError(request.target, request.address, str(exc)) from exc
        if response.isError():
            raise ModbusPortWriteFailedError(request.target, request.address, repr(response))


def _coerce_value(raw: object) -> int | Decimal | float:
    """Akzeptiert `Command.payload['value']` als int/Decimal/float;
    sonst -> `ModbusCodecPayloadTypeError` zum Adapter-Rand."""
    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, int | Decimal | float):
        return raw
    raise ModbusCodecPayloadTypeError(type(raw).__name__)


def _build_telemetry_point(
    target: str, reg_cfg: ModbusRegisterConfig, value: Decimal
) -> TelemetryPoint:
    """Verpackt einen dekodierten Register-Wert in einen
    `TelemetryPoint` mit Welle-3-Defaults.

    `run_id`/`tick`/`simulation_time`/`sequence` sind Adapter-frei
    und werden vom Caller (TickLoop oder Test) gesetzt — der Modbus-
    Adapter weiss nichts ueber die Simulationszeit. Welle 6 (Cross-
    Adapter-Hardening) wird vermutlich einen `ClockPort`-Bezug
    einfuehren, falls Adapter Wall-Clock-Telemetry brauchen.
    """
    return TelemetryPoint(
        run_id="",  # Caller-Verantwortung
        tick=0,
        simulation_time=0,
        device_id=target,
        metric=reg_cfg.datatype.value,
        value=value,
        unit="",  # Welle 6 Cross-Adapter-Hardening
        quality=Quality.VALID,
        source=f"protocol_modbus.{target}",
        sequence=0,
    )
