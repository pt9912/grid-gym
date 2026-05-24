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
`ScenarioFault.payload`): seit M2 Welle 0a (Trigger 014) prueft der
Validator rekursiv via
`hexagon/core/serialization/snapshot_codec.py::assert_payload_canonical_compatible`,
dass alle Payload-Werte canonical-kompatibel sind. Float-, Bytes- oder
Komplexzahlen-Injection vom YAML-Adapter wirft jetzt typisiert
`WrongTypeError(subsystem="scenario", ...)` (Subklasse von
`SnapshotFormatError` und via `ScenarioSchemaError` auch von
`ScenarioError`), nicht mehr `FloatNotAllowedError` aus dem
Hash-Encoder. Pattern-Drift zur Scheduler-Boundary (Welle-3-Review S2)
ist mit Trigger 014 geschlossen.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Final, cast

from grid_gym.hexagon.core.errors import (
    ScenarioDuplicateDeviceIdError,
    ScenarioInvalidAgentParamsError,
    ScenarioInvalidRuleComparatorError,
    ScenarioInvalidRuleMetricError,
    ScenarioMissingKeysError,
    ScenarioUnknownEventTargetError,
    ScenarioUnknownFaultTargetError,
    ScenarioUnsupportedReplayFormatError,
    ScenarioUnsupportedSchemaVersionError,
    ScenarioUnsupportedTimeMappingError,
    ScenarioWrongTypeError,
)
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_payload_canonical_compatible,
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

# Welle-6b (ADR 0021 §2.3): optionale Welle-6b-Top-Level-Sektionen.
# Alle drei sind optional — Welle-6a-Default ist „kein grid_model,
# keine load_events, keine load_profiles".
_REQUIRED_GRID_MODEL: Final[frozenset[str]] = frozenset(
    {
        "nominal_frequency_hz",
        "frequency_sensitivity_hz_per_kw",
        "frequency_clamp_min_hz",
        "frequency_clamp_max_hz",
        "nominal_voltage_v",
        "voltage_sensitivity_v_per_kw",
        "voltage_clamp_min_v",
        "voltage_clamp_max_v",
    }
)
_REQUIRED_LOAD_EVENT: Final[frozenset[str]] = frozenset(
    {"start_s", "duration_s", "target_device_id", "power_kw"}
)
_REQUIRED_LOAD_PROFILE: Final[frozenset[str]] = frozenset(
    {"target_device_id", "tick_values", "tick_ms"}
)

# M3-Welle-4b (ADR 0027 §2.2): `agents`-Top-Level-Block.
_REQUIRED_AGENT_DEF: Final[frozenset[str]] = frozenset({"type", "params"})
"""Pflicht-Keys pro `agents`-Eintrag (nested Mapping). `id` ist
der Dict-Key des umschliessenden `agents`-Blocks, nicht im
agent_def enthalten."""

_REQUIRED_RULE: Final[frozenset[str]] = frozenset({"condition", "action"})
_REQUIRED_RULE_CONDITION: Final[frozenset[str]] = frozenset({"metric", "comparator", "threshold"})
_REQUIRED_RULE_ACTION: Final[frozenset[str]] = frozenset({"type", "payload"})


