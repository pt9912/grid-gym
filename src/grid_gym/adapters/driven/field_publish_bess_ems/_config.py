"""Konfiguration fuer den bess-ems-Feldvertrags-Publisher (Slice 077 S2, ADR 0078).

Simulation only — spricht einen simulierten/Test-MQTT-Broker an, um grid-gyms
**simulierte** Battery-Telemetrie als bess-ems-konformen Feld-Envelope zu
exponieren; **keine** produktive Anlagensteuerung ([`GG-SAFE-007`], ADR 0078 §2.8).
Broker-Exposure ist Nur-Sim-Netz (keine Auth/TLS).

`BessEmsFieldPublishConfig` ist eine frozen-dataclass; der Konstruktor validiert
fail-fast (typed `BessEmsFieldPublishConfigError`-Familie, Muster analog
`MqttFieldPublishConfig`).

Felder:

- `broker_host` — MQTT-Broker-Hostname (z. B. Mosquitto-Sibling).
- `broker_port` — TCP-Port (`1..65535`).
- `client_id` — MQTT-Client-ID (Pflicht; paho-Auto-Generierung waere
  nicht-deterministisch).
- `topic_prefix` — Topic-Wurzel; der Publisher sendet auf
  ``{topic_prefix}/{asset_id}/{telemetry,status,fault,command/ack}`` (Default
  `battery`, bess-ems-Feldvertrag).
- `qos` — Publish-QoS (`0`/`1`/`2`, Default `0` = fire-and-forget).
- `asset_id_by_device_id` — optionale `device_id → asset_id`-Umbenennung
  (ADR 0078 §2.3). Default leer = Identitaet (`asset_id == device_id`). **Grenze
  (Review LOW-3):** die **Eindeutigkeit** der Ziel-`asset_id`s ist Aufrufer-Pflicht —
  zwei `device_id`s auf dasselbe `asset_id` clobbern das retained `telemetry`/`status`-
  Topic (last-writer-wins). Ueber den env-Pfad nicht erreichbar (Identitaet, und
  `device_id`s sind eindeutig); nur bei direkter Config-Konstruktion relevant.
- `command_ack_enabled` — ob der Publisher `{prefix}/+/command` subscribed und ein
  Always-Accept-`command_ack`-Echo published (ADR 0078 §2.9, Default `True` — haelt
  bess-ems' `MqttCommandSink` vom `ack-timeout`→Safe-Stop ab). Echo ≠ Feldeffekt.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final

_ALLOWED_QOS: Final[frozenset[int]] = frozenset({0, 1, 2})
_MIN_PORT: Final[int] = 1
_MAX_PORT: Final[int] = 65535
_DEFAULT_QOS: Final[int] = 0
_DEFAULT_TOPIC_PREFIX: Final[str] = "battery"
# MQTT-Topic-Sonderzeichen, die ein Segment (`topic_prefix`/`asset_id`) nicht
# tragen darf (Wildcard/Level-Trenner → Fehlrouting bzw. paho-`ValueError`).
_TOPIC_SPECIALS: Final[tuple[str, ...]] = ("/", "+", "#")

# ADR 0078 §2.5: die Battery-Param-Bloecke (ADR 0077 + `ThermalConfig`/ADR 0065), die
# eine Battery tragen MUSS, damit ein konformer 10-Feld-`telemetry`-Frame bildbar ist
# (thermal→temperature_celsius, health→soh_percent, dc_bus→dc_voltage,
# reactive→reactive_power_kvar; soc_pct/power_kw emittiert jede Battery). Der
# Composition-Root prueft das fail-fast (`BessEmsFieldPublishConfigMissingFieldBlocksError`).
REQUIRED_FIELD_BLOCKS: Final[frozenset[str]] = frozenset(
    {"thermal", "health", "dc_bus", "reactive"}
)


class BessEmsFieldPublishConfigError(ValueError):
    """Base-Klasse fuer `BessEmsFieldPublishConfig`-Validation-Fehler (ValueError)."""


class BessEmsFieldPublishConfigEmptyFieldError(BessEmsFieldPublishConfigError):
    """String-Pflichtfeld (`broker_host`, `client_id`, `topic_prefix`) ist leer."""

    def __init__(self, field_name: str) -> None:
        super().__init__(f"BessEmsFieldPublishConfig.{field_name} darf nicht leer sein.")
        self.field_name: str = field_name


class BessEmsFieldPublishConfigInvalidPortError(BessEmsFieldPublishConfigError):
    """`broker_port` liegt ausserhalb des TCP-Port-Bereichs."""

    def __init__(self, value: int) -> None:
        super().__init__(
            f"BessEmsFieldPublishConfig.broker_port={value}: "
            f"muss in [{_MIN_PORT}, {_MAX_PORT}] liegen."
        )
        self.value: int = value


class BessEmsFieldPublishConfigInvalidQosError(BessEmsFieldPublishConfigError):
    """`qos` ist nicht in `{0, 1, 2}`."""

    def __init__(self, value: int) -> None:
        super().__init__(
            f"BessEmsFieldPublishConfig.qos={value}: "
            f"muss in {sorted(_ALLOWED_QOS)} liegen (paho-mqtt-Spec)."
        )
        self.value: int = value


class BessEmsFieldPublishConfigInvalidTopicSegmentError(BessEmsFieldPublishConfigError):
    """Ein Topic-Segment (`topic_prefix` oder ein `asset_id` aus dem Mapping) enthaelt
    ein MQTT-Sonderzeichen (`/`, `+`, `#`) → Fehlrouting/paho-`ValueError`."""

    def __init__(self, field_name: str, value: str) -> None:
        super().__init__(
            f"BessEmsFieldPublishConfig.{field_name}={value!r} enthaelt ein "
            f"MQTT-Sonderzeichen ({', '.join(_TOPIC_SPECIALS)})."
        )
        self.field_name: str = field_name
        self.value: str = value


class BessEmsFieldPublishConfigEndpointError(BessEmsFieldPublishConfigError):
    """Der Broker-Endpoint-String (env `host[:port]` / `[ipv6]:port`) ist nicht
    parsebar — typisiert statt bare `ValueError` (der den FastAPI-Lifespan crashen
    wuerde), Muster `MqttFieldPublishConfigEndpointError`."""

    def __init__(self, raw: str) -> None:
        super().__init__(
            f"bess-ems-Broker-Endpoint {raw!r} nicht parsebar — erwartet 'host', "
            "'host:port' oder '[ipv6]:port' (Port numerisch)."
        )
        self.raw: str = raw


class BessEmsFieldPublishConfigMissingFieldBlocksError(BessEmsFieldPublishConfigError):
    """§2.5-Fail-fast (ADR 0078): der bess-ems-Publisher ist konfiguriert, aber eine
    Battery traegt **nicht** die vollen Field-Envelope-Bloecke (ADR 0077) — ein
    konformer 10-Feld-`telemetry`-Frame waere nicht bildbar. Kein Adapter-Default fuer
    Pflicht-Physik (User-Entscheid „voll modelliert") — der Composition-Root lehnt bei
    Konstruktion ab, statt still Schema-invalide Frames zu senden."""

    def __init__(self, device_id: str, missing_blocks: tuple[str, ...]) -> None:
        super().__init__(
            f"bess-ems-Publisher aktiv, aber Battery {device_id!r} fehlen die "
            f"Field-Envelope-Bloecke {missing_blocks} (ADR 0077) — konfiguriere "
            "sie (thermal/health/dc_bus/reactive) oder deaktiviere den Publisher."
        )
        self.device_id: str = device_id
        self.missing_blocks: tuple[str, ...] = missing_blocks


@dataclass(frozen=True, slots=True)
class BessEmsFieldPublishConfig:
    """bess-ems-Feldvertrags-Publisher-Profil (ADR 0078 §2.3/§2.9).

    Konstruktor validiert fail-fast — der Aufrufer bekommt sofort eine typed
    `BessEmsFieldPublishConfigError`-Subclass bei fehlerhafter Konfig.
    """

    broker_host: str
    broker_port: int
    client_id: str
    topic_prefix: str = _DEFAULT_TOPIC_PREFIX
    qos: int = _DEFAULT_QOS
    asset_id_by_device_id: Mapping[str, str] = field(default_factory=dict)
    command_ack_enabled: bool = True

    def __post_init__(self) -> None:
        if not self.broker_host:
            raise BessEmsFieldPublishConfigEmptyFieldError("broker_host")
        if not (_MIN_PORT <= self.broker_port <= _MAX_PORT):
            raise BessEmsFieldPublishConfigInvalidPortError(self.broker_port)
        if not self.client_id:
            raise BessEmsFieldPublishConfigEmptyFieldError("client_id")
        if not self.topic_prefix:
            raise BessEmsFieldPublishConfigEmptyFieldError("topic_prefix")
        if any(char in self.topic_prefix for char in _TOPIC_SPECIALS):
            raise BessEmsFieldPublishConfigInvalidTopicSegmentError(
                "topic_prefix", self.topic_prefix
            )
        if self.qos not in _ALLOWED_QOS:
            raise BessEmsFieldPublishConfigInvalidQosError(self.qos)
        # Die gemappten `asset_id`-Ziele muessen valide Topic-Segmente sein (die
        # `device_id`-Schluessel kommen aus der Scenario-Definition, sind bereits
        # validiert; die Werte sind frei konfiguriert → hier pruefen).
        for asset_id in self.asset_id_by_device_id.values():
            if not asset_id or any(char in asset_id for char in _TOPIC_SPECIALS):
                raise BessEmsFieldPublishConfigInvalidTopicSegmentError(
                    "asset_id_by_device_id", asset_id
                )

    def asset_id_for(self, device_id: str) -> str:
        """`device_id → asset_id`-Aufloesung (ADR 0078 §2.3). Default-Identitaet:
        nicht gemappte `device_id`s werden 1:1 als `asset_id` verwendet."""
        return self.asset_id_by_device_id.get(device_id, device_id)
