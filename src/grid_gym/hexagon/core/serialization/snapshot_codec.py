"""Wiederverwendbare Free-Functions fuer strukturelle Format-Validierung
(M2 Welle 0a, Trigger 014).

Sammelt das wortgleiche Pattern, das in M1 Welle 1..5 fuenfmal als
private Helfer-Funktion auftaucht (`_assert_required_keys`,
`_assert_int`, `_assert_mapping` in RandomPort-, Scheduler-, TickLoop-,
Scenario- und Replay-Modulen) plus `_assert_payload_canonical` aus
`hexagon/core/simulation/scheduler.py` als wiederverwendbare Free-
Functions. Aufrufer geben den `subsystem`-Identifier (`"random_port"`,
`"scheduler"`, `"tick_loop"`, `"scenario"`, `"replay"`, neue M2-
Geraete-Subsysteme wie `"battery"`, `"grid_model"`) explizit mit;
die geworfenen Fehler tragen ihn ueber `SnapshotFormatError.subsystem`
typisiert nach aussen.

Sub-Modul-Wahl: `hexagon/core/serialization/snapshot_codec.py` neben
dem bestehenden `canonical.py`. Beide Module sind stdlib-only und
respektieren `AC-HEXAGON-PURE`.

**Bestehende M1-Module behalten ihre privaten Helfer** (`scheduler.py`
ruft weiterhin `_assert_payload_canonical` lokal auf), bis sie in
einem Folge-Slice mechanisch auf die Free-Functions migriert werden.
M2-Welle-0a fuehrt die generischen Funktionen ein und verkabelt sie
im Scenario-Validator fuer den Payload-Canonical-Check; M2-Welle-1+
nutzt sie direkt fuer die Geraete-Snapshots.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from grid_gym.hexagon.core.errors import (
    MissingKeysError,
    WrongTypeError,
)


def assert_required_keys(
    state: Mapping[str, object],
    required: frozenset[str] | set[str],
    subsystem: str,
) -> None:
    """Prueft, dass `state` alle Keys aus `required` enthaelt.

    Wirft `MissingKeysError(subsystem, missing)` bei Verstoss.
    Welle-0b-Review L-11: die Sortierung der fehlenden Keys ist
    Aufgabe des `MissingKeysError`-Konstruktors (errors.py),
    der `sorted(missing)` defensiv vor dem Format ausfuehrt — hier
    waere ein zweiter `sorted()`-Aufruf redundant.
    """
    missing = required - state.keys()
    if missing:
        raise MissingKeysError(subsystem, list(missing))


def assert_int(value: object, key: str, subsystem: str) -> int:
    """Prueft, dass `value` ein `int` (und nicht `bool`) ist.

    `bool` ist `int`-Subklasse in Python — Schema-Versionen, Tick-IDs
    und Sequenz-Nummern sind aber Ganzzahlen, keine Wahrheitswerte.
    Bei Verstoss wirft `WrongTypeError(subsystem, key, "int", actual_type)`.
    Bei Erfolg liefert der Wert als `int` zurueck (fuer ergonomische
    Verkettung am Aufruferort).
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise WrongTypeError(subsystem, key, "int", type(value).__name__)
    return value


def assert_str(value: object, key: str, subsystem: str) -> str:
    """Prueft, dass `value` ein `str` ist.

    Wirft `WrongTypeError(subsystem, key, "str", actual_type)` bei
    Verstoss. Liefert den Wert als `str` zurueck (ergonomische
    Verkettung am Aufruferort).

    Welle-3-Review L-1: Vereinheitlicht das `_assert_str`-Pattern,
    das in Geraete-Snapshot-Modulen (battery/pv/load) dreimal als
    privater Helfer auftauchte.
    """
    if not isinstance(value, str):
        raise WrongTypeError(subsystem, key, "str", type(value).__name__)
    return value


def assert_decimal(value: object, key: str, subsystem: str) -> Decimal:
    """Prueft, dass `value` ein `Decimal` ist.

    Wirft `WrongTypeError(subsystem, key, "Decimal", actual_type)`
    bei Verstoss. Liefert den Wert als `Decimal` zurueck.

    `bool` und `int` werden NICHT akzeptiert — Snapshot-Felder mit
    physikalischer Bedeutung (Power, SOC, Decimal-Konfig) muessen
    immer als `Decimal` serialisiert werden (GG-DATA-005 no-float).

    Welle-3-Review L-1: Vereinheitlicht das `_decimal`-Pattern, das
    in Geraete-Snapshot-Modulen (battery/pv/load) dreimal als
    privater Helfer auftauchte.
    """
    if not isinstance(value, Decimal):
        raise WrongTypeError(subsystem, key, "Decimal", type(value).__name__)
    return value


