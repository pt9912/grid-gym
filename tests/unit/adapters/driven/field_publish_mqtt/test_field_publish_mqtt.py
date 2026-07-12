"""Unit-Tests fuer `MqttFieldPublishAdapter` (ADR 0075 §2.1).

Fake-paho-Client via `client_factory`-Injektion — kein echter Broker/Socket.
Muster analog `protocol_mqtt`-Tests.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import cast

import paho.mqtt.client as mqtt
import pytest

from grid_gym.adapters.driven.field_publish_mqtt import (
    MqttFieldPublishAdapter,
    MqttFieldPublishConfig,
    MqttFieldPublishConfigEmptyFieldError,
    MqttFieldPublishConfigError,
    MqttFieldPublishConfigInvalidPortError,
    MqttFieldPublishConfigInvalidQosError,
    MqttFieldPublishConnectError,
    MqttFieldPublishDisconnectError,
    MqttFieldPublishNotStartedError,
    MqttFieldPublishPublishFailedError,
)
from grid_gym.adapters.driven.field_publish_mqtt._adapter import _default_client_factory
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.field_publish import (
    FieldPublishPort,
    FieldPublishPortPublishError,
    FieldPublishPortStartError,
    FieldPublishPortStopError,
)


@dataclass
class _FakeInfo:
    rc: int


class _FakeClient:
    """Recording-Fake fuer den paho-`Client` (nur die vom Adapter
    genutzten Methoden)."""

    def __init__(
        self,
        *,
        connect_raises: bool = False,
        publish_rc: int = mqtt.MQTT_ERR_SUCCESS,
        disconnect_raises: bool = False,
    ) -> None:
        self.connect_calls: list[tuple[str, int]] = []
        self.loop_start_calls: int = 0
        self.loop_stop_calls: int = 0
        self.disconnect_calls: int = 0
        self.published: list[tuple[str, bytes, int]] = []
        self._connect_raises = connect_raises
        self._publish_rc = publish_rc
        self._disconnect_raises = disconnect_raises

    def connect(self, host: str, port: int) -> None:
        self.connect_calls.append((host, port))
        if self._connect_raises:
            raise OSError("connection refused")

    def loop_start(self) -> None:
        self.loop_start_calls += 1

    def publish(self, topic: str, payload: bytes, qos: int) -> _FakeInfo:
        self.published.append((topic, payload, qos))
        return _FakeInfo(self._publish_rc)

    def loop_stop(self) -> None:
        self.loop_stop_calls += 1

    def disconnect(self) -> None:
        self.disconnect_calls += 1
        if self._disconnect_raises:
            raise OSError("disconnect boom")


def _config(**overrides: object) -> MqttFieldPublishConfig:
    params: dict[str, object] = {
        "broker_host": "localhost",
        "broker_port": 1883,
        "client_id": "grid-gym-field-publish",
        "topic_prefix": "grid-gym/telemetry",
        "qos": 0,
    }
    params.update(overrides)
    return MqttFieldPublishConfig(**params)  # type: ignore[arg-type]


def _point() -> TelemetryPoint:
    return TelemetryPoint(
        run_id="run-1",
        tick=3,
        simulation_time=3000,
        device_id="meter-1",
        metric="voltage_v",
        value=Decimal("230.5"),
        unit="V",
        quality=Quality.VALID,
        source="smart_meter.meter-1",
        sequence=7,
    )


def _adapter_with(fake: _FakeClient) -> MqttFieldPublishAdapter:
    return MqttFieldPublishAdapter(
        _config(),
        client_factory=lambda _cfg: cast(mqtt.Client, fake),
    )


def test_adapter_satisfies_field_publish_port_protocol() -> None:
    assert isinstance(_adapter_with(_FakeClient()), FieldPublishPort)


def test_start_connects_and_loop_starts() -> None:
    fake = _FakeClient()
    adapter = _adapter_with(fake)
    adapter.start()
    assert fake.connect_calls == [("localhost", 1883)]
    assert fake.loop_start_calls == 1


def test_start_is_idempotent() -> None:
    fake = _FakeClient()
    adapter = _adapter_with(fake)
    adapter.start()
    adapter.start()
    assert len(fake.connect_calls) == 1
    assert fake.loop_start_calls == 1


def test_start_connect_failure_raises_typed_start_error() -> None:
    fake = _FakeClient(connect_raises=True)
    adapter = _adapter_with(fake)
    with pytest.raises(MqttFieldPublishConnectError) as excinfo:
        adapter.start()
    # Adapter-Fehler ist ein FieldPublishPort-Vertragsfehler.
    assert isinstance(excinfo.value, FieldPublishPortStartError)
    assert excinfo.value.broker_host == "localhost"
    assert excinfo.value.broker_port == 1883


def test_publish_builds_topic_and_deterministic_payload() -> None:
    fake = _FakeClient()
    adapter = _adapter_with(fake)
    adapter.start()
    point = _point()
    adapter.publish(point)
    assert len(fake.published) == 1
    topic, payload, qos = fake.published[0]
    assert topic == "grid-gym/telemetry/meter-1/voltage_v"
    assert qos == 0
    decoded = json.loads(payload, parse_float=Decimal)
    # Decimal fliesst kanonisch (Fixed-Point) — volle Fidelity, kein
    # float-Cast (ADR 0075 §2.1); parse_float=Decimal beim Decode.
    assert decoded["value"] == Decimal("230.5")
    assert decoded["quality"] == Quality.VALID.value
    assert decoded["device_id"] == "meter-1"
    assert decoded["metric"] == "voltage_v"
    assert decoded["simulation_time"] == 3000
    assert decoded["sequence"] == 7


def test_publish_before_start_raises_not_started() -> None:
    adapter = _adapter_with(_FakeClient())
    with pytest.raises(MqttFieldPublishNotStartedError) as excinfo:
        adapter.publish(_point())
    assert isinstance(excinfo.value, FieldPublishPortPublishError)


def test_publish_non_success_rc_raises_publish_failed() -> None:
    fake = _FakeClient(publish_rc=mqtt.MQTT_ERR_NO_CONN)
    adapter = _adapter_with(fake)
    adapter.start()
    with pytest.raises(MqttFieldPublishPublishFailedError) as excinfo:
        adapter.publish(_point())
    assert excinfo.value.topic == "grid-gym/telemetry/meter-1/voltage_v"
    assert excinfo.value.rc == mqtt.MQTT_ERR_NO_CONN


def test_stop_noop_before_start() -> None:
    fake = _FakeClient()
    adapter = _adapter_with(fake)
    adapter.stop()  # kein start() → No-op
    assert fake.loop_stop_calls == 0
    assert fake.disconnect_calls == 0


def test_stop_loop_stops_and_disconnects_idempotent() -> None:
    fake = _FakeClient()
    adapter = _adapter_with(fake)
    adapter.start()
    adapter.stop()
    adapter.stop()  # zweiter Stop → No-op
    assert fake.loop_stop_calls == 1
    assert fake.disconnect_calls == 1
    # publish nach stop → not-started
    with pytest.raises(MqttFieldPublishNotStartedError):
        adapter.publish(_point())


def test_stop_disconnect_failure_raises_typed_stop_error_but_resets_state() -> None:
    fake = _FakeClient(disconnect_raises=True)
    adapter = _adapter_with(fake)
    adapter.start()
    with pytest.raises(MqttFieldPublishDisconnectError) as excinfo:
        adapter.stop()
    assert isinstance(excinfo.value, FieldPublishPortStopError)
    # State ist trotz Fehler zurueckgesetzt (Best-Effort-Cleanup).
    with pytest.raises(MqttFieldPublishNotStartedError):
        adapter.publish(_point())


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"broker_host": ""}, MqttFieldPublishConfigEmptyFieldError),
        ({"client_id": ""}, MqttFieldPublishConfigEmptyFieldError),
        ({"topic_prefix": ""}, MqttFieldPublishConfigEmptyFieldError),
        ({"broker_port": 0}, MqttFieldPublishConfigInvalidPortError),
        ({"broker_port": 70000}, MqttFieldPublishConfigInvalidPortError),
        ({"qos": 3}, MqttFieldPublishConfigInvalidQosError),
    ],
)
def test_config_validation_rejects_bad_values(
    overrides: dict[str, object],
    expected: type[MqttFieldPublishConfigError],
) -> None:
    with pytest.raises(expected):
        _config(**overrides)


def test_default_client_factory_builds_paho_client() -> None:
    """Deckt die Default-Factory (kein Connect — nur Konstruktion)."""
    client = _default_client_factory(_config())
    assert isinstance(client, mqtt.Client)
