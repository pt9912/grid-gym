"""Callback->Sync-Marshal-Tests (Decision 4d) fuer
`MqttDeviceProtocolPort._on_message`.

Verifiziert:

- Per-Target-Queue-Lazy-Init bei erster Message.
- FIFO-Drain via `read()`.
- Decode-Fehler im Callback werden geschluckt (Loop-Thread
  ueberlebt; siehe ADR 0031 §2.4 Alternative A7).
- Unbekannte Topic-Strings werden ignoriert (kein Crash, kein Queue-
  Eintrag).
- Messages fuer Target A blockieren nicht den Read von Target B
  (Per-Target-Queue-Isolation).
"""

from __future__ import annotations

import logging
from decimal import Decimal
from unittest.mock import MagicMock

import paho.mqtt.client as mqtt
import pytest

from grid_gym.adapters.driven.protocol_mqtt import (
    MqttDeviceProtocolPort,
    MqttProtocolPortConfig,
    MqttTopicConfig,
    encode_telemetry,
)
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint


def _build_config() -> MqttProtocolPortConfig:
    return MqttProtocolPortConfig(
        broker_host="test",
        broker_port=1883,
        client_id="test",
        topics={
            "battery1": MqttTopicConfig(
                telemetry="grid/battery/1/tel",
                command="grid/battery/1/cmd",
            ),
            "pv1": MqttTopicConfig(
                telemetry="grid/pv/1/tel",
            ),
        },
    )


def _make_port() -> MqttDeviceProtocolPort:
    client = MagicMock(spec=mqtt.Client)
    port = MqttDeviceProtocolPort(_build_config(), client_factory=lambda _config: client)
    port.start()
    return port


def _make_message(topic: str, payload: bytes) -> mqtt.MQTTMessage:
    msg = MagicMock(spec=mqtt.MQTTMessage)
    msg.topic = topic
    msg.payload = payload
    return msg


def _sample_telemetry_for(device_id: str, value: Decimal) -> TelemetryPoint:
    return TelemetryPoint(
        run_id="run-1",
        tick=0,
        simulation_time=0,
        device_id=device_id,
        metric="power_kw",
        value=value,
        unit="kW",
        quality=Quality.VALID,
        source=device_id,
        sequence=0,
    )


def test_on_message_enqueues_decoded_telemetry_for_known_topic() -> None:
    port = _make_port()
    point = _sample_telemetry_for("battery1", Decimal("5.0"))
    payload = encode_telemetry(point)
    port._on_message(MagicMock(), None, _make_message("grid/battery/1/tel", payload))
    drained = port.read("battery1")
    assert drained == point


def test_on_message_ignores_unknown_topic_without_crash() -> None:
    port = _make_port()
    port._on_message(MagicMock(), None, _make_message("totally/unknown/topic", b'{"bad":"data"}'))
    # Kein Crash, keine Queue-Mutation fuer registrierte Targets.
    assert port.read("battery1") is None
    assert port.read("pv1") is None


def test_on_message_swallows_decode_errors_via_safe_callback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    port = _make_port()
    bad_payload = b"not-json-bytes"
    with caplog.at_level(logging.ERROR):
        port._on_message(MagicMock(), None, _make_message("grid/battery/1/tel", bad_payload))
    # Kein Crash. Queue bleibt leer.
    assert port.read("battery1") is None
    # Log enthaelt eine Error-Message.
    assert any("MQTT-Callback" in record.getMessage() for record in caplog.records)


def test_per_target_queues_are_isolated() -> None:
    port = _make_port()
    bat_point = _sample_telemetry_for("battery1", Decimal("1.0"))
    pv_point = _sample_telemetry_for("pv1", Decimal("2.0"))
    port._on_message(
        MagicMock(), None, _make_message("grid/battery/1/tel", encode_telemetry(bat_point))
    )
    port._on_message(MagicMock(), None, _make_message("grid/pv/1/tel", encode_telemetry(pv_point)))
    # Read in reverse order — Per-Target-Queues sind unabhaengig.
    assert port.read("pv1") == pv_point
    assert port.read("battery1") == bat_point


def test_per_target_queues_drain_in_fifo_order() -> None:
    port = _make_port()
    p1 = _sample_telemetry_for("battery1", Decimal("1.0"))
    p2 = _sample_telemetry_for("battery1", Decimal("2.0"))
    p3 = _sample_telemetry_for("battery1", Decimal("3.0"))
    for point in (p1, p2, p3):
        port._on_message(
            MagicMock(),
            None,
            _make_message("grid/battery/1/tel", encode_telemetry(point)),
        )
    assert port.read("battery1") == p1
    assert port.read("battery1") == p2
    assert port.read("battery1") == p3
    assert port.read("battery1") is None  # Queue erschoepft


def test_lazy_init_skips_queue_creation_when_no_message_received() -> None:
    """Decision 4d: Queues entstehen erst beim ersten `on_message`,
    nicht beim `start()`. Vor der ersten Message ist `_queues` leer
    fuer alle Targets — `read()` liefert `None` ohne KeyError."""
    port = _make_port()
    # Kein Message — Queue-Dict bleibt leer.
    assert port._queues == {}
    # `read()` liefert trotzdem `None` (Decision 4d-`get(target)`-Pfad).
    assert port.read("battery1") is None
    assert port.read("pv1") is None
