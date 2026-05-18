"""Tests fuer `BatteryConfig` (`GG-BESS-008` Initial-Validierung).

Pinnt:
- Happy-Path-Konstruktion mit allen Pflichtfeldern.
- Negativ-Pfade fuer jeden Validierungs-Vertrag (capacity_kwh > 0,
  SOC-Bereich [0, 100], min < max, initial in [min, max],
  Leistungsgrenzen positiv, Wirkungsgrade (0, 1], Ramp > 0).
- Derived Properties (`min_soc_kwh`/`max_soc_kwh`/`initial_soc_kwh`).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.devices.battery.config import (
    BatteryConfig,
    BatteryConfigInconsistentRangeError,
    BatteryConfigInvalidValueError,
)


def _valid_config(**overrides: Decimal) -> BatteryConfig:
    """Konstruiert eine valide Config; Overrides ueberschreiben
    Einzelfelder fuer Negativ-Tests."""
    base = dict(
        capacity_kwh=Decimal("1000"),
        initial_soc_pct=Decimal("50"),
        min_soc_pct=Decimal("10"),
        max_soc_pct=Decimal("90"),
        max_charge_kw=Decimal("500"),
        max_discharge_kw=Decimal("500"),
        charge_efficiency=Decimal("0.95"),
        discharge_efficiency=Decimal("0.95"),
        ramp_kw_per_s=Decimal("50"),
    )
    base.update(overrides)
    return BatteryConfig(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Happy-Path
# ---------------------------------------------------------------------------


def test_valid_config_constructs() -> None:
    config = _valid_config()
    assert config.capacity_kwh == Decimal("1000")
    assert config.initial_soc_pct == Decimal("50")


def test_config_is_frozen() -> None:
    from dataclasses import FrozenInstanceError

    config = _valid_config()
    with pytest.raises(FrozenInstanceError):
        config.capacity_kwh = Decimal("500")  # type: ignore[misc]


def test_derived_soc_kwh_properties() -> None:
    config = _valid_config()
    assert config.min_soc_kwh == Decimal("100")  # 10% * 1000kWh
    assert config.max_soc_kwh == Decimal("900")  # 90% * 1000kWh
    assert config.initial_soc_kwh == Decimal("500")  # 50% * 1000kWh


# ---------------------------------------------------------------------------
# Negativ-Pfade — Wertebereich-Verstoesse
# ---------------------------------------------------------------------------


def test_zero_capacity_rejected() -> None:
    with pytest.raises(BatteryConfigInvalidValueError) as exc_info:
        _valid_config(capacity_kwh=Decimal("0"))
    assert "capacity_kwh" in str(exc_info.value)


def test_negative_capacity_rejected() -> None:
    with pytest.raises(BatteryConfigInvalidValueError):
        _valid_config(capacity_kwh=Decimal("-1"))


def test_min_soc_pct_above_100_rejected() -> None:
    with pytest.raises(BatteryConfigInvalidValueError) as exc_info:
        _valid_config(min_soc_pct=Decimal("110"))
    assert "min_soc_pct" in str(exc_info.value)


def test_max_soc_pct_above_100_rejected() -> None:
    with pytest.raises(BatteryConfigInvalidValueError):
        _valid_config(max_soc_pct=Decimal("110"))


def test_negative_min_soc_pct_rejected() -> None:
    with pytest.raises(BatteryConfigInvalidValueError):
        _valid_config(min_soc_pct=Decimal("-5"))


def test_min_geq_max_soc_pct_rejected() -> None:
    with pytest.raises(BatteryConfigInconsistentRangeError) as exc_info:
        _valid_config(min_soc_pct=Decimal("50"), max_soc_pct=Decimal("50"))
    assert "min_soc_pct" in str(exc_info.value)
    assert "max_soc_pct" in str(exc_info.value)


def test_initial_below_min_soc_pct_rejected() -> None:
    with pytest.raises(BatteryConfigInconsistentRangeError) as exc_info:
        _valid_config(initial_soc_pct=Decimal("5"), min_soc_pct=Decimal("10"))
    assert "initial_soc_pct" in str(exc_info.value)


def test_initial_above_max_soc_pct_rejected() -> None:
    with pytest.raises(BatteryConfigInconsistentRangeError):
        _valid_config(initial_soc_pct=Decimal("95"), max_soc_pct=Decimal("90"))


def test_zero_max_charge_rejected() -> None:
    with pytest.raises(BatteryConfigInvalidValueError) as exc_info:
        _valid_config(max_charge_kw=Decimal("0"))
    assert "max_charge_kw" in str(exc_info.value)


def test_negative_max_discharge_rejected() -> None:
    with pytest.raises(BatteryConfigInvalidValueError):
        _valid_config(max_discharge_kw=Decimal("-100"))


def test_zero_charge_efficiency_rejected() -> None:
    with pytest.raises(BatteryConfigInvalidValueError) as exc_info:
        _valid_config(charge_efficiency=Decimal("0"))
    assert "charge_efficiency" in str(exc_info.value)


def test_charge_efficiency_above_one_rejected() -> None:
    with pytest.raises(BatteryConfigInvalidValueError):
        _valid_config(charge_efficiency=Decimal("1.05"))


def test_discharge_efficiency_negative_rejected() -> None:
    with pytest.raises(BatteryConfigInvalidValueError):
        _valid_config(discharge_efficiency=Decimal("-0.1"))


def test_efficiency_exactly_one_is_allowed() -> None:
    """Grenzfall: 100% Wirkungsgrad (verlustfrei) ist zulaessig
    (`(0, 1]`-Bereich, geschlossene 1)."""
    config = _valid_config(charge_efficiency=Decimal("1"), discharge_efficiency=Decimal("1"))
    assert config.charge_efficiency == Decimal("1")


def test_ramp_zero_rejected() -> None:
    with pytest.raises(BatteryConfigInvalidValueError) as exc_info:
        _valid_config(ramp_kw_per_s=Decimal("0"))
    assert "ramp_kw_per_s" in str(exc_info.value)


def test_ramp_negative_rejected() -> None:
    with pytest.raises(BatteryConfigInvalidValueError):
        _valid_config(ramp_kw_per_s=Decimal("-10"))
