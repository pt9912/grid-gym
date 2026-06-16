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
    LoadEvent,
    LoadProfile,
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
    is_islanded: bool = False,
    forming_device_id: str | None = None,
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
        is_islanded=is_islanded,
        forming_device_id=forming_device_id,
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
    """**Lastenheft `GG-GRID-001` Akzeptanz**: Frequenz reagiert
    auf Erzeugung/Last/Speicher im manuellen GridConnection-Pfad
    (kein Auto-Schluss). Pre-Grid-Restbilanz +1.5 kW, grid=0 →
    imbalance=+1.5, f = 50 + 0.001*1.5 = 50.0015 Hz."""
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
    """**Lastenheft `GG-GRID-001` Akzeptanz** (negativer Pfad):
    pv=1, load=3, battery=0, grid=0 → imbalance=-2, f drops.
    Lastenheft §11 GG-GRID-001 verlangt das Frequenz-Verhalten
    aus Erzeugung/Last/Speicher; voltage-Spur testet
    `GG-GRID-002` parallel."""
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
    """**Lastenheft `GG-GRID-001`/`002` Akzeptanz** (Manual-Pfad):
    manueller GridConnection unter dem Pre-Grid-Residual ->
    partielle Frequenzabweichung. Demonstriert ADR 0019 §3
    Manual-Pfad als primaeren Akzeptanz-Pfad gegenueber dem
    Auto-Schluss-Pfad."""
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


_EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {
        "version",
        "config",
        "model_kind",
        "current_frequency_hz",
        "current_voltage_v",
        "last_imbalance_kw",
        "clamp_event_count",
        "active_load_events",
        "active_load_profiles",
    }
)
"""Welle-5a-Review L-3: Test-eigene Single-Source-of-Truth fuer
die Top-Level-Snapshot-Keys (parallel zu `_V2_TOP_KEYS` in
snapshot.py). Welle 5b ergaenzt `active_load_events`
+ `active_load_profiles` (Snapshot v1→v2)."""


def test_snapshot_carries_required_fields() -> None:
    bilanz = GridModelBilanz(config=_config())
    state = bilanz.snapshot()
    for key in _EXPECTED_TOP_LEVEL_KEYS:
        assert key in state, f"missing top-level key: {key}"
    assert set(state.keys()) == _EXPECTED_TOP_LEVEL_KEYS


def test_snapshot_config_is_nested_dict_not_dataclass() -> None:
    """ADR 0019 §2.5: config wird als nested dict serialisiert
    (SnapshotEnvelope akzeptiert keine Dataclass-Objekte).
    Welle-5a-Review L-3: iteriert ueber `CONFIG_FIELD_NAMES` aus
    Snapshot-Modul-Single-Source-of-Truth statt hartkodierter
    Duplikation."""
    bilanz = GridModelBilanz(config=_config())
    state = bilanz.snapshot()
    config_state = state["config"]
    assert isinstance(config_state, dict)
    assert not hasattr(config_state, "__dataclass_fields__")
    config_mapping = cast(Mapping[str, object], config_state)
    for key in CONFIG_FIELD_NAMES:
        assert key in config_mapping, f"missing config key: {key}"
    assert set(config_mapping.keys()) == set(CONFIG_FIELD_NAMES)


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


def test_from_dict_bool_clamp_event_count_rejected() -> None:
    """Welle-5a-Review L-5: `assert_int` schliesst `bool` als
    int-Subclass explizit aus (snapshot_codec.py); Welle 5a hat
    zwei int-Felder (version + clamp_event_count) und beide
    sollen die Pruefung haben."""
    bilanz = GridModelBilanz(config=_config())
    state = dict(bilanz.snapshot())
    state["clamp_event_count"] = True
    with pytest.raises(WrongTypeError):
        GridModelSnapshot.from_dict(state)


def test_from_dict_unknown_model_kind_rejected() -> None:
    """Welle-5a-Review M-1: model_kind muss in Welle 5a auf
    `simplified-proportional` festgenagelt sein; ein
    `power-flow-adapter`-Snapshot darf nicht stillschweigend
    re-instantiiert werden (Lastenheft §11.2-Akzeptanz)."""
    bilanz = GridModelBilanz(config=_config())
    state = dict(bilanz.snapshot())
    state["model_kind"] = "power-flow-adapter"
    with pytest.raises(WrongTypeError) as exc_info:
        GridModelSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "grid_model"


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


# ---------------------------------------------------------------------------
# Welle-5b: Snapshot v1 -> v2 Backward-Compat + LoadEvents/Profiles
# (ADR 0020 §2.5 / §2.6)
# ---------------------------------------------------------------------------


