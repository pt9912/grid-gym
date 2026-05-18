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

from grid_gym.hexagon.core.devices.battery.config import (
    BatteryConfig,
    BatteryConfigError,
)
from grid_gym.hexagon.core.errors import (
    MissingKeysError,
    VersionError,
    WrongTypeError,
)
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_int,
    assert_mapping,
    assert_required_keys,
)

SUBSYSTEM: Final[str] = "battery"
SNAPSHOT_VERSION: Final[int] = 1

_TOP_KEYS: Final[frozenset[str]] = frozenset(
    {
        "version",
        "device_id",
        "run_id",
        "sequence",
        "config",
        "soc_kwh",
        "current_power_kw",
        "pending_power_kw",
    }
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
    (ADR 0013 §2.4): byte-stabil; ADR 0014 §2.2 Welle-2-Review-
    Schaerfung C-1: Snapshot ist **self-sufficient** —
    `from_dict(...)` + `BatteryDevice.from_snapshot(...)` liefert
    eine sofort nutzbare Device-Instanz (kein Re-`initialize`).
    """

    version: int
    device_id: str
    run_id: str
    sequence: int
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
            "device_id": self.device_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
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
        - `WrongTypeError("battery", ...)` bei falschen Typen
          (inkl. eingebetteter `BatteryConfig`-Validierungs-
          Verstoesse — siehe ADR 0014 §2.2 M-5-Schaerfung: der
          BatteryConfigError wird gefangen und als WrongTypeError
          reraised, damit Welle-6-Aufrufer typisiert auf der
          SnapshotFormatError-Ebene catchen).
        - `VersionError("battery", expected=1, found=...)` bei
          unbekannter Version.
        """
        assert_required_keys(state, _TOP_KEYS, SUBSYSTEM)

        version = assert_int(state["version"], "version", SUBSYSTEM)
        if version != SNAPSHOT_VERSION:
            raise VersionError(SUBSYSTEM, expected=SNAPSHOT_VERSION, found=version)

        device_id = _assert_str(state, "device_id")
        run_id = _assert_str(state, "run_id")
        sequence = assert_int(state["sequence"], "sequence", SUBSYSTEM)

        config_state = assert_mapping(state["config"], "config", SUBSYSTEM)
        assert_required_keys(config_state, _CONFIG_KEYS, SUBSYSTEM)
        try:
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
        except BatteryConfigError as err:
            # Welle-2-Review M-5: BatteryConfigError ist nicht Teil
            # der SnapshotFormatError-Hierarchie — Welle-6-Aufrufer
            # wuerden typisiert nur die generische Familie fangen.
            raise WrongTypeError(SUBSYSTEM, "config", "valid", str(err)) from err

        soc_kwh = _decimal(state, "soc_kwh")
        current_power_kw = _decimal(state, "current_power_kw")
        pending_power_kw = _decimal(state, "pending_power_kw")

        return cls(
            version=version,
            device_id=device_id,
            run_id=run_id,
            sequence=sequence,
            config=config,
            soc_kwh=soc_kwh,
            current_power_kw=current_power_kw,
            pending_power_kw=pending_power_kw,
        )


def _assert_str(mapping: Mapping[str, object], key: str) -> str:
    value = mapping[key]
    if not isinstance(value, str):
        raise WrongTypeError(SUBSYSTEM, key, "str", type(value).__name__)
    return value


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
