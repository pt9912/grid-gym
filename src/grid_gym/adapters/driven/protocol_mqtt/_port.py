"""`MqttDeviceProtocolPort` — MQTT-Adapter als
`DeviceProtocolPort`-Implementer (M4 Welle 2, ADR 0031).

Sync-Surface (ADR 0030 §2.1) gegen die asynchrone paho-mqtt-Client-
Library: paho-mqtt laeuft per `loop_start()` in einem internen
Thread, Callbacks (`on_message`) feuern aus diesem Thread. Decision
4d (ADR 0031 §2.4) marshallt vom Callback-Thread auf die Sync-
Surface via Per-Target `queue.Queue`.

Simulations-/Testadapter (Lastenheft Z. 1161-1163); **keine
produktive Anlagensteuerung**.
"""

from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING

import paho.mqtt.client as mqtt

from grid_gym.adapters.driven.protocol_mqtt._codec import (
    decode_telemetry,
    encode_command,
)
from grid_gym.adapters.driven.protocol_mqtt._config import (
    MqttProtocolPortConfig,
    MqttTopicConfig,
)
from grid_gym.adapters.driven.protocol_mqtt._errors import (
    MqttPortConnectError,
    MqttPortDisconnectError,
    MqttPortNoCommandTopicError,
    MqttPortNotStartedError,
    MqttPortPublishFailedError,
)
from grid_gym.adapters.driven.protocol_mqtt._topic_resolver import (
    build_telemetry_topic_index,
    collect_subscribe_topics,
)
from grid_gym.adapters.driven.protocol_mqtt.error_translation import safe_callback
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPortUnknownTargetError,
)

if TYPE_CHECKING:
    from paho.mqtt.client import MQTTMessage

_LOGGER: logging.Logger = logging.getLogger(__name__)


# Type-Alias fuer den Client-Factory-Hook (Default ruft paho.mqtt.Client
# mit Welle-2-API-Version 2; Tests reichen einen Mock durch).
ClientFactory = Callable[[MqttProtocolPortConfig], mqtt.Client]


def _default_client_factory(config: MqttProtocolPortConfig) -> mqtt.Client:
    """Default-Client-Factory: paho-mqtt 2.x mit CallbackAPIVersion.VERSION2.

    Trennt das Konstruktor-Detail vom Adapter-Pfad, damit Tests den
    Client mocken koennen, ohne die Welle-2-Default-Wahl zu
    duplizieren.
    """
    return mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # type: ignore[attr-defined]
        client_id=config.client_id,
    )


