"""Tests fuer `hexagon/core/scenario/{validator,loader}.py`
(M1 Welle 5, `GG-SCN-001..008`).

Pinnt:
- Erfolgreicher Roundtrip auf einem minimalen + voll-bestueckten
  Mapping.
- Hash-Stabilitaet: gleicher Input → gleicher `scenario_hash`.
- Hash-Sensitivitaet: kleinste Aenderung → anderer Hash.
- Typisierte Negativ-Pfade fuer alle Pflicht-Konstrukte.
"""

from __future__ import annotations

import pytest

from grid_gym.hexagon.core.domain.scenario import Scenario
from grid_gym.hexagon.core.errors import (
    ScenarioDuplicateDeviceIdError,
    ScenarioMissingKeysError,
    ScenarioUnknownEventTargetError,
    ScenarioUnsupportedReplayFormatError,
    ScenarioUnsupportedSchemaVersionError,
    ScenarioUnsupportedTimeMappingError,
    ScenarioWrongTypeError,
)
from grid_gym.hexagon.core.scenario.loader import load_scenario

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _minimal_mapping() -> dict[str, object]:
    """Minimal-Mapping nach `GG-SCN-001`: schema_version + metadata
    + simulation + devices."""
    return {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"id": "demo", "name": "Demo Scenario"},
        "simulation": {"tick_ms": 100, "duration_s": 60, "seed": 42},
        "devices": [
            {"id": "grid-1", "type": "grid_connection", "params": {}},
        ],
    }


def _full_mapping() -> dict[str, object]:
    """Voll-bestuecktes Mapping mit events/replay/faults."""
    return {
        **_minimal_mapping(),
        "events": [
            {
                "simulation_time": 1000,
                "target": "grid-1",
                "type": "dispatch",
                "payload": {"setpoint_kw": 100},
            }
        ],
        "replay": {
            "source": "/data/replay.csv",
            "format": "csv",
            "time_mapping": "monotonic",
            "validation_status": "validated",
        },
        "faults": [
            {
                "start_simulation_time": 2000,
                "duration_ms": 500,
                "target": "grid-1",
                "type": "voltage_drop",
                "payload": {"depth_pu": "0.2"},
                "recovery": "auto",
            }
        ],
    }


# ---------------------------------------------------------------------------
# Happy-Path
# ---------------------------------------------------------------------------


def test_load_minimal_scenario_returns_scenario_and_hash() -> None:
    result = load_scenario(_minimal_mapping())
    assert isinstance(result.scenario, Scenario)
    assert result.scenario.schema_version == "grid-gym.scenario.v1"
    assert result.scenario.metadata.id == "demo"
    assert result.scenario.simulation.tick_ms == 100
    assert len(result.scenario.devices) == 1
    assert result.scenario.events == ()
    assert result.scenario.replay is None
    assert result.scenario.faults == ()
    # Hash ist 64 Hex-Stellen (SHA-256).
    assert len(result.scenario_hash) == 64
    assert all(c in "0123456789abcdef" for c in result.scenario_hash)


def test_load_full_scenario_carries_events_replay_faults() -> None:
    result = load_scenario(_full_mapping())
    assert len(result.scenario.events) == 1
    assert result.scenario.events[0].target == "grid-1"
    assert result.scenario.replay is not None
    assert result.scenario.replay.format == "csv"
    assert len(result.scenario.faults) == 1
    assert result.scenario.faults[0].type == "voltage_drop"


# ---------------------------------------------------------------------------
# Hash-Eigenschaften (`GG-SCN-003`/`004`)
# ---------------------------------------------------------------------------


def test_load_scenario_hash_is_stable_for_same_mapping() -> None:
    a = load_scenario(_minimal_mapping())
    b = load_scenario(_minimal_mapping())
    assert a.scenario_hash == b.scenario_hash


def test_load_scenario_hash_changes_with_seed_change() -> None:
    a = load_scenario(_minimal_mapping())
    mapping = _minimal_mapping()
    simulation = mapping["simulation"]
    assert isinstance(simulation, dict)
    simulation["seed"] = 43
    b = load_scenario(mapping)
    assert a.scenario_hash != b.scenario_hash


def test_load_scenario_hash_changes_with_device_id_change() -> None:
    a = load_scenario(_minimal_mapping())
    mapping = _minimal_mapping()
    devices = mapping["devices"]
    assert isinstance(devices, list)
    device = devices[0]
    assert isinstance(device, dict)
    device["id"] = "grid-2"
    b = load_scenario(mapping)
    assert a.scenario_hash != b.scenario_hash


# ---------------------------------------------------------------------------
# Schema-Negativ-Pfade (`GG-SCN-008`)
# ---------------------------------------------------------------------------


def test_load_scenario_rejects_missing_top_level_key() -> None:
    mapping = _minimal_mapping()
    del mapping["metadata"]
    with pytest.raises(ScenarioMissingKeysError):
        load_scenario(mapping)


