"""`DieselGeneratorConfig` mit Initial-Validierung (ADR 0058 §2.3).

Dieselgenerator (`GG-DEV-018`, M8 Welle 2d). Folgt dem Battery-Muster
([`ADR 0014`]) als dispatchbarer Generator mit endlicher Ressource
(Kraftstoff).

Pflicht-Parameter:

- `max_power_kw` — Nenn-Maximalleistung, `> 0`.
- `min_start_power_kw` — Anfahr-Schwelle, `> 0`, `<= max_power_kw`.
- `min_stop_power_kw` — Abstell-Schwelle (Hysterese), `>= 0`,
  `< min_start_power_kw`.
- `fuel_capacity_l` — Tankgroesse, `> 0`.
- `initial_fuel_l` — Start-Kraftstoff, `0 <= x <= fuel_capacity_l`.
- `fuel_per_kwh_l` — Verbrauch (l/kWh), `> 0`.
- `ramp_kw_per_s` — Leistungsaenderung pro Sekunde, `> 0`.

Verstoesse werfen `DieselGeneratorConfigInvalidValueError` (Einzelwert)
bzw. `DieselGeneratorConfigInconsistentRangeError` (Reihenfolge).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from grid_gym.hexagon.core.errors import GridGymError

_ZERO = Decimal(0)

CONFIG_FIELD_NAMES: Final[tuple[str, ...]] = (
    "max_power_kw",
    "min_start_power_kw",
    "min_stop_power_kw",
    "fuel_capacity_l",
    "initial_fuel_l",
    "fuel_per_kwh_l",
    "ramp_kw_per_s",
)


class DieselGeneratorConfigError(GridGymError):
    """Wurzel der `DieselGeneratorConfig`-Validierungs-Fehler."""


class DieselGeneratorConfigInvalidValueError(DieselGeneratorConfigError):
    """Ein Einzelwert ist ausserhalb des erlaubten Wertebereichs."""

    def __init__(self, field: str, value: Decimal, constraint: str) -> None:
        super().__init__(
            f"DieselGeneratorConfig.{field}={value} violates constraint {constraint!r}"
        )


class DieselGeneratorConfigInconsistentRangeError(DieselGeneratorConfigError):
    """Zwei Werte sind in inkonsistenter Reihenfolge (z. B.
    `min_stop_power_kw >= min_start_power_kw`)."""

    def __init__(self, field: str, value: Decimal, range_description: str) -> None:
        super().__init__(
            f"DieselGeneratorConfig.{field}={value} inconsistent with {range_description}"
        )


@dataclass(frozen=True, slots=True)
class DieselGeneratorConfig:
    """Statische Dieselgenerator-Parameter (ADR 0058 §2.3)."""

    max_power_kw: Decimal
    min_start_power_kw: Decimal
    min_stop_power_kw: Decimal
    fuel_capacity_l: Decimal
    initial_fuel_l: Decimal
    fuel_per_kwh_l: Decimal
    ramp_kw_per_s: Decimal

    def __post_init__(self) -> None:
        positive: tuple[tuple[str, Decimal], ...] = (
            ("max_power_kw", self.max_power_kw),
            ("min_start_power_kw", self.min_start_power_kw),
            ("fuel_capacity_l", self.fuel_capacity_l),
            ("fuel_per_kwh_l", self.fuel_per_kwh_l),
            ("ramp_kw_per_s", self.ramp_kw_per_s),
        )
        for field, value in positive:
            if value <= _ZERO:
                raise DieselGeneratorConfigInvalidValueError(field, value, "> 0")

        non_negative: tuple[tuple[str, Decimal], ...] = (
            ("min_stop_power_kw", self.min_stop_power_kw),
            ("initial_fuel_l", self.initial_fuel_l),
        )
        for field, value in non_negative:
            if value < _ZERO:
                raise DieselGeneratorConfigInvalidValueError(field, value, ">= 0")

        self._validate_consistency()

    def _validate_consistency(self) -> None:
        if self.min_start_power_kw > self.max_power_kw:
            raise DieselGeneratorConfigInconsistentRangeError(
                "min_start_power_kw",
                self.min_start_power_kw,
                f"max_power_kw={self.max_power_kw} (min_start must be <= max)",
            )
        if self.min_stop_power_kw >= self.min_start_power_kw:
            raise DieselGeneratorConfigInconsistentRangeError(
                "min_stop_power_kw",
                self.min_stop_power_kw,
                f"min_start_power_kw={self.min_start_power_kw} (min_stop must be < min_start)",
            )
        if self.initial_fuel_l > self.fuel_capacity_l:
            raise DieselGeneratorConfigInconsistentRangeError(
                "initial_fuel_l",
                self.initial_fuel_l,
                f"fuel_capacity_l={self.fuel_capacity_l} (initial must be <= capacity)",
            )


__all__ = [
    "CONFIG_FIELD_NAMES",
    "DieselGeneratorConfig",
    "DieselGeneratorConfigError",
    "DieselGeneratorConfigInconsistentRangeError",
    "DieselGeneratorConfigInvalidValueError",
]
