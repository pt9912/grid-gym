"""`BessEmsFieldPublishAdapter` — bess-ems-Feldvertrags-Publisher (Slice 077 S2,
ADR 0078).

Aggregiert je Tick grid-gyms per-Punkt-Battery-Telemetrie + Fault-Surface eines
`TickResult` zu den **breiten** bess-ems-Envelope-Frames (`telemetry`/`status`/
`fault`) und published sie an einen MQTT-Broker, damit ein externes, **unveraendertes**
EMS (`bess-ems`, System-under-Test) grid-gym als simuliertes Feld konsumiert (HIL-
Konkretisierung von `GG-TEST-004`). Schreib-Gegenrolle zum schmalen per-Punkt-
`field_publish_mqtt`-Publisher (der unveraendert bleibt).

Anders als `field_publish_mqtt` implementiert dieser Adapter **keinen**
`FieldPublishPort`: die Frame-Aggregation lebt im Driver (`FieldPublishPort` bleibt
per-Punkt, ADR 0075 §2.2 / ADR 0078 §2.1). Der Driver ruft `start()` / `publish_tick()`
je Tick / `stop()`.

**Command-Ack-Echo (ADR 0078 §2.9).** Bei `command_ack_enabled` subscribed der
Adapter `{prefix}/+/command` und published ein Always-Accept-`command_ack` auf
`{prefix}/{asset_id}/command/ack` — **Empfangs-Ack, kein Feldeffekt** (der Sollwert-
Effekt-Pfad bleibt Modbus, ADR 0076/Slice 075). Das haelt bess-ems' `MqttCommandSink`
vom `ack-timeout`→Safe-Stop ab. paho-Callbacks feuern aus dem `loop_start()`-Thread;
`client.publish()` ist thread-safe (paho-Doku).

**Determinismus (ADR 0078 §2.7).** Zustandslose Projektion des `TickResult` — kein
Snapshot-Slot. `dispatched_at` (Ack) ist Wall-Clock (**exogen**, nicht im
Determinismus-Vertrag). Ohne konfigurierten Adapter byte-identisch.

**Simulations-/Testadapter** ([`GG-SAFE-007`], ADR 0078 §2.8): keine produktive
Anlagensteuerung; Broker-Exposure ist Nur-Sim-Netz (keine Auth/TLS).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from decimal import Decimal

import paho.mqtt.client as mqtt

from grid_gym.adapters.driven.field_publish_bess_ems._config import BessEmsFieldPublishConfig
from grid_gym.adapters.driven.field_publish_bess_ems._encoder import (
    BessEmsEncoderMissingMetricError,
    command_id_from_payload,
    encode_command_ack,
    encode_fault,
    encode_status,
    encode_telemetry,
)
from grid_gym.adapters.driven.field_publish_bess_ems._errors import (
    BessEmsFieldPublishConnectError,
    BessEmsFieldPublishDisconnectError,
    BessEmsFieldPublishError,
    BessEmsFieldPublishInvalidAssetIdError,
    BessEmsFieldPublishNotStartedError,
    BessEmsFieldPublishPublishFailedError,
)
from grid_gym.adapters.driven.field_publish_bess_ems.error_translation import safe_callback
from grid_gym.hexagon.core.domain.device import DeviceStatus
from grid_gym.hexagon.core.domain.tick_result import TickResult
from grid_gym.hexagon.core.serialization.canonical import canonical_json

_LOGGER: logging.Logger = logging.getLogger(__name__)

_TOPIC_SPECIALS: tuple[str, ...] = ("/", "+", "#")

# Client-Factory-Hook (Default ruft paho.mqtt.Client; Tests reichen einen Mock
# durch, damit kein echter Broker/Socket noetig ist — Muster `field_publish_mqtt`).
ClientFactory = Callable[[BessEmsFieldPublishConfig], mqtt.Client]
# Wall-Clock-Quelle fuer `command_ack.dispatched_at` (ISO-8601-UTC-String).
# Injizierbar, damit Tests den exogenen Wert pinnen koennen (ADR 0078 §2.9).
NowIsoSource = Callable[[], str]


def _default_client_factory(config: BessEmsFieldPublishConfig) -> mqtt.Client:
    """Default-Client-Factory: paho-mqtt 2.x mit CallbackAPIVersion.VERSION2."""
    return mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # type: ignore[attr-defined]
        client_id=config.client_id,
    )


def _default_now_iso() -> str:
    """Wall-Clock als ISO-8601-UTC-String (`...Z`, Sekunden-Aufloesung, Schema-
    `type: string`). Exogen — geht nicht in den Determinismus-Vertrag ein."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _valid_topic_segment(value: str) -> bool:
    return bool(value) and not any(char in value for char in _TOPIC_SPECIALS)


