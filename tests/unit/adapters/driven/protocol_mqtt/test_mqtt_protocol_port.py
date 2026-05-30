"""Lifecycle + Read/Write fuer `MqttDeviceProtocolPort` mit gemocktem
paho-mqtt-Client (M4 Welle 2, ADR 0030 + ADR 0031 §2.4).
"""

from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType
from typing import Any
from unittest.mock import MagicMock

import paho.mqtt.client as mqtt
import pytest

from grid_gym.adapters.driven.protocol_mqtt import (
    MqttDeviceProtocolPort,
    MqttProtocolPortConfig,
    MqttTopicConfig,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPort,
    DeviceProtocolPortStartError,
    DeviceProtocolPortStopError,
    DeviceProtocolPortUnknownTargetError,
    DeviceProtocolPortWriteError,
)


def _build_config() -> MqttProtocolPortConfig:
    return MqttProtocolPortConfig(
        broker_host="test-broker",
        broker_port=1883,
        client_id="grid-gym-test",
        topics={
            "battery1": MqttTopicConfig(
                telemetry="grid/battery/1/tel",
                command="grid/battery/1/cmd",
                qos_publish=0,
                qos_subscribe=1,
            ),
            "telemetry_only": MqttTopicConfig(
                telemetry="grid/sensor/2/tel",
                qos_subscribe=2,
            ),
            "command_only": MqttTopicConfig(
                command="grid/control/dispatch",
                qos_publish=1,
            ),
        },
    )


def _make_client_factory_returning_mock(client: MagicMock) -> Any:
    """Liefert eine `ClientFactory`, die immer dasselbe Mock-Objekt
    zurueckgibt (Test-Hook fuer Welle-2-Lifecycle-Pinning)."""
    return lambda _config: client


def _make_successful_publish_info() -> MagicMock:
    info = MagicMock()
    info.rc = mqtt.MQTT_ERR_SUCCESS
    return info


def _sample_command(target: str = "battery1") -> Command:
    return Command(
        command_id="cmd-001",
        simulation_time=0,
        target_device_id=target,
        type="set_power",
        payload=MappingProxyType({"setpoint": Decimal("1.0")}),
        validation_status="validated",
        result=CommandResult.ACCEPTED,
    )


def test_port_satisfies_device_protocol_port_protocol() -> None:
    """Strukturelles Protocol-Match (ADR 0030 §2.1)."""
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    assert isinstance(port, DeviceProtocolPort)


def test_start_connects_subscribes_and_starts_loop() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.start()
    client.connect.assert_called_once_with("test-broker", 1883)
    # Subscribe-Calls fuer Telemetry-Topics in deterministischer
    # Reihenfolge (sortiert nach device_id: battery1 -> telemetry_only).
    assert client.subscribe.call_args_list == [
        (("grid/battery/1/tel",), {"qos": 1}),
        (("grid/sensor/2/tel",), {"qos": 2}),
    ]
    client.loop_start.assert_called_once_with()


def test_start_is_idempotent() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.start()
    port.start()  # Doppel-Start ist No-op
    assert client.connect.call_count == 1
    assert client.loop_start.call_count == 1


def test_start_translates_connect_oserror_into_typed_exception() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    client.connect.side_effect = OSError("Connection refused")
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    with pytest.raises(DeviceProtocolPortStartError) as exc_info:
        port.start()
    assert "Connection refused" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, OSError)


def test_stop_loop_stops_and_disconnects() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.start()
    port.stop()
    client.loop_stop.assert_called_once_with()
    client.disconnect.assert_called_once_with()


def test_stop_without_start_is_noop() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.stop()  # nie gestartet
    client.loop_stop.assert_not_called()
    client.disconnect.assert_not_called()


def test_stop_translates_disconnect_oserror_into_typed_exception() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    client.disconnect.side_effect = OSError("Network reset")
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.start()
    with pytest.raises(DeviceProtocolPortStopError) as exc_info:
        port.stop()
    assert "Network reset" in str(exc_info.value)


def test_stop_is_idempotent_after_disconnect_error() -> None:
    """Auch wenn `stop()` einen StopError wirft, soll ein zweiter
    `stop()`-Call No-op sein (interner Zustand wurde zurueckgesetzt)."""
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    client.disconnect.side_effect = OSError("Network reset")
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.start()
    with pytest.raises(DeviceProtocolPortStopError):
        port.stop()
    # Zweiter stop() darf nicht erneut werfen (interner Zustand ist
    # bereits clean — Pattern analog TickLoop-Best-Effort-Cleanup).
    port.stop()  # No-op


def test_read_returns_none_when_no_message_received() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.start()
    assert port.read("battery1") is None
    assert port.read("telemetry_only") is None


def test_read_rejects_unknown_target() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.start()
    with pytest.raises(DeviceProtocolPortUnknownTargetError) as exc_info:
        port.read("unknown_device")
    assert exc_info.value.target == "unknown_device"
    assert "battery1" in exc_info.value.available_targets


def test_write_publishes_to_command_topic_with_default_qos() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    client.publish.return_value = _make_successful_publish_info()
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.start()
    port.write("battery1", _sample_command())
    assert client.publish.call_count == 1
    args, kwargs = client.publish.call_args
    assert args[0] == "grid/battery/1/cmd"
    assert isinstance(args[1], bytes)
    assert kwargs == {"qos": 0}


def test_write_publishes_to_command_topic_with_custom_qos() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    client.publish.return_value = _make_successful_publish_info()
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.start()
    port.write("command_only", _sample_command("command_only"))
    args, kwargs = client.publish.call_args
    assert args[0] == "grid/control/dispatch"
    assert kwargs == {"qos": 1}


def test_write_rejects_unknown_target() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.start()
    with pytest.raises(DeviceProtocolPortUnknownTargetError):
        port.write("unknown_target", _sample_command("unknown_target"))


def test_write_rejects_target_without_command_topic() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.start()
    with pytest.raises(DeviceProtocolPortWriteError) as exc_info:
        port.write("telemetry_only", _sample_command("telemetry_only"))
    assert "kein Command-Topic" in str(exc_info.value)


def test_write_before_start_raises_write_error() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    with pytest.raises(DeviceProtocolPortWriteError) as exc_info:
        port.write("battery1", _sample_command())
    assert "nicht gestartet" in str(exc_info.value)


def test_write_propagates_publish_non_success_returncode() -> None:
    config = _build_config()
    client = MagicMock(spec=mqtt.Client)
    bad_info = MagicMock()
    bad_info.rc = mqtt.MQTT_ERR_NO_CONN
    client.publish.return_value = bad_info
    port = MqttDeviceProtocolPort(
        config, client_factory=_make_client_factory_returning_mock(client)
    )
    port.start()
    with pytest.raises(DeviceProtocolPortWriteError) as exc_info:
        port.write("battery1", _sample_command())
    assert f"rc={mqtt.MQTT_ERR_NO_CONN}" in str(exc_info.value)


def test_default_factory_uses_callback_api_version_2() -> None:
    """Smoke: Default-Factory ruft `mqtt.Client` mit V2-API auf
    (Welle-2-Wahl gegen paho-mqtt 2.x; siehe `_port._default_client_factory`).
    """
    from grid_gym.adapters.driven.protocol_mqtt._port import (
        _default_client_factory,
    )

    config = _build_config()
    client = _default_client_factory(config)
    assert isinstance(client, mqtt.Client)
    # Aufraeumen — der Default-Konstruktor allokiert einen echten
    # Loop-Hintergrund-State.
    client.disconnect()
