"""DNP3-Adapter als `DeviceProtocolPort`-Implementer
(M4 Welle 5a, ADR 0030 + ADR 0034).

**Simulations- und Testadapter** im Sinne von Lastenheft Z. 1161-1163:
dieses Modul realisiert DNP3-Master/Client-Read gegen einen DNP3-
Outstation (z. B. `dnp3-outstation`-Library im Test-Sibling, produktive
Industrie-Steuerungen im Welle-6+-Pfad), um Point-basierte Telemetry
in deterministischen Test-/Demo-Scenarios zu modellieren. **Keine
produktive Anlagensteuerung.** Welle-5a-Minimum ist Read-only —
produktive DNP3-Integration braucht eigene Hardening-Schritte
(Secure-Authentication-Layer per IEEE-1815-2012 §10, Write-Pfad
mit Direct-Operate / Select-Before-Operate, Event-Class-Polling,
Audit-Trail) ueber den Welle-5a-Scope hinaus.

Aufbau (Module unter diesem Paket):

- `_config` — `Dnp3ProtocolPortConfig` + `Dnp3PointConfig`-
  Profile + `Dnp3ConfigError`-Familie (Decision D-a inline-Schema;
  Konstruktor-Validation mit Group/Variation-Allow-List
  `{(1,1), (1,2), (30,1), (30,5)}`).
- `_codec` — `decode_point_value`-Helfer (Decision D-c: Mapping
  `nfm-dnp3.AnalogInput`/`BinaryInput` -> `Decimal`;
  Float-Praezisions-Konvention `Decimal(repr(float))` analog
  ADR 0032 §2.2). Eigene `Dnp3CodecError`-Familie fuer
  Group-/Type-Mismatches.
- `_port` — `Dnp3DeviceProtocolPort` + Default-Client-Factory
  (Decision D-b direkt-sync; Decision D-d Class-0-Polling-Read
  mit Resultat-Filter).
- `_errors` — DNP3-spezifische `DeviceProtocolPort*Error`-
  Subclasses mit strukturierten Konstruktor-Parametern und
  operation-spezifischer Read-/Write-Taxonomie (Pattern analog
  Slice-031/032-Folgen aus M4-Welle-3/4).

Konsumenten importieren ueber dieses Paket. Decisions:

- ADR 0030 §2.1 — Sync-Vertrag (nfm-dnp3-Sync-Master passt direkt;
  kein Thread-Marshal noetig).
- ADR 0030 §2.2 — Caller-Scope-Lifecycle (TickLoop ruft
  `start_protocol_ports()`/`stop_protocol_ports()`).
- ADR 0030 §2.3 — stateless aus Replay-Sicht (Reconnect-State und
  IIN-Restart-Flag volatile).
- ADR 0030 §2.4 — Welle-1-DNP3-Verzicht-Default wird durch
  Welle-5a-Spike-Lieferung aufgeloest (Pattern ADR 0011;
  M4-Welle-7-Closure schaerft ADR 0030 §2.4 entsprechend).
- ADR 0034 §2.1..§2.5 — Welle-5a-Profile (Point-Schema inline,
  direkt-sync, Group/Variation-Set, Class-0-Polling-Read,
  in-process-Test-Sibling).
"""

from grid_gym.adapters.driven.protocol_dnp3._codec import (
    Dnp3CodecError,
    Dnp3CodecGroupMismatchError,
    Dnp3CodecValueTypeError,
    decode_point_value,
)
from grid_gym.adapters.driven.protocol_dnp3._config import (
    Dnp3ConfigEmptyFieldError,
    Dnp3ConfigEmptyPointsError,
    Dnp3ConfigError,
    Dnp3ConfigInvalidAccessError,
    Dnp3ConfigInvalidAddressError,
    Dnp3ConfigInvalidGroupVariationError,
    Dnp3ConfigInvalidIndexError,
    Dnp3ConfigInvalidPortError,
    Dnp3ConfigInvalidTimeoutError,
    Dnp3PointConfig,
    Dnp3ProtocolPortConfig,
)
from grid_gym.adapters.driven.protocol_dnp3._errors import (
    Dnp3PortAccessMismatchError,
    Dnp3PortConnectError,
    Dnp3PortDisconnectError,
    Dnp3PortNotStartedError,
    Dnp3PortPointNotInPollResultError,
    Dnp3PortReadAccessMismatchError,
    Dnp3PortReadFailedError,
    Dnp3PortReadNotStartedError,
    Dnp3PortWriteAccessMismatchError,
    Dnp3PortWriteFailedError,
    Dnp3PortWriteNotImplementedError,
    Dnp3PortWriteNotStartedError,
)
from grid_gym.adapters.driven.protocol_dnp3._port import (
    Dnp3DeviceProtocolPort,
)

__all__ = [
    "Dnp3CodecError",
    "Dnp3CodecGroupMismatchError",
    "Dnp3CodecValueTypeError",
    "Dnp3ConfigEmptyFieldError",
    "Dnp3ConfigEmptyPointsError",
    "Dnp3ConfigError",
    "Dnp3ConfigInvalidAccessError",
    "Dnp3ConfigInvalidAddressError",
    "Dnp3ConfigInvalidGroupVariationError",
    "Dnp3ConfigInvalidIndexError",
    "Dnp3ConfigInvalidPortError",
    "Dnp3ConfigInvalidTimeoutError",
    "Dnp3DeviceProtocolPort",
    "Dnp3PointConfig",
    "Dnp3PortAccessMismatchError",
    "Dnp3PortConnectError",
    "Dnp3PortDisconnectError",
    "Dnp3PortNotStartedError",
    "Dnp3PortPointNotInPollResultError",
    "Dnp3PortReadAccessMismatchError",
    "Dnp3PortReadFailedError",
    "Dnp3PortReadNotStartedError",
    "Dnp3PortWriteAccessMismatchError",
    "Dnp3PortWriteFailedError",
    "Dnp3PortWriteNotImplementedError",
    "Dnp3PortWriteNotStartedError",
    "Dnp3ProtocolPortConfig",
    "decode_point_value",
]