def _sample_event() -> LoadEvent:
    return LoadEvent(
        start_s=Decimal("10"),
        duration_s=Decimal("5"),
        target_device_id="load-1",
        power_kw=Decimal("2.5"),
    )


def _sample_profile() -> LoadProfile:
    return LoadProfile(
        target_device_id="load-2",
        tick_values=(Decimal("1.0"), Decimal("1.5"), Decimal("2.0")),
        tick_ms=1000,
    )


def test_bilanz_default_active_lists_are_empty() -> None:
    """ADR 0019 §2.6 + ADR 0020 §2.5: ohne explizite Argumente
    haelt Bilanz leere LoadEvent/Profile-Tupel."""
    bilanz = GridModelBilanz(config=_config())
    assert bilanz.active_load_events == ()
    assert bilanz.active_load_profiles == ()


def test_bilanz_constructor_accepts_events_and_profiles() -> None:
    bilanz = GridModelBilanz(
        config=_config(),
        active_load_events=(_sample_event(),),
        active_load_profiles=(_sample_profile(),),
    )
    assert bilanz.active_load_events == (_sample_event(),)
    assert bilanz.active_load_profiles == (_sample_profile(),)


def test_snapshot_v2_emits_version_two() -> None:
    """ADR 0020 §2.5: Welle 5b emittiert ausschliesslich v2-
    Snapshots (kein Down-Grade auf v1)."""
    bilanz = GridModelBilanz(config=_config())
    state = bilanz.snapshot()
    assert state["version"] == 2
    assert SNAPSHOT_VERSION == 2


def test_snapshot_v2_serializes_events_as_list_of_mappings() -> None:
    """ADR 0020 §2.5: active_load_events/profiles als Liste von
    Mappings (canonical-kompatibel, keine Dataclass-Objekte)."""
    bilanz = GridModelBilanz(
        config=_config(),
        active_load_events=(_sample_event(),),
        active_load_profiles=(_sample_profile(),),
    )
    state = bilanz.snapshot()
    events = state["active_load_events"]
    assert isinstance(events, list)
    assert len(events) == 1
    event_mapping = events[0]
    assert isinstance(event_mapping, dict)
    assert event_mapping["target_device_id"] == "load-1"

    profiles = state["active_load_profiles"]
    assert isinstance(profiles, list)
    profile_mapping = profiles[0]
    assert isinstance(profile_mapping, dict)
    assert profile_mapping["target_device_id"] == "load-2"
    assert isinstance(profile_mapping["tick_values"], list)


def test_snapshot_v2_byte_stable_across_repeated_emits() -> None:
    """Welle-5b-Review M-6: zwei aufeinanderfolgende `snapshot()`-
    Aufrufe auf demselben Bilanz-Zustand liefern byte-identische
    Mappings. ADR 0020 §2.7 Determinismus-Vertrag fuer v2-
    Snapshots mit befuellten LoadEvent/LoadProfile-Tupeln."""
    bilanz = GridModelBilanz(
        config=_config(),
        active_load_events=(_sample_event(),),
        active_load_profiles=(_sample_profile(),),
    )
    bilanz.update(
        generation_kw=Decimal("3"),
        load_kw=Decimal("1"),
        storage_kw=Decimal("0"),
        grid_connection_kw=Decimal("-1"),
    )
    snap_a = dict(bilanz.snapshot())
    snap_b = dict(bilanz.snapshot())
    assert snap_a == snap_b
    # Auch der Roundtrip muss byte-stabil sein:
    restored = GridModelBilanz.from_snapshot(snap_a)
    assert dict(restored.snapshot()) == snap_a


def test_snapshot_v2_roundtrip_with_events_and_profiles() -> None:
    bilanz = GridModelBilanz(
        config=_config(),
        active_load_events=(_sample_event(),),
        active_load_profiles=(_sample_profile(),),
    )
    bilanz.update(
        generation_kw=Decimal("3"),
        load_kw=Decimal("1"),
        storage_kw=Decimal("0"),
        grid_connection_kw=Decimal("-1"),
    )
    state = bilanz.snapshot()
    restored = GridModelBilanz.from_snapshot(state)
    assert restored == bilanz
    assert restored.active_load_events == (_sample_event(),)
    assert restored.active_load_profiles == (_sample_profile(),)


def test_from_dict_v1_backward_compat_reads_empty_lists() -> None:
    """ADR 0020 §2.6: v1-Snapshots (Welle-5a-Stand, ohne
    LoadEvents/Profiles) bleiben roundtrip-faehig; v1-Read
    liefert leere Tupel."""
    bilanz_v2 = GridModelBilanz(config=_config())
    state_v2 = dict(bilanz_v2.snapshot())

    # v1-Snapshot konstruieren: version=1 + entfernte Welle-5b-Felder.
    state_v1 = {
        k: v for k, v in state_v2.items() if k not in {"active_load_events", "active_load_profiles"}
    }
    state_v1["version"] = 1

    restored = GridModelSnapshot.from_dict(state_v1)
    assert restored.version == 1
    assert restored.active_load_events == ()
    assert restored.active_load_profiles == ()