def test_load_scenario_rejects_wrong_schema_version() -> None:
    mapping = _minimal_mapping()
    mapping["schema_version"] = "grid-gym.scenario.v2"
    with pytest.raises(ScenarioUnsupportedSchemaVersionError):
        load_scenario(mapping)


def test_load_scenario_rejects_non_string_schema_version() -> None:
    mapping = _minimal_mapping()
    mapping["schema_version"] = 1
    with pytest.raises(ScenarioWrongTypeError):
        load_scenario(mapping)


def test_load_scenario_rejects_non_int_tick_ms() -> None:
    mapping = _minimal_mapping()
    simulation = mapping["simulation"]
    assert isinstance(simulation, dict)
    simulation["tick_ms"] = "100"
    with pytest.raises(ScenarioWrongTypeError):
        load_scenario(mapping)


def test_load_scenario_rejects_bool_seed() -> None:
    """`bool` ist `int`-Subklasse — fuer Seed explizit abgelehnt."""
    mapping = _minimal_mapping()
    simulation = mapping["simulation"]
    assert isinstance(simulation, dict)
    simulation["seed"] = True
    with pytest.raises(ScenarioWrongTypeError):
        load_scenario(mapping)


def test_load_scenario_rejects_duplicate_device_ids() -> None:
    mapping = _minimal_mapping()
    mapping["devices"] = [
        {"id": "dup", "type": "grid_connection", "params": {}},
        {"id": "dup", "type": "pv", "params": {}},
    ]
    with pytest.raises(ScenarioDuplicateDeviceIdError):
        load_scenario(mapping)


def test_load_scenario_rejects_event_targeting_unknown_device() -> None:
    mapping = _minimal_mapping()
    mapping["events"] = [
        {
            "simulation_time": 1000,
            "target": "ghost-device",
            "type": "dispatch",
            "payload": {},
        }
    ]
    with pytest.raises(ScenarioUnknownEventTargetError):
        load_scenario(mapping)


def test_load_scenario_rejects_non_mapping_devices_entry() -> None:
    mapping = _minimal_mapping()
    mapping["devices"] = ["not-a-mapping"]
    with pytest.raises(ScenarioWrongTypeError):
        load_scenario(mapping)


def test_load_scenario_rejects_missing_device_id() -> None:
    mapping = _minimal_mapping()
    mapping["devices"] = [{"type": "grid_connection", "params": {}}]
    with pytest.raises(ScenarioMissingKeysError):
        load_scenario(mapping)


def test_load_scenario_rejects_non_mapping_replay() -> None:
    mapping = _full_mapping()
    mapping["replay"] = "not-a-mapping"
    with pytest.raises(ScenarioWrongTypeError):
        load_scenario(mapping)


def test_load_scenario_rejects_unsupported_replay_format() -> None:
    """Welle-5-Review-v2 Befund 2: `format` muss in {csv, jsonl}
    (`GG-REPLAY-001`)."""
    mapping = _full_mapping()
    replay = mapping["replay"]
    assert isinstance(replay, dict)
    replay["format"] = "parquet"
    with pytest.raises(ScenarioUnsupportedReplayFormatError):
        load_scenario(mapping)


def test_load_scenario_accepts_jsonl_format() -> None:
    """Sanity-Check: `jsonl` ist gueltig (nicht nur `csv`)."""
    mapping = _full_mapping()
    replay = mapping["replay"]
    assert isinstance(replay, dict)
    replay["format"] = "jsonl"
    result = load_scenario(mapping)
    assert result.scenario.replay is not None
    assert result.scenario.replay.format == "jsonl"


def test_load_scenario_rejects_unsupported_time_mapping() -> None:
    """Welle-5-Review-v2 Befund 2: `time_mapping` muss in
    {monotonic, index} (Mapper-API)."""
    mapping = _full_mapping()
    replay = mapping["replay"]
    assert isinstance(replay, dict)
    replay["time_mapping"] = "ntp-drifted"
    with pytest.raises(ScenarioUnsupportedTimeMappingError):
        load_scenario(mapping)


def test_load_scenario_accepts_index_time_mapping() -> None:
    mapping = _full_mapping()
    replay = mapping["replay"]
    assert isinstance(replay, dict)
    replay["time_mapping"] = "index"
    result = load_scenario(mapping)
    assert result.scenario.replay is not None
    assert result.scenario.replay.time_mapping == "index"


def test_load_scenario_rejects_fault_missing_recovery() -> None:
    mapping = _full_mapping()
    faults = mapping["faults"]
    assert isinstance(faults, list)
    fault = faults[0]
    assert isinstance(fault, dict)
    del fault["recovery"]
    with pytest.raises(ScenarioMissingKeysError):
        load_scenario(mapping)
