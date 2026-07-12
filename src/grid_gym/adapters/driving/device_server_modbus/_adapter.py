"""`ModbusDeviceServerAdapter` — `DeviceServerPort`-Implementer (ADR 0075 §2.1).

Modbus-TCP-**Server/Slave** fuer die **Pull-Seite** der Field-Server-Surface:
ein externes EMS (System-under-Test, z. B. `bess-ems`) pollt als Modbus-**Master**
grid-gyms simulierte Geraetewerte als Holding-Register (`float32`) + Quality als
Discrete-Input. **Read-Serving only** (Inbound-Write→`Command` ausgegliedert,
ADR 0075 §7). Die Register kommen aus der geteilten Current-Value-Projektion
ueber die `RegisterMap` (on-demand-Berechnung + Encode-Oracle).

**Server-Lifecycle (ADR 0075 §2.4)**: `start()` = bind + serve; **Bind-in-use
ist ein harter Fehler vor dem ersten Tick** (`_preflight_bind` macht ihn
synchron — pymodbus bindet erst tief in `serve_forever()`/`listen()`). `stop()`
= Server graceful herunterfahren; idempotent nach erfolglosem/nicht-erfolgtem
`start()`.

**Runner-Injektion**: die pymodbus-Server-Verdrahtung steckt hinter
`server_runner` (Default `_default_server_runner`). Unit-Tests reichen einen
Fake-Runner → Adapter-Lifecycle/Fehler-Wrapping/Idempotenz ohne echten Socket
pruefbar.

**pymodbus-3.13-Naht (C2)**: pymodbus 3.13 hat den Datastore auf das
`SimData`/`SimDevice`-Modell umgebaut (der alte `ModbusServerContext`/
`ModbusDeviceContext`-Shim serviert nur **statisch**: `async_setValues` liefert
fuer einen `ModbusDeviceContext` `DEVICE_BUSY`). Der Server laeuft darum ueber
ein `SimDevice` (`SimCore`): ein **Refresh-Task** im Server-Loop pusht die
on-demand aus der Projektion gerechneten `RegisterMap`-Werte via
`server.async_setValues` in den Datastore (Holding = `float32`/2 Register,
Discrete-Input = Quality-`VALID`-Flag). Ein initialer Push **vor** dem
Freischalten von `start()` macht den ersten Poll deterministisch; danach haelt
der Refresh-Task die Register aktuell (Staleness ≤ Refresh-Intervall, nie eine
Luecke — „letzter gueltiger Wert", ADR 0075 §2.2). Server-State ist volatil
(kein Snapshot-Slot, §2.5). Read-E2E: ein echter pymodbus-Master pollt gegen das
Encode-Oracle (`test_read_e2e.py`).

**Simulations-/Testadapter** ([`GG-SAFE-007`], [`GG-NONGOAL-001`]): keine
produktive Anlagensteuerung; Modbus-TCP hat kein Auth/TLS → Nur-Sim-Netz.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import socket
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Final, Protocol, runtime_checkable

from grid_gym.adapters.driving._field_current_value import CurrentValueProjection
from grid_gym.adapters.driving.device_server_modbus._config import ModbusServerConfig
from grid_gym.adapters.driving.device_server_modbus._errors import (
    ModbusServerBindError,
    ModbusServerStopError,
)
from grid_gym.adapters.driving.device_server_modbus._register_map import RegisterMap

if TYPE_CHECKING:
    from pymodbus.server import ModbusTcpServer
    from pymodbus.simulator import SimDevice

_LOGGER: logging.Logger = logging.getLogger(__name__)

# Modbus-Read-Funktions-Codes (der server-interne `async_setValues` waehlt
# darueber den Ziel-Block; FC03 = Holding-Register, FC02 = Discrete-Inputs).
_FC_READ_HOLDING_REGISTERS: Final[int] = 3
_FC_READ_DISCRETE_INPUTS: Final[int] = 2
_FLOAT32_REGISTERS: Final[int] = 2

_REFRESH_INTERVAL_S: Final[float] = 0.05
_READY_TIMEOUT_S: Final[float] = 5.0
_SHUTDOWN_TIMEOUT_S: Final[float] = 5.0


@runtime_checkable
class RunningServer(Protocol):
    """Handle auf einen laufenden Server; `stop()` faehrt ihn herunter."""

    def stop(self) -> None: ...


# Runner-Hook (Default fuehrt den Bind-Check + startet den pymodbus-Server;
# Tests reichen einen Fake durch, damit kein echter Socket/Server noetig ist).
ServerRunner = Callable[[ModbusServerConfig, RegisterMap], RunningServer]


def _preflight_bind(bind_host: str, bind_port: int) -> None:
    """Deterministischer Bind-in-use-Check **vor** dem pymodbus-Start
    (ADR 0075 §2.4).

    pymodbus bindet erst tief in `serve_forever()`/`listen()` (im Loop-Thread) —
    ein Port-belegt-Fehler taeuchte dort asynchron auf, nicht synchron aus
    `start()`. Dieser Vorab-Bind (sofort wieder geschlossen) macht „Port belegt"
    zu einem **harten, synchronen** Fehler vor dem ersten Tick. Der Rest-Race
    (TOCTOU zwischen Close und pymodbus-Rebind) ist fuer den Nur-Sim-Netz-Betrieb
    akzeptabel."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind((bind_host, bind_port))
    except OSError as exc:
        raise ModbusServerBindError(bind_host, bind_port, exc) from exc
    finally:
        probe.close()


