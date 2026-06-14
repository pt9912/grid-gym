"""`WindTurbineSnapshot` — Snapshot-Format fuer `WindTurbineDevice`
(ADR 0057 §2.6).

Layout (`version: int` = 1), self-sufficient (ADR 0014 §2.2). **Kein
`fault_state`** (Wind hat keinen Fault). Der `RandomPort` ist NICHT Teil
des Snapshots — der Root-Stream wird vom `TickLoop` persistiert, das
Geraet bekommt seinen Sub-Stream per `attach_random` nach `from_snapshot`
re-attached (ADR 0057 §2.6).

- `version`, `device_id`, `run_id`, `sequence` — Lifecycle-State.
- `config: WindTurbineConfig` — eingebettet (6 Decimal-Felder).
- `current_power_kw`, `current_wind_speed_ms` — letzter Tick-Zustand.
- `generated_kwh` — kumulative Einspeise-Energie (monoton nicht-fallend).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Self

from grid_gym.hexagon.core.devices.wind_turbine.config import (
    CONFIG_FIELD_NAMES,
    WindTurbineConfig,
    WindTurbineConfigError,
)
from grid_gym.hexagon.core.errors import VersionError, WrongTypeError
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_decimal,
    assert_int,
    assert_mapping,
    assert_required_keys,
    assert_str,
)

SUBSYSTEM: Final[str] = "wind_turbine"
SNAPSHOT_VERSION: Final[int] = 1

_TOP_KEYS: Final[frozenset[str]] = frozenset(
    {
        "version",
        "device_id",
        "run_id",
        "sequence",
        "config",
        "current_power_kw",
        "current_wind_speed_ms",
        "generated_kwh",
    }
)
_CONFIG_KEYS: Final[frozenset[str]] = frozenset(CONFIG_FIELD_NAMES)


@dataclass(frozen=True, slots=True)
class WindTurbineSnapshot:
    """Windkraftanlagen-Zustand zu einem bestimmten Zeitpunkt.

    Roundtrip-Vertrag (ADR 0013 §2.4): byte-stabil. Self-sufficient
    (ADR 0014 §2.2). Kumulative `generated_kwh` ueberlebt den Roundtrip.
    """

    version: int
    device_id: str
    run_id: str
    sequence: int
    config: WindTurbineConfig
    current_power_kw: Decimal
    current_wind_speed_ms: Decimal
    generated_kwh: Decimal

    def to_dict(self) -> Mapping[str, object]:
        """Wandelt den Snapshot in ein `Mapping[str, object]` mit
        `version` als Erst-Feld (ADR 0013 §2.4)."""
        return {
            "version": self.version,
            "device_id": self.device_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "config": {key: getattr(self.config, key) for key in CONFIG_FIELD_NAMES},
            "current_power_kw": self.current_power_kw,
            "current_wind_speed_ms": self.current_wind_speed_ms,
            "generated_kwh": self.generated_kwh,
        }

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Rekonstruiert einen `WindTurbineSnapshot` aus einem Mapping.
        Wirft typed `MissingKeysError`/`WrongTypeError`/`VersionError`
        mit `subsystem="wind_turbine"`."""
        assert_required_keys(state, _TOP_KEYS, SUBSYSTEM)

        version = assert_int(state["version"], "version", SUBSYSTEM)
        if version != SNAPSHOT_VERSION:
            raise VersionError(SUBSYSTEM, expected=SNAPSHOT_VERSION, found=version)

        device_id = assert_str(state["device_id"], "device_id", SUBSYSTEM)
        run_id = assert_str(state["run_id"], "run_id", SUBSYSTEM)
        sequence = assert_int(state["sequence"], "sequence", SUBSYSTEM)
        config = _config_from_state(state["config"])

        current_power_kw = assert_decimal(state["current_power_kw"], "current_power_kw", SUBSYSTEM)
        current_wind_speed_ms = assert_decimal(
            state["current_wind_speed_ms"], "current_wind_speed_ms", SUBSYSTEM
        )
        generated_kwh = assert_decimal(state["generated_kwh"], "generated_kwh", SUBSYSTEM)

        return cls(
            version=version,
            device_id=device_id,
            run_id=run_id,
            sequence=sequence,
            config=config,
            current_power_kw=current_power_kw,
            current_wind_speed_ms=current_wind_speed_ms,
            generated_kwh=generated_kwh,
        )


def _config_from_state(raw: object) -> WindTurbineConfig:
    """Parst den eingebetteten `config`-Block (6 Decimal-Felder)."""
    config_state = assert_mapping(raw, "config", SUBSYSTEM)
    assert_required_keys(config_state, _CONFIG_KEYS, SUBSYSTEM)
    decimals = {
        key: assert_decimal(config_state[key], f"config.{key}", SUBSYSTEM)
        for key in CONFIG_FIELD_NAMES
    }
    try:
        config = WindTurbineConfig(**decimals)
    except WindTurbineConfigError as err:
        raise WrongTypeError(SUBSYSTEM, "config", "valid", str(err)) from err
    return config


__all__ = [
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "WindTurbineSnapshot",
]
