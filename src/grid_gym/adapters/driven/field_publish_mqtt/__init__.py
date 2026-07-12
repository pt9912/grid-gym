"""MQTT-Field-Publish-Adapter als `FieldPublishPort`-Implementer
(Field-Server-Push-Seite, ADR 0075 §2.1).

**Simulations- und Testadapter** ([`GG-SAFE-007`], [`GG-NONGOAL-001`]):
exponiert grid-gyms **simulierte** Geraetetelemetrie an einen MQTT-Broker,
damit ein externes EMS (System-under-Test) sie konsumieren kann. **Keine
produktive Anlagensteuerung**; Broker-Exposure ist Nur-Sim-Netz (keine
Auth/TLS im Slice-073-Scope).

Publish-only (kein Subscribe/Decode/Callback — Gegensatz zum driven
`protocol_mqtt`-Client). Module:

- `_config` — `MqttFieldPublishConfig` (broker/topic_prefix/qos) +
  `MqttFieldPublishConfigError`-Familie.
- `_errors` — Adapter-Fehler als `FieldPublishPort`-Vertragsfehler-
  Subklassen.
- `_adapter` — `MqttFieldPublishAdapter` + Default-Client-Factory.
"""

from grid_gym.adapters.driven.field_publish_mqtt._adapter import (
    ClientFactory,
    MqttFieldPublishAdapter,
)
from grid_gym.adapters.driven.field_publish_mqtt._config import (
    MqttFieldPublishConfig,
    MqttFieldPublishConfigEmptyFieldError,
    MqttFieldPublishConfigError,
    MqttFieldPublishConfigInvalidPortError,
    MqttFieldPublishConfigInvalidQosError,
)
from grid_gym.adapters.driven.field_publish_mqtt._errors import (
    MqttFieldPublishConnectError,
    MqttFieldPublishDisconnectError,
    MqttFieldPublishNotStartedError,
    MqttFieldPublishPublishFailedError,
)

__all__ = [
    "ClientFactory",
    "MqttFieldPublishAdapter",
    "MqttFieldPublishConfig",
    "MqttFieldPublishConfigEmptyFieldError",
    "MqttFieldPublishConfigError",
    "MqttFieldPublishConfigInvalidPortError",
    "MqttFieldPublishConfigInvalidQosError",
    "MqttFieldPublishConnectError",
    "MqttFieldPublishDisconnectError",
    "MqttFieldPublishNotStartedError",
    "MqttFieldPublishPublishFailedError",
]
