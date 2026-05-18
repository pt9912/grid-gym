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

from grid_gym.hexagon.core.devices.battery.config import BatteryConfig
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
