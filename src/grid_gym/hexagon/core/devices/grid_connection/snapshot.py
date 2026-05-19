"""`GridConnectionSnapshot` — Snapshot-Format fuer
`GridConnectionDevice` (ADR 0017 §2.3).

Layout (`version: int` = 1), spiegelt Welle-2-Review-Schaerfung
(self-sufficient mit device_id/run_id/sequence) + zwei stateful
Felder fuer kumulative Energie:

- `version`, `device_id`, `run_id`, `sequence` — Lifecycle-State.
- `config: GridConnectionConfig` — eingebettet, damit
  `from_snapshot(state)` ohne externes ScenarioDevice
  rekonstruieren kann.
- `current_power_kw`, `pending_power_kw` — Power-State.
- `import_kwh`, `export_kwh` — kumulative Energie-Summen
  (monoton nicht-fallend; ADR 0017 §2.3/§2.5).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Self

from grid_gym.hexagon.core.devices.grid_connection.config import (
    GridConnectionConfig,
    GridConnectionConfigError,
)
from grid_gym.hexagon.core.errors import VersionError, WrongTypeError
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_decimal,
    assert_int,
    assert_mapping,
    assert_required_keys,
    assert_str,
)

SUBSYSTEM: Final[str] = "grid_connection"
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
        "import_kwh",
        "export_kwh",
    }
)
_CONFIG_KEYS: Final[frozenset[str]] = frozenset(
    {"nominal_voltage_v", "max_import_kw", "max_export_kw"}
)


@dataclass(frozen=True, slots=True)
class GridConnectionSnapshot:
    """GridConnection-Zustand zu einem bestimmten Zeitpunkt.

    Roundtrip-Vertrag (ADR 0013 §2.4): byte-stabil. Snapshot ist
    self-sufficient (ADR 0014 §2.2-Schaerfung). Kumulative
    Energie-Felder bleiben ueber den Roundtrip erhalten
    (ADR 0017 §2.3).
    """

    version: int
    device_id: str
    run_id: str
    sequence: int
    config: GridConnectionConfig
    current_power_kw: Decimal
    pending_power_kw: Decimal
    import_kwh: Decimal
    export_kwh: Decimal

    def to_dict(self) -> Mapping[str, object]:
        """Wandelt den Snapshot in ein `Mapping[str, object]` mit
        `version` als Erst-Feld (ADR 0013 §2.4)."""
        return {
            "version": self.version,
            "device_id": self.device_id,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "config": {
                "nominal_voltage_v": self.config.nominal_voltage_v,
                "max_import_kw": self.config.max_import_kw,
                "max_export_kw": self.config.max_export_kw,
            },
            "current_power_kw": self.current_power_kw,
            "pending_power_kw": self.pending_power_kw,
            "import_kwh": self.import_kwh,
            "export_kwh": self.export_kwh,
        }

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Rekonstruiert einen `GridConnectionSnapshot` aus einem
        Mapping. Wirft typed
        `MissingKeysError`/`WrongTypeError`/`VersionError`
        mit `subsystem="grid_connection"`."""
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
            config = GridConnectionConfig(
                nominal_voltage_v=assert_decimal(
                    config_state["nominal_voltage_v"],
                    "config.nominal_voltage_v",
                    SUBSYSTEM,
                ),
                max_import_kw=assert_decimal(
                    config_state["max_import_kw"],
                    "config.max_import_kw",
                    SUBSYSTEM,
                ),
                max_export_kw=assert_decimal(
                    config_state["max_export_kw"],
                    "config.max_export_kw",
                    SUBSYSTEM,
                ),
            )
        except GridConnectionConfigError as err:
            raise WrongTypeError(SUBSYSTEM, "config", "valid", str(err)) from err

        current_power_kw = assert_decimal(state["current_power_kw"], "current_power_kw", SUBSYSTEM)
        pending_power_kw = assert_decimal(state["pending_power_kw"], "pending_power_kw", SUBSYSTEM)
        import_kwh = assert_decimal(state["import_kwh"], "import_kwh", SUBSYSTEM)
        export_kwh = assert_decimal(state["export_kwh"], "export_kwh", SUBSYSTEM)

        return cls(
            version=version,
            device_id=device_id,
            run_id=run_id,
            sequence=sequence,
            config=config,
            current_power_kw=current_power_kw,
            pending_power_kw=pending_power_kw,
            import_kwh=import_kwh,
            export_kwh=export_kwh,
        )


__all__ = [
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "GridConnectionSnapshot",
]
