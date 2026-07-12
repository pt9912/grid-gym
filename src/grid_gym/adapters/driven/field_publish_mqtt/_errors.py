"""Adapter-spezifische Fehler fuer den MQTT-Field-Publish-Adapter
(ADR 0075 §2.1).

Jeder Fehler ist eine Subclass des passenden `FieldPublishPort`-
Vertragsfehlers, damit Aufrufer pauschal gegen den Port-Vertrag catchen
koennen (Muster analog `MqttPort*Error` -> `DeviceProtocolPortError` aus
`protocol_mqtt`).
"""

from __future__ import annotations

from grid_gym.hexagon.ports.driven.field_publish import (
    FieldPublishPortPublishError,
    FieldPublishPortStartError,
    FieldPublishPortStopError,
)


class MqttFieldPublishConnectError(FieldPublishPortStartError):
    """`start()` konnte nicht zum Broker connecten (OSError von paho)."""

    def __init__(self, broker_host: str, broker_port: int, cause: OSError) -> None:
        super().__init__(
            f"MqttFieldPublishAdapter: connect zu {broker_host}:{broker_port} "
            f"fehlgeschlagen: {cause}"
        )
        self.broker_host: str = broker_host
        self.broker_port: int = broker_port
        self.cause: OSError = cause


class MqttFieldPublishNotStartedError(FieldPublishPortPublishError):
    """`publish()` wurde vor `start()` (oder nach `stop()`) gerufen."""

    def __init__(self) -> None:
        super().__init__(
            "MqttFieldPublishAdapter: publish() vor start() (oder nach stop()) — "
            "kein aktiver Client."
        )


class MqttFieldPublishInvalidTopicError(FieldPublishPortPublishError):
    """`device_id`/`metric` ist als MQTT-Topic-Segment ungueltig (leer oder
    enthaelt `/`, `+`, `#`) — Review-Fix #5.

    Ungeprueft wuerde ein `/` die Topic-Hierarchie verschieben (Fehlrouting an
    SUT-Wildcard-Subscribes) und `+`/`#` von paho als ungueltiges Publish-Topic
    mit `ValueError` abgelehnt (der dann still im Driver-`_publish_field`
    verschluckt wuerde). Der Adapter lehnt darum fail-fast typisiert ab.
    """

    def __init__(self, segment_name: str, value: str) -> None:
        super().__init__(
            f"MqttFieldPublishAdapter: {segment_name}={value!r} ist als "
            "MQTT-Topic-Segment ungueltig (leer oder enthaelt '/', '+', '#')."
        )
        self.segment_name: str = segment_name
        self.value: str = value


class MqttFieldPublishPublishFailedError(FieldPublishPortPublishError):
    """paho-mqtt `publish()` lieferte einen Non-Success-Returncode."""

    def __init__(self, topic: str, rc: int) -> None:
        super().__init__(
            f"MqttFieldPublishAdapter: publish auf Topic {topic!r} lieferte "
            f"paho-Returncode rc={rc} (!= MQTT_ERR_SUCCESS)."
        )
        self.topic: str = topic
        self.rc: int = rc


class MqttFieldPublishDisconnectError(FieldPublishPortStopError):
    """`stop()` konnte nicht sauber vom Broker disconnecten (OSError)."""

    def __init__(self, cause: OSError) -> None:
        super().__init__(f"MqttFieldPublishAdapter: disconnect fehlgeschlagen: {cause}")
        self.cause: OSError = cause
