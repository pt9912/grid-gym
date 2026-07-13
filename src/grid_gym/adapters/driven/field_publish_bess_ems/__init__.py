"""bess-ems-konformer Field-Publisher (Slice 077 S2, ADR 0078).

Driven Push-Adapter neben `field_publish_mqtt`: aggregiert je Tick grid-gyms
per-Punkt-Battery-Telemetrie + Fault-Surface eines `TickResult` zu den **breiten**
bess-ems-Envelope-Frames (`telemetry`/`status`/`fault`) und published sie an einen
MQTT-Broker — damit ein externes, **unveraendertes** EMS (`bess-ems`) grid-gym als
simuliertes Feld konsumiert (HIL, [`GG-TEST-004`]). Der Driver ruft `start()` /
`publish_tick()` je Tick / `stop()`. **Simulations-/Testadapter** ([`GG-SAFE-007`]):
Nur-Sim-Netz, keine produktive Anlagensteuerung.

Module:

- `_encoder` — reines Feld-Mapping + Frame-Bau (`encode_telemetry`/`encode_status`/
  `encode_fault`/`encode_command_ack`; MQTT-frei, gegen Schema + Golden-Vektoren
  strukturell testbar).
- `_adapter` — `BessEmsFieldPublishAdapter`: paho-MQTT-Lifecycle + Tick-Aggregation +
  `command_ack`-Empfangs-Echo (ADR 0078 §2.9).
- `_config` / `_errors` — Broker-/Topic-/Ack-Profil (fail-fast) + Fehler-Familie.
"""

from grid_gym.adapters.driven.field_publish_bess_ems._adapter import (
    BessEmsFieldPublishAdapter,
)
from grid_gym.adapters.driven.field_publish_bess_ems._config import (
    REQUIRED_FIELD_BLOCKS,
    BessEmsFieldPublishConfig,
    BessEmsFieldPublishConfigEmptyFieldError,
    BessEmsFieldPublishConfigEndpointError,
    BessEmsFieldPublishConfigError,
    BessEmsFieldPublishConfigInvalidPortError,
    BessEmsFieldPublishConfigInvalidQosError,
    BessEmsFieldPublishConfigInvalidTopicSegmentError,
    BessEmsFieldPublishConfigMissingFieldBlocksError,
)
from grid_gym.adapters.driven.field_publish_bess_ems._encoder import (
    REQUIRED_METRICS,
    BessEmsEncoderMissingMetricError,
    command_id_from_payload,
    encode_command_ack,
    encode_fault,
    encode_status,
    encode_telemetry,
)
from grid_gym.adapters.driven.field_publish_bess_ems._errors import (
    BessEmsFieldPublishConnectError,
    BessEmsFieldPublishDisconnectError,
    BessEmsFieldPublishError,
    BessEmsFieldPublishInvalidAssetIdError,
    BessEmsFieldPublishNotStartedError,
    BessEmsFieldPublishPublishFailedError,
)

__all__ = [
    "REQUIRED_FIELD_BLOCKS",
    "REQUIRED_METRICS",
    "BessEmsEncoderMissingMetricError",
    "BessEmsFieldPublishAdapter",
    "BessEmsFieldPublishConfig",
    "BessEmsFieldPublishConfigEmptyFieldError",
    "BessEmsFieldPublishConfigEndpointError",
    "BessEmsFieldPublishConfigError",
    "BessEmsFieldPublishConfigInvalidPortError",
    "BessEmsFieldPublishConfigInvalidQosError",
    "BessEmsFieldPublishConfigInvalidTopicSegmentError",
    "BessEmsFieldPublishConfigMissingFieldBlocksError",
    "BessEmsFieldPublishConnectError",
    "BessEmsFieldPublishDisconnectError",
    "BessEmsFieldPublishError",
    "BessEmsFieldPublishInvalidAssetIdError",
    "BessEmsFieldPublishNotStartedError",
    "BessEmsFieldPublishPublishFailedError",
    "command_id_from_payload",
    "encode_command_ack",
    "encode_fault",
    "encode_status",
    "encode_telemetry",
]
