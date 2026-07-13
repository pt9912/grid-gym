"""`ModbusDeviceServerAdapter` — `DeviceServerPort`-Implementer (ADR 0075 §2.1).

Modbus-TCP-**Server/Slave** fuer die **Pull-Seite** der Field-Server-Surface:
ein externes EMS (System-under-Test, z. B. `bess-ems`) pollt als Modbus-**Master**
grid-gyms simulierte Geraetewerte als Holding-Register (`float32`) + Quality als
Discrete-Input. Die Register kommen aus der geteilten Current-Value-Projektion
ueber die `RegisterMap` (on-demand-Berechnung + Encode-Oracle).

**Inbound-Write→`Command` (optional, ADR 0076)**: ist ein geteilter
`InboundCommandBuffer` injiziert **und** eine `write_map` konfiguriert, traegt der
Server einen Master-Write (FC06/FC16) auf ein Sollwert-Fenster als `Command` in
den Kern zurueck. Der pymodbus-`SimAction`-Hook dekodiert den `float32`
(`InboundWriteDecoder`) und puffert ihn thread-sicher; der `TickLoop` zieht den
Puffer pro Tick als `inbound_source` (Schritt A0i). Ohne Puffer/`write_map` bleibt
es reines **Read-Serving** (byte-identisch/pin-neutral).

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
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Final, Protocol, runtime_checkable

from grid_gym.adapters.driving._field_current_value import CurrentValueProjection
from grid_gym.adapters.driving._inbound_command_buffer import InboundCommandBuffer
from grid_gym.adapters.driving.device_server_modbus._config import ModbusServerConfig
from grid_gym.adapters.driving.device_server_modbus._errors import (
    ModbusServerBindError,
    ModbusServerStopError,
    ModbusServerWiringError,
)
from grid_gym.adapters.driving.device_server_modbus._register_map import RegisterMap
from grid_gym.adapters.driving.device_server_modbus._write_map import InboundWriteDecoder

if TYPE_CHECKING:
    from pymodbus.server import ModbusTcpServer
    from pymodbus.simulator import SimDevice

_LOGGER: logging.Logger = logging.getLogger(__name__)

# Modbus-Read-Funktions-Codes (der server-interne `async_setValues` waehlt
# darueber den Ziel-Block; FC03 = Holding-Register, FC02 = Discrete-Inputs).
_FC_READ_HOLDING_REGISTERS: Final[int] = 3
_FC_READ_DISCRETE_INPUTS: Final[int] = 2
_FLOAT32_REGISTERS: Final[int] = 2

# Master-Write-Funktions-Codes, die pymodbus auf den Holding-Block routet und die
# ein vollstaendiges `float32`-Sollwert-Fenster (2 Register) schreiben koennen:
# FC06 (Write-Single), FC16 (Write-Multiple), FC23 (Read/Write-Multiple).
# **Diskriminator** in der SimAction: nur diese Codes sind echte Inbound-Master-
# Writes — der interne Refresh-Push nutzt FC03 (`async_setValues` mit dem Read-Code
# als Block-Selektor), Reads liefern `set_values is None`. Damit loest der Refresh
# nie einen Inbound-`Command` aus.
#
# Vollstaendigkeit ggue. `SimRuntime._fx_mapper` (`{3,6,16,22,23}` → Holding):
# - **FC23** MUSS rein (Review-Fund Slice 075): ein Master kann einen `float32`-
#   Sollwert per Read/Write-Multiple schreiben; ohne FC23 wuerde der Write still
#   gedroppt (pymodbus quittiert Erfolg, aber kein `Command` wird erfasst).
# - **FC22** (Mask-Write) bleibt bewusst draussen: er schreibt nur **ein** Register
#   und kann nie ein 2-Register-`float32`-Fenster bilden (der
#   `InboundWriteDecoder` wuerde es ohnehin ueberspringen).
# - **FC06** deckt selbst nie ein volles Fenster (1 Register); er steht als
#   Vollstaendigkeits-Marker im Set (ein FC06-Teil-Write wird vom Decoder
#   uebersprungen), schadet aber nicht.
_FC_WRITE_HOLDING: Final[frozenset[int]] = frozenset({6, 16, 23})

# pymodbus-`SimAction`-Signatur (async): wird bei jedem Register-Zugriff gerufen.
# `set_values is None` == Read; sonst die zu schreibenden Werte. Rueckgabe `None`
# == „Write erlauben" (ein truthy `ExcCodes` wuerde den Write ablehnen bzw. im
# Refresh-Pfad `server.async_setValues` werfen lassen).
_ModbusRegisterAction = Callable[
    [int, int, int, int, "list[int]", "list[int] | list[bool] | None"],
    Awaitable["None"],
]

_REFRESH_INTERVAL_S: Final[float] = 0.05
_READY_TIMEOUT_S: Final[float] = 5.0
_SHUTDOWN_TIMEOUT_S: Final[float] = 5.0


@runtime_checkable
class RunningServer(Protocol):
    """Handle auf einen laufenden Server; `stop()` faehrt ihn herunter."""

    def stop(self) -> None: ...


# Runner-Hook (Default fuehrt den Bind-Check + startet den pymodbus-Server;
# Tests reichen einen Fake durch, damit kein echter Socket/Server noetig ist).
# `inbound_buffer` (optional, ADR 0076): geteilter Inbound-Write-Puffer; `None`
# → reines Read-Serving.
ServerRunner = Callable[
    [ModbusServerConfig, RegisterMap, "InboundCommandBuffer | None"], RunningServer
]


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
    hoechsten gemappten Adresse + `float32`-Breite (2 Register).

    Deckt **Read- und Write-Fenster** ab — ein Sollwert-Register (`write_map`) muss
    im Holding-Block liegen, sonst wiese pymodbus einen Master-Write mit
    `ILLEGAL_ADDRESS` ab, **bevor** die SimAction feuert (die Bereichs-Pruefung
    laeuft vor dem Action-Hook, `SimRuntime.get_reg_block`)."""
    addresses = [mapping.address for mapping in config.register_map]
    addresses += [mapping.address for mapping in config.write_map]
    return max(addresses) + _FLOAT32_REGISTERS