class _InvalidAgentsKeyTypeError(ScenarioWrongTypeError):
    """`agents`-Block hat einen Key, der kein non-empty `str` ist.

    Slice 027 Paket B TRY003-Drop: Pfad-Praefix `agents[*] key` und
    Erwartungs-String `non-empty str` sind hier statisch — die
    Sub-Klasse haelt sie im `__init__`, damit der Aufrufer kein
    String-Tupel mehr inline bauen muss.
    """

    def __init__(self, actual_key: object) -> None:
        super().__init__("agents[*] key", "non-empty str", type(actual_key).__name__)


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
    _assert_fault_list(raw, devices)
    # Welle-6b (ADR 0021 §2.3): drei optionale Top-Level-Sektionen.
    _assert_grid_model_block(raw)
    _assert_load_events_block(raw, devices)
    _assert_load_profiles_block(raw, devices)
    # M3-Welle-4b (ADR 0027 §2.2): optionaler `agents`-Top-Level-Block.
    _assert_agent_list(raw, devices)


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
        # Payload-Canonical-Check (M2 Welle 0a, Trigger 014): faengt
        # Float-/Bytes-Injection vom YAML-Adapter typisiert ab, bevor
        # `canonical_json` in `loader.py::compute_scenario_hash` mit
        # `FloatNotAllowedError` aus dem Encoder bricht.
        assert_payload_canonical_compatible(params, "scenario", f"devices[{index}].params")
        # `_assert_str` oben hat den Typ bereits als str validiert.
        device_id = cast(str, entry["id"])
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
        assert_payload_canonical_compatible(payload, "scenario", f"events[{index}].payload")
        # `_assert_str` oben hat den Typ bereits als str validiert.
        target = cast(str, entry["target"])
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


def _assert_fault_list(
    raw: Mapping[str, object],
    devices: list[Mapping[str, object]],
) -> None:
    """Validiert den optionalen `faults`-Block.

    Welle-5-Strukturvertrag (Pflicht-Felder, Typen, Payload-
    Canonical-Check) bleibt unveraendert. M3-Welle-1 (ADR 0022
    §2.3) ergaenzt einen Target-Existenz-Check: `fault.target`
    muss in `devices` definiert sein — spiegelt
    `_assert_event_list`-Pattern (`ScenarioUnknownEventTargetError`).

    `devices` ist seit M3-Welle-1-Review-Folge **mandatory**
    (analog `_assert_event_list`). Einziger produktiver Caller
    ist `validate_scenario_mapping`, der die Liste immer
    durchreicht.
    """
    if "faults" not in raw:
        return
    raw_faults = raw["faults"]
    if not isinstance(raw_faults, list):
        raise ScenarioWrongTypeError("faults", "list", type(raw_faults).__name__)
    device_ids: set[str] = {cast(str, device["id"]) for device in devices}
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
        assert_payload_canonical_compatible(payload, "scenario", f"faults[{index}].payload")
        _assert_str(entry, f"faults[{index}].recovery")
        # M3-Welle-1 (ADR 0022 §2.3): Target-Existenz-Check
        # analog `_assert_event_list`.
        target = entry["target"]
        if isinstance(target, str) and target not in device_ids:
            raise ScenarioUnknownFaultTargetError(target)


# ---------------------------------------------------------------------------
# Welle 6b — optionale Top-Level-Sektionen (ADR 0021 §2.3)
# ---------------------------------------------------------------------------


def _assert_decimal(mapping: Mapping[str, object], path: str) -> None:
    """Welle-6b (ADR 0021 §2.3): GG-DATA-005-Decimal-Pflicht
    fuer alle physikalischen Felder (kein float, kein int, kein
    bool)."""
    leaf = path.split(".")[-1]
    value = mapping[leaf]
    if not isinstance(value, Decimal):
        raise ScenarioWrongTypeError(path, "Decimal", type(value).__name__)


def _assert_grid_model_block(raw: Mapping[str, object]) -> None:
    if "grid_model" not in raw:
        return
    block = raw["grid_model"]
    if not isinstance(block, Mapping):
        raise ScenarioWrongTypeError("grid_model", "Mapping", type(block).__name__)
    _assert_required_keys("grid_model", block, _REQUIRED_GRID_MODEL)
    for field in _REQUIRED_GRID_MODEL:
        _assert_decimal(block, f"grid_model.{field}")


