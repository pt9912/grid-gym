"""`SmartMeterConfig` mit Initial-Validierung (ADR 0018 §2.2).

SmartMeter-Geraet hat in Welle 4b zwei Felder:

- `aggregate_device_ids: tuple[str, ...]` — kanonisch
  sortiert (alphabetisch) und eindeutig. Leer (`()`) ist
  erlaubt; leeres Aggregat liefert `Decimal("0")`.
- `aggregate_metric_name: str` — Metric-Name, ueber den die
  Quellen aufsummiert werden. Default `"power_kw"`. Welle-4b-
  Minimum nutzt den Default; Welle 5 / Post-MVP kann auch
  `"import_kwh"`/`"export_kwh"`/`"soc_kwh"` aktivieren.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from grid_gym.hexagon.core.errors import GridGymError


class SmartMeterConfigError(GridGymError):
    """Wurzel der `SmartMeterConfig`-Validierungs-Fehler."""


class SmartMeterConfigInvalidValueError(SmartMeterConfigError):
    """Ein Konfigurationswert ist ausserhalb des erlaubten
    Wertebereichs."""

    def __init__(self, field_name: str, constraint: str) -> None:
        super().__init__(f"SmartMeterConfig.{field_name} violates constraint {constraint!r}")


@dataclass(frozen=True, slots=True)
class SmartMeterConfig:
    """Statische SmartMeter-Parameter (ADR 0018 §2.2).

    - `aggregate_device_ids` — kanonisch sortiert + eindeutig
      (Welle-1-Konvention; `ValueError`-Domain bei Verstoss).
    - `aggregate_metric_name` — Default `"power_kw"`.

    Verstoesse werfen `SmartMeterConfigInvalidValueError`.
    """

    aggregate_device_ids: tuple[str, ...]
    aggregate_metric_name: str = field(default="power_kw")

    def __post_init__(self) -> None:
        if not isinstance(self.aggregate_device_ids, tuple):
            raise SmartMeterConfigInvalidValueError(
                "aggregate_device_ids", "must be tuple[str, ...]"
            )
        if any(not isinstance(item, str) for item in self.aggregate_device_ids):
            raise SmartMeterConfigInvalidValueError(
                "aggregate_device_ids", "all entries must be str"
            )
        if any(item == "" for item in self.aggregate_device_ids):
            raise SmartMeterConfigInvalidValueError("aggregate_device_ids", "no empty-string IDs")
        sorted_ids = tuple(sorted(self.aggregate_device_ids))
        if self.aggregate_device_ids != sorted_ids:
            raise SmartMeterConfigInvalidValueError(
                "aggregate_device_ids", "must be alphabetically sorted (canonical)"
            )
        if len(set(self.aggregate_device_ids)) != len(self.aggregate_device_ids):
            raise SmartMeterConfigInvalidValueError("aggregate_device_ids", "must be unique")
        if not isinstance(self.aggregate_metric_name, str):
            raise SmartMeterConfigInvalidValueError("aggregate_metric_name", "must be str")
        if self.aggregate_metric_name == "":
            raise SmartMeterConfigInvalidValueError("aggregate_metric_name", "must not be empty")
        # Welle-4b-Review H-1: Telemetrie-Emission (model.py) hardcoded
        # auf `aggregated_power_kw` + Unit `kW`. Andere Metric-Namen
        # wuerden zwar korrekt summiert, aber unter dem falschen
        # Telemetrie-Label emittiert. Welle 4b verlangt deshalb den
        # Default; Welle 5 / Post-MVP aktiviert das Forward-Looking-
        # Feld zusammen mit einer dynamischen `_emit_telemetry`-
        # Emission.
        if self.aggregate_metric_name != "power_kw":
            raise SmartMeterConfigInvalidValueError(
                "aggregate_metric_name",
                "must be 'power_kw' in Welle 4b (Welle 5+ activates other metrics)",
            )


__all__ = [
    "SmartMeterConfig",
    "SmartMeterConfigError",
    "SmartMeterConfigInvalidValueError",
]
