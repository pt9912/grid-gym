"""`EvChargerConfig` mit Initial-Validierung (ADR 0055 §2.3).

EV-Ladepunkt (`GG-DEV-015`, M8 Welle 2a). Kombiniert das Battery-SoC-
Muster (endlicher Fahrzeug-Akku) mit dem GridConnection-Set-Power-Muster
(steuerbare, bidirektionale Leistung am Anschlusspunkt).

Pflicht-Parameter (alle `> 0`):

- `max_charge_kw` — Lade-Cap.
- `max_discharge_kw` — V2G-Entlade-Cap (V2G ist durchgaengig aktiv).
- `nominal_voltage_v` — Nennspannung am Anschlusspunkt.
- `battery_capacity_kwh` — Kapazitaet des verbundenen Fahrzeug-Akkus.

CC/CV-Schwelle:

- `cv_phase_start_soc` — SoC-Schwelle des CC→CV-Uebergangs, `0 < x <= 0.99`.
  Die Obergrenze `0.99` haelt den Taper-Nenner `1 - cv_phase_start_soc`
  endlich (ADR 0055 §2.3/§2.4).

Init-Parameter (Scenario-`params`, Teil des `scenario_hash`):

- `initial_soc` — Start-SoC `0 .. 1` (Default `0.5`). `initialize`
  rechnet ihn zu `initial_stored_kwh = initial_soc * battery_capacity_kwh`.
- `initial_plug_state` — `"plugged"`/`"unplugged"` (Default `"unplugged"`).

Verstoesse werfen `EvChargerConfigInvalidValueError` — keine stillen
Akzeptanzen. Eingangs-Quantisierung ist Adapter-Verantwortung; der
`EvChargerDevice` rechnet mit voller Decimal-Praezision.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from grid_gym.hexagon.core.errors import GridGymError

_ZERO = Decimal(0)
_ONE = Decimal(1)
_CV_START_MAX = Decimal("0.99")

PLUG_STATE_PLUGGED: Final[str] = "plugged"
PLUG_STATE_UNPLUGGED: Final[str] = "unplugged"
PLUG_STATES: Final[frozenset[str]] = frozenset({PLUG_STATE_PLUGGED, PLUG_STATE_UNPLUGGED})
"""ADR 0055 §2.2: erstes nicht-numerisches Geraete-Zustands-Enum
(Snapshot-String, Telemetrie `1`/`0`)."""

DEFAULT_INITIAL_SOC: Final[Decimal] = Decimal("0.5")
DEFAULT_INITIAL_PLUG_STATE: Final[str] = PLUG_STATE_UNPLUGGED


class EvChargerConfigError(GridGymError):
    """Wurzel der `EvChargerConfig`-Validierungs-Fehler."""


class EvChargerConfigInvalidValueError(EvChargerConfigError):
    """Ein Konfigurationswert ist ausserhalb des erlaubten
    Wertebereichs."""

    def __init__(self, field: str, value: object, constraint: str) -> None:
        super().__init__(f"EvChargerConfig.{field}={value} violates constraint {constraint!r}")


@dataclass(frozen=True, slots=True)
class EvChargerConfig:
    """Statische EV-Ladepunkt-Parameter (ADR 0055 §2.3).

    Felder mit Wertebereich-Vertrag (Pruefung in `__post_init__`):

    - `max_charge_kw` / `max_discharge_kw` / `nominal_voltage_v` /
      `battery_capacity_kwh` — alle `> 0`.
    - `cv_phase_start_soc` — `0 < x <= 0.99`.
    - `initial_soc` — `0 <= x <= 1` (Default `0.5`).
    - `initial_plug_state` — `"plugged"`/`"unplugged"` (Default
      `"unplugged"`).

    Verstoesse werfen `EvChargerConfigInvalidValueError`.
    """

    max_charge_kw: Decimal
    max_discharge_kw: Decimal
    nominal_voltage_v: Decimal
    battery_capacity_kwh: Decimal
    cv_phase_start_soc: Decimal
    initial_soc: Decimal = DEFAULT_INITIAL_SOC
    initial_plug_state: str = DEFAULT_INITIAL_PLUG_STATE

    def __post_init__(self) -> None:
        positive: tuple[tuple[str, Decimal], ...] = (
            ("max_charge_kw", self.max_charge_kw),
            ("max_discharge_kw", self.max_discharge_kw),
            ("nominal_voltage_v", self.nominal_voltage_v),
            ("battery_capacity_kwh", self.battery_capacity_kwh),
        )
        for field, value in positive:
            if value <= _ZERO:
                raise EvChargerConfigInvalidValueError(field, value, "> 0")

        if not (_ZERO < self.cv_phase_start_soc <= _CV_START_MAX):
            raise EvChargerConfigInvalidValueError(
                "cv_phase_start_soc", self.cv_phase_start_soc, "in (0, 0.99]"
            )

        if not (_ZERO <= self.initial_soc <= _ONE):
            raise EvChargerConfigInvalidValueError("initial_soc", self.initial_soc, "in [0, 1]")

        if self.initial_plug_state not in PLUG_STATES:
            raise EvChargerConfigInvalidValueError(
                "initial_plug_state", self.initial_plug_state, "in {'plugged', 'unplugged'}"
            )

    @property
    def initial_stored_kwh(self) -> Decimal:
        """Initialer Energieinhalt des Fahrzeug-Akkus in kWh
        (ADR 0055 §2.3): `initial_soc * battery_capacity_kwh`."""
        return self.initial_soc * self.battery_capacity_kwh


__all__ = [
    "DEFAULT_INITIAL_PLUG_STATE",
    "DEFAULT_INITIAL_SOC",
    "PLUG_STATES",
    "PLUG_STATE_PLUGGED",
    "PLUG_STATE_UNPLUGGED",
    "EvChargerConfig",
    "EvChargerConfigError",
    "EvChargerConfigInvalidValueError",
]
