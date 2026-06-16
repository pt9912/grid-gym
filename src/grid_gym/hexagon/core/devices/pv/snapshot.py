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

from grid_gym.hexagon.core.devices.pv.config import (
    VOLT_VAR_FIELD_NAMES,
    PvConfig,
    PvConfigError,
    VoltVarConfig,
)
from grid_gym.hexagon.core.errors import VersionError, WrongTypeError
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_decimal,
    assert_int,
    assert_mapping,
    assert_required_keys,
    assert_str,
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
# M8-Welle-3c-b-1 (ADR 0063 §2.5): Pflicht-Keys des opt-in volt_var-Blocks.
_VOLT_VAR_KEYS: Final[frozenset[str]] = frozenset(VOLT_VAR_FIELD_NAMES)


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
        config_dict: dict[str, object] = {"rated_power_kw": self.config.rated_power_kw}
        # M8-Welle-3c-b-1 (ADR 0063 §2.5): volt_var opt-in — ohne Kurve
        # byte-identisch (kein Versions-Bump).
        if self.config.volt_var is not None:
            config_dict["volt_var"] = {
                key: getattr(self.config.volt_var, key) for key in VOLT_VAR_FIELD_NAMES
            }
        return {
            "version": self.version,
            "device_id": self.device_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "config": config_dict,
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

        device_id = assert_str(state["device_id"], "device_id", SUBSYSTEM)
        run_id = assert_str(state["run_id"], "run_id", SUBSYSTEM)
        sequence = assert_int(state["sequence"], "sequence", SUBSYSTEM)

        config_state = assert_mapping(state["config"], "config", SUBSYSTEM)
        assert_required_keys(config_state, _CONFIG_KEYS, SUBSYSTEM)
        try:
            config = PvConfig(
                rated_power_kw=assert_decimal(
                    config_state["rated_power_kw"],
                    "config.rated_power_kw",
                    SUBSYSTEM,
                ),
                volt_var=_parse_volt_var(config_state),
            )
        except PvConfigError as err:
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


def _parse_volt_var(config_state: Mapping[str, object]) -> VoltVarConfig | None:
    """M8-Welle-3c-b-1 (ADR 0063 §2.5): liest den opt-in `volt_var`-Block
    (fehlt → `None`). Wertebereichs-Invarianten erzwingt der
    `VoltVarConfig`-Konstruktor (vom Aufrufer zu `WrongTypeError`
    ueberfuehrt)."""
    if "volt_var" not in config_state:
        return None
    block = assert_mapping(config_state["volt_var"], "config.volt_var", SUBSYSTEM)
    assert_required_keys(block, _VOLT_VAR_KEYS, SUBSYSTEM)
    fields = {
        key: assert_decimal(block[key], f"config.volt_var.{key}", SUBSYSTEM)
        for key in VOLT_VAR_FIELD_NAMES
    }
    return VoltVarConfig(**fields)


__all__ = [
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "PvSnapshot",
]
