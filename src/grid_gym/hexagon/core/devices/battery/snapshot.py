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
    CELL_FIELD_NAMES,
    THERMAL_FIELD_NAMES,
    BatteryConfig,
    BatteryConfigError,
    CellConfig,
    ThermalConfig,
)
from grid_gym.hexagon.core.errors import (
    VersionError,
    WrongTypeError,
)
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_decimal,
    assert_int,
    assert_mapping,
    assert_optional_fault_flag,
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
# M8-Welle-4a (ADR 0065 §2.5): Pflicht-Keys des opt-in thermal-Blocks.
_THERMAL_KEYS: Final[frozenset[str]] = frozenset(THERMAL_FIELD_NAMES)
# M8-Welle-4b (ADR 0066 §2.5): Pflicht-Keys des opt-in cell-Blocks.
_CELL_KEYS: Final[frozenset[str]] = frozenset(CELL_FIELD_NAMES)


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
    # M8-Welle-4a (ADR 0065 §2.5): akkumulierte Pack-Temperatur des opt-in
    # Thermomodells; `None` ohne Thermo-Block (opt-in serialisiert, kein
    # Versions-Bump — strenger als der immer emittierte `fault_state`-Block).
    temperature_celsius: Decimal | None = None
    # M8-Welle-4b (ADR 0066 §2.5): letzte Zellspannungen des opt-in Zell-
    # Modells; leeres Tuple ohne Zell-Block bzw. vor dem ersten Tick (opt-in
    # serialisiert nur bei Non-Empty, kein Versions-Bump).
    cell_voltages_v: tuple[Decimal, ...] = ()

    def to_dict(self) -> Mapping[str, object]:
        """Wandelt den Snapshot in ein `Mapping[str, object]` mit
        `version` als Erst-Feld (ADR 0013 §2.4 Konvention).

        Config-Embed: alle BatteryConfig-Felder als geschachteltes
        Dict unter `config`-Key. Reihenfolge-Konvention: Klassen-
        Feld-Reihenfolge aus `BatteryConfig` (lesbar, deterministisch
        ueber dict-Insertion-Order; canonical_json sortiert
        spaeter ohnehin lexikographisch).

        M8-Welle-4a (ADR 0065 §2.5): der opt-in `thermal`-Block im
        `config`-Sub-Mapping und der Top-Level `temperature_celsius`-State
        werden **nur bei aktivem Thermomodell** geschrieben — ohne Block
        byte-identisch (kein Versions-Bump; `EXPECTED_DEMO_*` unberuehrt).
        """
        config_dict: dict[str, object] = {
            "capacity_kwh": self.config.capacity_kwh,
            "initial_soc_pct": self.config.initial_soc_pct,
            "min_soc_pct": self.config.min_soc_pct,
            "max_soc_pct": self.config.max_soc_pct,
            "max_charge_kw": self.config.max_charge_kw,
            "max_discharge_kw": self.config.max_discharge_kw,
            "charge_efficiency": self.config.charge_efficiency,
            "discharge_efficiency": self.config.discharge_efficiency,
            "ramp_kw_per_s": self.config.ramp_kw_per_s,
        }
        if self.config.thermal is not None:
            config_dict["thermal"] = {
                key: getattr(self.config.thermal, key) for key in THERMAL_FIELD_NAMES
            }
        # M8-Welle-4b (ADR 0066 §2.5): cell-Block opt-in (nur bei aktivem
        # Zell-Modell). `n_cells` ist `int`, die uebrigen `Decimal`.
        if self.config.cell is not None:
            config_dict["cell"] = {
                "nominal_pack_voltage_v": self.config.cell.nominal_pack_voltage_v,
                "n_cells": self.config.cell.n_cells,
                "noise_amplitude_v": self.config.cell.noise_amplitude_v,
            }
        result: dict[str, object] = {
            "version": self.version,
            "device_id": self.device_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "config": config_dict,
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
        if self.temperature_celsius is not None:
            result["temperature_celsius"] = self.temperature_celsius
        # M8-Welle-4b (ADR 0066 §2.5): cell_voltages_v opt-in (nur bei
        # Non-Empty → leeres Tuple bleibt byte-identisch wie heute);
        # kanonisch als geordnete Decimal-Liste.
        if self.cell_voltages_v:
            result["cell_voltages_v"] = list(self.cell_voltages_v)
        return result

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
                # M8-Welle-4a (ADR 0065 §2.5): opt-in thermal-Block (fehlt
                # -> None; Alt-Snapshots lesen als „kein Thermomodell").
                thermal=_parse_thermal(config_state),
                # M8-Welle-4b (ADR 0066 §2.5): opt-in cell-Block (fehlt
                # -> None; Alt-Snapshots lesen als „kein Zell-Modell").
                cell=_parse_cell(config_state),
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
        cell_failure_active = assert_optional_fault_flag(
            state, _FAULT_STATE_KEY, "cell_failure_active", SUBSYSTEM
        )

        # M8-Welle-4a (ADR 0065 §2.5): Thermo-State opt-in lesen (backward-
        # compat — Alt-Snapshots ohne den Key lesen als „kein Thermomodell").
        temperature_celsius = (
            assert_decimal(state["temperature_celsius"], "temperature_celsius", SUBSYSTEM)
            if "temperature_celsius" in state
            else None
        )

        # M8-Welle-4b (ADR 0066 §2.5): Zellspannungs-Tuple opt-in lesen
        # (fehlt → leeres Tuple; Alt-Snapshots roundtrip-faehig).
        cell_voltages_v = _parse_cell_voltages(state)

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
            temperature_celsius=temperature_celsius,
            cell_voltages_v=cell_voltages_v,
        )


