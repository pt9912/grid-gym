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

**pymodbus-3.13-Naht (C1b/C2-Schnitt)**: pymodbus 3.13 hat den Datastore auf das
`SimData`/`SimDevice`-Modell umgebaut (der alte `ModbusServerContext`/
`ModbusDeviceContext`-Shim serviert nur **statisch**: `async_setValues` liefert
fuer einen `ModbusDeviceContext` `DEVICE_BUSY`, kein Live-Update). Der reale,
dynamisch aus der Projektion gespeiste Server wird darum im **Read-E2E (Slice
074 C2)** verdrahtet + verifiziert — dort steht ein echter pollender Master als
Oracle. C1b liefert den pymodbus-freien Kern (Config/`RegisterMap`/Encode/
Lifecycle/Preflight, alles unit-getestet); `_default_server_runner` faehrt den
synchronen Bind-Check und verweist fuer das Serving auf C2.

**Simulations-/Testadapter** ([`GG-SAFE-007`], [`GG-NONGOAL-001`]): keine
produktive Anlagensteuerung; Modbus-TCP hat kein Auth/TLS → Nur-Sim-Netz.
"""

from __future__ import annotations

import socket
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from grid_gym.adapters.driving._field_current_value import CurrentValueProjection
from grid_gym.adapters.driving.device_server_modbus._config import ModbusServerConfig
from grid_gym.adapters.driving.device_server_modbus._errors import (
    ModbusServerBindError,
    ModbusServerStopError,
)
from grid_gym.adapters.driving.device_server_modbus._register_map import RegisterMap


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


def _default_server_runner(
    config: ModbusServerConfig,
    _register_map: RegisterMap,
) -> RunningServer:
    """Default-Runner: synchroner Bind-in-use-Check, dann der reale
    pymodbus-Server.

    **Slice 074 C2**: das dynamische Serving aus der Projektion ueber das
    pymodbus-3.13-`SimData`/`SimDevice`-Modell (inkl. Adress-Offset + Live-
    Update) wird im Read-E2E verdrahtet + gegen einen echten Master verifiziert.
    Bis dahin einen `server_runner` injizieren (siehe Modul-Docstring)."""
    _preflight_bind(config.bind_host, config.bind_port)
    raise NotImplementedError(
        "ModbusDeviceServerAdapter: der reale pymodbus-Server (SimData/SimDevice, "
        "pymodbus 3.13) wird in Slice 074 C2 verdrahtet + per Read-E2E verifiziert. "
        "Bis dahin einen server_runner injizieren."
    )


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
