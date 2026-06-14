"""`WindTurbineConfig` mit Initial-Validierung (ADR 0057 §2.3).

Windkraftanlage (`GG-DEV-017`, M8 Welle 2c). Folgt dem PV-Muster
([`ADR 0016`]) als command-loser Generator; der Windgeschwindigkeits-
Eingang ist stochastisch (seeded `RandomPort`, ADR 0057 §2.4).

Pflicht-Parameter:

- `rated_power_kw` — Nennleistung, `> 0`.
- `cut_in_speed_ms` — Einschalt-Windgeschwindigkeit, `>= 0`.
- `rated_speed_ms` — Nennwindgeschwindigkeit, `> cut_in_speed_ms`.
- `cut_out_speed_ms` — Abschalt-Windgeschwindigkeit, `> rated_speed_ms`.
- `min_wind_speed_ms` — untere Grenze der stochastischen Ziehung, `>= 0`.
- `max_wind_speed_ms` — obere Grenze, `>= min_wind_speed_ms` (Gleichheit
  erlaubt = konstanter Wind).

Verstoesse werfen `WindTurbineConfigInvalidValueError` (Einzelwert) bzw.
`WindTurbineConfigInconsistentRangeError` (Reihenfolge).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from grid_gym.hexagon.core.errors import GridGymError

_ZERO = Decimal(0)

CONFIG_FIELD_NAMES: Final[tuple[str, ...]] = (
    "rated_power_kw",
    "cut_in_speed_ms",
    "rated_speed_ms",
    "cut_out_speed_ms",
    "min_wind_speed_ms",
    "max_wind_speed_ms",
)


class WindTurbineConfigError(GridGymError):
    """Wurzel der `WindTurbineConfig`-Validierungs-Fehler."""


class WindTurbineConfigInvalidValueError(WindTurbineConfigError):
    """Ein Einzelwert ist ausserhalb des erlaubten Wertebereichs."""

    def __init__(self, field: str, value: Decimal, constraint: str) -> None:
        super().__init__(f"WindTurbineConfig.{field}={value} violates constraint {constraint!r}")


class WindTurbineConfigInconsistentRangeError(WindTurbineConfigError):
    """Zwei Werte sind in inkonsistenter Reihenfolge (z. B.
    `rated_speed_ms <= cut_in_speed_ms`)."""

    def __init__(self, field: str, value: Decimal, range_description: str) -> None:
        super().__init__(f"WindTurbineConfig.{field}={value} inconsistent with {range_description}")


@dataclass(frozen=True, slots=True)
class WindTurbineConfig:
    """Statische Windkraftanlagen-Parameter (ADR 0057 §2.3)."""

    rated_power_kw: Decimal
    cut_in_speed_ms: Decimal
    rated_speed_ms: Decimal
    cut_out_speed_ms: Decimal
    min_wind_speed_ms: Decimal
    max_wind_speed_ms: Decimal

    def __post_init__(self) -> None:
        if self.rated_power_kw <= _ZERO:
            raise WindTurbineConfigInvalidValueError("rated_power_kw", self.rated_power_kw, "> 0")

        non_negative: tuple[tuple[str, Decimal], ...] = (
            ("cut_in_speed_ms", self.cut_in_speed_ms),
            ("min_wind_speed_ms", self.min_wind_speed_ms),
        )
        for field, value in non_negative:
            if value < _ZERO:
                raise WindTurbineConfigInvalidValueError(field, value, ">= 0")

        self._validate_consistency()

    def _validate_consistency(self) -> None:
        if self.rated_speed_ms <= self.cut_in_speed_ms:
            raise WindTurbineConfigInconsistentRangeError(
                "rated_speed_ms",
                self.rated_speed_ms,
                f"cut_in_speed_ms={self.cut_in_speed_ms} (rated must be > cut_in)",
            )
        if self.cut_out_speed_ms <= self.rated_speed_ms:
            raise WindTurbineConfigInconsistentRangeError(
                "cut_out_speed_ms",
                self.cut_out_speed_ms,
                f"rated_speed_ms={self.rated_speed_ms} (cut_out must be > rated)",
            )
        if self.max_wind_speed_ms < self.min_wind_speed_ms:
            raise WindTurbineConfigInconsistentRangeError(
                "max_wind_speed_ms",
                self.max_wind_speed_ms,
                f"min_wind_speed_ms={self.min_wind_speed_ms} (max must be >= min)",
            )


__all__ = [
    "CONFIG_FIELD_NAMES",
    "WindTurbineConfig",
    "WindTurbineConfigError",
    "WindTurbineConfigInconsistentRangeError",
    "WindTurbineConfigInvalidValueError",
]
