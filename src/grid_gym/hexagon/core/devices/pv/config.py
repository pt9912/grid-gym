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

    def __init__(self, field: str, value: object, constraint: str) -> None:
        super().__init__(f"PvConfig.{field}={value} violates constraint {constraint!r}")


# M8-Welle-3c-b-1 (ADR 0063 §2.2): Pflicht-Decimal-Felder der Volt-Var-Kurve
# (Single-Source fuer no-float + Snapshot-Serialisierung).
VOLT_VAR_FIELD_NAMES: tuple[str, ...] = (
    "reference_voltage_v",
    "deadband_v",
    "droop_kvar_per_v",
    "max_kvar",
)


@dataclass(frozen=True, slots=True)
class VoltVarConfig:
    """Volt-Var-Kennlinie Q(U) eines PV-Wechselrichters (M8-Welle-3c-b-1,
    ADR 0063 §2.2).

    Symmetrische Deadband-/Droop-Kurve um `reference_voltage_v`:
    innerhalb `±deadband_v` ist `Q=0`; ausserhalb steigt `|Q|` linear mit
    `droop_kvar_per_v`, geclamped auf `max_kvar`. Sign: hohe Spannung →
    induktiv absorbieren (`-Q`), niedrige → kapazitiv einspeisen (`+Q`).

    Invarianten (Verstoss → `PvConfigInvalidValueError`):
    - alle Felder `Decimal` (GG-DATA-005 no-float).
    - `reference_voltage_v > 0`, `droop_kvar_per_v > 0`, `max_kvar > 0`.
    - `deadband_v >= 0`.
    """

    reference_voltage_v: Decimal
    deadband_v: Decimal
    droop_kvar_per_v: Decimal
    max_kvar: Decimal

    def __post_init__(self) -> None:
        for field_name in VOLT_VAR_FIELD_NAMES:
            value = getattr(self, field_name)
            if not isinstance(value, Decimal):
                raise PvConfigInvalidValueError(
                    f"volt_var.{field_name}", value, f"Decimal (got {type(value).__name__})"
                )
        for positive in ("reference_voltage_v", "droop_kvar_per_v", "max_kvar"):
            if getattr(self, positive) <= _ZERO:
                raise PvConfigInvalidValueError(
                    f"volt_var.{positive}", getattr(self, positive), "> 0"
                )
        if self.deadband_v < _ZERO:
            raise PvConfigInvalidValueError("volt_var.deadband_v", self.deadband_v, ">= 0")

    def reactive_power_kvar(self, grid_voltage_v: Decimal) -> Decimal:
        """Wertet Q(U) gegen die Netzspannung aus (ADR 0063 §2.2)."""
        dv = grid_voltage_v - self.reference_voltage_v
        abs_excess = abs(dv) - self.deadband_v
        if abs_excess <= _ZERO:
            return _ZERO
        magnitude = min(self.droop_kvar_per_v * abs_excess, self.max_kvar)
        if dv > _ZERO:
            return -magnitude
        return magnitude


@dataclass(frozen=True, slots=True)
class PvConfig:
    """Statische PV-Parameter (ADR 0016 §2.3).

    - `rated_power_kw` — Nenn-Erzeugungsleistung, > 0 (PV
      erzeugt nicht-negativ; Sign-Konvention §2.2).
    - `volt_var` — optionale Q(U)-Kennlinie (M8-Welle-3c-b-1, ADR 0063);
      `None` = keine Q-Emission (kein `reactive_power_kvar`-Punkt).

    Verstoesse werfen `PvConfigInvalidValueError`.
    """

    rated_power_kw: Decimal
    volt_var: VoltVarConfig | None = None

    def __post_init__(self) -> None:
        if self.rated_power_kw <= _ZERO:
            raise PvConfigInvalidValueError("rated_power_kw", self.rated_power_kw, "> 0")
        if self.volt_var is not None and not isinstance(self.volt_var, VoltVarConfig):
            raise PvConfigInvalidValueError(
                "volt_var",
                self.volt_var,
                f"None or VoltVarConfig (got {type(self.volt_var).__name__})",
            )
