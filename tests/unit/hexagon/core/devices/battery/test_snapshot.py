"""Tests fuer `BatterySnapshot` (Welle-2-Roundtrip-Vertrag, ADR 0014).

Pinnt:
- Roundtrip `from_dict(to_dict()) == snapshot` byte-stabil.
- `version` ist Erst-Feld in `to_dict()`-Mapping (ADR 0013 §2.4).
- Codec-Errors fuer fehlende/falsche Top-Level-Keys,
  Config-Sub-Keys, Decimal-Werte, Version-Mismatch.
- `SnapshotEnvelope.__post_init__` akzeptiert den Battery-Snapshot
  (End-to-End-Verifikation gegen Welle-0a-Codec).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.devices.battery.config import (
    BatteryConfig,
    CellConfig,
    ThermalConfig,
)
from grid_gym.hexagon.core.devices.battery.snapshot import (
    SNAPSHOT_VERSION,
    BatterySnapshot,
)
from grid_gym.hexagon.core.domain.snapshot import SnapshotEnvelope
from grid_gym.hexagon.core.errors import (
    MissingKeysError,
    VersionError,
    WrongTypeError,
)


def _make_snapshot() -> BatterySnapshot:
    config = BatteryConfig(
        capacity_kwh=Decimal("1000"),
        initial_soc_pct=Decimal("50"),
        min_soc_pct=Decimal("10"),
        max_soc_pct=Decimal("90"),
        max_charge_kw=Decimal("500"),
        max_discharge_kw=Decimal("500"),
        charge_efficiency=Decimal("0.95"),
        discharge_efficiency=Decimal("0.95"),
        ramp_kw_per_s=Decimal("50"),
    )
    return BatterySnapshot(
        version=SNAPSHOT_VERSION,
        device_id="battery-1",
        run_id="run-42",
        sequence=0,
        config=config,
        soc_kwh=Decimal("500"),
        current_power_kw=Decimal("0"),
        pending_power_kw=Decimal("0"),
    )


# ---------------------------------------------------------------------------
# Happy-Path-Roundtrip
# ---------------------------------------------------------------------------


def test_to_dict_has_version_as_first_field() -> None:
    """ADR 0013 §2.4: `version` ist Erst-Feld im Mapping."""
    snapshot = _make_snapshot()
    state = snapshot.to_dict()
    assert next(iter(state)) == "version"
    assert state["version"] == SNAPSHOT_VERSION


def test_from_dict_to_dict_roundtrip_is_byte_stable() -> None:
    """`from_dict(to_dict(snapshot)) == snapshot` byte-stabil
    (ADR 0013 §2.4 Roundtrip-Pflicht)."""
    snapshot = _make_snapshot()
    restored = BatterySnapshot.from_dict(snapshot.to_dict())
    assert restored == snapshot


def test_snapshot_envelope_accepts_battery_snapshot() -> None:
    """End-to-End: SnapshotEnvelope-Composition akzeptiert das
    Battery-Snapshot-Mapping (Welle-0a-Item-5-Payload-Canonical-
    Walk)."""
    snapshot = _make_snapshot()
    envelope = SnapshotEnvelope(
        version=1,
        run_id="r",
        simulation_time=0,
        sub_snapshots={"devices.battery-1": snapshot.to_dict()},
    )
    assert "devices.battery-1" in envelope.sub_snapshots


# ---------------------------------------------------------------------------
# Codec-Errors
# ---------------------------------------------------------------------------


def test_from_dict_missing_top_level_key() -> None:
    state = _make_snapshot().to_dict()
    state = {k: v for k, v in state.items() if k != "soc_kwh"}
    with pytest.raises(MissingKeysError) as exc_info:
        BatterySnapshot.from_dict(state)
    assert exc_info.value.subsystem == "battery"
    assert "soc_kwh" in str(exc_info.value)


def test_from_dict_missing_config_sub_key() -> None:
    state = dict(_make_snapshot().to_dict())
    config = dict(state["config"])  # type: ignore[arg-type]
    del config["capacity_kwh"]
    state["config"] = config
    with pytest.raises(MissingKeysError) as exc_info:
        BatterySnapshot.from_dict(state)
    assert exc_info.value.subsystem == "battery"
    assert "capacity_kwh" in str(exc_info.value)


def test_from_dict_wrong_version_type_rejected() -> None:
    state = dict(_make_snapshot().to_dict())
    state["version"] = "1"  # str statt int
    with pytest.raises(WrongTypeError) as exc_info:
        BatterySnapshot.from_dict(state)
    assert exc_info.value.subsystem == "battery"
    assert "version" in str(exc_info.value)


def test_from_dict_bool_version_rejected() -> None:
    """`bool` ist `int`-Subklasse — Schema-Versionen sind aber
    Ganzzahlen, keine Wahrheitswerte."""
    state = dict(_make_snapshot().to_dict())
    state["version"] = True
    with pytest.raises(WrongTypeError):
        BatterySnapshot.from_dict(state)


def test_from_dict_unsupported_version_raises_version_error() -> None:
    state = dict(_make_snapshot().to_dict())
    state["version"] = 99
    with pytest.raises(VersionError) as exc_info:
        BatterySnapshot.from_dict(state)
    assert exc_info.value.subsystem == "battery"
    assert "99" in str(exc_info.value)


def test_from_dict_non_mapping_config_rejected() -> None:
    state = dict(_make_snapshot().to_dict())
    state["config"] = ["not", "a", "mapping"]
    with pytest.raises(WrongTypeError) as exc_info:
        BatterySnapshot.from_dict(state)
    assert exc_info.value.subsystem == "battery"
    assert "config" in str(exc_info.value)


def test_from_dict_non_decimal_soc_kwh_rejected() -> None:
    state = dict(_make_snapshot().to_dict())
    state["soc_kwh"] = 500  # int statt Decimal
    with pytest.raises(WrongTypeError) as exc_info:
        BatterySnapshot.from_dict(state)
    assert exc_info.value.subsystem == "battery"
    assert "soc_kwh" in str(exc_info.value)


# ---------------------------------------------------------------------------
# M8-Welle-4a (ADR 0065): opt-in Thermo-Block + temperature_celsius
# ---------------------------------------------------------------------------


def _make_thermal_snapshot() -> BatterySnapshot:
    base = _make_snapshot()
    thermal_config = BatteryConfig(
        capacity_kwh=base.config.capacity_kwh,
        initial_soc_pct=base.config.initial_soc_pct,
        min_soc_pct=base.config.min_soc_pct,
        max_soc_pct=base.config.max_soc_pct,
        max_charge_kw=base.config.max_charge_kw,
        max_discharge_kw=base.config.max_discharge_kw,
        charge_efficiency=base.config.charge_efficiency,
        discharge_efficiency=base.config.discharge_efficiency,
        ramp_kw_per_s=base.config.ramp_kw_per_s,
        thermal=ThermalConfig(
            ambient_temp_c=Decimal("20"),
            thermal_rise_c_at_full_load=Decimal("40"),
            thermal_time_constant_s=Decimal("600"),
        ),
    )
    return BatterySnapshot(
        version=SNAPSHOT_VERSION,
        device_id="battery-1",
        run_id="run-42",
        sequence=0,
        config=thermal_config,
        soc_kwh=Decimal("500"),
        current_power_kw=Decimal("0"),
        pending_power_kw=Decimal("0"),
        temperature_celsius=Decimal("23.5"),
    )


def test_inactive_snapshot_omits_thermal_keys() -> None:
    """Ohne Thermo-Block: weder `config.thermal` noch Top-Level
    `temperature_celsius` werden serialisiert (opt-in, kein Versions-Bump)."""
    state = _make_snapshot().to_dict()
    assert "temperature_celsius" not in state
    assert "thermal" not in state["config"]  # type: ignore[operator]


def test_thermal_snapshot_roundtrip_byte_stable() -> None:
    """Opt-in Thermo-Block + State roundtrippen byte-stabil."""
    snapshot = _make_thermal_snapshot()
    state = snapshot.to_dict()
    assert state["temperature_celsius"] == Decimal("23.5")
    assert "thermal" in state["config"]  # type: ignore[operator]
    assert BatterySnapshot.from_dict(state) == snapshot


def test_from_dict_v1_without_thermal_reads_as_inactive() -> None:
    """Backward-compat (ADR 0065 §2.5): ein Snapshot ohne
    `temperature_celsius`/`thermal` liest als „kein Thermomodell"."""
    restored = BatterySnapshot.from_dict(_make_snapshot().to_dict())
    assert restored.temperature_celsius is None
    assert restored.config.thermal is None