def _holding_register_count(config: ModbusServerConfig) -> int:
    """Anzahl Holding-Register, die der Datastore abdecken muss: bis zur
    hoechsten gemappten Adresse + `float32`-Breite (2 Register)."""
    return max(mapping.address for mapping in config.register_map) + _FLOAT32_REGISTERS


def _build_device(config: ModbusServerConfig) -> SimDevice:
    """Baut das pymodbus-3.13-`SimDevice` (non-shared Bloecke): Holding-Register
    (`REGISTERS`, ab Adresse 0) + Discrete-Inputs (`BITS`, ein Bit je Mapping in
    `register_map`-Reihenfolge). Coil-/Input-Register-Bloecke sind Platzhalter
    (grid-gym serviert sie nicht, aber leere Bloecke sind unzulaessig). Die
    tatsaechlichen Werte pusht der Refresh-Task via `async_setValues`."""
    from pymodbus.simulator import DataType, SimData, SimDevice

    coils = SimData(address=0, count=1, values=False, datatype=DataType.BITS)
    discrete = SimData(
        address=0,
        count=len(config.register_map),
        values=False,
        datatype=DataType.BITS,
    )
    holding = SimData(
        address=0,
        count=_holding_register_count(config),
        values=0,
        datatype=DataType.REGISTERS,
    )
    inputs = SimData(address=0, count=1, values=0, datatype=DataType.REGISTERS)
    # SimDevice-Tuple-Reihenfolge: (coils, discrete_inputs, holding, input_regs).
    return SimDevice(config.unit_id, simdata=([coils], [discrete], [holding], [inputs]))


