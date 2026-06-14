"""`DieselGeneratorSnapshot` — Snapshot-Format fuer
`DieselGeneratorDevice` (ADR 0058 §2.8).

Layout (`version: int` = 1), self-sufficient (ADR 0014 §2.2).

- `version`, `device_id`, `run_id`, `sequence` — Lifecycle-State.
- `config: DieselGeneratorConfig` — eingebettet (7 Decimal-Felder).
- `fuel_l` — aktueller Kraftstoff-Vorrat (`0 .. fuel_capacity_l`).
- `current_power_kw`, `pending_power_kw` — Power-State.
- `running: bool` — Anfahr-/Abstell-Zustandsmaschine (ADR 0058 §2.4).
- `generated_kwh` — kumulative Erzeugung (monoton nicht-fallend).
- `genset_fault_active` — Schutz-Fault-Flag im additiven `fault_state`-
  Sub-Block (ADR 0025 §2.2-Konvention).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Self

from grid_gym.hexagon.core.devices.diesel_generator.config import (
    CONFIG_FIELD_NAMES,
    DieselGeneratorConfig,
    DieselGeneratorConfigError,
)
from grid_gym.hexagon.core.errors import VersionError, WrongTypeError
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_bool,
    assert_decimal,
    assert_int,
    assert_mapping,
    assert_optional_fault_flag,
    assert_required_keys,
    assert_str,
)

SUBSYSTEM: Final[str] = "diesel_generator"
SNAPSHOT_VERSION: Final[int] = 1

_TOP_KEYS: Final[frozenset[str]] = frozenset(
    {
        "version",
        "device_id",
        "run_id",
        "sequence",
        "config",
        "fuel_l",
        "current_power_kw",
        "pending_power_kw",
        "running",
        "generated_kwh",
    }
)
_CONFIG_KEYS: Final[frozenset[str]] = frozenset(CONFIG_FIELD_NAMES)

_FAULT_STATE_KEY: Final[str] = "fault_state"
_GENSET_FAULT_KEY: Final[str] = "genset_fault_active"


@dataclass(frozen=True, slots=True)
class DieselGeneratorSnapshot:
    """Dieselgenerator-Zustand zu einem bestimmten Zeitpunkt.

    Roundtrip-Vertrag (ADR 0013 §2.4): byte-stabil. Self-sufficient
    (ADR 0014 §2.2). Kraftstoff + kumulative Erzeugung + running-Flag
    ueberleben den Roundtrip.
    """

    version: int
    device_id: str
    run_id: str
    sequence: int
    config: DieselGeneratorConfig
    fuel_l: Decimal
    current_power_kw: Decimal
    pending_power_kw: Decimal
    running: bool
    generated_kwh: Decimal
    genset_fault_active: bool = False

    def to_dict(self) -> Mapping[str, object]:
        """Wandelt den Snapshot in ein `Mapping[str, object]` mit
        `version` als Erst-Feld (ADR 0013 §2.4)."""
        return {
            "version": self.version,
            "device_id": self.device_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "config": {key: getattr(self.config, key) for key in CONFIG_FIELD_NAMES},
            "fuel_l": self.fuel_l,
            "current_power_kw": self.current_power_kw,
            "pending_power_kw": self.pending_power_kw,
            "running": self.running,
            "generated_kwh": self.generated_kwh,
            _FAULT_STATE_KEY: {
                _GENSET_FAULT_KEY: self.genset_fault_active,
            },
        }

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Rekonstruiert einen `DieselGeneratorSnapshot` aus einem
        Mapping. Wirft typed `MissingKeysError`/`WrongTypeError`/
        `VersionError` mit `subsystem="diesel_generator"`."""
        assert_required_keys(state, _TOP_KEYS, SUBSYSTEM)

        version = assert_int(state["version"], "version", SUBSYSTEM)
        if version != SNAPSHOT_VERSION:
            raise VersionError(SUBSYSTEM, expected=SNAPSHOT_VERSION, found=version)

        device_id = assert_str(state["device_id"], "device_id", SUBSYSTEM)
        run_id = assert_str(state["run_id"], "run_id", SUBSYSTEM)
        sequence = assert_int(state["sequence"], "sequence", SUBSYSTEM)
        config = _config_from_state(state["config"])

        fuel_l = assert_decimal(state["fuel_l"], "fuel_l", SUBSYSTEM)
        current_power_kw = assert_decimal(state["current_power_kw"], "current_power_kw", SUBSYSTEM)
        pending_power_kw = assert_decimal(state["pending_power_kw"], "pending_power_kw", SUBSYSTEM)
        running = assert_bool(state["running"], "running", SUBSYSTEM)
        generated_kwh = assert_decimal(state["generated_kwh"], "generated_kwh", SUBSYSTEM)

        return cls(
            version=version,
            device_id=device_id,
            run_id=run_id,
            sequence=sequence,
            config=config,
            fuel_l=fuel_l,
            current_power_kw=current_power_kw,
            pending_power_kw=pending_power_kw,
            running=running,
            generated_kwh=generated_kwh,
            genset_fault_active=assert_optional_fault_flag(
                state, _FAULT_STATE_KEY, _GENSET_FAULT_KEY, SUBSYSTEM
            ),
        )


def _config_from_state(raw: object) -> DieselGeneratorConfig:
    """Parst den eingebetteten `config`-Block (7 Decimal-Felder)."""
    config_state = assert_mapping(raw, "config", SUBSYSTEM)
    assert_required_keys(config_state, _CONFIG_KEYS, SUBSYSTEM)
    decimals = {
        key: assert_decimal(config_state[key], f"config.{key}", SUBSYSTEM)
        for key in CONFIG_FIELD_NAMES
    }
    try:
        config = DieselGeneratorConfig(**decimals)
    except DieselGeneratorConfigError as err:
        raise WrongTypeError(SUBSYSTEM, "config", "valid", str(err)) from err
    return config


__all__ = [
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "DieselGeneratorSnapshot",
]