def test_from_dict_missing_thermal_sub_key_rejected() -> None:
    state = dict(_make_thermal_snapshot().to_dict())
    config = dict(state["config"])  # type: ignore[arg-type]
    thermal = dict(config["thermal"])  # type: ignore[arg-type]
    del thermal["thermal_time_constant_s"]
    config["thermal"] = thermal
    state["config"] = config
    with pytest.raises(MissingKeysError) as exc_info:
        BatterySnapshot.from_dict(state)
    assert exc_info.value.subsystem == "battery"
    assert "thermal_time_constant_s" in str(exc_info.value)


def test_from_dict_non_mapping_thermal_rejected() -> None:
    state = dict(_make_thermal_snapshot().to_dict())
    config = dict(state["config"])  # type: ignore[arg-type]
    config["thermal"] = ["not", "a", "mapping"]
    state["config"] = config
    with pytest.raises(WrongTypeError) as exc_info:
        BatterySnapshot.from_dict(state)
    assert exc_info.value.subsystem == "battery"
    assert "thermal" in str(exc_info.value)


def test_from_dict_invalid_thermal_value_rejected() -> None:
    """Negativer `thermal_time_constant_s` verletzt die ThermalConfig-
    Invariante -> via from_dict zu `WrongTypeError` ueberfuehrt
    (ADR 0014 §2.2 M-5-Pattern)."""
    state = dict(_make_thermal_snapshot().to_dict())
    config = dict(state["config"])  # type: ignore[arg-type]
    thermal = dict(config["thermal"])  # type: ignore[arg-type]
    thermal["thermal_time_constant_s"] = Decimal("-1")
    config["thermal"] = thermal
    state["config"] = config
    with pytest.raises(WrongTypeError) as exc_info:
        BatterySnapshot.from_dict(state)
    assert exc_info.value.subsystem == "battery"
    assert "config" in str(exc_info.value)


