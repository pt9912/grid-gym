"""Unit-Tests fuer die private `_runs_router.py`-Helper rund um den
M5-Welle-6b `GET /runs/{run_id}/devices`-Endpunkt (Slice-Doc
Decision 21).

Pinnt:

- `_aggregate_quality`: Pre-First-Tick-Fall (leere Telemetrie →
  `VALID`), Single-FAULT_INJECTED-Point → `FAULT_INJECTED`,
  worst-case-Ordnung (`MISSING > NAN > INVALID > FAULT_INJECTED
  > VALID`), gemischte Sequenz nimmt das schlechteste.
- `_extract_state_subset`: per Device-Typ die in Decision 21 §3.1
  fixierten Felder + Decimal-→-String-Serialisierung + bool-Flag-
  Defaults.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from grid_gym.adapters.driving.http_api._runs_router import (
    _aggregate_quality,
    _extract_state_subset,
)
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint


@dataclass
class _FakeDevice:
    """Minimal-Stub fuer die Helper-Tests. `_runs_router.py`-Helper
    konsumieren nur `.snapshot()` und `.telemetry()` — kein
    vollstaendiges `DeviceModel`-Protocol noetig."""

    snapshot_data: Mapping[str, object]
    telemetry_points: tuple[TelemetryPoint, ...] = ()

    def snapshot(self) -> Mapping[str, object]:
        return self.snapshot_data

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return self.telemetry_points


def _make_point(quality: Quality) -> TelemetryPoint:
    """Pflicht-Felder fuer einen `TelemetryPoint`; die Werte sind
    irrelevant — die Helper-Tests lesen nur `.quality`."""
    return TelemetryPoint(
        run_id="run-1",
        tick=0,
        simulation_time=0,
        device_id="dev-1",
        metric="power_kw",
        value=Decimal("0.000"),
        unit="kW",
        quality=quality,
        source="battery",
        sequence=0,
    )


# ---------------------------------------------------------------------------
# _aggregate_quality
# ---------------------------------------------------------------------------


def test_aggregate_quality_returns_valid_for_empty_telemetry() -> None:
    """Decision 21 Pre-First-Tick-Fall: leere Telemetrie → VALID."""
    device = _FakeDevice(snapshot_data={"version": 1}, telemetry_points=())
    assert _aggregate_quality(device) == Quality.VALID


def test_aggregate_quality_returns_valid_when_all_points_are_valid() -> None:
    device = _FakeDevice(
        snapshot_data={"version": 1},
        telemetry_points=(
            _make_point(Quality.VALID),
            _make_point(Quality.VALID),
        ),
    )
    assert _aggregate_quality(device) == Quality.VALID


def test_aggregate_quality_returns_fault_injected_for_single_fault_point() -> None:
    """Decision 21: ein FAULT_INJECTED-Point propagiert auf die
    device-level Quality."""
    device = _FakeDevice(
        snapshot_data={"version": 1},
        telemetry_points=(
            _make_point(Quality.VALID),
            _make_point(Quality.FAULT_INJECTED),
            _make_point(Quality.VALID),
        ),
    )
    assert _aggregate_quality(device) == Quality.FAULT_INJECTED


def test_aggregate_quality_returns_worst_in_canonical_order() -> None:
    """Decision 21 worst-case-Ordnung
    (`MISSING > NAN > INVALID > FAULT_INJECTED > VALID`):
    eine MISSING-Telemetry gewinnt gegen alle anderen."""
    device = _FakeDevice(
        snapshot_data={"version": 1},
        telemetry_points=(
            _make_point(Quality.FAULT_INJECTED),
            _make_point(Quality.MISSING),
            _make_point(Quality.NAN),
            _make_point(Quality.INVALID),
        ),
    )
    assert _aggregate_quality(device) == Quality.MISSING


def test_aggregate_quality_nan_beats_invalid_and_fault_injected() -> None:
    """Decision 21: NAN ist schlechter als INVALID + FAULT_INJECTED."""
    device = _FakeDevice(
        snapshot_data={"version": 1},
        telemetry_points=(
            _make_point(Quality.INVALID),
            _make_point(Quality.NAN),
            _make_point(Quality.FAULT_INJECTED),
        ),
    )
    assert _aggregate_quality(device) == Quality.NAN


def test_aggregate_quality_invalid_beats_fault_injected() -> None:
    """Decision 21: INVALID ist schlechter als FAULT_INJECTED."""
    device = _FakeDevice(
        snapshot_data={"version": 1},
        telemetry_points=(
            _make_point(Quality.FAULT_INJECTED),
            _make_point(Quality.INVALID),
        ),
    )
    assert _aggregate_quality(device) == Quality.INVALID


# ---------------------------------------------------------------------------
# _extract_state_subset
# ---------------------------------------------------------------------------


def test_extract_state_subset_battery_picks_required_fields() -> None:
    """Decision 21 §3.1: Battery → `soc_kwh`, `current_power_kw`,
    `cell_failure_active`. Decimal-Werte als Strings; Bool bleibt
    Bool. Andere Snapshot-Felder werden gedroppt."""
    snap = {
        "version": 1,
        "device_id": "battery-1",
        "run_id": "run-1",
        "sequence": 0,
        "config": {"capacity_kwh": Decimal("100.000")},
        "soc_kwh": Decimal("50.000"),
        "current_power_kw": Decimal("12.500"),
        "pending_power_kw": Decimal("12.500"),
        "fault_state": {"cell_failure_active": True},
    }
    device = _FakeDevice(snapshot_data=snap)
    state = _extract_state_subset(device, "battery")
    assert state == {
        "soc_kwh": "50.000",
        "current_power_kw": "12.500",
        "cell_failure_active": True,
    }


def test_extract_state_subset_battery_defaults_fault_flag_when_missing() -> None:
    """ADR 0025 §2.2 Backward-Compat: Welle-1-Snapshots ohne
    `fault_state` defaulten den Flag auf `False`."""
    snap = {
        "version": 1,
        "soc_kwh": Decimal("0.000"),
        "current_power_kw": Decimal("0.000"),
    }
    device = _FakeDevice(snapshot_data=snap)
    state = _extract_state_subset(device, "battery")
    assert state is not None
    assert state["cell_failure_active"] is False


def test_extract_state_subset_battery_pre_init_returns_none() -> None:
    """Welle-6b-Review F2: pre-init device snapshots (nur
    `{"version": N}`) liefern None — Endpoint silent-droppt sie."""
    snap = {"version": 1}
    device = _FakeDevice(snapshot_data=snap)
    assert _extract_state_subset(device, "battery") is None
    assert _extract_state_subset(device, "pv") is None
    assert _extract_state_subset(device, "load") is None
    assert _extract_state_subset(device, "grid_connection") is None


def test_extract_state_subset_battery_fault_flag_coerces_int_to_true() -> None:
    """Welle-6b-Review F3: truthy-coerce statt strict-isinstance.
    Ein als int(1) round-tripped Fault-Flag muss als True erscheinen,
    nicht silent als False (safety-critical signal)."""
    snap = {
        "version": 1,
        "soc_kwh": Decimal("0.000"),
        "current_power_kw": Decimal("0.000"),
        "fault_state": {"cell_failure_active": 1},
    }
    device = _FakeDevice(snapshot_data=snap)
    state = _extract_state_subset(device, "battery")
    assert state is not None
    assert state["cell_failure_active"] is True


def test_extract_state_subset_battery_fault_flag_zero_is_false() -> None:
    """Welle-6b-Review F3-Symmetrie: int(0) → False (truthy-coerce)."""
    snap = {
        "version": 1,
        "soc_kwh": Decimal("0.000"),
        "current_power_kw": Decimal("0.000"),
        "fault_state": {"cell_failure_active": 0},
    }
    device = _FakeDevice(snapshot_data=snap)
    state = _extract_state_subset(device, "battery")
    assert state is not None
    assert state["cell_failure_active"] is False


def test_extract_state_subset_grid_pre_init_returns_none() -> None:
    """Welle-6b-Review F2: grid_connection pre-init returns None."""
    snap = {"version": 1, "current_power_kw": Decimal("0.000")}
    device = _FakeDevice(snapshot_data=snap)
    # current_voltage_v fehlt → None
    assert _extract_state_subset(device, "grid_connection") is None


def test_extract_state_subset_pv_picks_only_current_power_kw() -> None:
    """Decision 21 §3.1: PV → genau `current_power_kw` (Decimal als
    String)."""
    snap = {
        "version": 1,
        "current_power_kw": Decimal("5.250"),
        "pending_power_kw": Decimal("5.250"),
    }
    device = _FakeDevice(snapshot_data=snap)
    state = _extract_state_subset(device, "pv")
    assert state == {"current_power_kw": "5.250"}


def test_extract_state_subset_load_picks_only_current_power_kw() -> None:
    """Decision 21 §3.1: Load → genau `current_power_kw`."""
    snap = {"version": 1, "current_power_kw": Decimal("3.000")}
    device = _FakeDevice(snapshot_data=snap)
    state = _extract_state_subset(device, "load")
    assert state == {"current_power_kw": "3.000"}


def test_extract_state_subset_grid_connection_picks_required_fields() -> None:
    """Decision 21 §3.1: GridConnection → `current_power_kw`,
    `current_voltage_v`, `voltage_drop_active`."""
    snap = {
        "version": 1,
        "current_power_kw": Decimal("-2.500"),
        "current_voltage_v": Decimal("400.000"),
        "fault_state": {"voltage_drop_active": True},
    }
    device = _FakeDevice(snapshot_data=snap)
    state = _extract_state_subset(device, "grid_connection")
    assert state == {
        "current_power_kw": "-2.500",
        "current_voltage_v": "400.000",
        "voltage_drop_active": True,
    }


def test_extract_state_subset_smart_meter_is_empty() -> None:
    """Decision 21 §3.1: SmartMeter hat keinen eigenen State → `{}`."""
    snap = {"version": 1}
    device = _FakeDevice(snapshot_data=snap)
    state = _extract_state_subset(device, "smart_meter")
    assert state == {}


def test_extract_state_subset_unknown_device_type_returns_empty() -> None:
    """Forward-Compat-Defense: unbekannter Typ → leeres Mapping.
    Konsistent zu SmartMeter (kein Power-State)."""
    snap = {"version": 1}
    device = _FakeDevice(snapshot_data=snap)
    state = _extract_state_subset(device, "wind")  # Welle-7+/M3-Drift-Beispiel
    assert state == {}
