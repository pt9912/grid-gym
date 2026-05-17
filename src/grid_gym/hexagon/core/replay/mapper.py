"""Replay-Mapper (`GG-REPLAY-001`/`002`/`003`).

Konvertiert raw CSV/JSON-Lines-Eintraege in `ReplaySample`-Tupel
und mappt Originalzeitstempel auf Simulationszeit.

Determinismus-Vertrag (`GG-REPLAY-003`): Samples mit gleichem
`timestamp` werden stabil nach `(simulation_time, device_id,
metric, import_sequence)` sortiert. `import_sequence` ist eine
0-basierte Counter-Variable, die der Mapper vergibt — damit
bleibt die Tie-Breaking-Reihenfolge auch dann reproduzierbar,
wenn `device_id`/`metric` kollidieren.

Zeitmappings: Welle 5 liefert zwei Strategien:
- `time_mapping_monotonic`: erstes Sample → `simulation_time=0`,
  nachfolgende um `(timestamp - first_timestamp).total_seconds()`
  * 1000 (`ms`-Quantisierung) verschoben. Erwartet ISO-8601-UTC.
- `time_mapping_index`: Sample n bekommt `simulation_time = n *
  tick_ms`. Ignoriert den Originalzeitstempel (Fallback fuer
  format-fremde Quellen).

`canonical_json`-Vertrag: `value` ist `Decimal` (max. 6 NK per
`GG-DATA-005`); der Mapper konvertiert numerische Roh-Werte via
`Decimal(str(...)).quantize(Decimal("0.000001"))`.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final

from grid_gym.hexagon.core.domain.replay import ReplaySample
from grid_gym.hexagon.core.errors import (
    ReplayInvalidValueError,
    ReplayMissingFieldError,
)

_REQUIRED_CSV_FIELDS: Final[tuple[str, ...]] = (
    "timestamp",
    "device_id",
    "metric",
    "value",
    "unit",
)
"""Pflichtfelder pro Sample (`GG-REPLAY-001` Akzeptanz)."""

_QUANTUM_6_PLACES: Final[Decimal] = Decimal("0.000001")
"""Quantisierungsraster (`GG-DATA-005`)."""


def parse_csv(
    text: str, *, tick_ms: int, time_mapping: str = "monotonic"
) -> tuple[ReplaySample, ...]:
    """Parsed CSV-Text mit `timestamp,device_id,metric,value,unit`-
    Spalten in eine sortierte `ReplaySample`-Sequenz.

    `tick_ms` wird nur fuer `time_mapping="index"` genutzt.
    """
    reader = csv.DictReader(io.StringIO(text))
    raw_rows = [(index, row) for index, row in enumerate(reader)]
    return _build_samples(raw_rows, tick_ms=tick_ms, time_mapping=time_mapping)


def parse_jsonl(
    text: str, *, tick_ms: int, time_mapping: str = "monotonic"
) -> tuple[ReplaySample, ...]:
    """Parsed JSON-Lines-Text in eine sortierte `ReplaySample`-Sequenz."""
    raw_rows: list[tuple[int, dict[str, object]]] = []
    for index, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ReplayInvalidValueError(index, "<line>", "invalid JSON") from exc
        if not isinstance(row, dict):
            raise ReplayInvalidValueError(
                index, "<line>", f"expected JSON object, got {type(row).__name__}"
            )
        raw_rows.append((index, row))
    return _build_samples(raw_rows, tick_ms=tick_ms, time_mapping=time_mapping)


def _build_samples(
    raw_rows: list[tuple[int, dict[str, object]]],
    *,
    tick_ms: int,
    time_mapping: str,
) -> tuple[ReplaySample, ...]:
    """Konvertiert geparste Rohzeilen in sortierte `ReplaySample`-Tupel."""
    parsed = [_parse_row(index, row) for index, row in raw_rows]
    if not parsed:
        return ()
    timed = _assign_simulation_times(parsed, tick_ms=tick_ms, time_mapping=time_mapping)
    return tuple(sorted(timed, key=_sort_key))


def _parse_row(line_index: int, row: dict[str, object]) -> tuple[int, str, str, str, Decimal, str]:
    """Validiert eine Roh-Zeile und liefert (line_index, timestamp,
    device_id, metric, value, unit). Wirft typisierte Fehler."""
    for field in _REQUIRED_CSV_FIELDS:
        if field not in row or row[field] in (None, ""):
            raise ReplayMissingFieldError(line_index, field)
    timestamp = _as_str(line_index, "timestamp", row["timestamp"])
    device_id = _as_str(line_index, "device_id", row["device_id"])
    metric = _as_str(line_index, "metric", row["metric"])
    value = _as_decimal(line_index, "value", row["value"])
    unit = _as_str(line_index, "unit", row["unit"])
    return (line_index, timestamp, device_id, metric, value, unit)


def _as_str(line_index: int, field: str, value: object) -> str:
    if not isinstance(value, str):
        raise ReplayInvalidValueError(
            line_index, field, f"expected str, got {type(value).__name__}"
        )
    return value


def _as_decimal(line_index: int, field: str, value: object) -> Decimal:
    """Konvertiert `value` zu `Decimal(str(...))` mit 6-NK-Quantisierung.

    Akzeptiert `str`, `int`, `Decimal` als Eingabe. `float` wird
    bewusst nicht akzeptiert (`GG-DATA-005` verlangt Decimal-Pfad)."""
    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, str):
        try:
            decimal_value = Decimal(value)
        except (ValueError, ArithmeticError) as exc:
            raise ReplayInvalidValueError(
                line_index, field, f"cannot parse Decimal from {value!r}"
            ) from exc
    elif isinstance(value, int) and not isinstance(value, bool):
        decimal_value = Decimal(value)
    else:
        raise ReplayInvalidValueError(
            line_index, field, f"unsupported value type {type(value).__name__}"
        )
    return decimal_value.quantize(_QUANTUM_6_PLACES, rounding=ROUND_HALF_EVEN)


def _assign_simulation_times(
    rows: Iterable[tuple[int, str, str, str, Decimal, str]],
    *,
    tick_ms: int,
    time_mapping: str,
) -> list[ReplaySample]:
    """Mappt Originalzeitstempel auf Simulationszeit per gewaehlter
    Strategie."""
    if time_mapping not in {"monotonic", "index"}:
        raise ReplayInvalidValueError(0, "time_mapping", f"unknown strategy {time_mapping!r}")
    rows_list = list(rows)
    if time_mapping == "index":
        return [
            ReplaySample(
                timestamp=timestamp,
                simulation_time=position * tick_ms,
                device_id=device_id,
                metric=metric,
                value=value,
                unit=unit,
                import_sequence=line_index,
            )
            for position, (line_index, timestamp, device_id, metric, value, unit) in enumerate(
                rows_list
            )
        ]
    # monotonic: Original-Timestamps werden zu ms-deltas ab erstem Sample.
    first_dt = _parse_iso8601_utc(rows_list[0][0], rows_list[0][1])
    samples: list[ReplaySample] = []
    for line_index, timestamp, device_id, metric, value, unit in rows_list:
        dt = _parse_iso8601_utc(line_index, timestamp)
        delta_ms = int((dt - first_dt).total_seconds() * 1000)
        samples.append(
            ReplaySample(
                timestamp=timestamp,
                simulation_time=delta_ms,
                device_id=device_id,
                metric=metric,
                value=value,
                unit=unit,
                import_sequence=line_index,
            )
        )
    return samples


def _parse_iso8601_utc(line_index: int, timestamp: str) -> datetime:
    """ISO-8601-Parse via stdlib `datetime.fromisoformat` (Python 3.11+
    akzeptiert `Z`-Suffix)."""
    try:
        dt = datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise ReplayInvalidValueError(
            line_index, "timestamp", f"not ISO-8601: {timestamp!r}"
        ) from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _sort_key(sample: ReplaySample) -> tuple[int, str, str, int]:
    """Deterministische Tie-Breaking-Reihenfolge (`GG-REPLAY-003`):
    `(simulation_time, device_id, metric, import_sequence)`."""
    return (
        sample.simulation_time,
        sample.device_id,
        sample.metric,
        sample.import_sequence,
    )