def assert_mapping(value: object, key: str, subsystem: str) -> dict[str, object]:
    """Prueft, dass `value` ein `dict[str, object]` ist.

    Wirft `WrongTypeError(subsystem, key, "Mapping", actual_type)` bei
    Verstoss. Die Map-Werte werden NICHT rekursiv geprueft; dafuer ist
    `assert_payload_canonical_compatible` da.

    Welle-0b-Review H-2: bewusst eng auf `dict` (nicht beliebige
    `Mapping`-Subklassen), weil
    `serialization/canonical.py::canonical_json` ebenfalls nur `dict`
    akzeptiert. Ein `MappingProxyType`-Smuggler wuerde sonst hier
    durchgehen und erst im Hash-Encoder typloss kippen.
    """
    if not isinstance(value, dict):
        raise WrongTypeError(subsystem, key, "Mapping", type(value).__name__)
    return value


def assert_optional_fault_flag(
    state: Mapping[str, object],
    fault_state_key: str,
    flag_key: str,
    subsystem: str,
) -> bool:
    """Liest ein optionales Bool-Flag aus dem additiven `fault_state`-
    Sub-Block (ADR 0025 §2.2-Konvention).

    Sammelt das wortgleiche Pattern, das in den Geraete-Snapshots
    (`battery`/`grid_connection`/`ev_charger`/`transformer`) mehrfach als
    privater Reader auftaucht (M8-Welle-2b-Review-Folge, Slice 045).

    - `fault_state_key` fehlt im `state` → `False` (Backward-Compat:
      Welle-1-Snapshots ohne Fault-Block bleiben roundtrip-faehig).
    - Block vorhanden, `flag_key` fehlt → `False` (Default).
    - `flag_key` vorhanden, aber nicht `bool` → `WrongTypeError(subsystem,
      f"{fault_state_key}.{flag_key}", "bool", actual_type)`.
    - sonst der Bool-Wert.
    """
    if fault_state_key not in state:
        return False
    fault_state = assert_mapping(state[fault_state_key], fault_state_key, subsystem)
    raw_flag = fault_state.get(flag_key, False)
    if not isinstance(raw_flag, bool):
        raise WrongTypeError(
            subsystem, f"{fault_state_key}.{flag_key}", "bool", type(raw_flag).__name__
        )
    return raw_flag


def assert_payload_canonical_compatible(
    payload: object,
    subsystem: str,
    path: str = "payload",
) -> None:
    """Prueft rekursiv, dass `payload` ausschliesslich canonical_json-
    faehige Wertetypen enthaelt.

    Erlaubte Wertebereiche (1:1-Spiegel von
    `serialization/canonical.py::canonical_json`):
    `None`, `bool`, `int`, `Decimal`, `str`, `dict[str, ...]`, `list`,
    `tuple`. Verboten: `float`, `bytes`, `complex`, `set`,
    `frozenset`, `bytearray`, `MappingProxyType` und sonstige
    `Mapping`-Subklassen ausserhalb von `dict`, sowie `dict`-Keys,
    die nicht `str` sind, und alles Andere.

    Welle-0b-Review H-2: `dict` (nicht `Mapping`) ist Vertragsspiegel
    zum Encoder. Ein `types.MappingProxyType` oder eine eigene
    `Mapping`-Subklasse wuerde sonst hier durchgehen und erst spaeter
    in `canonical_json` mit `UnsupportedTypeError` brechen.

    Bei Verstoss wirft `WrongTypeError(subsystem, "<path>.<key>",
    "canonical-compatible", actual_type)`. Aufrufer (z. B. Scenario-
    Loader nach struktureller Validierung) fangen das auf der
    `SnapshotFormatError`-Ebene oder spezifisch auf `WrongTypeError`.

    Pfad-Konvention (`path`-Aufbau): `"<root>.<key>"` fuer
    Mapping-Eintraege, `"<root>[<index>]"` fuer Listen/Tuple-Eintraege.
    Default-`path="payload"` matched die heutige Scheduler-Boundary-
    Konvention; Scenario-Validator uebergibt z. B. `"events[0].payload"`.
    """
    if payload is None or isinstance(payload, bool | int | Decimal | str):
        # `bool` ist `int`-Subklasse — fuer Payload-Werte explizit
        # erlaubt (`canonical_json` emittiert `true`/`false`).
        return
    if isinstance(payload, dict):
        for key, sub_value in payload.items():
            if not isinstance(key, str):
                raise WrongTypeError(subsystem, f"{path}.<key>", "str", type(key).__name__)
            assert_payload_canonical_compatible(sub_value, subsystem, f"{path}.{key}")
        return
    if isinstance(payload, list | tuple):
        for sub_index, sub_value in enumerate(payload):
            assert_payload_canonical_compatible(sub_value, subsystem, f"{path}[{sub_index}]")
        return
    raise WrongTypeError(subsystem, path, "canonical-compatible", type(payload).__name__)
