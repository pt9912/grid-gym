"""`PvSnapshot` — Snapshot-Format fuer `PvDevice` (ADR 0016 §2.3).

Layout (`version: int` = 1), spiegelt Welle-2-Review-Schaerfung
(self-sufficient mit device_id/run_id/sequence):

- `version`, `device_id`, `run_id`, `sequence` — Lifecycle-State.
- `config: PvConfig` — eingebettet, damit `from_snapshot(state)`
  ohne externes ScenarioDevice rekonstruieren kann.
- `current_power_kw`, `pending_power_kw` — Power-State.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Self

from grid_gym.hexagon.core.devices.pv.config import PvConfig, PvConfigError
from grid_gym.hexagon.core.errors import VersionError, WrongTypeError
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_int,
    assert_mapping,
    assert_required_keys,
)

SUBSYSTEM: Final[str] = "pv"
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
class PvSnapshot:
    """PV-Zustand zu einem bestimmten Zeitpunkt.

    Roundtrip-Vertrag (ADR 0013 §2.4): byte-stabil. Snapshot ist
    self-sufficient (ADR 0014 §2.2-Schaerfung).
    """

    version: int
    device_id: str
    run_id: str
    sequence: int
    config: PvConfig
    current_power_kw: Decimal
    pending_power_kw: Decimal

    def to_dict(self) -> Mapping[str, object]:
        """Wandelt den Snapshot in ein `Mapping[str, object]` mit
        `version` als Erst-Feld (ADR 0013 §2.4)."""
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
        """Rekonstruiert einen `PvSnapshot` aus einem Mapping.
        Wirft typed `MissingKeysError`/`WrongTypeError`/`VersionError`
        mit `subsystem="pv"`."""
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
            config = PvConfig(
                rated_power_kw=_decimal(config_state, "config.rated_power_kw"),
            )
        except PvConfigError as err:
            raise WrongTypeError(SUBSYSTEM, "config", "valid", str(err)) from err

        current_power_kw = _decimal(state, "current_power_kw")
        pending_power_kw = _decimal(state, "pending_power_kw")

        return cls(
            version=version,
            device_id=device_id,
            run_id=run_id,
            sequence=sequence,
            config=config,
            current_power_kw=current_power_kw,
            pending_power_kw=pending_power_kw,
        )


def _assert_str(mapping: Mapping[str, object], key: str) -> str:
    value = mapping[key]
    if not isinstance(value, str):
        raise WrongTypeError(SUBSYSTEM, key, "str", type(value).__name__)
    return value


def _decimal(mapping: Mapping[str, object], path: str) -> Decimal:
    leaf = path.rsplit(".", 1)[-1]
    value = mapping[leaf]
    if not isinstance(value, Decimal):
        raise WrongTypeError(SUBSYSTEM, path, "Decimal", type(value).__name__)
    return value


__all__ = [
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "PvSnapshot",
]
