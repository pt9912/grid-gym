"""`TransformerSnapshot` — Snapshot-Format fuer `TransformerDevice`
(ADR 0056 §2.7).

Layout (`version: int` = 1), self-sufficient (ADR 0014 §2.2): die
eingebettete `config` erlaubt `from_snapshot(state)` ohne externes
`ScenarioDevice`.

- `version`, `device_id`, `run_id`, `sequence` — Lifecycle-State.
- `config: TransformerConfig` — eingebettet (5 Decimal-Felder).
- `current_primary_power_kw`, `pending_power_kw` — Power-State.
- `throughput_kwh` — kumulative gelieferte Sekundaer-Energie (monoton
  nicht-fallend).
- `winding_fault_active` — Schutz-Fault-Flag im additiven `fault_state`-
  Sub-Block (ADR 0025 §2.2-Konvention).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Self

from grid_gym.hexagon.core.devices.transformer.config import (
    CONFIG_FIELD_NAMES,
    TransformerConfig,
    TransformerConfigError,
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

SUBSYSTEM: Final[str] = "transformer"
SNAPSHOT_VERSION: Final[int] = 1

_TOP_KEYS: Final[frozenset[str]] = frozenset(
    {
        "version",
        "device_id",
        "run_id",
        "sequence",
        "config",
        "current_primary_power_kw",
        "pending_power_kw",
        "throughput_kwh",
    }
)
_CONFIG_KEYS: Final[frozenset[str]] = frozenset(CONFIG_FIELD_NAMES)

# ADR 0025 §2.2: additiver `fault_state`-Block (optional fuer Forward-/
# Backward-Compat — Snapshots ohne Block defaulten False).
_FAULT_STATE_KEY: Final[str] = "fault_state"
_WINDING_FAULT_KEY: Final[str] = "winding_fault_active"


@dataclass(frozen=True, slots=True)
class TransformerSnapshot:
    """Transformator-Zustand zu einem bestimmten Zeitpunkt.

    Roundtrip-Vertrag (ADR 0013 §2.4): byte-stabil. Self-sufficient
    (ADR 0014 §2.2). Kumulative `throughput_kwh` ueberlebt den Roundtrip.
    """

    version: int
    device_id: str
    run_id: str
    sequence: int
    config: TransformerConfig
    current_primary_power_kw: Decimal
    pending_power_kw: Decimal
    throughput_kwh: Decimal
    winding_fault_active: bool = False

    def to_dict(self) -> Mapping[str, object]:
        """Wandelt den Snapshot in ein `Mapping[str, object]` mit
        `version` als Erst-Feld (ADR 0013 §2.4)."""
        return {
            "version": self.version,
            "device_id": self.device_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "config": {key: getattr(self.config, key) for key in CONFIG_FIELD_NAMES},
            "current_primary_power_kw": self.current_primary_power_kw,
            "pending_power_kw": self.pending_power_kw,
            "throughput_kwh": self.throughput_kwh,
            _FAULT_STATE_KEY: {
                _WINDING_FAULT_KEY: self.winding_fault_active,
            },
        }

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Rekonstruiert einen `TransformerSnapshot` aus einem Mapping.
        Wirft typed `MissingKeysError`/`WrongTypeError`/`VersionError`
        mit `subsystem="transformer"`."""
        assert_required_keys(state, _TOP_KEYS, SUBSYSTEM)

        version = assert_int(state["version"], "version", SUBSYSTEM)
        if version != SNAPSHOT_VERSION:
            raise VersionError(SUBSYSTEM, expected=SNAPSHOT_VERSION, found=version)

        device_id = assert_str(state["device_id"], "device_id", SUBSYSTEM)
        run_id = assert_str(state["run_id"], "run_id", SUBSYSTEM)
        sequence = assert_int(state["sequence"], "sequence", SUBSYSTEM)
        config = _config_from_state(state["config"])

        current_primary_power_kw = assert_decimal(
            state["current_primary_power_kw"], "current_primary_power_kw", SUBSYSTEM
        )
        pending_power_kw = assert_decimal(state["pending_power_kw"], "pending_power_kw", SUBSYSTEM)
        throughput_kwh = assert_decimal(state["throughput_kwh"], "throughput_kwh", SUBSYSTEM)

        return cls(
            version=version,
            device_id=device_id,
            run_id=run_id,
            sequence=sequence,
            config=config,
            current_primary_power_kw=current_primary_power_kw,
            pending_power_kw=pending_power_kw,
            throughput_kwh=throughput_kwh,
            winding_fault_active=assert_optional_fault_flag(
                state, _FAULT_STATE_KEY, _WINDING_FAULT_KEY, SUBSYSTEM
            ),
        )


def _config_from_state(raw: object) -> TransformerConfig:
    """Parst den eingebetteten `config`-Block (5 Decimal-Felder)."""
    config_state = assert_mapping(raw, "config", SUBSYSTEM)
    assert_required_keys(config_state, _CONFIG_KEYS, SUBSYSTEM)
    decimals = {
        key: assert_decimal(config_state[key], f"config.{key}", SUBSYSTEM)
        for key in CONFIG_FIELD_NAMES
    }
    try:
        config = TransformerConfig(**decimals)
    except TransformerConfigError as err:
        raise WrongTypeError(SUBSYSTEM, "config", "valid", str(err)) from err
    return config


__all__ = [
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "TransformerSnapshot",
]
