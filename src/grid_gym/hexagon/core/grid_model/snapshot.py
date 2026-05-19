"""`GridModelSnapshot` — Snapshot-Format fuer `GridModelBilanz`
(ADR 0019 §2.5).

Layout (`version: int` = 1 in Welle 5a), spiegelt
self-sufficient-Pattern aus ADR 0014 §2.2-Schaerfung:

- `version`, `config` (eingebettet), `model_kind` —
  Identitaet und Selbstkennzeichnung.
- `current_frequency_hz`, `current_voltage_v` — aktueller
  Bilanz-Zustand.
- `last_imbalance_kw` — letzter Imbalance-Input.
- `clamp_event_count` — monoton nicht-fallender Zaehler
  (ADR 0019 §2.5 Clamp-Counting-Semantik).

`config` wird im `to_dict()`-Mapping als **nested dict mit
explizit benannten Keys** serialisiert (SnapshotEnvelope
akzeptiert keine Dataclass-Objekte; siehe
`hexagon/core/domain/snapshot.py::SnapshotEnvelope.
__post_init__`).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Self

from grid_gym.hexagon.core.errors import VersionError, WrongTypeError
from grid_gym.hexagon.core.grid_model.config import (
    GridModelConfig,
    GridModelConfigError,
)
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_decimal,
    assert_int,
    assert_mapping,
    assert_required_keys,
    assert_str,
)

SUBSYSTEM: Final[str] = "grid_model"
SNAPSHOT_VERSION: Final[int] = 1

# ADR 0019 §2.4 Welle-5a-Identifier; Welle-5+/M3 kann auf
# "power-flow-adapter" o.ae. umstellen.
MODEL_KIND_SIMPLIFIED_PROPORTIONAL: Final[str] = "simplified-proportional"

# Welle-4a-Review-L-3-Pattern: Single-Source-of-Truth fuer die
# Config-Keys; model.py / bilanz.py-Parsing nutzt diese
# Tuple-Reihenfolge.
CONFIG_FIELD_NAMES: Final[tuple[str, ...]] = (
    "nominal_frequency_hz",
    "frequency_sensitivity_hz_per_kw",
    "frequency_clamp_min_hz",
    "frequency_clamp_max_hz",
    "nominal_voltage_v",
    "voltage_sensitivity_v_per_kw",
    "voltage_clamp_min_v",
    "voltage_clamp_max_v",
)

_TOP_KEYS: Final[frozenset[str]] = frozenset(
    {
        "version",
        "config",
        "model_kind",
        "current_frequency_hz",
        "current_voltage_v",
        "last_imbalance_kw",
        "clamp_event_count",
    }
)
_CONFIG_KEYS: Final[frozenset[str]] = frozenset(CONFIG_FIELD_NAMES)


@dataclass(frozen=True, slots=True)
class GridModelSnapshot:
    """GridModel-Zustand zu einem bestimmten Zeitpunkt.

    Roundtrip-Vertrag (ADR 0013 §2.4-Spiegel): byte-stabil.
    Snapshot ist self-sufficient (ADR 0014 §2.2-Schaerfung).
    """

    version: int
    config: GridModelConfig
    model_kind: str
    current_frequency_hz: Decimal
    current_voltage_v: Decimal
    last_imbalance_kw: Decimal
    clamp_event_count: int

    def to_dict(self) -> Mapping[str, object]:
        """Wandelt den Snapshot in ein `Mapping[str, object]` mit
        `version` als Erst-Feld (ADR 0013 §2.4)."""
        return {
            "version": self.version,
            "config": {key: getattr(self.config, key) for key in CONFIG_FIELD_NAMES},
            "model_kind": self.model_kind,
            "current_frequency_hz": self.current_frequency_hz,
            "current_voltage_v": self.current_voltage_v,
            "last_imbalance_kw": self.last_imbalance_kw,
            "clamp_event_count": self.clamp_event_count,
        }

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Rekonstruiert einen `GridModelSnapshot` aus einem
        Mapping. Wirft typed
        `MissingKeysError`/`WrongTypeError`/`VersionError`
        mit `subsystem="grid_model"`."""
        assert_required_keys(state, _TOP_KEYS, SUBSYSTEM)

        version = assert_int(state["version"], "version", SUBSYSTEM)
        if version != SNAPSHOT_VERSION:
            raise VersionError(SUBSYSTEM, expected=SNAPSHOT_VERSION, found=version)

        model_kind = assert_str(state["model_kind"], "model_kind", SUBSYSTEM)
        # Welle-5a-Review M-1: model_kind ist in Welle 5a auf
        # `MODEL_KIND_SIMPLIFIED_PROPORTIONAL` festgenagelt
        # (ADR 0019 §2.4; Lastenheft §11.2 GG-GRID-002 verlangt
        # explizite Selbstkennzeichnung). Welle 5+/M3 lockert
        # das, wenn weitere Identifier dazukommen.
        if model_kind != MODEL_KIND_SIMPLIFIED_PROPORTIONAL:
            raise WrongTypeError(
                SUBSYSTEM,
                "model_kind",
                MODEL_KIND_SIMPLIFIED_PROPORTIONAL,
                model_kind,
            )
        current_frequency_hz = assert_decimal(
            state["current_frequency_hz"], "current_frequency_hz", SUBSYSTEM
        )
        current_voltage_v = assert_decimal(
            state["current_voltage_v"], "current_voltage_v", SUBSYSTEM
        )
        last_imbalance_kw = assert_decimal(
            state["last_imbalance_kw"], "last_imbalance_kw", SUBSYSTEM
        )
        clamp_event_count = assert_int(state["clamp_event_count"], "clamp_event_count", SUBSYSTEM)

        config_state = assert_mapping(state["config"], "config", SUBSYSTEM)
        assert_required_keys(config_state, _CONFIG_KEYS, SUBSYSTEM)
        config_fields = {
            key: assert_decimal(config_state[key], f"config.{key}", SUBSYSTEM)
            for key in CONFIG_FIELD_NAMES
        }

        try:
            config = GridModelConfig(**config_fields)
        except GridModelConfigError as err:
            raise WrongTypeError(SUBSYSTEM, "config", "valid", str(err)) from err

        return cls(
            version=version,
            config=config,
            model_kind=model_kind,
            current_frequency_hz=current_frequency_hz,
            current_voltage_v=current_voltage_v,
            last_imbalance_kw=last_imbalance_kw,
            clamp_event_count=clamp_event_count,
        )


__all__ = [
    "CONFIG_FIELD_NAMES",
    "MODEL_KIND_SIMPLIFIED_PROPORTIONAL",
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "GridModelSnapshot",
]
