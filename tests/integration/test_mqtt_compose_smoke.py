"""M4-Welle-2-C2 Integration-Smoke fuer den MQTT-Adapter
(`MqttDeviceProtocolPort` gegen Mosquitto-Sibling).

Spawnt einen `eclipse-mosquitto:2`-Sibling-Container via
testcontainers-`DockerContainer` (gleiches Pattern wie der OTLP-
Compose-Smoke in `test_otlp_compose_smoke.py` — kein DockerCompose,
weil der `test-runner` kein `docker`-CLI hat).

End-to-End-Pfad:

1. Mosquitto-Sibling kommt online; Readiness via Log-Pattern
   `mosquitto version 2.x.x running`.
2. Test-Hilfs-Publisher (`paho.mqtt.client.Client`) postet eine
   serialisierte `TelemetryPoint`-Message gegen das Subscribe-
   Topic des Adapters.
3. Adapter zieht die Message ueber `read(target)` aus seiner Per-
   Target-Queue (Decision 4d) — Bounded-Poll-Loop, weil paho-mqtt
   asynchron liefert.
4. Adapter publisht ueber `write(target, command)` ein `Command`
   auf das Command-Topic; ein Test-Hilfs-Subscriber prueft, dass
   die Message im Broker landete (Bounded-Poll-Loop).

Cross-Cutting (Lastenheft Z. 1161-1163): Smoke ist Test-Infrastruktur
unter `tests/integration/`; **keine produktive Anlagensteuerung**.

Welle 6 (Cross-Adapter-Hardening) wird auf diesem Pattern OTel-
Span-Wrap der Adapter-Calls ergaenzen (ADR 0024 §4.5).
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from decimal import Decimal
from types import MappingProxyType
from typing import Final

import paho.mqtt.client as mqtt
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from grid_gym.adapters.driven.protocol_mqtt import (
    MqttDeviceProtocolPort,
    MqttProtocolPortConfig,
    MqttTopicConfig,
    decode_command,
    encode_telemetry,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint

_MQTT_PORT: Final[int] = 1883
_MOSQUITTO_IMAGE: Final[str] = "eclipse-mosquitto:2"
_READY_LOG: Final[str] = "mosquitto version"
_BROKER_READY_TIMEOUT_S: Final[float] = 30.0
_POLL_TIMEOUT_S: Final[float] = 5.0
_POLL_INTERVAL_S: Final[float] = 0.1
_CLIENT_CONNECT_TIMEOUT_S: Final[float] = 5.0

# Inline-Mosquitto-Config: eclipse-mosquitto:2 verweigert anonymen
# Zugriff per Default; fuer Test-Smoke schalten wir das frei.
# Persistence off, damit Container-Restart keine Volume-Reste
# hinterlaesst.
_MOSQUITTO_CONFIG: Final[str] = "listener 1883\nallow_anonymous true\npersistence false\n"


@pytest.fixture(scope="module")
def _mosquitto() -> Iterator[DockerContainer]:
    """Spawnt einen Mosquitto-Sibling fuer das ganze Test-Modul
    (Boot ~1-2s; Funktions-Scope waere Verschwendung).

    Overridet das Default-CMD des Mosquitto-Images, damit wir die
    Anonymous-Config inline schreiben koennen (Bind-Mount waere im
    Sibling-Container-Modus path-translation-anfaellig).
    """
    container = (
        DockerContainer(_MOSQUITTO_IMAGE)
        .with_exposed_ports(_MQTT_PORT)
        .with_command(
            [
                "sh",
                "-c",
                f'printf "%s" "{_MOSQUITTO_CONFIG}" > /tmp/mosq.conf '
                "&& exec mosquitto -c /tmp/mosq.conf",
            ]
        )
    )
    container.start()
    try:
        wait_for_logs(container, _READY_LOG, timeout=_BROKER_READY_TIMEOUT_S)
        yield container
    finally:
        container.stop()


def _build_config(host: str, port: int) -> MqttProtocolPortConfig:
    return MqttProtocolPortConfig(
        broker_host=host,
        broker_port=port,
        client_id="grid-gym-smoke-port",
        topics={
            "battery1": MqttTopicConfig(
                telemetry="grid/test/battery/1/telemetry",
                command="grid/test/battery/1/command",
                qos_publish=1,
                qos_subscribe=1,
            ),
        },
    )


def _sample_telemetry() -> TelemetryPoint:
    return TelemetryPoint(
        run_id="smoke-run-1",
        tick=1,
        simulation_time=1000,
        device_id="battery1",
        metric="state_of_charge_pct",
        value=Decimal("85.5"),
        unit="pct",
        quality=Quality.VALID,
        source="smoke.publisher",
        sequence=1,
    )


def _sample_command() -> Command:
    return Command(
        command_id="smoke-cmd-1",
        simulation_time=1000,
        target_device_id="battery1",
        type="set_power_setpoint",
        payload=MappingProxyType({"setpoint_kw": Decimal("5.0")}),
        validation_status="validated",
        result=CommandResult.ACCEPTED,
    )


def _wait_for_paho_connect(client: mqtt.Client) -> None:
    """Blockierender Wait, bis paho die `connect()`-Bestaetigung
    verarbeitet hat (CONNACK-Roundtrip im Loop-Thread).
    """
    deadline = time.monotonic() + _CLIENT_CONNECT_TIMEOUT_S
    while time.monotonic() < deadline:
        if client.is_connected():
            return
        time.sleep(0.05)
    pytest.fail(f"paho-mqtt-Client-Connect nicht innerhalb {_CLIENT_CONNECT_TIMEOUT_S}s")


def test_mqtt_adapter_roundtrip_against_mosquitto_sibling(
    _mosquitto: DockerContainer,
) -> None:
    """End-to-End-Pfad: Publisher -> Mosquitto -> Adapter-Read,
    und Adapter-Write -> Mosquitto -> Test-Subscriber.

    Beide Pfade laufen ueber denselben Broker-Container; sie
    pruefen die zwei Decision-4d-Halften (Receive-Marshal +
    Publish).
    """
    host = _mosquitto.get_container_host_ip()
    port = int(_mosquitto.get_exposed_port(_MQTT_PORT))
    config = _build_config(host, port)

    received_commands: list[Command] = []

    def _capture_command(
        _client: mqtt.Client, _userdata: object, message: mqtt.MQTTMessage
    ) -> None:
        received_commands.append(decode_command(message.payload))

    subscriber = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="smoke-test-subscriber",
    )
    subscriber.on_message = _capture_command
    subscriber.connect(host, port)
    subscriber.subscribe("grid/test/battery/1/command", qos=1)
    subscriber.loop_start()
    _wait_for_paho_connect(subscriber)

    publisher = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="smoke-test-publisher",
    )
    publisher.connect(host, port)
    publisher.loop_start()
    _wait_for_paho_connect(publisher)

    port_adapter = MqttDeviceProtocolPort(config)
    try:
        port_adapter.start()
        # Subscribe-Pfad: Publisher pusht eine Telemetry-Message.
        point = _sample_telemetry()
        publisher.publish(
            "grid/test/battery/1/telemetry", encode_telemetry(point), qos=1
        ).wait_for_publish(timeout=_POLL_TIMEOUT_S)
        received_point = _poll_for_read(port_adapter, "battery1")
        assert received_point == point

        # Publish-Pfad: Adapter sendet ein Command; Test-Subscriber
        # faengt es ab.
        command = _sample_command()
        port_adapter.write("battery1", command)
        _poll_until(lambda: len(received_commands) >= 1)
        assert received_commands[0].command_id == command.command_id
        assert received_commands[0].target_device_id == command.target_device_id
        assert received_commands[0].result == command.result
    finally:
        port_adapter.stop()
        publisher.loop_stop()
        publisher.disconnect()
        subscriber.loop_stop()
        subscriber.disconnect()


def _poll_for_read(port_adapter: MqttDeviceProtocolPort, target: str) -> TelemetryPoint:
    """Bounded-Poll auf `port.read(target)`; failt nach Timeout."""
    deadline = time.monotonic() + _POLL_TIMEOUT_S
    while time.monotonic() < deadline:
        result = port_adapter.read(target)
        if result is not None:
            return result
        time.sleep(_POLL_INTERVAL_S)
    pytest.fail(
        f"MqttDeviceProtocolPort.read({target!r}) lieferte keinen "
        f"TelemetryPoint innerhalb {_POLL_TIMEOUT_S}s"
    )


def _poll_until(predicate: object) -> None:  # type: ignore[misc]
    """Bounded-Poll auf eine boolean-Bedingung."""
    deadline = time.monotonic() + _POLL_TIMEOUT_S
    while time.monotonic() < deadline:
        if predicate():  # type: ignore[operator]
            return
        time.sleep(_POLL_INTERVAL_S)
    pytest.fail(f"Bedingung nicht erfuellt innerhalb {_POLL_TIMEOUT_S}s")
