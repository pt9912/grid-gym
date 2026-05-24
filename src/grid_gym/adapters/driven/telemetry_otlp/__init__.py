"""OTLP-Adapter-Trio fuer das Observability-Port-Trio
(M3 Welle 6, ADR 0024 §4.5 — produktive Lieferung des
Observability-Sub-Bereichs).

Aufbau (Module unter diesem Paket):

- `_config` — `OtlpAdapterConfig` + `OtlpAdapterConfigError`
  (C1.3a-Lieferung).
- `logs` — `OtlpLogAdapter` (C1.3b-Lieferung).
- `metrics` — `OtlpMetricsAdapter` (C1.3b-Lieferung).
- `traces` — `OtlpTraceAdapter` (C1.3b-Lieferung; `| None`-
  Robustheit in `end_span`/`record_event` per ADR 0024 §4.5.1;
  kein `time.*`-Import per ADR 0024 §4.5.5).

Konsumenten importieren ueber dieses Paket. Die `build_otlp_adapters(
config)`-Factory und der `flush_and_shutdown()`-Helper kommen mit
C1.3c (siehe `M3-welle-6.md §3 C1`).
"""

from grid_gym.adapters.driven.telemetry_otlp._config import (
    OtlpAdapterConfig,
    OtlpAdapterConfigBatchTooLargeError,
    OtlpAdapterConfigEmptyFieldError,
    OtlpAdapterConfigEnvTimeoutParseError,
    OtlpAdapterConfigError,
    OtlpAdapterConfigInvalidHeaderError,
    OtlpAdapterConfigInvalidProtocolError,
    OtlpAdapterConfigNonPositiveError,
    OtlpAdapterConfigOverrides,
    OtlpAdapterConfigTimeoutTooSmallError,
)
from grid_gym.adapters.driven.telemetry_otlp._factory import (
    OtlpAdapterBundle,
    build_otlp_adapters,
)
from grid_gym.adapters.driven.telemetry_otlp.logs import OtlpLogAdapter
from grid_gym.adapters.driven.telemetry_otlp.metrics import (
    OtlpMetricsAdapter,
    OtlpMetricsNameCollisionError,
)
from grid_gym.adapters.driven.telemetry_otlp.traces import OtlpTraceAdapter

__all__ = [
    "OtlpAdapterBundle",
    "OtlpAdapterConfig",
    "OtlpAdapterConfigBatchTooLargeError",
    "OtlpAdapterConfigEmptyFieldError",
    "OtlpAdapterConfigEnvTimeoutParseError",
    "OtlpAdapterConfigError",
    "OtlpAdapterConfigInvalidHeaderError",
    "OtlpAdapterConfigInvalidProtocolError",
    "OtlpAdapterConfigNonPositiveError",
    "OtlpAdapterConfigOverrides",
    "OtlpAdapterConfigTimeoutTooSmallError",
    "OtlpLogAdapter",
    "OtlpMetricsAdapter",
    "OtlpMetricsNameCollisionError",
    "OtlpTraceAdapter",
    "build_otlp_adapters",
]