def _assert_load_events_block(
    raw: Mapping[str, object], devices: list[Mapping[str, object]]
) -> None:
    if "load_events" not in raw:
        return
    raw_events = raw["load_events"]
    if not isinstance(raw_events, list):
        raise ScenarioWrongTypeError("load_events", "list", type(raw_events).__name__)
    device_ids = {device["id"] for device in devices}
    for index, entry in enumerate(raw_events):
        if not isinstance(entry, Mapping):
            raise ScenarioWrongTypeError(f"load_events[{index}]", "Mapping", type(entry).__name__)
        _assert_required_keys(f"load_events[{index}]", entry, _REQUIRED_LOAD_EVENT)
        _assert_decimal(entry, f"load_events[{index}].start_s")
        _assert_decimal(entry, f"load_events[{index}].duration_s")
        _assert_str(entry, f"load_events[{index}].target_device_id")
        _assert_decimal(entry, f"load_events[{index}].power_kw")
        target = entry["target_device_id"]
        if isinstance(target, str) and target not in device_ids:
            raise ScenarioUnknownEventTargetError(target)


def _assert_load_profiles_block(
    raw: Mapping[str, object], devices: list[Mapping[str, object]]
) -> None:
    if "load_profiles" not in raw:
        return
    raw_profiles = raw["load_profiles"]
    if not isinstance(raw_profiles, list):
        raise ScenarioWrongTypeError("load_profiles", "list", type(raw_profiles).__name__)
    device_ids = {device["id"] for device in devices}
    for index, entry in enumerate(raw_profiles):
        if not isinstance(entry, Mapping):
            raise ScenarioWrongTypeError(f"load_profiles[{index}]", "Mapping", type(entry).__name__)
        _assert_required_keys(f"load_profiles[{index}]", entry, _REQUIRED_LOAD_PROFILE)
        _assert_str(entry, f"load_profiles[{index}].target_device_id")
        _assert_int(entry, f"load_profiles[{index}].tick_ms")
        tick_values = entry["tick_values"]
        if not isinstance(tick_values, list):
            raise ScenarioWrongTypeError(
                f"load_profiles[{index}].tick_values",
                "list[Decimal]",
                type(tick_values).__name__,
            )
        for value_index, value in enumerate(tick_values):
            if not isinstance(value, Decimal):
                raise ScenarioWrongTypeError(
                    f"load_profiles[{index}].tick_values[{value_index}]",
                    "Decimal",
                    type(value).__name__,
                )
        target = entry["target_device_id"]
        if isinstance(target, str) and target not in device_ids:
            raise ScenarioUnknownEventTargetError(target)


# ---------------------------------------------------------------------------
# M3-Welle-4b (ADR 0027 §2.2 + §2.3): `agents`-Top-Level-Block
# ---------------------------------------------------------------------------


