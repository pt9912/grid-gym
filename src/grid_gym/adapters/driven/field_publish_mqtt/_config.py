"""Konfiguration fuer den MQTT-Field-Publish-Adapter (ADR 0075 §2.1).

Simulation only — diese Konfiguration spricht einen simulierten/Test-
MQTT-Broker an, um grid-gyms **simulierte** Geraetetelemetrie fuer ein
externes EMS (System-under-Test) zu exponieren; **keine** produktive
Anlagensteuerung ([`GG-SAFE-007`], [`GG-NONGOAL-001`]). Broker-Exposure
ist eine Nur-Sim-Netz-Annahme (keine Auth/TLS im Slice-073-Scope).

`MqttFieldPublishConfig` ist eine frozen-dataclass; der Konstruktor
validiert fail-fast (typed `MqttFieldPublishConfigError`-Familie,
Muster analog `MqttConfigError` aus `protocol_mqtt`).

Felder:

- `broker_host` — MQTT-Broker-Hostname (z. B. Mosquitto-Sibling).
- `broker_port` — TCP-Port (`1..65535`).
- `client_id` — MQTT-Client-ID (Pflicht; paho-Auto-Generierung waere
  nicht-deterministisch).
- `topic_prefix` — Topic-Praefix; der Adapter publisht je Punkt auf
  ``{topic_prefix}/{device_id}/{metric}``.
- `qos` — Publish-QoS (`0`/`1`/`2`, Default `0` = fire-and-forget
  Telemetrie, `spec/protocol_profiles.md`-Konvention).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

_ALLOWED_QOS: Final[frozenset[int]] = frozenset({0, 1, 2})
_MIN_PORT: Final[int] = 1
_MAX_PORT: Final[int] = 65535
_DEFAULT_QOS: Final[int] = 0


class MqttFieldPublishConfigError(ValueError):
    """Base-Klasse fuer `MqttFieldPublishConfig`-Validation-Fehler.

    Erbt von `ValueError`; konkrete Faelle werfen Subklassen mit
    strukturierten Konstruktor-Parametern (TRY003-Konvention).
    """


class MqttFieldPublishConfigEmptyFieldError(MqttFieldPublishConfigError):
    """String-Pflichtfeld (`broker_host`, `client_id`, `topic_prefix`)
    ist leer."""

    def __init__(self, field_name: str) -> None:
        super().__init__(f"MqttFieldPublishConfig.{field_name} darf nicht leer sein.")
        self.field_name: str = field_name


class MqttFieldPublishConfigInvalidPortError(MqttFieldPublishConfigError):
    """`broker_port` liegt ausserhalb des TCP-Port-Bereichs."""

    def __init__(self, value: int) -> None:
        super().__init__(
            f"MqttFieldPublishConfig.broker_port={value}: "
            f"muss in [{_MIN_PORT}, {_MAX_PORT}] liegen."
        )
        self.value: int = value


class MqttFieldPublishConfigInvalidQosError(MqttFieldPublishConfigError):
    """`qos` ist nicht in `{0, 1, 2}`."""

    def __init__(self, value: int) -> None:
        super().__init__(
            f"MqttFieldPublishConfig.qos={value}: "
            f"muss in {sorted(_ALLOWED_QOS)} liegen (paho-mqtt-Spec)."
        )
        self.value: int = value


class MqttFieldPublishConfigEndpointError(MqttFieldPublishConfigError):
    """Der Broker-Endpoint-String (env `host[:port]` / `[ipv6]:port`) ist nicht
    parsebar (Review-Fix #2: typisiert statt bare `ValueError`, der den
    FastAPI-Lifespan crashen wuerde)."""

    def __init__(self, raw: str) -> None:
        super().__init__(
            f"Broker-Endpoint {raw!r} nicht parsebar — erwartet 'host', "
            "'host:port' oder '[ipv6]:port' (Port numerisch)."
        )
        self.raw: str = raw


@dataclass(frozen=True, slots=True)
class MqttFieldPublishConfig:
    """Field-Publish-Adapter-Profil (Push-Seite, ADR 0075 §2.1).

    Konstruktor validiert fail-fast — der Aufrufer bekommt sofort eine
    typed `MqttFieldPublishConfigError`-Subclass bei fehlerhafter Konfig.
    """

    broker_host: str
    broker_port: int
    client_id: str
    topic_prefix: str
    qos: int = _DEFAULT_QOS

    def __post_init__(self) -> None:
        if not self.broker_host:
            raise MqttFieldPublishConfigEmptyFieldError("broker_host")
        if not (_MIN_PORT <= self.broker_port <= _MAX_PORT):
            raise MqttFieldPublishConfigInvalidPortError(self.broker_port)
        if not self.client_id:
            raise MqttFieldPublishConfigEmptyFieldError("client_id")
        if not self.topic_prefix:
            raise MqttFieldPublishConfigEmptyFieldError("topic_prefix")
        if self.qos not in _ALLOWED_QOS:
            raise MqttFieldPublishConfigInvalidQosError(self.qos)