def _config_decimal(config_state: Mapping[str, object], leaf: str) -> Decimal:
    """Battery-Config-Schluessel-Helper.

    Mapt `leaf` → `"config.<leaf>"` als Pfad fuer den
    `WrongTypeError`-Path (Welle-3-Review L-1 Migration: dedup auf
    Codec-`assert_decimal` mit Battery-spezifischem Pfad-Prefix).
    """
    return assert_decimal(config_state[leaf], f"config.{leaf}", SUBSYSTEM)


def _parse_thermal(config_state: Mapping[str, object]) -> ThermalConfig | None:
    """M8-Welle-4a (ADR 0065 §2.5): liest den opt-in `thermal`-Block aus dem
    `config`-Sub-Mapping (fehlt → `None`). Die Wertebereichs-Invarianten
    (ADR 0065 §2.1) erzwingt der `ThermalConfig`-Konstruktor; sein
    `BatteryConfigError` wird vom Aufrufer (`from_dict`) zu `WrongTypeError`
    ueberfuehrt — spiegelt `_parse_volt_var` aus dem PV-Snapshot."""
    if "thermal" not in config_state:
        return None
    block = assert_mapping(config_state["thermal"], "config.thermal", SUBSYSTEM)
    assert_required_keys(block, _THERMAL_KEYS, SUBSYSTEM)
    fields = {
        key: assert_decimal(block[key], f"config.thermal.{key}", SUBSYSTEM)
        for key in THERMAL_FIELD_NAMES
    }
    return ThermalConfig(**fields)


def _parse_cell(config_state: Mapping[str, object]) -> CellConfig | None:
    """M8-Welle-4b (ADR 0066 §2.5): liest den opt-in `cell`-Block aus dem
    `config`-Sub-Mapping (fehlt → `None`). `n_cells` ist `int`, die uebrigen
    `Decimal`. Die Wertebereichs-Invarianten (ADR 0066 §2.1) erzwingt der
    `CellConfig`-Konstruktor; sein `BatteryConfigError` wird vom Aufrufer
    (`from_dict`) zu `WrongTypeError` ueberfuehrt."""
    if "cell" not in config_state:
        return None
    block = assert_mapping(config_state["cell"], "config.cell", SUBSYSTEM)
    assert_required_keys(block, _CELL_KEYS, SUBSYSTEM)
    return CellConfig(
        nominal_pack_voltage_v=assert_decimal(
            block["nominal_pack_voltage_v"], "config.cell.nominal_pack_voltage_v", SUBSYSTEM
        ),
        n_cells=assert_int(block["n_cells"], "config.cell.n_cells", SUBSYSTEM),
        noise_amplitude_v=assert_decimal(
            block["noise_amplitude_v"], "config.cell.noise_amplitude_v", SUBSYSTEM
        ),
    )


def _parse_cell_voltages(state: Mapping[str, object]) -> tuple[Decimal, ...]:
    """M8-Welle-4b (ADR 0066 §2.5): liest das opt-in `cell_voltages_v`-Tuple
    (fehlt → leeres Tuple). Erwartet eine geordnete Liste von `Decimal`."""
    if "cell_voltages_v" not in state:
        return ()
    raw = state["cell_voltages_v"]
    if not isinstance(raw, list):
        raise WrongTypeError(SUBSYSTEM, "cell_voltages_v", "list", type(raw).__name__)
    return tuple(
        assert_decimal(value, f"cell_voltages_v[{index}]", SUBSYSTEM)
        for index, value in enumerate(raw)
    )


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
