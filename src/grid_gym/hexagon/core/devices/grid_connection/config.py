"""`GridConnectionConfig` mit Initial-Validierung (ADR 0017 §2.1).

GridConnection-Geraet hat in Welle 4a drei Pflicht-Parameter:

- `nominal_voltage_v` — Nennspannung am Anschlusspunkt, > 0.
- `max_import_kw` — Maximaler Import (Sign-Konvention §2.2:
  positive Power), > 0.
- `max_export_kw` — Maximaler Export (Sign-Konvention §2.2:
  negative Power; der Limit-Wert ist hier als positiver
  Betrag gefuehrt), > 0.

Welle 5+ Blindleistung / Spannungsband / Anschlussgrenzen
erweitern die Config ueber eigene Folge-ADRs.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from typing import Final

from grid_gym.hexagon.core.errors import GridGymError

_ZERO = Decimal(0)

NOMINAL_FREQUENCY_HZ: Final[Decimal] = Decimal("50")
"""GG-FAULT-004: Nenn-Netzfrequenz am Anschlusspunkt (50 Hz). Single-
Source-Baseline fuer den `frequency_drop`-Fault — die GridConnection-
Config traegt (Welle-4a) keine Frequenz-Felder; der Fault droppt von
diesem Nennwert (Payload `delta_hz`) bzw. auf einen Payload-
`frequency_hz`-Absolutwert und stellt bei `clear_fault` hierher wieder
her. Modell- und Snapshot-Schicht teilen diese Konstante."""


class GridConnectionConfigError(GridGymError):
    """Wurzel der `GridConnectionConfig`-Validierungs-Fehler."""


class GridConnectionConfigInvalidValueError(GridConnectionConfigError):
    """Ein Konfigurationswert ist ausserhalb des erlaubten
    Wertebereichs."""

    def __init__(self, field: str, value: Decimal, constraint: str) -> None:
        super().__init__(f"GridConnectionConfig.{field}={value} violates constraint {constraint!r}")


@dataclass(frozen=True, slots=True)
class GridConnectionConfig:
    """Statische Netzanschluss-Parameter (ADR 0017 §2.3).

    - `nominal_voltage_v` — Nennspannung, > 0.
    - `max_import_kw` — Import-Cap (positiver Betrag), > 0.
    - `max_export_kw` — Export-Cap (positiver Betrag), > 0.

    Verstoesse werfen `GridConnectionConfigInvalidValueError`.
    """

    nominal_voltage_v: Decimal
    max_import_kw: Decimal
    max_export_kw: Decimal

    def __post_init__(self) -> None:
        if self.nominal_voltage_v <= _ZERO:
            raise GridConnectionConfigInvalidValueError(
                "nominal_voltage_v", self.nominal_voltage_v, "> 0"
            )
        if self.max_import_kw <= _ZERO:
            raise GridConnectionConfigInvalidValueError("max_import_kw", self.max_import_kw, "> 0")
        if self.max_export_kw <= _ZERO:
            raise GridConnectionConfigInvalidValueError("max_export_kw", self.max_export_kw, "> 0")


__all__ = [
    "NOMINAL_FREQUENCY_HZ",
    "GridConnectionConfig",
    "GridConnectionConfigError",
    "GridConnectionConfigInvalidValueError",
]
