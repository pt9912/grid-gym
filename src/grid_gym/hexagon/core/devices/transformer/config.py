"""`TransformerConfig` mit Initial-Validierung (ADR 0056 §2.3).

Transformator-Geraet (`GG-DEV-016`, M8 Welle 2b). Folgt dem
GridConnection-Set-Power-Muster ([`ADR 0017`]) mit Spannungs-Wandlung +
Verlusten.

Pflicht-Parameter:

- `rated_power_kw` — Nenn-Durchsatz (Saettigungs-/Ueberlast-Referenz), `> 0`.
- `primary_voltage_v` — Nenn-Primaerspannung, `> 0`.
- `turns_ratio` — Wandlungsverhaeltnis `n_p / n_s`, `> 0`.
- `no_load_loss_kw` — Eisen-/Leerlaufverlust (konstant), `>= 0`.
- `load_loss_kw` — Kupfer-/Lastverlust bei Nennlast, `>= 0` (skaliert
  quadratisch mit dem Lastfaktor).

Loss-Felder duerfen `0` sein (ideal-naher Transformator als Test-
Degenerat). Verstoesse werfen `TransformerConfigInvalidValueError`.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from grid_gym.hexagon.core.errors import GridGymError

_ZERO = Decimal(0)

CONFIG_FIELD_NAMES: Final[tuple[str, ...]] = (
    "rated_power_kw",
    "primary_voltage_v",
    "turns_ratio",
    "no_load_loss_kw",
    "load_loss_kw",
)


class TransformerConfigError(GridGymError):
    """Wurzel der `TransformerConfig`-Validierungs-Fehler."""


class TransformerConfigInvalidValueError(TransformerConfigError):
    """Ein Konfigurationswert ist ausserhalb des erlaubten
    Wertebereichs."""

    def __init__(self, field: str, value: Decimal, constraint: str) -> None:
        super().__init__(f"TransformerConfig.{field}={value} violates constraint {constraint!r}")


@dataclass(frozen=True, slots=True)
class TransformerConfig:
    """Statische Transformator-Parameter (ADR 0056 §2.3).

    Verstoesse werfen `TransformerConfigInvalidValueError`.
    """

    rated_power_kw: Decimal
    primary_voltage_v: Decimal
    turns_ratio: Decimal
    no_load_loss_kw: Decimal
    load_loss_kw: Decimal

    def __post_init__(self) -> None:
        positive: tuple[tuple[str, Decimal], ...] = (
            ("rated_power_kw", self.rated_power_kw),
            ("primary_voltage_v", self.primary_voltage_v),
            ("turns_ratio", self.turns_ratio),
        )
        for field, value in positive:
            if value <= _ZERO:
                raise TransformerConfigInvalidValueError(field, value, "> 0")

        non_negative: tuple[tuple[str, Decimal], ...] = (
            ("no_load_loss_kw", self.no_load_loss_kw),
            ("load_loss_kw", self.load_loss_kw),
        )
        for field, value in non_negative:
            if value < _ZERO:
                raise TransformerConfigInvalidValueError(field, value, ">= 0")

    @property
    def secondary_voltage_v(self) -> Decimal:
        """Nenn-Sekundaerspannung (ADR 0056 §2.4): `primary_voltage_v /
        turns_ratio`."""
        return self.primary_voltage_v / self.turns_ratio


__all__ = [
    "CONFIG_FIELD_NAMES",
    "TransformerConfig",
    "TransformerConfigError",
    "TransformerConfigInvalidValueError",
]
