"""Unit-Tests fuer das env-gated Field-Publish-Wiring (ADR 0075 §2.3,
Slice 073 C4).

`_field_publish_adapter_from_env(run_id)` liest ``GRID_GYM_FIELD_PUBLISH_MQTT_BROKER``
und konstruiert bei Bedarf einen `MqttFieldPublishAdapter` mit run-eindeutiger
`client_id`. `_parse_broker_endpoint` parst ``host[:port]`` / ``[ipv6]:port``
**typisiert** (Review-Fix #2: kein bare `ValueError` → kein Lifespan-Crash).
"""

from __future__ import annotations

import pytest

from grid_gym.adapters.driven.field_publish_mqtt import (
    MqttFieldPublishAdapter,
    MqttFieldPublishConfigError,
)
from grid_gym.composition._demo_scenario_setup import (
    _FIELD_PUBLISH_MQTT_BROKER_ENV_VAR,
    _field_publish_adapter_from_env,
    _parse_broker_endpoint,
)


def test_env_unset_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset → `None` → Driver skippt Fan-out (byte-identisch)."""
    monkeypatch.delenv(_FIELD_PUBLISH_MQTT_BROKER_ENV_VAR, raising=False)
    assert _field_publish_adapter_from_env("run-1") is None


def test_env_set_builds_adapter_with_run_unique_client_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`host:port` → Adapter mit run-eindeutiger client_id (Review-Fix #3)."""
    monkeypatch.setenv(_FIELD_PUBLISH_MQTT_BROKER_ENV_VAR, "broker.example:1884")
    adapter = _field_publish_adapter_from_env("run-xyz")
    assert isinstance(adapter, MqttFieldPublishAdapter)
    assert "run-xyz" in adapter._config.client_id


def test_env_without_port_uses_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Nur `host` → Default-Port, Adapter konstruiert."""
    monkeypatch.setenv(_FIELD_PUBLISH_MQTT_BROKER_ENV_VAR, "broker.example")
    assert isinstance(_field_publish_adapter_from_env("run-1"), MqttFieldPublishAdapter)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("host", ("host", 1883)),
        ("host:1884", ("host", 1884)),
        ("host:", ("host", 1883)),  # trailing colon → Default-Port
        ("[::1]:1883", ("::1", 1883)),  # IPv6 mit Klammern + Port
        ("[fe80::1]", ("fe80::1", 1883)),  # IPv6 mit Klammern, kein Port
    ],
)
def test_parse_broker_endpoint_valid(raw: str, expected: tuple[str, int]) -> None:
    assert _parse_broker_endpoint(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "host:abc",  # nicht-numerischer Port (Review-Fix #2: KEIN bare ValueError)
        "::1",  # unklammerte IPv6 (mehrdeutig)
        "[::1",  # unbalancierte Klammer
        "[::1]x",  # Junk nach der Klammer
    ],
)
def test_parse_broker_endpoint_rejects_bad_typed(raw: str) -> None:
    """Fehlkonfig → typisierter `MqttFieldPublishConfigError` (fail-fast,
    kein Lifespan-Crash durch bare `ValueError`)."""
    with pytest.raises(MqttFieldPublishConfigError):
        _parse_broker_endpoint(raw)
