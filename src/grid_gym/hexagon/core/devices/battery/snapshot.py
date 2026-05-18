"""`BatterySnapshot` — Snapshot-Format fuer `BatteryDevice` (ADR 0014).

Layout (`version: int` = 1):

- `config: BatteryConfig` — vollstaendige eingebettete Konfiguration
  (snapshot-self-contained per ADR 0014 §2.2).
- `soc_kwh: Decimal` — aktueller Energieinhalt.
- `current_power_kw: Decimal` — Lade-/Entladestrom nach Ramp.
- `pending_power_kw: Decimal` — letzter `apply_command`-Soll.

`to_dict()` mapped auf `Mapping[str, object]` mit `version` als
Erst-Feld (ADR 0013 §2.4 Konvention). `from_dict()` validiert
via Welle-0a-Codec-Free-Functions; Mismatches werfen typisierte
`SnapshotFormatError`-Subklassen mit `subsystem="battery"`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Self

from grid_gym.hexagon.core.devices.battery.config import BatteryConfig
from grid_gym.hexagon.core.errors import (
    MissingKeysError,
    VersionError,
    WrongTypeError,
)
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_mapping,
    assert_required_keys,
)

SUBSYSTEM: Final[str] = "battery"
SNAPSHOT_VERSION: Final[int] = 1

_TOP_KEYS: Final[frozenset[str]] = frozenset(
    {"version", "config", "soc_kwh", "current_power_kw", "pending_power_kw"}
)
_CONFIG_KEYS: Final[frozenset[str]] = frozenset(
    {
        "capacity_kwh",
        "initial_soc_pct",
        "min_soc_pct",
        "max_soc_pct",
        "max_charge_kw",
        "max_discharge_kw",
        "charge_efficiency",
        "discharge_efficiency",
        "ramp_kw_per_s",
    }
)


@dataclass(frozen=True, slots=True)
class BatterySnapshot:
    """Battery-State zu einem bestimmten Zeitpunkt.

    Wird von `BatteryDevice.snapshot()` als `to_dict()`-Mapping
    emittiert und von `BatteryDevice.from_snapshot()` per
    `from_dict()` rekonstruiert. Roundtrip-Vertrag
    (ADR 0013 §2.4): byte-stabil.
    """

    version: int
    config: BatteryConfig
    soc_kwh: Decimal
    current_power_kw: Decimal
    pending_power_kw: Decimal

    def to_dict(self) -> Mapping[str, object]:
        """Wandelt den Snapshot in ein `Mapping[str, object]` mit
        `version` als Erst-Feld (ADR 0013 §2.4 Konvention).

        Config-Embed: alle BatteryConfig-Felder als geschachteltes
        Dict unter `config`-Key. Reihenfolge-Konvention: Klassen-
        Feld-Reihenfolge aus `BatteryConfig` (lesbar, deterministisch
        ueber dict-Insertion-Order; canonical_json sortiert
        spaeter ohnehin lexikographisch).
        """
        return {
            "version": self.version,
            "config": {
                "capacity_kwh": self.config.capacity_kwh,
                "initial_soc_pct": self.config.initial_soc_pct,
                "min_soc_pct": self.config.min_soc_pct,
                "max_soc_pct": self.config.max_soc_pct,
                "max_charge_kw": self.config.max_charge_kw,
                "max_discharge_kw": self.config.max_discharge_kw,
                "charge_efficiency": self.config.charge_efficiency,
                "discharge_efficiency": self.config.discharge_efficiency,
                "ramp_kw_per_s": self.config.ramp_kw_per_s,
            },
            "soc_kwh": self.soc_kwh,
            "current_power_kw": self.current_power_kw,
            "pending_power_kw": self.pending_power_kw,
        }

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Rekonstruiert einen `BatterySnapshot` aus einem Mapping.

        Wirft typisiert:
        - `MissingKeysError("battery", ...)` bei fehlenden Top-/
          Config-Keys.
        - `WrongTypeError("battery", ...)` bei falschen Typen.
        - `VersionError("battery", expected=1, found=...)` bei
          unbekannter Version.
        """
        assert_required_keys(state, _TOP_KEYS, SUBSYSTEM)

        version = state["version"]
        if isinstance(version, bool) or not isinstance(version, int):
            raise WrongTypeError(SUBSYSTEM, "version", "int", type(version).__name__)
        if version != SNAPSHOT_VERSION:
            raise VersionError(SUBSYSTEM, expected=SNAPSHOT_VERSION, found=version)

        config_state = assert_mapping(state["config"], "config", SUBSYSTEM)
        assert_required_keys(config_state, _CONFIG_KEYS, SUBSYSTEM)
        config = BatteryConfig(
            capacity_kwh=_decimal(config_state, "config.capacity_kwh"),
            initial_soc_pct=_decimal(config_state, "config.initial_soc_pct"),
            min_soc_pct=_decimal(config_state, "config.min_soc_pct"),
            max_soc_pct=_decimal(config_state, "config.max_soc_pct"),
            max_charge_kw=_decimal(config_state, "config.max_charge_kw"),
            max_discharge_kw=_decimal(config_state, "config.max_discharge_kw"),
            charge_efficiency=_decimal(config_state, "config.charge_efficiency"),
            discharge_efficiency=_decimal(config_state, "config.discharge_efficiency"),
            ramp_kw_per_s=_decimal(config_state, "config.ramp_kw_per_s"),
        )

        soc_kwh = _decimal(state, "soc_kwh")
        current_power_kw = _decimal(state, "current_power_kw")
        pending_power_kw = _decimal(state, "pending_power_kw")

        return cls(
            version=version,
            config=config,
            soc_kwh=soc_kwh,
            current_power_kw=current_power_kw,
            pending_power_kw=pending_power_kw,
        )


def _decimal(mapping: Mapping[str, object], path: str) -> Decimal:
    """Holt `mapping[leaf]`, wo `leaf` der letzte Teil von `path`
    nach `.` ist (z. B. `"config.capacity_kwh"` → Key `capacity_kwh`).
    Wirft `WrongTypeError("battery", path, "Decimal", actual)` bei
    Verstoss."""
    leaf = path.rsplit(".", 1)[-1]
    value = mapping[leaf]
    if not isinstance(value, Decimal):
        raise WrongTypeError(SUBSYSTEM, path, "Decimal", type(value).__name__)
    return value


__all__ = [
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "BatterySnapshot",
    "MissingKeysError",
    "VersionError",
    "WrongTypeError",
]
