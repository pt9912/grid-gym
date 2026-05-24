"""OTLP-Adapter-Konfiguration (M3 Welle 6, ADR 0024 §4.5.6).

`OtlpAdapterConfig` ist eine frozen-dataclass mit Env-Var-Fallback fuer
die OpenTelemetry-Standard-Variablen. Allow-List-Validation am
`protocol`-Feld pinnt Welle 6 auf gRPC (ADR 0024 §4.5.6); HTTP/protobuf
ist Out-of-Scope und wuerde eine Konfig-Erweiterung plus Folge-Welle
erfordern.

Konstruktions-Pfade:

- Direkter Konstruktor `OtlpAdapterConfig(...)`: explizite Werte; alle
  Defaults stammen aus den Klassen-Konstanten unten (kein Env-Var-
  Pull). Eignet sich fuer Test-Setups und programmatische Konfig.
- `OtlpAdapterConfig.from_env(env=..., **overrides)`: zieht zuerst die
  OTEL-Standard-Env-Vars; explizite Kwargs ueberschreiben Env-Werte;
  fehlende Env-Vars fallen auf die Klassen-Defaults.

Welle-6-Felder (siehe `M3-welle-6.md §3 C1`):

- `endpoint` — OTLP-Collector-URL (gRPC; Default `http://localhost:4317`).
- `headers` — Zusaetzliche HTTP-/Metadata-Headers.
- `timeout_s` — Export-Timeout in Sekunden.
- `batch_max_export_size` — Maximale Batch-Groesse pro Export-Aufruf
  (SDK-`BatchSpanProcessor`-Parameter).
- `service_name` — Resource-Attribut `service.name`.
- `service_instance_id` — Resource-Attribut `service.instance.id`
  (`None` = Auto-Generierung im Adapter / OTel-SDK-Default).
- `protocol` — Transport-Wahl; Allow-List `{"grpc"}` (Welle-6-Pin).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final
from urllib.parse import unquote

__all__ = [
    "OtlpAdapterConfig",
    "OtlpAdapterConfigBatchTooLargeError",
    "OtlpAdapterConfigEmptyFieldError",
    "OtlpAdapterConfigEnvTimeoutParseError",
    "OtlpAdapterConfigError",
    "OtlpAdapterConfigInvalidHeaderError",
    "OtlpAdapterConfigInvalidProtocolError",
    "OtlpAdapterConfigNonPositiveError",
    "OtlpAdapterConfigOverrides",
    "OtlpAdapterConfigTimeoutTooSmallError",
]

# Default-Werte (siehe Modul-Docstring fuer Begruendung).
_DEFAULT_ENDPOINT: Final[str] = "http://localhost:4317"
_DEFAULT_TIMEOUT_S: Final[float] = 10.0

# OTLP-Exporter-`timeout`-Kwarg ist in Sekunden als `int` (OTel-SDK
# 1.42-Konvention). `int(0.5) == 0` waere ein Null-Timeout (sofortiger
# Fail oder unendlich, je nach SDK-Variante). Wir verlangen ≥ 1 s als
# Floor, damit `int(round(timeout_s)) >= 1` und der Konfig-Pfad sicher
# auf die OTel-API mappt (Review-Folge M-1).
_MIN_TIMEOUT_S: Final[float] = 1.0
_DEFAULT_BATCH_MAX_EXPORT_SIZE: Final[int] = 512

# OTel-SDK 1.42 setzt das interne `BatchSpanProcessor.max_queue_size`
# auf 2048 hart; `max_export_batch_size > max_queue_size` waere silent
# gedrosselt (Records verschwinden im Drop). Wir spiegeln das Limit
# als Validation, damit Konfig-Drift sofort sichtbar wird statt im
# Compose-Smoke (Review-Folge H-3 zu ADR 0024 §4.5.7).
_MAX_BATCH_MAX_EXPORT_SIZE: Final[int] = 2048
_DEFAULT_SERVICE_NAME: Final[str] = "grid-gym"
_DEFAULT_PROTOCOL: Final[str] = "grpc"

# Welle-6-Allow-List fuer `protocol` (ADR 0024 §4.5.6). Folge-Slices
# duerfen die Liste oeffnen — bis dahin ist alles ausser `grpc` ein
# `OtlpAdapterConfigError`.
_ALLOWED_PROTOCOLS: Final[frozenset[str]] = frozenset({"grpc"})

# OTEL-Standard-Env-Var-Namen (OpenTelemetry-SDK-Konvention).
_ENV_ENDPOINT: Final[str] = "OTEL_EXPORTER_OTLP_ENDPOINT"
_ENV_HEADERS: Final[str] = "OTEL_EXPORTER_OTLP_HEADERS"
_ENV_TIMEOUT_MS: Final[str] = "OTEL_EXPORTER_OTLP_TIMEOUT"
_ENV_SERVICE_NAME: Final[str] = "OTEL_SERVICE_NAME"
_ENV_PROTOCOL: Final[str] = "OTEL_EXPORTER_OTLP_PROTOCOL"
_ENV_RESOURCE_ATTRIBUTES: Final[str] = "OTEL_RESOURCE_ATTRIBUTES"

# OTEL-Spec: `OTEL_EXPORTER_OTLP_TIMEOUT` ist in Millisekunden
# definiert; wir rechnen intern in Sekunden.
_MS_PER_S: Final[int] = 1000


class OtlpAdapterConfigError(ValueError):
    """Base-Klasse fuer `OtlpAdapterConfig`-Validation-Fehler
    (ADR 0024 §4.5.6).

    Erbt von `ValueError`, damit defensiv-coded Aufrufer den Standard-
    Konstruktor-Fehler-Pfad nicht aendern muessen. Konkrete Fehlerfaelle
    werfen Subklassen mit strukturierten Konstruktor-Parametern; die
    Message-Bildung passiert in den Subklassen (loest `TRY003` per
    Codebase-Konvention, analog `BatteryConfigError`-Hierarchie).
    """


class OtlpAdapterConfigInvalidProtocolError(OtlpAdapterConfigError):
    """`protocol`-Wert ist nicht in der Welle-6-Allow-List (ADR 0024 §4.5.6)."""

    def __init__(self, value: str) -> None:
        allowed_sorted = sorted(_ALLOWED_PROTOCOLS)
        super().__init__(
            f"OtlpAdapterConfig.protocol={value!r}: nicht in Allow-List "
            f"{allowed_sorted} (ADR 0024 §4.5.6 — HTTP/protobuf ist Out-of-"
            "Scope und braucht eine Folge-Welle)."
        )


class OtlpAdapterConfigEmptyFieldError(OtlpAdapterConfigError):
    """String-Pflichtfeld (z. B. `endpoint`, `service_name`) ist leer."""

    def __init__(self, field: str) -> None:
        super().__init__(f"OtlpAdapterConfig.{field} darf nicht leer sein.")


class OtlpAdapterConfigNonPositiveError(OtlpAdapterConfigError):
    """Numerisches Feld (`timeout_s`, `batch_max_export_size`) ist ≤ 0."""

    def __init__(self, field: str, value: float | int) -> None:
        super().__init__(f"OtlpAdapterConfig.{field}={value} muss > 0 sein.")


class OtlpAdapterConfigTimeoutTooSmallError(OtlpAdapterConfigError):
    """`timeout_s` ist unter dem Sub-Sekunden-Floor (Review-Folge M-1).

    OTel-Exporter erwarten `timeout` als Integer-Sekunden; `int(0.5) == 0`
    wuerde als Null-Timeout interpretiert (SDK-Variante-abhaengig:
    sofortiger Fail oder unendlich). Floor ≥ 1 s erzwingt eine
    sinnvolle Sekunden-Aufloesung.
    """

    def __init__(self, value: float) -> None:
        super().__init__(
            f"OtlpAdapterConfig.timeout_s={value} muss >= {_MIN_TIMEOUT_S} s sein "
            "(OTel-Exporter-`timeout`-Kwarg ist int-Sekunden; "
            "Sub-Sekunden-Aufloesung waere verlustbehaftet). "
            "Review-Folge M-1 zu ADR 0024 §4.5."
        )


class OtlpAdapterConfigBatchTooLargeError(OtlpAdapterConfigError):
    """`batch_max_export_size` ueberschreitet das OTel-SDK-`max_queue_size`-Limit (2048).

    Review-Folge H-3 zu ADR 0024 §4.5.7: ueberlange Batches wuerden silent
    am `max_queue_size`-Hard-Limit von `BatchSpanProcessor`/
    `BatchLogRecordProcessor` gedrosselt; das ist kein Drop-Error, sondern
    Record-Verlust. Validation hier macht die Konfig-Drift sofort sichtbar.
    """

    def __init__(self, value: int) -> None:
        super().__init__(
            f"OtlpAdapterConfig.batch_max_export_size={value} > "
            f"{_MAX_BATCH_MAX_EXPORT_SIZE} (OTel-SDK-`max_queue_size`-Hard-Limit; "
            "ueberlange Batches werden silent gedrosselt). "
            "Review-Folge H-3 zu ADR 0024 §4.5.7."
        )


class OtlpAdapterConfigEnvTimeoutParseError(OtlpAdapterConfigError):
    """`OTEL_EXPORTER_OTLP_TIMEOUT` ist nicht als Millisekunden-Float parsbar."""

    def __init__(self, raw_value: str) -> None:
        super().__init__(
            f"{_ENV_TIMEOUT_MS}={raw_value!r}: nicht als Millisekunden-Float "
            "parsbar (erwartet: numerischer Wert in ms, OTel-Spec)."
        )


class OtlpAdapterConfigInvalidHeaderError(OtlpAdapterConfigError):
    """`OTEL_EXPORTER_OTLP_HEADERS`-Token ist syntaktisch ungueltig."""

    def __init__(self, token: str, reason: str) -> None:
        super().__init__(f"{_ENV_HEADERS} Token {token!r}: {reason} (erwartet: key=value).")


def _parse_headers(raw: str) -> dict[str, str]:
    """Parst `OTEL_EXPORTER_OTLP_HEADERS` im OTel-Standard-Format.

    Format: ``key1=value1,key2=value2``. Whitespace um Keys/Values wird
    getrimmt. URL-encoded Values (z. B. ``Authorization=Bearer%20token``)
    werden per `urllib.parse.unquote` decodiert — das matched die OTel-
    Spec (Environment-Variable-Specification §3.1; Review-Folge M-5).

    Newline-Characters (`\\n`, `\\r`) in Values sind verboten — Header-
    Injection-Schutz (Review-Folge M-5). Leere Werte sind erlaubt
    (OTel-Spec); leere Keys oder Eintraege ohne ``=`` erzeugen
    `OtlpAdapterConfigInvalidHeaderError`.
    """
    if not raw:
        return {}
    parsed: dict[str, str] = {}
    for token in raw.split(","):
        candidate = token.strip()
        if not candidate:
            continue
        if "=" not in candidate:
            raise OtlpAdapterConfigInvalidHeaderError(candidate, "kein '='-Separator")
        key, _, value = candidate.partition("=")
        key_stripped = key.strip()
        if not key_stripped:
            raise OtlpAdapterConfigInvalidHeaderError(candidate, "leerer Key")
        value_stripped = value.strip()
        decoded_value = unquote(value_stripped)
        if any(ch in decoded_value for ch in ("\n", "\r")):
            raise OtlpAdapterConfigInvalidHeaderError(
                candidate,
                "Newline/Carriage-Return im Value — Header-Injection-Schutz",
            )
        parsed[key_stripped] = decoded_value
    return parsed


def _parse_service_instance_id_from_resource_attrs(raw: str) -> str | None:
    """Liest `service.instance.id` aus `OTEL_RESOURCE_ATTRIBUTES`.

    Format ist identisch zu Headers (`key=value,key=value`). Gibt
    `None` zurueck, wenn der Schluessel fehlt; Parse-Fehler im Resource-
    Attributes-Format selbst sind hier silent (OTel-SDK validiert das
    bei Bedarf eigenstaendig).
    """
    if not raw:
        return None
    for token in raw.split(","):
        candidate = token.strip()
        if "=" not in candidate:
            continue
        key, _, value = candidate.partition("=")
        if key.strip() == "service.instance.id":
            return value.strip() or None
    return None


@dataclass(frozen=True, slots=True)
class OtlpAdapterConfigOverrides:
    """Override-Envelope fuer `OtlpAdapterConfig.from_env` (Slice 027 Paket C).

    Buendelt die optionalen Override-Felder zu einem einzigen Value-Object,
    damit `from_env` kein 7-Kwarg-Aufruf mehr ist. Jedes Feld matched ein
    Klassen-Feld von `OtlpAdapterConfig`; `None` heisst „Env-Var oder
    Default verwenden" (Praezedenz: explizite Overrides > Env-Vars >
    Klassen-Defaults).
    """

    endpoint: str | None = None
    headers: Mapping[str, str] | None = None
    timeout_s: float | None = None
    batch_max_export_size: int | None = None
    service_name: str | None = None
    service_instance_id: str | None = None
    protocol: str | None = None


@dataclass(frozen=True, slots=True)
class OtlpAdapterConfig:
    """Konfiguration fuer den OTLP-Adapter (M3 Welle 6).

    Siehe Modul-Docstring fuer Feld-Bedeutungen und Konstruktions-Pfade.
    Validierung erfolgt in `__post_init__`; `protocol` ist auf die
    Allow-List `{"grpc"}` gepinnt (ADR 0024 §4.5.6).
    """

    endpoint: str = _DEFAULT_ENDPOINT
    headers: Mapping[str, str] = field(default_factory=dict)
    timeout_s: float = _DEFAULT_TIMEOUT_S
    batch_max_export_size: int = _DEFAULT_BATCH_MAX_EXPORT_SIZE
    service_name: str = _DEFAULT_SERVICE_NAME
    service_instance_id: str | None = None
    protocol: str = _DEFAULT_PROTOCOL

    def __post_init__(self) -> None:
        if self.protocol not in _ALLOWED_PROTOCOLS:
            raise OtlpAdapterConfigInvalidProtocolError(self.protocol)
        if not self.endpoint:
            raise OtlpAdapterConfigEmptyFieldError("endpoint")
        if self.timeout_s <= 0:
            raise OtlpAdapterConfigNonPositiveError("timeout_s", self.timeout_s)
        if self.timeout_s < _MIN_TIMEOUT_S:
            raise OtlpAdapterConfigTimeoutTooSmallError(self.timeout_s)
        if self.batch_max_export_size <= 0:
            raise OtlpAdapterConfigNonPositiveError(
                "batch_max_export_size", self.batch_max_export_size
            )
        if self.batch_max_export_size > _MAX_BATCH_MAX_EXPORT_SIZE:
            raise OtlpAdapterConfigBatchTooLargeError(self.batch_max_export_size)
        if not self.service_name:
            raise OtlpAdapterConfigEmptyFieldError("service_name")

    @classmethod
    def from_env(
        cls,
        *,
        overrides: OtlpAdapterConfigOverrides | None = None,
        env: Mapping[str, str] | None = None,
    ) -> OtlpAdapterConfig:
        """Konstruktor mit OTEL_*-Env-Var-Fallback (Slice 027 Paket C).

        Praezedenzregel: `overrides`-Feld != None > Env-Vars > Klassen-
        Defaults. `env`-Parameter erlaubt Test-Injection (statt
        `os.environ`-Patching). Wenn `overrides` selbst `None` ist,
        werden ausschliesslich Env-Vars + Defaults benutzt.
        """
        env_source = env if env is not None else os.environ
        ov = overrides if overrides is not None else OtlpAdapterConfigOverrides()

        resolved_endpoint = (
            ov.endpoint
            if ov.endpoint is not None
            else env_source.get(_ENV_ENDPOINT, _DEFAULT_ENDPOINT)
        )

        resolved_headers: Mapping[str, str]
        if ov.headers is not None:
            resolved_headers = dict(ov.headers)
        else:
            resolved_headers = _parse_headers(env_source.get(_ENV_HEADERS, ""))

        resolved_timeout_s: float
        if ov.timeout_s is not None:
            resolved_timeout_s = ov.timeout_s
        else:
            timeout_env = env_source.get(_ENV_TIMEOUT_MS)
            if timeout_env is not None:
                try:
                    resolved_timeout_s = float(timeout_env) / _MS_PER_S
                except ValueError as exc:
                    raise OtlpAdapterConfigEnvTimeoutParseError(timeout_env) from exc
            else:
                resolved_timeout_s = _DEFAULT_TIMEOUT_S

        resolved_batch_size = (
            ov.batch_max_export_size
            if ov.batch_max_export_size is not None
            else _DEFAULT_BATCH_MAX_EXPORT_SIZE
        )

        resolved_service_name = (
            ov.service_name
            if ov.service_name is not None
            else env_source.get(_ENV_SERVICE_NAME, _DEFAULT_SERVICE_NAME)
        )

        resolved_instance_id: str | None
        if ov.service_instance_id is not None:
            resolved_instance_id = ov.service_instance_id
        else:
            resolved_instance_id = _parse_service_instance_id_from_resource_attrs(
                env_source.get(_ENV_RESOURCE_ATTRIBUTES, "")
            )

        resolved_protocol = (
            ov.protocol
            if ov.protocol is not None
            else env_source.get(_ENV_PROTOCOL, _DEFAULT_PROTOCOL)
        )

        return cls(
            endpoint=resolved_endpoint,
            headers=resolved_headers,
            timeout_s=resolved_timeout_s,
            batch_max_export_size=resolved_batch_size,
            service_name=resolved_service_name,
            service_instance_id=resolved_instance_id,
            protocol=resolved_protocol,
        )
