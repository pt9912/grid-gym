"""MQTT-Adapter-spezifische Subclasses der
`DeviceProtocolPort*Error`-Familie (M4 Welle 2, ADR 0030 §4 +
ADR 0031).

ADR 0030 §4 erlaubt Welle-2+-Adaptern, pro Adapter spezifische
Subclasses unterhalb der `DeviceProtocolPort*Error`-Wurzel
einzufuehren (Pattern analog `OtlpAdapterConfigError`-Familie aus
M3-Welle-6 / ADR 0024 §4.5). Jede Subklasse traegt strukturierte
Konstruktor-Parameter und baut die Message in `__init__` — das loest
`TRY003` per Codebase-Konvention.
"""

from __future__ import annotations

from grid_gym.hexagon.ports.driven.device_protocol import (
    DeviceProtocolPortStartError,
    DeviceProtocolPortStopError,
    DeviceProtocolPortWriteError,
)


class MqttPortConnectError(DeviceProtocolPortStartError):
    """paho-mqtt-`connect()` ist auf OS-Ebene gescheitert
    (z. B. Broker nicht erreichbar)."""

    def __init__(self, host: str, port: int, cause: OSError) -> None:
        super().__init__(f"MQTT-Connect zu {host}:{port} fehlgeschlagen: {cause}")
        self.host: str = host
        self.port: int = port


class MqttPortDisconnectError(DeviceProtocolPortStopError):
    """paho-mqtt-`disconnect()` / `loop_stop()` ist auf OS-Ebene
    gescheitert (z. B. Netzwerk-Reset waehrend Abbau)."""

    def __init__(self, cause: OSError) -> None:
        super().__init__(f"MQTT-Disconnect fehlgeschlagen: {cause}")


class MqttPortNoCommandTopicError(DeviceProtocolPortWriteError):
    """Target ist im Profil, aber hat keinen `command`-Topic
    (write-Pfad ist fuer dieses Target nicht konfiguriert)."""

    def __init__(self, target: str) -> None:
        super().__init__(
            f"Target {target!r}: kein Command-Topic im Profil "
            "(write-Pfad ist fuer dieses Target nicht konfiguriert)."
        )
        self.target: str = target


class MqttPortNotStartedError(DeviceProtocolPortWriteError):
    """`write()` wurde aufgerufen, bevor `start()` erfolgreich war."""

    def __init__(self, target: str) -> None:
        super().__init__(
            f"Target {target!r}: Client nicht gestartet — "
            "vor write() muss start() erfolgreich gelaufen sein."
        )
        self.target: str = target


class MqttPortPublishFailedError(DeviceProtocolPortWriteError):
    """paho-mqtt-`publish()` lieferte einen Non-Success-Returncode."""

    def __init__(self, target: str, topic: str, return_code: int) -> None:
        super().__init__(
            f"MQTT-Publish auf Topic {topic!r} (target={target!r}) lieferte rc={return_code}."
        )
        self.target: str = target
        self.topic: str = topic
        self.return_code: int = return_code
