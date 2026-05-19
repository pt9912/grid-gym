"""`hexagon/core/grid_model/loads.py` — Lastenheft-`GG-GRID-003`/`004`
(M2 Welle 5b, ADR 0020).

Liefert die **Daten-Repraesentation** fuer Last-Profile und
Last-Spruenge sowie **pure Parser** fuer CSV/JSON-Inhalte
(`parse_csv_profile`, `parse_json_profile`). Datei-I/O ist
**Adapter-Verantwortung** (`GG-AR-TABU-002`); diese Datei
enthaelt keinen `open()`-Aufruf.

Datenstrukturen:

- `LoadEvent` (`GG-GRID-004`): Scenario-Event mit Start/Dauer/
  Power; TickLoop uebersetzt aktive Events in
  `set_power_kw`-Commands. Nach Ablauf Restore auf
  `LoadConfig.rated_power_kw` (ADR 0020 §2.2 Restore-
  Konvention).
- `LoadProfile` (`GG-GRID-003` „Zeitreihen"): Tick-indizierte
  `Decimal`-Folge; Profil-Index ueber
  `(context.tick * context.tick_ms) // profile.tick_ms`
  (ADR 0020 §2.3 — off-by-one-frei gegen TickLoop-Clock-
  Konvention).

Welle-5b-Out-of-Scope (vgl. ADR 0020 §7): Datei-I/O, Glob,
Streaming-Loader, Profil-Interpolation, Loop-Modus,
Stochastik, ueberlappende Same-Device-Events (Stack-Restore).
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation, localcontext
from typing import Final

from grid_gym.hexagon.core.errors import GridGymError

_ZERO = Decimal(0)
_LOADS_DECIMAL_PRECISION: Final[int] = 28


@contextmanager
def _loads_decimal_context() -> Iterator[None]:
    """Decimal-Localcontext-Wrapper (Welle-5b-Review M-2):
    `Decimal(<string>)` haengt am thread-globalen Caller-Kontext.
    Eine Aufrufer-Umgebung mit reduzierter Praezision wuerde lange
    Decimal-Strings stumm verlieren; der Wrapper pinnt `prec=28`
    + `ROUND_HALF_EVEN` analog `bilanz.py::_grid_model_decimal_context`."""
    with localcontext() as ctx:
        ctx.prec = _LOADS_DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        yield


# ---------------------------------------------------------------------------
# Error-Hierarchie (Welle-0a-Codec-Spiegel, ADR 0020 §2.4)
# ---------------------------------------------------------------------------


class LoadProfileFormatError(GridGymError):
    """Wurzel der `LoadProfile`-Format-Fehler."""


class LoadProfileMissingFieldError(LoadProfileFormatError):
    """Pflicht-Feld fehlt in der Eingabe."""

    def __init__(self, field: str) -> None:
        super().__init__(f"LoadProfile: missing field {field!r}")


class LoadProfileTypeError(LoadProfileFormatError):
    """Feld hat falschen Typ oder unzulaessigen Wert."""

    def __init__(self, field: str, expected: str, actual: object) -> None:
        super().__init__(f"LoadProfile.{field}: expected {expected!r}, got {actual!r}")


class LoadProfileEmptyError(LoadProfileFormatError):
    """`tick_values` ist leer (verstoesst gegen Welle-5b-Invariante)."""

    def __init__(self) -> None:
        super().__init__("LoadProfile.tick_values must contain >= 1 entry")


# ---------------------------------------------------------------------------
# LoadEvent (GG-GRID-004, ADR 0020 §2.2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LoadEvent:
    """Scenario-Event-Lastsprung (`GG-GRID-004`).

    Invarianten (ADR 0020 §2.2):
    - `start_s` Decimal, `>= 0`.
    - `duration_s` Decimal, `> 0`.
    - `target_device_id` str, nicht-leer.
    - `power_kw` Decimal, `>= 0` (LoadDevice-Sign-Vertrag aus
      ADR 0016 §2.2 — Load verbraucht nicht-negativ).

    Restore nach Event-Ablauf: TickLoop ruft
    `apply_command(set_power_kw, value=LoadConfig.rated_power_kw)`
    am LoadDevice (Welle-5b-Konvention; kein gespeicherter
    Vor-Event-Wert).
    """

    start_s: Decimal
    duration_s: Decimal
    target_device_id: str
    power_kw: Decimal

    def __post_init__(self) -> None:
        for field_name in ("start_s", "duration_s", "power_kw"):
            value = getattr(self, field_name)
            if not isinstance(value, Decimal):
                raise LoadProfileTypeError(field_name, "Decimal", type(value).__name__)
        if not isinstance(self.target_device_id, str):
            raise LoadProfileTypeError(
                "target_device_id", "str", type(self.target_device_id).__name__
            )
        if self.target_device_id == "":
            raise LoadProfileTypeError("target_device_id", "non-empty str", "''")
        if self.start_s < _ZERO:
            raise LoadProfileTypeError("start_s", ">= 0", self.start_s)
        if self.duration_s <= _ZERO:
            raise LoadProfileTypeError("duration_s", "> 0", self.duration_s)
        if self.power_kw < _ZERO:
            raise LoadProfileTypeError("power_kw", ">= 0", self.power_kw)


# ---------------------------------------------------------------------------
# LoadProfile (GG-GRID-003 Zeitreihen, ADR 0020 §2.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LoadProfile:
    """Tick-indiziertes Last-Profil (`GG-GRID-003`).

    Invarianten (ADR 0020 §2.3):
    - `target_device_id` str, nicht-leer.
    - `tick_values` tuple[Decimal, ...], mindestens 1 Element,
      alle `>= 0`.
    - `tick_ms` int, `> 0`.

    Vertrag in Welle 6: Profil-Index
    `(context.tick * context.tick_ms) // profile.tick_ms`;
    out-of-bounds → Repeat-Last-Value. Keine Interpolation.
    """

    target_device_id: str
    tick_values: tuple[Decimal, ...]
    tick_ms: int

    def __post_init__(self) -> None:
        if not isinstance(self.target_device_id, str):
            raise LoadProfileTypeError(
                "target_device_id", "str", type(self.target_device_id).__name__
            )
        if self.target_device_id == "":
            raise LoadProfileTypeError("target_device_id", "non-empty str", "''")
        if not isinstance(self.tick_values, tuple):
            raise LoadProfileTypeError(
                "tick_values", "tuple[Decimal, ...]", type(self.tick_values).__name__
            )
        if len(self.tick_values) == 0:
            raise LoadProfileEmptyError
        for index, value in enumerate(self.tick_values):
            if not isinstance(value, Decimal):
                raise LoadProfileTypeError(f"tick_values[{index}]", "Decimal", type(value).__name__)
            if value < _ZERO:
                raise LoadProfileTypeError(f"tick_values[{index}]", ">= 0", value)
        # GG-DATA-005-Spiegel: tick_ms muss int sein, nicht bool/float/Decimal.
        if isinstance(self.tick_ms, bool) or not isinstance(self.tick_ms, int):
            raise LoadProfileTypeError(
                "tick_ms", "int (not bool/float/Decimal)", type(self.tick_ms).__name__
            )
        if self.tick_ms <= 0:
            raise LoadProfileTypeError("tick_ms", "> 0", self.tick_ms)


# ---------------------------------------------------------------------------
# Pure Parser (ADR 0020 §2.4) — KEIN Datei-I/O im Core
# ---------------------------------------------------------------------------


_CSV_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "target_device_id",
    "tick_ms",
    "tick_values",
)
_CSV_REQUIRED_LINES: Final[int] = 2  # header + exactly one data row


def parse_csv_profile(text: str) -> LoadProfile:
    """Parst einen CSV-Profil-Text in ein `LoadProfile`.

    CSV-Format (ADR 0020 §2.4):

    ```csv
    target_device_id,tick_ms,tick_values
    load-1,1000,1.5;2.0;1.8;1.2
    ```

    Einzeilige Header + einzeilige Daten; `tick_values` als
    `;`-separated Decimal-Strings (kein float-Roundtrip;
    `Decimal(<string>)` direkt).

    Wirft typed `LoadProfileFormatError`-Subklassen.
    """
    if not isinstance(text, str):
        raise LoadProfileTypeError("text", "str", type(text).__name__)
    lines = text.strip().splitlines()
    # Welle-5b-Review H-1: exakt 2 Zeilen (Header + 1 Data-Row).
    # Multi-Row-Input wird abgewiesen, statt stillschweigend nur
    # die erste Datenzeile zu nehmen — Welle 5b haelt nur Single-
    # Row-CSV. Multi-Row ist Welle-5+/M3-Erweiterung.
    if len(lines) != _CSV_REQUIRED_LINES:
        raise LoadProfileTypeError("csv", "exactly header + 1 data row", f"{len(lines)} lines")
    header_cells = [cell.strip() for cell in lines[0].split(",")]
    if header_cells != list(_CSV_REQUIRED_FIELDS):
        raise LoadProfileMissingFieldError(",".join(_CSV_REQUIRED_FIELDS))
    data_cells = [cell.strip() for cell in lines[1].split(",")]
    if len(data_cells) != len(_CSV_REQUIRED_FIELDS):
        raise LoadProfileTypeError(
            "csv-data", f"{len(_CSV_REQUIRED_FIELDS)} cells", f"{len(data_cells)}"
        )
    target_device_id, tick_ms_str, tick_values_str = data_cells
    try:
        tick_ms = int(tick_ms_str)
    except ValueError as err:
        raise LoadProfileTypeError("tick_ms", "int-string", tick_ms_str) from err
    tick_value_strs = [v.strip() for v in tick_values_str.split(";") if v.strip()]
    if not tick_value_strs:
        raise LoadProfileEmptyError
    # Welle-5b-Review M-2: localcontext-Wrapper schuetzt vor
    # Caller-Praezisions-Verlust.
    try:
        with _loads_decimal_context():
            tick_values = tuple(Decimal(v) for v in tick_value_strs)
    except InvalidOperation as err:
        raise LoadProfileTypeError(
            "tick_values", "Decimal-strings (';'-separated)", tick_values_str
        ) from err
    return LoadProfile(
        target_device_id=target_device_id,
        tick_values=tick_values,
        tick_ms=tick_ms,
    )


def parse_json_profile(payload: str | Mapping[str, object]) -> LoadProfile:
    """Parst einen JSON-Profil-Payload in ein `LoadProfile`.

    Akzeptiert beide Eingabeformen:
    - JSON-**String**: wird intern via
      `json.loads(payload, parse_float=Decimal)` deserialisiert.
    - **Mapping**: bereits deserialisiert (z. B. aus dem
      Scenario-YAML-Adapter); numerische `tick_values` muessen
      `Decimal` oder `int` sein, `float` wird abgelehnt
      (Round-Trip-Verlust-Defense).

    Number-Handling-Vertrag (ADR 0020 §2.4):
    1. `parse_float=Decimal` im String-Pfad.
    2. `int` → `Decimal(value)` im Builder.
    3. `bool` wird abgelehnt (Drift-Signal).
    4. `tick_ms` bleibt `int`.
    5. Mapping-Pfad lehnt `float` in `tick_values` ab.

    Wirft typed `LoadProfileFormatError`-Subklassen.
    """
    mapping = _coerce_to_mapping(payload)
    for field_name in _CSV_REQUIRED_FIELDS:
        if field_name not in mapping:
            raise LoadProfileMissingFieldError(field_name)
    target = _extract_string(mapping["target_device_id"], "target_device_id")
    tick_ms = _extract_strict_int(mapping["tick_ms"], "tick_ms")
    tick_values = _extract_tick_values(mapping["tick_values"])
    return LoadProfile(
        target_device_id=target,
        tick_values=tick_values,
        tick_ms=tick_ms,
    )


def _coerce_to_mapping(
    payload: str | Mapping[str, object],
) -> Mapping[str, object]:
    if isinstance(payload, str):
        raw = json.loads(payload, parse_float=Decimal)
        if not isinstance(raw, Mapping):
            raise LoadProfileTypeError("json-root", "mapping", type(raw).__name__)
        return raw
    if isinstance(payload, Mapping):
        return payload
    raise LoadProfileTypeError("payload", "str or Mapping", type(payload).__name__)


def _extract_string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise LoadProfileTypeError(field, "str", type(value).__name__)
    return value


def _extract_strict_int(value: object, field: str) -> int:
    """Akzeptiert nur `int` (kein `bool`/`float`/`Decimal`)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise LoadProfileTypeError(field, "int", type(value).__name__)
    return value


def _extract_tick_values(raw: object) -> tuple[Decimal, ...]:
    if not isinstance(raw, (list, tuple)):
        raise LoadProfileTypeError("tick_values", "list or tuple", type(raw).__name__)
    if len(raw) == 0:
        raise LoadProfileEmptyError
    return tuple(_coerce_tick_value(v, index) for index, v in enumerate(raw))


def _coerce_tick_value(value: object, index: int) -> Decimal:
    if isinstance(value, bool):
        raise LoadProfileTypeError(f"tick_values[{index}]", "Decimal or int", "bool")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    raise LoadProfileTypeError(
        f"tick_values[{index}]",
        "Decimal or int (not float)",
        type(value).__name__,
    )


__all__ = [
    "LoadEvent",
    "LoadProfile",
    "LoadProfileEmptyError",
    "LoadProfileFormatError",
    "LoadProfileMissingFieldError",
    "LoadProfileTypeError",
    "parse_csv_profile",
    "parse_json_profile",
]