def test_from_dict_v1_to_v2_write_upgrade() -> None:
    """ADR 0020 §2.6: v1-Read → v2-Write (kein Down-Grade).
    Nach from_dict eines v1-Snapshots emittiert die Bilanz beim
    naechsten snapshot() bereits v2."""
    bilanz_v2 = GridModelBilanz(config=_config())
    state_v2 = dict(bilanz_v2.snapshot())
    state_v1 = {
        k: v for k, v in state_v2.items() if k not in {"active_load_events", "active_load_profiles"}
    }
    state_v1["version"] = 1

    restored = GridModelBilanz.from_snapshot(state_v1)
    new_state = restored.snapshot()
    assert new_state["version"] == 2
    assert new_state["active_load_events"] == []
    assert new_state["active_load_profiles"] == []


def test_from_dict_unsupported_version_three_rejected() -> None:
    """Nur v1 und v2 sind in Welle 5b zugelassen."""
    bilanz = GridModelBilanz(config=_config())
    state = dict(bilanz.snapshot())
    state["version"] = 3
    with pytest.raises(VersionError):
        GridModelSnapshot.from_dict(state)


def test_from_dict_v2_missing_load_events_key_rejected() -> None:
    """ADR 0020 §2.6: v2-Read verlangt active_load_events Pflicht."""
    bilanz = GridModelBilanz(config=_config())
    state = dict(bilanz.snapshot())
    del state["active_load_events"]
    with pytest.raises(MissingKeysError):
        GridModelSnapshot.from_dict(state)


def test_from_dict_v2_non_list_load_events_rejected() -> None:
    bilanz = GridModelBilanz(config=_config())
    state = dict(bilanz.snapshot())
    state["active_load_events"] = "not-a-list"
    with pytest.raises(WrongTypeError):
        GridModelSnapshot.from_dict(state)


def test_from_dict_v2_invalid_load_event_reraises_as_wrong_type() -> None:
    """Welle-5b: LoadEvent-Invariant-Verletzung in Snapshot wird zu
    `WrongTypeError(subsystem='grid_model')` ueberfuehrt (Welle-3-
    Review-L-1 / Welle-4b-Review-M-2-Pattern)."""
    bilanz = GridModelBilanz(
        config=_config(),
        active_load_events=(_sample_event(),),
    )
    state = dict(bilanz.snapshot())
    events_raw = state["active_load_events"]
    assert isinstance(events_raw, list)
    bad_event = dict(events_raw[0])
    bad_event["duration_s"] = Decimal("0")  # Invariant-Verletzung
    state["active_load_events"] = [bad_event]
    with pytest.raises(WrongTypeError) as exc_info:
        GridModelSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "grid_model"


def test_from_dict_v2_invalid_load_profile_reraises_as_wrong_type() -> None:
    bilanz = GridModelBilanz(
        config=_config(),
        active_load_profiles=(_sample_profile(),),
    )
    state = dict(bilanz.snapshot())
    profiles_raw = state["active_load_profiles"]
    assert isinstance(profiles_raw, list)
    bad_profile = dict(profiles_raw[0])
    bad_profile["tick_ms"] = 0  # Invariant-Verletzung
    state["active_load_profiles"] = [bad_profile]
    with pytest.raises(WrongTypeError) as exc_info:
        GridModelSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "grid_model"


# ---------------------------------------------------------------------------
# M8-Welle-3a: Inselnetz-Config-Invarianten (ADR 0060 §2.1)
# ---------------------------------------------------------------------------


def test_island_fields_default_to_connected() -> None:
    """ADR 0060 §2.1: Default netzgekoppelt — is_islanded=False,
    forming_device_id=None (backward-compat)."""
    config = _config()
    assert config.is_islanded is False
    assert config.forming_device_id is None


def test_valid_islanded_config_constructs() -> None:
    config = _config(is_islanded=True, forming_device_id="diesel-1")
    assert config.is_islanded is True
    assert config.forming_device_id == "diesel-1"


def test_islanded_without_forming_device_id_rejected() -> None:
    """ADR 0060 §2.1 Biconditional: Inselnetz ohne Forming-ID ist ein
    Konfigurationsfehler."""
    with pytest.raises(GridModelConfigInvalidValueError) as exc_info:
        _config(is_islanded=True, forming_device_id=None)
    assert "forming_device_id" in str(exc_info.value)