def _build_device(
    config: ModbusServerConfig,
    action: _ModbusRegisterAction | None = None,
) -> SimDevice:
    """Baut das pymodbus-3.13-`SimDevice` (non-shared Bloecke): Holding-Register
    (`REGISTERS`, ab Adresse 0) + Discrete-Inputs (`BITS`, ein Bit je Mapping in
    `register_map`-Reihenfolge). Coil-/Input-Register-Bloecke sind Platzhalter
    (grid-gym serviert sie nicht, aber leere Bloecke sind unzulaessig). Die
    tatsaechlichen Werte pusht der Refresh-Task via `async_setValues`.

    `action` (optional, ADR 0076 §2.1) ist der Inbound-Write-Hook: pymodbus ruft
    ihn bei jedem Register-Zugriff; er filtert Master-Writes (FC06/FC16) heraus
    und puffert sie. `None` (Default) → reines Read-Serving (byte-identisch)."""
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
    return SimDevice(
        config.unit_id,
        simdata=([coils], [discrete], [holding], [inputs]),
        action=action,
    )


def _make_write_action(
    decoder: InboundWriteDecoder,
    inbound_buffer: InboundCommandBuffer,
) -> _ModbusRegisterAction:
    """Baut den Inbound-Write-`SimAction`-Hook (ADR 0076 §2.1).

    pymodbus ruft den Hook (im Server-Loop-Thread) bei **jedem** Register-Zugriff.
    Er wird nur bei einem echten Master-Holding-Write aktiv (`set_values is not
    None` **und** `function_code ∈ {FC06, FC16}`), dekodiert die geschriebenen
    `float32`-Fenster ueber den `InboundWriteDecoder` und puffert je Fenster einen
    Inbound-Write (`InboundCommandBuffer.enqueue`, thread-sicher, vergibt die
    `arrival_sequence`). Er gibt **immer `None`** zurueck — er beobachtet nur, er
    lehnt keinen Write ab und stoert den Refresh-Push (FC03) nicht."""

    async def _on_register_access(
        function_code: int,
        start_address: int,
        address: int,
        count: int,
        current_registers: list[int],
        set_values: list[int] | list[bool] | None,
    ) -> None:
        _ = (start_address, count, current_registers)
        # Nur echte Master-Holding-Writes (FC06/FC16, `set_values is not None`)
        # puffern; Reads + der interne Refresh-Push (FC03) fallen durch (kein
        # Return-Wert → `None` → Write erlaubt, Refresh-Pfad ungestoert).
        if set_values is not None and function_code in _FC_WRITE_HOLDING:
            for write in decoder.decode(address, [int(value) for value in set_values]):
                inbound_buffer.enqueue(
                    write.target_device_id, write.command_type, {"value": write.value}
                )

    return _on_register_access


