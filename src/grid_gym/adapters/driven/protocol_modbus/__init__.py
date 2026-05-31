"""Modbus-TCP-Adapter als `DeviceProtocolPort`-Implementer
(M4 Welle 3, ADR 0030 + ADR 0032).

**Simulations- und Testadapter** im Sinne von Lastenheft Z. 1161-1163:
dieses Modul realisiert Modbus-TCP-Read/Write gegen einen Standard-
Modbus-Server (z. B. pymodbus' eigener Server fuer Tests, produktive
Wechselrichter/Energiemeter im Welle-6+-Pfad), um Register-basierte
Telemetry und Setpoint-Commands in deterministischen Test-/Demo-
Scenarios zu modellieren. **Keine produktive Anlagensteuerung.**
Produktive Modbus-Integration braucht eigene Hardening-Schritte
(Authentication-Layer, TLS-Tunnel, Audit-Trail, Watchdog-Logik)
ueber den Welle-3-Scope hinaus.

Aufbau (Module unter diesem Paket):

- `_config` — `ModbusProtocolPortConfig` + `ModbusRegisterConfig`-
  Profile + `ModbusDatatype`-Enum (Decision M-a/M-b/M-d/M-e inline-
  Schema; Konstruktor-Validation mit `ModbusConfigError`-Familie).
- `_codec` — `encode_value_to_registers` /
  `decode_registers_to_value` (Decision M-b: `struct.pack`/
  `struct.unpack` mit Format-String aus Datatype + Byte-Order;
  Word-Swap-Rotation fuer Multi-Register-Datatypes). Eigene
  `ModbusCodecError`-Familie fuer Range-/Decode-Fehler.
- `_port` — `ModbusDeviceProtocolPort` + Default-Client-Factory
  (Decision M-c: direkt-sync; kein Background-Thread).
- `_errors` — Modbus-spezifische `DeviceProtocolPort*Error`-
  Subclasses mit strukturierten Konstruktor-Parametern und
  operation-spezifischer Read-/Write-Taxonomie.

Konsumenten importieren ueber dieses Paket. Decisions:

- ADR 0030 §2.1 — Sync-Vertrag (pymodbus-Sync-Client passt direkt;
  kein Thread-Marshal noetig).
- ADR 0030 §2.2 — Caller-Scope-Lifecycle (TickLoop ruft
  `start_protocol_ports()`/`stop_protocol_ports()`).
- ADR 0030 §2.3 — stateless aus Replay-Sicht.
- ADR 0032 §2.1..§2.6 — Welle-3-Profile (Register-Schema inline,
  Datatype-Set + Byte-Order-Defaults, direkt-sync-Polling,
  FC03/FC10-Defaults, Slave-Unit-ID, in-process-Test-Sibling).
"""

from grid_gym.adapters.driven.protocol_modbus._codec import (
    ModbusCodecDecodeError,
    ModbusCodecError,
    ModbusCodecNonFiniteError,
    ModbusCodecOutOfRangeError,
    ModbusCodecRegisterCountMismatchError,
    decode_registers_to_value,
    encode_value_to_registers,
)
from grid_gym.adapters.driven.protocol_modbus._config import (
    ModbusConfigEmptyFieldError,
    ModbusConfigEmptyRegistersError,
    ModbusConfigError,
    ModbusConfigFunctionCodeAccessMismatchError,
    ModbusConfigFunctionCodeDatatypeMismatchError,
    ModbusConfigInvalidAccessError,
    ModbusConfigInvalidAddressError,
    ModbusConfigInvalidByteOrderError,
    ModbusConfigInvalidFunctionCodeError,
    ModbusConfigInvalidPortError,
    ModbusConfigInvalidTimeoutError,
    ModbusConfigInvalidUnitIdError,
    ModbusDatatype,
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
    ModbusPortReadAccessMismatchError,
    ModbusPortReadFailedError,
    ModbusPortReadNotStartedError,
    ModbusPortWriteAccessMismatchError,
    ModbusPortWriteFailedError,
    ModbusPortWriteNotStartedError,
)
from grid_gym.adapters.driven.protocol_modbus._port import (
    ModbusDeviceProtocolPort,
)

__all__ = [
    "ModbusCodecDecodeError",
    "ModbusCodecError",
    "ModbusCodecNonFiniteError",
    "ModbusCodecOutOfRangeError",
    "ModbusCodecRegisterCountMismatchError",
    "ModbusConfigEmptyFieldError",
    "ModbusConfigEmptyRegistersError",
    "ModbusConfigError",
    "ModbusConfigFunctionCodeAccessMismatchError",
    "ModbusConfigFunctionCodeDatatypeMismatchError",
    "ModbusConfigInvalidAccessError",
    "ModbusConfigInvalidAddressError",
    "ModbusConfigInvalidByteOrderError",
    "ModbusConfigInvalidFunctionCodeError",
    "ModbusConfigInvalidPortError",
    "ModbusConfigInvalidTimeoutError",
    "ModbusConfigInvalidUnitIdError",
    "ModbusDatatype",
    "ModbusDeviceProtocolPort",
    "ModbusPortAccessMismatchError",
    "ModbusPortConnectError",
    "ModbusPortDisconnectError",
    "ModbusPortMissingCommandPayloadError",
    "ModbusPortNotStartedError",
    "ModbusPortReadAccessMismatchError",
    "ModbusPortReadFailedError",
    "ModbusPortReadNotStartedError",
    "ModbusPortWriteAccessMismatchError",
    "ModbusPortWriteFailedError",
    "ModbusPortWriteNotStartedError",
    "ModbusProtocolPortConfig",
    "ModbusRegisterConfig",
    "datatype_register_count",
    "decode_registers_to_value",
    "encode_value_to_registers",
    "resolve_function_code",
    "resolve_unit_id",
]
