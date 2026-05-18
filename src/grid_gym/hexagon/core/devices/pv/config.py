"""`PvConfig` mit Initial-Validierung (ADR 0016 §2.6).

PV-Geraet hat in Welle 3 nur ein Pflicht-Parameter:
`rated_power_kw` (Nenn-Erzeugungsleistung, positiv). Welle 5+
Profile/Forecast/Inselnetz-Erweiterungen erweitern die Config
ueber eigene Folge-ADRs.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.errors import GridGymError

_ZERO = Decimal(0)


class PvConfigError(GridGymError):
    """Wurzel der `PvConfig`-Validierungs-Fehler."""


class PvConfigInvalidValueError(PvConfigError):
    """Ein Konfigurationswert ist ausserhalb des erlaubten
    Wertebereichs."""

    def __init__(self, field: str, value: Decimal, constraint: str) -> None:
        super().__init__(f"PvConfig.{field}={value} violates constraint {constraint!r}")


@dataclass(frozen=True, slots=True)
class PvConfig:
    """Statische PV-Parameter (ADR 0016 §2.3).

    - `rated_power_kw` — Nenn-Erzeugungsleistung, > 0 (PV
      erzeugt nicht-negativ; Sign-Konvention §2.2).

    Verstoesse werfen `PvConfigInvalidValueError`.
    """

    rated_power_kw: Decimal

    def __post_init__(self) -> None:
        if self.rated_power_kw <= _ZERO:
            raise PvConfigInvalidValueError("rated_power_kw", self.rated_power_kw, "> 0")
