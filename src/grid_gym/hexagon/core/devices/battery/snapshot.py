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
    VersionError,
    WrongTypeError,
)
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_decimal,
    assert_int,
    assert_mapping,
    assert_required_keys,
    assert_str,
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
# M3-Welle-2 (ADR 0025 §2.2): `fault_state` ist optional und
# additiv (Backward-Compat fuer Welle-1-Snapshots ohne Fault-
# Block). Fehlt der Key, defaultet alle Flags auf `False`.
_FAULT_STATE_KEY: Final[str] = "fault_state"
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
    # M3-Welle-2 (ADR 0025 §2.2): Fault-Flag additiv. Default
    # `False` haelt Snapshot-Roundtrip mit Welle-1-Snapshots
    # ohne `fault_state`-Block kompatibel.
    cell_failure_active: bool = False

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
            # M3-Welle-2 (ADR 0025 §2.2): additiver fault_state-
            # Block. Welle-1-Snapshots ohne diesen Key bleiben
            # roundtrip-faehig (from_dict defaultet auf False).
            _FAULT_STATE_KEY: {
                "cell_failure_active": self.cell_failure_active,
            },
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

        device_id = assert_str(state["device_id"], "device_id", SUBSYSTEM)
        run_id = assert_str(state["run_id"], "run_id", SUBSYSTEM)
        sequence = assert_int(state["sequence"], "sequence", SUBSYSTEM)

        config_state = assert_mapping(state["config"], "config", SUBSYSTEM)
        assert_required_keys(config_state, _CONFIG_KEYS, SUBSYSTEM)
        try:
            config = BatteryConfig(
                capacity_kwh=_config_decimal(config_state, "capacity_kwh"),
                initial_soc_pct=_config_decimal(config_state, "initial_soc_pct"),
                min_soc_pct=_config_decimal(config_state, "min_soc_pct"),
                max_soc_pct=_config_decimal(config_state, "max_soc_pct"),
                max_charge_kw=_config_decimal(config_state, "max_charge_kw"),
                max_discharge_kw=_config_decimal(config_state, "max_discharge_kw"),
                charge_efficiency=_config_decimal(config_state, "charge_efficiency"),
                discharge_efficiency=_config_decimal(config_state, "discharge_efficiency"),
                ramp_kw_per_s=_config_decimal(config_state, "ramp_kw_per_s"),
            )
        except BatteryConfigError as err:
            # Welle-2-Review M-5: BatteryConfigError ist nicht Teil
            # der SnapshotFormatError-Hierarchie — Welle-6-Aufrufer
            # wuerden typisiert nur die generische Familie fangen.
            raise WrongTypeError(SUBSYSTEM, "config", "valid", str(err)) from err

        soc_kwh = assert_decimal(state["soc_kwh"], "soc_kwh", SUBSYSTEM)
        current_power_kw = assert_decimal(state["current_power_kw"], "current_power_kw", SUBSYSTEM)
        pending_power_kw = assert_decimal(state["pending_power_kw"], "pending_power_kw", SUBSYSTEM)

        # M3-Welle-2 (ADR 0025 §2.2): fault_state ist optional;
        # Welle-1-Snapshots ohne den Block defaultet alle Flags
        # auf False.
        cell_failure_active = False
        if _FAULT_STATE_KEY in state:
            fault_state = assert_mapping(state[_FAULT_STATE_KEY], _FAULT_STATE_KEY, SUBSYSTEM)
            raw_flag = fault_state.get("cell_failure_active", False)
            if not isinstance(raw_flag, bool):
                raise WrongTypeError(
                    SUBSYSTEM,
                    f"{_FAULT_STATE_KEY}.cell_failure_active",
                    "bool",
                    type(raw_flag).__name__,
                )
            cell_failure_active = raw_flag

        return cls(
            version=version,
            device_id=device_id,
            run_id=run_id,
            sequence=sequence,
            config=config,
            soc_kwh=soc_kwh,
            current_power_kw=current_power_kw,
            pending_power_kw=pending_power_kw,
            cell_failure_active=cell_failure_active,
        )


def _config_decimal(config_state: Mapping[str, object], leaf: str) -> Decimal:
    """Battery-Config-Schluessel-Helper.

    Mapt `leaf` → `"config.<leaf>"` als Pfad fuer den
    `WrongTypeError`-Path (Welle-3-Review L-1 Migration: dedup auf
    Codec-`assert_decimal` mit Battery-spezifischem Pfad-Prefix).
    """
    return assert_decimal(config_state[leaf], f"config.{leaf}", SUBSYSTEM)


# Welle-2-Review L-4: Error-Klassen NICHT re-exportiert — Aufrufer
# importieren sie aus `grid_gym.hexagon.core.errors` (kanonischer
# Pfad). Re-Export aus dem Sub-System-Modul wuerde die Import-
# Graph-Drift verstaerken; Welle 3+ PV/Load-Snapshots kopieren
# das Pattern nicht.
__all__ = [
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "BatterySnapshot",
]
