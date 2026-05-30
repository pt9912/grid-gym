"""MQTT-Adapter als `DeviceProtocolPort`-Implementer
(M4 Welle 2, ADR 0030 + ADR 0031).

**Simulations- und Testadapter** im Sinne von Lastenheft Z. 1161-1163:
dieses Modul realisiert MQTT-Pub/Sub gegen einen Standard-MQTT-Broker
(z. B. Mosquitto), um Telemetry-Empfang und Command-Versand in
deterministischen Test-/Demo-Scenarios zu modellieren. **Keine
produktive Anlagensteuerung.** Produktive MQTT-Integration braucht
eigene Hardening-Schritte (Authentifizierung, TLS, Access-Control,
Audit-Trail) ueber den Welle-2-Scope hinaus.

Aufbau (Module unter diesem Paket):

- `_config` — `MqttProtocolPortConfig` + `MqttTopicConfig`-Profile
  (Decision 4a inline-Schema im Scenario-YAML; Konstruktor-
  Validation mit `MqttConfigError`-Familie).
- `_codec` — `encode_command`/`encode_telemetry` (deterministisch
  via `canonical_json`, Decision 4b) + `decode_command`/
  `decode_telemetry` (asymmetrisch tolerant per `json.loads` mit
  `parse_float=Decimal`); `MqttCodecError`-Familie fuer Decode-
  Fehler auf der Empfangs-Seite.
- `_topic_resolver` — Reverse-Index `telemetry_topic -> device_id`
  und Subscribe-Topic-Liste (Decision 4d-Helper).
- `error_translation` — Callback-Exception-Boundary
  (`safe_callback`); `BLE001` ist nur in dieser Datei aktiviert
  (`tool.ruff.per-file-ignores`).
- `_port` — `MqttDeviceProtocolPort` + Default-Client-Factory.

Konsumenten importieren ueber dieses Paket. Decisions:

- ADR 0030 §2.1 — Sync-Vertrag (paho-mqtt-Loop-Thread marshallt
  intern via Per-Target `queue.Queue`).
- ADR 0030 §2.2 — Caller-Scope-Lifecycle (TickLoop ruft
  `start_protocol_ports()`/`stop_protocol_ports()`).
- ADR 0030 §2.3 — stateless aus Replay-Sicht (Reconnect-State ist
  volatile, kein Snapshot-Bump).
- ADR 0031 §2.1..§2.4 — Welle-2-Profile (Topic-Schema inline,
  `canonical_json`-Codec, QoS 0/1, Per-Target-Queue-Marshal).
"""

from grid_gym.adapters.driven.protocol_mqtt._codec import (
    MqttCodecDecodeError,
    MqttCodecError,
    MqttCodecInvalidEnumError,
    MqttCodecJsonDecodeError,
    MqttCodecMissingFieldError,
    MqttCodecPayloadShapeError,
    MqttCodecUtf8DecodeError,
    decode_command,
    decode_telemetry,
    encode_command,
    encode_telemetry,
)
from grid_gym.adapters.driven.protocol_mqtt._config import (
    MqttConfigDuplicateTopicError,
    MqttConfigEmptyFieldError,
    MqttConfigEmptyTopicError,
    MqttConfigEmptyTopicsError,
    MqttConfigError,
    MqttConfigInvalidPortError,
    MqttConfigInvalidQosError,
    MqttProtocolPortConfig,
    MqttTopicConfig,
)
from grid_gym.adapters.driven.protocol_mqtt._errors import (
    MqttPortConnectError,
    MqttPortDisconnectError,
    MqttPortNoCommandTopicError,
    MqttPortNotStartedError,
    MqttPortPublishFailedError,
)
from grid_gym.adapters.driven.protocol_mqtt._port import MqttDeviceProtocolPort
from grid_gym.adapters.driven.protocol_mqtt._topic_resolver import (
    build_telemetry_topic_index,
    collect_subscribe_topics,
)

__all__ = [
    "MqttCodecDecodeError",
    "MqttCodecError",
    "MqttCodecInvalidEnumError",
    "MqttCodecJsonDecodeError",
    "MqttCodecMissingFieldError",
    "MqttCodecPayloadShapeError",
    "MqttCodecUtf8DecodeError",
    "MqttConfigDuplicateTopicError",
    "MqttConfigEmptyFieldError",
    "MqttConfigEmptyTopicError",
    "MqttConfigEmptyTopicsError",
    "MqttConfigError",
    "MqttConfigInvalidPortError",
    "MqttConfigInvalidQosError",
    "MqttDeviceProtocolPort",
    "MqttPortConnectError",
    "MqttPortDisconnectError",
    "MqttPortNoCommandTopicError",
    "MqttPortNotStartedError",
    "MqttPortPublishFailedError",
    "MqttProtocolPortConfig",
    "MqttTopicConfig",
    "build_telemetry_topic_index",
    "collect_subscribe_topics",
    "decode_command",
    "decode_telemetry",
    "encode_command",
    "encode_telemetry",
]
