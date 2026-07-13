"""Adapter-spezifische Fehler fuer den Modbus-Server-Adapter
(ADR 0075 §2.1/§2.4).

Jeder Fehler ist eine Subclass des passenden `DeviceServerPort`-Vertragsfehlers,
damit Aufrufer pauschal gegen den Port-Vertrag catchen koennen (Muster analog
`MqttFieldPublish*Error` → `FieldPublishPort*Error`).
"""

from __future__ import annotations

from grid_gym.hexagon.ports.driving.device_server import (
    DeviceServerPortStartError,
    DeviceServerPortStopError,
)


class ModbusServerBindError(DeviceServerPortStartError):
    """`start()` konnte nicht binden — Port belegt / OSError.

    Harter Fehler **vor dem ersten Tick** (ADR 0075 §2.4; kein Lazy-Connect-
    Analogon wie beim driven `DeviceProtocolPort`).
    """

    def __init__(self, bind_host: str, bind_port: int, cause: Exception) -> None:
        super().__init__(
            f"ModbusDeviceServerAdapter: bind auf {bind_host}:{bind_port} fehlgeschlagen: {cause}"
        )
        self.bind_host: str = bind_host
        self.bind_port: int = bind_port
        self.cause: Exception = cause


class ModbusServerStopError(DeviceServerPortStopError):
    """`stop()` konnte den Server nicht sauber drainen/schliessen (harter
    Close-Fehler; der Idempotenz-Vertrag deckt den No-op-Fall separat ab)."""

    def __init__(self, cause: Exception) -> None:
        super().__init__(f"ModbusDeviceServerAdapter: stop/close fehlgeschlagen: {cause}")
        self.cause: Exception = cause


class ModbusServerWiringError(ValueError):
    """Fehlkonfiguration der Inbound-Write-Verdrahtung (ADR 0076; Review-Fund
    Slice 075): `config.write_map` deklariert beschreibbare Sollwert-Fenster, aber
    es ist **kein** `inbound_buffer` injiziert.

    Ohne Puffer wird der Write-`SimAction`-Hook nicht gebaut — ein Master-Write auf
    ein Sollwert-Fenster landet im Datastore und wird **still verworfen** (nie zu
    einem `Command` geroutet). Fail-fast bei Konstruktion statt stillem No-op."""

    def __init__(self) -> None:
        super().__init__(
            "ModbusDeviceServerAdapter: config.write_map ist gesetzt, aber kein "
            "inbound_buffer injiziert — Master-Writes wuerden akzeptiert, aber nie zu "
            "einem Command geroutet. Entweder inbound_buffer reichen oder write_map leeren."
        )
