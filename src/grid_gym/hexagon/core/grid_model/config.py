"""`GridModelConfig` mit Initial-Validierung (ADR 0019 §2.4a).

GridModel-Pflicht-Parameter (alle `Decimal`):

- Sollwerte: `nominal_frequency_hz` (Default `50.0`),
  `nominal_voltage_v` (Default `400.0`). Beide > 0.
- Sensitivitaeten: `frequency_sensitivity_hz_per_kw`
  (Default `0.001`), `voltage_sensitivity_v_per_kw`
  (Default `0.1`). Beide > 0 (Sign-Konvention: positiver
  Imbalance -> Frequenz/Spannung steigen).
- Clamp-Grenzen: `frequency_clamp_min_hz` (Default `45.0`),
  `frequency_clamp_max_hz` (Default `55.0`),
  `voltage_clamp_min_v` (Default `0.7 * nominal_voltage_v`),
  `voltage_clamp_max_v` (Default `1.3 * nominal_voltage_v`).
  Strikt: `clamp_min < nominal < clamp_max` (Equal-Form
  ausgeschlossen, damit Equilibrium nicht-clampend ist).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.errors import GridGymError

_ZERO = Decimal(0)


class GridModelConfigError(GridGymError):
    """Wurzel der `GridModelConfig`-Validierungs-Fehler."""


class GridModelConfigInvalidValueError(GridModelConfigError):
    """Ein Konfigurationswert ist ausserhalb des erlaubten
    Wertebereichs."""

    def __init__(self, field: str, value: object, constraint: str) -> None:
        super().__init__(f"GridModelConfig.{field}={value!r} violates constraint {constraint!r}")


@dataclass(frozen=True, slots=True)
class GridModelConfig:
    """Statische Netzbilanz-Parameter (ADR 0019 §2.4a).

    Pflicht-Invarianten:

    - `nominal_frequency_hz > 0`.
    - `nominal_voltage_v > 0`.
    - `frequency_sensitivity_hz_per_kw > 0`.
    - `voltage_sensitivity_v_per_kw > 0`.
    - `frequency_clamp_min_hz < nominal_frequency_hz <
      frequency_clamp_max_hz`.
    - `voltage_clamp_min_v < nominal_voltage_v <
      voltage_clamp_max_v`.

    Verstoesse werfen `GridModelConfigInvalidValueError`.
    """

    nominal_frequency_hz: Decimal
    frequency_sensitivity_hz_per_kw: Decimal
    frequency_clamp_min_hz: Decimal
    frequency_clamp_max_hz: Decimal
    nominal_voltage_v: Decimal
    voltage_sensitivity_v_per_kw: Decimal
    voltage_clamp_min_v: Decimal
    voltage_clamp_max_v: Decimal

    def __post_init__(self) -> None:
        if self.nominal_frequency_hz <= _ZERO:
            raise GridModelConfigInvalidValueError(
                "nominal_frequency_hz", self.nominal_frequency_hz, "> 0"
            )
        if self.nominal_voltage_v <= _ZERO:
            raise GridModelConfigInvalidValueError(
                "nominal_voltage_v", self.nominal_voltage_v, "> 0"
            )
        if self.frequency_sensitivity_hz_per_kw <= _ZERO:
            raise GridModelConfigInvalidValueError(
                "frequency_sensitivity_hz_per_kw",
                self.frequency_sensitivity_hz_per_kw,
                "> 0",
            )
        if self.voltage_sensitivity_v_per_kw <= _ZERO:
            raise GridModelConfigInvalidValueError(
                "voltage_sensitivity_v_per_kw",
                self.voltage_sensitivity_v_per_kw,
                "> 0",
            )
        if not (
            self.frequency_clamp_min_hz < self.nominal_frequency_hz < self.frequency_clamp_max_hz
        ):
            raise GridModelConfigInvalidValueError(
                "frequency_clamp_min_hz/nominal/max_hz",
                (
                    self.frequency_clamp_min_hz,
                    self.nominal_frequency_hz,
                    self.frequency_clamp_max_hz,
                ),
                "clamp_min < nominal < clamp_max",
            )
        if not (self.voltage_clamp_min_v < self.nominal_voltage_v < self.voltage_clamp_max_v):
            raise GridModelConfigInvalidValueError(
                "voltage_clamp_min_v/nominal/max_v",
                (
                    self.voltage_clamp_min_v,
                    self.nominal_voltage_v,
                    self.voltage_clamp_max_v,
                ),
                "clamp_min < nominal < clamp_max",
            )


__all__ = [
    "GridModelConfig",
    "GridModelConfigError",
    "GridModelConfigInvalidValueError",
]
