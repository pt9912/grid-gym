"""MQTT-Adapter-Profile-Konfiguration (M4 Welle 2, ADR 0031 §2.1).

Simulation only — diese Adapter-Konfiguration ist dafuer gedacht,
simulierte MQTT-Broker oder Testaufbauten anzusprechen, nicht
produktive Anlagen (`GG-SAFE-007`, `GG-NONGOAL-001`).

`MqttProtocolPortConfig` ist eine frozen-dataclass mit dem inline-im-
`protocol_ports`-Block deklarierten Topic-Schema (Decision 4a). Pro
`device_id` traegt `MqttTopicConfig` die Pflicht-Felder Telemetry-/
Command-Topic und die QoS-Defaults (Decision 4c). Validation-Errors
werfen typed Sub-Exceptions analog `OtlpAdapterConfigError`-Familie
aus M3-Welle-6.

Welle-2-Felder:

- `broker_host` — Mosquitto-/MQTT-Broker-Hostname (Default `localhost`).
- `broker_port` — TCP-Port (Default `1883`).
- `client_id` — MQTT-Client-ID (Pflichtfeld; paho-mqtt-Default-Auto-
  Generierung waere nicht-deterministisch und braeche Replay-Tests).
- `topics` — Mapping `device_id` -> `MqttTopicConfig` (Decision 4a
  inline-Schema). Mindestens ein Eintrag noetig.

`MqttTopicConfig`:

- `telemetry` — Topic-String fuer Subscribe-Telemetry (`None` = kein
  Subscribe fuer dieses Target; `read()` liefert dann immer `None`).
- `command` — Topic-String fuer Publish-Commands (`None` = kein
  Publish-Pfad; `write()` wirft `DeviceProtocolPortWriteError`).
- `qos_publish` — Publish-QoS (Decision 4c-Default `0`; `0`/`1`/`2`).
- `qos_subscribe` — Subscribe-QoS (Decision 4c-Default `1`).

Validation-Pflicht (im Konstruktor, fail-fast):

- Mindestens eine Topic-Definition (`telemetry` oder `command` gesetzt
  pro Topic-Config) — leere Topic-Configs sind verboten.
- QoS in `{0, 1, 2}` — paho-mqtt-Spec.
- Broker-Port in `1..65535`.
- Keine doppelten Topic-Strings ueber alle `device_id`s (sonst waere
  der Reverse-Index in `_topic_resolver` ambig).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final


_DEFAULT_QOS_PUBLISH: Final[int] = 0
_DEFAULT_QOS_SUBSCRIBE: Final[int] = 1
_ALLOWED_QOS: Final[frozenset[int]] = frozenset({0, 1, 2})
_MIN_PORT: Final[int] = 1
_MAX_PORT: Final[int] = 65535


class MqttConfigError(ValueError):
    """Base-Klasse fuer `MqttProtocolPortConfig`-Validation-Fehler
    (ADR 0031 §2.1).

    Erbt von `ValueError`, damit defensiv-coded Aufrufer den Standard-
    Konstruktor-Fehler-Pfad nicht aendern muessen. Konkrete Fehlerfaelle
    werfen Subklassen mit strukturierten Konstruktor-Parametern
    (TRY003-Konvention, Message-Bildung in Subklasse).
    """


class MqttConfigEmptyFieldError(MqttConfigError):
    """String-Pflichtfeld (`broker_host`, `client_id`) ist leer."""

    def __init__(self, field_name: str) -> None:
        super().__init__(f"MqttProtocolPortConfig.{field_name} darf nicht leer sein.")
        self.field_name: str = field_name


class MqttConfigInvalidPortError(MqttConfigError):
    """`broker_port` liegt ausserhalb des TCP-Port-Bereichs."""

    def __init__(self, value: int) -> None:
        super().__init__(
            f"MqttProtocolPortConfig.broker_port={value}: "
            f"muss in [{_MIN_PORT}, {_MAX_PORT}] liegen."
        )
        self.value: int = value


class MqttConfigEmptyTopicsError(MqttConfigError):
    """`topics` ist leer; mindestens ein Eintrag noetig."""

    def __init__(self) -> None:
        super().__init__("MqttProtocolPortConfig.topics darf nicht leer sein.")


class MqttConfigInvalidQosError(MqttConfigError):
    """QoS ist nicht in `{0, 1, 2}`."""

    def __init__(self, field_name: str, value: int, device_id: str) -> None:
        super().__init__(
            f"MqttTopicConfig({device_id!r}).{field_name}={value}: "
            f"muss in {sorted(_ALLOWED_QOS)} liegen (paho-mqtt-Spec)."
        )
        self.field_name: str = field_name
        self.value: int = value
        self.device_id: str = device_id


class MqttConfigEmptyTopicError(MqttConfigError):
    """Topic-Config hat weder `telemetry` noch `command` Topic.

    Eine Topic-Config ohne Pub/Sub-Pfad ist nutzlos — der Adapter
    haette weder Lese- noch Schreib-Operation fuer dieses Target.
    """

    def __init__(self, device_id: str) -> None:
        super().__init__(
            f"MqttTopicConfig({device_id!r}): mindestens eines von "
            "`telemetry` oder `command` muss gesetzt sein."
        )
        self.device_id: str = device_id


class MqttConfigDuplicateTopicError(MqttConfigError):
    """Derselbe Topic-String taucht in mehreren `device_id`-Eintraegen auf.

    Wuerde den Reverse-Index in `_topic_resolver` ambig machen
    (Decision 4d-Callback wuesste nicht, an welche `device_id`-Queue
    er die Message routen soll).
    """

    def __init__(self, topic: str, device_ids: tuple[str, ...]) -> None:
        ids = ", ".join(repr(d) for d in device_ids)
        super().__init__(
            f"MqttProtocolPortConfig.topics: Topic {topic!r} taucht "
            f"in mehreren device_ids auf ({ids}). Topic-Reverse-Index "
            "muss eindeutig sein (ADR 0031 §2.4)."
        )
        self.topic: str = topic
        self.device_ids: tuple[str, ...] = device_ids


@dataclass(frozen=True, slots=True)
class MqttTopicConfig:
    """Topic-Profil fuer ein einzelnes Target (Decision 4a inline-Schema).

    Beide Topic-Felder sind optional, aber **mindestens eines** muss
    gesetzt sein (siehe `MqttConfigEmptyTopicError`). QoS-Defaults
    folgen Decision 4c (0 fuer Publish, 1 fuer Subscribe);
    Override per Konstruktor.
    """

    telemetry: str | None = None
    command: str | None = None
    qos_publish: int = _DEFAULT_QOS_PUBLISH
    qos_subscribe: int = _DEFAULT_QOS_SUBSCRIBE


@dataclass(frozen=True, slots=True)
class MqttProtocolPortConfig:
    """MQTT-Adapter-Profile (Decision 4a inline-Schema im Scenario-YAML).

    Konstruktor validiert fail-fast — Konstruktor-Aufrufer (Scenario-
    Loader oder Test) bekommt sofort eine typed `MqttConfigError`-
    Subclass bei fehlerhafter Konfig.

    Konstruktion via `MqttProtocolPortConfig(...)` direkt; ein
    `from_yaml(...)`-Loader-Hook ist Welle-2-C2-Folge oder Welle-3-
    Material (Scenario-Loader bleibt MQTT-frei per AC-HEXAGON-PURE,
    siehe ADR 0031 §4 Konsequenzen).
    """

    broker_host: str
    broker_port: int
    client_id: str
    topics: Mapping[str, MqttTopicConfig]

    def __post_init__(self) -> None:
        self._validate()
        # Make topics-Mapping immutable nach Konstruktion (MappingProxyType
        # ist tooltable-frozen und passt zu AC-DOMAIN-FROZEN).
        object.__setattr__(self, "topics", MappingProxyType(dict(self.topics)))

    def _validate(self) -> None:
        if not self.broker_host:
            raise MqttConfigEmptyFieldError("broker_host")
        if not (_MIN_PORT <= self.broker_port <= _MAX_PORT):
            raise MqttConfigInvalidPortError(self.broker_port)
        if not self.client_id:
            raise MqttConfigEmptyFieldError("client_id")
        if not self.topics:
            raise MqttConfigEmptyTopicsError
        self._validate_topics()

    def _validate_topics(self) -> None:
        topic_to_device_ids: dict[str, list[str]] = {}
        for device_id, topic_cfg in self.topics.items():
            _validate_single_topic_config(device_id, topic_cfg)
            _collect_topic_strings(device_id, topic_cfg, topic_to_device_ids)
        _assert_unique_topics(topic_to_device_ids)


def _validate_single_topic_config(device_id: str, topic_cfg: MqttTopicConfig) -> None:
    """Prueft Pflicht-Felder und QoS-Range fuer eine einzelne
    `MqttTopicConfig`. Wirft typed Errors mit Kontext."""
    if topic_cfg.telemetry is None and topic_cfg.command is None:
        raise MqttConfigEmptyTopicError(device_id)
    if topic_cfg.qos_publish not in _ALLOWED_QOS:
        raise MqttConfigInvalidQosError("qos_publish", topic_cfg.qos_publish, device_id)
    if topic_cfg.qos_subscribe not in _ALLOWED_QOS:
        raise MqttConfigInvalidQosError("qos_subscribe", topic_cfg.qos_subscribe, device_id)


def _collect_topic_strings(
    device_id: str,
    topic_cfg: MqttTopicConfig,
    dest: dict[str, list[str]],
) -> None:
    """Sammelt Telemetry-/Command-Topic-Strings je `device_id` in
    `dest`, damit Duplikate spaeter erkennbar sind."""
    for topic in (topic_cfg.telemetry, topic_cfg.command):
        if topic is not None:
            dest.setdefault(topic, []).append(device_id)


def _assert_unique_topics(topic_to_device_ids: dict[str, list[str]]) -> None:
    """Wirft `MqttConfigDuplicateTopicError`, wenn ein Topic-String
    in mehreren `device_id`-Eintraegen auftaucht."""
    for topic, device_ids in topic_to_device_ids.items():
        if len(device_ids) > 1:
            raise MqttConfigDuplicateTopicError(topic, tuple(device_ids))
