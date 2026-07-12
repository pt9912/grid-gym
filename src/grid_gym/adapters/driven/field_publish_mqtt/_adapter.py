"""`MqttFieldPublishAdapter` — `FieldPublishPort`-Implementer (ADR 0075 §2.1).

Publish-only-Adapter fuer die **Push-Seite** der Field-Server-Surface: er
exponiert grid-gyms emittierte (simulierte) Geraetetelemetrie an einen
MQTT-Broker, damit ein externes EMS (System-under-Test, z. B. `bess-ems`)
sie konsumieren kann (HIL-Konkretisierung von `GG-TEST-004`).

Schlanker als der driven-`protocol_mqtt`-Adapter: **kein** Subscribe,
**kein** Callback-Marshal, **kein** Decode — nur connect / publish /
disconnect. paho-mqtt laeuft per `loop_start()` in einem internen Thread;
`client.publish()` ist thread-safe (paho-Doku), der `publish()`-Aufruf
kommt aus dem sync-Driver-Loop-Body (kein Cross-Loop-Await).

**Domaenen-`TelemetryPoint`** (ADR 0075 §2.1): der Payload wird direkt aus
dem Domaenen-Punkt serialisiert (`value: Decimal` als String) — **kein**
`Decimal->float`-Verlust.

**Simulations-/Testadapter** ([`GG-SAFE-007`], [`GG-NONGOAL-001`]): keine
produktive Anlagensteuerung; Broker-Exposure ist Nur-Sim-Netz (keine
Auth/TLS im Slice-073-Scope).
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import paho.mqtt.client as mqtt

from grid_gym.adapters.driven.field_publish_mqtt._config import MqttFieldPublishConfig
from grid_gym.adapters.driven.field_publish_mqtt._errors import (
    MqttFieldPublishConnectError,
    MqttFieldPublishDisconnectError,
    MqttFieldPublishNotStartedError,
    MqttFieldPublishPublishFailedError,
)
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.serialization.canonical import canonical_json

_LOGGER: logging.Logger = logging.getLogger(__name__)


# Client-Factory-Hook (Default ruft paho.mqtt.Client; Tests reichen einen
# Mock durch, damit kein echter Broker/Socket noetig ist).
ClientFactory = Callable[[MqttFieldPublishConfig], mqtt.Client]


def _default_client_factory(config: MqttFieldPublishConfig) -> mqtt.Client:
    """Default-Client-Factory: paho-mqtt 2.x mit CallbackAPIVersion.VERSION2."""
    return mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # type: ignore[attr-defined]
        client_id=config.client_id,
    )


def _encode_point(point: TelemetryPoint) -> bytes:
    """Serialisiert einen Domaenen-`TelemetryPoint` deterministisch zu
    kanonischen UTF-8-JSON-Bytes via `canonical_json` (AC-NO-JSON: kein
    `json.dumps`). `value: Decimal` fliesst nativ in den canonical-Pfad
    (Fixed-Point-Notation) — volle Fidelity, kein float-Cast (ADR 0075
    §2.1); Muster analog `protocol_mqtt`-`encode_telemetry`."""
    payload: dict[str, object] = {
        "run_id": point.run_id,
        "tick": point.tick,
        "simulation_time": point.simulation_time,
        "device_id": point.device_id,
        "metric": point.metric,
        "value": point.value,
        "unit": point.unit,
        "quality": point.quality.value,
        "source": point.source,
        "sequence": point.sequence,
    }
    return canonical_json(payload)


class MqttFieldPublishAdapter:
    """MQTT-Publish-Adapter (Simulations-/Testadapter; keine produktive
    Anlagensteuerung).

    Implementiert `FieldPublishPort` (ADR 0075 §2.1). Lifecycle idempotent:
    Doppel-`start()` ist No-op nach erstem erfolgreichem Connect; `stop()`
    nach erfolglosem/nicht-erfolgtem `start()` ist No-op.
    """

    def __init__(
        self,
        config: MqttFieldPublishConfig,
        *,
        client_factory: ClientFactory | None = None,
    ) -> None:
        self._config: MqttFieldPublishConfig = config
        self._client_factory: ClientFactory = client_factory or _default_client_factory
        self._client: mqtt.Client | None = None
        self._started: bool = False

    def start(self) -> None:
        """Connect zum Broker + `loop_start()`. Idempotent."""
        if self._started:
            return
        client = self._client_factory(self._config)
        try:
            client.connect(self._config.broker_host, self._config.broker_port)
        except OSError as exc:
            raise MqttFieldPublishConnectError(
                self._config.broker_host, self._config.broker_port, exc
            ) from exc
        client.loop_start()
        self._client = client
        self._started = True

    def publish(self, point: TelemetryPoint) -> None:
        """Publisht `point` auf ``{topic_prefix}/{device_id}/{metric}``.

        Wirft `MqttFieldPublishNotStartedError`, wenn kein aktiver Client
        (vor `start()` / nach `stop()`), und `MqttFieldPublishPublishFailedError`
        bei paho-Non-Success-Returncode.
        """
        client = self._client
        if client is None:
            raise MqttFieldPublishNotStartedError
        topic = f"{self._config.topic_prefix}/{point.device_id}/{point.metric}"
        info = client.publish(topic, _encode_point(point), qos=self._config.qos)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise MqttFieldPublishPublishFailedError(topic, info.rc)

    def stop(self) -> None:
        """`loop_stop()` + `disconnect()`. Idempotent — Doppel-Stop ist
        No-op. Der interne Zustand wird auch bei Disconnect-Fehler
        zurueckgesetzt (Best-Effort-Cleanup, Muster `protocol_mqtt`)."""
        if not self._started or self._client is None:
            return
        client = self._client
        self._client = None
        self._started = False
        try:
            client.loop_stop()
            client.disconnect()
        except OSError as exc:
            raise MqttFieldPublishDisconnectError(exc) from exc
