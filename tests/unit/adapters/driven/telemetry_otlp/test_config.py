"""Tests fuer `OtlpAdapterConfig` (M3 Welle 6 C1.3a, ADR 0024 §4.5.6).

Pinnt:

- Default-Werte der frozen-dataclass.
- `protocol`-Allow-List `{"grpc"}` (ADR 0024 §4.5.6) — alle anderen
  Werte fangen `OtlpAdapterConfigError`.
- Validation der numerischen Felder (`timeout_s > 0`,
  `batch_max_export_size > 0`).
- Leerstring-Validation fuer `endpoint` und `service_name`.
- `from_env`-Praezedenz: explizite Kwargs > Env-Vars > Klassen-Defaults.
- OTEL-Spec-konformes Parsing von `OTEL_EXPORTER_OTLP_HEADERS` und
  `service.instance.id` aus `OTEL_RESOURCE_ATTRIBUTES`.
- OTEL-Timeout in Millisekunden → Konfig in Sekunden.
- Frozen-Invariante (Mutation faengt `FrozenInstanceError`).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from grid_gym.adapters.driven.telemetry_otlp import (
    OtlpAdapterConfig,
    OtlpAdapterConfigError,
    OtlpAdapterConfigOverrides,
)


# --- Defaults ----------------------------------------------------------------


def test_default_construction() -> None:
    config = OtlpAdapterConfig()
    assert config.endpoint == "http://localhost:4317"
    assert config.headers == {}
    assert config.timeout_s == pytest.approx(10.0)
    assert config.batch_max_export_size == 512
    assert config.service_name == "grid-gym"
    assert config.service_instance_id is None
    assert config.protocol == "grpc"


def test_explicit_construction_overrides_all_defaults() -> None:
    config = OtlpAdapterConfig(
        endpoint="http://collector:4317",
        headers={"x-auth": "token"},
        timeout_s=5.0,
        batch_max_export_size=128,
        service_name="grid-gym-sim",
        service_instance_id="instance-42",
        protocol="grpc",
    )
    assert config.endpoint == "http://collector:4317"
    assert dict(config.headers) == {"x-auth": "token"}
    assert config.timeout_s == pytest.approx(5.0)
    assert config.batch_max_export_size == 128
    assert config.service_name == "grid-gym-sim"
    assert config.service_instance_id == "instance-42"
    assert config.protocol == "grpc"


# --- Frozen invariant --------------------------------------------------------


def test_frozen_instance_rejects_mutation() -> None:
    config = OtlpAdapterConfig()
    with pytest.raises(FrozenInstanceError):
        config.endpoint = "http://other:4317"  # type: ignore[misc]


# --- Protocol allow-list (ADR 0024 §4.5.6) -----------------------------------


def test_protocol_grpc_accepted() -> None:
    config = OtlpAdapterConfig(protocol="grpc")
    assert config.protocol == "grpc"


@pytest.mark.parametrize(
    "invalid_protocol",
    ["http", "http/protobuf", "GRPC", "", "tcp", "unknown"],
)
def test_protocol_outside_allow_list_raises(invalid_protocol: str) -> None:
    with pytest.raises(OtlpAdapterConfigError) as exc_info:
        OtlpAdapterConfig(protocol=invalid_protocol)
    msg = str(exc_info.value)
    assert "protocol=" in msg
    assert "ADR 0024 §4.5.6" in msg


# --- Numeric validation ------------------------------------------------------


@pytest.mark.parametrize("invalid_timeout", [0.0, -1.0, -0.001])
def test_timeout_must_be_positive(invalid_timeout: float) -> None:
    with pytest.raises(OtlpAdapterConfigError, match="timeout_s"):
        OtlpAdapterConfig(timeout_s=invalid_timeout)


@pytest.mark.parametrize("sub_second_timeout", [0.001, 0.1, 0.5, 0.999])
def test_timeout_below_min_raises(sub_second_timeout: float) -> None:
    """Review-Folge M-1: `timeout_s < 1.0` faengt der Floor (sonst wuerde
    `int(0.5) == 0` einen Null-Timeout an die OTel-Exporter weiterreichen).
    """
    with pytest.raises(OtlpAdapterConfigError) as exc_info:
        OtlpAdapterConfig(timeout_s=sub_second_timeout)
    msg = str(exc_info.value)
    assert "M-1" in msg or "Sekunden-Aufloesung" in msg


def test_timeout_at_min_accepted() -> None:
    """`timeout_s == 1.0` ist der niedrigste erlaubte Wert."""
    config = OtlpAdapterConfig(timeout_s=1.0)
    assert config.timeout_s == pytest.approx(1.0)


@pytest.mark.parametrize("invalid_size", [0, -1, -512])
def test_batch_max_export_size_must_be_positive(invalid_size: int) -> None:
    with pytest.raises(OtlpAdapterConfigError, match="batch_max_export_size"):
        OtlpAdapterConfig(batch_max_export_size=invalid_size)


def test_batch_max_export_size_at_otel_limit_accepted() -> None:
    """OTel-`max_queue_size` ist 2048 — Werte am Limit sind erlaubt."""
    config = OtlpAdapterConfig(batch_max_export_size=2048)
    assert config.batch_max_export_size == 2048


@pytest.mark.parametrize("oversized", [2049, 4096, 8192])
def test_batch_max_export_size_above_otel_limit_raises(oversized: int) -> None:
    """Review-Folge H-3: Werte ueber dem OTel-`max_queue_size`-Limit (2048)
    werden gefangen, statt im Compose-Smoke silent gedrosselt zu werden.
    """
    with pytest.raises(OtlpAdapterConfigError) as exc_info:
        OtlpAdapterConfig(batch_max_export_size=oversized)
    msg = str(exc_info.value)
    assert "2048" in msg
    assert "H-3" in msg or "max_queue_size" in msg


# --- String-field validation -------------------------------------------------


def test_empty_endpoint_raises() -> None:
    with pytest.raises(OtlpAdapterConfigError, match="endpoint"):
        OtlpAdapterConfig(endpoint="")


def test_empty_service_name_raises() -> None:
    with pytest.raises(OtlpAdapterConfigError, match="service_name"):
        OtlpAdapterConfig(service_name="")


# --- `from_env` precedence ---------------------------------------------------


def test_from_env_empty_falls_back_to_defaults() -> None:
    config = OtlpAdapterConfig.from_env(env={})
    assert config.endpoint == "http://localhost:4317"
    assert config.headers == {}
    assert config.timeout_s == pytest.approx(10.0)
    assert config.service_name == "grid-gym"
    assert config.service_instance_id is None
    assert config.protocol == "grpc"


def test_from_env_reads_endpoint() -> None:
    config = OtlpAdapterConfig.from_env(
        env={"OTEL_EXPORTER_OTLP_ENDPOINT": "http://collector:4317"},
    )
    assert config.endpoint == "http://collector:4317"


def test_from_env_reads_service_name() -> None:
    config = OtlpAdapterConfig.from_env(
        env={"OTEL_SERVICE_NAME": "grid-gym-api"},
    )
    assert config.service_name == "grid-gym-api"


def test_from_env_reads_protocol() -> None:
    config = OtlpAdapterConfig.from_env(env={"OTEL_EXPORTER_OTLP_PROTOCOL": "grpc"})
    assert config.protocol == "grpc"


def test_from_env_rejects_invalid_protocol() -> None:
    with pytest.raises(OtlpAdapterConfigError, match="protocol="):
        OtlpAdapterConfig.from_env(
            env={"OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf"},
        )


def test_from_env_kwargs_override_env() -> None:
    config = OtlpAdapterConfig.from_env(
        overrides=OtlpAdapterConfigOverrides(
            endpoint="http://override:4317",
            service_name="override-name",
        ),
        env={
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://env:4317",
            "OTEL_SERVICE_NAME": "env-name",
        },
    )
    assert config.endpoint == "http://override:4317"
    assert config.service_name == "override-name"


# --- `from_env` timeout parsing (milliseconds → seconds) ---------------------


def test_from_env_timeout_in_ms_converted_to_seconds() -> None:
    config = OtlpAdapterConfig.from_env(env={"OTEL_EXPORTER_OTLP_TIMEOUT": "5000"})
    assert config.timeout_s == pytest.approx(5.0)


def test_from_env_timeout_float_parsed() -> None:
    config = OtlpAdapterConfig.from_env(env={"OTEL_EXPORTER_OTLP_TIMEOUT": "2500.5"})
    assert config.timeout_s == pytest.approx(2.5005)


def test_from_env_invalid_timeout_raises() -> None:
    with pytest.raises(OtlpAdapterConfigError, match="OTEL_EXPORTER_OTLP_TIMEOUT"):
        OtlpAdapterConfig.from_env(env={"OTEL_EXPORTER_OTLP_TIMEOUT": "not-a-number"})


def test_from_env_timeout_zero_rejected_by_post_init() -> None:
    # Env-Var ist syntaktisch parsbar, semantisch aber ungueltig — fangs in
    # `__post_init__`.
    with pytest.raises(OtlpAdapterConfigError, match="timeout_s"):
        OtlpAdapterConfig.from_env(env={"OTEL_EXPORTER_OTLP_TIMEOUT": "0"})


# --- `from_env` headers parsing ----------------------------------------------


def test_from_env_headers_single_entry() -> None:
    config = OtlpAdapterConfig.from_env(
        env={"OTEL_EXPORTER_OTLP_HEADERS": "x-auth=token"},
    )
    assert dict(config.headers) == {"x-auth": "token"}


def test_from_env_headers_multiple_entries() -> None:
    config = OtlpAdapterConfig.from_env(
        env={"OTEL_EXPORTER_OTLP_HEADERS": "x-auth=token,x-tenant=demo"},
    )
    assert dict(config.headers) == {"x-auth": "token", "x-tenant": "demo"}


def test_from_env_headers_with_whitespace_trimmed() -> None:
    config = OtlpAdapterConfig.from_env(
        env={"OTEL_EXPORTER_OTLP_HEADERS": "  x-auth = token , x-tenant=demo "},
    )
    assert dict(config.headers) == {"x-auth": "token", "x-tenant": "demo"}


def test_from_env_headers_empty_value_allowed() -> None:
    # OTel-Spec laesst leere Werte zu; nur leerer Key oder fehlendes `=`
    # ist Fehler.
    config = OtlpAdapterConfig.from_env(
        env={"OTEL_EXPORTER_OTLP_HEADERS": "x-flag="},
    )
    assert dict(config.headers) == {"x-flag": ""}


def test_from_env_headers_missing_equals_raises() -> None:
    with pytest.raises(OtlpAdapterConfigError, match="OTEL_EXPORTER_OTLP_HEADERS"):
        OtlpAdapterConfig.from_env(
            env={"OTEL_EXPORTER_OTLP_HEADERS": "no-equals-sign"},
        )


def test_from_env_headers_empty_key_raises() -> None:
    with pytest.raises(OtlpAdapterConfigError, match="leerer Key"):
        OtlpAdapterConfig.from_env(env={"OTEL_EXPORTER_OTLP_HEADERS": "=value"})


# --- Headers URL-decode + Newline-Reject (Review-Folge M-5) ------------------


def test_from_env_headers_url_decoded() -> None:
    """OTel-Spec §3.1: Header-Values sind URL-encoded; `%20` → space."""
    config = OtlpAdapterConfig.from_env(
        env={"OTEL_EXPORTER_OTLP_HEADERS": "Authorization=Bearer%20token"},
    )
    assert dict(config.headers) == {"Authorization": "Bearer token"}


def test_from_env_headers_url_decoded_special_chars() -> None:
    """`%2C` (Komma), `%3D` (Gleichheit), `%2F` (Slash) werden decoded."""
    config = OtlpAdapterConfig.from_env(
        env={"OTEL_EXPORTER_OTLP_HEADERS": "x-token=abc%2Cdef%3Dghi"},
    )
    assert dict(config.headers) == {"x-token": "abc,def=ghi"}


@pytest.mark.parametrize(
    "raw_header",
    [
        "x-auth=token\nX-Inject: evil",
        "x-auth=token\r\nX-Inject: evil",
        "x-auth=before%0Aafter",  # URL-encoded LF — nach decode immer noch \n
        "x-auth=before%0D%0Aafter",  # URL-encoded CRLF
    ],
)
def test_from_env_headers_newline_in_value_raises(raw_header: str) -> None:
    """Review-Folge M-5: Newlines im Header-Value sind Injection-Vehikel.

    Pruefung passiert NACH `urlencode-decode` — `%0A` und `%0D` werden
    zu `\\n`/`\\r` aufgeloest und dann gefangen.
    """
    with pytest.raises(OtlpAdapterConfigError, match="Header-Injection"):
        OtlpAdapterConfig.from_env(env={"OTEL_EXPORTER_OTLP_HEADERS": raw_header})


def test_from_env_headers_kwarg_overrides_env() -> None:
    config = OtlpAdapterConfig.from_env(
        overrides=OtlpAdapterConfigOverrides(headers={"x-override": "yes"}),
        env={"OTEL_EXPORTER_OTLP_HEADERS": "x-env=no"},
    )
    assert dict(config.headers) == {"x-override": "yes"}


# --- `from_env` service.instance.id parsing from OTEL_RESOURCE_ATTRIBUTES ----


def test_from_env_service_instance_id_from_resource_attrs() -> None:
    config = OtlpAdapterConfig.from_env(
        env={
            "OTEL_RESOURCE_ATTRIBUTES": "service.instance.id=instance-uuid-42",
        },
    )
    assert config.service_instance_id == "instance-uuid-42"


def test_from_env_service_instance_id_in_multi_attr() -> None:
    config = OtlpAdapterConfig.from_env(
        env={
            "OTEL_RESOURCE_ATTRIBUTES": (
                "deployment.environment=prod,service.instance.id=uuid-42,service.version=1.0"
            ),
        },
    )
    assert config.service_instance_id == "uuid-42"


def test_from_env_missing_service_instance_id_returns_none() -> None:
    config = OtlpAdapterConfig.from_env(
        env={"OTEL_RESOURCE_ATTRIBUTES": "deployment.environment=prod"},
    )
    assert config.service_instance_id is None


def test_from_env_empty_service_instance_id_returns_none() -> None:
    config = OtlpAdapterConfig.from_env(
        env={"OTEL_RESOURCE_ATTRIBUTES": "service.instance.id="},
    )
    assert config.service_instance_id is None


def test_from_env_service_instance_id_kwarg_overrides() -> None:
    config = OtlpAdapterConfig.from_env(
        overrides=OtlpAdapterConfigOverrides(service_instance_id="kwarg-uuid"),
        env={"OTEL_RESOURCE_ATTRIBUTES": "service.instance.id=env-uuid"},
    )
    assert config.service_instance_id == "kwarg-uuid"


# --- `from_env` default env-source ------------------------------------------


def test_from_env_default_env_source_is_os_environ(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ohne `env`-Kwarg muss `os.environ` als Quelle verwendet werden."""
    monkeypatch.setenv("OTEL_SERVICE_NAME", "from-os-environ")
    config = OtlpAdapterConfig.from_env()
    assert config.service_name == "from-os-environ"
