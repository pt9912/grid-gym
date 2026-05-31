"""OPC-UA-Adapter als `DeviceProtocolPort`-Implementer
(M4 Welle 4, ADR 0030 + ADR 0033).

**Simulations- und Testadapter** im Sinne von Lastenheft Z. 1161-1163:
dieses Modul realisiert OPC-UA-Client-Read/Write gegen einen
Standard-OPC-UA-Server (z. B. asyncua's eigener Server fuer Tests,
produktive Industrie-Steuerungen im Welle-6+-Pfad), um Node-basierte
Telemetry und Setpoint-Commands in deterministischen Test-/Demo-
Scenarios zu modellieren. **Keine produktive Anlagensteuerung.**
Produktive OPC-UA-Integration braucht eigene Hardening-Schritte
(User/X509-Authentifizierung, Encryption-Suiten, Audit-Trail,
Subscription-Lifecycle) ueber den Welle-4-Scope hinaus.

Aufbau (Module unter diesem Paket):

- `_config` — `OpcuaProtocolPortConfig` + `OpcuaNodeConfig`-
  Profile + `OpcuaDatatype`-Enum (Decision O-a/O-c inline-Schema;
  Konstruktor-Validation mit `OpcuaConfigError`-Familie).
- `_codec` — `encode_value_to_variant` / `decode_variant_to_value`
  (Decision O-c: Mapping `OpcuaDatatype` -> `ua.VariantType`;
  Float/Double -> `Decimal` via `repr` analog ADR 0032 §2.2).
  Eigene `OpcuaCodecError`-Familie fuer Range-/Decode-Fehler.
- `_loop_thread` — `OpcuaLoopThread` (Decision O-b: dedizierter
  `asyncio.AbstractEventLoop` in `threading.Thread(daemon=True)`
  mit `run_coroutine_threadsafe`-Marshal). Erstes Repo-Pattern
  fuer Welle 5+ (DNP3/IEC, falls Spike) und Welle 6.
- `_port` — `OpcuaDeviceProtocolPort` + Default-Client-Factory
  (Decision O-b/O-d: Polling-Read + Direct-Write via Loop-Thread).
- `_errors` — OPC-UA-spezifische `DeviceProtocolPort*Error`-
  Subclasses mit strukturierten Konstruktor-Parametern und
  operation-spezifischer Read-/Write-Taxonomie (Pattern analog
  Slice-031-Folge aus M4-Welle-3).

Konsumenten importieren ueber dieses Paket. Decisions:

- ADR 0030 §2.1 — Sync-Vertrag (asyncua ist rein-async; Adapter-
  internes Marshal noetig).
- ADR 0030 §2.2 — Caller-Scope-Lifecycle (TickLoop ruft
  `start_protocol_ports()`/`stop_protocol_ports()`).
- ADR 0030 §2.3 — stateless aus Replay-Sicht.
- ADR 0033 §2.1..§2.5 — Welle-4-Profile (Node-ID-Schema inline,
  Async-Bridge via Loop-Thread, Datatype-Set Welle-4-Minimum,
  Polling-Read + Direct-Write, in-process-Test-Sibling).
"""

from grid_gym.adapters.driven.protocol_opcua._codec import (
    OpcuaCodecDecodeError,
    OpcuaCodecError,
    OpcuaCodecNonFiniteError,
    OpcuaCodecOutOfRangeError,
    OpcuaCodecPayloadTypeError,
    decode_variant_to_value,
    encode_value_to_variant,
)
from grid_gym.adapters.driven.protocol_opcua._config import (
    OpcuaConfigEmptyFieldError,
    OpcuaConfigEmptyNodesError,
    OpcuaConfigError,
    OpcuaConfigInvalidAccessError,
    OpcuaConfigInvalidNamespaceError,
    OpcuaConfigInvalidNodeIdError,
    OpcuaConfigInvalidTimeoutError,
    OpcuaDatatype,
    OpcuaNodeConfig,
    OpcuaProtocolPortConfig,
)
from grid_gym.adapters.driven.protocol_opcua._errors import (
    OpcuaPortAccessMismatchError,
    OpcuaPortConnectError,
    OpcuaPortDisconnectError,
    OpcuaPortMissingCommandPayloadError,
    OpcuaPortNotStartedError,
    OpcuaPortReadAccessMismatchError,
    OpcuaPortReadFailedError,
    OpcuaPortReadNotStartedError,
    OpcuaPortWriteAccessMismatchError,
    OpcuaPortWriteFailedError,
    OpcuaPortWriteNotStartedError,
)
from grid_gym.adapters.driven.protocol_opcua._loop_thread import (
    OpcuaLoopThread,
    OpcuaLoopThreadError,
    OpcuaLoopThreadNotStartedError,
)
from grid_gym.adapters.driven.protocol_opcua._port import (
    OpcuaDeviceProtocolPort,
)

__all__ = [
    "OpcuaCodecDecodeError",
    "OpcuaCodecError",
    "OpcuaCodecNonFiniteError",
    "OpcuaCodecOutOfRangeError",
    "OpcuaCodecPayloadTypeError",
    "OpcuaConfigEmptyFieldError",
    "OpcuaConfigEmptyNodesError",
    "OpcuaConfigError",
    "OpcuaConfigInvalidAccessError",
    "OpcuaConfigInvalidNamespaceError",
    "OpcuaConfigInvalidNodeIdError",
    "OpcuaConfigInvalidTimeoutError",
    "OpcuaDatatype",
    "OpcuaDeviceProtocolPort",
    "OpcuaLoopThread",
    "OpcuaLoopThreadError",
    "OpcuaLoopThreadNotStartedError",
    "OpcuaNodeConfig",
    "OpcuaPortAccessMismatchError",
    "OpcuaPortConnectError",
    "OpcuaPortDisconnectError",
    "OpcuaPortMissingCommandPayloadError",
    "OpcuaPortNotStartedError",
    "OpcuaPortReadAccessMismatchError",
    "OpcuaPortReadFailedError",
    "OpcuaPortReadNotStartedError",
    "OpcuaPortWriteAccessMismatchError",
    "OpcuaPortWriteFailedError",
    "OpcuaPortWriteNotStartedError",
    "OpcuaProtocolPortConfig",
    "decode_variant_to_value",
    "encode_value_to_variant",
]