class _PymodbusRunningServer:
    """Der echte pymodbus-3.13-Server in einem adapter-internen Loop-Thread.

    Serviert ein `SimDevice`; ein Refresh-Task pusht die aus der Projektion
    gerechneten `RegisterMap`-Werte via `server.async_setValues`. Der initiale
    Push laeuft vor `start()`-Freischaltung (deterministischer erster Poll)."""

    def __init__(
        self,
        config: ModbusServerConfig,
        register_map: RegisterMap,
        inbound_buffer: InboundCommandBuffer | None = None,
    ) -> None:
        self._config: ModbusServerConfig = config
        self._register_map: RegisterMap = register_map
        self._discrete_count: int = len(config.register_map)
        # ADR 0076 §2.1: Inbound-Write-Hook nur bauen, wenn ein Puffer da ist UND
        # ein beschreibbares Fenster konfiguriert ist — sonst kein `action` (reines
        # Read-Serving, byte-identisch).
        decoder = InboundWriteDecoder(config)
        self._write_action: _ModbusRegisterAction | None = (
            _make_write_action(decoder, inbound_buffer)
            if inbound_buffer is not None and decoder.has_writable
            else None
        )
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

        try:
            # Device-Build + Server-Konstruktion IM try (Review-Fund C2): ein
            # Fehler hier muss `_ready` setzen, sonst haengt `start()` bis zum
            # Timeout. TypeError/ValueError = defensiv (Config-Validierung +
            # totales encode_float32 schliessen die realen Trigger bereits aus).
            server = ModbusTcpServer(
                _build_device(self._config, self._write_action),
                address=(self._config.bind_host, self._config.bind_port),
            )
            self._server = server
            await server.serve_forever(background=True)  # bind + listen (non-blocking)
            await self._push(server)  # initialer Push → erster Poll deterministisch
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            # Bind-/Listen-Race (pymodbus wirft RuntimeError „Could not start
            # listen"; OSError bei Port-Problemen) bzw. Datastore-Aufbau →
            # start() meldet hart statt zu haengen.
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
            except (OSError, RuntimeError, TypeError, ValueError):
                # Refresh ist best-effort: ein Fehler darf den Server nicht toeten
                # (der naechste Tick zieht nach). `server.async_setValues` wirft
                # TypeError, falls der Datastore einen ExcCode liefert (z. B.
                # Adress-Fehlkonfiguration) — hier abgefangen + geloggt statt den
                # Task still sterben zu lassen (Review-Fund C2).
                _LOGGER.exception("Modbus-Server: Projektion-Refresh fehlgeschlagen")

    async def _push(self, server: ModbusTcpServer) -> None:
        """Schreibt einen **konsistenten** Projektions-Frame in den Datastore:
        je Read-Fenster ein `float32` (2 Register) + die Discrete-Inputs (Quality)
        aus genau **einem** Snapshot — kein Tearing zwischen den Registern eines
        `float32` (Review-Fund C2).

        **Nur Read-Fenster** (Review-Fund Slice 075): der Refresh pusht die
        `register_map`-Messwerte **fenster-weise** und laesst die `write_map`-
        Sollwert-Register **unangetastet**. Wuerde er (wie zuvor) den ganzen
        Holding-Block als Nullen-gefuellten Frame schreiben, ueberschriebe er einen
        gerade von einem Master geschriebenen Sollwert nach ≤ Refresh-Intervall mit
        `0` — ein pollender Master saehe seinen Sollwert stumm auf `0` zuruecksetzen.
        Der Command-Pfad ist davon unberuehrt (der Write wird beim Eintreffen vom
        `SimAction`-Hook erfasst, nicht ueber Readback)."""
        holding_windows, discrete = self._register_map.refresh_frame(self._discrete_count)
        for address, values in holding_windows:
            await server.async_setValues(
                self._config.unit_id, _FC_READ_HOLDING_REGISTERS, address, values
            )
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


def _default_server_runner(
    config: ModbusServerConfig,
    register_map: RegisterMap,
    inbound_buffer: InboundCommandBuffer | None = None,
) -> RunningServer:
    """Default-Runner: synchroner Bind-in-use-Check, dann der reale
    pymodbus-Server im Loop-Thread."""
    _preflight_bind(config.bind_host, config.bind_port)
    return _PymodbusRunningServer(config, register_map, inbound_buffer)


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
        inbound_buffer: InboundCommandBuffer | None = None,
    ) -> None:
        # ADR 0076 §2.1 (Review-Fund Slice 075): beschreibbare Sollwert-Fenster
        # (`write_map`) ohne injizierten Puffer sind eine Fehlkonfiguration — der
        # Write-Hook wuerde nicht gebaut, Master-Writes still verworfen. Fail-fast.
        if config.write_map and inbound_buffer is None:
            raise ModbusServerWiringError
        self._config: ModbusServerConfig = config
        self._projection: CurrentValueProjection = projection
        self._server_runner: ServerRunner = server_runner or _default_server_runner
        # ADR 0076 §2.1: geteilter Inbound-Write-Puffer (Write-Callback enqueued;
        # der `TickLoop` zieht ihn als `inbound_source`, Schritt A0i). `None` →
        # reines Read-Serving (kein Write-Hook, byte-identisch/pin-neutral).
        self._inbound_buffer: InboundCommandBuffer | None = inbound_buffer
        self._running: RunningServer | None = None

    def start(self) -> None:
        """Bind + serve. Idempotent. Bind-in-use → `ModbusServerBindError`
        (harter Fehler; der Lauf startet nicht)."""
        if self._running is not None:
            return
        register_map = RegisterMap(self._config, self._projection)
        try:
            self._running = self._server_runner(self._config, register_map, self._inbound_buffer)
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