def _assert_agent_list(raw: Mapping[str, object], devices: list[Mapping[str, object]]) -> None:
    """ADR 0027 §2.2: Validiert den optionalen `agents`-Block.

    Schema-Form: **nested Mapping** `agents: {<agent_id>:
    {type, params}}`. Aufrufer iteriert spaeter ueber
    `sorted(agents.keys())` lexikographisch fuer Determinismus.

    Pflicht-Pruefungen pro Eintrag:
    - `type` ist String.
    - `params` ist Mapping; canonical-kompatibel
      (`assert_payload_canonical_compatible`).
    - Wenn `params.target_device_id` vorhanden ist: muss in
      `devices` existieren
      (`ScenarioUnknownAgentTargetError`).
    - Hybrid Mutual-Exclusivity-Vertrag (ADR 0027 §2.3):
      genau einer von `rules` (Liste) oder `plugin` (String)
      muss in `params` vorhanden sein
      (`ScenarioInvalidAgentParamsError`).
    - Wenn `rules` vorhanden: pro Eintrag struktureller Check
      (Pflicht-Keys, Comparator-Whitelist, Metric-Whitelist;
      `ScenarioInvalidRuleComparatorError` /
      `ScenarioInvalidRuleMetricError`).

    Welle-4b-Validator macht KEINEN Factory-Type-Whitelist-
    Check fuer `agent.type` (kommt aus der Loader-Factory-Map
    via `ScenarioUnknownAgentTypeError` in `build_agents(...)`)
    und KEINEN Plugin-Registry-Whitelist-Check (kommt aus
    `_AGENT_PLUGIN_FACTORIES` via `ScenarioUnknownAgentPluginError`
    in `build_agents(...)`). Strukturell-Schema-Validierung
    bleibt hier; Factory-Dispatch ist Loader-Pflicht.
    """
    from grid_gym.hexagon.core.agents.rule_based import (
        COMPARATOR_WHITELIST,
        WELLE_4B_METRIC_WHITELIST,
    )

    if "agents" not in raw:
        return
    raw_agents = raw["agents"]
    if not isinstance(raw_agents, Mapping):
        raise ScenarioWrongTypeError("agents", "Mapping", type(raw_agents).__name__)
    device_ids: set[str] = {cast(str, device["id"]) for device in devices}
    for agent_id in sorted(raw_agents.keys()):
        if not isinstance(agent_id, str) or not agent_id:
            raise _InvalidAgentsKeyTypeError(agent_id)
        path = f"agents[{agent_id!r}]"
        entry = raw_agents[agent_id]
        if not isinstance(entry, Mapping):
            raise ScenarioWrongTypeError(path, "Mapping", type(entry).__name__)
        _assert_required_keys(path, entry, _REQUIRED_AGENT_DEF)
        _assert_str(entry, f"{path}.type")
        params = entry["params"]
        if not isinstance(params, Mapping):
            raise ScenarioWrongTypeError(f"{path}.params", "Mapping", type(params).__name__)
        assert_payload_canonical_compatible(params, "scenario", f"{path}.params")
        _assert_agent_target(agent_id, params, device_ids)
        _assert_agent_hybrid_params(
            agent_id, params, COMPARATOR_WHITELIST, WELLE_4B_METRIC_WHITELIST
        )


def _assert_agent_target(
    agent_id: str,
    params: Mapping[str, object],
    device_ids: set[str],
) -> None:
    """ADR 0027 §2.2: `params.target_device_id` (optional) muss
    auf ein bekanntes Device zeigen."""
    from grid_gym.hexagon.core.errors import ScenarioUnknownAgentTargetError

    target = params.get("target_device_id")
    if target is None:
        return
    if not isinstance(target, str):
        raise ScenarioWrongTypeError(
            f"agents[{agent_id!r}].params.target_device_id",
            "str",
            type(target).__name__,
        )
    if target not in device_ids:
        raise ScenarioUnknownAgentTargetError(agent_id, target)


def _assert_agent_hybrid_params(
    agent_id: str,
    params: Mapping[str, object],
    comparator_whitelist: tuple[str, ...],
    metric_whitelist: tuple[str, ...],
) -> None:
    """ADR 0027 §2.3 Mutual Exclusivity: genau einer von
    `rules` (Liste) oder `plugin` (String) muss vorhanden sein."""
    has_rules = "rules" in params
    has_plugin = "plugin" in params
    if has_rules and has_plugin:
        raise ScenarioInvalidAgentParamsError(
            agent_id,
            "params hat sowohl 'rules' als auch 'plugin' "
            "(Mutual-Exclusivity-Verstoss; ADR 0027 §2.3)",
        )
    if not has_rules and not has_plugin:
        raise ScenarioInvalidAgentParamsError(
            agent_id,
            "params hat weder 'rules' noch 'plugin' (kein Decision-Pfad; ADR 0027 §2.3)",
        )
    if has_rules:
        _assert_rules_block(agent_id, params["rules"], comparator_whitelist, metric_whitelist)
    if has_plugin:
        plugin_value = params["plugin"]
        if not isinstance(plugin_value, str):
            raise ScenarioWrongTypeError(
                f"agents[{agent_id!r}].params.plugin",
                "str",
                type(plugin_value).__name__,
            )


