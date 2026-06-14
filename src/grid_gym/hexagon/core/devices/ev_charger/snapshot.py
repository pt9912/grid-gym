"""`EvChargerSnapshot` — Snapshot-Format fuer `EvChargerDevice`
(ADR 0055 §2.8).

Layout (`version: int` = 1), self-sufficient (ADR 0014 §2.2-
Schaerfung): die eingebettete `config` erlaubt `from_snapshot(state)`
ohne externes `ScenarioDevice`.

- `version`, `device_id`, `run_id`, `sequence` — Lifecycle-State.
- `config: EvChargerConfig` — eingebettet.
- `plug_state: str` — `"plugged"`/`"unplugged"` (erster nicht-
  numerischer Geraete-Zustand, ADR 0055 §2.2).
- `stored_kwh` — Fahrzeug-Akku-Energie (`0 .. battery_capacity_kwh`).
- `current_power_kw`, `pending_power_kw` — Power-State.
- `charged_kwh`, `discharged_kwh` — kumulative Energie-Summen
  (monoton nicht-fallend).
- `connection_loss_active` — Fault-Flag im additiven `fault_state`-
  Sub-Block (ADR 0025 §2.2-Konvention, analog Battery/GridConnection).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Self

from grid_gym.hexagon.core.devices.ev_charger.config import (
    PLUG_STATES,
    EvChargerConfig,
    EvChargerConfigError,
)
from grid_gym.hexagon.core.errors import VersionError, WrongTypeError
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_decimal,
    assert_int,
    assert_mapping,
    assert_optional_fault_flag,
    assert_required_keys,
    assert_str,
)

SUBSYSTEM: Final[str] = "ev_charger"
SNAPSHOT_VERSION: Final[int] = 1

# Single-Source-of-Truth fuer die Config-Keys; `model.py` iteriert
# dieselbe Tuple beim Param-Parsing der Decimal-Felder.
CONFIG_DECIMAL_FIELD_NAMES: Final[tuple[str, ...]] = (
    "max_charge_kw",
    "max_discharge_kw",
    "nominal_voltage_v",
    "battery_capacity_kwh",
    "cv_phase_start_soc",
    "initial_soc",
)
_CONFIG_PLUG_FIELD: Final[str] = "initial_plug_state"

_TOP_KEYS: Final[frozenset[str]] = frozenset(
    {
        "version",
        "device_id",
        "run_id",
        "sequence",
        "config",
        "plug_state",
        "stored_kwh",
        "current_power_kw",
        "pending_power_kw",
        "charged_kwh",
        "discharged_kwh",
    }
)
_CONFIG_KEYS: Final[frozenset[str]] = frozenset(CONFIG_DECIMAL_FIELD_NAMES) | {_CONFIG_PLUG_FIELD}

# ADR 0025 §2.2: additiver `fault_state`-Block (optional fuer
# Forward-/Backward-Compat — Snapshots ohne Block defaulten False).
_FAULT_STATE_KEY: Final[str] = "fault_state"
_CONNECTION_LOSS_KEY: Final[str] = "connection_loss_active"


@dataclass(frozen=True, slots=True)
class EvChargerSnapshot:
    """EV-Charger-Zustand zu einem bestimmten Zeitpunkt.

    Roundtrip-Vertrag (ADR 0013 §2.4): byte-stabil. Self-sufficient
    (ADR 0014 §2.2). Kumulative Energie-Felder + SoC ueberleben den
    Roundtrip (ADR 0055 §2.8).
    """

    version: int
    device_id: str
    run_id: str
    sequence: int
    config: EvChargerConfig
    plug_state: str
    stored_kwh: Decimal
    current_power_kw: Decimal
    pending_power_kw: Decimal
    charged_kwh: Decimal
    discharged_kwh: Decimal
    connection_loss_active: bool = False

    def to_dict(self) -> Mapping[str, object]:
        """Wandelt den Snapshot in ein `Mapping[str, object]` mit
        `version` als Erst-Feld (ADR 0013 §2.4)."""
        return {
            "version": self.version,
            "device_id": self.device_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "config": {
                "max_charge_kw": self.config.max_charge_kw,
                "max_discharge_kw": self.config.max_discharge_kw,
                "nominal_voltage_v": self.config.nominal_voltage_v,
                "battery_capacity_kwh": self.config.battery_capacity_kwh,
                "cv_phase_start_soc": self.config.cv_phase_start_soc,
                "initial_soc": self.config.initial_soc,
                _CONFIG_PLUG_FIELD: self.config.initial_plug_state,
            },
            "plug_state": self.plug_state,
            "stored_kwh": self.stored_kwh,
            "current_power_kw": self.current_power_kw,
            "pending_power_kw": self.pending_power_kw,
            "charged_kwh": self.charged_kwh,
            "discharged_kwh": self.discharged_kwh,
            _FAULT_STATE_KEY: {
                _CONNECTION_LOSS_KEY: self.connection_loss_active,
            },
        }

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Rekonstruiert einen `EvChargerSnapshot` aus einem Mapping.
        Wirft typed `MissingKeysError`/`WrongTypeError`/`VersionError`
        mit `subsystem="ev_charger"`."""
        assert_required_keys(state, _TOP_KEYS, SUBSYSTEM)

        version = assert_int(state["version"], "version", SUBSYSTEM)
        if version != SNAPSHOT_VERSION:
            raise VersionError(SUBSYSTEM, expected=SNAPSHOT_VERSION, found=version)

        device_id = assert_str(state["device_id"], "device_id", SUBSYSTEM)
        run_id = assert_str(state["run_id"], "run_id", SUBSYSTEM)
        sequence = assert_int(state["sequence"], "sequence", SUBSYSTEM)
        config = _config_from_state(state["config"])

        plug_state = assert_str(state["plug_state"], "plug_state", SUBSYSTEM)
        if plug_state not in PLUG_STATES:
            raise WrongTypeError(SUBSYSTEM, "plug_state", "plugged|unplugged", plug_state)

        stored_kwh = assert_decimal(state["stored_kwh"], "stored_kwh", SUBSYSTEM)
        current_power_kw = assert_decimal(state["current_power_kw"], "current_power_kw", SUBSYSTEM)
        pending_power_kw = assert_decimal(state["pending_power_kw"], "pending_power_kw", SUBSYSTEM)
        charged_kwh = assert_decimal(state["charged_kwh"], "charged_kwh", SUBSYSTEM)
        discharged_kwh = assert_decimal(state["discharged_kwh"], "discharged_kwh", SUBSYSTEM)

        return cls(
            version=version,
            device_id=device_id,
            run_id=run_id,
            sequence=sequence,
            config=config,
            plug_state=plug_state,
            stored_kwh=stored_kwh,
            current_power_kw=current_power_kw,
            pending_power_kw=pending_power_kw,
            charged_kwh=charged_kwh,
            discharged_kwh=discharged_kwh,
            connection_loss_active=assert_optional_fault_flag(
                state, _FAULT_STATE_KEY, _CONNECTION_LOSS_KEY, SUBSYSTEM
            ),
        )


