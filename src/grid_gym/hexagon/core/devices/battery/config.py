"""`BatteryConfig` mit Initial-Validierung (`GG-BESS-008`).

Vor Simulationsstart validiert: Kapazitaet positiv, SOC-Grenzen
konsistent, Initial-SOC in [min, max]-Bereich, Leistungsgrenzen
positiv, Wirkungsgrade in (0, 1], Ramp-Limit positiv. Verstoesse
werfen `BatteryConfigError`-Subklassen — keine stillen Akzeptanzen.

Decimal-Praezision: Werte werden im Konstruktor NICHT quantisiert
— Eingangs-Quantisierung ist Adapter-Verantwortung. `BatteryDevice`
selbst arbeitet mit der vollen Decimal-Praezision; Telemetrie-
Output quantisiert auf 6 Nachkommastellen (`GG-DATA-005`).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from grid_gym.hexagon.core.errors import GridGymError

_ZERO = Decimal(0)
_HUNDRED = Decimal(100)
_ONE = Decimal(1)


class BatteryConfigError(GridGymError):
    """Wurzel der `BatteryConfig`-Validierungs-Fehler (`GG-BESS-008`)."""


class BatteryConfigInvalidValueError(BatteryConfigError):
    """Ein einzelner Konfigurationswert ist ausserhalb des
    erlaubten Wertebereichs."""

    def __init__(self, field: str, value: Decimal, constraint: str) -> None:
        super().__init__(f"BatteryConfig.{field}={value} violates constraint {constraint!r}")


class BatteryConfigInconsistentRangeError(BatteryConfigError):
    """SOC-Grenzen sind nicht konsistent (z. B. `min_soc_pct >=
    max_soc_pct` oder `initial_soc_pct` ausserhalb des Intervalls).

    Wird mit drei Decimals + Kontext-String konstruiert; die Message-
    Bildung passiert hier (statt am Aufruferort) — `TRY003` zufrieden.
    """

    def __init__(self, field: str, value: Decimal, range_description: str) -> None:
        super().__init__(f"BatteryConfig.{field}={value} inconsistent with {range_description}")


@dataclass(frozen=True, slots=True)
class BatteryConfig:
    """Statische Battery-Parameter (`GG-BESS-001..005, 008`).

    Felder mit Wertebereich-Vertrag (Pruefung in `__post_init__`):

    - `capacity_kwh` — Nennkapazitaet, > 0.
    - `initial_soc_pct` — Start-SOC in Prozent, [min_soc_pct,
      max_soc_pct].
    - `min_soc_pct` / `max_soc_pct` — SOC-Grenzen in Prozent, je
      [0, 100]; `min_soc_pct < max_soc_pct`.
    - `max_charge_kw` / `max_discharge_kw` — Leistungsgrenzen,
      beide > 0.
    - `charge_efficiency` / `discharge_efficiency` — Wirkungsgrade,
      jeweils (0, 1].
    - `ramp_kw_per_s` — Leistungsaenderung pro Sekunde, > 0.

    Verstoesse werfen typisierte `BatteryConfigError`-Subklassen
    (`BatteryConfigInvalidValueError`/`BatteryConfigInconsistentRangeError`).
    """

    capacity_kwh: Decimal
    initial_soc_pct: Decimal
    min_soc_pct: Decimal
    max_soc_pct: Decimal
    max_charge_kw: Decimal
    max_discharge_kw: Decimal
    charge_efficiency: Decimal
    discharge_efficiency: Decimal
    ramp_kw_per_s: Decimal

    def __post_init__(self) -> None:
        # Reduziert C901-Komplexitaet, indem die Pruefungen tabellarisch
        # gefuehrt werden. Reihenfolge ist load-bearing: Wertebereich-
        # Checks vor Konsistenz-Checks, damit Inkonsistenz-Fehler immer
        # auf bereits gueltige Einzelwerte aufbauen.
        positive: tuple[tuple[str, Decimal], ...] = (
            ("capacity_kwh", self.capacity_kwh),
            ("max_charge_kw", self.max_charge_kw),
            ("max_discharge_kw", self.max_discharge_kw),
            ("ramp_kw_per_s", self.ramp_kw_per_s),
        )
        for field, value in positive:
            if value <= _ZERO:
                raise BatteryConfigInvalidValueError(field, value, "> 0")

        pct_in_zero_hundred: tuple[tuple[str, Decimal], ...] = (
            ("min_soc_pct", self.min_soc_pct),
            ("max_soc_pct", self.max_soc_pct),
        )
        for field, value in pct_in_zero_hundred:
            if not (_ZERO <= value <= _HUNDRED):
                raise BatteryConfigInvalidValueError(field, value, "in [0, 100]")

        efficiencies: tuple[tuple[str, Decimal], ...] = (
            ("charge_efficiency", self.charge_efficiency),
            ("discharge_efficiency", self.discharge_efficiency),
        )
        for field, value in efficiencies:
            if not (_ZERO < value <= _ONE):
                raise BatteryConfigInvalidValueError(field, value, "in (0, 1]")

        self._validate_consistency()

    def _validate_consistency(self) -> None:
        if self.min_soc_pct >= self.max_soc_pct:
            raise BatteryConfigInconsistentRangeError(
                "min_soc_pct",
                self.min_soc_pct,
                f"max_soc_pct={self.max_soc_pct} (min must be < max)",
            )
        if not (self.min_soc_pct <= self.initial_soc_pct <= self.max_soc_pct):
            raise BatteryConfigInconsistentRangeError(
                "initial_soc_pct",
                self.initial_soc_pct,
                f"[min_soc_pct={self.min_soc_pct}, max_soc_pct={self.max_soc_pct}]",
            )

    @property
    def min_soc_kwh(self) -> Decimal:
        """SOC-Untergrenze in kWh — `min_soc_pct/100 * capacity_kwh`."""
        return self.min_soc_pct * self.capacity_kwh / _HUNDRED

    @property
    def max_soc_kwh(self) -> Decimal:
        """SOC-Obergrenze in kWh."""
        return self.max_soc_pct * self.capacity_kwh / _HUNDRED

    @property
    def initial_soc_kwh(self) -> Decimal:
        """Initialer Energieinhalt in kWh."""
        return self.initial_soc_pct * self.capacity_kwh / _HUNDRED