class MqttDeviceProtocolPort:
    """MQTT-Adapter (Simulations-/Testadapter; keine produktive
    Anlagensteuerung).

    Implementiert `DeviceProtocolPort` (ADR 0030 §2.1). Per-Target
    `queue.Queue` (Decision 4d) marshallt vom paho-Loop-Thread auf
    die Sync-`read()`-Surface. `write()` ruft `client.publish()`
    direkt (thread-safe per paho-mqtt-Doku).

    Lifecycle ist idempotent: Doppel-`start()` ist No-op nach erstem
    erfolgreichem Connect; `stop()` nach erfolglosem `start()` ist
    No-op.
    """

    def __init__(
        self,
        config: MqttProtocolPortConfig,
        *,
        client_factory: ClientFactory | None = None,
    ) -> None:
        self._config: MqttProtocolPortConfig = config
        self._client_factory: ClientFactory = client_factory or _default_client_factory
        self._client: mqtt.Client | None = None
        # Per-Target `queue.Queue` (Decision 4d). Mutation der Dict-Struktur
        # passiert nur im Callback-Thread (Lazy-Init in `_on_message`);
        # `read()` liest nur den Pointer aus dem Dict. Trotzdem schuetzen
        # wir die Dict-Mutation per Lock — andernfalls koennte eine
        # konkurrente `_topic_index`-Rebuild-Operation (Welle-3+-Folge)
        # den Dict-Zustand inkonsistent sehen.
        self._queues: dict[str, queue.Queue[TelemetryPoint]] = {}
        self._queues_lock: threading.Lock = threading.Lock()
        self._topic_to_device: Mapping[str, str] = build_telemetry_topic_index(config)
        self._started: bool = False

    # ------------------------------------------------------------------
    # `DeviceProtocolPort`-Surface (ADR 0030 §2.1)
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Connect zum Broker + Subscribe auf alle Telemetry-Topics.

        Idempotent: nach erstem erfolgreichem `start()` ist ein
        weiterer Aufruf No-op (Welle-2-Wahl; Pattern analog
        OtlpAdapterBundle).
        """
        if self._started:
            return
        client = self._client_factory(self._config)
        client.on_message = self._on_message
        try:
            client.connect(self._config.broker_host, self._config.broker_port)
        except OSError as exc:
            raise MqttPortConnectError(
                self._config.broker_host, self._config.broker_port, exc
            ) from exc
        for topic, qos in collect_subscribe_topics(self._config):
            client.subscribe(topic, qos=qos)
        client.loop_start()
        self._client = client
        self._started = True

    def stop(self) -> None:
        """Loop-Stop + Disconnect. Idempotent — Doppel-Stop ist No-op.

        Exceptions aus `loop_stop()` / `disconnect()` werden in einen
        typed `DeviceProtocolPortStopError` umgemantelt, aber der
        interne Zustand wird **trotzdem** zurueckgesetzt (Pattern
        analog TickLoop-Best-Effort-Cleanup aus ADR 0030 §2.2).
        """
        if not self._started or self._client is None:
            return
        client = self._client
        self._client = None
        self._started = False
        try:
            client.loop_stop()
            client.disconnect()
        except OSError as exc:
            raise MqttPortDisconnectError(exc) from exc

    def read(self, target: str) -> TelemetryPoint | None:
        """Zieht nicht-blockierend aus der Per-Target-Queue (Decision 4d).

        Liefert `None` wenn (a) das Target im Adapter-Profil registriert
        ist aber noch keine Message ankam (Subscribe ohne Empfang) oder
        (b) die Queue-Hashtable-Lazy-Init noch nicht ausgeloest wurde.

        Wirft `DeviceProtocolPortUnknownTargetError`, wenn das Target
        gar nicht im Profil ist (Pre-Dispatch-Pflichtcheck per
        ADR 0030 §2.1).
        """
        self._assert_known_target(target)
        with self._queues_lock:
            q = self._queues.get(target)
        if q is None:
            return None
        try:
            return q.get_nowait()
        except queue.Empty:
            return None

    def write(self, target: str, command: Command) -> None:
        """Serialisiert `command` und publisht auf das Command-Topic.

        Wirft:

        - `DeviceProtocolPortUnknownTargetError` wenn Target nicht
          im Profil.
        - `DeviceProtocolPortWriteError` wenn (a) Target hat kein
          Command-Topic, (b) Client nicht gestartet oder
          (c) paho-mqtt `publish()` einen Non-Success-Returncode
          liefert.
        """
        self._assert_known_target(target)
        topic_cfg: MqttTopicConfig = self._config.topics[target]
        if topic_cfg.command is None:
            raise MqttPortNoCommandTopicError(target)
        if self._client is None:
            raise MqttPortNotStartedError(target)
        payload_bytes = encode_command(command)
        info = self._client.publish(topic_cfg.command, payload_bytes, qos=topic_cfg.qos_publish)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise MqttPortPublishFailedError(target, topic_cfg.command, info.rc)

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _assert_known_target(self, target: str) -> None:
        if target not in self._config.topics:
            raise DeviceProtocolPortUnknownTargetError(
                target,
                available_targets=tuple(sorted(self._config.topics.keys())),
            )

    def _on_message(
        self,
        _client: mqtt.Client,
        _userdata: object,
        message: MQTTMessage,
    ) -> None:
        """paho-mqtt-`on_message`-Callback (laeuft im Loop-Thread).

        Decision 4d: Lookup Topic -> device_id, Lazy-Init Queue,
        Decode + Enqueue. Exceptions werden ueber `safe_callback`
        geschluckt (ADR 0031 §2.4 Alternative A7), damit der
        Loop-Thread weiterlaeuft.
        """
        safe_callback(
            f"on_message[topic={message.topic!r}]",
            lambda: self._dispatch_message(message),
            logger=_LOGGER,
        )

    def _dispatch_message(self, message: MQTTMessage) -> None:
        """Inhalts-Dispatch: Topic-Lookup, Decode, Enqueue.

        Wird ueber `safe_callback` aus dem paho-Loop-Thread aufgerufen;
        BLE-strict (Standard-`Exception`-Propagation). `safe_callback`
        kapselt den Blind-Except.
        """
        device_id = self._topic_to_device.get(message.topic)
        if device_id is None:
            # Unbekanntes Topic — wir koennten nichts zu tun haben
            # (paho-mqtt liefert nur Topics, auf die wir per subscribe()
            # zugehoert haben; Wildcard-Subscribes sind Welle-6).
            return
        point = decode_telemetry(message.payload)
        with self._queues_lock:
            q = self._queues.setdefault(device_id, queue.Queue())
        q.put_nowait(point)
