"""Tests fuer `loads.py` (M2 Welle 5b, ADR 0020, GG-GRID-003/004).

Pinnt:
- LoadEvent-Invarianten (Decimal-Type + Wertebereiche +
  nicht-leere target_device_id).
- LoadProfile-Invarianten (Decimal/int-Type + Wertebereiche +
  Sortier-/Eindeutigkeit-Pflicht).
- parse_csv_profile Happy-Path + alle Fehler-Pfade.
- parse_json_profile (String + Mapping) inkl. 5-Punkte-
  Number-Handling-Vertrag (parse_float=Decimal, Decimal(int),
  bool-Ablehnung, tick_ms-int-Pflicht, float-Ablehnung im
  Mapping-Pfad).
- Datei-I/O-frei (kein open()-Call im core).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.grid_model.loads import (
    LoadEvent,
    LoadProfile,
    LoadProfileEmptyError,
    LoadProfileMissingFieldError,
    LoadProfileTypeError,
    parse_csv_profile,
    parse_json_profile,
)


# ---------------------------------------------------------------------------
# LoadEvent (ADR 0020 §2.2)
# ---------------------------------------------------------------------------


def test_load_event_valid_constructs() -> None:
    event = LoadEvent(
        start_s=Decimal("10"),
        duration_s=Decimal("5"),
        target_device_id="load-1",
        power_kw=Decimal("2.5"),
    )
    assert event.start_s == Decimal("10")
    assert event.target_device_id == "load-1"


def test_load_event_zero_start_allowed() -> None:
    """start_s >= 0 (zero ist erlaubt)."""
    event = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("5"),
        target_device_id="load-1",
        power_kw=Decimal("2.5"),
    )
    assert event.start_s == Decimal("0")


def test_load_event_zero_power_allowed() -> None:
    """power_kw >= 0 (zero-Last ist erlaubt, z.B. Abschalt-Event)."""
    event = LoadEvent(
        start_s=Decimal("10"),
        duration_s=Decimal("5"),
        target_device_id="load-1",
        power_kw=Decimal("0"),
    )
    assert event.power_kw == Decimal("0")


def test_load_event_negative_start_rejected() -> None:
    with pytest.raises(LoadProfileTypeError):
        LoadEvent(
            start_s=Decimal("-1"),
            duration_s=Decimal("5"),
            target_device_id="load-1",
            power_kw=Decimal("2"),
        )


def test_load_event_zero_duration_rejected() -> None:
    with pytest.raises(LoadProfileTypeError):
        LoadEvent(
            start_s=Decimal("10"),
            duration_s=Decimal("0"),
            target_device_id="load-1",
            power_kw=Decimal("2"),
        )


def test_load_event_negative_power_rejected() -> None:
    with pytest.raises(LoadProfileTypeError):
        LoadEvent(
            start_s=Decimal("10"),
            duration_s=Decimal("5"),
            target_device_id="load-1",
            power_kw=Decimal("-1"),
        )


def test_load_event_empty_target_id_rejected() -> None:
    with pytest.raises(LoadProfileTypeError):
        LoadEvent(
            start_s=Decimal("10"),
            duration_s=Decimal("5"),
            target_device_id="",
            power_kw=Decimal("2"),
        )


def test_load_event_float_value_rejected() -> None:
    """GG-DATA-005 / Welle-5a-Review-M-4-Spiegel: float in
    Decimal-Feldern wird abgelehnt."""
    with pytest.raises(LoadProfileTypeError):
        LoadEvent(
            start_s=10.0,  # type: ignore[arg-type]
            duration_s=Decimal("5"),
            target_device_id="load-1",
            power_kw=Decimal("2"),
        )


def test_load_event_non_str_target_id_rejected() -> None:
    """Welle-5b-Review M-5: target_device_id-Type-Pflicht."""
    with pytest.raises(LoadProfileTypeError):
        LoadEvent(
            start_s=Decimal("0"),
            duration_s=Decimal("1"),
            target_device_id=42,  # type: ignore[arg-type]
            power_kw=Decimal("1"),
        )


def test_load_event_none_target_id_rejected() -> None:
    with pytest.raises(LoadProfileTypeError):
        LoadEvent(
            start_s=Decimal("0"),
            duration_s=Decimal("1"),
            target_device_id=None,  # type: ignore[arg-type]
            power_kw=Decimal("1"),
        )


# ---------------------------------------------------------------------------
# LoadProfile (ADR 0020 §2.3)
# ---------------------------------------------------------------------------


def test_load_profile_valid_constructs() -> None:
    profile = LoadProfile(
        target_device_id="load-1",
        tick_values=(Decimal("1.5"), Decimal("2.0")),
        tick_ms=1000,
    )
    assert profile.tick_ms == 1000
    assert profile.tick_values == (Decimal("1.5"), Decimal("2.0"))


def test_load_profile_empty_tick_values_rejected() -> None:
    with pytest.raises(LoadProfileEmptyError):
        LoadProfile(
            target_device_id="load-1",
            tick_values=(),
            tick_ms=1000,
        )


def test_load_profile_negative_value_rejected() -> None:
    with pytest.raises(LoadProfileTypeError):
        LoadProfile(
            target_device_id="load-1",
            tick_values=(Decimal("1.5"), Decimal("-0.1")),
            tick_ms=1000,
        )


def test_load_profile_zero_tick_ms_rejected() -> None:
    with pytest.raises(LoadProfileTypeError):
        LoadProfile(
            target_device_id="load-1",
            tick_values=(Decimal("1.5"),),
            tick_ms=0,
        )


def test_load_profile_bool_tick_ms_rejected() -> None:
    """GG-DATA-005 / Welle-5a-Review-L-5-Spiegel: bool ist
    int-Subclass, soll explizit abgelehnt werden."""
    with pytest.raises(LoadProfileTypeError):
        LoadProfile(
            target_device_id="load-1",
            tick_values=(Decimal("1.5"),),
            tick_ms=True,  # type: ignore[arg-type]
        )


def test_load_profile_float_tick_value_rejected() -> None:
    with pytest.raises(LoadProfileTypeError):
        LoadProfile(
            target_device_id="load-1",
            tick_values=(1.5,),  # type: ignore[arg-type]
            tick_ms=1000,
        )


def test_load_profile_empty_target_id_rejected() -> None:
    with pytest.raises(LoadProfileTypeError):
        LoadProfile(
            target_device_id="",
            tick_values=(Decimal("1.5"),),
            tick_ms=1000,
        )


def test_load_profile_list_tick_values_rejected() -> None:
    """ADR 0020 §2.3 verlangt tuple, nicht list."""
    with pytest.raises(LoadProfileTypeError):
        LoadProfile(
            target_device_id="load-1",
            tick_values=[Decimal("1.5")],  # type: ignore[arg-type]
            tick_ms=1000,
        )


def test_load_profile_non_str_target_id_rejected() -> None:
    """Welle-5b-Review M-5: target_device_id-Type-Pflicht (analog
    LoadEvent)."""
    with pytest.raises(LoadProfileTypeError):
        LoadProfile(
            target_device_id=99,  # type: ignore[arg-type]
            tick_values=(Decimal("1"),),
            tick_ms=1000,
        )


# ---------------------------------------------------------------------------
# parse_csv_profile (ADR 0020 §2.4)
# ---------------------------------------------------------------------------


def test_parse_csv_happy_path() -> None:
    text = "target_device_id,tick_ms,tick_values\nload-1,1000,1.5;2.0;1.8;1.2\n"
    profile = parse_csv_profile(text)
    assert profile.target_device_id == "load-1"
    assert profile.tick_ms == 1000
    assert profile.tick_values == (
        Decimal("1.5"),
        Decimal("2.0"),
        Decimal("1.8"),
        Decimal("1.2"),
    )


def test_parse_csv_trims_whitespace() -> None:
    text = "target_device_id,tick_ms,tick_values\n  load-1 , 1000 , 1.5 ; 2.0\n"
    profile = parse_csv_profile(text)
    assert profile.target_device_id == "load-1"
    assert profile.tick_values == (Decimal("1.5"), Decimal("2.0"))


def test_parse_csv_only_header_rejected() -> None:
    text = "target_device_id,tick_ms,tick_values\n"
    with pytest.raises(LoadProfileTypeError):
        parse_csv_profile(text)


def test_parse_csv_wrong_header_rejected() -> None:
    text = "target_device_id,wrong_field,tick_values\nload-1,1000,1.5\n"
    with pytest.raises(LoadProfileMissingFieldError):
        parse_csv_profile(text)


def test_parse_csv_non_int_tick_ms_rejected() -> None:
    text = "target_device_id,tick_ms,tick_values\nload-1,not-a-number,1.5\n"
    with pytest.raises(LoadProfileTypeError):
        parse_csv_profile(text)


def test_parse_csv_invalid_decimal_rejected() -> None:
    text = "target_device_id,tick_ms,tick_values\nload-1,1000,1.5;not-a-decimal;2.0\n"
    with pytest.raises(LoadProfileTypeError):
        parse_csv_profile(text)


def test_parse_csv_empty_tick_values_rejected() -> None:
    text = "target_device_id,tick_ms,tick_values\nload-1,1000,\n"
    with pytest.raises((LoadProfileEmptyError, LoadProfileTypeError)):
        parse_csv_profile(text)


def test_parse_csv_non_str_input_rejected() -> None:
    with pytest.raises(LoadProfileTypeError):
        parse_csv_profile(b"binary")  # type: ignore[arg-type]


def test_parse_csv_comma_in_field_rejected_as_cell_count_mismatch() -> None:
    """Welle-5b-Review L-6: Komma in einem Feldwert (z.B.
    target_device_id='load,with,commas') ist nicht supportet —
    der Cell-Count-Check faengt das mechanisch als
    LoadProfileTypeError ab. Welle 5b nutzt bewusst kein
    stdlib-csv-Modul (ID-Convention erlaubt keine Kommas)."""
    text = "target_device_id,tick_ms,tick_values\nload,with,commas,1000,1.5\n"
    with pytest.raises(LoadProfileTypeError):
        parse_csv_profile(text)


def test_parse_csv_multi_data_row_rejected() -> None:
    """Welle-5b-Review H-1: CSV-Multi-Row darf nicht stillschweigend
    nur die erste Datenzeile nehmen — Welle 5b haelt exakt
    Header + 1 Data-Row. Multi-Row ist Welle-5+/M3."""
    text = "target_device_id,tick_ms,tick_values\nload-1,1000,1.5\nload-2,1000,2.0\n"
    with pytest.raises(LoadProfileTypeError) as exc_info:
        parse_csv_profile(text)
    assert "exactly" in str(exc_info.value).lower() or "1 data row" in str(exc_info.value)


def test_parse_csv_decimal_robust_against_caller_low_precision() -> None:
    """Welle-5b-Review M-2: parse_csv_profile soll auch in einem
    Caller-Kontext mit niedriger Decimal-Precision verlustfrei
    parsen (localcontext-Wrapper)."""
    from decimal import localcontext as caller_localcontext

    text = "target_device_id,tick_ms,tick_values\nload-1,1000,1.123456789012345678901234\n"
    with caller_localcontext() as ctx:
        ctx.prec = 4  # bewusst zu niedrig
        profile = parse_csv_profile(text)
    # Volle 24 Nachkomma-Stellen erhalten (prec=28 im Wrapper).
    assert profile.tick_values[0] == Decimal("1.123456789012345678901234")


# ---------------------------------------------------------------------------
# parse_json_profile — String-Pfad (ADR 0020 §2.4)
# ---------------------------------------------------------------------------


def test_parse_json_string_happy_path() -> None:
    text = '{"target_device_id": "load-1", "tick_ms": 1000, "tick_values": [1.5, 2.0, 1.8]}'
    profile = parse_json_profile(text)
    assert profile.target_device_id == "load-1"
    assert profile.tick_ms == 1000
    assert profile.tick_values == (Decimal("1.5"), Decimal("2.0"), Decimal("1.8"))


def test_parse_json_string_integer_values_become_decimal() -> None:
    """ADR 0020 §2.4 Punkt 2: Integer in tick_values werden via
    Decimal(value) konvertiert."""
    text = '{"target_device_id": "load-1", "tick_ms": 1000, "tick_values": [1, 2, 3]}'
    profile = parse_json_profile(text)
    assert profile.tick_values == (Decimal("1"), Decimal("2"), Decimal("3"))


def test_parse_json_string_mixed_int_and_float() -> None:
    """ADR 0020 §2.4: parse_float=Decimal + Integer-Konvertierung."""
    text = '{"target_device_id": "load-1", "tick_ms": 1000, "tick_values": [1.5, 2, 3.0]}'
    profile = parse_json_profile(text)
    assert profile.tick_values == (
        Decimal("1.5"),
        Decimal("2"),
        Decimal("3.0"),
    )


def test_parse_json_string_missing_field_rejected() -> None:
    text = '{"target_device_id": "load-1", "tick_ms": 1000}'
    with pytest.raises(LoadProfileMissingFieldError):
        parse_json_profile(text)


def test_parse_json_string_non_object_root_rejected() -> None:
    with pytest.raises(LoadProfileTypeError):
        parse_json_profile("[1, 2, 3]")


def test_parse_json_string_float_tick_ms_rejected() -> None:
    """ADR 0020 §2.4 Punkt 4: tick_ms muss int sein, nicht float
    oder Decimal."""
    text = '{"target_device_id": "load-1", "tick_ms": 1000.0, "tick_values": [1.5]}'
    with pytest.raises(LoadProfileTypeError):
        parse_json_profile(text)


def test_parse_json_string_bool_tick_ms_rejected() -> None:
    """bool ist int-Subclass, soll abgelehnt werden."""
    text = '{"target_device_id": "load-1", "tick_ms": true, "tick_values": [1.5]}'
    with pytest.raises(LoadProfileTypeError):
        parse_json_profile(text)


def test_parse_json_string_bool_tick_value_rejected() -> None:
    """ADR 0020 §2.4 Punkt 3: bool in tick_values wird abgelehnt
    (Drift-Signal)."""
    text = '{"target_device_id": "load-1", "tick_ms": 1000, "tick_values": [1.5, true, 2.0]}'
    with pytest.raises(LoadProfileTypeError):
        parse_json_profile(text)


# ---------------------------------------------------------------------------
# parse_json_profile — Mapping-Pfad (ADR 0020 §2.4 Punkt 5)
# ---------------------------------------------------------------------------


def test_parse_json_mapping_happy_path() -> None:
    payload: dict[str, object] = {
        "target_device_id": "load-1",
        "tick_ms": 1000,
        "tick_values": [Decimal("1.5"), Decimal("2.0")],
    }
    profile = parse_json_profile(payload)
    assert profile.tick_values == (Decimal("1.5"), Decimal("2.0"))


def test_parse_json_mapping_int_tick_values_accepted() -> None:
    payload: dict[str, object] = {
        "target_device_id": "load-1",
        "tick_ms": 1000,
        "tick_values": [1, 2, 3],
    }
    profile = parse_json_profile(payload)
    assert profile.tick_values == (Decimal("1"), Decimal("2"), Decimal("3"))


def test_parse_json_mapping_str_decimal_accepted() -> None:
    """Welle-5b-Review M-3: Mapping-Pfad akzeptiert Decimal-Strings
    (z.B. aus YAML/TOML-Adaptern, die parse_float=Decimal nicht
    durchreichen koennen)."""
    payload: dict[str, object] = {
        "target_device_id": "load-1",
        "tick_ms": 1000,
        "tick_values": ["1.5", "2.0", "3.14"],
    }
    profile = parse_json_profile(payload)
    assert profile.tick_values == (Decimal("1.5"), Decimal("2.0"), Decimal("3.14"))


def test_parse_json_mapping_invalid_str_decimal_rejected() -> None:
    """Strings, die kein gueltiger Decimal sind, werden typed
    abgelehnt."""
    payload: dict[str, object] = {
        "target_device_id": "load-1",
        "tick_ms": 1000,
        "tick_values": ["not-a-decimal"],
    }
    with pytest.raises(LoadProfileTypeError):
        parse_json_profile(payload)


def test_parse_json_mapping_float_tick_value_rejected() -> None:
    """ADR 0020 §2.4 Punkt 5: float im Mapping-Pfad wird
    abgelehnt (Round-Trip-Verlust-Defense)."""
    payload: dict[str, object] = {
        "target_device_id": "load-1",
        "tick_ms": 1000,
        "tick_values": [1.5],  # float, nicht Decimal
    }
    with pytest.raises(LoadProfileTypeError):
        parse_json_profile(payload)


def test_parse_json_mapping_bool_tick_value_rejected() -> None:
    payload: dict[str, object] = {
        "target_device_id": "load-1",
        "tick_ms": 1000,
        "tick_values": [True, False],
    }
    with pytest.raises(LoadProfileTypeError):
        parse_json_profile(payload)


def test_parse_json_mapping_non_list_tick_values_rejected() -> None:
    payload: dict[str, object] = {
        "target_device_id": "load-1",
        "tick_ms": 1000,
        "tick_values": "1.5,2.0",
    }
    with pytest.raises(LoadProfileTypeError):
        parse_json_profile(payload)


def test_parse_json_mapping_empty_tick_values_rejected() -> None:
    payload: dict[str, object] = {
        "target_device_id": "load-1",
        "tick_ms": 1000,
        "tick_values": [],
    }
    with pytest.raises(LoadProfileEmptyError):
        parse_json_profile(payload)


def test_parse_json_non_str_non_mapping_rejected() -> None:
    with pytest.raises(LoadProfileTypeError):
        parse_json_profile(123)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Architektur-Pflicht: KEIN Datei-I/O im core (Review-Round-1-High-1)
# ---------------------------------------------------------------------------


def test_loads_all_subset_of_grid_model_init_all() -> None:
    """Welle-5b-Review L-7: `loads.__all__` und `__init__.__all__`
    pflegen ueberlappende Symbol-Listen. Pinnt, dass alle in
    `loads.__all__` exportierten Symbole auch im obersten Modul-
    Re-Export liegen — verhindert Drift bei zukuenftigen
    Erweiterungen."""
    from grid_gym.hexagon.core import grid_model as package
    from grid_gym.hexagon.core.grid_model import loads as loads_module

    loads_exports = set(loads_module.__all__)
    package_exports = set(package.__all__)
    missing = loads_exports - package_exports
    assert not missing, f"Symbols in loads.__all__ but not re-exported: {missing}"


def test_loads_module_does_not_import_pathlib_or_open_files() -> None:
    """GG-AR-TABU-002: hexagon/core ist I/O-frei. parse_*-Funktionen
    sollen ueber bereits-eingelesenen Text/Mapping arbeiten, kein
    open() oder Path-Lesen.

    Welle-5b-Review L-1: AST-basierte Pruefung statt `dir(module)`-
    Heuristik. `dir()` haette ein versehentliches
    `import pathlib as _pathlib` durchgelassen; AST-Scan
    findet jeden Import-Statement, unabhaengig vom Alias.
    """
    import ast
    import inspect

    import grid_gym.hexagon.core.grid_model.loads as loads_module

    source = inspect.getsource(loads_module)
    tree = ast.parse(source)

    forbidden_modules = {"pathlib", "io", "os"}
    forbidden_names = {"open"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root not in forbidden_modules, f"forbidden module import: {alias.name}"
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            root = node.module.split(".")[0]
            assert root not in forbidden_modules, f"forbidden from-import: {node.module}"
            for alias in node.names:
                assert alias.name not in forbidden_names, (
                    f"forbidden from-import name: {alias.name}"
                )
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            # Pruefe Aufrufstellen wie `open(...)`.
            assert node.id not in forbidden_names, f"forbidden builtin reference: {node.id}"