def _group_metrics_by_device(result: TickResult) -> dict[str, dict[str, Decimal]]:
    """Faltet die flache `emitted_telemetry`-Punktliste zu `device_id → {metric:
    value}` (die Envelope-Aggregations-Quelle, ADR 0078 §2.1)."""
    grouped: dict[str, dict[str, Decimal]] = {}
    for point in result.emitted_telemetry:
        grouped.setdefault(point.device_id, {})[point.metric] = point.value
    return grouped


class BessEmsFieldPublishAdapter:
    """bess-ems-Feldvertrags-Publisher (Simulations-/Testadapter; keine produktive
    Anlagensteuerung).

    Lifecycle idempotent: Doppel-`start()` ist No-op nach erstem erfolgreichem
    Connect; `stop()` nach nicht-erfolgtem `start()` ist No-op.
    """

    def __init__(
        self,
        config: BessEmsFieldPublishConfig,
        *,
        client_factory: ClientFactory | None = None,
        now_iso: NowIsoSource | None = None,
    ) -> None:
        self._config: BessEmsFieldPublishConfig = config
        self._client_factory: ClientFactory = client_factory or _default_client_factory
        self._now_iso: NowIsoSource = now_iso or _default_now_iso
        self._client: mqtt.Client | None = None
        self._started: bool = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Connect zum Broker + (bei `command_ack_enabled`) Subscribe auf
        `{prefix}/+/command` + `loop_start()`. Idempotent."""
        if self._started:
            return
        client = self._client_factory(self._config)
        client.on_message = self._on_message
        client.reconnect_delay_set(min_delay=1, max_delay=30)
        try:
            client.connect(self._config.broker_host, self._config.broker_port)
        except OSError as exc:
            raise BessEmsFieldPublishConnectError(
                self._config.broker_host, self._config.broker_port, exc
            ) from exc
        if self._config.command_ack_enabled:
            client.subscribe(f"{self._config.topic_prefix}/+/command", qos=self._config.qos)
        client.loop_start()
        self._client = client
        self._started = True

    def stop(self) -> None:
        """`disconnect()` VOR `loop_stop()` (graceful drain, Muster
        `field_publish_mqtt`). Idempotent; interner Zustand wird auch bei
        Disconnect-Fehler zurueckgesetzt."""
        if not self._started or self._client is None:
            return
        client = self._client
        self._client = None
        self._started = False
        try:
            client.disconnect()
            client.loop_stop()
        except OSError as exc:
            raise BessEmsFieldPublishDisconnectError(exc) from exc

    # ------------------------------------------------------------------
    # Push-Seite: Tick-Frame-Aggregation (ADR 0078 §2.1/§2.2/§2.3)
    # ------------------------------------------------------------------

    def publish_tick(self, result: TickResult) -> None:
        """Aggregiert `result` zu je Asset einem `telemetry`/`status`/(`fault`)-Frame
        und published sie (ADR 0078 §2.2/§2.3).

        Ein Asset ist jedes fault-surface-faehige Geraet (`result.emitted_device_status`,
        heute Batterien). `offset_millis = result.simulation_time`. `telemetry`/`status`
        retained; `fault` non-retained + unterdrueckt bei `fault_status ∈ {ok, ""}`.
        Fehlt einem Asset ein Envelope-Pflichtfeld, wirft `encode_telemetry`
        fail-fast (`BessEmsEncoderMissingMetricError`, ADR 0078 §2.5).

        **Per-Asset isoliert (Review LOW-2):** ein Frame-Fehler eines Assets (fehlende
        Metrik / Non-Success-rc / ungueltige asset_id) unterdrueckt **nicht** die Frames
        der anderen Assets — insbesondere nicht deren `status`/`fault` (Safe-Stop-E2E,
        S3). Der **erste** Fehler wird nach der Schleife re-raised, damit der Driver den
        Tick als Fehler zaehlt (`_publish_bess_ems`-Degrade)."""
        client = self._client
        if client is None:
            raise BessEmsFieldPublishNotStartedError
        offset_millis = result.simulation_time
        metrics_by_device = _group_metrics_by_device(result)
        first_error: BessEmsEncoderMissingMetricError | BessEmsFieldPublishError | None = None
        for status in result.emitted_device_status:
            try:
                self._publish_asset(client, offset_millis, metrics_by_device, status)
            except (BessEmsEncoderMissingMetricError, BessEmsFieldPublishError) as exc:
                if first_error is None:
                    first_error = exc
        if first_error is not None:
            raise first_error

    def _publish_asset(
        self,
        client: mqtt.Client,
        offset_millis: int,
        metrics_by_device: Mapping[str, Mapping[str, Decimal]],
        status: DeviceStatus,
    ) -> None:
        """Loest asset_id + Metriken eines fault-surface-Geraets auf und published
        dessen drei Envelope-Frames (isoliert je Asset, s. `publish_tick`)."""
        asset_id = self._config.asset_id_for(status.device_id)
        if not _valid_topic_segment(asset_id):
            raise BessEmsFieldPublishInvalidAssetIdError(asset_id)
        metrics = metrics_by_device.get(status.device_id, {})
        self._publish_asset_frames(client, asset_id, offset_millis, metrics, status)

    def _publish_asset_frames(
        self,
        client: mqtt.Client,
        asset_id: str,
        offset_millis: int,
        metrics: Mapping[str, Decimal],
        status: DeviceStatus,
    ) -> None:
        """Baut + published die drei Envelope-Frames eines Assets (ADR 0078 §2.3).

        `status` traegt die Fault-Surface (`available`/`fault_status`); `metrics` die
        per-Punkt-Battery-Emissionen des Assets."""
        prefix = self._config.topic_prefix
        available = status.available
        fault_status = status.fault_status
        telemetry = encode_telemetry(
            asset_id, offset_millis, metrics, available=available, fault_status=fault_status
        )
        self._publish(client, f"{prefix}/{asset_id}/telemetry", telemetry, retain=True)
        status_frame = encode_status(offset_millis, available=available, fault_status=fault_status)
        self._publish(client, f"{prefix}/{asset_id}/status", status_frame, retain=True)
        fault_frame = encode_fault(offset_millis, fault_status=fault_status)
        if fault_frame is not None:
            self._publish(client, f"{prefix}/{asset_id}/fault", fault_frame, retain=False)

    def _publish(
        self,
        client: mqtt.Client,
        topic: str,
        payload: Mapping[str, object],
        *,
        retain: bool,
    ) -> None:
        """Serialisiert `payload` deterministisch (`canonical_json`, kein `float`) und
        published; Non-Success-Returncode → `BessEmsFieldPublishPublishFailedError`."""
        info = client.publish(topic, canonical_json(payload), qos=self._config.qos, retain=retain)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise BessEmsFieldPublishPublishFailedError(topic, info.rc)

    # ------------------------------------------------------------------
    # Command-Ack-Echo (ADR 0078 §2.9) — laeuft im paho-Loop-Thread
    # ------------------------------------------------------------------

    def _on_message(
        self,
        client: mqtt.Client,
        _userdata: object,
        message: mqtt.MQTTMessage,
    ) -> None:
        """paho-`on_message`-Callback (Loop-Thread): Always-Accept-`command_ack`-Echo
        auf `{command-topic}/ack` (ADR 0078 §2.9). Exceptions werden ueber
        `safe_callback` geschluckt + geloggt, damit der Loop-Thread weiterlaeuft
        (Muster `protocol_mqtt`); ein Fremd-/Fehl-Payload fuehrt zu **keinem** Ack.

        Der Ack wird ueber den vom Callback gelieferten `client` publiziert (nicht
        `self._client`) — dieser ist immer der live Client (Review LOW-1: `self._client`
        wird in `start()` erst **nach** `loop_start()` gesetzt, ein Command im
        Startfenster wuerde sonst gedroppt)."""
        safe_callback(
            f"command-ack[topic={message.topic!r}]",
            lambda: self._echo_command_ack(client, message),
            logger=_LOGGER,
        )

    def _echo_command_ack(self, client: mqtt.Client, message: mqtt.MQTTMessage) -> None:
        try:
            payload = json.loads(message.payload)
        except (ValueError, TypeError):
            return
        if not isinstance(payload, Mapping):
            return
        command_id = command_id_from_payload(payload)
        if command_id is None:
            return
        ack = encode_command_ack(command_id, self._now_iso())
        # Ack-Topic = das empfangene `.../command`-Topic + `/ack` (Subscribe war
        # `{prefix}/+/command`, also ist die Form garantiert).
        self._publish(client, f"{message.topic}/ack", ack, retain=False)
