"""`LoadSnapshot` — Snapshot-Format fuer `LoadDevice` (ADR 0016
§2.3). Spiegelt `PvSnapshot`-Struktur."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Self

from grid_gym.hexagon.core.devices.load.config import LoadConfig, LoadConfigError
from grid_gym.hexagon.core.errors import VersionError, WrongTypeError
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_decimal,
    assert_int,
    assert_mapping,
    assert_required_keys,
    assert_str,
)

SUBSYSTEM: Final[str] = "load"
SNAPSHOT_VERSION: Final[int] = 1

_TOP_KEYS: Final[frozenset[str]] = frozenset(
    {
        "version",
        "device_id",
        "run_id",
        "sequence",
        "config",
        "current_power_kw",
        "pending_power_kw",
    }
)
_CONFIG_KEYS: Final[frozenset[str]] = frozenset({"rated_power_kw"})


@dataclass(frozen=True, slots=True)
class LoadSnapshot:
    """Load-Zustand zu einem bestimmten Zeitpunkt."""

    version: int
    device_id: str
    run_id: str
    sequence: int
    config: LoadConfig
    current_power_kw: Decimal
    pending_power_kw: Decimal

    def to_dict(self) -> Mapping[str, object]:
        return {
            "version": self.version,
            "device_id": self.device_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "config": {"rated_power_kw": self.config.rated_power_kw},
            "current_power_kw": self.current_power_kw,
            "pending_power_kw": self.pending_power_kw,
        }

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
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
            config = LoadConfig(
                rated_power_kw=assert_decimal(
                    config_state["rated_power_kw"],
                    "config.rated_power_kw",
                    SUBSYSTEM,
                ),
            )
        except LoadConfigError as err:
            raise WrongTypeError(SUBSYSTEM, "config", "valid", str(err)) from err
        current_power_kw = assert_decimal(state["current_power_kw"], "current_power_kw", SUBSYSTEM)
        pending_power_kw = assert_decimal(state["pending_power_kw"], "pending_power_kw", SUBSYSTEM)
        return cls(
            version=version,
            device_id=device_id,
            run_id=run_id,
            sequence=sequence,
            config=config,
            current_power_kw=current_power_kw,
            pending_power_kw=pending_power_kw,
        )


__all__ = [
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "LoadSnapshot",
]