def _assert_rules_block(
    agent_id: str,
    rules: object,
    comparator_whitelist: tuple[str, ...],
    metric_whitelist: tuple[str, ...],
) -> None:
    """ADR 0027 §2.3: pro `rules`-Eintrag Pflicht-Struktur +
    Comparator + Metric in Whitelist.

    Slice 027 Paket D: pro-Eintrag-Validierung in Sub-Helper
    extrahiert (`_assert_rule_entry`/`_assert_rule_condition_block`/
    `_assert_rule_action_block`); C901+PLR0915-Drop.
    """
    if not isinstance(rules, list):
        raise ScenarioWrongTypeError(
            f"agents[{agent_id!r}].params.rules", "list", type(rules).__name__
        )
    if not rules:
        raise ScenarioInvalidAgentParamsError(
            agent_id, "params.rules ist leer (kein Decision-Pfad; ADR 0027 §2.3)"
        )
    for index, entry in enumerate(rules):
        path = f"agents[{agent_id!r}].params.rules[{index}]"
        _assert_rule_entry(
            path,
            entry,
            agent_id=agent_id,
            comparator_whitelist=comparator_whitelist,
            metric_whitelist=metric_whitelist,
        )


def _assert_rule_entry(
    path: str,
    entry: object,
    *,
    agent_id: str,
    comparator_whitelist: tuple[str, ...],
    metric_whitelist: tuple[str, ...],
) -> None:
    """Sub-Validator pro `rules[i]` (Slice 027 Paket D)."""
    if not isinstance(entry, Mapping):
        raise ScenarioWrongTypeError(path, "Mapping", type(entry).__name__)
    _assert_required_keys(path, entry, _REQUIRED_RULE)
    _assert_rule_condition_block(
        f"{path}.condition",
        entry["condition"],
        agent_id=agent_id,
        comparator_whitelist=comparator_whitelist,
        metric_whitelist=metric_whitelist,
    )
    _assert_rule_action_block(f"{path}.action", entry["action"])


def _assert_rule_condition_block(
    path: str,
    condition: object,
    *,
    agent_id: str,
    comparator_whitelist: tuple[str, ...],
    metric_whitelist: tuple[str, ...],
) -> None:
    """Sub-Validator fuer `rules[i].condition` (Slice 027 Paket D)."""
    if not isinstance(condition, Mapping):
        raise ScenarioWrongTypeError(path, "Mapping", type(condition).__name__)
    _assert_required_keys(path, condition, _REQUIRED_RULE_CONDITION)
    metric = condition["metric"]
    if not isinstance(metric, str):
        raise ScenarioWrongTypeError(f"{path}.metric", "str", type(metric).__name__)
    if metric not in metric_whitelist:
        raise ScenarioInvalidRuleMetricError(agent_id, metric, metric_whitelist)
    comparator = condition["comparator"]
    if not isinstance(comparator, str):
        raise ScenarioWrongTypeError(f"{path}.comparator", "str", type(comparator).__name__)
    if comparator not in comparator_whitelist:
        raise ScenarioInvalidRuleComparatorError(agent_id, comparator, comparator_whitelist)
    threshold = condition["threshold"]
    if isinstance(threshold, bool) or not isinstance(threshold, int):
        raise ScenarioWrongTypeError(f"{path}.threshold", "int", type(threshold).__name__)


def _assert_rule_action_block(path: str, action: object) -> None:
    """Sub-Validator fuer `rules[i].action` (Slice 027 Paket D)."""
    if not isinstance(action, Mapping):
        raise ScenarioWrongTypeError(path, "Mapping", type(action).__name__)
    _assert_required_keys(path, action, _REQUIRED_RULE_ACTION)
    _assert_str(action, f"{path}.type")
    payload = action["payload"]
    if not isinstance(payload, Mapping):
        raise ScenarioWrongTypeError(f"{path}.payload", "Mapping", type(payload).__name__)
