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

    Wirft `MissingKeysError(subsystem, sorted(missing))` bei Verstoss.
    Die sortierte Liste der fehlenden Keys macht die Fehler-Meldung
    byte-stabil (deterministisch).
    """
    missing = required - state.keys()
    if missing:
        raise MissingKeysError(subsystem, sorted(missing))


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
