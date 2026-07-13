"""Modbus-TCP-Server-Adapter als `DeviceServerPort`-Implementer
(Field-Server-Pull-Seite, ADR 0075 §2.1).

**Simulations- und Testadapter** ([`GG-SAFE-007`], [`GG-NONGOAL-001`]): grid-gym
ist der Modbus-**Server/Slave**; ein externes EMS (System-under-Test) pollt als
**Master** grid-gyms **simulierte** Geraetewerte als Holding-Register
(`float32`) + Quality als Discrete-Input und kann — mit konfigurierter `write_map`
+ injiziertem `InboundCommandBuffer` — Sollwerte als `Command` zurueckschreiben
(FC06/FC16, ADR 0076). **Keine produktive Anlagensteuerung**; Modbus-TCP hat kein
Auth/TLS → Nur-Sim-Netz (ein beschreibbarer Feldbus erweitert die Angriffsflaeche,
ADR 0076 §2.7).

Server-/Slave-Rolle (Gegenrolle zum driven-`protocol_modbus`-Master, ADR 0030).
Module:

- `_config` — `ModbusServerConfig` (bind/register_map/write_map/unit_id) +
  `RegisterMapping`/`WritableRegisterMapping` + `ModbusServerConfigError`-Familie.
- `_register_map` — `encode_float32` (Encode-Oracle) + `RegisterMap` (on-demand
  aus der Current-Value-Projektion; pymodbus-frei, unit-getestet).
- `_write_map` — `decode_float32` (Decode-Oracle) + `InboundWriteDecoder`
  (Gegenrichtung: Write-Fenster → `DecodedInboundWrite`; pymodbus-frei).
- `_errors` — Adapter-Fehler als `DeviceServerPort`-Vertragsfehler-Subklassen.
- `_adapter` — `ModbusDeviceServerAdapter` + Default-Server-Runner (pymodbus,
  C2-verifiziert) + Runner-Injektion + Inbound-Write-`SimAction`-Hook.
"""

from grid_gym.adapters.driving.device_server_modbus._adapter import (
    ModbusDeviceServerAdapter,
    RunningServer,
    ServerRunner,
)
from grid_gym.adapters.driving.device_server_modbus._config import (
    ModbusServerConfig,
    ModbusServerConfigEmptyFieldError,
    ModbusServerConfigEmptyRegisterMapError,
    ModbusServerConfigEmptyWriteFieldError,
    ModbusServerConfigError,
    ModbusServerConfigInvalidAddressError,
    ModbusServerConfigInvalidPortError,
    ModbusServerConfigInvalidUnitIdError,
    ModbusServerConfigInvalidWriteAddressError,
    ModbusServerConfigRegisterOverlapError,
    RegisterMapping,
    WritableRegisterMapping,
)
from grid_gym.adapters.driving.device_server_modbus._errors import (
    ModbusServerBindError,
    ModbusServerStopError,
)
from grid_gym.adapters.driving.device_server_modbus._register_map import (
    RegisterMap,
    encode_float32,
)
from grid_gym.adapters.driving.device_server_modbus._write_map import (
    DecodedInboundWrite,
    InboundWriteDecoder,
    decode_float32,
)

__all__ = [
    "DecodedInboundWrite",
    "InboundWriteDecoder",
    "ModbusDeviceServerAdapter",
    "ModbusServerBindError",
    "ModbusServerConfig",
    "ModbusServerConfigEmptyFieldError",
    "ModbusServerConfigEmptyRegisterMapError",
    "ModbusServerConfigEmptyWriteFieldError",
    "ModbusServerConfigError",
    "ModbusServerConfigInvalidAddressError",
    "ModbusServerConfigInvalidPortError",
    "ModbusServerConfigInvalidUnitIdError",
    "ModbusServerConfigInvalidWriteAddressError",
    "ModbusServerConfigRegisterOverlapError",
    "ModbusServerStopError",
    "RegisterMap",
    "RegisterMapping",
    "RunningServer",
    "ServerRunner",
    "WritableRegisterMapping",
    "decode_float32",
    "encode_float32",
]
