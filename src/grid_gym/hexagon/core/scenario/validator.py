"""Schema-Validierung fuer Szenario-Mappings (`GG-SCN-001`/`008`).

Welle 5 nimmt ein `Mapping[str, object]` entgegen (z. B. das
Ergebnis eines YAML-Parsers im Adapter) und validiert es gegen
das `GG-SCN-001`-Schema: Pflicht-Keys, Typen, eindeutige Geraete-
IDs, Events-Ziele auf bekannte Geraete.

YAML-File-Parsing ist explizit Adapter-Verantwortung — der
Validator sieht nur strukturelle Maps. Damit bleibt
`AC-HEXAGON-PURE` ohne PyYAML-Whitelist-Erweiterung
(`docs/user/code-review.md` §3.5).

**Payload-Vertrag** (`ScenarioDevice.params`, `ScenarioEvent.payload`,
`ScenarioFault.payload`): Welle 5 prueft hier nur die strukturelle
`Mapping`-Form, NICHT die Werte rekursiv. `loader.py` hashed das
Szenario anschliessend per `canonical_json(asdict(scenario))` —
nicht-canonical-faehige Werte (insbesondere `float`) loesen dort
`FloatNotAllowedError` aus dem Encoder aus, NICHT eine
`Scenario*Error`-Subklasse. Aufrufer, die mit unkontrolliertem
Payload-Input arbeiten (z. B. YAML-Adapter mit `yaml.safe_load`,
das Floats produziert), MUESSEN am Adapter-Rand Decimal-
Konvertierung erzwingen. Pattern-Drift zur Scheduler-Boundary
(Welle-3-Review S2 hat dort eager-canonical eingefuehrt) ist im
Folge-Trigger 014 als Vereinheitlichungs-Punkt vorgemerkt.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from grid_gym.hexagon.core.errors import (
    ScenarioDuplicateDeviceIdError,
    ScenarioMissingKeysError,
    ScenarioUnknownEventTargetError,
    ScenarioUnsupportedReplayFormatError,
    ScenarioUnsupportedSchemaVersionError,
    ScenarioUnsupportedTimeMappingError,
    ScenarioWrongTypeError,
)

SUPPORTED_SCHEMA_VERSION: Final[str] = "grid-gym.scenario.v1"
"""Welle-5-Stand: nur eine Schema-Version unterstuetzt. Bumps
kommen mit eigener Folge-ADR."""

SUPPORTED_REPLAY_FORMATS: Final[tuple[str, ...]] = ("csv", "jsonl")
"""`GG-REPLAY-001`-Akzeptanz: CSV und JSON-Lines fuer MVP."""

SUPPORTED_TIME_MAPPINGS: Final[tuple[str, ...]] = ("monotonic", "index")
"""`hexagon/core/replay/mapper.py`-Strategien: ISO-8601-Deltas
oder Index-basiert. Erweiterungen brauchen Mapper-Code."""

_REQUIRED_TOP_LEVEL: Final[frozenset[str]] = frozenset(
    {"schema_version", "metadata", "simulation", "devices"}
)
"""Pflicht-Top-Level-Keys per `GG-SCN-001` Akzeptanzkriterium.

