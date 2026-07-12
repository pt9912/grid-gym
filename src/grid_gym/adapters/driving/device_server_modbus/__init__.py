"""Modbus-TCP-Server-Adapter als `DeviceServerPort`-Implementer
(Field-Server-Pull-Seite, ADR 0075 §2.1).

**Simulations- und Testadapter** ([`GG-SAFE-007`], [`GG-NONGOAL-001`]): grid-gym
ist der Modbus-**Server/Slave**; ein externes EMS (System-under-Test) pollt als
**Master** grid-gyms **simulierte** Geraetewerte als Holding-Register
(`float32`) + Quality als Discrete-Input. **Read-Serving only** (Inbound-Write
ausgegliedert, ADR 0075 §7). **Keine produktive Anlagensteuerung**; Modbus-TCP
hat kein Auth/TLS → Nur-Sim-Netz.

Server-/Slave-Rolle (Gegenrolle zum driven-`protocol_modbus`-Master, ADR 0030).
Module:

- `_config` — `ModbusServerConfig` (bind/register_map/unit_id) + `RegisterMapping`
  + `ModbusServerConfigError`-Familie.
- `_register_map` — `encode_float32` (Encode-Oracle) + `RegisterMap` (on-demand
  aus der Current-Value-Projektion; pymodbus-frei, unit-getestet).
- `_errors` — Adapter-Fehler als `DeviceServerPort`-Vertragsfehler-Subklassen.
- `_adapter` — `ModbusDeviceServerAdapter` + Default-Server-Runner (pymodbus,
  C2-verifiziert) + Runner-Injektion.
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
    ModbusServerConfigError,
    ModbusServerConfigInvalidPortError,
    ModbusServerConfigInvalidUnitIdError,
    ModbusServerConfigRegisterOverlapError,
    RegisterMapping,
)
from grid_gym.adapters.driving.device_server_modbus._errors import (
    ModbusServerBindError,
    ModbusServerStopError,
)
from grid_gym.adapters.driving.device_server_modbus._register_map import (
    RegisterMap,
    encode_float32,
)

__all__ = [
    "ModbusDeviceServerAdapter",
    "ModbusServerBindError",
    "ModbusServerConfig",
    "ModbusServerConfigEmptyFieldError",
    "ModbusServerConfigEmptyRegisterMapError",
    "ModbusServerConfigError",
    "ModbusServerConfigInvalidPortError",
    "ModbusServerConfigInvalidUnitIdError",
    "ModbusServerConfigRegisterOverlapError",
    "ModbusServerStopError",
    "RegisterMap",
    "RegisterMapping",
    "RunningServer",
    "ServerRunner",
    "encode_float32",
]
