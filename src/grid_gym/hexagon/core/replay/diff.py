"""Replay-Diff-Klassifikation (`GG-REPLAY-007`).

Vergleicht zwei `ReplaySample`-Sequenzen (`expected` vs.
`actual`) und liefert `ReplayDelta`-Tupel mit Klassifikation
„fachlich" vs. „volatil".

Klassifikations-Regeln:
- **Volatile Felder** sind Vergleichs-irrelevant fuer fachliche
  Korrektheit (z. B. `import_sequence`, `timestamp` als
  Roh-String wenn `simulation_time` schon stimmt). Welle 5
  fuehrt eine konfigurierbare `volatile_fields`-Liste; der
  Default ist `frozenset({"import_sequence", "timestamp"})`.
- **Fachliche Felder** sind alle anderen
  (`simulation_time`, `device_id`, `metric`, `value`, `unit`).

Vergleichs-Pfade (`path`-Feld in `ReplayDelta`):
- `"sample[i].field"` fuer Werte-Mismatches.
- `"sample[i]"` mit `expected="<sample>"` / `actual="<missing>"`
  fuer Laengen-Mismatches (oder umgekehrt).

`tick`-Feld in `ReplayDelta` ist `simulation_time // 1000` —
grobes Ticks-pro-Sekunde-Mapping; bei genauerer Tick-ms-
Zuordnung uebernimmt der Aufrufer den Mapping-Schritt
(`GG-REPLAY-007` Akzeptanz nennt nur „Tick", die konkrete
Skala ist Welle-5-Default).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import fields
from typing import Final

from grid_gym.hexagon.core.domain.replay import (
    ReplayDelta,
    ReplayDeltaClassification,
    ReplaySample,
)

_VOLATILE_FIELDS_DEFAULT: Final[frozenset[str]] = frozenset({"import_sequence", "timestamp"})
"""Default-volatile Felder.

`import_sequence` ist ein interner Mapper-Counter, der zwischen
zwei Laeufen variieren kann, ohne dass das Replay fachlich
abweicht.

`timestamp` ist der Original-String aus der Quelle; bei
ISO-8601-Quellen kann derselbe Moment in mehreren Formen
(`2024-01-01T00:00:00Z` vs. `2024-01-01T00:00:00+00:00`) auftauchen,
ohne dass das Replay fachlich abweicht. Wenn die Simulationszeit
korrekt gemappt ist, ist der Roh-String redundant.
"""


def diff_replay(
    expected: Iterable[ReplaySample],
    actual: Iterable[ReplaySample],
    *,
    volatile_fields: frozenset[str] | None = None,
) -> tuple[ReplayDelta, ...]:
    """Vergleicht zwei `ReplaySample`-Sequenzen feldweise und liefert
    klassifizierte `ReplayDelta`-Tupel.

    Wenn `volatile_fields=None`, gilt der Default aus
    `_VOLATILE_FIELDS_DEFAULT`. Per Aufrufer-Override kann die
    Liste je Use-Case verschaerft oder gelockert werden.
    """
    volatile = volatile_fields if volatile_fields is not None else _VOLATILE_FIELDS_DEFAULT
    expected_list = list(expected)
    actual_list = list(actual)
    deltas: list[ReplayDelta] = []
    pair_count = min(len(expected_list), len(actual_list))
    for index in range(pair_count):
        deltas.extend(_compare_sample(index, expected_list[index], actual_list[index], volatile))
    if len(actual_list) > pair_count:
        for index in range(pair_count, len(actual_list)):
            sample = actual_list[index]
            deltas.append(
                ReplayDelta(
                    path=f"sample[{index}]",
                    expected="<missing>",
                    actual="<sample>",
                    tick=sample.simulation_time // 1000,
                    device_id=sample.device_id,
                    classification=ReplayDeltaClassification.FACHLICH,
                )
            )
    elif len(expected_list) > pair_count:
        for index in range(pair_count, len(expected_list)):
            sample = expected_list[index]
            deltas.append(
                ReplayDelta(
                    path=f"sample[{index}]",
                    expected="<sample>",
                    actual="<missing>",
                    tick=sample.simulation_time // 1000,
                    device_id=sample.device_id,
                    classification=ReplayDeltaClassification.FACHLICH,
                )
            )
    return tuple(deltas)


def _compare_sample(
    index: int,
    expected: ReplaySample,
    actual: ReplaySample,
    volatile: frozenset[str],
) -> list[ReplayDelta]:
    """Feld-fuer-Feld-Vergleich; sammelt Deltas pro abweichendem Feld."""
    deltas: list[ReplayDelta] = []
    for field in fields(ReplaySample):
        name = field.name
        expected_value = getattr(expected, name)
        actual_value = getattr(actual, name)
        if expected_value == actual_value:
            continue
        classification = (
            ReplayDeltaClassification.VOLATIL
            if name in volatile
            else ReplayDeltaClassification.FACHLICH
        )
        deltas.append(
            ReplayDelta(
                path=f"sample[{index}].{name}",
                expected=str(expected_value),
                actual=str(actual_value),
                tick=expected.simulation_time // 1000,
                device_id=expected.device_id,
                classification=classification,
            )
        )
    return deltas
