"""Topic-Reverse-Index fuer den paho-mqtt-`on_message`-Callback
(M4 Welle 2, ADR 0031 §2.4).

Decision 4d: paho-mqtt callbacks receive raw MQTT-Topics als String;
um die Telemetry-Message dem richtigen `device_id`-Queue zuzuordnen,
brauchen wir einen O(1)-Lookup `topic_string -> device_id`. Dieses
Modul kapselt den Index-Bau aus der `MqttProtocolPortConfig` heraus,
damit er in Unit-Tests isoliert pruefbar bleibt (siehe
`test_mqtt_topic_resolver.py`).

Wildcard-Subscribes (`#`, `+`) sind in Welle 2 **nicht** unterstuetzt
— ADR 0031 §2.1 deklariert Topic-Schemas inline und pro `device_id`
eindeutig. Welle 6 (Cross-Adapter-Hardening) koennte Wildcard-
Subscribes per Folge-ADR einfuehren; bis dahin ist jeder Subscribe
exakt-Match.
"""

from __future__ import annotations

from collections.abc import Mapping

from grid_gym.adapters.driven.protocol_mqtt._config import (
    MqttProtocolPortConfig,
    MqttTopicConfig,
)


def build_telemetry_topic_index(
    config: MqttProtocolPortConfig,
) -> Mapping[str, str]:
    """Baut den Reverse-Index `telemetry_topic -> device_id` aus dem
    Konfigs-Topic-Mapping.

    Wird im paho-mqtt-`on_message`-Callback (Loop-Thread) aufgerufen,
    um `msg.topic` einer Per-Target-Queue zuzuordnen. Eindeutigkeit
    ist im `MqttProtocolPortConfig._validate_topics`-Aufruf bereits
    erzwungen (`MqttConfigDuplicateTopicError`).

    Devices ohne `telemetry`-Topic (nur Publish-Pfad) fallen aus dem
    Index — der Callback ignoriert dann Messages mit fremdem Topic
    grundsaetzlich (kein Fehler, weil paho-mqtt nur Topics liefert,
    auf die wir per `subscribe()` zugehoert haben).
    """
    index: dict[str, str] = {}
    for device_id, topic_cfg in config.topics.items():
        if topic_cfg.telemetry is not None:
            index[topic_cfg.telemetry] = device_id
    return index


def collect_subscribe_topics(
    config: MqttProtocolPortConfig,
) -> tuple[tuple[str, int], ...]:
    """Liefert die `(topic, qos)`-Liste, die der Adapter beim `start()`
    an `paho.mqtt.client.Client.subscribe(...)` durchreichen muss.

    Reihenfolge ist deterministisch (sortiert nach `device_id`), damit
    `start()` reproduzierbar ist und Tests die Subscribe-Argumente
    pinnen koennen. Devices ohne `telemetry`-Topic fehlen in der Liste
    (kein Subscribe noetig).
    """
    items: list[tuple[str, int]] = []
    for device_id in sorted(config.topics.keys()):
        topic_cfg: MqttTopicConfig = config.topics[device_id]
        if topic_cfg.telemetry is not None:
            items.append((topic_cfg.telemetry, topic_cfg.qos_subscribe))
    return tuple(items)
