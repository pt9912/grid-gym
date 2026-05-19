"""`SmartMeterSnapshot` — Snapshot-Format fuer `SmartMeterDevice`
(ADR 0018 §2.5).

Strukturell der kleinste Geraete-Snapshot der MVP-Geraete
(stateless aggregator):

- `version`, `device_id`, `run_id`, `sequence` — Lifecycle-State.
- `config: SmartMeterConfig` — eingebettet, damit
  `from_snapshot(state)` ohne externes ScenarioDevice
  rekonstruieren kann.

**Negative Assertion (Welle-4b-DoD):** der Snapshot enthaelt
KEINE Aggregat-Werte (`aggregated_power_kw`-aehnlich). Diese
sind derived und werden beim naechsten Tick neu berechnet.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Self

from grid_gym.hexagon.core.devices.smart_meter.config import (
    SmartMeterConfig,
    SmartMeterConfigError,
)
from grid_gym.hexagon.core.errors import VersionError, WrongTypeError
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_int,
    assert_mapping,
    assert_required_keys,
    assert_str,
)

SUBSYSTEM: Final[str] = "smart_meter"
SNAPSHOT_VERSION: Final[int] = 1

# Welle-4a-Review-L-3-Pattern: Single-Source-of-Truth fuer
# Config-Feld-Namen (model.py iteriert ueber dieselbe Reihenfolge
# beim Param-Parsing).
CONFIG_FIELD_NAMES: Final[tuple[str, ...]] = (
    "aggregate_device_ids",
    "aggregate_metric_name",
)

_TOP_KEYS: Final[frozenset[str]] = frozenset(
    {
        "version",
        "device_id",
        "run_id",
        "sequence",
        "config",
    }
)
_CONFIG_KEYS: Final[frozenset[str]] = frozenset(CONFIG_FIELD_NAMES)


@dataclass(frozen=True, slots=True)
class SmartMeterSnapshot:
    """SmartMeter-Zustand zu einem bestimmten Zeitpunkt.

    Roundtrip-Vertrag (ADR 0013 §2.4): byte-stabil. Snapshot ist
    self-sufficient (ADR 0014 §2.2-Schaerfung). **Keine derived
    Aggregat-Felder** (ADR 0018 §2.5 negative Assertion).
    """

    version: int
    device_id: str
    run_id: str
    sequence: int
    config: SmartMeterConfig

    def to_dict(self) -> Mapping[str, object]:
        """Wandelt den Snapshot in ein `Mapping[str, object]` mit
        `version` als Erst-Feld (ADR 0013 §2.4)."""
        return {
            "version": self.version,
            "device_id": self.device_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "config": {
                "aggregate_device_ids": list(self.config.aggregate_device_ids),
                "aggregate_metric_name": self.config.aggregate_metric_name,
            },
        }

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Rekonstruiert einen `SmartMeterSnapshot` aus einem
        Mapping. Wirft typed
        `MissingKeysError`/`WrongTypeError`/`VersionError`
        mit `subsystem="smart_meter"`."""
        assert_required_keys(state, _TOP_KEYS, SUBSYSTEM)

        version = assert_int(state["version"], "version", SUBSYSTEM)
        if version != SNAPSHOT_VERSION:
            raise VersionError(SUBSYSTEM, expected=SNAPSHOT_VERSION, found=version)

        device_id = assert_str(state["device_id"], "device_id", SUBSYSTEM)
        run_id = assert_str(state["run_id"], "run_id", SUBSYSTEM)
        sequence = assert_int(state["sequence"], "sequence", SUBSYSTEM)

        config_state = assert_mapping(state["config"], "config", SUBSYSTEM)
        assert_required_keys(config_state, _CONFIG_KEYS, SUBSYSTEM)

        raw_ids = config_state["aggregate_device_ids"]
        if not isinstance(raw_ids, list):
            raise WrongTypeError(
                SUBSYSTEM,
                "config.aggregate_device_ids",
                "list",
                type(raw_ids).__name__,
            )
        if any(not isinstance(item, str) for item in raw_ids):
            raise WrongTypeError(
                SUBSYSTEM,
                "config.aggregate_device_ids[*]",
                "str",
                "non-str entry",
            )
        device_ids = tuple(raw_ids)

        metric_name = assert_str(
            config_state["aggregate_metric_name"],
            "config.aggregate_metric_name",
            SUBSYSTEM,
        )

        try:
            config = SmartMeterConfig(
                aggregate_device_ids=device_ids,
                aggregate_metric_name=metric_name,
            )
        except SmartMeterConfigError as err:
            raise WrongTypeError(SUBSYSTEM, "config", "valid", str(err)) from err

        return cls(
            version=version,
            device_id=device_id,
            run_id=run_id,
            sequence=sequence,
            config=config,
        )


__all__ = [
    "CONFIG_FIELD_NAMES",
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "SmartMeterSnapshot",
]