def _config_from_state(raw: object) -> EvChargerConfig:
    """Parst den eingebetteten `config`-Block (6 Decimals + plug-str)."""
    config_state = assert_mapping(raw, "config", SUBSYSTEM)
    assert_required_keys(config_state, _CONFIG_KEYS, SUBSYSTEM)
    decimals = {
        key: assert_decimal(config_state[key], f"config.{key}", SUBSYSTEM)
        for key in CONFIG_DECIMAL_FIELD_NAMES
    }
    initial_plug_state = assert_str(
        config_state[_CONFIG_PLUG_FIELD], f"config.{_CONFIG_PLUG_FIELD}", SUBSYSTEM
    )
    try:
        config = EvChargerConfig(
            max_charge_kw=decimals["max_charge_kw"],
            max_discharge_kw=decimals["max_discharge_kw"],
            nominal_voltage_v=decimals["nominal_voltage_v"],
            battery_capacity_kwh=decimals["battery_capacity_kwh"],
            cv_phase_start_soc=decimals["cv_phase_start_soc"],
            initial_soc=decimals["initial_soc"],
            initial_plug_state=initial_plug_state,
        )
    except EvChargerConfigError as err:
        raise WrongTypeError(SUBSYSTEM, "config", "valid", str(err)) from err
    return config


__all__ = [
    "CONFIG_DECIMAL_FIELD_NAMES",
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "EvChargerSnapshot",
]