def test_forming_device_id_without_islanded_rejected() -> None:
    """ADR 0060 §2.1 Biconditional (Rueckrichtung): Forming-ID im
    netzgekoppelten Modus ist ein Tippfehler-Indikator."""
    with pytest.raises(GridModelConfigInvalidValueError) as exc_info:
        _config(is_islanded=False, forming_device_id="diesel-1")
    assert "forming_device_id" in str(exc_info.value)


def test_non_bool_is_islanded_rejected() -> None:
    """ADR 0060 §2.1: is_islanded muss bool sein (kein int-Subclass-
    Schmuggel als truthy)."""
    with pytest.raises(GridModelConfigInvalidValueError) as exc_info:
        _config(is_islanded=1, forming_device_id="diesel-1")  # type: ignore[arg-type]
    assert "is_islanded" in str(exc_info.value)


def test_empty_forming_device_id_rejected() -> None:
    """ADR 0060 §2.1: forming_device_id muss non-empty str sein."""
    with pytest.raises(GridModelConfigInvalidValueError) as exc_info:
        _config(is_islanded=True, forming_device_id="")
    assert "forming_device_id" in str(exc_info.value)


# ---------------------------------------------------------------------------
# M8-Welle-3a: Snapshot opt-in + backward-compat (ADR 0060 §2.4)
# ---------------------------------------------------------------------------


def test_connected_snapshot_omits_island_keys() -> None:
    """ADR 0060 §2.4: im netzgekoppelten Default emittiert das
    config-Sub-Mapping KEINE Insel-Keys — byte-identisch zu ADR 0019
    (EXPECTED_DEMO_* unberuehrt, kein Schema-Bump)."""
    bilanz = GridModelBilanz(config=_config())
    config_state = cast(Mapping[str, object], bilanz.snapshot()["config"])
    assert "is_islanded" not in config_state
    assert "forming_device_id" not in config_state
    assert set(config_state.keys()) == set(CONFIG_FIELD_NAMES)


def test_islanded_snapshot_emits_island_keys() -> None:
    """ADR 0060 §2.4: nur im Inselnetz tragen die Snapshot-config-Keys
    is_islanded/forming_device_id; Schema-Version bleibt 2."""
    bilanz = GridModelBilanz(config=_config(is_islanded=True, forming_device_id="diesel-1"))
    state = bilanz.snapshot()
    assert state["version"] == SNAPSHOT_VERSION
    config_state = cast(Mapping[str, object], state["config"])
    assert config_state["is_islanded"] is True
    assert config_state["forming_device_id"] == "diesel-1"


def test_islanded_snapshot_roundtrip() -> None:
    """ADR 0060 §2.4: Inselnetz-Snapshot ist self-sufficient
    roundtrip-faehig."""
    bilanz = GridModelBilanz(config=_config(is_islanded=True, forming_device_id="battery-1"))
    bilanz.update(
        generation_kw=Decimal("0"),
        load_kw=Decimal("10"),
        storage_kw=Decimal("-10"),
        grid_connection_kw=Decimal("0"),
    )
    restored = GridModelBilanz.from_snapshot(bilanz.snapshot())
    assert restored == bilanz
    assert restored.config.is_islanded is True
    assert restored.config.forming_device_id == "battery-1"


def test_from_dict_v2_without_island_keys_reads_connected() -> None:
    """ADR 0060 §2.4 backward-compat: ein v2-Snapshot OHNE Insel-Keys
    (Bestand vor Welle 3a) liest als netzgekoppelt."""
    bilanz = GridModelBilanz(config=_config())
    state = bilanz.snapshot()
    config_state = cast(Mapping[str, object], state["config"])
    assert "is_islanded" not in config_state  # Bestands-Form
    restored = GridModelSnapshot.from_dict(state)
    assert restored.config.is_islanded is False
    assert restored.config.forming_device_id is None


def test_from_dict_islanded_missing_forming_id_reraises_as_wrong_type() -> None:
    """ADR 0060 §2.4: ein korrupter Insel-Snapshot (is_islanded=True ohne
    forming_device_id) wird ueber die Config-Presence-Invariante zu
    WrongTypeError(subsystem='grid_model') ueberfuehrt."""
    bilanz = GridModelBilanz(config=_config(is_islanded=True, forming_device_id="diesel-1"))
    state = dict(bilanz.snapshot())
    bad_config = dict(cast(Mapping[str, object], state["config"]))
    del bad_config["forming_device_id"]  # Presence-Verletzung
    state["config"] = bad_config
    with pytest.raises(WrongTypeError) as exc_info:
        GridModelSnapshot.from_dict(state)
    assert exc_info.value.subsystem == "grid_model"
