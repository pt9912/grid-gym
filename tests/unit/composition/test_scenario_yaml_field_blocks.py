"""Tests fuer die YAML-Decimal-Coercion der Battery-Field-Envelope-Bloecke
(Slice 077 S3, ADR 0077).

Der bess-ems-E2E deckte auf: `_decimal_block_from_params` erwartet `Decimal` in den
verschachtelten `thermal`/`health`/`dc_bus`/`reactive`-Bloecken, aber der YAML-Coercer
rekursierte nicht in sie → die Bloecke waren nicht via YAML ladbar. Dieser Test pinnt
die block-scoped Rekursion + den End-to-End-Beweis (coerced params bauen ein
`BatteryDevice` ohne `WrongTypeError`).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.devices.battery import BatteryDevice
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.scenario_yaml import ScenarioYamlDecimalCoercionError, coerce_scenario_mapping
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom


def _battery_params(**block_overrides: object) -> dict[str, object]:
    return {
        "capacity_kwh": "100",
        "initial_soc_pct": "50",
        "min_soc_pct": "0",
        "max_soc_pct": "100",
        "max_charge_kw": "50",
        "max_discharge_kw": "50",
        "charge_efficiency": "1",
        "discharge_efficiency": "1",
        "ramp_kw_per_s": "100",
        "thermal": {
            "ambient_temp_c": "25",
            "thermal_rise_c_at_full_load": "15",
            "thermal_time_constant_s": "600",
        },
        "health": {"initial_soh_pct": "99", "degradation_pct_per_full_cycle": "0"},
        "dc_bus": {
            "nominal_voltage_v": "800",
            "ocv_soc_slope_v": "0",
            "internal_resistance_ohm": "0",
        },
        "reactive": {"power_factor": "0.95"},
        **block_overrides,
    }


def _scenario(params: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "s", "name": "n"},
        "simulation": {"tick_ms": 1000, "duration_s": 10, "seed": 0},
        "devices": [{"id": "single-bess-1", "type": "battery", "params": params}],
    }


def test_field_envelope_blocks_are_coerced_to_decimal() -> None:
    coerced = coerce_scenario_mapping(_scenario(_battery_params()))
    params = coerced["devices"][0]["params"]
    assert params["dc_bus"]["nominal_voltage_v"] == Decimal("800")
    assert isinstance(params["dc_bus"]["nominal_voltage_v"], Decimal)
    assert params["health"]["initial_soh_pct"] == Decimal("99")
    assert params["thermal"]["ambient_temp_c"] == Decimal("25")
    assert params["reactive"]["power_factor"] == Decimal("0.95")


def test_coerced_params_build_battery_device() -> None:
    # End-to-End: die coerced Bloecke bauen ein BatteryDevice ohne WrongTypeError.
    coerced = coerce_scenario_mapping(_scenario(_battery_params()))
    params = coerced["devices"][0]["params"]
    device = BatteryDevice()
    device.initialize(
        ScenarioDevice(id="single-bess-1", type="battery", params=params),
        FixedSeedRandom(seed=0),
    )
    assert device.device_id == "single-bess-1"


def test_malformed_decimal_in_block_raises_typed() -> None:
    bad = _battery_params(reactive={"power_factor": "not-a-number"})
    with pytest.raises(ScenarioYamlDecimalCoercionError):
        coerce_scenario_mapping(_scenario(bad))
