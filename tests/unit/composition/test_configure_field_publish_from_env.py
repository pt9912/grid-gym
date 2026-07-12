"""Unit-Tests fuer das env-gated Field-Publish-Wiring (ADR 0075 §2.3,
Slice 073 C4).

`_configure_field_publish_from_env` liest ``GRID_GYM_FIELD_PUBLISH_MQTT_BROKER``
und legt bei Bedarf einen `MqttFieldPublishAdapter` auf ``app.state.field_publish``.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI

from grid_gym.adapters.driven.field_publish_mqtt import MqttFieldPublishAdapter
from grid_gym.composition._demo_scenario_setup import (
    _FIELD_PUBLISH_MQTT_BROKER_ENV_VAR,
    _configure_field_publish_from_env,
)


def test_env_unset_leaves_field_publish_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unset → No-op → ``field_publish`` bleibt ungesetzt (byte-identisch)."""
    monkeypatch.delenv(_FIELD_PUBLISH_MQTT_BROKER_ENV_VAR, raising=False)
    app = FastAPI()
    _configure_field_publish_from_env(app)
    assert getattr(app.state, "field_publish", None) is None


def test_env_set_wires_mqtt_field_publish_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``host:port`` gesetzt → `MqttFieldPublishAdapter` auf app.state."""
    monkeypatch.setenv(_FIELD_PUBLISH_MQTT_BROKER_ENV_VAR, "broker.example:1884")
    app = FastAPI()
    _configure_field_publish_from_env(app)
    assert isinstance(app.state.field_publish, MqttFieldPublishAdapter)


def test_env_set_without_port_uses_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nur ``host`` (kein Port) → Default-Port, Adapter wird konstruiert."""
    monkeypatch.setenv(_FIELD_PUBLISH_MQTT_BROKER_ENV_VAR, "broker.example")
    app = FastAPI()
    _configure_field_publish_from_env(app)
    assert isinstance(app.state.field_publish, MqttFieldPublishAdapter)
