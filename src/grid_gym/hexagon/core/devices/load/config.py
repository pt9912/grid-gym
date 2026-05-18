"""`LoadConfig` mit Initial-Validierung (ADR 0016 §2.3).

Load-Geraet hat in Welle 3 nur ein Pflicht-Parameter:
`rated_power_kw` (Nenn-Verbrauchsleistung, positiv).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.errors import GridGymError

_ZERO = Decimal(0)


class LoadConfigError(GridGymError):
    """Wurzel der `LoadConfig`-Validierungs-Fehler."""


class LoadConfigInvalidValueError(LoadConfigError):
    """Ein Konfigurationswert ist ausserhalb des erlaubten
    Wertebereichs."""

    def __init__(self, field: str, value: Decimal, constraint: str) -> None:
        super().__init__(f"LoadConfig.{field}={value} violates constraint {constraint!r}")


@dataclass(frozen=True, slots=True)
class LoadConfig:
    """Statische Load-Parameter (ADR 0016 §2.3).

    - `rated_power_kw` — Nenn-Verbrauchsleistung, > 0 (Load
      verbraucht nicht-negativ; Sign-Konvention §2.2).
    """

    rated_power_kw: Decimal

    def __post_init__(self) -> None:
        if self.rated_power_kw <= _ZERO:
            raise LoadConfigInvalidValueError("rated_power_kw", self.rated_power_kw, "> 0")