class _PymodbusRunningServer:
    """Der echte pymodbus-3.13-Server in einem adapter-internen Loop-Thread.

    Serviert ein `SimDevice`; ein Refresh-Task pusht die aus der Projektion
    gerechneten `RegisterMap`-Werte via `server.async_setValues`. Der initiale
    Push laeuft vor `start()`-Freischaltung (deterministischer erster Poll)."""

    def __init__(self, config: ModbusServerConfig, register_map: RegisterMap) -> None:
        self._config: ModbusServerConfig = config
        self._register_map: RegisterMap = register_map
        self._holding_count: int = _holding_register_count(config)
        self._discrete_count: int = len(config.register_map)
        self._loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        self._server: ModbusTcpServer | None = None
        self._ready: threading.Event = threading.Event()
        # Startup-Fehler aus dem Server-Thread; als Liste, damit die
        # cross-thread-Zuweisung nicht von mypys Flow-Narrowing als
        # unreachable eingestuft wird.
        self._startup_error: list[Exception] = []
        self._thread: threading.Thread = threading.Thread(
            target=self._run,
            name=f"modbus-server-{config.bind_port}",
            daemon=True,
        )
        self._thread.start()
        if not self._ready.wait(timeout=_READY_TIMEOUT_S):
            # Nie bereit → laeuft evtl. noch: hart stoppen und melden.
            self.stop()
            raise ModbusServerBindError(
                config.bind_host,
                config.bind_port,
                TimeoutError(f"Server nicht binnen {_READY_TIMEOUT_S}s bereit"),
            )
        if self._startup_error:
            # _serve() ist mit Fehler zurueck → Thread laeuft aus, nur joinen.
            self._thread.join(timeout=_SHUTDOWN_TIMEOUT_S)
            raise ModbusServerBindError(config.bind_host, config.bind_port, self._startup_error[0])

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        finally:
            self._loop.close()

    async def _serve(self) -> None:
        from pymodbus.server import ModbusTcpServer

        server = ModbusTcpServer(
            _build_device(self._config),
            address=(self._config.bind_host, self._config.bind_port),
        )
        self._server = server
        try:
            await server.serve_forever(background=True)  # bind + listen (non-blocking)
            await self._push(server)  # initialer Push → erster Poll deterministisch
        except (OSError, RuntimeError) as exc:
            # Bind-/Listen-Race (pymodbus wirft RuntimeError „Could not start
            # listen"; OSError bei Port-Problemen) → start() meldet hart. Alles
            # Uebrige faengt das _ready-Timeout in __init__.
            self._startup_error.append(exc)
            self._ready.set()
            return
        self._ready.set()
        refresh = asyncio.create_task(self._refresh_loop(server))
        try:
            await server.serving  # blockiert bis shutdown()
        finally:
            refresh.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await refresh

    async def _refresh_loop(self, server: ModbusTcpServer) -> None:
        while True:
            await asyncio.sleep(_REFRESH_INTERVAL_S)
            try:
                await self._push(server)
            except (OSError, RuntimeError):
                # Refresh ist best-effort: ein Transport-/Runtime-Fehler darf den
                # Server nicht toeten; der naechste Tick zieht nach. (async_setValues
                # signalisiert Datastore-Probleme ueber ExcCodes, nicht per Raise.)
                _LOGGER.exception("Modbus-Server: Projektion-Refresh fehlgeschlagen")

    async def _push(self, server: ModbusTcpServer) -> None:
        """Schreibt die aktuelle Projektion (on-demand gerechnet) in den
        Datastore: Holding-Register (`float32`) + Discrete-Inputs (Quality)."""
        holding = self._register_map.holding_registers(0, self._holding_count)
        await server.async_setValues(self._config.unit_id, _FC_READ_HOLDING_REGISTERS, 0, holding)
        discrete = self._register_map.discrete_inputs(0, self._discrete_count)
        await server.async_setValues(self._config.unit_id, _FC_READ_DISCRETE_INPUTS, 0, discrete)

    def stop(self) -> None:
        server = self._server
        if server is not None and not self._loop.is_closed():
            try:
                shutdown = asyncio.run_coroutine_threadsafe(
                    server.shutdown(),  # type: ignore[no-untyped-call]
                    self._loop,
                )
                shutdown.result(timeout=_SHUTDOWN_TIMEOUT_S)
            except (TimeoutError, RuntimeError):
                with contextlib.suppress(RuntimeError):
                    self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=_SHUTDOWN_TIMEOUT_S)


def _default_server_runner(config: ModbusServerConfig, register_map: RegisterMap) -> RunningServer:
    """Default-Runner: synchroner Bind-in-use-Check, dann der reale
    pymodbus-Server im Loop-Thread."""
    _preflight_bind(config.bind_host, config.bind_port)
    return _PymodbusRunningServer(config, register_map)


class ModbusDeviceServerAdapter:
    """Modbus-TCP-Server-Adapter (Simulations-/Testadapter; keine produktive
    Anlagensteuerung).

    Implementiert `DeviceServerPort` (ADR 0075 §2.1). Lifecycle idempotent:
    Doppel-`start()` ist No-op nach erstem erfolgreichem Bind; `stop()` nach
    erfolglosem/nicht-erfolgtem `start()` ist No-op.
    """

    def __init__(
        self,
        config: ModbusServerConfig,
        projection: CurrentValueProjection,
        *,
        server_runner: ServerRunner | None = None,
    ) -> None:
        self._config: ModbusServerConfig = config
        self._projection: CurrentValueProjection = projection
        self._server_runner: ServerRunner = server_runner or _default_server_runner
        self._running: RunningServer | None = None

    def start(self) -> None:
        """Bind + serve. Idempotent. Bind-in-use → `ModbusServerBindError`
        (harter Fehler; der Lauf startet nicht)."""
        if self._running is not None:
            return
        register_map = RegisterMap(self._config, self._projection)
        try:
            self._running = self._server_runner(self._config, register_map)
        except OSError as exc:
            # Sicherheitsnetz: ein Runner, der einen nackten OSError statt eines
            # DeviceServerPortStartError wirft, wird typisiert nachgezogen.
            raise ModbusServerBindError(
                self._config.bind_host, self._config.bind_port, exc
            ) from exc

    def stop(self) -> None:
        """Server graceful herunterfahren. Idempotent — Doppel-Stop /
        Stop-ohne-Start ist No-op. Harte Close-Fehler → `ModbusServerStopError`;
        der interne Zustand wird auch im Fehlerfall zurueckgesetzt (Best-Effort-
        Cleanup, Muster `MqttFieldPublishAdapter`)."""
        running = self._running
        if running is None:
            return
        self._running = None
        try:
            running.stop()
        except OSError as exc:
            raise ModbusServerStopError(exc) from exc
