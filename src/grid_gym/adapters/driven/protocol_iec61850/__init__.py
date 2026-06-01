# SPDX-License-Identifier: GPL-3.0-only
"""IEC-61850-Adapter als `DeviceProtocolPort`-Implementer
(M4 Welle 5b, ADR 0030 + ADR 0035).

**Simulations- und Testadapter** im Sinne von Lastenheft Z. 1155-1157:
dieses Modul realisiert IEC-61850-MMS-Client-Read gegen einen
IEC-61850-Server (z. B. in-process `pyiec61850.server.IedServer`-
Sibling im Integration-Smoke; produktive IED-Anlagen-Integration
im Welle-6+-Pfad), um Logical-Node-/Data-Object-basierte Telemetry
in deterministischen Test-/Demo-Scenarios zu modellieren. **Keine
produktive Anlagensteuerung.** Welle-5b-Minimum ist Read-only —
produktive IEC-61850-Integration braucht eigene Hardening-Schritte
(IEC-62351-Security, Write-Pfad mit MMS-`write_value`, Report-
Control-Block-Subscription, GOOSE-Pub/Sub, Sampled-Values,
Audit-Trail) ueber den Welle-5b-Scope hinaus.

**Lizenz-Boundary (ADR 0035 Decision I-f):** dieses gesamte
Sub-Paket steht unter **GPLv3** (`SPDX-License-Identifier:
GPL-3.0-only`), weil es gegen das **GPLv3-lizenzierte**
`pyiec61850-ng` / `libiec61850` linkt. Der Rest von grid-gym
bleibt MIT (siehe Top-Level-`LICENSE` und `LICENSES/GPL-3.0.txt`).
`pyiec61850-ng` ist als optionales Extra deklariert; Installation:
`pip install grid-gym[iec61850]`. Ohne installiertes Extra wirft
der Adapter-Konstruktor `Iec61850PortLibraryNotInstalledError`
mit Install-Hinweis.

Aufbau (Module unter diesem Paket):

- `_config` — `Iec61850ProtocolPortConfig` + `Iec61850LnConfig`-
  Profile + `Iec61850ConfigError`-Familie (Decision I-a inline-
  Schema; Konstruktor-Validation mit FC-Allow-List
  `{"MX", "ST", "SP", "CF", "DC"}` und Datatype-Allow-List
  `{"bool", "int32", "float", "string"}`).
- `_codec` — `decode_mms_value`-Helfer (Decision I-c: Mapping
  `MMSClient.read_value`-Returnwert → Python-Native;
  Float-Praezisions-Konvention `Decimal(repr(float))` analog
  ADR 0032 §2.2; Container-vs-Leaf-Erkennung fuer
  `MmsValue type=15`-Containers).
- `_port` — `Iec61850DeviceProtocolPort` + Default-Client-Factory
  (Decision I-b direkt-sync; Decision I-d Per-Target MMS-Read
  mit FC-Override; Decision I-f Optional-Extra-ImportError-Guard).
- `_errors` — IEC-61850-spezifische `DeviceProtocolPort*Error`-
  Subclasses mit strukturierten Konstruktor-Parametern und
  operation-spezifischer Read-/Write-Taxonomie (Pattern analog
  Slice-031/032 + Welle-5a). Neu in Welle 5b:
  `Iec61850PortLibraryNotInstalledError` fuer Decision I-f.

Konsumenten importieren ueber dieses Paket. Decisions:

- ADR 0030 §2.1 — Sync-Vertrag (`pyiec61850.mms.MMSClient` ist
  sync-Context-Manager — Probe-Run-Befund 2026-06-01; kein
  Thread-Marshal noetig).
- ADR 0030 §2.2 — Caller-Scope-Lifecycle (TickLoop ruft
  `start_protocol_ports()`/`stop_protocol_ports()`).
- ADR 0030 §2.3 — stateless aus Replay-Sicht (MMS-Session-State
  und RCB-Subscription-State volatile).
- ADR 0030 §2.4 — Welle-1-IEC-61850-Verzicht-Default wird durch
  Welle-5b-Spike-Lieferung aufgeloest (Pattern ADR 0011;
  M4-Welle-7-Closure schaerft ADR 0030 §2.4 entsprechend).
- ADR 0035 §2.1..§2.6 — Welle-5b-Profile (LN/CDC-Schema inline,
  direkt-sync, Datatype-Set + FC-Mapping, Per-Target-Read mit
  FC-Override, in-process IedServer als Test-Sibling, GPLv3-
  Lizenz-Boundary).
"""

from grid_gym.adapters.driven.protocol_iec61850._codec import (
    decode_mms_value,
)
from grid_gym.adapters.driven.protocol_iec61850._config import (
    Iec61850ConfigEmptyFieldError,
    Iec61850ConfigEmptyPointsError,
    Iec61850ConfigError,
    Iec61850ConfigInvalidAccessError,
    Iec61850ConfigInvalidDatatypeError,
    Iec61850ConfigInvalidFcError,
    Iec61850ConfigInvalidPortError,
    Iec61850ConfigInvalidReferenceError,
    Iec61850ConfigInvalidTimeoutError,
    Iec61850LnConfig,
    Iec61850ProtocolPortConfig,
)
from grid_gym.adapters.driven.protocol_iec61850._errors import (
    Iec61850CodecError,
    Iec61850CodecOverflowError,
    Iec61850CodecValueTypeError,
    Iec61850PortAccessMismatchError,
    Iec61850PortConnectError,
    Iec61850PortDisconnectError,
    Iec61850PortLibraryNotInstalledError,
    Iec61850PortNotStartedError,
    Iec61850PortPointNotFoundError,
    Iec61850PortReadAccessMismatchError,
    Iec61850PortReadConnectionLostError,
    Iec61850PortReadFailedError,
    Iec61850PortReadNotStartedError,
    Iec61850PortWriteAccessMismatchError,
    Iec61850PortWriteFailedError,
    Iec61850PortWriteNotImplementedError,
    Iec61850PortWriteNotStartedError,
)
from grid_gym.adapters.driven.protocol_iec61850._port import (
    Iec61850DeviceProtocolPort,
)

__all__ = [
    "Iec61850CodecError",
    "Iec61850CodecOverflowError",
    "Iec61850CodecValueTypeError",
    "Iec61850ConfigEmptyFieldError",
    "Iec61850ConfigEmptyPointsError",
    "Iec61850ConfigError",
    "Iec61850ConfigInvalidAccessError",
    "Iec61850ConfigInvalidDatatypeError",
    "Iec61850ConfigInvalidFcError",
    "Iec61850ConfigInvalidPortError",
    "Iec61850ConfigInvalidReferenceError",
    "Iec61850ConfigInvalidTimeoutError",
    "Iec61850DeviceProtocolPort",
    "Iec61850LnConfig",
    "Iec61850PortAccessMismatchError",
    "Iec61850PortConnectError",
    "Iec61850PortDisconnectError",
    "Iec61850PortLibraryNotInstalledError",
    "Iec61850PortNotStartedError",
    "Iec61850PortPointNotFoundError",
    "Iec61850PortReadAccessMismatchError",
    "Iec61850PortReadConnectionLostError",
    "Iec61850PortReadFailedError",
    "Iec61850PortReadNotStartedError",
    "Iec61850PortWriteAccessMismatchError",
    "Iec61850PortWriteFailedError",
    "Iec61850PortWriteNotImplementedError",
    "Iec61850PortWriteNotStartedError",
    "Iec61850ProtocolPortConfig",
    "decode_mms_value",
]
