"""Topic-Reverse-Index + Subscribe-Liste fuer den Welle-2-MQTT-Adapter
(M4 Welle 2, ADR 0031 §2.1 + §2.4).
"""

from __future__ import annotations

import pytest

from grid_gym.adapters.driven.protocol_mqtt import (
    MqttConfigDuplicateTopicError,
    MqttConfigEmptyFieldError,
    MqttConfigEmptyTopicError,
    MqttConfigEmptyTopicsError,
    MqttConfigInvalidPortError,
    MqttConfigInvalidQosError,
    MqttProtocolPortConfig,
    MqttTopicConfig,
    build_telemetry_topic_index,
    collect_subscribe_topics,
)


def _build_basic_config() -> MqttProtocolPortConfig:
    return MqttProtocolPortConfig(
        broker_host="localhost",
        broker_port=1883,
        client_id="grid-gym-sim",
        topics={
            "battery1": MqttTopicConfig(
                telemetry="grid/devices/battery/1/telemetry",
                command="grid/devices/battery/1/command",
                qos_publish=0,
                qos_subscribe=1,
            ),
            "pv1": MqttTopicConfig(
                telemetry="grid/devices/pv/1/telemetry",
                command=None,
                qos_subscribe=2,
            ),
            "command_only": MqttTopicConfig(
                telemetry=None,
                command="grid/control/dispatch",
                qos_publish=1,
            ),
        },
    )


def test_telemetry_topic_index_skips_command_only_target() -> None:
    config = _build_basic_config()
    index = build_telemetry_topic_index(config)
    assert index == {
        "grid/devices/battery/1/telemetry": "battery1",
        "grid/devices/pv/1/telemetry": "pv1",
    }
    # `command_only` ist nicht im Telemetry-Index, weil es keinen
    # Subscribe-Pfad hat.
    assert "grid/control/dispatch" not in index


def test_subscribe_topics_collect_sorted_by_device_id() -> None:
    config = _build_basic_config()
    items = collect_subscribe_topics(config)
    # Sortiert nach device_id; command_only ist nicht dabei.
    assert items == (
        ("grid/devices/battery/1/telemetry", 1),
        ("grid/devices/pv/1/telemetry", 2),
    )


def test_config_validates_empty_broker_host() -> None:
    with pytest.raises(MqttConfigEmptyFieldError) as exc_info:
        MqttProtocolPortConfig(
            broker_host="",
            broker_port=1883,
            client_id="x",
            topics={"d": MqttTopicConfig(telemetry="t")},
        )
    assert exc_info.value.field_name == "broker_host"


def test_config_validates_empty_client_id() -> None:
    with pytest.raises(MqttConfigEmptyFieldError) as exc_info:
        MqttProtocolPortConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="",
            topics={"d": MqttTopicConfig(telemetry="t")},
        )
    assert exc_info.value.field_name == "client_id"


@pytest.mark.parametrize("port", [0, -1, 65536, 99999])
def test_config_rejects_invalid_port(port: int) -> None:
    with pytest.raises(MqttConfigInvalidPortError) as exc_info:
        MqttProtocolPortConfig(
            broker_host="localhost",
            broker_port=port,
            client_id="x",
            topics={"d": MqttTopicConfig(telemetry="t")},
        )
    assert exc_info.value.value == port


def test_config_rejects_empty_topics() -> None:
    with pytest.raises(MqttConfigEmptyTopicsError):
        MqttProtocolPortConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="x",
            topics={},
        )


def test_config_rejects_topic_without_telemetry_or_command() -> None:
    with pytest.raises(MqttConfigEmptyTopicError) as exc_info:
        MqttProtocolPortConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="x",
            topics={"empty_target": MqttTopicConfig()},
        )
    assert exc_info.value.device_id == "empty_target"


@pytest.mark.parametrize(
    ("qos_field", "qos_value"),
    [
        ("qos_publish", 3),
        ("qos_publish", -1),
        ("qos_subscribe", 99),
    ],
)
def test_config_rejects_invalid_qos(qos_field: str, qos_value: int) -> None:
    kwargs: dict[str, object] = {
        "telemetry": "t",
        "command": "c",
        "qos_publish": 0,
        "qos_subscribe": 1,
    }
    kwargs[qos_field] = qos_value
    with pytest.raises(MqttConfigInvalidQosError) as exc_info:
        MqttProtocolPortConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="x",
            topics={"d": MqttTopicConfig(**kwargs)},  # type: ignore[arg-type]
        )
    assert exc_info.value.field_name == qos_field
    assert exc_info.value.value == qos_value
    assert exc_info.value.device_id == "d"


def test_config_rejects_duplicate_topic_strings_across_devices() -> None:
    shared_topic = "grid/shared/topic"
    with pytest.raises(MqttConfigDuplicateTopicError) as exc_info:
        MqttProtocolPortConfig(
            broker_host="localhost",
            broker_port=1883,
            client_id="x",
            topics={
                "a": MqttTopicConfig(telemetry=shared_topic),
                "b": MqttTopicConfig(telemetry=shared_topic),
            },
        )
    assert exc_info.value.topic == shared_topic
    assert set(exc_info.value.device_ids) == {"a", "b"}


def test_config_allows_telemetry_only_target() -> None:
    config = MqttProtocolPortConfig(
        broker_host="localhost",
        broker_port=1883,
        client_id="x",
        topics={"d": MqttTopicConfig(telemetry="t")},
    )
    assert collect_subscribe_topics(config) == (("t", 1),)


def test_config_allows_command_only_target() -> None:
    config = MqttProtocolPortConfig(
        broker_host="localhost",
        broker_port=1883,
        client_id="x",
        topics={"d": MqttTopicConfig(command="c")},
    )
    assert collect_subscribe_topics(config) == ()
    assert build_telemetry_topic_index(config) == {}
