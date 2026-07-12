"""Integration-Smoke fuer den MQTT-Field-Publish-Adapter (ADR 0075 §2.1,
Slice 073 C4).

`MqttFieldPublishAdapter` -> Mosquitto-Sibling -> Test-Subscriber
(`bess-ems`-Platzhalter). Beweist den Kern-Anspruch der Field-Server-
Push-Seite: **ein externer MQTT-Konsument empfaengt grid-gyms exponierte
(simulierte) Telemetrie.** Mosquitto-Sibling via testcontainers-
`DockerContainer` (Pattern aus `test_mqtt_compose_smoke.py` — kein
DockerCompose, weil der `test-runner` kein `docker`-CLI hat).

Cross-Cutting (Lastenheft Z. 1161-1163): Test-Infrastruktur; **keine
produktive Anlagensteuerung** (Nur-Sim-Netz, kein Auth/TLS).
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from dataclasses import replace
from decimal import Decimal
from typing import Final

import paho.mqtt.client as mqtt
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from grid_gym.adapters.driven.field_publish_mqtt import (
    MqttFieldPublishAdapter,
    MqttFieldPublishConfig,
)
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint

_MQTT_PORT: Final[int] = 1883
_MOSQUITTO_IMAGE: Final[str] = "eclipse-mosquitto:2"
_READY_LOG: Final[str] = "mosquitto version"
_BROKER_READY_TIMEOUT_S: Final[float] = 30.0
_POLL_TIMEOUT_S: Final[float] = 5.0
_POLL_INTERVAL_S: Final[float] = 0.1
_CLIENT_CONNECT_TIMEOUT_S: Final[float] = 5.0
_TOPIC_PREFIX: Final[str] = "grid-gym/telemetry"
_MOSQUITTO_CONFIG: Final[str] = "listener 1883\nallow_anonymous true\npersistence false\n"


@pytest.fixture(scope="module")
def _mosquitto() -> Iterator[DockerContainer]:
    """Mosquitto-Sibling fuers Modul (anonymer Zugriff frei, Persistence off)."""
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


def _sample_point() -> TelemetryPoint:
    return TelemetryPoint(
        run_id="fp-smoke-1",
        tick=2,
        simulation_time=2000,
        device_id="meter-1",
        metric="voltage_v",
        value=Decimal("230.5"),
        unit="V",
        quality=Quality.VALID,
        source="smart_meter.meter-1",
        sequence=4,
    )


def _wait_for_paho_connect(client: mqtt.Client) -> None:
    deadline = time.monotonic() + _CLIENT_CONNECT_TIMEOUT_S
    while time.monotonic() < deadline:
        if client.is_connected():
            return
        time.sleep(0.05)
    pytest.fail(f"paho-mqtt-Client-Connect nicht innerhalb {_CLIENT_CONNECT_TIMEOUT_S}s")


def _poll_until(predicate: object) -> None:  # type: ignore[misc]
    deadline = time.monotonic() + _POLL_TIMEOUT_S
    while time.monotonic() < deadline:
        if predicate():  # type: ignore[operator]
            return
        time.sleep(_POLL_INTERVAL_S)
    pytest.fail(f"Bedingung nicht erfuellt innerhalb {_POLL_TIMEOUT_S}s")


def test_field_publish_reaches_external_subscriber(_mosquitto: DockerContainer) -> None:
    """MqttFieldPublishAdapter.publish(point) -> Broker -> Subscriber empfaengt
    die kanonisch serialisierte Telemetrie (`Decimal`-Fidelity)."""
    host = _mosquitto.get_container_host_ip()
    port = int(_mosquitto.get_exposed_port(_MQTT_PORT))

    received: list[mqtt.MQTTMessage] = []

    def _capture(_client: mqtt.Client, _userdata: object, message: mqtt.MQTTMessage) -> None:
        received.append(message)

    # Der externe Subscriber ist der `bess-ems`-Platzhalter.
    subscriber = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="fp-smoke-subscriber",
    )
    subscriber.on_message = _capture
    subscriber.connect(host, port)
    subscriber.subscribe(f"{_TOPIC_PREFIX}/#", qos=0)
    subscriber.loop_start()
    _wait_for_paho_connect(subscriber)

    adapter = MqttFieldPublishAdapter(
        MqttFieldPublishConfig(
            broker_host=host,
            broker_port=port,
            client_id="grid-gym-field-publish-smoke",
            topic_prefix=_TOPIC_PREFIX,
        )
    )
    point1 = _sample_point()
    point2 = replace(
        _sample_point(),
        device_id="meter-2",
        metric="current_a",
        value=Decimal("11.25"),
        unit="A",
        sequence=5,
    )
    try:
        adapter.start()
        adapter.publish(point1)
        adapter.publish(point2)
        _poll_until(lambda: len(received) >= 2)
    finally:
        adapter.stop()
        subscriber.loop_stop()
        subscriber.disconnect()

    by_topic = {m.topic: m for m in received}
    # Beide Punkte auf ihren eigenen `{prefix}/{device_id}/{metric}`-Topics.
    assert set(by_topic) == {
        f"{_TOPIC_PREFIX}/meter-1/voltage_v",
        f"{_TOPIC_PREFIX}/meter-2/current_a",
    }
    # QoS des Publish (Config-Default 0).
    assert all(m.qos == 0 for m in received)
    # Alle 10 `GG-DATA-001`-Felder + `Decimal`-Fidelity ueber den ganzen Pfad
    # (canonical_json -> Broker -> Decode mit parse_float=Decimal).
    decoded = json.loads(
        by_topic[f"{_TOPIC_PREFIX}/meter-1/voltage_v"].payload, parse_float=Decimal
    )
    assert decoded == {
        "run_id": "fp-smoke-1",
        "tick": 2,
        "simulation_time": 2000,
        "device_id": "meter-1",
        "metric": "voltage_v",
        "value": Decimal("230.5"),
        "unit": "V",
        "quality": Quality.VALID.value,
        "source": "smart_meter.meter-1",
        "sequence": 4,
    }
