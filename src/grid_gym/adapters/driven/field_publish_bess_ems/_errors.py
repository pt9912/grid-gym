"""Adapter-spezifische Fehler fuer den bess-ems-Feldvertrags-Publisher
(Slice 077 S2, ADR 0078).

Anders als `field_publish_mqtt` implementiert dieser Adapter **keinen**
`FieldPublishPort` (er aggregiert je Tick, ADR 0078 §2.1) — die Fehler sind darum
eine eigenstaendige Familie unter `BessEmsFieldPublishError` (nicht Subclasses des
Port-Vertrags). Der Driver faengt sie pauschal (Muster `_publish_field`:
graceful-degrade, Feld-Feed ist optional).
"""

from __future__ import annotations


class BessEmsFieldPublishError(Exception):
    """Base-Klasse fuer alle Laufzeit-Fehler des bess-ems-Publishers."""


class BessEmsFieldPublishConnectError(BessEmsFieldPublishError):
    """`start()` konnte nicht zum Broker connecten (OSError von paho)."""

    def __init__(self, broker_host: str, broker_port: int, cause: OSError) -> None:
        super().__init__(
            f"BessEmsFieldPublishAdapter: connect zu {broker_host}:{broker_port} "
            f"fehlgeschlagen: {cause}"
        )
        self.broker_host: str = broker_host
        self.broker_port: int = broker_port
        self.cause: OSError = cause


class BessEmsFieldPublishNotStartedError(BessEmsFieldPublishError):
    """`publish_tick()` wurde vor `start()` (oder nach `stop()`) gerufen — kein
    aktiver Client."""

    def __init__(self) -> None:
        super().__init__(
            "BessEmsFieldPublishAdapter: publish_tick() vor start() (oder nach "
            "stop()) — kein aktiver Client."
        )


class BessEmsFieldPublishInvalidAssetIdError(BessEmsFieldPublishError):
    """Die aufgeloeste `asset_id` (aus Mapping oder Identitaet = `device_id`) ist als
    MQTT-Topic-Segment ungueltig (leer / enthaelt `/`, `+`, `#`) — Fehlrouting bzw.
    paho-`ValueError` (Muster `field_publish_mqtt` Review-Fix #5). Die Mapping-Werte
    sind schon in der Config geprueft; dieser Guard faengt den Identitaets-Pfad
    (`asset_id == device_id`), falls eine Scenario-`device_id` ein Sonderzeichen
    traegt."""

    def __init__(self, asset_id: str) -> None:
        super().__init__(
            f"BessEmsFieldPublishAdapter: asset_id={asset_id!r} ist als "
            "MQTT-Topic-Segment ungueltig (leer oder enthaelt '/', '+', '#')."
        )
        self.asset_id: str = asset_id


class BessEmsFieldPublishPublishFailedError(BessEmsFieldPublishError):
    """paho-mqtt `publish()` lieferte einen Non-Success-Returncode."""

    def __init__(self, topic: str, rc: int) -> None:
        super().__init__(
            f"BessEmsFieldPublishAdapter: publish auf Topic {topic!r} lieferte "
            f"paho-Returncode rc={rc} (!= MQTT_ERR_SUCCESS)."
        )
        self.topic: str = topic
        self.rc: int = rc


class BessEmsFieldPublishDisconnectError(BessEmsFieldPublishError):
    """`stop()` konnte nicht sauber vom Broker disconnecten (OSError)."""

    def __init__(self, cause: OSError) -> None:
        super().__init__(f"BessEmsFieldPublishAdapter: disconnect fehlgeschlagen: {cause}")
        self.cause: OSError = cause
