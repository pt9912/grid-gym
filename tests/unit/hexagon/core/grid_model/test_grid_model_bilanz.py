"""Tests fuer `GridModelBilanz` (M2 Welle 5a, ADR 0019,
GG-GRID-001 + GG-GRID-002).

Konsolidiert Config-/Bilanz-/Snapshot-/Determinismus-Tests in
einem Modul (Spiegel zu Welle-4-Devices, aber **ohne**
DeviceModel-Protocol-Adherence-Test — `GridModelBilanz` ist
kein Geraet).

Pinnt:
- GridModelConfig-Invarianten (positive Sollwerte +
  Sensitivitaeten, strikte Clamp-Reihenfolge).
- Imbalance-Formel inkl. GridConnection (ADR 0019 §2.2).
- Frequency/Voltage proportionale Formel + Safety-Clamps.
- Clamp-Counting-Semantik (ADR 0019 §2.5 Round-3-Schaerfung):
  Frequenz + Spannung clampen gleichzeitig = +2; jeder
  Update zaehlt separat (keine Deduplizierung).
- Snapshot-Roundtrip byte-stabil; nested-Mapping fuer config.
- Determinismus-Property ueber >= 100 Updates mit 4 Inputs +
  4-Feld-Output-Spur (frequency, voltage, last_imbalance,
  clamp_count).
- Lastenheft GG-GRID-001 Akzeptanz: Frequenz reagiert auf
  Erzeugung/Last/Speicher (manual GridConnection-Pfad, kein
  Auto-Schluss).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import FrozenInstanceError
from decimal import Decimal
from typing import cast

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from grid_gym.hexagon.core.errors import (
    MissingKeysError,
    VersionError,
    WrongTypeError,
)
from grid_gym.hexagon.core.grid_model import (
    CONFIG_FIELD_NAMES,
    GridModelBilanz,
    GridModelConfig,
    GridModelConfigInvalidValueError,
    GridModelSnapshot,
    MODEL_KIND_SIMPLIFIED_PROPORTIONAL,
    SNAPSHOT_VERSION,
)


def _config(
    *,
    nominal_frequency_hz: Decimal = Decimal("50"),
    frequency_sensitivity_hz_per_kw: Decimal = Decimal("0.001"),
    frequency_clamp_min_hz: Decimal = Decimal("45"),
    frequency_clamp_max_hz: Decimal = Decimal("55"),
    nominal_voltage_v: Decimal = Decimal("400"),
    voltage_sensitivity_v_per_kw: Decimal = Decimal("0.1"),
    voltage_clamp_min_v: Decimal = Decimal("280"),
    voltage_clamp_max_v: Decimal = Decimal("520"),
) -> GridModelConfig:
    return GridModelConfig(
        nominal_frequency_hz=nominal_frequency_hz,
        frequency_sensitivity_hz_per_kw=frequency_sensitivity_hz_per_kw,
        frequency_clamp_min_hz=frequency_clamp_min_hz,
        frequency_clamp_max_hz=frequency_clamp_max_hz,
        nominal_voltage_v=nominal_voltage_v,
        voltage_sensitivity_v_per_kw=voltage_sensitivity_v_per_kw,
        voltage_clamp_min_v=voltage_clamp_min_v,
        voltage_clamp_max_v=voltage_clamp_max_v,
    )


# ---------------------------------------------------------------------------
# GridModelConfig — Invarianten (ADR 0019 §2.4a)
# ---------------------------------------------------------------------------


def test_valid_config_constructs() -> None:
    config = _config()
    assert config.nominal_frequency_hz == Decimal("50")
    assert config.nominal_voltage_v == Decimal("400")


def test_config_is_frozen() -> None:
    config = _config()
    with pytest.raises(FrozenInstanceError):
        config.nominal_frequency_hz = Decimal("60")  # type: ignore[misc]


def test_zero_nominal_frequency_rejected() -> None:
    with pytest.raises(GridModelConfigInvalidValueError) as exc_info:
        _config(nominal_frequency_hz=Decimal("0"))
    assert "nominal_frequency_hz" in str(exc_info.value)


def test_zero_nominal_voltage_rejected() -> None:
    with pytest.raises(GridModelConfigInvalidValueError):
        _config(nominal_voltage_v=Decimal("0"))


def test_negative_frequency_sensitivity_rejected() -> None:
    """Sign-Konvention: positiver Imbalance -> Frequenz steigt.
    Negative Sensitivitaet wuerde die Semantik invertieren."""
    with pytest.raises(GridModelConfigInvalidValueError) as exc_info:
        _config(frequency_sensitivity_hz_per_kw=Decimal("-0.001"))
    assert "frequency_sensitivity_hz_per_kw" in str(exc_info.value)


def test_zero_voltage_sensitivity_rejected() -> None:
    with pytest.raises(GridModelConfigInvalidValueError):
        _config(voltage_sensitivity_v_per_kw=Decimal("0"))


def test_clamp_min_equal_nominal_rejected() -> None:
    """Strikte Reihenfolge: clamp_min < nominal < clamp_max
    (Equal-Form ausgeschlossen, damit Equilibrium nicht-
    clampend ist)."""
    with pytest.raises(GridModelConfigInvalidValueError):
        _config(frequency_clamp_min_hz=Decimal("50"))


def test_clamp_max_equal_nominal_rejected() -> None:
    with pytest.raises(GridModelConfigInvalidValueError):
        _config(frequency_clamp_max_hz=Decimal("50"))


def test_clamp_inverted_rejected() -> None:
    """clamp_min > clamp_max ist invertiert."""
    with pytest.raises(GridModelConfigInvalidValueError):
        _config(
            frequency_clamp_min_hz=Decimal("55"),
            frequency_clamp_max_hz=Decimal("45"),
        )


def test_voltage_clamp_min_above_nominal_rejected() -> None:
    with pytest.raises(GridModelConfigInvalidValueError):
        _config(voltage_clamp_min_v=Decimal("450"))


def test_float_value_rejected() -> None:
    """Welle-5a-Review M-4: GG-DATA-005 no-float — direkter
    Konstruktor-Pfad muss float ablehnen, nicht nur Wertebereich."""
    with pytest.raises(GridModelConfigInvalidValueError) as exc_info:
        _config(nominal_frequency_hz=50.0)  # type: ignore[arg-type]
    assert "Decimal" in str(exc_info.value)


# ---------------------------------------------------------------------------
# GridModelBilanz — Initialer Zustand (ADR 0019 §2.6)
# ---------------------------------------------------------------------------


def test_initial_state_is_equilibrium() -> None:
    bilanz = GridModelBilanz(config=_config())
    assert bilanz.frequency_hz == Decimal("50")
    assert bilanz.voltage_v == Decimal("400")
    assert bilanz.last_imbalance_kw == Decimal("0")
    assert bilanz.clamp_event_count == 0
    assert bilanz.model_kind == MODEL_KIND_SIMPLIFIED_PROPORTIONAL


def test_is_not_device_model_protocol() -> None:
    """ADR 0019 §1: GridModelBilanz ist KEIN DeviceModel
    (Single-Instance-System-Modell, kein Geraet)."""
    from grid_gym.hexagon.core.devices import DeviceModel

    bilanz = GridModelBilanz(config=_config())
    assert not isinstance(bilanz, DeviceModel)


# ---------------------------------------------------------------------------
# Imbalance-Formel (ADR 0019 §2.2)
# ---------------------------------------------------------------------------


def test_balanced_inputs_keep_nominal() -> None:
    """pv=2, load=1, battery=1 (laden), grid=0 -> balanced
    (2 - 1 - 1 + 0 = 0)."""
    bilanz = GridModelBilanz(config=_config())
    bilanz.update(
        generation_kw=Decimal("2"),
        load_kw=Decimal("1"),
        storage_kw=Decimal("1"),
        grid_connection_kw=Decimal("0"),
    )
    assert bilanz.last_imbalance_kw == Decimal("0")
    assert bilanz.frequency_hz == Decimal("50")
    assert bilanz.voltage_v == Decimal("400")
    assert bilanz.clamp_event_count == 0


def test_excess_generation_raises_frequency() -> None:
    """Pre-Grid-Restbilanz +1.5 kW, grid=0 → imbalance=+1.5,
    f = 50 + 0.001*1.5 = 50.0015 Hz."""
    bilanz = GridModelBilanz(config=_config())
    bilanz.update(
        generation_kw=Decimal("3"),
        load_kw=Decimal("1"),
        storage_kw=Decimal("0.5"),
        grid_connection_kw=Decimal("0"),
    )
    assert bilanz.last_imbalance_kw == Decimal("1.5")
    assert bilanz.frequency_hz == Decimal("50.0015")
    assert bilanz.voltage_v == Decimal("400.15")


def test_excess_load_lowers_frequency() -> None:
    """pv=1, load=3, battery=0, grid=0 → imbalance=-2, f drops."""
    bilanz = GridModelBilanz(config=_config())
    bilanz.update(
        generation_kw=Decimal("1"),
        load_kw=Decimal("3"),
        storage_kw=Decimal("0"),
        grid_connection_kw=Decimal("0"),
    )
    assert bilanz.last_imbalance_kw == Decimal("-2")
    assert bilanz.frequency_hz == Decimal("49.998")
    assert bilanz.voltage_v == Decimal("399.8")


def test_grid_connection_auto_schluss_keeps_equilibrium() -> None:
    """ADR 0019 §3: Welle-6-Auto-Schluss-Beispiel —
    grid_connection := -(pv - load - battery) → imbalance = 0."""
    pre_grid_residual = Decimal("3") - Decimal("1") - Decimal("0.5")  # = 1.5
    bilanz = GridModelBilanz(config=_config())
    bilanz.update(
        generation_kw=Decimal("3"),
        load_kw=Decimal("1"),
        storage_kw=Decimal("0.5"),
        grid_connection_kw=-pre_grid_residual,  # Auto-Schluss
    )
    assert bilanz.last_imbalance_kw == Decimal("0")
    assert bilanz.frequency_hz == Decimal("50")


def test_grid_connection_partial_close_partial_deviation() -> None:
    """Manueller GridConnection unter dem Pre-Grid-Residual ->
    partielle Frequenzabweichung."""
    bilanz = GridModelBilanz(config=_config())
    bilanz.update(
        generation_kw=Decimal("3"),
        load_kw=Decimal("1"),
        storage_kw=Decimal("0"),  # pre_grid_residual = 2
        grid_connection_kw=Decimal("-1"),  # nur halber Schluss
    )
    assert bilanz.last_imbalance_kw == Decimal("1")
    assert bilanz.frequency_hz == Decimal("50.001")


# ---------------------------------------------------------------------------
# Safety-Clamps + Clamp-Counting-Semantik (ADR 0019 §2.3 / §2.5)
# ---------------------------------------------------------------------------


def test_extreme_imbalance_clamps_frequency() -> None:
    """imbalance=+10_000 kW → f = 50 + 10 = 60 → clamped auf 55."""
    bilanz = GridModelBilanz(config=_config())
    bilanz.update(
        generation_kw=Decimal("10000"),
        load_kw=Decimal("0"),
        storage_kw=Decimal("0"),
        grid_connection_kw=Decimal("0"),
    )
    assert bilanz.frequency_hz == Decimal("55")
    assert bilanz.clamp_event_count >= 1


def test_extreme_negative_imbalance_clamps_frequency() -> None:
    bilanz = GridModelBilanz(config=_config())
    bilanz.update(
        generation_kw=Decimal("0"),
        load_kw=Decimal("10000"),
        storage_kw=Decimal("0"),
        grid_connection_kw=Decimal("0"),
    )
    assert bilanz.frequency_hz == Decimal("45")
    assert bilanz.clamp_event_count >= 1


def test_simultaneous_freq_and_voltage_clamp_count_two() -> None:
    """ADR 0019 §2.5 Round-3-Medium-2: beide Clamps gleichzeitig
    -> count += 2."""
    bilanz = GridModelBilanz(config=_config())
    bilanz.update(
        generation_kw=Decimal("100000"),
        load_kw=Decimal("0"),
        storage_kw=Decimal("0"),
        grid_connection_kw=Decimal("0"),
    )
    assert bilanz.clamp_event_count == 2
    assert bilanz.frequency_hz == Decimal("55")
    assert bilanz.voltage_v == Decimal("520")


def test_repeated_clamping_increments_count_each_tick() -> None:
    """ADR 0019 §2.5 Round-3-Medium-2: keine Deduplizierung —
    100 identische clampende Inputs liefern count == 200
    (beide Clamps schnappen, 2 pro Tick)."""
    bilanz = GridModelBilanz(config=_config())
    for _ in range(100):
        bilanz.update(
            generation_kw=Decimal("100000"),
            load_kw=Decimal("0"),
            storage_kw=Decimal("0"),
            grid_connection_kw=Decimal("0"),
        )
    assert bilanz.clamp_event_count == 200


def test_no_clamp_no_count_increment() -> None:
    bilanz = GridModelBilanz(config=_config())
    for _ in range(50):
        bilanz.update(
            generation_kw=Decimal("100"),
            load_kw=Decimal("100"),
            storage_kw=Decimal("0"),
            grid_connection_kw=Decimal("0"),
        )
    assert bilanz.clamp_event_count == 0


# ---------------------------------------------------------------------------
# Snapshot-Roundtrip (ADR 0019 §2.5)
# ---------------------------------------------------------------------------


def test_snapshot_first_field_is_version() -> None:
    bilanz = GridModelBilanz(config=_config())
    state = bilanz.snapshot()
    assert next(iter(state)) == "version"
    assert state["version"] == SNAPSHOT_VERSION


def test_snapshot_carries_required_fields() -> None:
    bilanz = GridModelBilanz(config=_config())
    state = bilanz.snapshot()
    for key in (
        "version",
        "config",
        "model_kind",
        "current_frequency_hz",
        "current_voltage_v",
        "last_imbalance_kw",
        "clamp_event_count",
    ):
        assert key in state


def test_snapshot_config_is_nested_dict_not_dataclass() -> None:
    """ADR 0019 §2.5: config wird als nested dict serialisiert
    (SnapshotEnvelope akzeptiert keine Dataclass-Objekte)."""
    bilanz = GridModelBilanz(config=_config())
    state = bilanz.snapshot()
    config_state = state["config"]
    assert isinstance(config_state, dict)
    assert not hasattr(config_state, "__dataclass_fields__")
    # Alle 8 expliziten Config-Keys vorhanden:
    config_mapping = cast(Mapping[str, object], config_state)
    for key in (
        "nominal_frequency_hz",
        "frequency_sensitivity_hz_per_kw",
        "frequency_clamp_min_hz",
        "frequency_clamp_max_hz",
        "nominal_voltage_v",
        "voltage_sensitivity_v_per_kw",
        "voltage_clamp_min_v",
        "voltage_clamp_max_v",
    ):
        assert key in config_mapping


def test_from_snapshot_byte_stable_roundtrip() -> None:
    bilanz = GridModelBilanz(config=_config())
    bilanz.update(
        generation_kw=Decimal("3"),
        load_kw=Decimal("1"),
        storage_kw=Decimal("0.5"),
        grid_connection_kw=Decimal("-1"),
    )
    state = bilanz.snapshot()
    restored = GridModelBilanz.from_snapshot(state)
    assert restored == bilanz


def test_from_snapshot_preserves_clamp_count() -> None:
    bilanz = GridModelBilanz(config=_config())
    bilanz.update(
        generation_kw=Decimal("100000"),
        load_kw=Decimal("0"),
        storage_kw=Decimal("0"),
        grid_connection_kw=Decimal("0"),
    )
    assert bilanz.clamp_event_count == 2
    state = bilanz.snapshot()
    restored = GridModelBilanz.from_snapshot(state)
    assert restored.clamp_event_count == 2


def test_from_dict_missing_top_level_key() -> None:
    bilanz = GridModelBilanz(config=_config())
    state = dict(bilanz.snapshot())
    del state["last_imbalance_kw"]
    with pytest.raises(MissingKeysError) as exc_info:
        GridModelSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "grid_model"


def test_from_dict_unsupported_version_raises() -> None:
    bilanz = GridModelBilanz(config=_config())
    state = dict(bilanz.snapshot())
    state["version"] = 99
    with pytest.raises(VersionError):
        GridModelSnapshot.from_dict(state)


def test_from_dict_wrong_version_type_rejected() -> None:
    bilanz = GridModelBilanz(config=_config())
    state = dict(bilanz.snapshot())
    state["version"] = "1"
    with pytest.raises(WrongTypeError):
        GridModelSnapshot.from_dict(state)


def test_from_dict_invalid_config_reraises_as_wrong_type() -> None:
    """ADR 0019 §2.4a-Schaerfung: Config-Verletzung -> WrongTypeError."""
    bilanz = GridModelBilanz(config=_config())
    state = dict(bilanz.snapshot())
    bad_config = dict(cast(Mapping[str, object], state["config"]))
    bad_config["nominal_frequency_hz"] = Decimal("-1")
    state["config"] = bad_config
    with pytest.raises(WrongTypeError) as exc_info:
        GridModelSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "grid_model"


# ---------------------------------------------------------------------------
# Determinismus (ADR 0019 §2.7)
# ---------------------------------------------------------------------------


def _run_bilanz(
    inputs: tuple[tuple[Decimal, Decimal, Decimal, Decimal], ...],
) -> tuple[tuple[Decimal, Decimal, Decimal, int], ...]:
    """Faehrt die Bilanz ueber eine Sequenz von 4-Tupel-Inputs
    und sammelt die 4-Feld-Output-Spur."""
    bilanz = GridModelBilanz(config=_config())
    trace: list[tuple[Decimal, Decimal, Decimal, int]] = []
    for gen, load, storage, grid in inputs:
        bilanz.update(
            generation_kw=gen,
            load_kw=load,
            storage_kw=storage,
            grid_connection_kw=grid,
        )
        trace.append(
            (
                bilanz.frequency_hz,
                bilanz.voltage_v,
                bilanz.last_imbalance_kw,
                bilanz.clamp_event_count,
            )
        )
    return tuple(trace)


@given(
    inputs=st.lists(
        st.tuples(
            st.decimals(min_value=-10, max_value=10, places=2),
            st.decimals(min_value=0, max_value=10, places=2),
            st.decimals(min_value=-5, max_value=5, places=2),
            st.decimals(min_value=-10, max_value=10, places=2),
        ),
        min_size=10,
        max_size=20,
    )
)
@settings(deadline=None, max_examples=15)
def test_same_inputs_produce_byte_identical_trace(
    inputs: list[tuple[Decimal, Decimal, Decimal, Decimal]],
) -> None:
    """ADR 0019 §2.7: gleiche 4-Input-Sequenz -> byte-identische
    4-Feld-Output-Spur."""
    normalized = tuple(inputs)
    trace_a = _run_bilanz(normalized)
    trace_b = _run_bilanz(normalized)
    assert trace_a == trace_b


def test_100_tick_property_deterministic() -> None:
    """ADR 0019 §2.7: >= 100 Updates byte-identisch."""
    inputs = tuple((Decimal(i % 5), Decimal(i % 3), Decimal("0"), Decimal("0")) for i in range(100))
    trace_a = _run_bilanz(inputs)
    trace_b = _run_bilanz(inputs)
    assert trace_a == trace_b
    assert len(trace_a) == 100


@given(seed_kw=st.integers(min_value=0, max_value=1000))
@settings(deadline=None, max_examples=10)
def test_clamp_count_monotone_property(seed_kw: int) -> None:
    """ADR 0019 §2.5 Monotonie-Invariante."""
    bilanz = GridModelBilanz(config=_config())
    last = 0
    for _ in range(20):
        bilanz.update(
            generation_kw=Decimal(seed_kw),
            load_kw=Decimal("0"),
            storage_kw=Decimal("0"),
            grid_connection_kw=Decimal("0"),
        )
        current = bilanz.clamp_event_count
        assert current >= last
        last = current