`events`, `replay`, `faults` sind optional und werden vom Loader
auf leere Tupel / `None` gemappt, wenn nicht vorhanden.
"""

_REQUIRED_METADATA: Final[frozenset[str]] = frozenset({"id", "name"})
_REQUIRED_SIMULATION: Final[frozenset[str]] = frozenset({"tick_ms", "duration_s", "seed"})
_REQUIRED_DEVICE: Final[frozenset[str]] = frozenset({"id", "type", "params"})
_REQUIRED_EVENT: Final[frozenset[str]] = frozenset({"simulation_time", "target", "type", "payload"})
_REQUIRED_REPLAY: Final[frozenset[str]] = frozenset(
    {"source", "format", "time_mapping", "validation_status"}
)
_REQUIRED_FAULT: Final[frozenset[str]] = frozenset(
    {"start_simulation_time", "duration_ms", "target", "type", "payload", "recovery"}
)


def validate_scenario_mapping(raw: Mapping[str, object]) -> None:
    """Prueft die Pflicht-Struktur eines Szenario-Mappings.

    Wirft typisierte `ScenarioError`-Subklassen bei jedem Verstoss.
    Eine erfolgreiche Validierung garantiert dem `loader.py`, dass
    die folgenden `dataclass`-Konstruktionen ohne Type-Errors
    durchlaufen.
    """
    _assert_required_keys("scenario", raw, _REQUIRED_TOP_LEVEL)
    _assert_schema_version(raw)
    metadata = _assert_mapping(raw, "metadata")
    _assert_required_keys("metadata", metadata, _REQUIRED_METADATA)
    _assert_str(metadata, "metadata.id")
    _assert_str(metadata, "metadata.name")
    simulation = _assert_mapping(raw, "simulation")
    _assert_required_keys("simulation", simulation, _REQUIRED_SIMULATION)
    _assert_int(simulation, "simulation.tick_ms")
    _assert_int(simulation, "simulation.duration_s")
    _assert_int(simulation, "simulation.seed")
    devices = _assert_device_list(raw)
    _assert_event_list(raw, devices)
    _assert_replay_reference(raw)
    _assert_fault_list(raw)


def _assert_required_keys(
    path: str, mapping: Mapping[str, object], required: frozenset[str]
) -> None:
    missing = required - mapping.keys()
    if missing:
        raise ScenarioMissingKeysError(path, sorted(missing))


def _assert_schema_version(raw: Mapping[str, object]) -> None:
    value = raw["schema_version"]
    if not isinstance(value, str):
        raise ScenarioWrongTypeError("schema_version", "str", type(value).__name__)
    if value != SUPPORTED_SCHEMA_VERSION:
        raise ScenarioUnsupportedSchemaVersionError(SUPPORTED_SCHEMA_VERSION, value)


def _assert_mapping(raw: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = raw[key]
    if not isinstance(value, Mapping):
        raise ScenarioWrongTypeError(key, "Mapping", type(value).__name__)
    return value


def _assert_str(mapping: Mapping[str, object], path: str) -> None:
    leaf = path.split(".")[-1]
    value = mapping[leaf]
    if not isinstance(value, str):
        raise ScenarioWrongTypeError(path, "str", type(value).__name__)


def _assert_int(mapping: Mapping[str, object], path: str) -> None:
    leaf = path.split(".")[-1]
    value = mapping[leaf]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScenarioWrongTypeError(path, "int", type(value).__name__)


def _assert_device_list(raw: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_devices = raw["devices"]
    if not isinstance(raw_devices, list):
        raise ScenarioWrongTypeError("devices", "list", type(raw_devices).__name__)
    seen_ids: set[str] = set()
    validated: list[Mapping[str, object]] = []
    for index, entry in enumerate(raw_devices):
        if not isinstance(entry, Mapping):
            raise ScenarioWrongTypeError(f"devices[{index}]", "Mapping", type(entry).__name__)
        _assert_required_keys(f"devices[{index}]", entry, _REQUIRED_DEVICE)
        _assert_str(entry, f"devices[{index}].id")
        _assert_str(entry, f"devices[{index}].type")
        params = entry["params"]
        if not isinstance(params, Mapping):
            raise ScenarioWrongTypeError(
                f"devices[{index}].params", "Mapping", type(params).__name__
            )
        device_id = entry["id"]
        # `_assert_str` oben hat den Typ bereits geprueft.
        if not isinstance(device_id, str):  # pragma: no cover
            raise ScenarioWrongTypeError(f"devices[{index}].id", "str", type(device_id).__name__)
        if device_id in seen_ids:
            raise ScenarioDuplicateDeviceIdError(device_id)
        seen_ids.add(device_id)
        validated.append(entry)
    return validated


def _assert_event_list(raw: Mapping[str, object], devices: list[Mapping[str, object]]) -> None:
    if "events" not in raw:
        return
    raw_events = raw["events"]
    if not isinstance(raw_events, list):
        raise ScenarioWrongTypeError("events", "list", type(raw_events).__name__)
    device_ids = {device["id"] for device in devices}
    for index, entry in enumerate(raw_events):
        if not isinstance(entry, Mapping):
            raise ScenarioWrongTypeError(f"events[{index}]", "Mapping", type(entry).__name__)
        _assert_required_keys(f"events[{index}]", entry, _REQUIRED_EVENT)
        _assert_int(entry, f"events[{index}].simulation_time")
        _assert_str(entry, f"events[{index}].target")
        _assert_str(entry, f"events[{index}].type")
        payload = entry["payload"]
        if not isinstance(payload, Mapping):
            raise ScenarioWrongTypeError(
                f"events[{index}].payload", "Mapping", type(payload).__name__
            )
        target = entry["target"]
        if not isinstance(target, str):  # pragma: no cover
            raise ScenarioWrongTypeError(f"events[{index}].target", "str", type(target).__name__)
        if target not in device_ids:
            raise ScenarioUnknownEventTargetError(target)


def _assert_replay_reference(raw: Mapping[str, object]) -> None:
    if "replay" not in raw:
        return
    replay = raw["replay"]
    if not isinstance(replay, Mapping):
        raise ScenarioWrongTypeError("replay", "Mapping", type(replay).__name__)
    _assert_required_keys("replay", replay, _REQUIRED_REPLAY)
    for field in ("source", "format", "time_mapping", "validation_status"):
        _assert_str(replay, f"replay.{field}")
    # Semantik-Validierung (Welle-5-Review-v2 Befund 2):
    format_value = replay["format"]
    if isinstance(format_value, str) and format_value not in SUPPORTED_REPLAY_FORMATS:
        raise ScenarioUnsupportedReplayFormatError(SUPPORTED_REPLAY_FORMATS, format_value)
    time_mapping_value = replay["time_mapping"]
    if isinstance(time_mapping_value, str) and time_mapping_value not in SUPPORTED_TIME_MAPPINGS:
        raise ScenarioUnsupportedTimeMappingError(SUPPORTED_TIME_MAPPINGS, time_mapping_value)


def _assert_fault_list(raw: Mapping[str, object]) -> None:
    if "faults" not in raw:
        return
    raw_faults = raw["faults"]
    if not isinstance(raw_faults, list):
        raise ScenarioWrongTypeError("faults", "list", type(raw_faults).__name__)
    for index, entry in enumerate(raw_faults):
        if not isinstance(entry, Mapping):
            raise ScenarioWrongTypeError(f"faults[{index}]", "Mapping", type(entry).__name__)
        _assert_required_keys(f"faults[{index}]", entry, _REQUIRED_FAULT)
        _assert_int(entry, f"faults[{index}].start_simulation_time")
        _assert_int(entry, f"faults[{index}].duration_ms")
        _assert_str(entry, f"faults[{index}].target")
        _assert_str(entry, f"faults[{index}].type")
        payload = entry["payload"]
        if not isinstance(payload, Mapping):
            raise ScenarioWrongTypeError(
                f"faults[{index}].payload", "Mapping", type(payload).__name__
            )
        _assert_str(entry, f"faults[{index}].recovery")
