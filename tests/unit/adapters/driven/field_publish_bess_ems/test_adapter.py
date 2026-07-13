"""Unit-Tests fuer `BessEmsFieldPublishAdapter` (Slice 077 S2, ADR 0078).

Fake-paho-Client via `client_factory`-Injektion (kein echter Broker/Socket, Muster
`field_publish_mqtt`). Pinnt: Lifecycle (connect/subscribe/loop), Tick-Aggregation
(telemetry/status/fault-Topics + Retain + Suppression), `device_id→asset_id`-Mapping,
fail-fast (NotStarted / fehlende Metrik / Non-Success-rc) und das `command_ack`-Echo.
Werte-Korrektheit (Flip/derive) deckt `test_encoder`; hier zaehlt der Publish-Vertrag.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import cast

import paho.mqtt.client as mqtt
import pytest

from grid_gym.adapters.driven.field_publish_bess_ems import (
    BessEmsEncoderMissingMetricError,
    BessEmsFieldPublishAdapter,
    BessEmsFieldPublishConfig,
    BessEmsFieldPublishInvalidAssetIdError,
    BessEmsFieldPublishNotStartedError,
    BessEmsFieldPublishPublishFailedError,
)
from grid_gym.hexagon.core.domain.device import DeviceStatus
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.domain.tick_result import TickResult

_ISO = "2026-07-13T10:00:00Z"

_METRIC_VALUES: dict[str, Decimal] = {
    "soc_pct": Decimal("60.500000"),
    "power_kw": Decimal("250.000000"),
    "dc_voltage": Decimal("800.000000"),
    "soh_percent": Decimal("99.000000"),
    "reactive_power_kvar": Decimal("0.000000"),
    "temperature_celsius": Decimal("22.000000"),
}


@dataclass
class _FakeInfo:
    rc: int


@dataclass
class _FakeMessage:
    topic: str
    payload: bytes


class _FakeClient:
    """Recording-Fake fuer den paho-`Client` (nur die vom Adapter genutzten Member)."""

    def __init__(self, *, publish_rc: int = mqtt.MQTT_ERR_SUCCESS) -> None:
        self.connect_calls: list[tuple[str, int]] = []
        self.subscriptions: list[tuple[str, int]] = []
        self.published: list[tuple[str, bytes, int, bool]] = []
        self.loop_start_calls: int = 0
        self.loop_stop_calls: int = 0
        self.disconnect_calls: int = 0
        self.on_message: object = None
        self._publish_rc = publish_rc

    def reconnect_delay_set(self, *, min_delay: int, max_delay: int) -> None:
        self.reconnect_delay = (min_delay, max_delay)

    def connect(self, host: str, port: int) -> None:
        self.connect_calls.append((host, port))

    def subscribe(self, topic: str, *, qos: int) -> None:
        self.subscriptions.append((topic, qos))

    def loop_start(self) -> None:
        self.loop_start_calls += 1

    def publish(self, topic: str, payload: bytes, *, qos: int, retain: bool) -> _FakeInfo:
        self.published.append((topic, payload, qos, retain))
        return _FakeInfo(self._publish_rc)

    def loop_stop(self) -> None:
        self.loop_stop_calls += 1

    def disconnect(self) -> None:
        self.disconnect_calls += 1


def _config(**overrides: object) -> BessEmsFieldPublishConfig:
    params: dict[str, object] = {
        "broker_host": "localhost",
        "broker_port": 1883,
        "client_id": "grid-gym-bess-ems",
    }
    params.update(overrides)
    return BessEmsFieldPublishConfig(**params)  # type: ignore[arg-type]


def _adapter(fake: _FakeClient, **cfg: object) -> BessEmsFieldPublishAdapter:
    return BessEmsFieldPublishAdapter(
        _config(**cfg),
        client_factory=lambda _c: cast(mqtt.Client, fake),
        now_iso=lambda: _ISO,
    )


def _points(device_id: str, *, drop: str | None = None) -> tuple[TelemetryPoint, ...]:
    return tuple(
        TelemetryPoint(
            run_id="run-1",
            tick=1,
            simulation_time=1000,
            device_id=device_id,
            metric=metric,
            value=value,
            unit="",
            quality=Quality.VALID,
            source=f"battery.{device_id}",
            sequence=idx,
        )
        for idx, (metric, value) in enumerate(_METRIC_VALUES.items())
        if metric != drop
    )


def _tick_result(
    *,
    device_id: str = "battery-1",
    available: bool = True,
    fault_status: str = "ok",
    drop: str | None = None,
) -> TickResult:
    return TickResult(
        tick=1,
        simulation_time=1000,
        popped_events=(),
        emitted_telemetry=_points(device_id, drop=drop),
        emitted_device_status=(
            DeviceStatus(device_id=device_id, available=available, fault_status=fault_status),
        ),
    )


def _topics(fake: _FakeClient) -> list[str]:
    return [topic for topic, _payload, _qos, _retain in fake.published]


def _payload_for(fake: _FakeClient, topic: str) -> dict[str, object]:
    for pub_topic, payload, _qos, _retain in fake.published:
        if pub_topic == topic:
            return json.loads(payload)
    raise AssertionError(f"kein Publish auf {topic!r}")


# --- Lifecycle --------------------------------------------------------------


def test_start_connects_subscribes_command_and_loops() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake)
    adapter.start()
    assert fake.connect_calls == [("localhost", 1883)]
    assert fake.subscriptions == [("battery/+/command", 0)]
    assert fake.loop_start_calls == 1
    assert fake.on_message is not None


def test_start_is_idempotent() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake)
    adapter.start()
    adapter.start()
    assert fake.loop_start_calls == 1


def test_command_ack_disabled_skips_subscribe() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake, command_ack_enabled=False)
    adapter.start()
    assert fake.subscriptions == []


def test_stop_disconnects_then_loop_stops_idempotent() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake)
    adapter.start()
    adapter.stop()
    adapter.stop()
    assert (fake.disconnect_calls, fake.loop_stop_calls) == (1, 1)


# --- Tick-Aggregation -------------------------------------------------------


def test_publish_tick_emits_telemetry_and_status_retained() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake)
    adapter.start()
    adapter.publish_tick(_tick_result())
    by_topic = {topic: retain for topic, _p, _q, retain in fake.published}
    assert by_topic == {
        "battery/battery-1/telemetry": True,
        "battery/battery-1/status": True,
    }
    telemetry = _payload_for(fake, "battery/battery-1/telemetry")
    assert set(telemetry.keys()) == {
        "offset_millis",
        "soc_percent",
        "soh_percent",
        "active_power_kw",
        "reactive_power_kvar",
        "dc_voltage",
        "dc_current",
        "temperature_celsius",
        "available",
        "fault_status",
    }
    assert telemetry["offset_millis"] == 1000


def test_fault_topic_suppressed_when_ok() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake)
    adapter.start()
    adapter.publish_tick(_tick_result(fault_status="ok"))
    assert "battery/battery-1/fault" not in _topics(fake)


def test_fault_topic_emitted_non_retained_on_active_fault() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake)
    adapter.start()
    adapter.publish_tick(_tick_result(available=False, fault_status="cell_failure"))
    fault_pubs = [
        (topic, retain)
        for topic, _p, _q, retain in fake.published
        if topic == "battery/battery-1/fault"
    ]
    assert fault_pubs == [("battery/battery-1/fault", False)]
    assert _payload_for(fake, "battery/battery-1/fault") == {
        "fault_status": "cell_failure",
        "offset_millis": 1000,
    }


def test_asset_id_mapping_renames_topic() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake, asset_id_by_device_id={"battery-1": "asset-7"})
    adapter.start()
    adapter.publish_tick(_tick_result())
    assert "battery/asset-7/telemetry" in _topics(fake)
    assert "battery/battery-1/telemetry" not in _topics(fake)


def test_publish_tick_before_start_raises() -> None:
    adapter = _adapter(_FakeClient())
    with pytest.raises(BessEmsFieldPublishNotStartedError):
        adapter.publish_tick(_tick_result())


def test_missing_required_metric_fails_fast() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake)
    adapter.start()
    with pytest.raises(BessEmsEncoderMissingMetricError):
        adapter.publish_tick(_tick_result(drop="dc_voltage"))


def test_non_success_publish_rc_raises() -> None:
    fake = _FakeClient(publish_rc=mqtt.MQTT_ERR_NO_CONN)
    adapter = _adapter(fake)
    adapter.start()
    with pytest.raises(BessEmsFieldPublishPublishFailedError):
        adapter.publish_tick(_tick_result())


def test_invalid_asset_id_segment_raises() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake, asset_id_by_device_id={})
    adapter.start()
    # device_id mit MQTT-Sonderzeichen → Identitaets-asset_id ungueltig.
    with pytest.raises(BessEmsFieldPublishInvalidAssetIdError):
        adapter.publish_tick(_tick_result(device_id="battery/1"))


def test_non_fault_surface_devices_are_not_published() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake)
    adapter.start()
    # emitted_device_status leer (kein fault-surface-Geraet) → kein Publish.
    result = TickResult(
        tick=1,
        simulation_time=1000,
        popped_events=(),
        emitted_telemetry=_points("load-1"),
    )
    adapter.publish_tick(result)
    assert fake.published == []


def test_one_asset_failure_does_not_suppress_siblings() -> None:
    # Review LOW-2: battery-2 (fehlende Metrik) darf battery-1 (danach gelistet) nicht
    # unterdruecken; der Fehler wird trotzdem re-raised (Driver-Degrade-Signal).
    fake = _FakeClient()
    adapter = _adapter(fake)
    adapter.start()
    result = TickResult(
        tick=1,
        simulation_time=1000,
        popped_events=(),
        emitted_telemetry=_points("battery-2", drop="dc_voltage") + _points("battery-1"),
        emitted_device_status=(
            DeviceStatus(device_id="battery-2", available=True, fault_status="ok"),
            DeviceStatus(device_id="battery-1", available=True, fault_status="ok"),
        ),
    )
    with pytest.raises(BessEmsEncoderMissingMetricError):
        adapter.publish_tick(result)
    assert "battery/battery-1/telemetry" in _topics(fake)  # gesundes Geschwister publiziert
    assert "battery/battery-2/telemetry" not in _topics(fake)  # fehlerhaftes Asset nicht


# --- command_ack-Echo (ADR 0078 §2.9) --------------------------------------


def test_on_message_echoes_command_ack() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake)
    adapter.start()
    message = _FakeMessage(
        topic="battery/asset-1/command",
        payload=json.dumps({"command_id": "cmd-42", "active_power_kw": 10}).encode(),
    )
    adapter._on_message(cast(mqtt.Client, fake), None, cast(mqtt.MQTTMessage, message))
    ack = _payload_for(fake, "battery/asset-1/command/ack")
    assert ack == {
        "command_id": "cmd-42",
        "accepted": True,
        "dispatched_at": _ISO,
        "reason": "accepted",
    }
    ack_pub = next(p for p in fake.published if p[0] == "battery/asset-1/command/ack")
    assert ack_pub[3] is False  # non-retained


def test_command_ack_uses_callback_client_before_self_client_assigned() -> None:
    # Review LOW-1: der Ack wird ueber den Callback-Client publiziert, nicht
    # `self._client` — ein Command im Startfenster (self._client noch None) wird
    # trotzdem beantwortet, nicht gedroppt.
    fake = _FakeClient()
    adapter = _adapter(fake)  # NICHT gestartet → self._client is None
    message = _FakeMessage(
        topic="battery/asset-1/command",
        payload=json.dumps({"command_id": "cmd-early"}).encode(),
    )
    adapter._on_message(cast(mqtt.Client, fake), None, cast(mqtt.MQTTMessage, message))
    ack = _payload_for(fake, "battery/asset-1/command/ack")
    assert ack["command_id"] == "cmd-early"


def test_on_message_ignores_payload_without_command_id() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake)
    adapter.start()
    message = _FakeMessage(topic="battery/asset-1/command", payload=b'{"active_power_kw": 10}')
    adapter._on_message(cast(mqtt.Client, fake), None, cast(mqtt.MQTTMessage, message))
    assert fake.published == []


def test_on_message_swallows_malformed_json() -> None:
    fake = _FakeClient()
    adapter = _adapter(fake)
    adapter.start()
    message = _FakeMessage(topic="battery/asset-1/command", payload=b"not-json{")
    # kein Raise (Loop-Thread-Robustheit), kein Ack.
    adapter._on_message(cast(mqtt.Client, fake), None, cast(mqtt.MQTTMessage, message))
    assert fake.published == []
