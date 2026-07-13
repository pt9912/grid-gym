"""Unit-Tests fuer das env-gated bess-ems-Publisher-Wiring (Slice 077 S2, ADR 0078).

`_bess_ems_adapter_from_env(run_id, scenario)` liest ``GRID_GYM_BESS_EMS_MQTT_BROKER``
und konstruiert bei Bedarf einen `BessEmsFieldPublishAdapter` mit run-eindeutiger
`client_id` — **nach** dem §2.5-Fail-fast gegen die Battery-Field-Envelope-Bloecke.
"""

from __future__ import annotations

import pytest

from grid_gym.adapters.driven.field_publish_bess_ems import (
    BessEmsFieldPublishAdapter,
    BessEmsFieldPublishConfigEndpointError,
    BessEmsFieldPublishConfigMissingFieldBlocksError,
)
from grid_gym.composition._demo_scenario_setup import (
    _BESS_EMS_BROKER_ENV_VAR,
    _bess_ems_adapter_from_env,
)
from grid_gym.hexagon.core.domain.scenario import (
    Scenario,
    ScenarioDevice,
    ScenarioMetadata,
    ScenarioSimulation,
)

_FULL_BLOCKS: dict[str, object] = {
    "thermal": {},
    "health": {},
    "dc_bus": {},
    "reactive": {},
}


def _scenario(*devices: ScenarioDevice) -> Scenario:
    return Scenario(
        schema_version="grid-gym.scenario.v1",
        metadata=ScenarioMetadata(id="s-1", name="bess-ems-test"),
        simulation=ScenarioSimulation(tick_ms=1000, duration_s=10, seed=0),
        devices=devices,
        events=(),
        replay=None,
        faults=(),
    )


def _battery(device_id: str = "battery-1", **params: object) -> ScenarioDevice:
    return ScenarioDevice(id=device_id, type="battery", params=params)


def _load() -> ScenarioDevice:
    return ScenarioDevice(id="load-1", type="load", params={"rated_power_kw": 30})


def test_env_unset_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_BESS_EMS_BROKER_ENV_VAR, raising=False)
    assert _bess_ems_adapter_from_env("run-1", _scenario(_battery(**_FULL_BLOCKS))) is None


def test_env_set_full_blocks_builds_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_BESS_EMS_BROKER_ENV_VAR, "broker.example:1884")
    adapter = _bess_ems_adapter_from_env("run-xyz", _scenario(_battery(**_FULL_BLOCKS)))
    assert isinstance(adapter, BessEmsFieldPublishAdapter)
    assert "run-xyz" in adapter._config.client_id


def test_missing_field_block_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_BESS_EMS_BROKER_ENV_VAR, "broker.example")
    # Battery ohne `reactive`-Block → §2.5-Fail-fast.
    partial = {k: v for k, v in _FULL_BLOCKS.items() if k != "reactive"}
    with pytest.raises(BessEmsFieldPublishConfigMissingFieldBlocksError) as exc:
        _bess_ems_adapter_from_env("run-1", _scenario(_battery(**partial)))
    assert exc.value.device_id == "battery-1"
    assert "reactive" in exc.value.missing_blocks


def test_non_battery_devices_do_not_trip_fail_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ein Load-Geraet (keine Fault-Surface) loest den §2.5-Check nicht aus.
    monkeypatch.setenv(_BESS_EMS_BROKER_ENV_VAR, "broker.example")
    adapter = _bess_ems_adapter_from_env("run-1", _scenario(_battery(**_FULL_BLOCKS), _load()))
    assert isinstance(adapter, BessEmsFieldPublishAdapter)


def test_malformed_endpoint_raises_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_BESS_EMS_BROKER_ENV_VAR, "host:not-a-port")
    with pytest.raises(BessEmsFieldPublishConfigEndpointError):
        _bess_ems_adapter_from_env("run-1", _scenario(_battery(**_FULL_BLOCKS)))