# ---------------------------------------------------------------------------
# M8-Welle-4b (ADR 0066): opt-in cell-Block + cell_voltages_v
# ---------------------------------------------------------------------------


def _make_cell_snapshot() -> BatterySnapshot:
    base = _make_snapshot()
    cell_config = BatteryConfig(
        capacity_kwh=base.config.capacity_kwh,
        initial_soc_pct=base.config.initial_soc_pct,
        min_soc_pct=base.config.min_soc_pct,
        max_soc_pct=base.config.max_soc_pct,
        max_charge_kw=base.config.max_charge_kw,
        max_discharge_kw=base.config.max_discharge_kw,
        charge_efficiency=base.config.charge_efficiency,
        discharge_efficiency=base.config.discharge_efficiency,
        ramp_kw_per_s=base.config.ramp_kw_per_s,
        cell=CellConfig(
            nominal_pack_voltage_v=Decimal("400"),
            n_cells=4,
            noise_amplitude_v=Decimal("0.5"),
        ),
    )
    return BatterySnapshot(
        version=SNAPSHOT_VERSION,
        device_id="battery-1",
        run_id="run-42",
        sequence=0,
        config=cell_config,
        soc_kwh=Decimal("500"),
        current_power_kw=Decimal("0"),
        pending_power_kw=Decimal("0"),
        cell_voltages_v=(Decimal("100.1"), Decimal("99.9"), Decimal("100.0"), Decimal("100.2")),
    )


def test_cell_snapshot_roundtrip_byte_stable() -> None:
    snapshot = _make_cell_snapshot()
    state = snapshot.to_dict()
    assert state["cell_voltages_v"] == [
        Decimal("100.1"),
        Decimal("99.9"),
        Decimal("100.0"),
        Decimal("100.2"),
    ]
    assert "cell" in state["config"]  # type: ignore[operator]
    assert state["config"]["cell"]["n_cells"] == 4  # type: ignore[index]
    assert BatterySnapshot.from_dict(state) == snapshot


def test_inactive_snapshot_omits_cell_keys() -> None:
    state = _make_snapshot().to_dict()
    assert "cell_voltages_v" not in state
    assert "cell" not in state["config"]  # type: ignore[operator]


def test_from_dict_missing_cell_sub_key_rejected() -> None:
    state = dict(_make_cell_snapshot().to_dict())
    config = dict(state["config"])  # type: ignore[arg-type]
    cell = dict(config["cell"])  # type: ignore[arg-type]
    del cell["n_cells"]
    config["cell"] = cell
    state["config"] = config
    with pytest.raises(MissingKeysError) as exc_info:
        BatterySnapshot.from_dict(state)
    assert "n_cells" in str(exc_info.value)


def test_from_dict_cell_n_cells_wrong_type_rejected() -> None:
    state = dict(_make_cell_snapshot().to_dict())
    config = dict(state["config"])  # type: ignore[arg-type]
    cell = dict(config["cell"])  # type: ignore[arg-type]
    cell["n_cells"] = "4"  # str statt int
    config["cell"] = cell
    state["config"] = config
    with pytest.raises(WrongTypeError) as exc_info:
        BatterySnapshot.from_dict(state)
    assert "n_cells" in str(exc_info.value)


def test_from_dict_non_list_cell_voltages_rejected() -> None:
    state = dict(_make_cell_snapshot().to_dict())
    state["cell_voltages_v"] = "not-a-list"
    with pytest.raises(WrongTypeError) as exc_info:
        BatterySnapshot.from_dict(state)
    assert exc_info.value.subsystem == "battery"
    assert "cell_voltages_v" in str(exc_info.value)
