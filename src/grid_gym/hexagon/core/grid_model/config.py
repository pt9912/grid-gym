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


# M8-Welle-3b (ADR 0061 §2.1): Pflicht-Decimal-Felder des Transformer-
# Constraint-Blocks (Single-Source-of-Truth fuer no-float-Pruefung +
# Snapshot-Serialisierung).
TRANSFORMER_LIMIT_FIELD_NAMES: tuple[str, ...] = (
    "max_apparent_power_kva",
    "ambient_temp_c",
    "top_oil_rise_rated_c",
    "hot_spot_rise_rated_c",
    "top_oil_time_constant_s",
    "hot_spot_limit_c",
)


@dataclass(frozen=True, slots=True)
class TransformerLimitConfig:
    """Transformator-Grenzwert-Block fuer das Netzbilanzmodell
    (M8 Welle 3b, ADR 0061 §2.1) — **Netz-Grenze**, klar abgegrenzt vom
    Transformer-Geraet (ADR 0056, Per-Device-Saettigung).

    Vereinfachtes Single-Zonen-Thermomodell (ADR 0061 §2.2): die
    Top-Oil-Zeitkonstante `top_oil_time_constant_s` traegt die Zeit-Strom-
    Kennlinie (kurze Ueberlast erlaubt, dauerhafte nicht).

    Pflicht-Invarianten (Verstoss → `GridModelConfigInvalidValueError`):

    - alle Felder `Decimal` (GG-DATA-005 no-float).
    - `max_apparent_power_kva > 0` (Nennscheinleistung, Basis fuer
      `load_pu`).
    - `top_oil_rise_rated_c > 0`, `hot_spot_rise_rated_c > 0`,
      `top_oil_time_constant_s > 0`.
    - `hot_spot_limit_c > ambient_temp_c` (sonst loest das Modell bei
      Nulllast aus).
    """

    max_apparent_power_kva: Decimal
    ambient_temp_c: Decimal
    top_oil_rise_rated_c: Decimal
    hot_spot_rise_rated_c: Decimal
    top_oil_time_constant_s: Decimal
    hot_spot_limit_c: Decimal

    def __post_init__(self) -> None:
        for field_name in TRANSFORMER_LIMIT_FIELD_NAMES:
            value = getattr(self, field_name)
            if not isinstance(value, Decimal):
                raise GridModelConfigInvalidValueError(
                    f"transformer_limit.{field_name}",
                    value,
                    f"Decimal (got {type(value).__name__})",
                )
        for positive_field in (
            "max_apparent_power_kva",
            "top_oil_rise_rated_c",
            "hot_spot_rise_rated_c",
            "top_oil_time_constant_s",
        ):
            if getattr(self, positive_field) <= _ZERO:
                raise GridModelConfigInvalidValueError(
                    f"transformer_limit.{positive_field}",
                    getattr(self, positive_field),
                    "> 0",
                )
        if self.hot_spot_limit_c <= self.ambient_temp_c:
            raise GridModelConfigInvalidValueError(
                "transformer_limit.hot_spot_limit_c",
                (self.hot_spot_limit_c, self.ambient_temp_c),
                "hot_spot_limit_c > ambient_temp_c",
            )


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
    # M8-Welle-3a (ADR 0060 §2.1): additive Inselnetz-Felder. Default
    # `False`/`None` = netzgekoppelt = bit-genau heutiges Verhalten. Die
    # Existenz des referenzierten Geraets wird NICHT hier geprueft (Config
    # kennt keine Device-Registry) — das macht das TickLoop-Wiring
    # (ADR 0060 §2.3).
    is_islanded: bool = False
    forming_device_id: str | None = None
    # M8-Welle-3b (ADR 0061 §2.1): optionaler Transformer-Constraint-Layer.
    # `None` (Default) = kein Layer = bit-genau heutiges Verhalten. Eigene
    # Frozen-Dataclass mit eigener Validierung (oben).
    transformer_limit: TransformerLimitConfig | None = None

    def __post_init__(self) -> None:
        # Welle-5a-Review M-4: Decimal-Typ-Pruefung an allen
        # Direkt-Konstruktor-Pfaden (`from_dict` ist via
        # `assert_decimal` bereits geschuetzt; YAML-Adapter und
        # Test-Helper koennen jedoch float-Werte einschleichen).
        # GG-DATA-005 no-float-Invariante: kein float an
        # Datengrenzen.
        for field_name in (
            "nominal_frequency_hz",
            "frequency_sensitivity_hz_per_kw",
            "frequency_clamp_min_hz",
            "frequency_clamp_max_hz",
            "nominal_voltage_v",
            "voltage_sensitivity_v_per_kw",
            "voltage_clamp_min_v",
            "voltage_clamp_max_v",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, Decimal):
                raise GridModelConfigInvalidValueError(
                    field_name, value, f"Decimal (got {type(value).__name__})"
                )
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
        self._validate_island_presence()
        if self.transformer_limit is not None and not isinstance(
            self.transformer_limit, TransformerLimitConfig
        ):
            raise GridModelConfigInvalidValueError(
                "transformer_limit",
                self.transformer_limit,
                f"None or TransformerLimitConfig (got {type(self.transformer_limit).__name__})",
            )

    def _validate_island_presence(self) -> None:
        """M8-Welle-3a (ADR 0060 §2.1): Inselnetz-Presence-Invarianten.

        Reine Format-/Presence-Pruefung am Config-Rand (kein
        Device-Existenz-Check — der lebt im TickLoop-Wiring, ADR 0060
        §2.3). `bool`-Check VOR der Biconditional, damit ein
        int-Subclass-Schmuggel nicht als truthy durchrutscht.
        """
        if not isinstance(self.is_islanded, bool):
            raise GridModelConfigInvalidValueError(
                "is_islanded",
                self.is_islanded,
                f"bool (got {type(self.is_islanded).__name__})",
            )
        if self.forming_device_id is not None and (
            not isinstance(self.forming_device_id, str) or not self.forming_device_id
        ):
            raise GridModelConfigInvalidValueError(
                "forming_device_id",
                self.forming_device_id,
                "None or non-empty str",
            )
        # Biconditional: Forming-ID gesetzt genau dann wenn Inselnetz.
        if self.is_islanded and self.forming_device_id is None:
            raise GridModelConfigInvalidValueError(
                "forming_device_id",
                self.forming_device_id,
                "set when is_islanded=True",
            )
        if not self.is_islanded and self.forming_device_id is not None:
            raise GridModelConfigInvalidValueError(
                "forming_device_id",
                self.forming_device_id,
                "None when is_islanded=False",
            )


__all__ = [
    "TRANSFORMER_LIMIT_FIELD_NAMES",
    "GridModelConfig",
    "GridModelConfigError",
    "GridModelConfigInvalidValueError",
    "TransformerLimitConfig",
]
