"""`GridModelSnapshot` — Snapshot-Format fuer `GridModelBilanz`
(ADR 0019 §2.5 + ADR 0020 §2.5).

Layout (`version: int` = 2 ab Welle 5b), spiegelt
self-sufficient-Pattern aus ADR 0014 §2.2-Schaerfung:

- `version`, `config` (eingebettet), `model_kind` —
  Identitaet und Selbstkennzeichnung.
- `current_frequency_hz`, `current_voltage_v` — aktueller
  Bilanz-Zustand.
- `last_imbalance_kw` — letzter Imbalance-Input.
- `clamp_event_count` — monoton nicht-fallender Zaehler
  (ADR 0019 §2.5 Clamp-Counting-Semantik).
- `active_load_events: tuple[LoadEvent, ...]` (neu in v2,
  ADR 0020 §2.5).
- `active_load_profiles: tuple[LoadProfile, ...]` (neu in v2,
  ADR 0020 §2.5).

**Backward-Compat-Lesepfad (ADR 0020 §2.6):** `from_dict`
liest sowohl v1-Snapshots (Welle-5a-Stand, ohne LoadEvents/
Profiles) als auch v2-Snapshots (Welle-5b-Stand). v1-Read
liefert leere `LoadEvent`/`LoadProfile`-Tupel; v2-Write
bei jedem `to_dict()`-Aufruf (kein Down-Grade).

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
    TRANSFORMER_LIMIT_FIELD_NAMES,
    GridModelConfig,
    GridModelConfigError,
    TransformerLimitConfig,
)
from grid_gym.hexagon.core.grid_model.loads import (
    LoadEvent,
    LoadProfile,
    LoadProfileFormatError,
)
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_bool,
    assert_decimal,
    assert_int,
    assert_mapping,
    assert_required_keys,
    assert_str,
)

SUBSYSTEM: Final[str] = "grid_model"
SNAPSHOT_VERSION: Final[int] = 2
"""Welle 5b: Versions-Bump v1->v2 mit Backward-Compat-Lesepfad
fuer v1-Snapshots aus Welle 5a."""

_SUPPORTED_VERSIONS: Final[frozenset[int]] = frozenset({1, 2})

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

# v1-Felder (Welle 5a) — Pflicht-Set fuer beide Versionen.
_V1_TOP_KEYS: Final[frozenset[str]] = frozenset(
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
# v2-Zusatzfelder (Welle 5b).
_V2_ADDITIONAL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "active_load_events",
        "active_load_profiles",
    }
)
_V2_TOP_KEYS: Final[frozenset[str]] = _V1_TOP_KEYS | _V2_ADDITIONAL_KEYS
_CONFIG_KEYS: Final[frozenset[str]] = frozenset(CONFIG_FIELD_NAMES)
# M8-Welle-3b (ADR 0061 §2.5): Pflicht-Keys des opt-in Transformer-Blocks.
_TRANSFORMER_LIMIT_KEYS: Final[frozenset[str]] = frozenset(TRANSFORMER_LIMIT_FIELD_NAMES)

# Welle-5b-Review L-3: Welle-4a/5a-Review-L-3-Spiegel — Tupel als
# Single-Source-of-Truth fuer geordnete Serialisierung, frozenset
# daraus als Pflicht-Set fuer assert_required_keys.
LOAD_EVENT_FIELD_NAMES: Final[tuple[str, ...]] = (
    "start_s",
    "duration_s",
    "target_device_id",
    "power_kw",
)
LOAD_PROFILE_FIELD_NAMES: Final[tuple[str, ...]] = (
    "target_device_id",
    "tick_values",
    "tick_ms",
)
_LOAD_EVENT_KEYS: Final[frozenset[str]] = frozenset(LOAD_EVENT_FIELD_NAMES)
_LOAD_PROFILE_KEYS: Final[frozenset[str]] = frozenset(LOAD_PROFILE_FIELD_NAMES)


@dataclass(frozen=True, slots=True)
class GridModelSnapshot:
    """GridModel-Zustand zu einem bestimmten Zeitpunkt.

    Roundtrip-Vertrag (ADR 0013 §2.4-Spiegel): byte-stabil.
    Snapshot ist self-sufficient (ADR 0014 §2.2-Schaerfung).
    Ab Welle 5b traegt das Layout `active_load_events` +
    `active_load_profiles` (v2; ADR 0020 §2.5). v1-Snapshots
    bleiben lesbar via Backward-Compat-Pfad in `from_dict`.
    """

    version: int
    config: GridModelConfig
    model_kind: str
    current_frequency_hz: Decimal
    current_voltage_v: Decimal
    last_imbalance_kw: Decimal
    clamp_event_count: int
    active_load_events: tuple[LoadEvent, ...]
    active_load_profiles: tuple[LoadProfile, ...]
    # M8-Welle-3b (ADR 0061 §2.5): akkumulierter Thermo-State des
    # Transformer-Constraint-Layers; `None` ohne Layer (opt-in, kein
    # Versions-Bump).
    top_oil_temp_c: Decimal | None = None

    def to_dict(self) -> Mapping[str, object]:
        """Wandelt den Snapshot in ein `Mapping[str, object]` mit
        `version` als Erst-Feld (ADR 0013 §2.4). Welle 5b emittiert
        ausschliesslich v2-Snapshots (kein Down-Grade auf v1)."""
        config_dict: dict[str, object] = {
            key: getattr(self.config, key) for key in CONFIG_FIELD_NAMES
        }
        # M8-Welle-3a (ADR 0060 §2.4): Insel-Keys opt-in — nur bei
        # is_islanded emittieren, damit der Connected-Default byte-identisch
        # bleibt (EXPECTED_DEMO_*-Hash-Pins unberuehrt, kein Schema-Bump v2->v3).
        if self.config.is_islanded:
            config_dict["is_islanded"] = self.config.is_islanded
            config_dict["forming_device_id"] = self.config.forming_device_id
        # M8-Welle-3b (ADR 0061 §2.5): Transformer-Block opt-in im config-
        # Sub-Mapping (nur bei aktivem Layer → Default byte-identisch).
        if self.config.transformer_limit is not None:
            config_dict["transformer_limit"] = {
                key: getattr(self.config.transformer_limit, key)
                for key in TRANSFORMER_LIMIT_FIELD_NAMES
            }
        top_level: dict[str, object] = {
            "version": self.version,
            "config": config_dict,
            "model_kind": self.model_kind,
            "current_frequency_hz": self.current_frequency_hz,
            "current_voltage_v": self.current_voltage_v,
            "last_imbalance_kw": self.last_imbalance_kw,
            "clamp_event_count": self.clamp_event_count,
            "active_load_events": [
                {
                    "start_s": event.start_s,
                    "duration_s": event.duration_s,
                    "target_device_id": event.target_device_id,
                    "power_kw": event.power_kw,
                }
                for event in self.active_load_events
            ],
            "active_load_profiles": [
                {
                    "target_device_id": profile.target_device_id,
                    "tick_values": list(profile.tick_values),
                    "tick_ms": profile.tick_ms,
                }
                for profile in self.active_load_profiles
            ],
        }
        # M8-Welle-3b (ADR 0061 §2.5): Thermo-State opt-in (nur bei aktivem
        # Layer → Default byte-identisch, kein Versions-Bump).
        if self.top_oil_temp_c is not None:
            top_level["top_oil_temp_c"] = self.top_oil_temp_c
        return top_level

    @classmethod
    def from_dict(cls, state: Mapping[str, object]) -> Self:
        """Rekonstruiert einen `GridModelSnapshot` aus einem
        Mapping. Wirft typed
        `MissingKeysError`/`WrongTypeError`/`VersionError`
        mit `subsystem="grid_model"`.

        Versions-Verzweigung (ADR 0020 §2.6 Backward-Compat):
        - v1 (Welle 5a, ohne LoadEvents/Profiles): liest mit
          leeren `active_load_events`/`active_load_profiles`-
          Tupeln.
        - v2 (Welle 5b): liest die beiden neuen Felder als
          Pflicht.

        **Welle-5b-Review M-4 — Semantik-Toleranz:** Der
        Snapshot-Roundtrip ist **semantisch tolerant**:
        `from_dict(...)` prueft Pro-LoadEvent/LoadProfile-
        Invarianten (`__post_init__`), aber nicht Cross-Item-
        Konflikte (z. B. ueberlappende Same-Device-Events).
        Die Cross-Item-Validierung ist Welle-6-Scenario-Loader-
        Verantwortung (ADR 0020 §2.2 / §7); ein verkonfigurierter
        Snapshot kommt nach `from_dict` formal durch, wirft
        aber spaeter in der TickLoop-Verdrahtung.
        """
        if "version" not in state:
            from grid_gym.hexagon.core.errors import MissingKeysError

            raise MissingKeysError(SUBSYSTEM, ["version"])
        version = assert_int(state["version"], "version", SUBSYSTEM)
        if version not in _SUPPORTED_VERSIONS:
            raise VersionError(SUBSYSTEM, expected=SNAPSHOT_VERSION, found=version)

        # Pflicht-Felder gelten fuer beide Versionen; v2 erweitert.
        required_keys = _V1_TOP_KEYS if version == 1 else _V2_TOP_KEYS
        assert_required_keys(state, required_keys, SUBSYSTEM)

        model_kind = assert_str(state["model_kind"], "model_kind", SUBSYSTEM)
        # Welle-5a-Review M-1: model_kind ist in Welle 5a/5b auf
        # `MODEL_KIND_SIMPLIFIED_PROPORTIONAL` festgenagelt
        # (ADR 0019 §2.4). Welle 5+/M3 lockert das.
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

        config = _parse_config(state["config"])

        if version == 1:
            # Backward-Compat: v1-Snapshots haben keine LoadEvents/
            # Profiles; defaults auf leere Tupel.
            active_load_events: tuple[LoadEvent, ...] = ()
            active_load_profiles: tuple[LoadProfile, ...] = ()
        else:
            active_load_events = _parse_load_events(state["active_load_events"])
            active_load_profiles = _parse_load_profiles(state["active_load_profiles"])

        # M8-Welle-3b (ADR 0061 §2.5): Thermo-State optional lesen
        # (backward-compat — Alt-Snapshots ohne den Key lesen als „kein Layer").
        top_oil_temp_c = (
            assert_decimal(state["top_oil_temp_c"], "top_oil_temp_c", SUBSYSTEM)
            if "top_oil_temp_c" in state
            else None
        )

        return cls(
            version=version,
            config=config,
            model_kind=model_kind,
            current_frequency_hz=current_frequency_hz,
            current_voltage_v=current_voltage_v,
            last_imbalance_kw=last_imbalance_kw,
            clamp_event_count=clamp_event_count,
            active_load_events=active_load_events,
            active_load_profiles=active_load_profiles,
            top_oil_temp_c=top_oil_temp_c,
        )


def _parse_config(raw: object) -> GridModelConfig:
    """Rekonstruiert die `GridModelConfig` aus dem `config`-Sub-Mapping.

    Die acht Decimal-Felder sind Pflicht; die M8-Welle-3a-Insel-Keys
    (`is_islanded`/`forming_device_id`, ADR 0060 §2.4) werden **optional**
    gelesen (backward-compat — Alt-Snapshots ohne die Keys lesen als
    netzgekoppelt). Die Presence-Biconditional (ADR 0060 §2.1) erzwingt der
    `GridModelConfig`-Konstruktor; sein `GridModelConfigError` wird zu
    `WrongTypeError(subsystem="grid_model", field="config")` ueberfuehrt
    (Welle-3-Review-L-1 / Welle-4b-Review-M-2-Pattern)."""
    config_state = assert_mapping(raw, "config", SUBSYSTEM)
    assert_required_keys(config_state, _CONFIG_KEYS, SUBSYSTEM)
    config_fields = {
        key: assert_decimal(config_state[key], f"config.{key}", SUBSYSTEM)
        for key in CONFIG_FIELD_NAMES
    }
    is_islanded = (
        assert_bool(config_state["is_islanded"], "config.is_islanded", SUBSYSTEM)
        if "is_islanded" in config_state
        else False
    )
    forming_device_id = (
        assert_str(config_state["forming_device_id"], "config.forming_device_id", SUBSYSTEM)
        if "forming_device_id" in config_state
        else None
    )
    try:
        # _parse_transformer_limit konstruiert TransformerLimitConfig (mit
        # eigener Wertebereichs-Validierung); muss daher INNERHALB des
        # try liegen, damit auch dessen GridModelConfigError zu WrongTypeError
        # ueberfuehrt wird.
        transformer_limit = _parse_transformer_limit(config_state)
        return GridModelConfig(
            **config_fields,
            is_islanded=is_islanded,
            forming_device_id=forming_device_id,
            transformer_limit=transformer_limit,
        )
    except GridModelConfigError as err:
        raise WrongTypeError(SUBSYSTEM, "config", "valid", str(err)) from err


def _parse_transformer_limit(config_state: Mapping[str, object]) -> TransformerLimitConfig | None:
    """M8-Welle-3b (ADR 0061 §2.5): liest den optionalen
    `transformer_limit`-Block aus dem `config`-Sub-Mapping (opt-in —
    Alt-Snapshots ohne den Key lesen als „kein Layer"). Die Wertebereichs-
    Invarianten (ADR 0061 §2.1) erzwingt der `TransformerLimitConfig`-
    Konstruktor; sein `GridModelConfigError` wird vom Aufrufer zu
    `WrongTypeError` ueberfuehrt."""
    if "transformer_limit" not in config_state:
        return None
    block = assert_mapping(config_state["transformer_limit"], "config.transformer_limit", SUBSYSTEM)
    assert_required_keys(block, _TRANSFORMER_LIMIT_KEYS, SUBSYSTEM)
    fields = {
        key: assert_decimal(block[key], f"config.transformer_limit.{key}", SUBSYSTEM)
        for key in TRANSFORMER_LIMIT_FIELD_NAMES
    }
    return TransformerLimitConfig(**fields)


def _parse_load_events(raw: object) -> tuple[LoadEvent, ...]:
    """Parst eine Liste von LoadEvent-Mappings; wirft typed
    Subsystem-Fehler bei Verstoss."""
    if not isinstance(raw, list):
        raise WrongTypeError(
            SUBSYSTEM,
            "active_load_events",
            "list",
            type(raw).__name__,
        )
    events: list[LoadEvent] = []
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise WrongTypeError(
                SUBSYSTEM,
                f"active_load_events[{index}]",
                "Mapping",
                type(item).__name__,
            )
        assert_required_keys(item, _LOAD_EVENT_KEYS, SUBSYSTEM)
        start_s = assert_decimal(item["start_s"], f"active_load_events[{index}].start_s", SUBSYSTEM)
        duration_s = assert_decimal(
            item["duration_s"], f"active_load_events[{index}].duration_s", SUBSYSTEM
        )
        target_device_id = assert_str(
            item["target_device_id"],
            f"active_load_events[{index}].target_device_id",
            SUBSYSTEM,
        )
        power_kw = assert_decimal(
            item["power_kw"], f"active_load_events[{index}].power_kw", SUBSYSTEM
        )
        try:
            events.append(
                LoadEvent(
                    start_s=start_s,
                    duration_s=duration_s,
                    target_device_id=target_device_id,
                    power_kw=power_kw,
                )
            )
        except LoadProfileFormatError as err:
            raise WrongTypeError(
                SUBSYSTEM,
                f"active_load_events[{index}]",
                "valid LoadEvent",
                str(err),
            ) from err
    return tuple(events)


def _parse_load_profiles(raw: object) -> tuple[LoadProfile, ...]:
    """Parst eine Liste von LoadProfile-Mappings; wirft typed
    Subsystem-Fehler bei Verstoss."""
    if not isinstance(raw, list):
        raise WrongTypeError(
            SUBSYSTEM,
            "active_load_profiles",
            "list",
            type(raw).__name__,
        )
    profiles: list[LoadProfile] = []
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise WrongTypeError(
                SUBSYSTEM,
                f"active_load_profiles[{index}]",
                "Mapping",
                type(item).__name__,
            )
        assert_required_keys(item, _LOAD_PROFILE_KEYS, SUBSYSTEM)
        target_device_id = assert_str(
            item["target_device_id"],
            f"active_load_profiles[{index}].target_device_id",
            SUBSYSTEM,
        )
        tick_ms = assert_int(item["tick_ms"], f"active_load_profiles[{index}].tick_ms", SUBSYSTEM)
        raw_tick_values = item["tick_values"]
        if not isinstance(raw_tick_values, list):
            raise WrongTypeError(
                SUBSYSTEM,
                f"active_load_profiles[{index}].tick_values",
                "list",
                type(raw_tick_values).__name__,
            )
        tick_values_decimal = tuple(
            assert_decimal(
                v,
                f"active_load_profiles[{index}].tick_values[{j}]",
                SUBSYSTEM,
            )
            for j, v in enumerate(raw_tick_values)
        )
        try:
            profiles.append(
                LoadProfile(
                    target_device_id=target_device_id,
                    tick_values=tick_values_decimal,
                    tick_ms=tick_ms,
                )
            )
        except LoadProfileFormatError as err:
            raise WrongTypeError(
                SUBSYSTEM,
                f"active_load_profiles[{index}]",
                "valid LoadProfile",
                str(err),
            ) from err
    return tuple(profiles)


__all__ = [
    "CONFIG_FIELD_NAMES",
    "MODEL_KIND_SIMPLIFIED_PROPORTIONAL",
    "SNAPSHOT_VERSION",
    "SUBSYSTEM",
    "GridModelSnapshot",
]
